"""Record the separately verified figure-link amendment and its exports."""
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2]
KB = AGENT.parent / 'shared-knowledge/v0.1.0'
AUDIT = Path(__file__).resolve().parent
VERSION = '0.1.0-review-df7b7562fbf3'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    report_path = AUDIT / 'stage-c-l031-figure-links-amendment.json'
    report = read(report_path)
    assert report['graph_version'] == VERSION
    verification = read(AUDIT / 'stage-c-l031-figure-links-verification.json')
    assert verification['pass'] and verification['graph_version'] == VERSION and len(verification['checks']) == 5
    dev = read(AGENT / 'evaluation/stage-g-development-current.results.json')
    assert dev['graph_version'] == VERSION and dev['executable_development_cases'] == dev['retrieval_plan_contract_passed'] == 240
    assert all(r['source_identity_matches_expected'] for r in dev['observations'])
    assert read(KB / 'manifest.json')['graph_version'] == VERSION
    exports = {}
    for name, count in [('claims', 2259), ('concepts', 262), ('relations', 362)]:
        path = KB / 'exports' / (name + '.jsonl')
        rows = [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
        assert len(rows) == count and all(r['graph_version'] == VERSION for r in rows)
        exports[name] = {'rows': count, 'sha256': sha(path)}
    path = AGENT / 'curation/upper/c_stage_l031.figure-links-amended.figures.jsonl'
    assert not path.exists(), 'Do not append the same amendment review twice'
    db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True); db.row_factory = sqlite3.Row
    try:
        assert json.loads(db.execute("SELECT value FROM metadata WHERE key='graph_version'").fetchone()[0]) == VERSION
        figures = []
        for f in db.execute("SELECT * FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 219 AND 232 ORDER BY id"):
            row = dict(f)
            row.update(visual_review_complete=True, reviewer='Codex 主代理 / 第31课配图关联显式修复',
                       visual_review_note=f['note'], figure_source_review='原批已视觉核对，修复索引导致的漏关联；原图来源状态未变。',
                       amendment='stage-c-l031-figure-links-amendment.json',
                       linked_claim_ids=[r[0] for r in db.execute('SELECT DISTINCT claim_id FROM evidence WHERE instr(figure_ids,?)>0 ORDER BY claim_id', (f['id'],))])
            figures.append(row)
    finally:
        db.close()
    assert sum(len(r['linked_claim_ids']) for r in figures) == 5
    text = ''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n' for r in figures)
    path.write_text(text, encoding='utf-8')
    with (AGENT / 'curation/upper/figure_reviews.jsonl').open('a', encoding='utf-8') as out:
        out.write(text)
    checks = ['五条配图关联CLI/公共/桌面模块逐项一致', '33工程测试通过', '2259引用全量检查零错误', '240冻结开发取证计划/身份回归通过', '同版本JSONL/Markdown/coverage重新导出']
    report.update(post_checks='passed', checks_run=checks, exports=exports,
                  final_sha256={'database': sha(KB / 'graph.sqlite'), 'manifest': sha(KB / 'manifest.json')},
                  finalized_at=datetime.now(timezone.utc).isoformat(), writes_to_knowledge_graph_by_this_finalizer=False)
    write(report_path, report)
    path = AGENT / 'curation/progress.json'; progress = read(path)
    assert progress['graph_version'] == report['base_graph_version']
    progress.update(graph_version=VERSION, counts=report['counts'], updated_at=datetime.now(timezone.utc).isoformat())
    progress['completed'].append('第31课五条证据漏图关联已显式迁移，旧命题/源数据/历史复核及原批SHA未改，新建5复核；5查询关联/33工程/2259引用/240开发取证回归及导出通过。')
    progress['machine_outputs'] += ['source-audit/stage-c-l031-figure-links-amendment.json', 'source-audit/stage-c-l031-figure-links-verification.json', 'upper/c_stage_l031.figure-links-amended.jsonl', 'upper/c_stage_l031.figure-links-amended.figures.jsonl']
    progress['previous_turn_classification'] = 'progress：显式修复31课五条漏图关联，保持原批与历史证据可追溯，继续32课。'
    write(path, progress)
    print(json.dumps({'graph_version': VERSION, 'amended_figure_links': 5, 'post_checks': 'passed', 'semantic_completion': False}, ensure_ascii=False))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
