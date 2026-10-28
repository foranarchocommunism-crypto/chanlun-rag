"""Materialize the main agent's four-pass reading of lesson35.

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
BASE = 'c_stage_l035'
REVIEWER = 'Codex 主代理 / 阶段C上册35课同模型四轮复核'
SOURCE_SHA = 'd42802c2bc8fbdb84c004e7254fdbb5d0223ec8c8d753b722d513e915a95e75e'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-035' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 56
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 262 AND 264 ORDER BY pdf_page,id', (DOC,))]
assert len(figures) == 3
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
    pending.append({'id': 'upper-l035-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})










c(35, 'level-recursion-breaks-center-type-circular-definition', '259-b009',
  '作者说中枢与走势类型及其连接相互依存，若定义止步于此会循环；必须引入级别，才能展开严格递归定义。',
  '走势中枢|走势类型|走势类型连接|级别|递归定义', 1, '是作者理论内部的定义路径，不以递归一词代替最低入口和逐级构成条件。')
c(35, 'strict-trade-base-three-same-price-transactions', '259-b010',
  '本课最严格口径以每笔交易为最低级别，连续三笔相同价位的交易构成最低级别中枢。',
  '成交分笔|最低级别|最小级别中枢|递归定义', 1, '这里三笔指成交笔数而非后期技术笔，也非任意三根K线；相同价位、连续和最严格口径不能省略；量子类比不构成物理证明。')
c(35, 'lowest-one-center-consolidation-two-centers-trend', '259-b010',
  '在本课最低级别分类中，一个最低级别中枢的走势为盘整；两个为趋势，第二中枢高于第一为上涨，反之为下跌。',
  '最小级别中枢|最低级别|盘整|趋势|上涨|下跌|完全分类', 1, '限定所引最低层递归分类，不把任意两个重叠图框或两根K线当趋势中枢。')
c(35, 'lowest-n-centers-successive-higher-or-lower-continues', '259-b010',
  '最低级别依次有N个中枢且N>2时，逐一第N个高于第N−1个则上涨延续；逐一低于则下跌延续。',
  '最低级别|走势级别延续|上涨|下跌|走势中枢', 1, '是依次中枢的位置关系，不是单个价格新高或只比较首尾两中枢；保留原N>2范围。')
c(35, 'lowest-up-ends-only-next-center-not-higher', '259-b010',
  '按本课最低级别定义，上涨要到依次下一中枢不再高于前一中枢，即等于或低于时才说结束；下跌相反。',
  '最低级别|上涨|下跌|完成|走势中枢', 1, '仅为作者该递归定义下结束条件，非任意一秒价低就结束，也不据结束自动判反向趋势或推销提前量。')
c(35, 'three-consecutive-lowest-types-price-intersection-upward-recursion', '259-b011 260-b000',
  '三个连续最低级别走势类型各自经过的价格区间有交集，就形成高一级中枢；据中枢再分类走势，可逐级递归上推。',
  '最低级别|次级别|走势类型|走势中枢|价格区间|重叠|递归定义', 1, '跨页连读，连续三段、走势类型和共同价格交集均保留；不是只两两相交或三根成交价任意交集。')
c(35, 'minute-levels-practical-not-strict-trade-recursion', '260-b000',
  '逐笔确认严格级别太繁复，作者实际用1、5、15、30、60分及日周月季年；称三连续1分类型重叠成5分、三连续5分成15或30分是不大严格但便于操作的说法。',
  '递归定义|级别|周期K线图|走势类型|走势中枢', 1, '作者称无原则性问题是其使用评价，不能将图周期与严格递归级别永久等同，尤其原句15或30不可只留30。')
c(35, 'single-five-type-cannot-contain-thirty-center', '260-b001',
  '单个5分钟走势类型无论怎样延续，都不能出现30分钟中枢；要形成30分钟中枢，只能由三个以上5分钟走势类型连接才可能。',
  '走势类型|走势类型连接|走势中枢|级别|走势延伸', 1, '单类型延续和多类型连接是不同对象；至少三连接是必要入口，不是任意三段不重叠也充分成中枢。')
c(35, 'five-type-must-and-at-most-own-center-level', '260-b001',
  '5分钟走势类型必须包含且最高只包含5分钟中枢；同级中枢一个或多个不改变其5分类型级别，而影响盘整或趋势分类。',
  '走势类型|走势中枢|级别|盘整|趋势', 1, '原例为1个或5个同级中枢，不是中心个数增加自动升格；不省趋势本身中枢位置条件。')
c(35, 'mixed-lower-level-connection-a-b-b-example', '260-b002',
  '高级别类型可先分解为不同低级别而未必全是直接次级别：a+B+b中B是由三个5分类型构成的30分中枢，a、b为1分，则全程连接两1分和三5分类型。',
  '走势类型|走势类型连接|走势分解|次级别|级别', 1, '大写B是中枢，B内各段是类型；全程为30分类型，不把a+B+b整体裸称中枢或把a、b强改成5分。')
c(35, 'decomposition-two-regroup-at-least-three-direct-sublevels', '260-b002',
  '作者允许拆散重分，将高级别类型表成直接次级别类型连接，据中枢至少三段给出分解定理二：任一级别任一走势类型，至少由三段以上次级别走势类型构成。',
  '走势分解|次级别|走势类型|走势类型连接|走势中枢', 1, '三段以上按不少于三保存，不把初始任意分段都要求等次级别；定理依拆散重分及中枢构成，不当任意3段足以成类型。')
c(35, 'a-b1-b2-b3-b-associative-regrouping-example', '260-b003',
  '若B由5分B1、B2、B3构成，作者将a+B+b写成a+B1+B2+B3+b=(a+B1)+B2+(B3+b)，并把这三个括号项判为5分类型。',
  '走势分解|走势类型连接|结合律|次级别|走势类型', 1, '保留该例a/b为1分、B为30分中枢的设定；不是任意一小段接5分必成完整5分的普遍代数规则。')
c(35, 'type-connection-associative-not-commutative', '260-b003',
  '作者称走势类型连接运算符合结合律，但不符合交换律。',
  '走势类型连接|结合律|走势分解', 1, '允许在同一时序路径中重分括号，不允许交换历史顺序或忽略原类型完成、级别与中枢条件；原交换率字样按其语义转述为交换律。')
c(35, 'decomposition-one-same-level-three-type-connections', '260-b003',
  '本课重述分解定理一：任何级别的任何走势，都可分解成同级别盘整、下跌与上涨三种走势类型的连接。',
  '走势分解|走势类型连接|同级别|盘整|下跌|上涨|完全分类', 1, '是三种可用分类，不是每次分解都必须恰好包含三种或恰三段；和定理二的类型至少三次级段分开。')
c(35, 'objective-path-subjective-level-five-three-thirty-one', '260-b005 261-b000',
  '走势客观而分析级别选择主观；同一a+B+b从5分角度是三个类型连接，从30分角度只有一个类型，选操作级别就是选分析和操作尺度。',
  '走势|操作级别|走势分解|走势类型连接|当下', 1, '跨页连读；主观是观察尺度选择，不是随意改已选级别的客观构成或将三段5分说成三段30分。')
c(35, 'five-up-down-up-two-rounds-thirty-no-trades-example', '261-b000',
  '作者以5分钟上下上三段为例，说5分角度有两个底背驰、两个顶背驰和两次完整操作；在所举30分类型内则无30分买卖点而不操作。',
  '操作级别|背驰|买卖点|走势类型', 2, '保留所举完整类型与观察级别的例境，不将任何画出的上下上三折线机械认证四背驰或把低级别点抹除。',
  ['所举a+B+b分成三5分类型、整体单30分类型的例子'], ambiguity='illustrative_endpoint_count_not_general_three_zigzag_signal_test')
c(35, 'lower-level-theoretical-efficiency-practical-constraints', '261-b001',
  '作者从纯理论角度称操作级别越低效率越高，同时强调实际级别受资金等具体条件限制，不能任意降低。',
  '操作级别|资金管理|交易条件', 2, '效率比较未给收益样本或统一优化函数，后面交易制度、幅度与误差是限制而非保证高频盈利。')
c(35, 'historical-t-plus-one-blocks-full-subminute-except-tzero', '261-b001',
  '本课按当时T+1语境说，完全用1分以下级别操作有无法顺利兑现的风险，系统须考虑全部情况，因此不可如此，除非T+0。',
  'T+1|T+0|操作级别|交易条件|市场风险', 1, '是2007年原论证的交易制度假设，不作为当前所有品种/账户规则说明；除非T+0是必要放宽之一，不等T+0就足够可盈利。')
c(35, 'tiny-level-amplitude-cost-error-no-long-run-meaning', '261-b001',
  '级别越小平均买卖点间波幅越小；若交易成本、误差相对波幅不够小，作者认为长期操作无意义。',
  '操作级别|幅度|交易成本|交易误差', 1, '保留相对幅度条件，非任何小级别都无用；原文没有统一手续费率或安全幅度数值。')
c(35, 'recognition-execution-lag-price-error-small-level', '261-b001',
  '作者把看见买点至实际完成的时间差及所致价位差列为交易误差，称极小级别需长期难达到的特别精确。',
  '交易误差|交易通道|价格精度|操作级别', 2, '该误差源不只手续费，也不能以图上理想点代真实成交，未测任何实盘通道延迟。')
c(35, 'chosen-level-own-buy-sell-enter-exit-no-own-down', '261-b002',
  '选定操作级别后，作者要求按该级别买卖点进入退出，不参与该操作级别的调整或下跌类型，卖后等同级相应买点。',
  '操作级别|买卖点|操作策略|调整|下跌', 1, '该操作级别非其内部所有低级回调；作者2001后四年不看股票只是自述，不能由其例认证真实交易或零回撤。')
c(35, 'partial-lower-level-trades-under-chosen-level', '261-b002',
  '保留操作级别时，次级别以下部分操作属风格且作者建议安排，尤其本级次级别盘整或下跌；若本级很大，也可用次次级部分操作降成本。',
  '操作级别|次级别|操作策略|成本|仓位', 1, '本级以下部分操作不等变更全部仓位的本级退出条件，也不保证实际降本；所称可忍受最大非上涨级别为该例次级别。')
c(35, 'zero-cost-only-risk-escape-author-assertion', '261-b002',
  '作者称降低成本是唯一降低风险的活动，并以只有成本为0才真正脱离风险的强措辞要求立体操作。',
  '成本|零成本持仓|市场风险|操作策略', 3, '这记录作者强主张；现金净投入归零不等剩余持仓无市值回撤、流动性或其他经济风险，未作为风险理论证明。', ambiguity='cash_basis_zero_not_all_economic_risks_zero')
c(35, 'large-buy-sell-is-sublevel-or-below-not-necessarily-direct', '261-b003 261-b004',
  '买卖点级别定理说，大级别买卖点必是次级别以下某一级别的买卖点；未必是直接次级别，原例30分端点可落在1分b上。',
  '缠中说禅买卖点级别定理|买卖点|次级别|级别|走势分解', 1, '以下按包含直接次级别及更低层理解；大点必落某小点不是任意小点都必转大点，也不保证一分背驰每次引发大级下跌。')
c(35, 'buy-sell-level-proof-endpoint-completion-outline', '261-b004',
  '作者以(B3+b)的极限点在b上说明定理：若该点非b买卖点，b尚未完成仍延伸，它也就非(B3+b)的极限点，形成矛盾。',
  '缠中说禅买卖点级别定理|完成|走势终完美|买卖点|走势分解', 2, '原称具体证明不写而给例证，此处保留推理纲要，未替作者补完任意路径、极限存在或所有完成标准的数学证明。')
c(35, 'all-level-alignment-only-most-standard-coarse-theorem', '261-b004',
  '作者说最规范走势中大级别买卖点可刚好也是下面所有级别的买卖点，同时称当前买卖点级别定理粗糙，后续会更精细。',
  '缠中说禅买卖点级别定理|买卖点|级别|同步共振', 3, '最规范情形不能改成所有大买卖点必在每级同步，也不能据未出现全级共振就否认原定理。')
c(35, 'mar9-five-top-divergence-expands-new-thirty-from-mar7', '262-b001',
  '3月9日午间作者将5分顶背驰后的走势判为昨日三买后两可能之一：演化成较大中枢，新的30分中枢从3月7日13点多2911算起。',
  '背驰|第三类买点|中枢扩展|走势中枢|操作级别', 1, '具体作者时点判例，旧30分与新30分分开；不说三买失败必立即反趋势，也不用3/13后图证明作者3/9已知后行情。',
  ['2007年3月9日11:54:01解盘'], figs=[(262, 1)])
c(35, 'mar12-thirty-extension-third-buy-and-two-next-paths', '262-b003',
  '3月12日作者说走势是上周五完成30分中枢的延伸；若5分回试不跌破2911中枢上沿，则要形成三买，之后可中枢新生续涨或扩成日线。',
  '中枢延伸|第三类买点|中枢新生|中枢扩展|走势预测', 1, '回试完成及边界仍须看具体走势；是候选后继两支而非三买保证上涨，2911非所有中枢通用阈值。',
  ['2007年3月12日15:20:28指数具体结构'], figs=[(263, 1)], ambiguity='dated_third_buy_and_new_center_or_daily_expansion_conditional')
c(35, 'five-day-line-strength-fallback-not-center-definition', '262-b003',
  '对尚不会看图者，作者在该次指数解盘中给5日线不破则强势的简便观察口径。',
  '均线|确认|操作熟练程度|技术分析', 3, '具体历史辅助判断不等中枢或三买定义，更不构成一切标的跌破/不破均线的收益规则。')
c(35, 'mar7-thirty-center-running-type-less-common', '263-b001',
  '答2911位置时作者指向3月7日，说这30分中枢是较少见的奔走型，和下面那个常见形态不同。',
  '奔走型|走势中枢|操作级别', 2, '以作者指认固定案例为范围，不从较少见推出概率，也不以图形类别推翻三个次级类型重叠要求。', figs=[(263, 1)])
c(35, 'two-thirty-centers-below-2858-and-2911-up-or-a-prime-b', '263-b004',
  '作者说这次上涨有2858下和2911下两个中枢，构成30分上涨；当时要判断继续上涨还是演化成a`+B。',
  '走势中枢|上涨|走势类型|走势预测|中枢扩展', 1, '两个30分中枢与内部5分图框不混，未来a`+B是可能重分，非已确立终局或两个中枢必升格。',
  ['2007年3月12日15:52:31答复'], figs=[(263, 1)], ambiguity='dated_continuation_or_a_prime_plus_B_not_unique_forecast')
c(35, 'ex-right-gap-treat-as-lowest-down-new-center-usual', '263-b007',
  '对除权向下缺口，作者允许当最低级别下跌，之后新中枢按一般下跌中新中枢及原定义处理。',
  '缺口|复权|最低级别|下跌|走势中枢', 1, '是作者对缺口的结构处理口径，没有给前复权/后复权数据算法；不把任意缺口本身算成完整高层三段。')
c(35, 'gap-below-old-center-can-third-sell', '263-b007',
  '若缺口在原中枢下方不远处，作者说仍可按第三类卖点观察和操作，并举假填权为需识别情境。',
  '缺口|第三类卖点|走势中枢|复权', 2, '原称有些缺口与可按三卖处理，非所有除权一跳即完整三卖；仍保留离开、次级回抽等定义，不据假填权措辞断任何发行人欺诈。')
c(35, 'review-single-error-before-repeat-and-improve-method', '263-b010 264-b000',
  '对读者交易不佳，作者要求一次失误就马上总结，连续失误说明方法需改进，应想清再操作。',
  '操作熟练程度|操作策略|市场心理', 2, '这是训练建议而非统计上连亏必然证明方法无效，也未回答读者两只股票可否中线持有。')
c(35, 'diagnose-too-small-level-frequency-blindspot-news', '264-b001',
  '作者列举方法问题：操作级别过小、未按买卖点、参照过频、图形不熟、有盲点和听消息等，要求先识别具体问题。',
  '操作熟练程度|操作级别|买卖点|市场心理', 2, '列举为该答疑反思入口，不把读者已真实具备全部问题或列举穷尽所有交易风险。')
c(35, 'self-review-not-market-blame-author-normative', '264-b002',
  '作者用失误原因永远与市场无关、只能找自身原因的强措辞要求交易者自我反思。',
  '操作熟练程度|市场心理|市场风险', 3, '按责任训练主张保存，非已证所有损失都与市场、规则或通道无关的因果结论。', ambiguity='normative_self_review_not_universal_loss_causation')
c(35, 'mar8-2871-third-buy-then-new-thirty-from-mar7-2911', '264-b006',
  '3月12日作者回顾3月8日2871形成三买，其后向上并扩成30分中枢，新中枢仍从7日2911起算。',
  '第三类买点|中枢扩展|走势中枢|当下', 1, '作者本次明确指认2871，与34读者猜点未被认可分开；图2871.98仅图标价，不静改正文整数或据后结果倒造3/8全路径。',
  ['2007年3月12日16:28:30回顾具体案例'], figs=[(264, 1)])
c(35, 'on-spot-context-learning-for-intuition', '264-b006',
  '作者强调其解盘针对当下具体语境，认为当时全身关注的理解比回头干读理论更有助形成直觉。',
  '当下|操作熟练程度|市场心理', 3, '这是学习经验评价，不证明实盘训练总优于回测，也不由任何走势逃不过理论等话推出已验证完备性。')
c(35, 'mar12-near-2911-not-above-not-third-buy-next-retest', '264-b007',
  '作者说当日早跌在2911附近止住但未在其上，故还不算三买；又5分上去后，次日若5分回拉不跌破2911，再形成新三买。',
  '第三类买点|确认|次级别|走势中枢', 1, '保留附近不等在上及次日若条件，不从本例补全触边相等的普遍严格不等式。',
  ['2007年3月12日16:28:30当时与次日条件'], figs=[(264, 1)])
c(35, 'third-buy-after-second-center-not-guaranteed-up-daily-possible', '264-b007',
  '作者强调即使随后形成三买，也不意味着一定继续上扬，尤其第二中枢后仍可能演化为更大级别日线中枢。',
  '第三类买点|中枢扩展|走势预测|走势中枢', 1, '第三类买点定义不包含保证单边上涨或保本；扩成日线中枢仍为当时可能而非完成事实。',
  ['所论第二30分中枢之后的演化'], figs=[(264, 1)], ambiguity='third_buy_then_daily_center_possible_not_guaranteed_rally')
c(35, 'second-thirty-center-range-2892-2911', '265-b003',
  '作者对相邻读者问题作肯定并明确给出第二个30分钟中枢区间为2892到2911。',
  '走势中枢|价格区间|操作级别|奔走型', 1, '这是该例区间，不把读者ZG等于任意第一段最高点的整段猜测提升成普遍定义；保留整数与图2892.40/2911.41之别。',
  ['2007年3月12日16:31:55答复'], figs=[(263, 1), (264, 1)])
c(35, 'upward-running-second-high-third-slight-break-first-high', '265-b006',
  '本课将向上奔走型描述为第二段特别高，第三段下跌稍微跌破第一段高点的形态。',
  '奔走型|走势类型|高低点|重叠', 1, '原第三跌跌破按第三段下跌转述；特别高/一点未给数值，仍非脱离中枢条件的任意三折线，不把反向奔走另添本段。')

keep('259-b010 260-b000', 'upper-l029-c-stage-one-minute-lowest-three-k-only-if-chosen upper-l033-c-stage-strict-level-from-trades-not-fixed-time-periods',
     '35明确严格每笔成交/三同价和分钟实际模本分开，29自选1分三K口径不静合为最严格入口。')
keep('260-b001 260-b002 260-b003', 'upper-l034-c-stage-front-is-back-not-short-reply-referent-unclear',
     '35可明确a+B+b整体30分类型及其内部中枢，不因此事后解成34复合问句前后短答的唯一语法指代。')
keep('261-b001 261-b002', 'upper-l034-c-stage-current-level-by-capital-and-tolerance-not-second upper-l031-c-stage-proportional-loss-and-no-desperate-position',
     '操作级别按具体条件决定，不因低级信号随意改本级；零净现金成本仍非零经济风险。')
keep('261-b003 261-b004', 'upper-l033-c-stage-end-by-divergence-not-necessarily-direct-sublevel upper-l033-c-stage-subminute-pull-important-under-five-thirty-center',
     '35明确大点必为次级以下某小点且非必直接次级，不能把逆命题任意小点必转大点当结论。')
keep('262-b001 264-b006', 'upper-l034-c-stage-mar8-can-return-five-and-expand-new-thirty upper-l034-c-stage-mar8-five-retest-not-back-2858-thirty-third-buy',
     '34未来可能在35变作者事后判例，保留时间和新旧30分中枢不同对象，原预测命题不回写。')
keep('264-b007', 'upper-l033-c-stage-third-buy-center-edge-versus-swing-high-strongest upper-l034-c-stage-third-buy-confirm-look-inside-sublevel',
     '35具体附近未在上仍不三买及次日若回试条件，不擅补所有触边规则；已成三买仍可较大中枢演化。')
keep('265-b006', 'upper-l023-c-stage-running-pullback-description',
     '35明确向上奔走型第二段高第三稍破第一高的结构，与23B/C描述互补，未给量化特别高阈值。')

note('260-b004', 'abstract-mathematics-analogy-context', '量子多数学形式、抽象代数与几何的作者类比已读，后续会说为其安排。',
     '未给抽象代数完整公理系统或量子物理证明，不能从类比认证市场规律为物理定理。')
note('262-b004', 'historical-political-and-market-opinion-context', '作者对两会后心理、深圳走势、机构与中国市场的历史评价已读并保留。',
     '贬称与机构不敢退出的强断言只作历史作者观点，不据此认证机构身份、对抗行动、收益或当前市场结论。')
issue('strict-base-recursion-versus-minute-model', '259-b009 259-b010 259-b011 260-b000',
      '三连续同价成交的严格最低入口与1/5/15/30分钟便利模本不同；最低中枢依次高低和终结是该定义内部，后续笔不能混同成交笔。',
      '与29/33及后续构造分开，追踪完全分类与严格递归全部前提，未自行补成量子/数学完备证明。', True)
issue('single-type-connections-regrouping-and-associative-scope', '260-b001 260-b002 260-b003 260-b005 261-b000',
      '单5分类型不能30分中枢而连接可构大级别；混合小级段可重组，结合非交换；上下上两次操作为例境而非任意折线定理。',
      '接36详读结合运用与完成约束，不将任意小段合并都自动成完整高层，34短答指代仍不唯一。', True)
issue('buy-sell-level-theorem-below-not-all-levels', '261-b003 261-b004',
      '大点必为次级以下某点而非必直接次级，也非所有小点都大点；最规范全级重合不是一般要求，原定理承认粗糙。',
      '接后续精化与小转大结构，保存例证纲要及未给形式证明边界，不把一分背驰普遍当高层反转。', True)
issue('operation-level-cost-regime-and-zero-risk-claim', '261-b001 261-b002',
      '纯理论效率、T+1兑现限制、波幅相对成本误差和本级/部分操作要同时读；零现金成本不等零经济风险。',
      '按历史制度语境，未核当前所有品种规则/实盘收益，原零成本安全只作作者强主张；不回写31/74风险范围。', True)
issue('third-buy-followed-by-expansion-dated-center-range', '262-b001 262-b003 263-b004 264-b006 264-b007 265-b003',
      '2871三买后新30分由7日2911起、区间2892—2911；三买后仍可扩日线。附近不在上不算与次日回试若条件不是通用相等边界已解决。',
      '保留34可能、35事后判例及当天未确认，整数不同图小数；前后中枢与未来a`+B/日线分开。', True)
issue('gap-treatment-running-type-and-reader-endorsement', '263-b007 265-b001 265-b002 265-b003 265-b006',
      '除权缺口可当最低下跌非一跳充分三卖；向上奔走特别高/一点无数值，作者对为具体区间而非读者ZG普遍公式。',
      '未给复权数据算法，不扩真假填权、个股持有建议或读者整段定义；奔走仍需正式重叠和完成条件。', True)
issue('self-review-opinions-not-universal-causation', '263-b010 264-b000 264-b001 264-b002 264-b006',
      '连失误方法有问题/永远与市场无关是作者强训练主张，不是所有亏损归因或心理因果定理；原未推荐读者两股。',
      '保留反思建议、当下学习评价及历史自述，不用其主张抹客观交易风险或认证收益。')
issue('commentary-dates-and-figure-provenance', '261-b004-s01 262-b000 262-b001 262-b002 262-b003 262-b004',
      '6个解盘来源段日期原空，按3/9及3/12头补齐；3图两后行情一同日未核，原文、字符映射与坐标不改。',
      '后图未来K不倒证明预测，同日不等原博客同版作者配图；来源边界限制固定两册。')

relations = {
 'upper-l035-c-stage-level-recursion-breaks-center-type-circular-definition': [('递归定义','级别','qualifies')],
 'upper-l035-c-stage-strict-trade-base-three-same-price-transactions': [('最小级别中枢','成交分笔','defines')],
 'upper-l035-c-stage-three-consecutive-lowest-types-price-intersection-upward-recursion': [('走势中枢','价格区间','qualifies')],
 'upper-l035-c-stage-single-five-type-cannot-contain-thirty-center': [('走势类型','走势类型连接','qualifies')],
 'upper-l035-c-stage-decomposition-two-regroup-at-least-three-direct-sublevels': [('走势分解','次级别','qualifies')],
 'upper-l035-c-stage-type-connection-associative-not-commutative': [('走势类型连接','结合律','qualifies')],
 'upper-l035-c-stage-large-buy-sell-is-sublevel-or-below-not-necessarily-direct': [('缠中说禅买卖点级别定理','买卖点','defines'),('缠中说禅买卖点级别定理','次级别','qualifies')],
 'upper-l035-c-stage-tiny-level-amplitude-cost-error-no-long-run-meaning': [('操作级别','交易误差','qualifies')],
 'upper-l035-c-stage-partial-lower-level-trades-under-chosen-level': [('操作策略','次级别','qualifies')],
 'upper-l035-c-stage-ex-right-gap-treat-as-lowest-down-new-center-usual': [('缺口','最低级别','qualifies')],
 'upper-l035-c-stage-third-buy-after-second-center-not-guaranteed-up-daily-possible': [('第三类买点','中枢扩展','qualifies')],
 'upper-l035-c-stage-upward-running-second-high-third-slight-break-first-high': [('奔走型','高低点','defines')],
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
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], '读者2911提问、除权缺口、个股中线持有及奔走型猜测只作相邻回复对象；作者未推荐读者股票，短答的认同不扩大为读者整套定义。'
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
        'note': '严格成交递归与分钟模本分开，单个类型和多类型连接分开；结合律不等交换律，次级别以下非必直接次级别，历史T+1/零成本和具体三买的未核或条件保存。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True, reviewer=REVIEWER, visual_review_note=f['note'],
             figure_source_review='本课3图全部查看，262及264右端3/13晚于文字，263同日3/12仍原发未核；不以后图抹作者当时三买/日线中枢的条件。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 56 and Counter(x['lesson_number'] for x in ledger) == {35: 56}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [35], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(259, 266)), 'figure_objects_viewed': 3, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '35课56段7页3图及前后课边界同模型四轮；6解盘来源日期补齐，严格递归/分钟模本、单类型/连接、结合非交换、次级别以下定理和三买后扩展范围分开，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


