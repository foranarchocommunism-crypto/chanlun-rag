"""Save verified lesson34 publication and the lesson35 continuation point."""
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2]
KB = AGENT.parent / 'shared-knowledge/v0.1.0'
AUDIT = Path(__file__).resolve().parent
VERSION = '0.1.0-review-20e3aa53bf69'


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
                              concepts=266, claims=5005, evidence=5999, relations=387, reviews=2436)
        claim_status = db.execute('SELECT review_status,COUNT(*) FROM claims GROUP BY review_status ORDER BY review_status').fetchall()
        figure_status = db.execute('SELECT origin_status,COUNT(*) FROM figures GROUP BY origin_status ORDER BY origin_status').fetchall()
        unit_status = db.execute('SELECT processing_status,COUNT(*) FROM units GROUP BY processing_status ORDER BY processing_status').fetchall()
        assert dict(claim_status) == {'pending': 2612, 'rejected': 27, 'reviewed': 2366}
        assert dict(unit_status)['extracted'] == 27
        assert db.execute("SELECT COUNT(*) FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed'").fetchone()[0] == 3360
        next_row = db.execute("SELECT id,pdf_page,text FROM passages WHERE unit_id='lesson-035' ORDER BY pdf_page,block_index,id LIMIT 1").fetchone()
        assert next_row and next_row[2].startswith('教你炒股票35')
        next_anchor = next_row[0] + ' / lesson-035'
        known = {r[0] for r in db.execute("SELECT id FROM claims WHERE review_status='reviewed'")}
    finally:
        db.close()
    assert read(KB / 'manifest.json')['graph_version'] == VERSION
    exports = {}
    for name, number in [('claims', 2366), ('concepts', 266), ('relations', 387)]:
        path = KB / 'exports' / f'{name}.jsonl'
        rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
        assert len(rows) == number and all(r['graph_version'] == VERSION for r in rows)
        exports[name] = {'rows': number, 'graph_version': VERSION, 'sha256': sha(path)}
    assert VERSION in (KB / 'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150]
    assert read(KB / 'exports/coverage.json')['graph_version'] == VERSION
    inv = read(AUDIT / 'stage-c-l034-source-invariants.json')
    assert inv['pass'] and inv['graph_version'] == VERSION
    assert inv['original_reviewed_claims_unchanged'] == 2350 and inv['original_reviewed_evidence_unchanged'] == 3341
    verification = read(AUDIT / 'stage-c-l034-verification.json')
    assert verification['pass'] and verification['graph_version'] == VERSION
    assert len(verification['checks']) == 6 and len(verification['parity']) == 7
    assert verification['intended_figure_links_checked'] == dict(claims=4, associations=8, unique_figures=5)
    dev = read(AGENT / 'evaluation/stage-g-development-current.results.json')
    assert dev['graph_version'] == VERSION and dev['executable_development_cases'] == dev['retrieval_plan_contract_passed'] == 240
    assert all(r['source_identity_matches_expected'] for r in dev['observations'])
    pending_ids = set()
    for n in [30, 31, 32, 33]:
        pending_ids.update(json.loads(line)['id'] for line in (AGENT / 'curation/upper' / f'c_stage_l{n:03d}.pending.jsonl').read_text(encoding='utf-8').splitlines() if line.strip())
    changes = [
        ('upper-l030-c-stage-pending-entered-leg-breakage-versus-guaranteed-result',
         ['current-level-by-capital-and-tolerance-not-second', 'exit-when-chosen-level-actual-path-opposes-operation'],
         '34补充当下是资金承受所选级别，实际相反尽快退出；未给定量触发/成交保证，不等每秒噪音或入背驰段保证安全。'),
        ('upper-l031-c-stage-pending-parent-leg-main-rise-main-fall-and-event-exception',
         ['rotation-no-chase-but-five-main-rise-not-all-small-exits', 'beast-reflex-after-danger-no-emotional-shadow'],
         '34给5分主升下不应每次次1背驰都跑的范围，识险为比喻；不取消33中枢回拉下小信号重要及突发事件边界。'),
        ('upper-l032-c-stage-pending-third-buy-completion-large-daily-case-and-profit',
         ['third-buy-confirm-look-inside-sublevel', 'mar8-five-retest-not-back-2858-thirty-third-buy'],
         '34明确需看次级内部，并给5分回试不回原30分中枢的具体作者判例；仍不补统一等K数算法、触边相等规则或读者收益证明。'),
        ('upper-l033-c-stage-pending-third-buy-edge-gg-and-forming-invalidated',
         ['mar7-2915-stable-third-buy-or-two-range-shapes', 'mar8-five-retest-not-back-2858-thirty-third-buy', 'mar8-can-return-five-and-expand-new-thirty'],
         '34分清3/7联合要求、3/8已判三买、2915突破待确认和未来新30分可能；不倒改旧GG/ZG或以后图证明已知未来。'),
        ('upper-l033-c-stage-pending-indicator-priority-and-small-signal-context',
         ['a-plus-b-plus-b-area-sum-not-maximum-bar', 'five-center-formed-prior-close-later-pull-and-gap-oscillate', 'rotation-no-chase-but-five-main-rise-not-all-small-exits'],
         '34具体a+B+b比较用面积非最长柱，纯中枢角度前晚已成；保留33一般黄白线/多级配套和不同小信号对象，未强立全局单指标优先。'),
    ]
    followups = []
    for pending_id, slugs, finding in changes:
        ids = ['upper-l034-c-stage-' + slug for slug in slugs]
        assert pending_id in pending_ids and all(id in known for id in ids)
        followups.append({'pending_id': pending_id, 'status': 'new_source_located_scope_still_pending',
                          'new_claim_ids': ids, 'finding': finding, 'global_pending_not_closed': True, 'graph_version': VERSION})
    (AGENT / 'curation/upper/c_stage_l034.partial-resolutions.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n' for r in followups), encoding='utf-8')
    checks = [
        '16条JSON Schema及引用/身份/映射/坐标预检',
        '37段原文哈希及全段台账一致，实际PDF254至259共6页、5本课完整图及254前课图边界视觉核对',
        '原2350命题3341已复核证据未改，9647段528图逐行比较仅5来源日期与5图来源备注授权变更',
        '33项当前工作区Node测试通过（原有27项及另行验收的检索评测6项）',
        '2366条已复核命题全量引用校验0错误',
        '6组来源/条件边界及7组CLI/公共/桌面模块一致，4命题8配图关联逐项确认，只读哈希不变',
        '240/240冻结开发取证计划和已标注来源身份回归通过，无新题替换',
        '2366命题/266概念/387关系JSONL及Markdown/coverage同版本导出',
        '5条旧待核补充关联，原问题全部保持开放',
    ]
    not_run = ['240题完整类别/自然问题基线/生成回答评分/消融对抗验收未完成；开发取证计划通过不能代替',
               '35至61共27课完整语义及全书跨课/图文审查未完成',
               '独立Agent打包后运行及Windows真实离线/缩放旋转跨页交互未验收']
    acceptance = '34课16条19证据、5日期与5本课图来源已发布；2366引用/240冻结开发题回归通过；6待核及全书/产品目标未完成。'
    next_action = f'接续上册35课，实际PDF{next_row[1]}页标题；完整阅读中枢/走势类型基础定义、解盘及答疑，核对级别条件、短答范围和配图。'
    evaluation = {'executable_development_cases': 240, 'target': 240, 'gold_review_status': 'model_reviewed_development',
                  'human_gold_reviewed': False, 'independent_test_set': False, 'generated_answers_scored': False,
                  'retrieval_plan_and_source_identity_passed_on_current_graph': 240, 'full_stage_g_acceptance_complete': False,
                  'new_project_gold_cases_created_in_this_batch': 0,
                  'note': '冻结开发取证计划及本批边界检查通过，不证明完整G、独立金标准或实际桌面交互通过。'}
    path = AUDIT / 'stage-c-l034-publication.json'; pub = read(path)
    assert pub['graph_version'] == VERSION and pub['formal_import'] == 'passed'
    assert list(pub['batch_sha256'].values()) == [sha(AGENT / 'curation/upper/c_stage_l034.reviewed.jsonl')]
    pub.update(updated_at=datetime.now(timezone.utc).isoformat(), checks_run=checks, checks_not_run=not_run,
               acceptance=acceptance, next_action=next_action, exports=exports,
               final_sha256={'database': sha(KB / 'graph.sqlite'), 'manifest': sha(KB / 'manifest.json')},
               development_evaluation=evaluation, partial_pending_followups=5, semantic_completion=False,
               writes_to_knowledge_graph_by_this_finalizer=False)
    write(path, pub)
    path = AGENT / 'curation/progress.json'; progress = read(path)
    assert progress['graph_version'] in ['0.1.0-review-2c7fb5f929d2', VERSION]
    if progress['graph_version'] != VERSION:
        progress['previous_checkpoint'] = {key: progress[key] for key in ['graph_version', 'completed', 'next_action', 'evaluation']}
    outputs = ['source-audit/stage-c-l034-' + name + '.json' for name in ['source-plan', 'source-applied', 'source-invariants', 'publication', 'verification']]
    progress['machine_outputs'] = list(dict.fromkeys(progress['machine_outputs'] + outputs + ['upper/c_stage_l034.partial-resolutions.jsonl']))
    progress.update(updated_at=datetime.now(timezone.utc).isoformat(), graph_version=VERSION, counts=counts,
                    claim_status_counts=claim_status, figure_origin_counts=figure_status, unit_processing_status_counts=unit_status,
                    semantic_completion=False, completed=[
                        '上册34课37段6页5本课图同模型四轮审读，16命题19证据5关系支撑发布，新增正闻正见正学正行概念',
                        '5来源段按3/8 15:30:24修正，3/7前段不改；5本课图均文章后行情，254前课图仅核边界不重复归属',
                        '原2350命题3341证据及全源原文/字符映射/坐标逐行未改；四正为当下释义，走势含一切秘密及等归零概率只作作者主张',
                        '当下按资金承受选定级别而非每秒；逆选定级别尽快退出，野兽识险不当可预知风险保证；5分主升小信号用途与33中枢回拉情境分开',
                        '三买判例、2915突破待确认及未来新30分可能分对象；前后短答指代不唯一，不造组合裸中枢规则；a+B+b原记号面积非峰值不推翻全局指标优先；6待核',
                        '2366命题/266概念/387关系同版本导出；33工程/2366引用、6边界和7组CLI/公共/桌面模块一致，4命题8配图关联逐项通过',
                        '240冻结开发取证计划与已标注身份回归通过，不增题凑数；5条旧待核补充均开放，余27课',
                    ], pending=[
                        '本批6待核见upper/c_stage_l034.pending.jsonl：修辞/四正/等归零概率、选定级别退出、2915与原新中枢、前后短答指代、面积/前晚已成、跨日来源和后图',
                        '35至61共27课未完整语义审读；81课有阅读记录含历史62至64，不等全书技术抽取或全部解释统一',
                        '240题完整类别、自然问题基线、生成回答评分、消融对抗与全书跨课/图文审查未完成',
                        '独立Agent实际交付运行及Windows真实离线/缩放旋转跨页交互未验收',
                    ], checks_run=checks, checks_not_run=not_run, acceptance=acceptance,
                    next_resume_anchor=next_anchor, next_action=next_action,
                    coverage_caveat='34课37段6页5本课图同模型四轮，累计81课阅读记录含历史62至64，不称独立复核或全书完成。',
                    evaluation=evaluation,
                    previous_turn_classification='progress：34课37段5本课图、5来源日期修正与16条19证据发布；2366引用/240冻结开发题回归通过，余27课。')
    write(path, progress)
    print(json.dumps({'graph_version': VERSION, 'reviewed': 2366, 'development_cases': 240,
                      'remaining_lessons': 27, 'next_anchor': next_anchor, 'semantic_completion': False}, ensure_ascii=False))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
