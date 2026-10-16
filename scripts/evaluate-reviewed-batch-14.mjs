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
  ['zn-scope','第92课的Zn是20课Z走势段，还是88课周线编号？','同符号多义',
    [cid('092','axis-and-secondary-midpoints'), 'upper-l020-z-segment-definition'],['每个次级震荡区间的一半位置','称Z走势段'],
    ['92课是次级震荡中点，20课是Z走势段，88另有周线编号；按课文语境区分。'],['Zn在全图谱只有一个不变含义。']],
  ['cross-not-third','Zn越过A或B是否已经确认第三类买卖点？','必要非充分',
    [cid('092','boundary-cross-not-sufficient'),cid('092','eventual-boundary-cross-author-necessity')],['Zn超越A或B不意味着','Zn最终肯定超越'],
    ['作者断言最终须越界，但任一次越界不充分，可多次，只作预警。'],['每次越界自动三买三卖。']],
  ['extension-not-certain','Zn越界但没有三类点，就必然100%扩展中枢吗？','概率和例外',
    [cid('092','no-third-point-extension-probabilistic')],['未构成第三类买卖点，作者说一般'],
    ['作者说一般且极高概率，明确非100%，无独立统计。'],['作者经验概率即已验证无例外。']],
  ['smooth-not-exact','可按Zn平滑变动精确算出下一高低点吗？九点就是九根K线吗？','近似和取样边界',
    [cid('092','smooth-midpoint-only-rough-estimate'),cid('092','nine-observations-not-any-nine-bars')],['可大致预计下一Zn区间','Zn数据不会超过9个'],
    ['大致且有特殊情况，未给取样/误差完整算法；九是次级震荡中点数据语境，不是任意九根K线。'],['精确预测下一点无误差。','任意九K必升级。']],
  ['secondary-trend-conjunction','次级走势为趋势，就单独足以断言该中枢立刻变盘吗？','联合条件',
    [cid('092','secondary-trend-last-center-condition')],['次级震荡若为趋势且Zn相应配合'],
    ['还须Zn配合，所述特别条件有最后次级中枢在外及后继在其区间完成，配合未量化。'],['任意次级趋势足以变盘。']],
  ['unfinished-300','12月28日新5分钟中枢已经形成，是否图300也已完成且完整5分钟上涨确定？','对象状态区别',
    [cid('092','dec28-five-up-or-consolidation-open')],['图中的300尚未完成'],
    ['新中枢形成不等于完整上涨确定；作者仍分上涨或盘整且300未完。'],['图线已画到就是线段完成。']],
  ['zero-cost-conditions','(1,0)一出现，任何人都能不管盈亏先取本留利润吗？','状态与人群前提',
    [cid('093','zero-state-two-outcomes'),cid('093','conservative-withdraw-cost-leave-profit')],['零态信号本身不能唯一','且已有足够获利空间时'],
    ['零态仍两向；取本针对能力/时间/跑道偏好及足够周期、已有足够利润，不对无利润仓凭空留利润。'],['零态已确认反向。','亏损仓也一定能留下利润。']],
  ['skilled-no-rebuy','按93课先卖后买做短差，市场选择(-1,1)还须最后回补吗？','操作退出例外',
    [cid('093','skilled-sell-first-no-rebuy-down-state')],['最后一次不回补而退出'],
    ['能力较好者先卖后买，转下延时最后不回补；不可机械套所有震荡回补。'],['无论下延也必须回补。']],
  ['weekly-not-fixed-level','周线(1,1)到(1,0)必然对应30分钟上涨吗？用最后中枢判断的前提是什么？','周期与结构',
    [cid('093','weekly-state-corresponding-small-uptrend'),cid('093','confirmed-divergence-last-center-reference')],['级别可为1、5或30分钟','对应上涨已明确背驰并完全确认结束'],
    ['具体级别依图形，周K不固定对应；最后中枢判断限明确背驰且上涨完全确认结束支。'],['周K固定换算30分钟走势。','删去背驰确认前提。']],
  ['not-must-5675','剧本说5462—5675间看政策，是否大盘必须先到5675才允许改变？','作者明确澄清',
    [cid('092','jan10-gap-policy-conditional'),cid('093','jan18-not-must-reach-5675')],['取决于5462—5675区间','明确否定把此前剧本理解成'],
    ['观察区间不是必经上界，作者1/18明确反驳，并举5522已在区间内。'],['必须先到5675再允许下跌。']],
  ['stroke-not-segment','1月17日早盘急拉有向上笔，是否下跌线段已经破坏？类背驰是否都在两类中枢间？','配件与类对象范围',
    [cid('093','jan17-upstroke-not-segment-destroyed'),cid('093','jan17-single-segment-divergence-scope')],['早盘急拉只构成笔','不在两个类中枢之间'],
    ['笔反向不等段破坏；该日明确单线段内类背驰，和前日观察范围待核，非所有类背驰统一两中枢。'],['出现向上笔就破坏线段。','类背驰一律要求两类中枢。']],
  ['channel-future-not-confirmation','1月19日通道图画了四支点，能说明作者当时第四点已确认且通道必成功吗？','图来源和条件',
    [cid('093','jan19-channel-four-supports-conditional')],['若控制这次下跌才能形成第四'],
    ['正文第四仍条件，图含至2月未来行情属后加；不能反填已确认或成功保证。'],['未来图线证明当时第四点已完成。','通道为全市场无条件唯一解。']],
];

try {
  const cases=[],observations=[];
  for(const [slug,question,type,required,terms,conditions,forbidden] of specifications){
    const claims=required.map(id=>{const c=graph.getClaim(id);assert.ok(c,id);return c;});
    const plan=terms.map(query=>({command:'search',args:{query,limit:20}}));
    assert.ok(plan.length<=2);
    const expectedSources=claims.flatMap(c=>c.evidence.map(e=>({document_id:e.document_id,pdf_page:e.pdf_page,
      printed_page:e.printed_page,passage_id:e.passage_id,role:e.role,speaker:e.speaker})));
    cases.push({query_id:'g-b14-'+slug,query_text:question,query_type:type,
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
    observations.push({query_id:'g-b14-'+slug,automatic_retrieval_contract_pass:missing.length===0,missing,queries,
      generated_answer_scored:false,semantic_answer_faithfulness_automatically_proven:false});
  }
  writeFileSync(resolve(out,'stage-g-batch-14.cases.jsonl'),cases.map(x=>JSON.stringify(x)).join('\n')+'\n');
  const report={graph_version:graph.metadata.graph_version,executable_cases:cases.length,final_target_cases:240,
    gold_review_status:'model_reviewed_development',independent_test_set:false,human_gold_reviewed:false,
    retrieval_plan_contract_passed:observations.filter(x=>x.automatic_retrieval_contract_pass).length,observations,
    baselines:{source_keyword:'not_run_in_this_batch',vector:'not_implemented',structured:'query_plans_executed',hybrid:'not_run_in_this_batch'},
    generated_answers_evaluated:false,limits:['不是240题完整验收。','只执行取证计划，不将命中等同回答忠实度。','开发题整理时建立，非独立留出集。']};
  writeFileSync(resolve(out,'stage-g-batch-14.results.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({graph_version:report.graph_version,executable_cases:cases.length,retrieval_plan_contract_passed:report.retrieval_plan_contract_passed,failures:observations.filter(x=>!x.automatic_retrieval_contract_pass)}));
  if(report.retrieval_plan_contract_passed!==cases.length)process.exitCode=1;
} finally {graph.close();}
