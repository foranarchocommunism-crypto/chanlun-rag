"""Save verified lesson35 publication and the lesson36 continuation point."""
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2]
KB = AGENT.parent / 'shared-knowledge/v0.1.0'
AUDIT = Path(__file__).resolve().parent
VERSION = '0.1.0-review-bee490a04fe7'


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
                              concepts=269, claims=5047, evidence=6045, relations=400, reviews=2478)
        claim_status = db.execute('SELECT review_status,COUNT(*) FROM claims GROUP BY review_status ORDER BY review_status').fetchall()
        figure_status = db.execute('SELECT origin_status,COUNT(*) FROM figures GROUP BY origin_status ORDER BY origin_status').fetchall()
        unit_status = db.execute('SELECT processing_status,COUNT(*) FROM units GROUP BY processing_status ORDER BY processing_status').fetchall()
        assert dict(claim_status) == {'pending': 2612, 'rejected': 27, 'reviewed': 2408}
        assert dict(unit_status)['extracted'] == 26
        assert db.execute("SELECT COUNT(*) FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed'").fetchone()[0] == 3406
        next_row = db.execute("SELECT id,pdf_page,text FROM passages WHERE unit_id='lesson-036' ORDER BY pdf_page,block_index,id LIMIT 1").fetchone()
        assert next_row and next_row[2].startswith('教你炒股票36')
        next_anchor = next_row[0] + ' / lesson-036'
        known = {r[0] for r in db.execute("SELECT id FROM claims WHERE review_status='reviewed'")}
    finally:
        db.close()
    assert read(KB / 'manifest.json')['graph_version'] == VERSION
    exports = {}
    for name, number in [('claims', 2408), ('concepts', 269), ('relations', 400)]:
        path = KB / 'exports' / f'{name}.jsonl'
        rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
        assert len(rows) == number and all(r['graph_version'] == VERSION for r in rows)
        exports[name] = {'rows': number, 'graph_version': VERSION, 'sha256': sha(path)}
    assert VERSION in (KB / 'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150]
    assert read(KB / 'exports/coverage.json')['graph_version'] == VERSION
    inv = read(AUDIT / 'stage-c-l035-source-invariants.json')
    assert inv['pass'] and inv['graph_version'] == VERSION
    assert inv['original_reviewed_claims_unchanged'] == 2366 and inv['original_reviewed_evidence_unchanged'] == 3360
    verification = read(AUDIT / 'stage-c-l035-verification.json')
    assert verification['pass'] and verification['graph_version'] == VERSION
    assert len(verification['checks']) == 6 and len(verification['parity']) == 7
    assert verification['intended_figure_links_checked'] == dict(claims=8, associations=9, unique_figures=3)
    dev = read(AGENT / 'evaluation/stage-g-development-current.results.json')
    assert dev['graph_version'] == VERSION and dev['executable_development_cases'] == dev['retrieval_plan_contract_passed'] == 240
    assert all(r['source_identity_matches_expected'] for r in dev['observations'])
    pending_ids = set()
    for n in [31, 33, 34]:
        pending_ids.update(json.loads(line)['id'] for line in (AGENT / 'curation/upper' / f'c_stage_l{n:03d}.pending.jsonl').read_text(encoding='utf-8').splitlines() if line.strip())
    changes = [
        ('upper-l033-c-stage-pending-chart-model-and-valid-interpretations-versus-unique-path',
         ['strict-trade-base-three-same-price-transactions', 'minute-levels-practical-not-strict-trade-recursion', 'objective-path-subjective-level-five-three-thirty-one'],
         '35明确每笔成交/三同价严格入口和分钟便利模本，选级别主观而走势客观；仍不能以时间图名代全书递归或抹符合逻辑的多义。'),
        ('upper-l034-c-stage-pending-short-front-back-answer-ambiguous',
         ['mixed-lower-level-connection-a-b-b-example', 'single-five-type-cannot-contain-thirty-center', 'type-connection-associative-not-commutative'],
         '35明确a+B+b全程30分类型、B为中枢及结合不交换，可补概念范围；不能反向捏造34前面/后面的唯一语法指代，原待核仍开放。'),
        ('upper-l033-c-stage-pending-indicator-priority-and-small-signal-context',
         ['large-buy-sell-is-sublevel-or-below-not-necessarily-direct', 'buy-sell-level-proof-endpoint-completion-outline', 'all-level-alignment-only-most-standard-coarse-theorem'],
         '35说明大买卖点属次级以下某级而非必直接次级；不等任意小背驰都必大反转，全级同步只是最规范情形，MACD优先问题未被该定理替代。'),
        ('upper-l034-c-stage-pending-dated-2915-third-buy-confirmation-and-new-center',
         ['mar9-five-top-divergence-expands-new-thirty-from-mar7', 'mar8-2871-third-buy-then-new-thirty-from-mar7-2911', 'second-thirty-center-range-2892-2911', 'third-buy-after-second-center-not-guaranteed-up-daily-possible'],
         '35作者事后明确3/8 2871三买和新30分2892至2911，落实34新中枢可能一支；不回写当时尚待确认、不抹三买后还可扩日线或图小数/文整数范围。'),
        ('upper-l034-c-stage-pending-chosen-level-exit-not-second-noise-or-perfect-execution',
         ['historical-t-plus-one-blocks-full-subminute-except-tzero', 'tiny-level-amplitude-cost-error-no-long-run-meaning', 'chosen-level-own-buy-sell-enter-exit-no-own-down', 'partial-lower-level-trades-under-chosen-level'],
         '35补制度、波幅相对成本误差以及本级退出/低级部分操作区别；仍无统一金额阈值、触发量化或理想成交保证，按历史制度语境。'),
        ('upper-l031-c-stage-pending-cost-stages-cash-basis-versus-risk-guarantees',
         ['partial-lower-level-trades-under-chosen-level', 'zero-cost-only-risk-escape-author-assertion'],
         '35重复降成本唯一降风险、零成本才脱风险的强措辞；标作者主张，不能据重复就认证零现金净投入等同无经济风险，原成本阶段范围不改。'),
    ]
    followups = []
    for pending_id, slugs, finding in changes:
        ids = ['upper-l035-c-stage-' + slug for slug in slugs]
        assert pending_id in pending_ids and all(id in known for id in ids)
        followups.append({'pending_id': pending_id, 'status': 'new_source_located_scope_still_pending',
                          'new_claim_ids': ids, 'finding': finding, 'global_pending_not_closed': True, 'graph_version': VERSION})
    (AGENT / 'curation/upper/c_stage_l035.partial-resolutions.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n' for r in followups), encoding='utf-8')
    checks = [
        '42条JSON Schema及引用/身份/映射/坐标预检',
        '56段原文哈希及全段台账一致，实际PDF259至265共7页3完整图及前后课边界视觉核对',
        '原2366命题3360已复核证据未改，9647段528图逐行比较仅6解盘来源日期与3图来源备注授权变更',
        '33项当前工作区Node测试通过（原有27项及另行验收的检索评测6项）',
        '2408条已复核命题全量引用校验0错误',
        '6组来源/条件边界及7组CLI/公共/桌面模块一致，8命题9配图关联逐项确认，只读哈希不变',
        '240/240冻结开发取证计划和已标注来源身份回归通过，无新题替换',
        '2408命题/269概念/400关系JSONL及Markdown/coverage同版本导出',
        '6条旧待核补充关联，原问题全部保持开放',
    ]
    not_run = ['240题完整类别/自然问题基线/生成回答评分/消融对抗验收未完成；开发取证计划通过不能代替',
               '36至61共26课完整语义及全书跨课/图文审查未完成',
               '独立Agent打包后运行及Windows真实离线/缩放旋转跨页交互未验收']
    acceptance = '35课42条46证据、6日期与3图来源已发布；2408引用/240冻结开发题回归通过；8待核及全书/产品目标未完成。'
    next_action = f'接续上册36课，实际PDF{next_row[1]}页标题；完整阅读走势类型连接结合性运用及当下判断、重分、解盘与答疑，核对完成/级别/数量边界和原图。'
    evaluation = {'executable_development_cases': 240, 'target': 240, 'gold_review_status': 'model_reviewed_development',
                  'human_gold_reviewed': False, 'independent_test_set': False, 'generated_answers_scored': False,
                  'retrieval_plan_and_source_identity_passed_on_current_graph': 240, 'full_stage_g_acceptance_complete': False,
                  'new_project_gold_cases_created_in_this_batch': 0,
                  'note': '冻结开发取证计划及本批边界检查通过，不证明完整G、独立金标准或实际桌面交互通过。'}
    path = AUDIT / 'stage-c-l035-publication.json'; pub = read(path)
    assert pub['graph_version'] == VERSION and pub['formal_import'] == 'passed'
    assert list(pub['batch_sha256'].values()) == [sha(AGENT / 'curation/upper/c_stage_l035.reviewed.jsonl')]
    pub.update(updated_at=datetime.now(timezone.utc).isoformat(), checks_run=checks, checks_not_run=not_run,
               acceptance=acceptance, next_action=next_action, exports=exports,
               final_sha256={'database': sha(KB / 'graph.sqlite'), 'manifest': sha(KB / 'manifest.json')},
               development_evaluation=evaluation, partial_pending_followups=6, semantic_completion=False,
               writes_to_knowledge_graph_by_this_finalizer=False)
    write(path, pub)
    path = AGENT / 'curation/progress.json'; progress = read(path)
    assert progress['graph_version'] in ['0.1.0-review-20e3aa53bf69', VERSION]
    if progress['graph_version'] != VERSION:
        progress['previous_checkpoint'] = {key: progress[key] for key in ['graph_version', 'completed', 'next_action', 'evaluation']}
    outputs = ['source-audit/stage-c-l035-' + name + '.json' for name in ['source-plan', 'source-applied', 'source-invariants', 'publication', 'verification']]
    progress['machine_outputs'] = list(dict.fromkeys(progress['machine_outputs'] + outputs + ['upper/c_stage_l035.partial-resolutions.jsonl']))
    progress.update(updated_at=datetime.now(timezone.utc).isoformat(), graph_version=VERSION, counts=counts,
                    claim_status_counts=claim_status, figure_origin_counts=figure_status, unit_processing_status_counts=unit_status,
                    semantic_completion=False, completed=[
                        '上册35课56段7页3图同模型四轮审读，42命题46证据13关系支撑发布，新增走势类型连接/买卖点级别定理/交易误差3概念',
                        '6解盘来源日期按3/9 11:54及3/12 15:20补齐，正文与原署名回复不改；3图2文后1原发未核，后图不证明作者已知未来',
                        '原2366命题3360证据及全源原文/字符映射/坐标逐行未改；每笔成交/三同价为严格入口，分钟15或30为便利模本，不混后期技术笔',
                        '单5分类型延续不能含30分中枢与多类型连接分开；混合低级段可结合重分，结合非交换，三种分类非恰三段，a+B+b整体类型非裸中枢',
                        '大买卖点属次级以下某点非必直接次级，逆命题不成立，全级同步仅最规范；历史T+1、成本/误差相对波幅、本级与低级部分操作、零净现金非无经济风险；8待核',
                        '3/8 2871三买由3/12作者明确回顾，新30分2892至2911与未来日线演化分时；除权缺口可作最低跌非一跳三卖，奔走第二高第三稍破首高和读者认可范围保留',
                        '2408命题/269概念/400关系同版本导出；33工程/2408引用、6边界和7组CLI/公共/桌面模块一致，8命题9配图关联逐项通过',
                        '240冻结开发取证计划与已标注身份回归通过，不增题凑数；6条旧待核补充均开放，余26课',
                    ], pending=[
                        '本批8待核见upper/c_stage_l035.pending.jsonl：严格入口/分钟模本、单类型/连接结合范围、买卖点层级定理、操作级别/成本/历史制度、三买后扩展、缺口/奔走/认可范围、自责主张、日期/图源',
                        '36至61共26课未完整语义审读；82课有阅读记录含历史62至64，不等全书技术抽取或全部解释统一',
                        '240题完整类别、自然问题基线、生成回答评分、消融对抗与全书跨课/图文审查未完成',
                        '独立Agent实际交付运行及Windows真实离线/缩放旋转跨页交互未验收',
                    ], checks_run=checks, checks_not_run=not_run, acceptance=acceptance,
                    next_resume_anchor=next_anchor, next_action=next_action,
                    coverage_caveat='35课56段7页3图同模型四轮，累计82课阅读记录含历史62至64，不称独立复核或全书完成。',
                    evaluation=evaluation,
                    previous_turn_classification='progress：35课56段3图、6解盘来源日期与42条46证据发布；2408引用/240冻结开发题回归通过，余26课。')
    write(path, progress)
    print(json.dumps({'graph_version': VERSION, 'reviewed': 2408, 'development_cases': 240,
                      'remaining_lessons': 26, 'next_anchor': next_anchor, 'semantic_completion': False}, ensure_ascii=False))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
