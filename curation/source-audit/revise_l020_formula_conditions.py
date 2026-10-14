"""Explicit, version-locked amendment of one reviewed formula's alternatives.

The ordinary importer continues to prohibit silent semantic overwrites. This
source-specific plan records the prior record, dependency check and root review;
--apply requires that exact plan and saves a recoverable database snapshot.
"""
import argparse
import hashlib
import json
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from graph_release import refresh_version, update_manifest

CLAIM = "upper-l020-center-formula-reduced"
PASSAGE = "volume_1-a53e99c37ca5-p0098-b005"
BEFORE = ["A/B/C高低点分别a1/a2、b1/b2、c1/c2", "回升形成时a1=b1、b2=c2", "回调形成时a2=b2、b1=c1"]
AFTER = [BEFORE[0], "以下两种形成情形择一适用：回升形成时a1=b1、b2=c2；或回调形成时a2=b2、b1=c1；不是要求两组等式同时成立"]
NOTE = "主代理阶段C实际复看PDF98下方黑字原文：两种形成情形是替代分支，不能将回升与回调两组等式当成联合前提。只澄清conditions的逻辑组织，公式、命题文字、原始证据、图源边界均保留。"
REVIEWER = "主代理 / 阶段C第20课中枢公式条件修订复核"


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def ro(root):
    db = sqlite3.connect((root / "graph.sqlite").as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    return db


def snapshot(db):
    claim = dict(db.execute("SELECT * FROM claims WHERE id=?", (CLAIM,)).fetchone())
    evidence = [dict(r) for r in db.execute("SELECT * FROM evidence WHERE claim_id=? ORDER BY id", (CLAIM,))]
    dependencies = {
        "inferences": [dict(r) for r in db.execute("SELECT id,derivation FROM claims WHERE kind='inferred'") if CLAIM in json.loads(r["derivation"]).get("supporting_claim_ids", [])],
        "relations": [dict(r) for r in db.execute("SELECT * FROM relations") if CLAIM in json.loads(r["claim_ids"])],
    }
    return claim, evidence, dependencies


def plan(root):
    with ro(root) as db:
        meta = {r["key"]: json.loads(r["value"]) for r in db.execute("SELECT * FROM metadata")}
        before, evidence, dependencies = snapshot(db)
        assert before["review_status"] == "reviewed" and json.loads(before["conditions"]) == BEFORE
        assert not dependencies["inferences"] and not dependencies["relations"], "依赖项需先逐项复核"
        source = dict(db.execute("SELECT * FROM passages WHERE id=?", (PASSAGE,)).fetchone())
        assert source["role"] == "author_body" and source["speaker"] == "缠中说禅"
        assert "对于第一种有a1=b1,b2=c2；对第二种有a2=b2,b1=c1。但无论是哪种情况" in source["text"]
        assert len(evidence) == 1 and evidence[0]["passage_id"] == PASSAGE
        doc = dict(db.execute("SELECT * FROM documents WHERE id=?", (source["document_id"],)).fetchone())
    return {"stage": "C", "run_mode": "authorized_reviewed_claim_amendment", "schema_version": meta["schema_version"], "base_graph_version": meta["graph_version"], "claim_id": CLAIM, "before": before, "evidence_before": evidence, "dependencies": dependencies, "source_text_sha256": hashlib.sha256(source["text"].encode()).hexdigest(), "document": doc, "after": {"conditions": encode(AFTER), "review_note": before["review_note"] + " " + NOTE}, "reviewer": REVIEWER, "review_note": NOTE, "visual_pdf_pages": [98], "semantic_review_by": "root", "automatic_semantic_proof_claimed": False}


def apply(root, data):
    assert data["claim_id"] == CLAIM and data["reviewer"] == REVIEWER
    assert set(data["after"]) == {"conditions", "review_note"}
    assert json.loads(data["after"]["conditions"]) == AFTER
    assert data["after"]["review_note"] == data["before"]["review_note"] + " " + NOTE
    assert plan(root) == data, "当前记录、依赖或版本已变化；不能使用旧修订计划"
    doc = data["document"]; pdf = (root / doc["resource_path"]).resolve()
    assert pdf.is_relative_to(root) and hashlib.sha256(pdf.read_bytes()).hexdigest() == doc["sha256"]
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["graph_version"] == data["base_graph_version"]
    now = datetime.now(timezone.utc)
    backup = root.parent / "backups" / (now.strftime("%Y%m%dT%H%M%S%fZ") + "-l020-reviewed-amendment")
    backup.mkdir(parents=True)
    with ro(root) as source, sqlite3.connect(backup / "graph.sqlite") as dest:
        source.backup(dest)
    shutil.copy2(root / "manifest.json", backup / "manifest.json")
    (backup / "amendment-plan.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    with sqlite3.connect(root / "graph.sqlite") as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("BEGIN IMMEDIATE")
        assert json.loads(db.execute("SELECT value FROM metadata WHERE key='graph_version'").fetchone()[0]) == data["base_graph_version"]
        assert snapshot(db) == (data["before"], data["evidence_before"], data["dependencies"])
        db.execute("UPDATE claims SET conditions=?,review_note=? WHERE id=?", (data["after"]["conditions"], data["after"]["review_note"], CLAIM))
        checks = {"review_type": "explicit_reviewed_claim_amendment", "base_graph_version": data["base_graph_version"], "before": data["before"], "after": data["after"], "dependency_recheck": data["dependencies"], "source_passage_id": PASSAGE, "evidence_preserved": True, "semantic_entailment_automatically_proven": False, "visual_pdf_pages": [98], "independent_review_claimed": False}
        rid = "review-" + hashlib.sha256(encode(checks).encode()).hexdigest()[:16]
        db.execute("INSERT INTO reviews VALUES(?,?,?,?,?,?,?)", (rid, CLAIM, REVIEWER, now.isoformat(), encode(checks), "reviewed", NOTE))
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
        version = refresh_version(db)
        counts = {t: db.execute("SELECT count(*) FROM " + t).fetchone()[0] for t in ("documents", "pages", "units", "passages", "figures", "concepts", "claims", "evidence", "relations", "reviews")}
    update_manifest(root, version, counts=counts, updated_at=now.isoformat())
    return {"stage": "C", "base_graph_version": data["base_graph_version"], "graph_version": version, "changed_claim_id": CLAIM, "changed_fields": ["conditions", "review_note"], "review_id": rid, "backup_directory": str(backup), "evidence_preserved": True, "dependent_inferences": 0, "dependent_relations": 0, "reviewed_claims_added": 0}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--kb", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--apply", type=Path)
    args = parser.parse_args(); root = args.kb.resolve()
    result = apply(root, json.loads(args.apply.read_text(encoding="utf-8"))) if args.apply else plan(root)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(encode({k: v for k, v in result.items() if k not in ("before", "evidence_before", "document")}))
