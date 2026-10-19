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
const claim = slug => { const c = graph.getClaim('upper-l048-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try {
 assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l048-c-stage-%' AND review_status='reviewed'").get().n,39);
 assert.match(claim('risk-control-level-and-zero-cost-absolute-safety-author-claim').text,/0成本是绝对无风险/);
 assert.notEqual(claim('risk-control-level-and-zero-cost-absolute-safety-author-claim').ambiguity_status,'none');
 assert.match(claim('risk-control-level-and-zero-cost-absolute-safety-author-claim').review_note,/未证明剩余市值.*机会成本.*流动性/);
 assert.match(claim('large-capital-zero-cost-strategy-small-not-necessary-channel').text,/10万元.*10亿元.*操作时间和通道/);
 assert.match(claim('large-capital-zero-cost-strategy-small-not-necessary-channel').review_note,/非精确定量分界/);
 assert.match(claim('double-price-return-capital-depends-better-use').review_note,/但依然不动.*未补扣费/);
 assert.match(claim('after-zero-gain-chips-until-very-large-sell').text,/特大级别出现卖点/);
 checks.push('39新增；零成本绝对无风险记录作者强语与核算语境，不证剩余市值/机会/执行风险全无；10万10亿示例非阈值，资金容量通道和翻倍后资金利用率条件齐全，0后仍有特大卖点');

 assert.match(claim('effective-break-same-as-third-sell-no-three-bars-rule').text,/是否有效跌破.*有没有三卖/);
 assert.match(claim('effective-break-same-as-third-sell-no-three-bars-rule').review_note,/未认可固定三根K数量阈值/);
 assert.equal(source('0350-b005').role,'reader');assert.match(source('0350-b005').text,/连续3个5分钟线/);
 assert.match(claim('first-sell-most-active-second-next-third-later-skill').text,/一卖最主动.*二卖.*三卖/);
 assert.match(claim('two-centers-trend-can-end-any-time-not-must').review_note,/不表示任意两中枢即已成趋势.*必结束/);
 assert.match(claim('intraday-down-below-one-divergence-and-trend-level-may-differ').review_note,/不允许背驰大于其所处当下走势类型/);
 checks.push('有效跌破同三卖，读者三根5分收低不冒作者规则；一二卖主动和三卖较晚分开，两中枢可完非必结束，盘中例定级/背驰级别与43包含上界同时保留');

 assert.equal(claim('thirty-operation-tolerates-five-normal-correction').conditions.length,2);
 assert.match(claim('thirty-operation-tolerates-five-normal-correction').text,/正常情况下.*5分走势类型修正/);
 assert.match(claim('correction-first-center-above-five-exit-atleast-thirty-consolidation').text,/修正的第一中枢级别大于5分.*至少形成30分盘整.*二卖.*以后讲/);
 assert.equal(claim('correction-first-center-above-five-exit-atleast-thirty-consolidation').conditions.length,2);
 assert.match(claim('no-same-level-divergence-new-center-or-small-to-large').text,/新中枢或小级别转大/);
 assert.notEqual(claim('third-center-C-means-rise-extension-qualified-short-reply').ambiguity_status,'none');
 assert.match(claim('third-center-C-means-rise-extension-qualified-short-reply').review_note,/未逐项明确答/);
 checks.push('30分操作可忍正常5分修正，第一修正中枢>5才至少30盘整及先出/二卖，精细后讲；无同级背驰仍有小转大分支，短答一般如此不逐项背书读者B方向/c撇/d比较');

 assert.match(claim('first-segment-in-third-case-center-range-not-single-segment').text,/第一段完全被后第三段包含.*三段中枢区间等于第一段/);
 assert.match(claim('first-segment-in-third-case-center-range-not-single-segment').review_note,/不足一般证明第二也覆盖/);
 assert.match(claim('force-computable-no-formula-MACD-proxy-no-escape-physics-law').review_note,/不等认同读者引力质量/);
 assert.match(claim('c-force-above-b-not-necessarily-disjoint-new-center').text,/不必然生新中枢.*小级转大.*重合/);
 assert.match(claim('trend-new-centers-no-overlap-same-level').conditions.join(' '),/同级别.*中枢区间本身/);
 assert.match(claim('trend-new-centers-no-overlap-same-level').review_note,/不扩大成围绕中枢全部瞬时波动/);
 checks.push('中枢区间等首段限该例，不把单段当完整中枢或只首第三包含当一般三交证明；可计算不冒物理逃逸公式，c>b不必新生不交中枢，真趋势同级中枢区间不交与外围波动分开');

 const plan=JSON.parse(readFileSync(resolve(agent,'curation/source-audit/stage-c-l048-source-plan.json'),'utf8'));assert.equal(plan.operations.length,60);
 const pops=plan.operations.filter(x=>x.table==='passages');assert.equal(pops.length,59);
 const dates=pops.filter(op=>op.before.published_at.slice(0,10)!==op.after.published_at.slice(0,10));assert.equal(dates.length,4);
 for(const op of pops){assert.equal(source(op.id.split('-p')[1]).published_at,op.after.published_at);if(!dates.includes(op))assert.equal(op.before.published_at,op.after.published_at.replace(' ',''));}
 assert.equal(source('0349-b004').published_at,'2007-04-25 15:25:17');assert.equal(source('0350-b002').published_at,'2007-04-25 15:25:17');
 assert.match(source('0349-b002').text,/3688到3692/);assert.match(source('0349-b004').text,/3688到3699/);
 assert.notEqual(claim('apr25-return-3688-3699-oscillation-price-difference-retained').ambiguity_status,'none');
 const ledger=readFileSync(resolve(agent,'curation/upper/c_stage_l048.coverage.jsonl'),'utf8').trim().split('\n').map(JSON.parse);assert.equal(ledger.length,130);
 for(const p of ['0350-b002','0352-b006','0352-b008','0354-b006','0354-b009'])assert.equal(graph.db.prepare("SELECT count(*) n FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed' AND e.passage_id=?").get('volume_1-a53e99c37ca5-p'+p).n,0);
 assert.match(claim('fear-half-position-first-psychology-not-guaranteed-profit').text,/技术及心态好者不适用/);
 assert.match(claim('fear-half-position-first-psychology-not-guaranteed-profit').review_note,/不能回填别课/);
 checks.push('4段4/25收评日期纠正与55空格规范，130段含全部读者/非技术上下文；3692/3699原字不静合，机构阴谋和政治评语不升技术事实，恐慌半仓不回填其他课程且保好技术/心态例外');

 const links={
  'apr24-previous-small-center-support-five-minute-consolidation-top':'0349-b002',
  'apr25-return-3688-3699-oscillation-price-difference-retained':'0349-b004',
  'apr25-first-three-bars-most-balanced-case-not-universal':'0349-b004',
  'apr25-1335-1030-line-trumpet-conditional':'0350-b000',
  'apr25-3689-3745-five-center-extension-third-points':'0350-b000',
 };
 for(const [slug,p] of Object.entries(links)){const e=claim(slug).evidence.find(e=>e.passage_id==='volume_1-a53e99c37ca5-p'+p);assert.deepEqual(e.figure_ids,['volume_1-a53e99c37ca5-p0349-fig1']);assert.equal(e.figures[0].origin_status,'later_annotation');}
 assert.equal(graph.db.prepare("SELECT processing_status FROM units WHERE id='lesson-048'").get().processing_status,'semantic_read_with_pending');assert.equal(graph.metadata.semantic_completion,false);
 checks.push('5命题5关联1整图逐项核；4/25图相对4/24文字为后加，当日可得仍未核原制图者，历史大顶/周7%/20年强语非预测实证，模块一致不冒Windows实际运行');

 const anchor=claim('correction-first-center-above-five-exit-atleast-thirty-consolidation').evidence[0].id;
 const requests=[['search',{query:'第一中枢'},['search','第一中枢']],['concept',{id:'零成本持仓',limit:20},['concept','零成本持仓','--limit','20']],['neighbors',{id:'有效跌破',depth:1,limit:100},['neighbors','有效跌破','--depth','1','--limit','100']],['evidence',{id:anchor},['evidence',anchor]],['page',{documentId:'volume_1.pdf',page:354},['page','--document-id','volume_1.pdf','--page','354']],['search',{query:'3699',scope:'source',limit:8},['search','3699','--scope','source','--limit','8']],['coverage',{},['coverage']]];
 const parity=[];for(const [command,args,argv] of requests){const a=JSON.parse(JSON.stringify(graph.query(command,args)));assert.deepEqual(JSON.parse(JSON.stringify(desktop.query(command,args))),a);const cli=spawnSync(process.execPath,[resolve(agent,'bin/chan-kg.mjs'),...argv,'--kb',root],{encoding:'utf8',maxBuffer:24*1024*1024});assert.equal(cli.status,0,cli.stderr);assert.deepEqual(JSON.parse(cli.stdout),a);parity.push({command,args,cli_matches_shared:true,desktop_module_matches_shared:true});}
 assert.deepEqual({database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
 const report={graph_version:graph.metadata.graph_version,schema_version:graph.metadata.schema_version,checks,parity,intended_figure_links_checked:{claims:5,associations:5,unique_figures:1},core_sha256:sha(resolve(agent,'src/core.mjs')),desktop_core_sha256:sha(resolve(agent,'../chan-kg-desktop/vendor/core.mjs')),database_and_manifest_unchanged:true,pass:true,limits:['同模型范围检查/模块一致，非独立语义或生成回答及Windows运行验收。','零成本绝对风险、3692/3699及第二段交集、两中枢可完和力度可计算条件/公式仍待核。','冻结g-b05-coincidence前20召回回归未在此修改核心排序或金标准规避。']};writeFileSync(resolve(agent,'curation/source-audit/stage-c-l048-verification.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({graph_version:report.graph_version,boundary_groups:checks.length,parity:parity.length,figure_links:report.intended_figure_links_checked,pass:true}));
}finally{graph.close();desktop.close();}
