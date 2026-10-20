"""Plan lesson59 date and figure provenance corrections; preserve raw text."""
import hashlib,json,sqlite3,sys
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';DOC='volume_1-a53e99c37ca5'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
meta={r['key']:json.loads(r['value']) for r in db.execute('select * from metadata')};assert meta['graph_version']=='0.1.0-review-60afc026a0f3';ops=[]
def propose(table,id,after,reason):
 row=dict(db.execute(f'select * from {table} where id=?',(id,)).fetchone());after={k:v for k,v in after.items() if row[k]!=v};assert after
 op=dict(table=table,id=id,before={k:row[k] for k in after},after=after,reason=reason)
 if table=='passages':
  refs=[dict(r) for r in db.execute('select e.id,e.claim_id,c.review_status from evidence e join claims c on c.id=e.claim_id where e.passage_id=?',(id,))];assert not any(r['review_status']=='reviewed' for r in refs)
  op.update(text_sha256=hashlib.sha256(row['text'].encode()).hexdigest(),affected_references=refs)
 ops.append(op)
for short in ['0447-b005','0447-b006','0448-b000','0448-b001','0448-b002']:
 propose('passages',DOC+'-p'+short,dict(published_at='2007-06-15 15:30:42'),'PDF447独立2007-06-15 15:30:42时间头管之后跨页解盘到448周末结束；非6/14旧解盘日期，原字/角色/几何不动。')
notes={
 '0444-fig1':('unverified','第一张1分原图从6/4到6/8，18至33编号、19低3404.25，与58图17低点编号不同，不自动跨图同号等同；20—23枢与29三买，MACD12/26/9；6/14早正文前市场数据可得，原发未核。'),
 '0444-fig2':('unverified','第二张1分原图从6/7到6/12，28至41编号、33对28—31/37对32—35枢三买；接前图有交叠，非原编号全部首尾无重复；MACD12/26/9，6/14正文前可得原发未核。'),
 '0445-fig1':('unverified','第三张1分原图从6/12到6/13，41至45及未编号后续，红箭头高于绿箭头对应末段尚不能确认结束；最近42—45一分枢，MACD12/26/9；6/14早前数据可得但原发未核。'),
 '0445-fig2':('later_annotation','额外5分重绘图头选6/4但轴和K线到6/15，晚于6/14 08:23正文，粉线概括幅度不是完成中枢证明；原MACD标签26/12/9顺序原样保，不静改12/26/9。'),
 '0446-fig1':('unverified','重绘局部图头选6/12而完整至6/13、编号19至46，标22—31另一5分枢和41条件三买；注引6/14正文，制图原发未核，市场数据早于6/14早；图框5分钟非直接走势级别。'),
 '0447-fig1':('later_annotation','合并6/14和6/15解盘，头选6/14但完整到6/15收盘/57段，对6/14作者评论含未来K；图9段延伸5分为本例，不变所有中枢定义；原发未核。'),
 '0450-fig1':('later_annotation','头选6/18但右端已有6/19和65点，晚于6/18 15:16评论；4224有效跌破且一分三卖为联合条件，图后跌不证当时必然；原发未核。')}
for short,(status,note) in notes.items():propose('figures',DOC+'-p'+short,dict(origin_status=status,note=note),'主代理实际查看PDF443至450八页和7幅整图、446完整页：4原发未核3后加，局部编号/精度/参数与前瞻时间不混。')
plan=dict(stage='C/E-source-provenance',plan_format=1,schema_version=meta['schema_version'],base_graph_version=meta['graph_version'],documents=[dict(r) for r in db.execute('select * from documents order by id')],new_units=[],operations=ops,visual_pages=list(range(443,451)),pending=['正文3994.57/3994.21和7—8—9局部例必须保原精度语境，不自动与57点7=3858同点；58图17与59图19低3404编号变化未核因。','早期背驰/盘背确认线段与后64/67特征序列分层；不成趋势/未完成、另一分解、强弱扩张边界和停止回补条件均保。'],reviewer='Codex 主代理 / 59课八页七图与四轮来源/语义/精度及条件复核，知识库范围')
Path(__file__).with_name('stage-c-l059-source-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(dict(operations=len(ops),passages=5,figures=7,base=meta['graph_version']),ensure_ascii=False))
