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
  assert.equal(graph.db.prepare("SELECT count(*) AS n FROM claims WHERE id GLOB 'lower-l09[456]-c-stage-*' AND review_status='reviewed'").get().n,48);
  const prepare=claim('094','prepare-channel-capital-exit-before-entry');
  assert.equal(prepare.evidence.length,2);assert.deepEqual(prepare.evidence.map(e=>e.pdf_page).sort((a,b)=>a-b),[311,312]);
  assert.match(prepare.text,/通道、资金.*预先设置退出/);
  assert.match(claim('094','opportunity-may-be-skipped').text,/选择参与或放弃/);
  checks.push('48新增默认命题；跨页准备句保留，选择机会可放弃且先设退出');
  assert.match(claim('094','t1-same-day-exit-impossible-risk').text,/当天即完成.*可能无法卖出/);
  assert.ok(claim('094','beginner-fractal-and-ma-exit').conditions.some(x=>x.includes('分型后有效跌破')));
  assert.equal(claim('094','reentry-with-good-medium-trend-and-prior-sale').conditions.length,3);
  checks.push('T+1同日退出限制、中线/先卖/20%回补联合条件及初心者均线退出保留');
  assert.ok(claim('094','jan22-second-center-expected-exception').exceptions.some(x=>x.includes('重回5100')));
  assert.match(claim('095','jan23-second-center-formed-best-third-buy').text,/第二1分钟中枢已形成/);
  assert.match(claim('095','jan23-five-center-two-routes').text,/九次级震荡.*先1分钟三卖后底背驰/);
  checks.push('1/22预期含例外、1/23已成及两条扩展路线分开，九次级非任意九K');
  assert.match(claim('095','zero-investment-author-position-and-history').text,/自述.*归还本金/);
  assert.match(claim('096','zero-cost-explicitly-relaxed-life-safe-money').text,/明确说.*不必那么严格.*不影响生活/);
  const retry=claim('096','second-chance-after-full-failure-review');assert.equal(retry.conditions.length,3);
  assert.match(claim('096','after-exit-years-learning-conditional-return').text,/多年学习历练/);
  checks.push('0投入有作者明确放宽，借钱先还本仅自述；再试需复盘，后续多年学习路径不删除');
  assert.match(claim('094','jan22-unskilled-wait-bottom-confirmed').text,/没有相应技术.*确认才介入/);
  const early=claim('096','jan25-before-fractal-confirm-skill-context');
  assert.equal(early.ambiguity_status,'preconfirmation_vs_conservative_skill_scope');assert.ok(early.conditions.some(x=>x.includes('相应操作能力')));
  assert.match(claim('096','jan24-bottom-formed-stroke-not-confirmed').text,/是否延伸成笔.*仍待观察/);
  checks.push('无技术等底确认与熟练者具体提前操作并列，底形成不等于笔已确认');
  const answer=claim('096','jan24-question-jan25-third-unfinished');assert.match(answer.text,/第三段尚未完成/);
  assert.deepEqual(answer.evidence.map(e=>e.pdf_page).sort((a,b)=>a-b),[317,319]);
  assert.match(claim('096','jan24-1340-not-minute-third-buy').text,/否定.*13:40.*1分钟三买/);
  assert.match(claim('096','macd-assists-not-equals-divergence').text,/辅助.*不能以为MACD就等于背驰/);
  checks.push('跨日问答第三段未完、13:40非1分钟三买及MACD非背驰充分条件可取证');
  assert.match(claim('096','jan25-put-warrant-study-not-general-entry').text,/认沽/);
  assert.ok(!claim('096','jan25-put-warrant-study-not-general-entry').concept_ids.includes(graph.db.prepare("SELECT id FROM concepts WHERE label='认购权证'").get().id));
  const warrant=claim('096','jan28-put-entry-warning-and-exception');assert.match(warrant.text,/一般人不可介入/);assert.ok(warrant.exceptions[0].includes('已买入且'));
  assert.match(claim('096','jan28-three-step-opportunity-recognition-operation').text,/不预测点位时间.*成立确认.*最坏情况/);
  checks.push('认沽不归认购，教学/禁追与已持有高手例外保留；机会输出识别执行三步不同');
  const figures=graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_2-5332cd1b6038' AND pdf_page BETWEEN 311 AND 323").all();
  assert.equal(figures.length,5);assert.equal(figures.filter(x=>x.origin_status==='later_annotation').length,3);assert.equal(figures.filter(x=>x.origin_status==='unverified').length,2);
  assert.equal(claim('096','jan28-sixty-minute-chart-return-author-claim').ambiguity_status,'figure_2_029_vs_text_2_3');
  assert.equal(graph.metadata.semantic_completion,false);
  checks.push('三后期图两未核图与310邻图分开，2.3/2.029差异不自动改文，整体语义仍未完成');
  const requests=[
    ['search',{query:'赌徒心理'},['search','赌徒心理']],
    ['concept',{id:'当机立断',limit:100},['concept','当机立断','--limit','100']],
    ['concept',{id:'赌徒心理',limit:100},['concept','赌徒心理','--limit','100']],
    ['neighbors',{id:'当机立断',depth:1,limit:100},['neighbors','当机立断','--depth','1','--limit','100']],
    ['evidence',{id:prepare.evidence[1].id},['evidence',prepare.evidence[1].id]],
    ['page',{documentId:'volume_2.pdf',page:317},['page','--document-id','volume_2.pdf','--page','317']],
    ['search',{query:'第三段还没完成',scope:'source'},['search','第三段还没完成','--scope','source']],
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
    limits:['模块与CLI检查不是Windows成品离线、PDF高亮或实际界面验收。','同模型开发场景，未证明机会无遗漏/一一对应、资本/收益保证或提前分型操作的实时算法。']};
  writeFileSync(resolve(agent,'curation/source-audit/stage-c-l094-l096-verification.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report));
} finally {graph.close();desktop.close();}
