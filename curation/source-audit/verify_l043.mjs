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
const claim = slug => { const c = graph.getClaim('upper-l043-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try {
 assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l043-c-stage-%' AND review_status='reviewed'").get().n,32);
 assert.match(claim('divergence-level-not-above-containing-current-move').text,/不可能大于.*至少30分钟/);
 assert.match(claim('one-minute-top-at-least-one-consolidation-or-down-may-rise-again').text,/至少引出1分钟盘整或下跌.*仍可继续上涨/);
 assert.match(claim('extreme-yearly-down-by-gradual-expansion-not-direct-minimum-cause').review_note,/可能而非每次必然/);
 assert.match(claim('own-divergence-terminates-original-type-next-same-or-higher').review_note,/不把刚入背驰段等同已成立/);
 assert.match(claim('no-up-plus-up-no-down-plus-down-premise').review_note,/没有在此禁止38课.*盘整\+盘整/);
 assert.ok(graph.getClaim('upper-l029-c-stage-divergence-reversal-theorem-three-outcomes'));
 checks.push('32新增；背驰/所在类型级别与后续转折级别分开，1分顶背后先同级盘整可续涨，逐步扩张非即时年线预测；重引29定理保留旧记录，未推禁38同级盘整+盘整');

 assert.equal(claim('same-level-divergence-pulls-last-center-break-corresponding-extreme').conditions.length,2);
 assert.match(claim('same-level-divergence-pulls-last-center-break-corresponding-extreme').review_note,/不擅换成任意中枢上下沿/);
 assert.match(claim('entering-divergence-segment-not-guaranteed-divergence-small-extension').text,/并不保证最终背驰/);
 assert.match(claim('smaller-case-thirty-no-divergence-c-has-one-minute').text,/明确没有30分背驰.*c内可有1分/);
 assert.match(claim('smaller-turn-can-return-B-via-bigger-than-one-center').review_note,/若最终回B才是所述必经路径/);
 assert.match(claim('larger-center-after-small-divergence-may-break-up-extend').text,/未必回跌.*可向上突破/);
 assert.match(claim('MACD-zero-return-up-initial-segment-yellow-white-high-unknown').review_note,/候选而非预先确认/);
 assert.match(claim('strong-small-structure-new-yellow-white-high-no-divergence').review_note,/候选段语境/);
 checks.push('同级已成背驰才套回最后中枢分支；入段可被小级延伸取消，30分无背驰而c内1分背驰另一支，若回B先较大中枢/下破但可上破续延，MACD回轴再上只先视候选');

 assert.match(claim('decomposition-principle-no-higher-center-inside-one-type').text,/一部分，或几个本级类型的连接/);
 assert.equal(claim('C-thirty-no-overlap-B-original-thirty-unfinished-extends').conditions.length,2);
 assert.match(claim('C-thirty-no-overlap-B-original-thirty-unfinished-extends').text,/无任何重叠.*尚未完成.*须等完成/);
 assert.match(claim('B-C-overlap-evolves-daily-not-already-formed').text,/演化为日线中枢.*不等于.*已经形成/);
 assert.match(claim('C-not-necessarily-complete-expanded-division-normal').review_note,/不一定完成不是必然未完成/);
 assert.match(claim('overlap-original-part-daily-fixed-thirty-boundary-small-divergence').text,/若坚持30分同级分解.*1分背驰点/);
 assert.equal(source('0316-b001').role,'reader');assert.equal(source('0316-b003').role,'reader');
 for(const e of graph.db.prepare("SELECT e.quote FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed' AND e.passage_id='volume_1-a53e99c37ca5-p0316-b004'").all()) assert.ok(!e.quote.includes('注：')&&!e.quote.includes('禅师的意思'));
 assert.equal(claim('associativity-direction-not-most-important-author-tail').evidence[0].quote,'有了结合律，方向都不是最重要的。');
 checks.push('B/C无重合继续原30分待完，有重合演化日线不等已成，固定30分取小背驰为界且C不一定完成；316夹注一字不入作者引文，注后结合律单独定位，混合来源待核未冒称已拆');

 assert.equal(source('0315-b002').role,'reader');assert.equal(source('0315-b003').role,'reader');
 assert.match(claim('rough-exit-after-break-wait-rebound-not-chase-down-can-still-new-high').review_note,/读者引文与提问保留读者身份/);
 assert.match(claim('fine-method-can-exit-before-break-mechanical-rougher').review_note,/没有给提前退出的独立算法/);
 assert.notEqual(claim('persistent-mechanical-super-return-author-claim').ambiguity_status,'none');
 assert.equal(source('0315-b008').role,'reader');assert.match(source('0315-b008').text,/1\/3/);
 assert.match(claim('new-stock-candlestick-pattern-auxiliary-not-point-definition').review_note,/作者未逐项证明数字法/);
 assert.notEqual(claim('apr9-many-large-caps-below-twenty-PE-author-reply').ambiguity_status,'none');
 checks.push('读者破位反弹粗法获认可不等立即杀跌，精法可先走未给算法；超级回报无实证，新股前三K/1/3为读者、仅辅助K形态，不认证通用充分点或整体PE安全');

 const plan=JSON.parse(readFileSync(resolve(agent,'curation/source-audit/stage-c-l043-source-plan.json'),'utf8'));
 assert.equal(plan.operations.length,17);assert.equal(plan.operations.filter(x=>x.table==='passages').length,15);
 for(const op of plan.operations.filter(x=>x.table==='passages'))assert.equal(source(op.id.split('-p')[1]).published_at,op.after.published_at);
 for(const p of ['0314-b002','0314-b003','0314-b004','0314-b005'])assert.equal(source(p).published_at,'2007-04-09 15:33:39');
 assert.equal(source('0314-b001').published_at,'2007-04-06 15:32:12');
 assert.match(claim('apr6-pressure-attacked-not-yet-break-stand-ten-thousand-conditional').text,/未突破站上.*若突破站稳/);
 assert.match(claim('apr9-gap-break-needs-confirmation-gap-pullback-pressure').text,/有效性仍需确认/);
 assert.notEqual(claim('apr9-only-policy-large-oscillation-author-strong-view').ambiguity_status,'none');
 checks.push('4/9四段日期纠正且前4/6不改，11时间仅补空格；冲击/缺口不等确认，万点/二线/政策唯一风险仅历史条件判断和未核强词');

 const links={
  'one-minute-top-at-least-one-consolidation-or-down-may-rise-again':['0312-b001',['0312-fig1']],
  'apr6-pressure-attacked-not-yet-break-stand-ten-thousand-conditional':['0313-b007',['0314-fig1']],
  'apr6-second-line-spreads-beyond-ten-consolidation-earnings':['0313-b009',['0314-fig1']],
  'apr9-gap-break-needs-confirmation-gap-pullback-pressure':['0314-b003',['0314-fig1']],
 };
 for(const [slug,[passage,figures]] of Object.entries(links)){const e=claim(slug).evidence.find(e=>e.passage_id==='volume_1-a53e99c37ca5-p'+passage);assert.deepEqual(e.figure_ids,figures.map(f=>'volume_1-a53e99c37ca5-p'+f));assert.equal(e.figures.length,figures.length);}
 const figs=graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 311 AND 316").all();assert.equal(figs.length,2);assert.equal(figs.filter(f=>f.origin_status==='later_annotation').length,1);
 const ledger=readFileSync(resolve(agent,'curation/upper/c_stage_l043.coverage.jsonl'),'utf8').trim().split('\n').map(JSON.parse);assert.equal(ledger.length,57);assert.ok(ledger.some(x=>x.related_existing_claim_ids.includes('upper-l029-c-stage-divergence-reversal-theorem-three-outcomes')));
 assert.equal(graph.db.prepare("SELECT processing_status FROM units WHERE id='lesson-043'").get().processing_status,'semantic_read_with_pending');assert.equal(graph.metadata.semantic_completion,false);
 checks.push('57全段台账及旧29线索保留，4命题4关联2整图逐项核验：示意原发未核、行情4/10为后加；不补全全书/夹注来源或桌面运行验收');

 const anchor=claim('B-C-overlap-evolves-daily-not-already-formed').evidence.find(e=>e.pdf_page===316).id;
 const requests=[
  ['search',{query:'背驰段'},['search','背驰段']],
  ['concept',{id:'缠中说禅走势类型分解原则',limit:20},['concept','缠中说禅走势类型分解原则','--limit','20']],
  ['neighbors',{id:'小级别转大级别',depth:1,limit:100},['neighbors','小级别转大级别','--depth','1','--limit','100']],
  ['evidence',{id:anchor},['evidence',anchor]],
  ['page',{documentId:'volume_1.pdf',page:316},['page','--document-id','volume_1.pdf','--page','316']],
  ['search',{query:'1/3',scope:'source',limit:8},['search','1/3','--scope','source','--limit','8']],
  ['coverage',{},['coverage']],
 ];
 const parity=[];
 for(const [command,args,argv] of requests){const a=JSON.parse(JSON.stringify(graph.query(command,args)));assert.deepEqual(JSON.parse(JSON.stringify(desktop.query(command,args))),a);const cli=spawnSync(process.execPath,[resolve(agent,'bin/chan-kg.mjs'),...argv,'--kb',root],{encoding:'utf8',maxBuffer:24*1024*1024});assert.equal(cli.status,0,cli.stderr);assert.deepEqual(JSON.parse(cli.stdout),a);parity.push({command,args,cli_matches_shared:true,desktop_module_matches_shared:true});}
 assert.deepEqual({database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
 const report={graph_version:graph.metadata.graph_version,schema_version:graph.metadata.schema_version,checks,parity,intended_figure_links_checked:{claims:4,associations:4,unique_figures:2},core_sha256:sha(resolve(agent,'src/core.mjs')),desktop_core_sha256:sha(resolve(agent,'../chan-kg-desktop/vendor/core.mjs')),database_and_manifest_unchanged:true,pass:true,limits:['同模型边界检查与模块一致性，非独立语义或Windows真实运行/PDF交互。','316夹注在整来源段仍混存，作者证据已排除，身份细分待核；未给完整转折/提前退出/收益验证或原博客校对。']};
 writeFileSync(resolve(agent,'curation/source-audit/stage-c-l043-verification.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({graph_version:report.graph_version,boundary_groups:checks.length,parity:parity.length,figure_links:report.intended_figure_links_checked,pass:true}));
}finally{graph.close();desktop.close();}
