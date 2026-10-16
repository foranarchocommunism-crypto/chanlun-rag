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
    245: '实际查看PDF245及单图：文章11月12日，图头光标2007/11/13且横轴行情至11/14以后，属后期截图；制作人未核。不能据未来反抽行情倒填11月12日反弹已持续或5462颈线已触及。',
    248: '实际查看PDF248及单图：光标11/13但横轴行情至12月、含4778.73，晚于11月14日文章；后期截图，制作人未核。原文说5462重回仍看能否站住，不能用事后日线代替当时完成确认。',
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
path = Path(__file__).with_name('stage-c-l088-figure-plan.json')
path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'base_graph_version': plan['base_graph_version'], 'operations': len(operations), 'path': str(path)}, ensure_ascii=False))
