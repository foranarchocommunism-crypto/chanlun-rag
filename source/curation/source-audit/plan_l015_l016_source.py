"""Bounded metadata review from upper PDF58-75; original text is preserved."""
import hashlib
import json
import sqlite3
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2]
KB = AGENT.parent / 'shared-knowledge/v0.1.0'
DOC = 'volume_1-a53e99c37ca5'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
meta = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
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
        assert all(x['review_status'] != 'reviewed' for x in refs), id
        item['affected_references'] = refs
    ops.append(item)


for short in ['0064-b004', '0064-b005']:
    propose('passages', short, {'role': 'reader', 'speaker': '舞者', 'published_at': None},
            '实际PDF64：新的无时间“舞者”问题引作者前段再追问，不能沿用前条作者19:59身份/日期；末尾“缠中说禅：”仅为后答复头，原文不重切。')
propose('passages', '0064-b006', {'published_at': None},
        '实际PDF64：紧邻读者追问后有明确无日期作者署名，回答身份仍为author_reply，但其时间未单独记载，不借用前条19:59:07。')
notes = {
    '0061-fig1': ('later_annotation', '实际查看整图：北辰30分钟行情栏2006/12/12，嵌12/11答复及12/7箭头，晚于解答；后加图，不能由文后K证明当时必反抽或固定幅度。'),
    '0062-fig1': ('later_annotation', '实际查看整图：雅戈尔5分钟行情栏2006/12/12，嵌12/11作者短线/不全仓说明，主图含后续K；后加图，6.3原价不改为图6.26，低周期不泛化大资金。'),
    '0064-fig1': ('later_annotation', '实际查看整图：中国高科日线横轴从2006年延至次年4月，嵌12/12答复；后加图，只以作者文字核柱波与DEA/DIFF结合，不以未来行情补确认。'),
    '0065-fig1': ('later_annotation', '实际查看整图：长江电力30分钟行情栏2006/12/13，嵌12/12问答及12/7光标，晚于回答；后加图，30分已背与日线未背分开。'),
    '0065-fig2': ('later_annotation', '实际查看整图：长江电力日线光标2006/12/12，横轴右端已到次年1月，嵌12/12答复；后加图，不据后续拉升将该日线“并不存在”改写。'),
    '0066-fig1': ('later_annotation', '实际查看整图：华菱15分钟行情栏2006/12/13、箱型框，晚于12/12答复；后加图，箱型买入不是标准一买，框的制作者未核。'),
    '0067-fig1': ('later_annotation', '实际查看整图：038004日线光标2006/08/18，主图右端至2007年且叠12/13操作、三角末段标注；后加图，不按早光标认截止或把作者成本0自述认证为账户事实。'),
    '0068-fig1': ('unverified', '实际查看整图：580991日线光标2006/07/03，右端见12/13标注并嵌当日12:28答复；无明确晚于当天答复的时间证据，制作者/原站未核，不仅凭叠字认定原作者图。'),
    '0069-fig1': ('later_annotation', '实际查看整图：038004日线行情栏2006/12/15，晚于12/13答复；33(T)、21(T)、34/21神奇数字等图注不全部归作者，正文只说三角第五波末与时间周期点。'),
    '0069-fig2': ('later_annotation', '实际查看整图：000928日线光标2006/03/02，主图右端越过2007标记，晚于12/13；后加图，平台式非三角/不补缺口原句与图注身份分开。'),
    '0070-fig1': ('later_annotation', '实际查看整图：000928周线光标2004/07/23，横轴右端至2007年、已攻上250周线；后加图，12/13当时250周线支撑有效条件不按后续改成已验证保证。'),
    '0071-fig1': ('unverified', '实际查看整图：六种组合以3行2列对应陷阱式、反转式、中继式，名称与正文相符；无制作者/制作时间，未核原作者；示意线不能证明概率各半、实际买卖可无风险执行。'),
    '0072-fig1': ('unverified', '实际查看整图：驰宏日线历史图至2005年底，光标2004/08/18；蓝字正文与2005/10/25中枢说明/额外箭头为未核图注，作者正文仅列7/27和12/8买点，原图源未核。'),
    '0073-fig1': ('unverified', '实际查看整图：北辰30分钟行情栏2006/12/8，嵌第16课文字并画21天/175(T)；所示行情早于12/14，不能仅据彩色/叠字判后发；21天计数与175(T)非正文已证明时间之窗定律，制作者未核。'),
}
for short, (status, note) in notes.items():
    propose('figures', short, {'origin_status': status, 'note': note},
            '实际检查原页、整图、行情栏、主图右端与示意图；明确文后行情才标后加，未明原发身份保留unverified；图注不替正文。')
assert len(ops) == 17
plan = {'stage': 'C/E-source-provenance', 'plan_format': 1, 'schema_version': meta['schema_version'], 'base_graph_version': meta['graph_version'],
        'documents': [dict(r) for r in db.execute('SELECT * FROM documents ORDER BY id')], 'new_units': [], 'operations': ops,
        'pending': ['第74页006-12读者日期沿用已核null，不补推定年份；64无时间追问/回答保留未知时间。'],
        'visual_pages': list(range(58, 76)), 'reviewer': 'Codex 主代理 / 第15至16课源身份与原图核对'}
out = Path(__file__).parent / 'stage-c-l015-l016-source-plan.json'
out.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'operations': len(ops), 'passages': 3, 'figures': 14, 'base': meta['graph_version']}, ensure_ascii=False))
db.close()
