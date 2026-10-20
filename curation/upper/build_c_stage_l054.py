"""Materialize the main agent's four-pass reading of lesson54.

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
BASE = 'c_stage_l054'
REVIEWER = 'Codex 主代理 / 阶段C上册54课同模型四轮复核'
SOURCE_SHA = '32738dce3906062fc3b3fcc0a34077d0b583ecf46bf8f0e406ccee968db5e398'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-054' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 101
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 400 AND 411 ORDER BY pdf_page,id', (DOC,))]
assert len(figures) == 7
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
    pending.append({'id': 'upper-l054-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})


quote_overrides['409-b012']=passages[pid('409-b012')]['text'].split('，而且',1)[0]
quote_overrides['405-b003']=passages[pid('405-b003')]['text'].split('不过这样',1)[0]
quote_overrides['411-b005']=passages[pid('411-b005')]['text'].split('不是汉奸',1)[0]
c(54,'complex-graph-skill-confidence-absolute-understanding-author-view','400-b008 400-b009','作者用复杂图形强调概念清楚、多看图和磨练，并声称精通后能当下精确分析、指导操作。','操作熟练程度|走势分解|当下',2,'绝对把握性为作者理论/教学主张，不将读懂一图或同模型四轮当实盘无误判、独立语义验收或人工毕业标准。')
c(54,'case-equalities-d1-g2-d2-g4-and-g0-set-18-5','400-b010','本例设d1=g2、d2=g4，从设为g0的18.5元开始；作者说等值条件增加难度但有无不改变可分析性。','高低点|走势分解|价格区间',1,'仅本例等式，不改所有图形；整图标18.59而正文设18.5，两数分别保留不按图替换原字，原制图/原发未核。',figs=[(401,1)],ambiguity='source_g0_set_18_5_vs_figure_label_18_59')
c(54,'subminute-legs-as-lines-except-last-at-chosen-level','400-b011','本图除最后一个外，各dngn、gndn+1都为1分以下级别，作者在所选级别把它们当无内部结构线段。','次级别|操作级别|走势分解|最低级别',1,'明确保除最后一个，未凭图擅指最后一段所有内部构造；这里线段化为53观察原则，不等以后特征序列线段定义，图的1分周期不使每段都成1分走势。',figs=[(401,1)])
c(54,'g1-two-legs-no-one-center-tick-second-sell-d2-first-center','400-b012','从g0到g1仅两段，尚无1分中枢，分笔操作者却可视g1为二卖；到d2才形成1分中枢[d1,g1]。','走势中枢|第二类卖点|成交分笔|操作级别|完成',1,'不形成任何中枢限所取1分分析层，不否定紧后分笔二卖及更小结构；两个层次不可合成分笔二卖必为1分二卖。',conditions=['本图从g0逐段推进','g1仅两段；d2完成前三段才得到所述1分中枢'],figs=[(401,1)])
c(54,'equality-touch-oscillation-g3-third-sell-if-strict-g2-earlier','400-b012','因d1=g2，d2g2仍触及[d1,g1]属中枢震荡；d3g3不触及该区间，g3为三卖。若本例改为d1>g2，g2便是三卖。','第三类卖点|中枢震荡|重叠|高低点',1,'等于边界仍重叠，严格低于才对应本段假设的提前三卖；不把其他任意无完成次级回试的触边/未触边都机械当三卖。',figs=[(401,1)])
c(54,'associativity-g0g3-original-formula-ends-at-d3-unresolved','401-b000 401-b001','d1=g2时作者用结合律给两种括号重组，原式左端写g0g3而右端均以g2d3结束；这里保原式的端点张力。','结合律|走势分解|高低点',1,'已核PDF401原页及402图内重引；不能暗改g0d3或补d3g3。结合律用途与原等式书写端点歧义分开，不以符号错误证明任意分解等值。',figs=[(402,1)],ambiguity='source_equation_g0g3_left_vs_d3_right_endpoint')
c(54,'single-price-overlap-counts-not-ignored-under-equality','401-b002 409-b012','后一分解中枢[d1,g2]因d1=g2只有一个价位，作者说仍不影响g3三卖；答复也明确只要有重叠就算，不能因一个价位而忽略。','走势中枢|重叠|第三类卖点|结合律',1,'单价位重叠仍须此前结构/级别成立，非任一价格重复即有中枢；主力杰作动机评价未采为技术事实。',figs=[(402,1)])
c(54,'successive-leg-strength-MACD-consolidation-divergence-scale-operability','401-b003','作者以MACD辅助比较本图g1d2>g2d3>g3d4的力度，称后者相对前者盘整背驰；在1分图无甚操作意义，若日/年图则有。','MACD|盘整背驰|指标对比|操作级别|交易条件',1,'力度不等每段价格落差或K数，未自补面积数值；1分无意义限本图1分以下腿的可操作性，不是取消所有1分研究或宣称图周期等于信号级别。',figs=[(402,1)])
c(54,'same-level-centers-must-have-sublevel-connection-in-this-decomposition','401-b004','本课分解规范要求两同级中枢之间有次级走势连接，所举两个括号直接相接且无连接的g0d4分解不被允许。','走势分解|走势中枢|中枢连接|次级别',1,'本课图例必须次级原字保留；18课一般论述允许次级或更低以及缺口，范围尚未统一，不用后日期覆盖或改为全书已无分歧定理。',figs=[(403,1)],ambiguity='l054_sublevel_required_vs_l018_sublevel_or_lower_scope')
c(54,'three-child-groups-expanding-higher-center-no-separate-connectors','401-b004','作者特别区分三次级构成高一级中枢：三个括号可直接相加而不另插次级连接，这不同于两个同级中枢直接相接。','中枢扩展|走势中枢|次级别|中枢连接',1,'括号是扩为高一级的三次级结构，不是任意三个同级中心的裸加法都合格；不删除其重叠与完整走势条件。')
c(54,'at-d4-two-permitted-decompositions-preserve-original-formulas','401-b005 401-b006','到d4作者列两种合法分解：一式把d1g1+g1d2+d2g2入括号，另一式把d2g2+g2d3+d3g3入括号，其余腿按原式连接。','分解多样性|走势分解|结合律',1,'原两式都以g0d4为左端，不能把上一g0g3端点歧义串改至本式；不是无约束任意移括号，须满足中枢连接规范。',figs=[(403,1)])
c(54,'rebound-first-intermediate-second-center-oscillation-g4-equals-d2','402-b000','d4g4为盘背后正常反弹；第一分解中它和g4d5仍属三卖后到新同级或更大中枢的中间态，第二分解因g4=d2，d4g4及d5g5是中枢震荡。','盘整背驰|中枢震荡|第三类卖点|分解多样性',1,'同段不同分解对应不同结构标签，不能把第二式震荡改成第一式也已有确定新枢；g4=d2为本例条件。',figs=[(403,1)])
c(54,'choose-current-meaningful-decomposition-all-must-obey-rules','402-b001','两种分解都可，作者为短线操作倾向当下有明确中枢震荡或三类点意义的分解；第一种中间状态指导不足，所有分解仍须合规范。','分解多样性|当下|操作策略|走势分解',1,'方便指导是选法理由，不是改变历史原图或用未来结果倒定唯一正确划法。')
c(54,'first-decomposition-g5-five-center-d2-g5-whole-submoves','402-b002 402-b003 402-b004','第一分解到d5g5才消除中间状态；作者说三个括号内1分中枢重叠构成5分中枢[d2,g5]，并要求此时把1分走势当线段、以其整体高低点为端点。','走势中枢|次级别|操作级别|完成|中枢扩展',1,'保原小括号1分中枢用语及切换到完整1分走势线段的高低点要求，不把[d2,g5]静改成三个子中枢边缘交集；其中心/走势表述范围须继续核，读者CCTV不是独立作者证据。',figs=[(404,1)],ambiguity='source_child_center_wording_requires_whole_submove_extrema_context')
c(54,'d7g7-one-minute-type-specific-retest-doji-lower-chart-confirmation','402-b004 403-b000','在第一分解中g7为三卖：作者从d7g7第2、3根K较大回试及第5、6根小十字停留判断1分中枢、可画更小三段；有小图可进一步确认。','第三类卖点|走势中枢|K线|次级别|完成',1,'这些K序与形态仅本例经验识别，不建任意两十字或六根K必成递归走势的公式；离开/返回完整次级要求仍保留，不能用后续跌K当当时可成交证明。',figs=[(404,1)])
c(54,'second-decomposition-g6-five-center-d3-g5-g7-not-third-sell','403-b001 403-b002','第二分解到g6才完成5分中枢[d3,g5]；此时d7g7仍为中枢震荡，g7不构成该分解的三卖。','分解多样性|走势中枢|完成|第三类卖点|中枢震荡',1,'到g5/[d2,g5]与到g6/[d3,g5]各属一式，不能合并；为什么的作业未在本段给明细答案，409仅重申次级离开返回，不能将读者G6D7非次级理由冒为完整作者原答。',figs=[(405,1)])
c(54,'large-drop-can-precede-same-level-third-later-point-may-be-far','403-b003 404-b000','作者说大跌可由更小级三卖突破中枢，不须等该级三卖；足够长时间后该级三卖会出现，极端时可离原中枢很远，老庄股跳水反抽后再跌为例。','第三类卖点|操作级别|突破|走势中枢',1,'足够长时间未定量，后点可很远不等当前已完成本级点；跳水反抽例为作者历史概括未外验，不能泛化所有急跌都已满足某级三卖。')
c(54,'third-point-followthrough-absolute-author-claim-premises-unverified','403-b003 404-b000','作者在本段强称三卖后一定继续向下、三买后一定继续向上，并说所举监管未破坏理论的两个最基本前提。','第三类买卖点|理论成立前提|趋势转折|市场风险',1,'一定继续指本段作者模型性方向主张，不替换成必成趋势/永久不回/实盘保证；52三买可转大与本课409趋势可能性仍分别保留。本段未重列两前提，不自补或验证监管事实。',ambiguity='author_absolute_followthrough_vs_oscillation_and_execution_scope_pending')
c(54,'distant-third-buy-historical-600477-0409-and-600837-0206','403-b003','作者以600477在2007年4月9日的小级三买、距2月中枢很远，及600837在2月6日例子说明远离原枢的三类点仍可有效。','第三类买点|走势中枢|操作级别|理论成立前提',3,'保作者案例身份及两日期绑定；本课没有两股整图，未验证真实分段/监管事件/收益，也不将距离远本身当三买充分条件。')
c(54,'fast-forceful-weekly-break-smaller-third-needs-volume-strength','404-b001','大幅快速突破周线中枢时，等周线三类需日线离开再日线反抽，作者允许用30分甚至5分三类点介入；须与普通中枢震荡区别，并有猛烈快速走势、成交量和力度配合。','第三类买卖点|操作级别|成交量|突破|中枢震荡',1,'基本前提和混淆风险不可删；不是所有周线触边/小级三类都证明周线中枢已经被同级确认破坏。',conditions=['大幅快速突破而非一般中枢波动','小级别三类点成立，走势猛烈快速且成交量/力度配合'],exceptions=['不熟者易混淆普通中枢震荡，买入可等本级三类确认'])
c(54,'novice-buy-wait-own-level-third-sell-prefer-early-use-first-second','404-b001','作者建议理论不熟者买入仍等周线本级三买；卖点则宁早勿晚，可按小级别来，大级中枢也不应等到三卖才想起已有的一、二卖。','第三类买点|第三类卖点|第一类卖点|第二类卖点|操作熟练程度',1,'买卖处理不对称，不能把买入须保守等待原样套到退出，或把宁早卖变任意下跌无买卖点就全部强制卖的普遍公式。')
c(54,'extreme-amplitude-does-not-alone-upgrade-center-theoretical-example','404-b002 405-b000','作者构造5分中枢在10000元、以次级别以下震荡到0.01又涨100000000再回10000的极端例，仍称5分中枢震荡。','中枢震荡|操作级别|幅度|走势中枢',1,'作者明称仅理论例，不认证价格/涨跌停制度实际允许或真实出现；级别按结构而非绝对幅度，次级别以下原表述保留，不静定为只能严格小于次级。',ambiguity='ideal_extreme_amplitude_example_not_empirical_market_path')
c(54,'center-oscillation-sell-up-divergence-buy-down-not-chase','404-b002 405-b000','作者据极端例强调中枢震荡中，向上力度盘整背驰抛、向下力度盘整背驰回补，不杀跌追涨。','中枢震荡|盘整背驰|操作策略|追高',1,'限定中枢震荡、相应力度比较，不将任何涨跌都当点或忽视交易通道/仓位/完成确认；一定为作者操作论述非实盘效果实测。')
c(54,'chasing-after-third-may-survive-not-long-term-use-smaller-points','405-b001','作者区分中枢震荡内追涨杀跌与三类点后：后者中枢移动未必恰在买卖位置结束，即使结束还可能震荡，有活的机会但非长远办法，仍可用小级买卖点介入。','第三类买卖点|中枢震荡|追高|操作策略',2,'不是所有三类点后任意追价都有获利保障；震荡内一定死的修辞不作统计100%亏损率。')
c(54,'g7-two-decompositions-same-direction-warning-not-identical-labels','405-b002','作者说两种分解对g7结论相同，MACD两次拉回0轴冲不上且第二次红柱面积小，预示后面有麻烦；合规多解可互证。','分解多样性|MACD|指标对比|操作策略',1,'第一式g7三卖、第二式g7非三卖的明确标签各保留，相同结论指综合操作警示，不偷合两中心或给第二式补三卖；MACD是辅助非单条件保证。',figs=[(405,1)])
c(54,'skill-criterion-fast-current-ruleful-decomposition-not-real-diploma','405-b003','作者以能对任意图形熟练、当下、快速按上述规范分解并指导操作作为学习熟练标准。','操作熟练程度|当下|走势分解',2,'仅截规范标准前半；后小学/本科/北大毕业证为戏谑，非真实资质、学历认证或本项目独立能力测评结果。')
c(54,'may24-ten-first-1115-second-third-to1412-five-center','406-b001','5月24日作者指10:00一卖、11:15二卖为1分级，11:15至14:12为第三段，三段构成5分中枢；第三段为含二中枢趋势，末段为1分图上1分以下背驰，后拉回为5分中枢震荡。','第一类卖点|第二类卖点|走势中枢|背驰|操作级别|MACD',1,'1分图上1分以下信号与1分两卖级别区分，第三段含二中枢不等整个5分结构已经趋势；两中枢级别按本段1分走势语境，未用图上后K证明当时可成交。',figs=[(406,1)])
c(54,'may24-next-day-five-center-oscillation-and-4129-hold-premise','406-b002','5月24日作者预期次日围绕上述5分中枢震荡直到三类点，较大走势仍须在突破4129的1/2线后震荡站住才谈向上。','中枢震荡|第三类买卖点|1429点历史压力线|确认',1,'预期为历史作者模型分支，站住大前提不可删；未把图中已有的后来K认证未来一定如此。')
c(54,'998-343-study-third-buy-and-daily-MACD-not-complain','406-b003','作者要求个股也在买点买，举998、343在3月盘整的三买分析/日线MACD和回拉0轴后再起，强调研究细部而非抱怨。','第三类买点|MACD|操作熟练程度|操作策略',2,'635涨停问话不等作者推荐当时任意追涨，998/343暗码保原未强补证券全名；本段没有两股原图/完整级别，不由MACD过0单独证明三买或实盘收益。')
c(54,'reader-failed-third-buy-rejected-no-exception-author-assertion','407-b010','对读者把插回中枢后的回调当三买并被套的说法，作者否认这符合三买，要求先学基础，并说理论最大的例外就是没有例外。','第三类买点|操作熟练程度|理论成立前提',1,'读者407-b007实际操作/套牢是其自述，CCTV407-b009亦读者；作者没有逐段验证该读者所有时点，没例外为理论性强语，不当全市场/所有执行实证。',conditions=['针对读者407-b007及CCTV407-b009后作者回复','三买须按定义识别，不以自称三买即成立'],ambiguity='author_no_exception_claim_not_independent_validation')
c(54,'unicom-channel-rise-skill-trade-rails-divergence-or-hold-unbroken','407-b013','作者对联通中线说是通道式上涨，有技术可在上下轨结合短线背驰震荡买卖；没技术则下轨不破持有。','通道式上涨|上涨|背驰|操作熟练程度|操作策略',1,'历史个股分析，不等当前联通趋势，也未给轨道作图/突破容差或等同布林通道；两个人群与下轨不破条件保留。')
c(54,'1116-not-necessarily-consolidation-divergence-small-to-large-larger-context','407-b016 407-b017 408-b000','对10:38至11:16无盘背疑问，作者说盘背只是多数情况，可小转大；可参照第一段中枢回拉，或从5月22日11:00开始的大中枢震荡，更须综合不同级别中枢。','盘整背驰|小级别转大级别|走势中枢|操作级别|中枢震荡',1,'作者读者时刻不完全一致：解盘为11:15，读者问11:16，分别保留；原大下级别不静改引文。含5/25后行情的整理图不能证明5/24预测，盘背非唯一不等所有无盘背点都自动小转大。',figs=[(408,1)])
c(54,'five-center-one-down-one-up-no-high-or-divergence-second-sell','408-b004','站5分角度，作者以先1分向下再1分向上、不创新高或背驰解释二卖及5分中枢形成。','第二类卖点|次级别|走势中枢|背驰|操作级别',1,'本答原写背驰，53正文写盘整背驰，两条各保原语境，不替换原引；或非且，不能用两个1分K代两个完整1分走势。')
c(54,'rare-second-buy-below-first-or-second-sell-above-first-approved','409-b003','对编号1的二买能否低于一买、二卖能否高于一卖问题，作者答当然有可能，虽然很少见。','第一类买卖点|第二类买卖点|高低点',1,'问题具体文字在读者408-b008，作者原引只有1.当然有可能，虽然很少见；不得把读者创新高盘背推理全文改成作者原话。近邻API上下文未覆盖跨页整组问题，研究时须连读PDF408/409及本条条件。',conditions=['指向读者volume_1-a53e99c37ca5-p0408-b008的编号1问题：二买低一买/二卖高一卖','编号1作者认可可能性且很少见，不独立验证读者举例所有结构'],ambiguity='numbered_short_reply_requires_prior_page_reader_item_one')
c(54,'second-center-guarantee-no-larger-level-wording-reader-item-two','409-b004','对编号2引用二类后更大级别中枢并追问其必然性，作者答这绝对保证、没有什么更大级别，就是按这定义来。','第二类买卖点|走势中枢|次级别|操作级别',1,'原短答原字保留；问题在读者408-b009/b010和409-b000，不能把没有什么更大级别擅解为已撤销53整句或已给完整无限时间证明，当前API邻段不自动覆盖整个跨页问题须按ID联读。',conditions=['指向读者volume_1-a53e99c37ca5-p0408-b009、p0408-b010、p0409-b000编号2提问','绝对保证/没有什么更大级别为作者原答，比较基准与形成时序仍待核'],ambiguity='numbered_item_two_no_larger_level_reference_not_fully_resolved')
c(54,'third-point-sublevel-leave-return-no-center-reentry-item-three','409-b005','对编号3的分解作业，作者重申次级别离开、次级别返回不重回中枢。','第三类买卖点|次级别|走势中枢',1,'读者409-b002提出G6D7非次级原因，但作者这里只重申定义，不把读者完整因果判断冒作者明说；离开和返回均需次级完整类型，不只数子中枢。')
c(54,'may24-not-even-five-day-touch-novice-use-five-day','409-b008','对读者亏损跳水的说法，作者说当日连5日线都未碰到，不算其所称跳水；不熟者看5日线。','均线系统|操作熟练程度|操作策略',2,'历史作者相对尺度判读，不否定读者账户自述亏损或证明市场无风险；没碰5日线不能外推所有资产都没下跌。')
c(54,'divergence-return-causes-oscillation-third-only-trend-possibility','409-b013','作者说趋势在形成中，刚背驰回来归根造成中枢震荡，震荡出三类点才有趋势的可能。','背驰|中枢震荡|第三类买卖点|趋势|完成',1,'可能不可改必成趋势；未认可读者仅凭更高MACD可预先保证惯性幅度。与正文三类后必继续的方向强语分层保留，不能把继续位移等同完整趋势类型。')
c(54,'trend-center-connector-same-direction-no-overlap-wrong-d2g2','410-b007 411-b000','5月25日补充说趋势中两同级中枢间的连接次级必须与趋势同向；本图以d2g2连接两拟中枢不允许，因为中枢有重叠且连接方向不对。','趋势|中枢连接|次级别|走势中枢|重叠',1,'同向与中枢不重叠两问题均保留；不能以有一根连接就把重叠中枢当趋势。这里只保54必须次级原语境，不用后文抹掉18次级或更低/跳空范围。',figs=[(403,1)])
c(54,'may25-five-center-4129-retest-month-close-branches','411-b004','5月25日作者仍按昨天5分中枢震荡待三类点、4129突破后反抽确认；月收长上影则下月弱盘难免，光头阳则续强可能大。','中枢震荡|第三类买卖点|1429点历史压力线|K线|走势预测',2,'为有条件历史预测，长上影/光头阳的月线尚未收盘，不能当已发生或所有月份固定统计规律；弱盘难免为作者该时强语，续强只是可能。')
c(54,'market-script-depends-on-joint-forces-not-one-person','411-b005 411-b006','作者说其3之3剧本能否完成取决于多方面配合，自己一人不能决定，管理层也非一言堂，市场由合力形成。','市场合力|走势预测|宏观市场判断',2,'历史自述/剧本观点，不以自称总攻证明操控市场实际能力；3000/319/三个月预测争论不作当前行情或已验证收益。')

note('405-b003','teaching-diploma-and-cultural-joke-context','规范熟练标准之外的小学/北大毕业证及人物议论为作者教学戏谑。','技术命题只引前半，非真实学历证书/实际通过测验，文化人物评价未当已核事实。')
note('409-b012','main-fund-motive-opinion-context','一个价位重叠的定义答复之外，作者称有时为主力杰作。','技术引文止于只要有重叠就是，不将意图判断写成已查证市场主力行为。')
note('410-b001 410-b002 410-b003 410-b004 410-b005 410-b006','historical-blog-fee-policy-and-autobiography-context','5/25远离股票收费者文章：博客浏览、本人资产/身份/牛市判断、反收费忠告、删广告/不收费不收徒及宗教文化立场完整已读。','作者自述/价值忠告，非本人财富、99%人物/汇率宏观必然或所有收费服务诈骗的事实认证；技术连接补充另录，不把博客成交比喻作证券成交量。')
note('411-b001 411-b002 411-b003','historical-all-people-stock-policy-opinion-context','作者转引他人开户/家庭人数和自身四月全民炒股观点、30%/50%资产比例与监管建议。','转引他人及作者政策价值观/历史判断，不作当前人口账户事实、最优资产配置比例或法律经济证明；不凭嵌套引号冒另一人物为作者身份。')
note('411-b007','closing-context','周末活动收尾语。','保来源，不抽取技术或行为指令。')
issue('original-equation-endpoint-and-g0-price-not-silently-corrected','400-b010 401-b000 401-b001 401-b002','原设g0=18.5而图标18.59；g0g3等式右端止d3，端点张力已看原页/图中重引。','保原式原价，不暗改g0d3或补d3g3，不以图上文字替作者原引；原发未核不能宣称校原博客。',True)
issue('two-decompositions-whole-submove-extrema-and-g7-labels','401-b004 401-b005 401-b006 402-b000 402-b002 402-b003 402-b004 403-b000 403-b001 403-b002 405-b002','首式g5确认[d2,g5]与二式g6确认[d3,g5]不同；小括号中枢原用语与上级整走势高低点视角需分开，g7三卖/非三卖标签不同但操作警示可同。','保完整次级走势与子枢边缘不同；d7g7的2/3K及5/6十字只本例，不建K数充分定理，作业缺明细不冒用读者解释。',True)
issue('same-level-center-connector-direction-vs-l018-lower-level','401-b004 410-b007 411-b000','54同级中枢必须次级连接/与趋势同向/中心不重叠，18一般命题允许次级或更低及跳空；不能自动覆盖。','逐语境保原规范和18旧记录；方向和重叠两个禁因均保，未来全书核连接级别/分解前提而非只看日期。',True)
issue('third-point-followthrough-vs-trend-possibility-fast-break-and-extreme-range','403-b003 404-b000 404-b001 404-b002 405-b000 405-b001 409-b013','同级三类可远离且迟于小级突破，三类后必继续不等必成完整趋势；快破必须与普通震荡区分、量力配合，极端价差只是理论例。','保买入新手等本级而卖出宁早、一二卖不缺席；未核两理论前提在监管中是否保持、成交成本/量力阈值或极端路径真实可行。',True)
issue('numbered-replies-rare-inverted-second-and-no-larger-level','408-b007 408-b008 408-b009 408-b010 409-b000 409-b001 409-b002 409-b003 409-b004 409-b005','1答认可二买低一买/二卖高一卖但少见，2答绝对保证且没有什么更大级别，3仅重申次级离返不回；三者分别对号。','作者引文仅短答，详细问句保reader；默认邻段context不含跨页全部编号问题，须连读408/409原页及本条condition/review_note的稳定段ID；不把2答当已经解决53全部形成/完成时间证明。',True)
issue('seven-figure-origins-later-may25-and-cross-period-labels','401-b003 402-b004 403-b001 403-b002 405-b002 406-b001 407-b016 407-b017 408-b000','7整图6原发未核、408图含5/25未来K，1分图含以下级别信号；文字11:15与读者11:16分别保。','只图源/日期空格改元数据，原字/几何不动；后图不证明前日预测，重复黄框不是独立作者证据，图中MACD私有显示不补代码/面积值。',True)
issue('channel-rails-indicator-aids-and-five-day-reference','406-b003 407-b013 407-b016 408-b004 409-b008','联通通道上下轨无画法参数，个股MACD回0非三买单充分；53盘背与本答背驰各保原语境，5日线为不熟者历史参考。','不等同布林轨道/任意个股当前买点，补完整走势条件而非给隐含轨道/容差；二类或条件不改且。',True)
issue('historical-4129-month-close-and-author-absolute-teaching-claims','400-b008 405-b003 406-b002 407-b010 410-b004 411-b004 411-b005 411-b006','当下精确/无例外和毕业修辞为作者立场，4129站住、月收分支和合力剧本为历史条件观点，反收费政策及宏观资产比例非事实验证。','不冒独立能力/收益证明或当前金融法律观点；保所有非技术上下文，未给总体完成百分比/人工金标准。')
relations={
 'single-price-overlap-counts-not-ignored-under-equality':[('走势中枢','重叠','requires')],
 'same-level-centers-must-have-sublevel-connection-in-this-decomposition':[('中枢连接','次级别','requires')],
 'three-child-groups-expanding-higher-center-no-separate-connectors':[('中枢扩展','中枢连接','distinguishes')],
 'choose-current-meaningful-decomposition-all-must-obey-rules':[('分解多样性','当下','qualifies')],
 'first-decomposition-g5-five-center-d2-g5-whole-submoves':[('走势中枢','完成','requires')],
 'd7g7-one-minute-type-specific-retest-doji-lower-chart-confirmation':[('第三类卖点','次级别','requires')],
 'fast-forceful-weekly-break-smaller-third-needs-volume-strength':[('突破','成交量','qualifies')],
 'novice-buy-wait-own-level-third-sell-prefer-early-use-first-second':[('第三类卖点','操作熟练程度','qualifies')],
 'extreme-amplitude-does-not-alone-upgrade-center-theoretical-example':[('操作级别','幅度','distinguishes')],
 'g7-two-decompositions-same-direction-warning-not-identical-labels':[('分解多样性','MACD','qualifies')],
 'unicom-channel-rise-skill-trade-rails-divergence-or-hold-unbroken':[('通道式上涨','背驰','qualifies')],
 '1116-not-necessarily-consolidation-divergence-small-to-large-larger-context':[('盘整背驰','小级别转大级别','distinguishes')],
 'rare-second-buy-below-first-or-second-sell-above-first-approved':[('第二类买卖点','第一类买卖点','qualifies')],
 'divergence-return-causes-oscillation-third-only-trend-possibility':[('第三类买卖点','趋势','qualifies')],
 'trend-center-connector-same-direction-no-overlap-wrong-d2g2':[('中枢连接','趋势','qualifies')],
}
for r in rows:r['relations']=[dict(source=a,target=b,type=t) for a,b,t in relations.get(r['id'].split('upper-l054-c-stage-')[1],[])]


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
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], 'CCTV/Joyce中心边界解释仍读者；编号1/2/3问分别对作者三短答，完整问题跨页不冒作者原引；10:00/11:15/11:16时点不强修，亏损/操作和监管/行情自述非已证实绩。'
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
        'note': 'g0g3原式端点与18.5/18.59差不修；首g5和二g6两分解边界分开，整体走势高低点非子枢交集；连接次级/同向与18更低范围待核；三类必继续不等必成趋势，编号1/2/3短答需408/409完整reader问且不补证明；极端幅度/快速突破有前提，无例外/教学/宏观为作者观点非实证。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=f['note'],
             figure_source_review='实际查看400至411十二页及7整图：航天机电5/18五种旁注图与上证5/24一分图原发未核；408图含5/25晚于5/24问答，后K不证预测。g0g3原式/18.5设价与18.59图标及双分解不同中心/完成时刻均保，CCTV读者解非作者独立证据。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 101 and Counter(x['lesson_number'] for x in ledger) == {54: 101}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [54], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(400, 412)), 'figure_objects_viewed': 7, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '54课101段12页7整图同模型四轮；19时间空格和7图6未核1后加；原式端点/设价、两分解g5/g6中心不同，连接同向/级别范围、三类强语与趋势可能性、三编号跨页短答和执行条件分层，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


