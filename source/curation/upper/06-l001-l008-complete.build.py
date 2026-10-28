"""Materialize manually read stage-C lessons 1-8; all SQLite access is read-only.

Claims below are manual semantic selections, not keyword generated claims.
Only the batch-06 artifacts are written. Import is never invoked without --check.
"""
import hashlib
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).parent
KB = ROOT / 'shared-knowledge/v0.1.0'
BASE = '06-l001-l008-complete'
DOC = 'volume_1-a53e99c37ca5'
REVIEWER = 'Codex 主代理 / 阶段C上册1至8课同模型四轮审读'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id BETWEEN 'lesson-001' AND 'lesson-008' ORDER BY pdf_page,block_index,id")}
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
aliases = {a: r['label'] for r in concepts.values() for a in json.loads(r['aliases'])}
rows, pending, rejected = [], [], []
notes, reused = {}, {}

def pid(short):
    page, block = short.split('-', 1)
    return f'{DOC}-p{int(page):04d}-{block}'

def ev(short, quote=None, figures=()):
    p = passages[pid(short)]
    quote = p['text'] if quote is None else quote
    start = p['text'].find(quote)
    assert start >= 0 and p['text'][start:start+len(quote)] == quote, (short, quote)
    return {'passage_id': p['id'], 'quote': quote, 'quote_start': start, 'figure_ids': [f'{DOC}-p{page:04d}-fig{n}' for page,n in figures]}

def claim(lesson, slug, text, labels, citations, check, level=3, conditions=(), exceptions=(), ambiguity='none', context=None, figure_note=None):
    cid = f'upper-l{lesson:03d}-c-stage-{slug}'
    assert cid not in old and cid not in {r['id'] for r in rows}, cid
    labels = list(dict.fromkeys(aliases.get(x,x) for x in labels))
    context = context or f'第{lesson}课正文及所附问答的本条论述'
    reasons = {1:'基础核心：本条为明确基础定义。',2:'主要方法：本条直接限定选股、持仓、退出或风险控制。',3:'补充深化：本条保留技术解释、行为前提或方法边界。',4:'背景细节：本条仅保存历史个案、观点或当时预期。'}
    r = {'id':cid,'text':text,'kind':'explicit','conditions':list(conditions),'exceptions':list(exceptions),'concepts':labels,'ambiguity_status':ambiguity,
         'review_note':f'语境：{context}。适用条件：'+('；'.join(conditions) if conditions else '仅限本条明示的对象及来源语境')+f'。四轮处理：完整读本段与续段/问答，拆分原子命题，对照当前reviewed集合和标准概念后逆向核验；{check.rstrip("。")}。仅据固定汇编底本，未与原博客核对；同模型四轮不声称独立多人或人工审查。',
         'reviewer':REVIEWER,'importance_level':level,'importance_reason':reasons[level]+check,'evidence':citations,'relations':[]}
    if figure_note: r['figure_review_note'] = figure_note
    assert all(not e['figure_ids'] for e in citations) or figure_note
    rows.append(r)
    return cid

def issue(slug, shorts, description, action, blocker=True, candidates=()):
    p = {'id':f'upper-l001-l008-c-stage-pending-{slug}','status':'pending','passage_ids':[pid(s) for s in shorts],'description':description,'suggested_action':action,'candidate_propositions':list(candidates),'blocks_full_semantic_extraction_completion':blocker,'reviewer':REVIEWER}
    pending.append(p)
    return p['id']

def note(shorts, disposition, reading, atomic, inverse):
    for s in shorts:
        assert pid(s) in passages, s
        notes[pid(s)] = {'disposition':disposition,'reading':reading,'atomic':atomic,'inverse':inverse}

# Manual selections, first six lessons. Continuations are cited separately.
claim(1,'real-business-skill-not-transfer','作者指出在其他行业聪明或成功，并不意味着进入资本市场后仍能做好；实业与虚拟市场之间存在适应差异。',['市场心理'],[ev('8-b010'),ev('9-b000')],'保留“很少”“基本很难”的经验语气，不写成所有实业经营者必然失败。',4)
claim(1,'renminbi-resources-capital-market-case','作者回顾人民币放开后的建议：基于资源全球涨势、人民币升值与虚拟市场吸纳资本的判断，劝实业朋友把部分资金分流到资本市场，并预期至少大X浪级别的行情。',['宏观市场判断','经济大势'],[ev('9-b001')],'只是2005年至2006年叙事中的当时判断；部分资金、至少大X浪均保留，不验证预测或套用后期走势级别定义。',4,conditions=['2006-06-07回顾“去年人民币放开后”的历史建议'])
claim(1,'consumer-restructuring-selection-case','作者回顾2006年三四月曾建议朋友关注中国快速消费品企业、可能面临重组的大周期行业股票及权证，理由是外资大基金接触收购消费品企业及周期行业重组。',['操作策略','题材股'],[ev('9-b003')],'关注对象、当时收购与重组背景俱保留，不改成普遍荐股清单。',4,conditions=['2006年三四月朋友要求具体股票的历史语境'])
claim(1,'three-yuan-local-stocks-case','作者回顾2006年五月曾敷衍建议朋友购买深沪两地3元上下的本地股，同时警告其依赖别人且不学习的做法会出问题。',['操作策略','市场心理'],[ev('9-b004')],'明确敷衍、历史时段、地点和3元上下；不输出当前价格筛选规则。',4,conditions=['2006年五月的特定朋友求荐股场景'])
claim(1,'learn-independently','作者要求市场参与者自己学习，不能指望别人长期像照顾小孩一样随时看顾其操作。',['操作熟练程度','独立系统'],[ev('9-b004','最好自己好好学学，别人怎么厉害也不可能整天像照顾小孩一样看着。')],'这是自主学习要求；不补出本课未提出的系统设计或技术步骤。',3)
claim(1,'experience-not-profit-criterion','作者反对用“老人挣新人钱”概括市场，并以老参与者也会长期被套说明资历本身不能决定输赢；其表述是明白人挣糊涂人的钱。',['市场心理'],[ev('9-b006','有人说，市场是老人挣新人的钱，而市场中的老人，套个10年8年的一抓一大把。其实，市场从来都是明白人挣糊涂人的钱。')],'作者的评价性归纳，不改写为可实证的年龄或年限盈利定律。',3)
claim(1,'profit-loss-evaluation-stance','作者在第1课把资本市场中的输赢作为评价参与者的唯一标准，而不以其在其他领域的成功为依据。',['市场心理'],[ev('9-b006','无论你在其他方面如何成功，到了市场里，赢输就是唯一标准，除此之外，都是废话。')],'保存作者立场，不扩展为对人的一般价值判断。',4)

