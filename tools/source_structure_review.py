"""Review and apply bounded source-metadata corrections without re-extraction.

The default invocation is read-only and prints a plan.  --apply consumes that
exact plan, checks its base version and before-values, makes a recoverable
backup, and preserves passage IDs, source text, character maps and geometry.
These corrections are source review, not semantic approval of claims.
"""
import argparse
import hashlib
import json
import re
import shutil
import sqlite3
from datetime import datetime, timezone
from contextlib import contextmanager
from pathlib import Path

from graph_release import refresh_version


DATE = r"20\d{2}-\d{1,2}-\d{1,2}\s*\d{1,2}:\d{2}(?::\d{2})?"
DATED_TITLE = re.compile(r"^.{3,85}[（(](" + DATE + r")[）)]\s*$")
LESSON = re.compile(r"^教你炒股票\s*\d+\s*[：:]")
SOURCE_REVIEWER = "主代理 / 阶段B固定汇编来源结构复核"
EDITABLE = {
    "passages": {"unit_id", "role", "speaker", "published_at"},
    "units": {"end_page"},
    "figures": {"origin_status", "note"},
}


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@contextmanager
def open_ro(root):
    db = sqlite3.connect((root / "graph.sqlite").resolve().as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        db.execute("BEGIN")
        yield db
    finally:
        db.close()


def canonical_time(text):
    match = re.fullmatch(r"(20\d{2})-(\d{1,2})-(\d{1,2})\s*(\d{1,2}):(\d{2})(?::(\d{2}))?", text.strip())
    if not match:
        raise ValueError("不是可确认的完整时间：" + text)
    return datetime(*(int(x or 0) for x in match.groups())).isoformat(sep=" ")


def build_plan(root):
    with open_ro(root) as db:
        metadata = {r["key"]: json.loads(r["value"]) for r in db.execute("SELECT * FROM metadata")}
        documents = [dict(r) for r in db.execute("SELECT * FROM documents ORDER BY filename")]
        rows = [dict(r) for r in db.execute("SELECT * FROM passages ORDER BY document_id,pdf_page,block_index,id")]
        operations, new_units, issues = [], [], []
        changed = {}

        def propose(table, row, after, reason):
            key = (table, row["id"])
            item = changed.setdefault(key, {"table": table, "id": row["id"], "before": {}, "after": {}, "reason": []})
            for field, value in after.items():
                if row[field] != value:
                    item["before"].setdefault(field, row[field])
                    item["after"][field] = value
            if reason not in item["reason"]:
                item["reason"].append(reason)
            if table == "passages":
                item["text_sha256"] = sha(row["text"])

        for doc in documents:
            if doc["filename"] not in ("volume_1.pdf", "volume_2.pdf"):
                continue
            volume = 1 if doc["filename"] == "volume_1.pdf" else 2
            start, lesson, expected_pages = (471, 61, 475) if volume == 1 else (428, 108, 432)
            if doc["page_count"] != expected_pages:
                raise ValueError("底本页数改变，不能套用本次人工核对的范围")
            appendix_id = f"appendix-{doc['id']}-learning-outline"
            appendix_rows = [r for r in rows if r["document_id"] == doc["id"] and r["pdf_page"] >= start]
            if not appendix_rows or "后记" not in appendix_rows[0]["text"] or "学习大纲" not in appendix_rows[0]["text"]:
                raise ValueError("后记锚点与已视觉核对页面不一致")
            if not db.execute("SELECT 1 FROM units WHERE id=?", (appendix_id,)).fetchone():
                new_units.append({"id": appendix_id, "title": "后记——缠中说禅教你炒股票108课学习大纲", "kind": "compiler_appendix", "lesson_number": None, "published_at": None, "document_id": doc["id"], "start_page": start, "end_page": doc["page_count"], "processing_status": "excluded_from_author_knowledge", "note": "汇编后记及课程学习大纲；非对应末课正文。具体整理者身份未核，不作为作者直接证据，保留原文与定位。"})
            unit = dict(db.execute("SELECT * FROM units WHERE document_id=? AND lesson_number=?", (doc["id"], lesson)).fetchone())
            propose("units", unit, {"end_page": start - 1}, "将后记从课程范围分离，课程所附解盘仍保留")
            for row in appendix_rows:
                propose("passages", row, {"unit_id": appendix_id, "role": "unknown", "speaker": None, "published_at": None}, "后记/学习大纲为第三人称整理，未确认整理者身份；PDF页面视觉核对")

        article = None
        previous_doc = None
        for row in rows:
            if row["document_id"] != previous_doc:
                article = None
                previous_doc = row["document_id"]
            # Appendix changes take precedence; a course list is not a title.
            if changed.get(("passages", row["id"]), {}).get("after", {}).get("role") == "unknown":
                article = None
                continue
            lines = row["raw_text"].strip().splitlines()
            first = lines[0].strip() if lines else ""
            title = DATED_TITLE.fullmatch(first)
            explicit_commentary = first.startswith(("缠中说禅解盘", "缠中说禅看盘"))
            header_time = title.group(1) if title and not LESSON.match(first) else None
            if not header_time and explicit_commentary and len(lines) == 2 and re.fullmatch(DATE, lines[1].strip()):
                header_time = lines[1].strip()
            if header_time and row["role"] == "author_commentary" and row["speaker"] == "缠中说禅":
                article = (row["published_at"], canonical_time(header_time), row["id"])
            elif re.fullmatch(DATE, row["text"].strip()):
                # A bare timestamp may close the preceding message. Do not
                # guess its scope or shift it onto the following message.
                article = None
            elif article and (row["role"] != "author_commentary" or row["speaker"] != "缠中说禅" or row["published_at"] != article[0]):
                article = None
            if article:
                propose("passages", row, {"published_at": article[1]}, "使用本篇明确标题时间；来源标题 " + article[2])

        for suffix, speaker in (("p0074-b007", "在路上"), ("p0074-b008", "在路上"), ("p0080-b013", "中间体"), ("p0080-b014", "中间体")):
            row = next(r for r in rows if r["document_id"].startswith("volume_1-") and r["id"].endswith(suffix))
            propose("passages", row, {"role": "reader", "speaker": speaker, "published_at": None}, "读者署名/提问明确；源头年份为006，不补造缺失年份，保留原文")

        # PDF86 puts a new commentary timestamp at the preceding block's tail.
        # The following content keeps its stable text/ID; only its date is fixed.
        for suffix, timestamp in (("p0086-b003", "2006-12-27 15:29:37"), ("p0086-b004", "2006-12-28 15:45:14"), ("p0086-b005", "2006-12-28 15:45:14"), ("p0086-b006", "2006-12-28 15:45:14")):
            row = next(r for r in rows if r["document_id"].startswith("volume_1-") and r["id"].endswith(suffix))
            if row["role"] != "author_commentary" or row["speaker"] != "缠中说禅":
                raise ValueError("PDF86已复核解盘身份发生变化：" + row["id"])
            propose("passages", row, {"published_at": timestamp}, "实际查看PDF86：新时间头在前一block尾部，支配后文；不把尾部头的日期覆盖前段正文")

        # Individually reviewed commentary; these timestamps are
        # layout headers, some extracted into the preceding block's tail.
        reviewed_comment_dates = {
            "2006-11-23 12:09:31": ["p0024-b003", "p0024-b004"],
            "2006-11-23 13:42:46": ["p0024-b005"],
            "2006-11-23 15:11:58": ["p0024-b006", "p0025-b000", "p0025-b001"],
            "2007-01-10 16:22:39": ["p0107-b006", "p0107-b007"],
            "2007-01-10 22:02:27": ["p0107-b008"],
            "2007-01-12 12:02:09": ["p0114-b003"],
            "2007-01-12 15:26:45": ["p0114-b004", "p0114-b005", "p0115-b000", "p0115-b001"],
            "2007-01-15 22:40:08": ["p0120-b002", "p0120-b003"],
            "2007-01-16 15:37:18": ["p0120-b004"],
            "2007-01-16 15:51:16": ["p0120-b005", "p0120-b006", "p0120-b007"],
            "2007-01-17 15:18:53": ["p0120-b008", "p0120-b009", "p0121-b000", "p0121-b001"],
            "2007-01-22 15:27:14": ["p0136-b000", "p0136-b001", "p0136-b002", "p0137-b000", "p0137-b001", "p0137-b002"],
        }
        for timestamp, suffixes in reviewed_comment_dates.items():
            for suffix in suffixes:
                row = next(r for r in rows if r["document_id"].startswith("volume_1-") and r["id"].endswith(suffix))
                if row["role"] != "author_commentary" or row["speaker"] != "缠中说禅":
                    raise ValueError("已复核解盘身份发生变化：" + row["id"])
                propose("passages", row, {"published_at": timestamp}, "实际查看PDF24/25/107/114/115/120/121/136/137：时间头管辖其后内容，跨页保留直至下个时间头或回复栏目；只纠正日期元数据")

        for suffix, speaker in (("p0025-b004", "Nn"), ("p0025-b005", "Nn"), ("p0026-b014", "酸辣粉"), ("p0027-b000", "酸辣粉"), ("p0027-b002", "酸辣粉"), ("p0027-b003", "酸辣粉"), ("p0027-b005", None), ("p0027-b006", None)):
            row = next(r for r in rows if r["document_id"].startswith("volume_1-") and r["id"].endswith(suffix))
            propose("passages", row, {"role": "reader", "speaker": speaker, "published_at": None}, "实际查看PDF25至27：读者署名及提问在随后黄色作者署名之前；不沿用前一作者回复时间，末一提问未署名则不造姓名")

        upper_figure_notes = {
            "p0015-fig1": "第6课认沽权证后加截图；图中行情标2007-03-23，晚于2006-10-24课程；网页版权还标2008。已视觉核对，不作为课程原发时点证言，制作人未核。",
            "p0015-fig2": "第6课认购权证后加截图；图中行情标2007-03-23，晚于2006-10-24课程；网页版权还标2008。已视觉核对，不据该后期截图改写正文底线数值，制作人未核。",
            "p0016-fig1": "第6课正股后加行情图；横轴延伸至2007年4月，晚于2006-10-24课程；上方光标日期不等于全图最后行情日期。已视觉核对，制作人未核。",
            "p0022-fig1": "第8课东方金钰后加月线图；图头显示2007/11/30，晚于2006年11月课程及答疑；内嵌20061116回复、5.97元及注5月线与正文答疑2006-11-21、5.9元有差别，不视为作者更正，制作人未核。",
        }
        for suffix, note in upper_figure_notes.items():
            row = db.execute("SELECT * FROM figures WHERE document_id LIKE 'volume_1-%' AND id LIKE ?", ("%-" + suffix,)).fetchone()
            if not row:
                raise ValueError("已复核上册图像对象不存在：" + suffix)
            propose("figures", dict(row), {"origin_status": "later_annotation", "note": note}, "实际PDF15/16/22显示课程之后行情；后加时间证据与制作身份、图文含义分别记录")

        figure_notes = {
            "p0006-fig1": "后加彩色解释图；图内署名 FHSL 20080727，晚于第62课。已视觉核对，不作为作者原始配图证言。",
            "p0007-fig1": "后加彩色分型/包含解释图；原始图像裁切可见陈仁制作、2009-10-12 0:31:56水印，晚于第62课。旧日志将日期记为2009-09-10，本轮实际图像复核纠正。",
            "p0035-fig1": "后加第65课包含处理解释图；图内有FHSL 20080729署名日期，晚于2007-07-16课程。已视觉核对，不作为作者原始定义证言。",
            "p0035-fig2": "后加第65课顺序包含处理和方向解释图；图内有FHSL 20080730署名日期，晚于2007-07-16课程。已视觉核对，不以图中新增细节替代作者文字。",
            "p0052-fig3": "后加解释图；图内有陈仁制作、2008-08-14水印。已视觉核对，不作为第67课作者原始定义证言。",
            "p0053-fig1": "后加第三/第四种情况解释图；陈仁制作、2008-08-14水印。已视觉核对，保留第三方来源边界。",
            "p0053-fig2": "后加第五/第六种情况解释图；陈仁制作、2008-08-14水印。已视觉核对，保留第三方来源边界。",
            "p0054-fig1": "后加第七/第八种情况解释图；图内有陈仁制作、2008-08-15水印。已视觉核对，不作为第67课作者原始划分标准的证言。",
            "p0094-fig1": "后加标准顶与底组合形式一解释图；实际查看PDF94下部彩色图，陈仁制作及2008年日期水印晚于第71课2007年文字，不作为作者原始定义证言。",
            "p0095-fig1": "后加标准顶与底组合形式二解释图；实际查看PDF95上部彩色图，陈仁制作及2008年日期水印晚于第71课2007年文字，保留第三方解释身份。",
        }
        for suffix, note in figure_notes.items():
            row = db.execute("SELECT * FROM figures WHERE document_id LIKE 'volume_2-%' AND id LIKE ?", ("%-" + suffix,)).fetchone()
            if not row:
                raise ValueError("已复核图像对象不存在：" + suffix)
            propose("figures", dict(row), {"origin_status": "later_annotation", "note": note}, "实际PDF页面视觉核对图内署名及日期，图意不因此自动获批")
        row = db.execute("SELECT * FROM figures WHERE id='volume_2-5332cd1b6038-p0094-fig2'").fetchone()
        propose("figures", dict(row), {"note": "第71课上方黑色四图示意；作者在p0094-b002明确说最后一个图有问题、须看第81课更正。已实际查看并记录警示，原始绘制者未核，不把最后图作无条件正确例证。"}, "实际PDF94原页及邻接作者更正提示；补充警示而不批准错误图")

        operations = [x for x in changed.values() if x["after"]]
        source_ids = [x["id"] for x in operations if x["table"] == "passages"]
        affected = []
        for pid in source_ids:
            links = [dict(r) for r in db.execute("SELECT e.id evidence_id,c.id claim_id,c.review_status FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE e.passage_id=?", (pid,))]
            if links:
                affected.append({"passage_id": pid, "links": links})
        issues = [
            {"id": "source-bare-timestamps", "status": "pending", "scope": ["volume_1 PDF30/34/42/438-439", "volume_2 PDF391-408/425-427"], "reason": "裸日期与整句被当speaker、日期在前后段的作用域需逐篇核对，不用日期先后猜作者身份。"},
            {"id": "source-quoted-reader-scope", "status": "pending", "scope": ["volume_1 PDF151", "volume_2 PDF162-165"], "reason": "嵌入读者引文结束后作者叙述未恢复；需逐段回到引号和上下文确认。"},
            {"id": "source-parenthetical-note", "status": "pending", "passage_id": "volume_1-a53e99c37ca5-p0090-b002", "reason": "括号注的作者/汇编补注身份未核，不能作为一般作者规则。"},
            {"id": "source-historical-byline", "status": "pending", "scope": ["volume_1 PDF33"], "reason": "喜欢数学的女孩署名与作者身份的关系未在固定底本内确认，不自动合并作者身份。"},
        ]
        return {"stage": "B", "plan_format": 1, "schema_version": metadata["schema_version"], "base_graph_version": metadata["graph_version"], "documents": documents, "units_before": [dict(r) for r in db.execute("SELECT * FROM units ORDER BY document_id,start_page,lesson_number")], "visual_pdf_pages": {"volume_1.pdf": [80, 90, 438, 471], "volume_2.pdf": [6, 7, 52, 53, 392, 428, 429]}, "page_map": {"volume_1.pdf": {"numbered_pdf_range": [7, 470], "printed_equals_pdf_minus": 6, "printed_unrecorded_pdf_ranges": [[1, 6], [471, 475]]}, "volume_2.pdf": {"numbered_pdf_range": [6, 427], "printed_equals_pdf_minus": 5, "printed_unrecorded_pdf_ranges": [[1, 5], [428, 432]]}}, "new_units": new_units, "operations": operations, "affected_references": affected, "impact": {"reviewed_evidence": sum(x["review_status"] == "reviewed" for a in affected for x in a["links"]), "reviews_for_affected_claims": sorted({r[0] for a in affected for x in a["links"] for r in db.execute("SELECT id FROM reviews WHERE claim_id=?", (x["claim_id"],))}), "coverage_units": sorted({r["unit_id"] for r in rows if r["id"] in source_ids and r["unit_id"]}), "fts_text_changes": 0, "passage_ids_changed": 0}, "pending": issues, "semantic_completion": False}


def apply_plan(root, plan):
    root = root.resolve()
    with open_ro(root) as source:
        base = json.loads(source.execute("SELECT value FROM metadata WHERE key='graph_version'").fetchone()[0])
        if base != plan["base_graph_version"]:
            raise ValueError("计划所依据的图谱版本已经变化，先重新核对")
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        if manifest["graph_version"] != base or manifest["schema_version"] != plan["schema_version"]:
            raise ValueError("现有数据库/manifest版本不一致，不能应用来源修订")
        for document in plan["documents"]:
            package_pdf = (root / document["resource_path"]).resolve()
            if not package_pdf.is_relative_to(root) or hashlib.sha256(package_pdf.read_bytes()).hexdigest() != document["sha256"]:
                raise ValueError("底本资源路径或hash改变：" + document["filename"])
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backup_dir = root.parent / "backups" / (stamp + "-source-structure")
        backup_dir.mkdir(parents=True, exist_ok=False)
        with sqlite3.connect(backup_dir / "graph.sqlite") as backup:
            source.backup(backup)
        shutil.copy2(root / "manifest.json", backup_dir / "manifest.json")
        (backup_dir / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    db = sqlite3.connect(root / "graph.sqlite")
    db.row_factory = sqlite3.Row
    now = datetime.now(timezone.utc).isoformat()
    rejected = []
    try:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("BEGIN IMMEDIATE")
        if json.loads(db.execute("SELECT value FROM metadata WHERE key='graph_version'").fetchone()[0]) != plan["base_graph_version"]:
            raise ValueError("备份后图谱版本变化，拒绝应用旧计划")
        for item in plan["operations"]:
            table, fields = item["table"], item["after"]
            if table not in EDITABLE or not set(fields) <= EDITABLE[table] or set(fields) != set(item["before"]):
                raise ValueError("计划包含不允许的字段变更")
            current = db.execute(f"SELECT * FROM {table} WHERE id=?", (item["id"],)).fetchone()
            if not current or any(current[k] != v for k, v in item["before"].items()):
                raise ValueError("来源对象已变化：" + item["id"])
            if table == "passages":
                if sha(current["text"]) != item["text_sha256"]:
                    raise ValueError("原文已变化：" + item["id"])
                if db.execute("SELECT 1 FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE e.passage_id=? AND c.review_status='reviewed'", (item["id"],)).fetchone():
                    raise ValueError("已复核证据需单独迁移复核，不能批量修改：" + item["id"])
        for unit in plan["new_units"]:
            db.execute("INSERT INTO units(id,title,kind,lesson_number,published_at,document_id,start_page,end_page,processing_status,note) VALUES(:id,:title,:kind,:lesson_number,:published_at,:document_id,:start_page,:end_page,:processing_status,:note)", unit)
        for item in plan["operations"]:
            fields = item["after"]
            db.execute(f"UPDATE {item['table']} SET " + ",".join(k + "=?" for k in fields) + " WHERE id=?", (*fields.values(), item["id"]))
        # Preserve rejected candidates/evidence for audit; do not approve them
        # or silently delete source history.
        invalid_ids = {x["id"] for x in plan["operations"] if x["table"] == "passages" and x["after"].get("role") in ("reader", "unknown")}
        for pid in sorted(invalid_ids):
            for claim in db.execute("SELECT c.* FROM claims c JOIN evidence e ON e.claim_id=c.id WHERE e.passage_id=? AND c.id LIKE 'candidate-%' AND c.review_status='pending'", (pid,)).fetchall():
                note = "阶段B来源纠正：原候选误用了读者发言或身份未核后记，不能作为作者技术命题；保留原文与证据供审计。"
                db.execute("UPDATE claims SET review_status='rejected',ambiguity_status='source_attribution_rejected',review_note=? WHERE id=?", (note, claim["id"]))
                checks = {"review_type": "source_structure", "semantic_approval": False, "passage_id": pid, "previous_review_status": "pending", "plan_base_version": plan["base_graph_version"]}
                rid = "review-" + sha(claim["id"] + compact(checks))[:16]
                db.execute("INSERT INTO reviews VALUES(?,?,?,?,?,?,?)", (rid, claim["id"], SOURCE_REVIEWER, now, compact(checks), "rejected", note))
                rejected.append(claim["id"])
        bad_fts = db.execute("SELECT count(*) FROM passages p LEFT JOIN passage_fts f ON f.passage_id=p.id WHERE f.passage_id IS NULL OR f.text!=p.text").fetchone()[0]
        if bad_fts or db.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("来源变更后索引或外键检查失败")
        db.execute("INSERT OR REPLACE INTO metadata VALUES('source_structure_revision','1')")
        db.execute("INSERT OR REPLACE INTO metadata VALUES('semantic_completion','false')")
        version = refresh_version(db)
        counts = {t: db.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in ("documents", "pages", "units", "passages", "figures", "concepts", "claims", "relations", "reviews")}
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update(graph_version=version, counts=counts, source_structure_revision=1, updated_at=now)
    temporary = root / "manifest.next.json"
    temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(manifest_path)
    return {"stage": "B-source-corrections", "base_graph_version": plan["base_graph_version"], "graph_version": version, "backup_directory": str(backup_dir), "new_units": len(plan["new_units"]), "source_operations": len(plan["operations"]), "rejected_candidates": rejected, "pending": plan["pending"], "reviewed_claims_changed": 0, "text_or_geometry_changed": False}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--kb", required=True, type=Path)
    parser.add_argument("--output", type=Path, help="explicitly save the read-only review plan")
    parser.add_argument("--apply", type=Path, help="apply a previously reviewed plan, with backup")
    args = parser.parse_args()
    result = apply_plan(args.kb, json.loads(args.apply.read_text(encoding="utf-8"))) if args.apply else build_plan(args.kb)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if not args.apply and args.output:
        print(compact({"plan": str(args.output), "base_graph_version": result["base_graph_version"], "operations": len(result["operations"]), "new_units": len(result["new_units"]), "affected_references": len(result["affected_references"])}))
    else:
        print(compact(result))
