"""Materialize the main agent's four-pass reading of lesson31.

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
BASE = 'c_stage_l031'
REVIEWER = 'Codex 主代理 / 阶段C上册31课同模型四轮复核'
SOURCE_SHA = 'fd165c149345dae3105c167829481e35bb0fcdda2d2c16ddaeed86c067961ed2'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-031' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 183
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 219 AND 232 ORDER BY pdf_page,id', (DOC,))]
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
                          'figure_ids': [f'{DOC}-p{n:04d}-fig{k}' for n, k in figs] if i == 6 else []})
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
    pending.append({'id': 'upper-l031-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})





c(31, 'larger-capital-management-more-important', '219-b001',
  '作者说随着资金增长，资金管理越来越重要，大资金最终比的是管理水平，应从起初养成习惯，以免大级别调整中盈利被打回。',
  '资金管理|操作级别|市场风险', 1, '万元到千万元不难、短线客最终停滞等是作者经验概括，没有样本，不认证任何增长目标必可实现。')
c(31, 'long-pressure-free-funds-and-leverage-story', '219-b002',
  '作者要求资金长期无压力，以1996年朋友透支、急跌中被迫平仓而后股票大涨的故事说明杠杆会使人丧失持有主动权。',
  '资金期限|资金管理|被动带套|市场风险', 1, '不到10万/两千多万/不足20万和股价12至6至30为未独立核实故事；原文未具名，不由深天地A配图认证股票身份、杠杆规则或账户。',
  ['第31课长期无压力资金原则'], figs=[(219, 1)], ambiguity='historical_unnamed_leverage_story_not_independently_verified')
c(31, 'manage-own-capital-personally-author-rule', '220-b000',
  '作者要求自己的资金和盘子自己负责，不交别人管理，以1992年友人代管者擅自透支抄底的损失故事作警示。',
  '资金管理|资金期限|市场风险', 2, '这是作者个人管理原则与未具名历史故事，不是现行受托投资法律禁令，也不猜代管人身份。')
c(31, 'analysis-serves-capital-and-holding-level-transition', '220-b001',
  '作者把技术分析的用途归于资金管理：识别市场位置、如何建仓持有、把小级别持有逐步转大级别及如何退出，最终要收回资金。',
  '资金管理|操作级别|持股|技术分析|操作策略', 1, '转大级别是管理过程不是原小背驰自动生成大趋势；股票废纸等为风险修辞，不等持仓市值法律归零。')
c(31, 'proportional-loss-and-no-desperate-position', '220-b001',
  '作者反对背水一战式投资，强调不论资金大小都按比例损失，管理首先保持警觉，不能因规模大就认为不会被消灭。',
  '资金管理|仓位|市场风险', 1, '大资金与小资金相同比例损失的风险比喻不证明固定时间必归零，“最终必败”为作者强警示，未给概率模型。')
c(31, 'two-phases-cost-zero-then-earn-shares', '220-b002',
  '作者将单股管理分为成本为零前先降到零、为零后再挣股票两个阶段，直至历史性大顶，即至少月线以上卖点才考虑该终局退出。',
  '资金管理|成本|零成本持仓|操作级别|第一类卖点', 1, '零成本指原投入现金已收回的作者账户口径，不等剩余股票无经济价值或无风险；月线以上为所述长阶段终局，不取消期间短差。')
c(31, 'prepared-one-entry-no-upward-add-planned-allocation', '220-b002',
  '作者要求基本面和技术面研究充分、事前定好单股数量及占总资金比例，再一次性介入并留机动资金；反对上涨中不断追买加码、事后增加预定投入。',
  '资金管理|基本面|仓位|机动资金|追高', 1, '一次性与留机动资金同时保留，不等动用全部账户；本课后对弱技术者先3千/中线保持再补的例子另存，不能抹成统一禁加仓绝对命令。',
  ['充分准备并事先确定单股计划数量及资金占比'], ambiguity='planned_one_entry_and_later_skill_based_staging_contexts')
c(31, 'down-hold-has-thesis-and-severe-shape-exceptions', '220-b002',
  '对已买入后下跌的情形，作者说不可随意抛，可用预留机动资金做短差降成本；原文以“除非”保留买入理由消失、技术出现严重形态的退出限制。',
  '持股|机动资金|成本|市场风险|确认', 1, '原文两退出短语的关系未另给形式充要算法，不补为两个各自充分的独立信号；宁愿跌买不涨加码不能脱离前提解作无条件下跌无限补仓；机动例如1/10只是例。',
  ['所引已买入后下跌与机动短差的持有语境'], ['原文除非条款：证明买入理由没有了，技术上出现严重形态'],
  ambiguity='thesis_failure_and_severe_shape_exit_clause_relation_not_formalized')
c(31, 'before-zero-swing-must-not-increase-plan-shares', '220-b002',
  '在降到零成本之前，作者要求每次短差不增加原定股票数量，以回收现金降低成本；单股最初计划数量与占比确定后不再扩大预定投入。',
  '成本|资金管理|机动资金|仓位', 1, '目标总量不增加不等盘中卖出回补时股数永不变化；与成本零后再挣更多股的阶段区别保留。')
c(31, 'double-price-large-sell-recover-initial-capital', '220-b003',
  '除小级别短差外，作者主张股价达到约一倍升幅时找大级别卖点卖出部分，收回最初投入并使其所称持仓成本为零。',
  '零成本持仓|第一类卖点|成本|资金管理', 2, '原文约一倍与大级别卖点为联合口径，不是价格一翻倍立即机械卖一半；未计算费税、成交量或实际能否成交。')
c(31, 'after-zero-reinvest-swing-proceeds-for-more-shares', '220-b003 221-b000',
  '作者说成本为零以后，上方短差卖出再把所得全部用于下方回补，可使股数增加而不重新投入原本金；等待超大级别卖点结束该阶段。',
  '零成本持仓|机动资金|资金管理|操作级别', 2, '全回补是该阶段卖出所得的作者设想，不是把原来已收回本金再次全投；成本永远0与无论洗盘都增股未作费用/价差/成交实测，不据攻击修辞生成操盘计划。',
  ['已经按作者口径收回最初投入而成本为零', '短差能在较低位置回补'], ambiguity='zero_cash_basis_share_growth_strategy_not_empirical_guarantee')
c(31, 'large-consolidation-earn-shares-until-large-sell', '221-b001',
  '作者认为上涨后的大型盘整可用来挣回卖出股数甚至更多，只要超大级别卖点没出现；再次启动时希望持有更多零成本股。',
  '盘整|零成本持仓|持股|第一类卖点', 2, '盘整占一半以上、最安全与最大利润是作者未核比例及效果主张，并非每只股票保证能回补更多。', ambiguity='author_consolidation_duration_and_profit_claims_unmeasured')
c(31, 'recycle-recovered-capital-across-more-zero-cost-stocks', '221-b001',
  '作者把稳固持仓结构描述为零成本股票逐渐增多、收回资金再参与其他种类，直到大级别上涨结束清仓；意在不加单股操作资金难度。',
  '零成本持仓|资金管理|仓位|操作级别', 1, '对大资金增加种类的策略与小资金2/3只、避免十几只的答复范围分开；不会自动保证总体操作资金、风险或盈利不变。', ambiguity='author_capital_recycling_scheme_not_verified_portfolio_guarantee')
c(31, 'consolidation-reentry-sublevel-divergence-with-large-check', '222-b008',
  '盘背卖出后，作者说在次级背驰再接回，但必须看大级别；有盘不住倾向就不接，等破位后再论，精确解决留后课。',
  '盘整背驰|背驰|次级别|操作级别|操作策略', 1, '不认可读者跌成一个中枢即任意接回，也不把先破位当立即买点。',
  ['盘背退出后尝试次级回补', '大级别仍支持盘整维持'], ['有盘不住的倾向则不接'])
c(31, '000533-swing-small-size-and-replacement-question', '223-b001',
  '对000533复牌后大涨，作者建议先问退出后能否找到更好股票；短线有买卖点可分量卖回，不熟练者例如用1/10练习。',
  '操作熟练程度|仓位|机动资金|买卖点', 2, '一般复牌震荡后继续涨是当时经验非普遍复牌规律，不因涨50%就认证必须卖或读者无卖点判断准确。',
  ['2007年2月15日000533具体答复'], ambiguity='dated_stock_continuation_view_not_general_resume_rule')
c(31, 'midterm-entry-at-least-daily-buy-not-falling-blind', '223-b008',
  '对下跌中机动资金被套，作者先要求等买点，认为中线仓位至少应在日线级别买点介入才有中线运用价值。',
  '机动资金|买卖点|操作级别|持股', 1, '不能用正文宁愿跌买改成不等买点的补仓；中线仓位范围不套到所有短线练习。')
c(31, 'skill-based-entry-size-three-vs-eight-thousand', '223-b009 223-b010',
  '作者对技术较弱者要求控制介入量：1万元中技术好可先8千、不好可先3千；涨不追，跌而中线形态保持时在次级买点补，连涨跌都分不清则先不操作。',
  '操作熟练程度|仓位|次级别|买卖点|追高', 1, '8千/3千为例示非固定80%/30%仓位法，与准备充分一次性介入分语境；必须中线形态保持且次级买点，不是连续下跌无条件加。',
  ['技术不过关者以较小初始量控制错误风险', '下跌后中线形态保持且出现次级买点才补'], ambiguity='skill_based_staging_example_vs_prepared_one_entry_context')
c(31, 'standard-trend-nesting-with-sudden-break-exception', '224-b003',
  '在标准趋势中，作者否定次级无背驰而大级别先背驰的通常情形；标准状态是大级别先进入背驰段再逐级向下进入，但突发事件可使小级别突然破裂。',
  '趋势|区间套|背驰段|次级别|背驰', 1, '标准状态与除非例外同时保留，进入段并非已确认成功背驰，不能由本句推出所有事件下必可低级精确退出。',
  ['标准的趋势'], ['突发事件导致小级别突然破裂'])
c(31, 'feb15-center-1048-1129-third-buy-1413', '224-b006 225-b001',
  '作者把2月15日指数1048—1129认作上升调整中枢，第三段1114—1129、前三段同级，后面为延伸；1413三买确认该中枢完结。',
  '走势中枢|中枢延伸|第三类买点|完成|同级别', 1, '时间按原文紧写，读者1329笔误备注不视作额外作者更正文；完结属这个中枢而非一切更大走势已经完成。',
  ['2007年2月15日上证分钟图例'], figs=[(224, 1)])
c(31, 'third-buy-not-necessarily-after-consolidation-divergence', '225-b006',
  '作者允许强劲上涨、快速回调、再上升形成三买，不要求每个三买都先有盘背；关键仍是次级上去、次级回调不回中枢。',
  '第三类买点|盘整背驰|次级别|走势中枢', 1, '也有可能只回应有无其他形成途径，不认可读者每个新中枢第三下行都自动是三买。')
c(31, 'trend-c-versus-b-and-consolidation-around-center', '225-b007',
  '作者在该答复说盘背一般发生于中枢震荡，趋势背驰比较a+A+b+B+c中的c与b。',
  '背驰|盘整背驰|中枢震荡|趋势|背驰段', 1, '一般及所设结构保留，不能把任意b/c柱高比较取代同向段、对应中枢、级别和回轴等其他联合条件。')
c(31, '600316-center-new-and-ma120-fallback', '225-b010',
  '对600316作者称中枢不断新生，可逐个观察；暂不会看时以5分120线作简便参照，未破则预期无大调整。',
  '中枢新生|均线|操作级别|调整', 2, '这是当时该股简便替代与预期，不把120均线加入严格中枢定义或证明任何股票不破就绝无下跌。', ambiguity='dated_stock_ma120_heuristic_not_universal_center_rule')
c(31, 'feb16-final-leg-possible-not-confirmed-daily-top', '226-b002 226-b005',
  '2月16日作者说即使创新高也可能进入最后一段，不能死多；即使该段结束，仍预期在该中枢上下震荡，之后牛市继续。',
  '背驰段|走势预测|中枢震荡|牛市阶段', 3, '几率不少不是日线已背驰，不认可读者60分400点后这次一定更大跌的全部推断，续牛仍历史展望。', ambiguity='dated_future_leg_and_bull_forecast_not_confirmed')
c(31, 'feb16-1405-divergence-and-later-selloff-case', '226-b008',
  '对2月16日14:05在5分图上是否背驰的问句，作者以随后杀跌作肯定式说明，并评价当时指数权重股表现。',
  '背驰|操作级别|调整', 3, '按问句图表范围解释作者答复，不扩成所有5分信号必等幅杀跌或项目已独立重算MACD。',
  ['2007年2月16日15:48:37指数答复'], figs=[(226, 1)], ambiguity='case_answer_depends_on_reader_question_not_recomputed')
c(31, 'index-divergence-stock-smaller-sell-midterm-ignore', '227-b000',
  '作者对指数背驰而个股似无卖点的问答说个股通常只是1分以下的小卖点，可短线对冲卖后再买；若做中线则可不理。',
  '背驰|买卖点|操作级别|对冲', 2, '不会没有是作者强断言，未展示每只股票证据；短线/中线策略不同，不据本段补所有个股隐形卖点。', ambiguity='author_universal_small_stock_signal_assertion_unverified')
c(31, 'feb26-three-thousand-may-enter-daily-leg', '227-b004',
  '2月26日作者预期指数即使站稳3000仍很可能进入日线背驰段，题材二三线股可能逐渐减弱指数影响，并说联通供观摩、散户没必要买。',
  '背驰段|操作级别|走势预测|题材股', 3, '进入背驰段可能性不是日背驰已经成立；历史题材判断不变当前推荐或已验指数独立定理。', ambiguity='dated_index_leg_probability_and_stock_decoupling_view')
c(31, 'feb27-first-minute-center-2869-next-conditional', '228-b003',
  '2月27日作者称中午已有第一个1分中枢，次日若开盘不马上回2869之上，会有第二个再进入背驰段，要求按图回补。',
  '走势中枢|背驰段|当下|走势预测|确认', 2, '明天开盘条件保留，不能说第二中枢或背驰此刻已完成；位置来自当时案例，不作当前指数阈值。', ambiguity='dated_conditional_second_center_forecast')
c(31, 'feb27-zero-cost-realization-self-report', '228-b004',
  '作者在2月27日称对已翻倍的000416、600432等兑现成本至零，之后进入挣筹码阶段；未大涨者仍等买点回补，并预期周线调整后继续向上。',
  '零成本持仓|资金管理|买卖点|走势预测', 3, '资金兑现是作者交易自述，无账户/费用证明；是两阶段实例而非本项目认定可实现的实盘绩效。', ambiguity='author_cash_recovery_trade_self_report_not_verified')
c(31, 'small-divergence-adjustment-not-necessarily-large', '228-b009 229-b000',
  '作者说背驰须有调整却未必大调整，盘背往往转三买；要判断5分影响先看30分是否可能进入背驰段，30分主升时5分常盘中调整，符合区间套者另须重视。',
  '背驰|盘整背驰|第三类买点|区间套|背驰段|操作级别', 1, '往往非必然，30分主升与大背驰段分开；不认可读者000761柱面积比较即足够确认其所有背驰/工行一二买。')
c(31, 'capital-zero-point-five-float-does-not-decide-entry', '229-b003',
  '作者答100万元入6000万流通盘的例说是否被套取决于买入位置，一般0.5%流通盘以下的量可忽略。',
  '交易容量|流通量|资金管理|买卖点', 2, '0.5%为作者经验比例，资金与流通股数需同量纲而文中未给换算；不是小于此比例就不会被套或没有冲击。',
  ['2007年2月26日资金规模与交易量问答'], ambiguity='author_capacity_ratio_units_and_execution_effect_not_tested')
c(31, 'two-three-stocks-versus-dozens-large-capital-exception', '229-b006 229-b007',
  '作者重申充分分析后一次性买、留机动资金、不追买，并说一般2、3只股票不算多，十几只应避免，资金特别大另论。',
  '资金管理|机动资金|仓位|追高', 2, '2/3非固定最多三只的硬限，大资金例外与零成本后增加种类分语境；不把一次性解成全账户梭哈。',
  ['一般资金的持股种类及准备原则'], ['资金特别大可另论'])
c(31, 'consolidation-type-contains-one-center-not-equal-center', '229-b010',
  '作者明确盘整是包含相应级别一个中枢的走势类型，盘整与中枢不是同一概念，延伸和扩展等可处在盘整中，应用中枢概念来精确说明盘整。',
  '盘整|走势类型|走势中枢|中枢延伸|中枢扩展', 1, '只含一个为相应级别，不排除内部低级多个中枢；扩展使级别改变时须重新判定，非原级别永不变化。')
c(31, 'small-capital-thirty-buy-prefer-no-daily-divergence-leg', '229-b013',
  '对600028作者说若资金不大且能短线操作，30分买点可用，最好日线不在背驰段。',
  '资金管理|操作级别|买卖点|背驰段', 2, '小资金和短线能力是联合前提，最好不是绝对不得有的定义；不认可读者周月不值得所有判断。')
c(31, 'capacity-thirty-float-versus-minute-ten-day-volume', '230-b000',
  '作者给两种容量经验：不到所操作股票流通盘千分之五时，基本30分以上可操作；1分操作量一般在10天均量的1%以下可顺利完成。',
  '交易容量|流通量|成交量|操作级别|资金管理', 1, '两个不同分母不可混用，10天均量未给按股数/金额与期间粒度的完整计算；非当前市场滑点/冲击/通道实测或保证成交规则。',
  ['第31课2007年2月26日作者容量经验'], ambiguity='historical_float_and_ten_day_volume_capacity_heuristics_unvalidated')
c(31, 'center-framework-earlier-kiss-only-reference', '230-b003',
  '作者说不要把中枢之前的概念混入后来框架；有了中枢，前面的吻等均线说法可只作参考。',
  '走势中枢|均线系统|技术分析', 1, '这是作者明确范围说明，不是按发表日期自动删除早期技术体系，亦不把均线吻改为中枢定义。')
c(31, 'type-taxonomy-and-same-level-decomposition', '230-b004 230-b005',
  '作者重申走势类型是趋势（上涨、下跌）和盘整，任意走势终将形成类型或叠加，并称市场走势可按级别分成同级类型叠加。',
  '走势类型|趋势|上涨|下跌|盘整|走势分解|同级别', 1, '叠加为原文措辞不补唯一分解算法，完成/构成中、不同级别不混同。')
c(31, 'perfect-means-center-eventually-forms-count-type', '230-b005',
  '作者把走势必完美解释为中枢终将形成；趋势与盘整区别在相应级别中枢个数，趋势两个以上、盘整一个。',
  '走势终完美|走势中枢|趋势|盘整|完成', 1, '两个以上按本书通常含两个及以上，不误成必须三；同级同向不重叠等完整趋势定义另保留，不能凭任意两个框就认证趋势。')
c(31, 'weekly-three-legs-original-explicitly-qualified', '231-b000 231-b003',
  '作者先把0124—0206和随后上涨说成周线中枢前两段、需要第三段；被问级别后明确承认“不太严谨”，严格说只是第一段内部第三小段。',
  '操作级别|走势中枢|走势终完美|次级别', 1, '同日明确自我收窄有文字证据，不能只取前半当严格周线分段；原月日紧写不补其他年度。',
  ['2007年2月27日16:17原说明与17:18明确限定联合阅读'], figs=[(230, 1)],
  ambiguity='author_explicit_same_day_qualification_of_weekly_leg_description')
c(31, 'weekly-center-first-daily-then-expand-case', '231-b003',
  '作者在该周线例的严格说明是先形成一个日线中枢，再扩张开去；当时只在第一段里面第三小段，后续细节还需两课。',
  '走势中枢|中枢扩张|操作级别|次级别|完成', 1, '前提次序及当时未完成保留，扩张按原词不自动等同后课扩展精确定义，也不宣称已形成完整周线中枢。',
  ['2007年2月27日17:18:33对前说不严谨的限定'], figs=[(230, 1)])
c(31, 'feb27-first-minute-center-1306-1338-affirmed', '231-b006',
  '对读者问2月27日中午第一个1分中枢是否13:06—13:38，作者答“对”。',
  '走势中枢|操作级别', 2, '原证据是简短肯定，精确对象需同时读相邻两只老虎问题；不把肯定推广到读者其他全部图形判断。',
  ['相邻读者两只老虎询问中午第一个1分中枢13:06—13:38的特定指代'])
c(31, '580007-center-but-five-main-fall-limits-signal', '231-b009',
  '作者肯定580007在1分图10:55—11:18所问中枢，但指出5分为标准主跌段，至少等5分进入背驰段，单看1分走势意义有限。',
  '走势中枢|背驰段|区间套|操作级别|下跌', 1, '肯定有中枢不等可买；须连相邻读者问题定位区间，原一点要字形不改为别字。')
c(31, 'three-overlap-not-eternal-one-direction-self-similar', '231-b015',
  '作者以没有三段便无重叠、走势不能永远一个方向解释中枢三段，称结构与自相似有关但不需该概念。',
  '走势中枢|重叠|自相似性|走势终完美', 2, '属作者概念解释，不是本项目已补完存在性证明，不从自相似类比生成分形维数或必三根K的公式。')
c(31, 'a-c-consolidation-and-internal-c-divergence-nesting', '232-b000',
  '作者在一中枢走势转折问答中分两重：A与C比较的盘背，以及C内部次级背驰，一般呈类似区间套关系。',
  '盘整背驰|背驰|次级别|区间套|背驰段', 1, '一般/类似保留，未取消各比较段对应/级别/方向条件，不能把C内部任一短柱都称A/C盘背已确认。')
c(31, 'formed-thirty-center-watch-second-then-nest', '232-b003',
  '作者说若指数已形成30分中枢，可先看30分，从第二个中枢起密切关注是否进入背驰段，再用区间套定位精确背驰。',
  '走势中枢|背驰段|区间套|操作级别|确认', 1, '如果已形成和是否进入不能删，从第二个关注不等第二个必背驰，也不需在5分图上数所有小框。')
c(31, 'connections-below-one-and-c-must-rise-in-up-down-up', '232-b007',
  '作者说5分中枢间可为1分以下走势；对所谓反弹C段，至少须微微向上并延续时间，当天两段缓慢向下不符上下上要求。',
  '中枢连接|次级别|走势中枢|走势分解', 1, '这是反弹C段方向条件，不定义所有C都向上；不能把纯向下缓行当反弹第三上段，也不固定最少几秒。')
c(31, '099-five-main-fall-even-one-divergence-wait-parent', '232-b010',
  '对099全仓回补后跌停，作者说买入位置不对：若1分下跌已引发5分主跌，即使有1分背驰也不能据此用，应等5分进入背驰段后真背驰再回补。',
  '区间套|背驰段|背驰|仓位|操作级别', 1, '位置问题不大/当短差是作者安慰性案例评价，不否定前述买错，不认可读者不计代价先卖或日后必可获利。')
c(31, 'no-center-no-divergence-author-explanation', '232-b013',
  '作者对第三段若不下是否可不形成中枢的反问说：若不形成中枢，就不会出现任何背驰，这是其解释关键。',
  '走势中枢|背驰|走势终完美', 1, '在该中枢形成/背驰讨论内保存作者原强措辞，不把无中枢区间内任何短期指标缩小一概命名或否认背驰；需保留确认与区间口径。')

keep('219-b002 220-b000', 'upper-l026-c-stage-jan31-stable-long-funds-no-borrowing',
     '31透支与代管故事补资金长期稳定和自主负责，不由1996后涨推强平无风险或保证能撑过。')
keep('220-b002 220-b003 221-b000', 'upper-l026-c-stage-positive-cost-risk-and-negative-cost-ambition',
     '31细分零成本前后目标，负成本/零成本与当前报价分开；作者成本无风险修辞不成为实际无经济风险结论。')
keep('220-b002', 'upper-l009-c-stage-failure-exit-basic-principle upper-l026-c-stage-cautious-entry-and-midterm-cost-repair',
     '31不抛有理由消失/严重技术形态例外，降成本也需技术与机动资金，不取消旧失效退出防护。')
keep('224-b003', 'upper-l030-c-stage-entered-divergence-leg-can-break-and-reassess',
     '31明确标准趋势的逐级嵌套及突发小级破裂例外，与30当下重估范围对应；进入段非必成成功背驰。')
keep('224-b006 225-b001', 'upper-l018-center-first-three upper-l030-c-stage-one-extending-center-not-numbered-many',
     '31用具体分钟例说明前三段同级与后延伸，完结确认不将所有后续片段重新缩区间。')
keep('225-b006 232-b000', 'upper-l030-c-stage-000581-third-buy-wait-completed-sublevel-retest',
     '31三买未必先盘背但仍次级离开/回抽不回中枢；C内部低级背驰与A/C盘背两重比较不相同。')
keep('228-b009 229-b000 231-b009 232-b010', 'upper-l029-c-stage-large-breakout-one-divergence-may-only-intraday',
     '30分主升/5分主跌各例的小背驰作用需大级别段配合，不把所有1分交易都绝对无用。')
keep('229-b010 230-b005', 'upper-l028-c-stage-type-level-by-contained-centers-not-connections',
     '盘整是含相应级别一中枢的完成类型，非中枢对象本身；连接段更低不决定整体类型级别。')
keep('232-b007', 'upper-l028-c-stage-connections-sublevel-or-lower-not-exact',
     '中枢间可低于1分，需C段微弱但实际反向延续，不以视觉缓慢下斜替上下上第三上段。')

issue('cost-stages-cash-basis-versus-risk-guarantees', '220-b002 220-b003 221-b000 221-b001 228-b004',
      '零成本前股数目标不加、零后挣股分阶段；零指收回原现金不是无经济价值/无风险，最安全最大利润及一直增股未计费用/成交或给实证。',
      '不把约翻倍改成立刻机械半卖，保留大卖点、现金回补阶段与月线以上终局；攻击性修辞不变执行步骤。', True)
issue('one-entry-vs-skill-staging-and-thesis-exit', '220-b002 223-b008 223-b009 223-b010 229-b006 229-b007',
      '准备好一次性与弱技术先3千/形态保持次级买补不同语境，1/10是机动示例而非总计划加码；不抛有理由消失/严重形态例外。',
      '资金数量、机动分量与预定总投入分开，不推出跌越多买越多，关联9/13失效退出和26中线看好条件。', True)
issue('historical-leverage-stock-identity-and-self-report', '219-b002 220-b000 221-b002 222-b000 222-b001 222-b002 223-b004 223-b005 224-b000 227-b002 227-b003 227-b009 227-b010 228-b000 228-b004',
      '1996/1992未具名故事、深天地A图名、对手/资金/股价翻倍和2月交易归因均未独立核实；保证中线没问题/两个月翻两番不是本项目收益证据。',
      '保存作者身份、原数和日期，不猜未具名人物股票，历史板块观点不作当前推荐，文章敌对自述不转攻击方案。')
issue('capacity-float-and-volume-denominators', '229-b003 230-b000',
      '0.5%流通盘、30分以上/流通盘千分五、1分/10天均量1%是不同口径，资金与股数如何同量纲、10天均量粒度和费用冲击都未给齐。',
      '严格保留不同分母、一般/基本与历史经验身份；不补当前流动性保证或把持仓资金占比与日成交量1%混用。', True)
issue('weekly-third-leg-explicit-author-qualification', '228-b002 230-b008 231-b000 231-b002 231-b003 232-b013',
      '作者先说周线前两段及第三下跌，17:18明确承认不严谨，须先日线中枢再扩张，目前第一段内第三小段；读者嵌引原话仍读者记录。',
      '联合存原说与自我收窄，不能将5分/30分两段直接充周线次级；后32/33所预告细节待读，不称周线已完成。', True)
issue('center-minute-times-reader-typo-and-c-direction', '224-b005 224-b006 224-b008 225-b000 225-b001 231-b006 231-b009 232-b005 232-b006 232-b007',
      '1048—1129/第三1114—1129/1413是作者例，1329笔误说明在读者文本；对13:06—13:38和580007的简答需问题指代，反弹C须真的微上。',
      '不静改原时字符串，不认证读者所有分段；原图后配不能补所有最低1分以下数据或固定最短时间。', True)
issue('third-buy-consolidation-and-internal-c-nesting', '222-b008 225-b006 225-b007 228-b009 229-b010 230-b005 232-b000',
      '三买可无盘背，盘背只是往往转；盘整非中枢，A/C比较与C内部次级背驰两重类似区间套，完整结构和完成状态不可省。',
      '不将后每个新中枢第三下行自动称三买、不将任意两个同形柱当趋势背驰或把扩展永远留原级别。', True)
issue('parent-leg-main-rise-main-fall-and-event-exception', '224-b003 226-b002 226-b005 227-b000 228-b009 229-b000 229-b013 231-b009 232-b003 232-b010',
      '大级别进入再逐级向下为标准趋势，突发破裂有例外；30分主升/5分主跌的小背驰可盘中化解，第二中枢起关注不是必在第二背驰。',
      '不认可读者000761/工行/099所有信号，进入段与成功背驰分开；短线与中线持有目标分别保存。', True)
issue('figure-provenance-and-historical-forecasts', '221-b002 225-b013 226-b008 227-b004 228-b003 231-b003',
      '6图5文后1未核；1996旧光标、2/15与2/16浮窗及2/27日图右侧未来K不可混当日原发，作者未来3000/2869/牛市与板块预期不作后验胜率。',
      '源文本/身份/时间/字符映射与坐标不动，只改图来源备注；配图色框及后价格不替严格定理或原文自我限定。')

note('221-b002 221-b003 222-b000 222-b001 222-b002 222-b003 222-b004', 'dated-stock-self-report-and-separator',
     '2/15联通5元/指数3000承诺、股票新高/中线自评、公开目标使操作困难、14至25元故事及翌日预警完整已读。',
     '不认证账户、操盘成因或政治标签为事实，攻击修辞不输出操作步骤，星号只分隔。')
note('223-b004 223-b005 224-b000', 'dated-fundamental-crowding-and-stock-views',
     '938业绩/筹码、416货干净、山东人走慢等特定股票观点与换股短差建议已读。',
     '不认证内幕人物/资金与业绩因果，不将预计20元或技术换股当当前推荐；其一般买点/资金效率原则另抽。')
note('225-b011 225-b012 225-b013 225-b014', 'holiday-announcement-and-dated-market-context',
     '2/16放假24日开博公告、指数尾盘和14股新高自述及节日问候完整已读。',
     '非技术定义，续震荡预期不由后2/26图自动证实；标题日期与该段身份原已正确。')
note('227-b001 227-b002 227-b003 227-b005 227-b006 227-b007 227-b008 227-b009 227-b010 228-b000 228-b001 228-b002', 'dated-articles-stock-list-and-forecast-context',
     '2/26原列5+3+5+1共14股票与板块观点、2/27单边下跌/周线三段说法及操盘自述完整已读；周线原说另连后来更正。',
     '不把历史名单当当前选股池、翻倍/两月翻两番当回测，2/27自称事先计划未有独立证据，周线粗说不能脱离17:18限定。')
note('230-b006', 'theory-self-evaluation-and-learning-reminder', '作者纯数学自评及概念学习提醒已读。', '不是项目已经证明数学完整性或对读者智力的评价。')

relations = {
    'upper-l031-c-stage-two-phases-cost-zero-then-earn-shares': [('零成本持仓', '资金管理', 'related')],
    'upper-l031-c-stage-prepared-one-entry-no-upward-add-planned-allocation': [('仓位', '机动资金', 'qualifies')],
    'upper-l031-c-stage-down-hold-has-thesis-and-severe-shape-exceptions': [('持股', '确认', 'qualifies')],
    'upper-l031-c-stage-midterm-entry-at-least-daily-buy-not-falling-blind': [('持股', '操作级别', 'qualifies')],
    'upper-l031-c-stage-standard-trend-nesting-with-sudden-break-exception': [('区间套', '趋势', 'qualifies')],
    'upper-l031-c-stage-feb15-center-1048-1129-third-buy-1413': [('第三类买点', '中枢延伸', 'related')],
    'upper-l031-c-stage-third-buy-not-necessarily-after-consolidation-divergence': [('第三类买点', '盘整背驰', 'qualifies')],
    'upper-l031-c-stage-capacity-thirty-float-versus-minute-ten-day-volume': [('交易容量', '成交量', 'qualifies'), ('交易容量', '流通量', 'qualifies')],
    'upper-l031-c-stage-consolidation-type-contains-one-center-not-equal-center': [('盘整', '走势中枢', 'qualifies')],
    'upper-l031-c-stage-center-framework-earlier-kiss-only-reference': [('走势中枢', '均线系统', 'qualifies')],
    'upper-l031-c-stage-weekly-three-legs-original-explicitly-qualified': [('走势终完美', '操作级别', 'qualifies')],
    'upper-l031-c-stage-a-c-consolidation-and-internal-c-divergence-nesting': [('盘整背驰', '区间套', 'related')],
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
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], '读者买点/三卖猜想、前后周线段质疑与嵌引作者原话仍按问题身份；只对作者明确肯定的具体时段取证，读者笔误备注不等原作者更正。'
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
        'note': '降成本前/零成本后两阶段、机动资金/总预定量与弱技术3千例分开；交易容量不同分母；盘整非中枢，周线第三段原说有作者明确收窄，区间套与主跌段限制保留。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True, reviewer=REVIEWER, visual_review_note=f['note'],
             figure_source_review='6图全部查看，5文后1原发未核；深天地A图名不认证未具名透支故事，周线图含文后K且必须连读作者不严谨更正。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 183 and Counter(x['lesson_number'] for x in ledger) == {31: 183}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [31], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(219, 233)), 'figure_objects_viewed': 6, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '31课183段14页6图同模型四轮；资金降成本前后阶段/机动仓与总量/交易容量分母、盘整中枢与周线更正、三买及区间套条件保留，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


