"""Finalize lesson51 checked publication without mutating the graph."""
import hashlib,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';AUDIT=Path(__file__).resolve().parent;VERSION='0.1.0-review-af327b82af12'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
 try:
  assert json.loads(db.execute("select value from metadata where key='graph_version'").fetchone()[0])==VERSION
  counts={t:db.execute(f'select count(*) from {t}').fetchone()[0] for t in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']};assert counts==dict(documents=2,pages=907,units=110,passages=9647,figures=528,concepts=299,claims=5606,evidence=6730,relations=571,reviews=3037)
  statuses=db.execute('select review_status,count(*) from claims group by review_status order by review_status').fetchall();assert dict(statuses)==dict(pending=2612,rejected=27,reviewed=2967)
  unit_status=db.execute('select processing_status,count(*) from units group by processing_status order by processing_status').fetchall();assert dict(unit_status)['extracted']==10
  figure_status=db.execute('select origin_status,count(*) from figures group by origin_status order by origin_status').fetchall()
  assert db.execute("select count(*) from evidence e join claims c on c.id=e.claim_id where c.review_status='reviewed'").fetchone()[0]==4091
  next_row=db.execute("select id,pdf_page,text from passages where unit_id='lesson-052' order by pdf_page,block_index,id limit 1").fetchone();assert next_row[0]=='volume_1-a53e99c37ca5-p0382-b007'
  known={r[0] for r in db.execute("select id from claims where review_status='reviewed'")}
 finally:db.close()
 assert read(KB/'manifest.json')['graph_version']==VERSION
 inv=read(AUDIT/'stage-c-l051-source-invariants.json');assert inv['pass'] and inv['graph_version']==VERSION and inv['original_reviewed_claims_unchanged']==2930 and inv['original_reviewed_evidence_unchanged']==4035
 verify=read(AUDIT/'stage-c-l051-verification.json');assert verify['pass'] and verify['graph_version']==VERSION and len(verify['checks'])==6 and len(verify['parity'])==7 and verify['intended_figure_links_checked']==dict(claims=8,associations=8,unique_figures=3,reader_context_figures_not_author_evidence=1)
 dev=read(AGENT/'evaluation/stage-g-development-current.results.json');assert dev['graph_version']==VERSION and dev['executable_development_cases']==240 and all(r['source_identity_matches_expected'] for r in dev['observations'])
 failures=[dict(query_id=r['query_id'],missing=r['missing'],queries=r['queries']) for r in dev['observations'] if not r['automatic_retrieval_contract_pass']];assert dev['retrieval_plan_contract_passed']==239 and [f['query_id'] for f in failures]==['g-b05-coincidence']
 exports={}
 for name,count in [('claims',2967),('concepts',299),('relations',571)]:
  p=KB/'exports'/f'{name}.jsonl';rows=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()];assert len(rows)==count and all(r['graph_version']==VERSION for r in rows);exports[name]=dict(rows=count,graph_version=VERSION,sha256=sha(p))
 assert VERSION in (KB/'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150] and read(KB/'exports/coverage.json')['graph_version']==VERSION
 pending_ids={json.loads(l)['id'] for n in [48,49,50] for l in (AGENT/'curation/upper'/f'c_stage_l{n:03d}.pending.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()}
 changes=[
 ('upper-l050-c-stage-pending-MACD-period-linearity-sensitivity-and-missing-formula',['MACD-first-up-zero-then-sideways-second-buy-auxiliary','B-needs-third-buy-otherwise-oscillation-consolidation-divergence','C2-incomplete-no-high-no-confirmed-third-buy'],'51二买MACD提示须结合结构，B要三买才结束/C2走势完成，不补50跨采样公式或仅指标独立判点，CCTV用5分看1分不是作者答。'),
 ('upper-l050-c-stage-pending-logic-confidence-geometric-guarantee-and-practice-criteria',['oscillation-profit-vs-unilateral-author-skill-claim','market-formed-by-forces-manager-not-always-controls-theory-scope-claim'],'51再述震荡获利强于单边/全走势技术包含为作者强语，技能限制仍未给独立实证/数学证明或模拟达标门槛。'),
 ('upper-l050-c-stage-pending-historical-centers-later-charts-and-reader-nine-segments',['may10-day-center-three-next-day-strength-branches','may17-4040-key-extension-versus-expansion-conditional','half-line-center-ultimate-level-form-still-forming'],'51日内三分支/4040扩展案例及最终级别形成中补充，不证明50CCTV九段解释；四图后加其中一图明确读者，仍不当作者图证。'),
 ('upper-l050-c-stage-pending-new-five-center-first-one-down-up-confirmation-execution',['B-needs-third-buy-otherwise-oscillation-consolidation-divergence','C2-incomplete-no-high-no-confirmed-third-buy','ultrashort-afternoon-third-buy-after-morning-extension-example'],'51重申B未三买则盘背震荡、回试类型须完成并给下午三买超短例，未完整补50将成新5枢实时判定/执行程序。'),
 ('upper-l049-c-stage-pending-post-third-buy-stage-vs-original-oscillation-and-small-to-large',['B-needs-third-buy-otherwise-oscillation-consolidation-divergence','oscillation-until-third-points-third-sell-wait-adequate-bottom'],'51原中枢三买前后及三卖后等够级别底背明确，不把三买后所有小级修正都算趋势已完或撤43/44小转大边界。'),
 ('upper-l048-c-stage-pending-C-extension-short-reply-no-endpoint-or-comparison-endorsement',['B-needs-third-buy-otherwise-oscillation-consolidation-divergence','C2-incomplete-no-high-no-confirmed-third-buy'],'51对B须三买和C2完成有独立补充，未逐项回答48B方向/c撇分解点/d比较，旧待核不关闭。'),
 ('upper-l050-c-stage-pending-macro-allegations-stock-claims-and-orderbook-not-yet-taught',['recommendation-self-reinforcing-flow-hypothetical-numbers','warning-against-paid-tips-author-opinion-not-legal-verdict'],'51荐股假设模型及付费批评与真实机构指控/法律分类隔开，未核50公司动机/收益，也未给盘口语言具体算法。'),
 ]
 followups=[]
 for pid,slugs,finding in changes:
  ids=['upper-l051-c-stage-'+s for s in slugs];assert pid in pending_ids and all(x in known for x in ids);followups.append(dict(pending_id=pid,status='new_source_located_scope_still_pending',new_claim_ids=ids,finding=finding,global_pending_not_closed=True,graph_version=VERSION))
 (AGENT/'curation/upper/c_stage_l051.partial-resolutions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in followups),encoding='utf-8')
 checks=['37条Schema/引用/身份/坐标预检，129段台账、12页4整图视觉复核','原2930命题4035证据未改；2文907页9647段528图逐行仅4跨日/12空格时间和4图来源授权变更','33项Node工程测试通过','2967命题全量引用校验0错误','6组语义/来源/条件边界与7组CLI/共享/桌面模块一致，8命题8关联3图和1读者图排除作者证据逐项核；查询只读哈希不变','冻结240题执行239计划通过/240来源身份通过，重合前20召回失败保留，未改题或核心排序','2967命题/299概念/571关系及Markdown/coverage同版本导出','7旧待核补来源仍开放，本批8待核；1429/图1249及360比例/三个月历史强语未静修或假装外证']
 not_run=['重合冻结前20召回回归未修，完整G类别/自然查询基线/生成回答质量/消融对抗未完成','52至61共10课未完整语义审读，全书图文/跨课及43混合夹注未全核','独立Agent真实打包运行及Windows离线/PDF缩放旋转跨页交互未验收']
 evaluation=dict(executable_development_cases=240,target=240,gold_review_status='model_reviewed_development',human_gold_reviewed=False,independent_test_set=False,generated_answers_scored=False,retrieval_plan_passed_on_current_graph=239,source_identity_passed_on_current_graph=240,open_retrieval_regressions=failures,full_stage_g_acceptance_complete=False,new_project_gold_cases_created_in_this_batch=0,note='固定题未改，全部身份通过；一条重合前20召回仍失败，分页找到不算原计划通过。')
 acceptance='51课37命题56证据发布；2967引用及33工程通过，冻结240题239计划/240身份通过，1条召回回归开放，语义及产品目标未完成。'
 next_anchor=next_row[0]+' / lesson-052';next_action='接续52课炒股票就是真正的学佛，实际PDF382页标题；完整审读预测/观察/参与及训练者比喻，分开哲学修辞与明确技术答疑、配图和案例。'
 p=AUDIT/'stage-c-l051-publication.json';pub=read(p);assert pub['graph_version']==VERSION and pub['formal_import']=='passed' and list(pub['batch_sha256'].values())==[sha(AGENT/'curation/upper/c_stage_l051.reviewed.jsonl')]
 pub.update(updated_at=datetime.now(timezone.utc).isoformat(),checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_action=next_action,exports=exports,final_sha256=dict(database=sha(KB/'graph.sqlite'),manifest=sha(KB/'manifest.json')),development_evaluation=evaluation,partial_pending_followups=7,semantic_completion=False,writes_to_knowledge_graph_by_this_finalizer=False);write(p,pub)
 p=AGENT/'curation/progress.json';progress=read(p);assert progress['graph_version'] in ['0.1.0-review-8edb32d94216',VERSION]
 if progress['graph_version']!=VERSION:progress['previous_checkpoint']={k:progress[k] for k in ['graph_version','completed','next_action','evaluation']}
 outputs=['source-audit/stage-c-l051-'+n+'.json' for n in ['source-plan','source-applied','source-invariants','publication','verification']]+['upper/c_stage_l051.partial-resolutions.jsonl'];progress['machine_outputs']=list(dict.fromkeys(progress['machine_outputs']+outputs))
 progress.update(updated_at=datetime.now(timezone.utc).isoformat(),graph_version=VERSION,counts=counts,claim_status_counts=statuses,figure_origin_counts=figure_status,unit_processing_status_counts=unit_status,semantic_completion=False,completed=['51课129段12页4整图同模型四轮，37命题56证据13关系支撑；新增短线荐股及1429点历史压力线两概念','四段归5/10解盘/12空格规范及四后图，原2930命题4035证据与全源原字/几何/映射未改','荐股5000人各2000股为1000万股是假设非命中率/真实盘面，会员/私募演化与全部收费者批评只保作者模型/观点非法律事实；16股涨幅表/999洗盘和300%不作实证','B需三买才结束，否则盘背震荡；C2所谈类型须完成，不只MACD/两个次级中枢；午后14点后拉起是例非全类筛选公式','1429历史月线拟合、360比例及4129/5479公式照录，图1249不修正文1429；至少3月/7月与迟早破线只作者历史强语，不给虚假证明或概率','日内强中弱和中期1/2线三模式分开，扩张/扩展原词保留；4040只特定扩展判断，周缺口10:17不定周背驰；最终级别/形式仍形成','2967引用/33工程/6边界/7模块及8命题8关联3图通过，第四图CCTV读者无作者证据，同版导出；240题239计划/240身份通过，1前20召回回归开放','7旧待核补来源仍开放；98课阅读记录含历史62至64，52至61共10课未完整审读'],pending=['本批8待核见upper/c_stage_l051.pending.jsonl；荐股模型/未核绩效、压力线/360/时限与图异字、B/C2完成及日内扩展案例全几何未全验证','52至61共10课未完整语义审读，98课阅读记录不等技术全抽取或解释统一','重合前20召回回归与完整G类别/自然基线/生成回答/消融对抗、43夹注和全书交叉未完成','独立Agent和Windows真实交付、离线与PDF交互未验收'],checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_resume_anchor=next_anchor,next_action=next_action,coverage_caveat='51课129段12页4图由同一代理四轮，累计98课阅读记录含历史62至64，不称独立复核或全书完成。',evaluation=evaluation,previous_turn_classification='progress：51课37命题56证据发布，2967引用/33工程通过；冻结题239/240且240身份通过，1召回回归开放，全书余10课。');write(p,progress)
 print(json.dumps(dict(graph_version=VERSION,reviewed=2967,development_cases=240,development_passed=239,remaining_lessons=10,next_anchor=next_anchor,semantic_completion=False),ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
