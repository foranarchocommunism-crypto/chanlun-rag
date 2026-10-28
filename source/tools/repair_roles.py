"""Reconcile explicit speaker markers, including embedded markers and missing colons.

This improves source segmentation; it does not approve any semantic assertion.
"""
import argparse
import gzip
import json
import re
import sqlite3
from functools import lru_cache
from pathlib import Path

from extract_corpus import CONCEPTS, TECH, digest, j

DATE = r"20\d{2}-\d{1,2}-\d{1,2}\s*\d{1,2}:\d{2}(?::\d{2})?"
ACTOR = re.compile(r"^(.{1,35}?)\s*[：:；;]?\s*(" + DATE + r")\s*$")
AUTHOR = re.compile(r"缠中说禅\s*[：:]?\s*(" + DATE + r")")
COMMENTARY = re.compile(r"缠中说禅(?:解盘|看盘)\s*[：:]?\s*(" + DATE + r")?")
LESSON = re.compile(r"^教你炒股票\s*\d+\s*[：:]")


def compact(text):
    return re.sub(r"\s+", "", text)


def marker_events(row):
    text = row["text"]
    result = []
    cursor = 0
    for line in row["raw_text"].splitlines():
        match = ACTOR.fullmatch(line.strip())
        if match:
            name, time = match.group(1).strip(" ：:；;"), match.group(2)
            needle = compact(line)
            offset = text.find(needle, cursor)
            if offset < 0:
                offset = text.find(name, cursor)
            if offset >= 0:
                role = "author_reply" if name == "缠中说禅" else "author_commentary" if name.startswith("缠中说禅解盘") else "reader"
                result.append((offset, role, name, time))
                cursor = offset + len(needle)
    for match in AUTHOR.finditer(text):
        result.append((match.start(), "author_reply", "缠中说禅", match.group(1)))
    for match in COMMENTARY.finditer(text):
        result.append((match.start(), "author_commentary", "缠中说禅", match.group(1)))
    # Duplicate line-level and embedded markers resolve to the same trusted actor.
    by_offset = {event[0]: event for event in result}
    return sorted(by_offset.values())


