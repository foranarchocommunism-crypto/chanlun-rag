"""Finalize lesson49 checked publication without mutating the graph."""
import hashlib,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';AUDIT=Path(__file__).resolve().parent;VERSION='0.1.0-review-7fa30c4809d4'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
 try:
  assert json.loads(db.execute("select value from metadata where key='graph_version'").fetchone()[0])==VERSION
  counts={t:db.execute(f'select count(*) from {t}').fetchone()[0] for t in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']};assert counts==dict(documents=2,pages=907,units=110,passages=9647,figures=528,concepts=294,claims=5538,evidence=6638,relations=548,reviews=2969)
  statuses=db.execute('select review_status,count(*) from claims group by review_status order by review_status').fetchall();assert dict(statuses)==dict(pending=2612,rejected=27,reviewed=2899)
  unit_status=db.execute('select processing_status,count(*) from units group by processing_status order by processing_status').fetchall();assert dict(unit_status)['extracted']==12
  figure_status=db.execute('select origin_status,count(*) from figures group by origin_status order by origin_status').fetchall()
  assert db.execute("select count(*) from evidence e join claims c on c.id=e.claim_id where c.review_status='reviewed'").fetchone()[0]==3999
  next_row=db.execute("select id,pdf_page,text from passages where unit_id='lesson-050' order by pdf_page,block_index,id limit 1").fetchone();assert next_row[0]=='volume_1-a53e99c37ca5-p0362-b011'
  known={r[0] for r in db.execute("select id from claims where review_status='reviewed'")}
 finally:db.close()
 assert read(KB/'manifest.json')['graph_version']==VERSION
 inv=read(AUDIT/'stage-c-l049-source-invariants.json');assert inv['pass'] and inv['graph_version']==VERSION and inv['original_reviewed_claims_unchanged']==2857 and inv['original_reviewed_evidence_unchanged']==3946
 verify=read(AUDIT/'stage-c-l049-verification.json');assert verify['pass'] and verify['graph_version']==VERSION and len(verify['checks'])==6 and len(verify['parity'])==7 and verify['intended_figure_links_checked']==dict(claims=7,associations=10,unique_figures=4)
 dev=read(AGENT/'evaluation/stage-g-development-current.results.json');assert dev['graph_version']==VERSION and dev['executable_development_cases']==240 and all(r['source_identity_matches_expected'] for r in dev['observations'])
 failures=[dict(query_id=r['query_id'],missing=r['missing'],queries=r['queries']) for r in dev['observations'] if not r['automatic_retrieval_contract_pass']];assert dev['retrieval_plan_contract_passed']==239 and [f['query_id'] for f in failures]==['g-b05-coincidence']
 exports={}
 for name,count in [('claims',2899),('concepts',294),('relations',548)]:
  p=KB/'exports'/f'{name}.jsonl';rows=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()];assert len(rows)==count and all(r['graph_version']==VERSION for r in rows);exports[name]=dict(rows=count,graph_version=VERSION,sha256=sha(p))
 assert VERSION in (KB/'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150] and read(KB/'exports/coverage.json')['graph_version']==VERSION
 pending_ids={json.loads(l)['id'] for n in [45,47,48] for l in (AGENT/'curation/upper'/f'c_stage_l{n:03d}.pending.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()}
 changes=[
 ('upper-l048-c-stage-pending-zero-cost-absolute-risk-accounting-software-capacity-and-turnover',['mode-only-own-consolidation-up-small-level-no-zero-cost','capital-size-reduces-utilization-and-growth-bottleneck','full-oscillation-sell-buyback-needs-skill-novice-partial-risk'],'49小级无0成本与容量/全仓限制明确，作者模型保证不丢筹码仍受识别精度/误判风险；未解决会计与经济风险全无证明。'),
 ('upper-l048-c-stage-pending-force-calculable-no-formula-and-c-stronger-small-to-large',['oscillation-generally-contracts-expanding-force-not-automatic-third-sell','no-divergence-new-center-may-overlap-small-to-large','choose-two-legs-before-MACD-not-standalone-second-condition'],'49特殊扩张震荡可更强却不三卖，无同级背驰仍可重合大级新枢，先选择两段再MACD；未给完整力度函数/积分或物理逃逸公式。'),
 ('upper-l048-c-stage-pending-C-extension-short-reply-no-endpoint-or-comparison-endorsement',['choose-two-legs-before-MACD-not-standalone-second-condition','two-child-centers-connector-third-buy-is-third-child'],'49先选段再指标并补连接段第三次级，但未逐项答48B方向、c撇或d比哪段、完成确认，仍开放。'),
 ('upper-l048-c-stage-pending-commentary-dates-3692-3699-and-later-figure',['3745-center-upper-edge-not-reader-last-minute-price','center-start-apr24-0935-not-todays-retain-0931-difference'],'49解释3745为上沿又记0935，与48的0931原字并存，不修3692/3699；两行情图晚至4/27，不能认证早前预测。'),
 ('upper-l047-c-stage-pending-tick-divergence-length-vs-area-completion-and-rebound-target',['tick-divergence-one-minute-area-five-view-one-signal-correlations','000625-fifteen-view-area-only-corresponding-small-level'],'49分笔借1分柱面积/5分看1分，与47柱长措辞分别留；观察周期非背驰级别，未给精确面积窗或把二者强等。'),
 ('upper-l047-c-stage-pending-execution-Tplus1-Tplus0-cash-capacity-and-hedge-not-specified',['aggressive-thirty-five-down-next-up-no-high-or-divergence-exit','oscillation-upper-reduce-lower-add-no-rebuy-after-third-sell','full-oscillation-sell-buyback-needs-skill-novice-partial-risk'],'49增加固定级别震荡仓位/三卖停止回补和激进5下5上退出规则，仍未形式化T+1/费用/实际成交/对冲算法。'),
 ('upper-l045-c-stage-pending-hold-cash-waiting-level-guarantee-and-intralevel-trades',['fix-operation-level-first-find-last-established-center','inside-center-wait-skilled-sublevel-second-buy-exception','skip-own-and-above-down-larger-consolidation-may-miss-rebound'],'49固定级别三位置/三点状态、等待和技能次级二买例外补充，原编号张力及实时识别/执行保证仍不完整。'),
 ]
 followups=[]
 for pid,slugs,finding in changes:
  ids=['upper-l049-c-stage-'+s for s in slugs];assert pid in pending_ids and all(x in known for x in ids);followups.append(dict(pending_id=pid,status='new_source_located_scope_still_pending',new_claim_ids=ids,finding=finding,global_pending_not_closed=True,graph_version=VERSION))
 (AGENT/'curation/upper/c_stage_l049.partial-resolutions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in followups),encoding='utf-8')
 checks=['42条Schema/引用/身份/坐标预检，83段台账、8页4整图实际视觉审查','原2857命题3946证据未改；2文907页9647段528图逐行比对只21时间和4图来源字段授权变化','33项Node工程测试通过，串行运行','2899命题全量引用校验0错误','6组语义/来源/条件边界与7组CLI/共享/桌面模块一致，7命题10关联4图逐项核；查询只读哈希不变','240冻结开发题执行，239取证计划通过/240身份通过；g-b05-coincidence前20召回仍失败，未改题或核心排序，见47截断诊断','2899命题/294概念/548关系、Markdown和coverage同版本导出','7条旧待核新增来源但全部保持开放；本批8待核']
 not_run=['冻结前20召回回归尚未修；240完整类别/自然问题基线/生成回答质量/消融对抗未完成，开发计划不冒充完整G','50至61共12课尚未完整语义审读，全书交叉/43混合夹注/数值与图源未全解决','独立Agent实际打包运行与Windows离线/PDF缩放旋转跨页交互未验收']
 evaluation=dict(executable_development_cases=240,target=240,gold_review_status='model_reviewed_development',human_gold_reviewed=False,independent_test_set=False,generated_answers_scored=False,retrieval_plan_passed_on_current_graph=239,source_identity_passed_on_current_graph=240,open_retrieval_regressions=failures,full_stage_g_acceptance_complete=False,new_project_gold_cases_created_in_this_batch=0,note='固定题未改，全部身份通过；一条重合前20召回仍失败，分页找到不算原计划通过。')
 acceptance='49课42命题53证据发布；2899引用及33工程通过，冻结240题239计划/240身份通过，1条召回回归开放，语义及产品目标未完成。'
 next_anchor=next_row[0]+' / lesson-050';next_action='接续50课操作中的一些细节问题，实际PDF362页标题；核MACD跨周期面积/级别、操作细节对49两模式的限制，完整审读作者答疑和原图。'
 p=AUDIT/'stage-c-l049-publication.json';pub=read(p);assert pub['graph_version']==VERSION and pub['formal_import']=='passed' and list(pub['batch_sha256'].values())==[sha(AGENT/'curation/upper/c_stage_l049.reviewed.jsonl')]
 pub.update(updated_at=datetime.now(timezone.utc).isoformat(),checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_action=next_action,exports=exports,final_sha256=dict(database=sha(KB/'graph.sqlite'),manifest=sha(KB/'manifest.json')),development_evaluation=evaluation,partial_pending_followups=7,semantic_completion=False,writes_to_knowledge_graph_by_this_finalizer=False);write(p,pub)
 p=AGENT/'curation/progress.json';progress=read(p);assert progress['graph_version'] in ['0.1.0-review-ebd7062c0ca7',VERSION]
 if progress['graph_version']!=VERSION:progress['previous_checkpoint']={k:progress[k] for k in ['graph_version','completed','next_action','evaluation']}
 outputs=['source-audit/stage-c-l049-'+n+'.json' for n in ['source-plan','source-applied','source-invariants','publication','verification']]+['upper/c_stage_l049.partial-resolutions.jsonl'];progress['machine_outputs']=list(dict.fromkeys(progress['machine_outputs']+outputs))
 progress.update(updated_at=datetime.now(timezone.utc).isoformat(),graph_version=VERSION,counts=counts,claim_status_counts=statuses,figure_origin_counts=figure_status,unit_processing_status_counts=unit_status,semantic_completion=False,completed=['49课83段8页4图同模型四轮，42命题53证据14关系支撑；新增利润率及两条作者命名最大定理共3概念','21日期空格与4图来源核对，2后加2原发未核；2857命题3946证据及所有源字/几何/映射未改','固定级别找最后已形成中枢，不等最后已结束；三位置/三点状态保技能例外，原第二种第2类买点衔接错号张力未静改','两模式的三买前原枢震荡/后上移/新枢再震荡与同级背驰退出区分；震荡可更强不三卖，三卖停回补，小转大可重合','两最大定理只保作者命名陈述未附证明；利润率平均利润除占资平均时间，频率/市场三买机会/容量影响总体，50%/10%和年200/500不实证','理想全仓不抹误判/部分仓或大资金不能全仓，小级无0成本；激进30分例先5下再5上三择一退出，未变AND','先选比较段再MACD，分笔1分柱面积与47长度差异保留，观察周期非信号级；0935/0931与3745/3745.40不静合，公司恶意仅上下文','2899引用/33工程/6边界/7模块及7命题10图关联通过，同版本导出；240题239计划/240身份通过，1召回回归开放','7旧待核补充仍开放；96课阅读记录含历史62至64，50至61共12课未完整审读'],pending=['本批8待核见upper/c_stage_l049.pending.jsonl；最大定理证明/执行强语、原编号/时刻/图源、分笔长度面积及连接段完成等未解决','50至61共12课未完整语义审读；96课阅读记录不等全书技术抽取或解释统一','冻结g-b05-coincidence前20召回开放；完整G类别/自然查询基线/生成回答/消融对抗、43夹注及全书交叉未完成','独立Agent和Windows实际交付/离线/PDF交互未验收'],checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_resume_anchor=next_anchor,next_action=next_action,coverage_caveat='49课83段8页4图由同一代理四轮，累计96课阅读记录含历史62至64，不称独立复核或全书完成。',evaluation=evaluation,previous_turn_classification='progress：49课42命题53证据发布，2899引用/33工程通过；冻结题239/240且240身份通过，1召回回归开放，全书余12课。');write(p,progress)
 print(json.dumps(dict(graph_version=VERSION,reviewed=2899,development_cases=240,development_passed=239,remaining_lessons=12,next_anchor=next_anchor,semantic_completion=False),ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
