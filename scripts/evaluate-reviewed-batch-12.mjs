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
  ['boll-auxiliary','第90课说BOLL近100%，便是绝对判据或项目实测准确率吗？','经验与保证范围',
    [cid('090','boll-auxiliary-not-absolute')],['第90课明确限定所给中阴结束时间判断'],
    ['辅助非绝对且有例外，接近100%为作者自称经验，无项目样本验证。'],['BOLL绝不出错。','图谱已实测近100%交易胜率。']],
  ['first-point-sequence','碰到或越过一根BOLL轨道就能确认一类买卖点吗？','联合形态与顺序',
    [cid('090','boll-first-point-sequence')],['先从上轨上跌回其下'],
    ['先离超强区，再次创新高低且未有效回超强区，三步联合仍只是辅助。'],['单触轨充分确认正式一类点。','略过再次创新高低的条件。']],
  ['contraction-two-results','BOLL一收口，就一定是同级中阴已经结束且三类点已确认吗？','或条件与层次',
    [cid('090','boll-contraction-expand-or-end')],['更低某级别中阴过程将级别扩展或结束'],
    ['对应更低某级别，可能扩展或结束，一般对应三类点而非已无条件确认。'],['同级中阴必已结束。','省去级别扩展分支。']],
  ['period-not-six-times','5分钟中阴看30分钟BOLL，是所有级别固定六倍的公式吗？','级别与指标周期',
    [cid('090','boll-chart-period-not-one-to-one')],['作者所举5分钟中阴例用30分钟BOLL'],
    ['只为该例，非一一对应也非固定六倍；没有跨周期选择参数算法。'],['全书每层都必须固定乘六。']],
  ['must-center-not-direction','第89课必经5分钟中枢能提前预定方向吗？5分钟以上操作者也都必须管它吗？','结构必经与操作级别',
    [cid('089','higher-must-five-center'),cid('089','prepare-center-level-operation')],['必须先出现5分钟中枢','若按5分钟以上级别操作'],
    ['限6004起1分钟下跌背驰后超1分钟演化，先中枢而方向未定；5分钟以上可不管此中阴操作过程。'],['任意未完成1分钟波动必立即升级。','必经中枢就预定上涨。','把原文以上擅改成严格大于。']],
  ['consolidation-amplitude','盘整只能窄幅横着走，而且一定比多中枢趋势弱吗？','定义和强弱',
    [cid('089','consolidation-not-flat-range'),cid('089','consolidation-not-necessarily-weaker')],['10000跌到0也可属盘整','盘整不一定比趋势弱'],
    ['相应级别完整类型一个中枢可幅度极大，中枢数量不决定力度或幅度强弱。'],['盘整必为窄幅横盘。','趋势中枢多就必比盘整强。']],
  ['small-large-third','11月22日小1分钟三卖已有，是否等于大5分钟三卖确认？','跨级别状态',
    [cid('089','nov22-small-sell-large-unknown')],['大5分钟三卖仍未知'],
    ['小三卖已有、大三卖仍未知；若扩展30分钟，下破可能陷阱而非既成结论。'],['小三卖充分证明大三卖。']],
  ['future-fact-5032','11月29日将形成30分钟中枢的展望，可以直接当成已完成事实吗？','时态与确认',
    [cid('089','nov29-thirty-center-future'),cid('090','dec5-5032-fact-threshold')],['将扩展出30分钟中枢','5032之前还不能称事实'],
    ['11/29在扩展且将形成，12/5才说重回5032成为事实；后期图不倒填状态。'],['将形成等于当时已完成。','用2008截图反填11月已确立。']],
  ['trap-and-force','跌破一个价位但随后涨回去，就能不看中枢与力度认定陷阱吗？','结构及前后比较',
    [cid('090','traps-require-center-oscillation'),cid('090','traps-need-force-comparison')],['作者把市场陷阱归于中枢震荡','辨陷阱除中枢震荡外还要比较前后力度'],
    ['先辨震荡或移动，移动不按陷阱处理，再比较前后力度；本课没给统一数值阈值。'],['只要后来反弹就是当时可确定陷阱。','中枢移动也一律是陷阱。']],
  ['formed-versus-confirmed','12月12日日顶形成就确认下笔了吗？12月14日周底构成就已确立了吗？','构成与确立',
    [cid('090','dec12-top-formed-not-down-stroke'),cid('090','dec14-week-formed-await-confirmation')],['12月12日日顶分型已形成','下午作者说周底已构成'],
    ['日顶已形成但5日线有效破未确认，不能立刻断言下笔；周底已构成尚待下周5周线站住确立。'],['日顶形成充分确认下笔。','构成与确立可互换。']],
  ['monday-not-fulfilled','12月14日预计下周一先构成日底，12月17日就一定完成了吗？','条件及失败分支',
    [cid('090','dec14-next-daily-bottom-conditional'),cid('090','dec17-daily-inclusion-not-bottom')],['首先必须下周一构成日底分型','12月17日作者说日底未构成'],
    ['前文全段有周一构成前提，12/17实际仅包含、日底未成，保留未满足分支。'],['作者展望一出便是已完成事实。']],
  ['red-market-shortcut','第90课12月17日不红盘就不能成日底，可以直接编成通用算法吗？','原文疑点与无答案',
    [],[],['原句保留为历史作者解盘；当前价红绿与曾到高点不必同义，判断时点未明，未发布通用算法。'],['无条件把不红盘作为所有日底排除规则。','静默把作者原句改掉。']],
];

