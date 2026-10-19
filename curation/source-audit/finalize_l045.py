"""Finalize verified lesson45 publication; graph remains read-only."""
import hashlib,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';AUDIT=Path(__file__).resolve().parent
VERSION='0.1.0-review-f348422e88c4'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
 try:
  assert json.loads(db.execute("select value from metadata where key='graph_version'").fetchone()[0])==VERSION
  counts={t:db.execute(f'select count(*) from {t}').fetchone()[0] for t in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']}
  assert counts==dict(documents=2,pages=907,units=110,passages=9647,figures=528,concepts=283,claims=5388,evidence=6450,relations=501,reviews=2819)
  status=db.execute('select review_status,count(*) from claims group by review_status order by review_status').fetchall();assert dict(status)==dict(pending=2612,rejected=27,reviewed=2749)
  unit_status=db.execute('select processing_status,count(*) from units group by processing_status order by processing_status').fetchall();assert dict(unit_status)['extracted']==16
  figure_status=db.execute('select origin_status,count(*) from figures group by origin_status order by origin_status').fetchall()
  assert db.execute("select count(*) from evidence e join claims c on c.id=e.claim_id where c.review_status='reviewed'").fetchone()[0]==3811
  next_row=db.execute("select id,pdf_page,text from passages where unit_id='lesson-046' order by pdf_page,block_index,id limit 1").fetchone();assert next_row[2].startswith('教你炒股票46')
  known={r[0] for r in db.execute("select id from claims where review_status='reviewed'")}
 finally:db.close()
 assert read(KB/'manifest.json')['graph_version']==VERSION
 inv=read(AUDIT/'stage-c-l045-source-invariants.json');assert inv['pass'] and inv['graph_version']==VERSION and inv['original_reviewed_claims_unchanged']==2708 and inv['original_reviewed_evidence_unchanged']==3761
 verify=read(AUDIT/'stage-c-l045-verification.json');assert verify['pass'] and verify['graph_version']==VERSION and len(verify['checks'])==6 and len(verify['parity'])==7 and verify['intended_figure_links_checked']==dict(claims=5,associations=6,unique_figures=4)
 dev=read(AGENT/'evaluation/stage-g-development-current.results.json');assert dev['graph_version']==VERSION and dev['executable_development_cases']==dev['retrieval_plan_contract_passed']==240 and all(r['source_identity_matches_expected'] for r in dev['observations'])
 exports={}
 for name,number in [('claims',2749),('concepts',283),('relations',501)]:
  p=KB/'exports'/f'{name}.jsonl';rows=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()];assert len(rows)==number and all(r['graph_version']==VERSION for r in rows);exports[name]=dict(rows=number,graph_version=VERSION,sha256=sha(p))
 assert VERSION in (KB/'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150] and read(KB/'exports/coverage.json')['graph_version']==VERSION
 pending_ids={json.loads(l)['id'] for n in [38,40,41,43,44] for l in (AGENT/'curation/upper'/f'c_stage_l{n:03d}.pending.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()}
 changes=[
 ('upper-l044-c-stage-pending-MACD-reader-parameters-skill-switch-and-result-vs-process',['MACD-bars-area-not-height-shortening-plus-zero-return','force-precise-definition-measure-no-rectangle-formula-endorsement'],'45明确柱面积非缩短并看回轴，力度精确定义需测度但公式未给；不构成44读者5.10.10参数或矩形力度算法认可。'),
 ('upper-l044-c-stage-pending-historical-switch-stability-policy-only-and-twenty-year-risk-claims',['five-day-line-trending-not-consolidation-center-knowledge-replaces','twenty-year-script-and-2225-text-time-inconsistency','apr17-risk-remains-bad-data-rate-expectation-conditional'],'45限定5日线单边非盘整，承认顺利也风险，20年剧本与2225原字有差异；不消44站稳对象不明/政策唯一及20年强预测待核。'),
 ('upper-l043-c-stage-pending-MACD-candidate-yellow-white-new-high-and-first-zero-return',['MACD-bars-area-not-height-shortening-plus-zero-return','force-precise-definition-measure-no-rectangle-formula-endorsement'],'45补面积/黄白回轴及测度提示，未给43候选最终确认或42首次归零必回买全部条件，不编公式。'),
 ('upper-l043-c-stage-pending-small-turn-return-B-necessary-path-and-C-overlap-timing',['decomposition-previous-lessons-from-divergence-not-all-questions-answered','apr16-no-minute-bottom-required-third-center-leg-complete-can-up'],'45再指同级/小转大均从背驰点分解，当日中枢三段完成可续上；未取消43重合/完成的分类前提，也未补C与日线区间全规则。'),
 ('upper-l041-c-stage-pending-beginner-level-frequency-and-divergence-stage-necessary-not-sufficient',['subminute-operation-requires-skill-and-1055-1346-three-segments','beginner-smaller-level-needs-skill-thirty-minute-95-percent-rhetoric','five-day-line-trending-not-consolidation-center-knowledge-replaces'],'45强调子分钟须技能和分清三段、初学抓30分，95%无样本；5日线仅单边简法，不撤41初学级别/候选段限制或把缩级当万能。'),
 ('upper-l040-c-stage-pending-rhythm-price-stock-vs-long-term-fundamentals',['five-day-line-trending-not-consolidation-center-knowledge-replaces','bad-earnings-strength-watch-not-certain-conspiracy-or-buy','bull-market-can-sell-large-point-rebuy-not-blind-long'],'45说明5日线盘整用处小、牛市大级卖点可卖再买；坏业绩骗筹码是未核因果而非基本面事实，不抹40技术节奏/真长线估值范围。'),
 ('upper-l038-c-stage-pending-mechanical-branches-completion-equality-execution-and-profit',['fixed-thirty-level-buy-hold-to-sell-cash-to-next-buy','waiting-active-monitor-type-growth-and-classification','thirty-type-minimum-one-thirty-center-can-end-after-formed','size-limits-compounding-speed-and-point-capacity'],'45将持股持币明确为固定级别等待/当下分类，首中枢可随时完但不必即完，容量不能无限复利；未补38全部等值/完成/执行和盈利实证。'),
 ]
 followups=[]
 for pending_id,slugs,finding in changes:
  ids=['upper-l045-c-stage-'+s for s in slugs];assert pending_id in pending_ids and all(i in known for i in ids)
  followups.append(dict(pending_id=pending_id,status='new_source_located_scope_still_pending',new_claim_ids=ids,finding=finding,global_pending_not_closed=True,graph_version=VERSION))
 (AGENT/'curation/upper/c_stage_l045.partial-resolutions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in followups),encoding='utf-8')
 checks=['41条Schema/引用/身份/坐标预检，134段台账、12页及4整图视觉核对','原2708命题3761已复核证据未改；2文907页9647段528图逐行比对只45来源日期及4图备注授权变更','33项Node工程测试全部通过，串行运行','2749命题全量引用校验0错误','6组语义/身份/范围边界、7组CLI/公共/桌面模块一致且只读哈希不变；5命题6图关联逐项确认','八段博客/七段经济附文只作上下文，331媒体摘录全读者；2225不静改，四图3后加1原发未核','240冻结开发取证计划及已标注身份回归通过，无新题替换','2749命题/283概念/501关系及Markdown/coverage同版本导出','7条旧待核补充，原问题全部保持开放']
 not_run=['240题完整类别/自然问题基线/生成回答评分/消融对抗未完成，开发取证计划不替代完整G','46至61共16课完整语义及全书跨课/图文审查未完成，43课316混合夹注段身份细分仍待核','独立Agent打包后运行及Windows实际离线/缩放旋转跨页交互未验收']
 acceptance='45课41命题50证据发布；2749引用及240冻结开发题回归通过，8待核开放，全书及产品目标未完成。'
 next_anchor=next_row[0]+' / lesson-046';next_action=f'接续46课每日走势的分类，实际PDF{next_row[1]}页标题，完整审读日内结构/周期分类及与45首中枢后可能分支的作用域，保留附带答疑身份和图源。'
 evaluation=dict(executable_development_cases=240,target=240,gold_review_status='model_reviewed_development',human_gold_reviewed=False,independent_test_set=False,generated_answers_scored=False,retrieval_plan_and_source_identity_passed_on_current_graph=240,full_stage_g_acceptance_complete=False,new_project_gold_cases_created_in_this_batch=0,note='同模型开发取证计划/身份回归，非独立金标准、回答质量或实际桌面验收。')
 path=AUDIT/'stage-c-l045-publication.json';pub=read(path);assert pub['graph_version']==VERSION and pub['formal_import']=='passed' and list(pub['batch_sha256'].values())==[sha(AGENT/'curation/upper/c_stage_l045.reviewed.jsonl')]
 pub.update(updated_at=datetime.now(timezone.utc).isoformat(),checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_action=next_action,exports=exports,final_sha256=dict(database=sha(KB/'graph.sqlite'),manifest=sha(KB/'manifest.json')),development_evaluation=evaluation,partial_pending_followups=7,semantic_completion=False,writes_to_knowledge_graph_by_this_finalizer=False);write(path,pub)
 path=AGENT/'curation/progress.json';progress=read(path);assert progress['graph_version'] in ['0.1.0-review-1cb86d91f463',VERSION]
 if progress['graph_version']!=VERSION:progress['previous_checkpoint']={k:progress[k] for k in ['graph_version','completed','next_action','evaluation']}
 outputs=['source-audit/stage-c-l045-'+n+'.json' for n in ['source-plan','source-applied','source-invariants','publication','verification']]+['upper/c_stage_l045.partial-resolutions.jsonl']
 progress['machine_outputs']=list(dict.fromkeys(progress['machine_outputs']+outputs))
 progress.update(updated_at=datetime.now(timezone.utc).isoformat(),graph_version=VERSION,counts=counts,claim_status_counts=status,figure_origin_counts=figure_status,unit_processing_status_counts=unit_status,semantic_completion=False,completed=['上册45课134段12页4图同模型四轮，41命题50证据12关系支撑，新增持币/等待2概念','6跨日及39日期空格规范，四图3后加1原发未核；原2708命题3761证据及全源原字/坐标/映射未改','持股/币是固定级别等待并观察当下类型分类，理论绝对保证未来点非期限/盈利/成交保证；最弱A1+A2+A3为三完整重叠5分类型的可能','MACD看面积非单柱缩短并看回轴，测度未给公式、矩形算法仍读者；5日线明确单边非盘整，不把降本或持有作免风险','4/16子分钟盘背和三段完成不升1分；1055至1346分段技能前提、4/17两点未命名、95%无统计、分笔两股不混600855图','三分钟买点保留读者原词/有限认可；600855 1345反问未补点名或个人回买建议；331媒体文章全为读者转引，非作者事实','八段博客及七段净资产/市值经济文章完整读作上下文；20年/2225不一致保留、历史消息和坏业绩预谋未外核','2749引用/33工程、6边界和7模块一致、5命题6图关联、240冻结开发题及同版本导出通过；7旧待核补充开放，92课阅读记录，余46至61共16课'],pending=['本批8待核见upper/c_stage_l045.pending.jsonl：持有等待保证/首中枢最弱分支/力度与MACD/5日线降本风险/子分钟案例点名/分解未答细节/2225历史消息与预谋/图源日期与身份','46至61共16课未完整语义审读；92课阅读记录含历史62至64，不等全书技术抽取或全部解释统一','240题完整类别/自然问题基线/生成回答质量/消融对抗及全书交叉审查未完成；43课316混合夹注段来源细分待核','独立Agent实际交付与Windows真实离线/PDF交互验收未完成'],checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_resume_anchor=next_anchor,next_action=next_action,coverage_caveat='45课134段12页4图同模型四轮，累计92课阅读记录含历史62至64，不称独立复核或全书完成。',evaluation=evaluation,previous_turn_classification='progress：45课134段4图、45日期修正及41条50证据发布；2749引用/240冻结开发题回归通过，余16课。')
 write(path,progress);print(json.dumps(dict(graph_version=VERSION,reviewed=2749,development_cases=240,remaining_lessons=16,next_anchor=next_anchor,semantic_completion=False),ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
