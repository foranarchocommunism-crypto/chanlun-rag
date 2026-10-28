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
const id=slug=>`lower-l088-c-stage-${slug}`;
const claim=slug=>{const r=graph.getClaim(id(slug));assert.ok(r);return r;};
const checks=[];
try {
  const definition=claim('intermediate-stage-definition');
  assert.ok(definition.conditions.includes('新的走势类型尚未确立'));
  assert.match(definition.conditions.join(' '),/背驰或盘整背驰/);
  assert.match(definition.text,/中阴身阶段.*中阴阶段/);
  assert.equal(graph.db.prepare("SELECT count(*) AS n FROM claims WHERE id LIKE 'lower-l088-c-stage-%' AND review_status='reviewed'").get().n,36);
  checks.push('36条默认知识，中阴定义保留背驰/盘整背驰与新类型尚未确立的两端');
  assert.match(claim('stage-shape-not-new-type').conditions.join(' '),/只从截取.*形态/);
  assert.match(claim('stage-shape-not-new-type').text,/不表示新的走势类型一定是盘整/);
  assert.match(claim('stage-end-can-same-direction').text,/不一定反向.*上涨\+盘整\+上涨/);
  checks.push('截取盘整不冒充完整新类型，结束可同向延续或反向');
  const boundary=claim('195-boundary-class-line');
  assert.equal(boundary.ambiguity_status,'case_class_line_vs_formal_type');
  assert.match(boundary.text,/至少为线段类下跌.*在该线段层次/);
  assert.match(claim('old-structure-persists-higher').text,/191之前.*1分钟、5分钟/);
  assert.match(graph.getClaim('lower-l064-sublevel-as-segment-metaphor').text,/严格意义上线段只存在于最低级别之下/);
  checks.push('195为案例类线段分界，旧结构在大级别仍有用，严格最低级别边界保留');
  assert.ok(claim('compress-marks-after-completion').conditions.includes('新1分钟走势结束后才增加对应标号'));
  assert.match(claim('level-mark-notation').text,/Xn.*Yn.*Wn.*Sn.*Rn、Zn、Mn、Jn、Nn/);
  assert.match(claim('same-endpoint-multiple-marks').text,/可能同时有某Yn/);
  assert.equal(claim('all-levels-intermediate').ambiguity_status,'stage_length_not_time_formula');
  checks.push('分级标号增记依完成而非固定时长，Yn只可能有，级别长度无自行换算');
  assert.match(claim('nov12-return-last-oscillation-region').text,/最后1分钟中枢的波动区间/);
  assert.match(claim('nov12-return-last-oscillation-region').review_note,/不静默缩为中枢自身价格区间/);
  assert.match(claim('nov12-195-to-214-level-gate').conditions.join(' '),/可以接受1分钟级别/);
  assert.match(claim('nov12-195-to-214-level-gate').exceptions.join(' '),/5分钟以上/);
  assert.equal(claim('nov12-214-three-nesting').ambiguity_status,'internal_stroke_nesting_not_reconstructed');
  checks.push('回抽波动区间与中枢区间有别，214回补需1分钟操作级别，内部笔未重算状态可见');
  assert.match(claim('retest-need-not-touch-neckline').text,/不一定碰到5462/);
  assert.match(claim('nov14-regain-versus-hold-5462').text,/无论能否站住.*站住则有/);
  assert.match(claim('nov14-daily-stroke-end-hold').text,/10000只是其假设/);
  assert.match(claim('nov8-thousand-not-maximum').text,/未说超过1000点就没有/);
  checks.push('反抽不必触颈线，重回/站稳分开，1000及10000不变最大跌幅或预测目标');
  assert.match(claim('nov7-monthly-top-case').text,/月顶分型.*5月均线/);
  assert.match(claim('nov13-daily-bottom-five-day').text,/日底分型.*5日线/);
  assert.match(claim('nov9-petro-close-centers-not-certain').text,/极可能.*实际走势决定/);
  checks.push('月顶与5月线、日底与5日线分层；中石油两中枢扩展仍是概率预期');
  const fs=graph.db.prepare("SELECT origin_status,count(*) AS n FROM figures WHERE id IN ('volume_2-5332cd1b6038-p0240-fig1','volume_2-5332cd1b6038-p0245-fig1','volume_2-5332cd1b6038-p0246-fig1','volume_2-5332cd1b6038-p0248-fig1') GROUP BY origin_status").all();
  assert.equal(fs.find(f=>f.origin_status==='later_annotation').n,2);assert.equal(fs.find(f=>f.origin_status==='unverified').n,2);
  assert.ok(claim('retest-need-not-touch-neckline').evidence.flatMap(e=>e.figures).every(f=>f.origin_status==='later_annotation'));
  assert.equal(graph.metadata.semantic_completion,false);
  checks.push('两图后期与两图来源未核分开，后期图不充原发时证言，全书未完成');
  const requests=[
    ['search',{query:'中阴'},['search','中阴']],
    ['search',{query:'中阴身'},['search','中阴身']],
    ['concept',{id:'中阴阶段',limit:100},['concept','中阴阶段','--limit','100']],
    ['neighbors',{id:'中阴阶段',depth:1,limit:100},['neighbors','中阴阶段','--depth','1','--limit','100']],
    ['evidence',{id:definition.evidence[0].id},['evidence',definition.evidence[0].id]],
    ['page',{documentId:'volume_2.pdf',page:240},['page','--document-id','volume_2.pdf','--page','240']],
    ['search',{query:'这是只从截取这一阶段的形态说',scope:'source'},['search','这是只从截取这一阶段的形态说','--scope','source']],
    ['coverage',{},['coverage']],
  ];
  const parity=[];
  for(const [command,args,argv] of requests){
    const a=JSON.parse(JSON.stringify(graph.query(command,args)));
    assert.deepEqual(JSON.parse(JSON.stringify(desktop.query(command,args))),a);
    const cli=spawnSync(process.execPath,[resolve(agent,'bin/chan-kg.mjs'),...argv,'--kb',root],{encoding:'utf8',maxBuffer:24*1024*1024});
    assert.equal(cli.status,0,cli.stderr);assert.deepEqual(JSON.parse(cli.stdout),a);
    if(command==='search'&&args.query==='中阴身')assert.ok(a.data.results.some(r=>r.id===definition.id));
    if(command==='search'&&args.scope==='source')assert.ok(a.data.results.some(r=>r.id.endsWith('p0241-b005')));
    parity.push({command,args,cli_matches_shared:true,desktop_module_matches_shared:true});
  }
  assert.equal(graph.query('neighbors',{id:'中阴阶段',limit:100}).data.edges.filter(e=>e.review_status==='reviewed').length,6);
  assert.deepEqual({database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
  const report={graph_version:graph.metadata.graph_version,schema_version:graph.metadata.schema_version,checks,parity,
    core_sha256:sha(resolve(agent,'src/core.mjs')),desktop_core_sha256:sha(resolve(agent,'../chan-kg-desktop/vendor/core.mjs')),
    database_and_manifest_unchanged:true,pass:true,
    limits:['共享/CLI/桌面vendor模块检查，不是Electron界面、成品离线或PDF交互验收。','同模型开发场景，未独立重算214的内部笔，也非人工金标准。']};
  writeFileSync(resolve(agent,'curation/source-audit/stage-c-l088-verification.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report));
} finally {graph.close();desktop.close();}
