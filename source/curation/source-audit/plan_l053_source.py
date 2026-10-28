"""Plan lesson53 timestamp spacing only; preserve all literal text and geometry."""
import hashlib,json,re,sqlite3,sys
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
meta={r['key']:json.loads(r['value']) for r in db.execute('select * from metadata')}
assert meta['graph_version']=='0.1.0-review-58e2535c21e3'
ops=[]
for row in db.execute("select * from passages where unit_id='lesson-053' order by pdf_page,block_index,id"):
 t=row['published_at']
 if t and re.fullmatch(r'2007-\d{2}-\d{2}\d{2}:\d{2}:\d{2}',t):
  refs=[dict(r) for r in db.execute('select e.id,e.claim_id,c.review_status from evidence e join claims c on c.id=e.claim_id where e.passage_id=?',(row['id'],))]
  assert not any(r['review_status']=='reviewed' for r in refs)
  ops.append(dict(table='passages',id=row['id'],before=dict(published_at=t),after=dict(published_at=t[:10]+' '+t[10:]),reason='实际核对PDF396至400作者署名及跨页承接，只补日期时刻空格；并触及/并一定要的原字、原文及几何映射均不改。',text_sha256=hashlib.sha256(row['text'].encode()).hexdigest(),affected_references=refs))
plan=dict(stage='C/E-source-provenance',plan_format=1,schema_version=meta['schema_version'],base_graph_version=meta['graph_version'],documents=[dict(r) for r in db.execute('select * from documents order by id')],new_units=[],operations=ops,visual_pages=list(range(396,401)),pending=['PDF397并触及与同段没有该级别第一类的字面张力、398并一定要原字均保留，不暗补未/不。','第二类形成更大级别中枢的相对级别与确认范围、复权跨课范围和100%获利/不用亏钱作者强语待核。'],reviewer='Codex 主代理 / 53课固定级别、三类点用途、原字歧义和交易条件四轮复核')
Path(__file__).with_name('stage-c-l053-source-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(dict(operations=len(ops),passages=len(ops),figures=0,base=meta['graph_version']),ensure_ascii=False))
