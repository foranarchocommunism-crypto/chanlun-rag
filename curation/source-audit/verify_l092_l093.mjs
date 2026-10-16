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
  assert.equal(graph.db.prepare("SELECT count(*) AS n FROM claims WHERE (id LIKE 'lower-l092-c-stage-%' OR id LIKE 'lower-l093-c-stage-%') AND review_status='reviewed'").get().n,60);
  const axis=claim('092','axis-and-secondary-midpoints');
  assert.match(axis.text,/中枢区间的一半位置.*Z.*次级震荡区间的一半位置.*Zn/);
  assert.equal(axis.ambiguity_status,'secondary_interval_sampling');
  assert.match(graph.getClaim('upper-l020-z-segment-definition').text,/Z走势段/);
  assert.match(graph.getClaim('lower-l088-c-stage-level-mark-notation').text,/Zn/);
  checks.push('60条新增默认命题；92的Zn中点与20的Z走势段、88的周线编号分开');
  const cross=claim('092','boundary-cross-not-sufficient');
  assert.match(cross.text,/不意味着一定出现第三类.*可能多次/);
  assert.match(claim('092','eventual-boundary-cross-author-necessity').text,/最终肯定超越/);
  assert.ok(claim('092','no-third-point-extension-probabilistic').exceptions.some(x=>x.includes('没有100%')));
  assert.ok(claim('092','smooth-midpoint-only-rough-estimate').exceptions.includes('特殊情况'));
  checks.push('最终必要关系与任次越界非充分分开；扩展经验非100%，预计高低仅大致且有特殊情况');
  const trend=claim('092','secondary-trend-last-center-condition');
  assert.equal(trend.conditions.length,3);assert.equal(trend.ambiguity_status,'zn_corresponding_cooperation');
  assert.match(claim('092','nine-observations-not-any-nine-bars').review_note,/非任意九根K线/);
  checks.push('次级趋势、Zn配合及前后中枢联合条件保留；九点不能换成任意九根K线');
  assert.match(claim('092','dec28-five-up-or-consolidation-open').text,/仍待判断.*300尚未完成/);
  assert.match(claim('092','jan3-neckline-no-third-not-certain').text,/尚无三买.*不能说.*100%/);
  assert.ok(claim('092','jan8-second-consolidation-branch').exceptions.some(x=>x.includes('突破爆发')));
  assert.match(claim('092','jan8-strong-exception-and-first-denied').text,/已否定第一支/);
  checks.push('300未完和缺三买突破未100%保留；1/8第二支仍可爆发、第一支当日已否');
  assert.match(claim('093','zero-state-two-outcomes').text,/均可能连接.*不能唯一确定/);
  const cost=claim('093','conservative-withdraw-cost-leave-profit');
  assert.equal(cost.conditions.length,3);assert.ok(cost.conditions.some(x=>x.includes('足够获利空间')));
  assert.ok(claim('093','skilled-sell-first-no-rebuy-down-state').exceptions.some(x=>x.includes('不回补')));
  assert.match(claim('093','remaining-exit-five-week-alternative').review_note,/另一选择/);
  checks.push('零态两向保留；先取本需已有利润与能力条件，短差先卖后买遇下延不回补，均线为替代');
  assert.match(claim('093','weekly-state-corresponding-small-uptrend').text,/级别可为1、5或30分钟.*具体图形/);
  assert.ok(claim('093','confirmed-divergence-last-center-reference').conditions[0].includes('完全确认结束'));
  assert.equal(claim('093','confirmed-divergence-last-center-reference').ambiguity_status,'second_situation_not_explicitly_numbered');
  const source=graph.db.prepare("SELECT text FROM passages WHERE id='volume_2-5332cd1b6038-p0302-b013'").get().text;
  assert.ok(source.includes('以（1，0）为例子'));assert.ok(source.includes('（-1，0）这个信号'));
  checks.push('周K与走势级别不固定；最后中枢比较需背驰完全确认，未补第二情形或改不一致符号');
  assert.match(claim('093','jan18-not-must-reach-5675').text,/明确否定.*必须先到5675.*5522/);
  assert.match(claim('093','jan17-upstroke-not-segment-destroyed').text,/只构成笔.*没有破坏/);
  assert.equal(claim('093','jan17-single-segment-divergence-scope').ambiguity_status,'analog_divergence_observation_scope');
  assert.match(claim('093','jan21-third-sell-formed-downtrend-not-certain').text,/三卖已制造.*机会不小/);
  checks.push('区间上界非必经点；笔反弹不等于段破坏，类背驰观察范围待核，三卖已出不等于完整下跌必成');
  const figures=graph.db.prepare("SELECT id,origin_status FROM figures WHERE document_id='volume_2-5332cd1b6038' AND pdf_page BETWEEN 290 AND 310").all();
  assert.equal(figures.length,12);assert.equal(figures.filter(x=>x.origin_status==='later_annotation').length,8);
  assert.equal(figures.filter(x=>x.origin_status==='unverified').length,4);
  assert.equal(figures.find(x=>x.id.endsWith('p0303-fig1')).origin_status,'later_annotation');
  assert.ok(claim('093','jan19-channel-four-supports-conditional').evidence.flatMap(e=>e.figures).every(f=>f.origin_status==='later_annotation'));
  assert.equal(graph.metadata.semantic_completion,false);
  checks.push('八后加图与四未核图分开；第三方吻图无作者命题唯一支撑，未来四支点不倒填当日完成');
  const requests=[
    ['search',{query:'Zn超越A或B'},['search','Zn超越A或B']],
    ['concept',{id:'中枢震荡监视器',limit:100},['concept','中枢震荡监视器','--limit','100']],
    ['concept',{id:'震荡中轴',limit:100},['concept','震荡中轴','--limit','100']],
    ['neighbors',{id:'中枢震荡监视器',depth:1,limit:100},['neighbors','中枢震荡监视器','--depth','1','--limit','100']],
    ['evidence',{id:cross.evidence[0].id},['evidence',cross.evidence[0].id]],
    ['page',{documentId:'volume_2.pdf',page:302},['page','--document-id','volume_2.pdf','--page','302']],
    ['search',{query:'以（1，0）为例子',scope:'source'},['search','以（1，0）为例子','--scope','source']],
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
    limits:['模块与CLI检查不是Windows成品离线、PDF高亮或实际界面验收。','同模型开发场景，未证明Zn实时取样、九点升级及均线有效跌破统一算法，也未证明预测/利润断言。']};
  writeFileSync(resolve(agent,'curation/source-audit/stage-c-l092-l093-verification.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report));
} finally {graph.close();desktop.close();}
