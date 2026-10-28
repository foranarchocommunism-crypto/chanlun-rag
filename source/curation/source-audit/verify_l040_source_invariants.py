"""Compare source rows with the actual pre-correction backup, read-only."""
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2]
KB = AGENT.parent / 'shared-knowledge/v0.1.0'
AUDIT = Path(__file__).resolve().parent


def ro(path):
    db = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    return db


def main():
    plan = json.loads((AUDIT / 'stage-c-l040-source-plan.json').read_text(encoding='utf-8'))
    applied = json.loads((AUDIT / 'stage-c-l040-source-applied.json').read_text(encoding='utf-8'))
    old = ro(Path(applied['backup_directory']) / 'graph.sqlite')
    current = ro(KB / 'graph.sqlite')
    try:
        operations = {(x['table'], x['id']): x for x in plan['operations']}
        assert len(operations) == 18
        compared = {}
        unchanged_content = hashlib.sha256()
        for table in ['documents', 'pages', 'passages', 'figures']:
            count = 0
            for original in old.execute(f'SELECT * FROM {table} ORDER BY id'):
                before = dict(original)
                after_row = current.execute(f'SELECT * FROM {table} WHERE id=?', (before['id'],)).fetchone()
                assert after_row is not None, (table, before['id'])
                after = dict(after_row)
                operation = operations.get((table, before['id']))
                expected = dict(before)
                if operation:
                    assert all(before[k] == v for k, v in operation['before'].items())
                    expected.update(operation['after'])
                assert after == expected, (table, before['id'])
                stable = {k: v for k, v in before.items() if not operation or k not in operation['after']}
                unchanged_content.update(json.dumps([table, stable], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())
                count += 1
            assert current.execute(f'SELECT count(*) FROM {table}').fetchone()[0] == count
            compared[table] = count
        originals = old.execute("SELECT * FROM claims WHERE review_status='reviewed'").fetchall()
        assert len(originals) == 2550
        old_evidence = 0
        for claim in originals:
            assert dict(current.execute('SELECT * FROM claims WHERE id=?', (claim['id'],)).fetchone()) == dict(claim)
            for e in old.execute('SELECT * FROM evidence WHERE claim_id=?', (claim['id'],)):
                assert dict(current.execute('SELECT * FROM evidence WHERE id=?', (e['id'],)).fetchone()) == dict(e)
                old_evidence += 1
        report = {
            'stage': 'C-source-invariants',
            'graph_version': json.loads(current.execute("SELECT value FROM metadata WHERE key='graph_version'").fetchone()[0]),
            'source_base_graph_version': plan['base_graph_version'],
            'compared_source_rows': compared,
            'authorized_passage_operations': sum(x['table'] == 'passages' for x in plan['operations']),
            'authorized_figure_operations': sum(x['table'] == 'figures' for x in plan['operations']),
            'all_other_source_columns_unchanged': True,
            'original_reviewed_claims_unchanged': len(originals),
            'original_reviewed_evidence_unchanged': old_evidence,
            'stable_source_content_sha256': unchanged_content.hexdigest(),
            'backup_directory': applied['backup_directory'],
            'writes_to_database': False,
            'pass': True,
            'limits': ['行级一致性证明原文与几何未改，不代替语义蕴含或图像解释。'],
        }
        (AUDIT / 'stage-c-l040-source-invariants.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(report, ensure_ascii=False))
    finally:
        old.close()
        current.close()


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
