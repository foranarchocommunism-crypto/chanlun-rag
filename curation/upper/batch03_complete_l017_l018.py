"""Materialize the root agent's lesson 17/18 review; source database is read-only."""
import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
KB = HERE.parents[2] / 'shared-knowledge/v0.1.0'
PREFIX = 'volume_1-a53e99c37ca5-'
BATCH = '03-l017-l018-complete'
REVIEWER = '主代理 / 阶段C上册17至18课四轮复核'


def dump(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def build():
    db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id IN ('lesson-017','lesson-018') ORDER BY pdf_page,block_index,id")}
    concepts_before = {r['label'] for r in db.execute('SELECT label FROM concepts')}
    existing = [dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed' AND (id LIKE 'upper-l017-%' OR id LIKE 'upper-l018-%') AND id NOT LIKE '%-c-stage-%'")]
    prior_links = {}
    for record in existing:
        for row in db.execute('SELECT passage_id FROM evidence WHERE claim_id=?', (record['id'],)):
            prior_links.setdefault(row['passage_id'], []).append(record['id'])
    base = json.loads(db.execute("SELECT value FROM metadata WHERE key='graph_version'").fetchone()[0])
    common = '第一轮完整顺序读第17课75段和第18课24段，包括作者解盘、读者问题与作者答复；第二轮将定义、论证前提、方法和历史情境拆分；第三轮对照已有两课31条命题及65/66课相关边界，复用概念；第四轮逐条回到引文，并查看PDF75至84，核对量词、级别、完成状态、否定、公式和图源。主代理同一模型不同检查视角，不称独立或人工复核。'
    records = []

    def add(lesson, slug, text, concepts, sources, conditions, level, reason, note, relations=None, figures=None, kind='explicit', derivation=None):
        evidence = [{'passage_id': PREFIX + p, 'quote': passages[PREFIX + p]['text']} for p in sources]
        if figures:
            evidence[0]['figure_ids'] = [PREFIX + f for f in figures]
        record = {'id': f'upper-l{lesson:03d}-c-stage-' + slug, 'text': text, 'kind': kind, 'conditions': conditions, 'exceptions': [], 'concepts': concepts, 'ambiguity_status': 'none', 'review_note': common + ' ' + note, 'reviewer': REVIEWER, 'evidence': evidence, 'relations': relations or [], 'importance_level': level, 'importance_reason': reason + '；分级为整理判断。'}
        if any(passages[e['passage_id']]['role'] == 'author_commentary' for e in evidence):
            record['review_note'] += ' 语境：本课所附2006-12-19作者解盘或技术学习说明，具体时点见证据；适用条件：保留本条历史市场对象或方法限制。'
        if figures:
            record['figure_review_note'] = '实际查看PDF78的600497图与PDF79的580991日线图，核对对应标的和作者旁文；只发布对作者文字归类及解释的忠实转述。图的原始作者仍unverified，未用日线图独立证明30分钟结构或重新数中枢。具体图形独立验证继续pending。'
        if derivation:
            record['derivation'] = derivation
        records.append(record)

    add(17, 'classification-experience-foundation', '作者将走势可分趋势与盘整的分类称为从实际图形分析中总结的经验，并把它作为其技术分析理论基础。', ['走势分解', '走势类型', '技术分析'], ['p0075-b010'], ['作者在第17课对其理论来源的说明'], 3, '保留分类的经验来源与理论地位', '不把作者自述的经验总结写成本项目已经完成实证证明。')
    add(17, 'static-classification-dynamic-completion', '作者说明，走势终完美把静态的走势分类转换为动态的走势类型终要完成，以用于当下分析。', ['走势终完美', '走势类型', '当下'], ['p0075-b011', 'p0076-b000'], ['第17课原理一的用途说明'], 2, '补全原理一与实际分析的关系', '与现有原理一命题区分：本条解释作用，不另造不同的完成定义。')
    add(17, 'recursion-bottom-boundary', '第17课说明中枢定义的次级别递归不能无限下去，最后不可分解级别改用该级别单位K线的重叠来定义中枢。', ['递归定义', '最低级别', '走势中枢', 'K线'], ['p0076-b003'], ['第17课最后不可分解级别的定义入口'], 1, '保留递归停止与定义切换的边界', '文中物理学类比不作为本项目科学结论，不把最低级别固定为某个分钟数。', relations=[{'source': '递归定义', 'target': '最低级别', 'type': 'qualifies'}])
    add(17, 'alternating-directions-center-argument', '作者用向上、向下、向上或向下、向上、向下的图形说明会产生某一级别中枢，所讨论一般走势以前提可以继续延续、不会永久取消交易为范围。', ['走势中枢', '级别', '走势分解'], ['p0076-b007', 'p0077-b000'], ['可不断延续且不存在永久取消交易的一般走势讨论', '只称某一级别，不必是观察图周期所对应级别'], 2, '补全原理二的论证语境', '不将三次方向变化误写成任意同级别中枢充分条件。')
    add(17, 'no-center-degenerate-exclusion', '在第17课论证中，作者把完全没有中枢的图形归为一次下行后永远上行、或一次上行后永远下行两种情形，并将其归入永久取消交易而排除一般讨论。', ['走势中枢', '走势终完美', '交易规则'], ['p0076-b007', 'p0077-b000'], ['作者为原理二给出的论证和排除范围'], 3, '保留不含中枢情形的排除前提', '这是作者论证的转述，不称为对所有真实退市路径的本项目定理。')
    add(17, 'two-point-sell-side-statement', '作者说明，第17课对第一、第二类买点的分析，在卖点方面反之亦然。', ['第一类买卖点', '第二类买卖点', '买点', '卖点'], ['p0077-b005'], ['第17课该段关于两类买点分析的对称说明'], 2, '补全作者明确给出的卖点方向', '仅记录原文反之亦然，不擅自修正下一段定律一的买点措辞。')
    add(17, 'first-second-reduce-to-first', '作者称，由第一、第二类买卖点构成的买卖点可归结到不同级别的第一类买卖点。', ['第一类买卖点', '第二类买卖点', '级别'], ['p0077-b008'], ['仅所述由第一、第二类买卖点构成的范围'], 1, '保留转折定律前的归结关系', '未扩大到尚未在本段讨论的第三类买卖点。', relations=[{'source': '第二类买卖点', 'target': '第一类买卖点', 'type': 'related'}])
    add(17, 'multi-level-resonance', '作者说明，不同级别可以同时出现第一类买卖点，称为不同级别的同步共振；转折定律因此只说某级别而不限定为次级别。', ['同步共振', '级别', '第一类买卖点', '趋势转折'], ['p0077-b010'], ['对第17课趋势转折定律级别措辞的解释'], 2, '保存同时出现及某级别的边界', '不把共振扩展为多个指标同时金叉，也不把不同级别解释成必然同一时刻成交。', relations=[{'source': '同步共振', 'target': '第一类买卖点', 'type': 'related'}])
    add(17, 'case-similar-shapes-different-levels', '作者把600497从2004-06-02至2005-07-27的下跌、盘整、下跌归为日线结构，而把相似的580991归为30分钟结构，理由是后者日线下跌中没有日线中枢。', ['走势中枢', '级别', '下跌', '盘整'], ['p0078-b002', 'p0079-b000'], ['第17课600497与580991的历史图例', '归类为作者文字判断，非本项目独立重算'], 3, '保留相似外形不能代替级别中枢判定的例子', '实际查看相关日线图；完整30分钟原图及逐个中枢的独立重建未完成。', figures=['p0078-fig2', 'p0079-fig1'])
    add(17, 'case-first-leg-types-and-strength', '作者把600497其后2005-07-27至10-25判为日线上涨、580991在2006-10-23至12-13判为日线盘整，并以先前结构级别和其后第一段类型两个因素解释力度差别。', ['走势类型', '级别', '上涨', '盘整', '走势中枢'], ['p0079-b001', 'p0079-b002'], ['第17课两标的指定日期的比较', '作者分别称日线上有两个中枢和一个中枢'], 3, '保存力度比较的两项联合解释', '不改写成仅看价格涨幅就能确定级别；图示数字只作为作者历史案例。', figures=['p0078-fig2', 'p0079-fig1'])
    add(17, 'divergence-comparison-premise', '作者在本课思考题中先说明，背驰涉及两相邻同向趋势间后者比前者的走势力度减弱，再提出指标应在哪个级别判断的问题。', ['背驰', '趋势', '级别', '指标对比'], ['p0079-b005'], ['仅提取题目前半句已陈述的概念条件', '后半句关于均线及MACD的提问不是已作答定理'], 1, '保留相邻同向和前后力度比较', '不把问句当作作者肯定任何MACD柱背离必然是背驰。')
    add(17, 'center-more-basic-learning', '作者在解盘说明中要求从中枢概念思考，认为盘整、趋势可包含于该框架，中枢是比二者更基本的概念。', ['走势中枢', '盘整', '趋势'], ['p0079-b007'], ['第17课思考题的作者学习说明'], 2, '保留中枢在定义框架中的地位', '包含于概念框架不是价格区间的集合包含，不造无条件价格包含边。')
    add(17, 'indices-diverge-oscillation-case', '在2006-12-19解盘中，作者把沪深两市走势背离与随后震荡联系起来，并称当时深圳走势更明确。', ['指数走势背离', '市场震荡'], ['p0080-b000'], ['2006-12-19沪深市场的作者经验解释'], 4, '保存解盘技术解释的具体对象', '两市走势背离不与严格背驰概念合并，不把该句当跨市场统计结论。')
    add(17, 'downside-gap-short-term-test-case', '作者在当时解盘中认为，下方留下缺口会使短线面临考验，不回补是强势表现，但仍需经过考验。', ['缺口', '市场震荡', '操作级别'], ['p0080-b001'], ['2006-12-19上海连续缺口的历史背景'], 3, '保留缺口未补与免于考验的区别', '不写成缺口必补或不补即无风险。')
    add(17, 'breakout-inertia-retest-case', '作者把当时突破历史高位后的上涨称为惯性上攻，认为惯性耗尽后会回试此前历史高位进行确认。', ['突破', '突破惯性', '反抽', '确认'], ['p0080-b002'], ['2006-12-19突破历史高位后的短线判断'], 3, '保留突破、惯性耗尽和回试顺序', '原文必然语气留在引文，命题归于该日作者判断，不作所有突破的通用预测。')
    add(17, 'case-center-date-author-correction', '作者在580991答疑中否定读者给出的两个日期范围，明确指出日线中枢为11月8日至11月28日，由三个次级趋势构成。', ['走势中枢', '次级别', '趋势'], ['p0080-b012', 'p0080-b016'], ['2006-12-18的580991具体图例答疑', '日期是原文所给，不能推广到其他标的'], 3, '保留作者对具体中枢时间的纠正', '不采纳读者给出的10月23日至11月8日或11月14日至21日，具体图形独立定位仍pending。')
    add(17, 'indicators-auxiliary-not-necessary', '作者强调用均线或MACD看背驰只是辅助，没有这两个指标也能判断背驰，应先理清走势及级别等逻辑关系。', ['背驰', '均线', 'MACD', '级别'], ['p0080-b019', 'p0081-b000', 'p0081-b003'], ['第17课对指标与背驰判断关系的作者回复'], 1, '保留指标的辅助地位和非必要性', '与66课标准情况下同时看黄白线和柱面积的建议区分，不据此认为指标足以定义背驰。', relations=[{'source': 'MACD', 'target': '背驰', 'type': 'qualifies'}, {'source': '均线', 'target': '背驰', 'type': 'qualifies'}])
    add(17, 'divergence-learning-order', '作者给出的学习逻辑顺序为走势、级别、趋势、前后趋势比较、背驰，最后才是均线等辅助判断。', ['走势', '级别', '趋势', '背驰', '均线'], ['p0081-b001', 'p0081-b002'], ['本次答疑中先弄清前项再理解指标的方法要求'], 2, '保存背驰学习的前置顺序', '这是作者学习路线，不把每个顺序箭头当可传递的充分证明。')
    add(17, 'bull-market-mentality-holding', '作者在牛市学习答疑中强调持有信心，并要求先克服熊市心态、打好基础。', ['市场心理', '持股', '操作熟练程度'], ['p0081-b005'], ['2006-12-18作者对当时牛市学习者的说明'], 3, '保留市场状态与持有心理的语境', '没有把其对成分股的修辞和预期转述为每只股票保证上涨。')
    add(17, 'shortcuts-and-application-discipline', '作者认为追求捷径和一夜暴富会妨碍市场学习；理论需要由操作的人落实，仅得到消息或买到所谓黑马也可能拿不住。', ['市场心理', '持股', '操作熟练程度', '公开信息'], ['p0081-b013'], ['作者关于学习与实际执行的价值判断'], 3, '补齐方法执行和心理条件', '不把训诫写成经本项目统计验证的心理因果，也不将保有个股建议泛化。')
    add(17, 'adjustment-inertia-fund-year-end-case', '作者在2006-12-19答疑中认为，真正调整须待突破历史高位的惯性耗尽，并提醒年末基金业绩与募集关系可能影响行情。', ['突破惯性', '调整', '主力资金'], ['p0081-b016'], ['2006-12-19历史市场答疑', '平台、锯齿与三角形只为当时形态预期'], 4, '保留调整条件与资金时点背景', '未把锯齿型的很可能改成必然，也不宣称本项目确认基金真实行为。')
    add(18, 'trend-chart-level-entry', '作者把打开走势图所见称为走势，并指出走势分不同级别。', ['走势', '级别'], ['p0082-b002'], ['第18课基本术语入口'], 1, '补齐走势及其级别入口的直接表述', '没有用图表周期直接替代中枢和走势类型级别。')
    add(18, 'completion-before-profit-size-speed', '作者将判断走势类型完成列为核心问题，并把完成后方向选择与利润大小、快慢的进一步研究分开。', ['完成', '走势类型', '走势终完美', '技术分析'], ['p0083-b000'], ['第18课对理论分析顺序的说明'], 2, '保留完成判断与后续评价的层次', '百分百确定盈利为作者理论目标和修辞，原引文保留，不作本项目绩效保证。')
    add(18, 'ready-to-end-is-not-ended', '三个连续重叠次级别走势完成后，盘整具备随时完成的条件，但仍可以不结束而继续围绕中枢延伸。', ['盘整', '完成', '走势延伸', '走势中枢'], ['p0083-b001'], ['所说三个连续重叠次级别走势已走出来'], 1, '明确具备完成条件与已经结束不是同一状态', '与已发布盘整延伸命题互为解释，不把可随时完成写成必须立即结束。')
    add(18, 'extension-trading-difficulty', '作者以趋势延伸解释为何上涨中容易过早离场、下跌中抄底困难，并将逃顶抄底难归因于走势类型延伸。', ['走势延伸', '趋势', '市场风险', '操作策略'], ['p0083-b002'], ['作者对趋势延伸实际操作影响的说明'], 3, '保留趋势延伸的双向操作风险', '不把两个中枢已经出现当趋势结束确认，不添加交易阈值。')
    add(18, 'extension-known-type-new-center-key', '作者说明，走势类型延伸意味着该类型已确定并随时可以完成，判断延伸是否结束的关键在是否产生新的中枢。', ['走势延伸', '走势类型', '走势中枢', '完成'], ['p0083-b003'], ['作者所述已进入延伸的走势类型'], 1, '补齐延伸判断的对象和关键观察', '保留关键一词，不把任意新中枢单独变成所有类型延伸结束的充分条件。')
    add(18, 'center-connection-not-necessarily-trend', '在本课趋势内同级别中枢的连接讨论中，作者说明连接不必是趋势，可以是各种走势类型，并举跳空缺口后形成新中枢为极端例子。', ['中枢连接', '走势类型', '趋势', '缺口'], ['p0083-b004', 'p0083-b005'], ['趋势内两个同级别中枢的连接'], 1, '补全对第17课第一道思考题的类型回答', '不能将连接简写成必须次级别趋势。', relations=[{'source': '中枢连接', 'target': '走势类型', 'type': 'qualifies'}])
    add(18, 'center-connection-below-sublevel-gap', '连接同级别中枢的走势不必正好是次级别，也可更低；作者以跳空缺口属于最低级别、在日周线图上不等于次级别为例。', ['中枢连接', '次级别', '最低级别', '缺口'], ['p0083-b004', 'p0083-b005'], ['本课趋势内同级别中枢连接的讨论', '日线、周线仅为例子'], 1, '保留次级别或更低的范围和缺口例子', '不把缺口另行确认为一个完整次级别趋势。')
    add(18, 'connection-lower-level-usually-stronger', '作者称相连走势类型的级别往往越低，其力度越大，并以此解释缺口的技术含义。', ['中枢连接', '级别', '缺口'], ['p0083-b005'], ['本课趋势内中枢连接讨论', '原文往往的经验强度'], 2, '保留级别与力度关系的适用对象', '不是任意小级别走势都比大级别走势幅度更大，不与单线段幅度判级别混同。')
    add(18, 'same-level-exit-return-new-center', '作者论证原中枢维持时指出，离开或返回只要是同级别走势类型，就意味着形成新的中枢，与原中枢维持前提矛盾。', ['中枢维持', '中枢新生', '同级别', '走势类型'], ['p0084-b000'], ['原中枢维持的讨论', '离开或返回中有一个为同级别走势类型'], 2, '补全中枢维持充要条件的论证依据', '不把不满足维持的所有情形压缩成某个固定买卖点。', relations=[{'source': '中枢维持', 'target': '中枢新生', 'type': 'distinguishes'}])
    add(18, 'extrema-v-common-overlap-less-common', '在以1分钟图为最低级别的盘整极值解释中，作者称重叠震荡后回头较少见、V型尖顶较常见，以此解释高低点常在盘中一闪而过。', ['盘整', '高低点', '最低级别', 'K线'], ['p0084-b002'], ['离开与返回走势连接处的最低级别观察', '1分钟是本段示例'], 3, '保存两种极值情形的作者经验比较', '只作作者频率描述，不声称本项目已有统计检验。')
    add(18, 'three-destruction-pairs-strongest', '作者在趋势加盘整、趋势加反趋势、盘整加反趋势三种中枢破坏组合中，将趋势加盘整称为最用力的破坏形式。', ['中枢破坏', '趋势', '盘整', '反趋势'], ['p0084-b005'], ['仅所列三种次级别离开与回抽组合'], 2, '保留比较范围及原文最用力的强度', '往往上涨较有力的底部例子见原引文，不加强为必然大涨或无风险。')
    add(17, 'example-overlap-arithmetic', '整理计算：A经过8至18元、B经过18至12元、C经过12至24元时，共同价格范围的下界为12元、上界为18元。', ['价格区间', '重叠', '走势中枢'], ['p0081-b011', 'p0082-b005'], ['仅按给定价格区间计算共同范围', '不据此确认三段的级别、完成状态或已形成具体中枢'], 3, '为原文重叠提问提供可追溯算术推论', '作者本段提出问题而未直接写出答案；本条明确为整理推论，不改成作者明说。', kind='inferred', derivation={'supporting_claim_ids': ['upper-l017-overlap-example', 'upper-l018-center-first-three'], 'explanation': '将价格经过范围记为A的8至18、B的12至18、C的12至24。参照三范围重叠的上下界计算，max(8,12,12)=12，min(18,18,24)=18。本条仅作区间算术，不据例子补出连续次级别走势完成等中枢成立前提。'})

    original = next(json.loads(s) for s in (HERE / '01-center-trend-level-pilot.reviewed.jsonl').read_text(encoding='utf-8-sig').splitlines() if s.strip() and json.loads(s)['id'] == 'upper-l017-second-point-law')
    original['reviewer'] = REVIEWER
    original['ambiguity_status'] = 'source_buy_sell_wording_pending'
    original['review_note'] = common + ' 本次实际核对PDF77，正文确为第二类买卖点由次级别第一类买点构成；第19/20课本次复核未找到明确更正。仅更新歧义与复核说明，原命题、条件、概念、重要性及引文保留。买卖点与买点在卖点情形的措辞未确认，不擅自纠正原文。'
    records.append(original)
    for record in records:
        for e in record['evidence']:
            text = passages[e['passage_id']]['text']
            assert e['quote'] in text, record['id']
            e['quote_start'] = text.index(e['quote'])
    assert len({r['id'] for r in records}) == len(records)
    (HERE / (BATCH + '.reviewed.jsonl')).write_text('\n'.join(dump(r) for r in records) + '\n', encoding='utf-8')
    pending = [
        {'id': 'upper-l017-second-point-law-wording', 'lesson_number': 17, 'claim_id': 'upper-l017-second-point-law', 'passage_id': PREFIX + 'p0077-b007', 'status': 'pending', 'issue': '第二类买卖点与第一类买点的原文措辞在卖点情形有歧义；原页已核，19/20课暂未找到明确作者更正，保留原句并单独标注。'},
        {'id': 'upper-l017-case-center-independent-reconstruction', 'lesson_number': 17, 'status': 'pending', 'issue': 'p78/79日线图及作者归类解释已查看；580991的完整30分钟图和11月8日至28日中枢的独立逐段重建未完成。只发布作者文字判断，不称重算通过。'},
        {'id': 'upper-l017-macd-question-full-answer', 'lesson_number': 17, 'passage_id': PREFIX + 'p0079-b005', 'status': 'pending', 'issue': '背驰比较的条件和指标辅助说明已收录；该题关于MACD图级别与是否必然对应趋势背驰的完整逐问答案需跨课核对。'},
        {'id': 'upper-l017-figure-origin', 'lesson_number': 17, 'status': 'pending', 'issue': 'p78两图及p79一图已实际查看，原始绘制者均未核，不能当作者原图证明。'},
        {'id': 'upper-l018-figure-formula-origin', 'lesson_number': 18, 'figure_id': PREFIX + 'p0082-fig1', 'status': 'pending', 'issue': 'p82彩色图把正文三段重叠公式简化并含黄色说明；署名/日期未核，图注不作作者正文命题。原正文max(a2,b2,c2)、min(a1,b1,c1)已核。'},
        {'id': 'upper-l018-extension-infinite-wording', 'lesson_number': 18, 'passage_id': PREFIX + 'p0083-b001', 'status': 'pending', 'issue': '作者同时陈述走势终要完成与盘整可延伸直到无穷；本批保留随时可完成但不必立即结束的边界，关于无穷的严格逻辑解释不自行补造。'},
    ]
    (HERE / (BATCH + '.pending.jsonl')).write_text('\n'.join(dump(p) for p in pending) + '\n', encoding='utf-8')
    new_links = {}
    for record in records:
        for e in record['evidence']:
            new_links.setdefault(e['passage_id'], []).append(record['id'])
    repeated = {'p0082-b003': ['upper-l017-type-partition'], 'p0082-b004': ['upper-l017-type-partition'], 'p0082-b008': ['upper-l017-principle-one'], 'p0082-b009': ['upper-l017-principle-two'], 'p0082-b010': ['upper-l017-decomposition-one'], 'p0082-b011': ['upper-l017-decomposition-two']}
    question_pending = {PREFIX + 'p0079-b005': pending[2]['id']}
    specific = {'p0079-b004': '连接类型与级别问题已由第18课p83-b004/b005的正文答复收录', 'p0079-b006': '盘整高低点问题已由第18课p84-b002及既有命题收录', 'p0077-b002': '原理一、二和中枢定义是下列分解定理的作者论证入口，过渡句不另造命题', 'p0077-b006': '作者关于准确找点后的安全/战无不胜修辞，条件见前段两类买点命题，不写成实际收益保证', 'p0077-b011': '理论原创性自评，不作为技术成立证据', 'p0078-b000': '几何理论及长期不败的作者自评，具体原理和定理已收录', 'p0078-b001': '引入后续两标的案例', 'p0079-b003': '内容消化、版权提醒和作业引入', 'p0080-b003': '当时中长线牛市判断及成分股提问的插话，不另作通用技术规则', 'p0081-b012': '对重叠问题的修辞，前段例子已保留', 'p0082-b001': '引入基本概念列表', 'p0084-b003': '引入由前两中枢定理证明定理三的过渡'}
    ledger = []
    for pid, passage in passages.items():
        suffix = 'p' + pid.rsplit('-p', 1)[-1]
        new = new_links.get(pid, [])
        old = prior_links.get(pid, repeated.get(suffix, []))
        if new:
            result, reason = 'new_claim_or_annotation', '新增解释、条件或案例见关联记录；原定律仅明确歧义，未改原句'
        elif old:
            result, reason = 'existing_claim', '与已有命题重复，保持对应来源及稳定ID；本次逆向复核未改其内容'
        elif passage['role'] == 'reader':
            result, reason = 'reader_context', '读者问题保留回复上下文，不作作者直接证据'
        elif passage['role'] == 'unknown' or re.match(r'^缠中说禅[：解盘]*20', passage['text']) or suffix in {'p0075-b009', 'p0082-b000'}:
            result, reason = 'transition', '课程标题、身份时间头或答疑分隔'
        elif suffix in specific:
            result, reason = 'transition_or_context', specific[suffix]
        elif suffix in {'p0082-b003', 'p0082-b004', 'p0082-b008', 'p0082-b009', 'p0082-b010', 'p0082-b011'}:
            result, reason = 'existing_claim', '重复第17课的类型、原理或分解定理，按本页原文保留来源，不造第二套概念'
        else:
            result, reason = 'context', '已经顺序阅读；含义由同段既有/新增记录或紧邻语义单元承载'
        local = [r for r in records if r['id'] in new]
        ledger.append({'passage_id': pid, 'lesson_number': int(passage['unit_id'][-3:]), 'source_text_sha256': hashlib.sha256(passage['text'].encode()).hexdigest(), 'role': passage['role'], 'result': result, 'claim_ids': new, 'existing_claim_ids': old, 'pending_issue_ids': [question_pending[pid]] if pid in question_pending else [], 'reason': reason, 'rounds': {'1_read_and_scope': '全文顺序读段落与相邻问题/回答，区分作者身份及课程边界', '2_atomic_conditions': '定义、完成前提、案例时点、经验语气和问句分开；结果见本条', '3_normalization': {'reused_concepts': sorted({c for r in local for c in r['concepts'] if c in concepts_before}), 'new_concepts': sorted({c for r in local for c in r['concepts'] if c not in concepts_before})}, '4_reverse_check': '回看原文及PDF75至84；量词、否定、级别、公式与图源分别核对，未解事项保持pending'}})
    (HERE / (BATCH + '.coverage.jsonl')).write_text('\n'.join(dump(r) for r in ledger) + '\n', encoding='utf-8')
    summaries = []
    for lesson in [17, 18]:
        summaries.append({'lesson_number': lesson, 'document_id': 'volume_1-a53e99c37ca5', 'actual_read_scope': '全部75段，PDF75-b009至81-b016' if lesson == 17 else '全部24段，PDF82-b000至84-b005', 'whole_lesson_semantic_read_complete': True, 'technical_extraction_complete': False, 'four_round_review': True, 'reviewer': REVIEWER, 'batch': BATCH + '.reviewed.jsonl', 'base_graph_version': base, 'new_records': sum(r['id'].startswith(f'upper-l{lesson:03d}-c-stage-') for r in records), 'existing_annotation_updates': ['upper-l017-second-point-law'] if lesson == 17 else [], 'existing_claims_rechecked': sum(r['id'].startswith(f'upper-l{lesson:03d}-') for r in existing), 'pending': [p for p in pending if p['lesson_number'] == lesson], 'coverage_ledger': BATCH + '.coverage.jsonl', 'visual_pdf_pages': list(range(75, 82)) if lesson == 17 else [82, 83, 84], 'figure_objects_viewed': 3 if lesson == 17 else 1, 'logged_at': datetime.now(timezone.utc).isoformat()})
    (HERE / (BATCH + '.summary.json')).write_text(json.dumps(summaries, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    db.close()
    print(dump({'batch': BATCH, 'records': len(records), 'new': len(records)-1, 'annotation_updates': 1, 'passages': len(passages), 'base_graph_version': base}))


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    build()
