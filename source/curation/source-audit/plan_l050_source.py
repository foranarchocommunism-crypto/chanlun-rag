"""Plan lesson50 metadata provenance without modifying text/geometry."""
import hashlib,json,re,sqlite3,sys
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';DOC='volume_1-a53e99c37ca5'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
meta={r['key']:json.loads(r['value']) for r in db.execute('select * from metadata')};assert meta['graph_version']=='0.1.0-review-7fa30c4809d4'
ops=[]
def propose(table,id,after,reason):
 row=dict(db.execute(f'select * from {table} where id=?',(id,)).fetchone());after={k:v for k,v in after.items() if row[k]!=v};assert after
 item=dict(table=table,id=id,before={k:row[k] for k in after},after=after,reason=reason)
 if table=='passages':
  refs=[dict(r) for r in db.execute('select e.id,e.claim_id,c.review_status from evidence e join claims c on c.id=e.claim_id where e.passage_id=?',(id,))];assert not any(r['review_status']=='reviewed' for r in refs);item.update(text_sha256=hashlib.sha256(row['text'].encode()).hexdigest(),affected_references=refs)
 ops.append(item)
for row in db.execute("select * from passages where unit_id='lesson-050' order by pdf_page,block_index,id").fetchall():
 t=row['published_at']
 if t and re.fullmatch(r'2007-\d{2}-\d{2}\d{2}:\d{2}:\d{2}',t):propose('passages',row['id'],dict(published_at=t[:10]+' '+t[10:]),'原页5/8作者署名和后承接段核，仅补日期时刻空格，不改数字、原字、身份或坐标。')
notes={
 '0364-fig1':('later_annotation','上证5分图头和右端到4/30行情，嵌4/27 15:14:36解盘，晚于4/27文字；3745.40/3720.80/3761.99图标不静改原3745/3720/3761，不用后K认证三买未成或预测。'),
 '0367-fig1':('later_annotation','上证5分图头5/9且右端有5/9行情，嵌5/8 15:28:53收评；晚于该评，不能用后K证明放量强平衡市缺口判断或提前买卖能力，原发制图者未核。'),
}
for short,(status,note) in notes.items():propose('figures',DOC+'-p'+short,dict(origin_status=status,note=note),'实际查看PDF362至371十页与两整图，按图头/右端未来K与所嵌解盘文字时间区分，文字独立支持命题。')
passage_count=sum(x['table']=='passages' for x in ops)
plan=dict(stage='C/E-source-provenance',plan_format=1,schema_version=meta['schema_version'],base_graph_version=meta['graph_version'],documents=[dict(r) for r in db.execute('select * from documents order by id')],new_units=[],operations=ops,visual_pages=list(range(362,372)),pending=['5日线三天拉不回为通常不精确法，未逐项判最低/最高/收盘；理论前提改变可不完全回拉，未变则作者断言一定回拉。','两图后加且原发未核，CCTV九段1分为读者解释，不能升作作者背书；两篇央行/空头政治经济文章保上下文不作缠论技术定理。'],reviewer='Codex 主代理 / 50课MACD顺序、理论前提、均线确认和新中枢识别边界复核')
Path(__file__).with_name('stage-c-l050-source-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(dict(operations=len(ops),passages=passage_count,figures=2,base=meta['graph_version']),ensure_ascii=False))
