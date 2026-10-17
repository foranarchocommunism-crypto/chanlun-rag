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
 ['second-buy-three-forms','二买是否必须高于一买，二三买又能否在同一点？','二买三种情况',
  [cid('101','second-buy-below-first-permitted'),cid('101','second-third-coincide-strongest')],['比一买低完全可以','二三买合一'],
  ['明确允许低于一买；二三可合一，一二三依次抬高仅一般支，V形为一般而非保证。'],['二买低于一买一律无效。','二三买永远不重合。']],
 ['second-third-not-adjacent','二三买之间还能震荡吗？中间每个震荡买点都是严格新二买吗？','点类与宽称',
  [cid('101','second-third-not-necessarily-adjacent'),cid('101','intervening-oscillation-buys-loose-naming')],['二三之间可以','也可视为二买'],
  ['二三不必紧接；中间点一般不命名，也可宽称二买但严格首次回调定义未被自动改写。'],['二三之间不得有震荡。','每个震荡点都确认为正式第二类。']],
 ['strong-coincidence-not-guarantee','101说二三合一最强，是否保证大级别上涨、不能只扩张中枢？','跨课条件',
  [cid('101','second-third-coincide-strongest'),'upper-l021-c-stage-second-third-coincidence-no-guaranteed-trend'],['二买最强情况','重合不在理论上排除'],
  ['101一般V形与21理论不排除更大中枢扩张并列，仍须完整三买条件。'],['合一保证大级别上涨且无扩张分支。']],
 ['a0-not-any-algorithm','101说分型a0可随意设计，是否证明任意有歧义入口也合格？','递归入口范围',
  [cid('101','a0-arbitrary-design-author-wording'),'lower-l084-c-stage-fractal-only-recursion-start-optional'],['分型是递归的a0','替代递归入口仍能保证分解唯一性'],
  ['101随意措辞与84替代须保唯一前提并列，范围未形式统一，不许可任意歧义算法。'],['任意入口不需唯一性条件。']],
 ['unique-author-claim-not-proof','101、102的唯一分解和完美结构是否已经由项目形式证明？','作者主张与证明边界',
  [cid('101','recursive-unique-decomposition-author-claim'),cid('102','perfection-overall-structure-author-claim')],['任何行情唯一分解','完美整体结构'],
  ['可查作者归属和原句，形式证明未复现；数系类比不证明市场映射，结合律重组范围仍须保留。'],['项目已经形式证明所有行情唯一分解。']],
 ['control-current-not-intervention','102说走势可控，是说能预测或干预价格？','当下含义',
  [cid('102','classification-control-means-current-display')],['可控意思仅是走势'],
  ['原文说无须预测或干预，而按当下显示和操作原则操作，不保证价格或收益可控。'],['理论保证操控价格或预知唯一未来。']],
 ['three-layer-not-weighted-model','a1A1+a5A5+a30A30能直接编成已定义的加权收益模型吗？','表达式未定义边界',
  [cid('102','three-layer-expression-and-change-order')],['a1A1+a5A5+a30A30'],
  ['原文有表达式和大小级别改变顺序主张，未给系数意义，不能自补权重或收益公式。'],['系数权重数值已经由原文给全。']],
 ['timeline-third-sell-not-full-down','3/10三卖出现，是否当时1分钟下跌完整确认，3/11周线缺口也已补完？','日期与完成状态',
  [cid('102','mar10-third-sell-formed-minute-down-likely'),cid('102','mar11-gap-not-filled-minute-down-formed')],['周五1分钟中枢极可能','周线缺口还差1点'],
  ['3/10三卖已出而首下跌中枢极可能；3/11才称下跌已成，缺口尚差1点，不能混日期状态。'],['3/10完整下跌已确认且3/11缺口补完。']],
 ['one-minute-not-thirty-bottom','3/11有1分钟下跌、3/13盼30分钟反弹，是否真正30分钟背驰已完成？','级别与机会前提',
  [cid('102','mar11-minute-not-thirty-divergence'),cid('102','mar13-thirty-end-likely-five-not-formed')],['真正背驰还没有出现','最后5分钟下跌尚未形成'],
  ['3/11明确30真背驰未出；3/13机会是结束后的反弹，末5尚未成，不得推已结束或即将结束。'],['重要反弹机会等同30背驰已完成。']],
 ['sixty-chart-reference-frame','102说60分钟图连1分钟中枢都没形成，是否否定同篇之前的1分钟中枢？','图参考框架',
  [cid('102','mar17-sixty-chart-minute-center-reference')],['特意注明这是60分钟图'],
  ['照录60分钟图上的1分钟中枢语境，有参考框架歧义，不自动与前文严格1分钟对象合并或按周期换级别。'],['两处已核为完全同一对象而作者矛盾已被删除。']],
 ['explicit-stroke-correction','3/17反抽笔未出，3/19足够一笔，是否只因晚日期就覆盖旧判断？','明确纠正证据',
  [cid('102','mar17-retest-stroke-not-yet-author-state'),cid('102','mar19-explicit-correction-enough-stroke')],['反抽笔还未出现','作者明确纠正'],
  ['保留两日期原句，3/19有必须纠正明文且4431未到成类三卖；并非仅以时间自动覆盖定义。'],['后来日期本身就是撤回所有旧定义的证据。']],
 ['divergence-leg-fractal-stroke','3/19见60分钟底分型及背驰段，就能确认笔和完整底背驰都结束吗？','跨页与确认条件',
  [cid('102','mar19-divergence-leg-not-confirmed-bottom'),cid('102','mar19-3775-fractal-to-stroke-still-conditional')],['仍无明确区间套','3775关系到'],
  ['无明确区间套不能完全确认4下来走完；3775影响分型延伸笔，365/366跨页续句齐全，不能替代新笔完整条件。'],['底分型或背驰段出现就充分确认笔与最终底部。']],
];

