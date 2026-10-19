"""Plan lesson48 metadata provenance without modifying text/geometry."""
import hashlib,json,re,sqlite3,sys
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';DOC='volume_1-a53e99c37ca5'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
meta={r['key']:json.loads(r['value']) for r in db.execute('select * from metadata')};assert meta['graph_version']=='0.1.0-review-a4f759f80fae'
ops=[]
def propose(table,id,after,reason):
 row=dict(db.execute(f'select * from {table} where id=?',(id,)).fetchone());after={k:v for k,v in after.items() if row[k]!=v};assert after
 item=dict(table=table,id=id,before={k:row[k] for k in after},after=after,reason=reason)
 if table=='passages':
  refs=[dict(r) for r in db.execute('select e.id,e.claim_id,c.review_status from evidence e join claims c on c.id=e.claim_id where e.passage_id=?',(id,))];assert not any(r['review_status']=='reviewed' for r in refs);item.update(text_sha256=hashlib.sha256(row['text'].encode()).hexdigest(),affected_references=refs)
 ops.append(item)
for row in db.execute("select * from passages where unit_id='lesson-048' order by pdf_page,block_index,id").fetchall():
 t=row['published_at'];after={};reason=[]
 if row['id'] in [DOC+'-p0349-b004']+[DOC+'-p0350-b00'+str(i) for i in range(3)]:
  assert t=='2007-04-24 15:23:54';after['published_at']='2007-04-25 15:25:17';reason.append('原PDF349正文独立4/25 15:25:17时间起至350末解盘承接，不能仍用4/24时间；只修元数据不改原字。')
 elif t and re.fullmatch(r'2007-\d{2}-\d{2}\d{2}:\d{2}:\d{2}',t):
  after['published_at']=t[:10]+' '+t[10:];reason.append('原页作者署名时间与承接段可核，仅规范日期时刻空格，不改数字、身份、坐标。')
 if after:propose('passages',row['id'],after,'；'.join(reason))
propose('figures',DOC+'-p0349-fig1',dict(origin_status='later_annotation',note='实际查看整图：上证5分钟右端4/25收盘、含4/25 15:25:17文字及4/24 13:35/4/25 10:30连线；相对4/24晨文及收评为后加整理图，相对4/25收评行情已可得但原发制作者未核。图标3688至3699与前文3692差异保留，不用后K认证4/24预测。'),'9页与整幅配图视觉复核，按每段来源时间区分后加图和当日可得图，不证原作者制图。')
passage_count=sum(x['table']=='passages' for x in ops)
plan=dict(stage='C/E-source-provenance',plan_format=1,schema_version=meta['schema_version'],base_graph_version=meta['graph_version'],documents=[dict(r) for r in db.execute('select * from documents order by id')],new_units=[],operations=ops,visual_pages=list(range(347,356)),pending=['3692与3699原文及图内异值保持，零成本绝对无风险为作者核算/策略强语不证经济风险全无。','4/25图对4/24为后加，对4/25原发未核；两中枢可完非必已完，读者三根5分收低和逃逸速度公式未被认可。'],reviewer='Codex 主代理 / 48课跨日解盘、零成本资金容量与三卖/小转大范围复核')
Path(__file__).with_name('stage-c-l048-source-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(dict(operations=len(ops),passages=passage_count,figures=1,base=meta['graph_version']),ensure_ascii=False))
