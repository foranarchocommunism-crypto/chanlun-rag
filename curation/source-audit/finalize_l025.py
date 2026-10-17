"""Verify exports, preserve open questions, and save the lesson26 resume point."""
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2]
KB = AGENT.parent / 'shared-knowledge/v0.1.0'
VERSION = '0.1.0-review-c03707cf7b67'
AUDIT = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


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
                              concepts=243, claims=4654, evidence=5570, relations=302, reviews=2078)
        claim_status = db.execute('SELECT review_status,COUNT(*) FROM claims GROUP BY review_status ORDER BY review_status').fetchall()
        figure_status = db.execute('SELECT origin_status,COUNT(*) FROM figures GROUP BY origin_status ORDER BY origin_status').fetchall()
        unit_status = db.execute('SELECT processing_status,COUNT(*) FROM units GROUP BY processing_status ORDER BY processing_status').fetchall()
        assert dict(claim_status) == {'pending': 2614, 'rejected': 25, 'reviewed': 2015}
        assert dict(unit_status)['extracted'] == 36
        assert db.execute('SELECT unit_id FROM passages WHERE id=?', ('volume_1-a53e99c37ca5-p0166-b005',)).fetchone() == ('lesson-026',)
        known_claims = {r[0] for r in db.execute("SELECT id FROM claims WHERE review_status='reviewed'")}
    finally:
        db.close()
    assert read(KB / 'manifest.json')['graph_version'] == VERSION
    exports = {}
    for name, expected in [('claims', 2015), ('concepts', 243), ('relations', 302)]:
        path = KB / 'exports' / f'{name}.jsonl'
        rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
        assert len(rows) == expected and all(row['graph_version'] == VERSION for row in rows)
        exports[name] = {'rows': len(rows), 'graph_version': VERSION, 'sha256': sha(path)}
    assert VERSION in (KB / 'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150]
    assert read(KB / 'exports/coverage.json')['graph_version'] == VERSION
    inv = read(AUDIT / 'stage-c-l025-source-invariants.json')
    assert inv['pass'] and inv['graph_version'] == VERSION
    assert inv['original_reviewed_claims_unchanged'] == 1965 and inv['original_reviewed_evidence_unchanged'] == 2856
    verification = read(AUDIT / 'stage-c-l025-verification.json')
    assert verification['graph_version'] == VERSION and verification['pass']
    assert len(verification['checks']) == 6 and len(verification['parity']) == 7
    dev = read(AGENT / 'evaluation/stage-g-development-current.results.json')
    assert dev['graph_version'] == VERSION and dev['executable_development_cases'] == dev['retrieval_plan_contract_passed'] == 240
    assert all(row['source_identity_matches_expected'] for row in dev['observations'])

    followups = [
        ('upper-l013-l014-c-stage-pending-macd-double-period-and-example-comparison',
         ['macd-usual-parameters-and-ultrafast-limit'],
         '25明确一般参数12/26/9，不能由此推定14“长一倍”的具体变换；原待核不关闭。'),
        ('upper-l015-l016-c-stage-pending-macd-histogram-peaks-lines-and-law',
         ['rapid-one-minute-height-exception-600779', 'limit-up-sine-indicator-not-divergence', 'shrinking-bars-not-divergence-combined-conditions'],
         '25明确急速1分只看柱高的特殊警告、一字涨停指标弱点与普通柱缩不充分，不能把前课柱波条件推广所有行情。'),
        ('upper-l015-l016-c-stage-pending-ma-force-area-average-and-instant-boundaries',
         ['kiss-average-and-macd-auxiliary-not-center', 'usual-two-center-final-lines-or-area-or-height'],
         '25明确辅助系统与中枢不同；常见MACD线/面积/高度或项仍不提供15均线间面积完整数值算法。'),
        ('upper-l015-l016-c-stage-pending-warrant-trades-zero-cost-gap-cycle',
         ['imminent-suspension-risk-no-time-to-correct'],
         '25对580994另有临停没时间纠错的明确风险边界，支持保留权证风险，不核实038004账户、自述成本或时间周期。'),
        ('lower-l101-l102-c-stage-pending-second-buy-three-forms-and-loose-name',
         ['first-second-third-price-order-original-claim', 'jan26-first-second-buy-and-lowest-third-difficult'],
         '25保留未加一般限定的价序原话与当日1分实例；101后有二买低于一买的明确分支，新增前史但不自动宣布修订或全书统一。'),
    ]
    pending_ids = set()
    for name in ['upper/c_stage_l013_l014.pending.jsonl', 'upper/c_stage_l015_l016.pending.jsonl', 'lower/c_stage_l101_l102.pending.jsonl']:
        for line in (AGENT / 'curation' / name).read_text(encoding='utf-8').splitlines():
            if line.strip():
                pending_ids.add(json.loads(line)['id'])
    followup_rows = []
    for pending_id, slugs, finding in followups:
        ids = ['upper-l025-c-stage-' + slug for slug in slugs]
        assert pending_id in pending_ids and all(id in known_claims for id in ids)
        followup_rows.append({'pending_id': pending_id, 'status': 'new_source_located_scope_still_pending',
                              'new_claim_ids': ids, 'finding': finding, 'global_pending_not_closed': True, 'graph_version': VERSION})
    path = AGENT / 'curation/upper/c_stage_l025.partial-resolutions.jsonl'
    path.write_text(''.join(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n' for row in followup_rows), encoding='utf-8')
    checks = [
        '50条JSON Schema及引用/身份/映射/坐标预检',
        '272段原文哈希及全段台账一致；23页13本课图与144前课图边界实际视觉检查',
        '原1965命题2856已复核证据未改，9647段528图仅19段13图授权元数据变更，2误归读者候选拒绝',
        '当前工作区33项Node工程测试通过（原有27项和新增检索评测6项，后者另行验收）',
        '2015条已复核命题全量引用校验0错误',
        '6组边界断言及7组CLI/公共/桌面模块一致，只读检查哈希不变',
        '240/240冻结开发题原取证计划与已标注来源身份在当前图谱通过；未以新题替换失败题',
        '2015命题/243概念/302关系JSONL及Markdown/coverage同版本导出',
        '5条旧待核补充关联保留原待核开放状态',
    ]
    not_run = [
        '240题完整验收尚未完成；现有240道同模型开发取证计划不等完整类别覆盖、自然问题基线或生成回答评分',
        '26至61共36课完整语义审读及全书跨课/图文统一审查未完成',
        '独立Agent打包后运行及Electron Windows真实离线/缩放旋转跨页交互验收未完成',
    ]
    acceptance = '第25课50条75证据、19段来源修正和13图来源复核已发布；2015引用/240开发取证计划通过；8待核及全书/产品验收未完成。'
    next_action = '接续上册26课，从实际PDF166页26课标题开始；核对可交易时间/停牌风险、走势风险与操作风格及作者问答，逐段核查身份和原图。'
    evaluation = {'executable_development_cases': 240, 'target': 240, 'gold_review_status': 'model_reviewed_development',
                  'human_gold_reviewed': False, 'independent_test_set': False, 'generated_answers_scored': False,
                  'retrieval_plan_and_source_identity_passed_on_current_graph': 240, 'full_stage_g_acceptance_complete': False,
                  'new_project_gold_cases_created_in_this_batch': 0,
                  'note': '本批运行冻结240题回归及单独来源边界检查；全项目题型分布和G3/G4/G5/G6仍需专门核验。'}
    path = AUDIT / 'stage-c-l025-publication.json'
    pub = read(path)
    assert pub['graph_version'] == VERSION and pub['formal_import'] == 'passed'
    pub.update(updated_at=datetime.now(timezone.utc).isoformat(), checks_run=checks, checks_not_run=not_run,
               acceptance=acceptance, next_action=next_action, exports=exports,
               final_sha256={'database': sha(KB / 'graph.sqlite'), 'manifest': sha(KB / 'manifest.json')},
               development_evaluation=evaluation, partial_pending_followups=len(followup_rows), semantic_completion=False,
               validation_execution_note='并行首次旧开发题回归遇database is locked；全量引用检查结束后串行原样重跑240/240通过，未改断言、金标准或查询计划。',
               writes_to_knowledge_graph_by_this_finalizer=False)
    write(path, pub)

    path = AGENT / 'curation/progress.json'
    progress = read(path)
    assert progress['graph_version'] in ['0.1.0-review-a38ea0d31c7c', VERSION]
    if progress['graph_version'] != VERSION:
        progress['previous_checkpoint'] = {key: progress[key] for key in ['graph_version', 'completed', 'next_action', 'evaluation']}
    outputs = ['source-audit/stage-c-l025-' + name + '.json' for name in ['source-plan', 'source-applied', 'source-invariants', 'publication', 'verification']]
    outputs += ['upper/c_stage_l025.partial-resolutions.jsonl']
    progress['machine_outputs'] = list(dict.fromkeys(progress['machine_outputs'] + outputs))
    progress.update(updated_at=datetime.now(timezone.utc).isoformat(), graph_version=VERSION,
                    counts=counts, claim_status_counts=claim_status, figure_origin_counts=figure_status,
                    unit_processing_status_counts=unit_status, semantic_completion=False,
                    completed=[
                        '上册25课272段23页13本课图及144前课边界同模型四轮审读，50命题75证据11关系支撑发布，新增T+0/乖离极限/停牌风险/双次拉回/机动资金5概念',
                        '19段身份时间修正，赚到了/天山飞狐提问、151两条未署名读者后作者解盘、156晚间和161嵌29日头分开；2误归候选拒绝',
                        '13本课图8后加5原发未核；153尾括注署名不明保留待核，作者证据精确排除此尾注；原文和坐标不改',
                        '原1965命题2856证据与全源逐行不变检查通过；辅助工具/中枢、急速柱高/一字涨停、外围触及/回拉级别及递归/实用三K提示分开',
                        '25未限定价序与101二买可更低同存；机动资金1/4至1/3或1/2、牛市/快速行情/小资金条件和临停纠错风险保留；8待核',
                        '2015命题/243概念/302关系同版本导出，33工作区工程/2015引用通过；6组边界与7组CLI/公共/桌面模块一致',
                        '240冻结开发取证计划和来源身份串行回归通过；首次并行database locked已记录，未改题/断言；本批不增题凑数',
                        '5条旧待核补充记录已关联且均开放，余26至61共36课',
                    ], pending=[
                        '本批8待核见upper/c_stage_l025.pending.jsonl：辅助体系与参数、急速/涨停、级别/递归/实用法、价序与最低级三类点、确认/双次回拉、混合身份、历史数值/预测修辞、配图来源',
                        '26至61共36课未完整语义审读；72课已有阅读记录含历史62至64，不代表全书技术抽取或全部解释统一',
                        '240题完整类别、自然问题基线、生成回答评分、消融对抗及全书跨课/图文审查未完成',
                        '独立Agent实际交付运行及Windows真实离线/缩放旋转跨页交互未验收',
                    ], checks_run=checks, checks_not_run=not_run, acceptance=acceptance,
                    next_resume_anchor='volume_1-a53e99c37ca5-p0166-b005 / lesson-026', next_action=next_action,
                    coverage_caveat='本批25课272段23页13本课图+1前课边界，累计72课阅读记录含历史62至64；同模型四轮，不称独立复核或全书完成。',
                    evaluation=evaluation,
                    previous_turn_classification='progress：第25课272段13图、19源修正及50条75证据正式发布；2015引用/240冻结开发题回归通过，余36课。')
    write(path, progress)
    print(json.dumps({'graph_version': VERSION, 'reviewed': 2015, 'development_cases': 240,
                      'partial_followups': len(followup_rows), 'remaining_lessons': 36, 'semantic_completion': False}, ensure_ascii=False))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
