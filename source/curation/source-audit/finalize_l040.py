"""Save verified lesson40 publication and the lesson41 continuation point."""
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2]
KB = AGENT.parent / 'shared-knowledge/v0.1.0'
AUDIT = Path(__file__).resolve().parent
VERSION = '0.1.0-review-202e84864e97'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
    try:
        metadata = {k: json.loads(v) for k, v in db.execute('SELECT key,value FROM metadata')}
        assert metadata['graph_version'] == VERSION
        counts = {t: db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
                  for t in ['documents', 'pages', 'units', 'passages', 'figures', 'concepts', 'claims', 'evidence', 'relations', 'reviews']}
        assert counts == dict(documents=2, pages=907, units=110, passages=9647, figures=528,
                              concepts=278, claims=5223, evidence=6250, relations=454, reviews=2654)
        claim_status = db.execute('SELECT review_status,COUNT(*) FROM claims GROUP BY review_status ORDER BY review_status').fetchall()
        figure_status = db.execute('SELECT origin_status,COUNT(*) FROM figures GROUP BY origin_status ORDER BY origin_status').fetchall()
        unit_status = db.execute('SELECT processing_status,COUNT(*) FROM units GROUP BY processing_status ORDER BY processing_status').fetchall()
        assert dict(claim_status) == {'pending': 2612, 'rejected': 27, 'reviewed': 2584}
        assert dict(unit_status)['extracted'] == 21
        assert db.execute("SELECT COUNT(*) FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed'").fetchone()[0] == 3611
        next_row = db.execute("SELECT id,pdf_page,text FROM passages WHERE unit_id='lesson-041' ORDER BY pdf_page,block_index,id LIMIT 1").fetchone()
        assert next_row and next_row[2].startswith('教你炒股票41')
        next_anchor = next_row[0] + ' / lesson-041'
        known = {r[0] for r in db.execute("SELECT id FROM claims WHERE review_status='reviewed'")}
    finally:
        db.close()
    assert read(KB / 'manifest.json')['graph_version'] == VERSION
    exports = {}
    for name, number in [('claims', 2584), ('concepts', 278), ('relations', 454)]:
        path = KB / 'exports' / f'{name}.jsonl'
        rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
        assert len(rows) == number and all(r['graph_version'] == VERSION for r in rows)
        exports[name] = {'rows': number, 'graph_version': VERSION, 'sha256': sha(path)}
    assert VERSION in (KB / 'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150]
    assert read(KB / 'exports/coverage.json')['graph_version'] == VERSION
    inv = read(AUDIT / 'stage-c-l040-source-invariants.json')
    assert inv['pass'] and inv['graph_version'] == VERSION
    assert inv['original_reviewed_claims_unchanged'] == 2550 and inv['original_reviewed_evidence_unchanged'] == 3572
    verification = read(AUDIT / 'stage-c-l040-verification.json')
    assert verification['pass'] and verification['graph_version'] == VERSION
    assert len(verification['checks']) == 6 and len(verification['parity']) == 7
    assert verification['intended_figure_links_checked'] == dict(claims=7, associations=12, unique_figures=7)
    dev = read(AGENT / 'evaluation/stage-g-development-current.results.json')
    assert dev['graph_version'] == VERSION and dev['executable_development_cases'] == dev['retrieval_plan_contract_passed'] == 240
    assert all(r['source_identity_matches_expected'] for r in dev['observations'])
    pending_ids = set()
    for n in [34, 35, 37, 38, 39]:
        pending_ids.update(json.loads(line)['id'] for line in (AGENT / 'curation/upper' / f'c_stage_l{n:03d}.pending.jsonl').read_text(encoding='utf-8').splitlines() if line.strip())
    changes = [
        ('upper-l039-c-stage-pending-Ai-pair-parity-protection-delay-k-and-unique-history',
         ['Ai-divergence-next-protection-break-forms-higher-center', 'A0-through-At-equals-B1-B2-thirty-decomposition-switch', 'N-layer-fugue-each-capital-shares-rhythm'],
         '40给Ai盘背后保护位演化次高中心并可换档，再组合N层；39未盘背延后支、k奇支与相等/完成/成交细节仍未全，不以高层机会改旧切分。'),
        ('upper-l038-c-stage-pending-mechanical-branches-completion-equality-execution-and-profit',
         ['small-entry-large-rise-keep-small-or-upgrade-partial-small', 'A0-through-At-equals-B1-B2-thirty-decomposition-switch', 'switch-discretion-time-style-capital-larger-wave-benefit-view'],
         '40允许当下形成高层分解后择时换档，依时间风格资金而非套牢改口；仍无完整B2完成/EPS和实盘收益证明，稳定利益为作者预期。'),
        ('upper-l037-c-stage-pending-consolidation-divergence-comparable-force-and-trend-end',
         ['standard-divergence-two-small-trends-inside-trend', 'divergence-method-extension-even-same-direction-center-waves'],
         '40明确最标准为趋势内两小趋势比较，震荡同向波可类似推广；读者A>B等问未逐项证，37条件与c内部相对层级仍保留，不自动消除全部张力。'),
        ('upper-l034-c-stage-pending-area-versus-peak-and-center-formed-state',
         ['non-MACD-moving-average-area-alternative', 'subminute-case-one-minute-green-area-two-sum-versus-one', 'morning-five-top-sell-rhythm-before-bottom-precision'],
         '40给均线长短面积替代及具体1分以下借1分柱面积例，前两和比后一；原未给周期/积分区间或单一充分公式，不改34原记号和对象。'),
        ('upper-l035-c-stage-pending-operation-level-cost-regime-and-zero-risk-claim',
         ['mar29-zero-cost-safe-negative-only-profit-author-strong-wording', 'fund-weakness-vs-stable-long-no-cashout-author-view'],
         '40重申0成本安全/负成本才利润并给稳定长期无套现压力观点；仍不认证现金成本等于全部经济风险或全部基金同类清盘机制，旧风险范围不抹。'),
        ('upper-l039-c-stage-pending-entry-batches-direction-Tplus1-and-sell-all-buy-source',
         ['any-underwater-not-buy-point-author-claim-tension', 'underwater-stock-first-identify-divergence-level', 'five-day-trim-versus-long-term-fundamental-valuation'],
         '40被套非买点与39非最低总有被套范围未明，另要求先认级别及技术减仓/真长线基本面分境；不改39原字、不用事后浮亏判点真伪，也未消T+1风险。'),
        ('upper-l038-c-stage-pending-same-level-unique-rule-not-global-unique-or-formal-proof',
         ['A0-through-At-equals-B1-B2-thirty-decomposition-switch', 'each-layer-independent-and-integrated-own-level-rhythm'],
         '40多层各守自身分解、B1+B2成立可换高级，与固定规则内唯一不同作用域；未给所有分解全局唯一或无相关风险的形式证明。'),
    ]
    followups = []
    for pending_id, slugs, finding in changes:
        ids = ['upper-l040-c-stage-' + slug for slug in slugs]
        assert pending_id in pending_ids and all(id in known for id in ids)
        followups.append({'pending_id': pending_id, 'status': 'new_source_located_scope_still_pending',
                          'new_claim_ids': ids, 'finding': finding, 'global_pending_not_closed': True, 'graph_version': VERSION})
    (AGENT / 'curation/upper/c_stage_l040.partial-resolutions.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n' for r in followups), encoding='utf-8')
    checks = [
        '34条JSON Schema及引用/身份/映射/坐标预检',
        '125段原文哈希及全段台账一致，实际PDF291至301共11页7完整图及后课边界视觉核对',
        '原2550命题3572已复核证据未改，9647段528图逐行比较仅11跨时段来源日期与7图来源备注授权变更',
        '33项当前工作区Node测试通过（原有27项及另行验收的检索评测6项）',
        '2584条已复核命题全量引用校验0错误',
        '6组来源/条件边界及7组CLI/公共/桌面模块一致，7命题12配图关联逐项确认，只读哈希不变',
        '240/240冻结开发取证计划和已标注来源身份回归通过，无新题替换',
        '2584命题/278概念/454关系JSONL及Markdown/coverage同版本导出',
        '7条旧待核补充关联，原问题全部保持开放',
    ]
    not_run = ['240题完整类别/自然问题基线/生成回答评分/消融对抗验收未完成；开发取证计划通过不能代替',
               '41至61共21课完整语义及全书跨课/图文审查未完成',
               '独立Agent打包后运行及Windows真实离线/缩放旋转跨页交互未验收']
    acceptance = '40课34条39证据、11日期与7图来源已发布；2584引用/240冻结开发题回归通过；8待核及全书/产品目标未完成。'
    next_action = f'接续上册41课，实际PDF{next_row[1]}页标题；完整阅读市场节奏、买卖点/多层风险与解盘答疑，核对当下条件、作者修辞和原图。'
    evaluation = {'executable_development_cases': 240, 'target': 240, 'gold_review_status': 'model_reviewed_development',
                  'human_gold_reviewed': False, 'independent_test_set': False, 'generated_answers_scored': False,
                  'retrieval_plan_and_source_identity_passed_on_current_graph': 240, 'full_stage_g_acceptance_complete': False,
                  'new_project_gold_cases_created_in_this_batch': 0,
                  'note': '冻结开发取证计划及本批边界检查通过，不证明完整G、独立金标准或实际桌面交互通过。'}
    path = AUDIT / 'stage-c-l040-publication.json'; pub = read(path)
    assert pub['graph_version'] == VERSION and pub['formal_import'] == 'passed'
    assert list(pub['batch_sha256'].values()) == [sha(AGENT / 'curation/upper/c_stage_l040.reviewed.jsonl')]
    pub.update(updated_at=datetime.now(timezone.utc).isoformat(), checks_run=checks, checks_not_run=not_run,
               acceptance=acceptance, next_action=next_action, exports=exports,
               final_sha256={'database': sha(KB / 'graph.sqlite'), 'manifest': sha(KB / 'manifest.json')},
               development_evaluation=evaluation, partial_pending_followups=7, semantic_completion=False,
               writes_to_knowledge_graph_by_this_finalizer=False)
    write(path, pub)
    path = AGENT / 'curation/progress.json'; progress = read(path)
    assert progress['graph_version'] in ['0.1.0-review-01407b1617c1', VERSION]
    if progress['graph_version'] != VERSION:
        progress['previous_checkpoint'] = {key: progress[key] for key in ['graph_version', 'completed', 'next_action', 'evaluation']}
    outputs = ['source-audit/stage-c-l040-' + name + '.json' for name in ['source-plan', 'source-applied', 'source-invariants', 'publication', 'verification']]
    progress['machine_outputs'] = list(dict.fromkeys(progress['machine_outputs'] + outputs + ['upper/c_stage_l040.partial-resolutions.jsonl']))
    progress.update(updated_at=datetime.now(timezone.utc).isoformat(), graph_version=VERSION, counts=counts,
                    claim_status_counts=claim_status, figure_origin_counts=figure_status, unit_processing_status_counts=unit_status,
                    semantic_completion=False, completed=[
                        '上册40课125段11页7图同模型四轮审读，34命题39证据12关系支撑发布，新增多重赋格操作/时间之窗2概念',
                        '11来源段按3/27 21:29、3/28 15:24、3/29 21:44分组，午间前段和尾头字符不改；7图3后加4原发未核，选择栏旧日期不掩后K',
                        '原2550命题3572证据及全源原文/字符映射/坐标逐行未改；Ai盘背后次高中心、A0至At重分B1+B2才可换档，非小级套牢改中线，N层各自筹码节奏非无相关风险',
                        '均线长短面积另一路无完整参数/积分，1分以下借1分MACD两绿面积和比一案例，不升5分；先卖节奏优先有已识别顶背前提，000802股例不挂指数图；8待核',
                        '17/24/37引文保留读者身份，作者最标准两小趋势与震荡方法推广分开；被套非买点与39总有被套张力、成本0安全/负成本利润与无人能胜强词均未实证',
                        '7段货币评论完整保留非技术上下文，未名基金/机构与订单自述不认证；20%/金额读者条件非通用配置，技术5日减仓与真长线基本面分情境',
                        '2584命题/278概念/454关系同版本导出；33工程/2584引用、6边界和7组CLI/公共/桌面模块一致，7命题12配图关联逐项通过',
                        '240冻结开发取证计划与已标注身份回归通过，不增题凑数；7条旧待核补充均开放，余21课',
                    ], pending=[
                        '本批8待核见upper/c_stage_l040.pending.jsonl：多层换档/分仓、均线柱面积辅助、标准背驰/推广、时间窗/天数、被套/零成本强词张力、基金机构/附文、节奏时点/长线基本面、日期/图源',
                        '41至61共21课未完整语义审读；87课有阅读记录含历史62至64，不等全书技术抽取或全部解释统一',
                        '240题完整类别、自然问题基线、生成回答评分、消融对抗与全书跨课/图文审查未完成',
                        '独立Agent实际交付运行及Windows真实离线/缩放旋转跨页交互未验收',
                    ], checks_run=checks, checks_not_run=not_run, acceptance=acceptance,
                    next_resume_anchor=next_anchor, next_action=next_action,
                    coverage_caveat='40课125段11页7图同模型四轮，累计87课阅读记录含历史62至64，不称独立复核或全书完成。',
                    evaluation=evaluation,
                    previous_turn_classification='progress：40课125段7图、11日期修正与34条39证据发布；2584引用/240冻结开发题回归通过，余21课。')
    write(path, progress)
    print(json.dumps({'graph_version': VERSION, 'reviewed': 2584, 'development_cases': 240,
                      'remaining_lessons': 21, 'next_anchor': next_anchor, 'semantic_completion': False}, ensure_ascii=False))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
