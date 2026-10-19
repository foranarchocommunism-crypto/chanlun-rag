"""Save verified lesson36 publication and the lesson37 continuation point."""
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2]
KB = AGENT.parent / 'shared-knowledge/v0.1.0'
AUDIT = Path(__file__).resolve().parent
VERSION = '0.1.0-review-4867e2d2c06f'


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
                              concepts=272, claims=5082, evidence=6093, relations=410, reviews=2513)
        claim_status = db.execute('SELECT review_status,COUNT(*) FROM claims GROUP BY review_status ORDER BY review_status').fetchall()
        figure_status = db.execute('SELECT origin_status,COUNT(*) FROM figures GROUP BY origin_status ORDER BY origin_status').fetchall()
        unit_status = db.execute('SELECT processing_status,COUNT(*) FROM units GROUP BY processing_status ORDER BY processing_status').fetchall()
        assert dict(claim_status) == {'pending': 2612, 'rejected': 27, 'reviewed': 2443}
        assert dict(unit_status)['extracted'] == 25
        assert db.execute("SELECT COUNT(*) FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed'").fetchone()[0] == 3454
        next_row = db.execute("SELECT id,pdf_page,text FROM passages WHERE unit_id='lesson-037' ORDER BY pdf_page,block_index,id LIMIT 1").fetchone()
        assert next_row and next_row[2].startswith('教你炒股票37')
        next_anchor = next_row[0] + ' / lesson-037'
        known = {r[0] for r in db.execute("SELECT id FROM claims WHERE review_status='reviewed'")}
    finally:
        db.close()
    assert read(KB / 'manifest.json')['graph_version'] == VERSION
    exports = {}
    for name, number in [('claims', 2443), ('concepts', 272), ('relations', 410)]:
        path = KB / 'exports' / f'{name}.jsonl'
        rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
        assert len(rows) == number and all(r['graph_version'] == VERSION for r in rows)
        exports[name] = {'rows': number, 'graph_version': VERSION, 'sha256': sha(path)}
    assert VERSION in (KB / 'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150]
    assert read(KB / 'exports/coverage.json')['graph_version'] == VERSION
    inv = read(AUDIT / 'stage-c-l036-source-invariants.json')
    assert inv['pass'] and inv['graph_version'] == VERSION
    assert inv['original_reviewed_claims_unchanged'] == 2408 and inv['original_reviewed_evidence_unchanged'] == 3406
    verification = read(AUDIT / 'stage-c-l036-verification.json')
    assert verification['pass'] and verification['graph_version'] == VERSION
    assert len(verification['checks']) == 6 and len(verification['parity']) == 7
    assert verification['intended_figure_links_checked'] == dict(claims=5, associations=11, unique_figures=4, reader_context_figures_not_attached_to_author_claims=1)
    dev = read(AGENT / 'evaluation/stage-g-development-current.results.json')
    assert dev['graph_version'] == VERSION and dev['executable_development_cases'] == dev['retrieval_plan_contract_passed'] == 240
    assert all(r['source_identity_matches_expected'] for r in dev['observations'])
    pending_ids = set()
    for n in [33, 34, 35]:
        pending_ids.update(json.loads(line)['id'] for line in (AGENT / 'curation/upper' / f'c_stage_l{n:03d}.pending.jsonl').read_text(encoding='utf-8').splitlines() if line.strip())
    changes = [
        ('upper-l035-c-stage-pending-single-type-connections-regrouping-and-associative-scope',
         ['associativity-mixed-levels-and-multiple-not-vague', 'completion-depends-on-level-two-five-not-thirty-complete', 'mixed-five-thirty-redivide-regroup-last-unfinished'],
         '36展开异级结合、低已完非高已完、先低分后依中枢重组及末项未完成；仍不允许交换时序或任意拼段，不补所有分解唯一性证明。'),
        ('upper-l035-c-stage-pending-buy-sell-level-theorem-below-not-all-levels',
         ['five-leave-and-retest-may-thirty-third-not-daily', 'after-thirty-third-can-return-daily-via-thirty-type', 'daily-operator-attend-early-thirty-third-if-trend'],
         '36给5分离开/回抽可30分三买非日三买，之后仍可回日中枢；若真形成日三买则较小信号先出，未把任何小点必大点或相对安全当无风险。'),
        ('upper-l035-c-stage-pending-third-buy-followed-by-expansion-dated-center-range',
         ['regroup-mar8-retest-into-mar5-up-new-start-mar9-1030', 'simplify-unfinished-second-center-not-cancel-expansion-definition', 'chosen-combination-must-use-own-center-third-buy-boundary'],
         '36可保留旧3/7 2892至2911或用新3/9 2905至2947，但三买阈值须随所选组合；未完第二中枢重组不取消两已完中枢扩展，图文时分差仍开放。'),
        ('upper-l033-c-stage-pending-extension-initial-three-added-six-and-recursive-level',
         ['stay-around-daily-eventually-thirty-last-a-m-less-nine', 'daily-oscillation-can-below-thirty-even-gap'],
         '36日中枢围绕震荡式m<9以30分段计、否则改周/日分解，非K线或自然日；仍需与33初三/新增六及完成/重叠全部语境合读。'),
        ('upper-l034-c-stage-pending-area-versus-peak-and-center-formed-state',
         ['abc-compare-ac-consolidation-divergence-and-c-internal', 'completion-depends-on-level-two-five-not-thirty-complete'],
         '36明确A/C盘整背驰与C内部小背驰配合，两级完成分开；未把面积一项变成充分算法或回写34原a+B+b记号。'),
        ('upper-l035-c-stage-pending-gap-treatment-running-type-and-reader-endorsement',
         ['ipo-open-gap-short-answer-original-wording-unclear', 'third-buy-sublevel-leave-retest-not-reenter-general-answer'],
         '36新股开盘缺口短答原文不顺，保留而不补首段统一方向；读者三买辩论非作者，末尾作者答次级离开/回抽不回单独存，不扩整段读者获认可。'),
    ]
    followups = []
    for pending_id, slugs, finding in changes:
        ids = ['upper-l036-c-stage-' + slug for slug in slugs]
        assert pending_id in pending_ids and all(id in known for id in ids)
        followups.append({'pending_id': pending_id, 'status': 'new_source_located_scope_still_pending',
                          'new_claim_ids': ids, 'finding': finding, 'global_pending_not_closed': True, 'graph_version': VERSION})
    (AGENT / 'curation/upper/c_stage_l036.partial-resolutions.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n' for r in followups), encoding='utf-8')
    checks = [
        '35条JSON Schema及引用/身份/映射/坐标预检',
        '89段原文哈希及全段台账一致，实际PDF265至273共9页5完整图及前后课边界视觉核对',
        '原2408命题3406已复核证据未改，9647段528图逐行比较仅5附录日级时间与5图来源备注授权变更',
        '33项当前工作区Node测试通过（原有27项及另行验收的检索评测6项）',
        '2443条已复核命题全量引用校验0错误',
        '6组来源/条件边界及7组CLI/公共/桌面模块一致，5命题11配图关联逐项确认，1读者图未挂作者命题，只读哈希不变',
        '240/240冻结开发取证计划和已标注来源身份回归通过，无新题替换',
        '2443命题/272概念/410关系JSONL及Markdown/coverage同版本导出',
        '6条旧待核补充关联，原问题全部保持开放',
    ]
    not_run = ['240题完整类别/自然问题基线/生成回答评分/消融对抗验收未完成；开发取证计划通过不能代替',
               '37至61共25课完整语义及全书跨课/图文审查未完成',
               '独立Agent打包后运行及Windows真实离线/缩放旋转跨页交互未验收']
    acceptance = '36课35条48证据、5附录日级时间与5图来源已发布；2443引用/240冻结开发题回归通过；8待核及全书/产品目标未完成。'
    next_action = f'接续上册37课，实际PDF{next_row[1]}页标题；完整阅读背驰再分辨、同级/趋势/次级c条件及解盘答疑，核对原图、身份与跨课边界。'
    evaluation = {'executable_development_cases': 240, 'target': 240, 'gold_review_status': 'model_reviewed_development',
                  'human_gold_reviewed': False, 'independent_test_set': False, 'generated_answers_scored': False,
                  'retrieval_plan_and_source_identity_passed_on_current_graph': 240, 'full_stage_g_acceptance_complete': False,
                  'new_project_gold_cases_created_in_this_batch': 0,
                  'note': '冻结开发取证计划及本批边界检查通过，不证明完整G、独立金标准或实际桌面交互通过。'}
    path = AUDIT / 'stage-c-l036-publication.json'; pub = read(path)
    assert pub['graph_version'] == VERSION and pub['formal_import'] == 'passed'
    assert list(pub['batch_sha256'].values()) == [sha(AGENT / 'curation/upper/c_stage_l036.reviewed.jsonl')]
    pub.update(updated_at=datetime.now(timezone.utc).isoformat(), checks_run=checks, checks_not_run=not_run,
               acceptance=acceptance, next_action=next_action, exports=exports,
               final_sha256={'database': sha(KB / 'graph.sqlite'), 'manifest': sha(KB / 'manifest.json')},
               development_evaluation=evaluation, partial_pending_followups=6, semantic_completion=False,
               writes_to_knowledge_graph_by_this_finalizer=False)
    write(path, pub)
    path = AGENT / 'curation/progress.json'; progress = read(path)
    assert progress['graph_version'] in ['0.1.0-review-bee490a04fe7', VERSION]
    if progress['graph_version'] != VERSION:
        progress['previous_checkpoint'] = {key: progress[key] for key in ['graph_version', 'completed', 'next_action', 'evaluation']}
    outputs = ['source-audit/stage-c-l036-' + name + '.json' for name in ['source-plan', 'source-applied', 'source-invariants', 'publication', 'verification']]
    progress['machine_outputs'] = list(dict.fromkeys(progress['machine_outputs'] + outputs + ['upper/c_stage_l036.partial-resolutions.jsonl']))
    progress.update(updated_at=datetime.now(timezone.utc).isoformat(), graph_version=VERSION, counts=counts,
                    claim_status_counts=claim_status, figure_origin_counts=figure_status, unit_processing_status_counts=unit_status,
                    semantic_completion=False, completed=[
                        '上册36课89段9页5图同模型四轮审读，35命题48证据12关系支撑发布，新增新股/二线股/三线股3概念',
                        '3/14附录5段脱离08:58晨帖只存日级时间，晨帖与3/15独立；5图4文后1原发未核，270读者图不挂作者命题，图文时分差不静改',
                        '原2408命题3406证据及全源原文/字符映射/坐标逐行未改；下标抽取串段依原页释义不改底本，多义非含糊、低层已完非高层已完',
                        '未完第二中枢可重组非取消扩展定义；新旧组合2905至2947/2892至2911与三买边界联动，旧时点记录不回写；图13:25/10:05和文13:30/10:30差异保留',
                        '日中枢围绕可低级/缺口，m<9计30分段非K/日；早30分三买非日三买且仍可返回，若/往往/适量和相对安全作者强词分层；8待核',
                        'A/C盘整背驰与C内部小背驰配合，IPO短答原字不补，二三线俗称非官方/股本；读者改革与三买争论独立，晚4/5中枢几乎百分百和IPO利润主张无样本不认证',
                        '2443命题/272概念/410关系同版本导出；33工程/2443引用、6边界和7组CLI/公共/桌面模块一致，5命题11配图关联逐项通过',
                        '240冻结开发取证计划与已标注身份回归通过，不增题凑数；6条旧待核补充均开放，余25课',
                    ], pending=[
                        '本批8待核见upper/c_stage_l036.pending.jsonl：多义/完成、重组区间与图文时间差、m计数、早30分三买与相对安全、首次回抽/晚中枢频率、新股短答/俗称、历史强主张、日级附录/图源',
                        '37至61共25课未完整语义审读；83课有阅读记录含历史62至64，不等全书技术抽取或全部解释统一',
                        '240题完整类别、自然问题基线、生成回答评分、消融对抗与全书跨课/图文审查未完成',
                        '独立Agent实际交付运行及Windows真实离线/缩放旋转跨页交互未验收',
                    ], checks_run=checks, checks_not_run=not_run, acceptance=acceptance,
                    next_resume_anchor=next_anchor, next_action=next_action,
                    coverage_caveat='36课89段9页5图同模型四轮，累计83课阅读记录含历史62至64，不称独立复核或全书完成。',
                    evaluation=evaluation,
                    previous_turn_classification='progress：36课89段5图、5附录日级时间与35条48证据发布；2443引用/240冻结开发题回归通过，余25课。')
    write(path, progress)
    print(json.dumps({'graph_version': VERSION, 'reviewed': 2443, 'development_cases': 240,
                      'remaining_lessons': 25, 'next_anchor': next_anchor, 'semantic_completion': False}, ensure_ascii=False))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
