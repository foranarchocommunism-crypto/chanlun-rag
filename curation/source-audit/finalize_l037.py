"""Save verified lesson37 publication and the lesson38 continuation point."""
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2]
KB = AGENT.parent / 'shared-knowledge/v0.1.0'
AUDIT = Path(__file__).resolve().parent
VERSION = '0.1.0-review-fb1a6407424c'


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
                              concepts=274, claims=5121, evidence=6137, relations=421, reviews=2552)
        claim_status = db.execute('SELECT review_status,COUNT(*) FROM claims GROUP BY review_status ORDER BY review_status').fetchall()
        figure_status = db.execute('SELECT origin_status,COUNT(*) FROM figures GROUP BY origin_status ORDER BY origin_status').fetchall()
        unit_status = db.execute('SELECT processing_status,COUNT(*) FROM units GROUP BY processing_status ORDER BY processing_status').fetchall()
        assert dict(claim_status) == {'pending': 2612, 'rejected': 27, 'reviewed': 2482}
        assert dict(unit_status)['extracted'] == 24
        assert db.execute("SELECT COUNT(*) FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed'").fetchone()[0] == 3498
        next_row = db.execute("SELECT id,pdf_page,text FROM passages WHERE unit_id='lesson-038' ORDER BY pdf_page,block_index,id LIMIT 1").fetchone()
        assert next_row and next_row[2].startswith('教你炒股票38')
        next_anchor = next_row[0] + ' / lesson-038'
        known = {r[0] for r in db.execute("SELECT id FROM claims WHERE review_status='reviewed'")}
    finally:
        db.close()
    assert read(KB / 'manifest.json')['graph_version'] == VERSION
    exports = {}
    for name, number in [('claims', 2482), ('concepts', 274), ('relations', 421)]:
        path = KB / 'exports' / f'{name}.jsonl'
        rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
        assert len(rows) == number and all(r['graph_version'] == VERSION for r in rows)
        exports[name] = {'rows': number, 'graph_version': VERSION, 'sha256': sha(path)}
    assert VERSION in (KB / 'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150]
    assert read(KB / 'exports/coverage.json')['graph_version'] == VERSION
    inv = read(AUDIT / 'stage-c-l037-source-invariants.json')
    assert inv['pass'] and inv['graph_version'] == VERSION
    assert inv['original_reviewed_claims_unchanged'] == 2443 and inv['original_reviewed_evidence_unchanged'] == 3454
    verification = read(AUDIT / 'stage-c-l037-verification.json')
    assert verification['pass'] and verification['graph_version'] == VERSION
    assert len(verification['checks']) == 6 and len(verification['parity']) == 7
    assert verification['intended_figure_links_checked'] == dict(claims=5, associations=5, unique_figures=2)
    dev = read(AGENT / 'evaluation/stage-g-development-current.results.json')
    assert dev['graph_version'] == VERSION and dev['executable_development_cases'] == dev['retrieval_plan_contract_passed'] == 240
    assert all(r['source_identity_matches_expected'] for r in dev['observations'])
    pending_ids = set()
    for n in [32, 34, 35, 36]:
        pending_ids.update(json.loads(line)['id'] for line in (AGENT / 'curation/upper' / f'c_stage_l{n:03d}.pending.jsonl').read_text(encoding='utf-8').splitlines() if line.strip())
    changes = [
        ('upper-l036-c-stage-pending-multiple-combinations-not-vague-and-completion-scope',
         ['trend-divergence-requires-trend-and-same-level-a-b', 'a-larger-than-b-whole-oscillates-around-a-at-most-consolidation', 'local-b-perspective-not-forget-whole-trend'],
         '37明确多义局部B视角不能抹整体趋势同级A/B条件，若A较大则整体为其震荡；不以任意重括号或字母形式建立背驰。'),
        ('upper-l032-c-stage-pending-live-regrouping-b-level-and-exit-scope',
         ['trend-divergence-requires-trend-and-same-level-a-b', 'c-direct-sublevel-contains-b-third-point', 'b-can-smaller-gaps-strongest-and-not-higher-than-c'],
         '37给典型整体趋势中的A/B同级、c次级含三买卖点及b不大于c；32较大B后的重分属不同对象，不能继续按原同级趋势强套，仍无单一力度公式。'),
        ('upper-l035-c-stage-pending-buy-sell-level-theorem-below-not-all-levels',
         ['c-internal-two-sublevel-centers-original-relative-level', 'standard-c-internal-trend-recursive-interval-nesting', 'all-buy-sell-ultimately-first-points-different-levels'],
         '37再述大点归一类的层级概括及c内部标准嵌套，但内部次级相对词未唯一化；不补读者所求次级/次次级完整证明或把所有小点当大点。'),
        ('upper-l036-c-stage-pending-early-thirty-third-not-daily-and-relative-safety',
         ['no-absolute-prediction-consolidation-trend-respond-current', 'consolidation-extension-ends-third-point-when-probabilistic', 'trend-divergence-ends-trend-consolidation-may-same-type'],
         '37明确三买后大盘整/趋势两支无法绝对预判、盘背可仍同类型；不将早小级信号安全提升为日线脱离或把局部盘整退出当所有更大震荡终止。'),
        ('upper-l036-c-stage-pending-third-buy-repeated-exit-first-retest-and-late-center-frequency',
         ['all-buy-sell-ultimately-first-points-different-levels', 'no-absolute-prediction-consolidation-trend-respond-current', 'over-ninety-prediction-accuracy-auxiliary-claim-not-method'],
         '37强调当下分支应对且预测为或然，90%以上配套手段未给样本/协议；未解除36首次回抽范围或认证晚第4/5中心几乎百分百的统计。'),
        ('upper-l034-c-stage-pending-area-versus-peak-and-center-formed-state',
         ['comparable-force-can-use-consolidation-divergence-method', 'trend-divergence-ends-trend-consolidation-may-same-type'],
         '37给只要力度可比可用盘背方法但不等已背驰，并分趋势结束与同类型内盘背；未补面积唯一公式、不改34原a+B+b记号或36两层配合。'),
    ]
    followups = []
    for pending_id, slugs, finding in changes:
        ids = ['upper-l037-c-stage-' + slug for slug in slugs]
        assert pending_id in pending_ids and all(id in known for id in ids)
        followups.append({'pending_id': pending_id, 'status': 'new_source_located_scope_still_pending',
                          'new_claim_ids': ids, 'finding': finding, 'global_pending_not_closed': True, 'graph_version': VERSION})
    (AGENT / 'curation/upper/c_stage_l037.partial-resolutions.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n' for r in followups), encoding='utf-8')
    checks = [
        '39条JSON Schema及引用/身份/映射/坐标预检',
        '75段原文哈希及全段台账一致，实际PDF273至279共7页2完整图及前课边界视觉核对',
        '原2443命题3454已复核证据未改，9647段528图逐行比较仅6跨日来源日期与2图来源备注授权变更',
        '33项当前工作区Node测试通过（原有27项及另行验收的检索评测6项）',
        '2482条已复核命题全量引用校验0错误',
        '6组来源/条件边界及7组CLI/公共/桌面模块一致，5命题5配图关联逐项确认，只读哈希不变',
        '240/240冻结开发取证计划和已标注来源身份回归通过，无新题替换',
        '2482命题/274概念/421关系JSONL及Markdown/coverage同版本导出',
        '6条旧待核补充关联，原问题全部保持开放',
    ]
    not_run = ['240题完整类别/自然问题基线/生成回答评分/消融对抗验收未完成；开发取证计划通过不能代替',
               '38至61共24课完整语义及全书跨课/图文审查未完成',
               '独立Agent打包后运行及Windows真实离线/缩放旋转跨页交互未验收']
    acceptance = '37课39条44证据、6日期与2图来源已发布；2482引用/240冻结开发题回归通过；8待核及全书/产品目标未完成。'
    next_action = f'接续上册38课，实际PDF{next_row[1]}页标题；完整阅读同级别分解与操作原则及解盘答疑，核对完成/级别、结合重组条件和原图。'
    evaluation = {'executable_development_cases': 240, 'target': 240, 'gold_review_status': 'model_reviewed_development',
                  'human_gold_reviewed': False, 'independent_test_set': False, 'generated_answers_scored': False,
                  'retrieval_plan_and_source_identity_passed_on_current_graph': 240, 'full_stage_g_acceptance_complete': False,
                  'new_project_gold_cases_created_in_this_batch': 0,
                  'note': '冻结开发取证计划及本批边界检查通过，不证明完整G、独立金标准或实际桌面交互通过。'}
    path = AUDIT / 'stage-c-l037-publication.json'; pub = read(path)
    assert pub['graph_version'] == VERSION and pub['formal_import'] == 'passed'
    assert list(pub['batch_sha256'].values()) == [sha(AGENT / 'curation/upper/c_stage_l037.reviewed.jsonl')]
    pub.update(updated_at=datetime.now(timezone.utc).isoformat(), checks_run=checks, checks_not_run=not_run,
               acceptance=acceptance, next_action=next_action, exports=exports,
               final_sha256={'database': sha(KB / 'graph.sqlite'), 'manifest': sha(KB / 'manifest.json')},
               development_evaluation=evaluation, partial_pending_followups=6, semantic_completion=False,
               writes_to_knowledge_graph_by_this_finalizer=False)
    write(path, pub)
    path = AGENT / 'curation/progress.json'; progress = read(path)
    assert progress['graph_version'] in ['0.1.0-review-4867e2d2c06f', VERSION]
    if progress['graph_version'] != VERSION:
        progress['previous_checkpoint'] = {key: progress[key] for key in ['graph_version', 'completed', 'next_action', 'evaluation']}
    outputs = ['source-audit/stage-c-l037-' + name + '.json' for name in ['source-plan', 'source-applied', 'source-invariants', 'publication', 'verification']]
    progress['machine_outputs'] = list(dict.fromkeys(progress['machine_outputs'] + outputs + ['upper/c_stage_l037.partial-resolutions.jsonl']))
    progress.update(updated_at=datetime.now(timezone.utc).isoformat(), graph_version=VERSION, counts=counts,
                    claim_status_counts=claim_status, figure_origin_counts=figure_status, unit_processing_status_counts=unit_status,
                    semantic_completion=False, completed=[
                        '上册37课75段7页2图同模型四轮审读，39命题44证据12关系支撑发布，新增全流通/全球成长性2概念',
                        '6解盘来源段按3/20 15:24:15修正，前段3/19及尾时间头字符不改；两图1后加1原发未核，不据3/21后图认证原预测',
                        '原2443命题3454证据及全源原文/字符映射/坐标逐行未改；趋势背驰须整体趋势与同级A/B，c次级含三买卖点且创新高低，b可小但不大c',
                        '局部B多义视角不抹整体趋势，c内至少两个次级别中枢保留相对层级歧义；标准内趋势可套区间，盘背可仍同类型，结束趋势不必直接反向；8待核',
                        '所有点归一类为层级概括非完整固定算法，三买后大盘整/趋势以当下应对，90%以上预测无样本/协议不当项目实测',
                        '600195的3元多到11与翻5倍/图价不静合，2倍必5/10倍/宏观20年3万点和市值GDP门槛为历史主张；外汇问期货答、读者杠杆及三K连续未获明确答复分别存',
                        '2482命题/274概念/421关系同版本导出；33工程/2482引用、6边界和7组CLI/公共/桌面模块一致，5命题5配图关联逐项通过',
                        '240冻结开发取证计划与已标注身份回归通过，不增题凑数；6条旧待核补充均开放，余24课',
                    ], pending=[
                        '本批8待核见upper/c_stage_l037.pending.jsonl：趋势联合前提、c内部相对次级、盘背力度及结束、归一类与后续两支、影线/三K未答、历史预测、600195价倍不合、日期/图源',
                        '38至61共24课未完整语义审读；84课有阅读记录含历史62至64，不等全书技术抽取或全部解释统一',
                        '240题完整类别、自然问题基线、生成回答评分、消融对抗与全书跨课/图文审查未完成',
                        '独立Agent实际交付运行及Windows真实离线/缩放旋转跨页交互未验收',
                    ], checks_run=checks, checks_not_run=not_run, acceptance=acceptance,
                    next_resume_anchor=next_anchor, next_action=next_action,
                    coverage_caveat='37课75段7页2图同模型四轮，累计84课阅读记录含历史62至64，不称独立复核或全书完成。',
                    evaluation=evaluation,
                    previous_turn_classification='progress：37课75段2图、6日期修正与39条44证据发布；2482引用/240冻结开发题回归通过，余24课。')
    write(path, progress)
    print(json.dumps({'graph_version': VERSION, 'reviewed': 2482, 'development_cases': 240,
                      'remaining_lessons': 24, 'next_anchor': next_anchor, 'semantic_completion': False}, ensure_ascii=False))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
