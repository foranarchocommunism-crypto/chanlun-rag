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
    "early-category-platform-exception",
    "第15课高低点三分类是后来最严格定义吗？等高等低和顺势平台怎么办？",
    "定义与明确限定",
    [
      "upper-l015-c-stage-chart-consolidation-expanding-or-contracting",
      "upper-l016-c-stage-platform-exception-initial-definition-not-strict"
    ],
    [
      "高点更高且低点更低，或高点更低且低点更高",
      "当前趋势/盘整通用定义不完全严格"
    ],
    [
      "保留早期两分支且/或，等高等低未列；16作者明说暂不严格、顺势平台例外，价值中枢是未来术语不与宏观估值自动合并。"
    ],
    [
      "早期已完全严格且任意等高低算法是作者明说。"
    ]
  ],
  [
    "ma-area-versus-average-and-macd",
    "趋势力度和平均力度是什么，等MACD柱面积吗，平均变弱是已确认背驰？",
    "面积定义及确认",
    [
      "upper-l015-c-stage-trend-force-between-kisses-area",
      "upper-l015-c-stage-average-force-area-divided-by-time"
    ],
    [
      "前吻结束至后吻开始",
      "前吻结束至当下两均线所形成面积除以时间"
    ],
    [
      "两均线面积按吻界定，平均为到当下面积除时间；同向比较变弱是将形成，仍看延伸长度；非MACD面积，算法口径未全给。"
    ],
    [
      "直接是MACD积分或变弱已保证同步转折无风险。"
    ]
  ],
  [
    "histogram-peak-not-price-turn",
    "今天红柱短于昨天就背驰了吗？三天条件和前波比较区别何在？",
    "柱波/完整背驰",
    [
      "upper-l015-c-stage-patch-peak-three-day-turn-not-price-turn",
      "upper-l015-c-stage-histogram-divergence-peak-compare-with-lines"
    ],
    [
      "今日短于昨日且昨日长于前日",
      "该波峰值低于前波峰值"
    ],
    [
      "先确认柱波峰转，再比前后波峰；柱背驰还不够，需DEA/DIFF特别通道，不把柱峰等股价转折。"
    ],
    [
      "一根缩短就是完整趋势背驰并必价格见顶。"
    ]
  ],
  [
    "first-kiss-only-trend-and-later-consolidation",
    "首次缠绕非最后是否禁止盘整一次出现买点，也否定后来的盘整背驰？",
    "条件范围及跨课",
    [
      "upper-l015-c-stage-first-entanglement-exclusion-only-trend-search",
      "upper-l024-c-stage-divergence-default-trend-consolidation-analogy"
    ],
    [
      "只针对趋势中寻找背驰",
      "类似判断用于盘整则称盘整背驰"
    ],
    [
      "首次非最后针对趋势寻背驰，盘整一次可有买点、作者另许周月盘整；24后来明确类比盘整背驰，不据15一句全关盘整操作。"
    ],
    [
      "任意形态首次都不可能买，后课盘整背驰不存在。"
    ]
  ],
  [
    "skill-first-second-and-female-definition",
    "买二一律比买一更好吗？女上位每次回调都叫第二类买点吗？",
    "能力与定义",
    [
      "upper-l015-c-stage-buy-first-if-skilled-second-for-unfamiliar",
      "upper-l015-c-stage-female-later-kisses-not-all-second-buy"
    ],
    [
      "熟悉背弛者第一类买点更好",
      "只把女上位第一次缠绕后定义为第二类买点"
    ],
    [
      "熟者买一更好、不熟者买二降误判；女上只首吻定义二类，其他吻盈利是作者断言非保证。"
    ],
    [
      "所有人永远买二最优且每次回调都二买。"
    ]
  ],
  [
    "box-entry-no-retroactive-horizon",
    "000932的15分钟箱型买入可改等日周一卖吗？小周期是否应全仓进出？",
    "原入场前提",
    [
      "upper-l015-c-stage-000932-box-entry-not-upgrade-to-day-hold",
      "upper-l015-c-stage-small-short-buy-falling-not-full-low-period"
    ],
    [
      "按日/周买点持到日/周卖点须最初",
      "不建议全仓按1/5分钟进出"
    ],
    [
      "日周持有须原在相应日周一二买，箱型不是标准一买不可事后升级；低图小资金可短差、不建议全仓且大资金无效。"
    ],
    [
      "只要套住就改中线，所有资金全仓1分最优。"
    ]
  ],
  [
    "unfinished-patch-multilevel-confirmation",
    "600900日线与30分钟同样已背了吗？正在变长的一片能直接判背驰？",
    "未完/多周期",
    [
      "upper-l015-c-stage-600900-thirty-already-day-not-zero-retest",
      "upper-l015-c-stage-growing-current-patch-not-divergence-confirmed"
    ],
    [
      "30分钟背离早已发生、日线没有",
      "当前红柱仍较昨日长"
    ],
    [
      "30已背、日无，常用组合回轴再上且价新高线柱不高；当前片未完须等缩和前波比较，危险信号不等完整确认。"
    ],
    [
      "所有周期同样已背，当前柱仍长也无须完成。"
    ]
  ],
  [
    "down-up-specific-rule-versus-general-reduce",
    "第16课先减仓和一见盘整全部退矛盾吗？专门方法入场三步是什么？",
    "策略范围",
    [
      "upper-l016-c-stage-first-buy-then-reduce-consolidation-general",
      "upper-l016-c-stage-entry-second-down-exit-new-consolidation"
    ],
    [
      "买后若盘整先减仓",
      "只选下跌+盘整+下跌"
    ],
    [
      "一般风险分析保留部分，专门拒盘整方法只选跌盘跌、第二跌一买入、新盘整退；不是所有方法禁止盘整。"
    ],
    [
      "任意一买都可用且全市场一见盘整必须清。"
    ]
  ],
  [
    "half-probability-profit-300-not-proof",
    "盘整后两种结果就各50%，本法肯定赚并能保证年300%吗？",
    "概率与收益边界",
    [
      "upper-l016-c-stage-profit-and-half-risk-author-assertions",
      "upper-l016-c-stage-half-million-three-stocks-return-rhetoric"
    ],
    [
      "作者断言该方法可用低一级别一卖退出",
      "自称年300%都算差"
    ],
    [
      "半概率/肯定盈利/300%均作者自述无样本；约50万最多3只限该案，无费用/流动性/T+1执行证明。"
    ],
    [
      "项目回测已证明50%/300%或所有资金固定3只。"
    ]
  ],
  [
    "strategy-exclusion-not-no-profit",
    "上涨+下跌后的涨完全不能盈利吗？驰宏日图与30分跌盘跌一样吗？",
    "排除与周期",
    [
      "upper-l016-c-stage-exclude-prior-up-down-not-no-profit",
      "upper-l016-c-stage-chihong-daily-one-down-thirty-three-parts"
    ],
    [
      "不考虑不意味着不能盈利",
      "日图并非跌+盘+跌而只是一跌"
    ],
    [
      "专门策略排除是归高层盘整非无利润；驰宏该段日一跌而30分可跌盘跌，未逐项认可读者8/23为日买。"
    ],
    [
      "策略排除等任何方法不能盈利，两个图分解相同。"
    ]
  ],
  [
    "reader-identity",
    "64页舞者引述追问与无时间作者答复能都当19:59作者观点吗？",
    "来源身份",
    [],
    [],
    [
      "舞者两段为reader且未记时间，随后author_reply也未单记时间，不能承前19:59。"
    ],
    [
      "整段都是作者19:59明说。"
    ]
  ],
  [
    "macd-law-and-put-warning",
    "MACD零轴定律是否过轴就能买，038004作业是邀请买入认购权证吗？",
    "辅助条件与身份",
    [
      "upper-l015-c-stage-macd-law-first-below-second-first-retest",
      "upper-l015-c-stage-038004-risk-warning-homework-not-recommendation"
    ],
    [
      "第一类买点在零轴下背驰形成",
      "该认沽风险极大"
    ],
    [
      "一买轴下背驰/二买首上轴回抽确认还在整体走势语境，不能单项过轴充分；038004为认沽，风险极大/买点早过/不买教学边界明说。"
    ],
    [
      "任何过轴就是完整买点，038004是认购且老师喊买。"
    ]
  ]
];

