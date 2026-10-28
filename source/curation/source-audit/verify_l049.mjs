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
const graph = new KnowledgeGraph(root), desktop = new DesktopGraph(root);
const claim = slug => { const c = graph.getClaim('upper-l049-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try {
 assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l049-c-stage-%' AND review_status='reviewed'").get().n,42);
 assert.match(claim('fix-operation-level-first-find-last-established-center').review_note,/已形成不等已完成或被离开/);
 assert.match(claim('three-current-positions-around-last-center').text,/在内.*下.*上.*三卖.*三买/);
 assert.match(claim('inside-center-wait-skilled-sublevel-second-buy-exception').text,/次级二买.*也可参与/);
 assert.notEqual(claim('near-new-buy-entry-but-completed-submove-top-divergence-wait-number-tension').ambiguity_status,'none');
 assert.match(source('0356-b010').text,/对于第二种第2类/);
 assert.match(claim('near-new-buy-entry-but-completed-submove-top-divergence-wait-number-tension').review_note,/不偷偷校成第三种第2类/);
 assert.match(claim('third-sell-instant-point-operational-small-interval').review_note,/无固定时间\/价格宽度/);
 checks.push('42新增；先固定级别找最后已形成中枢非要求已结束，三位置/三点状态分类保技能例外；原第二种第2类买点衔接号差保歧义，瞬间精确点与足够小操作区间不冒预知/固定宽度');

 assert.match(claim('oscillation-generally-contracts-expanding-force-not-automatic-third-sell').text,/特殊扩张.*不必然.*三卖/);
 assert.match(claim('oscillation-upper-reduce-lower-add-no-rebuy-after-third-sell').conditions.join(' '),/震荡仍在.*三卖不再回补/);
 assert.match(claim('upward-center-move-full-position-no-intermediate-difference').text,/不做短差.*满仓持至新中枢/);
 assert.match(claim('completed-upmove-divergence-sell-all-wait-next-buy').review_note,/非任何分笔\/较小级背驰/);
 assert.match(claim('no-divergence-new-center-may-overlap-small-to-large').text,/小级转大.*重合.*趋势同级中枢不能/);
 assert.match(claim('full-oscillation-sell-buyback-needs-skill-novice-partial-risk').text,/误判可抛错.*不熟者可不全仓.*直接三卖/);
 assert.notEqual(claim('mechanical-own-center-oscillation-safe-no-chip-loss-author-condition').ambiguity_status,'none');
 checks.push('震荡一般收敛但可扩张更强而未三卖，三卖停止回补；三买前原枢震荡/完成上移持股/新枢再震荡区分，同级背驰退出不混所有小级；理想全仓不抹误判和新手部分、可直接三卖风险');

 for(const slug of ['first-profit-maximum-theorem-fixed-instrument-fixed-level-author','second-profit-maximum-theorem-different-instruments-fixed-level']){const c=claim(slug);assert.notEqual(c.ambiguity_status,'none');assert.match(c.review_note,/未附证明/);assert.equal(c.conditions.length,3);}
 assert.match(claim('profit-rate-average-profit-divided-average-capital-time-frequency').text,/平均利润除以.*平均时间.*频率.*不比第一/);
 assert.match(claim('profit-rate-average-profit-divided-average-capital-time-frequency').review_note,/不静改为年化收益率/);
 assert.notEqual(claim('practice-fifty-percent-wrong-ten-percent-spread-unverified').ambiguity_status,'none');
 assert.match(claim('practice-fifty-percent-wrong-ten-percent-spread-unverified').review_note,/没有|无样本|未给等概率实验/);
 assert.match(claim('annual-two-hundred-five-hundred-author-unverified-performance').review_note,/没有账户流水.*回测.*独立审计/);
 assert.match(claim('capital-size-reduces-utilization-and-growth-bottleneck').text,/不能全仓.*利用率.*瓶颈.*留后/);
 assert.match(claim('mode-only-own-consolidation-up-small-level-no-zero-cost').text,/小级别操作不会出现成本0/);
 checks.push('两命名最大定理是作者陈述未附证明/执行假设，利润率平均利润除占资平均时间非年化且总体看频率；50%/10%和200%/500%无样本/审计，资金容量和小级无0成本限定不删');

 assert.match(claim('aggressive-switch-only-third-buy-exit-at-new-center').text,/不参与中枢震荡.*三买买入.*新中枢就退出/);
 assert.match(claim('aggressive-thirty-five-down-next-up-no-high-or-divergence-exit').conditions.join(' '),/30分钟.*5分向下.*5分向上.*或背驰或盘整背驰/);
 assert.match(claim('aggressive-needs-third-buys-first-broader-not-worst-unilateral').text,/无|否则只能等/);
 assert.match(claim('aggressive-needs-third-buys-first-broader-not-worst-unilateral').review_note,/最恶劣例外/);
 assert.match(claim('two-child-centers-connector-third-buy-is-third-child').text,/连接.*含三买.*三个次级/);
 assert.match(claim('two-child-centers-connector-third-buy-is-third-child').review_note,/是否已完成未获独立明确/);
 assert.equal(source('0362-b005').role,'reader');assert.match(claim('lower-cost-before-chips-not-assume-future-doubling').review_note,/未认可读者/);
 checks.push('激进换股只三买/新枢退出，30例先5下后5上三择一退出不改成AND；无三买等待、最恶劣单边例外与频率条件保留，连接段补第三次级不冒高级中枢已完成，读者50/80抛法未认可');

 assert.match(claim('choose-two-legs-before-MACD-not-standalone-second-condition').text,/先选择比较哪两段.*MACD.*辅助/);
 assert.match(claim('tick-divergence-one-minute-area-five-view-one-signal-correlations').text,/分笔背驰.*1分柱面积.*5分柱面积.*1分背驰/);
 assert.notEqual(claim('tick-divergence-one-minute-area-five-view-one-signal-correlations').ambiguity_status,'none');
 assert.match(claim('tick-divergence-one-minute-area-five-view-one-signal-correlations').review_note,/47.*长度.*分别保留/);
 assert.match(source('0360-b009').text,/黄白柱.*面子/);
 assert.match(source('0361-b001').text,/04240935/);assert.match(source('0350-b000').text,/04240931/);
 assert.match(claim('3745-center-upper-edge-not-reader-last-minute-price').review_note,/不认可读者/);
 assert.match(claim('turnover-not-exit-intent-proof-level-and-chart-matter').review_note,/日线有背驰吗是反问/);
 const plan=JSON.parse(readFileSync(resolve(agent,'curation/source-audit/stage-c-l049-source-plan.json'),'utf8'));assert.equal(plan.operations.length,25);assert.equal(plan.operations.filter(x=>x.table==='passages').length,21);
 for(const op of plan.operations.filter(x=>x.table==='passages')){assert.equal(source(op.id.split('-p')[1]).published_at,op.after.published_at);assert.equal(op.before.published_at,op.after.published_at.replace(' ',''));}
 const ledger=readFileSync(resolve(agent,'curation/upper/c_stage_l049.coverage.jsonl'),'utf8').trim().split('\n').map(JSON.parse);assert.equal(ledger.length,83);
 assert.equal(graph.db.prepare("SELECT count(*) n FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed' AND e.passage_id='volume_1-a53e99c37ca5-p0361-b004'").get().n,0);
 checks.push('先比较段再MACD，观察周期不等信号级；49分笔面积与47柱长不静合，黄白柱/面子原字、0935/0931和3745上沿保来源，反问不冒已证无背驰，公司恶意不作事实，21时间仅补空格、83段全台账');

 const links={
  'three-current-positions-around-last-center':['0356-b001',['0356-fig1','0359-fig1']],
  'below-no-third-sell-compare-previous-down-current-leg-nesting':['0356-b008',['0356-fig1','0359-fig1']],
  'below-third-sell-complete-containing-sublevel-or-skip':['0356-b009',['0359-fig1']],
  'above-without-third-buy-wait':['0356-b010',['0359-fig1']],
  'near-new-buy-entry-but-completed-submove-top-divergence-wait-number-tension':['0356-b010',['0356-fig1','0359-fig1']],
  'apr26-balanced-first-three-extremes-3745-conditional':['0359-b001',['0359-fig2']],
  '000625-fifteen-view-area-only-corresponding-small-level':['0360-b009',['0360-fig1']],
 };
 for(const [slug,[p,fs]] of Object.entries(links)){const e=claim(slug).evidence.find(e=>e.passage_id==='volume_1-a53e99c37ca5-p'+p);assert.deepEqual(e.figure_ids,fs.map(f=>'volume_1-a53e99c37ca5-p'+f));assert.equal(e.figures.length,fs.length);}
 const figs=graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 355 AND 362").all();assert.equal(figs.length,4);assert.equal(figs.filter(f=>f.origin_status==='later_annotation').length,2);
 assert.equal(graph.db.prepare("SELECT processing_status FROM units WHERE id='lesson-049'").get().processing_status,'semantic_read_with_pending');assert.equal(graph.metadata.semantic_completion,false);
 checks.push('7命题10关联4图逐项核，两流程原发未核不替正文校号/删例外，两4/27后K不证4/26预测或指标因果；只读模块一致非全书/真实Windows运行验收');

 const anchor=claim('first-profit-maximum-theorem-fixed-instrument-fixed-level-author').evidence.find(e=>e.passage_id.endsWith('0357-b005')).id;
 const requests=[['search',{query:'利润率'},['search','利润率']],['concept',{id:'缠中说禅第一利润最大定理',limit:20},['concept','缠中说禅第一利润最大定理','--limit','20']],['neighbors',{id:'利润率',depth:1,limit:100},['neighbors','利润率','--depth','1','--limit','100']],['evidence',{id:anchor},['evidence',anchor]],['page',{documentId:'volume_1.pdf',page:356},['page','--document-id','volume_1.pdf','--page','356']],['search',{query:'第二种第2类',scope:'source',limit:8},['search','第二种第2类','--scope','source','--limit','8']],['coverage',{},['coverage']]];
 const parity=[];for(const [command,args,argv] of requests){const a=JSON.parse(JSON.stringify(graph.query(command,args)));assert.deepEqual(JSON.parse(JSON.stringify(desktop.query(command,args))),a);const cli=spawnSync(process.execPath,[resolve(agent,'bin/chan-kg.mjs'),...argv,'--kb',root],{encoding:'utf8',maxBuffer:24*1024*1024});assert.equal(cli.status,0,cli.stderr);assert.deepEqual(JSON.parse(cli.stdout),a);parity.push({command,args,cli_matches_shared:true,desktop_module_matches_shared:true});}
 assert.deepEqual({database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
 const report={graph_version:graph.metadata.graph_version,schema_version:graph.metadata.schema_version,checks,parity,intended_figure_links_checked:{claims:7,associations:10,unique_figures:4},core_sha256:sha(resolve(agent,'src/core.mjs')),desktop_core_sha256:sha(resolve(agent,'../chan-kg-desktop/vendor/core.mjs')),database_and_manifest_unchanged:true,pass:true,limits:['同一模型边界/来源与模块一致性检查，非独立语义/回答质量或Windows实际运行。','最大定理未附证明，50/200/500未实证，编号/0931与0935/分笔面积与长度差异及完整执行条件未解决。','冻结g-b05-coincidence前20召回回归保持开放，未改金标准或核心排序规避。']};writeFileSync(resolve(agent,'curation/source-audit/stage-c-l049-verification.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({graph_version:report.graph_version,boundary_groups:checks.length,parity:parity.length,figure_links:report.intended_figure_links_checked,pass:true}));
}finally{graph.close();desktop.close();}
