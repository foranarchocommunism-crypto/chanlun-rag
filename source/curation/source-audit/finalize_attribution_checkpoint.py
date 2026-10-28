"""Record current source repairs, normalized legacy coverage, and open gates."""
import hashlib,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';AUDIT=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def lines(p):return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()]
def jsonl(p,rs):p.write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in rs),encoding='utf-8')
def main():
 scope=read(AGENT/'curation/delivery-scope.json');assert scope['active_deliverable']=='shared_knowledge_base_only'
 applied=read(AUDIT/'stage-h-annotation-split-applied.json');verified=read(AUDIT/'stage-h-annotation-split-verification.json');amended=read(AUDIT/'stage-h-l054-context-notes-amended.json');plan=read(AUDIT/'stage-h-annotation-split-plan.json')
 assert applied['pass'] and verified['pass'] and amended['pass'] and amended['base_graph_version']==applied['graph_version']==verified['graph_version']
 c=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
 try:
  version=json.loads(c.execute("select value from metadata where key='graph_version'").fetchone()[0]);assert version==amended['graph_version']==read(KB/'manifest.json')['graph_version']
  passages={r['id']:dict(r) for r in c.execute('select * from passages')};units={r['id']:dict(r) for r in c.execute('select * from units')};counts={t:c.execute('select count(*) from '+t).fetchone()[0] for t in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']}
  statuses=[list(r) for r in c.execute('select review_status,count(*) from claims group by review_status')];assert dict(statuses)==dict(pending=2611,rejected=28,reviewed=3312)
  assert counts==dict(documents=2,pages=907,units=110,passages=9650,figures=528,concepts=309,claims=5951,evidence=7146,relations=683,reviews=3388)
  assert c.execute("select count(*) from evidence e join claims c on c.id=e.claim_id where c.review_status='reviewed'").fetchone()[0]==4505
  source_overlay=[]
  for item in plan['items']:
   for s in item['parts']:
    p=passages[s['after']['id']];assert p==s['after']
    ids=[r[0] for r in c.execute("select distinct e.claim_id from evidence e join claims c on c.id=e.claim_id where e.passage_id=? and c.review_status='reviewed'",(p['id'],))]
    source_overlay.append(dict(passage_id=p['id'],unit_id=p['unit_id'],lesson_number=int(p['unit_id'].split('-')[1]),document_id=p['document_id'],pdf_page=p['pdf_page'],role=p['role'],speaker=p['speaker'],published_at=p['published_at'],source_text_sha256=hashlib.sha256(p['text'].encode()).hexdigest(),result='unknown_annotation_retained_excluded_from_author_evidence' if p['role']=='unknown' else 'existing_author_claim_evidence_preserved',claim_ids=ids,source_segmentation_lineage='provenance/source-segmentation-001.json',original_parent_passage_id=item['before']['id'],original_normalized_range=[s['original_begin'],s['original_end']],reviewer='Codex 主代理 / 混合夹注来源专项核对',graph_version=version))
  unit_status=[list(r) for r in c.execute('select processing_status,count(*) from units group by processing_status')];figure_status=[list(r) for r in c.execute('select origin_status,count(*) from figures group by origin_status')]
 finally:c.close()
 jsonl(AUDIT/'stage-h-annotation-split.coverage.jsonl',source_overlay)
 overlay={r['passage_id']:r for r in source_overlay};registry={}
 for d in ['upper','lower']:
  for r in lines(AGENT/f'curation/{d}/coverage.jsonl'):registry[r.get('lesson_number',r.get('lesson'))]=(d,r)
 assert set(registry)==set(range(1,109)) and all(r.get('whole_lesson_semantic_read_complete',r.get('full_lesson_read_complete',False)) for d,r in registry.values())
 normalized=[];missing=[];mismatched_hashes=[];cache={}
 for n,(d,r) in sorted(registry.items()):
  actual={id for id,p in passages.items() if p['unit_id']==f'lesson-{n:03d}'}
  name=r.get('coverage_ledger');batch=r.get('batch','');stem=batch.removesuffix('.reviewed.jsonl').removesuffix('.jsonl');candidates=([AGENT/f'curation/{d}'/name] if name else [])+[AGENT/f'curation/{d}'/(stem+'.coverage.jsonl')]
  path=next((f for f in candidates if f.is_file()),None)
  ledger={}
  if path:
   if str(path) not in cache:cache[str(path)]=lines(path)
   ledger={x['passage_id']:x for x in cache[str(path)] if x.get('passage_id') in actual}
  ledger.update({id:x for id,x in overlay.items() if id in actual});uncovered=sorted(actual-set(ledger))
  for id,x in ledger.items():
   oldhash=x.get('source_text_sha256',x.get('text_sha256'))
   if oldhash and oldhash!=hashlib.sha256(passages[id]['text'].encode()).hexdigest():mismatched_hashes.append(dict(passage_id=id,ledger=str(path),recorded=oldhash,current=hashlib.sha256(passages[id]['text'].encode()).hexdigest()))
  record=dict(lesson_number=n,whole_lesson_read_recorded=True,technical_extraction_complete_as_recorded=r.get('technical_extraction_complete',False),source_passages=len(actual),per_passage_ledger_rows=len(ledger),ledger_path=str(path.relative_to(AGENT)) if path else None,overlay_path='curation/source-audit/stage-h-annotation-split.coverage.jsonl' if any(id in overlay for id in actual) else None,uncovered_passage_ids=uncovered,legacy_coverage_fields_preserved=True)
  normalized.append(record)
  if uncovered:missing.append(record)
 dev=read(AGENT/'evaluation/stage-g-development-current.results.json');assert dev['graph_version']==version and dev['executable_development_cases']==240 and dev['retrieval_plan_contract_passed']==239 and all(r['source_identity_matches_expected'] for r in dev['observations'])
 exports={}
 for name,count in [('claims',3312),('concepts',309),('relations',683)]:
  f=KB/'exports'/f'{name}.jsonl';rs=lines(f);assert len(rs)==count and all(r['graph_version']==version for r in rs);exports[name]=dict(rows=count,graph_version=version,sha256=sha(f))
 assert read(KB/'exports/coverage.json')['graph_version']==version and version in (KB/'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150]
 known_limits=[dict(query_id=r['query_id'],missing=r['missing'],queries=r['queries']) for r in dev['observations'] if not r['automatic_retrieval_contract_pass']]
 audit=dict(stage='H-knowledge-base-delivery-interim-audit',graph_version=version,schema_version='1.1.0',delivery_scope=scope['active_deliverable'],counts=counts,claim_status_counts=statuses,complete_reading_records=108,unit_coverage=normalized,lessons_without_complete_per_passage_ledger=[r['lesson_number'] for r in missing],uncovered_lesson_passages=sum(len(r['uncovered_passage_ids']) for r in missing),ledger_source_hash_mismatches=mismatched_hashes,known_resolved=[dict(priority='P0',issue='43/57匿名夹注整体冒作者来源',status='resolved_source_identity_isolation',proof=['stage-h-annotation-split-applied.json','stage-h-annotation-split-verification.json','../shared-knowledge/v0.1.0/provenance/source-segmentation-001.json']),dict(priority='P2',issue='54短答上下文旧缺口描述',status='current_interface_has_complete_questions_review_notes_corrected',proof=['stage-h-annotation-split-verification.json','stage-h-l054-context-notes-amended.json'])],open_delivery_requirements=[dict(priority='P1',issue='早期62至64试点的逐段覆盖/技术外围与图文待补项',lessons=[r['lesson_number'] for r in missing],acceptance='逐段核原文/既有reviewed及配图，补有价值遗漏或明确保留/待核/排除依据，生成当前源ID可对照台账'),dict(priority='P1',issue='全书最终来源、图文及条件质量审计尚未完结',acceptance='核完实际剩余项，区分来源错误与显式未决解释；不要求伪造原博客/人类金标准'),dict(priority='P1',issue='最终知识库交付目录/归档和校验清单未生成',acceptance='固定版本SQLite/原文/geometry/provenance/导出/覆盖待核及构建记录，逐文件哈希并核复制件')],development_evaluation=dict(cases=240,retrieval_plan_pass=239,source_identity_pass=240,human_gold_reviewed=False,independent_test_set=False,generated_answers_scored=False,known_retrieval_failures=known_limits),exports=exports,software_requirements_excluded=scope['excluded_software_deliverables'],completion_proven=False,next_action='优先重新核对62至64早期试点逐段覆盖与既有技术/图文待补项；保旧已复核命题并补真实遗漏。')
 write(AUDIT/'stage-h-kb-delivery-interim-audit.json',audit)
 resolution=[dict(scope='source_attribution_only',source_parent_passage_ids=applied['split_parent_ids'],status='source_identity_isolation_complete',annotation_authorship='unknown_retained',reviewed_author_quotes_and_coordinates_preserved=True,lineage_file=applied['lineage_file'],graph_version=version),dict(scope='lesson054_short_answer_context',status='current_context_complete_stale_review_notes_corrected',query_code_changed=False,proof='stage-h-l054-context-notes-amended.json',graph_version=version)]
 jsonl(AUDIT/'stage-h-source-resolutions.jsonl',resolution)
 p=AGENT/'curation/progress.json';progress=read(p)
 if progress['graph_version']!=version:progress['previous_checkpoint']={k:progress[k] for k in ['graph_version','completed','next_action','evaluation']}
 checks=['3312命题全引用检查0错误、33现有Node测试通过','两夹注源检索现返回unknown/null身份；作者尾句引文和坐标未改，仅一证据段ID/偏移迁移，原完整行/映射/依赖保provenance，1混合候选拒绝','54三短答接口包含全部所需跨页问题，2过时review_note已纠正，未改查询代码','108阅读记录逐课归一；新旧逐段ledger字段按实际passage所属单元匹配，分拆5片段overlay保全源字符映射','当前版本3312命题309概念683关系及Markdown/coverage导出一致；240冻结开发题239计划/240身份通过，原1召回回归开放']
 pending=['62至64早期试点逐段台账/技术外围和配图待补项需专项处理，不以已读或已有少量命题代替完成','全书来源/图文/条件和关系最终质量审计、待核汇总及知识库目录/归档哈希交付未完成','现有检索原前20召回回归及完整G评价边界如实保留；同一代理复核非独立/人类金标准，未核原博客','原文强语、公式/编号等解释分歧仍显式待核，软件交付已排除']
 outputs=['source-audit/'+n for n in ['stage-h-annotation-split-plan.json','stage-h-annotation-split-applied.json','stage-h-annotation-split-verification.json','stage-h-annotation-split.coverage.jsonl','stage-h-l054-context-notes-amended.json','stage-h-source-resolutions.jsonl','stage-h-kb-delivery-interim-audit.json']];progress['machine_outputs']=list(dict.fromkeys(progress['machine_outputs']+outputs))
 progress.update(updated_at=datetime.now(timezone.utc).isoformat(),stage='H final knowledge-base source and coverage audit in progress',graph_version=version,counts=counts,claim_status_counts=statuses,unit_processing_status_counts=unit_status,figure_origin_counts=figure_status,semantic_completion=False,complete_reading_records=108,remaining_never_read_lessons=0,completed=['60/61两课70命题83证据发布，全108课已有完整阅读记录','43/57混合夹注已正式分段为作者片段与unknown注释，原字符映射拼接一致；3312作者命题未变，4505已复核引文/源坐标未变，1尾句证据迁移，1混合候选拒绝','54当前接口完整包含编号问题，2过时工具限制备注修正，无查询/软件改动','逐课覆盖台账新旧字段和后分段覆盖归一，明确早期试点缺口而不冒全书技术全抽取','3312全引用/33测试通过，同版导出；冻结240开发题239计划/240身份通过，原1召回回归开放'],checks_run=checks,checks_not_run=pending,pending=pending,acceptance='来源归属修复与当前引用/测试/导出通过；108课阅读完成，早期试点技术/逐段图文覆盖及最终知识库交付仍未完成。',next_resume_anchor='volume_2-5332cd1b6038 / lessons062-064 / PDF6-32',next_action=audit['next_action'],coverage_caveat='阅读记录完整已逐课核实；缺少逐段台账不自动等于未读，现有早期63/64又明确登记技术/图文待补，必须专项核查。',evaluation=audit['development_evaluation'],delivery_scope=scope['active_deliverable'],previous_turn_classification='progress：60/61发布及两处P0夹注来源隔离、54旧备注纠正和当前覆盖审计完成；已识别下一处可行动的早期试点缺口。')
 write(p,progress);print(json.dumps(dict(graph_version=version,reviewed=3312,reviewed_evidence=4505,complete_reading_records=108,ledger_missing_lessons=audit['lessons_without_complete_per_passage_ledger'],uncovered_lesson_passages=audit['uncovered_lesson_passages'],ledger_hash_mismatches=len(mismatched_hashes),source_identity_repairs=2,context_notes_corrected=2,completion_proven=False),ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