claim(2,'reject-dealer-retail-binary','作者反对把庄家与散户的二元对立当作市场常识，并拒绝把资金量大、能影响走势者神化为超越技术、基本面和大势的无所不能者。',['主力资金','散户','市场心理'],[ev('9-b008'),ev('9-b009'),ev('10-b002','市场没有什么庄家，有的只是赢家和输家！')],'“没有庄家”按对庄家神话及二元分类的批评收录；不是否认大资金存在、控盘行为或后期资金层次论述。',3)
claim(2,'large-money-not-omnipotent-case','作者以准备二十亿元坐庄者和大量失败的所谓庄家为例，反对把大量资金本身当成坐庄成功的保证。',['主力资金','市场风险'],[ev('10-b000'),ev('10-b001')],'二十亿元是聚会个案，失败描述为作者经验；不编资金阈值或失败概率。',4,conditions=['第2课聚会与庄家失败的历史叙事'])
claim(2,'match-tools-to-targets-metaphor','作者用小弓箭打野兔、屠龙刀不必抓蛇的比喻，提示市场参与目标需与自身手段相称，关键在是否具备相应手段。',['资金管理','操作策略'],[ev('10-b002','市场就是一个围猎的游戏，当你只有一把小弓箭，你可以去打野兔；当你有了屠龙刀，抓几条蛇来玩当然就没劲了，关键你是否有屠龙刀！')],'仅保留比喻的能力匹配含义，不增设具体资本量、杠杆或收益目标。',3)

claim(3,'remove-stock-preferences','作者要求在市场中杜绝个人喜好，不对股票形成长久情感依恋，因为市场诱惑可以通过参与者的喜好形成陷阱。',['市场心理'],[ev('10-b005')],'针对股票喜好和情感依附；与既有当下直观命题相关，但本条具体补充喜好陷阱。',3)
claim(3,'stock-good-relative-profit-purpose','作者强调买入股票的目的在于通过买入获利，不能把股票被描述得好或被宣传得好，直接当成买入的充分理由。',['市场心理','操作策略'],[ev('10-b006')],'保留目标与宣传理由的区分；没有宣称任一股票必然获利。',3)
claim(3,'use-market-traps','作者认为看清市场陷阱只是第一步，还应学习利用陷阱：要买时利用空头陷阱，要卖时利用多头陷阱。',['空头陷阱','多头陷阱','买卖点'],[ev('10-b007','当然，能看清楚自己周围的市场陷阱，还只是第一步，更进一步，要学会利用市场陷阱来赢钱。当你要买的时候，空头的陷阱就是你的最佳机会，当你要卖的时候，多头的陷阱当然就是你的天堂。')],'买与卖的方向分别保留；本课未给陷阱的可执行图形判据，不补成第三类买卖点等定义。',2)
claim(3,'bull-market-not-everyone-profit','作者指出不存在让所有人都赢钱的安排，即使大牛市中也会有人严重亏损。',['市场风险','牛市阶段'],[ev('10-b007','这世界上没有什么是可以让所有人赢钱的，连大牛市中都有很多人要亏损累累。')],'保留即使牛市仍有亏损的反例功能，不量化亏损人数。',3)
claim(3,'success-personal-capacity','作者把市场实践最终能否成功，归结到个人的智慧、秉性、天赋和勤奋。',['操作熟练程度','市场心理'],[ev('10-b007','而市场中的行为，就如同一个修炼上乘武功的过程，最终能否成功，还是要落实到每个人的智慧、秉性、天赋、勤奋上来！')],'四项联合为作者评价，不改成任一项充分保证成功。',3)
claim(3,'n-zhonggong-turnover-case','作者在2006-06-19的N中工评论中，把当日90%多的换手解释为中签者基本卖出，并明确对手盘包括其中、绝大多数在十几元卖出。',['流通量','市场心理'],[ev('10-b009')],'这是作者对当日换手的解释；含对手盘限制，不能据累计换手率建立普遍“所有原股东已卖”定理。',4,conditions=['2006-06-19 N中工上市首日评论'],context='第3课所附《鄙视所有对N中工15元不敢买50元就吃醋的人》')
claim(3,'n-zhonggong-t1-supply-case','作者把N中工当日下午急冲高，解释为买方力量较大而T+1限制下缺乏足够筹码供给，较大买单因而冲到50元附近。',['交易规则','流通量','市场心理'],[ev('11-b001','下午激烈冲高，又有什么可值得奇怪的，市场上要买的力量大，而由于T+1，没有足够的筹码供应出来，要买几百万股都跑到50元的，这不很正常吗？')],'仅当日个股供求解释；T+1不单独构成所有股票必涨的充分条件。',4,conditions=['2006-06-19 N中工当日下午特定供求情境'],context='第3课N中工上市首日附文')
claim(3,'n-zhonggong-average-price-argument','作者在该N中工评论中以当日均价18元、均价未大幅上涨，作为反对把该走势简单指为投机的论据。',['市场心理','价格区间'],[ev('11-b001','请注意，今天的均价是在18元，均价并没有大幅上涨，因此任何有关投机的说法都是可耻的！')],'只是作者当日论证，非本项目认定走势是否投机，也不作为普遍估值标准。',4,conditions=['2006-06-19 N中工当日评论'],context='均价与瞬间最高价的比较论证')
claim(3,'participants-diverse-expectations','作者借N中工不同参与者在十几元卖出与买入的分歧，指出市场向各方开放，市场过程包含参与者心理与看法的差异。',['市场心理'],[ev('10-b009'),ev('11-b000')],'保留买卖双方观点不同的个案解释，不补成后期“非完全绝对趋同交易”理论证明。',3,conditions=['N中工上市首日不同参与者买卖的评论语境'],context='2006-06-19附文跨页续段')
claim(3,'regulator-follow-rules-stance','作者主张市场参与者及管理层都应遵守规则；交易若有问题，应依据该问题处罚，而不应因一时喜好突然改变规则。',['交易规则','政策风险'],[ev('11-b002')],'保存作者监管立场及交易违规处理条件，不当作现行法律规则或法律意见。',3,conditions=['2006-06-19评论N中工及327历史干预的语境'],context='第3课关于交易规则与临时干预的附文')
claim(3,'legal-protection-rule-compliance-stance','作者主张，只要符合市场交易规则，包括N中工在内的走势应获法律保护，判断应以法律而非个人喜好为依据。',['交易规则','市场心理'],[ev('11-b003')],'“只要符合规则”是作者规范性主张的前提；不替读者作当时或当前的法律合规认定。',3,conditions=['符合市场交易规则这一作者明示前提'],context='2006-06-19对N中工走势是否应被干预的评论')

