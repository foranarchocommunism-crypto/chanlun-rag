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
  ['intermediate-definition','中阴阶段从何时开始、何时结束，可以直接把第一次反向波动当新类型吗？','定义与完成边界',
    [cid('088','intermediate-stage-definition')],['到新走势类型确立前的过渡'],
    ['前类型背驰或盘整背驰后到新类型确立前，旧结束与新确立有过渡，初次反向不自动等于已确立。'],['任一反向波动都是新类型已确立。']],
  ['stage-shape','中阴截出来看像盘整，所以后面的新走势类型一定是盘整吗？','截取形态与类型',
    [cid('088','stage-shape-not-new-type')],['中阴阶段截取出来的形态'],
    ['只论截取阶段形态，作者明确否认新类型必盘整；V型也可能有该过渡。'],['截取盘整等同完整新类型必盘整。']],
  ['stage-direction','中阴结束就必定反转原方向，上涨后只能下跌吗？','延续与转折',
    [cid('088','stage-end-can-same-direction')],['中阴结束不一定反向'],
    ['也可上涨+盘整+上涨，同向和反向选择均存在。'],['结束充分保证反向。']],
  ['195-old-context','195后分析重心移到191之后，是全级别都可以删除之前的走势吗？','案例与级别边界',
    [cid('088','195-boundary-class-line'),cid('088','old-structure-persists-higher')],['该案例195三卖','191之前的走势仍在'],
    ['该例线段类层次转移重心，前走势仍在1分钟5分钟等层次起作用；195不作所有中阴的统一算法。'],['任意三卖都终结所有级别中阴。','全级别彻底丢弃旧结构。']],
  ['marks-completion','Xn、Yn等如何标？每加一段线段是否就能加一个1分钟标号？','符号及完成条件',
    [cid('088','level-mark-notation'),cid('088','compress-marks-after-completion')],['用Xn标线段','新1分钟走势结束才再增'],
    ['标号分层，Yn一类记号应等对应1分钟走势结束再增；191压到不足10仅例子。'],['线段每新增一个必添一个Yn。','固定时间到点自动添号。']],
  ['return-region','第88课底背驰反弹最低幅度，是回最后中枢自身区间还是其波动区间？','区间指代',
    [cid('088','nov12-return-last-oscillation-region')],['最后1分钟中枢的波动区间'],
    ['原词为波动区间，不能缩为中枢自身价格区间；当日最低目标达不保证更多反弹。'],['波动区间可静默换成ZD到ZG。','最低已达便保证后续反弹。']],
  ['214-level-gate','195退出到214考虑回补，5分钟以上操作者也必须同样买回吗？','操作级别条件',
    [cid('088','nov12-195-to-214-level-gate')],['214才值得考虑回补'],
    ['需接受1分钟操作，5分钟以上当次仍等待；值得考虑不是必须或保证收益。'],['所有级别214都必须无条件回补。']],
  ['internal-nesting','214三重区间套的内部笔已经由图谱独立重算了吗？','证据不足与核验范围',
    [cid('088','nov12-214-three-nesting')],['最后一重在213—214线段内部笔之间'],
    ['作者称三重，最后内部笔图未完整列出，独立重算及精确端点未验证。'],['图谱已经独立证明每一重及每一笔精确端点。']],
  ['retest-no-touch','对5462—5555颈线的反抽确认，价格至少必须碰到5462吗？','后文明确限制',
    [cid('088','retest-need-not-touch-neckline')],['不一定碰到5462'],
    ['11/12明说不必触5462，最弱可在颈线下折腾后走弱；不能自算未写的量度目标。'],['反抽必触5462才算原文所说反抽。']],
  ['month-versus-day','月顶分型5月均线，与日底分型5日线，可以当同一个条件吗？','时间工具与级别',
    [cid('088','nov7-monthly-top-case'),cid('088','nov13-daily-bottom-five-day')],['确认月顶分型','11月13日日底分型后'],
    ['两个日期、月顶5月线与日底5日线分别保留，均线观察不替代分型和笔形式条件。'],['5日线等同5月均线。','日底等于月顶确认。']],
  ['hypothetical-10000','作者说日线笔延伸到10000不反对，是预测必须涨到10000吗？','修辞与预测',
    [cid('088','nov14-daily-stroke-end-hold')],['延伸至10000只是其假设'],
    ['只作延伸假设，观察笔结束，并非目标或最低涨幅。'],['必须到10000才能结束反弹。']],
  ['petro-near-centers','中石油两个1分钟中枢太近，就已经确认升成更大中枢了吗？','可能与完成',
    [cid('088','nov9-petro-close-centers-not-certain')],['极可能二合一扩展'],
    ['作者极可能判断且由实际走势决定，未给仅凭近就确认升级的算法。'],['相邻或太近的两中枢一概已升级。']],
];

try {
  const cases=[],observations=[];
  for(const [slug,question,type,required,terms,conditions,forbidden] of specifications){
    const claims=required.map(id=>{const c=graph.getClaim(id);assert.ok(c,id);return c;});
    const plan=terms.map(query=>({command:'search',args:{query,limit:20}}));
    assert.ok(plan.length<=2);
    const expectedSources=claims.flatMap(c=>c.evidence.map(e=>({document_id:e.document_id,pdf_page:e.pdf_page,
      printed_page:e.printed_page,passage_id:e.passage_id,role:e.role,speaker:e.speaker})));
    cases.push({query_id:'g-b11-'+slug,query_text:question,query_type:type,
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
    observations.push({query_id:'g-b11-'+slug,automatic_retrieval_contract_pass:missing.length===0,missing,queries,
      generated_answer_scored:false,semantic_answer_faithfulness_automatically_proven:false});
  }
  writeFileSync(resolve(out,'stage-g-batch-11.cases.jsonl'),cases.map(x=>JSON.stringify(x)).join('\n')+'\n');
  const report={graph_version:graph.metadata.graph_version,executable_cases:cases.length,final_target_cases:240,
    gold_review_status:'model_reviewed_development',independent_test_set:false,human_gold_reviewed:false,
    retrieval_plan_contract_passed:observations.filter(x=>x.automatic_retrieval_contract_pass).length,observations,
    baselines:{source_keyword:'not_run_in_this_batch',vector:'not_implemented',structured:'query_plans_executed',hybrid:'not_run_in_this_batch'},
    generated_answers_evaluated:false,limits:['不是240题完整验收。','只执行取证计划，不将命中等同回答忠实度。','开发题整理时建立，非独立留出集。']};
  writeFileSync(resolve(out,'stage-g-batch-11.results.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({graph_version:report.graph_version,executable_cases:cases.length,retrieval_plan_contract_passed:report.retrieval_plan_contract_passed,failures:observations.filter(x=>!x.automatic_retrieval_contract_pass)}));
  if(report.retrieval_plan_contract_passed!==cases.length)process.exitCode=1;
} finally {graph.close();}
