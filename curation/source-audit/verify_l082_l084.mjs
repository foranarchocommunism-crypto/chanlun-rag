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
const claim=(lesson,slug)=>{const r=graph.getClaim(id(lesson,slug));assert.ok(r);return r;};
const page=n=>graph.query('page',{documentId:'volume_2.pdf',page:n}).data;
const checks=[];
try {
  const p209=page(209),p212=page(212);
  assert.equal(p209.passages.find(x=>x.id.endsWith('-b004')).role,'author_commentary');
  assert.equal(p209.passages.find(x=>x.id.endsWith('-b005')).role,'unknown');
  assert.equal(p212.passages.find(x=>x.id.endsWith('-b004')).role,'unknown');
  assert.equal(p212.passages.find(x=>x.id.endsWith('-b005')).role,'author_commentary');
  const reprint=page(211).passages;
  assert.ok(reprint.length===14&&reprint.every(x=>x.role==='unknown'&&x.speaker.includes('转载文')));
  const source=graph.query('search',{query:'上市公司市值已经是GDP',scope:'source'}).data.results;
  assert.ok(source.some(x=>x.role==='unknown'&&x.id.endsWith('p0210-b008')));
  assert.equal(graph.db.prepare("SELECT review_status FROM claims WHERE id='candidate-30a010d0e34c69dc'").get().review_status,'rejected');
  checks.push('39段转载与作者引言、下一篇边界隔离；GDP引述保留第三方身份，原错误候选已拒绝');
  const fractal=graph.query('concept',{id:'分型',limit:1}).data.concept;
  const other=graph.query('concept',{id:'分形',limit:1}).data.concept;
  assert.notEqual(fractal.id,other.id);
  assert.notEqual(graph.query('concept',{id:'自相似性',limit:1}).data.concept.id,graph.query('concept',{id:'自同构性结构',limit:1}).data.concept.id);
  assert.match(claim('084','explicit-self-structure-rename').text,/不够精确.*统一称/);
  assert.notEqual(graph.query('concept',{id:'圆顶',limit:1}).data.concept.id,graph.query('concept',{id:'圆底',limit:1}).data.concept.id);
  checks.push('分型/分形、圆顶/圆底不同概念；作者明确改称可查，不把数学近词无条件合并');
  const third=claim('082','third-sell-no-expansion-stroke');
  assert.ok(third.conditions.includes('出现第三类卖点'));
  assert.ok(third.conditions.includes('该卖点不形成中枢扩张'));
  assert.match(claim('082','no-stroke-break-top-needs-third-buy').review_note,/必要条件.*不是.*充分/);
  assert.match(claim('082','sell-then-check-replenishment').text,/确认为中继.*回补.*否则/);
  checks.push('三卖不扩张联合条件、破顶所需三买的必要性及中继确认后回补保留');
  assert.match(claim('083','stroke-center-possible-less-stable').text,/可以设计.*稳定性很差/);
  assert.match(claim('083','domino-prior-extreme-range').conditions.join(' '),/第二类.*骨牌/);
  assert.equal(claim('082','third-break-first-low-half').ambiguity_status,'source_inclusion_scope_wording');
  assert.ok(claim('082','third-break-first-low-half').evidence.some(e=>e.quote.includes('非包含关系处理后')));
  assert.equal(claim('082','choose-largest-local-center-example').ambiguity_status,'cross_lesson_time_level_scope');
  checks.push('笔构中枢是可能但作者认为较不稳；骨牌条件及非包含/时间级别原文歧义不被隐藏');
  const entry=claim('084','fractal-only-recursion-start-optional');
  assert.ok(entry.conditions.includes('替代递归入口仍能保证分解唯一性'));
  assert.match(claim('084','two-recursion-functions').text,/f1与f2可以完全不同/);
  assert.match(claim('084','base-and-higher-use-different-rules').text,/最低级别.*其上级别/);
  assert.match(claim('084','no-absolute-time-guarantee').text,/不对任何时间结构作绝对承诺/);
  checks.push('递归入口可替代但须唯一，f1/f2分层与级别不由时长保证可查');
  const unconfirmed=claim('084','oct8-139-not-confirmed');
  assert.match(unconfirmed.text,/尚未确认.*跌破5685/);
  assert.ok(unconfirmed.evidence.flatMap(e=>e.figures).every(f=>f.origin_status==='later_annotation'));
  assert.match(claim('084','oct18-top-not-confirmed').text,/没走完.*未破位/);
  const u84=graph.query('coverage',{}).data.units.find(x=>x.id==='lesson-084');
  const note=typeof u84.note==='string'?JSON.parse(u84.note):u84.note;
  assert.equal(note.source_role_review.third_party_reprint_passages_excluded,39);
  assert.equal(graph.metadata.semantic_completion,false);
  checks.push('后期140/141图不倒填139已完，顶部自评不抹去未确认条件；转载及全书未完成状态可见');
  const requests=[
    ['search',{query:'中枢'},['search','中枢']],
    ['search',{query:'自同构性结构'},['search','自同构性结构']],
    ['concept',{id:'递归定义',limit:100},['concept','递归定义','--limit','100']],
    ['neighbors',{id:'分型',depth:1,limit:100},['neighbors','分型','--depth','1','--limit','100']],
    ['evidence',{id:third.evidence[0].id},['evidence',third.evidence[0].id]],
    ['page',{documentId:'volume_2.pdf',page:211},['page','--document-id','volume_2.pdf','--page','211']],
    ['search',{query:'上市公司市值已经是GDP',scope:'source'},['search','上市公司市值已经是GDP','--scope','source']],
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
  const edges=graph.query('neighbors',{id:'周期K线图',limit:200}).data.edges;
  const edge=edges.find(x=>x.claim_ids.includes(id('084','level-not-time-classification')));
  assert.ok(edge);assert.equal(edge.type,'distinguishes');
  assert.deepEqual({database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
  const report={graph_version:graph.metadata.graph_version,schema_version:graph.metadata.schema_version,checks,parity,
    core_sha256:sha(resolve(agent,'src/core.mjs')),desktop_core_sha256:sha(resolve(agent,'../chan-kg-desktop/vendor/core.mjs')),
    database_and_manifest_unchanged:true,pass:true,
    limits:['共享核心、桌面vendor和CLI的数据检查，不代替Electron界面或Windows打包离线验收。','同模型开发场景，非人工独立语义金标准。']};
  writeFileSync(resolve(agent,'curation/source-audit/stage-c-l082-l084-verification.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report));
} finally {graph.close();desktop.close();}
