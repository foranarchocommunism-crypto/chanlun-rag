// Source-grounded development questions from the manually read lower lessons 82-84.
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
  ['fractal-word','分型就是数学分形在股票上的应用吗？','术语与近义消歧',
    [cid('082','fractal-not-fractal-theory')],['其“分型”与数学分形'],
    ['作者明确区分两词，称自身逻辑来自市场；不替作者认证所有分形理论无效。'],['分型与分形是同义。','用外部分形定义覆盖作者K线分型。']],
  ['inclusion-psychology','所有包含关系都代表犹豫吗？阴吞阳是否有例外？','例外与条件不足',
    [cid('082','inclusion-psychology-exception')],['长阴直接吞掉阳线'],
    ['一般包含的犹豫心理解释明确排除长阴直接吃阳，形式定义与心理经验分开。'],['所有包含都只能犹豫而不可能转折强。']],
  ['third-no-expansion','第82课小级别三卖后就必然成日线笔吗？','含条件的规则查询',
    [cid('082','third-sell-no-expansion-stroke')],['该卖点不形成中枢扩张'],
    ['须该日顶对应中枢三卖且不扩张，几乎100%是作者主张非项目样本统计。'],['一见任意三卖就必然日笔。','项目实测胜率近100%。']],
  ['break-top-third-buy','日顶不成笔并有效破顶，某级别三买是必要还是充分条件？','量词与条件',
    [cid('082','no-stroke-break-top-needs-third-buy')],['最终有效破坏该顶分型'],
    ['作者要求出现某级别三买，是必要条件；短暂新高本身不证明有效破顶。'],['任意三买充分保证该日顶破坏。']],
  ['stroke-base','作者说绝对不允许用笔构最小中枢，还是可设计但较不稳定？','定义及概念边界',
    [cid('083','stroke-center-possible-less-stable')],['可以设计用笔构造'],
    ['可以设计，以线段为部件是偶然因素较少的稳定性取舍。'],['作者说笔构任何最小中枢数学上绝不可能。']],
  ['rename','第84课为何把自相似性结构改称自同构性结构，是否改掉了早课原引文？','明确修订与证据',
    [cid('084','explicit-self-structure-rename')],['以后统一称'],
    ['作者明确觉得旧称不精确且易混分形；只关联其自身术语改称，不改旧引文或合并所有数学概念。'],['所有数学自相似都等同自同构。','旧课引文已静默替换。']],
  ['different-functions','递归的起始f1和后续f2必须是相同函数，且f1前还得递归吗？','定义及概念边界',
    [cid('084','two-recursion-functions')],['f1与f2可以完全不同'],
    ['f1起始和f2后续可不同，f1前无需再递归；公式原排字不直接当数值自增代码。'],['每级必须重做同一个f1。','an+1必定是价格数值加一。']],
  ['replace-unique','能随便换成收盘价或成交量入口吗？更高级别还必须数笔吗？','跨课前提查证',
    [cid('084','fractal-only-recursion-start-optional'),cid('084','base-and-higher-use-different-rules')],['前提是保证分解唯一性','其上级别再用另一套'],
    ['替代入口须保分解唯一性，原文未给完整替代算法；基底之上使用后续规则而非每层重数笔。'],['任何入口无条件有效。','作者已经给出可直接部署的成交量替代算法。']],
  ['level-duration','走势生长足够多年后必然升级吗？级别与K线时间怎样区分？','定义及概念边界',
    [cid('084','level-not-time-classification')],['作者举100年说明'],
    ['级别按规则结构生长，没有时长绝对保证；100年为说明例而非回测参数。'],['经过固定分钟或年数必升一级。','K线周期等于走势级别。']],
  ['reprint-identity','下册PDF211证券法10%与华生访谈，是否都是缠中说禅亲自发言？','身份隔离',
    [],[],['该段为转贴访谈，role unknown且speaker表明转载原作者未核；作者只在引言表达自己的意见。'],['全篇因在作者博客转贴便都是作者直接证据。','把历史10%引述当现行法律结论。']],
  ['three-phrase','第83课写三个特征序列分型，能据此把破坏规则改成必须三个分型吗？','无答案与原文疑点',
    [cid('080','feature-sequence-three-elements-general')],[],['保存该心理原句并与三个元素才可能有分型的明确条件对照，数量措辞待核；不补三个分型必要算法，亦不把三个K足以成笔。'],['作者已严格定义必须三套特征序列分型。','心理简称可替换严格笔条件。']],
  ['late-confirmation','10月8日139段已经确认完了吗？配图有140/141能否反填确认？','图文关系与状态',
    [cid('084','oct8-139-not-confirmed')],['139起线段尚未确认结束'],
    ['当日未确认，次日开盘破5685才可标140；图含10/09后期数据，不能倒填完成。'],['只因后期图有140就说作者10/8已经确认。']],
];

