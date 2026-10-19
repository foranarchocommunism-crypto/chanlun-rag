"""Plan lesson43 timestamps and figure-source metadata; retain all source text."""
import hashlib,json,re,sqlite3,sys
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';DOC='volume_1-a53e99c37ca5'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
meta={r['key']:json.loads(r['value']) for r in db.execute('select * from metadata')};assert meta['graph_version']=='0.1.0-review-25594b1ae8ac'
ops=[]
def propose(table,id,after,reason):
 row=dict(db.execute(f'select * from {table} where id=?',(id,)).fetchone());after={k:v for k,v in after.items() if row[k]!=v};assert after
 item=dict(table=table,id=id,before={k:row[k] for k in after},after=after,reason=reason)
 if table=='passages':
  refs=[dict(r) for r in db.execute('select e.id,e.claim_id,c.review_status from evidence e join claims c on c.id=e.claim_id where e.passage_id=?',(id,))];assert not any(r['review_status']=='reviewed' for r in refs);item.update(text_sha256=hashlib.sha256(row['text'].encode()).hexdigest(),affected_references=refs)
 ops.append(item)
group={'0314-b002','0314-b003','0314-b004','0314-b005'}
for row in db.execute("select * from passages where unit_id='lesson-043' order by pdf_page,block_index,id").fetchall():
 short=row['id'].split('-p')[1];t=row['published_at']
 if short in group:propose('passages',row['id'],dict(published_at='2007-04-09 15:33:39'),'PDF314独立4/9头支配后续解盘，之前4/6段不改；跨时段分组保留全部原字和身份。')
 elif t and re.fullmatch(r'2007-\d{2}-\d{2}\d{2}:\d{2}:\d{2}',t):propose('passages',row['id'],dict(published_at=t[:10]+' '+t[10:]),'原页作者署名时刻及承接段可核，仅规范日期与时刻间空格，数值/原字符不变。')
notes={
 '0312-fig1':('unverified','红框/蓝色走势/绿色后续及A/B/C为汇编示意，无作者原发证明；内嵌1分钟顶背后盘整再上涨文字，不把色线几何补成完整递归定义或必然大级反转。'),
 '0314-fig1':('later_annotation','深成5分图头选择4/9而右端含4/10行情，嵌4/6和4/9评论；后行情不证明当时已知万点突破或管理层行动，缺口有效性仍是原文待确认。'),
}
for short,(status,note) in notes.items():propose('figures',DOC+'-p'+short,dict(origin_status=status,note=note),'实际查看PDF311至316六页和两幅整图，核示意/市场图日期与文后来源。')
assert len(ops)==17 and sum(x['table']=='passages' for x in ops)==15
plan=dict(stage='C/E-source-provenance',plan_format=1,schema_version=meta['schema_version'],base_graph_version=meta['graph_version'],documents=[dict(r) for r in db.execute('select * from documents order by id')],new_units=[],operations=ops,visual_pages=list(range(311,317)),pending=['316-b004夹注禅师的意思为进行式非完成式，整理者未核；作者证据只引注前/注后可分离原句，整段混合身份待核不将注作作者断言。','本课区分同级背驰与小级转大、进入背驰段非最终背驰，B/C重合演化不等日线中枢已成；图1后加1原发未核。'],reviewer='Codex 主代理 / 43课跨日时间、混合夹注及原图来源复核')
Path(__file__).with_name('stage-c-l043-source-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(dict(operations=len(ops),passages=15,figures=2,base=meta['graph_version']),ensure_ascii=False))