claim(4,'rationality-value-system-critique','作者批评以某套价值系统支持的所谓理性依据，企图据此必然战胜市场的思路。',['市场心理','技术分析'],[ev('11-b005')],'保留对确定性心理依据的批评，不引申为所有分析或理论一概无用。',3)
claim(4,'rationality-current-practice','作者把真正的理性定位为当下的实践，而非仅靠文字论说。',['当下','操作策略'],[ev('11-b006','但真正的理性从来都是当下的，从来都是实践的，而实践，从来都是当下的理性。')],'作者关于理性与实践的方法论立场，不新增具体图形规则。',3)
claim(4,'participation-pattern-failure','作者认为参与者介入时会与市场相互塑造；真正应关注的是介入模式在当下如何运行，尤其该模式如何失效。',['当下','操作策略','市场风险'],[ev('11-b007')],'模式如何死去按失效表达；没有补写止损价、回测模型或不存在于本段的失效算法。',3)
claim(4,'know-current-mode','作者要求市场参与者首先且始终清楚自己当前介入模式的当下状态。',['当下','操作策略'],[ev('12-b001','对于市场的参与者来说，首要且时刻必须清楚自己目前介入模式的当下，')],'保留“首要且时刻”的持续性要求；不同于预测下一步的任务。',2)
claim(4,'money-size-not-understanding','作者指出不知道自己在做什么的市场参与状态，与资金实力无关，并以见过大资金迅速崩溃说明资金大不等于明白。',['主力资金','市场风险'],[ev('12-b001','这种构成与资金实力无关，大资金死起来更快，一夜之间土崩瓦解的事情，本ID见得多了。')],'经验叙述与观点保留；不定义大资金必比小资金更快失败。',3)
claim(4,'n-zhonggong-rational-entry-case','作者在2006-06-19以当早15元多买N中工，作为“理性是干出来的”这一实践立场的具体示例。',['当下','操作策略'],[ev('12-b001','今早15元多买N中工就是理性！理性是干出来的，今天，你干了吗？')],'不把个案15元多转成普遍买点或验证实际成交。',4,conditions=['2006-06-19 N中工上市首日示例'])
claim(4,'exchange-response-stance-case','作者在2006-06-20对N中工的评论中，认为由交易所而非证监会回应单个股票一天走势符合规则，并赞同深交所当时“表现正常、不调查”的回应。',['交易规则','政策风险'],[ev('12-b004'),ev('12-b005','首先，由交易所而不是证监会来回应这事，符合规则。')],'机构职责评价及回应均为历史作者论述，不认证当前监管职责或当年全部调查事实。',4,conditions=['2006-06-20对N中工首日走势回应的评论'],context='第4课附文《为管理层对N中工走势的回应热烈鼓掌》')
claim(4,'n-zhonggong-followup-market-stance','作者认为N中工之后如何走应由市场化过程决定，管理层不宜过多干预。',['交易规则','政策风险'],[ev('13-b001')],'仅保存当时监管立场；不把后续涨跌纳入承诺。',3,conditions=['2006-06-20 N中工后续走势评论'],context='第4课附文结尾')

claim(5,'observe-operate-not-eloquence','作者用猎手比喻强调观察和实际操作，评价不在于能说出多少道理，而在于置身其中的实际感受和直觉。',['当下','操作熟练程度'],[ev('13-b003'),ev('13-b007')],'比喻属于方法论；不据“无需分析”标题否定后文明确采用的技术分析。',3)
claim(5,'observe-without-prejudice','作者要求看实际出现的对象，不让已有成见改变观察，把主观想到的机会当成亲眼看到的机会。',['当下','市场心理'],[ev('13-b006')],'与既有upper-l019-c-stage-emotion-replaces-present相关；本条补观察与成见的具体要求，不宣称互相独立验证。',3)
claim(5,'avoid-rumors','作者要求在市场中用眼睛观察、用心感受，而不依赖耳听的流言蜚语。',['公开信息','市场心理'],[ev('13-b007','用你的眼睛去看，用你的心去感受，而不是用你的耳朵去听流言蜚语，用你的脑筋去抽筋！')],'不将流言转换为作者承认的公开第一手事实。',3)
claim(5,'self-use-vs-investment-property','作者在2006-06-26房地产附文中区分为自住买房与房地产投资，并明确自己的批评针对投资而非自住。',['长期投资','房地产投资'],[ev('13-b009'),ev('13-b010','当然，本ID买过这么多次房子，并没有脑子进水，因为这只是为了自住，而不是投资。这里说的是投资。')],'对象限制是自住/投资的区分；不输出当前房地产交易建议。',4,conditions=['2006-06-26房地产附文的历史观点'],context='第5课所附房地产评论')
claim(5,'property-rights-investment-critique','作者在该房地产附文中把投资同可实际主张的权利联系起来，并以中国土地非私有为前提，将业主描述为长期租户，质疑其所谓房地产投资。',['房地产投资','市场风险'],[ev('13-b010'),ev('14-b000')],'权利论证、土地前提和长期租户均作为作者2006年立场；没有核对法律事实或土地到期规则，不能作当前法律结论。',4,conditions=['2006-06-26作者讨论中国房地产投资的语境'],context='第5课房地产附文跨页段')
claim(5,'property-protection-war-revolution-stance','作者认为历史上私有财产保护承诺可能被战争、革命打断，并据此批评将其视为无条件保障。',['房地产投资','市场风险'],[ev('14-b001','而且历史上私有财产的保护其实不过等价于对没有战争和革命的空头承诺，战争、革命一来，企图保护私有财产的自己连命都不一定保住，就甭瞎掰了。')],'保存极端事件下的作者观点，不替其建立普适法学或历史结论。',4,conditions=['2006-06-26房地产评论中的权利保护批评'],context='第5课房地产附文')
claim(5,'property-warrant-comparison-stance','作者在2006年以部分权证一两个月涨十倍的历史描述作比较，把中国房地产比喻为70年权证，并否定到期续价承诺，认为开发商类似创设权证者。',['房地产投资','权证','市场风险'],[ev('14-b002')],'涨十倍仅为当时部分个案的作者描述；70年权证和到期判断是历史立场，未验证、不能当作当前物权规则或任何收益保证。',4,conditions=['2006-06-26中国房地产与当时权证市场的比较'],context='第5课房地产附文')
claim(5,'developer-speculation-exception','作者虽然批评房地产投资，仍承认在有人以更高价格接手的条件下存在投机机会，并以开发商向小业主售房作为例外角色。',['房地产投资','操作策略'],[ev('14-b003')],'投资批评与投机机会分开；保留开发商角色和后续买家条件，不宣称所有开发商盈利。',4,conditions=['2006-06-26评论语境','存在愿意接手的后续买家'],context='第5课房地产附文结尾')

