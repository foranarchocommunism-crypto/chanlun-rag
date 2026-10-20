"""Plan lesson49 metadata provenance without modifying text/geometry."""
import hashlib,json,re,sqlite3,sys
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';DOC='volume_1-a53e99c37ca5'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
meta={r['key']:json.loads(r['value']) for r in db.execute('select * from metadata')};assert meta['graph_version']=='0.1.0-review-ebd7062c0ca7'
ops=[]
def propose(table,id,after,reason):
 row=dict(db.execute(f'select * from {table} where id=?',(id,)).fetchone());after={k:v for k,v in after.items() if row[k]!=v};assert after
 item=dict(table=table,id=id,before={k:row[k] for k in after},after=after,reason=reason)
 if table=='passages':
  refs=[dict(r) for r in db.execute('select e.id,e.claim_id,c.review_status from evidence e join claims c on c.id=e.claim_id where e.passage_id=?',(id,))];assert not any(r['review_status']=='reviewed' for r in refs);item.update(text_sha256=hashlib.sha256(row['text'].encode()).hexdigest(),affected_references=refs)
 ops.append(item)
for row in db.execute("select * from passages where unit_id='lesson-049' order by pdf_page,block_index,id").fetchall():
 t=row['published_at']
 if t and re.fullmatch(r'2007-\d{2}-\d{2}\d{2}:\d{2}:\d{2}',t):propose('passages',row['id'],dict(published_at=t[:10]+' '+t[10:]),'原PDF作者署名与后承接段核，仅补日期时刻空格，不改数字、原字、身份或坐标。')
notes={
 '0356-fig1':('unverified','三分支简图无可核作者署名/原发时间，按原文给中枢上下/内与三点状态，忽略诸多技能/特殊震荡限制；不是作者原图证明，不用图静改正文第二种第2类编号。'),
 '0359-fig1':('unverified','30F入市流程图含www.chzhshch.net水印，制作者/原发日期未核；不能以其单线分支代替正文例外或替作者改编号，图来源独立标明。'),
 '0359-fig2':('later_annotation','上证5分图头4/27、右端到4/27行情，并嵌4/26 15:21:18解盘，明确晚于4/26文字；不得用后K验证站稳3745的预测，3745.40图标与原3745分别留。'),
 '0360-fig1':('later_annotation','长安000625为15分图，虽头选4/26，右端有4/27K，嵌4/26 21:40:35回复；相对答复属后加整理，不能据后跌证明当时红柱/17.05归因；图内黄白柱/面子原字不静修。'),
}
for short,(status,note) in notes.items():propose('figures',DOC+'-p'+short,dict(origin_status=status,note=note),'实际查看PDF355至362八页及四整图，图表右端/水印与作者时点、几种简化流程范围分别核对。')
passage_count=sum(x['table']=='passages' for x in ops)
plan=dict(stage='C/E-source-provenance',plan_format=1,schema_version=meta['schema_version'],base_graph_version=meta['graph_version'],documents=[dict(r) for r in db.execute('select * from documents order by id')],new_units=[],operations=ops,visual_pages=list(range(355,363)),pending=['原对于第二种第2类承接买点的编号张力不静改；两最大定理未附证明、50%/200%/500%非项目评测。','图2流程原发未核/2后K；0931/0935原字并存，分笔柱长与后柱面积不同说法未静统一。'],reviewer='Codex 主代理 / 49课固定级别两模式、利润率口径/强语、来源与图文边界复核')
Path(__file__).with_name('stage-c-l049-source-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(dict(operations=len(ops),passages=passage_count,figures=4,base=meta['graph_version']),ensure_ascii=False))
