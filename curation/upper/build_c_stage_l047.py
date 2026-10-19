"""Materialize the main agent's four-pass reading of lesson47.

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
BASE = 'c_stage_l047'
REVIEWER = 'Codex 主代理 / 阶段C上册47课同模型四轮复核'
SOURCE_SHA = 'e688fda4bc606a656164abd6fe37b7373bf3ed894e0b3d9165a2b0d6a7a0f57d'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-047' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 65
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 339 AND 347 ORDER BY pdf_page,id', (DOC,))]
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
    pending.append({'id': 'upper-l047-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})




















c(47,'apr19-1108-third-sell-last-theory-exit-not-arbitrary-later-sale','339-b002','作者把4月19日破5日线后的11:08反抽判为前日中枢三卖，称它是理论保障的最后离开机会；其后随意卖出不在他所论方法范围。','第三类卖点|均线系统|操作策略|卖点',1,'历史个案及理论方法边界，不将最后机会推为所有下跌唯一可成交时刻；所谓后来除最低外卖出皆对是作者事后范围说明，非预测/收益验证。')
c(47,'quick-recovery-possible-after-sale-wait-buy-point-precision','339-b003','破5日线后也可能很快回升；卖出者应等市场给买点，回补早可总结提高精度，作者在小级操作语境称节奏优先。','等待|买点|操作熟练程度|均线系统|操作策略',1,'可能非保证，回补过早不是自动正确买点；比没卖好是作者特定小级/小资金比较，不免交易成本和执行风险。')
c(47,'small-capital-small-level-only-daily-weekly-hold-separate-stock-chart','339-b004','以上短线例限较小资金和操作级别；按日线者在作者所判日线卖点未出现前可继续持有，周线大资金更无须理会，个股须在自身图上分析。','操作级别|交易容量|持股|买卖点|周期K线图',1,'1000多点持至当时是作者历史判点非所有股票通用指令；指数仅示范，不把股指买卖点/3358价位直接给个股。', ['较小资金、较小操作级别才适用前述短差程序'])
c(47,'first-three-no-overlap-case-excludes-two-day-centers-author-reasoning','339-b005','作者在该日11:08后以前三根30分K无重叠排除两日内中枢单边类，认为若成平衡市，中枢最好只能在11点后那根K范围内；无中枢则意味后续较大跌幅。','每日走势分类|每天走势上的中枢|K线|走势预测',1,'保存该案作者推理，不当项目已穷举所有8K证明；46允许中枢取后面几根，这里排除两中枢所需完整前提/边界仍待核。',ambiguity='author_case_exclusion_not_general_eight_bar_enumeration')
c(47,'after-third-sell-subminute-down-must-complete-author-100-percent-plan','339-b005','作者说该11:08三卖后至少有次级跌势，即1分以下下行须完成，据此称能100%确定安排后续可能回补。','第三类卖点|走势终完美|操作级别|买点|走势预测',1,'100%是作者该案条件内理论确定性措辞，不是经验胜率、精确价格时刻或已验证成交保证；至少下行完成不等立即底部或所有三卖都同一分钟以下级别。',ambiguity='author_theoretical_certainty_not_measured_success_rate')
c(47,'1330-three-bars-create-day-center-eliminate-zero-center-weak-balance','339-b006','到13:30连续三根30分K已共同重合形成当日中枢，作者据此排除无中枢下跌，将当天归最多弱平衡市，关注10:30至13:30中枢及前后下跌力度。','每天走势上的中枢|弱平衡市|每日走势分类|中枢震荡',1,'该日后续形成结构后的选择，不由13:30时间本身推任何日必平衡；仍为日内借用定义，非严格30分递归中枢。分时背景图不直接展示三根30分K，作者文字独立支持该分类。',figs=[(340,1)])
c(47,'five-minute-chart-area-below-five-signal-not-axis-return','340-b000','该案1分MACD不便看，作者改看5分图比较10:30前下跌绿柱面积与13:30后下跌；中间虽有红柱但黄白线未明显回0，所以后跌背驰不属5分，只能更低级甚至分笔。','MACD|MACD柱波|指标对比|背驰|操作级别',1,'观察周期与信号级别分开，红柱不等黄白线已回轴；不推所有未回轴走势必有低级背驰，也未给统一积分/端点算法。',figs=[(341,1),(341,2)])
c(47,'tiny-divergence-may-not-pull-entire-center-strength-context','340-b000','作者说特小级别背驰未必有足够力度把走势拉回该中枢，但中枢存在使力度可预期。','背驰|中枢回拉作用|动力学|走势预测',1,'预期不是必完整回归或固定幅度；该句限定须与后文强回拉/最后反弹位保证和未保证回整个中枢联合，不能静抹。')
c(47,'before-new-break-author-certain-analysis-wait-compare-not-trade-guarantee','340-b001','作者称13:30尚未再破位时可100%给出逻辑分析；假设11:08三卖已退出且做小级，接着应耐心等待，在5分图比较下跌力度。','等待|操作级别|第三类卖点|MACD|走势预测',1,'确定分析该看什么与确定未来价格/可成交不同；100%是作者主张未独立证成所有市场，保留已卖/小级条件，不鼓励一切资金复制。', ['该日已在11:08三卖退出','小级别操作，当前目的为等回补'],ambiguity='author_100_percent_logic_scope_not_empirical_proof')
c(47,'tick-divergence-strong-pullback-symmetry-not-absolute','340-b001','该案强回拉无需一定有1分背驰，分笔背驰也可引发；作者说中枢震荡一般有对称性但非绝对，应注意小级转大可能。','成交分笔|背驰|小级别转大级别|中枢震荡|动力学',1,'该案中枢与前跌反抽的语境不可删，不是任何分笔背驰必大回拉或统一左右对称公式。')
c(47,'tick-divergence-one-minute-MACD-bar-length-auxiliary-only','340-b001','作者括注分笔背驰一般可用1分MACD柱子长度辅助。','成交分笔|MACD柱波|MACD|指标对比|背驰',1,'保留分笔信号借1分柱长度辅助的特殊对象，不取代45/46中枢两段力度看面积；一般/辅助不等任意柱缩短就是已成背驰。')
c(47,'break-center-small-third-sell-consolidation-or-two-more-down-waves','340-b002','该次再破10:30至13:30中枢后先有小三卖，之后可成稍大盘整或继续下跌、至少再两段向下；作者说实际选了后者。','第三类卖点|盘整|下跌|走势类型|每天走势上的中枢',1,'盘整分支可等待选择介入而非立刻买，实际两波是已观察路径，非所有小三卖必固定两段/等时下行。')
c(47,'two-waves-after-small-third-sell-can-complete-not-necessarily-end','341-b000','对跌破中枢的该下跌，三卖后再两波便可随时完成；因该跌在1分以下，细部不能用1分背驰确认，只能看分笔背驰。','第三类卖点|走势终完美|背驰|成交分笔|操作级别',1,'可随时完成不等第二波末必已结束；该级别前提限定此例，不否认其他走势用1分背驰。')
c(47,'after1330-no-stronger-than-before1030-five-minute-area-shenzhen','341-b000','作者用5分MACD两绿面积比较，认为13:30后的下跌不强于10:30前，深成图更明显，据此断言该次后跌会强力回拉。','MACD柱波|中枢震荡|指标对比|动力学|走势预测',1,'保存不强于而非必须严格更小、以及作者强断言，未把两面积比较单独实证成普遍充分收益公式；当日中枢位置时间仍关键。',figs=[(341,1),(341,2)],ambiguity='author_case_strong_rebound_inference_not_general_forecast_accuracy')
c(47,'actual-1443-tick-divergence-morning-star-large-rebound-case','341-b001 342-b000','作者称实际第二波14:43分笔背驰后强回拉，1分该K为早晨之星，并用理论100%保证形容该例。','成交分笔|背驰|K线|中枢回拉作用|走势预测',2,'早晨之星为原文对该K称谓，不补所有形态构成/收益规则；14:43是当日例，实际低点/成交未外核，100%非项目评测值。',figs=[(342,1)],ambiguity='author_case_100_percent_guarantee_not_empirical_rate')
c(47,'strong-rebound-condition-day-balance-center-position-time-not-any-tick','342-b000','作者明确不是任意下跌分笔背驰都保证强回拉，而是该日平衡市类型、中枢位置和时间共同决定他所说的保证。','成交分笔|平衡市|每天走势上的中枢|中枢回拉作用',1,'这些条件限制保证的作用域，不证明所有同类形态成交可行；不能抽成见分笔背驰即无风险抄底。')
c(47,'minimum-last-rebound-place-not-full-center-return-guarantee','342-b000 343-b001','该案分笔背驰所保证的最低反抽位置是这次下跌最后一个反弹处，收盘已到；它并不100%保证完全回到中枢。','成交分笔|中枢回拉作用|价格区间|走势预测',1,'作者内部层次区分，最后反弹处不是中枢全部范围；既不静抹其理论强语，也不认证实际目标成交或固定幅度。')
c(47,'historical-3351-BOLL-mid-MA20-and-channel-3358-support','342-b001 343-b000','作者举日线布林中轨与20日线同在3351、实际低点3358，配1分下降通道下轨，认为多因素支持反抽位置。','布林通道|均线系统|技术分析|价格区间|确认',2,'历史数值/辅助解释，未独立核原行情/各指标参数或独立性；后日线图延到7月不证当时精准预测，原3358不据别图3359.04静改。',figs=[(342,2),(345,1)],ambiguity='historical_support_prices_and_indicator_confluence_not_verified')
c(47,'future-larger-divergence-or-direct-rise-market-chooses-center-key','343-b001','达到最后反弹处后，仍可继续下跌形成更大背驰再回拉，也可直接上行；市场选择，新中枢形成前旧中枢仍关键，4月20日中枢位置决定后续演化观察。','走势预测|当下|走势中枢|背驰|确认',1,'两条都可能，未承诺次日方向；420指正文时间语境，不能以后4/23图倒填4/20早上已经形成的未知中枢。')
c(47,'teaching-example-not-all-super-short-one-second-ability-rhetoric','343-b002','作者说分析范本可当下完成、熟练者甚至1秒看清，但反复强调只是示范分析，不鼓励所有人做超级短线，大级别分析原则一样。','操作熟练程度|操作级别|技术分析|操作策略',1,'1秒/最正确为作者能力强词非实际耗时评测，不证明所有人可复制或所有级别信号算法已给全。')
c(47,'Tplus1-even-3358-may-not-sell-next-day-Tplus0-intraday-exit','343-b002','作者承认T+1下即使3358买入，第二天仍可能出不掉；相较之下T+0超短可回拉最后反弹位卖出，再看下一买点。','T+1|T+0|成交分笔|操作级别|市场风险|买卖点',1,'讨论的是作者当时交易背景中隔日卖出限制，T+0不表示全部滑点/流动性/停牌或亏损风险消失，也不作现行交易制度建议；买入条件不自动保证卖出成交。')
c(47,'intraday-hedging-method-promised-not-given','343-b003','作者说深入理解当日辅助走势后可作当日对冲降成本，但具体办法留待下节。','对冲|成本|每日走势分类|操作策略',2,'本段未给完整对冲仓位、成交和制度约束算法，不能把预告当已交付可执行盈利策略。')
c(47,'index-external-influence-through-stock-internal-points','343-b003','作者认为大盘外因通过个股内在结构作用，可使有些股形成二三买、强中枢上移股忽略大盘；随跌者原有卖点，指数只放大向买点运动幅度，不改内在逻辑。','市场分力|买卖点|中枢上移|动力学|操作策略',1,'作者体系观点及研究建议，未逐股验证所有下跌必有先验卖点；不能把指数点位或方向直接当所有股票买卖点。')
c(47,'apr20-almost-no-day-center-up-3520-reclaimed-first-hour','343-b004','4月20日收盘作者称几乎无日内中枢上行，首小时已确认重新站稳3520，继原涨势；将继续害怕归为心态。','每日走势分类|确认|走势预测|市场心理',3,'历史判读和心理评价，几乎不等严格零重叠，后答承认极小中枢；未以事后涨幅证明每个人害怕均错或无风险。')
c(47,'medium-five-week-short-five-day-skills-qualified-following','343-b005 346-b015','作者给偏中线者看5周均线、不破可少看盘，短线要确认重新站稳5日线；后答跌破5周属较大调整，最精确仍需学中枢背驰。','均线系统|操作级别|操作熟练程度|持股',1,'历史能力/级别简法，不把5周不破证明所有股票安全或破线当严格级别定义；5日线单边非盘整限制仍按45保留。')
c(47,'apr23-no-day-center-rise-historical-statement-vs-tiny-overlap','345-b001','4月23日解盘作者先称无任何日内中枢单边上涨、站稳3520后创新高；晚间又澄清严格算有微小重叠，只是大看盘可忽略。','每日走势分类|每天走势上的中枢|确认|走势预测',2,'前后表述同时保留，近似观察与严格区间分开，不能自动把作者绝对无中枢句改成项目已验证无重叠；100%正常为其历史强语。',ambiguity='author_absolute_no_center_vs_later_tiny_overlap_qualification')
c(47,'frequent-switching-needs-skill-otherwise-conservative-learning','345-b002','作者认为频繁换股需好技术，反复换出后涨而换入不涨者应先保守持有、学习后再做换股短差。','操作熟练程度|操作策略|持股|市场心理',2,'作者能力训练/结果归因观点，不以短期另一股涨就单独证明全部策略错误，也不把保守持有当永久无风险。')
c(47,'gap-three-days-unfilled-breakaway-upside-author-conditional','345-b003','4月23日作者说若当日缺口在今后三天整理不破，就成所谓突破性缺口，拓展中短期上行目标，缺口也成后续下拉/支持和震荡因素。','突破性缺口|缺口|市场震荡|走势预测',1,'条件须三天后观察，不是预定只调整三天；强势目标为作者期望，缺口有牵引/支持双面，未给统计样本或当前普适参数。',figs=[(345,1)])
c(47,'three-day-gap-rule-not-absolute-large-statistical-concept','346-b005','回应为何三天，作者明确不是绝对，而是大统计概念：一般缺口后三天回补，若不回补则基本属突破性缺口。','突破性缺口|缺口|概率原则|确认',1,'大统计是作者措辞，本答没有样本/概率/检验，未说明自然日还是交易日；不能当固定倒计时必然规则。')
c(47,'five-day-support-gap-explanation-larger-adjustment-for-distant-gap','346-b005','作者用5日线三天后到缺口上方解释：不有效跌破该线则不补，随线推动续行；破线较大调整后才有回补机会，走远要更大级调整。','突破性缺口|缺口|均线系统|有效跌破|级别',2,'原5日上三天后一定在缺口上字样不改；为该历史技术解释非项目证明所有路径均如此，机会不等必补，未给有效跌破/移动均线全部参数。')
c(47,'thirty-minute-operation-observe-centers-in-departing-move','346-b008','问能否归结最后中枢与当下走势，作者说若按30分操作，应看从该30分中枢离开的那段走势里的中枢变化，细节后说。','操作级别|走势中枢|走势分解|当下',1,'关注离开段内部演化，不是只裸看单个最后中枢价位便穷尽全部系统；本答未给后续完整程序。')
c(47,'tiny-day-overlap-can-ignore-rough-view-ten-points-not-universal','346-b012','作者说严格算4、5、6也有点重叠，但几个点在大看盘可忽略，一般标准分时图中枢约需10来点，所以称当天几乎无中枢。','每天走势上的中枢|每日走势分类|价格区间|操作策略',1,'10来点是当时指数粗看幅度、未定精确阈值，不升为所有市场/严格递归中枢统一最小10点；严格交叠与可忽略是不同判断。')
c(47,'source-3892-3688-versus-3688-3692-number-tension','346-b012 347-b006','答K线重合作者先举一个最高3892、一个最低3688，后又给3688至3692小区间作次日强弱参考；两处数值按原页保留。','每天走势上的中枢|价格区间|确认|高低点',3,'3892已看原页确认字面，与后3692不静合；两个高低数不是完整三根各区间数据，不能单据这两数证明三K共同交集或私改为3692。',ambiguity='source_3892_vs_3692_and_incomplete_three_intervals')
c(47,'strict-five-center-three-one-types-day-center-borrowed-different','347-b005','作者明确5分中枢需三段1分级别走势重合，而这两节讲分时看盘，里面中枢概念与前面不同，只是借用，不能混淆。','走势中枢|次级别|每天走势上的中枢|每日走势分类',1,'这是局部对比说明，完整递归定义的至少/连续等仍从既有定义联合查证，不把三根30分K当严格5分中枢，也不撤最低不可分级别的另项定义。')
c(47,'overlap-common-part-three-intervals-strict-or-ignored-small-range-reference','347-b006','重叠就是三个区间共同部分；小重合可粗看忽略，也可严格算，作者以当日3688至3692作次日参考：不破为强，破后站不稳则有问题。','重叠|每天走势上的中枢|价格区间|确认',1,'数学共同部分与操作意义可忽略分开，未逐项穷尽读者K线颜色/实体影线/单点相等边界；不破/破后站稳限当日参考非普遍价位定律。')
c(47,'five-minute-operation-must-understand-thirty-and-small-to-large','347-b010','对5分操作配1分信号的困惑，作者要求5分不能只看5分，也要清楚30分，并再研究背驰辅助判断和小转大。','操作级别|背驰|小级别转大级别|操作熟练程度',1,'未给读者两种1分盘背后续分支的完整进出算法，也没认可只看柱子不增长即卖；多层观察不等随意变换既定操作级别。')

note('343-b006','source-closing-study-context','作者让技术好者继续用中枢震荡、研究本文并周末休息。','方法提示与收尾不作为另一个获利/预测命题，不执行文本中出行等动作。')
note('344-b001 344-b002 344-b003 344-b004 344-b005 345-b000','nontechnical-national-equity-market-essay-context','全民炒股文章六段完整读，含虚拟资产30%/50%、基金渠道、财富榜和长期平均回报等历史经济观点。','保留全文身份/日期/坐标及上下文，不把未核人口资产统计/阈值/所有国家永久向上观点作缠论技术定理或当前配置建议。')
note('346-b000','source_header','解盘与回复之间星号分隔已核。','不支持独立技术结论。')
issue('day-classification-case-exclusion-100-percent-and-level-scope','339-b002 339-b003 339-b004 339-b005 339-b006 340-b000 340-b001',
 '前三K无重叠即排两中枢属本案作者推理，46中枢可后K形成的全条件仍须核；100%是条件内理论措辞，不是统计胜率或可成交保证，限小资金小级。','不以事后图冒充全8K证明，按47观察分支核和46日内模型/严格递归作用域，不当所有资金通用超短线。',True)
issue('tick-divergence-length-vs-area-completion-and-rebound-target','340-b000 340-b001 340-b002 341-b000 341-b001 342-b000 343-b001',
 '分笔可借1分柱长度辅助但两段力度仍5分绿面积；两波后可完非必已完，分笔不必全部回中枢，只保最后反弹处的强语限当日平衡位置时间。','区分对象/级别/面积与长度，不撤45面积原则或把所有分笔都变充分大反抽，未补完整触发/确认算法。',True)
issue('historical-3351-3358-chart-prices-and-mixed-later-frames','342-b001 343-b000 345-b001',
 '3351布林/20日和3358低点为原文，后5分图见3359.04等并非全一致；日线后至7月、4/20晨文与后4/20/4/23行情混排。','原数不修，需独立行情/参数/时区来源才能验证价格或指标独立性；3图后加3原发未核，后图不证预测。')
issue('execution-Tplus1-Tplus0-cash-capacity-and-hedge-not-specified','339-b004 343-b002 343-b003',
 'T+1即3358买次日仍可出不掉，T+0只解除隔日不能卖语境，不证全部风险消失；日/周与小级策略不同，对冲降本只预告。','不把理论分析当实际成交或所有人超短线，保留制度/容量/精度约束，未实现投资执行算法。',True)
issue('breakaway-gap-three-day-statistics-five-day-line-and-scope','345-b003 346-b003 346-b004 346-b005',
 '三天缺口判据明确非绝对大统计但无样本/天数口径；5日线三天到缺口上方为作者解释，机会非必补、有效破位未量化。','不把三天当固定调整时限或所有标的充分条件，后课找例外/级别，不自补EPS/数值阈值。',True)
issue('borrowed-center-three-intervals-tiny-ignore-3892-3692-and-reader-questions','345-b001 346-b010 346-b011 346-b012 347-b002 347-b003 347-b004 347-b005 347-b006',
 '作者明确日内中枢借用，严格5分要三段1分；粗忽略几点与严格交集有别，3892/3688与3688至3692未一致，颜色/实体/等值提问未逐项细答。','绝不静合两定义或把10来点当递归硬阈值；原字保持、别把读者引文当作者独立原证，回查三完整区间再判断。',True)
issue('multi-level-skill-mean-line-reassurance-and-internal-stock-logic','343-b003 343-b004 343-b005 345-b001 345-b002 346-b008 346-b015 347-b009 347-b010',
 '日周资金/5周5日简法与小级不同；任何指数影响只放大个股内在结构是作者体系观点非逐股实证，换股失败归因技能未必唯一，离开段内中枢细节未全。','保留45单边/盘整限制及46T+1/技能，不把近似无中枢历史涨势认证未来安全，后续继续审读。')
relations={
 'upper-l047-c-stage-small-capital-small-level-only-daily-weekly-hold-separate-stock-chart':[('操作级别','交易容量','qualifies')],
 'upper-l047-c-stage-five-minute-chart-area-below-five-signal-not-axis-return':[('MACD柱波','操作级别','qualifies')],
 'upper-l047-c-stage-tick-divergence-one-minute-MACD-bar-length-auxiliary-only':[('成交分笔','MACD柱波','qualifies')],
 'upper-l047-c-stage-minimum-last-rebound-place-not-full-center-return-guarantee':[('中枢回拉作用','价格区间','qualifies')],
 'upper-l047-c-stage-Tplus1-even-3358-may-not-sell-next-day-Tplus0-intraday-exit':[('T+0','T+1','qualifies')],
 'upper-l047-c-stage-gap-three-days-unfilled-breakaway-upside-author-conditional':[('突破性缺口','缺口','qualifies')],
 'upper-l047-c-stage-three-day-gap-rule-not-absolute-large-statistical-concept':[('突破性缺口','概率原则','qualifies')],
 'upper-l047-c-stage-five-day-support-gap-explanation-larger-adjustment-for-distant-gap':[('突破性缺口','均线系统','qualifies')],
 'upper-l047-c-stage-tiny-day-overlap-can-ignore-rough-view-ten-points-not-universal':[('每天走势上的中枢','价格区间','qualifies')],
 'upper-l047-c-stage-strict-five-center-three-one-types-day-center-borrowed-different':[('每天走势上的中枢','走势中枢','qualifies')],
 'upper-l047-c-stage-overlap-common-part-three-intervals-strict-or-ignored-small-range-reference':[('重叠','确认','qualifies')],
 'upper-l047-c-stage-five-minute-operation-must-understand-thirty-and-small-to-large':[('操作级别','小级别转大级别','qualifies')],
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
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], '读者三天调整问法、几根K重合引文/否认、5分中枢与30分K混用和盘背分支问法保留身份；作者统计限定和借用概念澄清不静合严格递归、几数差异不修。'
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
        'note': '100%作者强语限当日结构/小级资金，分笔回最后反弹处非必全回枢，长度辅助非替两段面积；日内中枢借用与严格三段1分分开，极小忽略/3892数值差异和三日统计不改。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=f['note'],
             figure_source_review='6整图实际查看：340与341第一张/342第一张为4/19可得但原发未核；341第二图含4/20、342日线至7月、345至4/23相对晨文属后加。未来K不证保证/支撑，混正文与后评日期分开。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 65 and Counter(x['lesson_number'] for x in ledger) == {47: 65}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [47], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(339, 348)), 'figure_objects_viewed': 6, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '47课65段9页6图同模型四轮；13日期空格规范，图3后加3未核；案例推理强语/小资金级别、分笔最后反弹目标、T+1/0和借用中枢/三日缺口/数值张力分层，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


