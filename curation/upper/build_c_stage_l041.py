"""Materialize the main agent's four-pass reading of lesson41.

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
BASE = 'c_stage_l041'
REVIEWER = 'Codex 主代理 / 阶段C上册41课同模型四轮复核'
SOURCE_SHA = 'bd70acecbe09c0143f322f4950ab8edb6f2f4584ce7fb123f94fe57cd10db183'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-041' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 67
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 301 AND 306 ORDER BY pdf_page,id', (DOC,))]
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
    pending.append({'id': 'upper-l041-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})




















c(41, 'market-rhythm-buy-at-buy-point-sell-at-sell-point', '301-b004',
  '作者把市场节奏概括为买点买、卖点卖，并说买点在下跌中、卖点在上涨中形成。',
  '买卖点|买点|卖点|操作策略', 1, '以识别相应级别买卖点为前提，不能把任意下跌都判买点或任意上涨都判卖点；死亡词是告诫修辞，不作实证损失定律。')
c(41, 'greed-fear-obstruct-point-discipline', '301-b004',
  '作者认为恐惧会阻止在下跌中的买点买入，贪婪会阻止在上涨中的卖点卖出，因而干扰市场节奏。',
  '市场心理|买卖点|操作策略', 2, '陈述心理机制与纪律观点，未以所有恐惧/贪婪证明某个具体点成立，也未证明遵守便必然盈利。')
c(41, 'good-bad-stock-classification-as-entry-exit-timing', '301-b005',
  '作者在操作语境把买点上的股票称好股票、卖点上的称坏股票，强调据市场时点作判断。',
  '买点|卖点|基本面|操作策略', 2, '好坏是该段时点修辞，不替代企业基本面或全部投资价值评价；与40课技术节奏和真长线基本面不同语境并存。')
c(41, 'trust-current-market-not-author-reputation', '301-b005 301-b006',
  '作者要求参与者自己把握命运，称包括作者本人也不值得盲信；过往辉煌不能代替当下对市场节奏的判断。',
  '当下|市场心理|操作策略', 1, '不是由作者声誉认证所引市场事实，需对具体级别和结构取证；永远/唯一是其纪律性强调。')
c(41, 'capital-size-not-protection-same-zero-speed-rhetoric', '301-b006',
  '作者以1万亿与1万变成零的速度一样、前者甚至更快，告诫大资金和过去成绩不能免除节奏错误的风险。',
  '资金管理|市场风险|当下', 3, '金额和速度是原文强比喻，没有定义起止时间/杠杆/损失模型，不作资金规模无差异的统计或数学定律。', ambiguity='author_capital_to_zero_speed_rhetoric_unverified')
c(41, 'no-chase-third-points-form-in-pullback-and-rebound', '301-b007',
  '作者反对追涨杀跌，说明连第三类买卖点也分别在回调与反弹中形成，按买点买、卖点卖无需追涨杀跌。',
  '第三类买卖点|买点|卖点|反抽|反弹|追高', 1, '分别指第三类买点的回调与第三类卖点的反弹，仍须相应级别及原定义条件，不等任意回调/反弹都是三类点，亦未给所有风险止损的完整规则。')
c(41, 'points-have-level-small-point-may-continue-large-unspent-move', '301-b008',
  '买卖点有级别；大级别能量未耗尽时，小级别买卖点引发大级别走势延续，作者认为是正常情形。',
  '买卖点|操作级别|走势级别延续|能量结构', 1, '未把每个小级别点都当大级反转；能量耗尽本段未给量化阈值，需保留具体方向与结构。')
c(41, 'small-point-against-nonexhausted-large-trend-risk', '301-b008',
  '若小级别买卖点与大级别走势方向相反，而大级别走势没有衰竭，参与该小级别点要承担大级别走势继续的风险。',
  '买卖点|操作级别|走势级别延续|市场风险', 1, '须同时保留方向相反及大级无衰竭，不扩成所有小级别操作都禁做；与40课多层各自节奏的操作机会并列为风险限制。',
  ['小级别点与大级别走势相反', '该大级别走势尚无衰竭'])
c(41, 'accuracy-before-frequency-and-transaction-beneficiaries', '301-b008',
  '作者认为不需要频繁买卖，操作应重准确率而非次数，并说券商与税务部门喜欢高交易频率。',
  '操作策略|交易成本|操作熟练程度', 2, '是纪律及成本提醒，没有提供准确率阈值、频率上限或各市场税费制度；不认证只有这两类主体能从高频受益。', ambiguity='author_frequency_beneficiary_generalization_not_empirical')
c(41, 'pretrade-check-point-type-level-centers-market-sector', '301-b009',
  '买入前要检查是否买点、何级何类、大级别走势、各级别中枢分布、大盘及所属板块，卖出时类似；作者认为分析清楚有助操作。',
  '买卖点|操作级别|走势中枢|板块轮动|操作策略', 1, '原段列分析维度，不是六项满足即可保证买点或收益的评分算法，也不是只看单一指标。')
c(41, 'rhythm-before-precision-learning-and-practice', '301-b010 302-b000',
  '作者区分买卖点判断精度与操作程序节奏：精度可随理论学习和实践提高，但节奏不能乱，初学者也应要求自己按此执行。',
  '操作熟练程度|机械化操作|买卖点|操作策略', 1, '正文跨PDF301至302两段联合；节奏比精度重要不取消识别有效点和级别的要求，不把强制执行当盲目交易。')
c(41, 'beginner-prefer-thirty-minutes-never-below-five', '302-b001',
  '针对判断买卖点精度不高的初学者，作者建议按30分钟进出较好，怎么也不能小于5分钟。',
  '操作熟练程度|操作级别|买卖点', 1, '初学者教学约束，不是所有参与者永久最低5分钟或把周期图直接当严格递归级别；本段未给统一毕业门槛。', ['初学者、买卖点判断精度不高'])
c(41, 'beginner-five-minute-divergence-stage-is-necessary-not-buy-signal', '302-b001',
  '在初学者操作限制中，作者说5分钟都没进入背驰段就不能操作。',
  '操作熟练程度|操作级别|背驰段|买卖点', 1, '未进入不得操作是必要限制，不是进入背驰段便已背驰或立即买入，也不据此抹去第二第三类点的独立条件。', ['初学者的较低级别操作约束'])
c(41, 'smaller-level-higher-precision-frequent-errors-harm-learning', '302-b001',
  '作者说级别越小，判断精度要求越高；频繁交易带来的频繁失误会使心态变坏并妨碍技术学习。',
  '操作级别|操作熟练程度|市场心理|交易误差', 1, '是其教学因果判断而非任何交易频率必然失误的统计定律，未给小级别不可能成功的结论。')
c(41, 'correct-wrong-rhythm-not-endure-first-second-third-opportunity', '302-b002',
  '作者反对把心态好等同忍受节奏错误，一旦错就应跟上；例为错过第一类仍有第二类机会，再错至第三类更应改正。',
  '市场心理|第一类买卖点|第二类买卖点|第三类买卖点|操作策略', 1, '例为相应级别可识别的机会，不是每一走势都保证依次给三点或连错三次必损失固定金额；仍需保留战斗能力的风险前提。')
c(41, 'three-opportunities-rhetoric-and-rest-after-repeated-errors', '302-b003',
  '作者以三类买卖点作三次改错机会的比喻，劝连续犯同样错误者休息，反对股票已连续拉升后只赌后续涨停。',
  '买卖点|涨停|追高|操作熟练程度', 2, '三次是教学说法，不独立证明三类点必全出现或上涨N倍后任何时点绝无买点；原死亡词不作实际结果预测。')
c(41, 'mar30-month-quarter-close-and-further-oscillation-author-view', '302-b005 302-b006',
  '3月30日作者称当日走势和月季略上影对市场双方可接受，并认为3000点上再震荡盘整对自己有利，后续仍有震荡。',
  'K线|宏观市场判断|市场震荡|走势预测', 4, '具体历史判读与利益自述；未认证被其贬称的市场对手身份、控制能力或预测收益，不归为当今市场事实。')
c(41, 'mar30-second-line-balance-and-spark-not-spread', '302-b007',
  '作者据当时三线监管警告、一线大盘博弈，认为二线是较可接受的平衡，一些二线新高是点火，但能否扩散仍另说。',
  '二线股|三线股|板块轮动|监管风险', 4, '保留当时判断及能否燎原的不确定性，未核真实监管事件、未给固定分类股票表，不证明二线永远稳健。')
c(41, 'apr2-shenzhen-second-line-sector-strength-historical-view', '304-b001 304-b002',
  '4月2日作者让看不明上海指数者看深圳，称二线获更多认同，当天涨停多为二线和有题材三线，并把先拉金融后变弱的过程解释为不同力量博弈。',
  '指数走势背离|二线股|三线股|板块轮动|主力资金', 4, '只记作者具体盘面和因果解释，不认证所有深圳成分股均同一基本面或实际机构身份；10元上下不是普遍择股阈值。')
c(41, 'apr2-three-hundred-or-shenzhen-constituents-large-capital-partial-financial', '304-b003',
  '当时不会选股者被作者建议看300或深圳成分股；金融和特大盘股可能表现但多为博弈，较大资金可组合一部分。',
  '资金管理|仓位|板块轮动|操作策略', 3, '历史条件性建议；原只写300，不猜全称/具体名单，未给仓位比率，也不作当前可投资清单。')
c(41, 'apr2-stepwise-market-and-five-day-line-fallback', '304-b004',
  '作者预期当时走势进二退一甚至进三退二，提醒把握节奏；不明白者可看5日线，称此前折腾仍未破5日线。',
  '均线系统|市场震荡|操作策略|走势预测', 3, '步数为当时形容并非确定涨跌周期；5日线是辅助简法，非中枢定义或所有时期安全保证。')
c(41, 'sector-rotation-reply-does-not-confirm-reader-fifteen-minute-top', '305-b003',
  '对次日15分顶背驰可能性及几个行业的提问，作者只说大盘震荡正常、板块轮动，人多看好未必能拉起。',
  '板块轮动|市场心理|宏观市场判断|走势预测', 3, '读者3272.41突破则极可能顶背驰是读者推测，作者未明确确认该数值、15分钟级别或电力煤炭医药具体方向；拥挤抬轿是因果比喻。')
c(41, 'monthly-quarterly-large-sell-point-and-long-operation-exit', '305-b006',
  '问何时放弃长期操作的股票，作者说通常在超大级别卖点出现时，举季度甚至月线为例，并用年老色衰作比喻。',
  '长期投资|操作级别|卖点|持股', 1, '通常而非任意小卖点即永远放弃，也不认证月季卖点后企业终结或永无再买机会；未给这种卖点的独立完整算法。')
c(41, 'career-analogy-switch-not-from-buy-to-sell-single-stock-max-profit-view', '305-b011',
  '在职业发展答复中作者类比换股：等买点或换股时机，不从买点股票换到卖点股票；并称一只股票也能获取最大利润，关键在买卖节奏。',
  '买卖点|操作策略|资金管理', 3, '职业是类比上下文，最大利润为作者未实证的强说法，未给最优化目标/区间/基准或保证单股最优；不替代真实工作和配置判断。', ambiguity='author_single_stock_max_profit_undefined_objective')
c(41, 'divergence-consolidation-only-turn-force-is-current', '305-b016',
  '作者说背驰、盘整背驰只意味着转向；转向力度与中枢星球系统分布和当下买卖力度相关，是当下概念。',
  '背驰|盘整背驰|趋势转折|中枢系统|动力学|当下', 1, '转向不等一定发展为反趋势或给出幅度/持续时间；读者关于盘背怎样转趋势的问法未被一套确定算法回答，并保留相应级别边界。')
c(41, 'force-estimation-auxiliary-tools-promised-not-specified', '305-b016',
  '作者说有辅助工具可以预计转向力度，但因复杂留待专门课程，本答未展开。',
  '动力学|技术分析|走势预测', 2, '不从以后会说虚构本课已给公式，不将预计当保证可预知确切幅度。')
c(41, 'completion-question-basically-yes-qualified-not-equivalence', '306-b001',
  '面对读者以背驰解释趋势完成、以三买三卖解释中枢和盘整完成的提问，作者答基本上可以这样理解，随即补充本级盘整结束的范围。',
  '完成|趋势|盘整|第三类买卖点|背驰', 1, '保留基本上和作者后续限定；读者原问仍为读者，不转写成趋势完成当且仅当背驰、三买卖是所有对象唯一充要终结规则。', ambiguity='qualified_acknowledgment_not_formal_necessary_sufficient_completion_rule')
c(41, 'own-level-consolidation-center-end-consolidation-end', '306-b001',
  '作者说该级别盘整中枢结束，该级别盘整就结束。',
  '完成|盘整|走势中枢|操作级别', 1, '限定同一个该级别盘整及其中枢，不泛指任意一个小中枢结束等于所有大级趋势完成。')
c(41, 'own-consolidation-end-may-enter-larger-consolidation', '306-b001',
  '该级别盘整结束不意味着一定脱离盘整，还可以进入更大级别的盘整。',
  '盘整|级别|完成|中枢扩展', 1, '保留可以而非必然扩展；不能以本级三类点确认结束推导脱离一切级别盘整或行情幅度。')
c(41, 'yearly-perspective-consolidation-almost-absolute-scope', '306-b001',
  '作者称若站在年线角度，基本盘整就是绝对的。',
  '年线|盘整|周期K线图', 3, '保存若站在年线/基本的观察范围和强修辞，不作所有市场无限历史均为盘整的数学命题，也不据此取消其他级别趋势。', ambiguity='author_yearly_consolidation_strong_rhetoric_scope')

note('302-b004','closing-music-discipline-context','正文以巴赫赋格和周末自然音乐类比节奏，收尾抛贪恐。','音乐比喻不作市场概率/利润证明，正文却倾听字面保留，不另发音乐/交易操作。')
note('302-b009 303-b000 303-b001 303-b002 303-b003 303-b004 303-b005 304-b000','nontechnical-political-economy-essay-context','4月2日相对流动性、资本市场/金融重构八段含跨页已完整读，属于作者历史经济论述。','保留原文、日期、上下文与坐标；外储数字/资本大国预测未外部核验，不抽作缠论技术定理或当前经济事实。')
note('304-b008 304-b009','nontechnical-currency-opinion-context','答美元地位与人民币，强调当下合力及政策执行，作者历史判断已读。','不将读者将被颠覆或作者正被颠覆认证为当前汇率事实，不当缠论走势规则。')
note('304-b012 305-b010 305-b012','nontechnical-life-reply-context','人生归宿、职业束缚与自主性答复已读，保留其对应提问。','非技术哲学与人生比喻不变为市场收益定理，不对读者现实处境作外部认证。')

issue('rhythm-no-chase-third-point-and-strong-wording-scope','301-b004 301-b005 301-b006 301-b007 301-b010 302-b000 302-b002 302-b003',
      '节奏比精度和买点只在下跌中须结合级别/类型，三类点回调反弹不等任意回撤；死亡、资金归零同速、三次机会是强修辞。',
      '保留具体买卖点条件及纠错前提，不补全部止损/连续三点必然路径，不用修辞证明收益。',True)
issue('beginner-level-frequency-and-divergence-stage-necessary-not-sufficient','301-b008 302-b001',
      '初学者30分较好、不得小于5分且5分未入背驰段不操作；进入背驰段不是确认背驰，准确率优先未给阈值。',
      '联合识别能力及方向结构审查，跨后课找完整入段和完成判据，不将周期图/严格递归级别静同一。',True)
issue('opposing-small-level-and-force-amplitude-current','301-b008 301-b009 305-b016',
      '小级逆尚未衰竭大级有续行风险；背驰盘背只给转向，幅度依中枢系统及当下力量，辅助法本答未给。',
      '与后课动力学/转折定理逐项比对，不承诺任意转向即反趋势，不以40多层独立抹相关风险。',True)
issue('completion-qualified-acknowledgment-and-larger-consolidation','306-b000 306-b001',
      '读者将背驰与趋势完成、三买卖与中枢盘整完成相连，作者基本认可后重申本级结束可入更大盘整，非完整充要算法；年线强词有范围。',
      '与38/71及后课结构完成条件比对，保留作者基本上及读者身份，不认为本级结束就脱离所有盘整。',True)
issue('historical-index-sector-regulator-and-reader-forecast','302-b005 302-b006 302-b007 304-b001 304-b002 304-b003 304-b004 305-b001 305-b002 305-b003',
      '月季收盘、3000点上震荡/二线、300与深圳/5日线均历史语境；15分3272.41预测和行业观点未逐一获作者确认。',
      '不认定未名市场对手/监管因果，未外核盘面，不给当前股票建议或普遍固定价格/周期。')
issue('long-stock-exit-and-single-stock-max-profit-rhetoric','305-b006 305-b011',
      '长期操作退出通常例月季大卖点，非永久死亡定律；职业类比中单股最大利润未给目标/基准。',
      '与真长线基本面/多层资金范围并置，不把所有单股或全部投资者最优形式化。')
issue('nontechnical-appendices-reply-date-normalization-and-no-figures','302-b008 302-b009 303-b004 304-b000 304-b008 304-b012 305-b010 306-b001',
      '经济/人生附文已读只保留上下文，本课六页无图，17段作者日期时刻缺空格已规范元数据，原字符和身份不改。',
      '原始汇编边界无原博客逐字校对，宏观数字/人生比喻不作技术知识或实证结果。')

relations = {
 'upper-l041-c-stage-market-rhythm-buy-at-buy-point-sell-at-sell-point': [('买卖点','操作策略','qualifies')],
 'upper-l041-c-stage-greed-fear-obstruct-point-discipline': [('市场心理','买卖点','qualifies')],
 'upper-l041-c-stage-small-point-against-nonexhausted-large-trend-risk': [('操作级别','市场风险','qualifies')],
 'upper-l041-c-stage-accuracy-before-frequency-and-transaction-beneficiaries': [('操作策略','交易成本','qualifies')],
 'upper-l041-c-stage-beginner-prefer-thirty-minutes-never-below-five': [('操作熟练程度','操作级别','qualifies')],
 'upper-l041-c-stage-beginner-five-minute-divergence-stage-is-necessary-not-buy-signal': [('背驰段','操作熟练程度','qualifies')],
 'upper-l041-c-stage-divergence-consolidation-only-turn-force-is-current': [('背驰','动力学','qualifies'),('中枢系统','当下','qualifies')],
 'upper-l041-c-stage-own-consolidation-end-may-enter-larger-consolidation': [('盘整','中枢扩展','qualifies')],
 'upper-l041-c-stage-monthly-quarterly-large-sell-point-and-long-operation-exit': [('长期投资','卖点','qualifies')],
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
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], '读者15分3272.41顶背推测和完成概念原问仍保留读者身份；作者大盘震荡/板块轮动未明确认可数字预测，基本上可以理解不自动成为充要定理。'
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
        'note': '买卖点/级别和节奏纪律联合；初学者30分/5分限制、背驰段必要非充分，小级逆大级风险；完成基本认可与可入更大盘整分层，经济/人生附文保留上下文。'},
        '4_reverse_check': inverse}})
assert len(ledger) == 67 and Counter(x['lesson_number'] for x in ledger) == {41: 67}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [41], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(301, 307)), 'figure_objects_viewed': 0, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '41课67段6页无图及前后边界同模型四轮；17日期仅空格规范，纪律/级别/初学限制、转向力度与完成范围、历史盘面及非技术附文分层，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


