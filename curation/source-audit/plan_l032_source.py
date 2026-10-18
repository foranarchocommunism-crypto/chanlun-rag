"""Metadata-only corrections from actual PDF233-243 source and figure review."""
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
assert metadata['graph_version'] == '0.1.0-review-df7b7562fbf3'
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


for short in ['0236-b002', '0236-b003', '0236-b004', '0236-b005', '0237-b000']:
    propose('passages', short, {'role': 'author_commentary', 'published_at': '2007-02-28'},
            '实际PDF236/237明确“补充：今天收盘的讲评”，不能继承课程早8:44；当日明确但收盘讲评具体时刻未载，日粒度记录不捏造15点，作者身份和原文不改。')
notes = {
    '0233-fig1': ('later_annotation', '实际整图000416前复权日线，光标2007/02/28，右端已入3月；周/日中枢框和17(T)/32天为编图注，不由后图认证作者一个月100%实绩或图框唯一构造。'),
    '0235-fig1': ('unverified', '实际整图联通1分光标2/27，右端2/27，标0936—0945及5.52，早于2/28正文；原发制作者未核，蓝线/价点不等已独立核作者操盘或资金因果。'),
    '0236-fig1': ('later_annotation', '实际整图联通日线光标2007/03/01、右端3月，晚于2/28课程；1/4—1/30高点线只为原文举例，不成为所有股票必然压力或作者原发来源证明。'),
    '0237-fig1': ('unverified', '实际整图上证1分光标2/28，右端当天尾盘，嵌2/28收盘补充与15:29/15:35答复；未见晚于当日答复行情，原发制作者未核；2915.70为GG，不能替代2894中枢上沿。'),
    '0241-fig1': ('unverified', '实际整图上证分笔分段/1分界面光标2/27，右端至3/1，邻文已是3/1收盘；未见晚于该文行情，来源未核，三买/分段标注不能代替三段次级和原文条件。'),
}
for short, (status, note) in notes.items():
    propose('figures', short, {'origin_status': status, 'note': note},
            '逐一核对11页和5完整图的行情栏、右端与嵌文；区分文后行情及原发未核，不把先前光标当全图时间。')
assert len(ops) == 10
plan = {'stage': 'C/E-source-provenance', 'plan_format': 1, 'schema_version': metadata['schema_version'],
        'base_graph_version': metadata['graph_version'], 'documents': [dict(r) for r in db.execute('SELECT * FROM documents ORDER BY id')],
        'new_units': [], 'operations': ops, 'visual_pages': list(range(233, 244)),
        'pending': ['5收盘补充段只知2/28未载具体时刻，不继承8:44；CCTV被表扬也保留读者引文身份；2915作者已更正GG而上沿2894附近。'],
        'reviewer': 'Codex 主代理 / 第32课收盘补充与原图来源复核'}
out = Path(__file__).parent / 'stage-c-l032-source-plan.json'
out.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
db.close()
sys.stdout.reconfigure(encoding='utf-8')
print(json.dumps({'operations': len(ops), 'passages': 5, 'figures': 5, 'base': metadata['graph_version']}, ensure_ascii=False))
