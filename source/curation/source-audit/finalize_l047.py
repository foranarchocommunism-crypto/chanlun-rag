"""Finalize verified lesson47 publication; graph remains read-only."""
import hashlib,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';AUDIT=Path(__file__).resolve().parent
VERSION='0.1.0-review-a4f759f80fae'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
 try:
  assert json.loads(db.execute("select value from metadata where key='graph_version'").fetchone()[0])==VERSION
  counts={t:db.execute(f'select count(*) from {t}').fetchone()[0] for t in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']}
  assert counts==dict(documents=2,pages=907,units=110,passages=9647,figures=528,concepts=291,claims=5457,evidence=6535,relations=525,reviews=2888)
  status=db.execute('select review_status,count(*) from claims group by review_status order by review_status').fetchall();assert dict(status)==dict(pending=2612,rejected=27,reviewed=2818)
  unit_status=db.execute('select processing_status,count(*) from units group by processing_status order by processing_status').fetchall();assert dict(unit_status)['extracted']==14
  figure_status=db.execute('select origin_status,count(*) from figures group by origin_status order by origin_status').fetchall()
  assert db.execute("select count(*) from evidence e join claims c on c.id=e.claim_id where c.review_status='reviewed'").fetchone()[0]==3896
  next_row=db.execute("select id,pdf_page,text from passages where unit_id='lesson-048' order by pdf_page,block_index,id limit 1").fetchone();assert next_row[2].startswith('教你炒股票48')
  known={r[0] for r in db.execute("select id from claims where review_status='reviewed'")}
 finally:db.close()
 assert read(KB/'manifest.json')['graph_version']==VERSION
 inv=read(AUDIT/'stage-c-l047-source-invariants.json');assert inv['pass'] and inv['graph_version']==VERSION and inv['original_reviewed_claims_unchanged']==2782 and inv['original_reviewed_evidence_unchanged']==3855
 verify=read(AUDIT/'stage-c-l047-verification.json');assert verify['pass'] and verify['graph_version']==VERSION and len(verify['checks'])==6 and len(verify['parity'])==7 and verify['intended_figure_links_checked']==dict(claims=6,associations=9,unique_figures=6)
 dev=read(AGENT/'evaluation/stage-g-development-current.results.json');assert dev['graph_version']==VERSION and dev['executable_development_cases']==240 and dev['retrieval_plan_contract_passed']==239 and all(r['source_identity_matches_expected'] for r in dev['observations'])
 exports={}
 for name,number in [('claims',2818),('concepts',291),('relations',525)]:
  p=KB/'exports'/f'{name}.jsonl';rows=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()];assert len(rows)==number and all(r['graph_version']==VERSION for r in rows);exports[name]=dict(rows=number,graph_version=VERSION,sha256=sha(p))
 assert VERSION in (KB/'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150] and read(KB/'exports/coverage.json')['graph_version']==VERSION
 pending_ids={json.loads(l)['id'] for n in [45,46] for l in (AGENT/'curation/upper'/f'c_stage_l{n:03d}.pending.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()}
 changes=[
 ('upper-l046-c-stage-pending-daily-K-center-scope-session-model-not-recursive-center',['strict-five-center-three-one-types-day-center-borrowed-different','tiny-day-overlap-can-ignore-rough-view-ten-points-not-universal','overlap-common-part-three-intervals-strict-or-ignored-small-range-reference'],'47作者明确这两节日内中枢借用非递归，严格5分三段1分；小幅重叠可粗略忽略与严格算分开，未补所有交易时段模型或最低不可分级别细则。'),
 ('upper-l046-c-stage-pending-two-center-unilateral-bar-assignment-four-five-eight-and-no-center-context',['first-three-no-overlap-case-excludes-two-day-centers-author-reasoning','1330-three-bars-create-day-center-eliminate-zero-center-weak-balance','source-3892-3688-versus-3688-3692-number-tension'],'47给4/19前三K无重叠排两中枢、13:30成中枢排无中枢的案例推理，未项目穷举全部8K；允许后K中枢与条件关系仍需查，3892/3692原字不合不静改。'),
 ('upper-l046-c-stage-pending-oscillation-two-intervals-green-area-and-level-without-axis-return',['five-minute-chart-area-below-five-signal-not-axis-return','tick-divergence-one-minute-MACD-bar-length-auxiliary-only','after1330-no-stronger-than-before1030-five-minute-area-shenzhen','minimum-last-rebound-place-not-full-center-return-guarantee'],'47改看5分比较面积仍非5分背驰，分笔借1分柱长辅助为特殊对象；目标只最后反弹处非全回枢，未补完整力度积分或通用买点公式。'),
 ('upper-l046-c-stage-pending-skill-cash-Tplus1-market-direction-stockpool-and-execution',['small-capital-small-level-only-daily-weekly-hold-separate-stock-chart','Tplus1-even-3358-may-not-sell-next-day-Tplus0-intraday-exit','teaching-example-not-all-super-short-one-second-ability-rhetoric'],'47限小资金小级而日周持有另看，T+1低买仍次日难卖；T+0仅交易时间约束改变非所有风险消失，超短不鼓励所有人，未补成交/对冲完整模型。'),
 ('upper-l045-c-stage-pending-hold-cash-waiting-level-guarantee-and-intralevel-trades',['quick-recovery-possible-after-sale-wait-buy-point-precision','before-new-break-author-certain-analysis-wait-compare-not-trade-guarantee','future-larger-divergence-or-direct-rise-market-chooses-center-key'],'47退出后等市场选择，强语100%限该案理论/分析对象，不保精确买价/时刻/成交；分笔反弹目标达后仍可跌或直接涨，不把等待当猜唯一方向。'),
 ('upper-l045-c-stage-pending-force-measure-rectangular-proposal-MACD-area-zero-axis',['tick-divergence-one-minute-MACD-bar-length-auxiliary-only','five-minute-chart-area-below-five-signal-not-axis-return','after1330-no-stronger-than-before1030-five-minute-area-shenzhen'],'47说分笔信号可看1分柱长度辅助，并非取消较大中枢两段比较看面积/回轴；未给矩形力度公式认可或所有柱长变化均背驰。'),
 ('upper-l045-c-stage-pending-first-center-weakest-three-five-types-and-unknown-path',['thirty-minute-operation-observe-centers-in-departing-move','strict-five-center-three-one-types-day-center-borrowed-different','intraday-hedging-method-promised-not-given'],'47再指30分离开段里中枢变化和严格5分结构、对冲留后，仍非45首中枢后所有走势类型分支的完整讲解；日内辅助案例不能替代。'),
 ]
 followups=[]
 for pending_id,slugs,finding in changes:
  ids=['upper-l047-c-stage-'+s for s in slugs];assert pending_id in pending_ids and all(i in known for i in ids)
  followups.append(dict(pending_id=pending_id,status='new_source_located_scope_still_pending',new_claim_ids=ids,finding=finding,global_pending_not_closed=True,graph_version=VERSION))
 (AGENT/'curation/upper/c_stage_l047.partial-resolutions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in followups),encoding='utf-8')
 checks=['36条Schema/引用/身份/坐标预检，65段台账、9页6整图及346原页3892字面视觉核对','原2782命题3855已复核证据未改；2文907页9647段528图逐行比对只13时间空格和6图备注授权变更','33项Node工程测试全部通过，串行运行','2818命题全量引用校验0错误','6组语义/身份/范围边界、7组CLI/公共/桌面模块一致且只读哈希不变；6命题9图关联逐项确认','上证分时背景不当5分MACD证据，图3后加3原发未核；六段全民炒股经济议论只作上下文，百分比非配置规则','冻结240开发题执行，239取证计划通过/240身份通过；重合前20召回失败，分页可取但原失败保留，未改冻结题','2818命题/291概念/525关系及Markdown/coverage同版本导出','7条旧待核补充，原问题全部保持开放']
 not_run=['240题中g-b05-coincidence的重合前20召回失败仍开放；完整类别/自然问题基线/生成回答评分/消融对抗未完成，开发取证计划不替代完整G','48至61共14课完整语义及全书跨课/图文审查未完成；3892/3692与价格异值、43混合夹注等仍待核','独立Agent打包后运行及Windows实际离线/缩放旋转跨页交互未验收']
 acceptance='47课36命题41证据发布；2818引用通过；240冻结开发题239通过，1条前20召回回归保持开放，7待核开放，全书及产品目标未完成。'
 next_anchor=next_row[0]+' / lesson-048';next_action=f'接续48课暴跌，牛市行情的一夜情，实际PDF{next_row[1]}页标题，完整审读牛市/熊市例、买卖点与日内辅助分类范围，保存答疑及图源。'
 evaluation=dict(executable_development_cases=240,target=240,gold_review_status='model_reviewed_development',human_gold_reviewed=False,independent_test_set=False,generated_answers_scored=False,retrieval_plan_passed_on_current_graph=239,source_identity_passed_on_current_graph=240,open_retrieval_regressions=1,full_stage_g_acceptance_complete=False,new_project_gold_cases_created_in_this_batch=0,note='同模型开发取证计划/身份回归，非独立金标准、回答质量或实际桌面验收。')
 path=AUDIT/'stage-c-l047-publication.json';pub=read(path);assert pub['graph_version']==VERSION and pub['formal_import']=='passed' and list(pub['batch_sha256'].values())==[sha(AGENT/'curation/upper/c_stage_l047.reviewed.jsonl')]
 pub.update(updated_at=datetime.now(timezone.utc).isoformat(),checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_action=next_action,exports=exports,final_sha256=dict(database=sha(KB/'graph.sqlite'),manifest=sha(KB/'manifest.json')),development_evaluation=evaluation,partial_pending_followups=7,semantic_completion=False,writes_to_knowledge_graph_by_this_finalizer=False);write(path,pub)
 path=AGENT/'curation/progress.json';progress=read(path);assert progress['graph_version'] in ['0.1.0-review-e7c4870b7d7e',VERSION]
 if progress['graph_version']!=VERSION:progress['previous_checkpoint']={k:progress[k] for k in ['graph_version','completed','next_action','evaluation']}
 outputs=['source-audit/stage-c-l047-'+n+'.json' for n in ['source-plan','source-applied','source-invariants','publication','verification','retrieval-truncation']]+['upper/c_stage_l047.partial-resolutions.jsonl']
 progress['machine_outputs']=list(dict.fromkeys(progress['machine_outputs']+outputs))
 progress.update(updated_at=datetime.now(timezone.utc).isoformat(),graph_version=VERSION,counts=counts,claim_status_counts=status,figure_origin_counts=figure_status,unit_processing_status_counts=unit_status,semantic_completion=False,completed=['上册47课65段9页6图同模型四轮，36命题41证据12关系支撑，新增突破性缺口','13来源时间仅空格规范，图3后加3原发未核；原2782命题3855证据及全源原字/坐标/映射未改','作者100%限当日条件内理论措辞非实测胜率/成交保证；小资金小级、日周资金、指数和个股自身图分开，首次三K排两中枢推理仍未全模型证明','分笔借1分柱长度辅助与5分图两段绿面积不同对象；可完非必已完，不强于非必须更小，保证只最后反弹处不等全回中枢，后续可跌或直上','T+1低买次日仍出不掉，T+0只改变隔日约束非全风险消失；当日对冲留后，5周/5日简法保能力/结构限制','作者明确分时中枢借用非递归，严格5分三段1分；粗忽略几点非统一10点硬阈值，原3892/3688与后3688至3692不静合；三天缺口非绝对统计无样本','2818引用/33工程、6边界和7模块一致、6命题9图关联、240冻结开发题239计划通过及240身份通过；重合前20召回失败保留，分页可取，不改金标准；同版本导出完成；上证分时背景不充5分MACD证据，六段宏观附文保留上下文','7旧待核补充开放，94课阅读记录含历史62至64；48至61共14课尚未完整审读，45全类型分支仍待接续'],pending=['本批7待核见upper/c_stage_l047.pending.jsonl：日内案例排类与100%/分笔长度面积及目标/3351等价格和后图/执行T+1与0容量对冲/三日缺口统计/借用中枢及3892差异/多层技能与均线强语','48至61共14课未完整语义审读；94课阅读记录不等全书技术抽取或全部解释统一，45遗留类型分类未补齐','冻结题g-b05-coincidence前20召回回归开放；240题完整类别/自然问题基线/生成回答质量/消融对抗和全书交叉审查未完成，43混合夹注及数值异文待核','独立Agent实际交付与Windows真实离线/PDF交互验收未完成'],checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_resume_anchor=next_anchor,next_action=next_action,coverage_caveat='47课65段9页6图同模型四轮，累计94课阅读记录含历史62至64，不称独立复核或全书完成。',evaluation=evaluation,previous_turn_classification='progress：47课65段6图、13时间规范及36条41证据发布；2818引用通过、冻结240题239通过及240身份通过，1检索截断回归开放，余14课。')
 write(path,progress);print(json.dumps(dict(graph_version=VERSION,reviewed=2818,development_cases=240,development_passed=239,remaining_lessons=14,next_anchor=next_anchor,semantic_completion=False),ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
