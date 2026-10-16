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
  assert.equal(graph.db.prepare("SELECT count(*) AS n FROM claims WHERE (id LIKE 'lower-l089-c-stage-%' OR id LIKE 'lower-l090-c-stage-%') AND review_status='reviewed'").get().n,66);
  const required=claim('089','higher-must-five-center');
  assert.match(required.conditions.join(' '),/1分钟下跌背驰.*超1分钟/);
  assert.match(required.text,/必须先出现5分钟中枢.*不预设方向/);
  assert.match(claim('089','prepare-center-level-operation').exceptions.join(' '),/5分钟以上/);
  assert.match(claim('089','center-extension-or-third-point').text,/30分钟.*30分钟三类点/);
  checks.push('66条已复核知识；必经5分钟中枢的背驰前提、方向未定、操作级别与升级后处理保留');
  assert.match(claim('089','consolidation-not-flat-range').text,/10000跌到0.*一个中枢/);
  assert.match(claim('089','center-not-consolidation-apple').text,/不是同一概念/);
  assert.match(claim('089','consolidation-not-necessarily-weaker').text,/不一定比趋势弱/);
  assert.match(claim('089','nov22-small-sell-large-unknown').text,/1分钟三卖.*5分钟三卖仍未知/);
  checks.push('盘整与横盘、中枢和强弱分开，1分钟三卖不冒充5分钟确认');
  const auxiliary=claim('090','boll-auxiliary-not-absolute');
  assert.match(auxiliary.text,/辅助、非绝对.*接近100%.*例外/);
  assert.match(auxiliary.review_note,/无本项目样本测试/);
  assert.equal(claim('090','boll-first-point-sequence').conditions.length,4);
  assert.match(claim('090','boll-second-point-lag').text,/滞后.*常作阻力、支持/);
  checks.push('BOLL为有例外的辅助，近100%不是实测；一类点三步与二类点滞后条件保留');
  const contraction=claim('090','boll-contraction-expand-or-end');
  assert.match(contraction.text,/更低某级别.*扩展或结束.*一般/);
  assert.match(claim('090','boll-chart-period-not-one-to-one').text,/不能.*1分钟.*1分钟BOLL.*5分钟.*30分钟/);
  assert.match(claim('090','boll-chart-period-not-one-to-one').review_note,/不推广.*固定六倍/);
  assert.deepEqual(graph.query('concept',{id:'BOLL',limit:100}).data,graph.query('concept',{id:'布林通道',limit:100}).data);
  assert.deepEqual(graph.query('concept',{id:'中阴身阶段',limit:100}).data,graph.query('concept',{id:'中阴阶段',limit:100}).data);
  checks.push('收口可提示扩展或结束，指标周期不按固定倍数换算；两项别名返回同一概念');
  assert.match(claim('089','nov29-thirty-center-future').text,/将扩展出30分钟/);
  assert.match(claim('090','dec5-5032-fact-threshold').text,/5032之前还不能称事实.*12月5日/);
  assert.match(claim('090','dec4-channel-three-day-check').text,/一般突破后需3天/);
  assert.match(claim('090','dec5-ten-day-confirmation').text,/通道上轨突破、回抽，再突破10日线/);
  checks.push('展望与事实时点区分；通道三日观察和10日线确认不混并');
  const trap=claim('090','traps-require-center-oscillation');
  assert.match(trap.text,/中枢移动.*不能按陷阱/);
  assert.ok(claim('090','traps-need-force-comparison').conditions.includes('前后笔的力度比较'));
  const edges=graph.query('neighbors',{id:'市场陷阱',limit:100}).data.edges;
  assert.ok(edges.some(e=>e.claim_ids.includes(trap.id)&&e.type==='requires'));
  checks.push('陷阱要求中枢震荡而非移动，前后力度比较及关系依据保留');
  assert.match(claim('090','dec12-top-formed-not-down-stroke').text,/已形成.*尚未确认有效跌破.*不能马上断言/);
  assert.match(claim('090','dec14-week-formed-await-confirmation').text,/周底已构成.*下周.*确立/);
  assert.match(claim('090','dec14-next-daily-bottom-conditional').conditions.join(' '),/必须下周一构成/);
  assert.match(claim('090','dec17-daily-inclusion-not-bottom').text,/日底未构成、仅包含/);
  assert.match(claim('090','dec17-week-bottom-necessary').review_note,/必要不等于充分/);
  assert.match(claim('090','stock-commentary-not-buy-now').text,/并非让读者现在买/);
  checks.push('日顶形成/下笔确认、周底构成/确立及周一失败分支可查；旧股点评不成即时买点');
  const figs=graph.db.prepare("SELECT origin_status,count(*) AS n FROM figures WHERE document_id='volume_2-5332cd1b6038' AND pdf_page BETWEEN 250 AND 277 GROUP BY origin_status").all();
  assert.equal(figs.find(f=>f.origin_status==='later_annotation').n,11);
  assert.equal(figs.find(f=>f.origin_status==='unverified').n,7);
  const raw=graph.query('page',{documentId:'volume_2.pdf',page:276}).data.passages.find(p=>p.id.endsWith('-b002'));
  assert.equal(raw.role,'author_commentary');assert.match(raw.text,/只要大盘不红盘/);
  assert.equal(graph.db.prepare("SELECT count(*) AS n FROM claims WHERE review_status='reviewed' AND id LIKE 'lower-l090-c-stage-%' AND text LIKE '%不红盘%'").get().n,0);
  assert.equal(graph.metadata.semantic_completion,false);
  checks.push('11图后期/7图未核分开；不红盘原句保留但未抽成算法，全书未完成');
  const requests=[
    ['search',{query:'BOLL'},['search','BOLL']],
    ['concept',{id:'BOLL',limit:100},['concept','BOLL','--limit','100']],
    ['concept',{id:'中阴身阶段',limit:100},['concept','中阴身阶段','--limit','100']],
    ['neighbors',{id:'布林通道',depth:1,limit:100},['neighbors','布林通道','--depth','1','--limit','100']],
    ['evidence',{id:contraction.evidence[2].id},['evidence',contraction.evidence[2].id]],
    ['page',{documentId:'volume_2.pdf',page:276},['page','--document-id','volume_2.pdf','--page','276']],
    ['search',{query:'只要大盘不红盘',scope:'source'},['search','只要大盘不红盘','--scope','source']],
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
    limits:['共享核心/桌面vendor/CLI验证不等于Electron成品离线或PDF交互验收。','同模型开发场景，未验证BOLL统计胜率、全参数算法及作者账户成绩。']};
  writeFileSync(resolve(agent,'curation/source-audit/stage-c-l089-l090-verification.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report));
} finally {graph.close();desktop.close();}
