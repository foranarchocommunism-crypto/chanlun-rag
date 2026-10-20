"""Plan lesson54 timestamp spacing only; preserve all literal text and geometry."""
import hashlib,json,re,sqlite3,sys
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
meta={r['key']:json.loads(r['value']) for r in db.execute('select * from metadata')}
assert meta['graph_version']=='0.1.0-review-0a42d381d402'
ops=[]
for row in db.execute("select * from passages where unit_id='lesson-054' order by pdf_page,block_index,id"):
 t=row['published_at']
 if t and re.fullmatch(r'2007-\d{2}-\d{2}\d{2}:\d{2}:\d{2}',t):
  refs=[dict(r) for r in db.execute('select e.id,e.claim_id,c.review_status from evidence e join claims c on c.id=e.claim_id where e.passage_id=?',(row['id'],))]
  assert not any(r['review_status']=='reviewed' for r in refs)
  ops.append(dict(table='passages',id=row['id'],before=dict(published_at=t),after=dict(published_at=t[:10]+' '+t[10:]),reason='实际核对PDF400至411作者署名/跨页承接，只补日期时刻空格，保5/24正文答复与5/25两段文章/解盘各自日期；原公式/字/几何均不改。',text_sha256=hashlib.sha256(row['text'].encode()).hexdigest(),affected_references=refs))
notes={
 '0401-fig1':('unverified','航天机电1分5/18图，g0图示18.59而正文设18.5，原制图/原发未核；作者文字与黄框重引独立，保d1=g2/d2=g4及g3首分解三卖，不以图反改原价。'),
 '0402-fig1':('unverified','同一航天机电5/18图的结合律/MACD注释版本，原制图未核；g0g3原式右端止g2d3有端点张力，不按黄框静补d3g3。'),
 '0403-fig1':('unverified','同一航天机电5/18图两分解与反弹说明版；两中枢无连接的禁式与三个次级合高一级不同，制图/原发未核，不以旁注变作者新增引文。'),
 '0404-fig1':('unverified','航天机电首分解到g5确定5分[d2,g5]示意，d7g7含2/3回试与5/6小十字，属本图形识别不是任意K数等递归中枢；原制图未核。'),
 '0405-fig1':('unverified','航天机电第二分解到g6确定5分[d3,g5]，g7非该分解三卖但MACD两返0不过/后红柱小互证；不把两分解区间/形成时刻/标签硬合，原制图未核。'),
 '0406-fig1':('unverified','上证1分到2007/5/24收盘，10:00/11:15/14:12与当日15:34答前可得；原制图/原发未核，不以5/24已知后市证当时每个点可实际成交。'),
 '0408-fig1':('later_annotation','上证5分图含5/25右端行情，插入1分5/24视图，晚于5/24 15:50问答；混大小级视角及后K仅供整理查证，不能作为作者当时预测证明。'),
}
for short,(status,note) in notes.items():
 id='volume_1-a53e99c37ca5-p'+short;row=dict(db.execute('select * from figures where id=?',(id,)).fetchone());after={k:v for k,v in dict(origin_status=status,note=note).items() if row[k]!=v};assert after
 ops.append(dict(table='figures',id=id,before={k:row[k] for k in after},after=after,reason='主代理查看12整页与7幅整图，核5/18案例/5/24收评图和5/25后加图；保双分解不同区间、公式端点、正文设价与图值差，原发均未核。'))
plan=dict(stage='C/E-source-provenance',plan_format=1,schema_version=meta['schema_version'],base_graph_version=meta['graph_version'],documents=[dict(r) for r in db.execute('select * from documents order by id')],new_units=[],operations=ops,visual_pages=list(range(400,412)),pending=['7图6原发未核/1后加，不凭图改正文18.5或原g0g3等式，双分解g5/g6和[d2,g5]/[d3,g5]保持独立。','54连接同级中枢必须次级/同向与18可更低范围未统一；三卖后必下/极端幅度与理论前提、二买低一买/二卖高一卖少见许可、第二问没有什么更大级别短答均保上下文。'],reviewer='Codex 主代理 / 54课双分解、连接方向、三类点与次级完整类型、原式/短答指代和7图四轮复核')
Path(__file__).with_name('stage-c-l054-source-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(dict(operations=len(ops),passages=sum(x['table']=='passages' for x in ops),figures=7,base=meta['graph_version']),ensure_ascii=False))
