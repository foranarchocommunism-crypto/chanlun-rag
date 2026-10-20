"""Plan lesson52 metadata provenance without modifying text/geometry."""
import hashlib,json,re,sqlite3,sys
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';DOC='volume_1-a53e99c37ca5'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
meta={r['key']:json.loads(r['value']) for r in db.execute('select * from metadata')};assert meta['graph_version']=='0.1.0-review-af327b82af12'
ops=[]
def propose(table,id,after,reason):
 row=dict(db.execute(f'select * from {table} where id=?',(id,)).fetchone());after={k:v for k,v in after.items() if row[k]!=v};assert after
 item=dict(table=table,id=id,before={k:row[k] for k in after},after=after,reason=reason)
 if table=='passages':
  refs=[dict(r) for r in db.execute('select e.id,e.claim_id,c.review_status from evidence e join claims c on c.id=e.claim_id where e.passage_id=?',(id,))];assert not any(r['review_status']=='reviewed' for r in refs);item.update(text_sha256=hashlib.sha256(row['text'].encode()).hexdigest(),affected_references=refs)
 ops.append(item)
for row in db.execute("select * from passages where unit_id='lesson-052' order by pdf_page,block_index,id").fetchall():
 t=row['published_at'];after={};reason=[]
 if row['id'] in [DOC+'-p0390-b00'+str(i) for i in [2,3,4]]:
  assert t=='2007-05-21 15:42:35';after['published_at']='2007-05-22 15:28:48';reason.append('原PDF390独立5/22 15:28:48时间头起至解盘结束，不继续归5/21；前段末头不改变前文日期。')
 elif t and re.fullmatch(r'2007-\d{2}-\d{2}\d{2}:\d{2}:\d{2}',t):after['published_at']=t[:10]+' '+t[10:];reason.append('作者署名与承接段核，仅补日期时刻空格，不改原字/身份/坐标。')
 if after:propose('passages',row['id'],after,'；'.join(reason))
notes={
 '0384-fig1':('unverified','上证1分图含5/18收盘与两段05171430-05181000、05181058-05181326和1分MACD，可在5/18 15:38收评前得到，但原作者/制图者和原发未核。'),
 '0386-fig1':('later_annotation','600279 30分图右端5/22，嵌5/20弥向CCTV问答，晚于读者文字；18.1/15.53判点均读者解释，不作作者知识证据。'),
 '0387-fig1':('later_annotation','000802 60分图头5/21，晚于所嵌5/20新浪网友/CCTV问答；不是作者答复，不因图示19.51/盘背就认证作者认可。'),
 '0389-fig1':('later_annotation','上证30分图混引5/21和5/22收评，头选5/25但右端含5/29及其后K，明确晚于两段；未来跌K不证明原1/2线三分支预测。'),
 '0389-fig2':('later_annotation','上证5分头选5/22但右端5/23行情，混引5/21与5/22收评；晚于文字，图周期/图内框不直接证明所有严格递归中枢。'),
 '0391-fig1':('later_annotation','上证5分头选5/21但右端到5/22，嵌5/21问答与10:40二买；后K不证当时可成交或把观察周期等信号级别。'),
 '0391-fig2':('unverified','上证1分图到5/21收盘、标10:40，所引5/21 16:08答前可得；原发/制图者未核，不补新一般二买定义。'),
 '0392-fig1':('unverified','600569 30分图头选4/24、右端仅至5/11，5/22读者问答前行情可得；引用新浪网友和CCTV均为读者，原作者制图未核，不关联作者命题。'),
 '0394-fig1':('unverified','600216 30分右端5/22，与5/22 16:30否认05181000的作者答复当日可得；原发未核，30F三买箭头不能覆盖作者要求5分拆离开/回试。'),
 '0395-fig1':('unverified','600216 5分图至5/21，嵌5/22读者05161020-05171010离开/05171010-05171455回试问和作者对；作者仅对该问明确认可，不将读者文字改作作者原话，图原发未核。'),
}
for short,(status,note) in notes.items():propose('figures',DOC+'-p'+short,dict(origin_status=status,note=note),'实际查看382至396十五页与10整图，逐图核右端/文字时间、5后加5未核和3幅CCTV读者图，作者对的指代对象及原文不小于保留。')
passage_count=sum(x['table']=='passages' for x in ops)
plan=dict(stage='C/E-source-provenance',plan_format=1,schema_version=meta['schema_version'],base_graph_version=meta['graph_version'],documents=[dict(r) for r in db.execute('select * from documents order by id')],new_units=[],operations=ops,visual_pages=list(range(382,397)),pending=['原背驰级别一定不小于转折级别不静改，和前课小转大/本段30例关系待核；哲学/量子和科学比喻不作物理证明。','5/22三段日期、10图5后加5原发未核，600279/802/569三图均CCTV读者；600216对只认可紧前一问，不把读者时刻引文变作者原话。'],reviewer='Codex 主代理 / 52课观察参与/固定级别、不小于原字、三买回试与短答指代、图源和执行约束复核')
Path(__file__).with_name('stage-c-l052-source-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(dict(operations=len(ops),passages=passage_count,figures=10,base=meta['graph_version']),ensure_ascii=False))
