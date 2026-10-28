"""Materialize the manually read lower 85--87 batch; SQLite is read-only.

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
BASE='c_stage_l085_l087'
REVIEWER='Codex 主代理 / 阶段C下册85至87课同模型四轮复核'
SOURCE_SHA='9ee16cb55ff17aef3ff0dc0934ce9c335534c00459a4753ab8e9f4e7cba01400'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
db.row_factory=sqlite3.Row
metadata={r['key']:json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version']=='1.1.0'
assert hashlib.sha256((KB/'sources/volume_2.pdf').read_bytes()).hexdigest()=='5332cd1b60381c47ceb81358db6bbb47882efd074fc5c869dcc3002aaed1b5c0'
passages={r['id']:dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id BETWEEN 'lesson-085' AND 'lesson-087' ORDER BY pdf_page,block_index,id")}
assert len(passages)==219
assert hashlib.sha256(json.dumps(sorted(passages.values(),key=lambda p:p['id']),ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==SOURCE_SHA
old={r['id']:dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts={r['label']:dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical={label:r['label'] for r in concepts.values() for label in [r['label']]+json.loads(r['aliases'])}
figures=[dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 221 AND 239 ORDER BY pdf_page,id',(DOC,))]
assert len(figures)==4
rows,pending,notes=[],[],{}
retained=defaultdict(list)

def pid(short):
    page,block=short.split('-',1)
    return f'{DOC}-p{int(page):04d}-{block}'

def ev(short,quote=None,figs=()):
    p=passages[pid(short)]
    clean=re.sub(r'(?:\*+)?(?:2007-\d{2}-\d{2}\d{2}:\d{2}:\d{2})$','',p['text']).rstrip('*')
    quote=clean if quote is None else quote
    start=p['text'].find(quote)
    assert start>=0 and p['text'][start:start+len(quote)]==quote,(short,quote)
    return {'passage_id':p['id'],'quote':quote,'quote_start':start,'figure_ids':[f'{DOC}-p{n:04d}-fig{k}' for n,k in figs]}

figure_notes={
 (223,1):'上证日线光标10/23、行情至12月，后期图不认证当日预测；图内5860.59—5912.50区间不补成正文新规则',
 (228,1):'30分钟光标10/25、行情至10/26，内嵌最恶劣颈线反抽情景；6123.64与正文6124.04不同，保留原数',
 (232,1):'30分钟光标10/30、行情至11/01，显示5555线和上下降通道；不能倒填10/30新中枢已形成',
 (236,1):'1分钟图187—196、191高6004.79，189—192中枢、194—195回抽；数据至11/02，正文同日，绘者仍未核'
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
    pending.append({'id':'lower-l085-l087-c-stage-pending-'+slug,'status':'pending','passage_ids':[pid(s) for s in shorts.split()],
                    'description':description,'suggested_action':action,'blocks_full_semantic_extraction_completion':blocker,'reviewer':REVIEWER})


# Manually selected after sequential reading of all 219 passages and 19 pages.
c(85,'index-and-stock-top-complexity','222-b008 222-b009 222-b010','作者认为大盘顶因参与分力更多，通常图形更复杂、最后破位前犹豫较多，顶部过程中板块个股仍可能轮动；个股顶大多较简单，但多人参与的大型股为例外。','顶|市场分力|市场合力|板块轮动',3,'通常、大多和大型股例外保留，不能以形状复杂单独判定大盘已见顶。',exceptions=['很多人参与的大型股票，其顶部可类似大盘较复杂'])
c(85,'top-level-and-future-development','222-b011','顶部有级别，中期顶部可在中期调整后不再是顶部；其后是否发展为更严重下跌须由后续走势决定，作者要求分清级别并按买卖点处理。','顶|级别|调整|买卖点',2,'中期调整后不再是顶部是相对于后续发展的语境，不抹去历史顶端；不能把所有顶部视为永远不再新高。')
c(85,'forces-still-show-points','222-b012 223-b000','作者主张无论庄家或大资金采用何种手法，最终合力仍表现为买卖点，连其本人也不能逃避；读者不必先知道幕后故事才能看走势。','市场合力|市场分力|买卖点|主力资金',3,'这是作者理论立场，不是对匿名故事、账户成绩或任何操纵不可影响走势的独立证明。')
c(85,'oct23-rebound-phase-exception','223-b003','在10月23日做顶解盘中，作者区分做顶过程中的反弹与顶部完全形成并破位后的反弹：前者有其所述空头抢反弹用途，后者一般无此必要，除非有特别大级别买点。','反弹|顶|买点|操作级别',2,'空头做顶语境与散户参与资格分开，不把任意反弹同等处理；这是历史分析，不编成操纵流程。',['2007年10月23日作者所述做顶与破位阶段'],['顶部形成并破位后仍有特别大级别买点'])
c(85,'oct23-capability-standard','223-b005 223-b006','作者明确把10月23日反弹讨论限定给当时技术尚可者，标准为“空仓或者目前的市值比6124.04点那天高”；节奏已错者应先调整。','操作熟练程度|反弹|仓位',3,'空仓与市值较高是原文或条件，不能改成两者同时满足；6124.04只作当次基准，未核真实账户。',['2007年10月23日该次反弹讨论'])
c(85,'oct23-five-ten-line-sell-case','223-b002 223-b007','10月23日作者把1分钟下跌底背驰、3600起上升通道下轨及缺口作为当次反弹背景，列5日线、10日线依次为压力；若两线都不能突破，称该反弹将构成第二类卖点。','背驰|反弹|均线|第二类卖点|缺口',4,'两线与该次背景一并保留，不用均线突破替代所有二卖的正式定义；后期日线结果不认证当日预言。',['2007年10月23日反弹例','5日与10日线都不能突破时的条件结论'],figs=((223,1),))
c(85,'oct24-center-third-points-branches','224-b005 224-b009','10月24日10日线阻截下形成1分钟中枢后，作者以该中枢三类点分支判断短线：有三买则再次冲击6000，有三卖则需要二次探底。','走势中枢|第三类买点|第三类卖点|反弹',4,'三买、三卖尚为条件分支，不把当时未出现信号写成已确认，也不推广6000为普遍目标。',['2007年10月24日该1分钟中枢'])
c(85,'oct24-rebound-various-paths','224-b009 224-b010','作者说反弹也可二次探底后再展开，反弹类型选择很多，10月24日当次判断仍依据该1分钟中枢震荡。','反弹|中枢震荡|走势中枢',3,'反弹预期并不排除先下行，不能凭预期跳过三类点条件。',['2007年10月24日该次反弹分析'])
c(85,'oct24-news-and-box-exception','224-b011','作者在10月24日历史判断中称指数最后破位须消息配合，无消息最多箱体；但明确保留箱体持续太久、使参与者恐惧也可能破位的例外。','政策风险|市场心理|突破',4,'不能把历史消息判断写成任何市场破位都必须有新闻的逻辑定理；箱体延长的例外不能省略。',['2007年10月24日指数所处箱体语境'],['箱体延长太久使参与者恐惧时也可能破位'])

c(86,'no-fixed-start-result-formula','224-b013 224-b014 225-b000','作者反对把其理论当作同一起点必有同一结果的永恒固定公式，理由是走势为参与者心理合力痕迹，参与者心理及影响因素不能百分百复制。','市场心理|市场合力|走势预测|技术分析',1,'记录作者对理论应用的边界，非对所有科学可重复性的外部证明；原句9月30日开盘四小时不静默修正日期。')
c(86,'third-sell-in-larger-upshift','225-b002 225-b003','大级别中枢上移时，小级别三卖主要是警戒：看其后走势是否会改变大级别上移；作短差时也只是小级别中枢震荡中的操作点。','第三类卖点|中枢上移|中枢震荡|操作级别',1,'不能把小级别三卖直接等同大级别卖点或上移结束，也不把警戒改成可无视。',['大级别中枢上移中的小级别第三类卖点'])
c(86,'third-sell-in-larger-downshift','225-b004','大级别中枢下移时，小级别三卖须看是否延续该下移；若延续，作者认为此处没有所述做多操作价值，较好的大级别卖出机会此前已给出，并明确把卖空另算。','第三类卖点|中枢下移|操作级别',1,'没有操作价值的做多/卖出语境不能扩大为卖空也无价值，卖空例外保留。',['大级别中枢下移','小级别三卖使该下移继续'],['有卖空操作的情形另算'])
c(86,'third-sell-in-larger-oscillation','225-b005','大级别中枢震荡时，小级别三卖的关键是是否延伸出大级别三卖；无此危险则主要为短线震荡机会，且小三卖后可能反而延伸出大级别买点。','第三类卖点|买点|中枢震荡|操作级别',1,'可能形成大买点不是必然反转，判断须保留更大结构及三卖延伸风险。',['大级别中枢震荡中的小级别第三类卖点'])
c(86,'stop-loss-own-theory-stance','225-b006 225-b007','作者说其理论不用“止蚀”概念，而以三类卖点及不同级别卖点的先前机会作处理；邻文同时说明突破、止蚀位置被轮番触及时会使不同操作节奏错乱。','买卖点|操作策略|市场震荡',3,'这是作者体系自述，不推出任何账户都应拒绝风险管理，亦不把没有止蚀改成没有卖出条件或容许无限亏损。')
c(86,'big-buy-small-buy-nesting','225-b008 225-b009 225-b010','大买点后的小买点往往是第二次介入机会，但不一定最精确；作者称最精确须符合区间套，并非任意小买点都在原大买点的区间套中。','买点|区间套|操作级别',1,'第二次介入机会不等于正式第二类买点，先后次数与买点类型不能混淆。',['先有大级别买点、后有小级别买点'])
c(86,'small-buy-break-large-structure-intact','225-b010 226-b000','大买点后的小买点可以被小级别波动跌破；作者断言只要没有破坏原大买点所构造的大级别结构，之后仍会有小级别波动回到该小买点之上，小买点只是构造大结构的支架。','买点|走势级别延续|边界条件|操作级别',1,'结构不破为必要限定，不把单个小买点不失守当作原文承诺；未给本条结构破坏数值阈值。',['先有大买点、后有小买点','原大买点构造的大级别结构未被破坏'])
c(86,'big-sell-small-sell-reverse','225-b010 226-b001 226-b002','对“大卖点后小卖点”，作者只明确说把“大买点后小买点”的情形反过来理解。','卖点|买点|操作级别|区间套',2,'保留显式反向指示及所指前段，不自行补出未定义的反向数值算法；不是整理推论冒充逐字原话。',['先有大卖点、后有小卖点'])
c(86,'big-buy-small-sell-intermediate','226-b003 226-b004','大买点后小卖点，若两点间有大卖点则归入“大卖点后小卖点”；若没有，小卖点后的小级别走势用于再考验大结构，结构不破时后续小买点往往有大能量。','买点|卖点|操作级别|能量结构',1,'中间大卖点分支、结构不破和往往均保留，不能凭先后标签保证任何后续小买点获利。',['大买点后出现小卖点','无中间大卖点分支中，考验走势不破坏原大结构'])
c(86,'big-sell-small-buy-reverse','226-b004 226-b005','对“大卖点后小买点”，作者明确指示按上一项“大买点后小卖点”反过来理解。','买点|卖点|操作级别|能量结构',2,'仅转述作者反向指示及指代，不另造程序；上一项的中间同级转折与结构不破条件不能因反向而消失。',['先有大卖点、后有小买点'])
c(86,'inside-large-center-not-large-points','226-b006 226-b007','作者说一个大中枢内部没有其大级别买卖点，因为出现该级别第三类买卖点意味着该中枢被破坏；内部的小买卖点制造中枢震荡。','走势中枢|中枢破坏|中枢震荡|第三类买卖点|操作级别',1,'这里的没有限于该中枢内部，不说全市场无买卖点；同段一般不具有小级别操作意义的原字有衔接疑点，单列待核而不偷改大字。',['所论大中枢内部与同级别第三类买卖点'],ambiguity='small_level_significance_wording')
c(86,'next-level-points-two-paths','226-b008','大中枢震荡中的次级别买卖点可具有大级别操作意义，作者举5分钟震荡里的1分钟点：之后或继续5分钟震荡，或次级别离开、回抽形成三类点。','中枢震荡|次级别|第三类买卖点|操作级别',1,'次级别而非任意更小级别；离开加回抽顺序和两支保留，不把尚未回抽视为已确认三类点。',['大级别中枢震荡中恰为次级别的买卖点'])
c(86,'analogy-not-large-first-second','226-b008','在次级别点后离开原中枢并回抽成三类点的分支，作者比喻原点像一类点、随后三类点像新走势的二类点，同时明确声明它们并非大级别真正第一、第二类买卖点。','类买卖点|第一类买卖点|第二类买卖点|第三类买卖点|次级别',1,'比喻否认身份的括注必须一起显示，不能把操作意义提升误写为形式级别或类别升级。',['第86课大中枢次级别点后离开、回抽的比喻分支'])
c(86,'first-center-third-last-opportunity','226-b009','以1分钟下跌趋势为例，作者称第一个中枢三卖是最后合适卖出机会，第二中枢以后三卖操作意义小，此时应注意趋势是否结束、是否有底背驰而转向考虑买点。','第三类卖点|趋势|背驰|操作级别|中枢下移',1,'两个中枢不充分保证背驰或马上结束；这里是在该下跌趋势中的卖出取舍，不否定三卖的形式存在。',['第86课1分钟下跌趋势例的该级别操作'])
c(86,'post-divergence-first-leg-sell','226-b010','1分钟下跌最终背驰转折后，第一上行线段的卖点可能恰成最后1分钟中枢三卖；对该次抄底，作者认为其操作意义很小，反而应看下来的第二类买点。','背驰|趋势转折|第三类卖点|第二类买点|线段',1,'前提是所述最终背驰转折，可能恰成不是必然；不将原中枢任意三卖当无须处理。',['1分钟下跌最终背驰转折后的第一次上行'])
c(86,'bottom-then-one-minute-consolidation','226-b010 226-b011','在抄1分钟底的语境中，作者称后面最坏仍有1分钟盘整，并批评连最基本三个线段尚未形成就退出。','盘整|走势终完美|线段|操作级别',2,'该说法依赖前段已识别1分钟最终底背驰；三段是此处最低结构提醒，不是任意三线段就构成盘整的充分定义。',['已按前段识别1分钟下跌的最终底背驰'])
c(86,'second-buy-entry-program','226-b012 227-b000','对大级别背驰判断没信心者，作者给二买介入程序：一买后次级别上去，再以次级别回跌，只要不破一买位置就介入，可不单独处理二买形成中的背驰。','第二类买点|第一类买点|次级别|背驰',1,'一买存在、次级别上去及回跌、价位不破须联合；不是任何任意低点反弹未创新低均为二买。',['已经有第一类买点','其后次级别上去并次级别回跌','回跌不破第一类买点位置'])
c(86,'second-buy-followup-exit-program','227-b000','上述二买程序介入后，作者要求看下一个次级别上行：不破第一个次级别上行高点便卖，破则持有并等三买，有三买继续持有、没有则卖。','第二类买点|第三类买点|次级别|高低点|操作策略',2,'保留下一个次级别的判定语境，不能在尚未走完的任一瞬时未过高点就宣称失败；原文未在此给完整实时确认时点。',['第86课一买后次级别回跌不破的二买介入程序'],ambiguity='next_sublevel_completion_timing')
c(86,'decomposition-key-program','227-b000 227-b001','作者称按上述形态与次级别程序可不单独使用背驰概念，重点是分清走势类型，其他概念用于增强。','走势类型|背驰|操作策略',2,'这是该程序的范围，不说一买可以完全没有定义依据，也不删掉前段次级别、价位与三买条件。',['第86课所述二买介入及其后处理程序'])
c(86,'oct25-third-sell-not-top-confirmation','227-b011 227-b012','10月25日低开后第一小时反抽，作者认定为前1分钟中枢三卖，但强调其后二次探底并不等于顶部已完全成立，仍预期资金解冻及周末消息明朗后的反弹。','第三类卖点|确认|顶|反弹',4,'当时已识别的小三卖与尚未确认的大顶同时保存，不能从三卖直接跳成顶部确认。',['2007年10月25日当次1分钟中枢及二次探底'])
c(86,'oct25-neckline-alternative-scenarios','227-b013 228-b000 228-b001','10月25日作者列颈线约5555的两种情景：恶劣支先跌5300甚至5000、反抽不过5555才确认顶并预期4000或更低；较好支假破颈线再收回，甚至可能再冲6000。','颈线|确认|假突破|反弹|顶',4,'全部为该日情景，不是均已发生；5300/5000/4000及6000为历史预期而非通用阈值。',['2007年10月25日5555颈线情景'],figs=((228,1),))
c(86,'oct30-third-buy-two-meanings','231-b013 231-b014','作者把10月30日下午跳水同时解释为下降通道上轨突破后的回抽，以及昨日尾盘和当日早盘形成1分钟中枢的第三类买点。','第三类买点|反抽|走势中枢|突破',4,'两套工具指向同一次回抽的作者解释，不以该后期图确认每根K线端点。',['2007年10月30日通道与1分钟中枢案例'],figs=((232,1),))
c(86,'oct30-new-center-required-uptrend','231-b015 232-b000','10月30日作者说，若不回到原1分钟中枢而在上面形成新中枢，则反弹至少为1分钟上涨，随后等待背驰。','中枢上移|走势中枢|上涨|背驰|完成',1,'不回原中枢与上方新中枢形成须同时满足，未来条件不当作当日新中枢已经完成。',['2007年10月30日所述原1分钟中枢','不返回原中枢且在其上形成新的同级中枢'])
c(86,'oct30-neckline-unbroken-potential','232-b002 232-b003','10月30日作者说无论最终顶图形是哪一种，只要5555未有效跌破，图形尚未完成且可能成为中继；有效跌破则认定顶部和中级调整成立，期货时间是其当时列出的变数。','颈线|有效跌破|确认|顶|调整',2,'未有效跌破不保证必创新高，中继仅为潜力；数值和期货预期均限当次，不把5555用于别的行情。',['2007年10月30日所论5555颈线'],figs=((232,1),))

c(87,'cost-zero-stories-stance','233-b004 233-b005 233-b006 233-b007 233-b008','在自称“梦话”的庄家故事中，作者强调筹码、资金、足够时间及影响走势的分力，并以降低成本而非账面市值为核心，自述零成本后再运作可成负成本。','成本|主力资金|市场分力|资金管理',3,'梦话故事和足够资源为范围；所谓最安全是作者说法，无账户或外部验证，不由此认证零成本绝无风险或任何人都能摊低成本。',['第87课作者以梦话标识的庄家故事','作者所述筹码、资金、足够时间及较强分力前提'])
c(87,'oct31-new-center-still-unformed','234-b010','10月31日作者明确说新的1分钟中枢当天仍未形成，若次日有所回落才形成，形成后再看三类点。','走势中枢|完成|确认|第三类买卖点',1,'标题形成ing不等于已完成；此条可反核30日条件句，后期30日图不能倒填完成。',['2007年10月31日新1分钟中枢状态'])
c(87,'nov1-center-three-segments-case','235-b004','11月1日作者称早上背驰后形成1分钟中枢第二段、回跌成第三段，因此该中枢形成，随后围绕其震荡并等待三类点。','走势中枢|背驰|中枢震荡|第三类买卖点|完成',2,'同一实际对象的第二第三段和背驰时间顺序保留，不将所有任意三段当作中枢成立充分条件。',['2007年11月1日该1分钟中枢'])
c(87,'nov2-195-third-sell-and-analogy','235-b011','11月2日作者把195判为189—192的1分钟中枢三卖；相对于191起线段类下跌，194—195又是第二个类中枢，此后跌破力度不足、出现明显背驰并在该处形成新1分钟中枢。','第三类卖点|类中枢|类背驰|走势中枢|线段',1,'同一处的严格1分钟中枢和线段类结构分开；原句此处说背驰，所述比较对象为线段类下跌，不把两类中枢混作同级或以此改掉严格最低级别条件。',['2007年11月2日189至195案例'],figs=((236,1),))
c(87,'nov2-new-center-continuation-five','235-b012','11月2日新1分钟中枢形成后，作者要求看有无三卖以判断是否继续下延1分钟下跌，并认为此次反弹调整从大处至少向5分钟级别扩展。','第三类卖点|中枢下移|小级别转大级别|调整',2,'新中枢三卖尚待观察；当次向5分钟扩展是历史结构判断，不说任意两个1分钟中枢自动升级。',['2007年11月2日该次反弹调整'])
c(87,'nov2-191-193-different-perspectives','235-b013 236-b000','对这次调整的该级别卖出，作者把191称一卖（此前线段类上涨类背驰）、193在线段角度称二卖；在189—192的1分钟中枢震荡角度，次级别向上离开先为卖点，再看回跌是否成三买回补。','第一类卖点|第二类卖点|类背驰|中枢震荡|第三类买点|次级别',1,'191/193的线段角度与1分钟震荡角度不同，不将二者改成大级别形式类别或抹去先卖后看三买顺序。',['2007年11月2日所述191/193及189—192中枢'],figs=((236,1),))
c(87,'nov2-late-sell-only-probability','236-b001','作者说195之后针对该次调整再卖已迟，随时可能下跌结束；虽仍可能继续跌，那只是概率问题，不能再以理论100%保证。','第三类卖点|趋势转折|概率原则|操作级别',1,'不把太迟改成绝对不可能续跌，也不把100%否定扩成作者承认所有理论条件均随机。',['2007年11月2日该次调整、195三卖以后'])
c(87,'nov5-new-stock-first-down-segment','237-b001 237-b003','针对高开低走新股，作者要求第一笔介入至少等第一下降线段结束；还须分批，因为线段级别太短，不能保证T+1的绝对安全。','线段|次新股|交易规则|仓位|市场风险',1,'第一笔是第一批介入，不是结构笔；结束与分批是必要要求，不保证满足后获利或无风险，限该高开低走新股语境。',['高开低走的新股操作讨论','第一下降线段已经结束'])
c(87,'nov5-petro-417-not-safe-floor','237-b001 237-b002','作者在11月5日中石油例称48多至41.7为下降线段、其后转向上，但提前在41.7段结束介入不能保证次日无下降线段跌穿41.7，尤其受T+1约束。','线段|交易规则|市场风险|次新股',1,'历史价位、段结束与次日仍可能跌破同时保留；不能把第一段低点作绝对安全底。',['2007年11月5日中石油41.7案例'])
c(87,'nov5-staged-holding-hedge-author','237-b002 237-b003','该新股案例中，作者称较稳健作法是在下降段结束时介入部分，1分钟中枢形成后按位置补其他仓位，以便作其所称T+0对冲；邻段仍强调线段太短、T+1无绝对安全。','动态建仓|仓位|对冲|交易规则|市场风险',2,'至少保证仓位安全是作者该段主张，未认证零风险；原文未给可通用于任何账户的结算实现，不能将T+0对冲改成当日买入全仓必可卖。',['2007年11月5日新股案例的分批及中枢形成后处理'],ambiguity='hedge_safety_scope')
c(87,'nov6-second-top-not-confirmed','237-b009 237-b010','11月6日早文称6100为当次中期顶部一尖，6004是否第二尖还要有效跌破5555颈线才确认；此前仍按中枢震荡，上行背驰出、回跌不破5555可回补，等最终方向。','颈线|确认|中枢震荡|背驰|顶',2,'6004此刻为待确认，不用后见图补成已确认第二尖；回补与不破条件同时保留。',['2007年11月6日早文中6100/6004与5555颈线'])
c(87,'nov6-index-versus-stock-types','238-b000 238-b001 238-b002 238-b004','作者在11月6日中石油及期货预期语境下认为指数失真加大，需分清中字头、接近完成收集的题材股、仍需收集的股票，并对照个股相对指数的特点选择思路。','指数走势背离|板块轮动|题材股|主力资金|操作策略',3,'三类是当时作者市场分析，不是从价格唯一反推庄家库存；期货当时仍为变量，不写成已经推出。',['2007年11月6日指数与个股分化讨论'])
c(87,'nov6-december-window-conditional','238-b003','作者11月6日把当年12月称30月时间之窗：若前后出现低点，预期次年行情展开；若高点则次年初压力较大，这是其希望压制指数以低点触窗的理由。','走势预测|经济大势|市场心理',4,'仅保存作者有条件的历史时间窗判断，不认证其效果，不用时间窗换算走势级别。',['2007年11月6日对2007年12月的预测'])
c(87,'nov6-neckline-three-days-buffer','238-b006 238-b007','11月6日5555争夺战解盘中，作者说一般这样的胜负至少看3天，上下另有3%的缓冲，并举5555×97%让读者计算。','颈线|有效跌破|确认|价格区间',2,'至少3天与上下3%为当次一般经验，未说明连续收盘、盘中触价或严格联合判据，不扩成所有走势有效突破统一算法。',['2007年11月6日5555颈线争夺战'],ambiguity='case_buffer_not_universal_algorithm')
c(87,'nov6-neckline-force-downshift','238-b009 238-b010','作者从当时空头立场强调有杀伤力的颈线突破需三卖后中枢下移，若反而构成大中枢则力度小；快速破颈线也可能是假破。','颈线|第三类卖点|中枢下移|中枢扩展|假突破',2,'所需的是其空头目标中的破位力度，不把所有颈线突破形式定义为必有三卖中枢下移，也不认证其实际控制市场。',['2007年11月6日作者所述空头期待的颈线突破力度'])
c(87,'nov6-only-one-force','238-b011','作者明确说自己只是分力，最终颈线走势能否如愿并非自己一人决定，其他空头急切破位还可能反入多头埋伏。','市场分力|市场合力|主力资金',3,'与其控盘轶事并列，不据叙事宣称作者可单人任意决定市场；原句没有提供实际订单证据。',['2007年11月6日颈线博弈自述'])
c(87,'nov6-petro-class-third-not-strict','239-b000','11月6日作者把中石油反弹到41.2称为相对41.7上方类中枢的类第三类卖点，之后线段下跌，仍等待类背驰；若出现，预期反弹级别大于此前线段反弹、至少可T+1操作。','类中枢|类买卖点|类背驰|线段|交易规则',1,'类中枢、类三卖、类背驰不可升级为严格最低级别中枢三卖；背驰尚待出现，可T+1是当时预期，不等于保证盈利。',['2007年11月6日中石油41.2及41.7类结构','类背驰出现后的反弹结论为条件预期'])
c(87,'nov6-short-rebound-not-t1-profit','237-b003 239-b000','作者明确区分有线段反弹与可T+1赚钱：有些线段反弹未必能按T+1获利，并以11月6日中石油作为前日风险提醒的例证。','反弹|线段|交易规则|市场风险',1,'能看见小级别反弹不充分保证结算时仍有利润，未核成交、费用或账户成绩。',['第87课新股及中石油小级别反弹的T+1语境'])

# Existing claims are navigation references, not substituted evidence.
keep('225-b003 225-b004 225-b005','lower-l081-c-stage-levels-compatible-constraints','81课多级别联立约束与此课三种大背景一起保留；小三卖不会自动成为大三卖。')
keep('225-b010','lower-l065-interval-nesting-below-segment','65课精细定位与实际成交/成本边界保留；本课区间套不是任意小点。')
keep('233-b005 233-b007 233-b008','lower-l065-zero-cost-add-shares-author-strategy lower-l067-buy-point-relative-zero-cost-safety','零成本策略的较早出处与相对安全原话仍在；梦话故事不自动修订为绝对安全。')
keep('239-b000','lower-l064-line-below-center-is-analogy','64课严格最低结构与类结构边界保留；41.2类三卖不升级为正式三卖。')

issue('small-level-wording','226-b007 226-b008','原页226确写大中枢内小点一般不具有小级别操作意义，下一段又说次级别点可有大级别意义；是否作者笔误或具体操作范围未被本汇编勘误。','保留原字及相邻段，发布结构和显式例外；不静默把小改成大。',True)
issue('next-sublevel-time','227-b000','二买后处理写下一个次级别不破前高则卖，未在这里定义何时确认该次级别已完成或不破。','与既有走势完成规则对照；不把未走完任一时点不新高当实时卖出充分条件。',True)
issue('three-segments-minimum','226-b011 235-b004','本课三个线段/第三段是已识别特定底与中枢的语境，不重述重叠区域全部定义。','联查正式中枢定义，不能生成任意三个线段必构中枢的简化规则。')
issue('stories-and-performance','221-b008 221-b009 222-b002 222-b004 222-b005 233-b004 233-b008','85/87自称梦话的匿名案例含合法性、70%上涨、90%下跌、零负成本及最安全等自述，底本不能验证股票、账户或法律结论。','保存故事身份与原文，非知识库实测收益或现行法律判断；不推断匿名股票和人物。')
issue('figure-makers-and-late','223-b007 228-b001 231-b014 235-b011','4图均看过，223/228/232可见文后行情，236绘者未核；图峰6123.64/6124.04及6004.79/6004差异不能擅改。','三图登记后期，236维持未核；仅以正文支持命题，不用后见标记或图上精度倒填当时状态。')
issue('hedge-safety','237-b002 237-b003','同组文字既称分批T+0对冲可保证安全，又称线段太短不能保证T+1绝对安全，仓位与时间范围及保证含义未完整量化。','两句并列及分批前提保留；不将作者保证改成工程验证，也不写成普遍无风险策略。',True)
issue('neckline-confirmation-scope','232-b003 237-b009 238-b007 238-b010','11月6日给5555争夺战至少3天及上下3%缓冲，未说明是否普遍适用、收盘还是盘中、3天与3%如何合用；也没有明确给所有有效跌破的统一定义。','该例经验可查，保留与三卖后中枢下移力度目标的区别；仅补充早批待核的具体例，不全面解除旧待核。',True)

note('221-b008 221-b009 221-b010 221-b011 221-b012 221-b013 222-b000 222-b001 222-b002 222-b003 222-b004 222-b005 222-b006 222-b007','self_reported_story','梦话标识、匿名持仓30%多/老鼠仓10%、筹码调动、传闻、透支、分批出货、三周涨70%及后跌90%全部已读。','保留作者轶事和自称合法的来源；未核交易、当时法律或人物，不改写为可执行操纵手册、普遍绩效或客观清白证明。')
note('223-b004','strategic_metaphor','下棋、须有大想法和后手的比喻。','不以稳胜不败比喻认证实际无风险收益。')
note('223-b008 224-b000 224-b001 224-b002 224-b004 224-b006 224-b007 224-b008','historical_session_context','中石油上市预期、中字头/题材轮动、站岗换班、香港会面、资金解冻、指数无赚钱效应与消息诱因已读。','仅2007年10月23/24历史自评与预测，未核实际资金流；反弹风险及特定中枢分支另抽。')
note('225-b001','learning_scope','看1分钟不能把眼界锁死在1分钟的提醒。','不是以100年固定时长定义学习或级别升级；具体多级别条件另抽。')
note('225-b006','market_behavior_context','突破和止蚀反复触碰使不同操作模式节奏错乱的说明。','作为作者市场行为解释，不制成针对别人止损的操纵流程。')
note('227-b002 227-b003 227-b004 227-b005 227-b006','off_topic_personal_account','回家、剪彩邀请劳务费、名节感慨及课程86是否重复发布的作者自述完整读。','无新增缠论结构；不猜人物或认证贿赂法律事实，不因是否帖过自疑改变课程身份和底本时间。')
note('227-b008 227-b009 227-b010 228-b002 228-b003 228-b004 228-b006 228-b007','historical_policy_and_self_assessment','月圆、宏观调控回应、经济大局、反弹能力门槛、作者大胜及9月17剧本自评已读。','行情自评不认证因果及收益，历史原帖在该处引用非独立校对；核心顶部未确认与情景另抽。')
note('229-b000 229-b001 229-b002 229-b003 229-b004','quoted_historical_forecast','10月25日重引9月17日的2675.47、130.43%、6165及6100类比、疯狂资金和超530调整条件。','来源日期是当前再引用文章，不冒充原帖逐字独立核验；比例历史预期不升级为中枢结构规则。')
note('229-b005 229-b006 229-b007 229-b008 229-b009 229-b010 229-b011 229-b012 229-b013 229-b014 229-b015 229-b016 229-b017 230-b000 230-b001 230-b002 230-b003','historical_macro_opinion','中国长期牛市、GDP总市值、升值、资本市场与实体经济、20年目标及纠错立场完整读。','全为作者2007年宏观观点或自引，未核经济数据与后验实现；不作为当前金融建议、普遍数学定理或独立预测成绩。')
note('230-b005 230-b006 230-b007 230-b008 230-b009','historical_rebound_conditions','5555支撑反弹、消息例外、解冻资金、中石油表现和技术灵活性要求。','具体颈线/反弹分支已抽，不把无特别消息的预期当保证。')
note('230-b011 230-b012 230-b013 230-b014 230-b015 231-b000 231-b001 231-b002 231-b003 231-b004','historical_futures_stance','国宾馆比喻、327/319、流通量及现货卖空前提、确认年内期货则转多与工行200等修辞已读。','2007年期货尚未推出语境，不认证历史争议和后续法制；条件式夸张不是已成市场事实或现行政策建议。')
note('231-b006 231-b007 231-b008 231-b009 231-b010 231-b011','historical_channel_and_futures_context','10月29通道上轨、5555反弹、期货逼空100000夸张、指数股与其他股分化预期已读。','条件与夸张留原文，不形成无条件目标点、可执行逼空程序或已核仓位。')
note('232-b001 232-b002 232-b004 232-b005 232-b006 233-b000 233-b001 233-b002','historical_policy_responsibility','反弹资金解冻、期货决定中期形状的分支、市场外阻击、327责任及震荡自述。','尚未定局仍尚未定局，不认证作者政策影响力或当时资金规模；5555未有效破位与中继条件另抽。')
note('233-b009 233-b010 233-b011 234-b000 234-b001 234-b002 234-b003 234-b004 234-b005 234-b006 234-b007 234-b008','self_reported_accumulation_story','匿名8至20多旧事及抢筹码、成本、洗老鼠仓、时间四任务；假突破、当日透支平仓、传闻、远处吸筹、平台及15分钟越套牢区的故事逐段读。','保留梦话身份，不补股票/日期/账户，不认证真实获利或合法性，也不转成向现实参与者实施市场操纵的操作序列。')
note('234-b011 234-b012 234-b013 235-b000 235-b001 235-b002','historical_policy_context','九一反弹资金、香港风险提醒、直通车、换刀比喻与绿色字提示已读。','未核香港公告，未来假设不作已发生事实；10月31日中枢未成另抽。')
note('235-b005 235-b006 235-b007 235-b008 235-b009','historical_policy_and_new_stock','无方向等待中石油、美国减息、贱卖回归及市场参与者/管理者责任观点。','不认证利率史、估值或法律责任；作为2007年作者立场。')
note('236-b002 236-b004 237-b000 237-b004 237-b005','historical_petro_and_policy','11月2周末利率传闻和中石油高开风险、11月5市值与全球比较、封闭市场估值、人寿30/100类比、直通车及题材股判断已读。','不验证报价或市值比较，不把可能便宜/买入机会变成现在建议，不认证100目标；作者明确不是100%不再跌。')
note('237-b007 237-b008','personal_schedule_context','PE项目5亿与出差安排、本文中期总结引言。','未核项目与回报，不新增结构定义。')
note('238-b005 238-b008 238-b012 239-b001 239-b002','historical_risk_and_personal_context','操作自负、指数下跌多为中字头但不代表其他股无风险、PE占用时间与市场洞察修辞。','90%未跌及PE价格仅作者说法；颈线真破仍可能使其他股再探底，不把暂未跌当零风险。')

relations={
 'lower-l085-c-stage-top-level-and-future-development':[('顶','级别','related')],
 'lower-l086-c-stage-third-sell-in-larger-upshift':[('第三类卖点','中枢上移','related')],
 'lower-l086-c-stage-third-sell-in-larger-downshift':[('第三类卖点','中枢下移','related')],
 'lower-l086-c-stage-third-sell-in-larger-oscillation':[('第三类卖点','中枢震荡','related')],
 'lower-l086-c-stage-big-buy-small-buy-nesting':[('买点','区间套','related')],
 'lower-l086-c-stage-analogy-not-large-first-second':[('类买卖点','第一类买卖点','distinguishes'),('类买卖点','第二类买卖点','distinguishes')],
 'lower-l087-c-stage-nov6-petro-class-third-not-strict':[('类中枢','类买卖点','related')],
 'lower-l087-c-stage-nov6-short-rebound-not-t1-profit':[('反弹','交易规则','related')],
}
for r in rows:r['relations']=[{'source':s,'target':t,'type':kind} for s,t,kind in relations.get(r['id'],[])]

by_passage=defaultdict(list)
for r in rows:
    for e in r['evidence']:by_passage[e['passage_id']].append(r)
for item in pending:
    item['lesson_numbers']=sorted({int(passages[x]['unit_id'].split('-')[1]) for x in item['passage_ids']})
    if item['id'].endswith('figure-makers-and-late'):
        item['lesson_numbers']=[85,86,87];item['figure_ids']=[f['id'] for f in figures]
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
    elif (p['role']=='unknown' and p['text'] in ('缠中说禅回复:','缠中说禅回复：')) or p['text'].startswith('教你炒股票') or re.fullmatch(r'(?:缠中说禅(?:解盘)?[:：]?)?\d{4}-\d{2}-\d{2}.*',p['text']) or re.fullmatch(r'.+\(2007-\d{2}-\d{2}\d{2}:\d{2}:\d{2}\)',p['text']) or set(p['text'])=={'*'}:
        result='source_header';reading='文章标题、作者时间或分隔已核。';atomic=[];inverse='只定位原文，不独立支持结论。'
    else:raise AssertionError(('unaccounted paragraph',passage_id,p['text']))
    if linked and decision:reading+='；其余语境：'+decision['reading'];inverse+='；'+decision['inverse']
    ledger.append({'passage_id':passage_id,'lesson_number':int(p['unit_id'].split('-')[1]),'document_id':DOC,'pdf_page':p['pdf_page'],
      'role':p['role'],'speaker':p['speaker'],'published_at':p['published_at'],'source_text_sha256':hashlib.sha256(p['text'].encode()).hexdigest(),
      'result':result,'claim_ids':[r['id'] for r in linked],'related_existing_claim_ids':retained_ids,'existing_evidence_not_mutated':True,
      'pending_issue_ids':[x['id'] for x in pending if passage_id in x['passage_ids']],'reviewer':REVIEWER,
      'rounds':{'1_read_and_scope':reading,'2_atomic_conditions':atomic,'3_normalization':{'concept_labels':sorted({x for r in linked for x in r['concepts']}),
      'related_existing_claim_ids':retained_ids,'note':'买卖点操作意义保留大级别环境、先后与结构不破条件；类比与严格定义区分，梦话轶事不作客观绩效。'},'4_reverse_check':inverse}})
for f in figures:
    key=(f['pdf_page'],int(f['id'].rsplit('fig',1)[1]))
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=figure_notes[key],
      figure_source_review='三图后期见stage-c-l085-l087-figure-applied.json；全部绘者未核。',
      linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger)==219 and len({x['passage_id'] for x in ledger})==219
def dump(suffix,data):
    (OUT/f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x,ensure_ascii=False,separators=(',',':')) for x in data)+'\n',encoding='utf-8')
dump('reviewed.jsonl',rows);dump('coverage.jsonl',ledger);dump('pending.jsonl',pending);dump('figures.jsonl',figures)
summary={'stage':'C','schema_version':metadata['schema_version'],'graph_version':metadata['graph_version'],'lessons':[85,86,87],'document_id':DOC,'reviewer':REVIEWER,
 'passages_read':219,'claims':len(rows),'evidence':sum(len(r['evidence']) for r in rows),'importance_counts':dict(Counter(r['importance_level'] for r in rows)),
 'new_concepts':sorted({x for r in rows for x in r['concepts']}-set(concepts)),
 'whole_lesson_semantic_read_complete':True,'technical_extraction_complete':False,'four_round_review':True,'independent_review_claimed':False,
 'visual_pdf_pages':list(range(221,240)),'figure_objects_viewed':4,'figure_origin_counts':dict(Counter(f['origin_status'] for f in figures)),
 'pending':[x['id'] for x in pending],
 'source_passages_snapshot_sha256':SOURCE_SHA,'retained_source_links_in_ledger_only':True,'database_mode':'ro','formal_import':False,
 'acceptance':'219段四轮审读、19页及4图检查；跨级别操作条件和概率范围保留，三图后期，增量待预检发布。'}
(OUT/f'{BASE}.summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
db.close();sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(summary,ensure_ascii=False))
