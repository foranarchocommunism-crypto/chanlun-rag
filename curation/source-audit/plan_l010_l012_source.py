"""Metadata-only review from the actually viewed upper PDF27-43."""
import hashlib
import json
import sqlite3
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2]
KB = AGENT.parent / 'shared-knowledge/v0.1.0'
DOC = 'volume_1-a53e99c37ca5'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
meta = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
ops = []


def op(table, short, after, reason):
    id = DOC + '-p' + short
    row = dict(db.execute(f'SELECT * FROM {table} WHERE id=?', (id,)).fetchone())
    changes = {k: v for k, v in after.items() if row[k] != v}
    if not changes:
        return
    item = {'table': table, 'id': id, 'before': {k: row[k] for k in changes}, 'after': changes, 'reason': reason}
    if table == 'passages':
        item['text_sha256'] = hashlib.sha256(row['text'].encode()).hexdigest()
        refs = [dict(r) for r in db.execute('SELECT e.id,e.claim_id,c.review_status FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE e.passage_id=?', (id,))]
        assert not any(r['review_status'] == 'reviewed' for r in refs), id
        item['affected_references'] = refs
    ops.append(item)


def commentary(shorts, time, reason):
    for short in shorts.split():
        op('passages', short, {'role': 'author_commentary', 'speaker': '缠中说禅', 'published_at': time}, reason)


reason = '主代理实际查看PDF29至30解盘栏目：连续即时提示及作者明确自引昨日提示；前段末新时间仅管后文，结束引号不是读者署名。原文/ID/映射/坐标保持。'
for shorts, time in [
    ('0029-b002 0029-b003 0030-b000', '2006-11-24 12:15:10'),
    ('0030-b001', '2006-11-24 12:17:20'),
    ('0030-b001-s01 0030-b002', '2006-11-23 13:42:46'),
    ('0030-b003 0030-b004', '2006-11-23 15:11:58'),
    ('0030-b005', '2006-11-24 13:34:49'),
    ('0030-b006', '2006-11-24 13:50:35'),
    ('0030-b007', '2006-11-24 14:14:17'),
    ('0030-b008', '2006-11-24 15:00:18'),
]:
    commentary(shorts, time, reason)
commentary('0032-b013 0032-b014 0032-b015 0033-b000 0033-b001 0033-b002 0033-b003', '2006-11-27',
           'PDF32新蓝色标题“经典回放”开始独立11/27文章，不是11/24答复续文；仅保留标题提供日期，不造时分秒。')
for short in '0033-b004 0033-b005 0033-b006 0034-b000 0034-b001 0034-b002'.split():
    op('passages', short, {'role': 'unknown', 'speaker': '喜欢数学的女孩（正文自称旧名，原站身份未核）', 'published_at': '2005-08-05 12:15:00'},
       'PDF33原署名为喜欢数学的女孩，外层作者自称这是自己的旧名转载，非读者评论；原站身份/最早7月说法未取证，按自称转载待核，保留原署名正文，不进入直接作者证据。')
for shorts, time in [
    ('0034-b003', '2006-11-27 12:18:55'),
    ('0034-b004', '2006-11-27 12:19:44'),
    ('0034-b005 0034-b006', '2006-11-27 15:10:23'),
    ('0034-b007', '2006-11-28 12:15:13'),
    ('0034-b008 0034-b009 0034-b010 0034-b011 0034-b012 0034-b013 0034-b014 0034-b015 0035-b000', '2006-11-28 14:56:17'),
    ('0038-b005 0038-b006 0038-b007 0038-b008 0038-b009 0038-b010', '2006-11-29 15:14:38'),
    ('0039-b000 0039-b001', '2006-11-30 15:13:57'),
    ('0039-b001-s01 0039-b002', '2006-11-29 15:14:38'),
    ('0042-b005', '2006-12-01 11:37:58'),
    ('0042-b006', '2006-12-01 12:16:49'),
    ('0042-b007 0043-b000 0043-b001', '2006-12-01 15:02:23'),
]:
    commentary(shorts, time, '实际查看PDF34至43同栏解盘及明示附录自引；解析误把正文当署名，恢复作者评论身份，裸日期只支配后文，引用11/29建议不变成11/30新回复。')

figure_notes = {
    '0029-fig1': ('unverified', '实际查看PDF29整页及单图：上证5分钟图到11/24，箭头标11/23 13:20及13:45；与所引提示有时间关系，但无制作署名或原站取证，未确认原作者，不能由箭头独立证明背驰/统计准确率。'),
    '0029-fig2': ('unverified', '实际查看PDF29整页及单图：深成指5分钟图到11/24，与上证图并列，13:20/13:45箭头和走势差异可见；制作人/原发时间未核，图形语义与作者一般命题分开。'),
    '0035-fig1': ('later_annotation', '实际查看PDF35及单图：光标2006/11/27、嵌当日问答，主图右侧越过11/27到12月标记，含后续行情，为后加整理图；不按光标认截止，文字独立支持缩量确认再放量。'),
    '0041-fig1': ('unverified', '实际查看PDF41及单图：茅台复权日线黑白图、5/10/30，标男上位第二次缠绕/空头陷阱第一买点和第二买点，光标20060807，横轴至9月以后；未见足够后发时间证据，原作者/制作时间仍未核；不等严格一二类点证据。'),
    '0042-fig1': ('later_annotation', '实际查看PDF42及单图：茅台历史日线重绘图带2011/08/09行情栏、黄框作者文字和8/7、9/14箭头，属后加整理版；图嵌12:41:24与正文12:03:48分开，不能反填课程时刻。'),
    '0043-fig1': ('later_annotation', '实际查看PDF43及单图：ST东热周线重绘图带2011/08/09行情栏与2005-07-22/2005-11-03标注、黄框12/1答复，为后加整理版；原答复只写月日，不据未知图注补年份或改原价2.2/2.6。'),
}
for short, (status, note) in figure_notes.items():
    op('figures', short, {'origin_status': status, 'note': note}, '实际检查整图及右端、行情栏和插图，区分后加整理版与尚未核实的原图；并非同页即作者观点证明。')
plan = {'stage': 'C/E-source-provenance', 'plan_format': 1, 'schema_version': meta['schema_version'],
        'base_graph_version': meta['graph_version'], 'documents': [dict(r) for r in db.execute('SELECT * FROM documents ORDER BY id')],
        'new_units': [], 'operations': ops, 'pending': ['2005旧文自称署名尚未原站取证，不支持直接作者一般命题；课程10标题仅11-24不补时分秒。'],
        'reviewer': 'Codex 主代理 / 第10至12课源身份与图文核对', 'visual_pages': list(range(27, 44))}
out = Path(__file__).parent / 'stage-c-l010-l012-source-plan.json'
out.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'operations': len(ops), 'passages': sum(x['table'] == 'passages' for x in ops), 'figures': 6, 'base': meta['graph_version']}, ensure_ascii=False))
db.close()
