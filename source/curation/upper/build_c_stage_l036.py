"""Materialize the main agent's four-pass reading of lesson36.

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
BASE = 'c_stage_l036'
REVIEWER = 'Codex 主代理 / 阶段C上册36课同模型四轮复核'
SOURCE_SHA = '32a0c6c35e43b1c4fe09156b1360ca14c7d524c9a698399ef465ac1dbbc8a3e4'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-036' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 89
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 266 AND 272 ORDER BY pdf_page,id', (DOC,))]
assert len(figures) == 5
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
    pending.append({'id': 'upper-l036-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})












c(36, 'associativity-mixed-levels-and-multiple-not-vague', '265-b008',
  '走势类型连接满足A+B+C=(A+B)+C=A+(B+C)，A、B、C级别可以不同；作者强调多义性是在严格理论下换视角，不能等同概念含糊。',
  '走势类型连接|结合律|走势多义性|级别|走势分解', 1, '时序不交换，所有组合仍须符合类型/中枢定义；多义不意味着怎么分都行，35非交换条件保留。')
c(36, 'a-n-m-level-decomposition-and-operation-choice', '265-b009 265-b010 265-b011',
  '原文以A的n级分解第m段记为An-m，展示同一A可按1分、5分、30分、日线等分解；选操作级别相当于选择其中一组分解。',
  '走势分解|操作级别|级别|同级别|走势类型连接', 1, 'PDF265公式已视觉核对，下标在抽取中串到相邻段；原文/字符映射不修写，此处只释义n为级别m为段序，不把抽取A=A串当价格恒等式。')
c(36, 'completion-depends-on-level-two-five-not-thirty-complete', '265-b012',
  '同一时点按5分与30分分解可有不同意义；两段5分类型A+B在30分分解下尚未完成，作者依走势必完美原则观察其后完成过程。',
  '完成|走势终完美|操作级别|走势分解|次级别', 1, '低级已完成不代表高级完成，也未给固定多久、往哪个方向或获利幅度的承诺。')
c(36, 'mixed-five-thirty-redivide-regroup-last-unfinished', '265-b013 266-b000',
  '对A、C、E为5分而B、D、F为30分的混合连接，作者先按5分重分，再依中枢定义组合为前项标准30分、末项F`在30分意义下未完成的表达。',
  '走势分解|走势类型连接|结合律|走势中枢|完成', 1, '不把任意混合段无条件两两相加就自动同级；重分后依中枢定义和末项完成状态，组合可不唯一。')
c(36, 'best-combination-changes-with-current-not-prediction', '266-b001 267-b000',
  '作者说更利于判断操作的组合会随当下走势变化；这类重组处理已发生走势，不是预先预测未来，纯中枢角度也可保留原组合。',
  '结合律|走势分解|当下|走势预测|操作策略', 1, '随时变化须仍符合定义，作者称不影响操作是其理论内部评价，不可在交易后任意改标准再声称永不失误。')
c(36, 'mar8-1000-third-buy-below-old-swing-high-not-center-top', '266-b001',
  '作者说2760—2858的30分中枢后，3月8日10:00的5分回抽2871确认三买，虽低于上一中枢波动最高2888，仍在原中枢上方。',
  '第三类买点|走势中枢|次级别|高低点|价格区间', 1, '2858中枢上沿与2888波动高点分开，整数和图小数不静合；三买不必越过一切波动极值。',
  ['本课2007年3月13日回顾具体结构'], figs=[(266, 1), (267, 1), (267, 2)])
c(36, 'regroup-mar8-retest-into-mar5-up-new-start-mar9-1030', '266-b001',
  '原从3月7日13:30算新30分中枢延伸后，作者把3月8日10:00回抽纳入3月5日13:30起的5分上涨，重组后新30分中枢从3月9日10:30起算。',
  '结合律|走势分解|中枢延伸|走势中枢|走势类型连接', 1, '按原文字保留13:30/10:30；图标13:25/10:05不同不能静改，重组不改历史价格或把旧判断删除。',
  ['上述新中枢仍延伸时的具体重组'], figs=[(266, 1), (267, 1), (267, 2)], ambiguity='source_text_1330_1030_versus_figure_1325_1005_not_reconciled')
c(36, '2892-above-2888-conditional-thirty-up-not-yet-proof', '266-b001',
  '重组后低点2892高于旧波动高2888；若其后不跌破2888，可显出30分上涨，但新中枢被新三买有效突破前仍可能跌破2888并确认扩展。',
  '上涨|中枢扩展|第三类买点|确认|高低点', 1, '若与之前仍可能两支并存，不把当时中枢低点高就当最终上涨或扩展均已确认。',
  ['所举重组中枢及后续未完成走势'], figs=[(267, 1), (267, 2)], ambiguity='dated_no_break_or_later_expansion_conditions_open')
c(36, 'initial-regroup-would-hide-third-buy-meaning', '267-b001 268-b000',
  '作者解释一开始不采用该重组，是因会把3月8日回抽局限在小5分走势中、隐藏三买意义，使操作者只恐慌等背驰；应综合理解不同组合意义。',
  '结合律|走势分解|第三类买点|当下|操作熟练程度', 2, '这是具体例子选择分解的操作解释，不证明任何较简图一定更好，或允许知道未来后伪称事前唯一分解。')
c(36, 'simplify-unfinished-second-center-not-cancel-expansion-definition', '268-b000',
  '作者建议组合避繁就简，但强调中枢扩展定义用于两个中枢都完全走出；实际第二中枢未完仍延伸时，可在未出现明确合定义破坏前按有利判断重组。',
  '结合律|中枢扩展|中枢延伸|完成|走势中枢', 1, '未完与已完不同；避开复杂扩展的组合选择不能取消定义或在已明确破坏后仍任意重写。')
c(36, 'chosen-combination-must-use-own-center-third-buy-boundary', '268-b000',
  '采取哪种组合就按其图形意义判断操作：3月9日10:30起的新30分中枢是2905—2947；若保留3月7日13:30起则是2892—2911，对应三买参照不同。',
  '走势分解|操作策略|走势中枢|第三类买点|价格区间', 1, '原文倒序2947到2905在转述按低高书写，原证据不改；不得用新组合同时偷用旧边界，亦不认定两组都同一对象可无条件合并。',
  ['本课所举两种仍合定义的当下组合'], figs=[(267, 1), (267, 2)])
c(36, 'daily-oscillation-can-below-thirty-even-gap', '268-b001',
  '围绕日线中枢的震荡不必全是直接次级，可是30分以下任意级别乃至跳空缺口，原例包括连续一字涨停再跌停的跳动。',
  '中枢震荡|次级别|级别|缺口|走势中枢', 1, '围绕中枢运动与构成中枢的三个次级类型不是同一要求；低级跳动本身不是已成完整日线中枢。')
c(36, 'stay-around-daily-eventually-thirty-last-a-m-less-nine', '268-b001',
  '若仍围绕且不脱离日线中枢，作者说低级跳动最后至少能组成30分类型，分解为已成30分各段加未完a；原记m<9，否则升周中枢需改按日线分解。',
  '中枢震荡|走势分解|完成|走势终完美|中枢扩展|级别', 1, 'm为该式已列30分段序数口径，不是9根K或9自然天；PDF268下标视觉已核，原文/映射保留，不擅以此一式消除33初三/新增六计数语境。')
c(36, 'five-leave-and-retest-may-thirty-third-not-daily', '268-b002 268-b003',
  '若末尾a是5分离开且再5分反抽不回中枢，按日线还不构成三买卖点，但可能构成前一个30分类型A的三买卖点。',
  '第三类买卖点|次级别|走势中枢|操作级别|完成', 1, 'A为前已成30分类型的下标对象，不是整日线中枢；两段5分不足直接充作日线所需30分确认。')
c(36, 'lower-third-comes-before-genuine-daily-in-example', '268-b003 268-b004',
  '对于该路径后来真正形成日线三买卖点的情况，作者说前30分A的三买卖点在时间上先出现。',
  '第三类买卖点|买卖点|级别|完成', 2, '时间先后限定所举积累形成路径，不说所有先出现30分三买都最终形成日线三买；下标断行原样保留，依据PDF268连读。')
c(36, 'after-thirty-third-can-return-daily-via-thirty-type', '268-b004 268-b005',
  '前30分A三买卖点后完成的30分走势，仍可再经一个30分走势回到日线中枢，继续日线震荡。',
  '第三类买卖点|中枢震荡|走势类型|操作级别', 1, '较小层三买不保证日线脱离或趋势，正是本级与高层风险/完成状态不能混用。')
c(36, 'absolute-safety-relative-to-thirty-not-universal', '268-b003 268-b004',
  '作者称该三买卖点“对于A”绝对安全，同时明确对日线却不一定。',
  '第三类买卖点|操作级别|市场风险', 3, 'A是该前30分类型，绝对安全是作者强措辞，不等成交无损、零风险、任何级别均涨或不存在跳空流动性风险。', ambiguity='author_relative_structural_safety_not_unconditional_trade_guarantee')
c(36, 'daily-operator-attend-early-thirty-third-if-trend', '268-b006 268-b007 268-b008',
  '作者说若后30分走成趋势，日线三买往往在第二30分中枢附近才成且不回早先价位，因此日线操作者也可重视并适量参与先前A三买，后若成趋势更需注意。',
  '第三类买卖点|操作级别|趋势|仓位|中枢新生', 2, '原若/往往/适量均保留，未给仓位百分比或保证不回该价；不把全仓本级条件取消。')
c(36, 'completed-path-combinations-claim-and-experience-not-forecast', '268-b009 269-b000',
  '作者把分解已发生走势、选最适组合及综合不同组合视角，归于理论把握、图形熟悉和当下磨练，并宣称合理论的组合皆可解释最终走势而非预测。',
  '走势分解|结合律|走势多义性|当下|操作熟练程度|走势预测', 3, '任意组合永不违反理论是作者理论自述，仍受定义和原时序限制；本项目未完成其不变性/唯一性形式证明或实盘验证。', ambiguity='author_invariance_and_best_decomposition_claim_not_formally_proven')
c(36, 'mar14-daily-up-divergence-leg-or-weekly-longer-case', '270-b007',
  '3月14日晨作者把中线列为若此处日中枢直接上则入背驰段，或继续震荡成周中枢后预期幅度更大，并判断牛市第一波未完。',
  '走势中枢|背驰段|走势预测|宏观市场判断', 4, '是当时历史两支及看多判断，不证日/周皆已成或未来必涨，不是当前行情建议。')
c(36, 'mar14-third-line-rally-pressure-wait-sell-no-chase', '270-b008',
  '作者判断当时三线股行情除真题材业绩支持者外进入短线压力，可持有等卖点但不宜追高，其他二线和题材轮动机会需观察。',
  '三线股|二线股|板块轮动|追高|卖点|基本面', 4, '历史板块观点与自述，不能由三线名称推确定涨跌或把所有题材当同一层；原以没必要按不必转述。')
c(36, 'small-new-sme-float-and-profit-author-history-claim', '270-b009 271-b000',
  '作者当时关注深圳中小板新上市小盘股，举流通约2000万、总盘约6000万，并声称其熊市也无问题、上市阶段介入最终多获利。',
  '新股|次新股|流通量|交易容量|市场风险', 4, '约值是该历史观察池而非新股定义；熊市无问题和最终均获利无全样本审计，不认证收益或当前制度/板块组成。', ambiguity='historical_small_ipo_safety_and_profit_unverified')
c(36, 'mar14-appendix-oscillation-until-third-point', '271-b002',
  '3月14日附录作者把当日阴线仍视为围绕新中枢震荡，称第三类买卖点未出现则震荡延续。',
  '中枢震荡|第三类买卖点|走势中枢|确认', 2, '附录只知日级时点，所夹政治贬称不作因果事实或机构身份认证；技术状态是作者当时判读，非任意走势永久区间不变。')
c(36, 'mar14-appendix-rotation-second-line-bonus-view', '271-b003',
  '附录判断三线潜力缩水、板块需转换，提出关注有中线潜力的二线股，并把业绩公布时高送配列为常见交易题材。',
  '二线股|三线股|板块轮动|题材股|基本面', 4, '历史观点不证明相关机构真实交易、送配必有收益或现行规则，不按题材文字自动建立个股推荐。')
c(36, 'new-small-ipo-two-paths-down-divergence-strong-forecast', '271-b004',
  '作者将小盘中小板上市后概括为开盘附近中枢后上行或下行两支，称向下两波后日线背驰者会成中线大牛。',
  '新股|背驰|走势中枢|走势预测|下跌', 4, '两波与大牛为该历史概括和强预测，不是已验证所有IPO只有两路径或日背驰后必盈利，需独立样本而本批未做。', ambiguity='author_ipo_two_paths_and_bull_forecast_not_verified')
c(36, 'new-ipo-center-low-swings-then-third-buy-hold', '271-b004',
  '对向上路径，作者建议在开盘后中枢震荡低点做短差，三买出现后可持久些，并声称之后一般有可观升幅。',
  '新股|中枢震荡|第三类买点|操作策略|持股', 2, '历史方法口径不免除具体中枢级别、完成和三买判定，原可观升幅不当收益保证。')
c(36, 'mar14-rate-psychology-forex-weekly-pressure-author-view', '271-b005',
  '作者当时把加息影响主要说成心理因素，认为外汇投资公司问题压力较大但最多在周中枢可承受范围。',
  '基本面|市场心理|走势中枢|宏观市场判断', 4, '具体2007年判断无模型或事后检验，非当前利率/政策经济效应结论，也不证明周线已形成。')
c(36, 'mar15-still-2905-2947-thirty-center-oscillation', '271-b006',
  '3月15日15:23作者说指数仍在2905—2947的30分钟中枢震荡。',
  '中枢震荡|走势中枢|操作级别|价格区间', 1, '沿用本课新组合的具体整数范围，图右端3/16及夹读者文字不作作者当日预测证明或身份混合。',
  ['2007年3月15日15:23:22解盘'], figs=[(272, 1)])
c(36, 'index-not-worst-one-sided-stock-opportunities-view', '271-b008',
  '作者要求同时看中枢震荡技术与个股，判断当时只要指数不是最恶劣单边走势，个股仍有机会。',
  '中枢震荡|操作策略|宏观市场判断|市场风险', 3, '当时市场观察及条件，不是指数下跌所有个股均安全或无需风险管理，前段机构贬称只作历史语境。')
c(36, 'abc-compare-ac-consolidation-divergence-and-c-internal', '272-b011',
  '对日线三买的30分回抽中三5分段完成疑问，作者要求A、C比较盘整背驰，再配合看C内部小级别背驰。',
  '第三类买点|盘整背驰|背驰|次级别|完成', 1, '两层配合而非任选一项充分确认，原未给固定等几根K或任意小背驰就日三买的算法。')
c(36, 'ipo-open-gap-short-answer-original-wording-unclear', '273-b001',
  '对新股首中枢如何起段，作者短答“就把开盘到跳空缺口上涨，和有缺口的情况是一样的。”',
  '新股|缺口|走势中枢|确认', 3, '保留汇编这句不顺的原字次序，不自行补字或据此认可读者全部下上下/上下上起段公式；与35缺口处理可并查，不能捏造唯一语法。', ambiguity='short_ipo_gap_wording_not_silently_repaired')
c(36, 'second-third-line-conventional-performance-price-not-strict', '273-b004',
  '作者说二线三线并无严格区分，通常依业绩和价位约定；几分钱业绩、亏损、价在平均股价下者一般称三线。',
  '二线股|三线股|基本面|价格区间', 1, '本课通俗约定非官方分类，不等大盘/小盘、指数成分或特定流通规模的同义词，没有补出二线数值门槛。')
c(36, 'third-buy-sublevel-leave-retest-not-reenter-general-answer', '273-b009',
  '对曾返回后再离开、以及第二个日线中枢后回试两问，作者答只要次级别离开、次级别回抽不回中枢的都算三买。',
  '第三类买点|次级别|确认|走势中枢', 1, '作者答复不等CCTV读者全部辩论获认可；不能把第一次回抽与第一次离开混同或省次级别/完成条件，触边相等普遍规则未在本段形式化。')
c(36, 'late-fourth-fifth-center-third-buy-expands-nearly-all-claim', '273-b009',
  '作者警告连续延伸上涨的第4、5个中枢后，三买随即出现中枢扩展几乎百分百。',
  '第三类买点|中枢扩展|上涨|市场风险', 3, '几乎百分百为作者强经验措辞，无样本或概率校准，不改100%定理；第4/5个是连续上涨中枢序数，不是第4/5根K。', ambiguity='author_nearly_hundred_percent_without_sample')
c(36, 'key-after-third-trend-versus-larger-center-not-yet-algorithm', '273-b009',
  '作者说三买后能否走上涨趋势而非更大中枢才是关键，并把具体判断留待后课。',
  '第三类买点|趋势|中枢扩展|走势预测|确认', 1, '本课未提供完备预测或判别算法，不能以都有三买就推趋势延续；定义成立和后续演化分别返回。')

keep('265-b008 265-b013 266-b000', 'upper-l035-c-stage-type-connection-associative-not-commutative upper-l035-c-stage-mixed-lower-level-connection-a-b-b-example',
     '36展开不同级别组合，不取消35连接不交换、类型/中枢区别与完成条件。')
keep('265-b012 268-b001', 'upper-l035-c-stage-single-five-type-cannot-contain-thirty-center upper-l033-c-stage-extension-six-added-plus-three-initial-nine',
     '低层已完不等高层已完；m<9处是所列30分段序数，仍需跟中枢扩展/完成条件，不机械K数或自然日。')
keep('266-b001 268-b000', 'upper-l035-c-stage-second-thirty-center-range-2892-2911 upper-l035-c-stage-mar8-2871-third-buy-then-new-thirty-from-mar7-2911',
     '36重组后新参照不回写35历史当时区间；旧组合仍可用但三买标准须随所选组合，不把两框合成一个无条件对象。')
keep('268-b002 268-b003 268-b004', 'upper-l035-c-stage-large-buy-sell-is-sublevel-or-below-not-necessarily-direct',
     '36细化30分早信号和日线真正三买时序，未推任意小级背驰必日线转折。')
keep('272-b011', 'upper-l034-c-stage-third-buy-confirm-look-inside-sublevel upper-l035-c-stage-buy-sell-level-proof-endpoint-completion-outline',
     '36要求A/C盘整背驰及C内部小背驰配合，不给单项充分或固定K数算法。')
keep('273-b001', 'upper-l035-c-stage-ex-right-gap-treat-as-lowest-down-new-center-usual',
     'IPO短句和35除权缺口是相关但不同问题，保留原字与歧义，不能静合为完整复权或新股起段算法。')
keep('273-b009', 'upper-l035-c-stage-third-buy-after-second-center-not-guaranteed-up-daily-possible',
     '36强调晚第4/5中心更易扩展为经验强词，三买定义不保证趋势，尚待后课算法。')
note('271-b007', 'historical-institutional-political-opinion', '作者对机构、金融股、三线与小盘行情的贬称和判断已读。',
     '未核机构身份、动机、实力或作者真实交易，不把政治标签建成市场因果事实；上下文完整留存。')
note('272-b000', 'source_separator', '原文星号为3/15解盘终止分隔。', '只保留来源分界，不独立支持知识。')
note('271-b001', 'source_header', '附录标题已核，只确定同日盘后语境。', '不继承08:58晨帖的具体时间，不单独支持技术结论。')
issue('multiple-combinations-not-vague-and-completion-scope', '265-b008 265-b009 265-b010 265-b011 265-b012 265-b013 266-b000',
      '异级别结合与完成状态仍受定义，低层完成不等高层完成；公式下标在抽取中跨段错序但PDF可读。',
      '保存视觉公式释义和原映射，接后课完成/同级分解，不用结合律允许交换时序或任意小段拼成高层。', True)
issue('regroup-center-range-and-text-figure-time-mismatch', '266-b001 267-b000 267-b001 268-b000',
      '旧3/7 13:30区间2892—2911可保留，新3/9 10:30区间2905—2947可重组；图13:25/10:05不同不静合，三买参照随组合。',
      '未完第二中枢和两已完中枢扩展定义分开，时间差需更多原证据，不回写35旧时点。', True)
issue('daily-oscillation-thirty-completion-and-m-count', '268-b001',
      '围绕日震荡可更小/缺口，未完a若继续围绕应完成30分；m<9是该式计数，原未在此详列与初三新增六的全部条件。',
      '联系33/后续延伸扩展定义，不把m当K线/交易日数，不由理论终完美给固定时间承诺。', True)
issue('early-thirty-third-not-daily-and-relative-safety', '268-b002 268-b003 268-b004 268-b005 268-b006 268-b007 268-b008',
      '5离开/5回抽可前30分三买但非日线，仍可用30分返日中枢；若真日三买则早信号先出，绝对安全仅作者相对对象强词。',
      '保留若/往往/适量，不改全仓本级风格或收益保证，后续大级三买确认与风险仍需分层。', True)
issue('third-buy-repeated-exit-first-retest-and-late-center-frequency', '269-b007 269-b009 269-b011 269-b013 269-b015 269-b017 270-b003 273-b007 273-b008 273-b009',
      '中途大量第一次离开/第一次回抽辩论是读者；作者最终只给次级离开回抽不回都算，晚4/5几乎百分百扩展无统计。',
      '不能把CCTV全部讨论冒作者，保留三买定义、第一次回抽原规定与后续演化不同问题，未给趋势/扩展完备算法。', True)
issue('ipo-gap-short-answer-and-colloquial-stock-lines', '273-b001 273-b004',
      'IPO开盘缺口短句原文不顺未擅补字；二三线按业绩价位只是约定、非市值或指数身份严格分类。',
      '后续更明确来源前不补新股首段统一方向或流通股本阈值，不把二三线当官方品种。', True)
issue('historical-small-ipo-profit-policy-and-risk-opinions', '270-b007 270-b008 270-b009 271-b000 271-b002 271-b003 271-b004 271-b005 271-b007 271-b008',
      'IPO无风险/大牛、宏观行情/加息心理/周中枢压力是作者历史强判断；政治贬称及读者改革传闻未核，不当现行事实。',
      '固定两册历史边界，未查现行规则或收益样本，不由来源话语触发对外交易或宣传。')
issue('commentary-dates-and-figure-provenance', '271-b001 271-b002 271-b003 271-b004 271-b005',
      '盘后附录5段不能挂3/14 08:58晨帖，只保留日级日期；五图4文后1原发未核，270图挂读者讨论，272夹作者与读者不混。',
      '原文/下标抽取/字符映射/坐标不改；图后3/16行情不证明原预测或替读者背书。')
relations = {
 'upper-l036-c-stage-associativity-mixed-levels-and-multiple-not-vague': [('结合律','走势多义性','qualifies')],
 'upper-l036-c-stage-completion-depends-on-level-two-five-not-thirty-complete': [('完成','操作级别','qualifies')],
 'upper-l036-c-stage-chosen-combination-must-use-own-center-third-buy-boundary': [('走势分解','第三类买点','qualifies')],
 'upper-l036-c-stage-simplify-unfinished-second-center-not-cancel-expansion-definition': [('中枢扩展','完成','qualifies')],
 'upper-l036-c-stage-daily-oscillation-can-below-thirty-even-gap': [('中枢震荡','缺口','qualifies')],
 'upper-l036-c-stage-five-leave-and-retest-may-thirty-third-not-daily': [('第三类买卖点','操作级别','qualifies')],
 'upper-l036-c-stage-after-thirty-third-can-return-daily-via-thirty-type': [('第三类买卖点','中枢震荡','qualifies')],
 'upper-l036-c-stage-abc-compare-ac-consolidation-divergence-and-c-internal': [('盘整背驰','背驰','qualifies')],
 'upper-l036-c-stage-second-third-line-conventional-performance-price-not-strict': [('三线股','基本面','defines'),('二线股','三线股','qualifies')],
 'upper-l036-c-stage-new-ipo-center-low-swings-then-third-buy-hold': [('新股','第三类买点','qualifies')],
 'upper-l036-c-stage-key-after-third-trend-versus-larger-center-not-yet-algorithm': [('第三类买点','中枢扩展','qualifies')],
}

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
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], 'CCTV等读者的制度改革引文、2911/2947、第一次离开或回抽辩论、盘中观点和个股成本均只作读者上下文，不能改成作者定论。'
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
        'note': '多义分解须符合定义而非含糊，选择组合与其边界联动，未完第二中枢与两个已完再扩展分开；日/30分三买时序和相对安全范围不混，读者辩论非作者。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True, reviewer=REVIEWER, visual_review_note=f['note'],
             figure_source_review='本课5图全部查看，4后加1原发未核；270为读者讨论图不挂作者命题，272混读者/作者不混身份；图文10:05/10:30及13:25/13:30差异保留。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 89 and Counter(x['lesson_number'] for x in ledger) == {36: 89}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [36], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(265, 274)), 'figure_objects_viewed': 5, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '36课89段9页5图及前后课边界同模型四轮；附录5段改日级时间，组合边界与三买标准一致、未完成/完成扩展、日/30分提前信号和读者身份分开，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


