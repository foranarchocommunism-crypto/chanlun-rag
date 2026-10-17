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
 ['macd-skilled-exception','103零轴下回避是否禁止任何高手在背驰时介入？','防守方法能力范围',
  [cid('103','macd-zero-defense-corresponding-chart'),cid('103','macd-defense-skilled-divergence-exception')],['基本防守回避黄白线','明确允许技术较高者'],
  ['初学防守有最低周期和能力范围，高手背驰介入原文明确允许，不统一为任意人零轴下禁令。'],['所有人在任何周期零轴下都绝不能介入。']],
 ['lowest-period-chosen','103是否规定所有人统一用1分钟或60分钟作最低周期？','跨页周期条件',
  [cid('103','macd-defense-lowest-period-by-capability')],['按能力选最低时间周期'],
  ['按能力选，60/30仅例；1分钟常上下反复，366/367跨页完整，不机械等结构级别。'],['所有人统一1分钟过滤。']],
 ['physics-program-not-model','104是否已经提供可复现的现代物理能量方程证明市场预测？','作者纲领与科学证明',
  [cid('104','geometry-energy-dynamics-author-program')],['一切能量动力形态应几何化'],
  ['作者纲领和自评，具体以后再说；无量纲/函数/方程/实验，不冒称物理实证。'],['项目已用现代物理证明市场预测。']],
 ['price-rhythm-rounding','600、1345与6124至5522、4778是精确价差恒等式吗，3600是中轴价吗？','原数和尺度',
  [cid('103','3600-scale-targets-4922-3424-author')],['把5522说成6124下来600点'],
  ['原数照存，实际差602/1346有近似出入；3600为幅度尺度，4922/3424属作者条件预测。'],['600/1345为精确价差且3600是当前中轴。']],
 ['three-percent-not-epsilon','104上下3%能直接加进笔极值、中枢交集和EPS比较吗？','目标惯例边界',
  [cid('104','price-target-three-percent-author-convention')],['任何技术位置都有上下3%'],
  ['是作者目标惯例，未给结构判定容差规则，不改笔/中枢/EPS定义。'],['所有结构边界统一容许3%。']],
 ['3424-bottom-not-final','3/28说3424初显威力，就等日底分型和最终底部都确认吗？','确认层次',
  [cid('104','mar28-no-daily-fractal-no-final-bottom')],['连日底分型都尚不足形成'],
  ['连日底尚不足，传闻未兑现可再杀跌回试，最终底部无结论。'],['3424最终底部和日底已完全确认。']],
 ['five-thirty-vs-fifteen','3/25的5分钟带30预期与3/26只带15记录，是否应校成相同周期？','跨日原句',
  [cid('103','mar25-five-to-thirty-macd-exit-condition'),cid('103','mar26-five-consolidation-only-fifteen-zero')],['可带30分钟再次冲击零轴','只带15分钟MACD回零轴受阻'],
  ['前日条件计划30与当日实际15各自保存日期，不能因晚文自动篡改早计划或按图周期等中枢级别。'],['两处都已校成同一30分钟。']],
 ['fund-stage-t1-tail','大资金沉淀筹码是否从5522开始一直要求，前日尾盘是否取消T+1风险？','资金阶段和隔夜约束',
  [cid('104','small-fund-short-bite-large-chips-now'),cid('104','apr2-3462-fail-retest-and-t1-tail')],['以前离底部远未要求沉淀','前一天尾盘打提前量'],
  ['作者明确最近才要求大资金沉淀，前尾盘是提前量不改T+1，仍承受未确认隔夜风险。'],['从5522起所有资金都应沉淀。','提前买入保证次日随时安全退出。']],
 ['homework-author-vs-annotation','4/3作业答案是图括注下降趋势线还是作者后来3396底分型解释？','来源身份与跨日答案',
  [cid('104','apr3-homework-apr7-author-answer-3396')],['4月7日答只和60分钟底分型'],
  ['4/3问与4/7答分日期，作者说60分钟底分型3396破后成笔；下降趋势线括注制作者未核。'],['图括注就是作者原答。']],
 ['apr7-sixty-not-week-complete','4/7已有60分钟向上笔，是否日笔周底周笔都已完全确认？','周期与概率',
  [cid('104','apr7-sixty-up-stroke-formed'),cid('104','apr7-day-3613-week-fractal-likely-exception')],['60分钟图在数月来第一次','突破3555使周底分型'],
  ['60笔当天已成，日笔仍看3613，周底极大概率且本周再破底例外，周笔未因此确认。'],['三个周期同时已完成向上笔。']],
 ['apr11-three-chart-boundaries','4/11周底已成是否等周笔已成，3533、3613、3840能合为同一位置？','三周期边界',
  [cid('104','apr11-week-bottom-3840-stroke-or-relay'),cid('104','apr11-three-chart-boundaries-not-one-level')],['上边3840决定','分别观察超短、短、中走势'],
  ['周底形成但周笔/失败两支，3533六十分钟、3613日、3840周各对象，不按K周期直接换严格中枢。'],['周底成立自动周笔成立。','三价完全可互借。']],
 ['warrant-risk-not-profit-license','580989有所谓高收益案例，是否一般人就应在0.8附近追入？','历史风险与技术结构',
  [cid('103','warrant-no-chase-expiry-warning'),cid('104','mar27-warrant-one-center-consolidation')],['当天未介入者不得再介入','一般人远离该最后一波行情'],
  ['作者明说0.8远0.6风险极大、到期和高度投机；后0.7单中枢盘整看三类点，一般人远离，收益未核。'],['高收益修辞等同任何人应追权证。']],
];

