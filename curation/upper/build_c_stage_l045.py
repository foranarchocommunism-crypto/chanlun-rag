"""Materialize the main agent's four-pass reading of lesson45.

This writes curation artifacts only; the source DB remains read-only.
"""
import hashlib
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2]
KB = AGENT.parent / 'shared-knowledge/v0.1.0'
OUT = Path(__file__).resolve().parent
DOC = 'volume_1-a53e99c37ca5'
BASE = 'c_stage_l045'
REVIEWER = 'Codex 主代理 / 阶段C上册45课同模型四轮复核'
SOURCE_SHA = 'a902009b55daf6e93689228ac42515bb6b73c4bdaa92f50a2c984fda3ce4f756'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-045' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 134
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 320 AND 331 ORDER BY pdf_page,id', (DOC,))]
assert len(figures) == 4
rows, pending, notes = [], [], {}
quote_overrides = {}
retained = defaultdict(list)


def pid(short):
    page, block = short.split('-', 1)
    return f'{DOC}-p{int(page):04d}-{block}'


def c(lesson, slug, shorts, text, labels, level, check, conditions=(), exceptions=(), figs=(), ambiguity='none'):
    citations = []
    for i, short in enumerate(shorts.split()):
        p = passages[pid(short)]
        # A date heading extracted at the previous paragraph's tail belongs to
        # the following paragraph; preserve source text, but don't cite that tail.
        quote = quote_overrides.get(short, re.sub(r'(?:\*+)?200[678]-\d{2}-\d{2}\d{2}:\d{2}:\d{2}$', '', p['text']).rstrip('*'))
        citations.append({'passage_id': p['id'], 'quote': quote, 'quote_start': p['text'].index(quote),
                          'figure_ids': [f'{DOC}-p{n:04d}-fig{k}' for n, k in figs] if i == 0 else []})
    cid = f'upper-l{lesson:03d}-c-stage-{slug}'
    assert cid not in old and cid not in {r['id'] for r in rows}, cid
    ps = [passages[e['passage_id']] for e in citations]
    assert all(p['speaker'] == '缠中说禅' and p['role'] in ('author_body', 'author_reply', 'author_commentary') for p in ps)
    labels = list(dict.fromkeys(canonical.get(x, x) for x in labels.split('|')))
    reasons = {1: '基础核心：定义及不能省略的条件。', 2: '主要方法：影响识别与操作选择。',
               3: '补充深化：方法适用边界。', 4: '背景细节：作者历史判断或经验自述。'}
    context = '；'.join(f"PDF{p['pdf_page']} {p['role']} {p['published_at'] or '未记单独时间'}" for p in ps)
    applicable = '；'.join(conditions) if conditions else '本条陈述的对象、级别、完成状态与所引原段语境；' + check
    row = {'id': cid, 'text': text, 'kind': 'explicit', 'conditions': list(conditions), 'exceptions': list(exceptions),
           'concepts': labels, 'ambiguity_status': ambiguity,
           'review_note': f'语境：第{lesson}课；{context}。适用条件：{applicable}。四轮：通读全部段落并核对实际页面；拆分原子命题与联合条件；比对既有概念及跨课范围；回查证据、量词、时序和配图。{check}。同一主代理四轮，不称独立复核；固定汇编边界，未核原博客。',
           'importance_level': level, 'importance_reason': reasons[level] + check,
           'reviewer': REVIEWER, 'evidence': citations, 'relations': []}
    if figs:
        assert citations[0]['figure_ids'] == [f'{DOC}-p{n:04d}-fig{k}' for n, k in figs]
        row['figure_review_note'] = '主代理实际查看原页、整图和插图右端：' + '；'.join(f['note'] for f in figures if f['id'] in citations[0]['figure_ids']) + '。配图有后加整理版及来源未核图，制作者未核，不作为作者观点唯一证明，文字独立支持命题。'
    rows.append(row)
    return cid


def note(shorts, category, reading, reverse):
    for s in shorts.split():
        assert pid(s) in passages, s
        notes[pid(s)] = {'category': category, 'reading': reading, 'inverse': reverse}


