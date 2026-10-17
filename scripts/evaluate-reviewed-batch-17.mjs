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
  ['general-vs-same-level','中阴不能明确划分，是说同级别划分也不能做，且第一个1分钟中枢锁定最终类型？','划分范围',
    [cid('099','general-not-same-level-partition')],['无法明确的是一般划分'],
    ['作者区分一般与同级别，初现1分钟中枢不锁定整体类型，年中枢也可由小连接。'],['同级别完全无法划分。','最终一定1分钟类型。']],
  ['recompose-two-cases','d+e+f与f+g+h两种中阴重组，可以不管是否成中枢直接互换吗？','结合律前提',
    [cid('099','associativity-absorb-old-last-center'),cid('099','post-divergence-fgh-preserve-old-type')],['a+b+c+(d+e+f)','a+b+c+d+e+(f+g+h)'],
    ['前者末类中枢可吸收需拆旧类上涨，后者fgh自身成中枢可保留旧；中枢确立优先，非任意三段。'],['任意三段可随意重组为中枢。']],
  ['complete-before-larger','每个5分钟K收盘就必产生30分钟中枢震荡吗？','结构完成前提',
    [cid('099','completed-type-next-at-least-larger-center')],['一个级别走势完成后'],
    ['作者条件是级别走势完成，例5分钟上涨结束至少30分钟震荡，非K时间收盘且至少非恰好。'],['任意5分钟K收盘充分。']],
  ['relative-danger','原下跌的中阴危险，对多头也一定坏吗？第二中枢能自动改倒数第二吗？','相对方向和未核编号',
    [cid('099','danger-relative-downtrend-good-for-longs'),cid('099','deeper-center-danger-reference')],['原下跌走势的中阴危险','文中所称第二甚至更后中枢'],
    ['危险相对原方向，原下跌回升强可利多；计数方向未明照原文，不自改倒数第二。'],['危险一律是多头亏损。','倒数第二已明确核定。']],
  ['return-scope-annotated','98课无论盘整背驰均回原中枢，是否与24课三买支完全无歧义？','跨课范围',
    [cid('098','divergence-return-then-classify'),'upper-l024-c-stage-standard-divergence-retrace-b-center'],['盘整背驰或真正背驰后','盘整背驰不适用同一个最低回跌要求'],
    ['保留98原话，已标跨课歧义；24区分盘整背驰三买和趋势回B，99另有完成类型前提，未强行统一。'],['98已明确撤回24。','所有盘整背驰无歧义必回原中枢。']],
  ['three-current-states','2/25已有1分钟下跌，是否5分钟和30分钟都已确认下跌新状态？','层级状态',
    [cid('100','feb25-three-layer-current-states')],['5分钟离首中枢向下移动'],
    ['1已成，5未三卖不能100%确认，30仍其最近中枢震荡；小状态不自动确认大状态。'],['三层同时因1已成而确认。']],
  ['five-to-thirty-chain','1分钟回拉成5分钟三卖，就立即确认30分钟三卖吗？','多层确认链',
    [cid('100','pullback-five-third-sell-or-oscillation'),cid('100','five-change-not-thirty-change-immediate')],['若成原5分钟三卖','本身不改变30分钟状态'],
    ['5三卖与否是5层两支；还须5下跌以后结束回拉构30三卖才改30状态。'],['5三卖直接等30三卖。']],
  ['capacity-vs-quantity','100课只需减少数量就能让任何人安全参与所有机会吗？','一般说法与能力门槛',
    [cid('100','ability-only-quantity-author-general-claim'),cid('100','capacity-gate-and-tiny-practice')],['不存在某一分类完全不能执行','处理不了可能三卖者不参加'],
    ['一般数量说与后文具体门槛并列待核，极小仓有意识练习不是消执行/T+1风险。'],['任何人任何仓位都安全可执行。']],
  ['fractal-not-stroke-levels','2/27过4331底分型成立，是否日笔已确，3/3突破4391就等周笔已确？','分型笔及周期',
    [cid('100','feb27-fractal-formed-stroke-upper-4391'),cid('100','mar3-week-fractal-4391-stroke-4695')],['4331使底分型成立','周底分型已现'],
    ['日底成还须4391站稳等笔条件，周底出现后周笔还须4695有效突破；非同一价格/周期。'],['底分型成就笔成。','4391等同周笔4695条件。']],
  ['macd-zero-scope','100课所有真正行情需MACD回0轴，是否明确撤回17课指标非必要？','同篇及跨课范围',
    [cid('100','macd-zero-necessary-wording-scope'),cid('100','macd-visual-auxiliary-not-special')],['所有真正行情展开都需MACD','理解其理论后这些描述完全没必要'],
    ['两种措辞和17辅助非必要并列有歧义，无明确全局撤回；结构条件不可省。'],['MACD零轴为已统一全图谱必要充分条件。']],
  ['branch-timeline','2/22第二第三都可，2/25就三支全排除并确定最终底了吗？','分支随时间',
    [cid('099','feb25-policy-force-third-branch-eliminated'),cid('100','feb27-second-branch-first-not-excluded')],['当日新低已排除前述第三支','第一支仍不能完全排除'],
    ['2/25筛第三，2/27看第二仍未全排第一；不能以未来图断当时已知底。'],['全部分支当时已确定唯一结果。']],
  ['third-buy-still-absent','3/3已突破4391且图有5F框，是否真三买已出、不可能回4331？','完成与后期图',
    [cid('100','mar3-a-plus-a-nine-segments-no-third-buy'),cid('100','mar4-return-center-third-buy-absent')],['真正三买尚未出现','当日已转向回中枢'],
    ['3/3真三买未出仍可回，3/4原文才登记实际回；图到3/4为后期不倒填确认。'],['突破价或画框就是真三买。','3/3已保证不回中枢。']],
];

