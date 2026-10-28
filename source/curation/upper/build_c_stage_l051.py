"""Materialize the main agent's four-pass reading of lesson51.

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
BASE = 'c_stage_l051'
REVIEWER = 'Codex 主代理 / 阶段C上册51课同模型四轮复核'
SOURCE_SHA = 'f7fbd9917fcc5f46cd16750797a54e06944ee6663c6ecb800bc7954bc9a82420'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-051' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 129
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 371 AND 382 ORDER BY pdf_page,id', (DOC,))]
assert len(figures) == 4
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
    pending.append({'id': 'upper-l051-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})




















c(51,'recommendation-self-reinforcing-flow-hypothetical-numbers','371-b007','作者假设10万量级受众中5%即5000人、各买2000股形成1000万股买盘，可能支撑涨价；其余人看到推荐准、后来追入与盈利者传播又增加资金，直到流入和筹码松动平衡。','短线荐股|市场心理|流动性|资金食物链',1,'原文不妨假设模型，非真实调查、普遍成交/价格冲击保证或荐股准确率；超10万与5000为示例量级，不以5%×实际未知浏览数算确定买量，单位为股非1000万元。',ambiguity='explicit_author_hypothetical_flow_model_not_market_measurement')
c(51,'tiered-members-early-buy-control-flow-stability-risk','371-b008','作者描述分层会员提前买、再向外推荐以控制购买流量的系统，认为可持续更久并类似多层组织庄家，但困难时容易瓦解。','短线荐股|资金食物链|市场心理|流动性',2,'描述作者批评的假设结构，不实施组织/买卖；分散账户避某类监管风险只是作者历史比较，不证明合法或没有其他监管风险，也不等所有付费会员服务均操纵。',ambiguity='author_hypothetical_tiered_flow_not_verified_legal_classification')
c(51,'short-switching-exhausts-outsiders-longer-organization-evolves-author','371-b009','作者认为特别短线频换的荐股组织，外围套牢后资源会耗尽而崩溃；较长线精细组织会逐步演化成更稳定的私募结构。','短线荐股|资金食物链|基金|市场风险',2,'作者群体资金生命模型，不认定任何具体私募由传销演变或所有散户/推荐者必属犯罪；必然套最多为作者推理未给样本。',ambiguity='author_organizational_evolution_view_not_all_private_funds_origin')
c(51,'funds-redemption-risk-tolerance-and-plural-capital-ecology','372-b000 372-b001','作者把基金向对冲或合伙结构演化与赎回、风险忍受回旋余地联系，并认为多种资金生存方式会并存，不会一统天下。','资金食物链|基金|基金赎回|市场风险',2,'作者关于资本组织的解释，不逐一验证制度/生存期/某基金表现，猎鲸自述不当已验证控盘能力或攻击目标名单。')
c(51,'audience-growth-recommendation-can-be-used-as-flow','372-b002','作者称停止说具体股票与受众增多有关：再说可能成为或被利用成其批评的荐股资金循环。','短线荐股|市场心理|资金食物链',2,'停止时间/14股/600635与000802价格为作者自述未外核，不认证本人永不受该机制影响或证明其他推荐必操纵。')
c(51,'buy-by-level-point-not-author-target-or-chase','372-b003','作者说关键是有什么级别买卖点、不是对象，不让现在追高，也不希望所有人集中其提过股票；若恰有买点可按同法参与。','买卖点|操作级别|追高|操作策略|短线荐股',1,'负责到底为作者自述不等损失兜底；有级别买点条件不可删，未鼓励跟单/集体抬价或将原列股票当当前建议。')
c(51,'may9-gap-not-completely-filled-five-day-skill-fallback','373-b001','5月9日作者称缺口未全补问题不大，并提醒技术不足者按前述5日线不破的简法。','缺口|均线系统|操作熟练程度|市场震荡',2,'历史判断和前日呼应，不认证未补缺口必安全或不再补，前期45趋势非盘整限制仍要联合；后5/11图不验5/9预测。',figs=[(373,1)])
c(51,'4000-valid-break-center-then-third-buy-failure-third-sell-possible','373-b002','作者认为4000突破不能立即确认，要先形成有效且有些级别中枢、再有三买才确认；也可能失败向下成三卖，故不预猜唯一方向。','第三类买点|第三类卖点|走势中枢|突破|确认',1,'有点级别未量化具体分钟数，4000是案例参照非所有突破通用点位；不是任意价站上一K就突破有效或不存在下行风险。')
c(51,'may10-oscillation-above-center-not-only-green-fall','373-b004 374-b000','5月10日作者说震荡不等绿盘大跌，中枢上方也可震荡；将尾盘下行归小级背驰与走势必完美的技术说明。','中枢震荡|背驰|走势终完美|操作级别',1,'跨页独立5/10时标已核，保证为作者案例理论语，不因一天红盘排除震荡；中枢的走势必完美保原对象措辞，未当项目已证任意时刻必下跌。',figs=[(373,1)],ambiguity='author_case_technical_guarantee_not_verified_prediction')
c(51,'may10-day-center-three-next-day-strength-branches','374-b001','5月10日作者说三买前中枢未完结仍震荡；用分时中枢看两日平衡且当天位置上移，次日可继续上移、围绕当天震荡或回试前日而促一般中枢扩展。','每天走势上的中枢|每日走势分类|中枢震荡|中枢扩展|第三类买点',1,'分时借用与一般中枢层次分开，不把当日位置上移自动当严格同级上涨趋势；三分支为当时观察，次日开盘判断不等任意未来路径已知。')
c(51,'short-activity-use-best-known-method-not-all-switching','374-b002','作者强调这些是很短线活动，应量力用最精通、最可控的方法，能力不足看5日线，换股需学工夫。','操作级别|操作熟练程度|均线系统|操作策略',1,'不将均线简法当全结构永久法；原新帖15分钟安排只作历史背景，不执行定时发帖。')
c(51,'MACD-first-up-zero-then-sideways-second-buy-auxiliary','374-b006','对联通割肉后上涨的自述，作者要求补习MACD黄白第一次上0轴、再横0轴上形成二买的判断。','MACD|第二类买点|指标对比|确认',1,'原答没有明确周期、日期/买卖价或把这两指标动作单独定义为所有二买；联查结构定义与50先中枢选段，不独立认可读者割肉价。')
c(51,'large-stock-oscillation-large-fund-retail-larger-second-third-buy','374-b012','作者建议学中枢震荡避免换股两头落空，联通虽慢大资金可赚震荡；一般散户没必要参与这类股，通常较大二三买才值得考虑。','中枢震荡|交易容量|第二类买点|第三类买点|操作熟练程度',1,'作者该类股票/资金取舍，不证明大盘股必慢、所有震荡都赚或较大二三买保证涨停；不把比较大具体化任意分钟数。')
c(51,'B-needs-third-buy-otherwise-oscillation-consolidation-divergence','375-b002','对a+A+b+B+c，作者说B须出现三买才算结束；否则仍围绕B震荡，用盘整背驰即可。','第三类买点|中枢震荡|盘整背驰|趋势|走势中枢',1,'只明确B，未逐项认可读者A/B全套条件或MACD符合即趋势背驰；已形成中枢不等已结束，三买还需次级完整回试条件。')
c(51,'C2-incomplete-no-high-no-confirmed-third-buy','375-b005','作者对C1/C2提问说，若未出现所需完整走势则三买根本未出、仍震荡；不创新高仍在C2内、C2未完，不能先断定不会跌回原中枢，所谈走势类型均须完成。','第三类买点|走势类型|完成|中枢震荡|确认',1,'限该问C2回拉/新高确认语境，不推广所有走势不创新高均未完成；读者两个次级中枢并非本答新定义，作者要求的是走势类型完成，未补完整实时算法。')
c(51,'ultrashort-afternoon-third-buy-after-morning-extension-example','375-b009','作者给超短线优选例：上午原枢延续，后来拉起、下午三买确认，再在14点后拉起；其他类型留后。','第三类买点|每日走势分类|操作级别|操作策略',2,'最好的为作者方法取舍非普遍获利排名；不是已认可读者午前公式/两枢自动筛选策略，也非每天14点固定买点或完整分类已给全。')
c(51,'1429-historical-pressure-model-start-and-first-two-tops','375-b011 375-b012 375-b013','作者以1992年5月1429为月线基点：1993年2月1558顶接近1429+15×9=1564压力值，2001年6月2245顶接近1429+109×7.5=2246.5。','1429点历史压力线|宏观市场判断|经验压力线',2,'作者历史拟合例，1558不等1564、2245不等2246.5，只说触及/接近非数值相等；原1429不以后图1249纠正，未独立行情/回测验证、也不与其他经验压力线合并同义。',figs=[(376,1)],ambiguity='author_historical_linear_fit_not_out_of_sample_validation')
c(51,'pressure-rates-360-per-year-fractions-author-basis','375-b014 376-b000 376-b001','作者以圆周360度为其压力线分析基础，取每年360点基准，相关速率按1/4、1/2、3/4等比例；前两顶对应180和90点每年。','1429点历史压力线|时间之窗|技术分析',2,'360度到360点/年是作者选模依据，未给物理/统计必然证明；不将角度等同股指单位或宣称最优唯一比例，历史两点拟合非泛化验证。',ambiguity='author_360_degree_to_price_time_model_not_dimensional_proof')
c(51,'jan-mar2007-quarter-line-pullback-2764-historical-reading','376-b002','作者将2007年1至3月整理视为突破1/4线后的强回调，3月线值1429+178×7.5=2764，并把227下跌解释为末次回抽确认，随后攻击1/2线。','1429点历史压力线|确认|反抽|走势预测',2,'历史解释/作者主张而非本项目验证227因果或当时提前知道后涨；后月K不得当原发时已得证据，不认证空头动机。',figs=[(376,1)])
c(51,'may-half-line-4129-and-180-month-window-author','376-b003','作者给2007年5月1/2线1429+180×15=4129；1429至1558为9个月、至2245为9年、至当月180个月，称重要时间之窗且必有事情。','1429点历史压力线|时间之窗|宏观市场判断',2,'180个月/9年为作者月口径，未以事件发生证明360周期因果；必有事情强语未定义事件集，4129是该月模型数值非任何将来恒定压力价。')
c(51,'half-line-effective-break-new-regime-otherwise-old-speed','376-b004 376-b005','作者把能否有效突破每年180点的1/2线视为新旧模式分水岭：未破延续旧速率恢复涨，真正有效破才称脱胎换骨牛市开始，并预期多空争夺。','1429点历史压力线|突破|确认|牛市阶段|宏观市场判断',2,'作者2007框架，未给有效突破完整量化阈值、确认时长或对所有牛市定义；所谓序幕尚未拉开不撤此前牛市假设而是此处模式层次差别。')
c(51,'half-line-three-scenarios-top-balance-or-strong-break','377-b000 377-b001 377-b002','围绕1/2线作者列三条：线前止步或线上多头陷阱成大顶；突破后围绕线强盘整再寻突破；强破远离后强回调确认再攻3/4线，当时该线1429+270×15=5479。','1429点历史压力线|多头陷阱|盘整|突破|确认|走势预测',2,'三分支不当统计概率或单一路径预测；原两式的15因子不能望文固定相同单位，3/4线按270点/年与15年理解是整理单位说明，不回写原文；当前5479仅该历史时点模型值。',figs=[(376,1)],ambiguity='author_three_path_model_not_probabilities_or_verified_targets')
c(51,'pressure-line-three-months-before-july-claim-market-chooses','377-b003','作者说不论三条哪条，突破回试确认至少需3个月、至少7月前该线主导；具体选择无须预测，市场各方合力并非上帝预定，当下呈现。','1429点历史压力线|时间之窗|市场合力|当下|走势预测',2,'至少3个月/至少7月前是作者当时强时间判断，未给样本或精确起算与边界；不当理论保证所有压力线都3个月、全部市场参与者可提前识别。',ambiguity='author_historical_duration_forecast_not_general_three_month_law')
c(51,'half-line-eventual-break-support-author-long-bull-premise','377-b004','作者称1/2线最终突破是迟早的，有效破后每年180点旧压力可转最坚实底部支持，基础越扎实越利行情。','1429点历史压力线|突破|确认|牛市阶段|走势预测',2,'超级牛市是作者历史前提和最终乐观断言，非项目验证未来必破或突破价永不失守；压力线随时间变化，不把4129冻结永久支持。')
c(51,'may11-weak-day-branch-expansion-4000-still-needs-third-buy','377-b006','5月11日作者说开盘确认昨日三种日内分支中最弱类，此处形成中枢扩张；4000要经中枢后三买才确认，未出仍为形成与震荡。','每天走势上的中枢|中枢扩张|第三类买点|确认',1,'这里三种指5/10次日强中弱日内情况，非5/10另文1/2线三条中期模式；扩张原字保留，不静统一后文扩展术语或宣称全模型已证明。')
c(51,'direction-by-buy-sell-level-long-bull-until-long-sell','377-b006','作者强调不固定多空、见买点买卖点卖，自称长线看多只因长线没卖点，若季度线有卖点则转空。','买卖点|操作级别|市场心理|走势预测',1,'季度线例及作者当时判点未外核，非所有人同一持仓期限或项目认定现在季度无卖点；不把长期乐观当无退出条件。')
c(51,'may12-three-patterns-not-preselected-first-by-god','378-b005','5月12日作者再提醒三种中期模式没有预定答案，不能认为这三个月一定选第一种，市场各方力量平衡给出选择。','1429点历史压力线|完全分类|市场合力|走势预测',1,'区分预列模式与未来具体路径，未认证三分支数学完备/互斥或任何震荡都必赚；文中同段收益强语另有边界。')
c(51,'oscillation-profit-vs-unilateral-author-skill-claim','378-b005 379-b005 382-b002','作者多次声称有技术时震荡利润可不低于甚至超过单边，并强调需要技能磨练，技术不足看均线。','中枢震荡|操作熟练程度|操作策略|利润率',2,'原文保证性比较为作者方法主张无统一风险/本金/时间/频率样本，不当本项目回测结果或实际收益保证；49利润率与总利润口径仍分开。',ambiguity='author_oscillation_profit_comparison_not_audited_performance')
c(51,'may14-4040-day-center-reference-retest-4000','379-b003','5月14日作者判震荡、深圳强些仍平衡；沪当日中枢约4040，次日站稳或围绕震荡无碍，否则再考验4000。','每天走势上的中枢|平衡市|价格区间|中枢震荡|走势预测',2,'原4040上下为当日参考而非严格区间精确边界/所有指数通用值；图含5/17不能证5/14预测，技术和心理/政策为历史条件。',figs=[(380,1)])
c(51,'may14-high-with-less-volume-psych-policy-confirmation-view','379-b004','作者认为4000有效站稳还需震荡消化心理政策因素，并以当日新高量缩解释利空当利好的游戏疲态。','成交量|确认|市场心理|政策风险|走势预测',2,'作者历史解释，不把新高量缩等同必顶，也不认证相邻政治指控/特定人动机或所有政策利空必利好。')
c(51,'oscillation-until-third-points-third-sell-wait-adequate-bottom','379-b005','三买卖前按中枢震荡上卖下买；三点出现改按相应趋势，例如三卖后观察、等够级别底背驰再说。','中枢震荡|第三类买卖点|第三类卖点|背驰|等待|操作级别',1,'够级别未量化，不等三卖后任意分笔底背驰便回补；三点破坏原震荡后应改策略，不因前文震荡收益强语忽略止回补条件。')
c(51,'may15-4040-1046-last-rebound-five-day-break-case','379-b009 379-b011','5月15日作者以前日4040、当日10:46最后反抽随后破5日线作例，强调选级别见买卖点操作、4000不会很快确认突破而要震荡。','价格区间|均线系统|操作级别|中枢震荡|卖点',2,'事后案例/作者不会也不允许强语，不证明操控市场或原10:46必同级三卖；不与5/16 10:17混同，后图不认证可成交价格。',figs=[(380,1)])
c(51,'may16-1017-weekly-gap-bottom-divergence-case','380-b008 380-b009','5月16日作者把10:17填周线缺口的底背驰作为震荡操作例，重申震荡持续到三买卖点，不熟者继续练。','背驰|缺口|中枢震荡|第三类买卖点|操作熟练程度',1,'原文未明确该底背驰级别，填周线缺口不等周线背驰，也不因所有补缺口都自动出买点；图后有5/17K不作当时已知。',figs=[(380,1)])
c(51,'market-formed-by-forces-manager-not-always-controls-theory-scope-claim','380-b010','作者认为走势由市场各方合力形成、管理层不一定能随时决定，反对预定论；同时主张所有走势均技术性、被其理论包含。','市场合力|走势预测|技术分析',1,'前半反预定与后半全包含为作者体系主张，不宣称项目已检验所有走势或从中推出任意管理部门决策无影响。',ambiguity='author_all_moves_technical_inclusion_not_exhaustive_verification')
c(51,'half-line-center-ultimate-level-form-still-forming','380-b010 382-b002','作者在5月16、17日反复说围绕1/2线大震荡的最终级别和形式仍在形成，当前只是种子的一部分，可继续延伸扩展。','1429点历史压力线|中枢延伸|中枢扩展|完成|当下',1,'形成中不是已完成完整高级中枢或最终级别已确定；不能用未来月线图预先补齐结构，延伸/扩展须按原定义逐项核。')
c(51,'may17-4040-key-extension-versus-expansion-conditional','382-b000 382-b001','5月17日作者说4040早受压、午受支持，站稳会形成中枢震荡级别扩展，否则仍在当前级别延伸，要求学清两定义。','中枢延伸|中枢扩展|价格区间|确认|操作级别',1,'该案站稳4040为分支判读，不将任何价格站稳当一般扩展充分定义，未给新完整三段/波动区间或等值确认；与377原扩张字不静合。')
c(51,'warning-against-paid-tips-author-opinion-not-legal-verdict','378-b007 378-b012 382-b003 382-b004 382-b005','作者告诫警惕向读者全部或部分收费的荐股，批评此类活动，主张有本事应从市场取得回报。','短线荐股|市场风险|市场心理',3,'作者强烈价值判断/历史广告批评，不证明所有收费服务都是诈骗/违法或免费推荐无利益冲突，不作现今法律认定、也不认证所指广告身份。',ambiguity='author_paid_tip_criticism_not_universal_legal_judgment')

note('371-b005 371-b006','historical-intro-rhetorical-context','赌博心理/推销群体及替庄出货者不持久的开篇批评。','未给样本不当所有国人/所有荐股者的既成事实或智力判断，后假设模型另录。')
note('372-b004 372-b005 372-b006 372-b007','unverified-author-stock-performance-context','作者列16股涨幅200%以上/150%以上/100%以上/50%以上和入场成本自述，完整保留源码。','未外核价格基准/费用/账户权重，涨幅不是读者可得组合收益，不当荐股准确率/本项目绩效；表两档连字不改原文。')
note('372-b008 373-b000','historical-learning-and-author-personal-closing','作者小道大道、猎鲸学习愿望及个人修辞收尾。','不证自称猎鲸机构能力，不构成独立交易规则。')
note('373-b003','historical-stock-boast-date-tail-context','作者联通自述/嘲讽，末5/10 15:36:28头属于后段，前段仍5/9。','未核联通收益/公开直播，不当当今价格；时间头归属不反向污染。')
note('374-b009','historical-999-wash-intent-claim','作者称翻两倍暗示洗盘及将改方法。','未核动机/控盘与收益，不能把翻倍当所有股必洗通用阈值。')
note('377-b005','historical-location-context','作者在外地/解盘承诺前言。','不证明控盘能力或当前日程。')
note('377-b007','historical-oscillation-study-and-416-boast','震荡练习提示及416首翻300%/国安对比、行程。','未核300%与账户收益，不当现在标的表现；技术练习已由周围命题涵盖。')
note('377-b009 377-b010 378-b000 378-b001 378-b002 378-b003 378-b004 378-b006 378-b008 378-b009 378-b010 378-b011 379-b000','historical-policy-personal-allegation-context','5/12监管警示、政策/人脉剧本与360身心比喻、政治类别批评及自引，全部读。','保历史观点/未核指控，不证官员动机、政策必按360人体节律或现今法律；技术模式三选/作者收费意见另录。')
note('379-b002 379-b007','historical-travel-personal-context','深圳/长沙旅行前后和食物/美男感想。','非技术买卖或当前行程。')
note('379-b006','historical-policy-and-composure-context','股改风险/幕后事情自述及冷静按方法的提醒。','未核幕后指控，不作为技术定理；方法建议已在周围技术段保留。')
note('379-b010 380-b000 380-b001 380-b002 380-b003 380-b004 380-b005','nontechnical-political-poem-context','多空政治评语、97年唐家兄弟自述与湘火炬四句诗全读。','诗句/政治修辞非缠论技术，未核公司历史意图或人员私德，不转为事实命题。')
note('380-b007','source-closing-rhetoric','作者问今天爽吗的开场。','不作为收益验证。')
note('381-b000 381-b001 381-b012 382-b006','historical-learning-stock-intent-and-travel-context','训练者/独立学习比喻、上实医药/600607收益与对手动机、机场/腐败活动。','未核个股收益/主体意图，不用读者利润反证作者全市场保证，不执行出行。')
issue('recommendation-flow-hypothetical-not-accuracy-or-legal-universality','371-b005 371-b006 371-b007 371-b008 371-b009 372-b000 372-b001 372-b002 372-b003','10万/5%/5000/2000股为假设流量模型，不是真实荐股准确率；会员结构/私募演化/所有收费垃圾为作者评价非普遍法律分类。','不把描述变组织操盘程序，不认证私募全部出自传销或免费推荐无利益冲突，股票对象有级别买点条件独立。',True)
issue('sixteen-stocks-performance-wash-and-market-control-unverified','372-b004 372-b005 372-b006 372-b007 374-b009 377-b007 381-b000 381-b012','16股涨幅与416翻300%、999翻倍洗盘/猎鲸控盘/600607自述未核，不等组合净收益或可复制绩效。','保上下文和原单位、时间、基准不补造；未用价涨证明所有买点/理论正确。')
issue('B-third-buy-C2-finished-types-and-MACD-zero-axis','374-b006 375-b001 375-b002 375-b004 375-b005','B三买后才结束，C2需完整且不创新高仍未完；作者只答B和类型完成，不认可读者两个次级中枢/只MACD完整判据。','需既有三买递归/完成定义和比较对象，不把1条指标上轴当所有二买或将读者A/C1/C2假设全收。',True)
issue('historical-1429-linear-pressure-360-rates-and-chart-1249','375-b011 375-b012 375-b013 375-b014 376-b000 376-b001 376-b002 376-b003','1429模型/90和180年点速率及360比例为作者拟合，图首峰1249与正文1429矛盾；后月图有5/31及后K，不能证5/10预测。','原数字/公式/近似差分别留，未给样本外验证或360到点/年必然性，不与普通历史密集压力线混为同义。',True)
issue('three-month-midterm-patterns-support-and-forming-scope','376-b004 376-b005 377-b000 377-b001 377-b002 377-b003 377-b004 378-b005 378-b006 380-b010 382-b002','中期1/2线三条模式/至少3个月和7月为作者历史判断，5479公式两式15因子不同语义，最终级别/形式仍形成中；突破迟早与前提未实证。','不把日内强中弱三分支和中期顶/强盘/强破混用，未伪造概率、期限或预先完成结构。',True)
issue('day-centers-4000-4040-and-extend-expand-wording','373-b002 374-b001 377-b006 379-b003 379-b004 379-b005 379-b009 379-b011 380-b008 382-b000 382-b001','4000突破要先中枢再三买也可三卖，4040是特定案例，不是一般扩展定义；377扩张与后扩展原词分开，周缺口10:17不定周背驰级。','核日内借用/一般中枢层次、完整三段/波动区间与级别，不因价格站稳一项补完所有扩展条件。',True)
issue('source-date-tail-four-later-charts-and-CCTV-reader-evidence','373-b003 373-b004 374-b000 374-b001 374-b002 381-b003 381-b004 381-b005 381-b006','5/10时间在5/9尾、四图后加；600832图引5/17CCTV读者而非作者，哪两段指示不能因后绘图变作者背书。','只改四段日期和空格，保原字/坐标；图来源/时间/角色独立，读者例不加reviewed作者证据。',True)
issue('profit-strength-policy-and-paid-tip-opinion-boundaries','378-b004 378-b005 379-b004 379-b005 380-b010 382-b002 382-b003 382-b004 382-b005','震荡收益胜单边/全走势都技术被理论包含、政策和360人体周期与收费者价值评价未独立实证。','保作者主张/不确定性，不转当前投资/法律/医学事实，技能限制不证实际执行必然利润。')
relations={
 'recommendation-self-reinforcing-flow-hypothetical-numbers':[('短线荐股','市场心理','qualifies')],
 'tiered-members-early-buy-control-flow-stability-risk':[('短线荐股','资金食物链','qualifies')],
 'funds-redemption-risk-tolerance-and-plural-capital-ecology':[('基金赎回','资金食物链','qualifies')],
 'buy-by-level-point-not-author-target-or-chase':[('短线荐股','买卖点','qualifies')],
 '4000-valid-break-center-then-third-buy-failure-third-sell-possible':[('突破','第三类买点','qualifies')],
 'B-needs-third-buy-otherwise-oscillation-consolidation-divergence':[('盘整背驰','第三类买点','qualifies')],
 'C2-incomplete-no-high-no-confirmed-third-buy':[('第三类买点','完成','qualifies')],
 '1429-historical-pressure-model-start-and-first-two-tops':[('1429点历史压力线','经验压力线','qualifies')],
 'pressure-rates-360-per-year-fractions-author-basis':[('1429点历史压力线','时间之窗','qualifies')],
 'half-line-effective-break-new-regime-otherwise-old-speed':[('1429点历史压力线','突破','qualifies')],
 'pressure-line-three-months-before-july-claim-market-chooses':[('1429点历史压力线','市场合力','qualifies')],
 'half-line-center-ultimate-level-form-still-forming':[('1429点历史压力线','完成','qualifies')],
 'may17-4040-key-extension-versus-expansion-conditional':[('中枢扩展','中枢延伸','qualifies')],
}
relations={'upper-l051-c-stage-'+k:v for k,v in relations.items()}
scopes={
 'recommendation-self-reinforcing-flow-hypothetical-numbers':['作者不妨假设的受众/跟买模型','10万量级、5%、5000人×2000股=1000万股，非真实调查'],
 '4000-valid-break-center-then-third-buy-failure-third-sell-possible':['2007年4000点案例','先有有效且有些级别的中枢，再出现其三买，仍有向下三卖失败分支'],
 'B-needs-third-buy-otherwise-oscillation-consolidation-divergence':['a+A+b+B+c问题中的B中枢','B未出三买仍震荡而非已结束的向上段趋势背驰'],
 'C2-incomplete-no-high-no-confirmed-third-buy':['所问C2回拉走势尚未完成','相关走势类型均须完成，不能预断不回原中枢'],
 '1429-historical-pressure-model-start-and-first-two-tops':['作者以1992年5月1429为月线模型基点','历史近似拟合/未独立样本外验证'],
 'half-line-three-scenarios-top-balance-or-strong-break':['2007年5月围绕每年180点的1/2线','三条为作者可能路径，不预选唯一或给概率'],
 'oscillation-until-third-points-third-sell-wait-adequate-bottom':['原中枢震荡持续、未三买卖前','三卖后停止原策略回补，等够级别底背驰'],
}
for r in rows:
 if r['id'].split('upper-l051-c-stage-')[1] in scopes:r['conditions']=scopes[r['id'].split('upper-l051-c-stage-')[1]]

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
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], '读者联通买卖自述、C1/C2两个中枢/完成和背驰、每日自动公式筛选、CCTV600832用5分看1分的两段比较均保留原身份，不自动当作者认可；引用作者话仍是读者引文。'
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
        'note': '荐股流入为作者假设非命中率，付费/组织类别非法律判定；1429历史拟合/360比例/三个月作者强语保边界，图1249不修1429；B需三买、C2完整，日内与中期三模式分开，扩张/扩展原词不静合，CCTV图不作作者证据。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=f['note'],
             figure_source_review='实际查看371至382十二页和四整图；373至5/11，376选5/31并有后月K/1249对1429，380至5/17，381至5/18且为CCTV读者问答。均后加原发未核，未来K不证早前预测，381图不关联为作者命题。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 129 and Counter(x['lesson_number'] for x in ledger) == {51: 129}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [51], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(371, 383)), 'figure_objects_viewed': 4, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '51课129段12页4整图同模型四轮；4段日期归5/10与12空格规范、四后图；荐股模型/未核收益、B与C2完成、历史压力线360比例/三分支/形成中和数值图源分层，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


