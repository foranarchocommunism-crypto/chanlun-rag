"""Plan lesson46 timestamps and later teaching-chart provenance only."""
import hashlib,json,re,sqlite3,sys
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';DOC='volume_1-a53e99c37ca5'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
meta={r['key']:json.loads(r['value']) for r in db.execute('select * from metadata')};assert meta['graph_version']=='0.1.0-review-f348422e88c4'
ops=[]
def propose(table,id,after,reason):
 row=dict(db.execute(f'select * from {table} where id=?',(id,)).fetchone());after={k:v for k,v in after.items() if row[k]!=v};assert after
 item=dict(table=table,id=id,before={k:row[k] for k in after},after=after,reason=reason)
 if table=='passages':
  refs=[dict(r) for r in db.execute('select e.id,e.claim_id,c.review_status from evidence e join claims c on c.id=e.claim_id where e.passage_id=?',(id,))];assert not any(r['review_status']=='reviewed' for r in refs);item.update(text_sha256=hashlib.sha256(row['text'].encode()).hexdigest(),affected_references=refs)
 ops.append(item)
for row in db.execute("select * from passages where unit_id='lesson-046' order by pdf_page,block_index,id").fetchall():
 short=row['id'].split('-p')[1];t=row['published_at']
 if short in {'0335-b003','0335-b004','0336-b000','0336-b001'}:propose('passages',row['id'],dict(published_at='2007-04-19 15:37:29'),'335-b002原段尾4/19时间头支配后续四段解盘，前4/18段及尾头原字符不改。')
 elif t and re.fullmatch(r'2007-\d{2}-\d{2}\d{2}:\d{2}:\d{2}',t):propose('passages',row['id'],dict(published_at=t[:10]+' '+t[10:]),'作者时间头及承接段可核，仅日期和时刻缺空格规范，不改原数字、身份或几何。')
notes={
 '0332-fig1':('later_annotation','讲义图署FHSL 20080725、引用颜色说明及网站水印，晚于2007/4/18正文；一中枢/强弱平衡示意不作为作者原图或前三K预知全天极值证明。'),
 '0333-fig1':('later_annotation','讲义图署FHSL 20080725，含两中枢/单边区间的升降示意和4/17例，属后加教学整理；不能由插画补端点相等/三K归属或全天提前分类算法。'),
 '0334-fig1':('later_annotation','讲义图署FHSL 20080725，并附2008/7/17至25上证30分图，明确晚于2007原课；2007/2/27例与2008图分开，不把后加骗线/多空暗示当作者已知结果。'),
 '0334-fig2':('later_annotation','上证30分选择栏4/20而右端至4/24后，嵌4/18与4/19评论；未来K不证明当时延伸/三买/缺口压力判断已验真或安全。'),
 '0335-fig1':('unverified','上证5分图为4/19同日收盘可见行情，嵌当日15:37原文，制作者/原发未核；11:08与1030至1330三K之不同对象分开，不把图价位当普遍阈值。'),
 '0336-fig1':('unverified','上证1分图4/18、嵌同日16:41答，标4/17 14:53至4/18 10:01与13:35至14:16两段；图可于答时已有但原发身份未核，绿面积对比文字独立支持，不证明幅度公式。'),
}
for short,(status,note) in notes.items():propose('figures',DOC+'-p'+short,dict(origin_status=status,note=note),'实际查看PDF331至339九页及6整图，核讲义署期/2008案例、市场图选择栏与右端、文字日期和周期作用域。')
passage_count=sum(x['table']=='passages' for x in ops);assert passage_count==27 and len(ops)==33
plan=dict(stage='C/E-source-provenance',plan_format=1,schema_version=meta['schema_version'],base_graph_version=meta['graph_version'],documents=[dict(r) for r in db.execute('select * from documents order by id')],new_units=[],operations=ops,visual_pages=list(range(331,340)),pending=['三相邻30分K线的日内中枢辅助定义与递归走势中枢分开；强弱两极值同在前三K/等值/边界未穷尽，图4后加2原发未核。','337-b013括号转引提问只引作者答尾，基金指控/14只收益不认证，T+1为作者历史操作语境非现行法律建议。'],reviewer='Codex 主代理 / 46课辅助日内分类、时间与教学图来源复核')
Path(__file__).with_name('stage-c-l046-source-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(dict(operations=len(ops),passages=passage_count,figures=6,base=meta['graph_version']),ensure_ascii=False))
