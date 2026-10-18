"""Metadata-only corrections from actual PDF213-218 source review."""
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2]
KB = AGENT.parent / 'shared-knowledge/v0.1.0'
DOC = 'volume_1-a53e99c37ca5'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['graph_version'] == '0.1.0-review-c6ace0c23754'
ops = []


def propose(table, short, after, reason):
    id = DOC + '-p' + short
    row = dict(db.execute(f'SELECT * FROM {table} WHERE id=?', (id,)).fetchone())
    after = {k: v for k, v in after.items() if row[k] != v}
    assert after, id
    item = {'table': table, 'id': id, 'before': {k: row[k] for k in after}, 'after': after, 'reason': reason}
    if table == 'passages':
        item['text_sha256'] = hashlib.sha256(row['text'].encode()).hexdigest()
        refs = [dict(r) for r in db.execute('SELECT e.id,e.claim_id,c.review_status FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE e.passage_id=?', (id,))]
        assert not refs, refs
        item['affected_references'] = refs
    ops.append(item)


propose('passages', '0217-b000', {'published_at': '2007-02-14 15:13:25'},
        '实际PDF216页末独立2007-02-14 15:13:25头管下一页解盘段；216-b005创投预告仍2/13，217-b000不能继承2/13，全文与坐标不改。')
assert len(ops) == 1
plan = {'stage': 'C/E-source-provenance', 'plan_format': 1, 'schema_version': metadata['schema_version'],
        'base_graph_version': metadata['graph_version'], 'documents': [dict(r) for r in db.execute('SELECT * FROM documents ORDER BY id')],
        'new_units': [], 'operations': ops, 'visual_pages': list(range(213, 219)),
        'pending': ['本课无配图；原文价格充分有效市场为作者自定义，不等所有信息完全反映；绝对性未由本项目证明，第72课明确前提主要限动力学，范围另保留。'],
        'reviewer': 'Codex 主代理 / 第30课跨页解盘日期复核'}
out = Path(__file__).parent / 'stage-c-l030-source-plan.json'
out.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
db.close()
sys.stdout.reconfigure(encoding='utf-8')
print(json.dumps({'operations': len(ops), 'passages': 1, 'figures': 0, 'base': metadata['graph_version']}, ensure_ascii=False))