try {
  const cases=[],observations=[];
  for(const [slug,question,type,required,terms,conditions,forbidden] of specifications){
    const claims=required.map(id=>{const c=graph.getClaim(id);assert.ok(c,id);return c;});
    const plan=terms.map(query=>({command:'search',args:{query,limit:20}}));
    assert.ok(plan.length<=2);
    const expectedSources=claims.flatMap(c=>c.evidence.map(e=>({document_id:e.document_id,pdf_page:e.pdf_page,
      printed_page:e.printed_page,passage_id:e.passage_id,role:e.role,speaker:e.speaker})));
    cases.push({query_id:'g-b17-'+slug,query_text:question,query_type:type,
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
    observations.push({query_id:'g-b17-'+slug,automatic_retrieval_contract_pass:missing.length===0,missing,queries,
      generated_answer_scored:false,semantic_answer_faithfulness_automatically_proven:false});
  }
  writeFileSync(resolve(out,'stage-g-batch-17.cases.jsonl'),cases.map(x=>JSON.stringify(x)).join('\n')+'\n');
  const report={graph_version:graph.metadata.graph_version,executable_cases:cases.length,final_target_cases:240,
    gold_review_status:'model_reviewed_development',independent_test_set:false,human_gold_reviewed:false,
    retrieval_plan_contract_passed:observations.filter(x=>x.automatic_retrieval_contract_pass).length,observations,
    baselines:{source_keyword:'not_run_in_this_batch',vector:'not_implemented',structured:'query_plans_executed',hybrid:'not_run_in_this_batch'},
    generated_answers_evaluated:false,limits:['不是240题完整验收。','只执行取证计划，不将命中等同回答忠实度。','开发题整理时建立，非独立留出集。']};
  writeFileSync(resolve(out,'stage-g-batch-17.results.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({graph_version:report.graph_version,executable_cases:cases.length,retrieval_plan_contract_passed:report.retrieval_plan_contract_passed,failures:observations.filter(x=>!x.automatic_retrieval_contract_pass)}));
  if(report.retrieval_plan_contract_passed!==cases.length)process.exitCode=1;
} finally {graph.close();}
