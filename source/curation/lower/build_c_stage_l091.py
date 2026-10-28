"""Materialize the manually read lower 91 batch; SQLite is read-only.

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
BASE='c_stage_l091'
REVIEWER='Codex 主代理 / 阶段C下册91课同模型四轮复核'
SOURCE_SHA='2efb9fa4564f8c05399acacce21f5c6b030683b51a612b163500644b6b318138'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
db.row_factory=sqlite3.Row
metadata={r['key']:json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version']=='1.1.0'
assert hashlib.sha256((KB/'sources/volume_2.pdf').read_bytes()).hexdigest()=='5332cd1b60381c47ceb81358db6bbb47882efd074fc5c869dcc3002aaed1b5c0'
passages={r['id']:dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id BETWEEN 'lesson-091' AND 'lesson-091' ORDER BY pdf_page,block_index,id")}
assert len(passages)==119
assert hashlib.sha256(json.dumps(sorted(passages.values(),key=lambda p:p['id']),ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==SOURCE_SHA
old={r['id']:dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts={r['label']:dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical={label:r['label'] for r in concepts.values() for label in [r['label']]+json.loads(r['aliases'])}
figures=[dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 277 AND 290 ORDER BY pdf_page,id',(DOC,))]
assert len(figures)==9
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
 (278,1):'大/小周期16种状态表A至P，绘者未核；排列不证明16种皆可同时到达，也非正文8行矩阵原证明',
 (278,2):'四种周日恶劣次序整理图有网站水印，绘者未核；第四值得参与是图中加语，正文只说可能转机',
 (279,1):'四状态六条允许转换的线图有网站水印，绘者未核；箭头由正文独立支撑，图未给变量确认的实时算法',
 (280,1):'12/18嵌文、图头光标12/17而行情至12/18，制作人未核；图框写5F中枢而正文说1分钟下跌第二中枢，不能用图框改正文级别',
 (282,1):'12/20嵌文、图头12/21后期，4812.4起上行与4920附近中枢；不倒填第二中枢或线段已完成',
 (284,1):'2008展望旁2009/12/31年线和2009/03/31季线，后期；不能用未来K线认证未收盘时预测',
 (287,1):'12/25嵌文、12/26图，5209附近第二中枢及5210中间位置；后期，不倒填当时三种后续选择',
 (288,1):'12/27嵌文、12/28图，30分钟BOLL(20,2)收口及后续突破；仅正文支持选择例，不提升图参数为唯一算法',
 (289,1):'光标12/27但行情至12/28，后期；大5分钟框和5240条件分开，不从图自动重算九线段'
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
    pending.append({'id':'lower-l091-c-stage-pending-'+slug,'status':'pending','passage_ids':[pid(s) for s in shorts.split()],
                    'description':description,'suggested_action':action,'blocks_full_semantic_extraction_completion':blocker,'reviewer':REVIEWER})




# Selected after the entire lesson and source figures were read, then reversed.
c(91,'illness-three-points-metaphor','277-b002 277-b003 277-b004','作者把未病、欲病、已病的界限对应相应级别一、二、三类买卖点，说明上涨踏空也可称病，涨跌之病是相对的。','第一类买卖点|第二类买卖点|第三类买卖点|级别|操作策略',2,'疾病仅教学比喻，不作医学诊断；相应级别和涨跌相对保留，不以病名替代买卖点定义。')
c(91,'parts-center-capability','277-b006 277-b007','在第91课所论走势分解配件中，作者把线段及各级走势类型归为能构中枢，笔归为不能构中枢，并称这是笔与前者的最大区别。','笔|线段|走势类型|走势中枢|表里关系',1,'范围是本课所讨论配件；83课可设计笔构最小中枢但不稳及84课可替代入口原话仍保留，未有明确撤回，不自动按时间覆盖。',['第91课所论走势分解配件'],ambiguity='stroke_center_cross_lesson_scope')
c(91,'stroke-theorem-current-two-phases','277-b008 277-b009','作者称缠中说禅笔定理为：任何当下、任一时间周期K线图，走势处于明确方向的笔中，位置只有分型构造中或分型确认后延伸为笔两类。','笔定理|笔状态|笔|分型|周期K线图',1,'记录作者定理断言，不声称已形式证明有限历史边界、初始笔不足等所有实时情形；时间周期K线不是固定中枢级别。')
c(91,'two-state-variables','277-b010','笔状态用两变量数组表示：第一变量1为向上笔、-1为向下笔；第二变量0为分型构造中、1为分型确认延伸为笔的过程。','笔状态|笔定理|笔|分型',1,'1/-1是方向符号不是收益，第二变量分型确认的具体实时算法本段未给，后段四元含义一并查。')
c(91,'four-state-meanings','277-b011','四种笔状态中，(1,1)向上笔延伸，(-1,1)向下笔延伸，(1,0)向上笔出现顶分型构造，(-1,0)向下笔出现底分型构造。','笔状态|笔|顶分型|底分型',1,'0不等于笔方向已反转，(1,0)是上笔中的顶构造而非下笔延伸；符号按原数组意义转写。',figs=((278,1),))
c(91,'six-allowed-state-transitions','277-b012 278-b000','作者列允许的笔状态转换：(1,1)只到(1,0)，(-1,1)只到(-1,0)；(1,0)可到(1,1)或(-1,1)，(-1,0)可到(-1,1)或(1,1)，共六条有向连接。','笔状态|笔定理|笔|分型',1,'六条由正文逐项列出；不把图的所有跨周期排列当此单周期状态任意转换，也未给零态确认或回原态的完整检测程序。',figs=((279,1),))
c(91,'extension-cannot-directly-reverse','277-b012 278-b000','在这套连接中，(1,1)不能直接连(-1,1)或(-1,0)，(-1,1)也只能先到(-1,0)而非直接向上延伸。','笔状态|笔|分型',1,'是作者该状态模型的转换限制，不声称读者看两个不连续采样时点也不可能跨过中间状态。')
c(91,'larger-extension-filters-small-waves','278-b001','考察1分钟与5分钟K线图，5分钟仍为(1,1)或(-1,1)时，小图此前波动尚未改变该大图延伸状态；最少关心5分钟图者可过滤这些波动。','表里关系|笔状态|周期K线图|操作级别',1,'前提是大图状态仍未变，不是小波动永远无价值；两图周期与正式中枢次级别不作固定同一。',['第91课1/5分钟周期图例','5分钟图仍为笔延伸状态','操作者至少关注5分钟图'])
c(91,'both-up-small-warning-needed','278-b002','5分钟与1分钟均(1,1)时，作者认为大图不会在随后几分钟马上改变；大图要成(1,0)，小图至少先出现(1,0)或(-1,1)，绝大多数情况下会到(-1,1)。','笔状态|表里关系|周期K线图|确认',1,'至少的或条件与绝大多数不同，不能改成小图一定必须先确认向下笔；原文几分钟不是统一时间保证。',['第91课1/5分钟两图均向上笔延伸的例'])
c(91,'one-bar-warning-and-confirmation','278-b003 279-b000','5分钟(1,1)时，小图1分钟(1,0)是警告；若只在一个5分钟K里不足以破大图结构，若该小图构造被确认，则成更重要、向欲病发展的警告。','笔状态|表里关系|周期K线图|确认',1,'只在一根5分钟K中的范围和确认区别保留；原文被确认的分型对象/实时边界尚需与零态定义对读。',['第91课5分钟(1,1)下的一分钟警告例'],ambiguity='zero_state_confirmation_reference')
c(91,'small-down-large-zero-confirmation','279-b001','小图(-1,1)出现且导致5分钟(1,0)形成，作者比为欲病向已病发展；大图(1,0)再确认向(-1,1)发展才称已病。','笔状态|表里关系|确认|周期K线图',1,'小图转下不自动等于大图已病，大图零态形成与反向笔确认分层。',['第91课1/5分钟由上笔到下笔的分析例'])
c(91,'week-day-four-worst-order','279-b002','作者以周/日笔状态列下跌四种次序：最恶劣为周(-1,1)/日(-1,1)，其次周(-1,1)/日(-1,0)，第三周(-1,0)/日(-1,1)，第四周日均(-1,0)可能转机；第二三仅技术高者可考虑，最恶劣则即使技术高也回避。','笔状态|表里关系|市场风险|操作熟练程度',1,'第四只是可能转机须走出来，网站图的值得参与不是正文无条件结论；疾病轻重非量化损失排名。',['第91课2007年12月17日周日状态例'],figs=((278,2),))
c(91,'dec17-worst-or-fourth-pending','279-b002','12月17日周(-1,0)、日(-1,1)状态下，作者重点等日(-1,0)且周仍零态以向第四种发展；若日下笔延续破周零态，则周日均下延转最恶劣，尚待市场选择。','笔状态|表里关系|确认|走势预测',1,'这是当时两支条件，不从后期行情倒填所选分支，更不推广任意周日组合始终只有两个未来选项。',['2007年12月17日当次周日状态'])
c(91,'eight-row-state-matrix-count','279-b003','作者提出按1、5、30分钟及日周月季年记录8行状态数组，每行四状态，称可能情况为4^8，表示走势病情的组合记录。','笔状态|周期K线图|表里关系',2,'4^8为原文组合计数，未独立证明所有笛卡尔积组合同时可达；不将这些时间周期当固定中枢级别。')
c(91,'machine-profit-author-proposal','279-b004 279-b005','作者设想用大型计算机监控有限允许状态转换、找高效率转折并买卖，自称可构造自动赚钱的机器，认为效率研究是数学问题。','笔状态|操作策略|市场风险',4,'仅作者设想，未给执行算法、证明、数据或交易成本/成交实现，不认证机器永动获利或项目已实现自动交易。')
c(91,'three-periods-sixty-four','279-b006 280-b000','一般人可只关注三个连续周期，作者举1/5/30分钟并称对应64种状态，又借此类比易经。','笔状态|周期K线图|表里关系',2,'64为候选组合数，不证明全部实际可达；易经是作者联想，不把数字相同当预测有效证据或补交易规则。')
c(91,'stroke-layer-not-whole-diagnosis','280-b002 280-b003','作者明确说仅笔这一重表里关系不足精确诊断，另一重关系可能已显出问题，不同关系之间还相互作用，需要进一步研究。','笔状态|表里关系|笔|走势分解',1,'不把本课四状态就视为完整走势诊断算法；其他关系在此未完整给出，不自编全部生克表。')
c(91,'dec18-week-day-4778-choice','280-b006','12月18日作者仍说周图(-1,0)，日图须在4778上制造(-1,0)才保留转机，否则周日可能向更差发展。','笔状态|表里关系|底分型|确认',2,'4778为该次周日例，不是所有底分型统一阈值；条件尚待形成。',['2007年12月18日4778附近周日状态'])
c(91,'dec18-month-4778-stroke','280-b007','作者以12月是否破4778区分月K包含与继续向下月笔；若破而月向下笔展开，须新月底分型之前不谈中级上升。','包含关系|笔|底分型|操作级别',2,'月线范围不否认小反弹，12月当时未收盘，不将条件分支当已发生。',['2007年12月18日当月4778条件分析'])
c(91,'dec18-one-minute-end-region','280-b008 281-b000','5209起1分钟下跌若在4778之上结束，作者认为最坏局面不立即发生、反抽可收敛；若下破，则视为大级别下跌第一段，等相应下跌结束才有中线站稳机会。','背驰|走势类型|级别|反抽',2,'两支限该例，不能仅任何价格破位就判任意大级别下跌已完整构成。',['2007年12月18日5209起1分钟下跌'])
c(91,'dec18-second-center-sell-then-watch','281-b001','作者12月18日称该1分钟下跌已有两个中枢，早盘反抽为第二中枢三卖；其后等是否背驰，更看背驰后反抽会否受阻第二中枢区间，受阻则对多头不利。','第三类卖点|背驰|走势中枢|反抽',1,'已有三卖不等于背驰已经发生；图框写5F与正文1分钟对象差别待核，不以绘者标号改正文。',['2007年12月18日5209下跌的第二中枢'],figs=((280,1),),ambiguity='figure_center_label_level')
c(91,'dec18-4778-trap-author-scenario','281-b003','作者在当时大背景下断言跌破4778仍会构造背驰、成为空头陷阱，并认为若不能直接突破5200则可等待这个下破情景。','空头陷阱|背驰|反抽|走势预测',4,'保留作者历史条件预言，不变任何价位跌破必背驰的通用定理；90课辨中枢震荡或移动的条件仍在。',['2007年12月18日该次4778及5200情景'])
c(91,'petro-24-wine-not-price-guarantee','281-b004','作者明确把中石油24元称为酒话，14元则是其愿望且估计未必给；另述30分钟图的线段类下跌应开始关注类底背驰。','走势预测|类背驰|线段|市场风险',3,'酒话和愿望不是必须到达的目标或买点；30分钟图上线段类对象不自动当严格30分钟走势类型背驰。',['2007年12月18日中石油自述'])
c(91,'dec19-daily-bottom-not-all-clear','281-b009 282-b001','12月19日作者说日底分型已构造、早盘冲高基本确认且初回调为超短二买，但强调后续必须连续站5日线，否则仍只是中继，需配合5分钟震荡。','底分型|第二类买点|均线|确认|中枢震荡',1,'基本确认与连续站5日线后续要求并存，不静默把基本确认升级为所有层次完全确认。',['2007年12月19日日底及超短二买案例'],ambiguity='basic_confirmation_vs_continued_hold')
c(91,'dec19-divergence-five-center','281-b009 282-b000','作者把12月19日反抽归于5209起1分钟下跌背驰，其后至少需形成5分钟中枢，再以其三类点判断短线。','背驰|走势中枢|第三类买卖点|级别',1,'背驰后的结构前提与方向选择分开，尚未形成的中枢/三类点不倒填已确认。',['2007年12月19日该1分钟下跌背驰后的反抽'])
c(91,'dec20-break-5032-not-yet-hold','282-b005','12月20日已攻克5032、维持5000大震荡，下一步才站稳5032准备攻5209；作者以能否站住区分超短强弱。','颈线|中枢震荡|确认|反抽',2,'突破与站稳顺序保留，不因后期图直接宣布当时所有任务完成。',['2007年12月20日5032与5209例'])
c(91,'dec20-leg-incomplete-next-center','282-b006 282-b007','作者称12月20日整天一线段未完成；4812起已有4920附近首个1分钟中枢，还需等第二个以看1分钟上涨是否确立，再看顶背驰。','线段|完成|走势中枢|上涨|背驰',1,'未完线段和未成第二中枢保留；不把当天拉升或次日图作为已有完整上涨的证据。',['2007年12月20日4812起该次反抽'],figs=((282,1),))
c(91,'dec20-petro-bottom-constructed','282-b008 283-b000','12月20日作者说中石油底分型已构造而确认仍在后，30分钟图线段类背驰带来回升，30元附近至少可构较大中枢，再看三类点决定续涨或破位。','底分型|确认|类背驰|走势中枢|第三类买卖点',2,'构造不等于确认，图周期不等于结构级别；后续中枢仍是预期。',['2007年12月20日中石油30附近案例'])
c(91,'forecast-year-close-not-final','283-b007 283-b008 283-b009','12月20日2008展望因当年尚未收盘，只给约数框架：6124与年K实体半位约3800作箱边，四分后约4355/5555作次级支持阻力，6124加箱宽约8400仍只是假设边界。','走势预测|价格区间|均线|级别',4,'年收盘未知须保留，所有约数不改为独立精算；2009年季图不能认证当时未来预测或补成精确年收盘。',['2007年12月20日2008展望','2007年年K尚未最终收盘'],figs=((284,1),))
c(91,'forecast-quarter-condition','284-b001','作者在该2008展望中说若次年一季度低于本季低点、又不能立即创新高6124，则季顶分型构成，随后看5季度均线是否有效破坏。','顶分型|均线|确认|走势预测',3,'低破与不能创新高联合、季与月不同；是未发生时的条件预测，非当时季顶已构成。',['2007年12月20日对2008一季的展望','次年一季低于本季低点且未立即创新高6124'])
c(91,'forecast-2008-no-new-high-possible','285-b002 285-b003','作者也保留2008不突破6124、或只略过后陷阱的选项，前提为期货未推出，并出现政策趋严或外围大震荡；称虽暂悲观但须防。','走势预测|政策风险|市场陷阱',4,'这是未来一年条件选项，不把看好长期市场改成该年必创新高，也不据日期自动撤回所有更长周期旧观点。',['2007年12月20日对2008的条件展望','指数期货不能推出','政策严厉程度继续加大或外围市场再出现超大震荡'])
c(91,'dec21-two-observation-signals','285-b008 283-b001','对当次反抽，作者在日顶未现且1分钟上涨未背驰时等待卖点；能辨1分钟背驰者可更精细处理，日线笔延伸者则等日顶。','顶分型|笔|背驰|操作级别',2,'两种观察粒度不是同一信号，未出现的联合范围不作永远持有保证。',['2007年12月20/21日当次反抽'])
c(91,'dec24-neckline-break-await-confirm','286-b001 286-b002','12月24日5209颈线已突破但有效性仍待确认，确认后才看约5600基本涨幅；确认不了则回震荡，站稳前可有超短折腾。','颈线|确认|突破|中枢震荡',1,'突破待确认和条件目标保留，不把突破一刻当确认或保证5600。',['2007年12月24日5209颈线'])
c(91,'dec24-second-center-not-yet','286-b003','12月24日作者明确说日顶未出现、1分钟第二中枢也未出现，未来第二中枢可能因此前拉升而震荡较大。','走势中枢|顶分型|完成|市场风险',1,'未出现不改成已形成，较大震荡为预期，不由次日图倒填当天完成。',['2007年12月24日该1分钟上行'])
c(91,'dec24-ideal-upgrade-path','286-b004','作者列理想路径：5209附近先成第二1分钟中枢，再上后回跌确认5209、顺势将第二中枢扩展为首个5分钟中枢，才可能向5分钟上涨发展。','中枢扩展|走势中枢|上涨|确认|级别',2,'理想与可能不能改成必然，形成更高首中枢不充分保证完整高一级趋势已经确立。',['2007年12月24日5209附近条件展望'])
c(91,'dec25-center-formed-midpoint','286-b007','12月25日作者称5209附近已形成1分钟中枢，中间位置5210，与5209相差1点。','走势中枢|价格精度|完成',2,'一天前未成与当日已成区分，1点为原文差值，不用EPS消除差别或擅改两价相同。',['2007年12月25日该中枢'],figs=((287,1),))
c(91,'dec25-three-branches','286-b010','第二中枢后作者列三支：三卖则日向下笔较大调整；震荡成更大中枢而向5分钟扩展；或三买，但已有两个中枢，即使不背驰也须谨慎，更可能背驰后回跌成大中枢。','第三类买点|第三类卖点|中枢扩展|背驰|笔',1,'三买不是永涨保证，两个中枢不等于必背驰；不同分支与可能性保留。',['2007年12月25日该第二1分钟中枢'],figs=((287,1),))
c(91,'dec25-strong-exception-larger-center','286-b011 287-b000','除三买后最强势、无背驰而继续1分钟中枢上移这一支外，作者认为其他支至少最终形成更大中枢，故重视震荡操作。','第三类买点|背驰|中枢上移|中枢扩展|中枢震荡',1,'明确例外不能省略，不把所有三买后必扩展大中枢当定理。',['2007年12月25日三分支分析'],exceptions=['三买后最强势、不背驰而继续1分钟中枢上移'])
c(91,'oscillation-switch-stock-skill','287-b001 287-b002','作者认为散户在上升途中中枢震荡可换股提高效率，但要求熟悉板块轮动节奏；比较刚顶背驰与首中枢上移、进入阻力区与确认脱离阻力区等图形。','中枢震荡|板块轮动|背驰|中枢上移|操作熟练程度',2,'效率为作者方法主张，无独立回测；换股需能力与图形，不用题材名单替代买卖点。',['所述上升中途中枢震荡','具有板块轮动及图形辨识能力'])
c(91,'midpoint-numeric-reference-not-exact','287-b004 287-b005','作者用5210中间位置提示当日高低点对应，可由一端估另一端的大致位置，但特别说关系未必精确、只作参考，关键仍是图形。','走势中枢|价格区间|价格精度|技术分析',2,'原文没有在此写具体镜像算式，不自补精确公式、误差阈值或保证未来高低点。',['2007年12月26日5210震荡例'])
c(91,'boll-break-can-be-bigger-oscillation','287-b007 288-b000','12月26日30分钟BOLL收口提示三种选择，不是必向一个方向突破；升级成更大级别震荡也是选择，作者称时间换空间。','布林通道|中枢震荡|中枢扩展|级别',1,'收口不预定方向，也不排除结构扩展；时间换空间不是固定时长升级算法。',['2007年12月26日该中枢及30分钟BOLL'])
c(91,'boll-select-by-pattern-structure-first','288-b006 288-b007 289-b000','12月27日作者强调中枢须按对应图形选择BOLL周期，并非任意级别收口都有效；走势类型分解才是根本，不能只看MACD。','布林通道|MACD|走势分解|周期K线图|级别',1,'有效选择未给全参数算法；该文一般有效是经验辅助，次日图不证明100%预测率。',['2007年12月27日该中枢BOLL选择说明'],figs=((288,1),))
c(91,'dec27-no-divergence-before-third','289-b001','作者说12月27日先下段再一直上段至14:17，从该1分钟上涨走势角度尚无背驰，因所论中枢三买还未出现，其顶背驰须在三买之后讨论。','背驰|第三类买点|走势类型|线段',1,'范围限该次1分钟上涨，不推广所有盘整背驰也须三买；一个未完上段不等于完整走势背驰可判。',['2007年12月27日当次1分钟上涨及其三买未出状态'],ambiguity='trend_vs_consolidation_divergence_scope')
c(91,'dec27-5240-third-buy-two-paths','289-b002','当次向下笔回跌若不回5240下，作者称三买成立，随后或顶背驰回跌成5分钟中枢，或不背驰继续上移成第三个1分钟中枢。','第三类买点|笔|背驰|中枢上移|中枢扩展',1,'回跌条件及两个后续保留；不把正在回跌任一瞬时未到5240当正式三买已完成。',['2007年12月27日该次向下笔回跌不回5240下'])
c(91,'later-third-buy-entry-low-value','289-b003','作者认为该类上行中一般第二中枢以后三买缺少新的介入意义，正确程序应在首中枢三买完成最后介入，其后持有等整个类型完成。','第三类买点|走势中枢|完成|操作级别',1,'一般与既定操作级别保留；不否定后续三买形式存在，不直接套任何更大级别仓位。',['第91课所论该级别上行及第二中枢后的三买'])
c(91,'dec27-return-nine-case-upgrade','289-b004','若本次回5240下，作者称已有九段线段震荡并将扩展5分钟中枢；所以无论有无该三买，所列后续为5分钟震荡或1分钟中枢上移。','线段|中枢扩展|中枢震荡|第三类买点|中枢上移',1,'九段是该例既有震荡结构，不是任意九线段必升级；后期图大5分钟框不能反填12/27条件已满足。',['2007年12月27日该次回5240下的分支'],figs=((289,1),))
c(91,'first-five-center-high-not-always-good','289-b006','作者说该例即使扩展5分钟或30分钟，后续三买可推动相应上涨发展；继续1分钟上移只是抬高首5分钟中枢位置，太高未必好，若不能有第二中枢便只盘整，后续回杀力度反更大。','中枢扩展|第三类买点|中枢上移|走势中枢|盘整|上涨',2,'可发展不等于已形成完整上涨；首中枢太高未给数值门槛，不能将中枢越高必更牛。',['2007年12月27日该次1分钟上行及未来较大中枢'])

keep('277-b007','lower-l083-c-stage-stroke-center-possible-less-stable lower-l084-c-stage-fractal-only-recursion-start-optional','83允许设计笔作最小中枢部件但不稳，84入口可替代须唯一；91配件表不自动全局撤回前文。')
keep('277-b009 279-b003','lower-l063-chart-period-not-center-level lower-l084-c-stage-level-not-time-classification','笔状态按各周期K线图，时间周期不是严格走势中枢级别的固定一一映射。')
keep('281-b003','lower-l090-c-stage-traps-require-center-oscillation lower-l090-c-stage-traps-need-force-comparison','4778历史陷阱预言不能取消90课须辨中枢震荡/移动和力度的定义。')
keep('281-b009 282-b000','lower-l089-c-stage-higher-must-five-center','89课1分钟下跌背驰后的5分钟中枢必经前提保留，91另给新案例。')
keep('287-b007 288-b007','lower-l090-c-stage-boll-contraction-expand-or-end lower-l090-c-stage-boll-chart-period-not-one-to-one','90课收口为较低中阴扩展或结束的辅助，91明确不是任意周期收口都有效。')

issue('stroke-center-cross-lesson','277-b006 277-b007','91说笔不能构中枢，83说可设计笔构最小中枢程序但不稳，84又允许替代入口；没有明确文字说明撤回或二者适用体系边界。','并列原句及配件语境，不自动以日期覆盖；后续寻找作者明确范围说明。',True)
issue('zero-state-reference','277-b009 277-b010 277-b011 278-b000 278-b003 279-b000','第二变量1称分型确认延伸，0又分别上笔顶/下笔底构造；零态被确认、回同向一态或转反向一态的实时分型对象与确认步骤未全定义。','保留四个语义和六条正文连接，不能把零态直接当已反转，也不编出自动状态识别器。',True)
issue('matrix-reachability-and-profit','277-b009 279-b003 279-b004 279-b005 279-b006','任意当下四态、4^8及64组合、自动赚钱机器为作者断言；跨周期联动、初始历史边界、全部组合可达性及成交成本未给完整证明/实现。','组合计数与实盘可达、数学模型与可实现盈利分开，不宣称穷举状态即获利保证。',True)
issue('figure-makers-and-late','279-b002 281-b001 282-b007 283-b008 287-b007 289-b004','9图已看，5图明确文后；4图绘者未核。整理图加第四值得参与、280框5F与正文1分钟第二中枢不同、2009年季图均不能改正文。','五图登记后期，其他维持未核；图加语不作作者直接观点，不从未来框线倒填完成。')
issue('confirmation-scope','281-b009 282-b001 286-b001 286-b003 286-b007','基本确认、连续站5日线、突破5209待确认，以及12/24第二中枢未出到12/25已成，确认对象与时点不能压缩同词。','按日期保留不同对象状态，不把基本确认等同所有层次最终确立；不添统一百分比或根数。')
issue('divergence-and-nine-segment-scope','289-b001 289-b002 289-b004','本次1分钟上涨的顶背驰须三买后和九线段回5240升级是案例说明；未重写盘整背驰与所有九线段成中枢条件。','与既有正式定义对照，不把任意背驰强制三买前置，或任意九线段必升级。',True)
issue('forecast-and-numeric-reference','281-b004 283-b008 283-b009 284-b001 285-b003 287-b005','24酒话/14愿望、年度约数和条件预测、5210高低对应参考没有独立实测或完整精算规则。','保留未收盘、条件、约数与参考语气；不拿2009图认证预测或把镜像关系补成精确公式。')

note('277-b005 280-b001','medical_metaphor_context','肺大肠表里、生克及对中医学习的比喻已读。','只是作者教学语境，不发布医学事实、诊断或健康建议，不以医学比喻证明市场定理。')
note('280-b004 281-b002 281-b005 281-b007 281-b008 282-b002 282-b003','historical_schedule_and_capability','休息、5200/5032尚待收复、强股能力门槛、青蛙和陪练比喻。','自述和能力条件保留，不认证操盘结果或后续必然；具体状态及底分型另抽。')
note('283-b002 283-b003 283-b004 283-b005','historical_policy_opinion','指数期货审批传闻、利益集团、创业板与交易成本、错字修辞。','未核当时程序与决策者，不作现行政策或作者影响力证据。')
note('283-b010 283-b011 284-b000 284-b002 284-b003 284-b004 285-b000 285-b001 285-b004 285-b005','historical_annual_forecast_context','2008年250日两次考验、年K十字星、平台三角锯齿、两个顶三个底、2/3股票阴线及四类挖井者、印花税期望与习惯调整。','全部是2007年末作者预测/比喻，未核后验准确率与收益；不从2009图反填已预知，未收盘约数及悲观分支另抽。')
note('285-b007 285-b009 285-b010 285-b011 285-b012','historical_battle_context','加息鸡血、周末媒体5209、冷枪和喊多头万岁。','不认证加息实际因果或资金行为，不制成操纵流程。')
note('286-b005 286-b008 286-b009 287-b006','historical_learning_and_rotation','年末做账与2006工行不同、5日线为何与分型相关的思考题、能力不同的短差及次日说多数人知道。','原文没有在此给完整5日线推导，不替作者补证明；守5日线不变任何周期固定法则。')
note('288-b001 288-b002 288-b003 288-b004 289-b005 289-b007 290-b000 290-b001','historical_private_and_reminders','年K收盘参照、基金奖金推测、12元未买/PE酒话、等待市场选择与日线无信号、元旦时间修辞。','未核匿名股/交易/奖金制度，不补公司身份；不把无信号放大为永久无风险或精确大涨日期。')

relations={
 'lower-l091-c-stage-parts-center-capability':[('笔','线段','distinguishes')],
 'lower-l091-c-stage-stroke-theorem-current-two-phases':[('笔定理','笔状态','defines')],
 'lower-l091-c-stage-four-state-meanings':[('笔状态','顶分型','related'),('笔状态','底分型','related')],
 'lower-l091-c-stage-six-allowed-state-transitions':[('笔状态','分型','related')],
 'lower-l091-c-stage-larger-extension-filters-small-waves':[('表里关系','笔状态','related')],
 'lower-l091-c-stage-stroke-layer-not-whole-diagnosis':[('表里关系','走势分解','related')],
 'lower-l091-c-stage-boll-select-by-pattern-structure-first':[('布林通道','走势分解','related')],
}
for r in rows:r['relations']=[{'source':s,'target':t,'type':kind} for s,t,kind in relations.get(r['id'],[])]

by_passage=defaultdict(list)
for r in rows:
    for e in r['evidence']:by_passage[e['passage_id']].append(r)
for item in pending:
    item['lesson_numbers']=sorted({int(passages[x]['unit_id'].split('-')[1]) for x in item['passage_ids']})
    if item['id'].endswith('figure-makers-and-late'):
        item['lesson_numbers']=[91];item['figure_ids']=[f['id'] for f in figures]
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
      'related_existing_claim_ids':retained_ids,'note':'笔状态按时间周期K线，非中枢级别固定换算；六转换与联合可达性分开，理论断言不冒充实盘保证。'},'4_reverse_check':inverse}})
for f in figures:
    key=(f['pdf_page'],int(f['id'].rsplit('fig',1)[1]))
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=figure_notes[key],
      figure_source_review='五图后期见stage-c-l091-figure-applied.json，余四图制作人未核；两张网站整理图不独立升级正文。',
      linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger)==119 and len({x['passage_id'] for x in ledger})==119
def dump(suffix,data):
    (OUT/f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x,ensure_ascii=False,separators=(',',':')) for x in data)+'\n',encoding='utf-8')
dump('reviewed.jsonl',rows);dump('coverage.jsonl',ledger);dump('pending.jsonl',pending);dump('figures.jsonl',figures)
summary={'stage':'C','schema_version':metadata['schema_version'],'graph_version':metadata['graph_version'],'lessons':[91],'document_id':DOC,'reviewer':REVIEWER,
 'passages_read':119,'claims':len(rows),'evidence':sum(len(r['evidence']) for r in rows),'importance_counts':dict(Counter(r['importance_level'] for r in rows)),
 'new_concepts':sorted({x for r in rows for x in r['concepts']}-set(concepts)),
 'whole_lesson_semantic_read_complete':True,'technical_extraction_complete':False,'four_round_review':True,'independent_review_claimed':False,
 'visual_pdf_pages':list(range(277,291)),'figure_objects_viewed':9,'figure_origin_counts':dict(Counter(f['origin_status'] for f in figures)),
 'pending':[x['id'] for x in pending],
 'source_passages_snapshot_sha256':SOURCE_SHA,'retained_source_links_in_ledger_only':True,'database_mode':'ro','formal_import':False,
 'acceptance':'119段四轮审读、14页9图检查；笔状态转换、跨周期条件、作者理论断言与未核范围分开，五图后期，增量待预检发布。'}
(OUT/f'{BASE}.summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
db.close();sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(summary,ensure_ascii=False))
