"""Keep dated non-course articles and market commentary out of course assertions."""
import argparse
import json
import re
import sqlite3
from pathlib import Path
from repair_roles import ACTOR, LESSON, DATE
from graph_release import refresh_version, update_manifest

DATED_TITLE = re.compile(r"^.{3,85}[（(]" + DATE + r"[）)]\s*$")
COMMENTARY = re.compile(r"^(?:今日|当日|缠中说禅)?解盘\s*[：:]")


def mark(root):
    db = sqlite3.connect(root / "graph.sqlite")
    db.row_factory = sqlite3.Row
    changes, previous_doc, state = [], None, ("unknown", None, None)
    rows = db.execute("SELECT * FROM passages ORDER BY document_id,pdf_page,block_index").fetchall()
    db.execute("BEGIN IMMEDIATE")
    for row in rows:
        if previous_doc != row["document_id"]:
            state = ("unknown", None, None)
            previous_doc = row["document_id"]
        text, raw = row["text"], row["raw_text"]
        first = raw.splitlines()[0].strip() if raw else text
        actor = ACTOR.fullmatch(raw.strip())
        if row["unit_id"] and LESSON.match(text):
            state = ("author_body", "缠中说禅", row["published_at"])
        elif COMMENTARY.match(first) or (DATED_TITLE.fullmatch(first) and not LESSON.match(first)):
            state = ("author_commentary", "缠中说禅", row["published_at"])
        elif actor:
            name = actor.group(1).strip(" ：:；;")
            state = ("author_reply" if name == "缠中说禅" else "reader", name, actor.group(2))
        elif "缠中说禅回复" in text and len(text) < 35:
            state = ("unknown", None, None)
        if row["role"] != state[0] or row["speaker"] != state[1]:
            reviewed = db.execute("SELECT c.id FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE e.passage_id=? AND c.review_status='reviewed'", (row["id"],)).fetchall()
            if reviewed:
                # A reviewed source may only be reclassified after a separate semantic audit.
                changes.append({"id": row["id"], "proposed": state, "held_for_review": [r[0] for r in reviewed]})
                continue
            db.execute("UPDATE passages SET role=?,speaker=?,published_at=? WHERE id=?", state + (row["id"],))
            changes.append({"id": row["id"], "before": [row["role"], row["speaker"]], "after": state})
    db.execute("INSERT OR REPLACE INTO metadata VALUES('context_section_revision','1')")
    version = refresh_version(db)
    db.commit()
    db.close()
    update_manifest(root, version, context_section_revision=1)
    out = Path(__file__).parents[1] / "build"
    out.mkdir(exist_ok=True)
    (out / "context-section-report.json").write_text(json.dumps(changes, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"changed_or_held": len(changes), "held_for_review": sum('held_for_review' in r for r in changes)}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--kb", required=True, type=Path)
    mark(parser.parse_args().kb)
