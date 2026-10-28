"""Materialize the main agent's four-pass reading of lesson50.

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
BASE = 'c_stage_l050'
REVIEWER = 'Codex 主代理 / 阶段C上册50课同模型四轮复核'
SOURCE_SHA = '880eaea0da0e7a303efdbba6e9834946487a7cfccc4a163b3f5ee199582d8521'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-050' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 105
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 362 AND 371 ORDER BY pdf_page,id', (DOC,))]
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
    pending.append({'id': 'upper-l050-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})




















# Quote only the technical second half, while keeping the full source as context.
quote_overrides['366-b008']=passages[pid('366-b008')]['text'].split('给各位一句话，',1)[1]
c(50,'MACD-periods-calculation-sensitivity-not-identical-output','362-b013 363-b000','作者认为1分与30分MACD计算方法本质相同、周期不同，相关计算线性，主要差别为灵敏或迟钝。','MACD|指标对比|周期K线图|操作级别',1,'作者关于指标计算的解释，未在此给公式或证明；不把跨周期采样/参数变化说成数值完全相同、可任意无损换算，也不把所看图周期当信号级别。',ambiguity='author_linear_calculation_explanation_not_cross_sampling_identity')
c(50,'structure-then-comparable-legs-then-MACD-period','363-b000','顺序是先分析中枢与走势运动、选需比较力度的走势段，最后选适宜周期MACD辅助；不能因30分走势常对应30分指标就倒置。','走势中枢|动力学|指标对比|MACD|操作级别',1,'先结构选段后辅助指标，常对应非必同周期，未独立背书任意两段可比较或单凭回轴/柱子即可成立背驰。')
c(50,'choose-thirty-if-one-complex-two-areas-clearer','363-b000','若两段在1分MACD呈复杂柱线变化，而30分有清楚两柱面积和标准黄白线变化，作者建议选30分较便于辅助比较。','MACD柱波|指标对比|周期K线图|动力学',1,'示例条件及便于比较，不是将1分信号升级30分；也没给面积积分窗、参数或跨周期数值严格等式。')
c(50,'understand-logic-not-belief-in-author-confidence','363-b001','作者要求从道理逻辑弄清理论，理论讨论既指导分析也建立信心，反对因相信作者而盲信其理论。','操作熟练程度|市场心理|技术分析',1,'几何/三角形180度为作者比喻，不是本项目已经证完市场理论或以信心代替证据。')
c(50,'experience-psychology-and-long-practice-affect-precision','363-b002','作者认为相同理论应用因经验与心理状态而结果不同，精度提高是长期实践问题，纸上讨论不足。','操作熟练程度|市场心理|操作策略',1,'源文以理论正确为前提，不据结果差异反证理论永远正确或把所有亏损一概归咎个人；实践建议不构成收益实证。')
c(50,'habitual-bull-early-buy-late-sell-bear-reverse','363-b003','作者说不熟者易因买后再跌、卖后再涨而畏缩；习惯多头常买早卖晚，空头常买晚卖早，即便懂理论习惯也影响时机，不能一两天改完。','市场心理|操作熟练程度|买卖点',2,'一般心理描述非人人固定人格分类，不因后涨跌一项就认定买卖点全部错误或理论已被实证。')
c(50,'study-existing-then-record-live-simulations-before-real-trades','363-b004','作者建议先能用理论分析已有走势，再不真买卖、当下模拟并逐次记录，随后用后续走势复盘纠正，模拟有把握后再真买卖。','模拟操作|操作熟练程度|操作策略|市场心理',1,'源文所有曾有走势为学习要求，不称本项目已穷举市场；未给足够把握的样本量/胜率阈值，市场每周5天是当时背景不是永恒日历。')
c(50,'static-dynamic-actual-learning-sequence-not-days','363-b005 364-b000','学习过程先分析静态已有图形，再动态当下把握，最后实际操作；不是一两天完成，最终须自己学习并可能付市场学费。','模拟操作|操作熟练程度|技术分析',1,'静态看懂不等真实当下无前视偏差；作者过去荐股为读者准备学费只是自述，不证明收益/成本已被兜底，不把买了扔着扩为通用策略。')
c(50,'method-practice-geometric-profit-guarantee-author-only','364-b001','作者劝心态平稳、别只计少赚，强调有效方法和磨练，并断言真正掌握后足够时间自然产生足够利润、由其理论如几何般保证。','操作熟练程度|市场心理|操作策略|市场风险',2,'几何保证/自然赚钱为作者强主张，此课未给数学证明、资金时间边界/交易成本或实绩；不当本项目保证获利，未将其修辞静改为统计结果。',ambiguity='author_geometry_and_profit_guarantee_not_verified')
c(50,'other-analysis-news-only-auxiliary-not-override-buy-sell','364-b002','作者允许其他知识、消息与概念作辅助，但不得违反其理论；以较大级别反复一买卖、一卖买为错误方向示例。','技术分析|第一类买点|第一类卖点|操作策略',1,'记录体系内部原则和反例，不执行反向交易；并不认证任何消息、跟风都安全或N次必破产，亦非当前荐股。')
c(50,'apr27-break-3745-no-third-buy-oscillation','364-b003','4月27日作者说跌破3745所以未形成三买，震荡仍在，下午拉起为短差机会。','第三类买点|中枢震荡|价格区间|操作策略',1,'历史该中枢/该价位，未把任何价格跌破都等三卖；图到4/30不能用后K证明4/27判点或成交，原3745不按图3745.40改。',figs=[(364,1)])
c(50,'apr27-afternoon-compare-apr26-0930-MACD-no-new-high-sell','364-b003','该日下午冲高力度应与4月26日09:30那次比，作者说MACD未同时创新高，判为震荡卖点，强调只是很短线的示例。','中枢震荡|MACD|指标对比|卖点|操作级别',1,'两段时点和短线语境不可删，非所有MACD未高都无条件卖；原0930保留，不据图0935/10:00标签改写开始点，比较窗/具体参数未全。',figs=[(364,1)])
c(50,'apr27-five-center-expanded-thirty-3720-3761','365-b000','作者称上沿3745的5分中枢已扩展为30分、区间3720至3761，短线关注新中枢突破方向。','中枢扩展|走势中枢|操作级别|价格区间|突破',1,'历史作者判读，不把读者CCTV九段1分解释当作者亲自确认；原3720/3761不按图3720.80/3761.99静修，未从此推出所有九段都成30分。',figs=[(364,1)],ambiguity='historical_center_geometry_not_reader_nine_segment_proof')
c(50,'holiday-last-day-not-automatically-safe','365-b000','作者提醒放假前只剩一个交易日也不等天下太平，末日走势仍不可高枕无忧。','市场风险|操作策略',3,'一般风险提醒和历史节前例，不认证相邻政治指控或任何现今假期日程。')
c(50,'switching-needs-skill-strength-otherwise-focus','366-b008','作者用花心与专一比喻换股选择：须有技术实力；若频繁选择的收益不及专一，就没有资格如此操作。','操作熟练程度|操作策略|交易容量',2,'只引用给各位一句话之后的技能比较，前半999翻两倍和基金恶意指控未验证、不作本条证据；未给两模式同风险/同时间实证比较。')
c(50,'may8-gap-volume-strong-balance-not-as-strong-as-appearance','367-b003','5月8日作者判留大缺口后的放量强平衡市，认为未如表面强，缺口将困扰随后短线、震荡难免。','强平衡市|缺口|成交量|市场震荡|走势预测',2,'强平衡为日内结构非未来必强，难免是作者该案预测未独立验证；图有5/9后K不证先验准确，未说缺口一定立刻回补。',figs=[(367,1)])
c(50,'short-five-day-medium-five-week-higher-skill-divergence-not-gap-guess','367-b004 368-b000','作者一般建议短线看5日、中线看5周，不破拿着；高精度者关注短线背驰操作而不猜是否补缺口，别等跌完找卖点或涨后追买点。','均线系统|操作级别|操作熟练程度|背驰|缺口',1,'限当时行情/能力简法，仍与45单边非盘整限制联合；原涨了再早买点字样不静修，未给有效破位精确定义或预知所有信号。',figs=[(367,1)])
c(50,'stocks-use-own-chart-may-rise-while-index-fills-gap','368-b001','个股按自身走势决定进出，作者指出有些强股即使指数补缺口反可上扬；技术差者短线可先看5日线，别习惯乱跑。','操作策略|操作级别|均线系统|市场分力',1,'有些非所有，指数点位不替代个股买卖点；均线不破不是全部风险消失，也不把所有卖后涨归咎盲动。')
c(50,'wrong-early-sale-no-chase-wait-next-short-buy','368-b001','卖早或卖错不必追高，等短线买点再介入；作者说震荡中这种买点不难发现。','等待|追高|买点|市场心理|操作策略',1,'技能/当时震荡语境，未保证买点必同卖价回补或任意短线买点符合原定级别，仍需三卖停止回补限制。')
c(50,'novice-less-trades-small-practice-after-understanding-record','368-b005','不清理论者应少操作，作者以5日线作简法；理论已较有把握后用少量资金练，每次分析想法复盘并记录，不懂问具体问题。','操作熟练程度|均线系统|模拟操作|资金管理',1,'少量无固定比例/金额；持有简法与45结构条件联查，不能因一句拿着就取消各股/级别卖点或保证优于所有高手。')
c(50,'small-to-large-operate-as-center-oscillation','368-b012','作者说转大以后按中枢震荡操作。','小级别转大级别|中枢震荡|操作策略',1,'回答日线背驰后回拉中小转大提问，需先确认转大/相应中枢，不代表任意小背驰立刻等于大中枢；后文长周期前提例外须联合。')
c(50,'very-long-pullback-premise-change-may-not-fully-return','368-b012 369-b000','特别长的背驰回拉过程，作者承认理论可能失效：年线例中改朝换代、交易规则完全改变会改成立前提，因此可能不完全回拉。','理论成立前提|边界条件|交易规则|中枢回拉作用|背驰',1,'年线为举例而非仅年线有前提；前提具体全表未给，改朝换代是长期制度情境，不是当天价格波动就宣布前提变；不把作者承认可能失效抹成绝对无例外。')
c(50,'unchanged-premises-author-certain-pullback-not-proof','369-b000','作者认为应关心理论成立前提是否改变；前提未变，就一定回拉。','理论成立前提|中枢回拉作用|背驰|边界条件',1,'保留一定而非静软成可能，明确是作者条件内理论断言，不是已独立证明所有市场；日线最后中枢来自读者原问，未给全前提清单、回拉时限/成交可行性，回拉不等获利保证。',ambiguity='author_conditional_certain_pullback_with_unspecified_full_premises')
c(50,'five-day-three-days-no-return-usual-imprecise-delayed-confirmation','369-b003','作者称破5日线是通用不精确法，通常三天拉不回算真跌破，但这样确认已离真正高点远，不是最终办法。','均线系统|有效跌破|确认|操作熟练程度',1,'通常/一般/不精确不可删，未答最低触线还是最高低于的二选一，也未明确收盘、三天是否连续交易日或等值规则；不把此三天与47缺口三天统计混合。',ambiguity='usual_three_day_confirmation_not_exact_price_or_day_rule')
c(50,'997-need-comparable-legs-no-endorsement-form-repeat-rhythm','369-b012','对000997卖一部分是否正确，作者因未说比较哪两段而不知其是否真懂；要按操作级别形成卖后等买点回补、再卖的持续节奏，非只判准一两次。','操作节奏|指标对比|操作级别|买卖点|操作熟练程度',1,'未认可读者所称5分背驰或具体卖价；持续节奏不等每天必交易、任意价必须买回，原吸血比喻不作收益审计。')
c(50,'small-funds-under-million-more-than-five-too-many','370-b001','对小资金换成8只股的混乱，作者要求减少种类、集中些，一般100万以下超过5只都太多。','交易容量|资金管理|操作策略|操作节奏',1,'100万以下/超过5/一般是作者操作精力建议，非已证最优分散数、5只一定合适或所有本金都必须集中同股；不认可读者明日全抛重来或要求荐股。')
c(50,'part-funds-practice-qualified-not-every-reader-detail','370-b008','对读者用固定一部分资金做差价，作者说这样也可用部分练习，但仍须把技术真正学好。','操作熟练程度|资金管理|操作策略',1,'短答只明确部分练习，不逐项认可读者低买股永不丢、天天满仓或卖钱必买当天跌股全方案，也没给练习仓百分比。')
c(50,'solve-basics-one-difficulty-at-time-center-first','370-b011','作者要求一个难点一个难点解决，先彻底弄清中枢等最基础问题，反复读仍不懂基础则无法应用。','走势中枢|操作熟练程度|技术分析',2,'学习先后建议，不把读者打印5遍/手抄次数等同掌握或设固定达标课时。')
c(50,'five-minute-moving-no-new-five-center-until-it-ends','370-b014','作者澄清5分中枢推移的前提是尚未出现5分中枢；出现则这次移动结束，不能机械等全部完成才操作。','中枢上移|走势中枢|操作级别|确认',1,'此处指原枢完成后向上推移与新同级中枢出现，非中枢自身同时存在又不存在；出现/形成与已结束离开不同，不把任意低级小枢当5分。')
c(50,'one-down-next-one-up-divergence-or-no-high-can-exit-before-five-center','370-b014 371-b000','5分推移中，一个1分走势向下后再一个1分向上，若背驰或不创新高，作者说意味着一定将成5分中枢，此时可先出来。','操作级别|中枢新生|背驰|卖点|中枢上移',1,'先1分完整走势向下再向上、背驰或不新高不能省为任意1根K或AND；将形成不等此刻新5分中枢已完，作者结构断言未独立验证实时精度/全部执行，和49 30/5例同法不同级别。')
c(50,'framework-before-orderbook-details-promised-not-provided','371-b003','作者要求先建大框架，盘口语言等细节繁琐易迷失，留以后讲，不可喧宾夺主。','操作熟练程度|技术分析|操作策略',2,'只承诺后讲，未交付盘口特征/阈值/完整算法，不能据此称已完成49盘口语言问题。')

note('362-b012','source-study-context','节前多讲操作、节后恢复其他写作的课程缘由。','非用户工作日程或技术交易指令。')
note('365-b001','historical-holiday-closing-context','作者节前想出游及政治评语收尾。','不作为技术买卖/预测或当前日程事实。')
note('365-b009 365-b010 365-b011 365-b012 366-b000 366-b001 366-b002 366-b003 366-b004 366-b006 366-b007','nontechnical-politics-currency-short-essay','4/30空头/央行文章及附录宏观、法律/媒体指控、70%美元配置与券商受益意见完整审读。','只留作者历史观点/指控身份，不判当前法律/税制或官员动机，不将70%配置、夹空1000或政治攻击作技术定理、实测收益或现在建议。')
note('366-b005','source_header','附录头已核，仍属4/30文章。','不是独立技术结论。')
note('366-b008','historical-unverified-999-and-fund-allegation-context','前半999翻两倍/基金动机为未核自述；后半技术实力决定专一/换股另引。','技术命题引用起于给各位一句话以后，不把盈利或恶意指控当已核证据。')
note('366-b009','historical-holiday-context','作者放假七天、去甲骨文地方、7号恢复等日程完整保留。','不执行、也不当当前交易所假期。')
note('366-b011 367-b000 367-b001 367-b002','nontechnical-central-bank-opinion','5/8周行长文章涉及央行、外储、利率等历史批评完整审读。','不作为缠论技术定理或已验证历史机构动机、当前宏观政策结论；作者和读者身份分别留。')
note('368-b008','historical-company-identification-context','作者把VC指向600635、5元多时说过并称20%股东，现涨高不追。','历史公司/持股比例未外核，不认证当今股权或推送荐股，读者938误指不当作者结论。')
note('369-b006 369-b009','nontechnical-music-official-context','作者谈官员古典音乐喜好和不方便多说。','非技术买卖或已核政治人物偏好。')
note('370-b005','historical-script-wave-comparison-context','作者不让这里出背驰的剧本自述，反问何以不能3之3。','不认证操纵能力或作者已严格确认3之3，不把读者日线背驰段被破坏当已发生背驰后可取消的规则。')
issue('MACD-period-linearity-sensitivity-and-missing-formula','362-b013 363-b000','跨周期计算线性/实质相同为作者解释，未给采样/参数形式化；选30图清楚不等30信号或数值等价，先结构/选段再指标。','保持作者文字与既有级别边界，不自补面积窗/跨周期无损换算或只MACD充分判点。',True)
issue('logic-confidence-geometric-guarantee-and-practice-criteria','363-b001 363-b002 363-b003 363-b004 363-b005 364-b000 364-b001 364-b002','反盲信/逻辑及模拟记录顺序明确，但几何般保证收益未附证明，所有既有走势和足够把握无客观达标数，理论正确前提不能代替独立验证。','不把信心与作者自述荐股收益当证据或将失败全责于人；不发真实交易指令，保存静态/动态/实操区别。',True)
issue('historical-centers-later-charts-and-reader-nine-segments','364-b003 365-b000 365-b004 365-b005 365-b007 367-b003 367-b004 368-b000','3745三买未成、3720至3761扩30为作者历史判断；CCTV九段1分是读者解释，图已含4/30与5/9后K，价格小数不静合。','保留读者身份与未来图限制，不把9段充所有中枢必要条件/作者背书或由后K验先验预测。')
issue('very-long-pullback-premise-change-certain-return-and-full-list','368-b010 368-b011 368-b012 369-b000','作者承认长周期制度/规则前提改变可不完全回拉，未变则断言一定回拉；全前提清单、回拉时限/可成交未给。','不把任何价格逆行都称前提变，也不把前提未变强语静软为可能；研究问题日线与年线例作用域分开，理论陈述非实测保证。',True)
issue('five-day-usual-three-day-not-exact-low-high-close','367-b004 368-b000 368-b001 368-b005 369-b002 369-b003','5日/5周简法依能力/行情，45限趋势；通常三天拉不回是不精确延迟确认，未逐项判最低触线/最高低于或收盘、交易日与相等。','不得将三天与47缺口统计或读者三根5分混一硬阈值，保留源码原字和适用限制。',True)
issue('rhythm-partial-practice-concentration-no-reader-plan-endorsement','368-b005 369-b011 369-b012 369-b014 370-b000 370-b001 370-b007 370-b008','997没讲比较段所以未认可卖出；100万以下超5股一般太多，部分练习不背书天天满仓/卖钱买跌股/全部卖重新来，金额比例无统一算法。','按能力/级别/少量练习与等待买点保留；不把集中建议当实证最优组合/风控分散普遍法。')
issue('new-five-center-first-one-down-up-confirmation-execution','370-b013 370-b014 371-b000','5分推移中先1下再1上背驰或不新高可先退出、意味着将成5分中枢；形成与完成不同，尚无全实时确认/费用/成交程序。','不把任意1根K/小枢当完整1分类型/5分中枢，或条件不合并成AND；和49 30/5例及48首修正中枢>5的不同对象联读。',True)
issue('macro-allegations-stock-claims-and-orderbook-not-yet-taught','365-b009 365-b010 365-b011 365-b012 366-b002 366-b003 366-b008 366-b011 367-b000 367-b001 367-b002 368-b008 370-b005 371-b003','政治/法律/机构动机及公司20%/收益与剧本能力未独立核，盘口语言细节仍预告。','完整留历史上下文不升技术事实/当前建议，后查原书盘口课再说已交付规则。')
relations={
 'structure-then-comparable-legs-then-MACD-period':[('MACD','指标对比','qualifies')],
 'study-existing-then-record-live-simulations-before-real-trades':[('模拟操作','操作熟练程度','qualifies')],
 'static-dynamic-actual-learning-sequence-not-days':[('模拟操作','技术分析','qualifies')],
 'apr27-five-center-expanded-thirty-3720-3761':[('中枢扩展','操作级别','qualifies')],
 'wrong-early-sale-no-chase-wait-next-short-buy':[('等待','追高','qualifies')],
 'small-to-large-operate-as-center-oscillation':[('小级别转大级别','中枢震荡','qualifies')],
 'very-long-pullback-premise-change-may-not-fully-return':[('理论成立前提','交易规则','qualifies')],
 'unchanged-premises-author-certain-pullback-not-proof':[('中枢回拉作用','理论成立前提','qualifies')],
 'five-day-three-days-no-return-usual-imprecise-delayed-confirmation':[('均线系统','有效跌破','qualifies')],
 '997-need-comparable-legs-no-endorsement-form-repeat-rhythm':[('操作节奏','操作级别','qualifies')],
 'small-funds-under-million-more-than-five-too-many':[('交易容量','资金管理','qualifies')],
 'one-down-next-one-up-divergence-or-no-high-can-exit-before-five-center':[('中枢新生','卖点','qualifies')],
}
relations={'upper-l050-c-stage-'+k:v for k,v in relations.items()}
scopes={
 'structure-then-comparable-legs-then-MACD-period':['先中枢与走势运动、选定比较段','MACD只辅助，周期选取看清晰度/灵敏度'],
 'study-existing-then-record-live-simulations-before-real-trades':['先静态理论分析已有走势','动态模拟逐次记录并复盘，有足够把握再实际操作'],
 'very-long-pullback-premise-change-may-not-fully-return':['特别长的背驰回拉过程','改朝换代/交易规则完全改变等使理论成立前提改变'],
 'unchanged-premises-author-certain-pullback-not-proof':['理论成立的前提未改变','作者条件内一定回拉的主张，非项目独立实证'],
 'five-day-three-days-no-return-usual-imprecise-delayed-confirmation':['通用均线简法，通常理解的三天拉不回','不精确且确认远离高点，非最终完整判点办法'],
 'one-down-next-one-up-divergence-or-no-high-can-exit-before-five-center':['原5分中枢完成后的推移尚未出现新5分中枢','先一个1分走势向下、再一个1分向上','后向上背驰或不创新高'],
 'small-funds-under-million-more-than-five-too-many':['小资金因品种过多/换股而节奏混乱','一般100万以下，超过5只作者认为太多'],
}
for r in rows:
 if r['id'].split('upper-l050-c-stage-')[1] in scopes:r['conditions']=scopes[r['id'].split('upper-l050-c-stage-')[1]]

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
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], 'CCTV九段1分、997背驰卖出、8股重来、100万以下集中、天天满仓买跌股、日线背驰回拉小转大、5日线低高价与新5分枢完成问法保留身份，按实际作者回复范围不扩大认可。'
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
        'note': '先中枢运动选比较段再MACD，周期计算的作者说明非跨采样数值等价；模拟记录/技能与逻辑不冒几何收益证明，长回拉规则前提可改/未改则一定，通常三天非精确均线口径，1下1上或条件与将形成区分。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=f['note'],
             figure_source_review='实际查看PDF362至371十页两整图：364图含4/30晚于4/27文字，367图含5/9晚于5/8文字；后K不证提前预测，3720.80/3761.99不静改原3720/3761，CCTV九段原为读者未获作者认可。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 105 and Counter(x['lesson_number'] for x in ledger) == {50: 105}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [50], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(362, 372)), 'figure_objects_viewed': 2, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '50课105段10页2整图同模型四轮；28日期空格规范及2后图；MACD顺序/周期、模拟学习、长回拉理论前提及均线三天不精确、新枢将成与或条件分层，历史央行/空头文章保上下文，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


