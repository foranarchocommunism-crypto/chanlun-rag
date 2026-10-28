"""Finalize lesson55 checked publication without mutating the graph."""
import hashlib,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';AUDIT=Path(__file__).resolve().parent;VERSION='0.1.0-review-1faa97315b10'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
 try:
  assert json.loads(db.execute("select value from metadata where key='graph_version'").fetchone()[0])==VERSION
  counts={t:db.execute(f'select count(*) from {t}').fetchone()[0] for t in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']};assert counts==dict(documents=2,pages=907,units=110,passages=9647,figures=528,concepts=304,claims=5755,evidence=6915,relations=619,reviews=3186)
  statuses=db.execute('select review_status,count(*) from claims group by review_status order by review_status').fetchall();assert dict(statuses)==dict(pending=2612,rejected=27,reviewed=3116)
  unit_status=db.execute('select processing_status,count(*) from units group by processing_status order by processing_status').fetchall();assert dict(unit_status)['extracted']==6
  figure_status=db.execute('select origin_status,count(*) from figures group by origin_status order by origin_status').fetchall()
  assert db.execute("select count(*) from evidence e join claims c on c.id=e.claim_id where c.review_status='reviewed'").fetchone()[0]==4276
  next_row=db.execute("select id,pdf_page,text from passages where unit_id='lesson-056' order by pdf_page,block_index,id limit 1").fetchone();assert next_row[0]=='volume_1-a53e99c37ca5-p0422-b004'
  known={r[0] for r in db.execute("select id from claims where review_status='reviewed'")}
 finally:db.close()
 assert read(KB/'manifest.json')['graph_version']==VERSION
 inv=read(AUDIT/'stage-c-l055-source-invariants.json');assert inv['pass'] and inv['graph_version']==VERSION and inv['original_reviewed_claims_unchanged']==3077 and inv['original_reviewed_evidence_unchanged']==4233
 verify=read(AUDIT/'stage-c-l055-verification.json');assert verify['pass'] and verify['graph_version']==VERSION and len(verify['checks'])==6 and len(verify['parity'])==7 and verify['intended_figure_links_checked']==dict(claims=5,associations=5,unique_figures=3)
 dev=read(AGENT/'evaluation/stage-g-development-current.results.json');assert dev['graph_version']==VERSION and dev['executable_development_cases']==240 and all(r['source_identity_matches_expected'] for r in dev['observations'])
 failures=[dict(query_id=r['query_id'],missing=r['missing'],queries=r['queries']) for r in dev['observations'] if not r['automatic_retrieval_contract_pass']];assert dev['retrieval_plan_contract_passed']==239 and [f['query_id'] for f in failures]==['g-b05-coincidence']
 exports={}
 for name,count in [('claims',3116),('concepts',304),('relations',619)]:
  p=KB/'exports'/f'{name}.jsonl';rows=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()];assert len(rows)==count and all(r['graph_version']==VERSION for r in rows);exports[name]=dict(rows=count,graph_version=VERSION,sha256=sha(p))
 assert VERSION in (KB/'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150] and read(KB/'exports/coverage.json')['graph_version']==VERSION
 pending_ids={json.loads(l)['id'] for n in [49,50,53,54] for l in (AGENT/'curation/upper'/f'c_stage_l{n:03d}.pending.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()}
 changes=[
 ('upper-l054-c-stage-pending-two-decompositions-whole-submove-extrema-and-g7-labels',['association-A-still-center-B-complete-subtype-retest-complete-third','two-decomposition-MACD-comparisons-author-approval-d4-both-divergence','decomposition-strength-disagreement-only-valid-minimum-return-not-both'],'55要求A原级中枢仍成立/B及回试完整次级，认可读者两比较本例d4同背；若后段力度居前两段中间可不一致，只保证满足成立解最低幅度，不保证所有解目标；54公式端点/完成点/子枢措辞仍待核。'),
 ('upper-l054-c-stage-pending-numbered-replies-rare-inverted-second-and-no-larger-level',['association-A-still-center-B-complete-subtype-retest-complete-third','two-decomposition-MACD-comparisons-author-approval-d4-both-divergence','decomposition-strength-disagreement-only-valid-minimum-return-not-both'],'55对A+B和回试完成、双解比较提供新明说，但没有直接解决54编号2没有什么更大级别的比较基准或53无限时间/等高等证明；跨页编号context限制仍未修。'),
 ('upper-l054-c-stage-pending-third-point-followthrough-vs-trend-possibility-fast-break-and-extreme-range',['retail-daily-or-above-can-wait-second-or-third-buy','association-A-still-center-B-complete-subtype-retest-complete-third','five-third-buy-cannot-offset-thirty-top-daily-author-conditional-answer'],'55再要求离返完整次级，散户较大级可三买但5分三买斗不过30分顶背驰、日线没问题保作者强语；并未证明三类后必成趋势/免跌停或快速突破所有实时确认。'),
 ('upper-l053-c-stage-pending-small-level-skill-channel-capacity-and-absolute-profit-wording',['capital-channel-time-decide-own-style-level-not-small-fund-total-ban','increased-costs-minimum-five-even-thirty-plus-level','may29-fix-level-small-top-three-wave-retest-rebuy-skilled-only'],'55资金通道时间定风格/级别，交易成本升后至少5甚至30以上，极短操作不熟仍看5日线；不是所有普通人固定同一理论最低层，未证100%/任何事件实际收益。'),
 ('upper-l049-c-stage-pending-guaranteed-chip-safety-full-position-and-skill-execution',['profits-for-family-gradual-principal-consumption-withdrawal','withdraw-principal-not-clear-all-cash-safety-first','unexpected-events-position-cost-control-zero-cost-tool-author','low-held-profit-zero-cost-can-use-second-third-exit-author-claim','may30-miss-first-second-sell-0947-author-not-guaranteed-fill'],'55提本金消费款非清仓/永不空仓，零成本/二卖不会错过为作者账户或模型强语；原本金退出不等盈利筹码市值/流动性风险消失，T+1/跌停/通道容量并未实证可成交。'),
 ('upper-l050-c-stage-pending-logic-confidence-geometric-guarantee-and-practice-criteria',['cash-chip-exchange-asymmetric-time-irreversible-nominal-money','good-base-entry-cost-below-area-rise-cost-only-decreases-author-ideal','calm-unexpected-event-long-run-habits-not-one-outcome-victory'],'55以名义现金/时间不可逆解释买卖非同构，理想建仓成本与长期习惯是作者框架；未给50几何盈利证明、模拟实践达标样本或独立实绩评价，修辞不补成科学证据。'),
 ]
 followups=[]
 for pid,slugs,finding in changes:
  ids=['upper-l055-c-stage-'+s for s in slugs];assert pid in pending_ids and all(x in known for x in ids)
  followups.append(dict(pending_id=pid,status='new_source_located_scope_still_pending',new_claim_ids=ids,finding=finding,global_pending_not_closed=True,graph_version=VERSION))
 (AGENT/'curation/upper/c_stage_l055.partial-resolutions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in followups),encoding='utf-8')
 checks=['39条Schema/引用/身份/映射/坐标预检，107段台账、PDF412至422十一页及3幅整图实际视觉核对，419原页长上阴保原字','原3077命题4233证据未改；2文907页9647段528图逐行仅21时间空格和3图来源备注授权变化，原字/几何/映射不动','33项Node工程测试全部通过，测试终止后运行全量引用检查','3116命题全量引用校验0错误','6组语义/来源/条件/作者对的短答指代与7组CLI/共享/桌面模块一致，5命题5图文关联3图逐项核且全后加，查询只读哈希不变','冻结240题执行239取证计划/240来源身份通过，重合前20召回仍失败，原题/核心排序未改','3116命题/304概念/619关系及Markdown/coverage同版本导出','6旧待核补来源仍开放，本批8待核；09:47/下课9点48原时点、长上阴原字和图1249/1429/5月8日起点差均保留']
 not_run=['冻结前20召回回归未修，完整G类别/自然查询基线/生成回答/消融对抗未完成','56至61共6课未完整语义审读；09:47/9点48、54公式/连接/短答与53/52原字、43混合夹注和全书跨课/图文尚待核','54编号短答完整跨页问题未自动全部纳入邻段context；当前条件/备注给联读源ID和原页，不宣称该接口限制已修','0成本/二卖不会错过/日线没问题和作者宏观/法律/自述未外证，固定两册不宣称原博客或当前金融法律核实','独立Agent打包真实执行及Windows离线/PDF缩放旋转跨页交互未验收']
 evaluation=dict(executable_development_cases=240,target=240,gold_review_status='model_reviewed_development',human_gold_reviewed=False,independent_test_set=False,generated_answers_scored=False,retrieval_plan_passed_on_current_graph=239,source_identity_passed_on_current_graph=240,open_retrieval_regressions=failures,full_stage_g_acceptance_complete=False,new_project_gold_cases_created_in_this_batch=0,note='固定题未改，全部身份通过；一条重合前20召回仍失败，分页找到不算原计划通过。')
 acceptance='55课39命题43证据发布；3116引用/33工程/6边界/7模块和5图文关联检查通过，冻结240题239计划/240身份通过，1召回回归开放；完整语义及产品目标未完成。'
 next_anchor=next_row[0]+' / lesson-056';next_action='接续56课530印花税当日行情图解，实际PDF422页标题；完整审读突发事件二三卖、个股/指数与缺口最低级、完成段/未成中枢，核本课所有原页/整图并对照55三后加图范围及09:47/56 9点48，保真实执行和跨课边界。'
 p=AUDIT/'stage-c-l055-publication.json';pub=read(p)
 assert pub['graph_version']==VERSION and pub['formal_import']=='passed' and list(pub['batch_sha256'].values())==[sha(AGENT/'curation/upper/c_stage_l055.reviewed.jsonl')]
 pub.update(updated_at=datetime.now(timezone.utc).isoformat(),checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_action=next_action,exports=exports,final_sha256=dict(database=sha(KB/'graph.sqlite'),manifest=sha(KB/'manifest.json')),development_evaluation=evaluation,partial_pending_followups=len(followups),semantic_completion=False,writes_to_knowledge_graph_by_this_finalizer=False);write(p,pub)
 p=AGENT/'curation/progress.json';progress=read(p);assert progress['graph_version'] in ['0.1.0-review-6c88a992da52',VERSION]
 if progress['graph_version']!=VERSION:progress['previous_checkpoint']={k:progress[k] for k in ['graph_version','completed','next_action','evaluation']}
 outputs=['source-audit/stage-c-l055-'+n+'.json' for n in ['source-plan','source-applied','source-invariants','publication','verification']]+['upper/c_stage_l055.partial-resolutions.jsonl'];progress['machine_outputs']=list(dict.fromkeys(progress['machine_outputs']+outputs))
 progress.update(updated_at=datetime.now(timezone.utc).isoformat(),graph_version=VERSION,counts=counts,claim_status_counts=statuses,figure_origin_counts=figure_status,unit_processing_status_counts=unit_status,semantic_completion=False,
 completed=['55课107段11页3整图同模型四轮，39命题43证据15关系支撑，新增股性/本金提取两概念及13关系','21时间空格/3后加图元数据规范，原3077命题4233证据及全源原字/几何/映射未改；两30分图含6/4、日线选5/30实含7月，图1249/原模型1429、图框5/9/文5/8分别保','买卖非同构限名义现金/时间模型、成人同构修辞非生理学证明；散户可二三买与规模/训练至少二买入点分开，股性频幅复杂度无固定参数/建仓降本非自动市场保证','A仍原级中枢/B及回试完整次级，作者对的认可紧前读者两解比较本例d4同背，但两解可能不一致，只可满足成立解最低回抽目标，不补统一+1索引','资金通道时间定个体级别，技术允许才回补非追高；逐步提本金消费款非清仓非永不空仓，日线/30分/5分处理及0成本/二卖不会错过/日线没问题强语保范围和执行限制','09:47与下一课9点48分开，原长上阴整页核不修，至少3月确认和至少3月影响不同，3模式未定/理想5-7月未必；宏观唯一因果、草案/账户70-5-25/3之3仅作者历史观点自述','3116引用/33工程/6边界/7模块及5图文关联通过并同版本导出；冻结240题239计划/240身份通过，1前20召回回归开放','6旧待核补来源仍开放，本批8待核；102课阅读记录含历史62至64，56至61共6课未完整审读'],
 pending=['本批8待核见upper/c_stage_l055.pending.jsonl：名义模型/修辞与股性、建仓降本理想、A/B完成及两解回抽、技术回补/本金非清仓、执行绝对强语、时点/3后图、确认时间窗与历史政策自述','56至61共6课未完整语义审读，102课阅读记录不等技术全抽取或解释统一','54编号短答完整跨页问题未自动纳邻段context；重合前20召回回归、完整G类别/自然基线/生成回答/消融对抗及43夹注/全书交叉未完成','独立Agent与Windows真实交付、离线/PDF交互未验收'],checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_resume_anchor=next_anchor,next_action=next_action,coverage_caveat='55课107段11页3整图由同一代理四轮，累计102课阅读记录含历史62至64，不称独立复核或全书完成。',evaluation=evaluation,previous_turn_classification='progress：55课39命题43证据发布，3116引用/33工程与6边界7模块5图文关联通过；冻结题239/240且240身份通过，1召回回归开放，全书余6课。')
 write(p,progress)
 print(json.dumps(dict(graph_version=VERSION,reviewed=3116,reviewed_evidence=4276,development_cases=240,development_passed=239,remaining_lessons=6,next_anchor=next_anchor,semantic_completion=False),ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
