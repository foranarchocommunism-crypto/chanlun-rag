"""Save verified lesson26 publication, open followups, and the lesson27 anchor."""
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2]
KB = AGENT.parent / 'shared-knowledge/v0.1.0'
AUDIT = Path(__file__).resolve().parent
VERSION = '0.1.0-review-31581ef72e83'


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
                              concepts=247, claims=4701, evidence=5637, relations=311, reviews=2125)
        claim_status = db.execute('SELECT review_status,COUNT(*) FROM claims GROUP BY review_status ORDER BY review_status').fetchall()
        figure_status = db.execute('SELECT origin_status,COUNT(*) FROM figures GROUP BY origin_status ORDER BY origin_status').fetchall()
        unit_status = db.execute('SELECT processing_status,COUNT(*) FROM units GROUP BY processing_status ORDER BY processing_status').fetchall()
        assert dict(claim_status) == {'pending': 2614, 'rejected': 25, 'reviewed': 2062}
        assert dict(unit_status)['extracted'] == 35
        assert db.execute('SELECT unit_id FROM passages WHERE id=?', ('volume_1-a53e99c37ca5-p0178-b006',)).fetchone() == ('lesson-027',)
        known = {r[0] for r in db.execute("SELECT id FROM claims WHERE review_status='reviewed'")}
    finally:
        db.close()
    assert read(KB / 'manifest.json')['graph_version'] == VERSION
    exports = {}
    for name, number in [('claims', 2062), ('concepts', 247), ('relations', 311)]:
        path = KB / 'exports' / f'{name}.jsonl'
        rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
        assert len(rows) == number and all(r['graph_version'] == VERSION for r in rows)
        exports[name] = {'rows': number, 'graph_version': VERSION, 'sha256': sha(path)}
    assert VERSION in (KB / 'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150]
    assert read(KB / 'exports/coverage.json')['graph_version'] == VERSION
    inv = read(AUDIT / 'stage-c-l026-source-invariants.json')
    assert inv['pass'] and inv['graph_version'] == VERSION
    assert inv['original_reviewed_claims_unchanged'] == 2015 and inv['original_reviewed_evidence_unchanged'] == 2931
    verification = read(AUDIT / 'stage-c-l026-verification.json')
    assert verification['pass'] and verification['graph_version'] == VERSION
    assert len(verification['checks']) == 6 and len(verification['parity']) == 7
    dev = read(AGENT / 'evaluation/stage-g-development-current.results.json')
    assert dev['graph_version'] == VERSION and dev['executable_development_cases'] == dev['retrieval_plan_contract_passed'] == 240
    assert all(r['source_identity_matches_expected'] for r in dev['observations'])

    pending_ids = set()
    for name in ['c_stage_l013_l014', 'c_stage_l015_l016', 'c_stage_l025']:
        pending_ids.update(json.loads(line)['id'] for line in (AGENT / 'curation/upper' / f'{name}.pending.jsonl').read_text(encoding='utf-8').splitlines() if line.strip())
    changes = [
        ('upper-l013-l014-c-stage-pending-active-protection-vs-old-lot-and-lump-topup',
         ['tcl-recovery-conditional-author-recap', 'long-selection-not-casual-cut-conditional', 'bull-no-light-cut-delisting-exception'],
         '26有TCL后评及牛市/中长线不轻斩仓、退市例外；与13买点失效防护和14一次补旧仓范围并列，未据晚文取消原规则。'),
        ('upper-l013-l014-c-stage-pending-success-profits-and-efficiency-claims',
         ['long-capital-plus-skill-unbeatable-author-formula', 'positive-cost-risk-and-negative-cost-ambition'],
         '26追加足够长的钱/熟练理论与负成本永不败的作者强主张，仍无独立收益样本，原概率和效益待核未解。'),
        ('upper-l015-l016-c-stage-pending-warrant-trades-zero-cost-gap-cycle',
         ['warrant-keep-original-size-no-added-position-self-report', 'sudden-stop-or-cancellation-invalidates-premise'],
         '26未具名认购负成本与交易终止边界是新材料，不猜同038004认沽，账户、自述收益与时间周期仍未核。'),
        ('upper-l025-c-stage-pending-case-time-prices-forecast-and-guarantees',
         ['foreseeable-trading-continuation-level-horizon', 'capital-deadline-self-imposed-trading-stop', 'ordinary-suspension-vs-permanent-stop-author-claim'],
         '26细化没时间纠错为交易延续/有效与自有资金期限，另列普通停牌；不补普适期限或认证所有风险可控。'),
        ('upper-l025-c-stage-pending-center-level-recursion-retest-and-practical-heuristic',
         ['chihong-center-jul27-aug26-no-average', 'shanghai-thirty-to-daily-weekly-centers-case', '600316-third-buy-needs-preceding-first-second'],
         '26再明确中枢与均线无关并有日周扩张及错误三买问答，仍不能仅凭图中框线或原文反问生成级别/邻接算法。'),
    ]
    followups = []
    for pending_id, slugs, finding in changes:
        ids = ['upper-l026-c-stage-' + slug for slug in slugs]
        assert pending_id in pending_ids and all(id in known for id in ids)
        followups.append({'pending_id': pending_id, 'status': 'new_source_located_scope_still_pending',
                          'new_claim_ids': ids, 'finding': finding, 'global_pending_not_closed': True, 'graph_version': VERSION})
    (AGENT / 'curation/upper/c_stage_l026.partial-resolutions.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n' for r in followups), encoding='utf-8')
    checks = [
        '47条JSON Schema及引用/身份/映射/坐标预检；关系端点漏登记持股已在预检阶段修正后通过',
        '141段原文哈希及全段台账一致，13页6图实际视觉核对',
        '原2015命题2931已复核证据未改，全部9647段528图仅6段日期及6图元数据授权变更',
        '33项当前工作区Node测试通过（原有27项及另行验收的检索评测6项）',
        '2062条已复核命题全量引用校验0错误',
        '6组来源/条件边界断言及7组CLI/公共/桌面模块一致，只读哈希不变',
        '240/240冻结开发取证计划和已标注来源身份回归通过；无新题替换',
        '2062命题/247概念/311关系JSONL及Markdown/coverage同版本导出',
        '5条旧待核有新增来源关联，原问题全部保持开放',
    ]
    not_run = [
        '240题完整类别/自然问题基线/生成回答评分/消融对抗验收未完成；开发取证计划通过不能代替',
        '27至61共35课完整语义及全书跨课/图文审查未完成',
        '独立Agent打包后运行及Windows真实离线/缩放旋转跨页交互未验收',
    ]
    acceptance = '第26课47条67证据、6段日期和6图来源已发布；2062引用/240冻结开发题回归通过；8待核及全书/产品目标未完成。'
    next_action = '接续上册27课，实际PDF178页标题；核对趋势背驰/盘整背驰、历史底部与级别条件，保留概率陈述、读者身份和原图来源。'
    evaluation = {'executable_development_cases': 240, 'target': 240, 'gold_review_status': 'model_reviewed_development',
                  'human_gold_reviewed': False, 'independent_test_set': False, 'generated_answers_scored': False,
                  'retrieval_plan_and_source_identity_passed_on_current_graph': 240, 'full_stage_g_acceptance_complete': False,
                  'new_project_gold_cases_created_in_this_batch': 0,
                  'note': '本批运行冻结240题回归和单独边界检查，不能据此宣称完整阶段G或桌面验收通过。'}
    path = AUDIT / 'stage-c-l026-publication.json'
    pub = read(path)
    assert pub['graph_version'] == VERSION and pub['formal_import'] == 'passed'
    pub.update(updated_at=datetime.now(timezone.utc).isoformat(), checks_run=checks, checks_not_run=not_run,
               acceptance=acceptance, next_action=next_action, exports=exports,
               final_sha256={'database': sha(KB / 'graph.sqlite'), 'manifest': sha(KB / 'manifest.json')},
               development_evaluation=evaluation, partial_pending_followups=5, semantic_completion=False,
               writes_to_knowledge_graph_by_this_finalizer=False)
    write(path, pub)
    path = AGENT / 'curation/progress.json'
    progress = read(path)
    assert progress['graph_version'] in ['0.1.0-review-c03707cf7b67', VERSION]
    if progress['graph_version'] != VERSION:
        progress['previous_checkpoint'] = {key: progress[key] for key in ['graph_version', 'completed', 'next_action', 'evaluation']}
    outputs = ['source-audit/stage-c-l026-' + name + '.json' for name in ['source-plan', 'source-applied', 'source-invariants', 'publication', 'verification']]
    progress['machine_outputs'] = list(dict.fromkeys(progress['machine_outputs'] + outputs + ['upper/c_stage_l026.partial-resolutions.jsonl']))
    progress.update(updated_at=datetime.now(timezone.utc).isoformat(), graph_version=VERSION, counts=counts,
                    claim_status_counts=claim_status, figure_origin_counts=figure_status, unit_processing_status_counts=unit_status,
                    semantic_completion=False, completed=[
                        '上册26课141段13页6图同模型四轮审读，47命题67证据9关系支撑发布，新增交易延续/交易有效性/资金期限/负成本4概念',
                        '173尾2/1日期头仅管后6段，旧1/31段仍保留；6图4文后2原发未核，原词周线中线/顺便斩仓和记者转载读者身份保留',
                        '原2015命题2931证据及全9647段528图原文/字符映射/坐标逐行检查未改，仅12项授权元数据变更',
                        '交易延续/算数、突然终止/取消、普通停牌和自有资金期限分开；负成本不当负报价，认购不猜认沽，永不败/10%/业绩均作者未核主张',
                        '大级别强弱/方向/指数一致、资金量/1/3或1/4、新手日线、连绵跌势、基本面/不轻斩仓/退市例外和旧防护规则范围保留；8待核',
                        '2062命题/247概念/311关系同版本导出；33工程/2062引用、6组边界与7组CLI/公共/桌面模块一致通过',
                        '240冻结开发取证计划及已标注身份回归通过，不加题凑数；5条旧待核补充均不关闭原问题',
                    ], pending=[
                        '本批8待核见upper/c_stage_l026.pending.jsonl：风险/信息强主张、延续/有效/普通停牌/期限、负成本与认购身份、基本面及止蚀范围、级别/量/行情、中枢三买、历史收益/业绩、嵌日期与图源',
                        '27至61共35课未完整语义审读；73课有阅读记录含历史62至64，不等全书技术抽取或全部解释统一',
                        '240题完整类别、自然问题基线、生成回答评分、消融对抗与全书跨课/图文审查未完成',
                        '独立Agent实际交付运行及Windows真实离线/缩放旋转跨页交互未验收',
                    ], checks_run=checks, checks_not_run=not_run, acceptance=acceptance,
                    next_resume_anchor='volume_1-a53e99c37ca5-p0178-b006 / lesson-027', next_action=next_action,
                    coverage_caveat='26课141段13页6图同模型四轮，累计73课阅读记录含历史62至64，不称独立复核或全书完成。',
                    evaluation=evaluation,
                    previous_turn_classification='progress：第26课141段6图、6日期修正和47条67证据正式发布；2062引用/240冻结开发题回归通过，余35课。')
    write(path, progress)
    print(json.dumps({'graph_version': VERSION, 'reviewed': 2062, 'development_cases': 240,
                      'remaining_lessons': 35, 'partial_followups': 5, 'semantic_completion': False}, ensure_ascii=False))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
