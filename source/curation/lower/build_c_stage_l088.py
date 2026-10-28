"""Materialize the manually read lower 88 batch; SQLite is read-only.

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
BASE='c_stage_l088'
REVIEWER='Codex 主代理 / 阶段C下册88课同模型四轮复核'
SOURCE_SHA='c1784dde13d7d5dd9c3b8062c56c0fef01eed564915306242deb845f8a0a35ca'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
db.row_factory=sqlite3.Row
metadata={r['key']:json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version']=='1.1.0'
assert hashlib.sha256((KB/'sources/volume_2.pdf').read_bytes()).hexdigest()=='5332cd1b60381c47ceb81358db6bbb47882efd074fc5c869dcc3002aaed1b5c0'
passages={r['id']:dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id BETWEEN 'lesson-088' AND 'lesson-088' ORDER BY pdf_page,block_index,id")}
assert len(passages)==124
assert hashlib.sha256(json.dumps(sorted(passages.values(),key=lambda p:p['id']),ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==SOURCE_SHA
old={r['id']:dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts={r['label']:dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical={label:r['label'] for r in concepts.values() for label in [r['label']]+json.loads(r['aliases'])}
figures=[dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 239 AND 250 ORDER BY pdf_page,id',(DOC,))]
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
 (240,1):'187—196的1分钟案例图，与87课236页同一分析对象；191高6004.79、195三卖，日期至11/02早于11/06课程，绘者未核',
 (245,1):'11/12文章却光标11/13、行情至11/14以后，画5555/5462两颈线；后期截图不倒填未来反抽结果',
 (246,1):'191—214的1分钟图，绿箭头在后续三卖、最低214标5034.11；正文说最晚195、214三重定位，未从图重建内部笔算法',
 (248,1):'日线光标11/13却行情至12月、含4778.73，后期图；5462/5555水平线与5日/月均线正文分层，不用事后走势证实当日预测'
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
    pending.append({'id':'lower-l088-c-stage-pending-'+slug,'status':'pending','passage_ids':[pid(s) for s in shorts.split()],
                    'description':description,'suggested_action':action,'blocks_full_semantic_extraction_completion':blocker,'reviewer':REVIEWER})



# Selected after full source reading and page/crop inspection; no model API.
c(88,'continuation-or-turn','239-b004 239-b005','作者把走势分解的本质归为延续与转折，并用走势类型的生死作比喻：一个类型结束意味着另一类型开始。','走势类型|走势分解|趋势转折|走势延伸',1,'生死为结构比喻，不作生物或宗教实证；也不把转折只限反向趋势。')
c(88,'new-type-establishes-prior-end','239-b006','一个新走势类型确立时，作者同时确认前一走势类型结束；新类型又开始其自身延续到结束的过程。','走势类型|确认|完成',1,'确立与刚出现反向波动不同；没有在本句给出任何固定时间的确立判据。')
c(88,'intermediate-stage-definition','239-b007 241-b005','作者把前一走势类型背驰或盘整背驰后、到新走势类型确立前的过渡比为中阴身阶段，后文称中阴阶段。','中阴阶段|走势类型|背驰|盘整背驰|确认',1,'保留旧类型结束到新类型确立的两端；这是该课借喻的市场术语，不以宗教中阴身含义解释价格。',['前一走势类型背驰或盘整背驰后','新的走势类型尚未确立'])
c(88,'intermediate-reference-old-part','239-b008','分析中阴阶段须结合前段走势的部分结构；作者用业力比喻旧结构的作用与当下新合力共同影响最终方向。','中阴阶段|走势分解|市场合力|走势类型',1,'部分前走势与新合力并用，不能机械丢弃转折点前全部信息，也不把业力作为额外可测物理量。',['中阴阶段走势分析'])
c(88,'191-193-reference-189-center','239-b010 239-b011','第88课案例中，191背驰后从191分析新走势，但到193新类型轮廓仍不清，应借189起中枢；193可叫二卖，同时也是旧中枢震荡的一部分，为192/193及后续提供分析依据。','中阴阶段|走势中枢|中枢震荡|第二类卖点|走势类型',1,'线段类案例与严格1分钟类型分层，193二卖不取消对旧中枢的参照；本条只定位该图的189/191/193。',['第88课189至195案例'],figs=((240,1),))
c(88,'195-boundary-class-line','239-b012 240-b000','该案例195三卖是中阴与新类型初始形态确立的分界，此后至少为线段类下跌，分析重心可转191起新走势，在该线段层次基本不再依赖191之前。','中阴阶段|第三类卖点|类中枢|走势类型|线段|确认',1,'基本不再依赖仅限该线段层次；原文线段级别是该例简称，不取消64课严格最低级别；195分界不推广成任意三卖即结束任意级别中阴。',['第88课191起线段类案例','195第三类卖点已经出现'],figs=((240,1),),ambiguity='case_class_line_vs_formal_type')
c(88,'old-structure-persists-higher','240-b001','191之前的走势仍在1分钟、5分钟等更大层次发挥作用，191之后的走势须与之前结合成大级别形态。','级别|走势类型|走势分解|中阴阶段',1,'在小层次转移重心不等于全级别删除前史；1分钟5分钟是本例所列层次。',['第88课195以后与191前后结构的比较'])
c(88,'compress-marks-after-completion','240-b002','按1分钟级别操作且已熟练者，可把此前191个线段号简化为不足10个1分钟相关号；191后新1分钟走势结束才再增一个标记，更高级别标记还可更少。','线段|操作级别|完成|走势类型|级别',2,'191和不足10是示例而非固定压缩比；必须相应1分钟走势结束，不按时间或新增一线段就添一个1分钟号。',['熟练者按1分钟级别操作','新1分钟走势结束后才增加对应标号'])
c(88,'level-mark-notation','240-b003','作者建议用Xn标线段、Yn标1分钟、Wn标5分钟、Sn标30分钟，日周月季年依次用Rn、Zn、Mn、Jn、Nn；n是具体数字。','级别|线段|走势类型|走势分解',2,'建议标记体系不是必须更名的计算定义；这里分钟/日等按作者本例级别用语，不与任意周期K线自动等同。')
c(88,'same-endpoint-multiple-marks','240-b004','191在该例必有X191线段标号，在1分钟层次可能同时有某Yn；189则仅线段号，标号重合与否反映其结构作用不同。','级别|线段|操作级别',2,'可能某Yn不补其具体序号，不用图上同一坐标推所有层级必有端点。',['第88课189与191端点比较'])
c(88,'all-level-top-rhetoric','240-b005','作者称从线段一直到年均有标号的同一点最重要，若是顶则称百年大顶。','级别|顶|线段',3,'百年大顶为该处作者形容，不是已验证百年内不会越过的时间保证，也未给此时所有层级实际确认的算法。',['同一端点在从线段至年各层次均有标号的设想'])
c(88,'marks-systematic-habit','241-b000','分级标号除了阅读方便，也用于培养多层次系统观察，避免把每段走势孤立看待而受每日波动迷惑。','级别|走势分解|操作策略',3,'观察习惯不代替各层次成立条件。')
c(88,'all-levels-intermediate','241-b001','作者从线段例推广说其他级别也有中阴阶段，每个级别顶点之后都有对应级别长度的中阴阶段。','中阴阶段|级别|顶|线段',1,'对应级别长度没有具体分钟天数换算；不能从顶点一出现就判固定时长后新类型必确立。',ambiguity='stage_length_not_time_formula')
c(88,'stage-shape-not-new-type','241-b005','中阴阶段截取出来的形态表现为不同级别盘整，围绕前走势某部分的中枢震荡；作者明确说这不表示新的走势类型一定是盘整，即使V型反转也一样，只是震荡回得更深。','中阴阶段|盘整|中枢震荡|走势类型|趋势转折',1,'截取形态与完整新类型不等同，括注必须保留；V型也有过渡不保证新类型只能横盘。',['只从截取中阴这一阶段的形态说'])
c(88,'v-turn-and-stage-level','241-b006','作者称一类买卖点后的转折都对应某级别V型反转，V的级别决定中阴级别与力度；例为190—191与191—192的小V，以及日线图6124附近的某级别V。','中阴阶段|第一类买卖点|级别|趋势转折',2,'某级别与日线图所见不等同日线级别已确定，未给V宽度到中阴时长的公式。',['第88课作者关于一类点后V及中阴的解释'],figs=((240,1),))
c(88,'stage-end-can-same-direction','241-b007 241-b008','中阴结束不一定反向，也可沿前方向继续，如上涨+盘整+上涨；上涨+盘整+下跌或上涨+下跌同样可能。','中阴阶段|走势延伸|趋势转折|走势类型|盘整',1,'阶段结束不是充分反向信号，不把生死比喻硬译为上涨之后必然下跌。')
c(88,'intermediate-skill-gate','241-b008 241-b009 241-b010 241-b011','中阴阶段作者要求有技术者才作大中枢震荡操作，能力不足者等待市场选择方向再决定；不能因该阶段有机会就跳过技术训练。','中阴阶段|中枢震荡|操作熟练程度|操作策略',2,'技能条件不能省略，有真本事不作项目认证的收益或零风险承诺。',['能够识别并处理所述中枢震荡的技术能力'])
c(88,'nov7-monthly-top-case','242-b004 242-b005','11月7日作者把当月是否确认月顶分型分为确认与不确认，后者可能有包含或创新高；当次5462为关键，跌破成立后再看约5300的5月均线，并类比3600时的旧例。','顶分型|包含关系|均线|确认',2,'月顶与5月均线不是日底与5日线；本月确认语境不能换成任一盘中触价即最终确认月分型。',['2007年11月7日当月5462及5月均线案例'])
c(88,'nov7-index-new-center-down','242-b009','11月7日5555附近新1分钟中枢形成，作者据此称6004起走势已明确成1分钟下跌形态，短线胜负看该中枢后续发展。','走势中枢|下跌|完成|中枢下移',2,'当日已成中枢与此前尚待形成分开，不倒填以前日期或保证接着下跌。',['2007年11月7日指数6004起走势'])
c(88,'nov7-petro-first-center-branches','242-b011 243-b000','11月7日中石油38附近线段底背驰反弹后约40形成其第一个1分钟中枢；作者列两支：震荡扩展成大中枢，或跌破并中枢下移完成1分钟下跌，操作随实际选择。','类背驰|线段|走势中枢|中枢扩展|中枢下移',1,'原文写线段底背驰，按线段比较语境保留，不升为严格1分钟底背驰；首个中枢不充分断定新上升或绝对底。',['2007年11月7日中石油首次1分钟中枢'])
c(88,'stock-index-method-same','243-b001','作者说明以中石油从开始演进作走势生长示例，认为个股与大盘分析方法并无不同。','走势分解|技术分析|走势类型',3,'方法相同不意味着两者未来价位、流通制度或每个形态相同。',['第88课中石油与指数分析的比较'])
c(88,'nov8-thousand-not-maximum','243-b004 243-b005','作者11月8日明确说此前1000点回跌空间只是其做空设想的小康水平，并未说超过1000点就没有更大下跌空间。','幅度|调整|走势预测',4,'历史设想与自评，1000不是必止跌或理论最大跌幅，也未核作者持仓及实际实现。',['2007年11月8日1000点预期的自我说明'])
c(88,'nov8-neckline-retest-unconfirmed','243-b005 243-b008 244-b003','11月8/9日作者以5462—5555为中线反抽关键区，跌破后还看能否尽快收回，不能收回则跌势继续；颈线跌破确认与刚跌穿仍分开。','颈线|反抽|有效跌破|确认|下跌',2,'原文对量度跌幅只反问而未给明确目标，不自行用双顶量度算新目标或宣布11月8已最终确认。',['2007年11月8/9日该颈线反抽'])
c(88,'nov9-petro-close-centers-not-certain','244-b009','11月9日中石油38附近又有新1分钟中枢，作者因与上一中枢太近认为极可能二合一扩展成更大级别，但明确由实际走势决定。','走势中枢|中枢扩展|级别',2,'极可能不是已成，太近未给本条独立数值定义，不把任意相邻两个同级中枢直接判升级。',['2007年11月9日中石油两个1分钟中枢'])
c(88,'nov12-three-centers-nesting','245-b001 245-b002','11月12日作者认定6004起1分钟下跌经三个中枢底背驰：早上补缺失败为最后中枢三卖，其后下跌的线段类背驰与1分钟背驰段形成区间套。','背驰|类背驰|第三类卖点|区间套|走势中枢',1,'三中枢为该走势数量，不是凡三中枢必背驰；线段类与1分钟背驰段两个层次不同。',['2007年11月12日6004起该次1分钟下跌'],figs=((246,1),))
c(88,'nov12-return-last-oscillation-region','245-b003','该次1分钟底背驰后，作者给的最基本涨幅是回到最后1分钟中枢的波动区间，并说当日已达到；后续看如何扩展成5分钟中枢及其位置、震荡结果。','背驰|走势中枢|波动区间|中枢扩展|中枢震荡',1,'波动区间不静默缩为中枢自身价格区间；当日已达最低目标不保证进一步反弹或5分钟中枢已经确立。',['2007年11月12日当次1分钟底背驰'])
c(88,'nov12-five-center-third-branches','245-b003 245-b004','作者在当次底背驰反弹后以将扩展的5分钟中枢三买、三卖区分后续短线止跌反弹与继续下跌分支，并用小康和富裕作跌幅比喻。','走势中枢|中枢扩展|第三类买点|第三类卖点|反弹',2,'将扩展的中枢先看位置及形成，不能未有5分钟中枢就宣布三类点；投票是修辞而非用户下单决定市场。',['2007年11月12日1分钟背驰后的5分钟结构展望'])
c(88,'retest-need-not-touch-neckline','244-b003 245-b005','作者先说会有对5462—5555颈线的反抽确认过程，11月12日进一步明说不一定碰到5462；最弱者可仅在颈线下震荡数天后继续弱势。','颈线|反抽|确认|反弹',1,'后句明确限制反抽必须触及价位的读法，不用日期自动覆盖其他条件或补具体天数。',['2007年11月9及12日该颈线反抽'],figs=((245,1),))
c(88,'nov12-rebound-may-end-needs-second','246-b002','11月12日最低回抽最后中枢的幅度已达，作者说反弹完全可能已结束；关键看回来的走势能否形成二买，不成则转弱。','反弹|第二类买点|走势中枢|完成',1,'最低目标已达不等于必定结束，也不等于二买必出现；反弹参与仍有能力前提。',['2007年11月12日最低反抽目标已达后的状态'])
c(88,'nov12-195-to-214-level-gate','246-b004','作者在6004起下跌图把最晚适合退出处定195，后续绿箭头三卖仅示其后行情；从195退出后，214才值得考虑回补，前提是可接受1分钟操作，5分钟以上级别者仍等待。','第三类卖点|操作级别|背驰|买点',1,'值得考虑而非必须回补或保证收益；1分钟与5分钟以上的选择不可省略，不把后续箭头三卖都当同样重要。',['2007年11月12日195至214案例','操作者可以接受1分钟级别'],exceptions=['5分钟以上级别的操作在该例仍等待'],figs=((246,1),))
c(88,'nov12-214-three-nesting','246-b005','作者把214称为191起1分钟下跌的底背驰，称其经三重区间套定位，最后一重在213—214线段内部笔之间。','背驰|区间套|线段|笔',1,'三重为作者该例说明，原图未完整标内部笔，此条不声称独立重算了三层或推得每根笔的精确端点。',['2007年11月12日214定位案例'],figs=((246,1),),ambiguity='internal_stroke_nesting_not_reconstructed')
c(88,'nov13-daily-bottom-five-day','247-b012 247-b013 248-b001','11月13日日底分型后，作者以能否重上5日线看其能否延伸成笔；不能重上有被破坏可能，一般即使破坏也可能近处出现最终成笔的新底分型，更精确还看1分钟底背驰后的中阴演化。','底分型|笔|均线|中阴阶段|背驰',2,'日底和5日线是该次配合，可能与一般不变必然；均线观察不能取代笔完整形式条件。',['2007年11月13日日底分型及1分钟中阴分析'])
c(88,'nov14-five-day-recovery-case','248-b004 248-b005','11月14日作者把前日底分型后下午站上5日线与启动联系，并把底背驰后的两天归为中阴阶段的简单现场例。','底分型|均线|中阴阶段|反弹',4,'仅作者当时案例说明，不用含12月行情的日线图认证11月14日后续必上涨。',['2007年11月14日该次5日线反弹'],figs=((248,1),))
c(88,'nov14-regain-versus-hold-5462','248-b008 249-b001','11月14日作者分开两项判断：重回5462无论能否站住都会在该例形成大中枢；站住则有更大反弹空间，期货明确消息仍可改变指数预期。','颈线|走势中枢|中枢震荡|反弹|政策风险',2,'重回与站稳不是同一条件；形成中枢与进一步反弹的两项后果不可混并，数值只限当次。',['2007年11月14日5462颈线及该次结构展望'])
c(88,'nov14-daily-stroke-end-hold','248-b009 249-b000','该反弹若采用较省事观察法，作者看日线笔延伸何时结束再处理；延伸至10000只是其假设说法。','笔|反弹|操作策略|完成',2,'10000不是预测目标或最低涨幅，日线笔结束也未在此给唯一实时阈值。',['2007年11月14日当次日线反弹笔'])
c(88,'nov16-five-center-larger-development','250-b001','11月16日作者说当前5分钟中枢震荡将继续向更大级别延伸，因此最终突破的级别意义更大，但暂时还需时间。','中枢震荡|级别|突破|小级别转大级别',2,'当次发展展望非仅随时长必升级的通用定义；未给确定结束日期或突破方向。',['2007年11月16日该5分钟中枢震荡'])

keep('239-b011','lower-l087-c-stage-nov2-191-193-different-perspectives','87课191/193线段角度与1分钟震荡角度已分层；88课新增中阴参照，不覆盖旧证据。')
keep('240-b000 242-b011','lower-l064-sublevel-as-segment-metaphor lower-l065-divergence-requires-minimum-center','严格线段与最低走势类型边界仍有效；本例线段级别和线段底背驰用语不能消除类结构范围。')
keep('246-b004','lower-l087-c-stage-nov2-late-sell-only-probability lower-l086-c-stage-first-center-third-last-opportunity','195后续三卖较迟和可能反转的先前限制保留；214的回补还取决于操作级别。')
keep('241-b001 241-b006 250-b001','lower-l084-c-stage-no-absolute-time-guarantee lower-l084-c-stage-level-not-time-classification','中阴长度和发展耗时不能擅改成时间到级别的固定换算；V型图所见周期不等于结构级别。')

issue('line-class-and-stage-end','239-b010 239-b012 240-b000','原文在该例并称新走势类型、线段级别与线段类下跌；195是当次分界，未给跨所有级别的同一中阴结束算法。','保留类线段与严格最低类型的旧界限；不把任意三卖当任意级别中阴结束的充分规则。',True)
issue('stage-length-and-v','241-b001 241-b006','对应级别长度及V的级别决定中阴级别力度没有具体数值或时间映射。','原文明说可查，但不自造N分钟/天数结束公式，后续89/90课另核。',True)
issue('214-internal-nesting','246-b005','图中有191至214和后续箭头，但最后213—214线段内部笔及三重区间套并未完整列图。','可记录作者声称三重定位；独立重算及精确内部端点尚未验证，不从走势图模糊像素补笔。',True)
issue('figure-origin-price','245-b005 246-b004 246-b005 248-b004','四图已看，245/248含文后行情；245图低点5032.58与246图214所标5034.11不同，图峰6123.64/6124.04也不同，制作人与数据源未核。','保留图ID、两个价位及未知来源，不改正文214或补成单一精确价格；两后期图登记。')
issue('historical-claims-and-skill','240-b005 242-b008 243-b004 244-b006 247-b004','百年大顶、1000点自评、多数少数成功及控盘修辞没有本项目外部或账户验证。','作为作者立场、修辞或历史预期，不认证无风险绩效、真实控制力或按符号保证百年不新高。')

note('239-b009','example_transition','引入当次189至195例的过渡句。','无独立新结论，不补看不见的端点。')
note('241-b002 241-b003 241-b004','intermediate_psychological_context','抄底拿不住、逃顶再套、多空转换与轮回拟人说明。','保持作者教学比喻；不认证所有亏损唯一因为中阴或宗教业力的市场实证。')
note('242-b001 242-b002 242-b003 242-b006 242-b007 242-b008 242-b010','historical_battle_and_capability','11月7日5555最迟周一、空头陷阱、反向阵营、杀死空头的空头及技术门槛叙述。','原文尚未来到的时间及策略立场不作已实现成绩，不制成操纵流程；具体中枢和月顶条件另抽。')
note('243-b003 243-b006 243-b007 243-b009 243-b010 244-b000','historical_session_context','11月8日导演自评、牛人/大牛人、持有比喻、5月均线埋伏与技术不足勿抢反弹、复习旧文。','保留作者立场与能力要求；不认证个人战绩、不把关注背驰的未来条件写成已成。')
note('244-b002 244-b004 244-b005 244-b006 244-b007 244-b008 244-b010 244-b011 244-b013 245-b000','historical_rhetoric_and_policy','导演剧本、输赢道德比喻、历史人物、板块年末重组、1000点任务自评与出货自述完整读。','不核历史人物评判或控盘收益；1000点并非最大调整已抽，股票代码和匿名机构不猜。')
note('245-b006 246-b000 246-b001 246-b003 246-b006 247-b000 247-b001','historical_rebound_and_schedule','5月均线及5462—5555重回条件、多头板块轮动、趣味/通俗写法与出差酒类安排。','修辞不构成新数学规则；反弹必轮动为该次作者预期，不认证未来必实现。')
note('247-b003 247-b004 247-b005 247-b006 247-b007 247-b008 247-b009 247-b010','learning_and_macro_stance','少数成功与把握自己、共产主义类比、1000点回调/历史50%60%、大牛市一阶段与持股不放弃立场。','未核比例、账户或后验预测；反弹结束须处理的节奏与技术边界保留，不作当前建议。')
note('247-b014 248-b000 248-b003 248-b006 248-b007 249-b002 249-b003 249-b004','historical_timing_and_sector','出差保证解盘、板块反弹未破、作者教材自评、期货中字头、中驴比喻、追反弹换岗与反省。','未知代码不补，未核公司与政策；课中结构条件独立抽取，不认证绝对获利。')
note('249-b006 249-b007 249-b008 249-b009 249-b010 249-b011 249-b012 249-b014 249-b015 249-b016 250-b000 250-b002','personal_and_historical_context','饮酒、地方企业考察、5462未触的骂多头修辞、中关村词源叙述、技术盗用自述及板块无持续性。','未核词源或匿名企业违法事实；酒后胡言保持原状态，不把5462诉求当全市场普遍信号。')

relations={
 'lower-l088-c-stage-intermediate-stage-definition':[('中阴阶段','走势类型','related'),('中阴阶段','确认','related')],
 'lower-l088-c-stage-intermediate-reference-old-part':[('中阴阶段','走势分解','related')],
 'lower-l088-c-stage-stage-shape-not-new-type':[('中阴阶段','中枢震荡','related')],
 'lower-l088-c-stage-stage-end-can-same-direction':[('中阴阶段','走势延伸','related'),('中阴阶段','趋势转折','related')],
 'lower-l088-c-stage-nov12-214-three-nesting':[('区间套','笔','related')],
 'lower-l088-c-stage-retest-need-not-touch-neckline':[('反抽','颈线','related')],
}
for r in rows:r['relations']=[{'source':s,'target':t,'type':kind} for s,t,kind in relations.get(r['id'],[])]

by_passage=defaultdict(list)
for r in rows:
    for e in r['evidence']:by_passage[e['passage_id']].append(r)
for item in pending:
    item['lesson_numbers']=sorted({int(passages[x]['unit_id'].split('-')[1]) for x in item['passage_ids']})
    if item['id'].endswith('figure-makers-and-late'):
        item['lesson_numbers']=[88];item['figure_ids']=[f['id'] for f in figures]
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
      'related_existing_claim_ids':retained_ids,'note':'中阴截取形态与后续类型不同，线段类对象不升为严格级别；当次195分界与214定位、全局定义区分。'},'4_reverse_check':inverse}})
for f in figures:
    key=(f['pdf_page'],int(f['id'].rsplit('fig',1)[1]))
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=figure_notes[key],
      figure_source_review='两图后期见stage-c-l088-figure-applied.json；全部绘者未核。',
      linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger)==124 and len({x['passage_id'] for x in ledger})==124
def dump(suffix,data):
    (OUT/f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x,ensure_ascii=False,separators=(',',':')) for x in data)+'\n',encoding='utf-8')
dump('reviewed.jsonl',rows);dump('coverage.jsonl',ledger);dump('pending.jsonl',pending);dump('figures.jsonl',figures)
summary={'stage':'C','schema_version':metadata['schema_version'],'graph_version':metadata['graph_version'],'lessons':[88],'document_id':DOC,'reviewer':REVIEWER,
 'passages_read':124,'claims':len(rows),'evidence':sum(len(r['evidence']) for r in rows),'importance_counts':dict(Counter(r['importance_level'] for r in rows)),
 'new_concepts':sorted({x for r in rows for x in r['concepts']}-set(concepts)),
 'whole_lesson_semantic_read_complete':True,'technical_extraction_complete':False,'four_round_review':True,'independent_review_claimed':False,
 'visual_pdf_pages':list(range(239,251)),'figure_objects_viewed':4,'figure_origin_counts':dict(Counter(f['origin_status'] for f in figures)),
 'pending':[x['id'] for x in pending],
 'source_passages_snapshot_sha256':SOURCE_SHA,'retained_source_links_in_ledger_only':True,'database_mode':'ro','formal_import':False,
 'acceptance':'124段四轮审读、12页及4图检查；中阴与新走势类型、当次195分界和操作级别条件保留，两图后期，增量待预检发布。'}
(OUT/f'{BASE}.summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
db.close();sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(summary,ensure_ascii=False))
