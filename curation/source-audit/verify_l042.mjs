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
const claim = slug => { const c = graph.getClaim('upper-l042-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try {
 assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l042-c-stage-%' AND review_status='reviewed'").get().n,29);
 const typeClaims=graph.db.prepare("SELECT id FROM claims WHERE id LIKE 'upper-l042-c-stage-unsuitable-behavior-%'").all();assert.equal(typeClaims.length,10);
 for(const row of typeClaims){const c=graph.getClaim(row.id);assert.equal(c.conditions.length,2);assert.ok(c.conditions.some(x=>x.includes('当下')&&x.includes('不是永远')));assert.ok(c.evidence.some(e=>e.passage_id==='volume_1-a53e99c37ca5-p0307-b008'));}
 assert.match(claim('market-suitability-current-not-permanent-first-adjust').text,/当下意义.*并不意味着永远离开/);
 assert.match(claim('unsuitable-behavior-rigid-not-adapt').review_note,/非临床/);
 assert.match(claim('self-awareness-daily-ten-minute-operations-and-psychology-review').text,/十分钟.*操作及看盘心理/);
 assert.equal(graph.db.prepare("SELECT count(*) n FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed' AND e.passage_id='volume_1-a53e99c37ca5-p0306-b003'").get().n,0);
 checks.push('29新增；十类各有结尾非永久限定证据和条件，非临床标签；10分钟操作/心理复盘为建议，匿名内地亏香港赚无技术收益认证');

 assert.match(claim('apr5-second-line-ten-yuan-and-pressure-break-toward-ten-thousand').conditions.join(' '),/突破并站稳/);
 assert.match(claim('apr4-shenzhen-pressure-near-9200-second-line-author-script-view').review_note,/不认证真实机构/);
 assert.match(claim('weak-tech-five-day-midterm-ten-day-line-historical-fallback').review_note,/不认证5日线之上无风险/);
 assert.notEqual(claim('oscillation-lowers-cost-only-good-rhythm-author-view').ambiguity_status,'none');
 assert.match(claim('apr5-stability-policy-uncertainty-sector-rotation-multilevel-oscillation').review_note,/不认证.*真实组织身份/);
 checks.push('9200线/二线10元/万点和5或10日线均历史条件语境，突破且站稳联合；不以均线保无风险、成本强词证实盘或以后K认证预测/机构');

 const first=claim('first-daily-MACD-zero-return-rebuy-author-strong-case');
 assert.notEqual(first.ambiguity_status,'none');assert.match(first.review_note,/不推广为所有首次日线归零的充分买点/);assert.match(first.review_note,/创新高仅机会非必然/);
 for(const e of first.evidence)assert.deepEqual(e.figure_ids,[]);
 assert.equal(source('0309-b012').role,'reader');
 assert.match(claim('shenzhen-two-points-compare-one-minute-MACD-no-text-formula').review_note,/没有在文字指定零轴\/面积哪一项/);
 assert.match(claim('weak-tech-thirty-minute-five-day-no-large-energy-formula').text,/没有给耗尽公式/);
 checks.push('特定首次日线回零一定买回强语未作通用充分点且不挂指数图；两点都背驰仍是读者，作者只让看1分MACD未指定差异公式，大级耗尽问获30分/5日建议而非定义');

 assert.equal(source('0311-b009').role,'reader');assert.equal(source('0311-b010').role,'author_reply');
 assert.match(claim('consolidation-divergence-must-break-literal-target-unspecified').text,/盘整背驰一定跌破/);
 assert.match(claim('consolidation-divergence-must-break-literal-target-unspecified').review_note,/未重述级别、方向或跌破哪条边界/);
 assert.notEqual(claim('consolidation-divergence-must-break-literal-target-unspecified').ambiguity_status,'none');
 assert.ok(claim('break-not-necessarily-consolidation-divergence-a-prime-plus-B').text.includes('a`+B'));
 assert.match(claim('break-not-necessarily-consolidation-divergence-a-prime-plus-B').text,/不一定都是盘整背驰/);
 assert.match(graph.getClaim('upper-l041-c-stage-divergence-consolidation-only-turn-force-is-current').review_note,/转向不等一定发展为反趋势/);
 checks.push('盘背一定跌破保留作者原字，破位非都盘背及a`+B原式并存；目标/方向/级别未重述列歧义，未扩成必破任意中枢下沿或删41转向/幅度边界');

 assert.match(claim('600649-weekly-look-left-historical-dense-zone-case').text,/周线.*左边.*历史密集区/);
 assert.match(claim('historical-dense-zone-trapped-holders-turnover-author-explanation').review_note,/未以真实持有人账本证明/);
 assert.notEqual(claim('tsinghua-negative-news-fundamental-reassurance-author-rhetoric').ambiguity_status,'none');
 assert.match(claim('basic-chart-system-enough-if-understand-market-not-paid-tool-proof').review_note,/未对任何具体level2产品做功能评测/);
 assert.equal(source('0311-b012').role,'reader');
 checks.push('历史密集区概念可查，600649周线/多数被套换手为作者解释未核持仓账本；清华背景强安心非免风险，基础图足够有明白走势前提，反问不证全部付费工具无用');

 const plan=JSON.parse(readFileSync(resolve(agent,'curation/source-audit/stage-c-l042-source-plan.json'),'utf8'));
 assert.equal(plan.operations.length,28);assert.equal(plan.operations.filter(x=>x.table==='passages').length,24);
 for(const op of plan.operations.filter(x=>x.table==='passages')) assert.equal(source(op.id.split('-p')[1]).published_at,op.after.published_at);
 assert.equal(source('0308-b000').published_at,'2007-04-04 15:33:12');
 for(const p of ['0308-b001','0308-b002','0309-b000','0309-b001','0309-b002','0309-b003']) assert.equal(source(p).published_at,'2007-04-05 15:34:37');
 const links={
  'apr4-shenzhen-pressure-near-9200-second-line-author-script-view':['0307-b010',['0308-fig1','0308-fig2']],
  'apr5-second-line-ten-yuan-and-pressure-break-toward-ten-thousand':['0308-b002',['0308-fig1','0308-fig2']],
  'shenzhen-two-points-compare-one-minute-MACD-no-text-formula':['0309-b014',['0310-fig1']],
  '600649-weekly-look-left-historical-dense-zone-case':['0310-b002',['0310-fig2']],
  'historical-dense-zone-trapped-holders-turnover-author-explanation':['0311-b001',['0310-fig2']],
 };
 for(const [slug,[passage,figures]] of Object.entries(links)){const e=claim(slug).evidence.find(e=>e.passage_id==='volume_1-a53e99c37ca5-p'+passage);assert.deepEqual(e.figure_ids,figures.map(f=>'volume_1-a53e99c37ca5-p'+f));assert.equal(e.figures.length,figures.length);}
 const figs=graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 306 AND 311").all();assert.equal(figs.length,4);assert.equal(figs.filter(f=>f.origin_status==='later_annotation').length,3);
 const ledger=readFileSync(resolve(agent,'curation/upper/c_stage_l042.coverage.jsonl'),'utf8').trim().split('\n').map(JSON.parse);assert.equal(ledger.length,64);
 assert.equal(graph.db.prepare("SELECT processing_status FROM units WHERE id='lesson-042'").get().processing_status,'semantic_read_with_pending');assert.equal(graph.metadata.semantic_completion,false);
 checks.push('6跨日及18空格来源日期规范，前4/4段不改；5命题7关联4图逐项核验、3后加1原发未核，全64段台账、全书尚未完成');

 const anchor=claim('historical-dense-zone-trapped-holders-turnover-author-explanation').evidence[0].id;
 const requests=[
  ['search',{query:'历史密集区'},['search','历史密集区']],
  ['concept',{id:'历史密集区',limit:20},['concept','历史密集区','--limit','20']],
  ['neighbors',{id:'市场心理',depth:1,limit:100},['neighbors','市场心理','--depth','1','--limit','100']],
  ['evidence',{id:anchor},['evidence',anchor]],
  ['page',{documentId:'volume_1.pdf',page:310},['page','--document-id','volume_1.pdf','--page','310']],
  ['search',{query:'level2',scope:'source',limit:8},['search','level2','--scope','source','--limit','8']],
  ['coverage',{},['coverage']],
 ];
 const parity=[];
 for(const [command,args,argv] of requests){const a=JSON.parse(JSON.stringify(graph.query(command,args)));assert.deepEqual(JSON.parse(JSON.stringify(desktop.query(command,args))),a);const cli=spawnSync(process.execPath,[resolve(agent,'bin/chan-kg.mjs'),...argv,'--kb',root],{encoding:'utf8',maxBuffer:24*1024*1024});assert.equal(cli.status,0,cli.stderr);assert.deepEqual(JSON.parse(cli.stdout),a);parity.push({command,args,cli_matches_shared:true,desktop_module_matches_shared:true});}
 assert.deepEqual({database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
 const report={graph_version:graph.metadata.graph_version,schema_version:graph.metadata.schema_version,checks,parity,intended_figure_links_checked:{claims:5,associations:7,unique_figures:4},core_sha256:sha(resolve(agent,'src/core.mjs')),desktop_core_sha256:sha(resolve(agent,'../chan-kg-desktop/vendor/core.mjs')),database_and_manifest_unchanged:true,pass:true,limits:['同模型范围检查与模块一致性，非独立语义复核或Windows真实离线/PDF交互。','未补完归零买点/跌破/能量耗尽算法，不认证心理疗效、历史持仓成本或后行情预测。']};
 writeFileSync(resolve(agent,'curation/source-audit/stage-c-l042-verification.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({graph_version:report.graph_version,boundary_groups:checks.length,parity:parity.length,figure_links:report.intended_figure_links_checked,pass:true}));
}finally{graph.close();desktop.close();}
