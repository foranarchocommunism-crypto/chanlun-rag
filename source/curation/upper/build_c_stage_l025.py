"""Materialize the main agent's four-pass reading of lesson25.

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
BASE = 'c_stage_l025'
REVIEWER = 'Codex 主代理 / 阶段C上册25课同模型四轮复核'
SOURCE_SHA = '696e6b0665dae1227e6fe4f2695240ff025915e22b374230865412e5ae65cefb'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-025' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 272
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 145 AND 166 ORDER BY pdf_page,id', (DOC,))]
assert len(figures) == 13
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
    pending.append({'id': 'upper-l025-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})


quote_overrides['153-b012'] = passages[pid('153-b012')]['text'].split('（从图上看')[0]
assert quote_overrides['153-b012'].endswith('其他级别要相应去看了。')

c(25, 'kiss-average-and-macd-auxiliary-not-center', '144-b005',
  '第25课明确“吻”属于均线系统，均线是走势的简单数学处理、离不开或然率；均线与MACD同为辅助工具，不能与中枢概念混用。',
  '均线系统|均线体位|MACD|走势中枢', 1, '作者明确区分辅助系统与中枢；不把早期吻条件自动换成严格三类点或中枢充分条件。')
c(25, 'macd-usual-parameters-and-ultrafast-limit', '144-b006',
  '作者说MACD灵敏度与参数有关，一般使用12、26、9，可应付一般走势；过快走势中一分钟图的反应也可能太慢。',
  'MACD|操作级别|操作熟练程度', 2, '这里明确给一般参数，不能反推14课“长一倍”究竟加倍哪些参数；也不是唯一规定参数。')
c(25, 'rapid-one-minute-height-exception-600779', '144-b006 145-b000',
  '600779从16.5急升至19的一分钟趋势延伸例中，作者以17.5时柱高为标杆：18.5与19两次柱高不再突破，即使面积更大，也警示乖离过急后的回调。',
  'MACD|MACD柱波|乖离极限|走势延伸', 1, '只用柱高的特例前提是1分钟急促上升、快到本图不能表现通常背驰；其他情况必须配黄白线，不把柱面积较大静默改小。',
  ['600779该次一分钟急促上升及作者所辨乖离极限'], figs=((145, 1),), ambiguity='empirical_deviation_limit_not_numeric_algorithm')
c(25, 'limit-up-sine-indicator-not-divergence', '145-b001',
  '对不断一字涨停，作者说MACD在1分钟甚至5分钟可出现类正弦波动，不能按通常背驰套用；可观察1分钟中枢是否持续上移，停止上移后再看大级别调整。',
  '涨停|MACD|中枢上移|操作级别|背驰', 1, '中枢不断上移是该段持有观察条件，不等于任意柱波都已构成新中枢或所有涨停都无风险。')
c(25, 'limit-up-longer-macd-and-resistance-warning', '145-b001',
  '连续涨停若参考MACD，作者建议较长周期如30分钟；红柱回跌低点渐低、触零或略绿后再放红是警告，结合大级别阻力及涨停失封看震荡。',
  '涨停|MACD|MACD柱波|操作级别|调整', 2, '600385当时2.92/3.22/3.28为原例价格，警告加阻力/失封语境不是单柱充分卖点；图含后续行情。',
  ['本段不断涨停的MACD辅助观察'], figs=((146, 1),))
c(25, 'first-rise-limit-open-medium-term-scope', '145-b002 146-b000',
  '若连续涨停发生在上涨第一段，作者说开板震荡并形成一定级别中枢后往往还有一段上涨；中线应着重大级别调整，超短差须有能力才参与。',
  '涨停|走势中枢|操作级别|操作熟练程度|调整', 2, '保留如果/往往和中线语境，不把“必须大级别背驰”当任意事件无调整或确定新高的保证。',
  ['连续涨停在第一段上涨中，站在中线角度'])
c(25, 'usual-two-center-first-stage-zero-axis', '146-b003',
  '作者描述标准两中枢上涨的常见MACD形态：第一段黄白线从零轴下上穿，在零轴上停留时形成相应第一中枢与第二类买点。',
  'MACD|走势中枢|第二类买点|上涨', 1, '原文“一般来说”及“标准两个中枢上涨”的完整结构前提保留；不把刚上零轴视作所有二买充分判据。',
  ['第25课标准两个中枢上涨的常见辅助指标形态'])
c(25, 'usual-two-center-impulse-and-second-center', '146-b003',
  '第一中枢突破后黄白线快速拉起，作者说这段往往力度最大，延伸和指标钝化常在其中；一般次级别背驰结束后形成第二中枢，黄白线逐步回零轴附近。',
  'MACD|走势延伸|走势中枢|次级别|背驰', 1, '往往和一般不是无例外统计律；次级别背驰结束的是该段，不当整体大趋势已终。',
  ['前述标准两中枢上涨结构'])
c(25, 'usual-two-center-final-lines-or-area-or-height', '146-b003',
  '再次突破第二中枢时，作者列黄白线不创新高，或柱面积、或伸长高度不能突破新高，结合前述两中枢上涨过程出现背驰，结束该上涨。',
  'MACD|MACD柱波|背驰|走势中枢|上涨', 1, '这里的或按原文保留，不静默改成线柱必须全部同弱，也不把或项从完整趋势/中枢/回轴过程剥离成普遍充分判据。',
  ['第25课标准两中枢上涨及先前回轴过程'], ambiguity='macd_or_indicators_with_full_structure_not_standalone')
c(25, '000572-weekly-second-buy-dates', '146-b004 147-b000',
  '000572案例中，作者称日周双重第二类买点配合：周线2005/12/9至2006/7/14第一段使MACD回零轴上，其后第一中枢、2006/11/17二买，黄白线近零轴横盘后拉起。',
  '第二类买点|MACD|走势中枢|同步共振|操作级别', 2, '具体日期与股票为作者历史回顾，图为复权图而正文价格处理未详；不以叠箭头代替结构完成证明。',
  ['2007年1月23日对000572周线的回顾'], figs=((147, 1),))
c(25, '000572-day-first-center-dates', '147-b000',
  '000572日线例中，作者列2006/11/13至12/6为第一段，三段回拉于2007/1/4结束形成第一中枢，随后突破且MACD从零轴附近拉起。',
  '第二类买点|MACD|走势中枢|操作级别', 2, '日线与周线日期分别保存，不把第一中枢尚未形成时的直线拉升补成已有背驰。',
  ['2007年1月23日对000572日线的回顾'], figs=((147, 2),))
c(25, '000572-next-centers-author-projection', '147-b000',
  '对000572后续，作者按日线新中枢、回轴再突破背驰、周线以上中枢及更大调整的次序作展望，最后称至少月线级别。',
  '走势预测|走势中枢|MACD|调整|操作级别', 3, '这是当日作者未来推演，并非本项目验证已发生的事实；不能仅从日周二买推无条件指定未来完成时点。',
  ['2007年1月23日000572的作者后续推演'], ambiguity='historical_author_projection_not_outcome_verification')
c(25, 'zero-axis-center-at-least-chart-level', '148-b000',
  '作者提醒：MACD在零轴附近盘整或回抽所对应中枢，不一定恰为该级别，而是至少该级别；如日线也可能对应周线中枢，此时日线有三段走势。',
  'MACD|走势中枢|级别|周期K线图', 1, '这里是原文辅助识别描述，不把任何MACD触零都直接证明已完成中枢；三段与递归要求仍需另核。',
  ['原文所述零轴盘整/回抽已形成中枢的语境'], ambiguity='indicator_at_least_level_description_requires_price_structure')
c(25, 'jan23-gap-five-day-line-case', '148-b001 152-b001',
  '1月23日解盘称2870被触及，仍可能演化为大级别中枢；当时以5日线不破作简便观察，破则预期大级别中枢延续。',
  '缺口|走势中枢|均线|调整', 3, '同一解盘在152页重现，不计两次独立验证；仍可能不是已形成，5日线为该案例辅助界限。',
  ['2007年1月23日上证指数解盘'], figs=((148, 1),))
c(25, 'short-difference-buy-sell-or-sell-rebuy', '148-b007 149-b000',
  '纠正1月23日短差节奏时，作者主张早出午补，并明确短差既可先买后卖，也可先卖后补；若不及时轮动，则应按长线或至少日线背驰等待。',
  '缠中说禅短差程序|操作级别|资金管理', 2, '早出午补和百点空间是当日2970开盘/回试缺口的判断，不能推广成每天固定时段买卖。',
  ['2007年1月23日上证回试缺口的问答'])
c(25, 'outer-high-touch-needs-sublevel-retrace', '149-b003 149-b012 150-b000',
  '对2870外围高点触及，作者解释：首次低级别回抽未回原中枢、只触外围高点，尚不能断言扩成大中枢；日线例须至少30分钟次级别回拉触及，单5分钟可能只是途中小回拉。',
  '中枢扩张|围绕中枢的运动|次级别|走势中枢|中枢连接', 1, '外围高点与中枢上沿分开，价格触及还须看回拉级别；两次回试的当日操作说法与一般结构条件不压成同一计数公式。',
  ['1月23日2870/2840区别及日线中枢答复'], ambiguity='case_two_retests_not_universal_fixed_count')
c(25, 'v-turn-head-shoulder-then-new-down-center', '150-b003',
  '对直接转势提问，作者描述常见V转：最高点左右各有一上一下次级别走势，再左右形成中枢，形似头肩顶；继续下破并形成新中枢才构成所说下跌。',
  '趋势转折|走势中枢|下跌|次级别', 2, '一般形态描述，不把类似头肩顶作为充分定义；读者原设A/B不是作者逐项确认的中枢归类。')
c(25, 'direct-break-old-up-center-needs-second-new-down', '150-b004',
  '若从顶部直破原上涨最后中枢，作者说一般会回拉成大中枢；若罕见地不回拉而在下方直接成中枢，还须下破并再成第二个下方中枢才算下跌，常见于除权后或毁灭性突发利空。',
  '走势中枢|趋势转折|下跌|中枢下移', 1, '第一新中枢与第二新中枢的计数及先前上涨中枢不混加；罕见/基本只出是作者经验陈述，不作穷尽事件分类。')
c(25, 'thirty-minute-center-needs-five-minute-three', '150-b007 150-b008',
  '作者区分：日线中枢需三段30分钟走势；30分钟走势至少有一个30分钟中枢，而30分钟中枢需至少三段5分钟走势；30分图直线下跌不因画在该图就已有30分中枢。',
  '走势中枢|递归定义|次级别|级别|周期K线图', 1, '图周期与走势级别不能只凭显示外观等同；保留至少/三段与每段走势完成的递归语境。')
c(25, 'three-straight-chart-swings-not-daily-center', '150-b009',
  '作者说1分钟图连续暴跌、K线互不相挨不会形成所说中枢；30分图所见三段直上直下不构成日线中枢，只能按该例较小的30分中枢看。',
  '走势中枢|周期K线图|级别|重叠', 1, '这是紧邻三段5分/30分递归说明的例子，不是所有三根K线或任意三条直线即可认30分中枢。',
  ['第25课30分钟三段直上直下的级别误认问答'])
c(25, 'shrinking-bars-not-divergence-combined-conditions', '150-b012 151-b000 151-b001',
  '针对600779红柱缩短后仍上涨，作者强调背驰与柱子缩短不是一回事，须综合条件并检查黄白线是否回拉零轴；单看柱常会失效。',
  'MACD|MACD柱波|背驰|确认', 1, '与145页急速上升单看柱高的特殊警告并列；后者不等宣称标准背驰已经形成。')
c(25, 'learn-stock-before-futures-warning', '151-b002',
  '作者劝读者先在股票中练习，充分了解前不要做期货，并把股票风险较低作为当时练习比较。',
  '期货|市场风险|操作熟练程度', 3, '风险较低是作者相对期货的历史劝学语境，不宣称任何股票绝对低风险或风险被消除。')
c(25, 'crowd-no-risk-washout-fear-greed', '151-b010',
  '在引用两条读者从保证上涨转为惊慌的言论后，作者强调市场心态，称众人觉得无风险时须警惕洗盘，并指出恐惧和贪婪可被利用。',
  '市场心理|市场风险|市场陷阱', 3, '闭引号后的作者评论与两条读者话分别记载；这是作者心理观察，不是可验证无例外洗盘时间法则。',
  ['2007年1月24日药股洗盘评论'])
c(25, 'jan24-five-not-sixty-possible-divergence', '152-b006',
  '1月24日作者否定刚从零轴上来的5分钟背驰说法，转而提示60分钟可能背驰；若不迅速拉起而拖几天会有问题，并提醒60分一天四根、2870上站稳。',
  'MACD|背驰|操作级别|确认', 2, '可能与密切关注不是已确认，后图含2月走势不能使当时可能变确定；一天四根限该市场当时时段。',
  ['2007年1月24日16:03上证答复'], figs=((152, 1),))
c(25, 'daily-three-overlap-bars-practical-heuristic', '153-b006',
  '对逐级下看繁琐的提问，作者给实用识别：日线上明显三段，每段日K线有“至少三根以上重合”，基本可视作30分钟走势；看次级别背驰时再看次级别图。',
  '递归定义|走势中枢|周期K线图|次级别', 2, '基本都是为经验简化而非充分必要定义；原句至少三根以上不擅改精确不等号，不把任意三根重合等同完整30分走势。',
  ['2007年1月24日关于日线中枢实用识别的答复'], ambiguity='practical_overlap_heuristic_not_formal_level_definition')
c(25, 'macd-zero-retrace-before-level-divergence', '153-b012',
  '对上证15分钟回调问题，作者答复的确定引句要求MACD判断背驰先有黄白线对零轴回拉，无此则该级别不谈背驰，其他级别须另看。',
  'MACD|背驰|操作级别', 1, '同段尾括号“从图上看个人认为”署名未核，精确证据排除；不把该尾注说成作者确认小级别背驰。',
  ['本段通常MACD判断背驰语境，急速行情特例另条保留'], figs=((154, 1),), ambiguity='unsigned_parenthetical_attribution_unverified')
c(25, 'sixty-minute-adjustment-time-space-not-fixed', '154-b001',
  '对60分钟背驰是否必然调整较大且较久，作者回答不一定，往往可用空间换时间或相反。',
  '背驰|调整|幅度|级别', 1, '否定必然同时大幅且长时，不从更大级别推固定持续天数；此句不单独给量化换算。')
c(25, 'jan25-retest-and-complex-adjustment-stance', '154-b005 156-b001',
  '1月25日作者把回试前低确认2870突破与短线背驰联系，午间自称回试要求99%；收盘称三角后末段、30分钟背驰引发复杂调整，观察2700上下中枢。',
  '背驰|调整|三角形整理|走势中枢|概率原则', 3, '99%和2700范围均为当日判断，未有概率样本或实证；不与24日“60分可能背驰”静默归并同一已确认级别。',
  ['2007年1月25日午间和收盘上证解盘'], figs=((156, 1),), ambiguity='author_probability_and_level_descriptions_not_independently_verified')
c(25, 'jan25-weekly-center-maximum-not-duration-guarantee', '155-b005 156-b005 158-b000',
  '当时作者把最恶劣情况说成形成周线中枢，仍认为牛市第一波未完；同时说周线中枢能否走出也未定，强时歇两天可续攻。',
  '牛市阶段|走势中枢|调整|走势预测', 3, '相同展望在晚间重复，不作独立证据；这是2007年当日最大范围和强弱分支预测，不是普遍最大风险界。',
  ['2007年1月25日中线展望及21:31答复'], ambiguity='historical_maximum_adjustment_forecast_unverified')
c(25, 'concentrate-with-mobile-cash-size-exception', '157-b008',
  '对小账户同时买多只股票，作者要求较集中并保留机动资金反复短差降成本；大资金受举牌约束不宜同样集中。',
  '资金管理|机动资金|仓位|成本', 2, '保留资金量例外、机动资金和技术要求，未给统一持股数；不能把“最安全”转成无损保证。',
  ['2007年1月25日对读者同时买多只股票的答复'])
c(25, 'named-horizons-week-day-month-thirty-five-one', '157-b011',
  '本次问答按周线称中线、日线中短线、月线以上长线、30分钟短线、5分钟超短线，1分钟主要对T+0有意义。',
  '操作级别|周期K线图|T+0|长期投资', 2, '原句“只多T+0”保留为原引文，不纠正文；这是答中线多长的周期称法，不是将所有递归级别锁定K线周期或固定日数。',
  ['2007年1月25日中线含义问答'], ambiguity='source_only_duo_t0_typography_not_silently_corrected')
c(25, 'earnings-season-quality-small-technical-exception', '158-b007 161-b010',
  '业绩披露临近时作者偏向有业绩支持的股票，同时允许投入不大且有技术支持时考虑无业绩股票；盘整短差仍须关注质地、不追高。',
  '基本面|资金管理|操作策略|追高', 3, '限当时披露季的条件化意见，无业绩例外须同时投入不大和技术支持；不形成当前个股选择建议。',
  ['2007年1月25至26日业绩公布期问答'])
c(25, 'life-insurer-49-45-38-branches-case', '158-b010 159-b000 159-b001',
  '对601628，原答写“49那天不是背驰”，随后强调1月23需退出、有一波回落；后续看支持反弹和45中枢压力，较强围45震荡、较弱回38，长线仍待一线股启动。',
  '背驰|走势中枢|调整|操作级别|走势预测', 3, '原文“49那天不是背驰”可能是反问但句末无问号，保留原词不判唯一语气；24课同股背驰案例另证，不以图中后跌证实必然。',
  ['2007年1月25日22:04对39元买人寿者答复'], figs=((158, 1),), ambiguity='rhetorical_not_divergence_sentence_and_historical_forecast')
c(25, 'execute-level-points-not-extra-confirmation', '159-b010',
  '作者要求按相应级别有卖点卖、有买点买，不再等额外确认；中线持有也可在5/30分钟背驰先卖部分，下来找回补买点，反对卖点错过后恐慌杀跌。',
  '买卖点|操作级别|缠中说禅短差程序|机动资金|确认', 2, '本段“不能等什么确认”与162页三买须等次次级背驰或双次回拉确认分开记录；不解释成连买卖点自身形成条件也可省略。',
  ['2007年1月25日22:28操作提醒'], ambiguity='execution_not_wait_vs_signal_confirmation_scope')
c(25, 'mobile-cash-and-small-capital-all-in-condition', '159-b011 159-b012',
  '作者以自述8亿中留1亿机动及可随时变现持仓说明资金结构；特别小资金可全仓进出以提高利用率，但前提是充分把握买卖点。',
  '资金管理|机动资金|仓位|买卖点|操作熟练程度', 2, '资金数是作者自述，不认证账户；小资金/充分把握是全仓进出的联合限制，不把全仓写成全读者通用建议。')
c(25, 'icbc-jan26-third-daily-unfinished-case', '161-b001',
  '1月26日工行解盘中，作者预期破5.11形成日线第三段，再有周线第二段；他明确日线第三段是否走完需看下周，受新股与资金解冻配合影响。',
  '走势终完美|走势中枢|完成|走势预测', 3, '当时未完成判断须保留，不按图右端2月行情倒填当时已完成；5.11正文与图5.12标价分开。',
  ['2007年1月26日15:39工行解盘'], figs=((160, 1),), ambiguity='historical_unfinished_third_leg_and_forecast')
c(25, 'third-buy-needs-subsub-divergence-or-double-retest', '162-b001',
  '对600677猜测日线三买后失误的读者，作者要求第三类买点等次次级别背驰或双次回拉确认，不可只凭背驰迹象猜买。',
  '第三类买点|次级别|背驰|确认', 1, '保留或条件与原问日线/5分背景；未把双次回拉等成任意两根回调K线，最小级别无下一级问题另见165页。',
  ['2007年1月26日对600677买入失误的答复'], ambiguity='double_retest_confirmation_details_not_fully_formalized')
c(25, 'buy-and-sell-completes-operation', '162-b004 162-b007',
  '作者肯定当日低买者时，同时提醒震荡中出货点和会买也须会卖，来回才是一轮完整操作。',
  '买卖点|操作策略|交易规则', 2, '奖励不是读者每个买入价/全仓行为都已被技术复核；完整操作此处是交易轮次，不与走势类型完成混同。')
c(25, 'mobile-positions-and-liquidizable-assets', '162-b010 162-b011',
  '作者再次强调机动仓位，以及可随时变现的持股安排，用以应对突发波动。',
  '机动资金|资金管理|流动性|市场风险', 2, '所谓能对抗所有突发事件是作者表述，不证明停牌或流动性枯竭也能及时退出；166页风险反例另条保留。')
c(25, 'rapid-market-one-minute-mobile-exit-not-only-frame', '162-b014 162-b015 163-b001',
  '在急速波动市场可按1分钟背驰撤机动资金、部分兑现差价，不得追高；下次买点还需综合30分钟调整，市场缓和则看5或30分钟，不能始终死盯1分。',
  '机动资金|操作级别|背驰|追高|市场风险', 1, '先退出/再买对象是机动部分，非无条件全仓；次日开盘受消息心理影响，文中快速市场前提必须保留。')
c(25, 'mobile-fraction-quarter-third-half-in-bull', '162-b016',
  '作者说机动资金一般占仓位1/4至1/3，走势特别不好可提高至1/2；当时牛市中期调整认为不必完全空仓，可利用往返。',
  '机动资金|资金管理|仓位|牛市阶段', 1, '牛市、机动部分、一般与走势特别不好是比例限定；不外推熊市或所有风险，也不把拿着比空仓收益高当已实证。',
  ['2007年1月26日急剧变动市场及牛市调整问答'])
c(25, 'jan26-one-minute-not-five-and-time-difference', '163-b004 163-b007 163-b011 164-b000',
  '1月26日作者否定5分背驰，认定2720附近为1分背驰：前日13:40下跌、次日9:30指标低点、9:50三波反抽回零轴，再跌指标未创新低；简答写10:56，详答写10:57。',
  '背驰|MACD|操作级别|走势中枢', 1, '不同回复的10:56/10:57均保留，图低点2720.83不改文字2720；不得把1分肯定升成5分肯定。',
  ['2007年1月26日上证一分钟回顾'], figs=((163, 1), (164, 1)), ambiguity='same_case_minute_1056_1057_difference_retained')
c(25, 'double-zero-retest-first-center-third-sell-case', '164-b001',
  '作者把10:17更近零轴称双次拉回，并说通常第二次构成下跌第一中枢；在跌破前中枢的该例，刚好构成标准最小级别第三卖点。',
  '双次拉回|MACD|走势中枢|第三类卖点|最低级别', 1, '保留原句一般与该例跌破前中枢的结构；不将两次MACD回轴单独证明任意级别三卖。',
  ['1月26日16:06对上证1分钟下跌结构的回顾'], figs=((164, 1),), ambiguity='double_retest_usually_vs_definite_rhetoric')
c(25, '000915-consolidation-no-divergence-just-zero', '165-b001',
  '作者说000915仍盘整，不符趋势两段比较；当时盘整背驰也没有，因为MACD刚上零轴，须上轴后大拉、回轴、再拉才谈该类背驰。',
  '背驰|盘整背驰|MACD|趋势|盘整', 1, '否定两个不同判断均保留，不把“在盘整”一项就断言任何盘整背驰不可能，也不把柱已缩单独当成满足。',
  ['2007年1月26日15:56对000915五分追问'], figs=((164, 2),))
c(25, 'macd-instead-of-body-position-context', '165-b009',
  '面对男上位/女上位首次缠绕的问题，作者说有MACD便可不用上下位，道理一样且MACD直观。',
  'MACD|均线体位|均线系统', 2, '回答没有逐项认可读者同段关于所有第一二买价序和首次缠绕的推理；工具替代不等中枢定义替代。')
c(25, 'jan26-first-second-buy-and-lowest-third-difficult', '165-b010',
  '作者给当日1分一买10:57/2720，二买13:30/2771，对应双回抽零轴站稳；又说当时以1分钟为最低时，三买很难找到。',
  '第一类买点|第二类买点|第三类买点|最低级别|MACD|双次拉回', 1, '很难不是绝对不存在，也不与164页最小级别三卖自动统一成禁用第三类；保留当时最低观察级别前提。',
  ['2007年1月26日16:17当日上证实例'], figs=((164, 1),), ambiguity='minimum_frame_third_points_difficulty_not_impossibility')
c(25, 'first-second-third-price-order-original-claim', '165-b011',
  '第25课此答复说第一类买点比第二类低、二比三低，卖点反向；它紧接当日2720一买和2771二买实例。',
  '第一类买点|第二类买点|第三类买点|级别', 1, '原文“当然”不静默改成仅一般；后第101课明确给一般/最强/最弱含二买低于一买的情况，分条保留并标跨课边界待核。',
  ['第25课原答及相邻当日实例语境'], ambiguity='earlier_unqualified_price_order_vs_l101_explicit_exceptions')
c(25, 'working-hours-choose-larger-frame', '165-b014',
  '对上班时只能看走势成交量判断背驰的问题，作者说很难准确，可按30分钟等更大级别，变动较慢。',
  '背驰|操作级别|操作熟练程度|成交量', 2, '这是精度和精力限制的建议，不说无MACD就从逻辑上不可能判断，也不补成交量公式。')
c(25, 'imminent-suspension-risk-no-time-to-correct', '166-b004',
  '对580994过夜买入，作者强调快停牌不宜再介入，技术再好也先看风险；最大风险在没时间改错、使错误永久，复利力量则是作者的长期主张。',
  '停牌风险|市场风险|权证|赌徒心理|资金管理', 1, '不认可读者0.392为一买；复利必然/战胜一切为未实证主张，不覆盖停牌损失，不据此设计交易指令。',
  ['2007年1月29日对580994临近停牌的提醒'], ambiguity='compounding_guarantee_rhetoric_not_verified')

c(25, 'trade-points-not-predict-cost-practice-premise', '157-b003 157-b004',
  '作者要求应对走势而不预测，有持股者按短线买卖点往返降低成本，前提是先学好技术；他用“战无不胜”强调降成本作用。',
  '缠中说禅短差程序|成本|买卖点|走势预测|操作熟练程度', 2, '技术前提与作者修辞均明示，不把高卖低买的要求当任何操作者可机械保证做到，也不忽略费用和T+1。',
  ['2007年1月25日15:59回复提醒'], ambiguity='cost_reduction_guarantee_rhetoric_not_proven')

keep('144-b005 165-b009', 'upper-l024-c-stage-center-replaces-kiss-macd-auxiliary upper-l024-c-stage-moving-average-macd-complement',
     '25明确辅助工具与中枢不同，吻可由MACD替代；不把工具一致扩大为指标可证明中枢所有数学结论。')
keep('146-b001', 'upper-l024-c-stage-standard-divergence-retrace-b-center upper-l024-c-stage-consolidation-short-difference-scope',
     '标准趋势背驰至少回B与盘整背驰可能形成三买分开；25重述原范围，不另造固定百分比。')
keep('146-b002 149-b006 149-b007 153-b009', 'upper-l024-c-stage-early-higher-trend-small-divergence-limited upper-l024-c-stage-rapid-top-small-divergence-impact',
     '日线初中段与末段快速赶顶不同，1分短差需及时回补且消耗精力；不由任意背驰统一期待50%回跌。')
keep('153-b000 158-b004', 'upper-l024-c-stage-buy-in-falling-retest-with-signal',
     '上涨后不追高、回调找相应买点的历史提醒；不新增当前买入推荐。')
keep('153-b012', 'upper-l023-c-stage-zero-axis-nearby-not-strict-cross upper-l024-c-stage-standard-macd-area-completion-test',
     '正常MACD综合结构与零轴附近、完成状态并看；未核尾括注不进入新证据，不替作者判小级别结论。')
keep('165-b011', 'lower-l101-c-stage-first-second-third-higher-only-general lower-l101-c-stage-second-buy-below-first-permitted',
     '25原价序与101明确一般/最弱分支同存；101含二买低于一买，不能按日期自动覆盖25或把25抽成全书无例外。')

issue('auxiliary-system-vs-center-and-force', '144-b005 144-b006 146-b003 148-b000',
      '吻/均线/MACD与中枢不同；25给一般12/26/9但不解决14长一倍参数；零轴至少级别与两中枢常见形态不是完整可执行充分定义。',
      '保留前文两均线面积及后文MACD辅助各自来源，不补自动识别阈值，跨课参数按明确文本继续核。', True)
issue('rapid-bars-and-limit-up-exceptions', '145-b000 145-b001 145-b002 146-b003 151-b001',
      '一分钟急升可只看柱高警告，其他情况配黄白线；一字涨停类正弦MACD不能按通常背驰套。乖离极限与线/面积/柱高或项未给普遍计算法。',
      '严格保留特殊行情前提及警告/确认区别，不把柱缩直接当标准背驰，或把面积大一律否定高度特例。', True)
issue('center-level-recursion-retest-and-practical-heuristic', '149-b003 149-b012 150-b000 150-b007 150-b008 150-b009 153-b006',
      '外围高点触及须看回拉级别；直线三段与递归走势不同，日K至少三根以上重合是基本如此的实用提示而非形式定义。',
      '不只凭三K/两回试或图周期生成中枢，继续核后课级别细化及扩张条件。', True)
issue('price-order-vs-l101-and-lowest-third-points', '164-b001 165-b010 165-b011',
      '本课一二三价序未带一般限定，101后有二买低于一买的明确分支；本课又说最低1分三买难找，同时给最小级三卖。',
      '保留两个来源各自语境和未解决解释，不以较晚日期覆盖，也不把很难换绝无。', True)
issue('confirmation-word-and-double-retest', '159-b010 162-b001 164-b001 165-b010',
      '不能等什么确认与三买须次次级背驰或双次回拉确认分别出现，双次拉回还有MACD与结构语境；不可抹去信号形成条件。',
      '按问答对象分别给取证路径，不自行补统一实时算法、回拉次数或等价关系。', True)
issue('mixed-attribution-headers-and-time', '149-b008 149-b009 150-b005 150-b006 151-b007-s01 151-b008 151-b009 151-b010 153-b012 156-b004 161-b002 161-b003',
      '赚到了/天山飞狐追问、151双读者引用后作者解盘、晚间自引及29日嵌时间已修；153括注个人认为的署名仍未核。',
      '原文/几何不改，仅明确作者句作证；尾部时间头支配后文，不能移作前文日期；括注身份保留开放。', True)
issue('case-time-prices-forecast-and-guarantees', '154-b005 156-b001 158-b010 159-b001 161-b001 162-b016 163-b007 164-b000 165-b010 166-b004',
      '10:56/10:57、2720/图2720.83、5.11/图5.12、人寿不是背驰反问语气、30分/60分解盘及99%/复利必然等各有边界。',
      '保留原数与文字、预测/完成/实证区别，不倒用文后行情或宣称收益保证，停牌不能改错是明确风险。')
issue('figure-origin-and-extra-annotations', '145-b000 145-b001 146-b004 147-b000 148-b001 152-b006 153-b012 156-b001 159-b001 161-b001 163-b004 164-b001 165-b001',
      '13本课图已看，8有文后行情，5原发未核；另144上方前课图只作边界检查。复权图、箭头、柱面积数字/图线并非全已认证作者注。',
      '不以彩色判后加，不以顶部旧光标忽略右端未来K，不让图注替正文或证实历史预测。')

note('148-b002 148-b003 151-b011 151-b012 151-b013 151-b014 151-b015 152-b009 153-b001',
     'historical-sector-and-holdings-context',
     '银行回归、军工/有色/农业/环保/公用事业及八股、换老资金与新资金和持股涨幅的作者历史叙述已读。',
     '仓位和收益是作者自述，题材时效截至原日期；不核为账户事实或现时潜力，不将后来补的身份混回读者引言。')
note('149-b008', 'mixed-author-reader-heading-boundary',
     '作者难做短差者中线可能更好的观察及读者“赚到了”署名共段，后提问已单独改读者。',
     '不把读者后问作作者观点；该比较不是经统计验证的选股公式，段尾署名不进入作者证据。')
note('151-b004 151-b005 151-b006 151-b007', 'author-citation-and-reader-quotes-context',
     '作者引12/19公告并自述21交易日翻倍，随后两条未署名读者保证上涨/惊慌言论，下一段才恢复作者。',
     '公告内旧时间是所引标题而非本篇日期，读者/收益/神奇数字各不作技术充分条件。')
note('154-b003 154-b004 154-b006 155-b000 155-b001 155-b002 155-b003 155-b004 155-b006 155-b007 156-b000 156-b002 156-b003 156-b006',
     'historical-political-economic-and-forecast-context',
     '泡沫、外资/民族叙事、工行业务预期、战略转仓、三波牛市与自称无利益关系完整已读。',
     '保留原文可检索，不从政治修辞、未来业务或绝对看多断言推出普遍技术法则；作者持仓/操盘自述未外核。')
note('157-b000 157-b002 157-b005 157-b014 158-b003 159-b004 159-b007 159-b009',
     'historical-tactical-and-market-context',
     '当时金融稳定/二三线主攻、股权事件、控盘耐心、此前60分警告自评与操作提醒引语已读。',
     '历史战术和自评不等已经独立证实的价格因果或操盘能力，技术条件在相应命题中单列。')
note('159-b014 160-b000 160-b001 160-b002 160-b003 161-b000 161-b002 161-b003 161-b004 161-b005 161-b006 161-b011',
     'historical-self-quotation-capital-and-jan29-context',
     'Jan26自引Jan25观点、PK挑战、2720实践称赞、资金周转/同盟比喻及Jan29行情/中移动回归叙述已读。',
     '外层日期和自引旧内容分开，161前段尾Jan29头只管后段；不把称赞全仓等风险消除或资金故事变执行方案。')
note('163-b010', 'source-explanation-introduction', '作者引入1分钟案例的提示已读。', '具体下跌/回轴/时间条件在后续跨页命题，提示不独立作结论。')
note('165-b002 165-b017 166-b001', 'historical-politics-and-event-timing',
     '000915暂不突破的作者政治化解释、对PK的跟帖及中移动回归时间/热情/行情配合风险已读。',
     '不认证操盘/资金因果，不把预期回归及帖子引用当确定事件时间或技术信号。')

relations = {
    'upper-l025-c-stage-kiss-average-and-macd-auxiliary-not-center': [('均线系统', '走势中枢', 'qualifies'), ('MACD', '走势中枢', 'qualifies')],
    'upper-l025-c-stage-rapid-one-minute-height-exception-600779': [('乖离极限', 'MACD', 'related')],
    'upper-l025-c-stage-limit-up-sine-indicator-not-divergence': [('涨停', '背驰', 'qualifies')],
    'upper-l025-c-stage-outer-high-touch-needs-sublevel-retrace': [('中枢扩张', '次级别', 'requires')],
    'upper-l025-c-stage-thirty-minute-center-needs-five-minute-three': [('走势中枢', '递归定义', 'requires')],
    'upper-l025-c-stage-shrinking-bars-not-divergence-combined-conditions': [('MACD柱波', '背驰', 'qualifies')],
    'upper-l025-c-stage-mobile-fraction-quarter-third-half-in-bull': [('机动资金', '资金管理', 'related')],
    'upper-l025-c-stage-third-buy-needs-subsub-divergence-or-double-retest': [('第三类买点', '确认', 'requires')],
    'upper-l025-c-stage-double-zero-retest-first-center-third-sell-case': [('双次拉回', 'MACD', 'related')],
    'upper-l025-c-stage-imminent-suspension-risk-no-time-to-correct': [('停牌风险', '市场风险', 'related')],
}


for r in rows:
    r['relations'] = [{'source': a, 'target': b, 'type': t} for a, b, t in relations.get(r['id'], [])]
by_passage = defaultdict(list)
for r in rows:
    for e in r['evidence']:
        by_passage[e['passage_id']].append(r)
for item in pending:
    item['lesson_numbers'] = sorted({int(passages[x]['unit_id'].split('-')[1]) for x in item['passage_ids']})
    if item['id'].endswith('figure-origin-and-extra-annotations'):
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
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], '读者柱缩即背驰、全仓成绩、价序推理和中枢级别问题不作作者证据，相邻答复不表示逐项认可。'
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
        'note': '吻/均线/MACD辅助与中枢分开，急速柱高和一字涨停特例、三段递归与实用提示、1分/5分、机动仓位比例和价序后课例外分别保留。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True, reviewer=REVIEWER, visual_review_note=f['note'],
             figure_source_review='13本课图全部查看；8文后行情图5原发未核，另144前课图作边界检查，不以光标旧日遮盖主图未来行情。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 272 and Counter(x['lesson_number'] for x in ledger) == {25: 272}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [25], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(144, 167)), 'figure_objects_viewed': 13, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '25课272段23页13本课图同模型四轮；19源段身份/时间修正，辅助指标/急速行情/中枢递归/机动资金与确认范围保留，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


