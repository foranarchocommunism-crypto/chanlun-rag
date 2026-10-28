"""Finalize lesson54 checked publication without mutating the graph."""
import hashlib,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';AUDIT=Path(__file__).resolve().parent;VERSION='0.1.0-review-6c88a992da52'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
 try:
  assert json.loads(db.execute("select value from metadata where key='graph_version'").fetchone()[0])==VERSION
  counts={t:db.execute(f'select count(*) from {t}').fetchone()[0] for t in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']};assert counts==dict(documents=2,pages=907,units=110,passages=9647,figures=528,concepts=302,claims=5716,evidence=6872,relations=606,reviews=3147)
  statuses=db.execute('select review_status,count(*) from claims group by review_status order by review_status').fetchall();assert dict(statuses)==dict(pending=2612,rejected=27,reviewed=3077)
  unit_status=db.execute('select processing_status,count(*) from units group by processing_status order by processing_status').fetchall();assert dict(unit_status)['extracted']==7
  figure_status=db.execute('select origin_status,count(*) from figures group by origin_status order by origin_status').fetchall()
  assert db.execute("select count(*) from evidence e join claims c on c.id=e.claim_id where c.review_status='reviewed'").fetchone()[0]==4233
  next_row=db.execute("select id,pdf_page,text from passages where unit_id='lesson-055' order by pdf_page,block_index,id limit 1").fetchone();assert next_row[0]=='volume_1-a53e99c37ca5-p0412-b000'
  known={r[0] for r in db.execute("select id from claims where review_status='reviewed'")}
 finally:db.close()
 assert read(KB/'manifest.json')['graph_version']==VERSION
 inv=read(AUDIT/'stage-c-l054-source-invariants.json');assert inv['pass'] and inv['graph_version']==VERSION and inv['original_reviewed_claims_unchanged']==3036 and inv['original_reviewed_evidence_unchanged']==4176
 verify=read(AUDIT/'stage-c-l054-verification.json');assert verify['pass'] and verify['graph_version']==VERSION and len(verify['checks'])==6 and len(verify['parity'])==7 and verify['intended_figure_links_checked']==dict(claims=17,associations=17,unique_figures=7)
 dev=read(AGENT/'evaluation/stage-g-development-current.results.json');assert dev['graph_version']==VERSION and dev['executable_development_cases']==240 and all(r['source_identity_matches_expected'] for r in dev['observations'])
 failures=[dict(query_id=r['query_id'],missing=r['missing'],queries=r['queries']) for r in dev['observations'] if not r['automatic_retrieval_contract_pass']];assert dev['retrieval_plan_contract_passed']==239 and [f['query_id'] for f in failures]==['g-b05-coincidence']
 exports={}
 for name,count in [('claims',3077),('concepts',302),('relations',606)]:
  p=KB/'exports'/f'{name}.jsonl';rows=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()];assert len(rows)==count and all(r['graph_version']==VERSION for r in rows);exports[name]=dict(rows=count,graph_version=VERSION,sha256=sha(p))
 assert VERSION in (KB/'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150] and read(KB/'exports/coverage.json')['graph_version']==VERSION
 pending_ids={json.loads(l)['id'] for n in [49,50,52,53] for l in (AGENT/'curation/upper'/f'c_stage_l{n:03d}.pending.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()}
 changes=[
 ('upper-l053-c-stage-pending-second-point-larger-center-reference-and-type-completion',['five-center-one-down-one-up-no-high-or-divergence-second-sell','rare-second-buy-below-first-or-second-sell-above-first-approved','second-center-guarantee-no-larger-level-wording-reader-item-two'],'54以5分中枢和1下1上、不新高或背驰说明二卖；编号1肯定少见倒置二类，编号2绝对保证但又没有什么更大级别，补新来源并保跨页读者指代，未解全部级别/无限时间/实时完成证明。'),
 ('upper-l053-c-stage-pending-magnification-endpoints-and-cross-level-first-not-label-collapse',['subminute-legs-as-lines-except-last-at-chosen-level','first-decomposition-g5-five-center-d2-g5-whole-submoves','second-decomposition-g6-five-center-d3-g5-g7-not-third-sell','g1-two-legs-no-one-center-tick-second-sell-d2-first-center'],'54只在选级视角将完成次级看线段，首g5/二g6不同中心各用完整次级走势高低点，分笔二卖非1分二卖；原中枢/走势措辞和公式端点/设价仍待核，不强定全细级端点统一。'),
 ('upper-l052-c-stage-pending-third-point-type-vs-center-and-retest-whole-move',['d7g7-one-minute-type-specific-retest-doji-lower-chart-confirmation','third-point-sublevel-leave-return-no-center-reentry-item-three','fast-forceful-weekly-break-smaller-third-needs-volume-strength','divergence-return-causes-oscillation-third-only-trend-possibility'],'54本例K形可提示内部更小三段并可小图确认，非任意K数充分；次级离返重申，大幅快破用小级点须量力且区别震荡；三类后方向强语不等完整趋势，未穷尽实时识别/执行风险。'),
 ('upper-l052-c-stage-pending-same-level-association-first-three-extension-and-second-buy-second-leg',['at-d4-two-permitted-decompositions-preserve-original-formulas','choose-current-meaningful-decomposition-all-must-obey-rules','g7-two-decompositions-same-direction-warning-not-identical-labels','trend-center-connector-same-direction-no-overlap-wrong-d2g2'],'54合规多解按当下意义选择，g7两式标签不同但操作警示相同；同向连接/中枢不重叠规范补来源，仍未全解52九段/延伸/次级第二段所有等值。'),
 ('upper-l049-c-stage-pending-guaranteed-chip-safety-full-position-and-skill-execution',['fast-forceful-weekly-break-smaller-third-needs-volume-strength','novice-buy-wait-own-level-third-sell-prefer-early-use-first-second','third-point-followthrough-absolute-author-claim-premises-unverified'],'54快速大幅突破才有小级替代入口且要量力/技能，买卖保守程度不同，一二卖不可忽略；三类后必继续仍为作者模型强语，不证实盘成交/收益/全仓无风险。'),
 ('upper-l050-c-stage-pending-logic-confidence-geometric-guarantee-and-practice-criteria',['complex-graph-skill-confidence-absolute-understanding-author-view','skill-criterion-fast-current-ruleful-decomposition-not-real-diploma','reader-failed-third-buy-rejected-no-exception-author-assertion'],'54提出任意图当下快速合规分解并指导操作的熟练标准，学历是戏谑；否读者自称三买、无例外仍理论性主张，未补几何利润证明/量化达标样本或独立评测。'),
 ]
 followups=[]
 for pid,slugs,finding in changes:
  ids=['upper-l054-c-stage-'+s for s in slugs];assert pid in pending_ids and all(x in known for x in ids)
  followups.append(dict(pending_id=pid,status='new_source_located_scope_still_pending',new_claim_ids=ids,finding=finding,global_pending_not_closed=True,graph_version=VERSION))
 (AGENT/'curation/upper/c_stage_l054.partial-resolutions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in followups),encoding='utf-8')
 checks=['41条Schema/引用/身份/映射/坐标预检，101段台账、PDF400至411十二页及7幅整图实际视觉核对','原3036命题4176证据未改；2文907页9647段528图逐行仅19时间空格和7图来源备注授权变化，原字/公式/坐标不动','33项Node工程测试全部通过，测试终止后运行全量引用检查','3077命题全量引用校验0错误','6组语义/来源/条件/跨页编号指代与7组CLI/共享/桌面模块一致，17命题17图文关联7图逐项核，查询只读哈希不变','冻结240题执行239取证计划/240来源身份通过，重合前20召回仍失败，原题/核心排序未改','3077命题/302概念/606关系及Markdown/coverage同版本导出','6旧待核补来源仍开放，本批8待核；默认邻段context不涵盖全部跨页编号提问的限制明确标记']
 not_run=['冻结前20召回回归未修，完整G类别/自然查询基线/生成回答/消融对抗未完成','55至61共7课未完整语义审读；原式端点/两分解与53/52原字、18与54连接级别、43混合夹注和全书跨课/图文尚待核','编号短答跨页完整问题未自动全部纳入邻段context；当前条件/备注提供联读源ID和原页，不宣称该接口限制已修','独立Agent打包真实执行及Windows离线/PDF缩放旋转跨页交互未验收']
 evaluation=dict(executable_development_cases=240,target=240,gold_review_status='model_reviewed_development',human_gold_reviewed=False,independent_test_set=False,generated_answers_scored=False,retrieval_plan_passed_on_current_graph=239,source_identity_passed_on_current_graph=240,open_retrieval_regressions=failures,full_stage_g_acceptance_complete=False,new_project_gold_cases_created_in_this_batch=0,note='固定题未改，全部身份通过；一条重合前20召回仍失败，分页找到不算原计划通过。')
 acceptance='54课41命题57证据发布；3077引用/33工程/6边界/7模块和17图文关联检查通过，冻结240题239计划/240身份通过，1召回回归开放；完整语义及产品目标未完成。'
 next_anchor=next_row[0]+' / lesson-055';next_action='接续55课买之前戏、卖之高潮，实际PDF412页标题；完整审读买卖时序、级别/资金与离开回试条件，实际查看所有原页/整图，继续保跨页编号context、原式/原字和全书跨课边界。'
 p=AUDIT/'stage-c-l054-publication.json';pub=read(p)
 assert pub['graph_version']==VERSION and pub['formal_import']=='passed' and list(pub['batch_sha256'].values())==[sha(AGENT/'curation/upper/c_stage_l054.reviewed.jsonl')]
 pub.update(updated_at=datetime.now(timezone.utc).isoformat(),checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_action=next_action,exports=exports,final_sha256=dict(database=sha(KB/'graph.sqlite'),manifest=sha(KB/'manifest.json')),development_evaluation=evaluation,partial_pending_followups=len(followups),semantic_completion=False,writes_to_knowledge_graph_by_this_finalizer=False);write(p,pub)
 p=AGENT/'curation/progress.json';progress=read(p);assert progress['graph_version'] in ['0.1.0-review-0a42d381d402',VERSION]
 if progress['graph_version']!=VERSION:progress['previous_checkpoint']={k:progress[k] for k in ['graph_version','completed','next_action','evaluation']}
 outputs=['source-audit/stage-c-l054-'+n+'.json' for n in ['source-plan','source-applied','source-invariants','publication','verification']]+['upper/c_stage_l054.partial-resolutions.jsonl'];progress['machine_outputs']=list(dict.fromkeys(progress['machine_outputs']+outputs))
 progress.update(updated_at=datetime.now(timezone.utc).isoformat(),graph_version=VERSION,counts=counts,claim_status_counts=statuses,figure_origin_counts=figure_status,unit_processing_status_counts=unit_status,semantic_completion=False,
 completed=['54课101段12页7整图同模型四轮，41命题57证据15关系支撑，新增通道式上涨概念/15关系','19时间空格及7图6未核1后加元数据规范，原3036命题4176证据及全源原字/公式/几何/映射未改','原g0g3左端/右端到d3、正文18.5/图18.59保张力；单价位重叠仍算，第一g5/[d2,g5]与第二g6/[d3,g5]各保，完整子走势高低点非子枢交集，g7标签异但方向警示可同','同级中枢须连接且同向/不重叠与三次级扩高一级不同，18次级或更低/54必须次级范围待核；具体K序只本例不造通用中枢公式','快速大幅周破小级三类须迅猛量力并区别震荡，新手买等本级/卖宁早且一二卖不缺；极端幅度为理论例，三类必继续不等必成趋势/实盘保证','编号1少见倒置二类、2绝对保证/没有什么更大级别、3仅重申次级离返分别对号，短答作者引/全问题reader分开；默认context未涵跨页全问，条件/备注给ID原页并记限制未修','3077引用/33工程/6边界/7模块/17图文关联通过并同版本导出，冻结240题239计划/240身份通过，1前20召回回归开放','6旧待核补来源仍开放，本批8待核；101课阅读记录含历史62至64，55至61共7课未完整审读'],
 pending=['本批8待核见upper/c_stage_l054.pending.jsonl：原式/设价、双分解高低点和完成、连接级别、三类方向强语及快破/极端理论例、编号短答、图源/指标通道和历史教学观点','55至61共7课未完整语义审读，101课阅读记录不等技术全抽取或解释统一','编号短答完整跨页问题未自动纳邻段context；重合前20召回回归、完整G类别/自然基线/生成回答/消融对抗及43夹注/全书交叉未完成','独立Agent与Windows真实交付、离线/PDF交互未验收'],checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_resume_anchor=next_anchor,next_action=next_action,coverage_caveat='54课101段12页7整图由同一代理四轮，累计101课阅读记录含历史62至64，不称独立复核或全书完成。',evaluation=evaluation,previous_turn_classification='progress：54课41命题57证据发布，3077引用/33工程与6边界7模块17图文关联通过；冻结题239/240且240身份通过，1召回回归开放，全书余7课。')
 write(p,progress)
 print(json.dumps(dict(graph_version=VERSION,reviewed=3077,reviewed_evidence=4233,development_cases=240,development_passed=239,remaining_lessons=7,next_anchor=next_anchor,semantic_completion=False),ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
