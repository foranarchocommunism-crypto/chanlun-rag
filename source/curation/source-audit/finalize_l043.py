"""Finalize verified lesson43 publication; graph remains read-only."""
import hashlib,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';AUDIT=Path(__file__).resolve().parent
VERSION='0.1.0-review-3f0839731b9a'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
 try:
  assert json.loads(db.execute("select value from metadata where key='graph_version'").fetchone()[0])==VERSION
  counts={t:db.execute(f'select count(*) from {t}').fetchone()[0] for t in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']}
  assert counts==dict(documents=2,pages=907,units=110,passages=9647,figures=528,concepts=280,claims=5314,evidence=6365,relations=483,reviews=2745)
  status=db.execute('select review_status,count(*) from claims group by review_status order by review_status').fetchall();assert dict(status)==dict(pending=2612,rejected=27,reviewed=2675)
  unit_status=db.execute('select processing_status,count(*) from units group by processing_status order by processing_status').fetchall();assert dict(unit_status)['extracted']==18
  figure_status=db.execute('select origin_status,count(*) from figures group by origin_status order by origin_status').fetchall()
  assert db.execute("select count(*) from evidence e join claims c on c.id=e.claim_id where c.review_status='reviewed'").fetchone()[0]==3726
  next_row=db.execute("select id,pdf_page,text from passages where unit_id='lesson-044' order by pdf_page,block_index,id limit 1").fetchone();assert next_row[2].startswith('教你炒股票44')
  known={r[0] for r in db.execute("select id from claims where review_status='reviewed'")}
 finally:db.close()
 assert read(KB/'manifest.json')['graph_version']==VERSION
 inv=read(AUDIT/'stage-c-l043-source-invariants.json');assert inv['pass'] and inv['graph_version']==VERSION and inv['original_reviewed_claims_unchanged']==2643 and inv['original_reviewed_evidence_unchanged']==3688
 verify=read(AUDIT/'stage-c-l043-verification.json');assert verify['pass'] and verify['graph_version']==VERSION and len(verify['checks'])==6 and len(verify['parity'])==7 and verify['intended_figure_links_checked']==dict(claims=4,associations=4,unique_figures=2)
 dev=read(AGENT/'evaluation/stage-g-development-current.results.json');assert dev['graph_version']==VERSION and dev['executable_development_cases']==dev['retrieval_plan_contract_passed']==240 and all(r['source_identity_matches_expected'] for r in dev['observations'])
 exports={}
 for name,number in [('claims',2675),('concepts',280),('relations',483)]:
  p=KB/'exports'/f'{name}.jsonl';rows=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()];assert len(rows)==number and all(r['graph_version']==VERSION for r in rows);exports[name]=dict(rows=number,graph_version=VERSION,sha256=sha(p))
 assert VERSION in (KB/'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150] and read(KB/'exports/coverage.json')['graph_version']==VERSION
 pending_ids={json.loads(l)['id'] for n in [38,41,42] for l in (AGENT/'curation/upper'/f'c_stage_l{n:03d}.pending.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()}
 changes=[
 ('upper-l042-c-stage-pending-consolidation-divergence-must-break-direction-target-and-a-prime-B',['same-level-divergence-pulls-last-center-break-corresponding-extreme','smaller-turn-can-return-B-via-bigger-than-one-center','larger-center-after-small-divergence-may-break-up-extend'],'43分同级已成背驰回最后中枢和大级无背驰的小级转折，后者可向上；未把42盘背一定破短句等同标准背驰全部对象，a`+B/具体破位目标仍待核。'),
 ('upper-l042-c-stage-pending-daily-first-zero-return-must-rebuy-and-fourteen-stock-profit',['MACD-zero-return-up-initial-segment-yellow-white-high-unknown','strong-small-structure-new-yellow-white-high-no-divergence'],'43回轴再上先看候选段，未来线是否新高起初未知，小级强可取消候选；42特例一定买回完整条件及14只收益仍未核，不抹原强词。'),
 ('upper-l042-c-stage-pending-two-points-MACD-and-large-energy-not-fully-answered',['divergence-level-not-above-containing-current-move','entering-divergence-segment-not-guaranteed-divergence-small-extension','MACD-zero-return-up-initial-segment-yellow-white-high-unknown'],'43补候选段失效与级别区分，但未逐项指明42深圳两点MACD差异或通用能量/幅度公式。'),
 ('upper-l041-c-stage-pending-completion-qualified-acknowledgment-and-larger-consolidation',['own-divergence-terminates-original-type-next-same-or-higher','B-C-overlap-evolves-daily-not-already-formed','C-not-necessarily-complete-expanded-division-normal'],'43实际背驰终止原类型，B/C重合演化日线不等已成，C不一定完成；41基本认可非所有对象充要规则仍开放，夹注不作作者证明。'),
 ('upper-l041-c-stage-pending-opposing-small-level-and-force-amplitude-current',['one-minute-top-at-least-one-consolidation-or-down-may-rise-again','extreme-yearly-down-by-gradual-expansion-not-direct-minimum-cause','smaller-case-thirty-no-divergence-c-has-one-minute'],'43进一步分小级信号与当前大走势及转折级别，1分盘整后可继续涨，年线是逐步扩张非即时预言；41逆大级风险仍存。'),
 ('upper-l038-c-stage-pending-mechanical-branches-completion-equality-execution-and-profit',['rough-exit-after-break-wait-rebound-not-chase-down-can-still-new-high','fine-method-can-exit-before-break-mechanical-rougher','persistent-mechanical-super-return-author-claim'],'43粗法反弹退出/不杀跌且仍可无背新高，精法可提前但未给算法；坚持超级回报是未验证强词，38等值/成交/利润待核仍开放。'),
 ('upper-l038-c-stage-pending-same-level-unique-rule-not-global-unique-or-formal-proof',['decomposition-principle-no-higher-center-inside-one-type','C-thirty-no-overlap-B-original-thirty-unfinished-extends','overlap-original-part-daily-fixed-thirty-boundary-small-divergence'],'43给类型不得含更大中枢原则及B/C重合差异，固定30分可取小背驰点；未证明所有规则全局唯一或完整自动分解。'),
 ]
 followups=[]
 for pending_id,slugs,finding in changes:
  ids=['upper-l043-c-stage-'+s for s in slugs];assert pending_id in pending_ids and all(i in known for i in ids)
  followups.append(dict(pending_id=pending_id,status='new_source_located_scope_still_pending',new_claim_ids=ids,finding=finding,global_pending_not_closed=True,graph_version=VERSION))
 (AGENT/'curation/upper/c_stage_l043.partial-resolutions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in followups),encoding='utf-8')
 checks=['32条Schema/引用/身份/坐标预检，57段台账、6页及两幅整图视觉核对','原2643命题3688已复核证据未改；2文907页9647段528图逐行比对只15来源日期及2图备注授权变更','33项Node工程测试全部通过，串行运行','2675命题全量引用校验0错误','6组语义/身份/范围边界、7组CLI/公共/桌面模块一致且只读哈希不变；4命题4配图关联逐项确认','316夹注一字不入作者引文，注前/后独立原句精确定位；混合来源段细分仍待核','240冻结开发取证计划及已标注身份回归通过，无新题替换','2675命题/280概念/483关系及Markdown/coverage同版本导出','7条旧待核补充，原问题全部保持开放']
 not_run=['240题完整类别/自然问题基线/生成回答评分/消融对抗未完成，开发取证计划不替代完整G','44至61共18课完整语义及全书跨课/图文审查未完成，316混合夹注段身份细分仍待核','独立Agent打包后运行及Windows实际离线/缩放旋转跨页交互未验收']
 acceptance='43课32命题38证据发布；2675引用及240冻结开发题回归通过，6待核开放，全书及产品目标未完成。'
 next_anchor=next_row[0]+' / lesson-044';next_action=f'接续44课小级别背驰引发大级别转折，实际PDF{next_row[1]}页标题，完整审读必要/充分和最后次级别中枢三类点范围，交叉核对43回B路径。'
 evaluation=dict(executable_development_cases=240,target=240,gold_review_status='model_reviewed_development',human_gold_reviewed=False,independent_test_set=False,generated_answers_scored=False,retrieval_plan_and_source_identity_passed_on_current_graph=240,full_stage_g_acceptance_complete=False,new_project_gold_cases_created_in_this_batch=0,note='同模型开发取证计划/身份回归，非独立金标准、回答质量或实际桌面验收。')
 path=AUDIT/'stage-c-l043-publication.json';pub=read(path);assert pub['graph_version']==VERSION and pub['formal_import']=='passed' and list(pub['batch_sha256'].values())==[sha(AGENT/'curation/upper/c_stage_l043.reviewed.jsonl')]
 pub.update(updated_at=datetime.now(timezone.utc).isoformat(),checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_action=next_action,exports=exports,final_sha256=dict(database=sha(KB/'graph.sqlite'),manifest=sha(KB/'manifest.json')),development_evaluation=evaluation,partial_pending_followups=7,semantic_completion=False,writes_to_knowledge_graph_by_this_finalizer=False);write(path,pub)
 path=AGENT/'curation/progress.json';progress=read(path);assert progress['graph_version'] in ['0.1.0-review-25594b1ae8ac',VERSION]
 if progress['graph_version']!=VERSION:progress['previous_checkpoint']={k:progress[k] for k in ['graph_version','completed','next_action','evaluation']}
 outputs=['source-audit/stage-c-l043-'+n+'.json' for n in ['source-plan','source-applied','source-invariants','publication','verification']]+['upper/c_stage_l043.partial-resolutions.jsonl']
 progress['machine_outputs']=list(dict.fromkeys(progress['machine_outputs']+outputs))
 progress.update(updated_at=datetime.now(timezone.utc).isoformat(),graph_version=VERSION,counts=counts,claim_status_counts=status,figure_origin_counts=figure_status,unit_processing_status_counts=unit_status,semantic_completion=False,completed=['上册43课57段6页2图同模型四轮，32命题38证据10关系支撑，新增缠中说禅走势类型分解原则','4跨日及11日期空格规范，图1后加1原发未核；原2643命题3688证据及全源原字/坐标/映射未改','同级实际背驰与小级转大前提分开，1分盘整后可再涨、年线结果须逐步扩张；回0轴再上只先看候选段，小级强可消除大级候选','类型不得有更大中枢的两种归属原则；B/C无重合待原30分完成，有重合演化日线非已成，固定30分取小背驰点，C不一定完成','316第三人称整理夹注未入任何新作者引文，注前/后原句各自定位；混合段细分仍待核不假称完成','粗法跌破后待反弹/盘背不杀跌、精法可提前但未给算法，超级回报强词未实证；新股1/3读者与辅助K形态分开','2675引用/33工程、6边界和7模块一致、4命题4图关联、240冻结开发题及同版本导出通过','7条旧待核补充开放，累计90课有阅读记录（含历史62至64），余44至61共18课'],pending=['本批6待核见upper/c_stage_l043.pending.jsonl：两支级别/回B及C时序/MACD候选/粗精退出收益/历史盘面与K形态/混合夹注图源日期','44至61共18课未完整语义审读；90课阅读记录不等全书技术抽取或全部解释统一','240题完整类别/自然问题基线/生成回答质量/消融对抗及全书交叉审查未完成','独立Agent实际交付与Windows真实离线/PDF交互验收未完成'],checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_resume_anchor=next_anchor,next_action=next_action,coverage_caveat='43课57段6页2图同模型四轮，累计90课阅读记录含历史62至64，不称独立复核或全书完成。',evaluation=evaluation,previous_turn_classification='progress：43课57段2图、15日期修正及32条38证据发布；2675引用/240冻结开发题回归通过，余18课。')
 write(path,progress);print(json.dumps(dict(graph_version=VERSION,reviewed=2675,development_cases=240,remaining_lessons=18,next_anchor=next_anchor,semantic_completion=False),ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
