"""Save verified lesson31 publication and the lesson32 continuation point."""
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2]
KB = AGENT.parent / 'shared-knowledge/v0.1.0'
AUDIT = Path(__file__).resolve().parent
VERSION = '0.1.0-review-77ca557fa0f5'


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
                              concepts=262, claims=4898, evidence=5877, relations=362, reviews=2324)
        claim_status = db.execute('SELECT review_status,COUNT(*) FROM claims GROUP BY review_status ORDER BY review_status').fetchall()
        figure_status = db.execute('SELECT origin_status,COUNT(*) FROM figures GROUP BY origin_status ORDER BY origin_status').fetchall()
        unit_status = db.execute('SELECT processing_status,COUNT(*) FROM units GROUP BY processing_status ORDER BY processing_status').fetchall()
        assert dict(claim_status) == {'pending': 2612, 'rejected': 27, 'reviewed': 2259}
        assert dict(unit_status)['extracted'] == 30
        next_row = db.execute("SELECT id,pdf_page,text FROM passages WHERE unit_id='lesson-032' ORDER BY pdf_page,block_index,id LIMIT 1").fetchone()
        assert next_row and next_row[2].startswith('教你炒股票32')
        next_anchor = next_row[0] + ' / lesson-032'
        known = {r[0] for r in db.execute("SELECT id FROM claims WHERE review_status='reviewed'")}
    finally:
        db.close()
    assert read(KB / 'manifest.json')['graph_version'] == VERSION
    exports = {}
    for name, number in [('claims', 2259), ('concepts', 262), ('relations', 362)]:
        path = KB / 'exports' / f'{name}.jsonl'
        rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
        assert len(rows) == number and all(r['graph_version'] == VERSION for r in rows)
        exports[name] = {'rows': number, 'graph_version': VERSION, 'sha256': sha(path)}
    assert VERSION in (KB / 'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150]
    assert read(KB / 'exports/coverage.json')['graph_version'] == VERSION
    inv = read(AUDIT / 'stage-c-l031-source-invariants.json')
    assert inv['pass'] and inv['graph_version'] == VERSION
    assert inv['original_reviewed_claims_unchanged'] == 2212 and inv['original_reviewed_evidence_unchanged'] == 3183
    verification = read(AUDIT / 'stage-c-l031-verification.json')
    assert verification['pass'] and verification['graph_version'] == VERSION
    assert len(verification['checks']) == 6 and len(verification['parity']) == 7
    dev = read(AGENT / 'evaluation/stage-g-development-current.results.json')
    assert dev['graph_version'] == VERSION and dev['executable_development_cases'] == dev['retrieval_plan_contract_passed'] == 240
    assert all(r['source_identity_matches_expected'] for r in dev['observations'])
    pending_ids = set()
    for name in ['c_stage_l026', 'c_stage_l028', 'c_stage_l029', 'c_stage_l030']:
        pending_ids.update(json.loads(line)['id'] for line in (AGENT / 'curation/upper' / f'{name}.pending.jsonl').read_text(encoding='utf-8').splitlines() if line.strip())
    changes = [
        ('upper-l026-c-stage-pending-negative-price-cost-size-and-warrant-identity',
         ['two-phases-cost-zero-then-earn-shares', 'before-zero-swing-must-not-increase-plan-shares', 'after-zero-reinvest-swing-proceeds-for-more-shares'],
         '31给零成本前回现金不增计划数量、零后用卖出所得增股的两阶段；负价格不等负报价，仍无费用/账户证明，也未识别旧未具名权证。'),
        ('upper-l026-c-stage-pending-level-quantity-signal-and-trend-regime',
         ['capacity-thirty-float-versus-minute-ten-day-volume', 'capital-zero-point-five-float-does-not-decide-entry', 'skill-based-entry-size-three-vs-eight-thousand'],
         '31补30分以上流通盘千分五与1分10天均量1%不同分母，并给技能分仓例；未补完整单位换算/冲击模型，数量仍不取代买入位置与大级别阶段。'),
        ('upper-l028-c-stage-pending-second-third-points-center-referents-and-daily-alignment',
         ['third-buy-not-necessarily-after-consolidation-divergence', 'feb15-center-1048-1129-third-buy-1413', 'a-c-consolidation-and-internal-c-divergence-nesting'],
         '31补三买可无盘背、2/15三段同级/延伸/1413个例与A/C及C内部两重比较；不认后每一中枢第三下行都是三买，原所有指代未全解决。'),
        ('upper-l029-c-stage-pending-three-outcomes-dd-and-type-completion',
         ['consolidation-type-contains-one-center-not-equal-center', 'weekly-three-legs-original-explicitly-qualified', 'weekly-center-first-daily-then-expand-case'],
         '31明确盘整含相应中枢却非中枢对象，周线粗三段由作者明确收窄为第一段内部第三小段；仍待32/33扩张细节，不伪称定理证明和唯一分解完成。'),
        ('upper-l030-c-stage-pending-center-level-count-and-third-buy-completion',
         ['feb15-center-1048-1129-third-buy-1413', 'third-buy-not-necessarily-after-consolidation-divergence', 'perfect-means-center-eventually-forms-count-type'],
         '31再示前三段同级、后延伸及三买完结个例，趋势/盘整是相应级别中枢数量区别；不由任意两个框认证完整趋势，也不取消三买次级回抽条件。'),
        ('upper-l030-c-stage-pending-entered-leg-breakage-versus-guaranteed-result',
         ['standard-trend-nesting-with-sudden-break-exception', 'small-divergence-adjustment-not-necessarily-large', '099-five-main-fall-even-one-divergence-wait-parent'],
         '31直接列标准趋势大到小嵌套及突发破裂例外，5分主跌中1分背驰仍不能单用；进入段非成功背驰，父级阶段限制及实际成交收益未核。'),
    ]
    followups = []
    for pending_id, slugs, finding in changes:
        ids = ['upper-l031-c-stage-' + slug for slug in slugs]
        assert pending_id in pending_ids and all(id in known for id in ids)
        followups.append({'pending_id': pending_id, 'status': 'new_source_located_scope_still_pending',
                          'new_claim_ids': ids, 'finding': finding, 'global_pending_not_closed': True, 'graph_version': VERSION})
    (AGENT / 'curation/upper/c_stage_l031.partial-resolutions.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n' for r in followups), encoding='utf-8')
    checks = [
        '47条JSON Schema及引用/身份/映射/坐标预检',
        '183段原文哈希及全段台账一致，实际PDF219至232共14页及6完整图视觉核对',
        '原2212命题3183已复核证据未改，9647段528图逐行比较仅6图来源备注授权变更，原文/映射/几何全不改',
        '33项当前工作区Node测试通过（原有27项及另行验收的检索评测6项）',
        '2259条已复核命题全量引用校验0错误',
        '6组来源/条件边界及7组CLI/公共/桌面模块一致，只读哈希不变',
        '240/240冻结开发取证计划和已标注来源身份回归通过，无新题替换',
        '2259命题/262概念/362关系JSONL及Markdown/coverage同版本导出',
        '6条旧待核补充关联，原问题全部保持开放',
    ]
    not_run = ['240题完整类别/自然问题基线/生成回答评分/消融对抗验收未完成；开发取证计划通过不能代替',
               '32至61共30课完整语义及全书跨课/图文审查未完成',
               '独立Agent打包后运行及Windows真实离线/缩放旋转跨页交互未验收']
    acceptance = '31课47条55证据及6图来源已发布；2259引用/240冻结开发题回归通过；9待核及全书/产品目标未完成。'
    next_action = f'接续上册32课，实际PDF{next_row[1]}页标题；核对走势当下、思维方式及31所预告中枢扩张内容，逐段逐图核实身份/完成状态/条件。'
    evaluation = {'executable_development_cases': 240, 'target': 240, 'gold_review_status': 'model_reviewed_development',
                  'human_gold_reviewed': False, 'independent_test_set': False, 'generated_answers_scored': False,
                  'retrieval_plan_and_source_identity_passed_on_current_graph': 240, 'full_stage_g_acceptance_complete': False,
                  'new_project_gold_cases_created_in_this_batch': 0,
                  'note': '冻结开发取证计划及本批边界检查通过，不证明完整G、独立金标准或实际桌面交互通过。'}
    path = AUDIT / 'stage-c-l031-publication.json'
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
    assert progress['graph_version'] in ['0.1.0-review-958d0b42fad7', VERSION]
    if progress['graph_version'] != VERSION:
        progress['previous_checkpoint'] = {key: progress[key] for key in ['graph_version', 'completed', 'next_action', 'evaluation']}
    outputs = ['source-audit/stage-c-l031-' + name + '.json' for name in ['source-plan', 'source-applied', 'source-invariants', 'publication', 'verification']]
    progress['machine_outputs'] = list(dict.fromkeys(progress['machine_outputs'] + outputs + ['upper/c_stage_l031.partial-resolutions.jsonl']))
    progress.update(updated_at=datetime.now(timezone.utc).isoformat(), graph_version=VERSION, counts=counts,
                    claim_status_counts=claim_status, figure_origin_counts=figure_status, unit_processing_status_counts=unit_status,
                    semantic_completion=False, completed=[
                        '上册31课183段14页6图同模型四轮审读，47命题55证据13关系支撑发布，新增零成本持仓/交易容量2概念',
                        '6图5文后1原发未核，1996故事未具名不由深天地A图名认证；原文/身份/日期/字符映射与几何逐行不改',
                        '原2212命题3183证据未改；零成本前后两阶段、计划总量与机动量、一次性与弱技术3千分批范围分开，退出除非短语不补形式OR信号',
                        '交易容量流通盘千分五与1分10天均量1%不同分母，盘整含中枢非中枢对象，前三段同级/延伸/三买1413均按个例',
                        '周线第三段原说与作者明确不严谨自我限定联合取证，先日线再扩张且目前第一段第三小段；标准区间套突发破裂例外及主升主跌父段限制保留；9待核',
                        '2259命题/262概念/362关系同版本导出；33工程/2259引用、6边界和7组CLI/公共/桌面模块一致通过',
                        '240冻结开发取证计划与已标注身份回归通过，不增题凑数；6条旧待核补充均开放，余30课',
                    ], pending=[
                        '本批9待核见upper/c_stage_l031.pending.jsonl：成本两阶段、一次性/分批/退出、历史身份/自述、容量分母、周线更正、分钟时段/C方向、三买/盘背/中枢、父级段/突发例外、图源及预测',
                        '32至61共30课未完整语义审读；78课有阅读记录含历史62至64，不等全书技术抽取或全部解释统一',
                        '240题完整类别、自然问题基线、生成回答评分、消融对抗与全书跨课/图文审查未完成',
                        '独立Agent实际交付运行及Windows真实离线/缩放旋转跨页交互未验收',
                    ], checks_run=checks, checks_not_run=not_run, acceptance=acceptance,
                    next_resume_anchor=next_anchor, next_action=next_action,
                    coverage_caveat='31课183段14页6图同模型四轮，累计78课阅读记录含历史62至64，不称独立复核或全书完成。',
                    evaluation=evaluation,
                    previous_turn_classification='progress：31课183段14页6图和47条55证据发布；2259引用/240冻结开发题回归通过，余30课。')
    write(path, progress)
    print(json.dumps({'graph_version': VERSION, 'reviewed': 2259, 'development_cases': 240,
                      'remaining_lessons': 30, 'next_anchor': next_anchor, 'semantic_completion': False}, ensure_ascii=False))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
