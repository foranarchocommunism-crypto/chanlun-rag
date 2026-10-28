"""Metadata-only corrections from actual PDF204-213 source and figure review."""
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
assert metadata['graph_version'] == '0.1.0-review-e78ec8275af6'
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


for short in ['0210-b002', '0210-b003']:
    propose('passages', short, {'published_at': '2007-02-12 15:15:26'},
            '实际PDF210：前段末2007-02-12 15:15:26是新解盘头，管其后两段；前段999/777预告仍属2/9 15:09:19，原文不改。')
notes = {
    '0204-fig1': ('unverified', '实际整图：无署名日期，示意5分下跌末B中枢、ZG/ZD/DD与仅触DD后扩展；DD在ZD下方，触DD不等进入中枢；右侧嵌原文不证明作者制图。'),
    '0205-fig1': ('unverified', '实际整图：无署名日期，示意a+A+b+B+c及30分大框；9个1分计量须保留正文假设，不能由大框认定所有下跌后立即完成30分盘整。'),
    '0205-fig2': ('unverified', '实际整图：无署名日期，示意下跌后同级上涨，A/B各5分中枢、右侧向上新中枢；同级反趋势与更大盘整分开，制作者未核。'),
    '0207-fig1': ('unverified', '实际整图明确署“张大山习作”，写a+A+b+B+c至a~+A~，B+c扩展示意；作者制图身份无依据，日期未记，归来源未核习作。'),
    '0207-fig2': ('unverified', '实际整图署“张大山习作”，更大级别盘整方框在ZD下侧至上方，示意与正文两完成类型区别；署名非缠中说禅，不作作者原图证明。'),
    '0207-fig3': ('later_annotation', '实际整图上证5分光标2007/02/09，主图右端到2/12，晚于2/9正文；嵌2/6反弹和2/7 11点原文，后续K不能反证当时未来路径已确认。'),
    '0207-fig4': ('unverified', '实际整图署“张大山习作”，更大盘整方框覆盖DD附近至ZD上，和同页fig2是两幅不同习作；无日期，不把框位置当唯一严格构造算法。'),
    '0207-fig5': ('unverified', '实际整图署“张大山习作”，同级以上反趋势V形示意，A/B/DD/ZD明示；制作者与原作者分开，无日期，不以V图补预判V的充分条件。'),
    '0208-fig1': ('later_annotation', '实际整图标“上证20080703—0718”，光标2008/07/07，右端7/18；是2008年7月后配案例，非2007年2月作者原发，图注2566/2951/2665未独立核价。'),
    '0209-fig1': ('later_annotation', '实际整图标“上证20080220—0305一分图”，9段扩展2.5分中枢；晚于2007课文，2.5分为图注口径，不作为作者新规定级别或9段通用定理。'),
    '0209-fig2': ('later_annotation', '实际整图光标2007/02/12，主图右端2/13，嵌2/9与2/12两解盘；2850/3000仍原时条件展望，后续涨势不补兑现率或当时确定性。'),
    '0211-fig1': ('unverified', '实际整图光标2007/02/01，主图至2/6，嵌2/12星星读者与作者答复；不晚于答复，原发制作者未核；01301055/1345等标签与前后类型归属问题分开核。'),
}
for short, (status, note) in notes.items():
    propose('figures', short, {'origin_status': status, 'note': note},
            '逐一查看实际页面与完整图对象，核图题/行情栏/主图右端/习作署名；文后行情与未核原发分开。')
assert len(ops) == 14
plan = {'stage': 'C/E-source-provenance', 'plan_format': 1, 'schema_version': metadata['schema_version'],
        'base_graph_version': metadata['graph_version'], 'documents': [dict(r) for r in db.execute('SELECT * FROM documents ORDER BY id')],
        'new_units': [], 'operations': ops, 'visual_pages': list(range(204, 214)),
        'pending': ['PDF206/209两处备注在作者正文抽取块内但独立署名/时间不可辨；原文及角色不擅改，显式作者引文截除备注，备注出处与解释冲突待核。'],
        'reviewer': 'Codex 主代理 / 第29课日期与原图来源复核'}
out = Path(__file__).parent / 'stage-c-l029-source-plan.json'
out.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
db.close()
sys.stdout.reconfigure(encoding='utf-8')
print(json.dumps({'operations': len(ops), 'passages': 2, 'figures': 12, 'base': metadata['graph_version']}, ensure_ascii=False))
