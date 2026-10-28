"""Materialize the main agent's four-pass reading of lesson49.

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
BASE = 'c_stage_l049'
REVIEWER = 'Codex 主代理 / 阶段C上册49课同模型四轮复核'
SOURCE_SHA = '63182fde2838d7900bc6b33b43959750b027ffa3da30ce8a0fb9036549238a47'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-049' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 83
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 355 AND 362 ORDER BY pdf_page,id', (DOC,))]
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
    pending.append({'id': 'upper-l049-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})




















c(49,'fix-operation-level-first-find-last-established-center','355-b012 356-b000','入市或换入新股票，先明确操作级别；以30分为例，应先找当下之前最后一个30分中枢。','操作级别|走势中枢|操作策略',1,'30分为假设示范不是人人统一级别，最后已有中枢与未来新中枢形成的未知不同，已形成不等已完成或被离开，操作级别不能随临时盈亏任意变。')
c(49,'three-current-positions-around-last-center','356-b001 356-b002 356-b003 356-b004 356-b006','相对最后中枢，当下可在内、下、上；作者将内归延伸，下按三卖未出或已出分两类，上按三买未出或已出分两类。','完全分类|中枢延伸|第三类买卖点|操作策略',1,'固定中枢/固定级别分类，三点需完整原定义；不把简图不操作枝绝对化而删技能/特殊震荡等正文例外，后段第二种第2类买点衔接原编号张力另留。',figs=[(356,1),(359,1)])
c(49,'last-center-immediately-confirmable-with-skill-author-assertion','356-b005','作者称当下之前最后30分中枢无须预测、可立即确认，前提是学好相关理论并能分清中枢。','走势中枢|确认|操作熟练程度|当下',1,'对象是最后已形成中枢，不是任何进行式新中枢都能零延迟确认；立即是作者方法断言，未作实际识别耗时/可靠率评测。')
c(49,'third-sell-instant-point-operational-small-interval','356-b006','下方已出三卖一类包括正出现；作者说最严格精确卖点瞬间完成，有操作意义的三卖是包含该点的足够小区间，上方三买按有无作相似区分。','第三类卖点|第三类买点|交易误差|价格精度|确认',1,'足够小无固定时间/价格宽度，未补预知瞬间成交或所有未完成走势都可提前确认三卖；原文精确区间说明直接对卖点，不无条件搬成所有买点精确定义。')
c(49,'inside-center-wait-skilled-sublevel-second-buy-exception','356-b007','在中枢内作者认为不操作最好、等演化到上下；若有技术能判断次级二买则也可参与，只把握当下技能范围的机会。','等待|第二类买点|次级别|操作熟练程度|操作策略',1,'内不操作为简化默认而非绝对禁令；很多二买在内不等所有二买均在内，无技能则先不参与。')
c(49,'below-no-third-sell-compare-previous-down-current-leg-nesting','356-b008','在中枢下而未出三卖时按震荡处理，选前面震荡段、最标准为最近向下段，与当下向下离开段比较力度，MACD辅助并逐级区间套定位尽量精确买点。','中枢震荡|MACD|指标对比|区间套|盘整背驰|第三类卖点',1,'先选可比走势再辅助指标，当前段看成背驰段不是先断言背驰已经成立；尽量精确不保证最底价或成交。',figs=[(356,1),(359,1)])
c(49,'oscillation-generally-contracts-expanding-force-not-automatic-third-sell','356-b008','作者说一般中枢震荡逐渐收敛，若继续震荡后向下离开力度比前小；特殊扩张震荡也可更强，这不必然破坏震荡形成三卖。','中枢震荡|动力学|盘整背驰|第三类卖点',1,'一般与特殊同存，扩张震荡一词此处描述幅度/形态，不直接等同严格中枢扩张定理；不能把力度更大当三卖充分条件，形态分解细节留后。')
c(49,'below-third-sell-complete-containing-sublevel-or-skip','356-b009','中枢下已出三卖时，作者说该中枢结束，可分析含该三卖的次级走势类型完成、用背驰找买点；也可干脆不参与，等新下跌中枢或更大级别中枢形成后再定。','第三类卖点|次级别|走势终完美|背驰|等待|操作策略',1,'可选介入与更干脆不参与分开，未说有三卖立刻反向买入，也未保证新枢形成即自动止跌。',figs=[(359,1)])
c(49,'skip-own-and-above-down-larger-consolidation-may-miss-rebound','356-b009','即使错过大反弹，作者主张没必要参与操作级别及以上下跌、超过操作级别盘整，等其完成再考虑。','操作级别|下跌|盘整|等待|操作策略',1,'自身级别盘整可参与，而超过自身盘整默认回避，不能省略比较级；与后文无其他可做时较大震荡的能力/选择例外联读。')
c(49,'above-without-third-buy-wait','356-b010','在中枢上方尚无三买时，作者认为不存在合适买点，应等待。','第三类买点|等待|买点|操作策略',1,'在本文固定级别入市分类中，不否定其他既有持仓/别级买点；紧后原写第二种第2类与买点承接不静改成第三种第2类。',figs=[(359,1)])
c(49,'near-new-buy-entry-but-completed-submove-top-divergence-wait-number-tension','356-b010 357-b000','原文在上方未三买等待后写对于第二种第2类，再说距该买点形成及位置不远可介入、刚形成最好；若买点后次级走势完成并盘整顶背驰则须等待大级别盘整。','买点|第三类买点|盘整背驰|次级别|等待',1,'原第二种第2类字面与前第三种第1类/买点衔接张力保留，不偷偷校成第三种第2类；只归录明确买点距离/完成后盘背条件，不以两张未核流程图充作者改号证明。',figs=[(356,1),(359,1)],ambiguity='source_second_kind_second_subclass_buy_context_number_tension')
c(49,'no-other-entry-market-larger-oscillation-optional-author-safe-wording','357-b000','若全市场无值得介入机会但又希望操作，作者允许按较大级别中枢震荡操作，并称可得安全收益。','中枢震荡|操作级别|操作策略|市场风险',2,'安全为作者方法主张非项目风险保证，选择参与较大盘整为此补充条件，不撤默认固定级别/技能限制或假设一定有利润。')
c(49,'two-most-valuable-buy-third-and-down-oscillation-divergence','357-b001','对一个中枢，作者把三买及中枢向下震荡力度背驰买点列为最有价值两类；前者为向上新中枢机会，后者为震荡降本增筹码。','第三类买点|盘整背驰|中枢震荡|中枢上移|成本',1,'价值为本文模型比较，非所有市场收益实证排序；不能合并三买前震荡与三买后新枢上移的不同阶段。')
c(49,'third-buy-larger-center-worst-structural-case-not-loss-bound','357-b001','作者称三买后最坏是更大级别中枢，可看其后是否盘整背驰决定卖出；不出现该情况则向上形成新中枢过程。','第三类买点|盘整背驰|中枢新生|卖点|中枢扩展',1,'最坏说的是作者结构分支，不是最大亏损/滑点/成交保证或排除小转大重合；须联合后文及43/44小级变大条件，不独抽为三买后必盈利。',ambiguity='author_structural_worst_case_not_money_risk_bound')
c(49,'mechanical-own-center-oscillation-safe-no-chip-loss-author-condition','357-b002','最严格机械操作下作者称只有围绕操作级别中枢震荡短差最安全、肯定能做且不丢筹码，0成本后赚筹码也同理。','机械化操作|中枢震荡|操作级别|零成本持仓|市场风险',1,'绝对措辞为理论模式/正确识别震荡前提，后声明判断错误可抛错、技能要求高；未实证成交/成本/制度下100%回补，不当产品承诺。',ambiguity='author_ideal_mechanical_guarantee_with_identification_condition')
c(49,'upward-center-move-full-position-no-intermediate-difference','357-b002 357-b006','确定操作级别后，中枢完成向上移动阶段不做短差，应满仓持至新中枢再震荡操作。','中枢上移|仓位|持股|操作级别|机械化操作',1,'本文固定品种模式理想仓位，不向任何用户发当前满仓指令；持股受向上移动同级背驰全部退出条件及容量限制，不能任意阶段都称应满仓。')
c(49,'oscillation-upper-reduce-lower-add-no-rebuy-after-third-sell','357-b002','围绕中枢短差，上方减仓、下方加仓，前提是震荡依旧；一旦三卖不能回补，作者称力度判断可避开其后可能成三卖的震荡。','中枢震荡|仓位|第三类卖点|动力学|操作策略',1,'明确震荡仍在与三卖停止回补，最后避开为作者能力主张未证实时零误差；不是任何跌到中枢下方都加仓。')
c(49,'completed-upmove-divergence-sell-all-wait-next-buy','357-b003 357-b006','中枢完成向上移动若出现背驰，作者要求抛全部筹码，完成该操作级别买卖后等下一买点。','背驰|卖点|持币|操作级别|走势终完美',1,'所述级别走势类型完成，非任何分笔/较小级背驰都令大级全清；43/48小级修正/变大条件仍联合，未给所有实时确认细节。')
c(49,'no-divergence-new-center-may-overlap-small-to-large','357-b003','若该向上移动不背驰，作者说形成新中枢并继续震荡短差再上移；小级转大亦可看成新中枢，但可能与前中枢重合，而趋势同级中枢不能如此。','中枢新生|中枢震荡|小级别转大级别|趋势|重叠',1,'新枢不自动皆同级趋势不交新生，保持重合大级分支；不将无同级背驰当永远只上不跌。')
c(49,'first-profit-maximum-theorem-fixed-instrument-fixed-level-author','357-b004 357-b005','缠中说禅第一利润最大定理：对任何固定交易品种、确定操作级别，以上固定品种操作模式利润率最大。','缠中说禅第一利润最大定理|操作级别|操作策略|利润率',1,'以作者命名和原条件归录；文说可严格证明而本课未附证明/可行策略集合/成交成本与最优化假设，不作项目已证数学定理或回测最优结论。',ambiguity='named_author_theorem_assertion_no_proof_in_source')
c(49,'mode-only-own-consolidation-up-small-level-no-zero-cost','357-b006','该模式只参与确定级别的盘整与上涨；盘整震荡降本、0后增筹码，但作者特别说小级别操作不会出现成本0情况。','操作策略|操作级别|盘整|上涨|零成本持仓',1,'作者小级别与大型零成本持有法分开，未补小级具体分钟阈值；保证降本/不丢为理想模式非无错误交易实测。')
c(49,'oscillation-divergence-vs-post-third-buy-upmove-different-stages','357-b007','中枢震荡中类似盘整背驰的走势段，与中枢完成后向上移动背驰段不同，分别在三买前后；三买前中枢未破坏，之后原中枢已完成。','第三类买点|中枢震荡|盘整背驰|背驰|中枢上移',1,'区分的是原中枢阶段，后可形成新中枢再震荡；不说三买后任何图形永不再盘整，也不混为相同指标零轴判断。')
c(49,'full-oscillation-sell-buyback-needs-skill-novice-partial-risk','357-b008 358-b000','作者理想震荡操作是上方全抛、下方如数接回，但需高精度，误判可抛错；不熟者可不全仓，不过震荡可直接三卖，剩筹可能只能三卖出，影响利润。','仓位|中枢震荡|操作熟练程度|第三类卖点|市场风险',1,'允许不熟者部分操作与最理想模型全仓并列，不能从前文绝不丢筹码抹去此处误判风险；直接三卖不必先三买。')
c(49,'practice-fifty-percent-wrong-ten-percent-spread-unverified','358-b001','作者建议宁可抛错也按方法练，声称零判断力抛错概率50%、抛对可能每次短差10%以上，认为震荡比黑马频繁且利润大。','概率原则|操作熟练程度|中枢震荡|操作策略',3,'50%及10%以上为作者无样本强语，未给等概率实验/基准/费用；不是项目统计结果或承诺收益，后有三买回补也不保证同价或及时成交。',ambiguity='author_probability_and_spread_claims_without_data')
c(49,'aggressive-switch-only-third-buy-exit-at-new-center','358-b002','更激进方法不断换股、不参与中枢震荡，只三买买入，一旦形成新中枢就退出。','第三类买点|中枢新生|操作策略|交易容量',1,'不同品种策略与固定品种震荡模式分开，需技术和市场三买机会；不是所有投资者应频繁换股，也非一出现低级小中枢就一概离场。')
c(49,'aggressive-thirty-five-down-next-up-no-high-or-divergence-exit','358-b002','30分操作例：中枢完成向上后先有5分向下，再下一个5分向上若不能创新高，或背驰，或盘整背驰，就抛出，作者称后必有新30分中枢、往往在最高点区间退出。','第二类卖点|盘整背驰|背驰|操作级别|中枢新生|操作策略',1,'三个或条件不能改成同时满足；先5分向下再向上及固定30操作不可删，必有/往往为作者结构与理想精度主张，未独立验证任意K型或成交最高。')
c(49,'second-profit-maximum-theorem-different-instruments-fixed-level','358-b003 358-b004','缠中说禅第二利润最大定理：不同交易品种交易中、确定操作级别，以上激进操作模式利润率最大。','缠中说禅第二利润最大定理|操作策略|操作级别|利润率',1,'本课只陈述可严格证明但未附证明/最优可行集/交易成本条件；不是作者第一定理被第二推翻或项目实证最优。',ambiguity='named_author_theorem_assertion_no_proof_in_source')
c(49,'profit-rate-average-profit-divided-average-capital-time-frequency','358-b005','此处利润率指每次操作平均利润除以需占用资金的平均时间；总体利润还取决于操作频率，第二定理不比第一更有意义。','利润率|资金管理|操作策略|缠中说禅第一利润最大定理|缠中说禅第二利润最大定理',1,'保留作者比值定义，不静改为年化收益率或总利润/总本金，也未附币种/时间单位/平均方式/分母是否资金量规范公式；两模式可有不同机会数。')
c(49,'aggressive-needs-third-buys-first-broader-not-worst-unilateral','358-b005','激进法需市场有该操作级别三买，否则只能等；固定品种法市场要求较弱，作者说除恶劣连续单边下跌且连大些中枢都无，基本可操作，实际两者不能偏废。','第三类买点|等待|交易条件|操作策略|下跌',1,'基本/机会条件及最恶劣例外保留，不把无三买强造买点；交易条件限本条市场机会范围，未把任何有中枢的熊市都认证无损。')
c(49,'capital-size-reduces-utilization-and-growth-bottleneck','358-b006','大资金须特殊处理，许多级别不能全仓参与会降低总体资金利用率；资金越大作者认为利润率越低、达到规模会遇增长瓶颈，突破办法留后。','交易容量|资金管理|利润率|操作级别',1,'资本规模与可操作容量的作者解释，不是所有规模收益严格单调或已给精确容量阈值，和48通道/精度限制联读。')
c(49,'annual-two-hundred-five-hundred-author-unverified-performance','358-b006','作者声称小资金用其法无论牛熊、随机选股年200%以上无问题，精度高熊市年500%不难，但这种增长只能维持几年、规模大遇瓶颈。','操作策略|交易容量|操作熟练程度|利润率',3,'200%/500%及最笨/随机等为原文作者未验证收益主张，没有账户流水、样本、回测或独立审计；不当本项目成功率/投资建议/保证收益。',ambiguity='unverified_author_annual_return_claim_not_project_metric')
c(49,'apr26-balanced-first-three-extremes-3745-conditional','359-b001','4月26日收评作者判典型平衡市、全天高低在前三30分K，次日能站稳3745则继续向上，并称5日线未破。','每日走势分类|平衡市|高低点|均线系统|走势预测',2,'历史当日判读、次日条件预测不当项目实测；后图已含4/27不用于证明4/26提前结论，3745不按图3745.40默改。',figs=[(359,2)])
c(49,'3745-center-upper-edge-not-reader-last-minute-price','360-b006','作者对3745的解释是中枢上沿。','走势中枢|价格区间|确认',1,'这是相邻4/26问答的价位，不认可读者昨收盘前一分钟价的推测，不能把任何一分钟收价当中枢上沿；图标签3745.40原字异值不静合。')
c(49,'000625-fifteen-view-area-only-corresponding-small-level','360-b009','对000625红柱变大仍下跌提问，作者要求先定操作级别、小级可看15分图；一般只看柱面积、不看黄白柱代表相应小级比较。','MACD柱波|MACD|指标对比|操作级别|技术分析',1,'原黄白柱、面子字样不私改为线/面积，意义需配前后MACD语境；未说红柱较高必涨或确定17.05买卖点，观察15分非信号必15分，后4/27图不证当时。',figs=[(360,1)],ambiguity='original_yellow_white_columns_and_face_words_preserved')
c(49,'center-start-apr24-0935-not-todays-retain-0931-difference','361-b001','作者澄清所说不是当天新中枢，而是4月24日09:35开始的中枢；此前48课写09:31起，两个时刻原字并存。','走势中枢|中枢延伸|确认',1,'原0935不静改0931，也不凭5分K标签约定猜定两者一致；本答没有重新给所有上下沿坐标。',ambiguity='source_0931_versus_0935_not_normalized')
c(49,'two-child-centers-connector-third-buy-is-third-child','361-b007','作者反驳只有两个次级：连接两个次级的部分含三买，也属一个次级，合起来已有三个次级。','次级别|走势中枢|第三类买点|中枢连接|中枢扩展',1,'解释该问结构的第三连接段，不把只有两个中枢本身当三段完整重叠证明；读者问高级中枢是否已完成未获独立明确完成/离开确认答案，保留形成与完成区别。')
c(49,'react-to-market-switch-if-qualified-otherwise-endure-oscillation','361-b010','作者要求按市场选择及时反应而不烦恼其不突破；技术合格可用激进第二法避盘整，否则须忍受，较熟练可借盘整降本。','当下|等待|操作熟练程度|中枢震荡|操作策略',1,'避盘整依靠退出另找机会非保证别股有三买，原第二钟字样保留；不认证所有烦恼均可通过交易解决。')
c(49,'turnover-not-exit-intent-proof-level-and-chart-matter','361-b013','对高换手是否出货，作者说每天都有人买卖，关键看走势与自身级别；1分操作几乎天天可卖，日线操作应问日线是否背驰。','成交量|操作级别|背驰|卖点|技术分析',1,'没有认可读者两日14%换手就是机构出货；日线有背驰吗是反问，不能直接制成此股日线已确认无背驰事实。')
c(49,'choose-two-legs-before-MACD-not-standalone-second-condition','362-b003','作者纠正顺序：先选择比较哪两段，再参考MACD比较力度；30分或5分MACD道理相同、只是方便不同，MACD是辅助而非独立另有条件2。','MACD|指标对比|动力学|操作级别|背驰',1,'不自动确认读者C回轴、d<c的每项或只比较最后两任意段；未否认结构/级别与轴的前后语境，只反对把MACD和力度判断孤立倒序。')
c(49,'lower-cost-before-chips-not-assume-future-doubling','362-b006','作者要求开始先降成本以改善持有心态，操作不能建立在假设上，要能应对各种情况。','成本|零成本持仓|市场心理|操作策略',1,'未认可读者先赚N筹码后翻倍抛50%或80%方案，不把能应对视作已验证所有极端执行都无风险。')
c(49,'tick-divergence-one-minute-area-five-view-one-signal-correlations','362-b009','作者说无需精确看到分笔，分笔背驰可比较1分柱面积；看不到1分时可用5分柱面积发现1分背驰，操作重各级相关性。','成交分笔|MACD柱波|指标对比|操作级别|背驰',1,'本课明确面积，与47分笔借1分柱长度辅助的措辞分别保留，不静说完全一致或修改旧证据；5分观察图不等5分背驰成立，也未给完整面积窗/级别确认算法。',ambiguity='lesson47_tick_length_versus_lesson49_tick_area_not_forced_equal')
c(49,'order-book-language-at-level-turns-observation-suggestion','362-b010','若研究细节，作者建议观察各级别见顶见底时盘口语言变化，认为更有意义。','技术分析|操作级别|顶|底',3,'建议观察不等已提供盘口语言完整特征、阈值、数据源或必胜算法，也不必为日常研究购买Level2。')

note('355-b011','source-study-context','作者交代51学习机会、暂停论语、穿插实用课程缘由。','不是技术买卖或对用户的日程指令。')
note('359-b000','source_header','正文与解盘之间星号分隔。','只作身份边界。')
note('359-b002 360-b000 360-b001','historical-holiday-VC-closing-context','作者谈交易所假期单周量、不能离开和VC约会、晚间答疑。','原历史情绪/日程不作行情规律，不执行约会或变更任何交易安排。')
note('361-b004','unverified-company-intent-historical-context','作者指600198玩伎俩并说别追高、坏消息前后才买的历史答。','具体公司主观恶意未核，不升为reviewed公司事实或现在交易建议；保留原文可查。')
issue('fixed-level-branch-number-and-instant-vs-operational-interval','356-b006 356-b007 356-b008 356-b009 356-b010 357-b000','原对于第二种第2类承接买点与前文编号有张力；精确三卖瞬间与足够小操作区间无数值宽度，简流程图原发未核。','不静修成第三种第二类或当已证作者改号；保正文默认等待与技能/特殊震荡例外，不让简图替代。',True)
issue('oscillation-contraction-expansion-and-maximum-proof-assumptions','356-b008 357-b001 357-b002 357-b004 357-b005 358-b003 358-b004 358-b005','两最大定理有作者命名但未附证明、最优可行集/成本/执行假设；收敛一般与扩张特殊并存，最坏为结构不是亏损界限。','以作者明确主张保留，利润率平均利润除占资平均时间不静年化；后查细则不伪造数学证明。',True)
issue('guaranteed-chip-safety-full-position-and-skill-execution','357-b002 357-b003 357-b006 357-b008 358-b000 358-b001 358-b006','绝不丢筹码/全仓/肯定可做为正确识别理想模式，后明言误判抛错、低技可部分及大资金不能全仓；50%/10%无样本，200%/500%无审计。','上下文联合，不将强语认证实际无风险或全体用户满仓；小级无0成本、容量增长瓶颈及制度费用未完整。',True)
issue('post-third-buy-stage-vs-original-oscillation-and-small-to-large','357-b001 357-b002 357-b003 357-b006 357-b007 358-b002','三买前原中枢震荡/三买后原枢完成向上、新枢再震荡需区分；无同级背驰仍可小转大重合，激进下上5分或条件不可删。','结合43/44/48大级修正/变大，不把任何小背驰都全清、任何中枢都同级不交或模式二只要低级枢就离场。',True)
issue('source-0931-0935-3745-chart-prices-and-later-frames','359-b001 360-b005 360-b006 361-b001','3745为中枢上沿非读者最后1分收价；原0935与48的0931不静合，图标3745.40和后4/27K不改原价或证早前预测。','需独立行情/时间标签才能核异值；两流程原发未核，两K图后加，不用未核图作定义唯一证据。')
issue('two-child-centers-connector-and-completion-unanswered','361-b006 361-b007','作者补两个次级间连接也是次级含三买，三个次级结构不等已经逐项回答更高级中枢完成或离开确认。','保留形成/完成、走势类型/中枢区间与波动区间区别，不把读者表述全部当作者定义。',True)
issue('MACD-order-areas-signal-level-and-length-wording','360-b008 360-b009 362-b000 362-b001 362-b002 362-b003 362-b009','先选比较段再MACD；原黄白柱/面子保留，15分看图非15分信号，1分面积判断分笔与47柱长度辅助不同措辞。','不静统一面积与长度或承认读者回轴/d<c整套独立二条件，后查50计算/级别边界；窗口/参数/积分未完整。',True)
issue('stock-turnover-earnings-intent-orderbook-and-reader-allocations','361-b003 361-b004 361-b012 361-b013 362-b005 362-b006 362-b008 362-b009 362-b010','具体公司恶意和出货未核，换手14%非认可阈值；读者先赚筹码再抛50/80与作者先降本不同，盘口语言无规则。','保历史答疑身份，不认证公司阴谋、绩效或当前荐股；Level2无必需承诺，未实现交易执行系统。')
relations={
 'fix-operation-level-first-find-last-established-center':[('操作级别','走势中枢','qualifies')],
 'third-sell-instant-point-operational-small-interval':[('第三类卖点','交易误差','qualifies')],
 'oscillation-generally-contracts-expanding-force-not-automatic-third-sell':[('中枢震荡','第三类卖点','qualifies')],
 'upward-center-move-full-position-no-intermediate-difference':[('中枢上移','仓位','qualifies')],
 'oscillation-upper-reduce-lower-add-no-rebuy-after-third-sell':[('中枢震荡','仓位','qualifies')],
 'first-profit-maximum-theorem-fixed-instrument-fixed-level-author':[('缠中说禅第一利润最大定理','操作级别','qualifies')],
 'mode-only-own-consolidation-up-small-level-no-zero-cost':[('零成本持仓','操作级别','qualifies')],
 'aggressive-switch-only-third-buy-exit-at-new-center':[('第三类买点','中枢新生','qualifies')],
 'second-profit-maximum-theorem-different-instruments-fixed-level':[('缠中说禅第二利润最大定理','操作级别','qualifies')],
 'profit-rate-average-profit-divided-average-capital-time-frequency':[('利润率','资金管理','qualifies')],
 'capital-size-reduces-utilization-and-growth-bottleneck':[('利润率','交易容量','qualifies')],
 'two-child-centers-connector-third-buy-is-third-child':[('中枢连接','次级别','qualifies')],
 'choose-two-legs-before-MACD-not-standalone-second-condition':[('MACD','动力学','qualifies')],
 'tick-divergence-one-minute-area-five-view-one-signal-correlations':[('成交分笔','MACD柱波','qualifies')],
}
relations={'upper-l049-c-stage-'+k:v for k,v in relations.items()}
scopes={
 'upward-center-move-full-position-no-intermediate-difference':['固定交易品种/固定操作级别的理想模式','原中枢已完成向上移动，尚未到同级背驰退出或新中枢震荡'],
 'oscillation-upper-reduce-lower-add-no-rebuy-after-third-sell':['操作级别中枢震荡仍在','已出三卖不再回补'],
 'first-profit-maximum-theorem-fixed-instrument-fixed-level-author':['固定交易品种','确定操作级别','本文固定品种操作模式，源文未附证明/执行假设'],
 'second-profit-maximum-theorem-different-instruments-fixed-level':['不同交易品种切换','确定操作级别','激进模式，市场需有相应三买机会'],
 'aggressive-thirty-five-down-next-up-no-high-or-divergence-exit':['30分钟级别操作','中枢完成向上后先5分向下再下一个5分向上','不能创新高或背驰或盘整背驰三择一'],
 'full-oscillation-sell-buyback-needs-skill-novice-partial-risk':['震荡仍在的高精度理想全仓操作','不熟者可部分，误判可抛错，震荡可直接三卖'],
 'no-divergence-new-center-may-overlap-small-to-large':['该向上移动未同级背驰','小级转大级新中枢可重合，不同于同级趋势新生'],
}
for r in rows:
 if r['id'].split('upper-l049-c-stage-')[1] in scopes:r['conditions']=scopes[r['id'].split('upper-l049-c-stage-')[1]]

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
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], '读者3745收前1分钟价、红柱放大、两中枢是否完成、14%换手与出货、C回轴/d<c、先赚筹码抛50/80%、Level2功能问法保留身份，不自动当作者认可。'
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
        'note': '固定级别两模式/利润率口径与频率、市场机会和容量联读；作者最大定理未附证明，50/200/500非实测；三买前原枢震荡/后三段上移/新枢再震荡区别，错号与0931/0935、柱长/面积张力保留。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=f['note'],
             figure_source_review='实际查看355至362八页4整图；两流程原发/制作者未核，不能替正文修第二种第2类或删特殊分支；两行情图含4/27后K晚于4/26文字，日期/3745.40不静改，不能验证早前预测。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 83 and Counter(x['lesson_number'] for x in ledger) == {49: 83}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [49], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(355, 363)), 'figure_objects_viewed': 4, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '49课83段8页4整图同模型四轮，21日期空格规范/2后图2未核；两操作模式与利润率定义、技能资金/机会限制及未证强语、分支编号/时刻和MACD差异分层，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


