"""Stage C lessons 72-74. Read-only KB; write only this isolated batch.

The four review rounds were performed by the same GPT-6.1 Sol xhigh agent.
No database import, source repair, old batch modification, or Git action occurs.
"""
import hashlib, json, sqlite3, sys
from collections import Counter, defaultdict
from pathlib import Path
sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding='utf-8')
BASE = Path(__file__).resolve().parent
KB = Path(r'C:\Users\13240\Desktop\RAG\shared-knowledge\v0.1.0')
NAME = 'c_stage_l072_l074_sol61'
DOC = 'volume_2-5332cd1b6038'
PREFIX = DOC + '-'
REVIEWER = 'GPT-6.1 Sol xhigh / 阶段C下册第72—74课四轮复核'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
db.execute('BEGIN')
meta = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
P = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id IN ('lesson-072','lesson-073','lesson-074') ORDER BY pdf_page,block_index")}
existing = {r['id']: dict(r) for r in db.execute('SELECT * FROM claims')}
registry = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
alllabels = set(registry) | {a for r in registry.values() for a in json.loads(r['aliases'])}
old_map, candidate_map = defaultdict(list), defaultdict(list)
for r in db.execute("SELECT cl.id,cl.review_status,e.passage_id FROM claims cl JOIN evidence e ON e.claim_id=cl.id JOIN passages p ON p.id=e.passage_id WHERE p.unit_id IN ('lesson-072','lesson-073','lesson-074')"):
    (old_map if r['review_status'] == 'reviewed' else candidate_map)[r['passage_id']].append(r['id'])
contexts = {}
sections = {}
for p in P.values():
    if '(2007-' in p['text'] and len(p['text']) < 110:
        sections[p['unit_id']] = p['text']
    contexts[p['id']] = sections.get(p['unit_id'], p['unit_id'])
claims, decisions, pending = [], {}, []

def add(lesson, slug, text, concepts, refs, level, reason, conditions=(), exceptions=(), note='', figures=()):
    cid = f'lower-l{lesson:03d}-c-stage-' + slug
    assert cid not in existing and cid not in {c['id'] for c in claims}, cid
    citations = []
    for ref in refs:
        short, quote = ref if isinstance(ref, tuple) else (ref, None)
        p = P[PREFIX + short]
        quote = p['text'] if quote is None else quote
        assert p['speaker'] == '缠中说禅' and p['role'] in ('author_body','author_reply','author_commentary'), cid
        start = p['text'].find(quote)
        assert start >= 0 and p['text'][start:start+len(quote)] == quote, (cid, short)
        citations.append({'passage_id': p['id'], 'quote': quote, 'quote_start': start, 'figure_ids': [PREFIX + f for f in figures]})
    context = ' / '.join(dict.fromkeys(contexts[e['passage_id']] for e in citations))
    scope = '；'.join(conditions) or '本课作者对' + '、'.join(concepts) + '的论述及所列对象'
    record = dict(id=cid, text=text, kind='explicit', conditions=list(conditions), exceptions=list(exceptions), concepts=list(concepts), ambiguity_status='none', review_note=f'语境：{context}。适用条件：{scope}。同一复核者完成四轮：完整阅读与语义拆解、联合条件下的原子化、术语及既有reviewed归一、逐条回原文逆向核验。{note}', reviewer=REVIEWER, importance_level=level, importance_reason=reason+'；等级仅表示整理重要性。', evidence=citations, relations=[])
    if figures:
        record['figure_review_note'] = '已实际渲染并查看volume_2.pdf实际PDF页' + '、'.join(dict.fromkeys(str(int(f[1:5])) for f in figures)) + '对应图，核对作者所指点号、位置、均线或三角形及相邻文字。图像登记origin_status仍为unverified，不声称已溯源作者原图，不仅凭同页位置建立支撑，不从图补造作者未说的规则。'
    claims.append(record)
    return cid

def mark(short, category, reason, old=()):
    assert PREFIX + short in P, short
    decisions[PREFIX + short] = {'category': category, 'reason': reason, 'existing_claim_ids': list(old)}

def hold(lesson, slug, shorts, issue):
    pending.append({'id': f'lower-l{lesson:03d}-c-stage-pending-'+slug, 'lesson_number': lesson, 'document_id': DOC, 'passage_ids': [PREFIX+s for s in shorts], 'status': 'pending', 'issue': issue})

