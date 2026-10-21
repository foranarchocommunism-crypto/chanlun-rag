"""Assess the retained knowledge-only requirements on the frozen final graph."""
import hashlib,json,sqlite3,sys,shutil
from collections import Counter
from pathlib import Path
from datetime import datetime,timezone
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';OUT=Path(__file__).resolve().parent;VERSION='0.1.0-review-307029129712'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def lines(p):return [json.loads(l) for l in p.read_text(encoding='utf-8-sig').splitlines() if l.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 scope=read(AGENT/'curation/delivery-scope.json');assert scope['active_deliverable']=='shared_knowledge_base_only'
 checkpoint=read(OUT/'stage-h-l064-checkpoint.json');figproof=read(OUT/'stage-h-final-figure-log-completion.json');pub=read(OUT/'stage-h-l064-publication.json');assert checkpoint['graph_version']==figproof['graph_version']==pub['graph_version']==VERSION and figproof['pass']
 assert checkpoint['complete_reading_records']==108 and not checkpoint['uncovered_lesson_passages'] and not checkpoint['ledger_source_hash_mismatches'] and not checkpoint['unresolved_ledger_claim_references']
 db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
 try:
  assert json.loads(db.execute("SELECT value FROM metadata WHERE key='graph_version'").fetchone()[0])==VERSION==read(KB/'manifest.json')['graph_version']
  assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok' and not db.execute('PRAGMA foreign_key_check').fetchall()
  docs=[dict(r) for r in db.execute('SELECT * FROM documents ORDER BY id')];assert len(docs)==2 and sum(d['page_count'] for d in docs)==907
  for d in docs:assert sha(KB/d['resource_path'])==d['sha256']
  reviewed=[dict(r) for r in db.execute("SELECT * FROM claims WHERE review_status='reviewed'")];assert len(reviewed)==3369
  reviews={r[0] for r in db.execute("SELECT DISTINCT claim_id FROM reviews WHERE result='reviewed'")};assert all(r['id'] in reviews and r['review_note'].strip() for r in reviewed)
  linked=[dict(r) for r in db.execute("SELECT e.id,e.claim_id,p.role,p.speaker,p.unit_id FROM evidence e JOIN claims c ON c.id=e.claim_id JOIN passages p ON p.id=e.passage_id WHERE c.review_status='reviewed'")];assert len(linked)==4584
  assert all(r['speaker']=='缠中说禅' and r['role'] in ['author_body','author_commentary','author_reply'] and r['unit_id'].startswith('lesson-') for r in linked)
  assert {r['claim_id'] for r in linked}=={r['id'] for r in reviewed}
  for r in db.execute('SELECT * FROM relations'):
   assert r['review_status']=='reviewed' and json.loads(r['claim_ids']) and set(json.loads(r['claim_ids']))<={c['id'] for c in reviewed}
  units=[dict(r) for r in db.execute('SELECT * FROM units ORDER BY id')];excluded=[u for u in units if u['kind']!='lesson'];assert len(excluded)==2 and all(u['processing_status']=='excluded_from_author_knowledge' for u in excluded)
  counts={t:db.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in pub['counts']};assert counts==pub['counts']
  status=dict(db.execute('SELECT review_status,count(*) FROM claims GROUP BY review_status').fetchall());origins=dict(db.execute('SELECT origin_status,count(*) FROM figures GROUP BY origin_status').fetchall())
  ambiguity=[{k:r[k] for k in ['id','text','kind','ambiguity_status','review_note']} for r in reviewed if r['ambiguity_status']!='none']
  inference=[{k:r[k] for k in ['id','text','derivation','review_note']} for r in reviewed if r['kind']=='inferred'];assert len(inference)==3 and len(ambiguity)==473
 finally:db.close()
 assert dict(database=sha(KB/'graph.sqlite'),manifest=sha(KB/'manifest.json'))==figproof['final_sha256']
 exports={}
 for name,n in [('claims',3369),('concepts',318),('relations',692)]:
  p=KB/'exports'/f'{name}.jsonl';rs=lines(p);assert len(rs)==n and all(r['graph_version']==VERSION for r in rs);exports[name]=dict(rows=n,sha256=sha(p))
 assert read(KB/'exports/coverage.json')['graph_version']==VERSION and VERSION in (KB/'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150]
 base=read(AGENT/'evaluation/stage-h-final-baselines-307029129712.results.json');assert base['graph_version']==VERSION and base['executable_cases']==base['eligible_rank_cases']==240 and all(not r['gold_identity_mismatches'] for r in base['observations'])
 assert base['snapshot_and_gold_unchanged'] and not base['live_database_written']
 for f in base['snapshot']['source_case_files']:assert sha(AGENT/'evaluation'/f['name'])==f['sha256']
 dev=read(AGENT/'evaluation/stage-g-development-current.results.json');assert dev['graph_version']==VERSION and dev['retrieval_plan_contract_passed']==239 and all(r['source_identity_matches_expected'] for r in dev['observations'])
 source_files=['scripts/evaluate-retrieval-baselines.mjs','scripts/snapshot-retrieval-eval.py','scripts/lib/retrieval-baselines.mjs','src/core.mjs','package.json']
 toolroot=OUT/'final-retrieval-tool-snapshot';assert not toolroot.exists();toolroot.mkdir()
 tools=[]
 for name in source_files:
  target=toolroot/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(AGENT/name,target);tools.append(dict(path=name,sha256=sha(target)))
 assert next(r['sha256'] for r in tools if r['path'].endswith('evaluate-retrieval-baselines.mjs'))==base['implementation_sha256']['runner']
 assert next(r['sha256'] for r in tools if r['path'].endswith('lib/retrieval-baselines.mjs'))==base['implementation_sha256']['algorithms']
 shutil.copy2(AGENT/'build/final-kb-retrieval-307029129712/snapshot.json',OUT/'stage-h-final-retrieval-snapshot.json')
 write(toolroot/'source-hashes.json',dict(graph_version=VERSION,purpose='Existing evaluation-only source snapshot, not a new software product; originals left unchanged.',files=tools))
 (OUT/'stage-h-final-reviewed-ambiguities.jsonl').write_text(''.join(json.dumps(dict(graph_version=VERSION,**r),ensure_ascii=False,separators=(',',':'))+'\n' for r in ambiguity),encoding='utf-8')
 logs={directory:lines(AGENT/f'curation/{directory}/pending.jsonl') for directory in ['upper','lower']}
 pending_ids=[r.get('id') for rs in logs.values() for r in rs if r.get('id')]
 report=dict(stage='H-final-knowledge-base-quality',created_at=datetime.now(timezone.utc).isoformat(),graph_version=VERSION,schema_version='1.1.0',delivery_scope=scope['active_deliverable'],counts=counts,claim_status_counts=status,reviewed_evidence=4584,reviewed_kind_counts=dict(Counter(r['kind'] for r in reviewed)),reviewed_with_explicit_ambiguity=473,figure_origin_counts=origins,source_documents=docs,source_boundary='Only the two fixed compiled PDFs; no verbatim comparison with original blog, no external verification of historical trading/legal/performance assertions.',excluded_units=excluded,
  acceptance=[dict(requirement=scope['required'][0],status='passed_with_explicit_pending',proof='stage-h-l064-checkpoint.json',lessons_read=108,lessons_with_complete_per_passage_ledger=108,lesson_passages=9305,uncovered=0,recorded_source_hashes_checked=9138,legacy_rows_without_historical_text_hash=167),dict(requirement=scope['required'][1],status='passed_with_explicit_ambiguity',proof='Current SQLite integrity/FK and source-role/evidence/review/support audit; full quote validation and 33 tests recorded in stage-h-l064-publication.json.',reviewed_claims=3369,evidence=4584,inferred_separate=3),dict(requirement=scope['required'][2],status='passed_with_unverified_authorship_retained',proof='stage-h-final-figure-log-completion.json',viewing_records=528,reviewed_linked_figures=449),dict(requirement=scope['required'][3],status='passed',exports=exports),dict(requirement=scope['required'][4],status='passed_with_documented_limits',proof=['stage-h-final-reviewed-ambiguities.jsonl','../upper/pending.jsonl','../lower/pending.jsonl','../../evaluation/stage-h-final-baselines-307029129712.results.json']),dict(requirement=scope['required'][5],status='await_delivery_copy_and_archive_verification',proof='To be recorded in the external delivery receipt after actual copy/archive hashing.')],
  pending_inventory=dict(candidate_claims_not_default=status['pending'],rejected=status['rejected'],reviewed_ambiguity=473,pending_log_records=sum(map(len,logs.values())),distinct_historical_pending_ids=len(set(pending_ids)),pending_log_interpretation='Append-only construction history, including partial resolutions; do not equate all old records with current unresolved source defects. Preserve master logs and partial/source-resolution records together.'),
  evaluation=dict(frozen_plan_cases=240,frozen_plans_pass=239,frozen_source_identity_pass=240,known_frozen_failure='g-b05-coincidence: original 重合 top20 misses required lesson21 claim; results truncate at 36.',natural_question_cases=240,query_input='Original query_text only',comparison_unit=base['comparison_unit'],candidate_budget=base['candidate_budget'],baselines=base['baselines'],aggregates=base['aggregates'],query_type_distribution=dict(Counter(r['query_type'] for r in base['observations'])),ten_category_target_distribution_verified=False,ablation_run=False,human_gold_reviewed=False,independent_test_set=False,generated_answers_scored=False,generated_model_token_cost=None,full_stage_g_acceptance_claimed=False),
  known_limits=['Full-sentence native search remains weak; data delivery is not a validated natural-language QA product. Use concepts/keywords and inspect conditions/source evidence.','Vector baseline not implemented; fusion is offline evaluation only, no software feature added.','240 model-reviewed development cases are not an independent/human gold test. Precision is a lower bound against annotated passages; unannotated results are not automatically irrelevant.','No generated-answer faithfulness, human semantic score, conflict detection rate, adversarial score, visual interaction, ablation or generalization claim.','265 figure origins remain unverified and 263 are later annotations; viewing does not establish author identity.','473 reviewed claims retain explicit ambiguity, 2611 candidates remain excluded from default knowledge. Unresolved interpretation is not silently fixed.','9138 historical lesson-row hashes match current text; 167 legacy rows lack historical text hashes but contain per-passage dispositions. No fabricated historical hashes.','Software deliverables and desktop UI/build/package acceptance are excluded by the direct user scope.'],
  all_source_and_knowledge_facts_unchanged=True,final_sha256=figproof['final_sha256'],quality_ready_for_knowledge_delivery=True,actual_delivery_verified=False,semantic_completion_all_explanations_confirmed=False)
 write(OUT/'stage-h-final-kb-quality.json',report);print(json.dumps(dict(graph_version=VERSION,quality_ready_for_knowledge_delivery=True,delivery_copy_archive_still_required=True,reviewed=3369,source_evidence=4584,lessons=108,figures=528,natural_question_recall_at10={k:v['at_k']['10']['recall'] for k,v in base['aggregates'].items()},pending_log_records=report['pending_inventory']['pending_log_records']),ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');sys.stderr.reconfigure(encoding='utf-8');main()
