"""Metadata-only source review after visually reading upper actual PDF144-166."""
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
meta = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert meta['graph_version'] == '0.1.0-review-a38ea0d31c7c'
ops = []


def propose(table, short, after, reason):
    id = DOC + '-p' + short
    row = dict(db.execute(f'SELECT * FROM {table} WHERE id=?', (id,)).fetchone())
    after = {key: value for key, value in after.items() if row[key] != value}
    assert after, id
    item = {'table': table, 'id': id, 'before': {key: row[key] for key in after}, 'after': after, 'reason': reason}
    if table == 'passages':
        item['text_sha256'] = hashlib.sha256(row['text'].encode()).hexdigest()
        refs = [dict(r) for r in db.execute('SELECT e.id,e.claim_id,c.review_status FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE e.passage_id=?', (id,))]
        assert not any(r['review_status'] == 'reviewed' for r in refs), id
        item['affected_references'] = refs
    ops.append(item)


propose('passages', '0149-b009', {'role': 'reader', 'speaker': '赚到了', 'published_at': None},
        '实际PDF149：前段末“赚到了：”引出读者对两次回试的追问，本段在“大盘”读者头之前，未记时间，不能继承15:56作者身份。')
for short in ['0150-b005', '0150-b006']:
    propose('passages', short, {'role': 'reader', 'speaker': '天山飞狐', 'published_at': None},
            '实际PDF150：“天山飞狐”署名与中枢级别提问在下一黄色作者21:51:23头之前，未记读者时间。')
for short in ['0151-b007-s01', '0151-b008']:
    propose('passages', short, {'speaker': None},
            '实际PDF151：作者引用两条未署名读者言论，左引号不是读者姓名；首条时间14:12:16仍保留。')
propose('passages', '0151-b009', {'speaker': None, 'published_at': '2007-01-24 14:59:52'},
        '实际PDF151：第二条未署名读者话在前段末14:59:52头之后，闭引号止于本段；不继承首条14:12:16。')
for block in range(10, 16):
    propose('passages', f'0151-b{block:03d}',
            {'role': 'author_commentary', 'speaker': '缠中说禅', 'published_at': '2007-01-24 15:40:48'},
            '实际PDF151：两条斜体引述在上一段闭引号结束，“看来各位”以下恢复本篇作者解盘，直至星号结束；不把作者段误记引号读者。')
for block in range(4, 7):
    propose('passages', f'0156-b{block:03d}', {'published_at': '2007-01-25 21:16:36'},
            '实际PDF156：图后独立21:16:36时间头支配本头及随后重复的作者展望，不继承15:27:08；星号后才进入回复栏目。')
for block in range(3, 7):
    propose('passages', f'0161-b{block:03d}', {'published_at': '2007-01-29 15:22:17'},
            '实际PDF161：1/29 15:22:17头在前段尾，管辖其后“本ID说到做到”等至星号段；不覆盖前段1/26原文日期。')

notes = {
    '0145-fig1': ('unverified', '实际整图：600779一分钟，行情栏2007/01/22，右端未明确晚于1/23文章；17.5/18.5/19与柱高箭头可对正文，但叠字和制作者未核，不能仅凭彩色判后加。'),
    '0146-fig1': ('later_annotation', '实际整图：600385三十分钟，行情栏2007/02/06且横轴已到2/5，晚于1/23；文字点2.92/3.28/3.22与后K分开，不用未来走势证明当时警告。'),
    '0147-fig1': ('unverified', '实际整图：海马股份000572复权周线黑白图，标20061117二买及中枢三段；左光标日期不等制图日，未见明确晚于文章行情，未核原发作者和标注人。'),
    '0147-fig2': ('unverified', '实际整图：海马股份000572复权日线黑白图，标20061113/20061206/20070104，右端未核明确晚于1/23；标注可对正文，未据此认证原作者图或未来预测。'),
    '0148-fig1': ('later_annotation', '实际整图：上证三十分钟顶部光标1/23，主图右端已到1/26，晚于1/23解盘；2870.12线和三角形为未核制图注，不按未来结果改“仍存在”判断。'),
    '0152-fig1': ('later_annotation', '实际整图：上证六十分钟光标1/24，主图右端至2/5，晚于1/24回复；60分钟“可能”背驰和5分钟刚上零轴否定均按文字，不由后K变为预先确定。'),
    '0154-fig1': ('later_annotation', '实际整图：上证十五分钟光标1/24，右端至1/26，晚于1/24 21:12答复；括号“从图上看个人认为”在正文和图注均有，署名归属未核，不按确定作者观点引用，证据排除此尾注。'),
    '0156-fig1': ('later_annotation', '实际整图：上证三十分钟光标1/25，右端至2/6，晚于当天15:27；三角后最后一段及2700上下为当时作者判断，不作独立实证。'),
    '0158-fig1': ('later_annotation', '实际整图：601628三十分钟光标1/25，右端至2/1，晚于当天22:04回复；49/45/38与强弱分支按作者原话，不按后续行情认证必然。'),
    '0160-fig1': ('later_annotation', '实际整图：工行三十分钟光标1/26，右端至2/6，晚于当天解盘；蓝线和后K不证明作者当时“第三段是否完”已有确认。'),
    '0163-fig1': ('later_annotation', '实际整图：上证五分钟光标1/26，右端已到1/29；低点标2720.83而文用2720，不改原文，5分钟否定与1分钟肯定分别保留。'),
    '0164-fig1': ('unverified', '实际整图：上证一分钟行情栏1/26，标1/25 13:40、1/26 9:30/9:50/10:17/10:57/13:30；未见晚于1/26的主图日期，制作者未核；10:56/10:57差异按不同答复保留。'),
    '0164-fig2': ('unverified', '实际整图：000915五分钟行情栏1/26，右端亦1/26；无明确晚于回复的行情证据，叠字不等原作者图，柱缩不能取代零轴回拉及趋势比较条件。'),
}
for short, (status, note) in notes.items():
    propose('figures', short, {'origin_status': status, 'note': note},
            '实际阅读原页、整图、行情栏与主图右端；明确文后行情才标后加，制作身份未核；不以图注替代作者文字。')
assert len(ops) == 32
plan = {'stage': 'C/E-source-provenance', 'plan_format': 1, 'schema_version': meta['schema_version'],
        'base_graph_version': meta['graph_version'], 'documents': [dict(r) for r in db.execute('SELECT * FROM documents ORDER BY id')],
        'new_units': [], 'operations': ops, 'visual_pages': list(range(144, 167)),
        'pending': ['153-b012作者答复末“从图上看个人认为”括注身份未核，不进入确定作者证据；保留全文并待进一步来源核查，不直接断定其为作者或整理者。',
                    '149-b008末读者署名与161-b002末日期头仍保留原文本位置，只修正后段元数据，不重切或改字符坐标。'],
        'reviewer': 'Codex 主代理 / 第25课源身份与原图核对'}
out = Path(__file__).parent / 'stage-c-l025-source-plan.json'
out.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
db.close()
sys.stdout.reconfigure(encoding='utf-8')
print(json.dumps({'operations': len(ops), 'passages': 19, 'figures': 13, 'base': meta['graph_version']}, ensure_ascii=False))