# Rounds 1-2: all lesson prose and appended market commentary were read.
# Lesson 72: retain ten existing reviewed statements; supplement omitted context.
add(72,'fundamentals-industry-fund-route','作者把基本面研究最终归于行业或总体经济发展，并向散户提出购买指数基金或具体行业、板块基金的简便参与路径，认为个人基本面研究能力超过优秀基金团队的可能性很小。',['独立系统','基本面','经济大势','散户'],['p0102-b011','p0103-b000'],3,'保存散户基本面研究与基金参与路径',conditions=['2007年本课对普通散户研究能力与资本积累的讨论'],note='记录作者建议和判断；未将指数基金必不跑输指数的原句扩成已验证的跟踪收益保证，未把原始股时代判断作当前事实。')
add(72,'three-systems-division','作者把技术面、比价关系和基本面作为三个独立系统：后两者可配合决定介入品种，介入品种之后技术面在具体操作上起决定作用。',['独立系统','技术分析','比价关系','基本面','操作策略'],['p0103-b001'],1,'保存三系统名称与选品种/操作的分工',note='“独立”沿用作者体系称谓，不宣称已经证明统计独立。')
add(72,'multiplication-technical-excess-return','作者认为散户要战胜市场、获得超越市场的回报，须在其所称乘法原则下进行技术面操作。',['乘法原则','技术分析','散户'],[('p0103-b001','对于散户来说，最终能战胜市场、获得超越市场的回报的，只有在本ID所说的乘法原则下的技术面操作。')],3,'保留作者对技术面与资本积累的限定观点',conditions=['作者讨论散户超越市场回报的途径','作者所称乘法原则'],note='这是作者的排他性主张，本段没有给出乘法原则公式；未补公式、未承诺实际收益。')
add(72,'system-change-frequency','本课用变化频率说明三系统分工：作者认为基本面和既已确立的比价关系相对稳定，技术面变化更频繁，因此具体操作需要更持续关注技术面。',['独立系统','技术分析','比价关系','基本面'],['p0103-b001'],3,'保存三系统分工的解释依据',note='保留“相对稳定”的原语境，不把基本面变化少说成永无断裂点。')
add(72,'averages-auxiliary-horizons','作者将早期均线系统讲解与其形态学、动力学理论区分；在单边走势的简化观察中，举5日线、5周线、5月线分别作为日线、中线、长线的参考。',['均线','技术分析','操作级别'],['p0103-b003'],2,'保存均线体系身份及不同观察尺度',conditions=['作者针对单边走势给出的简便均线观察','均线系统并非其理论本体'],note='未把周期图名称等同所有操作级别，也未把单根均线当成全行情有效规则。')
add(72,'case-first-bull-month-average','2007年8月本课以5月线未被有效跌破判断当时牛市第一轮未完，并提出第一次跌破后由上移的10月、30月线构成新调整底部、再有大波行情的历史预期。',['均线','牛市阶段','宏观市场判断'],['p0103-b003'],4,'保存当时月均线判断及后续预期',conditions=['2007-08-21作者所述该轮牛市及月均线状态'],note='属于当时判断和预期，未实证核查历史结局，不能当作任意牛市必然重演的定理。')
add(72,'all-points-reduce-first','第72课作者概括所有买卖点归根结底都是第一类买卖点，并以此解释为何实际讲授中提前混入动力学内容。',['第一类买卖点','买卖点','动力学'],[('p0103-b004','而所有买卖点，归根结底都是第一类买卖点，那这样，要把形态学和动力学都说完，才说第一类买卖点，估计所有看的人都会晕倒。')],1,'保存本课对全部买卖点的明确概括',note='比17课仅对第一、第二类的早期表述范围更广；本段没有给各类逐级归结的完整证明，未自行补证明。')
add(72,'morphology-extreme-self-trade-example','作者称形态学本质上是无须其动力学前提的几何，并用单一庄家买下全部、独自反复交易的极端例子说明，仍不能逃出形态学的结构描述。',['形态学','动力学','控盘','市场合力'],['p0103-b006'],3,'补充既有形态学前提命题未保存的极端对象边界',conditions=['作者区分形态学几何描述与动力学前提的理论语境'],note='本段同时说“无须任何前提”，按其后明确限定为不要求价格充分有效与非完全绝对趋同交易两前提；不据此删除输入数据、定义对象等工程前提，也不将极端例子改成动力学适用。')
add(72,'dynamics-geometric-proof-distinction','作者说理论的动力学部分也以几何构造表达，但需要把价格充分有效市场中的非完全绝对趋同交易前提转化为几何结构；当下可理解的走势理论与其复杂证明应区分。',['动力学','形态学','价格充分有效市场','非完全绝对趋同交易','当下'],['p0103-b007','p0104-b000','p0104-b001'],3,'保存动力学几何构造的前提与理论/证明边界',note='物理和费马猜想是作者类比，未作为独立物理结论；本课没有展示所说完整几何证明。')
add(72,'case-morphology-4335-sell','作者用当时日线作形态学卖段示例：若回拉到4335点以下，第一次与回拉同级别、反抽至4335上方且不创新高者为卖点；若始终未回到4335且上方形成新同级中枢，则操作标杆上移至新中枢。',['形态学','买卖段','同级别','中枢新生'],['p0104-b005'],2,'保存买卖段的完整例子及替代分支',conditions=['2007-08-21以去年及当年5月调整同级别为前提的指数日线示例','实际操作须对应具体个股'],note='4335为例子参数；“第一次”、与回拉同级、反抽不创新高三项均保留。')
add(72,'case-morphology-individual-horizon','作者强调指数只是操作示例，实际须看具体个股；同一股票的日线卖段与周线卖段可以处于不同状态，000777的周线在本课时点尚无卖段。',['形态学','买卖段','周期K线图','级别'],['p0104-b005'],3,'保存个股与观察尺度条件',conditions=['2007-08-21以000777日线和周线作比较'],note='没有将未出现周线卖段推广为该股永久持有建议。')
add(72,'combine-morphology-dynamics','作者认为形态学与动力学结合运用更有效；对背驰、区间套尚无信心者可先从形态学着手，但形态分析不好也无法做好动力学分析。',['形态学','动力学','背驰','区间套'],['p0104-b006','p0104-b007'],2,'保存学习次序建议与结合使用要求')
add(72,'recursive-minimal-learning-distinction','作者说实际应用可先从分型、笔、线段构造最小级别入手，不必先解决其与中枢递归定义的区别；但不弄清区别容易造成逻辑混乱，仍应理解。',['递归定义','最小级别中枢','分型','笔','线段'],['p0104-b008'],2,'保存简化入门与逻辑边界',note='未把递归定义和最小级别定义当成同一定义。')
add(72,'morphology-combination-research','本课把结合律相关问题列为后续形态学重点，并提出从其形态学严格推出K线、波浪等形态理论及指出缺陷的研究工作。',['形态学','结合律','K线'],['p0105-b000'],3,'保存明确后续研究方向和作者主张',note='本课只提出工作与可推导主张，未展示推导，不能声称本批已完成对其他理论的证明。')
add(72,'learn-precision-in-stages','作者说明课程采用先给简单方向、再引入复杂概念精确化的教法；暂不能理解精确定义者可先用较简方式，理解与市场认识加深后再学精确内容。',['技术分析','操作熟练程度','标准特征序列'],['p0105-b004','p0105-b005'],3,'保存循序学习与精通要求',note='教学容许不精确入门不等于废止67课精确定义；作者只承诺安排代表性问题回答，未声称能回答所有问题。')
add(72,'react-market-policy-news','面对政策消息，作者要求投资者观察市场实际反应后作反应，按技术边界及自身操作级别处理，不需要先预测、猜测政策效果。',['政策风险','当下','操作级别','边界条件'],['p0105-b007','p0106-b004','p0106-b005','p0106-b010'],2,'保存消息后反应的操作要求',conditions=['2007-08-22加息与组合调控附文'],note='均线为尚未熟悉技术者的辅助观察，不将任何消息自动归为利多或利空。')
add(72,'case-diverse-policy-expectations','在该次加息附文中，作者赞成令市场产生不同预期的调控，认为预期分歧可避免合力一边倒、给市场磨合并自行选择方向的时间。',['政策风险','市场合力','市场分力','市场心理'],['p0106-b002','p0106-b003'],3,'保存作者对政策预期与市场合力的解释',conditions=['2007-08-22本次加息及作者所称组合拳'],note='作者评价当时政策时机与效果，未验证为普遍政策最优定理。')
add(72,'case-three-post-hike-branches','2007年8月22日早盘前，作者按强中弱完整列出加息后的三支：平/高开且不补缺口继续上攻，补缺口后附近震荡等待基本面方向，或跳空向下成岛型反转并至少再考验8—17中枢；强支仍须防新的调控与2/3线共振。',['完全分类','边界条件','缺口','中枢震荡','政策风险'],['p0106-b006','p0106-b007','p0106-b008','p0106-b009','p0106-b010'],2,'保存明确分类的联合条件及各支反应',conditions=['2007-08-22早盘前加息、昨日缺口及8—17中枢语境'],note='历史三支是此场景的划界，不强行套用所有市场开盘。')
add(72,'case-multilevel-unconfirmed-divergence','加息后作者仍将当日日线视为等待最后确认或破坏的背驰段，短线为30分钟中枢震荡、超短线为最后5分钟中枢震荡，要求按各自操作级别选择行动。',['背驰段','完成','操作级别','中枢震荡'],['p0106-b004'],3,'保存不同尺度并存及背驰尚未确认',conditions=['2007-08-22当时技术结构'],note='背驰段成立不等于背驰已经确认。')
add(72,'case-monthly-average-ignore-small-noise','对月线操作者，作者在加息附文中提出以5月线为简化观察，在未有效跌破之前可少管中短波动。',['均线','操作级别','有效跌破'],['p0106-b010'],3,'保存月线操作的简化边界',conditions=['2007-08-22月线操作示例','5月线尚未有效跌破'],note='与既有有效跌破需同尺度反抽的说明配合定位；未声称所有小级别风险消失。')
add(72,'case-triangle-provisional-segment','2007年8月22日向上倾斜三角形案例，特征序列分型未最终完成、尾盘回跌仅成一笔，因此56只是暂标：若次日高开5000之上猛烈上攻且不再跌回5000以下，该线段仍可延续。',['线段','特征序列','分型','完成','三角形整理'],['p0107-b002'],1,'保存暂标与确认的严格区别及未完条件',conditions=['2007-08-22图中56与向上倾斜三角形','第一种线段破坏情况'],figures=['p0107-fig1'],note='没有把“通常已在最高点完成”删掉后续条件，未将暂标当最终分段。')
add(72,'case-triangle-retrace-experience','作者在该例把向上倾斜三角形的特点表述为99%回跌到启动位置，并说当日尾盘满足这一跌幅，但跌幅满足本身并未确认线段完成。',['三角形整理','线段','完成'],['p0107-b002'],3,'保存经验比例与正式完成条件的区别',conditions=['2007-08-22向上倾斜三角形实例'],figures=['p0107-fig1'],note='99%是作者本段经验性说法，本批未做样本统计，不推广成可验证收益概率或任意三角形定理。')
add(72,'case-long-segment-force-conflict','作者把本例1分钟线段异常长的延续视为技术提示，解释为多方反复冲击5000与上方压制共存，尾盘回落后收回一半只说明上攻欲望未被满足。',['线段','市场合力','市场分力','市场心理'],['p0107-b003'],3,'保存形态与分力博弈的作者解释',conditions=['2007-08-22近5000点的长线段案例'],figures=['p0107-fig1'],note='不由形态反推可独立证实的特定主力身份。')
add(72,'case-middle-branch-policy-condition','当日选择补缺口后震荡的中等分支后，作者把短线政策变化视为重要分力：若继续调控则变数增大，若今明两天无特别消息、组合拳猜想暂被搁置，则可上试5000。',['政策风险','市场分力','完全分类'],['p0107-b001','p0107-b004','p0108-b000'],3,'保存政策附加条件下的历史分支',conditions=['2007-08-22已走出早盘分类的第二支','未来两日是否有特别消息'],note='属于当时条件判断，不当作未来两日的承诺。')
add(72,'case-price-line-update','在5089压力线讨论中，作者给2/3线算式1429＋183×30×2/3＝5089，3/4线只替换比例；下月计算时月份数183改为184，3/4线示例为5569。',['经验压力线','边界条件'],['p0109-b004'],3,'保存既有公式的月份更新与比例替换',conditions=['2007-08-23该套时间递增的经验线模型'],note='原文“下月计算时(5569)”按3/4比例与184月相符保留为示例；不把5089固定为永久阻力，不混入其他项目公式。')
add(72,'case-pressure-line-oscillation-scale','作者当时认为比例线突破往往围绕而非触线即返；由于2/3与3/4距离不大，若2/3附近震荡级别较小，则3/4附近一般可能较大，需观察前者的实际发展。',['经验压力线','级别','市场震荡'],['p0109-b004'],3,'保存相邻压力线震荡的条件经验',conditions=['2007-08-23以此前几条比例线突破为经验参照'],note='“一般”保留，不作两条线震荡级别的必然等式。')
add(72,'case-56-revision-59-unconfirmed','2007年8月23日，作者明确前日56的未确认分支实际发生，故须变更暂标；当日59同样未满足100%破坏标准而可变，58及以前满足标准者唯一且不可随意更改。',['线段','线段破坏','完成','当下'],['p0109-b005'],1,'保存完成标准控制标记变更的反例',conditions=['2007-08-22/23图中56、58、59位置'],figures=['p0108-fig1','p0110-fig1'],note='已对照前后两图；变更源于此前未满足定义，不将标准完成后的历史标记任意重画。')
add(72,'case-fund-hot-money-rotation','在本次加息行情中，作者认为银行股受压与二三线低价股活跃并存，基金等正规大资金与游资争夺话语权会和政策一起成为后续震荡分力；其自述持仓一二三线均有。',['板块轮动','主力资金','市场分力','题材股','仓位'],['p0108-b002','p0108-b003','p0108-b004','p0108-b005'],3,'保存当时热点和资金结构分析',conditions=['2007-08-22加息后银行、地产与二三线股的历史语境'],note='低价较低购买门槛是原文解释，未扩为低价等于低估，未将作者持仓结构作统一配比。')
add(72,'case-third-tier-climax-observation','作者在2007年8月23日按中国市场经验认为三线股参与是行情完整和高潮的重要表现，并用大众参与倾向解释其热度。',['板块轮动','牛市阶段','市场心理'],['p0109-b001','p0109-b002'],4,'保留作者具有地域和经验边界的行情观察',conditions=['作者所见中国特色市场及2007-08-23行情'],note='原文称自己未见过无三线高潮，未当成全球市场经过统计证明的必要条件。')
add(72,'case-daily-stock-three-classes','作者将当时个股日线分三类：已突破530高位、未破530高位但已破其后第一反弹高位、连第一反弹高位也未破；分别关注突破回抽后的假突破风险、突破530后的洗盘，以及新资金进场后的吸货风格，判断后者重点看第一次放量后回抽位置。',['完全分类','突破','假突破','放量突破','板块轮动'],['p0109-b006','p0109-b007'],2,'保存个股三分类及各支风险和观察对象',conditions=['2007-08-23以530及其后第一反弹高位为历史基准'],note='“一般”与新资金可能打压/高举高打两支均保留，未断定每只股票唯一资金意图。')
add(72,'third-tier-to-first-two-routes','在三线股变一线股的讨论中，作者说只有两条路线：企业自身成长为中字头乃至世界级公司，或由这类公司全面介入；相应持有需要更长时间和耐心。',['成长性','长期投资','板块轮动'],['p0109-b008','p0110-b000'],3,'保存选股成长路线与长期持有语境',conditions=['2007-08-23作者对未来一线企业的判断'],note='“只有两个途径”为作者在本段的概括，不保证具体三线股成功转型。')

