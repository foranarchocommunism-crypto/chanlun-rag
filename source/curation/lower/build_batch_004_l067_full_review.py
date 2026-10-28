"""Materialize the root agent's four-round lesson-67 review; no DB writes."""
import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
KB = HERE.parents[2] / "shared-knowledge/v0.1.0"
PREFIX = "volume_2-5332cd1b6038-"
REVIEWER = "主代理 / 阶段C第67课四轮原文复核"
BATCH = "batch_004_l067_full_review"


def dump(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def build():
    db = sqlite3.connect((KB / "graph.sqlite").as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    passages = {r["id"]: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id='lesson-067' ORDER BY pdf_page,block_index,id")}
    concepts_before = {r["label"]: r["id"] for r in db.execute("SELECT id,label FROM concepts")}
    base_version = json.loads(db.execute("SELECT value FROM metadata WHERE key='graph_version'").fetchone()[0])
    records = [json.loads(line) for line in (HERE / "batch_003_l065_l067.jsonl").read_text(encoding="utf-8-sig").splitlines() if line.strip() and json.loads(line)["id"].startswith("lower-l067-")]
    by_id = {r["id"]: r for r in records}
    common = "第一轮完整顺序阅读本课78个现有段落（PDF50-b001至59-b004）及问答；第二轮按联合条件、方法与案例拆解；第三轮与现有概念及已入库62/64/72课命题对照，不合并不同对象；第四轮逐条回到以下引文核对主语、量词、方向、例外和历史语境。主代理同一轮次的不同检查视角，不称独立或人工复核。"
    for record in records:
        record["reviewer"] = REVIEWER
        record["review_note"] = common + " 本记录重新核对未入库批003对应条目；正文定义不依据后加图新增规则。"
        record["importance_reason"] = record["importance_reason"].replace("该分级为整理判断。", "；分级为整理判断。")
    by_id["lower-l067-segment-unique-recursive-base"]["conditions"] = ["同一级别图上的走势", "按本课给出的线段划分定义"]
    by_id["lower-l067-feature-sequence-opposite-strokes"]["conditions"] = ["按线段起始笔方向区分"]
    by_id["lower-l067-feature-sequence-gap"]["conditions"] = ["特征序列相邻两元素的价格区间"]
    by_id["lower-l067-standard-feature-sequence"]["conditions"] = ["按一般K线分型方法对特征序列作非包含处理", "无特别说明时使用标准特征序列"]
    by_id["lower-l067-case-one-up-end"]["conditions"] = ["原线段由向上笔开始", "标准特征序列顶分型已成立", "该分型第一、第二元素之间没有特征序列缺口"]
    by_id["lower-l067-case-one-down-end"]["conditions"] = ["原线段由向下笔开始", "标准特征序列底分型已成立", "该分型第一、第二元素之间没有特征序列缺口"]
    by_id["lower-l067-case-two-up-end"]["conditions"] = ["原线段由向上笔开始", "原标准特征序列顶分型第一、第二元素之间有缺口", "从该顶分型最高点开始的向下一笔所起序列，其特征序列出现底分型"]
    by_id["lower-l067-case-two-down-end"]["conditions"] = ["原线段由向下笔开始", "原标准特征序列底分型第一、第二元素之间有缺口", "从该底分型最低点开始的向上一笔所起序列，其特征序列出现顶分型"]
    necessary = by_id["lower-l067-feature-fractal-necessary"]
    necessary["text"] = "出现特征序列分型是线段结束的前提条件。"
    necessary["conditions"] = ["按第67课给出的精确线段划分定义"]
    necessary["review_note"] += "只保留必要前提，不把出现任意分型改写为充分确认；有缺口分支仍需第二序列确认。"
    inclusion = by_id["lower-l067-inclusion-only-if-contained"]
    inclusion["text"] = "作者回复指出，不存在包含关系就不需要合并；包含指一根K线完全在相邻K线范围内。"
    inclusion["conditions"] = ["相邻K线合并判断的作者答疑"]
    inclusion["ambiguity_status"] = "equal_boundary_details_pending"
    inclusion["evidence"] = [e for e in inclusion["evidence"] if e["passage_id"].endswith("p0056-b005")]
    inclusion["review_note"] += "核对p56-b004-s01作者头与读者列举的等值问题；只记录作者明确回答，不自行构造所有等号/麻点处理算法。"
    dynamic = by_id["lower-l067-dynamic-position-building"]
    dynamic["text"] = "作者将建仓描述为动态过程，并称成本未降到一定值时建仓尚未完成。"
    dynamic["conditions"] = ["2007-08-02关于长期建仓示例的作者回复"]
    dynamic["evidence"] = [e for e in dynamic["evidence"] if e["passage_id"].endswith("p0057-b010")]
    dynamic["review_note"] += "个股价格只保留在原文语境；不把成本阈值补成未给出的数值。"
    average = by_id["lower-l067-moving-average-effective-break"]
    average["text"] = "该辅助均线策略所说的有效跌破，是跌破后相应级别的反抽上不来；月线跌破至少看下个月的反抽，不能以一日判断。"
    average["conditions"] = ["作者给低熟练操作者的辅助均线策略", "反抽观察须与所讨论级别对应"]
    average["concepts"] = ["均线", "有效跌破", "反抽"]
    average["importance_level"] = 2
    average["relations"] = [{"source": "有效跌破", "target": "均线", "type": "defines"}, {"source": "有效跌破", "target": "反抽", "type": "requires"}]
    average["review_note"] += "语境：2007-08-03上涨市场附文中的分层操作建议；适用条件：给低熟练操作者的辅助规则，不将均线周期直接当作中枢级别。"
    shares = by_id["lower-l067-maintain-shares-reduce-cost"]
    shares["text"] = "作者建议大资金和散户中高手利用震荡降低成本、保持持仓数量，并把这种操作解释为现金增加而筹码不减少。"
    shares["conditions"] = ["2007-08-03上涨市场附文", "针对大资金及散户中高手", "利用震荡降低成本且保持持仓数量"]
    shares["concepts"] = ["成本", "仓位", "市场震荡", "操作熟练程度"]
    shares["review_note"] += "语境：该日上涨与资金博弈说明；适用条件：作者针对具备相应操作能力者的策略，不保证实际执行一定降低仓位或消除风险。原文关于仓位自然下降的判断保留在引文，不写成本项目证明的数学定理。"

    def add(slug, text, concepts, sources, conditions, level, reason, note, exceptions=None, relations=None, quote=None, figures=None):
        evidence = []
        for suffix in sources:
            passage = passages[PREFIX + suffix]
            citation = {"passage_id": passage["id"], "quote": quote if quote is not None else passage["text"]}
            if figures:
                citation["figure_ids"] = [PREFIX + f for f in figures]
            evidence.append(citation)
        record = {"id": "lower-l067-" + slug, "text": text, "kind": "explicit", "conditions": conditions, "exceptions": exceptions or [], "concepts": concepts, "ambiguity_status": "none", "review_note": common + " " + note, "reviewer": REVIEWER, "evidence": evidence, "relations": relations or [], "importance_level": level, "importance_reason": reason + "；分级为整理判断。"}
        if any(passages[e["passage_id"]]["role"] == "author_commentary" for e in evidence):
            record["review_note"] += " 语境：本课后附2007-08-02或08-03作者市场说明，日期和篇名以证据为准；适用条件：保留本条所列对象、熟练程度及历史情境，不改写为无条件普遍保证。"
        if figures:
            record["figure_review_note"] = "主代理实际查看PDF55图像，可见红绿箭头指向MACD黄白线或柱子；结合p57作者文字只解释箭头用途，不认定全部标号买卖点有效。图的原始作者身份仍为unverified，不把汇编图像直接当作者原图证言。"
        records.append(record)

    add("stroke-notation", "第67课用S表示向上的笔，用X表示向下的笔。", ["笔", "特征序列"], ["p0050-b002"], ["第67课符号约定"], 3, "保留特征序列公式中符号的明确含义", "符号来自作者明确定义，不把S/X推广为其他课程全部公式的固定变量。")
    add("two-starting-directions", "线段按其起始笔分为从向上笔开始和从向下笔开始两类。", ["线段", "笔"], ["p0050-b002"], ["按线段起始笔方向分类"], 1, "线段及特征序列方向分类的基础", "保留起始笔分类，避免用全段涨跌幅替代起始方向。")
    add("opposite-sequence-overlap-rationale", "在以向上笔开始线段的S1X1S2X2…表示中，相邻Si与Si+1有重合区间，Xi与Xi+1却不一定重合；作者据此用后者考察线段性质。", ["线段", "笔", "特征序列", "重叠"], ["p0050-b003"], ["以向上笔开始线段的笔序列表示"], 2, "解释选择反向笔作特征序列的依据", "同段核对两个序列不同的重合性质，不把不一定改成一定不。")
    add("definition-refines-segment-destruction", "作者明确把第67课的两种划分情况称为对“线段被另一个线段破坏”的精确化，并要求以该精确定义为后续划分基础。", ["线段", "线段破坏", "特征序列"], ["p0051-b004"], ["第67课关于自身定义与先前表述的关系"], 1, "作者明确说明规则精确化的依据", "只建立作者本段明说的关系，不用发表日期自动认定任意后文推翻前文。", relations=[{"source": "线段破坏", "target": "特征序列", "type": "requires"}])
    add("learning-order", "学习本课线段划分时，作者要求先理解特征序列、标准特征序列及其顶底分型，再按分型第一和第二元素间是否有缺口区分两种情况。", ["线段", "特征序列", "标准特征序列", "分型", "特征序列缺口"], ["p0051-b005"], ["本课线段划分定义的学习顺序"], 2, "避免脱离标准序列直接判分型或缺口", "学习顺序按原段保留，不把图邻域路径当成独立逻辑证明。")
    add("definition-before-illustration", "作者要求学习线段划分先看清定义，并把图形定位为帮助分清概念的辅助。", ["线段", "技术分析"], ["p0051-b007"], ["本课作者关于定义和图示的说明"], 2, "限定图示与文字定义的解释地位", "只记录文字中的方法说明；实际查看p50-53，不认定后加图属于作者原图。")
    add("rebound-not-safety-confirmation", "在2007-08-02解盘中，作者不把当日反弹并收于5日线上直接视为市场安全，关注下周一前能否确认重站5日线，并提醒历史K线组合不会简单重复。", ["均线", "反弹", "K线"], ["p0054-b001"], ["2007-08-02当时短线市场", "观察窗口延伸至下周一"], 4, "保留历史案例中的确认与相似形态边界", "保留市场时点与确认对象；不把具体周三/周四组合变成普遍预测规则。", exceptions=["历史不会简单重复"])
    add("weekly-gap-convention", "作者在当时解盘中把周线缺口“三周不补就以后再补”称为技术惯例，并用它说明当时资金博弈背景。", ["缺口", "周期K线图"], ["p0054-b002"], ["周线缺口", "2007-08-02作者称技术惯例的经验描述"], 3, "收录经验性技术说明并保留其强度", "惯例不改写成永不回补或三周后必然回补，不作本项目实证结论。")
    add("rally-policy-feedback-case", "作者在该日假设中把急于突破4500点、吸引大量新资金并形成单边行情，与政策环境不利变化联系起来，并用“必然”表达自己的判断。", ["政策风险", "资金入场批次"], ["p0054-b003"], ["2007-08-02特定政策环境及4500点假设"], 4, "保留历史风险情景而不伪装成一般规律", "忠实保留作者判断语气，外层注明这是当时的情境判断，不推演现行制度。")
    add("range-consolidation-market-view", "在当时4000至4500点背景下，作者认为高位合理震荡或较长箱体震荡，比连续多根周K线长阳更有利于市场长远发展。", ["市场震荡", "K线"], ["p0054-b004", "p0055-b000"], ["2007-08-02解盘中的指数区间与政策背景"], 4, "保存行情附文中的技术比较及具体参数", "保留历史参数及作者判断，不将该点位范围推广到其他市场。")
    add("early-holder-no-addition-case", "针对当时已在3600点附近买足的第一拨持仓者，作者提出不增仓、保持仓位先卖后买打差价以降低成本的策略。", ["仓位", "成本", "操作策略"], ["p0055-b001"], ["2007-08-02特定上涨行情", "第一拨已买足的持仓者", "保持仓位的先卖后买操作"], 3, "保留资金位置不同导致的操作适用条件", "原文‘永远立于不败之地’保留在引文，作为作者修辞，不转述成确定盈利或绝对无风险。")
    add("chart-arrows-comparison", "作者在当次附文答疑中解释，红绿箭头用于提示比较所指黄白线或柱子面积。", ["MACD", "指标对比"], ["p0057-b007"], ["2007-08-02附文图的红绿箭头释义"], 3, "保留指标图中可查证的作者文字解释", "核对p57读者提问与作者答复，实际查看p55图；只解释箭头用途，不认定图示全部买卖点。", figures=["p0055-fig1"])
    add("global-market-duration-caveat", "作者在当时全球股灾答疑中反对中国股市可以永远逆全球股市上涨的说法，同时允许一天、两天这样的短时情形。", ["市场风险"], ["p0055-b007"], ["2007-08-02关于全球股市关联的作者答疑"], 4, "保存作者市场判断的时间与量词边界", "不作本项目验证过的宏观定律，不把不可能永远加强成不可能持续任何较长时段；作者并未认同提问者的全部前提。")
    add("policy-risk-rule-change", "作者在当时权证停牌答疑中强调政策风险应随时预防，并提醒交易规则也可能改变。", ["政策风险", "交易规则"], ["p0056-b009", "p0056-b010"], ["2007-08-02关于权证停牌和制度风险的答疑"], 2, "记录制度变化这一风险管理前提", "历史事件只作语境，不把该文当作现行交易规则或法律说明。")
    add("buy-point-relative-zero-cost-safety", "作者在该政策风险答疑中强调按买点买入，并把零成本仅称为“相对安全”。", ["买点", "成本", "市场风险"], ["p0056-b009"], ["2007-08-02政策风险答疑的操作立场"], 2, "保留买点纪律和相对安全限定", "原文的‘相对’不能删掉，不改写成零成本保证无风险。")
    add("understand-market-institution", "作者要求参与某一交易所市场前先认识其规则与制度条件。", ["交易规则", "市场风险"], ["p0056-b011"], ["当时关于交易规则异议的答疑", "参与该交易所市场的前提说明"], 3, "记录实际操作前的制度条件", "不补造具体法条或本项目不存在的交易所规范。")
    add("operation-versus-dispute", "作者在该答疑中主张股票用于实际操作而不是争吵，并以盈亏结果评价操作。", ["操作策略", "市场心理"], ["p0056-b011"], ["2007-08-02作者的操作价值判断"], 3, "保留操作心理与评价方式", "这是作者表述的价值立场，不把事后盈利当成本项目的真理判定方法。")
    add("macd-zero-axis-context-confirmation", "针对当次60分钟背驰问题，作者以“对”确认紧邻读者所说的黄白线尚未回抽零轴这一观察。", ["MACD", "背驰"], ["p0057-b001"], ["2007-08-02当次60分钟图讨论", "仅确认紧邻p0057-b000的观察"], 4, "保存简短作者答复的明确上下文", "逆向核对p56-b014、p57-b000及作者时间头；只引用作者的‘对’，读者句留在自动返回上下文，不把整个问题或任意未回零轴情形当普遍定理。")
    add("currency-appreciation-uncertainty", "作者在当时宏观答疑中把大规模升值后难以软着陆说成带“似乎”限定的历史观察，并对中国能否例外保留不确定性。", ["市场风险", "宏观市场判断"], ["p0057-b004"], ["2007-08-02关于物价及货币升值的答疑"], 4, "保存作者经验观察的语气和不确定性", "不把外部货币战争帖子内容补入；‘似乎’和‘能否例外’不删去。")
    add("position-cost-can-decrease", "作者反对把建仓成本必然很高作为前提，认为高明操作者建仓时成本可以不断下降。", ["动态建仓", "成本"], ["p0057-b011"], ["作者对高明操作者动态建仓的说明"], 3, "保存成本与建仓过程的非静态理解", "保留可以与适用操作者，不改成任何人建仓必然降成本。")
    add("position-building-patience", "作者建议散户学习动态建仓，并指出这种手法对没有耐心、持短线思维者是痛苦的。", ["动态建仓", "市场心理"], ["p0057-b011"], ["动态建仓的操作与心理要求"], 3, "保存方法对耐心与思维方式的要求", "作者建议与心理描述分别保留，不增加资金量阈值。")
    add("later-capital-batches-mix", "作者在该次资金博弈叙述中认为，越往后进入的资金批次，其成分一般越杂乱。", ["资金入场批次"], ["p0057-b014"], ["2007-08-03市场资金分批进入的经验叙述"], 4, "保留历史经验性市场解释", "一般来说保留为语气限制，不当成可由图谱证明的普遍资金规律。")
    add("strategy-before-endpoint-prediction", "在当时上涨博弈的比喻中，作者强调操作策略比猜行情在某一关结束更重要，并指出高手与低手应采用不同玩法。", ["操作策略", "操作熟练程度"], ["p0058-b000", "p0058-b001"], ["2007-08-03游戏比喻及操作分层语境"], 2, "保留策略、能力与预测对象的区分", "时间T和批次N在此为叙述变量；不据此声称作者否定所有走势预测，后续第68课需另作跨课查证。")
    add("moving-average-low-skill-strategy", "作者给低熟练操作者的基本辅助策略是短线看5日线、中线看5周线、长线看5月线；未有效跌破时，相应操作可保持持股。", ["均线", "操作熟练程度", "持股", "有效跌破"], ["p0058-b002"], ["2007-08-03附文给低手的策略", "没有相应级别的有效跌破"], 2, "保留均线参数、能力分层及持股条件", "与有效跌破定义独立链接，不把5日线当任意缠论中枢级别。")
    add("rotation-for-skilled-retail", "作者给散户高手的建议是利用大盘震荡中的板块轮动机会。", ["板块轮动", "市场震荡", "操作熟练程度"], ["p0059-b000"], ["2007-08-03附文", "针对散户里的高手"], 3, "保留轮动方法的技能适用范围", "不删高手限制，也不承诺一定取得最大收益。")
    add("strategy-fits-skill", "作者认为做不到高手操作时应采用低手的基本持股策略，而非因大盘短时波动慌乱。", ["操作策略", "操作熟练程度", "持股"], ["p0059-b001", "p0058-b002"], ["2007-08-03分层操作建议", "尚不具备高手操作能力"], 3, "保留能力与方法选择的匹配", "对应作者做不到高手就做低手的建议，不发明外部能力圈理论来源。")
    add("theme-stocks-no-chasing", "作者在该附文中强调题材股不要追高，并提醒错过当前股票后仍有其他机会。", ["题材股", "追高", "操作策略"], ["p0059-b002"], ["2007-08-03关于题材股的操作提醒"], 2, "保存题材操作纪律", "不附会当时个股后来收益，也不据题材推导确定盈利。", quote="注意，题材股的操作，一定不要追高，过了这个村，还有那个店，天天都有新机会，不管谁的股票，都不必追高。")
    add("case-technical-support-comparison", "在该反弹背景中，作者把MACD形态、前期两高点连线和周线缺口视为与此前比较的技术条件，并认为新进资金须守住高点连线、重站5日线。", ["MACD", "均线", "高点连线", "资金入场批次"], ["p0054-b002"], ["2007-08-02关于第三拨新进资金的情境判断", "相比6月20、21日的当时技术条件"], 4, "保留历史解盘的多条件比较", "不把这些有利条件改成单独充分上涨信号，必须与当时对象和时间一起读取。")
    add("formed-center-follow-evolution-case", "作者在当次短线说明中以其所称已形成的1分钟中枢及其演化作为观察对象，并强调当下判断。", ["走势中枢", "当下", "级别"], ["p0055-b002"], ["2007-08-02当次短线解盘", "1分钟中枢形成是作者对该案例的描述"], 3, "保存以已有中枢演化作当下观察的技术解释", "已查看p55图，仅记录作者的观察说明；不据图单独证明中枢成立或将任意1分钟图等同于1分钟中枢。")
    add("gap-open-excludes-prior-pattern-case", "作者在2007-08-03解盘中认为当日跳空高开使前述6月20前后的K线组合情形不能出现。", ["K线", "缺口"], ["p0057-b014"], ["2007-08-03当次行情与6月20前后组合的比较"], 4, "保存具体形态比较中的排除条件", "这是具体历史情形的作者判断，不造出所有跳空高开对应的普遍定理。")

    # Final reverse check: quote anchoring is automatic; the substantive
    # semantic/condition review is the root agent's work recorded above.
    for record in records:
        for evidence in record["evidence"]:
            source = passages[evidence["passage_id"]]["text"]
            if evidence["quote"] not in source:
                raise ValueError("引文与现有文本不匹配：" + record["id"])
            evidence["quote_start"] = source.index(evidence["quote"])
    batch_path = HERE / (BATCH + ".jsonl")
    batch_path.write_text("\n".join(dump(r) for r in records) + "\n", encoding="utf-8")
    source_to_claims = {}
    for record in records:
        for e in record["evidence"]:
            source_to_claims.setdefault(e["passage_id"], []).append(record["id"])
    pending = [{"id": "lower-l067-chart-seven-unanswered", "lesson": 67, "passage_id": PREFIX + "p0059-b004", "status": "pending", "issue": "作者问图中7与1分钟中枢的关系，当前单元未给答案；不能把问题当定理，已查看p58图，仍须其他明确作者讲解才能作原文明说结论。"}, {"id": "lower-l067-figure-origin", "lesson": 67, "status": "pending", "issue": "已查看本课14个图对象所在页，但p50/51/52前两图/55/58原图身份仍未核；p52-fig3、p53两图及p54图已确认陈仁后加。不将未核图或后加图当作者原始证言。"}, {"id": "lower-l067-equality-boundary-detail", "lesson": 67, "passage_id": PREFIX + "p0056-b005", "status": "pending", "issue": "作者只明确回复包含才合并的一般边界；对提问的单边等值、双边等值、麻点未逐项给算法，保留相等边界细节待跨课核对，不补造EPS或等号规则。"}]
    ledger = []
    for pid, passage in passages.items():
        links = source_to_claims.get(pid, [])
        text = passage["text"]
        if links:
            result, reason = "new_claim", "原子命题与来源对应；共同条件及语境见相应记录"
        elif passage["role"] == "reader":
            result, reason = "reader_context", "读者提问/引用保留上下文，不作作者直接证据；已对照其后明确作者回复"
        elif passage["role"] == "unknown" or text.startswith("缠中说禅20") or re.fullmatch(r"缠中说禅[：:]?20\d{2}.*", text):
            result, reason = "transition", "答疑分隔或作者时间头，仅保存身份与时间"
        elif pid.endswith("p0059-b004"):
            result, reason = "pending", pending[0]["issue"]
        elif pid.endswith(("p0055-b003", "p0057-b013", "p0059-b003")):
            result, reason = "transition", "天气/出行、日记引入或比喻修辞，不制造独立技术定理"
        elif pid.endswith(("p0054-b000", "p0057-b012", "p0050-b001", "p0050-b007", "p0050-b008", "p0051-b001")):
            result, reason = "transition", "篇名或分类标题，其结构含义由相邻定义和分支命题承载"
        else:
            result, reason = "historical_case", "具体历史资金流入、周末消息或点位预测，保留原情境，不提升为一般技术规则"
        ledger.append({"passage_id": pid, "source_text_sha256": hashlib.sha256(text.encode()).hexdigest(), "role": passage["role"], "result": result, "claim_ids": links, "reason": reason, "rounds": {"1_read_and_scope": "顺序阅读原段与相邻问答，区分正文、回复、解盘和读者", "2_atomic_conditions": "按本条result处理；支持命题保留联合条件，案例/标题不作无条件定理", "3_normalization": {"reused_concepts": sorted({c for r in records if r["id"] in links for c in r["concepts"] if c in concepts_before}), "new_concepts": sorted({c for r in records if r["id"] in links for c in r["concepts"] if c not in concepts_before})}, "4_reverse_check": "来源、量词、方向和语境已回看；仅对列出的claim作语义复核，图源与未答思考题保留pending"}})
    (HERE / (BATCH + ".coverage.jsonl")).write_text("\n".join(dump(r) for r in ledger) + "\n", encoding="utf-8")
    (HERE / (BATCH + ".pending.jsonl")).write_text("\n".join(dump(r) for r in pending) + "\n", encoding="utf-8")
    summary = {"lesson_number": 67, "document_id": "volume_2-5332cd1b6038", "actual_read_scope": "全部78个passages，PDF50-b001至59-b004；正文定义及后附两篇市场文章和答疑", "whole_lesson_semantic_read_complete": True, "technical_extraction_complete": False, "four_round_review": True, "reviewer": REVIEWER, "batch": BATCH, "base_graph_version": base_version, "records": len(records), "legacy_unimported_records_re_reviewed": 15, "coverage_ledger": BATCH + ".coverage.jsonl", "pending": pending, "visual_pdf_pages": [50, 51, 52, 53, 54, 55, 58, 59], "figure_objects_viewed": 14, "logged_at": datetime.now(timezone.utc).isoformat()}
    (HERE / (BATCH + ".summary.json")).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    db.close()
    print(dump({"batch": str(batch_path), "records": len(records), "passages_read": len(passages), "pending": len(pending), "base_graph_version": base_version}))


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    build()
