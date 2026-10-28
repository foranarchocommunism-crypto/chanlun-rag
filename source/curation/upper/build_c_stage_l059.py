"""Materialize the main agent's four-pass reading of lesson59.

This writes curation artifacts only; the source DB remains read-only.
"""
import hashlib
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2]
KB = AGENT.parent / 'shared-knowledge/v0.1.0'
OUT = Path(__file__).resolve().parent
DOC = 'volume_1-a53e99c37ca5'
BASE = 'c_stage_l059'
REVIEWER = 'Codex 主代理 / 阶段C上册59课同模型四轮复核'
SOURCE_SHA = '21100b48045efda3a27e50a7c5b9d64c4bbed73a43b3ebcd226b1e9d7a845ac8'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-059' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 46
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 443 AND 450 ORDER BY pdf_page,id', (DOC,))]
assert len(figures) == 7
rows, pending, notes = [], [], {}
quote_overrides = {}
retained = defaultdict(list)


def pid(short):
    page, block = short.split('-', 1)
    return f'{DOC}-p{int(page):04d}-{block}'


def c(lesson, slug, shorts, text, labels, level, check, conditions=(), exceptions=(), figs=(), ambiguity='none'):
    citations = []
    for i, short in enumerate(shorts.split()):
        p = passages[pid(short)]
        # A date heading extracted at the previous paragraph's tail belongs to
        # the following paragraph; preserve source text, but don't cite that tail.
        quote = quote_overrides.get(short, re.sub(r'(?:\*+)?200[678]-\d{2}-\d{2}\d{2}:\d{2}:\d{2}$', '', p['text']).rstrip('*'))
        citations.append({'passage_id': p['id'], 'quote': quote, 'quote_start': p['text'].index(quote),
                          'figure_ids': [f'{DOC}-p{n:04d}-fig{k}' for n, k in figs] if i == 0 else []})
    cid = f'upper-l{lesson:03d}-c-stage-{slug}'
    assert cid not in old and cid not in {r['id'] for r in rows}, cid
    ps = [passages[e['passage_id']] for e in citations]
    assert all(p['speaker'] == '缠中说禅' and p['role'] in ('author_body', 'author_reply', 'author_commentary') for p in ps)
    labels = list(dict.fromkeys(canonical.get(x, x) for x in labels.split('|')))
    reasons = {1: '基础核心：定义及不能省略的条件。', 2: '主要方法：影响识别与操作选择。',
               3: '补充深化：方法适用边界。', 4: '背景细节：作者历史判断或经验自述。'}
    context = '；'.join(f"PDF{p['pdf_page']} {p['role']} {p['published_at'] or '未记单独时间'}" for p in ps)
    applicable = '；'.join(conditions) if conditions else '本条陈述的对象、级别、完成状态与所引原段语境；' + check
    row = {'id': cid, 'text': text, 'kind': 'explicit', 'conditions': list(conditions), 'exceptions': list(exceptions),
           'concepts': labels, 'ambiguity_status': ambiguity,
           'review_note': f'语境：第{lesson}课；{context}。适用条件：{applicable}。四轮：通读全部段落并核对实际页面；拆分原子命题与联合条件；比对既有概念及跨课范围；回查证据、量词、时序和配图。{check}。同一主代理四轮，不称独立复核；固定汇编边界，未核原博客。',
           'importance_level': level, 'importance_reason': reasons[level] + check,
           'reviewer': REVIEWER, 'evidence': citations, 'relations': []}
    if figs:
        assert citations[0]['figure_ids'] == [f'{DOC}-p{n:04d}-fig{k}' for n, k in figs]
        row['figure_review_note'] = '主代理实际查看原页、整图和插图右端：' + '；'.join(f['note'] for f in figures if f['id'] in citations[0]['figure_ids']) + '。配图有后加整理版及来源未核图，制作者未核，不作为作者观点唯一证明，文字独立支持命题。'
    rows.append(row)
    return cid


def note(shorts, category, reading, reverse):
    for s in shorts.split():
        assert pid(s) in passages, s
        notes[pid(s)] = {'category': category, 'reading': reading, 'inverse': reverse}


def keep(shorts, ids, reason):
    for short in shorts.split():
        for id in ids.split():
            assert id in old, id
            retained[pid(short)].append(id)
    note(shorts, 'existing_claim_retained', reason, '保留跨课线索；旧命题及旧证据不改。' + reason)