# Lesson 73: classify opportunities, preserve multilevel and capital-size limits.
add(73,'two-profit-opportunities','作者把其理论下任何市场的获利机会归为中枢上移和中枢震荡两种模式。',['走势中枢','中枢上移','中枢震荡','买卖点'],['p0110-b002','p0110-b003'],1,'保存本课核心绝对分类',note='这是作者理论内的分类；未将任一实际交易或任意资金规模都保证获利。')
add(73,'same-level-opportunity-types','站在走势类型同级别看，中枢上移对应该级别上涨走势；中枢震荡可能是该级别盘整，或上涨中形成新中枢后的延续过程。',['中枢上移','中枢震荡','同级别','上涨','盘整'],['p0110-b003'],1,'保存分类与走势类型的同级别对应',conditions=['从走势类型同级别视角分析'],note='未把上涨中的新中枢震荡一概归为独立盘整走势。')
add(73,'oscillation-rebuy-third-buy-boundary','在操作级别中枢震荡向上离开段的卖点区域卖出后，作者断言必然有机会在后续震荡回补；必须识别第三类买点并回补，否则可能错过新中枢上移。第三买点后也可能进入更大中枢震荡，作者称该支回补机会仍是绝对的。',['中枢震荡','中枢上移','第三类买点','操作级别'],['p0110-b004'],1,'保存短差回补的前提、第三买点及两支后续',conditions=['自己的操作级别','确为中枢震荡','在向上离开段的卖点区域卖出','须正确识别第三类买点'],note='原文“必然/绝对”限于作者所设结构条件，未承诺操作不熟练者能原价回补。原段关于本级中枢上移中无短差由既有71课命题覆盖。')
add(73,'short-difference-recognition-prerequisites','短差前须分清中枢、级别、中枢上移与中枢震荡，并识别第三类买点；不具备这些条件而偶尔买回，并不说明已经掌握该方法。',['中枢震荡','中枢上移','级别','第三类买点','操作熟练程度'],['p0110-b005','p0111-b000'],2,'保存短差方法的技术前提')
add(73,'horizontal-vertical-level-views','作者把同一级别分析比作横切面，把不同级别纵向比较作为另一观察视野；较小级别上涨可能只是大级别中枢震荡中的一段。',['级别','同级别','上涨','中枢震荡'],['p0111-b001','p0111-b002'],2,'保存多级别观察与局部上涨的关系',note='月线与年线是本课例子，不把所有小级别上涨强行归入某一大级别震荡。')
add(73,'year-center-return-departure','本课以月线上涨处于年中枢震荡为例：从年中枢下方向中枢回拉时，中枢位置构成待消化阻力；在年中枢上方离开时，中枢具有反拉作用。',['级别','走势中枢','中枢震荡','上涨'],['p0111-b002'],2,'保存大中枢对不同位置上涨的作用分支',conditions=['例示月线上涨是年中枢震荡一段','分别从年中枢下方回拉或上方离开'],note='未由“反拉”补出固定幅度和强制回到中枢的期限。')
add(73,'long-term-center-upshift-horizon','作者将抓住年中枢上移称为人生尺度最大的长线机会，但指出该过程可能跨越数代；对多数人的现实长线投资，季线乃至月线中枢上移已是很大的单品种机会。',['中枢上移','长期投资','级别'],['p0111-b003','p0111-b004','p0111-b005'],3,'保存长线机会与人的时间尺度限制',note='100年、N代人是原文尺度说明；未当作每次年中枢震荡的固定持续年限，关于当时美股状态未另作当前事实。')
add(73,'company-industry-scale-limit','作者说季中枢上移可能对应十年甚至更长的月线上涨，企业规模仍有行业相关极限；挑选这类长线机会应考察哪些企业有能力向所属行业极限成长。',['中枢上移','长期投资','成长性','基本面'],['p0111-b006'],3,'保存长期技术机会与企业成长空间的连接',conditions=['寻找季线/月线大级别长线机会'],note='“可能”保留，未把十年设为季中枢上移的确定时长。')
add(73,'case-china-industry-leaders','2007年作者判断几乎每个行业都至少会有一家中国上市公司冲击全球行业理论极限，以此解释当时中国资本市场的长线魅力。',['成长性','基本面','经济大势','行业龙头'],['p0111-b007'],4,'保存明确量词和历史宏观判断',conditions=['2007-08-23作者对中国企业全球化前景的判断'],note='“几乎”“至少一个”保留，未当成每个行业无例外的已验证未来事实。')
add(73,'exclude-limited-industry-unless-transform','寻找大级别长线机会时，作者建议筛除空间有限、注定无季线乃至月线以上中枢上移的行业；企业转型是明确例外。基本面与世界经济判断须对应具体级别、类型的获利机会。',['基本面','成长性','中枢上移','级别','经济大势'],['p0111-b008'],2,'保存长线行业筛选及转型例外',conditions=['目标为季线/月线及以上中枢上移的长线机会'],exceptions=['相应企业转型'],note='没有否认这些行业仍存在某级别中枢震荡机会，也未自定具体排除行业名单。')
add(73,'winner-current-or-future-leader','作者论述长线最终强势股票与强企业对应，但无法预知最终胜者；在设定胜者达到巨大市值的前提下，其必是当下龙头或未来超越当下龙头的企业。',['长期投资','行业龙头','成长性','比价关系'],['p0111-b009','p0111-b010','p0112-b000'],3,'保存投资方案依据的条件论证',conditions=['作者给定未来行业胜者成长及大市值的假设'],note='10万亿元为假设例子，非具体公司目标价；这是作者明确推论故kind为explicit，不冒充整理者证明。')
add(73,'large-capital-leader-growth-allocation','对大资金的行业长线组合，作者建议最大比例放龙头、其余分配给最有成长性的少数企业，举70%与30%、两家龙头和两三家成长企业为例；龙头若基本面显示必然败落则选最佳替代者。',['长期投资','行业龙头','成长性','仓位','资金管理'],['p0112-b001','p0112-b007'],2,'保存组合结构和基本面替代条件',conditions=['本课面向大资金的行业组合方案'],exceptions=['龙头基本面显示必然败落，应选择最好的替代者'],note='70/30及企业数是“例如/可能”，未设为普遍固定配比。')
add(73,'allocation-stable-rank-change-swap','行业企业排序不变时保持投资比例；基本面显示明显行业地位变化时按等市值换股。技术把握好时，可在被超越企业的大级别卖点卖出，再在后续买点介入新龙头或成长企业。',['行业龙头','比价关系','基本面','买卖点','资金管理'],['p0112-b002'],2,'保存组合调整触发与等市值原则',conditions=['上述行业长线组合','基本面出现明显行业地位改变迹象才触发替换'],note='技术优化有能力前提，未改成等股数换股或任意频繁换仓。')
add(73,'oscillation-lower-cost-build-chips','在该长期组合中，作者要求利用可操作的中枢震荡（如日线、周线）降低至零投资成本并增加持有筹码；增加的筹码也可来自新的成长或低估公司。',['中枢震荡','成本','长期投资','成长性','操作策略'],['p0112-b003'],2,'保存长期组合与技术降成本的结合',conditions=['本课大资金长线行业组合','操作者能处理相应可操作级别震荡'],note='这是作者策略目标，未保证所有投资者能达到零成本；相比既有65课新增组合内可更换筹码对象。')
add(73,'relative-value-industry-position','本课组合中的比价关系指市值与行业地位之间的关系，应持续由此寻找低估品种。',['比价关系','行业龙头','基本面'],['p0112-b004'],2,'保存本课比价关系的特定含义',conditions=['本课行业龙头/成长企业长线方案'],note='不把跨市场同股比价等其他比价概念并为同一无条件公式。')
add(73,'zero-cost-investment-meaning','作者在本课长期投资方案中强调，投资必须做到0成本才真正有意义。',['成本','长期投资','操作策略'],['p0112-b005'],3,'保存作者对降成本的强措辞与策略身份',conditions=['第73课长线组合及中枢震荡降成本方案'],note='保留作者价值判断；未等同于净值无风险、没有机会成本或本项目证明0成本普遍可达。')
add(73,'three-system-investment-combination','作者将本课的长线行业组合、行业地位与市值比价、技术中枢震荡降成本合称基本面、比价关系、技术面三个独立系统的组合。',['独立系统','基本面','比价关系','技术分析','长期投资'],['p0112-b001','p0112-b002','p0112-b003','p0112-b004','p0112-b006'],2,'保存三个系统在同一方案中的具体作用',conditions=['第73课给定的行业长线投资策略'],note='只连接作者明确组合，未自建三系统打分模型。')
add(73,'small-capital-simplify-scale','小资金可按长线组合的简略版只跟踪龙头或最有成长性的一家；原始资本积累阶段作者认为小级别操作更快，但资金达到一定规模后小级别意义减弱。',['资金管理','操作级别','行业龙头','成长性','散户'],['p0112-b007','p0112-b008'],2,'保存资金规模与策略简化/级别选择',conditions=['区分原始资本积累小资金与达到一定规模后的资金'],note='没有给出资金规模数值阈值，不补杠杆或换手公式。')
add(73,'policy-weekly-fluctuation-author-scope','在本课年、季、月级别长线方案的语境中，作者把政策影响概括为最多周线级别震荡，并将其视为技术降成本、增筹码机会，认为未改变所举美股年线中枢移动。',['政策风险','级别','中枢震荡','长期投资'],['p0112-b009'],3,'保存作者政策作用尺度的原句与语境',conditions=['第73课超大级别长线投资讨论','作者以1929年和二战未改美股年中枢移动为类比'],note='“最多周线”是作者此段的强断言，本批未独立证实；与74课“中短期、时间不少”的说法并列保留，不据此保证任一政策调整都小于周线。')
add(73,'case-pressure-line-week-confirmation','2007年8月24日，作者把站稳5089的2/3线作为继续上攻3/4线的前提，并认为这类突破一般至少需周线确认，不能以当日刚突破代替站稳。',['经验压力线','确认','级别','突破'],['p0112-b011','p0112-b012'],3,'保存突破与周线站稳确认的区别',conditions=['2007-08-24该5089比例压力线及下周月线收盘环境'],note='“一般至少”保留，为经验线分析而非中枢定义。')
add(73,'case-retest-can-follow-first-rise','在2007年8月27日5089回抽案例中，作者说一天回抽难以完成确认，后续可以先上攻，再以周线等形式进行回抽确认；具体路径仍须看图反应。',['经验压力线','反抽','确认','当下'],['p0114-b005'],3,'保存先上攻后大尺度确认的允许路径',conditions=['2007-08-27所述5089回抽'],note='没有把所有回抽确认都硬定为当日完成或一概必须先涨。')
add(73,'case-fund-hot-money-funding-difference','作者在该次资金分歧附文中，把基金可持续吸收新增申购资金与游资需在具体股票寻找接盘资金相比较，并认为二者视野、选股与博弈不同。',['主力资金','市场分力','资金食物链','题材股'],['p0113-b003','p0113-b004','p0114-b003'],3,'保存资金来源差异对市场博弈的解释',conditions=['2007-08-27作者所描述基金与游资环境'],note='作者尖锐评价作为当时观点，不替其验证基金永有新增资金或全部成熟市场的绝对分类。')
add(73,'case-52-55-third-buy-uptrend','作者对2007年8月27日图明确标出52—55为1分钟中枢、55—58为线段离开、58—59回抽不跌回而成1分钟第三类买点；其后两支是更大级别中枢或中枢继续上移至新1分钟中枢，本例选择后者，60—63只暂作新中枢。',['第三类买点','中枢上移','中枢扩展','最小级别中枢','完成'],['p0114-b006'],1,'保存底层离开对象及第三买点后完整分支',conditions=['2007-08-27该图49以来走势和52—55等点号'],figures=['p0114-fig1'],note='“线段离开”按作者原文保留，不将它静默改成一般次级别走势；60—63暂定、上涨何时结束留作作业由74课作者后文明确解释。')
add(73,'case-average-entanglement-before-run','作者在600139等例子中强调均线系统先粘合，再出现单边拉升；以600139的a＋A＋b调整后一吻高潮及中铝7月20日前后为例说明。',['均线','结合律','走势','技术分析'],['p0115-b000'],2,'保存作者均线粘合条件和具体例子',conditions=['2007-08-27均线系统讲解及所列股票案例'],figures=['p0115-fig1','p0115-fig2','p0116-fig1'],note='已看图内a/A/b、均线与7月20日箭头；“没有粘合怎么可能单边拉升”限作者均线系统语境，未据图新增买点规则。')
add(73,'technical-chart-reflects-final-actions','作者在个股答疑中强调，不管哪方采取什么行动，最终都在技术图表上显现，技术掌握需要自己实际练习，不能由别人代为实践。',['技术分析','市场合力','操作熟练程度'],['p0116-b000'],2,'保存合力结果观察与实践要求',conditions=['2007-08-27个股洗盘与均线实践讨论'],note='未把作者声称别人洗自己筹码当作可独立证实的资金身份。')
add(73,'case-fund-feedback-bubble-policy','在2007年8月27日晚的泡沫判断中，作者认为基金资金正循环可让泡沫维持相当长时间而不自行破裂，把当时刺破风险归于政策；并列政策认为问题不大与暴风雨前安静两支，认为出台时点无法预测。',['政策风险','主力资金','市场风险','市场合力'],['p0116-b004','p0116-b005','p0116-b006','p0117-b002'],3,'保存历史泡沫机制与政策不确定性的完整限定',conditions=['2007-08-27中国市场及作者的超GDP泡沫框架'],note='“只有政策”是作者当时判断，不推广为任何泡沫都只能由政策刺破。')
add(73,'case-bubble-no-strategic-addition','作者自述当时超GDP后不再买入、只持有并将可用资金转往其他领域，理由是泡沫破裂中的非系统风险不在任何人的控制下。',['政策风险','市场风险','仓位','资金管理'],['p0117-b000'],3,'保存只持有策略的非系统风险理由',conditions=['2007-08-27作者所认定的超GDP泡沫行情'],note='与71课战略持有来源相呼应，新增具体非系统风险理由；不当作所有市场时点的禁买规则。')
add(73,'case-bears-switch-risk-sentiment','在当时行情中，作者把此前长期唱空者开始转向视为风险积聚的心理信号，并对过热资金循环保持警觉。',['市场心理','市场风险'],['p0117-b001','p0117-b003','p0117-b004'],4,'保存历史情绪指标的观察身份',conditions=['2007-08-27作者所见死空头开始转向'],note='未当作只要空头转多就必定见顶的信号。')

