"""Materialize the main agent's four-pass reading of lesson28.

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
BASE = 'c_stage_l028'
REVIEWER = 'Codex 主代理 / 阶段C上册28课同模型四轮复核'
SOURCE_SHA = '0286b78d29623f20ebea235d5cc0389c6eaef178a2c2b830ab7224c477a5d644'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-028' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 187
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 187 AND 203 ORDER BY pdf_page,id', (DOC,))]
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
    pending.append({'id': 'upper-l028-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})


c(28, 'fund-pyramid-language-is-author-opinion', '187-b013 188-b000',
  '第28课作者用“合法传销”等强烈措辞批评公私募基金与价值投资，并以公司利润向股价放大解释其资产虚拟化观点。',
  '基金|基本面|市场风险', 4, '这是作者2007年的争论性观点，不是法律分类、已核实机构行为或项目对所有基金的事实判决；1元利润/十倍增值为作者理论化例示。',
  ['第28课基金批评正文'], ambiguity='author_polemical_fund_and_valuation_claim_not_verified')
c(28, 'long-hold-from-long-buy-until-long-sell', '188-b001',
  '作者把长期持有理由限定为长期买点已出现而长期卖点未到，并用年线买卖点及一生约70至80根年K作比喻。',
  '持股|买卖点|年线|操作级别', 2, '反对价值持有是本段作者立场，不能抹去26中长线选股看基本面的另一个范围；人生K数非可检验交易周期。')
c(28, 'fund-redemption-and-capital-horizon-risk-view', '188-b002',
  '作者将基金资金类比为借来的钱，认为严重下跌时赎回会带来风险，尤其开放式基金可随时赎回，与长期稳定资金原则存在张力。',
  '基金|开放式基金|基金赎回|资金期限|市场风险', 1, '借贷/归零是作者类比与预测，不当基金法律资本结构结论或所有基金终必清盘的实证；不提供当前申赎规则。',
  ['2007年第28课作者对资金期限与赎回的风险分析'], ambiguity='fund_borrowing_analogy_and_collapse_prediction_unverified')
c(28, 'fund-nav-position-constraint-author-view', '188-b003',
  '作者认为基金经理受净值评价与单股持有比例约束，可能出现超配和调仓困难，基金持有也会减少市场可流动筹码。',
  '基金|仓位|流通量|市场风险', 3, '比例限制未给具体数值或法规来源；共同持有不自动证实违法串通，本文是作者结构性观点，不认证指控或制定攻击步骤。',
  ['第28课作者基金净值与仓位约束论述'], ambiguity='historical_fund_constraint_and_coordination_claims_unverified')
c(28, 'fund-monthly-adjustment-collapse-forecast', '188-b002 189-b003',
  '作者预测本轮牛市大调整、尤其月线中枢调整中会有基金崩溃，并认为周线就发生的可能较小。',
  '基金|基金赎回|走势中枢|走势预测|操作级别', 3, '2007当时未来判断和等级对比，不据后来的行情宣称该预测全部兑现，也不作当前风险预告。',
  ['第28课基金长期风险展望'], ambiguity='historical_fund_collapse_forecast_not_tested')
c(28, 'feb6-five-divergence-2720-two-paths', '189-b005',
  '2月6日解盘称已出现5分钟背驰；若上2720，周线第一段不演化下跌趋势而渐成2720附近中枢，否则可能在下方形成第二下跌中枢，并预期以后有更大级别背驰。',
  '背驰|走势中枢|操作级别|走势预测', 1, '两个如果分支和后续预测保留；不能把站上2720与中枢/背驰已完成混成一个已证事实。',
  ['2007年2月6日15:12上证解盘'], figs=((190, 1), (190, 2)), ambiguity='conditional_weekly_path_and_later_divergence_forecast')
c(28, 'feb7-rewritten-five-rise-end-one-divergence', '191-b001',
  '2月7日重写解盘称，5分钟背驰引发的5分钟上涨在11点后1分钟背驰中结束，进入5分钟中枢震荡；能否构成二买待后两日，不预测。',
  '背驰|走势中枢|第二类买点|操作级别|确认', 1, '日期从190尾时间头修正为2/7；待后两日不是当日已确认二买，1分结束5分上涨不等两者级别必须相同。',
  ['2007年2月7日20:43重写解盘'], figs=((191, 1),))
c(28, 'feb8-five-center-expands-thirty-conditions', '191-b005',
  '2月8日作者说下午5分盘整背驰后中枢向30分扩展，仍待完成确认；中枢确认且30分次级别以下背驰后站稳2720才看新上扬，2850上压力较大。',
  '盘整背驰|中枢扩展|走势中枢|操作级别|确认', 1, '且关系及完成确认/有效站稳前震荡条件保留，不拿后图2/9走势补确认时刻。',
  ['2007年2月8日15:10上证解盘'], figs=((191, 1),))
c(28, 'double-rise-half-sale-negative-cost-self-report', '191-b007 192-b000',
  '作者自述一股涨一倍以后找机会出半仓使其余成本为负，并称777继999后完成这一计划，仍看其中线题材。',
  '负成本|成本|仓位|资金管理', 3, '是作者账户自述；未给初始批次、真实卖价和费用，不能以涨一倍卖半简单算式认证严格负成本或保证后续赢家。',
  ['2007年2月8日777交易自述'], ambiguity='negative_cost_after_partial_sale_not_account_audit')
c(28, '600343-entry-and-index-strength-condition', '192-b004',
  '对15.8买600343者，作者否定那里为买点并说当天16附近应退出，认为中线尚可、短线有压；突破新高需大盘攻上2720显强才稳妥。',
  '买卖点|追高|操作级别|走势预测', 2, '15.8/16是当时答复，不变成当前价格指令；中线判断与大盘条件非未来收益保证。',
  ['2007年2月6日15:22对600343的答复'])
c(28, 'unskilled-reduce-operating-capital', '192-b010',
  '作者肯定降成本的进步，同时建议不熟练时先降低用于操作的资金。',
  '资金管理|操作熟练程度|成本', 2, '未逐项认证读者降本0.2元和同学20%的收益，也没规定所有账户同一比例。')
c(28, 'exrights-long-no-short-temporary-author-choice', '193-b002',
  '面对季月历史底部复权疑问，作者主张超长线不用复权；短线因除权缺口改变指标，可在除权后一定时间内有需要，熟练者也可不用。',
  '复权|MACD|周期K线图|操作级别', 1, '这是本答复建议，与15课5/10线日线不用而周月可复权的不同分析范围分别保留，不自动以较晚日期覆盖；一定时间未定量。',
  ['2007年2月6日15:34对季月图的答复'], ambiguity='adjustment_choice_scope_vs_earlier_average_system_not_unified')
c(28, 'macd-instead-of-private-average-force-not-prerequisite', '193-b005 193-b008',
  '对趋势平均力度，作者建议一般人直接MACD即可；私有指标需自己编、使用复杂，不是先MACD再另编的两步必要条件。',
  'MACD|缠中说禅趋势平均力度|操作熟练程度', 1, '读者误解被“不对”纠正；本答复没有给出指标代码或补齐15课面积/延伸长度算法。')
c(28, 'macd-center-divergence-95-author-claim', '193-b008',
  '作者称MACD虽精度差一点，只要配好中枢和背驰，95%以上没有问题。',
  'MACD|走势中枢|背驰|概率原则', 3, '95%以上是未给样本/任务口径的作者准确率主张，不作本项目检索准确率、交易胜率或算法评测数据。',
  ['第28课趋势平均力度替代工具问答'], ambiguity='author_95_percent_accuracy_not_measured')
c(28, 'icbc-fast-one-top-five-bottom-case', '194-b003',
  '作者以工行急速行情解释元旦后1分顶背驰引发急跌，随后下跌两中枢、三段B再破底，到2月6日出现5分背驰。',
  '背驰|MACD|走势中枢|操作级别|调整', 1, '不认可读者日/30分无背驰就理论失效的归纳；不同级别、两中枢与B三段按原答保留，后图不认证逐笔可成交。',
  ['2007年2月6日15:49工行答复'], figs=((193, 1),))
c(28, 'rebound-candidates-and-delayed-fall-risk', '194-b006',
  '作者说抢反弹偏向指标股及跌得多后背驰者，称后者可能有10%几空间；第一段未跌者若无强势新高，大盘反弹后可能补跌。',
  '反弹|背驰|补跌|操作级别|市场风险', 2, '肯定没问题/必须拉为作者强措辞，10%几原写法保留不认证收益；条件组合不是对所有权重股的无损保证。',
  ['2007年2月6日15:53反弹问答'], ambiguity='historical_rebound_confidence_and_return_not_tested')
c(28, '600016-five-divergence-amplitude-not-universal', '195-b001',
  '对600016五分背驰后涨幅，作者解释为此前跌多且为趋势结束，并结合板块、位置和前强势股，强调并非每次同力度，也须会卖。',
  '背驰|反弹|操作级别|操作策略', 1, '力度要看位置与背景，不把任意五分背驰都套10%以上；读者买入时点与浮盈不独立核验。',
  ['2007年2月6日15:58民生银行案例'], figs=((194, 1),))
c(28, 'kiss-crossing-broad-answer-only-auxiliary', '195-b004',
  '对“吻是不是短长均线交叉”，作者简答是，但马上说吻与MACD都仅辅助，关键仍是中枢。',
  '均线系统|MACD|走势中枢', 2, '这是该宽泛提问的简答，不将11课飞吻/唇吻未必交叉的具体定义静默改为所有吻必穿越。',
  ['第28课吻的简短问答'], ambiguity='broad_crossing_answer_vs_specific_kiss_types')
c(28, '600331-feb5-divergence-future-third-buy-conditional', '195-b007',
  '作者说600331五分背驰2月5日已发生，之后盘整待两日看能否突破回踩成小级别三买，否则仍可盘整，反对卖点未出就预测再跌。',
  '背驰|盘整|第三类买点|走势预测|操作级别', 1, '没有认可读者必须破17.6才背驰的预测；如果分支和可按小级别对冲的范围保留，不倒用后图确认。',
  ['2007年2月6日16:35对600331答复'], figs=((195, 1),))
c(28, '600495-reader-profit-not-real-buy-point', '196-b002 196-b003',
  '作者对600495读者按多级柱缩买后浮盈的叙述说是碰巧，买在买卖点之间而非真正三类买点；短差仍须看大级别中枢，走势强时卖点可选更大级别。',
  '买卖点|MACD|操作级别|走势中枢', 1, '浮盈3%不等买点判断被认可，作者未确认读者自造三次回拉必要程序；不把仅赚钱当技术定义通过。')
c(28, '600682-post-divergence-consolidation-two-paths', '196-b006',
  '对600682弱反弹，作者认为下跌尚缺两个中枢，可能盘整后再跌形成30分以上背驰；但大盘特别强时也可上破，并非必向下。',
  '背驰|走势中枢|盘整|操作级别|走势预测', 1, '最坏分支和向上可能同存，未逐项认可读者1/5分背驰判别；没跌透为该例作者判断，不补固定跌幅。',
  ['2007年2月6日16:51对S宁新百的答复'])
c(28, 'post-divergence-not-necessarily-v-reversal', '196-b007',
  '作者明确背驰后可先盘整再选方向，不必V形反转；抢反弹强调先有至少两个中枢的跌透过程。',
  '背驰|盘整|趋势转折|走势中枢|反弹', 1, '结合前述600682的盘整和趋势区别，不把反弹必须至少两中枢误说任何盘整背驰都无反弹。')
c(28, 'pure-short-difference-other-factors-constant-assumption', '196-b010',
  '作者区分综合市场与消息的分析和纯短差：短差时间内可把其他因素基本假设恒定，因而主要考虑技术因素。',
  '操作级别|基本面|技术分析|缠中说禅短差程序', 1, '基本假设不等真实恒定；同段基金持仓超过50%与消息等是作者当时未经核实的自述，不制作或执行针对机构的攻击方案。',
  ['第28课2月6日21:37关于分析时间尺度的答复'], ambiguity='short_horizon_constant_factor_assumption_not_guarantee')
c(28, 'shanghai-2980-five-minute-three-center-dates', '197-b003',
  '作者作业答案从2980后的5分下跌列三个中枢，原记1301055—1301345、2011105—2021110、2051005—2051330，第二为跌破30分以上大中枢的次级回拉三卖。',
  '走势中枢|下跌|第三类卖点|次级别|操作级别', 1, '时间串按原文保留，不用2/24读者主张把第二段改成2010935—2011410；后2/26作者解释单列，图框不能替结构证明。',
  ['2007年2月6日22:14上证作业答案'], figs=((197, 1),), ambiguity='compressed_times_and_later_reader_objection_not_silently_corrected')
c(28, 'third-sell-following-leg-usually-new-down-center', '197-b003',
  '作者说当第二中枢后下跌较前段MACD力度无明显减弱时须防第三中枢；三卖后除非力度特别弱、跌破马上拉回，否则一般不构成真正背驰，相应次级背驰只造一个下跌中枢。',
  '第三类卖点|背驰|走势中枢|下跌|MACD', 1, '一般与弱/迅速拉回例外都保留，不把三卖后永不背驰或最多三个中枢当无例外结论。',
  ['第28课该5分下跌及三卖后段的讨论'], figs=((197, 1),))
c(28, 'triple-nesting-five-one-subminute-case', '197-b004 199-b007 199-b008',
  '第三中枢后下跌弱于第二后，作者用5分背驰段内1分背驰段、再其更低级背驰三重收缩定位2月6日第二波下跌，强调不是早间第一波。',
  '区间套|背驰段|背驰|操作级别|最低级别', 1, '对应段包含不是任意三次指标背离；原未展示1秒行情，只作如果有1秒图的理论说明，不认证逐秒成交定位。',
  ['2月6日上证作业及22:21再说明'], figs=((198, 1),))
c(28, 'below-one-minute-histogram-special-comparison', '197-b004',
  '当1分钟是能看到最低图、须观察更低走势时，作者在本次急跌例比较柱子：黄白线常远离零轴，绿转红再绿但绿柱较前小、价创新低，视作1分次级背驰。',
  '最低级别|MACD柱波|MACD|背驰|操作级别', 1, '最低可视图内次级别比较的特例，不能抹去普通本级MACD回轴前提或以没有秒图假装已有秒级证据。',
  ['第28课2月6日快速下跌的最低图辅助判断'], figs=((198, 1),), ambiguity='subminute_analogy_without_observed_second_chart')
c(28, 'jan30-1035-previous-type-center-not-current', '198-b011',
  '2月26日作者答01301035属于前一走势类型的中枢，须区分同一走势类型里的中枢与下跌＋盘整中的盘整中枢。',
  '走势类型|走势中枢|走势分解|盘整', 1, '不是承认读者把1301055改成1301035；还须后29课走势完成解释，不能仅凭时间邻接替换中枢。',
  ['2007年2月26日16:12对前2月6日作业的追问'])
c(28, 'center-label-first-three-extension-optional', '199-b000',
  '作者说明通常标中枢只给前三段，后续延伸可省写，关键是知道后面属于延伸。',
  '走势中枢|中枢延伸|走势类型', 1, '省略文字标记不等延伸不存在或把中枢永远固定不再判扩展；作者没有认可CCTV全部解释。')
c(28, 'b-lower-than-a-not-prohibited-center-definition', '199-b003',
  '对1301055并非最低点、11:20又创新低的疑问，作者说定义未要求B低不能破A低，并指向29课第二种更大级别盘整。',
  '走势中枢|重叠|走势类型|盘整', 1, '原29课措辞“该级别更大级别的盘整”保留为待后课核；不由B可低推出任意未完成/无重叠片段可成中枢。')
c(28, 'completion-not-short-average-standing', '199-b006',
  '对连短均线都未站上能否算A段，作者说均线无关，关键在次级别将原走势类型完结，如何完结需看29课。',
  '均线系统|走势类型|完成|次级别', 1, '本段没给出完结的全部判别，不能自行用均线穿越或任意一段波动代替29课结构条件。')
c(28, 'third-five-center-departure-one-centers-two-needed', '200-b001 200-b002',
  '作者补充第三5分中枢后从2051330看的1分下跌须有两个1分中枢；02051410—02051436仅第一，次日9:51—10:08为第二，其第三段很弱，解释首波未成趋势背驰。',
  '背驰|走势中枢|操作级别|下跌|完成', 1, '中枢段数/一分内部数量与五分三个数量分开；弱第三段不补阈值，未把首次盘背等成完全无反弹。',
  ['2007年2月6日22:26上证1分例'], figs=((199, 1),))
c(28, 'three-four-center-count-author-frequency', '200-b001',
  '作者说一般一段下跌最多三四个中枢，超过四个极罕见。',
  '走势中枢|下跌|概率原则', 3, '一般和罕见与27延伸可更多中枢同存，不将最多作无例外上限，也不作已测频率。',
  ['第28课作业补充中的经验描述'], ambiguity='typical_center_count_not_hard_maximum')
c(28, 'connections-sublevel-or-lower-not-exact', '200-b006',
  '对中枢连接段是否一定次级别，作者回答不一定，但肯定次级别以下。',
  '中枢连接|次级别|级别', 1, '结合读者连接同级中枢的问题，只限制连接段相对级别，不改变中枢自身三段构成的递归条件。')
c(28, 'gap-infinitely-low-not-center-constituent', '200-b009',
  '作者称跳空级别无限低，不能成为任何中枢中的一段，与走势分解定理不矛盾。',
  '缺口|最低级别|走势中枢|走势分解', 1, '无限低为作者表述，不建立实际可无限交易层级；跳空本身不作中枢一段，不等含缺口的完整走势类型永远无效。')
c(28, 'type-level-by-contained-centers-not-connections', '200-b009',
  '作者区分已完成上涨下跌走势类型与中枢及连接：类型级别看所含中枢，含一个日线中枢为日线盘整，含两个以上为日线趋势，与中枢连接段级别无关。',
  '走势类型|走势中枢|中枢连接|级别|完成', 1, '同级、方向和完结仍按既有完整定义，不把任意混级两个中枢当日线趋势；两个以上原话不改成只需两根K。')
c(28, '600151-one-divergence-can-generate-five-rise', '200-b012',
  '作者否定600151当次为5分背驰，称2月1日1分背驰引发这次上涨；5分上涨不必由5分背驰起源，可经中枢扩展形成更大级别。',
  '背驰|中枢扩展|小级别转大级别|操作级别|上涨', 1, '否定/肯定的级别分开，能够经扩展不等所有1分背驰直接证明日线转势。',
  ['2007年2月6日22:35对600151的答复'], figs=((201, 1),))
c(28, 'divergence-at-least-own-type-larger-via-expansion', '201-b003 201-b004',
  '作者说5分背驰至少产生一个5分走势类型，也可经中枢扩展产生更大级别；1分背驰亦可能造成大顶底，以工行北辰后来逐步扩展为例。',
  '背驰|走势类型|中枢扩展|小级别转大级别|操作级别', 1, '至少和可以、逐步扩展联合保留，不把最低级结果预设最终最大级，回拉未必为趋势。')
c(28, 'minimum-five-three-done-further-center-development', '201-b006 201-b007',
  '作者说本次5分背驰已带来5分三段走势，反弹此时结束也满足最低要求；继续反弹须依中枢延伸扩展，第一类点由背驰、二三类由中枢演化来描述。',
  '背驰|走势类型|中枢延伸|中枢扩展|第一类买点|第二类买点|第三类买点', 1, '原“制造三段”不静改成已形成上涨趋势；第一类/二三类的机制性概括不替代各类完整定义，后续需新结构非原背驰无限作用。')
c(28, 'thirty-first-sell-aligned-daily-leg', '202-b001',
  '作者说30分背驰制造至少30分第一类卖点，若该30分卖点恰在日线背驰段，也可同时为日线第一类卖点。',
  '背驰|背驰段|第一类卖点|操作级别|区间套', 1, '原答以恰在/也同时描述，需要对应大级别背驰段，不能任意小卖点自动升级日线；与27包含/精确范围限制一起保留。')
c(28, 'after-thirty-top-two-five-types-second-sell', '202-b002',
  '在前述30分顶背驰后，作者描述先5分向下完成，再5分向上反抽，走势类型也可为盘整；第二个5分背驰构成第二类卖点。',
  '第二类卖点|走势类型|盘整|操作级别|背驰', 1, '下再上及完成前提保留，不能把任何次级反弹第一根K当二卖；原第二个5分背驰按上下文，不删为必须两个趋势。')
c(28, 'third-sell-after-consolidation-break-and-retest', '202-b003',
  '第三类卖点的常见路径是未马上下跌而先盘整，后跌破中枢，次级反抽不回中枢。',
  '第三类卖点|盘整|走势中枢|次级别', 1, '一般/常见不替换全部三卖定义，次级和不回中枢都不可省。')
c(28, 'feb8-index-center-down-up-down-after-one-top', '202-b007',
  '2月8日作者定位当时指数中枢，自2月7日11点后背驰起为下上下，5分或30分图可观察。',
  '走势中枢|走势类型|操作级别', 2, '图上可观察不等图周期自动赋同一严格中枢级别；与此前确认/扩展语境同存。',
  ['2007年2月8日15:41对指数中枢答复'])
c(28, 'sixty-leg-before-lower-precision-not-reader-morning', '202-b014',
  '对000919读者上午自称1小时背驰，作者问当时是否新高，并说似是昨日下午末小时才创新高；精确60分位置须先进背驰段再看15、5、1分。',
  '背驰段|操作级别|区间套|确认', 1, '好象原为不确定语气，不认证读者上午点位；本段未逐级展示完整定位，不能称已确认日线或60分背驰。')
c(28, 'center-max-low-min-high-first-three-not-all-shrinking', '203-b001',
  '作者肯定MAX低点、MIN高点的中枢区间表达，但说未必很窄，一般先看前三段，后续须分围绕震荡延伸与扩展，复杂者可为三角或矩形。',
  '走势中枢|重叠|中枢延伸|中枢扩展|三角形整理', 1, '限定原问已在构中枢三段语境，不对全部后续片段不断取交集压窄，也不取消完整次级/连续/完成前提。')
c(28, 'second-buy-first-retest-may-grow-large-consolidation', '203-b007',
  '作者说次级上涨后第一次次级回调可成二买，之后常演化大级别盘整，超级底部尤其如此；须看中枢演化及次级走势以判断大中枢二买。',
  '第二类买点|次级别|盘整|走势中枢|完成', 1, '其后肯定有利润为作者主张非可执行收益证据；不是认可读者二买只看中枢第三段的简化。',
  ['2007年2月8日16:31二三买区别答复'], ambiguity='profit_guarantee_and_larger_center_evolution_not_fully_formalized')
c(28, 'third-buy-smaller-center-than-broken-one', '203-b007 203-b011',
  '作者将三买判断所涉中枢级别小于下方被突破中枢作为区别；若更大，就转为中枢扩展或延伸中的新中枢等情况。',
  '第三类买点|第二类买点|走势中枢|中枢扩展|中枢延伸|级别', 1, '原中枢指代按该二三买问答保留，不等第三买点自身级别必须小于原中枢；唯一不同是本段比较口径，不覆盖全部定义前提。',
  ['2007年2月8日二三买及16:42追问'], ambiguity='center_referent_and_point_level_not_unqualified_equivalence')
c(28, 'small-divergence-large-impact-two-contexts', '203-b014',
  '作者列小背驰发挥大作用的两情形：处在大级别背驰段中；或行情急促时反转幅度可大，例工行元旦后、北辰和酒股。',
  '背驰|背驰段|操作级别|小级别转大级别|调整', 1, '大级别背驰段/急促行情两支不能删，幅度大不自动等大级别转势已完成；与201逐步扩展机制分条保留，不由一句否则推不可能扩展。')
c(28, 'exit-during-rising-divergence-skill-demand', '202-b004',
  '作者偏向在上涨中抓背驰卖出，称效益回报最高，但技巧要求高，须艰苦学习实践。',
  '第一类卖点|背驰|操作熟练程度|操作策略', 2, '最高回报是作者策略评价，未比较费用/通道或实证收益；不把未完成柱片预判当任意可保证的极值成交。')

keep('188-b002', 'upper-l026-c-stage-capital-deadline-self-imposed-trading-stop upper-l026-c-stage-jan31-stable-long-funds-no-borrowing',
     '28把长期稳定资金原则用于批评基金赎回压力，借贷只是作者类比，不倒推现行法律关系。')
keep('193-b002', 'upper-l015-c-stage-five-ten-ex-rights-daily-vs-week-month',
     '15在5/10均线系统允许周月复权，28针对超长线/MACD不同建议，按分析对象分别保存，不自动宣布全局修订。')
keep('193-b005 193-b008', 'upper-l015-c-stage-average-force-area-divided-by-time',
     '28说私有指标一般人可不用、MACD可替代，不是两步共同必要，也未补面积/时间/长度完整实现。')
keep('195-b004', 'upper-l025-c-stage-kiss-average-and-macd-auxiliary-not-center',
     '28宽泛说吻交叉后马上限定辅助，与25中枢区别一致，不能回改各吻细分定义。')
keep('192-b007', 'upper-l025-c-stage-buy-and-sell-completes-operation',
     '会买会卖是完整交易轮次提醒，不是认可读者联通30分钟背驰或其所有交易成绩。')
keep('197-b004 199-b007 199-b008', 'upper-l027-c-stage-nested-legs-must-be-inside-parent upper-l027-c-stage-finite-levels-no-unique-mathematical-point',
     '28增加5分/1分/更低三层具体实例，仍要求相应段包含；无秒图不伪造秒证据或无限点精度。')
keep('199-b003 203-b001', 'upper-l017-center-definition upper-l027-c-stage-center-b-may-exceed-a-extreme-with-overlap',
     'B越A极值和MAX低/MIN高公式不取消至少三个连续完成次级走势条件，不把所有延伸都重取交集。')
keep('200-b006 200-b009', 'upper-l018-c-stage-center-connection-below-sublevel-gap',
     '28再明中枢连接可低于次级、纯跳空不成中枢一段，连接级别不决定整体走势类型级别。')
keep('202-b010 203-b014', 'upper-l024-c-stage-early-higher-trend-small-divergence-limited upper-l024-c-stage-rapid-top-small-divergence-impact',
     '盘中回档非固定50%、大级别背驰段/快速末段两例再限定；不把小级别永远无大作用或必大转折都概括为通则。')

issue('fund-capital-redemption-and-polemical-claims', '187-b013 188-b000 188-b002 188-b003 189-b001 189-b003',
      '合法传销、借贷类比、公司1元/股价十倍、联合持有/崩溃预言及作者交易自述均未独立核实，不是法律事实或已测金融定理。',
      '保留历史作者观点/条件；原文操盘自述作上下文，不制作针对基金攻击的执行方案，不查现行规则来冒充2007来源。')
issue('adjustment-choice-and-private-force-versus-macd', '193-b002 193-b005 193-b008',
      '超长线不用复权与15周月可复权的分析语境不同，短期一定时间未定量；MACD可替私有指标而非共同必要，95%以上无样本。',
      '不自动按日期覆盖，不由图中参数补私有指标代码或统一有效性胜率。', True)
issue('homework-center-dates-reader-requote-and-type', '197-b003 198-b003 198-b004 198-b005 198-b006 198-b008 198-b011 199-b000 199-b003 199-b006',
      '2/24深潜问题原误归作者已修，CCTV解释仍读者；2/26作者把01301035归前走势中枢并指29课完成，第二中枢原时间不按读者笔误说替换。',
      '保留原压缩时间与嵌套引语层次，29未读前不补结束算法或把读者观点整套认作作者。', True)
issue('subminute-triple-nesting-and-normal-macd-premise', '197-b004 199-b007 199-b008 200-b001 200-b002',
      '最低可视1分内的更低级柱比较可远零轴，是快速例特例；三重包含须对应5分/1分/其次级，1秒图只是如果有，并无实测秒数据。',
      '不抹普通本级回轴前提，不把最低图或形似柱波当已定义秒级中枢，不混五分第三与一分第一第二。', True)
issue('post-divergence-minimum-and-expansion-to-larger', '196-b006 196-b007 200-b009 200-b012 201-b003 201-b006 201-b007 203-b014',
      '背驰可先盘整、三段最低走势不等趋势；大级别后果须中枢扩展/延伸，不是原背驰永久作用；203两大作用情形与逐步扩展不同层次。',
      '走势类型/中枢/连接三层分开，至少和可能不能互换，不按任何1分信号直接宣称日线反转完成。', True)
issue('second-third-points-center-referents-and-daily-alignment', '202-b001 202-b002 202-b003 203-b001 203-b007 203-b011',
      '30分卖点对齐日线背驰段、二卖五分盘整类型、二三买的中枢级别指代及MAX低/MIN高均有上下文，不能简化成一根柱/中枢第几段即可买。',
      '保持对应大级别/次级完成/不回中枢条件，后29及后续三类定义再核，原肯定盈利不是实证。', True)
issue('historical-probability-cost-percent-and-signals', '189-b005 191-b005 191-b007 192-b004 193-b008 194-b006 195-b001 196-b002 200-b001 202-b010',
      '2720/2850分支、777出半负成本、95%准确/反弹10%几/最多三四中枢皆当时作者主张；读者3%浮盈未成为真正买点认可。',
      '不认证账户/概率、未来确认时点或所有反弹等幅；不把不能等额外确认变为不等信号成立。')
issue('embedded-dates-and-figure-provenance', '190-b001 191-b000 191-b004 191-b005 198-b002-s01 198-b003 198-b004',
      '9段解盘按2/7 20:43及2/8 15:10分组，3段读者复原；10图6文后4原发未核，2/24读者内所引2/6作者头不污染引号外。',
      '全文/字符/坐标不动，主图右端晚于旧光标才是后加证据，图框和数字不替原文语义证明。')

note('188-b004 189-b000 189-b001 189-b002 189-b004', 'historical-self-report-polemical-and-method-context',
     '作者与基金对抗、短差/负成本自述、净值压力/赎回推演及独立承担责任、理论客观性宣称完整已读。',
     '历史观点和自述不认证操盘、串通、账户或法律事实，不把攻击性叙事改造成交易执行指导；资金/风险主张已按条件另抽。')
note('190-b000 190-b001 191-b000 191-b002 191-b003 191-b006', 'dated-stock-comparison-and-entry-cautions',
     '777/999技术成绩比较、涨跌消失的境界比喻、2/7重写引言和938买入责任/不追高、2/8个股突破叙述已读。',
     '自评不代替收益验证；不把其所言价格当当前建议；末时间头只管后段，已修9段解盘日期。')
note('197-b001 197-b002 198-b003 199-b009', 'homework-and-quoted-introduction',
     '5分/1分作业、公布答案、2/24读者引号内的原作者公布标题，以及数学书复习提醒已读。',
     '作业指令不改变工具权限，空引语不额外证明技术判断；引号外两问已复原读者，数学类比非独立证明。')
note('203-b004 203-b008', 'practice-reminder-and-future-detail',
     '作者对空仓错过背驰的劝学及二三买细节以后再说的提示已读。',
     '劝学不认证读者所有机会，预告不等完整定义和算法已在此给出。')

relations = {
    'upper-l028-c-stage-fund-redemption-and-capital-horizon-risk-view': [('基金赎回', '资金期限', 'related')],
    'upper-l028-c-stage-exrights-long-no-short-temporary-author-choice': [('复权', '操作级别', 'qualifies')],
    'upper-l028-c-stage-macd-instead-of-private-average-force-not-prerequisite': [('缠中说禅趋势平均力度', 'MACD', 'qualifies')],
    'upper-l028-c-stage-below-one-minute-histogram-special-comparison': [('MACD柱波', '最低级别', 'qualifies')],
    'upper-l028-c-stage-connections-sublevel-or-lower-not-exact': [('中枢连接', '次级别', 'related')],
    'upper-l028-c-stage-type-level-by-contained-centers-not-connections': [('走势类型', '走势中枢', 'requires')],
    'upper-l028-c-stage-divergence-at-least-own-type-larger-via-expansion': [('小级别转大级别', '中枢扩展', 'requires')],
    'upper-l028-c-stage-minimum-five-three-done-further-center-development': [('第一类买点', '背驰', 'related'), ('第二类买点', '中枢扩展', 'related')],
    'upper-l028-c-stage-third-buy-smaller-center-than-broken-one': [('第三类买点', '走势中枢', 'qualifies')],
}


for r in rows:
    r['relations'] = [{'source': a, 'target': b, 'type': t} for a, b, t in relations.get(r['id'], [])]
by_passage = defaultdict(list)
for r in rows:
    for e in r['evidence']:
        by_passage[e['passage_id']].append(r)
for item in pending:
    item['lesson_numbers'] = sorted({int(passages[x]['unit_id'].split('-')[1]) for x in item['passage_ids']})
    if item['id'].endswith('embedded-dates-and-figure-provenance'):
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
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], '读者作业笔误说、CCTV解释、多级柱缩买入3%及三次回拉设想不作作者证据；有盈利不等买点正确。'
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
        'note': '基金批评为历史作者观点，复权/平均力度与MACD分语境；三重背驰对应包含，纯跳空/中枢连接/类型级别分层，最低结果/后续扩展、二三买条件保留。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True, reviewer=REVIEWER, visual_review_note=f['note'],
             figure_source_review='10图全部实际查看；6文后行情4原发未核，旧光标不遮盖右端未来K；读者所框中枢和MACD柱值不替作者完整结构证据。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 187 and Counter(x['lesson_number'] for x in ledger) == {28: 187}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [28], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(187, 204)), 'figure_objects_viewed': 10, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '28课187段17页10图同模型四轮；9解盘日期/3嵌引读者修正，基金观点/复权/最低图特例及中枢扩展层次保留，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


