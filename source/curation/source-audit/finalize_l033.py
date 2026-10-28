"""Save verified lesson33 publication and the lesson34 continuation point."""
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2]
KB = AGENT.parent / 'shared-knowledge/v0.1.0'
AUDIT = Path(__file__).resolve().parent
VERSION = '0.1.0-review-2c7fb5f929d2'


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
                              concepts=265, claims=4989, evidence=5980, relations=382, reviews=2420)
        claim_status = db.execute('SELECT review_status,COUNT(*) FROM claims GROUP BY review_status ORDER BY review_status').fetchall()
        figure_status = db.execute('SELECT origin_status,COUNT(*) FROM figures GROUP BY origin_status ORDER BY origin_status').fetchall()
        unit_status = db.execute('SELECT processing_status,COUNT(*) FROM units GROUP BY processing_status ORDER BY processing_status').fetchall()
        assert dict(claim_status) == {'pending': 2612, 'rejected': 27, 'reviewed': 2350}
        assert dict(unit_status)['extracted'] == 28
        next_row = db.execute("SELECT id,pdf_page,text FROM passages WHERE unit_id='lesson-034' ORDER BY pdf_page,block_index,id LIMIT 1").fetchone()
        assert next_row and next_row[2].startswith('教你炒股票34')
        next_anchor = next_row[0] + ' / lesson-034'
        known = {r[0] for r in db.execute("SELECT id FROM claims WHERE review_status='reviewed'")}
    finally:
        db.close()
    assert read(KB / 'manifest.json')['graph_version'] == VERSION
    exports = {}
    for name, number in [('claims', 2350), ('concepts', 265), ('relations', 382)]:
        path = KB / 'exports' / f'{name}.jsonl'
        rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
        assert len(rows) == number and all(r['graph_version'] == VERSION for r in rows)
        exports[name] = {'rows': number, 'graph_version': VERSION, 'sha256': sha(path)}
    assert VERSION in (KB / 'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150]
    assert read(KB / 'exports/coverage.json')['graph_version'] == VERSION
    inv = read(AUDIT / 'stage-c-l033-source-invariants.json')
    assert inv['pass'] and inv['graph_version'] == VERSION
    assert inv['original_reviewed_claims_unchanged'] == 2300 and inv['original_reviewed_evidence_unchanged'] == 3284
    verification = read(AUDIT / 'stage-c-l033-verification.json')
    assert verification['pass'] and verification['graph_version'] == VERSION
    assert len(verification['checks']) == 6 and len(verification['parity']) == 7
    dev = read(AGENT / 'evaluation/stage-g-development-current.results.json')
    assert dev['graph_version'] == VERSION and dev['executable_development_cases'] == dev['retrieval_plan_contract_passed'] == 240
    assert all(r['source_identity_matches_expected'] for r in dev['observations'])
    pending_ids = set()
    for name in ['c_stage_l031', 'c_stage_l032']:
        pending_ids.update(json.loads(line)['id'] for line in (AGENT / 'curation/upper' / f'{name}.pending.jsonl').read_text(encoding='utf-8').splitlines() if line.strip())
    changes = [
        ('upper-l032-c-stage-pending-nine-extension-count-waves-and-next-lesson',
         ['extension-six-added-plus-three-initial-nine', 'nine-one-minute-can-be-thirty-center-view', 'daily-jan4-feb6-three-thirty-not-nine-thirty'],
         '33明确新增延伸最多五、出现六加初始三共九，另给实际九5分非九30分的日线案例；计数口径已补，仍不能脱离完成/重合/有波动而机械九根K。'),
        ('upper-l032-c-stage-pending-live-regrouping-b-level-and-exit-scope',
         ['larger-b-can-reverse-and-same-side-excursions', 'opposite-departure-strength-and-third-buy-retest', 'new-center-at-least-same-nonoverlap-old-enters-system'],
         '33从中枢回拉释义解释B更大后的反向c、两次同侧离开及新中枢与旧系统；仍无唯一力度公式，参照a+A+b或b不擅统一。'),
        ('upper-l032-c-stage-pending-subminute-macd-vs-own-level-axis-and-recursion',
         ['macd-same-side-divergence-versus-opposite-cross-zero', 'macd-just-crossed-zero-not-own-level-divergence', 'subminute-pull-important-under-five-thirty-center'],
         '33明确同向比较与反向比较分MACD同侧/异侧，普通刚上轴非本级背驰；5/30中枢且1分离开的次1信号可重要，不取消对应层级与原普通回轴。'),
        ('upper-l031-c-stage-pending-weekly-third-leg-explicit-author-qualification',
         ['daily-jan4-feb6-three-thirty-not-nine-thirty', 'weekly-first-leg-until-april-or-up-no-weekly', 'mar5-weekly-only-if-no-up-break-daily-alternative'],
         '33作者具体说明1/4—2/6完整日线而周线只第一段，若不直接突破且盘到4月以后才可能成周线；旧粗说/32足够句仍按时点和范围保存，未完成完整历史数据重算。'),
        ('upper-l031-c-stage-pending-parent-leg-main-rise-main-fall-and-event-exception',
         ['end-by-divergence-not-necessarily-direct-sublevel', 'larger-divergence-usually-more-but-small-can-accumulate', 'subminute-pull-important-under-five-thirty-center'],
         '33补至少本级结果非仅紧邻次级造成，a`+B和中枢回拉下小信号可积累作用；不把全部1分以下信号当大级反转或取消突发破裂例外。'),
        ('upper-l032-c-stage-pending-third-buy-completion-large-daily-case-and-profit',
         ['third-buy-center-edge-versus-swing-high-strongest', 'sudden-index-fall-destroys-forming-third-buy', 'center-bottom-entry-compare-next-top-third-buy'],
         '33明确不入中枢为三买而不回波动高点仅更强，形成中被急跌破坏就不呈现；未补触边相等的形式规则或认证读者盈利。'),
    ]
    followups = []
    for pending_id, slugs, finding in changes:
        ids = ['upper-l033-c-stage-' + slug for slug in slugs]
        assert pending_id in pending_ids and all(id in known for id in ids)
        followups.append({'pending_id': pending_id, 'status': 'new_source_located_scope_still_pending',
                          'new_claim_ids': ids, 'finding': finding, 'global_pending_not_closed': True, 'graph_version': VERSION})
    (AGENT / 'curation/upper/c_stage_l033.partial-resolutions.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n' for r in followups), encoding='utf-8')
    checks = [
        '50条JSON Schema及引用/身份/映射/坐标预检',
        '109段原文哈希及全段台账一致，实际PDF243至254共12页及7完整图视觉核对',
        '原2300命题3284已复核证据未改，9647段528图逐行比较仅10解盘日期与7图来源备注授权变更',
        '33项当前工作区Node测试通过（原有27项及另行验收的检索评测6项）',
        '2350条已复核命题全量引用校验0错误',
        '6组来源/条件边界及7组CLI/公共/桌面模块一致，12命题13配图关联逐项确认，只读哈希不变',
        '240/240冻结开发取证计划和已标注来源身份回归通过，无新题替换',
        '2350命题/265概念/382关系JSONL及Markdown/coverage同版本导出',
        '6条旧待核补充关联，原问题全部保持开放',
    ]
    not_run = ['240题完整类别/自然问题基线/生成回答评分/消融对抗验收未完成；开发取证计划通过不能代替',
               '34至61共28课完整语义及全书跨课/图文审查未完成',
               '独立Agent打包后运行及Windows真实离线/缩放旋转跨页交互未验收']
    acceptance = '33课50条57证据、10日期与7图来源已发布；2350引用/240冻结开发题回归通过；9待核及全书/产品目标未完成。'
    next_action = f'接续上册34课，实际PDF{next_row[1]}页标题；完整阅读投资思维/情绪论述、解盘和作者答疑，核对技术条件、身份时间及原图。'
    evaluation = {'executable_development_cases': 240, 'target': 240, 'gold_review_status': 'model_reviewed_development',
                  'human_gold_reviewed': False, 'independent_test_set': False, 'generated_answers_scored': False,
                  'retrieval_plan_and_source_identity_passed_on_current_graph': 240, 'full_stage_g_acceptance_complete': False,
                  'new_project_gold_cases_created_in_this_batch': 0,
                  'note': '冻结开发取证计划及本批边界检查通过，不证明完整G、独立金标准或实际桌面交互通过。'}
    path = AUDIT / 'stage-c-l033-publication.json'; pub = read(path)
    assert pub['graph_version'] == VERSION and pub['formal_import'] == 'passed'
    pub.update(updated_at=datetime.now(timezone.utc).isoformat(), checks_run=checks, checks_not_run=not_run,
               acceptance=acceptance, next_action=next_action, exports=exports,
               final_sha256={'database': sha(KB / 'graph.sqlite'), 'manifest': sha(KB / 'manifest.json')},
               development_evaluation=evaluation, partial_pending_followups=6, semantic_completion=False,
               writes_to_knowledge_graph_by_this_finalizer=False)
    write(path, pub)
    path = AGENT / 'curation/progress.json'; progress = read(path)
    assert progress['graph_version'] in ['0.1.0-review-68e03935d1ac', VERSION]
    if progress['graph_version'] != VERSION:
        progress['previous_checkpoint'] = {key: progress[key] for key in ['graph_version', 'completed', 'next_action', 'evaluation']}
    outputs = ['source-audit/stage-c-l033-' + name + '.json' for name in ['source-plan', 'source-applied', 'source-invariants', 'publication', 'verification']]
    progress['machine_outputs'] = list(dict.fromkeys(progress['machine_outputs'] + outputs + ['upper/c_stage_l033.partial-resolutions.jsonl']))
    progress.update(updated_at=datetime.now(timezone.utc).isoformat(), graph_version=VERSION, counts=counts,
                    claim_status_counts=claim_status, figure_origin_counts=figure_status, unit_processing_status_counts=unit_status,
                    semantic_completion=False, completed=[
                        '上册33课109段12页7图同模型四轮审读，50命题57证据12关系支撑发布，新增走势多义性/中枢回拉作用/中枢系统3概念',
                        '10解盘段按3/5 11:56/21:14及3/6 15:22分组，3/2原文与答复日期不污染；7图6文后1原发未核，4月后图不倒证原预测',
                        '原2300命题3284证据及全源原文/字符映射/坐标逐行未改；新增六延伸加初三总九、严格成交递归与周期模本分开，1分过程用15分图不升格',
                        '同向背驰与反向离开比较及MACD同侧回轴/异侧穿轴分对象，a+A+b与b参照不补唯一力度；中枢扩张一对象与扩展原词分开，旧中枢纳大系统非消失',
                        '周线仅日线第一段/若盘至4月或直接上破不成两支保留，三买不入中枢与不回GG更强分开，形成中破坏不等已成撤销；黄白/面积次序需多级配套；9待核',
                        '2350命题/265概念/382关系同版本导出；33工程/2350引用、6边界和7组CLI/公共/桌面模块一致，12命题13配图关联逐项通过',
                        '240冻结开发取证计划与已标注身份回归通过，不增题凑数；6条旧待核补充均开放，余28课',
                    ], pending=[
                        '本批9待核见upper/c_stage_l033.pending.jsonl：初三/新增六递归、模本/合理多义、回拉力度/同反向MACD、周线条件、扩张原词/中枢系统、三买边界、指标优先/小信号、历史预测/观察池、日期/13:37与38/图源',
                        '34至61共28课未完整语义审读；80课有阅读记录含历史62至64，不等全书技术抽取或全部解释统一',
                        '240题完整类别、自然问题基线、生成回答评分、消融对抗与全书跨课/图文审查未完成',
                        '独立Agent实际交付运行及Windows真实离线/缩放旋转跨页交互未验收',
                    ], checks_run=checks, checks_not_run=not_run, acceptance=acceptance,
                    next_resume_anchor=next_anchor, next_action=next_action,
                    coverage_caveat='33课109段12页7图同模型四轮，累计80课阅读记录含历史62至64，不称独立复核或全书完成。',
                    evaluation=evaluation,
                    previous_turn_classification='progress：33课109段7图、10日期修正与50条57证据发布；2350引用/240冻结开发题回归通过，余28课。')
    write(path, progress)
    print(json.dumps({'graph_version': VERSION, 'reviewed': 2350, 'development_cases': 240,
                      'remaining_lessons': 28, 'next_anchor': next_anchor, 'semantic_completion': False}, ensure_ascii=False))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
