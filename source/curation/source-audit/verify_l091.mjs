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
const id=slug=>`lower-l091-c-stage-${slug}`;
const claim=slug=>{const c=graph.getClaim(id(slug));assert.ok(c);return c;};
const checks=[];
try {
  assert.equal(graph.db.prepare("SELECT count(*) AS n FROM claims WHERE id LIKE 'lower-l091-c-stage-%' AND review_status='reviewed'").get().n,47);
  assert.equal(claim('parts-center-capability').ambiguity_status,'stroke_center_cross_lesson_scope');
  assert.match(claim('parts-center-capability').text,/第91课所论.*笔归为不能构中枢/);
  assert.match(graph.getClaim('lower-l083-c-stage-stroke-center-possible-less-stable').text,/可以设计用笔构造最小中枢/);
  checks.push('47条新默认知识；91配件语境与83替代程序并列，未以日期覆盖');
  assert.match(claim('stroke-theorem-current-two-phases').text,/任一时间周期K线图/);
  const meanings=claim('four-state-meanings');
  for(const term of ['(1,1)向上笔延伸','(-1,1)向下笔延伸','(1,0)向上笔出现顶分型构造','(-1,0)向下笔出现底分型构造'])assert.ok(meanings.text.includes(term));
  const connections=claim('six-allowed-state-transitions');
  for(const term of ['(1,1)只到(1,0)','(-1,1)只到(-1,0)','(1,0)可到(1,1)或(-1,1)','(-1,0)可到(-1,1)或(1,1)'])assert.ok(connections.text.includes(term));
  assert.equal(connections.evidence.length,2);assert.deepEqual(connections.evidence.map(e=>e.pdf_page).sort(),[277,278]);
  checks.push('四态方向/阶段与六允许连接可查，跨PDF277/278的原句分别保留');
  assert.match(claim('both-up-small-warning-needed').text,/至少先出现\(1,0\)或\(-1,1\).*绝大多数/);
  assert.equal(claim('one-bar-warning-and-confirmation').ambiguity_status,'zero_state_confirmation_reference');
  assert.match(claim('small-down-large-zero-confirmation').text,/小图.*且导致.*大图.*再确认/);
  assert.ok(claim('larger-extension-filters-small-waves').conditions.includes('5分钟图仍为笔延伸状态'));
  checks.push('小图警告或条件与多数情形不同，单根5分钟警告和大图反转确认分层');
  const ranking=claim('week-day-four-worst-order');
  assert.match(ranking.text,/最恶劣.*其次.*第三.*第四.*可能转机/);
  assert.equal(ranking.text.includes('值得参与'),false);
  assert.match(ranking.review_note,/值得参与不是正文无条件结论/);
  assert.match(claim('dec17-worst-or-fourth-pending').text,/尚待市场选择/);
  checks.push('周日四种次序保留，第四只可能转机，图中值得参与未升级作者原话');
  assert.match(claim('eight-row-state-matrix-count').text,/8行.*4\^8/);
  assert.match(claim('eight-row-state-matrix-count').review_note,/未独立证明.*同时可达/);
  assert.match(claim('three-periods-sixty-four').text,/64种状态/);
  assert.match(claim('machine-profit-author-proposal').review_note,/不认证机器永动获利/);
  assert.match(claim('stroke-layer-not-whole-diagnosis').text,/仅笔.*不足精确诊断/);
  checks.push('4^8/64为组合记录，联合可达和自动获利未证明，笔表里非完整诊断');
  assert.match(claim('dec24-second-center-not-yet').text,/第二中枢也未出现/);
  assert.match(claim('dec25-center-formed-midpoint').text,/已形成.*5210.*5209.*1点/);
  assert.match(claim('dec24-neckline-break-await-confirm').text,/有效性仍待确认/);
  assert.ok(claim('dec25-strong-exception-larger-center').exceptions.some(x=>x.includes('不背驰')));
  checks.push('第二中枢未出/次日已成、5210/5209及三买不背驰强势例外保留');
  assert.match(claim('boll-break-can-be-bigger-oscillation').text,/不是必向一个方向.*更大级别震荡/);
  assert.match(claim('boll-select-by-pattern-structure-first').text,/并非任意级别收口都有效/);
  assert.match(claim('dec27-return-nine-case-upgrade').review_note,/不是任意九线段必升级/);
  assert.match(claim('dec27-no-divergence-before-third').review_note,/不推广所有盘整背驰/);
  checks.push('BOLL选择依结构，九段与三买前背驰语境仅当例，不推广裸数量算法');
  const fs=graph.db.prepare("SELECT origin_status,count(*) AS n FROM figures WHERE document_id='volume_2-5332cd1b6038' AND pdf_page BETWEEN 277 AND 290 GROUP BY origin_status").all();
  assert.equal(fs.find(x=>x.origin_status==='later_annotation').n,5);assert.equal(fs.find(x=>x.origin_status==='unverified').n,4);
  assert.ok(claim('forecast-year-close-not-final').conditions.includes('2007年年K尚未最终收盘'));
  assert.ok(claim('forecast-year-close-not-final').evidence.flatMap(e=>e.figures).every(f=>f.origin_status==='later_annotation'));
  assert.match(claim('petro-24-wine-not-price-guarantee').text,/24元称为酒话.*14元.*愿望/);
  assert.equal(graph.metadata.semantic_completion,false);
  checks.push('五后期图四未核图分开；2009图不证明2008预言，24酒话/14愿望不是目标保证');
  const requests=[
    ['search',{query:'(1,0)'},['search','(1,0)']],
    ['concept',{id:'笔状态',limit:100},['concept','笔状态','--limit','100']],
    ['concept',{id:'笔定理',limit:100},['concept','笔定理','--limit','100']],
    ['neighbors',{id:'表里关系',depth:1,limit:100},['neighbors','表里关系','--depth','1','--limit','100']],
    ['evidence',{id:connections.evidence[1].id},['evidence',connections.evidence[1].id]],
    ['page',{documentId:'volume_2.pdf',page:278},['page','--document-id','volume_2.pdf','--page','278']],
    ['search',{query:'笔是不能构成中枢的',scope:'source'},['search','笔是不能构成中枢的','--scope','source']],
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
    limits:['模块与CLI检查不是Windows成品离线、PDF高亮或实际界面验收。','同模型开发场景，未证明全部联合状态可达、四态实时识别完备或自动机器获利。']};
  writeFileSync(resolve(agent,'curation/source-audit/stage-c-l091-verification.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report));
} finally {graph.close();desktop.close();}
