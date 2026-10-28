"""Publish bounded early-pilot completion with an explicit figure-link amendment."""
import hashlib,json,shutil,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
import jsonschema
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';LOWER=AGENT/'curation/lower';AUDIT=Path(__file__).resolve().parent
BASE='c_stage_l062_l063'
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
def main():
 batch=LOWER/f'{BASE}.reviewed.jsonl';records,hashes=load_records([batch]);data=[r[0] for r in records]
 summary=read(LOWER/f'{BASE}.summary.json');plan=read(AUDIT/'stage-h-l062-l063-amendment-plan.json')
 ledger=lines(LOWER/f'{BASE}.coverage.jsonl');pending=lines(LOWER/f'{BASE}.pending.jsonl');figures=lines(LOWER/f'{BASE}.figures.jsonl')
 assert len(data)==15 and len(ledger)==33 and len(figures)==6 and len(plan['evidence_figure_amendments'])==8
 validator=jsonschema.Draft202012Validator(read(AGENT/'contracts/curation.schema.json'))
 for r in data:validator.validate(r)
 db=ro()
 try:
  metadata={r['key']:json.loads(r['value']) for r in db.execute('SELECT * FROM metadata')}
  assert metadata['graph_version']==summary['graph_version']==plan['base_graph_version']==read(KB/'manifest.json')['graph_version']
  assert not any(db.execute('SELECT 1 FROM claims WHERE id=?',(r['id'],)).fetchone() for r in data)
  validate_records(db,KB,records)
  source={r['id']:r['text'] for r in db.execute("SELECT id,text FROM passages WHERE unit_id IN('lesson-062','lesson-063')")}
  assert len(source)==len(ledger) and set(source)=={r['passage_id'] for r in ledger}
  assert all(hashlib.sha256(source[r['passage_id']].encode()).hexdigest()==r['source_text_sha256'] for r in ledger)
  assert db.execute("SELECT count(*) FROM claims WHERE review_status='reviewed'").fetchone()[0]==3312
  now=datetime.now(timezone.utc);backup=KB.parent/'backups'/(now.strftime('%Y%m%dT%H%M%S%fZ')+'-curation-l062-l063');backup.mkdir(parents=True,exist_ok=False)
  with sqlite3.connect(backup/'graph.sqlite') as target:db.backup(target)
 finally:db.close()
 shutil.copy2(KB/'manifest.json',backup/'manifest.json');write(backup/'amendment-plan.json',plan)
 for n in ['coverage.jsonl','pending.jsonl','figure_reviews.jsonl']:shutil.copy2(LOWER/n,backup/n)
 db=sqlite3.connect(KB/'graph.sqlite');db.row_factory=sqlite3.Row
 try:
  db.execute('PRAGMA foreign_keys=ON');db.execute('BEGIN IMMEDIATE')
  assert json.loads(db.execute("SELECT value FROM metadata WHERE key='graph_version'").fetchone()[0])==plan['base_graph_version']
  for op in plan['figure_operations']:
   before=dict(db.execute('SELECT * FROM figures WHERE id=?',(op['id'],)).fetchone())
   assert all(before[k]==v for k,v in op['before'].items())
   db.execute('UPDATE figures SET origin_status=?,note=? WHERE id=?',(op['after']['origin_status'],op['after']['note'],op['id']))
  for op in plan['evidence_figure_amendments']:
   before=dict(db.execute('SELECT * FROM evidence WHERE id=?',(op['evidence_id'],)).fetchone())
   assert before['claim_id']==op['claim_id'] and json.loads(before['figure_ids'])==op['before_figure_ids']
   db.execute('UPDATE evidence SET figure_ids=? WHERE id=?',(j(op['after_figure_ids']),op['evidence_id']))
  old62=[r[0] for r in db.execute("SELECT id FROM claims WHERE id LIKE 'lower-l062-%' AND review_status='reviewed'")];assert len(old62)==12
  for cid in old62:
   checks=dict(review_type='early_pilot_original_diagram_association',base_graph_version=plan['base_graph_version'],claim_text_conditions_exceptions_and_quote_geometry_unchanged=True,original_evidence_ids_preserved=True,source_pdf_sha256=plan['source_pdf_sha256'],figure_review_note=next(f['note'] for f in figures if f['id'].endswith('p0006-fig2')),figure_origins={f['id']:f['origin_status'] for f in figures if f['lesson_number']==62},independent_review_claimed=False,amendment_plan='stage-h-l062-l063-amendment-plan.json')
   rid='review-'+hashlib.sha256((cid+j(checks)).encode()).hexdigest()[:16]
   db.execute('INSERT INTO reviews VALUES(?,?,?,?,?,?,?)',(rid,cid,summary['reviewer'],now.isoformat(),j(checks),'reviewed','实际复核正文指称的黑白图1至9；补空图关联，保留旧命题和所有引文/定位，后加彩色图单独标明。'))
  assert not db.execute('PRAGMA foreign_key_check').fetchall()
  intermediate=refresh_version(db);db.commit()
 except Exception:db.rollback();raise
 finally:db.close()
 update_manifest(KB,intermediate,updated_at=now.isoformat())
 amendment=dict(base_graph_version=plan['base_graph_version'],graph_version=intermediate,backup_directory=str(backup),figure_metadata_updated=6,evidence_links_added=8,old_claim_semantic_changes=0,source_text_mapping_geometry_changes=0,phase='amendment_applied_batch_not_yet_imported')
 write(AUDIT/'stage-h-l062-l063-amendment-applied.json',amendment)
 logs=[]
 for lesson in [62,63]:
  issues=[r for r in pending if lesson in r['lesson_numbers']];blocking=[r['id'] for r in issues if r['blocks_full_semantic_extraction_completion']]
  logs.append(dict(lesson_number=lesson,document_id=summary['document_id'],batch=batch.name,whole_lesson_semantic_read_complete=True,technical_extraction_complete=not bool(blocking),four_round_review=True,reviewer=summary['reviewer'],passages_read=sum(r['lesson_number']==lesson for r in ledger),new_claims=sum(r['id'].startswith(f'lower-l{lesson:03d}-') for r in data),pending=[r['id'] for r in issues],blocking_extraction_pending=blocking,source_batch_summary=f'{BASE}.summary.json',coverage_ledger=f'{BASE}.coverage.jsonl',base_graph_version=intermediate,logged_at=now.isoformat(),figure_origin_review=dict(later_figures=sum(f['lesson_number']==lesson and f['origin_status']=='later_annotation' for f in figures),unverified_figures=sum(f['lesson_number']==lesson and f['origin_status']=='unverified' for f in figures),source_audit='stage-h-l062-l063-amendment-applied.json')))
 append(LOWER/'coverage.jsonl',logs);append(LOWER/'pending.jsonl',pending);append(LOWER/'figure_reviews.jsonl',figures)
 try:result=import_batches(KB,[batch])
 except Exception:
  for n in ['coverage.jsonl','pending.jsonl','figure_reviews.jsonl']:shutil.copy2(backup/n,LOWER/n)
  raise
 old=ro(backup/'graph.sqlite');new=ro()
 try:
  # Exhaustively compare fixed source tables and every old reviewed row.
  for t in ['documents','pages','passages']:
   assert [tuple(r) for r in old.execute(f'SELECT * FROM {t} ORDER BY id')]==[tuple(r) for r in new.execute(f'SELECT * FROM {t} ORDER BY id')],t
  fops={r['id']:r['after'] for r in plan['figure_operations']}
  for r in old.execute('SELECT * FROM figures'):
   expected=dict(r);expected.update(fops.get(r['id'],{}));assert dict(new.execute('SELECT * FROM figures WHERE id=?',(r['id'],)).fetchone())==expected
  eops={r['evidence_id']:r for r in plan['evidence_figure_amendments']}
  claims={r['id']:dict(r) for r in old.execute("SELECT * FROM claims WHERE review_status='reviewed'")}
  evid=[dict(r) for r in old.execute("SELECT e.* FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed'")]
  for id,r in claims.items():assert dict(new.execute('SELECT * FROM claims WHERE id=?',(id,)).fetchone())==r
  for r in evid:
   expected=dict(r)
   if r['id'] in eops:expected['figure_ids']=j(eops[r['id']]['after_figure_ids'])
   assert dict(new.execute('SELECT * FROM evidence WHERE id=?',(r['id'],)).fetchone())==expected
  counts={t:new.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']}
  reviewed=new.execute("SELECT count(*) FROM claims WHERE review_status='reviewed'").fetchone()[0];assert reviewed==3327
  reviewed_evidence=new.execute("SELECT count(*) FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed'").fetchone()[0];assert reviewed_evidence==4522
 finally:old.close();new.close()
 amendment.update(phase='amendment_and_batch_published',final_graph_version=result['graph_version'],all_source_rows_unchanged=True,all_original_reviewed_claims_unchanged=len(claims),all_original_reviewed_evidence_only_allowed_figure_changes=len(evid),**{'pass':True});write(AUDIT/'stage-h-l062-l063-amendment-applied.json',amendment)
 report=dict(stage='H early pilot completion',base_graph_version=plan['base_graph_version'],graph_version=result['graph_version'],schema_version=summary['schema_version'],backup_directory=str(backup),batch_sha256=hashes,new_claims=len(data),new_evidence=17,reviewed_claims=reviewed,reviewed_evidence=reviewed_evidence,counts=counts,passages_read=33,figure_objects_viewed=6,figure_origin_counts=summary['figure_origin_counts'],original_reviewed_claims_unchanged=len(claims),old_evidence_preserved_except_8_explicit_figure_links=True,all_source_text_geometry_mapping_unchanged=True,pending=summary['pending'],formal_import='passed',semantic_completion=False,delivery_scope='shared_knowledge_base_only',checks_run=['15条Schema和引用/身份/映射/坐标预检','33段逐段台账全覆盖且哈希一致','6图来源记录与8旧证据图关联显式修订，原3312命题/4505引文定位保持','907页9650段逐行不变；528图仅6项来源注记变化'],checks_not_run=['发布后全引用/现有测试/边界与冻结检索及同版本导出待执行','64课223段及附图还需专项补完','全书最终知识库交付审计和归档尚未完成'])
 write(AUDIT/'stage-h-l062-l063-publication.json',report);print(j(report))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');sys.stderr.reconfigure(encoding='utf-8');main()
