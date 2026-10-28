"""Freeze DB + existing development gold without writing the live graph or gold."""
import argparse
import hashlib
import json
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

AGENT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--kb', type=Path, default=AGENT.parent / 'shared-knowledge/v0.1.0')
    parser.add_argument('--max-batch', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    cases, case_files, ids = [], [], set()
    for path in sorted((AGENT / 'evaluation').glob('stage-g-batch-*.cases.jsonl')):
        number = int(re.fullmatch(r'stage-g-batch-(\d+)\.cases\.jsonl', path.name)[1])
        if number > args.max_batch:
            continue
        raw = path.read_bytes()
        rows = [json.loads(line) for line in raw.decode('utf-8-sig').splitlines() if line.strip()]
        for row in rows:
            assert row['query_id'] not in ids, row['query_id']
            assert row['coverage_status'] == 'executable'
            assert row['gold_review_status'] == 'model_reviewed_development'
            assert row.get('human_gold_reviewed') is False and row.get('independent_test_set') is False
            ids.add(row['query_id'])
            cases.append(row)
        case_files.append({'name': path.name, 'sha256': hashlib.sha256(raw).hexdigest(), 'cases': len(rows)})
    assert cases, 'no executable gold'
    db = sqlite3.connect((args.kb.resolve() / 'graph.sqlite').as_uri() + '?mode=ro', uri=True, timeout=10)
    try:
        db.execute('BEGIN')
        meta = {key: json.loads(value) for key, value in db.execute('SELECT key,value FROM metadata')}
        original_manifest = (args.kb / 'manifest.json').read_bytes()
        manifest = json.loads(original_manifest)
        assert meta['graph_version'] == manifest['graph_version'], 'publication in progress; retry snapshot'
        for row in cases:
            for cid in row['required_claims']:
                assert db.execute("SELECT 1 FROM claims WHERE id=? AND review_status='reviewed'", (cid,)).fetchone(), cid
            for eid in row['expected_evidence_ids']:
                assert db.execute('SELECT 1 FROM evidence WHERE id=?', (eid,)).fetchone(), eid
            for ref in row['expected_source_refs']:
                source = db.execute('SELECT document_id,pdf_page,role,speaker FROM passages WHERE id=?', (ref['passage_id'],)).fetchone()
                assert source, ref['passage_id']
                for field, value in zip(['document_id', 'pdf_page', 'role', 'speaker'], source):
                    assert field not in ref or ref[field] == value, (row['query_id'], field, ref[field], value)
        with sqlite3.connect(out / 'graph.sqlite') as target:
            db.backup(target)
        assert original_manifest == (args.kb / 'manifest.json').read_bytes(), 'manifest changed during snapshot'
        (out / 'manifest.json').write_bytes(original_manifest)
    finally:
        db.close()
    # Gold is frozen verbatim as JSON objects, including original graph_version.
    (out / 'cases.jsonl').write_text(''.join(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n' for row in cases), encoding='utf-8')
    record = {'created_at': datetime.now(timezone.utc).isoformat(), 'graph_version': meta['graph_version'],
              'source_kb': str(args.kb.resolve()), 'snapshot_directory': str(out), 'cases': len(cases),
              'max_batch': args.max_batch, 'source_case_files': case_files,
              'database_sha256': sha(out / 'graph.sqlite'), 'manifest_sha256': sha(out / 'manifest.json'),
              'cases_sha256': sha(out / 'cases.jsonl'), 'live_database_written': False,
              'gold_review_status': 'model_reviewed_development', 'human_gold_reviewed': False,
              'independent_test_set': False, 'source_gold_files_written': False}
    (out / 'snapshot.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(record, ensure_ascii=False))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
