"""Plan lesson42 timestamp and figure provenance metadata only."""
import hashlib,json,re,sqlite3,sys
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';DOC='volume_1-a53e99c37ca5'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
meta={r['key']:json.loads(r['value']) for r in db.execute('select * from metadata')};assert meta['graph_version']=='0.1.0-review-ecd06e7bf4a5'
ops=[]
def propose(table,id,after,reason):
 row=dict(db.execute(f'select * from {table} where id=?',(id,)).fetchone());after={k:v for k,v in after.items() if row[k]!=v};assert after
 item=dict(table=table,id=id,before={k:row[k] for k in after},after=after,reason=reason)
 if table=='passages':
  refs=[dict(r) for r in db.execute('select e.id,e.claim_id,c.review_status from evidence e join claims c on c.id=e.claim_id where e.passage_id=?',(id,))];assert not any(r['review_status']=='reviewed' for r in refs);item.update(text_sha256=hashlib.sha256(row['text'].encode()).hexdigest(),affected_references=refs)
 ops.append(item)
group={'0308-b001','0308-b002','0309-b000','0309-b001','0309-b002','0309-b003'}
for row in db.execute("select * from passages where unit_id='lesson-042' order by pdf_page,block_index,id").fetchall():
 short=row['id'].split('-p')[1];t=row['published_at']
 if short in group:propose('passages',row['id'],dict(published_at='2007-04-05 15:34:37'),'PDF308独立4/5 15:34:37头支配随后跨页解盘；前段4/4不改，保留全部原始字符和身份。')
 elif t and re.fullmatch(r'2007-\d{2}-\d{2}\d{2}:\d{2}:\d{2}',t):propose('passages',row['id'],dict(published_at=t[:10]+' '+t[10:]),'作者署名时刻及承接段可核；仅日期与时刻缺空格规范化，数值和原文不改。')
notes={
 '0308-fig1':('later_annotation','上证15分图嵌4/4及4/5解盘，右端至4/10晚于正文；选择栏4/3不代表原文当时全可见，不以之后行情验证二线/指数万点预测。'),
 '0308-fig2':('later_annotation','深成60分图嵌4/4和4/5解盘，右端到4/9标记后、9662.09，晚于所答；画线和后K非作者原发证明，不据此认证压力突破或必到万点。'),
 '0310-fig1':('unverified','深成1分图同日4/4、11:04/13:51及MACD，原发制作者未核；作者只让对比两点差异，未在文字说哪一指标/公式，图表观察与作者明说分开。'),
 '0310-fig2':('later_annotation','600649周线图头4/13，箭头4/4周和两组答疑；右端晚于4/4答，历史密集区含大多数被套为作者解释非持有人账本证明。'),
}
for short,(status,note) in notes.items():propose('figures',DOC+'-p'+short,dict(origin_status=status,note=note),'逐一查看PDF306至311六页及四幅整图，核选择栏、图右端、周期和答疑时间。')
assert len(ops)==28 and sum(x['table']=='passages' for x in ops)==24
plan=dict(stage='C/E-source-provenance',plan_format=1,schema_version=meta['schema_version'],base_graph_version=meta['graph_version'],documents=[dict(r) for r in db.execute('select * from documents order by id')],new_units=[],operations=ops,visual_pages=list(range(306,312)),pending=['盘整背驰一定跌破的方向/级别/目标仍不全，a`+B按原式保留不补算法；行为类型是作者训练观点非心理诊断，图3后加1原发未核。'],reviewer='Codex 主代理 / 42课日期分组、行为观点与原图来源复核')
Path(__file__).with_name('stage-c-l042-source-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(dict(operations=len(ops),passages=24,figures=4,base=meta['graph_version']),ensure_ascii=False))
