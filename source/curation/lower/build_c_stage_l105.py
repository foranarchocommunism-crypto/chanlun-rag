"""Materialize the manually read lower 105 batch; SQLite is read-only.

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
BASE='c_stage_l105'
REVIEWER='Codex 主代理 / 阶段C下册105课同模型四轮复核'
SOURCE_SHA='0f4be61026cd0a42a0d56c3c328da5fdf4448525c41a1020f08c82aa2cfb28be'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
db.row_factory=sqlite3.Row
metadata={r['key']:json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version']=='1.1.0'
assert hashlib.sha256((KB/'sources/volume_2.pdf').read_bytes()).hexdigest()=='5332cd1b60381c47ceb81358db6bbb47882efd074fc5c869dcc3002aaed1b5c0'
passages={r['id']:dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id='lesson-105' ORDER BY pdf_page,block_index,id")}
assert len(passages)==181
assert hashlib.sha256(json.dumps(sorted(passages.values(),key=lambda p:p['id']),ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==SOURCE_SHA
old={r['id']:dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts={r['label']:dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical={label:r['label'] for r in concepts.values() for label in [r['label']]+json.loads(r['aliases'])}
figures=[dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 383 AND 401 ORDER BY pdf_page,id',(DOC,))]
assert len(figures)==11
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

figure_notes={(f['pdf_page'],int(f['id'].rsplit('fig',1)[1])):f['note'] for f in figures}

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
    pending.append({'id':'lower-l105-c-stage-pending-'+slug,'status':'pending','passage_ids':[pid(s) for s in shorts.split()],
                    'description':description,'suggested_action':action,'blocks_full_semantic_extraction_completion':blocker,'reviewer':REVIEWER})




c(105,'mechanical-follow-structural-joints','382-b003','作者以目无全牛、合其关节比喻机械化操作：按其理论把市场结构分解，逐步顺着各个结构关节的节奏操作，避免被全貌繁复影响。','机械化操作|走势分解|操作策略',1,'机械化在此是按结构与节奏行动，不直接等同电脑自动交易；两张未署名流程图的全部箭头及仓位旁注不自动作为作者程序。',figs=((383,1),(384,1)))
c(105,'classification-choice-must-be-complete','382-b004','作者说具体分解标准或分类原则并非关键，关键是这种分类能够导致完全分类。','机械化操作|完全分类|走势分解',1,'能导致完全分类是必要约束，不是任意有遗漏/交叠规则都合格；未给所有替代标准的完备性证明。',['所选分类确实能导致完全分类'],ambiguity='alternative_classification_completeness_not_proven')
c(105,'mechanical-not-predict-full-market','382-b005','作者说明其机械化思路关注关节节奏，不爱争论全市场道理，也不爱预测。','机械化操作|走势预测|当下|操作策略',2,'只挣钱为作者修辞，不报告实际收益；后附行情分析含预测，不能把这一态度删改成作者从未做预测。')
c(105,'fractal-stroke-simple-demonstration','382-b007','作者说近期解盘以分型及能否延伸为笔这一基本标准进行分类，作为应对当时震荡行情的示范。','分型|笔|完全分类|中枢震荡|操作策略',1,'作者说完全可处理是教学评价，不替代分型/包含/新笔联合定义，也不证明任意行情只用单价规则足够。',['第105课所论近期震荡行情'])
c(105,'master-simple-classification-before-more','383-b001','作者要求先熟练把握分型这一简单分类导致的操作，再谈继续学其他方法。','分型|操作熟练程度|操作策略',2,'是学习次序建议，未给可量化熟练阈值，不以此认证某人交易能力。')
c(105,'apr14-bench-or-sprint-by-capability','384-b001 385-b000 385-b001 385-b006','作者对当时行情给小板凳等待与短跑两种选择，解盘练短跑以读者具有相应水平为假设；短跑不应变成长跑。','操作熟练程度|操作策略',1,'能力假设和持有节奏限制不能省，不能因课程示范而默认所有人都能承受短线。',['2008年4月14日所论行情','具备相应短线水平才选择短跑'])
c(105,'apr14-3533-and-three-gap-failures','385-b002','4月14日作者以3533未站、早盘连续三次冲高未补缺口解释再探底风险。','确认|缺口|操作策略',2,'三次为当日记录，不推广任何三冲失败的普适定律；3533仍是当时对象。',['2008年4月14日该3533与缺口'])
c(105,'apr14-property-second-buy-or-new-down','385-b004','作者把地产以及金融此轮下跌是二买清洗还是新一轮下跌，作为指数中线的重要观察分支。','第二类买点|下跌|完全分类|板块轮动',1,'没有当时确定就是二买；地产此前多头陷阱与后来新买点须分开确认。',['2008年4月14日地产/金融所论结构'])
c(105,'apr15-three-bars-fourth-break-3311','385-b009','4月15日作者称四根60分钟K线中，前三根构造分型并确认后，第四根突破其上沿，3311成为短线关键。','底分型|周期K线图|笔|确认',2,'是该四K实例，不将第四K突破单项等同所有笔已完成；图到4/16为后加，不倒填次日回试。',['2008年4月15日该60分钟图四K'],figs=((385,1),))
c(105,'apr15-3311-retest-condition','385-b010','作者说该反弹能否继续取决于回试3311能否站住，站住继续，否则结束。','确认|完全分类|操作策略',2,'回试有效站住而非瞬间触价，单日反弹结束不等整个大级别调整结束。',['2008年4月15日该3311反弹'])
c(105,'apr16-half-position-range-break-rule','386-b003','围关键位震荡未定方向时，可等三卖再走，也可高位盘整背驰抛、下来不破位回补；作者明确后一法必然半仓，若真破位则不回补并抛掉余下半仓。','仓位|中枢震荡|盘整背驰|第三类卖点|操作策略',1,'半仓限本段这一震荡短差法，不套到所有主动买套或资金类型；不破位与真破不回补两支必须保留。',['2008年4月16日围关键位震荡未决方向的情景'])
c(105,'apr16-exit-high-reenter-confirmed-third-buy','386-b004','另一法是震荡高位先退出，等真正重新站住关键位置、出现三买再介入，避免预测最终能否站住。','第三类买点|确认|操作策略|中枢震荡',1,'真正站住及三买为联合条件；最安全有效是作者比较用语，不表示无交易风险。',['2008年4月16日该关键位震荡'])
c(105,'apr17-3311-fails-short-vs-medium','386-b008 386-b010','4月17日作者说3311未站后破底，同时又有新短线机会；中线仍等基本面明朗，不把短线反复当中线已确认。','确认|政策风险|操作策略|完全分类',2,'机会与能力/图形条件同读，不把任何新低都视作充分买点。',['2008年4月17日该3311结构'])
c(105,'apr18-no-sixty-bottom-yet','386-b013','4月18日60分钟底分型尚未构造出来，作者要求继续看图等待短线出击时间。','底分型|周期K线图|确认',2,'后期图和后来反弹不补写当日底分型已成。',['2008年4月18日该60分钟图'])
c(105,'apr18-platform-strength-or-trap-two-paths','386-b015 387-b000 387-b001','作者对3424附近弱市震荡给两支：逐步震荡走强再上破，或先狠跌造空头陷阱、快速回拉平台蓄势；两支都以该平台为后续基准。','中枢震荡|空头陷阱|完全分类|确认',2,'是当时展望，不证明所有后续下跌必为陷阱或必回平台；跨页续文齐全。',['2008年4月18日所论3424附近平台'],figs=((387,1),))
c(105,'apr18-three-rebound-strengths-not-chart-periods','387-b002','作者以4778至5524为第一级别力度、4196至4695为第二级别力度，列未来三种逐强反弹：第二级别、第一、第一级别以上力度。','级别|反弹|完全分类|价格区间',1,'本段级别直接说明历史反弹力度，不擅自指定严格1/5/30分钟级别；5524/4196照正文，不用前文5522或图5522.8/4195.8改字。',['2008年4月18日以这两次反弹力度为参照'],figs=((387,1),),ambiguity='rebound_strength_grade_vs_structural_level_and_price_rounding')
c(105,'apr18-weak-first-rebound-new-low-conditional','387-b003 387-b004 388-b004','作者认为若当时基本面继续，先有最弱反弹再新低至2500—2700甚至更低、之后才较大反弹的可能性大；第三种当时可能性不大，第二种仍有。','反弹|完全分类|政策风险|价格区间',2,'是作者条件预测，不是现行政策事实、理论唯一走势或已验证概率；历史深圳需两年类比不设所有市场固定一年等待。',['2008年4月18日该基本面继续的展望'])
c(105,'forecast-not-market-no-hundred-percent','388-b002 388-b005','作者承认历史对照未必完全成立，分析涉及预测、没有100%准确可能；实际操作应据市场最终选择，不能把分析预测当市场走势本身。','走势预测|当下|操作策略',1,'即使同篇用强烈预测措辞，也保留此限制，不把历史类比当未来充分证明。')
c(105,'apr21-3189-small-fractal-not-confirmed','388-b012','4月21日作者说有小底分型，能否成立还看3189。','底分型|确认|周期K线图',2,'有形态与成立尚待分别保留；不得自动把次日3085当该价笔误或已确认同一分型。',['2008年4月21日该小底分型'])
c(105,'apr22-3085-fractal-confirmed-stroke-pending','389-b002 389-b003','4月22日3085突破确认60分钟小底分型成立，后续仍看回试能否站住最终成向上笔；短线看3085，中线看3305。','底分型|笔|确认|周期K线图',1,'分型成立不等笔已成，3085/3305各自对象分开，后加图不把4/23回试反填。',['2008年4月22日该60分钟分型'],figs=((389,1),))
c(105,'apr23-3085-retest-3305-still-boundary','389-b007 389-b008','4月23日作者记录早盘3085回试已确认，尾盘仍在3305前；突破3305行情性质升级，不破则震荡。','确认|完全分类|中枢震荡',2,'性质升级为本例说法，不直接等严格中枢级别递归升级；原日边界未由未来图决定。',['2008年4月23日该3085/3305结构'])
c(105,'apr24-leading-sectors-after-broad-rise','390-b003 390-b005 390-b006','作者说普涨后的健康延续关键在分化及领涨板块继续走强，观察领涨之间轮动与向二三线蔓延节奏。','板块轮动|确认|操作策略',2,'该次大头/题材次序为历史判断，不据此建立全时期固定行业轮动模型。',['2008年4月24日该次普涨后情景'])
c(105,'apr24-25-3656-oscillation-third-sell-risk','390-b007 390-b009 390-b010','4月24日给3656站住续上、否则震荡；25日其处受阻跳水后作者按震荡处理，若平台最终只出三卖，仍可能再次探底。','确认|第三类卖点|中枢震荡|完全分类',2,'已受阻与三卖若最终出现不同状态，不把可能再探底说成三卖当日已确认。',['2008年4月24—25日该3656平台'])
c(105,'apr28-sixty-down-stroke-finish-before-next','391-b001','4月28日作者说3656未站之后，要等60分钟向下笔完成才再考虑相应行情。','笔|完成|确认|周期K线图',2,'完成是结构条件，不以图右侧未来走势提前填完。',['2008年4月28日该60分钟向下笔'],figs=((391,1),))
c(105,'apr28-daily-up-stroke-and-five-day-line','391-b002','作者称日线3656使一个向上笔完成，要继续延伸仍须重新站住3656；日线回探看5日线，站住则在可接受范围。','笔|均线|周期K线图|确认',2,'日线向上笔与同日60分钟向下笔是不同图框架；完成又谈延伸的原措辞照存，不擅改其笔终点算法。',['2008年4月28日日线图与5日线'],figs=((391,1),),ambiguity='completed_daily_stroke_vs_further_extension_wording')
c(105,'apr29-3656-and-five-day-failure','391-b005 391-b006','4月29日作者视3656为抉择位，其下震荡意义有限；若5日线震荡失败，则确立向下笔、调整压力加大。','均线|笔|确认|完全分类',2,'按原页时间头校为4/29，5日线失败仍是若的分支，不改成当时必已成下笔。',['2008年4月29日该3656及5日线'],figs=((392,1),))
c(105,'apr30-3840-premised-on-effective-3656','391-b008','4月30日作者说3840成中线关键的前提，是3656突破有效，须由节后前三天表现决定；该强不强则小心陷阱。','确认|完全分类|操作策略',2,'新时间头在前段末，本段校4/30；3840不无条件有效，节后强弱未提前定案。',['2008年4月30日所论3656有效突破','节后前三天表现验证'],figs=((392,1),))
c(105,'may5-weak-attack-3840-risk','392-b001','5月5日作者称上攻力度趋弱、以补涨为主，大震荡风险积聚，须观察3840上下表现。','确认|板块轮动|操作策略',2,'原误标读者已依解盘栏目校为作者，日期由前段末5/5头管辖，不继承4/30或次段5/6。',['2008年5月5日该3840情景'],figs=((392,1),))
c(105,'may7-to9-3656-range-rhythm-and-third-points','392-b004 392-b005 392-b007','作者5月7—9日以3656为强弱分水岭和暂时中轴，按中枢震荡及三类点处理；保持这种市场节奏时，下方跌不动买、之上或附近涨不动卖。','中枢震荡|第三类买卖点|确认|操作策略',1,'保持此震荡节奏是条件，失守不变成无限回补；三段各有5/7、5/8、5/9日期，不是读者观点。',['2008年5月7—9日该3656结构','所述市场震荡节奏继续保持'],figs=((392,1),))
c(105,'jun3-sixty-day-average-boll-possible-break-first','393-b000','6月3日作者说行情沿60天线调整，重站3656可上60天线，提醒观察布林通道并不排除先破再立。','均线|布林通道|确认|完全分类',2,'60天线为均线，不混60分钟图或严格60分钟级别；先破再立为可能，不保证任何破位都反转。',['2008年6月3日该3656与60天线'],figs=((393,1),))
c(105,'jun4-three-thousand-break-or-double-bottom','393-b002','6月4日作者给最坏最后一跌破3000与较强则双底而起两种可能，承接此前布林通道提醒。','布林通道|完全分类|确认',2,'历史作者展望，不用7月配图结果倒填6/4已选最坏分支。',['2008年6月4日该布林通道及3000情景'],figs=((393,1),))
c(105,'jun6-comments-not-promises-hold-self-report','393-b006 394-b000','作者明确股票评论只是提点、不作承诺，并自述当年常持股两三天，最长证券类也不断来回操作。','操作策略|操作熟练程度|仓位',2,'两三天是本人历史自述非任何人统一持有期限或账户证明；不承诺不能改成收益保证。',['2008年6月6日作者说明及本人持有自述'])
c(105,'jun6-3656-exit-gap-hold-reentry','394-b001','作者说即使没在3656上盘整顶背驰退出，有效跌破3656仍该退出；之后缺口上能站稳才再介入，站不稳则离开。','盘整背驰|缺口|确认|操作策略',2,'有效破位和缺口能站稳两对象不混，盈利自述未核；本段日期校6/6而非6/4。',['2008年6月6日该3656及缺口'],figs=((393,1),))
c(105,'jun10-prediction-game-operation-absolute-wording','394-b005','作者在6月10日强调预测与操作的区别：预测是谈资，绝对预测不成立，而操作设计应绝对明确、没有不确定；本例3656不站就走，3300缺口不回补才可回补筹码短差，否则离开。','走势预测|缺口|确认|机械化操作|操作策略',1,'绝对操作是作者的规则确定性主张，不证明任何资金/制度/流动性下都可无损执行；缺口不回补与买回筹码含义不同。',['2008年6月10日所述3656及3300缺口方案'],figs=((394,1),),ambiguity='absolute_rule_design_vs_actual_executability')
c(105,'jun10-down-divergence-rebound-gap-two-paths','395-b001','作者安排这轮下跌背驰后的短差：反弹不能回补6月10日缺口就退出，能回补则观察其后中枢三类买卖点。','背驰|缺口|第三类买卖点|确认|完全分类',1,'本段新缺口与前面3300支撑缺口不是自动同一对象；背驰已出现、反弹后是否补缺分别确认。',['2008年6月10日该轮下跌后的反弹方案'])
c(105,'jun10-wave-language-only-analogy','395-b002','作者以沪深历史对照作预测谈资，并借波浪语言称4778反弹为2浪、3000反弹为4浪、后有第5浪，同时说波浪理论不精确，只因读者熟悉而借用。','走势预测|走势分解|操作策略',3,'借用语言不建立波浪与缠论严格同义映射，沪深历史相似不等未来必复制。',['2008年6月10日历史类比及波浪语言'])
c(105,'jun11-small-center-third-buy-gap-or-rest','396-b001','6月11日小型中枢因未破底被作者视为盘整能量有限；有小三买才进一步攻前日缺口，否则休整后再探底；即使好支，没有大消息仍可能无功再考验3000。','走势中枢|第三类买点|缺口|完全分类|政策风险',2,'小三买与大消息条件保留，未给严格中枢级别，不由图表周期替填。',['2008年6月11日该小中枢及6月10日缺口'])
c(105,'jun11-week-bottom-support-daily-short','396-b002 396-b003','作者说有效支持须周线上标准底分型，月季线亦有压力；短线可看日分型，特别心急看30或60分钟，太短则不取。','底分型|周期K线图|确认|操作级别',1,'长/短图表条件不互借，必要措辞限当时支撑判断，不转所有行情普适因果定律。',['2008年6月11日该中长线压力与短线观察'])
c(105,'jun12-no-large-divergence-sixty-not-leg','396-b004','6月12日作者以30分钟以上MACD说明较大级别背驰尚未出现，60分钟甚至还谈不上背驰段，因此当时无有力大反抽。','MACD|背驰|周期K线图|确认',1,'原页新头校6/12，不沿用6/11；指标为该案例观察，未取代结构定义，背驰段与确认背驰分开。',['2008年6月12日该30分钟以上/60分钟图'])
c(105,'jun12-last-down-two-centers-standard','396-b005','作者认为3786起最后一跌须至少两个中枢，否则仍是原中枢震荡；当时3300上首中枢已有，标准完成走法为反弹成第二中枢、再破位真正背驰。','下跌|走势中枢|背驰|完成|完全分类',1,'两个中枢须在所述结构内合法成立，不是任意两图框；第二中枢波动基本不补缺口为该例预计，未直接定义一般中枢规则。',['2008年6月12日作者所称3786起最后一跌'])
c(105,'jun12-third-sell-divergence-or-more-centers','396-b006','作者说两中枢下跌也可因外围恶劣延续为多中枢，关键看第二中枢三卖之后是否真正背驰。','第三类卖点|背驰|走势中枢|完全分类|政策风险',1,'三卖后未真正背驰不能预定下跌已结束，两个不升为最多两个。',['2008年6月12日该第二中枢之后'])
c(105,'jun12-no-new-low-second-center-third-buy','396-b006','另有不破位而小级别转大级别的支，对应第二中枢出现三买；作者称其不常见，但仍在可观察范围。','第三类买点|小级别转大级别|完全分类|确认',1,'不常见不是已测概率，保留第二中枢三买的具体来源条件，不任意一涨都叫小转大。',['2008年6月12日该第二中枢三买情景'])
c(105,'jun13-price-support-not-more-than-rhythm','396-b008 397-b000','作者以6124减3600得2524、前后跌幅若相等约2430推看2500一带中线支持，但说最终到不到不重要，首要仍是形成这轮下跌第二中枢。','价格区间|走势中枢|下跌|确认',2,'2524与2430/2500是不同计算/近似目标，不变为确定底；1345和2430保留作者近似，不补精确回测。',['2008年6月13日该支持与下周结构任务'])
c(105,'jun14-second-center-opportunity-capability','397-b002','6月14日作者把下周短线机会定位为构成3700多点下来的第二中枢，有能力者做短差，无能力者小板凳。','走势中枢|操作熟练程度|操作策略',2,'构造中枢的短差不等整轮下跌已结束或任何人都可参与；日期不继承6/11。',['2008年6月14日所论下周第二中枢机会'])
c(105,'jun16-first-down-type-not-one-center','397-b003','作者6月16日认为6124下来第一段已是下跌类型而非一个中枢的盘整，所以最后一跌后反弹难太出色，之后仍极可能有锯齿型第二段下跌，须按能力设计。','下跌|盘整|走势中枢|完全分类|操作熟练程度',2,'是当时走势判断和后续预测，不把极可能记已发生，也不以7月目标反向覆盖日期。',['2008年6月16日作者所论6124大调整'])
c(105,'jun17-2917-possible-second-center-2976-strength','397-b004','作者6月17日给2917为第一关，过不了继续探底，过了才有最后一跌第二中枢成立的可能；2976观察整个反弹力度。','走势中枢|确认|完全分类',2,'过2917只是可能成第二中枢，不与笔完成/2976强度合成同一充分条件。',['2008年6月17日该2917/2976情景'])
c(105,'jun18-prior-high-before-2917-stroke','397-b005 397-b006','6月18日作者说前日未过2917后继续探底，要止跌先站前日高点，再突破站住2917可延伸为笔；逼近2700时留意小级别区间套。','笔|区间套|确认|操作策略',2,'前日高点与2917分步，未给统一止跌充分算法；相对安全为作者评价非无风险。',['2008年6月18日该前日高点/2917及2700附近'])
c(105,'jun19-nesting-entry-boundaries-for-exit','397-b007 397-b008','6月19日作者明确区间套成立即进场，并非等前日高点或2917站稳才进；已有仓位看2917站住且继续满足笔延伸条件才保持，否则分批撤。','区间套|笔|确认|仓位|操作策略',1,'入场信号与持有/退出边界方向不能倒置，站2917与笔延伸条件联合；该方法仍以使用者可识别区间套为前提。',['2008年6月19日该2700附近第二中枢反弹'])
c(105,'jun20-temporary-2700-2900-not-final-bottom','397-b009','6月20日作者暂按2700—2900大震荡，是否成真正底部震荡仍待下周，脱离震荡看2917。','中枢震荡|确认|完全分类',2,'暂时震荡与真正底部未定分别保存，不把区间范围自动作为最终底部证明。',['2008年6月20日该震荡'])
c(105,'jun23-large-rebound-height-triangle-risk','397-b010 398-b000','作者把6124调整视作最后阶段、3700起下跌视作第二中枢震荡，称一旦背驰则结束并总修正；但若大反弹成三角形，第一段向上幅度即最大，高度未必好；最坏3300上首中枢已足阻挡上拓。','背驰|走势中枢|反弹|完全分类|确认',1,'作者阶段判断非项目确认，背驰条件未省；超级大反弹不等必超3700或必回全部跌幅，三角形分支保留。',['2008年6月23日作者所论大调整及3700起下跌'])
c(105,'jun25-week-fractal-2945-and-no-new-low','398-b001','6月25日作者说本周任务为高点突破2945形成周底分型，能高收最好；又说只要本周不再破底形态成立，并强调剩两天不能前功尽弃。','底分型|周期K线图|确认',2,'原文即使不行指高收还是突破的范围须保留，未把任一条件独立升为所有周分型充分判据。',['2008年6月25日该周底分型构造任务'],ambiguity='weekly_fractal_even_if_not_reference_scope')
c(105,'jun27-center-oscillation-sublevel-divergence','398-b002 398-b003','6月27日作者继续按中枢震荡：上行次级别甚至次次级别顶背驰或盘背先退出，反向下行再进入；做不了短差者小板凳。','中枢震荡|次级别|背驰|盘整背驰|操作熟练程度|操作策略',1,'限中枢震荡继续有效的语境，不能把中枢已破后任意下跌都机械回补；从无意外为作者修辞，不当实测全胜。',['2008年6月27日该中枢震荡','能把握相应次级别短差'])
c(105,'jun30-new-low-containment-and-2700','398-b005 399-b000','6月30日作者说新低使前两周包含关系无需再纠缠；本周能否成为真正底分型最下一根，关键看起来后回试2700能否站住，短线仍2700—2900震荡。','包含关系|底分型|周期K线图|确认|中枢震荡',2,'最低K位置尚待，不把创新低一根自动当周底确认；跨页续句与校正日期齐全。',['2008年6月30日该周线包含及2700回试'])
c(105,'jun30-fast-trade-or-bench-or-active-accumulation','399-b000 399-b001 399-b002','作者说该底盘背短差须信号出现敢买敢卖、反应够快；做不到者可小板凳，或选基本面绝对低估股票分批主动买套，再用日波动降成本，并称后者为中长线大资金唯一正确做法。','主动买套|盘整背驰|资金管理|操作熟练程度|成本',1,'两种替代与基本面低估/分批条件照留，唯一正确是作者方法评价，未证明适合任意资金或保证每天有可交易差价。',['2008年6月30日所论方法及中长线大资金'],ambiguity='active_accumulation_exclusivity_and_execution_scope')
c(105,'jul1-second-center-divergence-or-third','399-b006 399-b007','7月1日作者按第二中枢后背驰观察，但仍允许第三中枢，条件是此次破底未形成标准区间套背驰。','走势中枢|背驰|区间套|完全分类|确认',1,'第二中枢已讨论不等下跌已结束，未成标准区间套背驰时不能强行宣告最后一跌终结。',['2008年7月1日所论这次破底'])
c(105,'jul1-theoretical-minimum-above-2990','399-b008','作者称一旦这次下跌最终完成，针对6124调整的理论确保最低反弹为以相应级别回到2990之上；做到这一点后继续下跌仍在理论允许范围。','背驰|完成|级别|走势中枢|反弹',1,'最终完成及相应级别两条件不能省，之上不改恰到；确保为作者理论断言，项目未独立重建/证明该实例理论幅度。',['这次下跌最终完成','以所论相应级别反弹回2990之上'],ambiguity='author_theoretical_guarantee_not_independently_reproduced')
c(105,'jul1-empirical-third-3700-not-guaranteed','399-b009','作者把整个下跌约1/3、基本回3700上的幅度明确列经验参考，并说非100%保证，自己认为一般90%以上准确；理论确保只能说2990。','反弹|概率原则|价格区间|操作策略',1,'经验比例与理论断言分层；90%以上没有样本/统计验证，不能作项目胜率或取消2990最低幅度的完成前提。',['2008年7月1日作者对该反弹幅度的区分'],ambiguity='empirical_accuracy_percentage_not_verified')
c(105,'jul1-internal-structure-and-center-double-check','399-b010','作者说反弹在2990、3700或更高结束，由反弹内部结构及前中枢角度双重判断，并称如联立方程可得极少甚至唯一结果。','走势分解|走势中枢|确认|反弹',1,'两角度独立为作者用语，不证明统计独立或具体唯一性方程已给；内部结构当下确认不等预知唯一价格。',ambiguity='double_confirmation_independence_not_formally_proven')
c(105,'jul1-final-decline-ninety-nine-not-hundred','399-b011 400-b000','作者认为3700起这段是6124下来最后一个下跌，但明确非理论100%：可有大的第三中枢，只因基本面等判断自称99%把握；其内部第二中枢后主动买套已现实、尤其大资金。','主动买套|走势中枢|下跌|资金管理|完全分类',1,'99%是作者判断非经验证概率，大第三中枢尚允许；最终一跌的非100%不与2990条件理论断言混成无条件保证。',['2008年7月1日作者该阶段判断','3700起下跌内部已出现第二中枢'],ambiguity='author_confidence_percentage_not_verified')
c(105,'jul1-two-third-centers-no-risk-author-assertion','400-b001','作者列主动买套两风险：6124下跌出现第三中枢，或3700下跌出现第三中枢；又断言实际都无风险，因为分批、每日波动足够降成本且对应反弹留退出余地。','主动买套|走势中枢|资金管理|成本|操作策略',2,'无风险是必须保留归属的作者断言，未独立验证流动性、制度、资金持续性和每日日波动可执行；两种第三中枢属不同范围。',['2008年7月1日作者所述分批建仓方案'],ambiguity='active_accumulation_risk_free_claim_vs_execution_constraints')
c(105,'jul1-active-accumulation-stage-eighty-percent-filter','400-b002 400-b003','作者向精确应用困难者、尤其较大资金，主张当时进入必须分批主动买套阶段，选择高位回落80%且基本面无重大改变者；本人回补熟悉旧股，仍要求基本面可操作，并说不必跟其扎堆。','主动买套|资金管理|操作熟练程度|操作策略',1,'必须是作者当时建议非项目指令；80%与其另举600737由30多到15下并不逐例严格吻合，不能宣称所有例子都回落80%；原段6007373字样未私改来源。',['2008年7月1日作者阶段判断','分批，所选股高位回落80%且基本面无重大改变'],ambiguity='eighty_percent_filter_vs_individual_examples_scope')
c(105,'jul2-inverted-t-seventy-percent-empirical','400-b004 400-b005','7月2日作者把连续下跌新低倒T型K线与2007年12月18日类比，自称成最终反弹底概率70%；随后明确这些K线方法是经验性、与其理论无关，只可辅助，操作仍据当下走势。','倒T型K线|概率原则|当下|操作策略',1,'70%未提供样本和统计，经验辅助不是理论买点充分条件；上次二次探底与本次不同的限制保留。',['2008年7月2日该倒T型K线'],exceptions=['作者指出上次是在二次探底中产生'],figs=((401,1),),ambiguity='empirical_accuracy_percentage_not_verified')
c(105,'jul2-active-accumulation-partial-chips-not-always-half','400-b006','作者以小级别盘背冲高卖部分、回落有差价再回补说明主动买套降成本；筹码够多时可只补固定数量，不必持续增筹，并指向一天8根30分钟线形态课程。','主动买套|盘整背驰|仓位|成本|操作策略',1,'部分不等4/16半仓统一比例，数量可变/不变两支保留；降成本为方法目标，未保证每天都有差价或可成交。',['2008年7月2日主动买套短差例','出现相应小级别盘背且回落有差价'])
c(105,'jul3-containment-delays-bottom-step-boundaries','401-b000','7月3日低开使前日倒T不太标准，两日包含令底分型须再等次日；作者要求依次2753、2945、缺口、3483观察，2753不攻克可短差，攻克才确认较大反弹并看下一关，不能超越阶段。','包含关系|底分型|倒T型K线|确认|完全分类',1,'时间校7/3，未用后图填当日分型已成；较大反弹不擅定严格级别，三价及缺口不同对象逐层处理。',['2008年7月3日该日线图及2753/2945/3483'],figs=((401,1),))
c(105,'jul4-weak-bottom-2753-still-pending','401-b002','7月4日作者说底分型终于勉强形成、但属最弱，若下周初2753未攻克仍会再探底，并可给短差/主动买套降成本机会。','底分型|确认|主动买套|操作策略',2,'校7/4而非7/2或段末7/9，分型已成不等2753已破/向上笔已确；机会不保证收益。',['2008年7月4日该最弱底分型'])
c(105,'jul9-moving-average-classification-homework','401-b003','7月9日作者留问题：用最简单均线方式对股票完全分类，再设计短线轮动方式，并说明次日继续讲。','均线|完全分类|板块轮动|操作策略',2,'本段只是作业及下文指向，未给分类具体条目或最优证明；不提前把下一课答案或未知流程图当本段已定义算法。',['2008年7月9日该作业'],ambiguity='moving_average_homework_answer_deferred')

keep('382-b004','lower-l084-c-stage-fractal-only-recursion-start-optional lower-l101-c-stage-a0-arbitrary-design-author-wording','105强调能完全分类的约束，未给任意替代标准证明；84唯一性条件与101随意a0措辞仍并列。')
keep('382-b003 382-b007','lower-l091-c-stage-machine-profit-author-proposal lower-l104-c-stage-apr8-one-fractal-method-demonstration','91大型计算机自动赚钱是作者设想；105按结构节奏的机械化不自动等同已实现自动交易。')
keep('385-b009 389-b002 401-b002','lower-l081-c-stage-new-stroke-two-joint-conditions','四K/边沿只是案例观察，不抹除新笔不共K及极值K间至少三根联合定义。')
keep('386-b003 400-b006','lower-l100-c-stage-capacity-gate-and-tiny-practice lower-l094-c-stage-t1-same-day-exit-impossible-risk','半仓只4/16所述震荡法，7/2部分筹码另有数量选择；T+1和能力门槛不因规则明确而消失。')
keep('391-b002 393-b000','lower-l063-chart-period-not-center-level','日/60分钟图笔及60天均线分别对应图表/指标，不机械换严格中枢级别。')
keep('388-b005 394-b005','lower-l068-c-stage-operations-piecewise lower-l102-c-stage-classification-control-means-current-display','按当下分类预设操作，与预测不等市场、可控不等干预价格相衔接；绝对规则不证明实际可执行。')
keep('399-b008 399-b009','upper-l024-c-stage-standard-divergence-retrace-b-center lower-l098-c-stage-divergence-return-then-classify','本例2990相应级别/完成前提与经验3700分层，不自动解决24/98广义盘背回中枢范围。')
keep('399-b002 400-b001','lower-l104-c-stage-small-fund-short-bite-large-chips-now lower-l102-c-stage-mar18-large-fund-batches-base-position','主动买套新增较大资金/阶段/基本面条件，作者无风险断言仍未证明资金及执行约束消除。')

issue('mechanical-classification-and-unknown-flowcharts','382-b003 382-b004 382-b007','105机械化核心仅结构节奏及完全分类，383/384未署名流程图另含大量加减仓箭头，不能自动当作者已认可程序；替代分类未给完整证明。','作者正文与图整理分开；不新建交易执行系统，不将未知图所有分支发布为作者明说。',True)
issue('half-position-vs-active-accumulation-execution','386-b003 394-b005 399-b002 400-b001 400-b006','4/16半仓震荡法与7/2部分筹码法不同；绝对操作、主动买套无风险与T+1/流动性/能力约束未统一。','保留规则清晰与实际成交的差别、两种第三中枢及数量可变/固定条件，不宣称稳赚。',True)
issue('fractal-stroke-reference-and-completed-extension','385-b009 388-b012 389-b002 391-b002 398-b001 399-b000 401-b000 401-b002','四K分型、3189/3085、日笔完成又延伸、6/25即使不行指代及周包含新低/2753等跨日对象不同。','保留原数字、日期、周期与未确/已成状态，不取后加图提前确认，不改笔算法。',True)
issue('theory-2990-vs-empirical-3700-confidence','399-b007 399-b008 399-b009 399-b010 400-b000 400-b004 400-b005','2990之上为作者附完成与相应级别条件的理论断言；3700经验1/3、90%/99%/70%比例无独立统计，双确认独立性未证明。','理论/经验/判断百分比区分，不等项目形式证明或实测胜率，不删除第三中枢与继续下跌允许支。',True)
issue('multiple-gap-objects-and-price-rounding','387-b002 394-b001 394-b005 395-b001 396-b001 396-b005 401-b000','5524/4196与前文/图小数、3656与3658等不统一；3300支撑缺口不回补和6/10新缺口能否回补是不同对象，2753之后缺口亦需单独定位。','原数照录，按日期/相对方向保留缺口对象，后续若形式化需逐图追溯，不能仅凭回补一词合并。',True)
issue('active-accumulation-filter-examples-and-historical-claims','385-b003 385-b013 387-b003 388-b003 393-b004 395-b003 395-b004 395-b005 395-b007 400-b002 400-b003','低价/80%筛选与600737半价例范围、作者交易/收益、32年历史周期、政策市场因果等均未外核；个人病情为上下文。','不认证80%逐例成立、病情/治疗效果或历史周期定律，不转当前市场建议；保留作者限定与不承诺原话。')
issue('figure-makers-and-late','382-b003 385-b009 387-b002 389-b002 391-b002 391-b008 392-b007 393-b000 394-b005 398-b003 400-b004 401-b000','11本课图已看：383/384流程图身份未核，9行情图含文后行情；382图属于上一课104且已核，不再计本批图。','未知流程不作作者算法，主图与插图都看；原日状态由正文支撑，不以后期K线自证预测。')

note('382-b002 382-b006 383-b000','author-habit-profit-rhetoric','聪明人、争论、挣钱简单及良好习惯的修辞已完整读。','作者价值判断和收益修辞不等可验证普遍因果、稳赚或账户实绩。')
note('385-b003 385-b005 385-b008 385-b011 385-b012 385-b013 386-b001 386-b002 386-b005 386-b006 386-b009 386-b012 386-b014','historical-short-trade-and-news-context','尾盘无仓者捞点、平安压制、短跑收益感受、券商直投和新能源等轮动、CPI多空说辞、新股抢筹、逼宫融资与贴分析安排已读。','历史政策/资金因果与收益未核；尾盘建议仍须能力及结构，不能直接当充分买点。')
note('387-b005 388-b000 388-b001 388-b003 388-b007 388-b008 388-b009 388-b010 388-b011 388-b013 388-b014','historical-comparison-and-policy-opinion','沪深6100历史类比、资本市场牺牲品观点、政策半夜鸡叫及做空风险、心理与双面操作、领涨板块叙事已读。','历史对照不是必然复制，匿名政策动机和政治断言仅归作者；实际操作仍受资金/制度条件。')
note('389-b001 389-b004 389-b005 389-b009 389-b010 390-b000 390-b002 390-b004 390-b011 390-b012 390-b013 390-b014 390-b015 390-b017 391-b000 391-b003','historical-sector-health-and-self-validation','公告/留言、金融地产空头陷阱、减税成交量与信心解释、板块黑马、个人病情/中医帖安排、3656自证技术尊严及承接资金已读。','不核企业政策因果或治疗效果，不把预测自证/神奇等措辞当统计验收；明确技术条件另抽。')
note('391-b004 391-b004-s01 391-b007 392-b000 392-b002 392-b003 392-b006','corrected-author-column-nontechnical-context','连续作者解盘头、4/29个股风险、4/30住院近况、5/6短句和治疗自述均按原页头校身份日期；段末下一日期不覆盖前段。','无独立读者署名，不能沿错误reader姓名；病情用药仅作者历史自述，不作医学判断、治疗有效性或建议。')
note('393-b001 393-b003 393-b004 393-b005 394-b002 394-b004 395-b000','corrected-author-context-and-cycle-rhetoric','井冈山比喻、裸时间头、6/5不应留余地及32年循环/妖蛾子、6/6解盘栏目说明、6/10历史神秘引言与自然反应要求已读。','时间头管后文；不把32年周期或不存在下破理由当已证明历史/市场规律，不把天灾与股价作科学因果。')
note('395-b003 395-b004 395-b005 395-b006 395-b007 396-b000 396-b000-s01','historical-cycle-political-and-survival-context','1912/1944/1976/2008与其后年份的历史循环、2009预言、2008生存和税反弹幅度、援越国家利益机械工程类比与新解盘头已读。','历史解释及预言不外核、不认证周期因果或政治事实；国家利益机械化与股票机械化不是自动同一模型。')
note('396-b007 397-b001 398-b004 399-b003 399-b004 399-b005 400-b003-s01 401-b001','author-learning-personal-and-date-context','读课提醒、走势必完美不应望文生义、6/30/7/4独立时间头、桌球和住院写帖说明、7/2解盘头均已读。','标题/时间只定位；身体近况非技术证据，原文日期头校后文，不以较晚时间自动撤回旧规则。')

relations={
 'lower-l105-c-stage-mechanical-follow-structural-joints':[('机械化操作','走势分解','requires')],
 'lower-l105-c-stage-classification-choice-must-be-complete':[('机械化操作','完全分类','requires')],
 'lower-l105-c-stage-apr16-half-position-range-break-rule':[('仓位','中枢震荡','qualifies')],
 'lower-l105-c-stage-jun19-nesting-entry-boundaries-for-exit':[('区间套','确认','related')],
 'lower-l105-c-stage-jul1-theoretical-minimum-above-2990':[('反弹','完成','requires')],
 'lower-l105-c-stage-jul2-active-accumulation-partial-chips-not-always-half':[('主动买套','成本','related')],
}
for r in rows:r['relations']=[{'source':s,'target':t,'type':kind} for s,t,kind in relations.get(r['id'],[])]

by_passage=defaultdict(list)
for r in rows:
    for e in r['evidence']:by_passage[e['passage_id']].append(r)
for item in pending:
    item['lesson_numbers']=sorted({int(passages[x]['unit_id'].split('-')[1]) for x in item['passage_ids']})
    if item['id'].endswith('figure-makers-and-late'):
        item['lesson_numbers']=[105];item['figure_ids']=[f['id'] for f in figures]
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
      'related_existing_claim_ids':retained_ids,'note':'机械化是按结构节奏，未知流程另列；预测/操作、2990条件理论/3700经验及70/90/99自述比例分开，来源身份日期已逐页校核。'},'4_reverse_check':inverse}})
for f in figures:
    key=(f['pdf_page'],int(f['id'].rsplit('fig',1)[1]))
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=figure_notes[key],
      figure_source_review='十一图已核：九后加、两流程图未核见stage-c-l105-source-applied.json；382上一课图不重算；未知流程不作作者程序，正文独立支持不倒填确认。',
      linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger)==181 and len({x['passage_id'] for x in ledger})==181
def dump(suffix,data):
    (OUT/f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x,ensure_ascii=False,separators=(',',':')) for x in data)+'\n',encoding='utf-8')
dump('reviewed.jsonl',rows);dump('coverage.jsonl',ledger);dump('pending.jsonl',pending);dump('figures.jsonl',figures)
summary={'stage':'C','schema_version':metadata['schema_version'],'graph_version':metadata['graph_version'],'lessons':[105],'document_id':DOC,'reviewer':REVIEWER,
 'passages_read':181,'claims':len(rows),'evidence':sum(len(r['evidence']) for r in rows),'importance_counts':dict(Counter(r['importance_level'] for r in rows)),
 'new_concepts':sorted({x for r in rows for x in r['concepts']}-set(concepts)),
 'whole_lesson_semantic_read_complete':True,'technical_extraction_complete':False,'four_round_review':True,'independent_review_claimed':False,
 'visual_pdf_pages':list(range(382,402)),'figure_objects_viewed':11,'adjacent_figure_viewed':{'id':DOC+'-p0382-fig1','unit':'lesson-104','counted_in_batch':False},'figure_origin_counts':dict(Counter(f['origin_status'] for f in figures)),
 'pending':[x['id'] for x in pending],
 'source_passages_snapshot_sha256':SOURCE_SHA,'retained_source_links_in_ledger_only':True,'database_mode':'ro','formal_import':False,
 'acceptance':'181段四轮审读、20页11本课图+1邻课边界；48来源身份日期及11图校核，机械化/半仓/主动买套和理论/经验/预测范围分开，增量待预检发布。'}
(OUT/f'{BASE}.summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
db.close();sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(summary,ensure_ascii=False))
