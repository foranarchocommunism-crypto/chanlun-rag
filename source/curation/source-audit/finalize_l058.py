"""Finalize lesson58 and apply the human's knowledge-base-only delivery scope."""
import hashlib,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';AUDIT=Path(__file__).resolve().parent
VERSION='0.1.0-review-60afc026a0f3'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 scope=read(AGENT/'curation/delivery-scope.json');assert scope['active_deliverable']=='shared_knowledge_base_only'
 db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
 try:
  assert json.loads(db.execute("select value from metadata where key='graph_version'").fetchone()[0])==VERSION
  counts={t:db.execute(f'select count(*) from {t}').fetchone()[0] for t in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']}
  assert counts==dict(documents=2,pages=907,units=110,passages=9647,figures=528,concepts=308,claims=5853,evidence=7029,relations=651,reviews=3284)
  statuses=db.execute('select review_status,count(*) from claims group by review_status order by review_status').fetchall();assert dict(statuses)==dict(pending=2612,rejected=27,reviewed=3214)
  unit_status=db.execute('select processing_status,count(*) from units group by processing_status order by processing_status').fetchall();assert dict(unit_status)['extracted']==3
  figure_status=db.execute('select origin_status,count(*) from figures group by origin_status order by origin_status').fetchall()
  assert db.execute("select count(*) from evidence e join claims c on c.id=e.claim_id where c.review_status='reviewed'").fetchone()[0]==4390
  next_row=db.execute("select id,pdf_page,text from passages where unit_id='lesson-059' order by pdf_page,block_index,id limit 1").fetchone();assert next_row[0]=='volume_1-a53e99c37ca5-p0443-b010'
  known={r[0] for r in db.execute("select id from claims where review_status='reviewed'")}
 finally:db.close()
 assert read(KB/'manifest.json')['graph_version']==VERSION
 inv=read(AUDIT/'stage-c-l058-source-invariants.json');assert inv['pass'] and inv['graph_version']==VERSION and inv['original_reviewed_claims_unchanged']==3179 and inv['original_reviewed_evidence_unchanged']==4351
 verify=read(AUDIT/'stage-c-l058-verification.json');assert verify['pass'] and verify['graph_version']==VERSION and len(verify['checks'])==6 and len(verify['parity'])==7 and verify['intended_figure_links_checked']==dict(claims=16,associations=16,unique_figures=4)
 dev=read(AGENT/'evaluation/stage-g-development-current.results.json');assert dev['graph_version']==VERSION and dev['executable_development_cases']==240 and all(r['source_identity_matches_expected'] for r in dev['observations'])
 failures=[dict(query_id=r['query_id'],missing=r['missing'],queries=r['queries']) for r in dev['observations'] if not r['automatic_retrieval_contract_pass']]
 assert dev['retrieval_plan_contract_passed']==239 and [f['query_id'] for f in failures]==['g-b05-coincidence']
 exports={}
 for name,count in [('claims',3214),('concepts',308),('relations',651)]:
  p=KB/'exports'/f'{name}.jsonl';rows=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()];assert len(rows)==count and all(r['graph_version']==VERSION for r in rows);exports[name]=dict(rows=count,graph_version=VERSION,sha256=sha(p))
 assert VERSION in (KB/'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150] and read(KB/'exports/coverage.json')['graph_version']==VERSION
 pending_ids={json.loads(l)['id'] for l in (AGENT/'curation/upper/c_stage_l057.pending.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()}
 changes=[
 ('upper-l057-c-stage-pending-coarse-view-precise-sublevel-and-weak-line-standards',['inner-five-fold-no-overlap-whole14-15-one-segment','preprecise-three-fold-gap-exception-nonoverlap-can-extend','chart-period-not-move-level-one-chart-can-find-daily-center','objective-move-level-subjective-chart-magnification'],'58给早期三折/缺口例外和不重合延伸、图周期不等走势级别；不自动替代后62/67精确定义，弱段阈值仍无统一量化算法。'),
 ('upper-l057-c-stage-pending-alternate-centers-if7-first-grouped-five-and-return-near',['15-16-third-sell-recent10-13-not-point7','old1-10-five-center-rebound-not-back-above4015-third-sell','point7-larger-five-divergence-return-improvement-only-possible'],'58说明15—16对最近10—13一分枢，不能用点7偷换；7在5分背驰回升有意义，旧5分1—10的4015边界和另一枢范围各自保，未补57全部弱段/分解歧义。'),
 ('upper-l057-c-stage-pending-historical-support-five-month-wording-body-vs-figure-prices',['jun5-monthly-five-average-intraday-false-break3434','jun5-17-end3404-18-still-watch-ending-center-oscillation'],'58于6/5明确原月线的5均线，补后续文字线索而不静改57原5月均线或用来源未核备注推定早段；正文3404与图3404.25继续分存。')]
 followups=[]
 for pid,slugs,finding in changes:
  ids=['upper-l058-c-stage-'+s for s in slugs];assert pid in pending_ids and all(x in known for x in ids)
  followups.append(dict(pending_id=pid,status='new_source_located_scope_still_pending',new_claim_ids=ids,finding=finding,global_pending_not_closed=True,graph_version=VERSION))
 (AGENT/'curation/upper/c_stage_l058.partial-resolutions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in followups),encoding='utf-8')
 checks=['35命题39证据Schema/引用/身份/原文映射/坐标预检，72段台账及PDF436至443八整页和4整图实际查看','原3179命题4351证据未改；2文907页9647段528图逐行比对，仅25段角色/日期及4图来源元数据授权变化','3214已复核命题全引用检查0错误，33项现有Node测试全部通过','6来源/条件边界组、7组现有CLI/共享读取一致、16命题16关联4图逐项检查通过，查询数据库/manifest哈希不变','冻结240题239取证计划/240来源身份通过，原重合前20召回仍失败，原题/排序未改','3214命题308概念651关系及Markdown/coverage同版本导出','3旧待核补来源仍开放、本批7待核；软件已依最新用户指令从交付和验收要求移除']
 not_run=['59至61共3课未完整语义审读，105课阅读记录不等技术全抽取或全部解释统一','43/57混合备注须来源拆分，54长编号短答需完整跨页上下文来源关联；全书来源/证据/覆盖最终审计未完成','冻结前20召回回归及完整G/自然查询/生成回答/消融对抗未完成，作为现有工具评价限制披露','固定两册未核原博客；同一代理四轮非独立或人类金标准，作者历史政策/PE收益/房价和可成交强语未外证','最终知识库目录/归档和哈希交付清单尚未组装']
 evaluation=dict(executable_development_cases=240,target=240,gold_review_status='model_reviewed_development',human_gold_reviewed=False,independent_test_set=False,generated_answers_scored=False,retrieval_plan_passed_on_current_graph=239,source_identity_passed_on_current_graph=240,open_retrieval_regressions=failures,full_stage_g_acceptance_complete=False,new_project_gold_cases_created_in_this_batch=0,note='固定题和gold未改，一条重合前20召回仍失败；软件已排除，现有评价不冒知识本体/生成回答质量证明。')
 acceptance='58课35命题39证据发布，3214引用/33测试/6边界/7现有读取一致和16图文关联通过，同版本导出；冻结240题239计划/240身份通过。知识库余3课及全书来源/交付审计，软件不再构建。'
 next_anchor=next_row[0]+' / lesson-059';next_action='接续59课图解分析示范四，PDF443标题；核线段延伸/中枢层次与17至18/后续示范、编号/均线/完整与进行中、全原页及整图，不以图周期替代走势级别。最终仅交付知识库。'
 p=AUDIT/'stage-c-l058-publication.json';pub=read(p)
 assert pub['graph_version']==VERSION and pub['formal_import']=='passed' and list(pub['batch_sha256'].values())==[sha(AGENT/'curation/upper/c_stage_l058.reviewed.jsonl')]
 pub.update(updated_at=datetime.now(timezone.utc).isoformat(),checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_action=next_action,exports=exports,final_sha256=dict(database=sha(KB/'graph.sqlite'),manifest=sha(KB/'manifest.json')),development_evaluation=evaluation,partial_pending_followups=len(followups),semantic_completion=False,writes_to_knowledge_graph_by_this_finalizer=False,delivery_scope=scope['active_deliverable'],delivery_scope_file='curation/delivery-scope.json',excluded_software_deliverables=scope['excluded_software_deliverables']);write(p,pub)
 p=AGENT/'curation/progress.json';progress=read(p);assert progress['graph_version'] in ['0.1.0-review-63d8b41da992',VERSION]
 if progress['graph_version']!=VERSION:progress['previous_checkpoint']={k:progress[k] for k in ['graph_version','completed','next_action','evaluation']}
 outputs=['source-audit/stage-c-l058-'+n+'.json' for n in ['source-plan','source-applied','source-invariants','publication','verification']]+['upper/c_stage_l058.partial-resolutions.jsonl'];progress['machine_outputs']=list(dict.fromkeys(progress['machine_outputs']+outputs))
 progress.update(updated_at=datetime.now(timezone.utc).isoformat(),graph_version=VERSION,counts=counts,claim_status_counts=statuses,figure_origin_counts=figure_status,unit_processing_status_counts=unit_status,semantic_completion=False,delivery_scope=scope['active_deliverable'],delivery_scope_file='curation/delivery-scope.json',excluded_software_deliverables=scope['excluded_software_deliverables'],
 completed=['58课72段8页4整图同模型四轮，35命题39证据15关系支撑，新增私人股权投资及10关系','25段来源角色/日期与4图2未核2后加修正，5误reader还原作者；6/6、6/7、6/8和6/13各自定位，原3179命题4351证据及全源原字/几何/映射不动','14—15内五折不单独分段而全段仍一段，原三折/缺口例外不覆盖后62/67；MACD黄白力度与最小绿面积分开，原24/52/9和重绘12/26/9不合并','最近10—13一分枢三卖不借点7；次级离返保留，从16可能背驰可被次日加速破坏，区间套确认后才回15成至少一分枢','旧1—10五分4015边界与4000概略强语、7更大层好转条件分开；从10新五分尚未形成，6/7大枢正在形成不冒完成','图周期/显微镜选择与客观走势级别不同，1分钟图可找日线枢；费用和技能决定微小盘背是否值得做，中线等点/PE/星号股/房产和政策强语保历史边界','3214引用/33测试/6边界/7现有读取一致及16图文关联通过，同版导出；冻结240题239计划/240身份通过，1回归开放','105课有阅读记录，剩59至61三课；3旧待核补来源仍开放，本批7待核，知识库交付范围已固定'],
 pending=not_run,checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_resume_anchor=next_anchor,next_action=next_action,coverage_caveat='58课72段8页4整图由同一代理四轮，累计105课阅读记录含先前62至64，不称独立复核或全书已完成。软件已明确排除；来源归属和最终知识库交付仍需完成。',evaluation=evaluation,previous_turn_classification='progress：57/58两课共70命题79证据发布，当前3214命题全引用通过，已完成105课阅读记录，余3课；最新用户指令仅交付知识库。')
 write(p,progress)
 print(json.dumps(dict(graph_version=VERSION,reviewed=3214,reviewed_evidence=4390,development_cases=240,development_passed=239,remaining_lessons=3,next_anchor=next_anchor,delivery_scope=scope['active_deliverable'],semantic_completion=False),ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
