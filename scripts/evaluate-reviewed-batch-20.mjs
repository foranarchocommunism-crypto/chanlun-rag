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
 ['mechanical-title-alias','105课机械操作是什么意思，是否任意分类规则或电脑自动交易都等价？','概念别名和方法前提',
  [cid('105','mechanical-follow-structural-joints'),cid('105','classification-choice-must-be-complete')],['机械操作'],
  ['课题短名与正文机械化操作同概念，按结构关节节奏；分类必须完全，不等任意规则或已实现电脑交易。'],['任意有遗漏分类都合格。','作者程序已实现自动赚钱。']],
 ['corrected-author-date','3840前提那段和5月5日补涨趋弱，是读者说的且都在4月29日吗？','身份和跨段日期',
  [cid('105','apr30-3840-premised-on-effective-3656'),cid('105','may5-weak-attack-3840-risk')],['4月30日作者说3840','5月5日作者称上攻力度趋弱'],
  ['均作者解盘，4/30前提3656有效由节后三天验证；5/5是后段新日期，未把段末时间头覆盖前文。'],['这些是姓名为住院近况的读者发言。','两段都4月29日。']],
 ['half-vs-partial','4/16必然半仓是否意味着7/2主动买套也必须所有人固定半仓？','仓位方法范围',
  [cid('105','apr16-half-position-range-break-rule'),cid('105','jul2-active-accumulation-partial-chips-not-always-half')],['明确后一法必然半仓','筹码够多时可只补固定数量'],
  ['半仓限4/16高抛不破回补法，真破不补且清剩；7/2部分筹码，够多可数量不变，未统一比例。'],['任何主动买套固定半仓即可无风险。']],
 ['strength-grade-not-structural-time','4/18第一级别与第二级别反弹可直接标为5分钟、1分钟吗？5524能改5522.8吗？','力度与原数范围',
  [cid('105','apr18-three-rebound-strengths-not-chart-periods')],['4778至5524为第一级别力度'],
  ['以两段历史反弹力度比较，三种逐强选项；未给固定结构级别，5524/4196原数不按图小数改写。'],['第一级别已明定5分钟且5524已纠错为5522.8。']],
 ['apr22-fractal-not-stroke','4/22突破3085确认小底，就等向上笔也已确认、不用看回试吗？','确认条件',
  [cid('105','apr22-3085-fractal-confirmed-stroke-pending')],['3085突破确认60分钟小底分型成立'],
  ['分型成立，成向上笔仍看回试站住；短3085中3305不互借，不用4/25图反填。'],['底分型成即笔成。']],
 ['jul3-jul4-containing-bars','7/3和7/4底分型状态一样吗？2753、2945、3483可直接跳到最后一关？','跨日包含和分阶段',
  [cid('105','jul3-containment-delays-bottom-step-boundaries'),cid('105','jul4-weak-bottom-2753-still-pending')],['两日包含令底分型须再等次日','底分型终于勉强形成'],
  ['7/3包含尚待，7/4最弱分型形成；仍先2753再2945、缺口、3483，不能越阶段或把日期全标7/2。'],['7/3已经强底形成且三关可互借。']],
 ['entry-nesting-not-2917','6/19应等2917站稳再进，还是区间套成立进、2917观察是否退出？','入场与持有边界',
  [cid('105','jun19-nesting-entry-boundaries-for-exit')],['区间套成立即进场'],
  ['作者明说区间套成立进，已有仓看2917且笔继续延伸才保持，否则分批撤，不倒置成等2917进。'],['2917站稳是该例唯一入场信号。']],
 ['theory-2990-empirical-3700','7/1反弹3700是100%理论保证吗？到2990后就不许再跌了吗？','理论条件与经验参考',
  [cid('105','jul1-theoretical-minimum-above-2990'),cid('105','jul1-empirical-third-3700-not-guaranteed')],['理论确保最低反弹','整个下跌约1/3'],
  ['作者理论断言附下跌完成、相应级别回2990之上条件，此后仍允许跌；3700经验1/3非100%，90%未独立统计。'],['3700是项目已证明必达。','一到2990之后下跌不可能。']],
 ['active-no-risk-author-claim','主动买套实际无风险和最后一跌99%，是否项目统计和所有人安全执行的证明？','作者断言与执行范围',
  [cid('105','jul1-two-third-centers-no-risk-author-assertion'),cid('105','jul1-final-decline-ninety-nine-not-hundred')],['主动买套两风险','只因基本面等判断自称99%'],
  ['无风险与99%均作者归属，未验证资金/制度/流动性；6124和3700各自第三中枢可能，非理论100%。'],['项目实测99%且任何人主动买套无风险。']],
 ['inverted-t-not-theory','倒T型K线70%和7/1的经验90%能当理论买点100%吗？','经验工具边界',
  [cid('105','jul2-inverted-t-seventy-percent-empirical')],['自称成最终反弹底概率70%'],
  ['7/2说经验K线方法与其理论无关只辅助，上次二探不同，仍按当下，70%无样本验证。'],['倒T一出现就是已证理论100%买点。']],
 ['different-gaps-and-buyback','3300缺口不回补才买筹码，与6/10新缺口能补才继续，是否作者自相矛盾的同一缺口？','缺口对象及动作',
  [cid('105','jun10-prediction-game-operation-absolute-wording'),cid('105','jun10-down-divergence-rebound-gap-two-paths')],['3300缺口不回补才可回补筹码','反弹不能回补6月10日缺口就退出'],
  ['3300支持缺口、6/10新缺口和买回筹码是不同对象/动作；分日期相对方向，不凭回补二字合并。'],['所有回补都指同一缺口且无需条件。']],
 ['moving-average-homework-deferred','7/9均线分类是否本课已经给了具体公式，可直接把383/384流程当其答案？','未给答案与未知图',
  [cid('105','jul9-moving-average-classification-homework')],['用最简单均线方式对股票完全分类'],
  ['7/9仅留作业并次日继续，本段未给具体分类公式；未署名流程不能自动当作者答案。'],['本段已完整给均线公式和可执行流程。']],
];

