"""Materialize the main agent's four-pass reading of lessons15-16.

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
BASE = 'c_stage_l015_l016'
REVIEWER = 'Codex 主代理 / 阶段C上册15至16课同模型四轮复核'
SOURCE_SHA = 'a82977934861d2c63253c37ae70522b9a97e431805c942cd760f0915a30d9cd4'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id IN ('lesson-015','lesson-016') ORDER BY pdf_page,block_index,id")}
assert len(passages) == 194
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 58 AND 75 ORDER BY pdf_page,id', (DOC,))]
assert len(figures) == 14
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
    pending.append({'id': 'upper-l015-l016-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})


c(15, 'three-chart-categories-and-period-choice', '58-b009 58-b010',
  '作者把走势分为上涨、下跌、盘整，并先要求指定周期图：日线盘整在30分钟可为涨跌，图表选择与资金、性格和操作风格相应。',
  '周期图走势分类|周期K线图|操作级别|走势类型', 1, '这是早期周期图分类语境；第16课作者随后承认当时定义未完全严格，不把图周期直接等后期递归中枢级别。')
c(15, 'chart-rise-higher-high-and-low', '58-b011',
  '在第15课周期图定义中，上涨要求最近高点高于前高，且最近低点高于前低。',
  '周期图走势分类|高低点|上涨', 1, '两个且条件保留；此处为早期高低点定义，不替代17课以同向中枢和完成走势定义的上涨。', ['本课指定周期图及其过滤后的高低点'])
c(15, 'chart-fall-lower-high-and-low', '58-b012',
  '在第15课周期图定义中，下跌要求最近高点低于前高，且最近低点低于前低。',
  '周期图走势分类|高低点|下跌', 1, '未把只破一次低点当作全部下跌条件；高低相等情况原文未列，不能补成弱不等式。', ['本课指定周期图及其过滤后的高低点'])
c(15, 'chart-consolidation-expanding-or-contracting', '58-b013',
  '第15课将高点更高且低点更低，或高点更低且低点更高两种交叉组合列作盘整。',
  '周期图走势分类|高低点|盘整', 1, '两个分支为或，各支内部是且；第16课顺势平台例外与未严格声明必须一起保留，不补等高等低为作者已给分类。', ['第15课早期周期图分类'], ambiguity='early_high_low_definition_and_later_platform_exception')
c(15, 'kiss-filter-highs-lows-chart-frame', '58-b014 59-b000',
  '作者以吻过滤本图高低点：连短期均线都未突破的波动主要属更低图级；30分钟明显的高低点在周图可能不显，不能不加过滤地混比。',
  '周期图走势分类|均线系统|高低点|周期K线图', 1, '意义是该图的过滤，不是否认低级别高低点实际存在；这是当时均线辅助入口，后期分型/中枢判定另看。')
c(15, 'price-cross-versus-average-kiss-resistance', '59-b000',
  '本课以价格对均线反抗程度解释吻：突破短线未破长线为飞吻，破长线马上陷阱为唇吻，破长线后反复为湿吻，湿吻反抗较强。',
  '飞吻|唇吻|湿吻|均线系统', 1, '这里是价格突破长线，并非短均线已穿长均线，故不据此推翻11课唇吻短线未穿长线的定义；未给数值突破阈值。')
c(15, 'two-turning-paths-no-trend-no-divergence-scope', '59-b001',
  '作者在此列转折两路：湿吻后续原趋势成陷阱再回头，或盘整以时间换空间；对前者强调没有趋势没有背驰，并说盘整中无所谓背驰。',
  '趋势转折|湿吻|背驰|盘整|周期图走势分类', 1, '保留当时未细分盘整背驰的原话，不据此否定24课后来明确命名的盘整背驰；本段还强调判断先基于两均线与走势而非指标。', ['第15课前后趋势比较的背驰语境'], ambiguity='early_trend_divergence_statement_vs_later_consolidation_analogy')
c(15, 'trend-force-between-kisses-area', '59-b002',
  '缠中说禅趋势力度在本课定义为前吻结束至后吻开始、短长均线相交所形成的面积；前后同向趋势中，本次力度弱于前次即作者所称背驰。',
  '缠中说禅趋势力度|背驰|均线系统', 1, '这是两均线间面积，不是MACD柱面积；边界、积分/缩放口径未给完整计算法，不补自动化数值实现。', ['前后两个同方向趋势','按所选均线与吻的边界比较'], ambiguity='average_curve_area_computation_not_fully_specified')
c(15, 'confirmed-area-lag-lower-chart-localization', '59-b002',
  '作者说按趋势力度面积等再次吻后判定较稳妥，但会离真正转折有距离；可降一级图，用同法找相应转折以减小滞后。',
  '缠中说禅趋势力度|周期K线图|确认|背驰', 1, '减小距离不等任何时刻都能精确命中极值；降一级相应图不自动补为后期严格区间套全部程序。')
c(15, 'average-force-area-divided-by-time', '59-b003',
  '缠中说禅趋势平均力度是前吻结束至当下两均线所形成面积除以时间，可即时与前次平均力度比较；变弱预示背驰将形成，再看短长均线延伸长度缩短以观察低部。',
  '缠中说禅趋势平均力度|缠中说禅趋势力度|均线系统|确认', 1, '将形成不是已经确认，原句延伸长度不擅改成特定导数算法；作者称可同步抓转折但也明说技巧更高、风险稍大，不作实证保证。', ['同向趋势下本课均线平均力度比较'], ambiguity='instant_average_force_boundaries_and_length_not_formalized')
c(15, 'macd-auxiliary-not-force-definition', '59-b004',
  '作者说两均线K线图可用于判断走势，能力不足可参考MACD等技术指标，指标是辅助入口。',
  'MACD|均线系统|缠中说禅趋势力度|操作熟练程度', 1, '不把MACD同趋势力度面积混为一个公式，也不删除后面作者关于黄白线与柱波的具体要求。')
c(15, 'one-divergence-per-corresponding-trend', '60-b006 66-b003',
  '作者要求形成趋势才谈背驰，对一段相应趋势背驰只一次；面对背离背离再背离之问，他要求别把非背驰误当背驰，并说真背离后有转折。',
  '背驰|趋势|确认', 1, '同一段相应趋势，不等不同级别不能先后出现背驰；与107必须分级说明并列，北臣保留原文词形。', ['本课所指同一段相应趋势'], ambiguity='single_trend_event_vs_different_levels_and_unfinished_signals')
c(15, 'adjacent-force-comparison-consolidation-not-trend', '60-b010',
  '面对是否比较相邻面积及中间盘整的提问，作者答是、可目测，并说盘整不是趋势、不计作趋势段。',
  '缠中说禅趋势力度|背驰|盘整', 1, '紧邻问题有两个子问，短答未给任意跨越盘整的完整选择算法；不凭一个是自动许可任意不相邻比较。', ['PDF60中间体两个子问及作者短答'], ambiguity='compound_question_short_yes_does_not_fully_define_comparison_selection')
c(15, 'buy-first-if-skilled-second-for-unfamiliar', '60-b022',
  '解释为何一般买第二点时，作者说熟悉背弛者第一类买点更好，不熟悉者第二类较好，可减少下跌中误判背弛买入风险。',
  '均线系统第一买点|均线系统第二买点|操作熟练程度|市场风险', 1, '这是对12课偏好的明确能力限定，不把第二点一律优于第一点，也不声称风险完全消除。', ['对前课两均线买点偏好的追问'])
c(15, 'first-entanglement-exclusion-only-trend-search', '60-b023 61-b000 61-b001',
  '作者说第一次缠绕不是最后一次的说法可用于各周期，但只针对趋势中寻找背驰，因为趋势须两次以上缠绕；盘整一次缠绕后也可有买点，他一般不赞成参与，周/月盘整另论。',
  '均线系统|周期图走势分类|背驰|盘整|均线系统第一买点', 1, '跨页保留只针对趋势和盘整例外，不能继续把12课首次非最后断言用于所有形态；两次以上按原词不硬补整数解释。', ['本课均线趋势中寻背驰'], exceptions=['盘整可一次缠绕后有买点','作者允许另看周线或月线盘整'])
c(15, 'female-later-kisses-not-all-second-buy', '61-b002',
  '作者只把女上位第一次缠绕后定义为第二类买点；他说除最后一次外其他缠绕后买可盈利，但仍只建议底部买以控风险。',
  '均线系统第二买点|均线体位|市场风险', 1, '其他缠绕盈利为作者强措辞未统计，不把每次回调都定义成第二点；底部此处未给后来108课完整定义。', ['本课女上位均线系统'], ambiguity='author_later_kiss_profit_wording_not_guarantee')
c(15, 'five-ten-ex-rights-daily-vs-week-month', '61-b007',
  '对除权分析，作者说若用5/10线，除权对日线及以下操作影响不大可不用复权，周/月线则可以复权。',
  '数据源一致性|周期K线图|均线系统', 2, '这是本课5/10系统和图周期的选择说明，不普遍证明除权对任意指标毫无影响，也不覆盖14课价格比较口径。', ['本课5/10均线系统'])
c(15, 'beichen-rebound-five-line-lower-chart', '61-b011',
  '作者未给北辰持仓者具体出场价，而说这类反抽5日线重要，短线可看1分钟图。',
  '均线|操作级别|反弹|操作策略', 2, '读者跌停买入和此前强反抽说法仅提问语境，不当作者新确认交易；不自动把触5日线当充分卖点。', ['2006年12月11日北辰反抽类型问答'])
c(15, 'beichen-waning-strength-before-average-cross', '61-b012 62-b000',
  '作者说北辰30分钟上涨中已有力度问题应先走，MACD三波红柱一次比一次低为其所举背驰信号，不需等均线下穿后才反应。',
  'MACD|MACD柱波|背驰|均线系统|确认', 1, '这是相应上涨和级别中的波对波，不是任意三根日柱递减即充分确认所有背驰。', ['2006年12月11日北辰30分钟相应上涨'], figs=((61, 1),))
c(15, 'small-short-buy-falling-not-full-low-period', '62-b005 62-b006',
  '对小资金短线追涨焦虑，作者说可用1/5分钟图在下跌时找第一类买点，以600177约6.3举例；但不建议全仓按1/5分钟进出，大资金无效，可作短差工具。',
  '均线系统第一买点|操作级别|资金管理|仓位', 1, '小资金/大波动及不全仓限制并存，6.3不按图6.26替换，不把作者当时例子作当前荐股。', ['2006年12月11日600177短线问题'], figs=((62, 1),))
c(15, 'macd-patch-to-patch-with-current-shrinking-alert', '63-b000 63-b001',
  '作者说MACD是辅助，比较应片与片；当前红/绿柱片不能再伸长而开始缩短时须严重关注，不必等颜色转换，但还要配合其他条件。',
  'MACD|MACD柱波|背驰|确认', 1, '关注信号不等完整确认背驰；片与片和当前片内部缩短用途不同，不能只选其一。')
c(15, 'growing-current-patch-not-divergence-confirmed', '63-b005 64-b003',
  '对指数价新高而MACD未同高的提问，作者说当前红柱仍较昨日长、该片尚在形成，待缩短且不能超过前波最后位置才有危险信号。',
  'MACD|MACD柱波|确认|背驰', 1, '同日两读者两答复各保留时间，不把未完成片与已结束波直接等量比较；仍是危险信号非无条件卖点。')
c(15, 'patch-peak-three-day-turn-not-price-turn', '64-b006',
  '作者把红绿柱一波描述为先伸长再缩短：今日短于昨日且昨日长于前日，才显示柱波峰值转折；今日仍更长则峰转折尚未出现。',
  'MACD柱波|MACD|确认', 1, '此答复原页无单独日期，已清空旧继承时间；柱波转折不是股价趋势已转，等长边界未给，不补非严格不等式。', ['PDF64舞者无时间追问后的作者答复'])
c(15, 'histogram-divergence-peak-compare-with-lines', '64-b010 65-b000 65-b001',
  '作者纠正价新高且柱低于昨日就直接背驰的理解：先确认柱波转折，再以该波峰值低于前波峰值判断柱子上的背驰；单看柱仍不足，还看DEA/DIFF，通道式尤其须看。',
  'MACD柱波|MACD|背驰|确认', 1, '跨页读完上一波峰对比与黄白线条件，不把柱波峰直接当价格顶；原文黄DEA白DIFF颜色仅本例。', ['2006年12月12日柱波背驰问答及通道式限制'], figs=((64, 1),))
c(15, '600900-thirty-already-day-not-zero-retest', '65-b004 66-b000',
  '对600900作者说30分钟背离早已发生、日线没有；通常较有效的MACD情形是黄白线回零轴附近再上、价新高而线和柱均不新高。',
  'MACD|背驰|操作级别|确认', 1, '一般最有效不是所有标准的无例外等价算法，30分钟与日线状态分开，不凭任一日柱缩短替代线柱/回轴组合。', ['2006年12月12日600900分周期问答'], figs=((65, 1), (65, 2)))
c(15, '000932-box-entry-not-upgrade-to-day-hold', '66-b006',
  '作者纠正000932持有者：按日/周买点持到日/周卖点须最初就在相应一二买介入；该15分钟买入不是标准一买而是箱型操作，应按箱顶不破退出、回落再买，不押一定突破。',
  '操作级别|均线系统第一买点|均线系统第二买点|仓位|操作策略', 1, '不得事后把原15分钟箱型买入升级成日线中线计划；读者价3.92仅上下文不当作者核实成本。', ['2006年12月12日000932箱型买入问题'], figs=((66, 1),))
c(15, 'ultrashort-versus-midterm-position-t1', '63-b008',
  '作者区分超短每天进出者要及时找到可买对象以应T+1和资金利用率，与牛市中线原在相应日/周买点介入者可做短差降成本、等日周一卖再退出，特别小资金另论。',
  'T+1|仓位|操作级别|资金管理', 1, '结合后文000932答复保留原入场日/周买点前提，不能将任何短线套仓事后改中线或所有人必须持续满仓。', ['作者所论牛市阶段与各自原操作周期'], exceptions=['作者另提资金特别少的情形'])
c(15, 'spare-funds-no-withdrawal-pressure', '63-b011',
  '针对把买房钱压入股票，作者要求市场资金应为闲钱、可放不动且无提走压力，以利心态平稳。',
  '资金管理|赌徒心理|市场心理', 1, '忠告的原始对象/身份保留，不把无提走压力解释为价格亏损不会发生。')
c(15, 'small-funds-avoid-long-consolidation-case', '63-b012 63-b013',
  '在000768答复中作者说不了解入场价和操作风格，提醒小资金不宜耗太久盘整，应选择难度较小方向与相应一二买；该股三角尾声后可能洗盘或再上一波是条件化看法。',
  '资金管理|盘整|操作熟练程度|三角形整理', 2, '不把读者买房钱价位当已核事实，庄家洗盘路径只是作者设想，不确认匿名资金动机。', ['2006年12月12日000768问答及未知入场信息'])
c(15, 'macd-lines-side-and-wave-role', '66-b009 67-b000',
  '作者说用均线判背驰技巧要求高，MACD较好把握但只看柱波仍初步；还须看黄白线，零轴上/下分别为该指标观察的多头/空头语境。',
  'MACD|MACD柱波|背驰|操作熟练程度', 1, '线分处零轴两侧的过渡细则本文未给；不把MACD多空语境自动等全级别走势类型。')
c(15, 'macd-law-first-below-second-first-retest', '67-b001',
  '作者在此命名MACD定律，称第一类买点在零轴下背驰形成，第二类在首次上零轴后回抽确认形成，卖点反向，并要求看一大段而非太零碎。',
  '缠中说禅MACD定律|MACD|均线系统第一买点|均线系统第二买点', 1, '原文写缠中说缠，标准名称按作者身份整理；这是一套早期辅助指标表述，不能单凭过轴或回抽就当完整买点，也不绕开本课同向趋势条件。', ['本课MACD辅助与相应大段走势'], ambiguity='early_macd_law_vs_complete_later_buy_point_conditions')
c(15, '038004-risk-warning-homework-not-recommendation', '67-b003 67-b004',
  '作者以038004作MACD作业例，明确称该认沽风险极大、最终要变废纸且买点早过，只为上课，要求不要买。',
  '权证|MACD|市场风险|认沽权证', 2, '正文称认沽，概念不转认购；这是历史教学风险边界，不替用户执行作业中的买卖或证明账户收益。', ['2006年12月12日038004教学说明'])
c(15, '038004-author-lots-zero-cost-not-audit', '67-b005',
  '作者自述038004在10月23至25日建仓、11月8日减半、60天线附近回补，12月6/7日加首次仓位一半，12日按5分钟背弛卖大部使余仓成本为0。',
  '权证|仓位|成本|操作级别', 3, '只记录作者交易回顾，未核账户/费用；成本为0和立不败之地不等余仓市值无风险、清算义务消失或本项目已验证零损失。', ['作者该038004历史操作自述'], figs=((67, 1),), ambiguity='author_zero_cost_account_story_not_independently_verified')
c(15, 'triangle-price-shape-not-kiss-count', '68-b006',
  '作者说038004三角判别直接看图形而非均线吻，并以11月8日至12月7日三角末段与时间周期点共同解释加仓。',
  '三角形整理|均线系统|确认|操作策略', 1, '时间周期点未给可推广计算式；图上21/34/33T等标注不都当作者正文已明说。', ['2006年12月13日038004三角形问题'], figs=((69, 1),))
c(15, 'second-buy-not-must-wet-kiss', '68-b009 69-b000',
  '作者回答第二买点前缠绕不一定湿吻，快速图可无湿吻，并举038004日图以三角构造第二点。',
  '均线系统第二买点|湿吻|三角形整理', 1, '跨页完整答复，作者还说不湿吻基础往往令人怀疑，不删风险语气；不把三角形自动当充分二买。', ['本课均线第二买点/038004示例'])
c(15, 'gap-types-not-all-fill', '69-b003',
  '作者说缺口不补显示强势，突破或岛型反转缺口可不补；对肯定要补的类别，原文写“就是盘整中的，已经上涨最后的衰竭性缺口”。',
  '缺口|盘整|确认', 2, '保留原页“已经”词形与逗号范围，不自行纠为“以及”并确定两个独立分类；原提问000400未补不等错误。肯定补/不补为作者经验强措辞，无期限/样本，不作项目必然定律。', ['2006年12月13日缺口类型答复'], ambiguity='gap_fill_absolute_wording_and_punctuation_scope')
c(15, '000928-platform-not-triangle-week250', '70-b002',
  '作者否定000928为三角，称典型平台式调整，认为周线尚可但250周线支撑不能有效跌破。',
  '平台式调整|三角形整理|均线|确认', 1, '平台式调整不因字形相似就同16课顺势平台别名；此为该股历史形态，250周线是该例条件。', ['2006年12月13日000928日/周图问题'], figs=((69, 2), (70, 1)))

c(16, 'same-level-default-not-chart-upgrade', '70-b004',
  '作者说图走势由涨跌盘整组合，上涨与下跌构趋势；30分钟上涨在日线可只是一段盘整或下跌反弹，未特别声明时本课前后均按同级别讨论。',
  '周期图走势分类|操作级别|趋势|盘整', 1, '同级别默认与不同图可不同状态须保留；不把本课初步图框架无条件等后期严格定义。')
c(16, 'trap-style-two-combinations', '70-b005 70-b006',
  '第16课将上涨+下跌、下跌+上涨两组合称陷阱式。',
  '陷阱式走势|周期图走势分类', 1, '同级别基本走势的组合，不凭名称断言有某个操盘者蓄意设陷阱。', ['本课同级别走势组合'])
c(16, 'reversal-style-two-combinations', '70-b007',
  '第16课将上涨+盘整+下跌、下跌+盘整+上涨两组合称反转式。',
  '反转式走势|周期图走势分类|盘整', 1, '中间盘整不能删掉，不以未完片段预认整个组合已完成。', ['本课同级别走势组合'])
c(16, 'continuation-style-two-combinations', '70-b008',
  '第16课将上涨+盘整+上涨、下跌+盘整+下跌两组合称中继式。',
  '中继式走势|周期图走势分类|盘整', 1, '两段同方向不等无需比较力度或第三段必延续；示意图仅导航不证明统计概率。', ['本课同级别走势组合'], figs=((71, 1),))
c(16, 'long-side-value-and-two-down-entry-risks', '71-b000',
  '作者从多头列有买入价值的三组合为跌+涨、跌+盘+涨、涨+盘+涨；下跌中介入仍有跌势未尽、虽尽却盘整后再跌两风险。',
  '周期图走势分类|下跌+上涨买卖法|市场风险', 1, '组合数量不是概率，作者比较少一种坏情形不自动证明胜率；只针对本课多头视角。', ['第16课同级别组合及多头方向'])
c(16, 'first-buy-then-reduce-consolidation-general', '71-b001',
  '作者用背驰一买应对跌势未尽风险；买后若盘整先减仓应对后跌及耗时，保留部分是因盘整后可涨可跌，未来再谈如何决定减仓或动态建仓。',
  '下跌+上涨买卖法|均线系统第一买点|动态建仓|仓位|盘整', 1, '这是引出专门策略前的一般讨论，不能同后段“不参与盘整即全部退出”的特定规则混写；未给盘整后涨跌预测成品算法。', ['第16课一般风险分析及中小资金语境'])
c(16, 'large-nonmarketmaker-entry-only-one-style-author', '71-b001',
  '作者在此称，不想坐庄的大资金安全建仓在六组合中只适用于下跌+盘整+上涨，坐庄建仓另有方法。',
  '动态建仓|主力资金|周期图走势分类', 3, '是作者安全/唯一措辞，未作普遍市场实证；未来建仓方法未在本段具体给出，不据此实现操纵策略。', ['本课不想坐庄的大资金与所列六组合'], ambiguity='author_unique_safe_accumulation_claim_not_empirical_guarantee')
c(16, 'down-up-strategy-refuses-consolidation', '71-b002',
  '作者另设计下跌+上涨买卖法：一买介入后，一旦出现盘整，无论后来怎样都退出，只参与跌+涨这一组合，称适合不大资金。',
  '下跌+上涨买卖法|均线系统第一买点|盘整|操作策略', 1, '这是选定策略主动排除盘整，不能扩成所有投资方法必须退出所有盘整；原最有效没有比较样本。', ['选择本课下跌+上涨方法','中小资金及相应同级别图'])
c(16, 'exclude-prior-up-down-not-no-profit', '71-b003',
  '对该方法，若买点前是上涨+下跌，则后续涨构成高一级别盘整，策略不参与；作者明确不考虑不意味着不能盈利，而是另归盘整操作。',
  '下跌+上涨买卖法|盘整|操作级别|确认', 1, '策略筛选与机会不存在分开，不把高一级别盘整无条件套所有未完成片段。', ['本课同级别基本段已可识别','专门拒绝盘整的方法'])
c(16, 'break-consolidation-and-recursive-filter', '71-b004 72-b000',
  '该方法先要前段盘整+下跌，且下跌须跌破前盘整否则仍在盘整；再排除上涨+盘整+下跌这种高一级别盘整后，剩下前史下跌+盘整+下跌。',
  '下跌+上涨买卖法|周期图走势分类|盘整|确认', 1, '跨页条件完整；仅本课所取分解与过滤论证，不把任意三段形似图自动判定一买。', ['第16课该策略的同级别分解'])
c(16, 'entry-second-down-exit-new-consolidation', '72-b001',
  '下跌+上涨方法标准程序为：只选下跌+盘整+下跌，第二段下跌出现一买才介入，介入后一旦盘整就退出；若不盘整，作者说至少回到前面盘整区域并可能成黑马。',
  '下跌+上涨买卖法|均线系统第一买点|操作级别|确认', 1, '三步骤与第二段一买缺一不可；不盘整回升和大黑马是作者本框架推断，不能无样本认证为所有市场保证。', ['本课已识别的同级别下跌+盘整+下跌','选择不参与盘整的方法'])
c(16, 'profit-and-half-risk-author-assertions', '72-b001',
  '作者断言该方法可用低一级别一卖退出而不亏、要盈利，并说盘整后有一半可能下跌，所以中小资金无需参与。',
  '下跌+上涨买卖法|均线系统第一卖点|市场风险', 3, '一半是作者原话而非由两种结果自动得50%；没有费用/流动性/T+1可执行证明，不将肯定盈利作项目保证。', ['本课该特定方法与低一级别退出设定'], ambiguity='author_profit_guarantee_and_half_probability_not_independently_verified')
c(16, 'chihong-date-sequence-example', '72-b002',
  '作者以驰宏日图举例：2004年6月2日至9月10日跌，至2005年3月14日盘，至7月27日再跌，一买在第二跌7月27日；后回原盘整区，12月8日回调出现所论二买。',
  '下跌+上涨买卖法|均线系统第一买点|均线系统第二买点|周期K线图', 2, '只作该历史样本，图上另加10/25中枢解释未核；不能据2004/8/23局部走势误说日图前段已有同层跌盘跌。', ['第16课驰宏日线示例'], figs=((72, 1),))
c(16, 'reverse-sell-second-up-first-sell', '73-b000',
  '该方法反向选卖点：前史上涨+盘整+上涨，第二段升势出现第一类卖点应退出，后面可能成上涨+下跌。',
  '下跌+上涨买卖法|均线系统第一卖点|操作策略', 1, '可能成下跌而非卖后任意时间必大跌；前史和第二段的条件不得删。', ['第16课同级别反向卖出方法'])
c(16, 'beichen-thirty-minute-two-up-segments', '73-b001',
  '北辰30分钟例中，作者列11月7日10:30至22日10:00上涨，至30日11:00盘整，再至12月7日10:00上涨；第二升三波红柱递矮配一卖，说明反向退出。',
  '下跌+上涨买卖法|MACD柱波|均线系统第一卖点|操作级别', 1, '这些时间是作者原文，图加175(T)/21天不证明时间之窗算法；MACD三波不能脱离走势与级别单项套用。', ['2006年12月14日对北辰30分钟例的回顾'], figs=((73, 1),))
c(16, 'half-million-three-stocks-return-rhetoric', '73-b006',
  '对约50万资金分散还是集中的提问，作者回答最多不超3只，可学本法用30分钟或日图，并自称年300%都算差。',
  '资金管理|仓位|下跌+上涨买卖法', 3, '3只限该约50万案例；300%是作者未实证的收益修辞，不作目标承诺或当前产品推荐。', ['2006年12月14日约50万资金问答'], ambiguity='author_300_percent_return_claim_not_project_evidence')
c(16, 'chihong-daily-one-down-thirty-three-parts', '74-b002',
  '作者对驰宏2004年6/2至9/10的追问说，日图并非跌+盘+跌而只是一跌，30分钟却可见跌+盘+跌，故读者对也不对取决图级别。',
  '周期图走势分类|下跌+上涨买卖法|操作级别', 1, '保留两周期不同分解，不把读者所给8/23日一买日期当作者已逐项认可。')
c(16, 'bull-phase-positions-method-not-universal-full', '74-b005 74-b006',
  '对当时牛市轻仓焦虑，作者要求将频繁变仓效果与一直持成分股比较，回笼资金找符合30分钟/日图要求者，或长持再短差降成本。',
  '仓位|资金管理|缠中说禅短差程序|操作级别', 2, '限定2006年当时作者牛市判断，不泛化所有环境必须满仓；读者成绩差是自述，比较收益未独立核验。', ['2006年12月14日该牛市阶段持仓问答'])
c(16, 'platform-exception-initial-definition-not-strict', '74-b010',
  '作者解释驰宏的特殊盘整为最弱的顺势平台，并明确尚未讲价值中枢，当前趋势/盘整通用定义不完全严格，先记这个例外，严格定义以后讲。',
  '顺势平台|周期图走势分类|价值中枢|盘整', 1, '这是作者对早期定义的明确限定；价值中枢只为本段将来术语，不自动同宏观估值中枢合并；后课走势中枢定义另以原文取证。', ['第16课对前述高低点定义与驰宏例的答复'])
c(16, 'same-chart-two-same-direction-trends-premise', '74-b013 74-b014',
  '作者重申离开级别无所谓趋势；背驰比较前后趋势，同一级别图存在两段同方向趋势是出现背驰的前提。',
  '背驰|趋势|操作级别|周期图走势分类', 1, '同级、两段、同向是联合前提；不凭任意价格双高低或均线单交叉断言已满足。')
c(16, 'visible-extrema-or-only-a-segment', '74-b015 75-b000 75-b001',
  '作者要求趋势/盘整须有该图明显高低点，无明显高低只构成其中一段；在盘整中照搬趋势一买会出问题。',
  '高低点|周期图走势分类|背驰|均线系统第一买点', 1, '跨页完整一段/整个走势的区别；与后文24盘整背驰命名并列，不据这句话禁止所有盘整短差。')
c(16, 'level-as-filter-channel-small-frame-trend', '75-b006 75-b007',
  '作者把级别比作过滤器：日线窄通道虽有微小高低，按日线须过滤、只算趋势一段；在5/30分钟图却可显现完整趋势基本特征。',
  '周期图走势分类|高低点|操作级别|趋势', 1, '图上看不见有意义极值不是物理没有极值；过滤不等以后严格级别都固定由K线周期直接换算。')
c(16, 'completion-principle-any-level-attribution', '75-b008',
  '作者在第16课末提出，对任何级别图形，趋势与盘整都要完成。',
  '走势终完美|完成|周期图走势分类|走势类型', 1, '记录该早期原理来源，光速不变的比喻不是形式证明；不能由要完成推断当下已完成或预测完成时刻。')

keep('60-b022', 'upper-l012-c-stage-prefer-second-buy-first-sell-asymmetry', '15课对12课买二偏好明确补充：熟悉背弛者买一更好，不熟者买二较稳，不全局改写为永远偏二。')
keep('60-b023 61-b000 61-b001', 'upper-l011-c-stage-wet-kiss-two-turn-paths-first-exception upper-l012-c-stage-bear-last-entanglement-divergent-drop-entry', '首次非最后是趋势寻背驰的范围，盘整一次也可买；对应早期绝对措辞提供作者明确限定。')
keep('59-b001 74-b014 75-b001', 'upper-l024-c-stage-divergence-default-trend-consolidation-analogy upper-l024-c-stage-consolidation-short-difference-scope', '15/16趋势背驰原话与24后来盘整背驰命名区分；不按日期覆盖一方，也不误抹盘整操作方法。')
keep('65-b001 66-b000', 'upper-l023-c-stage-zero-axis-nearby-not-strict-cross upper-l024-c-stage-standard-macd-area-completion-test', '零轴附近/线柱组合有后续更细条件；15早期均线面积与24MACD柱面积分开，不据线柱一项替代整体。')
keep('63-b008 66-b006', 'upper-l014-c-stage-weekly-hold-large-capital-small-use-daily upper-l014-c-stage-short-difference-program-reduce-rebuy-order', '15明确原入场须日周一二买，箱型15分入不能事后升格；保持大资金/短差与原周期。')
keep('74-b010 75-b008', 'upper-l017-trend-definition upper-l017-center-definition', '16承认高低点定义暂不严格并提出走势要完成，17随后具体中枢框架以其原文另查，不同定义入口不裸合并。')

issue('early-high-low-definition-platform-and-equality', '58-b011 58-b012 58-b013 70-b004 74-b010',
      '早期三类高低点定义没有列相等边界，作者16课又明确顺势平台例外/暂不严格；图周期与后期中枢级别不能等式换算。',
      '保留早期定义及作者自己的限定，不补等高等低算法，不将价值中枢与宏观估值中枢自动同义。', True)
issue('no-trend-scope-first-kiss-and-consolidation', '59-b001 60-b023 61-b001 74-b014 75-b001',
      '无趋势无背驰/首次非最后针对趋势，盘整一次也可有买点；后24课另有盘整背驰命名。',
      '保留同级两段同向前提、作者盘整例外与后期术语，不把原话推广到所有类似力度比较或关闭盘整短差。', True)
issue('ma-force-area-average-and-instant-boundaries', '59-b002 59-b003 59-b004',
      '均线间趋势力度面积与平均面积/时间、MACD柱面积不同；吻边界、瞬时延伸长度、尺度和风险没有完整可执行算法。',
      '只保存原定义和确认/预示区别，不从图形自行补积分、峰值或零延迟收益程序。', True)
issue('macd-histogram-peaks-lines-and-law', '63-b000 63-b005 64-b006 64-b010 65-b001 66-b000 67-b001',
      '片与片比较、片内峰转、柱背驰、线柱与回轴组合及早期MACD定律不同；一根缩短不够，零轴混合状态/等长边界未给细则。',
      '不把柱波转折等股价转折，不补冲突优先级、参数或一次过轴就充分买点。', True)
issue('exit-profit-half-probability-return-and-time', '71-b001 71-b002 72-b001 73-b006',
      '先减仓的一般讨论与拒绝盘整即退出的特定方法不同；肯定盈利、一半后跌、年300%及最有效无实证。',
      '保留策略条件和作者措辞，不从两种结果推出等概率，不把未验证执行成本/T+1约束消除。', True)
issue('warrant-trades-zero-cost-gap-cycle', '67-b004 67-b005 68-b006 68-b009 69-b003 73-b001',
      '038004危/废纸/不买边界、成本0交易自述、时间周期点和缺口肯定补/不补皆历史语境；图注神奇数字与175T未核。',
      '不认证账户回报、零风险、固定时间周期或缺口永久定律；自述不替用户执行买卖。')
issue('reader-headers-and-truncated-year', '64-b004 64-b005 64-b006 74-b007 74-b008',
      '64舞者无时间追问曾当作者并继承19:59，现分角色/清日期；74读者006年头已核日期null继续保留。',
      '原文/坐标不改，不补未记载时间年份；作者答复与问题引用分开。')
issue('figure-origin-and-extra-annotations', '61-b012 63-b000 65-b004 67-b005 68-b001 68-b006 70-b002 72-b002 73-b001',
      '14图10含文后K/4原发未核，图上未来行情/21、34/175T及中枢后加说明不能全归作者。',
      '所有整图和示意图已看，文字独立支持；038004/580991作业不是现代买入建议，不按图补日期/算法。')

note('58-b008', 'author-metaphor-and-self-description', '论语的庄家/散户位次、逸闻及自夸阻击经验已读。', '不据自夸验证身份/账户或生成操纵方案，市场分类另抽。')
note('59-b008 59-b009 60-b000 60-b001 60-b017', 'historical-market-and-metaphor-context',
     '12月震荡短线机会、银行地产为旗帜的牛市判断，以及以幻制幻和满仓无法应对的评论已读。', '历史牛市/收益/预见自评未外核，读者北辰引线说不转作者因果证明。')
note('61-b003 62-b001 66-b008 68-b003', 'practice-and-future-detail-context', '习惯劝学、未来指标/图周期细节和作业/看回复提醒完整已读。', '预告不等知识细节已在本段给出；命令式原文不改变当前工具权限。')
note('67-b003 68-b001', 'homework-and-answer-boundary', '038004及580991建仓作业已读，580991本段没有完整正式答案。', '不把作业问题自行猜测为作者确认，后期来源需单独取证，危险警示保留。')
note('73-b002 74-b012 75-b002', 'method-practice-and-unanswered-question',
     '方法熟练与跟帖提醒、重点句引言及某级盘整低点如何形成的思考题已读。', '题目预告定律不当现有作者答案，17等后续来源另查，不自行补推论为explicit。')

relations = {
    'upper-l015-c-stage-trend-force-between-kisses-area': [('缠中说禅趋势力度', '均线系统', 'requires'), ('缠中说禅趋势力度', '背驰', 'related')],
    'upper-l015-c-stage-average-force-area-divided-by-time': [('缠中说禅趋势平均力度', '缠中说禅趋势力度', 'related')],
    'upper-l015-c-stage-macd-auxiliary-not-force-definition': [('MACD', '缠中说禅趋势力度', 'qualifies')],
    'upper-l015-c-stage-patch-peak-three-day-turn-not-price-turn': [('MACD柱波', 'MACD', 'related')],
    'upper-l015-c-stage-macd-law-first-below-second-first-retest': [('缠中说禅MACD定律', '均线系统第一买点', 'related'), ('缠中说禅MACD定律', '均线系统第二买点', 'related')],
    'upper-l015-c-stage-second-buy-not-must-wet-kiss': [('均线系统第二买点', '湿吻', 'qualifies')],
    'upper-l016-c-stage-trap-style-two-combinations': [('陷阱式走势', '周期图走势分类', 'related')],
    'upper-l016-c-stage-reversal-style-two-combinations': [('反转式走势', '周期图走势分类', 'related')],
    'upper-l016-c-stage-continuation-style-two-combinations': [('中继式走势', '周期图走势分类', 'related')],
    'upper-l016-c-stage-entry-second-down-exit-new-consolidation': [('下跌+上涨买卖法', '均线系统第一买点', 'requires')],
    'upper-l016-c-stage-platform-exception-initial-definition-not-strict': [('顺势平台', '周期图走势分类', 'qualifies')],
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
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], '读者一根柱即背驰、15分钟入改日线、年收益/持仓自述不作作者证据。'
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
        'note': '早期高低点/顺势平台例外与后期中枢定义并列，均线面积/平均力度/MACD柱波分开，确认/预示、两段同向/盘整背驰和策略范围保留。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True, reviewer=REVIEWER, visual_review_note=f['note'],
             figure_source_review='14图全部查看；10文后行情图4未核原发，包括六组合示意，不以颜色/图注单独判作者或收益。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 194 and Counter(x['lesson_number'] for x in ledger) == {15: 145, 16: 49}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [15, 16], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(58, 76)), 'figure_objects_viewed': 14, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '15至16课194段18页14图同模型四轮；3源段身份/时间修正、早期分类/顺势平台限制、力度定义/柱波/均线系统及不盘整策略保留，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


