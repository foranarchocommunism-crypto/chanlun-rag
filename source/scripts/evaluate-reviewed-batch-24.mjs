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
  [
    "active-passive-two-meanings",
    "主动带套是不是只指容忍亏损，大资金一直补就行？",
    "定义/防护",
    [
      "upper-l013-c-stage-active-entrapment-two-meanings-and-protection",
      "upper-l013-c-stage-passive-entrapment-blind-entry"
    ],
    [
      "主动带套有两层意思",
      "盲目状态下被套称为被动带套"
    ],
    [
      "主动包括规模介入难一次完成及更重要的走势失效防护，不能做就退出程序，不论盈亏；被动是无明确介入依据。"
    ],
    [
      "主动就是无限补仓，所有亏损都被动。"
    ]
  ],
  [
    "invalid-entry-two-branches",
    "均线系统第一和第二买点分别在何种情况程序失效？盈利就可以不走吗？",
    "失效条件",
    [
      "upper-l013-c-stage-average-first-entry-another-bear-kiss-invalid",
      "upper-l013-c-stage-average-second-entry-break-old-bear-low-exit"
    ],
    [
      "上涨时又出现男上位缠绕",
      "该缠绕跌破前面男上位最低位"
    ],
    [
      "一买又男吻说明并非最后，二买破前男上位最低位后反弹清；盈利/后面还涨都不改变失效处理。"
    ],
    [
      "任何回落都失效或盈利永远不必走。"
    ]
  ],
  [
    "half-and-maotai-prior-low",
    "一半的位置可以直接写成50%公式吗？茅台8/7是破二买前低吗？",
    "参照范围",
    [
      "upper-l013-c-stage-half-position-warning-and-last-retest-not-guaranteed",
      "upper-l014-c-stage-maotai-aug7-not-break-prior-may26-low"
    ],
    [
      "称一般一半位置不该破",
      "前低在5月26日37元多"
    ],
    [
      "一半未给具体参照，不能补公式；8/7是作者认定买点，未破5/26前低37元多，反抽一般有非必然。"
    ],
    [
      "固定50%参照已给、8/7必是失败二买。"
    ]
  ],
  [
    "tcl-case-lot-and-topup",
    "TCL答复是否要求所有股票一次全补、原仓永不卖？",
    "案例与通则",
    [
      "upper-l013-c-stage-tcl-cost-topup-specific-not-universal-lump",
      "upper-l013-c-stage-tcl-swing-added-lot-not-original-holding"
    ],
    [
      "在TCL既有套仓的具体答复",
      "原套仓暂不动"
    ],
    [
      "该TCL成本语境的一次补/只动补仓部分，短线需能力、避免增总仓；不取消一般分批/程序失效退出，解套非保证。"
    ],
    [
      "任何股票一律全补且原仓永久不动。"
    ]
  ],
  [
    "ninety-and-no-speculative-switch",
    "强市90%以上是已验证胜率吗？没卖点换后更好是否证明该换？",
    "统计及纪律",
    [
      "upper-l013-c-stage-program-strength-ninety-author-estimate",
      "upper-l013-c-stage-no-sell-signal-no-speculative-switch"
    ],
    [
      "强市自称基本90%以上",
      "原股未出卖出信号就持有"
    ],
    [
      "90%无样本是作者自述且弱市较低；既定系统无卖点时不因想象更好换股，事后更好不替代程序。"
    ],
    [
      "项目已回测90%且事后更好能自动证明当时该换。"
    ]
  ],
  [
    "law-kiss-and-corresponding-next",
    "第14课缠绕只湿吻吗？大级别二买能随意跳到任意小级一买吗？",
    "均线框架与相应走势",
    [
      "upper-l014-c-stage-entanglement-includes-all-three-kisses",
      "upper-l014-c-stage-buy-point-law-corresponding-next-level"
    ],
    [
      "缠绕包括飞吻、唇吻、湿吻",
      "次一级别相应走势的第一类买点"
    ],
    [
      "缠绕包括三吻，买点定律保留次一级别与相应走势、周/日示例，均线框架不自动等严格中枢递归。"
    ],
    [
      "必须湿吻且可跳任意级，二类概念因此被取消。"
    ]
  ],
  [
    "short-program-order-and-specific-level",
    "短差是先回补再减仓吗？000503的30分卖与5分买怎么记录？",
    "程序/案例",
    [
      "upper-l014-c-stage-short-difference-program-reduce-rebuy-order",
      "upper-l014-c-stage-000503-thirty-sell-five-buy-case"
    ],
    [
      "次级别第一类卖点出现可先减仓",
      "12月1日10:30在30分钟背驰约9.7"
    ],
    [
      "大入后次级卖可减再买补；000503具体12/1 10:30 30分9.7卖、12/5 10:25 5分9.2补是独立实例，最高效非对比实证。"
    ],
    [
      "先补后卖或强改案例成同一个周期。"
    ]
  ],
  [
    "macd-doubled-not-fixed-priority",
    "MACD长一倍是否已给24/52/18，柱和线冲突时固定优先哪个？",
    "指标参数/上下文",
    [
      "upper-l014-c-stage-macd-double-period-and-double-head-context",
      "upper-l014-c-stage-macd-lines-and-histogram-combined"
    ],
    [
      "MACD周期比普通长一倍",
      "都要看、综合看"
    ],
    [
      "作者只说长一倍，未明各参数映射；本例普通4/13双头、回零轴后再拉过程；线柱都看未给冲突固定优先。"
    ],
    [
      "原文明确24/52/18且只看柱或只看线。"
    ]
  ],
  [
    "week-day-thirty-not-same-confirmation",
    "12/6茅台30分钟有卖点是否周日都已背驰？",
    "多周期确认",
    [
      "upper-l014-c-stage-dec6-week-none-daily-double-head-not-finished",
      "upper-l014-c-stage-dec6-thirty-minute-sell-and-zero-rebuy"
    ],
    [
      "周线不存在背驰，日线将演化",
      "30分钟图12月1日13:30卖点"
    ],
    [
      "周无、日待回零轴再上，30分可短差是不同层次；回零轴不自动成所有场景一买，图补时刻不当原文。"
    ],
    [
      "三周期都已确认背驰卖出。"
    ]
  ],
  [
    "divergence-amplitude-and-equal-low",
    "背驰承诺调整多长多大吗？600050等低2.43是失败的标准一买吗？",
    "定义边界",
    [
      "upper-l014-c-stage-divergence-no-promised-duration-amplitude",
      "upper-l014-c-stage-600050-equal-low-not-standard-first-buy"
    ],
    [
      "不承诺调整时间或幅度",
      "同为2.43、没有创新低"
    ],
    [
      "只说相应升势告段，回补看低一级一买；作者因未创新低否定标准点，不是承认标准点再说失败；不添加EPS。"
    ],
    [
      "所有背驰必跌固定幅度，等低标准点只是失败。"
    ]
  ],
  [
    "reader-identity",
    "600058自称按程序选股那句话是谁说的？作者是否确认图里个人理解所有细节？",
    "来源身份",
    [],
    [],
    [
      "PDF47前两段是瞎鼓捣读者、未记时间，后为作者15:23答复；作者确认11/17周二买，不代表图里4/7/个人理解都获认证。"
    ],
    [
      "提问是作者观点或问题时间沿用前个作者15:12。"
    ]
  ],
  [
    "000063-correction",
    "000063读者一二三点计数与作者纠正、图上标日一致吗？",
    "原文/读者/图注",
    [
      "upper-l014-c-stage-000063-reader-count-corrected-not-endorsed"
    ],
    [
      "作者纠正1999年4月30日为第二类买点"
    ],
    [
      "作者称99/4/30二类，03/1/3 12.69周为最标准唯一一类；读者03/1/2及图99/5/14不覆盖原话，未逐项认可全计数。"
    ],
    [
      "作者已认可读者全部点序且按图改成5/14。"
    ]
  ]
];

