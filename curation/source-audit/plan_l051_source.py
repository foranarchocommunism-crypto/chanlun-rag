"""Plan lesson51 metadata provenance without modifying text/geometry."""
import hashlib,json,re,sqlite3,sys
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';DOC='volume_1-a53e99c37ca5'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
meta={r['key']:json.loads(r['value']) for r in db.execute('select * from metadata')};assert meta['graph_version']=='0.1.0-review-8edb32d94216'
ops=[]
def propose(table,id,after,reason):
 row=dict(db.execute(f'select * from {table} where id=?',(id,)).fetchone());after={k:v for k,v in after.items() if row[k]!=v};assert after
 item=dict(table=table,id=id,before={k:row[k] for k in after},after=after,reason=reason)
 if table=='passages':
  refs=[dict(r) for r in db.execute('select e.id,e.claim_id,c.review_status from evidence e join claims c on c.id=e.claim_id where e.passage_id=?',(id,))];assert not any(r['review_status']=='reviewed' for r in refs);item.update(text_sha256=hashlib.sha256(row['text'].encode()).hexdigest(),affected_references=refs)
 ops.append(item)
for row in db.execute("select * from passages where unit_id='lesson-051' order by pdf_page,block_index,id").fetchall():
 t=row['published_at'];after={};reason=[]
 if row['id'] in [DOC+'-p0373-b004']+[DOC+'-p0374-b00'+str(i) for i in range(3)]:
  assert t=='2007-05-09 15:25:06';after['published_at']='2007-05-10 15:36:28';reason.append('原PDF373独立5/10 15:36:28时间起的解盘续至374前三段，不继续归5/9；只改时间元数据。')
 elif t and re.fullmatch(r'2007-\d{2}-\d{2}\d{2}:\d{2}:\d{2}',t):after['published_at']=t[:10]+' '+t[10:];reason.append('作者署名与承接段核，仅补日期时刻空格，不改数字、原字、身份或坐标。')
 if after:propose('passages',row['id'],after,'；'.join(reason))
notes={
 '0373-fig1':('later_annotation','上证5分图头和右端5/11，混引5/9 15:25:06与5/10 15:36:28收评；晚于两段文字，不以未来K证4000三买或震荡预测，图中文字来源按各自日期分开。'),
 '0376-fig1':('later_annotation','上证月线选框为2007/05/31已晚于5/10正文，右端更有后续月K与6124标；首峰图标1249与正文1429不一致，原字分别留，不以此后图证明线性压力线、360度比例或提前预测。'),
 '0380-fig1':('later_annotation','上证5分混引5/14、5/15、5/16解盘，头选5/16但右端已有5/17K；相对三段均为后加，4040/10:46与5/16 10:17是各日案例不混时点，原发制作者未核。'),
 '0381-fig1':('later_annotation','东方明珠600832 5分图右端有5/18行情，嵌5/17新浪网友向CCTV提问及CCTV回答；均是读者非作者答复，即使画线不能证明作者认可1分背驰，不关联为新作者命题。'),
}
for short,(status,note) in notes.items():propose('figures',DOC+'-p'+short,dict(origin_status=status,note=note),'实际查看371至382十二页及四整图，对图头/右端未来K、原文日期、1249/1429异字和读者身份逐项核对。')
passage_count=sum(x['table']=='passages' for x in ops)
plan=dict(stage='C/E-source-provenance',plan_format=1,schema_version=meta['schema_version'],base_graph_version=meta['graph_version'],documents=[dict(r) for r in db.execute('select * from documents order by id')],new_units=[],operations=ops,visual_pages=list(range(371,383)),pending=['压力线360比例是作者历史模型未外部验证，原1429和后图1249分别留；三个月/7月与三条分支不是实证预测。','四图后加，600832图为CCTV读者分析不可当作者背书；B和回试类型完成条件不只MACD。'],reviewer='Codex 主代理 / 51课荐股假设模型、压力线历史口径、三买完成与跨日/读者图源复核')
Path(__file__).with_name('stage-c-l051-source-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(dict(operations=len(ops),passages=passage_count,figures=4,base=meta['graph_version']),ensure_ascii=False))
