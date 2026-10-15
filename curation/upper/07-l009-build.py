"""Materialize the root agent's bounded lesson9 source review; SQLite is read-only."""
import hashlib
import json
import sqlite3
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
KB = HERE.parents[2] / "shared-knowledge/v0.1.0"
PREFIX = "volume_1-a53e99c37ca5-"
BATCH = "07-l009-complete"
REVIEWER = "主代理 / 阶段C上册第9课四轮复核"


def j(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def build():
    db = sqlite3.connect((KB / "graph.sqlite").resolve().as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    ps = {r["id"]: dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id='lesson-009' ORDER BY pdf_page,block_index,id")}
    assert len(ps) == 59
    version = json.loads(db.execute("SELECT value FROM metadata WHERE key='graph_version'").fetchone()[0])
    old_concepts = {r[0] for r in db.execute("SELECT label FROM concepts")}
    records = []
    common = "主代理顺序读完第9课59段，并实际查看PDF22至27。四轮分别核对全文和问答身份、原子命题及联合条件、既有533条命题与术语归属、逆向引文及原页图示。是同一模型的四种检查视角，不称独立或人工审查。"

    def add(slug, text, concepts, refs, conditions, level, note, figures=()):
        evidence = [{"passage_id": PREFIX + ref, "quote": ps[PREFIX + ref]["text"], "quote_start": 0, "figure_ids": []} for ref in refs]
        r = {"id": "upper-l009-c-stage-" + slug, "text": text, "kind": "explicit", "conditions": conditions, "exceptions": [], "concepts": concepts, "ambiguity_status": "none", "review_note": common + " " + note, "reviewer": REVIEWER, "evidence": evidence, "relations": [], "importance_level": level, "importance_reason": {1: "核心定义或重要成立前提", 2: "主要操作或研究方法", 3: "补充限制及方法辨析", 4: "有明确边界的历史案例"}[level] + "；为整理重要性判断，不表示证据强度或收益概率。"}
        if any(ps[e["passage_id"]]["role"] == "author_commentary" for e in evidence):
            r["review_note"] += " 语境：第9课所附2006-11-22/23历史解盘，具体日期已按原页时间头核正。适用条件：仅本条所列当时指数、板块和操作水平，不抽象成任何市场必然结果。"
        if figures:
            evidence[0]["figure_ids"] = [PREFIX + f for f in figures]
            r["figure_review_note"] = "实际查看PDF24武钢JTB1日线及PDF25上证5分钟图：图中文字与作者旁文分别对照。制作身份仍unverified，图中价格与时间不自动证明盈利或作者原发图身份；不从图内新增标注推广额外规则。"
        records.append(r)

    add("selection-program-not-perfect", "作者把按程序分类投资对象、只操作程序允许的对象列为首要原则，同时说明任何程序都不能保证入选对象最终百分之百成功。", ["操作策略", "完全分类", "市场风险"], ["p0022-b006"], ["本课讨论的投资对象筛选程序"], 2, "保留筛选与无法保证成功两面，不把能操作类等同于必盈利。")
    add("failure-discovery-not-next-guarantee", "本课以‘早泄’比喻介入后出现的失效，指出有些失效要实际介入后才发现，一次有效不能保证下一次有效。", ["操作策略", "市场风险"], ["p0022-b007"], ["‘早泄’为本课程序失效比喻"], 3, "不将比喻当生理事实，不另造确定预测算法。")
    add("failure-exit-basic-principle", "在严格资金管理的基本原则下，作者要求发现所述程序失效就退出，即使随后重新上涨；具体分批介入和退出另需严格程序。", ["资金管理", "操作策略", "市场风险"], ["p0022-b008", "p0023-b000"], ["本课所述基本原则", "具体分批操作须有严格介入和退出程序"], 2, "跨页保留立即退出及分批程序的适用层次；没有替作者编写仓位或止损数值。")
    add("long-adjustment-opportunity-cost", "作者在该失效讨论中说明，即使调整后还会继续上涨，长时间调整也可能浪费操作时间，资金还有其他可操作对象。", ["资金管理", "调整", "操作策略"], ["p0023-b000"], ["本课失效后长调整的操作语境"], 3, "不从此推出所有长期持有都错误。")
    add("program-break-and-long-data-test", "作者把所述失效归因于介入程序出现不能概括的异常，称各类程序均会面对这种破缺，并提出以长期数据测试估计异常概率。", ["操作策略", "概率原则", "市场风险"], ["p0023-b001"], ["本课介入程序及其异常概率讨论"], 2, "原文未给回测样本、算法或本项目实测数字，不补出。")
    add("isolated-program-low-rate-claim", "作者在本课把失效率低于10%的孤立介入程序称为超一流，并认为这类程序基本没有；抛硬币50%以上及10%是该段论述所用参数。", ["操作策略", "概率原则"], ["p0023-b001"], ["第9课作者论述，不是本项目统计结果"], 3, "‘十次最多一次’仍保留在精确引文中，其频率与单组次数的边界另列pending，不转述为任何十次必不超过一次失误的保证。")
    add("independent-product-example", "在三个程序互相独立、各失效率为30%、40%、30%的假设例子中，作者按乘法将程序组失效率写为3.6%。", ["独立系统", "概率原则", "乘法原则"], ["p0023-b002"], ["三个程序互相独立", "本课作者给出的30%、40%、30%假设例子"], 1, "这是原文明说的建模例子，不声称真实程序独立性或真实组合失效率已获验证；不得改为100次必少于4次的次数保证。")
    add("indicators-share-price-volume-input", "作者认为技术指标都由价量输入而来，不能将多个技术指标视为互相独立程序，举例时只选一个技术指标构成买卖程序。", ["独立系统", "技术分析", "指标对比"], ["p0023-b003", "p0023-b004"], ["本课设计独立程序组的论述"], 1, "保留作者关于输入相关的判断；不称项目已对所有指标作独立性统计检验。")
    add("experienced-chart-over-indicators", "对较有经验者，作者认为带均线和成交量的K线图比单独技术指标更有意义。", ["K线", "均线", "指标对比", "操作熟练程度"], ["p0023-b003"], ["作者所指水平较高的操作者"], 3, "经验建议保留对象，不扩大成禁用所有指标。")
    add("relative-prices-and-fund-flow", "作者提出股票处于市场整体比价关系中，比价变化可构成买卖系统；该系统与市场资金流向相关，其他资金相关系统不能直接视为独立于它。", ["比价关系", "主力资金", "独立系统"], ["p0023-b003"], ["本课市场比价系统与独立程序组设计"], 2, "这里的比价关系不自动等同于当日热点，另有作者直接答疑。")
    add("fundamentals-participant-behavior", "作者所说基本面筛选不只看公司盈利，还包括参与者利益和人性所形成的行为约束；文中以发行价与认沽兑现动机作例。", ["基本面", "市场心理", "独立系统"], ["p0023-b003"], ["本课对基本面含义的作者说明"], 2, "发行价和权证例子保留为作者当时行为判断，不保证相关方必按其动机行动。")
    add("group-design-not-fixed-three", "作者说技术、比价、基本面三类只是随手举例，读者可自行设计交易程序组，但组内所用程序必须互相独立；人气与资金面、多个相关技术指标不能仅换名称就充当独立程序。", ["独立系统", "操作策略", "概率原则"], ["p0023-b004"], ["本课独立交易程序组设计原则"], 1, "不把随手三类固定为唯一系统构成，也不据该句声称任意程序组合必有效。")
    add("learn-method-not-stock-tip", "作者要求读其文章时学习和吃透方法、具备自己的分析能力，而非只索取具体股票。", ["操作熟练程度", "操作策略"], ["p0023-b005", "p0024-b000"], ["作者对文章学习目的的说明"], 3, "武钢权证涨幅留作历史例子，不作为方法必获该收益证据。")
    add("case-bank-flag-and-rotation", "在当时牛市叙述中，作者把银行股视为市场旗帜，认为银行暂不动时其他股票可轮动，银行真正见顶则市场也需警惕。", ["板块轮动", "牛市阶段", "市场风险"], ["p0024-b001"], ["2006年11月当时牛市和银行股案例"], 4, "保留历史语境，不推广为所有时期银行股决定所有市场。")
    add("case-gap-exhaustion-bull-trap", "2006年11月23日解盘中，作者在1923—1925突破缺口、1972—1977中继缺口的具体背景下，提出若出现多头陷阱及衰竭性缺口应警惕调整。", ["缺口", "调整", "市场风险"], ["p0024-b003", "p0024-b004"], ["2006-11-23当时指数和两个缺口", "多头陷阱与衰竭性缺口是假设路径"], 4, "原文极大可能不改为无条件确定预测。", ["p0025-fig1"])
    add("case-index-divergence-volume", "在当时解盘中，作者以深成指与沪指背离、成交量萎缩提醒震荡及短线调整风险。", ["指数走势背离", "调整", "市场风险"], ["p0024-b005", "p0025-b000"], ["2006-11-23沪深指数具体走势", "盘中2点以后是否改变是当时条件"], 4, "指数背离不合并为严格背驰；不作跨市场实测规则。", ["p0025-fig1"])
    add("case-intraday-shake-versus-adjustment", "作者在该次解盘中区分盘中震荡与调整，并称当时即使最短线调整也至少会考验5天甚至10天线。", ["市场震荡", "调整", "均线"], ["p0025-b000"], ["2006-11-23短线市场解释", "5/10天线是本段所给观察尺度"], 3, "保留案例和至少措辞，不作为后续严格走势级别定义。")
    add("case-adjustment-rotation-opportunity", "作者在当时短线调整讨论中说，技术熟练者可利用调整寻找下一轮股票、换股或做差价，前期未动者也可能借调整启动。", ["板块轮动", "调整", "操作熟练程度"], ["p0024-b003", "p0024-b006", "p0025-b001"], ["2006-11-23当时板块轮动", "需相应短线技术"], 3, "不将机会描述改成无条件收益承诺。")
    add("case-unexpected-change-exit", "在N中工答疑中，作者称其15元多开盘买入、后来18或19元可退出；因情况意外而退出仍符合其基本原则，并要求避免追高以便意外时退出。", ["资金管理", "政策风险", "追高"], ["p0025-b006"], ["读者Nn提出的N中工历史情境", "价格及可退出性是作者当时陈述"], 4, "问题已按原页修正为reader；不把事后可退出的历史陈述当任何实际订单已获执行。")
    add("case-warrant-floor-not-required-entry", "针对认沽行权价Y与认购行权价X的提问，作者答不一定等认购权证跌至Y−X区间才介入，可在底线之上观察；其武钢例子给出0.21元底线和0.35元底部。", ["认购权证", "基本面", "市场风险"], ["p0026-b001"], ["紧邻读者Y/X行权价假设与当时武钢案例", "底线依作者关于相关方行为的假设，不是无风险承诺"], 3, "作者并未逐字认可读者全部假设为法律或套利必然；30%风险/300%利润未由本项目计算或验证，不当保证。", ["p0024-fig1"])
    add("case-midway-warrant-volume-exit", "对读者当时中途介入的580003、580002，作者提醒位置风险，若二次上涨要寻找退出时机，并将放巨量作为该权证情境的观察点。", ["认购权证", "市场风险", "成交量"], ["p0026-b004"], ["2006-11-22读者中途介入的权证案例", "再次上涨/二次上涨的条件"], 3, "不把任意放量写成所有证券的普遍卖点；成交量不等同于放量突破。")
    add("relative-price-not-current-hotspot", "作者明确比价系统不是当下热点，而是市场个股间比价的整体结构；把握它需要理解市场总体结构，重点看比价关系的变动。", ["比价关系", "板块轮动"], ["p0026-b009"], ["对第9课第二类程序的直接答疑"], 2, "保留否定读者热点等同的回答。")
    add("analyze-news-not-follow-it", "作者要求主动分析消息、使用消息，不瞎听消息或被消息驱使。", ["公开信息", "操作策略"], ["p0026-b010"], ["本课针对普通投资者消息来源的答疑"], 3, "不补作者未给的消息评分算法。")
    add("case-year-average-retest-and-index", "在600649原水答疑中，作者以刚上年线、回试年线不破为介入条件，同时要求注意大盘短线调整；逆大盘启动与跟随大盘的力度判断分别保留。", ["均线", "调整", "市场风险"], ["p0026-b013"], ["2006-11-23原水600649案例", "回试年线不破", "需结合当时大盘调整"], 4, "不泛化为所有年线回试必买。")
    add("case-triangle-false-line-joint-pattern", "比较600685与600220所举区间时，作者认为后者有三角形整理最后骗线、前者没有；并反对第一波太强且其后调整时间太长的联合形态，认为容易充满骗线。", ["三角形整理", "假突破", "调整"], ["p0027-b001"], ["酸辣粉所问600685的9.19—9.27与600220的9.14—9.21比较", "第一波太强与随后调整太长为联合特征"], 3, "读者的均线粘合及一般化结论不作作者证据；原文‘重来’不替换源码。")
    add("case-midterm-top-not-one-day", "针对当时放量滞涨与大阴线提问，作者区分短线顶和中线顶，称中线筑顶需要时间；上升途中大阴线与筑顶后大阴线在该论述中不能混同。", ["顶", "操作级别", "调整"], ["p0027-b004"], ["2006-11-23对沪市当时量价问题的回复"], 3, "保留作者关于上升途中反扑的当时观点，不给任意大阴线添加确定反弹交易指令。")
    add("avoid-rebound-after-heavy-volume-top", "作者在青海明胶持仓答疑中强调，不要在巨量大阴线构造顶部后的下跌反抽中介入；对该读者是否如此买入仅作‘大概’判断。", ["反抽", "顶", "市场风险"], ["p0027-b007"], ["巨量大阴线构顶后的下跌反抽这一联合状态"], 2, "不删‘大概’，不把随后中线解套预期当保证。")
    add("case-chasing-and-missed-opportunity", "对读者中国嘉陵持仓，作者仅推测可能追高，并重申错过上涨可以视作该股不存在，不应因上涨而追买。", ["追高", "市场心理"], ["p0027-b008"], ["2006-11-23该读者中国嘉陵案例"], 3, "其他课已有一般不要追高；本条保存具体回复、推测语气及错过机会的处理，不重复造无条件总规则。")

    pending = [
        {"id": "upper-l009-pending-product-frequency", "passage_ids": [PREFIX + "p0023-b001", PREFIX + "p0023-b002"], "status": "pending", "issue": "作者给10%/十次最多一次和3.6%/100次不到4次的次数说法，未给真实测试或程序组失败事件定义；不把概率例子当任意有限次数的确定保证。"},
        {"id": "upper-l009-pending-empirical-independence", "passage_ids": [PREFIX + "p0023-b003", PREFIX + "p0023-b004"], "status": "pending", "issue": "本课列设计方向但没有这三类真实程序相互独立的统计检验，也未给程序实现；不可将设计例子当已经验证的组合绩效。"},
        {"id": "upper-l009-pending-warrant-floor-proof", "passage_ids": [PREFIX + "p0026-b001"], "status": "pending", "issue": "底线依相关方动机和历史条款；固定底本本段未独立证明无风险兑现或给30%/300%的完整计算口径。作者说法已保留，不扩成套利保证。"},
        {"id": "upper-l009-pending-original-figure-origins", "passage_ids": [], "figure_ids": [PREFIX + "p0024-fig1", PREFIX + "p0025-fig1"], "status": "pending", "issue": "第9课两图实际查看，制作人及原博客图源未核；PDF22图属第8课且已经later_annotation，不误纳为9课原图。"},
    ]
    by_passage = {}
    for r in records:
        for e in r["evidence"]:
            by_passage.setdefault(e["passage_id"], []).append(r["id"])
    ledger = []
    for pid, p in ps.items():
        links = by_passage.get(pid, [])
        issues = [x["id"] for x in pending if pid in x["passage_ids"]]
        if links:
            result, reason = "new_claim", "正文方法、限定或历史案例见关联原子命题；原句修辞/收益语气不改为保证"
        elif p["role"] in ("reader", "unknown"):
            result, reason = "context_or_unknown", "读者提问、署名或栏目头，保留为作者回答上下文；不直接支持作者命题"
        else:
            result, reason = "transition_or_context", "课程标题、作者署名时间头、分隔、简短复习提示或已由相邻完整回答覆盖的过渡"
        ledger.append({"passage_id": pid, "lesson_number": 9, "role": p["role"], "speaker": p["speaker"], "published_at": p["published_at"], "source_text_sha256": hashlib.sha256(p["text"].encode()).hexdigest(), "result": result, "claim_ids": links, "pending_issue_ids": issues, "reason": reason, "rounds": {"1_read_and_scope": "顺序通读本课及问题上下文，回看PDF22至27确认读者/作者边界和跨页时间", "2_atomic_conditions": "将程序定义、失效率假设、联合条件和案例参数分开；保留失败与退出限制", "3_normalization": "与当前533条reviewed比较；复用独立系统/概率原则等，历史同词不自动合并规则", "4_reverse_check": "逐条核对原文语气、量词、图源和例子边界；具体结果见claim_ids及pending_issue_ids"}})
    figures = [dict(r) for r in db.execute("SELECT id,pdf_page,origin_status,note FROM figures WHERE document_id=? AND pdf_page IN (24,25) ORDER BY id", (PREFIX[:-1],))]
    for f in figures:
        f.update(visual_review_complete=True, reviewer=REVIEWER, origin_status_changed=False, semantic_scope="只对应作者旁文历史案例，制作身份未核")
    for suffix, rows in [("reviewed.jsonl", records), ("coverage.jsonl", ledger), ("pending.jsonl", pending), ("figures.jsonl", figures)]:
        (HERE / (BATCH + "." + suffix)).write_text("\n".join(j(x) for x in rows) + "\n", encoding="utf-8")
    summary = {"stage": "C", "schema_version": "1.1.0", "graph_version": version, "reviewer": REVIEWER, "lesson_number": 9, "document_id": PREFIX[:-1], "passages_read": len(ps), "claims": len(records), "evidence": sum(len(r["evidence"]) for r in records), "importance_counts": dict(Counter(r["importance_level"] for r in records)), "new_concepts": sorted({label for r in records for label in r["concepts"]} - old_concepts), "whole_lesson_semantic_read_complete": True, "technical_extraction_complete": False, "four_round_review": True, "independent_review_claimed": False, "visual_pdf_pages": list(range(22, 28)), "figure_objects_viewed": 2, "pending": [r["id"] for r in pending], "database_mode": "ro", "formal_import": False, "acceptance": "全部59段完成四轮审读；程序失效率的模型/次数边界及图源等4项继续待核，合格命题待统一发布。"}
    (HERE / (BATCH + ".summary.json")).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    db.close()
    print(j(summary))


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    build()
