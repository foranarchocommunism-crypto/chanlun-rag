"""Metadata-only corrections from actual PDF273-279 source and figure review."""
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
assert metadata['graph_version'] == '0.1.0-review-4867e2d2c06f'
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


for short in ['0276-b005','0276-b006','0277-b000','0277-b001','0277-b002','0277-b003']:
    propose('passages', short, {'published_at': '2007-03-20 15:24:15'},
            '实际PDF276在3/19评论末尾出现3/20 15:24:15时间头，支配其后3000两日游、持股/涨停和震荡爬升段及终止符；前段3/19原文及尾头字符不改。')
notes = {
    '0276-fig1': ('later_annotation', '实际5分整图图头/右端2007/03/21，嵌3/16、3/19及3/20解盘；右侧未来K晚于三段文字，不证3/19已知3000站稳或作者行动导致上涨。'),
    '0277-fig1': ('unverified', '实际600195中牧日线图头/右端2007/03/20，嵌同日评论；图价3.29至18.50等不能静改正文3元多到11却称翻5倍，也未核复权和原博客图身份；未据后图认证收益。'),
}
for short, (status, note) in notes.items():
    propose('figures', short, {'origin_status': status, 'note': note},
            '逐一实际查看PDF273至279七页和本课两张完整图，比较时点、文字/图价、证券与来源身份。')
assert len(ops) == 8
plan = {'stage': 'C/E-source-provenance', 'plan_format': 1, 'schema_version': metadata['schema_version'],
        'base_graph_version': metadata['graph_version'], 'documents': [dict(r) for r in db.execute('SELECT * FROM documents ORDER BY id')],
        'new_units': [], 'operations': ops, 'visual_pages': list(range(273, 280)),
        'pending': ['c内部两个次级别中枢的相对层级原词保留；正文3元多到11及翻5倍与图价不同不静合，1后加图1原发未核，三K连续问题未获明确答复。'],
        'reviewer': 'Codex 主代理 / 第37课跨日解盘和原图来源复核'}
out = Path(__file__).parent / 'stage-c-l037-source-plan.json'
out.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
db.close()
sys.stdout.reconfigure(encoding='utf-8')
print(json.dumps({'operations': len(ops), 'passages': 6, 'figures': 2, 'base': metadata['graph_version']}, ensure_ascii=False))