try {
  const cases=[],observations=[];
  for(const [slug,question,type,required,terms,conditions,forbidden] of specifications){
    const claims=required.map(id=>{const c=graph.getClaim(id);assert.ok(c,id);return c;});
    const sourceCase=type==='来源身份';
    const plan=sourceCase?[{command:'page',args:{documentId:'volume_1.pdf',page:64}}]:terms.map(query=>({command:'search',args:{query,limit:20}}));
    assert.ok(plan.length<=2);
    let expectedSources=claims.flatMap(c=>c.evidence.map(e=>({document_id:e.document_id,pdf_page:e.pdf_page,
      printed_page:e.printed_page,passage_id:e.passage_id,role:e.role,speaker:e.speaker,published_at:e.published_at})));
    if(sourceCase)expectedSources=graph.db.prepare("SELECT p.document_id,p.pdf_page,pg.printed_page,p.id AS passage_id,p.role,p.speaker,p.published_at FROM passages p JOIN pages pg ON pg.document_id=p.document_id AND pg.pdf_page=p.pdf_page WHERE p.id IN ('volume_1-a53e99c37ca5-p0064-b004','volume_1-a53e99c37ca5-p0064-b005','volume_1-a53e99c37ca5-p0064-b006') ORDER BY p.id").all();
    cases.push({query_id:'g-b25-'+slug,query_text:question,query_type:type,
      required_concepts:[...new Set(claims.flatMap(c=>c.concept_ids))],required_claims:required,
      expected_evidence_ids:[...new Set(claims.flatMap(c=>c.evidence.map(e=>e.id)))],
      expected_chapter_refs:sourceCase?['lesson-015']:[...new Set(claims.flatMap(c=>c.evidence.map(e=>e.unit_id)))],
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
    observations.push({query_id:'g-b25-'+slug,automatic_retrieval_contract_pass:missing.length===0,missing,queries,
      generated_answer_scored:false,semantic_answer_faithfulness_automatically_proven:false});
  }
  writeFileSync(resolve(out,'stage-g-batch-25.cases.jsonl'),cases.map(x=>JSON.stringify(x)).join('\n')+'\n');
  const report={graph_version:graph.metadata.graph_version,executable_cases:cases.length,final_target_cases:240,
    gold_review_status:'model_reviewed_development',independent_test_set:false,human_gold_reviewed:false,
    retrieval_plan_contract_passed:observations.filter(x=>x.automatic_retrieval_contract_pass).length,observations,
    baselines:{source_keyword:'not_run_in_this_batch',vector:'not_implemented',structured:'query_plans_executed',hybrid:'not_run_in_this_batch'},
    generated_answers_evaluated:false,limits:['不是240题完整验收。','只执行取证计划，不将命中等同回答忠实度。','开发题整理时建立，非独立留出集。']};
  writeFileSync(resolve(out,'stage-g-batch-25.results.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({graph_version:report.graph_version,executable_cases:cases.length,retrieval_plan_contract_passed:report.retrieval_plan_contract_passed,failures:observations.filter(x=>!x.automatic_retrieval_contract_pass)}));
  if(report.retrieval_plan_contract_passed!==cases.length)process.exitCode=1;
} finally {graph.close();}
