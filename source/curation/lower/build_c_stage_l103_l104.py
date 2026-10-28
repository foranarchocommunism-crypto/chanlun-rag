"""Materialize the manually read lower 103-104 batch; SQLite is read-only.

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
BASE='c_stage_l103_l104'
REVIEWER='Codex 主代理 / 阶段C下册103—104课同模型四轮复核'
SOURCE_SHA='f9b31e71b0e1e547a02fac3749b75d9d8051004892604445bb74fb3be84ceeca'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
db.row_factory=sqlite3.Row
metadata={r['key']:json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version']=='1.1.0'
assert hashlib.sha256((KB/'sources/volume_2.pdf').read_bytes()).hexdigest()=='5332cd1b60381c47ceb81358db6bbb47882efd074fc5c869dcc3002aaed1b5c0'
passages={r['id']:dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id BETWEEN 'lesson-103' AND 'lesson-104' ORDER BY pdf_page,block_index,id")}
assert len(passages)==154
assert hashlib.sha256(json.dumps(sorted(passages.values(),key=lambda p:p['id']),ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==SOURCE_SHA
old={r['id']:dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts={r['label']:dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical={label:r['label'] for r in concepts.values() for label in [r['label']]+json.loads(r['aliases'])}
figures=[dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 366 AND 382 ORDER BY pdf_page,id',(DOC,))]
assert len(figures)==13
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
    pending.append({'id':'lower-l103-l104-c-stage-pending-'+slug,'status':'pending','passage_ids':[pid(s) for s in shorts.split()],
                    'description':description,'suggested_action':action,'blocks_full_semantic_extraction_completion':blocker,'reviewer':REVIEWER})




c(103,'macd-zero-defense-corresponding-chart','366-b007 366-b009 367-b001','第103课作者以MACD零轴划分对应时间图表的多空主导，要求基本防守回避黄白线在零轴以下的市场或股票。','MACD|周期K线图|操作策略',1,'是防守过滤方法而非背驰的定义；须合读最低周期由能力决定、高手可背驰介入的例外，不推广成所有人任何周期绝不可介入。',['第103课初学防守方法及对应图表时间周期'],exceptions=['技术较高者可在背驰情况下介入'],figs=((366,1),),ambiguity='macd_defense_filter_vs_general_indicator_necessity')
c(103,'macd-defense-lowest-period-by-capability','366-b010 367-b000','1分钟MACD常在零轴上下反复；防守者可按能力选最低时间周期，例如60或30分钟图，所选最低周期MACD入零轴下便离开，直到重新站住零轴。','MACD|周期K线图|操作熟练程度|操作策略',1,'跨页合读；60/30为例，不是统一最低周期或按K时间机械定义结构级别。',['先按自身能力选定最低图表时间周期'])
c(103,'macd-defense-skilled-divergence-exception','367-b001','作者明确允许技术较高者在背驰情况下介入，但第103课为降低要求而把防守方法简化；连黄白线零轴位置都看不懂者应离开。','MACD|背驰|操作熟练程度|操作策略',1,'高手例外有原句，不静默删除；简化防守与17课指标辅助非必要属于不同方法范围。',['第103课防守方法的能力层次'],ambiguity='macd_defense_filter_vs_general_indicator_necessity')
c(103,'mar19-sixty-zero-down-example','366-b008','作者以60分钟图从5200附近MACD跌破零轴且反抽确认后至3000多点仍在零轴下，说明该防守术的历史案例。','MACD|周期K线图|确认',2,'价格为作者粗略叙述，未独立重建全部交易路径；图制作身份未核，不能用案例证明普遍充分有效。',['2008年3月19日作者所述60分钟图案例'],figs=((366,1),))
c(103,'mar20-3775-not-passed-trend-continues','367-b004','3月20日作者说3775未过，所以原趋势继续；同时将当时行情判断为宽幅底部区域、洗盘可给题材轮动机会。','确认|中枢震荡|板块轮动|操作策略',2,'底部区域/洗盘是当时作者判断，不等笔或完整底部已确认，也不证明企业资金行为。',['2008年3月20日该3775与行情语境'])
c(103,'annual-rhythm-greater-next-rise-author-forecast','367-b009 367-b011','作者以4778至5522及随后下跌对应年初扬、抑，并预言这轮5522起抑结束后大扬的幅度将大于前述扬。','价格区间|完全分类|操作策略',3,'是2008年展望中的作者预测，尚非项目验证结果；未来幅度断言不等任何品种实际收益保证。',['2008年3月20日作者年度展望'])
c(103,'3600-scale-targets-4922-3424-author','367-b010','作者按3600幅度尺度谈节奏：把5522说成6124下来600点、1/6，把4778说成下来1345点、3/8，进而关注4922压力及6/8位置3424底部可能。','价格区间|操作策略',3,'原数照录，6124与5522/4778的差并非精确600/1345；作者的近似节奏不能冒充精确恒等式，3600是幅度尺度非中轴价。',['该节奏继续保持的历史预测语境','3424底部可能以无特殊全球崩盘事件为条件'],exceptions=['特殊全球性崩盘事件'],ambiguity='author_reported_rounding_and_unverified_price_rhythm')
c(103,'annual-average-turn-conditional-large-down','368-b001','作者在年线仍向上背景下预计大扬反击年线；若年线走平时仍未重回其上，转头向下后才是真正大调整；若大扬未能在转头前重站并带动上扬，后续大抑更强。','均线|确认|完全分类|操作策略',2,'此处年线为文中技术年线指标，不等年级别走势中枢或一根年K；作者条件展望未独立验证。',['2008年3月20日年线仍向上的情景'])
c(103,'monthly-macd-cross-even-return-risk','368-b002','作者以月MACD刚死叉为条件说，即使大扬重站年线，也可能只是推迟其转头，最好形成MACD双头，后面仍有更大下跌。','MACD|均线|完全分类',2,'是历史条件预测，不当已证明MACD双头必跌或所有重回年线无效的通则。',['2008年3月20日月MACD刚死叉的情景'])
c(103,'monthly-zero-next-major-market-wording','368-b003','作者从直观技术上说，下一轮真正大行情必须等月MACD回到零轴附近才可能展开，期间只是小打小闹。','MACD|确认|操作策略',2,'必要措辞限该历史中长线展望，与103高手背驰例外及17指标非必要并列，不自动统一为图谱所有行情的必要充分条件。',['2008年3月20日下一轮大行情展望'],ambiguity='macd_necessary_wording_vs_auxiliary_scope')
c(103,'twenty-year-view-survival-prerequisite','368-b009','作者从20年角度仍把这次调整看作超级牛市中继，但强调前提是参与者能熬过调整，否则长远牛市对该人无意义。','资金管理|操作策略',3,'牛市与20年为作者历史视角和预测，不作已验证长期市场规律；生存前提不能省。',['2008年3月20日作者20年视角','参与者能熬过所论调整'])
c(103,'mar21-three-percent-touch-not-final-bottom','369-b001','作者以目标3424上下3%范围解释前日低点可视为触及有效，并说直接上去也符合其技术看法。','价格区间|确认',2,'3%是作者此处价格目标容许空间，不等EPS、笔极值或所有中枢相交边界都可放宽3%；下一段仍允许探底，不能据触及确认最终底。',['2008年3月21日对3424目标的解释'])
c(103,'mar21-3780-sixty-fractal-to-stroke','369-b002','3月21日作者仍保留再次探底；3780为新60分钟底分型上沿，站住后至少在60分钟图延伸向上笔，才对应其单脚反弹分支。','底分型|笔|周期K线图|确认|完全分类',1,'3780是新分型边沿，不自动改写3/19的3775；底已见与笔待站边沿分别记录，不替代81新笔完整条件。',['2008年3月21日新60分钟底分型'],figs=((369,1),))
c(103,'mar21-3780-thirty-sixty-macd-two-paths','369-b003 369-b004','3月21日30分钟MACD在零轴受阻；下周初若站住3780，作者预期突破零轴并带动60分钟冲击零轴，若不站则零轴受阻回跌再探底。','MACD|周期K线图|完全分类|确认',1,'两支及下周条件照留，不用4月图提前决定当时选哪支，不以指标替结构确认。',['2008年3月21日该3780与30/60分钟图'],figs=((370,1),))
c(103,'mar21-daily-3941-not-sixty-3780','369-b005','作者说当时日线底分型上沿3941决定反弹级别能否扩展，站住后可回原60分钟3—4类中枢。','底分型|类中枢|笔|周期K线图|确认',1,'日3941与60分钟3780是不同图上分型对象；不把级别扩展改成严格中枢已升级。',['2008年3月21日日线分型及3941'],figs=((369,1),),ambiguity='chart_period_fractal_vs_strict_structural_level')
c(103,'mar24-3780-break-retests-third-sell','370-b003','3月24日作者记跌破3780后两次反抽未上、确认有效跌破，下午2点标准第三类卖点成立后跌幅加大。','第三类卖点|确认|操作策略',1,'有当天原文才登记已确认；三卖级别此段未明给，不能凭五分图就自动指定严格5分钟。',['2008年3月24日该3780结构'],figs=((371,1),))
c(103,'mar24-exit-or-bench-capability','370-b004 370-b006','作者把3780失守或最晚三卖退出视为本次短差退出；若破技术位还不愿走，建议先小板凳等待。','第三类卖点|操作熟练程度|操作策略',1,'作者收益和成功评价非账户验证；能力门槛与价格结构必须同读，不给任何人收益承诺。',['2008年3月24日此前抄底仓位语境'])
c(103,'mar24-base-position-depends-capital','370-b005','作者认为当时在中线底部震荡区域，每次震荡后可沉淀一定底仓，但取决于各自资金量。','仓位|资金管理|中枢震荡',1,'底部区域为作者当时判断，资金量条件及一定比例未量化，不推广任意散户无限补仓。',['2008年3月24日作者判断的底部区域','按各人资金量决定底仓'])
c(103,'mar24-low-price-double-bottom-volume-conditions','370-b008 371-b000','作者所论下一次选择仍为短跌40%以上的中低价中小盘股，并加双底支持、新资金介入迹象，即放量后有缩量站住。','成交量|价格区间|确认|操作策略',1,'条件联合，40%由前次偏好与本次选择语境产生，不单独成为买点定义；具体天鹅涨停为作者自述。',['2008年3月24日所论下一次选股','中低价中小盘、短跌40%以上、双底支持、新资金放量后缩量站住'])
c(103,'mar25-3616-down-3780-up','371-b006 371-b007','3月25日作者给3616为超短线下方关键，再有效跌破会破底；上方仍为3780，未有效突破仍只底部徘徊。','确认|完全分类|操作策略',1,'3616与3780分别对应当天上下边界，不把任意一次盘中触价当有效站/破。',['2008年3月25日该3616/3780情景'])
c(103,'mar25-five-to-thirty-macd-exit-condition','371-b008','作者3月25日预期5分钟MACD从零轴起来可带30分钟再次冲击零轴，若出现又在30分钟零轴受阻，应择机退出当天买入部分。','MACD|周期K线图|操作策略|完全分类',1,'是次日条件计划，不提前登记已完成；后日实际只带15分钟是不同时间状态，不静默改原30。',['2008年3月25日所论次日5/30分钟图情景'])
c(103,'large-fund-dynamic-cost-and-chips','372-b000','作者称大资金应沉淀适当筹码，以成本不断降低、筹码不断增加进行动态建仓。','资金管理|仓位|成本|操作策略',1,'是作者操作原则，未给保证可实现的资金/流动性/交易参数，也不取消相应风险。',['2008年3月25日所论大资金建仓'])
c(103,'mar26-five-consolidation-only-fifteen-zero','372-b002','3月26日作者说早盘标准盘整背驰，5分钟MACD红柱小于前组，只带15分钟MACD回零轴受阻，随后回落。','MACD|盘整背驰|周期K线图|确认',1,'当日原文为15而前日预期30，按日期保留，不校成同一周期；红柱比较为该案例不直接定义全部背驰。',['2008年3月26日该5/15分钟图案例'],figs=((372,1),))
c(103,'warrant-no-chase-expiry-warning','372-b003 372-b004','作者说580989收盘到0.8附近已远离其0.6中枢、风险极大，当天未介入者不得再介入，并强调权证高度投机及还有两个多月到期。','中枢震荡|操作策略|资金管理',1,'价格/期限为当时作者记载未外核；稳赚修辞不作为收益证明，不转为当前交易推荐。',['2008年3月26日580989该行情及到期语境'])
c(103,'warrant-07-center-next-divergence-reference','372-b003','作者说580989在0.7附近小级别背驰后回次级别中枢、形成更大中枢，所以随后上涨是否背驰以0.7附近中枢为比较基准。','背驰|走势中枢|级别|操作策略',2,'0.6前期中枢、0.7本次比较、0.8已远离三种对象分开；具体级别未给，不能把金额当严格级别。',['2008年3月26日580989案例'])

c(104,'geometry-energy-dynamics-author-program','373-b002 373-b008','作者在第104课称其理论在数学和物理角度完美，并说其能量动力学结构从现代物理视角构建，一切能量动力形态应几何化，具体方法以后再说。','几何结构|能量结构|动力学|技术分析',2,'这是作者理论纲领与自评，此处未给可复现能量函数、量纲、方程或实验，不作现代物理支持市场预测的证明。',ambiguity='physics_analogy_no_formal_market_mapping')
c(104,'mar27-3424-not-yet-effective-break','373-b010 373-b011','3月27日作者以580989上次启动类比，若继续同样则指数下探后回破位前平台；因3%容许空间，当时不能说3424已有效破，若破则关注2500。','价格区间|确认|完全分类',2,'若继续同样为类比条件，2500为后续作者目标非项目预测，不把历史相似当必然复刻。',['2008年3月27日该3424与历史类比情景'])
c(104,'mar27-low-price-range-moves-with-market','374-b002','作者说市场重心下移时，关注的低价股价格也应下移，而其低价、题材与来回操作原则不变。','价格区间|题材股|操作策略',2,'所论低价非固定永远7/8或20阈值，未给统一移动公式或价值估计。',['2008年3月27日作者选股语境'])
c(104,'broken-issue-price-needs-skill-and-policy','374-b003','作者认为破发板块从投机角度有机会，但需要较高操作水平和政策敏感度，没有相应水平者不必关注。','操作熟练程度|政策风险|操作策略',1,'机会不等无风险折价，能力与政策条件不能由跌破发行价一项替代。',['2008年3月27日所论破发投机机会'])
c(104,'mar27-warrant-one-center-consolidation','374-b004 374-b005','3月27日580989冲高后回0.7中枢，作者据此说上冲仅一个中枢、为盘整，随后看第三类点，并再次让一般人远离该最后一波行情。','盘整|走势中枢|第三类买卖点|操作熟练程度',1,'30%回落与最后一波为历史记载，不能把任何一个图框自动当盘整完成；一般人远离限制保留。',['2008年3月27日580989该结构'])
c(104,'price-target-three-percent-author-convention','374-b007 374-b008','作者说任何技术位置都有上下3%的允许空间，以5678目标与实际5522举例，并继续按6124减2700即3424、3600的3/4谈底部位置。','价格区间|确认',2,'是作者价格目标惯例，不把3%作为本项目笔/中枢/EPS统一容差；作者目标命中说法未作为预测有效率验证。',['第104课3月28日所论价格目标方法'],ambiguity='price_target_tolerance_not_structural_epsilon')
c(104,'mar28-no-daily-fractal-no-final-bottom','374-b010','3月28日反弹连日底分型都尚不足形成，作者说传闻若下周未兑现仍可能杀跌回试，3424是否最终底部没有最终结论。','底分型|确认|完全分类|政策风险',1,'初步显威不等最终底部；有无日分型为当时状态，不能以后期图倒填。',['2008年3月28日该3424与日线状态'])
c(104,'mar28-3499-and-five-fifteen-condition','374-b011 374-b012','作者把3499作为超短线关键，站不住要再探底；下周看5分钟MACD红柱不能再伸且面积小于前组、15分钟零轴能否突破，失败会回试支持，高手可不等3499真破再走。','MACD|周期K线图|确认|操作熟练程度|完全分类',1,'5/15周期联合观察及高手提前退出不压成单一触价法；正文3499保留，不用图3499.2改字。',['2008年3月28日所论下周初情景'],figs=((375,1),(375,2)))
c(104,'small-fund-short-bite-large-chips-now','374-b013 374-b014 375-b000','作者区分小资金抓短机会、不延续先跑，与大资金此时需沉淀筹码；明确以前离底部远未要求沉淀，是最近才开始要求。','资金管理|仓位|操作策略|操作熟练程度',1,'时间/资金范围不能省；小资金一秒建好是修辞，大资金即使3424不是底也无所谓为作者风险态度，非无损保证。',['2008年3月28日作者所判断的阶段'])
c(104,'mar31-3499-current-center-next-day-two-paths','376-b001 376-b002','3月31日3499成为震荡中心但尾盘未站；次日能重站还有上行机会，否则继续探底，作者把其较强表现归于新资金。','中枢震荡|确认|完全分类',2,'当天震荡中心是价格语境，不直接认证严格中枢；新资金是作者解释未外核。',['2008年3月31日该3499结构'])
c(104,'mar31-quarter-down-stroke-only-probability','376-b004','3月31日月季线收盘时，作者说若这里不起来，季线上有极大机会形成向下笔。','笔|周期K线图|确认',1,'条件加极大机会不是季笔已确认；后加月季线图含未来低点，不填当日已成。',['2008年3月31日月季线收盘及不能起来的情景'],figs=((376,1),))
c(104,'apr1-3499-two-failures-next-skill-opportunity','376-b008 377-b000 377-b002','4月1日作者记早盘两次冲3499失败后下行，并说有本事者迎接破底后新短线机会，部分跌10%—20%的股票尾盘可回补、尤其大资金。','确认|操作熟练程度|资金管理|操作策略',2,'技术退出及能力、时段、资金范围照留，10%—20%不是通用充分买点。',['2008年4月1日该3499失败后情景'])
c(104,'apr1-channel-lower-break-rebound-author','377-b003','作者认为当时下降通道下轨可做短线，若破下轨加速则大反弹在前。','确认|反弹|操作策略',2,'是历史通道经验判断，未给画轨唯一标准或统计保证；后加图未来反弹不能证明无条件定律。',['2008年4月1日作者所画下降通道'],figs=((377,1),),ambiguity='channel_drawing_and_rebound_guarantee_unverified')
c(104,'apr2-hedge-style-not-formal-derivative-model','377-b008','作者称4月2日反弹后大震荡适合对冲式操作，或像前日所说于尾盘先介入。','操作策略|操作熟练程度',2,'对冲式在本段没有正式定义，不自行补衍生品、空仓对冲或资金参数；是历史操作建议。',['2008年4月2日该大震荡语境'],ambiguity='hedge_style_not_formally_defined')
c(104,'apr2-3462-fail-retest-and-t1-tail','377-b009 378-b000 378-b001','4月2日冲3462未站出现震荡，作者说再冲不过仍可破底；短线可高出回补，见不行先回，必要时为避T+1限制可在前一天尾盘打提前量。','确认|操作策略|操作熟练程度|T+1',1,'提前量为历史方法，不改变T+1制度或保证次日可盈利退出；尾盘先买须承担未确认隔夜风险，不补统一提前分钟。',['2008年4月2日该3462与短线操作'],figs=((378,1),))
c(104,'apr3-large-market-blueprint-only-rebound','378-b006 378-b007','作者说完整大行情需要一二三线轮动和中字头参与，但强调当时只是蓝图，实际行情未走出，暂按反弹处理，形势不对则反向处理。','板块轮动|反弹|确认|操作策略',1,'未来轮动构想不能当本年度最大行情已经成立或不再有下跌。',['2008年4月3日所论行情蓝图与现实'])
c(104,'apr3-daily-week-fractal-not-yet-known','378-b008 379-b000','4月3日3462尚未有效站住，作者把下周日周能否成底分型视为关键，并将短线简化为3462能否站稳。','底分型|周期K线图|确认',1,'日周分型当时仍待，不以后图4/7答案及行情确认本日已成；简化价格观察非替代完整分型定义。',['2008年4月3日该日周分型前景'],figs=((379,1),))
c(104,'apr3-homework-apr7-author-answer-3396','379-b002 380-b001','作者4月3日留作业问13:30至14:00站某位置后突破的技术意义；4月7日答只和60分钟底分型有关，3396突破后延伸出笔。','底分型|笔|周期K线图|确认',1,'原问与后来答各有时间，图中括注突破下降趋势线是未核制作者加字，不冒充作者答案；3396不与3462合为一价。',['4月3日该作业与4月7日明确答案'],figs=((379,1),))
c(104,'apr7-sixty-up-stroke-formed','379-b005','4月7日作者说突破3462后，60分钟图在数月来第一次延伸出向上笔，显示短线强势。','笔|周期K线图|确认',1,'这是当日文字登记的60分钟向上笔，不连带确认日笔或周笔；图后期制作不改变原日期结论。',['2008年4月7日该60分钟图'],figs=((381,1),))
c(104,'apr7-day-3613-week-fractal-likely-exception','379-b007','4月7日作者以3613能否突破观察日线向上笔；突破3555使周底分型形成可能性极大，但明确本周再破底例外。','笔|底分型|周期K线图|确认',1,'日笔未据此已成，周底极大概率未升为本周最终已确；3555与3613分别不同周期对象。',['2008年4月7日该日周图情景'],exceptions=['本周内再破底'],ambiguity='chart_period_fractal_vs_strict_structural_level')
c(104,'apr7-3613-not-broken-adjust-and-follow-chart','379-b008 380-b000','作者说3613攻不破可先调整筹码应对震荡，即使真是中线底部，在真正突破前仍会洗盘震荡，应按图作业、见一步走一步。','仓位|确认|中枢震荡|操作策略',1,'中线底部仍条件语气，不以先前3424预测取消此时退出/调整分支。',['2008年4月7日3613尚待攻击情景'])
c(104,'apr8-3613-and-sector-restart-conditions','380-b003 380-b004 380-b005 380-b006','4月8日指数围3613震荡、收3612.5；作者说站住续攻，否则大调整，同时观察先调的金融地产能否再启动，不能则至少调整。','确认|板块轮动|完全分类',1,'收盘接近不等站稳；具体板块顺序为当时案例，不作为全时期固定轮动规律。',['2008年4月8日该3613与板块状态'])
c(104,'apr8-one-fractal-method-demonstration','380-b008','作者说近期一直用各级别分型统一分析，是示范一招真正学会可解决绝大多数问题，并要求回看探底至回升过程。','分型|操作熟练程度|操作策略',2,'绝大多数为作者教学评价，不表示所有结构定义可省略或项目已验证全部交易可用单价规则。')
c(104,'apr9-top-fractal-break-3613-confirmed','380-b010','4月9日作者记60分钟跌破顶分型下边后早盘回抽未到3613，确认跌破有效，后续要形成向下笔。','顶分型|笔|确认|周期K线图',1,'有效破下边与回抽失败联合，不把盘中一跌直接认证所有周期转势；此处要形成与已经全部走完不同。',['2008年4月9日该60分钟顶分型'],figs=((381,1),))
c(104,'apr9-down-stroke-end-before-entry','380-b011 380-b012 380-b014','作者按向上笔后向下笔调整处理，向下笔结束前不宜再介入，结束后等新买点；不用先猜是洗盘还是继续下跌，只关心下个买点。','笔|完成|确认|操作策略',1,'等待笔结束与买点条件不省，不能把拒猜方向理解为任何下跌都可以买；作者完全把握为教学主张非项目实绩。',['2008年4月9日该60分钟图调整'])
c(104,'apr10-sixty-bottom-3533-two-paths','381-b001','4月10日作者称60分钟底分型已成，3533站上延续反弹、对应二次探底结束；站不住则再次探底且破底机会极大。','底分型|笔|确认|完全分类|周期K线图',1,'底分型已成与站上3533两支分开；3533按正文存，不改图中3534.6，也不自动确认为周底。',['2008年4月10日该60分钟底分型'])
c(104,'apr11-week-bottom-3840-stroke-or-relay','381-b005','4月11日作者称周底分型已形成，上边3840决定最终有效延伸向上笔，或失败仅成中继型。','底分型|笔|确认|周期K线图|完全分类',1,'周底已成不等周向上笔已成，3840条件及失败支并列；后一周图不预知其选哪支。',['2008年4月11日该周底分型'],figs=((382,1),))
c(104,'apr11-three-chart-boundaries-not-one-level','381-b006 381-b007','作者4月11日以3533为60分钟图关键、3613为日线对应位置、3840为周图关键，分别观察超短、短、中走势。','周期K线图|确认|操作级别|笔',1,'三价三图不同对象，原文称级别但此处图表分型不直接固定换算严格中枢级别，不能彼此替代。',['2008年4月11日该三周期分型观察'],figs=((382,1),),ambiguity='chart_period_fractal_vs_strict_structural_level')

keep('366-b007 367-b001 368-b003','upper-l017-c-stage-indicators-auxiliary-not-necessary lower-l100-c-stage-macd-zero-necessary-wording-scope lower-l100-c-stage-macd-visual-auxiliary-not-special','103为分能力最低周期防守，高手可背驰入；月零轴必要措辞仍与辅助非必要并列，不能自动撤回任何原话。')
keep('367-b010','lower-l097-c-stage-jan31-large-oscillation-range-not-axis-3600','3600是幅度尺度，作者600/1345近似和目标预测不能改成精确恒等式或中轴价。')
keep('369-b002 369-b005 381-b005','lower-l081-c-stage-new-stroke-two-joint-conditions lower-l063-chart-period-not-center-level','分型边沿关键不替代81新笔两个联合条件；图周期参考框架不机械换算中枢级别。')
keep('370-b008 371-b000','lower-l102-c-stage-mar18-low-price-drop-preference-not-rule lower-l101-c-stage-rotation-laggard-three-joint-conditions','40%偏好续加双底与放量缩量站住条件，并非所有跌40%股票都成技术买点。')
keep('372-b000 374-b014 375-b000','lower-l102-c-stage-mar18-large-fund-batches-base-position','大资金底仓/动态建仓继续限定资金与阶段，不作为无条件低风险加仓。')
keep('378-b001','lower-l094-c-stage-t1-same-day-exit-impossible-risk','尾盘提前量与T+1既有范围并列，不能把提前买入当取消锁定或保证逃离所有最坏分支。')
keep('379-b007 381-b005','lower-l102-c-stage-mar19-3775-fractal-to-stroke-still-conditional','底分型、笔及不同时间图边界分别确认，不能以后周底状态覆盖早日底/60分钟状态。')

issue('macd-defense-and-necessary-scope','366-b007 366-b009 366-b010 367-b000 367-b001 368-b003','103最低周期防守有高手背驰介入例外，月MACD必要句又是展望；与17非必要及100一般必要措辞范围仍需并列。','记录条件方法和一般措辞，不能归并为全图谱无条件零轴禁令或证明指标必需。',True)
issue('physics-geometry-not-formal-market-model','373-b002 373-b004 373-b005 373-b006 373-b007 373-b008','104现代物理/几何/能量动力为作者纲领，具体以后说，此处没有市场量纲、映射、函数和实验。','只归作者观点及类比，不认证现代物理史/物理学普遍主张，不自行发明能量算法。',True)
issue('price-tolerance-arithmetic-and-targets','367-b010 369-b001 373-b011 374-b007 374-b008','3600节奏中600/1345与所列价差有近似不一致；上下3%为作者价格目标惯例，3424/2500等预测未独立验证。','原数照录并显式记舍入/惯例范围，不改原价，不把3%加进笔/中枢/EPS算法或统计命中率。',True)
issue('fractal-chart-period-and-dated-confirmation','369-b002 369-b005 374-b010 376-b004 379-b000 379-b007 381-b001 381-b005 381-b007','3775/3780/3941、3499/3462/3396、3613/3533/3840各日期周期对象不同；分型已成/笔待延伸/可能周底不能混同。','保留原价及四月七日作业答案，图小数不反改正文；不以K周期固定换算中枢级别。',True)
issue('t1-advance-and-fund-stage-execution','370-b005 372-b000 374-b013 374-b014 375-b000 377-b008 378-b001','小/大资金与最近才沉淀筹码的时间门槛、对冲式未定义、尾盘提前量并未给可执行统一参数。','记录能力资金和隔夜约束，不保证降成本或免除T+1；保留前批执行范围待核。',True)
issue('historical-forecast-profits-and-policy','367-b004 367-b009 367-b011 368-b001 368-b002 368-b009 372-b003 372-b004 377-b003 379-b006','年度节奏、20年牛市、通道加速反弹、权证/个股收益与政策资金因果是作者历史判断，未独立复算/验证。','不认证实际成交、未来收益、通道唯一性、监管指控或现在制度；风险与能力原文限制照留。')
issue('figure-makers-and-late','366-b007 369-b002 369-b003 370-b003 372-b002 374-b012 376-b004 377-b003 378-b001 379-b002 380-b010 381-b005','13图已检查，12图含文后主图/插图K线或后来答案，366图同日但制作人未核。','看全部主图及插图，不把光标当全图截止；图中下降趋势线括注与作者3396答案分开。')

note('366-b003 366-b004 366-b005 366-b006','defense-teaching-metaphor','课程快慢、屠龙防狼比喻及学习建议已读。','防狼为防守教学类比，不能保证绝不受损；具体周期/能力/高手例外另抽。')
note('367-b003 367-b005 367-b006 367-b007 367-b008 368-b000 368-b004 368-b005 368-b006 368-b007 368-b008 369-b006','historical-annual-forecast-and-sector-context','股权收购安排、年度展望未改自评、年线两度喜悲、经济估值/危机、低价题材与大小盘比较全文已读。','匿名资金、经济因果、收益和预测自证未外核，年线融资原因不认证为唯一因果。')
note('370-b000 370-b001 370-b007 371-b001 371-b003 371-b004 371-b005 372-b005 372-b006 373-b000','historical-political-and-financing-rhetoric','政治身份攻击、平安融资催促、题材收益和权证/大盘联动说法已跨页读。','只保留作者历史立场，不认证群体评价、监管动机或市场因果；明确技术边界另抽。')
note('373-b003 373-b004 373-b005 373-b006 373-b007','author-physics-background-analogy','作者现代物理、相对论、规范场/超弦/膜及几何统一的解释背景已读。','不把作者的物理学概括列为本项目已验证科学事实，也不补市场与物理的严格映射。')
note('373-b012 373-b013 374-b000 374-b001 374-b009','historical-regulation-and-self-confirmation','破发宣泄、监管信誉与融资批评、类比走势自证均已读。','匿名利益动机与预测命中不经外核不成为项目事实；两支和容许空间另列。')
note('376-b003 376-b005 376-b006 377-b001 377-b004 377-b005 377-b006','historical-policy-risk-and-ability-rhetoric','政策干货期待、主管金融评价、非系统性风险原用字、本人顺利退出和2500/1500陪玩及依靠本事等评论已读。','不改作者非系统性用字为系统性，不认证交易实绩、利益动机或稳赚；能力范围另存。')
note('378-b002 378-b004 378-b005 379-b001 379-b003 379-b006 380-b007 380-b013 381-b002 381-b003 382-b000','historical-sector-rotation-and-rhetoric','金融/地产/有色扩散、个股买卖自述、消息兑现与回杀、清明随笔、板块涨20—30后调整、小板块大局和多头陷阱等已读。','具体板块/个股历史因果与收益未核，作者口号不当全时期轮动模型或当前推荐。')

relations={
 'lower-l104-c-stage-geometry-energy-dynamics-author-program':[('几何结构','能量结构','related')],
 'lower-l103-c-stage-macd-defense-lowest-period-by-capability':[('MACD','操作熟练程度','qualifies')],
 'lower-l103-c-stage-macd-defense-skilled-divergence-exception':[('MACD','背驰','qualifies')],
 'lower-l103-c-stage-mar24-low-price-double-bottom-volume-conditions':[('成交量','确认','related')],
 'lower-l104-c-stage-apr3-homework-apr7-author-answer-3396':[('底分型','笔','related')],
 'lower-l104-c-stage-apr11-week-bottom-3840-stroke-or-relay':[('底分型','确认','requires')],
}
for r in rows:r['relations']=[{'source':s,'target':t,'type':kind} for s,t,kind in relations.get(r['id'],[])]

by_passage=defaultdict(list)
for r in rows:
    for e in r['evidence']:by_passage[e['passage_id']].append(r)
for item in pending:
    item['lesson_numbers']=sorted({int(passages[x]['unit_id'].split('-')[1]) for x in item['passage_ids']})
    if item['id'].endswith('figure-makers-and-late'):
        item['lesson_numbers']=[103,104];item['figure_ids']=[f['id'] for f in figures]
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
      'related_existing_claim_ids':retained_ids,'note':'MACD防守保留能力最低周期和高手例外；现代物理只归作者纲领，目标3%不替结构容差，图周期/跨日确认和资金阶段分开。'},'4_reverse_check':inverse}})
for f in figures:
    key=(f['pdf_page'],int(f['id'].rsplit('fig',1)[1]))
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=figure_notes[key],
      figure_source_review='十三图已核：十二后加、一未核见stage-c-l103-l104-figure-applied.json；主图和插图均检查，图括注不冒充作者答案，正文独立支持不倒填确认。',
      linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger)==154 and len({x['passage_id'] for x in ledger})==154
def dump(suffix,data):
    (OUT/f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x,ensure_ascii=False,separators=(',',':')) for x in data)+'\n',encoding='utf-8')
dump('reviewed.jsonl',rows);dump('coverage.jsonl',ledger);dump('pending.jsonl',pending);dump('figures.jsonl',figures)
summary={'stage':'C','schema_version':metadata['schema_version'],'graph_version':metadata['graph_version'],'lessons':[103,104],'document_id':DOC,'reviewer':REVIEWER,
 'passages_read':154,'claims':len(rows),'evidence':sum(len(r['evidence']) for r in rows),'importance_counts':dict(Counter(r['importance_level'] for r in rows)),
 'new_concepts':sorted({x for r in rows for x in r['concepts']}-set(concepts)),
 'whole_lesson_semantic_read_complete':True,'technical_extraction_complete':False,'four_round_review':True,'independent_review_claimed':False,
 'visual_pdf_pages':list(range(366,383)),'figure_objects_viewed':13,'figure_origin_counts':dict(Counter(f['origin_status'] for f in figures)),
 'pending':[x['id'] for x in pending],
 'source_passages_snapshot_sha256':SOURCE_SHA,'retained_source_links_in_ledger_only':True,'database_mode':'ro','formal_import':False,
 'acceptance':'154段四轮审读、17页13图；MACD防守及高手例外、物理纲领、价格目标范围和跨日分型/笔、资金阶段分层，增量待预检发布。'}
(OUT/f'{BASE}.summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
db.close();sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(summary,ensure_ascii=False))
