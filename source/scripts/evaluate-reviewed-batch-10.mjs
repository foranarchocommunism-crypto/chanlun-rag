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
  ['upshift-small-sell','大级别中枢上移中见小三卖，就必须当成大级别上涨结束吗？','跨级别前提',
    [cid('086','third-sell-in-larger-upshift')],['大级别中枢上移时'],
    ['小三卖主要警戒，关键看后续是否改变大级别上移；短差仍在小级别震荡意义。'],['小三卖必然等于大卖点。','可以完全无视三卖。']],
  ['downshift-shorting','第86课大级别下移中的小三卖没有操作价值，连卖空也算吗？','例外与语境',
    [cid('086','third-sell-in-larger-downshift')],['明确把卖空另算'],
    ['做多及迟到卖出语境，卖空另算，须看是否延续大级别下移。'],['任何方向任何账户都绝无操作价值。']],
  ['nesting-not-second-type','大买点后第二次小买点介入就是正式二买吗，而且必然最精确吗？','类别与量词',
    [cid('086','big-buy-small-buy-nesting'),cid('086','small-buy-break-large-structure-intact')],['往往是第二次介入机会','原大买点所构造的大级别结构'],
    ['第二次介入不是正式二买；任意小点不必在区间套，跌破小点仍须看大结构是否破坏。'],['第二次介入一概是第二类买点。','大买后任何小买都最精确或永不跌破。']],
  ['intermediate-large-sell','大买点后小卖点，能跳过中间是否有大卖点的检查吗？','联合条件',
    [cid('086','big-buy-small-sell-intermediate')],['若两点间有大卖点'],
    ['中间有大卖点归另一类；没有才考验原大结构，且后续小买强势须结构不破。'],['大买后小卖无条件保证下一小买获利。']],
  ['analogy-first-second','大中枢震荡次级别点有大操作意义，便是真正大级别一买二买吗？','比喻与严格定义',
    [cid('086','next-level-points-two-paths'),cid('086','analogy-not-large-first-second')],['大中枢震荡中的次级别','并非大级别真正第一'],
    ['次级别而非任意小级别，后续震荡或离开回抽；一二类只是比喻，不能升级身份。'],['操作意义大即形式级别必升级。','作者确认它们就是大级别一二类。']],
  ['small-level-wording','下册PDF226到底写不具有小级别还是大级别操作意义，能否默改？','原字疑点',
    [],[],['原页与原文确为小级别，相邻段另说次级别点有大意义；未有勘误则保留并列待核。'],['把小字静默替换成大字当原话。']],
  ['unformed-center','10月30日预期上方新中枢，后期图有后续行情，就能说当时已成吗？','图文与完成状态',
    [cid('086','oct30-new-center-required-uptrend'),cid('087','oct31-new-center-still-unformed')],['若不回到原1分钟中枢','当天仍未形成'],
    ['10/30不回原中枢且上方新中枢为条件，10/31仍未成；后期图不能倒填完成。'],['10/30已经无条件确认新中枢。','标题形成ing就是已经完成。']],
  ['late-sell-probability','195以后卖出仍可能继续跌，是否还能理论百分百保证？','概率与保证范围',
    [cid('087','nov2-late-sell-only-probability')],['195之后针对该次调整再卖已迟'],
    ['仍可能续跌，但针对该调整的迟卖已面临结束，只是概率不能100%保证；保留当次语境。'],['195之后绝不再跌。','迟卖仍获理论100%保证。']],
  ['t1-not-safe-floor','高开低走新股首下降线段结束后，41.7就绝对安全、T+1必赚吗？','交易边界',
    [cid('087','nov5-new-stock-first-down-segment'),cid('087','nov5-petro-417-not-safe-floor')],['高开低走新股','不能保证次日无下降线段跌穿41.7'],
    ['首段结束和分批是要求，仍不保证T+1绝对安全或次日不破41.7。'],['线段结束充分保证不跌破。','可见反弹必能T+1获利。']],
  ['class-third','中石油41.2的类第三类卖点，是严格1分钟中枢三卖吗？','最低结构与类比',
    [cid('087','nov6-petro-class-third-not-strict'),'lower-l064-line-below-center-is-analogy'],['类第三类卖点'],
    ['保留类中枢、类三卖、类背驰身份并联查64课最低结构边界；未来背驰及可T+1只是条件预期。'],['类中枢和类三卖等于严格最低级别中枢和三卖。']],
  ['three-days-buffer','5555争夺战至少3天和上下3%，可作为所有有效跌破的统一算法吗？','数值与适用范围',
    [cid('087','nov6-neckline-three-days-buffer')],['上下另有3%的缓冲'],
    ['当次一般经验，未说明收盘或盘中及两条件如何合用，不升级统一定义。'],['全书每个有效跌破均必须3天加3%。','3天或3%任一必充分确认。']],
  ['dream-zero-cost','第87课零负成本最安全能当作独立验证的零风险事实吗？','来源身份与绩效',
    [cid('087','cost-zero-stories-stance'),'lower-l067-buy-point-relative-zero-cost-safety'],['在自称“梦话”的庄家故事中','把零成本仅称为'],
    ['梦话轶事和足够资源前提保留，不认证账户或零风险；67课相对安全旧话不被覆盖。'],['知识库已验证零成本绝无风险。','匿名操盘故事账户收益已独立核验。']],
];

