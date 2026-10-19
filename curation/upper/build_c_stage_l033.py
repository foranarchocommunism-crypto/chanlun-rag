"""Materialize the main agent's four-pass reading of lesson33.

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
BASE = 'c_stage_l033'
REVIEWER = 'Codex 主代理 / 阶段C上册33课同模型四轮复核'
SOURCE_SHA = '56cac728882dc7c32a85ce605cd2db441ea497a130c8c77762785c287dd9760c'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-033' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 109
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 243 AND 254 ORDER BY pdf_page,id', (DOC,))]
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
    pending.append({'id': 'upper-l033-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})







c(33, 'ambiguity-related-to-centers-not-fixed-template', '243-b010',
  '作者说市场并非永远是A/B中枢同级的标准a+A+b+B+c，走势多义性都与中枢有关。',
  '走势多义性|走势中枢|走势分解|当下', 1, '永远固定模板被否定不等定义可随意，后文把可消除的数量/模本问题与有意义的合理多释义分开。')
c(33, 'extension-six-added-plus-three-initial-nine', '243-b011',
  '第33课为消除延伸计数多义性，规定新增延伸一般不超过五段；一旦新增六段，加上形成中枢本身三段，共九段便构成更大级别中枢。',
  '中枢延伸|中枢扩展|走势多义性|次级别|走势中枢', 1, '新增六与总九不是两个不同阈值，原形成三段/延伸段须分清；所计为对应次级走势，不是九根K或任意九个时间格，连续/重叠与有波动前提仍在。',
  ['中枢本身三段已形成', '新增相应次级走势延伸六段的口径'])
c(33, 'nine-one-minute-can-be-thirty-center-view', '243-b011',
  '作者以5分中枢围绕延伸为例：九段1分次级走势每三段构成5分中枢，从三段5分重合角度可解释为30分中枢。',
  '中枢延伸|走势中枢|次级别|级别|走势多义性', 1, '按本例实际完成且重合的递归口径，不从九段任意形状直接计算级别，不把原已有中枢三段遗漏。')
c(33, 'strict-level-from-trades-not-fixed-time-periods', '243-b012 244-b000',
  '作者把不同周期图称为真实走势不同精度的模本；最严格级别可从每笔成交的最低图形按中枢延伸、扩展递归确认，不依赖固定5分、30分等名称。',
  '周期K线图|走势多义性|级别|递归定义|成交分笔', 1, '每笔成交非后期几何笔，精确结构递归与周期图时间标签分开，不默认本段已给全部后期分型线段规则。')
c(33, 'chart-seven-or-fifteen-sixty-arrangements-possible', '244-b000',
  '作者允许7分或按等比数列设图周期，也允许以15分与60分替代30分，称这些都是便于观察的简略安排，通常没必要追求过度精细。',
  '周期K线图|级别|操作级别', 2, '这些是图周期序列选择，不是所有严格中枢级别能任意改名或固定倍数换算。')
c(33, 'zoom-small-chart-train-current-whole-view', '244-b001',
  '作者建议把分笔或1分图逐步缩小以看见更多走势，体会细部到整体和层层级别变化，并把训练后的直观比作读诗。',
  '周期K线图|当下|操作熟练程度|走势多义性', 3, '主张是观察训练和文学比喻，缩放本身不改变结构级别、也不证明可绕开定义取得唯一交易路径。')
c(33, 'valid-multiple-interpretations-not-all-to-eliminate', '244-b002',
  '作者另分有实质意义的多义性：走势可以有多种符合理论内在逻辑的合理释义，用于多角度分析。',
  '走势多义性|分解多样性|走势分解|当下', 1, '区别于用数量限制消除延伸歧义和图模本细节损失，不能把任何互不相容的随意画法都称合理多义。')
c(33, 'a-c-can-be-center-swings-b-gap-extreme', '244-b003',
  '作者允许把a视作围绕后出现A的波动、c视作围绕B的波动，简化为两中枢及连接；极端时a/c可无、b可为跳空缺口，只剩两个中枢。',
  '走势分解|围绕中枢的运动|中枢连接|缺口|走势多义性', 1, '是对已经有结构的另一释义，不代表A形成前已知未来；缺口可作连接不等缺口本身构成中枢。')
c(33, 'existing-centers-and-current-trades-two-forces', '244-b003',
  '作者把已有中枢比作星球，位于当前价格上方者给向上作用、下方者给向下作用；又把当下买卖形成的力与已有走势的作用分开，提出研究两种合力关系。',
  '中枢系统|市场合力|市场分力|中枢回拉作用|当下', 2, '按原文上下方向保存，不以物理直觉反转；星球和力是分析释义，未给引力常数、可加数值或完整动力学方程。',
  ['第33课以中枢系统与当下交易作两重力的分析视角'], ambiguity='conceptual_force_analogy_without_quantitative_equations')
c(33, 'last-center-pullback-interpretation-of-divergence', '244-b004 245-b000',
  '作者从最后中枢B解释背驰：对假设向上的b+B+c，c向上离开弱于b所表示的向下离开，而中枢同样回拉两边，故向上离开也能回到中枢；反向为底背驰。',
  '中枢回拉作用|背驰|走势中枢|围绕中枢的运动', 1, 'b作为向下离开是相对B的另一释义，不静改实际时间箭头；回拉论证为作者定性解释，不补力度计算式或无条件保证所有反弹都回ZG。')
c(33, 'consolidation-and-trend-divergence-center-view', '245-b000',
  '作者说从中枢回拉角度，盘背与趋势背驰本质类似，区别在力度、级别和发生的中枢位置。',
  '盘整背驰|背驰|中枢回拉作用|操作级别', 1, '同视角相似不取消趋势至少两个同级中枢等定义差别，不把两个词全局并为同义。')
c(33, 'larger-b-can-reverse-and-same-side-excursions', '245-b001',
  '当B大于A时，作者说a+A+b+B之后可反向运行；中枢外离开不必始终上下交替，先一次向上、再一次向上也允许。',
  '中枢扩展|中枢回拉作用|围绕中枢的运动|当下', 1, '说的是围绕中枢的离开过程，不撤销构中枢三段的交替方向；B更大不保证其后必原方向或必反转。')
c(33, 'opposite-departure-strength-and-third-buy-retest', '245-b001',
  '作者把后续反转叫c，比较它与a+A+b在B两边的离开力度；c若较弱会回中枢，最强情况也至少回拉一次检查能否成三买。',
  '中枢回拉作用|第三类买点|背驰|走势分解', 1, '前段与c方向相反，区别通常同向b/c背驰；后例又比较c与b，两个文字口径不擅合为同一个已定量指标。',
  ['B大于A而尝试从B反向离开的例子'], ambiguity='opposite_departure_force_comparison_and_case_reference_scope')
c(33, 'macd-same-side-divergence-versus-opposite-cross-zero', '245-b001',
  '作者区分MACD辅助比较：普通背驰的黄白线和柱面积在0轴同一侧；反向a+A+b与c各在不同侧，此时不要求原样回拉，但黄白线至少穿越一次0轴。',
  'MACD|背驰|中枢回拉作用|指标对比', 1, '同向背驰回轴与反向力度比较穿轴不能混成矛盾或取消所有回轴条件，穿一次也非单独充分反转信号。',
  ['比较对象是方向相反的a+A+b与c时适用穿轴说明'])
c(33, 'one-minute-process-shown-on-fifteen-not-level', '245-b002 246-b000',
  '作者说该例a+A+b本属1分走势，因1分资料难保留才用15分图展示；02270945—02280945按其走势计时称4小时，A在1分图02271306—02271337，区间2877—2894、围绕高点2915。',
  '周期K线图|走势中枢|GG|ZG|操作级别', 1, '4小时是作者走势计时而非自然日历相差4小时；15分图不把对象升级15分，原13:37与31简答13:38均保留待核边界，紧写时间不自行补秒；GG2915非中枢上沿2894。',
  ['第33课2007年2月27日至28日指数例'], figs=[(245, 1)], ambiguity='case_minute_endpoint_1337_vs_prior_1338_not_silently_unified')
c(33, 'c-return-b-origin-2915-or-small-top-before', '246-b000',
  '作者把c约从02281100起算，要反转成功至少不弱于b，直观检验是重新到b起跌点2915；若c内部小级顶背驰出现仍未达到，便不再预期达到该点。',
  '中枢回拉作用|背驰|区间套|GG|确认', 1, '定性力度和直观价格检验依本例相同级别，不由该段推跨任何股票固定压力；5日线只是怕看不懂的辅助。',
  ['第33课该c与b的同级比较'], figs=[(245, 1)])
c(33, 'weak-c-reentry-b-2888-2859-sell-case', '246-b000',
  '作者说c弱便回B，例中2888首次卖点若未处理，03011100约2859再次较弱离开也应退出，随后回跌底背驰再看回补。',
  '第一类卖点|背驰|中枢回拉作用|操作策略', 2, '后又跌约100点和完美回补为作者事后例述，未独立核行情/成交；不是任何破位下跌都保证可精确回补。',
  ['第33课指数具体卖点叙述'], figs=[(245, 1)], ambiguity='historical_index_trade_example_not_performance_verification')
c(33, 'center-bottom-entry-compare-next-top-third-buy', '246-b001',
  '作者给围绕中枢操作：下方离开见底背驰介入，再看回拉顶背驰能否超过前次向上顶背驰高点；不能则退出，能也可退出，次级回抽不入中枢成三买后再回补。',
  '中枢回拉作用|背驰|第三类买点|次级别|操作策略', 1, '向上顶点比较、次级回抽及不入条件联合保留，不将任何底背驰都视为本级三买或实际必能成交。')
c(33, 'bottom-rebound-stays-below-center-third-sell', '246-b001',
  '若底背驰后的次级回拉不能回到中枢，作者判为三卖，要求退出并等下方形成新中枢再重复观察。',
  '第三类卖点|次级别|背驰|走势中枢|中枢回拉作用|操作策略', 1, '底背驰低级定位与原中枢三卖层次不同，不因有底背驰就忽略未回中枢的弱势。')
c(33, 'stock-specific-index-and-futures-different', '246-b002',
  '作者强调上述针对指数，个股须具体分析、指数非单边跌时许多个股可独立活跃；期货可随时开仓，与股票凭证数量基本稳定不同，力度分析细节另论。',
  '操作级别|期货|市场风险|缠中说禅趋势力度', 2, '这是作者当时对市场结构的分析范围，不提供现行开仓规则或称所有个股完全脱离指数，期货最大的利益是观点而非实证。')
c(33, 'dated-low-price-third-buy-selection-not-crowd', '246-b005 247-b000',
  '3月2日作者要求自己学方法选股、不要扎堆，低价科技/旅游等只作观察板块，技术上须找三买或刚从三买起来的股票。',
  '第三类买点|题材股|买卖点|操作策略', 2, '行业名单是历史语境，不作现在推荐；低价板块也不能代替实际买点。')
c(33, 'mar5-1017-subminute-top-range-operation', '247-b002',
  '3月5日11:56解盘将当天1017定位为1分以下背驰，盘整上离顶背驰退出、下离底背驰回补；若成三卖则先等跌透。',
  '背驰|第三类卖点|盘整|操作级别|操作策略', 2, '午前而非3/2评论，具体时点未独立重算，跌透须后文有级别背驰而非任意跌够百分比。', figs=[(247, 1)], ambiguity='dated_subminute_signal_case_not_independently_recomputed')
c(33, 'weak-skill-reduce-position-no-chasing-or-panic', '247-b004',
  '作者在该震荡行情要求技术不足者减少操作和仓位，掌握者才卖点退出后等买点再入，反对追高和恐慌杀跌。',
  '操作熟练程度|仓位|买卖点|追高|市场心理', 1, '没有股票值得追为作者操作态度，不取消技术严重形态或失效退出；不把所有跌时卖出都称错误杀跌。')
c(33, 'mar5-evening-pressure-line-2888-2858', '247-b006',
  '3月5日夜评说当天一顶一底背驰，底部创新低；2月28日2888与当日2858连线为后续压力，顶背驰若不越线则仍弱直至突破。',
  '高点连线|背驰|走势预测|确认', 3, '夜评21:14与午评11:56分开，原2858与图2858.37精度不统一；未来越线条件不是已确认持续转强。', figs=[(247, 1)], ambiguity='dated_pressure_line_and_future_branch')
c(33, 'consolidation-small-divergence-large-swing-author-returns', '248-b000',
  '作者说盘整中尤其离开中枢的小背驰不可忽略，举当天130点振幅、个股超过10%及若把握三次可降本30%为例。',
  '盘整|中枢回拉作用|背驰|成本', 3, '130/10%/30%为作者历史观察及条件收益设想，未给全样本、费税或成交，不当可复制收益保证。', ambiguity='author_historical_swing_and_cost_reduction_claims_unverified')
c(33, 'unskilled-can-leave-wait-weekly-bottom-divergence', '248-b001',
  '作者允许技术不足者盘整时离开、待走强，极简选择为等周线底背驰才再研究；熟练者则可利用盘整短差与板块活动。',
  '操作熟练程度|盘整|背驰|操作级别|操作策略', 2, '周线中枢几个月/N年看一次与盘整利润更大是作者经验修辞，不变成固定时间周期或收益排行。')
c(33, 'third-sell-break-wait-sized-divergence-not-blind-buy', '248-b002',
  '盘整若出现三卖并破位急跌，作者要求先等跌透、有一定级别背驰再进入，不熟练者减仓。',
  '第三类卖点|背驰|仓位|盘整|操作熟练程度', 1, '一定级别没有具体数值，不能补固定跌幅或仅一根小柱；避免跌势与利用震荡需完整条件。')
c(33, 'mar6-three-waves-broken-line-and-next-day-conditions', '248-b003',
  '3月6日作者说底至顶背驰的中枢震荡至少上下上三波，早盘是其中下段；已越2888—2858连线，次日若不回早盘区间则强，15分120均线、2888、2915为依次参照。',
  '中枢震荡|次级别|高点连线|均线|走势预测', 2, '依该日上行回拉说明而非所有方向都上下上；5/15图修复须1分不破坏、级别升则看更大背驰，明天条件仍未来。', figs=[(248, 1), (249, 1)], ambiguity='dated_chart_repair_and_next_day_strength_branch')
c(33, 'rotation-buy-not-started-with-buy-point', '249-b000',
  '作者在3月6日说板块轮动快，不追高，应找尚未启动而已有买点者，散户按当下走势而非市场背后叙事。',
  '板块轮动|追高|买卖点|当下', 2, '作者对金融股上涨因果/发行任务的解释未独立核；未动且有买点两个条件不等所有低价滞涨都可买。')
c(33, 'end-by-divergence-not-necessarily-direct-sublevel', '249-b004',
  '作者简说任何走势结束必因背驰，某级背驰至少结束该级别走势，但不一定仅由紧邻次级背驰造成，否则a`+B没有意义。',
  '背驰|完成|操作级别|走势分解', 1, '至少的最低作用与更大影响分开，结束不等立即反向趋势；原简说是作者强陈述，不补所有事件下充分预测算法。')
c(33, 'bull-third-buy-daily-then-thirty-watch-pool', '249-b007 250-b000 250-b001',
  '作者认为牛市三买爆发力强，可先找日线、实在没有再找30分；把潜力板块中低价、周线未拉升者列几十至百只自选，每天选买点，剔走坏者更新，前提掌握理论并实践。',
  '第三类买点|操作级别|资金管理|板块轮动|操作熟练程度', 2, '几十百只为观察池不是同时持仓数；爆发力最强/必有成果/即卖即买是作者未测效果主张，不变当前选股推荐。',
  ['牛市背景及足够理论和实践能力'], ambiguity='historical_stock_pool_and_efficiency_claim_not_empirical')
c(33, 'third-buy-center-edge-versus-swing-high-strongest', '250-b004',
  '作者对三买边界答复说次级不跌回中枢里面即可，若连围绕波动最高点也不跌回则更强。',
  '第三类买点|次级别|GG|ZG|走势中枢', 1, '原答后最高点需连读者中枢上沿/波动高点对比，强度偏好不替代三买定义；不擅补触边相等的精确开闭区间算法。')
c(33, 'rotate-sectors-or-work-one-sector-alternatives', '250-b007',
  '作者说板块不会永远单一，可选多个板块有卖点先卖再轮换，也可留在一个板块反复短差。',
  '板块轮动|买卖点|操作策略|资金管理', 2, '两种操作备选而非必须频换板块，原轮着吵字形保留，效率高为作者未实测评价。')
c(33, 'new-center-at-least-same-nonoverlap-old-enters-system', '250-b010',
  '作者回应B作用何时改变，说新中枢至少同级且不重叠、更大也可；旧中枢并非无作用，而纳入更大中枢系统继续起作用，短线可先把一个中枢做好。',
  '中枢系统|走势中枢|中枢回拉作用|级别|重叠', 1, '需问题指代的新中枢条件，不能简化成后面任意同级中枢出现旧B就消失；更大中枢层级关系作者另留后文。')
c(33, 'consolidation-plus-consolidation-can-increase-level', '250-b014',
  '作者说盘整加盘整仍可为盘整，但相加更多可能变成更大级别盘整，所以还须看级别。',
  '盘整|级别|走势分解|中枢延伸', 1, '不从类型名称相同推整个级别不变，也不将任何两个不相接盘整直接拼成同一中枢。')
c(33, 'mar5-weekly-only-if-no-up-break-daily-alternative', '251-b001',
  '3月5日作者把当时视为牛市第一波调整，可能成周线中枢的前提是盘整后不向上突破；仍可能只是第一段日线延伸后继续新高。',
  '走势预测|走势中枢|中枢延伸|操作级别|牛市阶段', 2, '是两支有条件预期，不把31/32较粗的周线说法视为永久已确认；牛市性质和将创新高为作者当时判断。', ambiguity='dated_weekly_or_daily_alternative_not_fixed_confirmed_path')
c(33, 'weekly-then-1500-up-is-conditional-forecast', '251-b002 251-b003',
  '作者预测若真新增六段形成周线盘整，结束后可预期至少上次上行级别的向上波动，举1500点以上，并以牛市历时作信心说明。',
  '走势预测|操作级别|中枢延伸|牛市阶段', 3, '若形成且结束两个条件与作者预期身份保留，13年/不到2年和1500点未独立核实，不能变成全部周中枢必涨1500点定律。',
  ['若当时真正延伸六段形成周线盘整', '该周线盘整已经结束后'], figs=[(253, 1)], ambiguity='conditional_historical_1500_point_forecast_not_verified')
c(33, 'dealer-amplitude-not-center-system-author-claim', '251-b006',
  '作者认为庄家可放大波动幅度，却不能改变中枢整体结构系统。',
  '控盘|幅度|中枢系统|走势中枢', 3, '这是作者理论范围的强主张，不是对000426/600777交易控制的独立调查或所有操纵市场事件实证。', ambiguity='author_structure_invariance_claim_not_empirically_validated')
c(33, 'expansion-word-one-center-not-two-same-centers', '251-b009',
  '针对读者“两个同级中枢扩张”的问法，作者明确说这里中枢扩张针对一个中枢从原级别变为另一等级，不以两个为对象。',
  '中枢扩张|走势中枢|级别', 1, '保存扩张原词，与20课中枢扩展的两同级比较条件另存，不自动当同词或宣告全部历史定义被废除。')
c(33, 'volume-auxiliary-structure-first', '251-b012',
  '作者说成交量有意义但更多作辅助，图形结构优先，课程尚只讲了部分内容。',
  '成交量|几何结构|技术分析', 1, '不把少提量解成量绝无用，也不把成交量当MACD柱，具体量化方案此处未给。')
c(33, 'combine-practically-tested-methods', '251-b015',
  '作者允许把经实践检验有一定效果的方法结合其框架，并以数学公理作类比。',
  '技术分析|操作熟练程度|指标对比', 2, '经过实践检验与一定效果为条件，不是任意理论都已正确，公理类比未构成项目完成形式证明。')
c(33, 'center-alternation-reference-not-absolute', '252-b001',
  '对平台调整中枢交替原则，作者说不是绝对、成功率特别高，认为与心理有关，只作重要参考。',
  '走势中枢|平台式调整|概率原则|市场心理', 2, '依相邻读者所问原则，原答未重新列完整交替规则，也没有成功率样本，不能补绝对定理或数值胜率。', ambiguity='qualitative_alternation_probability_without_test_sample')
c(33, 'sudden-index-fall-destroys-forming-third-buy', '252-b004',
  '作者说指数急跌若破坏个股内在结构，三买就不会呈现，须按当下已形成结构判断。',
  '当下|第三类买点|确认|市场风险', 1, '形成中的三买不等已成立后被任意撤销，也不能因后来反涨倒认当时买点已成立。')
c(33, 'larger-divergence-usually-more-but-small-can-accumulate', '252-b007',
  '作者一般赞同更大背驰/级别有更大力度，但对a`+B演化提醒最小级别也不可轻视，部分走势能量逐步积累。',
  '背驰|级别|小级别转大级别|中枢回拉作用', 1, '一般与a`+B例外都保留，不设级别倍数等于幅度倍数，也不说每个最小背驰必造成大级反转。')
c(33, 'macd-just-crossed-zero-not-own-level-divergence', '253-b000',
  '3月6日作者说用MACD辅助背驰须明显回拉0轴，刚上0轴时至少本级无背驰问题，下午信号为1分以下。',
  'MACD|背驰|操作级别|确认', 1, '原答否定读者两个区间直接比较即5分背驰，不与反向力度比较需穿轴的另一对象混同。', figs=[(252, 1)])
c(33, 'daily-jan4-feb6-three-thirty-not-nine-thirty', '253-b003',
  '作者把完整日线中枢定位1月4日至2月6日，虽视觉有九段但它们是5分、非30分；到2月6日才严格构成日线所需三段，也可看作5分中枢延伸形成。',
  '走势中枢|中枢延伸|次级别|操作级别', 1, '三5分到30分、九5分再到日线是本例层级计量，不能把九段各误升30分；图上周期或框线不能代替段真实级别。',
  ['2007年3月6日16:26对第一段日线的具体说明'], figs=[(253, 1)])
c(33, 'weekly-first-leg-until-april-or-up-no-weekly', '253-b004',
  '从周线中枢角度，作者说上述日线只算第一段，若在该位置真形成周线至少还盘到4月以后；也可直接上破，因此不构成周线中枢。',
  '走势中枢|操作级别|完成|走势预测|当下', 1, '至少4月是该时该位置预期非所有周线中枢固定时长，原文仍有强势不成周线支；后配4月K不能抹掉当时未确认。',
  ['2007年3月6日当时位置与未完成结构'], figs=[(253, 1)], ambiguity='dated_weekly_first_leg_and_future_duration_conditional')
c(33, 'macd-lines-generally-area-complex-multilevel-first', '254-b000',
  '作者对MACD相对重要性一般先看黄白线，复杂走势中柱面积和较重要，但更关键的是各级别配套以判断信号作用。',
  'MACD|MACD柱波|背驰|操作级别', 1, '一般次序不是所有情形固定词典序，也未逐条认可600598读者点价/柱峰；不用单指标冲突直接补背驰充分条件。', figs=[(254, 1)])
c(33, 'subminute-pull-important-under-five-thirty-center', '254-b000',
  '若中枢本是5分或30分、每次离开是1分走势，作者说1分以下背驰可因中枢回拉引起较大回调，故这些小信号重要。',
  '中枢回拉作用|背驰|次级别|操作级别|中枢震荡', 1, '5/30中枢与1分离开是联合语境，不能反推所有1分以下信号都同样重要或本身必使中枢升格。',
  ['已成5分或30分中枢', '围绕离开段为1分走势类型'], figs=[(254, 1)])
c(33, 'using-divergence-needs-practice-not-detection-only', '254-b001',
  '作者把辨别背驰视为基础，更重要是结合综合情况利用背驰，需要持续实践提高。',
  '背驰|操作熟练程度|操作策略', 2, '实践要求不认证任何具体账户成绩，也不以学习程度代替可追溯的结构和证据。')

keep('243-b011', 'upper-l032-c-stage-nine-sublevel-extension-author-limit-with-wave-premise upper-l032-c-stage-straight-limit-up-no-wave-cannot-add-level',
     '33明确初三加新增六，总九；32不能超过9为较粗口径，波动/相应次级与重叠条件不取消，不按九K计。')
keep('243-b012 244-b000 245-b002', 'lower-l063-chart-period-not-center-level lower-l077-c-stage-period-not-trend-level',
     '33严格从成交分笔递归与便利周期图序列分开；15分只是展示1分过程，7分/15加60可用也不是严格级别任意等式。')
keep('244-b003', 'upper-l028-c-stage-connections-sublevel-or-lower-not-exact upper-l018-c-stage-center-connection-below-sublevel-gap',
     'a/c非必有、b可缺口再次支持连接可更低，不将缺口自身当中心一段。')
keep('245-b001 246-b000', 'upper-l032-c-stage-b-no-divergence-b-center-may-exceed-a upper-l032-c-stage-2915-is-gg-not-center-top-2894-correction',
     '33以中枢回拉另一释义讲B更大后的反向c，GG2915与ZG2894区分，力的比较方向/参照段不擅统一。')
keep('249-b004 252-b007', 'upper-l032-c-stage-divergence-level-not-rise-level-without-nesting upper-l031-c-stage-standard-trend-nesting-with-sudden-break-exception',
     '至少本级最低结果与较大影响/未必紧邻次级分开，a`+B不允许机械把每级结束强制由直接次级造成。')
keep('250-b004', 'upper-l032-c-stage-third-buy-retest-at-least-sublevel-three-down-up-down upper-l032-c-stage-2915-is-gg-not-center-top-2894-correction',
     '三买定义以次级不入中枢为准，不回GG是更强程度而非必要条件，不擅补等于边界。')
keep('251-b001 253-b003 253-b004', 'upper-l031-c-stage-weekly-three-legs-original-explicitly-qualified upper-l032-c-stage-nine-sublevel-extension-author-limit-with-wave-premise',
     '33具体日线1/4—2/6及周线第一段/强势可不成的分支与31粗说更正、32周线判断并列；不能用晚图倒认早时必已完成。')
keep('253-b000 254-b000', 'upper-l032-c-stage-subminute-time-chart-or-one-minute-hist-not-lines upper-l032-c-stage-600550-no-five-without-macd-lines-return-zero',
     '普通本级明显回轴、反向比较穿轴、更低级借柱三种对象分开，面积/黄白相对重要性不补统一优先级程序。')

issue('extension-initial-three-added-six-and-recursive-level', '243-b011 250-b012 250-b013 250-b014 253-b003',
      '33将新增延伸最多五/到六加初三总九说清，但完成次级、重合、有波动仍为必要语境；日线例的九5分非九30分，不是时间/K计数。',
      '与32原九次级表述按计数口径关联，不改原文或仅凭数量断任何中枢级别；完整递归与后标准跨课仍待统核。', True)
issue('chart-model-and-valid-interpretations-versus-unique-path', '243-b012 244-b000 244-b001 244-b002 244-b003 245-b002',
      '周期图是简略模本，严格从每笔成交递归不同于后63/65几何入口；合理多释义非随意，训练直觉/唯一道路是比喻而非唯一可交易路径证明。',
      '保存7分/15加60的观察选择及1分过程用15分展示，不能任意固定图周期与结构级别等式。', True)
issue('center-pull-force-same-opposite-direction-and-macd', '244-b003 244-b004 245-b000 245-b001 246-b000',
      '回拉星球力未定量；普通同向b/c背驰与反向a+A+b/c比较不相同，后例又说c与b力度，参照段口径未完整形式化；同侧回轴/异侧穿轴分对象。',
      '不补物理公式或积分/唯一力度阈值，不能把反向不需回拉推成普通本级MACD也不必回轴。', True)
issue('weekly-status-current-branches-not-fixed-duration', '251-b001 251-b002 251-b003 253-b003 253-b004',
      '3/5仍列日线延伸可上破与周线盘整两支，3/6说日线完整1/4—2/6、周线仅第一段且若成须4月后；与32足够周线句存在语境/时点范围待全书统核。',
      '不简单按日期全局覆盖，也不把后图紫框与未来3532点当早时已成周线证明；1500点仅条件预测。', True)
issue('center-expansion-word-and-old-system-persistence', '250-b010 251-b009',
      '3/6明确扩张说一中枢升级，旧B遇新至少同级不重叠或更大中枢时仍归入系统；与20扩展两同级比较的原词范围不自动等同。',
      '保持中枢扩张/扩展独立概念，待后文系统定义；不把旧中枢说成失去一切作用。', True)
issue('third-buy-edge-gg-and-forming-invalidated', '246-b001 250-b004 252-b004',
      '三买须次级回抽不入中枢，连GG都不回才最强；形成中结构被急跌破坏不能成三买，不是已成立后随意撤销。',
      '不自行补触上沿等于的开闭规则，不把事后反涨/读者自述作为当时买点充分证据。', True)
issue('indicator-priority-and-small-signal-context', '251-b012 252-b007 253-b000 254-b000 254-b001',
      '成交量辅助/结构优先，黄白线一般重要、面积复杂走势重要而多级更重要；中枢5/30且1分离开时次1信号可大回拉，不等所有小信号必动。',
      '保留一般/具体条件，不认证读者6005989.24所有判断，不补统一指标打分优先级或实测成功率。', True)
issue('historical-probability-safety-forecasts-and-watch-pool', '246-b000 247-b001 247-b003 248-b000 248-b001 249-b007 250-b000 250-b007 251-b002 251-b006 252-b001',
      '100点/130点、10%/30%降本、三买最强、周线1500、结构不可控和交替成功率皆作者未独立验证主张；自选几十百只不是持仓数。',
      '历史板块/指数观点不作当前推荐，观察池/持仓和可轮换/可单板块两方案分开，不由自评或后图提供收益保证。')
issue('embedded-cross-day-dates-case-times-and-figure-origin', '247-b001 247-b002 247-b005 247-b006 248-b000 248-b002 248-b003 249-b000 246-b000',
      '10解盘段按3/5午/夜与3/6分组，7图6文后1未核；A端13:37和31简答13:38差异保留，图15分展示不升对象级别。',
      '原文/字符映射/坐标不改，源头3/2评论与每条答复日期不污染，后3/7—4月行情不能倒证当时预测。')

note('246-b003 246-b004 247-b001 247-b003', 'dated-market-self-report-and-news-context',
     '3/2军工/中信发行/心理修复/5日线辅助及999/343基金赎回自述、3/5平安/查资金影响等已读。',
     '消息因果和对抗操盘归属未独立核，不能视作法律事实或生成攻击步骤，尾部新日期只管后段。')
note('247-b005', 'standalone-evening-time-header', '独立2007-03-05 21:14:20时间头已视觉核。', '元数据改为夜评，不保留3/2错误继承，不独立支持技术结论。')

relations = {
    'upper-l033-c-stage-ambiguity-related-to-centers-not-fixed-template': [('走势多义性', '走势中枢', 'related')],
    'upper-l033-c-stage-extension-six-added-plus-three-initial-nine': [('中枢延伸', '次级别', 'qualifies')],
    'upper-l033-c-stage-strict-level-from-trades-not-fixed-time-periods': [('周期K线图', '级别', 'distinguishes')],
    'upper-l033-c-stage-valid-multiple-interpretations-not-all-to-eliminate': [('走势多义性', '分解多样性', 'related')],
    'upper-l033-c-stage-last-center-pullback-interpretation-of-divergence': [('中枢回拉作用', '背驰', 'related')],
    'upper-l033-c-stage-macd-same-side-divergence-versus-opposite-cross-zero': [('中枢回拉作用', 'MACD', 'qualifies')],
    'upper-l033-c-stage-bottom-rebound-stays-below-center-third-sell': [('第三类卖点', '中枢回拉作用', 'related')],
    'upper-l033-c-stage-third-buy-center-edge-versus-swing-high-strongest': [('第三类买点', 'GG', 'qualifies')],
    'upper-l033-c-stage-new-center-at-least-same-nonoverlap-old-enters-system': [('中枢系统', '走势中枢', 'composed_of')],
    'upper-l033-c-stage-volume-auxiliary-structure-first': [('成交量', '几何结构', 'qualifies')],
    'upper-l033-c-stage-sudden-index-fall-destroys-forming-third-buy': [('第三类买点', '当下', 'qualifies')],
    'upper-l033-c-stage-subminute-pull-important-under-five-thirty-center': [('中枢回拉作用', '次级别', 'qualifies')],
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
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], '读者盘整相加/中枢扩张/买卖点/个股与指数假设仍是提问；作者只回相应范围，未逐一认证读者点价、柱高/面积和所有操作表现。'
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
        'note': '延伸新增六加初始三共九，图周期是简略模本非严格结构级别；中枢回拉的同向/反向比较分开，MACD同侧回轴与异侧穿轴不混；周线仍有不成的强势分支，旧中枢归层级系统非消失。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True, reviewer=REVIEWER, visual_review_note=f['note'],
             figure_source_review='7图全部查看，6文后1原发未核；3/7、3/8、3/9及日图4月未来K不证明当时预测，1分过程用15分展示不是结构级别，原13:37与早13:38不静合。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 109 and Counter(x['lesson_number'] for x in ledger) == {33: 109}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [33], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(243, 255)), 'figure_objects_viewed': 7, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '33课109段12页7图同模型四轮；10跨日解盘日期修正，新增六延伸加初三/模本与严格级别/中枢回拉同反向MACD/周线条件及多级配套保留，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


