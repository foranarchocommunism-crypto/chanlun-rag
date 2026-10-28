"""Materialize the manually read lower 92-93 batch; SQLite is read-only.

Four passes are perspectives of the same agent, not independent reviewers.
This script writes review artifacts only. Publication has a separate backup gate.
"""
import hashlib
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

AGENT=Path(__file__).resolve().parents[2]
KB=AGENT.parent/'shared-knowledge/v0.1.0'
OUT=Path(__file__).resolve().parent
DOC='volume_2-5332cd1b6038'
BASE='c_stage_l092_l093'
REVIEWER='Codex 主代理 / 阶段C下册92—93课同模型四轮复核'
SOURCE_SHA='2c0574528df840512d1b6c9a51a5294777372b6b295da86464aa8630e5d49aeb'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
db.row_factory=sqlite3.Row
metadata={r['key']:json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version']=='1.1.0'
assert hashlib.sha256((KB/'sources/volume_2.pdf').read_bytes()).hexdigest()=='5332cd1b60381c47ceb81358db6bbb47882efd074fc5c869dcc3002aaed1b5c0'
passages={r['id']:dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id BETWEEN 'lesson-092' AND 'lesson-093' ORDER BY pdf_page,block_index,id")}
assert len(passages)==229
assert hashlib.sha256(json.dumps(sorted(passages.values(),key=lambda p:p['id']),ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==SOURCE_SHA
old={r['id']:dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts={r['label']:dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical={label:r['label'] for r in concepts.values() for label in [r['label']]+json.loads(r['aliases'])}
figures=[dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 290 AND 310 ORDER BY pdf_page,id',(DOC,))]
assert len(figures)==12
rows,pending,notes=[],[],{}
retained=defaultdict(list)

def pid(short):
    page,block=short.split('-',1)
    return f'{DOC}-p{int(page):04d}-{block}'

def ev(short,quote=None,figs=()):
    p=passages[pid(short)]
    clean=re.sub(r'(?:\*+)?(?:200[78]-\d{2}-\d{2}\d{2}:\d{2}:\d{2})$','',p['text']).rstrip('*')
    quote=clean if quote is None else quote
    start=p['text'].find(quote)
    assert start>=0 and p['text'][start:start+len(quote)]==quote,(short,quote)
    return {'passage_id':p['id'],'quote':quote,'quote_start':start,'figure_ids':[f'{DOC}-p{n:04d}-fig{k}' for n,k in figs]}

figure_notes={
 (291,1):'12/28分时图279至300标号，图300未确认须依正文；制作人未核，不从线条认定已完成',
 (294,1):'1/3嵌文但行情至1/14及5522.6，后期；当时三买尚未给出，不用未来突破认证',
 (295,1):'600636日线ABC与120日线及12.96/8.51标记，光标1/4，制作人未核；正文井上沿13为近似待确认',
 (295,2):'1/4文旁周K延至2月含4195.8，后期；不反填当时(1,1)以后状态',
 (296,1):'600078日K光标1/4、13.78标记，制作人未核；正文只是另一类型的作业，不能补成作者已给买点',
 (296,2):'000938日K光标1/4、24.65标记，制作人未核；图趋势线非作者正文逐条确认',
 (298,1):'1/8文旁行情至1/11、标号287至320及两个5F框，后期；框不改当天第一支已否及后两支选择',
 (301,1):'1/11嵌文但周K至2008年11月1664.93，后期；不以未来下跌证明当时已知全部骗线',
 (303,1):'当底分型让吻飞起来，署名一律斩首，5日/10日均线三图，明确第三方整理；不作作者吻/均线新定义',
 (304,1):'1/16嵌文但日K至2月4195.8，后期；原文顶后能否延伸及底分型仍须考察',
 (308,1):'1/19文讨论四支点通道能否形成，图有1/18光标却至2月4195.75，后期；未来通道线不改当时条件',
 (310,1):'1/21嵌文但行情至1/22及4576.4，后期；1F三卖标号不替原文完成分钟级路径证明'
}

def c(lesson,slug,shorts,text,labels,level,check,conditions=(),exceptions=(),figs=(),ambiguity='none'):
    citations=[ev(s,figs=figs if i==0 else ()) for i,s in enumerate(shorts.split())]
    cid=f'lower-l{lesson:03d}-c-stage-{slug}'
    assert cid not in old and cid not in {r['id'] for r in rows},cid
    labels=list(dict.fromkeys(canonical.get(x,x) for x in labels.split('|')))
    ps=[passages[e['passage_id']] for e in citations]
    context=f"第{lesson}课；角色{'/'.join(dict.fromkeys(p['role'] for p in ps))}；时间{'/'.join(dict.fromkeys(p['published_at'] or '无单独时间' for p in ps))}"
    reasons={1:'基础核心：定义及不能省略的前提。',2:'主要方法：影响结构识别与操作选择。',3:'补充深化：范围与边界。',4:'背景细节：历史案例、自述或作者经验立场。'}
    r={'id':cid,'text':text,'kind':'explicit','conditions':list(conditions),'exceptions':list(exceptions),'concepts':labels,
       'ambiguity_status':ambiguity,'review_note':f'语境：{context}。适用条件：'+('；'.join(conditions) if conditions else '本条列出的对象、级别及上下文')+
       '。四轮：通读全部正文及问答；拆分结论和联合条件；对照既有命题与标准概念；逆向核对原句、原页及涉及的图。'+check+
       '。同模型四轮不代表独立审查者；仅据固定汇编，未核原博客。',
       'importance_level':level,'importance_reason':reasons[level]+check,'reviewer':REVIEWER,'evidence':citations,'relations':[]}
    if figs:
        r['figure_review_note']='主代理实际查看原页及单图：'+'；'.join(figure_notes[x] for x in figs)+'。制作人均未核；后加图及未知示意图不作作者观点的唯一证据，命题由正文独立支持。状态：'+'；'.join(f['id']+'='+f['origin_status'] for f in figures if f['id'] in citations[0]['figure_ids'])
    rows.append(r)
    return cid

def note(shorts,category,reading,inverse):
    for s in shorts.split():
        assert pid(s) in passages,s
        notes[pid(s)]={'category':category,'reading':reading,'inverse':inverse}

def keep(shorts,cids,reason):
    for s in shorts.split():
        for cid in cids.split():
            assert cid in old,cid
            retained[pid(s)].append(cid)
    note(shorts,'existing_claim_retained',reason,'保留当前原段和跨课线索，不擅改旧命题及旧证据。'+reason)

def issue(slug,shorts,description,action,blocker=False):
    pending.append({'id':'lower-l092-l093-c-stage-pending-'+slug,'status':'pending','passage_ids':[pid(s) for s in shorts.split()],
                    'description':description,'suggested_action':action,'blocks_full_semantic_extraction_completion':blocker,'reviewer':REVIEWER})




# Selected after reading all 229 passages and 12 figures, then reversed.
c(92,'oscillation-ends-third-point','290-b004','作者说中枢震荡最终一定以某级别的第三类买卖点结束，监控震荡强弱及大致高低区间是其操作价值。','中枢震荡|第三类买卖点|级别',1,'某级别不能删成固定本级，监视预警与最终确认分开。',['已经确立的中枢震荡'])
c(92,'axis-and-secondary-midpoints','290-b005','中枢确立后，其中枢区间的一半位置称震荡中轴Z；每个次级震荡区间的一半位置依次称Zn，Zn恰等于Z只是特殊状态。','震荡中轴|中枢震荡监视器|中枢震荡|次级别|价格区间',1,'Z和Zn都是位置，非第20课的Z走势段或第88课周线编号；正文未给次级区间取样完整算法。',['中枢已经确立'],ambiguity='secondary_interval_sampling')
c(92,'relative-strength-and-monitor-curve','290-b006','Zn在Z之上偏强，在Z之下偏弱；中枢区间[A，B]的A、Z、B三条线等距，将Zn波动连成曲线即为中枢震荡监视指标。','震荡中轴|中枢震荡监视器|中枢震荡|价格区间',1,'偏强弱只针对所述震荡，不把Zn中点误当最高点、最低点或独立买卖点。',['所述已确立中枢及对应次级震荡区间'])
c(92,'nine-observations-not-any-nine-bars','290-b007','作者说该监视器的Zn数据不会超过9个，超过则次级别要升级，所以对这少量点再作中枢、走势类型分析意义不大。','中枢震荡监视器|次级别|中枢扩展|走势类型',3,'九是本段次级震荡中点数据的语境，非任意九根K线、九笔必升级；如何取样与计数完整边界待核。',['第92课该已确立中枢的Zn序列'],ambiguity='nine_secondary_midpoints_scope')
c(92,'eventual-boundary-cross-author-necessity','290-b008','作者以第三类买卖点最终必出现为由，断言Zn最终肯定超越A或B。','中枢震荡监视器|第三类买卖点|价格区间',1,'最终关系不提供下一次跨界的时间或方向，不自补逐步严格证明和算法。',['第92课所设中枢及次级震荡Zn序列'])
c(92,'boundary-cross-not-sufficient','290-b009','Zn超越A或B不意味着一定出现第三类买卖点，超越可能多次，只有最后一次才构成；一般这样的超越只是震荡面临变盘的大提醒。','中枢震荡监视器|第三类买卖点|中枢震荡|确认',1,'原文明确反向不成立；不能把任一次中点越界直接标成三买或三卖。',['Zn超越该中枢A或B边界'])
c(92,'no-third-point-extension-probabilistic','290-b010','若Zn超越边界却未构成第三类买卖点，作者说一般将构成中枢震荡级别扩展，但明确没有100%的绝对性，仅称概率极高。','中枢震荡监视器|第三类买卖点|中枢扩展|概率原则',1,'概率为作者经验断言，无样本及统计结果；一般不得变成无例外必然。',['Zn超越A或B且未构成第三类买卖点'],exceptions=['作者明确说没有100%的绝对性'])
c(92,'buy-risk-below-axis','290-b011','对于震荡中的买入，作者认为Zn在Z之下甚至A之下时介入风险较大，若动作不快，可能受阻于交易通道而不能顺利完成震荡操作。','中枢震荡监视器|震荡中轴|交易通道|操作熟练程度|市场风险',2,'风险和可能不是必亏或绝对禁止买入，必须保留震荡操作和执行速度条件。',['所述中枢震荡中的买入'])
c(92,'slow-rise-without-break-wedge-risk','290-b012','Zn缓慢提高却无力突破B时须防突然变盘，作者说一般会构成上升楔型等诱多图形；反向也有下降楔型诱空。','中枢震荡监视器|多头陷阱|空头陷阱|市场风险',2,'缓升与无力突破联合，不把Zn上升本身等同必上涨或必诱多；正文用一般。',['Zn缓慢提高且无力突破B的情形，反向类比'])
c(92,'secondary-trend-last-center-condition','291-b000','次级震荡若为趋势且Zn相应配合，须注意变盘；特别是其最后一个次级别中枢在所监视中枢之外，下一个次级别走势又在该次级中枢区间完成时，作者说震荡会变盘。','中枢震荡监视器|次级别|趋势|走势中枢|完成',1,'次级趋势、Zn配合、最后次级中枢在外和后继在其区间完成不缩为任意趋势必变盘；Zn相应配合未量化。',['次级震荡为趋势类型且Zn相应配合','所述最后次级中枢在所监视中枢之外','下一个次级走势在该次级中枢区间完成'],ambiguity='zn_corresponding_cooperation')
c(92,'boll-timing-combination','291-b001','作者提出将Zn监视器与布林通道的时间把握结合，称可提高对震荡变盘的预见性。','中枢震荡监视器|布林通道|中枢震荡',2,'仅作者方法主张，未在此指定周期、参数、命中率；前课结构选择条件仍保留。')
c(92,'smooth-midpoint-only-rough-estimate','291-b002','除特殊情况外，作者说Zn变动相对平滑，可大致预计下一Zn区间，结合当下震荡一端，大致估算下次高低点。','中枢震荡监视器|高低点|价格精度|价格区间',2,'两个大致及特殊情况必须保留；未提供特殊情况定义、拟合方法或误差保证，不补精确镜像预测公式。',exceptions=['特殊情况'],ambiguity='midpoint_forecast_unquantified')
c(92,'dec28-two-center-third-points-divergence','291-b005 292-b000','12月28日作者将286、296分别认作第一、二中枢的三类点，297顶背驰后至少回到287下且已完成，称1分钟走势向5分钟扩展、新5分钟中枢已形成。','第三类买卖点|背驰|中枢扩展|走势中枢|级别',1,'日期限定；原文4800约数与前课4812不擅改，图300仍另声明未完。',['2007年12月28日该次上行及回跌'],figs=((291,1),))
c(92,'dec28-five-up-or-consolidation-open','292-b001 292-b007','12月28日作者仍待判断5分钟走势类型是上涨还是盘整；若上涨，该中枢才是第一个，随后观察三类点，并特别声明图中的300尚未完成。','走势类型|盘整|上涨|走势中枢|完成',1,'首中枢已成不能直接宣布完整5分钟上涨；300未完成不因图线已画到而覆盖。',['2007年12月28日该5分钟结构'],figs=((291,1),))
c(92,'jan2-stock-index-relative-strength','293-b010','1月2日作者把个股对应6124点时的高位作为该次行情强弱分界，强调突破后还要站稳，并以600737的14元多至20元上为例。','指数走势背离|突破|确认|价格区间',4,'是当时个股的参照位，不是指数6124数值直接当所有个股价格，更非现在选股建议。',['2008年1月2日所论个股与6124时高位'])
c(92,'jan2-breakout-pullback-two-skill-paths','293-b011','对个股突破后反复，作者给技术高者顺势做短差且不丢筹码的做法；另一做法是设5周线之类中线位置，调整不破则持有。','操作熟练程度|均线|持股|操作策略',2,'5周线之类为可选中线参照，不是每股每级别唯一标准；保持筹码是执行要求，不认证操作必成功。',['1月2日所论个股突破后的反复'])
c(92,'jan3-neckline-no-third-not-certain','294-b001 297-b002','1月3日作者说站住5209后下一位置5500—5600，但5分钟震荡尚无三买，不能说颈线突破100%有效；1月4日也重申未出三买的突破没有100%保证。','颈线|突破|第三类买点|确认|概率原则',1,'口号向5600不替代三买确认，也不把未来图当当日已确认。',['2008年1月3—4日该5分钟中枢和5209颈线'],figs=((294,1),))
c(92,'jan4-week-up-extension-and-top','295-b002 295-b003 295-b004','作者1月4日称突破5336使周线(1,1)延续，以周(1,0)、即周顶分型出现为该种持股观察边界，并举3563至6124为历史示范。','笔状态|顶分型|持股|周期K线图',2,'这是周K笔状态方法，不是严格周级别走势中枢已上涨，更不是利润无风险保证。',['2008年1月4日该次周上笔延伸'],figs=((295,2),))
c(92,'jan4-low-period-differences-skill','295-b005','周(1,1)延伸中，作者允许技术高者利用低级别走势做差价或不同级别震荡换股；无相应技术者按所选周顶分型观察持股。','笔状态|操作熟练程度|板块轮动|操作策略|顶分型',2,'能力分支不能拼成任何人都须频繁短差；未来周K不证明当时利润有保障。',['所论周上笔延伸阶段'])
c(92,'jan4-abc-120-day-well-example','296-b000','作者以600636为例描述ABC下跌中B受120日线阻力、挖井后突破120日线并回试、回到13元附近井上沿，后面才看上沿能否站住。','均线|反抽|确认|走势分解|价格区间',3,'历史教学例，13为附近；到达上沿不等于已确认站稳，ABC不自动赋予严格级别。',['2008年1月4日600636案例'],figs=((295,1),))
c(92,'jan8-strong-gap-branch','298-b002 298-b003','1月8日分类最强支是回跌在当天跳空附近站住：作者说5200上1分钟上涨形成、结束后对应5分钟三买，极可能发展4800上5分钟上涨，最坏为大30分钟中枢。','完全分类|第三类买点|上涨|走势中枢',2,'站住与上涨结束后条件保留，极可能不升必然；这一支随后正文明确已被当日走势否定。',['2008年1月8日该次震荡分类','在当日跳空附近站住'],figs=((298,1),))
c(92,'jan8-second-consolidation-branch','298-b004','若在5360那1分钟中枢站住，向上偏移仅为1分钟盘整；再站住成三买时，大5分钟中枢机会较大，但仍可能突破爆发并继续上移至更高处形成5分钟中枢。','完全分类|盘整|第三类买点|中枢上移|走势中枢',1,'盘整次级偏移后的三买一般较弱，不是绝不能上移；前提和爆发例外都保留。',['2008年1月8日所论向上偏移','在5360附近1分钟中枢站住'],exceptions=['也可能突破爆发继续中枢上移在更高位置形成5分钟中枢'])
c(92,'jan8-third-return-branch','298-b005','若跌回5200点上原5分钟中枢才站住，作者判该例形成一个大的30分钟中枢。','完全分类|中枢扩展|走势中枢|级别',1,'限原5分钟结构和回跌对象，不将任意跌回任意中枢等同30分钟升级。',['2008年1月8日该次回跌','跌回5200点上原5分钟中枢才站住'])
c(92,'jan8-strong-exception-and-first-denied','298-b006 298-b007','该分类除最强继续1分钟中枢上移外，其余面对至少5分钟中枢、最坏30分钟中枢；作者随即说当日已否定第一支，只需对应第二、三支。','完全分类|中枢上移|中枢扩展|走势中枢',1,'展望分支与当日筛除分开，不因图后期呈现某框而说开盘时已知结局。',['2008年1月8日所列具体震荡分类'],exceptions=['最强继续1分钟中枢上移'])
c(92,'jan8-strategy-matches-time-and-speed','299-b003','作者区分能处理买卖点、背驰、震荡和换股者，与没时间或短线反应慢而看周顶分型、5周线持有者，强调并非每种操作适合任何人。','操作熟练程度|操作策略|顶分型|均线',1,'对号入座是方法适配条件，不能把短差和中线持有同时强加所有人。')
c(92,'jan9-no-response-no-oscillation-trade','299-b010','1月9日作者用日(1,1)是否被打破观察震荡；技术高者震荡后回补，没有回补反应能力者就不做该类震荡操作。','笔状态|操作熟练程度|中枢震荡|操作策略',2,'日K笔状态与中枢级别区分；条件不变成任何调整都自动结束。',['2008年1月9日当次震荡操作'])
c(92,'jan10-eighth-price-reference','300-b006 300-b007 300-b008','1月10日作者以3600的八分比例列6124下3/8为4774、2/8为5224、1/8为5674，并与实际4778、5209比较；另记半跌幅5451、颈线5462、2/3反弹位5675附近。','价格区间|价格精度|走势预测|颈线',4,'原文数字照录，5675为作者近似参照；不能据巧合价位证明可预测或要求必须先到5675。',['2008年1月10日该次6124起跌幅参照'])
c(92,'jan10-gap-policy-conditional','300-b009 300-b010','作者1月10日所说5860—5912补缺口的剧本，取决于5462—5675区间过程中的政策风向；风向不对便放弃补缺口安排。','缺口|政策风险|走势预测|完全分类',2,'区间内观察条件不等于先到区间上端；隐喻不当真实操盘成交或预测必达证据。',['2008年1月10日该区间及缺口情景','5462至5675过程中政策风向允许'],exceptions=['政策风向不对则放弃原安排'])
c(92,'jan11-macd-contraction-possible-trap','301-b001 301-b002','1月11日作者提示周MACD绿柱收敛转红途中可能突然转折形成骗线，并明确这只是技术上的可能陷阱，政策天气无须预测。','MACD|市场陷阱|政策风险|概率原则',2,'可能不当已经确认陷阱，2008年11月后期周图不能认证当时预测准确率。',['2008年1月11日周图背景'],figs=((301,1),))
c(92,'jan14-strategy-capability-period','302-b003','1月14日作者建议技术不行者中线观察周(1,1)与5周均线、短线观察日相应指标；技术好者可利用5分钟震荡节奏做板块操作。','笔状态|均线|操作熟练程度|板块轮动|操作策略',2,'中线、短线及能力三种限定保留，笔状态并非中枢级别，未设统一时间周期换算。',['2008年1月14日该市场背景'])
c(92,'jan15-two-adjustment-paths','302-b005 302-b006 302-b007 302-b008','面对该压力期，作者列急跌以空间换时间、或震荡缩量以时间换空间两支，都扩展30分钟中枢后再求突破；量能缩下来一般偏第二支，否则不排除一两天急跌。','完全分类|成交量|中枢扩展|走势中枢|市场风险',2,'限该压力期结构；一般与不排除不写成量能单因素充分判据，求突破非保证向上。',['2008年1月15日该次压力期与已有中枢'])

c(93,'zero-state-two-outcomes','302-b012','作者重申(1,0)或(-1,0)之后均可能连接(1,1)或(-1,1)，零态信号本身不能唯一确定下一方向。','笔状态|表里关系|确认',1,'两种方向与91课允许连接一致，不把零态当已反转；下一段符号不一致另列待核。')
c(93,'conservative-withdraw-cost-leave-profit','303-b001','震荡能力一般、胆小又缺时间或跑道、偏好落袋者，在足够周期的(1,1)后出现(1,0)，且已有足够获利空间时，可先兑现成本、留下利润交市场选择。','笔状态|资金管理|成本|操作熟练程度|交易通道',1,'足够周期、已有利润及人群条件不删；不是亏损仓也可凭空留下利润，不保证余仓无损。',['震荡能力一般、胆小、缺时间或跑道而偏好落袋','足够周期(如周或日)上延后转(1,0)','已有足够获利空间'])
c(93,'remaining-exit-lower-stroke-no-new-high','303-b002','剩余筹码若遇所看周期(-1,1)，作者称低周期也会有(-1,1)；等该下笔结束后的向上笔不创新高可卖余仓，周周期可看日或30分钟。','笔状态|表里关系|高低点|操作策略',1,'所看周期下延、低周期下笔结束后回上及不创新高联合；不将下笔未结束的一次反弹直接确认退出点。',['第93课先取成本后的余仓','所看周期出现(-1,1)','低周期下笔结束后的向上笔不创新高'])
c(93,'remaining-exit-five-week-alternative','303-b002','对所论周周期余仓，作者另给更简单的办法：直接观察5周均线，有效跌破即走。','均线|有效跌破|操作策略|笔状态',2,'另一选择而非与低周期不创新高必须同时满足；有效没有在这里统一根数或百分比。',['第93课周周期余仓处理'],ambiguity='effective_break_threshold_unspecified')
c(93,'skilled-sell-first-no-rebuy-down-state','303-b003','震荡水平较好者可利用(1,0)后的震荡先卖后买做短差；若市场选择(-1,1)，最后一次不回补而退出。','笔状态|中枢震荡|操作熟练程度|操作策略',1,'只限相应能力及先卖后买路径，不把已转下延还机械回补当作者方法。',['震荡操作水平较好','利用所论(1,0)后震荡且先卖后买'],exceptions=['市场选择(-1,1)则最后一次不回补'])
c(93,'weekly-state-corresponding-small-uptrend','303-b004','做短差前须分析(1,1)转(1,0)对应走势类型；作者举周线状态转换对应小级别上涨，其级别可为1、5或30分钟，取决于具体图形。','笔状态|走势类型|表里关系|上涨|级别',1,'周K时间周期不与严格走势级别固定对应，不能预设每次周顶都对应30分钟上涨。',['第93课所论周线(1,1)转(1,0)及短差分析'])
c(93,'confirmed-divergence-last-center-reference','303-b005','若对应上涨已明确背驰并完全确认结束，作者以其最后一个中枢为震荡区间依据；围绕该区间是强震荡，否则判将转(-1,1)为弱震荡。','背驰|确认|走势中枢|笔状态|中枢震荡',1,'明确背驰且完全确认上涨结束是本支前提；文中两种情形只显式编号一项，不补第二项。',['所论(1,0)对应上涨明确背驰且已完全确认结束'],ambiguity='second_situation_not_explicitly_numbered')
c(93,'weak-confirmed-avoid-until-bottom-zero','303-b005','在上述弱震荡一旦确认后，作者一般建议不参与，等待(-1,0)再观察。','笔状态|中枢震荡|操作策略|确认',2,'一般不是无条件禁止，等底构造不等于底已确认或必反转；沿用明确背驰结束该支范围。',['第93课已确认的所述弱震荡'])
c(93,'resumed-up-compare-strength-and-nesting','303-b006','若市场最终选择(1,1)，中间(1,0)区间可作为两段(1,1)力度比较的参照；后一段弱于前一段时作者称明确见顶信号，再按对应走势类型用区间套定位。','笔状态|背驰|区间套|走势类型|表里关系',1,'力度方法须依对应走势类型，信号后仍要区间套定位；不是所有同向两笔不看结构只比幅度。',['市场经所论(1,0)后恢复(1,1)','后段力度小于前段'])
c(93,'jan16-gap-and-neckline-conditional','304-b005','1月16日作者说当日缺口若三天内未补会增加后续压力，5209颈线只要未有效跌破仍属多头控制。','缺口|颈线|有效跌破|确认',2,'三天是该缺口案例的时间条件，不推广任何缺口或中枢确认都固定三天。',['2008年1月16日所论缺口及5209颈线'])
c(93,'jan16-analog-decline-rebound-second-center','304-b006','5522下来线段类下跌有两个类中枢，作者观察类背驰后的反弹能否突破第二类中枢牵制，否则补缺口困难。','线段|类中枢|类背驰|反弹|缺口',1,'类中枢与类背驰不静默变成严格该图周期的中枢/背驰，反弹仍有突破条件。',['2008年1月16日5522起该类下跌'])
c(93,'jan16-top-to-stroke-bottom-await','304-b007 305-b000','1月16日日顶后向下延伸成笔尚为可能，需次日新低才基本确定；稳健者等底分型才可能真正站稳，再考察类背驰能否造出底分型。','顶分型|底分型|笔|确认|类背驰',1,'可能、基本确定和真正站稳可能分层，不把后期图低点倒填当日底已确认。',['2008年1月16日该日顶及下一日条件'],figs=((304,1),))
c(93,'jan17-upstroke-not-segment-destroyed','305-b007 305-b008','1月17日作者称5522起近500点为一线段类下跌，早盘急拉只构成笔、没有破坏下跌线段，最猛烈中枢移动常见线段类趋势。','笔|线段|线段破坏|类背驰|趋势',1,'笔方向暂反不等于线段已破坏；常见描述不成为所有中枢移动仅一段的绝对定义。',['2008年1月17日5522起该线段类下跌'])
c(93,'jan17-single-segment-divergence-scope','305-b009','作者特别说1月17日类背驰不在两个类中枢之间，而在单一线段中；回拉若不能重新站住5209，后面仍要二次探底。','类背驰|类中枢|线段|反弹|确认',1,'与1/16两个类中枢的表述并列不同日观察范围，不擅自用后句删前句或把所有类背驰定义成两类中枢。',['2008年1月17日所述线段内类背驰','回拉不能重新站住5209'],ambiguity='analog_divergence_observation_scope')
c(93,'jan17-capability-position-and-bottom','306-b000','1月17日作者认为会操作30分钟震荡者可利用节奏；没有此水平者应把仓位控制在能睡好的范围，等待日底分型。','仓位|操作熟练程度|底分型|中枢震荡',1,'能力、人群及当时结构保留，不认证震荡收益必超单边。',['2008年1月17日该30分钟震荡背景'])
c(93,'jan18-not-must-reach-5675','306-b007 306-b008','1月18日作者明确否定把此前剧本理解成大盘必须先到5675，指出5522已在5462—5675区间，政策条件可在区间内触发变化。','走势预测|完全分类|政策风险|价格区间',1,'有明确否定原话才形成对误读的澄清关系；不把区间上界目标当必经点。',['第92课1月10日剧本及第93课1月18日澄清'])
c(93,'jan18-operation-three-details','306-b011 306-b012 306-b013','作者把操作细节依次列为认识自身水平、选择相应操作、按规程细节执行，并说第93课须依自己的类型采取对应处理。','操作熟练程度|操作策略|资金管理',1,'自我能力是明确方法条件，不因懂原文即认证实盘执行能力。')
c(93,'jan18-withdraw-cost-with-profit-and-bad-signal','307-b006','在2008年所论难度下，作者忠告技术不足者：已有足够利润又出现不好信号时，先把成本取出。','成本|资金管理|操作熟练程度|笔状态',2,'足够利润与不好信号联合；不当对亏损仓、无信号仓一概取本的命令。',['所述2008年环境下技术不足者','已有足够利润且出现不好信号'])
c(93,'jan18-rotation-not-copy-portfolio','307-b007 307-b008 307-b009 307-b010','作者以自身组合轮动为教学例，认为按组合买卖点轮动可提高资金效率，但不要求复制其组合，没相应水平和意识者不适用。','板块轮动|买卖点|资金管理|操作熟练程度',2,'收益安全说法是作者主张未回测；复制名单不是买卖点，能力门槛不可删。',['具有组合轮动能力和意识'],exceptions=['没有相应水平和意识者不采用'])
c(93,'jan19-neckline-three-day-case','307-b013','1月19日作者说5209跌破尚未到三天基本限期，只要次周初能重新站上即可。','颈线|有效跌破|确认',3,'是具体颈线有效性案例，不自补统一全部有效跌破三根K线规则。',['2008年1月19日5209颈线案例'],ambiguity='effective_break_case_three_days')
c(93,'jan19-thirty-oscillation-can-break-low','308-b000 309-b002','作者说该30分钟震荡最坏可跌破4778；1月21日又将未重新站5209、须二次探底至日底分型，与可破4778的坏分支并列。','中枢震荡|底分型|价格区间|级别',1,'可破不是保证破，也不意味一破4778就否定仍在所论30分钟震荡。',['2008年1月19—21日所论30分钟震荡'])
c(93,'jan19-channel-four-supports-conditional','308-b001 308-b002 308-b003','作者提出多头化解该30分钟震荡的缓升通道方案：日线已有四个原始支点中的三个，若控制这次下跌才能形成第四；上下各两点形成缓速大幅通道。','高点连线|价格区间|走势预测|确认',2,'日图通道是当时条件方案，唯一最佳为作者情境判断，不推广全市场唯一解；第四尚未完成不能由未来线补成。',['2008年1月19日该市场背景','多头能控制此次下跌形成第四支点'],figs=((308,1),))
c(93,'jan19-classify-follow-market-not-camp','309-b000','作者主张不先持多头空头立场，而列出所有可能走势及对应对策，按市场实际选择行动。','完全分类|操作策略|当下',2,'方法立场不认证每次分类已完备，具体区间及条件仍须原文逐条核。')
c(93,'jan21-first-center-down-worst-paths','309-b008','1月21日作者说5522起线段下跌结束后，中阴形成1分钟中枢，最坏可作1分钟下跌首中枢，须等其下跌背驰；若先扩展5分钟，则最坏为5分钟下跌首中枢。','中阴阶段|走势中枢|下跌|背驰|中枢扩展',1,'最坏两支而非已确认完整1或5分钟下跌；原文先扩展才5分钟保留在证据，命题按上下文指扩展到。',['2008年1月21日5522起结构及该30分钟震荡'])
c(93,'jan21-sublevel-five-and-third-buy','309-b008','在该30分钟震荡中作者说次级最大为5分钟；无论后续中枢1分钟或5分钟，都须走出第三类买点才算真正摆脱下跌压力。','次级别|级别|第三类买点|走势中枢',1,'范围是该30分钟震荡及后续中枢，三买是作者摆脱压力的必要条件，不自动保证更大趋势永涨。',['2008年1月21日该30分钟震荡及后续1/5分钟中枢'])
c(93,'jan21-third-sell-formed-downtrend-not-certain','309-b009','作者称1月21日下午该1分钟中枢三卖已制造，后面最好为扩展5分钟中枢，同时认为形成1分钟下跌机会不小。','第三类卖点|下跌|中枢扩展|走势中枢',1,'三卖已出与1分钟下跌尚为机会不同，不从1/22后期图改成当日全路径已确定。',['2008年1月21日当日下午的该1分钟中枢'],figs=((310,1),))
c(93,'jan21-stock-not-index-capability-paths','309-b010','对当时分类，作者给嫌麻烦者等日底分型、短线换股者随中枢演化操作的路径，同时强调指数与所持具体股票常不一致，须观察股票池自身走势。','指数走势背离|底分型|板块轮动|操作熟练程度|操作策略',1,'不能将指数买卖点直接替所有个股买卖点，也不删两类能力/时间分支。',['2008年1月21日所论指数与股票池'])
c(93,'jan21-position-eat-sleep-standard','310-b001','作者将能正常吃饭睡觉列为持仓最基本标准，持有某股已影响睡眠与吃饭时主张退出。','仓位|资金管理|市场心理',2,'作者对持仓承受能力的经验主张，不作医学诊断或获利保证。')
c(93,'jan21-daily-fractal-case-strategy','310-b004','作者对2008年该环境给出见日顶分型走、日底分型再回来的简化练习，称可减少坐电梯。','顶分型|底分型|操作策略|操作熟练程度',2,'限当时教学简化方法，分型与笔确认仍不同，不保证所有股票每一分型都能无成本成交。',['2008年1月21日所论年度震荡环境'])

keep('290-b005 290-b006','upper-l020-z-segment-definition lower-l088-c-stage-level-mark-notation','同样Zn符号在20课为Z走势段、88课为周线编号，92课为次级震荡中点；上下文不同，不注册全局Zn同义概念。')
keep('291-b001','lower-l090-c-stage-boll-contraction-expand-or-end lower-l091-c-stage-boll-select-by-pattern-structure-first','BOLL辅助须选对应结构周期，收口还可扩展震荡，不因92称高预见性取消条件。')
keep('292-b007 294-b001','lower-l091-c-stage-dec24-neckline-break-await-confirm','未完成线段与突破后仍待确认均有前课例；具体对象及日期分别保留。')
keep('302-b012 303-b002 303-b004','lower-l091-c-stage-four-state-meanings lower-l091-c-stage-six-allowed-state-transitions lower-l063-chart-period-not-center-level','零态仍有两向结果；周日K周期笔状态不与走势中枢级别一一对应。')
keep('303-b004 303-b006','lower-l091-c-stage-stroke-layer-not-whole-diagnosis','笔状态一层不足完整诊断；93引入对应走势类型和力度/区间套，不把只是周期状态当全部结构。')

issue('midpoints-sampling-nine-and-prediction','290-b005 290-b007 290-b008 291-b002','次级震荡区间如何划定、Zn实时取样与九点升级边界、特殊情况及预测误差未给完整算法；最终超界不提供时间方向。','保留中点定义、最终断言和大致预测，不自动生成精确实时监视器或任意九根K线升级规则。',True)
issue('zn-notation-collision','290-b005 290-b006','Zn在20课Z走势段和88课周线编号已有不同语义，92课又指次级震荡中点。','按课程与定义区分，不注册Zn为全局唯一概念；仅用震荡中轴/中枢震荡监视器链接本课。')
issue('trend-cooperation-unquantified','291-b000 291-b001','次级趋势与Zn相应配合未量化；结合BOLL未给统一参数或独立实测的高预见性证据。','保留趋势、最后中枢在外及后继在区间完成的联合条件，不编出胜率或唯一周期。',True)
issue('state-symbol-inconsistency','302-b013 303-b000','原文以(1,0)为例，却紧接称(-1,0)这个信号明确；原页确认汇编即如此，不能确定作者笔误或汇编错误。','不静默改字或用该句单独证明方向；依据91/93明确转换原句，等待原博客版本。',True)
issue('second-situation-not-numbered','303-b005 303-b006','正文称(1,0)有两种情形，仅显式列一：对应上涨明确背驰完全结束；下一段说市场最终选(1,1)，但未显式编号二。','保留两段明确内容，不自行将第二种写成未经背驰/小转大等缺失文本。',True)
issue('effective-break-and-force-thresholds','303-b002 303-b006 304-b005 307-b013','有效跌破、足够周期/利润、力度比较未在本课给统一阈值；5209与缺口三天为具体案例，不能泛化通用三天算法。','保留各对象的时间/价格/能力条件，后续查定义或更多明确补充。',True)
issue('analog-divergence-daily-scope','304-b006 305-b007 305-b008 305-b009','1/16两个类中枢后类背驰与1/17单线段内非两类中枢间的说法，观察对象/阶段关系需进一步核图和作者定义。','分别按日期记录，笔未破坏线段与类对象不得升级严格级别；不自行删除前日表述。',True)
issue('historical-forecast-and-profits','293-b012 294-b002 299-b001 300-b008 300-b009 301-b003 307-b002 307-b003 307-b004 307-b005 307-b008 308-b001 308-b003','历史预测、数字巧合、利润和四类投资者命运等为作者意见，未独立验证；通道唯一最佳为当时情境判断。','不将年度预测、千次震荡收益或组合安全性当项目验证，保留后续明确否定必须先到5675。')
issue('figure-makers-and-late','292-b007 294-b001 295-b002 296-b000 296-b001 298-b007 301-b001 303-b007 304-b007 308-b002 309-b009','12图实际检查，七图含文后行情，一张署一律斩首；余四制作人未核。后期线条不能补足未确认三类点/第四支点，第三方吻图不是作者规则。','八图登记后加，其余未核；全部图意仅辅助，正文独立支撑，原博客图版另待核。')

note('290-b003','lesson_context','由解盘中中枢震荡细节引入本课。','引言已读，不独立证明量化监视算法。')
note('291-b004 292-b002 292-b003 292-b004 292-b005 292-b006','historical_annual_outlook','指数油水与个股不同、2008展望箱体功课、井和肥料比喻、学费个股及绿色页面提醒。','年末年度判断及匿名资金自述，不当现行市场事实/投资指令或收益记录。')
note('292-b009 292-b010 292-b011 292-b012 292-b013 293-b000 293-b001 293-b002 293-b003 293-b004 293-b005','historical_policy_opinion','新年剧院评论、直通车/经济治理/地产泡沫引文，药性与用人类比、尚主席升迁主张及创业板/期货/税三愿望。','全文已读；作者政策意见、听说和因果自述未外核，不发布现行人事政策或验证影响力，也不当医学结论。')
note('293-b007 293-b008 293-b009 293-b012 293-b013 293-b014','historical_forecast_and_chasing','指数疲软个股活跃预言、5分钟三类点前仍震荡、年初先取利润与别追高、资金驻守和大家伙比喻。','均为1/2当时判断；不担保资金必拉升、个股风险必低；技术退出选择另抽。')
note('294-b002 294-b003 294-b004 294-b005 294-b006 295-b000','historical_rhetoric_and_levels','5600口号、大家伙抽动、私募与基金资金猜测，6100/530分水及600737学费自述。','口号不当100%突破保证，未核具体操盘收益及各公司，三买确认条件另抽。')
note('296-b001','homework_not_answer','600078与000938另一类型走势留作作业。','两个同日图已查看，但正文没有给该作业的标准买卖点答案，不补作者结论。')
note('297-b000 297-b001 297-b004 297-b005 297-b006 297-b007 297-b008 297-b009 297-b010 297-b012 297-b013','historical_policy_and_warning','喊多头、资金饥饿、紧箍咒政策升级比喻，周日上延与5462周内震荡提示及次日跳空/线段类顶背驰自述。','历史判断与修辞完整阅读，不认证政策真实因果或当时资金结果；周日状态非保证无风险。')
note('298-b000 298-b001 299-b000 299-b001 299-b002 299-b004 299-b005','classification_teaching_and_profit_rhetoric','5462技术点位、课堂玩笑、分类预案与一秒反应要求，千次震荡3000%及坐电梯比喻、陪练意义。','一秒为熟练主张，3000%无成交成本/基数证据，不用已读等于实测利润；三支本身另抽。')
note('299-b007 299-b008 299-b009 299-b011 299-b012 299-b013 299-b014 299-b015 299-b016 299-b017 300-b000','historical_cleaning_rhetoric','清洗与踏空套牢修辞、准备好个股越震越强、年初利润、5462站稳再上与指数个股有别、三种持仓者。','全部为当时经验与比喻，不能推出任何震荡必涨或股价必不受指数影响；按能力策略另抽。')
note('300-b002 300-b003 300-b004 300-b005 300-b011 300-b012 300-b014 300-b015 301-b000','historical_script_and_cash','剧本自述、深圳成分股先头的历史经验与资金猜测、测试风向、5462周末震荡和春节资金饥饿。','未核操盘和1996历史因果，不当所有牛市固定指数领先因果定理。')
note('301-b003 301-b004 301-b005 301-b006 301-b008 301-b009 302-b000 302-b001 302-b002 302-b009 302-b010','historical_policy_and_sector_context','利润安全位置、5600政策敏感、周日(1,1)、春运足球、5462五分钟震荡与板块补涨，6100/530站稳后第二波、耐心。','原文强势用语不作独立安全保证，政策与板块因果未核；按日期保留，不能变为当前预测。')
note('302-b013 303-b000','source_symbol_inconsistency','以(1,0)为例却写(-1,0)信号明确，跨页句子已连读。','原页确有该符号差异，不改底本、不补笔误；唯一性不由不一致句单独认证。')
note('303-b007','method_practice_context','作者强调分类方法需磨练得心应手。','操作能力未经项目验证，第三方署名吻图不能补成作者新的均线定义。')
note('304-b001 304-b002 304-b003 304-b004 305-b001 305-b002 305-b004 305-b005 305-b006 305-b010 305-b011 305-b012 305-b013 305-b014','historical_news_and_stock_context','花旗/中投与美国市场意见、个股红盘/先取本、深圳PE出差、主动震荡、530与600319自述、别追高须恐怖期过和周末幅度预测。','不外核匿名资金、政策及个股表现，不等同项目推荐或保证；等分型/不破线段的技术对象另抽。')
note('306-b002 306-b003 306-b004 306-b005 306-b006 306-b009 306-b010 306-b014 307-b000 307-b001 307-b002 307-b003 307-b004 307-b005 307-b011 307-b014','historical_four-fates_and_self-knowledge','会议安排、5209未站与情绪平复、拐杖及信心，四种技术/心态组合对应年度命运，日线级别两年多、自我能量与语言精确自述。','所有四类完整阅读，非实测群体收益/心理因果；日线级别的说法不等同周日K周期，不能认证语言从不出错。')
note('308-b004 308-b005 308-b006 308-b007 308-b008 308-b009','historical_channel_and_market-camp_rhetoric','通道节省能量/成本、飞腾后挖井，自称不属多空但支持多头赚面包及青蛙粥语言。','操控效率和成本无独立成交验证；署名非多空的思想方法另抽，不补实际操盘行动。')
note('309-b003 309-b004 309-b005 309-b006 309-b007 310-b000 310-b002 310-b003 310-b005','historical_policy_stock_and_risk_rhetoric','期货抢闸失败自述、资金刀光剑影、A股愿望与石油酒话数字可改、勿追高、级别节奏、年度板块机会和政策三愿望。','不认证实际人事审批、资金阻击或绝对收益；酒桌数字不能发布必达目标，政策愿望不是现行事实。')

relations={
 'lower-l092-c-stage-axis-and-secondary-midpoints':[('中枢震荡监视器','震荡中轴','defines')],
 'lower-l092-c-stage-relative-strength-and-monitor-curve':[('中枢震荡监视器','中枢震荡','related')],
 'lower-l092-c-stage-boundary-cross-not-sufficient':[('中枢震荡监视器','第三类买卖点','qualifies')],
 'lower-l092-c-stage-boll-timing-combination':[('中枢震荡监视器','布林通道','related')],
 'lower-l093-c-stage-weekly-state-corresponding-small-uptrend':[('表里关系','走势类型','related')],
 'lower-l093-c-stage-resumed-up-compare-strength-and-nesting':[('笔状态','区间套','related')],
 'lower-l093-c-stage-skilled-sell-first-no-rebuy-down-state':[('操作策略','操作熟练程度','requires')],
}
for r in rows:r['relations']=[{'source':s,'target':t,'type':kind} for s,t,kind in relations.get(r['id'],[])]
by_passage=defaultdict(list)
for r in rows:
    for e in r['evidence']:by_passage[e['passage_id']].append(r)
for item in pending:
    item['lesson_numbers']=sorted({int(passages[x]['unit_id'].split('-')[1]) for x in item['passage_ids']})
    if item['id'].endswith('figure-makers-and-late'):
        item['lesson_numbers']=[92,93];item['figure_ids']=[f['id'] for f in figures]
ledger=[]
for passage_id,p in passages.items():
    linked=by_passage[passage_id];decision=notes.get(passage_id);retained_ids=retained.get(passage_id,[])
    if linked:
        result='new_claim';reading='；'.join(r['text'] for r in linked)
        atomic=[{'claim_id':r['id'],'conditions':r['conditions'],'exceptions':r['exceptions']} for r in linked]
        inverse='；'.join(r['review_note'] for r in linked)
    elif decision:
        result=decision['category'];reading=decision['reading'];atomic=[];inverse=decision['inverse']
    elif p['role']=='reader':
        result='reader_context';reading='已读提问、署名及引述，限定作者回复对象。';atomic=[];inverse='读者成绩及观点不因作者赞赏而转为作者证据。'
    elif (p['role']=='unknown' and p['text'] in ('缠中说禅回复:','缠中说禅回复：')) or p['text'].startswith('教你炒股票') or re.fullmatch(r'(?:缠中说禅(?:解盘)?[:：]?)?\d{4}-\d{2}-\d{2}.*',p['text']) or re.fullmatch(r'.+\(200[78]-\d{2}-\d{2}\d{2}:\d{2}:\d{2}\)',p['text']) or set(p['text'])=={'*'}:
        result='source_header';reading='文章标题、作者时间或分隔已核。';atomic=[];inverse='只定位原文，不独立支持结论。'
    else:raise AssertionError(('unaccounted paragraph',passage_id,p['text']))
    if linked and decision:reading+='；其余语境：'+decision['reading'];inverse+='；'+decision['inverse']
    ledger.append({'passage_id':passage_id,'lesson_number':int(p['unit_id'].split('-')[1]),'document_id':DOC,'pdf_page':p['pdf_page'],
      'role':p['role'],'speaker':p['speaker'],'published_at':p['published_at'],'source_text_sha256':hashlib.sha256(p['text'].encode()).hexdigest(),
      'result':result,'claim_ids':[r['id'] for r in linked],'related_existing_claim_ids':retained_ids,'existing_evidence_not_mutated':True,
      'pending_issue_ids':[x['id'] for x in pending if passage_id in x['passage_ids']],'reviewer':REVIEWER,
      'rounds':{'1_read_and_scope':reading,'2_atomic_conditions':atomic,'3_normalization':{'concept_labels':sorted({x for r in linked for x in r['concepts']}),
      'related_existing_claim_ids':retained_ids,'note':'92课Zn是次级震荡中点，不同20课Z走势段及88课周线编号；必要非充分与经验概率分开，93课按能力和具体走势对应处理。'},'4_reverse_check':inverse}})
for f in figures:
    key=(f['pdf_page'],int(f['id'].rsplit('fig',1)[1]))
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=figure_notes[key],
      figure_source_review='八图后加见stage-c-l092-l093-figure-applied.json，余四图制作人未核；第三方吻图不独立升级作者正文。',
      linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger)==229 and len({x['passage_id'] for x in ledger})==229
def dump(suffix,data):
    (OUT/f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x,ensure_ascii=False,separators=(',',':')) for x in data)+'\n',encoding='utf-8')
dump('reviewed.jsonl',rows);dump('coverage.jsonl',ledger);dump('pending.jsonl',pending);dump('figures.jsonl',figures)
summary={'stage':'C','schema_version':metadata['schema_version'],'graph_version':metadata['graph_version'],'lessons':[92,93],'document_id':DOC,'reviewer':REVIEWER,
 'passages_read':229,'claims':len(rows),'evidence':sum(len(r['evidence']) for r in rows),'importance_counts':dict(Counter(r['importance_level'] for r in rows)),
 'new_concepts':sorted({x for r in rows for x in r['concepts']}-set(concepts)),
 'whole_lesson_semantic_read_complete':True,'technical_extraction_complete':False,'four_round_review':True,'independent_review_claimed':False,
 'visual_pdf_pages':list(range(290,311)),'figure_objects_viewed':12,'figure_origin_counts':dict(Counter(f['origin_status'] for f in figures)),
 'pending':[x['id'] for x in pending],
 'source_passages_snapshot_sha256':SOURCE_SHA,'retained_source_links_in_ledger_only':True,'database_mode':'ro','formal_import':False,
 'acceptance':'229段四轮审读、21页12图检查；监视器必要/非充分边界、状态操作能力及历史条件分开，八图后加，增量待预检发布。'}
(OUT/f'{BASE}.summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
db.close();sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(summary,ensure_ascii=False))