try {
  const cases=[],observations=[];
  for(const [slug,question,type,required,terms,conditions,forbidden] of specifications){
    const claims=required.map(id=>{const c=graph.getClaim(id);assert.ok(c,id);return c;});
    const plan=terms.map(query=>({command:'search',args:{query,limit:20}}));
    assert.ok(plan.length<=2);
    const expectedSources=claims.flatMap(c=>c.evidence.map(e=>({document_id:e.document_id,pdf_page:e.pdf_page,
      printed_page:e.printed_page,passage_id:e.passage_id,role:e.role,speaker:e.speaker})));
    cases.push({query_id:'g-b18-'+slug,query_text:question,query_type:type,
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
    observations.push({query_id:'g-b18-'+slug,automatic_retrieval_contract_pass:missing.length===0,missing,queries,
      generated_answer_scored:false,semantic_answer_faithfulness_automatically_proven:false});
  }
  writeFileSync(resolve(out,'stage-g-batch-18.cases.jsonl'),cases.map(x=>JSON.stringify(x)).join('\n')+'\n');
  const report={graph_version:graph.metadata.graph_version,executable_cases:cases.length,final_target_cases:240,
    gold_review_status:'model_reviewed_development',independent_test_set:false,human_gold_reviewed:false,
    retrieval_plan_contract_passed:observations.filter(x=>x.automatic_retrieval_contract_pass).length,observations,
    baselines:{source_keyword:'not_run_in_this_batch',vector:'not_implemented',structured:'query_plans_executed',hybrid:'not_run_in_this_batch'},
    generated_answers_evaluated:false,limits:['不是240题完整验收。','只执行取证计划，不将命中等同回答忠实度。','开发题整理时建立，非独立留出集。']};
  writeFileSync(resolve(out,'stage-g-batch-18.results.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({graph_version:report.graph_version,executable_cases:cases.length,retrieval_plan_contract_passed:report.retrieval_plan_contract_passed,failures:observations.filter(x=>!x.automatic_retrieval_contract_pass)}));
  if(report.retrieval_plan_contract_passed!==cases.length)process.exitCode=1;
} finally {graph.close();}
