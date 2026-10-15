"""Materialize the manually read lower 82--84 batch; SQLite is read-only.

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
BASE='c_stage_l082_l084'
REVIEWER='Codex 主代理 / 阶段C下册82至84课同模型四轮复核'
SOURCE_SHA='edd845cea6aa34f2f00b1413d75763f7a66c4b3782ac2a79aab759b87a9420c8'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
db.row_factory=sqlite3.Row
metadata={r['key']:json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version']=='1.1.0'
assert hashlib.sha256((KB/'sources/volume_2.pdf').read_bytes()).hexdigest()=='5332cd1b60381c47ceb81358db6bbb47882efd074fc5c869dcc3002aaed1b5c0'
passages={r['id']:dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id BETWEEN 'lesson-082' AND 'lesson-084' ORDER BY pdf_page,block_index,id")}
assert len(passages)==341
assert hashlib.sha256(json.dumps(sorted(passages.values(),key=lambda p:p['id']),ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==SOURCE_SHA
old={r['id']:dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts={r['label']:dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical={label:r['label'] for r in concepts.values() for label in [r['label']]+json.loads(r['aliases'])}
figures=[dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 189 AND 221 ORDER BY pdf_page,id',(DOC,))]
assert len(figures)==13
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
 (189,1):'三K顶分型的心理图解，箭头对照正文买卖三回合；www.chzhshch.net水印，绘者未核',
 (190,1):'三K不同情形表，含包含、长阳后小K、长上影及阴吞阳；表格是配图转述不独立新增条件',
 (190,2):'9月17/18/19日顶分型的小截图；旁边后续K线无完整日期，不据此认证未来结果',
 (191,1):'5月28至30与6月18至21的两组K线，第三K低破第一K及阴吞阳示意；正文非包含措辞保留',
 (191,2):'上证日线图内9/24正文但数据至10月并标6124.04，属于后期截图',
 (193,1):'9/25上证1分钟126至133及嵌入作者132/129不到半点文字；图中读数不补未写价格',
 (194,1):'上证1分钟101至136，9/26下跌与130附近第二类线段破坏答疑对象',
 (198,1):'9/28上证1分钟124至139，137结束后138/139回拉，配合130—131与136—137比较',
 (203,1):'图有140/141及10/09数据，却复制10/08时139段尚未确认文字；不能用后期标记倒填已完成',
 (204,1):'上证日线含4335.96和6124.04，10月中旬行情晚于内嵌10/08文字',
 (209,1):'10/10上证1分钟140至146，框140—143及嵌文区分中枢震荡区间与中枢区间',
 (213,1):'10/11上证1分钟140至147、144—147中枢及当时148尚未完成的正文',
 (220,1):'30分钟图头10/24、轴至10/25，嵌文10/22；图标6123.64与作者文本6124.04差异不改'
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
    pending.append({'id':'lower-l082-l084-c-stage-pending-'+slug,'status':'pending','passage_ids':[pid(s) for s in shorts.split()],
                    'description':description,'suggested_action':action,'blocks_full_semantic_extraction_completion':blocker,'reviewer':REVIEWER})

# Selected manually after the full sequential reading and original figure review.
c(82,'fractal-not-fractal-theory','189-b002 189-b003','作者明确区分其“分型”与数学分形：其理论逻辑自称直接来自市场走势，而非把市场外的先验数学分形理论套入市场。','分型|分形|技术分析',1,'这是作者对术语和方法来源的自我说明，不代替对分形数学或其他理论的外部评判。')
c(82,'top-three-psychological-rounds','189-b004 189-b005 190-b000','作者以已作包含处理的标准三K顶分型解释买卖三次较量：第二K创新高而小级别力度背驰，第三K攻击不能新高、大致呈小级别二卖；底分型反向。','顶分型|底分型|包含处理|市场分力|第二类卖点',3,'大致二卖不是每个顶分型都与唯一指定级别二卖精确同点；这是心理解释，不免除分型定义。',['经过包含处理的标准三K分型模型'],figs=((189,1),))
c(82,'inclusion-psychology-exception','190-b001','无包含的分型体现买卖双方较直接；一般包含体现犹豫观望及小级别中枢延伸、扩展，但作者明确排除长阴直接吞掉阳线的情形。','分型|包含关系|中枢延伸|中枢扩展|市场心理',3,'一般经验及例外保留；不把包含处理的形式定义换成心理测量。',['第82课分型心理分析'],['阳线被长阴线直接吃掉不属此处犹豫解释'],figs=((190,1),))
c(82,'long-first-small-next-continuation','190-b002','无包含顶分型中，第一K长阳、第二第三为小阴小阳时，作者认为真顶可能性小、绝大多数为中继，表现为小级别中枢上移后新中枢形成；例为上证9月17—19。','顶分型|中枢上移|走势中枢|市场心理',3,'三个K形态和无包含联用，可能性是作者经验，未给量化长短阈值或样本。',['无包含关系的顶分型','第一K长阳','第二第三K为小阴或小阳'],figs=((190,1),(190,2)))
c(82,'second-shadow-third-close-half','190-b003','若第二K长上影甚至长阴，第三K不能以阳线收在第二K区间一半之上，作者认为顶分型力度较大、成笔可能极大；6月18—21阴吞阳为所举较坏包含例。','顶分型|笔|包含关系|K线',2,'保留“以阳线收”的完整措辞，不能只改成任意收盘低于中点；可能极大不是必然成笔。',['第二K长上影或长阴','第三K不能以阳线收在第二K区间一半之上'],figs=((190,1),(191,1)))
c(82,'third-break-first-low-half','191-b000','在原文所谓“非包含关系处理后的顶分型”中，第三K跌破第一K底且不能高收到第一K区间一半之上，作者称为最弱、杀伤力较强的情形；例为5月28—30。','顶分型|K线|高低点',2,'PDF原页确有“非”字，暂不改写为“包含处理后”；两条联合价格条件及原措辞保留。',['第三K跌破第一K底','第三K不能高收到第一K区间一半之上','原文非包含关系处理后的范围措辞待核'],figs=((191,1),),ambiguity='source_inclusion_scope_wording')
c(82,'continuation-or-stroke-two-structures','191-b001','分型之后可为最终不成笔的中继型，或延续成笔；前者可看是否有效破相应5周期均线，后者可等待相反分型再操作。','分型|笔|均线|操作策略',2,'5周期与当前日/周K工具对应，日顶例看5日线，不能自动等同走势级别或保证反向分型时点。')
c(82,'choose-largest-local-center-example','191-b002 192-b000','作者在日顶分型区间例中要求选择小级别所成中枢中最大者，列5分钟或1分钟，一般最大5分钟，并称30分钟因时间不足不可能。','顶分型|走势中枢|级别|次级别',2,'保留本课日顶区间例的时间说法；与84课级别不对时间绝对承诺并列，不推广为所有日K必定5分钟级别。',['第82课日顶分型区间例'],ambiguity='cross_lesson_time_level_scope')
c(82,'third-sell-no-expansion-stroke','192-b000','相应5分钟或1分钟中枢出现三卖，且该卖点不形成中枢扩张，作者称几乎100%可肯定日线上成笔。','第三类卖点|中枢扩张|笔|走势中枢',1,'三卖和不扩张须同时保留；几乎100%是作者主张而非项目实测。',['第82课日顶对应的小级别中枢','出现第三类卖点','该卖点不形成中枢扩张'])
c(82,'no-stroke-break-top-needs-third-buy','192-b001','要不成笔并最终有效破坏该顶分型，作者要求出现某级别第三类买点；否则短暂新高也属假突破。','第三类买点|顶分型|假突破|笔',1,'第三买点是所述不成笔并有效破顶的必要条件，不是见任意级别三买即充分保证破顶。',['讨论日顶后不成笔且最终有效破坏顶分型'])
c(82,'no-daily-top-control-short-difference','192-b003','日线与5分钟配合时，小级别中枢震荡若日K尚无顶分型，作者认为无须退出，作短差也应控制数量，以免随时新高踏空。','顶分型|中枢震荡|操作级别|仓位',2,'这是该配合方法的持有取舍，不消除小级别卖点或适用于任何入场目的。',['第82课日线与5分钟配合方法','日K尚未出现顶分型'])
c(82,'continuation-third-sell-expansion-reentry','192-b003','顶分型对应小级别一二卖后看新中枢三类点；一般中继可在三卖后中枢扩展、盘整底背驰处重新介入，作者以9月7日前后周顶假破5周线并有小级别背驰为例。','顶分型|第三类卖点|中枢扩展|盘整背驰|均线',2,'一般情景不是三卖必定扩展；周顶例的假破5周与小级别背驰为联合解释。',['第82课分型与小级别走势配合方法'])
c(82,'sell-then-check-replenishment','192-b004','利用顶分型退出后须继续判断是否回补；一旦确认为中继应回补，否则等待笔完成。','顶分型|笔|操作策略|确认',2,'确认中继为回补前提，不是卖后无条件立即回补。')
c(82,'next-top-continuation-less-likely','192-b005','中继顶分型后，若相应小级别出现背驰或盘整背驰，作者认为下个顶分型继续中继的可能性明显降低。','顶分型|背驰|盘整背驰|市场心理',3,'明显降低不是归零，刹车比喻不提供精确概率。',['已有中继顶分型','其后相应小级别出现背驰或盘整背驰'])
c(82,'sep25-132-third-sell-case','192-b008','作者把9月25日13:46的132称为第三卖点，并强调与9:47的129相距不到半点。','第三类卖点|价格精度|走势中枢',4,'历史端点、时间和作者近似价差保留；不从图推精确价格或以此认证理论全局准确率。',['2007年9月25日132/129例'],figs=((193,1),))
c(82,'sep26-departure-return-not-complete','193-b003','9月26日作者描述1分钟走势正离开前5分钟中枢，何时完成仍待观察，完成后的回拉是否成三卖才是关键。','次级别|走势中枢|第三类卖点|完成',4,'离开尚未完成，不把正在下跌等同完整1分钟离开或已确认三卖。',['2007年9月26日当次离开'],figs=((194,1),))
c(82,'look-chart-not-follow-person','194-b007 194-b008','回应听作者话买600319者，作者要求按图上卖点先卖、买点回补来管理成本，并提示当时高位动态管理能力不足时没人保证承接风险。','买卖点|成本|操作策略|市场风险',3,'不将读者已经买入或作者提及代码当作当下买点证据。',['2007年9月26日600319答疑'])
c(82,'two-timeframe-tools-not-identical','195-b001','低周期图可用中枢与走势类型，高周期图可用分型、线段；作者认为这是分析同一走势的两套工具，不要求转过去的划分完全一致。','周期K线图|走势中枢|走势类型|分型|线段',1,'不把高低图上同词线段自动视为同级同端点，也不说任何不一致都可不检查。')
c(82,'130-case-second-type','195-b007','对9月26日读者指出上行未破130下段最后一笔的疑问，作者答该划分属第二种类型。','线段破坏|笔破坏|特征序列',4,'问题对象由上下文确定，回复未在此完整重演特征序列；不以读者猜测端点作作者确认。',['2007年9月26日130附近分段答疑'],figs=((194,1),))
c(82,'high-price-not-safety-guarantee','195-b004','作者对高价股更安全的问法，只说散户减少可使拉抬较容易，但特别大的调整时参与方不会硬抗。','市场风险|散户|主力资金',3,'不认可高价或百元就是安全的充分条件；仅当时答疑立场。',['第82课高价股问题'])

c(83,'stroke-center-possible-less-stable','196-b006 196-b007','作者明确说可以设计用笔构造最小中枢的程序，但认为稳定性很差，瞬时错单等能影响分型与笔；用线段受偶然因素影响较少。','笔|线段|最小级别中枢|分型',1,'可以与较少不能分别改成不允许和绝不受影响；这是选择基础部件的稳定性理由。')
c(83,'feature-fractal-psychological-confirmation','196-b008','作者用反复确认解释线段破坏的心理结构变化，认为特征序列分型用于勾勒这种变化、增强作为最小中枢部件的可靠性。','特征序列|分型|线段破坏|最小级别中枢|市场心理',3,'心理确认解释与严格元素数量分开；本课下一段三个特征序列分型的措辞另列待核。')
c(83,'first-case-psychological-pause','196-b010','第一种线段破坏的心理解释是首次反攻突破旧段最后打击、原方向再打击被扛住、反攻形成特征序列分型，从而至少形成停歇及最小中枢的心理基础。','线段破坏|特征序列|最小级别中枢|市场分力',3,'攻击比喻不能替代第一种情况的形式定义，也未把停歇说成确定大趋势反转。',['第83课第一种线段破坏的心理解释'])
c(83,'center-complexity-aftereffects','196-b011 197-b000','作者认为中枢是双方反复较量，越简单往往一方越强；超复杂中枢后一方虽胜，后续仍常反复，复杂程度可辅助判断动向。','走势中枢|市场分力|市场心理',3,'越简单/常反复为作者心理经验，不给未经来源的复杂度指标或概率。')
c(83,'adjacent-centers-anticipation','197-b001','同一趋势相邻中枢的形态复杂度常不同，作者归因于参与者按最近模板提前反应，提前变量改变合力结构。','走势中枢|趋势|市场心理|市场合力',3,'常有区别而非任何相邻中枢形态都必须不同。')
c(83,'second-case-time-and-domino','197-b002','作者把第二种破坏解释为反攻起初弱、以时间积累而原方向强；又提醒观察反攻是否快速蔓延成骨牌效应，反映分力趋同。','线段破坏|市场分力|市场心理',3,'缓慢积累和可能的骨牌效应均保留，不说第二种必然大跳水。',['第83课第二种破坏心理解释'])
c(83,'domino-prior-extreme-range','197-b003','一般第二类线段破坏一旦出现趋同性骨牌效应，作者认为至少回到前一高低点范围，表现为冲顶赶底的V形走势。','线段破坏|高低点|趋势转折|市场分力',3,'一般且一旦骨牌效应为联合范围，不把所有第二种破坏都要求固定回撤。',['第二类线段破坏','出现分力趋同的骨牌效应'])
c(83,'same-side-crowding','197-b004','作者把趋同骨牌效应对应多杀多、空杀空，特别是大趋势后一边倒再加速而突然逆转的场景。','市场分力|市场心理|趋势转折',3,'原侧参与者内部转向，不简化成任何加速都必立即反转。')
c(83,'sep27-no-third-sell-round-top-risk','197-b007','9月27日作者说1分钟结束后的回拉未成三卖，仍中枢震荡；中线需节后迅速突破站稳5500，否则圆顶可能增加。','第三类卖点|中枢震荡|圆顶|走势预测',4,'保留圆顶原称并独立建概念，不把已有圆底当圆顶同义。',['2007年9月27日当次行情'])
c(83,'sep28-legs-length-force','198-b004','作者在9月28日例中称130—131与136—137长度基本相等，可比较对应MACD柱面积的力度；137完成1分钟后，到138知前5分钟三卖不成，139仍给反应机会。','MACD|盘整背驰|第三类卖点|完成',4,'基本相等不是精确恒等；案例已有走势完成与参照中枢，不能只拿两波柱面积普遍判背驰。',['2007年9月28日130至139案例'],figs=((198,1),))
c(83,'postholiday-departure-retest-choice','199-b001','节后先完成1分钟离开，作者预期线段类上涨结束后成1分钟中枢，再等1分钟走势完成、回抽能否成原5分钟中枢三买；成则攻击上行，不成则继续向30分钟震荡发展。','走势中枢|次级别|第三类买点|完成',2,'分层完成顺序及特别大消息例外保留，不能未完成离开就宣布三买。',['9月28日对节后原5分钟中枢的条件分析'],['特别大的消息可能改变线段类上涨的预期'])

c(84,'explicit-self-structure-rename','199-b009','作者明确说明前文用“自相似性结构”不够精确，易与数学分形术语混淆，以后统一称“自同构性结构”。','自相似性|自同构性结构|分形',1,'只记录作者对自身术语的明确改称，不把所有数学自相似性与自同构概念无条件并为同义词；旧引文不改。')
c(84,'three-viewpoint-supports','200-b004 200-b005','作者列走势不可重复、自同构性结构绝对复制、理论纯逻辑推导为三个支点：对应不能绝对预测、仍可判断操作以及其自称结论有效。','自同构性结构|走势预测|技术分析',3,'绝对复制与有效性为作者理论主张，不认证外部数学证明或实盘成绩。')
c(84,'uniqueness-proof-author-claim','200-b006','作者自称其理论以100%理论推导证明走势分解唯一，并指向此前笔、线段唯一性证明。','走势分解|笔|线段',3,'仅核作者陈述；77课证明分支重叠等已知疑点不因此被自动解除。',ambiguity='formal_proof_not_reproduced')
c(84,'fractal-complete-k-classification','200-b003 201-b008','作者把分型界定为K线组合完全分类所给结构，区别于其所批评的经验归纳或数学分形用法。','分型|K线|完全分类|分形',1,'记录作者定义体系和区别，不替作者认证其对所有外部理论的优劣评价。')
c(84,'fractal-only-recursion-start-optional','201-b009','分型只是中枢及走势级别递归定义的起始程序，并非不可替代；可用收盘价或成交量设计其他入口，前提是保证分解唯一性。','分型|递归定义|走势中枢|成交量',1,'可替换不等于可任意删条件；保证唯一性是作者明确前提，未给替代程序完整算法。',['替代递归入口仍能保证分解唯一性'])
c(84,'two-recursion-functions','201-b010 202-b000','作者把递归分为f1(a0)=a1的起始部分及f2(an)=an+1的后续部分，说明f1与f2可以完全不同，f1之前不需再递归。','递归定义|最低级别|走势中枢',1,'公式按归一原文排字保留，结合上下层对象语境理解，不能直接转换成数值加一的计算程序。')
c(84,'later-recursion-rule-unchanged','201-b009 201-b010 202-b000','作者称中枢后续递归过程规则一直未改，起始入口可另设而不改变递归性；入口替代仍须前述分解唯一性。','递归定义|走势中枢|分型',1,'不能以此声称任何不满足唯一性的f1都能生成有效知识结构；也不说中枢正式定义后来被推翻。',['替代入口保证分解唯一性','后续中枢递归规则保持'])
c(84,'base-and-higher-use-different-rules','202-b001','可用分型、线段构造最低级别中枢和走势类型即a1，其上级别再用另一套f2规则，不必把基底函数与后续函数设成一样。','分型|线段|最低级别|递归定义|走势类型',1,'最低基底与更高级别区分，不把每层都重新数笔分段。')
c(84,'decomposition-before-macd','202-b002','MACD用于辅助判断，关键是走势分解；不能只用MACD而跳过走势结构。','MACD|走势分解|技术分析',2,'辅助并不等于无用，亦不把柱面积小单独当背驰成立的充分条件。')
c(84,'level-not-time-classification','202-b003','级别是按作者规则自生长的结构分类，本质上不是时间结构或K线周期；最低级别不到的走势可以很久不长成更高级别，作者举100年说明。','级别|周期K线图|走势类型',1,'100年是说明不受时长保证的极端例，不是数据回测时限。')
c(84,'no-absolute-time-guarantee','202-b003','作者明确说级别不对任何时间结构作绝对承诺，结构被破坏是因满足破坏条件，而非单因时间经过。','级别|走势类型',1,'与82课日顶区间时间例并列保存，不按日期先后自动取消早句。')
c(84,'present-is-first-step','202-b004','作者反复说当下是针对预测执念的手段，能当下只是第一步，并不把当下本身奉为最终目的。','当下|走势预测|操作策略',3,'哲理语境，不补新交易信号或把不预测改成忽视已知条件。')
c(84,'oct8-139-not-confirmed','203-b001','10月8日收盘139起线段尚未确认结束，作者列次日开盘跌破5685才可标140，随后一般在附近形成1分钟中枢。','线段|确认|走势中枢',2,'后期图已有140/141不能倒填10月8日已确认；未来跌破条件必须保留。',['2007年10月8日收盘状态','次日开盘跌破5685时才确认相应标记'],figs=((203,1),))
c(84,'oct8-4335-medium-center-condition','203-b004 203-b005','作者当时认为回跌不破4335仍保持中枢中线上移，并以12月距2005年6月30个月提示10月起时间压力及政策共振风险。','走势中枢|中枢上移|政策风险|走势预测',4,'4335和30个月为历史宏观条件，时间压力不改为走势级别由月份决定。',['2007年10月8日当轮中线上移判断'],figs=((204,1),))
c(84,'announced-medium-bear-not-long-bull-reversal','204-b005 204-b006 205-b005 205-b006','作者10月8日晚宣布选择性中期做空、终结3600起持有程序，同时说长期牛市看法未改，可能判断错误且只是自己的操作态度。','操作策略|宏观市场判断|走势预测',4,'中期策略、长线观点和可能错分开；未验证实际下单，不当作给读者的交易指令。',['2007年10月8日晚作者自述'])
c(84,'three-force-resonance-not-controllable-policy','205-b011 205-b012 206-b000 206-b001','作者说分力引导合力需要技术、资金、政策调配及时间，政策不由个人控制；底顶须形成相应形态并突破或跌破，不是一天按意愿完成。','市场分力|市场合力|政策风险|同步共振',3,'三球类比不是精确时点公式；作者自己的活动也须遵循其理论。',['2007年10月9日作者对中期博弈的说明'])
c(84,'retail-final-force-and-capacity','206-b002 206-b003 206-b004','作者要求散户看最终合力决定进出，不必跟随作者态度；有能力等较大卖点，能力或心态不足则分批退出或降到可承受仓位；其自己未引出卖点也可能被夹空。','散户|市场合力|市场分力|仓位|操作熟练程度',2,'可能失败分支保留，不把作者大资金自述无风险当客观事实。',['2007年10月9日散户与作者分力操作的区分'])
c(84,'oct10-oscillation-region-not-center','208-b006','10月10日回落触及140—143的1分钟中枢震荡区域而未触中枢区间；作者称若次日下段不再延续，可成类第三买点再上，政策配合则可继续下杀使中枢扩展。','中枢震荡|走势中枢|类买卖点|中枢扩展',2,'类第三买点不能改成正式同级三买；震荡区域与核心中枢区间不能混同，下段尚未完结。',['2007年10月10日140—143案例'],figs=((209,1),))
c(84,'repost-introduction-only-author','209-b004','作者说明转贴一篇回应其港股直通车文章类似观点的外部文章，并赞同增加蓝筹流通量的方向可能成为政策。','公开信息|流通量|主力资金',4,'只有转贴引言是作者发言；后续访谈中GDP、A/H七倍及法律比例不能一并归作者。',['2007年10月10日转贴引言'])
c(84,'oct11-next-center-not-ended-leg','212-b010','10月11日作者称144—147的1分钟中枢已经形成，但148线段仍未结束，并以交替原则解释当日14点跳水判断。','走势中枢|线段|完成',4,'中枢已形成与离开段未完分别记录；交替有效性只是作者当时判断。',['2007年10月11日144至148案例'],figs=((213,1),))
c(84,'futures-maturity-float-stance','213-b002 213-b004 213-b005 214-b000 214-b001 214-b002','作者2007年主张现货成熟度及超级蓝筹流通比例不足时应缓推股指期货，认为低流通比例会放大操纵与逼空风险，并以神华6.33%、建行2.7%为当时例子。','指数期货|流通量|主力资金|市场风险',4,'现货制度与比例只属当时文章；《证券法》10%是作者历史引述，未作现行法律核验或当前金融建议。',['2007年10月12日股指期货推出前的作者主张'])
c(84,'derivatives-own-risk-not-all-hedging-ban','214-b005','作者在期货缓推文章中要求考虑高杠杆衍生品自身风险，暂不论是否降低现货风险，仍须防范期货的参与及监管风险。','指数期货|对冲|市场风险',3,'不能从这篇批评推出作者禁止所有对冲；与80课大资金对冲自述语境分开。',['2007年10月12日缓推股指期货文章'])
c(84,'oct18-top-not-confirmed','218-b010 219-b001','作者10月18日说即使已到其所喜的6124.04，顶部图形仍没走完、更未破位；若政策不配合仍可能反复或再上冲。','确认|完成|政策风险|走势预测',4,'与作者自称完胜并列保留未确认条件，不从后期图或标题宣布当时顶部已经确认。',['2007年10月18日收盘对当轮顶部判断'])
c(84,'oct22-5600-adjustment-confirmation','221-b001','作者描述6124.04起1分钟下跌在中枢下移中延续，收在3600起上升通道下轨附近；若这个通道下轨、5600缺口附近区域有效跌破，则确认针对3600起上涨的调整。','中枢下移|缺口|确认|调整',4,'“这个地方”保留在原文指代上下文，不把两种区域表述补成两个固定阈值的机械合取，也不把5600作所有行情确认线；图峰值差异另列。',['2007年10月22日当前上升通道下轨及5600附近区域'],figs=((220,1),),ambiguity='case_reference_region')
c(84,'oct22-divergence-bounce-capacity','221-b002 221-b006','作者要求有技术者观察6124.04起1分钟下跌的底背驰再考虑反弹，能力不足不参与；下跌结束后极可能箱形震荡并等政策选择突破。','背驰|反弹|操作熟练程度|走势预测',3,'底背驰出现为观察前提，极可能箱形不是已成箱形或保证反弹收益。',['2007年10月22日该次1分钟下跌'])

# Cross-course links reference existing IDs without rewriting their evidence.
keep('192-b003','lower-l079-c-stage-fractal-small-points-one-way','79课分型与小级别一二点非双向等价保留；82课是在其后看新中枢第三类点。')
keep('196-b009','lower-l077-c-stage-complete-segment-three-odd lower-l080-c-stage-feature-sequence-three-elements-general','线段至少三笔及三个元素才可能有分型已有严格表述；本段心理数量措辞不能替代它们。')
keep('200-b006','lower-l077-c-stage-stroke-uniqueness-author-assertion lower-l077-c-stage-segment-uniqueness-asserted','84课再称唯一性证明，不自动解除77课原字分支及形式证明待核。')
keep('201-b010 202-b001','lower-l064-strokes-segments-only-base lower-l063-base-chart-recursion','最低基底与其上递归既有来源保留，84课补明确的f1/f2分层。')
keep('202-b002','upper-l024-c-stage-center-replaces-kiss-macd-auxiliary','MACD辅助与结构核心已有来源，此课明确以分解为关键，新增限定不覆盖旧文。')

issue('non-inclusion-wording','191-b000','原页正文确为非包含关系处理后的顶分型，不能静默删非；与前段无包含及阴吞阳情景的精确参照仍需核对。','保留原字、联合条件和歧义；后续有明确勘误才建立修订。',True)
issue('time-level-context','192-b000 202-b003','82课日顶例称30分钟因时间不够不可能，84课又强调级别不对任何时间结构作绝对承诺；两者参照和适用范围不能自动用日期覆盖。','同时展示日顶例和一般级别声明；核对是否具体结构限制，不造固定时间级别换算。',True)
issue('three-feature-fractals-phrase','196-b009','心理解释写三个K线决定笔转折、三个特征序列分型决定线段破坏；与严格笔条件及三个元素构一分型的表述不能直接等同。','仅保留心理说明与原句待核，不新增必须三套特征序列分型的算法规则。',True)
issue('probability-and-psychology','190-b002 190-b003 192-b000 192-b001 197-b003 217-b010','绝大多数、几乎100%、100%及20%属于作者经验、理论断言或预测，没有本项目样本或账户验证。','保持语气、条件及时间，不作开发评测胜率或真实收益统计。')
issue('fractal-and-replace-entry-uniqueness','201-b009 201-b010 202-b000','作者允许收盘价或成交量替代递归起始，但只给保证分解唯一性的要求，未给这些替代入口完整定义和证明。','可查到允许替代的原话，但不能据此自行部署替代识别算法或宣称已证明。',True)
issue('repost-original-author','209-b005 212-b003','转载标题为华生访谈、末署华生/第一财经日报；记者叙述和华生引语混排，原文具体撰写者未独立核实。','39段保留unknown及转载身份，禁止作为缠中说禅直接证据；作者转贴引言独立保留。')
issue('figure-makers-late-and-price','191-b001 203-b001 203-b004 221-b001','13图已查看，四图后期行情；220图6123.64与作者正文6124.04不同，水印图制作人亦未核。','保留图源状态与数值差异，不从后期标号倒填未确认段或静默改价格。')
issue('effective-break-not-parameterized','191-b001 192-b001 221-b001','有效突破/跌破在本批没有统一的百分比、tick、根数或收盘时点算法。','保留有效与小级别确认条件，不引入EPS或自动阈值。')

note('189-b001','psychological_context','走势映现贪嗔痴疑慢与自相似结构比喻。','84课明确改称自同构结构另抽；不认证心理可由价格唯一反演。')
note('192-b002','learning_reminder','识别中继分型有助操作的提示。','具体确认与回补规则已分别抽取，不另造指标。')
note('192-b007 192-b009 193-b000 193-b002 193-b004 194-b000 194-b001 194-b002 194-b003','historical_and_rhetorical_context','月亮/潮汐类比、作者预测自评、两股潜在基本面、000999/水井坊博弈及持仓故事。','保留历史文章，不认证天文因果、公司资料、实际成交或未来回报；不得把潜在变化作已公布事实。')
note('195-b010','historical_stock_answer','600636年线支撑问题，作者要求看形态而不凭支撑猜测，并给中长线好股的当时立场。','未核公司基本面，不给当前估值判断；不把年线一定支撑作为作者答复。')
note('196-b000 196-b001 196-b004','reader-performance-and-selection','作者给夜雨大红花、谈心态，并反对预测板块独善其身，主张只看有买点股票。','读者十倍投入及交易故事仍为reader，不因获赞变成作者实际收益或普遍绩效。')
note('196-b009','withheld_quantity_shorthand','心理比较中的三个K线和三个特征序列分型原句已读。','严格笔成形与特征分型元素数量已有旧命题，本段数量歧义不作新的算法要求。')
note('197-b005','rhetorical_context','同阵营背叛与熟悉面孔的比喻。','骨牌/多杀多说明已抽，不将拟人比喻作独立市场定律。')
note('197-b008 197-b009 197-b010 197-b011 198-b000 198-b002 198-b003 199-b000 199-b002 199-b003 199-b004 199-b005 199-b006 199-b007','historical_policy_context','9月27/28资金政策、蓝筹、圆顶、3/4比例线、国有股划转社保预期、5周线及放假公告。','政策是当时猜测/建议，非已出台或现行法律；操作案例单列，不用事后行情认证自评正确率。')
note('199-b010 199-b011 200-b000 200-b001 200-b002 200-b007 200-b008 201-b000 201-b001 201-b002 201-b003 201-b004 201-b005 201-b006 201-b007','theoretical_stance_and_philosophy','作者对理论涵盖性、欧几里德/波浪、社会马克思/资本主义、零向量及修炼的比较与哲理。','作为作者立场和比喻保留，不认证人类首次、外部理论必有缺陷或社会结局的数学证明。')
note('202-b005 202-b006','learning_assignment','建议对照混沌操作法/证券新时空、寻找行为模式缺点的作业。','本课未给书内逐条比较结果；不代作者编造外部书理论缺陷。')
note('202-b008 203-b000 203-b002 203-b003 203-b006 203-b007 204-b000 204-b001 204-b002','historical_session_context','10月8日行情自评、政策危险期、回跌空间1000点与反追高、节奏评论。','不把时间压力或政策预言当结构级别定义；未确认139段及4335情景另抽。')
note('204-b004 204-b007 204-b008 205-b000 205-b001 205-b002 205-b003 205-b004 205-b007 205-b008 205-b009','historical_strategy_reasons','中期做空自述的政策、资金、技术、空间理由与3100/6100/3/4、反复折腾叙述。','不认证资金实际影响力或具体下单；借上涨消耗多头是作者比喻叙事，不制成执行操纵指令。')
note('206-b005 206-b006 206-b008 206-b009 206-b010 206-b011 207-b000 207-b001 207-b002','historical_session_context','作者展示分力合力意图，板块轮动耗能、政策决定及大资金自称无风险/低价革命备用。','无风险不成为客观事实；自述失败分支已抽，具体市场状态限当时。')
note('207-b004 207-b005 207-b006 207-b007 207-b008 207-b009 208-b000 208-b001 208-b002 208-b003','off_topic_economic_essay','房地产泡沫、美国日本历史、融资圈地循环、信贷治理、居住权与双轨制建议已完整读。','作者2007年经济立场及政策主张非缠论结构判据；未外部核实当时经济史、宪法解释或现行政策，不发布通用法律经济定理。')
note('208-b005 208-b007 208-b008 209-b000 209-b001 209-b002','historical_session_context','吸精大法、轮动与政策共振、没技术降仓以及不贴图的叙述。','策略是作者自述及修辞，技术上的类三买联合条件已单列。')
note('212-b006 212-b007 212-b008 212-b009 212-b011 213-b000','historical_session_context','10月11日中字头/题材股切换、跳水自评、周末利率与印花税假设。','未成148段与已成中枢分别抽；未实现消息不变成政策事实，无风险言辞不认证。')
note('213-b003 214-b003 214-b004 214-b006','historical_market_design','1995国债期货类比、沪深与创业板布局建议、成熟现货后期货和监管取舍。','具体市场设计是作者当时政策建议，不当已实施制度或当前监管结论。')
note('214-b008 214-b009 215-b000 215-b001 215-b003 215-b004 215-b005 215-b006 215-b007 215-b008 215-b010 215-b011 215-b012','historical_policy_and_session','10月13/15技术资金政策、自称空头主控、仓位能力提示、通胀治理及板块轮动。','原文时间条件保留，不核经济指标、作者真实仓位或干预归因；不把所有短线反弹都给散户建议。')
note('216-b000 216-b001 216-b002 216-b003 216-b004 216-b005 216-b006 216-b007 216-b008 216-b009 216-b010','historical_eight_positions','作者八项市场立场：二十年三万、牛市第一阶段、中期调整、共振、分力合力、低价革命备用及散户能力分层。','作为2007年重申的立场，不转成当前预测或已验证自然规律；分力合力及能力边界已有相关来源。')
note('216-b012 216-b013 216-b014 216-b015 217-b000 217-b001 217-b002 217-b003','historical_opinion','成老先生评论、投机反转风险、80%/20%及经济节奏类比。','匿名股及比例无数据口径，未核受评者身份观点，不制造普遍胜率或现行政策评判。')
note('217-b005 217-b006 217-b007 217-b008 217-b009 217-b010 218-b001 218-b002 218-b003 218-b004','historical_forecast_context','6100突破自评、糖业与000777潜在题材、指数期货延期、11月政策窗及牛市延长/全面泡沫情景。','自述与未来可能分开，未验证匿名内幕或20%保市值比例；政策窗口不作时间决定级别规则。')
note('218-b006 218-b007 218-b008 219-b000 219-b002 219-b003 219-b004 219-b005 219-b006','historical_session_context','6124后待5分钟中枢、只抬第一波、自述PE、5800/5600情景、印度政策及空头震荡策略。','未核外部政策和企业交易，不把散户不应抢无技术反弹的提醒变成一般价格公式。')
note('219-b008 219-b009 219-b010 219-b011 219-b012 219-b013 220-b000 220-b001 220-b002 220-b003 220-b004 220-b005 220-b007 220-b008 220-b009 221-b000','rhetorical_and_historical_context','苹果、没种、北大等修辞，5800中枢、政策未配合继续上冲、期货及20%利润预言。','比喻对象未明不补人物；20%无统计证据，不认证任何人实际市场控制力。')
note('221-b003 221-b004 221-b005','historical_capability_and_policy','底背驰后短差自述、能力不足应调整仓位、政策敏感与国航自述。','未认证实际订单、6100收益或政策必利空；相应底背驰观察与能力条件已另抽。')

reprint=[p for p in passages.values() if p['role']=='unknown' and p['speaker']=='转载文（含华生访谈，原文作者未核）']
assert len(reprint)==39
for p in reprint:
    notes[p['id']]={'category':'third_party_reprint','reading':'已读华生访谈转载标题、记者叙述、引语或署名分隔；只作为转载上下文。',
      'inverse':'非缠中说禅直接发言；原作者未核，不把GDP150%、A/H七倍、10%法律引述等升级为作者原文或当前事实。'}

relations={
 'lower-l082-c-stage-fractal-not-fractal-theory':[('分型','分形','distinguishes')],
 'lower-l082-c-stage-third-sell-no-expansion-stroke':[('第三类卖点','中枢扩张','related')],
 'lower-l083-c-stage-stroke-center-possible-less-stable':[('最小级别中枢','线段','related')],
 'lower-l084-c-stage-explicit-self-structure-rename':[('自同构性结构','自相似性','related')],
 'lower-l084-c-stage-fractal-only-recursion-start-optional':[('分型','递归定义','related')],
 'lower-l084-c-stage-level-not-time-classification':[('周期K线图','级别','distinguishes')]
}
for r in rows:r['relations']=[{'source':s,'target':t,'type':kind} for s,t,kind in relations.get(r['id'],[])]

by_passage=defaultdict(list)
for r in rows:
    for e in r['evidence']:by_passage[e['passage_id']].append(r)
for item in pending:
    item['lesson_numbers']=sorted({int(passages[x]['unit_id'].split('-')[1]) for x in item['passage_ids']})
    if item['id'].endswith('figure-makers-late-and-price'):
        item['lesson_numbers']=[82,83,84];item['figure_ids']=[f['id'] for f in figures]
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
      'related_existing_claim_ids':retained_ids,'note':'作者分型/分形及改称分别记录；不合并数学同义，不混递归入口与后续规则；转载与作者隔离。'},'4_reverse_check':inverse}})
for f in figures:
    key=(f['pdf_page'],int(f['id'].rsplit('fig',1)[1]))
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=figure_notes[key],
      figure_source_review='四图后期及39段转载身份见stage-c-l082-l084-source-applied.json；全部绘者未核。',
      linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger)==341 and len({x['passage_id'] for x in ledger})==341
def dump(suffix,data):
    (OUT/f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x,ensure_ascii=False,separators=(',',':')) for x in data)+'\n',encoding='utf-8')
dump('reviewed.jsonl',rows);dump('coverage.jsonl',ledger);dump('pending.jsonl',pending);dump('figures.jsonl',figures)
summary={'stage':'C','schema_version':metadata['schema_version'],'graph_version':metadata['graph_version'],'lessons':[82,83,84],'document_id':DOC,'reviewer':REVIEWER,
 'passages_read':341,'claims':len(rows),'evidence':sum(len(r['evidence']) for r in rows),'importance_counts':dict(Counter(r['importance_level'] for r in rows)),
 'new_concepts':sorted({x for r in rows for x in r['concepts']}-set(concepts)),
 'whole_lesson_semantic_read_complete':True,'technical_extraction_complete':False,'four_round_review':True,'independent_review_claimed':False,
 'visual_pdf_pages':list(range(189,222)),'figure_objects_viewed':13,'figure_origin_counts':dict(Counter(f['origin_status'] for f in figures)),
 'pending':[x['id'] for x in pending],'third_party_reprint_passages_excluded':39,
 'source_passages_snapshot_sha256':SOURCE_SHA,'retained_source_links_in_ledger_only':True,'database_mode':'ro','formal_import':False,
 'acceptance':'341段四轮审读、33页及13图检查；39段转载隔离，关键联合条件及递归分层保留，增量待预检发布。'}
(OUT/f'{BASE}.summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
db.close();sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(summary,ensure_ascii=False))
