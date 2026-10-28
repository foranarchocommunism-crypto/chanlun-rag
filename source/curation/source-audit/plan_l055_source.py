"""Plan lesson55 timestamp spacing only; preserve all literal text and geometry."""
import hashlib,json,re,sqlite3,sys
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
meta={r['key']:json.loads(r['value']) for r in db.execute('select * from metadata')}
assert meta['graph_version']=='0.1.0-review-6c88a992da52'
ops=[]
for row in db.execute("select * from passages where unit_id='lesson-055' order by pdf_page,block_index,id"):
 t=row['published_at']
 if t and re.fullmatch(r'2007-\d{2}-\d{2}\d{2}:\d{2}:\d{2}',t):
  refs=[dict(r) for r in db.execute('select e.id,e.claim_id,c.review_status from evidence e join claims c on c.id=e.claim_id where e.passage_id=?',(row['id'],))]
  assert not any(r['review_status']=='reviewed' for r in refs)
  ops.append(dict(table='passages',id=row['id'],before=dict(published_at=t),after=dict(published_at=t[:10]+' '+t[10:]),reason='实际核对PDF412至422作者署名和跨页承接，只补日期时刻空格；5/28正文答复、5/29与5/30文章/解盘各自日期不串，原字/映射/坐标均不改。',text_sha256=hashlib.sha256(row['text'].encode()).hexdigest(),affected_references=refs))
notes={
 '0417-fig1':('later_annotation','上证30分图右端6/4且含5/30-6/4大跌，混引5/25、5/28、5/29收评，明显晚于文字；后K不能证平衡市/4323/4300分支预测，原制图者未核。'),
 '0420-fig1':('later_annotation','上证日线头选2007/5/30但右端已到7月，晚于5/30收评；标1992-05-26 1249上深1/2线，正文此前模型为1429点，分别保原不静改。该图不是1分09:47定位图，不能证明二卖实际成交/日线三买免跌停。'),
 '0421-fig1':('later_annotation','上证30分头2007/6/4且右端6/4，引用5/30收评关于5/8至5/21三十分中枢回拉；框从5/9显示不更改正文5/8起点，后K不证原日内买卖预测或已验证全部分段。'),
}
for short,(status,note) in notes.items():
 id='volume_1-a53e99c37ca5-p'+short;row=dict(db.execute('select * from figures where id=?',(id,)).fetchone());after={k:v for k,v in dict(origin_status=status,note=note).items() if row[k]!=v};assert after
 ops.append(dict(table='figures',id=id,before={k:row[k] for k in after},after=after,reason='主代理查看412至422十一整页与3幅整图，核右端6/4和7月而非只看头选日期；全为后加整理图，保1249/1429与5/8文字/5/9图框起点差，原字几何不动。'))
plan=dict(stage='C/E-source-provenance',plan_format=1,schema_version=meta['schema_version'],base_graph_version=meta['graph_version'],documents=[dict(r) for r in db.execute('select * from documents order by id')],new_units=[],operations=ops,visual_pages=list(range(412,423)),pending=['3图均后加，选中5/30日线实际含7月、两30分图含6/4；图1249/此前正文1429、图5/9/正文5/8分开，不用后K证明预测。','买卖非同构为名义现金/时间模型和修辞非生理学证明；完成次级/双分解比较、只在技术允许回补、提取本金非清仓、日线vs30分/5分级别边界保留。'],reviewer='Codex 主代理 / 55课买卖时序、股性/资金级别、完成次级、双分解力度与5/30执行边界及3后加图四轮复核')
Path(__file__).with_name('stage-c-l055-source-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(dict(operations=len(ops),passages=sum(x['table']=='passages' for x in ops),figures=3,base=meta['graph_version']),ensure_ascii=False))
