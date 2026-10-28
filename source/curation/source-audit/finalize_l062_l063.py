"""Save the current KB checkpoint; this does not write the knowledge graph."""
import hashlib,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';AUDIT=Path(__file__).resolve().parent
VERSION='0.1.0-review-2ac69fd77eec'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 pub=read(AUDIT/'stage-h-l062-l063-publication.json');verify=read(AUDIT/'stage-h-l062-l063-verification.json')
 assert pub['graph_version']==verify['graph_version']==VERSION and verify['pass']
 assert list(pub['batch_sha256'].values())==[sha(AGENT/'curation/lower/c_stage_l062_l063.reviewed.jsonl')]
 db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
 try:
  assert json.loads(db.execute("SELECT value FROM metadata WHERE key='graph_version'").fetchone()[0])==VERSION
  counts={t:db.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in pub['counts']};assert counts==pub['counts']
  statuses=db.execute('SELECT review_status,count(*) FROM claims GROUP BY review_status ORDER BY review_status').fetchall()
  figures=db.execute('SELECT origin_status,count(*) FROM figures GROUP BY origin_status ORDER BY origin_status').fetchall()
  units=db.execute('SELECT processing_status,count(*) FROM units GROUP BY processing_status ORDER BY processing_status').fetchall()
 finally:db.close()
 assert read(KB/'manifest.json')['graph_version']==VERSION
 dev=read(AGENT/'evaluation/stage-g-development-current.results.json');assert dev['graph_version']==VERSION and dev['executable_development_cases']==240 and dev['retrieval_plan_contract_passed']==239
 assert all(x['source_identity_matches_expected'] for x in dev['observations'])
 failed=[{k:r[k] for k in ['query_id','missing','queries']} for r in dev['observations'] if not r['automatic_retrieval_contract_pass']];assert [r['query_id'] for r in failed]==['g-b05-coincidence']
 exports={}
 for name,n in [('claims',3327),('concepts',309),('relations',687)]:
  p=KB/'exports'/f'{name}.jsonl';rows=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()];assert len(rows)==n and all(r['graph_version']==VERSION for r in rows);exports[name]=dict(rows=n,graph_version=VERSION,sha256=sha(p))
 assert VERSION in (KB/'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150] and read(KB/'exports/coverage.json')['graph_version']==VERSION
 ledger=[json.loads(l) for l in (AGENT/'curation/lower/c_stage_l062_l063.coverage.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
 audit=read(AUDIT/'stage-h-kb-delivery-interim-audit.json');assert audit['graph_version']=='0.1.0-review-a837c6e53243'
 for u in audit['unit_coverage']:
  if u['lesson_number'] in [62,63]:
   selected=[r for r in ledger if r['lesson_number']==u['lesson_number']];assert len(selected)==u['source_passages']
   u.update(per_passage_ledger_rows=len(selected),ledger_path='curation/lower/c_stage_l062_l063.coverage.jsonl',uncovered_passage_ids=[],technical_extraction_complete_as_recorded=u['lesson_number']==62)
 checks=pub['checks_run']+['3327命题全引用检查0错误；33项现有测试通过','5组知识边界、3个现有CLI/共享读取一致，6处新图文关联及8处旧图关联核对通过','冻结240开发题239计划/240来源身份，原重合前20截断问题开放','3327命题309概念687关系及Markdown/coverage同版导出']
 pending=['64课223段仍缺逐段台账，正文110/111图例和附带答疑/操作纪律须核','全书最终来源/图文/条件质量审计及最终知识库目录、归档/哈希未完成','63具体分型/笔/递归中枢练习原文未给完整答案，需64后文联读；来源未核与强收益/历史执行边界保留','固定开发检索原重合前20召回仍未通过；非独立/人类金标准且未评分生成回答']
 audit.update(stage='H-knowledge-base-delivery-after-early-pilot-62-63',graph_version=VERSION,counts=counts,claim_status_counts=statuses,lessons_without_complete_per_passage_ledger=[64],uncovered_lesson_passages=223,exports=exports,completion_proven=False,checkpoint_proof='stage-h-l062-l063-publication.json',source_hash_audit_note='本批全9650段逐行保持；前一全书台账0原文哈希错位结论继续有效，新增33段已逐项重核。',next_action='继续64课223段PDF12至32正文、图例、答疑与附带操作纪律逐段核对。')
 audit['open_delivery_requirements'][0].update(issue='早期64课逐段覆盖/技术外围与图文待补项',lessons=[64])
 audit['known_resolved'].append(dict(priority='P1',issue='62/63早期试点逐段台账和有价值遗漏',status='33_paragraphs_15_claims_17_quotes_6_figures_completed_with_explicit_pending',proof=['stage-h-l062-l063-publication.json','stage-h-l062-l063-verification.json']))
 audit['development_evaluation'].update(known_retrieval_failures=failed)
 write(AUDIT/'stage-h-l062-l063-checkpoint.json',audit)
 pub.update(checks_run=checks,checks_not_run=pending,exports=exports,final_sha256=dict(database=sha(KB/'graph.sqlite'),manifest=sha(KB/'manifest.json')),development_evaluation=audit['development_evaluation'],next_action=audit['next_action'],acceptance='62/63课33段15命题17引文6图完成补录，同版导出；64课及全书最终交付审计仍未完成。',updated_at=datetime.now(timezone.utc).isoformat());write(AUDIT/'stage-h-l062-l063-publication.json',pub)
 p=AGENT/'curation/progress.json';progress=read(p);assert progress['graph_version']=='0.1.0-review-a837c6e53243'
 progress['previous_checkpoint']={k:progress[k] for k in ['graph_version','completed','next_action','evaluation']}
 progress.update(updated_at=datetime.now(timezone.utc).isoformat(),stage='H final knowledge-base audit; early pilot64 remaining',graph_version=VERSION,counts=counts,claim_status_counts=statuses,figure_origin_counts=figures,unit_processing_status_counts=units,semantic_completion=False,completed=checks,pending=pending,checks_run=checks,checks_not_run=pending,acceptance=pub['acceptance'],next_resume_anchor='early-pilot-lesson064 / volume2 PDF12-32 / 223 paragraphs',next_action=audit['next_action'],coverage_caveat='108课有完整阅读记录；107课逐段台账完整（前一全书审计105课+本批62/63），仅64课223段待补。逐段处理完整不等全部知识解释已确认。',evaluation=audit['development_evaluation'],previous_turn_classification='progress：62/63课33段、15新命题17引文、6图及8旧图关联补录，3327引用0错误和33现有测试、同版导出；下一步64课。')
 progress['machine_outputs']=list(dict.fromkeys(progress['machine_outputs']+['source-audit/stage-h-l062-l063-'+s+'.json' for s in ['amendment-plan','amendment-applied','publication','verification','checkpoint']]))
 write(p,progress);print(json.dumps(dict(graph_version=VERSION,reviewed_claims=3327,reviewed_evidence=4522,covered_lesson_ledgers=107,remaining_lesson=64,remaining_paragraphs=223,semantic_completion=False),ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');sys.stderr.reconfigure(encoding='utf-8');main()
