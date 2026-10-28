"""Materialize the main agent's four-pass reading of lesson40.

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
BASE = 'c_stage_l040'
REVIEWER = 'Codex 主代理 / 阶段C上册40课同模型四轮复核'
SOURCE_SHA = '9a314fcecb5d53ca877e23f0a70277886945357e5552214800545b7938b822d9'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-040' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 125
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 291 AND 296 ORDER BY pdf_page,id', (DOC,))]
assert len(figures) == 7
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
    pending.append({'id': 'upper-l040-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})




















c(40, 'small-entry-large-rise-keep-small-or-upgrade-partial-small', '291-b001',
  '小级别进入后出现大级别上涨，作者列两选：继续小级别操作，或升级到大级别并部分保留小级操作；前者更累、精度要求高且容量低，较大资金较适合后者。',
  '操作级别|交易容量|资金管理|操作策略|同级别分解', 1, '是在更大上涨已出现语境选择，不是小级买错被套就随意改长线；资金/精度没有给统一数值门槛。')
c(40, 'Ai-divergence-next-protection-break-forms-higher-center', '291-b002',
  '沿39课例，作者说Ai/Ai+2盘背将演化为i偶时Ai+3跌破Ai高点、i奇时Ai+3升破Ai低点；Ai+1、Ai+2、Ai+3由此构30分中枢。',
  '同级别分解|盘整背驰|中枢扩展|走势中枢|高低点', 1, '沿A0向上a、各Ai为5分类型的编号及完成/重叠前提，不把任意新小背驰直接当高层中心；原文未展开全部形式证明。',
  ['第39课向上a+A的5分同级别分解例'], figs=[(291, 1), (291, 2)])
c(40, 'larger-centers-must-pass-next-level-first', '291-b002',
  '作者强调更大中枢须先有高一级中枢，原例先有30分，才谈日周月；据此可把小级操作按模式换到高级。',
  '递归定义|级别|走势中枢|同级别分解|操作级别', 1, '该递归层次不等所有分钟图严格递归永久同名；结构可升级与个人是否换档分别保存。')
c(40, 'A0-through-At-equals-B1-B2-thirty-decomposition-switch', '291-b003',
  '5分同级别例中，若A0+A1+…+At=B1+B2，且后者为30分同级别分解，便可继续按后一分解操作。',
  '同级别分解|走势分解|操作级别|完成', 1, '换档依原式30分分解已成立，不任意把若干K或两个局部拐点命名B1/B2；本段未额外列B2所有完成判据或固定时间。')
c(40, 'switch-discretion-time-style-capital-larger-wave-benefit-view', '291-b003',
  '是否换高级取决时间、风格和资金；作者建议明显大级走好时可短线转中线，称这样可取得稳定的大级波动利益，小资金也可考虑。',
  '操作级别|资金管理|操作策略|走势预测', 2, '明显走好需实际结构而非亏损改口，稳定利益是作者条件性预期，不保证收益/成交或强制每次升级。', ambiguity='author_stable_larger_wave_benefit_not_empirical_guarantee')
c(40, 'N-layer-fugue-each-capital-shares-rhythm', '291-b004',
  '大资金可扩成N重层次，每层对应一定资金筹码、节奏波动；作者以赋格的多层动机、移位对位类比统一操作。',
  '多重赋格操作|同级别分解|仓位|操作级别|资金管理', 1, 'N未给固定数量或仓位比例，音乐为结构比喻，不以音乐法则证明市场波动或收益。')
c(40, 'each-layer-independent-and-integrated-own-level-rhythm', '291-b005',
  '多重赋格操作中各层遵守自身级别分解的节奏，投入资金筹码可不同；各层独立，又属于整体组合。',
  '多重赋格操作|同级别分解|操作级别|仓位|操作策略', 1, '独立是信号/筹码分层，并非风险完全无相关，未要求每层全仓或任意串用不同层买卖点。')
c(40, 'mar27-night-time-window-three-day-month-close-case', '292-b002 293-b000',
  '3月27日晚作者将当时市场看成多空拉锯，提此前高点21天前后、突破连线的三天确认，以及周末月线收盘引起犹豫与震荡。',
  '时间之窗|确认|高点连线|宏观市场判断|走势预测', 4, '具体历史时间观察，未统一自然日/交易日算法或证明21天定律；后图21(T)标注不静改正文，也不以后涨验真。',
  ['2007年3月27日21:29:47具体解盘'], figs=[(292, 1), (292, 2)])
c(40, 'mar27-second-line-earnings-relative-stability-author-view', '293-b001',
  '作者认为当时启动二线股因业绩等支持，比前期三线稳健，并将银行低调与市场力量分布相联系。',
  '二线股|三线股|基本面|板块轮动|宏观市场判断', 4, '历史比较和作者因果解释，不认证机构身份、实际业绩样本或当前二线必稳。', figs=[(292, 1), (292, 2)])
c(40, 'novice-five-day-hold-fallback', '293-b002',
  '作者建议技术好者按买卖点，暂不足者可先看均线系统，例为5日线不破就持有。',
  '均线系统|操作熟练程度|持股|买卖点', 2, '该时点辅助简法非中枢/背驰定义，也不保证不破5日线无亏损；原夜帖与次日头分开。', figs=[(292, 2)])
c(40, 'mar28-line-second-day-and-month-quarter-candle-case', '293-b003 293-b005',
  '3月28日作者称连线已第二天站稳，余两天关系月、季收盘，认为光头阳与长上影会影响后续心理和走势。',
  '确认|高点连线|K线|宏观市场判断|走势预测', 3, '当时判读及形态预期，第二天不是全书突破固定确认天数，月季收盘后果未在本批实证。')
c(40, 'non-MACD-moving-average-area-alternative', '293-b009',
  '问不用MACD如何判断背驰，作者说也可用均线系统，比较短期与长期均线之间的面积，并称方法不只一种。',
  '均线系统|指标对比|背驰|MACD', 1, '原未给长短周期、面积积分区间/符号/统一阈值，不能凭本答补成可独立复现算法或取消趋势级别条件。')
c(40, 'mar27-balanced-center-no-new-low-less-down-force', '293-b012',
  '对读者13:38无背驰却上涨的问法，作者称当日是围绕中枢的平衡震荡，并以午后不创新低判断下行力度弱于上午，应拉回。',
  '中枢震荡|盘整背驰|高低点|指标对比|确认', 1, '原否认读者所说上涨对象，并非否认所有局部涨跌；具体同向震荡比较不普遍证明任何未新低都必立即涨。',
  ['2007年3月27日21:41:16具体指数答复'], figs=[(294, 1)])
c(40, 'time-window-auxiliary-first-basic-framework', '294-b005',
  '问时间之窗课程时，作者答它属辅助，须先把基本理论框架弄好。',
  '时间之窗|操作熟练程度|技术分析', 1, '未给神秘周期或把时间窗当买卖点充分条件，不由辅助二字抹原已说过的具体历史观察。')
c(40, 'small-capital-two-three-sectors-one-stock-each', '294-b008 295-b000',
  '对资金不大的配置提问，作者说每板块一只足够、通常最多两三个板块可互相照应，并要求提高分析把握度。',
  '仓位|资金管理|板块轮动|操作熟练程度', 1, '未认可读者10至20万及20%短差作为普遍阈值，未给等权或说集中无风险；怕集中因没把握为作者训练评价。')
c(40, 'subminute-case-one-minute-green-area-two-sum-versus-one', '295-b009',
  '3月28日11:20例被作者归1分钟以下，借1分MACD柱面积比较：前面两个绿柱面积之和，后面一个；他说恐慌假突破常见此形。',
  'MACD柱波|MACD|指标对比|假突破|盘整背驰', 1, '原说两个绿柱子面积之和，按该例图文比较，不能抽成任意两根单柱高度或只数柱数；不把5分图周期升格该信号，常见未给统计。',
  ['2007年3月28日21:13:40对当日11:20具体例'], figs=[(295, 1), (296, 1)])
c(40, 'morning-five-top-sell-rhythm-before-bottom-precision', '295-b010',
  '作者强调若上午5分明显顶背驰先卖，后来回补早晚并非最重要，先后节奏更重要。',
  '背驰|机械化操作|操作策略|卖点|操作级别', 1, '在该已识别5分顶背驰的案例中比较精度和节奏，未授权任何价回补或取消成本/成交风险。', figs=[(295, 1), (296, 1)])
c(40, '000802-one-minute-above-fifteen-bottom-case', '295-b010',
  '同答作者另举000802，称1分上破15元后底背驰很明显。',
  '背驰|操作级别|确认|买点', 4, '只存当时作者个股判读，指数图不是000802证据，未核实际点位/收益，也不将15元普遍化。')
c(40, 'standard-divergence-two-small-trends-inside-trend', '296-b008',
  '回应读者17、24、37课看似冲突的引文，作者说最标准背驰是在趋势中比较两段小级别趋势。',
  '背驰|趋势|次级别|指标对比', 1, '读者引文仍是读者，本答未逐项证明A>B也属标准背驰或消除37 c内相对级别歧义，标准条件和推广分别存。')
c(40, 'divergence-method-extension-even-same-direction-center-waves', '296-b008',
  '作者说两段走势力度比较可推广，在中枢震荡中甚至两段同向上行也可用类似背驰方法比较，这是方法推广。',
  '背驰|盘整背驰|中枢震荡|指标对比', 1, '类似方法可用不等都改名标准趋势背驰，未取消没有趋势没有标准背驰或给每种推广完整判据。')


c(40, 'market-not-one-master-morning-afternoon-groups-differ', '297-b002',
  '作者提醒早晚拉升未必同一拨、早上卖者下午也可回补，否定把市场想成一个总庄家的简单叙事。',
  '主力资金|市场心理|操作熟练程度|操作策略', 3, '对多参与者可能性的提醒不等认证其对早盘动机的指控，也未回答读者全部银行后续路径。')
c(40, 'fund-weakness-vs-stable-long-no-cashout-author-view', '297-b005',
  '作者认为基金模式在心态浮动市场有被阻击清盘的弱点，并将稳定、长期、无套现压力的资金称最安全，认为基金不符合。',
  '基金|资金期限|市场风险|资金管理', 3, '这是作者概括，未区分基金类型、杠杆或赎回制度，最安全/可能很大无样本模型，不当当前所有基金必然清盘或无风险资金定义。', ambiguity='author_fund_liquidity_and_safety_generalization')
c(40, 'practice-precision-only-after-basic-buy-sell-rhythm', '297-b007',
  '作者说操作根本是买点买、卖点卖，熟练实践可提高精度；若基本节奏错，越练反而毛病越多。',
  '买卖点|机械化操作|操作熟练程度|操作策略', 1, '训练方向先于精度，不保证任何次数实践都单调提高或所有人即时识别买卖点。')
c(40, 'mar29-finance-buy-before-sell-current-not-force', '298-b004 298-b007',
  '3月29日午帖到夜帖，作者自述当日金融股应顺势先买后卖，并称是唯一正确策略而非继续压盘。',
  '操作策略|机械化操作|板块轮动|当下', 3, '具体历史应对与自评，不是所有金融股或所有日子固定先买后卖，未核实际账户/因果或唯一最优。', ambiguity='historical_self_report_only_correct_strategy_unverified')
c(40, 'mar29-index-distortion-shenzhen-and-own-stock-charts', '298-b005',
  '作者认为该阶段沪指有失真，可参考深圳指数，更应按个股自身图形进出；并预期股指期货后指数对个股指导更弱。',
  '指数走势背离|宏观市场判断|指数期货|操作策略', 2, '历史比较与推出前预测，未定义失真测度、证明对所有个股均有效或核现行期货制度。')
c(40, 'mar29-zero-cost-safe-negative-only-profit-author-strong-wording', '299-b001',
  '作者称散户主力都应震荡降低筹码成本，只有成本0才安全，0以下才是真正利润，并以此论证理论也适用大资金。',
  '成本|零成本持仓|负成本|交易容量|市场风险', 3, '现金净投入/成本会计口径非全部经济风险，未因强词或重复出现认证无回撤/流动性风险，也不把零以下才利润当统一会计定义。', ambiguity='cash_basis_safety_and_profit_definition_author_claim')
c(40, 'next-day-drop-possible-not-certain-many-participants-current', '299-b005',
  '对次日会否大跌，作者答不排除，举长上影后接长阴可能，同时强调市场非一人一派决定，战机多在当下形成。',
  '走势预测|K线|当下|宏观市场判断', 1, '可能非必然，所说痛苦半月为作者历史措辞，无量化预测或实际对手交易证明。')
c(40, 'underwater-stock-first-identify-divergence-level', '299-b011',
  '对读者称600238底背驰后仍被套，作者要求先想清背驰级别。',
  '背驰|级别|操作级别|确认', 1, '没有据问句认可读者已正确判底背驰，亦不因小级点推所有大级持仓安全。')
c(40, 'any-underwater-not-buy-point-author-claim-tension', '299-b014',
  '作者在答二线被套时声称任何被套肯定不是在买点买，并归因明知非买点仍手痒的心态。',
  '买点|市场风险|市场心理|确认', 3, '保留作者绝对措辞；39称非最低那笔总有被套，与此处被套非买点存在范围/时长未明的张力，不能自行用事后结果定义买点正确或抹执行风险。', ambiguity='underwater_claim_scope_tension_with_lesson39_not_resolved')
c(40, 'good-stock-buy-point-large-level-performance-metaphor', '299-b015 300-b000',
  '作者把买点上的股票称好股票、其余称垃圾，大级买点称最好绩优股，要求耐心等待。',
  '买点|操作级别|基本面|市场心理', 3, '这里好/垃圾/绩优为操作时点修辞，不替代企业财务业绩或实际基本面质量，不据此贬称真实发行人。')
c(40, 'boc-unicom-small-amplitude-retail-000802-timing-case', '300-b003',
  '作者称中行联通波动小不适散户，重视买卖时点而非追随名称，并举000802即使被看好，17元以上在当时两天也属不佳买入。',
  '幅度|交易容量|买卖点|操作策略', 2, '具体2007年比较与时段，未认证收益或给当前价位建议；无需因无金融股而追入，股票喜好不替代信号。')
c(40, 'rhythm-makes-unbeatable-and-lower-cost-self-report', '300-b006',
  '作者自称筹码不少、成本越来越低，并用只要按市场节奏就无人能阻击或战胜的强措辞强调操作。',
  '机械化操作|成本|市场风险|操作熟练程度', 3, '行为/成本和无人能胜为作者自述修辞，无账户/对照/对手数据，不认证市场操作无风险或个人实盘行为。', ambiguity='author_unbeatable_rhythm_and_cost_self_report_unverified')
c(40, 'five-day-trim-versus-long-term-fundamental-valuation', '300-b013',
  '作者对信任博客而持股者，提出跌破5日线减仓等技术参照；若真中长线持有，则应分析基本面和相应价值位置。',
  '均线系统|基本面|长期投资|操作级别|仓位', 1, '技术操作和真中长线估值分情境，不认可因信任作者无条件持有；原16.5长阴为该未明确命名个股历史例，不擅绑定身份。')
c(40, 'market-rhythm-before-greed-fear-closing-advice', '301-b000',
  '结尾作者强调节奏属于市场，应抛开个人贪婪恐惧去观察，而非把愿望强加走势。',
  '机械化操作|市场心理|当下|操作熟练程度', 3, '训练建议不保证情绪可立刻消除或仅凭节奏感识别所有买卖点。')


keep('291-b001 291-b003 291-b004 291-b005', 'upper-l038-c-stage-different-position-portions-at-different-levels upper-l039-c-stage-center-can-grow-thirty-to-year-still-five-pair-operation',
     '40多重换档需出现高层分解，分层筹码各守本级，不能亏损才改中线或多层混用信号；38分仓未给份额仍保留。')
keep('291-b002', 'upper-l039-c-stage-pair-divergence-even-i-plus-two-sell-odd-buy upper-l039-c-stage-no-divergence-even-hold-until-protection-break-then-exit upper-l039-c-stage-no-divergence-odd-stay-cash-until-protection-break-rebuy',
     '40说明盘背后保护位演化形成次高层，非重写39无盘背支或将Ai+3破位压成同价即时操作。')
keep('293-b009 295-b009 296-b008', 'upper-l034-c-stage-a-plus-b-plus-b-area-sum-not-maximum-bar upper-l037-c-stage-comparable-force-can-use-consolidation-divergence-method',
     'MA面积/1分柱波案例/方法推广均有语境，不能把面积一项、图周期或类似方法改成所有标准背驰充分条件。')
keep('296-b008', 'upper-l037-c-stage-trend-divergence-requires-trend-and-same-level-a-b upper-l037-c-stage-c-internal-two-sublevel-centers-original-relative-level',
     '40作者说无矛盾后给标准小趋势对比和推广，未逐项确认读者A>B亦标准或唯一化c内部相对层级，旧条件保留。')
keep('299-b001', 'upper-l035-c-stage-zero-cost-only-risk-escape-author-assertion upper-l031-c-stage-proportional-loss-and-no-desperate-position',
     '40再述成本0安全/负成本才利润是作者强主张，重复不形成经济风险证明，净现金成本与持仓市值风险分开。')
keep('299-b014', 'upper-l039-c-stage-not-lowest-print-may-be-underwater-direction-author-view',
     '39非最低那笔总有被套与40任何被套非买点的时长/完成/成交口径未明，保留张力，不用事后结果回写买点正确性。')
keep('300-b003 300-b013', 'upper-l038-c-stage-boc-small-capital-amplitude-not-general-investor-target upper-l035-c-stage-chosen-level-own-buy-sell-enter-exit-no-own-down',
     '40强调时点/幅度和技术减仓vs真长线基本面，非受博客信任就持有，宏观喜好不取消本级卖点。')
note('291-b004 291-b005', 'musical-analogy-context', '作者以赋格、巴赫、不同音乐层次类比多级筹码和节奏，已读。',
     '音乐比喻不作市场定理、收益或听音乐有效性的证明，不据此操作其他应用。')
note('292-b001', 'midday-commentary-and-next-evening-time-tail', '3/27午间作者提谈判、板块和银行表现，自述已读；尾端21:29:47属夜帖头。',
     '会议/机构因果未经核验，原段保持12:57，夜帖只管后段，尾头原字符不拆改。')
note('293-b004', 'historical-political-and-hypothetical-positioning', '作者对机构、做空能力、未来期货的批评与假设已读。',
     '不以贬称建立真实主体、实际交易或技术实力，不将假设3000下当已发生。')
note('293-b012', 'historical-two-stock-reply-context', '同答末尾对读者所问600961/600713称中线可，保留为该历史问答上下文。',
     '未核当时标的完整结构/实际收益，不由短答认证读者30分三买或产生当前推荐。')
note('294-b002', 'historical-school-political-reply', '作者对938问题以学校/技术及当下作答，全文已读。',
     '未证学校领导关系、企业业绩或读者网页评价，不能从这句推基本面永远无用。')
note('295-b004 295-b005 295-b006', 'historical-bank-holdings-incentive-commentary', '作者以假设银行持仓和其他板块出货说明动机，附空头改观预期，已读。',
     '未核任何基金实际仓位、群体身份或行为，同一市场也非单一行动者；不转化为可执行操盘策略。')
note('297-b009 297-b010 297-b011 298-b000 298-b001 298-b002 298-b003', 'nontechnical-political-economy-essay-context',
     '3/29货币与资本主义社会三种幻影一文已逐段读完，讨论凭证、雇佣关系、消费主义和经济学起点的作者立场。',
     '非缠论结构/买卖点技术定义，保留完整作者评论原文，未将政治经济评价当科学定理、事实认证或行动指令。')
note('298-b006', 'midday-self-reported-combination-and-night-head', '作者把中行/联通称自己组合、谈争斗后板块轮动；尾21:44:58为夜帖头。',
     '原段保留午间12:41，夜头只管后文；未核账户组合或政治因果。')
note('298-b008 299-b000', 'historical-night-trade-self-report-context', '作者谈月季长影、二三线调整及次日以静制动，跨页已读。',
     '自述动作/对手/唯一招式未核，不认证操盘行为、压盘群体或未来所有行情。')
note('299-b008', 'unverified-fund-and-stock-allegation-context', '作者对999、600607和未具名基金的持股/出货/赎回数量自述已读并保留。',
     '基金身份、5000万/2000万数量和动机未核，非一般技术定义，不将指控当事实或猜基金/证券全名。')
note('300-b009', 'order-behavior-self-report-context', '作者否认自己填买单/对手盘的行为自述已读。',
     '未核订单数据，读者为何不撤单未得到通用解释，不据此生成具体下单策略。')
issue('upgrade-multilayer-decomposition-and-allocation', '291-b001 291-b002 291-b003 291-b004 291-b005',
      'Ai盘背后保护位演化高层，A0至At可重分B1+B2才可换30分；换档按时间/风格/资金，不同层份额节奏独立，稳定大波动利益未证。',
      '不把低买点不利后任意改中线，未给所有B2完成/换档比例算法或数学全证；音乐仅类比。', True)
issue('indicator-area-alternatives-and-subminute-scope', '293-b009 295-b009 295-b010',
      '均线长短面积未给周期/区间；1分钟以下借1分MACD，前两绿面积和对后一例不能改任意单柱高度，节奏优先非取消小级定位。',
      '与33黄白/面积范围和38A/C比较合读，不补唯一积分或通用所有背驰公式，不由图5分升格。', True)
issue('standard-divergence-and-generalization-reader-conflict', '296-b002 296-b003 296-b004 296-b005 296-b006 296-b007 296-b008',
      '17/24/37引文为读者，作者答最标准是趋势内两小趋势，比较可推广中枢同向波；未逐项证明A>B也标准或b与c层级完全等同。',
      '保留37标准条件与c内部相对层级待核，不能自动用无矛盾三字清除全体历史条件。', True)
issue('time-window-day-count-and-confirmation-history', '292-b002 293-b000 293-b002 293-b003 293-b005 294-b005',
      '21天/3天确认、月季K形是历史观察且时间窗称辅助；日/交易日计数、转折充分性和第二天站稳措辞未成为统一算法。',
      '后图21(T)不改正文/不证预测准确；保留当时均线简法和买卖点框架的区分。')
issue('underwater-buy-point-zero-cost-and-rhythm-safety-tensions', '299-b001 299-b011 299-b014 299-b015 300-b000 300-b006',
      '40被套非买点与39总有被套范围未明；成本0安全、负成本才利润、按节奏无人能胜是作者强主张，非风险/会计/实盘证明。',
      '不凭事后浮亏定义买点真伪，不删39原说；净现金成本/市值/流动性及定义时点需独立，不认证收益。', True)
issue('historical-fund-market-parties-and-self-report-context', '293-b001 294-b002 295-b004 295-b005 295-b006 297-b002 297-b005 297-b009 297-b010 297-b011 298-b000 298-b001 298-b002 298-b003 299-b008 300-b009',
      '基金清盘概率/安全资金、机构动机/持仓和货币政治评论均为作者观点自述，非已核当前市场或一般技术定义。',
      '保留原文及身份，不猜未名实体，不认证订单/持仓/清盘数量或现行基金制度。')
issue('rhythm-price-stock-vs-long-term-fundamentals', '294-b008 295-b000 297-b007 298-b004 298-b005 298-b007 299-b005 300-b003 300-b013 301-b000',
      '最多两三板块、午夜金融先买后卖、指引深圳和个股、自身图形及长线基本面都带时点/规模条件；好垃圾绩优为操作修辞。',
      '不认可读者20%/10至20万为通用配置，不给当前股票/价位指令，买卖点纪律与估值/幅度层次分开。', True)
issue('commentary-dates-and-figure-provenance', '292-b001 292-b002 293-b000 293-b001 293-b002 293-b003 293-b004 293-b005 298-b006 298-b007 298-b008 299-b000 299-b001',
      '11来源段按3/27夜/3/28收盘/3/29夜分组；7图3后加4原发未核，选择栏旧日期不代表右端无未来行情。',
      '原文/字符映射/坐标不改，读者引用和非技术附文不能变作者新技术定理或预测验真。')
relations = {
 'upper-l040-c-stage-small-entry-large-rise-keep-small-or-upgrade-partial-small': [('操作级别','交易容量','qualifies')],
 'upper-l040-c-stage-larger-centers-must-pass-next-level-first': [('走势中枢','递归定义','qualifies')],
 'upper-l040-c-stage-N-layer-fugue-each-capital-shares-rhythm': [('多重赋格操作','同级别分解','qualifies'),('多重赋格操作','仓位','qualifies')],
 'upper-l040-c-stage-each-layer-independent-and-integrated-own-level-rhythm': [('多重赋格操作','操作级别','qualifies')],
 'upper-l040-c-stage-non-MACD-moving-average-area-alternative': [('指标对比','均线系统','qualifies')],
 'upper-l040-c-stage-time-window-auxiliary-first-basic-framework': [('时间之窗','技术分析','qualifies')],
 'upper-l040-c-stage-small-capital-two-three-sectors-one-stock-each': [('仓位','板块轮动','qualifies')],
 'upper-l040-c-stage-subminute-case-one-minute-green-area-two-sum-versus-one': [('MACD柱波','假突破','qualifies')],
 'upper-l040-c-stage-divergence-method-extension-even-same-direction-center-waves': [('背驰','指标对比','qualifies')],
 'upper-l040-c-stage-fund-weakness-vs-stable-long-no-cashout-author-view': [('基金','资金期限','qualifies')],
 'upper-l040-c-stage-good-stock-buy-point-large-level-performance-metaphor': [('买点','基本面','qualifies')],
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
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], '读者17/24/37引文仍属读者，作者标准与推广答不能自动认可读者A>B标准背驰猜测；2成短差、10至20万、CCTV股票动员及未名基金均保留其来源身份和未核范围。'
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
        'note': '换档依高层分解出现而非任意套牢改级，N层各自筹码节奏；均线/柱面积案例与标准背驰/方法推广分开，零成本安全/被套非买点与39张力保留；货币评论作非技术上下文。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True, reviewer=REVIEWER, visual_review_note=f['note'],
             figure_source_review='本课7图全部查看，291两示意原发未核，292两图及294后行情为后加，295/296同日可用行情但原发未核；不以图周期升格1分以下信号或以后图证明时间窗。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 125 and Counter(x['lesson_number'] for x in ledger) == {40: 125}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [40], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(291, 302)), 'figure_objects_viewed': 7, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '40课125段11页7图及前后课边界同模型四轮；11跨时段来源日期修正，多层换档、MACD/均线辅助、标准与推广、被套/零成本强词和非技术附文分开，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


