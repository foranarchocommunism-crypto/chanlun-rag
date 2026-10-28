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
  const own=graph.db.prepare("SELECT * FROM claims WHERE id GLOB 'lower-l08[567]-c-stage-*'").all();
  assert.equal(own.length,51);assert.ok(own.every(c=>c.review_status==='reviewed'&&c.kind==='explicit'));
  assert.equal(page(221).passages.find(p=>p.id.endsWith('-b007')).unit_id,'lesson-085');
  assert.equal(page(224).passages.find(p=>p.id.endsWith('-b012')).unit_id,'lesson-086');
  assert.equal(page(233).passages.find(p=>p.id.endsWith('-b003')).unit_id,'lesson-087');
  assert.equal(page(239).passages.find(p=>p.id.endsWith('-b003')).unit_id,'lesson-088');
  checks.push('51条为已复核原文明说；85/86/87标题及相邻88课边界保留');
  assert.match(claim('086','third-sell-in-larger-upshift').conditions.join(' '),/大级别.*上移/);
  assert.match(claim('086','third-sell-in-larger-downshift').exceptions.join(' '),/卖空/);
  assert.match(claim('086','third-sell-in-larger-oscillation').text,/是否延伸出.*可能反而/);
  checks.push('小三卖的上移、下移及震荡三种大背景分开，卖空例外与可能大买点保留');
  assert.match(claim('086','big-buy-small-buy-nesting').text,/不一定最精确.*并非任意/);
  assert.match(claim('086','big-buy-small-buy-nesting').review_note,/第二次介入机会不等于正式第二类买点/);
  assert.match(claim('086','small-buy-break-large-structure-intact').conditions.join(' '),/大级别结构未被破坏/);
  assert.match(claim('086','big-buy-small-sell-intermediate').text,/两点间有大卖点.*若没有/);
  checks.push('区间套、结构不破及中间大卖点分支保留，第二次介入不冒充二买');
  const ambiguous=claim('086','inside-large-center-not-large-points');
  assert.equal(ambiguous.ambiguity_status,'small_level_significance_wording');
  assert.ok(ambiguous.evidence.some(e=>e.quote.includes('一般不具有小级别的操作意义')));
  assert.match(claim('086','next-level-points-two-paths').conditions.join(' '),/恰为次级别/);
  assert.match(claim('086','analogy-not-large-first-second').text,/并非大级别真正/);
  checks.push('小级别原字疑点可见，次级别操作意义与一二类点身份的比喻区别保留');
  const prospective=claim('086','oct30-new-center-required-uptrend');
  assert.match(prospective.conditions.join(' '),/不返回原中枢且.*形成新的同级中枢/);
  assert.match(claim('087','oct31-new-center-still-unformed').text,/当天仍未形成/);
  assert.match(claim('087','nov1-center-three-segments-case').text,/第二段.*第三段.*形成/);
  assert.ok(claim('086','oct30-third-buy-two-meanings').evidence.flatMap(e=>e.figures).every(f=>f.origin_status==='later_annotation'));
  checks.push('10/30条件预期、10/31未成、11/1已成逐日区分，后期图不倒填完成');
  assert.match(claim('087','nov2-late-sell-only-probability').text,/仍可能继续跌.*概率.*不能.*100%/);
  assert.match(claim('087','cost-zero-stories-stance').conditions.join(' '),/梦话/);
  assert.match(claim('087','cost-zero-stories-stance').review_note,/无账户或外部验证.*不由此认证零成本绝无风险/);
  const capacity=claim('085','oct23-capability-standard');
  assert.match(capacity.text,/空仓或者/);
  checks.push('晚卖后续跌仅概率，梦话成本与历史能力或条件不变成客观零风险证明');
  assert.match(claim('087','nov5-new-stock-first-down-segment').text,/第一下降线段结束.*分批.*不能保证T\+1/);
  assert.match(claim('087','nov5-petro-417-not-safe-floor').text,/不能保证.*跌穿41.7/);
  assert.match(claim('087','nov6-petro-class-third-not-strict').text,/类中枢.*类第三类卖点.*等待类背驰/);
  assert.match(claim('087','nov6-short-rebound-not-t1-profit').text,/未必.*T\+1获利/);
  checks.push('类三卖不升级严格中枢；首下降段结束仍非安全底，线段反弹不保证T+1利润');
  const buffer=claim('087','nov6-neckline-three-days-buffer');
  assert.equal(buffer.ambiguity_status,'case_buffer_not_universal_algorithm');
  assert.match(buffer.conditions.join(' '),/2007年11月6日5555/);
  assert.match(buffer.text,/至少看3天.*上下另有3%/);
  assert.equal(graph.metadata.semantic_completion,false);
  const figures=graph.db.prepare("SELECT origin_status,count(*) AS n FROM figures WHERE id IN ('volume_2-5332cd1b6038-p0223-fig1','volume_2-5332cd1b6038-p0228-fig1','volume_2-5332cd1b6038-p0232-fig1','volume_2-5332cd1b6038-p0236-fig1') GROUP BY origin_status").all();
  assert.equal(figures.find(f=>f.origin_status==='later_annotation').n,3);
  assert.equal(figures.find(f=>f.origin_status==='unverified').n,1);
  checks.push('3天/3%为当次经验而非统一算法；三图后期、一图制作人未核，全书未完成');
  const requests=[
    ['search',{query:'第三类卖点'},['search','第三类卖点']],
    ['search',{query:'T+1'},['search','T+1']],
    ['concept',{id:'颈线',limit:100},['concept','颈线','--limit','100']],
    ['neighbors',{id:'第三类卖点',depth:1,limit:100},['neighbors','第三类卖点','--depth','1','--limit','100']],
    ['evidence',{id:buffer.evidence[1].id},['evidence',buffer.evidence[1].id]],
    ['page',{documentId:'volume_2.pdf',page:226},['page','--document-id','volume_2.pdf','--page','226']],
    ['search',{query:'一般不具有小级别的操作意义',scope:'source'},['search','一般不具有小级别的操作意义','--scope','source']],
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
  const edges=graph.query('neighbors',{id:'类买卖点',limit:200}).data.edges;
  const analogy=edges.filter(e=>e.claim_ids.includes(id('086','analogy-not-large-first-second')));
  assert.equal(analogy.length,2);assert.ok(analogy.every(e=>e.type==='distinguishes'));
  assert.deepEqual({database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
  const report={graph_version:graph.metadata.graph_version,schema_version:graph.metadata.schema_version,checks,parity,
    core_sha256:sha(resolve(agent,'src/core.mjs')),desktop_core_sha256:sha(resolve(agent,'../chan-kg-desktop/vendor/core.mjs')),
    database_and_manifest_unchanged:true,pass:true,
    limits:['共享核心、桌面vendor和CLI的数据检查，不代替Electron界面或Windows打包离线验收。','同模型开发场景，非人工独立语义金标准。']};
  writeFileSync(resolve(agent,'curation/source-audit/stage-c-l085-l087-verification.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report));
} finally {graph.close();desktop.close();}
