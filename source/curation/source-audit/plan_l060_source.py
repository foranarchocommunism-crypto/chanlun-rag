"""Plan lesson60 timestamp spacing and visually checked figure provenance."""
import hashlib,json,re,sqlite3,sys
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';DOC='volume_1-a53e99c37ca5'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
meta={r['key']:json.loads(r['value']) for r in db.execute('select * from metadata')};assert meta['graph_version']=='0.1.0-review-dd5aebdeacd1';ops=[]
def propose(table,id,after,reason):
 row=dict(db.execute(f'select * from {table} where id=?',(id,)).fetchone());after={k:v for k,v in after.items() if row[k]!=v};assert after
 op=dict(table=table,id=id,before={k:row[k] for k in after},after=after,reason=reason)
 if table=='passages':
  refs=[dict(r) for r in db.execute('select e.id,e.claim_id,c.review_status from evidence e join claims c on c.id=e.claim_id where e.passage_id=?',(id,))];assert not any(r['review_status']=='reviewed' for r in refs)
  op.update(text_sha256=hashlib.sha256(row['text'].encode()).hexdigest(),affected_references=refs)
 ops.append(op)
for row in db.execute("select * from passages where unit_id='lesson-060' order by pdf_page,block_index,id").fetchall():
 t=row['published_at']
 if t and re.fullmatch(r'2007-\d{2}-\d{2}\d{2}:\d{2}:\d{2}',t):propose('passages',row['id'],dict(published_at=t[:10]+' '+t[10:]),'核PDF456作者6/20 15:49:31署名至457跨页回答；只补日期时刻空格，不改原日时/角色/原字和坐标。')
notes={
 '0451-fig1':('unverified','B0-A1-B1-A2-B2同级图式，两支分别B2低于/不低于A1，右图只画高于而等号归属由文字给出；下方黄框复述课程，原制作来源未核，非独立实证。'),
 '0452-fig1':('unverified','1分原样图头选6/13而完整含6/18、42至61，6/19早正文前数据可得但原发未核；45/46绿红箭头、55假一买类比与57、59/60/61和MACD12/26/9；图低4067.85与后重绘4068.20不静合。'),
 '0454-fig1':('later_annotation','5分框重绘头6/21且右端含6/21急跌，叠6/19 15:48评论，含未来K；60起[4224,4254]、4224下三卖与4254上三买须结构条件，后价不证当日判断。'),
 '0456-fig1':('later_annotation','5分框重绘头6/21并含次日急跌，叠6/20 15:36评论与13:30示意；晚于当时评论，4192附近46/4224的61和走势级别不由图周期替代，后K不证预测/成交。')}
for short,(status,note) in notes.items():propose('figures',DOC+'-p'+short,dict(origin_status=status,note=note),'实际查看PDF451至457七整页与4整图，2原发未核2后加；原图/重绘价差、含未来K及图周期分别记录。')
plan=dict(stage='C/E-source-provenance',plan_format=1,schema_version=meta['schema_version'],base_graph_version=meta['graph_version'],documents=[dict(r) for r in db.execute('select * from documents order by id')],new_units=[],operations=ops,visual_pages=list(range(451,458)),pending=['58—61一分枢与收评从60起[4224,4254]段落描述分别保存；原55假一买为类比，不改盘背无所谓一买的严格限定。','突发消息影响0/二卖足够与快行情5分50%空间为作者条件例，不能作所有账户成交保证或取消原定级别的一般规则。'],reviewer='Codex 主代理 / 60课七页四图同模型四轮，知识库范围')
Path(__file__).with_name('stage-c-l060-source-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(dict(operations=len(ops),passages=sum(x['table']=='passages' for x in ops),figures=4,base=meta['graph_version']),ensure_ascii=False))
