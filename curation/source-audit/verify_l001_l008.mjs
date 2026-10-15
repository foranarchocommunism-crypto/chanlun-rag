import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { KnowledgeGraph } from '../../src/core.mjs';
import { KnowledgeGraph as DesktopGraph } from '../../../chan-kg-desktop/vendor/core.mjs';

const agent = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const root = resolve(agent, '../shared-knowledge/v0.1.0');
const sha = path => createHash('sha256').update(readFileSync(path)).digest('hex');
const before = { database: sha(resolve(root, 'graph.sqlite')), manifest: sha(resolve(root, 'manifest.json')) };
const graph = new KnowledgeGraph(root);
const desktop = new DesktopGraph(root);
const checks = [];
const id = (lesson,slug) => `upper-l${String(lesson).padStart(3,'0')}-c-stage-${slug}`;
try {
  const observation=graph.getClaim(id(5,'observe-without-prejudice'));
  assert.match(observation.text,/不把主观想到的机会当成亲眼看到的机会/);
  checks.push('观察与想象的否定方向正确');
  const floor=graph.getClaim(id(6,'dual-warrant-safety-line-method'));
  assert.ok(floor.conditions.some(x=>x.includes('既有认购又有认沽')));
  assert.ok(floor.exceptions.some(x=>x.includes('行情特别不好')));
  const numeric=graph.getClaim(id(6,'wuliangye-baogang-body-values-case'));
  assert.match(numeric.text,/1.02元、0.43元/);
  assert.equal(numeric.ambiguity_status,'source_internal_numeric_conflict');
  checks.push('双权证及行情例外保留；正文0.43和数值冲突身份可查');
  const oldStock=graph.getClaim(id(7,'old-stock-year-line-retest'));
  assert.match(oldStock.text,/先放量突破年线、然后缩量回调年线/);
  assert.ok(oldStock.conditions.some(x=>x.includes('牛市')));
  const exit=graph.getClaim(id(7,'strong-first-wave-second-wave-warning'));
  assert.ok(exit.conditions.some(x=>x.includes('背弛或放巨量之一')));
  checks.push('年线突破回调顺序、牛市限定与退出的替代条件完整');
  const averages=graph.getClaim(id(8,'classification-example-averages'));
  assert.ok(averages.conditions.some(x=>x.includes('资金量不大且短线技术还可以')));
  const year=graph.getClaim(id(8,'year-line-250-days-and-chart-periods'));
  assert.match(year.text,/一般指250日均线/);
  assert.equal(year.evidence[0].pdf_page,21);
  assert.equal(year.evidence[0].printed_page,'15');
  assert.equal(year.evidence[0].role,'author_reply');
  checks.push('分类均线替换联合前提、年线定义和双页码一致');
  const figure=graph.getClaim(id(7,'baogang-year-line-case'));
  assert.equal(figure.evidence[0].figures.length,2);
  assert.ok(figure.evidence[0].figures.every(x=>x.origin_status==='unverified'));
  const page=graph.query('page',{documentId:'volume_1.pdf',page:22}).data;
  assert.equal(page.figures[0].origin_status,'later_annotation');
  assert.ok(page.passages.some(x=>x.role==='reader' && x.speaker==='冰火'));
  checks.push('已看图仍保留未核来源；后加月线图与读者身份分别显示');
  const requests=[
    ['search',{query:'年线',limit:100},['search','年线','--limit','100']],
    ['concept',{id:'年线'},['concept','年线']],
    ['search',{query:'行权价差'},['search','行权价差']],
    ['search',{query:'第二波'},['search','第二波']],
    ['evidence',{id:oldStock.evidence[0].id},['evidence',oldStock.evidence[0].id]],
    ['page',{documentId:'volume_1.pdf',page:21},['page','--document-id','volume_1.pdf','--page','21']],
    ['neighbors',{id:'中枢',depth:1,limit:40},['neighbors','中枢','--depth','1','--limit','40']],
    ['coverage',{},['coverage']],
  ];
  const parity=[];
  for(const [command,args,argv] of requests){
    const a=JSON.parse(JSON.stringify(graph.query(command,args)));
    const b=JSON.parse(JSON.stringify(desktop.query(command,args)));
    assert.deepEqual(a,b,command);
    const cli=spawnSync(process.execPath,[resolve(agent,'bin/chan-kg.mjs'),...argv,'--kb',root],{encoding:'utf8',maxBuffer:20*1024*1024});
    assert.equal(cli.status,0,cli.stderr);
    assert.deepEqual(JSON.parse(cli.stdout),a,command+' CLI');
    parity.push({command,args,cli_matches_shared:true,desktop_module_matches_shared:true});
  }
  const searched=graph.query('search',{query:'年线',limit:100}).data.results;
  assert.ok(searched.some(x=>x.id===year.id));
  const current={database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))};
  assert.deepEqual(current,before);
  const report={graph_version:graph.metadata.graph_version,schema_version:graph.metadata.schema_version,
    checks,parity,core_sha256:sha(resolve(agent,'src/core.mjs')),desktop_core_sha256:sha(resolve(agent,'../chan-kg-desktop/vendor/core.mjs')),
    database_and_manifest_unchanged:true,pass:true,
    limits:['这里只验证共享模块、桌面实际vendor模块及独立CLI；未运行Electron界面。','语义场景为同模型审读后的开发验收，未计为240题独立金标准。']};
  writeFileSync(resolve(agent,'curation/source-audit/stage-c-l001-l008-verification.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report));
}finally{graph.close();desktop.close();}