# Lesson 74: preserve nine defenses, author views, and appended technical cases.
add(74,'policy-risk-unpredictable-defense','作者把政策性风险归为非系统风险，认为本质上不可准确预测，只能进行有效的相应防范。',['政策风险','市场风险','走势预测','操作策略'],['p0117-b006'],1,'保存风险类型与防范/预测边界',note='沿用作者的“非系统风险”术语，不擅自替换成现代金融分类的外部定义。')
add(74,'case-policy-environment-long-lived','在2007年中国资本市场的发展阶段判断中，作者认为政策风险会长期存在，监管与调控至少同等重要，特定时期调控可能成为最重要方向。',['政策风险','经济大势','宏观市场判断'],['p0117-b007'],3,'保存政策环境判断的历史条件',conditions=['2007-08-28作者对当时中国资本市场发展阶段的判断'],note='不是对当前政策环境的事实更新。')
add(74,'hard-soft-policy-distinction','作者将调控分硬、软两类：社论、讲话、严查等属本段所称硬调控；软调控不以资本价格为最直接目标，结合更大方面且有温和、连续特征。',['政策风险','硬调控','软调控'],['p0117-b008'],2,'保存作者对两类调控的定义边界',note='不按外部政策术语重新分类，也未保证硬调控不再发生。')
add(74,'soft-failure-hard-control','作者提出，若软调控不得力且市场疯狂足以毁掉市场，硬调控可能成为不得已的唯一选择。',['政策风险','硬调控','软调控','市场风险'],['p0117-b009'],3,'保存硬调控出现的联合前提',conditions=['软调控不得力','市场疯狂足以毁掉市场'],note='原文为条件论述，不倒推每次硬调控都证明市场将毁灭。')
add(74,'policy-not-upside-only','作者反对调控只针对上涨的看法，以1994年325点三大政策缺口为针对过度下跌的案例；下跌调控有失败不等于不存在。',['政策风险','下跌','缺口'],['p0117-b010'],3,'保存上涨/下跌调控的区分',conditions=['本课以历史调控说明政策可以作用两个方向'],note='历史政策与成功评价为作者叙述，未开展外部历史实证。')
add(74,'avoid-abstract-policy-conspiracy','作者反对把调控者、机构、散户直接抽象成统一好坏阵营，强调应看到具体实体；并认为政策是在体制均衡中形成，不能简化成某个人任意决定。',['政策风险','市场分力','散户','主力资金'],['p0117-b011','p0117-b012'],3,'保存政策与参与者分析的具体对象要求',note='记录作者对抽象阴谋叙事的批评，不替其断言每一历史政策程序已被本项目调查。')
add(74,'policy-force-middle-long-boundary','作者将政策视为合力中的分力，称其只有中短期力量、没有长期力量，不能单独改变长期趋势；同时又说好政策可促进或延长历史发展进程。所举当时硬调控可使中短期转折，却不能改变大牛市最终方向。',['政策风险','市场分力','市场合力','经济大势','级别'],['p0118-b000'],2,'保存政策单独作用与长期趋势的作者界限',conditions=['第74课作者对政策中短期和长期作用的框架','当时中国经济历史发展阶段'],note='“不能单独”“没有长期力量”与促进/延长进程的原措辞并列保留，不替作者消除语义张力；不与73课“最多周线”静默合并成严格量化定理。')
add(74,'policy-force-bounded-state-dependent','政策分力的作用时间、能量均非无限且有边界；越界会产生新政策和新分力，同一政策在不同市场状态下的实际作用也会变化。',['政策风险','市场分力','边界条件','市场合力'],['p0118-b001'],2,'保存政策作用的边界与状态依赖',note='5000与1000是说明状态不同的例数，不构造政策弹性公式。')
add(74,'valuation-policy-direction','作者要求低估市场更注意向多政策影响，泡沫市场更注意向空调控影响，判断与价格和价值关系相联系。',['政策风险','比价关系','基本面','市场风险'],['p0118-b003'],2,'保存估值状态决定政策警觉方向',conditions=['区分市场低估阶段与泡沫阶段'],note='没有给定低估/泡沫的通用数值阈值。')
add(74,'company-value-defense-bottom-line','作者称有长线价值的个股是抵御一切中短分力的最终基础，以企业质量与成长性作为底线；只有该底线不被破坏时，中短波动才可视为长期介入买点的来源。',['基本面','成长性','长期投资','买点','市场分力'],['p0118-b004'],2,'保存长期持有的基本面必要条件',conditions=['个股有长线价值','对应企业质量与成长性底线未被破坏'],note='“一切”保留为作者在该框架中的断言，未把任何下跌都称为买点，也未承诺有成长性就不会亏损。')
add(74,'no-borrowing-position-control','本课防范政策风险的仓位要求明确反对借贷炒股，认为不应把资本市场当赌场。',['仓位','资金管理','政策风险'],[('p0118-b005','三、注意仓位的控制。现在透支已经不流行，但借贷炒股还是不少见。这是绝对不允许的，把资本市场当赌场的，永远也入不了资本市场的门。')],2,'保存借贷与仓位的明确限制',note='“绝对不允许”是作者策略立场，不伪装成当前法律禁令。')
add(74,'bubble-hold-no-strategic-buy','作者在进入泡沫化阶段后要求只战略性持有、不再战略性买入，以留出对中短波动反应的区间。',['仓位','政策风险','市场风险','资金管理'],[('p0118-b005','在进入泡沫化阶段后，应该坚持只战略性持有，不再战略性买入的根本原则，这样，任何的中短波动，都有足够的区间去反应。')],2,'保存泡沫阶段的仓位策略及反应目的',conditions=['作者判定已进入泡沫化阶段'],note='“战略性”保留，不等同禁止以原持仓做任何短差回补；与71课相同策略并保留本课防险目的。')
add(74,'zero-cost-safety-author-strong-wording','第74课作者以“只有成本为0才安全”的强措辞要求良好操作习惯，并称这大概是彻底逃避市场风险的唯一办法。',['成本','市场风险','操作策略'],['p0118-b006'],3,'保存作者强措辞及“大概”限定',conditions=['第74课政策风险防范中的降低持仓成本要求'],note='与67课“相对安全”、73课“真正有意义”分别记录；这是作者策略主张，未解释成价格不会归零、零成本持仓无经济风险或数学无风险保证。')
add(74,'position-reserves-low-cost-psychology','作者把贪婪与恐惧同列失败因素；若仓位适当、有足够应对资金且成本低，可对政策警觉而不必天天惊恐。',['市场心理','仓位','成本','资金管理','政策风险'],['p0118-b007'],2,'保存三项准备的联合条件',conditions=['保持好的仓位','有足够应对资金','低成本'],note='不因心理放松建议而删除资金和成本前提。')
add(74,'large-funds-preknowledge-no-full-exit','本课认为不能企望所有人都提前一天逃开硬调控；作者说当时政策保密效率提高，即便少数大资金提前知道，可反应时间也不足以全部兑现。',['政策风险','硬调控','资金管理','市场风险'],['p0118-b008'],3,'保存先知与可执行退出的区别',conditions=['2007-08-28作者所述政策保密环境','资金较大且时间窗口很短'],note='未验证当时内部消息事实，未声称永远无人提前知晓。')
add(74,'hedge-preparation-historical-warrants','作者将必要的对冲准备列入政策风险防范，并举当时权证、认沽需求为对冲预期的例子。',['政策风险','对冲','资金管理'],['p0118-b009'],3,'保存九项防范中的对冲准备',conditions=['2007-08-28当时可用权证工具的例示'],note='只记录历史工具例子，不把当时权证产品或当前可交易性当成当前事实，不补合约或比例。')
add(74,'hard-control-exit-opportunities','本课要求一旦硬调控出现，在一切可能的机会退出；作者依据历史经验说，即使后续调整空间不大，调整时间也不会少。',['政策风险','硬调控','操作策略','市场风险'],['p0118-b010'],2,'保存触发后反应与空间/时间区别',conditions=['硬调控已经出现','存在可执行退出机会'],note='不补硬调控提前预知条件；与73课最多周线的概括保留各自语境，不替作者给持续时间上限。')
add(74,'profits-buffer-nonsystem-risk','作者强调上涨阶段先积累足够利润，再留出一定幅度承受不可预测的非系统风险；举已获N平方倍后留10%—20%为例，认为最终赢家与是否早一天逃离无必然关系，关键是反应。',['市场风险','政策风险','成本','资金管理','当下'],['p0118-b011','p0119-b000'],2,'保存利润缓冲与反应优先的方法',conditions=['已在上涨阶段取得足够利润','作者N平方倍获利的举例前提'],note='10%—20%为例示容忍幅度，原文未明确百分比的计算分母；未设成所有仓位的统一止损比例。')
add(74,'case-one-minute-trend-end-divergence','2007年8月28日作者明确回答：49起已为标准1分钟上涨，其结束信号是背驰；当下须定位背驰段、再观察是否最终形成背驰，不能将背驰段预先当成已确认背驰。',['背驰','背驰段','上涨','完成','级别'],['p0119-b002'],1,'保存作者对前课留题的明确答案及未确认状态',conditions=['2007-08-28图中49起的标准1分钟上涨'],figures=['p0114-fig1','p0121-fig1'],note='直接依据作者本段回答73课p114-b006所留结束信号作业；未由整理者自行代答。')
add(74,'case-third-buy-larger-divergence-watch','在该1分钟中枢震荡中，作者先看有无第三类买点带来新上攻；本级背驰若发生，是否引发更大级别背驰段精确定位仍是后续待观察问题。',['第三类买点','中枢震荡','背驰','背驰段','级别'],['p0119-b002'],2,'保存第三买点与更大背驰的不同条件时序',conditions=['2007-08-28当前1分钟中枢与49起上涨案例'],note='没有把1分钟背驰必然等同更大级别背驰，也未声称当时已形成。')
add(74,'case-ah-valuation-feedback','作者在2007年8月28日赞成所述A股与H股、红筹相互带动的比价思路：A股高估值给后者上涨空间，后者上涨又被用作A股上涨理由。',['比价关系','市场分力','跨市场交易价值'],[('p0119-b004','第三、H股、红筹与A股对做，这样两头促进，两头赢，A股估值高，使得H股、红筹有空间，而后者一涨，前者又有了涨的理由。（当然，这点本ID是同意的，也是乐意，否则本ID为什么要钟情于中字头，今天，最懒之一的中字头中国人寿也动起来，本ID还是比较满意的。）；')],3,'保存作者明确认可的历史跨市场反馈思路',conditions=['2007-08-28基金与政策博弈的特定历史判断'],note='相邻其他理由是作者转述某些资金看法，未直接归为作者认可；“两头赢”不当作已证明无风险套利。')
add(74,'case-policy-game-two-exits','本次市场与政策博弈的附文中，作者列两种结局：市场因外部等因素主动回落而不触及底线，或继续加剧并最终触及底线、引出强硬反应；同时认为软调控无力与硬调控后果使管理层两难。',['政策风险','硬调控','软调控','市场合力','完全分类'],['p0119-b005','p0119-b006','p0119-b007','p0119-b008'],3,'保存历史博弈的两支和政策条件',conditions=['2007-08-28作者所述市场与政策博弈局面'],note='美国第二波冲击是第一支例子，不当作必发生事件。')
add(74,'case-trading-cost-policy-damage','作者认为该轮政策博弈已使全市场交易成本显著增加，即使指数后来回升也不能抵消持续成本负担，市场结构受损最终会转嫁给参与者。',['交易成本','政策风险','市场风险'],['p0119-b009','p0119-b010','p0120-b001'],3,'保存政策风险中的持续交易成本影响',conditions=['2007-08-28所述印花税及政策博弈背景'],note='不把当时税率、提案可行性或作者共业措辞当成当前法规。')
add(74,'case-two-thirds-acceptable-fast-trap','作者在当时表态可接受围绕2/3线的活动，反对快速抛离3/4线、直接冲击6000制造多头陷阱，并把这与避免激化政策风险联系。',['经验压力线','市场风险','政策风险','突破'],['p0120-b005','p0120-b011'],4,'保存个人市场偏好及对应风险情景',conditions=['2007-08-28/29作者所述比例线与当时政策环境'],note='是历史偏好和假设风险场景，不从其表态推导市场必遵从或一般固定涨幅上限。')
add(74,'case-new-five-center-basically-formed','2007年8月29日作者说从62开始的新5分钟中枢已基本成型，其后续走势决定短线发展。',['走势中枢','级别','完成','中枢震荡'],['p0120-b010'],3,'保存新中枢形成状态的精确措辞',conditions=['2007-08-29图中62开始的5分钟中枢'],figures=['p0121-fig1'],note='保留“基本成型”，没有升级为后续已完全确认。')
add(74,'case-62-63-second-destruction','作者将2007年8月29日下图中的62—63明确列为线段分段第二种情况的典型例子，要求结合图研究。',['线段破坏','线段','特征序列'],['p0120-b016'],2,'保存明确图例与第二种情况的对应',conditions=['2007-08-29附图62—63线段'],figures=['p0121-fig1'],note='已实际查看PDF121页顶部图，位于75课标题前，与120页“下图”明确跨页对应；未自行补未写出的分笔答案。')

