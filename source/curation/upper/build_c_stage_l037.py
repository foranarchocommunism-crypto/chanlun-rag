"""Materialize the main agent's four-pass reading of lesson37.

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
BASE = 'c_stage_l037'
REVIEWER = 'Codex 主代理 / 阶段C上册37课同模型四轮复核'
SOURCE_SHA = '5cf8379e0443c6c84ebb8167bf9b4dca1cb7e6d2f650123a52a12cdf543aae43'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-037' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 75
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 276 AND 277 ORDER BY pdf_page,id', (DOC,))]
assert len(figures) == 2
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
    pending.append({'id': 'upper-l037-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})














c(37, 'trend-divergence-requires-trend-and-same-level-a-b', '273-b012',
  '没有趋势就没有本课所说的背驰；a+A+b+B+c有背驰的前提是整体为趋势，A、B为同级别中枢，不能只凭字母形式判断。',
  '背驰|趋势|同级别|走势中枢|走势类型', 1, 'A/B同级是必要条件，不是仅两同级中枢就充分成趋势或背驰；仍须方向、结构及力度等其余前提。')
c(37, 'a-larger-than-b-whole-oscillates-around-a-at-most-consolidation', '273-b012',
  '若A级别大于B，作者将全程写作a+A+(b+B+c)，a与(b+B+c)只是围绕A的小级波动，不能按原整体判趋势背驰，最多按盘整背驰。',
  '盘整背驰|背驰|中枢震荡|走势分解|级别', 1, '针对A比B大的原例，不据任意重括号取消其他级别真正趋势；盘背也仍需实际力度可比和判别。')
c(37, 'local-b-perspective-not-forget-whole-trend', '273-b012',
  '对最后中枢B，可从多义性角度把b、c看成B的次级波动；但不能因此忘记另一角度下全程是趋势且A/B同级。',
  '走势多义性|走势分解|背驰|盘整背驰|走势中枢', 1, '局部B的观察与整体趋势并存，多义不是任意改层级；不把同一段两个不同对象的判断混成一个无条件背驰。')
c(37, 'c-direct-sublevel-contains-b-third-point', '273-b013',
  '在所论典型趋势背驰结构中，作者要求c为次级别，至少包含B的一个第三类买卖点；否则只当B内小级波动，用盘整背驰处理。',
  '背驰|次级别|第三类买卖点|盘整背驰|走势中枢', 1, '限定相对B的c及该典型末段，不以任意B内小波动代c，也不能只看一笔价格离开就算完整次级类型。')
c(37, 'b-can-smaller-gaps-strongest-and-not-higher-than-c', '273-b013',
  'b可以小于次级别，作者称连续缺口的力度最大，同时要求b在级别上不能大于c。',
  '背驰|缺口|级别|次级别|走势类型', 1, '级别大小不等价格涨跌幅或MACD柱高，连续缺口力度最大是作者此处经验比较，未给跨品种统一力学量。')
c(37, 'c-gaps-while-b-sublevel-divergence-less-likely-weakest', '273-b013 274-b000',
  '若b为次级别而c连续跳空，作者说c即使未完最终也延续为次级，但背驰可能很小；即便背驰也特别警惕其后最弱走势。',
  '背驰|缺口|次级别|完成|市场风险', 3, '很小/极大均是作者强经验词，无频率样本；最弱结果不等无背驰或必直接反趋势，需与29转折三结果范围合读。',
  ['所论b次级而c连续缺口的趋势末段'], ambiguity='author_gap_divergence_probability_and_weakest_outcome_unquantified')
c(37, 'c-must-new-trend-high-or-low', '274-b001',
  '整体为上涨的典型趋势背驰结构，c必须创该走势新高；整体下跌则c必须创新低。',
  '背驰|上涨|下跌|高低点|趋势', 1, '是对应趋势路径的新高低，不是历史所有行情绝对新高低；创新高低必要而非一创即背驰。')
c(37, 'c-no-new-extreme-even-third-point-use-consolidation', '274-b001',
  '若c没有相应新高或新低，即使含B的第三类买卖点，仍可按围绕B的次级震荡用盘整背驰方式判断。',
  '盘整背驰|背驰|第三类买卖点|中枢震荡|高低点', 1, '三买卖点存在不独立充分证明整体趋势背驰；盘背方式可用也不等每例已确认盘背。')
c(37, 'c-internal-two-sublevel-centers-original-relative-level', '274-b001',
  '作者据c含B的三买卖点，称c至少包含两个“次级别中枢”，否则不足满足次级离开后次级回拉不重回中枢。',
  '第三类买卖点|次级别|走势中枢|背驰', 1, '保留原次级别中枢措辞；c已称B次级，此处内部次级的相对对象须分层理解，未擅补唯一层级或改字。不能将c包含两个与B同级中枢作为新规则。',
  ['274-b001据c含B三买卖点所作的内部分析'], ambiguity='relative_sublevel_of_centers_inside_c_not_silently_resolved')
c(37, 'standard-c-internal-trend-recursive-interval-nesting', '274-b001',
  'c内部所述两个中枢若构成次级趋势，是作者称最标准常见的情况，可继续套用a+A+b+B+c分析其内部背驰，形成类似区间套的精确定位。',
  '背驰|区间套|次级别|趋势|走势分解', 1, '条件是内两中枢成趋势，并非所有c都强制标准小趋势；此处未给数值定位公式或保证恰成交极值。')
c(37, 'mar16-finance-participation-and-icbc-five-range-view', '274-b002',
  '3月16日作者认为指数脱离当时中枢需金融股配合，持续攻击有难度；中线仍将工行视为围绕5元上下的大级震荡。',
  '走势中枢|板块轮动|宏观市场判断|中枢震荡', 4, '具体历史判断与作者自述，未核机构身份、因果或真实交易；工行5元不是现价/目标价建议。')
c(37, 'mar16-before-third-buy-continue-oscillation', '274-b003',
  '作者对3月16日当时指数说，第三类买点出现之前继续震荡，要求熟练应对已多次出现的结构。',
  '第三类买点|中枢震荡|操作熟练程度|确认', 2, '具体当时状态，不等任何中枢永不改变边界或只要无三买就不会出现三卖；原文会议自述不触发外部行动。')
c(37, 'mar19-china-global-growth-source-and-exchange-forecast', '274-b008',
  '3月19日作者把中国崛起视为全球经济新动力，预言中国股市与交易所将成世界性市场，并以此解释其长牛判断。',
  '宏观市场判断|基本面|成长性|走势预测', 4, '历史宏观论述与预测，不将必然等强词当已证事实或当前经济判断，也未做事后实现审计。')
c(37, 'mar19-historical-cycle-and-full-circulation-institutional-view', '275-b000',
  '作者把1986至2001描述为第一轮大牛及其后四年大调整，并将2005年6月6日起新牛市与全流通改革相连，主张股票须有相同流通属性。',
  '全流通|交易规则|流通量|宏观市场判断', 4, '只存作者历史划分、制度观点及所记日期，不认证世界市场统一规律；全流通非所有股票随时无锁定可交易的现行规则。')
c(37, 'mar19-twenty-years-thirty-thousand-points-conditional-forecast', '275-b001',
  '作者以第二轮时间幅度超过第一轮的主张、以及1.5倍保守比例推断，称998起步的新牛市还将至少延续20年、上升3万点。',
  '宏观市场判断|走势预测|幅度|级别', 4, '20年/3万点是2007年预测而非已验证结论；原上升3万点不静改目标指数3万，世界无一例外及1.5假设均未获样本支持。',
  ['作者关于前后两轮可比及保守1.5比例的假设'], ambiguity='historical_macro_forecast_assumptions_unverified')
c(37, 'mar19-phase-one-reform-weights-marketcap-gdp-threshold', '275-b002',
  '作者把长牛第一阶段联系制度结构完善，侧重权重成分股，并声称总市值超GDP前该阶段不结束、此前谈泡沫可笑。',
  '宏观市场判断|全流通|基本面|市场风险', 4, '为作者阶段设想和估值强观点，市值/GDP不是本项目认定的无泡沫阈值，未补地域口径、分母时点或验证模型。')
c(37, 'mar19-phase-two-global-growth-asian-market-condition', '275-b003',
  '作者设想第二阶段随中国企业全球化，重点在有全球成长性的股票，并以中国股市成为亚洲市值最大且最重要前不结束作为判断。',
  '宏观市场判断|全球成长性|成长性|走势预测', 4, '历史条件预测，最重要未量化，未将成为亚洲最大认作第三类买点或技术级别完成定义。')
c(37, 'mar19-phase-three-global-integration-largest-market', '275-b004',
  '作者设想第三阶段重点为全球资源整合重组能力，预言中国股市成为世界最大且最重要市场前该阶段不结束。',
  '宏观市场判断|全球成长性|基本面|走势预测', 4, '阶段设想与中国GDP等宏观预言按历史作者论述保存，未验证实现、时间或投资收益。')
c(37, 'mar19-bubble-only-stage-author-historical-view', '275-b005',
  '作者在中国成为全球新动力的历史叙事下，将可能泡沫视作阶段性，并称此轮大牛是历史责任的呈现。',
  '宏观市场判断|市场风险|走势预测', 4, '叙事和规范评价不证明泡沫风险有限、不会长期亏损或任何股票值得买。')
c(37, 'mar19-one-attack-not-stable-three-thousand', '276-b001',
  '3月19日作者说3000点不会因一天上攻就站稳，尽管自述当日走势与中行启动曾被提示。',
  '确认|宏观市场判断|走势预测|有效跌破', 2, '站稳未给本段量化标准，自述预见/设计不认证操纵因果或预测准确率；3/21后图不倒证当日已知。',
  ['2007年3月19日15:18:14指数解盘'], figs=[(276, 1)])
c(37, 'market-many-participants-author-current-no-forcing', '276-b002',
  '作者说成分股启动能否燎原取决于所有参与者，不能由其一人决定，并强调按当下变化应对、不狂接硬撑。',
  '当下|操作策略|市场风险|宏观市场判断', 3, '作者市场观和行为自述，不证实际交易，也未让个人自述成为市场因果数据。')
c(37, 'mar19-sector-medium-long-view-structure-change', '276-b003',
  '作者将当时中长线观察联系经济增长方式变化，列环保含新能源、农业、军工和科技为关注方向。',
  '板块轮动|基本面|宏观市场判断|成长性', 4, '2007年历史观察池，不当当前行业推荐或行业内所有公司同样成长。')
c(37, 'mar20-two-day-three-thousand-lower-volume-then-up-view', '276-b005',
  '3月20日作者把3000点由此前一日游到至少两日游的缩量整理视为先站稳再谋上攻，并称3000主要是心理关口。',
  '确认|市场心理|宏观市场判断|成交量', 3, '历史当时观察与偏好，非两日缩量即普遍有效突破规则；图右端3/21不改3/20尚谋上攻的时态。',
  ['2007年3月20日15:24:15解盘'], figs=[(276, 1)])
c(37, 'medium-holding-partial-swings-not-limit-up-quality', '277-b001',
  '作者要求中线持股除部分筹码短差外应持住，认为敢涨停不等一定是好股票，最终涨幅比单次涨停更有意义。',
  '持股|仓位|涨停|操作策略|长期投资', 2, '本段中线持股口径不取消按本级卖点退出或个股风险，单次涨停并非质量充分证据。')
c(37, '600195-three-to-eleven-and-fivefold-self-report-not-reconciled', '277-b001',
  '作者举600195中牧自前一年4月中3元多到11元、从未涨停为例，同时称其一年未满翻5倍。',
  '涨停|成长性|幅度|复权|持股', 4, '3元多到11与翻5倍表述及图价不同，未核复权/起止或作者计倍口径，不强行算成一致或据图事后高价认证原说。',
  ['原3月20日解盘的作者个股例证'], figs=[(277, 1)], ambiguity='stated_price_range_and_fivefold_return_unreconciled')
c(37, 'twofold-no-limit-up-implies-five-ten-author-strong-claim', '277-b001',
  '作者进一步声称，一只已涨2倍还从未涨停的股票，只有将涨5倍甚至10倍这一种可能。',
  '涨停|走势预测|成长性|市场风险', 4, '只有一种可能是作者强经验断言，无样本或排他证明，本项目不据此生成保证倍涨或当前选股规则。', figs=[(277, 1)], ambiguity='author_exclusive_multifold_forecast_not_verified')
c(37, 'oscillating-climb-amplitude-potential-and-large-capacity', '277-b002',
  '作者偏好反复震荡爬升、可做多次短差的股票，重视波动和最终潜力，并称大资金无法天天追涨停。',
  '中枢震荡|交易容量|幅度|涨停|操作策略', 2, '是方法偏好与容量经验而非所有此形态必优，未给资金规模/容量阈值或保证每轮短差降成本。', figs=[(277, 1)])
c(37, 'near-market-means-current-clarity-not-physical-distance', '277-b007',
  '对读者抛后大涨而说离市场太近，作者重释近为对当下一目了然，远为走势无头绪乱猜，认为理解当下才不被波动迷惑。',
  '当下|市场心理|操作熟练程度', 3, '近远是作者认知比喻，不是盯盘时间或物理距离标准，也未证明掌握理论可消除一切情绪。')
c(37, 'comparable-force-can-use-consolidation-divergence-method', '278-b001',
  '对构中枢三段能否比较盘背的问题，作者答只要能比较力度，就可用盘整背驰方法。',
  '盘整背驰|指标对比|走势中枢|走势分解', 1, '可用方法不等已判盘背；力度可比未给本段唯一公式，也不认可读者对a+A+b身份的所有前提。')
c(37, 'trend-divergence-ends-trend-consolidation-may-same-type', '278-b001',
  '作者强调背驰必须在趋势中并意味该趋势结束；盘整背驰不一定结束走势类型，可能仍在同一类型里。',
  '背驰|盘整背驰|趋势|完成|走势类型', 1, '结束趋势不等必直接形成反向趋势，和29的三结果分别保存；盘背也非一律不结束。')
c(37, 'agriculture-potential-policy-and-model-author-historical-view', '278-b004 278-b007 278-b008',
  '作者把农业潜力联系新农村与资源倾斜，认为关键是寻找适合模式，现多炒概念而后或有实质，具体装入哪只股票是另一问题。',
  '基本面|成长性|宏观市场判断|题材股', 4, '2007年政策/行业判断及推广模式自述，未核其实际项目或资源倾斜；未按读者皮棉生猪蘑菇种子给出具体偏好。')
c(37, 'reader-forex-question-author-futures-second-point-caution', '278-b011 278-b012',
  '读者问外汇，作者答期货趋势延伸强，不熟练者用第二类买卖点相对安全，防把延伸误认第一类；股票都判断不好应先学会再做期货。',
  '期货|第二类买卖点|第一类买卖点|走势延伸|操作熟练程度', 1, '问外汇而答期货的对象差异保留；未确认读者银行5至15倍杠杆、24小时或现行产品规则，相对安全非保本。')
c(37, 'all-buy-sell-ultimately-first-points-different-levels', '279-b003',
  '作者答二三类点构成和次级盘整疑问时，概括所有买卖点归根结底都是第一类买卖点，只是级别不同。',
  '买卖点|第一类买卖点|第二类买卖点|第三类买卖点|级别', 1, '是层级归结，不将本级二三类名改一本级一类，也未在短答给出读者所求次级或次次级的完整证明/唯一层级算法。')
c(37, 'no-absolute-prediction-consolidation-trend-respond-current', '279-b003',
  '作者说无绝对规则预先区分盘整与趋势，三买后会面对较大盘整或趋势两支，关键是按当下实际情况立刻采取相应策略。',
  '第三类买点|走势预测|盘整|趋势|当下|操作策略', 1, '绝对预判不可能与可以分类备策不矛盾，不等不能做条件预测或所有概率信息都无意义。')
c(37, 'consolidation-strategy-reduce-cost-until-third-point', '279-b003',
  '对于盘整，作者建议制定相应操作策略降低筹码成本，直到第三类买卖点出现。',
  '盘整|成本|操作策略|第三类买卖点', 2, '降成本是目标非每轮必成功；不能用该建议抹本级离场条件、现实成本与成交误差。')
c(37, 'consolidation-extension-ends-third-point-when-probabilistic', '279-b004',
  '作者说盘整延伸无需预判，出现第三类买卖点自然结束；至于何时出现属于预测，任何预测都是或然的。',
  '盘整|走势延伸|第三类买卖点|走势预测|完成', 1, '所说本段盘整延伸的退出与其后仍可成更大中枢分别保存，不据此证明买点后永不回原区或整图中枢消失。')
c(37, 'over-ninety-prediction-accuracy-auxiliary-claim-not-method', '279-b004',
  '作者声称有配套手段可让预测准确率超过90%，但把这留作另一个问题。',
  '走势预测|确认|操作熟练程度', 3, '未给手段、预测事件、样本、分母、时间窗或评分标准，90%以上不当本系统实测指标或交易获利率。', ambiguity='author_prediction_accuracy_claim_without_protocol_or_data')
c(37, 'index-futures-direction-unchanged-extension-stronger-author-view', '279-b007 279-b008',
  '作者从纯走势角度认为股指期货推出不影响指数中长线总体方向，只会成为题材，并增强盘整延伸以及突破成趋势后的延伸。',
  '指数期货|期货|走势延伸|盘整|趋势|宏观市场判断', 3, '2007年推出前的作者预判，无因果或事后样本验证，非当前衍生品政策/风险结论，也不推出无杠杆或交割风险。')
c(37, 'center-overlap-not-occasional-wick-movement', '279-b012',
  '答影线重叠与偶然低价问题时，作者说中枢取重叠部分，偶然波动不因此计入中枢；围绕中枢波动理论上可到任意价位。',
  '走势中枢|重叠|波动区间|中枢震荡|高低点', 1, '中枢区间和外围波动分开，不据此普遍删除上下影线/所有快速成交；未明确回答读者三根分钟线须连续还是只同中枢，不把读者记忆当作者规则。')

keep('273-b012 278-b001', 'upper-l015-c-stage-two-turning-paths-no-trend-no-divergence-scope upper-l031-c-stage-trend-c-versus-b-and-consolidation-around-center',
     '37明确趋势背驰和盘背对象，局部B多义观察不能抹同级A/B的整体趋势，结束与否分别处理。')
keep('273-b013 274-b000', 'upper-l029-c-stage-divergence-reversal-theorem-three-outcomes upper-l029-c-stage-only-dd-weakest-expands-last-center',
     '缺口c若背驰要防最弱结果为作者经验，不强行认证哪个结果已发生；转折三支仍开放。')
keep('274-b001', 'upper-l035-c-stage-large-buy-sell-is-sublevel-or-below-not-necessarily-direct upper-l036-c-stage-abc-compare-ac-consolidation-divergence-and-c-internal',
     '37典型c内部嵌套与35大点属小点同向但不逆推所有小点必大转折，c内部次级中枢原词不擅统一。')
keep('278-b001', 'upper-l036-c-stage-abc-compare-ac-consolidation-divergence-and-c-internal',
     '可比较力度便可用盘背方法不等已经盘背，也未补MACD单一面积充分条件。')
keep('279-b003 279-b004', 'upper-l035-c-stage-third-buy-after-second-center-not-guaranteed-up-daily-possible upper-l036-c-stage-key-after-third-trend-versus-larger-center-not-yet-algorithm',
     '37强调不可绝对预判两支并以当下应对；概括归一类点不提供读者要求的完整固定层级/次级盘整终点证明。')
keep('279-b012', 'upper-l032-c-stage-2915-is-gg-not-center-top-2894-correction upper-l036-c-stage-mar8-1000-third-buy-below-old-swing-high-not-center-top',
     '37进一步区分重叠中枢与外围偶然价位，不由读者影线问题取消所有极值或改变已存GG/ZG。')
note('273-b011', 'source_intro', '正文说明用典型a+A+b+B+c澄清混淆，已读。', '只作后段技术条件的引言，不把字母形式独立作趋势成立证明。')
note('274-b004', 'historical-political-commentary', '3/16补充作者政治贬称、会议与应对自述已读。', '身份、行动与动机未经核验，不将贬称作市场因果事实或对外行动指令。')
note('274-b006 274-b007 275-b006', 'poem-and-literary-framing', '作者诗句与结尾复现已读并完整保留。', '文学表达不作为技术定义或预测实证。')
note('276-b004', 'historical-self-report-and-next-date-tail', '作者谈金融股、震荡降成本、长期准备及会议自述，末尾是下一段3/20时间头。',
     '未认证实际动作/每次震荡必降本，前段仍3/19；3/20头只管其后，原文不拆改。')
note('276-b006 277-b000', 'historical-political-context', '3/20解盘跨页批评和心理承受议论已读。', '不以政治贬称建立真实群体、行为或因果事实，保持跨页连续和3/20时点。')
note('277-b003', 'source_separator', '原文星号终止3/20解盘。', '只作来源边界不独立支持技术知识。')
issue('trend-same-level-c-sublevel-third-point-and-new-extreme', '273-b012 273-b013 274-b000 274-b001',
      '完整趋势/同级A-B、c次级含B三买卖点与新高低是联合前提；b可更小，c跳空即便背驰需防弱结果。',
      '不得只凭字母形式、仅两中心或一个新高判背驰，后文力度与c完成范围继续核查，强频率措辞无样本。', True)
issue('c-internal-sublevel-center-relative-level-and-recursion', '274-b001',
      'c已称B次级而后称c内两个次级别中枢，相对层级词须保留；内部两中心形成趋势为标准常见条件，不是任意c必再一完整趋势。',
      '后课更细结构前不改词或擅加唯一递归层级，区间套定位不认证实盘成交极点。', True)
issue('consolidation-divergence-comparable-force-and-trend-end', '273-b012 274-b001 278-b001',
      '局部B和整体趋势可多角度，盘背方法可用不等已盘背；背驰结束趋势非必反向，盘背可仍同类型。',
      '保留对象和完成状态，未给唯一力度公式，勿以晚回复抹早趋势必要前提。', True)
issue('all-points-first-level-and-third-after-paths', '279-b003 279-b004',
      '所有点归一类是层级概括，不给二三点确为次级/次次级一类的全证明或盘整延伸终点算法；三买后趋势/大盘整两支。',
      '接后续操作策略与完成标准，不补绝对预判；90%以上配套手段未披露，不当项目/实盘验收成绩。', True)
issue('wick-overlap-and-reader-three-minute-continuity-unanswered', '279-b010 279-b011 279-b012',
      '作者答重叠部分和偶然波动未明确回答三分钟是否连续；读者0.001可忽略及旧说只属读者。',
      '不擅删影线或伪造三K连续判据；保持中枢区间/外围波动及未答问题。', True)
issue('historical-macro-phases-returns-and-futures-predictions', '274-b008 275-b000 275-b001 275-b002 275-b003 275-b004 275-b005 277-b001 278-b011 279-b007 279-b008',
      '20年3万点、总市值/GDP泡沫界线、涨2倍必5/10倍及期货总体方向不变等为历史强预测，未核样本；外汇问期货答对象保留。',
      '只记录作者论述不当现行制度/政策或实际收益，银行杠杆/交易时段为读者不认证。')
issue('600195-three-to-eleven-fivefold-and-figure-not-reconciled', '277-b001 277-b002',
      '3元多到11却称未满一年翻5倍，图3.29到18.50等不是相同起止；复权、计倍口径与原图身份均未核。',
      '不静改原文或用图后高点替作者证明，保留语义不一致与历史股例范围。')
issue('commentary-dates-and-figure-provenance', '276-b004 276-b005 276-b006 277-b000 277-b001 277-b002 277-b003',
      '3/20头在3/19段尾，仅后6段日期修正；两图1后加1原发未核，诗文和历史宏观叙事不能当预测验真。',
      '原文/字符映射/坐标及前段时间不动，后图不证作者先知或实际控盘。')
relations = {
 'upper-l037-c-stage-trend-divergence-requires-trend-and-same-level-a-b': [('背驰','趋势','qualifies'),('背驰','同级别','qualifies')],
 'upper-l037-c-stage-a-larger-than-b-whole-oscillates-around-a-at-most-consolidation': [('盘整背驰','走势分解','qualifies')],
 'upper-l037-c-stage-c-direct-sublevel-contains-b-third-point': [('背驰','第三类买卖点','qualifies')],
 'upper-l037-c-stage-c-must-new-trend-high-or-low': [('背驰','高低点','qualifies')],
 'upper-l037-c-stage-standard-c-internal-trend-recursive-interval-nesting': [('区间套','次级别','qualifies')],
 'upper-l037-c-stage-trend-divergence-ends-trend-consolidation-may-same-type': [('盘整背驰','完成','qualifies')],
 'upper-l037-c-stage-all-buy-sell-ultimately-first-points-different-levels': [('买卖点','第一类买卖点','qualifies')],
 'upper-l037-c-stage-no-absolute-prediction-consolidation-trend-respond-current': [('第三类买点','当下','qualifies')],
 'upper-l037-c-stage-center-overlap-not-occasional-wick-movement': [('走势中枢','波动区间','qualifies')],
 'upper-l037-c-stage-mar19-historical-cycle-and-full-circulation-institutional-view': [('全流通','流通量','qualifies')],
 'upper-l037-c-stage-mar19-phase-two-global-growth-asian-market-condition': [('全球成长性','成长性','qualifies')],
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
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], '读者外汇/银行杠杆、次级与次次级一类点、盘整延伸及三根分钟线连续/同中枢等问句只作上下文，作者答复未逐项认可，不补不存在的明确答案。'
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
        'note': '趋势背驰须同级A/B、c次级含三买卖点和创新高低，内部次级中枢原词保留歧义；盘背可仍同类型，归一类点不补具体算法，宏观/收益/概率为历史主张非当前事实。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True, reviewer=REVIEWER, visual_review_note=f['note'],
             figure_source_review='本课2图全部查看；276右端3/21晚于所嵌3/16、19、20文字，277为同日3/20原发未核；600195图价/复权不能替正文3元多到11却称翻5倍。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 75 and Counter(x['lesson_number'] for x in ledger) == {37: 75}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [37], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(273, 280)), 'figure_objects_viewed': 2, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '37课75段7页2图及前后课边界同模型四轮；6段跨日日期修正，趋势背驰与盘背、c级别/新极值/内部层级歧义、历史预测与三K问答范围分开，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


