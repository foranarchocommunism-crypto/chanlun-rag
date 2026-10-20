"""Materialize the main agent's four-pass reading of lesson55.

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
BASE = 'c_stage_l055'
REVIEWER = 'Codex 主代理 / 阶段C上册55课同模型四轮复核'
SOURCE_SHA = '98878f30976d10586b2621145a00971773664b7cb3cbc7e9f38acc8989664c15'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-055' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 107
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 412 AND 422 ORDER BY pdf_page,id', (DOC,))]
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
    pending.append({'id': 'upper-l055-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})


quote_overrides['420-b000']=passages[pid('420-b000')]['text'][passages[pid('420-b000')]['text'].index('至于减磅这种活动'):]
c(55,'buy-before-mature-sell-climax-timing-metaphor-not-physiology','412-b003','作者用买之前戏、卖之高潮说明时机：过早买入易反复折腾，高潮后不能及时退出会受困，要在初起取其精华、后继乏力时退出。','操作节奏|操作策略|买卖点',2,'成人性别/生理同构只是作者交易修辞，不作生理学或性别能力事实，也未在此给前戏/高潮的独立量化识别算法。')
c(55,'cash-chip-exchange-asymmetric-time-irreversible-nominal-money','412-b004','作者将买的钱换筹码与卖的筹码换钱视为非同构：名义钱额保持、筹码价值随时间变，时间不可逆，故买卖策略不对等。','交易时间不可逆|交易条件|成本|操作策略',1,'原钱与时间无关限其名义计价模型，不推广为购买力/利息/汇率/货币风险恒定；非同构是其操作逻辑说明，不是项目另证金融数学定理。',ambiguity='nominal_cash_assumption_not_constant_real_value_or_risk')
c(55,'large-building-repeated-buy-sell-adjust-cost-and-quantity','412-b005','大级建仓过程反复、买中有卖，根据当下走势调成本与数量，利用底区中枢延伸/扩展取得足够且成本降低的筹码；不必然等于坐庄。','动态建仓|中枢延伸|中枢扩展|成本|仓位',1,'够量、降低成本为作者过程目标不当已证所有资金可无限反复成功；股性改造与退出底线为其资金视角，未给交易合法性或可成交保证。')
c(55,'bottom-area-can-be-shallow-channel-not-horizontal-only','412-b005','作者说底部不一定在平衡水平线上震荡，也可为斜率很小、震荡激烈的复杂通道式上升。','通道式上涨|中枢震荡|动态建仓|股性',1,'一般小斜率非固定角度阈值；本条为底区结构，不把54联通通道或布林轨道参数硬套，本课明言具体以后再说。')
c(55,'good-base-entry-cost-below-area-rise-cost-only-decreases-author-ideal','412-b006','作者对好的大级建仓设想为离开底区时成本已在区间之下，并称大级中枢上移中只会减成本，增加成本的拉抬愚蠢。','动态建仓|中枢上移|成本|操作策略',1,'这是作者理想操作/评价，不说所有上涨自动令成本下降、原始买价变零或无须承担成交/持仓风险；只会的强语未被实绩检验。',ambiguity='author_ideal_cost_path_not_automatic_market_or_execution_guarantee')
c(55,'first-rise-after-base-not-final-adjustment-may-be-short-violent','412-b006','对刚脱离底部的股票，作者用多次高潮比喻后续上升，称首次后的不应期往往不长却可很猛烈、震荡激烈并仍有继续上冲力。','中枢上移|调整|股性|操作节奏',2,'次数为修辞举例不是所有股票须涨十次或固定轮数，往往不等必然，性比喻非生理/生物学研究结论。')
c(55,'exit-large-level-exhaustion-divergence-not-first-small-shock','412-b006 413-b000','作者把出色的卖定位于大级最后高潮后继乏力、背驰中退出，大资金理想状态是在最后疯狂中完成退出。','背驰|操作级别|卖点|交易容量',1,'限定大级退出语境，不等所有资金只认一个卖点或实际大额货必能高价卖完；后筑平台出货贬语是作者评价，不立违法/财富事实。')
c(55,'retail-daily-or-above-can-wait-second-or-third-buy','413-b001','一般散户做日线以上介入不必都在一买，可等二买，或更干脆等三买，因其后准备阶段未必能忍受。','第一类买点|第二类买点|第三类买点|散户|操作级别',1,'不是取消一买或所有级别强制等三买；等待建立在所选日线以上级别和个体承受力，三买后并非免一切回撤。',conditions=['一般散户且日线以上介入','按承受准备阶段震荡的能力选择一/二/三买'])
c(55,'scale-or-training-start-at-least-second-use-oscillation-learn-stock','413-b001','若资金规模需较多筹码或要积累大资金操作经验，作者要求至少从二买起利用部分准备阶段介入，以震荡降低成本、增筹并熟悉股性。','第二类买点|交易容量|中枢震荡|股性|动态建仓',1,'资金量/筹码需求或训练目的不能省；不把散户可等三买与大规模需提前建仓合成人人一套，也不宣称震荡降本实际无失败。',conditions=['资金规模需要一定数量筹码，或为以后大规模操作储备经验','至少二买开始利用部分前期震荡，目标为降本/增筹/熟悉股性'])
c(55,'stock-character-frequency-amplitude-complexity-with-common-center-patterns','413-b002','作者将股票运行归为不同级别中枢震荡和移动组合；相同基本模式下，各股在频率、幅度、形态复杂度等方面有各自股性，呈现不同图形。','股性|中枢震荡|操作级别|幅度|走势分解',1,'同构论为作者框架，未等同所有个股同点同步，股性尚无本课量化度量或恒定不变承诺。')
c(55,'may28-gap-balance-next-three-day-pressure-not-universal-gap-law','413-b003','5月28日作者判开盘大缺口后不强、仍平衡市，缺口及新中枢吸引力令其后三天压力不可忽视，恰与周四月收盘重合。','平衡市|缺口|走势中枢|确认|市场震荡',1,'特定日预测，三天考验非任意缺口严格充分确认法，也不是50/53破5日线三天规则；图6/4后K不证原预判。',figs=[(417,1)])
c(55,'half-line-june-4144-daily-not-week-month-at-least-three-months','413-b004','作者说4129的1/2线6月上移4144，日线回试确认不保证周/月确认；最严格月线需至少3个月，理想5月光头阳、6月下影确认、7月长阳终确认，但市场未必走出。','1429点历史压力线|确认|操作级别|走势预测|K线',1,'保至少、理想而未必；不是五月已经完全确认或所有突破3个月有效。图头5/30实际含7月，1249图标与原模型1429不改，不能用未来行情作当时保证。',conditions=['作者2007年此1/2历史模型','日/周/月回试分层，至少3个月是最严格月线确认口径'],figs=[(420,1)])
c(55,'association-A-still-center-B-complete-subtype-retest-complete-third','414-b005','作者以中枢C=A+B说明结合律检查：A仍须满足该级别中枢定义，B是完成次级走势，再看回试段是否次级完成以确认三类点。','结合律|走势中枢|次级别|完成|第三类买卖点',1,'原问题问新枢从三类点腿还是加1腿计，作者回答以定义和完成检查，不静补统一+1索引；离开B及回试均完整次级，不只含一个次级中枢。',conditions=['A依然符合该级中枢定义','B及随后回试均需次级完整走势，结合律分解必须合法'])
c(55,'two-decomposition-MACD-comparisons-author-approval-d4-both-divergence','414-b010','作者认可读者两分解的力度比较：首式g3d4与g2d3、次式g3d4与g1d2；两种都得到d4为背驰点，故该点意义更大。','分解多样性|MACD|指标对比|背驰',1,'细段来自紧前读者414-b009并被作者对的明确认可；作者原引只保完整原答，不把读者公式改作者长引。作者背驰一词按该盘背比较语境，非自动提升成1分趋势背驰。',conditions=['对应volume_1-a53e99c37ca5-p0414-b009两分解比较的作者明确认可','本例两比较均成立，其他情况未必一致'],ambiguity='author_approval_of_adjacent_reader_comparison_not_author_long_quote')
c(55,'decomposition-strength-disagreement-only-valid-minimum-return-not-both','414-b010','作者说两分解可能不一致：后段力度居前两段之间时，回拉可能只满足成立分解的最低幅度，不必达到另一不成立分解的最低幅度。','分解多样性|盘整背驰|幅度|指标对比',1,'可能/不一定均保；不能因两解合法就声称全部回抽目标同时保证。本段未给完整等号/面积/时序算法，具体留后课。')
c(55,'rebuy-only-when-technically-allowed-do-not-chase-after-missed','414-b013','作者建议卖出后在技术允许时买回以免节奏乱；若未回补，不要等再冲高才追高回补，易被套。','操作节奏|操作策略|追高|买点',1,'技术允许是必要限定，不改任何已卖出都无条件立刻买回，尤其不能覆盖明确三卖后的退出或新买点未形成。')
c(55,'capital-channel-time-decide-own-style-level-not-small-fund-total-ban','415-b001','作者认可须按实际情况选操作风格与级别，资金量、通道、操作时间等都是决定因素。','交易容量|交易通道|操作级别|操作策略',1,'紧前读者说小资金不要盘整，作者对的随后给个体条件，不立一切小资金任何中枢震荡都禁做；与53技艺且通道、54快破门槛并存。')
c(55,'hypothetical-rule-change-cloud-not-rain-raise-operation-level','416-b004','作者说黑云不一定有暴雨，即使在其批评的交易条件下理论仍有效，但操作级别须大幅提高。','交易规则|交易条件|操作级别|理论成立前提',2,'指2007年作者讨论的草案若实行场景，不认证其为已生效或当前法律，也不提供规避监管步骤；理论仍有效为作者主张未证全部交易规则变化都无影响。',ambiguity='historical_hypothetical_rule_conditions_not_current_law_or_proof')
c(55,'profits-for-family-gradual-principal-consumption-withdrawal','416-b005 417-b006','在已有盈利的历史情境，作者建议先安排自己和家人生活，逐步提取本金及该消费的钱，再用股市所得继续操作。','资金管理|本金提取|成本|市场风险',2,'无所顾忌/更安全是作者账面本金与生活资金隔离的说法，不证剩余盈利筹码免价格/流动性风险；不当用户当前个性化资产配置建议。',ambiguity='principal_withdrawal_reduces_exposed_original_capital_not_all_market_risk')
c(55,'may29-balance-first-three-thirty-bars-4323-support-4300-center','416-b006','5月29日作者判前三根30K高低点均破的平衡市、全天在昨日中枢上方；次日4323若不有效跌破则超强，跌破则形成约4300中线的新中枢后待三类点。','平衡市|每日走势分类|确认|走势中枢|价格区间',1,'两分支为历史条件判读；日内前三30K辅助中枢不直接等递归30分中枢，4323/4300非通用阈值，6/4后加图不证明原预测。',figs=[(417,1)])
c(55,'withdraw-principal-not-clear-all-cash-safety-first','418-b002','作者澄清前文让拿走本金及消费款，并非要求清仓；已清也无所谓，震荡会有机会再买，但资金须安全、无其他顾忌。','资金管理|本金提取|操作策略|市场风险',1,'不将非清仓误改永不空仓/永远持股，原再拿回机会不是无需买点或任何价格买入；读者实际清仓是自述未外核。')
c(55,'may29-fix-level-small-top-three-wave-retest-rebuy-skilled-only','418-b005','作者要求先定级别，5月29日早顶在1分图是很小级别，后三波下杀未破昨日中枢、可视回抽确认回补高抛筹码；这是很短操作，不熟者看5日线。','操作级别|走势中枢|确认|操作熟练程度|均线系统',1,'1分观察图不等信号必是1分级，三波不等三根K；回补限所述中枢未破/技能条件，不以读者买后像头部问句证明三买必已成立。')
c(55,'daily-divergence-clear-vs-thirty-divergence-center-oscillation','418-b009','对读者永不空仓解读，作者说清仓条件是日线出现背弛，当时最多一些30分背弛，可用中枢震荡等处理。','背驰|操作级别|中枢震荡|操作策略',1,'清仓vs处理分别限定该较大级持仓语境，不禁止短线独立仓位按小级卖出；背弛为原字，概念导航规范为背驰，读者再不空仓并未获无条件认可。')
c(55,'macro-bull-change-only-economic-retreat-author-historical-view','419-b001','作者在2007年5月30日称只有经济倒退才能改变大牛市性质，其他事只是不同级别震荡的诱因。','宏观市场判断|市场震荡|操作级别|走势预测',3,'历史作者强判断而非本项目验证的经济定律/当前市场判断；不以价格图证明唯一宏观原因，也不保证任意政策冲击都不会造成长期损失。',ambiguity='author_historical_macro_only_cause_claim_not_verified_economic_law')
c(55,'unexpected-events-position-cost-control-zero-cost-tool-author','419-b001','作者认为突发事件不可避免，故仓位和成本控制重要，称良好操作习惯足以应付任何事件、零成本筹码是最好工具。','仓位|成本|零成本持仓|市场风险|操作策略',1,'任何/最好为作者模型性强语，成本0不是当前市值0或无机会成本/流动性/成交风险；不把已收回本金与所有风险消失混合，未证实盘应付一切事件。',ambiguity='author_zero_cost_any_event_claim_not_all_risk_elimination')
c(55,'calm-unexpected-event-long-run-habits-not-one-outcome-victory','419-b002','作者强调从容面对突发事件、长期坚持正确操作习惯，卖出不是胜利、没走也非末日，不按单次走没走评价。','操作熟练程度|操作策略|市场心理|市场风险',2,'其1996年及1987年后来走势为作者历史回看例，未独立外核；不能用长线回看代替当下仓位风险和实际卖点执行。')
c(55,'may30-month-shape-half-line-at-least-three-months-three-scenarios-open','419-b003','5月30日作者说月线若留长上阴则6月调整压力大，1/2线还需考验并至少影响3个月，三模式尚未最后确认，应看图操作。','1429点历史压力线|K线|确认|走势预测',1,'已看PDF419确为长上阴原字，未静补长上影；至少影响3个月不同于413月线至少3个月确认，三个模式未定不是已确认大顶或强突破。政策动机/能力评价非已核事实。')
c(55,'low-held-profit-zero-cost-can-use-second-third-exit-author-claim','419-b004','作者对从低位守均线、有足够利润尤其零成本的重仓，说按正常操作即使未走一卖也可走二、三卖，仍强调选级别买卖点和成本为0的安全观。','第一类卖点|第二类卖点|第三类卖点|零成本持仓|市场风险',1,'原无论什么情况/真正安全保作者强语身份；未证涨跌停、T+1、通道/容量下每点可成交，也不将近期追高的新仓等同低位盈利旧仓。',ambiguity='author_always_exit_and_true_safety_claim_execution_not_proven')
c(55,'increased-costs-minimum-five-even-thirty-plus-level','419-b005','因交易成本上升，作者要求操作级别大幅提高，最低至少5分甚至30分以上，买点买/卖点卖原则不变，有相应级别买点再介入。','交易成本|操作级别|买卖点|交易条件',1,'这是5/30历史成本场景的操作建议，不是理论最小级别、所有成本参数固定适用或当前税率事实；未量化两级之间资金/误差阈值。')
c(55,'unexpected-event-may-confirm-existing-thirty-top-leg-then-current-points','419-b005','作者说原已形成30分顶背驰段的区间套确认极可能被突发事件粗暴确认，应以此为起点参照随后当下走势逐步确认买卖点。','背驰段|区间套|确认|操作级别|当下',1,'极可能不是5/29尾盘当时已完成确认；不能把进入背驰段静改当时已经构成可成交一卖，细部56课尚待完整审读。')
c(55,'reduce-on-sell-rebuy-at-appropriate-buy-not-fixed-portfolio-proof','420-b000','作者说只要有卖点都会参与减磅，差别在数量，并在适当买点重新买入。','卖点|买点|仓位|操作节奏',2,'仅截技术部分，前文指引/消息/70%老股5%新股25%现金和应急保证金为自述非已核资产或本策略固定比例，不以该自述指导用户配置。')
c(55,'may30-miss-first-second-sell-0947-author-not-guaranteed-fill','420-b002','5月30日作者说突发事件可错过一卖而二卖不会错过，并指05300947为二卖，强调二、三类点在此情境的实用性。','第一类卖点|第二类卖点|第三类卖点|交易条件',1,'原09:47与下一课PDF422-b006作者9点48分别保留未统一；不会错过是作者可识别/可操作强语，不等所有资产T+1/跌停/容量下保证成交。本课所配日线图不能定位一分钟时点。',ambiguity='source_0947_vs_next_0948_and_execution_guarantee_unresolved')
c(55,'thirty-top-pressure-at-least-one-bottom-for-strong-rebound-higher-buy-points','420-b003 421-b000','作者说30分顶背驰压力后，较有力度反弹至少需1分底背驰，并参考5分、30分；真正底部构筑须这些级别重新走出买点。','背驰|操作级别|反弹|买点|完成',1,'至少1分不是任意更低反抽即确认大底，反弹力度与完整底部不同；本段原怎么都需要为作者该局模型判断，不用其替代所有小转大/形成中例外核查。')
c(55,'may30-adjustment-from-feb6-2541-half-line-shenzhen-13700','421-b001','作者将当时调整归于2月6日2541起约1800点上涨，强调180月窗及1/2线压力；称深圳13700对应线未突破，上海线走势更有指导性。','1429点历史压力线|走势预测|宏观市场判断|价格区间',2,'历史模型/作者解释，未外核深圳原图或1800精确差价；图正文1429与图1249标识差保留，含7月后K不能证明当时解释或强设当前价格。',figs=[(420,1)])
c(55,'thirty-top-return-may8-21-thirty-center-for-future-oscillation','421-b002','从中枢角度，作者要求30分顶背驰重新拉回5月8日至21日构成的30分中枢，今后可继续参照它考察中枢并按震荡看。','背驰|走势中枢|中枢震荡|操作级别',1,'保正文5/8至5/21，图框从5/9显示不静改文字起点；6/4后加K不当5/30当时预测实证，模型回拉也非所有路径当日立即完成。',figs=[(421,1)])
c(55,'skilled-short-rebuy-second-sale-stocks-then-center-oscillation','421-b003','短线有能力者，作者允许参考短线指标回补二卖卖出的股票，再做中枢震荡。','操作熟练程度|第二类卖点|中枢震荡|指标对比|操作策略',1,'限定有能力、短线，指标辅助需级别/结构，不给未完成买点或任何下跌都回补的指令；与技术允许回补、低技能看5日线并存。')
c(55,'after-market-stable-midyear-results-daily-third-buy-candidates','421-b003 422-b000','作者预计大盘稳定后个股机会多，中报业绩好相关股逐步走强，技术上关注大跌中形成日线三买的个股；后答复重申关注三买。','第三类买点|基本面|操作级别|操作策略',2,'稳定前提/前段日线限定保留；后短答省略日线不抹前文级别，也不认证个股真实业绩、必涨或读者所有三买自判。')
c(55,'five-third-buy-cannot-offset-thirty-top-daily-author-conditional-answer','422-b003','对读者三买后跌停，作者说5分三买斗不过30分顶背驰、日线的则没问题，并要求若未在二卖走仍须学习磨练。','第三类买点|背驰|第二类卖点|操作级别|市场风险',1,'先核买点级别，日线没问题和跌停不是问题为作者模型强语，不等日线三买免日内下跌/保证卖出；未独立验证读者三买实际成立或其账户有可成交二卖，下一课个股/指数差别待核。',conditions=['作者针对读者422-b002三买后跌停的级别对比回复','5分三买vs30分顶背驰；日线原答不能泛化为所有风险消失'],ambiguity='author_daily_okay_claim_not_immunity_to_drawdown_or_execution_limits')
c(55,'may30-three-of-three-script-longer-than-prior-1500-author-case','420-b001','作者称3之3剧本已走出，因为该段已比上一段1500点长，符合最严格理论条件；更长与否并不重要，仍须等买点。','走势预测|宏观市场判断|走势分解|买点',3,'只录作者本例判断，未给完整起止点/波浪规则，不立任意涨过1500即3之3；后巨额回报锁定/零成本资产为自述，未验账户，也不证牛市永不变。',ambiguity='historical_wave_script_and_return_self_report_not_independently_verified')
note('412-b001 412-b002','anthropomorphic-sex-analogy-context','作者以人的行为同构、男女和股票人格化作交易时序比喻。','不抽取为性别/生理能力、心理学或生物学事实，也不把修辞当量化市场证明。技术买卖时序另录。')
note('413-b005 414-b001','historical-policy-draft-and-nondisclosed-message-context','作者批评操纵指引草案与未明说调控信息，认为影响月线和市场格局。','仅固定2007作者观点/自述，不认证当时或当前法规效力/内幕先知，未给政策实施或人物动机的外部证据。')
keep('413-b006 414-b000 416-b007 417-b000','upper-l054-c-stage-market-script-depends-on-joint-forces-not-one-person','政策也是合力一部分、剧本需多方配合，继续保既有54合力来源边界；只台账关联，不改旧命题或证据。')
note('415-b003 415-b004 415-b005 415-b006 415-b007 415-b008 415-b009 415-b010 415-b011 416-b000 416-b001 416-b002 416-b003','historical-legal-draft-critique-and-biographic-context','作者两条草案摘引、撤单例、2001亿安事件/市场迟钝和个人去留财富/权力寻租评价完整已读。','条文是作者文章中的历史引述非当前法律；不验证撤单次数即违法/9亿处罚/因果或个人财富，不将作者攻击/性比喻转法律、生理或公司事实；不提供规避规则执行步骤。')
note('417-b001 417-b002','historical-conditional-exit-and-public-advocacy-context','作者解释只在草案成真才不玩、当时未成真并号召共同改变，称牛市不会因此改变。','不将条件去留静改已经逃跑或真实内幕、当前行情/法律结论；原号召为研究文本不是本项目操作指令。')
note('418-b011 418-b012 419-b000','historical-tax-news-recollection-and-author-position-context','作者回述5月时间窗/先前警示/提本金，对印花税凌晨公布及政策程序作历史评价，并称绝不会说事先知道准确时间。','不把不会说知道改为已承认准确知情或已证不知道；不外核公告时间/当年制度/机关动机/历史首例，也不当当前税制信息，操作条件另抽。')
note('419-b006 420-b000','historical-portfolio-allocation-and-motive-self-report','作者自述除协调应急保证金外约70%零成本老股、5%新股、25%现金，减磅有技术/指引/消息原因。','不是账户核验、固定资金配置模板或精确分母总额；仅420尾卖点减磅/买点回补技术引文抽出，不解析隐秘消息作事实。')
note('420-b001','historical-profit-and-bull-script-self-report','作者3之3/前1500长度判断外，还有牛市不变、回报锁定/零成本/能量储备的自述。','不认证收益已锁定不可损或真实组合；长度条件只是本例，买点等待仍保，观点与数据事实分开。')
note('421-b004','source-separator','解盘与答疑间原星号分隔。','非技术命题，原字符保留。')
note('421-b008','historical-group-rhetoric-and-skilled-adjustment-context','作者号召震荡中统一思想，并说技术好的可趁调整降本，后承接422个股技术答复。','群体号召不成技术事实或当前操作指令，技能条件不省；后个股机会与三买条件单列。')
issue('timing-metaphor-nominal-cash-and-stock-character-not-science-proof','412-b001 412-b002 412-b003 412-b004 413-b002','买卖钱筹码非同构基于名义计价/时间不可逆；性比喻和股性频幅复杂度为作者框架，非生理/性别/心理或金融独立证明。','保源文和比喻身份，名义金额不等实际购买力恒定，股性无本课量化参数；不把修辞转换可执行精确算法。',True)
issue('building-cost-ideal-and-retail-vs-scale-entry','412-b005 412-b006 413-b000 413-b001','大级建仓反复/成本下底区与中枢上移只降本为理想操作主张；散户可二三买与规模/训练至少二买各有前提。','不把资金量和股性改造目标变无风险收益/操纵合法性证明；首轮调整可猛、后轮数仅比喻，不生固定股票生命周期。',True)
issue('A-center-B-complete-subtype-two-comparisons-minimum-returns','414-b004 414-b005 414-b008 414-b009 414-b010','C=A+B中A仍是原级中枢，B及回试需完整次级；两解比较作者对的认可本例d4，但不一致时只可能满足成立解最低幅度。','引用只作者答，读者两公式/细比较保reader上下文；不补统一+1起算或两解全部回抽目标同时保证，等号/面积/实时完成细则待核。',True)
issue('style-skill-technical-rebuy-principal-withdrawal-not-clearance','414-b013 415-b000 415-b001 416-b005 417-b006 418-b002 418-b005 418-b009','资金通道时间定风格/级别，技术允许才回补；提本金消费款非清仓更非永不空仓，日线与30分持仓处理分级。','不把对的认可读者小资观点扩大成所有小资金禁震荡；保短线技能/中枢未破，取本金仍不免盈利筹码市场风险。',True)
issue('absolute-zero-cost-safety-second-sell-and-daily-third-execution','419-b001 419-b004 419-b005 420-b002 420-b003 421-b000 422-b002 422-b003','零成本才真安全/可应付任何事件、二卖不会错过、日线三买没问题是作者强语；5分3买vs30分顶背驰级别必须保。','不能声称T+1/跌停/通道/容量下保证每人成交或日线免回撤，低位盈利旧仓非追高新仓，指数与个股不同下一课再核，成本升对应提高级别。',True)
issue('source-0947-vs-next-0948-three-later-figures-and-date-fields','413-b003 413-b004 416-b006 420-b002 421-b001 421-b002','原05300947与56开头PDF422-b006的9点48不同；三图均后加，30分含6/4、日线选5/30却含7月，图1249/原模型1429及框5/9/文5/8不改。','只21时间空格/3图元数据修订，不用未来K认证预测/一分钟成交，正文/图/跨课时点分别返回；56未完整读不冒全核。',True)
issue('historical-half-line-month-confirmation-vs-influence-and-gap-days','413-b003 413-b004 416-b006 419-b003 421-b001 421-b002','日线确认不保周/月，最严格月至少3月确认与至少影响3月不同；4129六月4144/深13700和4323/4300历史值，缺口三天不同于5日线三天。','5-7月理想路径作者明确未必，三模式尚未最终确认；原长上阴已回看原页不静补影，不把后加图当证原1/2线或现在市场。',True)
issue('historical-policy-macro-portfolio-and-wave-script-claims','413-b005 415-b003 415-b004 415-b006 415-b009 416-b001 416-b002 417-b001 418-b011 418-b012 419-b000 419-b001 419-b006 420-b001','草案/印花税历史引述、个人财富和70/5/25仓位、宏观只有经济倒退改变牛市与3之3/1500是作者当时观点自述。','不认证法律效力/机关动机/内幕准确时点、真实绩效或经济唯一因果；保所有语境但不据此给当前投资或撤单规避建议。')
relations={
 'cash-chip-exchange-asymmetric-time-irreversible-nominal-money':[('操作策略','交易时间不可逆','qualifies')],
 'large-building-repeated-buy-sell-adjust-cost-and-quantity':[('动态建仓','成本','qualifies')],
 'bottom-area-can-be-shallow-channel-not-horizontal-only':[('动态建仓','通道式上涨','qualifies')],
 'stock-character-frequency-amplitude-complexity-with-common-center-patterns':[('股性','幅度','qualifies')],
 'scale-or-training-start-at-least-second-use-oscillation-learn-stock':[('第二类买点','交易容量','qualifies')],
 'association-A-still-center-B-complete-subtype-retest-complete-third':[('第三类买卖点','完成','requires')],
 'decomposition-strength-disagreement-only-valid-minimum-return-not-both':[('分解多样性','幅度','qualifies')],
 'rebuy-only-when-technically-allowed-do-not-chase-after-missed':[('操作节奏','买点','requires')],
 'capital-channel-time-decide-own-style-level-not-small-fund-total-ban':[('操作级别','交易通道','qualifies')],
 'profits-for-family-gradual-principal-consumption-withdrawal':[('本金提取','资金管理','qualifies')],
 'withdraw-principal-not-clear-all-cash-safety-first':[('本金提取','操作策略','qualifies')],
 'daily-divergence-clear-vs-thirty-divergence-center-oscillation':[('操作级别','背驰','qualifies')],
 'increased-costs-minimum-five-even-thirty-plus-level':[('操作级别','交易成本','qualifies')],
 'unexpected-event-may-confirm-existing-thirty-top-leg-then-current-points':[('背驰段','确认','requires')],
 'five-third-buy-cannot-offset-thirty-top-daily-author-conditional-answer':[('第三类买点','操作级别','qualifies')],
}
for r in rows:r['relations']=[dict(source=a,target=b,type=t) for a,b,t in relations.get(r['id'].split('upper-l055-c-stage-')[1],[])]


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
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], '读者两套MACD比较有作者明确对的认可，细式仍reader；小资禁震荡/永不空仓/三买跌停和账户收益疑问不自动全认可，关键技术/资金/级别条件以作者实际答为准。'
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
        'note': '买卖时序与名义现金模型/成人修辞分开；资金通道时间定级别，A中枢仍成立且离返完整次级，双解比较认可不等所有回拉目标均保；技术允许才回补、提本金非清仓非永不空仓，日/30/5级别不同，0成本和二卖/日线没问题为作者强语非实际免风险；09:47/下课9点48、长上阴原字及3未来图保留。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=f['note'],
             figure_source_review='实际查看412至422十一页及3整图和419原字整页：417/421两上证30分均含6/4，420日线选5/30但右端至7月，均后加；不把日线图当09:47定位图。图1249/原模型1429及框5/9/文5/8差保，后K不证早先预测/实际成交。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 107 and Counter(x['lesson_number'] for x in ledger) == {55: 107}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [55], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(412, 423)), 'figure_objects_viewed': 3, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '55课107段11页3整图同模型四轮；21时间空格/3后加图；买卖非同构名义模型与股性/资金级别、完成次级/两解力度回拉、技术允许回补/本金非清仓、级别和0成本强语及09:47/9点48分别保，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


