"""Materialize the main agent's four-pass reading of lesson53.

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
BASE = 'c_stage_l053'
REVIEWER = 'Codex 主代理 / 阶段C上册53课同模型四轮复核'
SOURCE_SHA = '8c5ac90bf36cd1b19f231bf5c065533ddca8c81ff783dcf37e0a7b094baa462b'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-053' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 57
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 396 AND 400 ORDER BY pdf_page,id', (DOC,))]
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
    pending.append({'id': 'upper-l053-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})


c(53,'recursive-center-definition-required-foundation','396-b012','作者要求先明白中枢的递归定义，称其为继续分析的基础。','递归定义|走势中枢|级别',1,'不以三根周期K线重叠替代至少三个连续完成次级走势类型；本段是学习前提，完整定义保留既有17/18课来源。')
c(53,'thirty-view-completed-five-moves-as-unstructured-lines','396-b013 397-b000','三个5分级别走势重叠构成30分中枢；在30分观察或操作中，把已完成的5分走势视为无内部结构线段，其高低点对应5分走势高低点。','操作级别|走势中枢|次级别|高低点|完成',1,'线段是本段粗粒度观察的比喻，不直接等于后来特征序列定义的结构线段；高低点非必为更小级别原始切分端点，完成条件不可删。',conditions=['30分钟观察/操作','5分钟走势已经完成，在线段化视角暂不看其内部结构'])
c(53,'one-level-regroup-extremes-not-all-finer-level-endpoints','396-b013 397-b000','从1分看5分走势，其高低点未必在原始开始/结束；可用1分结合律重组使高低点归端点，但再用分笔看仍有内部细节。','结合律|走势分解|操作级别|高低点|成交分笔',1,'总能归端点限所选1分重组后的视角，不证明任意原始接点天然极值，也不强定所有更细级别同时共用边界。')
c(53,'switch-magnification-for-divergence-leg-and-third-point','397-b001','30分进入背驰段可放大观察以区间套定位；判断30分第三类点须转看次级5分。每选一个级别，先把其下一层当线段。','操作级别|区间套|背驰段|第三类买卖点|次级别',1,'固定级别不禁止为具体判断目的下钻；不能把30分周期图本身当已包含精细5分完成信息，与52需1分判断5分完成的边界并存。',conditions=['30分钟背驰段细定位，或30分钟第三类点涉及5分钟判断','下钻时另换观察级别，保留上层操作目的'])
c(53,'strict-tick-bottom-up-possible-not-mandatory-every-analysis','397-b002','作者承认可从最低级分笔逐步组合得到最精细严格分析，但认为过累且无必要；不违理论基础时应选更简单用法。','最低级别|成交分笔|走势分解|操作级别',2,'方法选择非删除递归要求或可任意混年线/1分；不是要求所有查询必须重新抓逐笔数据。')
c(53,'consolidation-divergence-extends-strength-comparison','397-b003','作者区分背驰的基础地位与盘整背驰：后者推广前者的力度分析，主要用于中枢震荡力度比较。','背驰|盘整背驰|中枢震荡|指标对比',1,'不把盘整背驰与同级趋势背驰、第一类点完全等同；推广的是力度比较方法。')
c(53,'a-B-c-both-legs-viewed-as-B-oscillation-retrospective','397-b003','在a+B+c中，作者说a和c的盘整背驰都可视为B的中枢震荡，即使a发生时B尚未出现。','盘整背驰|中枢震荡|走势分解|当下',1,'回看分解口径不等当时已经完成B或能够预知B；不删a存在时B未出现的时序限制。',ambiguity='retrospective_center_oscillation_view_not_B_known_when_a_occurs')
c(53,'all-three-root-first-at-different-levels-not-same-label','397-b004','三类买卖点归根可归到不同级别的第一类点；作者仍在同一级别上保留三类区别，因为跨级点意义不同。','第一类买卖点|第二类买卖点|第三类买卖点|操作级别',1,'不把同级第二/第三类点直接重命名同级第一类；和52根于一类保持同一跨级范围，17买点/卖点原措辞歧义未以本句静修。')
c(53,'reaction-time-costs-require-coarser-level-three-equally-important','397-b004','作者说按分笔穷尽所有细波动在实际中因反应时间、交易成本等不可能；须忽略部分波动，统一较大级操作，同一级别的三类点都重要。','操作级别|交易成本|交易条件|买卖点',1,'同级三者均重要不否认在特定存在一类或小转大场景的一/二类优先次序；理论可操作性为作者立场，不证交易无误差。')
c(53,'first-point-is-divergence-at-selected-level','397-b005','作者定义第一类买卖点为该级别的背驰点，并指出其不足以应对该级别没有一类点的小级别转大级别。','第一类买卖点|背驰|小级别转大级别|操作级别',1,'无同级一类见同段末明确文字；中间并触及与所以无须操作有字面张力另存，不暗补未字；不是小级背驰自动等于大级第一类。',ambiguity='literal_middle_clause_tension_retained_separately')
c(53,'literal-bing-chuji-versus-no-same-level-first-point-unresolved','397-b005','PDF397原句作当小级别背驰时并触及该级别第一类点所以无须操作；同段末又说小转大没有该级别第一类点，两处字面张力仍待核。','第一类买卖点|小级别转大级别|操作级别',1,'实际看PDF397确为并触及，不改并未触及或并不触及；这里只记录原文歧义，不把触及一类也无须操作建成无争议总操作规则。',ambiguity='source_bing_chuji_tension_with_no_same_level_first_point')
c(53,'second-sell-sublevel-down-up-no-new-high-or-consolidation-divergence','397-b005','作者给第二类卖点的一般式：高点后一次级别向下，再一次级别向上，若不创新高或盘整背驰即构成；买点反向。','第二类卖点|第二类买点|次级别|盘整背驰',1,'或为择一条件，不擅改成同时不新高且盘整背驰；次级别是走势类型而非两根K线。本文不另定等高容差/实时完成算法。',conditions=['高点后次级别下行再上行','不创新高或盘整背驰；买点反向'],exceptions=['第二类点并非专为小级别转大级别而设'])
c(53,'first-best-when-present-second-best-small-to-large-no-first','397-b005','存在该级别一类点时作者称一类最佳、二类补充；小级别转大级别因没有该级别一类点，二类成为最佳，并非只为此情形设二类。','第一类买卖点|第二类买卖点|小级别转大级别',1,'最佳是作者按结构机会分类的表述，不是实测收益排序；不与同级三类均重要静合为只用一种点。')
c(53,'second-point-larger-center-claim-next-sublevel-overlap','398-b000','从中枢形成看，作者称第二类点必然要形成更大级别中枢，理由是之后至少再有一次级别走势且必与前两段重叠。','第二类买卖点|走势中枢|次级别|重叠',1,'原更大级别的比较基准不在本段独立给出，不擅定为超过买卖点所属级别一整级；前两段/后段以次级走势看，不改三根K线或第二类点处中枢已完成。',ambiguity='larger_center_relative_reference_and_completion_scope_pending')
c(53,'third-point-center-end-larger-or-move-to-new-same-level-center','398-b000','作者说第三类点用于辨识该级别中枢结束；结束后可转更大中枢，或继续上涨下跌直到形成新的该级别中枢。','第三类买卖点|走势中枢|中枢扩展|中枢新生',1,'三买不等后必持续上涨/必出新同级中枢；两种分支保留，原段新中枢未说明第三类点时已经完成。')
c(53,'between-second-third-is-oscillation-trades-use-lower-level-points','398-b000','作者说同级第二、第三类点之间为中枢震荡，期间没有该级别买卖点，参与其中使用的是低级别点。','第二类买卖点|第三类买卖点|中枢震荡|操作级别',1,'没有该级点不等完全没有低级别机会；本句按本段三类点形成顺序解释，不推广为每两个任意二三点之间所有走势无条件一个中枢。')
quote_overrides['398-b001']=passages[pid('398-b001')]['text'].rstrip('*')
c(53,'oscillation-optional-for-time-skill-large-funds','398-b001','作者说可只按预设买卖点、不参与中枢震荡；大资金或有足够时间和熟练度者可参与，且称中枢级别足够时利润往往更大稳定。','中枢震荡|操作熟练程度|交易容量|操作策略',1,'选择条件必须保留；往往更大稳定为作者经验论断，未有样本/费用/风险检验，不改为全部人所有震荡都应参与。')
c(53,'literal-bing-yiding-participation-and-skilled-capacity-context','398-b001','趋势中一般小级别点的句子原写并一定要参与，后又说特别熟练或大资金同样可参与；本条保原字，不替作者补不字。','操作级别|买卖点|操作熟练程度|交易容量',1,'PDF398确为并一定要，不自动规范为并不一定要；语法/上下句张力与本课回复技术通道门槛并存，不建无条件人人强制做小级波动。',ambiguity='source_bing_yiding_participation_wording_not_silently_negated')
c(53,'small-level-utilization-zero-cost-chips-capacity-position-detail-deferred','398-b001','作者说熟练或大资金参与小级别可为提高利用率、加快成本变0或增筹码，但受该级容纳资金量约束，仓位调配细节留待后文。','交易容量|仓位|零成本持仓|操作熟练程度',1,'目的不等保证达到零成本/无风险，也未给此处量化仓位公式；不能以资金大为无限小级容量通行证。')
c(53,'may23-4129-at-0945-1045-break-still-needs-confirmation','398-b002','5月23日作者指09:45及10:45在4129表现，10:45后横拉7、8分钟再上行；同时说突破4129仍需确认，当前可看5日线。','1429点历史压力线|确认|均线系统|价格区间',2,'特定历史走势复述，不用7/8分钟横拉定义所有有效突破；作者仍需确认不可删，未读未来行情替其补完成。')
c(53,'tiny-level-conditional-skilled-smooth-channel-thirty-usual-five-floor','398-b009 398-b010','作者说并非任何时候可操作，太小级别有些不能做；除非技术特别好且通道特别顺，否则别做太小级别。普通技术按30分、最低不小于5分，尤其散户通道慢。','操作级别|交易通道|操作熟练程度|散户|交易条件',1,'5分下限是这段普通技术/散户执行建议，不定义宇宙最低走势级别或否定所有熟练者1分研究；特别好与特别顺均要，不能只满足其一。',conditions=['一般技术或散户通道不顺的操作场景','极小级别例外须技术特别好且通道特别顺'])
c(53,'chase-price-replaced-by-points-daily-third-author-100-profit','398-b011 399-b000','作者以有无买卖点替代追不追高的说法，称日线级上涨股最晚在日线三买介入，并使用最安全、100%获利的强表述。','追高|第三类买点|操作级别|市场风险',1,'保原100%为作者理论性断言，未证实际收益/费用/误认/成交风险为零；前提上涨日线和真正日线三买不可删，不推广任意高价买入必赚。',ambiguity='author_absolute_profit_claim_not_empirical_or_execution_guarantee')
c(53,'miss-daily-third-lower-entry-operability-worsens','398-b011 399-b000','错过日线三买，作者说可按30分、5分甚至1分的小级别找介入位置，但级别越小可操作性越差。','第三类买点|操作级别|交易条件|交易通道',1,'小级别另有其点且操作约束不同，不把小买点冒充错过的大级三买；总能找到为作者机会论述非任何个体即时可成交保证，仍受本课技术与通道门槛。')
c(53,'stock-432-double-then-adjust-case-rhythm','399-b003','对读者问432未动，作者答两倍后要调整、股票有节奏，应动时自然会动。','操作节奏|调整|操作策略',3,'读者代码/矿产猜测保上下文，不代作者确认矿权；两倍后是该股历史答复，级别/时间未给，不立所有股票涨100%必调整的硬阈值。')
c(53,'two-stock-time-offset-rotation-permitted-with-skill','399-b006','对利用两股时间差互动的提问，作者认可可行，关键在技术过关。','操作熟练程度|操作策略',2,'相邻读者399-b005明确两股互动，不擅加必属同一板块或套利零风险，未给换股时点/成本/容量规则。',ambiguity='short_reply_requires_reader_two_stock_context')
c(53,'five-day-usual-three-day-slow-reference-for-beginners','399-b012','对5日线破否，作者说一般看3天确认，但反应慢，只是参考；初学者可看5日线持股，关键仍是学好后面理论。','均线系统|确认|操作熟练程度',1,'一般不是绝对；不把3天写成读者连续三根5分K或47缺口三天规则，未在本段规定收盘价/盘中价/三天边界。')
c(53,'exrights-short-adjust-long-large-may-ignore','399-b015','作者认为除权除息仍反映在走势中、分析同一般股票；前后有大缺口时短期可以复权，时间长或看大级别则可不管。','复权|缺口|操作级别|技术分析',1,'短期/长时未定量，未给前复权/后复权参数；与28大体相近但不以日期覆盖15在5/10系统日线不用/周月可复权的不同范围。',ambiguity='adjustment_scope_vs_l015_l028_not_unified')
c(53,'unfamiliar-sell-first-rebuy-author-no-loss-context-not-global-guarantee','400-b000','对降低成本失手的读者，作者建议不熟悉可先卖后买，卖错也无所谓，并说至少不用亏钱、股票很多不用困在一棵树。','操作策略|市场风险|成本|操作熟练程度',1,'原不用亏钱是该顺序建议的强语，不证明持仓原亏/费用/回买/踏空风险消失；读者失手50%为自述非作者绩效或完整策略认可。',ambiguity='author_no_loss_wording_in_sell_first_context_not_all_risk_elimination')
c(53,'may23-first-bull-phase-not-second-growth-not-leading','400-b003','5月23日对农业股是否牛市第二轮，作者认为第一轮尚未结束，第一轮内成长股也能表现但不是主角。','牛市阶段|成长性|板块轮动',3,'历史作者阶段判读，未外核也不作为当前市场状态；农业发动读者问句不当全部行情已经查证。')
c(53,'three-one-minute-bars-overlap-not-center-unless-lowest-assumption','400-b006','作者说最终都要形成中枢，并特别指出若不把1分视为最低级别，三根单位K线重叠也不等有中枢。','最低级别|走势中枢|K线|递归定义|走势终完美',1,'这个自然指紧前无连续3K重叠问题的短答；不将读者无重叠即永无1分趋势的全推论当作者明说，也不倒推任意最低图3K重叠已充分给出严格递归中枢。',conditions=['不将1分钟作为最低级别时，不能以3根K线重叠代替递归中枢','原最终形成中枢与当前尚未形成分开'])

note('398-b003','historical-stock-reminder-context','个股提醒的作者自述，未给可单独抽取技术内容。','不将未指明昨日提醒认证为实际收益、证券事件或新买点。')
note('399-b009','nontechnical-cultural-opinion-context','作者对父辈/文革读书者知识的文化观点。','保留原文供查证，不提取为技术知识或验证群体知识缺陷。')
issue('literal-bing-chuji-and-bing-yiding-source-words','397-b005 398-b001','397原并触及与同段无该级别一类、398并一定要与技能参与条件有字面张力。','已看完整原页，保持原字不补未/不；查其他明确原文更正或语境限定，来源只限两册，不能任意网上版本覆盖。',True)
issue('second-point-larger-center-reference-and-type-completion','397-b005 398-b000','二卖下后上、不创新高或盘背为择一；二类后更大中枢的相对基准/后第三段实时完成、等高容差未全明。','保次级完整走势与K线不同，不把必形成当已经完成，也不擅推出比操作级别必再升整一级。',True)
issue('magnification-endpoints-and-cross-level-first-not-label-collapse','396-b013 397-b000 397-b001 397-b004 400-b005 400-b006','线段化针对完成次级，1分结合律重组端点不强定所有更小级边界；三类根于不同级一类不可并同级；最低级假设决定3K不能代中枢。','比对52精确5分完成需1分图与17/18递归定义；短答这个自然不把读者全部趋势推论收进作者命题。',True)
issue('small-level-skill-channel-capacity-and-absolute-profit-wording','397-b004 398-b001 398-b009 398-b010 398-b011 399-b000 400-b000','反应时间、费用、技术且通道、资金容量限制，与100%获利/至少不用亏钱的理论性强语均需并列。','原强语保身份而非实盘实证；无费前费后样本或实际成交保证，仓位调配明言后说，不自补资金公式。',True)
issue('exrights-scope-vs-prior-average-system-and-long-view','399-b014 399-b015','53短期可复权/长时大级可不管与28范围相近，15的5/10均线日线/周月口径不同，未明确作者修订。','保独立原文、情境和歧义，不能只按后日期覆盖或合成所有周期通用复权开关。',True)
issue('historical-4129-three-day-reference-and-short-affirmations','398-b002 399-b003 399-b005 399-b006 399-b012 400-b003','4129当天09:45/10:45、7/8分横拉还需确认；三天5日线一般且慢；432翻倍/牛市阶段、两股互动短答都有明确历史或邻问范围。','不立通用7分钟突破/100%涨幅阈值；保读者身份和作者短答上下文、一般/参考程度，不宣称当前金融事实。')
relations={
 'recursive-center-definition-required-foundation':[('走势中枢','递归定义','requires')],
 'thirty-view-completed-five-moves-as-unstructured-lines':[('操作级别','完成','requires')],
 'one-level-regroup-extremes-not-all-finer-level-endpoints':[('结合律','高低点','qualifies')],
 'switch-magnification-for-divergence-leg-and-third-point':[('区间套','操作级别','qualifies'),('第三类买卖点','次级别','requires')],
 'consolidation-divergence-extends-strength-comparison':[('盘整背驰','中枢震荡','qualifies')],
 'first-best-when-present-second-best-small-to-large-no-first':[('第二类买卖点','小级别转大级别','qualifies')],
 'second-sell-sublevel-down-up-no-new-high-or-consolidation-divergence':[('第二类卖点','盘整背驰','qualifies')],
 'third-point-center-end-larger-or-move-to-new-same-level-center':[('第三类买卖点','中枢新生','qualifies')],
 'small-level-utilization-zero-cost-chips-capacity-position-detail-deferred':[('仓位','交易容量','qualifies')],
 'tiny-level-conditional-skilled-smooth-channel-thirty-usual-five-floor':[('操作级别','交易通道','qualifies')],
 'exrights-short-adjust-long-large-may-ignore':[('复权','操作级别','qualifies')],
 'three-one-minute-bars-overlap-not-center-unless-lowest-assumption':[('走势中枢','K线','distinguishes')],
}
for r in rows:r['relations']=[dict(source=a,target=b,type=t) for a,b,t in relations.get(r['id'].split('upper-l053-c-stage-')[1],[])]
by_passage=defaultdict(list)
for r in rows:
 for e in r['evidence']:by_passage[e['passage_id']].append(r)
for item in pending:item['lesson_numbers']=[53]
ledger=[]
for id,p in passages.items():
 linked,decision=by_passage[id],notes.get(id)
 if linked:
  result,reading='new_claim','；'.join(r['text'] for r in linked)
  atomic=[dict(claim_id=r['id'],conditions=r['conditions'],exceptions=r['exceptions']) for r in linked]
  inverse='；'.join(r['review_note'] for r in linked)
 elif decision:result,reading,atomic,inverse=decision['category'],decision['reading'],[],decision['inverse']
 elif p['role']=='reader':result,reading,atomic,inverse='reader_context','读者署名、成本自述/疑问、两股互动及除权/最低级提问全部已读，保相邻作者答复对象。',[],'不把读者15.5成本/失手50%/矿权/最低无趋势等问法作作者事实；短答互动许可须技术过关，个股和大盘当前状态均限历史。'
 elif p['text'].startswith('教你炒股票') or p['text'] in ('缠中说禅解盘:','缠中说禅解盘：','缠中说禅回复:','缠中说禅回复：') or re.fullmatch(r'.*200[5678]-\d{1,2}-\d{1,2}.*',p['text']) and (len(p['text'])<75 or p['text'].startswith('缠中说禅')):result,reading,atomic,inverse='source_header','课程、解盘/回复的作者署名和时间头已核。',[],'只作来源身份锚点，不独立支持技术结论。'
 else:raise AssertionError(('unaccounted paragraph',id,p['text']))
 ledger.append(dict(passage_id=id,lesson_number=53,document_id=DOC,pdf_page=p['pdf_page'],role=p['role'],speaker=p['speaker'],published_at=p['published_at'],source_text_sha256=hashlib.sha256(p['text'].encode()).hexdigest(),result=result,claim_ids=[r['id'] for r in linked],related_existing_claim_ids=retained[id],existing_evidence_not_mutated=True,pending_issue_ids=[x['id'] for x in pending if id in x['passage_ids']],reviewer=REVIEWER,rounds={'1_read_and_scope':reading,'2_atomic_conditions':atomic,'3_normalization':dict(concept_labels=sorted({x for r in linked for x in r['concepts']}),related_existing_claim_ids=retained[id],note='三类同级用途与跨级一类不同；完成次级线段化非新结构线段定义；并触及/并一定要原字不修，或条件/最终形成/已完成区分，技能且通道/成本容量限制和作者绝对收益强语并存，复权范围不按后日覆盖。'),'4_reverse_check':inverse}))
assert len(ledger)==57 and len(rows)==30 and len(figures)==0
for suffix,data in [('reviewed.jsonl',rows),('coverage.jsonl',ledger),('pending.jsonl',pending),('figures.jsonl',figures)]:
 (OUT/f'{BASE}.{suffix}').write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in data),encoding='utf-8')
summary=dict(stage='C/E',schema_version=metadata['schema_version'],graph_version=metadata['graph_version'],lessons=[53],document_id=DOC,reviewer=REVIEWER,passages_read=len(ledger),claims=len(rows),evidence=sum(len(r['evidence']) for r in rows),importance_counts=dict(Counter(r['importance_level'] for r in rows)),new_concepts=sorted({x for r in rows for x in r['concepts']}-set(concepts)),whole_lesson_semantic_read_complete=True,technical_extraction_complete=False,four_round_review=True,independent_review_claimed=False,visual_pdf_pages=list(range(396,401)),figure_objects_viewed=0,figure_origin_counts={},pending=[x['id'] for x in pending],source_passages_snapshot_sha256=SOURCE_SHA,retained_source_links_in_ledger_only=True,database_mode='ro',formal_import=False,acceptance='53课57段5页无图同模型四轮；22时间空格规范；三类用途与跨级一类、完成次级观察和放大、二卖或条件、两处原字歧义、执行门槛与绝对收益强语及复权范围待核。')
(OUT/f'{BASE}.summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
db.close();sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(summary,ensure_ascii=False))

