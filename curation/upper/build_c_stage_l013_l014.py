"""Materialize the main agent's four-pass reading of lessons13-14.

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
BASE = 'c_stage_l013_l014'
REVIEWER = 'Codex 主代理 / 阶段C上册13至14课同模型四轮复核'
SOURCE_SHA = 'f47aab4e87969428c7bfb56b6430032c353d74b7e12a9d5fa7d3e3f2ac1a02d6'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id IN ('lesson-013','lesson-014') ORDER BY pdf_page,block_index,id")}
assert len(passages) == 120
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 44 AND 57 ORDER BY pdf_page,id', (DOC,))]
assert len(figures) == 18
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
    pending.append({'id': 'upper-l013-l014-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})


c(13, 'passive-entrapment-blind-entry', '43-b010 44-b000',
  '作者把介入时不知为何介入、在盲目状态下被套称为被动带套，并批评只按亏损多少机械止蚀的做法。',
  '被动带套|操作策略|市场风险', 1, '跨页读完定义；这是作者框架中对介入依据的要求，不把几乎所有投资者如此或固定止损必不能成功当独立统计。')
c(13, 'exit-when-structure-no-longer-tradable-not-pnl', '44-b001',
  '作者把其所说止蚀限定为走势由能做变为不能做，退出依据是当下走势而非盈亏金额；即使已大幅盈利，也可能应退出。',
  '操作策略|当下|卖点|被动带套', 1, '能做标准须对应所选程序，本段未给通用价格阈值；不把不看盈亏改成不设任何风险约束或无条件死扛。')
c(13, 'active-entrapment-two-meanings-and-protection', '44-b002',
  '主动带套有两层意思：特别大资金介入难一次完成；更重要的是任何介入须有防护，一旦走势变不能做就从买入程序退出，触发依据与盈亏无关。',
  '主动带套|仓位|操作策略|市场风险', 1, '不是只指容忍亏损或无条件补仓；本节主动带套与105主动买套的分批降成本语境保留关联线索而不直接做别名。')
c(13, 'average-first-entry-another-bear-kiss-invalid', '44-b003',
  '对上一课均线系统第一买点，若上涨时又出现男上位缠绕，说明原以为最后一次的缠绕并非最后、程序判断失效，作者要求退出，即使通常有盈利或之后可能转女上位再涨。',
  '均线系统第一买点|均线体位|主动带套|确认', 1, '一般盈利非保证；未来可涨不能成为不退出的理由，若以后满足第二买点可再介入，不把任何价格回落等同这一失效信号。', ['选择前课均线系统第一买点方案','随后仍出现男上位缠绕'])
c(13, 'average-second-entry-break-old-bear-low-exit', '44-b004',
  '对均线系统第二买点，若该缠绕跌破前面男上位最低位，作者认为程序有问题，应在反弹中出清；后续仍可能上涨，也不能因此硬扛，任何操作都非百分百准确。',
  '均线系统第二买点|均线体位|主动带套|市场风险', 1, '参考前面男上位最低位，不是误用任意近低或8/7买点自身；反弹一般存在不等保证必等到有利反弹。', ['前课均线系统第二买点的该次缠绕','跌破前面男上位最低位'])
c(13, 'program-strength-ninety-author-estimate', '44-b005',
  '作者强调长期操作与合适程序，并说买入程序成功率随市场强弱变化：强市自称基本90%以上，弱市低得多。',
  '操作策略|市场风险|操作熟练程度', 3, '90%是作者没有样本口径的估计，未作项目回测或跨程序普遍统计；港湾也有台风的比喻保留风险含义。', ['作者本节买入程序和市场强弱比较'], ambiguity='author_success_rate_not_independently_verified')
c(13, 'technical-program-subjudgment-not-stock-strength-ranker', '44-b006 45-b000',
  '均线等技术买卖程序只是综合判断的子判断，不能单凭同一程序解释或选出最有涨幅力度者，作者比其为海选，后面仍需筛选。',
  '技术分析|均线系统|独立系统|操作策略', 1, '跨页完整子判断；未把后续复赛/PK细节虚构成已给的排名算法，不能把单指标买点当选股全部依据。')
c(13, 'dec4-shanghai-shenzhen-divergence-risk', '45-b001 46-b003',
  '12月4日作者重复以沪深指数背离观察短线调整或至少震荡将至。',
  '指数走势背离|市场风险|确认', 2, '解盘与回复栏同一观点分别保留原时间/角色；沪深指数背离不等严格趋势背驰，不给未提供的阈值和概率。', ['2006年12月4日该沪深短线提示'])
c(13, 'no-sell-signal-no-speculative-switch', '45-b006 45-b007',
  '对因外出想换满仓股票的提问，作者要求养成完成整个操作的习惯：原股未出卖出信号就持有，不能用换后也许更好替代程序。',
  '持股|卖点|操作策略', 1, '限所选操作框架，事后换股更好也不证明先前无信号换仓正确；不是任何风险场景都禁止换股。', ['2006年12月4日600653/000822换000932的问答'])
c(13, 'absence-still-needs-position-followup', '45-b008',
  '作者说离开市场时仍须有人跟进或自己通过网络关照持仓，不能把股票放着无人管理。',
  '持股|操作策略|操作熟练程度', 2, '这是所述主动市场参与的管理习惯，不是授权本项目替用户交易或联系他人。')
c(13, 'half-position-warning-and-last-retest-not-guaranteed', '45-b011',
  '答撤出亏损及能否等反弹时，作者说熟悉走势者不必等真正破前低，称一般一半位置不该破；真破低后常有反抽作最后退出机会，再不走则只能杀跌。',
  '确认|市场风险|操作策略', 1, '一半的参照区间未在本答复明确，不补50%公式；一般反抽非必然保障，也未赞同读者所说牛市无需止损。', ['12月4日紧邻撤出亏损/等待反弹问题'], ambiguity='half_reference_not_defined_and_retest_not_guaranteed')
c(13, 'retail-segment-adjustments-not-final-target', '46-b001',
  '作者认为对散户关键是避开相应较大级别调整、分段操作以提高资金利用率，行情终点即使很高也可分很多段处理，最终点位预测意义不大。',
  '走势分解|操作级别|资金管理|走势预测', 1, '紧邻5000/一万点自述是历史远景非兑现事实，未将任意微小波动都当必须退出。')
c(13, 'tcl-cost-topup-specific-not-universal-lump', '46-b006',
  '在TCL既有套仓的具体答复中，作者主张该次补仓一次把成本降到某标准，并比较4.3与3.3元在来年解套的机会。',
  '仓位|成本|操作策略', 3, '这是特定提问的成本方案，不普遍否定大资金分批介入；明年/上半年机会为未验证历史预测，未给所需资金和仓位比例。', ['2006年12月4日TCL旧仓及该次已补仓问题'], ambiguity='case_lump_topup_vs_general_staged_entry_scope')
c(13, 'tcl-swing-added-lot-not-original-holding', '46-b007 46-b008',
  '作者给TCL另一方案：原套仓暂不动，在以后中线上涨高位卖本次补仓部分、再待中线调整回试年线补回；若短线能力足，可用补仓筹码反复差价，避免持续增加总仓位和资金。',
  '仓位|成本|操作熟练程度|均线|操作策略', 1, '只动补仓部分是该案例原则，不导出所有原底仓在结构失效时仍永不卖；低于4元及很快解套是估计非保证。', ['2006年12月4日该TCL答复','短差分支需相应短线能力'], ambiguity='old_lot_retention_scope_vs_general_invalidated_program_exit')
c(13, '600058-weekly-second-buy-author-not-reader-proof', '47-b002',
  '作者在600058答复中确认周线11月17日那周为典型第二类买点，称当时介入较好。',
  '均线系统第二买点|周期K线图|确认', 2, '本节承接均线买入程序；读者选股自述与图中4/7第一点及个人理解不当作者逐项认证；不把原“第二类”自动等后课严格定义。', ['2006年12月4日600058均线程序问答'], figs=((46, 1),))

c(14, 'entanglement-includes-all-three-kisses', '47-b004',
  '第14课明确均线系统所称缠绕包括飞吻、唇吻、湿吻：湿吻最明显，飞吻与唇吻也作为特殊例子。',
  '均线系统|飞吻|唇吻|湿吻', 1, '不能把本课每次缠绕都限定为交叉的湿吻；湿吻比例最大、周月唇吻也多是作者定性经验，无统计样本。')
c(14, 'named-first-class-in-average-system', '47-b010',
  '在本课均线操作系统中，作者把男上位最后一吻后背驰下跌形成的位置称为第一类买点。',
  '均线系统第一买点|均线体位|背驰|均线系统', 1, '保留原文明称第一类，但限定本课均线系统语境，不自动与后期中枢定义的同名类点合并。', ['第14课明确的均线操作系统'], ambiguity='early_named_class_point_vs_later_strict_center_definition')
c(14, 'named-second-class-in-average-system', '47-b011',
  '在本课均线操作系统中，作者把女上位第一吻后的下跌形成的位置称为第二类买点。',
  '均线系统第二买点|均线体位|均线系统', 1, '第一吻依前段包括三种吻，不删第一或改为任意回调；后期严格类点需另外查条件。', ['第14课明确的均线操作系统'])
c(14, 'weekly-maotai-three-kisses-first-not-enough', '47-b012',
  '茅台5/10周示例中，作者列2002年4月19日转男上位，7月9日那周首吻一般不构买点；2003年2月14日第二吻后未背驰，6月27日第三吻后才见背驰，9月26日那周完成所论第一买点。',
  '均线系统第一买点|均线体位|周期K线图|背驰', 1, '吻次数不充分，至少第二吻后还须背驰；7/9那周照原文，不据日历/图注改日期，价格复权未独立复算。', ['第14课茅台5/10周均线历史示例'], figs=((48, 1), (48, 2)))
c(14, 'macd-green-shrink-price-new-low-example', '47-b012',
  '作者在该茅台周线例子以价较前低而MACD绿柱较前段缩短说明背驰，并以绿柱缩短时股价仍创新低作为最简结束观察，定位到2003年9月26日那周。',
  'MACD|背驰|均线系统第一买点|确认', 1, '明确只据该系统示例，不把任意一根绿柱变短普遍等同严格背驰或保证最低价；前吻/级别/走势条件仍需一起看。', ['本课茅台周线男上位末吻后的相应下跌'])
c(14, 'weekly-second-buy-first-female-kiss', '47-b013',
  '作者说茅台周线首买后转女上位，至2004年6月4日那周首次吻后下跌形成所论周线第二买点；因周图调整不明显，要降到日线找位置。',
  '均线系统第二买点|均线体位|周期K线图|确认', 1, '没有明显周图下跌不等没有调整，也不强行在周线要求出现同一套一买背弛图形。', ['本课茅台周线首女上位吻及其对应日图'])
c(14, 'buy-point-law-corresponding-next-level', '47-b013 48-b000',
  '作者在均线系统讲解中命名缠中说禅买点定律：大级别第二类买点由次一级别相应走势的第一类买点构成，以周线二买对应日线一买举例，并称可把买点定位归到第一类。',
  '缠中说禅买点定律|均线系统第一买点|均线系统第二买点|周期K线图', 1, '跨页保留次一级别与相应走势，不跳任意多级或把两类概念取消合并；本段K线周期框架与后期递归中枢级别分别核对。自称专利不作登记证据。', ['本课均线系统与相应走势语境'], ambiguity='early_chart_horizon_law_vs_later_structural_level_scope')
c(14, 'daily-third-kiss-june18-corresponds-weekly-second', '48-b001 49-b000',
  '在2004年6月4日周吻对应日图，作者列4月29日、5月18日、6月1日三湿吻，前两次后跌未背驰，第三次后6月18日低点配绿柱缩短形成日一买，同时对应周二买。',
  '缠中说禅买点定律|均线系统第一买点|均线系统第二买点|MACD', 1, '相应日图走势完整跨页取证，不把周6/4与日6/18当两种矛盾触发日，也不由三次吻的次数直接判点。', ['第14课该周/日对应实例'], figs=((49, 1), (49, 2)))
c(14, 'corporate-action-lower-looking-price-not-new-low', '49-b000',
  '作者提醒该茅台日线买点后因除权可能看起来出现更低价，按他所论比较口径实际并非再创新低。',
  '价格精度|数据源一致性|均线系统第一买点|确认', 2, '保留除权/复权比较口径，但未独立取得除权表或重算；不将图间不同复权数值当成原文错误或新的低点。', ['第14课该2004年茅台日图比较'], ambiguity='corporate_action_price_series_not_independently_recomputed')
c(14, 'weekly-hold-large-capital-small-use-daily', '49-b001 50-b000',
  '作者说该周线两买点后周卖点当时未出，周线方案应持有；以50亿以上特别大资金与10亿以下一般资金作例，后者可用日线卖点回避大调整提高流动性。',
  '持股|操作级别|资金管理|缠中说禅短差程序', 1, '50亿/10亿是该例规模对照，未规定10至50亿唯一边界或所有人必须按同一周期；当时未出卖点不等以后永久不出。', ['本课茅台周线买入方案与资金规模比较'])
c(14, 'short-difference-program-reduce-rebuy-order', '50-b000 51-b001',
  '缠中说禅短差程序在本课为：大级别买点介入后，次级别第一类卖点出现可先减仓，之后次级别第一类买点出现再回补；周线入场以日线卖买作例。',
  '缠中说禅短差程序|均线系统第一买点|均线系统第一卖点|操作级别|仓位', 1, '先减后补及次级别条件不可倒置，减仓不必清仓；原文可先减仓非强制每次都做，资金不特别巨大且需熟练。', ['本课大级别介入后次级别短差程序','按资金和性格选择周期并有对应熟练度'])
c(14, 'daily-ninth-kiss-april8-red-no-new-high', '50-b001 51-b000',
  '周线2003年9月26日入场后，作者在日图数女上位九吻，前八无背驰，第九在2004年3月26日；4月8日价格高位而MACD红柱未同创新高，作为日线第一卖点。',
  '均线系统第一卖点|MACD|均线体位|缠中说禅短差程序', 1, '吻出现日与后续卖点日分开，前八与第九是本例计数，不成所有第九吻必卖定理；尚未独立重算指标参数。', ['本课茅台该日图示例'], figs=((50, 1), (50, 2)))
c(14, 'daily-sequence-dec13-no-sell-yet', '51-b000',
  '作者接列茅台日线6月18日买、10月27日卖、12月22日买、2005年4月26日卖、12月13日买，并说截至本课该日线买入后尚未有卖点，应按该周期持有。',
  '均线系统第一买点|均线系统第一卖点|持股|操作级别', 1, '本段先后默认跨2004至2005的图例语境，未逐次复算；与12课2006年8/7另一日一买及周期选择不自动统一，原文截至时间不能外推永久。', ['2006年12月5日本课对所示茅台日图回顾'], figs=((51, 1),), ambiguity='multiple_daily_examples_and_macd_parameter_scope_not_unified')
c(14, 'smaller-fund-daily-entry-thirty-exit', '51-b000 51-b001',
  '作者说小资金若最多以日线第一/第二买点介入，可再到30分钟等更小图找第一卖点做短差；操作级别要按资金与性格选并实际熟练。',
  '缠中说禅短差程序|操作级别|资金管理|操作熟练程度', 1, '这是周期示例而非严格级别固定换算；更细操作并非所有人必须，未交付自动交易程序。')
c(14, '600639-red-shrink-not-enough', '52-b011',
  '对600639红柱缩小是否已背驰的提问，作者回答没有，并说中线已进成交密集区，再涨后短线震荡洗盘正常。',
  'MACD|背驰|成交量|确认', 1, '否定来自紧邻作者答复，不能把读者红柱缩写成作者确认背驰；风险展望不等当天已经震荡。', ['2006年12月5日600639问答'], figs=((52, 1),))
c(14, 'maotai-aug7-not-break-prior-may26-low', '52-b015',
  '作者否定把茅台8月7日当作第二买点失效破位，称它是买点，日线前低在5月26日37元多，并未被破。',
  '均线系统第一买点|均线系统第二买点|确认', 1, '参照前面男上位低位而非任意局部低；正文37元多不改图37.68，不把读者引用规则作为另一作者证据。', ['2006年12月5日该茅台问答'], figs=((53, 1),))
c(14, 'macd-double-period-and-double-head-context', '53-b004',
  '答4月13日与4月26日卖点差异时，作者说自己MACD周期比普通长一倍；普通指标4月13日背驰构双头，一般到零轴后双次拉回，这次才构最终背弛。',
  'MACD|背驰|均线系统第一卖点|指标对比', 1, '只记长一倍，不从未知图面板自行补24/52/18或各参数倍数算法；一般回零轴双次拉回保留为本答复原话。', ['2006年12月5日茅台该卖点比较'], figs=((53, 2),), ambiguity='macd_doubled_period_parameters_not_explicitly_supplied')
c(14, '000530-entry-points-not-certify-accumulation', '54-b003',
  '对000530读者分析，作者说可以但最好用第一/二类点：日图最近一买9月26日、二买10月23日，之后入场须看30分钟图。',
  '均线系统第一买点|均线系统第二买点|操作级别|确认', 2, '本段可以不视逐项认证读者关于庄家已收足筹码的事实；后面看30分钟也不是无条件追高。', ['2006年12月5日000530均线方法问答'], figs=((54, 1),))
c(14, 'dec6-week-none-daily-double-head-not-finished', '55-b003',
  '12月6日作者说茅台周线不存在背驰，日线将演化MACD双头，要先跌近零轴、再上形成所论真正日背驰。',
  'MACD|背驰|操作级别|确认', 1, '周线否定与日线未来过程分开，不把读者价新高/指标变化直接确认为两周期已背驰；后文回抽零轴规则可跨课查证。', ['2006年12月6日该茅台周/日图问答'])
c(14, 'dec6-thirty-minute-sell-and-zero-rebuy', '55-b004',
  '在同一茅台答复中，作者另给小资金短线30分钟图12月1日13:30卖点、12月6日下午MACD回零轴可回补。',
  'MACD|操作级别|缠中说禅短差程序|资金管理', 1, '30分钟可短差不等周/日卖点已出，未把回零轴单项升级所有情境的充分一买信号；图标13:30回补未由正文单独给出。', ['2006年12月6日该茅台30分钟短差示例'], figs=((54, 2),))
c(14, 'divergence-no-promised-duration-amplitude', '55-b008',
  '作者答000503说背驰只表相应升势告一段落，不承诺调整时间或幅度；回补须看低一级别相应第一类买点。',
  '背驰|操作级别|缠中说禅短差程序|幅度', 1, '相应级别与不承诺大小时间保留；不能把再创新高当原背驰自动无效，也不导出任意背驰毫无最低结构反应。', ['2006年12月6日000503的30分钟卖后回补问答'])
c(14, '000503-thirty-sell-five-buy-case', '55-b008 55-b009',
  '作者用000503示例：12月1日10:30在30分钟背驰约9.7元卖，12月5日10:25在低一级别5分钟第一买点约9.2元回补，兼有差价及两天交易时间释放。',
  '缠中说禅短差程序|操作级别|均线系统第一买点|背驰', 2, '30分卖与5分回补按本答复单独记录，不强改成所有程序均为同一周期卖买；作者最高效自评非系统对照实验，费用/真实交易未核。', ['第14课000503具体短差回顾'], figs=((55, 1), (56, 1)))
c(14, '600050-equal-low-not-standard-first-buy', '56-b003',
  '对600050周线，作者说2005年10月21日与先前同为2.43、没有创新低，不属标准背驰，因而不是标准第一类买点。',
  '背驰|均线系统第一买点|确认|价格精度', 1, '回答否定标准入点，不是先承认标准点再说失败；不补容差/EPS、也不把等低排除套到所有盘整或类背驰入口。', ['2006年12月6日600050所比周线两个低位'], figs=((56, 2),))
c(14, '600050-daily-aug7-and-thirty-hold', '56-b004 57-b000',
  '作者另指600050在2006年8月7日2.19为标准日线一买，30分钟最近一买在11月14日13:30约2.68；截至12月6日该30分钟一卖未出，应按该图持有。',
  '均线系统第一买点|均线系统第一卖点|持股|操作级别', 1, '日线与30分钟两入口日期/价格分开，不把周线否定改成所有级别均无买点；截至状态不外推文后图走势。', ['2006年12月6日600050多周期问答'], figs=((57, 1),))
c(14, '000063-reader-count-corrected-not-endorsed', '58-b002',
  '对000063读者的周线点序，作者纠正1999年4月30日为第二类买点，称周线最标准的唯一第一类买点为2003年1月3日12.69元那周。',
  '均线系统第一买点|均线系统第二买点|周期K线图|确认', 1, '不把读者03年1/2及第三买卖点计数当作者逐项认可；图另标99年5/14/03年1/2不覆盖作者原日。', ['2006年12月6日000063周线问答'], figs=((57, 2),))
c(14, 'macd-lines-and-histogram-combined', '58-b006',
  '面对MACD均线与柱体不同步该看哪个的提问，作者回答都要看、综合看，并把复杂细节留待后课。',
  'MACD|背驰|指标对比', 1, '保留紧邻问题，未给冲突时的固定优先级、权重或新算法；不能只凭一句补为总看柱体或总看黄白线。', ['2006年12月7日该MACD线/柱不同步问题'])

keep('44-b003 44-b004', 'upper-l012-c-stage-two-average-buy-points-not-risk-free upper-l012-c-stage-system-only-two-principle-and-later-clarification', '13课失效退出是承接12课均线系统两点及高风险例外，不按同名升级后期三类定义。')
keep('44-b002 46-b007 46-b008', 'lower-l105-c-stage-jul1-two-third-centers-no-risk-author-assertion lower-l105-c-stage-jul2-active-accumulation-partial-chips-not-always-half', '13主动带套防护及特定旧仓差价与105主动买套分批降成本分别留语境，不把旧底仓不动/无风险概括全局。')
keep('47-b005', 'upper-l011-c-stage-flying-kiss-definition', '14课飞吻复述11课定义，原文来源在本段保留，不重复造新定义命题。')
keep('47-b006', 'upper-l011-c-stage-lip-kiss-definition', '14课唇吻复述11课未穿越条件。')
keep('47-b007', 'upper-l011-c-stage-wet-kiss-definition', '14课湿吻复述11课穿越/甚至反复。')
keep('47-b008 47-b009', 'upper-l011-c-stage-average-position-short-above-long-bull', '14课男女上位复述短线相对长线位置。')
keep('45-b002 51-b002 51-b004 52-b004 52-b005', 'upper-l011-c-stage-nov29-shenzhen-sensitivity-historical-view upper-l012-c-stage-dec1-five-line-and-shenzhen-gap', '12/4建议继续有效、12/5解盘自引11/29建议、12/6嵌12/5再嵌12/1缺口提示；引用来源日期/外层日期分开，旧命题不变。')
keep('53-b004 55-b003', 'upper-l023-c-stage-macd-high-double-top-smaller-divergence upper-l023-c-stage-zero-axis-nearby-not-strict-cross', '早期双头与回零轴后的过程同23课可互查，保留指标参数和相应级别，未用旧例代替后课完整中枢定义。')

issue('early-class-names-and-level-law', '47-b010 47-b011 47-b013 48-b000 50-b000 51-b001',
      '第14课原文明称第一/第二类，但本节为均线体系；大级别二买与次一级别相应一买的周/日示例需与后期结构级别区分。',
      '保留原类名和完整相应/次一级别条件，仍使用独立均线点概念，不自动等同后课严格中枢类点。', True)
issue('active-protection-vs-old-lot-and-lump-topup', '44-b002 44-b003 44-b004 46-b006 46-b007 46-b008',
      '主动带套有规模介入及失效防护两义；TCL旧仓不动、一次补仓与其他课一般分批/失效退出有具体语境，不可全局合并。',
      '区分程序失效退出、停止买入与原仓差价案例；不把永不卖原仓或一次全补推为普遍法则。', True)
issue('half-warning-and-retest', '44-b004 45-b010 45-b011',
      '作者一半的位置未给明确参照区间，反抽一般有非保证；读者牛市无需止损的前提未获明确认同。',
      '不补50%计算式或无限等反弹，保留前男上位最低位与一般反抽范围。', True)
issue('macd-double-period-and-example-comparison', '47-b012 49-b000 50-b001 51-b000 53-b004 55-b003 58-b006',
      '长一倍MACD没有正文明确参数映射；图双面板12/26/9/2不直接证明作者24/52/18；12课8/7与14课2005/12/13日例及文后尚无日卖需留参数/口径差异。',
      '逐条保留原日期与参数说明、线柱综合看和没有卖点截至时间，不强行生成统一历史回测或冲突消解。', True)
issue('figure-origin-adjustment-and-dates', '47-b012 49-b000 53-b004 56-b003 58-b002',
      '18图9文后/2011重绘、9未核；黑白/彩色不同复权、2002/7/9那周、000063图日/正文日等不能由未知标注覆写。',
      '原文与图证并列，未独立复算除权或MACD，不认证图源；43前课图仅边界查看不重算。')
issue('nested-quotations-and-reader-mislabel', '45-b001 45-b002 47-b000 47-b001 51-b004 52-b000 52-b002 52-b004 52-b005 52-b006',
      '14源段已修正：47读者瞎鼓捣无时间，51/52多层引号中11/29、12/1、12/5、12/6作者评论分别定位，裸时间只管后文。',
      '保留源文本和坐标，引用不改为当前回复；读者选股/筹码判断不因作者笼统赞同而全获认证。')
issue('success-profits-and-efficiency-claims', '44-b003 44-b005 46-b006 46-b007 55-b009',
      '退出一般盈利、强市90%以上、解套价格时间与最有效率系统都是作者未给样本的经验/预测。',
      '保留作者身份、强弱/资金/能力条件，不转为项目回测胜率、固定收益或绝对无风险。')
issue('patent-and-copyright-self-description', '48-b000 51-b001',
      '作者自称定律有专利及发明权、允许无版权费使用并要求署名；本汇编未附专利登记或效力证明。',
      '作为作者自述/署名要求保留，不认证法律权利或执行其监督/惩罚指令。')

note('44-b003 44-b005 45-b007', 'rhetorical-context', '论语、有位次/无位次、港湾台风与习惯致命的类比完整已读。', '比喻支持说明方法态度，不是形式证明、医疗事实或行动指令；具体技术条件另抽。')
note('45-b014 46-b000', 'historical-price-forecast-context', '作者回顾一年半前私下说5000乃至一万的预期，跨页已读。', '未核私下时间与兑现，不转换成当前行情目标或预测胜率。')
note('51-b003 52-b001 52-b003', 'quotation-delimiters', '解盘自引中的多层引号起始已核，日期分别属所引文章。', '引号不是读者署名，空引号不独立支持命题。')
note('52-b000 52-b002 52-b006', 'historical-commentary-and-quote-introduction', '12/6午间回顾12/5提示、所引12/5外出说明和12/6收盘5日线/短差评论已读。', '引用内外层时间分开，不把预料中自评当准确率证据；无新严格结构定义。')
note('58-b003', 'practice-reminder', '作者要求多看不同图，尤其短线的练习提醒已读。', '练习建议不等模型/人工实际回测完成。')

relations = {
    'upper-l013-c-stage-passive-entrapment-blind-entry': [('被动带套', '操作策略', 'qualifies')],
    'upper-l013-c-stage-active-entrapment-two-meanings-and-protection': [('主动带套', '操作策略', 'related')],
    'upper-l013-c-stage-average-first-entry-another-bear-kiss-invalid': [('主动带套', '均线系统第一买点', 'qualifies')],
    'upper-l013-c-stage-average-second-entry-break-old-bear-low-exit': [('主动带套', '均线系统第二买点', 'qualifies')],
    'upper-l014-c-stage-entanglement-includes-all-three-kisses': [('均线系统', '飞吻', 'related'), ('均线系统', '唇吻', 'related'), ('均线系统', '湿吻', 'related')],
    'upper-l014-c-stage-buy-point-law-corresponding-next-level': [('缠中说禅买点定律', '均线系统第二买点', 'related'), ('缠中说禅买点定律', '均线系统第一买点', 'related')],
    'upper-l014-c-stage-short-difference-program-reduce-rebuy-order': [('缠中说禅短差程序', '操作级别', 'requires'), ('缠中说禅短差程序', '均线系统第一卖点', 'requires')],
    'upper-l014-c-stage-divergence-no-promised-duration-amplitude': [('背驰', '幅度', 'qualifies')],
}
for r in rows:
    r['relations'] = [{'source': a, 'target': b, 'type': t} for a, b, t in relations.get(r['id'], [])]
by_passage = defaultdict(list)
for r in rows:
    for e in r['evidence']:
        by_passage[e['passage_id']].append(r)
for item in pending:
    item['lesson_numbers'] = sorted({int(passages[x]['unit_id'].split('-')[1]) for x in item['passage_ids']})
    if item['id'].endswith('figure-origin-adjustment-and-dates'):
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
        result, reading, atomic, inverse = 'reader_context', '读者署名、问题、价位和判断已读，用于限定作者回复，不作为直接作者证据。', [], '例如600058提问、600639红柱缩及000530吸筹断言/000063计数不能直接归作者。'
    elif p['text'].startswith('教你炒股票') or p['text'] in ('缠中说禅解盘:', '缠中说禅解盘：', '缠中说禅回复:', '缠中说禅回复：') or re.fullmatch(r'.*200[5678]-\d{1,2}-\d{1,2}.*', p['text']) and (len(p['text']) < 75 or p['text'].startswith('缠中说禅')):
        result, reading, atomic, inverse = 'source_header', '课程、作者解盘或回复的标题与时间头已核。', [], '仅定位来源，时间头不独立支持结论。'
    else:
        raise AssertionError(('unaccounted paragraph', id, p['text']))
    if linked and decision:
        reading += '；其余语境：' + decision['reading']
        inverse += '；' + decision['inverse']
    ledger.append({'passage_id': id, 'lesson_number': int(p['unit_id'].split('-')[1]), 'document_id': DOC,
                   'pdf_page': p['pdf_page'], 'role': p['role'], 'speaker': p['speaker'], 'published_at': p['published_at'],
                   'source_text_sha256': hashlib.sha256(p['text'].encode()).hexdigest(), 'result': result,
                   'claim_ids': [r['id'] for r in linked], 'related_existing_claim_ids': retained[id], 'existing_evidence_not_mutated': True,
                   'pending_issue_ids': [x['id'] for x in pending if id in x['passage_ids']], 'reviewer': REVIEWER,
                   'rounds': {'1_read_and_scope': reading, '2_atomic_conditions': atomic,
                    '3_normalization': {'concept_labels': sorted({x for r in linked for x in r['concepts']}), 'related_existing_claim_ids': retained[id],
                     'note': '主动带套与105主动买套不做无条件别名；均线类点与后期严格类点、周/日/30/5图、相应走势与持有截至时间分别保留。'},
                    '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True, reviewer=REVIEWER, visual_review_note=f['note'],
             figure_source_review='18本课图全部查看；9文后/2011整理图、9未核原发图，黑白/彩色不自动判作者；43图属前课仅边界核查。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 120 and Counter(x['lesson_number'] for x in ledger) == {13: 42, 14: 78}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
           'lessons': [13, 14], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger),
           'claims': len(rows), 'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
           'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)),
           'whole_lesson_semantic_read_complete': True, 'technical_extraction_complete': False, 'four_round_review': True,
           'independent_review_claimed': False, 'visual_pdf_pages': list(range(43, 59)), 'figure_objects_viewed': 18,
           'adjacent_figure_viewed': {'id': DOC + '-p0043-fig1', 'unit': 'lesson-012', 'counted_in_batch': False},
           'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)), 'pending': [x['id'] for x in pending],
           'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True, 'database_mode': 'ro', 'formal_import': False,
           'acceptance': '13至14课120段16页18图同模型四轮；14段源修正、均线失效退出/多周期短差与倍周期MACD范围、9后加9未核图分别保留，增量待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close()
sys.stdout.reconfigure(encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False))


