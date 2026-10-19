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
const claim = slug => { const c = graph.getClaim('upper-l047-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try{
 assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l047-c-stage-%' AND review_status='reviewed'").get().n,36);
 assert.equal(claim('small-capital-small-level-only-daily-weekly-hold-separate-stock-chart').conditions.length,1);
 assert.match(claim('small-capital-small-level-only-daily-weekly-hold-separate-stock-chart').text,/较小资金和操作级别.*日线.*周线.*自身图/);
 assert.notEqual(claim('after-third-sell-subminute-down-must-complete-author-100-percent-plan').ambiguity_status,'none');
 assert.match(claim('after-third-sell-subminute-down-must-complete-author-100-percent-plan').review_note,/不是经验胜率/);
 assert.notEqual(claim('first-three-no-overlap-case-excludes-two-day-centers-author-reasoning').ambiguity_status,'none');
 assert.match(claim('first-three-no-overlap-case-excludes-two-day-centers-author-reasoning').review_note,/不当项目已穷举所有8K证明/);
 assert.match(claim('teaching-example-not-all-super-short-one-second-ability-rhetoric').text,/不鼓励所有人做超级短线/);
 checks.push('36新增；案例100%为作者条件内理论措辞非实测胜率/成交保证，排两中枢推理未假称8K穷举已证；小资金小级与日周/个股自身图分开，范本不鼓励所有人超短线');

 assert.match(claim('five-minute-chart-area-below-five-signal-not-axis-return').text,/黄白线未明显回0.*不属5分/);
 assert.match(claim('tick-divergence-one-minute-MACD-bar-length-auxiliary-only').review_note,/不取代45\/46.*看面积/);
 assert.match(claim('two-waves-after-small-third-sell-can-complete-not-necessarily-end').review_note,/可随时完成不等第二波末必已结束/);
 assert.match(claim('after1330-no-stronger-than-before1030-five-minute-area-shenzhen').review_note,/不强于而非必须严格更小/);
 assert.match(claim('strong-rebound-condition-day-balance-center-position-time-not-any-tick').text,/不是任意.*而是该日平衡市/);
 assert.match(claim('minimum-last-rebound-place-not-full-center-return-guarantee').text,/最后一个反弹处.*并不100%保证完全回到中枢/);
 assert.match(claim('future-larger-divergence-or-direct-rise-market-chooses-center-key').text,/更大背驰.*也可直接上行/);
 checks.push('分笔借1分柱长度辅助与两段绿面积不同对象，5分看图非5分信号；三卖后两波可完非必完，不强于非必须更小；强回拉条件在当日平衡位置时间，最后反弹目标不等完整回枢');

 assert.match(claim('strict-five-center-three-one-types-day-center-borrowed-different').text,/5分中枢需三段1分级别走势重合.*只是借用/);
 assert.match(claim('strict-five-center-three-one-types-day-center-borrowed-different').review_note,/至少\/连续/);
 assert.match(claim('tiny-day-overlap-can-ignore-rough-view-ten-points-not-universal').review_note,/不升为所有市场\/严格递归中枢统一最小10点/);
 assert.match(source('0346-b012').text,/最高3892.*最低3688/);assert.match(source('0347-b006').text,/3688到3692/);
 assert.notEqual(claim('source-3892-3688-versus-3688-3692-number-tension').ambiguity_status,'none');
 assert.match(claim('source-3892-3688-versus-3688-3692-number-tension').review_note,/不能单据这两数证明三K共同交集/);
 assert.equal(source('0346-b010').role,'reader');assert.equal(source('0347-b002').role,'reader');
 assert.match(claim('apr23-no-day-center-rise-historical-statement-vs-tiny-overlap').review_note,/前后表述同时保留/);
 checks.push('作者明确分时中枢借用非递归，严格5分三段1分仍联合完整定义；粗忽略几个点不改严格交集或设10点通用门槛，原3892/3688与后3688至3692两句保留，读者引文不冒作者证据');

 assert.match(claim('three-day-gap-rule-not-absolute-large-statistical-concept').text,/不是绝对.*大统计概念/);
 assert.match(claim('three-day-gap-rule-not-absolute-large-statistical-concept').review_note,/没有样本.*自然日还是交易日/);
 assert.match(claim('gap-three-days-unfilled-breakaway-upside-author-conditional').review_note,/不是预定只调整三天/);
 assert.match(claim('five-day-support-gap-explanation-larger-adjustment-for-distant-gap').review_note,/机会不等必补/);
 assert.match(claim('Tplus1-even-3358-may-not-sell-next-day-Tplus0-intraday-exit').text,/第二天仍可能出不掉/);
 assert.match(claim('Tplus1-even-3358-may-not-sell-next-day-Tplus0-intraday-exit').review_note,/不表示全部滑点\/流动性\/停牌或亏损风险消失/);
 assert.match(claim('intraday-hedging-method-promised-not-given').review_note,/未给完整对冲/);
 assert.match(claim('medium-five-week-short-five-day-skills-qualified-following').review_note,/5日线单边非盘整限制/);
 checks.push('三天缺口为非绝对统计说法但无样本，非固定调整倒计时/必补；T+1即低买仍有次日出不掉风险，T+0仅去隔日约束语境非全风险消失，对冲仅预告，5周/5日简法保能力和结构条件');

 const plan=JSON.parse(readFileSync(resolve(agent,'curation/source-audit/stage-c-l047-source-plan.json'),'utf8'));assert.equal(plan.operations.length,19);assert.equal(plan.operations.filter(x=>x.table==='passages').length,13);
 for(const op of plan.operations.filter(x=>x.table==='passages')){assert.equal(source(op.id.split('-p')[1]).published_at,op.after.published_at);assert.equal(op.before.published_at,op.after.published_at.replace(' ',''));}
 const ledger=readFileSync(resolve(agent,'curation/upper/c_stage_l047.coverage.jsonl'),'utf8').trim().split('\n').map(JSON.parse);assert.equal(ledger.length,65);assert.equal(ledger.filter(r=>r.result==='nontechnical-national-equity-market-essay-context').length,6);
 for(const p of ['0344-b001','0344-b002','0344-b003','0344-b004','0344-b005','0345-b000'])assert.equal(graph.db.prepare("SELECT count(*) n FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed' AND e.passage_id=?").get('volume_1-a53e99c37ca5-p'+p).n,0);
 assert.match(claim('historical-3351-BOLL-mid-MA20-and-channel-3358-support').review_note,/原3358不据别图3359.04静改/);
 assert.match(claim('index-external-influence-through-stock-internal-points').review_note,/未逐股验证/);
 checks.push('13来源时间只补空格、原字/身份不改；全民炒股六段经济论述保留上下文不作技术定理，30%/50%非配置建议；3351/3358与后图异值不静改，指标独立性/所有个股结构未外证');

 const links={
  '1330-three-bars-create-day-center-eliminate-zero-center-weak-balance':['0339-b006',['0340-fig1']],
  'five-minute-chart-area-below-five-signal-not-axis-return':['0340-b000',['0341-fig1','0341-fig2']],
  'after1330-no-stronger-than-before1030-five-minute-area-shenzhen':['0341-b000',['0341-fig1','0341-fig2']],
  'actual-1443-tick-divergence-morning-star-large-rebound-case':['0341-b001',['0342-fig1']],
  'historical-3351-BOLL-mid-MA20-and-channel-3358-support':['0342-b001',['0342-fig2','0345-fig1']],
  'gap-three-days-unfilled-breakaway-upside-author-conditional':['0345-b003',['0345-fig1']],
 };
 for(const [slug,[passage,figures]] of Object.entries(links)){const e=claim(slug).evidence.find(e=>e.passage_id==='volume_1-a53e99c37ca5-p'+passage);assert.deepEqual(e.figure_ids,figures.map(f=>'volume_1-a53e99c37ca5-p'+f));assert.equal(e.figures.length,figures.length);}
 assert.match(claim('1330-three-bars-create-day-center-eliminate-zero-center-weak-balance').review_note,/分时背景图不直接展示三根30分K/);
 const figs=graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 339 AND 347").all();assert.equal(figs.length,6);assert.equal(figs.filter(f=>f.origin_status==='later_annotation').length,3);
 assert.equal(graph.db.prepare("SELECT processing_status FROM units WHERE id='lesson-047'").get().processing_status,'semantic_read_with_pending');assert.equal(graph.metadata.semantic_completion,false);
 checks.push('6命题9关联6整图逐项核；上证分时图仅关联日内背景而非5分MACD，3图相对晨文后加/3原发未核，未来行情不证100%强语，未补全书或实际Windows运行');

 const anchor=claim('source-3892-3688-versus-3688-3692-number-tension').evidence.find(e=>e.pdf_page===346).id;
 const requests=[['search',{query:'突破性缺口'},['search','突破性缺口']],['concept',{id:'突破性缺口',limit:20},['concept','突破性缺口','--limit','20']],['neighbors',{id:'每天走势上的中枢',depth:1,limit:100},['neighbors','每天走势上的中枢','--depth','1','--limit','100']],['evidence',{id:anchor},['evidence',anchor]],['page',{documentId:'volume_1.pdf',page:346},['page','--document-id','volume_1.pdf','--page','346']],['search',{query:'3892',scope:'source',limit:8},['search','3892','--scope','source','--limit','8']],['coverage',{},['coverage']]];
 const parity=[];for(const [command,args,argv] of requests){const a=JSON.parse(JSON.stringify(graph.query(command,args)));assert.deepEqual(JSON.parse(JSON.stringify(desktop.query(command,args))),a);const cli=spawnSync(process.execPath,[resolve(agent,'bin/chan-kg.mjs'),...argv,'--kb',root],{encoding:'utf8',maxBuffer:24*1024*1024});assert.equal(cli.status,0,cli.stderr);assert.deepEqual(JSON.parse(cli.stdout),a);parity.push({command,args,cli_matches_shared:true,desktop_module_matches_shared:true});}
 assert.deepEqual({database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
 const report={graph_version:graph.metadata.graph_version,schema_version:graph.metadata.schema_version,checks,parity,intended_figure_links_checked:{claims:6,associations:9,unique_figures:6},core_sha256:sha(resolve(agent,'src/core.mjs')),desktop_core_sha256:sha(resolve(agent,'../chan-kg-desktop/vendor/core.mjs')),database_and_manifest_unchanged:true,pass:true,limits:['同模型范围检查/模块一致，非独立语义或回答质量及Windows实际运行验收。','100%作者理论措辞未作统计实证，日内排两中枢推理未穷举全模型，3892/3692及价格差异未解决、执行和三日统计无完整算法。']};writeFileSync(resolve(agent,'curation/source-audit/stage-c-l047-verification.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({graph_version:report.graph_version,boundary_groups:checks.length,parity:parity.length,figure_links:report.intended_figure_links_checked,pass:true}));
}finally{graph.close();desktop.close();}
