"""Save verified lesson39 publication and the lesson40 continuation point."""
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2]
KB = AGENT.parent / 'shared-knowledge/v0.1.0'
AUDIT = Path(__file__).resolve().parent
VERSION = '0.1.0-review-01407b1617c1'


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
                              concepts=276, claims=5189, evidence=6211, relations=442, reviews=2620)
        claim_status = db.execute('SELECT review_status,COUNT(*) FROM claims GROUP BY review_status ORDER BY review_status').fetchall()
        figure_status = db.execute('SELECT origin_status,COUNT(*) FROM figures GROUP BY origin_status ORDER BY origin_status').fetchall()
        unit_status = db.execute('SELECT processing_status,COUNT(*) FROM units GROUP BY processing_status ORDER BY processing_status').fetchall()
        assert dict(claim_status) == {'pending': 2612, 'rejected': 27, 'reviewed': 2550}
        assert dict(unit_status)['extracted'] == 22
        assert db.execute("SELECT COUNT(*) FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed'").fetchone()[0] == 3572
        next_row = db.execute("SELECT id,pdf_page,text FROM passages WHERE unit_id='lesson-040' ORDER BY pdf_page,block_index,id LIMIT 1").fetchone()
        assert next_row and next_row[2].startswith('教你炒股票40')
        next_anchor = next_row[0] + ' / lesson-040'
        known = {r[0] for r in db.execute("SELECT id FROM claims WHERE review_status='reviewed'")}
    finally:
        db.close()
    assert read(KB / 'manifest.json')['graph_version'] == VERSION
    exports = {}
    for name, number in [('claims', 2550), ('concepts', 276), ('relations', 442)]:
        path = KB / 'exports' / f'{name}.jsonl'
        rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
        assert len(rows) == number and all(r['graph_version'] == VERSION for r in rows)
        exports[name] = {'rows': number, 'graph_version': VERSION, 'sha256': sha(path)}
    assert VERSION in (KB / 'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150]
    assert read(KB / 'exports/coverage.json')['graph_version'] == VERSION
    inv = read(AUDIT / 'stage-c-l039-source-invariants.json')
    assert inv['pass'] and inv['graph_version'] == VERSION
    assert inv['original_reviewed_claims_unchanged'] == 2522 and inv['original_reviewed_evidence_unchanged'] == 3541
    verification = read(AUDIT / 'stage-c-l039-verification.json')
    assert verification['pass'] and verification['graph_version'] == VERSION
    assert len(verification['checks']) == 6 and len(verification['parity']) == 7
    assert verification['intended_figure_links_checked'] == dict(claims=7, associations=9, unique_figures=3)
    dev = read(AGENT / 'evaluation/stage-g-development-current.results.json')
    assert dev['graph_version'] == VERSION and dev['executable_development_cases'] == dev['retrieval_plan_contract_passed'] == 240
    assert all(r['source_identity_matches_expected'] for r in dev['observations'])
    pending_ids = set()
    for n in [35, 37, 38]:
        pending_ids.update(json.loads(line)['id'] for line in (AGENT / 'curation/upper' / f'c_stage_l{n:03d}.pending.jsonl').read_text(encoding='utf-8').splitlines() if line.strip())
    changes = [
        ('upper-l038-c-stage-pending-same-level-unique-rule-not-global-unique-or-formal-proof',
         ['a-plus-A-regroup-five-types-and-A-contains-thirty-center', 'new-Ai-plus-two-not-rewrite-prior-unique-decomposition'],
         '39说明未来Ai+2不影响此前至Ai+1分解、a可先规整5分，A含30分中心；仍是作者唯一性主张而非完整起点/等值/算法证明。'),
        ('upper-l038-c-stage-pending-own-consolidation-plus-consolidation-and-six-sublevel-types',
         ['A0-a-odd-down-even-up-A1-not-break-a-low', 'A2-break-a-high-A3-not-return-absorb-into-a-prime', 'center-can-grow-thirty-to-year-still-five-pair-operation'],
         '39给低层5分固定编号和保护/吸收分支，高层中心可扩至日周年而仍按固定低层操作；不把高层升级混成本级不定义延伸的规则矛盾。'),
        ('upper-l038-c-stage-pending-mechanical-branches-completion-equality-execution-and-profit',
         ['pair-divergence-even-i-plus-two-sell-odd-buy', 'no-divergence-even-hold-until-protection-break-then-exit', 'no-divergence-odd-stay-cash-until-protection-break-rebuy'],
         '39扩充Ai/i+2盘背与未盘背后保护位、后续Ai+k+4弱势联合触发；奇支k约定和相等/完成/成交细节仍未全，未证收益。'),
        ('upper-l038-c-stage-pending-exit-internal-divergence-capacity-and-signal-vs-fall-threshold',
         ['mar23-1325-minimum-divergence-not-five-return-center', 'up-buy-before-sell-down-sell-before-buy-rhythm', 'no-high-exit-low-purchase-is-add-not-repurchase'],
         '39作者否定13:25为5分背驰而判最小级回原中枢，并区分先卖回补与高没走后加仓；仍不能以任意小信号改本级退出或补统一跌幅。'),
        ('upper-l035-c-stage-pending-operation-level-cost-regime-and-zero-risk-claim',
         ['fearful-entry-can-split-two-no-proportions', 'no-high-exit-low-purchase-is-add-not-repurchase', 'prior-sale-then-staged-repurchase-if-not-confident'],
         '39给两笔/分单但未定50%，先卖后回补不是未卖后加仓；方向不错安抚与卖就全买源字不顺保留，未解决T+1/零风险/费用全部限制。'),
        ('upper-l037-c-stage-pending-historical-macro-phases-returns-and-futures-predictions',
         ['theory-europe-us-same-futures-certificate-variable-source-scope'],
         '39说欧美理论通用而期货交易凭证即时可变，但未定变量/机制，不据简答确认读者海外制度或验证37期货影响延伸/方向的历史预测。'),
    ]
    followups = []
    for pending_id, slugs, finding in changes:
        ids = ['upper-l039-c-stage-' + slug for slug in slugs]
        assert pending_id in pending_ids and all(id in known for id in ids)
        followups.append({'pending_id': pending_id, 'status': 'new_source_located_scope_still_pending',
                          'new_claim_ids': ids, 'finding': finding, 'global_pending_not_closed': True, 'graph_version': VERSION})
    (AGENT / 'curation/upper/c_stage_l039.partial-resolutions.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n' for r in followups), encoding='utf-8')
    checks = [
        '28条JSON Schema及引用/身份/映射/坐标预检',
        '40段原文哈希及全段台账一致，实际PDF287至290共4页3完整图及前课边界视觉核对，另看290原字',
        '原2522命题3541已复核证据未改，9647段528图逐行比较仅3跨日来源日期与3图来源备注授权变更',
        '33项当前工作区Node测试通过（原有27项及另行验收的检索评测6项）',
        '2550条已复核命题全量引用校验0错误',
        '6组来源/条件边界及7组CLI/公共/桌面模块一致，7命题9配图关联逐项确认，只读哈希不变',
        '240/240冻结开发取证计划和已标注来源身份回归通过，无新题替换',
        '2550命题/276概念/442关系JSONL及Markdown/coverage同版本导出',
        '6条旧待核补充关联，原问题全部保持开放',
    ]
    not_run = ['240题完整类别/自然问题基线/生成回答评分/消融对抗验收未完成；开发取证计划通过不能代替',
               '40至61共22课完整语义及全书跨课/图文审查未完成',
               '独立Agent打包后运行及Windows真实离线/缩放旋转跨页交互未验收']
    acceptance = '39课28条31证据、3日期与3图来源已发布；2550引用/240冻结开发题回归通过；8待核及全书/产品目标未完成。'
    next_action = f'接续上册40课，实际PDF{next_row[1]}页标题；完整阅读同级别分解多重赋格及解盘答疑，核对周期/级别、比率概率边界与原图。'
    evaluation = {'executable_development_cases': 240, 'target': 240, 'gold_review_status': 'model_reviewed_development',
                  'human_gold_reviewed': False, 'independent_test_set': False, 'generated_answers_scored': False,
                  'retrieval_plan_and_source_identity_passed_on_current_graph': 240, 'full_stage_g_acceptance_complete': False,
                  'new_project_gold_cases_created_in_this_batch': 0,
                  'note': '冻结开发取证计划及本批边界检查通过，不证明完整G、独立金标准或实际桌面交互通过。'}
    path = AUDIT / 'stage-c-l039-publication.json'; pub = read(path)
    assert pub['graph_version'] == VERSION and pub['formal_import'] == 'passed'
    assert list(pub['batch_sha256'].values()) == [sha(AGENT / 'curation/upper/c_stage_l039.reviewed.jsonl')]
    pub.update(updated_at=datetime.now(timezone.utc).isoformat(), checks_run=checks, checks_not_run=not_run,
               acceptance=acceptance, next_action=next_action, exports=exports,
               final_sha256={'database': sha(KB / 'graph.sqlite'), 'manifest': sha(KB / 'manifest.json')},
               development_evaluation=evaluation, partial_pending_followups=6, semantic_completion=False,
               writes_to_knowledge_graph_by_this_finalizer=False)
    write(path, pub)
    path = AGENT / 'curation/progress.json'; progress = read(path)
    assert progress['graph_version'] in ['0.1.0-review-0cc5c3d74a49', VERSION]
    if progress['graph_version'] != VERSION:
        progress['previous_checkpoint'] = {key: progress[key] for key in ['graph_version', 'completed', 'next_action', 'evaluation']}
    outputs = ['source-audit/stage-c-l039-' + name + '.json' for name in ['source-plan', 'source-applied', 'source-invariants', 'publication', 'verification']]
    progress['machine_outputs'] = list(dict.fromkeys(progress['machine_outputs'] + outputs + ['upper/c_stage_l039.partial-resolutions.jsonl']))
    progress.update(updated_at=datetime.now(timezone.utc).isoformat(), graph_version=VERSION, counts=counts,
                    claim_status_counts=claim_status, figure_origin_counts=figure_status, unit_processing_status_counts=unit_status,
                    semantic_completion=False, completed=[
                        '上册39课40段4页3图同模型四轮审读，28命题31证据10关系支撑发布，新增监管风险概念',
                        '3解盘来源段改3/26 15:20:49，前3/23及尾头字符不改；3图1行情后加2公式示意原发未核，图不补数学/未来确认',
                        '原2522命题3541证据及全源原文/字符映射/坐标逐行未改；a规整5分而A含30分中心非A等同纯中心，A0为向上a、奇下偶上和A1条件保存',
                        'A2破高且A3不回才吸收，A3破高三段中心留等值边界；Ai/i+2同向盘背按奇偶买卖，未盘背才保护位/随后Ai+k+4弱势联合，k奇支约定与唯一性未全证；8待核',
                        '上下先买后卖/先卖后买节奏和失步暂停保存，生理感应为未证类比；两笔非50%，高未卖后买是加仓，原页卖就全买原字不静改',
                        '13:25最小级非5分且未定1分/线段，3/26突破仍需确认；欧美理论通用未认证读者规则，期货凭证即时可变未定机制，历史板块/监管/方向安抚非收益保证',
                        '2550命题/276概念/442关系同版本导出；33工程/2550引用、6边界和7组CLI/公共/桌面模块一致，7命题9配图关联逐项通过',
                        '240冻结开发取证计划与已标注身份回归通过，不增题凑数；6条旧待核补充均开放，余22课',
                    ], pending=[
                        '本批8待核见upper/c_stage_l039.pending.jsonl：训练/生理/收益规范、a+A正规化等值、Ai奇偶/k/唯一历史、分单/方向/T+1/源字、最小非5分、期货凭证/海外规则、历史板块监管/确认、日期/图源',
                        '40至61共22课未完整语义审读；86课有阅读记录含历史62至64，不等全书技术抽取或全部解释统一',
                        '240题完整类别、自然问题基线、生成回答评分、消融对抗与全书跨课/图文审查未完成',
                        '独立Agent实际交付运行及Windows真实离线/缩放旋转跨页交互未验收',
                    ], checks_run=checks, checks_not_run=not_run, acceptance=acceptance,
                    next_resume_anchor=next_anchor, next_action=next_action,
                    coverage_caveat='39课40段4页3图同模型四轮，累计86课阅读记录含历史62至64，不称独立复核或全书完成。',
                    evaluation=evaluation,
                    previous_turn_classification='progress：39课40段3图、3日期修正与28条31证据发布；2550引用/240冻结开发题回归通过，余22课。')
    write(path, progress)
    print(json.dumps({'graph_version': VERSION, 'reviewed': 2550, 'development_cases': 240,
                      'remaining_lessons': 22, 'next_anchor': next_anchor, 'semantic_completion': False}, ensure_ascii=False))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
