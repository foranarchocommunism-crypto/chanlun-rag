"""Materialize the manually read lower 97-98 batch; SQLite is read-only.

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
BASE='c_stage_l097_l098'
REVIEWER='Codex 主代理 / 阶段C下册97—98课同模型四轮复核'
SOURCE_SHA='966844a998550c149272c893ff8cf2f1feb97166e0a98b6e47d9d5872433a34f'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
db.row_factory=sqlite3.Row
metadata={r['key']:json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version']=='1.1.0'
assert hashlib.sha256((KB/'sources/volume_2.pdf').read_bytes()).hexdigest()=='5332cd1b60381c47ceb81358db6bbb47882efd074fc5c869dcc3002aaed1b5c0'
passages={r['id']:dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id BETWEEN 'lesson-097' AND 'lesson-098' ORDER BY pdf_page,block_index,id")}
assert len(passages)==179
assert hashlib.sha256(json.dumps(sorted(passages.values(),key=lambda p:p['id']),ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==SOURCE_SHA
old={r['id']:dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts={r['label']:dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical={label:r['label'] for r in concepts.values() for label in [r['label']]+json.loads(r['aliases'])}
figures=[dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 323 AND 338 ORDER BY pdf_page,id',(DOC,))]
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
 (326,1):'1/30嵌文但行情到2/1的4195.8，后期；4400中枢向5分钟扩展及三买前提依正文',
 (327,1):'1/31文旁图头2/29、光标2/1且行情到2月末，后期；4335/6124/4778/5522标记不是当时日中枢已完成的证明',
 (331,1):'2/4文旁图光标2/4却到3月3891.7，后期；加第二次碰年线不能反填首次年线判断已知未来',
 (332,1):'2/4嵌文但15分钟图行情到2/13，后期；两个5F图框不改正文5分钟三买未出，图周期不等于结构级别',
 (333,1):'2/4一分图编号356至364及4672.2，当日形态，制作人未核；361等为位置编号非点位价格，不从图补成背驰完整证明',
 (336,1):'2/14嵌文但日K延至4月2990.8与3277.1，后期；不把将来K线用作30分钟向上必盘整或日下跌当时已成的证据'
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
    pending.append({'id':'lower-l097-l098-c-stage-pending-'+slug,'status':'pending','passage_ids':[pid(s) for s in shorts.split()],
                    'description':description,'suggested_action':action,'blocks_full_semantic_extraction_completion':blocker,'reviewer':REVIEWER})




c(97,'reject-universal-predictive-indicator','323-b009 323-b010 323-b011 323-b012','作者批评寻找预测性、一劳永逸的万能指标或模式，尤其幻想自动给全部买卖而无需自己行动便持续获利的思维。','赌徒心理|技术分析|操作策略|走势预测',1,'批评的是万能且无须能力的获利幻想，不能据此证明任何辅助指标/计算都无效，也不删除91自动机器设想。')
c(97,'classification-foundation-not-application-skill','323-b014 323-b015 324-b000 324-b001','作者以中医为类比，称理论可逐一输出机会；掌握分类是基础，却不等于应用能力，实际效果随人的素质与修炼不同。','完全分类|操作熟练程度|操作策略',1,'仅作者操作教学类比，不核医学有效性或一一对应完备性；知道分类与成功执行不同。')
c(97,'observe-arrival-not-predict-time-price','324-b002 324-b003 324-b004 324-b005','作者以病人到来后望闻问切类比机会显现：不必预测其时间点位，应在出现时识别，通过多看走势图与实践改善判断。','当下|走势预测|操作熟练程度|走势分解',1,'不是医疗流程建议，识别练习也不等于已给精确算法或永不看错。')
c(97,'application-hard-and-person-dependent','324-b007 324-b008 324-b009 324-b011','作者将识别与操作分别类比诊断与开方、行军布阵，强调同一理论背景下仍须因人因时因地应用，操作是不断修炼的过程。','操作策略|操作熟练程度|完全分类',2,'诊断1/10开方9/10是作者修辞性比例，不是医学或交易难度统计；不发布对西医的贬评为事实。')
c(97,'invariant-background-author-claim','324-b010 324-b011','作者称市场各种不同之中有共同的不患基础，由其理论完全描述；个人在这一背景上形成不同操作记录。','完全分类|走势|操作策略',3,'不患为本段哲学性表述，不补作已证明的形式不变量或全市场完备性。')
c(97,'deviation-from-points-skilled-not-beginner','324-b012 325-b000 325-b001','一般须遵买卖点原则；作者自述有时为更多数量或更大目的在买卖点偏移处交易，并用格律诗说明初学者先严格守规则，熟练得心应手后才谈变通。','买卖点|操作熟练程度|操作策略|交易条件',1,'偏移是作者自身较熟练语境，不变成所有人可忽略买卖点；没给允许偏移幅度或实现细则。',['一般按买卖点原则','所述变通以熟练掌握规则为前提'],ambiguity='skilled_deviation_limit_unspecified')
c(97,'jan30-center-expand-await-third-buy','325-b012','1月30日作者称4400附近中枢震荡逐步向5分钟扩展，若无该中枢三买，向上冲动仍只能视为冲动。','走势中枢|中枢扩展|第三类买点|确认',1,'正在扩展与已经完成分开，无三买不被消息刺激或后期图替代。',['2008年1月30日4400附近该中枢'],figs=((326,1),))
c(97,'jan31-minute-center-cannot-break','326-b007','1月31日作者说该1分钟中枢突不上去则继续下台阶，并认为部分高位个股需要主动回落。','走势中枢|中枢下移|确认|指数走势背离',2,'限当时结构，突不上去未给统一时间阈值，不推广每次中枢震荡必跌。',['2008年1月31日该1分钟中枢'])
c(97,'jan31-technical-operation-over-rhetoric','327-b006','作者区分非技术评论与操作：可用语言影响分力，但不能遮蔽技术判断，操作仍按图形技术，尤其散户共同可见的是图形。','技术分析|市场分力|操作策略',2,'作者观点及所设散户条件，不认证评论影响市场的实际因果或唯一信息公平性。')
c(97,'jan31-1800-confluence-approximate','327-b007 327-b008','1月31日作者将4335到6124的差近似为1800，4778对应其3/4回落，并认为当前1800回落区与年线、5522起1200回落位置相近。','价格区间|价格精度|均线|走势预测',3,'基本/近似保留，不把差值精确相等或数字巧合当预测定理，不自动替换其他日期参照价。',['2008年1月31日该指数位置分析'],figs=((327,1),))
c(97,'jan31-daily-center-forming','328-b000','因触4335，作者称一个日线级别中枢正在形成，4335上下为其必然部分，是1000上来首个日中枢，预期影响至少很多个月。','走势中枢|级别|完成|价格区间',1,'原文形成中不能改为全部构件完成；下一段日中枢震荡已形成的不同用语并列，后98条件成日中枢关系待核。',['2008年1月31日从1000起该走势'],ambiguity='daily_center_forming_vs_oscillation_formed')
c(97,'jan31-large-oscillation-range-not-axis-3600','328-b001 328-b002','同文作者称大日中枢震荡已形成，以3600点为幅度基础上下可各1800，认为2500也可在震荡范围；当前中间位置会反复见到，直到中枢被破坏。','中枢震荡|价格区间|震荡中轴|中枢破坏',1,'3600是所述幅度尺度而非明说中轴价格3600；2500/6100为作者概略位置，不能算成精确边界或保证反复成交。',['2008年1月31日该中线震荡分析'],ambiguity='daily_center_forming_vs_oscillation_formed')
c(97,'jan31-grid-450-and-5228','328-b003','该中枢震荡可用450点、即3600的1/8为格，作者列4778首压力、5228第二压力，450还可细分用于短线。','中枢震荡|价格区间|价格精度|技术分析',2,'5228照录，不擅按1月10日5224或反弹5209合并；划格不是结构中枢上下边的完整推导。',['2008年1月31日所论中枢震荡格子'])
c(97,'jan31-daily-deviation-sublevels','328-b004 328-b005','在所论日中枢中，作者称最大偏移级别为30分钟，30分钟向下偏移为中短线机会，5分钟偏移为短线，超短者可看1分钟，需配合内部结构。','次级别|级别|中枢震荡|操作级别|走势分解',1,'是该日结构的层级说明，30/5/1非任意K周期固定换算，机会大小不等于各人可获利。',['2008年1月31日该日中枢及对应操作尺度'])
c(97,'jan31-holiday-deviation-joint-conditions','328-b007','作者把节前后向4778偏移的基础设为当前位置守住、震荡上5日线，且周一没有前两周式坏消息；否则须先砸空头陷阱。','完全分类|均线|空头陷阱|政策风险|中枢震荡',1,'守位、上5日线与消息联合，基础不等于保证完成偏移；不是预测春节必涨。',['2008年1月31日节前后该情景','当前位置坚守并震荡上5日线','周一无所述坏消息'])
c(97,'confidence-not-permanent-long','328-b008 328-b009','作者说其对市场的信心在于震荡操作，并非一定向上的死多头信心，同时区分对市场外经济事项的担忧。','中枢震荡|操作策略|市场心理',2,'自信和利润能力为自述，未独立证明熊市必能获利或对经济预测正确。')
c(97,'feb1-petro-explicit-revision-by-force','329-b010','作者明确说中石油原先30附近筑底上行的判断，因期货相关重要分力改变，改为至少24的酒席故事，并以此解释结论可修改。','市场合力|市场分力|走势预测|确认',2,'有明确修改原话才记录此关系；至少24为所述故事，不自动升级当时24酒话/14愿望为必达价，也不核实期货政策因果。',['2008年2月1日作者回述中石油判断改变'])
c(97,'feb1-long-outlook-retained-conditional','329-b011 330-b000','作者又自述有些未再提的结论无修改，例如20年大牛市、20年后至少3万点，仍附中国经济不自废武功条件。','走势预测|经济大势|市场合力',3,'此处对特定长期预测的保留有明确文字；不能把沉默本身写成全图谱自动有效规则，更不能认证20年收益结果。',['作者所述长期展望','中国经济不自废武功'])
c(97,'feb1-annual-cadence-and-5522-author-reading','329-b005 329-b006 329-b007','作者2月1日将4778至5522归为年度先小扬之支、小顶5522，重申其先小扬再抑大扬大抑展望，并认为后续第二波还待准备。','走势预测|完全分类|价格区间',3,'作者历史展望和事后解读，不等于全年路径已被项目验证；5462至5675为条件区间，不恢复必须先到5675误读。',['2008年2月1日回述年度展望'])
c(97,'feb1-strong-stocks-and-leading-types','330-b003 330-b004 330-b005','作者把强势题材补跌视作当时真正筑底前提，并称点燃行情需领头者，一般为新股/突发题材，或前次崩溃祸首与率先被压调整者；未见领头则仍构底。','补跌|次新股|题材股|市场合力|确认',2,'历史经验分类非已验证全市场必要充分定理；三类文字的分组保留，不补匿名股票名单。',['2008年2月1日所论探底与点燃情景'])
c(97,'feb1-leader-breadth-metaphor','330-b006','作者以全球、全国、全市、家中裸奔比喻领头力度和扩散范围，分别类比大、中、小及反弹行情，扩散展开、普遍习惯后高潮结束。','市场合力|市场分力|市场心理|走势预测',3,'仅行情传播力度比喻，不补量化广度阈值、地理交易规则或收益保证。')
c(97,'feb1-two-days-conditional-not-three','330-b007','作者否定节前必连涨三天，仅保留两天有希望，前提为周末无不利消息且中石油出来时不过分异常。','走势预测|完全分类|政策风险',2,'希望与双前提不删，不能改成承诺连涨两天，后续实际选择另记。',['2008年2月1日节前情景','周末无所述不利消息','中石油所述影响不过分异常'])
c(97,'feb4-360-label-not-mathematical-proof','330-b013 331-b000','作者把周五低点对应线段编号360与圆周作联系，并要求看15分钟图比较两段力度识别该次底背驰。','线段|背驰|周期K线图|价格精度',3,'360为编号不是价格，15分钟是观察图；未据编号/3600巧合证明数学因果或补出正文没指名的比较两段。',['2008年2月4日回看2月1日低点'],figs=((332,1),))
c(97,'feb4-divergence-return-independent-news','331-b001','作者说背驰成立只保证回原最后中枢，与周末有无利好无关，周五收盘前已达到，利好只是加强力度。','背驰|走势中枢|市场分力|确认',1,'该例返回与后续力度分开，不说消息与所有走势力度毫无关系，也不以周末新闻倒推背驰成立。',['2008年2月4日所论2月1日背驰及随后上涨'])
c(97,'feb4-rise-still-center-no-third-buy','331-b002','2月4日上涨尚未脱离最后中枢范围，4500上下5分钟中枢的三买未出，作者仍按该中枢震荡看待。','走势中枢|中枢震荡|第三类买点|确认',1,'涨幅大与完成三买不同，后期图不能替当日宣布已脱离。',['2008年2月4日4500附近该5分钟中枢'],figs=((332,1),))
c(97,'feb4-no-4778-two-five-centers-thirty','331-b007','若4778破不了，作者认为会把前面两个5分钟中枢构成30分钟震荡，仍沿用450一格参照。','中枢扩展|走势中枢|中枢震荡|价格区间',1,'限已有两个5分钟中枢及4778条件，不将任意两中枢一定升级或任意触价即确认。',['2008年2月4日所论两个5分钟中枢','4778不能突破'])
c(97,'feb4-avoid-chase-use-own-skill-top','332-b001','作者反对追高杀跌，技术不足者宁可坐电梯也不追砍；应在涨时观察大级别卖点，见日/周顶分型按自身水平处理。','追高|顶分型|操作熟练程度|操作策略|买卖点',1,'宁可坐电梯是避免更坏追砍的比较，不等于主动鼓励被套；未强迫所有人同一分型卖出。',['2008年2月4日所述年度操作背景'])

c(98,'divergence-return-then-classify','332-b007','作者说盘整背驰或真正背驰后，理论只能保证回拉原中枢；回拉后应将可能情况完全分类，再按各支后果定对策。','盘整背驰|背驰|走势中枢|完全分类',1,'回拉为所述保证边界，不代表只到必停或必立即反向；不删既有特定趋势背驰高一级结构结论。')
c(98,'feb1-close-two-next-segment-options','332-b008 333-b000','对周五背驰介入后的收盘，作者列继续突向中枢上边或再次回探两支：前者362起线段继续，后者须先破坏该段，等周一开盘当下判断。','线段|线段破坏|完全分类|确认',1,'362是图中位置编号，非价格；开盘前不预定利好或段破坏，跨页末句合读。',['2008年2月4日回述2月1日收盘后的该结构'],figs=((333,1),))
c(98,'feb4-news-not-operation-boundary','333-b001 333-b006','有无周一利好不改变按图形触及分类边界操作的逻辑；若利好仍破坏362起线段，作者认为更须警惕。','市场分力|边界条件|线段破坏|操作策略',1,'消息不替代图形边界，非主张消息不影响强弱；正文若与实际分支必须分开。',['2008年2月4日该线段及周末消息情景'])
c(98,'feb4-364-break-and-361-exception','333-b001','作者称实际到364才破坏该线段，此时演化成线段类上涨可能极大，除非363起线段跌破361位置；实际未跌破便继续持有。','线段|线段破坏|确认|持股|完全分类',1,'编号361/363/364不是指数价位，可能极大非完整上涨已确立；不把任一线段破坏都直接卖或都不卖。',['2008年2月4日所论编号结构'],exceptions=['363开始线段跌破361位置'],figs=((333,1),))
c(98,'feb4-next-class-divergence-await-slope','333-b002','364出来再展开新线段后，因已有第二线段类中枢，应注意类背驰；若次日不能保持相似斜率上涨，作者认为类上涨结束形成1分钟中枢合乎情理。','类中枢|类背驰|线段|走势中枢|确认',1,'类结构与严格1分钟中枢分层，关注/如果/合情理不能写成当时类背驰已成立；斜率没有统一数值。',['2008年2月4日编号364后的新线段','次日不能保持类似斜率上涨的条件支'])
c(98,'class-divergence-sell-depends-op-level','333-b003','一个线段类背驰是否卖些筹码，作者说取决于个人选择和操作级别。','类背驰|操作级别|操作策略',1,'结构发生与是否执行不同，不把任何微小类背驰强制成所有仓位退出点。')
c(98,'update-when-signal-exceeds-own-level','333-b004 333-b005','作者用战场、药效需当下观察作类比：可在上涨趋势持有，但一旦有超越自身级别和操作限度的转折信号即背驰，操作方案须改变。','背驰|操作级别|确认|操作策略',1,'医学/兵法只类比，不发布药效保证；所选级别/操作限度前提不可删成所有背驰一律清仓。',['转折信号超越自己的级别和操作限度'])
c(98,'preplan-all-branches-author-requirement','333-b007 334-b000 334-b001','作者要求操作前明白所有后续分类与对策，等待市场触发预设边界，并宣称其理论能给统一唯一完全分类。','完全分类|边界条件|操作策略|操作熟练程度',1,'作者完备性主张未独立证明；跨页句子与操作准备保留，不把预案完备当实盘无风险。')
c(98,'t1-retrace-risk-stronger-stock-proposal','334-b003','作者承认背驰买入后回探时受T+1限制可能无法卖出，提出选先于大盘、相对更强的股票以留反应空间。','交易规则|指数走势背离|市场风险|操作策略',1,'作者缓解方法非消除T+1风险或保证强股不跌，不作当前交易制度结论。',['所论T+1约束及背驰介入后可能回探'])
c(98,'slightly-leading-not-fully-inverse','334-b004','作者偏好稍先于大盘而非完全逆势的股票，因为后者可能补跌或逆大盘洗盘，举600737为例；先于大盘调整者亦属可选类型。','指数走势背离|补跌|操作策略|操作熟练程度',1,'稍先并非任意最强/完全逆势；可能不升所有逆势必补跌，选股还需能力。',['第98课所论相对大盘的选股方法'])
c(98,'new-stock-selection-conjunctive','334-b004 334-b005','新股作为另一选择，作者要求开得不太高、有明显新资金介入，并处在有一定级别的向上过程中；选股经验需反复练习。','次新股|资金入场批次|操作级别|操作熟练程度|操作策略',1,'三个条件及一般较稳的语气不能丢，未给不太高/明显的统一阈值，不当任意新股必稳。',['新股开得不太高','有明显新资金介入','处于有一定级别的向上过程'])
c(98,'feb5-class-divergence-to-minute-center','334-b009','2月5日作者称该线段类背驰后必然出现1分钟中枢，节后看其演化，中短线仍4500上下中枢震荡。','类背驰|走势中枢|中枢震荡|级别',1,'限具体线段类上涨情景，不把任何笔内类背驰都自动构1分钟中枢，未来需等演化。',['2008年2月5日所论线段类上涨及类背驰'])
c(98,'feb5-hedge-large-small-different','334-b010 334-b011','长假不确定性下作者以580989谈大资金对冲，却说小资金没必要参与这种高风险品种，也不一定对冲，可利用机动性先减部分留现金。','对冲|权证|资金管理|市场风险|仓位',1,'大资金对冲是作者案例观点，不是风险全消或任意权证适用；小资金不一定对冲不等于绝对禁止所有对冲。',['2008年2月5日长假不确定性及不同资金规模'])
c(98,'position-control-not-necessarily-empty','335-b001','作者说不确定时应控制仓位，但不一定空仓，而是降到特殊情况发生时仍有足够反应能力的水平。','仓位|市场风险|资金管理|操作熟练程度',1,'唯一正确为作者主张，不补固定仓位百分比；控制与空仓非同义。',['面临所述不确定或特殊情况'])
c(98,'feb13-warrant-return-boast-not-general-buy','335-b006 335-b009 335-b010','2月13日作者自述580989两次启动及很高收益机会，同时强烈声明一般人绝对不能买，没有相应本事与心态者只看教学演示。','权证|操作熟练程度|市场风险|追高',2,'单日50%/比30涨停是自述未核成交与基数，不能只取收益删参与限制或变为项目推荐。',['2008年2月13日580989教学案例'])
c(98,'feb13-oscillation-end-third-points','335-b013','对原最后中枢的扩展，作者说震荡结束的唯一标准是出现第三类买卖点。','中枢震荡|中枢扩展|第三类买卖点|确认',1,'限该中枢震荡结构，不能以开门红/涨幅或MACD替代三类点确认。',['2008年2月13日所论原最后中枢扩展'])
c(98,'feb13-petro-24-center-not-forecast-target','335-b014','作者2月13日将中石油24上下中枢如何突破与指数中枢突破联系，关注当日缺口回补及能否站稳。','走势中枢|缺口|确认|指数走势背离',2,'24此处是当时结构价格区，不同12月酒话或未来必达目标；影响关联为作者历史判断。',['2008年2月13日中石油24附近案例'])
c(98,'feb14-same-start-not-same-outcome','336-b002 336-b003 336-b004','作者以580989连续相似尾盘拉升警告，同样开始不保证同样结果，前N-1次重复也不能预定第N次，N本身会变化。','市场陷阱|赌徒心理|走势预测|操作策略',1,'历史骗局自述未外核，不把任何相似图形一定为骗局；反对无条件克隆结果。',['2008年2月14日580989相似形态教学'])
c(98,'feb14-macd-cross-two-trap-directions','336-b005','作者预期后三日MACD等金叉，提醒可能骗空也可能骗多，不能只预设一种方向。','MACD|金叉|多头陷阱|空头陷阱|完全分类',1,'金叉预期不等于确认涨势；三日是此案例窗口，不补指标参数或保证两方向必发生之一。',['2008年2月14日该指标窗口'],figs=((336,1),))
c(98,'feb14-next-thirty-up-direction-not-trend','336-b007','作者称6124起30分钟类型结束后的向上30分钟机会仍在中阴酝酿，但向上类型最坏可仅盘整，并不一定成为上涨类型。','中阴阶段|走势类型|盘整|上涨|级别|完全分类',1,'向上方向与上涨类型不同，酝酿不是当时已结束旧类型/完成新类型；后期日K不能定当时分支。',['2008年2月14日6124起该30分钟结构'],figs=((336,1),))
c(98,'feb14-consolidation-daily-first-center-risk','336-b007','若向上30分钟类型为盘整，作者说可在附近形成日中枢、作为6124起日类型首中枢，其后日下跌或日盘整都可能，三月前后因而关键。','盘整|走势中枢|下跌|级别|完全分类',1,'条件性日中枢与1/31形成中/震荡已形成的说法并列待核，不自动判同一对象已撤回或全部已完成。',['所论向上30分钟类型最终是盘整的条件支'],ambiguity='daily_center_cross_date_completion_scope')
c(98,'feb14-bench-capability-at-least-thirty','337-b001 337-b002 337-b003 337-b004','作者把操作者分为坐小板凳与可不断活动者；若假设前者至少做30分钟以上，则4778至5522属于30分钟以下活动，不要求其起身参与，应先认清能力。','操作级别|操作熟练程度|操作策略|级别',1,'30分钟是该人群假设，不是全体散户统一门槛，涨了也不取消能力/级别约束。',['作者假设小板凳者至少操作30分钟以上'])
c(98,'feb15-annual-support-head-shoulders-conditional','337-b006 337-b007','2月15日回试年线仅暂显支持，MACD柱能否有效转红仍待下周；三月前或仍震荡，若最终头肩底则有再跳水支，非该底形则不一定。','均线|MACD|确认|完全分类|市场风险',1,'暂显、待下周、底形条件不删，不把头肩底可能写成肯定再跳水。',['2008年2月15日年线与底形情景'])
c(98,'feb15-600795-risk-allocation-example','337-b008 337-b009','作者以600795说明布局：送股后的9元是估算，18元上介入大概风险10%—15%，小阴在构造小三买；按风险承受力定仓，并留资金对冲降成本。','第三类买点|仓位|对冲|成本|价格精度|操作策略',1,'除权估算不当现价9元，构造不等于确认；10%—15%非已证明最大亏损，不能推广全股固定风险或仓位。',['2008年2月15日600795教学例','按自身风险承受能力安排仓位并留资金'],ambiguity='small_third_buy_constructing_not_confirmed')
c(98,'feb15-600795-method-not-buy-instruction','337-b010 338-b000 338-b001','作者随即明确说教的是思维操作方法，不一定让人买600795，已经拉起后再买没意义。','操作策略|追高|操作熟练程度',1,'跨页声明必须随示例保留，不能只凭估算低风险或题材名单转成买入指令。',['2008年2月15日600795教学示例'])
c(98,'feb18-red-histogram-await-confirmation','338-b004 338-b005','2月18日MACD红柱出现并不代表一切无忧，仍需确认；若站不住当日位置，可能几根红后再绿，一般对应新一轮下跌。','MACD|确认|市场风险|概率原则',1,'可能/一般与价格条件不删，不能把红柱直接等同买点或确认反转。',['2008年2月18日所论MACD转红及当日位置'])
c(98,'feb18-weak-energy-exit-and-bottom-forms','338-b006 338-b007','若红柱后能量不能跟上，作者认为再绿及急转风险大，冲高无力应先退出观察；这类情况可对应头肩底，最好也可能双底。','MACD|操作策略|确认|市场风险',2,'能量/冲高无力无统一阈值，底形是可能对应不是必成，不能只凭红绿柱判完整底结构。',['2008年2月18日红柱后能量不足、冲高无力的条件支'])
c(98,'feb18-indicators-imprecise-center-primary','338-b008','作者称上述指标/底形分析不精确、按其理论意义不大；当天未构成线段类上涨，4575附近1分钟中枢已成，后续超短看其演化。','MACD|技术分析|走势中枢|线段|中枢震荡',1,'作者明确降低指标分析地位，不把早段红柱/头肩底当最终结构结论；未成类上涨与已成中枢分开。',['2008年2月18日该中枢震荡'])
c(98,'feb18-red-and-4575-joint-watch','338-b010','对当周多头，作者把维持MACD红柱与站稳4575之上列为联合技术要求，并将次日CPI看作考验。','MACD|确认|走势中枢|政策风险',2,'两项联合不是仅红柱即可，经济消息只是当时条件，未核现行CPI或以之保证走势。',['2008年2月18日对当周的判断','保持MACD红柱且站稳4575之上'])

keep('323-b010 324-b001 324-b004','lower-l096-c-stage-jan28-three-step-opportunity-recognition-operation','97用中医类比重述输出、观察、操作三层，不能只会理论就认证实盘能力。')
keep('325-b000 325-b001','lower-l091-c-stage-machine-profit-author-proposal','91自动机器设想和97反万能无须行动指标的语境并列，未有明确撤回，不自动删除前课。')
keep('329-b010','lower-l091-c-stage-petro-24-wine-not-price-guarantee lower-l091-c-stage-dec20-petro-bottom-constructed','97明确自述30筑底改24故事，既有酒话/愿望和30构中枢待三类点仍按原日语境保留。')
keep('329-b007','lower-l093-c-stage-jan18-not-must-reach-5675','5462至5675是过程中政策条件区间，不因第二波展望恢复先到5675的误读。')
keep('331-b001 332-b007','lower-l071-c-stage-trend-end-divergence-retrace lower-l089-c-stage-higher-must-five-center','回最后中枢是所述保证边界，不能删特定趋势背驰必成更高级中枢/1分钟下跌背驰后5分钟的前提结论。')
keep('333-b000 333-b001 333-b002','lower-l063-chart-period-not-center-level lower-l064-preconfirm-not-actual-confirm','图周期与结构级别不同，预计结束不等于已实际确认；361至364是编号，不是价格。')
keep('334-b003','lower-l094-c-stage-t1-same-day-exit-impossible-risk','98提出相对先行股缓解空间，不取消94小机会同日完成、T+1不能退出风险。')
keep('334-b010 335-b010','lower-l096-c-stage-jan28-put-entry-warning-and-exception','580989大资金对冲及收益自述不取消一般人不得买、能力和已持有例外限制。')
keep('338-b004 338-b008','lower-l096-c-stage-macd-assists-not-equals-divergence','红柱/金叉辅助不等于背驰或结构反转，作者同文称不精确分析。')

issue('metaphor-and-completeness','323-b013 323-b014 324-b007 324-b009 324-b010 325-b001 334-b001','中医/兵法/格律类比及诊断1/10开方9/10、不患和理论一一对应为作者教学说法；未证明医学事实或形式完备性。','按操作语境保存，不引类比代替结构证据，比例/万能指标/机器设想仍区别对待。')
issue('skilled-point-deviation-limit','324-b012 325-b000 325-b001','买卖点偏移为作者数量/目的自述，熟练与初学守格律有明确范围，但未给偏移容忍度、执行及风险算法。','保留一般守规则与熟练变通，不能当所有人任意偏离或为自动交易补参数。',True)
issue('daily-center-completion-cross-date','328-b000 328-b001 328-b004 336-b007','1/31日中枢形成中、日震荡已形成，与2/14向上30分钟若盘整再形成日中枢，具体对象及完成层次未完全说明。','分别按日期和条件并列，不把震荡已形成等同严格全部中枢完成，也不自动以后文撤回前文。',True)
issue('numerical-grid-and-360','327-b007 327-b008 328-b001 328-b002 328-b003 330-b013 331-b000','1800/3600/450及2500/6100概数，5228与先前5224/5209不同；360编号与3600联系未提供独立数学证明。','照录数字及概数，不EPS合并、不把3600当中轴价或用线段编号巧合证明预测。')
issue('petro-revision-and-silence','329-b010 329-b011 330-b000 335-b014','作者明确自述重要分力改变使30筑底改24酒席故事，也说未提即未修改；24后又为实际中枢区域。','只给有具体原话的修订线索，不能把酒话变必达目标或把沉默变全图谱自动有效规则；政策因果未核。')
issue('return-guarantee-and-news-scope','331-b001 332-b007 333-b001 333-b002 333-b005 333-b006','两种背驰回中枢后的分类与特定趋势背驰更高级中枢结论须共同保留；新闻不改操作边界不等于新闻不改力度，实时斜率/转折界限未量化。','保留趋势/盘整对象、级别及方向，只到中枢非必停；不自动输出具体时价或段确认。',True)
issue('t1-leading-stock-and-capacity','334-b003 334-b004 334-b005 335-b001 337-b002 337-b009','先于大盘稍强与完全逆势不同；新股不太高/明显资金、足够反应仓位、小板凳级别及600795风险估算没有统一阈值。','所有能力和人群假设保留，相对强股不消T+1风险，控仓不等空仓；不补统一固定仓位或损失上限。',True)
issue('indicator-status-vs-structure','336-b005 337-b006 337-b007 338-b004 338-b005 338-b006 338-b007 338-b008 338-b010','MACD金叉/红柱、头肩底双底只是条件辅助，作者明确说不精确；4575结构及确认标准仍须对应，未有通用参数。','不将红柱已现当反转确认，也不将看涨技术与消息面不满压成唯一方向，后续证据再接续。',True)
issue('figure-makers-and-late','325-b012 327-b008 330-b013 331-b001 332-b008 333-b001 336-b007','6图均查看，5图明显含文后行情，2/4编号图制作者未核；未来日K/15分钟框不能反填中枢完成和背驰/年线预测。','登记五后期、一未核，图意仅辅助正文，未核原博客图版。')

note('323-b013','analogy-introduction','作者将市场操作与中医、兵法、诗歌作相似性引入。','类比不是三个领域的独立事实证明，后续分类/观察/操作论述分别核对。')
note('324-b006 325-b002','learning-and-schedule-context','热爱走势图、贪念遮蔽与接电话暂停写作。','作者练习立场和日程，不作心理实验结论或自动股价判断方法。')
note('325-b004 325-b005 325-b006 325-b007 325-b008 325-b009 325-b010 325-b011 325-b013 325-b014 326-b000','historical-macro-and-warrant-context','减息/看脸色、题材股强势、年度扬抑节奏、石油转机、美国1987愿望、580989缩幅0.6及首次年线喜剧。','历史情境与自述未外核，不证明操盘影响、年度收益或消息方向；结构条件另抽。')
note('326-b002 326-b003 326-b004 326-b005 326-b006 326-b008 326-b009 327-b000 327-b001 327-b002 327-b003 327-b005','historical-policy-and-private-context','香港收壳来访、美国资产、经济管理人选意见、印花税最高及三月会/信心、读诗和晚饭日程。','不发布当前交易税率/人事/国际经济事实，不核匿名项目或作者经济预测。')
note('328-b006 328-b010 328-b011 328-b012 329-b001 329-b002 329-b003 329-b004 329-b008 329-b009','historical-economic-and-training-context','震荡赚不比去年少、经济长期忧虑、春节/奥运幻想、春晚传闻及美阿经济史论，93帖及陪练说明。','全部已读；未核年度收益/节目/历史因果，不将比喻视为经济专业事实，能力练习边界在命题。')
note('330-b001 330-b002 330-b008 330-b009 330-b011 330-b012 331-b003 331-b004 331-b005 331-b006 331-b008 332-b000 332-b002 332-b003 332-b004','historical-news-and-market-force-context','石油10亿与恐慌底、印花税/平安融资意见、利好/新基金喜剧自述、央行表态、股票阻力与资金/题材、跟帖收集罪证。','均是固定汇编历史发言，不执行征集/攻击或发布指控事实，不核融资/人事及涨跌因果；没有用户授权的消息发送。')
note('332-b006 334-b002 334-b007 334-b008 335-b000 335-b002 335-b003 335-b004','thought-and-holiday-context','强走势旧习、石油异常和一根筋、贪最后一分、春节奥运不必红及珍惜家庭。','心理批评不作诊断，节日前后红盘不是必然，家庭价值意见仅语境。')
note('335-b007 335-b008 335-b011 335-b012 335-b015 335-b016 336-b001 336-b006','historical-reaction-and-schedule','红包自述、开门不红、1993深综指368至94、春晚和三月、请假与重复大方向。','历史收益/点位/政策未外核，不把资金下一步意图等同可验证事实。')
note('337-b000 338-b002 338-b009','historical-stock-and-sector-context','环保新能源/农业消费/化工/高送配题材、580989走避20%自述、60079520整数关口及板块尚无领头。','作者当时名单与收益自述非当前推荐，不补匿名驴身份；600795方法及不追声明另抽。')

relations={
 'lower-l097-c-stage-classification-foundation-not-application-skill':[('完全分类','操作熟练程度','requires')],
 'lower-l097-c-stage-feb1-petro-explicit-revision-by-force':[('市场分力','走势预测','qualifies')],
 'lower-l098-c-stage-divergence-return-then-classify':[('背驰','盘整背驰','related')],
 'lower-l098-c-stage-preplan-all-branches-author-requirement':[('操作策略','边界条件','requires')],
 'lower-l098-c-stage-position-control-not-necessarily-empty':[('仓位','市场风险','qualifies')],
}
for r in rows:r['relations']=[{'source':s,'target':t,'type':kind} for s,t,kind in relations.get(r['id'],[])]
by_passage=defaultdict(list)
for r in rows:
    for e in r['evidence']:by_passage[e['passage_id']].append(r)
for item in pending:
    item['lesson_numbers']=sorted({int(passages[x]['unit_id'].split('-')[1]) for x in item['passage_ids']})
    if item['id'].endswith('figure-makers-and-late'):
        item['lesson_numbers']=[97,98];item['figure_ids']=[f['id'] for f in figures]
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
      'related_existing_claim_ids':retained_ids,'note':'中医/兵法/诗歌仅作者操作类比；回中枢后继续分类不保证停止或单边反转，熟练偏移和分力改变修订需具体原话。'},'4_reverse_check':inverse}})
for f in figures:
    key=(f['pdf_page'],int(f['id'].rsplit('fig',1)[1]))
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=figure_notes[key],
      figure_source_review='五图后期见stage-c-l097-l098-figure-applied.json，2/4编号图当日但制作人未核；所有图只作辅助，未来图不反填确认。',
      linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger)==179 and len({x['passage_id'] for x in ledger})==179
def dump(suffix,data):
    (OUT/f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x,ensure_ascii=False,separators=(',',':')) for x in data)+'\n',encoding='utf-8')
dump('reviewed.jsonl',rows);dump('coverage.jsonl',ledger);dump('pending.jsonl',pending);dump('figures.jsonl',figures)
summary={'stage':'C','schema_version':metadata['schema_version'],'graph_version':metadata['graph_version'],'lessons':[97,98],'document_id':DOC,'reviewer':REVIEWER,
 'passages_read':179,'claims':len(rows),'evidence':sum(len(r['evidence']) for r in rows),'importance_counts':dict(Counter(r['importance_level'] for r in rows)),
 'new_concepts':sorted({x for r in rows for x in r['concepts']}-set(concepts)),
 'whole_lesson_semantic_read_complete':True,'technical_extraction_complete':False,'four_round_review':True,'independent_review_claimed':False,
 'visual_pdf_pages':list(range(323,339)),'figure_objects_viewed':6,'figure_origin_counts':dict(Counter(f['origin_status'] for f in figures)),
 'pending':[x['id'] for x in pending],
 'source_passages_snapshot_sha256':SOURCE_SHA,'retained_source_links_in_ledger_only':True,'database_mode':'ro','formal_import':False,
 'acceptance':'179段四轮审读、16页6幅图检查；理论/应用类比、回中枢后的分类、资金能力与新闻/指标边界保留，五图后期，增量待预检发布。'}
(OUT/f'{BASE}.summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
db.close();sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(summary,ensure_ascii=False))