try {
  const cases=[],observations=[];
  for(const [slug,question,type,required,terms,conditions,forbidden] of specifications){
    const claims=required.map(id=>{const c=graph.getClaim(id);assert.ok(c,id);return c;});
    const special=slug==='red-market-shortcut';
    const plan=special?[{command:'page',args:{documentId:'volume_2.pdf',page:276}}]:terms.map(query=>({command:'search',args:{query,limit:20}}));
    assert.ok(plan.length<=2);
    const expectedSources=special?[1,2].map(block=>({document_id:'volume_2-5332cd1b6038',pdf_page:276,printed_page:'271',
      passage_id:`volume_2-5332cd1b6038-p0276-b00${block}`,role:'author_commentary',speaker:'缠中说禅'})):
      claims.flatMap(c=>c.evidence.map(e=>({document_id:e.document_id,pdf_page:e.pdf_page,
        printed_page:e.printed_page,passage_id:e.passage_id,role:e.role,speaker:e.speaker})));
    cases.push({query_id:'g-b12-'+slug,query_text:question,query_type:type,
      required_concepts:[...new Set(claims.flatMap(c=>c.concept_ids))],required_claims:required,
      expected_evidence_ids:[...new Set(claims.flatMap(c=>c.evidence.map(e=>e.id)))],
      expected_chapter_refs:[...new Set([...(special?['lesson-090']:[]),...claims.flatMap(c=>c.evidence.map(e=>e.unit_id))])],
      acceptable_answer_conditions:conditions,forbidden_inferences:forbidden,
      ambiguity_notes:special?['不红盘与已到最高点的关系及判断时点未明，保留原字不发布算法。']:claims.filter(c=>c.ambiguity_status!=='none').map(c=>c.ambiguity_status),
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
    observations.push({query_id:'g-b12-'+slug,automatic_retrieval_contract_pass:missing.length===0,missing,queries,
      generated_answer_scored:false,semantic_answer_faithfulness_automatically_proven:false});
  }
  writeFileSync(resolve(out,'stage-g-batch-12.cases.jsonl'),cases.map(x=>JSON.stringify(x)).join('\n')+'\n');
  const report={graph_version:graph.metadata.graph_version,executable_cases:cases.length,final_target_cases:240,
    gold_review_status:'model_reviewed_development',independent_test_set:false,human_gold_reviewed:false,
    retrieval_plan_contract_passed:observations.filter(x=>x.automatic_retrieval_contract_pass).length,observations,
    baselines:{source_keyword:'not_run_in_this_batch',vector:'not_implemented',structured:'query_plans_executed',hybrid:'not_run_in_this_batch'},
    generated_answers_evaluated:false,limits:['不是240题完整验收。','只执行取证计划，不将命中等同回答忠实度。','开发题整理时建立，非独立留出集。']};
  writeFileSync(resolve(out,'stage-g-batch-12.results.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({graph_version:report.graph_version,executable_cases:cases.length,retrieval_plan_contract_passed:report.retrieval_plan_contract_passed,failures:observations.filter(x=>!x.automatic_retrieval_contract_pass)}));
  if(report.retrieval_plan_contract_passed!==cases.length)process.exitCode=1;
} finally {graph.close();}
