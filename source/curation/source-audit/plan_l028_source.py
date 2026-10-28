"""Metadata-only corrections from actual PDF187-203 visual/source review."""
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
assert metadata['graph_version'] == '0.1.0-review-031e34587250'
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


for short in ['0191-b000', '0191-b001', '0191-b002', '0191-b003']:
    propose('passages', short, {'published_at': '2007-02-07 20:43:08'},
            '实际PDF190/191：2/7 20:43:08在前段末，只管其后“把今天对大盘评价重写”等至938评论，不改前段2/6解盘日期。')
for short in ['0191-b004', '0191-b005', '0191-b006', '0191-b007', '0192-b000']:
    propose('passages', short, {'published_at': '2007-02-08 15:10:09'},
            '实际PDF191/192：新独立2/8 15:10:09头及其后5分盘背/30分扩展/777减半自述至星号，不能继承2/6时间。')
for short in ['0198-b004', '0198-b005', '0198-b006']:
    propose('passages', short, {'role': 'reader', 'speaker': '深潜', 'published_at': '2007-02-24 19:43:19'},
            '实际PDF198：深潜引2/6作者作业的引号已在前段“各位请参考…… ”闭合；“在此产生两个问题”及两问属于2/24读者，不能继承引文作者身份时间。')
notes = {
    '0190-fig1': ('later_annotation', '实际整图：上证5分光标2/6，主图右端到2/7；晚于2/6 15:12解盘。2720上/下两支仍为当时展望，图中2741.15不改正文。'),
    '0190-fig2': ('later_annotation', '实际整图：上证30分光标2/6，右端至2/13，晚于2/6解盘；未来K与2720分支分开，不据后涨反证当日确定。'),
    '0191-fig1': ('later_annotation', '实际整图：上证5分光标2/7，主图右端至2/9，嵌2/7及2/8两次解盘；两次时间和形成中/确认条件分开，不把后图框线当作者严格中枢算法。'),
    '0193-fig1': ('later_annotation', '实际整图：工行5分光标2/5，右端至2/7，晚于2/6 15:49答复；两框及4.57后反弹不把作者当日波段判断变成已独立验证。'),
    '0194-fig1': ('later_annotation', '实际整图：600016五分光标2/6，右端至2/7；嵌读者10:30问题和作者跌得多/板块位置/强势股条件，后图不证明所有5分背驰同幅度。'),
    '0195-fig1': ('later_annotation', '实际整图：600331五分光标2/6，右端至2/7，晚于当日16:35；注明5号已背与今后两天待看三买，不由未来拉起改为已确认突破。'),
    '0197-fig1': ('unverified', '实际整图：上证5分光标2/6，右端仍2/6，标三个5分中枢和第二为30分以上三卖；原发制作者未核，读者后来第二中枢日期疑问未由图自动解决。'),
    '0198-fig1': ('unverified', '实际整图：上证1分顶部光标2/5，右端已2/6但不晚于2/6夜间作者答案；最低1分以下的柱高比较是该快速例，不能据图补正式秒级中枢原数据。'),
    '0199-fig1': ('unverified', '实际整图：上证1分行情栏2/6，右端亦2/6，标02051410—1436与次日9:51—10:08；制作者未核，“一分中枢第三段弱”不补数值阈值。'),
    '0201-fig1': ('unverified', '实际整图：600151五分行情栏2/6，右端亦2/6，嵌2/6 22:35答复；图日期不足判后加，原发身份未核；1分背驰导致5分上涨与扩展过程仍按文字。'),
}
for short, (status, note) in notes.items():
    propose('figures', short, {'origin_status': status, 'note': note},
            '实际查看整图、行情栏、主图右端和嵌框署名；明确文后行情才判后加，原发未核与语义认可分开。')
assert len(ops) == 22
plan = {'stage': 'C/E-source-provenance', 'plan_format': 1, 'schema_version': metadata['schema_version'],
        'base_graph_version': metadata['graph_version'], 'documents': [dict(r) for r in db.execute('SELECT * FROM documents ORDER BY id')],
        'new_units': [], 'operations': ops, 'visual_pages': list(range(187, 204)),
        'pending': ['2/24读者关于第二中枢笔误的主张和CCTV解读不当作者认可；2/26作者明确回复单独取证，保留0130/130等原时间字符串。'],
        'reviewer': 'Codex 主代理 / 第28课日期、嵌引读者与原图来源复核'}
out = Path(__file__).parent / 'stage-c-l028-source-plan.json'
out.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
db.close()
sys.stdout.reconfigure(encoding='utf-8')
print(json.dumps({'operations': len(ops), 'passages': 12, 'figures': 10, 'base': metadata['graph_version']}, ensure_ascii=False))
