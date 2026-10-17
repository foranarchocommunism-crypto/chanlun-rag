"""Save the source metadata corrections read from PDF416-427; no DB writes."""
import hashlib
import json
import sqlite3
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2]
KB = AGENT.parent / 'shared-knowledge/v0.1.0'
DOC = 'volume_2-5332cd1b6038'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
operations = []


def propose(table, id, after, reason):
    row = dict(db.execute(f'SELECT * FROM {table} WHERE id=?', (id,)).fetchone())
    after = {k: v for k, v in after.items() if row[k] != v}
    assert after, id
    item = {'table': table, 'id': id, 'before': {k: row[k] for k in after},
            'after': after, 'reason': reason}
    if table == 'passages':
        item['text_sha256'] = hashlib.sha256(row['text'].encode()).hexdigest()
        refs = [dict(x) for x in db.execute('SELECT e.id,e.claim_id,c.review_status FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE e.passage_id=?', (id,))]
        assert all(x['review_status'] != 'reviewed' for x in refs), id
        item['affected_references'] = refs
    operations.append(item)


reason = '主代理实际查看PDF425至427：原段末尾裸时间头仅支配后文，原段原日期保留；不修改text/ID/字符映射/坐标。'
for time, shorts in [
    ('2008-09-03 15:14:03', ['0425-b004', '0425-b005']),
    ('2008-09-05 15:08:42', ['0425-b006', '0425-b007', '0426-b000', '0426-b001']),
    ('2008-09-24 14:38:08', ['0427-b009']),
    ('2008-09-25 20:14:17', ['0427-b010']),
    ('2008-09-26 10:32:38', ['0427-b011', '0427-b012', '0427-b013']),
]:
    for short in shorts:
        propose('passages', DOC + '-p' + short, {'published_at': time}, reason)
propose('passages', DOC + '-p0426-b009',
        {'role': 'author_commentary', 'speaker': '缠中说禅', 'published_at': '2008-09-11 16:14:14'},
        'PDF426实际页面显示“还是那句话，无欲无求，按图作业。”是9/11作者解盘结束语，并非读者署名；其后的9/12裸日期只支配下一段。')
propose('passages', DOC + '-p0426-b010',
        {'role': 'author_commentary', 'speaker': '缠中说禅'},
        'PDF426的9/12 12:59:29后为同栏目作者解盘“收盘马上有事，先说两句”，没有读者署名；原先把前文结束语误作speaker。保留作者90%估计非独立统计身份。')

figure_notes = {
    417: '实际查看原页与单图：嵌8/20与8/21两日解盘、光标8/20，主日线右侧到9月并显示1802.3；为文后图，不能按光标认截止或反填2455/2656分支。',
    420: '实际查看原页与单图：嵌8/25和8/26，主日线延至9月含1802.3，月线插图到2009年且有1664.9；后加图，正文可能扩展更大中枢未成为已确认事实。',
    422: '实际查看原页与单图：8/29文字及光标，但月线主图已到2009年，含后续低点/反弹；后加图；图嵌09:15:01不是课程正文已核时间，正文仅记8/29。',
    423: '实际查看原页与单图：8/29文字/光标，主日线含9月1802.3，周线插图至12月含1664.9；后加图；正文2601/2284/2455不按图2601.5/2284.6/2455.5替换。',
    425: '实际查看原页与单图：嵌9/1和9/3文字、光标9/4；主日线到11月并有1664.9，月线插图到2009年；后加图；图中2329/2203.3不替代9/3正文2329或倒填当时结果。',
}
for page, note in figure_notes.items():
    propose('figures', f'{DOC}-p{page:04d}-fig1', {'origin_status': 'later_annotation', 'note': note},
            '已实际查看整图及插图右端，显示正文发表后行情；制作人/原网页来源未核，不作作者原始配图认证。')

plan = {'stage': 'C/E-source-provenance', 'plan_format': 1,
        'schema_version': metadata['schema_version'], 'base_graph_version': metadata['graph_version'],
        'documents': [dict(r) for r in db.execute('SELECT * FROM documents ORDER BY id')],
        'new_units': [], 'operations': operations, 'pending': [],
        'visual_pages': list(range(416, 428)), 'reviewer': 'Codex 主代理 / 107至108课来源核对'}
assert len(operations) == 18
out = Path(__file__).parent / 'stage-c-l107-l108-source-plan.json'
out.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'plan': str(out), 'passage_operations': 13, 'figure_operations': 5,
                  'affected_reviewed_evidence': 0, 'base_graph_version': metadata['graph_version']}, ensure_ascii=False))
db.close()
