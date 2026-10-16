"""Materialize the manually read lower 94-96 batch; SQLite is read-only.

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
BASE='c_stage_l094_l096'
REVIEWER='Codex 主代理 / 阶段C下册94—96课同模型四轮复核'
SOURCE_SHA='2ff4b9cfdfb58f3875ff8075ed63a854ccc1c82a17e5eb09f60598cca6794ec4'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
db.row_factory=sqlite3.Row
metadata={r['key']:json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version']=='1.1.0'
assert hashlib.sha256((KB/'sources/volume_2.pdf').read_bytes()).hexdigest()=='5332cd1b60381c47ceb81358db6bbb47882efd074fc5c869dcc3002aaed1b5c0'
passages={r['id']:dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id BETWEEN 'lesson-094' AND 'lesson-096' ORDER BY pdf_page,block_index,id")}
assert len(passages)==168
assert hashlib.sha256(json.dumps(sorted(passages.values(),key=lambda p:p['id']),ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==SOURCE_SHA
old={r['id']:dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts={r['label']:dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical={label:r['label'] for r in concepts.values() for label in [r['label']]+json.loads(r['aliases'])}
figures=[dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 311 AND 323 ORDER BY pdf_page,id',(DOC,))]
assert len(figures)==5
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
 (311,1):'1/21课程旁一分图光标1/16，行情至1/25含4511.08，后期；不能倒填课程当日机会已经显现',
 (313,1):'1/22嵌文但5分钟图行情至1/23及4511.1，后期；第二1分钟中枢仍先是预测可能',
 (318,1):'1/24嵌文但主图至1/25、日线嵌图至2月4195.8，后期；13:40非三买与段未完依正文',
 (320,1):'1/28当天五分图、标13:40及蓝框，来源未核；图时间周期不是所论中枢结构级别',
 (320,2):'580989南航JTP1六十分图、低0.338及红箭头，未见可确认日期，来源未核；顶部2.029标记与正文2.3不自行改字'
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
    pending.append({'id':'lower-l094-l096-c-stage-pending-'+slug,'status':'pending','passage_ids':[pid(s) for s in shorts.split()],
                    'description':description,'suggested_action':action,'blocks_full_semantic_extraction_completion':blocker,'reviewer':REVIEWER})




c(94,'classification-boundary-not-price-prediction','310-b007 310-b008 311-b000','作者把当机立断作为学习第一层次：机会预先分析基于完全分类的边界分划，并称其理论的数学构造保证分类边界可在当下确认。','当机立断|完全分类|边界条件|当下|走势预测',1,'数学唯一精确为作者理论主张，非项目已形式证明；预先给结构分支不保证具体点位或时间。')
c(94,'jan21-small-segment-opportunity-two-paths','311-b002 311-b003','1月21日所列最小机会为线段下移后的线段类背驰；其后最好回拉上面1分钟中枢形成5分钟中枢，另一支形成下跌的第二1分钟中枢。','线段|类背驰|走势中枢|中枢扩展|完全分类',1,'限该时点结构，最好与另一支分开，不把类背驰直接升级严格1分钟背驰。',['2008年1月21日所论指数下跌结构'],figs=((311,1),))
c(94,'jan21-follow-up-five-or-second-center','311-b004','第一个机会后，若形成5分钟中枢则有其中枢震荡机会；若为第二1分钟中枢，则等待随后底背驰，或扩展5分钟后的震荡机会。','完全分类|走势中枢|中枢震荡|背驰|中枢扩展',1,'等底背驰与先扩展两支不能并成必同刻发生，机会存在不等于每个人可交易获利。',['2008年1月21日该首个类背驰机会后的演化'])
c(94,'all-opportunities-author-correspondence','311-b005 311-b006 312-b010','作者断言任何当下均可依其理论列出后续必然出现的机会，买卖对称，并称市场机会与理论输出严格一一对应。','完全分类|买卖点|当下|走势预测',3,'作者理论全覆盖断言，未作独立完备性或市场无失误证明，不提升为项目实测结论。')
c(94,'opportunity-may-be-skipped','311-b007 311-b008 312-b011','列出机会后仍可按级别、当下资金与自身意愿选择参与或放弃，选定后等机会实际显现再当机立断。','当机立断|操作级别|资金管理|操作策略',1,'看见机会不等于必须参与全部机会；兴趣选择仍受准备、退出及能力条件约束。')
c(94,'prepare-channel-capital-exit-before-entry','311-b009 312-b000','决定参与前须安排通道、资金等准备，并预先设置退出边界条件。','当机立断|交易通道|资金管理|边界条件|操作策略',1,'跨页句子合读，退出设置是行动之前的准备，不把当机立断写成无计划追入。',['已经选择准备参与所论机会'])
c(94,'small-opportunity-exit-alternatives','312-b001','对该第一个线段类背驰机会，作者给退出参照为原最后类中枢，或向上线段走势类型中的类背驰、类盘整背驰。','类中枢|类背驰|盘整背驰|边界条件|操作策略',1,'可选参照而非全部同时满足；原文类盘整背驰保留在逐字证据，不自动成为严格中枢级别背驰。',['第94课1月21日所列第一个小机会'])
c(94,'t1-same-day-exit-impossible-risk','312-b002','在作者所说T+1条件下，所设小级别买卖点可能当天即完成，买入后可能无法卖出；设置时须参考出现时间，早上更需考虑，下午可稍放宽。','交易规则|交易通道|买卖点|操作级别|市场风险',1,'这是当时制度条件下的可执行性限制；下午胆大不等于保证次日可盈利退出，不当现行规则说明。',['作者所述T+1交易约束','所论买卖点可能同日完成'])
c(94,'reentry-with-good-medium-trend-and-prior-sale','312-b003','若中线走势很好、单一下跌线段已回落20%，且自己此前高位已卖出，作者认为相应回补可更积极。','操作级别|线段|操作策略|持股',2,'三个条件合取，20%是例子不是任何跌幅的通用买点，也不保证反弹。',['中线走势极为良好','该例一线段跌去20%','自己已在高位卖出'])
c(94,'larger-period-not-short-only','312-b004','作者以按周线操作从2005年下半年持有至当时无需一次操作为例，否定其理论只能做短线。','操作级别|周期K线图|持股|操作策略',3,'历史示范未独立核实具体买点及收益；周线操作不等于严格周级别中枢。',['2008年1月21日作者的周线操作示范'])
c(94,'size-by-situations-and-force','312-b005 312-b006 312-b007','作者要求对机会各种可能情况先判断力度再安排资金量，先明确级别再掌握见好收的节奏，并强调不会卖会丢下次买入机会。','当机立断|资金管理|级别|操作策略',2,'力度和资金量无固定比例算法，原文绝对进出疑似用字问题留底本，不补风险百分比；见好收不指任意盈利即卖。')
c(94,'beginner-fractal-and-ma-exit','312-b008','初学者可用5周、5日等均线作机械约束，一旦分型后有效跌破须退出；熟练者则依严格走势分类，不一定依赖这些线。','分型|均线|有效跌破|操作熟练程度|操作策略',1,'分型后与有效跌破联合，初心者与熟练者两层不合并；未在此给有效的统一阈值。',['初学者采用所选5周/5日等均线约束','分型后有效跌破相应均线'],exceptions=['熟练者可依严格走势分类而不依赖该约束'])
c(94,'practice-two-steps','312-b009 312-b011','作者的练习先是在任何时点迅速列出理论中的后续机会，再按当下资金等选择，等待机会显现时执行；最后一步需长期修炼。','当机立断|完全分类|操作熟练程度|操作策略',2,'练习要求不是自动证明使用者已能无遗漏输出，也不是免准备立即交易。')
c(94,'jan22-second-center-expected-exception','312-b014 313-b000','1月22日早反弹后已有第二类中枢，线段类背驰小机会将近；预期反弹至少构1分钟中枢，极可能是下跌第二中枢，除非线段式直接回5100。','类中枢|类背驰|走势中枢|下跌|完全分类',1,'类中枢已形成与类背驰尚将近、严格中枢预期不同；未来图不能反填。',['2008年1月22日该线段下跌'],exceptions=['线段式直接重回5100点'],figs=((313,1),))
c(94,'jan22-after-center-paths-and-4778','313-b001','该1分钟中枢后作者列扩展5分钟或1分钟下跌背驰两支；最坏反弹只是跌破4778后的回抽，再探底，所以是否重站4778是关键。','走势中枢|中枢扩展|背驰|反抽|确认',1,'最坏是分支非必然，4778为该次结构参照，不给任意中枢固定价规则。',['2008年1月22日所论反弹及1分钟中枢'])
c(94,'jan22-unskilled-wait-bottom-confirmed','313-b002','对该短线机会，没有相应技术者继续等日底分型确认才介入，作者认为这样风险较小。','底分型|确认|操作熟练程度|市场风险',1,'风险较小不是零风险；无技术和该机会限定保留，后96熟练提前操作不得静默撤回本句。',['2008年1月22日该反弹机会','没有把握该机会的技术'])

c(95,'market-force-made-by-people','314-b000','作者认为市场是人的合力而非机械，了解市场参与者是作者所说战胜市场的前提。','市场合力|市场心理|技术分析',2,'方法论立场，不量化参与者分力，也不认证每个人的行为可精确预测。')
c(95,'zero-investment-author-position-and-history','314-b003 314-b004 314-b005','作者提出市场要0投入赚钱，并自述1990年初借他人钱买新股、上市后归还本金，余下利润作为第一笔市场资金，此后未另投本金。','成本|资金管理|操作策略',3,'自述未查账户，不等于没有初始资金、没有借款责任或资金从无中产生；第96课明确放宽绝对零投入。')
c(95,'no-unlimited-capital-addition','314-b006 314-b008','作者反对投入市场的钱无限增加，认为原有资金还无法运作赚钱时追加更多不能替代技术与操作。','资金管理|赌徒心理|操作熟练程度',1,'反对无限加码不等同绝对禁止任何再尝试，后96限定复盘后再次机会另有原话。')
c(95,'ten-doubles-illustration-not-return-promise','314-b007','作者用1万元连续10次翻倍约到1000万元、较大本金连续亏损也会大减，说明操作稳定性比起始投入重要。','资金管理|操作熟练程度|成本',3,'1000万为原文概数，精算1024万不是原文新结论；未承诺可连续10次翻倍或验证收益率。',['具有稳定技术与操作的作者假设'])
c(95,'first-money-withdraw-principal-profit-growth','314-b009 314-b010','作者忠告先运作好第一笔资金再取回本金、用利润发展，并以十年作为考察真正成功的尺度。','成本|资金管理|操作熟练程度',2,'零成本是本金取回后的作者称呼，不意味着余仓无机会成本/无亏损风险；十年成长不是保证收益。')
c(95,'practice-money-not-affect-life','314-b012 314-b014 314-b015 314-b016 315-b000 315-b001','作者主张以不影响生活的第一笔钱实践，理论须穷源并在实践磨练升级，别人最多陪练，应从操作得失中提高自己。','资金管理|操作熟练程度|操作策略',1,'不影响生活是资金前提，修炼论不证明必人人可成功，长期练习不等于强制全职盯盘。')
c(95,'jan23-listed-stocks-for-study','315-b012 315-b013','1月23日作者列600737等股票震荡图，明确说目的为学习图形，不是说股票本身。','技术分析|操作熟练程度|走势分解',2,'完整保留教学身份，不将名单转成买入推荐或项目收益证明。',['2008年1月23日所列图形练习'])
c(95,'jan23-second-center-formed-best-third-buy','315-b014 315-b016','1月23日作者称第二1分钟中枢已形成，最好路径是其三买后线段或1分钟上涨回5100上；未有三买和有效重站4778前仍震荡。','走势中枢|第三类买点|上涨|确认|完全分类',1,'前日预期与当日已成分开；三买是该最好走势前提，非当时已确认该支或保证5100。',['2008年1月23日该第二1分钟中枢'])
c(95,'jan23-five-center-two-routes','315-b017','次好支先形成5分钟中枢再三买，有两途：九次级震荡扩展，或先1分钟三卖后底背驰回升形成5分钟。','中枢扩展|次级别|第三类卖点|背驰|第三类买点|完全分类',1,'九为原次级震荡而非任意九K；先三卖与背驰顺序不能省，第二路线不是直接三卖确认5分钟中枢。',['2008年1月23日该第二1分钟中枢后的次好分支'])
c(95,'jan23-worst-five-third-sell','316-b000 316-b001','最坏支是在该5分钟中枢后出现三卖，可构成5分钟下跌首中枢；若5分钟不能重站4778，须警惕向此支演化的苗头。','第三类卖点|下跌|走势中枢|确认|完全分类',1,'可能首中枢与完整5分钟下跌已完成不同；未站稳只是提醒非无其他支。',['2008年1月23日所列结构及最坏支'])

c(96,'gambler-virtual-target-and-fomo','316-b006 316-b007 316-b008 316-b009 316-b010','作者把无视市场而预设虚拟目标、亏后要求反弹到自定价才走，以及怕失去大赚机会，归入赌徒心理；持续加码也是其前课所指行为。','赌徒心理|市场心理|走势预测|资金管理',1,'这是作者对交易心态的分类，不作临床心理诊断；有结构依据的边界计划不与无视市场的虚拟目标混同。')
c(96,'gambler-chase-cut-fear-shortcut-life-target','316-b013 316-b014 316-b015 316-b016','作者又列砍后追、追后砍，机会时怕而涨后追，听消息找捷径，以及把买房装修等生活支出强加成市场必赚目标为赌徒行为。','赌徒心理|追高|市场心理|操作策略',2,'行为批评保留作者身份，不推断任何特定读者精神状态；5元/50元是例子不是收益记录。')
c(96,'discipline-missed-opportunities-not-one-windfall','316-b011 316-b012 316-b017 317-b000 317-b001','作者反对靠一次暴富或错过后追逐，主张严格程序、平常可持续节奏及按市场显现行动，错过可等后续机会。','赌徒心理|操作策略|操作熟练程度|当下',1,'作者称严格操作足保长期成功，项目未证明收益保证；生活膳食比喻不作为营养医学证据。')
c(96,'zero-cost-explicitly-relaxed-life-safe-money','317-b004','第96课作者明确说0成本投入不必那么严格，可使用完全不影响生活的钱，将其视为唯一资本、无后援。','资金管理|成本|赌徒心理',1,'以明确放宽原话限定95的0投入，不以日期自动覆盖；生活不受影响与不无限加码仍保留。',['资金完全不影响生活'])
c(96,'second-chance-after-full-failure-review','317-b004 317-b005','若这笔资本输光，可再给一次机会，但必须先剖析全部失败根源并视作最后尝试；又输光则退出，不是人人适合市场。','资金管理|赌徒心理|操作熟练程度|操作策略',1,'再试有复盘和最后一次限定，不能当无限补资金；退出后再学习多年的另一路径还在后段。',['首次资本输光','再次尝试前全面剖析失败根源','将其视作最后尝试'])
c(96,'after-exit-years-learning-conditional-return','317-b006 317-b007','退出后作者允许经过多年学习历练、认为有足够信心再给一次机会；仍失败则不再亲自操作，并强调市场只是生活一部分。','资金管理|操作熟练程度|操作策略',2,'多年与足够信心无统一客观阈值；不把前三次顺序编成无条件自动充值额度，基金国债是作者例举非当前推荐。',['所论退出后经过多年学习历练且认为已有足够信心'])
c(96,'jan24-bottom-formed-stroke-not-confirmed','317-b009 317-b010','1月24日作者说早上下跌最终构成日底分型、称其买点，但是否延伸成笔或被5日线压制仍待观察；5日线下移约4815、次日约4778，需突破站住。','底分型|笔|均线|确认',1,'底形成不等于向上笔确认，约数按时点保留，未来日线不能反填当日笔已确立。',['2008年1月24日该日底及4778位置'],figs=((318,1),))
c(96,'jan24-1340-not-minute-third-buy','317-b011','作者否定把1月24日13:40前后当1分钟三买，要求检查线段划分第二种情况，以及九段线段延伸后应考虑5分钟中枢、次级变成1分钟走势类型。','线段|线段破坏|第三类买点|中枢扩展|次级别',1,'原文线段分类结合上下文为分段处理，不补第二种算法全文；九段限该已存震荡，不推广任意九线段。',['2008年1月24日13:40该结构'],figs=((318,1),),ambiguity='nine_segments_case_scope')
c(96,'jan24-question-jan25-third-unfinished','317-b012 319-b007','1月24日作者问当天几段并给2/3/4/5/都非选项，1月25日明确答案为第三段尚未完成。','线段|完成|确认',1,'保留问与答跨日来源；不简化成三个均已完成，也不依后期图静默重数。',['2008年1月24日当天线段计数及1月25日答案'])
c(96,'jan25-upstroke-three-ending-zones','318-b007 318-b008 319-b000 319-b001 319-b002','该日线形态不好，即使上笔延伸后还会下笔确认；作者按上笔终点分三支：4818附近最弱，4918附近可能成双底/头肩底，5000上且回跌幅度不大则形态较好。','笔|完全分类|价格区间|确认',1,'三个价格限该情景，5000上与回跌不大联合，可能成底形态不是必然完成。',['2008年1月25日该日线向上笔情景'])
c(96,'jan25-before-fractal-confirm-skill-context','319-b003 319-b004','作者就这两日底分型操作说应在前日探低不创新低时介入，技术好者可确认其为震荡性质；不是等分型已确认才操作，随后(1,1)保持可等顶分型处理。','底分型|确认|笔状态|操作熟练程度|操作策略',1,'保留具体练习、能力与后续状态；不将此句静默删除94对无技术者等底确认的保守路径，实时确认对象仍待核。',['2008年1月24—25日该底分型练习','能辨探低属震荡并有相应操作能力'],ambiguity='preconfirmation_vs_conservative_skill_scope')
c(96,'jan25-put-warrant-study-not-general-entry','319-b005 319-b006','作者以580989认沽日线包含关系、0.739起跌约50%后的底分型和早盘不创新低为教学例，同时明确说认沽不要乱玩，无能力者不适用。','权证|包含关系|底分型|操作熟练程度',2,'该标的是认沽，概念不使用认购权证归类；跌50%不是任何权证买点，不作现行推荐。',['2008年1月25日580989教学例'])
c(96,'jan28-put-entry-warning-and-exception','319-b010 319-b011 321-b006 321-b008 321-b009','1月28日作者重申580989供学习、一般人不可介入，涨后不能追；只对底分型已买且极高震荡技术者保留参与条件，并提醒未来清零及创设等多重风险。','权证|底分型|操作熟练程度|市场风险|追高',1,'所有禁限与例外随案例保留，未来清零为当时作者风险判断而非项目核到期结果；不是新买许可。',['2008年1月28日580989案例'],exceptions=['底分型时已买入且有极高震荡技术者才保留所论参与条件'])
c(96,'jan28-worst-branch-and-nonreturn-risk','319-b013 320-b000 320-b001','1月28日作者称开盘选4818附近结束的弱支；一段跌约400点后的反弹若不回原震荡区间，有逐步成5分钟三卖风险，最坏为4778下5分钟下跌首中枢。','完全分类|第三类卖点|线段|下跌|走势中枢',1,'风险不等于三卖已确认、首中枢已形成完整5分钟下跌；约400点照录。',['2008年1月28日该弱支及反弹'],figs=((320,1),))
c(96,'jan28-other-branches-not-best-only','321-b002 321-b003','作者还列次坏支为5分钟盘整中枢最终扩展30分钟，最好支为5分钟又震回并出三买，特别反对思维被最好走势占据。','完全分类|盘整|中枢扩展|第三类买点|赌徒心理',1,'最好支是选择非预定，不得省略最坏支，也不依据主观愿望确认三买。',['2008年1月28日所列该5分钟中枢情景'])
c(96,'jan28-sixty-minute-chart-return-author-claim','321-b005','作者说580989在60分钟图从2.3下来底背驰后回拉首红箭头中枢，达到理论最低回拉幅度；后续先围绕该中枢震荡，并列未来有条件爆发与清零风险。','权证|背驰|走势中枢|周期K线图|市场风险',2,'原文60分钟图不擅升严格60分钟走势级别；图标2.029与文2.3未核，箭头和最低幅度仅作者案例认定，不认证实测。',['2008年1月28日580989该案例'],figs=((320,2),),ambiguity='figure_2_029_vs_text_2_3')
c(96,'jan28-unskilled-worst-case-capability-gate','321-b011 321-b012 321-b013','作者要求技术不足者先把最坏情况作为自己要面对的情景，若不能应付便不操作；按能力选择能胜任难度的机会。','操作熟练程度|完全分类|市场风险|操作策略',1,'知道机会与能交易不同，能力门槛不由收益诱惑替代。',['准备参与所论机会时先评估最坏情况与自身能力'])
c(96,'jan28-three-step-opportunity-recognition-operation','322-b000 322-b001 322-b003 322-b004 322-b005 322-b006 322-b007 322-b008 322-b010 322-b011','作者将初级有自我意识操作分三步：能列出各级后续机会而不预测点位时间；能辨机会成立确认；决定操作前明白下个卖点、最坏情况、分类边界及触界处理。','完全分类|确认|边界条件|操作策略|操作熟练程度|走势预测',1,'三步有严格执行前提，不把理论列机会等同实盘获利能力；作者无遗漏主张不作项目完备性证明。')
c(96,'macd-assists-not-equals-divergence','322-b009','作者明确说MACD是辅助，不能以为MACD就等于背驰；识别背驰取决于对理论的把握。','MACD|背驰|操作熟练程度|技术分析',1,'不把指标单个信号当结构背驰充分条件，具体辅助参数本段未给。')
c(96,'jan29-warrant-oscillation-and-rebound-trap-study','322-b013 322-b014 323-b000 323-b001','1月29日作者描述580989约0.6中枢及0.4至0.95震荡，并将0.72后逐级回0.85称骗人图形、一般会制造二卖后再跌；明确要求学习而不要操作。','权证|走势中枢|中枢震荡|第二类卖点|市场陷阱',2,'大致/一般和教学禁限保留，不凭价格幅度独立确认所有二卖，不推算未核收益。',['2008年1月29日580989图形教学'])
c(96,'jan29-annual-line-condition-and-force-branches','323-b002 323-b003 323-b004 323-b007','1月29日作者称初触年线，既可直接上也可先空头陷阱，要看合力；美国是否减息未知，行情不固定；所述参与需控仓，未有效破年线则仍原中枢震荡。','均线|市场合力|空头陷阱|仓位|中枢震荡|完全分类',1,'未有效破与控仓为条件，年线作用非无风险买入；外国消息因果是作者历史情景而非独立验证。',['2008年1月29日该年线及中枢震荡背景'])
c(96,'jan29-not-camp-understand-force-intentions','323-b005 323-b006','作者主张自己不预先成为多头或空头，但需分析双方想做什么、实际是否做成及失败后的后续步骤，以走势结果判断。','市场合力|市场分力|完全分类|操作策略',2,'愿望是潜在力不等于结果，不能仅由多头想补缺口宣布必补。')

keep('312-b002','lower-l087-c-stage-nov6-short-rebound-not-t1-profit','有线段反弹不等于可T+1盈利，94再次说明同日买卖点完成的执行限制。')
keep('313-b002 319-b003','lower-l093-c-stage-jan17-capability-position-and-bottom lower-l093-c-stage-jan21-daily-fractal-case-strategy','无技术者保守等底分型、较熟练者具体练习提前介入并列，不能静默以新句删除旧路径。')
keep('317-b011 319-b007','lower-l091-c-stage-dec27-return-nine-case-upgrade','九段及第二种划分是具体震荡结构条件，不把任意九线段写成5分钟中枢充分条件。')
keep('322-b009','lower-l091-c-stage-boll-select-by-pattern-structure-first','指标是辅助而走势分解为本，不把MACD直接等同背驰。')

issue('opportunity-completeness-not-proven','311-b000 311-b005 311-b006 312-b010 315-b003 322-b000 322-b003 322-b006','作者宣称数学唯一精确、理论与所有市场机会一一对应/不遗漏，但本批未给可供项目独立验证的全算法或完备性证明。','保留作者明确断言，不将查询可命中等同形式完备性、预测准确率或自动获利证明。',True)
issue('t1-time-and-exit-parameters','312-b001 312-b002 312-b003 312-b005 312-b008','类中枢退出参照、早晚时机、资金力度和有效均线跌破没有统一参数；原文从而绝对进出的资金量疑似用字，底本如此。','原文不改，能力与T+1约束随方法保留；不补统一仓位比例、下午安全保证或当前制度结论。',True)
issue('zero-cost-retry-boundaries','314-b003 314-b005 314-b007 314-b009 314-b010 317-b004 317-b005 317-b006','0投入自述与十次翻倍概数未核；96明确放宽为不影响生活资本、复盘后末次尝试及退出多年后再试，但未给客观能力/资本阈值。','将明确放宽按原话记录，不能称零初始资金、余仓零风险、保证十年成功或无限再充值。')
issue('bottom-preconfirmation-skill-scope','313-b002 317-b010 319-b003 319-b004','94无技术等日底确认与96说确认后已病太晚须提前操作，需区分保守人群/具体熟练练习；96实时判断震荡性质算法未全给。','并列条件和原话，不据课号自动覆盖，也不将确认前任一不创新低当无条件底买点。',True)
issue('nine-segments-and-second-case','315-b017 317-b011 317-b012 319-b007','九次级震荡/九线段升级、线段第二种情况与13:40不为三买、第三段尚未完均为具体例；未独立重建当日全部逐笔标记。','用作者跨日问答支持未完状态，不从后期图重数为三段已完或推广任意九段即升级。',True)
issue('figure-makers-and-late','311-b003 313-b000 317-b010 317-b011 320-b000 321-b005','本批五图已看，三图明确有文后行情，两图制作人未核；60分钟图2.029标签与文中2.3未解释，310邻图已在93批复核。','登记三后期，保留两未核；不能改正文数字/级别或用未来波动证明当时路径已确立。')
issue('warrant-expiry-and-historical-claims','319-b010 319-b011 320-b002 321-b000 321-b001 321-b005 321-b008 322-b013 322-b014','580989清零/创设/对冲、美国1987及99.999%不会等均为2008作者判断，未外核合约/历史政策/概率；图和正文价位不同。','保留教学且一般人不得介入的原话，不作当前权证/市场推荐或验证收益、期限和概率。')

note('311-b001 313-b008','lesson-teaching-context','反复强调思维差异及刺激后学习效率。','作者教学动机已读，不作为学习效率实验或数学证明。')
note('312-b013 313-b003 313-b004 313-b005 313-b006','historical-policy-and-well-rhetoric','年度展望链接、印花税/大公司圈钱、游戏规则和井年/青蛙比喻。','不核定现行政策和市场因果，不把心态技术足以成功当项目收益保证。')
note('314-b001 314-b002 314-b011 314-b013','self-training-rhetoric','糊涂入市、砸锅加码、贪婪恐惧与粉丝选秀比喻。','批评行为不诊断读者，不当参与者比例统计或鼓励借资。')
note('315-b003 315-b004 315-b005 315-b006 315-b007 315-b008 315-b009 315-b010 315-b011 315-b015 316-b002 316-b003 316-b004','historical-practice-and-market-language','预先机会与操作差异、四小时看盘/语言语法、综合竞争和青蛙汤，随图形选择。','主张练习不证明每个人可每日交易成功；四小时非所有能力人群必须全职规则，具体三支另抽。')
note('317-b002 317-b003','self-confidence-and-crisis-metaphor','超人自比、少数人长期成功及直面危机保留翅膀。','作者修辞非长期赢家比例统计或危机处理专业建议。')
note('317-b013 318-b000 318-b001 318-b002 318-b003 318-b005 318-b006 319-b008','historical-stock-and-news-rhetoric','个股新高不完全脱离指数、600737取本别追买、自己独立，深指补缺及沪指周末消息条件、补课修辞。','作者股票名单和补缺展望不是当前推荐/保证，周末无利空条件不能丢；收益及操盘未核。')
note('319-b012 320-b002 321-b000 321-b001 321-b004 321-b010 321-b014 322-b002','historical-forecast-and-discipline-rhetoric','石油10亿消息/腰斩约数、1987美崩盘假想及99.999%不可能，年线第一次喜剧预言、题材股爆发、纪律与贪念。','不认证美国政策、解禁、概率或低价反弹收益；未来清零警示保留在命题，纪律不是保证交易成功。')

relations={
 'lower-l094-c-stage-classification-boundary-not-price-prediction':[('当机立断','完全分类','requires')],
 'lower-l094-c-stage-prepare-channel-capital-exit-before-entry':[('当机立断','边界条件','requires'),('当机立断','交易通道','requires')],
 'lower-l095-c-stage-no-unlimited-capital-addition':[('资金管理','赌徒心理','related')],
 'lower-l096-c-stage-gambler-virtual-target-and-fomo':[('赌徒心理','市场心理','related')],
 'lower-l096-c-stage-gambler-chase-cut-fear-shortcut-life-target':[('赌徒心理','追高','related')],
 'lower-l096-c-stage-macd-assists-not-equals-divergence':[('MACD','背驰','qualifies')],
}
for r in rows:r['relations']=[{'source':s,'target':t,'type':kind} for s,t,kind in relations.get(r['id'],[])]
by_passage=defaultdict(list)
for r in rows:
    for e in r['evidence']:by_passage[e['passage_id']].append(r)
for item in pending:
    item['lesson_numbers']=sorted({int(passages[x]['unit_id'].split('-')[1]) for x in item['passage_ids']})
    if item['id'].endswith('figure-makers-and-late'):
        item['lesson_numbers']=[94,95,96];item['figure_ids']=[f['id'] for f in figures]
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
      'related_existing_claim_ids':retained_ids,'note':'机会结构分类与具体点位时间预测分开，能力及交易制度限制随操作保留；零投入有作者明确放宽，认沽案例不是一般人入场指令。'},'4_reverse_check':inverse}})
for f in figures:
    key=(f['pdf_page'],int(f['id'].rsplit('fig',1)[1]))
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=figure_notes[key],
      figure_source_review='本批五图：三图后期见stage-c-l094-l096-figure-applied.json，另两图制作人未核；PDF310相邻93图已经前批复核，不重复计作本批图对象。',
      linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger)==168 and len({x['passage_id'] for x in ledger})==168
def dump(suffix,data):
    (OUT/f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x,ensure_ascii=False,separators=(',',':')) for x in data)+'\n',encoding='utf-8')
dump('reviewed.jsonl',rows);dump('coverage.jsonl',ledger);dump('pending.jsonl',pending);dump('figures.jsonl',figures)
summary={'stage':'C','schema_version':metadata['schema_version'],'graph_version':metadata['graph_version'],'lessons':[94,95,96],'document_id':DOC,'reviewer':REVIEWER,
 'passages_read':168,'claims':len(rows),'evidence':sum(len(r['evidence']) for r in rows),'importance_counts':dict(Counter(r['importance_level'] for r in rows)),
 'new_concepts':sorted({x for r in rows for x in r['concepts']}-set(concepts)),
 'whole_lesson_semantic_read_complete':True,'technical_extraction_complete':False,'four_round_review':True,'independent_review_claimed':False,
 'visual_pdf_pages':list(range(310,324)),'figure_objects_viewed':5,'figure_origin_counts':dict(Counter(f['origin_status'] for f in figures)),
 'pending':[x['id'] for x in pending],
 'source_passages_snapshot_sha256':SOURCE_SHA,'retained_source_links_in_ledger_only':True,'database_mode':'ro','formal_import':False,
 'acceptance':'168段四轮审读、14页5幅本批图检查；当机立断有退出/能力/T+1限制，零投入明确放宽与分型确认操作范围保留，三图后期，增量待预检发布。'}
(OUT/f'{BASE}.summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
db.close();sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(summary,ensure_ascii=False))
