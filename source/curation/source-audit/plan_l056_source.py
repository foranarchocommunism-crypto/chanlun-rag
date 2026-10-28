"""Plan lesson56 timestamp spacing only; preserve all literal text and geometry."""
import hashlib,json,re,sqlite3,sys
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
meta={r['key']:json.loads(r['value']) for r in db.execute('select * from metadata')}
assert meta['graph_version']=='0.1.0-review-1faa97315b10'
ops=[]
for row in db.execute("select * from passages where unit_id='lesson-056' order by pdf_page,block_index,id"):
 t=row['published_at']
 if t and re.fullmatch(r'2007-\d{2}-\d{2}\d{2}:\d{2}:\d{2}',t):
  refs=[dict(r) for r in db.execute('select e.id,e.claim_id,c.review_status from evidence e join claims c on c.id=e.claim_id where e.passage_id=?',(row['id'],))]
  assert not any(r['review_status']=='reviewed' for r in refs)
  ops.append(dict(table='passages',id=row['id'],before=dict(published_at=t),after=dict(published_at=t[:10]+' '+t[10:]),reason='实际核对PDF422至427作者署名/跨页承接，仅补答复日期时刻空格；标题5/30与正文昨天这530张力保留，不改成5/31，原字T+0/不大过/几何映射均不改。',text_sha256=hashlib.sha256(row['text'].encode()).hexdigest(),affected_references=refs))
notes={
 '0423-fig1':('unverified','上证1分原样截图右侧记2007/5/30，完整当日行情在5/30 22:49标题前可得；原作者/原发未核。MACD标(24,52,9)，绿箭头划1分以下、红箭头比柱，不能把截图参数静换成重绘图(12,26,9)或伪造柱面积数值。'),
 '0424-fig1':('later_annotation','上证1分重绘图头5/31、含5/31早段三卖，晚于正文5/30 22:49；MJ_MACD(12,26,9)与423原图(24,52,9)不同，ABC框/旁注供定位，不能证同参数原始面积或当时预测。'),
 '0425-fig1':('unverified','上证1分至5/31收盘，10:02及4015-4122高一级框在当日15:43收评前可得；原制图/原发未核。图边4087.40/4122.41等精值不静改正文整数4087/4122，C为新枢首段按作者答限定。'),
 '0425-fig2':('later_annotation','日线右端横轴已到2007/9附近，软件头选却为2011/08/18，明显是后加再加工而非5/31当时原图；图标1992-05-26 1249上深1/2线，原模型1429保独立，不据后行情证明作者1/2线预测。'),
}
for short,(status,note) in notes.items():
 id='volume_1-a53e99c37ca5-p'+short;row=dict(db.execute('select * from figures where id=?',(id,)).fetchone());after={k:v for k,v in dict(origin_status=status,note=note).items() if row[k]!=v};assert after
 ops.append(dict(table='figures',id=id,before={k:row[k] for k in after},after=after,reason='主代理查看422至427六整页与4幅整图，核1分原样图参数/重绘晚于正文、5/31收评图当时可得和日线头2011/08/18/轴2007/9；2未核2后加，原T+0/不大过/昨天与标题日期不改。'))
plan=dict(stage='C/E-source-provenance',plan_format=1,schema_version=meta['schema_version'],base_graph_version=meta['graph_version'],documents=[dict(r) for r in db.execute('select * from documents order by id')],new_units=[],operations=ops,visual_pages=list(range(422,428)),pending=['标题5/30 22:49与正文昨天这530、55 09:47/56 9点48、回补段T+0、不大过等原字保留，不静修或补规则。','4图2未核2后加，MACD(24,52,9)/(12,26,9)参数不合并；A/B/C完成与小转大、C为新中枢首段及4015-4122/读者4027-4077分解范围分别保留。'],reviewer='Codex 主代理 / 56课突发二三卖、最低观察级/完成段、MACD对比与大小转折和四图原字四轮复核')
Path(__file__).with_name('stage-c-l056-source-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(dict(operations=len(ops),passages=sum(x['table']=='passages' for x in ops),figures=4,base=meta['graph_version']),ensure_ascii=False))