def issue(slug, shorts, description, action, blocker=False):
    pending.append({'id': 'upper-l059-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})

c(59,'segment-shape-not-amplitude-nonoverlap-up-can-extend','443-b012','线段长短和幅度无关，关键在走出形态；本课说若各低点都高于前一个高点，即使持续延伸仍只是一线段。','线段|幅度|重叠',1,'保此同向无重叠形态条件，不因涨百点就自动升线段数/级别；早期线段语境不当后67特征序列全部细则。')
c(59,'adjacent-segments-alternate-direction-not-two-same-direction','444-b000','前后相邻的两个线段不能同向，同为向上或同为向下不能构成相邻两线段。','线段|走势分解',1,'是相邻已构成线段的方向限制，不是所有上涨之间都无需完整相反段；不把同向同级走势类型也套成此线段结论。')
c(59,'atleast-three-fold-no-flat-one-price-limit-below-segment','444-b000','本课说线段至少呈上—下—上或下—上—下，不能只是一条走平直线；一字涨停无论延续多久，仍低于线段层次、属最小级别。','线段|涨停|最低级别',1,'保原至少三折及一字涨停形态例；58除缺口例外/后62至少三笔和严格笔结构分存，不以历时/涨幅自行升级，也非所有涨停走势都无段。',ambiguity='definition_boundary')
c(59,'first20-23-one-center-extends-29-third-buy','445-b000','图一20—23形成的1分钟中枢继续延伸，29是该中枢的第三类买点。','中枢延伸|第三类买点|走势中枢',1,'点号为59本图局部编号；不得与58同号直接实体合并，需完整次级离返和最近中枢条件，不以任意29价格点就买。',figs=[(444,1)])
c(59,'second33-and37-two-recent-one-centers-third-buys','445-b000','图二33对应28—31、37对应32—35，分别是相应1分钟中枢的第三类买点。','第三类买点|走势中枢|次级别',1,'两买点各有自己的最近中枢，不把28—31一枢同时套到37；与图一有编号交叠，不等三图时间无重叠。',figs=[(444,2)])
c(59,'third-red-arrow-higher-green-segment-end-unconfirmed','445-b000','图三红箭头高于绿箭头，因此作者说该线段尚不能确定完成，须看后续走势。','线段|完成|确认',1,'未编号尾段与45后折返不能提前画成最终终点；后K不许倒填6/14早确认状态。',figs=[(445,1)])
c(59,'early-segment-end-trend-divergence-else-consolidation-shock-second','445-b000','本课一般以趋势背驰或其他情形盘整背驰确认线段结束；若突发事件，则看第二类买卖点，因原理同大级别而所用级别特别小。','线段|背驰|盘整背驰|第二类买卖点',1,'保一般/趋势与其他/突发分支；是第59课早期图解法，后64/67的线段破坏/特征序列精确化不能被一句MACD背驰替代。',figs=[(445,1)],ambiguity='definition_boundary')
c(59,'third-future-42-45-one-center-oscillation-until-third-point','445-b000','图三后续走势应联系42—45的1分钟中枢，先按中枢震荡观察，直到出现其第三类买卖点。','中枢震荡|第三类买卖点|走势中枢',1,'最近枢42—45与前28—31/32—35分开，直到出现非作者已经确认未来三买/三卖。',figs=[(445,1)])
c(59,'3994-precision-one-or-three-segments-preselect-uniform','446-b000','本课所称前课7—8—9例中，8下低3994.57与7中最后高3994.21极近；个位精度可作重合而分三线段，两位小数可作一线段，精度须事先确认并统一。','价格精度|重叠|线段',1,'原数和局部7—8—9引用保留，未核其与前各图标号对应，不当57点7=3858同点；未指定四舍五入/截尾算法，不补精度容差数值。',conditions=['本课3994.57与3994.21近邻例','事先预设同一价格精度并全程统一'],ambiguity='definition_boundary')
c(59,'near-and-obvious-down-up-down-prefers-three-no-substantial-impact-author','446-b000','对如此相近且8内有明显下—上—下的例子，作者倾向看三线段，并称按何种统一精度无实质影响。','价格精度|线段|操作策略',2,'倾向不是一律必须；无实质影响是作者该例评价，非所有精度/软件/阈值/交易结果都等价的实证结论。')
c(59,'one-minute-chart-is-precision-premise-not-larger-level-ban','446-b001','从1分钟图起分析，只是把1分钟图精度作为基础前提，并不妨碍分析更大级别。','周期K线图|价格精度|级别',1,'观察图与走势级别不同，不把图框5分钟偷换为5分走势；最低数据精度仍限制可分辨结构。')
c(59,'1-19-five-type-only-consolidation-no-two-five-centers','446-b001','1—19最终未形成两个5分钟中枢，作者将其定为一个5分钟盘整走势类型。','盘整|走势类型|走势中枢',1,'最终确认且未两个同5分枢，不因前跌幅大或内部多个1分枢自动叫5分下跌趋势；59图19低3404与58图17同价编号差异未自动归因。',figs=[(445,2)],ambiguity='definition_boundary')
c(59,'19-45-atleast-five-center41-below32-but-type-unfinished','446-b001','从19至45因41低于32，作者判至少含一个5分钟中枢，但新的5分钟走势类型尚未最终完成。','完成|走势类型|走势中枢',1,'有中枢不等走势已完成；不只凭图幅或选图周期判级别，也不提前叫已完成上涨趋势。',figs=[(446,1)])
c(59,'alternate22-31-five-center29-below24-unfinished-invariant','446-b002','另一分解下，因29低于24，22—31构成5分钟中枢；无论如何分解，19—45至少是未完成5分钟走势类型的结论不变。','走势多义性|走势中枢|完成',1,'不同分解的枢范围不硬合并，未完成是本时点不变量；不等未来任何级别/任意不合规则划分都等价。',figs=[(446,1)])
c(59,'alternate41-third-buy-if-new-five-nonoverlap-then-uptrend','446-b002','在22—31为5分钟中枢的分解下，41是其第三类买点；若41起上升最终形成的5分钟中枢与22—31中枢不重叠，19起才成为5分钟上涨趋势。','第三类买点|上涨|完成|走势多义性',1,'保指定分解/若/最终新枢与旧枢不重叠；不是41三买本身已保证形成完整上涨趋势。',conditions=['本课22—31为5分钟中枢的另一分解','41起上升最终形成新5分钟中枢且与旧枢不重叠'],figs=[(446,1)])
c(59,'strong-if-no42-45-third-sell-or-expand-not-touch22-31-oscillation','446-b003','若42—45一分枢震荡不出三卖，或虽出三卖但后扩张走势不触及22—31五分中枢震荡区间，作者判断仍为强势；即便成30分钟以上枢，也至少围绕42—45发展。','中枢扩展|第三类卖点|中枢震荡',1,'原中枢震荡区间不同于只取中枢核心上下界；两个强支为或，第二支仍要求后扩张不触及；30分钟以上/至少不省，不把三卖无条件等弱。',conditions=['本课42—45一分枢及22—31五分枢震荡区间'],figs=[(446,1)])
c(59,'otherwise-weaker30-center-expand-from22-31-operation-own-level','446-b003 447-b000','不满足上述强势条件时，作者认为将以22—31五分中枢震荡区间为基础扩出30分枢，走势较弱；具体按自身操作级别选择对应中枢作震荡操作。','中枢扩展|操作级别|中枢震荡',1,'跨页的手法承接明确；较弱不等必然直跌、具体区间参数未给，操作须自己的级别不任意逃避换级。',figs=[(446,1)])
c(59,'jun14-42-45-extended-nine-now-five-center-gap-not-filled','447-b001','6月14日收评称42—45原1分钟中枢已延伸9段而成为5分钟中枢；当日缺口尚未完全回补，短线仍关键。','中枢延伸|中枢扩展|完成|缺口',1,'9段为本例已延伸总结构，不是所有中枢定义须九段或原三段之外再九段；由早未完成到收盘新增结构，后加6/15图不证早知。',figs=[(447,1)])
c(59,'oscillation-sell-before-buy-top-reduce-bottom-rebuy-old-low-chips','447-b002','对低位已有筹码，在单边结束进入较大震荡、出现顶背驰或盘背时先减仓，后震荡下底背驰或盘背再补；作者称先卖后买形成节奏较安全。','中枢震荡|仓位|背驰|盘整背驰|操作节奏',1,'保已有低位筹码、单边结束/较大震荡和两端结构；不把先卖买变所有新资金建仓唯一方式，较安全非零风险或各账户必降成本。',conditions=['从低位上来的已有筹码','单边结束进入较大级别震荡，顶/底背驰或盘背分别出现'])
c(59,'buy-before-sell-low-position-wrong-rhythm-author-context','447-b002','作者在该已持低位筹码的节奏语境中，将先买后卖解释为单边时仓位不高、尚有闲资，并评价为此前节奏先错。','仓位|操作节奏|机动资金',2,'保作者唯一可能强语及其限定语境，不泛化所有分批建仓/资金管理/新入资金都是错。')
c(59,'possible-third-sell-stronger-shake-stop-rebuy-wait-down-buy','447-b003','一旦震荡力度超过前面、可能形成第三类卖点，就应停止回补，等三卖引发下跌后出现买点再进入，不能预先假定跌不深。','第三类卖点|操作节奏|买点|确认',1,'有可能阶段已停回补，不等先确认三卖才停；后续再入仍需买点，不能跌到猜测百分比就补；力度量化本段未给。')
c(59,'policies-news-psychology-component-move-result-force','447-b004','作者将政策、心理和消息视作市场分力，将走势视作合力结果。','市场分力|市场合力|政策风险|市场心理',1,'历史理论主张非对所有政策因果影响的外部实证，也不等可以忽略政策风险/执行限制。')
c(59,'jun15-third-goal4144-reached-stand-before-fourth-newhigh','447-b006 448-b000','6月15日补缺口后继续中枢震荡，作者称第三目标4144已达到，下一目标创新高，但须先站稳4144半线。','走势预测|缺口|经验压力线',2,'跨页及6/15新日期保持；达到不等站稳，创新高尚未来，消息两天都消化为作者解释未外证。',figs=[(447,1)])
c(59,'jun15-two-stock-groups-conditional-newhigh-or-no-large-divergence-retest','448-b001','若大盘重新新高，作者关注绝大多数未新高股的随后表现；另一组是已新高、无大级别背驰且回试站稳前高的股票。','板块轮动|背驰|确认|反抽',2,'两组条件不同；后一组无大级背驰与回试站稳是且，前一组依大盘新高且只是绝大多数；新高自身非任意追高买点。')
c(59,'midterm-monthly-double-bottom-neckline-retest-buy-no-crowding','448-b002','作者对中长线资金的环保股例，指出月线双底颈线处整理，回试时找买点，不要一窝蜂追高。','颈线|资金期限|买点|追高',2,'600636业绩/环保方向为当时自述未外证，月线双底非图上任何W、回试仍需买点，非当前推荐。')
c(59,'expectations-price-and-regulation-change-force-author-economic-view','449-b006 449-b007','6月18日独立文章中，作者以未来预期解释证券价格和市场波动，认为调控改变预期而走势仍是各种预期合力。','市场合力|市场心理|监管风险',3,'作为作者经济观点保存，不证明人皆只因预期涨跌买卖或一切理性预期模型被推翻；不是本项目当前经济学共识。')
c(59,'rule-confirm-maintain-not-control-results-author-regulatory-view','449-b005 449-b008','作者在该文主张虚拟经济不能靠调控结果，应通过确认维护规则、监督打假及增加优质股票供给来监管。','监管风险|市场规律',3,'原唯一有效手段为作者规范性主张，不当现行法律/政策事实或市场绝不能被任何政策影响的经验证明。')
quote_overrides['450-b004']=passages[pid('450-b004')]['text'].split('个股，',1)[0]
c(59,'jun18-gap-nature-watch-one-third-sell-effective-below4224','450-b004','6月18日作者说站稳4144后继续尝试新高，当日缺口须后续震荡确认性质；只要震荡不出现1分三卖有效跌破4224，就仍强势，否则补缺口压力增大。','缺口|第三类卖点|有效跌破|确认',1,'保一分三卖与有效跌破4224联合，不把盘中单价触4224就等三卖，也不把压力增大写必补；不会看可用5日线是辅助。',conditions=['2007-06-18当日留下缺口，后续震荡性质尚待确认'],figs=[(450,1)])

note('443-b011 444-b001','teaching_plan_and_figure_order','出差后三图补连续走势，图一二时间/编号有交叠，另增重绘图非三原图之一。','以图内点号联读，不自动把58/59同号当同点；三原图连续不等无重叠。')
note('448-b008 448-b009 448-b010 448-b011 448-b012 449-b000 449-b001 449-b002 449-b003 449-b004 450-b000 450-b001 450-b002 450-b003','independent_macro_opinion_context','完整阅读6/18独立资本市场文章四部分，生产力/文化财富/虚拟经济/个人机会为作者宏观观点，源身份和时间与技术解盘分开。','历史三次释放/中国胜出/人人可跃升/年龄性别无关等强语未外证，不作为作者技术中枢定理或本项目证实的经济事实。')
note('449-b005','independent_macro_opinion_context','独立文章第三节标题，作者监管立场由后文展开。','独立文章不是6/14课程正文；引用作者观点不构成现行制度建议。')
issue('early-segment-end-vs-later-feature-sequence-gap-flat-boundaries','443-b012 444-b000 445-b000','早期无重叠可延续/三折/无平段与背驰确认分段需同后62/64/67精确定义分层。','不以59背驰句代替后特征序列破坏条件；58缺口例外不静删。',True)
issue('precision3994-local-numbering-and-58-17-vs59-19','446-b000 446-b001','3994.57/3994.21整数相同、两小数可异及7—8—9对应原图未核；3404低58标17而59标19。','保精度事先统一；不造四舍五入算法、不自动与57点7=3858或58其他同号合并；需局部标号对照。',True)
issue('alternate-decomposition-unfinished-five-third41-trend-conditional','446-b001 446-b002','1—19盘整、19—45新5分未完和另22—31枢/41三买下未来新枢不重叠才趋势。','不把三买必续方向升级为必成上涨趋势；不任意合并不同分解中枢范围。',True)
issue('strong30-expansion-center-oscillation-range-and-nine-sections','446-b003 447-b000 447-b001','强支不三卖或后扩张不触旧五分中枢震荡区间；否则弱，9段延伸本例升级5分。','区分中枢核心与震荡区间，原30分以上/至少保；未给所有扩张与9段通用算法。',True)
issue('sell-before-buy-scope-and-stop-rebuy-before-confirmation','447-b002 447-b003','先卖后买限低位已有筹码进入较大震荡，作者先买后卖节奏错的强语不泛化；可能三卖须停补。','量化力度/通道/成本/容量仍未给，不作必可成交或必降成本，保等新买点。',True)
issue('dates-seven-figures-local-ids-MACD26-12-and-future-bars','447-b005 448-b000 450-b004','5段改6/15，7图4未核3后加，445额外图原26/12/9次序及450未来6/19保留。','原发与局部标号因未核，后K不证前瞻；CCTV9元三买与罗锅自述是读者，不因回复标题升级作者。',False)
issue('macro-article-historical-stock-and-4224-joint-conditions','448-b001 448-b002 449-b006 449-b007 449-b008 450-b004','独立宏观文章观点/环保股自述非已证事实；6/18一分三卖有效破4224联合条件。','不输出当前金融法律建议，价格触点不等结构三卖，引用不等外部事实验证。',False)

relations={
 'segment-shape-not-amplitude-nonoverlap-up-can-extend':[('线段','幅度','qualifies')],
 'adjacent-segments-alternate-direction-not-two-same-direction':[('线段','走势分解','qualifies')],
 '3994-precision-one-or-three-segments-preselect-uniform':[('线段','价格精度','requires')],
 'one-minute-chart-is-precision-premise-not-larger-level-ban':[('周期K线图','价格精度','qualifies')],
 '1-19-five-type-only-consolidation-no-two-five-centers':[('盘整','走势中枢','requires')],
 'alternate22-31-five-center29-below24-unfinished-invariant':[('走势多义性','完成','qualifies')],
 'alternate41-third-buy-if-new-five-nonoverlap-then-uptrend':[('上涨','第三类买点','qualifies')],
 'strong-if-no42-45-third-sell-or-expand-not-touch22-31-oscillation':[('中枢扩展','中枢震荡','qualifies')],
 'oscillation-sell-before-buy-top-reduce-bottom-rebuy-old-low-chips':[('操作节奏','中枢震荡','qualifies')],
 'possible-third-sell-stronger-shake-stop-rebuy-wait-down-buy':[('第三类卖点','操作节奏','qualifies')],
 'policies-news-psychology-component-move-result-force':[('市场合力','市场分力','qualifies')],
 'jun18-gap-nature-watch-one-third-sell-effective-below4224':[('第三类卖点','有效跌破','requires')],
}
for r in rows:r['relations']=[dict(source=a,target=b,type=t) for a,b,t in relations.get(r['id'].split('upper-l059-c-stage-')[1],[])]


by_passage=defaultdict(list)
for r in rows:
 for e in r['evidence']:by_passage[e['passage_id']].append(r)
for item in pending:
 item['lesson_numbers']=[59]
 if item['id'].endswith('dates-seven-figures-local-ids-MACD26-12-and-future-bars'):item['figure_ids']=[f['id'] for f in figures]
ledger=[]
for id,p in passages.items():
 linked,decision=by_passage[id],notes.get(id)
 if linked:
  result,reading='new_claim','；'.join(r['text'] for r in linked);atomic=[dict(claim_id=r['id'],conditions=r['conditions'],exceptions=r['exceptions']) for r in linked];inverse='；'.join(r['review_note'] for r in linked)
 elif decision:result,reading,atomic,inverse=decision['category'],decision['reading'],[],decision['inverse']
 elif p['role']=='reader':result,reading,atomic,inverse='reader_context','CCTV两组署名和自述完整读过。',[],'600839九元三买及罗锅身份自述为读者，虽前标题为缠回复，本处无作者署名或认可，不作为作者证据。'
 elif p['text'].startswith('教你炒股票') or p['text'] in ('缠中说禅回复：',) or re.fullmatch(r'.*200[5678]-\d{1,2}-\d{1,2}.*',p['text']) and (len(p['text'])<75 or p['text'].startswith('缠中说禅')):result,reading,atomic,inverse='source_header','课/独立文章/作者解盘/答疑/时间头定位已核。',[],'只作来源锚点，不独立证明技术命题。'
 else:raise AssertionError(('unaccounted paragraph',id,p['text']))
 if linked and decision:reading+='；其余语境：'+decision['reading'];inverse+='；'+decision['inverse']
 ledger.append(dict(passage_id=id,lesson_number=59,document_id=DOC,pdf_page=p['pdf_page'],role=p['role'],speaker=p['speaker'],published_at=p['published_at'],source_text_sha256=hashlib.sha256(p['text'].encode()).hexdigest(),result=result,claim_ids=[r['id'] for r in linked],related_existing_claim_ids=retained[id],existing_evidence_not_mutated=True,pending_issue_ids=[x['id'] for x in pending if id in x['passage_ids']],reviewer=REVIEWER,rounds={'1_read_and_scope':reading,'2_atomic_conditions':atomic,'3_normalization':{'concept_labels':sorted({x for r in linked for x in r['concepts']}),'related_existing_claim_ids':retained[id],'note':'59早期线段/三折/背驰确认分层，精度3994.57/3994.21预设统一；图内编号不跨课自动合并，盘整/新5分未完/另一22-31枢及41条件趋势分别保，强弱扩张需震荡区间，先卖后买限旧低位筹码/可能三卖停补，4224一分三卖有效破联合。'},'4_reverse_check':inverse}))
for f in figures:
 f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=f['note'],figure_source_review='实际查看443至450八页7整图及446完整页；444两图/445图一和446重绘原发未核、445额外5分图/447/450含未来K为后加；26/12/9原顺序和局部标号/精度不静改。',linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger)==46 and len(figures)==7
for suffix,data in [('reviewed.jsonl',rows),('coverage.jsonl',ledger),('pending.jsonl',pending),('figures.jsonl',figures)]:
 (OUT/f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x,ensure_ascii=False,separators=(',',':')) for x in data)+'\n',encoding='utf-8')
summary=dict(stage='C/E',schema_version=metadata['schema_version'],graph_version=metadata['graph_version'],lessons=[59],document_id=DOC,reviewer=REVIEWER,passages_read=len(ledger),claims=len(rows),evidence=sum(len(r['evidence']) for r in rows),importance_counts=dict(Counter(r['importance_level'] for r in rows)),new_concepts=sorted({x for r in rows for x in r['concepts']}-set(concepts)),whole_lesson_semantic_read_complete=True,technical_extraction_complete=False,four_round_review=True,independent_review_claimed=False,visual_pdf_pages=list(range(443,451)),figure_objects_viewed=7,figure_origin_counts=dict(Counter(f['origin_status'] for f in figures)),pending=[x['id'] for x in pending],source_passages_snapshot_sha256=SOURCE_SHA,retained_source_links_in_ledger_only=True,database_mode='ro',formal_import=False,delivery_scope='shared_knowledge_base_only',acceptance='59课46段8页7整图同模型四轮，5时间头修正和4未核3后加图；精度/局部编号、早期分段、两分解未完成/条件趋势、强弱扩张震荡区间和回补节奏/4224联合条件保，待预检。')
(OUT/f'{BASE}.summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
db.close();sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(summary,ensure_ascii=False))