try {
  const cases=[],observations=[];
  for(const [slug,question,type,required,terms,conditions,forbidden] of specifications){
    const claims=required.map(id=>{const c=graph.getClaim(id);assert.ok(c,id);return c;});
    const sourceCase=type==='来源身份';
    const plan=sourceCase?[{command:'page',args:{documentId:'volume_1.pdf',page:47}}]:terms.map(query=>({command:'search',args:{query,limit:20}}));
    assert.ok(plan.length<=2);
    let expectedSources=claims.flatMap(c=>c.evidence.map(e=>({document_id:e.document_id,pdf_page:e.pdf_page,
      printed_page:e.printed_page,passage_id:e.passage_id,role:e.role,speaker:e.speaker})));
    if(sourceCase)expectedSources=graph.db.prepare("SELECT p.document_id,p.pdf_page,pg.printed_page,p.id AS passage_id,p.role,p.speaker FROM passages p JOIN pages pg ON pg.document_id=p.document_id AND pg.pdf_page=p.pdf_page WHERE p.id IN ('volume_1-a53e99c37ca5-p0047-b000','volume_1-a53e99c37ca5-p0047-b001','volume_1-a53e99c37ca5-p0047-b002') ORDER BY p.id").all();
    cases.push({query_id:'g-b24-'+slug,query_text:question,query_type:type,
      required_concepts:[...new Set(claims.flatMap(c=>c.concept_ids))],required_claims:required,
      expected_evidence_ids:[...new Set(claims.flatMap(c=>c.evidence.map(e=>e.id)))],
      expected_chapter_refs:sourceCase?['lesson-013']:[...new Set(claims.flatMap(c=>c.evidence.map(e=>e.unit_id)))],
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
    const missing=sourceCase?expectedSources.filter(x=>!foundPassages.has(x.passage_id)).map(x=>x.passage_id):required.filter(id=>!foundClaims.has(id));
    observations.push({query_id:'g-b24-'+slug,automatic_retrieval_contract_pass:missing.length===0,missing,queries,
      generated_answer_scored:false,semantic_answer_faithfulness_automatically_proven:false});
  }
  writeFileSync(resolve(out,'stage-g-batch-24.cases.jsonl'),cases.map(x=>JSON.stringify(x)).join('\n')+'\n');
  const report={graph_version:graph.metadata.graph_version,executable_cases:cases.length,final_target_cases:240,
    gold_review_status:'model_reviewed_development',independent_test_set:false,human_gold_reviewed:false,
    retrieval_plan_contract_passed:observations.filter(x=>x.automatic_retrieval_contract_pass).length,observations,
    baselines:{source_keyword:'not_run_in_this_batch',vector:'not_implemented',structured:'query_plans_executed',hybrid:'not_run_in_this_batch'},
    generated_answers_evaluated:false,limits:['不是240题完整验收。','只执行取证计划，不将命中等同回答忠实度。','开发题整理时建立，非独立留出集。']};
  writeFileSync(resolve(out,'stage-g-batch-24.results.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({graph_version:report.graph_version,executable_cases:cases.length,retrieval_plan_contract_passed:report.retrieval_plan_contract_passed,failures:observations.filter(x=>!x.automatic_retrieval_contract_pass)}));
  if(report.retrieval_plan_contract_passed!==cases.length)process.exitCode=1;
} finally {graph.close();}
