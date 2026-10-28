"""Materialize the main agent's four-pass reading of lesson44.

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
BASE = 'c_stage_l044'
REVIEWER = 'Codex 主代理 / 阶段C上册44课同模型四轮复核'
SOURCE_SHA = '0048ace68c1d6c20bd4d0648b45c2fc78bc32f81c64b5592d9fc4eb587093aad'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-044' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 47
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 316 AND 320 ORDER BY pdf_page,id', (DOC,))]
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
    pending.append({'id': 'upper-l044-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})




















c(44,'scope-smaller-divergence-than-current-level-not-same-level-case','316-b007 316-b008',
  '本课进一步分析背驰级别小于当下走势级别的情形，沿向上30分a+A+b+B+c、c内1分背驰最终下跌回B的设例。',
  '小级别转大级别|背驰|级别|走势类型',1,'最终回B是设问所选结果，不是任意小背驰都必回B；与43同级实际背驰分支区别保持。')
c(44,'c-contains-five-minute-center-for-B-third-buy-completion','316-b009',
  '在该向上30分例中，作者说c至少含一个5分中枢，否则B不能完成，因为不能形成第三类买点。',
  '小级别转大级别|走势中枢|第三类买点|完成',1,'保留本例结构及B完成问题，不把任何1分钟级走势都宣称含5分中枢；c在此是离开段容器不是把1分背驰误作c整体级别。')
c(44,'one-minute-top-after-last-five-center-pulls-back-around-it','316-b009',
  '设c`为c中最后5分中枢，作者说1分顶背驰在c`之后，先把走势拉回c`，整体可看作围绕c`震荡。',
  '小级别转大级别|背驰|走势中枢|中枢震荡',1,'c`指正文最后5分中枢，别与43另记号或习作图c`标法静同一；这是回c`，不是小背驰已经保证回30分B。')
c(44,'normal-last-subcenter-oscillation-not-large-turn','316-b009',
  '小级背驰后若仍在最后一个次级别中枢正常震荡，作者说不能转化为大级别转折；大的向下变动须先有该中枢三卖。',
  '小级别转大级别|中枢震荡|第三类卖点|趋势转折',1,'限定仍正常震荡的状态，三卖是破坏其正常震荡所需条件，不意味着三卖单独足够带来所有大级结果。')
c(44,'small-top-large-down-necessary-last-subcenter-third-sell','316-b010',
  '缠中说禅小背驰-大转折定理规定：小级别顶背驰引发大级别向下，必要条件是该级别走势最后一个次级别中枢出现第三类卖点。',
  '缠中说禅小背驰-大转折定理|小级别转大级别|第三类卖点|次级别|背驰',1,'最后一个、次级别、必要三个限制不可省略；非任意早期中枢三卖或任意卖点即充分大跌。')
c(44,'small-bottom-large-up-necessary-last-subcenter-third-buy','316-b010',
  '同定理对小级别底背驰引发大级别向上，要求该级别走势最后一个次级别中枢出现第三类买点，作为必要条件。',
  '缠中说禅小背驰-大转折定理|小级别转大级别|第三类买点|次级别|背驰',1,'原文必要条件提是字样留在引文；只整理语句不改条件，非所有三买都保证大级向上。')
c(44,'necessary-not-sufficient-third-sell-not-guaranteed-return-B','316-b011',
  '作者强调该小转大情形只有必要条件，没有充分条件；末个次级别中枢三卖出现，也不保证大级别转折或本例必回30分B。',
  '缠中说禅小背驰-大转折定理|小级别转大级别|第三类卖点|趋势转折',1,'不扩为所有背驰转折定理都无约束，只说此小级到大级分支不能因条件出现就断定结果。')
c(44,'actual-same-level-top-own-operation-full-exit-versus-small-complexity','317-b000',
  '同级背驰必回该级最后中枢，作者称比小转大条件更强；若实际顶背驰级别正是操作级别，可直接全部卖出，小转大则需复杂程序。',
  '背驰|操作级别|卖点|小级别转大级别|仓位',1,'前提是相应级别已成立顶背驰且以该级别操作，非任何更小点或仅候选段即全出；这里先给可全仓操作的情境，后文较大资金需分批。',
  ['背驰级别等于当下走势类型级别','该级别同时是自己的操作级别、实际顶背驰已成立'])
c(44,'thirty-minute-operator-bears-five-minute-pullback-or-switches-level','317-b001',
  '按30分钟操作就需承受5分钟回调，否则可把操作级别调到5分钟。',
  '操作级别|市场风险|操作策略',1,'是自选级别对应容忍的作者纪律，不给固定百分比回撤阈值，也不等永久忍受已破坏本级结构的走势。')
c(44,'example-smaller-top-first-at-least-five-minute-down-move','317-b001',
  '沿该30分走势例，作者说小于30分的顶背驰先至少导致一个5分向下走势，后续按其是否触及所指结构位置处理。',
  '小级别转大级别|操作级别|背驰|下跌',1,'保留本例与前c含5分中枢结构，不孤立泛成任意市场1分顶背驰均必有5分下跌；与43一般1分盘整后再涨不能无条件混同。')
c(44,'five-down-not-back-to-third-buy-retest-type-high-ignore','317-b001',
  '本例若5分向下走势没有回到构成最后30分中枢第三类买点的那个5分向下走势类型高点，作者说可不理睬，仍在30分操作可接受范围内。',
  '操作级别|第三类买点|高低点|小级别转大级别|操作策略',1,'破位对象为嵌套的5分回试走势类型高点，原文没叫GG；不由习作蓝2/GG自动替换，也不简化成30分中枢上沿。未回到与跌破之间的刚好相等细节未穷尽。',figs=[(317,1),(318,1)])
c(44,'strongest-pullback-not-touch-last-five-center-in-up-five-containing-buy','317-b001',
  '最强情形中，5分回调甚至不触及包含最后30分中枢三买的5分向上类型里的最后5分中枢，作者认为更无须理睬。',
  '小级别转大级别|第三类买点|走势中枢|操作级别',1,'按原文向上类型内最后5分中枢的嵌套说法保留，未静改成任意次次级中枢；强弱是该操作语境，图蓝1非统一价格阈值。',figs=[(317,1)])
c(44,'break-five-retest-type-high-exit-on-any-up-rebound','317-b001',
  '若5分向下走势跌破上述构成30分中枢三买的5分回试走势类型高点，作者要求此后任何向上回抽先离开。',
  '第三类买点|高低点|卖点|小级别转大级别|操作策略',1,'保留先破该5分类型高点、再向上回抽的时序；不变破位即杀跌或未来任意价成交保证，未给回抽完成/相等/EPS所有判据。',figs=[(317,1),(318,1)])
c(44,'many-chips-part-at-last-five-center-third-sell-then-clear-on-boundary','317-b002',
  '上述先是全仓处理；筹码较多时，包含最后30分三买的5分向上类型内最后5分中枢出现三卖，先出部分，后续出现上一段破位情形再出清。',
  '仓位|资金管理|第三类卖点|操作级别|小级别转大级别',1,'正文没有给部分的固定比例；对应该嵌套中枢，不是随意任何小三卖；出清仍接前段回抽时序，图无实盘成交证明。',figs=[(318,1)])
c(44,'no-later-boundary-break-can-rebuy-short-spread','317-b002',
  '分批先出后，若未出现前述进一步破位情形，作者说可以回补，视为做一次短差。',
  '仓位|操作策略|第三类卖点|小级别转大级别',2,'沿上一段特定筹码及结构程序，未给回补价格/时间或取消真实买点核查，不据此担保短差盈利。')
c(44,'thirty-minute-not-all-out-at-every-one-minute-top','317-b003',
  '30分操作者不能见任意1分顶背驰就全抛，因不能预测它必转大级；这样做会变为按1分操作，小转大被作者称并不常见。',
  '操作级别|背驰|小级别转大级别|走势预测|仓位',1,'风险与操作层级须一致，并不否认较大资金可先卖部分；不常见未给统计频率。')
c(44,'one-minute-operation-if-capital-and-precision-procedure-same-levels-different','317-b003',
  '若资金量和精度能按1分操作，可选择1分而非30分；操作程序与30分相同，只是相应级别不同。',
  '操作级别|操作熟练程度|交易容量|操作策略',1,'能力/容量是前提，不保证初学者立即缩级；各级信号不可混串，也未给所有分钟周期图严格递归对应证明。')
c(44,'larger-capital-part-at-one-minute-then-follow-rebuy-or-more-exit','318-b000',
  '一定量资金即使按30分操作，见1分顶背驰也可先出部分，再依后续回调决定回补或继续出；作者解释这种资金不能在每个固定级别卖点都全卖。',
  '交易容量|资金管理|仓位|操作级别|背驰',1,'作者唯一可行的说法限其容量语境，未给规模阈值/出货比例/流动性模型，也不证所有大资金策略唯一；区别317任意小点全抛。',ambiguity='author_capacity_only_feasible_claim_not_modeled')
c(44,'bottom-case-reverse-program-author-instruction-not-complete-algorithm','318-b000',
  '作者说底背驰的对应处理可将上述顶背驰程序反过来。',
  '背驰|操作策略|小级别转大级别|买点|卖点',2,'此句未逐项写底部的所有回试对象、等值、确认及成交条件；镜像方向与定理三买必要条件可联合，不能自造完整可执行算法。')
c(44,'apr10-Sinopec-earnings-large-caps-valuation-author-view','318-b002',
  '4月10日作者以中石化业绩和估值反驳大盘股应被压制的意见，并预期当年仍高速增长。',
  '基本面|宏观市场判断|走势预测',4,'历史估值和业绩预期，原未列具体PE/财报，本批未外核；不把作者反问当整个市场安全或对手真实意图证明。')
c(44,'apr10-gap-pressure-oscillation-shenzhen-ten-thousand-policy','318-b003',
  '作者把当日震荡解释为前日缺口压力的反应，认为深圳万点已近，并以此评论管理层应对。',
  '缺口|市场震荡|政策风险|走势预测',4,'只存当时因果解释和预期，不认证压力唯一因果、预测结果或管理层实际行动。')
c(44,'apr10-five-day-fallback-not-top-prediction-and-futures-warning','318-b004',
  '作者当时仍让看5日线，反对持续猜顶，并对凭这种预测参与期货发出强烈警告。',
  '均线系统|走势预测|期货|操作策略',3,'历史教学警示和死亡修辞，不把5日线当所有市场安全规则，未核任何预测者真实盈亏或给期货交易指令。')
c(44,'switch-after-top-divergence-and-confirmed-intraday-stability','318-b005',
  '当时换股操作，作者要求先在某级别顶背驰抛出，再等盘中回跌确实站稳后换，认为这样风险较小，并反对追高。',
  '操作策略|背驰|确认|追高|市场风险',1,'某级别及先抛后回跌站稳顺序不可省；原没有明说站稳对象是大盘/原股/新股，也未给确定阈值，不补成已证低风险买点。')
c(44,'weak-tech-avoid-casual-switch-quality-second-lines-start-author-view','318-b005',
  '作者建议技术不足者别随便换股，以均线控制持有，并称当时优质二线成分股及业绩送配好的二线都会启动。',
  '操作熟练程度|均线系统|持股|二线股|走势预测',3,'都会启动为当时强预测而非样本实证，未给股票全集/期限；不代表持有无风险，段尾4/11新时间头不归本段日期。',ambiguity='author_all_selected_second_lines_start_prediction_unverified')
c(44,'apr11-large-caps-index-role-and-leadership-author-interpretation','318-b006 319-b000',
  '4月11日作者以中石化、联通、中行和工行为例谈大盘股对指数的作用，称中行成龙头，要求体会何时使用不同权重股。',
  '指数走势背离|板块轮动|主力资金|宏观市场判断',4,'历史盘面/操作叙述，不认证未名机构被操控、真实出货或作者一人导演市场；5元反问非通用价位指令。')
c(44,'apr11-top-done-not-predicted-energy-balance-unknown','319-b001',
  '作者说顶由市场做出来，资金与筹码能量平衡后的休整位置不能事先预测；技术好可震荡先卖后买，不懂者看5日线，不能追高。',
  '当下|能量结构|走势预测|操作熟练程度|操作策略',1,'本段未给能量平衡计算公式或顶的提前充分确认；历史口吻不抹实际顶背驰卖点，5日线仍是辅助简法。')
c(44,'apr11-only-policy-stop-and-half-position-author-risk-view','319-b001',
  '作者当时称只有管理层大棒能打住大盘，并建议心态等承受不足者用半仓，便于应对。',
  '政策风险|仓位|市场心理|市场风险',3,'只有政策为未核强判断，半仓按原词不推所有人最佳比例或免风险；原心脏说法不作医疗判断。',ambiguity='author_policy_only_risk_and_half_position_context')
c(44,'fall-not-necessarily-bears-bulls-can-wash-case','319-b005',
  '对读者把当天下跌归空方，作者反问多头也可洗盘，并把石化动作前先跌解释为剧本的一部分。',
  '市场分力|主力资金|宏观市场判断|市场震荡',2,'排除跌必为空的单因猜测，不反向认证每次下跌必多头洗盘，也不核具体机构交易。')
c(44,'sector-rotation-shenzhen-main-shanghai-reference-no-chase','319-b008',
  '回应一线齐动是否二八行情等问法，作者让当板块轮动看，指数看深圳、上海参考，任何股票不追高。',
  '板块轮动|指数走势背离|追高|操作策略',2,'历史语境，未明确肯定读者未来二八走势或银行具体整理预测，不当永久两指数优劣排名。')
c(44,'want-faster-five-minute-but-not-unskilled-parameter-unendorsed','319-b011',
  '读者问把MACD改5.10.10，作者没有认可参数，而说等不到30分可按5分，但不熟练别用太小级别，错后可能来不及改。',
  'MACD|操作级别|操作熟练程度|交易误差',1,'5.10.10是读者建议，作者改级不等修改指标参数；不得据此把默认MACD改成新标准，也不让初学者盲目缩级。')
c(44,'correct-operation-before-better-results-focus-repeat-selected-stocks','320-b001',
  '作者把操作正确与结果更好分为先后两层，建议先专注选定股票反复操作、把握相应级别震荡，认为效率不低。',
  '操作熟练程度|操作策略|市场心理|操作级别',1,'效率为条件性观点，不能以当天别股涨停反证本股操作错，亦不保证单股最大利润或所有持股长期获益。')
c(44,'one-minute-just-example-five-and-subminute-same-principle','320-b005',
  '对c内5分背驰但c对b不背驰的问法，作者说没有不同，即使1分以下道理也一样；1分只是例子，并非必须为1分背驰。',
  '小级别转大级别|背驰|级别|操作策略',1,'认可小级小于当前大级的原理推广，不把5分小背驰与30分同级背驰必回B两支混为同一必要充分；保留正文c结构及最后次级中枢条件。')
c(44,'twenty-year-bull-three-months-twenty-PE-author-strong-reassurance','320-b008',
  '问大资金如何出货及000912为何未涨，作者以20年大牛市、出后何处买回作反问，并让20倍市盈率股票三个月后再看，称市场只回报耐心者。',
  '长期投资|基本面|走势预测|市场风险',4,'原回复未点明20倍就对应000912，未核估值/三月收益/20年趋势；强安心和只耐心为作者意见，不取消风险或转成当前持仓建议。',ambiguity='author_twenty_year_bull_and_patience_return_unverified')

note('318-b001','source_header','正文与解盘之间星号分隔已核。','仅分隔不作独立技术知识。')
issue('small-large-theorem-necessary-only-and-generalized-examples','316-b007 316-b008 316-b009 316-b010 316-b011 317-b000 320-b004 320-b005',
      '末个次级中枢三卖/三买是必要而非充分，回c`不等必回B；1分仅例可推广5分或更低，但本例至少5分下行与43一般1分盘整后上行作用域须保留。','按大级结构/操作级别和实际背驰分支比对，不将每个小点推成大转折，也不抹本例5分中枢完成条件。',True)
issue('nested-retest-type-high-boundary-equality-and-full-position','317-b001 317-b002',
      '原文破位对象是构成最后30分三买的5分回试走势类型高点，不是裸中枢上沿；未回到/跌破之间相等及回抽完成未全，最强嵌套中枢名词仍待精确。','保留完整对象与先破再回抽退出时序；图GG/蓝1/2属习作，不自动代换，后续补完整定位但不自造EPS。',True)
issue('capacity-layered-exit-rebuy-and-bottom-mirror-completeness','317-b000 317-b002 317-b003 318-b000',
      '可全仓情况与筹码多分批、早小级点先部分再跟踪不同；唯一可行未给规模/比例/成交/底部全部镜像分支，反弹/回补未量化。','保留容量和精度条件，不将看到小点全抛冒充30分策略，未给收益/回撤保证。',True)
issue('MACD-reader-parameters-skill-switch-and-result-vs-process','319-b010 319-b011 320-b000 320-b001',
      '读者5.10.10参数未获明确认可，作者改操作级别而非改参数；专注重复/先操作后结果是能力训练，不以事后涨停判全部正确。','不改默认MACD标准或鼓励初学盲目缩级，回查相应级别/费用/成交，不把能力建议当算法验证。')
issue('historical-switch-stability-policy-only-and-twenty-year-risk-claims','318-b002 318-b003 318-b004 318-b005 318-b006 319-b000 319-b001 319-b005 319-b008 320-b008',
      '换股先顶背抛再盘中回跌站稳但对象未明；政策唯一风险、二线全启、20年牛市/三月/20倍/耐心回报为历史强观点，半仓条件性。','不认证估值/机构/未来收益，不静配000912至20倍股票，不因反追高取消实际市场风险。',True)
issue('date-tail-and-student-drawings-not-author-GG-definition','318-b005 318-b006 319-b000 319-b001',
      '3段4/11承接纠正、12时间空格规范；两图署张大山习作为后加学习者示意，GG/蓝线及c`图标不是作者原定义，制作者身份/发布时未核。','固定原文/字符映射/几何及前4/10段尾时间头不改；作者文字支持命题，习作仅定位不作独立证明。')
relations={
 'upper-l044-c-stage-small-top-large-down-necessary-last-subcenter-third-sell':[('缠中说禅小背驰-大转折定理','第三类卖点','qualifies'),('小级别转大级别','次级别','qualifies')],
 'upper-l044-c-stage-small-bottom-large-up-necessary-last-subcenter-third-buy':[('缠中说禅小背驰-大转折定理','第三类买点','qualifies')],
 'upper-l044-c-stage-necessary-not-sufficient-third-sell-not-guaranteed-return-B':[('小级别转大级别','趋势转折','qualifies')],
 'upper-l044-c-stage-thirty-minute-operator-bears-five-minute-pullback-or-switches-level':[('操作级别','市场风险','qualifies')],
 'upper-l044-c-stage-many-chips-part-at-last-five-center-third-sell-then-clear-on-boundary':[('仓位','第三类卖点','qualifies')],
 'upper-l044-c-stage-one-minute-operation-if-capital-and-precision-procedure-same-levels-different':[('操作级别','交易容量','qualifies')],
 'upper-l044-c-stage-larger-capital-part-at-one-minute-then-follow-rebuy-or-more-exit':[('交易容量','仓位','qualifies')],
 'upper-l044-c-stage-want-faster-five-minute-but-not-unskilled-parameter-unendorsed':[('MACD','操作熟练程度','qualifies')],
 'upper-l044-c-stage-correct-operation-before-better-results-focus-repeat-selected-stocks':[('操作熟练程度','市场心理','qualifies')],
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
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], '读者MACD5.10.10参数、二八行情预测、000912未涨及5分对比30分问题仍保留身份；作者改级不代表认可参数，也不因小级原理推广取消两支必要/充分边界。'
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
        'note': '小背驰-大转折末个次级中枢三类点仅必要无充分；正文嵌套回试类型高点不代习作GG，先破再向上回抽及全仓/分批不同，参数读者与操作改级分开。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=f['note'],
             figure_source_review='两整图署张大山习作，按后加学习者注图保存，真实身份/发布时未核；GG和蓝1/2/c`解释不替代正文5分回试类型高点或完整级别/成交算法。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 47 and Counter(x['lesson_number'] for x in ledger) == {44: 47}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [44], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(316, 321)), 'figure_objects_viewed': 2, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '44课47段5页2习作图同模型四轮；3跨日及12空格规范，两图后加；小转大必要非充分、嵌套破位对象和分层容量/读者参数边界保留，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