def repair(root):
    db = sqlite3.connect(root / "graph.sqlite")
    db.row_factory = sqlite3.Row
    if db.execute("SELECT 1 FROM metadata WHERE key='role_parser_revision' AND value='2'").fetchone():
        print(j({"status": "already_repaired", "revision": 2}))
        return
    @lru_cache(maxsize=4)
    def geometry(doc, page):
        path = db.execute("SELECT geometry_path FROM pages WHERE document_id=? AND pdf_page=?", (doc, page)).fetchone()[0]
        with gzip.open(root / path, "rt", encoding="utf-8") as f:
            return json.load(f)["chars"]

    changes, splits = [], []
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("BEGIN IMMEDIATE")
    pending = "SELECT id FROM claims WHERE id LIKE 'candidate-%' AND review_status='pending'"
    db.execute(f"DELETE FROM evidence WHERE claim_id IN ({pending})")
    db.execute(f"DELETE FROM claims WHERE id IN ({pending})")
    rows = db.execute("SELECT * FROM passages ORDER BY document_id,pdf_page,block_index").fetchall()
    previous_doc, role, speaker, published = None, "unknown", None, None
    for row in rows:
        if row["document_id"] != previous_doc:
            role, speaker, published = "unknown", None, None
            previous_doc = row["document_id"]
        if row["unit_id"] and LESSON.match(row["text"]):
            role, speaker = "author_body", "缠中说禅"
            published = db.execute("SELECT published_at FROM units WHERE id=?", (row["unit_id"],)).fetchone()[0]
        elif "缠中说禅回复" in row["text"] and len(row["text"]) < 35:
            role, speaker, published = "unknown", None, None
        events = marker_events(row)
        segments = []
        start = 0
        for offset, next_role, next_speaker, next_time in events:
            if offset > start:
                segments.append((start, offset, role, speaker, published))
            start, role, speaker, published = offset, next_role, next_speaker, next_time
        if start < len(row["text"]):
            segments.append((start, len(row["text"]), role, speaker, published))
        if not segments:
            segments = [(0, len(row["text"]), role, speaker, published)]
        if len(segments) > 1 and db.execute("SELECT 1 FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE e.passage_id=? AND c.review_status='reviewed'", (row["id"],)).fetchone():
            raise RuntimeError("已复核证据涉及拆段，必须先单独迁移：" + row["id"])
        mapping = json.loads(row["normalized_map"])
        for n, (begin, end, seg_role, seg_speaker, seg_time) in enumerate(segments):
            pid = row["id"] if n == 0 else row["id"] + f"-s{n:02}"
            text, segment_map = row["text"][begin:end], mapping[begin:end]
            boxes, raw = json.loads(row["boxes"]), row["raw_text"]
            indices = json.loads(row["source_char_indices"])
            if len(segments) > 1:
                geo = geometry(row["document_id"], row["pdf_page"])
                indices = list(dict.fromkeys(i for i in segment_map if i >= 0))
                line_boxes, raw_chars, last_top = [], [], None
                for idx in indices:
                    char, x0, top, x1, bottom = geo[idx]
                    if last_top is None or abs(top - last_top) > 3:
                        line_boxes.append([x0, top, x1, bottom])
                        if raw_chars:
                            raw_chars.append("\n")
                        last_top = top
                    else:
                        box = line_boxes[-1]
                        box[0], box[1], box[2], box[3] = min(box[0], x0), min(box[1], top), max(box[2], x1), max(box[3], bottom)
                    raw_chars.append(char)
                boxes, raw = line_boxes, "".join(raw_chars)
            values = (pid, row["unit_id"], row["document_id"], row["pdf_page"], row["block_index"] * 100 + n, seg_role, seg_speaker, seg_time, text, raw, j(boxes), j(segment_map), j(indices))
            if n == 0:
                db.execute("UPDATE passages SET unit_id=?,document_id=?,pdf_page=?,block_index=?,role=?,speaker=?,published_at=?,text=?,raw_text=?,boxes=?,normalized_map=?,source_char_indices=? WHERE id=?", values[1:] + (pid,))
            else:
                db.execute("INSERT INTO passages VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", values)
            if seg_role in ("author_body", "author_reply") and TECH.search(text) and len(text) > 30 and not LESSON.match(text) and not ACTOR.fullmatch(raw.strip()):
                concept_ids = ["concept-" + digest(k) for k, aliases in CONCEPTS.items() if k in text or any(a in text for a in aliases)]
                cid = "candidate-" + digest(pid)
                db.execute("INSERT OR IGNORE INTO claims(id,text,kind,concept_ids,review_status,review_note) VALUES(?,?,?,?,?,?)", (cid, text, "explicit", j(concept_ids), "pending", "技术词召回候选；角色解析修订2，语义与发言者仍待逐项复核"))
                db.execute("INSERT OR IGNORE INTO evidence VALUES(?,?,?,?,?,?,?,?)", ("evidence-" + digest(cid), cid, pid, text, 0, len(text), j([{"document_id": row["document_id"], "pdf_page": row["pdf_page"], "char_indices": segment_map, "boxes": boxes}]), "[]"))
        if row["role"] != segments[0][2] or row["speaker"] != segments[0][3]:
            changes.append({"id": row["id"], "before": [row["role"], row["speaker"]], "after": [segments[0][2], segments[0][3]]})
        if len(segments) > 1:
            splits.append({"id": row["id"], "parts": len(segments)})
    db.execute("DELETE FROM passage_fts")
    db.execute("INSERT INTO passage_fts SELECT id,text FROM passages")
    db.execute("INSERT OR REPLACE INTO metadata VALUES('role_parser_revision','2')")
    version = "0.1.0-source-rolefix2"
    db.execute("UPDATE metadata SET value=? WHERE key='graph_version'", (j(version),))
    db.commit()
    counts = {t: db.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in ("documents", "pages", "units", "passages", "figures", "concepts", "claims")}
    db.close()
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update(graph_version=version, counts=counts, role_parser_revision=2)
    temporary = root / "manifest.next.json"
    temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(manifest_path)
    report = {"revision": 2, "role_changes": changes, "split_passages": splits, "counts": counts, "semantic_approval": False}
    report_dir = Path(__file__).parents[1] / "build"
    report_dir.mkdir(exist_ok=True)
    (report_dir / "role-repair-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(j({"role_changes": len(changes), "split_passages": len(splits), "counts": counts}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--kb", type=Path, required=True)
    repair(parser.parse_args().kb)
