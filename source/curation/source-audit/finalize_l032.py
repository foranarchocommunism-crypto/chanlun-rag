"""Save verified lesson32 publication and the lesson33 continuation point."""
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2]
KB = AGENT.parent / 'shared-knowledge/v0.1.0'
AUDIT = Path(__file__).resolve().parent
VERSION = '0.1.0-review-68e03935d1ac'


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
                              concepts=262, claims=4939, evidence=5923, relations=371, reviews=2370)
        claim_status = db.execute('SELECT review_status,COUNT(*) FROM claims GROUP BY review_status ORDER BY review_status').fetchall()
        figure_status = db.execute('SELECT origin_status,COUNT(*) FROM figures GROUP BY origin_status ORDER BY origin_status').fetchall()
        unit_status = db.execute('SELECT processing_status,COUNT(*) FROM units GROUP BY processing_status ORDER BY processing_status').fetchall()
        assert dict(claim_status) == {'pending': 2612, 'rejected': 27, 'reviewed': 2300}
        assert dict(unit_status)['extracted'] == 29
        next_row = db.execute("SELECT id,pdf_page,text FROM passages WHERE unit_id='lesson-033' ORDER BY pdf_page,block_index,id LIMIT 1").fetchone()
        assert next_row and next_row[2].startswith('教你炒股票33')
        next_anchor = next_row[0] + ' / lesson-033'
        known = {r[0] for r in db.execute("SELECT id FROM claims WHERE review_status='reviewed'")}
    finally:
        db.close()
    assert read(KB / 'manifest.json')['graph_version'] == VERSION
    exports = {}
    for name, number in [('claims', 2300), ('concepts', 262), ('relations', 371)]:
        path = KB / 'exports' / f'{name}.jsonl'
        rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
        assert len(rows) == number and all(r['graph_version'] == VERSION for r in rows)
        exports[name] = {'rows': number, 'graph_version': VERSION, 'sha256': sha(path)}
    assert VERSION in (KB / 'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150]
    assert read(KB / 'exports/coverage.json')['graph_version'] == VERSION
    inv = read(AUDIT / 'stage-c-l032-source-invariants.json')
    assert inv['pass'] and inv['graph_version'] == VERSION
    assert inv['original_reviewed_claims_unchanged'] == 2259 and inv['original_reviewed_evidence_unchanged'] == 3238
    verification = read(AUDIT / 'stage-c-l032-verification.json')
    assert verification['pass'] and verification['graph_version'] == VERSION
    assert len(verification['checks']) == 6 and len(verification['parity']) == 7
    dev = read(AGENT / 'evaluation/stage-g-development-current.results.json')
    assert dev['graph_version'] == VERSION and dev['executable_development_cases'] == dev['retrieval_plan_contract_passed'] == 240
    assert all(r['source_identity_matches_expected'] for r in dev['observations'])
    pending_ids = set()
    for name in ['c_stage_l028', 'c_stage_l029', 'c_stage_l030', 'c_stage_l031']:
        pending_ids.update(json.loads(line)['id'] for line in (AGENT / 'curation/upper' / f'{name}.pending.jsonl').read_text(encoding='utf-8').splitlines() if line.strip())
    changes = [
        ('upper-l031-c-stage-pending-weekly-third-leg-explicit-author-qualification',
         ['nine-sublevel-extension-author-limit-with-wave-premise', 'straight-limit-up-no-wave-cannot-add-level'],
         '32次日以有波动的九个30分延伸及三日线说明周线，并称当时足以形成；31同日不严谨限定保留，仍需33阈值与计数说明，不把分钟数或直线累计成周线。'),
        ('upper-l031-c-stage-pending-third-buy-consolidation-and-internal-c-nesting',
         ['b-and-c-departures-require-third-buy-not-guaranteed', 'third-buy-retest-at-least-sublevel-three-down-up-down', 'exit-standard-changes-when-b-becomes-daily'],
         '32补离开中枢需三买/回抽至少次级三段与B扩日线后退出标准变化；不把任意突破、一次下探或原字母恒定看成三买充分条件。'),
        ('upper-l031-c-stage-pending-parent-leg-main-rise-main-fall-and-event-exception',
         ['five-divergence-rebuy-parent-rise-vs-nesting', 'divergence-level-not-rise-level-without-nesting'],
         '32明确背驰级别与上涨级别无必然对应、须区间套，主升可回补与嵌套背驰不可随便回补分开；不补突发事件可无损退出。'),
        ('upper-l030-c-stage-pending-lowest-consecutive-k-direction-and-subsequent-recursion',
         ['five-center-three-one-types-with-child-center', 'straight-pull-no-overlap-no-center-macd-not-volume'],
         '32明确5分须三1分类型，各1分类型至少一1分中枢，自选最低才三K；连续直拉无重合不成中枢，仍不抹后期几何递归口径。'),
        ('upper-l028-c-stage-pending-subminute-triple-nesting-and-normal-macd-premise',
         ['subminute-time-chart-or-one-minute-hist-not-lines', '600550-no-five-without-macd-lines-return-zero'],
         '32分别答更低级只看1分柱和本级黄白线须回轴，显示对象范围不同；未提供秒图或一根缩柱充分条件，不取消三重包含。'),
        ('upper-l029-c-stage-pending-three-outcomes-dd-and-type-completion',
         ['b-no-divergence-b-center-may-exceed-a', 'daily-b-reclassify-c-use-daily-standard', '2915-is-gg-not-center-top-2894-correction'],
         '32补中枢可能升级而须当下重组，并有GG/ZG作者明确更正，呼应DD/ZD区别；未补完整形式证明或全书唯一分解算法。'),
    ]
    followups = []
    for pending_id, slugs, finding in changes:
        ids = ['upper-l032-c-stage-' + slug for slug in slugs]
        assert pending_id in pending_ids and all(id in known for id in ids)
        followups.append({'pending_id': pending_id, 'status': 'new_source_located_scope_still_pending',
                          'new_claim_ids': ids, 'finding': finding, 'global_pending_not_closed': True, 'graph_version': VERSION})
    (AGENT / 'curation/upper/c_stage_l032.partial-resolutions.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n' for r in followups), encoding='utf-8')
    checks = [
        '41条JSON Schema及引用/身份/映射/坐标预检',
        '131段原文哈希及全段台账一致，实际PDF233至243共11页及5完整图视觉核对',
        '原2259命题3238已复核证据未改，9647段528图逐行比较仅5收盘补充角色/日期与5图来源备注授权变更',
        '33项当前工作区Node测试通过（原有27项及另行验收的检索评测6项）',
        '2300条已复核命题全量引用校验0错误',
        '6组来源/条件边界及7组CLI/公共/桌面模块一致，7命题8配图关联逐项确认，只读哈希不变',
        '240/240冻结开发取证计划和已标注来源身份回归通过，无新题替换',
        '2300命题/262概念/371关系JSONL及Markdown/coverage同版本导出',
        '6条旧待核补充关联，原问题全部保持开放',
    ]
    not_run = ['240题完整类别/自然问题基线/生成回答评分/消融对抗验收未完成；开发取证计划通过不能代替',
               '33至61共29课完整语义及全书跨课/图文审查未完成',
               '独立Agent打包后运行及Windows真实离线/缩放旋转跨页交互未验收']
    acceptance = '32课41条46证据、5补充段身份/日期和5图来源已发布；2300引用/240冻结开发题回归通过；8待核及全书/产品目标未完成。'
    next_action = f'接续上册33课，实际PDF{next_row[1]}页标题；核对走势多义性、中枢延伸与扩展的数量/级别及32九次级阈值，逐段逐图保留身份和完成条件。'
    evaluation = {'executable_development_cases': 240, 'target': 240, 'gold_review_status': 'model_reviewed_development',
                  'human_gold_reviewed': False, 'independent_test_set': False, 'generated_answers_scored': False,
                  'retrieval_plan_and_source_identity_passed_on_current_graph': 240, 'full_stage_g_acceptance_complete': False,
                  'new_project_gold_cases_created_in_this_batch': 0,
                  'note': '冻结开发取证计划及本批边界检查通过，不证明完整G、独立金标准或实际桌面交互通过。'}
    path = AUDIT / 'stage-c-l032-publication.json'
    pub = read(path)
    assert pub['graph_version'] == VERSION and pub['formal_import'] == 'passed'
    pub.update(updated_at=datetime.now(timezone.utc).isoformat(), checks_run=checks, checks_not_run=not_run,
               acceptance=acceptance, next_action=next_action, exports=exports,
               final_sha256={'database': sha(KB / 'graph.sqlite'), 'manifest': sha(KB / 'manifest.json')},
               development_evaluation=evaluation, partial_pending_followups=6, semantic_completion=False,
               writes_to_knowledge_graph_by_this_finalizer=False)
    write(path, pub)
    path = AGENT / 'curation/progress.json'; progress = read(path)
    assert progress['graph_version'] in ['0.1.0-review-df7b7562fbf3', VERSION]
    if progress['graph_version'] != VERSION:
        progress['previous_checkpoint'] = {key: progress[key] for key in ['graph_version', 'completed', 'next_action', 'evaluation']}
    outputs = ['source-audit/stage-c-l032-' + name + '.json' for name in ['source-plan', 'source-applied', 'source-invariants', 'publication', 'verification']]
    progress['machine_outputs'] = list(dict.fromkeys(progress['machine_outputs'] + outputs + ['upper/c_stage_l032.partial-resolutions.jsonl']))
    progress.update(updated_at=datetime.now(timezone.utc).isoformat(), graph_version=VERSION, counts=counts,
                    claim_status_counts=claim_status, figure_origin_counts=figure_status, unit_processing_status_counts=unit_status,
                    semantic_completion=False, completed=[
                        '上册32课131段11页5图同模型四轮审读，41命题46证据10关系支撑发布，无新增概念',
                        '5收盘补充段改author_commentary并只记2/28不造具体时刻，早课8:44保留；CCTV/老新手/Tryrtytry读者与作者有限表扬/记号认可分开',
                        '原2259命题3238证据未改，全部原文/字符映射/坐标逐行未变，仅5补充段来源精度和5图来源备注修正；5图2文后3未核',
                        'A已成不保证B/c，B可扩级需当下a`+B/a`+A`重组与新级别判断；2915为GG/ZG约2894有作者明确更正，九次级延伸须波动且阈值待33细化',
                        '次级回抽三段/三1分类型与自选最低三K、普通MACD回轴与更低级只看柱分对象；预测列全分支可行而非唯一未来，读者盈利不认证三买；8待核',
                        '2300命题/262概念/371关系同版本导出；33工程/2300引用、6边界和7组CLI/公共/桌面模块一致，7命题8配图关联逐项通过',
                        '240冻结开发取证计划与已标注身份回归通过，不增题凑数；6条旧待核补充均开放，余29课',
                    ], pending=[
                        '本批8待核见upper/c_stage_l032.pending.jsonl：当下重组/级别、九延伸阈值、GG更正、三买/日线确认、预测分支、MACD/递归、补充时间与有限认可、历史自述/图源',
                        '33至61共29课未完整语义审读；79课有阅读记录含历史62至64，不等全书技术抽取或全部解释统一',
                        '240题完整类别、自然问题基线、生成回答评分、消融对抗与全书跨课/图文审查未完成',
                        '独立Agent实际交付运行及Windows真实离线/缩放旋转跨页交互未验收',
                    ], checks_run=checks, checks_not_run=not_run, acceptance=acceptance,
                    next_resume_anchor=next_anchor, next_action=next_action,
                    coverage_caveat='32课131段11页5图同模型四轮，累计79课阅读记录含历史62至64，不称独立复核或全书完成。',
                    evaluation=evaluation,
                    previous_turn_classification='progress：31课5条漏图关联显式迁移与32课131段5图/41条46证据发布；2300引用/240冻结开发题回归通过，余29课。')
    write(path, progress)
    print(json.dumps({'graph_version': VERSION, 'reviewed': 2300, 'development_cases': 240,
                      'remaining_lessons': 29, 'next_anchor': next_anchor, 'semantic_completion': False}, ensure_ascii=False))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
