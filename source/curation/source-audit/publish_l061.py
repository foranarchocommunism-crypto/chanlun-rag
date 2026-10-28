"""Publish manually reviewed 61; preflight and backup precede all writes."""
import hashlib
import json
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
import jsonschema

AGENT=Path(__file__).resolve().parents[2]
KB=AGENT.parent/'shared-knowledge/v0.1.0'
UPPER=AGENT/'curation/upper'
BASE='c_stage_l061'
sys.path.insert(0,str(AGENT/'tools'))
from import_curation import import_batches, load_records
from curation_contract import validate_records

def lines(path):
    return [json.loads(x) for x in path.read_text(encoding='utf-8-sig').splitlines() if x.strip()]
def ro():
    db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    return db
def snapshot(db):
    return ({r['id']:dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")},
            {r['id']:dict(r) for r in db.execute("SELECT e.* FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed'")})
def append(path,data):
    with path.open('a',encoding='utf-8') as out:
        for item in data:out.write(json.dumps(item,ensure_ascii=False,separators=(',',':'))+'\n')

def main():
    batch=UPPER/f'{BASE}.reviewed.jsonl'
    records,hashes=load_records([batch]);data=[r[0] for r in records]
    summary=json.loads((UPPER/f'{BASE}.summary.json').read_text(encoding='utf-8'))
    ledger=lines(UPPER/f'{BASE}.coverage.jsonl');pending=lines(UPPER/f'{BASE}.pending.jsonl')
    figures=lines(UPPER/f'{BASE}.figures.jsonl')
    validator=jsonschema.Draft202012Validator(json.loads((AGENT/'contracts/curation.schema.json').read_text(encoding='utf-8')))
    for r in data:validator.validate(r)
    db=ro()
    try:
        metadata={r['key']:json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
        assert metadata['graph_version']==summary['graph_version'],'base changed'
        assert metadata['graph_version']==json.loads((KB/'manifest.json').read_text(encoding='utf-8'))['graph_version']
        assert not any(db.execute('SELECT 1 FROM claims WHERE id=?',(r['id'],)).fetchone() for r in data),'already imported'
        validate_records(db,KB,records)
        source={r['id']:r['text'] for r in db.execute("SELECT id,text FROM passages WHERE unit_id = 'lesson-061'")}
        assert len(source)==len(ledger)==83 and set(source)=={r['passage_id'] for r in ledger}
        assert all(hashlib.sha256(source[r['passage_id']].encode()).hexdigest()==r['source_text_sha256'] for r in ledger)
        before_claims,before_evidence=snapshot(db)
        assert len(before_claims)==3268 and len(before_evidence)==4453
        now=datetime.now(timezone.utc)
        backup=KB.parent/'backups'/(now.strftime('%Y%m%dT%H%M%S%fZ')+'-curation-l061')
        backup.mkdir(parents=True,exist_ok=False)
        with sqlite3.connect(backup/'graph.sqlite') as target:db.backup(target)
        shutil.copy2(KB/'manifest.json',backup/'manifest.json')
    finally:db.close()
    for name in ['coverage.jsonl','pending.jsonl','figure_reviews.jsonl']:shutil.copy2(UPPER/name,backup/name)
    coverage=[]
    for lesson in [61]:
        issues=[r for r in pending if lesson in r['lesson_numbers']]
        blocking=[r['id'] for r in issues if r['blocks_full_semantic_extraction_completion']]
        coverage.append({'lesson_number':lesson,'document_id':summary['document_id'],'batch':batch.name,
          'whole_lesson_semantic_read_complete':True,'technical_extraction_complete':not bool(blocking),
          'four_round_review':True,'reviewer':summary['reviewer'],'passages_read':sum(r['lesson_number']==lesson for r in ledger),
          'new_claims':sum(r['id'].startswith(f'upper-l{lesson:03d}-') for r in data),'pending':[r['id'] for r in issues],
          'blocking_extraction_pending':blocking,'source_batch_summary':f'{BASE}.summary.json','coverage_ledger':f'{BASE}.coverage.jsonl',
          'base_graph_version':metadata['graph_version'],'logged_at':now.isoformat()})
    for log in coverage:
        selected=figures
        log['figure_origin_review']={'later_figures':sum(f['origin_status']=='later_annotation' for f in selected),'unverified_figures':sum(f['origin_status']=='unverified' for f in selected),'source_audit':'stage-c-l061-source-applied.json'}
    append(UPPER/'coverage.jsonl',coverage);append(UPPER/'pending.jsonl',pending);append(UPPER/'figure_reviews.jsonl',figures)
    try:result=import_batches(KB,[batch])
    except Exception:
        for name in ['coverage.jsonl','pending.jsonl','figure_reviews.jsonl']:shutil.copy2(backup/name,UPPER/name)
        raise
    db=ro()
    try:
        after_claims,after_evidence=snapshot(db)
        assert all(after_claims[k]==v for k,v in before_claims.items())
        assert all(after_evidence[k]==v for k,v in before_evidence.items())
        counts={table:db.execute(f'SELECT count(*) FROM {table}').fetchone()[0] for table in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']}
    finally:db.close()
    report={'stage':'C/E','run_mode':'authorized_execution','schema_version':metadata['schema_version'],
      'base_graph_version':metadata['graph_version'],'graph_version':result['graph_version'],
      'scope':'第61课83段，PDF457至470十四页11图；8来源日期与7未核4后加图，区间套四重/结合律至少五次级、仓量容量、嵌套旧答/原字编号/三精度算法与时效',
      'new_claims':len(data),'new_evidence':sum(len(r['evidence']) for r in data),'relation_supports_added':sum(len(r['relations']) for r in data),
      'reviewed_before':len(before_claims),'reviewed_after':len(after_claims),'counts':counts,
      'original_reviewed_claims_and_evidence_unchanged':True,'batch_sha256':hashes,'backup_directory':str(backup),
      'reviewer':summary['reviewer'],'formal_import':'passed','pending':summary['pending'],
      'source_structure_changes':'stage-c-l061-source-applied.json',
      'checks_run':['44条Schema及引用/身份/映射/坐标预检','83段全台账与原文哈希一致','原3268命题4453证据未改'],
      'checks_not_run':['导入后全引用/边界与导出待接续','原冻结检索回归诚实披露，非回答金标准'],
      'delivery_scope':'shared_knowledge_base_only',
      'acceptance':'44命题52证据发布，7待核；108课均有完整阅读记录，区间套/五次级与精度时效分存，全书来源/覆盖/最终交付审计未完成。',
      'next_action':'验证知识库引用、来源边界、同版本导出及恢复点；不构建软件'}
    (Path(__file__).parent/'stage-c-l061-publication.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
