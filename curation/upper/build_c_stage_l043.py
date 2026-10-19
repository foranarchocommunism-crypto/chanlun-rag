"""Materialize the main agent's four-pass reading of lesson43.

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
BASE = 'c_stage_l043'
REVIEWER = 'Codex 主代理 / 阶段C上册43课同模型四轮复核'
SOURCE_SHA = '58de5e1760fcca65b710c76425a114c0d542b5740aff3cd8fbaf232fe1df9b41'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-043' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 57
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 311 AND 316 ORDER BY pdf_page,id', (DOC,))]
assert len(figures) == 2
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
    pending.append({'id': 'upper-l043-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})




















quote_overrides['316-b004']=passages[pid('316-b004')]['text'].split('（注：')[0]
keep('311-b016 312-b000','upper-l029-c-stage-divergence-reversal-theorem-three-outcomes','43重引29课背驰-转折三种结果，既有定理不改证据；本课对类型终止/两种转折再作补充。')
c(43,'turns-relate-to-divergence-but-not-one-to-one-level','311-b016 312-b001',
  '作者说转折必由背驰导致，但背驰引发的转折不一定同级；小级别背驰可逐步累积后导致更大级别转折，二者级别并非一一对应。',
  '背驰|趋势转折|级别|小级别转大级别',1,'作者体系内的普遍陈述，不以某一小级信号直接预言年线调整，未给所有市场经验验证或级别映射算法。')
c(43,'own-divergence-terminates-original-type-next-same-or-higher','311-b016 312-b000',
  '在重引29课定理后，作者解释某级别背驰必使该级别原走势类型终止，继而开始该级别或以上的另一个走势类型。',
  '缠中说禅背驰-转折定理|背驰|走势类型|完成|级别',1,'这里为对应原走势的已成立背驰及类型结束解释，不把刚入背驰段等同已成立；原三结果的文字仍按29课独立可查。')
c(43,'no-up-plus-up-no-down-plus-down-premise','312-b001',
  '作者以不允许上涨+上涨、下跌+下跌作为背驰后走势类型讨论的前提。',
  '走势类型连接|上涨|下跌|走势分解',1,'按本文类型连接语境；没有在此禁止38课本级同级别分解中的盘整+盘整，亦不把连续价格上涨K线当两个已完成上涨类型。')
c(43,'one-minute-top-at-least-one-consolidation-or-down-may-rise-again','312-b001',
  '1分钟顶背驰至少引出1分钟盘整或下跌类型；其中若先有一个1分钟盘整，之后仍可继续上涨。',
  '背驰|操作级别|盘整|下跌|走势类型',1,'已成立1分顶背驰，不等必须形成持续单边下跌或最终年线反转；配图为来源未核示意而非独立定义。',figs=[(312,1)])
c(43,'extreme-yearly-down-by-gradual-expansion-not-direct-minimum-cause','312-b001',
  '作者举极端可能：1分钟顶背驰后形成的盘整或下跌可逐步扩张成很大级别下跌，但不能把年线下跌直接归因为那个1分钟背驰。',
  '小级别转大级别|背驰|中枢扩展|年线|趋势转折',1,'可能而非每次必然，须实际后续结构逐步扩张，不由小信号当下充分预言年线结果。')
c(43,'divergence-level-not-above-containing-current-move','312-b002',
  '背驰级别不可能大于其所处当下走势类型级别，30分钟背驰只能出现在至少30分钟级别的走势类型中。',
  '背驰|级别|走势类型',1,'比较的是背驰与其包含走势类型，不是所用图表周期或背驰以后最终转折级别。')
c(43,'same-level-divergence-pulls-last-center-break-corresponding-extreme','312-b004',
  '若30分钟走势类型出现30分钟背驰，作者说至少把走势拉向该走势最后一个中枢，并跌破或升破相应高点或低点。',
  '背驰|走势中枢|操作级别|有效跌破|高低点',1,'同级已成立背驰和对应方向，原相应高低点不擅换成任意中枢上下沿；下文进入背驰段还可能失效，不把尚在候选段的信号自动等同必回中枢。',
  ['背驰级别等于当下走势类型级别','相应级别背驰已经成立'])
c(43,'entering-divergence-segment-not-guaranteed-divergence-small-extension','312-b004',
  '30分钟走势进入同级背驰段，并不保证最终背驰；小级别延伸可使大级别最终摆脱背驰，需要当下跟踪判断。',
  '背驰段|背驰|走势延伸|当下|级别',1,'候选段与已成立背驰分开，不能先按必返中枢交易再说失效；保留本段同级走势语境。')
c(43,'smaller-case-thirty-no-divergence-c-has-one-minute','312-b006',
  '第二种情况以30分走势明确没有30分背驰为前提：向上a+A+b+B+c的A、B为30分中枢，c对b无30分背驰，但c内可有1分背驰。',
  '小级别转大级别|背驰|背驰段|走势中枢|级别',1,'保留当前大级背驰段最终不成立与小级实际背驰两个状态，不因c小背驰自动改判c对b大级背驰。')
c(43,'smaller-turn-can-return-B-via-bigger-than-one-center','312-b006 313-b000',
  '上述c内1分背驰并不保证其后永不回到B；若最终回B，第二种路径须先形成比1分更大的中枢，再向下突破。',
  '小级别转大级别|中枢扩展|趋势转折|走势中枢',1,'若最终回B才是所述必经路径，不把形成较大中枢当必然下破/回B；按作者例，非自造所有市场充分路径。')
c(43,'larger-center-after-small-divergence-may-break-up-extend','313-b001',
  '与同级背驰回跌必然不同，小级背驰后即使形成比1分更大的中枢，也未必回跌；可向上突破，使原a+A+b+B+c继续延伸。',
  '小级别转大级别|背驰|走势延伸|走势中枢',1,'充分与必要范围分开，不从形成较大中枢推导大级反转，反之也不由继续延伸否认当时的小级背驰。')
c(43,'climax-small-divergence-large-turn-author-historical-examples','313-b001',
  '作者特别提醒趋势冲顶或赶底的小级背驰，称这类一般引发大级转折，举2007年1月4日工行、2006年12月7日北辰实业、2007年1月22日水井坊。',
  '小级别转大级别|趋势转折|背驰|走势预测',3,'一般未给样本率或确认阈值，三例仅作者历史判读，本课未提供其原价数据；不把冲顶赶底的事后标签作预测充分条件。',ambiguity='author_climax_large_turn_frequency_and_examples_unverified')
c(43,'same-level-type-boundary-at-divergence-smaller-case-more-complex','313-b002',
  '30分走势由30分背驰完成时，前后类型以该背驰点分界；小级背驰引发大级转折的分解较复杂，但须遵守同一分解原则。',
  '走势分解|完成|背驰|小级别转大级别',1,'不把所有小背驰即时作为大级类型边界，后面的B/C重合/未重合决定不同处理。')
c(43,'decomposition-principle-no-higher-center-inside-one-type','313-b003',
  '缠中说禅走势类型分解原则：某级别走势类型内不能出现更大级别中枢；一旦出现，原段应属更大级别走势类型一部分，或几个本级类型的连接。',
  '缠中说禅走势类型分解原则|走势分解|走势类型|走势中枢|级别',1,'给两种结构归属而非都强制成单一更高类型；本课不提供全数据自动分解和所有完成判据。')
c(43,'C-thirty-no-overlap-B-original-thirty-unfinished-extends','313-b005',
  '向上30分a+A+b+B+c中c内1分背驰后，若演化出30分中枢C且与B无任何重叠，原30分类型尚未完成，将延伸为a+A+b+B+c+C，须等完成再分解。',
  '同级别分解|走势分解|走势延伸|完成|走势中枢',1,'A/B/C为所设中枢，必须无任何重叠条件；不把新C一出现立即结束原30分类型，也未规定等待固定K数。',
  ['向上30分a+A+b+B+c、c内1分背驰后所设例','演化出的30分中枢C与B没有任何重叠'])
c(43,'B-C-overlap-evolves-daily-not-already-formed','313-b005 316-b004',
  '若30分中枢B、C有区间重合，原式可结合成a+A+b+（B+c+C），后者必然演化为日线中枢；作者随后明确这不等于（B+c+C）已经形成日线中枢。',
  '中枢扩展|结合律|走势中枢|完成|级别',1,'联合正文与4/9作者澄清，只引用316段注前作者句，排除禅师的意思为进行式非完成式夹注；演化与已成分开，不用整理注当作者证据。',
  ['本例两个30分中枢B/C存在区间重合'])
c(43,'overlap-original-part-daily-fixed-thirty-boundary-small-divergence','313-b005',
  'B/C重合例中原a+A+b+B+c是日线类型一部分；若坚持30分同级分解，分界取那1分背驰点，a+A+b+B+c+C=（a+A+b+B+c）+C。',
  '同级别分解|走势分解|小级别转大级别|结合律|完成',1,'保留若按固定30分视角及所设重合条件；符号C先为中枢后在分解式表后续段，具体完成不能因同名推定，另答C不一定完成。')
c(43,'C-not-necessarily-complete-expanded-division-normal','316-b005',
  '对分解式中的C是否未完成及扩展后如何划分，作者答C不一定完成，扩展后划分与一般中枢正常划分没有区别。',
  '完成|中枢扩展|同级别分解|走势分解',1,'不一定完成不是必然未完成，也不等当前已成完整30分走势类型；未在短答列全部区间/确认算法。')
c(43,'MACD-zero-return-up-initial-segment-yellow-white-high-unknown','315-b000',
  'MACD作辅助时，回0轴再上去可先看成进入背驰段，作者举当时大盘日线；刚开始无法知道黄白线最后会否创新高，要看小级结构。',
  'MACD|背驰段|当下|级别|确认',1,'先看成候选而非预先确认背驰或充分买点；不撤42特例首次归零一定买回的原字，但该强指令的完整条件仍待核。')
c(43,'strong-small-structure-new-yellow-white-high-no-divergence','315-b000',
  '若小级走势特别强，使MACD黄白线创出新高，作者说就不存在此前所候选的背驰。',
  'MACD|背驰段|背驰|走势延伸|确认',1,'沿同答回轴后再上行的候选段语境，不以任意不同时标黄白线新高取消其他级别已成立背驰；本答未给强的数值阈值。')
c(43,'apr6-pressure-attacked-not-yet-break-stand-ten-thousand-conditional','313-b007',
  '4月6日作者称深圳已冲击压力线但未突破站上；若突破站稳，才谈向1万点推进。',
  '高点连线|确认|走势预测|宏观市场判断',4,'历史条件性判断，冲击不等有效突破，万点预测不由后加图认证，军事比喻不核真实机构。',figs=[(314,1)])
c(43,'apr6-second-line-spreads-beyond-ten-consolidation-earnings','313-b009 313-b010 314-b000',
  '作者说当时10元上下二线带动15、20、30元乃至更高二线，故不必限10元，盘整到位且业绩支持者可启动并给下一轮三线腾空间。',
  '二线股|三线股|板块轮动|基本面|走势预测',4,'是作者历史盘面解释和预期，盘整/业绩条件未给量化阈值；不由价格直接判断品质或认证其资金造成市场变化。',figs=[(314,1)])
c(43,'apr6-no-chase-policy-influence-uncertain','314-b001',
  '作者重申应选买卖点、不要追高，特别散户否则小震荡也可能出问题；当时政策影响有不确定性。',
  '买卖点|追高|政策风险|市场风险',2,'当时风险提醒，未认证其描述对手的具体游说行为或当下政策。')
c(43,'apr9-gap-break-needs-confirmation-gap-pullback-pressure','314-b003',
  '4月9日作者称深圳以缺口突破高点连线，上海随之走强，但突破有效性仍需确认，缺口回拉力量是短线主要压力。',
  '缺口|高点连线|确认|市场震荡',2,'已出现缺口不等确认完成；没有给统一确认天数/幅度，也不从配图后行情补当时已知结果或认证各方因果。',figs=[(314,1)])
c(43,'apr9-rotation-short-oscillation-skills-five-day-fallback','314-b004',
  '作者认为良性轮动保持则当时大盘问题不大，但短线震荡难免；有能力可按短线指标操作，技术不足者5日线不破先观察。',
  '板块轮动|市场震荡|均线系统|操作熟练程度|操作策略',2,'历史条件性意见，不核业绩将公布的预测，不把5日不破证明零风险或每次短线都可成交获利。')
c(43,'apr9-only-policy-large-oscillation-author-strong-view','314-b005',
  '作者当时把可能引发大盘大震荡的唯一因素归于管理层态度，并认为过严转变不太会出现、自身不会受害。',
  '政策风险|宏观市场判断|市场风险|走势预测',4,'唯一/自我免疫为作者强判断，未枚举或排除所有风险，不认证管理层决定、未名对手或实际抗风险收益。',ambiguity='author_only_policy_risk_and_self_immunity_unverified')
c(43,'rough-exit-after-break-wait-rebound-not-chase-down-can-still-new-high','315-b004',
  '对读者在小转大特殊情况跌破后等反弹不破前高或盘背再退出的粗法提问，作者认可不能杀跌，并提醒仍可强力不背驰创新高。',
  '同级别分解|盘整背驰|卖点|操作策略|高低点',1,'读者引文与提问保留读者身份，认可有相邻问答范围；不把破位立即抛或任意延后持仓当通用规则，未给全部强力例外/EPS。',
  ['对应读者4月9日关于同级分解特殊情况的粗法提问'])
c(43,'fine-method-can-exit-before-break-mechanical-rougher','315-b004',
  '作者说精细方法可以不等跌破先走；机械化程序通常较粗糙，和上述反弹退出的粗法不矛盾。',
  '机械化操作|操作熟练程度|卖点|同级别分解',2,'本答没有给提前退出的独立算法，不能据此要求对未发生破位精确预测或实盘收益保证。')
c(43,'persistent-mechanical-super-return-author-claim','315-b004',
  '作者称粗糙些的机械化程序只要坚持，也一定有超级回报。',
  '机械化操作|操作策略|市场风险',3,'作者未经实证的强收益承诺，未给区间、基准、费用、回撤、成交及样本；不当保证或历史回测结果。',ambiguity='author_super_return_claim_no_empirical_validation')
c(43,'new-stock-candlestick-pattern-auxiliary-not-point-definition','315-b010',
  '对读者首日新股K线观察，作者称是一种辅助性用法，相当于放量长阳后小阴调整再上涨的K线组合形态。',
  '新股|K线|成交量|技术分析',2,'读者首30分高换手、后三K在首K高位1/3以上为问题前提，作者未逐项证明数字法必赚钱或等同中枢买点；不把辅助当充分信号。')
c(43,'apr9-many-large-caps-below-twenty-PE-author-reply','315-b013',
  '对读者市场50倍市盈率并担忧未来大跌的看法，作者反问很多大盘股连20倍都不到，何以说现在有问题。',
  '基本面|宏观市场判断|市场风险',4,'仅记4月9日作者估值反驳，原都市赢率字样保留于证据；未核股票清单/财报/估值口径，不证整个市场安全或否认所有读者风险。',ambiguity='historical_valuation_reassurance_unverified')
quote_overrides['316-b004']=passages[pid('316-b004')]['text'].split('）')[-1]
assert quote_overrides['316-b004']=='有了结合律，方向都不是最重要的。'
c(43,'associativity-direction-not-most-important-author-tail','316-b004',
  '解释B/C区间重合扩展时，作者补充有了结合律，方向并非最重要。',
  '结合律|中枢扩展|走势分解',2,'只引用夹注之后独立原句，不将禅师的意思为进行式非完成式认作作者；方向不是最重要不等任何区间/级别/完成条件都无关。')

note('311-b015','source-scope-introduction','作者说明本课不重讲基础背驰识别及与盘背区别。','并非这些区别不再需要；先前基础规则仍独立可查。')
note('312-b003 312-b005 313-b004','source_header','两种级别分类及后续分解分析导语已读。','标题本身不证明任意小信号可当大级信号，保留两支不同前提。')
note('313-b006','closing-learning-rhetoric-context','作者以掌纹清晰类比熟悉分解后的读图能力。','清晰可辨为教学比喻，非系统已形式证明/预测正确率100%。')
note('313-b008','historical-unverified-market-party-context','关于对手在市场外活动的作者评论已读。','不猜贬称所指实体或认证幕后活动。')
note('316-b004','mixed-compiler-inline-note-excluded','作者前后原句之外，夹注禅师的意思为进行式非完成式为第三人称整理说明，注者未核。','作者证据分别截取注前或注后，夹注没有进入任何新命题引文；原整段及坐标不改，混合来源身份保留待核，不能把整段一律当作者引文。')

issue('divergence-level-original-type-turn-not-one-to-one','311-b016 312-b000 312-b001 312-b002 312-b004',
      '同级实际背驰终止原类型/回最后中枢，小级可逐步积成大转折；原相应高低点未精确定义，不预言任意1分背驰即年线反转。','保持两支前提，和29/37/41/42及后44比较，不把背驰段候选当已成或盘背一句必破扩为任意下沿。',True)
issue('small-turn-return-B-necessary-path-and-C-overlap-timing','312-b006 313-b000 313-b001 313-b002 313-b003 313-b005 316-b004 316-b005',
      '大级无背驰的小级转折若回B须先更大中枢并下破，但更大中枢也能向上；B/C重合演化日线非已成，C不一定完成，符号中枢与后续段角色待清。','保留两分支及更高级归属/本级连接，接44必要非充分；不私加C完成/全部ZDZG划法或以事后划分预测。',True)
issue('MACD-candidate-yellow-white-new-high-and-first-zero-return','312-b004 315-b000',
      '回零再上先看入背驰段但未来黄白线能否新高未知，小级强可取消候选；强的数值、终确认及42归零必买回完整条件仍不全。','与64候选/已成及42原强语并置，不补全通用买入或能量公式。',True)
issue('rough-exit-rebound-fine-before-break-and-super-return','315-b002 315-b003 315-b004',
      '读者引文/粗法提问获不能杀跌认可，精法可先走但未给规则，机械坚持一定超级回报无实证。','保留反弹/盘背和继续无背创新高例外，跨39/40/42补范围，未补成交/费用/EPS/回撤收益。',True)
issue('historical-forecast-sector-policy-PE-and-new-stock-auxiliary','313-b007 313-b008 313-b009 313-b010 314-b001 314-b003 314-b004 314-b005 315-b008 315-b010 315-b012 315-b013',
      '二线价格扩散/万点/缺口确认、政策唯一风险和大盘PE皆历史意见；新股1/3数值为读者，作者仅辅助K形态认可。','不以后图证预测、认未名对手或估值安全，不替代买卖点定义及当前事实。')
issue('inline-compiler-note-source-role-and-figures-dates','314-b002 316-b004',
      '4/9四段纠正及11作者时间空格规范；两图1后加1未核；316夹注禅师的意思为进行式非完成式为第三人称整理说明，作者/整理混在同一来源段未物理拆开。','新作者证据已排除夹注；原文/映射不改，保留混合来源限制，后续来源分层如拆段需单独备份审计，不把注当原作者完成证明。',True)
relations={
 'upper-l043-c-stage-turns-relate-to-divergence-but-not-one-to-one-level':[('趋势转折','级别','qualifies')],
 'upper-l043-c-stage-own-divergence-terminates-original-type-next-same-or-higher':[('缠中说禅背驰-转折定理','完成','qualifies')],
 'upper-l043-c-stage-divergence-level-not-above-containing-current-move':[('背驰','走势类型','qualifies')],
 'upper-l043-c-stage-entering-divergence-segment-not-guaranteed-divergence-small-extension':[('背驰段','走势延伸','qualifies')],
 'upper-l043-c-stage-decomposition-principle-no-higher-center-inside-one-type':[('缠中说禅走势类型分解原则','走势中枢','qualifies'),('缠中说禅走势类型分解原则','走势类型','qualifies')],
 'upper-l043-c-stage-B-C-overlap-evolves-daily-not-already-formed':[('中枢扩展','完成','qualifies')],
 'upper-l043-c-stage-C-not-necessarily-complete-expanded-division-normal':[('完成','走势分解','qualifies')],
 'upper-l043-c-stage-fine-method-can-exit-before-break-mechanical-rougher':[('机械化操作','操作熟练程度','qualifies')],
 'upper-l043-c-stage-new-stock-candlestick-pattern-auxiliary-not-point-definition':[('新股','技术分析','qualifies')],
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
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], '读者特殊情况引文及反弹退出、新股30分前三K/1/3和估值50倍、B/C重合与C是否完成问题保留读者身份，作者认可保留具体问答范围；316夹注不进入作者证据。'
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
        'note': '同级背驰与小级转大两支前提分开，候选段非最终背驰；B/C重合演化日线不等已成、C不一定完成；316整理夹注排除作者引文，粗法/精法及超额回报强词分层。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=f['note'],
             figure_source_review='本课两整图逐一查看：312示意原发未核，314深成5分图嵌4/6和4/9文而右端有4/10属后加；示意非独立递归证明，后图不证万点预测。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 57 and Counter(x['lesson_number'] for x in ledger) == {43: 57}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [43], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(311, 317)), 'figure_objects_viewed': 2, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '43课57段6页2图及前后边界同模型四轮；4跨日与11空格规范、图1后加1未核；两支转折/候选段与已成、B/C演化与完成分层，夹注不作作者证据，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


