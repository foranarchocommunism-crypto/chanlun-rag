"""Finalize verified lesson42 publication; graph remains read-only."""
import hashlib,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';AUDIT=Path(__file__).resolve().parent
VERSION='0.1.0-review-25594b1ae8ac'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
 try:
  assert json.loads(db.execute("select value from metadata where key='graph_version'").fetchone()[0])==VERSION
  counts={t:db.execute(f'select count(*) from {t}').fetchone()[0] for t in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']}
  assert counts==dict(documents=2,pages=907,units=110,passages=9647,figures=528,concepts=279,claims=5282,evidence=6327,relations=474,reviews=2713)
  status=db.execute('select review_status,count(*) from claims group by review_status order by review_status').fetchall();assert dict(status)==dict(pending=2612,rejected=27,reviewed=2643)
  unit_status=db.execute('select processing_status,count(*) from units group by processing_status order by processing_status').fetchall();assert dict(unit_status)['extracted']==19
  figure_status=db.execute('select origin_status,count(*) from figures group by origin_status order by origin_status').fetchall()
  assert db.execute("select count(*) from evidence e join claims c on c.id=e.claim_id where c.review_status='reviewed'").fetchone()[0]==3688
  next_row=db.execute("select id,pdf_page,text from passages where unit_id='lesson-043' order by pdf_page,block_index,id limit 1").fetchone();assert next_row[2].startswith('教你炒股票43')
  known={r[0] for r in db.execute("select id from claims where review_status='reviewed'")}
 finally:db.close()
 assert read(KB/'manifest.json')['graph_version']==VERSION
 inv=read(AUDIT/'stage-c-l042-source-invariants.json');assert inv['pass'] and inv['graph_version']==VERSION and inv['original_reviewed_claims_unchanged']==2614 and inv['original_reviewed_evidence_unchanged']==3645
 verify=read(AUDIT/'stage-c-l042-verification.json');assert verify['pass'] and verify['graph_version']==VERSION and len(verify['checks'])==6 and len(verify['parity'])==7 and verify['intended_figure_links_checked']==dict(claims=5,associations=7,unique_figures=4)
 dev=read(AGENT/'evaluation/stage-g-development-current.results.json');assert dev['graph_version']==VERSION and dev['executable_development_cases']==dev['retrieval_plan_contract_passed']==240 and all(r['source_identity_matches_expected'] for r in dev['observations'])
 exports={}
 for name,number in [('claims',2643),('concepts',279),('relations',474)]:
  p=KB/'exports'/f'{name}.jsonl';rows=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()];assert len(rows)==number and all(r['graph_version']==VERSION for r in rows);exports[name]=dict(rows=number,graph_version=VERSION,sha256=sha(p))
 assert VERSION in (KB/'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150] and read(KB/'exports/coverage.json')['graph_version']==VERSION
 pending_ids={json.loads(l)['id'] for n in [39,40,41] for l in (AGENT/'curation/upper'/f'c_stage_l{n:03d}.pending.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()}
 changes=[
 ('upper-l041-c-stage-pending-rhythm-no-chase-third-point-and-strong-wording-scope',['market-suitability-current-not-permanent-first-adjust','self-awareness-daily-ten-minute-operations-and-psychology-review','first-daily-MACD-zero-return-rebuy-author-strong-case'],'42补十类当下行为及非永久、复盘训练，特例归零回补仍禁追涨；未补所有止损/三点必现或以强词保证结果。'),
 ('upper-l041-c-stage-pending-beginner-level-frequency-and-divergence-stage-necessary-not-sufficient',['weak-tech-five-day-midterm-ten-day-line-historical-fallback','weak-tech-thirty-minute-five-day-no-large-energy-formula'],'42继续不足者30分和5/10日线辅助，非全部参与者统一阈值或大级能量耗尽定义；41初学5分入段必要限制不撤。'),
 ('upper-l041-c-stage-pending-opposing-small-level-and-force-amplitude-current',['shenzhen-two-points-compare-one-minute-MACD-no-text-formula','weak-tech-thirty-minute-five-day-no-large-energy-formula'],'42两点幅度只让看1分MACD，耗尽问获能力/30分/5日建议；仍未给完整幅度与能量耗尽公式，接43查。'),
 ('upper-l039-c-stage-pending-Ai-pair-parity-protection-delay-k-and-unique-history',['consolidation-divergence-must-break-literal-target-unspecified','break-not-necessarily-consolidation-divergence-a-prime-plus-B'],'42说盘背一定跌破及破位非全盘背、a`+B，但短答不重述目标/方向/级别，待按39/40同级保护位核，不据此补k/相等/延后支。'),
 ('upper-l040-c-stage-pending-underwater-buy-point-zero-cost-and-rhythm-safety-tensions',['oscillation-lowers-cost-only-good-rhythm-author-view','weak-tech-five-day-midterm-ten-day-line-historical-fallback','tsinghua-negative-news-fundamental-reassurance-author-rhetoric'],'42震荡降本、5日不破安心和背景强词仍无实证安全保证，不消39总有被套与40被套非买点/零成本安全张力。'),
 ]
 followups=[]
 for pending_id,slugs,finding in changes:
  ids=['upper-l042-c-stage-'+s for s in slugs];assert pending_id in pending_ids and all(i in known for i in ids)
  followups.append(dict(pending_id=pending_id,status='new_source_located_scope_still_pending',new_claim_ids=ids,finding=finding,global_pending_not_closed=True,graph_version=VERSION))
 (AGENT/'curation/upper/c_stage_l042.partial-resolutions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in followups),encoding='utf-8')
 checks=['29条Schema/引用/身份/坐标预检、64段台账和6页及4幅整图视觉核对','原2614命题3645已复核证据未改；2文907页9647段528图逐行比对只24来源日期及4图来源备注授权变更','33项Node工程测试全部通过，串行运行避免验证期数据库锁','2643命题全量引用校验0错误','6组语义/身份/范围边界、7组CLI/公共/桌面模块一致且只读哈希不变；5命题7配图关联逐项确认','240冻结开发取证计划及已标注身份回归通过，无新题替换','2643命题/279概念/474关系及Markdown/coverage同版本导出','5条旧待核补充，原问题全部保持开放']
 not_run=['240题完整类别/自然问题基线/生成回答评分/消融对抗未完成，开发取证计划不替代完整G','43至61共19课完整语义及全书跨课/图文审查未完成','独立Agent打包后运行及Windows实际离线/缩放旋转跨页交互未验收']
 acceptance='42课29命题43证据发布；2643引用及240冻结开发题回归通过，7待核开放，全书及产品目标未完成。'
 next_anchor=next_row[0]+' / lesson-043';next_action=f'接续43课有关背驰的补习课，实际PDF{next_row[1]}页标题，完整审读背驰/转折级别及附带解盘答疑，交叉核对42必跌破对象与力度范围。'
 evaluation=dict(executable_development_cases=240,target=240,gold_review_status='model_reviewed_development',human_gold_reviewed=False,independent_test_set=False,generated_answers_scored=False,retrieval_plan_and_source_identity_passed_on_current_graph=240,full_stage_g_acceptance_complete=False,new_project_gold_cases_created_in_this_batch=0,note='同模型开发取证计划/身份回归，非独立金标准、回答质量或实际桌面验收。')
 path=AUDIT/'stage-c-l042-publication.json';pub=read(path);assert pub['graph_version']==VERSION and pub['formal_import']=='passed' and list(pub['batch_sha256'].values())==[sha(AGENT/'curation/upper/c_stage_l042.reviewed.jsonl')]
 pub.update(updated_at=datetime.now(timezone.utc).isoformat(),checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_action=next_action,exports=exports,final_sha256=dict(database=sha(KB/'graph.sqlite'),manifest=sha(KB/'manifest.json')),development_evaluation=evaluation,partial_pending_followups=5,semantic_completion=False,writes_to_knowledge_graph_by_this_finalizer=False);write(path,pub)
 path=AGENT/'curation/progress.json';progress=read(path);assert progress['graph_version'] in ['0.1.0-review-ecd06e7bf4a5',VERSION]
 if progress['graph_version']!=VERSION:progress['previous_checkpoint']={k:progress[k] for k in ['graph_version','completed','next_action','evaluation']}
 outputs=['source-audit/stage-c-l042-'+n+'.json' for n in ['source-plan','source-applied','source-invariants','publication','verification']]+['upper/c_stage_l042.partial-resolutions.jsonl']
 progress['machine_outputs']=list(dict.fromkeys(progress['machine_outputs']+outputs))
 progress.update(updated_at=datetime.now(timezone.utc).isoformat(),graph_version=VERSION,counts=counts,claim_status_counts=status,figure_origin_counts=figure_status,unit_processing_status_counts=unit_status,semantic_completion=False,completed=['上册42课64段6页4图同模型四轮，29命题43证据10关系支撑及历史密集区1新概念发布','6跨日及18日期空格规范，4图3后加1原发未核；原2614命题3645证据及全源原字/坐标/映射未改','十类行为每条联合结尾非永久限定，不作心理诊断；当下先调节及10分钟操作/心理复盘为作者训练观点','首次日线MACD回零一定回补为强个案非通用充分点；深圳两点只让看1分MACD，大级耗尽只给30分/5日/能力建议，均未补公式','盘背一定跌破、破位非全盘背和a`+B原式并存，目标方向/级别未明待跨39/40/43复核，不扩必破任意中枢下沿','600649周线历史密集区可检索，但多数被套/换手解释未核持仓账本；清华背景/付费系统反问不认证风险或工具效益','2643引用/33工程、6边界和7模块一致、5命题7配图关联、240冻结开发题及同版本导出通过','5条旧待核补充均开放，累计89课有阅读记录（含历史62至64），余43至61共19课'],pending=['本批7待核见upper/c_stage_l042.pending.jsonl：十类行为/历史均线与预测/日线回零强买回/两点MACD及能量/历史密集区/盘背破位与a`+B/图源日期实体','43至61共19课未完整语义审读；89课阅读记录不等全书技术抽取或全部解释统一','240题完整类别/自然问题基线/生成回答质量/消融对抗及全书交叉审查未完成','独立Agent实际交付与Windows真实离线/PDF交互验收未完成'],checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_resume_anchor=next_anchor,next_action=next_action,coverage_caveat='42课64段6页4图同模型四轮，累计89课阅读记录含历史62至64，不称独立复核或全书完成。',evaluation=evaluation,previous_turn_classification='progress：42课64段4图、24日期修正及29条43证据发布；2643引用/240冻结开发题回归通过，余19课。')
 write(path,progress);print(json.dumps(dict(graph_version=VERSION,reviewed=2643,development_cases=240,remaining_lessons=19,next_anchor=next_anchor,semantic_completion=False),ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
