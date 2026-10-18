"""Materialize the main agent's four-pass reading of lesson32.

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
BASE = 'c_stage_l032'
REVIEWER = 'Codex 主代理 / 阶段C上册32课同模型四轮复核'
SOURCE_SHA = 'b66483fbc77110f25ea9679f36e0514449bf0b3cd7d561de9078a24efc74eb8b'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-032' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 131
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 233 AND 243 ORDER BY pdf_page,id', (DOC,))]
assert len(figures) == 5
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
    pending.append({'id': 'upper-l032-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})






c(32, 'objective-long-condition-ends-at-second-leg-divergence', '233-b001',
  '作者反对固定死多死空，以春节前技术上需要中枢第二段为做多条件；第二段出现背驰后，该例继续做多的客观条件便消失。',
  '当下|背驰|走势中枢|操作策略|市场心理', 1, '作者对具体第二段的复述，牛快跌慢涨/熊快涨慢跌为经验节奏而非所有阶段硬定律，不抹31对周线段级别的明确限定。')
c(32, 'zero-cost-no-risk-language-is-author-view', '233-b002',
  '第32课作者把只涨才高兴、下跌便恐惧视为思维问题，重申零成本股票才安全，并称理论不用风险概念而以买卖点与背驰处理。',
  '零成本持仓|买卖点|背驰|市场风险|市场心理', 3, '无风险/唯一途径为作者强观点，不能推导零现金成本无经济风险，也不取消31保持警觉和退出限制；不当本项目已证金融结论。',
  ['第32课作者对操作思维的论述'], ambiguity='author_no_risk_and_zero_cost_safety_claim_not_empirically_proven')
c(32, 'fall-to-third-buy-and-416-gain-case', '233-b002',
  '作者主张大跌后寻找会形成三买的股票，以000416前次下跌后三买、随后一个月约100%含一周假期为例说明节奏。',
  '第三类买点|操作策略|当下|题材股', 2, '涨得最快与100%是当时作者主张，未独立核行情、复权和成交；不是大跌即买或所有三买必同幅上涨。',
  ['第32课000416历史例'], figs=[(233, 1)], ambiguity='historical_gain_and_fastest_rebound_claim_not_verified')
c(32, 'chosen-thirty-level-follow-buy-sell-rhythm', '234-b001',
  '作者以30分操作为例要求在相应顶背驰时按卖点处理、底背驰时按买点处理，避免因还想涨而不卖、跌后恐惧反而卖在底部。',
  '操作级别|买卖点|背驰|市场心理|操作策略', 2, '与选定级别对应而非看到任何更小信号都全仓反向，跳舞和合力是顺势比喻不是保证极值成交。')
c(32, 'a-formed-not-predict-b-required', '234-b002',
  '在30分a+A+b+B+c示意中，A已经走出不能据此预断B必有；b是否退出由b当下结构及与a的背驰比较决定，不由偏好决定。',
  '当下|走势预测|走势分解|背驰|走势中枢', 1, '所写五段是分析示意不是事前完整路径保证，b与a需对应级别和方向，不能把形似短波任意作两段。')
c(32, 'b-structure-no-nested-divergence-wait', '234-b002',
  '作者说通过b的5分和1分结构观察生长，未出现符合区间套背驰条件的结构时继续等待，可能延伸出使30分不再背驰的力度。',
  '区间套|背驰|背驰段|当下|次级别', 1, '“使得背驰不可能”限该a/b比较与当下结构，不等价格永远无卖点或一次未背驰就必无限上涨。')
c(32, 'thirty-a-center-b-at-most-five', '234-b003',
  '在该30分示意中，A已被判定为30分中枢，b不能再含30分中枢，最多是5分级别。',
  '走势中枢|次级别|走势分解|操作级别', 1, '最多5分不等所有连接恰5分，b若包含同级新中枢就须重判分解，不把模板字母赋固定实体。')
c(32, 'five-rise-ends-then-new-thirty-b-expected', '234-b003',
  '若b起始的5分上涨已使30分图上该比较不可能背驰，作者让其继续发展至5分中枢及5分走势背驰，再据此预期新的30分中枢B出现。',
  '背驰|走势中枢|次级别|当下', 1, '5分上涨/本级已排除该背驰/继续发展后的小级背驰为本例前后条件，不能从任意一个5分背驰断言B已完成。',
  ['本例b起始5分上涨已排除所讨论的30分背驰'])
c(32, 'center-b-three-leg-swings-depend-on-capital', '234-b003',
  '对即将形成的B，作者允许按资金操作偏好做短差：第一段后回补，第二段高点看5分或1分背驰退出，第三段再回补，再观察能否向上突破。',
  '资金管理|走势中枢|次级别|背驰|操作策略', 2, '作者给的是本中枢操作示意，第一/第二/第三段须对应实际构造，非任何三次涨跌或任何资金都必获利。')
c(32, 'b-and-c-departures-require-third-buy-not-guaranteed', '234-b003',
  '作者说a或c并非天经地义必有；要从所讨论的30分中枢走出b或c，须有针对该中枢的三买，5分上离后回拉不回中枢则回补等待后续段。',
  '第三类买点|走势中枢|次级别|走势分解|确认', 1, '字母角色随当下结构，不把a/b/c所有命名一律当需三买，也不将突破一根K等同三买；原“a也不必有”保留而不静改为b。')
c(32, 'b-no-divergence-b-center-may-exceed-a', '234-b004 235-b000',
  '在a+A+b阶段不能预知B最终级别；作者说b不背驰时B至少与A同级，也可更大，此时原串不能仍称原级上涨，而要把a+A+b归为a`，改按a`+B理解。',
  '当下|走势分解|中枢扩展|走势中枢|级别', 1, '至少同级与可能更大分开，条件b不背驰不可删；a`+B是重组意义而不是两个中枢必同级的永久模板。')
c(32, 'daily-b-reclassify-c-use-daily-standard', '235-b000',
  '若B扩为日线中枢，作者要求到日线框架判断，后若有c段也按日线标准看背驰，中枢内则可利用次级背驰或盘背做短差。',
  '中枢扩展|操作级别|背驰|盘整背驰|当下', 1, '若有c与B已扩日线均为前提，不能沿用入场30分后永远只等30分背驰，也不声称所有小信号直接导致日线中枢。')
c(32, 'order-book-anomaly-only-in-valid-nesting', '235-b001',
  '作者允许区间套继续研究到盘口，但强调仅在符合区间套的背驰中看盘口异动才有相应意义，不是每次盘口异常都重要。',
  '区间套|背驰|确认|技术分析', 1, '最精确操作成功是作者方法效果主张，未给盘口数据/成交验证；盘口不能替代上级结构与嵌套条件。')
c(32, 'price-framework-can-combine-other-factors', '235-b001',
  '作者称可在基本走势框架内结合基本面、政策面、资金面及庄家等因素，观察它们如何起作用及是否有效。',
  '基本面|政策风险|资金管理|技术分析|当下', 2, '这是与其他分析结合的范围，不和30纯价格研究对象混成禁止基本面，也不证明任何新闻都已无延迟充分反映。')
c(32, 'unicom-936-945-552-and-resistance-line-case', '236-b000',
  '作者以2月27日联通936—945到5.52形成顶背驰为卖点案例，并提1月4日与1月30日高点连线作简易参照。',
  '第一类卖点|背驰|高点连线|当下', 4, '价格/时段为作者历史自述，非独立重算或作者实际卖单证明；连线只是例示，不是任意两高点普遍充分卖点。',
  ['第32课联通具体例'], figs=[(235, 1), (236, 1)], ambiguity='historical_stock_signal_and_trade_self_report_not_verified')
c(32, 'market-signal-before-any-person-words', '236-b001',
  '作者要求走势优先于任何人说的话，包括作者本人，并称掌握理论后可以有自己的市场立场而不服从作者的言论。',
  '当下|市场心理|操作策略', 2, '万有引力类比是作者修辞，不当理论已达物理定律验证；原文对抗言论仅作为来源上下文。')
c(32, 'close-supplement-live-regroup-1351-third-buy', '236-b003',
  '2月28日收盘补充称当天走势展示a+A+b+B+c转为a`+B，并将1351标为三买回补点，提醒个股与指数节奏不同。',
  '走势分解|当下|第三类买点|操作级别', 2, '这段为当日收盘后补充而非8:44事前预告，具体补入时刻未载；图和作者自评不构成全部读者实际成功证明。',
  ['2007年2月28日收盘补充，时刻未载'], figs=[(237, 1)], ambiguity='post_close_commentary_not_morning_prediction')
c(32, '2915-is-gg-not-center-top-2894-correction', '236-b004 237-b013',
  '作者原称2915是前日1分中枢高点，随后明确更正“不太严谨”：2915所指是围绕中枢波动的最高点GG，中枢上沿在2894附近。',
  'GG|ZG|走势中枢|围绕中枢的运动', 1, '这是作者具体文字更正，原粗说仍保留，不能把GG与ZG合并；2894附近不补为精确2894.00，图2915.70不静改正文2915。',
  ['2月28日原补充与15:33:55明确更正联合阅读'], figs=[(237, 1)])
c(32, 'feb28-2915-five-day-branches-not-confirmed', '236-b004 237-b010 238-b004',
  '作者说2月28日上午5分中枢已成，下午三买确认结束并离开；后看上方新中枢能否站稳5日线和2915，能则期待再冲3000，不能则回下形成30分中枢。',
  '走势中枢|第三类买点|完成|走势预测|确认', 2, '当前已成与未来能否再成/站稳分开，原5日线与2915联合条件保留，2915按GG更正解释；不是已形成第二5分或确定V反转。',
  ['2007年2月28日指数问答'], figs=[(237, 1)], ambiguity='dated_conditional_future_center_and_index_branches')
c(32, 'praise-cctv-does-not-change-reader-identity', '237-b000',
  '作者在收盘补充中明确点名表扬CCTV的几句讨论；所引老新手与CCTV的发言仍保留各自读者身份。',
  '当下|走势分解|确认', 3, '作者未逐句复述所有推断，表扬不能把读者“然后突破B直接上去”的可能性改成作者保证或未来已确认。',
  ['“为了这几句话”的相邻引用范围'], ambiguity='explicit_praise_scope_not_blanket_validation_of_reader_forecasts')
c(32, 'third-buy-retest-at-least-sublevel-three-down-up-down', '238-b001',
  '针对1335与1351三买区别，作者要求至少一个次级回抽，至少在分时图有三段下上下。',
  '第三类买点|次级别|完成|走势中枢', 1, '未逐条认可读者2809/2811数字或其全部猜测，不用一根回跌替代次级走势；三段条件不等任意三根K。')
c(32, 'forecast-all-possibilities-qualified-not-blanket-ban', '235-b001 238-b007',
  '正文强调当下反应、称预测无意义，但答疑又明确允许把所有可能情形列清楚的预测，批评漏掉当天a`+B这一支。',
  '走势预测|完全分类|当下|操作策略', 1, '是作者明确补充的范围，不把不预测简化成禁止条件预案，也不从全部可能性概念推已知唯一未来。')
c(32, 'skilled-center-hedge-no-one-way-before-rebuy', '238-b010',
  '作者对技术能胜任者允许5日线冲不过先退出，回落未成单边、能构中枢再补；个股已强势上涨则直接看自身背驰，技术不足者少操作。',
  '操作熟练程度|中枢震荡|背驰|对冲|操作策略', 2, '示例与个股差异保留，不把5日线本身设为所有正式买卖点，也不无条件逢跌全回补。',
  ['技术可以且结合具体个股', '回落不出现单边且能形成中枢时才回补'], ['技术不足则减少操作'])
c(32, '600888-reader-profit-not-daily-third-buy', '238-b013',
  '作者否定读者600888低位已成三买的判断，称仍在较大中枢内震荡，向上突破须至少日线上三买确认，并用600432约22元回抽作较小中枢参照。',
  '第三类买点|走势中枢|操作级别|确认', 1, '读者26.67卖/23.60买及13%自述未被认证；空间不小是当时展望，不由一段获利证明三买成立。', ambiguity='dated_stock_breakout_potential_and_reader_returns_not_verified')
c(32, 'exit-standard-changes-when-b-becomes-daily', '239-b001',
  '作者区分30分a+A+b+B+c按30分背驰处理，和低级背驰后形成日线以上B的a`+B；后者再跌破或升破B，应按这个大中枢判断，不必机械等30分背驰。',
  '走势分解|操作级别|中枢扩展|背驰|当下', 1, '两种已演化的结构条件分开，不等30分入场可以任意临时放弃操作纪律，也不把最低级信号直接当大级反转已完成。')
c(32, 'post-third-buy-up-divergence-or-new-center', '239-b004',
  '对三买后上涨再回跌疑问，作者说上涨段若背驰应先处理，否则至少会在上方形成新中枢。',
  '第三类买点|背驰|走势中枢|确认', 1, '“早出了/没问题”是按正确辨识和执行的作者理想化表述，不认证所有交易者可无延迟卖在下跌前；须保留对应上涨段级别。')
c(32, 'inside-b-decompose-sublevel-not-all-tiny-swings', '239-b007',
  '作者说B内部也有次级走势，可按次级逐段分解、以背驰等判断买卖点，但特别小级别无必要逐一操作。',
  '次级别|走势分解|买卖点|盘整|操作策略', 2, '没有直接认可读者回抽越来越高即已确认a`+B的充分条件；分解分析与是否值得操作分开。')
c(32, 'nine-sublevel-extension-author-limit-with-wave-premise', '239-b011',
  '作者说中枢延伸不能超过9个次级，否则变更大级别，并以9个30分、每三段组成日线、三日线形成周线作说明，称该时指数已足以形成周线中枢。',
  '中枢延伸|中枢扩展|次级别|走势中枢|级别', 1, '原不能超过9与9个即高一级的阈值表述需连后33进一步说明，不补成任意9根K或固定9个时间周期；须有波动和相应完成结构，指数级别为作者当时判断未独立重算。',
  ['存在有波动的相应次级走势延伸'], ambiguity='nine_segment_count_boundary_and_later_refinement_not_fully_resolved')
c(32, 'straight-limit-up-no-wave-cannot-add-level', '239-b011',
  '作者明确说没有波动的直线价格不能照三三相加升格，如直接封涨停最多按1分口径处理；无波动就无扩展、延伸问题。',
  '中枢延伸|中枢扩展|涨停|最低级别|次级别', 1, '是该递归计数说明的反例，不把所有涨停历史走势或开板前后全部恒定为1分，也不能按经过时间长直接累成大级别。')
c(32, 'b-departure-again-requires-third-buy', '240-b002',
  '对走出A是否必有b，作者再以当天下午从上午5分中枢突破为例，强调须有三买。',
  '第三类买点|突破|走势中枢|确认', 1, '不是逐条肯定读者“前面a只有一中枢”等其余猜想；不以一次突破取消次级回抽不回的定义。')
c(32, 'five-divergence-rebuy-parent-rise-vs-nesting', '240-b005',
  '作者说5分背驰是否退出要看30分与日线：大级别主升时即使走也需考虑回补，符合区间套背驰时不能随便补回，应先分清卖点已过后的买入节奏。',
  '操作级别|背驰段|区间套|背驰|操作策略', 1, '这段未直接回答读者一跌穿多个GG是否立刻周线扩展的数学条件，不能据此补该充分条件。')
c(32, 'mar1-2800-thirty-center-five-day-fail-case', '241-b003',
  '3月1日作者以2800附近30分中枢演化为观察重点，称上不去5日线会二次探底。',
  '走势中枢|操作级别|均线|走势预测', 3, '当时条件判断而非所有中枢5日线公式或当前点位建议。', figs=[(241, 1)], ambiguity='dated_index_five_day_branch_not_general_rule')
c(32, 'mar1-subminute-turns-center-third-sell-next-day', '241-b008',
  '作者把前日下午判为1分上涨、收盘前1分以下顶背驰，3月1日1006附近1分以下底背驰后成较大中枢；次日下方若有三卖则续探，否则围绕震荡。',
  '背驰|操作级别|走势中枢|第三类卖点|走势预测', 2, '1分上涨不自动等1分背驰；明天三卖条件未确认，不采纳读者当日a+A+b+B+c重组的全部标注。',
  ['2007年3月1日16:00:35指数答复'], figs=[(241, 1)], ambiguity='dated_subminute_turns_and_next_day_third_sell_branch')
c(32, 'divergence-level-not-rise-level-without-nesting', '242-b001',
  '作者说背驰级别与上涨级别无必然对应，要有对应就必须满足区间套关系，详细情况后课再讲。',
  '背驰|上涨|区间套|操作级别|背驰段', 1, '不把任意小背驰当大上涨已结束，也不读成永远不能对应；具体父段包含和成功背驰条件另存。')
c(32, 'third-buy-above-center-strong-stock-index-exception', '242-b004',
  '作者强调三买在中枢上方，震荡可看次级背驰对冲，偏好有大级别三买的强股；指数不在一天内大跌时一般较安全。',
  '第三类买点|次级别|对冲|操作级别|市场风险', 1, '一般与指数单日大跌例外保留，不能把三买与中枢下方三卖混同，更不是强股无风险担保。',
  ['个股有大级别第三类买点', '大盘不在一天内大幅下跌'], ['指数单日大幅下跌的情况另论'], ambiguity='author_relative_safety_heuristic_not_guarantee')
c(32, 'pingan-48-center-formation-then-short-bottom', '242-b007',
  '3月1日对平安作者说48附近小中枢能否向上形成大中枢是短线强弱关键；未出现前不必关注，下面成中枢后可找短线底背驰。',
  '走势中枢|背驰|第一类买点|确认', 3, '中线这个位置套不住为作者未验保证，读者虽问非技术作者仍按技术回答，不补外部基本面结论。', ambiguity='dated_stock_safety_forecast_not_verified')
c(32, 'renotation-a-prime-a-prime-author-accepts', '242-b015',
  '对读者将a`+B改写为更高级的a`+A`的概念问题，作者明确说写成a`+A`最好，关键是理解结构意义。',
  '走势分解|中枢扩展|级别|当下', 1, '只认可本处记号重命名与意义，不将Tryrtytry整段推测都升为作者命题，也不保证每个尚未形成B已可认更高级A。')
c(32, 'five-center-three-one-types-with-child-center', '243-b002',
  '作者否定把看似相近的1分中枢直接当5分：5分中枢须三个1分走势类型重合，而1分走势类型至少含一个1分中枢；若自选1分最低，则其最低中枢至少三K重合。',
  '走势中枢|走势类型|次级别|最低级别|最小级别中枢|重叠', 1, '三个1分类型与三根1分K不等价；自选最低条件不能删，不能据图形相似、周期时间或任意三段就升为5分。')
c(32, 'straight-pull-no-overlap-no-center-macd-not-volume', '243-b002',
  '作者说连续直拉直下若无K线重合不能认作中枢，并强调MACD与成交量是不同东西。',
  '走势中枢|重叠|K线|MACD|成交量', 1, '位于上条自选最低口径的解释，不能把MACD红绿柱当成交量柱；无重合也不靠时间或涨幅补中枢。')
c(32, 'subminute-time-chart-or-one-minute-hist-not-lines', '243-b005',
  '作者对1分以下背驰建议看分时图，或看1分MACD红绿柱而不看黄白线。',
  '最低级别|MACD柱波|MACD|背驰|周期K线图', 1, '这是借最低可视图辨更低级背驰的特定口径，不取消普通本级MACD回轴条件，也不认证一根缩柱必有背驰。',
  ['识别1分钟以下背驰的具体问答'])
c(32, '600550-no-five-without-macd-lines-return-zero', '243-b008',
  '对600550是否进5分背驰段，作者说MACD黄白线未回0轴就无该级别背驰可能；当日尾盘低点为1分以下背驰，非5分。',
  'MACD|背驰|背驰段|操作级别|确认', 1, '原味盘字形保留，回轴是该级别判断条件而非单独充分成立信号；与1分图只看柱辨更低级的答复分对象。')

keep('233-b002', 'upper-l031-c-stage-two-phases-cost-zero-then-earn-shares upper-l031-c-stage-proportional-loss-and-no-desperate-position',
     '32无风险/零成本修辞与31保持警觉、两阶段现金口径分别保存，未以较晚口号覆盖具体风险和退出条件。')
keep('234-b004 235-b000 239-b001', 'upper-l029-c-stage-last-center-expansion-one-unfinished-type upper-l029-c-stage-expansion-regroups-a-tilde-and-may-evolve',
     '32补B可变大导致重组，原30分a+A+b串不再保持旧名，不把中枢扩级和已完成两个类型相混。')
keep('235-b001', 'upper-l027-c-stage-nested-legs-must-be-inside-parent upper-l027-c-stage-finite-levels-no-unique-mathematical-point',
     '盘口研究仍受区间套对应限制，最低有限与真实成交通道风险未消失，原最精确效果自述非无限数学唯一点证明。')
keep('237-b013', 'upper-l020-center-central-two-expansion upper-l029-c-stage-rebound-must-touch-dd-not-zd',
     'GG/ZG如DD/ZD需区分，32有作者明确更正证据，不能把所有波动极值都叫中枢上/下沿。')
keep('238-b001 240-b002', 'upper-l030-c-stage-000581-third-buy-wait-completed-sublevel-retest',
     '32强调至少次级三段回抽，仍不入中枢才三买，不把简单放量突破或一次回落即命名三买。')
keep('239-b011', 'upper-l031-c-stage-weekly-three-legs-original-explicitly-qualified upper-l031-c-stage-weekly-center-first-daily-then-expand-case',
     '32在次日给有波动的九次级说明与当时周线判断，31原不严谨更正保留；33阈值细化待读，不把一串直线上涨按分钟数累级。')
keep('240-b005 242-b001', 'upper-l031-c-stage-standard-trend-nesting-with-sudden-break-exception upper-l031-c-stage-099-five-main-fall-even-one-divergence-wait-parent',
     '背驰级别与上涨级别要区间套对应，父级主升/主跌分别限制小信号，不能凭一个1分信号保证大级转势。')
keep('243-b002', 'upper-l029-c-stage-one-minute-lowest-three-k-only-if-chosen upper-l030-c-stage-lowest-three-consecutive-k-have-direction',
     '32再说最低自选三K，严格5分中枢须三1分类型且各有其1分中枢，不能压扁为三根K=5分。')
keep('243-b005 243-b008', 'upper-l028-c-stage-below-one-minute-histogram-special-comparison',
     '最低图柱波辨更低级与本级黄白线回轴是不同对象，两个原答并存而不是互相废除。')

issue('live-regrouping-b-level-and-exit-scope', '234-b002 234-b003 234-b004 235-b000 239-b001 242-b015',
      'A已成不保证B/c，b不背驰后的B可更大，a`+B/a`+A`是当下重组；同一字母在不同级别和时间的意义不能固化，何时足以排除原背驰未给完整量化。',
      '保留已出现/条件成立/若有c及重判级别，30分入场不等永久只用30分，也不把小级背驰直接判大级完成。', True)
issue('nine-extension-count-waves-and-next-lesson', '239-b011 243-b002',
      '不能超过9与9个组成高层的阈值表述、每三段的完成/重叠与有波动前提须连33，不能按K根数或经过分钟数累加；直线/封板反例不能任意扩成所有涨停一分。',
      '下一课核中枢延伸数量、延伸与扩展/扩张词义及计数起点，未读前不宣布唯一算法或历史周线已独立复算。', True)
issue('2915-gg-2894-zg-author-correction', '236-b004 237-b012 237-b013',
      '2915中枢高点的粗说已由作者明确更正GG，ZG约2894；图2915.70、正文2915及附近2894精度不同。',
      '联合保存原说及更正，不改原数、不合并GG/ZG，不据后图伪补所有中枢边界。')
issue('third-buy-completion-large-daily-case-and-profit', '233-b002 234-b003 237-b010 238-b001 238-b004 238-b013 239-b004 240-b002 242-b004',
      '次级回抽至少三段、已形成/三买确认结束与未来新中枢分开；600888盈利13%不是三买，至少日线确认是该大中枢案例；安全/最大涨幅/先于跌出非实证。',
      '不抹具体级别及单日指数大跌例外，不把读者1335/2809/2811全部猜测当作者认可，不保证所有三买等幅上涨。', True)
issue('forecast-all-branches-versus-unique-prediction', '234-b002 235-b001 238-b007 237-b010 241-b008',
      '正文说预测无意义而答疑允许列全可能情形，未来站稳/三卖分支未确认；不能靠当前强弱选出唯一必然路径。',
      '保留作者明确限定，完整分支与执行条件同存，未给概率就不补概率。')
issue('subminute-macd-vs-own-level-axis-and-recursion', '242-b001 243-b002 243-b005 243-b008',
      '1分以下看分时或1分柱波，不看黄白线；本级背驰又须黄白线回轴；自选最低三K不等三1分类型组成5分，成交量非MACD。',
      '按所判断对象分级，不能由一柱缩短代替完整结构，也不能把走势图周期直接等同严格中枢级别。', True)
issue('close-addition-unknown-time-and-reader-endorsement', '236-b002 236-b003 236-b004 236-b005 237-b000 237-b002 237-b004 237-b006 242-b011 242-b015',
      '5段收盘补充不应继承早8:44，现只记2/28，具体时刻未载；CCTV被表扬/记号被认可只限明确范围，读者身份仍在。',
      '原文/字符映射/坐标不变，不能把事后1351补评伪作早上精准预告，读者B必突破等未来主张不批量升为作者。')
issue('historical-self-report-safety-and-figure-provenance', '233-b002 233-b003 234-b000 235-b002 236-b000 236-b001 240-b008 240-b009 240-b010 240-b011 241-b000 241-b001 241-b002 242-b007',
      '零成本安全/无风险、000416100%、联通5.52与14至25操盘、金融控制/政策指控及平安中线套不住均为作者当时主张未独立核；5图2文后3未核。',
      '历史政治及市场观点与技术条件分层，不作现时金融/法律事实或攻击方案，图后行情/复权框线不替原文证明。')

note('233-b003 234-b000 235-b002', 'historical-stock-self-report-and-public-rhetoric',
     '14至25到3元多、联通对抗与话语影响等历史操盘自述完整已读。',
     '不认证账户、匿名股票身份或因果，不把敌对叙事制作执行方案；技术卖点例与走势优先另抽。')
note('236-b002', 'post-close-supplement-heading', '明确写今天收盘讲评，后续5段属于当日收盘补充。', '只知日期2/28不造具体时刻，不能当8:44事前预测。')
note('236-b005', 'post-close-third-buy-practice-reminder', '当日补充再次要求大跌找将形成三买、调整心态并复盘直播，完整已读。', '学习提醒和作者自评不认证每位读者确有交易成功；仍须三买完整条件。')
note('240-b006 240-b007 240-b008 240-b009 240-b010 240-b011 241-b000 241-b001 241-b002 241-b004', 'dated-political-market-opinion-and-stock-selection-context',
     '3/1文章标题、金融安全/政策及对抗论述、深圳低价农业环保/新能源与5元上下三线股观点及分隔完整已读。',
     '保存历史观点身份，不认证政治指控、资金因果或现今板块结论，不把当时价格口号变成当前选股指令。')

relations = {
    'upper-l032-c-stage-a-formed-not-predict-b-required': [('当下', '走势预测', 'qualifies')],
    'upper-l032-c-stage-b-and-c-departures-require-third-buy-not-guaranteed': [('第三类买点', '走势分解', 'qualifies')],
    'upper-l032-c-stage-b-no-divergence-b-center-may-exceed-a': [('走势分解', '中枢扩展', 'qualifies')],
    'upper-l032-c-stage-order-book-anomaly-only-in-valid-nesting': [('技术分析', '区间套', 'qualifies')],
    'upper-l032-c-stage-2915-is-gg-not-center-top-2894-correction': [('GG', 'ZG', 'distinguishes')],
    'upper-l032-c-stage-third-buy-retest-at-least-sublevel-three-down-up-down': [('第三类买点', '次级别', 'requires')],
    'upper-l032-c-stage-nine-sublevel-extension-author-limit-with-wave-premise': [('中枢延伸', '中枢扩展', 'qualifies')],
    'upper-l032-c-stage-divergence-level-not-rise-level-without-nesting': [('背驰', '区间套', 'qualifies')],
    'upper-l032-c-stage-five-center-three-one-types-with-child-center': [('走势中枢', '走势类型', 'qualifies')],
    'upper-l032-c-stage-subminute-time-chart-or-one-minute-hist-not-lines': [('最低级别', 'MACD柱波', 'related')],
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
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], 'CCTV/老新手/面首甲/Tryrtytry的原话保留读者，作者明确表扬或认可只限具体范围；读者600888盈利13%不等三买成立，未答的问题不补答案。'
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
        'note': 'A已成不保证B/c，b背驰与B扩级须当下重判；GG2915/ZG2894作者明确更正，九次级延伸须波动不能累加直线，最低自选三K/严格5分三1分类型及MACD普通回轴与次1柱比较分层。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True, reviewer=REVIEWER, visual_review_note=f['note'],
             figure_source_review='5图全部查看，2文后3原发未核；000416前复权和周期框不替收益实测，联通3/1日图为后配，指数分时与三买图标须连次级三段和GG更正。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 131 and Counter(x['lesson_number'] for x in ledger) == {32: 131}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [32], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(233, 244)), 'figure_objects_viewed': 5, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '32课131段11页5图同模型四轮；5收盘补充只记当日不造时刻，a`+B当下扩级/GG更正/延伸九段与非直线条件/自选最低及MACD范围分开，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


