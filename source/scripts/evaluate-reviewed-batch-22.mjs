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
    "running-fees-and-decomposition",
    "30分钟反弹都等上下上完再卖，首上低点买入能保证收益吗？",
    "奔走型/费用和次级分段",
    [
      "lower-l107-c-stage-running-rebound-later-high-not-guaranteed",
      "lower-l107-c-stage-segment-from-first-rise-author-safety-wording"
    ],
    [
      "上下上反弹的末上不保证",
      "30分钟反弹按5分钟节奏"
    ],
    [
      "末上可仅触首上低点，手续费后不保证；30按5分段为作者方案，安全仍有制度执行边界。"
    ],
    [
      "后上必创新高且收益无条件保证。"
    ]
  ],
  [
    "t1-second-sell-alternatives",
    "107分段安全是否消除T+1？低开后第二类卖点的两个条件是且吗？",
    "执行约束与替代条件",
    [
      "lower-l107-c-stage-aug21-t1-first-sell-second-sell-after-low-open"
    ],
    [
      "T+1可能使首类卖点无法卖出"
    ],
    [
      "T+1可能卖不出首卖，首次次级别回拉不破顶或盘整背驰；95%为作者历史回顾非本项目验证。"
    ],
    [
      "T+1不限制首卖，必须不破顶且盘背，所有本次规避95%。"
    ]
  ],
  [
    "formation-versus-completed",
    "首中枢后三买并非背驰是不是已经完成两中枢上涨？",
    "形成与完成",
    [
      "lower-l107-c-stage-uptrend-formation-wording-not-completed-type",
      "upper-l017-trend-definition"
    ],
    [
      "上升趋势形成的精确定义",
      "趋势是至少包含两个依次同向"
    ],
    [
      "107形成联合信号与17完成走势至少两个同向中枢并列，未出现撤回；持有还须无扭转信号。"
    ],
    [
      "107日期晚自动把17改成完成趋势只要一中枢。"
    ]
  ],
  [
    "partition-directions",
    "107反弹上下上是否否定64课标准上涨中枢下上下？",
    "分解语境",
    [
      "lower-l107-c-stage-center-three-subtypes-up-down-up-context",
      "lower-l064-uptrend-center-standard-decomposition"
    ],
    [
      "用上下上三个5分钟走势类型",
      "标准分解中，可把上涨趋势中枢"
    ],
    [
      "分别保留反弹操作分解和标准上涨中枢语境、结合律及分解多样性，未直接覆盖。"
    ],
    [
      "所有上涨中枢无条件都改上下上。"
    ]
  ],
  [
    "rotation-capacity-not-half",
    "平均效率更高是否要求所有人一半底仓、另一半全仓轮动？",
    "资金/能力与经验",
    [
      "lower-l107-c-stage-rotation-efficiency-part-position-higher-skill"
    ],
    [
      "分段安全方案并非平均效率最高"
    ],
    [
      "部分仓位无固定半仓，小资金可全仓轮动但技术更高；作者评价没有比较收益样本。"
    ],
    [
      "无条件固定半仓并已验证效率最优。"
    ]
  ],
  [
    "bottom-precise-failure-and-coarse",
    "第一类买点出现就底部成功吗？分型底部是否等于精确走势类型？",
    "底部两入口",
    [
      "lower-l108-c-stage-bottom-precise-first-buy-to-first-third-point",
      "lower-l108-c-stage-fractal-bottom-coarser-entry"
    ],
    [
      "到其引发中枢首次走出第三类买卖点前",
      "以分型定义底部称为较粗糙"
    ],
    [
      "底部按级别，从一买到其引发中枢首次三点前；先三卖失败、先三买成功；分型是粗略入口不强求等价。"
    ],
    [
      "任何一买都已成功且分型区间等精确中枢。"
    ]
  ],
  [
    "fractal-confirmation-versus-entry",
    "分型上沿有效站住就是最佳买点和严格走势类型完成吗？",
    "确认与入场",
    [
      "lower-l108-c-stage-fractal-bottom-low-fail-upper-success-at-least-stroke",
      "lower-l108-c-stage-buy-failed-down-probe-not-upper-boundary"
    ],
    [
      "分型角度的底部是底分型所构区间",
      "在区间下探失败时买"
    ],
    [
      "最低点破则失败，上沿有效站住是分型意义成功/至少一笔措辞；买入按下探失败，不能升级成严格类型已完。"
    ],
    [
      "上沿就必最佳买点且所有严格级别条件都已满足。"
    ]
  ],
  [
    "month-candidate-and-confirmation",
    "8/29给2284/2952是不是保证9月已确认月线行情？",
    "月候选/确认",
    [
      "lower-l108-c-stage-aug29-month-2284-no-break-september",
      "lower-l108-c-stage-month-no-market-before-october-effective-2952"
    ],
    [
      "8月K线给月区间2284",
      "10月有效确认站住2952前"
    ],
    [
      "破2284将候选延后，10月有效2952前仅月分型底部构造；图2009行情不倒填，正文课程仅8/29。"
    ],
    [
      "9月已经保证成功且用图09:15:01补作者正文时间。"
    ]
  ],
  [
    "week-day-exception",
    "周2284/2601与日2284/2455是否一个区间，2523有何例外？",
    "月周日层次",
    [
      "lower-l108-c-stage-week-2284-2601-containment-2523-exception",
      "lower-l108-c-stage-day-bottom-2284-2455-still-building"
    ],
    [
      "走出底部还须2284—2601有效突破",
      "最终是否有效看2284—2455"
    ],
    [
      "周与日分开；周含包含且中秋前不能确认的原例有8/29突破2523例外，图小数不改正文整数。"
    ],
    [
      "日底成就等于周月底且删2523例外。"
    ]
  ],
  [
    "sep12-role-and-ninety",
    "9/12是读者声称90%还是作者解盘？90%是库内回测概率吗？",
    "身份与概率",
    [
      "lower-l108-c-stage-sep12-nonfirst-center-ninety-estimate"
    ],
    [
      "9月12日作者说小反弹后继续下跌"
    ],
    [
      "原页同栏目作者解盘，426结束语非读者；非首中枢下跌为语境，可先再破2000，90%多是作者估计非独立统计。"
    ],
    [
      "读者言论可直接归作者或90%已回测。"
    ]
  ],
  [
    "new-level-day-week-confirmation",
    "9/25日笔无问题能否视周笔已成？9/11下一买点为何换视角？",
    "层次及日期",
    [
      "lower-l108-c-stage-sep25-daily-stroke-confirmed-weekly-open",
      "lower-l108-c-stage-sep11-larger-center-next-buy-new-level"
    ],
    [
      "9月25日作者说未破5日线",
      "下一买点须站在新级别数中枢"
    ],
    [
      "9/25日笔确认但周笔仍期望；9/11较大中枢后再跌要在新级别数；尾头日期只管后文。"
    ],
    [
      "9/25自动标9/26且周笔已确认，仍按原小级数。"
    ]
  ],
  [
    "aesthetic-period-and-macd-open",
    "一年最美、17/18月与月MACD回零轴能保证某月见底吗？",
    "经验周期非硬时钟",
    [
      "lower-l108-c-stage-sep1-october-beauty-not-timing-rule",
      "lower-l108-c-stage-sep1-month-macd-zero-pullback-open-dates"
    ],
    [
      "从美学称10月见底",
      "月线MACD回零轴后的中级回拉"
    ],
    [
      "作者美学/经验预测，市场自行选择，10月或次年3/4月取决条件；未声称当时月MACD底背驰已确认。"
    ],
    [
      "固定月份必须见底且回零轴就是背驰。"
    ]
  ]
];