claim(6,'wait-for-opportunity','作者要求在时机未到时耐心等待市场出现可参与的机会，不因频繁关注而强行操作。',['当下','操作策略'],[ev('14-b007')],'保留时机到/不到两种状态；“提款机”只作作者比喻，不写成获利保证。',2)
claim(6,'safety-and-opportunity-joint','作者把安全与存在获利机会列为值得投机的联合前提，强调并非每一种机会都应参与。',['市场风险','操作策略'],[ev('14-b008')],'“又安全又能G点”联合条件不可拆成任一项充分；安全为作者评价，非无风险认证。',2)
claim(6,'dual-warrant-issuer-incentive','作者解释同时有认购与认沽权证的选择时，认为企业通常不会希望认沽兑现，因为兑现要付真金白银，但明确排除行情特别不好的情形。',['权证','市场风险'],[ev('14-b009'),ev('15-b000','否则是不会让认沽兑现的，因为不兑现，这就是一个空头支票，而兑现是要掏真金白银的。')],'跨页“除非行情特别不好”已读并保留；是作者的激励判断，不是发行人法定义务或不兑现保证。',3,conditions=['同一对象既有认购又有认沽权证','行情并非特别不好'],exceptions=['行情特别不好时原判断不再成立'])
claim(6,'dual-warrant-safety-line-method','在同一对象既有认购又有认沽、且行情并非特别不好的论证下，作者把认沽与认购的行权价差称为认购权证最安全的底线。',['权证','安全线','市场风险'],[ev('14-b009'),ev('15-b000','因此，对既有认购又有认沽的认购权证来说，认沽和认购的行权价之间的差价，就是认购权证最安全的底线。')],'仅记录本课作者方法，保留双权证与行情例外；未补行权比例或套利证明，也未将其认证为可执行的无风险下限。',2,conditions=['同一对象既有认购又有认沽权证','作者所设企业避免认沽兑现的激励情境','行情并非特别不好'],exceptions=['行情特别不好时原激励判断有例外'])
claim(6,'wuliangye-baogang-body-values-case','第6课正文将五粮液、包钢认购权证的安全底线分别写为1.02元、0.43元，并称作者当时分别在1元多、4毛多买入。',['权证','安全线','成本'],[ev('15-b000','对于五粮液、包钢认购权证，这个底线就分别是1.02和0.43元。而本ID当时分别在1元多和4毛多吃他们，是不是和去银行提款一样安全？')],'准确保存正文数值及自述，不改0.43为0.45；附列2.00/2.45差值冲突另列pending，本条只确认“正文写了什么”，不确认底线计算或成交。',4,conditions=['2006-10-24第6课回顾当年四月五粮液、包钢权证布局'],ambiguity='source_internal_numeric_conflict')
claim(6,'small-float-capacity','作者指出五粮液、包钢权证盘子小，容纳不了太大资金，并把这一容量约束同小盘股票相比较。',['流通量','资金管理'],[ev('15-b000','唯一遗憾的是，他们的盘子都太小，属于小男人的类型，容纳不了太大的资金。小男人，没什么劲；小盘的股票，也一样。')],'容量限制不能改成小盘股票必然不值得散户参与；第7课另有散户可做小盘的限定。',3)
claim(6,'understand-before-speculation','作者强调投机应建立在对市场充分理解、清楚其运作道理的基础上，而不是盲目操作。',['操作熟练程度','操作策略'],[ev('15-b001','投机不是瞎搞，是要清清楚楚地搞。要清清楚楚，就要对市场充分地理解，要明白其道道。')],'不从比喻补写本课未给的建仓、止损程序。',3)

# The interrupted draft also selected nontechnical historical commentary.
# Keep it as source context rather than publishing it as technical knowledge.
context_only_slugs = {
    'renminbi-resources-capital-market-case', 'consumer-restructuring-selection-case',
    'three-yuan-local-stocks-case', 'n-zhonggong-turnover-case', 'n-zhonggong-t1-supply-case',
    'n-zhonggong-average-price-argument', 'participants-diverse-expectations',
    'regulator-follow-rules-stance', 'legal-protection-rule-compliance-stance',
    'exchange-response-stance-case', 'n-zhonggong-followup-market-stance',
    'self-use-vs-investment-property', 'property-rights-investment-critique',
    'property-protection-war-revolution-stance', 'property-warrant-comparison-stance',
    'developer-speculation-exception',
}
context_drafts = [r for r in rows if any(r['id'].endswith('-'+s) for s in context_only_slugs)]
rows[:] = [r for r in rows if r not in context_drafts]
for r in rows:
    if r['id'].endswith('-rationality-value-system-critique'):
        r['text'] = '作者批评以某套价值系统支持的所谓理性依据，企图据此战胜市场的思路。'
    elif r['id'].endswith('-observe-without-prejudice'):
        r['text'] = '作者要求看实际出现的对象，不让已有成见改变观察，不把主观想到的机会当成亲眼看到的机会。'

