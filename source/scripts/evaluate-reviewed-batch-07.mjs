// Source-grounded development questions from the manually read lower lessons 75-77.
// These are model-reviewed evidence expectations, not an independent human gold.
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
  ['equal-boundaries','相邻K线只有一个对应端点相同，或两端都相同，算不算包含？可以加EPS吗？','定义及概念边界',
    [cid('075','equal-endpoint-inclusion'),cid('075','absolute-and-measurement-equality')],['对应的一端相同','软件显示到最后一位'],
    ['对应一端或两端相同均为包含；须绝对相同，软件最后小数相同。'],['任意高点碰低点都算包含。','作者在此规定浮点EPS容差。']],
  ['one-price-limit','一字涨停合成一根K线后，作者是否说任何定义下都没有最小级别中枢？','跨命题前提查证',
    [cid('075','one-price-limit-two-constructions')],['全天未打开的一字涨停'],
    ['最初入口有最小级别中枢；分型构造入口不构成分型与笔，两种入口分开。'],['任何入口下一字涨停都绝无最小级别中枢。']],
  ['uncompleted','三买后的上涨只稍回落又上涨，能拿中途段与已完成离开段比较盘整背驰吗？','例外与条件不足',
    [cid('075','unfinished-not-compare-completed')],['尚未走完的段'],
    ['未走完不能与已完成段比较；结合区间套避免该误判。'],['任何中途小回落都证实盘整背驰已经完成。']],
  ['return-force','第三类买卖点只要回拉力度比离开小，就必然成立吗？回拉没出现能提前判定吗？','含条件的规则查询',
    [cid('076','third-return-force-necessary')],['才可能形成'],
    ['回拉小于离开只是必要条件，回拉未出现不可预判，还须相应定义条件。'],['力度小于就是三买充分条件。','只见离开大就能宣布三买已成立。']],
  ['gap-complete','缺口区间触及任意一点就算全部回补吗？缺口是否必须三天回补？','定义及概念边界',
    [cid('077','gap-fill-entire-interval-no-deadline')],['最终全部再次出现成交'],
    ['回补指全缺口区间最终全部再次成交；可下一K，也可永不回补。'],['触及任意点即全部回补。','全部缺口三日必补。']],
  ['gap-level','日K线上的衰竭缺口必然对应日线走势及周线调整吗？','术语与近义消歧',
    [cid('077','exhaustion-higher-adjustment'),cid('077','period-not-trend-level')],['调整级别至少大于','不能直接按缺口'],
    ['调整对应走势类型级别，日K周期不自动等同日线趋势；须回补且不创原方向极值并转折。'],['缺口K线周期直接决定走势级别。']],
  ['old-stroke','第77课旧笔标准只要求相邻顶底吗？还缺什么联合条件？','含条件的规则查询',
    [cid('077','old-stroke-joint-conditions')],['第77课笔须'],
    ['一顶一底、处理后的归属、至少一根独立K线、顶最高K区间部分高于底最低K区间。'],['任意相邻顶底都成为旧标准笔。','第77课已经用后课新笔替换原笔。']],
  ['proof-wording','第77课唯一性证明第二个底分支原文是不低于还是不高于？项目证明已经通过了吗？','引文与来源核验',
    [cid('077','stroke-uniqueness-author-assertion')],['两处分支原字重叠'],
    ['原文不低于；与此前高于分支重叠，歧义单列，作者主张唯一不等于项目形式验证。'],['原文已更正成不高于。','项目验证全部分支完备。']],
  ['first-second','所有线段破坏都必须找第二特征序列吗？第二种找不到又怎样？','含条件的规则查询',
    [cid('076','classify-before-second-sequence')],['应先区分类别'],
    ['先分第一二种；第一种无需第二序列，第二种找不到则原段未破坏。'],['第一种也必须第二序列。','没有第二序列就能宣布第二种已确认破坏。']],
  ['provisional-abc','第77课A、B、C在破坏关系确认前都已经是完成线段吗？','状态及歧义',
    [cid('077','second-case-abc-provisional')],['假设称呼'],
    ['是先按结合律命名的假设，括号满足基本性质，确认与基本性质分别处理。'],['标了A/B/C就均已完成。']],
  ['later-annotation','第77课81—82图中蓝字新笔是否就是作者9月5日原定义？','图文关系与来源',
    [cid('077','81-82-rebound-segment-actual-branch')],['第一笔破坏、A及该反弹'],
    ['正文反弹成段破坏A支持组合；蓝字新笔后加，9月18日新条件不自动覆盖9月5日旧标准。'],['蓝字是第77课作者当时新笔原话。','靠蓝字证明当课原笔条件改变。']],
  ['pair-unanswered','第76课79—80该与77—78还是75—76比较，作者这次回复明选了哪对？','无答案与反幻觉',
    [cid('076','trend-before-high-amount')],[],
    ['只说看有没有趋势、与创新高多少无关；该次回复没有明选段对。'],['作者明确指定其中一对。','创新高太少自动决定比较对。']],
];

