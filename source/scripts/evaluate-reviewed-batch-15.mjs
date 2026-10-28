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
  ['prepare-and-skip','当机立断是否见任何机会都必须无准备参与？','准备和选择',
    [cid('094','prepare-channel-capital-exit-before-entry'),cid('094','opportunity-may-be-skipped')],['预先设置退出边界条件','选择参与或放弃'],
    ['先选择且可放弃，参与前安排通道/资金/退出，等实际显现。'],['无退出计划必须参加所有机会。']],
  ['t1-no-same-day-exit','第94课线段机会存在，就保证T+1能获利退出吗？下午是否绝对安全？','可执行性限制',
    [cid('094','t1-same-day-exit-impossible-risk')],['买入后可能无法卖出'],
    ['买卖点可能同日完成，制度约束下买后卖不掉；早晚参考非下午安全保证。'],['结构机会等于可T+1赚钱。']],
  ['beginner-ma-conjunction','初学者均线约束是任意跌破5日线都走吗？','联合条件和人群',
    [cid('094','beginner-fractal-and-ma-exit')],['一旦分型后有效跌破须退出'],
    ['初学者、所选均线、分型后及有效跌破联合，熟练者可依严格分类。'],['所有人任意触均线即退出。']],
  ['jan22-versus-23','1月22日第二1分钟中枢已经确定，且没有回5100例外吗？','预期和事实',
    [cid('094','jan22-second-center-expected-exception'),cid('095','jan23-second-center-formed-best-third-buy')],['极可能是下跌第二中枢','第二1分钟中枢已形成'],
    ['1/22预期且有线段直接5100例外，1/23才称已形成，后期图不反填。'],['两日都已确定完成。']],
  ['zero-not-no-initial-money','0投入是否等于从没用初始资金、任何后来投入都绝对不准？','自述和明确补充',
    [cid('095','zero-investment-author-position-and-history'),cid('096','zero-cost-explicitly-relaxed-life-safe-money')],['上市后归还本金','明确说0成本投入不必那么严格'],
    ['95借款还本留利润是自述，96明确放宽允许不影响生活资本；非没有初始资金或余仓零风险。'],['零初始资金无借款责任。','96没有放宽。']],
  ['retry-not-unlimited','第96课允许输光后无限补资金再试吗？','再试条件',
    [cid('096','second-chance-after-full-failure-review'),cid('096','after-exit-years-learning-conditional-return')],['必须先剖析全部失败根源','经过多年学习历练'],
    ['再试先复盘且作最后尝试，仍败退出；后有多年学习后条件再回支，非无限补仓。'],['每次输光即自动充值。','永久删除多年学习再回原话。']],
  ['gambler-target','亏了便规定必须反弹到我的成本才走，按第96课是什么问题？','心态和结构边界',
    [cid('096','gambler-virtual-target-and-fomo')],['亏后要求反弹到自定价才走'],
    ['作者批评无视市场的虚拟目标和怕错过，与结构支持的退出计划区分；非临床诊断。'],['个人回本愿望就是市场必须发生的买卖点。']],
  ['wait-versus-early','94课等底确认与96课说确认后太晚，能删掉前者并要求所有人提前买吗？','能力范围分歧',
    [cid('094','jan22-unskilled-wait-bottom-confirmed'),cid('096','jan25-before-fractal-confirm-skill-context')],['没有相应技术者继续等日底分型确认','不是等分型已确认才操作'],
    ['保守无技术与两日具体有能力练习分别保留，实时范围待核，不能静默用后文覆盖。'],['所有人确认前无条件买。','前课原句已明确撤回。']],
  ['third-unfinished','1月24日数线段题，答案三个都是已经完成吗？','跨日问答',
    [cid('096','jan24-question-jan25-third-unfinished')],['第三段尚未完成'],
    ['1/24提问，1/25答第三未完，非三个均完成。'],['未来线图证明当日第三已完成。']],
  ['put-not-call-not-recommendation','580989教学例是认购权证推荐一般人追涨吗？','标的和参与身份',
    [cid('096','jan25-put-warrant-study-not-general-entry'),cid('096','jan28-put-entry-warning-and-exception')],['580989认沽日线','一般人不可介入'],
    ['认沽教学非认购推荐，一般人不介入，涨后不追；例外仅底时已持有且极高震荡技术。'],['所有人可在上涨后新追入。','认购与认沽同一类别。']],
  ['macd-not-divergence','只会MACD信号，就等于已经看出背驰了吗？','指标辅助',
    [cid('096','macd-assists-not-equals-divergence')],['不能以为MACD就等于背驰'],
    ['MACD辅助且需结构理解，不是背驰充分定义。'],['MACD就是背驰。']],
  ['three-steps-not-price-predictor','96课操作三步是否只要预测明天的精确点位时间就完成？','结构分类和执行',
    [cid('096','jan28-three-step-opportunity-recognition-operation')],['不预测点位时间'],
    ['输出各级机会、辨成立确认、操作前知下卖点/最坏/边界处理；不预测精确点位时间，能力另需磨练。'],['预测具体时价即可代替三步。','理论无遗漏已由项目独立证明。']],
];

try {
  const cases=[],observations=[];
  for(const [slug,question,type,required,terms,conditions,forbidden] of specifications){
    const claims=required.map(id=>{const c=graph.getClaim(id);assert.ok(c,id);return c;});
    const plan=terms.map(query=>({command:'search',args:{query,limit:20}}));
    assert.ok(plan.length<=2);
    const expectedSources=claims.flatMap(c=>c.evidence.map(e=>({document_id:e.document_id,pdf_page:e.pdf_page,
      printed_page:e.printed_page,passage_id:e.passage_id,role:e.role,speaker:e.speaker})));
    cases.push({query_id:'g-b15-'+slug,query_text:question,query_type:type,
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
    observations.push({query_id:'g-b15-'+slug,automatic_retrieval_contract_pass:missing.length===0,missing,queries,
      generated_answer_scored:false,semantic_answer_faithfulness_automatically_proven:false});
  }
  writeFileSync(resolve(out,'stage-g-batch-15.cases.jsonl'),cases.map(x=>JSON.stringify(x)).join('\n')+'\n');
  const report={graph_version:graph.metadata.graph_version,executable_cases:cases.length,final_target_cases:240,
    gold_review_status:'model_reviewed_development',independent_test_set:false,human_gold_reviewed:false,
    retrieval_plan_contract_passed:observations.filter(x=>x.automatic_retrieval_contract_pass).length,observations,
    baselines:{source_keyword:'not_run_in_this_batch',vector:'not_implemented',structured:'query_plans_executed',hybrid:'not_run_in_this_batch'},
    generated_answers_evaluated:false,limits:['不是240题完整验收。','只执行取证计划，不将命中等同回答忠实度。','开发题整理时建立，非独立留出集。']};
  writeFileSync(resolve(out,'stage-g-batch-15.results.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({graph_version:report.graph_version,executable_cases:cases.length,retrieval_plan_contract_passed:report.retrieval_plan_contract_passed,failures:observations.filter(x=>!x.automatic_retrieval_contract_pass)}));
  if(report.retrieval_plan_contract_passed!==cases.length)process.exitCode=1;
} finally {graph.close();}
