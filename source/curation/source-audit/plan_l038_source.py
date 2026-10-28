"""Metadata-only corrections from actual PDF280-287 source and figure review."""
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
assert metadata['graph_version'] == '0.1.0-review-fb1a6407424c'
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


for short in ['0282-b006','0283-b000','0283-b001']:
    propose('passages', short, {'published_at': '2007-03-22 15:29:02'},
            '实际PDF282段尾出现3/22 15:29:02头，支配后段周四尾盘、三日收高和0124/0227压力线及终止符；前3/21段和尾头字符不改。')
notes = {
    '0281-fig1': ('later_annotation', '实际蓝字折线操作示意图署风清月明、09.10.15，晚于2007/3/21正文；仅作后加说明，不将简图缺少完成/级别约束当作者原定理或作者原配图。'),
    '0283-fig1': ('later_annotation', '实际30分图头3/22而右端3/23，嵌3/22 15:29评论；0124/0227压力线和右侧后行情不证明原未来三日突破已经确定。'),
    '0284-fig1': ('later_annotation', '实际日线选择栏为3/21，但右端在所选3/21后尚有上涨K线，主图至4月附近且标3326.92；晚于3/21答复，后图不抹日背驰可能或再延伸日中枢的条件。'),
    '0286-fig1': ('later_annotation', '实际5分图头与右端3/26，嵌3/22 15:42作者答和读者提问；未来K晚于问答，沪深背离与盘背为当日作者判读，不据后图认证预测或混读者身份。'),
}
for short, (status, note) in notes.items():
    propose('figures', short, {'origin_status': status, 'note': note},
            '逐一实际查看PDF280至287八页和本课四张完整图，核署名日期、选择栏与主图右端、混合文字发言者。')
assert len(ops) == 7
plan = {'stage': 'C/E-source-provenance', 'plan_format': 1, 'schema_version': metadata['schema_version'],
        'base_graph_version': metadata['graph_version'], 'documents': [dict(r) for r in db.execute('SELECT * FROM documents ORDER BY id')],
        'new_units': [], 'operations': ops, 'visual_pages': list(range(280, 288)),
        'pending': ['同级别本级盘整+盘整和低级不允许分层；三买首有效回抽与次次级两次回抽区别，所有图后加，机械流程相等边界未擅补。'],
        'reviewer': 'Codex 主代理 / 第38课跨日解盘和原图来源复核'}
out = Path(__file__).parent / 'stage-c-l038-source-plan.json'
out.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
db.close()
sys.stdout.reconfigure(encoding='utf-8')
print(json.dumps({'operations': len(ops), 'passages': 3, 'figures': 4, 'base': metadata['graph_version']}, ensure_ascii=False))
