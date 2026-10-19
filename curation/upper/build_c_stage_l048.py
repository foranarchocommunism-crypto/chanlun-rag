"""Materialize the main agent's four-pass reading of lesson48.

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
BASE = 'c_stage_l048'
REVIEWER = 'Codex 主代理 / 阶段C上册48课同模型四轮复核'
SOURCE_SHA = '575d11fc9bbd40f003360b5e7e8c67df99aa28b69325f3ba4c7fed5c653ab841'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-048' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 130
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 347 AND 355 ORDER BY pdf_page,id', (DOC,))]
assert len(figures) == 1
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
    pending.append({'id': 'upper-l048-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})




















c(48,'bull-crash-and-bear-rebound-historical-counterexamples','347-b012 347-b013 348-b000','作者将牛市暴跌比作猛烈短暂的调整，举停国债期货后三天指数不到550至920上再跌及1996年12月1250上至850附近后仍涨作牛熊反向剧烈波动例。','宏观市场判断|牛市阶段|调整|反弹|走势预测',3,'作者历史类比与行情数字，未外核并不证明任何当前暴跌均短暂或所有反弹可卖；原419双关保留，不将性/道德讽刺当技术条件。',ambiguity='historical_cases_and_bull_market_premise_not_verified')
c(48,'large-top-repeated-attacks-V-top-basically-not-real-author-view','348-b000','作者主张真正大顶由反复冲击形成、有时间反应判断，V型顶在大型走势中基本不会成真正顶部。','顶|走势预测|操作级别|市场风险',2,'保留大型走势/基本及作者强断言，未把类比概率0当实测；不能据此排除所有突发V顶或保证卖出时间/通道。',ambiguity='author_large_scale_top_generalization_not_probability')
c(48,'price-PE-variable-not-absolute-risk-scale','348-b001','作者反对仅以股价或市盈率高低判断风险大小，因两者会变动而无绝对意义，并称市场任何时候均存在风险。','市场风险|基本面|价格区间',1,'记录作者风险观，不把市盈率无绝对意义改写为完全无信息，也不承认低价必安全或高价必危险。')
c(48,'risk-control-level-and-zero-cost-absolute-safety-author-claim','348-b001','作者声称理解其理论可把风险控制在操作级别、利用风险降低成本，并称0成本是绝对无风险；理解不足时可用均线系统控制风险。','市场风险|零成本持仓|成本|操作级别|均线系统',1,'保存原文绝对措辞但只作为作者方法/成本核算观，未证明剩余市值、机会成本、流动性、制度和执行风险全消失；不作项目的金融安全保证，均线简法还需45趋势/盘整限制。',ambiguity='author_absolute_zero_cost_risk_claim_not_economic_risk_proof')
c(48,'relative-wealth-growth-and-losing-chips-in-bull-market','348-b002','站在财富增长与牛市前提，作者把增长赶不上社会平均及上涨中不断丢筹码视作风险；无做空机制且未永久退出市场时，做空最终仍为做多。','市场风险|持股|牛市阶段|资金管理',2,'3元1万股、4元1千股、30元零股为例非回测；相对收益目标及当时制度前提，不扩大成所有制度/资产永远应满仓。')
c(48,'before-zero-lower-cost-after-zero-increase-chips-bull-goal','348-b003','作者的目标是成本0前降成本、0后增筹码，至大牛市结束持股最多且成本0，把震荡作为降本增筹码机会。','零成本持仓|成本|持股|市场震荡|操作策略',2,'理想策略及作者自述非已经实现的绩效；不是拒绝所有卖出，须与后答特大级别卖点及容量/资金利用率联合，未给通用无损仓位算式。')
c(48,'correction-levels-long-bull-projection-author-only','348-b004','作者承认中短线能量耗尽会大调整，并认为日、周、月、季、年都可能出现猛烈调整；其至少20年牛市论是本文历史前提。','调整|操作级别|牛市阶段|走势预测',2,'原227/419为日线例，20年以上不是项目现时预测；精度影响降本增筹码为作者主张，不证明技术收益必然排序。',ambiguity='historical_twenty_year_projection_not_current_forecast')
c(48,'correction-magnitude-depends-level-weekly-seven-case','348-b005','作者强调日线与年线暴跌力度不同，并称从2005年中至本文时两次周调整均7%、月线未有真正有意义下跌。','调整|操作级别|周期K线图|幅度',2,'作者历史幅度和有意义的定性语未外核，不将7%当周调整上限或日/年固定倍数。')
c(48,'skill-not-enough-for-daily-choose-weekly-monthly','348-b006 349-b000','若把握不了日线调整，作者建议选择周线、月线等技术精度要求较低的级别，按能力安排活动。','操作级别|操作熟练程度|调整|操作策略',1,'能力与级别配合，不是已进场后为拖延卖出任意放大级别；低精度不等无风险、免确认或无限持有。')
c(48,'apr24-previous-small-center-support-five-minute-consolidation-top','349-b002','4月24日收评称前日3688至3692小中枢提供支持，下午出现5分盘整顶背驰，据此认为相邻日的日内走势有技术意义。','每天走势上的中枢|盘整背驰|每日走势分类|价格区间',2,'历史判读未外核；配图含4/25后K，不能用后图认证4/24判点或收益；后4/25段写3699不静改此处3692。',figs=[(349,1)],ambiguity='historical_level_price_and_mixed_next_day_figure')
c(48,'apr24-volume-balanced-five-day-gap-breakout-branches','349-b002','作者判4月24日为收得一般的巨量平衡市，5日线上来后站稳则寻机上攻，否则受前缺口吸引；须有效向上突破当日中枢，否则大幅震荡难免。','平衡市|成交量|均线系统|缺口|突破|走势预测',2,'保留条件分支/作者强语，不把巨量一律当顶部或站稳后必涨；本文未给5日线有效站稳统一数值标准。')
c(48,'short-trade-center-direction-medium-five-week-not-random-switch','349-b003','4月24日作者要求短线按当日中枢最后演化方向决定进出，中线看5周均线，并反对当时随意换股。','操作级别|均线系统|操作策略|中枢震荡',1,'限该收评资金级别语境，不把5周线替代所有中线条件；晚换股与所有换股均错误不同，原段尾4/25时标不属此4/24正文。')
c(48,'apr25-return-3688-3699-oscillation-price-difference-retained','349-b004','4月25日收评称低开后很快回到前天3688至3699小中枢，意味着中枢震荡继续；此处3699与此前3688至3692原字不同，分别保留。','每天走势上的中枢|中枢震荡|价格区间|确认',1,'4/25身份经独立时间头及续文核对，未静合数值或声称误字已解决；回区间为该案判断非任何一次回抽都排除后续大跌。',figs=[(349,1)],ambiguity='source_3692_versus_3699_not_normalized')
c(48,'apr25-first-three-bars-most-balanced-case-not-universal','349-b004','作者称该日前三根30分K基本确立平衡市形态与震幅，属于最平衡一类，前三根已给全天高低，下午下探为短线对冲机会。','每日走势分类|平衡市|每天走势上的中枢|对冲|高低点',2,'最平衡是该案描述，非正式新增互斥类别；作者事后所见全天极值和送钱比喻不保证所有日第三根后极值不再变、或交易无亏损。',figs=[(349,1)])
c(48,'apr25-1335-1030-line-trumpet-conditional','350-b000','作者认为4月24日13:35与25日10:30连线必须突破，否则会被技术派视作喇叭形态。','高点连线|技术分析|突破|走势预测',2,'作者借外部图形术语条件判读，不新增无定义的所有喇叭形态收益规则，也不让后涨K证明提前必突破。',figs=[(349,1)])
c(48,'apr25-3689-3745-five-center-extension-third-points','350-b000','作者将4月24日09:31起3689至3745视作5分中枢延伸，结束要看明后两天是否形成三买卖点，主张等待市场给出而非预测。','中枢延伸|第三类买卖点|等待|走势中枢|价格区间',1,'属于4/25收评的大点视角与后答中枢区间，不把从09:31起的单段当一个完整中枢；三点需原定义级别/回试条件，不是任意越界。',figs=[(349,1)])
c(48,'first-sell-most-active-second-next-third-later-skill','350-b006 352-b001','作者称一卖最主动、二卖也好、三卖较晚且更累，应尽量一二卖操作；级别越低难度和精度要求越高，需实践。','第一类卖点|第二类卖点|第三类卖点|操作熟练程度|操作级别',1,'三卖离真正高位较远是所述退出取舍，不否定三卖有效性，也不是所有价格路径收益严格排序。')
c(48,'effective-break-same-as-third-sell-no-three-bars-rule','352-b001','对有效跌破的追问，作者说是否有效跌破与有没有三卖是一个意思，仍建议最好一卖、最多二卖操作。','有效跌破|第三类卖点|第一类卖点|第二类卖点',1,'读者连续三根5分收3688下、击穿反抽不回等提案只作问题；作者答给三卖概念，未认可固定三根K数量阈值或免除三卖次级别完整定义。')
c(48,'two-centers-trend-can-end-any-time-not-must','351-b005','作者强调趋势有两个中枢后即可随时结束。','趋势|走势终完美|走势延伸|走势中枢',1,'两个中枢是趋势结构必要语境，不表示任意两中枢即已成趋势、第三卖后固定两波必结束或禁止后续继续延伸。')
c(48,'intraday-down-below-one-divergence-and-trend-level-may-differ','351-b005','作者认为所问盘中下跌基本不会是1分、更可能1分以下；背驰级别与趋势级别不一定相同，否则无小级转大。','背驰|操作级别|趋势|小级别转大级别',1,'限47例盘中下跌，基本/更可能不是所有日内跌的普遍定级；级别不相同不允许背驰大于其所处当下走势类型，保留43包含边界，未答1408精确判点。')
c(48,'panic-exit-without-five-day-week-break-case-rebuke','351-b010','对无法日间看图而恐惧清仓者，作者认为5日线未破、中线5周线未破时如此操作更易出错。','均线系统|市场心理|操作级别|操作策略',2,'历史针对性评价，不把均线未破视为所有股票没有风险/永远不能卖；45趋势非盘整限制及既定操作级别仍需保留。')
c(48,'fear-half-position-first-psychology-not-guaranteed-profit','351-b011 353-b004 353-b005','极度恐慌承压时作者建议半仓或不看、中线看5周线，先调心态再技术、量力而行并知后果；技术及心态好者不适用上述建议。','仓位|市场心理|均线系统|操作熟练程度',1,'半仓是此处明确原词，不能回填别课含糊半仓为统一50%或当收益保证；肯定不会错为作者心理取舍强语，非市场涨跌风险消失，不扩成医学建议。')
c(48,'potential-not-current-buy-wait-large-point-hold-until-sell','351-b014 352-b003 352-b004','作者拒绝此时推荐新股：有中线潜力不等现在有好买点，不必追高；机会可等待，已有者等较大级别卖点、未出则持有。','买点|卖点|追高|等待|持股|操作级别',1,'本文当时14股等自述不证明未来表现；大调整后表现断言为作者条件内看法，持有前提不是任何套牢头寸无限展期。')
c(48,'bad-results-not-fall-strong-after-adjustment-heuristic','352-b005 353-b008','作者把坏业绩公布不跌反涨、随大盘调整后仍强者视作潜在黑马线索；好年报季报却明显出货走势则应小心。','基本面|技术分析|市场风险|确认',3,'历史选股经验非可验证通用预测器；只说走势相对业绩，不认证相邻段公司故意造差业绩阴谋，未列名单/收益率。',ambiguity='historical_heuristic_without_verified_sample_or_company_intent')
c(48,'star-ST-without-accurate-understanding-avoid-delisting-risk','352-b007','作者建议没有特别准确把握、不了解时不要买星号ST，理由是买错退市很麻烦，即使自称掌握若干也不鼓励不明者照买。','市场风险|基本面|操作熟练程度',2,'固定2007语境风险提醒，不核当今ST制度/名单、也不认证作者掌握公司内幕；本段不是足够把握就无退市风险。')
c(48,'third-center-C-means-rise-extension-qualified-short-reply','352-b011','对a+A+b+B+c+C问题，作者短答一般如此，有C中枢意味着上涨延伸，可参照只有两个中枢的情况。','走势延伸|同级别分解|走势中枢|上涨',1,'一般如此保留，读者B必下上下、反向并b、c还是c撇分解点及是否小转大未逐项明确答；不把整串问法自动变作者定理。',ambiguity='compressed_reply_not_each_reader_subquestion_endorsed')
c(48,'bull-first-constituent-second-growth-stock-stage-view','352-b014 352-b015 353-b000','作者把牛市第一波重点放成分股、第二波成长股科技股，称其938、998为整牛市布局、第一波可慢，并把科技股动与大盘调整联系为节奏。','牛市阶段|成长性|板块轮动|操作策略',3,'作者当时布局/节奏观点，不认定所有牛市行业次序、具体证券未来收益，未把原年14只静改为已核本年14只。',ambiguity='author_historical_sector_order_not_market_law')
c(48,'no-same-level-divergence-new-center-or-small-to-large','353-b011','该级别不背驰时，作者给两种选择：形成新中枢或小级别转大级别。','背驰|中枢新生|小级别转大级别|走势延伸',1,'针对趋势第二中枢后提问，不是无同级背驰就唯一继续同向上涨；读者d与c或b比较/MACD回轴方案未逐一认可。')
c(48,'mirror-chart-buy-sell-equal-structure-all-levels','353-b014','买熟卖不熟时作者建议可反过来看走势图、见买点去卖，最终应平等对待买卖点、不存偏好；各级别图形结构相同。','买卖点|自相似性|市场心理|操作级别',1,'作为买卖对称学习方法，不修改真实价格/交易方向，也不保证镜像后所有费用、制度、流动性对称。')
c(48,'thirty-operation-tolerates-five-normal-correction','354-b001','30分操作中，5分背驰在可忍受范围内；正常情况下只引发5分走势类型修正。','操作级别|背驰|走势类型|调整',1,'正常情况下限定不能删，与后文第一修正中枢级别变大联读，不推所有5分背驰绝不形成大转折或每次均须30操作者全清。')
c(48,'correction-first-center-above-five-exit-atleast-thirty-consolidation','354-b001','若上述5分背驰后修正的第一中枢级别大于5分，作者要求先出来，因为至少形成30分盘整，这也是需要二卖的原因；精细办法以后讲。','第二类卖点|操作级别|盘整|走势中枢|小级别转大级别',1,'第一中枢/大于5分/至少30分不可删，不改成任意5分背驰或任意跌破价格；文中未给完整进行式识别/成交时刻程序，不以已有大中枢事后确认为提前无延迟信号。')
c(48,'large-capital-zero-cost-strategy-small-not-necessary-channel','354-b012','作者说10万元没必要照此降本持有法，10亿元则须考虑；大资金不能整天换股，换股对精度、操作时间和通道要求高，规模增长可遭瓶颈。','交易容量|零成本持仓|交易通道|资金管理|操作熟练程度',1,'10万/10亿为作者对比示例而非精确定量分界，也不认证任何规模唯一可用策略，保留资金容量与执行渠道条件。')
c(48,'short-difference-zero-best-doubling-not-predictable','355-b001','作者认为通过短差做到0成本最好，因为无法预测某股一定翻倍或数倍，等翻倍的降本法不一定实用。','零成本持仓|成本|操作策略|走势预测',1,'这是目标/取舍，未证明短差总能成功或成本软件算法一致；不能把跌后亏损仍记剩余成本0当经济无损。')
c(48,'double-price-return-capital-depends-better-use','355-b001','若真翻倍且取出资金有更好选择，作者允许先抛至成本0；否则可继续短差，讨论关键是资金利用率。','零成本持仓|资金管理|成本|操作策略',1,'原但依然不动语义保留待核，未明确软件先买后卖成本显示算法，未补扣费/税/分红/复权净额公式；读者卖一半提案非该段唯一普遍规则。',ambiguity='original_but_still_not_moving_and_cost_accounting_not_formalized')
c(48,'after-zero-gain-chips-until-very-large-sell','355-b001','作者说成本为0后要赚筹码，直到特大级别出现卖点。','零成本持仓|持股|卖点|操作级别',1,'特大级别无统一分钟数，不是0成本永不卖出；与容量和能力约束联查，未给全部中间短差仓位规则。')
c(48,'first-segment-in-third-case-center-range-not-single-segment','355-b005','作者确认读者所指09:31起的是第一段，但该第一段完全被后第三段包含，因此此例三段中枢区间等于第一段区间；他所说是中枢区间。','走势中枢|重叠|包含关系|价格区间',1,'这是该例三完整区间的答复，不说单段自身构成中枢；仅第一被第三包含不足一般证明第二也覆盖，第二段完整范围仍需查图核；三段不静改为三K。',ambiguity='case_intersection_equal_first_not_two_intervals_sufficiency')
c(48,'force-computable-no-formula-MACD-proxy-no-escape-physics-law','355-b009','对逃逸速度类比作者说可以计算，但自编程序麻烦、用MACD即可；本段未给计算式。','动力学|MACD|缠中说禅趋势力度|指标对比',1,'答可计算不等认同读者引力质量/唯一逃逸阈值物理公式，未给数值函数或普适充分判据；不以MACD代替形态/级别条件。')
c(48,'c-force-above-b-not-necessarily-disjoint-new-center','355-b009','作者纠正c力度比b大不必然生新中枢：特殊情况是小级转大；某意义亦可说成新中枢，但它最后与原中枢重合。','动力学|中枢新生|小级别转大级别|中枢扩展|重叠',1,'不能把c强于b只给新生同级不重叠C，亦不把所有c强于b都判成小转大；读者弱于b则转折未被本句逐条证明。')
c(48,'trend-new-centers-no-overlap-same-level','355-b009','作者强调真正趋势中的新中枢不能与前同级别中枢有任何重合。','趋势|同级别|走势中枢|重叠|中枢新生',1,'同级别与中枢本身区间不可省，不扩大成围绕中枢全部瞬时波动区间也必须不交；与20课扩张/扩展及高级中枢关系联合查，不将重合大中枢算继续同级趋势新生。')

note('349-b001','source-closing-context','作者收尾谈精度须实践和419双关。','不作为独立行情或性/道德规则，不执行原文行为。')
note('350-b001 350-b002','historical-sector-political-commentary-context','板块切换、基金市值动机及社论政治评语完整保留上下文。','不把未核机构动机/政治指控作技术事实或当前新闻。')
note('350-b009','historical-sector-uncertainty-context','作者称二三线转换还未必成、题材应收敛、个股分化及群庄乱舞。','保留对349板块切换的不确定性；不认证公司案件、主力意图或所有题材股未来必跌。')
note('350-b012 350-b015','historical-policy-sector-short-replies','政策社论传闻和银行股弱表现的作者短评已读。','传闻和人物评语不是已证新闻，短答未形成通用量化买卖规则。')
note('352-b006 352-b008','unverified-company-intent-context','故意做差业绩、N公司阴谋及找异动的说法保留原作者语境。','未核公司意图/名单，不把指控升作reviewed事实或鼓励依所谓内幕买股。')
note('353-b003','historical-psychology-metaphor-context','作者称震荡好玩、让不想51持股者出去。','不构成所有震荡可盈利或清仓者错误的定理。')
note('354-b006 354-b009','nontechnical-currency-regulator-opinion','人民币升值应对、央行和监管部门政治评价已读。','保留作者历史意见与读者地缘推测身份，不抽成缠论技术命题/当前政治经济事实。')
issue('bull-crash-large-top-twenty-year-and-historical-numbers','347-b012 347-b013 348-b000 348-b004 348-b005','牛市前提、V顶基本不成大顶及20年以上为作者强判断，550/920、1250/850及周7%均未独立行情验证。','保留历史/级别和基本等量词，不将牛市认定作已证外部事实或把V顶概率0做统计值。')
issue('zero-cost-absolute-risk-accounting-software-capacity-and-turnover','348-b001 348-b002 348-b003 354-b012 355-b000 355-b001','零成本绝对无风险是作者成本观强语，不能证剩余市值/机会/执行风险全无；软件记账与但依然不动未形式化，10万/10亿不是硬阈值。','后查49/96等容量/零成本补充；保留条件，未补具体净额/手续费/分红/复权公式或无损策略。',True)
issue('commentary-dates-3692-3699-and-later-figure','349-b002 349-b003 349-b004 350-b000','4/24正文和两日收评混排，4/25时间需独立；3692与3699按原字分列，图含4/25收盘不证4/24预测。','只修日期元数据，保留原字/坐标；原始图作者待核，不以图内同为3699静改前3692。')
issue('effective-break-third-sell-not-three-five-bars-or-all-boundaries','350-b005 350-b006 351-b009 352-b000 352-b001','有效跌破与三卖同义但未认可读者三根5分收低阈值；有效站稳及所有三卖子级确认/等值细则未此段穷尽。','沿既有三买卖定义查证，不把读者假设变作者定理；一二卖主动与三卖保守取舍分开。',True)
issue('two-centers-can-end-level-mismatch-and-first-correction-center','351-b001 351-b002 351-b003 351-b004 351-b005 354-b001','两枢可随时结束非必结束；盘中例更可能1分以下，背驰/趋势级别不一但受包含上界；修正第一枢>5则至少30盘整，精细后说。','未补1408精确确认或第一中枢进行式/二卖完整程序，保留小转大例外，不让30操作者任一5背驰都全清。',True)
issue('C-extension-short-reply-no-endpoint-or-comparison-endorsement','352-b010 352-b011 353-b010 353-b011','一般如此短答未逐一答B下上下、并b、c撇分解点、d比c还是b；无同级背驰有新枢和小转大两分支。','保持问答身份及概括范围，不从含糊短答填完整同级分解/力度计算程序。',True)
issue('first-segment-range-third-contains-not-single-center','350-b000 355-b003 355-b004 355-b005','作者说中枢区间等首段、首段在第三段内；还需完整第二段范围，不可一般化为只要首第三包含就证明三重交集。','读者09:31到10:25只一段疑问为上下文；图三段标注保留未当独立原作者定义，核三完整走势区间。',True)
issue('force-calculable-no-formula-and-c-stronger-small-to-large','355-b007 355-b008 355-b009','可计算但没给公式，未背书物理引力质量/逃逸速度模型；c强不必新生不交中枢，可小转大并最后重合。','保留强弱比较对象/同级中枢不交边界，后查力度公式和扩展/扩张，不能新增物理阈值或c强唯一继续趋势。',True)
issue('fear-position-skill-mean-line-and-sector-claims','351-b010 351-b011 351-b014 352-b003 352-b004 352-b005 352-b006 352-b007 352-b008 352-b014 352-b015 353-b000 353-b004 353-b005 353-b008','恐慌半仓强语为心理应对，技术心态好者例外；5周简法与45趋势限制并存，选股/机构阴谋和板块阶段未实证。','按当时能力/资金/买卖点保留；不得将本文半仓统一回填所有课程，不认证公司主观故意造假或当今荐股。')
relations={
 'risk-control-level-and-zero-cost-absolute-safety-author-claim':[('零成本持仓','市场风险','qualifies')],
 'before-zero-lower-cost-after-zero-increase-chips-bull-goal':[('零成本持仓','持股','qualifies')],
 'skill-not-enough-for-daily-choose-weekly-monthly':[('操作熟练程度','操作级别','qualifies')],
 'effective-break-same-as-third-sell-no-three-bars-rule':[('有效跌破','第三类卖点','qualifies')],
 'intraday-down-below-one-divergence-and-trend-level-may-differ':[('背驰','小级别转大级别','qualifies')],
 'correction-first-center-above-five-exit-atleast-thirty-consolidation':[('第二类卖点','盘整','qualifies')],
 'large-capital-zero-cost-strategy-small-not-necessary-channel':[('零成本持仓','交易容量','qualifies')],
 'first-segment-in-third-case-center-range-not-single-segment':[('走势中枢','价格区间','qualifies')],
 'force-computable-no-formula-MACD-proxy-no-escape-physics-law':[('动力学','MACD','qualifies')],
 'c-force-above-b-not-necessarily-disjoint-new-center':[('中枢新生','小级别转大级别','qualifies')],
 'trend-new-centers-no-overlap-same-level':[('趋势','中枢新生','qualifies')],
 'after-zero-gain-chips-until-very-large-sell':[('零成本持仓','卖点','qualifies')],
}
relations={'upper-l048-c-stage-'+k:v for k,v in relations.items()}

scopes={
 'relative-wealth-growth-and-losing-chips-in-bull-market':['作者所假设大牛市','无做空机制且不永久退出市场'],
 'short-trade-center-direction-medium-five-week-not-random-switch':['4月24日解盘，短线与中线分开'],
 'thirty-operation-tolerates-five-normal-correction':['30分钟级别操作','5分钟背驰正常修正情形'],
 'correction-first-center-above-five-exit-atleast-thirty-consolidation':['30分钟操作中5分钟背驰后的修正','修正第一中枢级别大于5分钟'],
 'fear-half-position-first-psychology-not-guaranteed-profit':['恐惧承压、先调节心态','技术和心态好者不适用该退让建议'],
 'large-capital-zero-cost-strategy-small-not-necessary-channel':['资金已大到影响换股/通道与操作时间','10万与10亿是例示非硬门槛'],
 'first-segment-in-third-case-center-range-not-single-segment':['4月24日起3689至3745这一例的三段中枢','作者已判第一段区间为共同部分，不能独靠第一第三包含一般推出'],
 'trend-new-centers-no-overlap-same-level':['真正趋势中的同级别新中枢','所比为中枢区间本身，不是全部围绕波动范围'],
}
for r in rows:
    if r['id'].split('upper-l048-c-stage-')[1] in scopes:r['conditions']=scopes[r['id'].split('upper-l048-c-stage-')[1]]

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
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], '读者3根5分收低、1408问法、B的方向/c撇/d比较、首段与逃逸速度物理类比和记账软件问题保留身份，不自动当作者认可；读者宏观与恐惧自述不当独立事实。'
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
        'note': '0成本绝对无风险为作者策略/核算观非经济风险全无；三卖有效跌破不认读者三根阈值，两中枢可完非必完，第一修正中枢>5/至少30、同级新枢不交及小转大例外联读，3692/3699不静改。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=f['note'],
             figure_source_review='实际查看PDF347至355九页和349整图，上证5分含4/25收盘与4/25文字；相对4/24正文/收评为后图，4/25当日可得但原发身份未核，不能证早一日预测；3699不自动修3692。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 130 and Counter(x['lesson_number'] for x in ledger) == {48: 130}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [48], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(347, 356)), 'figure_objects_viewed': 1, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '48课130段9页1整图同模型四轮；4段跨日时间纠正及55空格规范、后图/原发未核；零成本强语/容量、三卖有效跌破、两枢可完及小转大、修正首枢与同级趋势边界分层，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


