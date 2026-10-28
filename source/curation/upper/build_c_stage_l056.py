"""Materialize the main agent's four-pass reading of lesson56.

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
BASE = 'c_stage_l056'
REVIEWER = 'Codex 主代理 / 阶段C上册56课同模型四轮复核'
SOURCE_SHA = '53dd98c45a583b666cc40a353b45500d4aa47fa3012b1d939939273c7584a363'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-056' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 48
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 422 AND 427 ORDER BY pdf_page,id', (DOC,))]
assert len(figures) == 4
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
    pending.append({'id': 'upper-l056-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})


c(56,'index-second-sell-not-individual-same-kind-weak-stock-third-0948','422-b006','作者指9点48为指数二卖，同时提醒较弱个股可能三卖；指数是平均且当日比很多股强，指数二卖不等个股也二卖。','第二类卖点|第三类卖点|市场分力|操作级别',1,'55原05300947与本课9点48不统一；个股需自身结构，原一大早提醒为作者自述，未证每个市场参与者真实可按该时成交。',figs=[(423,1)],ambiguity='source_0948_vs_l055_0947_and_asset_specific_structure')
c(56,'may29-divergence-leg-unconfirmed-before-gap-first-sell-unavailable','422-b007','5月29日30分进入背驰段但尾盘高收，区间套尚不能确认；次日突发低开才确认，原一卖已不可能实操，只能用二、三卖应对。','背驰段|确认|区间套|第一类卖点|第二类卖点|第三类卖点',1,'进入段不等当时已确认一卖；原理论完全保证为作者模型性表述，不证明T+1/跌停/通道/容量下任何二三点都可成交，低开这一触发前提不可删。',conditions=['5/29尾盘高收、30分背驰段尚有次日走势待定','突发事件导致大幅低开后确认；指数/个股类型分别判断'],figs=[(423,1)],ambiguity='author_second_third_guarantee_not_individual_execution_proof')
c(56,'gap-and-subminute-at-same-coarse-view-not-global-identical-level','422-b008','在本1分图的统一观察标准下，把缺口视为最低级，1分以下结构视为无内部线段，因此缺口和1分以下走势同属图上被忽略细节的层次。','缺口|最低级别|操作级别|周期K线图',1,'视图下同级不等原始成交数据中所有细级都严格相等，也不是普遍把真实缺口定义为完成1分趋势；可换显微镜标准但一图内须统一。',figs=[(423,1)])
c(56,'B-three-apparent-centers-not-complete-sloping-third-within-second','422-b008','绿箭头之间为1分以下走势类型；B虽看似有三个1分中枢，每个所谓第三段仍向下倾斜、属第二向下段一部分，不能当中枢完成；本日为五个1分以下类型组合。','完成|走势中枢|次级别|走势分解',1,'不以三处视觉停顿/摆动即三完整中枢；五类型是本日分法不是所有暴跌固定五浪或所有最低图三段都已形成高一级中枢。',figs=[(423,1)])
c(56,'gap-down-first-leg-A-up-second-sell-forming-not-already-complete','422-b009','本例下缺口先构成1分以下向下腿；随后同层向上若不创新高或背驰构成二卖，A出现时只是构成二卖的走势形成中。','第二类卖点|缺口|次级别|完成',1,'或保持原条件，形成中不偷改已完成；不能在A一出现就排除直接强升新高，须按下文内部结构确认。',figs=[(423,1)])
c(56,'A-internal-structure-confirm-no-new-high-or-consolidation-top','423-b000','确认A二卖须看内部：作者以内部背驰、当时未新高或与前走势盘顶背的条件判断，不能仅凭出现反弹就断定二卖完成。','第二类卖点|背驰|盘整背驰|区间套|完成',1,'保原内部出现背驰而当时位置没创新高或与前面走势产生盘整顶背驰的层次，未将而/或擅重写为唯一布尔公式；仍需区分本例与53少见二卖高于一卖分支。',figs=[(423,1)])
c(56,'A-up-down-up-upward-leg-volume-or-green-red-absolute-height-aids','423-b000','作者从A内部上下上结构中原称第二段向上之背驰来确认，以成交量或首红箭头MACD绿柱与后来红柱绝对值大小辅助。','MACD|成交量|指标对比|背驰|第二类卖点',1,'第二段向上不改为上下上中间向下段；这里跨色柱绝对值大小，不等B段绿柱累计面积法，图423参数24/52/9与重绘12/26/9不静合，没数值重算。',figs=[(423,1)])
c(56,'B-vs-gap-green-area-include-three-small-not-greater-literal','423-b001','二卖后B与缺口腿比较绿柱面积，第二处须连前三小绿柱一起加；作者说后力度不大过前，判B为盘整背驰。','MACD|MACD柱波|指标对比|盘整背驰',1,'不大过原字包括未严格区分等值边界，不擅改严格小于；柱面积非价格跌幅/单柱高度，图无逐柱原数据未计算精确比值，跨图参数不混。',figs=[(423,1)],ambiguity='source_not_greater_area_boundary_vs_strict_divergence_scope')
c(56,'subminute-compare-area-one-minute-also-zero-axis-lines','423-b001','作者对本1分以下力度比较说只需柱面积；若为1分级则还须同时看黄白线回抽0轴。','MACD|操作级别|指标对比|周期K线图',1,'1分图上观察不等信号是1分级；只需/还须为本例作者辅助口径，不以任意参数MACD单独取代走势结构或给跨采样同一性公式。')
c(56,'B-consolidation-divergence-return-above-first-green-not-all-inner-start','423-b001','作者判B盘背后反弹须回到第一绿箭头位置之上，并说C验证；这只是该比较所对应的回拉目标。','盘整背驰|中枢回拉作用|幅度|走势分解',1,'第一箭头不是B内部最后一次反弹起点，后者下一段另说不必达到；回看C不当事前成交保证或所有背驰统一回抽阈值。',figs=[(424,1)])
c(56,'C-high-column-height-qualitative-not-B-area-method','423-b001 426-b009','C高点作者用对应MACD柱高度对比辅助背驰判断，答复只说一高一矮。','MACD|指标对比|背驰|高低点',2,'仅本图定性判读，未给比值/精确阈值；高度法、A跨色绝对大小与B累计绿面积分别保留，不混成所有点同一量。',figs=[(424,1)])
c(56,'ABC-overlap-one-center-4087-4122-current-reference','423-b001','作者以A、B、C三个1分以下走势重叠构成1分中枢4087—4122，后续震荡、三类点及转更大中枢/趋势以此作基准。','走势中枢|第三类买卖点|次级别|中枢震荡',1,'三完整类型与B内未成枢区分，正文整数不按重绘图4087.40/4122.41精值静改；正文包括明天为当时前瞻，不用5/31后加图证预测已保证。',figs=[(424,1)])
c(56,'B-inner-small-to-large-C-not-reach-last-inner-rebound-start','423-b002 424-b000','C高点未回B内部最后反弹起点不违作者解释：B末向下无该内部级背驰，以更小转大结束；大盘背段内部可没有该级背驰。','小级别转大级别|盘整背驰|背驰|中枢回拉作用|操作级别',1,'外B与缺口盘背不强迫内末段也有同级背驰，回拉目标依实际比较范围；绿柱缩短仅级别极小的参考，不自动定义该级背驰完成。',figs=[(424,1)])
c(56,'B-growing-green-areas-wait-break-A-low-before-gap-comparison','423-b002 424-b000','B内部绿面积逐次大，作者据此等其向下而非提前当背驰结束，最后跌破A低才形成B与缺口的盘背比较。','MACD|指标对比|完成|盘整背驰',1,'内部走势形成中与最终外比较不同范围，不能只见小柱缩短就断完整B已结束或外盘背必含内同级背驰。')
c(56,'rebound-participation-level-stock-cost-futures-hypothetical-T0-literal','424-b001','B盘背买点是否回补取决操作级别和具体股票；作者说若是股指期货有约100点空间可参与，但股票还需考虑成本与自身情况，原连接处写T+0。','指数期货|交易成本|操作级别|交易条件|T+0',1,'实际看PDF424为但由于T+0，不私改T+1，原转接与股票语境关系仍待核；如果股指期货为条件举例，不认证当时产品已上市/现行制度，100点不是扣费可得固定收益。',ambiguity='source_T_plus_0_stock_transition_not_silently_corrected_to_T_plus_1')
c(56,'larger-level-same-principles-less-frequency-safer-author-relative','424-b001','作者说小级例为解释理论，大级操作原则相同，安全性与可操作性更高、频率更低。','操作级别|操作熟练程度|市场风险|交易条件',2,'更高是作者相对选择判断，不等较大级别绝对免风险或无需仓位/通道控制。')
c(56,'may31-early-rise-below-4087-third-sell','424-b002','5月31日早上反弹未触及昨日1分中枢下沿4087，作者认定该中枢三卖。','第三类卖点|走势中枢|次级别|完成',1,'仅本例完整次级离返语境，未触价本身非所有走势都充分构成三卖；所配5/31收盘图回看不能证明每账户卖点成交。',figs=[(425,1)])
c(56,'may31-three-down-legs-vs-B-inner-divergence-nesting-1002','424-b002','三卖后三波下跌与昨日B比背驰，最后一波1分图绿柱缩短、内部亦背驰，作者用区间套定位10:02低点。','背驰|区间套|MACD|指标对比|操作级别',1,'外段比较/内部嵌套同时保留，1分观察非全部信号同级；10:02是本日案例定位，非所有三波跌都必有可实际买入点。',figs=[(425,1)])
c(56,'may31-original-one-center-expands-five-4015-4122-original-kuozhang','424-b003','作者说三卖后不成趋势就构更大中枢，反弹后原1分中枢已扩张为5分中枢4015—4122，接着围绕其震荡至三类点。','中枢扩张|走势中枢|中枢震荡|第三类买卖点|完成',1,'原扩张不静改扩展，数字为正文区间；不能认同读者4027—4077就是作者此分解的区间，后答指C首段并可另法分解。',figs=[(425,1)])
c(56,'half-line-middle-of-shock-still-at-least-three-months-influence','424-b004 425-b000','作者称1/2线在此大震荡中间，是大盘强弱重要标准，至少管3个月的观点不变。','1429点历史压力线|走势预测|价格区间|确认',2,'历史模型解释，至少影响期非所有月线三月后确认有效；日线后加图头2011且右端2007/9不作5/31当时证明，1249/1429源差保留。',figs=[(425,2)])
c(56,'may31-month-close-not-inverted-T-quality-constituents-first','425-b001','作者评价5月月线收盘上影不太长、好于最恶劣倒T，给下月回旋余地；预测近期以质优一二线成分股为主，三线待大盘基本稳定。','K线|倒T型K线|一线股|二线股|三线股|板块轮动',2,'股票分层为本段历史预测不是当前荐股/所有成分都强，月线好转不等6月不会跌或波动已完全稳定。')
c(56,'near-term-weekend-pressure-rotation-and-match-oscillation-or-trend','425-b002 426-b000','作者预期周五消息压力、震荡稳定需下周，称大震荡可比单边利润大，同时强调该震荡时震荡、该单边时单边。','中枢震荡|操作策略|市场心理|利润率',2,'作者当时预期与技能性盈利主张，无测量样本；不把震荡收益大变人人固定收益或所有时间都应来回短差。')
c(56,'S-ST-two-limit-down-comparison-rebound-space-author-case','426-b004','对重仓S/ST连续跌停读者，作者用其两个跌停约别人一个、别人回20%以上而它们约10%解释反弹空间未够。','三线股|跌停|反弹|市场风险',3,'作者历史粗略比较非精确复利等式/当前涨跌停规则，原文没给所有个股细节；不由等有空间自然反弹认证何时恢复或真实仓位。')
c(56,'choose-one-lowest-standard-ignore-below-can-change-between-charts','426-b009 426-b010','作者要求每图先定最低观察标准，把其下全部当无内部线段；换显微镜/合并图可改用5分标准、忽略不同细节，但同图标准须统一。','最低级别|周期K线图|操作级别|次级别',1,'下层实际仍可无限细不是结构事实消失，肉眼字/电子仅类比；不是任意随时切换标准使分解永远正确，需声明当前观察/操作级别。')
c(56,'new-five-center-starts-yesterday-C-other-decomposition-allowed','426-b013','对读者4027—4077疑问，作者提示其所讲新中枢三段以昨日C为第一段；也可另种分解定中枢，但讨论须按那种分解。','分解多样性|走势中枢|完成|次级别',1,'未明确认可读者所报区间在另式一定正确，也未以较晚回复覆盖前述4015—4122；三段先搞清，不能混两分解边界。')
c(56,'late-rotation-dont-sell-weak-chase-risen-strong-reset-rhythm','427-b001 427-b002','作者说理想节奏是前一日三卖退出后转一二线；若它们已涨才杀三线追一线会两边挨打，节奏不对宁暂原地调整。','操作节奏|第三类卖点|板块轮动|操作策略',1,'前一日为本段5/30，不改在5/31已知后任意按旧价格执行；非所有原地踏步都保证安全或所有板块同样点。')
c(56,'master-one-before-precise-sector-jumping-skilled-goal','427-b005','作者认为板块轮动，理想能每次准点跳换；无此技术先做好一只，技艺提高再尝试高难度。','板块轮动|操作熟练程度|操作节奏',1,'读者降低成本短差方案未获逐项无条件认可，准点轮动是目标不是既有实测能力。')
c(56,'MACD-top-bottom-shortest-dozens-bars-statistical-suggestion-not-fixed-minimum','427-b008','作者建议统计MACD从顶到底背弛的最短时间，估任何级别怎么也要几十根K，同时强调当下观察。','MACD|周期K线图|操作级别|当下',2,'原吧/可统计为估计建议，未提供样本或严格最小数，不补固定30根/各级走势最短日历表；MACD顶底时间不等任何盘整/趋势类型的普适完成下限。',ambiguity='tentative_dozen_bars_statistics_suggestion_not_proven_duration_theorem')
note('422-b005','historical-introduction-date-reference-tension','作者说讲昨天这530的1分图，标题记2007/5/30 22:49。','昨天与标题日字面不协调，日期仍按标题保，未核原博客不改成5/31；教学/股民评价非独立技术事实。')
issue('literal-T0-not-greater-and-title-yesterday-0948-vs-0947','422-b004 422-b005 422-b006 423-b001 424-b001','标题5/30却称昨天530、9点48与55原09:47不一；力度不大过未严格小于，股票回补转接T+0原字不可私改T+1。','回看原页/整图并保原字和适用范围，未核原博客；不自定时间/制度更正或全书等值背驰阈值。',True)
issue('MACD-parameter-area-height-and-inner-outer-scope','423-b000 423-b001 423-b002 424-b000 426-b008 426-b009','原截图24/52/9和重绘12/26/9不同；A跨色绝对大小/B累计面积含三小绿/C高低柱分别用，外盘背不必内末段同级背。','没有逐柱原数据不伪造数值重算，内部增长/缩短与结构完成分开；不把不大过/不一定回最后反弹起点静修成更强保证。',True)
issue('lowest-view-consistency-incomplete-B-centers-and-dozens-bars','422-b008 422-b009 423-b000 426-b007 426-b009 426-b010 427-b008','最低观察统一后缺口/更细级按线段，B所谓三中枢未完成；A形成中不能预断二卖，MACD几十K只是统计建议。','不能把固定K数/三停顿当递归中枢充分定义或把任何周期最短时间定死；而/或原确认条件逻辑范围未擅形式化。',True)
issue('shock-confirmation-first-unavailable-second-third-asset-specific-execution','422-b006 422-b007 422-b009 423-b000 424-b002','5/29只是进入背驰段未确认，低开后原一卖实际不可得；指数二卖/弱股三卖不同，理论完全保证是作者模型口径。','不回看未来造5/29已可精准退出，不证所有T+1/跌停/通道/容量下二三卖都可实操，5/31 10:02低点同样不是成交保证。',True)
issue('ABC-one-center-and-C-first-new-five-center-alternate-boundary','423-b001 424-b003 426-b012 426-b013','ABC完整重叠定1分4087-4122，5/31后反弹使5分4015-4122；作者说昨日C是新分解第一段，读者4027-4077未明确被认可。','保各式三段/整体走势边界，不混旧新中心或把另分解允许静说读者数值已正确；扩张原字不改扩展，数字不按图精值重写。',True)
issue('four-figure-provenance-parameter-and-price-label-boundaries','422-b008 423-b001 424-b002 424-b003 424-b004 425-b000','4图2当时可得但原发未核，424重绘头5/31晚正文；425日线头2011/08/18/轴2007/9后加，1249/1429、整数/小数、MACD参数均不合并。','原图/后加图供定位不互当独立原作证据，后K不证当时预测；图未核原作者不能据截图改文本日期。',True)
issue('rebound-participation-futures-hypothetical-T0-cost-and-safer-level','424-b001 427-b001 427-b002 427-b005','回补看级别/实际股票/成本，股指期货100点为如果场景，原T+0关系未明；大级更安全为相对、轮动准点为技能目标。','不认证当年期指已上市/现行规则或实赚100点，资金/时间/通道和买卖点仍需；错节奏宁先调，不在已涨后杀弱追强。',True)
issue('historical-may31-month-close-leaders-S-ST-and-profit-forecasts','424-b004 425-b000 425-b001 425-b002 426-b000 426-b004','1/2线至少影响3月、月K好于倒T、质优一二线/三线与S/ST反弹空间、下周稳定和震荡利润为作者历史判断。','不当当前资产/涨跌停法则/精确复利、实际账户/未来涨幅或策略胜率；比喻/教学语不做独立实证。')
relations={
 'index-second-sell-not-individual-same-kind-weak-stock-third-0948':[('第二类卖点','市场分力','qualifies')],
 'may29-divergence-leg-unconfirmed-before-gap-first-sell-unavailable':[('背驰段','确认','requires')],
 'gap-and-subminute-at-same-coarse-view-not-global-identical-level':[('缺口','最低级别','qualifies')],
 'B-three-apparent-centers-not-complete-sloping-third-within-second':[('走势中枢','完成','requires')],
 'B-vs-gap-green-area-include-three-small-not-greater-literal':[('盘整背驰','MACD柱波','qualifies')],
 'subminute-compare-area-one-minute-also-zero-axis-lines':[('指标对比','操作级别','qualifies')],
 'B-inner-small-to-large-C-not-reach-last-inner-rebound-start':[('盘整背驰','小级别转大级别','qualifies')],
 'rebound-participation-level-stock-cost-futures-hypothetical-T0-literal':[('操作级别','交易成本','qualifies')],
 'may31-original-one-center-expands-five-4015-4122-original-kuozhang':[('中枢扩张','中枢震荡','qualifies')],
 'choose-one-lowest-standard-ignore-below-can-change-between-charts':[('最低级别','周期K线图','qualifies')],
 'new-five-center-starts-yesterday-C-other-decomposition-allowed':[('分解多样性','次级别','qualifies')],
 'late-rotation-dont-sell-weak-chase-risen-strong-reset-rhythm':[('板块轮动','操作节奏','qualifies')],
 'MACD-top-bottom-shortest-dozens-bars-statistical-suggestion-not-fixed-minimum':[('MACD','周期K线图','qualifies')],
}
for r in rows:r['relations']=[dict(source=a,target=b,type=t) for a,b,t in relations.get(r['id'].split('upper-l056-c-stage-')[1],[])]


by_passage = defaultdict(list)
for r in rows:
    for e in r['evidence']:
        by_passage[e['passage_id']].append(r)
for item in pending:
    item['lesson_numbers'] = sorted({int(passages[x]['unit_id'].split('-')[1]) for x in item['passage_ids']})
    if item['id'].endswith('commentary-dates-and-figure-provenance'):
        item['figure_ids'] = [f['id'] for f in figures]
ledger = []
for id, p in passages.items():
    linked, decision = by_passage[id], notes.get(id)
    if linked:
        result, reading = 'new_claim', '；'.join(r['text'] for r in linked)
        atomic = [{'claim_id': r['id'], 'conditions': r['conditions'], 'exceptions': r['exceptions']} for r in linked]
        inverse = '；'.join(r['review_note'] for r in linked)
    elif decision:
        result, reading, atomic, inverse = decision['category'], decision['reading'], [], decision['inverse']
    elif p['role'] == 'reader':
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], '读者A内部结构疑问/4027-4077另一边界、S/ST账户和换股问题全部保reader；作者只按统一最低标准/C首段提示/节奏技能条件答，不默认为读者推理或数值已正确。'
    elif p['text'].startswith('教你炒股票') or p['text'] in ('缠中说禅解盘:', '缠中说禅解盘：', '缠中说禅回复:', '缠中说禅回复：') or re.fullmatch(r'.*200[5678]-\d{1,2}-\d{1,2}.*', p['text']) and (len(p['text']) < 75 or p['text'].startswith('缠中说禅')):
        result, reading, atomic, inverse = 'source_header', '课程、解盘/回复的作者署名与时间头已核。', [], '只作来源身份锚点，不独立支持技术结论。'
    else:
        raise AssertionError(('unaccounted paragraph', id, p['text']))
    if linked and decision:
        reading += '；其余语境：' + decision['reading']; inverse += '；' + decision['inverse']
    ledger.append({'passage_id': id, 'lesson_number': int(p['unit_id'].split('-')[1]), 'document_id': DOC,
      'pdf_page': p['pdf_page'], 'role': p['role'], 'speaker': p['speaker'], 'published_at': p['published_at'],
      'source_text_sha256': hashlib.sha256(p['text'].encode()).hexdigest(), 'result': result, 'claim_ids': [r['id'] for r in linked],
      'related_existing_claim_ids': retained[id], 'existing_evidence_not_mutated': True,
      'pending_issue_ids': [x['id'] for x in pending if id in x['passage_ids']], 'reviewer': REVIEWER,
      'rounds': {'1_read_and_scope': reading, '2_atomic_conditions': atomic,
        '3_normalization': {'concept_labels': sorted({x for r in linked for x in r['concepts']}), 'related_existing_claim_ids': retained[id],
        'note': '统一最低观察视角下无结构不等真实细层消失；B第三段未完成不成枢，外B盘背不要求内末段同级背；MACD原24/52/9与重绘12/26/9、A跨色大小/B含3绿面积/C高度区分，不大过/T+0/日期昨天原字保；C是新枢首段和另分解范围不混，二三卖模型保证非实盘必成，几十K统计建议非定理。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=f['note'],
             figure_source_review='实际查看422至427六页及4整图：423原样1分参数24/52/9，424重绘头5/31晚正文且12/26/9；425一分5/31收盘可得，日线头2011/08/18/轴2007/9明显后加。2未核2后加，1249/1429和整数/小数保，不以未来K证预测或面积数值。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 48 and Counter(x['lesson_number'] for x in ledger) == {56: 48}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [56], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(422, 428)), 'figure_objects_viewed': 4, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '56课48段6页4整图同模型四轮；14时间空格/4图2未核2后加；突发二三卖/指数个股、最低观察与完成B/ABC/C新枢首段、柱高面积和小转大、T+0/不大过/昨天日期及轮动/几十K估计分层，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