# Specific exclusions, unresolved proof/origin boundaries, and prior knowledge.
hold(72,'figure-origins',['p0107-b002','p0109-b005'],'已渲染并实际查看p107、108、110三个图对象；原博客版本和制作者身份未独立溯源，数据库unverified保持。p107图内嵌有正文引述，不自动算作新增独立作者证据。')
hold(73,'figure-origins',['p0114-b006','p0115-b000'],'已实际查看p114、p115两图及p116四个图对象。600139图内a/A/b及两图“一吻”批注制作身份未核；不能因与正文匹配把图源认定作者原图。')
hold(74,'figure-origin-cross-page',['p0120-b016'],'第74课“下图”实际在PDF121页75课标题前；跨页语义对应已核，原博客制作来源仍unverified。仅保存作者明确62—63第二种情况，不自行细化其分笔确认过程。')
hold(72,'unshown-geometric-proofs',['p0104-b000','p0104-b001','p0105-b000'],'作者主张动力学前提可转为几何并构造证明，及K线/波浪形态理论可从其形态学推出；本课未展示完整证明或推导，保存为作者主张及后续工作，不补证明。')
hold(73,'policy-timescale-boundary',['p0112-b009'],'73课“政策最多周线级别震荡”在超大级别长线策略语境中出现，74课另说政策可改中短期且硬调控后调整时间不少。已分别保存；未给统一形式时标，不能据此从几何定义证明全部政策作用的严格周线上限。')