try{
  const cases=[],observations=[];
  for(const [slug,question,type,required,terms,conditions,forbidden] of specifications){
    const claims=required.map(id=>{const r=graph.getClaim(id);assert.ok(r,id);return r;});
    const special=slug==='pair-unanswered';
    const plan=special?[{command:'page',args:{documentId:'volume_2.pdf',page:136}}]:terms.map(query=>({command:'search',args:{query,limit:20}}));
    const expectedSources=special?[
      {document_id:'volume_2-5332cd1b6038',pdf_page:136,passage_id:'volume_2-5332cd1b6038-p0136-b013',role:'reader'},
      {document_id:'volume_2-5332cd1b6038',pdf_page:136,passage_id:'volume_2-5332cd1b6038-p0136-b014',role:'author_reply'},
    ]:claims.flatMap(c=>c.evidence.map(e=>({document_id:e.document_id,pdf_page:e.pdf_page,printed_page:e.printed_page,passage_id:e.passage_id,role:e.role})));
    cases.push({query_id:'g-b07-'+slug,query_text:question,query_type:type,
      required_concepts:[...new Set(claims.flatMap(c=>c.concept_ids))],required_claims:required,
      expected_evidence_ids:[...new Set(claims.flatMap(c=>c.evidence.map(e=>e.id)))],
      expected_chapter_refs:[...new Set(claims.flatMap(c=>c.evidence.map(e=>e.unit_id)))],
      acceptable_answer_conditions:conditions,forbidden_inferences:forbidden,
      ambiguity_notes:special?['作者只说关键看有没有趋势，未在本次回复直接指定比较段对。']:claims.filter(c=>c.ambiguity_status!=='none').map(c=>c.ambiguity_status),
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
    observations.push({query_id:'g-b07-'+slug,automatic_retrieval_contract_pass:missing.length===0,missing,queries,
      generated_answer_scored:false,semantic_answer_faithfulness_automatically_proven:false});
  }
  writeFileSync(resolve(out,'stage-g-batch-07.cases.jsonl'),cases.map(x=>JSON.stringify(x)).join('\n')+'\n');
  const report={graph_version:graph.metadata.graph_version,executable_cases:cases.length,final_target_cases:240,
    gold_review_status:'model_reviewed_development',independent_test_set:false,human_gold_reviewed:false,
    retrieval_plan_contract_passed:observations.filter(x=>x.automatic_retrieval_contract_pass).length,
    observations,baselines:{source_keyword:'not_run_in_this_batch',vector:'not_implemented',structured:'query_plans_executed',hybrid:'not_run_in_this_batch'},
    generated_answers_evaluated:false,limits:['不是240题完整验收。','只检查取证计划取得预定证据，不把检索命中等同回答忠实度或人工语义评分。','开发题在整理时建立，未作为独立留出集。']};
  writeFileSync(resolve(out,'stage-g-batch-07.results.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({graph_version:report.graph_version,executable_cases:cases.length,retrieval_plan_contract_passed:report.retrieval_plan_contract_passed,failures:observations.filter(x=>!x.automatic_retrieval_contract_pass)}));
}finally{graph.close();}
