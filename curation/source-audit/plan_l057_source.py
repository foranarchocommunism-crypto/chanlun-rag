"""Plan lesson57 source identity, date and figure provenance corrections."""
import hashlib,json,re,sqlite3,sys
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';DOC='volume_1-a53e99c37ca5'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
meta={r['key']:json.loads(r['value']) for r in db.execute('select * from metadata')};assert meta['graph_version']=='0.1.0-review-f3668c6fc5ca'
ops=[]
def propose(table,id,after,reason):
 row=dict(db.execute(f'select * from {table} where id=?',(id,)).fetchone());after={k:v for k,v in after.items() if row[k]!=v};assert after
 op=dict(table=table,id=id,before={k:row[k] for k in after},after=after,reason=reason)
 if table=='passages':
  refs=[dict(r) for r in db.execute('select e.id,e.claim_id,c.review_status from evidence e join claims c on c.id=e.claim_id where e.passage_id=?',(id,))];assert not any(r['review_status']=='reviewed' for r in refs)
  op.update(text_sha256=hashlib.sha256(row['text'].encode()).hexdigest(),affected_references=refs)
 ops.append(op)
article=[f'0432-b{i:03d}' for i in range(7,11)]+[f'0433-b{i:03d}' for i in range(5)]+['0434-b000','0434-b001']
for row in db.execute("select * from passages where unit_id='lesson-057' order by pdf_page,block_index,id").fetchall():
 short=row['id'].split('-p')[1];t=row['published_at'];after={};reason=''
 if short in article:
  assert row['role']=='author_reply' and t=='2007-06-0116:16:24'
  after=dict(role='author_commentary',published_at='2007-06-04');reason='PDF432蓝色独立文章标题明确2007-06-04，直到434论语引文结束；非6/1相邻作者回复，无具体时分不补造。'
 elif short in ['0432-b001','0432-b002']:
  assert t=='2007-06-01 15:47:14';after=dict(published_at='2007-06-01 15:47:30');reason='PDF432前段结尾独立2007-06-01 15:47:30新时间头管辖其后两段，前段仍15:47:14；备注原文/身份边界保待核，不改字。'
 elif t and re.fullmatch(r'2007-\d{2}-\d{2}\d{2}:\d{2}:\d{2}',t):
  after=dict(published_at=t[:10]+' '+t[10:]);reason='核原作者署名与承接，只补日期时刻空格，不改变原日和原文几何。'
 if after:propose('passages',row['id'],after,reason)
notes={
 '0428-fig1':('unverified','上证原样1分图含5/30与5/31全日，0至10标记、01缺口/23和78弱段/89较明显，5/31 22:35正文前可得；原作者/原发未核，MACD12/26/9，视图线段不当后62/72严格特征序列定义。'),
 '0429-fig1':('unverified','上证1分重绘头选5/30，但完整图含5/31的6与7、3858.19低点，正文5/31夜前可得；原制图未核。45/56具精确次级和粗视角全以下可线段分开，MACD面积/时间换空间为本例。'),
 '0430-fig1':('unverified','上证1分重绘含5/31，示34-45-56另一中枢、23/67比较及7一买/9二买，5/31正文前可得；原发未核，另一中枢与旧4087-4122边界不可混，原if7一买的条件不删。'),
 '0431-fig1':('later_annotation','日线头选6/1但右端到7月，晚于6/1收评；图示33.3%3739.273/50%3440.034而正文3734/3434，分别保原不据图改数，图不能证当时反弹/支持预测。'),
 '0434-fig1':('later_annotation','上证30分头选6/4但右端至6/13附近，晚于6/4收评；后反弹不能证当时30分MACD拉0为最大压力或3540买入可成交，原制图未核。'),
}
for short,(status,note) in notes.items():propose('figures',DOC+'-p'+short,dict(origin_status=status,note=note),'主代理核427至436十整页与5幅整图/432完整页：3当时可得原发未核、2后加，后K不证前文预测；原旁注/正文差和混合备注不自动作者化。')
plan=dict(stage='C/E-source-provenance',plan_format=1,schema_version=meta['schema_version'],base_graph_version=meta['graph_version'],documents=[dict(r) for r in db.execute('select * from documents order by id')],new_units=[],operations=ops,visual_pages=list(range(427,437)),pending=['432-b001末备注来源未核，作者引文止备注前，整段仍混合来源；与43夹注同需后续范围拆分，不能当作者月线3K理论。','11段6/4独立文章改author_commentary/日期仅日，2段按15:47:30；3734/3434与图3739/3440、原5月均线参数及反弹/补仓强语仍待核。'],reviewer='Codex 主代理 / 57课统一视角和精确次级、另一分解、仓位T+1、6/4文章身份/混合备注与五图四轮复核')
Path(__file__).with_name('stage-c-l057-source-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(dict(operations=len(ops),passages=sum(x['table']=='passages' for x in ops),article_passages=11,new_time_passages=2,figures=5,base=meta['graph_version']),ensure_ascii=False))
