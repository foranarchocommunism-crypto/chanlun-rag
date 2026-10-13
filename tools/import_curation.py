"""Import explicitly reviewed source batches, validating every evidence anchor."""
import argparse
import gzip
import json
import sqlite3
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from extract_corpus import digest, j
from graph_release import refresh_version


def import_batches(root, paths):
    db = sqlite3.connect(root / "graph.sqlite")
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    records = []
    for path in paths:
        for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
            if line.strip():
                records.append((json.loads(line), path, line_number))
    if len({r[0]["id"] for r in records}) != len(records):
        raise RuntimeError("批次中存在重复命题ID")
    @lru_cache(maxsize=8)
    def geometry(doc_id, page_number):
        relative = db.execute("SELECT geometry_path FROM pages WHERE document_id=? AND pdf_page=?", (doc_id, page_number)).fetchone()[0]
        with gzip.open(root / relative, "rt", encoding="utf-8") as f:
            return json.load(f)["chars"]

    def evidence_boxes(passage, indices):
        chars = geometry(passage["document_id"], passage["pdf_page"])
        boxes = []
        last_top = None
        for index in dict.fromkeys(indices):
            if index < 0 or index >= len(chars):
                raise RuntimeError("字符定位索引无效：" + passage["id"])
            _, x0, top, x1, bottom = chars[index]
            if last_top is None or abs(top - last_top) > 3:
                boxes.append([x0, top, x1, bottom])
                last_top = top
            else:
                box = boxes[-1]
                box[0], box[1], box[2], box[3] = min(box[0], x0), min(box[1], top), max(box[2], x1), max(box[3], bottom)
        return boxes

    existing = [dict(r) for r in db.execute("SELECT * FROM concepts")]
    labels = {r["label"]: r["id"] for r in existing}
    aliases = {alias: r["id"] for r in existing for alias in json.loads(r["aliases"])}
    def concept_id(label):
        if label in labels:
            return labels[label]
        if label in aliases:
            return aliases[label]
        cid = "concept-" + digest(label)
        db.execute("INSERT INTO concepts(id,label,aliases,description) VALUES(?,?,?,?)", (cid, label, "[]", ""))
        labels[label] = cid
        return cid

    now = datetime.now(timezone.utc).isoformat()
    db.execute("BEGIN IMMEDIATE")
    imported, errors = [], []
    for record, path, line_number in records:
        claim_id = record["id"]
        try:
            for key in ("text", "kind", "conditions", "exceptions", "concepts", "review_note", "evidence", "importance_level", "importance_reason"):
                if key not in record:
                    raise ValueError("缺少 " + key)
            if record["kind"] not in ("explicit", "inferred"):
                raise ValueError("未知命题类型")
            if record["importance_level"] not in (1, 2, 3, 4) or not record["importance_reason"].strip():
                raise ValueError("重要性必须是1-4级并附整理理由")
            if not record["text"].strip() or not record["review_note"].strip() or not record["evidence"]:
                raise ValueError("命题、复核记录及证据均不能为空")
            derivation = record.get("derivation", {})
            if record["kind"] == "inferred" and (not derivation.get("supporting_claim_ids") or not derivation.get("explanation")):
                raise ValueError("推论缺少前提命题或推导说明")
            evidence_rows = []
            for n, citation in enumerate(record["evidence"]):
                passage = db.execute("SELECT * FROM passages WHERE id=?", (citation["passage_id"],)).fetchone()
                if not passage:
                    raise ValueError("原文段落不存在：" + citation["passage_id"])
                if passage["role"] not in ("author_body", "author_reply") or passage["speaker"] != "缠中说禅":
                    raise ValueError("引用发言者未确认是作者正文/技术回复：" + citation["passage_id"] + " / " + str(passage["role"]) + " / " + str(passage["speaker"]))
                quote = citation["quote"]
                begin = passage["text"].find(quote) if "quote_start" not in citation else citation["quote_start"]
                if not quote or begin < 0 or passage["text"][begin:begin + len(quote)] != quote:
                    raise ValueError("引文不是原文精确连续子串：" + passage["id"])
                end = begin + len(quote)
                mapping = json.loads(passage["normalized_map"])
                if len(mapping) != len(passage["text"]):
                    raise ValueError("归一文本映射长度不一致：" + passage["id"])
                selected = mapping[begin:end]
                figures = citation.get("figure_ids", [])
                for fid in figures:
                    figure = db.execute("SELECT * FROM figures WHERE id=?", (fid,)).fetchone()
                    if not figure or figure["document_id"] != passage["document_id"]:
                        raise ValueError("配图不存在或来自另一文档：" + fid)
                if figures and not record.get("figure_review_note"):
                    raise ValueError("配图相关结论缺少单独的视觉复核记录")
                span = {"document_id": passage["document_id"], "pdf_page": passage["pdf_page"], "char_indices": selected, "boxes": evidence_boxes(passage, selected), "coordinate_system": "pdf_points_top_left"}
                eid = "evidence-" + digest(claim_id + ":" + str(n) + ":" + passage["id"])
                evidence_rows.append((eid, claim_id, passage["id"], quote, begin, end, j([span]), j(figures)))
            concept_ids = list(dict.fromkeys(concept_id(label) for label in record["concepts"]))
            db.execute("INSERT INTO claims(id,text,kind,conditions,exceptions,concept_ids,review_status,ambiguity_status,review_note,derivation,importance_level,importance_reason) VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET text=excluded.text,kind=excluded.kind,conditions=excluded.conditions,exceptions=excluded.exceptions,concept_ids=excluded.concept_ids,review_status=excluded.review_status,ambiguity_status=excluded.ambiguity_status,review_note=excluded.review_note,derivation=excluded.derivation,importance_level=excluded.importance_level,importance_reason=excluded.importance_reason", (claim_id, record["text"], record["kind"], j(record["conditions"]), j(record["exceptions"]), j(concept_ids), "reviewed", record.get("ambiguity_status", "none"), record["review_note"], j(derivation), record["importance_level"], record["importance_reason"]))
            db.execute("DELETE FROM evidence WHERE claim_id=?", (claim_id,))
            db.executemany("INSERT INTO evidence VALUES(?,?,?,?,?,?,?,?)", evidence_rows)
            for relation in record.get("relations", []):
                source, target = concept_id(relation["source"]), concept_id(relation["target"])
                relation_id = "relation-" + digest(source + ":" + relation["type"] + ":" + target)
                previous = db.execute("SELECT claim_ids FROM relations WHERE id=?", (relation_id,)).fetchone()
                supporters = list(dict.fromkeys((json.loads(previous[0]) if previous else []) + [claim_id]))
                db.execute("INSERT INTO relations(id,source,target,type,claim_ids,review_status) VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET claim_ids=excluded.claim_ids,review_status='reviewed'", (relation_id, source, target, relation["type"], j(supporters), "reviewed"))
            review_id = "review-" + digest(claim_id + j(record))
            checks = {"quote_exact_match": True, "author_identity": True, "source_geometry": True, "semantic_review_note": record["review_note"], "figure_review_note": record.get("figure_review_note"), "curation_file": path.name, "line": line_number}
            db.execute("INSERT OR IGNORE INTO reviews VALUES(?,?,?,?,?,?,?)", (review_id, claim_id, record.get("reviewer", "GPT-6.1 Sol xhigh / source curation"), now, j(checks), "reviewed", record["review_note"]))
            imported.append(claim_id)
        except Exception as error:
            errors.append({"id": claim_id, "file": str(path), "line": line_number, "error": str(error)})
    if errors:
        db.rollback()
        db.close()
        raise RuntimeError(json.dumps({"batch_rejected_atomically": True, "errors": errors}, ensure_ascii=False, indent=2))
    for record, _, _ in records:
        for premise in record.get("derivation", {}).get("supporting_claim_ids", []):
            if not db.execute("SELECT 1 FROM claims WHERE id=? AND review_status='reviewed'", (premise,)).fetchone():
                db.rollback()
                raise RuntimeError("推论前提未复核或不存在：" + premise)
    db.execute("INSERT OR REPLACE INTO metadata VALUES('semantic_completion','false')")
    for coverage_path in sorted((Path(__file__).parents[1] / "curation").glob("*/coverage.jsonl")):
        for line in coverage_path.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip():
                continue
            log = json.loads(line)
            read_complete = log.get("whole_lesson_semantic_read_complete", log.get("full_lesson_read_complete", False))
            extraction_complete = log.get("technical_extraction_complete", False)
            status = "semantic_extraction_complete" if read_complete and extraction_complete and not log.get("pending") else "semantic_read_with_pending" if read_complete else "semantic_read_partial"
            lesson_number = log.get("lesson_number", log.get("lesson"))
            if lesson_number is None:
                raise ValueError("覆盖日志缺少lesson_number：" + str(coverage_path))
            db.execute("UPDATE units SET processing_status=?,note=? WHERE lesson_number=?", (status, j(log), lesson_number))
    for concept in db.execute("SELECT id FROM concepts").fetchall():
        supporting = db.execute("SELECT id,importance_level FROM claims WHERE review_status='reviewed' AND instr(concept_ids,?)>0 AND importance_level IS NOT NULL ORDER BY importance_level,id", (concept["id"],)).fetchall()
        if supporting:
            level = supporting[0]["importance_level"]
            reason = "按关联已复核命题最高重要性汇总；依据：" + "、".join(r["id"] for r in supporting if r["importance_level"] == level)[:500]
            db.execute("UPDATE concepts SET importance_level=?,importance_reason=? WHERE id=?", (level, reason, concept["id"]))
    for relation in db.execute("SELECT id,claim_ids FROM relations").fetchall():
        supporters = [db.execute("SELECT id,importance_level FROM claims WHERE id=? AND review_status='reviewed'", (cid,)).fetchone() for cid in json.loads(relation["claim_ids"])]
        graded = [r for r in supporters if r and r["importance_level"] is not None]
        if graded:
            db.execute("UPDATE relations SET importance_level=?,importance_reason=? WHERE id=?", (min(r["importance_level"] for r in graded), "按支持该关系的已复核命题最高重要性汇总", relation["id"]))
    version = refresh_version(db)
    db.commit()
    counts = {t: db.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in ("documents", "pages", "units", "passages", "figures", "concepts", "claims", "relations", "reviews")}
    reviewed_count = db.execute("SELECT count(*) FROM claims WHERE review_status='reviewed'").fetchone()[0]
    db.close()
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update(graph_version=version, counts=counts, reviewed_claims=reviewed_count, stage="semantic_review_in_progress", updated_at=now)
    temporary = root / "manifest.next.json"
    temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(manifest_path)
    report = {"graph_version": version, "imported": imported, "reviewed_claims": reviewed_count, "errors": []}
    out = Path(__file__).parents[1] / "build"
    out.mkdir(exist_ok=True)
    (out / "last-curation-import.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(j(report))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--kb", type=Path, required=True)
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()
    import_batches(args.kb, args.files)