for shorts, cat, reason in [
 (['p0102-b008','p0105-b006','p0107-b000','p0109-b000','p0110-b001','p0112-b010','p0113-b002','p0116-b001','p0117-b005','p0119-b001','p0120-b006'],'transition','课程/附文标题及日期，确认来源语境，不单独形成技术命题。'),
 (['p0102-b009','p0102-b010','p0103-b002'],'autobiography_or_rhetoric','个人写作缘起、经历及自我评价，不另造技术规则。'),
 (['p0103-b005'],'historical_case_or_background','000999买入价格与学费比喻是历史个人教学例子；边学边实践可自选，不推广个股获利承诺。'),
 (['p0104-b002','p0104-b009','p0104-b011'],'existing_repeat_or_transition','课程编排说明与形态学学习路线引入；路线已有reviewed，强调基本要素不可再简省。'),
 (['p0105-b008','p0106-b000','p0106-b001'],'historical_policy_evaluation','当次加息、利差与调控时机的个人评价；政策预期分歧的技术解释已另抽取，不当当前制度事实。'),
 (['p0106-b011'],'historical_case_or_background','当时美国市场后续被列重要分力，属特定宏观观察；无额外独立几何操作规则。'),
 (['p0108-b001'],'existing_repeat','5089的2/3压力线与此前1/2磨合已有69、71课reviewed；本批另保存月份更新和震荡级别比较。'),
 (['p0109-b003'],'rhetoric','关于5000点的修辞和既往预测自评，不另造预测成果。'),
 (['p0112-b013'],'historical_case_or_background','当时基金、游资热点冲突的简短评论；机制由本课后附资金来源解释补全。'),
 (['p0113-b000','p0113-b001'],'historical_case_or_background','所列个股龙头身份、原买价、当前涨幅与个人持股自述保留原文；未外部验证企业排名，不将目标价或零成本自评推广成收益保证。'),
 (['p0113-b005','p0114-b000','p0114-b001','p0114-b002','p0114-b004'],'historical_market_opinion','当时蓝筹/垃圾资金阵营与市场演化的作者评论；已有资金来源/博弈解释承载技术意义，不把修辞、口号或8228/2882隐喻补成可执行信号。'),
 (['p0116-b002'],'transition','引入当晚泡沫风险附文，未新增具体技术规则。'),
 (['p0116-b003'],'existing_repeat','超GDP泡沫化框架已有68、71课reviewed，本次保存基金正循环与政策破裂机制补充。'),
 (['p0118-b002'],'transition','引入九项防范，不另作抽象命题。'),
 (['p0119-b003'],'historical_case_or_background','后进资金与政策博弈的引入；具体已认可的A/H比价与结局分类另抽取。'),
 (['p0119-b011','p0120-b000'],'existing_local_case','此前死空头涨后转多的风险观察与73课附文重复，保留历史来源。'),
 (['p0120-b002','p0120-b003','p0120-b004'],'personal_action_or_background','作者个人出手能力、意向与权利表态，不据此造市场服从作者的规则。'),
 (['p0120-b007','p0120-b008','p0120-b009'],'historical_case_or_background','当日美股下跌、漂亮50休整与其他股活跃是市场过程描述；不以巧合验证预测命中。'),
 (['p0120-b012','p0120-b013'],'historical_comparison_or_forecast','1996深成指速度比较及6000/10000/30000远景判断保留原文背景，不认定未给期限的目标为已验证必达价格。'),
 (['p0120-b014','p0120-b015'],'market_psychology_or_rhetoric','个人救市努力和市场愿望、贪婪的修辞；合力与风险心理内容已保存，不另造不可定位操作法。'),
]:
    for s in shorts: mark(s, cat, reason)

