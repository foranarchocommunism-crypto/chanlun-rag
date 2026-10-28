"""Metadata-only corrections from actual PDF219-232 source and figure review."""
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
assert metadata['graph_version'] == '0.1.0-review-958d0b42fad7'
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


notes = {
    '0219-fig1': ('unverified', '实际整图标深天地A日线，光标1996/12/02，右端到1997年5月，嵌1996透支故事；正文股票未具名，不能凭后配图把身份、价格与账户故事认证为作者已核事实，制作者日期未核。'),
    '0221-fig1': ('later_annotation', '实际整图中国联通5分光标2007/02/15，右端至2/16，浮窗分时2/15；晚于2/15正文解盘，5元承诺和作者操盘自述非账户或因果证据。'),
    '0222-fig1': ('later_annotation', '实际整图指数5分光标2/15，右端至2/16，浮窗明确2/16分时；晚于2/15解盘，3036/2998后行情不补作者当时承诺之完成证明。'),
    '0224-fig1': ('later_annotation', '实际整图1分光标2/15，右端至2/26，嵌2/15小鸟/兰兰及两作者答复；1048/1114/1129/1413标注依本例，1329笔误备注在读者段不另当作者更正文。'),
    '0226-fig1': ('later_annotation', '实际整图指数5分光标2/16，右端到2/26，嵌2/16 14:05问答；文后行情与当天背驰判断分开，图箭头与MACD不补所有级别数值算法。'),
    '0230-fig1': ('later_annotation', '实际整图日线光标2007/02/27，右边多根K到2007年3月，嵌2/27原解释和17:18不严谨自我收窄；须读更正：先日线中枢再扩张，当前第一段里的第三小段，非已成周线前三段。'),
}
for short, (status, note) in notes.items():
    propose('figures', short, {'origin_status': status, 'note': note},
            '逐一实际查看14页和6完整图，按行情右端、浮窗分时及嵌答辨原文先后，后配图不能自动证明作者原发身份。')
assert len(ops) == 6
plan = {'stage': 'C/E-source-provenance', 'plan_format': 1, 'schema_version': metadata['schema_version'],
        'base_graph_version': metadata['graph_version'], 'documents': [dict(r) for r in db.execute('SELECT * FROM documents ORDER BY id')],
        'new_units': [], 'operations': ops, 'visual_pages': list(range(219, 233)),
        'pending': ['6图5文后1未核，正文未具名1996股票不因图深天地A自动认证；作者明确不严谨的周线三段早说与随后限定并列取证。'],
        'reviewer': 'Codex 主代理 / 第31课原图来源复核'}
out = Path(__file__).parent / 'stage-c-l031-source-plan.json'
out.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
db.close()
sys.stdout.reconfigure(encoding='utf-8')
print(json.dumps({'operations': len(ops), 'passages': 0, 'figures': 6, 'base': metadata['graph_version']}, ensure_ascii=False))
