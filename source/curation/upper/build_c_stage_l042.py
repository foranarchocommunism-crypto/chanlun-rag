"""Materialize the main agent's four-pass reading of lesson42.

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
BASE = 'c_stage_l042'
REVIEWER = 'Codex 主代理 / 阶段C上册42课同模型四轮复核'
SOURCE_SHA = '93f7787742d224805f4501fc9420c27e85b276dcecff34fadc8908930d19efad'
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
metadata = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
assert metadata['schema_version'] == '1.1.0'
assert hashlib.sha256((KB / 'sources/volume_1.pdf').read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id = 'lesson-042' ORDER BY pdf_page,block_index,id")}
assert len(passages) == 64
assert hashlib.sha256(json.dumps(sorted(passages.values(), key=lambda p: p['id']), ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == SOURCE_SHA
old = {r['id']: dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
concepts = {r['label']: dict(r) for r in db.execute('SELECT * FROM concepts')}
canonical = {label: r['label'] for r in concepts.values() for label in [r['label']] + json.loads(r['aliases'])}
figures = [dict(r) for r in db.execute('SELECT * FROM figures WHERE document_id=? AND pdf_page BETWEEN 306 AND 311 ORDER BY pdf_page,id', (DOC,))]
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
    pending.append({'id': 'upper-l042-c-stage-pending-' + slug, 'status': 'pending',
                    'passage_ids': [pid(s) for s in shorts.split()], 'description': description,
                    'suggested_action': action, 'blocks_full_semantic_extraction_completion': blocker,
                    'reviewer': REVIEWER})




















c(42,'knowing-rule-not-enough-if-impulse-controls-order','306-b004',
  '作者指出，明知不能买却控制不住下单时，技术理论也无法代替行为约束；网上交易方便会让关键一刻的冲动直接变为交易。',
  '市场心理|操作熟练程度|操作策略',1,'1秒是当时便捷性的举例，不是所有订单执行时延标准，成瘾等词为作者比喻而非临床诊断。')
c(42,'psychological-training-distance-or-environment-author-options','306-b004',
  '对关键时刻难以控制冲动者，作者列基础心理训练、远离股市、换环境几种办法，并说没有股市也可以生活。',
  '市场心理|操作策略|操作熟练程度',2,'作者应对观点，不作心理疾病治疗或换市场必赚钱的证据；上段香港个案没有独立核实，三种并非临床疗效方案。')
c(42,'trading-not-necessarily-trains-temperament-leave-for-severe-problems','306-b005',
  '作者说操作并不一定能磨练心态；特别严重而不适合继续留市者，应先远离一段时间、调节后才可能改善。',
  '市场心理|操作熟练程度|操作策略',1,'保留并不一定、才可能及当下范围，不把带病交易当训练或把人的性格永久定罪；原疾病比喻不作医学事实。')
c(42,'market-suitability-current-not-permanent-first-adjust','306-b005 307-b008',
  '作者明确适不适合市场只具当下意义，列出的十种表现并不意味着永远离开，关键是先调节过来。',
  '当下|市场心理|操作熟练程度',1,'十种是作者操作行为分类，不是穷尽所有参与者的临床人格诊断，也不能对现实用户据一表现永久贴标签。')

types=[
 ('ear-controls-brain','306-b007','耳朵控制大脑型','每次买卖几乎都仅听消息便直接动手、不经过自己的思考','消息来源真假未核，听取信息不等不思考交易'),
 ('shopping-many-stocks-small-funds','306-b008','疯狂购物型','仅几万元却持十几甚至几十只，什么股都想有，以都有来安慰自己','金额/只数是行为举例而非普遍仓位阈值，不推出任何分散投资都错'),
 ('uncontrolled-known-wrong','307-b000','不受控制型','操作时明知不对却每逢关键抉择控制不住自己','评的是反复行为，不用一次失误作永久判断'),
 ('apologizes-never-corrects','307-b001','永远认错型','口头认错却不改，同一个毛病反复犯','永远/致命为作者强调，不是已经计算的损失概率'),
 ('lament-enjoy-tragic-mood','307-b002','祥林嫂型','总在哀叹甚至沉浸悲剧情调，作者劝其离开折磨环境','文学称谓与离开建议不是精神疾病诊断'),
 ('gambler-market-casino','307-b003','赌徒型','只把市场当赌场，作者认为不必参与市场','赌博/旅游设施段只是历史旁述，不核未名集团/企业，也不将劝诫理解为鼓励去赌场'),
 ('commentator-boasts-not-trades','307-b004','股评型','实际亏损仍只吹嘘，把市场当谈资而不认真操作','针对所述行为，不断言全部市场评论者都亏损或欺骗'),
 ('too-absorbed-every-tick-emotion','307-b005','入戏太深型','每个细微波动无论涨跌盘整都使情绪失控，开盘期间持续煎熬','4小时为当时举例，非全部交易市场统一交易时间'),
 ('rigid-not-adapt','307-b006','偏执狂型','认死理、无法随万变市场调节，作者认为在市场无出路','原词是作者贬称，非临床术语使用或对具体人的诊断，亦保留其理论等事或有益的对照'),
 ('zhao-kuo-theory-not-operation','307-b007','赵括型','把实际市场操作等同纯理论研究，忽视操作差异','赵括/战场是比喻，不是历史人物归因证据或说所有理论研究无用'),
]
for slug,short,name,description,check in types:
 c(42,'unsuitable-behavior-'+slug,short+' 307-b008',
   f'作者把{name}列为当下特别不适合市场的表现，指{description}；仍需结合先调节、非永远离开的限定。',
   '市场心理|操作熟练程度|操作策略',2,check+'；十类共同范围由结尾限定段联合支持。',
   ['所述反复操作行为及作者分类语境','当下需先调节，不是永远不能参与市场'])
c(42,'self-awareness-daily-ten-minute-operations-and-psychology-review','307-b009',
  '作者要求先认清自己和弱点，并清楚意识每个市场行为；每天收盘后用十分钟复盘当天操作及看盘心理过程。',
  '市场心理|操作熟练程度|操作策略',1,'十分钟是原文训练建议，未证明固定时长是盈利充分条件；性格决定命运是作者强调，不作确定因果定律。')
c(42,'apr4-shenzhen-pressure-near-9200-second-line-author-script-view','307-b010',
  '4月4日作者称深圳近9200的前两高点连线有技术压力，并把深强沪弱解释为二线认同及上海暂缺目标，称走势在演其剧本。',
  '高点连线|二线股|指数走势背离|宏观市场判断|走势预测',4,'只存历史技术判读/事后自述及因果解释，不认证真实机构、预测能力或必破压力；配图有之后行情。',figs=[(308,1),(308,2)])
c(42,'oscillation-lowers-cost-only-good-rhythm-author-view','308-b000',
  '作者称对节奏好的人，震荡有利于降低成本，并盼多震荡；不是无条件地把震荡当坏事。',
  '市场震荡|成本|操作策略',2,'原为条件性强经验判断，未核成交、费用及收益，不保证任何震荡策略降本。',ambiguity='author_rhythm_cost_reduction_not_verified')
c(42,'weak-tech-five-day-midterm-ten-day-line-historical-fallback','308-b000',
  '作者给技术不足者看5日线、中线看10日线的简法，举去年8月一波基本不破10日线；若真破称有较大级别调整，5日不破则劝不担心。',
  '均线系统|操作熟练程度|操作级别|市场风险',1,'当时辅助简法与强安心说法，不把10日突破作为任何大级调整充要定义，也不认证5日线之上无风险或去年走势统计。',ambiguity='historical_moving_average_fallback_and_reassurance_scope')
c(42,'apr5-second-line-ten-yuan-and-pressure-break-toward-ten-thousand','308-b002 309-b000 309-b001',
  '4月5日作者称仍是10元上下二线股行情；深圳临近压力线显沉，若能突破站稳则可攻击1万点，并预期上海以后也会到此位置。',
  '二线股|高点连线|确认|宏观市场判断|走势预测',4,'若能突破站稳为联合条件，万点是当时预测非结果认证；10元不是通用筛选门槛，作者贬称对手不核身份，后图不验证原预测可得。',
  ['2007年4月5日具体解盘','深圳突破并站稳所指压力线才谈攻击万点'],figs=[(308,1),(308,2)])
c(42,'apr5-stability-policy-uncertainty-sector-rotation-multilevel-oscillation','309-b002 309-b003',
  '作者认为当时政策和各方平衡尚不明，不宜太乐观，应稳健轮动、通过不同级别震荡消除压力。',
  '政策风险|板块轮动|市场震荡|操作策略',3,'当时策略及机构心理推断，不认证其正规军/民兵等比喻的真实组织身份或唯一市场因果。')
c(42,'first-daily-MACD-zero-return-rebuy-author-strong-case','309-b010',
  '对白玉兰卖出后不敢再入的答复，作者称第一次大洗盘令日线MACD首次回拉0轴后一定要买回，即使背驰仍有创新高机会，也可能不背驰；同时反对现在追涨。',
  'MACD|确认|买点|背驰|追高',1,'一定买回是作者特定个案的强指令，不推广为所有首次日线归零的充分买点；创新高仅机会非必然，未明安全/成交条件；原14只翻倍说法未实证，原7779元不擅拆成证券身份。',ambiguity='author_first_zero_return_rebuy_strong_claim_context_incomplete')
c(42,'shenzhen-two-points-compare-one-minute-MACD-no-text-formula','309-b014',
  '对读者所说深圳11:04和13:51两点回调幅度不同，作者让看1分钟图MACD、比较两点大的区别。',
  'MACD|指标对比|操作级别|动力学',1,'作者没有在文字指定零轴/面积哪一项或完整幅度公式，读者两处都背驰的说法未逐一认证；图中差异观察不能伪装作者明说指标定律。',figs=[(310,1)],ambiguity='author_invites_comparison_but_indicator_difference_not_explicit')
c(42,'600649-weekly-look-left-historical-dense-zone-case','310-b002',
  '对600649走慢并以持股磨耐心的提问，作者让打开周线、看左边，指出当时位置在历史密集区。',
  '历史密集区|周期K线图|持股|操作级别',2,'个股周线历史判读，不认可读者持股必是训练；图后至4/13，不能当4/4已知的后涨或证实多数持仓成本。',figs=[(310,2)])
c(42,'historical-dense-zone-trapped-holders-turnover-author-explanation','311-b001',
  '作者解释历史密集区是历史上大多数人被套的地方，并认为要让缺信心耐心者退出、换手充分，才可能大涨。',
  '历史密集区|成交量|市场心理|持股',1,'这是作者筹码/供给解释，未以真实持有人账本证明大多数、换手比例或必涨；必要式反问也不是成交量充分预测定律。',figs=[(310,2)],ambiguity='author_historical_holders_and_turnover_not_empirically_verified')
c(42,'weak-tech-thirty-minute-five-day-no-large-energy-formula','311-b004',
  '问怎样识别大级别能量是否耗尽，作者没有给耗尽公式，而让技术不足者按30分钟进出、5日线不破别乱折腾，先提高能力。',
  '操作熟练程度|操作级别|均线系统|能量结构',1,'读者小级别卖后续涨为问题背景，作者差价遍地说法不认证实盘机会；未把30分钟或5日线当能量耗尽定义。')
c(42,'consolidation-divergence-must-break-literal-target-unspecified','311-b010',
  '在读者质疑盘背后是否一定跌破的答复中，作者原话说盘整背驰一定跌破。',
  '盘整背驰|有效跌破|同级别分解',1,'本句未重述级别、方向或跌破哪条边界；按39/40同级分解保护位线索待查，不擅扩为任意盘背必破任意中枢低点，也不以后果倒认背驰。',ambiguity='break_target_direction_level_not_repeated_in_short_reply')
c(42,'break-not-necessarily-consolidation-divergence-a-prime-plus-B','311-b010',
  '同答作者说跌破不一定都是盘整背驰，a`+B这种形式也可以。',
  '盘整背驰|有效跌破|同级别分解|走势分解',1,'按原式保留a`+B，不用其简短记号补全每段级别、完成条件及破位对象；不能由跌破倒推之前必盘背。',ambiguity='a_prime_plus_B_not_fully_defined_in_reply')
c(42,'tsinghua-negative-news-fundamental-reassurance-author-rhetoric','311-b007',
  '问紫光股份不利消息，作者以清华不是清华才是最大不利作答，称其余所谓不利算不了什么。',
  '基本面|市场风险|题材股',4,'历史身份/背景强安心修辞，未核公司关系、公告或实质风险，未给下跌不可能或消息全免疫的事实。',ambiguity='author_historical_identity_reassurance_not_risk_guarantee')
c(42,'basic-chart-system-enough-if-understand-market-not-paid-tool-proof','311-b013',
  '问只靠技术及付费level2值不值，作者质疑靠卖系统获利者，并说若明白市场走势，有最基本走势图的系统就足够。',
  '技术分析|走势|操作熟练程度|操作策略',1,'若明白走势是条件，未对任何具体level2产品做功能评测；作者反问不证明所有付费系统无用、卖家不能盈利，亦未明确认可仅技术即下单如神。')

note('306-b003','unverified-anecdote-context','作者转述06年内地亏损转香港、看内地股票买香港对应股票并T+0不隔夜的个案已读。','匿名人物身份、收益和跨市场机制未核，不推出香港天然可盈利或授权当前套利策略。')
note('306-b006','source_header','十类行为清单导语已读。','是作者训练分类引子，未增加心理诊断效力。')
note('307-b003','mixed-unverified-gambling-tourism-context','赌徒类型后澳门/珠海岛桥、美国集团旅游收购描述为历史旁述。','原文保留，不猜未名实体或给赌博建议，旅游因果无外部认证。')
note('308-b000','strong-historical-market-reassurance-context','段尾板块都会轮到等说法为当时强安心判断。','未核全部股票样本或保证轮动，不以5日不破得无风险。')
note('309-b007','historical-policy-opinion-context','答创业板推出速度取决利益平衡，作者称越快越好。','不是年内推出的承诺，不将读者媒体消息或作者态度作现行法规。')

issue('behavior-ten-types-current-not-permanent-or-clinical','306-b004 306-b005 306-b007 306-b008 307-b000 307-b001 307-b002 307-b003 307-b004 307-b005 307-b006 307-b007 307-b008 307-b009',
      '十类为作者行为劝诫，须保留当下、先调节非永久；成瘾/病/偏执等贬称非临床诊断，十分钟复盘无疗效/盈利验证。','不按词给真实用户贴诊断或永久排除，区分心理训练观点和已实证因果。')
issue('historical-forecast-moving-lines-and-anonymous-market-parties','307-b010 308-b000 308-b002 309-b000 309-b001 309-b002 309-b003',
      '9200压力、10元二线/万点预测、5/10日简法及都会轮到都限当时；3图含后行情，未认证对手/政策因果。','保留突破且站稳条件，不以后K证预测，不把均线当无风险或级别调整充要定义。',True)
issue('daily-first-zero-return-must-rebuy-and-fourteen-stock-profit','309-b009 309-b010',
      '日线MACD首次归零一定买回是强个案指令，背驰仍有新高仅机会；14只翻倍说法未实证，777与9元原连字不擅认证证券。','后课比对首次回轴/趋势条件，保留时点和不追高，未补统一买入算法，不挂指数图作该股证据。',True)
issue('two-points-MACD-and-large-energy-not-fully-answered','309-b012 309-b013 309-b014 311-b003 311-b004',
      '两点差异只让看1分MACD，原答未指明具体项或幅度公式；大级能量耗尽问仅获30分/5日/能力建议。','图像观察另记非作者原话，不据两图归纳通用幅度/能量耗尽公式，接续43背驰补习。',True)
issue('historical-dense-zone-holder-data-and-turnover','310-b001 310-b002 310-b004 311-b001',
      '600649周线历史密集区按作者解释为多数被套、换手不足不易大涨，但无持有人数据/量阈值，后图4/13。','概念可检索但多数被套为作者解释，不拿换手量充分证明涨幅或必涨。')
issue('consolidation-divergence-must-break-direction-target-and-a-prime-B','311-b009 311-b010',
      '作者盘背一定跌破、跌破不一定盘背及a`+B未在此重述方向、破哪级何位；读者拿三买质疑尚须跨课定范围。','联合39/40及43细查Ai保护位/形成更高中枢语境，不扩为所有盘背必破任意中枢下沿，保留原式不补等价算法。',True)
issue('source-dates-figures-and-unverified-reassurance-entities','308-b001 309-b007 311-b007 311-b013',
      '4/5解盘6段纠正、18答疑时间空格规范，四图3后加1原发未核；创业板/旅游/清华背景、付费系统评价均历史意见。','保留原文/映射/几何与身份，匿名不猜、强安心不证无风险，付费level2未做实际功能/收益评测。')
relations={
 'upper-l042-c-stage-market-suitability-current-not-permanent-first-adjust':[('市场心理','当下','qualifies')],
 'upper-l042-c-stage-self-awareness-daily-ten-minute-operations-and-psychology-review':[('市场心理','操作熟练程度','qualifies')],
 'upper-l042-c-stage-first-daily-MACD-zero-return-rebuy-author-strong-case':[('MACD','买点','qualifies')],
 'upper-l042-c-stage-shenzhen-two-points-compare-one-minute-MACD-no-text-formula':[('指标对比','动力学','qualifies')],
 'upper-l042-c-stage-600649-weekly-look-left-historical-dense-zone-case':[('历史密集区','周期K线图','qualifies')],
 'upper-l042-c-stage-historical-dense-zone-trapped-holders-turnover-author-explanation':[('历史密集区','成交量','qualifies'),('历史密集区','市场心理','qualifies')],
 'upper-l042-c-stage-weak-tech-thirty-minute-five-day-no-large-energy-formula':[('能量结构','操作熟练程度','qualifies')],
 'upper-l042-c-stage-consolidation-divergence-must-break-literal-target-unspecified':[('盘整背驰','有效跌破','qualifies')],
 'upper-l042-c-stage-break-not-necessarily-consolidation-divergence-a-prime-plus-B':[('同级别分解','走势分解','qualifies')],
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
        result, reading, atomic, inverse = 'reader_context', '读者署名、引用、提问和自述已读，限定相邻作者回复对象。', [], '读者两点都背驰、7779元、600649持股练耐心、大级能量耗尽及盘背破位/三买、level2下单如神问法保留身份，作者短答不认证全部读者前提。'
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
        'note': '十类行为当下先调节非永久或临床标签，10分复盘为作者训练建议；日线首次归零强指令有个案条件，MACD差异及大级耗尽未给公式；盘背必破原字保留目标范围待核。'},
        '4_reverse_check': inverse}})
for f in figures:
    f.update(visual_review_complete=True,reviewer=REVIEWER,visual_review_note=f['note'],
             figure_source_review='本课4幅整图逐一查看：308两图右端至4/9至10，310周图头4/13均为后加；310一分同日图原发未核，图像观察与作者短答明说分开。',
             linked_claim_ids=[r['id'] for r in rows if any(f['id'] in e['figure_ids'] for e in r['evidence'])])
assert len(ledger) == 64 and Counter(x['lesson_number'] for x in ledger) == {42: 64}
for suffix, data in [('reviewed.jsonl', rows), ('coverage.jsonl', ledger), ('pending.jsonl', pending), ('figures.jsonl', figures)]:
    (OUT / f'{BASE}.{suffix}').write_text('\n'.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) for x in data) + '\n', encoding='utf-8')
summary = {'stage': 'C/E', 'schema_version': metadata['schema_version'], 'graph_version': metadata['graph_version'],
  'lessons': [42], 'document_id': DOC, 'reviewer': REVIEWER, 'passages_read': len(ledger), 'claims': len(rows),
  'evidence': sum(len(r['evidence']) for r in rows), 'importance_counts': dict(Counter(r['importance_level'] for r in rows)),
  'new_concepts': sorted({x for r in rows for x in r['concepts']} - set(concepts)), 'whole_lesson_semantic_read_complete': True,
  'technical_extraction_complete': False, 'four_round_review': True, 'independent_review_claimed': False,
  'visual_pdf_pages': list(range(306, 312)), 'figure_objects_viewed': 4, 'figure_origin_counts': dict(Counter(f['origin_status'] for f in figures)),
  'pending': [x['id'] for x in pending], 'source_passages_snapshot_sha256': SOURCE_SHA, 'retained_source_links_in_ledger_only': True,
  'database_mode': 'ro', 'formal_import': False,
  'acceptance': '42课64段6页4图及前后边界同模型四轮；6跨日与18空格规范、4图3后加1未核；十类行为与当下调节、历史密集区及归零/破位强答范围分层，待预检。'}
(OUT / f'{BASE}.summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
db.close(); sys.stdout.reconfigure(encoding='utf-8'); print(json.dumps(summary, ensure_ascii=False))


