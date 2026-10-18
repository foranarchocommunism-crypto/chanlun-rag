"""Materialize the main agent's four-pass reading of lesson27.

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
BASE = 'c_stage_l027'
REVIEWER = 'Codex 主代理 / 阶段C上册27课同模型四轮复核'
SOURCE_SHA = 'ac64fe7c1bcc41c48c497fda458091f9c6a6bcb297b3e8669d183ecb6acd93d2'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-027' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 93
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 179 AND 187 ORDER BY pdf_page,id', (DOC,))]
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
    pending.append({'id': 'upper-l027-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})


c(27, 'trend-divergence-after-at-least-second-center', '178-b007 179-b000',
  '趋势至少有两个同级别中枢；作者说真正趋势背驰须在至少第二中枢之后，延伸中可更晚，不能把第二中枢出现直接等同已经背驰。',
  '趋势|走势中枢|同级别|背驰|走势延伸', 1, '至少两个、同级和之后完整保留；第100中枢是延伸可能的极端例，不指定任意第几中枢必终结。')
c(27, 'second-center-proportion-author-estimate', '178-b007 179-b000',
  '作者称第二中枢后即背驰占绝大多数，日线以上几乎90%以上；小级别如1分钟比例稍低，4或5中枢后才背驰较罕见。',
  '背驰|走势中枢|概率原则|操作级别', 3, '原文几乎90%以上与罕见没有样本和统计方法，不是项目测得概率或必发生时点。',
  ['第27课对趋势延伸中枢数的经验陈述'], ambiguity='author_center_count_probability_not_empirical_estimate')
c(27, 'first-center-only-consolidation-divergence', '179-b001',
  '第一个中枢处所见的类似背驰，作者称只能算盘整背驰，并以企图脱离中枢但力度不足、被阻回中枢解释其技术含义。',
  '盘整背驰|背驰|走势中枢|围绕中枢的运动', 1, '这是该段释义，不能据此抹掉同课盘整背驰可形成二三买或转三卖；回中枢的描述不当所有盘背最终路径的无例外定理。',
  ['第27课第一中枢后的类似背驰释义'], ambiguity='return_to_center_description_vs_third_point_paths')
c(27, 'consolidation-divergence-compare-first-third-types', '179-b001',
  '二三买的盘整背驰常有三段，第三段往往稍破第一段极限；比较的是第一、第三两个走势类型，二者不必都是趋势，两个盘整也可比较力度。',
  '盘整背驰|走势类型|盘整|第二类买点|第三类买点', 1, '往往稍破不改成所有情况必须新极值；两个走势类型不能换成任意三根K或未完成片段，后文完成条件另证。')
c(27, 'divergence-leg-named-by-type-and-level', '179-b001',
  '本课把某级别某类型走势构成背驰或盘整背驰时的该走势类型，命名为该级别背驰段。',
  '背驰段|背驰|盘整背驰|走势类型|级别', 1, '保留本处命名原句；本课解盘又谈进入背驰段待精确结束，64课另区分成功背驰与可失效背驰段，不能按词形认所有背驰段已完成确认。',
  ['第27课引入背驰段名称的语境'], ambiguity='early_naming_vs_later_provisional_leg_and_success')
c(27, 'low-position-consolidation-and-buy-types', '179-b001 180-b004 181-b000',
  '作者认为小级别高位盘整背驰风险较大，低位不同；开头称多数二三买由盘整背驰、而多数一买由趋势背驰，后文进一步说严格一买肯定源于趋势背驰，大级别盘整另称类一买。',
  '盘整背驰|背驰|第一类买点|第二类买点|第三类买点|类第一类买点', 1, '多数与肯定分别按两处原文保留，不能把类一买静默合并严格一买，也不把盘背一律贬为低效。',
  ['第27课低位盘背与严格/类买点分别论述'], ambiguity='most_vs_definite_wording_and_analogous_buy_distinction')
c(27, 'large-consolidation-historical-bottom-scope', '179-b002 182-b001',
  '作者认为大级别、特别至少周线以上的盘整背驰较有用，往往可找历史性底部；但随后提醒周线也可能仅长线底部，日线上可用而可靠性较低。',
  '盘整背驰|历史性底部|操作级别|底', 1, '往往、不一定及日线可靠性较低同时保留，不把任何周线盘背等成历史最低或所有日线法不可用。')
c(27, 'vanke-quarter-three-segments-original-dates', '179-b002',
  '000002季线例按三个月一根K：1993一季36.7至1996一季3.2为第一段，至2001三季15.99为三角形第二段，再至2005三季3.12为第三段。',
  '周期K线图|盘整背驰|三角形整理|走势类型', 1, '日期与价位是作者例示，未独立复权核价；原文给13季度、23季度、17周，其中17周不静改季度，不能作为时间算法直接执行。',
  ['第27课万科季线历史例'], figs=((179, 1),), ambiguity='source_seventeen_weeks_unit_and_price_basis_unverified')
c(27, 'vanke-numeric-iron-bottom-author-downplays', '179-b002 180-b000',
  '作者以33.5、12.87跌幅近34与13等数字推万科约2.99铁底，但紧接说明这种数字分析意义不大，转用MACD判断。',
  '历史性底部|幅度|MACD|走势预测', 3, '神奇数字近似及铁底为作者经验推断，不补斐波纳契充分必要规则或证明最低价不可能再破。',
  ['第27课万科数字说明及其自我降权'], ambiguity='numeric_approximation_not_proof_of_floor')
c(27, 'vanke-quarter-lines-or-area-divergence-signal', '180-b000',
  '万科季线第三段破3.2时，作者列回轴后黄白线再跌不创新低、柱面积小于第一段；一般任一项符合可为信号，两项都符合更标准。',
  'MACD|盘整背驰|历史性底部|确认', 1, '或项限该季线三段盘背实例，不替换24/66标准趋势背驰整体条件；信号与小级别精确买点分开。',
  ['第27课000002季线三段与MACD辅助'], figs=((179, 1),), ambiguity='case_or_indicators_not_universal_standard_trend_sufficiency')
c(27, 'vanke-large-capital-build-versus-small-precision', '180-b000',
  '作者说季度判断不足以给精确买点，大资金可在此范围分批越跌越买；小资金时间利用不同，可沿月、周、日、30分钟向下找更精确背驰点。',
  '资金管理|操作级别|区间套|背驰段|历史性底部', 1, '先有本例季度盘背及后续行情判断，不推任意跌势大资金都能越跌越买或小级别单项信号是季度底部。')
c(27, 'nested-legs-must-be-inside-parent', '180-b001',
  '作者以万科说明区间套：季度第三段内找月线最后中枢对应背驰段，该月线段应在季度段内且更小，再递到周、日、30、5、1分钟乃至每笔成交。',
  '区间套|背驰段|次级别|成交分笔|操作级别', 1, '对应与包含是关键，不把大买点后任意小买点当同一区间套；每笔成交不等后期严格定义的几何笔。')
c(27, 'precision-theorem-recursive-until-minimum', '180-b002',
  '缠中说禅精确大转折点寻找程序定理称：先找大级别背驰段，再在次级别图找相应段内的背驰段，逐级收缩到最低级别，转折点在该最低段确定范围内。',
  '缠中说禅精确大转折点寻找程序定理|区间套|背驰段|最低级别', 1, '这记录作者程序定理及其范围结论，不冒称已完成独立数学证明或给出最低级别自动算法。')
c(27, 'finite-levels-no-unique-mathematical-point', '180-b001 180-b002 180-b003',
  '作者说理想中可缩到最后一笔成交，但级别不无限可分，理论不能证明如极限般唯一点状精度；实用目标是较精确历史底部区间，1分钟对大级别常已够用。',
  '区间套|最低级别|成交分笔|历史性底部|价格精度', 1, '唯一一笔为达到成交级别时的理论理想，不包装成交保证或无条件唯一最低；作者明确承认有限层级精度限制。')
c(27, 'analogous-first-buy-at-large-consolidation', '180-b004 181-b000',
  '严格第一类买点源于趋势背驰；最大尺度股票常只见一个中枢而属盘整，此时大级别盘整背驰形成类第一类买点，作者要求至少周线以上。',
  '类第一类买点|第一类买点|盘整背驰|走势中枢|操作级别', 1, '类似不等严格类别；原至少周线以上措辞按来源保存，并与182周线不一定历史大底限制同读。')
c(27, 'analogous-second-buy-no-new-low-600685', '181-b001 182-b000',
  '大级别不再新低而MACD回零轴上下、后一柱子面积小于前一柱子时，作者举600685在2005第三季2.21为类第二类买点；位置仍按逐级背驰段缩小。',
  '类第二类买点|第二类买点|盘整背驰|MACD|区间套', 1, '类二买不改成严格二买；原文柱子面积的粒度未详，不静补完整波片算法，图旧光标6/30不改第三季。',
  ['第27课600685季度图例'], figs=((181, 2),), ambiguity='histogram_unit_and_analogous_type_not_strict_second_buy')
c(27, 'weekly-long-bottom-not-always-historic', '180-b003 182-b001',
  '作者区分下一轮大牛市的历史底部与周线较长线底部：季度法需老股票，周线不用等30年但不一定历史大底，日线应用可靠性也较低。',
  '历史性底部|操作级别|周期K线图|走势预测', 2, '30年是作者对下一轮大牛市的猜测而非周期定律；周线不必等待该预测成真才能应用。',
  ['第27课方法用途与长期展望'], ambiguity='thirty_year_bull_market_forecast_not_verified_cycle')
c(27, 'feb2-five-minute-buy-next-week-author-forecast', '182-b008',
  '2月2日作者称周线中枢仍形成，预期下周有5分钟买点、抓住可有10%利润，强调卖点走、看准买点再进。',
  '买点|操作级别|走势中枢|走势预测', 3, '下周/10%是作者尚未验证的预测，不是项目承诺；中枢形成中不是已经完成，后图不能反证当时必然。',
  ['2007年2月2日15:19上证解盘'], ambiguity='future_buy_point_and_ten_percent_claim_unverified')
c(27, 'feb5-leg-entered-not-precise-end', '182-b010',
  '2月5日解盘称周线第一段探底预计最多30分钟背驰后结束，等待5分钟背驰拉30分MACD回轴；早盘只算进入背驰段，精确点还看1分。',
  '背驰段|背驰|区间套|MACD|操作级别', 1, '预计/很可能明天与仅进入段均保留，不当当时已结束或已定位；本段日期由前段尾嵌头确定为2/5。',
  ['2007年2月5日15:18上证解盘'], figs=((183, 1), (183, 2)), ambiguity='entered_leg_vs_unconfirmed_future_end')
c(27, 'feb5-999-third-leg-no-divergence-case', '182-b014 183-b000',
  '2月5日15:25作者反对追高416等，称999尚看不到背驰、下跌为中枢形成第三段，应按图形而非盼涨。',
  '背驰|走势中枢|走势终完美|追高', 2, '999是否全称000999仅按前文药股上下文，不补其他股票；当日判断不与别日或别级别混同，未确认底部。',
  ['2007年2月5日15:25原补充评论'])
c(27, 'false-divergence-is-misclassification-not-new-type', '184-b001',
  '对假背驰提问，作者说不存在另一个假背驰类别，错误在判断，常把盘整背驰转第三类买卖点误当趋势背驰。',
  '背驰|盘整背驰|第三类买卖点|确认', 1, '作者没有确认读者中信证券600640的具体背驰判断；这是名义与误判归因，不证明任何人可永不判断错。')
c(27, 'life-insurer-second-down-center-and-49-confirmation', '184-b004',
  '2月2日作者对人寿明确回述49元上涨背驰后须等下跌背驰，正在形成下跌第二中枢；他希望约30元，并称N年以后复权上100。',
  '背驰|走势中枢|下跌|操作级别|走势预测', 2, '本条明确49上涨背驰可补25页含混语气，但不改旧引文；30/100均作者展望，不当成交价或已兑现收益。',
  ['2007年2月2日15:47人寿答复'], ambiguity='historical_price_forecasts_not_verified')
c(27, 'not-daily-buy-point-forming-five-minute-partial', '184-b007',
  '作者说买点不是每天都有，强趋势下1分钟买点有时两三天一个；当时5分钟买点正形成，大资金与好股票可开始部分介入。',
  '买点|背驰段|资金管理|操作级别', 1, '有时不等固定频率；形成中与大资金好股部分布局须同存，不改成5分钟已确认或所有资金可提前全仓。',
  ['2007年2月2日15:49问答'], ambiguity='forming_signal_and_partial_build_not_confirmed_buy_for_all')
c(27, 'novice-recent-base-break-good-earnings', '184-b010 186-b010',
  '作者建议不熟练时选刚突破底部且业绩不差、图形简单标准而自己看得懂者，避开尚不懂的复杂图形，随练习扩展。',
  '操作熟练程度|基本面|操作策略|买点', 2, '较安全是作者比较判断，不是突破底部或基本面一项充分买点，也不承认读者所有股名代码组合正确。')
c(27, 'life-insurer-thirty-no-zero-only-one-forming', '184-b013',
  '对601628是否30分钟背驰，作者否定黄白线尚未回零轴时的该判断，称最多正在形成1分钟背驰。',
  '背驰|背驰段|MACD|操作级别', 1, '30分否定与1分形成中不改成已完成，读者36元进场不因此获认可。')
c(27, '600331-feb1-center-flanks-comparable', '184-b016',
  '对600331，作者指出5分钟中枢昨天已成，原记010935到011410，两侧各一段可以比较，纠正读者只看当天13:15至14:00。',
  '走势中枢|盘整背驰|操作级别|走势类型', 1, '昨天按2月2日答复为2月1日；010935/011410原格式保留，并未逐项认可读者趋势或背驰结论。',
  ['2007年2月2日16:40对600331五分答复'], figs=((185, 1),))
c(27, 'zero-retest-one-condition-look-lower-end', '185-b002',
  '对601628十五分钟回轴一次的追问，作者说这只是一个条件，还看“其后股价新低后是否创新低”，更精确可参考5分钟图找背驰段何时结束。',
  'MACD|背驰段|操作级别|确认', 1, '原句第二个是否创新低省略主语，保留不擅填唯一指标；不能把一次回轴等充分背驰，也不以文后反弹证明当时已确认。',
  ['2007年2月2日16:43人寿答复'], figs=((185, 2),), ambiguity='new_low_comparison_pronoun_not_fully_explicit')
c(27, 'long-holding-differences-during-large-center', '186-b002 186-b003',
  '对只买不卖死拿者，作者要求卖点卖、买点买，长期持股尤其在形成大级别中枢时多作短差降成本，反对跌后低位恐慌斩仓。',
  '持股|缠中说禅短差程序|成本|走势中枢', 2, '不把要求实际做到当作已实现收益，也不能抹去26熟练程度、长期资金和大级别单边上涨例外。')
c(27, 'efficiency-related-to-point-amplitude', '186-b006',
  '作者把准确按买卖点执行称最高效率，同时指出不同股票买卖点间幅度影响资金效率，选股也重要，具体方法留后。',
  '操作策略|资金管理|幅度|买卖点', 2, '最高效率为作者原则，不是已测优化结论；幅度不能单独代表费用、时间和成交约束下的实际效率。')
c(27, 'five-percent-rebound-profit-author-reply', '186-b009',
  '对读者称套5%，作者答5%不算什么、一反弹就开始挣钱。',
  '反弹|成本|操作策略', 3, '仅历史简答，不补具体股票买点、反弹必到价位或赔偿保证；读者00079代码原样，作者未逐只确认。',
  ['2007年2月5日15:49对套5%者简答'], ambiguity='brief_recovery_confidence_without_price_or_execution_evidence')
c(27, 'big-leg-before-small-divergence-precision', '186-b013',
  '作者说MACD仅辅助，须先辨趋势和大级别背驰段：30分钟急跌时孤立1分背驰用途有限；先有5分背驰段再用1分定位，30分段内用5分更稳。',
  'MACD|背驰段|背驰|区间套|操作级别', 1, '先后/包含与大级别方向条件完整，不把绿柱波波缩短当标准已背驰，也不把更稳写成无风险。')
c(27, 'small-third-buy-t1-not-executable-profit', '187-b002',
  '作者提醒小级别第三类买点有风险，并非买后不涨，而是T+1下涨了也未必能卖出。',
  '第三类买点|T+1|市场风险|操作级别', 1, '价格反弹与交易可执行利润分开；未把读者第一段力度大便最佳买点的整套推断一并认可。')
c(27, 'consolidation-divergence-not-inferior-need-regime', '187-b005',
  '作者说二三买的盘整背驰未必比趋势背驰差；须防它转第三类买卖点，并结合更大级别，不能只看本图。',
  '盘整背驰|背驰|第三类买卖点|操作级别', 1, '好坏与本级/大级方向、买卖角色有关，不给盘背设全局劣等排序。')
c(27, 'thirty-down-break-five-down-divergence-third-sell-risk', '187-b005',
  '30分钟下跌刚破位时，作者称5分钟盘整背驰转三卖几率99%，通常不参与；若30分钟刚上涨，5分钟向下盘整背驰反而可为好买点。',
  '盘整背驰|第三类卖点|买点|操作级别|概率原则', 1, '两支方向/阶段都保留；99%是作者无样本经验估计，不能当项目统计或任意下跌一律三卖。',
  ['第27课2月5日对600879及多级别方向的答复'], ambiguity='author_99_percent_not_measured_probability')
c(27, 'macd-b-must-retrace-near-zero-not-arbitrary-three', '187-b008',
  '作者说MACD比较中的B段若不是回抽零轴附近，便不满足本处判断条件，不能任意拿三段来判断背驰。',
  'MACD|背驰|走势类型|确认', 1, '附近不是精确等于零；没有认可读者B太大就一定大中枢，也不把指标B与中枢自身ABC任意替换。')
c(27, 'center-b-may-exceed-a-extreme-with-overlap', '187-b011',
  '对构成中枢三段的B高能否高于A、B低能否低于A，作者答可，只要三段有重叠。',
  '走势中枢|重叠|走势类型', 1, '紧邻问题已限定形成中枢的三段，不能抹去同级/连续次级走势等全书前提，亦不等任意三片段有重叠就成中枢。')

keep('178-b007 179-b000', 'upper-l017-trend-definition',
     '27再申趋势至少两个同级别中枢，同时说明延伸可多于两个，第二个后须关注非已必背驰。')
keep('179-b001 187-b005', 'upper-l024-c-stage-divergence-default-trend-consolidation-analogy upper-l024-c-stage-consolidation-short-difference-scope',
     '盘背和趋势背驰术语/回跌范围、第三类点路径继续限定，179回中枢释义不能覆盖全体第三买点分支。')
keep('179-b001 182-b010 186-b013', 'lower-l064-divergence-segment-vs-success lower-l074-c-stage-case-one-minute-trend-end-divergence',
     '27命名原句与同课进入段待精确结束、64/74后来未确认/可失效用法保留，不能仅出现段名就宣告背驰成功。')
keep('180-b001 180-b002 180-b003', 'lower-l065-interval-nesting-below-segment lower-l086-c-stage-big-buy-small-buy-nesting',
     '区间套需相应段包含，成交逐笔非后期几何笔；精确定位仍不等通道可成交，最低层和费用制约另有证据。')
keep('184-b004', 'upper-l025-c-stage-life-insurer-49-45-38-branches-case',
     '27明确回述49上涨背驰，补充25“49那天不是背驰”可能反问的旁证；旧原句及旧语气歧义不改写。')
keep('187-b002', 'lower-l087-c-stage-nov6-short-rebound-not-t1-profit',
     '27早先已有涨但T+1卖不了的限制，87新股案例另有真实来源，两者同存不将小级别反弹当可实现利润。')
keep('187-b011', 'upper-l017-center-definition',
     'B可越A极值只针对已限定中枢构成三段，严格至少三个连续次级走势定义继续适用。')

issue('center-count-probabilities-and-completion', '178-b007 179-b000 182-b008 187-b005',
      '第二中枢后日线上90%以上、罕见四五个/百个、10%利润和99%转三卖皆作者经验/预测，未提供样本；关注或形成中不能改为已完成。',
      '记录原比例和条件，不因数量凑统计，不建立必第二中枢背驰或固定收益规则。', True)
issue('consolidation-return-types-and-analogous-buy-names', '179-b001 180-b004 181-b000 181-b001 182-b001 187-b005',
      '回中枢释义与盘背可成二三买/转三卖须分情形；一买多数/肯定原措辞并存，类一/类二与严格一二买不能同词归并。',
      '保留大级别特别周线以上、周线未必历史底和日线可用但可靠性较低，不给盘背统一优劣等级。', True)
issue('divergence-leg-naming-versus-confirmation', '179-b001 182-b010 184-b007 184-b013 185-b002 186-b013',
      '27先用构成背驰/盘背命名该走势类型背驰段，随后又有进入段/形成中待结束；64以后明确可失效与成功背驰不同。',
      '保留早期定义与后期使用语境，不把段名出现当已确认转折，不自动按日期宣布修订。', True)
issue('finite-nesting-trades-not-strokes-and-proof', '180-b001 180-b002 180-b003',
      '区间套程序需对应背驰段包含且逐级缩小，最低级有限；唯一一笔是理想，不能证明无限极限一点；本处笔指成交不是后期几何笔。',
      '不补数学证明、无条件极值唯一、无限递归算法或真实成交保证，后65交易通道成本限制另证。', True)
issue('quarter-numbers-week-unit-macd-and-historic-bottom', '179-b002 180-b000 181-b001 182-b001',
      '17周原单位、神奇数字/2.99铁底、季度跌破3.2确认及MACD任一项信号、后一柱面积粒度均有语境或未明口径。',
      '原词原数保留不静改季度，不把数字近似或一种指标变普遍充分买点；不把周线底一律认证历史最低。', True)
issue('multilevel-regime-t1-and-abc-premises', '184-b007 184-b013 185-b002 186-b013 187-b002 187-b005 187-b008 187-b011',
      '大级别方向/阶段与小级别用途、T+1可卖、回轴只是条件、ABC有结构前提；一次回轴/三任意片段/任意盘背不能代替整体。',
      '保持30弱急跌和30刚上涨的不同支，B附近非严格等零，作者没有确认读者全部案例日期和结构。', True)
issue('case-forecasts-reader-codes-and-pronouns', '184-b004 184-b009 184-b012 184-b016 185-b002 186-b009 187-b004',
      '人寿30/复权100、套5%即反弹可盈为展望；读者中信600640/00079等代码名组合不核；股价新低后是否创新低代词未详，010935格式需上下文。',
      '不填唯一代词/无来源价格或认证读者标注，不用后图反弹证明先前确认；25含混49原句留存并补27明确旁证。')
issue('embedded-timestamps-and-later-figures', '178-b006 182-b009 182-b010 182-b013 182-b014 183-b000',
      '19正文段补标题15:11:27，7解盘段按嵌2/5两头分组；7图5后加2原发未核，600663为2011图，复权/参数/箭头来源未核。',
      '原文/字符映射/坐标不变，旧光标不抵消右端未来K，178前课图只边界核对，不由图线补作者证明。')

note('182-b002 182-b003 182-b004 182-b005 182-b006', 'learning-metaphor-and-skills-scope',
     '幼儿园/学前班/小学的学习层次比喻完整已读，强调辨中枢变化、盘背和第三类点的技能。',
     '比喻不是学历认证或已完成掌握证明；技术条件在相关命题另存。')
note('182-b007 182-b009 182-b011 182-b012 182-b013 183-b001', 'dated-market-self-report-and-next-topic',
     '本次走势与上次不同、作者照图短差、个股强于大盘、基金下篇预告及000938自述建仓/坏消息/技术不足勿碰已读。',
     '作者持仓与强弱自评未核，预告非基金策略内容已给出；182两新时间头只管后段，星号不独立作证。')

relations = {
    'upper-l027-c-stage-divergence-leg-named-by-type-and-level': [('背驰段', '走势类型', 'related')],
    'upper-l027-c-stage-large-consolidation-historical-bottom-scope': [('历史性底部', '盘整背驰', 'related')],
    'upper-l027-c-stage-precision-theorem-recursive-until-minimum': [('缠中说禅精确大转折点寻找程序定理', '区间套', 'related'), ('缠中说禅精确大转折点寻找程序定理', '背驰段', 'requires')],
    'upper-l027-c-stage-finite-levels-no-unique-mathematical-point': [('区间套', '最低级别', 'qualifies')],
    'upper-l027-c-stage-analogous-first-buy-at-large-consolidation': [('类第一类买点', '盘整背驰', 'related')],
    'upper-l027-c-stage-analogous-second-buy-no-new-low-600685': [('类第二类买点', '第二类买点', 'qualifies')],
    'upper-l027-c-stage-small-third-buy-t1-not-executable-profit': [('T+1', '第三类买点', 'qualifies')],
    'upper-l027-c-stage-center-b-may-exceed-a-extreme-with-overlap': [('走势中枢', '走势类型', 'requires')],
}


for r in rows:
    r['relations'] = [{'source': a, 'target': b, 'type': t} for a, b, t in relations.get(r['id'], [])]
by_passage = defaultdict(list)
for r in rows:
    for e in r['evidence']:
        by_passage[e['passage_id']].append(r)
for item in pending:
    item['lesson_numbers'] = sorted({int(passages[x]['unit_id'].split('-')[1]) for x in item['passage_ids']})
    if item['id'].endswith('embedded-timestamps-and-later-figures'):
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
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], '读者对中枢时段、30分背驰、买入价和明日走势的自述不作作者证据，相邻答复不表示逐项认可。'
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
        'note': '趋势背驰/盘整背驰/背驰段及严格一二买/类一二买分开，区间套须对应包含且精度有限，成交分笔不作几何笔，概率和图示不替证明。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True, reviewer=REVIEWER, visual_review_note=f['note'],
             figure_source_review='7本课图全部实际查看；5文后行情或2011重绘、2原发未核，另178前课边界图已看，未核复权/箭头不替正文。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 93 and Counter(x['lesson_number'] for x in ledger) == {27: 93}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [27], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(178, 188)), 'figure_objects_viewed': 7, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '27课93段10页7本课图同模型四轮；26段来源时间修正，区间套有限精度/背驰段/类一二买及多级别限制保留，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


