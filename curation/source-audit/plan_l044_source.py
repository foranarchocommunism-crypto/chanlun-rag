"""Lesson44 source metadata plan, fixed original text and geometry."""
import hashlib,json,re,sqlite3,sys
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';DOC='volume_1-a53e99c37ca5'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
meta={r['key']:json.loads(r['value']) for r in db.execute('select * from metadata')};assert meta['graph_version']=='0.1.0-review-3f0839731b9a'
ops=[]
def propose(table,id,after,reason):
 row=dict(db.execute(f'select * from {table} where id=?',(id,)).fetchone());after={k:v for k,v in after.items() if row[k]!=v};assert after
 item=dict(table=table,id=id,before={k:row[k] for k in after},after=after,reason=reason)
 if table=='passages':
  refs=[dict(r) for r in db.execute('select e.id,e.claim_id,c.review_status from evidence e join claims c on c.id=e.claim_id where e.passage_id=?',(id,))];assert not any(r['review_status']=='reviewed' for r in refs);item.update(text_sha256=hashlib.sha256(row['text'].encode()).hexdigest(),affected_references=refs)
 ops.append(item)
for row in db.execute("select * from passages where unit_id='lesson-044' order by pdf_page,block_index,id").fetchall():
 short=row['id'].split('-p')[1];t=row['published_at']
 if short in {'0318-b006','0319-b000','0319-b001'}:propose('passages',row['id'],dict(published_at='2007-04-11 15:38:12'),'318前段尾4/11时间头支配后文及跨319续段，前318-b005仍4/10；原字符尾头及映射不改。')
 elif t and re.fullmatch(r'2007-\d{2}-\d{2}\d{2}:\d{2}:\d{2}',t):propose('passages',row['id'],dict(published_at=t[:10]+' '+t[10:]),'原页作者时刻和承接可核，仅日期与时刻空格规范，不改数字原字身份。')
notes={
 '0317-fig1':'图署张大山习作，属后加学习者示意、非作者原图；蓝1/2和GG为图解标注，正文是5分回试类型高点，未以其GG定义替代；图中c`标法与正文最后5分中枢需分别保留。',
 '0318-fig1':'图署张大山习作，为学习者分层示意、非作者原发证据；紫框/红线用于说明全仓及分批，但无固定仓位比例、几何价格或成交/收益证明，不据图补完整级别算法。',
}
for short,note in notes.items():propose('figures',DOC+'-p'+short,dict(origin_status='later_annotation',note=note),'实际查看PDF316至320五页及两幅完整图，署名张大山习作；保留汇编学习者图与作者文字层次，制作者真实身份/原发布时未核。')
assert len(ops)==17 and sum(x['table']=='passages' for x in ops)==15
plan=dict(stage='C/E-source-provenance',plan_format=1,schema_version=meta['schema_version'],base_graph_version=meta['graph_version'],documents=[dict(r) for r in db.execute('select * from documents order by id')],new_units=[],operations=ops,visual_pages=list(range(316,321)),pending=['图两张学习者习作不作作者证据，正文破位对象保留原嵌套级别不自动等GG；小背驰-大转折只有必要无充分，未补等值/成交/比例或盈利保证。'],reviewer='Codex 主代理 / 44课必要条件、操作阈值与学习者图来源复核')
Path(__file__).with_name('stage-c-l044-source-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(dict(operations=len(ops),passages=15,figures=2,base=meta['graph_version']),ensure_ascii=False))