claim(7,'confidence-and-rhythm','作者把当时部分散户赚了指数却亏钱的主要原因归为对牛市缺乏信心、对牛市节奏没有把握。',['牛市阶段','市场心理'],[ev('17-b001')],'仅记录2006-11-16作者的阶段判断；不认证所有亏损者的原因，也不建立信心就能盈利的充分条件。',3,conditions=['2006-11-16所述牛市阶段与散户现象'])
claim(7,'first-tier-leads-bull-stage','作者把2006年5月前有色上涨称为牛市预热，把当时金融等指数股上涨称为第一阶段，并以一线股先涨说明其所说牛市节奏。',['牛市阶段','板块轮动'],[ev('17-b001')],'保留作者当时归类及“基本这样”的经验措辞；不把所有市场、所有时期的一线股领先写成实证定律。',4,conditions=['2006-11-16作者对当时行情及1996年例子的比较'])
claim(7,'strong-stock-pullback-entry','对错过当时牛市节奏而跟盘技术尚可的散户，作者建议在回档时跟进强势股票。',['操作策略','散户','操作熟练程度'],[ev('17-b002','错过了这个节奏怎么办？如果你跟盘技术还行的，就要在回档的时候跟进强势股票。')],'牛市、错过节奏、跟盘技术、强势股与回档联合保留，不写成任何下跌都该买。',2,conditions=['本课讨论的牛市情境','错过前段节奏','跟盘技术还行','对象为回档中的强势股票'])
claim(7,'novice-new-stock-volume-breakout','在本课牛市讨论中，对跟盘技术不足者，作者给出的一个筛选方向是放量突破上市首日最高价的新股。',['放量突破','成交量','次新股','操作策略'],[ev('17-b002','如果跟盘技术不行，有一种方式是最简单的，就是盯着所有放量突破上市首日最高价的新股以及放量突破年线然后缩量回调年线的老股，这都是以后的黑马。')],'放量、上市首日最高价、新股均保留；“黑马”是作者当时的评价，不保证入选必盈利。',2,conditions=['本课牛市中找股票的方法','跟盘技术不足','放量突破上市首日最高价'])
claim(7,'old-stock-year-line-retest','在同一牛市筛选方法中，作者要求老股先放量突破年线、然后缩量回调年线，并特别关注年线走平后向上出现拐点者；尚在年线下的先等上年线。',['均线','放量突破','成交量','操作策略'],[ev('17-b002','如果跟盘技术不行，有一种方式是最简单的，就是盯着所有放量突破上市首日最高价的新股以及放量突破年线然后缩量回调年线的老股，这都是以后的黑马。特别那些年线走平后向上出现拐点的股票，一定要看好了。至于还在年线下面的股票，先别看了，等他们上年线再说。')],'突破与回调有时间顺序，不拆成任一放量或任一回调足够；不添加正文未给的回调容差。',2,conditions=['本课牛市选股语境','老股先放量突破年线、随后缩量回调年线'])
claim(7,'baogang-year-line-case','作者以宝钢为上述年线方法的历史例子：突破年线后缩量回调，10月23日价格回到4.20元、当时年线4.17元，随后放量启动，到11月16日已6元多。',['均线','放量突破','成交量'],[ev('17-b002','举一个例子，去看看宝钢，突破年线后缩量回调，10月23日回调4.20元，当时年线就在4.17元，然后再放量启动，今天，11月16日，已经6元多了，50%就这么完成了。',figures=((17,1),(18,1)))],'是作者自述的特定日期价格例子；本项目未重算收益、未以图中框线推出额外买点。',4,conditions=['2006年宝钢及2006-11-16回顾'],figure_note='主代理实际查看PDF17/18两张宝钢日线图：17页光标2006/11/16、18页光标2006/10/23，两图均含成交量及MACD、年线附近矩形和正文摘录；18页显示MA250约4.17与回调4.20，17页显示6元多。图形与文字的例子对应，但制作人与加框/摘录者未核；仍为unverified，不当作原博客作者原图，也不据50%文字证明真实收益。')
claim(7,'small-caps-and-false-breakouts','作者因资金容量通常只看大盘股，但说明散户可按相同原则看小盘股；同时提醒大盘股启动骗线一般较少，小盘股未必如此。',['流通量','资金管理','散户','假突破'],[ev('17-b002','本ID一般只看大盘股票，小盘股没法进去，但散户可以看小盘股，原则是一样的，不过小盘股可要留意，一般大盘股启动的骗线比较少，小盘股可不一定，这都要自己好好去揣摩。')],'不把作者容量限制变成散户禁做小盘，也不把骗线比较变成统计概率。',3,conditions=['本课大盘/小盘参与容量和筛选方法比较'])
claim(7,'retail-waits-clear-trend','作者要求散户不以抄底逃顶为目标，等趋势明确才介入或退出。',['散户','趋势','操作策略'],[ev('17-b002','散户就当好散户，别整天想着抄底、逃顶，底都让你抄了，顶都'),ev('18-b000')],'跨页续句保留；本课“趋势明确”没有形式算法，不补以后走势类型定理为当前句判据。',2,conditions=['第7课面向散户的操作建议'])
claim(7,'midterm-thirty-day-line-hold','作者对已经上涨的股票提出，中线连三十天线都没跌破时应视为很强并持有，不随意抛弃。',['均线','持股','操作策略'],[ev('18-b001','一只股票长起来千万别随意抛了，中线如果连三十天线都没跌破，证明走势很强，就要拿着。')],'保留已经上涨、中线、三十天线未破；不推成跌破就必须立即卖的逆命题。',2,conditions=['股票已上涨','中线三十天线未跌破'])
claim(7,'short-trade-repurchase-condition','对水平较高者，作者允许上涨时依据短线指标做差价，但高位卖后若中线图形未走坏，回档时应买回，尤其尚未加速的股票。',['操作熟练程度','操作策略','持股','指标对比'],[ev('18-b001','当然，如果你水平高一点，在上涨的时候，根据短线指标可以打短差，这样可以增加资金的利用率，但高位抛掉的，只要中线图形没走坏，回挡时一定要买回来，特别那些没出现加速的股票。')],'操作水平、上涨、中线未坏和回档全保留；未补短线指标、次数或仓位。',2,conditions=['操作者水平较高','上涨时依据短线指标做差价','高位卖后中线图形未走坏','回档买回，尤其未加速者'])
claim(7,'slow-rise-accelerates-exit-watch','对缓慢推升的股票，作者要求一旦加速上涨就时刻注意出货机会。',['操作策略','上涨','卖点'],[ev('18-b001','有一个抛股票的原则，分两种情况，一种是缓慢推升的，一旦出现加速上涨，就要时刻注意出货的机会；')],'“注意机会”不改写为加速即刻全部卖出；没有给数值加速阈值。',2,conditions=['前期缓慢推升','随后出现加速上涨'])
claim(7,'strong-first-wave-second-wave-warning','对第一波就猛烈上涨、调整后再涨的股票，作者要求第二波一旦出现背弛或放巨量，就警惕并寻找退出机会。',['操作策略','背驰','成交量','卖点'],[ev('18-b001','另一种是第一波就火暴上涨，调整后第二波上涨一旦出现背弛或放巨量的，一定要小心，找机会走人。')],'保留第一波、调整、第二波顺序，背弛与放巨量为替代条件；引文原写“背弛”，规范标签复用“背驰”，未宣称本句已给严格背驰定义。',2,conditions=['第一波猛烈上涨后有调整','随后第二波上涨出现背弛或放巨量之一'])
claim(7,'operation-timing-needs-practice','作者说明具体操作的火候需要本人在实践中体会，不能只靠文字讲授获得。',['操作熟练程度','操作策略'],[ev('18-b001','具体的操作是一个火候的问题，必须自己用心去体会，就像煲汤，火候的问题是没法教的，只能自己在实践中体会。')],'火候是经验描述，未给出程序参数；不宣称所有知识都不可学习。',3)
claim(7,'bull-market-component-attention','在牛市语境下，作者要求关注成分股，特别对已有一定资金规模者如此，并将其参与者称为大部队。',['牛市阶段','资金管理','主力资金','操作策略'],[ev('18-b002','还有一点必须提醒，在牛市中，一定要严重关注成分股，特别有一定资金规模的，成分股都是大部队在战斗，别整天跟那些散兵游勇玩，那些人自己都自身难保，')],'关注不等于每只成分股必买或必涨；不设不存在的资金阈值。',2,conditions=['本课牛市语境','尤其操作者有一定资金规模'])
claim(7,'rotation-capital-use','作者把避开大的回档、借回档踏准轮动节奏作为提高资金利用率的原则。',['板块轮动','资金管理','调整','操作策略'],[ev('18-b002','要达到这种水平，其实很简单，就一个原则：避开大的回挡，借回挡踏准轮动节奏。')],'同段4/5倍收益是作者评价性目标，不作为已验证收益或此原则的保证；大回档阈值未给。',2,conditions=['本课牛市中的资金利用讨论'])
claim(7,'fundamentals-as-other-beliefs','作者在第7课针对所述散户，要求了解别人心目中的基本面及相应影响，而不要以自己相信基本面来壮胆。',['基本面','市场心理','散户'],[ev('18-b002','所谓基本面，只是一个由头，给自己壮胆和忽悠别人用的。对基本面，只要知道别人心目中的基本面以及相应的影响就可以了，自己千万别信。')],'保留第7课措辞与对象；不据此删除第9课另行讨论的基本面程序，二者语境比较留待跨课查证。',3,conditions=['第7课对散户与当时基本面说辞的论述'])
claim(7,'find-failure-reason-before-retry','作者要求失败后先找到失败的真正原因，再寻找扳回机会，否则可能只是重复同一失败。',['市场风险','操作熟练程度'],[ev('19-b000','别给自己的失败找任何理由，失败只能是你自己的失败，失败就找机会扳回来，但前提是必须找到失败的真正原因，否则不过是延续不同的情节、相同的悲剧。')],'前提与行动顺序保留；不将找原因等同于下一次获利保证。',3,conditions=['操作已经失败','再寻机会前先找到真正失败原因'])

