"""Materialize the main agent's four-pass reading of lessons10-12.

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
BASE = 'c_stage_l010_l012'
REVIEWER = 'Codex 主代理 / 阶段C上册10至12课同模型四轮复核'
SOURCE_SHA = 'dc72ef39641b6cd93f98e666f00818d59ce0e2c3e05b71d2e6651fe75eb605cd'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id IN ('lesson-010','lesson-011','lesson-012') ORDER BY pdf_page,block_index,id")}
assert len(passages) == 213
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 27 AND 43 ORDER BY pdf_page,id', (DOC,))]
assert len(figures) == 6
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
    pending.append({'id': 'upper-l010-l012-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})


quote_overrides['28-b004'] = 'N只能有限地给予一个固定的能搞对象，有N1，就要有N2，这样才能生生不息，才能风生水起。'
c(10, 'policy-preference-not-market-observation', '28-b001',
  '作者区分自己反对人民币升值、国有股流通的立场与市场观察，并以当时预期股市大涨解释重新看盘。',
  '市场心理|宏观市场判断|操作策略', 3, '大涨因果是作者历史判断，未独立验证；不把政策好恶直接作为交易信号。', ['第10课对2005年重新看盘的历史自述'])
c(10, 'trade-observed-opportunity-not-liking', '28-b003',
  '作者把只做能做的而非喜欢的股票作为投机原则，要求通过观察判断机会，不能只用股票好坏故事解释买入。',
  '操作策略|市场心理|确认', 1, '一万人9999为修辞而非统计，能做的具体标准应随所选系统明确，不自补收益保证。')
c(10, 'finite-holding-object-and-changing-opportunity', '28-b004 28-b005',
  '作者要求对单一对象的参与有有限阶段；能做是相对的，机会会变化，参与时须专注观察，失去机会时须能退出。',
  '操作策略|当下|持股', 1, '仅截取有限参与的原句，不以侮辱修辞或所有亏损归因作技术证明；本条未定义具体退出点。')
c(10, 'nov24-resistant-stocks-five-line-branches', '29-b003 30-b000',
  '11月24日午间作者关注逆市不跌、尚未启动的个股，列5日线争夺两支：多头胜可当日完成调整，否则时间延长。',
  '均线|板块轮动|确认|完全分类', 2, '跨页读完分支，不把下轮黑马可能性当保证，也不把当日盘中提示当收盘已确认。', ['2006年11月24日12:15该盘中提示'], figs=((29, 1), (29, 2)))
c(10, 'nov23-index-divergence-not-technical-beichi', '30-b002 30-b003',
  '在作者转录的11月23日提示中，沪深指数背离、量缩被用作震荡及调整风险；他另区分盘中震荡与至少考验5天甚至10天线的短线调整。',
  '指数走势背离|成交量|均线|市场风险', 2, '这是作者明确自引昨日提示，不是引号署名的读者；两地指数背离不直接等同后文严格趋势背驰。', ['2006年11月23日该沪深指数观察'])
c(10, 'nov23-rotation-on-adjustment-capacity', '30-b004 34-b004',
  '作者在当时调整语境中把换股或打短差看作有技术者的机会，技术一般者可等待，短线继续关注未动板块轮动。',
  '板块轮动|操作熟练程度|操作策略', 2, '11/23与11/27提示分别保留日期，机会不是任何人在调整都能获利。', ['各段历史调整阶段','有相应短线能力'])
c(10, 'nov24-five-line-retest-not-just-cross', '30-b005 30-b006 30-b007 30-b008',
  '11月24日作者先要求5日线站稳前观察，再以14点回试确认站稳看反攻；收盘仍说力度弱、下周可能反复，若再失5日线则看2000下方缺口。',
  '均线|确认|缺口|完全分类', 1, '按13:34、13:50、14:14、15:00四条提示分别取证，突破、回试和力度判断不是同一瞬间；不据图提前判整周。', ['2006年11月24日盘中至收盘该指数状态'])
c(10, 'no-chasing-late-rise-not-forced-entry', '30-b012 31-b019 36-b005',
  '作者在601111、600028/600019和600016答复中反复要求避免大涨后追高，偏好刚启动或中线调整结束的机会；中线没问题也不是必须介入的理由。',
  '追高|操作策略|确认', 1, '保留三次个股问答语境；牛市随便买也赚钱为当时修辞，不作普遍盈利事实，未声称永不参与任何已涨股票。', ['2006年11月24/27日所列个股答复及相应介入阶段'])
c(10, 'breakout-retest-not-big-candle-chase', '30-b013',
  '对000039作者要求不等大阳线后再追，而习惯放量突破后的回调介入；当时前期缺口可能带来短线折腾。',
  '放量突破|追高|缺口|操作策略', 2, '限该答复的突破/回调语境，不把任何缩量回落都认有效买点。', ['2006年11月24日000039问答'])
c(10, 'nov24-false-breakout-562-and-week120-875', '31-b004 31-b005',
  '作者对000562提醒急涨后调整的突破可能骗线、第二波需有效突破9.6；对000875则以当时约3.4元的120周线有效突破观察中线启动。',
  '假突破|均线|确认|操作策略', 3, '不同股票、8.8短压与9.6中压/120周线不混并为通用阈值，未独立复算行情。', ['2006年11月24日000562与000875各自案例'])
c(10, 'news-test-market-reaction-not-prediction', '31-b008 31-b009',
  '面对美元大跌影响的提问，作者要求观察市场对所有消息的综合反应，即走势本身；消息被用来测试市场状态而非预言单条消息效果。',
  '公开信息|市场心理|走势预测|当下', 1, '感冒/体质仅比喻，不是医疗结论，也不等不看任何消息。')
c(10, 'entry-horizon-plan-position-before-fluctuation', '31-b018',
  '对600177作者先区分原本中线还是短线介入：中线指标仍好且未破其120周参考线时不应仅因短波动离场；买入前须定理由、期限、介入模式及仓位。',
  '操作级别|仓位|均线|操作策略', 1, '120周为该股票案例而非所有股票统一生命线，不能把一次卖出理由泛化成从不卖出。', ['该600177问答','按原定短线或中线标准'])
c(10, 'full-position-reduce-vs-small-position-hold-case', '32-b003',
  '在600028/600019追高问答中，作者未要求全部抛出：若满仓可借短冲减仓以降风险、增灵活性；占比不高可继续留，前提是所论中线尚未结束。',
  '仓位|持股|操作策略', 1, '满仓与低占比分支不能省略，不当对当前个股的建议或普遍不止损规则。', ['2006年11月24日该两股问答','作者判断中线行情尚未完全结束'])
c(10, 'good-habits-avoid-forced-dilemmas', '32-b004 32-b005',
  '作者强调发现和把握机会的能力要有良好操作习惯，并用庖丁解牛说明高手应尽量避免把操作陷入两难。',
  '操作熟练程度|操作策略', 2, '所有困难归先前失误是作者劝学绝对措辞，未独立证明；机会永存不等任何时刻都应下单。')
c(10, 'procedure-before-market-intuition', '32-b012',
  '作者要求先减少消息、情绪干扰，逐步把基础变成本能，包括建立适合自己的有效操作程序，再谈对市场的敏感与直觉。',
  '市场心理|操作熟练程度|机械化操作', 1, '直觉是训练描述，不作神秘预测能力或忽略所有信息的要求。')
c(10, 'nov27-three-bull-phases-historical-view', '33-b000 33-b001',
  '11月27日回放外层作者把当时市场看作大牛第一阶段，并用96至2001经验列成分股、成长股、重组股三段，认为大面积炒重组才增结束风险。',
  '牛市阶段|成长性|板块轮动', 3, '这是2006外层作者评论，不以2005自称署名旧文直接举证；三阶段为其历史经验，非所有牛市必经定律。', ['2006年11月27日作者对当轮行情的历史解释'], ambiguity='historical_bull_stage_generalization_not_independently_verified')
c(10, 'nov27-current-five-and-next-adjustment', '34-b005 34-b006',
  '11月27日作者说指数收5日线，侧重个股轮动；同时预期本轮调整后再上攻完成，下一调整会更全面、较大，而非仅大盘股。',
  '均线|板块轮动|市场风险', 2, '当前收盘与下一轮展望分开，日期不是被误解析的正文署名。', ['2006年11月27日收盘评论'])
c(10, 'nov28-kiss-branches-historical-application', '34-b007 34-b008 34-b009 34-b010 34-b011 34-b012 34-b013',
  '11月28日作者对5/10日线吻分类：飞吻则次日直接攻5日线，唇吻仍反复且5日为压，湿吻则10日要破并反复，再等待方向。',
  '均线系统|飞吻|唇吻|湿吻|完全分类', 2, '这是该次指数情景，不能把10日必破写成所有湿吻的必要条件；与第11课一般定义分别查证。', ['2006年11月28日该5/10日线情景'])
c(10, 'morning-entry-t0-exceptions', '35-b005',
  '作者因无T+0，通常不主张早上买股，认为下午常有选择；强力突破走势及着眼中线逐步建仓是他明确保留的不同情况。',
  '交易规则|操作级别|仓位', 1, '原话是没有T+0，不补成任何制度下禁止早盘；两类例外均保留，与后课T+1执行限制可追溯。', ['作者所述无T+0的股票交易环境'], exceptions=['强力突破走势','着眼中线逐步建仓'])
c(10, 'warrant-full-position-high-skill-limit', '35-b008',
  '针对满仓认沽表态，作者要求别赌性太大；除非短线感觉很好，否则不宜满仓参与高风险品种，赚钱应按长期过程看。',
  '仓位|权证|赌徒心理|操作熟练程度', 1, '短线感觉好不是已证明安全的充分条件，作者未给量化满仓阈值或收益承诺。', ['2006年11月27日读者满仓认沽语境'])
c(10, 'volume-shrink-confirm-then-expand-case', '35-b011',
  '对600087作者说短线放量过急，应先缩量确认突破，再看放量。',
  '成交量|放量突破|确认', 2, '三阶段顺序仅该短线答复，不把任意放量过急都断言后涨；后加图不能反填当日结果。', ['2006年11月27日600087短线案例'], figs=((35, 1),))
c(10, 'own-standard-capital-experience-before-trade', '36-b000 36-b001',
  '作者说与其问600036调整是否到位，应先问是否符合自己的介入标准；标准与资金及经验有关，连标准未清楚时应先停下来想清。',
  '操作策略|操作熟练程度|资金管理', 1, '不同操作标准不等结构定义可任意变化，未将“自己知道”当无法核查的正确性。')
c(10, 'nov28-bank-barometer-not-buy-now', '36-b010 36-b011 36-b012 36-b013',
  '11月28日作者谈银行股是大盘风向而非叫读者立即买；以招行有效过历史高位观察市场空间，并明确不预测招行能否50元。',
  '指数走势背离|主力资金|确认|追高', 3, '25/30/50及深发展叙述是历史作者比价/预期，未独立证实，也不是当前目标价。', ['2006年11月28日招行/银行板块评论'])
c(10, 'avoid-all-averages-downward-spread', '36-b016 37-b000',
  '对002037作者要求不要在所有均线向下发散时买，认为风险大；当时中小板扩容与小非压力是其背景解释。',
  '均线|均线系统|市场风险', 2, '跨页读完等待语句，未把单条线略下或所有反向方法都等同该情形，背景因果未外核。', ['2006年11月28日002037问答及均线发散状态'])

c(11, 'technical-one-of-three-systems', '37-b002',
  '作者要求技术分析放在三个独立系统中使用，单纯技术或单纯非技术都不足。',
  '独立系统|技术分析', 1, '本段未列其余两者名称，不把其他来源定义假托为本段明说；与72课具体三系统可另行查证。')
c(11, 'technical-analysis-core-classification', '37-b003 37-b004',
  '作者把技术分析核心放在分类：指标按自己的视角区分可操作与不可操作情形，信号不是上帝暗示，也不保证所对应情况百分百兑现。',
  '技术分析|完全分类|确认', 1, '完全分类是评价框架，不等指标100%预测实际路径；作者对成功者评价不是独立统计。')
c(11, 'averages-evaluation-not-single-cross', '37-b005',
  '均线系统在本课是若干短中长期均线的评价系统；作者提醒单条尤其短线突破买、跌破卖易有骗线。',
  '均线系统|均线|假突破', 1, '不精确和骗线风险保留，不将其评估用法改成突破即充分买点或项目胜率结论。')
c(11, 'relative-strength-five-versus-ten', '37-b005',
  '同一走势可在5日线上而在10日线下，相对5日评价强、相对10日评价弱，强弱需说明所选评价标准。',
  '均线系统|均线|确认', 1, '两线相对评价不同不构成事实矛盾，也不由某一强势自动代表所有周期强势。')
c(11, 'parameters-capital-time-t0-context', '37-b006',
  '技术指标系统参数应先按资金量和操作时间选择；超短可看1分钟强势，尤其T+0情形，而大资金未必看重日线5日强势。',
  '均线系统|操作级别|交易规则|资金管理', 1, '原文1分钟钱为排版词形，未改原文；示例不是1分钟强势就任何人能买或周期等严格级别。', ['按实际资金与操作时间','1分钟示例特别注明T+0背景'])
c(11, 'average-position-short-above-long-bull', '37-b007',
  '作者把两条均线的短线上、长线下称女上位，对应该系统多头；短线下、长线上称男上位，对应该系统空头，并以吻给两线关系分类。',
  '均线体位|均线系统|飞吻|唇吻|湿吻', 1, '体位是均线相对位置比喻，不是对市场所有级别永久牛熊或社会性别论断。')
c(11, 'flying-kiss-definition', '37-b008',
  '飞吻指短期均线略走平后继续按原趋势运行。',
  '飞吻|均线系统', 1, '原文没有以两均线交叉定义飞吻，也未给略走平数值阈值。')
c(11, 'lip-kiss-definition', '37-b009',
  '唇吻指短期均线靠近长期均线而不跌破或升破，随后按原趋势继续。',
  '唇吻|均线系统', 1, '靠近而未穿越是定义条件，双向不跌破/不升破依原趋势；不改成两线已交叉。')
c(11, 'wet-kiss-definition', '38-b000',
  '湿吻指短期均线跌破或升破长期均线，甚至出现反复缠绕。',
  '湿吻|均线系统', 1, '甚至反复表示可进一步缠绕，不把反复多次误作所有湿吻必需；方向对称。')
c(11, 'flying-kiss-strong-trend-and-later-shake', '38-b001',
  '作者认为飞吻出现较少，一般在特别强的趋势中，过强难久、其后常震荡；这是他对该均线形态的经验描述。',
  '飞吻|均线系统|市场震荡', 3, '频率与寿命无数据，不能据本课给确定概率、延续天数或收益。', ambiguity='qualitative_frequency_not_empirically_verified')
c(11, 'lip-kiss-position-continuation-and-wet-risk', '38-b001',
  '作者把唇吻视为基本趋势常见形式：男上位中反弹常趋结束，女上位中调整结束可能较大，但须防唇吻转湿吻。',
  '唇吻|湿吻|均线体位|反弹|确认', 1, '可能和湿吻演化保留，不将接近未穿越瞬时状态看作未来必延续。', ['按均线体位区分原趋势方向'])
c(11, 'wet-kiss-adjustment-and-turn-context', '38-b001',
  '作者说湿吻常见于一段趋势后的较大调整或转折，长期男上位后短中长期均线一同缠绕尤其值得观察重大变化。',
  '湿吻|均线系统|趋势转折', 2, '值得观察不等已经完成转折，未给同时缠绕的精确阈值或统计概率。')
c(11, 'wet-kiss-two-turn-paths-first-exception', '38-b002',
  '作者列湿吻后两类转折演化：先续原趋势制造陷阱后转折，或反复缠绕成转折箱体；长期男上位后的湿吻再下跌可关注空头陷阱，但明确不适用于趋势形成的第一次湿吻。',
  '湿吻|空头陷阱|均线体位|趋势转折|完全分类', 1, '第一次湿吻例外不能省；行情转折很大几率和陷阱概率大均作者经验，无项目统计。', ['本段湿吻/长期男上位语境'], exceptions=['趋势形成的第一次湿吻不适用该空头陷阱介入判断'], ambiguity='first_wet_kiss_exception_and_unverified_probability')
c(11, 'wet-kiss-direction-not-guaranteed-profit', '38-b002',
  '作者虽说湿吻之后必有高潮，仍强调关键是辨别多空体位而非只问有无行情变化。',
  '湿吻|均线体位|确认', 3, '必有高潮是原文强措辞，可能转为相反方向，不等任一湿吻买入无风险；12课明确不能100%确认中继转折。', ambiguity='author_absolute_movement_rhetoric_not_profit_guarantee')
c(11, 'nov29-skill-strong-stocks-or-five-line', '38-b004 38-b005',
  '11月29日作者按能力分开：有技术者在急跌选相对不跌股票、打短差或换股，技术一般者等5日线站稳。',
  '操作熟练程度|板块轮动|均线|确认', 1, '上午与下午日期分开，机会不等任何人应立即抄底。', ['2006年11月29日该湿吻急跌/震荡','按操作技术能力选择'])
c(11, 'nov29-five-line-three-strength-branches', '38-b006',
  '作者以5日线分次日震荡强弱：强则线上整固，一般围绕折腾，弱还会再下探；站稳后才看继续冲击。',
  '均线|完全分类|确认', 2, '三情形为11/29当时后续分类，不把还未到次日的分支当实绩。', ['2006年11月29日该次日震荡分类'])
c(11, 'nov29-shenzhen-sensitivity-historical-view', '38-b008 38-b010 39-b002',
  '作者当时认为深成指较沪指敏感，偏好先过6103历史高位再由上海跟上、后调整的路径，并明确以建议表达。',
  '指数走势背离|确认|宏观市场判断', 3, '11/30附录引11/29建议不作新回复，历史指数敏感性和健康程度未独立验证。', ['2006年11月29日建议与11月30日明示附录'])
c(11, 'nov29-bank-adjust-triangle-flag-not-date', '39-b007',
  '面对银行股能否12月11日前调整好的提问，作者未给固定到位日，而说更长上升三角或旗形整理有利，招行历史高位突破仍作风向观察。',
  '三角形整理|确认|操作策略', 2, '旗形未另建为严格中枢类型；保持提问时间限制与回答未承诺日期的区别。', ['2006年11月29日银行股问答'])
c(11, 'nov29-resistance-needs-volume-case', '39-b010',
  '对600498作者以下降压力线突破及成交量堆积为观察，不把触线本身视上升空间已打开。',
  '成交量|突破|确认', 2, '当天刚触及与未来一旦突破分开，科技股必表现是历史预期。', ['2006年11月29日600498短线问答'])
c(11, 'thirty-average-hold-acceleration-exception-case', '39-b013',
  '对000851作者说30天线有效跌破前可中线持有，但出现放量加速上涨是明确例外。',
  '均线|成交量|持股|确认', 1, '不能删掉放量加速例外或把该股30天线普遍化为所有持股规则。', ['2006年11月30日000851问答'], exceptions=['出现放量加速上涨'])

c(12, 'any-entry-risk-no-perfect-kiss-prediction', '39-b018 40-b000',
  '作者明确任何位置介入都存在风险，行情未走出前连均线采用哪种吻也无人能100%预知，妄求投资绝对无风险不可行。',
  '市场风险|均线系统|操作策略|走势预测', 1, '跨页完成否定句；不把分类可操作等同风险消失，与后文作者绝对安全措辞分别按范围记录。')
c(12, 'risk-classification-to-buy-sell-hold', '40-b001',
  '按资金与能力建立分类评价及对应程序，出现相应情形再执行买、卖或持有；本段把N种分类对应三种操作，并暂不讨论资金管理的数量。',
  '完全分类|机械化操作|仓位|操作策略', 1, '数量暂省是论述范围，不是实际交易无需仓位；所有可能的完整性为作者方案要求，未由模型自动证明。')
c(12, 'five-ten-position-and-entanglement', '40-b002 40-b003',
  '在5/10日系统中，5日在10日上为女上位、反之男上位，另有缠绕；缠绕完成后可能原体位中继或转换体位。',
  '均线体位|均线系统|完全分类', 1, '缠绕过程中与完成后分开，不由当前一个交叉提前断言最终体位。', ['本例5/10日均线系统'])
c(12, 'long-bear-reversal-bull-continuation', '40-b002 40-b004',
  '作者在该均线多头方案中关注男上位最后缠绕的转折与女上位第一次缠绕的中继，做空方向反向理解。',
  '均线体位|均线系统|均线系统第一买点|均线系统第二买点', 1, '该两均线买入入口不与后文严格第一/第二类买点合并；哪次最后不能事前百分百确认，须结合后续背弛判断。', ['选择本节均线买卖系统','多头方案，空头反向'])
c(12, 'first-bull-entanglement-force-volume-conditions', '40-b003',
  '作者认为女上位初次缠绕中继可能较大、第三四次转折可能增加；初次前5日应强劲，成交量不宜过大，骤放又骤缩会增骗线或延长缠绕并再缩量。',
  '均线体位|均线系统|成交量|假突破', 1, '次序、力度与成交量联合语境保留，不能把任一初次缠绕当100%中继；原文概率未给样本。', ['本节女上位缠绕的辅助判断'], ambiguity='qualitative_entanglement_probability_without_sample')
c(12, 'bear-last-entanglement-divergent-drop-entry', '40-b004',
  '作者寻找男上位最后缠绕转折后急跌而背弛的空头陷阱；他说不能100%预知哪次是最后，同时说一般男上位后首次肯定不是最后一次，第二次起才可能。',
  '均线系统第一买点|均线体位|背驰|空头陷阱', 1, '原文“第一次肯定不是”是该系统判断，未证明跨所有走势无例外；背弛后课将专门论述，不补早文尚无的严格中枢定义。', ['本节均线抄底系统','男上位最后缠绕后急跌且背弛'], ambiguity='last_entanglement_not_ex_ante_certain')
c(12, 'two-average-buy-points-not-risk-free', '40-b005 41-b000',
  '该均线系统第一买点是男上位最后缠绕后背弛的空头陷阱，第二买点是女上位首次缠绕低位；作者称风险收益较优，但明确两者并非没有风险。',
  '均线系统第一买点|均线系统第二买点|均线系统|市场风险', 1, '第一点把中继误为转折或误判背弛、第二点把转折误为中继的风险都保留；没有实测最优收益比。', ['第12课均线系统入口'], ambiguity='average_system_points_not_strict_class_one_two_points')
c(12, 'two-entry-errors-and-skill-not-changing-principle', '40-b005 41-b000',
  '作者把两均线买点的主要误判分为转折/中继或背弛判断错误，熟练度可影响判断，但在选择该系统后买点原则不随熟练度改变。',
  '均线系统第一买点|均线系统第二买点|操作熟练程度|市场风险', 1, '能力提高不等风险消灭，也不把所有交易损失仅归这三种错误。')
c(12, 'system-only-two-principle-and-later-clarification', '41-b001 43-b007 43-b008',
  '作者先要求选择该均线系统就按两个买点原则，随后澄清并非其他点不能买，而是风险更大；这也只是一招，不能只靠这一招。',
  '均线系统|均线系统第一买点|均线系统第二买点|市场风险', 1, '保留正文原则与12:30答复的明确限定，不用正文一句否定后文可承更高风险的说法，也不把早期两点等同后课所有合法买点。')
c(12, 'parameters-fund-size-and-minute-use', '41-b001',
  '作者说该均线参数可按资金调整，资金越大参数相应越大，具体需摸索；短线可由日线换分钟线使用。',
  '均线系统|资金管理|操作级别|周期K线图', 2, '未给资金到参数的精确公式，分钟图不直接等严格走势级别，制度执行限制仍在。')
c(12, 'two-average-sell-points', '41-b001',
  '该均线系统买入后等待卖点：女上位缠绕后出现背弛为第一卖点，转男上位后首次缠绕高点为第二卖点。',
  '均线系统第一卖点|均线系统第二卖点|均线系统|背驰', 1, '卖点身份仅本均线系统，不能等同后课严格第一/第二类卖点；前后体位与首次条件不删。', ['选择本课均线买卖系统'])
c(12, 'prefer-second-buy-first-sell-asymmetry', '41-b002',
  '作者对该均线系统一般偏好在第二买点买，而尽量在第一卖点卖，明确买卖选择有不对称。',
  '均线系统第二买点|均线系统第一卖点|操作策略', 1, '一般最好与尽量是偏好，不改成必须或所有交易系统统一要求。', ['本课均线买卖系统'])
c(12, 'maotai-aug7-sep14-average-examples', '41-b004 41-b005 41-b006',
  '作者以茅台5/10日为例：8月7日男上位第二缠绕后跌、量等背弛及小空头陷阱，为41元附近第一点；9月14日女上位首缠绕下跌，为44元附近第二点。',
  '均线系统第一买点|均线系统第二买点|均线系统|成交量|空头陷阱', 2, '近似价与该历史样本保留，黑白图来源仍未核，2011重绘黄框时刻不改课程正文；不认证已复算全部K线/均线。', ['第12课茅台日线5/10案例'], figs=((41, 1), (42, 1)))
c(12, 'maotai-ten-hold-no-sell-yet', '41-b007 42-b000',
  '在该茅台案例当时，作者说10日线不有效跌破仍持有等缠绕后背弛第一卖点或转男上位首缠绕高点第二卖点，因当时两者尚未出现。',
  '均线系统第一卖点|均线系统第二卖点|均线|持股|确认', 1, '跨页读完当时尚未出现，图右端或当前价格不能反填卖点已经发生。', ['第12课该茅台历史案例'])
c(12, 'observe-buy-hold-sell-not-price-targets', '42-b002',
  '作者说自己观察买点出现后介入、持有等卖点，不以问将涨跌多少或猜空间作为该操作流程。',
  '操作策略|走势预测|买点|卖点|持股', 1, '不据该段抹去其他历史预测存在，区分作者操作原则和聊天式价格展望。')
c(12, 'dec1-five-line-and-shenzhen-gap', '42-b004 43-b000 43-b001',
  '12月1日作者以5日线站稳看轮动，并提醒深成指当日缺口若很快补属不利信号；下周及12月上冲后的大震荡仍是未来展望。',
  '均线|缺口|板块轮动|确认', 2, '三个来源分上午与收盘；沪深管理者竞争的匿名因果不作独立技术证明。', ['2006年12月1日该沪深指数情景'])
c(12, '000958-weekly-two-points-not-best-now', '43-b005',
  '答000958时作者用5/10周系统，称7月22日约2.2元背弛为第一点、11月3日约2.6元首女上位缠绕为第二点；当时非不能买，只是最好位置已过，大资金可先看月线、短线参日线。',
  '均线系统第一买点|均线系统第二买点|均线系统|周期K线图|资金管理', 2, '原答复未写两点年份，不据后加图补2005；不因最佳点已过去改成绝对禁止买，选周/月/日依资金和期限。', ['2006年12月1日000958答复'], figs=((43, 1),))

keep('37-b002', 'upper-l019-analysis-system lower-l072-c-stage-three-systems-division', '11课仅说三个系统不列名称；19及72有进一步解释，未由11单段宣称数理独立已经证明。')
keep('37-b005 40-b004 41-b001', 'lower-l072-c-stage-averages-auxiliary-horizons upper-l024-c-stage-center-replaces-kiss-macd-auxiliary', '早期均线系统买卖点与后期中枢/形态动力学明确区分，不把吻或两均线点直接升级严格三类点。')
keep('35-b005', 'lower-l094-c-stage-t1-same-day-exit-impossible-risk lower-l106-c-stage-jul14-t1-limits-precise-small-level-operation', '早期没有T+0的早盘限制与后期T+1限制相互取证，原来的两类例外保留。')
keep('40-b001', 'lower-l068-c-stage-operations-piecewise', '12课N分类到买卖持有与68分段操作可互查，完全分类不自动证明收益。')
keep('39-b018 40-b000', 'lower-l107-c-stage-segment-from-first-rise-author-safety-wording', '12任何位置有风险与107分段安全措辞并列其范围，不把一个词相同就宣布互相撤回。')

issue('average-points-vs-strict-classes', '37-b005 40-b004 40-b005 41-b001 41-b002 43-b005',
      '早期5/10均线第一第二买卖点未按后课中枢三类点定义，买二卖一是该系统偏好；24/72明确均线辅助范围。',
      '建立均线系统专属点概念，保留后课不同体系，不把早期点直接映射严格一二类点。', True)
issue('probability-and-absolute-wording', '28-b004 32-b004 38-b001 38-b002 40-b003 40-b004 40-b005',
      '99.99%修辞、所有亏损/困难归因、湿吻必高潮/首次肯定非最后、最优风险比皆无独立样本证明。',
      '保留作者意见和例外，以12课任何位置有风险/不能100%预测限制，不输出项目统计或无损保证。')
issue('two-points-only-and-risk-clarification', '41-b001 43-b005 43-b007 43-b008',
      '正文选该系统只在两点买与后文其他点也可但风险更大明确并存，且只是一招。',
      '按作者后文明确限定记录，不改成所有别点被严格禁止或一招包办全部操作。', True)
issue('source-replay-and-unknown-old-name', '32-b013 32-b014 33-b004 33-b005 33-b006 34-b000 34-b001 34-b002',
      '外层11/27独立文章自称转录喜欢数学的女孩2005旧文，原站作者身份及最早7月/现存8/5未外证。',
      '转载段改unknown及实际署名，原文保留但不作直接作者命题；不把外层11/27文章误留11/24回复。', True)
issue('dates-in-previous-block-and-source-identity', '30-b001 30-b001-s01 30-b002 30-b005 34-b003 38-b004 39-b001 42-b004 42-b005 42-b006',
      '解盘和引号自引曾误作读者；裸日期在前段尾，引用旧建议不是新回复，课程10仅11-24。',
      '54段源元数据已核改，混合段正文不改、引用不包含下一日期；课程10不补无证时分秒。')
issue('parameters-valid-break-and-volume-algorithm', '31-b018 35-b005 37-b006 37-b009 40-b003 41-b001',
      '有效突破/走平/靠近/放量过急及资金到参数未给完整算法；早盘通常不买有强突破与中线逐步建仓例外。',
      '保留原文语义条件，不自行补阈值或把经验系统写成已交付交易程序。', True)
issue('figures-originals-vs-reconstruction', '29-b003 35-b011 41-b004 41-b005 41-b006 43-b005',
      '六图中三图有后期行情或2011行情栏/整理文字，另三图原作者仍未核；000958原文无年份而后图补2005。',
      '三后加三未核分别保留，所有文字命题独立取证，不补原文日期/年份、不拿图箭头认证严格买点。')
issue('macro-rhetoric-and-reader-context', '27-b010 28-b001 33-b001 36-b008 36-b011 36-b013 42-b006',
      '人民币/股改因果、三轮牛市/银行风向/沪深管理者动机为历史自述与预测，读者持仓收益及满仓赌局不作作者一般规则。',
      '保留案例身份和条件，不作当前宏观事实、价格目标或收益回测。')

note('27-b010 27-b011 28-b000 28-b002 28-b006 29-b000', 'author-personal-and-metaphor-context',
     '重看股票经历、股改文章、论语与4N9/性比喻、下节预告全文跨页已读。', '历史身份/性比喻不是形式金融定理，不执行辱骂或伤害修辞，不把长久承诺当收益保证。')
note('29-b001 30-b001 32-b011', 'author-introduction-or-nonmarket-answer',
     '即时提示序言、明确自引昨日提示，以及数学读物须看孩子兴趣的答复已读。', '不把非证券答复抽为投资定理，序言只用于确定自引身份。')
note('30-b014 31-b000 31-b001 35-b004 36-b004', 'historical-case-retained',
     '600436的17/18与15.5/19.6箱体、600832年线11.4、000004的4/4.2、600426的9/11箱体案例完整已读。',
     '当时个股未独立复算，保留原文查询及案例范围，不制造普遍价格常数或重复一般节点。')
note('32-b013 32-b014 32-b015 33-b002 33-b003', 'replay-outer-article-context',
     '11/27新标题、旧站帖子失效/自称旧名、G股与大牛不用套阶段及抄袭自述已读。',
     '外层作者自述与旧文署名分开，未核原站链接/先知主张；33-b000/001技术阶段另抽。')
note('33-b004 33-b005 33-b006 34-b000 34-b001 34-b002', 'unknown-self-claimed-reprint-context',
     '2005-8-5 12:15署名喜欢数学的女孩的经济论坛旧文和跨页续文已读；外层作者自称旧名。',
     '不是读者但原站身份未核，保留unknown和署名，不通过改标签成为直接作者技术证据。')
note('34-b003 34-b014 34-b015 35-b000', 'commentary-transition-and-rhetoric',
     '11/27解盘结束语/11/28应酬近况及AV修辞已读，时间头和跨页完整。', '正文结束语不是读者署名，性修辞不当操作成功证明。')
note('36-b008', 'historical-sector-forecast', '中低价补涨/强板块补涨与新板块大高潮待下轮调整后的历史预测已读。', '所有板块都会动一次为作者当时预期，未外核且不当永恒板块轮动法则。')
note('38-b007 38-b009 39-b000 39-b001 39-b016', 'historical-index-and-stock-case-context',
     '个股比指数重要、下次调整更大、11/30突破回试/银行资金争夺、600857涨后整固再放量案例已读。',
     '作者走势自评与匿名管理者因果未核，600857只保留该次案例，不泛化再次放量必涨。')
note('41-b003 42-b001 42-b003 42-b005 42-b006 42-b007', 'introductory-and-historical-commentary-context',
     '例子引言、补充说明、脱胎换骨劝学及12/1午间和收盘沪深竞争/个股行情评论已读。',
     '沪深管理者动机和牛市深圳必强是历史作者经验未外证，不将误识别的段落当读者观点或当前市场判断。')

relations = {
    'upper-l011-c-stage-technical-one-of-three-systems': [('技术分析', '独立系统', 'related')],
    'upper-l011-c-stage-technical-analysis-core-classification': [('技术分析', '完全分类', 'requires')],
    'upper-l011-c-stage-average-position-short-above-long-bull': [('均线体位', '均线系统', 'related')],
    'upper-l011-c-stage-flying-kiss-definition': [('飞吻', '均线系统', 'related')],
    'upper-l011-c-stage-lip-kiss-definition': [('唇吻', '均线系统', 'related')],
    'upper-l011-c-stage-wet-kiss-definition': [('湿吻', '均线系统', 'related')],
    'upper-l012-c-stage-two-average-buy-points-not-risk-free': [('均线系统第一买点', '均线系统', 'related'), ('均线系统第二买点', '均线系统', 'related')],
    'upper-l012-c-stage-two-average-sell-points': [('均线系统第一卖点', '均线系统', 'related'), ('均线系统第二卖点', '均线系统', 'related')],
    'upper-l010-c-stage-morning-entry-t0-exceptions': [('交易规则', '操作级别', 'qualifies')],
}
for r in rows:
    r['relations'] = [{'source': a, 'target': b, 'type': t} for a, b, t in relations.get(r['id'], [])]

by_passage = defaultdict(list)
for r in rows:
    for e in r['evidence']:
        by_passage[e['passage_id']].append(r)
for item in pending:
    item['lesson_numbers'] = sorted({int(passages[x]['unit_id'].split('-')[1]) for x in item['passage_ids']})
    if item['id'].endswith('figures-originals-vs-reconstruction'):
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
        result, reading, atomic, inverse = 'reader_context', '读者署名、问题、持仓/价格与评价已读，用于限定相邻作者回复。', [], '读者的建议/成绩/观点不因作者回复就成为作者命题。'
    elif p['text'].startswith('教你炒股票') or p['text'] in ('缠中说禅解盘:', '缠中说禅解盘：', '缠中说禅回复:', '缠中说禅回复：') or re.fullmatch(r'.*200[5678]-\d{1,2}-\d{1,2}.*', p['text']) and (len(p['text']) < 75 or p['text'].startswith('缠中说禅')) or p['text'].startswith('会吻，才有高潮'):
        result, reading, atomic, inverse = 'source_header_or_ending', '课程/解盘/回复标题、作者时间头或结束语已读并核对。', [], '仅作来源定位，不独立支持技术结论。'
    else:
        raise AssertionError(('unaccounted paragraph', id, p['text']))
    if linked and decision:
        reading += '；其余语境：' + decision['reading']
        inverse += '；' + decision['inverse']
    ledger.append({'passage_id': id, 'lesson_number': int(p['unit_id'].split('-')[1]), 'document_id': DOC,
                   'pdf_page': p['pdf_page'], 'role': p['role'], 'speaker': p['speaker'], 'published_at': p['published_at'],
                   'source_text_sha256': hashlib.sha256(p['text'].encode()).hexdigest(), 'result': result,
                   'claim_ids': [r['id'] for r in linked], 'related_existing_claim_ids': retained[id], 'existing_evidence_not_mutated': True,
                   'pending_issue_ids': [x['id'] for x in pending if id in x['passage_ids']], 'reviewer': REVIEWER,
                   'rounds': {'1_read_and_scope': reading, '2_atomic_conditions': atomic,
                    '3_normalization': {'concept_labels': sorted({x for r in linked for x in r['concepts']}),
                    'related_existing_claim_ids': retained[id], 'note': '均线系统两买卖点与后课严格三类点分开；吻/体位定义和早期参数/概率、原文/后加图及回放/读者身份分层。'},
                    '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True, reviewer=REVIEWER, visual_review_note=f['note'],
             figure_source_review='6图均实际看整图；3后加、3原作者未核，图中时间/年份/箭头不改正文。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 213 and Counter(x['lesson_number'] for x in ledger) == {10: 135, 11: 43, 12: 35}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
           'lessons': [10, 11, 12], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger),
           'claims': len(rows), 'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
           'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)),
           'whole_lesson_semantic_read_complete': True, 'technical_extraction_complete': False, 'four_round_review': True,
           'independent_review_claimed': False, 'visual_pdf_pages': list(range(27, 44)), 'figure_objects_viewed': 6,
           'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)), 'pending': [x['id'] for x in pending],
           'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True, 'database_mode': 'ro', 'formal_import': False,
           'acceptance': '第10至12课213段17页6图同模型四轮；54源修正、均线两点与严格三类点、吻/体位/概率及原文/后加图分开，增量待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close()
sys.stdout.reconfigure(encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False))


