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
const id=(lesson,slug)=>`upper-l${lesson}-c-stage-${slug}`;
const claim=(lesson,slug)=>{const r=graph.getClaim(id(lesson,slug));assert.ok(r);return r;};
const checks=[];
try{
  const coincidence=claim('021','second-third-coincidence-iff');
  assert.ok(coincidence.conditions.some(x=>x.includes('最后中枢')));
  assert.ok(coincidence.conditions.some(x=>x.includes('不触及')));
  assert.match(claim('021','second-third-coincidence-no-guaranteed-trend').text,/不在理论上排除/);
  assert.ok(claim('021','confirmed-uptrend-only-third-buy').conditions.includes('讨论该上涨趋势级别'));
  checks.push('二三买重合的联合条件、扩大中枢可能及同级别限制保留');
  const capital=claim('022','third-buy-interception-time-opponent-exception');
  assert.ok(capital.exceptions.some(x=>x.includes('且资金无期限且题材不迫切')));
  const funds=claim('022','own-unlimited-funds-interception');
  assert.ok(funds.conditions.includes('资金自由且无期限'));
  assert.ok(funds.conditions.includes('自有资金且无利息压力'));
  checks.push('大资金阻击的联合例外与自有资金期限限制保留');
  const running=claim('023','running-pullback-description');
  assert.match(running.text,/C段回拉只稍破A段高点/);
  assert.ok(claim('023','pullback-center-down-up-down-flat-alternative').exceptions.some(x=>x.includes('盘整平走')));
  assert.match(claim('023','daily-third-three-level-divergence-location').text,/30分钟回抽.*5分钟背驰/);
  assert.equal(claim('023','third-buy-confirm-return-cannot-enter').ambiguity_status,'reference_level_ambiguity');
  checks.push('奔走型A高点、平走替代与三层定位保留；参照歧义未隐藏');
  const standard=claim('024','standard-macd-area-completion-test');
  assert.ok(standard.conditions.includes('C走势类型完成'));
  assert.ok(standard.conditions.includes('C对应柱面积小于A'));
  assert.ok(claim('024','macd-area-estimate-twice-existing').conditions.includes('柱子伸长力度已经变慢'));
  assert.match(claim('024','consolidation-breakout-first-exit-two-paths').text,/不回原中枢.*第一买点.*回原中枢则继续盘整/);
  assert.match(claim('024','standard-divergence-retrace-b-center').text,/至少重新进入B段中枢/);
  checks.push('标准MACD的完成与面积条件、近似估计限制及盘整两分支可查');
  assert.equal(graph.getClaim(id('024','second-retrace-not-necessarily-lower')),null);
  const onePrice=graph.query('page',{documentId:'volume_1.pdf',page:143}).data;
  assert.ok(onePrice.passages.some(x=>x.id.endsWith('-b000')&&x.role==='reader'&&x.text.includes('一个单位价格')));
  assert.ok(onePrice.passages.some(x=>x.id.endsWith('-b001')&&x.role==='author_reply'&&x.text.includes('均线')));
  checks.push('缺失问题的两次回拉未进入默认库；单价重叠问题和实际答复身份分开');
  const typo=claim('024','600217-new-high-first-zero-retest-case');
  assert.equal(typo.ambiguity_status,'source_typographic_discrepancy');
  assert.ok(typo.evidence.some(x=>x.quote.includes('6000217')));
  const later=claim('024','601333-departure-unconfirmed-response-case');
  assert.ok(later.evidence[0].figures.every(x=>x.origin_status==='later_annotation'));
  assert.match(later.text,/不能断言成功/);
  checks.push('原文代码异常原样保存；后加601333图不能把未确认摆脱改为成功');
  const requests=[
    ['search',{query:'重合',limit:100},['search','重合','--limit','100']],
    ['search',{query:'标准MACD'},['search','标准MACD']],
    ['concept',{id:'盘整背驰',limit:100},['concept','盘整背驰','--limit','100']],
    ['neighbors',{id:'背驰',depth:1,limit:100},['neighbors','背驰','--depth','1','--limit','100']],
    ['evidence',{id:standard.evidence[0].id},['evidence',standard.evidence[0].id]],
    ['page',{documentId:'volume_1.pdf',page:143},['page','--document-id','volume_1.pdf','--page','143']],
    ['search',{query:'6000217',scope:'source'},['search','6000217','--scope','source']],
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
  const edge=graph.query('neighbors',{id:'背驰',limit:200}).data.edges.find(x=>x.claim_ids.includes(id('024','divergence-points-theorem')));
  assert.ok(edge);
  assert.deepEqual({database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
  const report={graph_version:graph.metadata.graph_version,schema_version:graph.metadata.schema_version,checks,parity,
    core_sha256:sha(resolve(agent,'src/core.mjs')),desktop_core_sha256:sha(resolve(agent,'../chan-kg-desktop/vendor/core.mjs')),
    database_and_manifest_unchanged:true,pass:true,
    limits:['验证共享模块、桌面vendor及独立CLI，未执行Electron界面。','以上来源语义场景属于同模型开发验收，不宣称独立或人工金标准。']};
  writeFileSync(resolve(agent,'curation/source-audit/stage-c-l021-l024-verification.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report));
}finally{graph.close();desktop.close();}
