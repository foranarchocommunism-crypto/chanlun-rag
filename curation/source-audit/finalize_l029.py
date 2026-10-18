"""Save verified lesson29 publication and the lesson30 continuation point."""
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2]
KB = AGENT.parent / 'shared-knowledge/v0.1.0'
AUDIT = Path(__file__).resolve().parent
VERSION = '0.1.0-review-c6ace0c23754'


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
                              concepts=257, claims=4824, evidence=5790, relations=339, reviews=2250)
        claim_status = db.execute('SELECT review_status,COUNT(*) FROM claims GROUP BY review_status ORDER BY review_status').fetchall()
        figure_status = db.execute('SELECT origin_status,COUNT(*) FROM figures GROUP BY origin_status ORDER BY origin_status').fetchall()
        unit_status = db.execute('SELECT processing_status,COUNT(*) FROM units GROUP BY processing_status ORDER BY processing_status').fetchall()
        assert dict(claim_status) == {'pending': 2612, 'rejected': 27, 'reviewed': 2185}
        assert dict(unit_status)['extracted'] == 32
        next_row = db.execute("SELECT id,pdf_page,text FROM passages WHERE unit_id='lesson-030' ORDER BY pdf_page,block_index,id LIMIT 1").fetchone()
        assert next_row and next_row[2].startswith('教你炒股票30')
        next_anchor = next_row[0] + ' / lesson-030'
        known = {r[0] for r in db.execute("SELECT id FROM claims WHERE review_status='reviewed'")}
    finally:
        db.close()
    assert read(KB / 'manifest.json')['graph_version'] == VERSION
    exports = {}
    for name, number in [('claims', 2185), ('concepts', 257), ('relations', 339)]:
        path = KB / 'exports' / f'{name}.jsonl'
        rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
        assert len(rows) == number and all(r['graph_version'] == VERSION for r in rows)
        exports[name] = {'rows': number, 'graph_version': VERSION, 'sha256': sha(path)}
    assert VERSION in (KB / 'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150]
    assert read(KB / 'exports/coverage.json')['graph_version'] == VERSION
    inv = read(AUDIT / 'stage-c-l029-source-invariants.json')
    assert inv['pass'] and inv['graph_version'] == VERSION
    assert inv['original_reviewed_claims_unchanged'] == 2147 and inv['original_reviewed_evidence_unchanged'] == 3108
    verification = read(AUDIT / 'stage-c-l029-verification.json')
    assert verification['pass'] and verification['graph_version'] == VERSION
    assert len(verification['checks']) == 6 and len(verification['parity']) == 7
    dev = read(AGENT / 'evaluation/stage-g-development-current.results.json')
    assert dev['graph_version'] == VERSION and dev['executable_development_cases'] == dev['retrieval_plan_contract_passed'] == 240
    assert all(r['source_identity_matches_expected'] for r in dev['observations'])
    pending_ids = set()
    for name in ['c_stage_l015_l016', 'c_stage_l027', 'c_stage_l028']:
        pending_ids.update(json.loads(line)['id'] for line in (AGENT / 'curation/upper' / f'{name}.pending.jsonl').read_text(encoding='utf-8').splitlines() if line.strip())
    changes = [
        ('upper-l028-c-stage-pending-homework-center-dates-reader-requote-and-type',
         ['trend-completion-final-leg-sublevel-below-divergence', 'previous-type-last-center-not-reassigned-forward', 'last-center-expansion-one-unfinished-type'],
         '29给完成末段至少次级以下背驰及前类型末中枢归属，区分未完成类型扩展与两完成类型；仍未逐一复算所有分钟数据，不将读者0201时间替换原作业。'),
        ('upper-l028-c-stage-pending-post-divergence-minimum-and-expansion-to-larger',
         ['divergence-reversal-theorem-three-outcomes', 'rebound-must-touch-dd-not-zd', 'last-center-expansion-one-unfinished-type'],
         '29新增三类定理、DD非ZD与未完成扩展说明；不是小背驰一律大反趋势，完整形式证明及唯一未来仍无。'),
        ('upper-l027-c-stage-pending-consolidation-return-types-and-analogous-buy-names',
         ['weak-trend-case-versus-consolidation-third-sell', 'first-sublevel-rebound-heuristic-not-absolute'],
         '29按反弹相对末中枢级别区别趋势背驰扩展与盘背转三卖，首次回抽仅非绝对判据；不统一类买/严格买点或删除备注归属疑问。'),
        ('upper-l027-c-stage-pending-multilevel-regime-t1-and-abc-premises',
         ['large-breakout-one-divergence-may-only-intraday', '600640-nesting-before-small-signal-and-third-fall'],
         '29再给大级别背驰段与二买初升/主升分层、小信号可盘中化解；没有补T+1成交保证、ABC完整阈值或读者买点认可。'),
        ('upper-l015-l016-c-stage-pending-ma-force-area-average-and-instant-boundaries',
         ['average-area-rough-definition-macd-measure-proof-absent'],
         '29明确均线面积定义粗糙及MACD辅助，测度论精确定义只被声称未展示；原面积/时间及瞬时延伸口径不由此自动补完。'),
    ]
    followups = []
    for pending_id, slugs, finding in changes:
        ids = ['upper-l029-c-stage-' + slug for slug in slugs]
        assert pending_id in pending_ids and all(id in known for id in ids)
        followups.append({'pending_id': pending_id, 'status': 'new_source_located_scope_still_pending',
                          'new_claim_ids': ids, 'finding': finding, 'global_pending_not_closed': True, 'graph_version': VERSION})
    (AGENT / 'curation/upper/c_stage_l029.partial-resolutions.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n' for r in followups), encoding='utf-8')
    checks = [
        '38条JSON Schema及引用/身份/映射/坐标预检',
        '72段原文哈希及全段台账一致，10页12图实际视觉核对',
        '原2147命题3108已复核证据未改，9647段528图仅2解盘日期及12图授权来源备注变更',
        '33项当前工作区Node测试通过（原有27项及另行验收的检索评测6项）',
        '2185条已复核命题全量引用校验0错误',
        '6组来源/条件边界及7组CLI/公共/桌面模块一致，只读哈希不变',
        '240/240冻结开发取证计划和已标注来源身份回归通过，无新题替换',
        '2185命题/257概念/339关系JSONL及Markdown/coverage同版本导出',
        '5条旧待核补充关联，原问题全部保持开放',
    ]
    not_run = ['240题完整类别/自然问题基线/生成回答评分/消融对抗验收未完成；开发取证计划通过不能代替',
               '30至61共32课完整语义及全书跨课/图文审查未完成',
               '独立Agent打包后运行及Windows真实离线/缩放旋转跨页交互未验收']
    acceptance = '29课38条43证据、2段日期和12图来源已发布；2185引用/240冻结开发题回归通过；8待核及全书/产品目标未完成。'
    next_action = f'接续上册30课，实际PDF{next_row[1]}页标题；核对缠论绝对性、背驰与第三类买卖点及中枢级别，保留作者断言/条件/读者及原图来源。'
    evaluation = {'executable_development_cases': 240, 'target': 240, 'gold_review_status': 'model_reviewed_development',
                  'human_gold_reviewed': False, 'independent_test_set': False, 'generated_answers_scored': False,
                  'retrieval_plan_and_source_identity_passed_on_current_graph': 240, 'full_stage_g_acceptance_complete': False,
                  'new_project_gold_cases_created_in_this_batch': 0,
                  'note': '冻结开发取证计划及本批边界检查通过，不证明完整G、独立金标准或实际桌面交互通过。'}
    path = AUDIT / 'stage-c-l029-publication.json'
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
    assert progress['graph_version'] in ['0.1.0-review-e78ec8275af6', VERSION]
    if progress['graph_version'] != VERSION:
        progress['previous_checkpoint'] = {key: progress[key] for key in ['graph_version', 'completed', 'next_action', 'evaluation']}
    outputs = ['source-audit/stage-c-l029-' + name + '.json' for name in ['source-plan', 'source-applied', 'source-invariants', 'publication', 'verification']]
    progress['machine_outputs'] = list(dict.fromkeys(progress['machine_outputs'] + outputs + ['upper/c_stage_l029.partial-resolutions.jsonl']))
    progress.update(updated_at=datetime.now(timezone.utc).isoformat(), graph_version=VERSION, counts=counts,
                    claim_status_counts=claim_status, figure_origin_counts=figure_status, unit_processing_status_counts=unit_status,
                    semantic_completion=False, completed=[
                        '上册29课72段10页12图同模型四轮审读，38命题43证据11关系支撑发布，新增背驰-转折定理/超跌2概念',
                        '2解盘段按2/12 15:15日期修正，前段2/9时间未改；12图4后加8未核含4张大山习作，2008年7月图不混2007原发',
                        '原2147命题3108证据及全源原文/字符映射/坐标逐行未改；两处署名未明备注原文保留而截除出作者命题引文',
                        'DD与ZD分开，三类定理/同级反趋势与更大盘整、一未完成扩展与两完成类型、9段假设及首次回抽非绝对均保留',
                        '早期自选最低1分三K不等全书严格递归；V预判超本章，安全/利润/效率/测度论证明仅作者主张；8待核',
                        '2185命题/257概念/339关系同版本导出；33工程/2185引用、6边界和7组CLI/公共/桌面模块一致通过',
                        '240冻结开发取证计划与已标注身份回归通过，不增题凑数；5条旧待核补充均开放，余32课',
                    ], pending=[
                        '本批8待核见upper/c_stage_l029.pending.jsonl：未署名备注、三类/DD/完成、原指数归属、最低1分口径、效果断言/V、历史自述、测度论证明缺失、日期图源',
                        '30至61共32课未完整语义审读；76课有阅读记录含历史62至64，不等全书技术抽取或全部解释统一',
                        '240题完整类别、自然问题基线、生成回答评分、消融对抗与全书跨课/图文审查未完成',
                        '独立Agent实际交付运行及Windows真实离线/缩放旋转跨页交互未验收',
                    ], checks_run=checks, checks_not_run=not_run, acceptance=acceptance,
                    next_resume_anchor=next_anchor, next_action=next_action,
                    coverage_caveat='29课72段10页12图同模型四轮，累计76课阅读记录含历史62至64，不称独立复核或全书完成。',
                    evaluation=evaluation,
                    previous_turn_classification='progress：29课72段12图、2日期修正和38条43证据发布；2185引用/240冻结开发题回归通过，余32课。')
    write(path, progress)
    print(json.dumps({'graph_version': VERSION, 'reviewed': 2185, 'development_cases': 240,
                      'remaining_lessons': 32, 'next_anchor': next_anchor, 'semantic_completion': False}, ensure_ascii=False))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
