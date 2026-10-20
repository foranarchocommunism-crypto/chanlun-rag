"""Finalize lesson50 checked publication without mutating the graph."""
import hashlib,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';AUDIT=Path(__file__).resolve().parent;VERSION='0.1.0-review-8edb32d94216'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
 try:
  assert json.loads(db.execute("select value from metadata where key='graph_version'").fetchone()[0])==VERSION
  counts={t:db.execute(f'select count(*) from {t}').fetchone()[0] for t in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']};assert counts==dict(documents=2,pages=907,units=110,passages=9647,figures=528,concepts=297,claims=5569,evidence=6674,relations=558,reviews=3000)
  statuses=db.execute('select review_status,count(*) from claims group by review_status order by review_status').fetchall();assert dict(statuses)==dict(pending=2612,rejected=27,reviewed=2930)
  unit_status=db.execute('select processing_status,count(*) from units group by processing_status order by processing_status').fetchall();assert dict(unit_status)['extracted']==11
  figure_status=db.execute('select origin_status,count(*) from figures group by origin_status order by origin_status').fetchall()
  assert db.execute("select count(*) from evidence e join claims c on c.id=e.claim_id where c.review_status='reviewed'").fetchone()[0]==4035
  next_row=db.execute("select id,pdf_page,text from passages where unit_id='lesson-051' order by pdf_page,block_index,id limit 1").fetchone();assert next_row[0]=='volume_1-a53e99c37ca5-p0371-b004'
  known={r[0] for r in db.execute("select id from claims where review_status='reviewed'")}
 finally:db.close()
 assert read(KB/'manifest.json')['graph_version']==VERSION
 inv=read(AUDIT/'stage-c-l050-source-invariants.json');assert inv['pass'] and inv['graph_version']==VERSION and inv['original_reviewed_claims_unchanged']==2899 and inv['original_reviewed_evidence_unchanged']==3999
 verify=read(AUDIT/'stage-c-l050-verification.json');assert verify['pass'] and verify['graph_version']==VERSION and len(verify['checks'])==6 and len(verify['parity'])==7 and verify['intended_figure_links_checked']==dict(claims=5,associations=5,unique_figures=2)
 dev=read(AGENT/'evaluation/stage-g-development-current.results.json');assert dev['graph_version']==VERSION and dev['executable_development_cases']==240 and all(r['source_identity_matches_expected'] for r in dev['observations'])
 failures=[dict(query_id=r['query_id'],missing=r['missing'],queries=r['queries']) for r in dev['observations'] if not r['automatic_retrieval_contract_pass']];assert dev['retrieval_plan_contract_passed']==239 and [f['query_id'] for f in failures]==['g-b05-coincidence']
 exports={}
 for name,count in [('claims',2930),('concepts',297),('relations',558)]:
  p=KB/'exports'/f'{name}.jsonl';rows=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()];assert len(rows)==count and all(r['graph_version']==VERSION for r in rows);exports[name]=dict(rows=count,graph_version=VERSION,sha256=sha(p))
 assert VERSION in (KB/'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150] and read(KB/'exports/coverage.json')['graph_version']==VERSION
 pending_ids={json.loads(l)['id'] for n in [48,49] for l in (AGENT/'curation/upper'/f'c_stage_l{n:03d}.pending.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()}
 changes=[
 ('upper-l049-c-stage-pending-MACD-order-areas-signal-level-and-length-wording',['MACD-periods-calculation-sensitivity-not-identical-output','structure-then-comparable-legs-then-MACD-period','choose-thirty-if-one-complex-two-areas-clearer'],'50再次明确先结构选段再周期指标、周期图不等信号级；未给跨采样线性证明/面积窗，也未静统一47柱长和49面积。'),
 ('upper-l049-c-stage-pending-oscillation-contraction-expansion-and-maximum-proof-assumptions',['understand-logic-not-belief-in-author-confidence','method-practice-geometric-profit-guarantee-author-only','very-long-pullback-premise-change-may-not-fully-return','unchanged-premises-author-certain-pullback-not-proof'],'50反盲信/逻辑与几何收益保证同时保，明示理论前提可变及未变一定回拉；仍未给49最大定理证明、全前提/执行约束。'),
 ('upper-l049-c-stage-pending-guaranteed-chip-safety-full-position-and-skill-execution',['study-existing-then-record-live-simulations-before-real-trades','novice-less-trades-small-practice-after-understanding-record','part-funds-practice-qualified-not-every-reader-detail'],'50模拟复盘/少量资金和部分练习为精度补充，不证明实际不丢筹码/全仓安全，未认可读者天天满仓全套计划。'),
 ('upper-l049-c-stage-pending-post-third-buy-stage-vs-original-oscillation-and-small-to-large',['five-minute-moving-no-new-five-center-until-it-ends','one-down-next-one-up-divergence-or-no-high-can-exit-before-five-center','small-to-large-operate-as-center-oscillation'],'50澄清新同级中枢出现则推移结束，先1下后1上背驰或不新高可先出/将成5枢；形成与完成、固定与激进模式具体执行仍未全。'),
 ('upper-l049-c-stage-pending-two-child-centers-connector-and-completion-unanswered',['apr27-five-center-expanded-thirty-3720-3761'],'50给已扩30分历史判断但九段1分仅CCTV读者解释未被作者认可，未用读者或后K补49更高级中枢完成答案。'),
 ('upper-l049-c-stage-pending-source-0931-0935-3745-chart-prices-and-later-frames',['apr27-break-3745-no-third-buy-oscillation','apr27-afternoon-compare-apr26-0930-MACD-no-new-high-sell','apr27-five-center-expanded-thirty-3720-3761'],'50另记4/26 09:30比较段与3720至3761，图上价格小数不静改；不解决49 0931/0935差异，图均晚于文字不能证预测。'),
 ('upper-l048-c-stage-pending-fear-position-skill-mean-line-and-sector-claims',['five-day-three-days-no-return-usual-imprecise-delayed-confirmation','short-five-day-medium-five-week-higher-skill-divergence-not-gap-guess','small-funds-under-million-more-than-five-too-many'],'50均线三天被明确为通常不精确/延迟法，技能与集中100万超5只仍只是一般建议；48恐慌半仓及45单边限制未被覆盖取消。'),
 ]
 followups=[]
 for pid,slugs,finding in changes:
  ids=['upper-l050-c-stage-'+s for s in slugs];assert pid in pending_ids and all(x in known for x in ids);followups.append(dict(pending_id=pid,status='new_source_located_scope_still_pending',new_claim_ids=ids,finding=finding,global_pending_not_closed=True,graph_version=VERSION))
 (AGENT/'curation/upper/c_stage_l050.partial-resolutions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in followups),encoding='utf-8')
 checks=['31条Schema/引用/身份/坐标预检，105段台账、10页2整图视觉审查','原2899命题3999证据未改；2文907页9647段528图逐行只28时间空格和2图来源授权变化','33项Node工程测试全部通过，串行运行','2930命题全量引用校验0错误','6组语义/身份/条件边界与7组CLI/共享/桌面模块一致，5命题5关联2图逐项核，查询只读哈希不变','240冻结题执行，239取证计划通过/240身份通过；重合前20召回失败保持开放，未改题或核心排序','2930命题/297概念/558关系及Markdown/coverage同版本导出','7旧待核补充来源仍开放；本批8待核']
 not_run=['冻结前20召回回归未修；完整G类别/自然查询基线/生成回答质量/消融对抗未完成','51至61共11课未完整语义审读；43混合夹注/全书图文与跨课未全复核','独立Agent打包真实执行与Windows离线/缩放旋转跨页交互未验收']
 evaluation=dict(executable_development_cases=240,target=240,gold_review_status='model_reviewed_development',human_gold_reviewed=False,independent_test_set=False,generated_answers_scored=False,retrieval_plan_passed_on_current_graph=239,source_identity_passed_on_current_graph=240,open_retrieval_regressions=failures,full_stage_g_acceptance_complete=False,new_project_gold_cases_created_in_this_batch=0,note='固定题未改，全部身份通过；一条重合前20召回仍失败，分页找到不算原计划通过。')
 acceptance='50课31命题36证据发布；2930引用及33工程通过，冻结240题239计划/240身份通过，1条召回回归开放，语义及产品目标未完成。'
 next_anchor=next_row[0]+' / lesson-051';next_action='接续51课短线股评荐股者的传销把戏，实际PDF371页标题；完整审读短线推荐/资金循环与可识别技术答疑，分开作者模型、读者问题和未验证市场指控。'
 p=AUDIT/'stage-c-l050-publication.json';pub=read(p);assert pub['graph_version']==VERSION and pub['formal_import']=='passed' and list(pub['batch_sha256'].values())==[sha(AGENT/'curation/upper/c_stage_l050.reviewed.jsonl')]
 pub.update(updated_at=datetime.now(timezone.utc).isoformat(),checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_action=next_action,exports=exports,final_sha256=dict(database=sha(KB/'graph.sqlite'),manifest=sha(KB/'manifest.json')),development_evaluation=evaluation,partial_pending_followups=7,semantic_completion=False,writes_to_knowledge_graph_by_this_finalizer=False);write(p,pub)
 p=AGENT/'curation/progress.json';progress=read(p);assert progress['graph_version'] in ['0.1.0-review-7fa30c4809d4',VERSION]
 if progress['graph_version']!=VERSION:progress['previous_checkpoint']={k:progress[k] for k in ['graph_version','completed','next_action','evaluation']}
 outputs=['source-audit/stage-c-l050-'+n+'.json' for n in ['source-plan','source-applied','source-invariants','publication','verification']]+['upper/c_stage_l050.partial-resolutions.jsonl'];progress['machine_outputs']=list(dict.fromkeys(progress['machine_outputs']+outputs))
 progress.update(updated_at=datetime.now(timezone.utc).isoformat(),graph_version=VERSION,counts=counts,claim_status_counts=statuses,figure_origin_counts=figure_status,unit_processing_status_counts=unit_status,semantic_completion=False,completed=['50课105段10页2整图同模型四轮，31命题36证据12关系支撑；新增模拟操作、操作节奏和理论成立前提3概念','28日期空格及两后图规范，原2899命题3999证据及所有原字/几何/映射未改','MACD先中枢走势选比较段再适宜周期，线性为作者解释非跨采样无损数值等价，观察图周期非信号级别','逻辑反盲信、静态/动态模拟逐次记录复盘/真实操作顺序明确；几何利润保证只保作者强语未证，足够把握无伪造阈值','特别长回拉前提可因制度规则改变而不完全，未变则作者断言一定，未抹例外或强语；未补全前提/时限/成交条件','均线三天拉不回通常不精确且滞后，不替最低/最高/收盘全口径，保45单边限制；997未认可具体卖点，100万以下超5股一般过多不当组合定理','新5分枢将成/已完分开，先1下1上背驰或不新高可先出不等任意1K；政治经济附文/公司与剧本主张保上下文，CCTV九段不冒作者证明','2930引用/33工程/6边界/7模块/5命题5关联2图通过，同版导出；240题239计划/240身份通过，1前20召回回归开放','7旧待核补来源仍开放；97课阅读记录含历史62至64，51至61共11课未完整审读'],pending=['本批8待核见upper/c_stage_l050.pending.jsonl；全理论前提/回拉期限、MACD公式、均线精确口径/新枢实时执行与几何保证未全验证','51至61共11课未完整语义审读，97课阅读记录不等技术全抽取/解释统一','重合冻结前20召回回归、完整G类别/自然查询基线/生成回答/消融对抗及43夹注/全书交叉未完成','独立Agent及Windows真实交付、离线/PDF交互未验收'],checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_resume_anchor=next_anchor,next_action=next_action,coverage_caveat='50课105段10页2图由同一代理四轮，累计97课阅读记录含历史62至64，不称独立复核或全书完成。',evaluation=evaluation,previous_turn_classification='progress：50课31命题36证据发布，2930引用/33工程通过；冻结题239/240且240身份通过，1召回回归开放，全书余11课。');write(p,progress)
 print(json.dumps(dict(graph_version=VERSION,reviewed=2930,development_cases=240,development_passed=239,remaining_lessons=11,next_anchor=next_anchor,semantic_completion=False),ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
