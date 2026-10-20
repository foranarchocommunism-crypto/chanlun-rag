"""Materialize the main agent's four-pass reading of lesson58.

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
BASE = 'c_stage_l058'
REVIEWER = 'Codex 主代理 / 阶段C上册58课同模型四轮复核'
SOURCE_SHA = '95cb3a78410b2863ac18bdce17862d24d531d0a7cb1f5c3147e3f9871b3940f5'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-058' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 72
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 436 AND 443 ORDER BY pdf_page,id', (DOC,))]
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
    pending.append({'id': 'upper-l058-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})

quote_overrides['439-b004']=passages[pid('439-b004')]['text'].split('今天跑了不少地方',1)[0]
c(58,'chart-only-response-without-greed-fear-not-loss-tolerance-rule','436-b005','作者要求看图操作时摆脱自身贪婪与恐惧，不把股票当宝而在该卖时不卖；这属于其操作纪律和心理主张。','操作策略|市场心理|操作节奏',2,'跌40%不惊慌/国债安心为作者劝诫，非容忍40%亏损的止损规则或国债零风险证明；无我不等忽略资金约束。')
c(58,'simple-five-day-exit-and-current-chart-own-response','436-b006','作者以本轮跌势中跌破5日线退出为最简复盘例，强调市场当下发生、不能由别人替自己反应。','均线系统|当下|当机立断',2,'具体卖点需自己回看；未给所有个股/缺口/涨跌停/成交成本条件下5日线必可退出保证，不混前57原5月均线。')
c(58,'inner-five-fold-no-overlap-whole14-15-one-segment','436-b008','第58课图14—15内部红绿箭头所示下上下来回五折，第二个上终点未触及第一个上起点、同向相邻不重合，作者把整个14—15仍看作一个向下线段。','线段|重叠|走势分解',1,'问句不是说整个14—15不是线段，而是内部箭头折返不单独成段；这是分型/笔精确定义前的本图说法，不据后图改当时标号。',figs=[(437,1)])
c(58,'preprecise-three-fold-gap-exception-nonoverlap-can-extend','436-b008','本课说线段除缺口外至少由上—下—上或下—上—下三折组成；相邻的上或下不重合时，这种模式可延伸而仍为一个线段。','线段|缺口|重叠',1,'原文保缺口例外/至少/不重合，不称任意三折充分成段；与后62至少三笔及67特征序列细则分语境保留，不按日期自动消除张力。',figs=[(437,1)],ambiguity='definition_boundary')
c(58,'14-15-force-largest-no-one-minute-plus-divergence','436-b009','作者说14—15不构成合适买点，并以MACD黄白线显示其力度大于此前各段，判不构成1分钟以上背驰，最多为1分钟以下最小级别背驰。','MACD|背驰|级别',1,'原1分钟以上/以下最小级别范围照录；MACD是辅助、图参数24/52/9不静改12/26/9，不以力度一句证明所有级别结构。',figs=[(437,1)])
c(58,'15-minimal-green-area-divergence-rebound-last-inner-up','436-b009','作者在15下MACD小红箭头用绿柱面积比较识别小背驰，15—16反弹在14—15最后一个上附近受阻。','盘整背驰|MACD柱波|反弹',2,'只支持此例最小级别背驰和附近受阻，未给数值面积/精确相等边界，也非外层背驰必回最后内部反抽点。',figs=[(437,1)])
c(58,'15-16-third-sell-recent10-13-not-point7','436-b010 437-b000','15—16反弹是针对最近10—13所成1分钟中枢的第三类卖点；作者明确否定仅因没突破点7就判这一三卖的理由。','第三类卖点|走势中枢|次级别',1,'三卖成立所依中枢必须对应；点7虽有另一5分技术意义，不能偷换为最近1分枢的判据。',conditions=['第58课15—16反弹及最近10—13的1分钟中枢'],figs=[(437,1)])
c(58,'third-point-direct-sublevel-leave-return-nearest-center-far','437-b000','第三类买卖点须次级别离开、次级别反抽，针对该级别最近的中枢；快速变动行情中，离开的距离往往很远。','第三类买卖点|次级别|走势中枢',1,'保该级别/最近/两个次级别及快速行情往往，非任意更低级折返或离得远本身就三类；三折和完整次级类型条件应联读。',figs=[(437,1)])
c(58,'from16-only-potential-accelerated-fall-can-break-nested-confirm','437-b001','从16开始的一段在6月4日晚仅可能进入背驰段；次日若突然加速下跌会破坏这一可能，是否成立须看次日内部区间套的当下定位。','背驰段|区间套|确认|当下',1,'前瞻可能与已成立明确分开，不由6/5后图把6/4断言改成已知；区间套仍需内部结构，不是MACD面积一项定论。',figs=[(437,1)])
c(58,'if-divergence-return-at-least15-form-one-center-from15','437-b001','对上述从16起走势，若背驰出现，作者预期反弹至少重回点15，从点15起至少形成一个1分钟中枢。','背驰|中枢扩展|反弹',1,'保如果背驰及至少、从15开始，不称16起任何反弹都必回15，也不等于回旧10—13中枢。',conditions=['第58课从16起走势的背驰成立'],figs=[(437,1)])
c(58,'old1-10-five-center-rebound-not-back-above4015-third-sell','437-b002','相对1—10的5分钟中枢，该反弹如果不能重新回到4015之上，作者判将形成5分钟第三类卖点。','第三类卖点|中枢回拉作用|级别',1,'原不能回4015之上保留，不静换4000或图4016.30，也不省完整次级离开/反抽条件；尚属当时未来反弹的条件判断。',conditions=['第58课1—10的5分钟中枢及未来该反弹'],figs=[(437,1)])
c(58,'below4000-rebound-sell-larger-center-or-fall-author-outlook','437-b002','作者当时判断今后几天4000点下反弹会构成卖点、至少引发更大级别中枢乃至新下跌，并以反弹重回4000之上作例外。','走势预测|中枢扩展|反弹',2,'4000是该段概略历史判断，严格前句4015边界另存；这是作者强语预测非已实现的逐笔可成交或所有反弹必跌定理。',conditions=['2007-06-04夜对今后几天的判断'],exceptions=['原文：除非这反弹能重回4000点之上。'])
c(58,'from10-new-five-not-formed-nonoverlap-future-downtrend','437-b003','6月4日晚从10起新的5分钟中枢尚未形成；若其最终与1—10的5分钟中枢不重合，则作者判形成5分钟下跌。','中枢新生|下跌|完成',1,'保尚未/最终/若/同5分；不把两暂时无交集范围提前当两个完成中枢，不将未来下跌升级为当前已成趋势。',figs=[(437,1)])
c(58,'point7-larger-five-divergence-return-improvement-only-possible','437-b003','点7另有强技术含义：若5分钟背驰引发的反弹能重回点7之上，作者认为大盘才有好转可能，否则短线压力仍在。','背驰|反弹|走势预测',2,'5分钟背驰条件与好转可能保留，不据此认可读者用7点判15—16的1分三卖理由；不是突破7保证新高。',figs=[(437,1)])
c(58,'jun5-17-end3404-18-still-watch-ending-center-oscillation','438-b001','6月5日解盘记17段结束于3404点，下午走第18段；18段结束后进入前述中枢震荡，次日任务是观察18段结束。','完成|中枢震荡|当下',2,'正文3404与重绘图3404.25分开保，未把18在当日已结束；作者要求研究精确定位但本段没有完整下钻算法。',figs=[(438,1)])
c(58,'jun5-monthly-five-average-intraday-false-break3434','438-b002','6月5日作者以月线的5均线及3434点一般的位置描述盘中假突破的大走势背景。','均线系统|假突破',2,'原月线的5均线及一般保留，不回改57原5月均线或补其来源未核备注；未给此时具体均线精确值。')
c(58,'jun6-3858-point7-center-formed-view-oscillation','438-b004','6月6日作者称受制于3858点即点7，下面中枢已经形成，应按中枢震荡看。','走势中枢|中枢震荡|反弹',2,'日期按438前时间头6/6 16:52:09修正，不沿用6/5；本文未在此处给中枢完整数值上下界或宣称所有大级中枢已完。',figs=[(439,1)])
c(58,'best-stock-no-chase-low-of-oscillation-safety-first','438-b004','作者认为即使最好的股票也不能追高买，应在震荡低点介入，安全第一。','追高|操作节奏|市场风险',2,'历史一二线集中背景，不保证任何局部低点都是合格结构买点/安全成交，亦非当前荐股。')
c(58,'jun7-break3858-large-center-forming-next4015-conditional','438-b006 439-b000','6月7日作者说突破3858意味着一个大的中枢正在形成，成为可依赖的波动中心；4015是下一关，不能突破仍可能严重变坏，突破才有再挑战半线或新高可能。','中枢扩展|完成|走势预测',1,'正在形成非已经完成；跨页4015在438尾/439头联读，半线/新高均是可能，不以6/8后加图证明前瞻必然。',figs=[(439,1)])
c(58,'midterm-money-wait-buy-no-chase-jun10-view','439-b004','6月10日作者对其中线题材例要求不追高，中线资金可耐心等待好的买点，原已持有者则可拿着。','资金期限|等待|买点|长期投资',2,'只取作者中线条件和等点操作原则；创业板明年一定出/635和潍柴题材/20年30000点为历史预测与自述，未外证，不作买入保证。')
c(58,'not-only-technical-and-worth-holding-ten-years-author-choice','440-b000','作者否认自己只看技术面或理论只能短线，称有些股票可持十年以上，关键是是否值得其持有。','基本面|技术分析|长期投资',2,'这是作者自身选股/持有观点，十年非所有个股最低期限，称潍柴中线绝对无问题不作本项目事实或收益保障；公司份额/收益数字未外证。')
c(58,'jun11-cost-higher-less-frequent-larger-level-five-day-reference','440-b010','6月11日作者说印花税贵时短线不要过于频繁，可放大操作级别；看不懂短线者可看5日线，不破则持有。','交易成本|操作级别|均线系统',1,'保持当时费用背景/不会短线的适用者，不宣称大级零风险或所有人机械5日线买卖；前句深带沪/13700空间为历史条件。')
c(58,'private-equity-prelisting-industrial-layout-not-general-VC-definition','441-b000','作者将其所指私人股权投资区别于传统VC，称只投马上能上市的项目，并考虑产业结构大布局。','私人股权投资|创业投资|基本面',3,'是作者当时所指业务/策略，不把只投马上上市当全世界PE法定定义；基金未发展/普通人没机会等为当时看法未外证。')
c(58,'jun12-4015-five-day-retest-next4144-newhigh-conditional-script','441-b001','6月12日作者将突破4015后回抽5日线视为第二步，下一步沪4144半线、再创新高；深13700单列，并明确剧本实现须各方面配合。','走势预测|政策风险|均线系统',2,'四步是当时路径预期不是已完成/必然，沪深数值不混；大资金砸回补不会有事是作者自述强语，不证账户无风险。',figs=[(441,1)])
c(58,'jun12-rotation-sequence-if-index-stable-not-guarantee','441-b002','作者认为修复过程中个股轮动有先后，先绩优；指数没问题时绝大多数可轮到，站稳4000后三线题材才逐步活跃。','板块轮动|一线股|三线股',2,'保指数条件、绝大多数非所有、逐步非同时；不会看图仍看5日线不破拿着是此语境建议，不构成收益保证。')
c(58,'jun13-gap-remaining-week-important-shake-required-author-view','441-b004 442-b000','6月13日作者说短线留下的缺口对本周余下走势最重要，震荡与充分换防是继续发展的必要过程，并同时考虑心理和政策考验。','缺口|市场心理|政策风险',2,'跨页续文及日期6/13保持；这里换防必需是作者市场解释，非本项目验证的所有行情因果定律。',figs=[(441,1)])
c(58,'jun13-neckline-no-chase-shenzhen-stand-newhigh-conditional','442-b001','6月13日作者建议震荡中看底部形态颈线的具体走势、不追高；个股轮动依赖围绕4144震荡，后续深圳能否站稳新高另作短线技术与心理条件。','颈线|板块轮动|追高|指数走势背离',2,'若深圳下周初站稳才鼓励上海及未创新高股，原句上海已经所有有排字疑义，未变成所有股必创新高；颈线需具体走势非触线即买。')
c(58,'chart-period-not-move-level-one-chart-can-find-daily-center','442-b007','5分钟图和1分钟图有观察精度差异，1分钟图中也可找日线中枢；图的级别与走势的级别不是一回事，应先理解线段如何继续形成更高级结构。','周期K线图|级别|线段|价格精度',1,'作者是在回复读者54/56至58图例矛盾疑问，不等于直接认可所有读者分级，精度高非任意图可无损推回全部分笔。')
c(58,'objective-move-level-subjective-chart-magnification','442-b008','作者将走势级别视为客观，而周期图级别是主观选择的不同倍数显微镜。','级别|周期K线图|价格精度',1,'主观的是观察图选择非走势级别任意指定，不把1分钟图恒定等同1分钟走势或图框5分钟等同5分中枢。')
c(58,'small-float-no-crowding-star-five-percent-historical-rhythm','442-b012','针对读者所持小盘带星号股票，作者说当时不应一窝蜂买，小盘经不住；在该跌势下涨起较后，事情须按节奏进行。','交易容量|操作节奏|追高',2,'原每天才5%为作者2007特定星号股表述，不当所有ST/当前市场交易规则；没有回答持有永远没事，未识别代码不补造。')
c(58,'missed-buy-three-alternatives-realestate-analogy-personal-choice','443-b001','对错过股票或房子的提问，作者列找买点进入、先买落后标的（房子可远或旧）后再换、或先不买三种选择，由当事人自行选择。','买点|等待|操作策略',3,'读者房价不会跌/将来狂涨为提问叙述，作者未在本答确认房价不会跌；仅保类比的三选项，非当前房地产建议。')
c(58,'small-consolidation-divergence-can-resolve-fees-skill-larger-space','443-b004','小级别盘整背驰可能盘中跳动即化解；费用变贵、技术不好时不必做这类对冲，应看更大背驰，给操作足够空间。','盘整背驰|交易成本|操作熟练程度|操作级别',1,'不认读者10:20的背驰级别/有效性；更大依能容费用和操作空间，非所有背驰必须大级或小级必无效。')
c(58,'small-capital-error-other-larger-buy-profit-sale-author-value','443-b005 443-b006','作者对小资金卖错说可在盘中震荡找其他新启动股票，关键选大些级别的买点；赚钱卖无所谓对错是其评价，技术需实践磨练。','交易容量|买点|操作熟练程度|操作节奏',2,'有合格新买点仍是前提，未证明总能更好成交/免除机会成本；技术好烦恼全无属作者强语非实证，不强制追回原股。')
c(58,'policy-part-of-force-chart-force-itself-not-news-price-cap','443-b009','作者将政策视作合力的一部分，走势视作合力本身画出的结果；对消息政策应平和，技术出问题时应退出。','市场合力|政策风险|技术分析',1,'读者5000上限/利得税传闻未获确认；政策是分力不等政策永远不影响走势，也非所有技术坏点都能无摩擦退出。')
c(58,'may30-second-sell-jun5-buy-retrospective-not-fill-proof','443-b009','作者以5月30日第二类卖点退出、6月5日标准买点进入作回顾，强调重仓者亦应依技术节奏应对政策。','第二类卖点|买点|操作节奏|仓位',2,'这是事后例，不消除56所述突发低开后原一卖不可得，也非指数二卖等于所有个股同类或T+1/跌停都能成交；未给该答具体5日买点等级。')

note('436-b004 436-b007','background_context','出差安排及转入连续图解，非技术定理。','个人行程仅原上下文，不升操作保证。')
note('437-b004','author_self_assessment_and_plan','作者自称严格条理清晰，前提先分解正确；计划后续示范到日线中枢。','自评不作本项目数学证明/全部歧义已解；计划不等当前已成日线枢。')
note('438-b003 438-b005 439-b001','date_transition_and_travel','前段私人行程结束，尾部新时间头只管后文；438/439解盘按6/5、6/6、6/7、6/8分开。','无读者署名，错误reader已修；尾新时间不回改前段。')
note('439-b002','historical_commentary','6/8称前日3858站稳任务完成，担心周末消息并有旅行修辞。','不把后见结果倒作6/7必然证明，不证明消息或心理事实。')
note('439-b004 439-b005 440-b000 440-b001','historical_business_self_report','保股票题材/VC股权收益/布局/20年30000点/创业板明年一定出等历史预测和自述，只有所列技术/资金期限观点进入本批。','未经外部核对，不确认公司股权、财报、实际收益/商业机密和市场未来。')
note('440-b002 440-b003 440-b004 440-b005 440-b006','literary_context','潍柴诗及出行上下文，读原页保留。','诗不是技术买点或财务论证。')
note('440-b008 440-b009','personal_context','跨城印象、旅途与通讯自述。','地理印象和个人行程非知识图谱技术事实。')
note('442-b002','historical_stock_self_report','钢铁停复牌、买价9元多/反应快10%以上和原本连续涨停剧本为作者自述。','无代码与成交记录不补；未发生反事实涨停和停牌逃跌不当实证收益/保险。')
note('442-b011','personal_context','无新文章因出差积事，次日再写。','与下段小盘股答分开，未回答所有持股无风险。')

issue('early-segment-gap-exception-vs-later-precise-definition','436-b008','第58课三折/缺口例外和不重合延伸为早期图解，与62至少三笔及67精确特征序列需分语境。','保58原说，不把内部箭头误成整个14—15非段，不凭时间全盘覆盖后定义。',True)
issue('minimal-divergence-force-area-and-potential-not-confirmed','436-b009 437-b001 438-b001','14—15只最小背驰；从16可能需次日内部确认；17精确终点完整下钻未在该段给出。','分别记录黄白线/绿面积与未来确认，正文3404及图3404.25保持，不能用后图冒当前已知。',True)
issue('recent-center-third-sell-4015-vs4000-point7-larger-scope','436-b010 437-b000 437-b002 437-b003','15—16一分三卖依据最近10—13，不是点7；5分旧1—10界4015与4000概略预测分开，7是更大层好转条件。','不偷换中枢/点位/级别，未形成新5分不能提前判完整下跌，保强语预测不是实证保证。',True)
issue('macro-center-forming-not-finished-and-conditional-rotation','438-b006 439-b000 441-b001 441-b002 442-b001','6/7大枢仍形成、4015/4144/沪深/轮动与政策配合均有条件。','审后59至61是否补形成过程；图4016.30不回改正文4015/3858。',True)
issue('chart-vs-move-level-precision-and-fees-skill','442-b007 442-b008 443-b004 443-b005','图级别与走势级别、精度与客观结构不同；费用和技能决定是否做微小盘背，利润没错是作者评价。','和54/57及62至72联读，不把图5分钟定义为5分走势，不把大级/好技术升零风险。',True)
issue('date-role-corrections-and-four-figure-provenance','438-b004 438-b005 438-b006 439-b000 439-b001 439-b002 441-b003 442-b000','25段身份/日期修正；4图2未核2后加，437原MACD24/52/9与重绘12/26/9、图5分钟框、3404.25/4016.30保差。','原发未核，不以多日合并图证前日预测；未核原博客。',False)
issue('midterm-PE-self-reports-star-rules-realestate-policy-and-fill-guarantees','439-b004 440-b000 441-b000 442-b012 443-b001 443-b009','PE/VC公司收益、星号5%/房价传言/政策及卖买必可执行强语属于历史自述/观点。','固定两册边界，读者房价不跌和5000上限传言不作作者确认；不输出当前金融法律建议。',False)

relations={
 'preprecise-three-fold-gap-exception-nonoverlap-can-extend':[('线段','重叠','qualifies')],
 '15-16-third-sell-recent10-13-not-point7':[('第三类卖点','走势中枢','requires')],
 'third-point-direct-sublevel-leave-return-nearest-center-far':[('第三类买卖点','次级别','requires')],
 'from16-only-potential-accelerated-fall-can-break-nested-confirm':[('背驰段','确认','requires'),('确认','区间套','requires')],
 'if-divergence-return-at-least15-form-one-center-from15':[('背驰','中枢扩展','qualifies')],
 'from10-new-five-not-formed-nonoverlap-future-downtrend':[('下跌','中枢新生','requires')],
 'jun7-break3858-large-center-forming-next4015-conditional':[('中枢扩展','完成','qualifies')],
 'jun11-cost-higher-less-frequent-larger-level-five-day-reference':[('操作级别','交易成本','qualifies')],
 'private-equity-prelisting-industrial-layout-not-general-VC-definition':[('私人股权投资','创业投资','qualifies')],
 'chart-period-not-move-level-one-chart-can-find-daily-center':[('周期K线图','级别','qualifies')],
 'objective-move-level-subjective-chart-magnification':[('周期K线图','价格精度','qualifies')],
 'small-consolidation-divergence-can-resolve-fees-skill-larger-space':[('盘整背驰','交易成本','qualifies'),('操作级别','操作熟练程度','qualifies')],
 'policy-part-of-force-chart-force-itself-not-news-price-cap':[('市场合力','政策风险','qualifies')],
}
for r in rows:r['relations']=[dict(source=a,target=b,type=t) for a,b,t in relations.get(r['id'].split('upper-l058-c-stage-')[1],[])]
by_passage=defaultdict(list)
for r in rows:
 for e in r['evidence']:by_passage[e['passage_id']].append(r)
for item in pending:
 item['lesson_numbers']=[58]
 if item['id'].endswith('date-role-corrections-and-four-figure-provenance'):item['figure_ids']=[f['id'] for f in figures]
ledger=[]
for id,p in passages.items():
 linked,decision=by_passage[id],notes.get(id)
 if linked:
  result,reading='new_claim','；'.join(r['text'] for r in linked);atomic=[dict(claim_id=r['id'],conditions=r['conditions'],exceptions=r['exceptions']) for r in linked];inverse='；'.join(r['review_note'] for r in linked)
 elif decision:result,reading,atomic,inverse=decision['category'],decision['reading'],[],decision['inverse']
 elif p['role']=='reader':result,reading,atomic,inverse='reader_context','读者署名/问题/自述已读，只限定相邻回复对象。',[],'54/56至58图例级别疑问、星号股/房价不跌/10:20减仓/5000传言均保reader，未冒作者确认。'
 elif p['text'].startswith('教你炒股票') or p['text'] in ('缠中说禅回复：',) or re.fullmatch(r'.*200[5678]-\d{1,2}-\d{1,2}.*',p['text']) and (len(p['text'])<75 or p['text'].startswith('缠中说禅')):result,reading,atomic,inverse='source_header','课/独立文章/作者解盘/答疑/时间头定位已核。',[],'只作来源锚点，不独立证明技术命题。'
 else:raise AssertionError(('unaccounted paragraph',id,p['text']))
 if linked and decision:reading+='；其余语境：'+decision['reading'];inverse+='；'+decision['inverse']
 ledger.append(dict(passage_id=id,lesson_number=58,document_id=DOC,pdf_page=p['pdf_page'],role=p['role'],speaker=p['speaker'],published_at=p['published_at'],source_text_sha256=hashlib.sha256(p['text'].encode()).hexdigest(),result=result,claim_ids=[r['id'] for r in linked],related_existing_claim_ids=retained[id],existing_evidence_not_mutated=True,pending_issue_ids=[x['id'] for x in pending if id in x['passage_ids']],reviewer=REVIEWER,rounds={'1_read_and_scope':reading,'2_atomic_conditions':atomic,'3_normalization':{'concept_labels':sorted({x for r in linked for x in r['concepts']}),'related_existing_claim_ids':retained[id],'note':'58早期线段/缺口例外与后精确分型笔分层；最近中枢/次级离返与点7更大层分开，潜在背驰不冒确认，4000概略与4015边界不混；形成中不冒完成，图周期不等走势级别；费用/技能/资金期限均保。'},'4_reverse_check':inverse}))
for f in figures:
 f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=f['note'],figure_source_review='实际查看436至443八页及4幅整图、436完整页；437/438当时可得但原发未核，439/441多日合并后加；MACD24-52与12-26、图框5分钟/正文1分、3404.25/3404及4016.30/4015不合并。',linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger)==72 and len(figures)==4
for suffix,data in [('reviewed.jsonl',rows),('coverage.jsonl',ledger),('pending.jsonl',pending),('figures.jsonl',figures)]:
 (OUT/f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x,ensure_ascii=False,separators=(',',':')) for x in data)+'\n',encoding='utf-8')
summary=dict(stage='C/E',schema_version=metadata['schema_version'],graph_version=metadata['graph_version'],lessons=[58],document_id=DOC,reviewer=REVIEWER,passages_read=len(ledger),claims=len(rows),evidence=sum(len(r['evidence']) for r in rows),importance_counts=dict(Counter(r['importance_level'] for r in rows)),new_concepts=sorted({x for r in rows for x in r['concepts']}-set(concepts)),whole_lesson_semantic_read_complete=True,technical_extraction_complete=False,four_round_review=True,independent_review_claimed=False,visual_pdf_pages=list(range(436,444)),figure_objects_viewed=4,figure_origin_counts=dict(Counter(f['origin_status'] for f in figures)),pending=[x['id'] for x in pending],source_passages_snapshot_sha256=SOURCE_SHA,retained_source_links_in_ledger_only=True,database_mode='ro',formal_import=False,delivery_scope='shared_knowledge_base_only',acceptance='58课72段8页4整图同模型四轮，25身份/日期修正及2未核2后加图；早期线段/最近枢三卖/潜在背驰/4015和4000/形成中及图级别与走势级别/费用技能条件分别保，待预检。')
(OUT/f'{BASE}.summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
db.close();sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(summary,ensure_ascii=False))


