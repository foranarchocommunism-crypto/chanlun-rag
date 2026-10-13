"""Materialize the root agent's source review of lessons 65/66; SQLite stays read-only."""
import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
KB = HERE.parents[2] / 'shared-knowledge/v0.1.0'
PREFIX = 'volume_2-5332cd1b6038-'
BATCH = 'batch_005_l065_l066_full_review'
REVIEWER = '主代理 / 阶段C第65、66课四轮原文复核'


def dump(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def build():
    db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    passages = {r['id']: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id IN ('lesson-065','lesson-066') ORDER BY pdf_page,block_index,id")}
    concepts_before = {r['label'] for r in db.execute('SELECT label FROM concepts')}
    version = json.loads(db.execute("SELECT value FROM metadata WHERE key='graph_version'").fetchone()[0])
    common = '第一轮顺序阅读第65课112段和第66课59段，包括全部所附作者文章及问答；第二轮按定义、联合前提、方法、经验和历史情境拆分；第三轮对照已有62/64/67/72课命题与概念，保留同词异义及不同层次；第四轮回到引文核对方向、量词、不等式、时点和否定。主代理同一模型不同检查视角，不称独立或人工复核。'
    records = [json.loads(s) for s in (HERE / 'batch_003_l065_l067.jsonl').read_text(encoding='utf-8-sig').splitlines() if s.strip() and json.loads(s)['id'].startswith(('lower-l065-', 'lower-l066-'))]
    by_id = {r['id']: r for r in records}
    for record in records:
        record['reviewer'] = REVIEWER
        record['review_note'] = common + ' 本记录重新复核未发布的旧批003条目；公式实际查看PDF32/34，回复身份查看PDF47/48，技术补充查看PDF37/39。'
        record['importance_reason'] = record['importance_reason'].replace('该分级为整理判断。', '；分级为整理判断。')
        record['concepts'] = ['当下' if c == '当下性' else c for c in record['concepts']]
        for relation in record.get('relations', []):
            for field in ('source', 'target'):
                if relation[field] == '当下性':
                    relation[field] = '当下'
    by_id['lower-l065-inclusion-sequential']['conditions'] = ['按时间顺序处理相邻K线包含关系']
    by_id['lower-l065-no-fractal-do-not-force']['conditions'] = ['已确定所观察的周期K线图']
    by_id['lower-l065-chart-not-operation-level']['conditions'] = ['区分观察图周期与操作级别']
    formed = by_id['lower-l065-formed-bars-unique-fractals']
    formed['evidence'].append({'passage_id': PREFIX + 'p0034-b006', 'quote': passages[PREFIX + 'p0034-b006']['text']})
    theorem = by_id['lower-l065-segment-decomposition-theorem']
    theorem['conditions'] = ['第65课线段被笔破坏的定义与连续前三笔重叠的前提']
    theorem['review_note'] += ' 保留第65课本段原述；67课精确化另见已发布命题，不把后课条件写成本段原文明说。'
    nesting = by_id['lower-l065-interval-nesting-below-segment']
    nesting['evidence'] = [{'passage_id': PREFIX + 'p0037-b004', 'quote': passages[PREFIX + 'p0037-b004']['text']}]
    nesting['concepts'] += ['交易通道', '交易成本']
    nesting['review_note'] += ' 成本限制的完整依据在原段结尾，补全引文，不以摘要推断成本约束。'
    for slug in ['market-force-nonuniform', 'dominant-force-stock', 'main-capital-factions', 'technical-not-main-capital-strategy', 'main-funds-produce-points', 'main-funds-economic-trend', 'capital-food-chain']:
        record = by_id['lower-l066-' + slug]
        record['conditions'].append('第66课作者关于资金运作的描述，非本项目实证结论')
        record['review_note'] += ' 宏观资金说法归于作者，不补造资金身份、收益或当前市场事实。'
    by_id['lower-l066-dominant-force-stock']['text'] = '作者认为，若只有一个巨大分力而其他分力相对可忽略，合力与该分力基本无异；高度控盘个股往往如此，作者称该系统稳定性会产生突变。'
    by_id['lower-l066-stroke-needs-standard-opposite-fractal']['evidence'] = [{'passage_id': PREFIX + 'p0048-b005', 'quote': passages[PREFIX + 'p0048-b005']['text']}]
    by_id['lower-l066-stroke-needs-standard-opposite-fractal']['conditions'] = ['回应紧邻p0048-b004关于顶分型首根K线范围的提问', '仅为新笔所需底分型的条件说明，非充分算法']
    nine = by_id['lower-l066-nine-types-combine-before-center']
    nine['text'] = '在关于九个1分钟走势类型重叠所得5分钟中枢点位的提问中，作者答“不一定”，并要求按3+3+3组合后确定5分钟中枢。'
    nine['conditions'] = ['紧邻p0048-b010读者提问的范围', '按3+3+3组合后再确定，不能只凭九个数量认定具体点位']
    nine['evidence'] = [{'passage_id': PREFIX + 'p0048-b011', 'quote': passages[PREFIX + 'p0048-b011']['text']}]
    nine['review_note'] += ' 未把读者九个重叠的前提提升为作者普遍充分定理；回复保留不一定及组合要求。'
    for record in records:
        if any(passages[e['passage_id']]['role'] == 'author_commentary' for e in record['evidence']):
            record['review_note'] += ' 语境：第65课后附2007年7月作者技术解释，篇名及日期见证据；适用条件：保持本条的层次、递归入口或操作对象限制。'

    def add(lesson, slug, text, concepts, sources, conditions, level, reason, note, exceptions=None, relations=None):
        evidence = [{'passage_id': PREFIX + suffix, 'quote': passages[PREFIX + suffix]['text']} for suffix in sources]
        record = {'id': f'lower-l{lesson:03d}-' + slug, 'text': text, 'kind': 'explicit', 'conditions': conditions, 'exceptions': exceptions or [], 'concepts': concepts, 'ambiguity_status': 'none', 'review_note': common + ' ' + note, 'reviewer': REVIEWER, 'evidence': evidence, 'relations': relations or [], 'importance_level': level, 'importance_reason': reason + '；分级为整理判断。'}
        if any(passages[e['passage_id']]['role'] == 'author_commentary' for e in evidence):
            record['review_note'] += ' 语境：本课附文作者技术解释或历史市场判断，具体日期和篇名见证据；适用条件：保留本条列出的对象、时间与能力，不推广成无条件规律。'
        records.append(record)
        by_id[record['id']] = record

    add(65, 'geometry-from-definitions', '作者将几何化思维和从基本定义出发，作为实际辨认复杂图形的方法要求。', ['技术分析', '分型', '笔', '线段'], ['p0032-b007', 'p0034-b006'], ['按本文的几何定义辨认走势'], 2, '记录定义驱动的辨认方法', '方法立场属于作者；未把作者自述唯一性等同于本项目已经证明所有划分算法。')
    add(65, 'inclusion-associativity-and-order', '作者要求K线包含处理遵守结合律，并同时遵守先合并前两根、再与第三根比较的顺序原则。', ['包含处理', '结合律', '包含关系'], ['p0032-b010'], ['本课相邻K线包含处理'], 1, '将结合律与顺序约束共同保留', '不把结合律误写成可随意换序，非传递性另有独立命题。')
    add(65, 'formed-bars-analysis-chain', '作者说明，尚未走出的K线不能确定具体分型，因而不能据此划分相应笔、线段、最低级别中枢及高级别走势类型。', ['K线', '分型', '笔', '线段', '最小级别中枢', '走势类型', '当下'], ['p0033-b002'], ['当下尚未走出的K线与相应结构'], 1, '保留从基础数据到高层结构的完成前提', '不把当下性解释为对未来K线的预测能力。')
    add(65, 'stroke-direction-from-fractals', '按本课对同类连续分型的处理后，先顶后底构成向下一笔，先底后顶构成向上一笔。', ['笔', '顶分型', '底分型'], ['p0033-b004', 'p0033-b005'], ['已处理两个同类分型中没有其他顶底时的前一分型'], 1, '补全笔方向的明确判定', '保留上文第二种情况前提，不把任意两个顶底跨越连接。')
    add(65, 'destruction-index-notation', '本课线段被笔破坏的序列中，di表示第i个底、gi表示第i个顶；向上开始与向下开始分别采用d1g1d2g2…和g1d1g2d2…序列。', ['笔破坏', '线段', '顶', '底'], ['p0034-b002', 'p0034-b003'], ['仅本课线段被笔破坏公式的符号语境'], 3, '避免K线低高区间符号与分型序列混同', '不把同字母在不同公式中的对象自动合并。')
    add(65, 'practice-definitions-authority', '作者要求分型、笔、线段的辨认依据定义并反复对照图形练习，认为这类辨认有标准答案。', ['分型', '笔', '线段', '技术分析'], ['p0037-b003', 'p0034-b007', 'p0035-b000'], ['基础结构的学习和实际辨认'], 2, '记录学习与检查方法', '已查看12图，但该段没有列出每图答案，不自行借读者或后加图补齐。')
    add(65, 'large-funds-nesting-precision', '作者认为，大资金的精确定位一般不必到线段以下，1分钟甚至30分钟级别区间已可作为精确定位。', ['区间套', '操作级别', '主力资金'], ['p0037-b004'], ['一般的大资金操作定位', '作者对实用定位精度的说明'], 3, '保留定位精度与资金对象的关系', '一般及例如均保留，不规定所有资金必须同一周期。')
    add(65, 'two-drawings-change-meaning-with-unit', '作者说明，p39两幅题图在每划代表笔时从线段角度有本质区别；若每划改为线段，两图便没有该区别。', ['笔', '线段', '走势类型'], ['p0039-b008'], ['仅p39两幅指定题图', '比较每划代表笔与代表线段两种解释'], 3, '保存图示对象变化带来的边界', '实际查看p39两图。作者只确认有区别，未逐图确认插班生所给的完整划分答案。')
    add(65, 'strokes-segments-no-real-center-divergence', '作者区分笔与线段和中枢、走势类型；笔与线段内部只能用类中枢及类似背驰力度方法，不能称为严格的中枢或背驰。', ['笔', '线段', '走势中枢', '走势类型', '类中枢', '类背驰', '背驰'], ['p0039-b008'], ['严格术语意义下的笔与线段内部'], 1, '保存构造层和递归走势层的关键区分', '与已有64课类比边界对照，新增本课直接证据，不称为另一套不同定义。')
    add(65, 'recursion-existence-operation-distinction', '作者要求区分中枢递归定义的存在性意义，与分型、笔、线段方法的操作性意义。', ['递归定义', '走势中枢', '分型', '笔', '线段'], ['p0039-b009'], ['讨论递归理论存在与实际可操作构造'], 1, '明确同一递归体系的两种入口意义', '不推导两个系统冲突；本段作者明确说没有违反递归意义。')
    add(65, 'actual-trade-not-defined-stroke', '纯理论递归起点所说的每一分笔是实际成交分笔，区别于分型定义构成的笔；作者认为从每次成交递归没有实际操作意义。', ['递归定义', '笔', '成交分笔'], ['p0039-b009'], ['纯理论a0入口的说明'], 1, '避免分笔成交和几何笔同词误并', '保持理论可能构造与实用意义不同，未添加外部tick算法。')
    add(65, 'market-drawing-not-freehand', '作者区分随手绘制的讲解图和由合力形成的真实市场图，并要求观察当下走势。', ['市场合力', '当下', '技术分析'], ['p0039-b010', 'p0040-b000'], ['作者在题图讨论后的方法说明'], 2, '保留示意图与真实走势的认识边界', '不预测的用语保留在引文；关于可否预测的跨课关系留待68课等明确文字核对。')
    add(65, 'sentiment-force-feedback-case', '在2007-07-17解盘中，作者把汇聚人气、修复心理、改变合力与技术面联系起来。', ['市场心理', '市场合力', '技术分析'], ['p0035-b002'], ['2007-07-17技术与基本面不利多方时的市场解释'], 3, '收录技术、人气与合力的作者解释', '作者市场观点，不作为本项目验证的定量因果。')
    add(65, 'macd-golden-cross-needs-confirmation-case', '作者在2007-07-17指出日MACD已金叉，同时明确该金叉仍需确认。', ['MACD', '金叉', '确认'], ['p0036-b000'], ['2007-07-17日线MACD的情境观察'], 4, '保留信号出现与确认的区别', '未将单一金叉当无条件上涨充分条件。')
    add(65, 'moving-average-entanglement-news-case', '作者把当时3900点附近中短期均线缠绕视为具备变盘条件，并将利空兑现与人气和走势的正反馈联系起来。', ['均线', '市场心理', '市场合力'], ['p0036-b001'], ['2007-07-17市场与消息背景'], 4, '保存多条件技术解释', '变盘条件不改成充分上涨信号，方向判断保留当时多方语境。')
    add(65, 'policy-part-of-force-case', '作者认为政策也是市场合力的一部分，走势、人气和政策条件需要放在一起理解。', ['政策风险', '市场合力', '市场心理'], ['p0036-b002', 'p0036-b003', 'p0042-b002'], ['当时多方扭转不利局面的作者描述'], 3, '补充技术分析与政策心理的关联', '不转述为现行政策事实，不补充税制或法律判断。')
    add(65, 'rotation-builds-sentiment-case', '作者在2007-07-17将300成分股轮动称为带动人气的基本方法，并将充分调整、有题材潜力的中低价股作为当时动态建仓的另一类对象。', ['板块轮动', '市场心理', '动态建仓', '题材股'], ['p0036-b004'], ['2007-07-17两类对象的历史选择'], 3, '保留轮动与建仓的对象条件', '只记录当时策略；不将300成分或中低价永久化为选股要求。')
    add(65, 'constituents-downside-if-failure-case', '作者提醒，如果当次多方努力失败，成分股存在较大的补跌风险。', ['市场风险', '补跌'], ['p0036-b005'], ['2007-07-17多方努力失败这一假设'], 4, '保留原文明确的失败场景', '若条件不能删去，不把反面行情说成既成事实。')
    add(65, 'golden-cross-can-be-damaged-case', '作者在2007-07-18假设自己站在空方，提出先让一步、利用4000点及60天线心理屏障震荡，破坏日MACD金叉信号。', ['MACD', '金叉', '均线', '市场心理'], ['p0037-b007'], ['2007-07-18空方策略假设', '4000点与60天线的特定情境'], 4, '保存信号可能受后续走势破坏的解释', '不把假设策略当真实空方身份或已发生事实。')
    add(65, 'neckline-break-retest-case', '作者区分突破3919点颈线与突破有效：突破后多方需要反抽，空方可能制造假突破；其当时技术观察窗为三天回抽确认。', ['突破', '反抽', '假突破', '确认'], ['p0037-b008', 'p0038-b000', 'p0038-b001'], ['2007-07-18颈线突破的具体观察', '三天为本次原文窗口'], 3, '保存突破与确认及共同回落的语境', '不推广三天为所有市场统一确认阈值。')
    add(65, 'triangle-opposing-interpretations-case', '作者在当时多空策略比较中，分别把所处三角形解释为多方的第四段和空方的第三段，突破方向也不同。', ['三角形整理', '走势分解', '市场合力'], ['p0038-b002'], ['2007-07-18所讨论图形与多空策略'], 4, '保留同一行情下不同博弈预期', '不把三角形任一段等同于本课几何线段，也不冒称已核图示分段。')
    add(65, 'range-operation-before-half-line-case', '作者在当时4159点1/2线未有效站稳前，主张按震荡行情及自己的操作级别处理，以顶背驰出、底背驰买。', ['市场震荡', '操作级别', '背驰', '操作策略'], ['p0038-b004'], ['2007-07-18未有效站稳当时1/2线之前'], 3, '保留策略、市场状态和操作级别', '该日点位只是案例参数，不作为通用数值。')
    add(65, 'capital-hierarchy-not-chart-level', '作者在当时市场博弈解释中说主力、庄家资金也有层次，并把上层博弈结果与下层资金选择方向联系起来。', ['主力资金', '资金食物链', '市场合力'], ['p0038-b003'], ['2007-07-18资金博弈的叙述层次'], 4, '保留资金层次与走势层次的语境区别', '此处资金级别不映射成几分钟中枢或走势图级别。')
    add(65, 'triangle-minimum-scenario-case', '在2007-07-25对前日走势的解释中，作者以碰到前两高点连线达到三角形第四段为最低要求，并分别讨论直接突破与回调第五段。', ['三角形整理', '高点连线', '操作策略'], ['p0040-b012'], ['2007-07-25对前一日指数的情景解释'], 4, '保存作者对替代走势情景的比较', '明确第四/第五段为该三角形讨论，不据此发布一般线段数公式。')
    add(65, 'cash-shares-fit-alternative-paths-case', '作者称自己当时已调配资金和筹码，使配置适应直接突破与继续三角形两种走势。', ['仓位', '操作策略', '三角形整理'], ['p0040-b012', 'p0041-b000'], ['2007-07-25作者对自身历史配置的说明'], 3, '保存策略适应多个情景的操作解释', '无实际账户资料，不称为本项目核实的收益或配置绩效。')
    add(65, 'half-line-support-alternatives-case', '作者在当时4159点1/2线附近，分别讨论守住后创新高与失守后回补缺口、考验4000点或两低点连线的情景。', ['缺口', '高点连线', '操作策略'], ['p0041-b001'], ['2007-07-25具体指数位置'], 4, '保留支撑条件与相反场景', '不推广点位，不把条件性预测当一般定理。')
    add(65, 'longer-position-patience-case', '作者在其中长线股票示例中强调足够耐心，不因短期不动就否定中长线持有价值。', ['持股', '操作级别', '市场心理'], ['p0041-b002'], ['2007-07-25作者对所举中长线个股的说明'], 3, '保存持有期限与耐心的条件', '个股表现仅是作者历史举例，不作当前标的建议。')
    add(65, 'zero-cost-add-shares-author-strategy', '作者主张中长线运作先降低成本，成本到0后保持0成本增加筹码；同时明确提醒当时举例个股涨后不要追买。', ['成本', '仓位', '追高', '操作策略'], ['p0041-b003'], ['2007-07-25中长线运作方法及已持有示例'], 2, '保留成本管理方法与不得追买的限制', '永远不败属于作者修辞，原引文保留；命题不作确定无风险保证。')
    add(65, 'break-date-versus-confirmation-case', '作者认为，当时4335点突破早一天或晚一天并不重要，重要的是突破后适当回抽确认，否则面临假突破风险。', ['突破', '反抽', '确认', '假突破'], ['p0041-b007'], ['2007-07-25对后续两周的具体技术讨论'], 2, '保留突破确认方法及失效风险', '当时情景的作者技术解释，不把任意回抽视为确认成功。')
    add(65, 'false-break-rejection-two-paths-case', '作者在当时判断中，把确认假突破不成立与随后坚定行情联系起来；反之，仍保留考验4000点等可能。', ['假突破', '确认', '市场风险'], ['p0041-b007'], ['2007-07-25未来两周的具体行情情景'], 4, '保留条件预测的相反分支', '两条路径作为作者当时判断，不是本项目已证明的上涨充分条件。')
    add(65, 'rotation-spreads-beyond-constituents-case', '作者当时认为成分股先轮动，非成分股随后也会轮动，尤其有题材和基本面支持的对象可能具备中长线价值。', ['板块轮动', '题材股'], ['p0041-b009', 'p0042-b000'], ['2007-07-25市场策略与作者预期'], 4, '保留轮动的范围与对象', '原文肯定语气留在引文，外层归于作者当时预期，不冒充已检验的普遍次序。')
    add(65, 'weekly-four-scenarios-case', '作者在2007-07-27按由弱到强讨论四种突破后周线演化：本周上影调整、下周周K线调整、下周继续长阳并更后一周调整、连续周阳而以日线完成调整。', ['周期K线图', '调整', '突破'], ['p0042-b005'], ['2007-07-27该次突破后的周线情景分类'], 3, '完整保存四种情景及时间先后', '弱强排序描述所列走势，不将四类推广成所有走势的几何完备分类。')
    add(65, 'weekly-strength-policy-tradeoff-case', '作者在该四种周线情景中，从中长线健康及基本面阻力角度反对第三、四种强势走势，并明确自身只是市场分力。', ['政策风险', '市场分力', '市场风险'], ['p0042-b006', 'p0043-b000'], ['2007-07-27周线情景及当时基本面背景'], 4, '保留强势技术形态与政策风险的作者比较', '不补充现行印花税等制度事实。')
    add(65, 'five-day-line-window-case', '作者把当时5日线作为能否直接真突破的关键：若下周初均线上移到当前位置而指数仍不脱离该区间，则面临重新回跌。', ['均线', '突破', '假突破'], ['p0043-b001'], ['2007-07-27讨论下周初', '均线上移与指数仍在区间两个联合条件'], 3, '保留均线、价格及窗口联合判断', '不压缩成触及5日线就下跌。')
    add(65, 'weekly-second-preferred-case', '作者在当次四种演化比较中认为第二种最有利多头，第一种给空头喘息机会，并偏好上下震荡的差价机会。', ['市场震荡', '操作策略', '周期K线图'], ['p0043-b001', 'p0043-b002'], ['2007-07-27前述四种特定情景'], 4, '保存作者操作偏好与强弱比较', '这不是本项目验证的最优策略。')
    add(65, 'rotation-breadth-restart-case', '作者在2007-07-27要求观察成分股轮动是否扩散到其他股票，并在各线轮动后看一线能否重新启动，否则大盘可能休息。', ['板块轮动', '市场风险'], ['p0043-b004'], ['当时一二三线轮动顺序的观察'], 3, '保留轮动广度及重新启动的技术解释', '不发明一二三线的外部分组阈值。')
    add(65, 'divergence-segment-invalidation-case', '在当时日MACD未突破前高、且没有作者所说极强走势例外时，作者把行情视为背驰段；除非背驰段被破坏，否则处在区间套定位过程中。', ['MACD', '背驰段', '区间套'], ['p0043-b009', 'p0044-b000'], ['2007-07-27日线技术情境', '原文6000至8000点极强走势是该情景例外'], 3, '保留背驰段、失效与定位的条件关系', '不把当时指数目标或MACD前高推广为所有背驰的充分定义。')
    add(65, 'high-point-line-false-break-case', '作者在当时认为，若指数基本保持在前两高位连线上震荡整理会走强，否则应面对假突破后的清理风险。', ['高点连线', '假突破', '市场震荡'], ['p0044-b001'], ['2007-07-27具体指数突破背景'], 4, '保存条件两侧的历史技术解释', '原文的行情自身规律与操作立场也保留在引文。')
    add(65, 'weekly-second-branches-support-case', '作者在第一种周线情景未发生后，把第二种的下周线再分为长阴、十字星或小阴小阳、长上影，并将长阴视为巨大风险情景，要求守住5日线或前两高点连线。', ['周期K线图', '均线', '高点连线', '市场风险'], ['p0044-b002'], ['2007-07-27所剩第二至第四种情景', '此处是第二种内部的分类'], 3, '保留分类层级及支撑边界', '不把同文不同层的第二种合并，不把守线扩展为永远不跌。')
    add(65, 'holding-or-center-oscillation-case', '在当时支撑线守住、长阴风险未出现的情形下，作者提出持股或用部分筹码作中枢震荡操作。', ['持股', '中枢震荡', '仓位'], ['p0044-b002'], ['2007-07-27当时行情', '仅用部分筹码进行中枢震荡操作'], 2, '保留策略选择及部分仓位限制', '不是任意指数位置均适用的持股建议。')
    add(65, 'rise-then-fail-adjustment-case', '作者在该周末情景中认为，先扬后抑时若再次上攻失败或出现15分钟以上短线背驰，会引发有力度调整；先抑后扬可能更轻松。', ['背驰', '调整', '操作级别'], ['p0044-b003'], ['2007-07-27讨论下周初', '上攻失败或15分钟以上短线背驰的分支'], 4, '保存时序及级别条件', '原文形势判断归于作者，不作跨市场预测公式。')
    add(65, 'capital-entry-batches-protection-case', '作者在2007-07-30把先后3600、4000、4300点进入的资金描述为相继推动行情，并讨论守住后续位置可吸引下一拨资金。', ['资金入场批次', '市场合力'], ['p0044-b006', 'p0045-b002'], ['2007-07-30当时资金批次叙述'], 4, '保留入场位置和资金利益差异', '保护膜是作者比喻，不声称实际风险被消除。')
    add(65, 'weekly-daily-adjustment-choice-case', '作者在2007-07-30区分周线上影调整与日线形式调整，并认为先扬后抑会增加后面的调整压力。', ['周期K线图', '调整'], ['p0045-b000'], ['2007-07-30第二与第三种周线选择'], 4, '保留日周尺度及先后变化', '不能只按编号脱离前述四种情景。')
    add(65, 'entry-cost-month-end-preferences-case', '作者在月末前按资金进入位置区分对月线十字星、阴线与震荡短差机会的不同接受程度。', ['资金入场批次', '周期K线图', '成本'], ['p0045-b001'], ['2007-07-30月末前三天', '分别对应4300、4000和3600点入场资金'], 4, '保存成本位置影响形态诉求的作者解释', '情景参数留在条件与引文，不推导通用资金心理定律。')

    add(66, 'main-funds-adapt-markets-sectors', '作者认为主力资金为了随市场发展和维持位置，会在不同市场、板块之间持续变换运作对象。', ['主力资金', '板块轮动', '经济大势'], ['p0046-b000'], ['第66课作者关于主力资金演变的宏观说明'], 4, '补全经济大势之后的运作对象变化', '折腾的修辞保留在引文，不把持续运作解释为固定交易频率。')
    add(66, 'top-funds-competition-not-static', '作者描述最大的资金势力也会随年代改变，彼此仍存在竞争，并非最大势力之间没有冲突。', ['主力资金', '资金食物链'], ['p0046-b001', 'p0046-b002'], ['作者对资金食物链上层的一般性描述'], 4, '保留上层身份变化与相互竞争', '未添加真实机构姓名或未提供的历史事例。')
    add(66, 'food-chain-balance-and-nonmarket', '作者认为上层主力偏好有利自己的分层生态平衡，可能针对破坏平衡的势力采取行动，且行动未必是市场化的。', ['资金食物链', '主力资金', '市场风险'], ['p0046-b003'], ['第66课作者的资金生态解释'], 4, '保存宏观叙述的完整范围和方式限定', '类比称呼不作法律事实或本项目已证实的阴谋判断。')
    add(66, 'three-batches-month-end-alignment-case', '作者在2007-07-31把当时回试4335点与新进资金维护成本线联系起来，并认为三拨资金在月末暂时有共同做多利益。', ['资金入场批次', '成本', '市场合力'], ['p0046-b005'], ['2007-07-31月线收盘日', '三拨资金仅暂时利益一致'], 4, '保留短时利益一致及回试解释', '不将资金意图视为本项目独立核实事实，不省略暂时。')
    add(66, 'monthly-half-line-first-defense-case', '作者在当时月K线一半位置与1/2线接近的条件下，称突破多了一道中线防线，同时明确不能说万无一失。', ['周期K线图', '突破', '市场风险'], ['p0046-b006'], ['2007-07-31月线确立后的当时技术位置'], 4, '保留技术有利条件及失效可能', '不能说万无一失须与防线判断一起读取。')
    add(66, 'fundamentals-uncertainty-collective-case', '作者认为能否复制去年8月后的走势仍有基本面不确定性，该因素不是某一拨资金所能控制，而是合力结果。', ['市场合力', '市场风险', '主力资金'], ['p0046-b007', 'p0047-b000'], ['2007-07-31对后续走势的历史比较'], 3, '保留单一资金不可控制及不确定性', '不把复制历史走势写成确定预言。')
    add(66, 'simple-average-indicator-context', '作者给不会看复杂图形者提供5日线、或中线5周均线的简单观察指标，依据是此前几次单边势的经验表现。', ['均线', '操作熟练程度', '周期K线图'], ['p0047-b001'], ['2007-07-31对前几次单边行情的经验总结'], 2, '保存简化观察方法及其经验语境', '原文三天收于5日线下的描述不是新的普遍有效跌破定义。')
    add(66, 'divergence-segment-await-confirmation-case', '作者在当时允许先将日线按背驰段观察，再由后续走势确认背驰段是否有效。', ['背驰段', '确认', '周期K线图'], ['p0047-b001'], ['2007-07-31日线的当时观察'], 2, '保留待确认与已成功背驰的区别', '对照64课已发布背驰段可延续，未预先认定背驰成功。')
    add(66, 'rapid-rise-technical-policy-risk-case', '作者在当时认为过快通过4500点会埋下技术隐患，周线继续长阳会加重可能的政策隐患；即使突破也偏好反复震荡。', ['政策风险', '市场风险', '市场震荡'], ['p0047-b001', 'p0049-b003'], ['2007-07-31及2007-08-01当周的政策与技术语境'], 4, '保留技术和政策两个风险层面', '此为历史条件判断，不作现行政策预测。')
    add(66, 'oversold-rotation-awaits-medium-confirmation', '作者在当时超跌股自年线或半年线上来的语境中，将充分轮动行情与大盘中线上升完全确立联系起来，并指出该确立尚不完全。', ['板块轮动', '均线', '确认'], ['p0047-b002'], ['2007-07-31超跌股与大盘中线背景'], 3, '保留尚未确认这一状态', '不将形态逐步变好偷换成中线上升已经确立。')
    add(66, 'larger-level-frequency-and-practice', '作者在新手答疑中建议技术不佳者扩大操作级别，并举每月一两次为例，强调最优买卖位置需要磨练、不可一上手就强求。', ['操作级别', '操作熟练程度', '市场心理'], ['p0047-b013'], ['2007-07-31针对技术不佳新手', '30分钟以上甚至日线的建议语境'], 2, '补全频率举例、心态与熟练前提', '次数是该建议中的举例，不规定所有日线交易者月频率。')
    add(66, 'news-long-deployment-short-trade-distinction', '作者在钢铁医药消息答疑中指出，主力从去年开始的长期布局与提问者短线买入属于不同时间层面。', ['主力资金', '操作级别', '公开信息'], ['p0048-b002'], ['2007-07-31钢铁医药布局与短线消息问题'], 3, '保留消息理解中的时间尺度区别', '没有把作者答案改成消息应一律反着看。')
    add(66, 'standard-divergence-minimum-level-scope', '作者说明，标准背驰概念在最低级别之上使用，线段上的判断只能是类背驰。', ['背驰', '类背驰', '最低级别', '线段'], ['p0048-b014'], ['采用作者此段的严格术语范围'], 1, '补全背驰与类背驰的层次限制', '保留原文之上，不自行补成某个固定分钟数的严格大于或大于等于算法。')
    add(66, 'small-platform-direction-confirmation', '在类小转大讨论中，作者说一般有小平台，因平台也可向下突破，等待平台确认向上后介入更好。', ['小级别转大级别', '确认', '操作策略'], ['p0048-b014'], ['线段层次的类小转大', '一般而非所有情形有小平台'], 2, '独立保留平台可能失败的方向', '不补造平台宽度、持续时长或价格阈值。')
    add(66, 'subminute-operation-skill-exception', '作者强调，除非技术已经很好，否则不要参与1分钟以下的操作。', ['操作级别', '操作熟练程度'], ['p0048-b014'], ['2007-07-31答疑对低周期操作的建议'], 2, '保存技能例外与分钟边界', '与交易通道答复并列但不混为作者承诺可盈利。')
    add(66, 'adjustment-five-week-patience-case', '作者在2007-08-01将当时震荡视为先卖后买的短差机会，并认为等待5周均线上来更稳健。', ['市场震荡', '均线', '操作策略'], ['p0049-b001'], ['2007-08-01特定周线调整背景'], 3, '保留等待与操作节奏', '不概括为任何震荡都应先卖后买。')
    add(66, 'high-line-effective-break-gap-case', '作者以当时前两高点连线约4260点且10日线接近该处，作为调整强弱观察；有效跌破则上周缺口面临考验。', ['高点连线', '均线', '有效跌破', '缺口'], ['p0049-b002'], ['2007-08-01该指数技术位置'], 3, '保留两个技术位置与失守后果', '实际看p49日线图，但只收录作者文字判断，不将图中每个区间标成已确认中枢。')
    add(66, 'five-day-retest-two-directions-case', '作者在跌破5日线后的当时情境中分别讨论反抽不能重站而调整加大，与重站后再挑战4500点。', ['均线', '反抽', '调整'], ['p0049-b003'], ['2007-08-01已经跌破5日线的具体背景'], 3, '保留反抽两侧分支', '不把反抽不来归入未给出数值的所有级别统一阈值。')
    add(66, 'early-holder-no-add-case', '作者针对当时第一拨已入场者提出不在该位置加码，而通过先卖后买的震荡差价降低成本，以应对不能突破4500点的风险。', ['资金入场批次', '成本', '仓位', '操作策略'], ['p0049-b004'], ['2007-08-01第一拨持仓者及日线背驰段背景'], 3, '保留入场位置与风险场景', '不转述为所有账户都能确定降成本或市场预测无任何用途。')
    add(66, 'buy-sell-points-no-chasing-case', '作者在当时行情中要求不杀跌、不追涨，按买卖点操作，并将先卖后买作为所述行情的节奏。', ['买卖点', '追高', '操作策略'], ['p0049-b005', 'p0050-b000'], ['2007-08-01作者对能看懂线段、中枢、走势类型者的说明'], 2, '保留纪律与能力语境', '跨页引文补齐，历史个股启动预期不作确定收益。')
    add(66, 'intraday-sell-point-not-daily-location-case', '作者把当日高点解释为15分钟背驰及区间套定位，并明确60分钟未进背驰段，所以不能称日线背驰段已经被定位，只能视作15分钟卖点引发。', ['背驰', '背驰段', '区间套', '操作级别', '卖点'], ['p0049-b005', 'p0050-b000'], ['2007-08-01当日高点案例', '60分钟尚未进入背驰段'], 2, '保留不同层次定位的否定边界', '只收录文字解释；p49仅日线示意，15分钟区间套的完整图示核验继续pending。')
    add(66, 'watch-fifteen-minute-plus-sells-case', '作者在该周的操作提醒中要求注意15分钟以上级别卖点。', ['卖点', '操作级别'], ['p0050-b000'], ['2007-08-01所讨论的当周', '作者已在上周作过同类提醒'], 3, '保存操作提醒的明确级别与时间', '不是所有时期必须使用15分钟的普遍规则。')

    drawing = by_id['lower-l065-two-drawings-change-meaning-with-unit']
    drawing['evidence'][0]['figure_ids'] = [PREFIX + 'p0039-fig1']
    drawing['figure_review_note'] = '主代理实际查看PDF39上部两幅笔折线题图及同页后续作者说明，确认比较对象对应。只记录作者明确说的笔/线段解释差别；不认定读者完整答案，也不确认图的原始绘制者，origin_status仍为unverified。'

    for record in records:
        for evidence in record['evidence']:
            source = passages[evidence['passage_id']]['text']
            assert evidence['quote'] in source, record['id']
            evidence['quote_start'] = source.index(evidence['quote'])
    assert len({r['id'] for r in records}) == len(records)
    (HERE / (BATCH + '.jsonl')).write_text('\n'.join(dump(r) for r in records) + '\n', encoding='utf-8')
    pending = [
        {'id': 'lower-l065-twelve-exercise-answers', 'lesson': 65, 'passage_id': PREFIX + 'p0037-b002', 'status': 'pending', 'issue': '已查看12种笔走势题图；本单元未列出逐图作者完整答案，不能由模型或读者代答后标作原文明说。'},
        {'id': 'lower-l065-two-drawings-full-answers', 'lesson': 65, 'passage_id': PREFIX + 'p0039-b000', 'status': 'pending', 'issue': '作者只明确图中笔与线段解释的本质区别，没有逐一确认插班生给出的划分答案；完整逐图答案待另找明确作者说明。'},
        {'id': 'lower-l065-figure-origin', 'lesson': 65, 'status': 'pending', 'issue': '9个图对象已实际查看。p35两图FHSL 20080729/20080730明确后加；p34图内有张太山署名但日期及原始归属未核，其余图来源未核，不能当作者原图证言。'},
        {'id': 'lower-l066-intraday-nesting-figure', 'lesson': 66, 'passage_id': PREFIX + 'p0050-b000', 'status': 'pending', 'issue': '作者15分钟背驰/区间套与60分钟、日线的文字边界已收录；p49仅日线图，未找到本段完整15分钟区间套图示，具体图示结论未核。'},
        {'id': 'lower-l066-figure-origin', 'lesson': 66, 'status': 'pending', 'issue': '已查看本单元p49唯一图对象及相邻p50（同页67课定义图另属67课）；p49图原始作者未核。'},
    ]
    links = {}
    for record in records:
        for e in record['evidence']:
            links.setdefault(e['passage_id'], []).append(record['id'])
    titles = {'p0032-b006', 'p0035-b001', 'p0037-b000', 'p0037-b005', 'p0038-b005', 'p0039-b007', 'p0040-b002', 'p0040-b006', 'p0040-b011', 'p0041-b004', 'p0042-b003', 'p0043-b005', 'p0044-b004', 'p0045-b003', 'p0046-b004', 'p0049-b000'}
    specific = {'p0032-b008': '引入包含问题的过渡，具体公式已分别收录', 'p0032-b011': '引入方向严格定义，具体判断在下一段', 'p0037-b001': '日记与课程编号更正，保留来源历史', 'p0037-b002': pending[0]['issue'], 'p0039-b000': pending[1]['issue'], 'p0039-b001': '要求答题的过渡，题图结论见后文', 'p0040-b001': '饮食与出行日记，不是技术解释', 'p0041-b005': '好友申请上限通知，不是技术解释', 'p0040-b009': '4159点1/2线重要性已由p0041-b001的两侧情景完整承载', 'p0041-b006': '站稳1/2线与攻击前高的历史叙述已由相邻明确情景及突破确认命题承载', 'p0043-b003': '作者自身按市场选择操作的历史姿态，情景适应已收录', 'p0044-b005': '当日资金顶住的修辞与具体经过，后文资金批次解释已收录', 'p0047-b003': '基本面尚无结果与稳健要求已由本单元不确定性和策略命题承载'}
    ledger = []
    for pid, passage in passages.items():
        suffix = 'p' + pid.rsplit('-p', 1)[-1]
        claim_ids = links.get(pid, [])
        if claim_ids:
            result, reason = 'new_claim', '原子知识及共同条件见关联记录；历史行情有明确日期、对象及作者归属'
        elif passage['role'] == 'reader':
            result, reason = 'reader_context', '完整对照后续作者回复；读者问题或答案仅作语境，不作为作者直接证据'
        elif suffix in {'p0037-b002', 'p0039-b000'}:
            result, reason = 'pending', specific[suffix]
        elif suffix in titles or passage['role'] == 'unknown' or re.match(r'^缠中说禅20', passage['text']):
            result, reason = 'transition', '篇名、身份时间头或答疑分隔，语义由相邻具体段落承载'
        elif suffix in specific:
            result, reason = 'context_or_already_covered', specific[suffix]
        else:
            result, reason = 'historical_background', '顺序读过；作者个人出行、政治修辞、具体市场行动或行情回顾，未另制造一般技术规则'
        local = [r for r in records if r['id'] in claim_ids]
        ledger.append({'passage_id': pid, 'lesson_number': int(passage['unit_id'][-3:]), 'source_text_sha256': hashlib.sha256(passage['text'].encode()).hexdigest(), 'role': passage['role'], 'result': result, 'claim_ids': claim_ids, 'reason': reason, 'rounds': {'1_read_and_scope': '整段及前后文顺序审读，识别正文、附文、读者和作者回复', '2_atomic_conditions': '支持命题按对象、量词、时间和联合条件拆解；其余按result记录', '3_normalization': {'reused_concepts': sorted({c for r in local for c in r['concepts'] if c in concepts_before}), 'new_concepts': sorted({c for r in local for c in r['concepts'] if c not in concepts_before})}, '4_reverse_check': '回看关联命题引文及必要原页，量词、方向、否定与图源分别核对；未答题和图源仍pending'}})
    (HERE / (BATCH + '.coverage.jsonl')).write_text('\n'.join(dump(r) for r in ledger) + '\n', encoding='utf-8')
    (HERE / (BATCH + '.pending.jsonl')).write_text('\n'.join(dump(r) for r in pending) + '\n', encoding='utf-8')
    summaries = []
    for lesson, pages, figure_count in [(65, [32, 33, 34, 35, 36, 37, 39, 42, 44], 9), (66, [47, 48, 49, 50], 1)]:
        summaries.append({'lesson_number': lesson, 'document_id': 'volume_2-5332cd1b6038', 'whole_lesson_semantic_read_complete': True, 'technical_extraction_complete': False, 'four_round_review': True, 'reviewer': REVIEWER, 'batch': BATCH, 'base_graph_version': version, 'actual_read_scope': '全部112段，PDF32-b006至45-b002' if lesson == 65 else '全部59段，PDF45-b003至50-b000', 'records': sum(r['id'].startswith(f'lower-l{lesson:03d}-') for r in records), 'legacy_unimported_records_re_reviewed': 21 if lesson == 65 else 14, 'supersedes_unimported_records': {'file': 'batch_003_l065_l067.jsonl', 'id_prefix': f'lower-l{lesson:03d}-'}, 'coverage_ledger': BATCH + '.coverage.jsonl', 'pending': [p for p in pending if p['lesson'] == lesson], 'visual_pdf_pages': pages, 'figure_objects_viewed': figure_count, 'logged_at': datetime.now(timezone.utc).isoformat()})
    (HERE / (BATCH + '.summary.json')).write_text(json.dumps(summaries, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    db.close()
    print(dump({'batch': BATCH, 'records': len(records), 'by_lesson': {s['lesson_number']: s['records'] for s in summaries}, 'passages_read': len(passages), 'pending': len(pending), 'base_graph_version': version}))


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    build()
