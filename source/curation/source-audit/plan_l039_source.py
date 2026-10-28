"""Metadata-only corrections from actual PDF287-290 source and figure review."""
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
assert metadata['graph_version'] == '0.1.0-review-0cc5c3d74a49'
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
        assert not any(r['review_status'] == 'reviewed' for r in refs), refs
        item['affected_references'] = refs
    ops.append(item)


for short in ['0288-b005','0289-b000','0289-b001']:
    propose('passages', short, {'published_at': '2007-03-26 15:20:49'},
            '实际PDF288在3/23段尾出现3/26 15:20:49时间头，支配其后突破待确认、次日传闻和二线/监管风险三段；原尾头与前段3/23不改。')
notes = {
    '0288-fig1': ('unverified', '实际为左侧Ai/Ai+2奇数回补及延后回补示意，未见作者署名日期；原发/制作者未核，仅作汇编解释图，不能补奇数支k取值或证明算法。'),
    '0288-fig2': ('unverified', '实际为右侧Ai奇偶标记、Ai+3保护条件和延后卖出示意，带网站水印但无作者原发证明；不将示意中的折线当完整走势类型或精确成交保证。'),
    '0290-fig1': ('later_annotation', '实际5分整图图头/右端2007/03/28，嵌3/23与3/26解盘及3/23 13:25最小级别答；右端晚于原文，不倒证压力突破有效性已确认或把最小级信号改5分背驰。'),
}
for short, (status, note) in notes.items():
    propose('figures', short, {'origin_status': status, 'note': note},
            '逐一实际查看PDF287至290四页、两示意及完整行情图，另看290原页核卖就全买原字。')
assert len(ops) == 6
plan = {'stage': 'C/E-source-provenance', 'plan_format': 1, 'schema_version': metadata['schema_version'],
        'base_graph_version': metadata['graph_version'], 'documents': [dict(r) for r in db.execute('SELECT * FROM documents ORDER BY id')],
        'new_units': [], 'operations': ops, 'visual_pages': list(range(287, 291)),
        'pending': ['卖就全买原页原字保留不静改，Ai+k奇偶及等值边界未补成独立算法；2示意原发未核1行情后加，读者T+0/无涨跌停不认证当前规则。'],
        'reviewer': 'Codex 主代理 / 第39课跨日解盘、公式与原图来源复核'}
out = Path(__file__).parent / 'stage-c-l039-source-plan.json'
out.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
db.close()
sys.stdout.reconfigure(encoding='utf-8')
print(json.dumps({'operations': len(ops), 'passages': 3, 'figures': 3, 'base': metadata['graph_version']}, ensure_ascii=False))
