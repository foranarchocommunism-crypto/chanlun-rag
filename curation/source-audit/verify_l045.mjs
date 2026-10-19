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
const claim = slug => { const c = graph.getClaim('upper-l045-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try{
 assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l045-c-stage-%' AND review_status='reviewed'").get().n,41);
 assert.match(claim('fixed-thirty-level-buy-hold-to-sell-cash-to-next-buy').text,/30分买点买入后持股.*卖出，再持币/);
 assert.match(claim('fixed-thirty-level-buy-hold-to-sell-cash-to-next-buy').review_note,/不抹本课其他层级短差或44容量分层/);
 assert.match(claim('waiting-active-monitor-type-growth-and-classification').review_note,/不是盲目忍受/);
 assert.notEqual(claim('theory-guarantees-next-point-author-claim-not-calendar').ambiguity_status,'none');
 assert.match(claim('weakest-example-A1-A2-A3-three-overlapping-five-types').text,/三段重叠5分走势类型A1、A2、A3/);
 assert.match(claim('weakest-example-A1-A2-A3-three-overlapping-five-types').review_note,/非任意三根K/);
 assert.match(claim('thirty-type-minimum-one-thirty-center-can-end-after-formed').review_note,/不等中枢初成当刻必结束/);
 assert.match(claim('classify-possible-structures-observe-current-market-choice').review_note,/未列完首中枢后全部分支/);
 checks.push('41新增；持股/币是固定级别等待且观察当下分类，理论保证非收益/成交保证；三完整5分重叠A1+A2+A3仅最弱可能，首中枢形成可结束非即刻必完，后分支留46');

 assert.equal(source('0322-b007').role,'reader');assert.match(source('0322-b007').text,/持续的时间乘以价格变动范围/);
 assert.match(claim('force-precise-definition-measure-no-rectangle-formula-endorsement').review_note,/没有获明确肯定/);
 assert.match(claim('MACD-bars-area-not-height-shortening-plus-zero-return').text,/面积.*不能只看缩短.*黄白线是否回抽0轴/);
 assert.match(claim('five-day-line-trending-not-consolidation-center-knowledge-replaces').text,/单边走势.*盘整中用处不大/);
 assert.deepEqual(claim('five-day-line-trending-not-consolidation-center-knowledge-replaces').evidence.map(e=>e.pdf_page).sort((a,b)=>a-b),[327,330]);
 assert.match(claim('bull-market-can-sell-large-point-rebuy-not-blind-long').text,/大级别卖点可先卖再买/);
 assert.match(claim('bull-keep-chips-lower-cost-rhythm-not-risk-immunity').review_note,/不等任何买入筹码永久不能卖/);
 checks.push('时间乘价格范围是读者未获认可，作者测度未给公式；MACD面积/回轴不单柱高；5日线两答明确单边非盘整、牛市不丢筹码不等死拿，降本未证明免经济风险');

 assert.match(claim('apr16-no-one-minute-divergence-only-below-minute-consolidation').text,/否认当日有1分背驰.*1分以下盘整背驰/);
 assert.match(claim('subminute-operation-requires-skill-and-1055-1346-three-segments').text,/前提能分清.*10:55至13:46.*三段/);
 assert.match(claim('apr16-no-minute-bottom-required-third-center-leg-complete-can-up').review_note,/不否定更低级可能转向/);
 assert.match(claim('apr17-one-minute-1030-1340-case-and-fallback-misses-spreads').review_note,/没有在文字|并未在文字逐点命名/);
 assert.notEqual(claim('beginner-smaller-level-needs-skill-thirty-minute-95-percent-rhetoric').ambiguity_status,'none');
 assert.match(claim('two-stock-cases-tick-orders-feel-or-small-large-later-exits').review_note,/不得挂600855图/);
 for(const e of claim('two-stock-cases-tick-orders-feel-or-small-large-later-exits').evidence)assert.deepEqual(e.figure_ids,[]);
 assert.equal(source('0328-b011').role,'reader');assert.match(source('0328-b011').text,/三分钟买点/);
 assert.notEqual(claim('reader-1345-third-minute-wording-qualified-can-see-next-open').ambiguity_status,'none');
 assert.match(claim('600855-five-divergence-not-endless-fall-1345-question-refuse-rebuy').review_note,/没在原句明确给13:45点名或建议明后天回买/);
 checks.push('4/16子分钟盘背不升1分、三段识别/技能前提保留；4/17两点未文字命名，95%非评测指标；分笔两股不混600855图，读者三分钟原字与有限认可/作者1345反问不补正式分类或回买建议');

 const ledger=readFileSync(resolve(agent,'curation/upper/c_stage_l045.coverage.jsonl'),'utf8').trim().split('\n').map(JSON.parse);assert.equal(ledger.length,134);
 assert.equal(ledger.filter(r=>r.result==='nontechnical-blog-motivation-and-fee-opinion-context').length,8);
 assert.equal(ledger.filter(r=>r.result==='nontechnical-market-structure-essay-context').length,7);
 for(const p of ['0325-b001','0325-b002','0325-b003','0325-b004','0325-b005','0326-b000','0326-b001','0331-b003','0331-b011'])assert.equal(graph.db.prepare("SELECT count(*) n FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed' AND e.passage_id=?").get('volume_1-a53e99c37ca5-p'+p).n,0);
 for(let i=0;i<=11;i++)assert.equal(source('0331-b'+String(i).padStart(3,'0')).role,'reader');
 assert.match(claim('twenty-year-script-and-2225-text-time-inconsistency').text,/2225/);assert.match(claim('twenty-year-script-and-2225-text-time-inconsistency').review_note,/不擅改2025/);
 assert.match(claim('apr17-data-HK-one-billion-usd-news-author-report-unverified').text,/10亿美元/);
 assert.match(claim('bad-earnings-strength-watch-not-certain-conspiracy-or-buy').review_note,/不认所有亏损股均有预谋/);
 checks.push('八段博客动机/付费观点和七段经济附文只作上下文，331媒体摘录全部读者非作者；2225不静改2025、20年矛盾保留，10亿美元消息/亏损预谋/收益仅历史转述和未核意见');

 const plan=JSON.parse(readFileSync(resolve(agent,'curation/source-audit/stage-c-l045-source-plan.json'),'utf8'));assert.equal(plan.operations.length,49);assert.equal(plan.operations.filter(x=>x.table==='passages').length,45);
 for(const op of plan.operations.filter(x=>x.table==='passages'))assert.equal(source(op.id.split('-p')[1]).published_at,op.after.published_at);
 assert.equal(source('0326-b004').published_at,'2007-04-16 15:25:25');assert.match(source('0326-b004').text,/2007-04-1715:38:56$/);
 for(const p of ['0326-b005','0326-b006','0326-b007','0327-b000','0327-b001','0327-b002'])assert.equal(source(p).published_at,'2007-04-17 15:38:56');
 assert.match(claim('size-limits-compounding-speed-and-point-capacity').review_note,/读者CCTV\/罗锅盈利未核/);
 assert.match(claim('decomposition-previous-lessons-from-divergence-not-all-questions-answered').review_note,/非任意小背驰即时切所有大级/);
 checks.push('六段4/17日期纠正、39时间仅规范空格，前4/16段和尾头原字不改；容量限制不证明读者月翻倍，背驰点分解仍须43/44完成和重合前提，16课读者细问未获逐项答');

 const links={
  'apr17-one-minute-1030-1340-case-and-fallback-misses-spreads':['0326-b005',['0327-fig1']],
  'apr16-no-one-minute-divergence-only-below-minute-consolidation':['0328-b001',['0327-fig1']],
  'apr16-no-minute-bottom-required-third-center-leg-complete-can-up':['0328-b004',['0327-fig1']],
  'reader-1345-third-minute-wording-qualified-can-see-next-open':['0328-b012',['0329-fig1']],
  '600855-five-divergence-not-endless-fall-1345-question-refuse-rebuy':['0329-b002',['0329-fig2','0330-fig1']],
 };
 for(const [slug,[passage,figures]] of Object.entries(links)){const e=claim(slug).evidence.find(e=>e.passage_id==='volume_1-a53e99c37ca5-p'+passage);assert.deepEqual(e.figure_ids,figures.map(f=>'volume_1-a53e99c37ca5-p'+f));assert.equal(e.figures.length,figures.length);}
 const figs=graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 320 AND 331").all();assert.equal(figs.length,4);assert.equal(figs.filter(f=>f.origin_status==='later_annotation').length,3);
 assert.equal(graph.db.prepare("SELECT processing_status FROM units WHERE id='lesson-045'").get().processing_status,'semantic_read_with_pending');assert.equal(graph.metadata.semantic_completion,false);
 checks.push('5命题6关联4整图逐项确认：327含4/18、329两图含4/17后行情，330同日原发未核；图像不替作者点名、未来K不证预测；全书/真实桌面尚未完成');

 const anchor=claim('600855-five-divergence-not-endless-fall-1345-question-refuse-rebuy').evidence.find(e=>e.pdf_page===329).id;
 const requests=[['search',{query:'持币'},['search','持币']],['concept',{id:'等待',limit:20},['concept','等待','--limit','20']],['neighbors',{id:'持币',depth:1,limit:100},['neighbors','持币','--depth','1','--limit','100']],['evidence',{id:anchor},['evidence',anchor]],['page',{documentId:'volume_1.pdf',page:331},['page','--document-id','volume_1.pdf','--page','331']],['search',{query:'GDP',scope:'source',limit:8},['search','GDP','--scope','source','--limit','8']],['coverage',{},['coverage']]];
 const parity=[];for(const [command,args,argv] of requests){const a=JSON.parse(JSON.stringify(graph.query(command,args)));assert.deepEqual(JSON.parse(JSON.stringify(desktop.query(command,args))),a);const cli=spawnSync(process.execPath,[resolve(agent,'bin/chan-kg.mjs'),...argv,'--kb',root],{encoding:'utf8',maxBuffer:24*1024*1024});assert.equal(cli.status,0,cli.stderr);assert.deepEqual(JSON.parse(cli.stdout),a);parity.push({command,args,cli_matches_shared:true,desktop_module_matches_shared:true});}
 assert.deepEqual({database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
 const report={graph_version:graph.metadata.graph_version,schema_version:graph.metadata.schema_version,checks,parity,intended_figure_links_checked:{claims:5,associations:6,unique_figures:4},core_sha256:sha(resolve(agent,'src/core.mjs')),desktop_core_sha256:sha(resolve(agent,'../chan-kg-desktop/vendor/core.mjs')),database_and_manifest_unchanged:true,pass:true,limits:['同模型边界检查及模块一致性，非独立语义/生成回答质量或Windows实际离线/PDF交互。','未给全分类/力度/子分钟交易算法，历史消息/2225/强收益未外核；来源限定固定两册。']};writeFileSync(resolve(agent,'curation/source-audit/stage-c-l045-verification.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({graph_version:report.graph_version,boundary_groups:checks.length,parity:parity.length,figure_links:report.intended_figure_links_checked,pass:true}));
}finally{graph.close();desktop.close();}