try {
  const cases=[],observations=[];
  for(const [slug,question,type,required,terms,conditions,forbidden] of specifications){
    const claims=required.map(id=>{const c=graph.getClaim(id);assert.ok(c,id);return c;});
    const plan=terms.map(query=>({command:'search',args:{query,limit:20}}));
    assert.ok(plan.length<=2);
    const expectedSources=claims.flatMap(c=>c.evidence.map(e=>({document_id:e.document_id,pdf_page:e.pdf_page,
      printed_page:e.printed_page,passage_id:e.passage_id,role:e.role,speaker:e.speaker})));
    cases.push({query_id:'g-b20-'+slug,query_text:question,query_type:type,
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
    observations.push({query_id:'g-b20-'+slug,automatic_retrieval_contract_pass:missing.length===0,missing,queries,
      generated_answer_scored:false,semantic_answer_faithfulness_automatically_proven:false});
  }
  writeFileSync(resolve(out,'stage-g-batch-20.cases.jsonl'),cases.map(x=>JSON.stringify(x)).join('\n')+'\n');
  const report={graph_version:graph.metadata.graph_version,executable_cases:cases.length,final_target_cases:240,
    gold_review_status:'model_reviewed_development',independent_test_set:false,human_gold_reviewed:false,
    retrieval_plan_contract_passed:observations.filter(x=>x.automatic_retrieval_contract_pass).length,observations,
    baselines:{source_keyword:'not_run_in_this_batch',vector:'not_implemented',structured:'query_plans_executed',hybrid:'not_run_in_this_batch'},
    generated_answers_evaluated:false,limits:['不是240题完整验收。','只执行取证计划，不将命中等同回答忠实度。','开发题整理时建立，非独立留出集。']};
  writeFileSync(resolve(out,'stage-g-batch-20.results.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({graph_version:report.graph_version,executable_cases:cases.length,retrieval_plan_contract_passed:report.retrieval_plan_contract_passed,failures:observations.filter(x=>!x.automatic_retrieval_contract_pass)}));
  if(report.retrieval_plan_contract_passed!==cases.length)process.exitCode=1;
} finally {graph.close();}
