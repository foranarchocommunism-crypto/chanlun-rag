"""Materialize the main agent's four-pass reading of lesson38.

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
BASE = 'c_stage_l038'
REVIEWER = 'Codex 主代理 / 阶段C上册38课同模型四轮复核'
SOURCE_SHA = '98e2563f9b6e2d301048b40f40e8072aa15ffb996d8adc9d467fd3949ca739bf'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-038' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 75
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 281 AND 286 ORDER BY pdf_page,id', (DOC,))]
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
    pending.append({'id': 'upper-l038-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})
















c(38, 'learn-mastered-mode-then-return-with-experience', '280-b001',
  '作者建议暂时不能吃透更深课程时，先选能掌握的级别与模式实践，经验增加、有直观问题后再回头学习。',
  '操作熟练程度|操作级别|操作策略', 2, '以理解背驰和选适合级别为前提，不是未掌握条件即可盲目交易，也未证明一招必盈利。')
c(38, 'same-level-decomposition-fixed-level-definition', '280-b002',
  '同级别分解是把所有走势按一个固定级别的走势类型分解；多义可换视角，但不等于胡乱分解。',
  '同级别分解|同级别|走势分解|走势类型|走势多义性', 1, '固定分解规则与参数后才谈唯一，不把不同级别/不同规则所有分法都要求一个相同切点集合。')
c(38, 'good-rule-unique-and-same-level-uniqueness-author-claim', '280-b002 281-b001',
  '作者要求好分解在其规则下保证唯一，并据走势分解定理及结合律宣称该同级别分解唯一、适于机械操作。',
  '同级别分解|走势分解|结合律|机械化操作', 1, '原文只称容易证明而未给形式算法、起点/终点全部约定和证明；记录作者结论，不宣称本项目已独立数学证明唯一性。', ambiguity='author_uniqueness_claim_not_full_formal_proof')
c(38, 'thirty-mode-up-consolidation-participate-avoid-down', '280-b003',
  '以30分为操作标准时，将图形分为30分类型连接，只选择上涨和盘整，避开所有下跌类型。',
  '同级别分解|操作级别|上涨|盘整|下跌|操作策略', 1, '限定该同级别操作视角，不抹盘整内部低级下行或改成长持所有下跌；需实际识别各类型完成。')
c(38, 'one-forming-same-level-center-then-next', '280-b003',
  '在该同级别操作视角中，只针对一个正在完成的同级别中枢；完成后转而关注下一个同级别中枢。',
  '同级别分解|走势中枢|完成|操作策略', 1, '与纯中枢延伸/扩展观察模式分开，不把此处完成擅等同后文所有三买/中枢延伸结束状态。')
c(38, 'same-level-no-extension-three-overlap-six-two-consolidations', '280-b003',
  '同级别分解本级不需延伸或扩展概念：30分例中三段5分上下上或下上下有共同价格区间即成中枢；延伸成六段则当两个30分盘整类型连接。',
  '同级别分解|中枢延伸|中枢扩展|盘整|重叠|次级别', 1, '六段指实际次级类型非六根K，三段共同重叠及完成条件保留；仅本级分解规则，不普遍取消中枢扩展定义。')
c(38, 'consolidation-plus-consolidation-allowed-only-mode-scope', '280-b003',
  '本级同级别分解允许盘整+盘整；作者说明此前不允许这种连接，说的是非同级别分解方式。',
  '同级别分解|盘整|走势类型连接|走势分解', 1, '按分解方式保存范围，不把33盘整相加可变级别与本课本级记账连接强合成一个无条件断言。')
c(38, 'sublevels-need-not-use-same-mode-can-extend', '280-b004',
  '本级做同级别分解，不要求其次级别也如此；次级别仍可用中枢延伸、扩展确定，只须不违结合律和分解唯一性且便于判断操作。',
  '同级别分解|次级别|结合律|中枢延伸|中枢扩展', 1, '选择分层规则不等层级随意改名或可随意交换时序，明晰易用不替代定义。')
c(38, 'hybrid-rule-own-level-all-below-and-above-ignored', '280-b005 281-b000',
  '作者给一套混合规则：本级不定义中枢延伸、允许盘整+盘整；本级以下所有级别允许延伸、不允许盘整+盘整；以上级别在该分解视角不考虑。',
  '同级别分解|级别|盘整|中枢延伸|走势类型连接', 1, '跨页读全，本级/全部以下/以上三种作用域不能互换；不考虑高层是此方法视角非市场高层不存在。')
c(38, 'bull-bear-label-relative-to-chosen-thirty-mode', '281-b001',
  '作者在机械同级别视角把30分上涨称牛市、否则称熊市，强调按所选级别逐段操作而不依赖市场总体牛熊标签。',
  '同级别分解|机械化操作|操作级别|上涨|宏观市场判断', 3, '牛熊为该方法局部口径，不将30分转折改成宏观牛熊定论，也不取消前段允许盘整参与。')
c(38, 'different-position-portions-at-different-levels', '281-b002',
  '同级别分解可嵌入较大操作系统：把一定量筹码按一较小级别操作，另一定量按更大级别操作，作者称可借此不断降成本。',
  '同级别分解|仓位|操作级别|机械化操作|成本', 2, '未给分仓比例，降成本是作者目标，不保证每段成交/盈亏或把不同部分的信号混成全仓条件。')
c(38, 'active-swings-profit-time-proportional-author-claim', '281-b003',
  '作者称足够活跃、震荡大的股票按该机械方式利润与时间成正比，时间够长可超任何单边上涨。',
  '机械化操作|幅度|成本|市场风险|走势预测', 3, '利润线性/必超单边为作者强主张，无成本误差/样本模型，未认证任意震荡都可稳定盈利或永不失误。', ambiguity='author_linear_profit_and_superiority_unverified')
c(38, 'historical-level-amplitude-ranking-suggestion', '281-b003',
  '作者建议计算历史某级别平均震荡幅度，选择该幅度较大的股票组来做上述操作。',
  '幅度|操作级别|机械化操作|技术分析', 2, '只给研究思路，未给窗口/数据复权/费用/生存偏差/执行算法，也未在本项目运行收益回测。')
c(38, 'small-time-rich-full-position-large-partial-applications', '281-b003',
  '作者称同级别方法适合时间充裕的小资金全仓操作，也可供大资金一定量差价操作或庄家降本，各具体应用方法不同。',
  '交易容量|仓位|资金管理|机械化操作', 2, '原适用经验不构成对用户全仓建议或保证风险可控，未给资金阈值/仓位比例，庄家语境不触发实际市场行为。')
c(38, 'procedure-start-down-divergence-first-up-exit', '282-b000',
  '所举30分机械程式从下跌背驰开始，随后第一向上类型依内部结构判背驰或盘背结束点，先卖出，再观察第二向下段。',
  '同级别分解|机械化操作|背驰|盘整背驰|完成', 1, '是所选30分分解且从已判下跌背驰出发的流程，不是任意两段折线或未完成拐头即确认终点。',
  ['282-b000所举30分同级别机械流程'], figs=[(281, 1)])
c(38, 'procedure-second-not-break-first-low-rebuy', '282-b000',
  '第二向下段若不跌破第一向上段低点，按所举程式重新买入。',
  '机械化操作|同级别分解|高低点|买点', 1, '依完整段与所举程式判断，不把盘中一触不破就充分确认第二段完成；原未给EPS或固定K数。',
  ['282-b000从下跌背驰出发的30分同级别流程'], figs=[(281, 1)])
c(38, 'procedure-second-break-low-compare-prior-down-else-wait', '282-b000',
  '若第二向下段跌破第一段低点，但与第一段前的向下段形成盘整背驰，也重新买入；否则继续观望，直到新的下跌背驰。',
  '机械化操作|同级别分解|盘整背驰|背驰|高低点', 1, '比较对象是第二下段与首上段之前的下段，非第二下段与首上段不同向比较；只破低本身不等新买点。',
  ['所举30分流程第二段破低分支'], figs=[(281, 1)])
c(38, 'procedure-third-below-first-high-sell', '282-b000',
  '第二段重新买入后出现第三向上段，若第三段高点低于第一段高点，程式要求先卖出。',
  '机械化操作|同级别分解|高低点|卖点', 1, '原本分支用低于，未在此单列等高处理；不能补出未规定容差或由未创新高普遍宣称已确认趋势背驰。',
  ['所举30分流程第二段已回补后的第三段'], figs=[(281, 1)])
c(38, 'procedure-third-above-first-high-diverge-sell-else-hold', '282-b000',
  '第三段超过第一段高点时，若相对第一段盘整背驰则卖出；若不盘背则继续持有。',
  '机械化操作|同级别分解|盘整背驰|高低点|持股', 1, '先有超过和同向段比较，再区分力度；并非任何新高卖出或新高无风险。',
  ['所举30分流程第三段超过首段高点'], figs=[(281, 1)])
c(38, 'procedure-repeat-up-until-no-new-high-or-divergence', '282-b000',
  '流程可重复，直到下一向上30分类型相对前一向上类型不创新高或盘整背驰，结束该向上运作；此过程先买后卖。',
  '机械化操作|同级别分解|盘整背驰|高低点|完成', 1, '此处不创新高与前子分支低于措辞分别存，不私补全等高边界；向上运作不等宏观上涨趋势结束。',
  ['所举30分同级别机械流程'], figs=[(281, 1)])
c(38, 'procedure-down-side-sell-before-buy-reverse', '282-b000',
  '向上运作结束后，从该背驰点进入向下运作；作者说把流程反过来，采取先卖后买。',
  '机械化操作|同级别分解|买卖点|下跌', 1, '是持有筹码的卖出回补方向描述，未授权裸卖空/杠杆，也未列尽每个反向等值分支。',
  ['前述向上运作已结束的所举30分流程'], figs=[(281, 1)])
c(38, 'mar21-five-day-line-fallback-strength', '282-b001',
  '3月21日作者对不会看图者给出看5日线、不破则暂无问题的指数辅助口径。',
  '均线|确认|操作熟练程度|宏观市场判断', 3, '具体历史解盘口径，不代替中枢、背驰或买点定义，原政治贬称不作机构事实。')
c(38, 'mar21-boc-rest-await-five-day-line-author-view', '282-b002',
  '作者把当时中行休息说成等待5日线上来，认为大盘股难持续远离该线。',
  '均线|板块轮动|宏观市场判断', 4, '历史经验判断而非所有大盘股固定均线距离或收益规律，未核机构因果。')
c(38, 'mar21-hold-partial-swings-more-cash-no-fewer-shares-self-report', '282-b003 282-b004',
  '作者自述其减成本方式使钱增加而筹码不减，并说所论14股前8只大多翻倍、持有加部分短差可不断降成本而永远不败。',
  '成本|仓位|持股|市场风险|机械化操作', 4, '收益与永远不败为作者自述/强措辞，没有账户/样本核验，不认证内幕消息、实盘利润或零风险。', ambiguity='author_return_and_never_lose_self_report_unverified')
c(38, 'mar22-three-closes-and-jan24-feb27-pressure-line', '282-b006',
  '3月22日作者关注随后三天能否收在前期高位，称这样突破有效性就有保障；当日受阻0124与0227连线，其有效突破是后市关键。',
  '确认|经验压力线|高点连线|突破|走势预测', 1, '是作者当时保证性条件判断而未实测，三天未在此定交易日/具体收盘阈值，非所有突破一律三天；后图至3/23不能证未来三天全通过。',
  ['2007年3月22日15:29:02指数解盘'], figs=[(283, 1)])
c(38, 'steady-no-rush-wait-opportunity-author-strategy', '283-b000',
  '作者说机会未成熟就稳打不冒进，反复震荡等待，不因他人急进而跟随。',
  '操作策略|当下|市场心理|确认', 3, '规范策略与行为自述不证明其账户不受损或可预知机会，贬称不作真实机构分类。')
c(38, 'mar21-nonferrous-zinc-bull-futures-risk-view', '283-b008',
  '作者预期有色金属牛市较长、国内锌期货将推出，同时提醒期货风险较股票大，时间经验不足应少碰。',
  '期货|市场风险|操作熟练程度|宏观市场判断', 3, '原2007年推出前预测与经验提醒，未确认当前产品/制度，也不推所有期货风险固定大于所有股票。')
c(38, 'daily-divergence-possible-two-centers-or-one-more', '284-b001',
  '答日线上涨背驰是否可能，作者说可能存在，计去年5月后中枢已有两个且压力线未破；若上面再延伸一个日中枢则另看。',
  '背驰|走势中枢|中枢延伸|经验压力线|走势预测', 1, '可能非已确认，未逐字确认读者双0轴回试；图后续日K不撤原不确定性，亦不认证作者8股收益。',
  ['2007年3月21日16:13:10具体指数答复'], figs=[(284, 1)])
c(38, 'return-first-not-third-later-not-return-can-be-third', '284-b006',
  '作者对第一次回到中枢、第二次未回的例子说，回到中枢者不是三买，第二次未回才是三买。',
  '第三类买点|次级别|中枢震荡|确认', 1, '这只是该前次回中枢仍震荡的例子，须与后答第一次有效回抽区分，不改为任何多次已有效不回都重复三买。')
c(38, 'first-effective-retest-only-later-no-return-not-third', '285-b004',
  '作者解释跌回中枢仍是围绕震荡，连所说回抽都算不上；第一次有效回抽不到中枢是三买卖点，之后再上去回抽仍不回也不再算三买卖点。',
  '第三类买卖点|次级别|中枢震荡|确认', 1, '第一次是有效脱离后所指层级回抽，不把第一次尝试离开或次次级内部两回抽混同；原不回未在此给相等/EPS形式规则。')
c(38, 'third-point-and-center-extension-end-same-object', '285-b004',
  '作者把第三类买卖点与中枢延伸结束说成一回事情，并让读者参照此前定义。',
  '第三类买卖点|中枢延伸|完成|走势中枢', 1, '该纯中枢/三买语境不覆盖本课同级别模式本级不定义延伸的不同规则，亦非此后不可能更大中枢。')
c(38, 'abc-macd-five-chart-ac-compare-c-internal-precision', '285-b001',
  '对三段5分ABC构30分盘整的问法，作者说用MACD时5分图通常较清楚，比较仍是A和C，并可参考C内部结构提高定位精度。',
  'MACD|盘整背驰|指标对比|区间套|次级别', 1, '图周期辅助不等对象级别，比较非只看C内部；没有在本答单独回答读者刚上0轴能否判盘背的问题。')
c(38, 'consolidation-c-need-not-highest-no-new-high-weak-macd-aux', '285-b008',
  '作者说ABC盘整的C不必高过A；若连新高也创不出则力度更弱，无需MACD辅助，该处MACD主要用于创新高时比较力度。',
  '盘整背驰|高低点|MACD|指标对比|背驰', 1, '本问ABC盘整C非37整体趋势末c，不撤其创新高低必要条件；无新高并非凭一根价线就自动确认所有完成/背驰。')
c(38, 'two-subsub-retests-complete-one-sublevel-retest', '285-b011',
  '作者解释所问两次回抽是次次级：一个次级类型至少三段次次级，第二次内部回抽才完成该次级回抽。',
  '第三类买点|次级别|完成|走势终完美', 1, '原只字按指代转述而原证据不改；并非同级两个完整有效回抽都算首次，也不限定所有回抽只能恰三段。')
c(38, 'mar22-small-consolidation-divergence-and-shanghai-shenzhen-after-1430', '285-b014',
  '3月22日作者说0124/0227线不易一次突破，当时1分或5分MACD有小盘背；14:30后沪深走势背离为其提示信号。',
  '盘整背驰|MACD|指数走势背离|经验压力线|确认', 1, '沪深走势背离是两指数比较，不静合MACD技术背驰；作者事后判读不保证每次背离都跌或可同价卖出。',
  ['2007年3月22日15:42:32对尾盘回落的答复'], figs=[(286, 1)])
c(38, 'segmentation-and-third-end-confirmation-internal-divergence', '286-b002',
  '作者说背驰、盘背是走势分段依据；三买卖确认盘整结束，最终还要看内部结构的背驰或盘背。',
  '背驰|盘整背驰|走势分解|第三类买卖点|完成', 1, '并未给读者要求的固定跌多少量化阈值，分段需对象/级别/内部完成，不能等跌后才机械补确认。')
c(38, 'nested-divergence-exit-staged-by-capital', '286-b002',
  '上涨进入背驰区间套时作者要求陆续退出，小资金可等最后几个价位，大资金则不能如此集中等待。',
  '区间套|背驰段|交易容量|资金管理|卖点', 1, '容量约束而非提前任意卖或大资金无误成交；最后价位是作者操作理想，未提供实时定位保证。')
c(38, 'miss-first-sell-use-second-not-wait-third', '286-b002',
  '作者要求第一卖点未走应在第二卖点走，若等第三卖点可能已跌很多，宁卖早不卖迟。',
  '第一类卖点|第二类卖点|第三类卖点|操作策略|市场风险', 2, '原具体退出建议不认证所有第二卖点都在更好价或第三卖点总固定跌幅，仍依所选操作级别。')
c(38, 'boc-small-capital-amplitude-not-general-investor-target', '286-b005',
  '作者当时说一般投资者没必要参与中行，因其幅度不一定满足小资金要求，应看走势。',
  '交易容量|幅度|资金管理|操作策略', 3, '是具体历史品种及资金差异，不构成当前买卖建议；作者对局/底牌自述未核，也未推荐读者北京旅游。')
c(38, 'stock-not-one-group-no-reader-orderflow-story-endorsement', '287-b001',
  '对读者大单成交、调仓试盘的猜测，作者提醒一只股票未必只有一拨参与者，拒绝细说具体行为。',
  '主力资金|成交量|市场心理|操作熟练程度', 3, '未认证读者对600343单笔大单的庄家动机或作者实际排挤行为，不从涨跌猜测唯一参与者。')


keep('280-b001', 'upper-l037-c-stage-all-buy-sell-ultimately-first-points-different-levels',
     '38以所有点归某级一类为操作起点，保留37概括而不重复建立所有点都本级一类的错误规则。')
keep('280-b002', 'upper-l036-c-stage-associativity-mixed-levels-and-multiple-not-vague upper-l035-c-stage-type-connection-associative-not-commutative',
     '38固定同级规则谈唯一，不抹换规则/级别合法多义，且仍不允许交换时序。')
keep('280-b003', 'upper-l033-c-stage-consolidation-plus-consolidation-can-increase-level',
     '本级同级别允许盘整+盘整是特殊分解记账，非取消33其他语境相加可升级，不能把六段与九段混成K线计数。')
keep('280-b004 280-b005 281-b000', 'upper-l035-c-stage-single-five-type-cannot-contain-thirty-center upper-l036-c-stage-simplify-unfinished-second-center-not-cancel-expansion-definition',
     '只改变选定层的分解规则，低层仍用延伸且已完/未完分开，高层不考虑非市场不存在；原类型级别定义不删除。')
keep('283-b005', 'upper-l037-c-stage-near-market-means-current-clarity-not-physical-distance',
     '本段与37课277-b007为同一3/20 15:44答复的汇编重复，完整核对同文同署名时间，只保留原命题跨源台账线索，不新建重复命题或改旧证据。')
keep('285-b004 285-b011', 'upper-l036-c-stage-third-buy-sublevel-leave-retest-not-reenter-general-answer upper-l037-c-stage-all-buy-sell-ultimately-first-points-different-levels',
     '38细化首有效回抽和次次级两次完成一次次级，不能将36都算扩大成完成三买后任意再回抽又是同中心新三买。')
keep('285-b008', 'upper-l037-c-stage-c-must-new-trend-high-or-low upper-l037-c-stage-c-no-new-extreme-even-third-point-use-consolidation',
     '38为ABC盘整C与读者引文问题，37为整体趋势末c；新高要求按对象分层，未自动以时间较晚覆盖早条件。')
keep('285-b001', 'upper-l036-c-stage-abc-compare-ac-consolidation-divergence-and-c-internal upper-l034-c-stage-a-plus-b-plus-b-area-sum-not-maximum-bar',
     'A/C比较和C内精确是两层；MACD看5分图一般更清楚不是级别改名，未回答0轴或给唯一力度算法。')
keep('286-b002', 'upper-l035-c-stage-large-buy-sell-is-sublevel-or-below-not-necessarily-direct upper-l037-c-stage-trend-divergence-ends-trend-consolidation-may-same-type',
     '38按内部背驰/盘背和容量分步退出，不由跌多少统一决定，也不把任意小背驰当大级结束。')
note('282-b005', 'historical-forecast-self-report-and-next-date-tail',
     '3/21作者谈未来震荡、20年及到30000点的自述，末尾附3/22 15:29:02时间头，已读。',
     '历史到30000点与37上升3万点不是同一数值语义，未静合或据强语气证明未来；尾头仅管后段，不改本段3/21时间。')
note('283-b001', 'source_separator', '原文星号终止3/22解盘。', '只保留来源边界，不独立支持技术规则。')
issue('same-level-unique-rule-not-global-unique-or-formal-proof', '280-b002 280-b004 280-b005 281-b000 281-b001',
      '规则内唯一与可选择分解规则/级别不冲突；作者称易证但没有给全部起终点约定/算法与形式证明，本级/所有低级/高层作用域不同。',
      '后39继续检查同级分解操作，不把所有合法多义合并一个全局唯一切法或以测试声明数学证明。', True)
issue('own-consolidation-plus-consolidation-and-six-sublevel-types', '280-b003 280-b004 280-b005 281-b000',
      '本级不定义延伸扩展、六小类型当两本级盘整，而低层允许延伸禁盘整+盘整；六/九计数口径及三段完成重叠不能混。',
      '保持规则局部，参照33/35/36，未把所有真实中枢延伸删除或认为六根K即两盘整。', True)
issue('mechanical-branches-completion-equality-execution-and-profit', '281-b002 281-b003 282-b000',
      '先下背驰出发，二下破低与否、三上低于/高于及盘背分支完整，但等高在子支未单列；最终不创新高含不同措辞。线性利润超一切单边无样本。',
      '不补容差/固定K数或实时成交保证，原先卖后买不等可裸卖空；资金/时间/幅度/成本误差条件与原强收益断言分开。', True)
issue('third-first-effective-retest-subsub-completion', '284-b006 285-b004 285-b011',
      '跌回中枢是震荡非所说回抽，首有效不回才三买，已三买后再不回非再三买；两个次次级回抽完成一个次级，仍未形式化触边相等规则。',
      '补36读者辩论与20定义的对象，后续数据例可比，不把第一次离开/尝试、有效回抽和内部两次混同。', True)
issue('consolidation-capital-c-versus-trend-c-and-unanswered-zero-axis', '284-b000 284-b001 284-b008 284-b009 285-b000 285-b001 285-b008',
      '盘整ABC之C可不新高，不能撤37趋势c条件；MACD5分图比较A/C并参C内，但读者刚上0轴是否盘背未获单独答。',
      '原MACD只要是辅助创新高措辞保留，不造所有MACD仅适用某一情境的全局定理，价弱非单独充分完成判据。', True)
issue('exit-internal-divergence-capacity-and-signal-vs-fall-threshold', '285-b014 286-b002 286-b005',
      '退出看内部背驰/盘背，进入区间套陆续出且容量有别；未给小拐头跌多少阈值，沪深背离非MACD背驰同词同物。',
      '不把所有小信号等同大结束或理想极值成交，首卖/二卖纪律按级别，个股历史观点不转当前推荐。', True)
issue('historical-profit-self-report-and-futures-motives', '281-b002 281-b003 282-b001 282-b002 282-b003 282-b004 282-b005 283-b000 283-b008 286-b005 287-b001',
      '永远不败、8股翻倍、内幕熟人、锌牛市和主力动机是历史作者自述/预测，未核实际账户/机构；重复3/20答不重抽。',
      '未验证利润线性或当前产品制度，不认可读者大单试盘因果，不按政治贬称建立真实实体/风险保证。')
issue('commentary-dates-and-figure-provenance', '282-b005 282-b006 283-b000 283-b001 283-b005',
      '3/22尾头只管后三段，3/20重复答保留自身时间；4图全后加，281有2009署名示意，284光标3/21但右端更晚。',
      '原文/字符映射/坐标不改，后图和示意不补作者定义、证明预测或抹当时可能条件。')
relations = {
 'upper-l038-c-stage-same-level-decomposition-fixed-level-definition': [('同级别分解','同级别','defines')],
 'upper-l038-c-stage-good-rule-unique-and-same-level-uniqueness-author-claim': [('同级别分解','结合律','qualifies')],
 'upper-l038-c-stage-one-forming-same-level-center-then-next': [('同级别分解','完成','qualifies')],
 'upper-l038-c-stage-consolidation-plus-consolidation-allowed-only-mode-scope': [('同级别分解','盘整','qualifies')],
 'upper-l038-c-stage-sublevels-need-not-use-same-mode-can-extend': [('同级别分解','中枢延伸','qualifies')],
 'upper-l038-c-stage-different-position-portions-at-different-levels': [('机械化操作','操作级别','qualifies')],
 'upper-l038-c-stage-small-time-rich-full-position-large-partial-applications': [('交易容量','仓位','qualifies')],
 'upper-l038-c-stage-first-effective-retest-only-later-no-return-not-third': [('第三类买卖点','中枢震荡','qualifies')],
 'upper-l038-c-stage-third-point-and-center-extension-end-same-object': [('第三类买卖点','中枢延伸','qualifies')],
 'upper-l038-c-stage-two-subsub-retests-complete-one-sublevel-retest': [('第三类买点','次级别','qualifies')],
 'upper-l038-c-stage-consolidation-c-need-not-highest-no-new-high-weak-macd-aux': [('盘整背驰','高低点','qualifies')],
 'upper-l038-c-stage-abc-macd-five-chart-ac-compare-c-internal-precision': [('MACD','指标对比','qualifies')],
 'upper-l038-c-stage-nested-divergence-exit-staged-by-capital': [('区间套','交易容量','qualifies')],
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
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], '读者第三买点重复回抽、ABC/图周期、MACD刚上轴和两次回抽、个股主力猜测只作问答上下文；作者未逐项认可未答部分，不将引用的旧文当本次作者全新答复。'
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
        'note': '同级别分解本级允许盘整+盘整而低级可用延伸，唯一性为作者主张；机械操作留全部条件与相等未详分支，三买首有效回抽/次次级两次分层，盘整C非趋势c新高要求。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True, reviewer=REVIEWER, visual_review_note=f['note'],
             figure_source_review='本课4图全部查看且全晚于文字，281为2009读者示意，283至3/23、284日线所选3/21后仍有K、286至3/26；示意不补作者未详规则，后图不倒证预测。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 75 and Counter(x['lesson_number'] for x in ledger) == {38: 75}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [38], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(280, 288)), 'figure_objects_viewed': 4, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '38课75段8页4图及前后课边界同模型四轮；3跨日日期修正，同级别规则/机械流程、三买首有效回抽和盘整C范围分层，重复3/20答保留不重抽，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