try {
  const cases=[],observations=[];
  for(const [slug,question,type,required,terms,conditions,forbidden] of specifications){
    const claims=required.map(id=>{const c=graph.getClaim(id);assert.ok(c,id);return c;});
    const plan=terms.map(query=>({command:'search',args:{query,limit:20}}));
    assert.ok(plan.length<=2);
    const expectedSources=claims.flatMap(c=>c.evidence.map(e=>({document_id:e.document_id,pdf_page:e.pdf_page,
      printed_page:e.printed_page,passage_id:e.passage_id,role:e.role,speaker:e.speaker})));
    cases.push({query_id:'g-b22-'+slug,query_text:question,query_type:type,
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
    observations.push({query_id:'g-b22-'+slug,automatic_retrieval_contract_pass:missing.length===0,missing,queries,
      generated_answer_scored:false,semantic_answer_faithfulness_automatically_proven:false});
  }
  writeFileSync(resolve(out,'stage-g-batch-22.cases.jsonl'),cases.map(x=>JSON.stringify(x)).join('\n')+'\n');
  const report={graph_version:graph.metadata.graph_version,executable_cases:cases.length,final_target_cases:240,
    gold_review_status:'model_reviewed_development',independent_test_set:false,human_gold_reviewed:false,
    retrieval_plan_contract_passed:observations.filter(x=>x.automatic_retrieval_contract_pass).length,observations,
    baselines:{source_keyword:'not_run_in_this_batch',vector:'not_implemented',structured:'query_plans_executed',hybrid:'not_run_in_this_batch'},
    generated_answers_evaluated:false,limits:['不是240题完整验收。','只执行取证计划，不将命中等同回答忠实度。','开发题整理时建立，非独立留出集。']};
  writeFileSync(resolve(out,'stage-g-batch-22.results.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({graph_version:report.graph_version,executable_cases:cases.length,retrieval_plan_contract_passed:report.retrieval_plan_contract_passed,failures:observations.filter(x=>!x.automatic_retrieval_contract_pass)}));
  if(report.retrieval_plan_contract_passed!==cases.length)process.exitCode=1;
} finally {graph.close();}
