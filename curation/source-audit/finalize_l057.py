"""Finalize lesson57 and apply the human's knowledge-base-only delivery scope."""
import hashlib,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';AUDIT=Path(__file__).resolve().parent
VERSION='0.1.0-review-63d8b41da992'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 scope=read(AGENT/'curation/delivery-scope.json');assert scope['active_deliverable']=='shared_knowledge_base_only'
 db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
 try:
  assert json.loads(db.execute("select value from metadata where key='graph_version'").fetchone()[0])==VERSION
  counts={t:db.execute(f'select count(*) from {t}').fetchone()[0] for t in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']}
  assert counts==dict(documents=2,pages=907,units=110,passages=9647,figures=528,concepts=307,claims=5818,evidence=6990,relations=641,reviews=3249)
  statuses=db.execute('select review_status,count(*) from claims group by review_status order by review_status').fetchall();assert dict(statuses)==dict(pending=2612,rejected=27,reviewed=3179)
  unit_status=db.execute('select processing_status,count(*) from units group by processing_status order by processing_status').fetchall();assert dict(unit_status)['extracted']==4
  figure_status=db.execute('select origin_status,count(*) from figures group by origin_status order by origin_status').fetchall()
  assert db.execute("select count(*) from evidence e join claims c on c.id=e.claim_id where c.review_status='reviewed'").fetchone()[0]==4351
  next_row=db.execute("select id,pdf_page,text from passages where unit_id='lesson-058' order by pdf_page,block_index,id limit 1").fetchone();assert next_row[0]=='volume_1-a53e99c37ca5-p0436-b003'
  known={r[0] for r in db.execute("select id from claims where review_status='reviewed'")}
 finally:db.close()
 assert read(KB/'manifest.json')['graph_version']==VERSION
 inv=read(AUDIT/'stage-c-l057-source-invariants.json');assert inv['pass'] and inv['graph_version']==VERSION and inv['original_reviewed_claims_unchanged']==3144 and inv['original_reviewed_evidence_unchanged']==4311
 verify=read(AUDIT/'stage-c-l057-verification.json');assert verify['pass'] and verify['graph_version']==VERSION and len(verify['checks'])==6 and len(verify['parity'])==7 and verify['intended_figure_links_checked']==dict(claims=11,associations=11,unique_figures=5)
 assert verify['mixed_annotation_status']['source_search_context_still_mixed'] and not verify['mixed_annotation_status']['source_span_split_complete']
 dev=read(AGENT/'evaluation/stage-g-development-current.results.json');assert dev['graph_version']==VERSION and dev['executable_development_cases']==240 and all(r['source_identity_matches_expected'] for r in dev['observations'])
 failures=[dict(query_id=r['query_id'],missing=r['missing'],queries=r['queries']) for r in dev['observations'] if not r['automatic_retrieval_contract_pass']]
 assert dev['retrieval_plan_contract_passed']==239 and [f['query_id'] for f in failures]==['g-b05-coincidence']
 exports={}
 for name,count in [('claims',3179),('concepts',307),('relations',641)]:
  p=KB/'exports'/f'{name}.jsonl';rows=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()];assert len(rows)==count and all(r['graph_version']==VERSION for r in rows);exports[name]=dict(rows=count,graph_version=VERSION,sha256=sha(p))
 assert VERSION in (KB/'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150] and read(KB/'exports/coverage.json')['graph_version']==VERSION
 pending_ids={json.loads(l)['id'] for n in [50,55,56] for l in (AGENT/'curation/upper'/f'c_stage_l{n:03d}.pending.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()}
 changes=[
 ('upper-l056-c-stage-pending-lowest-view-consistency-incomplete-B-centers-and-dozens-bars',['minimum-analysis-view-three-subsegments-overlap-not-final-segment-definition','gap01-and-complex23-real-levels-differ-coarse-one-view-same-lines','precise45-leave56-retest-sublevel-not-all-below-one-4077-third-sell'],'57分粗最低观察与精确直接次级；弱段另一标准须全图统一，尚无通用量化阈值或几十K最小值。'),
 ('upper-l056-c-stage-pending-ABC-one-center-and-C-first-new-five-center-alternate-boundary',['at6-alternate-center345456-23-vs67-oscillation-return-near','if7-first-buy-9-second-no-low-or-consolidation-divergence','ten-lines-group-nine-after-gap-five-center4015-4122'],'57给另一34/45/56枢及如果7一买9二买、缺口后九段三组5分4015-4122；另一枢未给数值，不移植原边界或认定读者另区间获批。'),
 ('upper-l050-c-stage-pending-MACD-period-linearity-sensitivity-and-missing-formula',['fine56-up-up-area-divergence-needs-skill-reaction-channel','67-down-up-down-later-weaker-time-for-space-zero-green-retrace'],'57细56面积需技艺/反应/通道，67时长长而幅小、绿柱回零不应忽略；绿柱零不等黄白线零，未补线性/敏感性公式。')]
 followups=[]
 for pid,slugs,finding in changes:
  ids=['upper-l057-c-stage-'+s for s in slugs];assert pid in pending_ids and all(x in known for x in ids)
  followups.append(dict(pending_id=pid,status='new_source_located_scope_still_pending',new_claim_ids=ids,finding=finding,global_pending_not_closed=True,graph_version=VERSION))
 (AGENT/'curation/upper/c_stage_l057.partial-resolutions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in followups),encoding='utf-8')
 checks=['35条命题40证据Schema/引用/身份/映射/坐标预检；66段台账、PDF427至436十页和5幅整图实际视觉核对','原3144命题4311证据未改；全2文907页9647段528图仅23段身份/时间与5图来源元数据授权变化','33项现有Node测试及3179命题全量引用检查通过、0错误','6组语义/来源边界和7组现有查询模块一致，11命题11图文关联5图逐项核，查询只读哈希不变','冻结240题239取证计划/240来源身份通过，重合前20召回仍失败，原题和排序未改','3179命题/307概念/641关系及Markdown/coverage同版本导出','3旧待核补来源仍开放，本批8待核；432未核备注不入作者引文但原段混合未拆','按直接用户指令将最终范围设为知识库，软件构建/打包和交互验收从交付门槛移除']
 not_run=['58至61共4课未完整语义审读；104课有阅读记录不等技术全抽取或解释统一','43与57混合夹注仍需来源拆分；54编号短答需完整跨页上下文来源关联，当前接口未自动全纳','全书最终来源/引文/覆盖和交付文件哈希审计未完成，尚未组装最终知识库交付目录','冻结前20召回回归及完整G/自然查询基线/生成回答/消融对抗未完成，保留为现有工具限制，不伪称知识库问答金标准','同一代理四轮复核非独立/人类金标准；未核原博客、未外证作者历史预测或强收益/执行保证']
 evaluation=dict(executable_development_cases=240,target=240,gold_review_status='model_reviewed_development',human_gold_reviewed=False,independent_test_set=False,generated_answers_scored=False,retrieval_plan_passed_on_current_graph=239,source_identity_passed_on_current_graph=240,open_retrieval_regressions=failures,full_stage_g_acceptance_complete=False,new_project_gold_cases_created_in_this_batch=0,note='固定题未改；一条重合前20召回仍失败。软件已排除，现有检索评价仍如实披露，不冒知识本体或生成回答质量证明。')
 acceptance='57课35命题40证据发布；3179引用/33测试/6边界/7现有模块及11图文关联检查通过，冻结240题239计划/240身份通过。知识库余4课及全书来源/交付审计；软件不再构建或作为验收门槛。'
 next_anchor=next_row[0]+' / lesson-058';next_action='接续第58课图解分析示范三，PDF436页标题；逐段及整图核对底分型/笔/线段前后定义、当下分解、原字与日期，保留后加图和未核解释边界。最终仅交付知识库。'
 p=AUDIT/'stage-c-l057-publication.json';pub=read(p)
 assert pub['graph_version']==VERSION and pub['formal_import']=='passed' and list(pub['batch_sha256'].values())==[sha(AGENT/'curation/upper/c_stage_l057.reviewed.jsonl')]
 pub.update(updated_at=datetime.now(timezone.utc).isoformat(),checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_action=next_action,exports=exports,final_sha256=dict(database=sha(KB/'graph.sqlite'),manifest=sha(KB/'manifest.json')),development_evaluation=evaluation,partial_pending_followups=len(followups),semantic_completion=False,writes_to_knowledge_graph_by_this_finalizer=False,delivery_scope=scope['active_deliverable'],delivery_scope_file='curation/delivery-scope.json',excluded_software_deliverables=scope['excluded_software_deliverables']);write(p,pub)
 p=AGENT/'curation/progress.json';progress=read(p);assert progress['graph_version'] in ['0.1.0-review-f3668c6fc5ca',VERSION]
 if progress['graph_version']!=VERSION:progress['previous_checkpoint']={k:progress[k] for k in ['graph_version','completed','next_action','evaluation']}
 outputs=['source-audit/stage-c-l057-'+n+'.json' for n in ['source-plan','source-applied','source-invariants','publication','verification']]+['upper/c_stage_l057.partial-resolutions.jsonl','delivery-scope.json'];progress['machine_outputs']=list(dict.fromkeys(progress['machine_outputs']+outputs))
 progress.update(updated_at=datetime.now(timezone.utc).isoformat(),graph_version=VERSION,counts=counts,claim_status_counts=statuses,figure_origin_counts=figure_status,unit_processing_status_counts=unit_status,semantic_completion=False,delivery_scope=scope['active_deliverable'],delivery_scope_file='curation/delivery-scope.json',excluded_software_deliverables=scope['excluded_software_deliverables'],
 completed=['57课66段10页5整图同模型四轮，35命题40证据15关系支撑，新增时间换空间及13关系','11段独立6/4文章身份/仅日期修复、2尾头新时点和10日期空格规范；3图未核2图后加，保全原字/几何/映射','粗最低观察/精直接次级及全图弱段标准分层；56面积需技艺反应通道，67幅小时长换空间/绿柱回零不等黄白线零','另一34/45/56枢无新数值不套旧边界；若7一买则9二买、不新低或盘背和更低内部点保留，缺口后九段三组5分4015-4122','T+1等买点分批、半仓或技好且资小可全出；30分持有10至100000为理想例、反弹40/20不证必回本，原5月均线/图文价差不静修','432未核备注避开作者引文但来源段仍混合，3旧待核补来源仍开放；本批8待核','3179引用/33测试/6边界/7现有模块/11图文关联通过，同版本导出；冻结240题239计划/240身份通过，1召回回归开放','104课有阅读记录含先前62至64，58至61共4课待完整审读；最终交付依最新用户指令仅保留知识库'],
 pending=not_run,checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_resume_anchor=next_anchor,next_action=next_action,coverage_caveat='57课66段10页5整图由同一代理四轮，累计104课阅读记录，不称独立复核或全书完成；知识库允许显式未决解释，但来源混合必须明确处理。',evaluation=evaluation,previous_turn_classification='progress：57课35命题40证据发布并完成全引用和同版本导出，剩4课；按新指令移除所有后续软件交付门槛。')
 write(p,progress)
 print(json.dumps(dict(graph_version=VERSION,reviewed=3179,reviewed_evidence=4351,development_cases=240,development_passed=239,remaining_lessons=4,next_anchor=next_anchor,delivery_scope=scope['active_deliverable'],semantic_completion=False),ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