claim(8,'no-theory-guaranteed-profit','作者否认基本面、技术面等输入与获利输出之间存在必然因果链，但也反对绕过这些输入而直接取得结果的幻想。',['技术分析','基本面','市场风险'],[ev('19-b003'),ev('19-b004','投资领域，没有任何理论可以描述这种从“面”的输入到“里子”输出的必然关系，因为这种关系根本不存在。')],'这是作者的理论边界立场；保留否定必然和仍需输入两面，不改成任何方法都无用。',3)
claim(8,'market-must-show-activity','作者认为市场进入可投资视野前应先显示所述萌动，反对把长期没有活跃表现当成安全的充分理由，也反对随后见到活跃就追扑。',['操作策略','市场风险','市场心理'],[ev('19-b004','一个市场能进入可投资的视界，首先要显示其G点的萌动，否则还是一边凉快去吧。'),ev('19-b005')],'“萌动/高潮”是本课比喻，具体分类示例另列；不把活跃当唯一充分买入条件。',3)
claim(8,'dynamic-eligible-set','作者要求按所定萌动标准把股票动态分为可以操作与不能操作两类，将参与对象限制在可以操作类；分类标准可因人而异。',['完全分类','操作策略'],[ev('20-b001','具体对于股票来说，按其是否萌动的标准把所有股票动态地进行分类，一种是可以搞的，一种是不能搞的，将你参与的股票限制在能搞的范围内，不管任何情况，这是必须遵守的原则。当然，搞的分类原则，各人可以有所不同。')],'动态二类是参与范围，不是成功/失败预测；不把例子写成所有人同一固定参数。',2)
claim(8,'classification-example-averages','第8课举250天线及周线成交量压力线突破为分类示例；资金量不大且短线技术尚可者，可换用70天线、35天线或30分钟图的相应均线。',['均线','成交量','操作熟练程度','资金管理','完全分类'],[ev('20-b001','例如，250天线以及周线上的成交量压力线的突破；资金量不大且短线技术还可以的，可以把250天线改成70天线、35天线，甚至改为30分钟图里的相应均线；')],'小资金与短线能力是联合前提，70/35/30分钟是可替代例子，不能并成同时满足的万能买点；“以及”的联合要求细节另列待核。',2,conditions=['分类原则的示例','替换均线须资金量不大且短线技术还可以'])
claim(8,'classification-new-stock-first-high','作者对新股举上市第一日最高价作为可采用的分类标准。',['次新股','高低点','完全分类'],[ev('20-b001','对新股，可以用上市第一日的最高价作为标准；')],'本句只说标准，未逐字重申第7课放量条件；两课保持各自完整来源，不把缺省写成作者取消放量。',3,conditions=['对象为新股','本课允许采用的分类标准之一'])
claim(8,'classification-floor-and-traps','作者把接近第6课所述带认沽认购权证安全线作为另一分类示例，并称有一定水平者可识别、利用空头陷阱介入，具体专业方法留待以后。',['认购权证','安全线','空头陷阱','操作熟练程度','完全分类'],[ev('20-b001','还有，就是接近安全线的股票，例如在第六期里，本ID给出的一个带认沽权怔的认购权怔介入的安全线标准；而对于有一定水平的人，识别各种空头陷阱，利用空头陷阱介入是一个很好的方法，这种方法比较专业点，以后专门说。')],'两种示例分别保留，未将陷阱图形和权证下限作本课已经证明；安全线限制回查第6课。',3,conditions=['安全线示例参照第6课相应权证','空头陷阱介入面向有一定水平者'])
claim(8,'ineligible-only-changes-at-standard','分类原则确定后，作者要求严格只操作可操作类；不能操作的对象只有达到该分类标准、转为可操作对象，才可进入候选集合。',['完全分类','操作策略'],[ev('20-b002')],'例外是按标准转类，不能写成永久禁止某一只股票；贪图全部机会的修辞不另造收益定理。',2)
claim(8,'eligibility-does-not-remove-failure','作者说明达到萌动标准只是筛掉所述不能操作类，接着还要甄别介入后的失效，并把这一问题留到下一讲。',['完全分类','市场风险','操作策略'],[ev('20-b003')],'“早泄”为失效比喻，熊市80%以上/牛市大概30%没有样本或估计口径，单独待核；不把筛选通过等同必涨。',3)
claim(8,'survival-over-imagination','作者要求不以想象代替现实，把长期生存列为市场第一原则。',['市场风险','市场心理'],[ev('20-b008')],'30年是原文长期生存的修辞例子，不生成30年任意盈亏均算牛人的无条件标准；后续问答限定另列。',2)
claim(8,'profit-not-index-prediction','作者在答疑中表示关注赚钱而非预测大盘，并指出大盘下跌也可能赚钱。',['走势预测','操作策略'],[ev('20-b011'),ev('21-b000')],'跨页“预测它干什么”完整核对；“可以”不是任何下跌都能赚钱，不补交易机制。',3)
claim(8,'overall-failure-versus-local-failure','针对读者提出前25年惨败、后5年风光能否算牛人的问题，作者区分个别失败与整体失败：个别失败可允许，但不能影响大局；整体失败一次后基本难以翻身。',['资金管理','市场风险'],[ev('21-b004'),ev('21-b005')],'读者问题作为上下文、不作作者证据；“基本”与“一般”语气保留，不写成数学上绝无翻身可能。',2,conditions=['答复Of_fox关于30年生存与前25年失败的特定问题','区分个别失败与影响大局的整体失败'])
claim(8,'year-line-250-days-and-chart-periods','作者答复年线一般指250日均线，同时说明均线可在分钟、小时、周、月等各种周期图表中使用。',['均线','周期K线图','年线'],[ev('21-b010','年线一般指250日的均线，但在各种周期的图表上都可以用上。例如分钟图、小时图、周线图、月线图等都可以。')],'保留“一般”和图表周期举例；不把250分钟说成年线，也不把图表周期直接等同走势级别。',2)
claim(8,'avoid-large-prior-gain','作者告诫不要轻易介入涨幅过大的股票，从开始就学习以尽量小的风险换取尽量大的利润。',['追高','市场风险','操作策略'],[ev('21-b012'),ev('22-b000')],'跨页风险/利润续句完整；没有原文数值阈值，不补涨幅百分比。',2)
claim(8,'risk-first-total-loss','作者认为长期胜利应坚持风险优先、以最小风险换取最大利润；并以一百亿和一百万亏损百分之百都归零说明本金规模不能免除全损。',['资金管理','市场风险'],[ev('22-b003')],'作者风险原则与全损算例分明；不声称存在本项目实现的最优风险收益算法。',2)
claim(8,'contrarian-selection-asymmetric','作者答疑说人弃不一定取、人抢一定给，两个方向的表述并不对称。',['操作策略','市场心理'],[ev('22-b004')],'保存原文“不一定/一定”的不对称语气，语境为该次风险答疑；不扩成任何抢购都卖出或任何被弃都买入的无条件程序。',3,conditions=['第8课2006-11-21风险优先答疑结尾'])

