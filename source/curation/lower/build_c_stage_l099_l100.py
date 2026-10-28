"""Materialize the manually read lower 99-100 batch; SQLite is read-only.

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
BASE='c_stage_l099_l100'
REVIEWER='Codex 主代理 / 阶段C下册99—100课同模型四轮复核'
SOURCE_SHA='ce0c1d8505ddca0a461f65494dc80e46f366ee7d456b7614bf218c8f675ee095'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
db.row_factory=sqlite3.Row
metadata={r['key']:json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version']=='1.1.0'
assert hashlib.sha256((KB/'sources/volume_2.pdf').read_bytes()).hexdigest()=='5332cd1b60381c47ceb81358db6bbb47882efd074fc5c869dcc3002aaed1b5c0'
passages={r['id']:dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id BETWEEN 'lesson-099' AND 'lesson-100' ORDER BY pdf_page,block_index,id")}
assert len(passages)==155
assert hashlib.sha256(json.dumps(sorted(passages.values(),key=lambda p:p['id']),ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==SOURCE_SHA
old={r['id']:dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts={r['label']:dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical={label:r['label'] for r in concepts.values() for label in [r['label']]+json.loads(r['aliases'])}
figures=[dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 339 AND 352 ORDER BY pdf_page,id',(DOC,))]
assert len(figures)==6
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
 (339,1):'CHYS20091010署名三式整理图，2009后加；d+e+f与f+g+h两重组及九段框以正文独立支持，图非作者唯一证明',
 (340,1):'光标2/19右还有后续日K，大阴线属后期；不能反填2/19的4672笔延伸已确认',
 (344,1):'2/22文旁日图到7月含2566.5，后期；未来下跌不证明当时MACD分类已确定第一支',
 (347,1):'2/26嵌文但五分图到2/27，后期；三卖后背驰与日底雏形须按原日期记录',
 (349,1):'2/27文旁日图到3月3607.3，后期；4331底分型已成与4391未站/笔未确分开',
 (351,1):'3/3嵌文但五分图到3/4，后期；a+A中九段与真三买未出不由后期框线更改'
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
    pending.append({'id':'lower-l099-l100-c-stage-pending-'+slug,'status':'pending','passage_ids':[pid(s) for s in shorts.split()],
                    'description':description,'suggested_action':action,'blocks_full_semantic_extraction_completion':blocker,'reviewer':REVIEWER})




c(99,'intermediate-uncertainty-operate-as-oscillation','338-b012 338-b013','作者把中阴看作走势生长阶段的未确定性，认为可按中枢震荡整理处理，未确定性不妨碍这种操作思路。','中阴阶段|中枢震荡|操作策略',1,'量子化/测不准为作者解释性用语，不作量子物理证明；可按震荡处理不等于使用者无执行风险。')
c(99,'general-not-same-level-partition','338-b014 339-b000','中阴中无法明确的是一般划分，不是同级别划分；线段类上涨背驰后虽先有1分钟中枢，后续整体却不必就是1分钟类型，极端年中枢之间也可线段或缺口连接。','中阴阶段|同级别|走势分解|走势中枢|中枢连接|缺口',1,'首次出现的中枢级别不锁定最终整体走势级别；极端连接为作者理论断言，未独立重建实例。')
c(99,'associativity-absorb-old-last-center','339-b001','连接中枢的走势不一定为完整趋势；作者举a+b+c+d+e+f=a+b+c+(d+e+f)，原线段类上涨末类中枢可并入中阴中枢，最终须拆开旧a至e段而可继续成1分钟上涨。','结合律|走势分解|类中枢|走势中枢|中阴阶段|上涨',1,'保留c+d+e为原末类中枢、f为回调，重组不抹除时间顺序；原文第二类类中枢用字不自行校正。',figs=((339,1),),ambiguity='second_class_class_center_wording')
c(99,'post-divergence-fgh-preserve-old-type','339-b002','若背驰点后f、g、h自身构成1分钟中枢，可分成a+b+c+d+e+(f+g+h)，保留原线段类上涨a至e整体。','结合律|走势分解|走势中枢|类背驰',1,'f+g+h成中枢是明确前提，不能把任意三段直接当中枢；两种分法依后续结构而定。',['f、g、h在背驰点后已构成所述1分钟中枢'],figs=((339,1),))
c(99,'center-first-nine-case-repartition','339-b003','若包括d+e+f后延伸九段再上去，划分须先保证5分钟中枢成立，再依结合律使连接走势形态尽量完整；中枢确立优先。','走势中枢|结合律|走势分解|中枢扩展|线段',1,'九段限本例含d/e/f的已有结构，不是任意九笔/九K或只画框就成5分钟。',['本例包含d+e+f延伸九段后再上行的结构'],figs=((339,1),))
c(99,'completed-type-next-at-least-larger-center','339-b004','作者称连接中枢的走势级别必小于中枢；一个级别走势完成后必面对至少大一级中枢震荡，举5分钟上涨结束后至少30分钟中枢震荡。','中枢连接|级别|完成|中枢震荡|走势类型',1,'完成是结构条件，不是任意一根K收盘或未确认背驰；至少不改成恰好一级，断言不当项目形式证明。',['所述级别走势已经完成'])
c(99,'next-first-center-location-key','339-b005','作者认为后续较大走势级别首个中枢震荡的位置，是诊断行情的关键。','走势中枢|中枢震荡|级别|表里关系',1,'位置而非只有价格涨跌幅；后续类型未确认前不能预定最终走势方向。')
c(99,'healthy-intermediate-in-last-center','340-b000 340-b001','作者称后续较大级别中枢震荡至少落在前走势最后中枢范围，落在最后范围内为正常、健康的中阴。','中阴阶段|走势中枢|中枢震荡|级别',1,'健康仅走势诊断比喻，跨页句子合读；与第24课盘整背驰不一定同回跌要求须分清对象，未推广任意未完成走势。',['第99课前一走势完成后所论较大级别中枢震荡'],ambiguity='return_scope_completed_type_vs_consolidation_divergence')
c(99,'deeper-center-danger-reference','340-b002','若中枢震荡回到原走势文中所称第二甚至更后中枢，作者判该中阴不健康、危险，原最后中枢成为关键指标位置。','中阴阶段|走势中枢|表里关系|确认',1,'第二甚至更后原样保留，不擅自改为按时间第二或倒数第二；具体编号方向待核。',ambiguity='second_or_further_center_reference')
c(99,'danger-relative-downtrend-good-for-longs','340-b003','中阴危险是相对原走势方向说的；原下跌走势的中阴危险，意味着回升力度强，对多头反为好事。','中阴阶段|下跌|反弹|表里关系',1,'不能把危险标签直接等同多头亏损风险或无条件回避，也不据回升力度保证新上涨已成。')
c(99,'daily-fractal-corresponding-center-location','340-b004','作者说日分型出现意味着笔内对应小级别走势里有大中枢，其位置对该分型是否最终真顶或真底极关键。','分型|笔|走势中枢|级别|表里关系',1,'几乎决定不是已充分确认，日K分型不固定对应严格日中枢级别。')
c(99,'feb19-petro-gap-not-center-break','340-b006','2月19日指数围4575震荡后向上偏移，中石油回补缺口；因其大中枢未有效突破，作者只给回补震荡意义，不高估技术评价。','缺口|走势中枢|确认|指数走势背离',1,'补缺口不等中枢已破，CPI为当时消息语境，不自动赋予长期方向。',['2008年2月19日所论指数与中石油'])
c(99,'feb19-minute-type-next-center-4672','340-b007','作者称4431起回升至少为1分钟走势类型，首中枢4575；若上方形成新中枢可续强，最强支在前高4672附近或之上形成。','走势类型|走势中枢|中枢上移|级别|确认',1,'至少1分钟与完整上涨已成不同，第二中枢是条件预期，不由当时一涨确认。',['2008年2月19日4431起回升'])
c(99,'feb19-stroke-fractal-upper-boundary','340-b008 341-b000','4672同时为该底分型范围上沿，4195起能否延伸为笔关键在站稳4672；作者以1月23底未站上1月22高4818说明底构造后仍可能原下笔延伸。','底分型|笔|确认|高低点',1,'本段强调顶底应有不重合部分，不替换81新笔两个联合条件，也不把站价一项视为任意笔完整充分条件。',['2008年2月19日该底分型与4672边界'],figs=((340,1),))
c(99,'feb20-best-five-or-third-sell-worst','341-b005 341-b006','2月20日该1分钟上涨不成，最好转5分钟中枢再谋5分钟上涨，最坏在4575震荡后三卖重探底；4672未站仍震荡。','完全分类|走势中枢|第三类卖点|上涨|确认',1,'最好不是已成5分钟上涨，三卖为最坏条件支，不能只取一支预测。',['2008年2月20日该4575结构'])
c(99,'feb21-five-center-confirmed','342-b007','2月21日作者称4575震荡的5分钟中枢已经确定，随后关键为第三类买卖点。','走势中枢|第三类买卖点|确认|完成',1,'与前日最好转中枢预期区分，已成中枢不保证三买或上涨类型。',['2008年2月21日4575附近结构'])
c(99,'feb21-rotation-no-chasing-skill','342-b011 342-b012','在当时板块持续性较低的行情，作者主张轮动不追已涨板块，关注未启动而有新资金者，势头不对可退出；无轮动能力者按中线板块持有，收益差异仅其示意。','板块轮动|追高|操作熟练程度|资金入场批次|操作策略',2,'500%/50%是作者未核收益说法，不变保证或强迫没能力者频繁换股；新资金不是完整买点。',['2008年2月21日所论板块行情及相应能力'])
c(99,'feb22-three-class-centers-retrace-branches','343-b001','4695起线段类下跌有三类中枢，2月22日下午类底背驰回最后类中枢、至少造1分钟中枢；最坏是新1分钟下跌首中枢，最好三买后至少回第二类中枢。','类中枢|类背驰|走势中枢|第三类买点|完全分类',1,'最小返回已达到与最好支尚未出现分开；类中枢不自动当严格1分钟中枢。',['2008年2月22日4695起该类下跌'])
c(99,'feb22-macd-green-larger-no-divergence-case','343-b003 343-b004 343-b005 343-b006','作者MACD分类第一支为再绿且较前更长、面积更大，对应6124起30分钟下跌不背驰，空间可到2500、处4300中轴下1800范围；当时基本面暂不支持但未排除。','MACD|背驰|下跌|价格区间|完全分类',2,'比较长度与面积联合，2500为条件可能非必达，基本面判断/美国1987愿望非实测概率；指标辅助条件另保留。',['2008年2月22日该MACD及6124起结构','绿柱较前更长且面积更大'])
c(99,'feb22-smaller-green-end-and-month-bottom-not-yet','343-b007 343-b008','第二支再绿但更短、面积更小，作者对应30分钟下跌背驰结束再向上；月底分型尚未出现，2—3月需构造以支持行情。','MACD|背驰|底分型|走势类型|确认',1,'更短与面积更小联合，作者对应分析不替代结构背驰条件；月底尚未出现不能倒填完成。',['2008年2月22日该MACD第二支','再绿比前更短且面积更小'])
c(99,'feb22-no-green-consolidation-divergence-reverse','343-b009 343-b010 344-b000','第三支不再绿而红延长直接上；作者说4195为30分钟中枢盘整背驰，a+A+b+B+c中c不一定存在，可从B直接反转，但通常需基本面支持，直接上冲不有效突破也可能成日下跌首中枢。','盘整背驰|MACD|完全分类|走势中枢|下跌',1,'可无c不表示任意删完成条件，盘整背驰与趋势背驰不同；直接上非一定更强，跨页风险句保留。',['2008年2月22日4195及该第三支'],figs=((344,1),))
c(99,'feb22-two-three-still-market-choice','344-b001','作者在2月22日仍保留第二、三两支，由市场实际选择后再操作。','完全分类|当下|操作策略',1,'当日未定不拿7月后期图补成已知第一支；后续明确筛除才更新案例状态。',['2008年2月22日上述MACD分类'])
c(99,'feb22-thirty-up-large-second-sell-risk','344-b003','作者认为未来30分钟向上最大可能形成大二卖，6124为一卖，后至少回杀成大日中枢，并预言当年多数股票年K收阴。','第二类卖点|第一类卖点|走势预测|走势中枢',2,'最大可能与年度预测是当时主张，不认证后验收益/全年阴线比例；中枢尚未来不可标已完。',['2008年2月22日年度情景展望'])
c(99,'feb22-capability-bench-or-thirty-exit','344-b002 344-b004 345-b001 345-b002','作者按能力给日以下不适应者坐小板凳、能处理30分钟者等待相应向上机会的选择；后者须在顶背驰/二卖处理，并说二卖大调后仍可能再涨，震荡节奏不适应者不强做。','操作级别|操作熟练程度|背驰|第二类卖点|操作策略',1,'能力与未来机会前提保留，退出不意味着永无再涨，0.76至0.64为作者类比案例非项目成交证明。',['第99课所论年度震荡及对应能力'])
c(99,'feb25-policy-force-third-branch-eliminated','345-b005','2月25日作者称政策只是市场分力，走势体现合力；当日新低已排除前述第三支，随后看第二支演化。','市场分力|市场合力|完全分类|确认',1,'特定第三支筛除有明确文字，不能把一次政策无效推广所有政策永远无作用；第一支以后文仍未全排除。',['2008年2月25日该MACD情景'])
c(99,'feb25-sell-on-weak-up-red-case','345-b006','作者在当次反弹说卖在上冲无力、红柱阶段，并指出4695附近5分钟盘整背驰含1分钟盘整背驰区间套，等绿才走会迟。','盘整背驰|区间套|MACD|操作策略',1,'限该结构与上冲无力，不改成任何红柱都卖；消息可提醒但不是背驰定义。',['2008年2月25日回述4695反弹'])
c(99,'feb25-minute-down-formed-two-centers','345-b007','2月25日跌破此前1分钟中枢、早反弹三卖后下跌，下午第二1分钟中枢构造完成，作者据此称4695起至少1分钟下跌。','下跌|走势中枢|第三类卖点|完成|级别',1,'至少不升确切只1分钟；第二中枢完成不等整个下跌已结束。',['2008年2月25日4695起下跌'])
c(99,'feb25-divergence-rebound-five-worst','345-b008','短线机会待该1分钟下跌背驰后反弹构5分钟中枢；若反弹只在当天1分钟中枢内结束，最坏可成5分钟下跌首中枢并进一步下跌。','背驰|中枢扩展|走势中枢|下跌|完全分类',1,'背驰尚待、反弹力度与基本面相关、最坏为条件支，不作反弹必反转。',['2008年2月25日所论1分钟下跌后的反弹'])
c(99,'feb25-stock-selection-conditions-not-any-low-price','345-b010 346-b000','作者偏好离前高有距离、近期强站且持续有量的个股；真正站稳新高且前期未暴炒者也有其所称投机价值。','成交量|确认|多头陷阱|操作策略',2,'三项联合与另一新高支分别保留，吸纳/洗盘是作者经验判断，不保证补跌只是洗盘。',['2008年2月25日个股情景'])

c(100,'multilevel-complete-classification','346-b003 346-b004 346-b006','作者以小说用兵类比谋划，强调完全分类必须多层次：自然形成的不同级别各有分类，合成操作依赖的立体系统。','完全分类|级别|操作策略',1,'小说不是史实/军事专业证据；自然级别是走势结构不是固定K线时间换算。')
c(100,'small-fund-one-layer-large-multilayer','346-b007','小资金可只用一个层次的完全分类，较大资金不合适；作者举30、5、1分钟三层系统，每个当下在各层有对应现实状态。','完全分类|级别|资金管理|当下',1,'小/较大未给金额阈值，三层是举例不是所有人唯一参数或全组合可达证明。')
c(100,'ability-only-quantity-author-general-claim','346-b005','作者一般性地称股票分类谋划基本不超越能力，只是买卖数量多少，不存在某一分类完全不能执行。','完全分类|操作熟练程度|仓位|操作策略',2,'这是作者一般主张；随后又明确处理不了可能三卖者不参与，并许极小仓练习，执行/T+1约束未取消，范围待核。',ambiguity='general_executable_vs_specific_capability_gate')
c(100,'feb25-three-layer-current-states','346-b008','2月25日系统状态为：30分钟下跌最近中枢仍震荡、未三卖则有效；5分钟离首中枢向下移动但三卖未形成，是否下跌不能100%定；1分钟下跌已成。','级别|中枢震荡|第三类卖点|下跌|确认|完全分类',1,'三个对象各自状态不可互借，小级别已成不自动确认大级别下跌。',['2008年2月25日该30/5/1系统'])
c(100,'one-minute-divergence-first-system-change','346-b009','在该三层状态下，作者说最先必发生的变化是1分钟底背驰；它未出现前，另外两层不会有相应状态变化。','背驰|级别|完全分类|表里关系',1,'仅该已知三层结构的状态转换，不能推广一切大图状态变动都必须等待任意1分钟背驰。',['第100课2月25日所列三层状态'])
c(100,'pullback-five-third-sell-or-oscillation','346-b009','1分钟底背驰后回拉若成原5分钟三卖，则确认第二5分钟中枢及5分钟下跌；若不成，则确认原5分钟中枢继续震荡。','背驰|第三类卖点|走势中枢|下跌|中枢震荡|确认',1,'回拉完成与三卖确认前不能预定两支，不能把没看见三卖的一瞬间直接作永久不成。',['第100课所述1分钟底背驰后的回拉'])
c(100,'five-change-not-thirty-change-immediate','346-b010 347-b000','这两种5分钟变化本身不改变30分钟状态；若5分钟下跌以后结束并回拉构30分钟三卖，才会导致30分钟层次改变。','级别|表里关系|第三类卖点|完成|确认',1,'5分钟下跌完成、回拉、30分钟三卖是后续联合链，不把5分钟三卖直接升级30分钟三卖。',['第100课所述5分钟变化及后续链'])
c(100,'capacity-gate-and-tiny-practice','347-b001 347-b002 347-b003 347-b004','应按能承受的各支匹配资金比例和仓位；处理不了可能三卖者不参加，能面对所有支才参加该1分钟背驰，也可用特别小仓位有意识练习。','操作熟练程度|仓位|资金管理|完全分类|操作策略',1,'小仓练习是有意识培养而非无风险/无限补资，未给统一百分比；与前段数量即可执行的一般说法并列待核。',['评估所论机会所有分支和自身承受能力'],ambiguity='general_executable_vs_specific_capability_gate')
c(100,'feb26-third-sell-then-bottom-divergence','347-b007 348-b000','2月26日作者称午后开盘出现三卖，再破底后2:30形成最后底背驰，作为前日所述1分钟底背驰机会。','第三类卖点|背驰|确认|下跌',1,'三卖在前、背驰在后与日底分型仍雏形分开，不用次日图补当日全天路径。',['2008年2月26日该分钟下跌'],figs=((347,1),))
c(100,'feb26-retrace-minimum-fractal-only-prototype','348-b001','1分钟背驰最低回升为最后中枢；日底仅雏形，次日不破底且高于当日高点才成立，之后还须看能否延伸为笔。','背驰|走势中枢|底分型|笔|确认',1,'两个次日条件联合，雏形/成立/延伸为笔三层不可压缩；最低幅度不保证后续反转。',['2008年2月26日该日底及1分钟背驰'])
c(100,'feb27-fractal-formed-stroke-upper-4391','348-b005 348-b006','2月27日未新低并过4331使底分型成立，但未直接过整体上沿4391，仍非最强；延伸为笔关键须站住4391，4818/4672前例同理。','底分型|笔|确认|高低点',1,'4331成底与4391笔边界是不同对象，不能并价或当底已成等于笔已成；不替代81新笔完整条件。',['2008年2月27日该底分型'],figs=((349,1),))
c(100,'feb27-second-branch-first-not-excluded','348-b007 348-b008 348-b010 348-b011','2月27日作者按第二中线支观察，但第一支仍不能完全排除；绿缩后再红更大是最好，绿再长或少红再绿则继续底部震荡。','MACD|完全分类|中枢震荡|确认',1,'选择第二不自动删除第一；最佳形态未发生不标已确认，指标比较仍结合结构。',['2008年2月27日该MACD分类'])
c(100,'macd-zero-necessary-wording-scope','348-b009','作者在该分析中断言所有真正行情展开都需MACD黄白线回零轴、站零轴后展开。','MACD|技术分析|确认',2,'该必要用语与17课指标非必要、同篇348-b013说并非特殊且懂理论无需指标并列；没有明确全局撤回，范围待核。',['第100课2月27日这段分析语境'],ambiguity='macd_necessary_wording_vs_auxiliary_scope')
c(100,'feb27-neckline-zero-joint-conditions','348-b012','当时中线颈线4700上下，作者设MACD黄白回零轴同时指数回颈线并最终站稳为突破情景，需多方配合；颈线未有效破前仍按30分钟震荡。','MACD|颈线|确认|中枢震荡|完全分类',1,'零轴/颈线同时与站稳、多方配合联合，突破不可避免是作者条件断言，非当时已成或保证时价。',['2008年2月27日4700附近颈线情景','黄白线回零轴同时指数回颈线且最终站稳'])
c(100,'macd-visual-auxiliary-not-special','348-b013','作者解释用MACD是人人可见且直观，并非指标特殊，理解其理论后这些描述完全没必要。','MACD|技术分析|走势分解',1,'同文必要说法范围待核，辅助描述不直接等背驰/三类点，更不能以此删结构条件。',ambiguity='macd_necessary_wording_vs_auxiliary_scope')
c(100,'feb27-one-minute-type-up-or-consolidation','348-b015 349-b000 349-b001','该回升无论是否成5分钟三卖都对应1分钟类型，尚待确定盘整还是上涨；4331首1分钟中枢已成，若三买则成上涨并回原5分钟震荡的几率极大。','走势类型|盘整|上涨|第三类卖点|第三类买点|确认',1,'方向回升不等上涨类型；三买条件和极大概率不升100%保证，不由后期图反填。',['2008年2月27日4331附近回升'])
c(100,'feb27-half-exit-or-hold-or-skilled-swap','349-b002 349-b003 349-b004','该线段类背驰后可随1分钟中枢演化决定；胆小者可先出一半避免满仓震荡，心态好者可持，技术更高者可换股，须先懂基本分析和操作。','类背驰|仓位|操作熟练程度|板块轮动|操作策略',1,'一半为该人群案例非统一仓位命令，换股更高要求不能抹掉持有或减半分支。',['2008年2月27日所论背驰后1分钟中枢'])
c(100,'feb28-no-third-sell-still-oscillation','350-b001 350-b003 350-b005','2月28日该1分钟三卖未出仍震荡，4391未站仍有探底压力；操作上冲无力减，回跌且震荡依旧才回补。','第三类卖点|中枢震荡|确认|操作策略',1,'回补须震荡依旧，不把任意下跌或中枢下移也机械买回。',['2008年2月28日该分钟震荡'])
c(100,'feb29-red-after-entanglement-not-certain','350-b008 350-b009','2月29日黄白线两次缠绕再红，作者认为一般将回零轴并上攻，但明确骗线仍可能，并列外围大跌、新增发压力或利好传闻落空等不稳定因素。','MACD|市场陷阱|政策风险|概率原则',1,'10次不到1次仅作者未核频率，不作胜率；具备技术条件不等所有外部条件已满足。',['2008年2月29日该指标形态'],exceptions=['骗线仍可能','所述突发外部下跌、增发或利好传闻落空'])
c(100,'feb29-4331-five-center-4391-boundary','350-b010 350-b011','2月29日4331震荡已延伸5分钟，按理论观察其三类点，其他按震荡处理；4391仍须有效突破站稳才能延伸为笔。','中枢扩展|走势中枢|第三类买卖点|笔|确认',1,'5分钟中枢已成与笔仍待4391两个状态分开，不把红柱代替笔/三类点确认。',['2008年2月29日该4331及4391结构'])
c(100,'mar3-a-plus-a-nine-segments-no-third-buy','351-b002','3月3日作者把早回跌作为5分钟中枢最后线段，a+A中a可作线段盘整分解、A为九线段基本形式；真正三买尚未出现，仍可能回该中枢。','走势分解|线段|盘整|走势中枢|第三类买点',1,'九是该例A的基本形式，不任意九线段即成；突破4391也不替真正三买。',['2008年3月3日所论a+A结构'],figs=((351,1),))
c(100,'mar3-week-fractal-4391-stroke-4695','351-b005','3月3日突破4391后作者称周底分型已现，但延伸为笔须有效突破4695。','底分型|笔|确认|周期K线图',1,'周底已现与周笔未确认分开，日笔边界4391不能替周笔4695。',['2008年3月3日该周底分型'])
c(100,'mar3-zero-and-4695-fundamental-conditions','351-b003 351-b004 351-b006 351-b007','作者把站零轴、突破4695且有效站稳作为行情展开条件，仍须基本面无重大变化，并防外围继续大跌或平安增发影响4391站稳。','MACD|确认|政策风险|完全分类',1,'价格/指标/基本面联合不压为单一零轴信号；具体公司/消息影响为当时作者判断未外核。',['2008年3月3日该情景','MACD站零轴且4695有效突破站稳','基本面无重大变化'])
c(100,'mar4-return-center-third-buy-absent','352-b002','作者3月4日回述因真正三买未出，技术仍可回4331中枢，当日已转向回中枢；将触发消息归于深发展增发传闻。','第三类买点|走势中枢|中枢震荡|确认',1,'技术可回与新闻因果分开，实际返回有当日文字才登记，不用前日后期图宣布已知。',['2008年3月4日4331结构'])
c(100,'mar4-low-price-slogan-author-selection','352-b010 352-b011','3月4日作者以7—8元金、12—13元银、20以上垃圾作选股口号，认为大牛股基本个位数起步，并以600737和600635历史提及时价格说明。','价格区间|题材股|操作策略',3,'历史口号和经验不是内在价值/确定涨幅或当前买入推荐，送股前后价格不混同，不能只按绝对低价忽略结构风险。',['2008年3月4日作者所述选股思路'])
c(100,'cost-reduction-30-percent-as-goal-not-guarantee','346-b001 352-b009','作者说底部需反复震荡，可利用节奏降成本，并以启动时成本先降30%为理想状态；3月4日题材股回补也限其所论背景。','成本|中枢震荡|操作熟练程度|操作策略',2,'30%是作者理想示例，非任何人可保证达成；指数下跌不保证所有题材都只是洗盘。',['所述年度题材股与底部震荡背景'])

keep('338-b013 339-b000','lower-l088-c-stage-stage-shape-not-new-type lower-l089-c-stage-outcome-current-force-not-preset','中阴可按震荡操作不等最终新走势必盘整或必固定1分钟，最终仍由当下合力选择。')
keep('339-b000 339-b003','upper-l019-c-stage-gap-not-center-lowest-connection lower-l070-c-stage-associativity-connects','缺口可为连接，结合律须保证结构，不能据连接很小预定整体级别。')
keep('339-b004 340-b000','lower-l071-c-stage-trend-end-divergence-retrace upper-l024-c-stage-standard-divergence-retrace-b-center lower-l098-c-stage-divergence-return-then-classify','99强调走势完成后高一级中枢，与24盘整背驰不必同回跌要求、98较宽概括的对象范围并列，不自动撤回。')
keep('340-b008 348-b006','lower-l081-c-stage-new-stroke-two-joint-conditions','本例站分型上沿是关键观察，不代替81包含处理不共K及极值K之间至少3根两个联合条件。')
keep('343-b004 343-b007 348-b009 348-b013','upper-l017-c-stage-indicators-auxiliary-not-necessary lower-l096-c-stage-macd-assists-not-equals-divergence lower-l098-c-stage-feb18-indicators-imprecise-center-primary','MACD描述为直观辅助，必要零轴断言有范围待核，不以日期自动撤回指标非必要或直接等背驰。')
keep('344-b004 347-b002','lower-l098-c-stage-feb14-bench-capability-at-least-thirty lower-l096-c-stage-jan28-unskilled-worst-case-capability-gate','小板凳按能力/级别假设，处理不了最坏支不参与，不能被100一般数量说法覆盖。')
keep('345-b008 348-b001','lower-l089-c-stage-higher-must-five-center','1分钟下跌背驰后更大结构与最低回拉范围是不同层次，均随当例条件保留。')

issue('intermediate-partition-recomposition','338-b014 339-b000 339-b001 339-b002 339-b003','一般划分与同级别划分不同；d+e+f合组可拆旧类上涨，f+g+h可保留；原文第二类类中枢用字和九段推广范围未完整形式化。','保留两式及各自成中枢前提，中枢确立优先，不自动把任意三段/九段框当合法中枢。',True)
issue('completed-type-return-cross-lesson','339-b004 340-b000 340-b001','99走势完成后至少高一级中枢及回原末中枢，与24盘整背驰三买支可能不回、98无论盘整背驰都回原中枢的概括有对象范围问题。','并列明确原句，区分已完成类型与盘整背驰，不静默删除旧条件；98命题需补跨课歧义标记。',True)
issue('health-center-number-relative-direction','340-b002 340-b003 340-b004','第二甚至更后中枢的计数方向未明；危险相对原走势，对原下跌的回升可能有利，分型对应中枢位置未给精确确认算法。','原文措辞照留，不擅改倒数第二或把危险统一当多头风险/医学诊断。',True)
issue('macd-necessary-vs-auxiliary','343-b004 343-b007 348-b009 348-b012 348-b013 350-b008','绿柱长短/面积分类与所有真正行情需MACD0轴的措辞，同篇直观非特殊/懂理论无需及17非必要存在范围差异。','把历史指标案例和一般必要句分别保留歧义，不让单一指标取代结构或宣称胜率/无条件反转。',True)
issue('general-executability-and-capability','346-b005 346-b007 347-b001 347-b002 347-b003 347-b004','100先称不存在分类不能执行、只多少数量，后又说处理不了可能三卖者不要参与，极小仓练习为另一途径；T+1仍约束。','并列一般/具体/练习范围，不解读成任意人任意交易都可安全执行，也不补统一金额/仓位。',True)
issue('fractal-stroke-level-confirmation','340-b008 348-b001 348-b005 348-b006 349-b001 350-b010 351-b002 351-b005','日底雏形/成立/日笔上沿4331与4391、周底4391与周笔4695、1/5分钟中枢与真三买未出不可混同，站价还非完整笔条件。','按日期级别保留，继续核原图但不拿未来图补确认，81新笔两个联合条件不删。',True)
issue('historical-returns-fundamental-causality','342-b012 343-b005 343-b006 344-b003 344-b004 345-b005 345-b006 350-b008 350-b009 352-b010 352-b011','500%/50%、年阴线、2500、骗线不到十分之一及低价牛股口号，连同融资/政策因果均为作者历史判断或修辞，未独立验证。','保留条件和归属，不发布实际收益、统计频率或当前推荐；砸锅卖铁等比喻不执行。')
issue('figure-makers-and-late','339-b001 340-b008 343-b010 347-b007 348-b005 351-b002','六图均已看且后加：CHYS20091010、日图文后K线、7月/3月未来与次日五分截图。','图源明确后加但制作身份未核，正文独立支持，不能用未来走势证明当时分支/笔/三类点已确认。')

note('338-b012','uncertainty-metaphor-context','作者把中阴与量子化测不准作解释性比喻。','不作为量子物理或数学随机模型证据，不自行添加量子算法。')
note('341-b001 341-b003 341-b004 341-b007 341-b008 341-b009 341-b010 342-b006 342-b008 342-b009 342-b010 342-b013','historical-sector-and-news-context','CPI/增发足球比喻、板块点火和消费品题材、中线三月预言、580989风险与震荡、元宵安排。','作者历史消息/板块/收益未核，不转当前投资建议；一般人权证勿参与的限制保留在上下文。')
note('341-b012 341-b013 342-b000 342-b001 342-b002 342-b003 342-b004','historical-capital-ecology-opinion','资本市场生态、资源合理开发、引导时效和利益关系的评论已完整跨页阅读。','是作者宏观政策立场，不当生态科学结论、现行监管规定或未证实利益指控事实。')
note('343-b002 344-b005 345-b000 345-b004 345-b009','historical-market-and-policy-context','MACD三支引言、期货/题材/重组展望、新基金增发意见、印花税与政策期待。','情境观点未外核，真正技术分支另抽，不认证当时制度因果或当前政策。')
note('347-b006 348-b002 348-b003 348-b014 349-b005 349-b007 350-b000 350-b002 350-b004 350-b006','historical-policy-and-capability-context','救市发言/融资压力、政策干货与震荡、补课、板块轮动、红柱关键日、浦发和印花税传闻。','不发布具体企业未证实指控或现行税率，练习批评不认证交易能力；具体无力退出及三类点条件另抽。')
note('350-b012 350-b013 351-b001 351-b008 351-b009 352-b000 352-b003 352-b004 352-b005 352-b006 352-b007 352-b008 352-b012','historical-stock-and-financing-rhetoric','黄金1000、板块/填权、爆发面包、3/3基本面支持与个股新高、增发金融股与砸死/8228及送钱口号。','全文已读；匿名资金/融资因果与收益未外核，不执行市场行动或用口号替买卖点和风险条件。')

relations={
 'lower-l099-c-stage-intermediate-uncertainty-operate-as-oscillation':[('中阴阶段','中枢震荡','related')],
 'lower-l099-c-stage-center-first-nine-case-repartition':[('结合律','走势分解','qualifies')],
 'lower-l099-c-stage-next-first-center-location-key':[('表里关系','走势中枢','related')],
 'lower-l100-c-stage-multilevel-complete-classification':[('完全分类','级别','related')],
 'lower-l100-c-stage-capacity-gate-and-tiny-practice':[('仓位','操作熟练程度','requires')],
}
for r in rows:r['relations']=[{'source':s,'target':t,'type':kind} for s,t,kind in relations.get(r['id'],[])]
by_passage=defaultdict(list)
for r in rows:
    for e in r['evidence']:by_passage[e['passage_id']].append(r)
for item in pending:
    item['lesson_numbers']=sorted({int(passages[x]['unit_id'].split('-')[1]) for x in item['passage_ids']})
    if item['id'].endswith('figure-makers-and-late'):
        item['lesson_numbers']=[99,100];item['figure_ids']=[f['id'] for f in figures]
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
      'related_existing_claim_ids':retained_ids,'note':'中阴一般划分与同级别划分分开，中枢先确立再结合律重组；30/5/1状态各自确认，指标案例不自动撤销辅助而非必要的旧原话。'},'4_reverse_check':inverse}})
for f in figures:
    key=(f['pdf_page'],int(f['id'].rsplit('fig',1)[1]))
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=figure_notes[key],
      figure_source_review='六图均后加见stage-c-l099-l100-figure-applied.json；2009整理图与文后行情不作原作者观点唯一证明，也不倒填确认。',
      linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger)==155 and len({x['passage_id'] for x in ledger})==155
def dump(suffix,data):
    (OUT/f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x,ensure_ascii=False,separators=(',',':')) for x in data)+'\n',encoding='utf-8')
dump('reviewed.jsonl',rows);dump('coverage.jsonl',ledger);dump('pending.jsonl',pending);dump('figures.jsonl',figures)
summary={'stage':'C','schema_version':metadata['schema_version'],'graph_version':metadata['graph_version'],'lessons':[99,100],'document_id':DOC,'reviewer':REVIEWER,
 'passages_read':155,'claims':len(rows),'evidence':sum(len(r['evidence']) for r in rows),'importance_counts':dict(Counter(r['importance_level'] for r in rows)),
 'new_concepts':sorted({x for r in rows for x in r['concepts']}-set(concepts)),
 'whole_lesson_semantic_read_complete':True,'technical_extraction_complete':False,'four_round_review':True,'independent_review_claimed':False,
 'visual_pdf_pages':list(range(338,353)),'figure_objects_viewed':6,'figure_origin_counts':dict(Counter(f['origin_status'] for f in figures)),
 'pending':[x['id'] for x in pending],
 'source_passages_snapshot_sha256':SOURCE_SHA,'retained_source_links_in_ledger_only':True,'database_mode':'ro','formal_import':False,
 'acceptance':'155段四轮审读、15页6图检查；中阴重组、后续高一级结构、相对危险和多层状态/能力条件分别保留，六图后加，增量待预检发布。'}
(OUT/f'{BASE}.summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
db.close();sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(summary,ensure_ascii=False))
