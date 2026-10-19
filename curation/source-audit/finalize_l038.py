"""Save verified lesson38 publication and the lesson39 continuation point."""
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2]
KB = AGENT.parent / 'shared-knowledge/v0.1.0'
AUDIT = Path(__file__).resolve().parent
VERSION = '0.1.0-review-0cc5c3d74a49'


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
                              concepts=275, claims=5161, evidence=6180, relations=433, reviews=2592)
        claim_status = db.execute('SELECT review_status,COUNT(*) FROM claims GROUP BY review_status ORDER BY review_status').fetchall()
        figure_status = db.execute('SELECT origin_status,COUNT(*) FROM figures GROUP BY origin_status ORDER BY origin_status').fetchall()
        unit_status = db.execute('SELECT processing_status,COUNT(*) FROM units GROUP BY processing_status ORDER BY processing_status').fetchall()
        assert dict(claim_status) == {'pending': 2612, 'rejected': 27, 'reviewed': 2522}
        assert dict(unit_status)['extracted'] == 23
        assert db.execute("SELECT COUNT(*) FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed'").fetchone()[0] == 3541
        next_row = db.execute("SELECT id,pdf_page,text FROM passages WHERE unit_id='lesson-039' ORDER BY pdf_page,block_index,id LIMIT 1").fetchone()
        assert next_row and next_row[2].startswith('教你炒股票39')
        next_anchor = next_row[0] + ' / lesson-039'
        known = {r[0] for r in db.execute("SELECT id FROM claims WHERE review_status='reviewed'")}
    finally:
        db.close()
    assert read(KB / 'manifest.json')['graph_version'] == VERSION
    exports = {}
    for name, number in [('claims', 2522), ('concepts', 275), ('relations', 433)]:
        path = KB / 'exports' / f'{name}.jsonl'
        rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
        assert len(rows) == number and all(r['graph_version'] == VERSION for r in rows)
        exports[name] = {'rows': number, 'graph_version': VERSION, 'sha256': sha(path)}
    assert VERSION in (KB / 'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150]
    assert read(KB / 'exports/coverage.json')['graph_version'] == VERSION
    inv = read(AUDIT / 'stage-c-l038-source-invariants.json')
    assert inv['pass'] and inv['graph_version'] == VERSION
    assert inv['original_reviewed_claims_unchanged'] == 2482 and inv['original_reviewed_evidence_unchanged'] == 3498
    verification = read(AUDIT / 'stage-c-l038-verification.json')
    assert verification['pass'] and verification['graph_version'] == VERSION
    assert len(verification['checks']) == 6 and len(verification['parity']) == 7
    assert verification['intended_figure_links_checked'] == dict(claims=10, associations=10, unique_figures=4)
    dev = read(AGENT / 'evaluation/stage-g-development-current.results.json')
    assert dev['graph_version'] == VERSION and dev['executable_development_cases'] == dev['retrieval_plan_contract_passed'] == 240
    assert all(r['source_identity_matches_expected'] for r in dev['observations'])
    pending_ids = set()
    for n in [33, 34, 35, 36, 37]:
        pending_ids.update(json.loads(line)['id'] for line in (AGENT / 'curation/upper' / f'c_stage_l{n:03d}.pending.jsonl').read_text(encoding='utf-8').splitlines() if line.strip())
    changes = [
        ('upper-l036-c-stage-pending-multiple-combinations-not-vague-and-completion-scope',
         ['same-level-decomposition-fixed-level-definition', 'good-rule-unique-and-same-level-uniqueness-author-claim', 'hybrid-rule-own-level-all-below-and-above-ignored'],
         '38固定规则内唯一与跨规则合法多义分层，本级/低层/高层作用域不同；未给完整形式证明或统一所有合法分法为一个切点集合。'),
        ('upper-l035-c-stage-pending-single-type-connections-regrouping-and-associative-scope',
         ['consolidation-plus-consolidation-allowed-only-mode-scope', 'sublevels-need-not-use-same-mode-can-extend', 'same-level-no-extension-three-overlap-six-two-consolidations'],
         '38特设本级允许盘整+盘整、六小段作两盘整，但低层仍沿延伸/扩展；不改单个5分类型不能含30分中心或原定义完成约束。'),
        ('upper-l033-c-stage-pending-extension-initial-three-added-six-and-recursive-level',
         ['same-level-no-extension-three-overlap-six-two-consolidations', 'hybrid-rule-own-level-all-below-and-above-ignored'],
         '38六次级类型作两个本级盘整是特定同级模式，总六非33新增六加初三；不混六/九K数，非取消其他分解的延伸升级条件。'),
        ('upper-l036-c-stage-pending-third-buy-repeated-exit-first-retest-and-late-center-frequency',
         ['return-first-not-third-later-not-return-can-be-third', 'first-effective-retest-only-later-no-return-not-third', 'two-subsub-retests-complete-one-sublevel-retest'],
         '38明确前次回中枢仍震荡、首有效不回才三买，已成后再不回非再同心三买；内部两次次次级完成一次次级。晚第4/5中心频率和触边全规则仍未核。'),
        ('upper-l037-c-stage-pending-all-points-first-level-and-third-after-paths',
         ['third-point-and-center-extension-end-same-object', 'two-subsub-retests-complete-one-sublevel-retest', 'segmentation-and-third-end-confirmation-internal-divergence'],
         '38补次级回抽内部完成和盘整结束须内背驰/盘背，三买同中枢延伸结束按对象；未提供所有点固定次级/次次级数学证明或预知未来两支算法。'),
        ('upper-l037-c-stage-pending-consolidation-divergence-comparable-force-and-trend-end',
         ['abc-macd-five-chart-ac-compare-c-internal-precision', 'consolidation-c-need-not-highest-no-new-high-weak-macd-aux'],
         '38说明盘整ABC之C可不新高，A/C比较和C内精确分两层；不撤37趋势末c创新高低条件，刚上轴问仍未单独答，未给唯一力度公式。'),
        ('upper-l034-c-stage-pending-chosen-level-exit-not-second-noise-or-perfect-execution',
         ['different-position-portions-at-different-levels', 'nested-divergence-exit-staged-by-capital', 'miss-first-sell-use-second-not-wait-third'],
         '38分仓各级信号与容量下分批退出，首二卖纪律不等全仓秒级噪音；仍无仓位阈值、EPS/固定K数或理想成交保证。'),
    ]
    followups = []
    for pending_id, slugs, finding in changes:
        ids = ['upper-l038-c-stage-' + slug for slug in slugs]
        assert pending_id in pending_ids and all(id in known for id in ids)
        followups.append({'pending_id': pending_id, 'status': 'new_source_located_scope_still_pending',
                          'new_claim_ids': ids, 'finding': finding, 'global_pending_not_closed': True, 'graph_version': VERSION})
    (AGENT / 'curation/upper/c_stage_l038.partial-resolutions.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n' for r in followups), encoding='utf-8')
    checks = [
        '40条JSON Schema及引用/身份/映射/坐标预检',
        '75段原文哈希及全段台账一致，实际PDF280至287共8页4完整图及后课边界视觉核对',
        '原2482命题3498已复核证据未改，9647段528图逐行比较仅3跨日来源日期与4图来源备注授权变更',
        '33项当前工作区Node测试通过（原有27项及另行验收的检索评测6项）',
        '2522条已复核命题全量引用校验0错误',
        '6组来源/条件边界及7组CLI/公共/桌面模块一致，10命题10配图关联逐项确认，只读哈希不变',
        '240/240冻结开发取证计划和已标注来源身份回归通过，无新题替换',
        '2522命题/275概念/433关系JSONL及Markdown/coverage同版本导出',
        '7条旧待核补充关联，原问题全部保持开放',
    ]
    not_run = ['240题完整类别/自然问题基线/生成回答评分/消融对抗验收未完成；开发取证计划通过不能代替',
               '39至61共23课完整语义及全书跨课/图文审查未完成',
               '独立Agent打包后运行及Windows真实离线/缩放旋转跨页交互未验收']
    acceptance = '38课40条43证据、3日期与4图来源已发布；2522引用/240冻结开发题回归通过；8待核及全书/产品目标未完成。'
    next_action = f'接续上册39课，实际PDF{next_row[1]}页标题；完整阅读同级别分解再研究、机械节奏/递归及解盘答疑，核对类型完成、相等边界和原图。'
    evaluation = {'executable_development_cases': 240, 'target': 240, 'gold_review_status': 'model_reviewed_development',
                  'human_gold_reviewed': False, 'independent_test_set': False, 'generated_answers_scored': False,
                  'retrieval_plan_and_source_identity_passed_on_current_graph': 240, 'full_stage_g_acceptance_complete': False,
                  'new_project_gold_cases_created_in_this_batch': 0,
                  'note': '冻结开发取证计划及本批边界检查通过，不证明完整G、独立金标准或实际桌面交互通过。'}
    path = AUDIT / 'stage-c-l038-publication.json'; pub = read(path)
    assert pub['graph_version'] == VERSION and pub['formal_import'] == 'passed'
    assert list(pub['batch_sha256'].values()) == [sha(AGENT / 'curation/upper/c_stage_l038.reviewed.jsonl')]
    pub.update(updated_at=datetime.now(timezone.utc).isoformat(), checks_run=checks, checks_not_run=not_run,
               acceptance=acceptance, next_action=next_action, exports=exports,
               final_sha256={'database': sha(KB / 'graph.sqlite'), 'manifest': sha(KB / 'manifest.json')},
               development_evaluation=evaluation, partial_pending_followups=7, semantic_completion=False,
               writes_to_knowledge_graph_by_this_finalizer=False)
    write(path, pub)
    path = AGENT / 'curation/progress.json'; progress = read(path)
    assert progress['graph_version'] in ['0.1.0-review-fb1a6407424c', VERSION]
    if progress['graph_version'] != VERSION:
        progress['previous_checkpoint'] = {key: progress[key] for key in ['graph_version', 'completed', 'next_action', 'evaluation']}
    outputs = ['source-audit/stage-c-l038-' + name + '.json' for name in ['source-plan', 'source-applied', 'source-invariants', 'publication', 'verification']]
    progress['machine_outputs'] = list(dict.fromkeys(progress['machine_outputs'] + outputs + ['upper/c_stage_l038.partial-resolutions.jsonl']))
    progress.update(updated_at=datetime.now(timezone.utc).isoformat(), graph_version=VERSION, counts=counts,
                    claim_status_counts=claim_status, figure_origin_counts=figure_status, unit_processing_status_counts=unit_status,
                    semantic_completion=False, completed=[
                        '上册38课75段8页4图同模型四轮审读，40命题43证据13关系支撑发布，新增同级别分解概念',
                        '3解盘来源段改3/22 15:29:02，前3/21及尾头字符不改；4图全后加，281为2009读者示意不作作者原图，光标旧日期不掩后行情',
                        '原2482命题3498证据及全源原文/字符映射/坐标逐行未改；同级固定规则内唯一为作者未全证主张，本级允许盘整+盘整而低层仍可延伸',
                        '本级六小类型作两盘整非新增六或六K，以上级别只本视角不考虑；30分程式全部二下/三上分支和逆向操作保存，等高/EPS/实时成交未擅补；8待核',
                        '三买首有效不回、前次回中枢仍震荡、成三买后再不回非再同心三买；次次级两次完成一次次级。盘整C非趋势末c，MACD看5分仍A/C加C内，刚上轴未答',
                        '按容量区间套分批退出与首二卖纪律保存，沪深背离非MACD技术背驰；3/20近远答为汇编重复只留台账，利润线性/永不败等历史强主张未核',
                        '2522命题/275概念/433关系同版本导出；33工程/2522引用、6边界和7组CLI/公共/桌面模块一致，10命题10配图关联逐项通过',
                        '240冻结开发取证计划与已标注身份回归通过，不增题凑数；7条旧待核补充均开放，余23课',
                    ], pending=[
                        '本批8待核见upper/c_stage_l038.pending.jsonl：规则内唯一/未证、六小段盘整连接、机械等高/成交/利润、首有效回抽和次次级、盘整C/0轴未答、容量退出、历史自述、日期/后图/重复源',
                        '39至61共23课未完整语义审读；85课有阅读记录含历史62至64，不等全书技术抽取或全部解释统一',
                        '240题完整类别、自然问题基线、生成回答评分、消融对抗与全书跨课/图文审查未完成',
                        '独立Agent实际交付运行及Windows真实离线/缩放旋转跨页交互未验收',
                    ], checks_run=checks, checks_not_run=not_run, acceptance=acceptance,
                    next_resume_anchor=next_anchor, next_action=next_action,
                    coverage_caveat='38课75段8页4图同模型四轮，累计85课阅读记录含历史62至64，不称独立复核或全书完成。',
                    evaluation=evaluation,
                    previous_turn_classification='progress：38课75段4图、3日期修正与40条43证据发布；2522引用/240冻结开发题回归通过，余23课。')
    write(path, progress)
    print(json.dumps({'graph_version': VERSION, 'reviewed': 2522, 'development_cases': 240,
                      'remaining_lessons': 23, 'next_anchor': next_anchor, 'semantic_completion': False}, ensure_ascii=False))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
