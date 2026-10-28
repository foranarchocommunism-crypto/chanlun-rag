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
const claim = slug => { const c = graph.getClaim('upper-l046-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try{
 assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l046-c-stage-%' AND review_status='reviewed'").get().n,33);
 assert.match(claim('four-hour-eight-thirty-bars-three-adjacent-overlap-day-center').text,/4小时.*8根30分K线.*相邻三根/);
 assert.match(claim('four-hour-eight-thirty-bars-three-adjacent-overlap-day-center').review_note,/不是三完整次级走势类型的严格递归/);
 assert.match(claim('daily-auxiliary-classification-not-strict-level-type-replacement').text,/只是辅助.*暂未接着讲/);
 assert.match(claim('one-center-balanced-first-three-often-one-extreme-not-absolute').text,/一般.*并非完全绝对/);
 assert.match(claim('one-center-balanced-first-three-often-one-extreme-not-absolute').review_note,/不意味着第三根收完即先知/);
 assert.equal(claim('first-three-day-high-weak-balance-close-ranking-not-red-green').conditions.length,2);
 assert.ok(claim('first-three-day-high-weak-balance-close-ranking-not-red-green').evidence.some(e=>e.passage_id.endsWith('0332-b003')));
 assert.ok(claim('first-three-day-low-strong-balance-close-ranking-not-red-green').evidence.some(e=>e.passage_id.endsWith('0332-b005')));
 assert.ok(claim('neither-day-extreme-in-first-three-turning-balance').evidence.some(e=>e.passage_id.endsWith('0332-b007')));
 assert.match(claim('one-day-center-can-be-later-triples-not-first-three').text,/不一定.*前三根.*后面/);
 checks.push('33新增；4小时8K三相邻30分K重叠为日内辅助而非递归中枢，45未完分类仍未接；一中枢前三极值非绝对/先知，强弱转折各带标题证据，中枢可来自后K，双极值/等值不补规则');

 assert.match(claim('unilateral-interval-between-two-centers-and-bar-belongs-neither').text,/部分区间.*不从属任一/);
 assert.equal(claim('eight-bars-unilateral-interval-fourth-or-fifth-midday-half-hour').conditions.length,2);
 assert.match(claim('fourth-and-fifth-both-possible-fourth-only-eighth-can-cross').text,/同时.*可能穿越/);
 assert.notEqual(claim('fourth-and-fifth-both-possible-fourth-only-eighth-can-cross').ambiguity_status,'none');
 assert.match(claim('zero-center-no-adjacent-triple-common-overlap-strong-day').review_note,/不是每两根也必须无交叠/);
 assert.match(claim('zero-center-not-guaranteed-continuation-large-daily-center-fake-risk').text,/不保证趋势延续/);
 assert.match(claim('zero-center-after-third-point-large-strong-trend-more-likely-not-certain').review_note,/不是充分保证/);
 checks.push('两中枢不重合/单边K归属、第4第5可同时及第8可能穿越限8K模型；原200070417不静改；无日内中枢指三K共同重叠而非任意两K，强日不保续，第三类点后也仅大概率观点');

 assert.match(claim('center-oscillation-two-intervals-green-area-earlier-stronger').text,/17日14:53至18日10:01与18日13:35至14:16.*前段绿柱面积大/);
 assert.match(claim('center-oscillation-two-intervals-green-area-earlier-stronger').review_note,/不是单柱放长/);
 assert.equal(source('0337-b003').role,'reader');
 assert.match(claim('ABC-first-two-exist-C-can-rise-directly-not-next-day-forecast').review_note,/未答读者尾盘满仓明日安全/);
 assert.match(claim('five-minute-no-yellow-white-return-not-five-divergence-below-five').text,/没回轴就不是5分背驰.*5分以下/);
 assert.match(claim('five-minute-no-yellow-white-return-not-five-divergence-below-five').review_note,/不把一定以下直接当所有未回轴走势均有下级背驰/);
 checks.push('中枢震荡比两完整同向跨日区间绿面积，读者单柱放长误解不作公式；ABC可直接上非次日安全预测，5分看图无回轴不升5分信号，仅此例更低级且比较对象未补全');

 assert.match(claim('completion-is-form-not-amplitude-not-auto-confirm-B-from-strength').text,/形态.*幅度无关/);
 assert.match(claim('completion-is-form-not-amplitude-not-auto-confirm-B-from-strength').review_note,/不由涨得强就认B已完/);
 assert.equal(claim('qualified-same-level-separation-at-small-divergence-followup').evidence[0].quote,'这说过了，就是这样分解的。');
 assert.match(claim('subsub-retest-makes-sublevel-third-point-earlier-can-act').review_note,/不把较小点升级成30分严格三买/);
 assert.match(claim('offset-rhythm-stock-pool-one-at-a-time-max-two').text,/每次只操作一只、最多两只/);
 assert.match(claim('weak-skill-below-five-day-cash-unless-clear-larger-divergence').text,/除非.*较大级背驰.*否则持币/);
 assert.match(claim('bad-market-larger-level-or-late-buy-point-Tplus1').review_note,/等尾盘仍须买点/);
 assert.notEqual(claim('Tplus1-consider-real-five-divergence-big-fall-small-capital-view').ambiguity_status,'none');
 assert.match(claim('600855-afternoon-buy-except-larger-point-unclear-trend').review_note,/未预测该股明日是否继续下调/);
 checks.push('完成形态非幅度、较小第三类点较早不等B严格完成；转引提问排除作者引文；股票池每次1最多2、弱技术5日破持币带较大背驰例外，大盘/T+1/小资金/下午仍须点联合，不保本或答个人预测');

 const plan=JSON.parse(readFileSync(resolve(agent,'curation/source-audit/stage-c-l046-source-plan.json'),'utf8'));assert.equal(plan.operations.length,33);assert.equal(plan.operations.filter(x=>x.table==='passages').length,27);
 for(const op of plan.operations.filter(x=>x.table==='passages'))assert.equal(source(op.id.split('-p')[1]).published_at,op.after.published_at);
 assert.equal(source('0335-b002').published_at,'2007-04-18 15:38:33');assert.match(source('0335-b002').text,/2007-04-1915:37:29$/);
 for(const p of ['0335-b003','0335-b004','0336-b000','0336-b001'])assert.equal(source(p).published_at,'2007-04-19 15:37:29');
 for(const p of ['0334-b002','0335-b000','0335-b001'])assert.equal(graph.db.prepare("SELECT count(*) n FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed' AND e.passage_id=?").get('volume_1-a53e99c37ca5-p'+p).n,0);
 assert.notEqual(claim('apr18-fourteen-stock-average-double-self-report-not-performance-gate').ambiguity_status,'none');
 assert.match(claim('apr18-strong-balanced-next-day-third-buy-or-extension-five-day-risk').text,/至少会出现盘整级别延伸.*可能增/);
 assert.match(claim('apr19-1030-1330-three-bars-3520-watch-recross-and-market-choice').text,/上穿并站稳/);
 checks.push('4段4/19与23时间空格规范、前4/18及尾头不改；数据延后/基金指控仅上下文，14只100%涨幅非个人实盘或评测门槛；条件至少会延伸与破线可能不同强度，3520例非通用阈值');

 const links={
  'one-center-balanced-first-three-often-one-extreme-not-absolute':['0332-b001',['0332-fig1']],
  'first-three-day-high-weak-balance-close-ranking-not-red-green':['0332-b003',['0332-fig1']],
  'first-three-day-low-strong-balance-close-ranking-not-red-green':['0332-b005',['0332-fig1']],
  'neither-day-extreme-in-first-three-turning-balance':['0332-b007',['0332-fig1']],
  'unilateral-interval-between-two-centers-and-bar-belongs-neither':['0333-b000',['0333-fig1']],
  'eight-bars-unilateral-interval-fourth-or-fifth-midday-half-hour':['0333-b001',['0333-fig1']],
  'fourth-and-fifth-both-possible-fourth-only-eighth-can-cross':['0333-b002',['0333-fig1']],
  'zero-center-no-adjacent-triple-common-overlap-strong-day':['0333-b004',['0334-fig1']],
  'zero-center-not-guaranteed-continuation-large-daily-center-fake-risk':['0333-b005',['0334-fig1']],
  'apr18-strong-balanced-next-day-third-buy-or-extension-five-day-risk':['0334-b001',['0334-fig2']],
  'apr19-five-day-break-1108-third-sell-reaction-rebuy-opportunity':['0335-b003',['0334-fig2','0335-fig1']],
  'apr19-1030-1330-three-bars-3520-watch-recross-and-market-choice':['0335-b004',['0335-fig1']],
  'center-oscillation-two-intervals-green-area-earlier-stronger':['0337-b001',['0336-fig1']],
 };
 for(const [slug,[passage,figures]] of Object.entries(links)){const e=claim(slug).evidence.find(e=>e.passage_id==='volume_1-a53e99c37ca5-p'+passage);assert.deepEqual(e.figure_ids,figures.map(f=>'volume_1-a53e99c37ca5-p'+f));assert.equal(e.figures.length,figures.length);}
 const figs=graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 331 AND 339").all();assert.equal(figs.length,6);assert.equal(figs.filter(f=>f.origin_status==='later_annotation').length,4);
 const ledger=readFileSync(resolve(agent,'curation/upper/c_stage_l046.coverage.jsonl'),'utf8').trim().split('\n').map(JSON.parse);assert.equal(ledger.length,86);
 assert.equal(graph.db.prepare("SELECT processing_status FROM units WHERE id='lesson-046'").get().processing_status,'semantic_read_with_pending');assert.equal(graph.metadata.semantic_completion,false);
 checks.push('86段台账、13命题14关联6整图逐项核：3讲义2008署期和334后K为4后加，335/336同日原发未核；后图不证预测/作者原图，不补全全书/真实Windows验收');

 const anchor=claim('center-oscillation-two-intervals-green-area-earlier-stronger').evidence.find(e=>e.passage_id.endsWith('0337-b004')).id;
 const requests=[['search',{query:'单边区间'},['search','单边区间']],['concept',{id:'每天走势上的中枢',limit:20},['concept','每天走势上的中枢','--limit','20']],['neighbors',{id:'每日走势分类',depth:1,limit:100},['neighbors','每日走势分类','--depth','1','--limit','100']],['evidence',{id:anchor},['evidence',anchor]],['page',{documentId:'volume_1.pdf',page:332},['page','--document-id','volume_1.pdf','--page','332']],['search',{query:'GDP',scope:'source',limit:8},['search','GDP','--scope','source','--limit','8']],['coverage',{},['coverage']]];
 const parity=[];for(const [command,args,argv] of requests){const a=JSON.parse(JSON.stringify(graph.query(command,args)));assert.deepEqual(JSON.parse(JSON.stringify(desktop.query(command,args))),a);const cli=spawnSync(process.execPath,[resolve(agent,'bin/chan-kg.mjs'),...argv,'--kb',root],{encoding:'utf8',maxBuffer:24*1024*1024});assert.equal(cli.status,0,cli.stderr);assert.deepEqual(JSON.parse(cli.stdout),a);parity.push({command,args,cli_matches_shared:true,desktop_module_matches_shared:true});}
 assert.deepEqual({database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
 const report={graph_version:graph.metadata.graph_version,schema_version:graph.metadata.schema_version,checks,parity,intended_figure_links_checked:{claims:13,associations:14,unique_figures:6},core_sha256:sha(resolve(agent,'src/core.mjs')),desktop_core_sha256:sha(resolve(agent,'../chan-kg-desktop/vendor/core.mjs')),database_and_manifest_unchanged:true,pass:true,limits:['同模型范围复核及模块一致性，非独立语义/回答质量或Windows实际离线/PDF交互。','日内辅助模型不替递归，双极值/等值/包含/多组三K归属未补全部算法；历史基金/收益/制度语境不作当前事实。']};writeFileSync(resolve(agent,'curation/source-audit/stage-c-l046-verification.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({graph_version:report.graph_version,boundary_groups:checks.length,parity:parity.length,figure_links:report.intended_figure_links_checked,pass:true}));
}finally{graph.close();desktop.close();}
