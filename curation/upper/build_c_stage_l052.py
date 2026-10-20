"""Materialize the main agent's four-pass reading of lesson52.

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
BASE = 'c_stage_l052'
REVIEWER = 'Codex 主代理 / 阶段C上册52课同模型四轮复核'
SOURCE_SHA = '4b5a1acd34f5bd71ffeb3c6e318e4bd5ac0c902f335dd0ea3c5d486e0663e6c2'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-052' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 150
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 382 AND 396 ORDER BY pdf_page,id', (DOC,))]
assert len(figures) == 10
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
    pending.append({'id': 'upper-l052-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})




















quote_overrides['385-b003']=passages[pid('385-b003')]['text'].split('至于203',1)[0]
quote_overrides['388-b005']=passages[pid('388-b005')]['text'].split('而最理想的方式',1)[0]
quote_overrides['389-b000']='当然，震荡的区间可以加大，并不是说一定要限制在目前的区间中。'
quote_overrides['390-b000']=passages[pid('390-b000')]['text'].split('个股方面',1)[0]
quote_overrides['392-b003']=passages[pid('392-b003')]['text'].split('如果说消息',1)[0]
c(52,'prediction-includes-observers-not-independent-clockwork','382-b008 382-b009','作者说无须预测不等绝对不可预测：观察、预测和参与者本身构成走势，反对把市场视为不受观察参与干扰的机械系统。','走势预测|市场合力|当下|市场心理',1,'这是作者市场认识论，量子力学只作类比而非本项目证明金融等同物理测量；不将其改为精确预知任意未来点价。')
c(52,'basic-patterns-predictable-price-formed-in-present-author-view','382-b009','作者把唯一绝对可预测对象限定为市场基本形态，点位为形态当下演化结果，以不患与患解释两者关系。','走势预测|当下|走势类型|价格区间',1,'绝对可预测是作者模式层面主张，非点位/时间预报已验证；不患/患为其哲学术语，不建立自然科学证明或固定收益承诺。',ambiguity='author_absolute_pattern_predictability_not_exact_future_price_forecast')
c(52,'training-guide-independent-present-fixed-operation-level','382-b010 383-b000','作者称自己是训练者、引导者，操作当下须由操作者把握，事先确立的操作级别是另一不患前提。','操作级别|操作熟练程度|当下|操作策略',1,'固定操作级别先于具体当下，不因亏损临时随意放大；原科学死无葬身之地是修辞，不当项目反科学结论。')
c(52,'multi-level-isomorphic-patterns-mental-structure-religious-analogy','383-b001 383-b003','作者认为各操作级别基本模式同构，根源为参与者贪嗔痴疑慢的相似结构，并借学佛/轮回说明其理论与自我磨练关系。','自同构性结构|操作级别|市场心理|贪嗔痴疑慢',2,'作者哲学/宗教解释而非心理学实测或对其他世界股票市场的事实断言；公开理论不会影响作者操作为自述，未证普适盈利。',ambiguity='author_philosophical_religious_explanation_not_scientific_validation')
c(52,'literal-divergence-level-not-smaller-than-turn-level-unresolved','383-b002','第52课原句写背驰的级别一定不小于转折的级别；本条保留不小于原字，其与小级别转大及同段30分例的作用域关系待核。','背驰|操作级别|趋势转折|小级别转大级别',1,'已回看PDF383原页确为不小于，不静修为不大于；44课原文称小级转折引发大级转折、52同段又举30分背驰后下跌/更大盘整，不能无说明合并成唯一无争议总定理；本条是原句及张力记录，不修改旧命题。',ambiguity='source_not_smaller_inequality_scope_tension_with_small_to_large')
c(52,'thirty-top-divergence-exit-own-down-or-above-consolidation-author','383-b002','以30分操作为例，作者要求30分顶背驰时退出，因后必有30分下跌或扩成30分钟级别以上的盘整；前文亦称不必参与这两类。','背驰|操作级别|下跌|盘整|操作策略',1,'源文绝对保证是作者该同级例主张，非所有小级背驰令大级操作者全清；原30分钟级别以上的盘整不静改为严格大于；与49本级盘整可参与的范围关系仍待核，未把原不小于量词静合、也不认证实盘无误判/成交风险。',ambiguity='author_same_level_example_guarantee_not_execution_proof')
c(52,'may18-balance-4040-rough-reference-not-most-precise','383-b004','5月18日作者判周末消息压力下的平衡市，4040仍站不住；称该数只是给不懂中枢者参考，正常分析可更精确。','平衡市|价格区间|确认|市场心理',2,'历史判读/作者因果解释，4040不是所有场景绝对精确枢边或保证不新高；周末消息未外核。')
c(52,'may18-five-ten-day-kiss-direction-larger-range-forecast','383-b005','作者从5日线对10线之吻判断下周初震荡须选方向，最终导致区间加大和更大级别震荡。','均线系统|唇吻|市场震荡|走势预测',2,'10线依本段均线语境而非自设参数；一定为作者当时预测未独立实证，不将均线吻单条件推广为所有市场必升级中枢。')
c(52,'shenzhen-half-line-13700-relative-strength-two-markets-view','384-b000','作者把深圳相对强解释为其1/2线在13700尚有空间，认为后续或深带沪上、或相反，沪深背离不能持续。','1429点历史压力线|指数走势背离|宏观市场判断|走势预测',2,'13700是深圳另一个历史模型线，未给本课基点/速率完整推导，不把上海1429基点套深圳；不认证两市场任何背离都固定时内消失。')
c(52,'may18-1326-compare-two-down-legs-one-MACD-nesting','384-b001','作者定位5月18日13:26，比较5月17日14:30至18日10:00与18日10:58至13:26两段中枢震荡力度，用1分MACD辅助，再按后一段细部类似区间套定位。','中枢震荡|指标对比|MACD|区间套|操作级别',1,'保跨日/同日两组时点，1分观察图不自动定义1分背驰；作者称当下可完成不等实际每人可成交最底，图当日可得但原发未核。',figs=[(384,1)])
c(52,'near-opposite-points-use-large-unless-skilled-exit-room','384-b006 385-b000','作者否认同一点同时为所问买卖点，但承认大级卖买点与小级相反点可很接近；原则看大级操作，除非有经验精度确认小级有退出空间。','买卖点|操作级别|操作熟练程度|交易条件',1,'不可能与很接近有别，原问题跨级表述不能删；退出空间条件不等所有小级反向点都不可做或总应改原定操作级别。')
c(52,'novice-coarser-view-strong-large-up-sell-to-rebuy','385-b003','不熟者可放大观察/操作级别，不必1分没背驰就急动，可先忽略5日未破调整；大级强升股卖出应考虑买回。','操作级别|均线系统|中枢上移|操作熟练程度|买卖点',1,'特别限大级强升/不熟者，不能推广已出原级三卖仍不加条件强制回补；后300/500涨幅自述不当方法实绩，保45趋势限制。')
c(52,'match-intended-level-to-volatility-tolerance','385-b006','看好大级图形就按大级思维；只能忍受小级波动则按小级操作，不混大小级别。','操作级别|市场风险|市场心理|操作策略',1,'选择级别和承受力相配，不能以买前大级看好、买后小波恐惧随意拼接来证明同一策略。')
c(52,'individual-index-correlation-by-buy-sell-structure','385-b009','个股看自身走势；作者认为若跟大盘，会表现与指数一致买卖点结构，可据此判断相关程度，指数震荡时有股反会大涨。','市场分力|买卖点|操作策略|技术分析',1,'作者结构关联判断而非统计相关系数/所有个股行情核验，416/607为历史例，不把指数信号硬搬个股。')
c(52,'600601-short-center-around-11-8-case','385-b012','作者对600601短线答为围绕11.8的中枢震荡。','中枢震荡|价格区间|操作级别',3,'价位依紧前读者问题指代而非600166，未给上下沿/明确分钟级别，11.8非当前价格或通用买点。')
c(52,'precise-five-completion-needs-one-chart-only-five-enlarge-base','386-b001','作者说精确判断5分走势完成需1分图，5分走势未必有5分背驰，小转大只看5分难辨；只有5分图则放大操作级别、把5分当最小级。','操作级别|周期K线图|最低级别|小级别转大级别|完成',1,'本条精确形态完成识别，与49/50可借大周期MACD比较小信号的辅助场景分开，不静说二者完全等价；读者6至9段级别问题未被逐项肯定。')
c(52,'may21-fourth-thirty-bar-4050-unilateral-interval-branches','388-b004','5月21日作者说先冲4040回调、第四根30分K向上破，下午确认4050上下单边区间；次日未破继续拓展，否则回原中枢延伸震荡。','单边区间|每日走势分类|中枢延伸|价格区间|突破',1,'该日30分K辅助分类不等严格30分递归中枢，4050上下是历史区间参考不是全市场通用位；后5/23/5/29K不认证先验预测。',figs=[(389,1),(389,2)])
c(52,'may21-pressure-patterns-forming-forces-no-absolute-controller','388-b005 389-b000','作者说1/2线三种大震荡形式仍形成选择中，是市场各方合力结果，无管理层或参与者一方有绝对力量；震荡区间可加大。','1429点历史压力线|市场合力|市场震荡|走势预测',1,'作者对合力和剧本的历史观点，不认证本人强制市场共识能力，三模式尚在选不是当前已经确定最终级别。')
c(52,'skill-fallback-five-ten-week-and-five-day-kiss','389-b001 390-b000','技术不足者作者建议看5周甚至10周均线作心理缓冲，称10周自去年8月未破；短线不明白可看5日，关注与10日吻是否再次女上位。','均线系统|操作熟练程度|市场心理|均线体位',2,'历史10周未破未外核，长短均线依既定级别分开，前45趋势限制继续；后医药/铜矿/故意亏损等个股暗示未作本条技术事实。')
c(52,'technical-skill-not-news-dependence','390-b001 392-b003','作者要求别养成听消息习惯，最终仍需技术过关，认为有技术可操作不同股票。','操作熟练程度|技术分析|操作策略',1,'原最大消息集散地/逃避监管自述未外核，不认证所暗示内幕真实或以消息替代级别买点；390尾5/22时间归后文。')
c(52,'may22-4129-first-cross-does-not-exclude-first-top-scenario','390-b002 390-b003','5月22日作者说早冲4129的1/2线后有小多头陷阱、回试缺口再拉回；即使首次越过该线，也不能绝对否定第一种大顶模式。','1429点历史压力线|多头陷阱|缺口|走势预测|确认',1,'首次突破过不等有效突破/确认，仍保51三路径，历史判读未外核；原5/22时标已独立修正，不用后5/29大跌证明预测。',figs=[(389,1),(389,2)])
c(52,'may22-gap-line-new-small-center-third-point-observe','390-b002 390-b003','作者要求观察压力线与缺口之间、新成小中枢的震荡和三买卖点选择，不预猜方向；技术差可5/10日线，技术好针对个股短背驰。','中枢震荡|第三类买卖点|均线系统|操作熟练程度|操作级别',1,'新枢开始形成不等完整结束；每股自身走势/能力条件不可删，均线简法不承诺亏损不出现。')
c(52,'may21-fast-market-channel-no-exact-low-guarantee','390-b008','作者让用5分比较该次震荡弱于上次，并承认行情太快、准备不足或通道慢，基本买不到精确位置，做不到不必苛求。','指标对比|交易通道|交易条件|操作熟练程度',1,'理论分析与实际成交明确分开，观察5分非判点必5分；未把保证分析变最底价成交，后还有机会不等任何回补必同价。',figs=[(391,1),(391,2)])
c(52,'may21-1040-second-buy-first-retest-zero-on-one-MACD','390-b008','作者举5月21日10:40二买，1分MACD典型冲0轴后第一次回抽0轴，作为错过快速低点后仍可另选机会的例。','第二类买点|MACD|指标对比|操作级别|交易通道',1,'此例1分观察图不单独定义所有二买，须结构与级别联查；原10:40按原文，不以后K证明当时所有人精确可买。',figs=[(391,1),(391,2)])
c(52,'same-level-decomposition-associativity-standard-high-low-joints','391-b002','作者说通过结合律可将所问同级分解归成标准形式，使相邻连接点都是高低点。','同级别分解|结合律|高低点|走势分解',1,'可通过结合律归标准不等任何未调整原分解的每个接点自动为整体最高低，紧后九段收敛质疑有另答，不认可任意重组无条件等价。')
c(52,'extension-first-three-range-later-oscillation-five-thirty-decomposition','392-b001','作者答延伸只看前三段区间，后面都是震荡；从5分和30分角度分解得不同中枢结果正常、原则相同。','中枢延伸|中枢震荡|走势分解|操作级别|结合律',1,'原问题九段5分扩张/日线和三角收敛为读者假设，作者未逐项补每组三段最终高低；前三段区间与整个走势类型波动范围不能混一。')
c(52,'small-cap-examples-not-herding-larger-buy-first','392-b002 393-b005','作者说举例股票有小盘、公开易乱，任何股票先注意风险按大级买点，小盘尤不能追高；已有获利且有潜力股可减少乱换风险，大盘股也不必追。','交易容量|买点|追高|市场风险|操作策略',1,'大小盘仍须具体买点，既有潜力为作者判断不证所有长期持股安全；不破解暗语/推荐实际公司，洗盘意图未外核。')
c(52,'doubling-zero-cost-preference-not-price-top','393-b002','作者说自己喜欢在翻倍位置降成本0、调出资金做其他事，并不表示翻倍就是顶部；该股自述进入0成本增筹码阶段。','零成本持仓|成本|资金管理|持股',2,'13元/翻倍为特定历史自述未核账户与净额，未推所有股票翻倍必洗/必卖；原文不答何时开涨停、不是保证0成本经济风险全无。')
c(52,'third-points-both-leave-retest-sublevel-one-child-center-not-safe','393-b010','作者明确离开和回试都必须次级别，单在原中枢上有一个次级中枢不能绝对保证安全，跳空后岛型反转可为例。','第三类买卖点|次级别|走势中枢|岛型反转|市场风险',1,'次级走势类型不等只数次级中枢个数，未认可读者1个/2个中枢争论作为完整定义；岛型反转仅风险类比，未给每种岛反结构/参数。')
c(52,'third-buy-larger-oscillation-close-to-first-sell-size-and-exit-room','393-b010','三买后可转更大震荡，与一卖位置可能很近；作者建议选较大级别留回旋，熟练者可当下识别转大即离，只取继续中枢上移以提高资金效率。','第三类买点|第一类卖点|中枢震荡|操作级别|交易条件|操作熟练程度',1,'源文说够级别即使转大也有利润空间是作者强语，非通道/费用/滑点全部保证；大小级相反点接近而非原题同一点皆买卖的混同，不把三买必胜当结论。',ambiguity='author_larger_level_exit_room_claim_not_execution_or_profit_proof')
c(52,'leaving-child-center-can-be-within-parent-context-affirmation','393-b013 394-b002','作者对离开段的次级中枢可在原中枢内答当然可以、且多数如此，继而解释中枢不等走势全部，上方价格离开也算离开。','第三类买卖点|次级别|走势中枢|波动区间',1,'393-b013指代紧前393-b012读者问题，仅明确离开段子枢可在内；回试条件须按次级走势整体，不把子枢/整段波动/价格端点混同，短答不是读者全部表述无条件背书。')
c(52,'price-outside-center-leaves-usual-return-third-point-not-pulled-back','394-b002','围绕中枢震荡时，价格不在中枢里就是离开、通常又被抽回；三买卖的重要性是离开后回试抽不回原枢。','中枢震荡|第三类买卖点|中枢回拉作用|走势中枢',1,'抽不回限定义中的次级回试，不等之后永远绝不回原枢或三买后不能转大；不能由任意瞬时离开直接确认完整次级走势/三点。')
c(52,'600216-not-may18-1000-thirty-third-buy-use-five-subtypes','394-b009','作者否认600216的5月18日10:00为30分三买，要求先找离开次级再回试次级；30分次级是5分，至少由三段1分走势类型构成，要到5分图找精确位置。','第三类买点|次级别|操作级别|走势类型|确认',1,'该股/时点依394-b007读者原问，作者不是否定所有30分三买；至少3段1分类型非3K/3笔，30分图难精确定位不等观察图自动定操作级别。',figs=[(394,1)])
c(52,'600216-may17-1455-author-yes-to-reader-two-legs','395-b001','作者以对认可紧前读者的600216问法：5月16日10:20至17日10:10为离开次级，17日10:10至14:55为回试，14:55为30分三买。','第三类买点|次级别|确认|操作级别',1,'作者原话仅对，详细时刻来自紧前读者volume_1-a53e99c37ca5-p0395-b000（续394-b010），这是明确指代认可而非把读者改写为作者长引；证据读取上下文保留读者身份，未说5/18 10:00正确，图当时可得原发未核。',figs=[(395,1)],ambiguity='author_one_word_affirmation_requires_adjacent_reader_context')
c(52,'B-stock-currency-risk-historical-conditional-view','395-b009','作者说B股收益可能不够美元贬值抵消；已有美元又不想换人民币者可考虑，并判断当时需震荡但行情未完。','跨市场交易价值|市场风险|交易条件|走势预测',3,'固定2007语境及作者汇率/行情观点，未核现今B股币种规则或给当前建议；底部上来/已有美元条件不等保证净收益。')
c(52,'larger-divergence-needs-longer-digestion-stock-cases-author','396-b000','作者以578翻倍、343破历史高后15上下整理、802的60分顶背驰解释调整，认为大级背驰通常需较长时间消化。','背驰|操作级别|调整|时间之窗',2,'历史价格和北京股中线没问题为作者未核观点，不把翻倍或15元推广成所有股阈值/当前安全承诺；通常较长无固定天数。')
c(52,'all-points-root-first-first-root-divergence-not-same-level-collapse','396-b003','作者说所有买卖点归根结底都是一类，一类归根结底与背驰相关。','买卖点|第一类买卖点|背驰|操作级别',1,'归根结底的递归解释不将所有同级二三买静改成同级一买/一卖同一标签，仍须各级前后关系和完整定义，不从此省掉三买回试。')
c(52,'second-buy-thirty-first-five-up-five-retest-no-low-second-leg','396-b007','作者以30分一买后一个5分次级上去、再5分回试不破低点说明二买；通过结合次级分解只能在第二段。','第二类买点|第一类买点|次级别|结合律|走势类型',1,'第二段指此例次级分解中的回试，不凭读者a+(A1+A2+A3)+b强填A1或A3；5分完整走势非单K，未给不破相等/完成所有数值细则。')
c(52,'forget-rebuy-small-level-full-in-out-use-larger-view-or-few-stocks','396-b010','对小级背驰全进全出却忘回补、错过主升者，作者建议只看大级图，或反复操作少数几只。','操作级别|操作熟练程度|操作节奏|交易容量',1,'针对该读者行为纠偏，不认可其每次小级背驰都应全清，也不规定所有账户恒定持股数或无三卖条件强买回。')

note('384-b002','historical-personal-news-stock-boast-context','作者华生婚讯/文章分量和股票涨幅排行、周末日程自述。','未核人事/绩效，不拿人物新闻证技术理论，不作当前新闻。')
note('385-b003','historical-return-tail-context','末203/416的300%与500%为自述比较。','本段技术命题不将涨幅作可复制账户收益或项目验证。')
note('387-b002 387-b003 387-b004 388-b000 388-b001 388-b002 388-b003','nontechnical-currency-policy-essay','加息/金融结构奇点、外储/利差、1996指数2792至6102以及西中医比喻完整审读。','作者2007宏观政策观点/历史自述，未外核经济因果、央行账表或医学比喻，不作缠论技术定理/现行政策或医疗事实。')
note('388-b005 389-b000','historical-policy-script-context','技术合力之外要求市场共识/政治修辞和本人剧本的意见。','只保历史观点，不认证作者或任何人可强控走势；技术三模式形成中另录。')
note('390-b000','historical-sector-inside-information-context','均线短长逻辑外，医药/钢铁/铜矿/故意亏损ST及某地暗语。','截不出具体公司事实/荐股；不破解消息交易、未核铜矿资产或造差业绩动机，技术均线/个股结构另录。')
note('390-b004','historical-regulatory-evasion-boast-context','作者梦话/监管把柄修辞。','不认证其合法性/内幕准确，不帮执行或作为技术方法。')
note('392-b002 392-b003','historical-stock-intent-and-news-boast-context','作者摆弄小盘/锌锗/最大消息集散地自述。','只引风险/买点/不追消息的技术建议，不认证控盘意图和资产信息。')
note('394-b005 395-b006','historical-personal-intent-regulatory-context','首钢熟人、419地点与史玉柱/抓人、合法投资等作者自述。','未核人物/法律/股票中线结论，不作为作者已证公司事件或当前建议。')
issue('literal-not-smaller-inequality-and-small-to-large-scope','383-b002','背驰级别一定不小于转折级别为原字，和44小级转折引发大级/本段30例有范围张力；原30级别以上盘整也不静定包含边界或改49本级盘整可做，不能私改不大于或直接合成通用定理。','读原页/跨课原句已核，保本条原句和歧义，后查作者更正/转折含义与适用前提，不修改已复核43/44记录。',True)
issue('observer-pattern-predictability-philosophy-not-physics-proof','382-b008 382-b009 382-b010 383-b000 383-b001 383-b002 383-b003','观察参与和形态绝对预测为作者哲学体系，量子/科学/六道/贪嗔痴疑慢类比不是物理心理学或金融实证；固定级别和当前点位不同对象。','不把类比变自然科学证明/逐点未来预测，30同级顶背驰退出条件单列，理论保证非执行保证。',True)
issue('precise-five-completion-lower-chart-versus-MACD-auxiliary','386-b001 390-b008 396-b007','精确5分完成需1分图与49/50较大MACD辅助小信号范围不同；小转大/完整次级类型不能只靠高周期柱看出。','保只5分则选更大操作/5分最低级基准，不将所有周期图看成同一信息或读者6至9段分组全部认可。',True)
issue('source-dates-ten-figures-and-three-CCTV-reader-charts','386-b005 386-b009 387-b000 390-b001 390-b002 390-b003 390-b004 392-b005 392-b007','5/22三段在5/21尾时间后，十图5后加5未核，600279/802/569均CCTV读者，不作作者新命题证据。','只修日期/空格和图备注，原字/几何不改；不可图示未来走势认证早前预测或无独立作者认可就升读者话。',True)
issue('third-point-type-vs-center-and-retest-whole-move','393-b007 393-b008 393-b009 393-b010 393-b012 393-b013 394-b001 394-b002','离开回试均次级走势类型，中枢不等全走势，离开子枢可在内；一个子枢不保安全，岛反例；三买后仍可转大，够级利润空间为作者强语。','回试按整体走势而非只子枢，抽不回限该次级回试非永不返回，保两种接近点/高级优先与技能退出空间，未补全实时成交风险。',True)
issue('600216-one-word-affirmation-context-and-corrected-time','394-b007 394-b009 394-b010 395-b000 395-b001','作者先否5/18 10:00，再用对认可读者5/16 10:20至5/17 10:10离开/10:10至14:55回试的5/17 14:55三买；细时刻属读者文本、认可属作者。','必须一起返回上下文和身份，不能只高亮对就伪装完整作者长引；图当时可得未核原发，未证明全部分段几何和执行价。',True)
issue('same-level-association-first-three-extension-and-second-buy-second-leg','391-b000 391-b002 391-b004 392-b000 392-b001 396-b003 396-b005 396-b006 396-b007','结合律可归标准高低接点，延伸看前三段区间但各级分解可异；二买5上5回不破是第二段，未将读者A1/A3问法逐项作答，所有买卖根于一类非同级标签全合。','保形成/完成与类型/中枢/全波动范围区别，不用九段收敛读者质疑当作者已证日线结构，等值和全分解细节待核。',True)
issue('historical-4050-4129-13700-and-policy-stock-strong-claims','383-b004 383-b005 384-b000 384-b001 388-b004 388-b005 389-b001 390-b000 390-b002 390-b003 393-b002 395-b009 396-b000','4040/4050/4129/深13700是特定历史模型及单边区间例，首次越线仍可第一种大顶；零成本/翻倍/外币B股及公司宏观自述未实证。','不把价格/期限当所有资产硬阈值，不外推当前投资/法律/经济或医学事实，执行通道/快速行情明确与理论分析分开。')
relations={
 'prediction-includes-observers-not-independent-clockwork':[('走势预测','市场合力','qualifies')],
 'training-guide-independent-present-fixed-operation-level':[('操作级别','当下','qualifies')],
 'multi-level-isomorphic-patterns-mental-structure-religious-analogy':[('自同构性结构','贪嗔痴疑慢','qualifies')],
 'near-opposite-points-use-large-unless-skilled-exit-room':[('操作级别','交易条件','qualifies')],
 'precise-five-completion-needs-one-chart-only-five-enlarge-base':[('周期K线图','完成','qualifies')],
 'may21-fast-market-channel-no-exact-low-guarantee':[('交易通道','交易条件','qualifies')],
 'same-level-decomposition-associativity-standard-high-low-joints':[('同级别分解','结合律','qualifies')],
 'third-points-both-leave-retest-sublevel-one-child-center-not-safe':[('第三类买卖点','岛型反转','qualifies')],
 'leaving-child-center-can-be-within-parent-context-affirmation':[('次级别','走势中枢','qualifies')],
 'all-points-root-first-first-root-divergence-not-same-level-collapse':[('买卖点','第一类买卖点','qualifies')],
 'second-buy-thirty-first-five-up-five-retest-no-low-second-leg':[('第二类买点','结合律','qualifies')],
 'forget-rebuy-small-level-full-in-out-use-larger-view-or-few-stocks':[('操作节奏','操作级别','qualifies')],
}
relations={'upper-l052-c-stage-'+k:v for k,v in relations.items()}
scopes={
 'literal-divergence-level-not-smaller-than-turn-level-unresolved':['第52课原句记录，不静改不小于','跨课关系/转折一词范围未统一，本条不当无歧义总定理'],
 'thirty-top-divergence-exit-own-down-or-above-consolidation-author':['30分钟操作中的30分钟顶背驰','原30分钟级别下跌及30分钟级别以上的盘整，不静定以上的包含边界'],
 'near-opposite-points-use-large-unless-skilled-exit-room':['大级与相反小级点很接近而非完全同一点','小级例外须经验精度确认有退出空间'],
 'precise-five-completion-needs-one-chart-only-five-enlarge-base':['精确识别5分钟走势类型完成/小转大','只有5分钟图时放大操作并将5分钟作最低基准'],
 'third-points-both-leave-retest-sublevel-one-child-center-not-safe':['离开和回试均完整次级走势类型','仅上方一个子中枢不保证安全'],
 '600216-may17-1455-author-yes-to-reader-two-legs':['作者395-b001仅答对，指代紧前读者395-b000','600216离开5/16 10:20至5/17 10:10，回试至5/17 14:55'],
 'second-buy-thirty-first-five-up-five-retest-no-low-second-leg':['30分钟一买之后','5分钟向上后5分钟回试不破原低点，次级分解第二段'],
}
for r in rows:
 if r['id'].split('upper-l052-c-stage-')[1] in scopes:r['conditions']=scopes[r['id'].split('upper-l052-c-stage-')[1]]

for r in rows:
    r['relations'] = [{'source': a, 'target': b, 'type': t} for a, b, t in relations.get(r['id'], [])]
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
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], '600279/802/569的CCTV答复仍读者；600216先否05181000后对认可邻问05171455，细时刻仍读者来源不冒作者长引；9段分组、回试子枢/走势混用、首钢暗语与收益自述不默认全收。'
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
        'note': '原不小于不静改并保跨课张力；固定级别/模式预测与具体点价、哲学类比区别；理论分析不保通道快市精确成交，形成/完成与走势/子枢/波动区间区分，三买离开回试都次级，短答对有明确读者指代，所有点根一类非同级标签全并。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=f['note'],
             figure_source_review='实际查看382至396十五页及10整图：386/387/392三图为CCTV读者，5图有晚于文字未来K/5图当时可得但原发未核；作者600216对只认可紧前一问，未把读者时刻写成作者原引；384当日1分和391两周期视角不同，后K不证预测。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 150 and Counter(x['lesson_number'] for x in ledger) == {52: 150}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [52], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(382, 397)), 'figure_objects_viewed': 10, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '52课150段15页10整图同模型四轮；3段归5/22及50日期空格、5后图5未核；原不小于/固定级别预测、精确小级完成/通道、三买类型与子枢、600216短答指代分层，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


