import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { KnowledgeGraph } from '../../src/core.mjs';
import { KnowledgeGraph as DesktopGraph } from '../../../chan-kg-desktop/vendor/core.mjs';

const agent=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
const root=resolve(agent,'../shared-knowledge/v0.1.0');
const sha=path=>createHash('sha256').update(readFileSync(path)).digest('hex');
const before={database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))};
const graph=new KnowledgeGraph(root),desktop=new DesktopGraph(root);
const id=(lesson,slug)=>`lower-l${lesson}-c-stage-${slug}`;
const claim=(lesson,slug)=>{const c=graph.getClaim(id(lesson,slug));assert.ok(c);return c;};
const checks=[];
try {
  assert.equal(graph.db.prepare("SELECT count(*) AS n FROM claims WHERE id LIKE 'lower-l106-c-stage-%' AND review_status='reviewed'").get().n,55);
  const parameters=claim('106','eight-average-parameters-fit-existing-market');
  assert.match(parameters.text,/5、13、21、34、55、89、144、233八个/);assert.match(parameters.review_note,/不插入8/);
  const classes=claim('106','smallest-not-yet-conquered-average-nine-classes');
  assert.match(classes.text,/本次反弹截至当时未曾攻克的最小周期均线.*八条均线分九类/);
  assert.match(classes.review_note,/不直接改成当前价格在几条线上/);
  assert.equal(claim('106','strongest-not-necessarily-currently-above-all').ambiguity_status,'strongest_class_question_not_answered_here');
  checks.push('55新增；八周期不插8，九类按本轮反弹历史未曾攻克最小周期，最强不必当前全在线上之设问未编造详答');
  const strength=claim('106','sector-strength-average-class-number');
  assert.match(strength.text,/成员类别数的平均.*平均数越大越强/);assert.ok(strength.conditions[0].includes('反弹'));
  assert.match(strength.review_note,/未给市值\/成交量加权/);
  assert.equal(graph.query('concept',{id:'缠中说禅板块强弱指标',limit:10}).data.status,'found');
  assert.match(claim('106','leading-sector-dynamics-combine-stock-structure').text,/还须配合具体股票走势分析/);
  assert.match(claim('106','rotation-rhythm-founded-on-buy-sell-points').text,/以买卖点为基础/);
  assert.match(claim('106','program-possible-not-supplied').text,/本节不提供成品/);
  checks.push('板块取同规则类别平均且越大越强，不补市值权重；配合个股买卖点，未把电脑程序设想当成品交付');
  assert.match(claim('106','average-level-no-necessary-correspondence').text,/没有必然关系.*大致区间对应/);
  assert.equal(claim('106','historical-average-support-233-not-annotation-144').ambiguity_status,'text_233_vs_unverified_144_annotation');
  assert.equal(claim('106','nine-class-stock-examples-and-index-four').ambiguity_status,'text_class7_vs_figure_class6_for_600578');
  assert.match(claim('106','nine-class-stock-examples-and-index-four').text,/600578\/600607第7/);
  checks.push('均线与严格级别不定式换算，正文233和600578第7类不依未知图注144/第6类擅改');
  const six=claim('106','six-basic-bars-five-day-touch-author-wording');
  assert.deepEqual(six.evidence.map(x=>x.pdf_page).sort((a,b)=>a-b),[401,402]);
  assert.ok(six.evidence.every(x=>x.published_at==='2008-07-10'));
  assert.equal(six.ambiguity_status,'six_bar_minimum_vs_l081_joint_rule_scope');
  assert.equal(claim('106','aug14-six-bars-fourth-confirm-fifth-turn').ambiguity_status,six.ambiguity_status);
  assert.match(graph.getClaim('lower-l081-c-stage-new-stroke-two-joint-conditions').text,/至少有3根K线/);
  assert.match(claim('106','aug14-boundary-hold-not-best-buy-point').text,/不是最佳买点.*只是是否延伸为笔.*买点须从走势类型/);
  assert.match(claim('106','aug14-multilevel-fractal-nesting-not-single-edge').text,/不等单纯上下边沿/);
  checks.push('六根原话/去包含示例与81两联合条件并列，未改81；8/14明文边沿仅观察成笔，非最佳买点或完整区间套');
  assert.match(claim('106','jul14-t1-limits-precise-small-level-operation').text,/T\+1确实限制.*最精确操作/);
  const plan=JSON.parse(readFileSync(resolve(agent,'curation/source-audit/stage-c-l106-source-plan.json'),'utf8'));
  const sourceOps=plan.operations.filter(x=>x.table==='passages');assert.equal(sourceOps.length,23);
  for(const op of sourceOps){const p=graph.db.prepare('SELECT * FROM passages WHERE id=?').get(op.id);
    for(const [key,value] of Object.entries(op.after))assert.equal(p[key],value,op.id+':'+key);
    assert.equal(createHash('sha256').update(p.text).digest('hex'),op.text_sha256);
  }
  const date=(short)=>graph.db.prepare('SELECT published_at FROM passages WHERE id=?').get('volume_2-5332cd1b6038-p'+short).published_at;
  assert.equal(date('0406-b003'),'2008-07-14 06:40:48');assert.equal(date('0406-b004'),'2008-07-16 06:12:17');
  assert.equal(date('0406-b005'),'2008-07-16 06:12:17');assert.equal(date('0407-b002'),'2008-07-21 15:37:35');
  assert.equal(date('0408-b000'),'2008-08-03 08:25:09');assert.equal(date('0408-b001'),'2008-08-04 15:26:00');
  assert.equal(date('0409-b009'),'2008-08-08 15:20:58');assert.equal(date('0409-b012'),'2008-08-08 15:20:58');
  assert.equal(date('0413-b006-s01'),'2008-08-13 08:28:09');assert.equal(date('0414-b001'),'2008-08-13 08:28:09');
  assert.equal(date('0415-b001'),'2008-08-15 15:27:47');
  checks.push('T+1明确限制理论化小级精确操作；23日期逐项匹配，2/28被引文章和14:21被引标题不作新解盘头，7/10不补时分秒');
  assert.match(claim('106','aug6-first-leg-ended-2762-conditional-day-stroke').text,/至少第一段.*2762未有效站.*第二段下跌/);
  assert.match(claim('106','aug11-am-major-center-break-needs-complete-retest').text,/次级别类型完成后.*次级别反弹不能回/);
  assert.match(claim('106','aug12-direct-third-buy-no-c-still-down').text,/a、c可不出现.*中枢数量/);
  assert.ok(claim('106','aug12-direct-third-buy-no-c-still-down').conditions[0].includes('A、B'));
  assert.match(claim('106','aug13-pm-second-rebound-means-forming-b').text,/第二个.*构成2924下来第二中枢/);
  const cross=claim('106','jul11-inclusion-exception-five-day-two-paths');
  assert.deepEqual(cross.evidence.map(x=>x.pdf_page).sort((a,b)=>a-b),[404,405]);
  checks.push('第一段终结非整体完成，大中枢三卖须次级下跌完后反抽不回；A/B合法而a/c可缺，8/13第二反弹明指构造2924第二中枢');
  assert.match(claim('106','aug12-prediction-as-leveled-boundary-classification').text,/各种级别边界条件的完全分类/);
  assert.equal(claim('106','aug8-fourth-test-ninety-five-author-estimate').ambiguity_status,'author_probability_not_independently_verified');
  assert.equal(claim('106','aug12-direct-third-buy-at-most-ten-estimate').ambiguity_status,'probability_conditioning_and_sample_not_supplied');
  assert.match(claim('106','aug12-direct-third-buy-at-most-ten-estimate').review_note,/不自行相加推得常规支80%/);
  assert.match(claim('106','aug18-sublevel-rebound-third-sell-risk').text,/可能只成原大中枢三卖.*最好也只构更大中枢/);
  checks.push('预测在该段专指分级边界分类，不抹除旧方向预测非100%；95/两个10/90非实测且不能自加，次级反弹仍有三卖风险');
  const figures=graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_2-5332cd1b6038' AND pdf_page BETWEEN 402 AND 415").all();
  assert.equal(figures.length,10);assert.ok(figures.every(x=>x.origin_status==='later_annotation'));
  assert.equal(graph.metadata.semantic_completion,false);
  checks.push('10本课图全部文后行情，401邻课图未重算；全书语义与Windows成品目标仍未完成');
  const requests=[
    ['search',{query:'均线分类'},['search','均线分类']],
    ['concept',{id:'缠中说禅板块强弱指标',limit:100},['concept','缠中说禅板块强弱指标','--limit','100']],
    ['concept',{id:'均线系统',limit:100},['concept','均线系统','--limit','100']],
    ['neighbors',{id:'均线分类',depth:1,limit:100},['neighbors','均线分类','--depth','1','--limit','100']],
    ['evidence',{id:cross.evidence.find(e=>e.pdf_page===405).id},['evidence',cross.evidence.find(e=>e.pdf_page===405).id]],
    ['page',{documentId:'volume_2.pdf',page:404},['page','--document-id','volume_2.pdf','--page','404']],
    ['search',{query:'6根K线',scope:'source'},['search','6根K线','--scope','source']],
    ['coverage',{},['coverage']],
  ];
  const parity=[];
  for(const [command,args,argv] of requests){
    const a=JSON.parse(JSON.stringify(graph.query(command,args)));
    assert.deepEqual(JSON.parse(JSON.stringify(desktop.query(command,args))),a);
    const cli=spawnSync(process.execPath,[resolve(agent,'bin/chan-kg.mjs'),...argv,'--kb',root],{encoding:'utf8',maxBuffer:24*1024*1024});
    assert.equal(cli.status,0,cli.stderr);assert.deepEqual(JSON.parse(cli.stdout),a);
    parity.push({command,args,cli_matches_shared:true,desktop_module_matches_shared:true});
  }
  assert.deepEqual({database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
  const report={graph_version:graph.metadata.graph_version,schema_version:graph.metadata.schema_version,checks,parity,
    core_sha256:sha(resolve(agent,'src/core.mjs')),desktop_core_sha256:sha(resolve(agent,'../chan-kg-desktop/vendor/core.mjs')),
    database_and_manifest_unchanged:true,pass:true,
    limits:['模块与CLI检查不是Windows成品离线、PDF高亮或实际界面验收。','同模型开发场景，不证明全书歧义已解决、均线分类阈值/最强设问已有唯一算法、板块指标经收益回测、六K与81已统一或95/10/90比例已实测。']};
  writeFileSync(resolve(agent,'curation/source-audit/stage-c-l106-verification.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report));
} finally {graph.close();desktop.close();}
