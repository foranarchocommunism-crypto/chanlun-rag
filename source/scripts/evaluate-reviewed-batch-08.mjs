// Source-grounded development questions from the manually read lower lessons 78-80.
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
  ['prior-confirmation','B出现笔破坏后回落可以直接判B延续吗？B与前段的关系及首段例外是什么？','含条件的规则查询',
    [cid('078','b-extension-after-break-bottom'),cid('078','destruction-backward-transmission')],['B已确认破坏其前段','每一线段都应破坏前一段'],
    ['先确认B已破坏前段；随后下段破向上破坏笔底才延续；新股最初段无前段。'],['不查B前段即可套用所有分支。','首个上市段也必须有前段。']],
  ['second-inclusion','第二种情况的第二特征序列可以照用第一种跨分界点禁包含的要求吗？','定义及概念边界',
    [cid('078','second-sequence-inclusion-required')],['第二种情况的第二特征序列须严格'],
    ['第二序列严格处理包含，不套第一种跨界禁止规则，相关图绘者选择不当作者观点。'],['两种情况跨界包含口径完全一样。']],
  ['normalize','线段高低点不在真实端点时，标准化是否意味着改掉原分段和证据坐标？','术语与近义消歧',
    [cid('078','standardize-only-basic-unit-analysis')],['无内部结构的基本部件'],
    ['仅在以线段作无内部结构的高层部件时按实际区间标准化；不改真实笔段和原文定位。'],['一律重写原端点。','所有原线段端点必为全段最高最低。']],
  ['trend-outside-legs','1分钟上涨必须在两中枢前后各有一段走势吗？第78课怎样答A+b+B？','跨课规则',
    [cid('078','a-b-b-two-centers-trend')],['A+b+B'],
    ['在17—38上涨例中A+b+B也可，关键两中枢不重合；不能推广任意无方向两中枢。'],['任何上涨都须a+A+b+B+c完整五项。','任何两个中枢都构成上涨。']],
  ['right-unfinished','第79课右图10—11一笔是否已经确认第三段？9跌破7、10不变时又如何？','状态及条件',
    [cid('079','right-diagram-uncompleted-two-more-strokes'),cid('079','right-diagram-nine-below-seven-alternative')],['须再看两笔','9跌破7'],
    ['原图尚未完成，须看后两笔能否成所需分型；9破7且10不变的假设才明确三段，图前无走势。'],['原图已确认三段。','无条件多等两笔即成立。']],
  ['method-capacity','第79课散户第三买点法适合谁？上移背驰能否人人全出？','含条件的规则查询',
    [cid('079','third-method-response-level'),cid('079','third-method-all-exit-skilled-exception')],['有充足时间且交易通道可用','对背驰判断特别有把握'],
    ['充足时间、通道和足以反应级别须同时保留；上移背驰全出是判断特别有把握者的替代法。'],['无时间和通道也照用小级别。','所有人首次背驰都必须全出。']],
  ['first-center-preference','第79课只做第一个中枢三买，是绝对禁止第二中枢，还是方法偏好？','量词与条件',
    [cid('079','prefer-first-center-third-buy')],['尽量只参与第一个'],
    ['尽量是资金时间效率方法的偏好；后中枢扩成更大中枢的概率判断没有统计样本。'],['第二中枢不存在三买。','项目实测后中枢扩张概率已知。']],
  ['fractal-one-way','有小级别一二买卖点就必然有大级别分型吗？','定义及概念边界',
    [cid('079','fractal-small-points-one-way')],['不一定形成大级别分型'],
    ['大分型有某小级别一二点，反方向不必成立；分型辅助而非等价。'],['大小级别绝对双向一一对应。']],
  ['quote-boundary','下册PDF162表扬网友后，哪些段属于网友，作者的这就如同下棋仍是网友吗？','身份隔离',
    [],[],['162-b003/004是网友署名与原话，b005起恢复作者解盘及文章16:00:16时间。'],['自网友署名起直到下一文章都是reader。','把网友原话改为作者发言。']],
  ['corrected-level','9月13日为何改96—99分段？更正后93起回抽已是1分钟走势吗？','明确修订与证据',
    [cid('080','sep13-wrong-level-explicit-correction'),cid('080','sep13-corrected-96-conditional')],['错把绿箭头中一折','跌破96则1分钟中枢形成'],
    ['小折不成笔而段至少三笔；更正为线段类上涨且尚无1分钟中枢，未来破96才成中枢，不破则97段延伸。'],['把原错图的96—99中枢继续当现时事实。','未到未来条件先宣布中枢已成。']],
  ['pure-center','后期笔线段定义推翻了前55课的纯理论中枢吗？','跨课概念边界',
    [cid('080','early-pure-center-not-overturned')],['明确否认后期'],
    ['作者明确说没有推翻；早期纯理论逐笔成交入口与实用划分有别。'],['只按后课日期自动废弃前定义。','线段等于成交分笔。']],
  ['later-explicit-completion','第80课都一段的简答是否完整？第81课如何按5与7补全两图？','明确修订与证据',
    [cid('081','two-diagrams-conditional-answer')],['5＝7'],
    ['作者明确承认下午答复不完整；5=7或5<7均一段，5>7均三段，保留原答复而不无条件套用。'],['两图永远都是一段。','仅因日期新就自行宣布推翻旧答。']],
];

