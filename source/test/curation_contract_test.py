"""Synthetic contract fixtures only; never read or mutate the formal corpus."""
import contextlib
import copy
import gzip
import hashlib
import io
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from curation_contract import j, validate_records, validate_shape
from import_curation import import_batches


class SyntheticCurationContract(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="synthetic-chan-contract-")
        self.root = Path(self.temporary.name)
        self.db = sqlite3.connect(self.root / "graph.sqlite")
        self.db.row_factory = sqlite3.Row
        self.db.executescript((Path(__file__).parents[1] / "contracts/schema.sql").read_text(encoding="utf-8"))
        self.db.executemany("INSERT INTO metadata VALUES(?,?)", [("schema_version", j("1.1.0")), ("graph_version", j("synthetic-version"))])
        self.db.execute("INSERT INTO documents VALUES(?,?,?,?,?)", ("synthetic-doc", "synthetic.pdf", "0" * 64, 1, "sources/synthetic.pdf"))
        self.db.execute("INSERT INTO units(id,title,kind,lesson_number,document_id,start_page,end_page) VALUES(?,?,?,?,?,?,?)", ("synthetic-unit", "合成测试", "lesson", 1, "synthetic-doc", 1, 1))
        self.text = "若类型已完成，则规则甲成立；例外乙除外。甲😀乙。"
        chars = [[c, (i % 20) * 4 + 1, (i // 20) * 10 + 1, (i % 20) * 4 + 4, (i // 20) * 10 + 9] for i, c in enumerate(self.text)]
        (self.root / "geometry").mkdir()
        with gzip.open(self.root / "geometry/synthetic.json.gz", "wt", encoding="utf-8") as stream:
            json.dump({"width": 100, "height": 100, "chars": chars}, stream, ensure_ascii=False)
        self.db.execute("INSERT INTO pages VALUES(?,?,?,?,?,?,?,?)", ("synthetic-page", "synthetic-doc", 1, None, 100, 100, self.text, "geometry/synthetic.json.gz"))
        self.db.execute("INSERT INTO passages VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", ("synthetic-passage", "synthetic-unit", "synthetic-doc", 1, 0, "author_body", "缠中说禅", None, self.text, self.text, j([[1, 1, 80, 19]]), j(list(range(len(self.text)))), j(list(range(len(self.text))))))
        self.db.commit()
        (self.root / "manifest.json").write_text(j({"schema_version": "1.1.0", "graph_version": "synthetic-version"}), encoding="utf-8")
        self.record = {"id": "synthetic-claim", "text": "合成规则：类型完成且不属于例外乙时规则甲成立。", "kind": "explicit", "conditions": ["类型已完成"], "exceptions": ["例外乙"], "concepts": ["合成规则甲"], "review_note": "synthetic fixture；语境：测试材料；适用条件：仅供契约测试。", "reviewer": "synthetic contract fixture", "evidence": [{"passage_id": "synthetic-passage", "quote": self.text}], "importance_level": 1, "importance_reason": "synthetic fixture"}

    def tearDown(self):
        self.db.close()
        self.temporary.cleanup()

    def validate(self, *records):
        return validate_records(self.db, self.root, [(r, Path("synthetic.jsonl"), i + 1) for i, r in enumerate(records)])

    def test_valid_anchor_and_non_bmp_codepoints(self):
        record = copy.deepcopy(self.record)
        record["evidence"][0]["quote"] = "😀乙"
        result = self.validate(record)[0]["anchors"][0]
        self.assertEqual(result["begin"], self.text.index("😀乙"))
        self.assertEqual(result["end"] - result["begin"], 2)
        self.assertEqual(result["span"]["char_indices"], [self.text.index("😀"), self.text.index("😀") + 1])

    def test_boolean_grade_and_wrong_array_types_rejected(self):
        for field, value in (("importance_level", True), ("conditions", "已完成"), ("exceptions", [1]), ("concepts", []), ("reviewer", "")):
            with self.subTest(field=field):
                record = copy.deepcopy(self.record)
                record[field] = value
                with self.assertRaises(ValueError):
                    validate_shape(record)

    def test_unknown_fields_and_default_reviewer_rejected(self):
        record = copy.deepcopy(self.record)
        record["review_status"] = "reviewed"
        with self.assertRaises(ValueError):
            validate_shape(record)
        record.pop("review_status")
        record["reviewer"] = "GPT-6.1 Sol xhigh / source curation"
        with self.assertRaises(ValueError):
            validate_shape(record)

    def test_commentary_requires_explicit_context_note(self):
        self.db.execute("UPDATE passages SET role='author_commentary'")
        self.validate(self.record)
        record = copy.deepcopy(self.record)
        record["review_note"] = "只说已经检查"
        with self.assertRaisesRegex(ValueError, "语境"):
            self.validate(record)

    def test_reader_and_unknown_cannot_be_author_evidence(self):
        for role in ("reader", "unknown"):
            self.db.execute("UPDATE passages SET role=?", (role,))
            with self.assertRaisesRegex(ValueError, "作者"):
                self.validate(self.record)

    def test_in_range_wrong_character_map_is_rejected(self):
        mapping = list(range(len(self.text)))
        mapping[0] = 1
        self.db.execute("UPDATE passages SET normalized_map=?", (j(mapping),))
        with self.assertRaisesRegex(ValueError, "重建"):
            self.validate(self.record)

    def test_alias_self_loop_and_missing_endpoint_scope(self):
        self.db.execute("INSERT INTO concepts(id,label,aliases) VALUES(?,?,?)", ("synthetic-concept", "合成规则甲", j(["合成别名"])))
        record = copy.deepcopy(self.record)
        record["relations"] = [{"source": "合成规则甲", "target": "合成别名", "type": "related"}]
        with self.assertRaisesRegex(ValueError, "自环"):
            self.validate(record)
        record["relations"][0]["target"] = "未登记对象"
        with self.assertRaisesRegex(ValueError, "概念归属"):
            self.validate(record)

    def test_inference_cycle_and_missing_premise_rejected(self):
        a, b = copy.deepcopy(self.record), copy.deepcopy(self.record)
        a.update(id="synthetic-a", kind="inferred", derivation={"supporting_claim_ids": ["synthetic-b"], "explanation": "synthetic"})
        b.update(id="synthetic-b", kind="inferred", derivation={"supporting_claim_ids": ["synthetic-a"], "explanation": "synthetic"})
        with self.assertRaisesRegex(ValueError, "循环"):
            self.validate(a, b)
        with self.assertRaisesRegex(ValueError, "不存在"):
            self.validate(a)

    def test_pending_premise_and_explicit_disguise_rejected(self):
        self.db.execute("INSERT INTO claims(id,text,kind,concept_ids,review_status) VALUES(?,?,?,?,?)", ("synthetic-parent", "synthetic", "explicit", "[]", "pending"))
        record = copy.deepcopy(self.record)
        record.update(kind="inferred", derivation={"supporting_claim_ids": ["synthetic-parent"], "explanation": "synthetic"})
        with self.assertRaisesRegex(ValueError, "未复核"):
            self.validate(record)
        record["kind"] = "explicit"
        with self.assertRaisesRegex(ValueError, "explicit"):
            self.validate(record)

    def test_reviewed_semantic_overwrite_is_rejected(self):
        self.db.execute("INSERT INTO claims(id,text,kind,conditions,exceptions,concept_ids,review_status) VALUES(?,?,?,?,?,?,?)", (self.record["id"], "原合成内容", "explicit", "[]", "[]", "[]", "reviewed"))
        with self.assertRaisesRegex(ValueError, "隐式覆盖"):
            self.validate(self.record)

    def test_missing_and_unreviewed_figure_provenance(self):
        record = copy.deepcopy(self.record)
        record["evidence"][0]["figure_ids"] = ["synthetic-missing-figure"]
        record["figure_review_note"] = "synthetic visual note; origin unverified"
        with self.assertRaisesRegex(ValueError, "配图不存在"):
            self.validate(record)
        self.db.execute("INSERT INTO figures(id,document_id,pdf_page,bbox) VALUES(?,?,?,?)", ("synthetic-missing-figure", "synthetic-doc", 1, "[1,1,3,3]"))
        result = self.validate(record)[0]["anchors"][0]
        self.assertEqual(result["figure_origins"]["synthetic-missing-figure"], "unverified")

    def test_readonly_preflight_does_not_write_any_file(self):
        path = self.root / "synthetic.jsonl"
        path.write_text(j(self.record) + "\n", encoding="utf-8")
        snapshot = {str(p.relative_to(self.root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.rglob("*") if p.is_file()}
        with contextlib.redirect_stdout(io.StringIO()):
            report = import_batches(self.root, [path], check=True)
        after = {str(p.relative_to(self.root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.rglob("*") if p.is_file()}
        self.assertFalse(report["writes"])
        self.assertFalse(report["semantic_entailment_proven"])
        self.assertEqual(snapshot, after)

    def test_invalid_batch_never_partially_imports(self):
        path = self.root / "synthetic.jsonl"
        bad = copy.deepcopy(self.record)
        bad.update(id="synthetic-bad", importance_level=True)
        path.write_text(j(self.record) + "\n" + j(bad) + "\n", encoding="utf-8")
        before = (self.root / "graph.sqlite").read_bytes()
        with self.assertRaises(ValueError):
            import_batches(self.root, [path])
        self.assertEqual(self.db.execute("SELECT count(*) FROM claims").fetchone()[0], 0)
        self.assertEqual(before, (self.root / "graph.sqlite").read_bytes())


if __name__ == "__main__":
    unittest.main()
