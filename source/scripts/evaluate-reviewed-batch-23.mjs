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
    "lip-wet-definition",
    "唇吻与湿吻是否都要求短线已穿长线、而湿吻一定反复多次？",
    "吻定义",
    [
      "upper-l011-c-stage-lip-kiss-definition",
      "upper-l011-c-stage-wet-kiss-definition"
    ],
    [
      "唇吻指短期均线",
      "湿吻指短期均线"
    ],
    [
      "唇吻靠近未穿而续原趋势；湿吻已穿，甚至反复不是必需反复。"
    ],
    [
      "唇吻已经交叉、湿吻必须反复多次。"
    ]
  ],
  [
    "flying-strong-qualitative",
    "飞吻怎样定义，是否在强趋势里反而不常有，概率有实测吗？",
    "定义与经验",
    [
      "upper-l011-c-stage-flying-kiss-definition",
      "upper-l011-c-stage-flying-kiss-strong-trend-and-later-shake"
    ],
    [
      "飞吻指短期均线",
      "飞吻出现较少，一般在特别强"
    ],
    [
      "短线略平后续原势；飞吻总体少，通常特强趋势，过强难久为作者定性经验非频率数据。"
    ],
    [
      "飞吻必交叉或强趋势不可能飞吻，已统计胜率。"
    ]
  ],
  [
    "position-relative-system",
    "女上位和男上位何指？5日强10日弱矛盾吗？",
    "均线体位/相对评价",
    [
      "upper-l011-c-stage-average-position-short-above-long-bull",
      "upper-l011-c-stage-relative-strength-five-versus-ten"
    ],
    [
      "短线上、长线下称女上位",
      "同一走势可在5日线上而在10日线下"
    ],
    [
      "短上为女、短下为男，是该均线系统评价；相对5与10可强弱不同，不等所有级别牛熊。"
    ],
    [
      "男上位就是多头，5强必10强。"
    ]
  ],
  [
    "wet-first-exception-no-risk-free",
    "长期男上位后湿吻下跌就必能抄底获利吗？第一次有没有例外？",
    "例外与风险",
    [
      "upper-l011-c-stage-wet-kiss-two-turn-paths-first-exception",
      "upper-l012-c-stage-any-entry-risk-no-perfect-kiss-prediction"
    ],
    [
      "不适用于趋势形成的第一次湿吻",
      "任何位置介入都存在风险"
    ],
    [
      "有先续原势陷阱后转与反复成箱转两支，第一次湿吻例外必须留；任何位置有风险，不能100%预知。"
    ],
    [
      "第一次湿吻也无条件安全且必买。"
    ]
  ],
  [
    "average-points-not-strict-only",
    "第12课两个买点等严格一二类买点吗？其他点都绝对禁止吗？",
    "概念边界与后文限定",
    [
      "upper-l012-c-stage-two-average-buy-points-not-risk-free",
      "upper-l012-c-stage-system-only-two-principle-and-later-clarification"
    ],
    [
      "该均线系统第一买点是男上位",
      "随后澄清并非其他点不能买"
    ],
    [
      "该两点按均线体位/背弛定义，不直接等后课严格三类点；选系统遵原则但其他点可买风险更高，只是一招。"
    ],
    [
      "两种一二买完全等价，所有其他点都不能买。"
    ]
  ],
  [
    "second-buy-first-sell",
    "均线系统买二卖一何指？第一第二卖点怎么分？",
    "买卖不对称",
    [
      "upper-l012-c-stage-prefer-second-buy-first-sell-asymmetry",
      "upper-l012-c-stage-two-average-sell-points"
    ],
    [
      "一般偏好在第二买点买",
      "该均线系统买入后等待卖点"
    ],
    [
      "买偏第二、卖尽量第一；女上缠绕后背弛第一卖，转男首缠绕高点第二卖，均非严格类点通称。"
    ],
    [
      "所有系统强制买一卖二或卖点不看体位。"
    ]
  ],
  [
    "first-continuation-last-reversal",
    "首次女上缠绕只看次数就100%中继吗？男上最后一次事前能确定吗？",
    "联合条件与不确定性",
    [
      "upper-l012-c-stage-first-bull-entanglement-force-volume-conditions",
      "upper-l012-c-stage-bear-last-entanglement-divergent-drop-entry"
    ],
    [
      "初次前5日应强劲",
      "不能100%预知哪次是最后"
    ],
    [
      "女上首次需看前5日力度与量，概率未实测；男上最后需后续急跌背弛，事前不100%确认，首次肯定非最后是作者原系统措辞。"
    ],
    [
      "只数次数即必然，任何急跌都抄。"
    ]
  ],
  [
    "early-entry-no-t0-exceptions",
    "没有T+0是否所有人任何早盘都不能买？30天持有无例外吗？",
    "执行例外",
    [
      "upper-l010-c-stage-morning-entry-t0-exceptions",
      "upper-l011-c-stage-thirty-average-hold-acceleration-exception-case"
    ],
    [
      "通常不主张早上买股",
      "30天线有效跌破前可中线持有"
    ],
    [
      "通常早盘不买有强突破和中线逐步建仓例外；000851的30天规则有放量加速上涨例外，不能泛化全部股票。"
    ],
    [
      "任何早盘都禁止，任何情况都等30天破才卖。"
    ]
  ],
  [
    "position-context-full-small",
    "600028/600019追高后作者要求全部卖吗？原介入期限重要吗？",
    "仓位与期限",
    [
      "upper-l010-c-stage-full-position-reduce-vs-small-position-hold-case",
      "upper-l010-c-stage-entry-horizon-plan-position-before-fluctuation"
    ],
    [
      "若满仓可借短冲减仓",
      "买入前须定理由、期限"
    ],
    [
      "当时中线未完是前提，满仓减一些/低仓可留；先定中短期限、模式和仓位，不等普遍永不卖出。"
    ],
    [
      "不问仓位期限全部抛或全部永持。"
    ]
  ],
  [
    "news-and-personal-standard",
    "问美元大跌影响或股票调整到位，作者怎样重构问题？",
    "观察与介入标准",
    [
      "upper-l010-c-stage-news-test-market-reaction-not-prediction",
      "upper-l010-c-stage-own-standard-capital-experience-before-trade"
    ],
    [
      "市场对所有消息的综合反应",
      "是否符合自己的介入标准"
    ],
    [
      "看综合走势反应而非单消息预测；标准依资金经验，未定标准先停想清；不表示结构定义任意。"
    ],
    [
      "按单消息直接预测涨跌，不需预定标准。"
    ]
  ],
  [
    "replay-source-identity",
    "2005喜欢数学的女孩转载能标成普通读者，或直接当已外证的作者原博客吗？",
    "回放身份",
    [],
    [],
    [
      "外层11/27文章自称旧名转载，六段保留unknown及原署名/日期，原站未核；既不是普通读者也未升级直接作者证据。"
    ],
    [
      "原站已校对或读者发言自动归作者。"
    ]
  ],
  [
    "weekly-case-no-year-invention",
    "000958例子原文给2005年吗？最好点已过是绝对不能买吗？",
    "图文日期及原话限定",
    [
      "upper-l012-c-stage-000958-weekly-two-points-not-best-now"
    ],
    [
      "答000958时作者用5/10周系统"
    ],
    [
      "原文只写7/22约2.2与11/3约2.6，不据后图补2005；当时不是不能买而是最佳位置已过，资金/期限决定月周日。"
    ],
    [
      "正文明确2005且绝对禁止后续买。"
    ]
  ]
];

