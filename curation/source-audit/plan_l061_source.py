"""Plan lesson61 nested quotation boundaries and all eleven figure origins."""
import hashlib,json,sqlite3,sys
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';DOC='volume_1-a53e99c37ca5'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
meta={r['key']:json.loads(r['value']) for r in db.execute('select * from metadata')};assert meta['graph_version']=='0.1.0-review-bb28763cfcd8';ops=[]
def propose(table,id,after,reason):
 row=dict(db.execute(f'select * from {table} where id=?',(id,)).fetchone());after={k:v for k,v in after.items() if row[k]!=v};assert after
 op=dict(table=table,id=id,before={k:row[k] for k in after},after=after,reason=reason)
 if table=='passages':
  refs=[dict(r) for r in db.execute('select e.id,e.claim_id,c.review_status from evidence e join claims c on c.id=e.claim_id where e.passage_id=?',(id,))];assert not any(r['review_status']=='reviewed' for r in refs)
  op.update(text_sha256=hashlib.sha256(row['text'].encode()).hexdigest(),affected_references=refs)
 ops.append(op)
for short in ['0461-b004-s01','0461-b005']:
 propose('passages',DOC+'-p'+short,dict(published_at='2007-05-22 08:49:55'),'PDF461为6/22文章内引5/22旧回复，署名/风险段直至原中文闭引号，仍保旧答身份日期，只补日期时刻空格。')
for short in ['0461-b006']+[f'0462-b{i:03d}' for i in range(5)]:
 propose('passages',DOC+'-p'+short,dict(role='author_commentary',published_at='2007-06-22 08:30:44'),'PDF461原5/22引用在前段末中文闭引号结束；还有一只是600569起恢复6/22独立文章，内述6/13复牌和600636建仓，至462出差结束。非5/22作者回复，原字/几何不动。')
notes={
 '0458-fig1':('unverified','1分原样图到6/20，55至74、四重背驰红箭头及MACD12/26/9；可在6/21课程前取得而原发未核，正文65/69/71/71内部四重与74对69—72枢，不借后K证明当下可成交。'),
 '0459-fig1':('later_annotation','重绘头6/25、右端扩至89并叠6/21收评，晚于6/21；4244/4144与正文最低4147分开保，未来6/22至后续K不证前预测。'),
 '0463-fig1':('unverified','1分原样到6/22，72至87、81—82/84/微枢箭头/87；原87低4024.92，86—87无背驰未确认结束，4131的85为条件，正文30分枢4067—4192为粗数不据图修正。'),
 '0463-fig2':('later_annotation','重绘头选6/22但较上方原图额外出现88/89及3981.72低，叠6/22评论，后K延伸超过当时87；原图87=4024.92与该图后低3981.72不合并，不证明当时线段已完。'),
 '0464-fig1':('unverified','6/23正文明确称随手画两图，图一若干上下形态均等价为一线段；汇编位图原发一致性未外核，文字关联强于泛无署名图，但不以此改后62/67严格定义。'),
 '0464-fig2':('unverified','6/23图二含等号/不等号及小级别转大级别标记，区分易混形态；原发一致性未核，不从手绘无坐标图生成数值阈值或自动完备判段算法。'),
 '0465-fig1':('later_annotation','重绘头6/26而右端已到6/27，叠6/26凌晨对前交易日解盘；原91低3818.85与后原图3819.03/3819.05分开，不能将未来图证当时3982/4025条件。'),
 '0466-fig1':('later_annotation','重绘头6/27但右端含6/29及105低3779.81，晚于6/27解盘；4025、4131和新5分震荡是当时条件，后跌不证预测或精确成交。'),
 '0467-fig1':('unverified','1分原样到6/28，100顶背驰/102二卖与103未完成、紫线MACD比较，原91低3819.03；正文要102走完与前103矛盾保原待核，不能据图静改字。'),
 '0468-fig1':('unverified','6/29早重标前日1分图，含红绿箭头4022.69/4022.42精度讨论、104较细分编号，原91低3819.05；两位小数/直接取整/四舍五入三标准分别保，不倒写前日标号。'),
 '0469-fig1':('unverified','1分原样到6/29，105最低3780.84及106—108，105无明确一分中枢故仅盘中意义；图低3779.81重绘/3780.84此原图分开，不擅改正文压力3919或最低级别范围。')}
for short,(status,note) in notes.items():propose('figures',DOC+'-p'+short,dict(origin_status=status,note=note),'主代理实际核457至470十四页和11整图；7原发未核/4后加，嵌套旧回复边界、原编号/小数差和未来K分别记录。')
plan=dict(stage='C/E-source-provenance',plan_format=1,schema_version=meta['schema_version'],base_graph_version=meta['graph_version'],documents=[dict(r) for r in db.execute('select * from documents order by id')],new_units=[],operations=ops,visual_pages=list(range(457,471)),pending=['6/21课头仅日期，不补TOC里的时分；6/22文章内5/22旧答结束后角色/日期须恢复，原字与坐标保留。','69/70/71/72四重套与74二三卖结合律、5段子级完整条件不删；103未完/要102完、跌段后高低于前低原字、6/29直接取整有明确以后时效。'],reviewer='Codex 主代理 / 61课十四页十一图同模型四轮，知识库范围')
Path(__file__).with_name('stage-c-l061-source-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(dict(operations=len(ops),passages=8,figures=11,base=meta['graph_version']),ensure_ascii=False))
