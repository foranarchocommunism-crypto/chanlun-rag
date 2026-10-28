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
const claim = slug => { const c = graph.getClaim('upper-l044-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try{
 assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l044-c-stage-%' AND review_status='reviewed'").get().n,33);
 assert.match(claim('small-top-large-down-necessary-last-subcenter-third-sell').text,/必要条件.*最后一个次级别中枢.*第三类卖点/);
 assert.match(claim('small-bottom-large-up-necessary-last-subcenter-third-buy').text,/最后一个次级别中枢.*第三类买点.*必要条件/);
 assert.match(claim('necessary-not-sufficient-third-sell-not-guaranteed-return-B').text,/只有必要条件，没有充分条件.*不保证.*必回30分B/);
 assert.match(claim('one-minute-top-after-last-five-center-pulls-back-around-it').review_note,/这是回c`，不是.*保证回30分B/);
 assert.match(claim('normal-last-subcenter-oscillation-not-large-turn').review_note,/不意味着三卖单独足够/);
 checks.push('33新增；小背驰-大转折末个次级中枢三卖/三买为必要非充分，回c`非必回B，正常震荡不转大、破坏后仍不能据此断定大转折');

 assert.match(claim('five-down-not-back-to-third-buy-retest-type-high-ignore').text,/5分向下走势类型高点/);
 assert.match(claim('five-down-not-back-to-third-buy-retest-type-high-ignore').review_note,/不由习作蓝2\/GG自动替换/);
 assert.match(claim('break-five-retest-type-high-exit-on-any-up-rebound').text,/跌破.*此后任何向上回抽/);
 assert.match(claim('break-five-retest-type-high-exit-on-any-up-rebound').review_note,/不变破位即杀跌/);
 assert.match(claim('strongest-pullback-not-touch-last-five-center-in-up-five-containing-buy').review_note,/未静改成任意次次级中枢/);
 assert.match(claim('example-smaller-top-first-at-least-five-minute-down-move').review_note,/不孤立泛成任意市场1分顶背驰/);
 assert.match(graph.getClaim('upper-l043-c-stage-one-minute-top-at-least-one-consolidation-or-down-may-rise-again').text,/盘整.*继续上涨/);
 checks.push('本例5分回试类型高点保完整嵌套，不换GG或30分中枢上沿；先破再向上回抽退出，相等/完成未补，强势嵌套原词保留；本例5分下行与43一般1分盘整作用域区分');

 assert.equal(claim('actual-same-level-top-own-operation-full-exit-versus-small-complexity').conditions.length,2);
 assert.match(claim('many-chips-part-at-last-five-center-third-sell-then-clear-on-boundary').review_note,/没有给部分的固定比例/);
 assert.match(claim('thirty-minute-not-all-out-at-every-one-minute-top').text,/不能见任意1分顶背驰就全抛/);
 assert.match(claim('larger-capital-part-at-one-minute-then-follow-rebuy-or-more-exit').text,/可先出部分.*回补或继续出/);
 assert.notEqual(claim('larger-capital-part-at-one-minute-then-follow-rebuy-or-more-exit').ambiguity_status,'none');
 assert.match(claim('bottom-case-reverse-program-author-instruction-not-complete-algorithm').review_note,/未逐项写底部/);
 checks.push('同级实际背驰且本级操作先给可全仓情境，容量较大末小中枢三卖/更小顶背可分批而非任意小点全抛；部分比例/成交未定义，底反向为作者概述非完整代码算法');

 assert.equal(source('0319-b010').role,'reader');assert.match(source('0319-b010').text,/5.10.10/);
 assert.match(claim('want-faster-five-minute-but-not-unskilled-parameter-unendorsed').review_note,/作者改级不等修改指标参数/);
 assert.match(claim('one-minute-operation-if-capital-and-precision-procedure-same-levels-different').text,/资金量和精度/);
 assert.match(claim('correct-operation-before-better-results-focus-repeat-selected-stocks').review_note,/不能以当天别股涨停反证本股操作错/);
 assert.match(claim('one-minute-just-example-five-and-subminute-same-principle').review_note,/不把5分小背驰与30分同级背驰必回B.*混为/);
 checks.push('MACD5.10.10是读者未获认可，改操作级别有熟练/容量精度前提；过程正确与结果更好分层，1分仅例可推广5分或以下而不抹同级与小级两支');

 assert.match(claim('switch-after-top-divergence-and-confirmed-intraday-stability').review_note,/没有明说站稳对象/);
 assert.match(claim('fall-not-necessarily-bears-bulls-can-wash-case').review_note,/不反向认证每次下跌必多头/);
 assert.notEqual(claim('apr11-only-policy-stop-and-half-position-author-risk-view').ambiguity_status,'none');
 assert.notEqual(claim('twenty-year-bull-three-months-twenty-PE-author-strong-reassurance').ambiguity_status,'none');
 assert.match(claim('twenty-year-bull-three-months-twenty-PE-author-strong-reassurance').review_note,/未点明20倍就对应000912/);
 const plan=JSON.parse(readFileSync(resolve(agent,'curation/source-audit/stage-c-l044-source-plan.json'),'utf8'));assert.equal(plan.operations.length,17);assert.equal(plan.operations.filter(x=>x.table==='passages').length,15);
 for(const op of plan.operations.filter(x=>x.table==='passages'))assert.equal(source(op.id.split('-p')[1]).published_at,op.after.published_at);
 assert.equal(source('0318-b005').published_at,'2007-04-10 15:25:20');assert.match(source('0318-b005').text,/2007-04-1115:38:12$/);
 for(const p of ['0318-b006','0319-b000','0319-b001'])assert.equal(source(p).published_at,'2007-04-11 15:38:12');
 checks.push('换股站稳对象未明、跌不必空方不等必多头、政策唯一风险/半仓/二线必启/20年牛市为历史意见，未静配000912至20倍；3跨日和12空格规范、前段及尾头不改');

 const links={
  'five-down-not-back-to-third-buy-retest-type-high-ignore':['0317-b001',['0317-fig1','0318-fig1']],
  'strongest-pullback-not-touch-last-five-center-in-up-five-containing-buy':['0317-b001',['0317-fig1']],
  'break-five-retest-type-high-exit-on-any-up-rebound':['0317-b001',['0317-fig1','0318-fig1']],
  'many-chips-part-at-last-five-center-third-sell-then-clear-on-boundary':['0317-b002',['0318-fig1']],
 };
 for(const [slug,[passage,figures]] of Object.entries(links)){const e=claim(slug).evidence.find(e=>e.passage_id==='volume_1-a53e99c37ca5-p'+passage);assert.deepEqual(e.figure_ids,figures.map(f=>'volume_1-a53e99c37ca5-p'+f));assert.equal(e.figures.length,figures.length);}
 const figs=graph.db.prepare("SELECT origin_status,note FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 316 AND 320").all();assert.equal(figs.length,2);for(const f of figs){assert.equal(f.origin_status,'later_annotation');assert.match(f.note,/张大山习作/);}
 const ledger=readFileSync(resolve(agent,'curation/upper/c_stage_l044.coverage.jsonl'),'utf8').trim().split('\n').map(JSON.parse);assert.equal(ledger.length,47);
 assert.equal(graph.db.prepare("SELECT processing_status FROM units WHERE id='lesson-044'").get().processing_status,'semantic_read_with_pending');assert.equal(graph.metadata.semantic_completion,false);
 checks.push('47全段台账、4命题6配图关联逐项核，两图署张大山习作按后加学习者图保存；GG/蓝线非作者新增定义，未补全全书/真实桌面验收');

 const anchor=claim('break-five-retest-type-high-exit-on-any-up-rebound').evidence[0].id;
 const requests=[
  ['search',{query:'小背驰 大转折'},['search','小背驰 大转折']],
  ['concept',{id:'缠中说禅小背驰-大转折定理',limit:20},['concept','缠中说禅小背驰-大转折定理','--limit','20']],
  ['neighbors',{id:'交易容量',depth:1,limit:100},['neighbors','交易容量','--depth','1','--limit','100']],
  ['evidence',{id:anchor},['evidence',anchor]],
  ['page',{documentId:'volume_1.pdf',page:317},['page','--document-id','volume_1.pdf','--page','317']],
  ['search',{query:'5.10.10',scope:'source',limit:8},['search','5.10.10','--scope','source','--limit','8']],
  ['coverage',{},['coverage']],
 ];
 const parity=[];
 for(const [command,args,argv] of requests){const a=JSON.parse(JSON.stringify(graph.query(command,args)));assert.deepEqual(JSON.parse(JSON.stringify(desktop.query(command,args))),a);const cli=spawnSync(process.execPath,[resolve(agent,'bin/chan-kg.mjs'),...argv,'--kb',root],{encoding:'utf8',maxBuffer:24*1024*1024});assert.equal(cli.status,0,cli.stderr);assert.deepEqual(JSON.parse(cli.stdout),a);parity.push({command,args,cli_matches_shared:true,desktop_module_matches_shared:true});}
 assert.deepEqual({database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
 const report={graph_version:graph.metadata.graph_version,schema_version:graph.metadata.schema_version,checks,parity,intended_figure_links_checked:{claims:4,associations:6,unique_figures:2},core_sha256:sha(resolve(agent,'src/core.mjs')),desktop_core_sha256:sha(resolve(agent,'../chan-kg-desktop/vendor/core.mjs')),database_and_manifest_unchanged:true,pass:true,limits:['同模型边界检查及模块一致性，非独立语义审查或Windows实际运行/PDF交互。','未补全嵌套阈值所有相等/确认/比例/底部镜像/成交；学习者图不作作者定义，历史强收益和20年牛市未实证。']};
 writeFileSync(resolve(agent,'curation/source-audit/stage-c-l044-verification.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({graph_version:report.graph_version,boundary_groups:checks.length,parity:parity.length,figure_links:report.intended_figure_links_checked,pass:true}));
}finally{graph.close();desktop.close();}
