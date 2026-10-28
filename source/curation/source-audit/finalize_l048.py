"""Finalize lesson48 checked publication without mutating the graph."""
import hashlib,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';AUDIT=Path(__file__).resolve().parent;VERSION='0.1.0-review-ebd7062c0ca7'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
 try:
  assert json.loads(db.execute("select value from metadata where key='graph_version'").fetchone()[0])==VERSION
  counts={t:db.execute(f'select count(*) from {t}').fetchone()[0] for t in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']};assert counts==dict(documents=2,pages=907,units=110,passages=9647,figures=528,concepts=291,claims=5496,evidence=6585,relations=535,reviews=2927)
  statuses=db.execute('select review_status,count(*) from claims group by review_status order by review_status').fetchall();assert dict(statuses)==dict(pending=2612,rejected=27,reviewed=2857)
  unit_status=db.execute('select processing_status,count(*) from units group by processing_status order by processing_status').fetchall();assert dict(unit_status)['extracted']==13
  figure_status=db.execute('select origin_status,count(*) from figures group by origin_status order by origin_status').fetchall()
  assert db.execute("select count(*) from evidence e join claims c on c.id=e.claim_id where c.review_status='reviewed'").fetchone()[0]==3946
  next_row=db.execute("select id,pdf_page,text from passages where unit_id='lesson-049' order by pdf_page,block_index,id limit 1").fetchone();assert next_row[0]=='volume_1-a53e99c37ca5-p0355-b010'
  known={r[0] for r in db.execute("select id from claims where review_status='reviewed'")}
 finally:db.close()
 assert read(KB/'manifest.json')['graph_version']==VERSION
 inv=read(AUDIT/'stage-c-l048-source-invariants.json');assert inv['pass'] and inv['graph_version']==VERSION and inv['original_reviewed_claims_unchanged']==2818 and inv['original_reviewed_evidence_unchanged']==3896
 verify=read(AUDIT/'stage-c-l048-verification.json');assert verify['pass'] and verify['graph_version']==VERSION and len(verify['checks'])==6 and len(verify['parity'])==7 and verify['intended_figure_links_checked']==dict(claims=5,associations=5,unique_figures=1)
 dev=read(AGENT/'evaluation/stage-g-development-current.results.json');assert dev['graph_version']==VERSION and dev['executable_development_cases']==240 and all(r['source_identity_matches_expected'] for r in dev['observations'])
 failures=[dict(query_id=r['query_id'],missing=r['missing'],queries=r['queries']) for r in dev['observations'] if not r['automatic_retrieval_contract_pass']];assert dev['retrieval_plan_contract_passed']==239 and [f['query_id'] for f in failures]==['g-b05-coincidence']
 exports={}
 for name,count in [('claims',2857),('concepts',291),('relations',535)]:
  p=KB/'exports'/f'{name}.jsonl';rows=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()];assert len(rows)==count and all(r['graph_version']==VERSION for r in rows);exports[name]=dict(rows=count,graph_version=VERSION,sha256=sha(p))
 assert VERSION in (KB/'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150] and read(KB/'exports/coverage.json')['graph_version']==VERSION
 pending_ids={json.loads(l)['id'] for n in [45,46,47] for l in (AGENT/'curation/upper'/f'c_stage_l{n:03d}.pending.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()}
 changes=[
 ('upper-l047-c-stage-pending-tick-divergence-length-vs-area-completion-and-rebound-target',['two-centers-trend-can-end-any-time-not-must','intraday-down-below-one-divergence-and-trend-level-may-differ'],'48两枢可完非必完，日内例更可能1分以下且背驰/趋势可异级；47目标/柱长面积未全部形式化。'),
 ('upper-l047-c-stage-pending-borrowed-center-three-intervals-tiny-ignore-3892-3692-and-reader-questions',['apr25-return-3688-3699-oscillation-price-difference-retained','first-segment-in-third-case-center-range-not-single-segment'],'48保留3699与前3692新异值，作者说明所说是三段中枢共同区间非单段中枢；第二段覆盖及43/47旧数值未解决。'),
 ('upper-l047-c-stage-pending-execution-Tplus1-Tplus0-cash-capacity-and-hedge-not-specified',['large-capital-zero-cost-strategy-small-not-necessary-channel','skill-not-enough-for-daily-choose-weekly-monthly'],'48加强资金容量/通道/时间与技能级别限制；未补T+1及对冲完整成交/仓位算法。'),
 ('upper-l047-c-stage-pending-breakaway-gap-three-day-statistics-five-day-line-and-scope',['effective-break-same-as-third-sell-no-three-bars-rule'],'48答有效跌破对应三卖，不认可读者三根5分收低阈值；三天统计/有效站稳仍未形式化。'),
 ('upper-l046-c-stage-pending-balance-extremes-retrospective-overlap-labels-and-endpoint-equality',['apr25-first-three-bars-most-balanced-case-not-universal'],'48最平衡市是当日描述、前三K给全天高低为作者事后案例，不补所有日实时保证或强弱互斥定义。'),
 ('upper-l045-c-stage-pending-force-measure-rectangular-proposal-MACD-area-zero-axis',['force-computable-no-formula-MACD-proxy-no-escape-physics-law','c-force-above-b-not-necessarily-disjoint-new-center'],'48说可计算但未式，MACD辅助，未认可逃逸物理定律；c强不必不交新枢，小转大可重合，未解决45矩形提案。'),
 ('upper-l045-c-stage-pending-five-day-unilateral-not-consolidation-and-cost-safety',['risk-control-level-and-zero-cost-absolute-safety-author-claim','short-difference-zero-best-doubling-not-predictable','after-zero-gain-chips-until-very-large-sell'],'48零成本强语留作者核算/策略身份，0后仍特大卖点，并未证均线/零成本经济风险全无，保留45结构限制。'),
 ]
 followups=[]
 for pid,slugs,finding in changes:
  ids=['upper-l048-c-stage-'+s for s in slugs];assert pid in pending_ids and all(x in known for x in ids);followups.append(dict(pending_id=pid,status='new_source_located_scope_still_pending',new_claim_ids=ids,finding=finding,global_pending_not_closed=True,graph_version=VERSION))
 (AGENT/'curation/upper/c_stage_l048.partial-resolutions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in followups),encoding='utf-8')
 checks=['39条Schema/引用/身份/坐标预检，130段台账、9页1整图实际视觉审查','原2818命题3896证据未改；2文907页9647段528图逐行比对只59时间和1图来源字段授权变化','33项Node工程测试通过，串行运行','2857命题全量引用校验0错误','6组语义/来源/条件边界与7组CLI/共享/桌面模块一致，5命题5关联1图逐项核；查询只读哈希不变','240冻结开发题执行，239取证计划通过/240身份通过；g-b05-coincidence前20召回仍失败，未改题或核心排序，见47截断诊断','2857命题/291概念/535关系、Markdown和coverage同版本导出','7条旧待核新增来源但全部保持开放；本批9待核']
 not_run=['冻结前20召回回归尚未修；240完整类别/自然问题基线/生成回答质量/消融对抗未完成，开发计划不冒充完整G','49至61共13课尚未完整语义审读，全书交叉/43混合夹注/数值与图源未全解决','独立Agent实际打包运行与Windows离线/PDF缩放旋转跨页交互未验收']
 evaluation=dict(executable_development_cases=240,target=240,gold_review_status='model_reviewed_development',human_gold_reviewed=False,independent_test_set=False,generated_answers_scored=False,retrieval_plan_passed_on_current_graph=239,source_identity_passed_on_current_graph=240,open_retrieval_regressions=failures,full_stage_g_acceptance_complete=False,new_project_gold_cases_created_in_this_batch=0,note='固定题未改，全部身份通过；一条重合前20召回仍失败，分页找到不算原计划通过。')
 acceptance='48课39命题50证据发布；2857引用及33工程通过，冻结240题239计划/240身份通过，1条召回回归开放，语义及产品目标未完成。'
 next_anchor=next_row[0]+' / lesson-049';next_action='接续49课利润率最大的操作模式，实际PDF355页标题；完整审读固定级别、仓位/资金效率与操作模式范围，保留作者答疑和图源。'
 p=AUDIT/'stage-c-l048-publication.json';pub=read(p);assert pub['graph_version']==VERSION and pub['formal_import']=='passed' and list(pub['batch_sha256'].values())==[sha(AGENT/'curation/upper/c_stage_l048.reviewed.jsonl')]
 pub.update(updated_at=datetime.now(timezone.utc).isoformat(),checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_action=next_action,exports=exports,final_sha256=dict(database=sha(KB/'graph.sqlite'),manifest=sha(KB/'manifest.json')),development_evaluation=evaluation,partial_pending_followups=7,semantic_completion=False,writes_to_knowledge_graph_by_this_finalizer=False);write(p,pub)
 p=AGENT/'curation/progress.json';progress=read(p);assert progress['graph_version'] in ['0.1.0-review-a4f759f80fae',VERSION]
 if progress['graph_version']!=VERSION:progress['previous_checkpoint']={k:progress[k] for k in ['graph_version','completed','next_action','evaluation']}
 outputs=['source-audit/stage-c-l048-'+n+'.json' for n in ['source-plan','source-applied','source-invariants','publication','verification']]+['upper/c_stage_l048.partial-resolutions.jsonl'];progress['machine_outputs']=list(dict.fromkeys(progress['machine_outputs']+outputs))
 progress.update(updated_at=datetime.now(timezone.utc).isoformat(),graph_version=VERSION,counts=counts,claim_status_counts=statuses,figure_origin_counts=figure_status,unit_processing_status_counts=unit_status,semantic_completion=False,completed=['48课130段9页1图完整同模型四轮，39命题50证据12关系支撑、无新概念','4段归4/25收评、55日期空格规范及1后图，原2818命题3896证据未改；全源字/映射/坐标未变','零成本强语明确作者核算/策略观非所有风险无，容量通道/10万10亿示例与翻倍后资金效率、0后特大卖点联查','有效跌破对应三卖不背书读者三根5分收低；两枢可完非必完，盘中级别与43背驰包含界限并存','30操作忍正常5分修正，首修正中枢>5才至少30盘整/二卖，短答不逐项背书B方向与分解点；c强可小转大非必不交新生','三段区间等首段是该例不改单段中枢，3692/3699分别留原字；力度可算未给式不冒物理逃逸定律','2857引用/33工程/6边界/7模块/5图链接检查和同版导出通过；冻结240题239计划/240身份通过，一前20召回回归开放','7旧待核补来源仍开放；95课阅读记录含历史62至64，49至61共13课未完整审读'],pending=['本批9待核见upper/c_stage_l048.pending.jsonl；零成本风险/记账、数值图源、有效站稳、修正首枢实时与力度公式等未解决','49至61共13课未完整语义审读；95课阅读记录不等全书技术抽取或解释统一','冻结g-b05-coincidence前20召回开放；完整G类别/自然查询基线/生成回答/消融对抗、43夹注及全书交叉未完成','独立Agent和Windows实际交付/离线/PDF交互未验收'],checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_resume_anchor=next_anchor,next_action=next_action,coverage_caveat='48课130段9页1图由同一代理四轮，累计95课阅读记录含历史62至64，不称独立复核或全书完成。',evaluation=evaluation,previous_turn_classification='progress：48课39命题50证据发布，2857引用/33工程通过；冻结题239/240且240身份通过，1召回回归开放，全书余13课。');write(p,progress)
 print(json.dumps(dict(graph_version=VERSION,reviewed=2857,development_cases=240,development_passed=239,remaining_lessons=13,next_anchor=next_anchor,semantic_completion=False),ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
