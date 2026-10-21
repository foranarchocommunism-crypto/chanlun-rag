"""Finalize lesson61 and apply the human's knowledge-base-only delivery scope."""
import hashlib,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';AUDIT=Path(__file__).resolve().parent
VERSION='0.1.0-review-135f4fcad3e3'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 scope=read(AGENT/'curation/delivery-scope.json');assert scope['active_deliverable']=='shared_knowledge_base_only'
 db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
 try:
  assert json.loads(db.execute("select value from metadata where key='graph_version'").fetchone()[0])==VERSION
  counts={t:db.execute(f'select count(*) from {t}').fetchone()[0] for t in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']}
  assert counts==dict(documents=2,pages=907,units=110,passages=9647,figures=528,concepts=309,claims=5951,evidence=7144,relations=683,reviews=3382)
  statuses=db.execute('select review_status,count(*) from claims group by review_status order by review_status').fetchall();assert dict(statuses)==dict(pending=2612,rejected=27,reviewed=3312)
  unit_status=db.execute('select processing_status,count(*) from units group by processing_status order by processing_status').fetchall();assert dict(unit_status).get('extracted',0)==0 and sum(n for k,n in unit_status if k.startswith('semantic_'))==108
  figure_status=db.execute('select origin_status,count(*) from figures group by origin_status order by origin_status').fetchall()
  assert db.execute("select count(*) from evidence e join claims c on c.id=e.claim_id where c.review_status='reviewed'").fetchone()[0]==4505
  known={r[0] for r in db.execute("select id from claims where review_status='reviewed'")}
 finally:db.close()
 assert read(KB/'manifest.json')['graph_version']==VERSION
 inv=read(AUDIT/'stage-c-l061-source-invariants.json');assert inv['pass'] and inv['graph_version']==VERSION and inv['original_reviewed_claims_unchanged']==3268 and inv['original_reviewed_evidence_unchanged']==4453
 verify=read(AUDIT/'stage-c-l061-verification.json');assert verify['pass'] and verify['graph_version']==VERSION and len(verify['checks'])==6 and len(verify['parity'])==7 and verify['intended_figure_links_checked']==dict(claims=25,associations=26,unique_figures=11)
 dev=read(AGENT/'evaluation/stage-g-development-current.results.json');assert dev['graph_version']==VERSION and dev['executable_development_cases']==240 and all(r['source_identity_matches_expected'] for r in dev['observations'])
 failures=[dict(query_id=r['query_id'],missing=r['missing'],queries=r['queries']) for r in dev['observations'] if not r['automatic_retrieval_contract_pass']]
 assert dev['retrieval_plan_contract_passed']==239 and [f['query_id'] for f in failures]==['g-b05-coincidence']
 exports={}
 for name,count in [('claims',3312),('concepts',309),('relations',683)]:
  p=KB/'exports'/f'{name}.jsonl';rows=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()];assert len(rows)==count and all(r['graph_version']==VERSION for r in rows);exports[name]=dict(rows=count,graph_version=VERSION,sha256=sha(p))
 assert VERSION in (KB/'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150] and read(KB/'exports/coverage.json')['graph_version']==VERSION
 by_lesson={}
 for directory in ['upper','lower']:
  for line in (AGENT/f'curation/{directory}/coverage.jsonl').read_text(encoding='utf-8').splitlines():
   if line.strip():
    item=json.loads(line);by_lesson[item.get('lesson_number',item.get('lesson'))]=item
 assert set(by_lesson)==set(range(1,109)) and all(r.get('whole_lesson_semantic_read_complete',r.get('full_lesson_read_complete',False)) for r in by_lesson.values())
 pending_ids={json.loads(l)['id'] for l in (AGENT/'curation/upper/c_stage_l060.pending.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()}
 changes=[
 ('upper-l060-c-stage-pending-lowest-operable-precision-and-45-46-small-to-large',['one-top-exit-wait-one-bottom-monthly-ignore-smaller-volatility','provisional-divergence-from65-invalid-if-stronger-else-recurse','four-nests65-69-71-inner71-locate72'],'61补原操作级别和四重套比较/否定/内部定位，不证明所有账户无限细分可操作或固定四重必可成交。'),
 ('upper-l060-c-stage-pending-55-first-only-analogy-58-61-vs-from60-center-and46',['around-one-center-strength-compare55-60-vs-from65','five60-69-key69-4244-third-sell-below-expands-atleast30','jun22-46-87-thirty-center4067-4192-third-leg-unfinished'],'61给后续60—65一分枢/60—69五分枢及46—87三十分枢，但不倒改60旧58—61或收评从60起[4224,4254]锚点；已构成/第三段未确认张力继续列待核。'),
 ('upper-l060-c-stage-pending-news-zero-effect-second-sell-level-and-fast-space-exceptions',['72-sell-quantity-five-or-below-all-larger-capacity-hedge','small-funds-higher-return-same-skill-capacity-author-model','oscillation-fund-matched-specific-stock-larger-buy-and-sell'],'61补按级别卖数量及资金容量/个股买点条件，仍无影响0/小概率/100%或任意价零成本的独立成交收益实证，60例外不删除。')]
 followups=[]
 for pid,slugs,finding in changes:
  ids=['upper-l061-c-stage-'+s for s in slugs];assert pid in pending_ids and all(x in known for x in ids)
  followups.append(dict(pending_id=pid,status='new_source_located_scope_still_pending',new_claim_ids=ids,finding=finding,global_pending_not_closed=True,graph_version=VERSION))
 (AGENT/'curation/upper/c_stage_l061.partial-resolutions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in followups),encoding='utf-8')
 checks=['44命题52证据预检；83段全台账、457至470十四页和11整图实际查看','原3268命题4453证据未改；全2文907页9647段528图逐行仅8身份/日期和11图元数据授权变化，原字/几何/映射保持','3312命题全引用0错误，33现有测试通过','6边界组、7现有CLI/共享读取一致与25命题26图文关联11图核对通过，查询哈希不变','冻结240题239计划/240来源身份通过，原重合前20召回仍失败，固定题未改','3312命题309概念683关系及Markdown/coverage同版本导出','上下册台账按旧lesson/full_lesson与新lesson_number/whole_lesson字段归一，108课均有完整阅读记录；3旧待核补来源仍开放、本批7待核']
 not_run=['全书来源/引用/覆盖及最终交付审计未完成；108课阅读记录不等所有技术外围已抽取，早期62至64试点需专项核对其未抽取/未图审项','43/57混合夹注来源拆分和54长编号答完整跨页来源关联尚未完成','61原103未完/要102完、跌段后高低于前低、30分枢第三段完成张力、精度及强收益/执行语继续显式待核','现有冻结召回回归/完整G和自然查询/生成回答评价未完，如实披露；同一代理复核非独立/人类金标准','最终知识库目录/归档和哈希清单未组装；两册未核原博客或历史政策/收益/可成交外部事实，软件已排除']
 evaluation=dict(executable_development_cases=240,target=240,gold_review_status='model_reviewed_development',human_gold_reviewed=False,independent_test_set=False,generated_answers_scored=False,retrieval_plan_passed_on_current_graph=239,source_identity_passed_on_current_graph=240,open_retrieval_regressions=failures,full_stage_g_acceptance_complete=False,new_project_gold_cases_created_in_this_batch=0,note='固定题和gold未改，重合前20仍失败；现有评价不冒知识本体/生成回答质量证明，软件已排除。')
 acceptance='61课44命题52证据发布，3312引用/33测试/6边界/7现有读取一致及25命题26图文关联通过，同版导出；108课均有阅读记录。全书来源/早期试点抽取覆盖/最终交付审计仍待完成。'
 next_anchor='book-delivery-source-and-coverage-audit / mixed annotations lesson043,057 / early pilot062-064';next_action='转全书最终知识库审计：核62至64早期试点剩余技术/图文覆盖，拆分43/57未核夹注且保原字符映射/旧证据，补54跨页编号答的完整问题来源；逐要求核覆盖、引用和同版导出，整理待核及工具限制，再组装知识库目录/哈希。'
 p=AUDIT/'stage-c-l061-publication.json';pub=read(p);assert pub['graph_version']==VERSION and pub['formal_import']=='passed' and list(pub['batch_sha256'].values())==[sha(AGENT/'curation/upper/c_stage_l061.reviewed.jsonl')]
 pub.update(updated_at=datetime.now(timezone.utc).isoformat(),checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_action=next_action,exports=exports,final_sha256=dict(database=sha(KB/'graph.sqlite'),manifest=sha(KB/'manifest.json')),development_evaluation=evaluation,partial_pending_followups=len(followups),semantic_completion=False,writes_to_knowledge_graph_by_this_finalizer=False,complete_reading_records=108,remaining_never_read_lessons=0,delivery_scope=scope['active_deliverable'],delivery_scope_file='curation/delivery-scope.json',excluded_software_deliverables=scope['excluded_software_deliverables']);write(p,pub)
 p=AGENT/'curation/progress.json';progress=read(p);assert progress['graph_version'] in ['0.1.0-review-bb28763cfcd8',VERSION]
 if progress['graph_version']!=VERSION:progress['previous_checkpoint']={k:progress[k] for k in ['graph_version','completed','next_action','evaluation']}
 outputs=['source-audit/stage-c-l061-'+n+'.json' for n in ['source-plan','source-applied','source-invariants','publication','verification']]+['upper/c_stage_l061.partial-resolutions.jsonl'];progress['machine_outputs']=list(dict.fromkeys(progress['machine_outputs']+outputs))
 progress.update(updated_at=datetime.now(timezone.utc).isoformat(),stage='C corpus reading recorded; final knowledge-base source and coverage audit',graph_version=VERSION,counts=counts,claim_status_counts=statuses,figure_origin_counts=figure_status,unit_processing_status_counts=unit_status,semantic_completion=False,complete_reading_records=108,remaining_never_read_lessons=0,delivery_scope=scope['active_deliverable'],delivery_scope_file='curation/delivery-scope.json',excluded_software_deliverables=scope['excluded_software_deliverables'],completed=['61课83段14页11整图同代理四轮，44命题52证据14关系支撑、11新增关系','8来源日期规范：5/22旧答保旧身份并补空格，闭引后六段恢复6/22文章；11图7未核4后加，原3268命题4453证据及全源原字几何映射不动','65起假设/否定/递归、69未新高/70无盘背/71三买后上移必要不盘背、四重套本例定位72均保比较与当下条件','74二三卖对69—72非70—73，结合律至少五次级前三枢四离五点，不成任意五笔或同价触点三类；72卖量限级别和容量，100%/0成本强语非实证','30分枢已构成/第三段未确认、103未完/要102完、跌段后高低于前低原字张力保；4022小数/截整/四舍五入三算法及6/29以后选择分开，不倒改59或后64自选','3312引用/33测试/6边界/7现有读取一致及25命题26关联11图通过，同版导出；冻结240题239计划/240身份通过，原1回归开放','上下册台账归一确认108课均有完整阅读记录；尚需早期试点技术外围覆盖与全书来源/交付审计，不称技术全抽取或所有解释统一'],pending=not_run,checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_resume_anchor=next_anchor,next_action=next_action,coverage_caveat='108课完整阅读记录已经逐课台账归一确认；104课semantic_read_with_pending/4课semantic_extraction_complete并存，不宣称全部技术解释已确认。早期试点剩余技术/图审项须最终审计处理。',evaluation=evaluation,previous_turn_classification='progress：60/61两课70命题83证据发布，3312全引用通过、108课阅读记录；下一步是全书来源/覆盖与最终知识库交付审计。')
 write(p,progress);print(json.dumps(dict(graph_version=VERSION,reviewed=3312,reviewed_evidence=4505,development_cases=240,development_passed=239,complete_reading_records=108,remaining_never_read_lessons=0,next_anchor=next_anchor,delivery_scope=scope['active_deliverable'],semantic_completion=False),ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
