"""Materialize the main agent's four-pass reading of lessons107-108.

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
DOC = 'volume_2-5332cd1b6038'
BASE = 'c_stage_l107_l108'
REVIEWER = 'Codex 主代理 / 阶段C下册107至108课同模型四轮复核'
SOURCE_SHA = 'd32387315bbdc81d1b9e45e14859e748322ed9ddb78414576385d367545b73c8'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_2.pdf').read_bytes()).hexdigest() == '5332cd1b60381c47ceb81358db6bbb47882efd074fc5c869dcc3002aaed1b5c0'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id IN ('lesson-107','lesson-108') ORDER BY pdf_page,block_index,id")}
assert len(passages) == 120
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 416 AND 427 ORDER BY pdf_page,id', (DOC,))]
assert len(figures) == 5 and all(f['origin_status'] == 'later_annotation' for f in figures)
rows, pending, notes = [], [], {}
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
        quote = re.sub(r'(?:\*+)?200[78]-\d{2}-\d{2}\d{2}:\d{2}:\d{2}$', '', p['text']).rstrip('*')
        citations.append({'passage_id': p['id'], 'quote': quote, 'quote_start': 0,
                          'figure_ids': [f'{DOC}-p{n:04d}-fig{k}' for n, k in figs] if i == 0 else []})
    cid = f'lower-l{lesson:03d}-c-stage-{slug}'
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
        row['figure_review_note'] = '主代理实际查看原页、整图和插图右端：' + '；'.join(f['note'] for f in figures if f['id'] in citations[0]['figure_ids']) + '。5图均为后加行情图，制作者未核，不作为作者观点唯一证明，文字独立支持命题。'
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
    pending.append({'id': 'lower-l107-l108-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})


c(107, 'rebound-forms-not-predicted-operation-plan', '416-b003',
  '以至少有30分钟级别反弹为前提，不同走势形式的难度与操作方式不同；作者要求操作计划不以事先预测反弹形式为基础。',
  '反弹|操作策略|完全分类|走势预测', 1, '至少30分钟反弹是题设，未据本段证明当时必有该级别；不把作者反预测原则改为不需结构分类。', ['已有理论依据的至少30分钟级别反弹题设'])
c(107, 'thirty-rebound-at-least-one-center', '416-b004',
  '对本例30分钟走势类型，作者以反弹至少包含一个30分钟中枢作为构造操作方案的基础。',
  '反弹|走势类型|走势中枢|级别', 1, '级别题设与尚未完成的实际反弹分开，不能由任意小反弹自动确认30分钟走势。', ['本例30分钟级别走势类型'])
c(107, 'center-three-subtypes-up-down-up-context', '416-b005',
  '作者重申中枢由三个以上次级别走势类型重叠构成，并在本例反弹操作中用上下上三个5分钟走势类型说明30分钟中枢。',
  '走势中枢|次级别|重叠|走势分解', 1, '上下上是本段反弹操作分解语境，不能据此全局改写64课标准上涨中枢下上下；不删除既有定义的连续与完成限制。', ['第107课反弹示例及其分解'], ambiguity='rebound_partition_vs_standard_uptrend_center_partition')
c(107, 'running-rebound-later-high-not-guaranteed', '416-b006',
  '上下上反弹的末上不保证高过首上；奔走型末上可能仅触首上低点，故首上最低点买入后等全程完成，可能只剩不够手续费且稍纵即逝的卖点。',
  '奔走型|反弹|交易成本|卖点|操作策略', 1, '保留可能和手续费风险，不把奔走型下跌反弹同23课回抽后上扬的不同语境强并；最低点入场也不保证收益。', ['所述上下上反弹分解'])
c(107, 'segment-from-first-rise-author-safety-wording', '416-b006 416-b007',
  '因同级别下的幅度无法绝对控制，作者主张从首上即分段操作，30分钟反弹按5分钟节奏处理，并把这称为分段带来的具体操作安全。',
  '反弹|次级别|走势分解|操作级别|操作策略', 1, '原文称同次级别分解；安全是作者对方案的论述，不是项目验证的无损保证，8/21又明确T+1可能卖不出首卖。', ['30分钟反弹、按5分钟节奏操作的本例'], ambiguity='author_absolute_safety_vs_execution_constraints')
c(107, 'third-buy-nondivergent-rise-can-hold', '416-b008',
  '首上与下出现后，若30分钟中枢后出现第三类买点并非背驰力度强拉，可转持有，等待后续第二乃至第三、四、五中枢完成、背驰及第三类卖点。',
  '第三类买点|背驰|持股|走势中枢|反弹', 1, '三买与非背驰向上是联合条件，不据预测先决定持有；后续各中枢并非当时已经形成，也非必须五个。', ['该30分钟中枢之后','第三类买点并形成非背驰力度向上'])
c(107, 'rotation-efficiency-part-position-higher-skill', '416-b009',
  '作者认为分段安全方案并非平均效率最高，提出保留部分仓位、其余换股轮动；小资金可全仓轮动，但技术要求更高。',
  '仓位|板块轮动|操作熟练程度|操作策略', 2, '未给统一半仓比例、收益比较数据或机械全仓建议；全部仓位轮动限小资金及更高技术。', ['按各自资金规模与更高技术能力'])
c(107, 'no-reversal-prediction-first-center-condition', '416-b010 417-b000',
  '作者要求不预判反弹或反转；只有第一中枢后出现第三类买点并形成非背驰向上，才具备其所述持股等后续中枢的条件，否则仍随时可能反回。',
  '第三类买点|反弹|持股|背驰|走势预测', 1, '跨页读完否则分支；不把一项三买或任意反弹等同反转已成。', ['第一中枢之后第三类买点与非背驰向上同时具备'])
c(107, 'uptrend-formation-wording-not-completed-type', '417-b001',
  '作者在本节把第一中枢后第三类买点并形成非背驰向上称为上升趋势形成的精确定义；持有还以前述趋势未有扭转信号为条件。',
  '上涨|趋势|第三类买点|背驰|持股|确认', 1, '这是形成过程的原话，与17课至少两个同向中枢的完成走势定义并列；本段未明说撤回旧定义，不把刚出现该联合信号改记已完成两中枢趋势。', ['第一中枢后三买并非背驰向上','未出现趋势扭转信号'], ambiguity='trend_formation_signal_vs_completed_two_center_definition')
c(107, 'practice-and-reverse-for-pullback', '417-b002',
  '作者说反弹类型的分析也有助盘整操作，实际效果必须靠磨练；回调操作可按反向理解。',
  '反弹|调整|盘整|操作熟练程度', 2, '后续课程将分析是计划，不视本汇编已交付所有反弹分类；反向不消除制度差异。')
c(107, 'aug20-2455-2656-level-branches', '417-b004 417-b005',
  '8月20日作者以日底分型上沿2455须站住、上方2656须攻破来观察三卖是否成立，并要求按实际走势机械反应，不以希望上涨代替。',
  '底分型|第三类卖点|确认|机械化操作', 1, '该历史上下点位不能泛化为所有分型/三卖定义；图2455.5/2656.6不倒改正文整数。', ['2008年8月20日该反弹情景'], figs=((417, 1),))
c(107, 'aug20-divergences-require-level-distinction', '417-b006',
  '作者要求先分清级别再谈背驰，所谓背了又背可对应不同级别，不能用1分钟背驰推断无限更大尺度转向。',
  '背驰|级别|确认', 1, '先分级是必要边界，未宣布任何重复背驰必属异级或小级别转大级别不可能。')
c(107, 'aug21-t1-first-sell-second-sell-after-low-open', '418-b003 418-b004',
  '8月21日作者说2455观察可能偏晚，首段虽有明确顶背驰，T+1可能使首类卖点无法卖出；大幅低开后首次次级别回拉不破顶或盘整背驰，可用第二类卖点应对突发风险。',
  'T+1|第二类卖点|第一类卖点|盘整背驰|次级别', 1, '不破顶或盘整背驰按原句替代条件保留，不自加且；95%是作者回顾530的跌幅规避自述非本项目统计，未保证本次也有95%。', ['本段大幅低开及T+1风险语境','首次次级别回拉'], ambiguity='second_sell_alternatives_and_unverified_95_percent_example')
c(107, 'aug21-ma13-class-two-and-ma5-short', '418-b005',
  '作者用13天线受阻称该反弹二级力度，能否升第3级以上仍看13天线；5日线有效跌破为其超短线风险观察。',
  '均线分类|均线|反弹|确认', 2, '本处2级力度沿均线分类，不改为严格2分钟走势级别；理论不足看均线是简化观察。', ['2008年8月21日该均线反弹'])
c(107, 'aug21-stroke-segment-not-unqualified-divergence', '418-b007',
  '作者批评未分清笔与线段就在线段上直接谈背驰，并要求先读书和实际磨练结构划分。',
  '笔|线段|背驰|操作熟练程度', 3, '批评按本段语境保留，不据此抹去早课单线段类背驰/类中枢的明确特殊入口。', ambiguity='ordinary_divergence_vs_segment_class_divergence_scope')
c(107, 'aug22-five-flat-opening-down-risk', '419-b001',
  '8月22日作者将周一开盘看作短线突破方向观察，若5日线走平后再向下张口，则按继续新低风险处理。',
  '均线|确认|完全分类', 2, '是所论历史均线条件判断，未给通用概率或所有市场因果定理。', ['2008年8月22日该5日线情景'])
c(107, 'aug22-news-gap-back-second-buy-capacity', '419-b002',
  '对周末消息作者说高位已退出者若押消息落空须迅速处理，能力不足不做；真有实质消息可等高开回落出现小次级别第二类买点再介入。',
  '第二类买点|次级别|操作熟练程度|操作策略', 1, '实质消息、高开回落和相应第二买点均保留；不是消息本身充分买入或必须赌周末。', ['该历史周末消息/高开回落情景','有对应操作能力'])
c(107, 'aug22-midterm-needs-week-month-fractals', '419-b003',
  '作者从当时中线角度要求观察周与月能否最终构底分型，否则即使消息推动也可能只是一日几日短线。',
  '底分型|周期K线图|确认|反弹', 1, '最终构造而非已有底分型，不把消息反弹提前登记中线行情。', ['2008年8月22日该中线结构'])
c(107, 'aug25-five-thirteen-two-branches', '419-b005',
  '8月25日5日在13日下收口，作者列出短线分水岭两支：5日上穿13日，或重新扩大而展开下一轮下跌。',
  '均线|完全分类|确认', 2, '当时等待一两日答案，不用文后图倒填已选方向。', ['2008年8月25日该5/13均线状态'])
c(107, 'aug25-week-before-month-not-yet-bottom', '419-b006',
  '作者当时将中线次序表达为先构周底分型、后月底分型，二者构出才期待大行情，否则仍可能上下折腾。',
  '底分型|周期K线图|确认', 1, '顺序和历史阶段保留，不能无条件把任一日底升级周月底。', ['2008年8月25日该中线标准'])
c(107, 'aug25-month-counts-empirical-not-clock', '419-b007',
  '作者说若当周破坏月最下根条件，月底构造至少顺延一月，并列本月10个月、下一周期12/13、再17/18；明确这属经验分析、以实际走势为准。',
  '底分型|周期K线图|确认', 3, '后调整至少三月、N倍及两年新高是该例经验预期，无通用证明；不把月数作固定时间定理。', ['2008年8月25日该调整第一轮时间'], ambiguity='empirical_month_counts_not_proven_cycle_law')
c(107, 'aug25-large-capital-stage-not-all-in', '419-b008',
  '作者说当时大资金对中字头按冲不上就退出、有差价回买来沉淀筹码，不会立即全仓，完全不介入又可能影响后续参与。',
  '主力资金|仓位|操作策略', 3, '是作者特定阶段资金叙述，6元中驴是其目标非事实确认或小资金一般要求；不借此保证操纵/收益叙述真实。', ['2008年8月25日作者所论大资金/中字头阶段'])
c(107, 'aug25-small-capital-short-or-wait', '419-b009',
  '对当时混乱环境，作者给小资金的选择是短线分段或干脆等待。',
  '操作策略|操作熟练程度|反弹', 2, '短跑与等待为可选，不把其唯一可行修辞变成所有人的强制交易。', ['2008年8月25日该市场环境'])
c(107, 'aug26-five-line-retest-and-center-expansion-possible', '420-b005 420-b006',
  '8月26日作者说回拉不站5日线时可继续以该线判超短线；同时保留下探不断扩成更大中枢、等上方均线下来缠绕后再选方向的可能。',
  '均线|走势中枢|中枢扩展|完全分类', 1, '可能而非本次已经扩展确认，不把均线缠绕本身等同严格中枢；真正的下跌是原句过程判断，不删除价格已下跌事实。', ['2008年8月26日该承接和均线状态'], figs=((420, 1),))
c(107, 'aug26-week-lowest-bar-still-conditional', '420-b007',
  '8月26日作者说上周作为周底分型最下根的形态尚未最终破坏，须当周继续保住；否则往下另找可安置周底分型的区域。',
  '底分型|周期K线图|确认', 1, '尚未破坏最下根候选不等周底分型完成。', ['2008年8月26日该周线候选形态'])
c(107, 'aug27-expanding-center-bottom-top-reverse', '421-b001',
  '作者说前日所提逐步扩展大中枢的演化在底部构造常见，反过来也可用于顶部构造研究。',
  '底|顶|中枢扩展|走势中枢', 2, '常见为作者经验，不给频率数据或由同形必同走势的逻辑。')
c(107, 'aug28-policy-technical-resonance-scope', '421-b003 421-b004',
  '作者针对当时中期底部要求政策与技术共振，并把先横住、各级中枢扩展叠合后等共振突破列为越来越可能的演化。',
  '底|中枢扩展|均线|基本面', 2, '限定当时环境的判断，单面不足和可能不可泛化为所有底部必须政策干预，未给共振量化指标。', ['2008年8月28日所论市场条件'], ambiguity='historical_policy_technical_resonance_not_universal_definition')
c(107, 'aug28-ability-short-cost-or-wait', '421-b006',
  '作者说该阶段有能力者可做个股短差，中线可通过短差降总成本；无把握者可等待底部形态彻底摆脱后再说。',
  '操作熟练程度|操作策略|成本|底', 2, '机会不等保证盈利，能力和等待选择保留。', ['2008年8月28日该底部构造阶段'])

c(108, 'bottom-precise-first-buy-to-first-third-point', '421-b008',
  '按精确走势类型，底部按级别区分：从第一类买点出现后，到其引发中枢首次走出第三类买卖点前，为底部构造过程；先三卖则构造失败，先三买则完成并展开新行情，顶部反向。',
  '底|顶|走势中枢|第一类买点|第三类买点|第三类卖点|级别', 1, '保留其引发中枢、第一次及失败分支，不把任意三买/后续中枢或任何第一买都说底部已成功；底分型粗略入口另条。')
c(108, 'fractal-bottom-coarser-entry', '421-b009',
  '作者把以分型定义底部称为较粗糙的办法，供暂不能精确分类走势者使用，也可把握一般大方向。',
  '底|底分型|走势类型', 1, '并列两种分析入口，不宣称分型区间与精确中枢区间必等价。')
c(108, 'fractal-bottom-low-fail-upper-success-at-least-stroke', '421-b010 422-b000',
  '分型角度的底部是底分型所构区间；跌破最低点则构造失败，有效站住区间上沿则作者称构造成功、至少向上一笔，顶部反向。',
  '底|顶|底分型|笔|确认', 1, '跨页续文和有效站住保留；这是分型意义而非必已满足严格走势类型级别，结合106仅观察成笔而非最佳买点限制。', ['分型意义的底部区间'], ambiguity='fractal_success_wording_vs_strict_stroke_and_type_confirmation')
c(108, 'buy-failed-down-probe-not-upper-boundary', '422-b001',
  '作者说不是在底部的区间上买，而仿中枢震荡，在区间下探失败时买；日线底分型对应的是分型意义的日线底部。',
  '底|底分型|中枢震荡|买点|周期K线图', 1, '失败下探不是任意下跌接刀；周日图分型底部不改为严格同名级别走势类型；与106边沿非最佳买点相互查证。', ['本节分型意义的底部操作'])
c(108, 'aug29-month-2284-no-break-september', '422-b002',
  '8月29日作者以已基本走出的8月K线给月区间2284—2952；若9月破2284，月底分型至少到10月后才有戏；回2284不破的分型意义周级别以下走势可按区间套寻找短线位置。',
  '底分型|周期K线图|区间套|买点|确认', 1, '原文有“9月是否能构造”与后文“10月有效确认”层次，保持原话，不自造9月全月确认月行情；原整数2284不改图2284.6。', ['2008年8月29日该月K线状态','回2284未破的相应分型意义走势'], figs=((422, 1),), ambiguity='month_fractal_candidate_vs_confirmation_month_scope')
c(108, 'month-no-market-before-october-effective-2952', '422-b003',
  '对该例，作者说10月有效确认站住2952前，最多视分型意义月级别底部构造，不能认月线行情，参与力度与投入应据此安排。',
  '底|底分型|确认|仓位|周期K线图', 1, '10月和2952是历史情景条件，不作为所有月份或今后行情阈值；不据文后图把2008年8月判断写为事实保证。', ['第108课该历史月线情景'])
c(108, 'week-2284-2601-containment-2523-exception', '422-b004',
  '当周与前周含包含关系，作者等待下周能否成周底分型；走出底部还须2284—2601有效突破，中秋前确认周行情原则上不可能，除非8月29日突破2523。',
  '底分型|包含关系|确认|周期K线图', 1, '候选分型、突破确认及最后一天例外分别保留；正文2601不以图2601.5改写，原句区间突破细则未量化。', ['2008年8月29日周K线状态'], exceptions=['8月29日当周最后一天突然突破2523'], figs=((423, 1),))
c(108, 'day-bottom-2284-2455-still-building', '422-b005',
  '作者把当时日线看作8月18日开始的底分型引发的底部构造，最终是否有效看2284—2455区间演化。',
  '底|底分型|确认|周期K线图', 1, '最终待定，不由日线候选直接推出周月底成功；保留该段原日期指称，2455不改成图2455.5。', ['2008年8月29日该日线底部构造'])
c(108, 'three-phases-end-oscillation-middle-hold', '423-b000',
  '作者按操作级别将节奏分底、顶和连接中间段：两端仿中枢震荡，底部先买后卖、顶部先卖后买；中间段持有，空头走势可持币等待到底部构造完成。',
  '底|顶|中枢震荡|持股|操作级别|操作策略', 1, '空头时小板凳指等待持币，不能误解为持股死扛；先买后卖与先卖后买的顺序不可交换。')
c(108, 'all-losses-errors-author-claim-not-audit', '423-b001',
  '作者在按级别分清三阶段的劝学语境中说有技术者不需等待、亏钱由错误操作引起，并要求反省。',
  '操作熟练程度|操作策略|操作级别', 4, '这是作者绝对化评价，没有交易样本或执行成本论证；不能宣称本项目验证所有损失必因操作者错误或理论不可能亏损。', ['作者该劝学语境'], ambiguity='author_absolute_profit_rhetoric_not_empirical_guarantee')
c(108, 'aug29-2403-monday-stroke-not-confirmed', '423-b003',
  '8月29日作者说周一若站住2403，很有机会延伸出日线向上笔，2523是下一个重要位置。',
  '笔|确认|周期K线图|完全分类', 2, '原文极大机会而非充分定义；未来周一未到，未记录当日笔已完成。', ['2008年8月29日该超短线条件'])
c(108, 'next-larger-rebound-not-justify-holding-loss', '423-b006 424-b000',
  '作者以10000跌6000反弹8000、再跌2000反弹4000的假设路径说明：等下一大级别不能代替当下分段操作，下一段的机会不抵消当前段处理。',
  '走势分解|操作策略|当下|反弹', 1, '数字是示意路径，非真实历史；后一次反弹幅度或比例不能拿来证明先前死扛有效。')
c(108, 'current-classification-not-story-prediction', '424-b001 424-b002',
  '作者要求面对当下走势而非编故事支持预判，并称操作必须以完全分类为基础、机械执行。',
  '当下|完全分类|机械化操作|走势预测', 1, '作者自称每天已给完全分类不构成项目独立证明其分类穷尽所有风险；与68课操作分段接口查证。')
c(108, 'sep1-new-low-delay-not-end-world', '424-b005',
  '9月1日作者认为月初破前月底会推后原月底分型但可能使其更有力；强行上拉若形成包含，反可能使真正分型更晚。',
  '底分型|包含关系|周期K线图|确认', 2, '可能和该月情景保留，不将越跌越好或每次新低必更强写成一般规律。', ['2008年9月1日该月线候选状态'])
c(108, 'sep1-october-beauty-not-timing-rule', '424-b006',
  '作者从美学称10月见底对应一年最美、周期可前后差一两月，随即说市场自行选择，实际操作可不理这些。',
  '底|周期K线图|走势预测|操作策略', 3, '美学经验不是硬性时间周期或9/10月必见底保证。', ['作者2008年9月1日从美学谈周期'], ambiguity='aesthetic_cycle_not_confirmed_timing_law')
c(108, 'sep1-month-macd-zero-pullback-open-dates', '424-b008 425-b000',
  '作者把较大走势待机点放在月线MACD回零轴后的中级回拉，列狠则17/18月即次年3/4月、不太狠则10月前后，并说取决多条件、无现在必须规定的行情。',
  'MACD|周期K线图|反弹|完全分类', 2, '回零轴后的回拉是历史预期，不是当时已确认MACD底背驰；政策因果为作者看法，日期非通用日历定律。', ['2008年9月1日作者讨论本轮大走势'], figs=((425, 1),), ambiguity='historical_month_cycle_forecast_not_necessary_market_path')
c(108, 'sep2-five-not-held-down-not-done', '425-b002 425-b003',
  '9月2日作者以5日线未站住判断该轮杀跌未完，并认为无量下阴跌后也可能很快回到当时位置，关键仍是月底分型结果。',
  '均线|成交量|底分型|确认', 2, '突发事件例外和可能回返不当底部已经确认；末尾9/3时间头不覆盖本段9/2。', ['2008年9月2日该超短线/无量情景'], exceptions=['半夜突发事件可能改变短线路径'])
c(108, 'sep3-new-low-month-earliest-october-2329', '425-b004 425-b005',
  '9月3日作者记破底使月底分型最快到10月，短线却有技术反弹基础、须看能力；2329若站不上仍弱，先急跌后反弹可能更有操作性。',
  '底分型|反弹|确认|操作熟练程度', 1, '已发生破底与可能反弹分开；正确9/3日期，图光标9/4和图注2203.3不替换正文2329。', ['2008年9月3日该破底后的技术反弹'], figs=((425, 1),))
c(108, 'sep5-acceleration-technical-rebound-not-reversal', '425-b006',
  '9月5日作者说前两天所论加速已现，预期下周有一定力度反弹，但只按纯技术反弹短线处理。',
  '反弹|操作策略|确认', 2, '其后宏观1929/30年调整和道指论述是历史作者预测，非证明该技术反弹变成反转。', ['2008年9月5日该加速后的展望'])
c(108, 'sep10-divergence-five-2220-branches', '426-b004 426-b005',
  '9月10日作者称两小中枢下跌后的早盘背驰已带反弹、5日线仍受阻；2220若站住才有更大反弹级别，否则回探，最恶劣支的最小升幅当时已完成。',
  '背驰|走势中枢|均线|反弹|确认|完全分类', 1, '最小升幅完成不等整个跌势结束；CPI为作者同日背景描述，9/10月月底分型仍是多条件下最好预期。', ['2008年9月10日该反弹结构'])
c(108, 'sep11-larger-center-next-buy-new-level', '426-b007 426-b008',
  '9月11日作者记5日线未过而走最恶劣支；反弹构成较大中枢后继续下跌，下一买点须站在新级别数中枢，接受理论允许的不同情况。',
  '走势中枢|级别|买点|完全分类|确认', 1, '新级别视角而非沿原更小级别机械数；未由未过5日线单项重写所有买点定义。', ['2008年9月11日该较大中枢后继续下跌'])
c(108, 'sep12-nonfirst-center-ninety-estimate', '426-b010',
  '9月12日作者说小反弹后继续下跌且并非第一中枢后下跌，预期下周更大力度与级别反弹，即使先再破2000也不排除，并自述90%多把握。',
  '反弹|走势中枢|级别|完全分类', 2, '实际页核定为作者解盘而非读者；90%多是作者估计无样本，不由中枢数量推出本项目统计概率或无后续下跌风险。', ['2008年9月12日该非第一中枢后的下跌'], ambiguity='author_probability_not_independently_verified')
c(108, 'sep18-october-still-possible-not-promise', '427-b001 427-b002 427-b003',
  '9月18日作者仍说10月可能见底，但需更猛烈暴跌，否则可能等17月周期；短线有能力者只抢一段，并关注外围变化。',
  '底|反弹|操作熟练程度|走势预测', 3, '21年神奇数字是作者未核经验联想，不作科学因果；可能和需暴跌条件不改成已确认10月底。', ['2008年9月18日作者的历史展望'], ambiguity='unverified_cycle_and_external_market_forecast')
c(108, 'sep22-second-weekly-stroke-expectation', '427-b005 427-b006',
  '9月22日作者说6124以来仅一次周笔反弹，最大期望本次制造第二次，并提醒周内大震荡、具体看图不要有成见。',
  '笔|反弹|周期K线图|确认', 2, '作者计数未独立重算，最大期望与已确认周笔分开。', ['2008年9月22日该周线展望'])
c(108, 'sep23-five-line-second-gap', '427-b008',
  '9月23日作者预告后面震荡，短线看5日线，破了有回补第二缺口风险。',
  '均线|缺口|确认', 2, '文末9/24头不改变此前9/23内容；安定自述与技术条件分开，不核药物效果。', ['2008年9月23日该5日线/缺口语境'])
c(108, 'sep25-daily-stroke-confirmed-weekly-open', '427-b010',
  '9月25日作者说未破5日线仍上攻但注意背驰，日笔已无问题，所盼周笔仍看是否有机会。',
  '笔|周期K线图|背驰|确认', 1, '正确日期为前段末9/25，末尾9/26仅支配后文；日笔确认不升级成周笔已成。', ['2008年9月25日该日/周笔与5日线状态'])

keep('416-b005', 'lower-l064-uptrend-center-standard-decomposition', '107反弹分解上下上与64标准上涨中枢下上下语境不同，结合律/分解多样性保留，未全局覆盖。')
keep('416-b006 418-b004', 'lower-l094-c-stage-t1-same-day-exit-impossible-risk lower-l106-c-stage-jul14-t1-limits-precise-small-level-operation', '107首段分解安全措辞须与8/21T+1可能首卖无法退出并列，不能无损保证。')
keep('417-b001', 'upper-l017-trend-definition upper-l018-trend-can-extend', '形成信号与完成走势至少两个同向中枢定义并列，未见撤回原定义。')
keep('418-b005', 'lower-l106-c-stage-average-level-no-necessary-correspondence lower-l106-c-stage-smallest-not-yet-conquered-average-nine-classes', '本处二级力度是均线分类，不自动等严格走势级别。')
keep('421-b010 422-b001', 'lower-l106-c-stage-aug14-boundary-hold-not-best-buy-point lower-l106-c-stage-aug14-multilevel-fractal-nesting-not-single-edge', '108上沿成功是分型意义确认，买入须区间下探失败，与106边沿不是最佳入场明确衔接。')
keep('424-b002', 'lower-l068-c-stage-operations-piecewise lower-l068-c-stage-prediction-as-current-piecewise', '107/108反预测操作与68分段分类措辞不同但有可查的条件共同点，不凭日期宣布撤回。')
keep('427-b010', 'lower-l104-c-stage-apr7-day-3613-week-fractal-likely-exception', '日笔与周笔分层的查证线索，本处9/25日笔确认不代4/7或更大层确认。')

issue('trend-formation-vs-completed-type', '416-b004 416-b005 416-b008 417-b001',
      '107首中枢后三买+非背驰称趋势形成，17课完成趋势至少两同向中枢；107上下上分解与64标准上涨中枢方向不同。',
      '将形成信号/完成类型和分解语境并列，进一步跨课核对；不按较晚时间覆盖旧定义。', True)
issue('absolute-safety-t1-and-efficiency', '416-b006 416-b007 416-b009 418-b004 419-b002 423-b001',
      '分段安全/平均效率最高、全部亏损归操作错误均作者论断；奔走型手续费风险及T+1首卖可能无法执行明示，没有收益样本。',
      '保留作者论断和制度/费用/能力边界，不宣称无损、实测最优或任何人全仓轮动可行。', True)
issue('fractal-bottom-vs-strict-type-and-entry', '421-b008 421-b009 421-b010 422-b001 422-b002 422-b004',
      '精确类型底部与分型粗略底部是两个入口；上沿确认、至少一笔的措辞与106观察成笔/非最佳买点须按范围理解；月9月候选和10月确认有层次。',
      '保留类型与图周期、候选与完成、上沿确认与下探失败入场的区别，不补有效突破阈值或统一等价公式。', True)
issue('historical-month-cycle-not-timing-law', '419-b007 424-b006 424-b008 427-b001 427-b002',
      '10/12/13/17/18月、N倍/三月/两年、一年美学和21年神奇数字均经验预测，无通用证明；9/1与9/18仍有政策/外围条件。',
      '逐项保留历史日期、可能性和作者身份，不转成确定月份或现代科学周期。')
issue('probabilities-levels-and-price-thresholds', '418-b004 418-b005 422-b002 422-b004 426-b010',
      '530规避95%跌幅与9/12至少90%多把握均作者自述非本项目统计；2级均线力度不等严格级别，整数价格与图小数不同。',
      '不合并收益/概率指标，不改正文整数；攻克/有效站住与底分型确认阈值未给完整算法。', True)
issue('date-heads-role-and-quoted-title', '425-b003 425-b005 426-b009 426-b010 427-b000 427-b008 427-b009 427-b010',
      '原页裸日期只管后文；426结束语曾误判读者；427引用9/4文章标题仍属9/18，图嵌8/29时间并非正文独立时间。',
      '已在source-plan校正13源段，原文本/映射保留，后续证据使用更正身份；混合段只引原文句子不引下一日期。')
issue('figure-makers-and-future-bars', '417-b004 420-b006 422-b002 422-b004 424-b008 425-b004',
      '5图均含文章之后的主图行情或插图，部分至2009年；制作者未核，8/29图嵌09:15:01未证明是作者课程时间。',
      '图保留后加身份和定位，所有文字命题独立取证，不以未来行情/图注改原文或倒填分支。')

note('416-b002', 'author-introduction', '课程承接前日走势与学习把握的引言已读。', '作者归因于理论掌握程度是劝学，不独立证明所有执行问题只因理论未掌握。')
note('417-b007 418-b000 418-b001 418-b006 418-b008 418-b009', 'historical-macro-and-personal-context',
     '刺激传闻/管理层批评、教科书自评、笔线段教学负担、四期病情及未来变种/五人预测全文跨页已读。',
     '政策因果、病情和匿名修辞未外核；不把夸张语句当行动指令、独立统计或医疗事实。')
note('419-b010 420-b000 420-b001 420-b002 420-b003', 'cultural-opinion-context',
     '北京/伦敦奥运、八分钟、宏大叙事与全球文化重建意见完整已读。', '属于作者文化评论，不抽为市场一般规则或技术能量指标。')
note('421-b005', 'historical-news-scenario-context', '周末消息分量与无消息再探及平衡形态的历史预期已读。', '没有精确结构新定义，不把消息大小作为自动买卖触发；相邻技术分类已抽。')
note('423-b004 423-b005', 'historical-capital-and-gain-context',
     '中信证券近30%、中字头资金进退及来回获利一年消费的作者自述已读。', '未核样本或账户，不将收益/资金动机自述当项目收益验证；能力与阶段边界保留。')
note('424-b004 424-b007', 'personal-and-news-context',
     '周末消息失望与杂志合作邀请、无固定合作/稿费的个人叙述已读。', '不是建立作者外部身份/机构影响力的独立证据，不执行其征集写作要求。')
note('425-b007 426-b000 426-b001 426-b003 426-b012 426-b013 427-b000 427-b009 427-b011 427-b012 427-b013',
     'historical-macro-and-personal-context', '1929/30年调整、道指10000、身体近况、国际政策棋局及9/4文章引用跨页完整已读。',
     '历史宏观/因果/收益自述未外核；9/4是被引文章非9/18本段新头；9/24与9/26按原页前头日期，政治评价不作技术证明。')
note('426-b009', 'corrected-author-ending', '9/11按图作业结束语及其后9/12裸时间已核，旧读者署名是解析误判。', '结束语属于作者9/11，9/12只管下一段；不把结束语当新命题。')

relation_map = {
    'lower-l107-c-stage-running-rebound-later-high-not-guaranteed': [('奔走型', '反弹', 'qualifies')],
    'lower-l107-c-stage-third-buy-nondivergent-rise-can-hold': [('持股', '第三类买点', 'requires')],
    'lower-l107-c-stage-aug21-t1-first-sell-second-sell-after-low-open': [('T+1', '第一类卖点', 'qualifies')],
    'lower-l107-c-stage-aug27-expanding-center-bottom-top-reverse': [('中枢扩展', '底', 'related')],
    'lower-l108-c-stage-bottom-precise-first-buy-to-first-third-point': [('底', '第一类买点', 'related'), ('底', '第三类买点', 'qualifies')],
    'lower-l108-c-stage-fractal-bottom-coarser-entry': [('底', '底分型', 'related')],
    'lower-l108-c-stage-buy-failed-down-probe-not-upper-boundary': [('底', '中枢震荡', 'related')],
}
for r in rows:
    r['relations'] = [{'source': a, 'target': b, 'type': t} for a, b, t in relation_map.get(r['id'], [])]

by_passage = defaultdict(list)
for r in rows:
    for e in r['evidence']:
        by_passage[e['passage_id']].append(r)
for item in pending:
    item['lesson_numbers'] = sorted({int(passages[x]['unit_id'].split('-')[1]) for x in item['passage_ids']})
    if item['id'].endswith('figure-makers-and-future-bars'):
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
    elif p['text'].startswith('教你炒股票') or re.fullmatch(r'.+\(200[78]-\d{2}-\d{2}(?:\d{2}:\d{2}:\d{2})?\)', p['text']) or p['text'].startswith('缠中说禅解盘:') or p['text'].startswith('话就不多说了') or p['text'].startswith('看图作业，多想无益') or p['text'].startswith('好了，最关键点') or set(p['text']) == {'*'}:
        result, reading, atomic, inverse = 'source_header_or_ending', '课程/解盘标题、作者时间头、分隔或结束语已读并核对。', [], '仅作来源定位，不能独立支持技术结论。'
    else:
        raise AssertionError(('unaccounted paragraph', id, p['text']))
    if linked and decision:
        reading += '；其余语境：' + decision['reading']
        inverse += '；' + decision['inverse']
    ledger.append({'passage_id': id, 'lesson_number': int(p['unit_id'].split('-')[1]), 'document_id': DOC,
                   'pdf_page': p['pdf_page'], 'role': p['role'], 'speaker': p['speaker'], 'published_at': p['published_at'],
                   'source_text_sha256': hashlib.sha256(p['text'].encode()).hexdigest(), 'result': result,
                   'claim_ids': [r['id'] for r in linked], 'related_existing_claim_ids': retained[id],
                   'existing_evidence_not_mutated': True, 'pending_issue_ids': [x['id'] for x in pending if id in x['passage_ids']],
                   'reviewer': REVIEWER, 'rounds': {'1_read_and_scope': reading, '2_atomic_conditions': atomic,
                   '3_normalization': {'concept_labels': sorted({x for r in linked for x in r['concepts']}),
                    'related_existing_claim_ids': retained[id], 'note': '形成/完成、反弹分解/标准中枢、T+1/安全、精确类型/分型底部、候选/确认及月周日分开。'},
                   '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True, reviewer=REVIEWER, visual_review_note=f['note'],
             figure_source_review='5图均后加；原页及整图插图右端已看，制作者未核，文字独立支持，不倒填未来行情。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 120 and Counter(x['lesson_number'] for x in ledger) == {107: 55, 108: 65}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
           'lessons': [107, 108], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger),
           'claims': len(rows), 'evidence': sum(len(r['evidence']) for r in rows),
           'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
           'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)),
           'whole_lesson_semantic_read_complete': True, 'technical_extraction_complete': False,
           'four_round_review': True, 'independent_review_claimed': False, 'visual_pdf_pages': list(range(416, 428)),
           'figure_objects_viewed': 5, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
           'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA,
           'retained_source_links_in_ledger_only': True, 'database_mode': 'ro', 'formal_import': False,
           'acceptance': '107至108课120段/12页/5图同模型四轮，形成与完成、奔走型/费用/T+1、底部两入口和月周日条件保留，增量待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close()
sys.stdout.reconfigure(encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False))
