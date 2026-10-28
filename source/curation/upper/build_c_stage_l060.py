"""Materialize the main agent's four-pass reading of lesson60.

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
BASE = 'c_stage_l060'
REVIEWER = 'Codex 主代理 / 阶段C上册60课同模型四轮复核'
SOURCE_SHA = '50420ef133369d290e61862ac1334ba32920947a1ecc2afff4ee4d668c787bde'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-060' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 38
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 451 AND 457 ORDER BY pdf_page,id', (DOC,))]
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
    pending.append({'id': 'upper-l060-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})

c(60,'expectation-force-only-externalized-actual-trade-not-fear-alone','451-b001','作者将走势视为预期合力，但进入市场合力的预期须外化为买卖行为；只有恐惧而无实际行动不构成交易行为。','市场合力|市场心理|市场分力',1,'这是作者市场心理模型，不把恐惧个体的内心当可测真实分力，也不证明未成交委托或观望对一切市场机制均无影响。')
c(60,'samelevel-B0A1B1A2B2-below-vs-not-below-equality-larger-center','451-b002','同级别B0跌A1、弹B1、再跌破至A2、反弹B2，作者分B2低于A1和不低于A1两类；后者构成某更大级别中枢，前者没有。','走势中枢|同级别|重叠',1,'保同级连续示例及不低于含相等，图右只画高于不删文字等号；不能用两个任意价格的B2≥A1代替完整同级走势/中枢条件。',conditions=['本课B0—A1—B1—A2—B2连续同级走势示例'],figs=[(451,1)])
c(60,'A1-psych-price-three-expectations-watch-no-actual-trade','451-b002','A1被跌破后成重要心理位；作者分预期回到A1并交易、预期不能回到并交易、观望三类，以前两种实际行为的合力解释当下B2是否低于A1。','市场心理|市场合力|当下',2,'前两类都要实际交易；不据走势反推每个参与者具体心理、人数或资金量，第二预期更大是作者对该模型结果的解释非独立心理测量。',figs=[(451,1)])
c(60,'no-prediction-not-impossibility-not-driven-by-greed-fear','451-b003','本课把不预测、不预期解释为不因贪婪恐惧作预期，而按走势自身规律跟随市场合力；并非不可预测、不可预期。','走势预测|当下|市场心理',1,'保作者自己对术语的限定，不以一句从不预测删除其后实际条件预测，亦非本项目证明能无误预测价格。')
c(60,'multiple-current-decompositions-forming-not-fuzziness-author-theory','451-b004 452-b000','作者强调当下走势正在形成，因此有符合理论的多种分解；多样性被其视为多角度约束市场，而非模糊性。','走势多义性|走势分解|当下',1,'跨页完整承接，符合理论的多解不等任意画法皆有效；不患/万变不离控制为作者理论主张，不当本项目完备性数学证明。')
c(60,'finite-minimum-observed-segment-cost-channel-capacity-flatten-below','452-b001','因成本、交易通道和资金规模约束，实际观察并操作的精度不能无限细，须确定最低级别线段并抹平其下波动；每笔成交构造虽理论可细分，却不具实际操作性。','最低级别|交易成本|交易通道|交易容量|价格精度',1,'理论每笔精度与可操作最低级别分开；费用增加时可操作级别须增大，未给适用所有账户的固定最小分钟或笔参数。')
c(60,'meaningful-operation-atleast-subminute-segment-literal-not-fixed-minute','452-b002','作者把实际有意义的操作大致表述为“至少是1分钟以下线段级别的”，与最严格、无太大操作意义的线段下分析区分。','操作级别|线段|最低级别',2,'原大概/至少/1分钟以下线段级别照存，不静改至少1分钟走势；是经验与成本语境非严格数学最低级别，线段定义仍需前后文。',ambiguity='definition_boundary')
c(60,'45-46-vs43-44-consolidation-all-red-areas-sum','452-b002','最严格分析下，45—46相对43—44构成盘整背驰，力度比较需计下面所有红柱面积之和。','盘整背驰|MACD柱波|线段',1,'所有红柱求和，不只挑最后一小团或改用柱峰高度；本批无像素积分数值，MACD只辅助结构。',figs=[(452,1)])
c(60,'45-46-inner-small-to-large-first-no-new-high-exit-smaller-center','452-b002','细分线段以下，45—46是小级别转大级别；红箭头后第一次拉起不创新高可退出，因为其后会形成下上下重叠小中枢，线段以下同级操作不参与它。','小级别转大级别|同级别分解|中枢震荡|卖点',1,'限最严格线段下操作，不把此小回拉当所有30分操作必须卖；必成小枢为作者此例推断，未给通道/成交保证。',conditions=['第60课45—46及红箭头后走势','按线段以下级别作同级操作'],figs=[(452,1)])
c(60,'thirty-operation-ignore46-47-hold-five-up-until-div-or-break','452-b002 453-b000','若按30分钟操作，可忽略46—47；从3404起作者称为标准5分钟上涨，持有至少等该5分钟上涨背驰或突发破坏。','操作级别|持股|背驰|确认',1,'跨页按30分钟与忽略波动联合，退出条件是5分背驰或突发破坏，不等任意持股永不卖；后文大级破坏可用更小卖点需联读。',conditions=['本课从3404起走势','原按30分钟级别操作'],figs=[(452,1)])
c(60,'46-55-five-center55-consolidation-not-true-first-buy57-analogy','453-b001','46—55构成5分钟中枢，55跌破53后盘整背驰；仅类比把55作一买时，57可称二买，作者明确严格说盘整背驰无所谓第一类买点。','走势中枢|盘整背驰|第一类买点|第二类买点',1,'如果/类比/严格限定不能省，不把盘背55升级成标准趋势一买或任何盘背后都正式二买。',figs=[(452,1)])
c(60,'55-60-segment-up59-60-div-zero-return-newhigh-weaker-area-height','453-b001','55—60是线段级上涨；59—60背驰的MACD辅助为黄白线先回零轴、60新高，而柱面积及黄白高度均弱于前面。','背驰|MACD|MACD柱波|线段',1,'先回零/价格新高/面积高度较弱联合，不把任一项当背驰充分条件，不补MACD数值或把绿柱回0当黄白回0。',figs=[(452,1)])
c(60,'60-pull-under58-61-lower-new58-61-one-center','453-b001','按该背驰，作者说60后须回拉58之下；61实际低于58，由此58—61形成新的1分钟中枢。','背驰|中枢新生|走势中枢',1,'保原文字58—61，不能静改收评另说从60起的[4224,4254]锚点；理论须回拉为作者推断，本文另以已发生61作案例结果。',figs=[(452,1)])
c(60,'new-one-expand-five-and46-touch-key-no46-superstrong-five-up-continues','453-b001','新1分钟中枢是否扩成5分钟、旧5分钟中枢最高点46是否重新被跌破，是后续关键；若46不再被触及，则超强并延续3404起5分钟上涨。','中枢扩展|上涨|确认',1,'触及与跌破两种原词保留，不能静换成同一严格不等号；并非当前已知新1分必扩5分，收评4192附近46另存时点。',figs=[(452,1)])
c(60,'news-during-nested-confirm-worst-after-zero-effect-author-strong','453-b002','作者把突发消息视作当下分力；称其在区间套精确定位背驰期间出现最不幸，530属此例，定位后出现则操作影响为0，并称前者小概率。','区间套|确认|政策风险|市场分力',2,'0及小概率是作者理论/经验强语，未外证频率或无滑点/T+1/跌停/流动性风险，不当所有账户实测保证。',ambiguity='execution_boundary')
c(60,'not-every-second-sell-act-monthly-or-five-intact-one-center-ignore','453-b002','突发消息后是否反应二卖取决于操作级别和被破坏级别；月线操作者可忽略本次跌势，5分操作者若连1分中枢未破、仅1分以下震荡也可不理其二卖。','第二类卖点|操作级别|政策风险|走势中枢',1,'这是条件分支，不能只取二卖足以应付就说任何二卖都要卖；不破1分中枢只是本5分操作例，不据月线话术逃避既定级别风险。')
c(60,'large-level-news-break-dont-wait-same-level-intraday-smaller-second','453-b003','突发消息破坏级别越大，越不必等同级二卖；例如下缺口破坏日线上涨，当天盘中1分甚至线段二卖可供退出，等日线二卖可能久且位置更差。','第二类卖点|缺口|操作级别|走势破坏',1,'大级已被破坏是前提，不作为平常随意改操作级别理由；可供退出为结构机会，不证明每只股每个通道必成交。',conditions=['突发消息/下缺口已破坏日线级别上涨的例子'])
c(60,'level-usual-space-fast-five-drop50-may-enter-smaller-than-thirty','453-b003','级别通常对应操作空间，但快速行情可在5分走势跌50%，其底背驰反弹空间可能大于平常30分；此时原按30分者亦可按5分买入，不必等30分买点。','操作级别|幅度|背驰|交易有效性',1,'保快速/5分大跌例及空间理由，不把所有5分底背驰大于30分、50%必反弹或任意下调级别写定理；原50%是作者本次例述未独立测算。',conditions=['快速变动行情中较小级别具有足够可操作空间'],ambiguity='execution_boundary')
c(60,'jun19-from60-one-center4224-4254-below-third-sell-not-price-alone','453-b004 454-b000','6月19日收评以61处4224界定从60起的1分中枢[4224,4254]；4224下不出现1分三卖仍强，后两天观察该枢三类点。','走势中枢|第三类卖点|确认',1,'原从60起与正文58—61不同描述并存，三卖须结构/次级离返，不把单笔跌到4224下当三卖；联合三卖有效破的59原话亦保。',figs=[(454,1)])
c(60,'jun19-above4254-one-third-buy-for-new-up-otherwise-oscillation','453-b004 454-b000','作者称要展开新轮上攻，需在4254上出现1分三买，否则继续该区间中枢震荡延伸。','第三类买点|中枢延伸|中枢震荡',1,'4254上是结构三买的条件，不等单价突破或保证完成更大上涨趋势；后加6/21图不证6/19当时必然路径。',figs=[(454,1)])
c(60,'four-stock-shapes-individual-not-index-all-same-buy-kind','454-b001','个股应分四形态：新高回试看三买；前高下蓄势看小级三买突破或震荡低点；反弹受阻平台同前类但离前高较远；底部双底头肩底看一二买。','买点|第三类买点|第一类买点|第二类买点|走势多义性',1,'四分类是当时技术处理法，非所有个股/所有行情穷尽定理；看点是找对应结构，不能光凭指数或图形名称机械介入。')
c(60,'jun20-touch46-near4192-center-expand-now-larger-oscillation','456-b002','6月20日震荡已触及4192附近的46，作者判断中枢将扩展，后续进入较大的中枢震荡。','中枢扩展|中枢震荡|确认',1,'原附近和将/后面保留，此处未明确扩至哪个分钟级别，不据后图添30分已完成；缺口仍在是风险背景。',figs=[(456,1)])
c(60,'jun20-one-return-fail-touch4224-five-third-sell-or-stand-strong','456-b002','相对61的4224，若1分走势不能重新触及会成5分三卖、震荡向下扩；若重新站稳4224，震荡仍强。','第三类卖点|中枢震荡|次级别',1,'原不能触及与重新站稳两支条件保留，不将刚回到4224立刻当站稳或未完成1分反抽先确认三卖；级别5分三卖非1分三卖。',figs=[(456,1)])
c(60,'jun20-mid4144-stand-or-adjust-level-five-day-five-week-reference','456-b002','中线若4144半线站不稳则调整级别加大；不会细看者短线看5日线、中线看5周线，不破则作者认为问题不大。','操作级别|均线系统|经验压力线',2,'短5日/中5周不同，问题不大为作者相对判断非无风险，未补复权/收盘/均线参数和站稳机械阈值。')
c(60,'newhigh-check-large-divergence-or-consolidation-to-third-buy','456-b003','新高股须防大级别背驰和多头陷阱；没有背驰，或盘整背驰最终转三买时才可考虑进入，仍应按前四形态分别处理。','背驰|第三类买点|盘整背驰|多头陷阱',1,'原没有背驰或盘背最终转三买分支保留，不因新高无背驰单条件就替代各形态买点/交易约束；盘背尚未转化不提前当三买。')
c(60,'chart-period-not-move-level-one-minute-can-find-year-center','456-b007 457-b000','5分或30分图定线段相对1分图仅精度较低，图周期与走势级别不等；用1分图一样可判断年线中枢。','周期K线图|级别|价格精度|线段',1,'跨页作者答疑完整承接，读者请求看5分图不作5分图只能5分级别的认可；不能反向凭粗图恢复未存细节。')

note('454-b002','learning_context','作者要求自己动脑分析而非等待个股答案。','不是本项目个人服务或收益保证。')
note('454-b003 454-b004 454-b005 454-b006 455-b000 455-b001 455-b002 455-b003 455-b004 455-b005 455-b006','independent_historical_PE_article','完整阅读6/20独立人民币PE文章：退出渠道/上市与企业观念/基金资源配置/监管及附录上市条件，保独立日期来源。','作者所列12/36月禁售、银监办法/合伙企业法日期及股本/利润/现金流门槛是固定底本历史引述，未核现行法规或独立史实，不输出当前法律投资建议；不纳中枢技术定理。')
note('456-b001','cross_lesson_plan','6/20评论指13:30附近背弛，要求先自己分析、待61课对照。','本段只指向下课，未给完整区间套算法，不以6/21后图提前证明。')
issue('expectations-model-samelevel-overlap-not-predict-fear','451-b001 451-b002 451-b003 451-b004 452-b000','交易化预期的作者模型、B2不低于A1含相等、符合理论的多解以及不预测术语应分层。','不任意价格重合成中枢，不证心理人数和市场完备性；原不预测不是不可预测。',True)
issue('lowest-operable-precision-and-45-46-small-to-large','452-b001 452-b002 453-b000','实际有限精度与每笔理论精度/至少1分以下线段原话、45—46面积/小转大和30分忽略波动不同。','无通用固定最小分钟参数；成本/通道/容量和原操作级别保，不造面积积分数。',True)
issue('55-first-only-analogy-58-61-vs-from60-center-and46','453-b001 453-b004 454-b000 456-b002','55只盘背假一买类比57二买；正文58—61一分枢与收评从60起[4224,4254]描述分存，46触及/跌破与新枢升级条件保。','核61是否补形态，不静改旧锚点或量化附近4192；原图4067.85/重绘4068.20分别保。',True)
issue('news-zero-effect-second-sell-level-and-fast-space-exceptions','453-b002 453-b003','消息定位后影响0/最不幸小概率/二卖足够属作者强语；不必每二卖反应，大级已破可更小卖、快行情更小入。','保前提与空间理由，不取消一般既定操作级别，不伪造实测胜率或保证成交。',True)
issue('4224-4254-one-vs-five-third-points-and-four-stock-shapes','453-b004 454-b000 454-b001 456-b002 456-b003','4224下1分三卖和后日1分回抽不触4224形成5分三卖不同；四股形态及新高防大背驰条件。','触价不等三类点，不把所有股等于指数，站稳/回试/完成仍需结构。',True)
issue('three-date-spaces-four-figures-and-historical-PE-law','456-b006-s01 456-b007 457-b000 455-b004 455-b006','3作者答日期只补空格，4图2未核2后加，独立PE文章法规/门槛为历史原话未外证。','后6/21 K不证明前评论/成交，原发未核不充作者唯一证据；法律原话不作为当前规则。',False)

relations={
 'expectation-force-only-externalized-actual-trade-not-fear-alone':[('市场合力','市场心理','qualifies')],
 'samelevel-B0A1B1A2B2-below-vs-not-below-equality-larger-center':[('走势中枢','同级别','requires')],
 'finite-minimum-observed-segment-cost-channel-capacity-flatten-below':[('最低级别','交易成本','qualifies'),('最低级别','交易通道','qualifies'),('最低级别','交易容量','qualifies')],
 '45-46-vs43-44-consolidation-all-red-areas-sum':[('盘整背驰','MACD柱波','qualifies')],
 '45-46-inner-small-to-large-first-no-new-high-exit-smaller-center':[('小级别转大级别','同级别分解','qualifies')],
 '46-55-five-center55-consolidation-not-true-first-buy57-analogy':[('第一类买点','盘整背驰','qualifies')],
 'not-every-second-sell-act-monthly-or-five-intact-one-center-ignore':[('第二类卖点','操作级别','qualifies')],
 'large-level-news-break-dont-wait-same-level-intraday-smaller-second':[('第二类卖点','缺口','qualifies')],
 'level-usual-space-fast-five-drop50-may-enter-smaller-than-thirty':[('操作级别','幅度','qualifies')],
 'jun20-one-return-fail-touch4224-five-third-sell-or-stand-strong':[('第三类卖点','次级别','requires')],
 'newhigh-check-large-divergence-or-consolidation-to-third-buy':[('多头陷阱','背驰','qualifies')],
}
for r in rows:r['relations']=[dict(source=a,target=b,type=t) for a,b,t in relations.get(r['id'].split('upper-l060-c-stage-')[1],[])]


by_passage=defaultdict(list)
for r in rows:
 for e in r['evidence']:by_passage[e['passage_id']].append(r)
for item in pending:
 item['lesson_numbers']=[60]
 if item['id'].endswith('three-date-spaces-four-figures-and-historical-PE-law'):item['figure_ids']=[f['id'] for f in figures]
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
 ledger.append(dict(passage_id=id,lesson_number=60,document_id=DOC,pdf_page=p['pdf_page'],role=p['role'],speaker=p['speaker'],published_at=p['published_at'],source_text_sha256=hashlib.sha256(p['text'].encode()).hexdigest(),result=result,claim_ids=[r['id'] for r in linked],related_existing_claim_ids=retained[id],existing_evidence_not_mutated=True,pending_issue_ids=[x['id'] for x in pending if id in x['passage_ids']],reviewer=REVIEWER,rounds={'1_read_and_scope':reading,'2_atomic_conditions':atomic,'3_normalization':{'concept_labels':sorted({x for r in linked for x in r['concepts']}),'related_existing_claim_ids':retained[id],'note':'交易化预期模型/同级B2不低于A1含等号，实际最低级别受成本通道容量；严格45-46小转大与30分忽略46-47分层，55假一买仅类比，58-61与从60起枢分别保，消息后分级反应/大破坏用小卖与快速空间小买均保条件。'},'4_reverse_check':inverse}))
for f in figures:
 f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=f['note'],figure_source_review='实际查看451至457七页4整图；451理论图和452原图原发未核，454/456重绘含后6/21为后加；B2等号由文字给出、4067.85/4068.20分别保，不据后K证明前瞻。',linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger)==38 and len(figures)==4
for suffix,data in [('reviewed.jsonl',rows),('coverage.jsonl',ledger),('pending.jsonl',pending),('figures.jsonl',figures)]:
 (OUT/f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x,ensure_ascii=False,separators=(',',':')) for x in data)+'\n',encoding='utf-8')
summary=dict(stage='C/E',schema_version=metadata['schema_version'],graph_version=metadata['graph_version'],lessons=[60],document_id=DOC,reviewer=REVIEWER,passages_read=len(ledger),claims=len(rows),evidence=sum(len(r['evidence']) for r in rows),importance_counts=dict(Counter(r['importance_level'] for r in rows)),new_concepts=sorted({x for r in rows for x in r['concepts']}-set(concepts)),whole_lesson_semantic_read_complete=True,technical_extraction_complete=False,four_round_review=True,independent_review_claimed=False,visual_pdf_pages=list(range(451,458)),figure_objects_viewed=4,figure_origin_counts=dict(Counter(f['origin_status'] for f in figures)),pending=[x['id'] for x in pending],source_passages_snapshot_sha256=SOURCE_SHA,retained_source_links_in_ledger_only=True,database_mode='ro',formal_import=False,delivery_scope='shared_knowledge_base_only',acceptance='60课38段7页4整图同模型四轮，3时间空格及2未核2后加图；预期模型/实际最低级别/55假一买/中枢锚点/消息级别与快空间例外/1和5分三类点分存，待预检。')
(OUT/f'{BASE}.summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
db.close();sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(summary,ensure_ascii=False))


