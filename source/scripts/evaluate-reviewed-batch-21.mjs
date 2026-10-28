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
 ['eight-parameters-history-system','106的均线系统是否包含8日线、且无条件适合未来所有行情？','参数及适用范围',
  [cid('106','eight-average-parameters-fit-existing-market'),cid('106','system-retain-until-material-change-55-34')],['5、13、21、34、55、89、144、233','后续走势没有大变化时作者沿用'],
  ['八周期不插8，针对6124历史示例；后续无大变化才沿用，55/89与34是该次反弹条件，不报最优。'],['八周期当然补8且永远适用。']],
 ['history-classification-not-current-count','八线九类是否只数当前股价站上几根线？最强一定当前高于全部线吗？','分类进程和未答设问',
  [cid('106','smallest-not-yet-conquered-average-nine-classes'),cid('106','strongest-not-necessarily-currently-above-all')],['未曾攻克的最小周期均线','最厉害者不一定当前'],
  ['按这次反弹历史未曾攻克最小周期，最弱全在线下；最强不必当前全在线上，原文留思考未给详细原因，阈值未定义。'],['直接用当前在线数完全等价。','原文已给最强设问全部算法答案。']],
 ['sector-average-not-weighted-return','缠中说禅板块强弱指标取什么平均，是否市值加权收益越大越好就能单独买入？','指标定义和个股条件',
  [cid('106','sector-strength-average-class-number'),cid('106','leading-sector-dynamics-combine-stock-structure')],['板块成员类别数的平均','还须配合具体股票走势分析'],
  ['同一反弹分类规则的类别数平均、越大越强，非收益率，未给市值权重；还须个股走势和买卖点。'],['原文给了市值加权收益公式及自动买点。']],
 ['averages-level-and-unverified-corrections','均线周期可直接当走势级别吗？图疑144和600578类6是否作者撤回233、类7？','级别与图文身份',
  [cid('106','average-level-no-necessary-correspondence'),cid('106','nine-class-stock-examples-and-index-four')],['走势级别与均线没有必然关系','600578/600607第7'],
  ['只有大致对应；正文233与类别7照留，图144疑问和类6制作者未核，不作为作者修订。'],['均线直接等严格级别，图注自动覆盖正文。']],
 ['six-bars-vs-new-stroke','106六根K线可成笔是否明确撤回81新笔的两个联合条件？','跨课计数范围',
  [cid('106','six-basic-bars-five-day-touch-author-wording'),'lower-l081-c-stage-new-stroke-two-joint-conditions'],['至少延伸6个基本K线单位','顶分型最高K线与底分型最低K线之间'],
  ['原106六根和8/14去包含示例并列81包含后不共K及极值间至少3根，未见明确撤回，计数范围待核。'],['较晚日期自动把81的3根改2根。']],
 ['rotation-t1-and-buy-sell-points','有板块类别均值就能忽略个股买卖点，T+1也不限制理论最精确短线吗？','轮动基础和制度限制',
  [cid('106','rotation-rhythm-founded-on-buy-sell-points'),cid('106','jul14-t1-limits-precise-small-level-operation')],['所有节奏仍须以买卖点为基础','T+1确实限制'],
  ['轮动仍以买卖点，7/14明确T+1限制小级最精确操作且按能力选择，不能据规则明确消制度限制。'],['板块排名取代买点且T+1无影响。']],
 ['boundary-not-best-entry','8/14说分型边沿站稳是最好买点吗？不同级分型区间套等于单看边沿吗？','明确解释与方法范围',
  [cid('106','aug14-boundary-hold-not-best-buy-point'),cid('106','aug14-multilevel-fractal-nesting-not-single-edge')],['分型上边沿站稳不是最佳买点','不等单纯上下边沿判断'],
  ['只是观察成笔；买点从类型，边沿最多类似三类非自动满足；多级分型类区间套不是单一边沿。'],['任何站边沿就是最佳买点并充分成三买。']],
 ['dates-next-header-not-previous-paragraph','7/14解盘末抽出7/16时间头，是否应把7/14的T+1说明整段改标7/16？','来源时间头范围',
  [cid('106','jul14-t1-limits-precise-small-level-operation'),cid('106','jul16-daily-stroke-intraday-down-divergence')],['T+1确实限制','7月16日作者说未上5日线'],
  ['7/14的T+1说明仍7/14，段末7/16头管后面日笔对应分时底背驰段；不改前段，不按7/16段内引用2/28另文改本段。'],['时间头所在抽取块及所有上下文全改7/16或2/28。']],
 ['first-leg-not-whole-type','8/6第一段结束和8/13第二级别反弹是否都等2924整个下跌结束？','层次与时间',
  [cid('106','aug6-first-leg-ended-2762-conditional-day-stroke'),cid('106','aug13-pm-second-rebound-means-forming-b')],['2924下来至少第一段','当天为三级反弹中的第二个'],
  ['8/6仅第一段，2762支未定；8/13第二是构2924第二中枢的小反弹，不等整体结束后的大中枢次级反抽。'],['凡称第二级别反弹就代表整个2924调整完成。']],
 ['a-b-without-c-still-down','a+A+b+B+c没有c，就只能盘整、不能下跌吗？','中枢数量和合法前提',
  [cid('106','aug12-direct-third-buy-no-c-still-down')],['a、c可不出现而不改所述下跌性质'],
  ['作者对该已成立A/B下跌说明a/c可缺，趋势盘整区别中枢数量；不是任何两重叠图框都下跌，也不许删A/B。'],['没有c必盘整，A/B也可任意缺。']],
 ['major-center-not-just-price-break','指数跌价就能确认7月3日大中枢三卖、彻底破坏吗？','跨级别确认链',
  [cid('106','aug11-am-major-center-break-needs-complete-retest')],['次级别类型完成后，其次级别反弹不能回该中枢'],
  ['8/11早仍无三卖，须2924次级下跌完后其后次级反抽不回，不能小价破就借级确认。'],['任何瞬间跌破价格都确认大中枢三卖。']],
 ['probability-conditioning-not-eighties','两个不超10%能直接推出标准情形80%，四次探底95%是项目回测概率吗？','条件和统计边界',
  [cid('106','aug8-fourth-test-ninety-five-author-estimate'),cid('106','aug12-direct-third-buy-at-most-ten-estimate')],['破底概率至少95%','第二种从中枢直接三买扩大'],
  ['95/两个10/90都是作者估计，无样本及条件分布，不能直接相加或当独立统计胜率、也不能删除少数支。'],['项目已验证95%且两10%必相加得80%。']],
];

