"""Plan lesson47 metadata provenance without modifying text/geometry."""
import hashlib,json,re,sqlite3,sys
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';DOC='volume_1-a53e99c37ca5'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
meta={r['key']:json.loads(r['value']) for r in db.execute('select * from metadata')};assert meta['graph_version']=='0.1.0-review-e7c4870b7d7e'
ops=[]
def propose(table,id,after,reason):
 row=dict(db.execute(f'select * from {table} where id=?',(id,)).fetchone());after={k:v for k,v in after.items() if row[k]!=v};assert after
 item=dict(table=table,id=id,before={k:row[k] for k in after},after=after,reason=reason)
 if table=='passages':
  refs=[dict(r) for r in db.execute('select e.id,e.claim_id,c.review_status from evidence e join claims c on c.id=e.claim_id where e.passage_id=?',(id,))];assert not any(r['review_status']=='reviewed' for r in refs);item.update(text_sha256=hashlib.sha256(row['text'].encode()).hexdigest(),affected_references=refs)
 ops.append(item)
for row in db.execute("select * from passages where unit_id='lesson-047' order by pdf_page,block_index,id").fetchall():
 t=row['published_at']
 if t and re.fullmatch(r'2007-\d{2}-\d{2}\d{2}:\d{2}:\d{2}',t):propose('passages',row['id'],dict(published_at=t[:10]+' '+t[10:]),'原页作者署名时间与承接段可核，仅规范日期/时刻空格，不改数字原文身份坐标。')
notes={
 '0340-fig1':('unverified','4/19上证分时行情及辅助指标屏幕，正文4/20 08:51时可得，但未核原作者/制图者；不同于三相邻30分K的递归定义，不补通用分笔买点算法。'),
 '0341-fig1':('unverified','深成5分与分时4/19收盘图，在次晨正文前可得；显示未回轴而不升为5分背驰，截图原发/作者未核。'),
 '0341-fig2':('later_annotation','深成5分选择栏4/19但主图右端有4/20行情，晚于4/20 08:51正文；注叙1330/绿面积说明，不用后K验证上午文字当时已知次日走势。'),
 '0342-fig1':('unverified','深成1分4/19图及14:43局部早晨之星放大，原发身份未核，正文次晨可得；注释100%须与当天平衡市/中枢位置时间条件联合，非所有分笔背驰都强回拉。'),
 '0342-fig2':('later_annotation','上证日线BOLL含4/19箭头而右端到7月刻度，明显为后图；3351/3358及配合支撑为原文历史案例，不能用未来K证明精准预测或全部因果。'),
 '0345-fig1':('later_annotation','上证5分右端到4/23收盘，混引4/20正文支撑和4/23解盘；相对4/20晨文属后加，4/23评论时同日行情可得但原发未核，不用后K认证缺口三日判据。'),
}
for short,(status,note) in notes.items():propose('figures',DOC+'-p'+short,dict(origin_status=status,note=note),'实际查看PDF339至347九页和6整图，核4/20晨文、后4/20/7月/4/23行情和来源未核同日截图。')
passage_count=sum(x['table']=='passages' for x in ops);assert passage_count==13 and len(ops)==19
plan=dict(stage='C/E-source-provenance',plan_format=1,schema_version=meta['schema_version'],base_graph_version=meta['graph_version'],documents=[dict(r) for r in db.execute('select * from documents order by id')],new_units=[],operations=ops,visual_pages=list(range(339,348)),pending=['3892/3688与后3688至3692原字不一致，未静改；三日缺口是统计非绝对，分时中枢借用非严格递归。','图3后加3原发未核；100%作者条件内理论措辞非经验胜率或成交保证，T+0解除隔日不能卖约束不表示所有风险消失。'],reviewer='Codex 主代理 / 47课晨文/后图、借用中枢与数值/强语范围复核')
Path(__file__).with_name('stage-c-l047-source-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(dict(operations=len(ops),passages=passage_count,figures=6,base=meta['graph_version']),ensure_ascii=False))
