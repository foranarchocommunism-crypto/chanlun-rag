"""Materialize the manually read lower 75--77 batch; SQLite is read-only.

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
BASE='c_stage_l075_l077'
REVIEWER='Codex 主代理 / 阶段C下册75至77课同模型四轮复核'
SOURCE_SHA='906caadf57f45e046e039638579dbea8dfeb0113ae1e168c1fc8e39f76bde3de'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
db.row_factory=sqlite3.Row
metadata={r['key']:json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version']=='1.1.0'
assert hashlib.sha256((KB/'sources/volume_2.pdf').read_bytes()).hexdigest()=='5332cd1b60381c47ceb81358db6bbb47882efd074fc5c869dcc3002aaed1b5c0'
passages={r['id']:dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id BETWEEN 'lesson-075' AND 'lesson-077' ORDER BY pdf_page,block_index,id")}
assert len(passages)==234
assert hashlib.sha256(json.dumps(sorted(passages.values(),key=lambda p:p['id']),ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==SOURCE_SHA
old={r['id']:dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts={r['label']:dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical={label:r['label'] for r in concepts.values() for label in [r['label']]+json.loads(r['aliases'])}
figures=[dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 124 AND 141 ORDER BY pdf_page,id',(DOC,))]
assert len(figures)==10
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
 (124,1):'600008日线，08-20箭头与19.15—19.98灰框；横轴至2007年10月，光标8/23不代表整图日期',
 (124,2):'000998日线，图头2011/08/19与横轴2007年5至10月混用；不据此确定截图精确日期',
 (125,1):'000938日线及16.77—16.92灰框；2011图头与2007横轴混用，晚于8/30正文',
 (125,2):'000099日线；2011图头与2007横轴混用，晚于8/30正文',
 (126,1):'600578日线及15.43—15.50灰框；2011图头与2007横轴混用',
 (126,2):'000915日线；2011图头与2007横轴混用，不据后期走势验证作者当时预测',
 (134,1):'上证1分钟图58至83，62—71中枢、71—80离开、80—83回拉；不凭图补未明说端点时价',
 (135,1):'上证5分钟图与9/5嵌文，光标9/3而行情到9/5；未观察到晚于对应9/5文字的证据，仍未核制图人',
 (140,1):'标题77课文中81-82划分的图解，含79/80/81/82、a至f、走势A及组合箭头；示意图作者未知',
 (141,1):'80-81、走势A、82实图，两处蓝字新旧笔对照；新笔条件9/18才提出，属于后加标注，不当作9/5作者规则'
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
    pending.append({'id':'lower-l075-l077-c-stage-pending-'+slug,'status':'pending','passage_ids':[pid(s) for s in shorts.split()],
                    'description':description,'suggested_action':action,'blocks_full_semantic_extraction_completion':blocker,'reviewer':REVIEWER})

# Round 2 and 3: propositions manually selected after full sequential reading.
# Dream-talk passages remain source-bound accounts rather than trading recipes.
c(75,'force-psychology-scope','121-b002 121-b003','作者认为走势是市场合力的结果，分力背后是人的思想情感；一般散户对合力影响可忽略，仍应严格客观地只看合力最终结果。','市场合力|市场分力|市场心理|散户',3,'心理研究有益与一般散户的操作范围并列，不把作者大资金博弈叙述转作所有人的操作条件。',['一般散户语境'])
c(75,'stock-capital-technique-example','121-b005','作者仅就个股博弈举例：技巧高超者可能以对方十分之一资金折磨对手，技巧低劣者即使有十倍资金也可能失败。','主力资金|操作熟练程度|资金管理',4,'1/10与十倍是梦话中的说明，不作为获胜资金阈值或经过验证的倍率。',['第75课梦话','这里讨论个股而非复杂大盘集团博弈'])
c(75,'group-trust-time','121-b005 122-b000','作者区分个股资金技巧与复杂大盘集团博弈，后者涉及领袖人格魅力、集团信任与共同经历，通常须长期积累。','主力资金|市场心理',4,'跨页读完多年经历，不用单笔技巧代替集团条件。',['第75课梦话中的大盘集团博弈'])
c(75,'no-fixed-target-and-experience','122-b004 122-b005','作者梦话说选择博弈标的无一定原则：新手宜谨慎垃圾标的，老手在有资源组合能力和长期资金时可能利用重组等题材。','主力资金|题材股|资金管理',4,'不把叙述推广成垃圾股必有重组或适合普通散户。',['作者博弈叙述','老手的资源组合能力和长期资金条件'])
c(75,'old-opponent-long-battle','123-b004 123-b005','作者梦话把资金来路、期限和对手经验视为博弈弱点；面对有经验且资金可久持者须准备长期战斗，通常避开，但作者又自述常不遵守此一般原则。','主力资金|阻击|资金管理',4,'保留一般原则与自述例外；不将带攻击性的比喻重写为技术定理。',['第75课梦话'],['作者自述常不遵守一般避开原则'])
c(75,'kiss-examples-not-algorithm','123-b008 123-b009 123-b010','在2007年8月30日附文中，作者称二三线活跃，并用600635、000998、000938、000099、600578、000915及600008的8月20日作“吻”与拉起的历史例子。','均线|板块轮动|补涨',4,'代码和8/20限于当时；原文未列均线参数，不能从后加图反推精确吻算法。',['2007年8月30日当次行情'],figs=((124,1),(124,2),(125,1),(125,2),(126,1),(126,2)))
c(75,'rotation-phase-risk','124-b000','作者在8月30日把当时阶段概括为指数耷拉、二三线活跃，并回引8月13日判断：成分股行情延续伴随升幅大品种短震风险，业绩风险释放后题材股可活跃。','板块轮动|题材股|牛市阶段|市场风险',4,'阶段判断及业绩风险释放条件保留，不能变成所有牛市固定轮动顺序。',['2007年8月30日行情与8月13日回引'])
c(75,'rotation-not-absolutely-safe','126-b002 127-b001 127-b002','作者在当时政策风险背景下认为，把做多冲动引向二三线是较好的选择但并非绝对安全，并提醒不追高。','政策风险|板块轮动|追高|市场风险',3,'停发基金、直通车及6000亿为当时风险背景，不当成当前事实或轮动无风险证明。',['2007年8月30日附文'])
c(75,'equal-endpoint-inclusion','127-b006','相邻两根K线只要对应的一端相同即属于包含关系，两端都相同更属于包含；非包含关系不需考虑相等情形。','包含关系|K线|价格精度',1,'结合读者对应高低点问题，不解释成任意一根高点碰另一根低点也包含；与绝对精度答疑联读。',['相邻两根K线','相等指对应高点或对应低点'])
c(75,'one-minute-types-before-five-center','127-b009','应先辨别三个有重叠的1分钟走势类型，才能据此识别5分钟中枢，不能先从图面认定5分钟中枢再倒填三个1分钟走势类型。','走势中枢|走势类型|级别|次级别',1,'答复给识别逻辑顺序，不补未给的端点分解算法。',['本例为三个有重叠的1分钟走势类型形成5分钟中枢'])
c(75,'gap-not-change-structural-unit','127-b012','作者答期货跳空问题时说，缺口若在线段里仍是线段、在笔里仍是笔，不能仅因跳空就改变所在线段或笔的身份。','缺口|线段|笔',2,'原引文“不该变”保留，不据此免除笔、线段本身的定义条件。')
c(75,'unfinished-not-compare-completed','127-b015','比较三买后向上走势与离开中枢走势的盘整背驰时，不能拿尚未走完的段与已走完的段比较；作者要求复习区间套以避免这种误判。','盘整背驰|完成|区间套',2,'未走完是所问小回落后续涨的解释；不把中途柱面积小等同已确认背驰。',['所问三买后向上段与离开中枢向上段的比较'])
c(75,'absolute-and-measurement-equality','128-b006 128-b013','包含关系中的相等是绝对相等，须软件显示到最后一位小数都相同；作者另提后文有测量相等的语境，不能把两者混同。','包含关系|价格精度',1,'不引入EPS、四舍五入容差或相对误差，原文没有给测量相等的通用容差算法。')
c(75,'inequality-noninclusion-premise','128-b006 128-b013','第65课≥符号包含等于的数学含义，但对应叙述先要求非包含；该前提排除了绝对相等，因而不构成作者所说的矛盾。','包含关系|包含处理|价格精度',2,'不静默把原文≥改成>，不以宽松浮点比较替代绝对相等。',['第65课被引用的方向判定','相应两根K线非包含为前提'])
c(75,'one-price-limit-two-constructions','128-b007','全天未打开的一字涨停可视作跳空加合并后的一根K线；按作者最初入口只形成最小级别中枢，而从分型开始构造最小级别中枢的角度连分型都不构成，更谈不上笔。','涨停|包含处理|分型|笔|最小级别中枢|最低级别',1,'两种构造入口同时保留，不能改写成所有定义下一字涨停绝无最小中枢。',['开盘一字涨停且全天未打开','区分最初最低级别入口与分型构造入口'])
c(75,'large-small-capital-time-channel','129-b009 129-b010','作者区分大资金与小资金：把中短走势降低长线成本至零再长持，称为大资金基本唯一可行且效率最高的方法；小资金不必照搬，有时间、通道和技术才可更多作短线。','资金管理|主力资金|交易通道|成本|长期投资',3,'唯一和效率最高是作者方法评价，未经策略比较实测；三个小资金条件不可只保留资金少，不给固定短线频率。',['第75课8月31日附文的资金规模比较','小资金作短线还须时间、通道和技术'])
c(75,'zero-cost-capital-meaning','129-b011 130-b002','作者把长期持股成本降至零解释为不占用资金，大级别回调时再作差价增加筹码。','成本|长期投资|资金管理',3,'零成本是作者资金占用口径，不等于资产价格无回撤、无交易成本或无市场风险。',['作者中长线持仓与短差策略','已通过短差降低成本的持仓'])
c(75,'policy-short-and-long-horizon','130-b008 130-b009 130-b010','在2007年9月3日宏观附文中，作者当时认为政策戳泡沫会有短期影响而未改中长期方向，并称持有20年的股票也要以中短操作管理成本、参与泡沫须提高技术和心态。','政策风险|宏观市场判断|长期投资|操作熟练程度',4,'这是当时判断及作者自述策略，未验证预测实现，不得推广成任何政策永不改变长期方向。',['2007年9月3日当时语境'])
c(75,'three-stock-resistance-classes','131-b011 131-b012 131-b013 131-b014','作者以600636未站稳半年线、600737突破“530”后首个反弹高位再回调、000938突破“530”高位后震荡，示范当时三类补涨结构；各自关键位须站稳才谈后续空间。','补涨|有效跌破|操作策略',4,'“530”是2007年5月30日行情语境，不把它误读为指数530点；原文排字仍保留，未新增精确阈值。',['2007年9月3日三个历史个股案例'])
c(75,'five-day-week-and-skill','131-b015 132-b000','作者对当时补涨行情说，无时间或不会技术者可看5日或5周线进出；会看中枢震荡者可在阻力位震荡中作短差。','均线|操作策略|中枢震荡|操作熟练程度',3,'5日/5周是均线观察周期，不能替换为走势级别；短差以能判断相应结构为条件。',['第75课当时补涨行情','作中枢震荡短差须具备相应技术'])
c(75,'policy-no-frequent-trades','132-b001','面对当时消息可能隔夜改变行情的环境，作者不建议技术未特别过关者频繁买卖。','政策风险|操作熟练程度|操作策略',3,'当时政策环境及能力条件保留，不将频繁交易本身设为必要。',['第75课2007年9月3日行情','技术未特别过关'])
c(75,'small-buy-not-become-long-buy','132-b002','长线介入应有长线买点，不能仅因在小级别买点买入后持有很久，就把它当成长线买点。','长期投资|买点|操作级别',2,'强调入场依据的级别，区别已建立长期持仓作短差与临时小买后被动转长线。')

c(76,'technique-only-one-aspect','132-b005 132-b007','作者称技术远非股票市场的全部；梦话假设技巧足够时可用5%流通筹码阻止持有50%者拉抬，借此说明博弈还涉及其他条件。','技术分析|流通量|主力资金|阻击',4,'5%/50%为作者假设而非经验证胜率或可直接执行的持仓阈值。',['第76课梦话','假设阻击者技术足够'])
c(76,'time-space-and-opponent','132-b008','作者梦话把对手受损分为时间与空间两方面，举过度洗盘而错过行情及偏执性格可被利用的经验。','主力资金|市场心理|阻击',4,'人物性格与洗盘是经验叙述，不构造可普遍判断的心理量化模型。')
c(76,'account-trick-historical-obsolete','132-b009','作者自述曾用显眼账户吸引对手、再换账户持仓至流通2%以下，并明确说后来因使用者多已无效。','主力资金|流通量|阻击',4,'保留作者说该方法已失效，不能作为当前有效算法。',['第76课历史自述'])
c(76,'holdings-vs-turnover-example','132-b010 133-b000 133-b001','作者梦话区分自身持有筹码与全市场成交换手：叙述流通10%以内持仓在宽幅交易中造成10%—20%换手，成交量也可由其他资金贡献，而非自己完成全部交易。','流通量|成交量|主力资金|成本',4,'持仓占流通量与成交换手不是同一变量；仅在所叙接近对手成本、筹码不丢的历史条件下说明。',['第76课梦话中的宽幅短差案例','接近对手成本且不丢所需筹码'])
c(76,'borrow-other-forces','133-b002','作者认为庄家只是市场的一种分力，博弈还可借其他力量，走势不由某一庄家单独决定。','主力资金|市场分力|市场合力',3,'复用合力框架但新增庄家在其中的限定，未把其他分力都归为作者资金。')
c(76,'time-funding-experience','133-b003 133-b005','作者梦话说耗资金期限的时间战会使图上形成复杂且级别越来越大的中枢；其“100至少99”失败比例是经验断言。','资金管理|走势中枢|级别|阻击',4,'比例无样本、分母与观察窗口，不能当项目实测概率或确定生存率。',['第76课时间战叙述'])
c(76,'space-timing-not-fixed-method','133-b005 133-b006 133-b007','作者梦话的空间战叙述依赖接回时机及筹码来自何方：太早、太晚均可能失败，并区分接散户恐慌筹码与接庄家抛盘；作者称判断须经验。','主力资金|散户|阻击|操作熟练程度',4,'保留叙述的条件与失败分支，未把借势砸盘、V形等修辞制成机械策略。',['第76课梦话中的空间战案例'])
c(76,'sep4-gap-two-branches','133-b009 134-b000','2007年9月4日作者把当次缺口不补视为强势，补后若无力拉回则短线严重，要求结合补缺后的实际走势判断。','缺口|市场风险|确认',4,'仅本次案例，不将“三天考验”扩成每个缺口三日内必补。',['2007年9月4日当次缺口'])
c(76,'62-83-center-third-buy-case','134-b005','在9月5日案例中，作者把62—71划为5分钟中枢，71—80为1分钟上涨离开，80—83为1分钟盘整回拉，并把83称为5分钟第三类买点，后续或更大震荡、或5分钟中枢上移。','走势中枢|第三类买点|次级别|中枢上移',4,'走势级别与图周期分开；保留两个后续分支，不从后加标线猜未写端点。',['2007年9月5日上证62—83案例'],figs=((134,1),(135,1)))
c(76,'sep6-conditional-center-paths','135-b000','对该次5分钟上涨，作者列最弱形成30分钟中枢、最强继续5分钟上涨；次日不新高，或虽新高但出现1分钟盘背且不能形成三买，都会形成当前新的5分钟中枢；若形成1分钟三买则继续寻找下一个5分钟中枢。','走势中枢|第三类买点|盘整背驰|级别',4,'“不新高”与“新高且盘背且不能三买”是或分支，不能改成三个条件必须同时发生。',['2007年9月5日对下一交易日的条件情景'])
c(76,'81-82-stroke-not-segment-break','136-b001','对81—82中间一笔创新高的问题，作者答复那只是一笔，笔破坏不等于线段破坏。','笔破坏|线段破坏|线段',2,'保存具体问答对象；既有第71课一般命题不因此自动得到本图端点证明。',['81—82历史划分问题'],figs=((134,1),))
c(76,'second-case-abc-not-confirmed','136-b004','下跌后ABC回拉若属第二种情况而未满足其定义，随后一笔直接创新低时原下跌仍未结束；若ABC回拉满足第一种情况，原下跌则已结束。','线段破坏|特征序列|完全分类',1,'保留同一ABC例子的两类不同前提；不是一见ABC外观就确认反向线段。',['第76课所举下跌—ABC回拉—再下跌例子'])
c(76,'classify-before-second-sequence','136-b005','第一、第二种情况是完全分类，应先区分类别再谈第二特征序列；第一种不需第二特征序列，第二种若找不到第二特征序列则原线段未破坏。','线段破坏|特征序列|完全分类',1,'不把第二特征序列条件施加到第一种，也不以其不存在证明任意线段不会破坏。')
c(76,'74-75-only-stroke-break-case','136-b011','对74—75附近8月31日10:55后下笔及填缺口的问题，作者只判断为笔破坏，没有线段破坏。','笔破坏|线段破坏',4,'作者未在此给完整标图推演；不能把读者列举条件当充分分段规则。',['第76课74—75具体答疑'])
c(76,'trend-before-high-amount','136-b014','在79—80应与哪段比较背驰的答疑中，作者强调关键看有无趋势，与创新高幅度多少无关。','趋势|背驰|盘整背驰|幅度',2,'答复没有明选77—78或75—76；不能代作者指定比较对。',['第76课79—80比较问题'])
c(76,'third-return-force-necessary','137-b001','第三类买卖点只有回拉力度小于离开力度才可能形成；回拉尚未出现不能预判，若回拉力度更大则不形成所说第三类买卖点。','第三类买卖点|当下|确认',2,'“才可能”是必要条件，不是小于即充分成立；还须相应级别和不回中枢等定义条件。',['回拉和离开走势按对应对象比较'])
c(76,'gap-strength-three-joint-branches','137-b004 137-b005','对当次向上缺口，作者列不补最强、补后强力拉回且继续新高次强、补后拉回无力且不能新高最弱，并让市场实际选择而不预言。','缺口|完全分类|当下',3,'拉回强弱和是否新高是联合描述；未出现的新高不能预先填成事实。',['2007年9月5日向上缺口案例'])
c(76,'daily-up-gap-fill-answer','137-b008','对于读者所问向上日线缺口跌回缺口前一日高点的补缺问题，作者答“对”，并以原无交易区间后来有交易解释补缺。','缺口|周期K线图',3,'只对应所问方向与完整上下文；第77课另明说全区间再次成交，不推广为任意单点有交易就全部回补。',['第76课读者向上日线缺口问题'])

c(77,'classification-before-prediction','137-b011','作者要求预测建立在严格分类基础上，缺口的定义与完全分类用于说明这一方法。','完全分类|走势预测|缺口',3,'保存作者方法论要求，不把分类本身当成预测正确率证明。')
c(77,'gap-definition-unit','137-b012','缺口是在选定单位K线图上，两相邻K线之间出现没有成交的价格区间。','缺口|K线|周期K线图|价格区间',1,'选定图单位、相邻和无成交区间均保留，不把任何视觉空白都算缺口。')
c(77,'gap-fill-entire-interval-no-deadline','137-b012','缺口回补是缺口出现后，该缺口区间最终全部再次出现成交的过程；可以下一根K线发生，也可能永远不再发生。','缺口|价格区间|K线',1,'全区间和发生于之后均保留；不能用三天、一半区间或触及任意点代替。')
c(77,'1994-gap-example-source-time','137-b012','作者以1994年7月29日与8月1日上证日线的[339,377]区间说明缺口，并在2007年9月5日表示它大概难有机会回补。','缺口|走势预测',4,'前半是作者历史实例，后半是当时预测；未验证截至今天是否回补，未认证其自述交易。',['第77课当时叙述'])
c(77,'gap-strength-three-types','137-b013 138-b000','按缺口是否回补及其后是否继续原方向极值，作者分不回补为强势、回补后继续新高或新低为平势、回补后不能新高新低而出现原走势转折为弱势。','缺口|完全分类|趋势转折',1,'跨页读完弱势分支；原方向向上用新高，向下用新低，不能把不创新高单独用于下跌。',['结合原走势方向判断极值'])
c(77,'breakaway-continuation-experience','138-b001','作者称突破性缺口极少回补，中继性缺口处于趋势延续，回补几率对半，但仍继续新高或新低，至少属平势。','缺口|趋势|走势延伸',3,'极少与对半是作者经验，未给样本和统计口径，不作为已验证50%模型。')
c(77,'exhaustion-higher-adjustment','138-b001 138-b002','作者将补缺后不再创原方向极值、趋势转折的衰竭性缺口与更大级别调整相联系：调整级别至少大于原趋势；例为日线趋势对应至少周线调整、5分钟趋势对应至少30分钟调整。','缺口|趋势转折|调整|级别|走势类型',1,'等级指走势类型，不由缺口所在K线周期决定；两组示例不等于所有级别的固定倍率表。',['原趋势中的衰竭性缺口','回补后不再创原方向极值并发生趋势转折'])
c(77,'period-not-trend-level','138-b002','不同周期K线图是观察走势的工具，走势类型的级别是被观察对象的属性；缺口后调整的级别不能直接按缺口所在K线图周期认定。','周期K线图|级别|走势类型|缺口',1,'显微镜比喻的对象关系保留，不能把日K上的缺口等同日线趋势衰竭缺口。')
c(77,'daily-gap-lower-period-asymmetry','138-b003','日K线有缺口时日线以下周期图也会相应有缺口，但回补日线缺口不一定回补日线以下周期图上的缺口。','缺口|周期K线图',2,'存在对应与回补非对称分开，不强行把不同周期缺口区间认作相同。',['同一市场数据的不同周期K线图'])
c(77,'ordinary-consolidation-gap','138-b003','作者把盘整走势中的缺口列为普通缺口，称通常回补、分析意义不大；在中枢震荡中可作回拉目标，几乎肯定至少回到补缺位置。','缺口|盘整|中枢震荡',3,'通常与几乎肯定是经验语气，不能改为所有普通缺口必补或确定时限。',['盘整走势中的普通缺口'])
c(77,'fractal-inclusion-and-no-shared-bars','138-b005 138-b006','无包含关系时三根K线可决定一个分型；作者要求相邻分型满足结合律，不能让K线分属不同分型，并建议按包含与结合律处理后先标全顶底。','分型|包含处理|K线|顶分型|底分型',1,'这里是第77课分型归属语境，不能无条件等同所有走势分解的结合律。',['第77课原笔标准的分型处理语境'])
c(77,'old-stroke-joint-conditions','138-b007','第77课笔须一顶一底；两分型之间至少有一根K线不属于顶底分型；顶分型最高K线区间至少有一部分高于底分型最低K线区间。','笔|顶分型|底分型|K线|分型',1,'三项须联用；这是9月5日原标准，与9月18日新标准分开，不凭后期蓝字图注覆盖。',['一顶分型与一底分型','按包含关系及分型归属处理','顶底之间至少一根独立K线','最高顶K线区间须部分高于最低底K线区间'])
c(77,'stroke-uniqueness-author-assertion','138-b008 138-b009 139-b000 139-b001 139-b002 139-b003','作者主张满足前述条件的笔划分唯一，并以第N笔首次分歧作反证；但汇编证明先写“前面的底高于后面的底”，后写“前面的底不低于后面的底”，两处分支原字重叠，尚未消除。','笔|分型|完成',1,'核对PDF139原页仍为不低于，不替换为不高于；作者结论的可检索性不表示项目已复演证明。',['满足第77课列出的笔与分型条件'],ambiguity='source_proof_branch_overlap')
c(77,'new-lower-bottom-unfinished','138-b009 139-b000','在第77课顶起始笔的唯一性讨论中，一个底之后未经顶分型又出现更低底，说明此前取底的笔尚未完成。','笔|底分型|顶分型|完成',2,'只抽原文独立明确的前一分支，不代为修复下一分支。',['顶起始的候选笔','先后两个底之间没有顶分型','后底更低'])
c(77,'stroke-step1-valid-fractals','139-b004 139-b005','第77课划笔步骤先确定所有符合标准的分型。','笔|分型|包含处理',2,'符合标准须回到前文包含处理与分型归属，不能标任意局部极值。',['第77课原笔条件'])
c(77,'stroke-step2-same-type-and-equality','139-b006','相邻同性质分型中，前顶低于后顶则弃前顶，前底高于后底则弃前底；不满足者如相等可先保留。','笔|顶分型|底分型|价格精度',1,'先保留不等于最终都成笔；不新增相等强制弃前或EPS规则。',['第77课三步划笔流程','前后相邻分型同性质'])
c(77,'stroke-step3-opposite-with-premises','138-b007 139-b007','完成同性质分型处理后，相邻顶底可划为笔，仍须满足本课前述独立K线和顶底区间的笔条件。','笔|分型|顶分型|底分型',1,'“相邻顶底”不能脱离整段前提，尤其不能把不满足独立K线的近邻分型视为旧标准笔。',['同性质分型处理已完成','满足前述第77课笔的全部条件'])
c(77,'stroke-step3-chain-first','139-b008','同性质分型链经前步处理后，前顶不低于后顶、前底不高于后底；遇到新的相反分型时，以链中最先一个与它连接成笔，中间同性质分型删除。','笔|顶分型|底分型|分型',2,'保留“经前步处理”与链首条件，不能不经处理总取任意同型链第一点。',['第77课三步流程第二步已完成','相反分型到来且满足笔条件'])
c(77,'stroke-steps-uniqueness-claim','139-b009','作者称按其三个步骤可以唯一划分所有笔。','笔|分型',3,'复核出处和步骤表述不等于已证明算法在所有输入上唯一；证明分支重叠另列待核。',['第77课三步骤与全部笔条件'],ambiguity='source_proof_branch_overlap')
c(77,'complete-segment-three-odd','139-b010','完整线段至少三笔，起止分型须异性质，不能顶至顶或底至底，故所含笔数为奇数。','线段|笔|分型',1,'完整线段的端点与笔数，未完成候选段不能仅因暂时偶数笔就自动强制截断。',['完整线段'])
c(77,'first-three-strokes-overlap','139-b011','线段开始的三笔必须有重合；开始三笔没有重合则不能构成线段。','线段|笔|重叠',1,'前三笔与重合联合保留，不改为任意三笔存在某处重叠。')
c(77,'first-case-no-overlap-no-completion','139-b012 139-b013','第一种情况中，先发生一笔破坏，接着一笔创新高，再后一笔完全不触及破坏那笔时，后三笔无重合、不能构成反向线段，也不能形成所需特征序列分型来确认原段完成。','线段破坏|笔破坏|线段|特征序列|重叠',1,'三笔先后条件不可漏；单次笔破坏不能替代反向段确认。',['第77课第一种情况所举向上原段例子','后续三笔不重合'])
c(77,'opposite-direction-destruction','139-b014','线段破坏须由相反性质线段完成；向上一笔起始的线段不能被同样向上一笔起始的线段破坏。','线段|线段破坏|笔',1,'性质指起始笔方向，不由整体视觉斜率或笔数自行替代。')
c(77,'second-case-abc-provisional','139-b015 140-b000','第二种情况可先按结合律假设命名A、B、C：A未按第一种情况被B破坏，而C破坏B后确认B完成，作者据此说明A也应完成；确认前这些名称只是括号内满足线段基本性质的假设称呼。','线段破坏|结合律|确认|线段',1,'不能把用于论证的A/B/C在破坏确认前全部当成已完成段。',['A/B/C括号内满足线段基本性质','破坏关系尚待或已经按相应条件确认'])
c(77,'second-sequence-simplification','140-b001 140-b003','第二种情况的第二特征序列对应C对B的破坏；作者在此不再把该判断重复分第一、第二种情况，以简化不断追溯再倒推的操作。','特征序列|线段破坏|递归',1,'这是作者给定的简化口径，不强加无限二次分类，也不取消第二序列的分型条件。',['第77课第二种情况的第二特征序列判断'])
c(77,'shrinking-chain-author-argument','140-b002 140-b003','作者论证一串连续第二种情况最终会出现回补特征序列缺口的第一种破坏，否则区间无限缩小成一点；据此可从后倒推破坏链。','特征序列缺口|线段破坏|递归',3,'仅记录作者极限论证；本课未给有限步界、最小价格单位或完整形式证明，项目未认证其数学完备性。',['作者假设的连续第二种情况线段串'],ambiguity='formal_proof_not_reproduced')
c(77,'second-case-purpose','140-b004','作者解释区分第二种情况是为避免在线段层次出现小级别转大级别式不确定。','线段|小级别转大级别|线段破坏',3,'这是作者设计目的，不外推为所有更高层走势都已消除不确定性。')
c(77,'80-81-first-break-and-a','140-b005','80—81出现第一笔破坏后，有符合线段标准但未创新低的走势A，此时既不能视为原段延续，也不能仅据它确认破坏，因为尚无满足要求的三笔。','笔破坏|线段破坏|线段|确认',2,'明确是该复杂案例的中间状态，不将符合基本标准A自动判已完成新段。',['2007年9月5日80—83案例'],figs=((140,1),(141,1)))
c(77,'80-81-one-stroke-rebound-branch','140-b005','若走势A后反弹仅一笔，则未破坏A，随后新低意味着A延续，A也成为原80—81的延续。','笔|线段|线段破坏|走势延伸',2,'假设反弹只有一笔的分支，与实际反弹成段分开。',['80—81案例的假设分支','反弹只有一笔且未破坏A','随后创新低'],figs=((140,1),))
c(77,'81-82-rebound-segment-actual-branch','140-b005 140-b006','在作者所述实际分支，反弹满足线段要求并破坏A，后面的走势不能继续算作A延续；第一笔破坏、A及该反弹合并成一个线段，形成81—82。','笔破坏|线段破坏|线段|结合律',2,'文字独立支持组合关系；图中后来新笔蓝字不作为本课作者原标准证据。',['80—83历史案例','反弹满足线段要求且已线段破坏A'],figs=((140,1),(141,1)))
c(77,'segment-uniqueness-asserted','140-b007','作者称从定义与两种情况可证明线段划分唯一，本课该句未展开完整证明。','线段|线段破坏|完全分类',3,'保留作者主张，不能把“容易证明”标作项目形式验证通过。',['按作者两种线段划分情况'],ambiguity='formal_proof_not_reproduced')
c(77,'telecom-plan-unconfirmed-context','141-b002','9月6日附文中，作者把联通G网、移动、大唐及CDMA安排称作尚未正式公告、方案未最终批准的可能组合，并解释此前相关梦话。','公开信息|宏观市场判断',4,'保留尚未公告和可能，不能凭后来的行业事实倒填当时已确认消息。',['2007年9月6日附文'])
c(77,'sep6-continuation-gap-case','141-b004','作者在9月6日把当次补缺后继续新高解释为中继性缺口及震荡后向上有利。','缺口|当下|走势预测',4,'这是当次已经补缺且新高后的判断，不等于任何补缺都强势。',['2007年9月6日当次缺口已回补并继续新高'])
c(77,'short-term-fatal-news-rule','142-b000 142-b006','作者在当时六项提醒中，把遇到其所谓致命消息先退出列为短线操作最关键一条，把消息技巧比较视为实用性判断。','政策风险|操作策略|市场风险',3,'主观风险原则与短线适用范围保留，不把“致命”补成固定机械新闻阈值。',['2007年9月6日短线语境'])
c(77,'strategic-holding-intermediate-sell','142-b004 142-b005','当时晚阶段不宜临时打长线算盘；已经为中长期战略持有者，则持有至中线卖点，并以部分仓位作降低成本、增加筹码的活动。','长期投资|卖点|仓位|成本',2,'区分新介入与既有战略持仓，不能把“不打长线算盘”写成无条件清仓长期持仓。',['2007年9月6日附文','已有中长期战略持仓与临时入场分别处理'])

# Explicit cross-course normalization links; old rows/evidence stay untouched.
keep('139-b011','lower-l065-segment-decomposition-theorem','第65课连续三笔重叠及线段破坏定理与本课开头三笔条件相联，新增本课直接证据，不替换旧定理。')
keep('136-b001 136-b011','lower-l071-c-stage-stroke-vs-segment-no-implication','笔破坏和线段破坏的非等同已有一般命题，本课保留具体问答作为单独案例。')
keep('138-b007','lower-l081-c-stage-new-stroke-two-joint-conditions lower-l081-c-stage-new-standard-optional-old-kept','本课原笔和后课新笔是不同条件；只关联两套明确原文，不能以时间后者自动覆盖前者。')
keep('128-b010','lower-l069-c-stage-second-sequence-three-elements','作者让重读第二种情况，未完整再答62—63三段端点；已复核第二序列规则只是相关线索。')
note('142-b002','repeated_method','5日/5周线的简便观察建议与本批75课相同，保留原文重复来源。','观察周期不等于走势级别；这里不再制造重复方法节点。')

issue('proof-bottom-branch-overlap','138-b008 138-b009 139-b000 139-b001 139-b002 139-b003','PDF139原页确为“前面的底不低于后面的底”，与上个“高于”分支重叠；未见其明确处理前底低于后底的独立分支。','保留原字与作者结论；后续有明确勘误才建立修订，不能自行改成不高于。',True)
issue('finite-chain-proof','140-b002 140-b003 140-b007','区间趋于一点的论证及线段唯一性主张未给形式化假设和有限步界；本批未复演完整证明。','返回作者论证并明确项目未形式验证，不把收敛本身当有限终止证明。',True)
issue('62-63-unexpanded-answer','128-b009 128-b010','读者问62—63为何不可分三段，作者只指向昨天及第二种情况，没有在本段重新给全套标号判别。','保留关联69/74课，后续逐图补取明确端点证据，不猜答复。',True)
issue('74-75-no-marked-proof','136-b010 136-b011','74—75填缺口问答只有“笔破坏，没有线段破坏”，未展开所缺的特征序列条件。','保留具体结论；在更多明确作者说明下再补图上完整推演。')
issue('79-80-comparison-pair-unanswered','136-b013 136-b014','作者说看有无趋势，没有直接指定与77—78还是75—76比较。','不代选比较对；查相应完整趋势结构和作者其他明确答复。')
issue('measurement-equality-unspecified','128-b006 128-b013','已明确包含要求软件最后小数绝对相同，但“后面的测量相等”没有在此给通用容差、精度或数值算法。','不补EPS、tick或相对误差；具体场景另核。')
issue('dream-talk-probability','121-b005 132-b007 133-b003 138-b001 138-b003','1/10与十倍、5%阻50%、100至少99、回补对半及几乎肯定属于假设或经验，未给统计样本。','保持作者语气与适用范围，不转化为实测策略参数或胜率。')
issue('figure-dates-and-makers','123-b010 134-b005 140-b005 140-b006','已检查10张当课图；六张混有后期行情/日期，第77课蓝字新旧笔晚于本课；制作人、示意图绘制者及截屏精确日期仍未核。','七图已登记later_annotation；不得以图内后加新笔字样修订77课原标准。')

# Context-only ledger covers all other author passages, not just claim hits.
note('121-b001 121-b004 123-b002 123-b006 132-b006','rhetorical_context','梦话前置提醒、修辞和段落收束已读。','不从自嘲、忍耐或人格比喻造技术定理。')
note('122-b001 122-b002 122-b003','historical_dream_context','庄家及玩庄家的历史描述、作者说自己不坐庄的理由和圈内经验。','法律、胜负及交友自述不当作当前法律结论或已证实市场事实。')
note('122-b006 122-b007 122-b008 123-b000 123-b001','anonymous_performance_context','四个匿名庄家股的缺口、跌幅与后续涨幅故事完整读过。','代码和日期未明，不跨课补股票身份；匿名收益未经订单或统计核实，不制作通用收益节点。')
note('123-b003','historical_self_report','000338、唐家、5月15日诗及100元的自述已读。','未核交易和诗歌外部记录，不以图像反推实际成交。')
note('123-b011 124-b001','transition_and_news_context','作者不再具体说吻及中报时段、快男的时事穿插。','没有新增可独立执行的定义，吻参数仍未给。')
note('125-b000 125-b001 126-b000 126-b001 127-b000','historical_policy_context','持仓二三线/中字头自述、政策宏观风险、指数五分钟震荡以及温柔刀的修辞。','存作当时背景，不认证作者仓位或当前政策；有关不安全与不追高已单列。')
note('128-b001','unconfirmed_policy_context','40%首付的传闻及作者对政策能否出台的怀疑。','保留“听说”和不确定，未核当前房地产政策，也非技术命题。')
note('129-b001 129-b002 129-b003 129-b004 129-b005 129-b006 129-b007 129-b008','historical_rotation_context','8月31日泡沫定性、政策情景、二三线轮动及持仓PE/VC的历史评论。','涨幅和政策预期未经外部核对；重复8月13日原话已有本批来源，不另重复造规律。')
note('130-b000 130-b001','historical_zero_cost_examples','000938百元与N年设想、000021七元起三季度降成本零的自述。','成本零策略另抽；未核这些账户、持仓和实际收益，未来价格不当事实。')
note('130-b004 130-b005 130-b006 130-b007','historical_forecast_context','9月3日泡沫附文的二十年三万点、GDP类比、可能两万及其后大跌的预测。','保留来源与情景，不给当前预测背书；其时间和强烈修辞不成为通用估值公式。')
note('130-b011 131-b000 131-b001 131-b002 131-b003','reported_earnings_context','十大增长公司标题及净利润、ST重组因素的历史列表。','未逐公司核半年报，作者报告性陈述作为上下文，非模型输入或当前财务事实。')
note('131-b005 131-b006 131-b007 131-b008 131-b009 131-b010 132-b003','historical_session_context','9月3日5330/4330、当日缺口、消息和轮动情绪及中铝自述。','未从自评认证预测正确；具体后三类结构已抽，不引入未证交易记录。')
note('133-b004 134-b001 134-b002 134-b004','historical_session_context','梦话未展开的资金链外部玩法、联通权重和会议、周一缺口三天考验。','不从未展开玩法制造规则；三天是当次叙述而非缺口统一期限。')
note('135-b001 135-b002','historical_valuation_forecast','建行、移动、中石油回归同类价格带动的当时比较与预测。','未核定价实现或当前公司估值，不把可达价格当已经发生。')
note('135-b003 135-b004 135-b005','risk_and_rhetorical_context','政策梦话、谨慎仓位、心理负担及跨过心理坎的提醒。','保存风险语境；一般提醒不新增准确交易触发条件。')
note('136-b008','historical_conditional_forecast','整体上市中字头可能200只百元股票的预测。','须满足作者说的上市条件且为可能，不当A股现状。')
note('137-b010 138-b004 140-b008','transition','回到技术、转入分型笔线段、邀请继续提问。','提示语不独立支持新定义。')
note('141-b001 141-b003 141-b005','historical_self_report_and_transition','建行比价、作者称公开说买入当天/此前已买、以及六项提醒的引言。','交易和消息非外部核验事实；不把作者自述提升为订单证据。')
note('142-b001','historical_news_preference','作者当时称无消息状态最好、消息可炒与是否顺势。','主观历史经验，没有足够对象与时限形成普适规则。')
note('142-b003','repeated_case_classification','重复75课三个股票的三种技术位置分类。','已有本批75课三类结构，不以重复文字另制造命题；原段保留。')

relations={
 'lower-l075-c-stage-equal-endpoint-inclusion':[('包含关系','价格精度','related')],
 'lower-l075-c-stage-unfinished-not-compare-completed':[('盘整背驰','完成','requires')],
 'lower-l076-c-stage-classify-before-second-sequence':[('线段破坏','特征序列','related')],
 'lower-l077-c-stage-period-not-trend-level':[('周期K线图','级别','distinguishes')],
 'lower-l077-c-stage-old-stroke-joint-conditions':[('笔','分型','requires')],
 'lower-l077-c-stage-first-three-strokes-overlap':[('线段','重叠','requires')],
 'lower-l077-c-stage-first-case-no-overlap-no-completion':[('笔破坏','线段破坏','distinguishes')]
}
for r in rows:r['relations']=[{'source':s,'target':t,'type':kind} for s,t,kind in relations.get(r['id'],[])]

by_passage=defaultdict(list)
for r in rows:
    for e in r['evidence']:by_passage[e['passage_id']].append(r)
for item in pending:
    item['lesson_numbers']=sorted({int(passages[x]['unit_id'].split('-')[1]) for x in item['passage_ids']})
    if item['id'].endswith('figure-dates-and-makers'):
        item['lesson_numbers']=[75,76,77];item['figure_ids']=[f['id'] for f in figures]
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
        result='reader_context';reading='已读提问、引述和署名，确定答复对象。';atomic=[];inverse='读者问句及引述不直接升级作者证据。'
    elif (p['role']=='unknown' and p['text'] in ('缠中说禅回复:','缠中说禅回复：')) or p['text'].startswith('教你炒股票') or re.fullmatch(r'(?:缠中说禅(?:解盘)?[:：]?)?\d{4}-\d{2}-\d{2}.*',p['text']) or re.fullmatch(r'.+\(2007-\d{2}-\d{2}\d{2}:\d{2}:\d{2}\)',p['text']) or set(p['text'])=={'*'}:
        result='source_header';reading='标题、时间署名或分隔符已核。';atomic=[];inverse='定位栏目而非实质技术命题。'
    else:raise AssertionError(('unaccounted paragraph',passage_id,p['text']))
    if linked and decision:reading+='；其余语境：'+decision['reading'];inverse+='；'+decision['inverse']
    ledger.append({'passage_id':passage_id,'lesson_number':int(p['unit_id'].split('-')[1]),'document_id':DOC,'pdf_page':p['pdf_page'],
      'role':p['role'],'speaker':p['speaker'],'published_at':p['published_at'],'source_text_sha256':hashlib.sha256(p['text'].encode()).hexdigest(),
      'result':result,'claim_ids':[r['id'] for r in linked],'related_existing_claim_ids':retained_ids,'existing_evidence_not_mutated':True,
      'pending_issue_ids':[x['id'] for x in pending if passage_id in x['passage_ids']],'reviewer':REVIEWER,
      'rounds':{'1_read_and_scope':reading,'2_atomic_conditions':atomic,'3_normalization':{'concept_labels':sorted({x for r in linked for x in r['concepts']}),
      'related_existing_claim_ids':retained_ids,'note':'相似语句不等于相同条件；旧新笔、测量绝对相等、完结未完结分别核对。'},'4_reverse_check':inverse}})
for f in figures:
    key=(f['pdf_page'],int(f['id'].rsplit('fig',1)[1]))
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=figure_notes[key],
      figure_source_review='七图后加登记见stage-c-l075-l077-figure-applied.json；制作人均未核。',
      linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger)==234 and len({x['passage_id'] for x in ledger})==234
def dump(suffix,data):
    (OUT/f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x,ensure_ascii=False,separators=(',',':')) for x in data)+'\n',encoding='utf-8')
dump('reviewed.jsonl',rows);dump('coverage.jsonl',ledger);dump('pending.jsonl',pending);dump('figures.jsonl',figures)
partial=[{'id':'lower-l067-equality-boundary-detail-partial-resolution-l075','status':'partially_resolved','resolves_pending_id':'lower-l067-equality-boundary-detail',
  'lesson_number':67,'source_lesson_number':75,'resolved_aspects':['对应一端相同为包含','对应两端相同为包含','相等须软件最后一位小数绝对相同'],
  'supporting_claim_ids':['lower-l075-c-stage-equal-endpoint-inclusion','lower-l075-c-stage-absolute-and-measurement-equality'],
  'remaining':['其他麻点走势逐段处理未全部展开；一字涨停只解决所述特例','测量相等未给通用容差算法'],
  'old_pending_record_preserved':True,'reviewer':REVIEWER}]
dump('partial-resolutions.jsonl',partial)
summary={'stage':'C','schema_version':metadata['schema_version'],'graph_version':metadata['graph_version'],'lessons':[75,76,77],'document_id':DOC,'reviewer':REVIEWER,
  'passages_read':234,'claims':len(rows),'evidence':sum(len(r['evidence']) for r in rows),'importance_counts':dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts':sorted({x for r in rows for x in r['concepts']}-set(concepts)),
  'whole_lesson_semantic_read_complete':True,'technical_extraction_complete':False,'four_round_review':True,'independent_review_claimed':False,
  'visual_pdf_pages':list(range(121,143)),'figure_objects_viewed':10,'neighboring_l074_figure_seen_but_excluded':f'{DOC}-p0121-fig1',
  'figure_origin_counts':dict(Counter(f['origin_status'] for f in figures)),'pending':[x['id'] for x in pending],'partial_resolutions':len(partial),
  'source_passages_snapshot_sha256':SOURCE_SHA,'retained_source_links_in_ledger_only':True,'database_mode':'ro','formal_import':False,
  'acceptance':'234段、22页及10张当课图审读完成；证明分支原字保留，新旧笔及后加图分开，技术抽取存在待核。'}
(OUT/f'{BASE}.summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
db.close();sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(summary,ensure_ascii=False))
