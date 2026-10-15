"""Materialize the manually read lower 78--80 batch; SQLite is read-only.

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
BASE='c_stage_l078_l080'
REVIEWER='Codex 主代理 / 阶段C下册78至80课同模型四轮复核'
SOURCE_SHA='48304534719a1ed6da51594c3a6feaf8b70cede95db92c21536025a0a398dc70'
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
db.row_factory=sqlite3.Row
metadata={r['key']:json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version']=='1.1.0'
assert hashlib.sha256((KB/'sources/volume_2.pdf').read_bytes()).hexdigest()=='5332cd1b60381c47ceb81358db6bbb47882efd074fc5c869dcc3002aaed1b5c0'
passages={r['id']:dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id BETWEEN 'lesson-078' AND 'lesson-080' ORDER BY pdf_page,block_index,id")}
assert len(passages)==392
assert hashlib.sha256(json.dumps(sorted(passages.values(),key=lambda p:p['id']),ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==SOURCE_SHA
old={r['id']:dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts={r['label']:dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical={label:r['label'] for r in concepts.values() for label in [r['label']]+json.loads(r['aliases'])}
figures=[dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 143 AND 172 ORDER BY pdf_page,id',(DOC,))]
assert len(figures)==21
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
 (143,1):'1至22、A/B/C及红箭头；图注以第78课句子提问，属课后解释，绘者未核',
 (144,1):'两组绿色背景共12示意，含a至f及包含处理红虚线，www.chzhshch.net水印；不能凭水印确认作者',
 (145,1):'绿色c/d图及笔破坏、同中间地带解释，文字为图内附注，身份未核',
 (145,2):'含我总结的处理原则及我选了第二种，独立绘者处理选择，不归作者',
 (145,3):'e/f等重叠图、粉笔色端点变更和红字原则；课后解释与正文引用区分',
 (147,1):'上证1分钟图72至87，含76—85附近当次5分钟中枢，数据至9/10',
 (149,1):'0至11点阵折线图，4/8两个峰，明确0—3、3—8、8—11三段问答对象',
 (153,1):'左侧0至11点阵图，与149图相同形态，正文讲3—4、5—6包含合并3—6',
 (153,2):'右侧0至11点阵图，9—10与7—8包含，正文说尚缺后两笔确认，不能从长箭头猜完成',
 (154,1):'600737日线、14.28和9/7标注，图延至10月，属于后期截图',
 (154,2):'两张点阵图上附加彩色线段及未来箭头，www.chzhshch.net水印；新增预测箭头不作正文证据',
 (155,1):'000938日线、9/4顶分型与假破5日线，图含11月行情，晚于9/10正文',
 (156,1):'600008日线、8/8与9/3、20.90、8/20吻，数据至10月，晚于正文',
 (157,1):'上证日线/周线合成图，9/7与6124.04、10月行情，晚于9/11附文',
 (160,1):'上证1分钟76至95、绿箭头及93点5025.57，与9/12现场解盘对照',
 (163,1):'9/13初版1分钟图含98/99标号；作者同日晚明确此处划分错误，原错图保留作比较',
 (164,1):'9/13更正版图97延伸、取消初版98/99，须与作者改错文字一起看',
 (166,1):'9/14上证1分钟图89至101，98—101中枢与随后第三类点情景',
 (169,1):'9/17上证1分钟96至101，图内复制读者问题与作者16:06答复；不混同发言身份',
 (172,1):'图一0至9点阵，5与7高度需按正文及81课完整条件分别处理',
 (172,2):'图二0至9点阵，6接近低端；单凭字形高低不能代替81课明确的5/7条件'
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
    pending.append({'id':'lower-l078-l080-c-stage-pending-'+slug,'status':'pending','passage_ids':[pid(s) for s in shorts.split()],
                    'description':description,'suggested_action':action,'blocks_full_semantic_extraction_completion':blocker,'reviewer':REVIEWER})

# Manually selected after reading all 392 passages and inspecting the 21 figures.
c(78,'segment-start-end-direction','142-b012','笔和线段都有方向；向上笔起始的线段须以向上笔结束，向下笔起始则以向下笔结束，线段不能底至底或顶至顶。','线段|笔|顶分型|底分型',1,'完整线段端点性质与首末笔方向联合保留；不是按折线净涨跌临时改变首末笔。',['完整线段'])
c(78,'segment-top-above-bottom','142-b013','同一线段两端的一顶一底，顶必须高于底；不满足该基本要求的划分错误。','线段|顶|底|高低点',1,'同一线段两端的上下关系，不把内部最高价必须为端点附加进来。')
c(78,'destruction-backward-transmission','142-b014','除新股上市后的最初一段外，每一线段都应破坏前一段；被后一段破坏的段也必须已破坏其前段，作者称这一约束可逆时间传递。','线段|线段破坏|确认',1,'保留新上市首段例外；不能用未来任意一段自动确认此前所有假定段。',['按作者定义识别的相邻线段'],['新股上市后的最初一段没有前段'])
c(78,'start-window-limits','142-b015','实际划分可从近期高低点开始，但较短窗口不能保证理解较大走势；作者在当例区分从5224点起划短图与至少追到8月17日4646点观察整波行情。','线段|走势分解|级别',2,'具体点位只是2007年9月例子，未把4646或固定回溯天数设为通用参数。',['第78课当时1分钟图案例'])
c(78,'beginner-fractal-stroke-segment','142-b016 143-b000','熟练者可心算分型和笔而直接分段；不熟练者应依次从分型、笔再到线段划分。','分型|笔|线段|操作熟练程度',2,'跨页读完；心算不等于取消笔或分型定义条件。')
c(78,'strange-segment-cause','143-b001 143-b002 143-b003','线段不必总呈一波比一波高或低；作者把所谓古怪段归因于第一种情况的笔破坏后，未在该方向由该笔最终发展成线段破坏，震荡中更常见。','线段|笔破坏|线段破坏|市场震荡',1,'“该方向、由该笔”不能漏；最终线段会被破坏不等于最初破坏笔必发展成反向段。')
c(78,'down-b-up-stroke-not-enough','143-b004','对向下线段B，第一种情况的破坏笔向上；若其后未形成所需特征序列分型，就不能据该笔确认该方向的线段破坏。','线段破坏|笔破坏|特征序列',1,'方向、第一种情况、后续分型联合；不是任意向上一笔都构成破坏。',['原线段B向下','第一种情况的笔破坏'])
c(78,'same-direction-unrelated-or-extension','143-b005','同方向线段不能互相破坏；它们可能无关，也可能后者其实是前者延续，表示前段尚未完成。','线段|线段破坏|走势延伸',1,'两个分支并列，不能把所有同向段都强行拼为一段。')
c(78,'b-extension-after-break-bottom','143-b006 143-b007 143-b009','在B已确认破坏其前段、向上破坏笔未形成反向段的前提下，随后向下线段若跌破该向上笔底，B仍在延续；破坏笔曾越过B高点时，B开始点可以不是最高点。','线段|笔破坏|走势延伸|线段破坏',1,'先确认B破坏前段是关键前提；区分真实端点与全段极值。',['B已确认线段破坏其前段','向上破坏笔未在该方向形成线段破坏','随后向下段跌破该向上笔底'])
c(78,'b-destroyed-if-return-not-break-bottom','143-b008 143-b009','在同一B案例及前段已确认的前提下，随后向下段若不破向上破坏笔底，作者据此判断该向上笔可延伸为线段，B被破坏。','线段|线段破坏|确认',1,'仅本段已列结构的另一分支，不把任意回落未创新低作为线段破坏充分条件。',['B已确认破坏前段','符合前文B及破坏笔的结构','随后向下段未破向上笔底'])
c(78,'81-endpoint-data-correction','143-b007','作者明确修正前日图的81为2007年9月5日11:01的5268.74，82不变；理由是急跌时数据收集混乱，修正数据后原标记位置实际较高。','数据源一致性|线段|高低点',4,'作者明确更正而非按后来时间覆盖；实际数据正确性未独立行情回放验证。',['第77课前日80—83图的端点更正'])
c(78,'second-case-abc-one-without-fractal','144-b000','若B对A为第二种情况，C未形成第二特征序列分型就直接新高或新低，A、B、C合起来只能算一段，不能当三段。','线段|线段破坏|特征序列',1,'A/B/C是先按结构假称；缺少第二序列分型时不能凭形状完成分段。',['B对A属于第二种情况','C未形成所需第二特征序列分型便直接新高或新低'],figs=((143,1),))
c(78,'second-sequence-inclusion-required','144-b001','第二种情况的第二特征序列须严格按包含关系处理，不适用第一种情况中假设分界点两边不能作包含处理的要求。','特征序列|包含关系|包含处理|线段破坏',1,'两种情况的对象不能混同；图内第三人“我选第二种”不是作者规则。',['第二种情况的第二特征序列分型判断'],figs=((144,1),(145,1),(145,2),(145,3)))
c(78,'inclusion-direction-energy-explanation','144-b001','作者解释两类处理差别：第一种跨界包含呈现原段转折力度大；第二种的第二序列方向与原段一致，包含呈现原段能量足，须照包含处理。','特征序列|包含处理|能量结构|线段破坏',3,'这是作者对给定处理规则的解释，不从能量措辞推导未给的数字阈值。')
c(78,'standardize-only-basic-unit-analysis','144-b002','以线段为无内部结构的基本部件分析时，即使实际高低点不是端点，也可把线段标准化至高低点在端点，只关心其实际价格区间。','线段|价格区间|走势中枢|走势分解',1,'仅以线段为基础的更高层分析，不能倒改原始分段、笔或真实证据坐标。',['以线段为没有内部结构的基本部件','例如据线段构造最小级别中枢'])
c(78,'standardized-connected-polyline','146-b000','标准化后向上段最低点开始、最高点结束，向下段相反；线段连接形成连续首尾相连折线，作为后续中枢和走势类型分析的基础部件。','线段|走势中枢|走势类型',2,'与前段标准化适用范围一起读，不说未经标准化的真实端点必等极值。',['已按本课用途进行线段标准化'])
c(78,'sep10-skill-strategies','147-b003 147-b004 147-b005 147-b006 147-b007','9月10日作者按能力分当时应对：水平很差者减仓留长线品种；看不懂中枢震荡者看5日/5周线；懂震荡者按先卖后买，能力不足时宁愿卖错不买错。','操作熟练程度|仓位|中枢震荡|均线|操作策略',3,'三类能力分别适用，5日/5周指均线周期；不是人人必须减仓或能无损作差价。',['2007年9月10日高位政策与资金博弈行情'])
c(78,'sep10-five-center-not-third-point','147-b008','在9月10日案例中，76开始的5分钟中枢明确，第三类买卖点出现前继续按中枢震荡处理。','走势中枢|第三类买卖点|中枢震荡',4,'76及5分钟属于本次图，未从图的1分钟周期改成1分钟中枢。',['当次76开始的5分钟中枢'],figs=((147,1),))
c(78,'a-b-b-two-centers-trend','148-b004','对17—38上涨例子，作者指出A+b+B也可为1分钟上涨，关键是两中枢不重合，中枢之前和之后是否另有走势并不重要。','趋势|上涨|走势中枢|走势类型',1,'公式A+b+B保留；未认可读者对所有a/b级别的复述，不把任何无方向两中枢都叫上涨。',['第70课17—38的1分钟上涨案例','两个中枢按上涨结构不重合'])
c(78,'left-context-needed-before-segmentation','149-b001','对0—11示意图，若前面还有走势须先查看，不能只凭截图片段分段；若图前无任何走势，作者划为0—3、3—8、8—11三段。','线段|走势分解|笔破坏|线段破坏',2,'原归一引文末尾0338811不加改字；PDF原页的分隔和示意图共同确认三组端点。',['当前0—11图前没有其他走势时才采用三段结论'],figs=((149,1),))
c(78,'000915-entry-horizon-case','149-b004 149-b005 149-b006','作者区分000915在其所说3元附近长线买点介入，与9月10日现时中短买卖位置；后者面对大盘激烈变化有风险，须能承受中短震荡或有技术管理成本。','长期投资|操作级别|成本|市场风险',3,'保留当时价格、长短入场差别与技术/承受能力分支，不认证当前股票价值。',['2007年9月10日000915答疑'])
c(78,'short-third-buy-time-efficiency','151-b001','作者对追求快的短线法要求级别不能太小，向上盘整背驰须出，只持中枢上移而不参与演变成大级别震荡；第一卖点错过时第二卖点须走。','第三类买点|盘整背驰|中枢上移|第一类卖点|第二类卖点',2,'本段“新中枢成立马上走”与79课更细持有规则分别保留，不偷偷统一为一种机械时点。',['第78课追求快的短线策略','操作级别不能太小'])
c(78,'retail-capital-constraint','151-b005 151-b006 151-b007','作者说散户无须照搬大资金长期持同一股：有畅通通道且有相应技术者可轮换第三买点、避开中枢震荡；无技术者用较大级别，持有至背驰卖点再等新买点。','散户|主力资金|第三类买点|操作级别|交易通道',2,'能力不足分支保留，大资金不能短线任意进出是作者当时约束叙述，不是金额阈值。',['有畅通通道且相应技术时使用轮换法'],['技术不足者改用较大级别及简便观察'])

c(79,'theory-skill-capital-time-factors','151-b010 151-b011','理论、操作者理解掌握程度、资金规模与操作时间共同影响操作结果，作者明确理论不是唯一主宰因素；其中资金与时间可分类分析。','技术分析|操作熟练程度|资金管理|操作策略',3,'不能把理论自称完备等同人人实际获利。')
c(79,'busy-fund-mix-example','151-b012 151-b013 152-b000 152-b001 152-b002 152-b003','作者在2007年为无时间者举定投组合例：60%指数基金、40%与指数相关较弱的高速成长股基金，每月一次；同时不信任基金整体，并保留管理者能否选好成长股的不确定。','资金管理|成长性|操作策略|市场风险',4,'60/40和每月是示例，不是普适资产配置；指数不跑输及未来三四万点是作者当时观点，未核收益。',['第79课2007年无操作时间的散户示例'])
c(79,'third-method-response-level','152-b004 152-b005 152-b006','有充足时间且交易通道可用的散户，第三买点法须先选足以反应的级别，例如30分钟、5分钟或日线，只介入该级别第三类买点。','第三类买点|操作级别|散户|交易通道',2,'“该级别”与有时间、通道均保留，不把观察的K线周期自动当走势级别。',['散户有充足时间','交易通道可用','所选操作级别足以反应'])
c(79,'third-method-first-return-exit','152-b007','该第三买点法买后，新的次级别向上若不能新高或出现盘整背驰即退出；作者说即使其后二次回抽另起行情，也可用节省的时间参与其他机会。','第三类买点|盘整背驰|次级别|操作策略',2,'不能新高与出现盘背是或条件；“级别足够肯定赚钱”是作者主张，未认证现实收益。',['第79课有时间及通道的散户第三买点法','买后新的次级别向上'])
c(79,'third-method-center-rise-half-exit','152-b008','若未出现上述退出条件，则按该级别中枢上移持有到上移走势背驰后至少卖一半；次级别下来可回补，但有新标的时可不回补。','中枢上移|背驰|次级别|仓位',2,'至少一半、可回补和可不回补分别保留，不把首次中枢形成就当此处背驰。',['第79课第三买点法','未出现新次级别不能新高或盘背的分支'])
c(79,'third-method-second-up-all-exit','152-b008','在上移背驰后的次级别下行之后，再次级别向上只要不创新高或盘整背驰，就全部退出。','中枢上移|次级别|盘整背驰|操作策略',2,'下后再上的先后顺序不可漏，仍为两个择一触发条件。',['第79课上移背驰后的处理流程'])
c(79,'third-method-all-exit-skilled-exception','152-b008','作者另列上移背驰即全出的更快做法，但前提是对背驰判断特别有把握，而非半懂。','背驰|操作熟练程度|仓位',2,'全出是有能力前提的替代法，不覆盖至少半仓退出的一般流程。',['第79课第三买点法','对背驰判断特别有把握'])
c(79,'prefer-first-center-third-buy','152-b009','此法尽量只参与第一个中枢的第三类买点，作者认为第二个中枢以后形成更大中枢的概率急增。','第三类买点|走势中枢|中枢扩张',2,'尽量不是绝对禁止；概率急增没有样本和精确数值，不写成统计结论。',['第79课追求资金时间效率的散户方法'])
c(79,'reentry-higher-center-position','152-b010 152-b011','退出后即使股票盘整再上移，也应看高一级别中枢位置；若有可能形成其第三类买卖点才值得按作者此法再介入，否则可另找股票。','第三类买卖点|走势中枢|级别|操作策略',2,'跨段读完；这是该方法的取舍，不改买卖点一般定义。',['第79课退出后的重新选择','结合高一级别中枢位置'])
c(79,'large-retail-fundamentals-cost','152-b012','资金较大的散户不宜全资金追第三买点，可选有长期基本面价值的股票，利用各级中枢震荡降低成本、增加筹码；作者认为效率低于小资金轮换法。','主力资金|基本面|成本|中枢震荡|资金管理',3,'比较的是不同资金约束下的方法，不说大资金无需买点或不承担基本面风险。',['资金规模已不适合全量轮换第三买点'])
c(79,'higher-capital-games-more-than-chart','152-b013 153-b000 153-b001 153-b002','作者从专门猎手、板块战役到全局金融战描述更大资金层次，强调后两者须有前层经验，且全局问题不能只靠市场盘面解决。','主力资金|操作熟练程度|技术分析',4,'博弈及法律界限模糊为作者历史叙述，不构造当前法律结论或可执行攻击方案。',['第79课资金层次的作者叙述'])
c(79,'force-result-not-override-divergence','153-b003','背驰是合力结果，并非某处预先应该背驰；若力量改变了可能背驰处的最终结果，说明那里并未发生原先可能的背驰，而非已确认背驰被外力例外取消。','背驰|市场合力|市场分力|确认',1,'可能与已发生分开，不保证盘中所有疑似背驰最终成立。')
c(79,'force-result-result-opponent-exception','153-b004','作者说力量可调节合力结果本身，却不能调节“合力结果的结果”；例外是完全没有对手的一人交易。','市场合力|市场分力',3,'保留作者原措辞及对手例外，不新增可检验收益公式。',['存在市场对手的交易'],['完全没有对手的一人交易'])
c(79,'two-diagrams-no-left-context-premise','153-b006','本课两张点阵图的分析以图前无其他走势为前提；若前面有走势，则有更多变化，不能直接套同一分段答案。','线段|走势分解',2,'左侧上下文前提对两图都有效。',['本课两点阵图前无其他走势'],figs=((153,1),(153,2)))
c(79,'both-diagrams-feature-inclusion','153-b007','两图中3—4笔破坏后，3—4、5—6、7—8为相关特征元素，前两者包含可合成区间3—6，7—8与1—2、3—6构成底分型，因此两图至少两线段。','特征序列|包含处理|线段破坏|底分型',1,'3—6为区间合并，不是新增成交笔；至少两段不是都已三段。',['第79课两图','图前无其他走势'],figs=((153,1),(153,2)))
c(79,'left-diagram-three-segments','153-b008','左图8—9为第一种情况的笔破坏，随后延伸出特征序列分型，第二线段被破坏，故为三线段。','线段|笔破坏|线段破坏|特征序列',2,'包含本课前图分析的共同前提，不从折线数直接数三段。',['第79课左图','图前无其他走势'],figs=((153,1),))
c(79,'right-diagram-uncompleted-two-more-strokes','153-b009','右图9—10与7—8包含，第二段延至10；10—11仅一笔，须再看两笔是否延伸出所需特征序列分型，所以图尚未完成。','线段|包含关系|特征序列|确认',1,'须看两笔不是两笔必确认；保留未完成状态，不从后加未来箭头反填。',['第79课右图','图前无其他走势'],figs=((153,2),(154,2)))
c(79,'right-diagram-nine-below-seven-alternative','153-b009','若右图9跌破7而10位置不变，作者明确说即为三线段。','线段|线段破坏|高低点',2,'9跌破7与10不变须联用；不能迁移成第80/81课不同示意图的5/7条件。',['第79课右图的假设变体','9跌破7','10位置不变'],figs=((153,2),))
c(79,'fractal-auxiliary-periods','154-b001','分型辅助判断一般至少用日线以上K线图，30分钟也可；作者认为变化太快时准确率有问题。','分型|周期K线图|操作策略',3,'图周期与走势级别分开；没有给准确率数值或限制分型只能存在于这些周期。')
c(79,'600737-inclusion-fractal-example','154-b005','600737日线2007年9月4—6日包含处理后，9月7日打破包含且未创14.28新高，作者称为典型顶分型。','顶分型|包含处理|K线',4,'日期、价格限于当例，图含后期行情不认证当时判断准确率。',['第79课600737历史案例'],figs=((154,1),))
c(79,'top-fractal-not-necessarily-stroke','155-b000 155-b001','顶分型后不一定形成满足独立K线要求的底分型及笔；作者以0008022007年8月9日顶分型后未成笔而在5日线附近盘旋为例。','顶分型|底分型|笔|均线',1,'形成分型与构成笔不是等价；不删旧笔的独立K线条件。')
c(79,'five-day-break-or-continuation','155-b000 155-b002 155-b003','顶分型后若有效跌破5日线，作者认为即使不成笔也可能以时间换空间调整；未有效跌破则往往是中继，0009389月4日假破后上攻为例。','顶分型|有效跌破|均线|调整',2,'往往及一般经验保留；有效跌破本课未给固定百分比或天数。',['第79课日线顶分型辅助观察'],figs=((155,1),))
c(79,'fractal-needs-small-level-points','155-b004 155-b007','利用顶分型操作须配合小级别第一、第二买卖点；仅看当日未破前高或前低而看不清小级别，作者认为效果不会好。','分型|第一类买卖点|第二类买卖点|次级别',2,'必要配合条件保留，不能把当日一个未破价格单独当可执行卖点。')
c(79,'second-sell-retest-divergence-branches','155-b004','小级别第二卖点后，次级别跌破无盘整背驰时调整力度大，时间延长可形成笔；若形成盘整背驰，调整可演化为较大级别震荡而力度有限，一般不有效破5日线。','第二类卖点|盘整背驰|次级别|笔|均线',2,'两分支分别处理，日线向下笔对应较长调整是作者此处经验，不给固定持续时长。',['第79课日线顶分型的小级别配合语境'])
c(79,'replenish-divergence-not-premature','155-b008','分型辅助操作要识别盘整背驰以免漏回补；若不是盘整背驰，作者要求等背驰出现再回补，买点情形反向看。','盘整背驰|背驰|买点|操作策略',2,'不是一跌就回补；这是一套分型辅助方法的后续条件。',['第79课与小级别买卖点配合的分型辅助法'])
c(79,'fractal-small-points-one-way','156-b000','大级别分型出现时有某小级别第一、第二买卖点，但某小级别一二点出现不一定形成大级别分型，因此分型只是辅助。','分型|第一类买卖点|第二类买卖点|级别',1,'某小级别不是所有低级别；有前者推后者的单向关系不改为双向等价。')
c(79,'600008-intraday-not-close-only','156-b002 156-b003','6000089月3日例中，当日未破20.9且小级别确认卖点时可在冲高操作，不必等收盘；次日回补核心看小级别盘整背驰而不只是5日线是否破。','顶分型|盘整背驰|确认|均线',2,'当日不破阈值与小级别当下确认必须同时保留，不能未开盘无条件预测整日最高价。',['第79课6000089月3日案例','当日未破20.9','结合小级别走势当下确认卖点'],figs=((156,1),))
c(79,'000938-intraday-case','155-b005','作者以0009389月4日冲高低于前高且有小级别卖点先退出、跌破5日线后见小级别盘背再回补，说明分型形成日不必等收盘操作，称该次短差超过10%。','顶分型|盘整背驰|操作策略',4,'10%为作者案例自述，未核成交；有卖点及回补盘背条件不能省略。',['第79课000938历史案例'],figs=((155,1),))

c(80,'top-fractal-exit-author-stance','158-b008 158-b009 158-b010 158-b011','第80课作者从所有顶点为顶分型出发，主张出现顶分型先离开，再判断后续是否成笔，并把前课形成分型当日冲高操作的说法扩到周K线。','顶分型|笔|操作策略|周期K线图',2,'保留作者此课强语气，与79课小级别配合和辅助定位分别展示，不擅自统一或删除前课条件；不认证见任何局部形状就可盈利退出。',['第80课对当次日周顶分型的操作论述'],ambiguity='cross_lesson_scope_requires_context')
c(80,'top-fractal-stroke-or-not-adjustment','158-b009 158-b010','作者把顶分型后的调整分为形成笔与不形成笔，认为前者调整大、后者小，均有反应空间。','顶分型|底分型|笔|调整',3,'应联读77课原笔全部条件；本课简写不替代独立K线与顶底区间条件，也未给固定幅度。')
c(80,'center-up-departure-sell-before-third-buy','158-b013 158-b014','作者在最近5分钟中枢案例中，强调向上离开5333后的震荡卖点应先处理；卖后回抽若不到5333可能形成三买，但属于后续事情。','中枢震荡|卖点|第三类买点|当下',2,'可能三买不是充分条件；5333限本次中枢，不把每次离开都视作即时已确认卖点。',['第80课最近5分钟中枢震荡案例'])
c(80,'5395-week-fractal-risk-branches','158-b015 159-b000 159-b001 159-b002 159-b003','5395处类背驰并出现线段破坏后，作者比较上破5412仅17点与周顶成立后至少到底分型及5周线、成笔可能调整3600以来约四分之一450点的两条情景；卖后仍可等震荡低点或三买。','顶分型|类背驰|线段破坏|调整|均线',4,'17/450、1/4为作者当时风险情景，不作概率实测；周顶可能不成立，不能预写必跌450。',['2007年9月11日5395处案例'])
c(80,'error-correct-and-capability','159-b012 159-b013 159-b014 160-b001 160-b002 160-b003','作者要求失误后总结、避免重犯，确认买错应及时纠正；技术与执行不足时先减仓，只做能力范围内的机会。','操作策略|操作熟练程度|仓位|市场风险',3,'自律原则不等于每个二三类点都是错误交易的保证救援；能力条件保留。')
c(80,'participation-level-ability','160-b004','作者把大跌视为下一买点后大反弹的前戏，同时强调是否参与与操作者的级别和能力有关。','操作级别|操作熟练程度|买点|反弹',3,'反弹前戏是作者对走势的判断，不认证实际盈利；参与范围明确与级别和能力相关。')
c(80,'sep12-92-third-sell-case','161-b001 161-b002','9月12日作者说首个绿箭头一笔未笔破坏，须回落完成段；92虽线段破坏但未回85，构成85—88的1分钟中枢第三类卖点。','笔破坏|线段破坏|第三类卖点|走势中枢',4,'原文100%为作者理论保证说法；图上历史端点与对应中枢范围保留。',['2007年9月12日图中绿箭头与92案例'],figs=((160,1),))
c(80,'sep12-93-class-divergence-expansion','161-b003 161-b004','作者在同图把93称为线段类背驰，表示88—93下跌完成、其后至少形成1分钟中枢并出现针对该下跌的反弹。','类背驰|完成|走势中枢|反弹',4,'类背驰不是已完成1分钟趋势背驰；至少形成中枢不等于反弹已完成。',['2007年9月12日88—93下跌案例'],figs=((160,1),))
c(80,'sep12-five-center-third-sell-path','161-b005 161-b006','84—93的1分钟走势离开76—85的5分钟中枢后，作者要求看1分钟反抽能否回到79点5265以上；不能则三卖、至少扩30分钟中枢或最弱5分钟下跌，若三卖不成则继续中枢震荡。','第三类卖点|次级别|走势中枢|中枢扩展',4,'1分钟反抽须实际走出，不能仅凭瞬时不到5265就宣布完整三卖。',['2007年9月12日76—85中枢及84—93离开案例'])
c(80,'sep13-wrong-level-explicit-correction','163-b007 164-b000 164-b001','9月13日晚作者明确更正当日划分：错把绿箭头中一折当笔、进而当成线段；它不构成笔，而线段至少三笔，因此93起回抽其实是线段类上涨，当时连1分钟中枢尚未构成。','笔|线段|走势中枢|类中枢|数据源一致性',1,'明确更正依据在原文，不仅靠较晚时间覆盖；初版96—99中枢叙述与错图保留作历史比较，不作当前结构事实。',['2007年9月13日当日图的作者更正'],figs=((163,1),(164,1)))
c(80,'sep13-corrected-96-conditional','164-b001','更正后作者列次日两分支：开盘跌破96则1分钟中枢形成；不破则97起段继续延伸，后面线段回抽也不破96时，该线段类上涨可延出三个类中枢。','线段|类中枢|走势中枢|走势延伸',2,'现时未构中枢与未来跌破96后成中枢分开，97延伸及其后回抽须实际满足。',['9月13日更正后的93起线段类上涨','对应96/97端点'])
c(80,'sep13-other-analysis-retained','164-b002 164-b003','作者明确说更正后其他分析仍有效：76起5分钟中枢未成三卖，线段类上涨已越5265；再看该上涨结束位置及后续线段调整形成的1分钟中枢演化。','第三类卖点|线段|走势中枢|确认',2,'更正对象是错误分段及级别，不能连带说当篇全部观点均被撤回。',['2007年9月13日作者明确更正语境'])
c(80,'wrong-level-understates-retrace-force','165-b003 165-b004 165-b005 165-b006','作者感谢指出错误者，并说明把线段类上涨误当1分钟走势会误判回拉力度；在这个比较中级别越小表示回拉越强，应严谨划分。','级别|线段|走势类型|操作熟练程度',3,'此处只恢复作者更正文末身份；相同93回拉的两种误划比较，不发布无条件“所有小级别力度必大”。',['第80课9月13日93起回拉的更正对比'])
c(80,'600078-rumor-not-company-benefit','163-b002 163-b003 163-b004 163-b005 165-b009','作者把600078矿消息明确称为未核实传闻，既未见详勘资料，也不能保证矿装入上市公司；即使矿真实，公司仍可能无收益，股价可随大盘跌。','公开信息|基本面|市场风险',4,'保留不保证、未核实与上市主体差异；未核当前公司事实或投资价值。',['2007年9月13日600078传闻及21:10补充'])
c(80,'sep14-week-fractal-support','165-b014','作者9月14日说周顶后若5周线支持且不有效跌破，只制造较小调整而非周笔的大调整，下一周观察该支持能否破坏周顶。','顶分型|笔|均线|调整',3,'当周情景的条件句，不把所有周顶都预判被破坏。',['2007年9月14日当周周顶及5周线'])
c(80,'sep14-one-center-third-point-choice','165-b015','对98—101的1分钟中枢，作者列下一交易日先三买则上涨走势延续、先三卖则二次探底并再考验5周线。','第三类买点|第三类卖点|走势中枢|均线',4,'先出现哪个仍待行情选择；周顶破坏只是可能极大，不写成已发生。',['2007年9月14日98—101中枢情景'],figs=((166,1),))
c(80,'ratio-lines-september-values','166-b002 166-b003','作者9月17日宏观文以1992年1429基点的比例线分析，写9月2/3线为1429+184×30×2/3=5109、3/4线为1429+184×30×3/4=5569，并称确认站稳一般需三个月以上。','经验压力线|宏观市场判断|确认',4,'直接保留公式，不为184和30补未在此说明的单位；三个月是作者通常分析经验，不作中枢定理。',['2007年9月宏观比例线案例'])
c(80,'quarter-close-ratio-conditional','166-b004 166-b005','作者预期若9月未收3/4线上，即使年收盘向上脱离，期间也必至少有一次类似227、530、911走势；又按9月收盘在2/3线上下分强弱，并称强弱绝对值正比于距离。','经验压力线|走势预测|宏观市场判断',4,'必至少一次和正比是作者当时预测与模型主张，未认证事后走势或统计关系；227小、530大及后续交替为其论证背景。',['2007年9月17日季度收盘前预测','9月收盘未到3/4线上时讨论年内至少一次大震荡'])
c(80,'five-month-break-large-adjustment-case','167-b000 167-b001 167-b002','作者以2005年中行情从未有效跌破5月均线的观察，认为未来有效跌破将确认更大级别调整，未破之前行情仍延续；9月震荡也在等待均线上移。','均线|调整|走势预测',4,'5月线是均线周期；这次行情的观察及未来情景不推广成所有牛市统一判据。',['2005年中至2007年9月该轮行情'])
c(80,'five-week-space-time-alternation-case','167-b003','作者预期当轮有效破5周线将有类530级别调整，并因530以空间换时间，下一次较可能以时间换空间；明确以前提无特别非系统性影响为限。','均线|调整|走势预测|市场风险',4,'绝大可能不是必定；非系统性例外不能省。',['2007年9月当轮行情','没有特别非系统性因素影响'])
c(80,'year-end-three-policy-funding-paths','167-b004 167-b005 167-b006 167-b007','作者以6100附近为当年关注位，列理想的9月收2/3线上且四季度震荡小实体、政策压力过大收2/3线下并留长上影、资金疯狂强破6100后大调整三情景。','政策风险|资金管理|走势预测|宏观市场判断',4,'理想、条件及未来时点保留；不把6100设为永恒估值或把三情景认证成已实现结果。',['2007年9月17日对2007年末的情景分析'])
c(80,'macro-forecast-not-own-theory-analysis','168-b001','作者明确说明年末文章为了照顾读者只用了通常分析方法，没有使用其理论，目的仅给大致方向。','技术分析|走势预测|宏观市场判断',3,'作者自己区分通常预测与当下理论，不能把比例线判断归为中枢或线段定理。')
c(80,'600078-followup-uncertain','168-b008 168-b009 168-b010 168-b011 168-b012','作者9月17日跟进600078时说，已查地方公司但未找到领采矿证申报资料，也可能漏查，列闹剧、私吞或以后装入等可能，称由PE变成VC。','公开信息|基本面|市场风险',4,'未找到不等于确定不存在，可能性不能变成已查实指控或当前企业事实。',['2007年9月17日作者自述跟进'])
c(80,'101-force-compare-center-context','169-b010','回答101回补时，作者要求从96—99中枢整体比较力度，不只比最近两段；101前震荡未破97表示力度有限，并以100内部黄线双回拉后再下跌较弱及柱面积较小辅助。','中枢震荡|盘整背驰|MACD|幅度',2,'保留从96开始、97边界及“100内部”原称，未替作者补另一套端点或把指标小直接判完整背驰。',['2007年9月17日96—101回补问答'],figs=((169,1),))
c(80,'segment-base-not-copy-center-below','169-b011 170-b000','作者在当次线段层次操作答疑中说线段下没有中枢，不能照套中枢概念；一般不宜用线段操作，除非概念特别清楚且深入理解中枢震荡。','线段|走势中枢|操作级别|中枢震荡',2,'实用线段层次语境，与原纯理论从逐笔成交构造中枢的入口分开，不能宣称后定义推翻前定义。',['第80课以线段为基础的实用操作答疑'],['概念特别清楚且对中枢震荡研究透彻者'])
c(80,'market-stock-correlation-and-ability','170-b003','作者把个股与大盘相关性列为另一问题：水平不高者宜选择相关度高者，水平高者可不受此取舍；日周顶后仍分别看5日/5周线支持。','操作熟练程度|市场合力|均线|顶分型',3,'未直接认可读者见底分型即可买的提问前提；相关性不是无条件跟指数交易。')
c(80,'psychological-capability-exit','170-b009','作者对恐高者说先退出可取，机会多而无需强迫自己；继续参与危险行情须有承受力，技术好者仍应按走势及消息应对。','市场心理|操作熟练程度|操作策略',3,'心理或技术两种能力条件保留，不将作者满仓自述推广给读者。',['2007年9月17日刀锋行情答疑'])
c(80,'time-convenience-select-larger-level','171-b003','买后想着卖点、卖后想着买点；时间不足或操作不便者应选较大级别，小级别只适合职业或至少半职业看盘，否则买卖点易错过。','操作级别|买卖点|操作策略',2,'节奏与时间条件联用，不给所有人指定同一个分钟数。')
c(80,'early-pure-center-not-overturned','171-b013','作者明确否认后期分型、笔、线段内容推翻原中枢定义；原定义是纯理论，从每笔成交观察在操作上很麻烦。','走势中枢|最低级别|成交分笔|线段',1,'保留理论入口与实用划分差别，不以较晚时间覆盖早定义，也不把线段等同成交分笔。')
c(80,'second-center-nine-extension-five-level','172-b012','对两个不重叠1分钟中枢中第二个经九段延伸形成5分钟中枢、尚未与第一个重叠的提问，作者答应按5分钟走势的中枢震荡处理。','中枢延伸|走势中枢|级别|中枢震荡',2,'仅该完整问题条件，不能仍只看作未完成1分钟趋势，亦不能由九段说任意九笔都是5分钟中枢。',['第二个1分钟中枢已按问题所述延伸为5分钟中枢'])
c(80,'mobile-capital-and-hedge-self-report','173-b001 173-b002','作者9月17日自述战略满仓须扣除机动资金和对冲风险仓位，机动通常在组合中10%—30%流动；大卖点时趋30%，并强调大资金有对冲的重要性。','主力资金|仓位|对冲|资金管理',4,'满仓不是总资产无任何现金或风险对冲；比例为自述非核实账户，不认证实际持仓。',['2007年9月17日回应踏空读者的自述'])
c(80,'feature-sequence-three-elements-general','173-b003','特征序列至少三个元素才可能形成分型，两个元素不可能有分型。','特征序列|分型',1,'才可能而非有三元素必有分型；补充一般数量条件，不改写成恰好三个元素。')

# Existing propositions remain immutable; related passages are ledger links.
keep('142-b012','lower-l077-c-stage-complete-segment-three-odd','首末异分型及奇数笔已有77课命题；78课新增明确首末笔方向。')
keep('144-b001','lower-l071-c-stage-after-boundary-inclusion-allowed','71课假设转折后同性质元素包含处理是相关前文；78课明确第二序列不适用第一类跨界禁包含。')
keep('149-b005','lower-l075-c-stage-zero-cost-capital-meaning lower-l075-c-stage-small-buy-not-become-long-buy','长线买点与降成本入口已有明确命题，当前000915例子保留特定对象。')
keep('150-b009','lower-l075-c-stage-unfinished-not-compare-completed','作者要求研究区间套但没有在这里重新回答滞后性的逐步证明，不代补答案。')
keep('172-b006 172-b009','lower-l081-c-stage-two-diagrams-conditional-answer lower-l081-c-stage-lesson71-last-diagram-correction','80课当日下午答案不完整，81课作者明确承认并认可完整5/7条件；不是靠时间先后擅自覆盖。')
keep('173-b003','lower-l069-c-stage-second-sequence-three-elements','69课限定第二序列的三元素要求，与此处一般特征序列补充相联。')

issue('stroke-endpoint-reply-reference','150-b003 150-b004','问笔最高点是否可不在端点，作者答“当然”后又说顶上有顶则第一个不是顶；“当然”的省略指向在本段不够明确。','保留原答复，不能只截当然来发布允许笔极值不在端点的一般结论。',True)
issue('valid-break-no-fixed-threshold','155-b000 155-b002 156-b003 165-b014','本批多处要求均线有效跌破，但未给统一百分比、根数、收盘或盘中确认算法。','保留有效条件与小级别配合，不增EPS或固定三天规则。')
issue('fractal-exit-scope','155-b004 156-b000 158-b009 158-b011','79课说分型仅辅助且须小级别配合，80课用顶分型后离开唯一选择的强语气；不能省掉前课条件，也未见本批把它们形式统一。','两课按各自表述与条件展示，不以80课自动删除79课辅助限制。',True)
issue('short-method-exit-timing','151-b001 152-b008','78课追求快策略说新中枢成立马上走，79课细化分支可持到上移背驰至少卖半；本批未将两者统一成一条固定时点算法。','分别保留课次、资金时间目标与触发条件，不静默替换。')
issue('chart-timing-and-makers','144-b001 153-b009 154-b005 155-b005 156-b003 157-b000','21张当课图已查看，七图后附解释或含后期行情；其余绘者和截屏时间未核，后加未来箭头不能确认原文未完成分段。','来源状态与文字证据分开；页173两张81课图不算当前80课图。')
issue('same-high-not-explicit-answer','172-b001 172-b002','读者问两K同高是否顶分型，作者只反问没有顶分型哪里有笔，没有明确判该两根同高构型。','不要把反问转成已认可等高顶；须先核包含、完整三K及分型条件。')
issue('forecast-performance-not-measured','152-b007 153-b003 159-b005 161-b001 167-b003','肯定赚钱、100%理论保证、1%对99%及绝大机会都是作者主张、修辞或经验；没有本项目统计样本和实际订单。','不得当开发评测准确率或当前可实现收益。')
issue('normalization-operation-details','144-b002 146-b000','作者允许以线段作无内部部件时按实际高低标准化，但本批未列所有相邻标准化区间重叠时的坐标连接细节。','记录用途和原区间，不改原始端点；实现级细则须更多明确来源。')

# Every remaining author paragraph receives an explicit context decision.
note('142-b008 142-b009 142-b010','historical_self_report','002149上市日买入自述、果汁与补课引言。','不认证订单或品牌，不从生活叙述造股票规则。')
note('142-b011','uniqueness_assertion','作者再称两种情况可唯一分线段，强调概念。','已保留77课唯一性主张及证明疑点；重复口号不新增形式证明。')
note('144-b002','scope_remainder','标准化用途已单独抽取；作者称讲完足以解决所有问题是教学修辞。','不能据此宣布项目全部线段边界已确认。')
note('146-b002 146-b003 146-b004 146-b005 146-b007 146-b008 146-b010 146-b011 147-b000 147-b001 147-b002','historical_policy_context','9月7/10日风险提示、政策与资金冲突、000938/600375及关联交易的历史评论。','原文保留；未经公司资料或交易独立核查，不将作者指责、收益预想或宏观判断作当前事实。')
note('146-b006','historical_average_context','当轮大震荡按中枢，能力不足看5周线，称3600以来未触该线。','5周线经验与后文能力分类已有本批节点，历史未触事实不认证到今天。')
note('147-b009 148-b000','historical_conditional_context','补涨后老板块不启动则扩大调整；本周能否破前高决定周分型警示。','保留当时条件预测，与后续79/80的已发生观察分开；不新增恒常行业轮动定律。')
note('148-b007 148-b010 148-b013 148-b014','historical_answers_context','同方中继与底部不同，600569收购预测，基金无信心及未来大基金事件预测。','未核当前公司或基金状况；79课基金示例单独保留，不能认证必不跑输或必倒闭。')
note('149-b009 149-b010 149-b013 150-b000 150-b001','historical_stock_context','600737顶分型14.28条件、庄家消息及002149洗盘和成本降至十几的自述。','79课直接技术例子已抽；消息、操纵动机、持仓成本未独立查实，不能把粗略数字作当前估值。')
note('150-b004','withheld_ambiguous_reply','笔端点问答逐字保留，回复当然的省略指向不唯一。','不发布笔极值不在端点的一般规则；疑点已列。')
note('150-b012 150-b013','horizon_context','作者区分中长线延泡沫目标与短线中枢震荡先卖后买。','不把欲维持两年的主观目标当行情必延两年；相关资金目标区分已在其他命题保留。')
note('150-b016 151-b000 151-b004','historical_holding_context','600636长短理由、基本面、半年线及作者两年持有和600569降成本自述。','长短入场原则已有75/81课；未认证实际持仓、不把作者个人两年设散户必须。')
note('151-b009 153-b005 154-b000 154-b002 155-b006 156-b001 156-b004','transition_or_learning','概念解答、示例引入、难点序号及多看图磨练提示。','转场不造新技术定理；全部具体规则已单列。')
note('154-b003 154-b004','historical_fractal_examples','0007788月27日与6001399月7日周K高开未破前高的顶分型例。','本批600737详细例子及一般配合规则已抽；保留无图例原文，不由两句反推所有K线高低。')
note('156-b006 156-b007 156-b008 157-b000 157-b001 157-b002 157-b003 157-b004 157-b005 157-b006','historical_session_context','9月11日政策自评、5265三卖条件、周顶/5周线、比例线及情绪纪律。','80课后续同对象分析和能力原则已抽；预测自评、几乎确定及资金结果不当实测，图157晚期行情已单列。')
note('158-b001 158-b002 158-b003 158-b004 158-b005 158-b006 158-b007 158-b012','rhetoric_and_case_intro','贪嗔痴疑慢、哲学家、棒喝、市场逻辑、9/7日顶的背景引入。','作者哲理与市场自评不是可量化技术定律；具体分型操作及例子另抽。')
note('159-b004 159-b005 159-b006 159-b007 159-b008 159-b015 159-b016 159-b017 160-b000 160-b005','rhetorical_context','宁卖错不买错、贪嗔痴疑慢、钢铁战士和无授无得等表达。','1%/99%为修辞无样本，卖出也可能有损益；不把语气强烈提升为无风险定理。')
note('159-b009 159-b010 159-b011','repeated_discipline','买点买、上涨守、卖点卖的三项操作纪律。','既有买卖点及持有原则已保留；不把情绪恐慌/疯狂本身当充分买卖信号。')
note('160-b007 160-b008 161-b000 161-b007 161-b008 161-b009 161-b010','historical_session_context','9月12日5周线反弹、当下演示和三股强弱、00093817.59底背驰、技术能力评论。','图160端点技术另抽；个股自述与100%言辞未经行情订单复核，不认证收益。')
note('161-b012 161-b013 161-b014','off_market_context','西南矿投资、人事争论与现代服务业PE的个人叙述。','不当市场结构或已证公司事实，保留上下文。')
note('162-b001 162-b002','quote_introduction','作者要求读严重更正，表扬网友并引入所引两段。','只162-b003/004保留网友；162-b005起回到作者解盘，已经来源修正。')
note('162-b005 162-b006 162-b007 162-b008 162-b009 162-b010 162-b011 162-b012 162-b013 162-b014 162-b015 163-b000 163-b001','corrected_historical_analysis','9月13日初版解盘及传闻引言已恢复作者身份，含96—99被误划1分钟中枢的情景。','同日晚作者明确更正分段和级别，错误结构不另发布为有效一般命题；原错图和原文保留作比较。')
note('164-b004','transition','作者寻找指出错误者给红花。','感谢不作为技术证明；随后读者署名和原话仍为reader。')
note('165-b012 165-b016 166-b000','method_reminder_and_rhetoric','请勿预测看当下及花开花落比喻。','不把愿望当信号，图形演化的实际规则已有具体案例。')
note('167-b009 168-b000 168-b002 168-b003 168-b004 168-b005 168-b006 168-b007','historical_session_context','9月17日三买新高自评、预测与操作区分、5000空间/比例线、政策、中字头、600569历史剧本。','年末文章通常方法另列；当下自评及持仓/价格目标未经独立回放，不作准确率。')
note('168-b013 169-b000 169-b001 169-b002','rumor_and_transition','驴的入股传闻、未明确股票、回答提问的过渡。','未明身份不从谐音补股票；传闻不是已批准事件。')
note('169-b006','unexpanded_segment_reply','对10:58—11:18成段疑问，作者反问为何不从早上高点开始。','没有在此给完整端点标注推演，不自行替作者指定线段始点价格。')
note('170-b006 170-b012 170-b015 171-b000 171-b006','historical_company_answers','番茄酱人事/增发、600432作者持仓、中铝ABC回拉和参股轮动的具体回复。','未核公司内部事实、实际成交及当前持仓；不能将未来轮动可能变成普适板块保证。')
note('171-b009 171-b010','learning_and_rhetoric','理论需学清楚多看图，图由资金画出与艺术价格的比喻。','不把画价类比当成交量估算；能力和概念要求已保留。')
note('172-b002','unanswered_equal_high_detail','没有顶分型哪里有笔的反问已读。','不能当作者直接认可读者两高相等构型；已登记未答细节。')

relations={
 'lower-l078-c-stage-segment-start-end-direction':[('线段','笔','related')],
 'lower-l078-c-stage-second-sequence-inclusion-required':[('特征序列','包含处理','requires')],
 'lower-l078-c-stage-standardize-only-basic-unit-analysis':[('线段','价格区间','related')],
 'lower-l079-c-stage-fractal-small-points-one-way':[('分型','第一类买卖点','related')],
 'lower-l079-c-stage-third-method-response-level':[('第三类买点','操作级别','requires')],
 'lower-l080-c-stage-early-pure-center-not-overturned':[('走势中枢','成交分笔','related')],
 'lower-l080-c-stage-feature-sequence-three-elements-general':[('特征序列','分型','related')]
}
for r in rows:r['relations']=[{'source':s,'target':t,'type':kind} for s,t,kind in relations.get(r['id'],[])]

by_passage=defaultdict(list)
for r in rows:
    for e in r['evidence']:by_passage[e['passage_id']].append(r)
for item in pending:
    item['lesson_numbers']=sorted({int(passages[x]['unit_id'].split('-')[1]) for x in item['passage_ids']})
    if item['id'].endswith('chart-timing-and-makers'):
        item['lesson_numbers']=[78,79,80];item['figure_ids']=[f['id'] for f in figures]
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
        result='reader_context';reading='已读提问、引述和署名，供作者回复限定对象。';atomic=[];inverse='读者观点和引述不升级为作者明说。'
    elif (p['role']=='unknown' and p['text'] in ('缠中说禅回复:','缠中说禅回复：')) or p['text'].startswith('教你炒股票') or re.fullmatch(r'(?:缠中说禅(?:解盘)?[:：]?)?\d{4}-\d{2}-\d{2}.*',p['text']) or re.fullmatch(r'.+\(2007-\d{2}-\d{2}\d{2}:\d{2}:\d{2}\)',p['text']) or set(p['text'])=={'*'}:
        result='source_header';reading='标题、时间头或栏目分隔。';atomic=[];inverse='只定位语境，不独立支持技术结论。'
    else:raise AssertionError(('unaccounted paragraph',passage_id,p['text']))
    if linked and decision:reading+='；其余语境：'+decision['reading'];inverse+='；'+decision['inverse']
    ledger.append({'passage_id':passage_id,'lesson_number':int(p['unit_id'].split('-')[1]),'document_id':DOC,'pdf_page':p['pdf_page'],
      'role':p['role'],'speaker':p['speaker'],'published_at':p['published_at'],'source_text_sha256':hashlib.sha256(p['text'].encode()).hexdigest(),
      'result':result,'claim_ids':[r['id'] for r in linked],'related_existing_claim_ids':retained_ids,'existing_evidence_not_mutated':True,
      'pending_issue_ids':[x['id'] for x in pending if passage_id in x['passage_ids']],'reviewer':REVIEWER,
      'rounds':{'1_read_and_scope':reading,'2_atomic_conditions':atomic,'3_normalization':{'concept_labels':sorted({x for r in linked for x in r['concepts']}),
      'related_existing_claim_ids':retained_ids,'note':'按对象、级别与联合条件对照；原错图、明确更正、辅助分型和实用/理论中枢入口分别保留。'},'4_reverse_check':inverse}})
for f in figures:
    key=(f['pdf_page'],int(f['id'].rsplit('fig',1)[1]))
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=figure_notes[key],
      figure_source_review='七图后加及21段作者身份恢复见stage-c-l078-l080-source-applied.json；制作人未核。',
      linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger)==392 and len({x['passage_id'] for x in ledger})==392
def dump(suffix,data):
    (OUT/f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x,ensure_ascii=False,separators=(',',':')) for x in data)+'\n',encoding='utf-8')
resolution=[{'id':'lower-l080-diagrams-explicit-l081-completion','status':'resolved_by_explicit_later_source','lesson_number':80,
  'passage_ids':[pid('172-b006'),pid('172-b009')],'supporting_claim_ids':['lower-l081-c-stage-two-diagrams-conditional-answer'],
  'resolution':'81课作者明确承认下午答复不完整，并认可5=7或5<7两图一段、5>7两图三段；旧答复及图像保留，不作无条件都一段规则。',
  'author_explicit_correction_not_timestamp_inference':True,'reviewer':REVIEWER}]
dump('reviewed.jsonl',rows);dump('coverage.jsonl',ledger);dump('pending.jsonl',pending);dump('figures.jsonl',figures);dump('resolutions.jsonl',resolution)
summary={'stage':'C','schema_version':metadata['schema_version'],'graph_version':metadata['graph_version'],'lessons':[78,79,80],'document_id':DOC,'reviewer':REVIEWER,
 'passages_read':392,'claims':len(rows),'evidence':sum(len(r['evidence']) for r in rows),'importance_counts':dict(Counter(r['importance_level'] for r in rows)),
 'new_concepts':sorted({x for r in rows for x in r['concepts']}-set(concepts)),
 'whole_lesson_semantic_read_complete':True,'technical_extraction_complete':False,'four_round_review':True,'independent_review_claimed':False,
 'visual_pdf_pages':list(range(142,174)),'figure_objects_viewed':21,
 'neighboring_l081_figures_seen_but_excluded':[f'{DOC}-p0173-fig1',f'{DOC}-p0173-fig2'],
 'figure_origin_counts':dict(Counter(f['origin_status'] for f in figures)),'pending':[x['id'] for x in pending],'explicit_later_source_resolutions':len(resolution),
 'restored_author_passages':21,'source_passages_snapshot_sha256':SOURCE_SHA,'retained_source_links_in_ledger_only':True,'database_mode':'ro','formal_import':False,
 'acceptance':'392段四轮审读、32页及21张当课图核对；来源身份已修正，技术增量待预检发布，歧义和明确更正分别保留。'}
(OUT/f'{BASE}.summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
db.close();sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(summary,ensure_ascii=False))
