"""Materialize the manually read lower 89--90 batch; SQLite is read-only.

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
BASE='c_stage_l089_l090'
REVIEWER='Codex 主代理 / 阶段C下册89至90课同模型四轮复核'
SOURCE_SHA='621e64023e151913b8df5e86661a68eb0af9dadf32c4ed749bdea3f98caeda6e'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
db.row_factory=sqlite3.Row
metadata={r['key']:json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version']=='1.1.0'
assert hashlib.sha256((KB/'sources/volume_2.pdf').read_bytes()).hexdigest()=='5332cd1b60381c47ceb81358db6bbb47882efd074fc5c869dcc3002aaed1b5c0'
passages={r['id']:dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id BETWEEN 'lesson-089' AND 'lesson-090' ORDER BY pdf_page,block_index,id")}
assert len(passages)==276
assert hashlib.sha256(json.dumps(sorted(passages.values(),key=lambda p:p['id']),ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==SOURCE_SHA
old={r['id']:dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts={r['label']:dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical={label:r['label'] for r in concepts.values() for label in [r['label']]+json.loads(r['aliases'])}
figures=[dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 250 AND 277 ORDER BY pdf_page,id',(DOC,))]
assert len(figures)==18
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
 (253,1):'11/20嵌文但日线至2008年2月，后期；MACD收口和不上0轴只依正文语境',
 (259,1):'11/29嵌文但日线至2008年2月，后期；30分钟中枢展望不倒填完成',
 (261,1):'15分钟图至12/03、6004下降通道上轨，嵌文12/03，绘者未核',
 (261,2):'30分钟光标12/03但行情至12/05，后期；与第一图分别保存',
 (262,1):'日线与BOLL上下配图、标6/20及6004，光标12/03而右端延伸12月，确切截止日未核，维持unverified',
 (263,1):'000938日线/BOLL与9/14、10/08一二卖，右端12月截止日不明，制作人未核，不据图证明准确率',
 (263,2):'000999日线/BOLL与10/10、11/06一二卖，右端12月截止日不明，制作人未核',
 (264,1):'000002周线/BOLL、40.78峰，行情至次年6月，后期；不从未来跌幅认证周一卖',
 (264,2):'30分钟复权黑白图至12/03、下降通道与BOLL收口箭头；参数画在图上但正文未指定统一参数',
 (265,1):'5分钟与30分钟BOLL上下图，光标12/06晚于12/03课程，后期；仅正文支持跨周期选择例',
 (266,1):'12/5嵌文但30分钟行情至12/11，后期；通道突破/10日线/5010分层',
 (267,1):'12/5嵌文但日线至2008年，后期；5032.6图数不改正文5032',
 (268,1):'12/6嵌文但图头12/7，后期；1分钟破低与力度比较示例，不能后见替代判断',
 (269,1):'日线已至2008年2月、嵌周线12/7，后期；当时周线仅包含不补成底分型',
 (270,1):'12/11当日1分钟5151.2、5209.5、5104.3及拉回，右端末K确切时间未核，维持unverified',
 (272,1):'图头12/13而嵌12/12说明，后期；标后续1分钟三卖5148.9，不混成当天5分钟三卖',
 (274,1):'12/14当日5分钟框大5分钟与内部1分钟、5148.9三卖及4860.2，绘者未核',
 (276,1):'12/17文旁日线却行情至2008年2月，嵌周线12/7，后期；当日构成与确认状态按正文'
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
    pending.append({'id':'lower-l089-l090-c-stage-pending-'+slug,'status':'pending','passage_ids':[pid(s) for s in shorts.split()],
                    'description':description,'suggested_action':action,'blocks_full_semantic_extraction_completion':blocker,'reviewer':REVIEWER})




# Manually selected after all 276 passages, 28 pages and 18 crops were read.
c(89,'stage-not-ordinary-oscillation','250-b004 250-b005','中阴虽表现为中枢震荡，却不是一般性的中枢震荡；作者强调其处理连接前后操作节奏，不能仅以都是盘整而忽略差别。','中阴阶段|中枢震荡|盘整|操作策略',1,'承接88课截取形态与新类型的区别，不把中阴另造为上涨下跌盘整之外的第四种走势类型。')
c(89,'outcome-current-force-not-preset','250-b011','中阴阶段体现走势形式在级别上的多种可能，最终选择不是预先设定，而由当下市场合力决定；作者认为可统一按中阴过程处理。','中阴阶段|级别|市场合力|走势预测',1,'统一处理不等于提前知道最后方向或所有后续形态相同。')
c(89,'one-minute-divergence-higher','250-b012','作者在6004起1分钟下跌背驰例中，依据走势分解称后续必为超1分钟级别走势，但具体向上、向下或盘整仍有多种可能。','中阴阶段|背驰|走势分解|级别|走势类型',1,'限定该1分钟下跌背驰后的演化，不擅推广为任意未完成1分钟波动立即升级。',['第89课6004起1分钟下跌已经背驰'])
c(89,'higher-must-five-center','250-b012 251-b000 251-b001','在该超1分钟演化语境，作者断言无论后续何种级别，必须先出现5分钟中枢；他把此结构必经说为100%，同时不预设方向。','中阴阶段|走势中枢|级别|递归定义',1,'100%是作者理论断言，非本项目样本准确率；先有中枢不等于已确定最后走势类型或其形成日期。',['6004起1分钟下跌背驰后的超1分钟演化'])
c(89,'prepare-center-level-operation','251-b002 251-b003 251-b004','作者要求先准备处理该5分钟中枢；若按5分钟以上级别操作，这个5分钟中枢的中阴过程可以不管。','中阴阶段|走势中枢|操作级别',1,'以上按原文保留，不擅改成大于；可忽略是对操作者的相关性，不是否认结构存在。',['第89课所述5分钟中枢中阴过程'],['按5分钟以上级别操作者可以不管该过程'])
c(89,'center-extension-or-third-point','251-b005 251-b006','该5分钟中枢成立后须看延伸或三类点；若继续发展成30分钟中枢，则按30分钟三类点处理，依次类推，最终由某级别三类点结束相应中枢震荡。','中阴阶段|中枢延伸|走势中枢|第三类买卖点|级别',1,'原文延伸搞成30分钟是发展描述，不给本条固定时长或以任意一次三类点终结所有级别中阴的算法。',['中枢已经成立','操作所针对级别随实际形成的中枢变化'])
c(89,'five-minute-type-force-choice','251-b007','以5分钟中枢后出现三类点为例，作者说原1分钟走势演化为5分钟类型，再看一个中枢的盘整还是两个中枢的趋势，并用背驰力度判断。','走势类型|走势中枢|盘整|趋势|背驰',1,'一般例而非任何一次小三类点必构5分钟趋势；正式趋势需同级中枢方向等既有条件，不把两中枢裸数量当充分条件。',['第89课已形成5分钟中枢并出现其三类点的示例'])
c(89,'consolidation-not-flat-range','251-b010','作者特别区别其盘整与通常的区间横盘：指数即使10000跌到0也可属盘整，只要该级别中间只有一个中枢。','盘整|走势中枢|幅度|级别',1,'10000到0是极端说明例非预测；数量需相应级别且走势类型定义成立，不把任意一段暴跌自动盘整。',['所论级别的完整走势类型只含一个中枢'])
c(89,'center-not-consolidation-apple','251-b010','中枢与盘整不是同一概念；作者比中枢为苹果、盘整为只有一个苹果的树，趋势则可有两个以上中枢。','走势中枢|盘整|趋势|走势类型',1,'苹果与树是对象和所含结构的比喻，不将中枢自身叫一个盘整走势类型。')
c(89,'consolidation-not-necessarily-weaker','251-b011','盘整不一定比趋势弱，第一段与后段合起来的幅度、力度可以超过某趋势；中枢个数不直接决定整体走势强弱。','盘整|趋势|幅度|动力学',1,'可以而非所有盘整都更强，也不借幅度比较改变中枢数量及方向定义。')
c(89,'nov20-five-center-still-unsettled','252-b016 252-b004','11月19/20日作者仍把大盘看成5分钟中枢震荡、方向未定，若继续发展才会延伸出30分钟，并提示指数意义下降应看具体板块图形。','中阴阶段|中枢震荡|级别|指数走势背离',3,'继续才形成更大级别，不倒填当时30分钟已完成；月亮提问另作修辞。',['2007年11月19/20日当前5分钟震荡'])
c(89,'nov20-macd-next-zero-risk','253-b000 253-b001','11月20日作者认为当次震荡有利日MACD收口；反弹后若日MACD转头却上不了0轴，通常意味着更严重下跌，因此中线应看反弹上去后的表现。','MACD|反弹|市场风险',3,'通常与当次中线范围保留，不把MACD单指标独立定义结构背驰或必然跌幅。',['2007年11月20日日MACD与后续反弹的判断'],figs=((253,1),))
c(89,'nov22-small-sell-large-unknown','254-b011','11月22日已有小1分钟三卖，但是否形成大5分钟三卖仍未知；若中枢扩展为30分钟，此次下破可能只是陷阱。','第三类卖点|中枢扩展|中阴阶段|空头陷阱|级别',1,'大小级别与未知状态保留，可能扩展不当成已经扩展。',['2007年11月22日该次下破'])
c(89,'oscillation-sublevel-force-rule','254-b012 255-b000','作者重申中枢震荡操作：冲不起在次级别上涨背驰时卖；跌下来若不成中枢下移、最多扩展，则在次级别下跌背驰时买，并限定有技术者。','中枢震荡|次级别|背驰|中枢下移|中枢扩展|操作熟练程度',1,'不下移是回补前提，不是任意跌下来都买；次级别须完成相应背驰判断。',['中枢震荡','下行未形成中枢下移而最多扩展','有相应结构与背驰识别能力'])
c(89,'nov22-month-day-supports','255-b001','11月22日作者把月收盘确认失去5月线后的下一个支持看10月线；另从日线看120日半年线附近预期反弹以确认5000是否有效跌破。','均线|反弹|有效跌破|确认',4,'5月、10月、120日层次不混为5日10日；这是当次条件预期，未验证必然反弹。',['2007年11月22日月线与日线两套支持分析'])
c(89,'familiar-stock-pool-not-chase','255-b002 255-b003 255-b004','作者主张长期关注一组股票、熟悉股性，并在所述反弹与中级调整过程中动态观察；以不熟不做说明耐心和熟练的重要性。','操作熟练程度|动态建仓|操作策略',3,'历史方法主张不构成当前股票推荐，不把熟悉即保证赚大钱的修辞认证为绩效。',['第89课2007年11月22日股票池与股性讨论'])
c(89,'policy-one-force-not-total','256-b004','作者在11月22日印花税文章中强调政策只是分力之一、不是合力本身，不能直接把某项政策本身视为真正市场顶底的定义。','政策风险|市场分力|市场合力|顶|底',3,'记录作者观点，不认证所举1994/1996/2007政策史，也不推出政策从不影响市场。',['2007年11月22日政策与印花税论述'])
c(89,'nov25-month-top-stroke-gate','256-b010 257-b000','月顶分型成立后，作者从中长线角度要求看能否延伸成笔；一旦成向下月笔，在月底分型出现之前不认为会有中长线实质上涨。','顶分型|底分型|笔|操作级别',1,'分型成立与成笔分两步，月笔语境不否认期间较小级别反弹。',['2007年11月25日中长线月线分析','月顶分型已经成立且延伸为笔'])
c(89,'nov26-250-day-bull-boundary-case','257-b009 257-b010','作者11月26日以250日线作当次长线牛熊观察边界，有效跌破前不讨论牛市结束；中短线120日、10月线附近则暂按反弹眼光处理。','年线|均线|有效跌破|反弹|操作级别',3,'这是历史观察框架，不替代当前市场定义，长线与中短线的不同态度并列。',['2007年11月26日当次指数的长短线框架'])
c(89,'nov26-week-top-needs-bottom','257-b011','对6124那周的周顶分型，作者要求先构造周底分型以完成一笔，随后数周以寻找、构造该底分型的视角分析。','顶分型|底分型|笔|确认',2,'须同一周线层次，不把任意日底当周底已构成。',['2007年11月26日6124前后周顶案例'])
c(89,'nov27-week-new-low-not-bottom','257-b014','11月27日作者因本周已创新低，认定当周完成不了周底分型；在5周线重新站稳之前，以该周线角度不急于看反弹。','底分型|均线|包含关系|确认',2,'所论当周构造条件及5周线不是盘中任意新低都永久排除以后底分型；正文5160/邻文5163差异原样保留。',['2007年11月27日该周周K'])
c(89,'nov29-thirty-center-future','259-b002 259-b003','11月29日作者说拉回5000使更大中枢在扩展，5000上下将扩展出30分钟中枢，随后看其三卖与5周线反抽力度；站不上5周线仍有再探底压力。','中枢扩展|中枢震荡|第三类卖点|均线|反抽',2,'正在扩展/将形成的时态保留，不写成30分钟已经完成；未给第三卖点已出现。',['2007年11月29日5000及120日线反抽案例'],figs=((259,1),))
c(89,'nov30-large-bottom-often-two-feet','260-b006','作者11月30日说当时只是首次探底、第一只脚未落地，大底往往需两只甚至更多脚确认，技术不足者等整体转势、底确认再参与。','底|确认|市场风险|操作熟练程度',2,'往往不是严格必要或足够的固定二次低点计数；脚是探底比喻，不把第二低点一到就自动确认。',['2007年11月30日当次大底形成状态'])
c(89,'nov30-stock-fractal-and-center','260-b009','作者当时优先关注周/月底分型已构造完成的个股，手脚麻利者也可看日底分型，再看大级别中枢位置以评估较大力度的可能。','底分型|走势中枢|级别|操作熟练程度',2,'可能而非必爆发，日/周/月与操作者能力不同，不将已构造与后续确立混并。',['2007年11月30日个股技术观察方法'])
c(89,'dec3-channel-two-paths','260-b011 260-b012 261-b000','12月3日作者称6004下降通道上轨约4950，与下移10日线接近；短线可能突破上轨后总反抽，也可能先再一次空头陷阱才反抽。','反抽|均线|突破|空头陷阱',4,'两支均未来选择，15分钟及30分钟配图观察工具不直接定义1分钟/5分钟走势级别。',['2007年12月3日4950附近下降通道分析'],figs=((261,1),(261,2)))
c(89,'dec3-rebound-not-final-bottom','262-b000','12月3日作者强调该次反抽后至少还需一次探底确认，10月线为中短线参照、250日线为更下方长线边界。','反抽|底|确认|均线|操作级别',2,'反抽确立不等于中级底部已确认，均线数值只作该历史框架。',['2007年12月3日当次反抽展望'])

c(90,'boll-auxiliary-not-absolute','262-b004','第90课明确限定所给中阴结束时间判断是辅助、非绝对；作者虽自称有效性接近100%、很少例外，仍承认存在例外。','布林通道|中阴阶段|技术分析|概率原则',1,'接近100%仅作者经验主张，无本项目样本测试；不能因为绝对判据被称复杂就说本课已给可执行的绝对算法。',exceptions=['辅助判断有例外，非绝对判断'])
c(90,'boll-skill-and-practice','262-b005 265-b003','辅助判断依赖技巧和熟练程度，作者称其比MACD还更讲技巧，需要持续看图、自己总结经验。','布林通道|MACD|操作熟练程度',2,'训练有素类比不是保证任何使用者近100%成绩；未训练不自动获得作者所称有效性。')
c(90,'boll-three-bands-strong-zones','262-b006','作者称布林通道通常标BOLL、有上中下三轨；上轨以上与下轨以下通常是上涨、下跌的超强区，并说中枢移动时一般会出现相应超强状态。','布林通道|中枢上移|中枢下移|技术分析',1,'一般与通常保留；本课正文未指定计算周期、标准差倍数或价格取值，图上BOLL(20)不自动定为全书唯一参数。')
c(90,'boll-first-point-sequence','262-b007 263-b000','作者给一类点辅助情形：先从上轨上跌回其下或从下轨下涨回其上，再次涨跌创新高/低却不能有效回到原超强区，则称进入中阴、一类买卖点出现。','布林通道|第一类买卖点|中阴阶段|高低点',1,'顺序、新高低和未有效回超强区须联合，且始终为辅助判断；不能仅碰轨就独立定义正式一类点。',['先由超强区域回到一般区域','随后再涨/跌创新高/低','未能有效回到对应超强区域','第90课辅助性而非绝对判据'])
c(90,'boll-second-point-lag','263-b001','进入中阴后，上下轨往往滞后，第一次回跌/回升后再向上/下时才转向；转向的上轨、下轨常作阻力、支持，使二卖在其下、二买在其上构造，作者认为此辅助比一类点更有效。','布林通道|第二类买卖点|中阴阶段',1,'滞后、往往/常及辅助均保留，不把任意一根轨道掉头充分等同二类点已确认。',['已进入中阴','经历首次回跌或回升后再向原方向运动的阶段'])
c(90,'boll-index-second-examples','263-b001','作者举上海大盘6004处及6月20日为BOLL辅助二卖示例。','布林通道|第二类卖点|走势中枢',4,'仅记录作者举例，不从未知制作截图独立证明背驰结构或准确率；6004不补为图上6004.79。',['第90课列出的两个指数历史例'],figs=((262,1),))
c(90,'boll-stock-first-second-examples','263-b002 264-b000','作者列000938的9月14日一卖、10月8日二卖，以及000999的10月10日一卖、11月6日二卖，作为BOLL辅助的历史例。','布林通道|第一类卖点|第二类卖点',4,'角色为作者举例而非项目独立识别回测；图截止日与制作者未核，不能据例数得出总体胜率。',['第90课000938及000999历史例'],figs=((263,1),(263,2)))
c(90,'boll-weekly-vanke-example','264-b001','作者以000002周线40.78元所在周作一卖辅助示例，强调并非只有其自述持股才可见此模式。','布林通道|第一类卖点|操作级别',4,'周线例与日线例分层；图含次年行情，不用未来跌幅替代当时结构条件，未核作者持仓。',['第90课000002周线40.78历史例'],figs=((264,1),))
c(90,'boll-contraction-expand-or-end','264-b002 265-b000 265-b001','布林收口是作者给中阴结束时间的辅助提示：某级别通道收口，通常提示更低某级别中阴过程将级别扩展或结束，一般对应相应三类点。','布林通道|中阴阶段|中枢扩展|第三类买卖点|级别',1,'扩展或结束两支、某个较低级别与一般性必须保留，不把收口当同级中阴已结束或三类点必已确认。',['某级别布林通道收口','对应的是比其低的某个中阴过程'])
c(90,'boll-chart-period-not-one-to-one','265-b000 265-b002','不能把1分钟走势级别机械配1分钟BOLL；作者所举5分钟中阴例用30分钟BOLL，并结合图中的下降通道观察。','布林通道|中阴阶段|周期K线图|级别',1,'5与30仅所举选择例，不推广所有5分钟中阴固定六倍周期或每层都同倍数；图为后期截图不倒填12/3状态。',['第90课所举5分钟中阴过程及30分钟布林图'],figs=((264,2),(265,1)))
c(90,'dec4-channel-three-day-check','265-b005','12月4日突破6004下降通道上轨但受阻10日线，回落未回上轨下；作者说一般突破后需3天确认，所以接下来两日关键。','突破|反抽|均线|确认',2,'一般经验与当次上轨突破范围保留，三天不能自行补连续收盘或全市场强制算法，也不与10日线确认混为同一事件。',['2007年12月4日下降通道上轨突破'])
c(90,'dec4-low-volume-news-force','266-b001','作者在当时成交偏小、市场合力偏弱的情景，认为消息力量更易放大，细致判断不能忽略经济会议消息；大方向与细节层次不同。','市场合力|市场分力|政策风险',3,'这是该次条件判断，不认证会议实际决定了价格，也不说低成交必然只受政策支配。',['2007年12月4日作者所述成交小及合力弱情景'])
c(90,'dec5-ten-day-confirmation','266-b002 266-b007 266-b008 267-b000','作者12月4日以站稳10日线作为大反抽确立标志，12月5日称早盘30分钟攻克后已确认，顺序为通道上轨突破、回抽，再突破10日线。','反抽|均线|确认|突破',1,'通道三天观察与10日线确认是不同参照，不能凭后一确认自动删前条一般经验；本条非所有反抽统一定义。',['2007年12月4至5日当次大反抽'],figs=((266,1),))
c(90,'rebound-second-test-and-trap-exception','266-b004 266-b006','该次大反抽之后仍需二次探底确认；若本次先有空头陷阱再反抽，后次确认不一定破底，可成双底，否则再次破底并不奇怪。','反抽|底|确认|空头陷阱',1,'仍需确认与未必新低并列，不把二次探底当作必创新低或反抽确认就等于最终底。',['2007年12月4/5日该次大反抽后的展望'],['本次先有空头陷阱再起时，后次可不破底'])
c(90,'dec5-5010-potential','267-b001','12月5日作者把5010称该小双底颈线，站住才有攻击双底基本升幅的潜力。','颈线|确认|反抽',2,'潜力不等于必达到某高度，原句未写明确升幅目标，不自行补量度价位。',['2007年12月5日5010小双底颈线','5010站住'])
c(90,'dec5-5032-fact-threshold','267-b002','作者明确说5000下空头陷阱扩成大中枢，重新站上5032之前还不能称事实；12月5日才称成为事实并转看其震荡。','中枢扩展|中枢震荡|空头陷阱|确认',1,'将要形成与已成事实以该例5032区分，不能用后期图或11/29展望倒填此前已完成；图5032.6不静默改正文。',['2007年12月5日5032重回后的该次大中枢'],figs=((267,1),))
c(90,'dec5-gap-first-then-achieved','267-b003 270-b008','作者12月5日把回补11月21/22向下缺口列首要任务，12月11日明确称5200缺口第一目标已经完成。','缺口|反抽|完成',2,'首要目标及已完成分属不同日期，不把12/5预期写成当日已补完或所有反抽必补缺。',['2007年12月5至11日该次反抽目标'])
c(90,'dec5-head-shoulder-only-best-path','267-b004','作者12月5日把先反抽5462再回调确认、小头肩底作为较有力量的最好情景，但强调需多方面配合。','反抽|确认|走势预测',3,'最好情景不是必然路径，不能把5462作该次反抽必须到达或固定买点。',['2007年12月5日该次反抽的条件展望'])
c(90,'dec5-thirty-center-five-sublevel','267-b005','对该30分钟中枢震荡，作者用次级别5分钟上行背驰先出、回落仍维持震荡再入的思路；动作特别快者也可观察1分钟。','中枢震荡|次级别|背驰|操作级别',1,'30对5为此例的结构次级别，1分钟是额外能力选择，不替换正式次级别概念；回补须仍震荡。',['2007年12月5日该30分钟中枢','回落仍保持中枢震荡'],exceptions=['动作特别麻利者可看1分钟进行操作观察'])
c(90,'traps-require-center-oscillation','268-b000','作者把市场陷阱归于中枢震荡；若实际是中枢移动，就不能按陷阱处理，原文称是真陷进去了。','市场陷阱|中枢震荡|中枢上移|中枢下移',1,'这是作者技术语境里的陷阱，不泛指全部欺骗；破某价位本身不足判假突破，须先辨震荡和移动。')
c(90,'traps-need-force-comparison','268-b001 268-b002','辨陷阱除中枢震荡外还要比较前后力度；12月6日例先辨1分钟中枢大概位置，再比较破第一下降段低点形成的笔与前笔力度，作者据此判断盘中小陷阱。','市场陷阱|中枢震荡|动力学|笔|线段',1,'原文未给此比较的统一数值指标或仅两线段充分成中枢规则，不凭后期12/7反弹证明当时已能无条件识别。',['2007年12月6日该小陷阱例','已有所论中枢震荡','前后笔的力度比较'],figs=((268,1),))
c(90,'dec7-daily-stroke-before-top','269-b001 269-b005','12月7日作者称当时日线上已确定至少成向上一笔，该笔结束须顶分型，所以日顶未出现前不急于宣布该日线反弹结束；之后再看是否延伸为笔上涨。','笔|顶分型|反抽|完成',1,'已确认当次日线笔是前提，不推广任何没有日顶的任意反弹都可无条件持有。',['2007年12月7日已确定日线向上笔的该次反抽'])
c(90,'dec7-week-inclusion-not-bottom','269-b003 269-b006','12月7日作者称本周尚未越过上周高位，只形成包含，周底分型还需下周构造，再看5周线。','包含关系|底分型|均线|确认',1,'包含不冒充周底已成，后期日周拼图不倒填该周确认。',['2007年12月7日该周周K状态'],figs=((269,1),))
c(90,'dec10-top-then-five-day','270-b001','12月10日作者要求日线笔未出顶分型前先持有等卖点，日顶出现后再看是否有效跌破5日线而确立。','顶分型|笔|均线|有效跌破|确认',1,'分型出现、有效跌5日线是该方法不同步骤，不把盘中震荡直接当日顶或完成笔。',['2007年12月10日已成日线上笔的反抽'])
c(90,'dec11-5151-center-case','271-b000','12月11日补缺后形成1分钟中枢，作者说第三分线段结束再拉回5151上，确认其震荡中枢有效；随后以能否围绕5151震荡作观察。','走势中枢|完成|确认|中枢震荡',2,'第三分线段保留该例用词，不从此给任意三线段即可成中枢的充分规则，图5151.2不改正文5151。',['2007年12月11日补缺后该1分钟中枢'],figs=((270,1),))
c(90,'dec11-three-observation-tools','271-b001 270-b002','作者在该反抽中给不同能力的观察选择：较大操作看日线笔结束，手脚快者用小级别震荡换股或短差，无感觉者看5日线；普涨首轮换股较难。','操作级别|操作熟练程度|笔|均线|操作策略',2,'观察工具不等于同级别同信号，换股与短差均有能力限制。',['2007年12月10/11日当次反抽'])
c(90,'dec12-5151-weak-five-center','271-b015 272-b000','12月12日开盘跌破5151且反抽不上，作者判为弱势休整，并把该休整与5010那次1分钟中枢震荡共同扩展为5分钟层次。','中枢扩展|中枢震荡|反抽|确认',1,'弱势性质与更大中枢范围不是后期图里的1分钟三卖已于12/12确认；价位只限该例。',['2007年12月12日该次5151及5010震荡'],figs=((272,1),))
c(90,'dec12-top-formed-not-down-stroke','272-b001','12月12日日顶分型已形成，但5日线尚未确认有效跌破，因此作者不能马上断言休整必成向下日笔；若有效跌破才至少成下笔，并等底分型结束。','顶分型|底分型|笔|均线|确认|有效跌破',1,'分型形成、5日线有效破、笔确认顺序保留，不能以当天顶分型或次日图倒填当日下笔已确立。',['2007年12月12日当日顶分型已形成','后续有效跌破5日线才确认向下笔'])
c(90,'dec12-no-third-sell-rebound-branch','272-b002','作者12月12日认为该5分钟震荡即使扩展30分钟，只要不出向下三卖，仍将继续向上反弹。','中枢震荡|中枢扩展|第三类卖点|反弹',2,'只在该次震荡的条件判断，不推出任何市场无三卖就必涨或小三卖等同大三卖。',['2007年12月12日所述5分钟/扩展30分钟震荡','该相应中枢没有向下第三类卖点'])
c(90,'weekly-stock-bottom-five-week','272-b003','个股周底分型已确认时，作者用5周均线参照持有，毋须过度关注指数震荡；短跑仍限手脚麻利者。','底分型|均线|持股|操作熟练程度',2,'周底已确认是前提，不把周底刚构成或任意日底替代。',['2007年12月12日个股讨论','个股周底分型已经确认'])
c(90,'stock-commentary-not-buy-now','272-b004 273-b012','作者明确说复点评早先股票只论长线基本面，并非让读者现在买；是否买须看有无买点及买点级别，许多个股此前已涨较多。','买点|级别|基本面|操作策略',1,'不得截取股票名单或长线看好当即时买入信号，未核公司基本面。',['2007年12月12/14日对旧股票点评的解释'])
c(90,'dec14-down-stroke-length-not-key','273-b007','12月14日凌晨作者称前日反抽未过5日线而顶分型确立；其后10根短阴或一根长阴，只要未有底分型，都仍是向下笔过程。','顶分型|底分型|笔|均线|K线',1,'长阴不是顶分型确立必要条件，也不是不可能结果；十与一为过程形态比喻，不固定笔所需根数。',['2007年12月14日凌晨对前一交易日的分析'])
c(90,'dec14-five-center-no-third-sell','273-b008','12月14日凌晨作者仍说下跌暂未震出该5分钟中枢三卖，故仍是中枢震荡；若三卖出现，跌破前低的几率极大。','第三类卖点|中枢震荡|高低点|概率原则',1,'暂未、若与几率极大保留，不把图内内部1分钟三卖当此处5分钟已确认，也不把几率大改成客观必然。',['2007年12月14日凌晨该5分钟中枢'])
c(90,'third-sell-illness-metaphor','273-b009','作者用未病、欲病、已病评价处理时机，把中枢震荡的三卖比为已病，并认为等到此时处理已较迟。','第三类卖点|中枢震荡|操作策略',3,'本段为教学比喻，不给医学建议；尚未在此逐一定义全部三级买卖点映射，不以未病之名凭猜测提前交易。')
c(90,'dec14-week-formed-await-confirmation','274-b008 273-b011','12月14日早文还待当日不破4778以构造周底，下午作者说周底已构成，下周任务才是站住5周线使之确立。','底分型|均线|确认|完成',1,'同一天不同发表时刻分开，构成与确立不可互换；不是12/14下午已经全部确认。',['2007年12月14日早文与收盘后周底状态'])
c(90,'dec14-5149-rebound-still-oscillation','274-b009 275-b000 275-b001','12月14日5149起下跌段背驰后回抽5010所在5分钟中枢，作者仍以震荡处理，直到相应三类点出现；需要较高技术。','背驰|中枢震荡|第三类买卖点|操作熟练程度',2,'图内部1分钟三卖与5分钟震荡三类点分层；5149不由图5148.9静默更正。',['2007年12月14日5010扩展的该5分钟中枢'],figs=((274,1),))
c(90,'dec14-next-daily-bottom-conditional','275-b002','作者12月14日展望下周一先构成日底，若成立再看周二后5日线站稳以确立，向下笔才完成；其后才看向上日笔能否带出周上笔。','底分型|笔|均线|确认|级别',1,'周一能构日底是全段前提，不把预期写成已成或上日笔必带周上笔。',['2007年12月14日对下周的展望','首先必须下周一构成日底分型'])
c(90,'dec17-daily-inclusion-not-bottom','276-b001','12月17日作者说日底未构成、仅包含；若次日低于前周五，则5209起向下笔继续延伸。','底分型|包含关系|笔|完成',1,'与12/14周一日底展望并列保留失败分支，条件未发生不宣称已经延伸完成。',['2007年12月17日日线状态','若次日低于前周五低位的后续分支'],figs=((276,1),))
c(90,'dec17-week-bottom-necessary','276-b004','作者称该指数要形成中级底部，周底确认是必要前提；本处不能确认则仍可能下台阶后重新构造、确认，当时日底也尚未构成。','底|底分型|确认|级别',1,'必要不等于充分，也不限定必在现价确认；周底构成与确认、日底未成两层保留。',['2007年12月17日该指数中级底部讨论'])
c(90,'dec17-third-sell-threat-not-confirmed','276-b005','12月17日5010中枢震荡面临三卖威胁，作者说一旦确认便不可避免新低；当时文字仍是威胁与条件，并未宣布三卖已确认。','第三类卖点|中枢震荡|确认|高低点',1,'不可避免为作者条件断言，不用后期2008图替其完成当日确认，且不自动覆盖12/14概率措辞的不同状态。',['2007年12月17日5010中枢','相应第三类卖点确认后才作所述新低结论'])

keep('250-b004 250-b005 250-b011','lower-l088-c-stage-stage-shape-not-new-type lower-l088-c-stage-stage-end-can-same-direction','88课截取盘整及可同向延续的边界与89课必经结构并列，不能以必经5分钟中枢提前预设方向。')
keep('251-b007 251-b010','upper-l017-type-partition','上册正式类型划分保留；苹果比喻与一二中枢裸数量不代替完整走势类型及趋势方向条件。')
keep('265-b000 265-b001','lower-l084-c-stage-level-not-time-classification lower-l088-c-stage-all-levels-intermediate','走势级别不等于K线周期，BOLL跨周期只是辅助经验，未提供中阴固定长度公式。')
keep('265-b005','lower-l065-neckline-break-retest-case lower-l087-c-stage-nov6-neckline-three-days-buffer','三天在3919、5555及此通道例中可追溯，不自动把3天或3%推广成全书每次有效破位的充分必要算法。')
keep('267-b002','lower-l088-c-stage-nov14-regain-versus-hold-5462','不同案例重回与站稳分别陈述；11/29将扩展与12/5成为事实为本批两条新命题，不复写旧图。')
keep('268-b000','lower-l088-c-stage-stage-shape-not-new-type','中阴截取震荡与最终类型分开，陷阱判断仍须辨中枢震荡还是移动。')

issue('boll-parameters-and-period-choice','262-b006 262-b007 263-b001 265-b000 265-b001','正文未给BOLL计算参数、收口阈值、有效回轨量化条件或跨周期选择算法；图见BOLL(20)不能提升为唯一正式参数。','仅发布辅助与联合形态原话，5分钟中阴看30分钟为例，不写固定六倍换算或可直接部署识别器。',True)
issue('auxiliary-near-100','262-b004 262-b005 251-b000 251-b009','90课近100%属辅助经验且承认例外，89课100%属作者理论必经与操作断言；两者都没有项目样本或独立账户核验。','保持原语气和前提，不将理论逻辑必经、指标有效率及交易获利胜率混为同一100%。')
issue('extend-upgrade-wording','251-b005 251-b006 251-b007','正文用不断延伸搞成30分钟，也用三类点后演成5分钟类型的简述，未在此重写所有中枢延伸/扩展及走势完成规则。','保留作者发展描述并联查正式定义，不将仅耗时或只有两个中枢的裸数量作为升级/趋势算法。',True)
issue('red-market-shortcut','276-b002','12/17把构成日底需高于周五最高与不红盘就不必等收盘相连，但红绿通常指当前价相对前收，是否曾盘中达高点及判断时点未明。','保留原句为历史语境，暂不抽成通用不红盘必不能成底分型算法；不静默修正作者原话。',True)
issue('figure-makers-and-late','253-b001 259-b002 263-b002 264-b000 265-b000 267-b002 272-b001 276-b004','18图实际查看；11图可见文后日期/行情，余7图制作人或截止日未核，262/263日图12月具体截止仍不清。','11图登记后期，其余不自动认证原图；5151/5151.2、5149/5148.9、5032/5032.6等图文精度保留，不从图倒填确认。')
issue('three-day-two-confirmations','265-b005 266-b002 266-b007','12/4一般突破3天确认，与12/5站10日线称大反抽确立属于不同参照，未给统一收盘/盘中及3天3%合用规范。','并列追溯来源，不静默删除任一规则或自动解除早批有效突破算法待核。',True)
issue('macro-law-stock-claims','254-b001 255-b007 256-b001 256-b004 271-b008 273-b004','2007年的流通比例10%、印花税、企业股性与十倍等法律/经济/绩效自述未与外部历史资料或账户验证。','仅保留历史观点与语境，非现行法律、当前选股建议或独立收益统计；股票点评非现在买的明确说明单独发布。')

note('250-b006 250-b007 250-b008 250-b009 250-b010 251-b008 251-b009 251-b012','theoretical_and_teaching_context','上涨下跌盘整公理、欧氏几何、精确思维、幼儿园及100%理论威力、全面小康比喻完整读。','不认证外部数学优先性或作者实盘100%；结构与辅助指标的不同性质单独保留。')
note('252-b001 252-b002 252-b003 252-b005 252-b006 252-b007 252-b008 252-b009 252-b010 252-b011 252-b012 252-b013 252-b015 252-b017','mixed_literary_and_market_context','神华/石油与题材轮动、阶级斗争和谐比喻、古文引语、解盘承诺及指数调控试验自述。','古文是文章所引而非作者原创技术证据；不核性医学修辞、政治主张或真实控盘。')
note('253-b002 253-b003 253-b004 253-b005 254-b001 254-b002 254-b003 254-b004 254-b005 254-b006 254-b007 254-b008 254-b010','historical_policy_and_stocks','5月线收盘、能力门槛、煤液化/150油价情景、动态建仓、AH首发10%流通、期货、ST小盘及月圆自评。','作者当时政策理解、企业预期与自述未外核；不把疑似非法作为已判法律事实或月亮因果。')
note('255-b006 255-b007 255-b008 255-b009 255-b010 256-b000 256-b001 256-b002 256-b003 256-b005','historical_stamp_tax_essay','印花税应降、流通比例、40亿/180亿、印度上市数和4000家资源、供需及5月政策后的行情论证已逐段读。','2007年作者经济政策建议与数据未外部核对，不作现行税率或真实因果证明；政策分力观点单列。')
note('256-b007 256-b008 256-b009 257-b001 257-b002 257-b003 257-b004 257-b006 257-b007 257-b008 257-b013','historical_session_and_personal','股权收购日程、120日反抽5000/5163分支、月收盘、神油/人寿类比、10月线区间陷阱与丛林修辞。','当前价格情景仅当时；不认证收购、筹码及个人盈利，不把类比当价格复制；月笔及长线框架另抽。')
note('258-b000 258-b001 258-b002 258-b003 258-b004 258-b005 258-b007 258-b008 258-b009 258-b010 258-b011 258-b012 258-b013','historical_forecasts_and_battle','1000至3500跌幅命名、决策责任、割肉/豺狼比喻、收购、双顶量幅/支持区、次月反抽上下影、4000缺口与陷阱自述。','不认证强制下跌或操纵能力；量度未给算法，不补计算新目标；预测与结果不混同。')
note('259-b001 259-b004 259-b005 259-b006 259-b007 260-b000 260-b002 260-b003 260-b004 260-b005 260-b007 260-b008','historical_capability_and_rhetoric','收购时间、游击战及道德比喻、技术不足不抢反弹、5周10月夹板、长阴后反抽预言、个股先行和练技术。','不把任意上/下破夹板都必陷阱作普遍事实；能力和大底确认边界另抽，反抽预测未独立验证。')
note('261-b001 261-b002 262-b001 262-b002','historical_petro_and_policy','中石油30预期、既有个股未来不放弃、经济会议影响与香港会面。','不认证公司信息、价格目标或政策无致命影响，维持2007年预期身份。')
note('265-b006 266-b000 266-b003','historical_news_and_sector','经济会议等待、必有总反抽自评、中低价启动与9119轮动。','新闻方向未核，必然为作者条件立场，不认证结果；合力弱时消息影响单列。')
note('267-b006 267-b008 268-b003 268-b004 268-b005 268-b007 269-b000 269-b002 269-b004 269-b007 269-b009 270-b000','historical_sessions_and_psychology','5日线简化观察、5010当日低破/次日5021回升、周末心理、反弹认同递进、综合级别、领涨共识、温泉雪和绿色字。','个别成交价不变市场统一阈值；心理操盘叙事不编执行流程，也不将天气证明行情因果。')
note('270-b003 270-b004 270-b005 270-b006 271-b002 271-b003 271-b004 271-b005 271-b006 271-b007 271-b008 271-b009 271-b010 271-b011 271-b012 271-b014','historical_stock_pool_and_targets','补缺循序、000999/600737学费股、2008板块、长线股票池与90%筹码自述、8只基本面/多倍涨幅预期及休整解释。','未核账户、内幕、公司资料或十倍预测；名单非即时买入，作者明确声明另抽。')
note('272-b005 272-b006 272-b007 272-b008 273-b000 273-b001 273-b002 273-b003 273-b004 273-b006 273-b010','historical_stock_opinion_and_schedule','600343/078/777/649、奥运/环保/国航/中核等题材与估值夸张，饮酒日程和技术不足休息。','不核企业宝藏、治理、军人背景或80/800价格，不作为当前金融建议；能力限制保留。')
note('273-b013 273-b014 274-b000 274-b001 274-b002 274-b003 274-b004 274-b005 274-b006','historical_stock_risk_profiles','等比6001399至24至12、600569、农业、000416/778/099、有色600432、ST600234等股性和基本面变化观点。','未核股价与企业事实；妖股、ST须技术的风险立场是作者当时说法，非当前推荐。')
note('275-b003 275-b004 275-b005 275-b006 275-b007 275-b008 275-b009 275-b010 275-b011 275-b012 275-b013 275-b014 275-b015 275-b016','historical_stock_comments','训练场及最后股票清单：医药钢铁、治理/收购、低价变动、科技、有色、002149建仓与中字头业务重组。','只原文历史点评，不核真实持仓、收益、公司治理或未来上市；未实现条件不变事实，不生成当下交易建议。')
note('276-b002','withheld_red_price_shortcut','原文不红盘与构成日底要求的历史捷径已读。','当前价格红绿与曾到的高点不必等价，时点未明；不编成普遍底分型判别规则，待核原字。')
note('276-b003 276-b006 277-b000','historical_index_divergence_and_personal','逆市营销自述、冰火两重天、个股受指数影响及为次年准备。','不验证真实操纵者或企业营业额；指数无方向不自动保证逆市股票安全。')

relations={
 'lower-l089-c-stage-stage-not-ordinary-oscillation':[('中阴阶段','中枢震荡','related')],
 'lower-l089-c-stage-higher-must-five-center':[('中阴阶段','走势中枢','related')],
 'lower-l089-c-stage-center-not-consolidation-apple':[('走势中枢','盘整','distinguishes')],
 'lower-l089-c-stage-consolidation-not-necessarily-weaker':[('盘整','趋势','related')],
 'lower-l089-c-stage-policy-one-force-not-total':[('政策风险','市场分力','related')],
 'lower-l090-c-stage-boll-auxiliary-not-absolute':[('布林通道','中阴阶段','related')],
 'lower-l090-c-stage-boll-first-point-sequence':[('布林通道','第一类买卖点','related')],
 'lower-l090-c-stage-boll-second-point-lag':[('布林通道','第二类买卖点','related')],
 'lower-l090-c-stage-boll-chart-period-not-one-to-one':[('周期K线图','级别','distinguishes')],
 'lower-l090-c-stage-traps-require-center-oscillation':[('市场陷阱','中枢震荡','requires')],
 'lower-l090-c-stage-traps-need-force-comparison':[('市场陷阱','动力学','related')],
}
for r in rows:r['relations']=[{'source':s,'target':t,'type':kind} for s,t,kind in relations.get(r['id'],[])]

by_passage=defaultdict(list)
for r in rows:
    for e in r['evidence']:by_passage[e['passage_id']].append(r)
for item in pending:
    item['lesson_numbers']=sorted({int(passages[x]['unit_id'].split('-')[1]) for x in item['passage_ids']})
    if item['id'].endswith('figure-makers-and-late'):
        item['lesson_numbers']=[89,90];item['figure_ids']=[f['id'] for f in figures]
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
      'related_existing_claim_ids':retained_ids,'note':'理论结构必经与BOLL辅助概率分开；级别和指标周期不固定换算，构成/确立及预期/事实按日期分层。'},'4_reverse_check':inverse}})
for f in figures:
    key=(f['pdf_page'],int(f['id'].rsplit('fig',1)[1]))
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=figure_notes[key],
      figure_source_review='11图明确文后见stage-c-l089-l090-figure-applied.json；其余7图截止日或制作人未核。',
      linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger)==276 and len({x['passage_id'] for x in ledger})==276
def dump(suffix,data):
    (OUT/f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x,ensure_ascii=False,separators=(',',':')) for x in data)+'\n',encoding='utf-8')
dump('reviewed.jsonl',rows);dump('coverage.jsonl',ledger);dump('pending.jsonl',pending);dump('figures.jsonl',figures)
summary={'stage':'C','schema_version':metadata['schema_version'],'graph_version':metadata['graph_version'],'lessons':[89,90],'document_id':DOC,'reviewer':REVIEWER,
 'passages_read':276,'claims':len(rows),'evidence':sum(len(r['evidence']) for r in rows),'importance_counts':dict(Counter(r['importance_level'] for r in rows)),
 'new_concepts':sorted({x for r in rows for x in r['concepts']}-set(concepts)),
 'whole_lesson_semantic_read_complete':True,'technical_extraction_complete':False,'four_round_review':True,'independent_review_claimed':False,
 'visual_pdf_pages':list(range(250,278)),'figure_objects_viewed':18,'figure_origin_counts':dict(Counter(f['origin_status'] for f in figures)),
 'pending':[x['id'] for x in pending],
 'source_passages_snapshot_sha256':SOURCE_SHA,'retained_source_links_in_ledger_only':True,'database_mode':'ro','formal_import':False,
 'acceptance':'276段四轮审读、28页及18图检查；中阴结构条件与BOLL辅助、跨周期选择与当时确认状态分开，增量待预检发布。'}
(OUT/f'{BASE}.summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
db.close();sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(summary,ensure_ascii=False))