try {
  const cases=[],observations=[];
  for(const [slug,question,type,required,terms,conditions,forbidden] of specifications){
    const claims=required.map(id=>{const c=graph.getClaim(id);assert.ok(c,id);return c;});
    const plan=terms.map(query=>({command:'search',args:{query,limit:20}}));
    assert.ok(plan.length<=2);
    const expectedSources=claims.flatMap(c=>c.evidence.map(e=>({document_id:e.document_id,pdf_page:e.pdf_page,
      printed_page:e.printed_page,passage_id:e.passage_id,role:e.role,speaker:e.speaker})));
    cases.push({query_id:'g-b19-'+slug,query_text:question,query_type:type,
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
    observations.push({query_id:'g-b19-'+slug,automatic_retrieval_contract_pass:missing.length===0,missing,queries,
      generated_answer_scored:false,semantic_answer_faithfulness_automatically_proven:false});
  }
  writeFileSync(resolve(out,'stage-g-batch-19.cases.jsonl'),cases.map(x=>JSON.stringify(x)).join('\n')+'\n');
  const report={graph_version:graph.metadata.graph_version,executable_cases:cases.length,final_target_cases:240,
    gold_review_status:'model_reviewed_development',independent_test_set:false,human_gold_reviewed:false,
    retrieval_plan_contract_passed:observations.filter(x=>x.automatic_retrieval_contract_pass).length,observations,
    baselines:{source_keyword:'not_run_in_this_batch',vector:'not_implemented',structured:'query_plans_executed',hybrid:'not_run_in_this_batch'},
    generated_answers_evaluated:false,limits:['不是240题完整验收。','只执行取证计划，不将命中等同回答忠实度。','开发题整理时建立，非独立留出集。']};
  writeFileSync(resolve(out,'stage-g-batch-19.results.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({graph_version:report.graph_version,executable_cases:cases.length,retrieval_plan_contract_passed:report.retrieval_plan_contract_passed,failures:observations.filter(x=>!x.automatic_retrieval_contract_pass)}));
  if(report.retrieval_plan_contract_passed!==cases.length)process.exitCode=1;
} finally {graph.close();}
