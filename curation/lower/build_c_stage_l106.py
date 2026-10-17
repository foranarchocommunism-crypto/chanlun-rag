"""Materialize the manually read lower 106 batch; SQLite is read-only.

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
BASE='c_stage_l106'
REVIEWER='Codex 主代理 / 阶段C下册106课同模型四轮复核'
SOURCE_SHA='29f403297d066099695d75cb6b3d8f27e6fa12aab02d032143ac7943d784a441'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
db.row_factory=sqlite3.Row
metadata={r['key']:json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version']=='1.1.0'
assert hashlib.sha256((KB/'sources/volume_2.pdf').read_bytes()).hexdigest()=='5332cd1b60381c47ceb81358db6bbb47882efd074fc5c869dcc3002aaed1b5c0'
passages={r['id']:dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id='lesson-106' ORDER BY pdf_page,block_index,id")}
assert len(passages)==125
assert hashlib.sha256(json.dumps(sorted(passages.values(),key=lambda p:p['id']),ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==SOURCE_SHA
old={r['id']:dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts={r['label']:dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical={label:r['label'] for r in concepts.values() for label in [r['label']]+json.loads(r['aliases'])}
figures=[dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 402 AND 415 ORDER BY pdf_page,id',(DOC,))]
assert len(figures)==10
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
    pending.append({'id':'lower-l106-c-stage-pending-'+slug,'status':'pending','passage_ids':[pid(s) for s in shorts.split()],
                    'description':description,'suggested_action':action,'blocks_full_semantic_extraction_completion':blocker,'reviewer':REVIEWER})




c(106,'rebound-example-reverse-for-adjustment','401-b005','第106课以反弹为例说明，调整情形按反向理解。','反弹|均线|操作策略',2,'只说明本节示例方向的对称性，不删后文级别、均线系统及买卖点条件。')
c(106,'six-basic-bars-five-day-touch-author-wording','401-b006 402-b000','作者说任一级别有最少延伸时间，以笔须顶底分型而至少延伸6个基本K线单位为例，并说5日线都碰不到就不是笔反弹；其他类型也可找最少时间及相应挑战均线。','笔|分型|均线|级别',1,'跨页合读，6及5日均保留原文；与62独立K要求和81新笔两联合条件计数范围并列，不把此句自动撤回81或补一张已证明的全级别时间表。',['第106课所论反弹及基本K线单位'],ambiguity='six_bar_minimum_vs_l081_joint_rule_scope')
c(106,'average-level-no-necessary-correspondence','402-b001','作者明确走势级别与均线没有必然关系，只有大致区间对应。','均线|级别|走势中枢',1,'不能把均线周期直接当严格中枢级别或固定比例换算，更不以均线独立定义走势级别。')
c(106,'same-trend-centers-similar-pressure-empirical','402-b001','作者凭经验说同一趋势各中枢的压制均线大致相同：首中枢受89日压制，后继很可能也受89日；若反弹仅到34日，与前首中枢同级概率很小。','均线|走势中枢|级别|反弹',2,'大致/经验/很可能保留，不给已测概率或把碰同一均线作为同级充分必要条件。',['同一趋势内合法中枢的经验比较'])
c(106,'nested-types-need-average-system','402-b002','作者认为除最简单的笔外，走势大级别套小级别，单条均线意义不大，需要均线系统。','均线系统|均线|级别|笔',1,'这是本节观察系统要求，不把一组均线当完整走势递归或用它取消结构定义。')
c(106,'eight-average-parameters-fit-existing-market','402-b003','均线系统须吻合实际已有走势；作者为6124下来行情选择5、13、21、34、55、89、144、233八个参数。','均线系统|均线|完全分类',1,'八个参数按原文，不插入8，不把历史吻合自评当跨市场最优或未来普遍保证；课程原头仅2008-07-10，图嵌时分秒不反填。',['第106课该6124以来已发生行情的示例'],figs=((402,1),))
c(106,'historical-average-support-233-not-annotation-144','402-b004','作者举4778受233日支持，后55/89日多头陷阱、21日压至3000下、反弹55日受阻及再跌13日下，说明该组均线历史吻合。','均线系统|均线|多头陷阱',3,'图中是否应为144日是未核整理者疑问，正文233不改；历史逐K及均线没有独立复算，不报告经验自证为模型精度。',['第106课所述历史均线案例'],figs=((402,1),),ambiguity='text_233_vs_unverified_144_annotation')
c(106,'system-retain-until-material-change-55-34','402-b005','在后续走势没有大变化时作者沿用该系统；55日及将缠绕的89日为本次反弹试金石，若不突破甚至不触及，级别仍不够大、可回试再组更大反弹，短线先看34日。','均线系统|均线|反弹|完全分类|确认',1,'不突破/不触及的强弱措辞及大变化前提照留，不把历史参数永久锁定或尚待均线突破当已成。',['该示例系统仍吻合且后续走势未发生大变化'])
c(106,'horizontal-stock-classification-for-rotation','402-b006','作者将同一均线系统横向用于所有股票分类，以观察强弱先后和市场轮动，而非只对单一指数使用。','均线分类|均线系统|板块轮动|完全分类',1,'横向类别须统一分类语境，不能给不同股票各用任意参数后仍称同一平均类别；本文没有完整列市场数据。')
c(106,'smallest-not-yet-conquered-average-nine-classes','402-b007 403-b000','分类依据是本次反弹截至当时未曾攻克的最小周期均线，八条均线分九类，最差类为完全在所有均线下。','均线分类|均线系统|完全分类',1,'这是本次反弹进程的未曾攻克标准，不直接改成当前价格在几条线上或只按均线价格排序；攻克阈值、反弹起点等未给全算法。',['同一轮所论反弹截至当下','使用该八周期均线系统'],ambiguity='conquer_threshold_and_rebound_start_not_formalized')
c(106,'strongest-not-necessarily-currently-above-all','403-b000','作者提醒最厉害者不一定当前完全在全部均线之上，并把为什么留给读者思考。','均线分类|完全分类|操作策略',1,'本文没有直接给这个设问的详答，不把历史攻克/当前回撤的整理解释伪称作者已说，也不把所有线之上视充分买点。',ambiguity='strongest_class_question_not_answered_here')
c(106,'nine-class-stock-examples-and-index-four','403-b002 404-b000','作者把000802/000998/600636列第9类，600139第8，600578/600607第7，600195/600343第6，600737/000600第5；指数最大周期仅站21日，从最弱数第4类。','均线分类|均线系统|完全分类',2,'这是历史作者分类，不是当前名单；图把600578标类别6而正文第7，制作人未核，不据图改文，也未独立复算全部股票攻克历程。',['2008年7月10日作者所举股票与指数'],figs=((403,1),(403,2)),ambiguity='text_class7_vs_figure_class6_for_600578')
c(106,'class-distribution-warns-index-34-pressure','404-b001','作者说当时最多股票受34天线上下压制，故指数未到34日时也可提前提示该线压力。','均线分类|均线|板块轮动|确认',2,'统计最多是作者观察，未提供计数/样本全集，不当本项目独立统计或保证触线必跌。',['2008年7月10日该横向分布示例'])
c(106,'class-n-top-divergence-rotate-after-exit','404-b002 404-b009','作者说从N类调整到N+1类需时间，趋势级别走势在N类顶背驰可先退出，转看已调整可重启或补涨股票。','均线分类|板块轮动|背驰|操作策略',1,'至少几天为作者节奏经验，未给任意市场硬时间下限；N类别不是N分钟级别，换股仍须具体买点。',['所论反弹分类中N类调整且有相应顶背驰'])
c(106,'sector-strength-average-class-number','404-b003','作者以板块成员类别数的平均判断强弱，平均数越大越强，并命名为缠中说禅板块强弱指标。','缠中说禅板块强弱指标|均线分类|板块轮动',1,'原文是类别数平均，未给市值/成交量加权、缺失样本或板块成分动态规则，不自行补权重模型；类别是序数比较非收益率。',['本节以反弹为例的均线分类','使用同一组规则所得板块成员类别数'])
c(106,'leading-sector-dynamics-combine-stock-structure','404-b004','作者把最强板块称领涨板块，关注其动态；将各板块强弱指标同图比较轮动次序与节奏，还须配合具体股票走势分析。','缠中说禅板块强弱指标|板块轮动|操作策略',1,'配合个股结构的条件不能由板块均值代替；未给并列最高的唯一领涨判定或自动买卖触发。')
c(106,'program-possible-not-supplied','404-b005','作者认为上述分类与轮动可由电脑程序处理，但表示程序应由读者自行设计，本节不提供成品。','均线分类|缠中说禅板块强弱指标|操作策略',2,'不把容易编程的作者评价当已有可执行程序、完整阈值或收益验收，不另行实现交易系统。')
c(106,'jul11-top-fractal-risk-before-rotation','404-b007 404-b008 404-b010','7月11日作者提醒即将构顶分型时先看风险，虽顶分型未必延伸笔，短线顶背驰并接近压力线时仍应处理风险，不能只谈轮动。','顶分型|笔|背驰|板块轮动|确认',1,'顶分型出现与笔已成分开；34日压力是前日横向示例的承接，不取文后图补确认。',['2008年7月11日午前所论风险'],figs=((405,1),))
c(106,'jul11-inclusion-exception-five-day-two-paths','404-b011 405-b000','作者说除非当日下午大涨形成包含，否则顶分型构成；5日线未有效破则不成笔、再冲34日，否则成笔调整，等该笔对应短线底背驰。','包含关系|顶分型|笔|均线|背驰|完全分类',1,'午前条件与下午例外照留，跨页续句齐全；5日线是本例观察，不替完整新笔联合定义。',['2008年7月11日午前所论当日下午/5日线分支'],exceptions=['下午大幅起来形成包含关系'],figs=((405,1),))
c(106,'rotation-rhythm-founded-on-buy-sell-points','405-b001','作者称节奏最终考验操作水平，轮动只是节奏的一种方式，所有节奏仍须以买卖点为基础。','板块轮动|操作熟练程度|操作策略|第三类买卖点',1,'基础是各自相应买卖点，不把板块均值、排名或强势单项当充分入场信号。')
c(106,'jul14-t1-limits-precise-small-level-operation','406-b003','7月14日作者说T+1确实限制理论化小级别最精确操作，小级别短线更宜T+0或期货等；是否做节奏按能力情况，能力不足不必提高要求。','T+1|操作级别|操作熟练程度|操作策略',1,'这是明确制度限制原话，不把100数量即可执行/105绝对设计概括成制度障碍消失，也不转当前产品推荐或收益保证。',['第106课该小级别短线与T+1约束语境'])
c(106,'jul16-daily-stroke-intraday-down-divergence','406-b004','7月16日作者说未上5日线则调整延伸为笔，等日线图该笔所对应分时图下跌类型出现底背驰，再考虑介入。','笔|均线|背驰|周期K线图|确认',1,'日线笔与分时图走势类型不是同一层；底背驰后仍考虑是否，而非价格一触均线就买，日期校7/16。',['2008年7月16日该日线笔及对应分时走势'])
c(106,'jul19-five-day-not-confirmed-risk','407-b001','7月19日作者虽见周五反弹，仍说5日线不能认有效站住；下周初再破会有新一轮下跌风险，站住才至少再冲一次。','均线|确认|完全分类',2,'反弹与有效站住分开，未以盘中触线或传闻确认站稳；下周预期未当已发生。',['2008年7月19日该5日线状态'])
c(106,'jul21-five-day-held-2896-34-and-2952','407-b002','7月21日作者记5日站住来第二波，接看2896及对应34天线；站住可改善短线系统、MACD挑战零轴及形成所称头肩底，颈线2952仍为后续关口。','均线|MACD|颈线|确认|完全分类',2,'当天5日已站与2896/2952待攻不同；三项预期不是当时全部确认，日期校7/21。',['2008年7月21日该短线系统'],figs=((407,1),))
c(106,'jul29-34-55-lines-coarse-boundaries','407-b003','7月29日作者认为55日线加速下移时急上可能只碰顶，不能精看者可先看34、55日线来判短线。','均线系统|均线|确认',2,'简化观察不等所有走势只受两线决定或适用于所有周期；作者强措辞保留为该例判断。',['2008年7月29日该均线位置'])
c(106,'jul31-zero-obstruction-hold-or-diverge-new-low','407-b004','7月31日MACD零轴受阻后作者列两支：当前位置坚持后再上零轴，或破底背驰后再来，以均线系统辨别。','MACD|均线系统|背驰|完全分类',2,'两支未提前定案，不把指标过轴独立作底背驰定义；日期不继承7/19。',['2008年7月31日该MACD/均线结构'],figs=((407,1),))
c(106,'aug3-month-doji-continuation-or-bottom-base','407-b006','8月3日作者说7月月线十字星究竟为中继还是底分型最下一K，将影响后续数月走势。','底分型|周期K线图|确认|完全分类',2,'十字星单K不能自动定月底，后文奥运经济预期只是作者宏观语境，日期校8/3。',['2008年8月3日该月线十字星'])
c(106,'aug4-no-bottom-without-market-structure','408-b002 408-b003 408-b004','作者说走势不体现底部就没有底部，不能以奥运行情愿望代替；5日线尚上不去时仍待MACD零轴破/不破、破后真假等分支决断。','当下|确认|均线|MACD|完全分类',1,'是8月4日当时结构与作者原则，假破判据未在此定义，不以愿望/消息代结构或以零轴代全部理论。',['2008年8月4日该底部未明状态'])
c(106,'aug6-first-leg-ended-2762-conditional-day-stroke','408-b007 409-b000','8月6日作者称2924下来至少第一段在早间小背驰段区间套完美后结束；2762未有效站则短休后第二段下跌，站稳则该反弹至少延伸日线笔，更大可能待后图。','区间套|背驰|笔|确认|完全分类',1,'第一段结束不等2924整体下跌类型已完；2762有效站稳与未来更大级别分别确认，跨页续文齐。',['2008年8月6日该2924第一段及2762'],figs=((408,1),))
c(106,'aug6-july3-center-valid-until-third-points','409-b001','作者8月6日仍把波动视7月3日后大中枢震荡，未有针对该中枢三类买卖点前继续按震荡。','走势中枢|第三类买卖点|中枢震荡|确认',1,'对应特定大中枢，不把小级别已跌破当大中枢三卖；需要明确同一对象。',['2008年8月6日7月3日后所述大中枢'],figs=((408,1),))
c(106,'aug8-am-second-buy-2762-three-day-branches','409-b003','8月8日早作者说前日包含K构短线二买并回5日线附近；中长阳过2762可确认笔，仍在其下则最晚下周初中继中枢扩展完后续跌，关注当日起三天。','第二类买点|包含关系|笔|均线|完全分类',2,'早盘条件预测不登记当日已确认笔，中继扩展照原措辞不擅改同级延伸；三天非普适时间上限。',['2008年8月8日早所论2762临界结构'])
c(106,'aug8-fourth-test-ninety-five-author-estimate','409-b004','作者称当时已三次探底，若第四次探底，破底概率至少95%。','概率原则|确认|操作策略',3,'95%是作者当时估计，没有样本/统计检验，不发布为项目胜率或任何四底必破定律。',['2008年8月8日该三次探底后的假设'],ambiguity='author_probability_not_independently_verified')
c(106,'aug8-capability-buy-point-exit-or-cost-bench','409-b005','作者要求见买点介入、冲不上先退出；没短线能力者可按情况用原持仓做差价降成本，或小板凳，自己按能力选择。','操作熟练程度|仓位|成本|操作策略',1,'见买点和冲不出是联合节奏，不将唯一正确/降成本修辞当无风险，也不把存在持仓的方法变为必须新开仓。',['2008年8月8日所论行情','按各自能力及是否已有持仓选择'])
c(106,'aug11-am-force-two-paths-one-or-more-centers','410-b001','作者称2762下三角为2924下跌首中枢；比较30或60分钟两段力度，后段更强则还需另中枢后下跌背驰才能完成；反之2924下来为单中枢盘整，后快回2679上。','走势中枢|下跌|盘整|背驰|完全分类',1,'后段强弱是相应图上比较，未在此给面积/斜率/阈值算法；反之按原文，不能擅以EPS或MACD单一数替代全部结构。',['2008年8月11日早该2924下降及30/60分钟力度比较'],figs=((411,1),))
c(106,'aug11-am-major-center-break-needs-complete-retest','410-b002','8月11日早7月3日中枢尚未三卖，仍可看震荡；要彻底破坏，须2924起向下次级别类型完成后，其次级别反弹不能回该中枢。','走势中枢|次级别|完成|第三类卖点|确认',1,'次级下跌完成、其后次级反抽不回是联合确认链，小级别跌价不自动确认大中枢三卖。',['2008年8月11日早该7月3日大中枢'],figs=((410,1),))
c(106,'aug11-am-type-end-at-least-same-level-rebound','410-b003','作者将2924起走势类型结束点视为该周最大短线机会，认为其后至少有2924这段同一级别的反弹。','完成|级别|反弹|确认',1,'结束是前提，至少与同级对象不能省；作者判断非项目独立证明或保证交易可获利。',['所论2924起走势类型实际结束'],figs=((410,1),))
c(106,'aug11-pm-green-growth-first-case-strengthening','411-b001','8月11日下午作者以60分钟绿柱持续伸长判断动能强，认为早间第一种较强下跌分支成立的可能不断增大。','MACD|完全分类|确认',2,'原文越来越演化必然为作者当时倾向，未据此把第二中枢已成/下跌已完全部确认，未来图不作当时证据。',['2008年8月11日下午该早间力度两支'],figs=((411,1),))
c(106,'aug11-pm-second-center-bounce-worst','411-b002','作者最坏支是先反弹构2700中枢破位后的第二中枢，力度可能连当日高点都碰不到，随后再跌；第二中枢后真背驰才有更高买点，文中说至少可成30分钟笔。','走势中枢|背驰|反弹|笔|级别|完全分类',1,'构第二中枢反弹与其后背驰反弹分开，原句买点最小第二中枢级别的参考需对照后段；明后日/下周的时限为作者预测。',['2008年8月11日下午该最坏情景'],figs=((411,1),),ambiguity='rebound_numbering_and_pronoun_reference_scope')
c(106,'aug11-pm-whole-2924-end-next-major-third-sell','411-b003','作者另强调只到2924第二中枢级别反弹仍可能再跌背驰，待2924下跌完成后，7月大中枢的次级别反抽才决定三卖；若成三卖其后风险更大。','走势中枢|背驰|次级别|第三类卖点|完成|反弹',1,'不同反弹层次与完成先后不合并；这个反弹的代词范围需结合8/13明确说明，不替作者补唯一分级表。',['该2924下跌内部与7月大中枢的不同层次'],ambiguity='rebound_numbering_and_pronoun_reference_scope')
c(106,'aug11-fourth-test-weak-consolidation-example','411-b005','作者8月11日说上海也是四次破底，只是第二底低于6月20日第一底，这是弱势盘整常见情况，盘整形态以后再讲。','盘整|高低点|确认',2,'原文弱式措辞/两底不同位置不改成四个等低点；不是对95%的独立统计验证。',['2008年8月11日所论上海弱势盘整'])
c(106,'aug12-prediction-as-leveled-boundary-classification','412-b006','作者8月12日解释其所谓预测为各种级别边界条件的完全分类、操作分类图；节奏来自清楚级别，没级别买卖点也无意义。','走势预测|级别|完全分类|操作策略',1,'这是本段预测的专用解释，不把旧市场方向预测/概率自述全改称已验证分类，也不自动撤销105预测不等实际走势的原话。')
c(106,'aug12-pm-second-center-bounce-now-recorded','413-b001','8月12日下午作者记录已出现盘中反弹，构造2700中枢破位后的第二中枢反弹。','走势中枢|反弹|确认',2,'当天原句才记出现，不由此前后加图反填8/11已成；构造中枢的反弹不等整段2924下跌已完。',['2008年8月12日下午该盘中反弹'],figs=((413,1),))
c(106,'aug12-break-center-diverge-or-third','413-b002','后续若跌破该第二中枢，作者分真背驰见更大底/反弹，或无背驰继续跌出第三中枢两支，并称后一支一般不超10%。','走势中枢|背驰|完全分类|反弹',1,'不超10%为作者未核概率；是否真背驰须当下核结构，不能把未见背驰一刻当永不背驰或据概率删分支。',['2008年8月12日该第二中枢向下破的条件支'],ambiguity='author_probability_not_independently_verified')
c(106,'aug12-direct-third-buy-no-c-still-down','413-b003','另一支是直接从该中枢三买扩成较大反弹，等于a+A+b+B+c中c不出现；作者说只要A、B在，a、c可不出现而不改所述下跌性质，趋势盘整区别在中枢数量。','第三类买点|走势中枢|下跌|盘整|走势分解|完全分类',1,'A/B指该标准下跌里已合法成立的相应中枢，不把任意两个重叠框直接当趋势；c缺失不能改说第二中枢也可缺。',['该所论下跌结构的A、B中枢已成立'])
c(106,'aug12-direct-third-buy-at-most-ten-estimate','413-b004','作者对第二种从中枢直接三买扩大的情景也估不超10%，并要求分清三买三卖。','第三类买点|第三类卖点|概率原则|完全分类',2,'两个10%的条件基准未明，不自行相加推得常规支80%；都非项目实测频率。',['2008年8月12日该直接三买反弹支'],ambiguity='probability_conditioning_and_sample_not_supplied')
c(106,'index-stock-rhythms-may-differ','413-b005','作者说明个股与指数节奏可能不同，必须各自分析。','板块轮动|操作策略|级别',1,'不可把指数短差点位直接当所有个股买卖点，板块类别均值也不能取消个股结构。')
c(106,'aug13-am-fractal-upper-boundary-simple-observation','414-b001','8月13日早作者让超短线看30/60分钟底分型后上边沿是否有效站住，未站则继续探底；称这为一般操作的简便观察，更深入者有更精确方法。','底分型|周期K线图|确认|操作策略',1,'后续8/14明确其为判断延伸笔而非最佳买点；保留本日一般观察范围，不直接当原理上足够的买入信号。',['2008年8月13日早一般超短线观察'],figs=((413,1),))
c(106,'aug13-pm-second-rebound-means-forming-b','414-b003','8月13日下午作者明确当天为三级反弹中的第二个，即构成2924下来第二中枢的反弹，要求从15/30/60分钟图对照。','反弹|走势中枢|周期K线图|级别',1,'这里第二是该八月结构层次，不自动等4月以4778/4196两段力度分级的第二；作者当日文字而非后加图才确认。',['2008年8月13日下午所论三级反弹'],figs=((413,1),))
c(106,'aug13-larger-rebound-diverge-or-direct-and-skill','414-b004 414-b005','更大反弹即前大中枢次级反抽，仍可由更大底背驰或当前中枢直接上去；作者说本周已有第二级别不是最恐怖支，能者先退第二再找第三，未达者继续练。','次级别|反弹|背驰|走势中枢|操作熟练程度|完全分类',1,'退第二/抄第三为能力条件方法，尚待最大反弹不记已成，第二/第三只限本次结构参考。',['2008年8月13日该三级反弹','具备相应识别和执行能力'])
c(106,'aug14-boundary-hold-not-best-buy-point','414-b009','作者8月14日明确分型上边沿站稳不是最佳买点，只是是否延伸为笔的简便判断；买点须从走势类型判别，边沿最多类似三类点，照此买可能第二根K就转折。','分型|笔|走势类型|第三类买卖点|确认|操作策略',1,'最多类似不等已经满足严格三类点定义；此处有明确解释，限制的是边沿用法，不自动撤回全部分型方法。')
c(106,'aug14-six-bars-fourth-confirm-fifth-turn','414-b009','作者举抛去包含时6根K可成笔，确认站稳边沿至少第4根、转折在第5根，用来解释单用边沿作为买点可能很快反向。','分型|包含关系|笔|确认',1,'这是原文计数说明，需与62/81标准并列；不据此静默把81极值K间至少3根改为2根，也不报已统一最少K数算法。',['该段抛去包含关系的计数示例'],ambiguity='six_bar_minimum_vs_l081_joint_rule_scope')
c(106,'aug14-multilevel-fractal-nesting-not-single-edge','414-b010','作者说方法须懂范围；课程中用不同级别分型、类似区间套确定买卖点的方法，不等单纯上下边沿判断。','分型|级别|区间套|确认|操作策略',1,'不把不同方法同名合并，本文未重新给该分型区间套全部算法；没有唯一买点保证。')
c(106,'aug15-day-bottom-2484-five-day-branches','415-b001','8月15日作者称前日包含、当日成日底分型，2484为短线关键；下周初不站可能周一低开探底，5日线有效跌破确认探底，否则撑住有更大反弹扩展机会。','底分型|包含关系|均线|确认|完全分类',1,'日底已成与笔/2484站稳不同；正文2484不改图2484.7，日期校8/15，不将未来图反填周一选择。',['2008年8月15日该日底/2484/5日线情景'],figs=((415,1),))
c(106,'aug18-edge-failed-divergence-or-third-center','415-b004','8月18日作者记周五日底上沿未站而续探底，称通常90%情景；随后若不能形成背驰就先第三中枢，若跌势力度延续该支可能大，反之次级反弹展开。','底分型|背驰|走势中枢|次级别|完全分类',1,'90%只是作者未核估计，未来两日力度未定，不把未确认反弹记已结束大跌。',['2008年8月18日该边沿失败后结构'],figs=((415,1),),ambiguity='author_probability_not_independently_verified')
c(106,'aug18-sublevel-rebound-third-sell-risk','415-b005 415-b006','作者提醒该次级反弹可能只成原大中枢三卖，之后更猛烈下跌，三卖后最好也只构更大中枢；最弱平台反弹甚至不触2500。','次级别|反弹|第三类卖点|走势中枢|完全分类',1,'可能、最弱/最好条件均保留，不能把次级反弹当长期反转；基本面/奥运时点因果为作者预测未外核。',['2008年8月18日该次级反弹的条件展望'])

keep('401-b006 414-b009','lower-l062-stroke-separation lower-l081-c-stage-new-stroke-two-joint-conditions','106六根措辞及去包含计数，与62独立K和81包含后不共K/极值之间至少3根联合条件并列，未明说撤回81，不能按日期静默覆盖。')
keep('402-b001','lower-l063-chart-period-not-center-level lower-l072-c-stage-averages-auxiliary-horizons','均线与级别仅大致对应，早期辅助均线与形态学/动力学仍有区分，不能定式换算。')
keep('402-b007 404-b003','lower-l105-c-stage-jul9-moving-average-classification-homework','7/10给出前课7/9均线分类作业的具体标准和类别平均指标，保留原题日期并建立后续来源线索。')
keep('404-b007 405-b001','lower-l079-c-stage-top-fractal-not-necessarily-stroke lower-l081-c-stage-rotate-after-sell-wait-buy','顶分型未必成笔，轮动须买卖点及能力，不以板块强弱指标替代。')
keep('406-b003','lower-l094-c-stage-t1-same-day-exit-impossible-risk lower-l105-c-stage-jun10-prediction-game-operation-absolute-wording lower-l100-c-stage-ability-only-quantity-author-general-claim','106明确T+1限制小级别精确操作，支持把规则明确/仓位数量与实际执行条件分开，未直接全局撤回旧说法。')
keep('412-b006','lower-l105-c-stage-forecast-not-market-no-hundred-percent lower-l068-c-stage-operations-piecewise','本段预测专指分级边界条件完全分类，不把作者全部数值方向预测的非100%性质删掉。')
keep('414-b001 414-b009','lower-l105-c-stage-jun19-nesting-entry-boundaries-for-exit lower-l102-c-stage-mar19-3775-fractal-to-stroke-still-conditional','站边沿可观察成笔，不等最佳入场；区间套入场与持有退出边界分开，解释有明确后文，不凭日期全局覆盖。')
keep('411-b003 414-b003','lower-l105-c-stage-apr18-three-rebound-strengths-not-chart-periods','4月三级反弹是以两段历史力度分级，8月第二指2924第二中枢反弹，不能把相同序号强行同一对象。')

issue('six-bars-and-new-stroke-counting','401-b006 402-b000 414-b009','106说至少6基本K以及去包含6根可笔，62实用独立K/81新笔极值间至少3根仍有联合计数范围；106无明确撤回81文字。','原句和条件并列，标歧义，不改现有新笔标准，不对全级别补已证明最少时间表。',True)
issue('classification-history-threshold-and-strongest-question','402-b007 403-b000 403-b002 404-b000','本次反弹未曾攻克最小周期是历史进程标准，攻克阈值、反弹起点及最强不一定当前全在线上之设问未给完整算法。','不改成当前价在线数，不擅填唯一阈值；成员名单与600578图类6/文类7分别保留。',True)
issue('sector-average-system-scope','402-b003 402-b005 404-b003 404-b004 404-b005','5/13/21/34/55/89/144/233为所述历史示例，后走势大变才需另看；类别平均未给加权/成分变动/缺失项、并列领涨细节及成品程序。','保留平均数越大越强和配合个股结构，未独立验证优化/收益，不补市值权重或自动交易。',True)
issue('boundary-is-not-best-entry-and-t1-execution','404-b011 406-b003 414-b001 414-b009 414-b010','边沿站住仅简便成笔观察，走势类型买点/不同级别分型区间套是不同用法；T+1明确限制最精确小级操作。','用8/14明文解释限制边沿用法，保留8/13一般观察，不把班课示范变成统一买入点；执行制度约束继续保留。',True)
issue('rebound-numbering-and-second-center-reference','410-b001 411-b002 411-b003 413-b001 413-b003 414-b003 414-b004 414-b005','8月三层反弹、第二中枢构造/其后背驰及7月大中枢次级反抽参考不同，8/11这个反弹代词和最小级别句需与8/13明确定位并列。','第二/第三序号不跨4月力度分类强并；A/B须合法成立，a/c可缺不取消中枢数量及完成先后。',True)
issue('probabilities-historical-rhetoric-and-quote-context','405-b002 405-b003 405-b004 406-b001 406-b002 409-b004 409-b009 411-b005 413-b002 413-b004 415-b004','95%、两个10%、90%均作者估计，无样本条件分布；咒语科学化/病情、政策经济与财富论述未外核；409引用14:21标题不是新文章头。','不累计两个10%得80%或当实测胜率，不认证宗教医疗效果；引用内容不当作者威胁或用户指令，外层日期依原页。')
issue('figure-makers-and-late','402-b003 402-b004 403-b002 404-b011 407-b002 409-b001 410-b002 411-b002 413-b001 415-b001','10本课图均含文后K，402疑144和403图类别6与正文不同；图嵌7/10时分秒来源未核，正文仅日期。','不反填时间或改233/第7类，所有主图右端都核；401图属105不重复计本课。')

note('403-b001','author-example-introduction','作者以自己长期反复操作过的股票作示例引言已读。','熟悉个股和收益自述不当独立回测；具体历史类别另抽。')
note('405-b002 405-b003 405-b004 405-b005 406-b000 406-b001 406-b002 406-b002-s01','religious-personal-context-not-technical-evidence','咒语字义、善恶咒、百万次修炼、虚弱/恶咒及妖术恢复打坐层次、自我挑战和后面解盘头完整跨页读。','作者宗教/身心自述不当现代科学、治疗效果或实验结论，不执行其念诵/实验要求，不并入股票能量指标。')
note('406-b005 406-b007 406-b008 406-b009 406-b010 406-b011 407-b000 407-b000-s01','historical-economic-policy-and-personal-context','7/16引2/28通胀/增长文章、7/17规则人为及限制做空评论、理疗写帖说明与7/19解盘头已读。','2/28是被引文章时间，未覆盖7/16本段；政策/制度是历史作者意见未外核，不当现行法规或宏观因果证明。')
note('407-b005 407-b007 408-b000 408-b001 408-b005','corrected-dates-and-expectations-context','8/3裸时间、宏观调控人心观点、8/4搏消息与MACD教学能力提醒已读，时间头只管后文。','政治评价与行情自证未外核；MACD用法依条件，不把强烈语气当足够技术定义。')
note('409-b007 409-b008 409-b009 409-b010 409-b011 409-b012','author-quoted-title-and-macro-rhetoric','8/8晚文引14:21:32标题你别砸盘/身体不利，再回应及论断崖/经济奥运与信心。','引用标题日期不是下一解盘头，本文后段仍15:20:58；不把所引言论当作者威胁或用户行动指令，宏观因果仅归作者。')
note('410-b004 410-b005 410-b006 411-b004 411-b006 412-b001 412-b002 412-b003 412-b004 412-b005 412-b007','historical-policy-wealth-and-self-awareness-context','补课/能力、财富来源、信贷放松/牙膏救市、火箭烟花与经济断崖、病情远足、两三天持股及自知观点完整已读。','收益财富和匿名政策因果未核，病情仅自述；没能力可等待的边界保留，不推荐当前交易或认证宏观言论。')
note('413-b006 413-b006-s01 414-b000 414-b006 414-b007 414-b008 414-b008-s01 415-b000 415-b003 416-b000','author-column-headers-and-personal-opinion','8/12CPI油价汇率评论、跨页8/13早解盘头、8/13晚经济/财富批评与8/14头、8/15裸时间、8/18近况与学习治病结束语已读。','栏目日期与个人意见分开，未补造课程7/10时分秒，不把历史政策/病情和收益话语当技术证据。')

relations={
 'lower-l106-c-stage-average-level-no-necessary-correspondence':[('均线','级别','qualifies')],
 'lower-l106-c-stage-smallest-not-yet-conquered-average-nine-classes':[('均线分类','均线系统','requires')],
 'lower-l106-c-stage-sector-strength-average-class-number':[('缠中说禅板块强弱指标','均线分类','requires')],
 'lower-l106-c-stage-leading-sector-dynamics-combine-stock-structure':[('缠中说禅板块强弱指标','板块轮动','related')],
 'lower-l106-c-stage-jul14-t1-limits-precise-small-level-operation':[('T+1','操作级别','qualifies')],
 'lower-l106-c-stage-aug14-boundary-hold-not-best-buy-point':[('分型','走势类型','qualifies')],
}
for r in rows:r['relations']=[{'source':s,'target':t,'type':kind} for s,t,kind in relations.get(r['id'],[])]

by_passage=defaultdict(list)
for r in rows:
    for e in r['evidence']:by_passage[e['passage_id']].append(r)
for item in pending:
    item['lesson_numbers']=sorted({int(passages[x]['unit_id'].split('-')[1]) for x in item['passage_ids']})
    if item['id'].endswith('figure-makers-and-late'):
        item['lesson_numbers']=[106];item['figure_ids']=[f['id'] for f in figures]
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
      'related_existing_claim_ids':retained_ids,'note':'均线分类历史攻克与当前位置、板块平均及个股点位分开；6根与81条件、边沿成笔非最佳买点、T+1和三层反弹保留原范围。'},'4_reverse_check':inverse}})
for f in figures:
    key=(f['pdf_page'],int(f['id'].rsplit('fig',1)[1]))
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=figure_notes[key],
      figure_source_review='十图均后加见stage-c-l106-source-applied.json；401上一课图不重算；233/144与第7/第6类图文差异分开，正文独立支持不倒填确认。',
      linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger)==125 and len({x['passage_id'] for x in ledger})==125
def dump(suffix,data):
    (OUT/f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x,ensure_ascii=False,separators=(',',':')) for x in data)+'\n',encoding='utf-8')
dump('reviewed.jsonl',rows);dump('coverage.jsonl',ledger);dump('pending.jsonl',pending);dump('figures.jsonl',figures)
summary={'stage':'C','schema_version':metadata['schema_version'],'graph_version':metadata['graph_version'],'lessons':[106],'document_id':DOC,'reviewer':REVIEWER,
 'passages_read':125,'claims':len(rows),'evidence':sum(len(r['evidence']) for r in rows),'importance_counts':dict(Counter(r['importance_level'] for r in rows)),
 'new_concepts':sorted({x for r in rows for x in r['concepts']}-set(concepts)),
 'whole_lesson_semantic_read_complete':True,'technical_extraction_complete':False,'four_round_review':True,'independent_review_claimed':False,
 'visual_pdf_pages':list(range(401,417)),'figure_objects_viewed':10,'adjacent_figure_viewed':{'id':DOC+'-p0401-fig1','unit':'lesson-105','counted_in_batch':False},'figure_origin_counts':dict(Counter(f['origin_status'] for f in figures)),
 'pending':[x['id'] for x in pending],
 'source_passages_snapshot_sha256':SOURCE_SHA,'retained_source_links_in_ledger_only':True,'database_mode':'ro','formal_import':False,
 'acceptance':'125段四轮审读、16页10本课图+1邻课边界；23日期及10后加图校核，均线九类/类别平均、边沿范围、T+1及多层反弹分开，增量待预检发布。'}
(OUT/f'{BASE}.summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
db.close();sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(summary,ensure_ascii=False))
