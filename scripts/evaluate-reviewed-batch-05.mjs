// Source-grounded development questions from the manually read lessons 21-24.
// These are model-reviewed evidence expectations, not an independent human gold.
import assert from 'node:assert/strict';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { KnowledgeGraph } from '../src/core.mjs';

const agent=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const graph=new KnowledgeGraph(resolve(agent,'../shared-knowledge/v0.1.0'));
const out=resolve(agent,'evaluation');mkdirSync(out,{recursive:true});
const cid=(lesson,slug)=>`upper-l${lesson}-c-stage-${slug}`;
const specifications=[
  ['coincidence','二买和三买在什么条件下重合，重合后能保证形成大级别上涨吗？','含条件的规则查询',
    [cid('021','second-third-coincidence-iff'),cid('021','second-third-coincidence-no-guaranteed-trend')],['重合'],
    ['第一买点出现后，次级别直接上破下跌最后中枢，再次级别回抽不触及。','重合仍不在理论上排除更大中枢扩张。'],['任意上破均构成二三买重合。','重合必定形成大级别上涨。']],
  ['same-level','上涨趋势确定后，第21课排除一买二买的说法能推广到更低级别吗？','定义及概念边界',
    [cid('021','confirmed-uptrend-only-third-buy')],['上涨趋势确定'],
    ['限定为该上涨趋势被讨论级别，不能排除更低级别买点。'],['任意级别均再无一买二买。']],
  ['platform','第三买点是否就是任意平台突破后的回档确认？','术语与近义消歧',
    [cid('023','third-buy-not-generic-platform-retest')],['平台突破'],
    ['作者否定这种宽泛等同，指出会纳入假突破且非所有平台突破均可参与。'],['作者认可读者的等价定义。']],
  ['three-levels','定位日线第三买点时，30分钟和5分钟分别起什么作用？','含条件的规则查询',
    [cid('023','daily-third-three-level-divergence-location')],['三个级别共同'],
    ['日线三买、30分钟回抽、5分钟背驰定位回抽低点，三个层次共同考察。'],['看5分钟图就等于操作级别为5分钟。']],
  ['standard-structure','标准MACD背驰只比较两波红柱面积就足够吗？','例外与条件不足',
    [cid('024','macd-abc-structure-premises'),cid('024','standard-macd-area-completion-test')],['用MACD判断标准背驰','标准MACD'],
    ['A/C同向趋势、B结构与更大中枢前提不能省略。','须保留C完成、C面积小于A及红绿方向。'],['任意两波柱子即可认定标准趋势背驰。']],
  ['consolidation','盘整背驰上破中枢后，回跌进入原中枢和未进入时如何分别处理？','含条件的规则查询',
    [cid('024','consolidation-breakout-first-exit-two-paths')],['C上破中枢'],
    ['先退出；不回原中枢于次级别一买回补并构成三买，回原中枢则继续盘整。'],['所有盘整背驰都持续大跌。','上破后无条件立即回补。']],
  ['b-center','本课标准趋势背驰发生后，回跌至少到哪里，盘整背驰能照搬吗？','定义及概念边界',
    [cid('024','standard-divergence-retrace-b-center')],['重新进入B段'],
    ['标准A/B/C结构的B段中枢是最低回跌界，盘整背驰另分路径。'],['回跌只许到B而不能更低。','盘整背驰一律至少回B。']],
  ['estimate','柱面积乘二的盘中估计能否当作C已经完成或百分之百准确的信号？','跨命题前提查证',
    [cid('024','macd-area-estimate-twice-existing'),cid('024','standard-macd-area-completion-test')],['面积乘二','标准MACD'],
    ['乘二为柱伸长力度变慢后的近似预估，标准判断仍要求C走势类型完成。'],['任意时刻面积乘二均为精确终值。','预估等同完成。']],
  ['zero-axis','MACD回抽零轴必须穿到零轴以下才算吗？','例外与条件不足',
    [cid('023','zero-axis-nearby-not-strict-cross')],['略在其上或下'],
    ['略在上或下不关键，关键是分明的两趋势比较；不能推广到远离零轴。'],['必须穿零或精确触零。']],
  ['end-low','第三买点的结束位置必然是整个次级别回拉最低价吗？','定义及概念边界',
    [cid('024','third-buy-end-not-total-low')],['整个次级别回拉最低位'],
    ['不一定，三段回拉C段可能不创新低；结束位置与全程最低位置分开。'],['第三买点一律取全回拉最低价格点。']],
  ['source-code','第24课所问600217的回复为何写6000217，工具是否静默改过原引文？','引文与来源核验',
    [cid('024','600217-new-high-first-zero-retest-case')],['6000217'],
    ['说明读者问题与作者回复的代码差异；引文保留6000217，歧义状态可见。'],['原文已经写成600217。','根据相邻图自动宣布作者原文已更正。']],
  ['unanswered','第24课PDF143读者问一个单位价格重叠是否中枢，紧接的作者回复明确认可了吗？','无答案与反幻觉',
    [cid('024','moving-average-macd-complement')],[],
    ['该次答复只说均线/MACD；不能用邻接回复宣称作者已回答单价重叠成立。'],['作者直接回答单价重叠一定构成中枢。']],
];

