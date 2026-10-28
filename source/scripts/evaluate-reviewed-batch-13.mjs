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
  ['stroke-center-scope','91课说笔不能构中枢，是否可以删除83课可设计笔构最小中枢程序的话？','跨课语境分歧',
    [cid('091','parts-center-capability'),cid('083','stroke-center-possible-less-stable')],['笔归为不能构中枢','可以设计用笔构造最小中枢的程序'],
    ['91配件分类与83替代设计语境并列，原文未明确撤回；不能按时间自动覆盖。'],['删除83原句当已被明确撤回。','把可设计程序说成绝对不可能。']],
  ['zero-not-reversal','笔状态(1,0)代表已经在向下笔延伸，还是上笔中的顶分型构造？','变量及定义',
    [cid('091','four-state-meanings')],['向上笔出现顶分型构造'],
    ['第一位仍上笔，0为顶构造，非已转向下延伸；(-1,0)为下笔中底构造。'],['0等于方向已经反转。']],
  ['no-direct-jump','(1,1)能跳过零态直接到(-1,1)或(-1,0)吗？','状态转换限制',
    [cid('091','six-allowed-state-transitions'),cid('091','extension-cannot-directly-reverse')],['作者列允许的笔状态转换','不能直接连(-1,1)或(-1,0)'],
    ['上延只先到上零、下延只先到下零，零态再到原向或反向延伸；不连续采样可能漏看中间不等于规则允许跳。'],['四个状态可任意互跳。']],
  ['small-warning-or-usual','5分钟上延要改变，小图必须无例外先转为下笔延伸吗？','必要条件与多数',
    [cid('091','both-up-small-warning-needed')],['小图至少先出现'],
    ['小图至少出现上零或下延，绝大多数是下延；或条件与多数不可合为必然下延。'],['绝大多数就是无例外必要条件。']],
  ['one-bar-versus-confirmation','一个5分钟K内的一分钟警告，就足以确认5分钟向下笔了吗？','跨周期确认',
    [cid('091','one-bar-warning-and-confirmation'),cid('091','small-down-large-zero-confirmation')],['若只在一个5分钟K里','小图(-1,1)出现且导致'],
    ['单根内小警告不足破大结构，小构造确认更重要，大图零态再确认转下才是所述已病；确认对象仍有待核。'],['小图一警告就确认大图反转。']],
  ['fourth-not-automatic-entry','周日均(-1,0)是第四种情况，图写值得参与就能说作者无条件建议买入吗？','图源和语气',
    [cid('091','week-day-four-worst-order')],['第四周日均(-1,0)可能转机'],
    ['正文仅可能转机且须市场走出，值得参与是未核整理图加语；第二三也有限技术能力。'],['图加语就是作者直接原话。','第四种无条件入场且必反转。']],
  ['matrix-not-profit-proof','8行四态有4^8候选，是否证明所有组合可达且能自动永动赚钱？','计数和证明边界',
    [cid('091','eight-row-state-matrix-count'),cid('091','machine-profit-author-proposal')],['称可能情况为4^8','自称可构造自动赚钱的机器'],
    ['作者组合计数与机器设想，没有联合可达/初始边界/交易实现证明；不认证自动获利。'],['候选数量就是实际可达状态数证明。','项目已实现无风险自动交易。']],
  ['second-center-timeline','12月24日已经有第二个1分钟中枢吗？5210与5209可以按误差当同点吗？','状态与价格精度',
    [cid('091','dec24-second-center-not-yet'),cid('091','dec25-center-formed-midpoint')],['第二中枢也未出现','中间位置5210'],
    ['12/24未出、12/25才称成，中间5210与5209差1点照录，不从次日图倒填。'],['12/24第二中枢已完成。','EPS自动消掉作者记载的1点差别。']],
  ['strong-exception','12月25日三支以后是否全部无例外都必形成更大中枢？','例外和量词',
    [cid('091','dec25-strong-exception-larger-center')],['除三买后最强势'],
    ['三买后不背驰继续1分钟上移是明确强势例外，其他支作者才作更大中枢判断。'],['删去最强势例外说所有支都必扩展。']],
  ['boll-structure-choice','BOLL收口是否必突破单一方向，且任何周期收口都有效？','辅助和周期选择',
    [cid('091','boll-break-can-be-bigger-oscillation'),cid('091','boll-select-by-pattern-structure-first')],['不是必向一个方向突破','并非任意级别收口都有效'],
    ['可升级震荡，周期须依中枢对应图形选择，分解为本而非独立指标万能。'],['排除更大震荡分支。','任意周期BOLL收口必有效。']],
  ['nine-and-divergence-scope','本课九线段回5240与三买后顶背驰，能推广成任何九段必升级、所有盘整背驰须三买吗？','案例与形式定义',
    [cid('091','dec27-return-nine-case-upgrade'),cid('091','dec27-no-divergence-before-third')],['若本次回5240下','其顶背驰须在三买之后讨论'],
    ['九段是该例既有震荡与回5240条件，顶背驰限该次1分钟上涨；不替代普遍中枢与盘整背驰条件。'],['任意九线段必升级。','所有背驰都必须先有三买。']],
  ['wine-not-target','中石油24元和14元，在第91课分别是必达目标和确定买点吗？','自述与预测身份',
    [cid('091','petro-24-wine-not-price-guarantee')],['24元称为酒话'],
    ['24酒话、14愿望且估计未必给，不是保证目标或已成立买点；30分钟图类背驰不升严格30分钟背驰。'],['作者保证股价必到14。','24或14自动构成买点。']],
];

try {
  const cases=[],observations=[];
  for(const [slug,question,type,required,terms,conditions,forbidden] of specifications){
    const claims=required.map(id=>{const c=graph.getClaim(id);assert.ok(c,id);return c;});
    const plan=terms.map(query=>({command:'search',args:{query,limit:20}}));
    assert.ok(plan.length<=2);
    const expectedSources=claims.flatMap(c=>c.evidence.map(e=>({document_id:e.document_id,pdf_page:e.pdf_page,
      printed_page:e.printed_page,passage_id:e.passage_id,role:e.role,speaker:e.speaker})));
    cases.push({query_id:'g-b13-'+slug,query_text:question,query_type:type,
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
    observations.push({query_id:'g-b13-'+slug,automatic_retrieval_contract_pass:missing.length===0,missing,queries,
      generated_answer_scored:false,semantic_answer_faithfulness_automatically_proven:false});
  }
  writeFileSync(resolve(out,'stage-g-batch-13.cases.jsonl'),cases.map(x=>JSON.stringify(x)).join('\n')+'\n');
  const report={graph_version:graph.metadata.graph_version,executable_cases:cases.length,final_target_cases:240,
    gold_review_status:'model_reviewed_development',independent_test_set:false,human_gold_reviewed:false,
    retrieval_plan_contract_passed:observations.filter(x=>x.automatic_retrieval_contract_pass).length,observations,
    baselines:{source_keyword:'not_run_in_this_batch',vector:'not_implemented',structured:'query_plans_executed',hybrid:'not_run_in_this_batch'},
    generated_answers_evaluated:false,limits:['不是240题完整验收。','只执行取证计划，不将命中等同回答忠实度。','开发题整理时建立，非独立留出集。']};
  writeFileSync(resolve(out,'stage-g-batch-13.results.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({graph_version:report.graph_version,executable_cases:cases.length,retrieval_plan_contract_passed:report.retrieval_plan_contract_passed,failures:observations.filter(x=>!x.automatic_retrieval_contract_pass)}));
  if(report.retrieval_plan_contract_passed!==cases.length)process.exitCode=1;
} finally {graph.close();}