# Source-specific unresolved questions. No draft here is sent to the reviewed importer.
issue('l006-warrant-numeric-conflict',['15-b000','15-b007','16-b002'],'正文包钢底线0.43元，而附列行权价2.45−2.00=0.45元；不能无依据替正文改数。','保留原文差异；核对同底本其他明确答疑，不能以外部常识覆盖。')
issue('l006-attached-terms-origin',['15-b001','15-b002','15-b003','16-b004'],'星号之后的包钢权证条款列表没有作者署名；配图行情晚于课程，附列技术资料身份未确认。','以汇编附列资料读取，不作为新增作者一般规则证据。')
issue('l006-warrant-floor-proof',['14-b009','15-b000'],'作者以企业不愿认沽兑现的动机论证安全线，未在本课给出套利、履约或极端行情下的完整证明。','保留作者明说及行情例外，不把安全线转成兑现保证。')
issue('l007-origin',['17-b002','18-b000'],'PDF17/18宝钢图已查看；制作人、矩形和黄色摘录的制作身份未核。','保留unverified，文字可独立支持作者所举案例。',False)
issue('l008-failure-percentages',['20-b003'],'熊市至少80%以上、牛市大概30%是作者在失效比喻中给出的比例，未给样本、时间范围或估计方法；医学比例不属技术知识。','原文保留，研究时标为作者经验性说法，不当项目统计结果。')
issue('l008-classification-joint-example',['20-b001'],'250天线以及周线成交量压力线突破是否要求同时满足，及“相应均线”参数，本段未给完整程序定义。','仅记录本段示例；具体程序需其他原文支持，不自行把示例固化成交易算法。')
issue('l008-monthly-case-annotation',['21-b011'],'600086答疑正文标2006-11-21、5.9元；PDF22后加图摘录标20061116、5.97元，且显示2007/11/30行情；正文“注：5月线位置”的注者未核。','正文案例保留为上下文；图不用于改正文日期价格，括号注释不自动作作者命题。')
issue('l004-chart-origin',['12-b001'],'PDF12中工日线/分时复合图已查看，黄色摘录及制图者未确认；没有据图新增交易规则。','维持来源未核，图留作历史案例定位。',False)
for item in pending:
    item['lesson_numbers'] = sorted({int(passages[p]['unit_id'].split('-')[1]) for p in item['passage_ids']})

# Per-passage reading decisions. Claims supply the detailed reverse checks;
# the following groups give reasons for material deliberately not made into nodes.
note(['8-b008','8-b009'],'transition','第1课标题、缘起及写股票与炒股票的区分。','标题和缘起不制造技术命题。','非课程前的房地产续文；处理从本课标题开始。')
note(['9-b007'],'transition','第2课课程标题及日期。','标题观点由随后三段关于庄家神话的完整陈述承载。','课程标题不脱离论述独立解释为不存在大资金。')
note(['9-b001','9-b002','9-b003','9-b004','9-b005'],'historical_context','朋友入市、人民币和行业判断、具体历史荐股与情绪变化。','一般自主学习要求另抽；个股价格和预测保留上下文。','不得改成当前选股规则或将大X浪自动等同后期走势级别。')
note(['10-b003','10-b004'],'transition','第3课标题、世界杯和庄家外貌的修辞。','不把世界杯前后大跌当经本项目验证的季节性规律。','技术方法从后续喜好陷阱段抽取。')
note(['10-b008','10-b009','11-b000','11-b001','11-b002','11-b003'],'historical_context','2006-06-19中工首日换手/T+1供求及监管立场附文。','行情与监管评论留作原文上下文，不发布一般交易或法律规则。','附文时间独立于第3课；没有据90%换手推定所有原始持有人离场。')
note(['11-b004','11-b008','12-b000'],'transition','第4课标题及生死/模式的哲理比喻与跨页续文。','实际方法已由模式失效和当下状态命题承载。','比喻不补成量化法则、程序或确定生死概率。')
note(['12-b002','12-b003','12-b004','12-b005','13-b000','13-b001'],'historical_context','2006-06-20监管回应附文及跨页完整句。','不构造现行法规、监管职责或股票允许波动的规则。','交易规则与资金异常为历史作者评价，未外部核法。')
note(['13-b002','13-b004','13-b005'],'transition','第5课标题及猎手/无言/自我成见的比喻。','观察与不受成见影响由邻近命题承载；不为同一比喻重复建节点。','不把无须分析解释为禁止后文技术分析。')
note(['13-b008','13-b009','13-b010','14-b000','14-b001','14-b002','14-b003'],'historical_context','2006-06-26房地产自住/投资、权利与权证比喻附文。','非股票技术正文或技术答疑，完整原文留查证，不导入默认技术命题。','不将70年权证等历史立场认证为现在的法律事实或收益比较。')
note(['14-b004','14-b005','14-b006'],'transition','第6课标题、孔子文章缘起与阴符引语。','不是权证安全线参数；引用不单独制造作者技术规则。','区分古籍引文与本课作者直接技术论述。')
note(['15-b002','15-b003','15-b004','15-b005','15-b006','15-b007','15-b008','15-b009','15-b010','15-b011','15-b012','15-b013','16-b000','16-b001','16-b002','16-b003','16-b004'],'unverified_attachment','星号分隔后的包钢认购/认沽条款、代码、行权价、比例、欧式窗口和正股图题。','作为汇编附列资料，身份未确认，不直接证成作者一般命题。','0.43与0.45分开留待核；没有依据后加图认定列表作者。')
note(['16-b005','16-b006','16-b007','17-b000'],'historical_context','第7课标题、基金经理和大叔个案；17页续句说箱形短差中涨不敢卖跌不敢买。','特定荐股/自述不再节点化；一般心理与后文技术方法分开。','没有将国航领导身份推成不能跌破发行价的普遍保证。')
note(['18-b003'],'transition','资本主义游戏修辞的跨页开头。','19页实际失败原因要求另抽。','暴力比喻不作为交易行为建议。')
note(['19-b001','19-b002','20-b000'],'transition','第8课标题、面/里子与采阳比喻；20页为19页续句。','输入输出关系和萌动标准由具体命题承载。','不生成性医学或人格评价节点。')
note(['20-b004','20-b005','20-b007','20-b010','21-b003','21-b009-s01','22-b002-s01'],'source_header','回复栏目及作者署名时间头。','只作发言者和回复时间锚点。','原页21/22无冒号作者头已正确分出，不能当读者正文。')
note(['20-b006','20-b009'],'historical_context','作者对当时牛市第一阶段的安抚和2001至2005不看股的自述。','阶段观点已由第7课语境命题承载；自述不构成买卖信号。','作者是否看股不作读者可执行技术条件。')
note(['21-b001','21-b002','21-b006','21-b007','21-b008','21-b009','22-b001','22-b002'],'reader_context','Of_fox长期生存问题、罗锅发言、傻妞年线/个股问题、冰火对风险理解。','均保留读者身份，供相邻作者答复理解；不能当作者同意的前提。','读者关于央行、经济学家的观点不冒充作者知识。')
note(['21-b011'],'historical_context_with_pending','600086连续8个月上涨后调整、70月均线长压和5.9至7.2箱体的当时答疑。','具体价格和高抛低回补保留个案上下文，正文括号注释与后图差异待核。','不从后加2007行情证明2006预测或把5.97改写成5.9更正。')

