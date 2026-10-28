"""Finalize lesson56 checked publication without mutating the graph."""
import hashlib,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';AUDIT=Path(__file__).resolve().parent;VERSION='0.1.0-review-f3668c6fc5ca'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
 try:
  assert json.loads(db.execute("select value from metadata where key='graph_version'").fetchone()[0])==VERSION
  counts={t:db.execute(f'select count(*) from {t}').fetchone()[0] for t in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']};assert counts==dict(documents=2,pages=907,units=110,passages=9647,figures=528,concepts=306,claims=5783,evidence=6950,relations=628,reviews=3214)
  statuses=db.execute('select review_status,count(*) from claims group by review_status order by review_status').fetchall();assert dict(statuses)==dict(pending=2612,rejected=27,reviewed=3144)
  unit_status=db.execute('select processing_status,count(*) from units group by processing_status order by processing_status').fetchall();assert dict(unit_status)['extracted']==5
  figure_status=db.execute('select origin_status,count(*) from figures group by origin_status order by origin_status').fetchall()
  assert db.execute("select count(*) from evidence e join claims c on c.id=e.claim_id where c.review_status='reviewed'").fetchone()[0]==4311
  next_row=db.execute("select id,pdf_page,text from passages where unit_id='lesson-057' order by pdf_page,block_index,id limit 1").fetchone();assert next_row[0]=='volume_1-a53e99c37ca5-p0427-b009'
  known={r[0] for r in db.execute("select id from claims where review_status='reviewed'")}
 finally:db.close()
 assert read(KB/'manifest.json')['graph_version']==VERSION
 inv=read(AUDIT/'stage-c-l056-source-invariants.json');assert inv['pass'] and inv['graph_version']==VERSION and inv['original_reviewed_claims_unchanged']==3116 and inv['original_reviewed_evidence_unchanged']==4276
 verify=read(AUDIT/'stage-c-l056-verification.json');assert verify['pass'] and verify['graph_version']==VERSION and len(verify['checks'])==6 and len(verify['parity'])==7 and verify['intended_figure_links_checked']==dict(claims=16,associations=16,unique_figures=4)
 dev=read(AGENT/'evaluation/stage-g-development-current.results.json');assert dev['graph_version']==VERSION and dev['executable_development_cases']==240 and all(r['source_identity_matches_expected'] for r in dev['observations'])
 failures=[dict(query_id=r['query_id'],missing=r['missing'],queries=r['queries']) for r in dev['observations'] if not r['automatic_retrieval_contract_pass']];assert dev['retrieval_plan_contract_passed']==239 and [f['query_id'] for f in failures]==['g-b05-coincidence']
 exports={}
 for name,count in [('claims',3144),('concepts',306),('relations',628)]:
  p=KB/'exports'/f'{name}.jsonl';rows=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()];assert len(rows)==count and all(r['graph_version']==VERSION for r in rows);exports[name]=dict(rows=count,graph_version=VERSION,sha256=sha(p))
 assert VERSION in (KB/'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150] and read(KB/'exports/coverage.json')['graph_version']==VERSION
 pending_ids={json.loads(l)['id'] for n in [50,54,55] for l in (AGENT/'curation/upper'/f'c_stage_l{n:03d}.pending.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()}
 changes=[
 ('upper-l055-c-stage-pending-A-center-B-complete-subtype-two-comparisons-minimum-returns',['B-three-apparent-centers-not-complete-sloping-third-within-second','ABC-overlap-one-center-4087-4122-current-reference','new-five-center-starts-yesterday-C-other-decomposition-allowed'],'56示范B内第三段未完成不成中枢、ABC三完整类型叠1分，次日C为新5分三段首段；另分解允许不等读者另区间被认可，仍未给55统一+1索引或全部双解/完成算法。'),
 ('upper-l055-c-stage-pending-absolute-zero-cost-safety-second-sell-and-daily-third-execution',['may29-divergence-leg-unconfirmed-before-gap-first-sell-unavailable','index-second-sell-not-individual-same-kind-weak-stock-third-0948','A-internal-structure-confirm-no-new-high-or-consolidation-top'],'56明确5/29背驰段未确认，突发低开后原一卖实操不可得；指数二卖/弱股三卖各看结构，A形成中须内部确认，不将理论完全保证升级为所有T+1/跌停/通道/容量可成交。'),
 ('upper-l055-c-stage-pending-source-0947-vs-next-0948-three-later-figures-and-date-fields',['index-second-sell-not-individual-same-kind-weak-stock-third-0948','rebound-participation-level-stock-cost-futures-hypothetical-T0-literal','half-line-middle-of-shock-still-at-least-three-months-influence'],'56原9点48与55原09:47继续分存；新增标题5/30与昨天、原T+0/不大过及图24/52和12/26参数、后日线2011头/2007轴张力，未据图修改旧时间/模型。'),
 ('upper-l055-c-stage-pending-style-skill-technical-rebuy-principal-withdrawal-not-clearance',['rebound-participation-level-stock-cost-futures-hypothetical-T0-literal','larger-level-same-principles-less-frequency-safer-author-relative','late-rotation-dont-sell-weak-chase-risen-strong-reset-rhythm','master-one-before-precise-sector-jumping-skilled-goal'],'56回补看操作级别/股票/成本，期指100点为如果场景；大级相对安全频低，错节奏先调、低技能先做一只，未补本金风险消失或所有小资同风格的证明。'),
 ('upper-l050-c-stage-pending-MACD-period-linearity-sensitivity-and-missing-formula',['A-up-down-up-upward-leg-volume-or-green-red-absolute-height-aids','B-vs-gap-green-area-include-three-small-not-greater-literal','subminute-compare-area-one-minute-also-zero-axis-lines','C-high-column-height-qualitative-not-B-area-method'],'56分A跨色绝对大小/B含3绿面积/C高度，原样24/52/9与后重绘12/26/9参数不同，不据图伪造面积值；1分与以下零轴辅助不同，仍无50跨周期线性公式和敏感性证明。'),
 ('upper-l054-c-stage-pending-third-point-followthrough-vs-trend-possibility-fast-break-and-extreme-range',['B-inner-small-to-large-C-not-reach-last-inner-rebound-start','may31-original-one-center-expands-five-4015-4122-original-kuozhang','may31-early-rise-below-4087-third-sell'],'56外盘背内可小转大且不必回最后内反弹起点，三卖后未趋势则原扩张为5分例补范围；三类后继续方向不等完整趋势/永久不回，未解54全部强语和快破执行。'),
 ]
 followups=[]
 for pid,slugs,finding in changes:
  ids=['upper-l056-c-stage-'+s for s in slugs];assert pid in pending_ids and all(x in known for x in ids)
  followups.append(dict(pending_id=pid,status='new_source_located_scope_still_pending',new_claim_ids=ids,finding=finding,global_pending_not_closed=True,graph_version=VERSION))
 (AGENT/'curation/upper/c_stage_l056.partial-resolutions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in followups),encoding='utf-8')
 checks=['28条Schema/引用/身份/映射/坐标预检，48段台账、PDF422至427六页及4幅整图视觉核对','原3116命题4276证据未改；2文907页9647段528图逐行仅14时间空格和4图来源备注授权变化，原字/几何/映射不动','33项Node工程测试全部通过，测试终止后运行全量引用检查','3144命题全量引用校验0错误','6组语义/来源/完成/参数及原T+0边界与7组CLI/共享/桌面模块一致，16命题16图文关联4图逐项核，查询只读哈希不变','冻结240题执行239取证计划/240来源身份通过，重合前20召回仍失败，原题/核心排序未改','3144命题/306概念/628关系及Markdown/coverage同版本导出','6旧待核补来源仍开放，本批8待核；T+0/不大过/昨天日期/9点48原字、图24-52/12-26参数与后来图日期不静修']
 not_run=['冻结前20召回回归未修，完整G类别/自然查询基线/生成回答/消融对抗未完成','57至61共5课未完整语义审读；56原字/参数/观察完成与55时点、54公式/连接/短答、53/52原字、43混合夹注和全书跨课/图文尚待核','54编号短答完整跨页问题未自动全部纳入邻段context；当前条件/备注给联读源ID和原页，不宣称该接口限制已修','二三卖理论保证/回补股指期货100点/大级更安全及S-ST/轮动/利润历史判断未外证；固定两册不宣称原博客或当前金融法律核实','独立Agent打包真实执行及Windows离线/PDF缩放旋转跨页交互未验收']
 evaluation=dict(executable_development_cases=240,target=240,gold_review_status='model_reviewed_development',human_gold_reviewed=False,independent_test_set=False,generated_answers_scored=False,retrieval_plan_passed_on_current_graph=239,source_identity_passed_on_current_graph=240,open_retrieval_regressions=failures,full_stage_g_acceptance_complete=False,new_project_gold_cases_created_in_this_batch=0,note='固定题未改，全部身份通过；一条重合前20召回仍失败，分页找到不算原计划通过。')
 acceptance='56课28命题35证据发布；3144引用/33工程/6边界/7模块和16图文关联检查通过，冻结240题239计划/240身份通过，1召回回归开放；完整语义及产品目标未完成。'
 next_anchor=next_row[0]+' / lesson-057';next_action='接续57课当下图解分析再示范，实际PDF427页标题；完整审读当下走势分解/级别、资金仓位与买卖节奏，检查所有原页/整图及后加时间边界，保原字/参数和实际执行限制。'
 p=AUDIT/'stage-c-l056-publication.json';pub=read(p)
 assert pub['graph_version']==VERSION and pub['formal_import']=='passed' and list(pub['batch_sha256'].values())==[sha(AGENT/'curation/upper/c_stage_l056.reviewed.jsonl')]
 pub.update(updated_at=datetime.now(timezone.utc).isoformat(),checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_action=next_action,exports=exports,final_sha256=dict(database=sha(KB/'graph.sqlite'),manifest=sha(KB/'manifest.json')),development_evaluation=evaluation,partial_pending_followups=len(followups),semantic_completion=False,writes_to_knowledge_graph_by_this_finalizer=False);write(p,pub)
 p=AGENT/'curation/progress.json';progress=read(p);assert progress['graph_version'] in ['0.1.0-review-1faa97315b10',VERSION]
 if progress['graph_version']!=VERSION:progress['previous_checkpoint']={k:progress[k] for k in ['graph_version','completed','next_action','evaluation']}
 outputs=['source-audit/stage-c-l056-'+n+'.json' for n in ['source-plan','source-applied','source-invariants','publication','verification']]+['upper/c_stage_l056.partial-resolutions.jsonl'];progress['machine_outputs']=list(dict.fromkeys(progress['machine_outputs']+outputs))
 progress.update(updated_at=datetime.now(timezone.utc).isoformat(),graph_version=VERSION,counts=counts,claim_status_counts=statuses,figure_origin_counts=figure_status,unit_processing_status_counts=unit_status,semantic_completion=False,
 completed=['56课48段6页4整图同模型四轮，28命题35证据13关系支撑，新增一线股/跌停两概念及9关系','14时间空格/4图2未核2后加元数据规范，原3116命题4276证据及全源原字/几何/映射未改；原样24/52/9与重绘12/26/9、日线头2011/轴2007/9不合并','突发前5/29只是进入背驰段未确认，低开后一卖实操不可得，用二三卖但指数二卖非个股同类，理论完全保证不作所有账户可成交证明；9点48/55 09:47与标题5/30/昨天分别保','最低观察统一忽略细层非真实级别相等，B视觉三枢未完成/A形成中不预断已二卖；A跨色大小、B含3绿面积/C高度与1分零轴辅助不同，不大过不静改严格小于','外B与缺口盘背不强制内末段同级背，可小转大；ABC1分4087-4122与次日原扩张5分4015-4122分开，C是新枢第一段，另分解不等读者4027-4077获认可','原T+0不修T+1，期指100点是如果场景/股市回补看级别成本；几十K为统计建议非定理，轮动准点为技能目标、错节奏不杀弱追已涨','3144引用/33工程/6边界/7模块及16图文关联通过并同版本导出；冻结240题239计划/240身份通过，1前20召回回归开放','6旧待核补来源仍开放，本批8待核；103课阅读记录含历史62至64，57至61共5课未完整审读'],
 pending=['本批8待核见upper/c_stage_l056.pending.jsonl：T+0/不大过/标题昨天/时点、MACD参数与高度面积内外级、最低观察/完成和几十K、实操二三卖、新枢C首段、4图源、回补成本/期指和历史预测','57至61共5课未完整语义审读，103课阅读记录不等技术全抽取或解释统一','54编号短答完整跨页问题未自动纳邻段context；重合前20召回回归、完整G类别/自然基线/生成回答/消融对抗及43夹注/全书交叉未完成','独立Agent与Windows真实交付、离线/PDF交互未验收'],checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_resume_anchor=next_anchor,next_action=next_action,coverage_caveat='56课48段6页4整图由同一代理四轮，累计103课阅读记录含历史62至64，不称独立复核或全书完成。',evaluation=evaluation,previous_turn_classification='progress：55/56两课共67命题78证据发布，当前3144引用/33工程与6边界7模块16图文关联通过；冻结题239/240且240身份通过，1召回回归开放，全书余5课。')
 write(p,progress)
 print(json.dumps(dict(graph_version=VERSION,reviewed=3144,reviewed_evidence=4311,development_cases=240,development_passed=239,remaining_lessons=5,next_anchor=next_anchor,semantic_completion=False),ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