try{
  const cases=[],observations=[];
  for(const [slug,question,type,required,terms,conditions,forbidden] of specifications){
    const claims=required.map(id=>{const r=graph.getClaim(id);assert.ok(r,id);return r;});
    const special=slug==='unanswered';
    const plan=special?[{command:'page',args:{documentId:'volume_1.pdf',page:143}}]:terms.map(query=>({command:'search',args:{query,limit:20}}));
    const expectedSources=special?[
      {document_id:'volume_1-a53e99c37ca5',pdf_page:143,passage_id:'volume_1-a53e99c37ca5-p0143-b000',role:'reader'},
      {document_id:'volume_1-a53e99c37ca5',pdf_page:143,passage_id:'volume_1-a53e99c37ca5-p0143-b001',role:'author_reply'},
    ]:claims.flatMap(c=>c.evidence.map(e=>({document_id:e.document_id,pdf_page:e.pdf_page,printed_page:e.printed_page,passage_id:e.passage_id,role:e.role})));
    cases.push({query_id:'g-b05-'+slug,query_text:question,query_type:type,
      required_concepts:[...new Set(claims.flatMap(c=>c.concept_ids))],required_claims:required,
      expected_evidence_ids:[...new Set(claims.flatMap(c=>c.evidence.map(e=>e.id)))],
      expected_chapter_refs:[...new Set(claims.flatMap(c=>c.evidence.map(e=>e.unit_id)))],
      acceptable_answer_conditions:conditions,forbidden_inferences:forbidden,
      ambiguity_notes:special?['只评价该次回复，不能外推作者其他课程从未回答。']:claims.filter(c=>c.ambiguity_status!=='none').map(c=>c.ambiguity_status),
      difficulty:required.length>1||special?'medium':'basic',
      scoring_rubric:{retrieval:'取证计划须取得所列命题或页内发言。',answer:'回答全部保留条件且不作禁止推论；本次未运行回答生成评分。'},
      expected_source_refs:expectedSources,expected_speaker_roles:[...new Set(expectedSources.map(s=>s.role))],
      expected_kind:['explicit'],expected_review_status:['reviewed'],
      graph_version:graph.metadata.graph_version,gold_review_status:'model_reviewed_development',coverage_status:'executable',
      retrieval_plan:plan,budget:{max_queries:2,results_per_search:20},
      human_gold_reviewed:false,independent_test_set:false});
    const foundClaims=new Set(),foundPassages=new Set();const queries=[];
    for(const request of plan){
      const start=performance.now(),result=graph.query(request.command,request.args);
      const values=result.data.results??[];
      for(const value of values){foundClaims.add(value.id);for(const e of value.evidence??[])foundPassages.add(e.passage_id);}
      for(const p of result.data.passages??[])foundPassages.add(p.id);
      queries.push({request,total:result.data.total??result.data.passages?.length??null,truncated:result.data.truncated??false,elapsed_ms:performance.now()-start});
    }
    const missing=special?expectedSources.filter(s=>!foundPassages.has(s.passage_id)).map(s=>s.passage_id):required.filter(id=>!foundClaims.has(id));
    observations.push({query_id:'g-b05-'+slug,automatic_retrieval_contract_pass:missing.length===0,missing,queries,
      generated_answer_scored:false,semantic_answer_faithfulness_automatically_proven:false});
  }
  writeFileSync(resolve(out,'stage-g-batch-05.cases.jsonl'),cases.map(x=>JSON.stringify(x)).join('\n')+'\n');
  const report={graph_version:graph.metadata.graph_version,executable_cases:cases.length,final_target_cases:240,
    gold_review_status:'model_reviewed_development',independent_test_set:false,human_gold_reviewed:false,
    retrieval_plan_contract_passed:observations.filter(x=>x.automatic_retrieval_contract_pass).length,
    observations,baselines:{source_keyword:'not_run_in_this_batch',vector:'not_implemented',structured:'query_plans_executed',hybrid:'not_run_in_this_batch'},
    generated_answers_evaluated:false,limits:['不是240题完整验收。','只检查取证计划取得预定证据，不把检索命中等同回答忠实度或人工语义评分。','开发题在整理时建立，未作为独立留出集。']};
  writeFileSync(resolve(out,'stage-g-batch-05.results.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({graph_version:report.graph_version,executable_cases:cases.length,retrieval_plan_contract_passed:report.retrieval_plan_contract_passed,failures:observations.filter(x=>!x.automatic_retrieval_contract_pass)}));
}finally{graph.close();}