by_passage = defaultdict(list)
for r in rows:
    for e in r['evidence']:
        by_passage[e['passage_id']].append(r)
ledger = []
for passage_id, p in passages.items():
    linked = by_passage[passage_id]
    decision = notes.get(passage_id)
    assert decision or linked, ('unaccounted passage', passage_id)
    related = [x['id'] for x in pending if passage_id in x['passage_ids']]
    if linked:
        reading = '；'.join(r['text'] for r in linked)
        atomic = '；'.join('前提：'+('、'.join(r['conditions']) or '按具体陈述及上下文') for r in linked)
        inverse = '；'.join(r['review_note'].split('四轮处理：',1)[1] for r in linked)
        disposition = 'new_claim'
        if decision:
            reading += '；其余内容：'+decision['reading']
            inverse += '；'+decision['inverse']
    else:
        reading, atomic, inverse = decision['reading'], decision['atomic'], decision['inverse']
        disposition = decision['disposition']
    ledger.append({'passage_id':passage_id,'lesson_number':int(p['unit_id'].split('-')[1]),'document_id':DOC,
                   'pdf_page':p['pdf_page'],'role':p['role'],'speaker':p['speaker'],'published_at':p['published_at'],
                   'source_text_sha256':hashlib.sha256(p['text'].encode()).hexdigest(),'result':disposition,
                   'claim_ids':[r['id'] for r in linked],'pending_issue_ids':related,'reviewer':REVIEWER,
                   'rounds':{'1_read_and_scope':reading,'2_atomic_conditions':atomic,
                             '3_normalization':{'concepts':sorted({x for r in linked for x in r['concepts']}),'existing_claims_in_scope':[], 'decision':'同册同词按实际语境登记；均线/级别和案例/一般规则不合并。'},
                             '4_reverse_check':inverse}})

figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 8 AND 22 ORDER BY pdf_page,id',(DOC,))]
figure_notes = {
    12:'中工日线叠加分时与成交量/MACD、两块黄色文字摘录。只作当日案例，不新增作者规则；制作人未核。',
    15:'两张包钢权证截图行情2007-03-23、Copyright2008，晚于2006-10-24课程，现有later_annotation正确；不改原文底线。',
    16:'包钢正股图横轴延至2007年4月，图头光标2006/05/30不等于全图时点；后加图仍later_annotation。',
    17:'宝钢日线光标2006/11/16、10-23箭头、两矩形、成交量/MACD和黄色正文摘录，图源未核。',
    18:'宝钢日线光标2006/10/23、MA250约4.17与低4.20、两矩形和黄色正文摘录，图源未核。',
    22:'600086月线图头2007/11/30，红摘录20061116及5.97，与正文2006-11-21及5.9不同；不作作者更正，现有later_annotation正确。',
}
for f in figures:
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=figure_notes[f['pdf_page']],origin_status_changed=False,
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])

assert len(passages)==126 and len(ledger)==126
def dump(suffix, data):
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(r,ensure_ascii=False,separators=(',',':')) for r in data)+'\n',encoding='utf-8')
dump('reviewed.jsonl',rows)
dump('coverage.jsonl',ledger)
dump('pending.jsonl',pending)
dump('figures.jsonl',figures)
dump('context-only.jsonl',[{'id':r['id'],'text':r['text'],'evidence':r['evidence'],'disposition':'historical_context_only','reason':'历史行情或非股票技术附文，保留上下文，不送已复核命题导入器。'} for r in context_drafts])
summary={'stage':'C','schema_version':metadata['schema_version'],'graph_version':metadata['graph_version'],'reviewer':REVIEWER,
         'lessons':list(range(1,9)),'document_id':DOC,'passages_read':len(ledger),'claims':len(rows),
         'evidence':sum(len(r['evidence']) for r in rows),'importance_counts':dict(Counter(r['importance_level'] for r in rows)),
         'new_concepts':sorted({x for r in rows for x in r['concepts']}-set(concepts)),
         'whole_lesson_semantic_read_complete':True,'technical_extraction_complete':False,'four_round_review':True,
         'independent_review_claimed':False,'visual_pdf_pages':list(range(8,23)),'figure_objects_viewed':len(figures),
         'pending':[r['id'] for r in pending],'database_mode':'ro','formal_import':False,
         'context_drafts_not_published':len(context_drafts),
         'acceptance':'第1至8课126段四轮审读及15页7图视觉核对完成；数值/附列身份/比例与示例程序边界等待核分别保留，已核命题待预检发布。'}
(OUT/f'{BASE}.summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
db.close()
sys.stdout.reconfigure(encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))
