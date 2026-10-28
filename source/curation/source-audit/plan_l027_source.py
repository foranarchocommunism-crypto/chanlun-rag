"""Source timestamps and figure provenance after reading actual PDF178-187."""
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
assert metadata['graph_version'] == '0.1.0-review-31581ef72e83'
ops = []


def propose(table, id, after, reason):
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


body_ids = [r['id'] for r in db.execute("SELECT id FROM passages WHERE unit_id='lesson-027' AND role='author_body'")]
assert len(body_ids) == 19
for id in body_ids:
    propose('passages', id, {'published_at': '2007-02-02 15:11:27'},
            '实际PDF178第27课标题明确2007-02-02 15:11:27，19正文段属于此标题直至182作者解盘；补来源原记时间，不改原文字符。')
for short in ['0182-b010', '0182-b011', '0182-b012', '0182-b013']:
    propose('passages', DOC + '-p' + short, {'published_at': '2007-02-05 15:18:33'},
            '实际PDF182：2/5 15:18:33在前段尾，只管其后周线第一段探底至000938评论，不能继承2/2解盘时间。')
for short in ['0182-b014', '0183-b000', '0183-b001']:
    propose('passages', DOC + '-p' + short, {'published_at': '2007-02-05 15:25:03'},
            '实际PDF182/183：2/5 15:25:03头在前段末，只管其后不追高/999中枢第三段至星号；不改前段000938的15:18。')
notes = {
    '0179-fig1': ('unverified', '实际整图：000002季线，顶部光标2006/12/29，右端2007季度K无法确定晚于2/2；标36.70/3.20/15.99/3.12可对正文。13/23/17数字与正文17周单位分开，不以图注补原文。'),
    '0181-fig1': ('later_annotation', '实际整图：600663月线，行情栏2011/08/12，晚于2007/2/2多年；后加重绘图，均线/MJ_MACD及除权标志未核，不以未来K认证作者历史性底部推断。'),
    '0181-fig2': ('unverified', '实际整图：600685季线，顶部光标2005/06/30，右端仅见至2006/2007交界季K，未明确证明晚于2/2；2.21标注与2005第三季度原文分开，光标不能改买点日期，原发身份未核。'),
    '0183-fig1': ('later_annotation', '实际整图：上证30分光标2007/02/05，主图右端至2/8，晚于2/5 15:18；周线探底/5分背驰段尚待定位原话不被后续行情回填确认。'),
    '0183-fig2': ('later_annotation', '实际整图：上证5分光标2/5，主图右端已见2/6之后走势；晚于2/5解盘，柱高/面积数字与作者文字条件分开，不以涨后K验证“明天很可能”。'),
    '0185-fig1': ('later_annotation', '实际整图：600331五分钟顶部2/2，右端已到2/5，晚于2/2问答；010935/011410标注为2/1时点，作者只认可两侧段可比较，不据此认同读者只有13:15—14:00中枢。'),
    '0185-fig2': ('later_annotation', '实际整图：601628十五分钟顶部2/5，主图右端至2/7，晚于2/2 16:43；回轴只是一个条件、须看后续新低及低级别结束，不把后图反弹预设当时已确认背驰。'),
}
for short, (status, note) in notes.items():
    propose('figures', DOC + '-p' + short, {'origin_status': status, 'note': note},
            '实际查看原页、整图、行情栏和主图右端；明确文后时间才标后加，原发未核与语义认可分开。')
assert len(ops) == 33
plan = {'stage': 'C/E-source-provenance', 'plan_format': 1, 'schema_version': metadata['schema_version'],
        'base_graph_version': metadata['graph_version'], 'documents': [dict(r) for r in db.execute('SELECT * FROM documents ORDER BY id')],
        'new_units': [], 'operations': ops, 'visual_pages': list(range(178, 188)),
        'pending': ['179原文“17周”与季度跨度、185股价新低后是否创新低的代词、184读者中信证券600640代码名组合均保留不静改。'],
        'reviewer': 'Codex 主代理 / 第27课原页、日期和配图来源复核'}
out = Path(__file__).parent / 'stage-c-l027-source-plan.json'
out.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
db.close()
sys.stdout.reconfigure(encoding='utf-8')
print(json.dumps({'operations': len(ops), 'passages': 26, 'figures': 7, 'base': metadata['graph_version']}, ensure_ascii=False))
