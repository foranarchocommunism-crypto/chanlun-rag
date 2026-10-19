"""Finalize verified lesson44 publication; graph remains read-only."""
import hashlib,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];KB=AGENT.parent/'shared-knowledge/v0.1.0';AUDIT=Path(__file__).resolve().parent
VERSION='0.1.0-review-1cb86d91f463'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
 try:
  assert json.loads(db.execute("select value from metadata where key='graph_version'").fetchone()[0])==VERSION
  counts={t:db.execute(f'select count(*) from {t}').fetchone()[0] for t in ['documents','pages','units','passages','figures','concepts','claims','evidence','relations','reviews']}
  assert counts==dict(documents=2,pages=907,units=110,passages=9647,figures=528,concepts=281,claims=5347,evidence=6400,relations=489,reviews=2778)
  status=db.execute('select review_status,count(*) from claims group by review_status order by review_status').fetchall();assert dict(status)==dict(pending=2612,rejected=27,reviewed=2708)
  unit_status=db.execute('select processing_status,count(*) from units group by processing_status order by processing_status').fetchall();assert dict(unit_status)['extracted']==17
  figure_status=db.execute('select origin_status,count(*) from figures group by origin_status order by origin_status').fetchall()
  assert db.execute("select count(*) from evidence e join claims c on c.id=e.claim_id where c.review_status='reviewed'").fetchone()[0]==3761
  next_row=db.execute("select id,pdf_page,text from passages where unit_id='lesson-045' order by pdf_page,block_index,id limit 1").fetchone();assert next_row[2].startswith('教你炒股票45')
  known={r[0] for r in db.execute("select id from claims where review_status='reviewed'")}
 finally:db.close()
 assert read(KB/'manifest.json')['graph_version']==VERSION
 inv=read(AUDIT/'stage-c-l044-source-invariants.json');assert inv['pass'] and inv['graph_version']==VERSION and inv['original_reviewed_claims_unchanged']==2675 and inv['original_reviewed_evidence_unchanged']==3726
 verify=read(AUDIT/'stage-c-l044-verification.json');assert verify['pass'] and verify['graph_version']==VERSION and len(verify['checks'])==6 and len(verify['parity'])==7 and verify['intended_figure_links_checked']==dict(claims=4,associations=6,unique_figures=2)
 dev=read(AGENT/'evaluation/stage-g-development-current.results.json');assert dev['graph_version']==VERSION and dev['executable_development_cases']==dev['retrieval_plan_contract_passed']==240 and all(r['source_identity_matches_expected'] for r in dev['observations'])
 exports={}
 for name,number in [('claims',2708),('concepts',281),('relations',489)]:
  p=KB/'exports'/f'{name}.jsonl';rows=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()];assert len(rows)==number and all(r['graph_version']==VERSION for r in rows);exports[name]=dict(rows=number,graph_version=VERSION,sha256=sha(p))
 assert VERSION in (KB/'exports/reviewed-knowledge.md').read_text(encoding='utf-8')[:150] and read(KB/'exports/coverage.json')['graph_version']==VERSION
 pending_ids={json.loads(l)['id'] for n in [38,40,41,42,43] for l in (AGENT/'curation/upper'/f'c_stage_l{n:03d}.pending.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()}
 changes=[
 ('upper-l043-c-stage-pending-divergence-level-original-type-turn-not-one-to-one',['small-top-large-down-necessary-last-subcenter-third-sell','small-bottom-large-up-necessary-last-subcenter-third-buy','necessary-not-sufficient-third-sell-not-guaranteed-return-B'],'44明定末个次级中枢三卖/三买必要非充分，与43同级已成背驰不同；未补全部破位对象、强弱/幅度预测或任意1分必返大级。'),
 ('upper-l043-c-stage-pending-small-turn-return-B-necessary-path-and-C-overlap-timing',['c-contains-five-minute-center-for-B-third-buy-completion','one-minute-top-after-last-five-center-pulls-back-around-it','normal-last-subcenter-oscillation-not-large-turn','one-minute-just-example-five-and-subminute-same-principle'],'44展开c最后5分中枢正常震荡/破坏及三类必要点，1分仅例；回c`非回B，仍不保证回B或补43新C完成及日线区间。'),
 ('upper-l043-c-stage-pending-rough-exit-rebound-fine-before-break-and-super-return',['break-five-retest-type-high-exit-on-any-up-rebound','many-chips-part-at-last-five-center-third-sell-then-clear-on-boundary','larger-capital-part-at-one-minute-then-follow-rebuy-or-more-exit'],'44给具体5分回试类型高点破后回抽退出，筹码多可早出部分；未给所有相等/确认/成交/比例，也不验证43坚持超级回报。'),
 ('upper-l042-c-stage-pending-two-points-MACD-and-large-energy-not-fully-answered',['necessary-not-sufficient-third-sell-not-guaranteed-return-B','thirty-minute-not-all-out-at-every-one-minute-top','want-faster-five-minute-but-not-unskilled-parameter-unendorsed'],'44加必要非充分与按既定级别、小级非全出限制，MACD读者新参数未获认可；未逐项解42深圳两点差异或提供大级能量耗尽公式。'),
 ('upper-l041-c-stage-pending-beginner-level-frequency-and-divergence-stage-necessary-not-sufficient',['thirty-minute-operator-bears-five-minute-pullback-or-switches-level','one-minute-operation-if-capital-and-precision-procedure-same-levels-different','want-faster-five-minute-but-not-unskilled-parameter-unendorsed'],'44操作级别配容忍/资金精度，想快可降级但不熟练禁太小；不抹41初学30/5分及候选段必要非充分范围。'),
 ('upper-l040-c-stage-pending-upgrade-multilayer-decomposition-and-allocation',['many-chips-part-at-last-five-center-third-sell-then-clear-on-boundary','larger-capital-part-at-one-minute-then-follow-rebuy-or-more-exit'],'44解释容量大为何在小级先部分跟踪，而不是每卖点全出；无比例/规模阈值/流动性模型，不撤40各层独立信号却风险相关限制。'),
 ('upper-l038-c-stage-pending-mechanical-branches-completion-equality-execution-and-profit',['five-down-not-back-to-third-buy-retest-type-high-ignore','break-five-retest-type-high-exit-on-any-up-rebound','no-later-boundary-break-can-rebuy-short-spread','bottom-case-reverse-program-author-instruction-not-complete-algorithm'],'44给嵌套类型高点和破后回抽、部分后未再破可回补的程序，但相等/底部镜像/成交/利润仍不全，习作GG不补正文定义。'),
 ]
 followups=[]
 for pending_id,slugs,finding in changes:
  ids=['upper-l044-c-stage-'+s for s in slugs];assert pending_id in pending_ids and all(i in known for i in ids)
  followups.append(dict(pending_id=pending_id,status='new_source_located_scope_still_pending',new_claim_ids=ids,finding=finding,global_pending_not_closed=True,graph_version=VERSION))
 (AGENT/'curation/upper/c_stage_l044.partial-resolutions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in followups),encoding='utf-8')
 checks=['33条Schema/引用/身份/坐标预检，47段台账、5页及两幅完整习作图视觉核对','原2675命题3726已复核证据未改；2文907页9647段528图逐行比对只15来源日期和2图备注授权变更','33项Node工程测试全部通过，串行运行','2708命题全量引用校验0错误','6组语义/身份/范围边界、7组CLI/公共/桌面模块一致且只读哈希不变；4命题6配图关联逐项确认','两图署张大山习作，后加学习者图不变作者原图；GG/蓝线不代正文嵌套5分回试类型高点','240冻结开发取证计划及已标注身份回归通过，无新题替换','2708命题/281概念/489关系及Markdown/coverage同版本导出','7条旧待核补充，原问题全部保持开放']
 not_run=['240题完整类别/自然问题基线/生成回答评分/消融对抗未完成，开发取证计划不替代完整G','45至61共17课完整语义及全书跨课/图文审查未完成，43课316混合夹注段身份细分仍待核','独立Agent打包后运行及Windows实际离线/缩放旋转跨页交互未验收']
 acceptance='44课33命题35证据发布；2708引用及240冻结开发题回归通过，6待核开放，全书及产品目标未完成。'
 next_anchor=next_row[0]+' / lesson-045';next_action=f'接续45课持股与持币，两种最基本的操作，实际PDF{next_row[1]}页标题，完整审读等待/买卖点、持有与持币的级别条件及附带答疑。'
 evaluation=dict(executable_development_cases=240,target=240,gold_review_status='model_reviewed_development',human_gold_reviewed=False,independent_test_set=False,generated_answers_scored=False,retrieval_plan_and_source_identity_passed_on_current_graph=240,full_stage_g_acceptance_complete=False,new_project_gold_cases_created_in_this_batch=0,note='同模型开发取证计划/身份回归，非独立金标准、回答质量或实际桌面验收。')
 path=AUDIT/'stage-c-l044-publication.json';pub=read(path);assert pub['graph_version']==VERSION and pub['formal_import']=='passed' and list(pub['batch_sha256'].values())==[sha(AGENT/'curation/upper/c_stage_l044.reviewed.jsonl')]
 pub.update(updated_at=datetime.now(timezone.utc).isoformat(),checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_action=next_action,exports=exports,final_sha256=dict(database=sha(KB/'graph.sqlite'),manifest=sha(KB/'manifest.json')),development_evaluation=evaluation,partial_pending_followups=7,semantic_completion=False,writes_to_knowledge_graph_by_this_finalizer=False);write(path,pub)
 path=AGENT/'curation/progress.json';progress=read(path);assert progress['graph_version'] in ['0.1.0-review-3f0839731b9a',VERSION]
 if progress['graph_version']!=VERSION:progress['previous_checkpoint']={k:progress[k] for k in ['graph_version','completed','next_action','evaluation']}
 outputs=['source-audit/stage-c-l044-'+n+'.json' for n in ['source-plan','source-applied','source-invariants','publication','verification']]+['upper/c_stage_l044.partial-resolutions.jsonl']
 progress['machine_outputs']=list(dict.fromkeys(progress['machine_outputs']+outputs))
 progress.update(updated_at=datetime.now(timezone.utc).isoformat(),graph_version=VERSION,counts=counts,claim_status_counts=status,figure_origin_counts=figure_status,unit_processing_status_counts=unit_status,semantic_completion=False,completed=['上册44课47段5页2习作图同模型四轮，33命题35证据10关系支撑，新增缠中说禅小背驰-大转折定理','3跨日及12日期空格规范，两图署张大山习作记后加学习者图；原2675命题3726证据及全源原字/坐标/映射未改','末个次级别中枢三卖/三买仅必要非充分，回c`非必回B，1分只举例可推广5分/以下但不抹同级/小级两支','嵌套5分回试走势类型高点不替成GG/30分中枢上沿，先破再向上回抽退出；未回到/跌破相等细节及最强中枢名词仍待核','可全仓情形、筹码多末小中枢三卖先部分、容量大1分先部分跟踪分层；无固定比例或底部全镜像/成交算法','读者MACD5.10.10未获认可，改级须容量精度/熟练；操作正确先于更好结果；政策唯一风险/二线全启/20年牛市/三月收益均未实证','2708引用/33工程、6边界和7模块一致、4命题6图关联、240冻结开发题及同版本导出通过','7条旧待核补充开放，累计91课有阅读记录（含历史62至64），余45至61共17课'],pending=['本批6待核见upper/c_stage_l044.pending.jsonl：必要非充分/嵌套回试高点等值/容量分批及底镜像/读者参数与能力/换股站稳对象和历史风险强词/时间尾头与习作来源','45至61共17课未完整语义审读；91课阅读记录不等全书技术抽取或全部解释统一','240题完整类别/自然问题基线/生成回答质量/消融对抗及全书交叉审查未完成；43课316混合夹注段来源细分待核','独立Agent实际交付与Windows真实离线/PDF交互验收未完成'],checks_run=checks,checks_not_run=not_run,acceptance=acceptance,next_resume_anchor=next_anchor,next_action=next_action,coverage_caveat='44课47段5页2习作图同模型四轮，累计91课阅读记录含历史62至64，不称独立复核或全书完成。',evaluation=evaluation,previous_turn_classification='progress：44课47段2图、15日期修正及33条35证据发布；2708引用/240冻结开发题回归通过，余17课。')
 write(path,progress);print(json.dumps(dict(graph_version=VERSION,reviewed=2708,development_cases=240,remaining_lessons=17,next_anchor=next_anchor,semantic_completion=False),ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
