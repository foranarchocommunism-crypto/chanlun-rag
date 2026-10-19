"""Finalize verified lesson41 publication; graph remains read-only."""
import hashlib,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';AUDIT=Path(__file__).resolve().parent
VERSION='0.1.0-review-ecd06e7bf4a5'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
 try:
  assert json.loads(db.execute("select value from metadata where key='graph_version'").fetchone()[0])==VERSION
  counts={t:db.execute(f'select count(*) from {t}').fetchone()[0] for t in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']}
  assert counts==dict(documents=2,pages=907,units=110,passages=9647,figures=528,concepts=278,claims=5253,evidence=6284,relations=464,reviews=2684)
  status=db.execute('select review_status,count(*) from claims group by review_status order by review_status').fetchall();assert dict(status)==dict(pending=2612,rejected=27,reviewed=2614)
  unit_status=db.execute('select processing_status,count(*) from units group by processing_status order by processing_status').fetchall();assert dict(unit_status)['extracted']==20
  figure_status=db.execute('select origin_status,count(*) from figures group by origin_status order by origin_status').fetchall()
  assert db.execute("select count(*) from evidence e join claims c on c.id=e.claim_id where c.review_status='reviewed'").fetchone()[0]==3645
  next_row=db.execute("select id,pdf_page,text from passages where unit_id='lesson-042' order by pdf_page,block_index,id limit 1").fetchone();assert next_row[2].startswith('教你炒股票42')
  known={r[0] for r in db.execute("select id from claims where review_status='reviewed'")}
 finally:db.close()
 assert read(KB/'manifest.json')['graph_version']==VERSION
 inv=read(AUDIT/'stage-c-l041-source-invariants.json');assert inv['pass'] and inv['graph_version']==VERSION and inv['original_reviewed_claims_unchanged']==2584 and inv['original_reviewed_evidence_unchanged']==3611
 verify=read(AUDIT/'stage-c-l041-verification.json');assert verify['pass'] and verify['graph_version']==VERSION and len(verify['checks'])==6 and len(verify['parity'])==7 and verify['intended_figure_links_checked']==dict(claims=0,associations=0,unique_figures=0)
 dev=read(AGENT/'evaluation/stage-g-development-current.results.json');assert dev['graph_version']==VERSION and dev['executable_development_cases']==dev['retrieval_plan_contract_passed']==240 and all(r['source_identity_matches_expected'] for r in dev['observations'])
 exports={}
 for name,number in [('claims',2614),('concepts',278),('relations',464)]:
  p=KB/'exports'/f'{name}.jsonl';rows=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()];assert len(rows)==number and all(r['graph_version']==VERSION for r in rows);exports[name]=dict(rows=number,graph_version=VERSION,sha256=sha(p))
 assert VERSION in (KB/'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150] and read(KB/'exports/coverage.json')['graph_version']==VERSION
 pending_ids={json.loads(l)['id'] for n in [38,40] for l in (AGENT/'curation/upper'/f'c_stage_l{n:03d}.pending.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()}
 changes=[
 ('upper-l038-c-stage-pending-third-first-effective-retest-subsub-completion',['no-chase-third-points-form-in-pullback-and-rebound','completion-question-basically-yes-qualified-not-equivalence','own-consolidation-end-may-enter-larger-consolidation'],'41补三类点回调/反弹及本级盘整结束仍可大盘整，完成原问仅基本认可；未补全次次级回试完成算法或改38首次有效定义。'),
 ('upper-l038-c-stage-pending-exit-internal-divergence-capacity-and-signal-vs-fall-threshold',['divergence-consolidation-only-turn-force-is-current','force-estimation-auxiliary-tools-promised-not-specified'],'41区分背驰/盘背转向与力度，后者依中枢系统/当下买卖且辅助另课；未补统一跌幅止损或足额成交模型。'),
 ('upper-l040-c-stage-pending-upgrade-multilayer-decomposition-and-allocation',['small-point-against-nonexhausted-large-trend-risk','pretrade-check-point-type-level-centers-market-sector'],'41加小点逆无衰竭大级续行风险及各级中枢分布分析，不抹40多层独立不等风险无关；未补N层配置数值。'),
 ('upper-l040-c-stage-pending-rhythm-price-stock-vs-long-term-fundamentals',['good-bad-stock-classification-as-entry-exit-timing','monthly-quarterly-large-sell-point-and-long-operation-exit','career-analogy-switch-not-from-buy-to-sell-single-stock-max-profit-view'],'41延续好坏时点修辞，超大级别卖点通常退出长期操作，单股最大利润仍未定义基准；不撤40长线基本面范围。'),
 ('upper-l040-c-stage-pending-underwater-buy-point-zero-cost-and-rhythm-safety-tensions',['capital-size-not-protection-same-zero-speed-rhetoric','small-point-against-nonexhausted-large-trend-risk','rhythm-before-precision-learning-and-practice'],'41强调规模不能保安全、小逆大有风险、节奏不取消有效点；未消39被套与40非买点或零成本安全强词范围张力。'),
 ]
 followups=[]
 for pending_id,slugs,finding in changes:
  ids=['upper-l041-c-stage-'+s for s in slugs];assert pending_id in pending_ids and all(i in known for i in ids)
  followups.append(dict(pending_id=pending_id,status='new_source_located_scope_still_pending',new_claim_ids=ids,finding=finding,global_pending_not_closed=True,graph_version=VERSION))
 (AGENT/'curation/upper/c_stage_l041.partial-resolutions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in followups),encoding='utf-8')
 checks=['30条Schema/引用/身份/坐标预检、67段台账和6页原页视觉核对，本课无图','原2584命题3611已复核证据未改；2文907页9647段528图逐行比对只17日期空格规范','33项Node工程测试单独重跑全部通过；初次并发校验期间1项database is locked，32通过，未改产品代码','2614命题全量引用校验0错误','6组语义/身份/范围边界、7组CLI/公共/桌面模块一致且只读哈希不变；本课零虚挂图','240冻结开发取证计划及已标注身份回归通过，无新题替换','2614命题/278概念/464关系及Markdown/coverage同版本导出','5条旧待核补充，原问题全部保持开放']
 not_run=['240题完整类别/自然问题基线/生成回答评分/消融对抗未完成，开发取证计划不替代完整G','42至61共20课完整语义及全书跨课/图文审查未完成','独立Agent打包后运行及Windows实际离线/缩放旋转跨页交互未验收']
 acceptance='41课30命题34证据发布；2614引用及240冻结开发题回归通过，7待核开放，全书及产品目标未完成。'
 next_anchor=next_row[0]+' / lesson-042';next_action=f'接续42课，实际PDF{next_row[1]}页标题，完整审读参与市场条件、心理和附带解盘答疑；保留源身份、限定与原图。'
 evaluation=dict(executable_development_cases=240,target=240,gold_review_status='model_reviewed_development',human_gold_reviewed=False,independent_test_set=False,generated_answers_scored=False,retrieval_plan_and_source_identity_passed_on_current_graph=240,full_stage_g_acceptance_complete=False,new_project_gold_cases_created_in_this_batch=0,note='同模型开发取证计划/身份回归，非独立金标准、回答质量或实际桌面验收。')
 path=AUDIT/'stage-c-l041-publication.json';pub=read(path);assert pub['graph_version']==VERSION and pub['formal_import']=='passed' and list(pub['batch_sha256'].values())==[sha(AGENT/'curation/upper/c_stage_l041.reviewed.jsonl')]
 pub.update(updated_at=datetime.now(timezone.utc).isoformat(),checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_action=next_action,exports=exports,final_sha256=dict(database=sha(KB/'graph.sqlite'),manifest=sha(KB/'manifest.json')),development_evaluation=evaluation,partial_pending_followups=5,semantic_completion=False,writes_to_knowledge_graph_by_this_finalizer=False);write(path,pub)
 path=AGENT/'curation/progress.json';progress=read(path);assert progress['graph_version'] in ['0.1.0-review-202e84864e97',VERSION]
 if progress['graph_version']!=VERSION:progress['previous_checkpoint']={k:progress[k] for k in ['graph_version','completed','next_action','evaluation']}
 outputs=['source-audit/stage-c-l041-'+n+'.json' for n in ['source-plan','source-applied','source-invariants','publication','verification']]+['upper/c_stage_l041.partial-resolutions.jsonl']
 progress['machine_outputs']=list(dict.fromkeys(progress['machine_outputs']+outputs))
 progress.update(updated_at=datetime.now(timezone.utc).isoformat(),graph_version=VERSION,counts=counts,claim_status_counts=status,figure_origin_counts=figure_status,unit_processing_status_counts=unit_status,semantic_completion=False,completed=['上册41课67段6页无图同模型四轮，30命题34证据10关系支撑发布，无新概念','17来源日期仅补日期/时刻空格，原字/身份/坐标未改，原2584命题3611证据逐行未改','节奏/精度与有效买卖点级别联合，三类点回调反弹；初学30分/5分限制及入背驰段必要非充分','小级逆无衰竭大级有续行风险，背驰盘背仅转向而幅度依中枢系统和当下力量，辅助工具未于本答给出','完成原问保留读者及基本上认可，本级盘整结束可入更大盘整；年线强词有范围，不推充要定理','八段经济附文及人生/货币答保留上下文，历史15分3272.41预测不变作者确认，单股最大利润不实证','2614引用/33工程单独重跑、6边界和7模块一致、240冻结开发题及同版本导出通过','5条旧待核补充均开放，累计88课有阅读记录（含历史62至64），余42至61共20课'],pending=['本批7待核见upper/c_stage_l041.pending.jsonl：纪律强词/初学级别入段/大级风险与力度/完成更大盘整/历史盘面/长线单股利润/附文日期','42至61共20课未完整语义审读；88课阅读记录不等全书技术抽取或全部解释统一','240题完整类别/自然问题基线/生成回答质量/消融对抗及全书交叉审查未完成','独立Agent实际交付与Windows真实离线/PDF交互验收未完成'],checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_resume_anchor=next_anchor,next_action=next_action,coverage_caveat='41课67段6页无图同模型四轮，累计88课阅读记录含历史62至64，不称独立复核或全书完成。',evaluation=evaluation,previous_turn_classification='progress：41课67段、17日期空格修正及30条34证据发布；2614引用/240冻结开发题回归通过，余20课。')
 write(path,progress);print(json.dumps(dict(graph_version=VERSION,reviewed=2614,development_cases=240,remaining_lessons=20,next_anchor=next_anchor,semantic_completion=False),ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
