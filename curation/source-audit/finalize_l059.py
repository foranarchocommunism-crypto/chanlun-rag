"""Finalize lesson59 and apply the human's knowledge-base-only delivery scope."""
import hashlib,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';AUDIT=Path(__file__).resolve().parent
VERSION='0.1.0-review-dd5aebdeacd1'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 scope=read(AGENT/'curation/delivery-scope.json');assert scope['active_deliverable']=='shared_knowledge_base_only'
 db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
 try:
  assert json.loads(db.execute("select value from metadata where key='graph_version'").fetchone()[0])==VERSION
  counts={t:db.execute(f'select count(*) from {t}').fetchone()[0] for t in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']}
  assert counts==dict(documents=2,pages=907,units=110,passages=9647,figures=528,concepts=308,claims=5881,evidence=7061,relations=661,reviews=3312)
  statuses=db.execute('select review_status,count(*) from claims group by review_status order by review_status').fetchall();assert dict(statuses)==dict(pending=2612,rejected=27,reviewed=3242)
  unit_status=db.execute('select processing_status,count(*) from units group by processing_status order by processing_status').fetchall();assert dict(unit_status)['extracted']==2
  figure_status=db.execute('select origin_status,count(*) from figures group by origin_status order by origin_status').fetchall()
  assert db.execute("select count(*) from evidence e join claims c on c.id=e.claim_id where c.review_status='reviewed'").fetchone()[0]==4422
  next_row=db.execute("select id,pdf_page,text from passages where unit_id='lesson-060' order by pdf_page,block_index,id limit 1").fetchone();assert next_row[0]=='volume_1-a53e99c37ca5-p0451-b000'
  known={r[0] for r in db.execute("select id from claims where review_status='reviewed'")}
 finally:db.close()
 assert read(KB/'manifest.json')['graph_version']==VERSION
 inv=read(AUDIT/'stage-c-l059-source-invariants.json');assert inv['pass'] and inv['graph_version']==VERSION and inv['original_reviewed_claims_unchanged']==3214 and inv['original_reviewed_evidence_unchanged']==4390
 verify=read(AUDIT/'stage-c-l059-verification.json');assert verify['pass'] and verify['graph_version']==VERSION and len(verify['checks'])==6 and len(verify['parity'])==7 and verify['intended_figure_links_checked']==dict(claims=14,associations=14,unique_figures=7)
 dev=read(AGENT/'evaluation/stage-g-development-current.results.json');assert dev['graph_version']==VERSION and dev['executable_development_cases']==240 and all(r['source_identity_matches_expected'] for r in dev['observations'])
 failures=[dict(query_id=r['query_id'],missing=r['missing'],queries=r['queries']) for r in dev['observations'] if not r['automatic_retrieval_contract_pass']]
 assert dev['retrieval_plan_contract_passed']==239 and [f['query_id'] for f in failures]==['g-b05-coincidence']
 exports={}
 for name,count in [('claims',3242),('concepts',308),('relations',661)]:
  p=KB/'exports'/f'{name}.jsonl';rows=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()];assert len(rows)==count and all(r['graph_version']==VERSION for r in rows);exports[name]=dict(rows=count,graph_version=VERSION,sha256=sha(p))
 assert VERSION in (KB/'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150] and read(KB/'exports/coverage.json')['graph_version']==VERSION
 pending_ids={json.loads(l)['id'] for l in (AGENT/'curation/upper/c_stage_l058.pending.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()}
 changes=[
 ('upper-l058-c-stage-pending-early-segment-gap-exception-vs-later-precise-definition',['segment-shape-not-amplitude-nonoverlap-up-can-extend','adjacent-segments-alternate-direction-not-two-same-direction','atleast-three-fold-no-flat-one-price-limit-below-segment','early-segment-end-trend-divergence-else-consolidation-shock-second'],'59补形态非幅度、相邻异向、三折/一字涨停及一般背驰确认；仍属早期图解，不自动代后64/67特征序列，58缺口例外保留。'),
 ('upper-l058-c-stage-pending-macro-center-forming-not-finished-and-conditional-rotation',['1-19-five-type-only-consolidation-no-two-five-centers','19-45-atleast-five-center41-below32-but-type-unfinished','alternate22-31-five-center29-below24-unfinished-invariant','alternate41-third-buy-if-new-five-nonoverlap-then-uptrend'],'59确认1—19只一个5分盘整，新19—45未完及另22—31枢；41三买后新5分枢最终不重叠才上涨趋势，旧图17/新19局部编号未自动合并。'),
 ('upper-l058-c-stage-pending-chart-vs-move-level-precision-and-fees-skill',['3994-precision-one-or-three-segments-preselect-uniform','one-minute-chart-is-precision-premise-not-larger-level-ban','oscillation-sell-before-buy-top-reduce-bottom-rebuy-old-low-chips','possible-third-sell-stronger-shake-stop-rebuy-wait-down-buy'],'59给3994近邻预设统一精度及基图精度不碍大级；已有低位筹码先卖后买、可能三卖即停补仍有条件，未证明任何精度交易结果等价或费用/容量可忽略。')]
 followups=[]
 for pid,slugs,finding in changes:
  ids=['upper-l059-c-stage-'+s for s in slugs];assert pid in pending_ids and all(x in known for x in ids)
  followups.append(dict(pending_id=pid,status='new_source_located_scope_still_pending',new_claim_ids=ids,finding=finding,global_pending_not_closed=True,graph_version=VERSION))
 (AGENT/'curation/upper/c_stage_l059.partial-resolutions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in followups),encoding='utf-8')
 checks=['28命题32证据预检，46段全台账、PDF443至450八页7整图及446完整页实际查看','原3214命题4390证据未改；2文907页9647段528图逐行仅5段日期及7图来源元数据授权变化，原字/几何/映射保持','3242命题全引用检查0错误，33项现有Node测试全部通过','6来源/条件边界组、7组现有CLI/共享读取一致、14命题14关联7图核对通过；查询数据库/manifest哈希不变','冻结240题239取证计划/240来源身份通过，原重合前20召回仍失败，固定题/排序未改','3242命题308概念661关系及Markdown/coverage同版本导出','3旧待核补来源仍开放，本批7待核；交付仅知识库，软件已排除']
 not_run=['60至61共2课未完整语义审读，106课阅读记录不等技术全抽取或所有解释统一','43/57混合夹注来源拆分、54长编号答复完整跨页来源关联及全书最终来源/引用/覆盖审计未完成','59早期线段/3994精度与局部编号、不同分解/震荡区间和回补力度量化仍有显式待核','冻结前20召回回归及完整G/自然查询/生成回答评价未完成，现有工具评价限制如实披露；同模型四轮非独立/人类金标准','最终知识库目录/归档及哈希交付清单尚未组装；固定两册未核原博客、未外证历史宏观/股票及可成交强语']
 evaluation=dict(executable_development_cases=240,target=240,gold_review_status='model_reviewed_development',human_gold_reviewed=False,independent_test_set=False,generated_answers_scored=False,retrieval_plan_passed_on_current_graph=239,source_identity_passed_on_current_graph=240,open_retrieval_regressions=failures,full_stage_g_acceptance_complete=False,new_project_gold_cases_created_in_this_batch=0,note='固定题和gold未改，重合前20仍失败；软件已排除，不冒知识本体/生成回答质量证明。')
 acceptance='59课28命题32证据发布；3242引用/33测试/6边界/7现有读取一致和14图文关联通过，同版本导出；冻结240题239计划/240身份通过。知识库余2课及全书来源和交付审计，不构建软件。'
 next_anchor=next_row[0]+' / lesson-060';next_action='接续第60课图解分析示范五，PDF451标题；核走势类型/中枢、当下完成状态、精度与局部编号及原页/整图的后加时间边界。然后61及全书来源拆分/覆盖与最终知识库交付。'
 p=AUDIT/'stage-c-l059-publication.json';pub=read(p);assert pub['graph_version']==VERSION and pub['formal_import']=='passed' and list(pub['batch_sha256'].values())==[sha(AGENT/'curation/upper/c_stage_l059.reviewed.jsonl')]
 pub.update(updated_at=datetime.now(timezone.utc).isoformat(),checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_action=next_action,exports=exports,final_sha256=dict(database=sha(KB/'graph.sqlite'),manifest=sha(KB/'manifest.json')),development_evaluation=evaluation,partial_pending_followups=len(followups),semantic_completion=False,writes_to_knowledge_graph_by_this_finalizer=False,delivery_scope=scope['active_deliverable'],delivery_scope_file='curation/delivery-scope.json',excluded_software_deliverables=scope['excluded_software_deliverables']);write(p,pub)
 p=AGENT/'curation/progress.json';progress=read(p);assert progress['graph_version'] in ['0.1.0-review-60afc026a0f3',VERSION]
 if progress['graph_version']!=VERSION:progress['previous_checkpoint']={k:progress[k] for k in ['graph_version','completed','next_action','evaluation']}
 outputs=['source-audit/stage-c-l059-'+n+'.json' for n in ['source-plan','source-applied','source-invariants','publication','verification']]+['upper/c_stage_l059.partial-resolutions.jsonl'];progress['machine_outputs']=list(dict.fromkeys(progress['machine_outputs']+outputs))
 progress.update(updated_at=datetime.now(timezone.utc).isoformat(),graph_version=VERSION,counts=counts,claim_status_counts=statuses,figure_origin_counts=figure_status,unit_processing_status_counts=unit_status,semantic_completion=False,delivery_scope=scope['active_deliverable'],delivery_scope_file='curation/delivery-scope.json',excluded_software_deliverables=scope['excluded_software_deliverables'],completed=['59课46段8页7整图同模型四轮，28命题32证据12关系支撑、10新增关系，无新增概念','5段6/15时间头管辖与7图4未核3后加修正；原3214命题4390证据及全源原字/几何/映射不动，原26/12/9顺序/未来K保留','线段形态非幅度、相邻异向、三折/一字涨停和一般背驰确认保早期语境；3994.57/3994.21近邻精度预设统一，7—8—9局部及58图17/59图19不自动实体合并','1—19只5分盘整，19—45新5分未完，另一22—31枢和41三买后新枢最终不重叠才条件上涨趋势；42—45强支用旧枢震荡区间非裸核心，9段升级为本例','先卖后买限已有低位筹码进入较大震荡；可能三卖即停补并等新买点，6/15两类新高股条件/6/18三卖有效破4224联合保留，CCTV自述仍reader','3242引用/33测试/6边界/7现有读取一致及14图文关联通过，同版导出；冻结240题239计划/240身份通过，原1回归开放','106课有阅读记录，剩60至61两课；3旧待核补来源仍开放、本批7待核，最终仅知识库'],pending=not_run,checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_resume_anchor=next_anchor,next_action=next_action,coverage_caveat='59课46段8页7整图由同一代理四轮，累计106课阅读记录含先前62至64；全书尚余2课且来源/交付审计未完，不称独立复核或最终完成。',evaluation=evaluation,previous_turn_classification='progress：57至59三课98命题111证据发布，当前3242命题全引用通过、106课阅读记录，余2课；最新用户指令仅交付知识库。')
 write(p,progress);print(json.dumps(dict(graph_version=VERSION,reviewed=3242,reviewed_evidence=4422,development_cases=240,development_passed=239,remaining_lessons=2,next_anchor=next_anchor,delivery_scope=scope['active_deliverable'],semantic_completion=False),ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
