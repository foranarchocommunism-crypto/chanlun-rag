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
const checks=[];
try {
  const equal=claim('075','absolute-and-measurement-equality');
  assert.ok(equal.evidence.some(x=>x.quote.includes('软件上最后一位小数都相等')));
  assert.ok(claim('075','equal-endpoint-inclusion').conditions.includes('相等指对应高点或对应低点'));
  const onePrice=claim('075','one-price-limit-two-constructions');
  assert.match(onePrice.text,/最小级别中枢.*分型.*更谈不上笔/);
  checks.push('包含的对应端点和绝对精度有作者证据；一字涨停两种构造入口未混合');
  assert.match(claim('076','third-return-force-necessary').text,/才可能/);
  assert.match(claim('076','third-return-force-necessary').review_note,/必要条件.*不是.*充分/);
  assert.match(claim('075','unfinished-not-compare-completed').text,/尚未走完.*已走完/);
  checks.push('第三类点力度只作必要条件；未完成段不冒充已完成比较');
  const gap=claim('077','gap-fill-entire-interval-no-deadline');
  assert.match(gap.text,/全部再次出现成交.*永远/);
  assert.match(claim('077','exhaustion-higher-adjustment').conditions.join(' '),/原趋势.*回补后/);
  assert.match(claim('077','period-not-trend-level').text,/不能直接按.*周期/);
  checks.push('补缺为全区间且无强制期限；调整走势级别与图周期分开');
  const oldStroke=claim('077','old-stroke-joint-conditions');
  const newStroke=claim('081','new-stroke-two-joint-conditions');
  assert.ok(oldStroke.conditions.includes('顶底之间至少一根独立K线'));
  assert.ok(newStroke.evidence.some(x=>x.quote.includes('不考虑包含关系，至少有3根')));
  assert.notEqual(oldStroke.id,newStroke.id);
  const proof=claim('077','stroke-uniqueness-author-assertion');
  assert.equal(proof.ambiguity_status,'source_proof_branch_overlap');
  assert.ok(proof.evidence.some(x=>x.quote.startsWith('如果前面的底不低于后面的底')));
  checks.push('旧笔和后课新笔同时保留；原文不低于及证明分支歧义可返回');
  const classified=claim('076','classify-before-second-sequence');
  assert.match(classified.text,/第一种不需.*第二种若找不到/);
  assert.match(claim('077','second-case-abc-provisional').text,/假设称呼/);
  assert.match(claim('077','first-case-no-overlap-no-completion').text,/无重合.*不能构成/);
  checks.push('第一二种情况先分类；A/B/C确认前为假设，不因单笔破坏确认分段');
  const combined=claim('077','81-82-rebound-segment-actual-branch');
  const annotated=combined.evidence.flatMap(x=>x.figures).find(x=>x.id.endsWith('p0141-fig1'));
  assert.equal(annotated.origin_status,'later_annotation');
  assert.match(annotated.note,/2007-09-18.*2007-09-05/);
  assert.match(combined.review_note,/新笔蓝字不作为/);
  checks.push('81—82正文组合关系可查；蓝字新笔后加状态与原文证据分别返回');
  const coverage=graph.query('coverage',{}).data;
  const u67=coverage.units.find(x=>x.id==='lesson-067');
  const note=typeof u67.note==='string'?JSON.parse(u67.note):u67.note;
  assert.ok(note.pending.some(x=>(x.id??x)==='lower-l067-equality-boundary-detail'));
  assert.equal(note.partial_resolutions[0].status,'partially_resolved');
  assert.ok(note.partial_resolutions[0].remaining.length);
  assert.equal(coverage.semantic_completion,false);
  const page=graph.query('page',{documentId:'volume_2.pdf',page:137}).data;
  assert.equal(page.passages.find(x=>x.id.endsWith('-b007')).role,'reader');
  assert.equal(page.passages.find(x=>x.id.endsWith('-b008')).role,'author_reply');
  assert.equal(page.passages.find(x=>x.id.endsWith('-b009')).unit_id,'lesson-077');
  checks.push('67课仅部分解除等值疑问；读者/作者回复/下一课边界与全书未完成状态保持');
  const requests=[
    ['search',{query:'相等',limit:100},['search','相等','--limit','100']],
    ['search',{query:'中枢'},['search','中枢']],
    ['concept',{id:'笔',limit:100},['concept','笔','--limit','100']],
    ['neighbors',{id:'线段',depth:1,limit:100},['neighbors','线段','--depth','1','--limit','100']],
    ['evidence',{id:proof.evidence.find(x=>x.quote.startsWith('如果前面的底不低于')).id},['evidence',proof.evidence.find(x=>x.quote.startsWith('如果前面的底不低于')).id]],
    ['page',{documentId:'volume_2.pdf',page:141},['page','--document-id','volume_2.pdf','--page','141']],
    ['search',{query:'不低于后面的底',scope:'source'},['search','不低于后面的底','--scope','source']],
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
  const edge=graph.query('neighbors',{id:'线段',limit:200}).data.edges.find(x=>x.claim_ids.includes(id('077','first-three-strokes-overlap')));
  assert.ok(edge);
  assert.deepEqual({database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
  const report={graph_version:graph.metadata.graph_version,schema_version:graph.metadata.schema_version,checks,parity,
    core_sha256:sha(resolve(agent,'src/core.mjs')),desktop_core_sha256:sha(resolve(agent,'../chan-kg-desktop/vendor/core.mjs')),
    database_and_manifest_unchanged:true,pass:true,
    limits:['验证共享模块、桌面vendor及CLI；未执行Electron界面或打包离线交互。','同模型开发验收，不宣称独立或人工语义金标准。']};
  writeFileSync(resolve(agent,'curation/source-audit/stage-c-l075-l077-verification.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report));
} finally {graph.close();desktop.close();}
