"""Materialize the main agent's four-pass reading of lesson30.

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
BASE = 'c_stage_l030'
REVIEWER = 'Codex 主代理 / 阶段C上册30课同模型四轮复核'
SOURCE_SHA = 'bfb93bc01534626c83ecfae43bd0331970cbdf45a919773d6d2dbe0e66878d2a'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-030' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 60
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 213 AND 218 ORDER BY pdf_page,id', (DOC,))]
assert len(figures) == 0
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
    pending.append({'id': 'upper-l030-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})




c(30, 'pure-trading-price-not-information-completeness', '213-b008',
  '第30课作者从纯交易角度说，不论价格是否充分反映信息，交易仍按当下价格进行并构成价格，只研究价格随时间延伸的走势。',
  '当下|价格充分有效市场|走势|技术分析', 1, '纯交易研究视角是范围，不等证明所有信息已入价或基本面研究对所有目标无用；成交量被类比为最低时间段内重复成交量次。',
  ['作者所称纯交易与价格轨迹研究视角'], ambiguity='author_price_only_research_scope_not_empirical_information_efficiency')
c(30, 'ordered-price-path-and-irreversible-trading-time', '213-b009 214-b000',
  '作者说价格轨迹的前后已表示交易可按时间排序，理论以交易时间不可逆为前提；若今天交易可改成昨天或直接不算，理论随之失去基础。',
  '交易时间不可逆|价格充分有效市场|走势|交易条件', 1, '交易时间前提与物理时间哲学不是同一定理；交易事后可随意更改/作废是边界，不等普通停牌就违反不可逆。',
  ['可按时间排序且过去交易不被随意改写的价格轨迹'])
c(30, 'price-sufficient-market-author-defined', '214-b001',
  '作者把满足“交易以时间不可逆为前提、完全等价反映在价格轨迹上”的市场命名为价格充分有效市场，理论针对这个自定义范围。',
  '价格充分有效市场|交易时间不可逆|交易条件|走势', 1, '该命名不等市场价格已反映全部信息的有效市场假说；作者称当时全部正式市场满足是另一个未经项目核实的断言。',
  ['第30课作者对价格充分有效的专门定义'], ambiguity='author_defined_price_sufficiency_not_standard_information_efficient_market')
c(30, 'retroactive-cancellation-non-price-sufficient-example', '214-b001',
  '作者以昨天买石头、今天卖方强令交易不算且钱物均收回为非价格充分有效市场例，强调过去交易不能随意抹除。',
  '价格充分有效市场|交易时间不可逆|交易条件|边界条件', 2, '原文胁迫例仅说明定义外情形，不作为任何现实市场案件或现行交易撤销法律规则。')
c(30, 'reality-price-path-against-fixed-causal-models', '214-b002 214-b003',
  '作者将交易动机和恒定因子解释排除出其纯交易数学研究对象，批评决定论及随机论的永恒模式假设，并把现实交易产生的价格轨迹作为研究基础。',
  '技术分析|走势|价格充分有效市场', 3, '作者的方法论立场并未证明随机过程数学无效，也不构成经济学所有基本面/行为研究毫无价值的项目结论。',
  ['第30课纯交易研究对象之争'], ambiguity='author_methodological_polemic_not_refutation_of_all_other_models')
c(30, 'trade-deferral-from-response-and-social-differences', '214-b004',
  '作者以反应需要时间、社会结构多层与个体差异解释群体交易的延异性：即使相同原因下相同买卖也有先后，不会完全同时趋同。',
  '交易延异性|非完全绝对趋同交易|交易时间不可逆', 1, '这是作者对可分析走势现实基础的论述，非已验证所有订单绝无同时成交的统计定律；不会完全同时属群体行为总体。',
  ['第30课对群体交易延异性的论述'], ambiguity='author_group_heterogeneity_premise_not_measured_microstructure_law')
c(30, 'absolute-convergence-only-one-participant-boundary', '214-b005',
  '作者把一人吃进全部股票且每笔交易都仅他参与作为完全绝对趋同例，称其等同赌博；只要另有人买入或仍持有1股，就重新成为可由理论描述的非完全绝对趋同交易。',
  '非完全绝对趋同交易|交易延异性|边界条件|控盘', 1, '100%及另有人1股均为作者极端边界例，不是实证安全阈值，也不把单一因子驱动直接等同完全趋同。',
  ['第30课完全与非完全绝对趋同的极端示例'], ambiguity='author_one_share_boundary_example_not_trading_safety_threshold')
c(30, 'two-premises-and-absolute-validity-author-claim', '214-b006 215-b000',
  '第30课作者称理论只有两个界限：价格充分有效市场与非完全绝对趋同交易；只要两者存在，就永远绝对有效。',
  '价格充分有效市场|非完全绝对趋同交易|边界条件', 1, '这是作者对当时理论整体范围的强主张，压缩映射不动点类比未在本章给出公理/度量/压缩常数及证明；72课随后明确前提主要针对动力学，分别保留。',
  ['价格充分有效市场', '非完全绝对趋同交易'], ambiguity='author_absolute_validity_claim_and_later_dynamics_scope')
c(30, 'all-learners-not-identical-trades-author-argument', '215-b000',
  '作者认为学习人数乃至人人采用同一理论，也不会因社会结构和个体差异而造成完全绝对趋同，故不改变其理论有效性。',
  '非完全绝对趋同交易|交易延异性|操作熟练程度', 2, '关于群体学习与有效性是作者推理，不是所有参与者策略相同后的市场实验结果。',
  ['第30课对公开理论的自我说明'], ambiguity='author_universal_adoption_argument_not_tested')
c(30, 'entered-divergence-leg-can-break-and-reassess', '215-b000',
  '作者举日线被判断进入背驰段后遇绝对突发事件为例，小级别结构可能突然破裂并影响大级别，此时须基于新走势重新判断。',
  '背驰段|当下|小级别转大级别|走势预测|确认', 1, '进入背驰段不等已经成功背驰；原文极端事件是说明当下重估的假想，不认证事件发生、必可提前退出或无实际损失。',
  ['日线被判断进入背驰段后出现当下结构变化'], ambiguity='hypothetical_structure_break_and_no_execution_guarantee')
c(30, 'greater-level-control-energy-and-capital-skill-view', '215-b001',
  '作者认为资金越大对操作功力要求越高，级别越大控制干扰所需能量越大，周线以后基本无人完全控制，功力较浅者可提高操作级别加强安全性。',
  '资金管理|操作级别|操作熟练程度|控盘|市场风险', 2, '大资金须高两重、周线后基本不可控及安全性为作者武功类比和未量化经验，不是可检验资本/能量公式或周线必安全。',
  ['第30课理论普及时资金规模与操作级别讨论'], ambiguity='author_skill_energy_and_weekly_control_assertions_not_verified')
c(30, 'same-theory-different-capital-and-trader-outcomes', '215-b001',
  '作者说同一理论在不同资金规模、资金管理、选股策略、基本面把握、性格和气质下呈现不同结果，借此解释共同学习仍非完全趋同。',
  '非完全绝对趋同交易|资金管理|基本面|操作熟练程度|操作策略', 2, '与纯交易研究只看价格的范围分开；作者实际操作仍列基本面因素，不把13—30所有选股语境合成一条禁用基本面规则。')
c(30, 'monitor-two-premises-and-group-delayed-prices', '215-b002 216-b000',
  '作者再次要求监控两个前提，并说同法群体操作中早晚出手、心态与熟练程度会留下不同价格痕迹；趋同较强还可能造成级别延伸，收益仍会不同。',
  '价格充分有效市场|非完全绝对趋同交易|走势级别延续|操作熟练程度|市场心理', 2, '“完全数学公理化”“早在计算中”为自称，本段无公式或收益样本，不把群体早晚差异当已独立检验机制。', ambiguity='author_axiomatization_and_profit_difference_not_formally_demonstrated')
c(30, 'understanding-versus-practice-seen-heard-learned-done', '216-b001',
  '作者区分看明白与行得通，主张在交易中修炼，见、闻、学、行缺一不可；理论知识的理解本身不保证操作能力。',
  '操作熟练程度|操作策略|市场心理', 2, '修行和论语为作者学习观，不是心理资质测试或实测绩效标准。')
c(30, 'zero-vector-follow-market-metaphor', '216-b002',
  '作者把群体行为比作向量叠加、走势比作总向量，以先去贪婪恐惧的“零向量”比喻减少主观干扰，再顺市场总方向交易。',
  '市场心理|操作策略|走势', 3, '这是修行与顺势的比喻，先零向量后顺向增加力度两步不合成订单量恒等零，不构造未给出的向量数值模型。',
  ['第30课“恰好”、顺势与零向量的比喻'], ambiguity='metaphor_not_defined_quantitative_vector_model')
c(30, 'universal-no-greed-market-disappearance-author-view', '216-b003',
  '作者认为市场以贪婪恐惧为基础，若所有参与者都无贪婪恐惧，市场、货币与资本主义消失，其理论也不再存在。',
  '市场心理|市场规律|边界条件', 4, '作者哲学/政治推演与人类首次公理化的自评，非已证经济规律或历史优先权事实。', ambiguity='author_philosophical_counterfactual_and_priority_self_claim')
c(30, 'feb13-2850-one-minute-divergence-not-five', '216-b004 218-b012',
  '2月13日作者把2850压力附近的背驰定为1分钟并进入震荡；对读者10:45称5分背驰，回复仍是一分钟，其后补缺口就是反应。',
  '背驰|操作级别|缺口|中枢震荡', 2, '不认可读者5分钟归属或把补缺口当所有背驰固定后果；当时指数点位和作者判断未独立重算。',
  ['2007年2月13日指数解盘及16:38答复'], ambiguity='dated_index_level_judgment_not_recomputed_from_market_ticks')
c(30, 'first-center-next-center-lower-level-strength', '217-b004',
  '作者说第一个中枢后上扬一段若不出现背驰段，会形成第二个中枢；若后中枢级别比第一个低，上涨力度就强，详细规则留待后讲。',
  '走势中枢|背驰段|上涨|级别', 1, '这是本答对中枢前后幅度问题的条件说明，不认可读者蝴蝶对称；第二个的较低级别不能冒充同级趋势中枢计数，更不补强度百分比。',
  ['第一个中枢后上扬段未出现背驰段的讨论'], ambiguity='second_center_lower_level_context_not_full_strength_algorithm')
c(30, 'perfect-three-buy-points-usually-strong', '217-b005',
  '作者补充说一、二、三类买点都能完美出现的走势“基本比较厉害”。',
  '第一类买点|第二类买点|第三类买点|上涨', 2, '基本/比较的经验程度保留，不能倒推任何三买后必大涨或三个点必须无间隔依次出现。', ambiguity='qualitative_author_strength_heuristic_not_profit_law')
c(30, 'venture-capital-label-in-2007-reply', '217-b008',
  '作者对当时“创投”一词解释为风险投资、创业投资、VC。',
  '创业投资', 4, '仅记录2/13短答的词义对应，正文朝阳产业及将升温是当时展望，不提供当前基金分类、资质或投资推荐。',
  ['2007年2月13日15:18:47创投词义答复'])
c(30, 'one-extending-center-not-numbered-many', '217-b013',
  '作者回应头肩顶及三重叠中枢问题时说不必先套头肩顶；一个中枢还在延伸时就只有一个中枢，不存在中枢1、2的问题。',
  '走势中枢|中枢延伸|中枢扩展|走势分解', 1, '作者未逐一肯定读者重叠中枢1/2/3的编号及区间，也未在此补数学扩展公式，不能把同一延伸中心重复计数。')
c(30, '600607-after-buy-not-on-thirty-buy', '218-b001',
  '对读者600607开盘买入，作者说买在30分买点出现后的走势发展中，没有买在该30分买点上。',
  '买卖点|操作级别|确认', 2, '“股票没问题”是当时个股评价，不把读者盈利/放量/开盘等同三买确认，也不擅认该句同时肯定000581操作。',
  ['2007年2月13日对小丸子600607与000581问题的答复'], ambiguity='dated_stock_view_not_entry_validation')
c(30, 'third-buy-localize-like-first-below-sublevel', '218-b001',
  '作者说第三类买点仍按第一类买点的方法操作，但向次级别以下走势定位。',
  '第三类买点|第一类买点|次级别|区间套', 1, '定位方法类同不等三买在本级定义上就是一买；下级一买还须满足本级三买离开/回抽不入中枢的条件。')
c(30, '000581-third-buy-wait-completed-sublevel-retest', '218-b002',
  '作者用000581说明三买骗线：关键是次级回抽不能再进中枢，应耐心等次级走势发展走出，不能未走出来就冲入。',
  '第三类买点|次级别|完成|走势中枢|假突破|确认', 1, '不把放量脱离或主观以为向上当三买；不入中枢与次级走出联合保留，非预设固定等几根K。',
  ['2007年2月13日000581三买答复'])
c(30, 'lowest-three-consecutive-k-have-direction', '218-b005',
  '对自选最低级别三K中枢的追问，作者明确须连续三根且有方向；从高位下来形成时为下上下，并说分时图通常比把1分图当最低更清楚。',
  '最低级别|最小级别中枢|K线|重叠|次级别', 1, '须连读者自选最低如1分的口径和29条件，非后期严格1分必由三根K；下上下为从高位下来的例子，不是所有中枢唯一方向。',
  ['采用三K重叠的自选最低级别口径'], ['例子从高位下行时方向下上下'], ambiguity='early_lowest_k_overlap_choice_vs_later_recursive_minimum')
c(30, 'practice-one-stock-purpose-before-changing', '218-b008',
  '作者建议先明确操作目的；若纯粹练习，可选好一只股票反复操作，便于提高和培养感觉。',
  '操作熟练程度|操作策略|操作级别', 2, '个股中线不错及卖后找机会接回是当时案例评价，不把读者600001 14:20认证严格买点，也不规定所有资金永远只持一股。',
  ['目的为纯粹操作练习'])
c(30, 'novice-fundamental-near-bottom-large-buy-selection', '218-b009',
  '作者一般建议新手挑基本面有支持、股价离底部不远且大级别出现买点的股票反复操作，认为比频繁换股有效；熟练后另论。',
  '基本面|买卖点|操作级别|操作熟练程度|操作策略', 1, '三个条件并列，新手/一般/熟练后另论保留；原“不元”不静改原文，转述按该句语境作不远，不提供距离阈值或效率实测。',
  ['新手的一般操作练习选股建议', '基本面支持、离底部不远及大级别买点同时考虑'], ['熟练以后另论'], ambiguity='qualitative_near_bottom_and_efficiency_not_measured')

keep('213-b008 214-b000 214-b001', 'upper-l026-c-stage-technical-risk-reflected-in-price-author-view',
     '26纯技术风险视角与30价格轨迹范围互相参看，30交易时间不可逆另有前提，不能推出所有突发消息可无损规避。')
keep('214-b006 215-b000 215-b002 216-b000', 'lower-l072-dynamics-premises',
     '72明确以前两个前提主要针对动力学、形态学无此前提，是具体文字限定；30整体范围主张保留，不能仅按较晚日期全局覆盖。')
keep('215-b000', 'upper-l027-c-stage-nested-legs-must-be-inside-parent upper-l028-c-stage-completion-not-short-average-standing',
     '进入背驰段后仍可结构变化需重估，和嵌套父段/已完成判断分开；不由命名进入段保证成功背驰。')
keep('218-b001 218-b002', 'upper-l029-c-stage-small-capital-or-skilled-exit-rebuy-third upper-l029-c-stage-first-second-enter-then-watch-third-after-break',
     '29突破后观察三买，30补必须次级回抽已走出且不回中枢；方法定位按低级一买不等本级三买改名一买。')
keep('218-b005', 'upper-l029-c-stage-one-minute-lowest-three-k-only-if-chosen',
     '30补连续及方向，但仍是自选最低口径，不能取消29如果的条件或后期递归区别。')
keep('218-b009', 'upper-l026-c-stage-technical-risk-reflected-in-price-author-view',
     '纯价格轨迹的理论研究视角与新手实际选股看基本面范围分别保留，不用正文所有其他研究无用吞掉具体联合建议。')

issue('two-premises-and-later-dynamics-qualification', '214-b000 214-b001 214-b005 214-b006 215-b000 215-b002',
      '30将两个前提作为整体界限且声称永远绝对有效；72原文明说以前前提主要针对动力学，形态学不需，不能把早晚文本无条件混为一项。',
      '保存作者自定义价格充分有效≠全部信息反映、绝对趋同极端例；72有具体限制文字可关联，但本批不重写旧命题/证据或宣称形式证明完成。', True)
issue('axiomatization-fixed-point-and-vector-metaphors', '214-b002 214-b003 215-b000 215-b002 216-b002 216-b003',
      '完全数学公理化/压缩不动点类比没有形式对象和证明；向量/零向量是修行比喻，首次公理化/其他理论无价值/全无贪恐市场消失为作者自评与哲学立场。',
      '不补压缩常数、完备度量空间或订单向量算法，不以作者口吻替项目认证数学与历史优先权。', True)
issue('entered-leg-breakage-versus-guaranteed-result', '215-b000 215-b001 215-b002',
      '进入日线背驰段仍可由突发小结构破裂影响大结构，需当下重估；大资金高两重/周线无人完全控制和收益差异没有数值验证。',
      '区分进入段与成功背驰，不把通常未成交扩成必能规避损失；不把提高级别等同绝对安全或补实证胜率。', True)
issue('center-level-count-and-third-buy-completion', '217-b004 217-b005 217-b013 218-b001 218-b002 218-b017',
      '第二中枢可比第一低是答复强度口径，不直接计作同级趋势第二；延伸中只有一中枢，三买低级定位不改本级定义，CCTV解释仍读者。',
      '保留背驰段/无背驰、三买次级已走出且回抽不入中枢条件，不能用放量突破或读者三中枢编号建裸规则。', True)
issue('lowest-consecutive-k-direction-and-subsequent-recursion', '218-b004 218-b005',
      '三K须连续且有方向只对早期自选最低口径，分时图更清楚也非后期正式级别算法；下上下是从高位下来的条件例。',
      '关联29选择前提及后63/65递归区别，不默认每个1分中枢都是三根1分K或所有方向相同。', True)
issue('dated-commentary-cases-and-novice-selection', '216-b004 216-b005 217-b000 217-b008 218-b008 218-b009 218-b012',
      '1段跨页解盘已修2/14；创投升温/联通近5元/操盘自述及股票中线看好是当时观点，原“不元”留存；新手基本面/近底/大级别买点未给数值标准。',
      '不核收益/实际买点或把历史展望当当前推荐；新手与熟练、理论研究与实际选股分语境，读者CCTV不能升为作者答复。')

note('216-b005 217-b000', 'dated-forecast-self-report-and-date-header',
     '2/13创投升温预告及2/14对翌日指数、联通、资金兑现/操盘的自述已读；216末2/14时间管217第一段。',
     '未独立核市场因果、账户或资金流，不由对抗叙事制作操盘步骤，1段只改日期而原文/映射/坐标不改。')

relations = {
    'upper-l030-c-stage-price-sufficient-market-author-defined': [('价格充分有效市场', '交易时间不可逆', 'requires')],
    'upper-l030-c-stage-trade-deferral-from-response-and-social-differences': [('非完全绝对趋同交易', '交易延异性', 'related')],
    'upper-l030-c-stage-two-premises-and-absolute-validity-author-claim': [('价格充分有效市场', '非完全绝对趋同交易', 'related')],
    'upper-l030-c-stage-entered-divergence-leg-can-break-and-reassess': [('背驰段', '当下', 'qualifies')],
    'upper-l030-c-stage-same-theory-different-capital-and-trader-outcomes': [('非完全绝对趋同交易', '资金管理', 'related')],
    'upper-l030-c-stage-one-extending-center-not-numbered-many': [('中枢延伸', '走势分解', 'qualifies')],
    'upper-l030-c-stage-third-buy-localize-like-first-below-sublevel': [('第三类买点', '第一类买点', 'qualifies')],
    'upper-l030-c-stage-000581-third-buy-wait-completed-sublevel-retest': [('第三类买点', '完成', 'requires')],
    'upper-l030-c-stage-lowest-three-consecutive-k-have-direction': [('最小级别中枢', 'K线', 'qualifies')],
    'upper-l030-c-stage-novice-fundamental-near-bottom-large-buy-selection': [('操作熟练程度', '基本面', 'qualifies')],
}

for r in rows:
    r['relations'] = [{'source': a, 'target': b, 'type': t} for a, b, t in relations.get(r['id'], [])]
by_passage = defaultdict(list)
for r in rows:
    for e in r['evidence']:
        by_passage[e['passage_id']].append(r)
for item in pending:
    item['lesson_numbers'] = sorted({int(passages[x]['unit_id'].split('-')[1]) for x in item['passage_ids']})
    if item['id'].endswith('embedded-dates-and-figure-provenance'):
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
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], '读者蝴蝶对称、重叠三中枢编号、600607/000581点位、5分10:45及CCTV解释不作作者认可；作者更正和读者说法分开。'
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
        'note': '价格充分有效为作者自定义而非信息全反映，两前提与绝对性/证明分开，72明确限动力学另存；进入背驰段可结构破裂需重估，三买需已走出次级回抽，最低三K连续有方向，CCTV仍读者。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True, reviewer=REVIEWER, visual_review_note=f['note'],
             figure_source_review='本课实际页面无配图，图来源字段不适用。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 60 and Counter(x['lesson_number'] for x in ledger) == {30: 60}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [30], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(213, 219)), 'figure_objects_viewed': 0, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '30课60段6页无图同模型四轮；1跨页解盘日期修正，理论前提/绝对性与72动力学范围、当下结构变动、三买完成和最低三K连续方向条件保留，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