try {
  const cases=[],observations=[];
  for(const [slug,question,type,required,terms,conditions,forbidden] of specifications){
    const claims=required.map(id=>{const c=graph.getClaim(id);assert.ok(c,id);return c;});
    const special=slug==='small-level-wording';
    const plan=special?[{command:'page',args:{documentId:'volume_2.pdf',page:226}}]:
      terms.map(query=>({command:'search',args:{query,limit:20}}));
    assert.ok(plan.length<=2);
    const expectedSources=special?[7,8].map(block=>({document_id:'volume_2-5332cd1b6038',pdf_page:226,printed_page:'221',
      passage_id:`volume_2-5332cd1b6038-p0226-b00${block}`,role:'author_body',speaker:'缠中说禅'})):
      claims.flatMap(c=>c.evidence.map(e=>({document_id:e.document_id,pdf_page:e.pdf_page,printed_page:e.printed_page,
        passage_id:e.passage_id,role:e.role,speaker:e.speaker})));
    cases.push({query_id:'g-b10-'+slug,query_text:question,query_type:type,
      required_concepts:[...new Set(claims.flatMap(c=>c.concept_ids))],required_claims:required,
      expected_evidence_ids:[...new Set(claims.flatMap(c=>c.evidence.map(e=>e.id)))],
      expected_chapter_refs:[...new Set([...(special?['lesson-086']:[]),...claims.flatMap(c=>c.evidence.map(e=>e.unit_id))])],
      acceptable_answer_conditions:conditions,forbidden_inferences:forbidden,
      ambiguity_notes:special?['PDF原字衔接疑点未勘误，不以整理者直觉替字。']:claims.filter(c=>c.ambiguity_status!=='none').map(c=>c.ambiguity_status),
      difficulty:required.length>1||special?'medium':'basic',
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
    const missing=special?expectedSources.filter(s=>!foundPassages.has(s.passage_id)).map(s=>s.passage_id):required.filter(id=>!foundClaims.has(id));
    observations.push({query_id:'g-b10-'+slug,automatic_retrieval_contract_pass:missing.length===0,missing,queries,
      generated_answer_scored:false,semantic_answer_faithfulness_automatically_proven:false});
  }
  writeFileSync(resolve(out,'stage-g-batch-10.cases.jsonl'),cases.map(x=>JSON.stringify(x)).join('\n')+'\n');
  const report={graph_version:graph.metadata.graph_version,executable_cases:cases.length,final_target_cases:240,
    gold_review_status:'model_reviewed_development',independent_test_set:false,human_gold_reviewed:false,
    retrieval_plan_contract_passed:observations.filter(x=>x.automatic_retrieval_contract_pass).length,observations,
    baselines:{source_keyword:'not_run_in_this_batch',vector:'not_implemented',structured:'query_plans_executed',hybrid:'not_run_in_this_batch'},
    generated_answers_evaluated:false,limits:['不是240题完整验收。','只执行取证计划，不将命中等同回答忠实度。','开发题整理时建立，非独立留出集。']};
  writeFileSync(resolve(out,'stage-g-batch-10.results.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({graph_version:report.graph_version,executable_cases:cases.length,retrieval_plan_contract_passed:report.retrieval_plan_contract_passed,failures:observations.filter(x=>!x.automatic_retrieval_contract_pass)}));
  if(report.retrieval_plan_contract_passed!==cases.length)process.exitCode=1;
} finally {graph.close();}