# Round 3: exact earlier reviewed identities, no implicit replacement.
cross = {
 'p0103-b001':['upper-l019-analysis-system'],
 'p0103-b003':['lower-l066-simple-average-indicator-context'],
 'p0103-b004':['lower-l072-morphology-dynamics','upper-l017-c-stage-first-second-reduce-to-first'],
 'p0103-b006':['lower-l072-morphology-geometric-scope','lower-l072-dynamics-premises'],
 'p0104-b003':['lower-l072-dynamics-energy-and-divergence'],
 'p0104-b004':['lower-l072-morphology-second-not-first','lower-l072-morphology-operation-segment'],
 'p0104-b010':['lower-l072-morphology-learning-chain'],
 'p0105-b001':['lower-l072-center-makes-types-strict'],
 'p0105-b002':['lower-l072-l067-explicit-refinement'],
 'p0105-b003':['lower-l072-feature-sequence-removes-small-to-large'],
 'p0106-b010':['lower-l067-moving-average-effective-break'],
 'p0108-b001':['lower-l069-c-stage-case-pressure-two-thirds','lower-l071-c-stage-case-pressure-experience-not-prior'],
 'p0109-b005':['lower-l070-c-stage-case-46-provisional'],
 'p0110-b004':['lower-l071-c-stage-trend-vs-center-difference'],
 'p0112-b003':['lower-l065-zero-cost-add-shares-author-strategy'],
 'p0116-b003':['lower-l068-c-stage-case-gdp-bubble','lower-l071-c-stage-case-gdp-dynamic-analogy'],
 'p0117-b000':['lower-l071-c-stage-case-strategic-hold-to-sell'],
 'p0118-b005':['lower-l071-c-stage-case-strategic-hold-to-sell'],
 'p0118-b006':['lower-l067-buy-point-relative-zero-cost-safety'],
}
for short, ids in cross.items():
    ids = [cid for cid in ids if cid in existing and existing[cid]['review_status']=='reviewed']
    if PREFIX+short not in decisions:
        mark(short,'technical_or_existing','保留本课新增解释或按已有reviewed命题覆盖，并核对上下文条件。',ids)
    else:
        decisions[PREFIX+short]['existing_claim_ids'] = ids

# Round 4: reverse evidence, original character geometry, all-passage coverage.
sys.path.insert(0,str(BASE.parents[1]/'tools'))
from curation_contract import validate_records, digest
prepared = validate_records(db,KB,[(c,BASE/(NAME+'.jsonl'),i+1) for i,c in enumerate(claims)])
by_passage = defaultdict(list)
for c in claims:
    for e in c['evidence']: by_passage[e['passage_id']].append(c)
ledger, unassigned = [], []
for pid,p in P.items():
    linked = by_passage[pid]
    d = decisions.get(pid)
    if not d and linked:
        d = {'category':'technical_new','reason':'有价值技术解释形成所列原子命题；原文日期、级别、完成状态与联合条件均保留。','existing_claim_ids':[]}
    if not d and old_map[pid]:
        d = {'category':'existing_repeat','reason':'对应既有reviewed命题已覆盖本段技术内容；保持旧ID及证据，不隐式覆盖。','existing_claim_ids':old_map[pid]}
    if not d:
        unassigned.append((pid,p['text'])); continue
    old_ids = list(dict.fromkeys(d['existing_claim_ids'] + old_map[pid]))
    ledger.append(dict(passage_id=pid,unit_id=p['unit_id'],document_id=DOC,pdf_page=p['pdf_page'],role=p['role'],speaker=p['speaker'],published_at=p['published_at'],text_sha256=hashlib.sha256(p['text'].encode()).hexdigest(),categories=[d['category']]+(['technical_new'] if linked and d['category']!='technical_new' else []),reason=d['reason'],new_claim_ids=[c['id'] for c in linked],existing_claim_ids=old_ids,existing_candidate_claim_ids=candidate_map[pid],candidate_status_changed=False,rounds={
      '1_full_read':{'complete':True,'semantic_focus':'；'.join(c['text'] for c in linked) if linked else d['reason'],'context_kept':True},
      '2_atomic_split':{'complete':True,'claim_ids':[c['id'] for c in linked],'joint_conditions_kept':True,'exclusion_reason':d['reason']},
      '3_normalization':{'complete':True,'concept_labels':sorted({v for c in linked for v in c['concepts']}),'existing_claim_ids':old_ids,'same_label_not_same_condition':True},
      '4_reverse_evidence':{'complete':True,'exact_quotes_and_coordinates_checked':bool(linked),'semantic_qualifiers_rechecked':bool(linked),'existing_reviewed_checked':bool(old_ids),'excluded_nonclaims_rechecked':not bool(linked),'figure_origin_boundary_kept':True}},reviewer=REVIEWER))
