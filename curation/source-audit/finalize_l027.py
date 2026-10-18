"""Record verified lesson27 publication and retain open cross-course questions."""
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2]
KB = AGENT.parent / 'shared-knowledge/v0.1.0'
AUDIT = Path(__file__).resolve().parent
VERSION = '0.1.0-review-031e34587250'


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
                              concepts=251, claims=4737, evidence=5687, relations=320, reviews=2161)
        claim_status = db.execute('SELECT review_status,COUNT(*) FROM claims GROUP BY review_status ORDER BY review_status').fetchall()
        figure_status = db.execute('SELECT origin_status,COUNT(*) FROM figures GROUP BY origin_status ORDER BY origin_status').fetchall()
        unit_status = db.execute('SELECT processing_status,COUNT(*) FROM units GROUP BY processing_status ORDER BY processing_status').fetchall()
        assert dict(claim_status) == {'pending': 2614, 'rejected': 25, 'reviewed': 2098}
        assert dict(unit_status)['extracted'] == 34
        assert db.execute('SELECT unit_id FROM passages WHERE id=?', ('volume_1-a53e99c37ca5-p0187-b012',)).fetchone() == ('lesson-028',)
        known = {r[0] for r in db.execute("SELECT id FROM claims WHERE review_status='reviewed'")}
    finally:
        db.close()
    assert read(KB / 'manifest.json')['graph_version'] == VERSION
    exports = {}
    for name, number in [('claims', 2098), ('concepts', 251), ('relations', 320)]:
        path = KB / 'exports' / f'{name}.jsonl'
        rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
        assert len(rows) == number and all(r['graph_version'] == VERSION for r in rows)
        exports[name] = {'rows': number, 'graph_version': VERSION, 'sha256': sha(path)}
    assert VERSION in (KB / 'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150]
    assert read(KB / 'exports/coverage.json')['graph_version'] == VERSION
    inv = read(AUDIT / 'stage-c-l027-source-invariants.json')
    assert inv['pass'] and inv['graph_version'] == VERSION
    assert inv['original_reviewed_claims_unchanged'] == 2062 and inv['original_reviewed_evidence_unchanged'] == 2998
    verification = read(AUDIT / 'stage-c-l027-verification.json')
    assert verification['pass'] and verification['graph_version'] == VERSION
    assert len(verification['checks']) == 6 and len(verification['parity']) == 7
    dev = read(AGENT / 'evaluation/stage-g-development-current.results.json')
    assert dev['graph_version'] == VERSION and dev['executable_development_cases'] == dev['retrieval_plan_contract_passed'] == 240
    assert all(r['source_identity_matches_expected'] for r in dev['observations'])

    pending_ids = set()
    for name in ['upper/c_stage_l015_l016', 'upper/c_stage_l025', 'upper/c_stage_l026', 'lower/c_stage_l101_l102']:
        pending_ids.update(json.loads(line)['id'] for line in (AGENT / 'curation' / f'{name}.pending.jsonl').read_text(encoding='utf-8').splitlines() if line.strip())
    changes = [
        ('upper-l015-l016-c-stage-pending-no-trend-scope-first-kiss-and-consolidation',
         ['first-center-only-consolidation-divergence', 'consolidation-divergence-compare-first-third-types', 'analogous-first-buy-at-large-consolidation'],
         '27明确第一中枢处类背驰、两个盘整可比与大级别类一买；不取消15趋势背驰语境，也不等全部盘背回中枢。'),
        ('upper-l015-l016-c-stage-pending-macd-histogram-peaks-lines-and-law',
         ['vanke-quarter-lines-or-area-divergence-signal', 'zero-retest-one-condition-look-lower-end', 'macd-b-must-retrace-near-zero-not-arbitrary-three'],
         '27季线实例说线/面积任一项可信号、两者更标准，而问答回轴只是一条件；不补成全书普遍充分条件，代词粒度仍未明。'),
        ('upper-l025-c-stage-pending-case-time-prices-forecast-and-guarantees',
         ['life-insurer-second-down-center-and-49-confirmation'],
         '27明确说49上涨背驰，为25“49那天不是背驰”的可能反问增旁证；旧字句/旧语气不改，30/100展望未验证。'),
        ('upper-l026-c-stage-pending-center-third-buy-context-and-heuristic',
         ['center-b-may-exceed-a-extreme-with-overlap', 'small-third-buy-t1-not-executable-profit', 'thirty-down-break-five-down-divergence-third-sell-risk'],
         '27给B可越A极值但三段须重叠、T+1涨而卖不了及盘背转第三类的方向条件；不据此删除递归/连续/级别前提。'),
        ('lower-l101-l102-c-stage-pending-uniqueness-and-recomposition-proof',
         ['precision-theorem-recursive-until-minimum', 'finite-levels-no-unique-mathematical-point', 'nested-legs-must-be-inside-parent'],
         '27有逐级对应范围程序及有限层级不能证明唯一数学点的明确限制；不是101整体结构唯一性的独立证明，原问题保持开放。'),
    ]
    followups = []
    for pending_id, slugs, finding in changes:
        ids = ['upper-l027-c-stage-' + slug for slug in slugs]
        assert pending_id in pending_ids and all(id in known for id in ids)
        followups.append({'pending_id': pending_id, 'status': 'new_source_located_scope_still_pending',
                          'new_claim_ids': ids, 'finding': finding, 'global_pending_not_closed': True, 'graph_version': VERSION})
    (AGENT / 'curation/upper/c_stage_l027.partial-resolutions.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n' for r in followups), encoding='utf-8')
    checks = [
        '36条JSON Schema及引用/身份/映射/坐标预检',
        '93段原文哈希及全段台账一致；10页7本课图与178前课边界实际视觉检查',
        '原2062命题2998已复核证据未改，全部9647段528图仅26段时间与7图元数据授权变更',
        '33项当前工作区Node测试通过（原有27项及另行验收的检索评测6项）',
        '2098条已复核命题全量引用校验0错误',
        '6组来源/条件边界及7组CLI/公共/桌面模块一致，只读哈希不变',
        '240/240冻结开发取证计划和已标注来源身份回归通过，无新题替换',
        '2098命题/251概念/320关系JSONL及Markdown/coverage同版本导出',
        '5条旧待核补充关联，全部原问题仍开放',
    ]
    not_run = ['240题完整类别/自然问题基线/生成回答评分/消融对抗验收未完成；开发取证计划通过不能代替',
               '28至61共34课完整语义及全书跨课/图文审查未完成',
               '独立Agent打包后运行及Windows真实离线/缩放旋转跨页交互未验收']
    acceptance = '27课36条50证据、26段时间和7图来源已发布；2098引用/240冻结开发题回归通过；8待核及全书/产品目标未完成。'
    next_action = '接续上册28课，实际PDF187页标题；核对基金/资金与市场运行观点、作者技术答疑及跨日解盘，保留历史自述、条件、读者身份与原图。'
    evaluation = {'executable_development_cases': 240, 'target': 240, 'gold_review_status': 'model_reviewed_development',
                  'human_gold_reviewed': False, 'independent_test_set': False, 'generated_answers_scored': False,
                  'retrieval_plan_and_source_identity_passed_on_current_graph': 240, 'full_stage_g_acceptance_complete': False,
                  'new_project_gold_cases_created_in_this_batch': 0,
                  'note': '冻结240题回归和本批边界检查通过，不表示完整G或桌面验收通过。'}
    path = AUDIT / 'stage-c-l027-publication.json'
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
    assert progress['graph_version'] in ['0.1.0-review-31581ef72e83', VERSION]
    if progress['graph_version'] != VERSION:
        progress['previous_checkpoint'] = {key: progress[key] for key in ['graph_version', 'completed', 'next_action', 'evaluation']}
    outputs = ['source-audit/stage-c-l027-' + name + '.json' for name in ['source-plan', 'source-applied', 'source-invariants', 'publication', 'verification']]
    progress['machine_outputs'] = list(dict.fromkeys(progress['machine_outputs'] + outputs + ['upper/c_stage_l027.partial-resolutions.jsonl']))
    progress.update(updated_at=datetime.now(timezone.utc).isoformat(), graph_version=VERSION, counts=counts,
                    claim_status_counts=claim_status, figure_origin_counts=figure_status, unit_processing_status_counts=unit_status,
                    semantic_completion=False, completed=[
                        '上册27课93段10页7本课图+178前课边界同模型四轮审读，36命题50证据9关系支撑发布，新增历史性底部/类一买/类二买/精确转折程序定理4概念',
                        '19正文补标题15:11:27，7解盘段按2/5 15:18及15:25分组；7图5文后含2011重绘2原发未核，17周原单位与读者代码不改',
                        '原2062命题2998证据及源原文/字符映射/坐标逐行未改，仅26段时间和7图来源元数据变更',
                        '严格与类一二买分开；背驰段命名/进入段/已确认不同，区间套需对应包含且层级有限，成交分笔非后期几何笔；不保证唯一数学点',
                        '万科数字自我降权/季线MACD或项、周线不必历史底/日线可靠性、T+1涨不一定卖、30下破/初涨盘背两支及ABC前提保留；8待核',
                        '2098命题/251概念/320关系同版本导出；33工程/2098引用、6边界与7组CLI/公共/桌面模块一致通过',
                        '240冻结开发取证计划和已标注身份回归通过，不增题凑数；5条旧待核补充均开放，余34课',
                    ], pending=[
                        '本批8待核见upper/c_stage_l027.pending.jsonl：中枢数概率、盘背/严格与类点、背驰段确认、区间套有限精度、季线单位与MACD、多级别/T+1、案例预测代词、时间图源',
                        '28至61共34课未完整语义审读；74课有阅读记录含历史62至64，不等全书技术抽取或全部解释统一',
                        '240题完整类别、自然问题基线、生成回答评分、消融对抗与全书跨课/图文审查未完成',
                        '独立Agent实际交付运行及Windows真实离线/缩放旋转跨页交互未验收',
                    ], checks_run=checks, checks_not_run=not_run, acceptance=acceptance,
                    next_resume_anchor='volume_1-a53e99c37ca5-p0187-b012 / lesson-028', next_action=next_action,
                    coverage_caveat='27课93段10页7本课图同模型四轮，累计74课阅读记录含历史62至64，不称独立复核或全书完成。',
                    evaluation=evaluation,
                    previous_turn_classification='progress：27课93段7图、26时间修正及36条50证据发布；2098引用/240冻结开发题回归通过，余34课。')
    write(path, progress)
    print(json.dumps({'graph_version': VERSION, 'reviewed': 2098, 'development_cases': 240,
                      'remaining_lessons': 34, 'partial_followups': 5, 'semantic_completion': False}, ensure_ascii=False))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
