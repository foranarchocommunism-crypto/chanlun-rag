"""Materialize the main agent's four-pass reading of lesson46.

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
BASE = 'c_stage_l046'
REVIEWER = 'Codex 主代理 / 阶段C上册46课同模型四轮复核'
SOURCE_SHA = 'de1dcda524d496e2ac2b364e674e257aca4178b2c3ca5e0597f8a488b9caccc1'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-046' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 86
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 331 AND 339 ORDER BY pdf_page,id', (DOC,))]
assert len(figures) == 6
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
    pending.append({'id': 'upper-l046-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})




















c(46,'daily-auxiliary-classification-not-strict-level-type-replacement','331-b013 331-b014 331-b015','本课先讲每日走势分类，称严格按某级操作时按天切分没有本质改变，日内分类只是辅助；45课首中枢后完整类型分类暂未接着讲。','每日走势分类|操作级别|技术分析|走势类型',1,'与严格递归走势类型分开，不把这课当45未完分类已补齐，也不据按天分段改变任意级别买卖点。')
c(46,'four-hour-eight-thirty-bars-three-adjacent-overlap-day-center','331-b016 332-b000','作者以一天4小时、8根30分K线为系统，将相邻三根30分K线的重叠部分当作每天走势上的一个中枢。','每日走势分类|每天走势上的中枢|K线|周期K线图',1,'限本课当时4小时交易日模型，非所有市场统一时长；本处K线辅助定义不是三完整次级走势类型的严格递归走势中枢，端点相等/包含处理未详。')
c(46,'daily-one-two-zero-center-three-classes-strength-order','332-b000','在上述日内模型下，作者一般把一天分为一中枢、两中枢、无中枢三类，称力度依此趋强。','每日走势分类|每天走势上的中枢',1,'强是该日走势力度，不等都向上或未来收益更高；一般分类未给所有边界/多重重叠枚举算法，不宣布全局唯一分解已证。')
c(46,'one-center-balanced-first-three-often-one-extreme-not-absolute','332-b001 332-b002','一中枢为平衡市，作者说一般前三根30分K线决定当日区间，通常至少有一个全天极值在前三根出现，但并非完全绝对。','平衡市|每天走势上的中枢|高低点|K线',1,'全天极值是回看确认对象，不意味着第三根收完即先知当天高低，作者一般/基本/非绝对限制保留；是否仍为一中枢也需后续确认。',figs=[(332,1)])
c(46,'first-three-day-high-weak-balance-close-ranking-not-red-green','332-b003 332-b004','一中枢且前三根出现全天高点，称弱平衡市；收当天低点最弱，其次收中枢下，中枢内一般，接近当天高点最强，强弱与当天是否红盘无关。','弱平衡市|平衡市|每天走势上的中枢|高低点|K线',1,'例如高开后仍红收也可最弱；前三根同时含日高日低时标签交叠、近高及等边界未穷尽，不私补优先级/EPS。', ['已经属于本课一中枢日内形态','前三根30分K线出现该日全天高点'],figs=[(332,1)])
c(46,'first-three-day-low-strong-balance-close-ranking-not-red-green','332-b005 332-b006','一中枢且前三根出现全天低点，称强平衡市；收当天高点最强，其次中枢上，中枢内一般，接近当天低点最弱，同样与是否红盘无关。','强平衡市|平衡市|每天走势上的中枢|高低点|K线',1,'按本课已确认日内对象，未保证红盘或明天延续；双极值同在前三及近低/边界未给严格互斥处理。', ['已经属于本课一中枢日内形态','前三根30分K线出现该日全天低点'],figs=[(332,1)])
c(46,'neither-day-extreme-in-first-three-turning-balance','332-b007 332-b008','一中枢且前三根未出现全天高低点，称转折平衡市，也可依收盘位置区分强弱。','转折平衡市|平衡市|每天走势上的中枢|高低点',1,'未出现是全天回看，不是只看前三无新高新低便预定后果；转折标签不是严格大级别反趋势定理。', ['本课一中枢日内形态','前三根不包含全天高点或低点'],figs=[(332,1)])
c(46,'one-day-center-can-be-later-triples-not-first-three','332-b009','以上三种平衡市的中枢不一定取前三根30分K线重叠，也可由后面几根形成。','每天走势上的中枢|平衡市|K线',1,'前三极值标签与中枢实际位置两个对象分开，不能永远把开盘前三根框作全天中枢。')
c(46,'two-centers-up-down-and-nonoverlap','332-b011 333-b000','两中枢可按先后方向分向上、向下，本文详向上、向下反过来；两中枢不能有重叠，否则归前述一中枢情形。','每日走势分类|每天走势上的中枢|上涨|下跌|重叠',1,'仍限本课三K日内辅助模型，不拿它否认严格递归中枢扩展/延伸的复杂语境；相等端点的可否重叠未另给数值规则。')
c(46,'unilateral-interval-between-two-centers-and-bar-belongs-neither','333-b000','两日内中枢间至少有一根30分K线，其部分区间不属任何一个中枢，该部分称单边区间；有此区间的K线不从属任一中枢，是后续关键位置。','单边区间|每天走势上的中枢|K线|价格区间',1,'单边区间是部分价格区间，K线归属是另一个原文限制，不能要求整根与两中枢价格全无交叠或把它当跳空缺口定义。',figs=[(333,1)])
c(46,'eight-bars-unilateral-interval-fourth-or-fifth-midday-half-hour','333-b001','在8根30分K线系统内，单边区间只能落第4或第5根，作者据此说这种单边走势的变盘时间在午间收盘前后30分内。','单边区间|每日走势分类|K线|时间之窗',1,'限定本课两中枢/8K/4小时模型，不推广为所有市场任何趋势都午间转折；不是无条件提前预测当日必变盘。', ['本课两日内中枢情形','一天按4小时8根30分K线建模'],figs=[(333,1)])
c(46,'fourth-and-fifth-both-possible-fourth-only-eighth-can-cross','333-b002','第4、第5根可同时有单边区间；若只有第4根有，第8根可能穿越该区间，作者以昨天走势作例。','单边区间|K线|每日走势分类|确认',1,'可能而非必然；原写昨天200070417的异常数字保留，按4/18语境疑指前日但不改原字或把后加图当原发证据。',figs=[(333,1)],ambiguity='source_200070417_date_digits_and_crossing_not_guaranteed')
c(46,'up-two-centers-close-above-second-strongest-below-first-weakest','333-b003','两中枢向上例中，收第二中枢之上最强；第8根穿越单边区间并最终收第一中枢下最弱，其余按收盘位置排序。','每日走势分类|每天走势上的中枢|单边区间|K线',1,'限定向上例和日内收盘相对位置，下向分支作者仅称反过来；未细列所有相等/中枢边界，也不表示未来方向已定。')
c(46,'zero-center-no-adjacent-triple-common-overlap-strong-day','333-b004 333-b005','若8根K线没有任何相邻三根具共同重叠区间，则属本课无中枢、最强单边日，作者说这种日K有重要意义且少见。','每日走势分类|每天走势上的中枢|K线',1,'无的是本课三K日内中枢，不等其他周期/递归中枢都不存在；不是每两根也必须无交叠，少见未统计。',figs=[(334,1)])
c(46,'zero-center-not-guaranteed-continuation-large-daily-center-fake-risk','333-b005','无日内中枢强日不保证趋势延续；作者称常被用于骗线，尤其处大日K中枢内，举227为例。','每日走势分类|走势中枢|假突破|走势预测',1,'相对于更大日K中枢的语境不能省，常见/更大可能未有样本概率；不以强日方向预测次日或把附2008图当2007原证据。',figs=[(334,1)],ambiguity='author_fake_move_frequency_not_measured')
c(46,'zero-center-after-third-point-large-strong-trend-more-likely-not-certain','333-b005','若这种无日内中枢走势出现在第三类买卖点后，作者认为形成大级强势趋势的可能性极大。','第三类买卖点|每日走势分类|趋势|走势预测',2,'先有相应级别第三类点、再出现该日结构，非仅强日即第三类点；极大可能不是充分保证或已测概率。')
c(46,'apr18-strong-balanced-next-day-third-buy-or-extension-five-day-risk','334-b001','4月18日作者判为较强强平衡市；若次日不迅速上破，至少会出现盘整级别延伸，没有两日中枢三买则破5日线可能增；若站上区间震荡上行，则观察下个中枢上移。','强平衡市|第三类买点|中枢延伸|均线系统|走势预测',2,'历史条件分支，原至少会延伸与下破可能不是同等确定性；日内K线中枢与此跨日结构条件分开，不以后K验证预测或把5日线当定义。',figs=[(334,2)])
c(46,'apr18-fourteen-stock-average-double-self-report-not-performance-gate','335-b002','作者自述000416等翻倍、14只元旦以来平均涨幅逾100%，并让收益未达此者反省操作。','操作熟练程度|持股|走势预测',4,'作者选股集合/区间/复权/交易未外核，市场涨幅不是个人实际收益；100%不能变为项目评测或任何人收益验收门槛，段尾次日头不归此前。',ambiguity='author_stock_set_average_return_and_normative_comparison_unverified')
c(46,'apr19-five-day-break-1108-third-sell-reaction-rebuy-opportunity','335-b003','4月19日作者称破5日线和11:08前日中枢三卖已给反应机会，并说牛市快跌慢涨，卖后要找买点买回，认为数据/加息问题不大。','第三类卖点|均线系统|买卖点|操作策略|政策风险',2,'具体历史判点/策略与强安心观点，未核实际充分反应/成交；买回仍须买点，不是任何价立刻追入，数据无事不是风险实证。',figs=[(334,2),(335,1)])
c(46,'apr19-1030-1330-three-bars-3520-watch-recross-and-market-choice','335-b004 336-b000','作者说当日10:30至13:30三K成3520附近中枢，短线看能否重上穿并站稳；其本人希望整固，但承认资金快、市场未必认可，要看市场反应。','每天走势上的中枢|确认|当下|主力资金|走势预测',2,'该价位/三K为4/19案例，不套所有日期或严格30分递归中枢；上穿且站稳是条件，补涨/故意坏业绩预期也未实证。',figs=[(335,1)])
c(46,'apr19-response-types-active-sell-buy-aggressive-only-valid-points','336-b001','作者按当日下跌反应列吓傻、夹空谈预测、看卖点先出再等买点、技术支持的下跌中买点进攻几类，强调按点操作不随指数情绪。','市场心理|买卖点|操作策略|操作熟练程度',2,'分组为作者带贬称的教学比喻，未评真实人心理；激进须与后答技术/大盘/T+1条件联合，非见任何下跌就买。')
c(46,'ABC-first-two-exist-C-can-rise-directly-not-next-day-forecast','336-b006','对14:16为何直接上行，作者以ABC前三段已有前两段时C可直接一段上去说明这种路径允许。','走势类型|走势分解|中枢震荡|走势预测',1,'可以是可能路径，不保证每个C同幅同向或给14:16明确买点算法；未答读者尾盘满仓明日安全的个性预测。')
c(46,'center-oscillation-two-intervals-green-area-earlier-stronger','337-b001 337-b004','作者让从4月17日14:53比较中枢震荡，明确比17日14:53至18日10:01与18日13:35至14:16，前段绿柱面积大、下行力度强，前段能回中枢则较弱后段也可回。','中枢震荡|MACD柱波|指标对比|动力学',1,'保留同向完整区间和面积不是单柱放长，早/午后力比较为特定案例非通用幅度预测；时间跨日不能静换成同日两根K，图原发未核。',figs=[(336,1)])
c(46,'only-participate-capable-unfair-channels-not-need-chase-fast','337-b008','对消息/急回试来不及应对，作者答来不及就不参与，市场渠道非完全公平，只参与自己能把握的。','交易通道|操作熟练程度|市场风险|操作策略',1,'市场渠道判断是作者观点，未指认违法主体；不把读者GDP消息转述作事实认证或让能力不足者强行跟单。')
c(46,'completion-is-form-not-amplitude-not-auto-confirm-B-from-strength','337-b012','作者强调完成是形态问题，与幅度无关；次级别从次次级别生长。','完成|次级别|走势类型|幅度',1,'回应c强劲1分但30分B尚无严格三买的问题，不由涨得强就认B已完；本答未穷尽B完成全部结构/确认条件。')
c(46,'subsub-retest-makes-sublevel-third-point-earlier-can-act','337-b012','作者说次次级回试可构成次级第三类买卖点，比该级别的点更早，实际操作可以先利用。','次级别|第三类买卖点|操作级别|完成',1,'原该级别指代依相邻问答保留，不把较小点升级成30分严格三买已经成立；还须联合操作能力、大级风险及交易限制，未给所有早入成功率。')
quote_overrides['337-b013']='这说过了，就是这样分解的。'
c(46,'qualified-same-level-separation-at-small-divergence-followup','337-b013','对读者后续小级背驰引发30分转折时能否在该小背驰点分开、此前a+A+b+B+c作完整趋势的追问，作者认可就是这样分解。','同级别分解|小级别转大级别|背驰|完成',1,'仅引括号提问之后作者答尾，原提问保留读者；须联合43/44重合/原级无背驰/更大中枢等上下文，不据简短认可信号尚无完成条件时就切分所有大级。')
c(46,'offset-rhythm-stock-pool-one-at-a-time-max-two','338-b000','对小资金零成本筹码还是换现金的提问，作者建议建几只节奏错位股票池，反复按买卖点换股，每次只操作一只、最多两只。','操作策略|资金管理|买卖点|仓位',1,'读者3万元是个案金额，非普遍规模阈值；股票池几只不等同时持仓无限，未给等权比例，也未认可零成本即无风险。')
c(46,'weak-skill-below-five-day-cash-unless-clear-larger-divergence','338-b004','技术不足者宜保守：跌破5日线后，除非有特别明显较大级背驰，否则持币等候；即便再涨，仍可考虑第二第三类买点。','操作熟练程度|均线系统|持币|背驰|第二类买卖点|第三类买卖点',1,'有技能/结构和例外，非任何交易者永久用单线替代中枢；买点机会不保证所有路径都三类齐备，特别明显未量化。')
c(46,'bad-market-larger-level-or-late-buy-point-Tplus1','338-b007','大盘不好时作者要求等较大级别买点，或尾盘买点，否则未必能避过T+1限制带来的问题。','市场风险|操作级别|买点|T+1',1,'作者当时T+1交易背景，等尾盘仍须买点，不是下午任意买即解除制度/行情风险；不作当前所有市场交易规则声明。')
c(46,'Tplus1-consider-real-five-divergence-big-fall-small-capital-view','338-b010','作者说T+1局限必须考虑；一般特别大跌中若真有5分背驰，认为反弹力度够短线，但明确限小资金。','T+1|背驰|操作级别|交易容量|反弹',1,'一般/真有5分/特别大跌/小资金联合，未给成交期限/足够幅度阈值，也未保证T+1下必有可卖利润或认可读者30分买5分卖皆通用。',ambiguity='author_rebound_enough_short_trade_not_execution_guarantee')
c(46,'600855-afternoon-buy-except-larger-point-unclear-trend','338-b013','对600855上午追强后跌破5日线的追问，作者称除非较大级买点，尤其走势不明时宜下午买，并断言该股早上没有买点。','买点|操作级别|市场风险|操作策略',2,'历史个股判读未外核，下午是其当时风险简法，不是任意下午都买点；原未预测该股明日是否继续下调，不反推所有上午股都无买点。')
c(46,'five-minute-no-yellow-white-return-not-five-divergence-below-five','339-b000','4月19日尾盘例作者要求先找比较两段；1分不清可看5分，但黄白线没回轴就不是5分背驰，而是5分以下背驰。','MACD|背驰|操作级别|指标对比|确认',1,'图表观察周期不等信号级别，原未在文字点名两段精确端点，也不把一定以下直接当所有未回轴走势均有下级背驰；保留该例和相应比较前提。')

note('332-b001 332-b003 332-b005 332-b007 332-b010 333-b004','source_header','一中枢/高低极值分支、两中枢及无中枢小标题已核。','标题依日内三K辅助定义，不偷换成严格递归走势类型。')
note('333-b006 334-b000','source-scope-closing','作者将每日图辅助操作留待下一课，星号分隔正文与解盘。','不宣称本课已列全执行程序或补完45遗留分类。')
note('334-b002 335-b000 335-b001','unverified-news-fund-allegation-context','作者把数据延后与走势关联，谈未名基金/老鼠仓、999/343和阻击基金自述，完整读保留历史上下文。','不猜未名实体或补完整证券代码，不认证违规、真实交易/清盘或消息因果，非作者已证技术规则。')
note('337-b013','quoted-reader-question-excluded-from-author-quote','括号后续而原式是否完整趋势为转引提问，作者仅答说过了/就是这样分解。','新证据只引答尾，不能把括号读者命题当独立作者定义，认可范围须联合此前条件。')
issue('daily-K-center-scope-session-model-not-recursive-center','331-b013 331-b014 331-b015 331-b016 332-b000 332-b009',
 '本课4小时8根30分K日内模型，以三相邻K重叠作辅助中枢，与递归次级走势中枢分开；45首中枢后完整分类仍延后。','概念与关系保留作用域，不自动换算其他交易时段/分钟周期或宣称完整类型分类已完。',True)
issue('balance-extremes-retrospective-overlap-labels-and-endpoint-equality','332-b002 332-b004 332-b006 332-b008 332-b009',
 '一中枢前三K常有一极值但非绝对；日高日低均在前三时强弱标签如何互斥、接近极值/边界触碰未给算法，中枢可在后K。','保留回看和一般限制，不把第三根闭合当未来全天锁定，不编EPS/标签优先级。',True)
issue('two-center-unilateral-bar-assignment-four-five-eight-and-no-center-context','333-b000 333-b001 333-b002 333-b003 333-b005',
 '两中枢无重叠且单边K不属任何一枢，第4/5均可、第8可能穿越；无中枢是相邻三K无共同重叠而非任意两K无交叉，强日不保延续。','细查等值/包含/多组三K归属，午间规则仅8K模型；原200070417不改，227/后2008整理图不做未来概率证明。',True)
issue('oscillation-two-intervals-green-area-and-level-without-axis-return','336-b004 336-b005 336-b006 337-b001 337-b003 337-b004 339-b000',
 '4/17 14:53至4/18 10:01与4/18 13:35至14:16比绿面积，非单柱高度；可ABC直接上不答满仓安全，5分看图无回轴是更低信号不升格。','与45面积/回轴及43层级联合，比较对象/级别完整，不补通用幅度和精确进出公式。',True)
issue('completion-form-subsub-earlier-third-point-and-separation-acknowledgment','337-b010 337-b011 337-b012 337-b013',
 '完成是形态非幅度，次次回试生出次级三类点可更早；作者认可后续从小背驰分解，但未逐项认证无严格30分三买时B已完，括号读者问单列。','保留43/44原级无背驰/重合/完成分支与早小点作用域，不由c强劲或答是就补所有完成算法。',True)
issue('skill-cash-Tplus1-market-direction-stockpool-and-execution','337-b008 337-b015 338-b000 338-b003 338-b004 338-b007 338-b009 338-b010 338-b013',
 '能力不足可不参与/持币，5日破例外较大背驰；差大盘等较大或尾盘点、T+1及小资金真实5分反弹语境不可省，股票池每次1最多2。','不把下午/5日线或零成本作保本，不外推3W为资金线或读者30买5卖通用，实际成交/剩余时间风险未建模。',True)
issue('historical-predictions-fund-allegations-profit-and-dates-figures','334-b001 334-b002 335-b001 335-b002 335-b003 335-b004 336-b000 336-b001',
 '4/19四段日期纠正、23时间空格规范，图4后加2原发未核；基金指控/14只平均100%/个股买点和宏观因果皆作者历史观点未外核。','原字/映射/几何不改，基金不猜名、涨幅非实际收益、未来K/2008附图不证原预测；后续阅读47。')
relations={
 'upper-l046-c-stage-daily-auxiliary-classification-not-strict-level-type-replacement':[('每日走势分类','技术分析','qualifies')],
 'upper-l046-c-stage-four-hour-eight-thirty-bars-three-adjacent-overlap-day-center':[('每天走势上的中枢','K线','qualifies'),('每日走势分类','周期K线图','qualifies')],
 'upper-l046-c-stage-first-three-day-high-weak-balance-close-ranking-not-red-green':[('弱平衡市','平衡市','qualifies')],
 'upper-l046-c-stage-first-three-day-low-strong-balance-close-ranking-not-red-green':[('强平衡市','平衡市','qualifies')],
 'upper-l046-c-stage-neither-day-extreme-in-first-three-turning-balance':[('转折平衡市','平衡市','qualifies')],
 'upper-l046-c-stage-unilateral-interval-between-two-centers-and-bar-belongs-neither':[('单边区间','价格区间','qualifies')],
 'upper-l046-c-stage-eight-bars-unilateral-interval-fourth-or-fifth-midday-half-hour':[('单边区间','时间之窗','qualifies')],
 'upper-l046-c-stage-center-oscillation-two-intervals-green-area-earlier-stronger':[('中枢震荡','MACD柱波','qualifies')],
 'upper-l046-c-stage-completion-is-form-not-amplitude-not-auto-confirm-B-from-strength':[('完成','幅度','qualifies')],
 'upper-l046-c-stage-subsub-retest-makes-sublevel-third-point-earlier-can-act':[('次级别','第三类买卖点','qualifies')],
 'upper-l046-c-stage-bad-market-larger-level-or-late-buy-point-Tplus1':[('买点','T+1','qualifies')],
 'upper-l046-c-stage-Tplus1-consider-real-five-divergence-big-fall-small-capital-view':[('T+1','交易容量','qualifies')],
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
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], '读者GDP转引/急回试满仓风险、B无严格三买是否完成、3W资金零成本取舍与600855走势追问保留身份；作者有限认可和技能/制度语境不补成全条件保证或现行规则。'
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
        'note': '日内三相邻30分K重叠辅助定义与递归走势中枢分开，前三极值非先知且不绝对；两中枢单边区间/无中枢强日不保延续，力度两完整跨日区间与T+1技能条件保留。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=f['note'],
             figure_source_review='六整图实际看：三讲义FHSL20080725含2008案例及334三十分市场后K共4后加；335五分/336一分同日原发未核。后图不证明原预测，日内三K与严格递归中枢不同。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 86 and Counter(x['lesson_number'] for x in ledger) == {46: 86}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [46], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(331, 340)), 'figure_objects_viewed': 6, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '46课86段9页6图同模型四轮；4跨日及23空格规范，图4后加2未核；日内辅助分类/回看限定与两区间力度比较、完成及能力T+1范围保留，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


