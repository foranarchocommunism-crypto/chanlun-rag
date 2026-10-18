"""Save verified lesson30 publication and the lesson31 continuation point."""
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2]
KB = AGENT.parent / 'shared-knowledge/v0.1.0'
AUDIT = Path(__file__).resolve().parent
VERSION = '0.1.0-review-958d0b42fad7'


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
                              concepts=260, claims=4851, evidence=5822, relations=349, reviews=2277)
        claim_status = db.execute('SELECT review_status,COUNT(*) FROM claims GROUP BY review_status ORDER BY review_status').fetchall()
        figure_status = db.execute('SELECT origin_status,COUNT(*) FROM figures GROUP BY origin_status ORDER BY origin_status').fetchall()
        unit_status = db.execute('SELECT processing_status,COUNT(*) FROM units GROUP BY processing_status ORDER BY processing_status').fetchall()
        assert dict(claim_status) == {'pending': 2612, 'rejected': 27, 'reviewed': 2212}
        assert dict(unit_status)['extracted'] == 31
        next_row = db.execute("SELECT id,pdf_page,text FROM passages WHERE unit_id='lesson-031' ORDER BY pdf_page,block_index,id LIMIT 1").fetchone()
        assert next_row and next_row[2].startswith('教你炒股票31')
        next_anchor = next_row[0] + ' / lesson-031'
        known = {r[0] for r in db.execute("SELECT id FROM claims WHERE review_status='reviewed'")}
    finally:
        db.close()
    assert read(KB / 'manifest.json')['graph_version'] == VERSION
    exports = {}
    for name, number in [('claims', 2212), ('concepts', 260), ('relations', 349)]:
        path = KB / 'exports' / f'{name}.jsonl'
        rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
        assert len(rows) == number and all(r['graph_version'] == VERSION for r in rows)
        exports[name] = {'rows': number, 'graph_version': VERSION, 'sha256': sha(path)}
    assert VERSION in (KB / 'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150]
    assert read(KB / 'exports/coverage.json')['graph_version'] == VERSION
    inv = read(AUDIT / 'stage-c-l030-source-invariants.json')
    assert inv['pass'] and inv['graph_version'] == VERSION
    assert inv['original_reviewed_claims_unchanged'] == 2185 and inv['original_reviewed_evidence_unchanged'] == 3151
    verification = read(AUDIT / 'stage-c-l030-verification.json')
    assert verification['pass'] and verification['graph_version'] == VERSION
    assert len(verification['checks']) == 6 and len(verification['parity']) == 7
    dev = read(AGENT / 'evaluation/stage-g-development-current.results.json')
    assert dev['graph_version'] == VERSION and dev['executable_development_cases'] == dev['retrieval_plan_contract_passed'] == 240
    assert all(r['source_identity_matches_expected'] for r in dev['observations'])
    pending_ids = set()
    for name in ['c_stage_l026', 'c_stage_l027', 'c_stage_l028', 'c_stage_l029']:
        pending_ids.update(json.loads(line)['id'] for line in (AGENT / 'curation/upper' / f'{name}.pending.jsonl').read_text(encoding='utf-8').splitlines() if line.strip())
    changes = [
        ('upper-l026-c-stage-pending-price-risk-information-and-absolute-control',
         ['pure-trading-price-not-information-completeness', 'price-sufficient-market-author-defined', 'entered-divergence-leg-can-break-and-reassess'],
         '30把价格充分有效明确为作者定义，不要求信息全反映，进入背驰段后突发结构破裂须重估；不因此认证26所有风险均可提前反映或永不失败。'),
        ('upper-l026-c-stage-pending-continuation-cancellation-ordinary-suspension-and-deadline',
         ['ordered-price-path-and-irreversible-trading-time', 'retroactive-cancellation-non-price-sufficient-example'],
         '30补交易时间不可逆与过去交易可随意抹除的定义边界，仍无普通停牌/自有资金期限的统一数值条件，不把二者混同。'),
        ('upper-l027-c-stage-pending-divergence-leg-naming-versus-confirmation',
         ['entered-divergence-leg-can-break-and-reassess'],
         '30明说进入日线背驰段后小结构仍可突发破裂并影响大级别，须当下重估；是进入段非成功背驰的直接补充，旧命名/已确认范围问题仍开放。'),
        ('upper-l029-c-stage-pending-lowest-one-minute-choice-versus-later-recursion',
         ['lowest-three-consecutive-k-have-direction'],
         '30给连续三根且有方向，并举从高位下来下上下，仍是早期自选最低口径；不取消29如果1分最低的前提或后期递归。'),
        ('upper-l028-c-stage-pending-second-third-points-center-referents-and-daily-alignment',
         ['third-buy-localize-like-first-below-sublevel', '000581-third-buy-wait-completed-sublevel-retest', 'one-extending-center-not-numbered-many'],
         '30补三买按次级以下一买方式定位、次级已走出且回抽不入中枢，同一延伸中枢不重复编号；不是本级一三买恒等，也未统一28所有中枢指代。'),
        ('upper-l026-c-stage-pending-long-fundamental-selection-and-no-cut-vs-protection',
         ['same-theory-different-capital-and-trader-outcomes', 'novice-fundamental-near-bottom-large-buy-selection'],
         '30实际结果仍列基本面，新手练习明确基本面支持/近底/大级别买点三条件，理论纯价格对象与选股范围分开；未解除其他防护条件。'),
    ]
    followups = []
    for pending_id, slugs, finding in changes:
        ids = ['upper-l030-c-stage-' + slug for slug in slugs]
        assert pending_id in pending_ids and all(id in known for id in ids)
        followups.append({'pending_id': pending_id, 'status': 'new_source_located_scope_still_pending',
                          'new_claim_ids': ids, 'finding': finding, 'global_pending_not_closed': True, 'graph_version': VERSION})
    (AGENT / 'curation/upper/c_stage_l030.partial-resolutions.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n' for r in followups), encoding='utf-8')
    checks = [
        '27条JSON Schema及引用/身份/映射/坐标预检',
        '60段原文哈希及全段台账一致，实际PDF213至218共6页核对，本课无配图',
        '原2185命题3151已复核证据未改，9647段528图逐行比较仅1段解盘日期授权变更',
        '33项当前工作区Node测试通过（原有27项及另行验收的检索评测6项）',
        '2212条已复核命题全量引用校验0错误',
        '6组来源/条件边界及7组CLI/公共/桌面模块一致，只读哈希不变',
        '240/240冻结开发取证计划和已标注来源身份回归通过，无新题替换',
        '2212命题/260概念/349关系JSONL及Markdown/coverage同版本导出',
        '6条旧待核补充关联，原问题全部保持开放',
    ]
    not_run = ['240题完整类别/自然问题基线/生成回答评分/消融对抗验收未完成；开发取证计划通过不能代替',
               '31至61共31课完整语义及全书跨课/图文审查未完成',
               '独立Agent打包后运行及Windows真实离线/缩放旋转跨页交互未验收']
    acceptance = '30课27条32证据、1段日期已发布；六页无图，2212引用/240冻结开发题回归通过；6待核及全书/产品目标未完成。'
    next_action = f'接续上册31课，实际PDF{next_row[1]}页标题；核对资金管理最稳固基础、仓位/级别/买卖点与风险边界，逐段和逐图复核来源及答疑。'
    evaluation = {'executable_development_cases': 240, 'target': 240, 'gold_review_status': 'model_reviewed_development',
                  'human_gold_reviewed': False, 'independent_test_set': False, 'generated_answers_scored': False,
                  'retrieval_plan_and_source_identity_passed_on_current_graph': 240, 'full_stage_g_acceptance_complete': False,
                  'new_project_gold_cases_created_in_this_batch': 0,
                  'note': '冻结开发取证计划及本批边界检查通过，不证明完整G、独立金标准或实际桌面交互通过。'}
    path = AUDIT / 'stage-c-l030-publication.json'
    pub = read(path)
    assert pub['graph_version'] == VERSION and pub['formal_import'] == 'passed'
    pub.update(updated_at=datetime.now(timezone.utc).isoformat(), checks_run=checks, checks_not_run=not_run,
               acceptance=acceptance, next_action=next_action, exports=exports,
               final_sha256={'database': sha(KB / 'graph.sqlite'), 'manifest': sha(KB / 'manifest.json')},
               development_evaluation=evaluation, partial_pending_followups=6, semantic_completion=False,
               writes_to_knowledge_graph_by_this_finalizer=False)
    write(path, pub)
    path = AGENT / 'curation/progress.json'
    progress = read(path)
    assert progress['graph_version'] in ['0.1.0-review-c6ace0c23754', VERSION]
    if progress['graph_version'] != VERSION:
        progress['previous_checkpoint'] = {key: progress[key] for key in ['graph_version', 'completed', 'next_action', 'evaluation']}
    outputs = ['source-audit/stage-c-l030-' + name + '.json' for name in ['source-plan', 'source-applied', 'source-invariants', 'publication', 'verification']]
    progress['machine_outputs'] = list(dict.fromkeys(progress['machine_outputs'] + outputs + ['upper/c_stage_l030.partial-resolutions.jsonl']))
    progress.update(updated_at=datetime.now(timezone.utc).isoformat(), graph_version=VERSION, counts=counts,
                    claim_status_counts=claim_status, figure_origin_counts=figure_status, unit_processing_status_counts=unit_status,
                    semantic_completion=False, completed=[
                        '上册30课60段6页无图同模型四轮审读，27命题32证据10关系支撑发布，新增交易时间不可逆/交易延异性/创业投资3概念',
                        '1跨页解盘段按2/14 15:13日期修正，前段2/13创投预告不改；60段角色及CCTV/大盘读者问题分别保留',
                        '原2185命题3151证据及全源原文/字符映射/坐标逐行未改；价格充分有效为作者自定义而非全部信息反映',
                        '30两前提整体绝对性与72明确限动力学分范围；不动点/公理化/零向量及周线可控性不补形式证明，进入背驰段结构突变须重估',
                        '三买低级定位不改本级定义，次级走出且回抽不入、最低三K连续方向、新手基本面/近底/大级别买点联合条件保留；6待核',
                        '2212命题/260概念/349关系同版本导出；33工程/2212引用、6边界和7组CLI/公共/桌面模块一致通过',
                        '240冻结开发取证计划与已标注身份回归通过，不增题凑数；6条旧待核补充均开放，余31课',
                    ], pending=[
                        '本批6待核见upper/c_stage_l030.pending.jsonl：两前提与72范围、公理化/比喻、进入背驰段结构破裂、中枢及三买完成、最低三K、历史解盘/新手联合条件',
                        '31至61共31课未完整语义审读；77课有阅读记录含历史62至64，不等全书技术抽取或全部解释统一',
                        '240题完整类别、自然问题基线、生成回答评分、消融对抗与全书跨课/图文审查未完成',
                        '独立Agent实际交付运行及Windows真实离线/缩放旋转跨页交互未验收',
                    ], checks_run=checks, checks_not_run=not_run, acceptance=acceptance,
                    next_resume_anchor=next_anchor, next_action=next_action,
                    coverage_caveat='30课60段6页无图同模型四轮，累计77课阅读记录含历史62至64，不称独立复核或全书完成。',
                    evaluation=evaluation,
                    previous_turn_classification='progress：30课60段6页、1日期修正和27条32证据发布；2212引用/240冻结开发题回归通过，余31课。')
    write(path, progress)
    print(json.dumps({'graph_version': VERSION, 'reviewed': 2212, 'development_cases': 240,
                      'remaining_lessons': 31, 'next_anchor': next_anchor, 'semantic_completion': False}, ensure_ascii=False))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
