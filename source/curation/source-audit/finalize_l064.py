"""Reconcile all 108 lesson ledgers and save the current knowledge-only checkpoint."""
import hashlib,json,sqlite3,sys
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';AUDIT=Path(__file__).resolve().parent;VERSION='0.1.0-review-307029129712'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def lines(p):return [json.loads(l) for l in p.read_text(encoding='utf-8-sig').splitlines() if l.strip()]
def main():
 pub=read(AUDIT/'stage-h-l064-publication.json');verify=read(AUDIT/'stage-h-l064-verification.json');prior=read(AUDIT/'stage-h-l062-l063-checkpoint.json')
 assert pub['graph_version']==verify['graph_version']==VERSION and verify['pass'] and len(verify['checks'])==5
 assert list(pub['batch_sha256'].values())==[sha(AGENT/'curation/lower/c_stage_l064.reviewed.jsonl')]
 db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
 try:
  assert json.loads(db.execute("SELECT value FROM metadata WHERE key='graph_version'").fetchone()[0])==VERSION
  counts={t:db.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in pub['counts']};assert counts==pub['counts']
  statuses=[list(r) for r in db.execute('SELECT review_status,count(*) FROM claims GROUP BY review_status ORDER BY review_status')]
  figures=[list(r) for r in db.execute('SELECT origin_status,count(*) FROM figures GROUP BY origin_status ORDER BY origin_status')]
  units=[list(r) for r in db.execute('SELECT processing_status,count(*) FROM units GROUP BY processing_status ORDER BY processing_status')]
  passages={r['id']:dict(r) for r in db.execute('SELECT * FROM passages')};known={r[0] for r in db.execute('SELECT id FROM claims')}
 finally:db.close()
 assert read(KB/'manifest.json')['graph_version']==VERSION
 registry={}
 for d in ['upper','lower']:
  for r in lines(AGENT/f'curation/{d}/coverage.jsonl'):registry[r.get('lesson_number',r.get('lesson'))]=(d,r)
 assert set(registry)==set(range(1,109)) and all(r.get('whole_lesson_semantic_read_complete',r.get('full_lesson_read_complete',False)) for d,r in registry.values())
 overlay={r['passage_id']:r for r in lines(AUDIT/'stage-h-annotation-split.coverage.jsonl')}
 normalized=[];missing=[];mismatches=[];cache={};hash_checked=0;legacy_without_hash=0;invalid_refs=[];dispositions=Counter()
 for n,(d,r) in sorted(registry.items()):
  actual={id for id,p in passages.items() if p['unit_id']==f'lesson-{n:03d}'};name=r.get('coverage_ledger');batch=r.get('batch','');stem=batch.removesuffix('.reviewed.jsonl').removesuffix('.jsonl')
  candidates=([AGENT/f'curation/{d}'/name] if name else [])+[AGENT/f'curation/{d}'/(stem+'.coverage.jsonl')];path=next((p for p in candidates if p.is_file()),None);assert path,(n,candidates)
  if str(path) not in cache:cache[str(path)]=lines(path)
  ledger={x['passage_id']:x for x in cache[str(path)] if x.get('passage_id') in actual};ledger.update({id:x for id,x in overlay.items() if id in actual});uncovered=sorted(actual-set(ledger))
  for id,x in ledger.items():
   oldhash=x.get('source_text_sha256',x.get('text_sha256'))
   if oldhash:
    hash_checked+=1
    if oldhash!=hashlib.sha256(passages[id]['text'].encode()).hexdigest():mismatches.append(dict(passage_id=id,ledger=str(path),recorded=oldhash))
   else:legacy_without_hash+=1
   outcome=x.get('result',x.get('disposition',x.get('categories')));assert outcome,(id,x);dispositions[str(outcome)]+=1
   for field in ['claim_ids','new_claim_ids','existing_claim_ids','related_existing_claim_ids']:
    for cid in x.get(field,[]):
     if cid not in known:invalid_refs.append(dict(passage_id=id,field=field,claim_id=cid,ledger=str(path.relative_to(AGENT))))
  normalized.append(dict(lesson_number=n,whole_lesson_read_recorded=True,technical_extraction_complete_as_recorded=r.get('technical_extraction_complete',False),source_passages=len(actual),per_passage_ledger_rows=len(ledger),ledger_path=str(path.relative_to(AGENT)),ledger_sha256=sha(path),overlay_path='curation/source-audit/stage-h-annotation-split.coverage.jsonl' if any(id in overlay for id in actual) else None,uncovered_passage_ids=uncovered,legacy_coverage_fields_preserved=True))
  if uncovered:missing.append(n)
 assert not missing and not mismatches,(missing,mismatches)
 dev=read(AGENT/'evaluation/stage-g-development-current.results.json');assert dev['graph_version']==VERSION and dev['executable_development_cases']==240 and dev['retrieval_plan_contract_passed']==239 and all(r['source_identity_matches_expected'] for r in dev['observations'])
 failed=[{k:r[k] for k in ['query_id','missing','queries']} for r in dev['observations'] if not r['automatic_retrieval_contract_pass']];assert [r['query_id'] for r in failed]==['g-b05-coincidence']
 exports={}
 for name,n in [('claims',3369),('concepts',318),('relations',692)]:
  p=KB/'exports'/f'{name}.jsonl';rows=lines(p);assert len(rows)==n and all(r['graph_version']==VERSION for r in rows);exports[name]=dict(rows=n,graph_version=VERSION,sha256=sha(p))
 assert VERSION in (KB/'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150] and read(KB/'exports/coverage.json')['graph_version']==VERSION
 newids={r['id'] for r in lines(AGENT/'curation/lower/c_stage_l064.reviewed.jsonl')}
 followup=dict(pending_id='lower-l063-c-stage-pending-110-111-pen-fractal-and-center-homework-not-fully-given',status='new_source_located_scope_still_pending',new_claim_ids=['lower-l064-c-stage-'+s for s in ['106-107-arrow-stroke-under-preset-rounding','108-109-not-three-segments-same-direction-gap-contained','110-111-compare104-105-around105-110-center','green-rebound-analogue-third-sell-micro-center-two-branches','running-up-down-up-second-micro-center-final-green-area-comparison']],finding='64补精度/108至109、110至111实际104至105比较与105至110枢及微型结构最终面积比较；逐K分型构成、逆向缺口统一标准和真实执行仍无全答案，不自动关闭待核。',global_pending_not_closed=True,graph_version=VERSION)
 assert set(followup['new_claim_ids'])<=newids
 (AGENT/'curation/lower/c_stage_l064.partial-resolutions.jsonl').write_text(json.dumps(followup,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
 checks=pub['checks_run']+['3369命题全引用检查0错误；33项现有测试通过','5组知识边界、3个现有读取一致、15处图文关联5图与223段当前哈希通过','108课逐段台账重新按当前源ID/旧新字段/夹注overlay核对，无未覆盖段、无已记录原文哈希错位','冻结240开发题239检索计划/240来源身份，原重合前20截断问题开放','3369命题318概念692关系及Markdown/coverage同版导出']
 pending=['全书最终来源/图文/条件与关系质量审计、待核汇总尚未完结','最终知识库目录、归档/逐文件哈希和实际复制件核验尚未完成','原文字义/早期缺口说法、位图原发、微型结构特例及历史执行收益/估值强语继续显式待核','固定开发检索原重合前20召回仍未通过；非独立/人类金标准且未评分生成回答']
 if invalid_refs:pending.insert(0,f'全书台账有{len(invalid_refs)}条历史命题ID引用不在现库，须核是否已更名/仅旧候选并补追溯记录')
 audit=dict(stage='H-all-108-lesson-ledgers-reconciled',graph_version=VERSION,schema_version='1.1.0',delivery_scope='shared_knowledge_base_only',counts=counts,claim_status_counts=statuses,complete_reading_records=108,unit_coverage=normalized,lessons_without_complete_per_passage_ledger=[],uncovered_lesson_passages=0,ledger_source_hash_mismatches=[],source_hashes_checked=hash_checked,legacy_ledger_rows_without_text_hash=legacy_without_hash,legacy_hash_limit='无历史源哈希行仍有逐段处置/原页与四轮记录，本次仅核当前源ID/处置；不冒称原历史哈希已存在。',ledger_disposition_counts=dict(dispositions),unresolved_ledger_claim_references=invalid_refs,known_resolved=prior['known_resolved']+[dict(priority='P1',issue='64早期试点逐段/技术外围与图文待补',status='223_paragraphs_42_claims_62_quotes_5_figures_with_explicit_pending',proof=['stage-h-l064-publication.json','stage-h-l064-verification.json'])],open_delivery_requirements=[dict(priority='P1',issue=p) for p in pending[:2]],development_evaluation=dict(cases=240,retrieval_plan_pass=239,source_identity_pass=240,human_gold_reviewed=False,independent_test_set=False,generated_answers_scored=False,known_retrieval_failures=failed),exports=exports,software_requirements_excluded=prior['software_requirements_excluded'],completion_proven=False,next_action='转最终知识库质量/待核和来源条件关系审计；处理实际缺陷或明确来源边界，再组装固定版本知识库目录、归档与校验清单。')
 write(AUDIT/'stage-h-l064-checkpoint.json',audit)
 pub.update(checks_run=checks,checks_not_run=pending,exports=exports,final_sha256=dict(database=sha(KB/'graph.sqlite'),manifest=sha(KB/'manifest.json')),development_evaluation=audit['development_evaluation'],next_action=audit['next_action'],acceptance='64课223段42命题62引文5图完成补录；108课逐段台账闭合，同版导出；最终知识库质量/交付审计未完成。',updated_at=datetime.now(timezone.utc).isoformat());write(AUDIT/'stage-h-l064-publication.json',pub)
 p=AGENT/'curation/progress.json';progress=read(p);assert progress['graph_version']=='0.1.0-review-2ac69fd77eec';progress['previous_checkpoint']={k:progress[k] for k in ['graph_version','completed','next_action','evaluation']}
 progress.update(updated_at=datetime.now(timezone.utc).isoformat(),stage='H all108 lesson ledgers complete; final knowledge-base quality and delivery audit remaining',graph_version=VERSION,counts=counts,claim_status_counts=statuses,figure_origin_counts=figures,unit_processing_status_counts=units,semantic_completion=False,completed=checks,pending=pending,checks_run=checks,checks_not_run=pending,acceptance=pub['acceptance'],next_resume_anchor='book-final-quality-and-delivery / version307029129712 / all108 ledgers',next_action=audit['next_action'],coverage_caveat='108课完整阅读及逐段处置台账均已核对闭合；真实解释分歧/原始位图未核/执行绩效等仍显式待核，不能将逐段处理齐全写成全部知识已确认。',evaluation=audit['development_evaluation'],previous_turn_classification='progress：62至64三课256段57新命题79引文11整图完成，3369引用0错误、33测试、同版导出；全108课逐段台账闭合，下一步最终质量审计和知识库归档。')
 progress['machine_outputs']=list(dict.fromkeys(progress['machine_outputs']+['source-audit/stage-h-l064-'+s+'.json' for s in ['amendment-plan','amendment-applied','publication','verification','checkpoint']]+['lower/c_stage_l064.partial-resolutions.jsonl']))
 write(p,progress);print(json.dumps(dict(graph_version=VERSION,reviewed_claims=3369,reviewed_evidence=4584,complete_lesson_ledgers=108,uncovered_lesson_passages=0,hashes_checked=hash_checked,legacy_rows_without_hash=legacy_without_hash,invalid_ledger_claim_refs=len(invalid_refs),semantic_completion=False),ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');sys.stderr.reconfigure(encoding='utf-8');main()
