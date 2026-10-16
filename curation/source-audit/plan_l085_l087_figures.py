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
    223: '实际查看PDF223及单图：图头光标2007/10/23但横轴行情延伸至12月、含4778.73低点，晚于10月23日文章；后期截图，制作人未核。不能以该后期结果认证当日预测或改写当日未确认状态。',
    228: '实际查看PDF228及单图：内嵌作者2007-10-25 15:43:22文字且光标10/25，但横轴和行情至10/26；后期截图，制作人未核。图峰6123.64与正文邻文6124.04保留差异，不视为作者修订。',
    232: '实际查看PDF232及单图：光标2007/10/30但横轴行情至11/01，晚于10月30日文章；后期截图，制作人未核。不以未来行情倒填10月30日新中枢已经形成或当时顶部已确认。',
}
operations = []
for page, note in notes.items():
    fid = f'volume_2-5332cd1b6038-p{page:04d}-fig1'
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
path = Path(__file__).with_name('stage-c-l085-l087-figure-plan.json')
path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'base_graph_version': plan['base_graph_version'], 'operations': len(operations), 'path': str(path)}, ensure_ascii=False))