def keep(shorts, ids, reason):
    for short in shorts.split():
        for id in ids.split():
            assert id in old, id
            retained[pid(short)].append(id)
    note(shorts, 'existing_claim_retained', reason, '保留跨课线索；旧命题及旧证据不改。' + reason)


def issue(slug, shorts, description, action, blocker=False):
    pending.append({'id': 'upper-l045-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})




















c(45,'holding-shares-and-cash-are-basic-longer-operations','320-b010','作者指出买入卖出之间更长的过程是持股、持币，它们也是基本而重要的操作。','持股|持币|操作策略',1,'买卖1秒为时长对照修辞，不是所有实际订单时延；持有不等不观察结构或无风险。')
c(45,'fixed-thirty-level-buy-hold-to-sell-cash-to-next-buy','320-b011','按30分操作的例子中，30分买点买入后持股，到相应30分卖点卖出，再持币等下一30分买点；作者把两种持有概括为等待。','持股|持币|等待|操作级别|买卖点',1,'固定级别该笔操作视角，不抹本课其他层级短差或44容量分层；卖点宣告相应类型结束为作者体系陈述，未保证现金收益、可成交或时点可预知。', ['以30分为该笔操作级别、相应买卖点已识别'])
c(45,'theory-guarantees-next-point-author-claim-not-calendar','320-b011','作者称前方相应级别买卖点由理论绝对保证，因此持股持币都是等待该点的过程。','等待|买卖点|操作级别|走势终完美',2,'绝对保证是作者理论主张，不是本项目对所有证券盈利、存续/停牌、成交和等待期限的独立证明；不把等待说成无条件永久持有。',ambiguity='author_theoretical_guarantee_not_empirical_execution_guarantee')
c(45,'points-grow-with-types-not-comet-fixed-schedule','320-b012 321-b000','市场买卖点随具体走势类型生灭而生长，不能像彗星一样预先确定具体时间；本课以30分一买a起的类型为例。','等待|买卖点|走势类型|第一类买点|当下',1,'跨页联合，不把所有一买名称强制归30分，也不把后续分类观察当预报日历。')
c(45,'thirty-type-minimum-one-thirty-center-can-end-after-formed','321-b001','30分走势类型最低需形成一个30分中枢，一旦形成，随后随时结束都符合作者理论。','走势类型|走势中枢|完成|操作级别',1,'可随时结束不等中枢初成当刻必结束，仍需实际结束/卖点条件；与更大中心演化未完成区别保持。')
c(45,'weakest-example-A1-A2-A3-three-overlapping-five-types','321-b001','本例最弱情形从一买a起，三段重叠5分走势类型A1、A2、A3结束就完成该30分类型，可表示A1+A2+A3。','走势类型|走势中枢|次级别|完成|走势分解',1,'三段为完整5分走势类型且有重叠，非任意三根K；最弱是一种可能，不宣称所有30分类型只三段或可预知必走最弱。')
c(45,'no-prior-confirmation-weakest-or-all-completion-details','321-b001','作者说不能事先确认是否走最弱类型，任何可能走势都不能事先确认其完成细节；方向由参与者合力形成，大资金可引导但不能全知。','当下|走势预测|市场合力|主力资金|完全分类',1,'不预先确认与条件分类推演分开，不抹文中作者实际历史预测；普遍不可预知为其理论立场，非本项目已证所有预测无信息。')
c(45,'classify-possible-structures-observe-current-market-choice','321-b002','虽然不能预定实际路径，可能结构与类型可分类，作者要求观察当下，让市场选择结构后再依其选择行动。','完全分类|当下|走势类型|操作策略',1,'本课未列完首中枢后全部分支，留待后课；分类框架不等本批已有完整自动执行算法或所有界线已无歧义。')
c(45,'all-capital-is-component-not-total-market-force','321-b002','无论资金规模多大，都只是市场分力而非合力本身，仍需观察市场反应来选择。','市场分力|市场合力|资金管理|当下',1,'是作者市场结构与纪律主张，不认证某机构实际资金份额/控盘能力；死亡词为警戒修辞。')
c(45,'author-ignites-sector-interacts-on-energy-exhaustion-self-report','321-b003','作者称自己可点火二线、将大盘股纳入剧本，但只是同市场互动；某方面能量被引导耗尽后应反向操作并敏锐观察。','二线股|能量结构|当下|主力资金|操作策略',3,'自我操作/影响力叙述未外核，未给能量耗尽数值公式；不以此认证其导演市场或具体买卖记录。',ambiguity='author_market_influence_and_energy_self_report_unverified')
c(45,'waiting-active-monitor-type-growth-and-classification','321-b004','买卖点操作之后的等待，须密切关注相应类型的生长与分类选择，过程始终是当下的。','等待|走势类型|完全分类|当下',1,'不是盲目忍受已错级别/结构，也不要求每次小波动频繁买卖；本段承认后续分类未讲完。')
c(45,'points-type-growth-mutual-classification-boundary','321-b004','买卖点由走势类型生长状态和分类决定；反过来，某些买卖点出现也明确界定类型生长分类。','买卖点|走势类型|完全分类|完成',1,'保留某些而非所有任意点，双向观察不是循环自证或不核结构便给点名。')
c(45,'twenty-year-script-and-2225-text-time-inconsistency','322-b001 322-b003','作者当时坚持20年牛市剧本、承认可能周月级调整，却又写把戏演到2225年以后。','长期投资|走势预测|市场风险',4,'2225按原页字面保留，与20年长度不一致，不擅改2025；不可改变大方向及剧本为未经验证强预测，不能压过当下信号或用作当前行情判断。',ambiguity='source_2225_vs_twenty_years_and_unverified_bull_forecast')
c(45,'apr12-half-position-five-day-or-skilled-oscillation-context','322-b003','4月12日作者按承受与能力给怕者半仓、胆大看5日线、技术好利用震荡的分层建议，并描述二线带三线轮动。','仓位|均线系统|操作熟练程度|板块轮动',3,'当时条件性建议，半仓按原词不推所有人最佳配置；5日线适用范围须联合后答单边/盘整限制，不证任何路线无风险。')
c(45,'force-precise-definition-measure-no-rectangle-formula-endorsement','322-b008','问走势力度计算，作者说精确定义要测度知识，MACD也一样，精确公式让读者自行编，本答未给出。','动力学|指标对比|MACD',1,'读者时间乘价格范围的矩形算法及连接A影响没有获明确肯定，不能冒充作者力度定义、积分公式或现成算法。')
c(45,'bull-market-can-sell-large-point-rebuy-not-blind-long','322-b011','作者说大牛市也无须死拿，出现大级别卖点可先卖再买，利用震荡降成本，多头不应盲目。','长期投资|卖点|操作级别|成本|操作策略',1,'卖点与级别前提不省，降本为条件性操作目标未证收益；读者成交额2500亿极限猜测未获确认，政策干预反对为其历史态度。')
c(45,'size-limits-compounding-speed-and-point-capacity','323-b001','回应读者按月翻倍外推，作者说资金到一定规模后不会保有该速度，买卖点不能无限容量参与，能长期操作大资金盈利者很少。','交易容量|资金管理|操作策略',1,'未给容量/规模阈值、实际收益或翻倍可持续性；读者CCTV/罗锅盈利未核，不做复利增长承诺。')
c(45,'apr13-1445-drop-oscillation-opportunity-author-view','323-b012 324-b000','4月13日作者称14:45尾盘下跌正常且可用技术先卖后买降成本。','市场震荡|成本|操作策略',3,'具体历史判读/机会判断，未给此处完整信号和成交条件，不认证每日同刻必跌或实际短差收益。')
c(45,'apr13-targets-reached-consolidation-policy-uncertain-view','324-b001','作者称深圳万点、上海3500第一目标已到，震荡整固合理，并认为短期要看管理层态度、长期仍牛。','宏观市场判断|政策风险|走势预测',4,'只记当时作者目标/因果和预测，未外核指数、政策和长期结果，未把观点与文前反预测立场静合。')
c(45,'apr13-cool-excess-speculation-not-certified-entities','324-b002','作者反对个股乱炒和急功近利，认为过火表现会增加政策干预口实，市场应降温。','监管风险|市场心理|宏观市场判断',3,'历史态度和因果解释，未认证未名对手、监管智力或具体公司行为。')
c(45,'report-not-key-decision-maker-author-policy-opinion','324-b006','对读者转述国务院发展研究中心报告，作者认为其层级不是关键，只是写东西。','政策风险|宏观市场判断',4,'读者报告内容和真实政策效力未核，不把作者意见当机构权限法律事实或已发布政策。')
c(45,'sensitive-watch-times-14-and-1445-literal','324-b009','作者提醒注意14、1445这两个看盘敏感时间。','时间之窗|操作策略',2,'保留原数字写法，语境可对应14点/14:45但未给正式周期、时区/交易日算法或每天同刻必转定律。')
c(45,'MACD-bars-area-not-height-shortening-plus-zero-return','324-b012','作者纠正MACD柱子要看面积，不能只看缩短，还要看黄白线是否回抽0轴。','MACD|MACD柱波|指标对比|确认',1,'回答读者三买后新高柱变短的问题，没认可其仅柱高比较或任意面积变小即背驰；须联合走势级别/趋势及回轴语境。')
c(45,'emotion-blocks-point-perception-rhythm-cost-author-view','324-b014','作者说若情绪使人看不到买卖点，技术也无用，应感受市场节奏才能降成本。','市场心理|买卖点|成本|操作熟练程度',2,'心理纪律主张，不证明放松情绪即能识别全部点或实际降本；与42操作未必能磨心态的严重情形范围并置。')
c(45,'bull-keep-chips-lower-cost-rhythm-not-risk-immunity','324-b015 324-b016','作者在牛市语境强调不要丢筹码、应不断降成本来抵抗短线震荡，技术好可用震荡降本。','仓位|成本|市场震荡|操作策略',2,'不等任何买入筹码永久不能卖，须联合本课大级卖点可卖后买和分层操作；未证明不断降本必可执行或成本等全部经济风险。')
c(45,'apr16-five-day-fallback-beats-top-forecast-author-exaggeration','326-b003','4月16日作者让技术不足者看5日线、技术好者震荡换股打差，并用比测顶者强1万倍作强调。','均线系统|走势预测|操作熟练程度',3,'1万倍为修辞无度量实证；未证所有空仓都心理错误或5日不破没有风险，盘整限制另答明确。')
c(45,'apr16-skilled-one-five-minute-divergence-oscillation','326-b004','作者当时建议技术不足者继续看5日线，技术好者看1分、5分小背驰利用震荡，反对追高。','背驰|操作级别|操作熟练程度|均线系统',2,'属历史能力分层，不给预测所有震荡或所有小级点足够成交获利的承诺；段尾新日期支配后文。')
c(45,'apr17-one-minute-1030-1340-case-and-fallback-misses-spreads','326-b005','4月17日作者让看1分图10:30、13:40两点，并称暂学不会者用5日线虽错过短差仍可作简法。','操作级别|买卖点|均线系统|操作熟练程度',2,'原句反问两点是什么，并未在文字逐点命名顶/底或背驰级别；图含4/16另一问答和后行情，不混日期或补作者未写的分类。',figs=[(327,1)],ambiguity='two_intraday_point_labels_not_explicit_in_reply')
c(45,'apr17-data-HK-one-billion-usd-news-author-report-unverified','326-b006','作者把当日震荡与次日重要数据相连，并转述以后赴港上市须10亿美元以上的消息，认为当时政策仍有利。','政策风险|宏观市场判断|走势预测',4,'这是4月17日作者历史新闻转述及因果意见，未核规则范围/生效/实施主体，不作现行上市规定，也不认证匿名报纸文章和对手。')
c(45,'apr17-risk-remains-bad-data-rate-expectation-conditional','326-b007 327-b000','作者提醒顺利时也须谨慎，市场永远有风险；若次日数据差、加息预期大，继续震荡正常，但他仍坚持大方向不变。','市场风险|政策风险|走势预测|市场震荡',1,'条件预测与风险警告并存，大方向不变未验证，不以其强安心撤销风险或将股票废纸比喻当财产权事实。')
c(45,'apr17-fourteen-stock-new-highs-patience-self-report','327-b001','作者称14只股票中当日过半创新高，并举600578、600777、000915及未名VC股、小盘股谈持有耐心。','持股|操作熟练程度|走势预测',4,'股票集合/新高统计与实际收益未核，不补未名VC身份；不是当前推荐或将未抓住归因唯一心理问题。')
c(45,'bad-earnings-strength-watch-not-certain-conspiracy-or-buy','327-b002 330-b002','作者建议中线注意预计报亏损或业绩差却走强的股票，可先不买、关注并找买点；他将部分现象解释为故意做坏业绩骗筹码。','基本面|买点|长期投资|主力资金',3,'操纵/故意为作者未核因果指控，不认所有亏损股均有预谋；不补公司名单，关注不等立即买入，也非坏业绩充分买点。',ambiguity='author_intentional_bad_earnings_allegation_unverified')
c(45,'five-day-line-trending-not-consolidation-center-knowledge-replaces','327-b006 330-b005','作者两次明确5日线在单边走势可作简法，在盘整中用处不大；进一步懂中枢后可不依赖5日线。','均线系统|盘整|走势中枢|操作熟练程度',1,'适用限制来自作者答复，不因之前放心持有强词抹去；足以应付猛烈是观点，非任何单边无亏损保证；未确认读者0912风险很小。')
c(45,'apr16-no-one-minute-divergence-only-below-minute-consolidation','328-b001','4月16日答疑中作者否认当日有1分背驰，只承认午后很小的1分以下盘整背驰，因此不一定做短差，就算做也可换股。','背驰|盘整背驰|操作级别|操作策略',1,'当日指数案例，不把1分以下直接升格为1分底背驰；原文非全世界当日所有证券均无背驰，配图后加。',figs=[(327,1)])
c(45,'subminute-operation-requires-skill-and-1055-1346-three-segments','328-b001','作者允许技术特别好者做1分以下，但前提能分清当日10:55至13:46中枢的三段，不必过短操作。','操作熟练程度|操作级别|走势中枢|次级别',1,'明确三段识别/技能前提，不能把两秒图或任何微波都当可执行买卖点；未在本答列三段每个内部端点。')
c(45,'apr16-no-minute-bottom-required-third-center-leg-complete-can-up','328-b004','作者反问指数为何非要1分底背驰才回头，称连1分顶背都未有、只有更低级；午后下跌完成中枢第三段后便可继续上行，加速与否不作预测。','中枢震荡|走势中枢|背驰|走势预测|操作级别',1,'不否定更低级可能转向/背驰，不把中枢第三段完成当所有市场反转充分条件或保证加速；与43转折级别分层相容待细查。',figs=[(327,1)])
c(45,'beginner-smaller-level-needs-skill-thirty-minute-95-percent-rhetoric','328-b007','作者说级别越小越需经验熟练，初学勿为小波动折腾；若抓住30分节奏，称市场95%的人不是对手。','操作熟练程度|操作级别|市场心理',1,'95%为作者未给样本的强比较，非本项目准确率或胜率指标，也不证30分节奏单独盈利。',ambiguity='author_95_percent_comparison_not_empirical_metric')
c(45,'two-stock-cases-tick-orders-feel-or-small-large-later-exits','328-b008 328-b009','对隧道股份停牌后跌停、000739快涨回落两例，作者将其归分笔层级，称须看盘口摆单和拉升且感觉好；不够精细者仍可依小转大后续位置处理。','成交分笔|操作熟练程度|小级别转大级别|操作策略',1,'没有逐项解释公告和下跌力度公式，读者17.82%/19.88/换手等数字未核；不得挂600855图当这两例证据或补止损/盘口算法。')
c(45,'reader-1345-third-minute-wording-qualified-can-see-next-open','328-b012','读者把5分图13:45离开前中枢再回抽称三分钟买点，作者答可以这样看，后续演化看次日开盘，观察中枢形成发展无需预测。','第三类买点|走势中枢|确认|当下',2,'三分钟买点是读者原字，可能涉词误，不能静改为作者正式定义；可以这样看属该问答有限认可，不证明所有条件或预知明日结果。',figs=[(329,1)],ambiguity='reader_three_minute_wording_and_qualified_acknowledgment')
c(45,'600855-five-divergence-not-endless-fall-1345-question-refuse-rebuy','329-b002 330-b000','对600855，作者承认有5分背驰，但不等要跌不停，反问1分图13:45是什么；对何时再买等其余问题拒绝作答。','背驰|操作级别|买卖点|走势预测',1,'没在原句明确给13:45点名或建议明后天回买，不以图箭头补文字；5分图后行情不验证当时全部判断，同答不用于000739。',figs=[(329,2),(330,1)],ambiguity='author_intraday_point_label_and_personal_trade_answer_withheld')
c(45,'decomposition-previous-lessons-from-divergence-not-all-questions-answered','330-b010','对同级以下非同级分解等问题，作者指前两课已讲小转大和同级背驰分解，均从背驰点分开。','走势分解|同级别分解|小级别转大级别|背驰',1,'对照43/44所述分支、完成/重合前提，非任意小背驰即时切所有大级；读者16课三形是否穷尽及上涨级别差两级未逐项答清。')

keep('323-b011','upper-l041-c-stage-trust-current-market-not-author-reputation','再次强调自立连作者也不能依靠；旧41命题和证据不改，只留补充来源线索。')
note('321-b005 322-b000 322-b002','historical-political-identity-context','深圳万点、管理层与未名山东人/对手的作者历史政治言论已读。','不猜实体、不给行政智力/真实交往或因果作认证，相关行情预期在其他原段保存。')
note('323-b003 323-b004 323-b005 323-b006 323-b007 323-b008 323-b009 323-b010','nontechnical-blog-motivation-and-fee-opinion-context','闲话文章八段含写论语、免费博客、独立生存、分享CD、持有博客比喻及收费者一定失败的观点完整读。','保留作者身份原文及上下文，非技术目的/收费者贬称无外核，不当所有付费工具或从业者实测结论，也不触发音乐下载操作。')
note('324-b013 324-b017','nontechnical-closing-psychology-and-music-context','市场自如无物干扰的强修辞和周末音乐收尾已读。','不作心理训练疗效/绝对不受干扰的实证，不执行文中音乐动作。')
note('325-b001 325-b002 325-b003 325-b004 325-b005 326-b000 326-b001','nontechnical-market-structure-essay-context','4/16净资产到市值的七段经济文章完整读，含股权分置/全流通/股东利益和长期牛市解释。','保留历史经济观点及原文，不核所有股东利益一致、国家恒多头或仅经济衰退能熊等普遍因果，不转换为已证缠论技术定理。')
note('326-b002','historical-weekend-news-policy-self-report-context','作者以周末无消息解释4/16走势，并贬测顶者谈期货。','未核新闻全集/期货盈亏，侮辱和死亡措辞为作者修辞不作现实结果。')

issue('hold-cash-waiting-level-guarantee-and-intralevel-trades','320-b010 320-b011 320-b012 321-b000 321-b004 322-b011 324-b015 324-b016',
 '持股/币是固定级别等待，绝对保证未来点未证期限/成交；筹码不能丢与大级卖点可先卖后买/小层短差需分作用域。','联合44容量分层和后46分类，不把等候变无条件死拿或把理论保证当收益保证。',True)
issue('first-center-weakest-three-five-types-and-unknown-path','321-b001 321-b002 321-b003 321-b004',
 '最弱A1+A2+A3三完整5分类型重叠只是可能，一中枢成后可随时结束不等立即必完；后分支尚未全，市场分力/合力和不预测立场带强词。','接46后续分类核完成/可选择路径，保留不能提前确认与作者历史预测并存，不补完整算法。',True)
issue('force-measure-rectangular-proposal-MACD-area-zero-axis','322-b006 322-b007 322-b008 324-b011 324-b012',
 '测度精确定义只提示未给公式，时间×价格范围是读者未获认可；MACD看面积非缩短并看回零，不能只柱高或面积一项充分。','跨24/34/40等查比较对象/级别，不自编积分或默认参数算官方定义。',True)
issue('five-day-unilateral-not-consolidation-and-cost-safety','322-b003 324-b014 324-b015 324-b016 326-b003 326-b004 327-b006 330-b005',
 '作者明确5日线单边简法/盘整用处不大；先前不破安心/1万倍/降本必需是条件或修辞，不等成本消全部风险。','关联40至44强安心范围，半仓/持有/震荡分能力和结构，不把辅助线当中枢规则或无限安全保证。',True)
issue('subminute-index-three-legs-1345-identity-and-stock-cases','326-b005 328-b001 328-b004 328-b007 328-b008 328-b009 328-b011 328-b012 329-b002 330-b000',
 '4/16下分级盘背/三段完成非1分背驰，4/17两点不同日；1055至1346三段技能前提、三分钟买点读者字/有限认可和600855 1345点名未明，分笔两股不可混图。','保留作者未回答部分及95%未统计，不推所有转折无背驰/所有小点可做，区分图像观察和作者明说。',True)
issue('decomposition-from-divergence-scope-reader-unanswered-details','330-b007 330-b008 330-b009 330-b010',
 '作者指前两课从背驰点分解，非同级细节、16三形是否全及级别差两级问题未逐项回答。','保留43重合/无重合与完成前提和44小转大必要非充分，不任意小点切大级。',True)
issue('historical-bull-2225-policy-news-and-intentional-earnings','322-b001 322-b003 324-b001 324-b006 326-b006 326-b007 327-b000 327-b001 327-b002 330-b002',
 '20年剧本与2225原字矛盾；监管、10亿美元赴港消息、14只新高及故意做坏业绩均历史观点/转述/指控未外核，不能转当前事实或建议。','不改2225、未名实体不猜、亏损预谋无证不认证；331新闻仍读者转引，宏观附文不作技术定理。')
issue('source-date-tail-later-charts-and-context-identity','326-b004 326-b005 327-b000 328-b012 329-b002 330-b000 331-b003',
 '六段4/17日期纠正、39时间空格规范；四图3后加1未核，混日期/周期/证券不可升格，331媒体文字读者转引无作者答。','原字/映射/几何及4/16前段尾头不改；图不验真预测或补个性化买回指令，博客与经济文章已读作上下文。')
relations={
 'upper-l045-c-stage-holding-shares-and-cash-are-basic-longer-operations':[('持股','持币','qualifies')],
 'upper-l045-c-stage-fixed-thirty-level-buy-hold-to-sell-cash-to-next-buy':[('等待','操作级别','qualifies'),('持币','买卖点','qualifies')],
 'upper-l045-c-stage-waiting-active-monitor-type-growth-and-classification':[('等待','走势类型','qualifies'),('等待','当下','qualifies')],
 'upper-l045-c-stage-points-type-growth-mutual-classification-boundary':[('买卖点','完全分类','qualifies')],
 'upper-l045-c-stage-all-capital-is-component-not-total-market-force':[('市场分力','市场合力','qualifies')],
 'upper-l045-c-stage-size-limits-compounding-speed-and-point-capacity':[('交易容量','资金管理','qualifies')],
 'upper-l045-c-stage-MACD-bars-area-not-height-shortening-plus-zero-return':[('MACD柱波','确认','qualifies')],
 'upper-l045-c-stage-five-day-line-trending-not-consolidation-center-knowledge-replaces':[('均线系统','盘整','qualifies')],
 'upper-l045-c-stage-subminute-operation-requires-skill-and-1055-1346-three-segments':[('操作熟练程度','走势中枢','qualifies')],
 'upper-l045-c-stage-decomposition-previous-lessons-from-divergence-not-all-questions-answered':[('走势分解','背驰','qualifies')],
}

for r in rows:
    r['relations'] = [{'source': a, 'target': b, 'type': t} for a, b, t in relations.get(r['id'], [])]
by_passage = defaultdict(list)
for r in rows:
    for e in r['evidence']:
        by_passage[e['passage_id']].append(r)
for item in pending:
    item['lesson_numbers'] = sorted({int(passages[x]['unit_id'].split('-')[1]) for x in item['passage_ids']})
    if item['id'].endswith('commentary-dates-and-figure-provenance'):
        item['figure_ids'] = [f['id'] for f in figures]
ledger = []
for id, p in passages.items():
    linked, decision = by_passage[id], notes.get(id)
    if linked:
        result, reading = 'new_claim', '；'.join(r['text'] for r in linked)
        atomic = [{'claim_id': r['id'], 'conditions': r['conditions'], 'exceptions': r['exceptions']} for r in linked]
        inverse = '；'.join(r['review_note'] for r in linked)
    elif decision:
        result, reading, atomic, inverse = decision['category'], decision['reading'], [], decision['inverse']
    elif p['role'] == 'reader':
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], '读者时间乘价格范围力度公式、2500亿极限、三分钟买点字样、个股数字与331媒体摘录均保留身份；作者有限认可和未答部分不补作普遍定理或当前新闻。'
    elif p['text'].startswith('教你炒股票') or p['text'] in ('缠中说禅解盘:', '缠中说禅解盘：', '缠中说禅回复:', '缠中说禅回复：') or re.fullmatch(r'.*200[5678]-\d{1,2}-\d{1,2}.*', p['text']) and (len(p['text']) < 75 or p['text'].startswith('缠中说禅')):
        result, reading, atomic, inverse = 'source_header', '课程、解盘/回复的作者署名与时间头已核。', [], '只作来源身份锚点，不独立支持技术结论。'
    else:
        raise AssertionError(('unaccounted paragraph', id, p['text']))
    if linked and decision:
        reading += '；其余语境：' + decision['reading']; inverse += '；' + decision['inverse']
    ledger.append({'passage_id': id, 'lesson_number': int(p['unit_id'].split('-')[1]), 'document_id': DOC,
      'pdf_page': p['pdf_page'], 'role': p['role'], 'speaker': p['speaker'], 'published_at': p['published_at'],
      'source_text_sha256': hashlib.sha256(p['text'].encode()).hexdigest(), 'result': result, 'claim_ids': [r['id'] for r in linked],
      'related_existing_claim_ids': retained[id], 'existing_evidence_not_mutated': True,
      'pending_issue_ids': [x['id'] for x in pending if id in x['passage_ids']], 'reviewer': REVIEWER,
      'rounds': {'1_read_and_scope': reading, '2_atomic_conditions': atomic,
        '3_normalization': {'concept_labels': sorted({x for r in linked for x in r['concepts']}), 'related_existing_claim_ids': retained[id],
        'note': '持股/币等待固定级别且观察当下分类，最弱三完整5分类型重叠仅一种可能；MACD面积/回轴和5日线单边非盘整限定保留，日/级别/证券与转引身份分开。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=f['note'],
             figure_source_review='四整图均实际看：327上证1分含4/18后K，329上证5分/600855五分有4/17后K为后加；330同日600855一分原发未核，分笔739不混同该股，点名反问不补作者明说。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 134 and Counter(x['lesson_number'] for x in ledger) == {45: 134}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [45], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(320, 332)), 'figure_objects_viewed': 4, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '45课134段12页4图同模型四轮；6跨日及39空格规范，3图后加1未核；等待/分类、MACD和5日限定、子分钟案例及非技术附文/读者新闻分层，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


