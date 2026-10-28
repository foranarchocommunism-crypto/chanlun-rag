"""Finalize lesson52 checked publication without mutating the graph."""
import hashlib,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';AUDIT=Path(__file__).resolve().parent;VERSION='0.1.0-review-58e2535c21e3'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
 try:
  assert json.loads(db.execute("select value from metadata where key='graph_version'").fetchone()[0])==VERSION
  counts={t:db.execute(f'select count(*) from {t}').fetchone()[0] for t in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']};assert counts==dict(documents=2,pages=907,units=110,passages=9647,figures=528,concepts=301,claims=5645,evidence=6780,relations=580,reviews=3076)
  statuses=db.execute('select review_status,count(*) from claims group by review_status order by review_status').fetchall();assert dict(statuses)==dict(pending=2612,rejected=27,reviewed=3006)
  unit_status=db.execute('select processing_status,count(*) from units group by processing_status order by processing_status').fetchall();assert dict(unit_status)['extracted']==9
  figure_status=db.execute('select origin_status,count(*) from figures group by origin_status order by origin_status').fetchall()
  assert db.execute("select count(*) from evidence e join claims c on c.id=e.claim_id where c.review_status='reviewed'").fetchone()[0]==4141
  next_row=db.execute("select id,pdf_page,text from passages where unit_id='lesson-053' order by pdf_page,block_index,id limit 1").fetchone();assert next_row[0]=='volume_1-a53e99c37ca5-p0396-b011'
  known={r[0] for r in db.execute("select id from claims where review_status='reviewed'")}
 finally:db.close()
 assert read(KB/'manifest.json')['graph_version']==VERSION
 inv=read(AUDIT/'stage-c-l052-source-invariants.json');assert inv['pass'] and inv['graph_version']==VERSION and inv['original_reviewed_claims_unchanged']==2967 and inv['original_reviewed_evidence_unchanged']==4091
 verify=read(AUDIT/'stage-c-l052-verification.json');assert verify['pass'] and verify['graph_version']==VERSION and len(verify['checks'])==6 and len(verify['parity'])==7 and verify['intended_figure_links_checked']==dict(claims=7,associations=11,unique_figures=7,reader_context_figures_not_author_evidence=3)
 dev=read(AGENT/'evaluation/stage-g-development-current.results.json');assert dev['graph_version']==VERSION and dev['executable_development_cases']==240 and all(r['source_identity_matches_expected'] for r in dev['observations'])
 failures=[dict(query_id=r['query_id'],missing=r['missing'],queries=r['queries']) for r in dev['observations'] if not r['automatic_retrieval_contract_pass']];assert dev['retrieval_plan_contract_passed']==239 and [f['query_id'] for f in failures]==['g-b05-coincidence']
 exports={}
 for name,count in [('claims',3006),('concepts',301),('relations',580)]:
  p=KB/'exports'/f'{name}.jsonl';rows=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()];assert len(rows)==count and all(r['graph_version']==VERSION for r in rows);exports[name]=dict(rows=count,graph_version=VERSION,sha256=sha(p))
 assert VERSION in (KB/'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150] and read(KB/'exports/coverage.json')['graph_version']==VERSION
 pending_ids={json.loads(l)['id'] for n in [49,50,51] for l in (AGENT/'curation/upper'/f'c_stage_l{n:03d}.pending.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()}
 changes=[
 ('upper-l051-c-stage-pending-B-third-buy-C2-finished-types-and-MACD-zero-axis',['third-points-both-leave-retest-sublevel-one-child-center-not-safe','600216-not-may18-1000-thirty-third-buy-use-five-subtypes','600216-may17-1455-author-yes-to-reader-two-legs'],'52离开/回试均次级类型且仅子枢不保安全，600216先否旧时刻后对认可紧前读者正确分段，未形式化全部C2完成/等值/实时确认。'),
 ('upper-l050-c-stage-pending-MACD-period-linearity-sensitivity-and-missing-formula',['precise-five-completion-needs-one-chart-only-five-enlarge-base','may21-fast-market-channel-no-exact-low-guarantee','may21-1040-second-buy-first-retest-zero-on-one-MACD'],'52精确5分完成需1分形态与此前大周期MACD辅助范围不同；5分观察和1分10:40二买例仍需结构，未给跨采样公式/积分。'),
 ('upper-l050-c-stage-pending-new-five-center-first-one-down-up-confirmation-execution',['same-level-decomposition-associativity-standard-high-low-joints','extension-first-three-range-later-oscillation-five-thirty-decomposition','second-buy-thirty-first-five-up-five-retest-no-low-second-leg'],'52结合律归标准/延伸前三段及5上5回二买补充，未补50将成新5枢的完整进行式算法与执行确认。'),
 ('upper-l051-c-stage-pending-day-centers-4000-4040-and-extend-expand-wording',['may21-fourth-thirty-bar-4050-unilateral-interval-branches','may22-4129-first-cross-does-not-exclude-first-top-scenario','may21-pressure-patterns-forming-forces-no-absolute-controller'],'52给4050单边区间和4129首次越线仍可能第一种模式、三形式合力选择中，不等已解决原4040一般扩展充分条件或扩张/扩展术语差。'),
 ('upper-l051-c-stage-pending-source-date-tail-four-later-charts-and-CCTV-reader-evidence',['600216-may17-1455-author-yes-to-reader-two-legs','individual-index-correlation-by-buy-sell-structure'],'52继续保CCTV三个病例为读者图，600216是作者独立对的指代认可而非把读者冒作者；来源时间/角色不凭图倒改，51旧图原发仍未核。'),
 ('upper-l049-c-stage-pending-guaranteed-chip-safety-full-position-and-skill-execution',['may21-fast-market-channel-no-exact-low-guarantee','near-opposite-points-use-large-unless-skilled-exit-room','third-buy-larger-oscillation-close-to-first-sell-size-and-exit-room'],'52明确快市/慢通道可能买不到精确点，大级近小级反向点须有退出空间；未把理想全仓或较大级别利润空间强语证成实际成交/收益。'),
 ('upper-l050-c-stage-pending-logic-confidence-geometric-guarantee-and-practice-criteria',['prediction-includes-observers-not-independent-clockwork','basic-patterns-predictable-price-formed-in-present-author-view','literal-divergence-level-not-smaller-than-turn-level-unresolved'],'52给观察参与/固定级别和形态预测哲学解释非自然科学证明，原不小于及30以上盘整保持范围张力不静修；未补50几何收益保证证明/模拟达标样本。'),
 ]
 followups=[]
 for pid,slugs,finding in changes:
  ids=['upper-l052-c-stage-'+s for s in slugs];assert pid in pending_ids and all(x in known for x in ids);followups.append(dict(pending_id=pid,status='new_source_located_scope_still_pending',new_claim_ids=ids,finding=finding,global_pending_not_closed=True,graph_version=VERSION))
 (AGENT/'curation/upper/c_stage_l052.partial-resolutions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in followups),encoding='utf-8')
 checks=['39条Schema/引用/身份/坐标预检，150段台账、15页10整图及PDF383原不小于整页视觉核对','原2967命题4091证据未改；2文907页9647段528图逐行只3跨日/50空格时间与10图来源授权变化','33项Node工程测试全部通过','3006命题全量引用校验0错误','6组语义/来源/条件/短答指代边界与7组CLI/共享/桌面模块一致，7命题11关联7图及3读者图无作者证据逐项核；查询只读哈希不变','冻结240题执行239取证计划/240来源身份通过，重合前20召回失败保持开放，未改题或核心排序','3006命题/301概念/580关系及Markdown/coverage同版本导出','7旧待核补来源仍开放，本批8待核；原不小于/以上跨课范围和哲学/预测强语未伪装外证']
 not_run=['冻结前20召回回归未修，完整G类别/自然查询基线/生成回答/消融对抗未完成','53至61共9课未完整语义审读；原不小于/以上、43混合夹注和全书跨课/图文尚待核','独立Agent打包真实执行及Windows离线/PDF缩放旋转跨页交互未验收']
 evaluation=dict(executable_development_cases=240,target=240,gold_review_status='model_reviewed_development',human_gold_reviewed=False,independent_test_set=False,generated_answers_scored=False,retrieval_plan_passed_on_current_graph=239,source_identity_passed_on_current_graph=240,open_retrieval_regressions=failures,full_stage_g_acceptance_complete=False,new_project_gold_cases_created_in_this_batch=0,note='固定题未改，全部身份通过；一条重合前20召回仍失败，分页找到不算原计划通过。')
 acceptance='52课39命题50证据发布；3006引用及33工程通过，冻结240题239计划/240身份通过，1条召回回归开放，语义及产品目标未完成。'
 next_anchor=next_row[0]+' / lesson-053';next_action='接续53课三类买卖点的再分辨，实际PDF396页标题；完整审读级别/次级走势与中枢、三买后的分支及三类点关系，继续保52原不小于/以上张力与来源边界。'
 p=AUDIT/'stage-c-l052-publication.json';pub=read(p);assert pub['graph_version']==VERSION and pub['formal_import']=='passed' and list(pub['batch_sha256'].values())==[sha(AGENT/'curation/upper/c_stage_l052.reviewed.jsonl')]
 pub.update(updated_at=datetime.now(timezone.utc).isoformat(),checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_action=next_action,exports=exports,final_sha256=dict(database=sha(KB/'graph.sqlite'),manifest=sha(KB/'manifest.json')),development_evaluation=evaluation,partial_pending_followups=7,semantic_completion=False,writes_to_knowledge_graph_by_this_finalizer=False);write(p,pub)
 p=AGENT/'curation/progress.json';progress=read(p);assert progress['graph_version'] in ['0.1.0-review-af327b82af12',VERSION]
 if progress['graph_version']!=VERSION:progress['previous_checkpoint']={k:progress[k] for k in ['graph_version','completed','next_action','evaluation']}
 outputs=['source-audit/stage-c-l052-'+n+'.json' for n in ['source-plan','source-applied','source-invariants','publication','verification']]+['upper/c_stage_l052.partial-resolutions.jsonl'];progress['machine_outputs']=list(dict.fromkeys(progress['machine_outputs']+outputs))
 progress.update(updated_at=datetime.now(timezone.utc).isoformat(),graph_version=VERSION,counts=counts,claim_status_counts=statuses,figure_origin_counts=figure_status,unit_processing_status_counts=unit_status,semantic_completion=False,completed=['52课150段15页10整图同模型四轮，39命题50证据12关系支撑；新增岛型反转/贪嗔痴疑慢两概念','3段归5/22和50日期空格、10图5后加5原发未核，原2967命题4091证据及全源原字/几何/映射未改','PDF383整页核原不小于与30级别以上盘整，跨课范围待核不静修或合总定理；观察参与/固定级别和形态预测的哲学解释不冒物理证明/逐价预测','精确5分完成需1分形态和较大周期MACD辅助不同范围，大级近小级反向点须退出空间；快行情/慢通道可能买不到精确位置，分析不保成交','离开回试均次级走势类型，子中枢不等完整走势/全波动，离开子枢可在内；单子枢不保安全、岛反和三买可转大例外保留','600216先否5/18 10:00，后对只认可紧前读者5/17 14:55及两段；作者原引仅对/上下文保reader；二买30一买后5上5回第二段不硬填A1/A3，买卖根一类非同级标签全并','3006引用/33工程/6边界/7模块及7命题11图关联通过，3幅CCTV图无作者证据，同版本导出；冻结240题239计划/240身份通过，1前20召回回归开放','7旧待核补来源仍开放；99课阅读记录含历史62至64，53至61共9课未完整审读'],pending=['本批8待核见upper/c_stage_l052.pending.jsonl：不小于/以上跨课范围、观察参与哲学强语、精确完成/指标辅助、三买类型/子枢/短答指代及次级分解未全核','53至61共9课未完整语义审读，99课阅读记录不等技术全抽取或解释统一','重合前20召回回归、完整G类别/自然基线/生成回答/消融对抗及43夹注/全书交叉未完成','独立Agent与Windows真实交付、离线/PDF交互未验收'],checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_resume_anchor=next_anchor,next_action=next_action,coverage_caveat='52课150段15页10图由同一代理四轮，累计99课阅读记录含历史62至64，不称独立复核或全书完成。',evaluation=evaluation,previous_turn_classification='progress：52课39命题50证据发布，3006引用/33工程通过；冻结题239/240且240身份通过，1召回回归开放，全书余9课。');write(p,progress)
 print(json.dumps(dict(graph_version=VERSION,reviewed=3006,development_cases=240,development_passed=239,remaining_lessons=9,next_anchor=next_anchor,semantic_completion=False),ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
