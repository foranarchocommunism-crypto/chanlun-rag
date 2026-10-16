// Model-reviewed development questions; retrieval checks do not score answers.
import assert from 'node:assert/strict';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { KnowledgeGraph } from '../src/core.mjs';

const agent=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const graph=new KnowledgeGraph(resolve(agent,'../shared-knowledge/v0.1.0'));
const out=resolve(agent,'evaluation');mkdirSync(out,{recursive:true});
const cid=(lesson,slug)=>`lower-l${lesson}-c-stage-${slug}`;
const specifications=[
  ['expert-deviation','97课允许偏离买卖点，是所有初学者也可随意忽略规则吗？','能力和例外',
    [cid('097','deviation-from-points-skilled-not-beginner')],['初学者先严格守规则'],
    ['一般守买卖点，作者偏移自述有数量/目的和熟练范围，未给任意偏移许可。'],['所有人可任意偏离。']],
  ['theory-not-application','97课说诊断1/10开方9/10，是否医学统计且懂分类就保证获利？','类比证据边界',
    [cid('097','application-hard-and-person-dependent'),cid('097','classification-foundation-not-application-skill')],['作者将识别与操作分别类比','不等于应用能力'],
    ['仅作者教学类比与修辞比例，不是医学实证；应用能力仍须练习。'],['比例为医学测量。','知道分类即有实盘获利能力。']],
  ['daily-forming-dates','1/31日中枢形成中与2/14盘整条件再成日中枢，能直接认为全都已完成？','跨日期层次',
    [cid('097','jan31-daily-center-forming'),cid('098','feb14-consolidation-daily-first-center-risk')],['一个日线级别中枢正在形成','若向上30分钟类型为盘整'],
    ['保留日期、形成中与条件支，不自动同一对象全完成或后句撤回前句。'],['两个日期严格中枢都全部完成且没有条件。']],
  ['grid-not-axis','1/31的3600就是日中枢中轴价吗？第二压力能改成5224吗？','数量和符号范围',
    [cid('097','jan31-large-oscillation-range-not-axis-3600'),cid('097','jan31-grid-450-and-5228')],['以3600点为幅度基础','5228第二压力'],
    ['3600为幅度尺度，当前中间位置另述；5228照录，不和别日5224/5209合并。'],['中轴价格确定3600。','按误差把5228改5224。']],
  ['revision-not-silence','97课如何支持中石油判断修改？只要后来不提就可全图谱自动确认吗？','明确修订和沉默',
    [cid('097','feb1-petro-explicit-revision-by-force'),cid('097','feb1-long-outlook-retained-conditional')],['因期货相关重要分力改变','作者又自述有些未再提'],
    ['有作者具体修改原话才记该30至24故事线索；未提未修改只在此自述，不构全局有效算法或必达价。'],['沉默足以所有命题自动确认。','24酒话自动必达目标。']],
  ['return-not-stop-or-news','背驰回原中枢是否必停并反向？没有利好则该次背驰不能成立吗？','保证边界和消息',
    [cid('098','divergence-return-then-classify'),cid('097','feb4-divergence-return-independent-news')],['回拉后应将可能情况完全分类','利好只是加强力度'],
    ['回拉后继续分类，不保证必停；该次背驰成立/已返回与利好力度分开，旧特定趋势条件仍保留。'],['必到即停并单边反转。','利好是背驰成立的必要条件。']],
  ['numbered-361-exception','2/4编号364后破坏线段是否无条件卖出？361是指数价格吗？','具体编号条件',
    [cid('098','feb4-364-break-and-361-exception')],['除非363起线段跌破361位置'],
    ['编号不是价格；作者该例在未跌破361时继续持有，演化类上涨只是极可能，不普遍任何破段不卖。'],['361为指数价格。','忽略例外任意段破坏一律卖或一律不卖。']],
  ['slightly-leading-vs-inverse','比大盘稍先的股票等同完全逆势吗？新股只要有新资金就都稳吗？','相对走势与联合前提',
    [cid('098','slightly-leading-not-fully-inverse'),cid('098','new-stock-selection-conjunctive')],['稍先于大盘而非完全逆势','新股作为另一选择'],
    ['完全逆势可能补跌；新股还需开得不太高、明显资金及一定级别向上三项，不保证稳定获利。'],['完全逆势必更安全。','新资金一项足够。']],
  ['position-not-empty','不确定时控制仓位就是必须全部空仓，并有统一百分比吗？','仓位定义范围',
    [cid('098','position-control-not-necessarily-empty')],['不一定空仓'],
    ['留足应付特殊情况反应空间，不一定空仓，无固定百分比。'],['所有人必须清仓。','作者给统一仓位比例。']],
  ['direction-not-uptrend','2/14后向上30分钟类型一定是上涨，且日下跌第一中枢已经完成吗？','方向和类型',
    [cid('098','feb14-next-thirty-up-direction-not-trend'),cid('098','feb14-consolidation-daily-first-center-risk')],['向上类型最坏可仅盘整','若向上30分钟类型为盘整'],
    ['尚在中阴，向上可仅盘整；后日中枢/下跌盘整为条件可能，非当时全已成。'],['向上就是上涨类型。','未来日K证明当时日下跌确定完成。']],
  ['stock-method-not-chase','600795估算9元、风险10%—15%是否当前现价和保证最大亏损，拉起后仍推荐买？','案例估算及声明',
    [cid('098','feb15-600795-risk-allocation-example'),cid('098','feb15-600795-method-not-buy-instruction')],['送股后的9元是估算','已经拉起后再买没意义'],
    ['历史送股估算不是现价，风险估计非上限，三买在构造；作者明确方法非一定买，涨后不追。'],['9元是未调整当前成交价。','风险上限保证15%。','拉起后一般人应追买。']],
  ['red-not-confirmed','2/18有MACD红柱就无忧且结构上涨已成吗？','指标与结构状态',
    [cid('098','feb18-red-histogram-await-confirmation'),cid('098','feb18-indicators-imprecise-center-primary')],['仍需确认','当天未构成线段类上涨'],
    ['红柱后仍看站位与能量，作者称指标底形分析不精确；未成类上涨而4575中枢已成，不能互换。'],['红柱足以确认反转。','线段类上涨当日已成。']],
];