assert not unassigned,unassigned
assert len(ledger)==len(P)==171
assert len({c['id'] for c in claims})==len(claims)
assert all('语境：' in c['review_note'] and '适用条件：' in c['review_note'] for c in claims)

def write(suffix, rows):
    (BASE/(NAME+suffix)).write_text(''.join(json.dumps(v,ensure_ascii=False)+'\n' for v in rows),encoding='utf-8')
write('.jsonl',claims)
write('.coverage.jsonl',ledger)
write('.pending.jsonl',pending)
write('.rejected.jsonl',[])
newlabels=sorted({v for c in claims for v in c['concepts']}-alllabels)
write('.concepts.jsonl',[{'id':'concept-'+digest(label),'label':label,'aliases':[],'new_claim_ids':[c['id'] for c in claims if label in c['concepts']]} for label in newlabels])
write('.anchors.jsonl',[{'claim_id':v['record']['id'],'anchors':[{'evidence_id':a['id'],'passage_id':a['passage_id'],'quote':a['quote'],'quote_start':a['begin'],'quote_end':a['end'],'source_spans':[a['span']],'figure_ids':a['figure_ids'],'source_role':a['source_role'],'figure_origins':a['figure_origins']} for a in v['anchors']]} for v in prepared])
figs={r['id']:dict(r) for r in db.execute("SELECT * FROM figures WHERE document_id=? AND pdf_page IN (107,108,110,114,115,116,121)",(DOC,))}
fig_notes={
 'p0107-fig1':'上证1分钟图含上倾三角形边线、56暂标及嵌入作者段落；下一交易日高开情形与图内K线可见，但图内正文不是独立新增证据。',
 'p0108-fig1':'上证1分钟图显示20—56附近标记；与p110图对照56位置后移，支撑原文暂定标记说明，不自行重分段。',
 'p0110-fig1':'上证1分钟图显示49低点、后续52—59以及右端暂标，已对照p109关于56更改和59未完成的文字。',
 'p0114-fig1':'上证1分钟图49以来走势，52—55、55—58、58—59与暂定60—63可定位；以作者文字给出的中枢/第三买点为判定，不只凭视觉补规则。',
 'p0115-fig1':'西部资源/600139日线，a、A、b与均线粘合、一吻高潮注释可见；汇编批注制作身份仍未核。',
 'p0115-fig2':'航天动力日线含“一吻”标注、均线与15.60—15.65图内数值；对应正文600343例子，未将图内数值升为一般规则。',
 'p0116-fig1':'中国铝业日线，7月20日箭头与均线粘合后上行可见；不从涨幅推导确定获利，不认定图为已溯源作者原图。',
 'p0121-fig1':'页顶上证1分钟图在75课标题之前，62—63及其后至72点可见；明确对应74课p120末“下图”。跨页关联经版面核对，不修改units课程边界。',
}
figure_rows=[]
for fid,f in figs.items():
    short=fid.split(PREFIX)[1]
    figure_rows.append(dict(figure_id=fid,document_id=DOC,pdf_page=f['pdf_page'],bbox=json.loads(f['bbox']),origin_status=f['origin_status'],visual_review_complete=True,reviewer=REVIEWER,render_path=str(BASE/(NAME+'.visual')/(short+'.png')),full_page_render_path=str(BASE/(NAME+'.visual')/f"p{f['pdf_page']:04d}.png"),review_note=fig_notes[short],linked_claim_ids=[c['id'] for c in claims if any(fid in e['figure_ids'] for e in c['evidence'])],original_blog_origin_verified=False))
assert len(figure_rows)==8
write('.figures.jsonl',figure_rows)
source_sha=hashlib.sha256((KB/'sources'/'volume_2.pdf').read_bytes()).hexdigest()
assert source_sha=='5332cd1b60381c47ceb81358db6bbb47882efd074fc5c869dcc3002aaed1b5c0'
summary=dict(stage='C',run_mode='authorized_isolated_curation_no_import',schema_version=meta['schema_version'],graph_version=meta['graph_version'],input_scope=['lesson-072','lesson-073','lesson-074'],document_id=DOC,source_filename='volume_2.pdf',source_sha256=source_sha,source_page_count=432,pdf_pages_read=list(range(102,122)),passages_read=len(P),coverage_counts=dict(Counter(p['unit_id'] for p in P.values())),claims=len(claims),claims_by_lesson=dict(Counter(c['id'].split('-c-stage')[0] for c in claims)),evidence=sum(len(c['evidence']) for c in claims),importance_counts=dict(Counter(c['importance_level'] for c in claims)),existing_reviewed_in_scope=sorted({cid for ids in old_map.values() for cid in ids}),existing_reviewed_preserved=True,figure_objects_visually_reviewed=len(figure_rows),figure_original_origins_verified=False,pending=len(pending),new_concepts=newlabels,whole_lesson_semantic_read_complete=True,technical_extraction_complete=True,all_four_rounds_complete=True,independent_review_claimed=False,author_commentary_reviewed_with_context=True,checks_run=['curation_contract.validate_records(db mode=ro) exact quote/codepoint/source mapping/geometry/role/figure/reference validation','171 of 171 passages individually covered','all eight figure objects rendered and viewed','fixed PDF SHA256 verified'],checks_not_run=['formal import','database or manifest mutation','desktop interaction or retrieval acceptance','original blog provenance investigation','independent human review'],acceptance='部分通过：三课171段全部四轮审读，所列新增命题和8图视觉对应已完成；图源及未展示理论证明保留待核，政策时间尺度不自行统一，未正式导入。',next_resume_anchor=NAME+'.pending.jsonl',next_action='主代理按最新图谱版本复核本隔离批并统一只读预检、授权发布。')
summary['relations_added']=0
summary['relation_note']='阶段C以有条件命题和概念归属承载；未为凑图边添加缺少独立语义的关系。'
summary['resolved_exercise']={'question_passage_id':PREFIX+'p0114-b006','author_answer_passage_id':PREFIX+'p0119-b002','answer_claim_id':'lower-l074-c-stage-case-one-minute-trend-end-divergence','note':'作者后附明确给背驰，不由模型补答。'}
check_path=BASE/(NAME+'.check.json')
if check_path.exists():
    check=json.loads(check_path.read_text(encoding='utf-8-sig'))
    batch_sha=hashlib.sha256((BASE/(NAME+'.jsonl')).read_bytes()).hexdigest()
    if check.get('graph_version')==meta['graph_version'] and check.get('records_checked')==len(claims) and check.get('machine_checks_pass') and check.get('writes') is False and batch_sha in check.get('batch_sha256',{}).values():
        summary['checks_run'].append(f"import_curation.py --check: {len(claims)} records, readonly, writes=false, graph {meta['graph_version']}")
(BASE/(NAME+'.summary.json')).write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in BASE.glob(NAME+'.*') if p.is_file() and p.name!=NAME+'.hashes.json'}
(BASE/(NAME+'.hashes.json')).write_text(json.dumps({'schema_version':meta['schema_version'],'base_graph_version':meta['graph_version'],'sha256':hashes},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'claims':len(claims),'evidence':summary['evidence'],'coverage':len(ledger),'new_concepts':newlabels,'figure_objects':len(figure_rows),'graph_version':meta['graph_version']},ensure_ascii=False))
