"""Finalize lesson60 and apply the human's knowledge-base-only delivery scope."""
import hashlib,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';AUDIT=Path(__file__).resolve().parent
VERSION='0.1.0-review-bb28763cfcd8'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 scope=read(AGENT/'curation/delivery-scope.json');assert scope['active_deliverable']=='shared_knowledge_base_only'
 db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
 try:
  assert json.loads(db.execute("select value from metadata where key='graph_version'").fetchone()[0])==VERSION
  counts={t:db.execute(f'select count(*) from {t}').fetchone()[0] for t in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']}
  assert counts==dict(documents=2,pages=907,units=110,passages=9647,figures=528,concepts=309,claims=5907,evidence=7092,relations=672,reviews=3338)
  statuses=db.execute('select review_status,count(*) from claims group by review_status order by review_status').fetchall();assert dict(statuses)==dict(pending=2612,rejected=27,reviewed=3268)
  unit_status=db.execute('select processing_status,count(*) from units group by processing_status order by processing_status').fetchall();assert dict(unit_status)['extracted']==1
  figure_status=db.execute('select origin_status,count(*) from figures group by origin_status order by origin_status').fetchall()
  assert db.execute("select count(*) from evidence e join claims c on c.id=e.claim_id where c.review_status='reviewed'").fetchone()[0]==4453
  next_row=db.execute("select id,pdf_page,text from passages where unit_id='lesson-061' order by pdf_page,block_index,id limit 1").fetchone();assert next_row[0]=='volume_1-a53e99c37ca5-p0457-b001'
  known={r[0] for r in db.execute("select id from claims where review_status='reviewed'")}
 finally:db.close()
 assert read(KB/'manifest.json')['graph_version']==VERSION
 inv=read(AUDIT/'stage-c-l060-source-invariants.json');assert inv['pass'] and inv['graph_version']==VERSION and inv['original_reviewed_claims_unchanged']==3242 and inv['original_reviewed_evidence_unchanged']==4422
 verify=read(AUDIT/'stage-c-l060-verification.json');assert verify['pass'] and verify['graph_version']==VERSION and len(verify['checks'])==6 and len(verify['parity'])==7 and verify['intended_figure_links_checked']==dict(claims=13,associations=13,unique_figures=4)
 dev=read(AGENT/'evaluation/stage-g-development-current.results.json');assert dev['graph_version']==VERSION and dev['executable_development_cases']==240 and all(r['source_identity_matches_expected'] for r in dev['observations'])
 failures=[dict(query_id=r['query_id'],missing=r['missing'],queries=r['queries']) for r in dev['observations'] if not r['automatic_retrieval_contract_pass']]
 assert dev['retrieval_plan_contract_passed']==239 and [f['query_id'] for f in failures]==['g-b05-coincidence']
 exports={}
 for name,count in [('claims',3268),('concepts',309),('relations',672)]:
  p=KB/'exports'/f'{name}.jsonl';rows=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()];assert len(rows)==count and all(r['graph_version']==VERSION for r in rows);exports[name]=dict(rows=count,graph_version=VERSION,sha256=sha(p))
 assert VERSION in (KB/'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150] and read(KB/'exports/coverage.json')['graph_version']==VERSION
 pending_ids={json.loads(l)['id'] for l in (AGENT/'curation/upper/c_stage_l059.pending.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()}
 changes=[
 ('upper-l059-c-stage-pending-early-segment-end-vs-later-feature-sequence-gap-flat-boundaries',['45-46-vs43-44-consolidation-all-red-areas-sum','45-46-inner-small-to-large-first-no-new-high-exit-smaller-center'],'60以45—46对43—44全部红柱面积、内部小转大及首次拉起不新高补早期尾段分析；仍非后64/67特征序列精确法替代。'),
 ('upper-l059-c-stage-pending-alternate-decomposition-unfinished-five-third41-trend-conditional',['thirty-operation-ignore46-47-hold-five-up-until-div-or-break','46-55-five-center55-consolidation-not-true-first-buy57-analogy','new-one-expand-five-and46-touch-key-no46-superstrong-five-up-continues'],'60称3404起标准5分上涨并给46—55枢，46不触仍延续；新源后续结构补充不倒写59时点未完成状态，也不证明任意三买必成趋势。'),
 ('upper-l059-c-stage-pending-sell-before-buy-scope-and-stop-rebuy-before-confirmation',['finite-minimum-observed-segment-cost-channel-capacity-flatten-below','not-every-second-sell-act-monthly-or-five-intact-one-center-ignore','large-level-news-break-dont-wait-same-level-intraday-smaller-second','level-usual-space-fast-five-drop50-may-enter-smaller-than-thirty'],'60补成本/通道/容量与被破坏级别，大级已破可较小卖、快速小级足够空间可入；不证所有回补可成交或免成本，也不取消一般原操作级别。')]
 followups=[]
 for pid,slugs,finding in changes:
  ids=['upper-l060-c-stage-'+s for s in slugs];assert pid in pending_ids and all(x in known for x in ids)
  followups.append(dict(pending_id=pid,status='new_source_located_scope_still_pending',new_claim_ids=ids,finding=finding,global_pending_not_closed=True,graph_version=VERSION))
 (AGENT/'curation/upper/c_stage_l060.partial-resolutions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in followups),encoding='utf-8')
 checks=['26命题31证据预检；38段全台账、451至457七页及4整图实际查看','原3242命题4422证据未改；全2文907页9647段528图逐行仅3日期空格/4图元数据授权变化，原字几何映射保持','3268命题全引用0错误、33现有Node测试通过','6边界组、7现有CLI/共享读取一致和13命题13图文关联4图核对通过，查询哈希不变','冻结240题239计划/240来源身份通过，原重合前20召回仍失败，固定题未改','3268命题309概念672关系及Markdown/coverage同版导出','3旧待核补来源仍开放，本批6待核；软件已从交付范围排除']
 not_run=['第61课未完整语义审读，107课阅读记录不等技术全抽取或所有解释统一','43/57混合夹注来源拆分、54长编号答复完整跨页来源关联，以及全书来源/引用/覆盖最终审计未完成','60预期模型/最低可操作级别、55假一买及枢锚点、消息强语/快速空间例外仍有显式待核','冻结召回回归/完整G和自然查询/生成回答评价未完成，作为现有工具限制披露，不伪称独立/人类金标准','最终知识库目录/归档和哈希清单未组装；固定两册未核原博客或历史政策/法规/收益与可成交强语']
 evaluation=dict(executable_development_cases=240,target=240,gold_review_status='model_reviewed_development',human_gold_reviewed=False,independent_test_set=False,generated_answers_scored=False,retrieval_plan_passed_on_current_graph=239,source_identity_passed_on_current_graph=240,open_retrieval_regressions=failures,full_stage_g_acceptance_complete=False,new_project_gold_cases_created_in_this_batch=0,note='固定题和gold未改；重合前20召回仍失败，现有工具评价不冒生成回答/知识本体质量证明。软件已排除。')
 acceptance='60课26命题31证据发布，3268引用/33测试/6边界/7现有读取一致及13图文关联通过，同版本导出；冻结240题239计划/240身份通过。余61课及全书来源和交付审计。'
 next_anchor=next_row[0]+' / lesson-061';next_action='接续61课区间套定位标准图解，PDF457标题；审读60—65/65—67与69/内部力度比较、当下待确认和可能破坏、全页/整图及时间来源。完成后做混合夹注/跨页上下文与全书覆盖、知识库归档哈希交付。'
 p=AUDIT/'stage-c-l060-publication.json';pub=read(p);assert pub['graph_version']==VERSION and pub['formal_import']=='passed' and list(pub['batch_sha256'].values())==[sha(AGENT/'curation/upper/c_stage_l060.reviewed.jsonl')]
 pub.update(updated_at=datetime.now(timezone.utc).isoformat(),checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_action=next_action,exports=exports,final_sha256=dict(database=sha(KB/'graph.sqlite'),manifest=sha(KB/'manifest.json')),development_evaluation=evaluation,partial_pending_followups=len(followups),semantic_completion=False,writes_to_knowledge_graph_by_this_finalizer=False,delivery_scope=scope['active_deliverable'],delivery_scope_file='curation/delivery-scope.json',excluded_software_deliverables=scope['excluded_software_deliverables']);write(p,pub)
 p=AGENT/'curation/progress.json';progress=read(p);assert progress['graph_version'] in ['0.1.0-review-dd5aebdeacd1',VERSION]
 if progress['graph_version']!=VERSION:progress['previous_checkpoint']={k:progress[k] for k in ['graph_version','completed','next_action','evaluation']}
 outputs=['source-audit/stage-c-l060-'+n+'.json' for n in ['source-plan','source-applied','source-invariants','publication','verification']]+['upper/c_stage_l060.partial-resolutions.jsonl'];progress['machine_outputs']=list(dict.fromkeys(progress['machine_outputs']+outputs))
 progress.update(updated_at=datetime.now(timezone.utc).isoformat(),graph_version=VERSION,counts=counts,claim_status_counts=statuses,figure_origin_counts=figure_status,unit_processing_status_counts=unit_status,semantic_completion=False,authorization='用户授权持续构建固定两册知识库；最新明确仅交付知识库，不再构建独立Agent软件包或Windows应用，无额外中途批准关卡。',delivery_scope=scope['active_deliverable'],delivery_scope_file='curation/delivery-scope.json',excluded_software_deliverables=scope['excluded_software_deliverables'],completed=['60课38段7页4整图同代理四轮，26命题31证据13关系支撑，新增走势破坏及11关系','3作者跨页答日期空格及4图2未核2后加修正，原3242命题4422证据和全源原字/几何/映射未改，图4067.85/4068.20分存','预期须外化为交易、B2不低于A1含等号、不预测非不可预测，理论多解非任意画法；每笔理论精度与成本通道容量限制下实际最低线段分别保','最严格45—46全部红面积/小转大与30分忽略46—47分层；55盘背假一买类比57二买、58—61与收评从60起[4224,4254]锚点分存，MACD先回零/新高/面积和高度弱联合','并非每二卖反应，大级已破可较小二卖退出、快速小级空间足够可供原30分者5分入；消息0影响/小概率强语非实证，1分与5分三类点不同、四股形态分别处理','3268引用/33测试/6边界/7现有读取一致及13图文关联通过，同版导出；冻结240题239计划/240身份通过，1回归开放','107课有阅读记录，余61；3旧待核补来源仍开放，本批6待核，最终仅知识库'],pending=not_run,checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_resume_anchor=next_anchor,next_action=next_action,coverage_caveat='60课38段7页4整图同一代理四轮；107课阅读记录非独立复核或技术全抽取，余61及全书来源/交付审计。',evaluation=evaluation,previous_turn_classification='progress：60课26命题31证据发布，3268全引用通过，107课阅读记录，余61；软件已排除。')
 write(p,progress);print(json.dumps(dict(graph_version=VERSION,reviewed=3268,reviewed_evidence=4453,development_cases=240,development_passed=239,remaining_lessons=1,next_anchor=next_anchor,delivery_scope=scope['active_deliverable'],semantic_completion=False),ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
