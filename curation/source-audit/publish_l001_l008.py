"""Publish only the manually reviewed batch 06, with a recoverable snapshot.

No PDF extraction or source identity changes. Existing reviewed rows and evidence
must remain byte-for-byte equal as SQL values. This script refuses repeat imports.
"""
import hashlib
import json
import shutil
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2]
ROOT = AGENT.parent
KB = ROOT / 'shared-knowledge/v0.1.0'
UPPER = AGENT / 'curation/upper'
BASE = '06-l001-l008-complete'
sys.path.insert(0, str(AGENT / 'tools'))
from import_curation import import_batches, load_records
from curation_contract import validate_records
import jsonschema


def read_lines(path):
    return [json.loads(s) for s in path.read_text(encoding='utf-8-sig').splitlines() if s.strip()]


def ro():
    con = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    return con


def reviewed_snapshot(db):
    claims = {r['id']:dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
    evidence = {r['id']:dict(r) for r in db.execute("SELECT e.* FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed'")}
    return claims, evidence


def append(path, items):
    with path.open('a',encoding='utf-8') as stream:
        for item in items:
            stream.write(json.dumps(item,ensure_ascii=False,separators=(',',':'))+'\n')


def main():
    batch = UPPER / f'{BASE}.reviewed.jsonl'
    records, hashes = load_records([batch])
    data = [r[0] for r in records]
    summary = json.loads((UPPER / f'{BASE}.summary.json').read_text(encoding='utf-8'))
    ledger = read_lines(UPPER / f'{BASE}.coverage.jsonl')
    pending = read_lines(UPPER / f'{BASE}.pending.jsonl')
    figures = read_lines(UPPER / f'{BASE}.figures.jsonl')
    schema = json.loads((AGENT / 'contracts/curation.schema.json').read_text(encoding='utf-8'))
    for record in data:
        jsonschema.Draft202012Validator(schema).validate(record)
    db = ro()
    try:
        metadata = {r['key']:json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
        assert metadata['graph_version']==summary['graph_version'], 'batch base version changed'
        assert metadata['graph_version']==json.loads((KB/'manifest.json').read_text(encoding='utf-8'))['graph_version']
        assert not any(db.execute('SELECT 1 FROM claims WHERE id=?',(r['id'],)).fetchone() for r in data), 'already imported'
        validate_records(db,KB,records)
        all_source = {r['id']:r['text'] for r in db.execute("SELECT id,text FROM passages WHERE unit_id BETWEEN 'lesson-001' AND 'lesson-008'")}
        assert set(all_source)=={r['passage_id'] for r in ledger} and len(ledger)==len(all_source)==126
        assert all(hashlib.sha256(all_source[r['passage_id']].encode()).hexdigest()==r['source_text_sha256'] for r in ledger)
        before_claims, before_evidence = reviewed_snapshot(db)
        now = datetime.now(timezone.utc)
        backup = KB.parent / 'backups' / (now.strftime('%Y%m%dT%H%M%S%fZ')+'-curation-l001-l008')
        backup.mkdir(parents=True,exist_ok=False)
        destination = sqlite3.connect(backup / 'graph.sqlite')
        db.backup(destination)
        destination.close()
        shutil.copy2(KB/'manifest.json',backup/'manifest.json')
    finally:
        db.close()
    for name in ['coverage.jsonl','pending.jsonl','figure_reviews.jsonl']:
        shutil.copy2(UPPER/name,backup/name)
    per_lesson=[]
    for lesson in range(1,9):
        issue_ids=[x['id'] for x in pending if lesson in x['lesson_numbers']]
        blocking=[x['id'] for x in pending if lesson in x['lesson_numbers'] and x['blocks_full_semantic_extraction_completion']]
        per_lesson.append({'lesson_number':lesson,'document_id':summary['document_id'],'batch':batch.name,
            'whole_lesson_semantic_read_complete':True,'technical_extraction_complete':not bool(blocking),
            'four_round_review':True,'reviewer':summary['reviewer'],
            'passages_read':sum(x['lesson_number']==lesson for x in ledger),
            'new_claims':sum(r['id'].startswith(f'upper-l{lesson:03d}-') for r in data),
            'pending':issue_ids,'blocking_extraction_pending':blocking,
            'source_batch_summary':f'{BASE}.summary.json','coverage_ledger':f'{BASE}.coverage.jsonl',
            'base_graph_version':metadata['graph_version'],'logged_at':now.isoformat()})
    append(UPPER/'coverage.jsonl',per_lesson)
    append(UPPER/'pending.jsonl',pending)
    append(UPPER/'figure_reviews.jsonl',figures)
    try:
        result=import_batches(KB,[batch])
    except Exception:
        for name in ['coverage.jsonl','pending.jsonl','figure_reviews.jsonl']:
            shutil.copy2(backup/name,UPPER/name)
        raise
    db=ro()
    try:
        after_claims,after_evidence=reviewed_snapshot(db)
        assert all(after_claims[k]==v for k,v in before_claims.items()), 'existing reviewed claims changed'
        assert all(after_evidence[k]==v for k,v in before_evidence.items()), 'existing reviewed evidence changed'
        counts={t:db.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']}
    finally:
        db.close()
    report={'stage':'C','run_mode':'authorized_execution','schema_version':metadata['schema_version'],
        'base_graph_version':metadata['graph_version'],'graph_version':result['graph_version'],
        'scope':'第1至8课全部126段，实际PDF8至22共15页，7图对象',
        'new_claims':len(data),'new_evidence':sum(len(r['evidence']) for r in data),
        'reviewed_before':len(before_claims),'reviewed_after':len(after_claims),
        'original_reviewed_claims_and_evidence_unchanged':True,'counts':counts,
        'batch_sha256':hashes,'backup_directory':str(backup),'reviewer':summary['reviewer'],
        'formal_import':'passed','pending':summary['pending'],
        'checks_run':['60条JSON Schema和只读证据/身份/坐标/推论检查','126段源文本哈希与逐段台账一致','原646条已复核命题及所有证据未改'],
        'checks_not_run':['导入后的Node检查、validate及同版本导出待接续','240条真实评测未完成','Electron及打包后离线验收未完成'],
        'acceptance':'本批60条已复核命题已发布；8项待核单独保留；整个工程尚未验收',
        'next_action':'运行既有工程检查、validate和同版本导出，更新恢复记录'}
    (Path(__file__).parent/'stage-c-l001-l008-publication.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
