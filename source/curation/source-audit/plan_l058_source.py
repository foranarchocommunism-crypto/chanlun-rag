"""Plan visually checked lesson58 author identities, dates and four figures."""
import hashlib,json,re,sqlite3,sys
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';DOC='volume_1-a53e99c37ca5'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
meta={r['key']:json.loads(r['value']) for r in db.execute('select * from metadata')};assert meta['graph_version']=='0.1.0-review-63d8b41da992'
ops=[]
def propose(table,id,after,reason):
 row=dict(db.execute(f'select * from {table} where id=?',(id,)).fetchone());after={k:v for k,v in after.items() if row[k]!=v};assert after
 op=dict(table=table,id=id,before={k:row[k] for k in after},after=after,reason=reason)
 if table=='passages':
  refs=[dict(r) for r in db.execute('select e.id,e.claim_id,c.review_status from evidence e join claims c on c.id=e.claim_id where e.passage_id=?',(id,))];assert not any(r['review_status']=='reviewed' for r in refs)
  op.update(text_sha256=hashlib.sha256(row['text'].encode()).hexdigest(),affected_references=refs)
 ops.append(op)
dates={
 '0438-b004':'2007-06-06 16:52:09','0438-b005':'2007-06-06 16:52:09',
 '0438-b006':'2007-06-07 15:04:21','0439-b000':'2007-06-07 15:04:21','0439-b001':'2007-06-07 15:04:21',
 '0439-b002':'2007-06-08 15:13:42',
 **{x:'2007-06-13 15:49:07' for x in ['0441-b003','0441-b004','0442-b000','0442-b001','0442-b002']}}
for row in db.execute("select * from passages where unit_id='lesson-058' order by pdf_page,block_index,id").fetchall():
 short=row['id'].split('-p')[1];t=row['published_at'];after={};reason=''
 if short in dates:
  after=dict(published_at=dates[short]);reason='原页438/439及441/442连续解盘：独立时间头管后文，尾部新日期不管前文；6/6、6/7、6/8、6/13分别存，原文及跨页坐标不动。'
  if row['role']=='reader':
   after.update(role='author_commentary',speaker='缠中说禅');reason+='PDF作者解盘连续语气/原署名、非读者问答；此处无读者署名，5段误reader修正。'
 elif t and re.fullmatch(r'2007-\d{2}-\d{2}\d{2}:\d{2}:\d{2}',t):
  after=dict(published_at=t[:10]+' '+t[10:]);reason='实际核作者署名与问答承接，只补日期时刻空格，不改原日时或原字。'
 if after:propose('passages',row['id'],after,reason)
notes={
 '0437-fig1':('unverified','上证1分原样图到6/4收盘3659.32，含14-15内箭头与15/16，MACD24/52/9；可在6/4夜正文前取得但原作者/原发未核，保58缺口例外和前67非严格线段语境。'),
 '0438-fig1':('unverified','重绘图完整到6/5收盘，按1分线段编号但图框标5分钟，图周期不能等同走势级别；17低3404.25而正文3404分别保，MACD12/26/9与437原图24/52/9不混，原发未核。'),
 '0439-fig1':('later_annotation','头选6/6但全图到6/8收盘，合并6/6、6/7、6/8三日评论；对前两日含未来K，不能用后走势证明当时3858/4015判断。3858.19与4016.30图线不改正文3858/4015，底框5分钟及12/26/9不当走势级别定义。'),
 '0441-fig1':('later_annotation','头选6/13并全图至6/13收盘，合并6/12与6/13评论；晚于6/12，不证前日轮动或政策预测。正文4015、4144、深圳13700和图4016.30各自保，编号32至53及图5分钟不是直接走势级别。')}
for short,(status,note) in notes.items():propose('figures',DOC+'-p'+short,dict(origin_status=status,note=note),'主代理实际核PDF436至443八整页和4整图：2当时可得原发未核，2多日合并后加；原参数/正文图值及图周期分开。')
plan=dict(stage='C/E-source-provenance',plan_format=1,schema_version=meta['schema_version'],base_graph_version=meta['graph_version'],documents=[dict(r) for r in db.execute('select * from documents order by id')],new_units=[],operations=ops,visual_pages=list(range(436,444)),pending=['58缺口例外和相邻同向不重合延伸不作为后62/67严格线段定义替代；14-15内箭头非独立段/全14-15为一段。','背驰段可能与次日成立、4015严区间和4000概略强语、7的5分好转与最近1分枢三卖分别保条件；图参数/周期/小数差不静修。'],reviewer='Codex 主代理 / 58课八页四图与四轮语义/来源/时序复核，知识库范围')
Path(__file__).with_name('stage-c-l058-source-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(dict(operations=len(ops),passages=sum(x['table']=='passages' for x in ops),figures=4,base=meta['graph_version']),ensure_ascii=False))
