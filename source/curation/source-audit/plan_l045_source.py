"""Plan lesson45 date grouping and figure provenance; source bytes untouched."""
import hashlib,json,re,sqlite3,sys
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';DOC='volume_1-a53e99c37ca5'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
meta={r['key']:json.loads(r['value']) for r in db.execute('select * from metadata')};assert meta['graph_version']=='0.1.0-review-1cb86d91f463'
ops=[]
def propose(table,id,after,reason):
 row=dict(db.execute(f'select * from {table} where id=?',(id,)).fetchone());after={k:v for k,v in after.items() if row[k]!=v};assert after
 item=dict(table=table,id=id,before={k:row[k] for k in after},after=after,reason=reason)
 if table=='passages':
  refs=[dict(r) for r in db.execute('select e.id,e.claim_id,c.review_status from evidence e join claims c on c.id=e.claim_id where e.passage_id=?',(id,))];assert not any(r['review_status']=='reviewed' for r in refs);item.update(text_sha256=hashlib.sha256(row['text'].encode()).hexdigest(),affected_references=refs)
 ops.append(item)
group={'0326-b005','0326-b006','0326-b007','0327-b000','0327-b001','0327-b002'}
for row in db.execute("select * from passages where unit_id='lesson-045' order by pdf_page,block_index,id").fetchall():
 short=row['id'].split('-p')[1];t=row['published_at']
 if short in group:propose('passages',row['id'],dict(published_at='2007-04-17 15:38:56'),'326-b004尾4/17时间头支配后续六段，前段仍4/16；原始尾头/字符映射和身份不改。')
 elif t and re.fullmatch(r'2007-\d{2}-\d{2}\d{2}:\d{2}:\d{2}',t):propose('passages',row['id'],dict(published_at=t[:10]+' '+t[10:]),'作者署名时刻可核，规范日期与时刻缺空格，不改数值、原字、身份和几何。')
notes={
 '0327-fig1':('later_annotation','上证1分图头4/18，嵌4/17 15:38解盘和4/16读者/21:17答，右端为文后行情；1055/1346与1030/1340分属不同日期语境，图不统一升格信号或验真收益。'),
 '0329-fig1':('later_annotation','上证5分图选择4/16而右端至4/17，嵌读者三分钟买点字样及作者可以这样看；后K不证明当时已知后续，也不把读者模糊级别词静改作者严格定义。'),
 '0329-fig2':('later_annotation','600855五分图头选择4/16但主图右端至4/17并见14.50，嵌4/16 22:13答；不以后行情证明背驰精度或作者答应再买，分笔例739不是本图证券。'),
 '0330-fig1':('unverified','600855一分图为4/16同日可见行情，嵌当晚读者问和作者答，原发身份/制作者未核；1345作者反问未文字命名具体买点，不由标箭头补成作者明确分类。'),
}
for short,(status,note) in notes.items():propose('figures',DOC+'-p'+short,dict(origin_status=status,note=note),'逐一实际查看PDF320至331十二页与四完整图，核选择栏、右端行情、证券、周期和文字身份。')
passage_count=sum(x['table']=='passages' for x in ops);assert passage_count==45 and len(ops)==49
plan=dict(stage='C/E-source-provenance',plan_format=1,schema_version=meta['schema_version'],base_graph_version=meta['graph_version'],documents=[dict(r) for r in db.execute('select * from documents order by id')],new_units=[],operations=ops,visual_pages=list(range(320,332)),pending=['持股持币等待依相应级别和当下结构，5日线盘整用处不大；2225原字与20年剧本不一致，不静改。','图3后加1原发未核，三分钟买点为读者模糊词/作者有限认可；331媒体摘录保持读者转引，非作者解盘或当前新闻。'],reviewer='Codex 主代理 / 45课等待与结构、限定5日线及跨时段图源复核')
Path(__file__).with_name('stage-c-l045-source-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(dict(operations=len(ops),passages=passage_count,figures=4,base=meta['graph_version']),ensure_ascii=False))
