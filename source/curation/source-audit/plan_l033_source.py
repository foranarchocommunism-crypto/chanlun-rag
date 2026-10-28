"""Metadata-only corrections from actual PDF243-254 source and figure review."""
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
assert metadata['graph_version'] == '0.1.0-review-68e03935d1ac'
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


for short in ['0247-b002', '0247-b003', '0247-b004']:
    propose('passages', short, {'published_at': '2007-03-05 11:56:42'},
            '实际PDF247：前段末3/5 11:56:42为新解盘时间，支配提前发帖/1017背驰及其后两段；前段999/343自述仍3/2。')
for short in ['0247-b005', '0247-b006', '0248-b000', '0248-b001', '0248-b002']:
    propose('passages', short, {'published_at': '2007-03-05 21:14:20'},
            '实际PDF247/248：独立3/5 21:14:20头与随后刚回来、130点/30%降本、盘整技能及三卖破位段同属夜间补评，末3/6头不回改本段。')
for short in ['0248-b003', '0249-b000']:
    propose('passages', short, {'published_at': '2007-03-06 15:22:36'},
            '实际PDF248/249：3/6 15:22:36新头管次日压力/15分120及个股轮动，不能继承3/2或3/5日期；3/2作者问答仍按各自署名时间。')
notes = {
    '0245-fig1': ('unverified', '实际整图上证1分光标3/1，右端亦3/1，嵌3/2课程对2/28 c及2915的解释；没有晚于课程行情，原发制作者未核。A标13:37、正文13:37与此前13:38不静合，图周期不补15分严格级别。'),
    '0247-fig1': ('later_annotation', '实际整图1分光标3/7，主图到3/7，嵌3/5午/夜两个解盘；晚于3/5，1017点与2888—2858连线保留当时例，后上行不证明所有盘整可降本30%。'),
    '0248-fig1': ('later_annotation', '实际整图5分主图右端至3/7，嵌3/6 15:22解盘；晚于该文，5分中枢框/突破连线不替原文三波、级别修复与次日不回区间条件。'),
    '0249-fig1': ('later_annotation', '实际整图15分光标2007/03/09，右端3/9，晚于3/6；120均线/2888.90/2915.70/2858.37为图上参照，不能以15分图直接认走势类型15分或校改原文数字。'),
    '0252-fig1': ('later_annotation', '实际整图5分光标3/8，右端亦3/8，嵌3/6新年好问题及16:07作者答；晚于答复，初上零轴非本级背驰与小级别信号区别按文字，柱高不替完整结构。'),
    '0253-fig1': ('later_annotation', '实际整图日线光标3/6，右端已至4月且高点3532.86，嵌3/5与3/6两答；明显文后，紫框周中枢不能把原条件“若盘至4月/也可直接上破”改成当时已成。'),
    '0254-fig1': ('later_annotation', '实际整图600598五分光标3/6，右端3/7，嵌3/6读者柱/面积/黄白线问题和作者16:39答；晚于答复，作者未直接认证全部读者9.24点背驰，只给指标相对重要性及多级配套范围。'),
}
for short, (status, note) in notes.items():
    propose('figures', short, {'origin_status': status, 'note': note},
            '实际核对12页与7完整图，比较光标、右端和嵌文日期，来源未核与后配未来行情分开。')
assert len(ops) == 17
plan = {'stage': 'C/E-source-provenance', 'plan_format': 1, 'schema_version': metadata['schema_version'],
        'base_graph_version': metadata['graph_version'], 'documents': [dict(r) for r in db.execute('SELECT * FROM documents ORDER BY id')],
        'new_units': [], 'operations': ops, 'visual_pages': list(range(243, 255)),
        'pending': ['延伸新增6加初始3共9的口径与32粗说分别保留；3/6作者仍列仅日线延伸直接突破的可能，后配4月图不改变当时条件。'],
        'reviewer': 'Codex 主代理 / 第33课跨日解盘与原图来源复核'}
out = Path(__file__).parent / 'stage-c-l033-source-plan.json'
out.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
db.close()
sys.stdout.reconfigure(encoding='utf-8')
print(json.dumps({'operations': len(ops), 'passages': 10, 'figures': 7, 'base': metadata['graph_version']}, ensure_ascii=False))