try {
  const cases=[],observations=[];
  for(const [slug,question,type,required,terms,conditions,forbidden] of specifications){
    const claims=required.map(id=>{const c=graph.getClaim(id);assert.ok(c,id);return c;});
    const plan=terms.map(query=>({command:'search',args:{query,limit:20}}));
    assert.ok(plan.length<=2);
    const expectedSources=claims.flatMap(c=>c.evidence.map(e=>({document_id:e.document_id,pdf_page:e.pdf_page,
      printed_page:e.printed_page,passage_id:e.passage_id,role:e.role,speaker:e.speaker})));
    cases.push({query_id:'g-b21-'+slug,query_text:question,query_type:type,
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
    observations.push({query_id:'g-b21-'+slug,automatic_retrieval_contract_pass:missing.length===0,missing,queries,
      generated_answer_scored:false,semantic_answer_faithfulness_automatically_proven:false});
  }
  writeFileSync(resolve(out,'stage-g-batch-21.cases.jsonl'),cases.map(x=>JSON.stringify(x)).join('\n')+'\n');
  const report={graph_version:graph.metadata.graph_version,executable_cases:cases.length,final_target_cases:240,
    gold_review_status:'model_reviewed_development',independent_test_set:false,human_gold_reviewed:false,
    retrieval_plan_contract_passed:observations.filter(x=>x.automatic_retrieval_contract_pass).length,observations,
    baselines:{source_keyword:'not_run_in_this_batch',vector:'not_implemented',structured:'query_plans_executed',hybrid:'not_run_in_this_batch'},
    generated_answers_evaluated:false,limits:['不是240题完整验收。','只执行取证计划，不将命中等同回答忠实度。','开发题整理时建立，非独立留出集。']};
  writeFileSync(resolve(out,'stage-g-batch-21.results.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({graph_version:report.graph_version,executable_cases:cases.length,retrieval_plan_contract_passed:report.retrieval_plan_contract_passed,failures:observations.filter(x=>!x.automatic_retrieval_contract_pass)}));
  if(report.retrieval_plan_contract_passed!==cases.length)process.exitCode=1;
} finally {graph.close();}
