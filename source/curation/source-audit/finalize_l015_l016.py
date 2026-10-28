"""Record verified post-publication state without changing the knowledge graph."""
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2]
KB = AGENT.parent / 'shared-knowledge/v0.1.0'
VERSION = '0.1.0-review-a38ea0d31c7c'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
    try:
        metadata = {k: json.loads(v) for k, v in db.execute('SELECT key,value FROM metadata')}
        assert metadata['graph_version'] == VERSION
        counts = {t: db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
                  for t in ['documents', 'pages', 'units', 'passages', 'figures', 'concepts', 'claims', 'evidence', 'relations', 'reviews']}
        claim_status = db.execute('SELECT review_status,COUNT(*) FROM claims GROUP BY review_status ORDER BY review_status').fetchall()
        figure_status = db.execute('SELECT origin_status,COUNT(*) FROM figures GROUP BY origin_status ORDER BY origin_status').fetchall()
        unit_status = db.execute('SELECT processing_status,COUNT(*) FROM units GROUP BY processing_status ORDER BY processing_status').fetchall()
        assert counts == dict(documents=2, pages=907, units=110, passages=9647, figures=528,
                              concepts=238, claims=4604, evidence=5495, relations=292, reviews=2026)
        assert dict(claim_status)['reviewed'] == 1965
        assert dict(unit_status)['extracted'] == 37
        next_row = db.execute('SELECT unit_id FROM passages WHERE id=?', ('volume_1-a53e99c37ca5-p0144-b004',)).fetchone()
        assert next_row == ('lesson-025',)
    finally:
        db.close()

    assert read(KB / 'manifest.json')['graph_version'] == VERSION
    exports = {}
    for name, expected in [('claims', 1965), ('concepts', 238), ('relations', 292)]:
        path = KB / 'exports' / f'{name}.jsonl'
        rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
        assert len(rows) == expected and all(row['graph_version'] == VERSION for row in rows)
        exports[name] = {'rows': len(rows), 'graph_version': VERSION, 'sha256': sha(path)}
    assert VERSION in (KB / 'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150]
    assert read(KB / 'exports/coverage.json')['graph_version'] == VERSION

    audit = AGENT / 'curation/source-audit'
    inv = read(audit / 'stage-c-l015-l016-source-invariants.json')
    assert inv['pass'] and inv['graph_version'] == VERSION
    assert inv['original_reviewed_claims_unchanged'] == 1905
    assert inv['original_reviewed_evidence_unchanged'] == 2773
    verification = read(audit / 'stage-c-l015-l016-verification.json')
    assert verification['graph_version'] == VERSION
    assert len(verification['checks']) == len(verification['parity']) == 7
    assert all(row['cli_matches_shared'] and row['desktop_module_matches_shared'] for row in verification['parity'])
    dev = read(AGENT / 'evaluation/stage-g-development-current.results.json')
    assert dev['graph_version'] == VERSION
    assert dev['executable_development_cases'] == dev['retrieval_plan_contract_passed'] == 240
    assert all(row['source_identity_matches_expected'] for row in dev['observations'])
    cases = [json.loads(line) for line in (AGENT / 'evaluation/stage-g-batch-25.cases.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    assert len(cases) == 12
    date_refs = sum('published_at' in ref for case in cases for ref in case['expected_source_refs'])
    assert date_refs == sum(len(case['expected_source_refs']) for case in cases) == 33
    followups = [json.loads(line) for line in (AGENT / 'curation/upper/c_stage_l015_l016.partial-resolutions.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    assert len(followups) == 4 and all(row['global_pending_not_closed'] for row in followups)

    checks = [
        '60条JSON Schema及引用/身份/映射/坐标预检',
        '194段原文哈希及全段台账一致，18页14图实际视觉核对',
        '原1905条命题2773条已复核证据未改，9647段528图仅3段14图授权元数据变更',
        '33项当前工作区Node测试通过（原有27项及新增检索评测6项）；新增基线文件另行验收',
        '1965条已复核命题全量引用校验0错误',
        '7组语义边界断言与7组CLI/公共/桌面模块结果一致，只读哈希不变',
        '1965命题/238概念/292关系JSONL及Markdown/coverage同版本导出',
        '240/240同模型开发题取证计划及已标注身份通过；本批12题33条来源引用含日期核对',
        '4条旧待核补充关联保留原待核开放状态',
    ]
    not_run = [
        '240题完整验收尚未完成：开发取证计划检查不等于自然问题基线和生成回答评分',
        '37课25至61的完整语义审读及全书跨课/图文统一审查未完成',
        '独立Agent打包后运行和Electron Windows真实离线/缩放旋转跨页交互验收未完成',
    ]
    acceptance = '15至16课60条83证据、3段身份时间及14图元数据已发布；1965引用/240开发取证计划通过；8待核与全书/产品目标仍未完成。'
    next_action = '接续上册25课，从实际PDF144页标题开始；审读吻、MACD、背驰、中枢的联系，保留级别、作者/读者、原图和跨课补充的证据边界。'
    evaluation = {'executable_development_cases': 240, 'target': 240,
                  'gold_review_status': 'model_reviewed_development', 'human_gold_reviewed': False,
                  'independent_test_set': False, 'generated_answers_scored': False,
                  'retrieval_plan_and_source_identity_passed_on_current_graph': 240,
                  'batch_25_date_annotated_source_refs_checked': date_refs,
                  'full_stage_g_acceptance_complete': False}
    path = audit / 'stage-c-l015-l016-publication.json'
    pub = read(path)
    assert pub['graph_version'] == VERSION and pub['formal_import'] == 'passed'
    pub.update(updated_at=datetime.now(timezone.utc).isoformat(), checks_run=checks,
               checks_not_run=not_run, acceptance=acceptance, next_action=next_action,
               exports=exports, final_sha256={'database': sha(KB / 'graph.sqlite'), 'manifest': sha(KB / 'manifest.json')},
               development_evaluation=evaluation, partial_pending_followups=4,
               semantic_completion=False, writes_to_knowledge_graph_by_this_finalizer=False)
    write(path, pub)

    path = AGENT / 'curation/progress.json'
    progress = read(path)
    assert progress['graph_version'] in ['0.1.0-review-c5310a86c5bb', VERSION]
    if progress['graph_version'] != VERSION:
        progress['previous_checkpoint'] = {key: progress[key] for key in ['graph_version', 'completed', 'next_action', 'evaluation']}
    outputs = ['source-audit/stage-c-l015-l016-' + name + '.json'
               for name in ['source-plan', 'source-applied', 'source-invariants', 'publication', 'verification']]
    outputs += ['upper/c_stage_l015_l016.partial-resolutions.jsonl', '../evaluation/stage-g-batch-25.cases.jsonl', '../evaluation/stage-g-batch-25.results.json']
    progress['machine_outputs'] = list(dict.fromkeys(progress['machine_outputs'] + outputs))
    progress.update(updated_at=datetime.now(timezone.utc).isoformat(), graph_version=VERSION,
                    counts=counts, claim_status_counts=claim_status, figure_origin_counts=figure_status,
                    unit_processing_status_counts=unit_status, semantic_completion=False,
                    completed=[
                        '上册15至16课194段18页14图同模型四轮审读，60命题83证据13关系支撑发布，新增13概念',
                        '64页舞者两段读者和无时间作者答复分别修正，74页截断年份保留null；14图10后加4未核',
                        '原1905已复核命题2773证据及全部源原文/字符映射/坐标未改，来源备份逐行比较通过',
                        '早期高低点不严格及顺势平台、同级两同向趋势前提、两均线力度/平均力度/MACD柱波、拒绝盘整策略范围分别保留；8待核',
                        '日周持仓买点与15分箱型、T+1和资金条件、038004认沽、缺口原词及作者收益/概率自述保留原范围',
                        '1965命题/238概念/292关系同版本导出，1965引用0错误；7组边界与7组CLI/公共/桌面模块一致',
                        '当前工作区33项工程测试通过；240开发题取证计划和身份通过，本批33来源引用含日期；不称完整基线或回答验收',
                        '4条旧待核补充记录已关联，均未关闭全局待核；继续25至61共37课',
                    ],
                    pending=[
                        '本批8待核见upper/c_stage_l015_l016.pending.jsonl：早期分类/等值/顺势平台、首吻/盘整、力度面积/长度、MACD柱线组合、概率收益/时效、权证缺口/周期、读者年份、配图来源',
                        '25至61共37课未完整语义审读；71课已有阅读记录含历史62至64，不代表全书技术抽取或全部解释统一',
                        '240题完整评测、自然问题基线、生成回答评分和全书跨课/图文审查未完成',
                        '独立Agent实际交付运行及Windows真实离线/缩放旋转跨页交互未验收',
                    ], checks_run=checks, checks_not_run=not_run, acceptance=acceptance,
                    next_resume_anchor='volume_1-a53e99c37ca5-p0144-b004 / lesson-025', next_action=next_action,
                    coverage_caveat='本批15至16课194段18页14图，累计71课阅读记录含历史62至64；同模型四轮，不称独立复核或全书完成。',
                    evaluation=evaluation,
                    previous_turn_classification='progress：第15至16课194段14图、3源修正与60条83证据正式发布；1965引用/240开发取证计划通过，余37课。')
    write(path, progress)
    print(json.dumps({'graph_version': VERSION, 'reviewed': 1965, 'exports': exports,
                      'development_cases': 240, 'remaining_lessons': 37, 'semantic_completion': False}, ensure_ascii=False))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
