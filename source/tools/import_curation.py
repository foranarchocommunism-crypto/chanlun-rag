"""Preflight reviewed source batches in read-only mode, then import atomically."""
import argparse
import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from curation_contract import digest, j, validate_records
from graph_release import refresh_version


def load_records(paths):
    records, hashes = [], {}
    for path in paths:
        raw = path.read_bytes()
        hashes[str(path)] = hashlib.sha256(raw).hexdigest()
        for line_number, line in enumerate(raw.decode("utf-8-sig").splitlines(), 1):
            if line.strip():
                records.append((json.loads(line), path, line_number))
    if not records:
        raise ValueError("批次没有记录")
    return records, hashes


def import_batches(root, paths, check=False):
    root = root.resolve()
    records, batch_hashes = load_records(paths)
    with closing(sqlite3.connect((root / "graph.sqlite").as_uri() + "?mode=ro", uri=True)) as readonly:
        readonly.row_factory = sqlite3.Row
        readonly.execute("BEGIN")
        metadata = {r["key"]: json.loads(r["value"]) for r in readonly.execute("SELECT * FROM metadata")}
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        if manifest["graph_version"] != metadata["graph_version"] or manifest["schema_version"] != metadata["schema_version"]:
            raise ValueError("图谱数据库与manifest版本不一致")
        prepared = validate_records(readonly, root, records)
    if check:
        report = {"run_mode": "readonly", "graph_version": metadata["graph_version"], "records_checked": len(prepared), "batch_sha256": batch_hashes, "machine_checks_pass": True, "semantic_entailment_proven": False, "visual_interpretation_proven": False, "writes": False}
        print(j(report))
        return report

    now = datetime.now(timezone.utc).isoformat()
    db = sqlite3.connect(root / "graph.sqlite")
    db.row_factory = sqlite3.Row
    imported = []
    try:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("BEGIN IMMEDIATE")
        if json.loads(db.execute("SELECT value FROM metadata WHERE key='graph_version'").fetchone()[0]) != metadata["graph_version"]:
            raise ValueError("只读预检后图谱版本改变，需重新预检")
        for path in paths:
            if hashlib.sha256(path.read_bytes()).hexdigest() != batch_hashes[str(path)]:
                raise ValueError("只读预检后整理文件已改变")
        existing = [dict(r) for r in db.execute("SELECT * FROM concepts")]
        labels = {r["label"]: r["id"] for r in existing}
        aliases = {a: r["id"] for r in existing for a in json.loads(r["aliases"])}

        def concept_id(label):
            if label in labels:
                return labels[label]
            if label in aliases:
                return aliases[label]
            cid = "concept-" + digest(label)
            db.execute("INSERT INTO concepts(id,label,aliases,description) VALUES(?,?,?,?)", (cid, label, "[]", ""))
            labels[label] = cid
            return cid

        for item in prepared:
            record, path, line_number = item["record"], item["path"], item["line"]
            cid = record["id"]
            concept_ids = list(dict.fromkeys(concept_id(label) for label in record["concepts"]))
            db.execute("INSERT INTO claims(id,text,kind,conditions,exceptions,concept_ids,review_status,ambiguity_status,review_note,derivation,importance_level,importance_reason) VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET text=excluded.text,kind=excluded.kind,conditions=excluded.conditions,exceptions=excluded.exceptions,concept_ids=excluded.concept_ids,review_status=excluded.review_status,ambiguity_status=excluded.ambiguity_status,review_note=excluded.review_note,derivation=excluded.derivation,importance_level=excluded.importance_level,importance_reason=excluded.importance_reason", (cid, record["text"], record["kind"], j(record["conditions"]), j(record["exceptions"]), j(concept_ids), "reviewed", record.get("ambiguity_status", "none"), record["review_note"], j(record.get("derivation", {})), record["importance_level"], record["importance_reason"]))
            db.execute("DELETE FROM evidence WHERE claim_id=?", (cid,))
            for anchor in item["anchors"]:
                db.execute("INSERT INTO evidence VALUES(?,?,?,?,?,?,?,?)", (anchor["id"], cid, anchor["passage_id"], anchor["quote"], anchor["begin"], anchor["end"], j([anchor["span"]]), j(anchor["figure_ids"])))
            for relation in record.get("relations", []):
                source, target = concept_id(relation["source"]), concept_id(relation["target"])
                rid = "relation-" + digest(source + ":" + relation["type"] + ":" + target)
                previous = db.execute("SELECT claim_ids FROM relations WHERE id=?", (rid,)).fetchone()
                supporters = list(dict.fromkeys((json.loads(previous[0]) if previous else []) + [cid]))
                db.execute("INSERT INTO relations(id,source,target,type,claim_ids,review_status) VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET claim_ids=excluded.claim_ids,review_status='reviewed'", (rid, source, target, relation["type"], j(supporters), "reviewed"))
            checks = {
                "machine_checks": {"quote_codepoints_exact": True, "source_mapping": True, "geometry": True, "allowed_source_role_and_speaker": True, "inference_graph_acyclic": True},
                "submitted_reviewer": record["reviewer"],
                "reviewer_identity_independently_verified": False,
                "independent_review_claimed": False,
                "semantic_review_note": record["review_note"],
                "semantic_entailment_automatically_proven": False,
                "figure_review_note": record.get("figure_review_note"),
                "figure_origins": {fid: origin for a in item["anchors"] for fid, origin in a["figure_origins"].items()},
                "source_roles": {a["passage_id"]: a["source_role"] for a in item["anchors"]},
                "curation_file": path.name, "line": line_number,
                "batch_sha256": batch_hashes[str(path)],
                "claim_record_sha256": hashlib.sha256(j(record).encode("utf-8")).hexdigest(),
                "base_graph_version": metadata["graph_version"],
            }
            rid = "review-" + digest(cid + j(record))
            db.execute("INSERT OR IGNORE INTO reviews VALUES(?,?,?,?,?,?,?)", (rid, cid, record["reviewer"], now, j(checks), "reviewed", record["review_note"]))
            imported.append(cid)
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
                db.execute("UPDATE units SET processing_status=?,note=? WHERE kind='lesson' AND lesson_number=?", (status, j(log), lesson_number))
        for concept in db.execute("SELECT id FROM concepts").fetchall():
            supporting = [r for r in db.execute("SELECT id,importance_level,concept_ids FROM claims WHERE review_status='reviewed' AND importance_level IS NOT NULL ORDER BY importance_level,id") if concept["id"] in json.loads(r["concept_ids"])]
            if supporting:
                level = supporting[0]["importance_level"]
                reason = "按关联已复核命题最高重要性汇总；依据：" + "、".join(r["id"] for r in supporting if r["importance_level"] == level)[:500]
                db.execute("UPDATE concepts SET importance_level=?,importance_reason=? WHERE id=?", (level, reason, concept["id"]))
        for relation in db.execute("SELECT id,claim_ids FROM relations").fetchall():
            supporters = [db.execute("SELECT importance_level FROM claims WHERE id=? AND review_status='reviewed'", (cid,)).fetchone() for cid in json.loads(relation["claim_ids"])]
            graded = [r for r in supporters if r and r["importance_level"] is not None]
            if graded:
                db.execute("UPDATE relations SET importance_level=?,importance_reason=? WHERE id=?", (min(r["importance_level"] for r in graded), "按支持该关系的已复核命题最高重要性汇总", relation["id"]))
        if db.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("导入后外键检查失败")
        version = refresh_version(db)
        counts = {t: db.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in ("documents", "pages", "units", "passages", "figures", "concepts", "claims", "relations", "reviews")}
        reviewed_count = db.execute("SELECT count(*) FROM claims WHERE review_status='reviewed'").fetchone()[0]
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    manifest.update(graph_version=version, counts=counts, reviewed_claims=reviewed_count, stage="semantic_review_in_progress", updated_at=now)
    temporary = root / "manifest.next.json"
    temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(root / "manifest.json")
    report = {"graph_version": version, "imported": imported, "reviewed_claims": reviewed_count, "errors": []}
    out = Path(__file__).parents[1] / "build"
    out.mkdir(exist_ok=True)
    (out / "last-curation-import.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(j(report))
    return report


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--kb", type=Path, required=True)
    parser.add_argument("--check", action="store_true", help="read-only preflight; no database, manifest or report writes")
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()
    import_batches(args.kb, args.files, check=args.check)
