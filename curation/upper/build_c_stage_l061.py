"""Materialize the main agent's four-pass reading of lesson61.

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
BASE = 'c_stage_l061'
REVIEWER = 'Codex 主代理 / 阶段C上册61课同模型四轮复核'
SOURCE_SHA = '36e39bcf1a97837414232fef4cf43deb1cff4086df37f38e725af8107e1be10b'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-061' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 83
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 457 AND 470 ORDER BY pdf_page,id', (DOC,))]
assert len(figures) == 11
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
    pending.append({'id': 'upper-l061-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})

c(61,'actual-operator-react-decomposition-not-abstract-meaning','457-b003','对实际操作者，作者强调看懂走势分解并正确反应，而非纠缠中枢抽象意义。','走势分解|当下|操作策略',2,'作者没有意义修辞不等中枢无定义/无作用；删出个人贬词作为技术事实的可能，不以此证明理论正确。')
c(61,'one-top-exit-wait-one-bottom-monthly-ignore-smaller-volatility','457-b004','按1分操作应在1分顶背驰退出、等新1分底背驰，不依后跌幅大小决定当时动作；若原按月线操作，则可接受忽略1分震荡。','操作级别|背驰|等待|操作节奏',1,'原操作级别是前提，非被套后改称月线；60已述大级破坏/快速空间例外仍保留，月年耐心例非零风险承诺。')
c(61,'around-one-center-strength-compare55-60-vs-from65','457-b006','围绕一个中枢的两段走势可比较力度；本例60—65为1分中枢，55—60与从65起的一段相比较。','走势中枢|背驰|动力学',1,'先明确哪两段、相对哪个枢，不混任意时间柱面积；此1分枢与后66—69/69—72和5分60—69各自保。',figs=[(458,1)])
c(61,'provisional-divergence-from65-invalid-if-stronger-else-recurse','457-b006','从65起未走出时可先假设进入背驰段；一旦实际力度大于55—60，则该假设被否定，在未否定前继续观察其内部背驰并逐层下钻定位。','背驰段|区间套|确认|当下',1,'假设并非已背驰；大于为原失效条件，不把等于改成大于，也不把未否定视为已证实，逐层须各自结构和比较对象。',conditions=['本课60—65一分枢两侧55—60与65起走势'],figs=[(458,1)])
c(61,'at69-no-newhigh-no-divergence70-risk-zone-not-confirmed','457-b007 458-b000','65起内部走到69时因未创新高而不构成背驰，待70出现才进入真正背驰危险区；危险区本身不是卖出确认。','背驰|背驰段|确认',1,'原没有创新高限定本向上比较语境，反向新低类比未偷写；不把70新高单条件当已背驰。',figs=[(458,1)])
c(61,'69-70-vs67-68-no-consolidation-div-no-exit-except-subsegment','458-b000','69—70比67—68没有盘整背驰，故70没有走的理由，除非按线段以下级别操作。','盘整背驰|操作级别|卖点',1,'不是否定所有级别70附近都可能卖，保线段以下例外；不借更细卖点替代原操作级别。',exceptions=['原文：除非你是按线段以下级别操作的。'],figs=[(458,1)])
c(61,'71-third-buy66-69-future-expand-or-center-up-requires-no-pan-div','458-b000','71是66—69一分枢三买；其后可中枢级别扩展或中枢上移，而要走后者，从71起上段至少不能出现盘整背驰。','第三类买点|中枢扩展|中枢上移|盘整背驰',1,'三买非保证形成完整上涨趋势；不出现盘背是上移最基本必要要求，非单一充分条件。',figs=[(458,1)])
c(61,'71-weaker69-70-and-from69-weaker65-66-red-area-aid','458-b000','本例71起力度弱于69—70，69起力度又弱于65—66，可用相应MACD所有红柱面积之和辅助判断。','MACD柱波|区间套|盘整背驰',1,'原两比较对象/面积求和保留，不用峰值高度替代或造积分数；MACD为结构辅助非独立心理测量。',figs=[(458,1)])
c(61,'four-nests65-69-71-inner71-locate72','458-b001','72背驰点以四层定位：65起背驰段、其中69起、再其中71起、最后71内部背驰；走势与MACD红箭头辅助最后一层。','区间套|背驰段|背驰|当下',1,'四重是本例实际嵌套而非所有转折必须四层/任意四个箭头；当下可定位是作者主张，本批无逐笔回放成交证明。',figs=[(458,1)])
c(61,'72-sell-quantity-five-or-below-all-larger-capacity-hedge','458-b002','72四重背驰后作者要求卖，区别在数量；5分及以下操作者全卖，因后至少5分震荡，60—69实际为5分枢；更大级别按震荡可容数量对冲。','操作级别|仓位|交易容量|中枢震荡',1,'卖唯一选择为作者本例规则，保级别/数量条件，不变成所有资金清仓；对冲容量无固定百分比或无摩擦成交保证。',conditions=['本课72四重背驰已定位','分别按5分及以下或更大级别操作'],figs=[(458,1)])
c(61,'small-funds-higher-return-same-skill-capacity-author-model','458-b002','作者在相同操作水平下以72卖点说明，小资金可全仓操作而大资金不能，因而小资金利润率更高。','交易容量|利润率|操作熟练程度|仓位',2,'同水平及容量约束是前提，高于/全仓能力为作者模型非所有账户实测收益，也不推小资金应总满仓。')
c(61,'74-second-and-third69-72-not70-73-associativity','458-b003 459-b000','74既为二卖又为69—72一分枢的三卖，不能归70—73枢，因为需满足结合律及结构分组。','第二类卖点|第三类卖点|结合律',1,'两个类别同点不等任何二卖三卖必重合；最近枢须合法分组，不能只挑更靠近三段。',figs=[(458,1)])
c(61,'third-point-atleast-five-subsegments-three-center-four-leave-five-point','459-b000','一个第三类买卖点至少需5段次级别：前三段构成中枢，第四段离开，第五段构成三类点。','第三类买卖点|次级别|结合律|走势中枢',1,'保至少/次级别及前三段先成枢，第四第五仍需完整次级走势和不回枢等既有条件；不是任意五根K或五笔自动三类。',figs=[(458,1)])
c(61,'second-third-coincident-often-force-not-guarantee','459-b000','二三类买卖点同时出现时，作者称后续力度往往值得关注，74后较大下跌为其本例说明。','第二类买卖点|第三类买卖点|动力学',2,'保往往非必然、关注非保证盈利/趋势；本例已发生结果不证明所有重合点同幅度。',figs=[(458,1)])
c(61,'five60-69-key69-4244-third-sell-below-expands-atleast30','459-b001','对60—69五分枢，69的4244关键；若其下出现三卖，则至少扩为30分枢，调整幅度与压力增大。','中枢扩展|第三类卖点|走势中枢',1,'对应5分枢之三卖仍需次级离返结构，非单价低于4244即成立；至少30分与完成状态分开。',figs=[(458,1)])
c(61,'after72-break73-also4244-stand-max-five-else-five-down-or30','459-b001','72起走势要转强须冲破73，其位置也为4244；重新站稳则至多5分枢延伸震荡，否则即使不成5分下跌也会扩30分震荡。','中枢延伸|中枢扩展|下跌|确认',1,'73与69同价但不是同时间点；冲破/站稳不混，未站稳不等已完成5分下跌，两个后果保留。',figs=[(458,1)])
c(61,'jun21-4244-next-4144-mid-close4147-near-not-same','459-b003 460-b000','6月21日作者称早盘补缺口有底背驰定位；次日看4244站稳，否则5分震荡并防三卖；最低4147接近中线半线4144，不破该线仍强。','区间套|确认|经验压力线|中枢震荡',2,'4147与4144不静合，底背驰定位本段未给逐层明细；文字前瞻不据后6/25合并图证必然。',figs=[(459,1)])
c(61,'rhythm-buy-sell-points-capital-efficiency-not-must-sixteen-stocks','460-b001 460-b002','作者强调资金安全和利用率依赖节奏，而节奏依赖买卖点；展示16只股只是说明资金运用，不要求学习者买这些股票。','操作节奏|买卖点|资金管理',1,'小资金反弹100%说法和8只新高/3涨停为作者历史自述强语，不作最低收益或已核绩效，不能推出每人须轮动满仓。')
c(61,'uncertain-understanding-dont-use-especially-too-small-one-mastered-method','460-b007','对理论理解还有疑问就不要据其操作，尤其小级别；若彻底理解其中一方面如同级分解，可仅按已理解部分操作。','操作熟练程度|操作级别|同级别分解',1,'真明白为前提，非背会术语即可精确成交；作者自比数学定理不作为本项目已证正确。')
c(61,'quoted-may22-small-cap-risk-large-buy-no-herd','461-b005','6月22日转引5月22日旧回复，要求任何股票先注意风险、按大级别买点进入，小盘不能乱买或一窝蜂换股。','交易容量|买点|操作级别|追高',1,'保旧答5/22身份和当前转引语境，不能把6/22后文沿用5/22日期；原持股获利大潜力是作者建议，不为当前荐股。')
quote_overrides['461-b006']=passages[pid('461-b006')]['text'].split('如果你在6月13日后',1)[1]
c(61,'jun22-wait-buy-not-chase-big-sell-first-sell-rebuy600569-example','461-b006','6月22日文章要求别在6月13日后追高600569而应等买点；作者以60分顶背驰说明有大卖点先卖后买、注意节奏以降成本。','背驰|操作节奏|卖点|追高',2,'6/13复牌收益/停牌碰530和零成本是回顾自述，本文未独立验证；此源是6/22文章恢复段，不是5/22旧回复，先卖买不证任何价位最终必零成本。')
c(61,'jun22-81-82-pan84-second-microdiv87-not-end-unless85-4131','462-b005','6月22日例中81—82盘背、84二卖，后微枢前后背驰有87转折；但86—87无背驰，转折仅线段下级，尚不能确认线段完，除非重破85的4131。','盘整背驰|第二类卖点|完成|小级别转大级别',1,'微枢背驰与86—87无同层背驰分开，原4131一点保，不将87小转折直接最终分段；图后88/89不倒写当时状态。',figs=[(463,1)])
c(61,'jun22-five75-84-lower4188-return-fail-warn-third-sell','462-b006','75—84五分枢下边4188，后走势若不能重站其上，要防5分三卖。','第三类卖点|中枢回拉作用|走势中枢',1,'后回抽仍须合格次级结构；这是当时将来条件，不是6/22已确认所有后续路径。',figs=[(463,2)])
c(61,'jun22-46-87-thirty-center4067-4192-third-leg-unfinished','462-b006','作者称46—87已构成30分中枢[4067,4192]，同时说短线第三段是否完成尚待看；后按该枢震荡直到30分三类点。','走势中枢|完成|中枢震荡|第三类买卖点',1,'保已构成与第三段未确认的原张力，未替作者改成已全部完成或仅候选；4067粗数与原图4067.85不静合，须联读完整三次级定义。',figs=[(463,2)],ambiguity='definition_boundary')
c(61,'jun22-quarter-long-wick-pressure4144-close-ideal-three-month-claim','462-b007','作者称季线若长上影将压7—9月，次周若收4144半线上为多方胜利，并自评该线至少管3个月的断言成立。','周期K线图|经验压力线|走势预测',2,'这是当时前瞻及自评，不能用6月22日就证明未来三个月已发生；未外证统计或季线因果。')
c(61,'jun23-hand-draw-figure-one-equivalent-segment-second-distinctions','464-b002','6月23日作者说明手画图一各形态等价、均一线段，图二用于区分易混情形。','线段|走势分解|小级别转大级别',2,'实际查看两图的等/不等号和小转大字样；手绘无数值坐标，不造通用阈值或据此代后62/67严格特征序列，汇编图原发一致性未核。',figs=[(464,1),(464,2)])
c(61,'jun26-published-prior-session-return4131-under4188-third-sell','464-b005','6月26日凌晨解盘以反抽最高4131未回4188说明此前5分三卖警告兑现，后续下跌为其历史案例。','第三类卖点|反抽|当下',2,'发布时间为6/26 00:49，文内今天指所述前一交易日，不重写原日期；作者事后总结不作为逐笔成交或预测成功率证明。',figs=[(465,1)])
c(61,'jun26-4025-new-one-lower3982-return-new-five-else-line-down','464-b005','作者以4025为新1分枢下边，未重站仍会变坏；若回3982上至少演化新5分枢，否则线段下移直至新1分枢，可用当下背驰判断而无需预测价位。','中枢新生|中枢扩展|背驰|确认',1,'4025与更低3982不同技术层，不因价格更低就混成一个中枢上下界；至少/若/直到和背驰条件保，未补最终价。',figs=[(465,1)])
c(61,'after-fall-watch-rebuy-but-new-buy-still-needed','464-b006 465-b000','作者反对卖点不卖和买点出现不买两种僵化做法；跌多后应密切关注回补时机，仍按买点行动。','买点|卖点|操作节奏|等待',1,'跌多是关注而非无点抄底，先卖后买不等永远只卖不回；日MACD麻烦是作者经验判断非独立结构充分条件。')
c(61,'jun27-midnight-new-one-after-segment-div-old3982-4025-stay','465-b005','6月27日凌晨作者称线段下移至背驰后形成新1分枢，3982和4025仍是关键位置。','中枢新生|背驰|确认',2,'仍以发布时间与所述前交易日区分，不据后至6/29图证明前日已知路径；新枢完整区间此段未给。')
c(61,'jun27-break3982-retest4025-watch4131-before-third-buy-oscillation','466-b003','6月27日开盘破3982、13:40回调至4025；后看4025能否站稳及4131阻力，新5分枢三买出现前暂按震荡。','中枢震荡|第三类买点|确认',1,'历史观察和次日前瞻分开，图含6/29未来K不能证6/27预测；不把摸到4131当有效突破。',figs=[(466,1)])
c(61,'jun27-4131-effective-break-five-day-stand-and-quarter4144-goal','466-b003 466-b004','4131未有效突破前，作者以站稳5日线为随后三天关键；季度收盘4144半线上只是最理想目标，尚须尽力。','均线系统|经验压力线|确认',2,'最理想不是保证完成，季度余两天/随后三天按原6/27时点，非当前市场指南。')
c(61,'jun28-requote-jun4-monthly-five-vs4144-compress-july-aug-direction','467-b002','6月28日作者转引6月4日3600附近原“5月均线”与4144半线区间，认为7月前者上移压缩空间，最迟8月初选方向。','均线系统|空间压缩|走势预测',2,'3600为6/4引用时点不是6/28实算均线，原5月不静改5日；沪4144和深13700分开，最迟日期为作者预测非已证规律。')
c(61,'jun28-should-sell-buy-not-must-low-skill-control-position','468-b000','震荡中作者要求该卖时卖，但买不一定，技术有问题者可控制仓位，差价操作需学习练习。','操作节奏|仓位|操作熟练程度',1,'买不一定明确保留，不因先卖后买节奏强迫立刻买回；不是保证震荡比任何行情更容易赚钱。')
c(61,'jun28-100-top102-second103-unfinished-literal102-completion-conflict','468-b001','6月28日作者指出100顶背驰、102二卖，103收盘未走完；紧接原文却说“要102走完”须线段内底背驰，编号矛盾仍待核。','背驰|第二类卖点|完成|线段',1,'两个编号原样保，不擅改102为103；最低箭头未站稳为最弱并至少等1分以上背驰才参与，3919在后日文字另明确。',figs=[(467,1)],ambiguity='source_numbering_conflict')
c(61,'4022-precision-two-decimal-no-break-truncate-overlap-round-not','468-b004 469-b000','红箭头4022.69、绿4022.42按两位小数未破坏原线段；直接取整同为4022可作重合新段，四舍五入成4023/4022则不能如此分段。','价格精度|线段|线段破坏|重叠',1,'三种标准分别保，不能说凡整数都相同；直接取整明说在6/29，不倒写59当时未指定的算法。',conditions=['6/29早对前日图的4022.69/4022.42例','全图统一选用同一精度规则'],figs=[(468,1)])
c(61,'jun29-henceforth-direct-truncation-choice-not-universal-theorem','469-b002','为照顾习惯并简化，作者决定此后统一以直接取整确认线段，图上分段随之改用所示方案。','价格精度|线段|数据源一致性',1,'明确以后时效及教学选择，不是理论必须取整；后64软件差异/可自行预设精度的条件仍保，不能按日期自动覆盖所有读者。',figs=[(468,1)])
c(61,'new-segment-break-old-literal-down-laterhigh-below-priorlow','469-b001','作者说新线段重要标准是破坏老段结构，并以跌段“后高点一定低于前低点”作原文例述。','线段破坏|线段|走势分解',1,'原低于不擅改高于，所举为跌段排列与破坏旧段的适用对象未展开，不能由此单句造通用终结算法或代后65/67精确定义。',ambiguity='definition_boundary')
c(61,'jun29-3919-rebound-block-prediction-function-but-action-first','469-b004','6月29日作者称反弹被前箭头3919压制，认为理论有预测功能，但仍以当下操作为关键。','走势预测|当下|确认',2,'作者事后自评不作本项目外部精度统计；与60不预测非不可预测联读，不伪造所有压力点从未偏差。')
c(61,'105-div-no-clear-one-center-intraday-cost-noT0-skill-exceptions','469-b005','105背驰因前无明确1分枢一般只具盘中意义；费用高又非T+0，生手只能较大级别，过小操作估计限权证或特强股，技术好者除外。','背驰|交易成本|T+0|操作熟练程度|权证',1,'保一般/估计/熟练例外和无明确1分枢，不把任意105无条件好买点，原非T+0不用于静改56原T+0，亦非当前交易法规。',figs=[(469,1)])
c(61,'jun29-quarter500wick-july-halfline4159-beforestand-big-shake','469-b006 470-b000','6月29日作者称季线500点上影将压7—9月，下月半线将上移4159，站稳前难有像样行情而以大震荡为主。','经验压力线|周期K线图|走势预测',2,'跨页接6月4日引述完整，4159是下月预测不把旧4144改掉；500点/压制关系为作者陈述未独立统计。')
c(61,'monthly-five-hold-triangle-else-platform-retest-jun5-not-V-view','470-b001','作者判断下月5月均线不破仍可能三角形，否则平台型并再试6月5日低点；称本轮反弹不会成V型、最强三角形。','均线系统|三角形整理|平台式调整|走势预测',2,'保原5月、可能与否则及当时预测/追述，不把本图判断泛为所有大跌都无V反转；未独立验证其6/5旧说。')
c(61,'jun29-atleast-one-div-entry-res3919-fiveweek-unskilled-can-stay-out','470-b002','作者以至少1分以上背驰为较好介入时机，压力3919及5周线；技术差或不善震荡者，在重站5周线前可不参与，熟练者可例外活动。','操作级别|背驰|均线系统|操作熟练程度',1,'至少1分以上原范围保，不降为任意线段背驰；可不参与非强制买点，5月均线趋势条件与5周执行条件不混。')
c(61,'oscillation-fund-matched-specific-stock-larger-buy-and-sell','470-b003','震荡操作须等适合自身资金、具体个股的较大买点，到较大卖点应卖，并通过练习形成感觉。','交易容量|买卖点|操作节奏|操作熟练程度',1,'资金/个股/级别和等待条件保，较大不是固定30分钟；不能用指数买卖点替代个股或把买卖必降成本作实证。')

note('457-b002 457-b005 459-b002','teaching_rhetoric','作者学习和理论自评、万有引力/定理类比及贬词上下文已读。','不把个人攻击、人人学会假命题或自比自然定律当本项目技术/完备性证明。')
note('460-b004 460-b005 460-b006','learning_rhetoric','出差安排、拒依先知荐股及要求自己判断的教育语境。','从无荐股者真正成功/比费马定理等绝对说法未外证，不化成所有人的分类事实。')
note('461-b000 461-b001 461-b002 461-b003 462-b000 462-b001 462-b002 462-b003 462-b004','historical_holdings_self_report','完整读作者东北股9/26/38、16只列表、原入价四舍五入、0成本及建仓时间自述，6/22文章身份已恢复。','无账户成交证据不作任何价位必0成本、全仓收益保证或所有人须买16只；历史列表原价保，不当前荐股。')
note('461-b004','quote_open_marker','原中文开引号接5/22署名与旧答，闭引号在461-b005末。','不把开引号独立当技术命题；旧答后6段已恢复6/22来源。')
note('463-b000 464-b001 464-b003 464-b004 465-b001 465-b003 465-b004 466-b005 467-b000 468-b002 468-b003 470-b004','personal_or_historical_context','旅行/饮酒/音乐/城市印象/个人持仓控盘和PE海外上市自述均完整读过，保原文作语境。','原话不作个人行程/上市法规/绩效外部核实，不将股票因本人看盘兴奋等主观描述升为技术因果。')
note('466-b000 466-b001 466-b004','historical_commentary_context','延续关注回补/季月收盘与4144目标，保作者时间和过去文字引用。','中线政策消化为当时解释，若已有新命题仅取相关片段，其余背景不作业绩证明。')

issue('recursive-hypothesis-four-nests-and-no-newhigh-boundaries','457-b006 457-b007 458-b000 458-b001','假设背驰与已确认、强于前段否定/69未新高/70无盘背/71必要不盘背，四重套例不能省比较对象。','无逐笔当下回放/独立盲测；四重不是所有定位必须次数，MACD只辅助。',True)
issue('74-associativity-atleast-five-subsegments-and-4244-structure','458-b003 459-b000 459-b001','74对69—72而非70—73，至少5段次级/前三枢四离五点；4244是不同时间69/73同价且需结构。','同价不等同点，不把任意五笔或单价触4244当三卖；二三重合往往非必然大趋势。',True)
issue('operation-grade-sell-quantity-capacity-and-return-strong-claims','457-b004 458-b002 460-b001 461-b000 470-b003','72必卖及5分以下全出/大级按容量、1分与月线、100%和任意价0成本都是有条件或作者强语。','保60快速空间/大级破坏例外，不能逃避换级；无账户实证不称收益保证。',True)
issue('nested-may22-quote-restored-jun22-and-eleven-figure-provenance','461-b004-s01 461-b005 461-b006 462-b000','5/22旧答闭引后六段恢复6/22文章，2日期空格；11图7未核4后加，原图/重绘不同极值/局部编号不静合。','原发未核、含未来K不证前瞻，6/21课头只有日期不补时分。',False)
issue('thirty-center-third-leg-unfinished-103-vs102-and-down-high-low-literal','462-b006 468-b001 469-b001','30分枢已构成但第三段是否完成、103未完却要102完、跌段后高低于前低均保原字张力。','待核不偷偷修编号/不等号，不用后图或后课定义回改原文；完整子级定义需并列。',True)
issue('precision4022-truncation-vs-rounding-henceforth-scope','468-b004 469-b000 469-b002','4022.69/4022.42两位无破、截整同4022可重、四舍五入4023/4022不可，作者此后选截整。','精度预先统一；明确选择时效不自动替代59未指定算法或后64允许自选，未核软件数据来源差。',True)
issue('historical-key-levels-midnight-session-monthly-weekly-and105-minimum','464-b005 465-b005 466-b003 467-b002 469-b005 469-b006 470-b001 470-b002','凌晨发布时间/所述前交易日、3982/4025/4131/3919与4144/次月4159各层时点，5月/5周和105最低级别限制分开。','原5月不修5日、至少1分以上保；无法据当时强语或后加图外证季度预测/成交。',True)

relations={
 'provisional-divergence-from65-invalid-if-stronger-else-recurse':[('区间套','确认','requires')],
 '71-third-buy66-69-future-expand-or-center-up-requires-no-pan-div':[('中枢上移','盘整背驰','qualifies')],
 'four-nests65-69-71-inner71-locate72':[('区间套','背驰段','requires')],
 '72-sell-quantity-five-or-below-all-larger-capacity-hedge':[('仓位','交易容量','qualifies')],
 '74-second-and-third69-72-not70-73-associativity':[('第三类卖点','结合律','requires')],
 'third-point-atleast-five-subsegments-three-center-four-leave-five-point':[('第三类买卖点','次级别','requires'),('第三类买卖点','结合律','requires')],
 'rhythm-buy-sell-points-capital-efficiency-not-must-sixteen-stocks':[('资金管理','操作节奏','requires'),('操作节奏','买卖点','requires')],
 'jun22-46-87-thirty-center4067-4192-third-leg-unfinished':[('走势中枢','完成','qualifies')],
 'jun28-should-sell-buy-not-must-low-skill-control-position':[('仓位','操作熟练程度','qualifies')],
 '4022-precision-two-decimal-no-break-truncate-overlap-round-not':[('线段破坏','价格精度','qualifies')],
 '105-div-no-clear-one-center-intraday-cost-noT0-skill-exceptions':[('背驰','交易成本','qualifies')],
 'oscillation-fund-matched-specific-stock-larger-buy-and-sell':[('买卖点','交易容量','qualifies')],
}
for r in rows:r['relations']=[dict(source=a,target=b,type=t) for a,b,t in relations.get(r['id'].split('upper-l061-c-stage-')[1],[])]


by_passage=defaultdict(list)
for r in rows:
 for e in r['evidence']:by_passage[e['passage_id']].append(r)
for item in pending:
 item['lesson_numbers']=[61]
 if item['id'].endswith('nested-may22-quote-restored-jun22-and-eleven-figure-provenance'):item['figure_ids']=[f['id'] for f in figures]
ledger=[]
for id,p in passages.items():
 linked,decision=by_passage[id],notes.get(id)
 if linked:
  result,reading='new_claim','；'.join(r['text'] for r in linked);atomic=[dict(claim_id=r['id'],conditions=r['conditions'],exceptions=r['exceptions']) for r in linked];inverse='；'.join(r['review_note'] for r in linked)
 elif decision:result,reading,atomic,inverse=decision['category'],decision['reading'],[],decision['inverse']
 elif p['role']=='reader':result,reading,atomic,inverse='reader_context','读者Abc请求5/30分钟图示范，保问题身份。',[],'读者对图/级别/线段困惑为问题；作者完整跨页答不认可图周期等于走势级别。'
 elif p['text'].startswith('教你炒股票') or p['text'] in ('缠中说禅回复：',) or re.fullmatch(r'.*200[5678]-\d{1,2}-\d{1,2}.*',p['text']) and (len(p['text'])<75 or p['text'].startswith('缠中说禅')):result,reading,atomic,inverse='source_header','课/独立文章/作者解盘/答疑/时间头定位已核。',[],'只作来源锚点，不独立证明技术命题。'
 else:raise AssertionError(('unaccounted paragraph',id,p['text']))
 if linked and decision:reading+='；其余语境：'+decision['reading'];inverse+='；'+decision['inverse']
 ledger.append(dict(passage_id=id,lesson_number=61,document_id=DOC,pdf_page=p['pdf_page'],role=p['role'],speaker=p['speaker'],published_at=p['published_at'],source_text_sha256=hashlib.sha256(p['text'].encode()).hexdigest(),result=result,claim_ids=[r['id'] for r in linked],related_existing_claim_ids=retained[id],existing_evidence_not_mutated=True,pending_issue_ids=[x['id'] for x in pending if id in x['passage_ids']],reviewer=REVIEWER,rounds={'1_read_and_scope':reading,'2_atomic_conditions':atomic,'3_normalization':{'concept_labels':sorted({x for r in linked for x in r['concepts']}),'related_existing_claim_ids':retained[id],'note':'区间套假设/否定/递归与65-69-71-内部四重例，74结合律至少五次级分组和4244结构条件，72卖数量/原级别及资金容量，5/22闭引后六段6/22来源修复，103与102/跌段后高低于原字、4022精度三算法及时效、凌晨时点/5月与5周分层。'},'4_reverse_check':inverse}))
for f in figures:
 f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=f['note'],figure_source_review='实际查看457至470十四页11整图，7原发未核4后加；5/22引用原闭引号与6/22恢复，464手绘等不等/小转大，原87/后89、3819.03/.05/重绘3818.85及105原3780.84/重绘3779.81分存，102/103不静改。',linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger)==83 and len(figures)==11
for suffix,data in [('reviewed.jsonl',rows),('coverage.jsonl',ledger),('pending.jsonl',pending),('figures.jsonl',figures)]:
 (OUT/f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x,ensure_ascii=False,separators=(',',':')) for x in data)+'\n',encoding='utf-8')
summary=dict(stage='C/E',schema_version=metadata['schema_version'],graph_version=metadata['graph_version'],lessons=[61],document_id=DOC,reviewer=REVIEWER,passages_read=len(ledger),claims=len(rows),evidence=sum(len(r['evidence']) for r in rows),importance_counts=dict(Counter(r['importance_level'] for r in rows)),new_concepts=sorted({x for r in rows for x in r['concepts']}-set(concepts)),whole_lesson_semantic_read_complete=True,technical_extraction_complete=False,four_round_review=True,independent_review_claimed=False,visual_pdf_pages=list(range(457,471)),figure_objects_viewed=11,figure_origin_counts=dict(Counter(f['origin_status'] for f in figures)),pending=[x['id'] for x in pending],source_passages_snapshot_sha256=SOURCE_SHA,retained_source_links_in_ledger_only=True,database_mode='ro',formal_import=False,delivery_scope='shared_knowledge_base_only',acceptance='61课83段14页11整图同模型四轮，8来源日期修正和7未核4后加图；四重套/结合律五次级/仓位容量/中枢完成张力/精度三算法与原字编号、历史层级时点分存，待预检。')
(OUT/f'{BASE}.summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
db.close();sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(summary,ensure_ascii=False))


