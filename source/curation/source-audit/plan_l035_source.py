"""Metadata-only corrections from actual PDF259-265 source and figure review."""
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
assert metadata['graph_version'] == '0.1.0-review-20e3aa53bf69'
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


for shorts, date in [(['0261-b004-s01','0262-b000','0262-b001'],'2007-03-09 11:54:01'),
                     (['0262-b002','0262-b003','0262-b004'],'2007-03-12 15:20:28')]:
    for short in shorts:
        propose('passages', short, {'published_at': date},
                '实际PDF261/262作者解盘头、3/9 11:54及3/12 15:20独立时间头支配后段；文章正文与原有3/12署名回复不动。')
notes = {
    '0262-fig1': ('later_annotation', '实际整图5分图头2007/03/13且右端3/13，嵌3/9 11:54评论；后行情与30F/5F框不是作者3/9可见未来，不用图2911.41替换文2911。'),
    '0263-fig1': ('unverified', '实际整图5分图头/右端2007/03/12，嵌同日15:52答复；日期同日不能证明原博客发布身份，蓝框与2911.41/2858.37等标价保留为汇编图，不静改正文整数。'),
    '0264-fig1': ('later_annotation', '实际整图5分图头2007/03/13且右端3/13，嵌3/12 16:28评论；2892.40/2911.41、2871.98为图标价，不抹原文尚未构成三买、次日回试条件或日线中枢可能。'),
}
for short, (status, note) in notes.items():
    propose('figures', short, {'origin_status': status, 'note': note},
            '逐一实际看PDF259至265七页和本课三张完整图，比对图头、主图右端、嵌入原答日期与来源边界。')
assert len(ops) == 9
plan = {'stage': 'C/E-source-provenance', 'plan_format': 1, 'schema_version': metadata['schema_version'],
        'base_graph_version': metadata['graph_version'], 'documents': [dict(r) for r in db.execute('SELECT * FROM documents ORDER BY id')],
        'new_units': [], 'operations': ops, 'visual_pages': list(range(259, 266)),
        'pending': ['本课行情图2幅晚于文字，1幅同日仍无原博客身份核验；严格成交递归和分钟模本不同，单类型与类型连接及次级别以下层次须分别保留。'],
        'reviewer': 'Codex 主代理 / 第35课解盘日期和原图来源复核'}
out = Path(__file__).parent / 'stage-c-l035-source-plan.json'
out.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
db.close()
sys.stdout.reconfigure(encoding='utf-8')
print(json.dumps({'operations': len(ops), 'passages': 6, 'figures': 3, 'base': metadata['graph_version']}, ensure_ascii=False))
