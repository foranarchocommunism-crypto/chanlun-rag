"""Publish pilot64 after preflight, preserving all original source and evidence."""
import hashlib,json,shutil,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
import jsonschema
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';LOWER=AGENT/'curation/lower';AUDIT=Path(__file__).resolve().parent;BASE='c_stage_l064'
sys.path.insert(0,str(AGENT/'tools'))
from import_curation import import_batches,load_records
from curation_contract import validate_records
from graph_release import refresh_version,update_manifest
def j(v):return json.dumps(v,ensure_ascii=False,separators=(',',':'))
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def lines(p):return [json.loads(l) for l in p.read_text(encoding='utf-8-sig').splitlines() if l.strip()]
def ro(p=KB/'graph.sqlite'):
 d=sqlite3.connect(p.as_uri()+'?mode=ro',uri=True);d.row_factory=sqlite3.Row;return d
def append(p,rows):
 with p.open('a',encoding='utf-8') as f:
  for r in rows:f.write(j(r)+'\n')
def counts(d):return {t:d.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']}
def main():
 batch=LOWER/f'{BASE}.reviewed.jsonl';records,hashes=load_records([batch]);data=[r[0] for r in records];summary=read(LOWER/f'{BASE}.summary.json');plan=read(AUDIT/'stage-h-l064-amendment-plan.json')
 ledger=lines(LOWER/f'{BASE}.coverage.jsonl');pending=lines(LOWER/f'{BASE}.pending.jsonl');figs=lines(LOWER/f'{BASE}.figures.jsonl')
 assert len(data)==summary['claims']==42 and sum(len(r['evidence']) for r in data)==62 and len(ledger)==223 and len(figs)==5
 validator=jsonschema.Draft202012Validator(read(AGENT/'contracts/curation.schema.json'))
 for r in data:validator.validate(r)
 db=ro()
 try:
  meta={r['key']:json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')};assert meta['graph_version']==summary['graph_version']==plan['base_graph_version']==read(KB/'manifest.json')['graph_version']
  assert not any(db.execute('SELECT 1 FROM claims WHERE id=?',(r['id'],)).fetchone() for r in data);validate_records(db,KB,records)
  source={r['id']:dict(r) for r in db.execute("SELECT * FROM passages WHERE unit_id='lesson-064'")};assert set(source)=={r['passage_id'] for r in ledger} and len(source)==223
  assert all(hashlib.sha256(source[r['passage_id']]['text'].encode()).hexdigest()==r['source_text_sha256'] for r in ledger)
  assert hashlib.sha256(j(sorted(source.values(),key=lambda r:r['id'])).encode()).hexdigest()==summary['source_passages_snapshot_sha256']
  assert db.execute("SELECT count(*) FROM claims WHERE review_status='reviewed'").fetchone()[0]==3327
  now=datetime.now(timezone.utc);backup=KB.parent/'backups'/(now.strftime('%Y%m%dT%H%M%S%fZ')+'-curation-l064');backup.mkdir(parents=True,exist_ok=False)
  with sqlite3.connect(backup/'graph.sqlite') as t:db.backup(t)
 finally:db.close()
 shutil.copy2(KB/'manifest.json',backup/'manifest.json');write(backup/'amendment-plan.json',plan)
 for n in ['coverage.jsonl','pending.jsonl','figure_reviews.jsonl']:shutil.copy2(LOWER/n,backup/n)
 db=sqlite3.connect(KB/'graph.sqlite');db.row_factory=sqlite3.Row
 try:
  db.execute('PRAGMA foreign_keys=ON');db.execute('BEGIN IMMEDIATE');assert json.loads(db.execute("SELECT value FROM metadata WHERE key='graph_version'").fetchone()[0])==plan['base_graph_version']
  for op in plan['figure_operations']:
   r=dict(db.execute('SELECT * FROM figures WHERE id=?',(op['id'],)).fetchone());assert all(r[k]==v for k,v in op['before'].items());db.execute('UPDATE figures SET origin_status=?,note=? WHERE id=?',(op['after']['origin_status'],op['after']['note'],op['id']))
  for op in plan['claim_review_note_amendments']:
   assert db.execute('SELECT review_note FROM claims WHERE id=?',(op['id'],)).fetchone()[0]==op['before_review_note'];db.execute('UPDATE claims SET review_note=? WHERE id=?',(op['after_review_note'],op['id']))
   checks=dict(review_type='early_pilot_specific_figure_case_now_reviewed',base_graph_version=plan['base_graph_version'],claim_semantics_and_all_evidence_unchanged=True,source_passages_unchanged=True,figure_origins={r['id']:r['origin_status'] for r in figs},independent_review_claimed=False,amendment_plan='stage-h-l064-amendment-plan.json')
   rid='review-'+hashlib.sha256((op['id']+j(checks)).encode()).hexdigest()[:16];db.execute('INSERT INTO reviews VALUES(?,?,?,?,?,?,?)',(rid,op['id'],summary['reviewer'],now.isoformat(),j(checks),'reviewed',op['reason']))
  assert not db.execute('PRAGMA foreign_key_check').fetchall();intermediate=refresh_version(db);current_counts=counts(db);db.commit()
 except Exception:db.rollback();raise
 finally:db.close()
 update_manifest(KB,intermediate,counts=current_counts,updated_at=now.isoformat())
 amendment=dict(base_graph_version=plan['base_graph_version'],graph_version=intermediate,backup_directory=str(backup),figure_metadata_updated=5,review_notes_amended=2,claim_semantic_changes=0,source_and_evidence_changes=0,phase='amendment_applied_batch_not_yet_imported');write(AUDIT/'stage-h-l064-amendment-applied.json',amendment)
 blocking=[r['id'] for r in pending if r['blocks_full_semantic_extraction_completion']]
 log=dict(lesson_number=64,document_id=summary['document_id'],batch=batch.name,whole_lesson_semantic_read_complete=True,technical_extraction_complete=False,four_round_review=True,reviewer=summary['reviewer'],passages_read=223,new_claims=42,pending=[r['id'] for r in pending],blocking_extraction_pending=blocking,source_batch_summary=f'{BASE}.summary.json',coverage_ledger=f'{BASE}.coverage.jsonl',base_graph_version=intermediate,logged_at=now.isoformat(),figure_origin_review=dict(later_figures=4,unverified_figures=1,source_audit='stage-h-l064-amendment-applied.json'))
 append(LOWER/'coverage.jsonl',[log]);append(LOWER/'pending.jsonl',pending);append(LOWER/'figure_reviews.jsonl',figs)
 try:result=import_batches(KB,[batch])
 except Exception:
  for n in ['coverage.jsonl','pending.jsonl','figure_reviews.jsonl']:shutil.copy2(backup/n,LOWER/n)
  raise
 old=ro(backup/'graph.sqlite');new=ro()
 try:
  for t in ['documents','pages','passages']:
   assert [tuple(r) for r in old.execute(f'SELECT * FROM {t} ORDER BY id')]==[tuple(r) for r in new.execute(f'SELECT * FROM {t} ORDER BY id')],t
  fops={r['id']:r['after'] for r in plan['figure_operations']}
  for r in old.execute('SELECT * FROM figures'):
   expected=dict(r);expected.update(fops.get(r['id'],{}));assert dict(new.execute('SELECT * FROM figures WHERE id=?',(r['id'],)).fetchone())==expected
  cnotes={r['id']:r['after_review_note'] for r in plan['claim_review_note_amendments']};old_claims=list(old.execute("SELECT * FROM claims WHERE review_status='reviewed'"))
  for r in old_claims:
   expected=dict(r)
   if r['id'] in cnotes:expected['review_note']=cnotes[r['id']]
   assert dict(new.execute('SELECT * FROM claims WHERE id=?',(r['id'],)).fetchone())==expected
  old_evidence=list(old.execute("SELECT e.* FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed'"))
  for r in old_evidence:assert dict(new.execute('SELECT * FROM evidence WHERE id=?',(r['id'],)).fetchone())==dict(r)
  final_counts=counts(new);reviewed=new.execute("SELECT count(*) FROM claims WHERE review_status='reviewed'").fetchone()[0];assert reviewed==3369
  reviewed_evidence=new.execute("SELECT count(*) FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed'").fetchone()[0];assert reviewed_evidence==4584
 finally:old.close();new.close()
 amendment.update(phase='amendment_and_batch_published',final_graph_version=result['graph_version'],all_original_reviewed_claim_semantics_unchanged=len(old_claims),all_original_reviewed_evidence_unchanged=len(old_evidence),all_source_rows_unchanged=True,**{'pass':True});write(AUDIT/'stage-h-l064-amendment-applied.json',amendment)
 report=dict(stage='H early pilot64 completion',base_graph_version=plan['base_graph_version'],graph_version=result['graph_version'],schema_version=summary['schema_version'],backup_directory=str(backup),batch_sha256=hashes,new_claims=42,new_evidence=62,reviewed_claims=reviewed,reviewed_evidence=reviewed_evidence,counts=final_counts,passages_read=223,figure_objects_viewed=5,figure_origin_counts=summary['figure_origin_counts'],new_concepts=summary['new_concepts'],original_reviewed_claim_semantics_unchanged=len(old_claims),original_reviewed_evidence_unchanged=len(old_evidence),only_2_review_note_caveats_amended=True,all_source_text_geometry_mapping_unchanged=True,pending=summary['pending'],formal_import='passed',semantic_completion=False,delivery_scope='shared_knowledge_base_only',checks_run=['42条Schema和引用/身份/映射/坐标预检','223段全台账哈希、21实际页5整图核对','907页9650段逐行不变，528图仅5项元数据；旧3327命题语义和4522引文/定位保持，仅两旧图审待核描述更新'],checks_not_run=['发布后全引用/现有测试/边界与冻结检索及同版本导出待执行','全书最终知识库质量审计、目录归档及实际文件哈希尚未完成'])
 write(AUDIT/'stage-h-l064-publication.json',report);print(j(report))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');sys.stderr.reconfigure(encoding='utf-8');main()