try{
  const cases=[],observations=[];
  for(const [slug,question,type,required,terms,conditions,forbidden] of specifications){
    const claims=required.map(id=>{const r=graph.getClaim(id);assert.ok(r,id);return r;});
    const special=slug==='quote-boundary';
    const plan=special?[{command:'page',args:{documentId:'volume_2.pdf',page:162}}]:terms.map(query=>({command:'search',args:{query,limit:20}}));
    const expectedSources=special?[
      {document_id:'volume_2-5332cd1b6038',pdf_page:162,passage_id:'volume_2-5332cd1b6038-p0162-b003',role:'reader'},
      {document_id:'volume_2-5332cd1b6038',pdf_page:162,passage_id:'volume_2-5332cd1b6038-p0162-b004',role:'reader'},
      {document_id:'volume_2-5332cd1b6038',pdf_page:162,passage_id:'volume_2-5332cd1b6038-p0162-b005',role:'author_commentary'},
    ]:claims.flatMap(c=>c.evidence.map(e=>({document_id:e.document_id,pdf_page:e.pdf_page,printed_page:e.printed_page,passage_id:e.passage_id,role:e.role})));
    cases.push({query_id:'g-b08-'+slug,query_text:question,query_type:type,
      required_concepts:[...new Set(claims.flatMap(c=>c.concept_ids))],required_claims:required,
      expected_evidence_ids:[...new Set(claims.flatMap(c=>c.evidence.map(e=>e.id)))],
      expected_chapter_refs:special?['lesson-080']:[...new Set(claims.flatMap(c=>c.evidence.map(e=>e.unit_id)))],
      acceptable_answer_conditions:conditions,forbidden_inferences:forbidden,
      ambiguity_notes:special?['只162-b003/004为网友引文；162-b005起恢复作者解盘，不将引用后的整篇留为reader。']:claims.filter(c=>c.ambiguity_status!=='none').map(c=>c.ambiguity_status),
      difficulty:required.length>1||special?'medium':'basic',
      scoring_rubric:{retrieval:'取证计划须取得所列命题或页内发言。',answer:'回答全部保留条件且不作禁止推论；本次未运行回答生成评分。'},
      expected_source_refs:expectedSources,expected_speaker_roles:[...new Set(expectedSources.map(s=>s.role))],
      expected_kind:special?[]:['explicit'],expected_review_status:special?[]:['reviewed'],
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
    observations.push({query_id:'g-b08-'+slug,automatic_retrieval_contract_pass:missing.length===0,missing,queries,
      generated_answer_scored:false,semantic_answer_faithfulness_automatically_proven:false});
  }
  writeFileSync(resolve(out,'stage-g-batch-08.cases.jsonl'),cases.map(x=>JSON.stringify(x)).join('\n')+'\n');
  const report={graph_version:graph.metadata.graph_version,executable_cases:cases.length,final_target_cases:240,
    gold_review_status:'model_reviewed_development',independent_test_set:false,human_gold_reviewed:false,
    retrieval_plan_contract_passed:observations.filter(x=>x.automatic_retrieval_contract_pass).length,
    observations,baselines:{source_keyword:'not_run_in_this_batch',vector:'not_implemented',structured:'query_plans_executed',hybrid:'not_run_in_this_batch'},
    generated_answers_evaluated:false,limits:['不是240题完整验收。','只检查取证计划取得预定证据，不把检索命中等同回答忠实度或人工语义评分。','开发题在整理时建立，未作为独立留出集。']};
  writeFileSync(resolve(out,'stage-g-batch-08.results.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({graph_version:report.graph_version,executable_cases:cases.length,retrieval_plan_contract_passed:report.retrieval_plan_contract_passed,failures:observations.filter(x=>!x.automatic_retrieval_contract_pass)}));
}finally{graph.close();}
