"""Materialize the manually read lower 101-102 batch; SQLite is read-only.

Four passes are perspectives of the same agent, not independent reviewers.
This script writes review artifacts only. Publication has a separate backup gate.
"""
import hashlib
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

AGENT=Path(__file__).resolve().parents[2]
KB=AGENT.parent/'shared-knowledge/v0.1.0'
OUT=Path(__file__).resolve().parent
DOC='volume_2-5332cd1b6038'
BASE='c_stage_l101_l102'
REVIEWER='Codex 主代理 / 阶段C下册101—102课同模型四轮复核'
SOURCE_SHA='bcf7e9340b5ea6d740d5268055f6f522aec461946f9ae3d1c8f412c06f2eac5c'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
db.row_factory=sqlite3.Row
metadata={r['key']:json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version']=='1.1.0'
assert hashlib.sha256((KB/'sources/volume_2.pdf').read_bytes()).hexdigest()=='5332cd1b60381c47ceb81358db6bbb47882efd074fc5c869dcc3002aaed1b5c0'
passages={r['id']:dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id BETWEEN 'lesson-101' AND 'lesson-102' ORDER BY pdf_page,block_index,id")}
assert len(passages)==161
assert hashlib.sha256(json.dumps(sorted(passages.values(),key=lambda p:p['id']),ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==SOURCE_SHA
old={r['id']:dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts={r['label']:dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical={label:r['label'] for r in concepts.values() for label in [r['label']]+json.loads(r['aliases'])}
figures=[dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 353 AND 365 ORDER BY pdf_page,id',(DOC,))]
assert len(figures)==6
rows,pending,notes=[],[],{}
retained=defaultdict(list)

def pid(short):
    page,block=short.split('-',1)
    return f'{DOC}-p{int(page):04d}-{block}'

def ev(short,quote=None,figs=()):
    p=passages[pid(short)]
    clean=re.sub(r'(?:\*+)?(?:200[78]-\d{2}-\d{2}\d{2}:\d{2}:\d{2})$','',p['text']).rstrip('*')
    quote=clean if quote is None else quote
    start=p['text'].find(quote)
    assert start>=0 and p['text'][start:start+len(quote)]==quote,(short,quote)
    return {'passage_id':p['id'],'quote':quote,'quote_start':start,'figure_ids':[f'{DOC}-p{n:04d}-fig{k}' for n,k in figs]}

figure_notes={
 (353,1):'二买三式示意无署名日期，未核；三种情况以正文独立支持',
 (359,1):'3/11嵌文和光标但日图到4月含2990.8，后加；不能倒填倾斜三角形已破或30分钟背驰',
 (360,1):'3/11嵌文而五分图到3/12，后加；两分支不能提前定案',
 (362,1):'3/14五分图与嵌文同日，制作身份仍未核；第三1分钟中枢及后续五分压力分开',
 (363,1):'3/17嵌文而60分钟图标题3/19、光标3/18，后加；未反抽与3/19纠正分别按文字留存',
 (365,1):'3/19图与文同日，制作身份未核；绿色箭头足够一笔是明文纠正，背驰段仍未区间套确认'
}

def c(lesson,slug,shorts,text,labels,level,check,conditions=(),exceptions=(),figs=(),ambiguity='none'):
    citations=[ev(s,figs=figs if i==0 else ()) for i,s in enumerate(shorts.split())]
    cid=f'lower-l{lesson:03d}-c-stage-{slug}'
    assert cid not in old and cid not in {r['id'] for r in rows},cid
    labels=list(dict.fromkeys(canonical.get(x,x) for x in labels.split('|')))
    ps=[passages[e['passage_id']] for e in citations]
    context=f"第{lesson}课；角色{'/'.join(dict.fromkeys(p['role'] for p in ps))}；时间{'/'.join(dict.fromkeys(p['published_at'] or '无单独时间' for p in ps))}"
    reasons={1:'基础核心：定义及不能省略的前提。',2:'主要方法：影响结构识别与操作选择。',3:'补充深化：范围与边界。',4:'背景细节：历史案例、自述或作者经验立场。'}
    r={'id':cid,'text':text,'kind':'explicit','conditions':list(conditions),'exceptions':list(exceptions),'concepts':labels,
       'ambiguity_status':ambiguity,'review_note':f'语境：{context}。适用条件：'+('；'.join(conditions) if conditions else '本条列出的对象、级别及上下文')+
       '。四轮：通读全部正文及问答；拆分结论和联合条件；对照既有命题与标准概念；逆向核对原句、原页及涉及的图。'+check+
       '。同模型四轮不代表独立审查者；仅据固定汇编，未核原博客。',
       'importance_level':level,'importance_reason':reasons[level]+check,'reviewer':REVIEWER,'evidence':citations,'relations':[]}
    if figs:
        r['figure_review_note']='主代理实际查看原页及单图：'+'；'.join(figure_notes[x] for x in figs)+'。制作人均未核；后加图及未知示意图不作作者观点的唯一证据，命题由正文独立支持。状态：'+'；'.join(f['id']+'='+f['origin_status'] for f in figures if f['id'] in citations[0]['figure_ids'])
    rows.append(r)
    return cid

def note(shorts,category,reading,inverse):
    for s in shorts.split():
        assert pid(s) in passages,s
        notes[pid(s)]={'category':category,'reading':reading,'inverse':inverse}

def keep(shorts,cids,reason):
    for s in shorts.split():
        for cid in cids.split():
            assert cid in old,cid
            retained[pid(s)].append(cid)
    note(shorts,'existing_claim_retained',reason,'保留当前原段和跨课线索，不擅改旧命题及旧证据。'+reason)

def issue(slug,shorts,description,action,blocker=False):
    pending.append({'id':'lower-l101-l102-c-stage-pending-'+slug,'status':'pending','passage_ids':[pid(s) for s in shorts.split()],
                    'description':description,'suggested_action':action,'blocks_full_semantic_extraction_completion':blocker,'reviewer':REVIEWER})




c(101,'first-third-points-reference','353-b003 353-b004','第101课先以买点说明，卖点反过来；作者把第一类买点对应背驰点、第三类买点对应中枢破坏点。','第一类买点|第三类买点|背驰|走势中枢',1,'此处概括不删既有三类点的次级别离开及回抽不触中枢等完整定义；不是任意价格穿越即第三类。')
c(101,'second-buy-retest-end-definition','353-b005','第二类买点是一买后次级别回抽结束，再探底或回试的那个次级别走势的结束点；例5分钟底背驰一买后，1分钟向上结束再接1分钟向下，其结束点为二买。','第二类买点|第一类买点|次级别|背驰|完成',1,'先次级向上完成再次级向下完成，不能以任意一根回落K代替；回试的结束与一买的背驰结束不同。',['所论级别第一类买点已出现','一买后次级别回抽结束，再探底/回试次级别走势结束'])
c(101,'second-third-coincide-strongest','353-b007 353-b008','二买最强情况是刚好成为原下跌最后中枢开始震荡的第三类买点，即二三买合一，作者说一般会有快速V形走势。','第二类买点|第三类买点|中枢震荡|下跌',1,'一般不等必然V形或保证大级别上涨；21课已经明确二三重合也不排除更大中枢扩张。',['二买同时满足原下跌最后中枢的三买条件'],figs=((353,1),))
c(101,'second-buy-below-first-permitted','353-b009 353-b010','二买最弱情况下可以跌破一买，比一买低完全可以；作者说一般发生在盘整背驰后，对应顺势平台至扩张平台等变化，留待以后详述。','第二类买点|第一类买点|盘整背驰',1,'低于一买是明确允许分支，不能把一般一二三依次抬高升为定义；平台术语没有在此完整定义，不自行补公式。',figs=((353,1),),ambiguity='platform_terms_not_defined_here')
c(101,'first-second-third-higher-only-general','353-b011 353-b012','一般情况下，一买、二买、三买依次往上、一个比一个高；这是第101课三种情况中的一般支。','第一类买点|第二类买点|第三类买点',1,'另有二三重合和二买低于一买两支，依次抬高不是无条件必要要求。',figs=((353,1),))
c(101,'second-third-not-necessarily-adjacent','353-b013','从原下跌末中枢看，这些买点是该中枢震荡的结果；一二买的紧接关系不适用于二三买，二三之间可以有更多中枢震荡。','第二类买点|第三类买点|中枢震荡',1,'二三买不必相邻，不能把每次中间震荡买点都认定为正式第三类。')
c(101,'intervening-oscillation-buys-loose-naming','353-b013','二三买之间的中枢震荡买点一般不特别命名，作者说也可视为二买、影响不大。','第二类买点|中枢震荡|操作策略',2,'这是该段宽泛称呼，不静默改写一买后首次次级别回调的严格定义；正式点类与中间震荡操作分开。',ambiguity='strict_second_buy_vs_loose_oscillation_name')
c(101,'first-second-only-current-rise-intermediate','353-b014','作者限定只有这回升的中阴阶段才有第一、第二类买点；该中阴结束后，走势中枢震荡只剩第三类及中枢震荡买卖点，不再有一二买。','中阴阶段|第一类买点|第二类买点|第三类买卖点|中枢震荡',1,'这回升与该中阴是对象范围，不推广成未来一切新下跌永无新一买；与21已确认上涨无同级一二买并列。',['第101课所论这回升及其后中阴结束的结构'])
c(101,'recursive-unique-decomposition-author-claim','354-b002 354-b004','作者称分型、笔、线段及不同级别走势类型对应的递归函数，可把任何行情唯一分解，并把该唯一分解定理等同走势必完美。','走势分解|递归|走势终完美|分型|笔|线段',1,'原文是作者理论主张，此段没有完整形式化定义与证明；不能报告项目已证明任意行情唯一性，也不直接删除结合律重组及分解多样性。',ambiguity='formal_proof_not_reproduced')
c(101,'a0-arbitrary-design-author-wording','354-b005','作者说分型是递归的a0，设计可以随意，而且不影响唯一分解定理的证明。','分型|递归|递归定义|走势分解',1,'保留101随意措辞，同时84课明确替代入口须保证分解唯一；两段范围未形式统一，不能据此采用任意有歧义算法。',ambiguity='a0_arbitrary_design_vs_uniqueness_prerequisite')
c(101,'chosen-fractal-design-best-author-opinion','354-b006','作者认为所选分型a0设计在所有可能设计中最好，使笔出现的可能性最大并消除最多的偶然因素，便于实用分解。','分型|笔|递归',3,'最好和排除偶然性为作者评价，没有对所有替代入口的穷尽比较或性能实验，不列为已验证最优算法。',ambiguity='optimality_comparison_not_supplied')
c(101,'fractal-definition-unique-author-claim','354-b007','作者认为分型无需假设、只按定义即可有唯一明确答案。','分型|完全分类|走势分解',1,'限遵守既定分型和包含处理规则的作者主张；实现仍须按原定义核查，不据此认定所有笔线段级别歧义已消失。')
c(101,'contains-other-theories-author-claim','354-b008','作者以其唯一分解主张说明其理论可包含其他技术理论，而认为其他理论不如此分解。','走势分解|技术分析|走势终完美',3,'没有对其他理论的逐一比较，此处不证明普遍包含性或外部理论优劣。',ambiguity='other_theories_comparison_not_supplied')
c(101,'practical-use-without-modern-math','354-b009','作者说有好的现代数学背景可以理解更深；不明白这些背景者也可把其给出的操作方法搞明白后应用。','操作熟练程度|技术分析|操作策略',2,'可学方法不等自动获得交易能力或收益，数学理解与本项目证据/实现验证也分开。')
c(101,'mar5-line-down-class-divergence-to-minute','354-b012','3月5日作者称标准线段类下跌类背驰后回拉最后类中枢并构新1分钟中枢；4331的5分钟中枢仍震荡，因为三卖未出现。','类背驰|类中枢|走势中枢|第三类卖点|中枢震荡',1,'线段类背驰与严格级别背驰分开；新1分钟中枢不能自动宣告原5分钟已破。',['2008年3月5日该4331结构'])
c(101,'mar5-red-and-center-not-sufficient','354-b013','作者认为中线MACD红柱仍保持且5分钟中枢未破时存在机会，但行情能否摆脱震荡仍须基本面配合。','MACD|走势中枢|中枢震荡|确认|政策风险',1,'红柱与中枢不破不是无条件行情启动的充分条件，保留基本面限制。',['2008年3月5日所论情景'])
c(101,'above-twenty-not-no-opportunity','355-b003','作者补充20元以上被其口号称垃圾，并非没有机会，而是其所谓第二、第三、第四中枢以后的机会。','价格区间|走势中枢|操作策略',2,'是对3月4日低价口号的明说限制，不等20元阈值有已验证投资有效性；中枢数量与复权价格未提供普适量化方法。',['2008年3月5日该选股口号上下文'],ambiguity='price_slogan_center_number_scope')
c(101,'rotation-laggard-three-joint-conditions','355-b005','作者说大资金布局非一日之功；短线选当前活跃板块的补涨股，要前期没动、有新资金关注且出现相应技术买点。','板块轮动|资金管理|操作策略',2,'三项联合不缩成只找低价或只找没涨的股票，新资金关注未给可重复测量标准。',['当时活跃板块中的补涨选择','前期未动、有新资金关注且有相应技术买点'])
c(101,'mar6-4391-not-stable-4695-not-ready','355-b010 355-b011','3月6日4331的5分钟震荡依旧，4391未站稳使4695更未到准备阶段；红柱仍在但反弹过弱，突破4391后若无力仍可能返回。','中枢震荡|MACD|笔|确认',1,'日笔4391与周笔4695边界不同，不以红柱取代站稳或否认失败分支。',['2008年3月6日所论4331/4391/4695'])
c(101,'rotation-sell-weak-buy-potential-not-chase','356-b001 356-b002','作者描述轮动节奏为热点冲高卖出，再低吸有启动潜力的热点，而不是追高；不能把握节奏者不做。','板块轮动|操作熟练程度|操作策略',1,'低吸潜力仍须技术及能力条件，不认定任何热点回落都是买点。',['第101课所论当时轮动环境','能把握相应节奏'])
c(101,'mar6-red-expands-price-not-confirmed','356-b003','3月6日即使红柱扩大，4695未站且4391也未站，作者仍保留再次破位可能，并提醒该年度不会只有上涨。','MACD|确认|完全分类|操作策略',1,'指标扩大不等价格边界或结构已确认，年度语句为当时作者判断而非项目预测。',['2008年3月6日该情景'])

c(102,'perfection-overall-structure-author-claim','356-b005 356-b008 356-b009','作者解释走势必完美不只指单个唯一分解，还指递归分解给出的类似记数系统的完美整体结构，并据此支持操作。','走势终完美|走势分解|递归',1,'记数系统为解释性类比，没有在此建立市场序列与数系的严格等价或完整证明。',ambiguity='formal_proof_not_reproduced')
c(102,'recursive-system-graded','356-b010','作者强调其递归函数有级别，而且级别依次升大。','递归|级别|走势分解',1,'级别来自结构递归，不把任意固定K线周期直接作为严格结构级别。')
c(102,'interval-nesting-from-overall-structure','356-b011','作者称区间套方法是其完美整体结构的重要应用，可据此精确定位买卖点。','区间套|走势终完美|操作策略',1,'保留作者归属；此处未给覆盖所有行情的终止/精度证明，精确定位还需当下满足各级结构，不当无条件预测保证。',ambiguity='nested_precision_formal_guarantee_not_supplied')
c(102,'eight-level-names-convenience','356-b012','作者说其1分钟到年线的八个级别，其名称可以任意取，目前命名只是习惯上方便。','级别|周期K线图|递归',1,'名字可换不等结构任意；本段没有重新逐项列八级，不据时间名称机械换算笔/线段。')
c(102,'finer-levels-optional','356-b013','在八级下还可增加笔、线段等更细级别，但作者说一般没必要。','级别|笔|线段|操作级别',2,'没必要为一般应用建议，不删最低递归入口定义或把笔等同实际成交分笔。')
c(102,'one-five-thirty-usual-day-large-funds','357-b000','作者说一般操作不必一直分解到年季月，通常1、5、30分钟足以应对走势；较大资金可考虑加日级别，因为大级别多年才变化。','操作级别|资金管理|级别|走势分解',1,'通常/一般与较大资金范围保留；6124下来仍30分钟为当时案例，不建立跨品种固定资金阈值。',['第102课所论一般操作范围'])
c(102,'three-layer-expression-and-change-order','357-b001','作者将走势表示为a1A1+a5A5+a30A30，并称大级别变化首先出现在小级别，不会5分钟已由下跌转上涨而1分钟仍下跌。','级别|走势分解|表里关系|当下',1,'符号系数未进一步定义，不自行实现线性加权模型；上下级是相应同一结构的状态，不混不同起止区间。',['第102课所述对应的1/5/30层结构'],ambiguity='coefficients_not_formally_defined')
c(102,'classification-control-means-current-display','357-b003','作者说走势必完美使完全分类成为可能，而其可控意思仅是走势按理论原则当下显示，没有其他特别含义。','走势终完美|完全分类|当下',1,'可控不解释为可操纵价格、预知唯一未来或无交易风险；作者随后量化主张仍须定义和实现检验。')
c(102,'classification-boundaries-exact-author-claim','357-b004','作者说此完全分类有级别，分界点可精确到具体位置，而非一般含混的涨跌平。','完全分类|级别|当下|确认',1,'此处宣称精确但未完整提供所有边界算法、误差与终止证明，不等工程实现已经全部验证。',ambiguity='classification_precision_not_formally_proven')
c(102,'mar7-4331-and-4391-weak','357-b008 357-b009','3月7日4331的5分钟震荡继续，4391多次未站上；作者保留继续探底、下周无改观可能在4123附近新低的分支。','中枢震荡|确认|完全分类',1,'下一周及4123是当时条件展望而非既成事实，不用后期行情替当时确认。',['2008年3月7日该4331/4391情景'])
c(102,'mar7-temporary-thirty-oscillation-conditional-trap','357-b010','作者暂时按大30分钟震荡观察，若两会后基本面没有改观，保留较快下跌制造空头陷阱的可能。','中枢震荡|级别|空头陷阱|政策风险',2,'暂时和若基本面未改是条件，不认为所有随后下跌均已证实空头陷阱或保证反转。',['2008年3月7日的临时30分钟观察框架'])
c(102,'mar10-third-sell-formed-minute-down-likely','358-b006','3月10日作者说早盘弱反弹已出现三卖，而周五1分钟中枢极可能成为新1分钟下跌第一个中枢。','第三类卖点|走势中枢|下跌|确认',1,'三卖已出与整体下跌极可能两种确认程度照留，不把极可能改已完整形成。',['2008年3月10日该分钟结构'])
c(102,'mar10-opportunity-capability-gate','358-b010','作者说所述机会不是人人适合，有能力者选择相应机会，无能力者先等基本面好转。','操作熟练程度|操作策略|政策风险',1,'能力门槛未因低价或市场未来反弹取消，也不提供统一收益承诺。',['2008年3月10日所论行情机会'])
c(102,'mar11-gap-not-filled-minute-down-formed','359-b002','3月11日指数离4062周线缺口还差1点，尚未完全回补；作者此时称1分钟下跌已经形成。','缺口|下跌|级别|确认',1,'差1点不改成已补完，与3月10日极可能状态按日期分别保存。',['2008年3月11日该周线缺口及分钟下跌'],figs=((359,1),))
c(102,'mar11-second-center-third-buy-or-c','359-b002','3月11日所论1分钟下跌第二中枢之后，作者仅保留直接第三类买点反弹，或走完a+A+b+B+c中的c后标准背驰上去两支。','走势中枢|第三类买点|背驰|完全分类|走势分解',1,'条件分支不是两者已同时发生，a/A等不能改成任意等长段；次日截图不提前确定选哪支。',['2008年3月11日该已成1分钟下跌的第二中枢'],figs=((360,1),))
c(102,'mar11-preliminary-triangle-two-low-line','359-b003','作者把3月11日低点在前两个低点连线附近视为倾斜三角形的初步形态，关键是该连线不能跌破。','确认|高低点|操作策略',2,'初步不等形态永久成立，不能利用右侧4月K线反填当时已破或已确。',['2008年3月11日所论三低点连线'],figs=((359,1),))
c(102,'mar11-minute-not-thirty-divergence','359-b004','作者说当时仅为1分钟下跌，对大30分钟震荡未有实质破坏，6124起30分钟下跌的真正背驰还没有出现。','级别|下跌|背驰|中枢震荡|确认',1,'小级别下跌不自动确认30背驰；文字对30下跌与其最近中枢震荡的参考范围保留。',['2008年3月11日该6124起结构'])
c(102,'mar11-consolidation-divergence-bottom-conditional','359-b004','作者认为盘整背驰也可制造底点，随后三买直接上去，但须后市确认；确认前仍按震荡，上冲无力先退出。','盘整背驰|第三类买点|确认|中枢震荡|操作策略',1,'可能与须后市确认不省，盘整背驰不自动当真正趋势背驰或确定上涨已成。',['2008年3月11日该盘整背驰底部可能支'])
c(102,'mar11-worst-five-center-break-then-thirty','359-b005 359-b006','3月11日最坏支是反弹形成5分钟下跌首中枢，再跌破低点连线后形成真正30分钟背驰；作者同时保留极端如美国1987行情未必有背驰的例外，最好仍继续30分钟震荡。','走势中枢|下跌|背驰|完全分类|确认',1,'5分钟首中枢仍属最坏条件链，美国1987仅作者举例未独立重建，不当所有市场必背驰定理。',['2008年3月11日该后续分类'],exceptions=['作者所举极端美国1987情形可能没有背驰'])
c(102,'mar12-c-or-extend-five-center','361-b009 361-b010 361-b011','3月12日作者仍按前述1分钟中枢观察；走c后形成5分钟中枢，或直接延伸成5分钟中枢，对所论随后五分中枢没有本质区别，最坏是否为5分钟下跌首中枢仍待市场选择。','走势中枢|中枢扩展|下跌|完全分类|确认',1,'没本质区别限此后5分钟中枢，不推广成盘整背驰与趋势背驰定义相同或所有路径等价。',['2008年3月12日该分钟中枢后续'])
c(102,'mar13-short-rebound-not-medium-stability','361-b016','作者区分短线反弹与中线站稳，认为中线站稳还需要多方面条件。','反弹|确认|政策风险|操作策略',2,'反弹发生不即中线反转，不能把消息期待登记成已站稳。',['2008年3月13日该基本面与行情语境'])
c(102,'mar13-weak-up-exit-capability','362-b001','在当时基本面不稳定的语境下，作者强调上冲无力退出；没有技术能力者先坐小板凳等待。','操作策略|操作熟练程度|确认',1,'能力条件和不稳定环境照留，不改为任何涨幅均卖或任何人必须交易。',['2008年3月13日所论不稳定行情'])
c(102,'mar13-thirty-end-likely-five-not-formed','362-b002','3月13日作者把6124起30分钟下跌结束后的强力反弹视为技术上最大机会，但最后5分钟下跌尚未形成，当前仍是1分钟结构；因此此时只能30分钟盘整背驰，或以后另有更大下跌形成5分钟类型。','级别|背驰|盘整背驰|下跌|确认|完全分类',1,'所论机会不升为当时已结束或即将结束，5分钟未形成不能凭大图外形当形成；后续仍由市场选择。',['2008年3月13日该6124起下跌'])
c(102,'mar14-third-minute-center-rebound-risk','363-b001','3月14日4000下又构1分钟中枢，为这次1分钟下跌第三个中枢，作者说一般短线反弹将至；若反弹只在4000上下形成5分钟中枢，可能成为5分钟下跌首中枢并带来压力。','走势中枢|下跌|反弹|完全分类',1,'一般及若条件保留，第三个中枢不自动定底或保证反转；仅此例的反弹中枢范围。',['2008年3月14日该4000上下结构'],figs=((362,1),))
c(102,'mar14-rebound-divergence-vs-consolidation-limited','363-b001','作者说这次1分钟下跌结束后反弹，由背驰还是盘整背驰产生，本质没有太大差别。','背驰|盘整背驰|反弹',2,'本质没有太大差别限所论随后反弹，仍保存二者定义和最低回跌要求差异，不全局合并概念。',['第102课3月14日这一反弹语境'])
c(102,'mar17-sixty-chart-minute-center-reference','363-b007','3月17日作者在6124下来的60分钟图上说目前只走四个线段，连一个1分钟中枢都未形成，并特意注明这是60分钟图。','周期K线图|线段|走势中枢|级别',1,'保留60分钟图上的1分钟中枢这一原话参考框架；不能与前文严格1分钟中枢已成直接当同一对象，也不做固定周期级别换算。',['2008年3月17日作者所示60分钟图的参考框架'],figs=((363,1),),ambiguity='chart_reference_frame_vs_strict_structural_level')
c(102,'mar17-fifth-segment-class-third-sell-nesting','363-b008 364-b000','在该60分钟图框架中，作者给第五线段标准走法：一笔对3反抽，成类第三卖点后再破底，一旦当下满足区间套即可精确定位底部。','线段|笔|类中枢|第三类卖点|区间套|确认',1,'类三卖与严格级别三卖分开，区间套满足是前提而非四段已见即底部已确认；3是图上标号不是第三类同义。',['第102课该60分钟图第五线段情景','类三卖后再破底且当下满足区间套'],figs=((363,1),),ambiguity='chart_reference_frame_vs_strict_structural_level')
c(102,'mar17-retest-stroke-not-yet-author-state','364-b001','3月17日作者当时说对3的反抽笔还未出现；以下反弹若成类三卖最好，若再回3上则3/4类中枢震荡继续。','笔|类中枢|第三类卖点|中枢震荡|确认',1,'3月19日作者明确纠正绿色箭头处已足够一笔，旧日期判断照录并建立纠正线索，不用后期图悄改3月17日文字。',['2008年3月17日该60分钟图当时的说明'],figs=((363,1),),ambiguity='explicit_mar19_correction_to_mar17_stroke_state')
c(102,'mar17-macd-zero-pressure-example','364-b002','作者指出该60分钟图标号4对应MACD在零轴被压下去，之后再次破底，并称这是标准走势。','MACD|确认|周期K线图',2,'标号4是本图位置而非第4中枢通则；标准是作者案例判断，不证明MACD为所有背驰必要条件。',['2008年3月17日该图标号4及MACD'],figs=((363,1),))
c(102,'large-chart-coarse-small-chart-precision','364-b003 364-b004','作者说较大周期图可看大概，但精确买卖点仍须结合小周期图；以中石油日线48元下来一线段未完、很有机会走该线段第四笔为例。','周期K线图|线段|笔|区间套|操作策略',1,'中石油笔数及后续为当时作者大图示例，不是项目逐笔独立复算，更不把图周期固定等同严格级别。',['第102课所论大图判断与小图定位'])
c(102,'mar18-author-first-batch-buy-self-report','364-b009 364-b012','3月18日作者自述尾盘吃进第一批筹码。','资金管理|仓位|操作策略',4,'只是作者自述，未有成交单、账户或独立收益验证，不把本项目当执行交易者。',['2008年3月18日作者自述'])
c(102,'mar18-large-fund-batches-base-position','364-b013 364-b014','作者说大资金不能像小资金在某个精确瞬间建仓，应分批；底仓建立后相对保持，用其他资金做震荡逐步降低成本。','资金管理|仓位|成本|中枢震荡|操作策略',1,'底仓与其他资金分开，大小资金无金额阈值，不保证降成本或取消流动性与交易制度约束。',['第102课3月18日所论大资金建仓'])
c(102,'mar18-low-price-drop-preference-not-rule','365-b001','作者选股偏好绝对价格低且短线跌幅够大，最好超过40%。','价格区间|操作策略|资金管理',3,'最好超过40%为作者该次偏好，不是第一类买点定义或跌40%即充分买入条件，未附收益验证。',['2008年3月18日所论作者选股偏好'])
c(102,'mar19-sixty-bottom-fractal-3775-boundary','365-b004 365-b005','3月19日作者把早盘跳空后回试作为次佳买入机会，理由是60分钟图刚形成底分型，3775为该底分型上边沿。','底分型|周期K线图|确认|操作策略',1,'60分钟底分型与严格60分钟级别买点分开；次佳为作者案例评价，000938低开涨停自述未独立核验。',['2008年3月19日所论60分钟图及3775边界'],figs=((365,1),))
c(102,'mar19-explicit-correction-enough-stroke','365-b006','3月19日作者明确纠正：图上绿色箭头所指已经足够构成一笔，且未回到4431，刚好成类第三卖点；之后可直接回图中3的位置或在此折腾出一线段。','笔|第三类卖点|线段|确认|完全分类',1,'有必须有一个纠正的明文才登记修订，针对3月17日反抽笔未出判断，不用文章日期自动覆盖全部旧定义；3和4431为本图参照。',['2008年3月19日对该60分钟图绿色箭头的明确纠正'],figs=((365,1),),ambiguity='explicit_mar19_correction_to_mar17_stroke_state')
c(102,'mar19-divergence-leg-not-confirmed-bottom','365-b007','作者说到3月19日仍无明确区间套，不能完全确认从4下来的下跌已走完；仅从60分钟图看形成背驰段，该段仍未由区间套精确定位确认。','背驰|区间套|线段|确认|周期K线图',1,'背驰段不等完整底背驰已确，4为图上标号；较大图外观不代替小图完成条件。',['2008年3月19日该60分钟图背驰段'],figs=((365,1),))
c(102,'mar19-return-three-two-paths-not-known','365-b007','作者说按通常情况最终回图中3的位置是必然的，但尚待选择先完成区间套再回，还是直接上去。','区间套|完全分类|确认',2,'通常非无条件保证，3的图上标号不是原文已证明所有盘整背驰回原中枢的全局定理；两路径未定。',['2008年3月19日该60分钟图情景'],figs=((365,1),))
c(102,'mar19-3775-fractal-to-stroke-still-conditional','365-b008 366-b000','作者说3775关系到这60分钟底分型能否最终延伸成笔；若连笔都不能延伸出来，则还须探底完成区间套构造。','底分型|笔|区间套|确认',1,'底分型已见不等笔已成，3775一价观察不替代81新笔两个联合条件，跨页句意合读。',['2008年3月19日该3775与60分钟底分型'],figs=((365,1),))

keep('353-b005','upper-l017-second-buy-definition','101以一买后次级上再下结束细述二买，首次回调定义保留，不自行补价格必高要求。')
keep('353-b008 353-b012','upper-l021-c-stage-second-third-coincidence-iff upper-l021-c-stage-second-third-coincidence-no-guaranteed-trend','二三合一须满足完整离开回抽不触中枢条件；一般快速V形仍不排除较大中枢扩张。')
keep('353-b014','upper-l021-c-stage-confirmed-uptrend-only-third-buy','所论回升中阴结束后无一二买，与已确认上涨同级只三类范围对应，不限制未来新走势。')
keep('354-b002 354-b005','lower-l084-c-stage-uniqueness-proof-author-claim lower-l084-c-stage-fractal-only-recursion-start-optional lower-l084-c-stage-two-recursion-functions','101唯一性与随意a0主张并列84替代入口须保证唯一性及两递归函数，不冒充完整形式证明。')
keep('354-b002 356-b009','lower-l099-c-stage-general-not-same-level-partition lower-l070-c-stage-associativity-connects','唯一分解主张不自动抹除一般与同级别差异、结合律合法重组，精确等价范围待核。')
keep('355-b003','lower-l100-c-stage-mar4-low-price-slogan-author-selection','有并非没有机会的明说才记口号限制，不改旧价格口号原句，不把价格阈值当充分买点。')
keep('355-b011 356-b003','lower-l100-c-stage-macd-visual-auxiliary-not-special lower-l100-c-stage-mar3-week-fractal-4391-stroke-4695','红柱、日4391与周4695各自条件不能互借。')
keep('363-b007 364-b003 365-b007','lower-l063-chart-period-not-center-level lower-l064-preconfirm-not-actual-confirm','图周期是观察尺度，图上背驰段未区间套确认不等线段/真实背驰已完成。')
keep('365-b008 366-b000','lower-l081-c-stage-new-stroke-two-joint-conditions','本图3775上边沿观察不替代包含处理后不共K及极值K之间至少三根两条件。')

issue('second-buy-three-forms-and-loose-name','353-b005 353-b008 353-b010 353-b012 353-b013 353-b014','二三可合一、二买可低于一买；二三间震荡点也可宽称二买，与正式首次次级回调定义范围需保留。','不强制一二三价格严格上升，不把每个震荡买点自动作为新正式二买，平台术语在本课未详定。',True)
issue('uniqueness-and-recomposition-proof','354-b002 354-b004 354-b007 354-b008 356-b008 356-b009 357-b003 357-b004','作者宣称任意行情唯一分解、完美整体结构和精确分类，未在本批完整呈现证明；一般划分、结合律多种重组的等价对象尚待形式化。','标作者主张与未复现证明，保留合法划分条件，不以软件检查替代数学证明。',True)
issue('a0-arbitrary-vs-prerequisite','354-b005 354-b006','101说a0设计随意不影响证明，84要求替代入口保证唯一；所选设计最好也未给穷尽比较。','并列原句和范围，不把任意歧义入口自动认为合法，不宣称已验证最优。',True)
issue('chart-reference-frame-and-precision','356-b012 357-b001 363-b007 363-b008 364-b003 365-b007','60分钟图上的1分钟中枢不是已明确严格级别换算；分解系数和区间套精度/终止边界未完整定义。','保留图上参考框架、系数未定义和当下满足前提，不机械按K周期换算结构。',True)
issue('explicit-stroke-correction-and-confirmation','364-b001 365-b006 365-b007 365-b008 366-b000','3/19明确纠正3/17绿色箭头反抽笔状态，但仍无明确区间套；底分型、笔和背驰段完成不同。','以明确纠正文字登记跨日修订；旧日期判断照录，3775不替新笔两个联合条件。',True)
issue('historical-price-policy-and-self-report','355-b003 355-b005 357-b010 358-b010 359-b005 359-b006 364-b009 364-b012 364-b014 365-b001','低价口号、40%偏好、政策与资金因果、1987类比、作者第一批建仓及收益预期未独立核验。','保留历史作者归属、能力/资金/结构限制，不记项目成交、实测收益或当前推荐。')
issue('figure-makers-and-late','353-b008 359-b002 363-b001 363-b007 365-b006','本批六图已看：359/360/363明确含文后行情，353/362/365来源仍未核；366图属于下一课103。','三图标后加、三图保持未核；正文独立支持，不倒填确认，不把邻课图重复计入本批。')

note('353-b001 353-b002 353-b006 354-b000','author-self-authored-qa-structure','作者自行设题组织答疑，依次介绍第二类点及走势必完美，无独立读者发言。','标题与自设问句不误标读者，保留原作者身份及时间。')
note('354-b001 354-b003','author-math-history-rhetoric','现代数学、费马大定理和分圆域理想唯一分解的历史叙述已读。','仅作作者论证背景；不认证数学史细节或以类比证明市场分解。')
note('354-b011 354-b014 355-b000 355-b001 355-b002 355-b004 355-b006 355-b007 355-b009 355-b012 356-b000','historical-policy-sector-opinion','平安融资、护盘、农业5000亿、医改、板块中期轮动及除权填权、创业板/税/期货期待均为当时作者评论。','不认证未核企业资金动作与政策因果，不转为当前制度或推荐；技术条件另抽。')
note('356-b006 356-b007 357-b002 357-b005','author-number-system-analogy','素数、二进制十进制与幂级数分解、等价完全分类记数系统及篇末总结已读。','类比和作者断言不等建立严格数学映射，不补系数意义、函数或证明。')
note('357-b007 357-b011 357-b012 358-b000 358-b002 358-b003 358-b004 358-b005 358-b007 358-b008 358-b009 358-b011 359-b000','historical-market-capital-rhetoric','停牌融资、围城、新基金资本迁移、中小板和权证投机、吃肉及资金争夺等评论已跨页读。','作者利益/政策/收益判断未经外核；不建议任何人照做权证投机，能力条件另列。')
note('359-b007 360-b000 360-b001 360-b002 360-b003 360-b004 360-b005 360-b007 360-b008 361-b000 361-b001 361-b002 361-b003 361-b004 361-b005 361-b006 361-b007 361-b008','historical-financing-and-regulator-opinion','题材板块、美国救市、融资、资金空转及监管者批评全文已读。','匿名力量、企业动机、宏观因果与指控只归作者，不当已证事实、当前法律或投资判断。')
note('361-b013 361-b014 361-b015 362-b000 362-b004 362-b005 362-b006 362-b007 363-b000 363-b002 363-b003 363-b005 363-b006','historical-confidence-and-liquidation-opinion','3G消息、信心危机、多杀多、基本面三风险和融资意见已读。','多杀多为作者底部叙事非已证明通用必要条件，政策信息未外核，明确结构状态另抽。')
note('364-b005 364-b006 364-b007 364-b010 364-b011 364-b015 364-b016 365-b000 365-b002 366-b001','historical-building-position-and-profits','记者会期待、基本面转变前的多杀多、作者操作议论、年度预期和小板凳学习、低价板块牛股收益口号已读。','没有账户和统计检验，不认证实际收益或未来走势；能力、分批和偏好限制另列。')

relations={
 'lower-l101-c-stage-second-buy-retest-end-definition':[('第二类买点','第一类买点','requires')],
 'lower-l101-c-stage-second-third-coincide-strongest':[('第二类买点','第三类买点','related')],
 'lower-l101-c-stage-first-second-only-current-rise-intermediate':[('中阴阶段','第二类买点','qualifies')],
 'lower-l102-c-stage-classification-control-means-current-display':[('完全分类','当下','related')],
 'lower-l102-c-stage-mar19-divergence-leg-not-confirmed-bottom':[('区间套','确认','related')],
}
for r in rows:r['relations']=[{'source':s,'target':t,'type':kind} for s,t,kind in relations.get(r['id'],[])]

by_passage=defaultdict(list)
for r in rows:
    for e in r['evidence']:by_passage[e['passage_id']].append(r)
for item in pending:
    item['lesson_numbers']=sorted({int(passages[x]['unit_id'].split('-')[1]) for x in item['passage_ids']})
    if item['id'].endswith('figure-makers-and-late'):
        item['lesson_numbers']=[101,102];item['figure_ids']=[f['id'] for f in figures]
ledger=[]
for passage_id,p in passages.items():
    linked=by_passage[passage_id];decision=notes.get(passage_id);retained_ids=retained.get(passage_id,[])
    if linked:
        result='new_claim';reading='；'.join(r['text'] for r in linked)
        atomic=[{'claim_id':r['id'],'conditions':r['conditions'],'exceptions':r['exceptions']} for r in linked]
        inverse='；'.join(r['review_note'] for r in linked)
    elif decision:
        result=decision['category'];reading=decision['reading'];atomic=[];inverse=decision['inverse']
    elif p['role']=='reader':
        result='reader_context';reading='已读提问、署名及引述，限定作者回复对象。';atomic=[];inverse='读者成绩及观点不因作者赞赏而转为作者证据。'
    elif (p['role']=='unknown' and p['text'] in ('缠中说禅回复:','缠中说禅回复：')) or p['text'].startswith('教你炒股票') or re.fullmatch(r'(?:缠中说禅(?:解盘)?[:：]?)?\d{4}-\d{2}-\d{2}.*',p['text']) or re.fullmatch(r'.+\(200[78]-\d{2}-\d{2}\d{2}:\d{2}:\d{2}\)',p['text']) or set(p['text'])=={'*'}:
        result='source_header';reading='文章标题、作者时间或分隔已核。';atomic=[];inverse='只定位原文，不独立支持结论。'
    else:raise AssertionError(('unaccounted paragraph',passage_id,p['text']))
    if linked and decision:reading+='；其余语境：'+decision['reading'];inverse+='；'+decision['inverse']
    ledger.append({'passage_id':passage_id,'lesson_number':int(p['unit_id'].split('-')[1]),'document_id':DOC,'pdf_page':p['pdf_page'],
      'role':p['role'],'speaker':p['speaker'],'published_at':p['published_at'],'source_text_sha256':hashlib.sha256(p['text'].encode()).hexdigest(),
      'result':result,'claim_ids':[r['id'] for r in linked],'related_existing_claim_ids':retained_ids,'existing_evidence_not_mutated':True,
      'pending_issue_ids':[x['id'] for x in pending if passage_id in x['passage_ids']],'reviewer':REVIEWER,
      'rounds':{'1_read_and_scope':reading,'2_atomic_conditions':atomic,'3_normalization':{'concept_labels':sorted({x for r in linked for x in r['concepts']}),
      'related_existing_claim_ids':retained_ids,'note':'二买一般抬高另有合一/低于一买两支；唯一分解为作者主张并列84入口前提，60分钟图参考框架与明确纠正不抹掉旧日期状态。'},'4_reverse_check':inverse}})
for f in figures:
    key=(f['pdf_page'],int(f['id'].rsplit('fig',1)[1]))
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=figure_notes[key],
      figure_source_review='六图已核：三后加、三未核见stage-c-l101-l102-figure-applied.json；366图属103，不计本课图；正文独立支持，不倒填确认。',
      linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger)==161 and len({x['passage_id'] for x in ledger})==161
def dump(suffix,data):
    (OUT/f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x,ensure_ascii=False,separators=(',',':')) for x in data)+'\n',encoding='utf-8')
dump('reviewed.jsonl',rows);dump('coverage.jsonl',ledger);dump('pending.jsonl',pending);dump('figures.jsonl',figures)
summary={'stage':'C','schema_version':metadata['schema_version'],'graph_version':metadata['graph_version'],'lessons':[101,102],'document_id':DOC,'reviewer':REVIEWER,
 'passages_read':161,'claims':len(rows),'evidence':sum(len(r['evidence']) for r in rows),'importance_counts':dict(Counter(r['importance_level'] for r in rows)),
 'new_concepts':sorted({x for r in rows for x in r['concepts']}-set(concepts)),
 'whole_lesson_semantic_read_complete':True,'technical_extraction_complete':False,'four_round_review':True,'independent_review_claimed':False,
 'visual_pdf_pages':list(range(353,367)),'figure_objects_viewed':6,'adjacent_figure_viewed':{'id':DOC+'-p0366-fig1','unit':'lesson-103','counted_in_batch':False},'figure_origin_counts':dict(Counter(f['origin_status'] for f in figures)),
 'pending':[x['id'] for x in pending],
 'source_passages_snapshot_sha256':SOURCE_SHA,'retained_source_links_in_ledger_only':True,'database_mode':'ro','formal_import':False,
 'acceptance':'161段四轮审读、14页6本课图及1邻课边界图；二买三式、唯一性主张、图参考框架及明确纠正分层，增量待预检发布。'}
(OUT/f'{BASE}.summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
db.close();sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(summary,ensure_ascii=False))
