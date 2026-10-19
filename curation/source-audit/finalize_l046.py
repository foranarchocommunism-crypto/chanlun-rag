"""Finalize verified lesson46 publication; graph remains read-only."""
import hashlib,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';AUDIT=Path(__file__).resolve().parent
VERSION='0.1.0-review-e7c4870b7d7e'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
 try:
  assert json.loads(db.execute("select value from metadata where key='graph_version'").fetchone()[0])==VERSION
  counts={t:db.execute(f'select count(*) from {t}').fetchone()[0] for t in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']}
  assert counts==dict(documents=2,pages=907,units=110,passages=9647,figures=528,concepts=290,claims=5421,evidence=6494,relations=514,reviews=2852)
  status=db.execute('select review_status,count(*) from claims group by review_status order by review_status').fetchall();assert dict(status)==dict(pending=2612,rejected=27,reviewed=2782)
  unit_status=db.execute('select processing_status,count(*) from units group by processing_status order by processing_status').fetchall();assert dict(unit_status)['extracted']==15
  figure_status=db.execute('select origin_status,count(*) from figures group by origin_status order by origin_status').fetchall()
  assert db.execute("select count(*) from evidence e join claims c on c.id=e.claim_id where c.review_status='reviewed'").fetchone()[0]==3855
  next_row=db.execute("select id,pdf_page,text from passages where unit_id='lesson-047' order by pdf_page,block_index,id limit 1").fetchone();assert next_row[2].startswith('教你炒股票47')
  known={r[0] for r in db.execute("select id from claims where review_status='reviewed'")}
 finally:db.close()
 assert read(KB/'manifest.json')['graph_version']==VERSION
 inv=read(AUDIT/'stage-c-l046-source-invariants.json');assert inv['pass'] and inv['graph_version']==VERSION and inv['original_reviewed_claims_unchanged']==2749 and inv['original_reviewed_evidence_unchanged']==3811
 verify=read(AUDIT/'stage-c-l046-verification.json');assert verify['pass'] and verify['graph_version']==VERSION and len(verify['checks'])==6 and len(verify['parity'])==7 and verify['intended_figure_links_checked']==dict(claims=13,associations=14,unique_figures=6)
 dev=read(AGENT/'evaluation/stage-g-development-current.results.json');assert dev['graph_version']==VERSION and dev['executable_development_cases']==dev['retrieval_plan_contract_passed']==240 and all(r['source_identity_matches_expected'] for r in dev['observations'])
 exports={}
 for name,number in [('claims',2782),('concepts',290),('relations',514)]:
  p=KB/'exports'/f'{name}.jsonl';rows=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()];assert len(rows)==number and all(r['graph_version']==VERSION for r in rows);exports[name]=dict(rows=number,graph_version=VERSION,sha256=sha(p))
 assert VERSION in (KB/'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150] and read(KB/'exports/coverage.json')['graph_version']==VERSION
 pending_ids={json.loads(l)['id'] for n in [43,44,45] for l in (AGENT/'curation/upper'/f'c_stage_l{n:03d}.pending.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()}
 changes=[
 ('upper-l045-c-stage-pending-first-center-weakest-three-five-types-and-unknown-path',['daily-auxiliary-classification-not-strict-level-type-replacement','four-hour-eight-thirty-bars-three-adjacent-overlap-day-center'],'46明确暂改讲日内辅助分类，三相邻30分K重叠非45三完整5分类型；45首中枢后全部分支仍未完成，不假闭旧问题。'),
 ('upper-l045-c-stage-pending-force-measure-rectangular-proposal-MACD-area-zero-axis',['center-oscillation-two-intervals-green-area-earlier-stronger','five-minute-no-yellow-white-return-not-five-divergence-below-five'],'46给两个完整跨日同向区间绿面积比较，并明确无回轴非5分而该例更低；未给测度公式、矩形算法或任意单柱充分信号。'),
 ('upper-l045-c-stage-pending-five-day-unilateral-not-consolidation-and-cost-safety',['weak-skill-below-five-day-cash-unless-clear-larger-divergence','bad-market-larger-level-or-late-buy-point-Tplus1','Tplus1-consider-real-five-divergence-big-fall-small-capital-view'],'46加低技能破5日线持币/较大背驰例外及大盘差T+1条件，小资金真实5分反弹为作者一般判断非必成盈利；不取消45单边/盘整范围。'),
 ('upper-l045-c-stage-pending-subminute-index-three-legs-1345-identity-and-stock-cases',['ABC-first-two-exist-C-can-rise-directly-not-next-day-forecast','center-oscillation-two-intervals-green-area-earlier-stronger','five-minute-no-yellow-white-return-not-five-divergence-below-five'],'46另两日的ABC可直接上、两区间比较和以下级信号丰富范围，但未逐项命名45的1345或证明所有原股案例；日期对象不可混。'),
 ('upper-l045-c-stage-pending-decomposition-from-divergence-scope-reader-unanswered-details',['completion-is-form-not-amplitude-not-auto-confirm-B-from-strength','subsub-retest-makes-sublevel-third-point-earlier-can-act','qualified-same-level-separation-at-small-divergence-followup'],'46说明完成形态非幅度、较小三类点更早和小背驰分界的有限认可；未全答16三类穷尽/级差或无严格三买B完成的全部算法。'),
 ('upper-l043-c-stage-pending-small-turn-return-B-necessary-path-and-C-overlap-timing',['completion-is-form-not-amplitude-not-auto-confirm-B-from-strength','qualified-same-level-separation-at-small-divergence-followup'],'46再问强c无严格三买与后续分界，作者强调形态及认可既有分法；不抹43更大中枢/重合/未完C前提，也不由强劲幅度单独证B完成。'),
 ('upper-l044-c-stage-pending-small-large-theorem-necessary-only-and-generalized-examples',['subsub-retest-makes-sublevel-third-point-earlier-can-act','bad-market-larger-level-or-late-buy-point-Tplus1','Tplus1-consider-real-five-divergence-big-fall-small-capital-view'],'46允许更小第三类点先利用，但大盘方向/能力与T+1仍约束，并不将44必要点变充分大转折或保证小点实际盈利。'),
 ]
 followups=[]
 for pending_id,slugs,finding in changes:
  ids=['upper-l046-c-stage-'+s for s in slugs];assert pending_id in pending_ids and all(i in known for i in ids)
  followups.append(dict(pending_id=pending_id,status='new_source_located_scope_still_pending',new_claim_ids=ids,finding=finding,global_pending_not_closed=True,graph_version=VERSION))
 (AGENT/'curation/upper/c_stage_l046.partial-resolutions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in followups),encoding='utf-8')
 checks=['33条Schema/引用/身份/坐标预检，86段台账、9页及6整图视觉核对，强弱/转折及无中枢标题联合引文','原2749命题3811已复核证据未改；2文907页9647段528图逐行比对只27来源日期和6图备注授权变更','33项Node工程测试全部通过，串行运行','2782命题全量引用校验0错误','6组语义/身份/范围边界、7组CLI/公共/桌面模块一致且只读哈希不变；13命题14图关联逐项确认','三讲义署FHSL20080725含2008案例及334行情后K共4后加，335/336同日原发未核；基金指控不进已复核技术证据','240冻结开发取证计划及已标注身份回归通过，无新题替换','2782命题/290概念/514关系及Markdown/coverage同版本导出','7条旧待核补充，原问题全部保持开放']
 not_run=['240题完整类别/自然问题基线/生成回答评分/消融对抗未完成，开发取证计划不替代完整G','47至61共15课完整语义及全书跨课/图文审查未完成，43课316混合夹注段身份细分仍待核','独立Agent打包后运行及Windows实际离线/缩放旋转跨页交互未验收']
 acceptance='46课33命题44证据发布；2782引用及240冻结开发题回归通过，7待核开放，全书及产品目标未完成。'
 next_anchor=next_row[0]+' / lesson-047';next_action=f'接续47课一夜情行情分析，实际PDF{next_row[1]}页标题，完整审读4/19日内分类/买卖点及相应资金级别风险、辅助模型与严格结构作用域。'
 evaluation=dict(executable_development_cases=240,target=240,gold_review_status='model_reviewed_development',human_gold_reviewed=False,independent_test_set=False,generated_answers_scored=False,retrieval_plan_and_source_identity_passed_on_current_graph=240,full_stage_g_acceptance_complete=False,new_project_gold_cases_created_in_this_batch=0,note='同模型开发取证计划/身份回归，非独立金标准、回答质量或实际桌面验收。')
 path=AUDIT/'stage-c-l046-publication.json';pub=read(path);assert pub['graph_version']==VERSION and pub['formal_import']=='passed' and list(pub['batch_sha256'].values())==[sha(AGENT/'curation/upper/c_stage_l046.reviewed.jsonl')]
 pub.update(updated_at=datetime.now(timezone.utc).isoformat(),checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_action=next_action,exports=exports,final_sha256=dict(database=sha(KB/'graph.sqlite'),manifest=sha(KB/'manifest.json')),development_evaluation=evaluation,partial_pending_followups=7,semantic_completion=False,writes_to_knowledge_graph_by_this_finalizer=False);write(path,pub)
 path=AGENT/'curation/progress.json';progress=read(path);assert progress['graph_version'] in ['0.1.0-review-f348422e88c4',VERSION]
 if progress['graph_version']!=VERSION:progress['previous_checkpoint']={k:progress[k] for k in ['graph_version','completed','next_action','evaluation']}
 outputs=['source-audit/stage-c-l046-'+n+'.json' for n in ['source-plan','source-applied','source-invariants','publication','verification']]+['upper/c_stage_l046.partial-resolutions.jsonl']
 progress['machine_outputs']=list(dict.fromkeys(progress['machine_outputs']+outputs))
 progress.update(updated_at=datetime.now(timezone.utc).isoformat(),graph_version=VERSION,counts=counts,claim_status_counts=status,figure_origin_counts=figure_status,unit_processing_status_counts=unit_status,semantic_completion=False,completed=['上册46课86段9页6图同模型四轮，33命题44证据13关系支撑，新增每日走势分类/每天走势上的中枢/平衡市强弱转折/单边区间7概念','4跨日及23日期空格规范，图4后加2原发未核；原2749命题3811证据及全源原字/坐标/映射未改','4小时8根30分K的三相邻重叠仅日内辅助模型，独立于严格递归；一中枢前三常极值非绝对或先知，强弱标签联合标题证据、双极值/等值待核','两中枢无重合/单边区间及K归属、第4第5可兼、第8可能穿越限本模型；零中枢三K无共同重叠非任意两K无交叉，强日不保延续，200070417原字不改','两完整跨日同向绿面积比较非单柱高度，5分看图无回轴不升5分背驰；完成形态非幅度，小点较早不自动B完整，括号读者引文排除','能力不足可不参与/持币，5日线破带较大背驰例外；大盘差等较大/尾盘买点与T+1、小资金5分反弹条件联合，股票池每次1最多2','2782引用/33工程、6边界和7模块一致、13命题14图关联、240冻结开发题及同版本导出通过','7旧待核补充开放，93课阅读记录含历史62至64；47至61共15课尚未完整审读，45首中枢后全类型分类仍未补齐'],pending=['本批7待核见upper/c_stage_l046.pending.jsonl：日内模型作用域/极值回看等值标签/两枢单边与无枢/两区间力度及级别/完成与早小点/T+1能力执行/历史指控日期图源','47至61共15课未完整语义审读；93课阅读记录不等全书技术抽取或全部解释统一，45遗留分类仍在后续','240题完整类别/自然问题基线/生成回答质量/消融对抗及全书交叉审查未完成；43课316混合夹注段来源细分待核','独立Agent实际交付与Windows真实离线/PDF交互验收未完成'],checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_resume_anchor=next_anchor,next_action=next_action,coverage_caveat='46课86段9页6图同模型四轮，累计93课阅读记录含历史62至64，不称独立复核或全书完成。',evaluation=evaluation,previous_turn_classification='progress：46课86段6图、27日期修正及33条44证据发布；2782引用/240冻结开发题回归通过，余15课。')
 write(path,progress);print(json.dumps(dict(graph_version=VERSION,reviewed=2782,development_cases=240,remaining_lessons=15,next_anchor=next_anchor,semantic_completion=False),ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
