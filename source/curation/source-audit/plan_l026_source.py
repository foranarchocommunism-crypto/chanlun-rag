"""Metadata-only corrections after visual reading of upper PDF166-178."""
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
assert metadata['graph_version'] == '0.1.0-review-c03707cf7b67'
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
        assert not any(r['review_status'] == 'reviewed' for r in refs)
        item['affected_references'] = refs
    ops.append(item)


for short in ['0173-b011', '0173-b012', '0173-b013', '0173-b014', '0174-b000', '0174-b001']:
    propose('passages', short, {'published_at': '2007-02-01 15:32:19'},
            '实际PDF173：2/1 15:32:19头在前段尾，只管其后“今天因为一个1分钟背驰反弹”等至174星号；原173-b010仍1/31，不改其正文日期。')
notes = {
    '0169-fig1': ('later_annotation', '实际整图：上证5分顶部光标2007/01/30，主图右端至1/31，晚于1/30 15:25解盘；5分背驰当时判断与蓝线/未来K分开。'),
    '0174-fig1': ('later_annotation', '实际整图：上证5分行情栏2/1而主图右端至2/2，晚于2/1 15:32；较上次弱和周线形成中的当日判断，不按后图回填已确认。'),
    '0174-fig2': ('later_annotation', '实际整图：上证前复权日线行情栏2007/02/01，晚于1/31 21:30回复；图中MJ_PPOS非正文MACD公式，方框/百分比柱值来源未核，不自行补级别算法。'),
    '0176-fig1': ('later_annotation', '实际整图：600677日线行情栏2/1报收6.89，但主图在2月刻度之后已有多根K并升至9.85，含2/1答复后的行情；未核制图人，不用右端反弹证明当时250周线5.9条件必兑现。'),
    '0177-fig1': ('unverified', '实际整图：600836一分钟行情栏2/1，标14:30中枢后回轴二买，右端仍该日，未见晚于2/1答复日期的确定行情；叠读者/作者框各有署名，原制作者未核。'),
    '0178-fig1': ('unverified', '实际整图：600836三十分顶部光标1/23，横轴右端1/24，早于2/1回复；标1/4 10:00一买和1/18 11:00二买可对正文，不仅凭叠框判后加，原发身份未核。'),
}
for short, (status, note) in notes.items():
    propose('figures', short, {'origin_status': status, 'note': note},
            '实际阅读原页、整图、行情栏和主图右端；明确文后行情才标后加，图中指标/框线不当已核作者命题。')
assert len(ops) == 12
plan = {'stage': 'C/E-source-provenance', 'plan_format': 1, 'schema_version': metadata['schema_version'],
        'base_graph_version': metadata['graph_version'], 'documents': [dict(r) for r in db.execute('SELECT * FROM documents ORDER BY id')],
        'new_units': [], 'operations': ops, 'visual_pages': list(range(166, 179)),
        'pending': ['173页“周线中线”与176页“不赞成顺便斩仓”、168“负价格”等原词保留，不静默改成中枢/随便/市场报价负数。'],
        'reviewer': 'Codex 主代理 / 第26课源时间与原图核对'}
path = Path(__file__).parent / 'stage-c-l026-source-plan.json'
path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
db.close()
sys.stdout.reconfigure(encoding='utf-8')
print(json.dumps({'operations': len(ops), 'passages': 6, 'figures': 6, 'base': metadata['graph_version']}, ensure_ascii=False))
