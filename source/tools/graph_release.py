"""Content versioning shared by all graph build stages."""
import hashlib
import json


def refresh_version(db):
    fingerprint = hashlib.sha256()
    for row in db.execute("SELECT key,value FROM metadata WHERE key NOT IN ('graph_version','built_at','updated_at') ORDER BY key"):
        fingerprint.update(json.dumps(tuple(row), ensure_ascii=False).encode("utf-8"))
    for table in ("documents", "units", "pages", "passages", "figures", "concepts", "claims", "evidence", "relations"):
        names = [r[1] for r in db.execute(f"PRAGMA table_info({table})")]
        for row in db.execute(f"SELECT * FROM {table} ORDER BY id"):
            fingerprint.update(json.dumps(dict(zip(names, row)), ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    for row in db.execute("SELECT id,claim_id,reviewer,checks,result,note FROM reviews ORDER BY id"):
        fingerprint.update(json.dumps(tuple(row), ensure_ascii=False).encode("utf-8"))
    version = "0.1.0-review-" + fingerprint.hexdigest()[:12]
    db.execute("UPDATE metadata SET value=? WHERE key='graph_version'", (json.dumps(version),))
    return version


def update_manifest(root, version, **updates):
    path = root / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest.update(graph_version=version, **updates)
    temporary = root / "manifest.next.json"
    temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)
