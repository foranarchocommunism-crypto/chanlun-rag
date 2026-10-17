"""Source corrections reviewed against PDF43-58, with no DB writes."""
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


propose('passages', '0045-b002', {'published_at': '2006-12-04 15:35:32'},
        '实际PDF45：13:24解盘末的15:35:32裸时间只支配后段，前段保持13:24。')
for short in ['0047-b000', '0047-b001']:
    propose('passages', short, {'role': 'reader', 'speaker': '瞎鼓捣', 'published_at': None},
            '实际PDF47为读者瞎鼓捣署名与600058提问，后有独立作者12/4 15:23:17答复；问题没有记载时间，不能沿用前位作者15:12。')
for shorts, time in [
    ('0051-b003-s01 0051-b004', '2006-11-29 15:14:38'),
    ('0052-b000 0052-b001', '2006-12-06 11:55:52'),
    ('0052-b001-s01 0052-b002 0052-b003', '2006-12-05 13:46:42'),
    ('0052-b003-s01 0052-b004 0052-b005', '2006-12-01 15:02:23'),
    ('0052-b006', '2006-12-06 15:01:20'),
]:
    for short in shorts.split():
        propose('passages', short, {'role': 'author_commentary', 'speaker': '缠中说禅', 'published_at': time},
                '实际PDF51至52解盘栏目有明确引用与多层引号：11/29建议、12/5再引12/1、外层12/6午/晚分别保存；引用不是新读者答复，末尾裸日期只管下一段。')

notes = {
    '0046-fig1': ('later_annotation', '实际查看整图：600058周线光标2006/04/07，嵌12/4读者/作者问答，右端主图延至2007年1至2月；后加图。4/7一买及均线分析的“以上为个人理解”另有制作者署名边界，不归作者。'),
    '0048-fig1': ('unverified', '实际查看整图：茅台复权周线黑白5/10图，光标20030926，标三吻与女上第一吻/两买点，横轴到2004年；未见明确文后时间证据，原作者与标注制作者未核，不仅凭黑白图式认证原博客图。'),
    '0048-fig2': ('unverified', '实际查看整图：茅台周线彩色重绘、光标2004/07/16并叠正文，三吻/9/26/6/4标签；图示历史早于文章，制作人/制作时间仍未核，不凭彩色或叠文自动认作者或确定后发。'),
    '0049-fig1': ('unverified', '实际查看整图：茅台复权日线黑白图、光标20040618，三次吻、第一买点和MACD过零轴/柱缩标注；原作者/制作时间未核，价格复权口径不能和后图直接比较。'),
    '0049-fig2': ('unverified', '实际查看整图：茅台日线彩色历史重绘至2004年秋，光标6/18、叠正文/除权说明及三个吻；无足够文章后时间证据，制作人未核，不将黄框/箭头作为唯一作者证据。'),
    '0050-fig1': ('unverified', '实际查看整图：茅台日线黑白复权图，光标20030926，多个吻箭头及后续背驰卖标记、横轴至2004年；来源未核，不由箭头给出唯一可执行九吻算法。'),
    '0050-fig2': ('unverified', '实际查看整图：彩色日线历史重绘、光标2004/02/25，3/26吻与4/8背驰卖，正文9/26和图附9/23分别保留；参数/制作者未核，不能按图补作者具体MACD周期。'),
    '0051-fig1': ('unverified', '实际查看整图：彩色茅台日线历史重绘至2005年底，嵌正文日线买卖序列；10/27、12/22、4/26、12/13等标注可见，未见2006/12/5之后行情，原发/制作者未核。'),
    '0052-fig1': ('later_annotation', '实际查看整图：浦东金桥日线光标2006/12/5，嵌读者红柱缩/作者否定答复，主图右端已跨到次年1月；后加图，后续回跌不反填12/5已经背驰。'),
    '0053-fig1': ('unverified', '实际查看整图：茅台日线历史重绘至2006年秋，光标5/26，标37.68与8/7；12/5问答叠字，未核制作人/制作时间，正文37元多/未破前低不改成精确37.68一般阈值。'),
    '0053-fig2': ('unverified', '实际查看整图：2004/12至2005/6日线历史重绘，4/13与4/26及两MACD面板12/26/9和12/26/9/2可见；作者只说周期长一倍，不能用未知面板设置断言作者已给24/52/18算法。'),
    '0054-fig1': ('later_annotation', '实际查看整图：大冷股份日线光标2006/12/5，右端主图至次年1月；读者吸筹判断与作者可以/最好用买点分析分框，不把笼统可以视为逐项认定资金事实。'),
    '0054-fig2': ('later_annotation', '实际查看整图：茅台30分钟图行情栏2006/12/8，嵌12/6问答及12/1 13:30卖、12/6 13:30回零轴箭头；后加，周/日背驰未成不以文后价格改写。'),
    '0055-fig1': ('later_annotation', '实际查看整图：000503三十分钟图行情栏2006/12/7，嵌12/6问答和12/1卖点，晚于答复；后加图，9.7/9.2是作者原例，不能证明所有系统效率最优。'),
    '0056-fig1': ('later_annotation', '实际查看整图：000503五分钟图行情栏2006/12/7、光标12/6 11:00，标12/5 10:25回买并有后续K；晚于12/6答复，后加图，时间及级别以正文独立核查。'),
    '0056-fig2': ('later_annotation', '实际查看整图：中国联通历史周线重绘带2011/08/09行情栏，嵌12/6问答与2005/6/3、10/21、2006/8/7标注；后加图，不能用重绘价替正文两次2.43或2.19。'),
    '0057-fig1': ('later_annotation', '实际查看整图：中国联通30分钟图行情栏2006/12/8，光标11/24，标11/14 13:30 2.68后有12/8行情；后加图，原答复截至12/6未有一卖的状态不倒填。'),
    '0057-fig2': ('later_annotation', '实际查看整图：中兴通讯历史周线重绘带2011/08/09行情栏；读者99年4/30/03年1/2与作者99年4/30二买、03年1/3一买分框，图另标99年5/14；后加图，不按图覆写作者原日期/12.69。'),
}
for short, (origin, note) in notes.items():
    propose('figures', short, {'origin_status': origin, 'note': note}, '主代理实际查看PDF原页、整图、行情栏、右端与标注身份；未确认图源与后加证据分别记录，文字命题不只靠配图。')
assert len(ops) == 32
plan = {'stage': 'C/E-source-provenance', 'plan_format': 1, 'schema_version': meta['schema_version'],
        'base_graph_version': meta['graph_version'], 'documents': [dict(r) for r in db.execute('SELECT * FROM documents ORDER BY id')],
        'new_units': [], 'operations': ops, 'pending': [], 'visual_pages': list(range(43, 59)),
        'reviewer': 'Codex 主代理 / 第13至14课来源及配图核对',
        'adjacent_figure_unchanged': DOC + '-p0043-fig1'}
out = Path(__file__).parent / 'stage-c-l013-l014-source-plan.json'
out.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'operations': len(ops), 'passages': 14, 'figures': 18, 'base': meta['graph_version']}, ensure_ascii=False))
db.close()