try {
  const cases=[],observations=[];
  for(const [slug,question,type,required,terms,conditions,forbidden] of specifications){
    const claims=required.map(id=>{const c=graph.getClaim(id);assert.ok(c,id);return c;});
    const plan=terms.map(query=>({command:'search',args:{query,limit:20}}));
    assert.ok(plan.length<=2);
    const expectedSources=claims.flatMap(c=>c.evidence.map(e=>({document_id:e.document_id,pdf_page:e.pdf_page,
      printed_page:e.printed_page,passage_id:e.passage_id,role:e.role,speaker:e.speaker})));
    cases.push({query_id:'g-b16-'+slug,query_text:question,query_type:type,
      required_concepts:[...new Set(claims.flatMap(c=>c.concept_ids))],required_claims:required,
      expected_evidence_ids:[...new Set(claims.flatMap(c=>c.evidence.map(e=>e.id)))],
      expected_chapter_refs:[...new Set(claims.flatMap(c=>c.evidence.map(e=>e.unit_id)))],
      acceptable_answer_conditions:conditions,forbidden_inferences:forbidden,
      ambiguity_notes:claims.filter(c=>c.ambiguity_status!=='none').map(c=>c.ambiguity_status),
      difficulty:required.length>1?'medium':'basic',
      scoring_rubric:{retrieval:'取证计划取得所列命题或原页身份。',answer:'保留全部条件且不作禁止推论；本次未生成或评分回答。'},
      expected_source_refs:expectedSources,expected_speaker_roles:[...new Set(expectedSources.map(s=>s.role))],
      expected_kind:claims.length?['explicit']:[],expected_review_status:claims.length?['reviewed']:[],
      graph_version:graph.metadata.graph_version,gold_review_status:'model_reviewed_development',coverage_status:'executable',
      retrieval_plan:plan,budget:{max_queries:2,results_per_search:20},human_gold_reviewed:false,independent_test_set:false});
    const foundClaims=new Set(),foundPassages=new Set(),queries=[];
    for(const request of plan){
      const start=performance.now(),result=graph.query(request.command,request.args);
      for(const value of result.data.results??[]){foundClaims.add(value.id);for(const e of value.evidence??[])foundPassages.add(e.passage_id);}
      for(const p of result.data.passages??[])foundPassages.add(p.id);
      queries.push({request,total:result.data.total??result.data.passages?.length??null,truncated:result.data.truncated??false,elapsed_ms:performance.now()-start});
    }
    const missing=required.filter(id=>!foundClaims.has(id));
    observations.push({query_id:'g-b16-'+slug,automatic_retrieval_contract_pass:missing.length===0,missing,queries,
      generated_answer_scored:false,semantic_answer_faithfulness_automatically_proven:false});
  }
  writeFileSync(resolve(out,'stage-g-batch-16.cases.jsonl'),cases.map(x=>JSON.stringify(x)).join('\n')+'\n');
  const report={graph_version:graph.metadata.graph_version,executable_cases:cases.length,final_target_cases:240,
    gold_review_status:'model_reviewed_development',independent_test_set:false,human_gold_reviewed:false,
    retrieval_plan_contract_passed:observations.filter(x=>x.automatic_retrieval_contract_pass).length,observations,
    baselines:{source_keyword:'not_run_in_this_batch',vector:'not_implemented',structured:'query_plans_executed',hybrid:'not_run_in_this_batch'},
    generated_answers_evaluated:false,limits:['不是240题完整验收。','只执行取证计划，不将命中等同回答忠实度。','开发题整理时建立，非独立留出集。']};
  writeFileSync(resolve(out,'stage-g-batch-16.results.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({graph_version:report.graph_version,executable_cases:cases.length,retrieval_plan_contract_passed:report.retrieval_plan_contract_passed,failures:observations.filter(x=>!x.automatic_retrieval_contract_pass)}));
  if(report.retrieval_plan_contract_passed!==cases.length)process.exitCode=1;
} finally {graph.close();}
