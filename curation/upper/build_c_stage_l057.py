"""Materialize the main agent's four-pass reading of lesson57.

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
BASE = 'c_stage_l057'
REVIEWER = 'Codex 主代理 / 阶段C上册57课同模型四轮复核'
SOURCE_SHA = '628b3b19023428355fa78cc687d803480de9e476bfd72bd9a0ba52b5dcf23543'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-057' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 66
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 427 AND 436 ORDER BY pdf_page,id', (DOC,))]
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
    pending.append({'id': 'upper-l057-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})


quote_overrides['427-b013']=passages[pid('427-b013')]['text'].split('这些人大概',1)[0]
quote_overrides['432-b001']=passages[pid('432-b001')]['text'].split('（备注：',1)[0]
quote_overrides['431-b000']=passages[pid('431-b000')]['text'].split('，各种',1)[0]
quote_overrides['435-b009']=passages[pid('435-b009')]['text'].split('这股票的中线',1)[0]
c(57,'coach-example-not-real-time-signal-service-self-practice','427-b011','作者以两天1分图作当下分析示范，拒绝QQ实时提示，称自己最多是陪练、学习者需自己练习。','操作熟练程度|当下|周期K线图',2,'作者资金超过所有来者/个人活动为自述未核，非本项目服务承诺；回看图可当下分析是教学主张，不证明每人实盘反应或成交。')
c(57,'novice-not-full-position-trade-base-longer-part-practice','427-b012','不熟者不应全仓操作；作者建议基本仓位持中长线股票，用部分仓位练习，避免半熟反复操作伤本金。','仓位|长期投资|操作熟练程度|操作策略',1,'作者教学建议并非所有人必须持某固定比例/品种，未给量化仓位公式；基本仓保留不等无需风险控制。')
c(57,'sell-on-rise-no-panic-profit-early-new-buy-before-return-author-view','427-b012','作者说卖点在涨时出现而非追杀，宁愿卖早；赚钱就不算卖错，卖错后除非新买点否则不看原股。','卖点|买点|操作节奏|追高',1,'涨时可为大跌后的局部反抽，不保证高于前收/原高；赚钱没错是作者评价，不排除机会成本、费用或所有止损都错误，买回仍需新买点。')
c(57,'not-short-only-annual-decades-weekly-two-years-author-examples','427-b013 428-b000','作者反驳本法只做短线，举年线买点后可能持几十年、当时两年按周线指数无卖点为例。','操作级别|长期投资|买卖点',2,'年线几十年是示意、周线两年为历史作者判断，未统计验证实际最短持有期/全部指数信号；级别应预先确定，不因亏损临时放大逃避退出。')
c(57,'thirty-third-buy-center-up-no-new-center-hold-huge-price-ideal','428-b000','作者设30分三买后中枢上移，若10元起且不形成新30分中枢，即使到100000也应持有，理由为尚无该级卖点。','第三类买点|中枢上移|操作级别|卖点|完成',1,'极端数值是作者模型例不是目标价/真实股票；原无新中枢仍持有保其语境，不覆50未成新枢前可按次级盘背处理的别种操作级别/程序，实际小转大和成交风险未证明。',ambiguity='author_ideal_no_new_center_hold_scope_vs_finer_execution_pending')
c(57,'minimum-analysis-view-three-subsegments-overlap-not-final-segment-definition','428-b001','作者先定最小分析级别，将以下都视线段，在该视角把每段作次级走势，三段重合构成最小分析级别中枢。','最低级别|次级别|走势中枢|操作级别',1,'这是本课粗视角简说，至少三个连续完成次级的完整定义仍保17/18；下文精确三卖不把所有以下都当直接次级，亦非后来特征序列线段定义。',conditions=['先明确最小分析级别、粗视角忽略以下细节','核精确离开/回试时须转用直接次级完整结构标准'],figs=[(428,1)],ambiguity='coarse_view_subsegment_wording_not_all_finer_levels_direct_sublevel')
c(57,'gap01-and-complex23-real-levels-differ-coarse-one-view-same-lines','428-b002','本图最小分析定1分，01缺口比复杂23真实级别低，但二者均无1分中枢，站1分显微镜下都可视无内部结构线段；要看23内部须换视角。','缺口|最低级别|次级别|周期K线图|操作级别',1,'同视角忽略不等原始细级严格相同；所有[N,N+1]是本图标记，不推出任意两高低点都合后来严格线段标准。',figs=[(428,1)])
c(57,'ten-segments-weak-third-not-recognized-consistent-alternative-standard','428-b003 429-b000','本图按十段处理；23/78绿箭头处拟三段的第三段太弱，缩图几乎不可见，89处则明显。若另认78弱段可使78/89合为上涨趋势，但同等弱处须全图统一处理。','走势分解|分解多样性|最低级别|完成',1,'微弱/明显为作者本例观察阈值未数值化，不建任意缩图消失即无中枢定理；另一标准允许不等可为结果任意挑段。',figs=[(428,1)])
c(57,'at0930-no-future-segments-same-standard-through-time','429-b001','作者提醒当日9:30尚无后续线段，但分段标准须与随后保持一致，不能借已知后图改变当时规则。','当下|走势分解|完成',1,'回看示范不是所有后段在开盘已知，未证明提前知道7/9点或真实逐笔执行准确。')
c(57,'precise45-leave56-retest-sublevel-not-all-below-one-4077-third-sell','429-b001','对原1分中枢4087—4122，45离开、含上下上且中段为缺口的56回试具精确次级结构；56只到4077，故点6为三卖。此视角不能把所有1分以下笼统作直接次级。','第三类卖点|次级别|走势中枢|完成|操作级别',1,'45和56均须完成次级结构，粗视角无内部与精看可有内部不冲突；不单凭4077<4087或任意未触边就认三卖。',conditions=['先取原1分中枢4087—4122','切换到精确直接次级视角核45离开/56完整回试，56高4077未触原枢'],figs=[(429,1)])
c(57,'fine56-up-up-area-divergence-needs-skill-reaction-channel','429-b002','精看56上下上，可由后上柱面积不足前上辅助判极小级背驰；作者限精确操作需十分熟练、反应和通道都快，不要求人人能做。','MACD|指标对比|操作熟练程度|交易通道|交易条件',1,'三项执行条件不省，不以图上面积显示证明实际最优价成交；图为示范，大级原理类似不等跨周期参数/数据严格相同。',figs=[(429,1)])
c(57,'67-down-up-down-later-weaker-time-for-space-zero-green-retrace','429-b003 430-b000','67内部下上下，后下绿面积弱于前下；中间上虽幅度小但时间长，是时间换空间反弹，且使绿柱回0轴，故不可忽视。','MACD|指标对比|时间换空间|反弹|操作级别',1,'小幅不自动忽略，时间/指标共同为本例结构证据；未给秒数/幅度比阈值，不能用绿柱回0单独等同完整走势或指标黄白线回0。',figs=[(429,1)])
c(57,'at6-alternate-center345456-23-vs67-oscillation-return-near','430-b001','到6可把34、45、56作另一1分中枢，23与67成为其震荡；比较各段下全部绿面积，后者小，作者判67至少回抽该枢附近，再用内部区间套定位。','分解多样性|结合律|走势中枢|盘整背驰|区间套',1,'另一分解不是原4087—4122枢，段中未明报新枢数值区间，不硬套旧边界；附近不静改精确上沿/必须穿越，回抽为作者本例模型非交易保证。',figs=[(430,1)])
c(57,'if7-first-buy-9-second-no-low-or-consolidation-divergence','430-b001','若把点7当一买，作者称9为二买，符合次级上再次级下、不新低或盘背；与点2一卖同为第二类，78内小回落也有更低级二买。','第一类买点|第二类买点|第二类卖点|次级别|盘整背驰',1,'如果条件不省，不把所有视角点7均强定同级一买；不新低或盘背是OR，78内部二买级别低于9不可并同级。',figs=[(430,1)])
c(57,'ten-lines-group-nine-after-gap-five-center4015-4122','430-b002','十段中以(12+23+34)+(45+56+67)+(78+89+910)组成5分中枢4015—4122；作者据6三卖与后背驰称本例升级必然。','走势中枢|中枢扩展|次级别|完成|结合律',1,'括号实含01缺口之后九段、三组完整次级，不能说十段裸相交；本例必然不普遍推出所有三卖后必升级而不趋势，保56不趋势则转大分支。',figs=[(430,1)])
c(57,'one-chart-demonstration-not-required-use-larger-if-poor-channel','430-b003','作者称示范才分析复杂1分图，大级图一般更简单；技术或通道不好者通常放大观察/操作级别，不必用1分图。','周期K线图|操作级别|交易通道|操作熟练程度',1,'放大级别是选择适合能力的前置策略，不在亏损时随意变更既定操作级别或推迟所有卖点。')
c(57,'jun1-center-oscillation4015-4122-not-policy-fact-proof','430-b004 431-b000','6月1日作者仍把指数走势看作4015—4122中枢震荡。','中枢震荡|走势中枢|操作级别',2,'仅截技术中心判断所需跨页首句，后政策程序/舆论/国债与参与者动机为作者历史立场，不作已核事实。')
c(57,'jun1-missed-sell-no-panic-now-future-higher-author-view','431-b002','6月1日作者对错过此前二三卖者认为当时再卖意义不大，称未来必有大反弹且更高，强调该退出时勿幻想。','第二类卖点|第三类卖点|操作节奏|市场风险',1,'这是特定历史时点作者强判断，不变成普遍跌后永不止损/所有个股必回原价，也未以1996回看例证明当前路径或T+1成交。',ambiguity='historical_future_higher_rebound_claim_not_universal_recovery_guarantee')
c(57,'dont-kill-down30-chase-resilient-strong-compensatory-fall','431-b003','作者警告别卖已跌30%的股去追抗跌上涨股，混乱市应防补跌、保持专一。','补跌|板块轮动|操作节奏|市场风险',1,'历史环境的节奏警告，不是所有强势股都必补跌或任何原弱股都应死守；后40%/20%操作例另列。')
c(57,'down40-rebound20-half-two-thirds-rebuy-lower-author-example','431-b003 432-b000','作者举跌40%、首反弹20%卖半或2/3、回跌买回再反弹，可使退出效果近原高位；有现金时跌40%补仓且非被查庄股，称风险基本小。','仓位|操作节奏|成本|买点|卖点|市场风险',1,'作者示意未给第二轮回落价/费用/成交及20%计价基准，不能计算为已证必然回本或无风险；非被查庄股和技术买卖点条件保留，仍强调以后先二三卖退出。',ambiguity='author_rebound_cost_recovery_example_missing_prices_and_execution')
c(57,'jun1-halfline4144-support3734-3434-before-unverified-note','432-b001','6月1日15:47:30作者说1/2线升到4144，上涨1/3位置3734为首支持，若有特别变化再考验一半3434，但当时未见到该位理由。','1429点历史压力线|价格区间|确认|走势预测',1,'作者引文止（备注：之前；备注的30分/日线笔/月线3K对应关系未核不采。正文3734/3434与图3739.273/3440.034分别保，不重算替换或认证未来强支撑。',figs=[(431,1)],ambiguity='mixed_passage_unverified_trailing_annotation_excluded_from_author_quote')
c(57,'jun1-skilled-center-trade-rebound-at-year-halfyear-forecast','432-b002','作者对有技术者继续按4015—4122震荡操作，预期下周暴跌股反弹，尤其到年/半年线者力度较大。','中枢震荡|操作熟练程度|均线系统|反弹',2,'作者特定日预测/能力条件，未逐股证基本面或反弹收益，也不以未来图当当时可成交证明。')
c(57,'limit-down-MACD-question-look-larger-not-proof-distortion','432-b006','对跌停股票MACD是否失真的疑问，作者要求看大级别，并强调1分示范不等必须1分操作。','MACD|周期K线图|操作级别|跌停',1,'作者没有明确承认所有跌停MACD都失真，也未给修正公式，回复是选择观察级别，不能把问题当已证指标缺陷。')
c(57,'jun4-4341-from2541-1800-time-window-pressure-author','432-b009','6月4日文章回述5月为1429以来180月时间窗，并称4341即2月6日2541上1800，形成技术调整压力。','1429点历史压力线|走势预测|价格区间',2,'按独立6/4文章日期而非6/1回复；4341作者计算与图4335.96高点不同，不静改数或把时间窗变已证明政策预知。')
c(57,'jun4-halfline4144-shenzhen13700-stand-before-midterm-strong','433-b003','6月4日作者以沪4144、深13700两线能否有效站稳判断中期是否复强，站稳前预期震荡消化技术政策压力。','1429点历史压力线|确认|走势预测|市场震荡',1,'独立文章只有日期无时分，不补造时间；沪深模型各自价位不能跨市场套基点或宣称已有效确认。')
c(57,'jun4-morning-five-month-wording3600-normal-adjust-if-no-break','433-b003','作者把当时3600附近原称5月均线作为调整正常与否关键，不有效跌破则正常，否则调整时间大增。','均线系统|确认|市场震荡|操作级别',1,'原5月均线不静改5日线；月线5期解释须另核，432备注来源未明不能拿来强证参数，也不将3600写成全市永久底线。',ambiguity='source_five_month_average_wording_parameter_not_inferred_from_unverified_note')
c(57,'jun4-midyear-quality-leaders-theme-stock-differentiation-forecast','433-b003','作者预期6、7月中期业绩主导，绩优一二线成分股支持指数，三线题材分化；只有真实基本面好转者再强，其余反弹后多进较大调整。','基本面|一线股|二线股|三线股|板块轮动',2,'是作者历史条件预测，不证所有题材股真实业绩、未来涨跌或当前资产推荐，只有/大多数的原范围均保。')
c(57,'jun4-close-average-now3540-rebound-down40-at-halfyear-best-year','434-b003','6月4日收评称下跌后原5月均线变3540，附近短线介入问题不大；反弹选择限跌40%以上、已到半年最好年线，待大盘稳定有较大力度。','均线系统|反弹|操作级别|确认|市场风险',1,'原附近问题不大/一定只能为作者该时判断，非本项目当前建议或40%充分买点；3600前文/3540收评时点不同不硬合，T+1/分批后答仍保。')
c(57,'jun4-full-position-first-big-rebound-sell-half-rebuy-not-universal-hold','434-b004','对当时仍满仓者，作者认为现走意义不大、未来有更好位置，要求首大反弹先兑现半仓、回跌再找机会补，以有资金应对中线震荡。','仓位|操作节奏|成本|市场风险',1,'限定该历史满仓案例，未来更好是作者强预期，不给任何个股/无限时间回本保证，也非跌市都不应止损的普遍指令。',ambiguity='historical_full_position_rebound_plan_not_universal_hold_or_recovery_guarantee')
c(57,'jun4-light-after-second-sell-novice-gradual-targeted-few-stocks','435-b000','已在30日二卖退出、仓位轻者，作者要求准备反弹；技术不足对超跌股逐步、定向、集中买，持几十只操作不过来。','仓位|动态建仓|操作熟练程度|交易容量',1,'本周必然反弹保作者历史强语，不省略实际买点/T+1风险和分批资金安全；集中非全仓押一只或固定组合数。')
c(57,'jun4-average-short-beartrap-divergence-location-MACD-zero-pressure','435-b001','作者把短线跌破原5月均线视空头陷阱，须看随后背驰点位置；预期反弹最直接令30分MACD拉0轴，该轴为反弹最大压力。','均线系统|空头陷阱|背驰|MACD|操作级别',1,'是历史条件预期，零轴是MACD量非价格0或固定目标价；6/13后加反弹图不证当时必停于此/每个跌破都陷阱。',figs=[(434,1)])
c(57,'novice-unseen-buy90-position-wait-batch-T1-risk','435-b006','对读者未见买点却约90%建仓，作者要求耐心等买点：此跌市小级买点若不能T+1跑掉风险大，建仓像赌博应分批，宁少做反弹也保资金仓位。','买点|T+1|动态建仓|仓位|市场风险',1,'90%是读者自述不是建议目标；本条原T+1不用于私改56原T+0，先等点/分批及宁愿没买到的条件不可删。',conditions=['回复读者435-b005未见买点即近90%仓的具体行为','小级买点在该跌市受T+1退出限制，须等点并分批'])
c(57,'ST-five-percent-historical-rebound-after-larger-fall-not-copper-proof','435-b009','对仍持ST者，作者说此前不该买，现只能等反弹，因每天才5%，反弹先让跌得多者。','跌停|反弹|市场风险|操作节奏',3,'历史作者规则/节奏判断，不作当前各ST规则或全部反弹时间保证；技术引文在铜矿注入自述前截止，未认证公司资产事件或主力洗盘动机。')
c(57,'futures-not-risk-insurance-skill-liquidation-author-view','435-b012','作者反驳仅靠有期货即可保障风险的想法，强调技术；有期货也会在牛市多次暴仓。','期货|对冲|操作熟练程度|市场风险',1,'暴仓为原字、对应通常爆仓风险，原别信对冲废话是作者针对问题的强评价，不升级为所有对冲机制无效或认可读者不动产一定更优。')
c(57,'rebound-exit-half-good-skill-small-capital-full-then-select-rebuy','436-b002','对跌40%后何时退出提问，作者以仓位答：半仓；技术好且资金不大可全出，回跌后再挑好品种补入。','仓位|交易容量|操作熟练程度|操作节奏',1,'并未给反弹固定百分比或点位；技术好且资金不大是联合例外，不改或，也不默认普通人都应一律全仓进出。',conditions=['作者针对436-b001跌40%反弹退出的历史问答','半仓为默认回答；全出例外须技术好且资金不大'])
note('427-b010','teaching-introduction-context','作者本周连续说股票和管理层夜半歌声的教学开场。','未作独立技术命题，政策评价/个人烦躁不是已核市场因果。')
note('431-b000 431-b001','historical-policy-media-bond-and-large-capital-opinion-context','中心震荡后作者对政策程序/舆论转向、国债分流、北京股、大资金作用和个人关系作历史论述。','跨页技术引文仅首片段；不认证国债发行/机关动机/本人资金总量或永远中流砥柱等事实，政治人物评价非技术知识。')
note('432-b001','mixed-author-plus-unverified-inline-annotation','段首支持位正文与末备注混在同段；备注称30分枢/日线笔/月线3K/5均线近似对应。','备注来源未核，本批作者引文止备注前，不把备注补为作者原理；整段角色仍混合，原文搜索/上下文可能连带备注的归属问题保持阻断待核，与43夹注后续处理。')
note('432-b008 432-b010 433-b000 433-b001 433-b002 433-b004 434-b000 434-b001 434-b002','jun4-independent-policy-article-and-ancient-quote-context','6/4独立文章的舆论/调控/监管成熟度、个人未受伤害及基本面价值观，结尾论语引文与同日收评政治段完整已读。','文章11段角色/日期修为author_commentary/2007-06-04仅日，不承接6/1回复；政策主张/内幕与自身绩效未外核，嵌套引文不当作者自创技术定理，非当前法律金融建议。')
note('435-b009','historical-ST-copper-injection-and-market-cleanliness-self-report','作者5%/反弹节奏之外称该股中线铜矿注入取决盘面干净程度。','作者技术引文排除此资产/主力动机自述，未验证公司/矿权或用读者ST问自动识别公司代码。')
keep('435-b002','upper-l056-c-stage-may29-divergence-leg-unconfirmed-before-gap-first-sell-unavailable','6/4重申30日二卖该走以保反手资金，保56突发前一卖未确认/指数个股区别与实际执行限度；只台账关联，不改旧命题/证据。')
issue('coarse-view-precise-sublevel-and-weak-line-standards','428-b001 428-b002 428-b003 429-b000 429-b001','最小分析下把以下作线段/次级是粗视角，精确三卖则不能所有以下都当直接次级；微弱第三段是否认作结构允许全图统一另一标准。','保至少三连续完成次级的既有定义，不把缩图看不见变固定数学阈值，线段比喻与62/72严格结构定义分层，现无通用参数化弱段规则。',True)
issue('alternate-centers-if7-first-grouped-five-and-return-near','430-b001 430-b002','34/45/56另一1分中枢不同原4087-4122；23/67面积比较回附近，7若一买9二买且78内部二买更低；三组九段扩5分。','不硬补另一枢未报的数界、不删如果/或/附近、不把十段全交集或三卖后一律必扩当总规则；多解一致性/全分段还需跨课核。',True)
issue('preselected-level-hold-ideal-and-novice-capital-risk','427-b012 427-b013 428-b000 429-b002 430-b003','不熟勿全仓、部分练习；预设大级可长期持有，30三买后无新30枢极端持有例为作者理想，精细执行须技艺反应通道均快。','不能将年线几十年/10到100000当实测时长/目标价，或以粗级无枢取消50提前程序/小转大风险；不得因亏损改级别。',True)
issue('mixed-annotation-role-date-and-source-boundaries','432-b000 432-b001 432-b002 432-b006 432-b007 432-b008 433-b003 434-b001','2段按前尾15:47:30承接、11段6/4独立文章改角色日期仅日，432-b001末备注仍混合作者/未核旁注。','本批不改原文字几何，作者引用避备注；整段原文搜索/上下文归属仍可能混淆，须后续范围拆分/独立标识，与43夹注一并修，不能把仅避引文说成来源隔离已完成。',True)
issue('historical-support-five-month-wording-body-vs-figure-prices','432-b001 432-b009 433-b003 434-b003 435-b001','正文3734/3434与图3739.273/3440.034、4341与图4335.96分开；原5月均线上午3600/下跌后3540，参数不借未核备注强证。','均线原词不改5日线；确认时点/条件不同不硬合为固定支撑，沪4144/深13700各自模型；MACD0轴为指标量非股价目标。',True)
issue('rebound-cost-recovery-half-position-and-execution-guarantees','431-b002 431-b003 432-b000 434-b003 434-b004 435-b000 436-b001 436-b002','未来更高/40跌20弹多次近高位退出/当前满仓等反弹/半仓兑现为作者历史预期和示意，未给完整价格成本或成交证明。','不计算成所有人必回本或普遍下跌不止损；非被查庄股、技艺/小资且条件均保，仓位回答不冒固定反弹点位。',True)
issue('T1-batch-entry-futures-and-ST-historical-scope','432-b005 432-b006 435-b005 435-b006 435-b008 435-b009 435-b011 435-b012','作者明言未见点近90%像赌博，应等买点/分批，若小级不能T+1跑风险高；ST5%与期货暴仓为该时/问答范围。','不将57 T+1静改56 T+0，也不承认所有跌停MACD失真或所有对冲无效；铜矿注入/读者不动产更优及账户事实均未核。',True)
issue('five-figure-origins-policy-forecasts-and-independent-gold-limits','428-b002 429-b001 430-b001 431-b000 432-b001 433-b003 434-b003 435-b001','5整图3原发未核2后加，日线右端7月、30分右端6/13；监管/舆论/恢复与绩优轮动为作者历史观点。','后图不证早期预测/最佳成交，同模型四轮和模式能力不当独立/人类金标准或Windows交付验收。')
relations={
 'minimum-analysis-view-three-subsegments-overlap-not-final-segment-definition':[('最低级别','次级别','distinguishes')],
 'gap01-and-complex23-real-levels-differ-coarse-one-view-same-lines':[('缺口','操作级别','qualifies')],
 'ten-segments-weak-third-not-recognized-consistent-alternative-standard':[('分解多样性','最低级别','qualifies')],
 'precise45-leave56-retest-sublevel-not-all-below-one-4077-third-sell':[('第三类卖点','次级别','requires')],
 'fine56-up-up-area-divergence-needs-skill-reaction-channel':[('交易条件','交易通道','requires')],
 '67-down-up-down-later-weaker-time-for-space-zero-green-retrace':[('时间换空间','反弹','qualifies')],
 'at6-alternate-center345456-23-vs67-oscillation-return-near':[('分解多样性','结合律','requires')],
 'if7-first-buy-9-second-no-low-or-consolidation-divergence':[('第二类买点','次级别','requires')],
 'ten-lines-group-nine-after-gap-five-center4015-4122':[('中枢扩展','完成','requires')],
 'novice-not-full-position-trade-base-longer-part-practice':[('仓位','操作熟练程度','qualifies')],
 'dont-kill-down30-chase-resilient-strong-compensatory-fall':[('补跌','操作节奏','qualifies')],
 'jun4-average-short-beartrap-divergence-location-MACD-zero-pressure':[('均线系统','空头陷阱','qualifies')],
 'novice-unseen-buy90-position-wait-batch-T1-risk':[('T+1','动态建仓','qualifies')],
 'futures-not-risk-insurance-skill-liquidation-author-view':[('期货','市场风险','qualifies')],
 'rebound-exit-half-good-skill-small-capital-full-then-select-rebuy':[('仓位','交易容量','qualifies')],
}
for r in rows:r['relations']=[dict(source=a,target=b,type=t) for a,b,t in relations.get(r['id'].split('upper-l057-c-stage-')[1],[])]


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
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], '读者90%无点建仓/跌停MACD失真/ST取舍/期货保险与反弹幅度问题保reader，作者没无条件认可其事实和推论；半仓/全出答仓量非固定点位，技艺与T+1条件均保。'
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
        'note': '粗视角全部以下线段化与精确次级离返不同，弱段标准须整图一致；34-45-56另枢/23-67比较、如果7一买9二买及三组九段高枢各有条件；新手部分练习/T+1等点分批，理想持有/反弹回本非实证；6/4独立文章角色日期已修，未核备注原文搜索边界仍未修，3734/3434和图差/原5月均线不静合。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=f['note'],
             figure_source_review='实际查看427至436十页及5整图、432完整页：428原图/429-430重绘至5/31在夜间正文前可得但原发未核，431日线右7月/434三十分右6/13为后加；正文3734/3434与图3739.273/3440.034不改。混合备注不作作者证据，未来K不证当时预测/成交。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 66 and Counter(x['lesson_number'] for x in ledger) == {57: 66}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [57], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(427, 437)), 'figure_objects_viewed': 5, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '57课66段10页5整图同模型四轮；11段独立6/4文章改角色/日期、2新时间及10空格，3图未核2后加；粗视角/精次级、另一分解/有条件点标、T+1和仓位/反弹理想及未核备注边界分层，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


