"""Materialize the main agent's four-pass reading of lesson39.

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
BASE = 'c_stage_l039'
REVIEWER = 'Codex 主代理 / 阶段C上册39课同模型四轮复核'
SOURCE_SHA = 'f2bf5014883543db7cea16e52d180f94e31352acdc45645b267a9f36d7ee6720'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-039' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 40
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 288 AND 290 ORDER BY pdf_page,id', (DOC,))]
assert len(figures) == 3
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
    pending.append({'id': 'upper-l039-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})


















c(39, 'profitable-sale-or-lower-repurchase-author-training-view', '287-b003',
  '作者以股票为废纸/交易凭证作比喻，称盈利卖出或卖后较低价回补无所谓错误，卖后继续涨、回补后继续跌归于技术精度。',
  '操作策略|成本|市场心理|操作熟练程度', 3, '是作者训练评价，不是含费用、机会成本与风险的最优性证明；纸凭证比喻不认证股票无任何价值。')
c(39, 'mechanical-rhythm-training-may-initially-slower', '287-b003',
  '作者把机械程式训练比短跑分段步数，认为形成韵律前可能暂时比随意操作差，但应先练基本节奏再提高精度。',
  '机械化操作|操作熟练程度|操作策略', 2, '训练建议而非长期盈利必然承诺，未做对照实验或指定训练周期。')
c(39, 'up-buy-before-sell-down-sell-before-buy-rhythm', '287-b004',
  '机械程式的基本节奏是向上段先买后卖、向下段先卖后买，各段内小段也须配合当下结构和时点。',
  '机械化操作|同级别分解|操作策略|买卖点', 1, '是所选分解下的持仓卖出/回补节奏，未授权裸卖空或把任意下跌都当可逆向开仓。')
c(39, 'step-wrong-stop-adjust-mind-rhythm-before-resume', '287-b004',
  '作者要求一旦机械节奏某步出错，应停止操作，先调好心态和节奏再继续。',
  '机械化操作|市场心理|操作熟练程度|操作策略', 1, '原唯一正确为训练纪律措辞，不补出错的统一价格阈值或认为暂停一定避免所有损失。')
c(39, 'physiological-response-from-training-author-analogy', '287-b004',
  '作者认为长期机械节奏训练后，看到相应图形可像定时醒来般有生理反应，并说同级类型分解节奏大致有周期性。',
  '机械化操作|操作熟练程度|市场心理|同级别分解', 3, '是作者身体节奏类比，无生理实验或确定周期，不能当超常感应、无需结构判断或科学训练证明。', ambiguity='author_physiology_and_periodicity_analogy_unverified')
c(39, 'a-plus-A-regroup-five-types-and-A-contains-thirty-center', '287-b006 288-b000',
  '作者对向上a+A先用结合运算把a规整为5分类型，并将A分成m段5分类型A1至Am，最终把一般情形归结为A包含30分中枢。',
  '同级别分解|结合律|走势分解|走势类型|走势中枢', 1, 'A是包含中枢的连接段，不静改A本身必为一个纯30分中枢；一般归结依后述吸收分支及前提，不保证任意几根K立即成30分中枢。')
c(39, 'A0-a-odd-down-even-up-A1-not-break-a-low', '287-b006 288-b001',
  '以a为A0，在所举向上a+A的5分分解中，Ai奇数为向下、偶数为向上，且先有A1、A2，A1不得跌破a低点。',
  '同级别分解|走势分解|上涨|下跌|高低点', 1, '奇偶从A0=a的此向上例开始，不能脱离起点任意编号就套买卖方向；同级类型而非单根K线。')
c(39, 'A2-break-a-high-A3-not-return-absorb-into-a-prime', '287-b006',
  '若A2升破a高点且A3不跌回a高点，作者把a+A1+A2+A3合为新的a`，仍为5分走势类型。',
  '结合律|同级别分解|走势类型|高低点|走势分解', 1, '两条件联合而非仅A2新高即吸收，原不跌回与后分支跌破措辞保留，未自补等高/EPS的统一算法。',
  ['向上a+A例，A0=a且A1不破a低点'])
c(39, 'general-A3-break-a-high-three-form-thirty-center', '287-b006 288-b000',
  '排除上述可吸收情形后，作者转而一般性考虑A3跌破a高点，此时A1、A2、A3构30分中枢。',
  '走势中枢|同级别分解|重叠|次级别|高低点', 1, '依原向上a+A和A1不破a低等前提，不将任意三个已命名片段都判成中枢；A3等于a高点未被此句单列。')
c(39, 'compare-Ai-Ai-plus-two-force-consolidation-method', '288-b001',
  '以a为A0后，作者不断比较同向Ai与Ai+2的力度，用盘整背驰方法决定买卖；这与围绕中枢震荡操作类似，但本处立足同级别分解。',
  '盘整背驰|同级别分解|指标对比|机械化操作', 1, '可比较与已判盘背分开，没有给本段唯一MACD或积分公式；i与i+2同向而非相邻异向比较。', figs=[(288, 1), (288, 2)])
c(39, 'new-Ai-plus-two-not-rewrite-prior-unique-decomposition', '288-b001',
  '作者说下一Ai+2在当下产生，但不影响此前至Ai+1的同级别唯一分解。',
  '同级别分解|完成|当下|走势分解', 1, '此前至Ai+1为原所有前面Ai+1措辞的范围释义；唯一性仍是作者理论主张，未据此声称已给全算法或取消36未完末段可重组。', ambiguity='prior_completed_decomposition_invariance_author_claim')
c(39, 'center-can-grow-thirty-to-year-still-five-pair-operation', '288-b001',
  '原中枢可由30分扩至日、周甚至年，而该机械操作仍只理会所选5分Ai与Ai+2间是否盘背。',
  '同级别分解|机械化操作|中枢扩展|操作级别|盘整背驰', 1, '高层中心升级与固定低层分解是两种视角，不取消38本级不定义延伸的规则，也不说所有扩展都不影响风险。')
c(39, 'pair-divergence-even-i-plus-two-sell-odd-buy', '288-b001',
  'Ai与Ai+2盘背时，若i+2为偶数卖出，为奇数买入。',
  '机械化操作|同级别分解|盘整背驰|买卖点', 1, '依A0为向上a、偶上奇下的完整5分类型编号；不是按交易日单双数或任意一根柱号买卖。',
  ['本文A0=a的向上a+A同级5分例'], figs=[(288, 1), (288, 2)])
c(39, 'no-divergence-even-hold-until-protection-break-then-exit', '288-b001',
  '无盘背且i偶时，若Ai+3不跌破Ai高点则继续持有；直到Ai+k+3跌破Ai+k高点后，在不创新高或盘整顶背驰的Ai+k+4卖出，原注明k为偶数。',
  '机械化操作|同级别分解|持股|高低点|盘整背驰', 1, '保护位破坏与其后同向段不新高/顶盘背联合，不是Ai+3一跌即无条件该价卖；未给k起点/范围、实盘完成识别或相等容差的全细节。',
  ['原Ai/Ai+2无盘背且i为偶'], figs=[(288, 2)])
c(39, 'no-divergence-odd-stay-cash-until-protection-break-rebuy', '288-b001',
  '无盘背且i奇时，若Ai+3不升破Ai低点则继续不回补；直到Ai+k+3升破Ai+k低点后，在不创新低或盘整底背驰的Ai+k+4回补。',
  '机械化操作|同级别分解|盘整背驰|高低点|仓位', 1, '保护位升破与随后下段的弱势条件联合，非任意反弹立即买；奇数支沿用k记号但没有重新写取值约定，不擅补成全覆盖独立算法。',
  ['原Ai/Ai+2无盘背且i为奇'], figs=[(288, 1)], ambiguity='odd_branch_k_convention_not_repeated_in_source')
c(39, 'two-pattern-classes-divergence-vs-protected-continuation', '288-b002',
  '作者将方法概括为两类：奇偶方向下Ai+3未破Ai对应高低保护位，或Ai与Ai+2盘整背驰，分别采取不同策略。',
  '机械化操作|同级别分解|盘整背驰|高低点|操作策略', 1, '两类为作者程式概括，结合前段先判盘背/无盘背的顺序，不凭总结声称已形式证明所有输入互斥穷尽；90%读者头晕为修辞非预测准确率。')
c(39, 'mar23-pressure-line-not-effectively-broken-patience', '288-b003',
  '3月23日作者说两高点连线仍在上方，未有效突破前市场心理仍可能反复，要求耐心应对震荡。',
  '经验压力线|确认|中枢震荡|市场心理', 2, '历史当时判读，作者中行主动示弱/机构动机未核，3/28后图不作当日预知证明。',
  ['2007年3月23日15:18:15指数解盘'], figs=[(290, 1)])
c(39, 'mar26-pressure-break-still-needs-confirmation', '288-b005',
  '3月26日作者说指数突破上方压力线，但有效性仍需确认，其他板块在轮动。',
  '突破|确认|经验压力线|板块轮动', 1, '突破发生与有效性确认分时保留，中行不涨对指数支持属作者解释而未做因果核验，后图不把尚待确认改已通过。',
  ['2007年3月26日15:20:49解盘'], figs=[(290, 1)])
c(39, 'mar26-second-line-ten-fifteen-and-third-line-regulatory-risk', '289-b001',
  '作者当时关注约10元二线、业绩特别好者约15元，并说可看300成分股；认为三线除真题材外监管风险较大。',
  '二线股|三线股|监管风险|基本面|板块轮动', 4, '具体历史选股口径非二三线定义或现价推荐，价格例和300池不认证具体收益；监管风险非所有三线必违规。')
c(39, 'not-lowest-print-may-be-underwater-direction-author-view', '289-b009',
  '作者对读者担心未成三买被套说，只要未买到最低那一笔，总有被套的时候，并称大方向不错就没问题。',
  '市场风险|市场心理|操作策略|确认', 3, '方向不错未给可判阈值，总有/没问题是作者泛化和安抚强词，不认证每笔必套或保证未成买点、T+1锁定后最终回本。', ambiguity='author_direction_right_reassurance_not_risk_guarantee')
c(39, 'fearful-entry-can-split-two-no-proportions', '289-b009',
  '对同一担心，作者建议若害怕可分两笔买入。',
  '资金入场批次|仓位|市场心理|操作策略', 2, '两笔是次数而非必等额50%或认证读者每低补一些都合理，也未解决未成三买的全部确认问题。')
c(39, 'corrected-sector-rotation-not-only-third-line', '289-b012',
  '作者判断此前强势、近月调整较多的板块也会动，要求不只炒三线，重视比价而非假消息。',
  '板块轮动|比价关系|三线股|基本面', 4, '历史经验与判断，未认可读者对601333的动员或全部突破标注，原政治标签不作真实主体事实。')
c(39, 'retail-not-must-index-stock-second-line-consolidated-restart', '289-b013',
  '作者说散户未必买相对慢的指标股，可观察约10元二线中盘整充分、重新启动者。',
  '二线股|盘整|操作策略|资金管理', 3, '具体历史方法偏好，不给当前标的或固定盘整时长/启动阈值，也不使10元成为二线的严格定义。')
c(39, 'mar23-1325-minimum-divergence-not-five-return-center', '289-b016',
  '对3月23日13:25是否5分背驰，作者否定该级别，称只是最小级别背驰后对称拉回中枢，可当原中枢小级震荡。',
  '最低级别|背驰|中枢震荡|级别|确认', 1, '原没有给最小级确为1分/线段的命名，不因图为5分就改成5分结构背驰；开头不是的否定针对读者所问5分级别。',
  ['2007年3月23日15:38:46具体13:25例'], figs=[(290, 1)])
c(39, 'no-high-exit-low-purchase-is-add-not-repurchase', '290-b002',
  '作者指出高位未卖、低位再买就是加仓，不是回补，要求先分清向上与向下段的节奏。',
  '仓位|操作策略|机械化操作|成本', 1, '加仓与卖后回补按已有筹码流区分，不由低价本身认证任何新仓安全或读者000938获利可持续。')
c(39, 'small-capital-sell-all-buy-original-contradictory-wording', '290-b002',
  '谈小资金节奏时，固定汇编原页写“卖就全买”。',
  '仓位|操作策略|资金管理', 3, '主代理另看PDF290完整原页，原字如此；与先卖后买语境不顺，不静改全卖或据此推出全仓买入/卖出命令，需更明确来源才能唯一释义。', ambiguity='source_says_sell_then_all_buy_not_silently_corrected')
c(39, 'prior-sale-then-staged-repurchase-if-not-confident', '290-b002',
  '同段另明确说已先卖出后，若回补信心不足可以分单回补，作者认为这样心理压力较小。',
  '仓位|机械化操作|市场心理|操作策略', 2, '分单未规定笔数和份额，先卖是该回补语境前提，不把安抚变成无风险成交或未卖也可无条件加仓。')
c(39, 'theory-europe-us-same-futures-certificate-variable-source-scope', '290-b005',
  '答理论能否用于欧美股市，作者称都一样；另说期货略不同，因为交易凭证即时可变，而股票无此问题。',
  '期货|交易条件|市场规律|技术分析', 3, '保留即时可变原词而不擅定其变量/机制；未据简答确认读者美股T+0及无涨跌幅规则，更非当前各市场制度或期货风险完全相同。', ambiguity='futures_certificate_immediate_variability_not_defined')


keep('287-b003 287-b004', 'upper-l038-c-stage-procedure-down-side-sell-before-buy-reverse upper-l038-c-stage-learn-mastered-mode-then-return-with-experience',
     '39强调先练上下节奏、失步暂停，生理感应为类比，不使机械训练变成保证获利或无需结构判断。')
keep('287-b006 288-b000', 'upper-l038-c-stage-same-level-decomposition-fixed-level-definition upper-l038-c-stage-same-level-no-extension-three-overlap-six-two-consolidations',
     '39先把a正规化5分、A为多5分连接并含30分中心，A非必单独一个中心；吸收与三段构中心分支不取消38固定级别定义。')
keep('288-b001', 'upper-l038-c-stage-procedure-third-above-first-high-diverge-sell-else-hold upper-l038-c-stage-procedure-second-break-low-compare-prior-down-else-wait upper-l036-c-stage-simplify-unfinished-second-center-not-cancel-expansion-definition',
     '39扩成Ai/i+2及无盘背保护位延迟支，不能只看相邻Ai/Ai+1或把未来未完段重组改成既有已完历史切分；本级/高层观察分开。')
keep('289-b009 290-b002', 'upper-l035-c-stage-historical-t-plus-one-blocks-full-subminute-except-tzero upper-l038-c-stage-different-position-portions-at-different-levels',
     '分两笔/分单未定份额，也未解除未成买点、T+1与仓位风险；先卖后回补不同高没走后加仓。')
keep('289-b016', 'upper-l037-c-stage-c-direct-sublevel-contains-b-third-point upper-l037-c-stage-c-no-new-extreme-even-third-point-use-consolidation',
     '39作者否定5分背驰而判最小级后回原中枢，与37典型趋势c范围不同，未将所有小信号认成大级反转。')
keep('290-b005', 'upper-l037-c-stage-reader-forex-question-author-futures-second-point-caution upper-l037-c-stage-index-futures-direction-unchanged-extension-stronger-author-view',
     '作者说欧美通用/期货交易凭证即时可变，仍未细定义该变量；不能据此确认读者海外制度、消除期货延伸/风险区别。')
note('287-b005', 'source_reader_guidance', '作者提示公式较难可用纸笔画图，已读并实际核对公式图。', '来源内学习指令仅作上下文，不改变用户授权或把示意变作者证据。')
note('288-b004', 'historical-sector-self-report-and-next-date-tail', '3/23作者讲板块、旅游科技会表现及保密自述，末尾为3/26时间头。',
     '未核预测、机构与真实交易；3/26头仅管后段，原段仍3/23，原文字符不拆改。')
note('289-b000', 'historical-unverified-market-rumor-context', '3/26作者转述次日砸盘传闻和只点火不死顶自述已读。',
     '传闻/政治贬称与动机未证，不据此建立真实主体或触发交易、宣传和外部联络。')
issue('rhythm-training-physiology-and-profitable-sale-norms', '287-b003 287-b004',
      '赚钱卖/低回补无所谓错误为作者训练评价，机械节奏生理反应/大致周期为类比，非收益最优或实验事实。',
      '保留先练节奏与失步暂停，但不据长期训练保证盈利或把生理感应替代结构。')
issue('a-A-normalform-absorb-and-thirty-center-equality', '287-b006 288-b000',
      'a先规整5分，A分m个5分且含30分中心，A2破a高且A3不回可吸收为a`，一般考虑A3跌破a高；等高及归结过程未形式化。',
      '保留A含中心非A等于纯中心，后课更精条件前不补EPS或任何三段必充分构中枢。', True)
issue('Ai-pair-parity-protection-delay-k-and-unique-history', '288-b001 288-b002',
      'A0向上例奇偶定位，先比Ai/Ai+2盘背；否则Ai+3保护位及随后Ai+k+3破坏、Ai+k+4弱势联合。k偶仅前支明写，奇支沿记号。',
      '不得删联合条件、把保护破位当立即同价成交或补所有k/等值/完成算法；未来段不改已完唯一为作者主张未独证。', True)
issue('entry-batches-direction-Tplus1-and-sell-all-buy-source', '289-b009 290-b002',
      '大方向不错未定量且没问题非风险保证；两笔/分单非50%，高未卖后买是加仓；原页卖就全买不顺不能静改全卖。',
      '保留原字歧义与先卖后回补清晰部分，不补全仓命令或宣称T+1/未成三买问题已全解。', True)
issue('minimum-level-1325-not-five-and-return-center', '289-b015 289-b016',
      '作者13:25判最小级背驰非5分，并称对称回中枢是原中心小级震荡；未说最小级具体为1分/线段。',
      '后图5分周期不等结构级别，不据小级转折推大趋势结束或补当日所有区间点。', True)
issue('futures-certificate-variable-and-overseas-reader-rules', '290-b004 290-b005',
      '作者欧美都一样答复对象为理论，期货交易凭证即时可变未定变量/机制；读者美股T+0无涨跌幅不是本答逐项核验。',
      '保持固定历史语料，未查现行制度、不静补持仓量/合约数量唯一解释或认定各产品风险相同。', True)
issue('historical-sector-regulatory-risk-and-pressure-confirmation', '288-b003 288-b004 288-b005 289-b000 289-b001 289-b012 289-b013',
      '压力线3/23未破与3/26突破待确认分时，板块价格/成分股池、监管风险/传闻及政治自述为历史观点，未核实际收益/因果。',
      '后图不代确认，未认证读者601333动员或将当时10/15元标准当今天推荐。')
issue('commentary-dates-and-figure-provenance', '288-b004 288-b005 289-b000 289-b001 290-b002',
      '3/26尾头只支配后三段，3/23未动；两Ai示意原发未核，3/28行情后于文本；另看290原页确认卖就全买原字。',
      '原文/字符映射/坐标不改，图不补数学条件、源字或证明未来突破有效。')
relations = {
 'upper-l039-c-stage-up-buy-before-sell-down-sell-before-buy-rhythm': [('机械化操作','同级别分解','qualifies')],
 'upper-l039-c-stage-step-wrong-stop-adjust-mind-rhythm-before-resume': [('机械化操作','市场心理','qualifies')],
 'upper-l039-c-stage-a-plus-A-regroup-five-types-and-A-contains-thirty-center': [('同级别分解','结合律','qualifies')],
 'upper-l039-c-stage-compare-Ai-Ai-plus-two-force-consolidation-method': [('同级别分解','盘整背驰','qualifies')],
 'upper-l039-c-stage-center-can-grow-thirty-to-year-still-five-pair-operation': [('同级别分解','中枢扩展','qualifies')],
 'upper-l039-c-stage-pair-divergence-even-i-plus-two-sell-odd-buy': [('机械化操作','盘整背驰','qualifies')],
 'upper-l039-c-stage-no-divergence-even-hold-until-protection-break-then-exit': [('机械化操作','高低点','qualifies')],
 'upper-l039-c-stage-fearful-entry-can-split-two-no-proportions': [('资金入场批次','仓位','qualifies')],
 'upper-l039-c-stage-no-high-exit-low-purchase-is-add-not-repurchase': [('仓位','成本','qualifies')],
 'upper-l039-c-stage-mar26-second-line-ten-fifteen-and-third-line-regulatory-risk': [('监管风险','三线股','qualifies')],
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
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], '读者T+1/未成三买的焦虑、601333动员、13:25级别、000938交易及美股制度记述均只作上下文；作者未逐项认证涨停规则、具体股票或读者成交获利。'
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
        'note': 'a+A正规化与A含30分中枢、Ai奇偶和i/i+2同向比较、无盘背后保护条件与延迟操作分别保存；未来段不回写过去唯一分解是作者主张，卖就全买原字不修，最小级与5分背驰不混。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True, reviewer=REVIEWER, visual_review_note=f['note'],
             figure_source_review='本课3图全部查看，288两幅Ai示意原发/制作者未核，290行情图右端3/28晚于评论；公式示意不补k奇偶/相等/完成条件，后图不倒证突破确认。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 40 and Counter(x['lesson_number'] for x in ledger) == {39: 40}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [39], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(287, 291)), 'figure_objects_viewed': 3, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '39课40段4页3图及前后课边界同模型四轮；3跨日日期修正，a+A正规化、Ai奇偶/保护边界/延后买卖与源字歧义、历史小级信号分开，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


