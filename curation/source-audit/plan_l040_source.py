"""Metadata-only corrections from actual PDF291-301 source and figure review."""
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
assert metadata['graph_version'] == '0.1.0-review-01407b1617c1'
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


groups = [
    (['0292-b002','0293-b000','0293-b001','0293-b002'], '2007-03-27 21:29:47'),
    (['0293-b003','0293-b004','0293-b005'], '2007-03-28 15:24:11'),
    (['0298-b007','0298-b008','0299-b000','0299-b001'], '2007-03-29 21:44:58'),
]
for shorts, stamp in groups:
    for short in shorts:
        propose('passages', short, {'published_at': stamp},
                '原页前段尾有独立时间头，支配后续跨页段落；依3/27晚间、3/28收盘或3/29夜间分组，不继承午间日期，原文字及尾头字符不改。')
notes = {
    '0291-fig1': ('unverified', '左侧Ai奇数回补/保护位示意与39课图同型，未见作者署名日期；仅作汇编解释图，不能补原式奇数支k范围或换档算法。'),
    '0291-fig2': ('unverified', '右侧Ai偶数卖出/保护位示意，无原发作者证明；小段折线不是完整类型的独立证明，不认证机械收益。'),
    '0292-fig1': ('later_annotation', '5分图头2007/03/30、右端晚于3/27 21:29，嵌时间窗及二线业绩评论；后K不证明当时三日确认或月季预测已知。'),
    '0292-fig2': ('later_annotation', '日线选择栏3/27而主图右端至5月刻度附近、3964.71，明显晚于所选3/27；21(T)天标注/后涨非时间窗预测的验真。'),
    '0294-fig1': ('later_annotation', '5分图头3/30、嵌读者3/27 13:38问及作者21:41答，右端晚于文字；原当日中枢震荡和两指数/级别问题不据后图改趋势背驰。'),
    '0295-fig1': ('unverified', '5分图头3/27而主图到3/28，嵌3/28 21:13答；可为答前同日行情，未证原博客身份，图周期不把1分钟以下信号升成5分背驰。'),
    '0296-fig1': ('unverified', '1分图头/主图3/28，嵌同日夜间作者和读者文字；两个绿柱面积之和对一个按文字范围，未核原发，也不把假突破案例泛作所有背驰算法。'),
}
for short, (status, note) in notes.items():
    propose('figures', short, {'origin_status': status, 'note': note},
            '逐一实际查看PDF291至301十一页和七幅完整图，比对选择栏与右端、正文/示意/读者答疑各来源。')
assert len(ops) == 18
plan = {'stage': 'C/E-source-provenance', 'plan_format': 1, 'schema_version': metadata['schema_version'],
        'base_graph_version': metadata['graph_version'], 'documents': [dict(r) for r in db.execute('SELECT * FROM documents ORDER BY id')],
        'new_units': [], 'operations': ops, 'visual_pages': list(range(291, 302)),
        'pending': ['多层换档依已成高层分解不是低买点套牢后任意改级；39总有被套与40被套非买点、零成本安全的强词分歧保留；7图3文后4原发未核。'],
        'reviewer': 'Codex 主代理 / 第40课跨日解盘、层级与原图来源复核'}
out = Path(__file__).parent / 'stage-c-l040-source-plan.json'
out.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
db.close()
sys.stdout.reconfigure(encoding='utf-8')
print(json.dumps({'operations': len(ops), 'passages': 11, 'figures': 7, 'base': metadata['graph_version']}, ensure_ascii=False))
