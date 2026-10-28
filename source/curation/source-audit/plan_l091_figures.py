"""Write only a bounded figure-origin plan after actual PDF/crop inspection."""
import json
import sqlite3
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2]
KB = AGENT.parent / 'shared-knowledge/v0.1.0'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
notes = {
 (282,1):'实际查看PDF282及单图：内嵌12月20日文字，图头已为12/21且行情延至12/20后，后期截图，绘者未核。不以次日走势倒填12/20第二1分钟中枢已成或未完成线段已确认。',
 (284,1):'实际查看PDF284及单图：2008年展望文章12月20日发布，年线图光标2009/12/31、季线2009/03/31，明显后期截图；不能用2008/2009实际K线验证当时未来预测。',
 (287,1):'实际查看PDF287及单图：嵌文12月25日，图头与右端行情12/26，后期截图。不能将次日变化反填当时中枢/三类点确认。',
 (288,1):'实际查看PDF288及单图：内嵌今天12/27正文，图头12/28，后期截图；BOLL(20,2)为图显示，正文未指定唯一参数。',
 (289,1):'实际查看PDF289及单图：内嵌12/27文字、光标12/27，但行情横轴明确至12/28，后期截图；图已标大5分钟框，不能倒填12/27仍有回到5240下才升级的条件。',
}
operations = []
for (page, number), note in notes.items():
    fid = f'volume_2-5332cd1b6038-p{page:04d}-fig{number}'
    row = db.execute('SELECT * FROM figures WHERE id=?', (fid,)).fetchone()
    assert row is not None and row['origin_status'] == 'unverified'
    # Changes are scoped to previously uncited images, preserving old reviews.
    assert not any(fid in json.loads(r[0]) for r in db.execute("SELECT e.figure_ids FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed'"))
    operations.append({'table': 'figures', 'id': fid,
        'before': {'origin_status': row['origin_status'], 'note': row['note']},
        'after': {'origin_status': 'later_annotation', 'note': note},
        'reason': '原页及单图可见晚于文章的行情；光标日期并非整张图行情的截止时间。'})
plan = {'stage': 'C/E-source-provenance', 'plan_format': 1, 'schema_version': metadata['schema_version'],
    'base_graph_version': metadata['graph_version'],
    'documents': [dict(r) for r in db.execute('SELECT * FROM documents ORDER BY filename')],
    'new_units': [], 'operations': operations, 'pending': []}
db.close()
path = Path(__file__).with_name('stage-c-l091-figure-plan.json')
path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'base_graph_version': plan['base_graph_version'], 'operations': len(operations), 'path': str(path)}, ensure_ascii=False))
