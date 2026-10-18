"""Materialize the main agent's four-pass reading of lesson26.

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
BASE = 'c_stage_l026'
REVIEWER = 'Codex 主代理 / 阶段C上册26课同模型四轮复核'
SOURCE_SHA = 'eb8dbdd15cfc0e639240d9db325d7e280147698433e1770fd8147e597f1f1d43'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-026' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 141
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 166 AND 178 ORDER BY pdf_page,id', (DOC,))]
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
    pending.append({'id': 'upper-l026-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})


c(26, 'technical-risk-reflected-in-price-author-view', '166-b007',
  '第26课从纯技术角度，把政策、系统、交易、流通和经营等风险最终都归入价格走势波动；高市盈率但持续上涨的例子须按技术衡量。',
  '市场风险|走势|技术分析|基本面', 1, '纯技术角度是原话限定，不等项目证明所有现实风险可预知或基本面永远无用；本课后文中长线选股另要求基本面。',
  ['作者关于纯技术风险衡量的观点'], ambiguity='all_risks_price_reflection_is_author_doctrine_not_external_proof')
c(26, 'foreseeable-trading-continuation-level-horizon', '166-b008',
  '作者把交易品种在可预见时间内可继续交易列作理论重要前提：日线操作若一周后停止交易便不合前提；1分钟操作对已知一周后终止的风险可有不同控制尺度。',
  '交易延续|交易条件|操作级别|市场风险', 1, '可预见时间与操作级别联合，不把一周这个例子推广成统一安全天数或1分钟必能免损。')
c(26, 'sudden-stop-or-cancellation-invalidates-premise', '166-b008 167-b001',
  '未知何时突然停止交易、或交易事后不算，作者说是技术最大死穴，理论前提失效；对将停止的品种他反对再用理论赌博。',
  '交易延续|交易有效性|停牌风险|赌徒心理|市场风险', 1, '突然终止/不算与下条普通停牌分别保留，不能把技术万能口号覆盖这一明确例外。')
c(26, '319-last-exit-not-from-chart-self-report', '166-b008 167-b001',
  '作者用327交易不算及319退出经历说明制度风险，自述319最后一天平仓并非看图，而是受此前交易取消教训、先退出防再次不算。',
  '交易有效性|市场风险|期货|技术分析', 3, '327/319交易及后续转股涨幅是作者自述，未查账或独立历史核验；明确非图形信号的归因不能改为技术成功预判。',
  ['第26课作者自述国债期货经历'], ambiguity='autobiographical_trades_unverified')
c(26, 'ordinary-suspension-vs-permanent-stop-author-claim', '167-b001',
  '在交易延续、交易算数前提下，作者称理论没有盲点；他又说停牌之类不影响风险控制，前提是走势不会被突然停止而永远没有。',
  '交易延续|交易有效性|停牌风险|市场风险', 1, '普通停牌和突然永久终止的原文范围分开；没有盲点/控制一切是作者未证明强主张，不保证停牌期间或复牌跳空可执行止损。',
  ['交易继续且有效的作者理论论述'], ambiguity='ordinary_suspension_and_absolute_control_claim_unproven')
c(26, 'capital-deadline-self-imposed-trading-stop', '167-b001',
  '作者指出资金有限期等于自行设置交易停止时限，透支失败常属此类；投入的钱最好无期限，若有期限也须足够长。',
  '资金期限|交易延续|资金管理|市场风险', 1, '足够长相对策略与可交易性，不补统一月数；作者的常见失败比例无统计样本。')
c(26, 'deadline-lower-frame-last-resort', '167-b001',
  '对于有期限的钱，作者只把降低操作级别以尽量控制期限风险称为没有办法的办法，并说最好别出现这种情况。',
  '资金期限|操作级别|市场风险', 1, '尽量控制不等消除资金期限或允许借贷；与后1月31长期资金、不能借贷的提醒共同保留。')
c(26, 'bad-news-prior-price-reflection-author-claim', '167-b002',
  '作者认为坏业绩和消息影响会先反映在资金运动与走势中，未知消息不等于无人知道；基本面、消息面最终要落实到走势观察。',
  '走势|基本面|公开信息|市场合力', 2, '一切必然事先反映是作者主张，不作为项目已证实的信息效率定理或突发风险可无损交易证明。',
  ['第26课对坏消息如何处理的论述'], ambiguity='universal_prior_information_reflection_unproven')
c(26, 'stock-as-exchange-certificate-trading-view', '167-b003 168-b000',
  '作者从交易角度把股票看作一笔钱经过时间换成另一笔钱的凭证，反对对股票产生感情，并把获益归于操作者能力而非股票本身。',
  '交易规则|操作策略|市场心理', 2, '废纸/基本面胡诌是该段交易修辞，不当法律上的股票权利定义；后文谨慎中长线择股仍看基本面。')
c(26, 'positive-cost-risk-and-negative-cost-ambition', '168-b001',
  '作者先说0以上价格交易都包含不能换回更多钱的风险，又提出把持有凭证变成“负价格”作为理论目标，并称这才可毫无风险、永远不败。',
  '负成本|成本|市场风险|操作策略', 1, '与后段总体成本降低语境对读，不把负价格改成证券市场报价为负；风险消失/永不败为作者强主张，未作实证或形式证明。',
  ['第26课摊低持有成本的理论目标'], ambiguity='negative_cost_not_negative_quote_or_verified_zero_risk')
c(26, 'bidirectional-differences-and-trade-quantity', '168-b002',
  '作者说先买后卖与先卖后买均可降低总体成本，任意级别买卖点都可参与，但须控制数量；他以日线通常参与量大于1分钟说明级别与数量关系。',
  '负成本|资金管理|仓位|操作级别|缠中说禅短差程序', 1, '本段级别基本只和量有关为该资金操作视角，不能抹去本课后文大级别方向/短差时机要求；不从任意信号保证成本必降。')
c(26, 'minute-fifty-thousand-shares-self-example', '168-b002',
  '作者自举1分钟卖5万股、跌回买回、差1毛钱，扣费可能约4000元；日线可参与100万、1000万股等更大量。',
  '操作级别|仓位|交易成本|成本', 3, '具体数量/价差为自述示例，4000是作者含手续费可能值，不补现行费率、流动性或账户核验。',
  ['第26课作者资金量与短差操作例'], ambiguity='trade_size_and_fee_example_unverified')
c(26, 'warrant-keep-original-size-no-added-position-self-report', '168-b002',
  '作者自述一只已停交易认购权证最终在1元多出清时成本负2.8元多；其规则是初始买够、卖点减少、买点恢复原数量，绝不额外加仓。',
  '认购权证|负成本|仓位|资金管理', 2, '未具名认购不猜为前课038004认沽；持仓一直不变按其后变少/恢复解释为目标原数量，不改成全过程逐刻股数不变。',
  ['第26课未具名认购权证的作者交易自述'], ambiguity='unnamed_call_warrant_negative_cost_unverified')
c(26, 'volatility-selection-small-vs-large-capital', '168-b003',
  '在降成本目标下，作者说看重波动大但波动不能完全预测；小资金可全仓进出不同品种，此法不适于难随时买足数量的大资金。',
  '资金管理|仓位|市场震荡|操作熟练程度', 2, '不把“市场从无风险”自夸当选择波动股即可无损；全仓进出只是该资金规模/方法语境，日后基本面择股另有限定。')
c(26, 'large-capital-month-week-second-third-buy', '168-b003 169-b000',
  '作者说其大资金一般在月线、最低周线买点入，不追高；多选二三买，通常不在月线一买进入，以免自己变庄家。',
  '操作级别|第二类买点|第三类买点|第一类买点|主力资金|追高', 2, '作者本人资金及策略自述，不推广小资金必须周月或所有一买不值得；庄家进贡等比喻不作可验证操盘证据。')
c(26, 'long-capital-plus-skill-unbeatable-author-formula', '169-b001',
  '本课结尾作者用“足够长的钱＋熟练运用理论＝战无不胜”概括其主张。',
  '资金期限|操作熟练程度|市场风险', 3, '两前提和作者归属明确，等号为原文修辞，不是项目验证的收益保证，也不能覆盖突然停止或交易取消例外。',
  ['第26课风险论述结尾'], ambiguity='author_unbeatable_claim_not_demonstrated')
c(26, 'jan30-five-minute-divergence-and-no-chase', '169-b002 169-b004',
  '1月30日解盘认定早盘5分钟背驰引发调整，提醒震荡中按卖买点往返并反对追高；技术不过关者先练习。',
  '背驰|操作级别|追高|操作熟练程度', 2, '1月30的5分钟不与1月26否定5分而肯定1分混为一件；农业军工等表现和消息自称未独立核实。',
  ['2007年1月30日15:25上证解盘'], figs=((169, 1),))
c(26, 'thirty-minute-strength-changes-rebuy-level', '170-b001',
  '作者要求综合看买点：30分钟很强时1分钟买点也可回补；30分钟很弱时至少等30分钟买点。',
  '操作级别|买点|缠中说禅短差程序', 1, '强/弱未给数值阈值，不把1分钟买点任意套所有市场；回补的原持仓语境保留。')
c(26, '000999-doubled-month-one-minute-not-enough', '170-b004',
  '对000999一月已翻倍却按1分钟买点全仓买入者，作者反问其依据并要求反省，未将1分钟信号认可为洗盘结束。',
  '买点|操作级别|追高|市场风险', 2, '中线肯定没问题是当时作者看法，不验证后来结果；不能把此例变成涨过一倍后任何级别永无买点。',
  ['2007年1月30日对读者11.30买000999的答复'], ambiguity='historical_medium_term_confidence_not_verified')
c(26, 'acquisition-news-final-buyer-price-uncertain', '170-b009 170-b011',
  '作者反对据记者“如无意外”报道就断定三九买家，称谈判到最后买家与价格仍是多方较力，需考虑收购价能否支持股价并落实走势。',
  '公开信息|基本面|走势|市场风险', 2, '记者及读者转载不是作者事实；作者自称有准确信息不认证消息来源或现今收购情况。',
  ['2007年1月30日三九收购问答'], ambiguity='author_information_and_acquisition_claims_unverified')
c(26, 'recognition-vs-execution-size-stock-index', '170-b014',
  '作者把看出信号与实际操作分开，强调操作还涉及数量及个股与指数的差异，须实践提高。',
  '买卖点|仓位|操作熟练程度|指数走势背离', 2, '没有逐项认可读者所称5分钟回拉无中枢，不把看到信号等成已经可执行盈利。')
c(26, 'large-frame-before-short-trade-up-down-sides', '171-b000 171-b003',
  '作者要求先判断日线等大级别：震荡适于短差，日线上涨中过多短差易夹空、下跌中易被套；一般看5分钟或更长，末段急拉再配1分钟。',
  '操作级别|操作熟练程度|市场震荡|追高|缠中说禅短差程序', 1, '上涨卖后应及时买回与不得追高须共同保留，不能为赶回补而取消买点条件；纯1分机械执行受到本条限制。')
c(26, 'cautious-entry-and-midterm-cost-repair', '171-b004',
  '作者要求宁可买不到也不要卖不出，进入应慎重；若中线仍看好且有短线技术，他认为被套可用短差降成本修复。',
  '市场风险|成本|操作熟练程度|持股', 2, '中线看好和熟练技术是有条件修复范围，不指任意被套不退出或保证回本。')
c(26, 'master-quantity-and-small-capital-qualification', '171-b005 172-b002',
  '作者说高手须能长短并用并控制出入数量，这对小资金意义较小；选择图级别先看自身资金量，除非很大不必先按股票盘子定，退出级别须综合走势。',
  '仓位|资金管理|操作级别|流通量', 1, '不把量比买卖点更重要这一资金操作观点推广成大资金可忽略信号；原文量与不同级别的综合限制并存。')
c(26, 'small-capital-can-switch-to-larger-buy-point', '171-b008',
  '作者说不必专守一股，可换着做；30分钟买点比1分钟更有吸引力，对小资金尤其如此。',
  '资金管理|操作级别|买点|操作策略', 2, '可以适当不是要求无条件换股，也不是只因级别大就可省买点形成。')
c(26, 'index-signal-only-if-stock-aligned', '171-b011',
  '对尾盘个股急跌的疑问，作者以早盘指数5分钟背驰为例，但明确以个股与大盘一致为条件；卖点后重心是等买点而非猜中间路径。',
  '指数走势背离|买卖点|走势预测|操作级别', 1, '如果一致的条件不能删除，不把所有个股急跌都归同一指数卖点或验证庄家集体意愿。')
c(26, 'jan31-stable-long-funds-no-borrowing', '172-b011',
  '1月31日作者重申股市中的钱应能长期稳定留下，不能有借贷之类情况，并将许多失败归于资金非长期性。',
  '资金期限|资金管理|市场风险', 1, '是原文资金原则，未提供失败样本比例；与降低级别应对期限风险的无奈例外并列，不把后者当鼓励借贷。')
c(26, 'novice-near-bottom-at-least-daily-entry', '173-b000',
  '作者建议不单做短线，特别新手尽量在至少日线买点、离底部不远处进入；短差用于降成本，可控制如1/3仓位，日线单边上扬除外。',
  '操作级别|买点|仓位|成本|操作熟练程度', 1, '最好/特别新手及单边上涨例外保留；日线买点是结构条件，不改为日历周期或任意相对低价。')
c(26, 'long-entry-fundamentals-short-tech', '173-b002 175-b010 175-b012 175-b013',
  '中长线谨慎选股时作者要求参考基本面、不要太烂，短线主要看技术降成本；即使自称任何股可变负成本，也仍主张挑好一点的。',
  '基本面|操作级别|负成本|操作策略', 1, '与正文纯技术风险/股票无须选择的特定视角分开，不把整课简化为完全不看基本面；永不败仍是作者主张。')
c(26, 'long-selection-not-casual-cut-conditional', '173-b005',
  '对原本按中长线谨慎选择、尤其仍看好的持股，作者反对随意斩仓止蚀，主张用短差摊成本，并质疑换股一定更好。',
  '持股|成本|基本面|操作策略', 1, '若谨慎中长线选股和依然看好是原文条件；不覆盖退市、资金到期、基本面不明或前课买点失效防护。',
  ['1月31日补充第7条原则'], ambiguity='conditional_no_cut_loss_stance_not_universal_risk_rule')
c(26, 'independent-practice-habit-review', '173-b003 173-b004 173-b008',
  '作者要求不依赖他人，在实践中形成技术并每次总结坏习惯，也把恐惧贪婪与市场无知联系。',
  '操作熟练程度|市场心理|操作策略', 3, '心态要求不构成收益充分条件，不能由勇敢或无反应推技术正确。')
c(26, 'feb1-weaker-one-minute-rebound-and-cash-profit', '173-b011 173-b014 174-b000',
  '2月1日作者称指数1分钟背驰反弹力度不及上次；震荡中不熟练者宁早卖兑现差价，没条件则中线持有，但须非烂股、非追高。',
  '背驰|操作级别|操作熟练程度|基本面|追高', 2, '两条件跨页完整保存，时间按嵌头修为2/1而非1/31；不能把较弱反弹视为卖点已指定某时价。',
  ['2007年2月1日15:32上证解盘'], figs=((174, 1),))
c(26, 'chihong-center-jul27-aug26-no-average', '175-b003',
  '对驰宏日线中枢区间，作者说中枢与均线无关，答“727到826是中枢”，纠正读者7/28至8/4的设想。',
  '走势中枢|均线系统|周期K线图', 1, '读者问题年份2005为上下文，不按旁边上证图补成另一年；原答紧写727/826保留，不从一句补完整三段端点算法。',
  ['第26课1月31日对600497日线区间的答复'])
c(26, 'shanghai-thirty-to-daily-weekly-centers-case', '175-b004',
  '作者以当时上海指数区分中枢规模：此前8月至年底上涨中最多30分钟中枢，今年开始先日线中枢再扩张周线。',
  '走势中枢|中枢扩张|级别|上涨', 1, '此前/今年按1月31日2007语境，图为后加前复权且MJ_PPOS与框线未认证作者，不从图自行重建严格级别换算。',
  ['2007年1月31日21:30上海指数例'], figs=((174, 2),))
c(26, '600316-third-buy-needs-preceding-first-second', '175-b007',
  '面对600316在1月26日明明三买的断言，作者反问前面没有第一二类买点何来第三类，要求先清概念。',
  '第一类买点|第二类买点|第三类买点', 1, '是对该错误识别的回应，不等认可读者三买；未给出一二三时间，也不推出二三必紧接或价序永无例外。')
c(26, '600343-earnings-one-yuan-author-forecast', '175-b011',
  '作者解释自选600343时，自称研究预期2007年业绩达1元、航天将有动作及其他因素。',
  '基本面|走势预测|操作策略', 3, '这是1月31日预测和未披露研究，自称消息不认证真实业绩或事件，不能变成当前推荐或已实现财务数字。',
  ['2007年1月31日作者选股自述'], ambiguity='historical_earnings_forecast_not_verified')
c(26, 'fast-drop-macd-rebuy-size-and-prolonged-fall-exception', '175-b017',
  '对急跌后等均线还是中枢处理的疑问，作者建议MACD，背驰可买或回补、量随级别；大资金不熟练可看30分，小资金5分通常有短差利润，但特别连绵跌势除外。',
  'MACD|背驰|操作级别|资金管理|操作熟练程度', 1, '保留一般/从纯短线/小资金/连绵下跌例外，不把利润足够视为回测结论；图形信号仍需本书其他联合条件。',
  ['1月31日对急跌处理的答复'], ambiguity='typical_short_profit_claim_not_demonstrated')
c(26, '600677-earnings-trap-exit-half-or-small-position', '176-b002 176-b004',
  '对600677业绩风险，作者建议有逃出机会先退出或减半再下补；若仓位不多可先留，重仓等反抽减半再短差降成本。',
  '基本面|仓位|成本|市场风险|反抽', 1, '大小仓位分支完整；先逃或减半的当时判断与不随便斩仓的有条件主张并存，不把反抽一定解套当保证。',
  ['2007年2月1日21:17对600677的答复'], figs=((176, 1),), ambiguity='conditional_recovery_forecast_not_guarantee')
c(26, '600677-earnings-causes-author-research', '176-b002 176-b005',
  '作者自称查得600677亏损与前董事长调查及下属清算有关，虽可能为中线转机仍是兑现前压力；要求了解基本面并等冲击过去再入。',
  '基本面|市场风险|操作策略', 2, '成因和可接受范围为当时作者研究转述，未独立核对公告；不认证事实或推定管理层责任。',
  ['2007年2月1日600677业绩问答'], ambiguity='author_earnings_cause_report_unverified')
c(26, '600677-week250-59-conditional', '176-b003',
  '作者把600677当时约5.9的250周线列为中线关键，要求不有效跌破才谈不入大空头、重新走强可能。',
  '均线|有效跌破|调整|操作级别', 2, '5.9为当日周线位置，不用后加日线未来9.85证明承诺；原文未给有效跌破数值/天数阈值。',
  ['2007年2月1日600677中线条件'], figs=((176, 1),), ambiguity='effective_break_threshold_not_specified')
c(26, 'tcl-recovery-conditional-author-recap', '176-b007 177-b000 177-b001',
  '作者回顾前11月底TCL被套问答，说3.5成本解套可能大、补仓降成本或短差可能获利；两月后称若当事人未走且补仓已可获利。',
  '成本|仓位|反抽|操作策略', 2, '如果未走且补仓是反事实分支，不认证该读者实际执行/利润；与14课一次补/原旧仓的具体范围分开核。',
  ['2007年2月1日对前TCL问答的回顾'], ambiguity='conditional_recovery_self_evaluation_not_account_evidence')
c(26, 'bull-no-light-cut-delisting-exception', '177-b002',
  '作者以套牢50%的例子说牛市不宜轻易斩仓，有相应技术可在原处修复，但明确面临退市的股票除外。',
  '牛市阶段|成本|市场风险|操作熟练程度|交易延续|持股', 1, '牛市/技术/退市例外三者不得删；也不与14买点失效退出来取同一全局优先级。',
  ['2007年2月1日TCL后续提醒'], ambiguity='no_cut_stance_context_and_earlier_protective_exit_need_scope')
c(26, 'larger-short-difference-ten-percent-author-claim', '177-b005',
  '作者提醒不要迷恋1分钟，15或30分钟更需做好，并称短差做好成本至少降10%、往返数次可负成本。',
  '操作级别|成本|负成本|缠中说禅短差程序', 2, '10%为作者条件化收益主张，未提供样本/费用口径；读者自述1%降本不是验证作者10%的数据。',
  ['2007年2月1日21:31短差问答'], ambiguity='ten_percent_cost_claim_not_empirical_benchmark')
c(26, 'unskilled-small-position-quarter-or-third', '177-b006 177-b007',
  '作者主张先买后卖与先卖后买都学；不熟练且仓位不太大可用1/3或1/4参与，卖错宁错过也不能追高回补，只在买点买。',
  '仓位|操作熟练程度|缠中说禅短差程序|追高|买点', 1, '不熟练且仓位不大是比例条件，不混成25课市场很差时1/2的同一范围，也不借及时回补取消买点。')
c(26, '600836-intraday-second-buy-not-chase', '178-b001',
  '对怕错过超强600836的读者，作者指出当日14:30为1分钟第一中枢后零轴回抽二买，若那里买不算追高，拉起后再买则没必要。',
  '第二类买点|走势中枢|MACD|追高|操作级别', 1, '该例时间对应2月1日，图框内另印作者2007-02-01未补1月；一根回轴不等普遍二买充分条件。',
  ['2007年2月1日22:08对600836一分钟案例'], figs=((177, 1),))
c(26, '600836-thirty-minute-first-second-dates', '178-b002',
  '作者给600836的30分钟一买为1月4日10点左右，二买为1月18日11点。',
  '第一类买点|第二类买点|操作级别', 2, '前图1月23旧光标不把问答改期；左右/具体时间按原文，未补作者没说的成交价或证明端点唯一。',
  ['2007年2月1日600836三十分钟回顾'], figs=((178, 1),))
c(26, 'mindset-requires-technical-insight', '178-b005',
  '作者回应预测明日大涨的读者时，强调没有技术保证的无反应心态不够，好心态须由智慧洞察支撑。',
  '市场心理|操作熟练程度|走势预测', 2, '答复不是对读者低开低走/千亿/周线翻红的预言认可；心理与技术仍不构成项目验证的获利充分条件。')

keep('166-b008 167-b001', 'upper-l025-c-stage-imminent-suspension-risk-no-time-to-correct',
     '26把25没时间改错细化为交易可延续/算数前提，另区分普通停牌；不把文字强断言当零风险证明。')
keep('168-b002 173-b006', 'upper-l025-c-stage-short-difference-buy-sell-or-sell-rebuy',
     '先买后卖与先卖后买均是短差入口，本批增加量和期限条件，不变为固定盘中时点程序。')
keep('170-b001 171-b000 171-b003', 'upper-l025-c-stage-rapid-market-one-minute-mobile-exit-not-only-frame',
     '再度要求大级别强弱/方向与快速末段配套，不把1分钟所有环境全仓自动交易。')
keep('173-b000 177-b006', 'upper-l025-c-stage-mobile-fraction-quarter-third-half-in-bull',
     '26新手和仓位不大可用1/3或1/4，25很差时1/2另有行情语境，比例不全局替换。')
keep('173-b002 175-b010 175-b013', 'upper-l025-c-stage-earnings-season-quality-small-technical-exception',
     '26中长线基本面与短线技术分工，使不看基本面的正文交易修辞不能笼统概括全课。')
keep('173-b005 177-b002', 'upper-l013-c-stage-exit-when-structure-no-longer-tradable-not-pnl upper-l013-c-stage-average-second-entry-break-old-bear-low-exit',
     '26牛市/谨慎中长线/相应技术的不轻斩仓及退市例外，与13类点失效后的防护范围有差别；不自动宣布通用优先级。')

issue('price-risk-information-and-absolute-control', '166-b007 167-b001 167-b002 168-b001 169-b001',
      '纯技术把风险归价格与消息先反映、交易继续就无盲点、负成本永不败均有作者强措辞，未有独立信息效率/收益证据。',
      '保留作者归属和前提，不把引用复核变成经济定理或实际无风险保证。', True)
issue('continuation-cancellation-ordinary-suspension-and-deadline', '166-b008 167-b001 172-b011',
      '永久终止/事后取消与普通停牌不同；按日/按1分例及自有钱到期各有时间尺度，“足够长”未数值化。',
      '不由普通停牌不影响反推出跳空/终止也可控，不以降级交易鼓励有期限借贷；进一步核后课风险限制。', True)
issue('negative-price-cost-size-and-warrant-identity', '168-b001 168-b002 168-b003',
      '负价格在总体成本语境，非负报价；5万/一毛/扣费可能4000、目标原数量不加仓、未具名认购成本负2.8皆自述。',
      '不猜认购为前文认沽，不把目标量不变说成股数时刻不变，不补费率/账户证明或负成本必不败。', True)
issue('long-fundamental-selection-and-no-cut-vs-protection', '166-b007 167-b003 168-b003 173-b002 173-b005 175-b010 175-b013 176-b004 176-b005 177-b002',
      '正文无须选择/不看市盈率的纯技术视角，与中长线择优看基本面、重仓反抽减半、牛市不轻斩仓除退市有不同范围；前13失效防护并未被撤销。',
      '按作者/日期/对象分别保留，不合成为任何被套都永久补仓，也不自动以晚文覆盖早文。', True)
issue('level-quantity-signal-and-trend-regime', '168-b002 170-b001 171-b000 171-b003 171-b005 171-b011 172-b002 173-b000 175-b017',
      '级别基本只与数量相关为资金操作视角；强弱/大级别方向/指数个股一致/小资金连续跌势例外又影响入退信号；强弱无阈值。',
      '不抽裸的级别=数量定理，不将1分信号套所有环境，不凭柱缩或心态取代买卖点联合条件。', True)
issue('center-third-buy-context-and-heuristic', '175-b003 175-b004 175-b007 178-b001 178-b002',
      '727/826为原答紧写，年份仅问句上下文；上海30分/日/周为当时例；600316反问不证明一二三必紧接，600836回轴二买仍需完整结构。',
      '不由反问造普遍邻接/价序定理，保持101后来二三关系例外另证，不拿后加图框代替三段构造。', True)
issue('historical-earnings-percent-and-recovery-guarantees', '170-b004 172-b008 175-b011 175-b017 176-b002 176-b003 176-b007 177-b001 177-b005',
      '000999中线肯定、600343业绩1元、600677亏损成因/5.9、TCL条件获利、至少降本10%及可避所有下跌均未独立核验。',
      '预测/自述/反事实与事实分开，保留条件、例外和原数字，不能据历史帖担保交易结果。')
issue('embedded-date-typography-and-figure-origin', '173-b010 173-b011 173-b013 174-b000 175-b004 176-b005 178-b002',
      '6段嵌2/1日期已修；周线中线/顺便斩仓等原词不改；6图4文后2原发未核，MJ_PPOS/框线非已核作者公式。',
      '源文本与坐标保留，顶部旧光标不掩主图未来K；复权和图注只作待核资料，不替作者命题。')

note('166-b006', 'author-scope-introduction', '作者声明先谈风险再深入中枢，完整已读。', '引言不是风险控制证明，具体前提和主张分条记录。')
note('167-b000', 'autobiographical-context', '327/319故事后红马甲、大学期间炒股经历和别学的自述已读。', '不据自述认证身份/成绩或实际交易流水，不将学业逸事抽成市场规则。')
note('169-b003', 'historical-holding-and-practice-context', '药股当时洗盘、持仓者继续拿及不再提醒避免依赖的作者评论已读。', '历史中线仍看好与读者具体成本不明，不变成当下继续持仓建议。')
note('172-b005 172-b006 172-b008 172-b009 172-b010', 'historical-sector-prediction-and-rhetoric',
     '航天/航空区分、三日30%自评、1/31自称5分卖点可避全部下跌、压盘/洗盘修辞与免责声明及补充引言已读。',
     '未正面确认读者洪都1/26三买；避免所有跌幅和操盘能力是作者自述非实证，免责声明不作法律结论。')
note('173-b001 173-b006 173-b007 173-b009 173-b010 173-b012 173-b013 174-b001', 'principles-repetition-and-dated-market-context',
     '买点谨慎不追高、双向短差、凭证比喻、1/31周线中枢震荡、2/1股票组轮换/周线中线形成及星号分界已读。',
     '173-b010尾新日期只管其后；周线中线原词不静改中枢，历史行情观点不作当下或已验证结果；重复原则在相关命题取证。')

relations = {
    'upper-l026-c-stage-foreseeable-trading-continuation-level-horizon': [('交易延续', '交易条件', 'related')],
    'upper-l026-c-stage-sudden-stop-or-cancellation-invalidates-premise': [('交易有效性', '市场风险', 'qualifies')],
    'upper-l026-c-stage-ordinary-suspension-vs-permanent-stop-author-claim': [('交易延续', '停牌风险', 'qualifies')],
    'upper-l026-c-stage-capital-deadline-self-imposed-trading-stop': [('资金期限', '资金管理', 'related')],
    'upper-l026-c-stage-deadline-lower-frame-last-resort': [('资金期限', '操作级别', 'qualifies')],
    'upper-l026-c-stage-positive-cost-risk-and-negative-cost-ambition': [('负成本', '成本', 'related')],
    'upper-l026-c-stage-large-frame-before-short-trade-up-down-sides': [('缠中说禅短差程序', '操作级别', 'qualifies')],
    'upper-l026-c-stage-long-entry-fundamentals-short-tech': [('操作策略', '基本面', 'qualifies')],
    'upper-l026-c-stage-bull-no-light-cut-delisting-exception': [('持股', '交易延续', 'qualifies')],
}


for r in rows:
    r['relations'] = [{'source': a, 'target': b, 'type': t} for a, b, t in relations.get(r['id'], [])]
by_passage = defaultdict(list)
for r in rows:
    for e in r['evidence']:
        by_passage[e['passage_id']].append(r)
for item in pending:
    item['lesson_numbers'] = sorted({int(passages[x]['unit_id'].split('-')[1]) for x in item['passage_ids']})
    if item['id'].endswith('embedded-date-typography-and-figure-origin'):
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
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], '读者柱缩即背驰、全仓成绩、价序推理和中枢级别问题不作作者证据，相邻答复不表示逐项认可。'
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
        'note': '交易可延续/有效与普通停牌分开，期限与级别/数量/行情配套，负成本非负报价，中长线基本面与不轻斩仓的条件不省。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True, reviewer=REVIEWER, visual_review_note=f['note'],
             figure_source_review='6图全部实际查看；4文后行情2原发未核，MJ_PPOS/框线/未来K不替正文或确认历史预测。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 141 and Counter(x['lesson_number'] for x in ledger) == {26: 141}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [26], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(166, 179)), 'figure_objects_viewed': 6, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '26课141段13页6图同模型四轮；6源段日期修正、交易延续/有效/资金期限、负成本强措辞和各操作范围保留，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


