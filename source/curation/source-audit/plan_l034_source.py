"""Metadata-only corrections from actual PDF254-259 source and figure review."""
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
assert metadata['graph_version'] == '0.1.0-review-2c7fb5f929d2'
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


for short in ['0257-b002', '0257-b003', '0258-b000', '0258-b001', '0258-b002']:
    propose('passages', short, {'published_at': '2007-03-08 15:30:24'},
            '实际PDF257/258独立2007-03-08 15:30:24头支配5分回试、30分扩展及板块/平台自述；前段3/7两种盘整方式不改，原文与坐标保留。')
notes = {
    '0256-fig1': ('later_annotation', '实际整图60分光标2007/03/20，右端3/20，嵌3/7解盘；晚于3/7，2915.70等图价/上方框及后涨不证明作者原未来分支已确定。'),
    '0256-fig2': ('later_annotation', '实际整图30分光标3/15，右端3/15，晚于3/7；蓝框和2915.32/2858.37为后图标注，不静改正文2915/2858或建立图周期=中枢级别。'),
    '0257-fig1': ('later_annotation', '实际整图15分旧光标3/7，右端3/9，嵌3/7 15:12评论；右侧未来K明确文后，综合1/5/15/30/60观察不等作者已在当日掌握3/9结果。'),
    '0257-fig2': ('later_annotation', '实际整图5分光标3/8，主图至3/9，嵌3/8 15:30评论；原5分回试不回2858原30分中枢为该例三买，2915突破仍需确认且可再扩30分，后图不抹未来条件。'),
    '0258-fig1': ('later_annotation', '实际整图1分光标3/9，右端3/9，嵌3/8原文；5分回试/蓝框由1分显示不改变对象级别；三买已判断与2915尚待确认/可能再扩30分分别保留。'),
}
for short, (status, note) in notes.items():
    propose('figures', short, {'origin_status': status, 'note': note},
            '逐一实际看六页和本课五张完整图，比较行情栏和主图右端，PDF254前课图仅作边界核对不重复改来源。')
assert len(ops) == 10
plan = {'stage': 'C/E-source-provenance', 'plan_format': 1, 'schema_version': metadata['schema_version'],
        'base_graph_version': metadata['graph_version'], 'documents': [dict(r) for r in db.execute('SELECT * FROM documents ORDER BY id')],
        'new_units': [], 'operations': ops, 'visual_pages': list(range(254, 260)),
        'pending': ['PDF258“前面是，后面不是”的问句有AB及a+A+b/b+B+c多项，短答指代不唯一，不补a+A+b为中枢的裸规则；五图皆文后。'],
        'reviewer': 'Codex 主代理 / 第34课跨日解盘和原图来源复核'}
out = Path(__file__).parent / 'stage-c-l034-source-plan.json'
out.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
db.close()
sys.stdout.reconfigure(encoding='utf-8')
print(json.dumps({'operations': len(ops), 'passages': 5, 'figures': 5, 'base': metadata['graph_version']}, ensure_ascii=False))