try {
  const cases=[],observations=[];
  for(const [slug,question,type,required,terms,conditions,forbidden] of specifications){
    const claims=required.map(id=>{const c=graph.getClaim(id);assert.ok(c,id);return c;});
    const replay=type==='回放身份';
    const plan=replay?[{command:'page',args:{documentId:'volume_1.pdf',page:33}},{command:'page',args:{documentId:'volume_1.pdf',page:34}}]:terms.map(query=>({command:'search',args:{query,limit:20}}));
    assert.ok(plan.length<=2);
    let expectedSources=claims.flatMap(c=>c.evidence.map(e=>({document_id:e.document_id,pdf_page:e.pdf_page,
      printed_page:e.printed_page,passage_id:e.passage_id,role:e.role,speaker:e.speaker})));
    if(replay)expectedSources=graph.db.prepare("SELECT p.document_id,p.pdf_page,pg.printed_page,p.id AS passage_id,p.role,p.speaker FROM passages p JOIN pages pg ON pg.document_id=p.document_id AND pg.pdf_page=p.pdf_page WHERE p.document_id='volume_1-a53e99c37ca5' AND p.id IN ('volume_1-a53e99c37ca5-p0033-b004','volume_1-a53e99c37ca5-p0033-b005','volume_1-a53e99c37ca5-p0033-b006','volume_1-a53e99c37ca5-p0034-b000','volume_1-a53e99c37ca5-p0034-b001','volume_1-a53e99c37ca5-p0034-b002') ORDER BY p.id").all();
    cases.push({query_id:'g-b23-'+slug,query_text:question,query_type:type,
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
    const missing=replay?expectedSources.filter(x=>!foundPassages.has(x.passage_id)).map(x=>x.passage_id):required.filter(id=>!foundClaims.has(id));
    observations.push({query_id:'g-b23-'+slug,automatic_retrieval_contract_pass:missing.length===0,missing,queries,
      generated_answer_scored:false,semantic_answer_faithfulness_automatically_proven:false});
  }
  writeFileSync(resolve(out,'stage-g-batch-23.cases.jsonl'),cases.map(x=>JSON.stringify(x)).join('\n')+'\n');
  const report={graph_version:graph.metadata.graph_version,executable_cases:cases.length,final_target_cases:240,
    gold_review_status:'model_reviewed_development',independent_test_set:false,human_gold_reviewed:false,
    retrieval_plan_contract_passed:observations.filter(x=>x.automatic_retrieval_contract_pass).length,observations,
    baselines:{source_keyword:'not_run_in_this_batch',vector:'not_implemented',structured:'query_plans_executed',hybrid:'not_run_in_this_batch'},
    generated_answers_evaluated:false,limits:['不是240题完整验收。','只执行取证计划，不将命中等同回答忠实度。','开发题整理时建立，非独立留出集。']};
  writeFileSync(resolve(out,'stage-g-batch-23.results.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({graph_version:report.graph_version,executable_cases:cases.length,retrieval_plan_contract_passed:report.retrieval_plan_contract_passed,failures:observations.filter(x=>!x.automatic_retrieval_contract_pass)}));
  if(report.retrieval_plan_contract_passed!==cases.length)process.exitCode=1;
} finally {graph.close();}
