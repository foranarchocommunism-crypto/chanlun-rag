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
 (253,1):'实际查看PDF253及单图：内嵌11月20日原文，日线横轴已至2008年2月，晚于该文；后期截图，制作人与数据源未核，不能认证当时MACD反弹预测。',
 (259,1):'实际查看PDF259及单图：光标11/29但行情延至2008年2月并含4195.75，晚于文章；后期截图，不以未来走势倒填30分钟中枢当时已形成。',
 (261,2):'实际查看PDF261第二图：12月3日文章旁30分钟图光标12/03但横轴已至12/05；后期截图，制作人未核。第一图15分钟截止12/03另留unverified，不能合并身份。',
 (264,1):'实际查看PDF264第一图：万科周线光标2007/11/02，但横轴含次年1至6月行情，晚于12月3日课程；后期图不证明作者当时知晓未来跌幅，40.78为正文原数。',
 (265,1):'实际查看PDF265及单图：5分钟/30分钟上下图光标2007/12/06、行情亦越过12/04，晚于12月3日课程；后期示例图，不倒填当时收口已完成或突破已经确认。',
 (266,1):'实际查看PDF266及单图：嵌12月5日原文、光标12/05但横轴行情至12/11，后期截图；不可用后续确认代替当时5010待站稳条件。',
 (267,1):'实际查看PDF267及单图：嵌12月5日原文、光标12/05，横轴行情已至2008年1月，后期图；正文5032重回才是事实的时态保持。',
 (268,1):'实际查看PDF268及单图：嵌12月6日陷阱说明，图头已是12/07，晚于所配文章；后期截图，不能用次日回升替代当日力度比较与中枢震荡的条件。',
 (269,1):'实际查看PDF269及单图：光标12/10、内嵌周线选择12/07，但主日线已至2008年2月，晚于12月7日文章；后期截图，不倒填当周底分型已成立。',
 (272,1):'实际查看PDF272及单图：嵌12月12日原文，图头与行情12/13，标有之后的1分钟三卖；后期截图，不反填12月12日已确立三卖或混同5分钟三卖。',
 (276,1):'实际查看PDF276及单图：日线光标12/14、周线光标12/07，但日线行情已至2008年2月；晚于12月17日文章。后期图，不倒填当日周底确认或未来跌幅。',
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
path = Path(__file__).with_name('stage-c-l089-l090-figure-plan.json')
path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'base_graph_version': plan['base_graph_version'], 'operations': len(operations), 'path': str(path)}, ensure_ascii=False))
