"""Materialize the main agent's four-pass reading of lesson29.

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
BASE = 'c_stage_l029'
REVIEWER = 'Codex 主代理 / 阶段C上册29课同模型四轮复核'
SOURCE_SHA = 'a8872533d74f0bd1739a74fb33daaed06d8a3514289d6183ff176f8f8a6572d3'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-029' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 72
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 204 AND 213 ORDER BY pdf_page,id', (DOC,))]
assert len(figures) == 12
rows, pending, notes = [], [], {}
quote_overrides = {}
for short in ['206-b003', '209-b000']:
    source_id = f'{DOC}-p0{short}'
    assert '（备注：' in passages[source_id]['text']
    quote_overrides[short] = passages[source_id]['text'].split('（备注：')[0]
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
    pending.append({'id': 'upper-l029-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})



c(29, 'same-center-oscillation-no-own-level-reversal', '204-b001',
  '在某级别盘整、围绕该级别中枢的震荡延续中，作者不在同一级别谈转折；站在次级别图形才可讨论其转折。',
  '盘整|中枢震荡|趋势转折|次级别', 1, '“不存在”限定某级别盘整内部，不等所有更低级别无转折或盘整永不结束。')
c(29, 'up-and-down-reversal-two-directions', '204-b001',
  '上涨的转折可为下跌或盘整，下跌的转折可为上涨或盘整，转折本身有级别。',
  '上涨|下跌|盘整|趋势转折|级别', 1, '与接下来背驰后三类结构结果分层，转折不只表示同级反向趋势。')
c(29, 'divergence-reversal-theorem-three-outcomes', '204-b002',
  '缠中说禅背驰-转折定理称：某级别趋势的背驰将导致该趋势最后一个中枢的级别扩展、该级别更大级别的盘整，或该级别以上级别的反趋势。',
  '缠中说禅背驰-转折定理|趋势|背驰|中枢扩展|盘整|反趋势', 1,
  '作者给出的定理陈述，某级别趋势/最后一个/更大盘整/以上反趋势均保留；正文仅给例子与证明轮廓，项目未完成数学证明。',
  ['某级别趋势发生背驰'], ambiguity='author_theorem_statement_without_full_formal_proof_in_chapter')
c(29, 'five-divergence-point-nested-one-and-below', '204-b003',
  '作者以5分钟下跌背驰段为例，通过1分钟及1分钟以下背驰逐层定位点位，其后所谓反弹须再按三类结构结果界定。',
  '背驰段|区间套|次级别|反弹|缠中说禅背驰-转折定理', 2, '精确点是作者方法主张，不补秒图实测或唯一数学点；不能以反弹一词代替三类级别条件。')
c(29, 'five-trend-n-centers-and-last-leg-below-one', '204-b005',
  '在5分钟趋势背驰例中，作者设趋势内有N个5分钟中枢且N≥2；跌破最后中枢后的背驰段须在1分钟以下，否则与它是最后一个5分中枢的前提矛盾。',
  '趋势|走势中枢|背驰段|次级别|最低级别', 1, '仅属所设最后中枢与背驰段的反证语境，不把所有a/b/c连接都强制恰为1分，亦不把以下替换为等于。',
  ['5分钟级别趋势且已认定最后中枢'], figs=[(204, 1)])
c(29, 'rebound-must-touch-dd-not-zd', '204-b005',
  '上述第一类买点后的反弹，作者断言至少触及最后中枢的DD=min(dn)，即围绕该中枢震荡的最低点；否则下方至少又成一个新5分中枢，与“最后”前提矛盾。',
  '第一类买点|DD|ZD|走势中枢|反弹', 1, 'DD为围绕震荡最低点，不是ZD中枢下沿；触DD并不等进入中枢重叠区，不以定理文字认证实际成交收益。',
  ['上条5分趋势背驰及最后中枢前提'], figs=[(204, 1)])
c(29, 'only-dd-weakest-expands-last-center', '204-b005',
  '只触及最后中枢DD的反弹被作者称为背驰后最弱反弹，会把最后中枢扩为更大级别，如5分扩到30分甚至更大。',
  'DD|反弹|中枢扩展|缠中说禅背驰-转折定理', 1, '此为原文最弱类，不把任意触DD都当充分判据，也不称已经形成两个完成走势类型。', figs=[(204, 1)])
c(29, 'first-buy-safe-profit-rare-weak-author-claim', '205-b000',
  '作者称第一类买点“绝对安全”，即使最弱反弹也足够获利，并说该弱类很少；若遇到，为资金利用率应找机会退出。',
  '第一类买点|反弹|资金管理|市场风险', 3, '绝对安全/足够获利/特别少是作者未经本项目实测的断言，没有费用、流动性和成交样本；退出未给机械时点。',
  ['第29课所设趋势背驰后的最弱反弹'], ambiguity='author_safety_profit_and_rarity_claims_not_empirically_verified')
c(29, 'weak-trend-case-versus-consolidation-third-sell', '205-b001',
  '作者区别趋势背驰后的末中枢扩展与盘整背驰转三卖：后者反弹级别低于最后中枢，前者反弹级别等于或大于最后中枢。',
  '背驰|盘整背驰|第三类卖点|中枢扩展|反弹|级别', 1, '须先明确趋势背驰或盘背转三卖的结构语境，不能把所有小反弹直接命名三卖。')
c(29, 'down-plus-consolidation-requires-larger-center', '205-b003 206-b000',
  '在两个完成走势类型的“下跌+盘整”连接中，盘整的中枢级别须大于下跌中的中枢；5分钟下跌后的这种盘整至少为30分钟级别。',
  '下跌|盘整|走势类型|走势中枢|完成', 1, '两个完成类型与单个未完成类型扩展分开，同级盘整会混入下跌延伸/末中枢扩展；这里触及最后中枢不同于仅触DD。',
  ['下跌与后续盘整各为完成走势类型'], figs=[(205, 1)])
c(29, 'down-plus-up-may-be-same-level', '205-b003',
  '“下跌+上涨”的反趋势连接不要求上涨中枢大于下跌中枢，5分钟下跌后接5分钟上涨是作者允许的正常情形。',
  '下跌|上涨|反趋势|同级别|走势中枢', 1, '定理的以上含同级，不将更大盘整的限制移植成反趋势也必须更大。', figs=[(205, 2)])
c(29, 'nine-one-minute-count-conditional-illustration', '206-b000',
  '作者以a+A+b+B+c作数量例示：A/B各至少三段1分类型，另假设a/b/c都是1分并统一按1分计量，则有9个；30分盘整也至少由三段5分、各至少三段1分组成。',
  '走势类型|次级别|级别|盘整|中枢连接', 2, 'a/b/c原可更低甚至缺口，9个依赖另加假设和计量口径，作者明说数量匹配不是主要原因；非所有趋势刚好9段的算法。',
  ['5分下跌示意', 'a/b/c假设均为1分钟走势类型', '按1分钟统一计量'], figs=[(205, 1)],
  ambiguity='conditional_count_example_not_general_minimum_nine_rule')
c(29, 'last-center-expansion-one-unfinished-type', '206-b001',
  '下跌最后中枢扩展仍是一个未完成走势类型的延续；“5分下跌+30分盘整”则表示下跌与盘整两个完成走势类型的连接。',
  '中枢扩展|走势类型|完成|下跌|盘整', 1, '相同更大中枢形状不抹去完成状态及分段边界，未完成与两个完成不互换。', figs=[(207, 1)])
c(29, 'expansion-regroups-a-tilde-and-may-evolve', '206-b001',
  '作者把a+A+b归为a~、把B+c的5分扩30分归为A~，得到a~+A~；其后可继续成a~+A~+b~+B~+c~的30分下跌，也可有其他演化。',
  '走势分解|中枢扩展|走势类型|走势延伸', 2, '保留可继续/其他演化，不把一次中枢扩展视为必然已成30分下跌；a+A+b为作者该重新组合例的5分类型。', figs=[(207, 1)])
c(29, 'first-sell-three-outcomes-reverse-direction', '206-b003',
  '作者称三类结果完整分类该级别第一类买点后的级别与力度，第一类卖点同理而方向相反。',
  '第一类买点|第一类卖点|缠中说禅背驰-转折定理|完全分类', 1, '完整分类是作者主张，引用只取备注前明确作者文字，不借未署名备注补定理。')
c(29, 'coarse-two-outcomes-omits-rare-first', '206-b003',
  '作者说第一类末中枢扩展很少且与第二类相似，故粗略可称背驰后盘整或反趋势；精确说法仍分三类。',
  '背驰|盘整|反趋势|中枢扩展|完全分类', 2, '粗略简说不能删除第一类，稀少无统计样本。')
c(29, 'first-sublevel-rebound-heuristic-not-absolute', '206-b003',
  '作者以首次反弹的末中枢次级走势判断强弱：5分下跌例看首次1分反弹是否回到末中枢；若不能，末中枢扩展类可能很大、力度可疑，但明确说判别并不绝对。',
  '反弹|次级别|走势中枢|中枢扩展|概率原则', 1, '有效性很大是作者未量化经验；引文止于备注前，不能由未回中枢推出必然第一类，也不能反推回中枢必排除所有扩展。',
  ['第29课末中枢的第一次次级反弹'], ambiguity='non_absolute_heuristic_and_unattributed_remark_kept_separate')
c(29, 'feb6-first-rebound-enters-last-center-case-judgment', '207-b000 208-b000',
  '在2007年2月6日指数例中，作者称首次1分反弹马上回到从2980下跌的末5分中枢，因而该例第一种最弱情形可“完全排除”。',
  '反弹|走势中枢|次级别|中枢扩展', 2, '保留本例原绝对措辞，与通论非绝对和未署名备注的边界并列，不扩大为所有回中枢都排除扩展；实践很多人把握住未核。',
  ['第29课2007年2月6日上证案例'], figs=[(207, 3)], ambiguity='case_absolute_exclusion_versus_general_heuristic_not_resolved')
c(29, 'feb7-up-end-and-thirty-future-two-branches', '208-b000',
  '作者说随后1分走势完成并扩成5分上涨，2月7日11点前后1分背驰结束该上涨；后中枢至少5分、实际演成30分，未来是30分以上盘整或上涨，须观察后续。',
  '背驰|上涨|走势中枢|盘整|完成|当下', 2, '排除快速5分上涨是本例演化后的判断，未来两支不是已确认30分上涨；2008图不能补2007预测准确率。',
  ['第29课2007年2月7日上证案例'], figs=[(207, 3)])
c(29, 'first-second-enter-then-watch-third-after-break', '208-b001',
  '作者的该例操作顺序是先在一、二买进入，再看突破第一个中枢后是否形成三买，出现则持有，否则可退出。',
  '第一类买点|第二类买点|第三类买点|突破|持股|操作策略', 2, '先买与后观察的顺序保留，不把突破本身等同三买；无困难为作者评价，不证明实际收益。')
c(29, 'small-capital-or-skilled-exit-rebuy-third', '208-b001',
  '对资金特别小或达到其所谓“小学毕业”熟练程度者，作者允许先在突破的次级走势背驰退出，再看回试三买：形成则回补，不形成不回补。',
  '资金管理|操作熟练程度|次级别|背驰|第三类买点|操作策略', 2, '小资金或熟练为原文或条件，辨盘背与三买转化须反复看图实践；不把学习阶段口号变成可量化合格证。',
  ['资金特别小，或作者所称已能熟练辨别盘背与三买转化'], ['不形成三买就不回补'])
c(29, 'oversold-relative-distance-to-last-dd', '208-b002',
  '作者在首次抄底筛选例中把“超跌”定义为当下位置离最后中枢DD=min(dn)幅度较大，偏好该距离最大的股票。',
  '超跌|DD|第一类买点|幅度|操作策略', 2, '标准依赖已识别趋势背驰/最后中枢，非离历史高点跌幅最大；“理论保证最高效率”与反弹保证是作者主张，未作收益排序实证。',
  ['第29课首次抄底策略及最后中枢前提'], ambiguity='author_efficiency_guarantee_not_tested')
c(29, 'first-wave-exit-ignore-weak-with-rare-exceptions', '208-b002',
  '该筛选法在反弹第一波次级背驰后退出；若此时仍达不到最后中枢，作者说可基本不考虑，但保留少见例外。',
  '反弹|次级别|背驰|走势中枢|操作策略', 2, '达不到最后中枢与未触DD不同，不把基本/例外改成永远无后续行情。',
  ['第29课第一次抄底及反弹第一波次级背驰'], ['作者承认可能有例外，只称可能性小'])
c(29, 'retest-select-reached-center-prefer-break-and-hold', '208-b002 209-b000',
  '作者在首次次级回试后，选择首次反弹已到最后中枢的股票，最好已突破且回试站稳；按走势必完美预期还有一个次级向上类型，若它盘背则退出。',
  '次级别|走势中枢|突破|走势终完美|盘整背驰|操作策略', 2, '达到为选择条件，突破站稳为最好而非偷换成唯一必要；此向上走势类型不必已成上涨趋势，备注不在作者引文内。')
c(29, 'no-v-prejudgment-from-this-theorem', '209-b000',
  '作者把后续无盘背的强力例称V型反转，但明确说预先判断V型反转不由本章定理解决，留待后课。',
  '缠中说禅背驰-转折定理|盘整背驰|反转式走势|走势预测', 1, '不由三类完备性推能事前选择唯一未来，图示V形不能补预判充分条件。')
c(29, 'feb9-triangle-fifth-leg-2720-branches', '210-b000',
  '2月9日解盘把2720附近中枢称为三角形，尾盘下跌为第五段；预计下周初突破，站稳2720再一波，站不稳则二次探底。',
  '三角形整理|走势中枢|突破|确认|走势预测', 3, '这是2007年当日分支预测，短线指标未给阈值；2/12后图不把2/9预期改成当时确定结果。',
  ['2007年2月9日15:09:19指数解盘'], figs=[(209, 2)], ambiguity='dated_index_branch_forecast_not_independently_verified')
c(29, 'feb12-triangle-rise-pressure-3000-uncertain', '210-b002',
  '2月12日解盘称三角形后再起一波、2850以上有压力，而能否3000点过年仍说不好。',
  '三角形整理|突破|走势预测|市场心理', 4, '这是2/12而非2/9，作者自述驱动个股/心理预期不当市场因果证明或当前点位建议。',
  ['2007年2月12日15:15:26指数解盘'], figs=[(209, 2)], ambiguity='historical_index_pressure_and_future_forecast')
c(29, 'unicom-needs-new-stimulus-historical-view', '210-b007',
  '2月9日作者判断联通大幅启动需新刺激，否则仍中枢震荡，当时把中移动回归预期视为主要支持。',
  '走势中枢|题材股|当下', 4, '特定股票当时条件判断，不认证回归事件、作者对手100亿资金或实际操盘，不生成阻击步骤。',
  ['2007年2月9日联通答复'], ambiguity='historical_stock_catalyst_view_and_self_report_not_verified')
c(29, 'bull-first-round-quarter-adjustment-forecast', '210-b010',
  '作者在2月9日称牛市第一轮尚早，第一轮真正结束时指数会有季线级别调整。',
  '牛市阶段|调整|操作级别|走势预测', 4, '第一轮为作者大概念及历史预测，非一般所有牛市分期定义，未做后验实证。', ambiguity='historical_bull_phase_forecast')
c(29, 'long-hold-long-buy-to-sell-and-week-center', '211-b000',
  '作者只接受从长线买点持有到长线卖点的长线概念；对000858当时大周线中枢，除资金巨大者外，主张先降为负成本再长持，以腾出资金。',
  '长期投资|买卖点|负成本|资金管理|走势中枢', 2, '巨大资金为例外且无金额阈值，负成本是策略主张非已证可实现；对几乎所有较好股票终创新高为作者牛市展望。',
  ['2007年2月9日000858长线与周线中枢答复'], ['资金巨大者作者另论'], ambiguity='dated_stock_forecast_and_negative_cost_strategy_not_verified')
c(29, 'one-minute-lowest-three-k-only-if-chosen', '211-b003',
  '作者说如果把1分钟当最低级别，三根K线重合部分即为该口径的1分钟中枢；如果把每笔成交当最低，则另算。',
  '最低级别|最小级别中枢|K线|重叠|成交分笔|递归定义', 1, '如果自选最低1分钟的条件不可省，非所有阶段严格递归1分中枢一律三根1分K；每笔成交非后期几何笔。',
  ['明确选择1分钟为最低级别的早期答复'], ['最低按每笔成交选取时另算'], ambiguity='early_chosen_lowest_level_vs_later_geometric_recursion_context')
c(29, 'do-not-predict-consolidation-up-also-possible', '211-b006',
  '对读者担心涨后必盘整跌回的追问，作者说也可能演化上涨，应到时看图反应，不须预测唯一分支。',
  '盘整|上涨|当下|走势预测', 2, '须连读者具体问题，不能脱离指代解释为任意行情永远只涨或否认结构预期。')
c(29, 'trend-completion-final-leg-sublevel-below-divergence', '212-b001',
  '作者答复说一个趋势完成，其最后一段至少在次级别以下出现背驰，须把走势类型里的中枢延续与“趋势+盘整”分清。',
  '趋势|完成|次级别|背驰|中枢延伸|走势类型', 1, '最后一段/至少在次级别以下保留，原文未在此提供可单靠一个小背驰充分确认任意高层完结的算法。',
  ['2007年2月12日中枢分段答复'], figs=[(211, 1)], ambiguity='completion_criterion_context_not_full_sufficient_algorithm')
c(29, 'previous-type-last-center-not-reassigned-forward', '212-b001',
  '对星星的指数中枢划分，作者说其第一段属于前一个走势类型的最后中枢，随后小背驰，再形成大级别中枢，不能把前面归到后面。',
  '走势分解|走势类型|走势中枢|背驰|完成', 1, '保留前后类型归属的文字判断，不采纳读者0201 9:50—14:10作为正式替换，也不凭图画补完所有分钟段数据。',
  ['2007年2月12日15:39:26星星中枢问题'], figs=[(211, 1)])
c(29, 'large-breakout-one-divergence-may-only-intraday', '212-b004 212-b005',
  '作者以30分明显突破前期为例，1分背驰可能只完成盘中震荡；要先大后小用区间套，大级别背驰段与二买初升或主升的作用不同，须综合各级别。',
  '区间套|背驰|背驰段|第二类买点|操作级别|中枢震荡', 1, '小信号发挥大作用的大级别背驰段条件保留；卖出还要找位置接回是作者对本例的策略，不推广为所有小背驰都能当场重入。')
c(29, '600640-nesting-before-small-signal-and-third-fall', '212-b011 213-b000',
  '对600640读者1分背驰后再跌，作者重申先大级别背驰段再区间套定位，小背驰可能盘中化解，并据该股大级别走势必完美判断第三段下跌必然。',
  '区间套|背驰段|走势终完美|次级别|下跌', 2, '第三段必然是该股当时作者判断，未提供完整走势数据独立验证；不认可读者13:45本来已是成立的一买。',
  ['2007年2月12日600640答复'], ambiguity='case_third_leg_necessity_not_independently_checked')
c(29, 'average-area-rough-definition-macd-measure-proof-absent', '213-b003',
  '对均线面积背驰问题，作者称只能算粗糙定义，一般用MACD辅助即可，并声称精确定义与证明须用测度论知识。',
  '缠中说禅趋势力度|缠中说禅趋势平均力度|背驰|MACD', 1, '测度论证明未在此给出，不补造公式或背书完备；读者面积越大力度越大等猜想不是作者认可的精确定义。',
  ['2007年2月12日16:45:09均线面积答复'], ambiguity='formal_measure_definition_and_proof_not_supplied')
c(29, 'gap-question-capital-level-daily-leg-nested-exit', '213-b006',
  '对600268缺口目标问题，作者主张不必预测补缺口，应按资金选日线或30分操作；若选日线，进入日线背驰段再用区间套定位卖点，否则按该级别持有。',
  '缺口|资金管理|操作级别|背驰段|区间套|第一类卖点', 2, '“好股票补后还涨”为历史修辞，不作所有缺口必回补的规则；日线背驰段与任意1分背驰分开。')

keep('204-b005', 'upper-l027-c-stage-nested-legs-must-be-inside-parent upper-l027-c-stage-finite-levels-no-unique-mathematical-point',
     '5分/1分以下定位仍须相应父段包含，有限层级不等唯一数学成交点；本课无秒图原数据。')
keep('206-b000', 'upper-l018-c-stage-center-connection-below-sublevel-gap',
     'a/b/c可低至缺口，后面统一计量假设不取消连接低于次级的条件。')
keep('211-b003', 'upper-l017-center-definition',
     '三K答复仅在自选最低1分口径，递归中枢至少三个连续次级走势的范围另保留，不把二者直接合一。')
keep('212-b001', 'upper-l028-c-stage-jan30-1035-previous-type-center-not-current upper-l028-c-stage-completion-not-short-average-standing',
     '29回复补充完成末段至少次级以下背驰及前后类型归属，但未完整给所有分钟段唯一划分，原压缩时间不改。')
keep('212-b004 212-b005 212-b011 213-b000', 'upper-l024-c-stage-early-higher-trend-small-divergence-limited upper-l028-c-stage-small-divergence-large-impact-two-contexts',
     '大背驰段/初升主升中的小信号作用分开，不把急促末段、原最小后果和后续逐步扩展合成无条件反转。')
keep('213-b003', 'upper-l015-c-stage-average-force-area-divided-by-time upper-l028-c-stage-macd-instead-of-private-average-force-not-prerequisite',
     '粗糙面积定义与MACD辅助、私有精确定义声称分开；测度论原文未给，不补形式证明或读者正比猜想。')

issue('unsigned-remarks-and-absolute-case-versus-heuristic', '206-b003 208-b000 209-b000',
      '206/209两备注无单独署名时间，不能确认为作者；首次回中枢仍可扩展备注、作者通论非绝对与2/6案例完全排除在解释强度上有张力。',
      '原文角色/字符/坐标保留，明确作者引用截到备注前；备注作为署名未核内容，后续查固定底本跨课范围，不抹掉完全排除或强行统一。', True)
issue('three-outcomes-dd-and-type-completion', '204-b002 204-b005 205-b003 206-b000 206-b001 212-b001',
      '三类定理仅给证明轮廓，DD非ZD；9段依假设，最后中枢扩展为一个未完成类型，两个完成类型的盘整须更大；末段小背驰不是高层完成的完整充分算法。',
      '保持必要前提、量词、完成状态和连接界线，不由图框/一次小背驰补唯一走势划分。', True)
issue('historical-index-case-and-prior-center-identity', '207-b000 208-b000 210-b000 210-b002 212-b001',
      '2/6、2/7指数分支与前一走势末中枢归属仍需更完整原始时序；星星读者的9:50—14:10范围不能替换作者作业时间。',
      '保留作者个例与原时间；后配2/12、2/13及2008行情不补当日确定性或唯一分段，28课关联待核仅部分补充。', True)
issue('lowest-one-minute-choice-versus-later-recursion', '211-b003',
      '如果把1分当最低则三K重叠，与后期分型/笔/线段递归1分口径需分语境，不能仅按时间覆盖或把成交分笔当几何笔。',
      '跨17/63/65及最低定义对照保留选择前提；本条不是全书通用三根1分K=严格1分中枢算法。', True)
issue('profit-safety-efficiency-and-v-prediction-limits', '205-b000 206-b003 208-b001 208-b002 209-b000',
      '绝对安全、足够获利、最弱少见、有效性很大、最高效率均无样本；原文不能预判V，且弱股可忽略有例外，三买需回试成立。',
      '历史方法与未经验证效果分层，保持小资金或熟练的或条件、最好非必要；不以定理宣称实际收益保证。', True)
issue('historical-self-report-and-forecasts', '206-b002 210-b001 210-b002 210-b003 210-b007 210-b010 211-b000 212-b008 213-b000',
      '牛顿类比、纯数学完美自评、负成本/对手资金与阻击自述、季线/3000/第三段下跌等均为作者当时主张或预测，未独立核实。',
      '保留日期与作者身份，未作为现代金融事实、已验因果或实测交易表现，不生成操盘攻击执行步骤。')
issue('average-force-and-absent-measure-theory-proof', '213-b003',
      '作者把均线面积定义称粗糙，声称测度论精确定义但未给出；不能从读者问题自动接受面积直接正比或反比力度。',
      '保持15/25/28均线与MACD的不同范围，原文未给的数学定义和证明返回证据不足。', True)
issue('embedded-dates-and-figure-provenance', '210-b001 210-b002 210-b003',
      '2/12解盘两段原继承2/9，已按嵌时间头修正；12图含4文后行情及8原发未核，4习作署张大山，2008图注2.5分和9段不是作者新定义。',
      '只改2段日期和12图来源备注，原文/字符/坐标不变；原图来源与作者命题语义复核独立。')

note('204-b004 205-b002', 'classification-heading', '三种情况分项标题已读，与定理陈述相对应。', '标题不额外支持独立结论。')
note('206-b002', 'historical-theory-self-assessment', '牛顿类比、纯数学无颠覆和拟书名等自评已读。', '作者自评不证明数学完整性和所有市场结论成立，双书名号原字保留。')
note('206-b003 209-b000', 'unattributed-inline-remarks-excluded-from-author-quotes',
     '段尾备注完整已读，但两处无单独署名/时间；作者引文只到备注前，原文仍完整。',
     '不推定备注必为作者或必为编者；第一处与本例完全排除张力待核，第二处大级别位置影响不由署名未核文字单独建立作者命题。')
note('209-b001', 'source-separator', '课程与作者解盘间星号分隔已核。', '分隔符不支持技术命题。')
note('210-b001 210-b003', 'historical-self-report-and-preview', '999/777负成本与筹码预告及2/12练图提醒已读；前段尾2/12时间头只管后两段。', '未核账户或攻击基金自述，不把预告当实际执行方法；全文不删改。')
note('212-b008', 'dated-market-forecast-context', '作者关于二三线股独立性、指数不大跌及3000试探条件已读。', '当时展望无独立行情/事件验证，不建立所有小盘股始终独立的定律。')

relations = {
    'upper-l029-c-stage-divergence-reversal-theorem-three-outcomes': [('缠中说禅背驰-转折定理', '背驰', 'requires'), ('缠中说禅背驰-转折定理', '中枢扩展', 'related'), ('缠中说禅背驰-转折定理', '反趋势', 'related')],
    'upper-l029-c-stage-rebound-must-touch-dd-not-zd': [('第一类买点', 'DD', 'related')],
    'upper-l029-c-stage-weak-trend-case-versus-consolidation-third-sell': [('盘整背驰', '第三类卖点', 'qualifies')],
    'upper-l029-c-stage-last-center-expansion-one-unfinished-type': [('中枢扩展', '完成', 'qualifies')],
    'upper-l029-c-stage-down-plus-consolidation-requires-larger-center': [('盘整', '走势类型', 'qualifies')],
    'upper-l029-c-stage-down-plus-up-may-be-same-level': [('反趋势', '同级别', 'qualifies')],
    'upper-l029-c-stage-oversold-relative-distance-to-last-dd': [('超跌', 'DD', 'requires')],
    'upper-l029-c-stage-one-minute-lowest-three-k-only-if-chosen': [('最小级别中枢', '最低级别', 'requires')],
    'upper-l029-c-stage-trend-completion-final-leg-sublevel-below-divergence': [('完成', '背驰', 'qualifies')],
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
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], '读者中枢分段、600640点位、面积关系猜想不作作者认可；三根K有最低级别自选前提。'
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
        'note': 'DD非ZD；三类后果、两完成类型与一未完成类型分开，首次回抽非绝对判据；不把署名未明备注/张大山习作/后配2008图当作者明说，最低1分三K保留自选前提。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True, reviewer=REVIEWER, visual_review_note=f['note'],
             figure_source_review='12图全部实际查看；4文后行情、8未核含4张大山习作；2008后图不作2007作者原发，DD/ZD与示意框分开，图注2.5分不建立正式级别。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 72 and Counter(x['lesson_number'] for x in ledger) == {29: 72}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [29], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(204, 214)), 'figure_objects_viewed': 12, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '29课72段10页12图同模型四轮；2解盘日期修正，三类后果/DD与ZD/扩展与两完成类型/最低级别自选及两署名未明备注分开，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