try{
  const cases=[],observations=[];
  for(const [slug,question,type,required,terms,conditions,forbidden] of specifications){
    const claims=required.map(id=>{const r=graph.getClaim(id);assert.ok(r,id);return r;});
    const special=['reprint-identity','three-phrase'].includes(slug);
    const specialPage=slug==='reprint-identity'?211:196;
    const plan=special?[
      {command:'page',args:{documentId:'volume_2.pdf',page:specialPage}},
      slug==='reprint-identity'?{command:'page',args:{documentId:'volume_2.pdf',page:209}}:
        {command:'search',args:{query:'三个元素才可能形成分型',limit:20}},
    ]:terms.map(query=>({command:'search',args:{query,limit:20}}));
    const expectedSources=special?[
      {document_id:'volume_2-5332cd1b6038',pdf_page:specialPage,
       passage_id:slug==='reprint-identity'?'volume_2-5332cd1b6038-p0211-b008':'volume_2-5332cd1b6038-p0196-b009',
       role:slug==='reprint-identity'?'unknown':'author_body',
       speaker:slug==='reprint-identity'?'转载文（含华生访谈，原文作者未核）':'缠中说禅'},
      ...(slug==='reprint-identity'?[{document_id:'volume_2-5332cd1b6038',pdf_page:209,
        passage_id:'volume_2-5332cd1b6038-p0209-b004',role:'author_commentary',speaker:'缠中说禅'}]:[]),
      ...claims.flatMap(c=>c.evidence.map(e=>({document_id:e.document_id,pdf_page:e.pdf_page,
        printed_page:e.printed_page,passage_id:e.passage_id,role:e.role,speaker:e.speaker}))),
    ]:claims.flatMap(c=>c.evidence.map(e=>({document_id:e.document_id,pdf_page:e.pdf_page,printed_page:e.printed_page,passage_id:e.passage_id,role:e.role})));
    cases.push({query_id:'g-b09-'+slug,query_text:question,query_type:type,
      required_concepts:[...new Set(claims.flatMap(c=>c.concept_ids))],required_claims:required,
      expected_evidence_ids:[...new Set(claims.flatMap(c=>c.evidence.map(e=>e.id)))],
      expected_chapter_refs:[...new Set([...(special?[slug==='reprint-identity'?'lesson-084':'lesson-083']:[]),
        ...claims.flatMap(c=>c.evidence.map(e=>e.unit_id))])],
      acceptable_answer_conditions:conditions,forbidden_inferences:forbidden,
      ambiguity_notes:special?[slug==='reprint-identity'?'第三方转载保留原文，不升级缠中说禅作者证据。':'本段心理数量措辞待核，不替代前课严格笔条件与三个元素才可能成分型。']:claims.filter(c=>c.ambiguity_status!=='none').map(c=>c.ambiguity_status),
      difficulty:required.length>1||special?'medium':'basic',
      scoring_rubric:{retrieval:'取证计划须取得所列命题或页内发言。',answer:'回答全部保留条件且不作禁止推论；本次未运行回答生成评分。'},
      expected_source_refs:expectedSources,expected_speaker_roles:[...new Set(expectedSources.map(s=>s.role))],
      expected_kind:claims.length?['explicit']:[],expected_review_status:claims.length?['reviewed']:[],
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
    observations.push({query_id:'g-b09-'+slug,automatic_retrieval_contract_pass:missing.length===0,missing,queries,
      generated_answer_scored:false,semantic_answer_faithfulness_automatically_proven:false});
  }
  writeFileSync(resolve(out,'stage-g-batch-09.cases.jsonl'),cases.map(x=>JSON.stringify(x)).join('\n')+'\n');
  const report={graph_version:graph.metadata.graph_version,executable_cases:cases.length,final_target_cases:240,
    gold_review_status:'model_reviewed_development',independent_test_set:false,human_gold_reviewed:false,
    retrieval_plan_contract_passed:observations.filter(x=>x.automatic_retrieval_contract_pass).length,
    observations,baselines:{source_keyword:'not_run_in_this_batch',vector:'not_implemented',structured:'query_plans_executed',hybrid:'not_run_in_this_batch'},
    generated_answers_evaluated:false,limits:['不是240题完整验收。','只检查取证计划取得预定证据，不把检索命中等同回答忠实度或人工语义评分。','开发题在整理时建立，未作为独立留出集。']};
  writeFileSync(resolve(out,'stage-g-batch-09.results.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({graph_version:report.graph_version,executable_cases:cases.length,retrieval_plan_contract_passed:report.retrieval_plan_contract_passed,failures:observations.filter(x=>!x.automatic_retrieval_contract_pass)}));
}finally{graph.close();}
