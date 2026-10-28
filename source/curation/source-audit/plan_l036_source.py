"""Metadata-only corrections from actual PDF265-273 source and figure review."""
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
assert metadata['graph_version'] == '0.1.0-review-bee490a04fe7'
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


for short in ['0271-b001','0271-b002','0271-b003','0271-b004','0271-b005']:
    propose('passages', short, {'published_at': '2007-03-14'},
            '实际PDF271附录谈昨晚/今天已发生行情及早上已说内容，非3/14 08:58晨帖；同日盘后无独立时分秒，保留日级精度，不猜15时具体时间。')
notes = {
    '0266-fig1': ('later_annotation', '黑白30分整图主轴右端3/16，晚于3/13 09:00正文；箭头03071330/03091030和原整数保留，不能以后图认证原先已确认突破。'),
    '0267-fig1': ('later_annotation', '实际5分整图图头3/13，右端3/13含当天盘中行情，晚于3/13 09:00开盘前正文；图0309-10:05/0307-13:25与文03091030/03071330不同，保留差异不静改。'),
    '0267-fig2': ('unverified', '实际5分整图图头与右端3/12，早于3/13正文但原博客身份未核；图0309-10:05、图价小数不替换正文03091030及整数；同段不同组合保留。'),
    '0270-fig1': ('later_annotation', '实际5分整图图头3/13且右端有当日盘中行情，晚于3/13 09:00正文；位于CCTV/3G等读者讨论下，读者三买判断不变作者认可，图只作汇编上下文。'),
    '0272-fig1': ('later_annotation', '实际5分整图右端3/16，嵌CCTV 3/14答及作者3/15 15:23解盘；右端晚于两者，读者预测/作者评论身份各自保留，后行情不证原预测。'),
}
for short, (status, note) in notes.items():
    propose('figures', short, {'origin_status': status, 'note': note},
            '逐一实际看PDF265至273九页和本课五张完整图，比较时点、图周期、文字/图标价和正文/读者归属。')
assert len(ops) == 10
plan = {'stage': 'C/E-source-provenance', 'plan_format': 1, 'schema_version': metadata['schema_version'],
        'base_graph_version': metadata['graph_version'], 'documents': [dict(r) for r in db.execute('SELECT * FROM documents ORDER BY id')],
        'new_units': [], 'operations': ops, 'visual_pages': list(range(265, 274)),
        'pending': ['附录只知3/14日级时间；五图四文后、一早于正文但原发未核，图10:05/文10:30及13:25/13:30不能静合，读者三买辩论不当作者结论。'],
        'reviewer': 'Codex 主代理 / 第36课附录时间和原图来源复核'}
out = Path(__file__).parent / 'stage-c-l036-source-plan.json'
out.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
db.close()
sys.stdout.reconfigure(encoding='utf-8')
print(json.dumps({'operations': len(ops), 'passages': 5, 'figures': 5, 'base': metadata['graph_version']}, ensure_ascii=False))
