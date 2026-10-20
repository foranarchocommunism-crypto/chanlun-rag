"""Finalize lesson53 checked publication without mutating the graph."""
import hashlib,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';AUDIT=Path(__file__).resolve().parent;VERSION='0.1.0-review-0a42d381d402'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
 try:
  assert json.loads(db.execute("select value from metadata where key='graph_version'").fetchone()[0])==VERSION
  counts={t:db.execute(f'select count(*) from {t}').fetchone()[0] for t in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']};assert counts==dict(documents=2,pages=907,units=110,passages=9647,figures=528,concepts=301,claims=5675,evidence=6815,relations=591,reviews=3106)
  statuses=db.execute('select review_status,count(*) from claims group by review_status order by review_status').fetchall();assert dict(statuses)==dict(pending=2612,rejected=27,reviewed=3036)
  unit_status=db.execute('select processing_status,count(*) from units group by processing_status order by processing_status').fetchall();assert dict(unit_status)['extracted']==8
  figure_status=db.execute('select origin_status,count(*) from figures group by origin_status order by origin_status').fetchall()
  assert db.execute("select count(*) from evidence e join claims c on c.id=e.claim_id where c.review_status='reviewed'").fetchone()[0]==4176
  next_row=db.execute("select id,pdf_page,text from passages where unit_id='lesson-054' order by pdf_page,block_index,id limit 1").fetchone();assert next_row[0]=='volume_1-a53e99c37ca5-p0400-b007'
  known={r[0] for r in db.execute("select id from claims where review_status='reviewed'")}
 finally:db.close()
 assert read(KB/'manifest.json')['graph_version']==VERSION
 inv=read(AUDIT/'stage-c-l053-source-invariants.json');assert inv['pass'] and inv['graph_version']==VERSION and inv['original_reviewed_claims_unchanged']==3006 and inv['original_reviewed_evidence_unchanged']==4141
 verify=read(AUDIT/'stage-c-l053-verification.json');assert verify['pass'] and verify['graph_version']==VERSION and len(verify['checks'])==6 and len(verify['parity'])==7 and verify['intended_figure_links_checked']==dict(claims=0,associations=0,unique_figures=0)
 dev=read(AGENT/'evaluation/stage-g-development-current.results.json');assert dev['graph_version']==VERSION and dev['executable_development_cases']==240 and all(r['source_identity_matches_expected'] for r in dev['observations'])
 failures=[dict(query_id=r['query_id'],missing=r['missing'],queries=r['queries']) for r in dev['observations'] if not r['automatic_retrieval_contract_pass']];assert dev['retrieval_plan_contract_passed']==239 and [f['query_id'] for f in failures]==['g-b05-coincidence']
 exports={}
 for name,count in [('claims',3036),('concepts',301),('relations',591)]:
  p=KB/'exports'/f'{name}.jsonl';rows=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()];assert len(rows)==count and all(r['graph_version']==VERSION for r in rows);exports[name]=dict(rows=count,graph_version=VERSION,sha256=sha(p))
 assert VERSION in (KB/'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150] and read(KB/'exports/coverage.json')['graph_version']==VERSION
 pending_ids={json.loads(l)['id'] for n in [28,49,50,52] for l in (AGENT/'curation/upper'/f'c_stage_l{n:03d}.pending.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()}
 changes=[
 ('upper-l052-c-stage-pending-precise-five-completion-lower-chart-versus-MACD-auxiliary',['thirty-view-completed-five-moves-as-unstructured-lines','switch-magnification-for-divergence-leg-and-third-point','one-level-regroup-extremes-not-all-finer-level-endpoints'],'53完成次级线段化和背驰/三类点下钻说明固定操作不排斥为目的换观察级；没有补MACD跨采样关系或所有实时完成算法。'),
 ('upper-l052-c-stage-pending-same-level-association-first-three-extension-and-second-buy-second-leg',['all-three-root-first-at-different-levels-not-same-label','second-sell-sublevel-down-up-no-new-high-or-consolidation-divergence','first-best-when-present-second-best-small-to-large-no-first'],'53明确跨级根一类却保同级三类，二卖下后上、不新高或盘背为OR，二类非专为小转大；仍未逐项确定52读者A1/A3或所有分解等值。'),
 ('upper-l052-c-stage-pending-literal-not-smaller-inequality-and-small-to-large-scope',['first-point-is-divergence-at-selected-level','literal-bing-chuji-versus-no-same-level-first-point-unresolved','first-best-when-present-second-best-small-to-large-no-first'],'53同段末明确小转大无该级一类，但中间并触及又字面有张力；为52不小于提供更多原文范围线索，不私改任一原字或称其已统一。'),
 ('upper-l049-c-stage-pending-guaranteed-chip-safety-full-position-and-skill-execution',['tiny-level-conditional-skilled-smooth-channel-thirty-usual-five-floor','small-level-utilization-zero-cost-chips-capacity-position-detail-deferred','chase-price-replaced-by-points-daily-third-author-100-profit','unfamiliar-sell-first-rebuy-author-no-loss-context-not-global-guarantee'],'53反应/成本/容量及技术且通道门槛进一步限定执行，同时仍有100%/不用亏钱作者强语；不能把历史理论保证换成实盘绩效或无风险认证。'),
 ('upper-l050-c-stage-pending-logic-confidence-geometric-guarantee-and-practice-criteria',['reaction-time-costs-require-coarser-level-three-equally-important','chase-price-replaced-by-points-daily-third-author-100-profit','strict-tick-bottom-up-possible-not-mandatory-every-analysis'],'53客观反应时间/费用支持选择较大统一级别，但理论绝对可操作性/100%强语仍无实测；没有补50几何收益证明或模拟达标样本。'),
 ('upper-l028-c-stage-pending-adjustment-choice-and-private-force-versus-macd',['exrights-short-adjust-long-large-may-ignore'],'53短期可复权、长时大级可不管与28相近，但15特定均线日/周月范围还不同；未给短期时长、复权方式或MACD私有指标实测，不自动按后日期覆盖。'),
 ]
 followups=[]
 for pid,slugs,finding in changes:
  ids=['upper-l053-c-stage-'+s for s in slugs];assert pid in pending_ids and all(x in known for x in ids)
  followups.append(dict(pending_id=pid,status='new_source_located_scope_still_pending',new_claim_ids=ids,finding=finding,global_pending_not_closed=True,graph_version=VERSION))
 (AGENT/'curation/upper/c_stage_l053.partial-resolutions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in followups),encoding='utf-8')
 checks=['30条Schema/引用/身份/映射/坐标预检，57段台账及PDF396至400五页视觉核对，397/398原并字不修','原3006命题4141证据未改；2文907页9647段528图逐行只22日期时刻空格授权变化','33项Node工程测试全部通过，测试终止后运行全量引用检查','3036命题全量引用校验0错误','6组语义/来源/条件/短答指代与7组CLI/共享/桌面模块查询一致，零图关联逐条核且查询只读哈希不变','冻结240题执行239取证计划/240来源身份通过，重合前20召回失败开放，原题/核心排序未改','3036命题/301概念/591关系及Markdown/coverage同版本导出','6旧待核补来源仍开放，本批6待核；并触及/并一定要、更大中枢相对基准/复权范围及收益强语不伪装已解决']
 not_run=['冻结前20召回回归未修，完整G类别/自然查询基线/生成回答/消融对抗未完成','54至61共8课未完整语义审读；52不小于/以上、53并字、43混合夹注和全书跨课/图文尚待核','独立Agent打包真实执行及Windows离线/PDF缩放旋转跨页交互未验收']
 evaluation=dict(executable_development_cases=240,target=240,gold_review_status='model_reviewed_development',human_gold_reviewed=False,independent_test_set=False,generated_answers_scored=False,retrieval_plan_passed_on_current_graph=239,source_identity_passed_on_current_graph=240,open_retrieval_regressions=failures,full_stage_g_acceptance_complete=False,new_project_gold_cases_created_in_this_batch=0,note='固定题未改，全部身份通过；一条重合前20召回仍失败，分页找到不算原计划通过。')
 acceptance='53课30命题35证据发布；3036引用/33工程/6边界/7三端模块检查通过，冻结240题239计划/240身份通过，1召回回归开放，完整语义及产品目标未完成。'
 next_anchor=next_row[0]+' / lesson-054'
 next_action='接续54课一个具体走势的分析，实际PDF400页标题；完整审读跨级图例、分段次序、三类点与中枢形成/完成，核完整原图及后加图时间边界，保既有原字歧义和执行约束。'
 p=AUDIT/'stage-c-l053-publication.json';pub=read(p)
 assert pub['graph_version']==VERSION and pub['formal_import']=='passed' and list(pub['batch_sha256'].values())==[sha(AGENT/'curation/upper/c_stage_l053.reviewed.jsonl')]
 pub.update(updated_at=datetime.now(timezone.utc).isoformat(),checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_action=next_action,exports=exports,final_sha256=dict(database=sha(KB/'graph.sqlite'),manifest=sha(KB/'manifest.json')),development_evaluation=evaluation,partial_pending_followups=len(followups),semantic_completion=False,writes_to_knowledge_graph_by_this_finalizer=False);write(p,pub)
 p=AGENT/'curation/progress.json';progress=read(p);assert progress['graph_version'] in ['0.1.0-review-58e2535c21e3',VERSION]
 if progress['graph_version']!=VERSION:progress['previous_checkpoint']={k:progress[k] for k in ['graph_version','completed','next_action','evaluation']}
 outputs=['source-audit/stage-c-l053-'+n+'.json' for n in ['source-plan','source-applied','source-invariants','publication','verification']]+['upper/c_stage_l053.partial-resolutions.jsonl']
 progress['machine_outputs']=list(dict.fromkeys(progress['machine_outputs']+outputs))
 progress.update(updated_at=datetime.now(timezone.utc).isoformat(),graph_version=VERSION,counts=counts,claim_status_counts=statuses,figure_origin_counts=figure_status,unit_processing_status_counts=unit_status,semantic_completion=False,
 completed=['53课57段5页无图同模型四轮，30命题35证据13关系支撑，新增11关系/无新概念','22日期空格规范，原3006命题4141证据及全源原字/几何/映射未改；397并触及与段末无一类、398并一定要原字和歧义分别保留','完成次级在线段化视角忽略内部结构，1分结合律归端点不证明全部分笔原端点相同；背驰段区间套/三类判断可下钻，a发生时B未出现不当当下已知','同级三类均重要与跨级根一类分开，二卖下后上不新高或盘背保OR；小转大无同级一类时二类最佳，二类后更大中枢相对基准仍待核，三类转大/新同级分支保留','反应/费用/容量和技术且通道条件保留，普通30/最低5为执行建议非理论最低；100%/不用亏钱为作者强语不冒实盘证明，仓位细节明言后说；复权53/28与15范围不同仍开放','3036引用/33工程/6边界/7模块通过并同版本导出，短答两股互动保reader上下文；冻结240题239计划/240身份通过，1前20召回回归开放','6旧待核补来源仍开放；100课阅读记录含历史62至64，54至61共8课未完整审读'],
 pending=['本批6待核见upper/c_stage_l053.pending.jsonl：两处并原字、二类更大中枢基准/完成、跨级观察/三类用途、执行绝对强语、复权及历史短答范围','54至61共8课未完整语义审读，100课阅读记录不等技术全抽取或解释统一','重合前20召回回归、完整G类别/自然基线/生成回答/消融对抗及43夹注/全书交叉未完成','独立Agent与Windows真实交付、离线/PDF交互未验收'],checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_resume_anchor=next_anchor,next_action=next_action,coverage_caveat='53课57段5页无图由同一代理四轮，累计100课阅读记录含历史62至64，不称独立复核或全书完成。',evaluation=evaluation,previous_turn_classification='progress：53课30命题35证据发布，3036引用/33工程及6边界7模块通过；冻结题239/240且240身份通过，1召回回归开放，全书余8课。')
 write(p,progress)
 print(json.dumps(dict(graph_version=VERSION,reviewed=3036,reviewed_evidence=4176,development_cases=240,development_passed=239,remaining_lessons=8,next_anchor=next_anchor,semantic_completion=False),ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
