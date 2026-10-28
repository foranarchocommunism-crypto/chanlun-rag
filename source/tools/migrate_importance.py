import argparse
import json
import sqlite3
from pathlib import Path

LEVELS = {"1": "基础核心", "2": "主要方法", "3": "补充深化", "4": "背景细节"}


def migrate(root):
    db = sqlite3.connect(root / "graph.sqlite")
    for table in ("concepts", "claims", "relations"):
        columns = {row[1] for row in db.execute(f"PRAGMA table_info({table})")}
        if "importance_level" not in columns:
            db.execute(f"ALTER TABLE {table} ADD COLUMN importance_level INTEGER CHECK(importance_level BETWEEN 1 AND 4)")
        if "importance_reason" not in columns:
            db.execute(f"ALTER TABLE {table} ADD COLUMN importance_reason TEXT NOT NULL DEFAULT '待评定'")
    db.execute("INSERT OR REPLACE INTO metadata VALUES('schema_version',?)", (json.dumps("1.1.0"),))
    db.execute("INSERT OR REPLACE INTO metadata VALUES('importance_levels',?)", (json.dumps(LEVELS, ensure_ascii=False),))
    db.commit()
    db.close()
    path = root / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest.update(schema_version="1.1.0", importance_levels=LEVELS)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"schema_version": "1.1.0", "importance_levels": LEVELS}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--kb", required=True, type=Path)
    migrate(parser.parse_args().kb)
