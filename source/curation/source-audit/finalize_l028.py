"""Save verified lesson28 publication and the lesson29 continuation point."""
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2]
KB = AGENT.parent / 'shared-knowledge/v0.1.0'
AUDIT = Path(__file__).resolve().parent
VERSION = '0.1.0-review-e78ec8275af6'


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
                              concepts=255, claims=4786, evidence=5747, relations=328, reviews=2212)
        claim_status = db.execute('SELECT review_status,COUNT(*) FROM claims GROUP BY review_status ORDER BY review_status').fetchall()
        figure_status = db.execute('SELECT origin_status,COUNT(*) FROM figures GROUP BY origin_status ORDER BY origin_status').fetchall()
        unit_status = db.execute('SELECT processing_status,COUNT(*) FROM units GROUP BY processing_status ORDER BY processing_status').fetchall()
        assert dict(claim_status) == {'pending': 2612, 'rejected': 27, 'reviewed': 2147}
        assert dict(unit_status)['extracted'] == 33
        next_row = db.execute("SELECT id,pdf_page,text FROM passages WHERE unit_id='lesson-029' ORDER BY pdf_page,block_index,id LIMIT 1").fetchone()
        assert next_row and next_row[2].startswith('教你炒股票29')
        next_anchor = next_row[0] + ' / lesson-029'
        known = {r[0] for r in db.execute("SELECT id FROM claims WHERE review_status='reviewed'")}
    finally:
        db.close()
    assert read(KB / 'manifest.json')['graph_version'] == VERSION
    exports = {}
    for name, number in [('claims', 2147), ('concepts', 255), ('relations', 328)]:
        path = KB / 'exports' / f'{name}.jsonl'
        rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
        assert len(rows) == number and all(r['graph_version'] == VERSION for r in rows)
        exports[name] = {'rows': number, 'graph_version': VERSION, 'sha256': sha(path)}
    assert VERSION in (KB / 'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150]
    assert read(KB / 'exports/coverage.json')['graph_version'] == VERSION
    inv = read(AUDIT / 'stage-c-l028-source-invariants.json')
    assert inv['pass'] and inv['graph_version'] == VERSION
    assert inv['original_reviewed_claims_unchanged'] == 2098 and inv['original_reviewed_evidence_unchanged'] == 3048
    verification = read(AUDIT / 'stage-c-l028-verification.json')
    assert verification['pass'] and verification['graph_version'] == VERSION
    assert len(verification['checks']) == 6 and len(verification['parity']) == 7
    dev = read(AGENT / 'evaluation/stage-g-development-current.results.json')
    assert dev['graph_version'] == VERSION and dev['executable_development_cases'] == dev['retrieval_plan_contract_passed'] == 240
    assert all(r['source_identity_matches_expected'] for r in dev['observations'])
    pending_ids = set()
    for name in ['upper/c_stage_l013_l014', 'upper/c_stage_l015_l016', 'upper/c_stage_l026', 'upper/c_stage_l027']:
        pending_ids.update(json.loads(line)['id'] for line in (AGENT / 'curation' / f'{name}.pending.jsonl').read_text(encoding='utf-8').splitlines() if line.strip())
    changes = [
        ('upper-l013-l014-c-stage-pending-figure-origin-adjustment-and-dates',
         ['exrights-long-no-short-temporary-author-choice'],
         '28给超长线不复权、短期除权暂用的建议，15均线体系周月可复权另有范围；仍不核实13图价/复权来源或全书统一处理。'),
        ('upper-l015-l016-c-stage-pending-ma-force-area-average-and-instant-boundaries',
         ['macd-instead-of-private-average-force-not-prerequisite'],
         '28明确一般人MACD可替私有指标，不需先MACD再编；仍未提供15均线面积/延伸长度的完整计算算法。'),
        ('upper-l015-l016-c-stage-pending-macd-histogram-peaks-lines-and-law',
         ['below-one-minute-histogram-special-comparison', 'macd-center-divergence-95-author-claim'],
         '28最低可视1分内的次级柱比较可远零轴为快速例特例，95%仍是作者无样本主张，不取代普通本级回轴联合条件。'),
        ('upper-l027-c-stage-pending-finite-nesting-trades-not-strokes-and-proof',
         ['triple-nesting-five-one-subminute-case', 'below-one-minute-histogram-special-comparison', 'third-five-center-departure-one-centers-two-needed'],
         '28新增三层对应段的具体例与两个1分中枢时段，但秒图是假设，仍非无限精度或通道成交的证明。'),
        ('upper-l026-c-stage-pending-center-third-buy-context-and-heuristic',
         ['type-level-by-contained-centers-not-connections', 'center-max-low-min-high-first-three-not-all-shrinking', 'third-buy-smaller-center-than-broken-one'],
         '28分清类型/中枢/连接级别、前三段与延伸扩展、三买中枢指代；29课完成规则尚待读，不补普遍裸算法。'),
    ]
    followups = []
    for pending_id, slugs, finding in changes:
        ids = ['upper-l028-c-stage-' + slug for slug in slugs]
        assert pending_id in pending_ids and all(id in known for id in ids)
        followups.append({'pending_id': pending_id, 'status': 'new_source_located_scope_still_pending',
                          'new_claim_ids': ids, 'finding': finding, 'global_pending_not_closed': True, 'graph_version': VERSION})
    (AGENT / 'curation/upper/c_stage_l028.partial-resolutions.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n' for r in followups), encoding='utf-8')
    checks = [
        '49条JSON Schema及引用/身份/映射/坐标预检',
        '187段原文哈希及全段台账一致，17页10图实际视觉核对',
        '原2098命题3048已复核证据未改，9647段528图仅9解盘日期/3读者及10图授权元数据变更；2误归候选拒绝',
        '33项当前工作区Node测试通过（原有27项及另行验收的检索评测6项）',
        '2147条已复核命题全量引用校验0错误',
        '6组来源/条件边界及7组CLI/公共/桌面模块一致，只读哈希不变',
        '240/240冻结开发取证计划和已标注来源身份回归通过，无新题替换',
        '2147命题/255概念/328关系JSONL及Markdown/coverage同版本导出',
        '5条旧待核补充关联，原问题全部保持开放',
    ]
    not_run = ['240题完整类别/自然问题基线/生成回答评分/消融对抗验收未完成；开发取证计划通过不能代替',
               '29至61共33课完整语义及全书跨课/图文审查未完成',
               '独立Agent打包后运行及Windows真实离线/缩放旋转跨页交互未验收']
    acceptance = '28课49条60证据、12段身份日期和10图来源已发布；2147引用/240冻结开发题回归通过；8待核及全书/产品目标未完成。'
    next_action = f'接续上册29课，实际PDF{next_row[1]}页标题；核对转折、走势类型完结及更大级别盘整，重点回应28课01301035/1055和中枢三段问题，保留作者/读者及原图。'
    evaluation = {'executable_development_cases': 240, 'target': 240, 'gold_review_status': 'model_reviewed_development',
                  'human_gold_reviewed': False, 'independent_test_set': False, 'generated_answers_scored': False,
                  'retrieval_plan_and_source_identity_passed_on_current_graph': 240, 'full_stage_g_acceptance_complete': False,
                  'new_project_gold_cases_created_in_this_batch': 0,
                  'note': '冻结开发取证计划及本批边界检查通过，不证明完整G、独立金标准或实际桌面交互通过。'}
    path = AUDIT / 'stage-c-l028-publication.json'
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
    assert progress['graph_version'] in ['0.1.0-review-031e34587250', VERSION]
    if progress['graph_version'] != VERSION:
        progress['previous_checkpoint'] = {key: progress[key] for key in ['graph_version', 'completed', 'next_action', 'evaluation']}
    outputs = ['source-audit/stage-c-l028-' + name + '.json' for name in ['source-plan', 'source-applied', 'source-invariants', 'publication', 'verification']]
    progress['machine_outputs'] = list(dict.fromkeys(progress['machine_outputs'] + outputs + ['upper/c_stage_l028.partial-resolutions.jsonl']))
    progress.update(updated_at=datetime.now(timezone.utc).isoformat(), graph_version=VERSION, counts=counts,
                    claim_status_counts=claim_status, figure_origin_counts=figure_status, unit_processing_status_counts=unit_status,
                    semantic_completion=False, completed=[
                        '上册28课187段17页10图同模型四轮审读，49命题60证据10关系支撑发布，新增基金/开放式基金/基金赎回/复权4概念',
                        '9解盘段按2/7 20:43及2/8 15:10分组，2/24深潜引文后3问题段恢复读者，2误归候选拒绝；10图6后加4原发未核',
                        '原2098命题3048证据与全源原文/字符映射/坐标逐行未改；基金指控/净值限制/未来崩溃只作作者历史观点，不当法律事实或执行指令',
                        '超长线复权与15均线范围分开，MACD替代非两步必要/95%无样本；三重对应/最低1分以下特例无伪秒图，读者3%浮盈不认证买点',
                        '中枢连接/纯跳空/已完成类型级别、背驰最低结果/后续扩展、二三点条件和中心指代分开；原作业时间不按读者笔误说替换；8待核',
                        '2147命题/255概念/328关系同版本导出；33工程/2147引用、6边界和7组CLI/公共/桌面模块一致通过',
                        '240冻结开发取证计划与已标注身份回归通过，不增题凑数；5条旧待核补充均开放，余33课',
                    ], pending=[
                        '本批8待核见upper/c_stage_l028.pending.jsonl：基金历史观点、复权及私有指标、作业时间/嵌引读者、最低图三重定位、最低结果/扩展、二三买中枢指代、历史概率/成本、日期图源',
                        '29至61共33课未完整语义审读；75课有阅读记录含历史62至64，不等全书技术抽取或全部解释统一',
                        '240题完整类别、自然问题基线、生成回答评分、消融对抗与全书跨课/图文审查未完成',
                        '独立Agent实际交付运行及Windows真实离线/缩放旋转跨页交互未验收',
                    ], checks_run=checks, checks_not_run=not_run, acceptance=acceptance,
                    next_resume_anchor=next_anchor, next_action=next_action,
                    coverage_caveat='28课187段17页10图同模型四轮，累计75课阅读记录含历史62至64，不称独立复核或全书完成。',
                    evaluation=evaluation,
                    previous_turn_classification='progress：28课187段10图、12源修正和49条60证据发布；2147引用/240冻结开发题回归通过，余33课。')
    write(path, progress)
    print(json.dumps({'graph_version': VERSION, 'reviewed': 2147, 'development_cases': 240,
                      'remaining_lessons': 33, 'next_anchor': next_anchor, 'semantic_completion': False}, ensure_ascii=False))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
