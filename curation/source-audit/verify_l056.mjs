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
const claim = slug => { const c = graph.getClaim('upper-l056-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try {
 assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l056-c-stage-%' AND review_status='reviewed'").get().n,28);
 assert.match(claim('index-second-sell-not-individual-same-kind-weak-stock-third-0948').text,/9点48.*个股可能三卖.*不等个股也二卖/);assert.match(source('0420-b002').text,/05300947/);
 const shock=claim('may29-divergence-leg-unconfirmed-before-gap-first-sell-unavailable');assert.equal(shock.conditions.length,2);assert.notEqual(shock.ambiguity_status,'none');assert.match(shock.text,/进入背驰段.*尚不能确认.*一卖已不可能实操/);
 assert.match(source('0422-b004').text,/2007-05-3022:49:10/);assert.match(source('0422-b005').text,/昨天这530/);
 assert.match(claim('may29-divergence-leg-unconfirmed-before-gap-first-sell-unavailable').review_note,/不证明T\+1\/跌停\/通道\/容量/);
 checks.push('28新增；9点48与55原09:47分开，指数二卖不等弱股二卖；5/29进入段未确认不回看造一卖可成交，突发低开后改二三卖仍非每账户执行证明；标题5/30与昨天530张力不修');

 assert.match(claim('gap-and-subminute-at-same-coarse-view-not-global-identical-level').review_note,/不等原始成交数据中所有细级都严格相等/);
 assert.match(claim('B-three-apparent-centers-not-complete-sloping-third-within-second').text,/第三段仍向下倾斜.*第二向下段一部分.*不能当中枢完成/);
 assert.match(claim('gap-down-first-leg-A-up-second-sell-forming-not-already-complete').text,/只是.*形成中/);
 assert.match(claim('A-internal-structure-confirm-no-new-high-or-consolidation-top').review_note,/未将而\/或擅重写为唯一布尔公式/);
 assert.match(claim('choose-one-lowest-standard-ignore-below-can-change-between-charts').text,/同图标准须统一/);
 assert.notEqual(claim('MACD-top-bottom-shortest-dozens-bars-statistical-suggestion-not-fixed-minimum').ambiguity_status,'none');assert.match(claim('MACD-top-bottom-shortest-dozens-bars-statistical-suggestion-not-fixed-minimum').review_note,/不补固定30根/);
 checks.push('统一最低观察下缺口/细层线段化非原始细级严格相等，B视觉三枢未完成/A二卖形成中不等已完成；一图标准统一，换视角声明范围，几十K为可统计估计而非所有走势最短时长定理');

 const area=claim('B-vs-gap-green-area-include-three-small-not-greater-literal');assert.match(area.text,/前三小绿柱.*不大过/);assert.notEqual(area.ambiguity_status,'none');assert.match(area.review_note,/不擅改严格小于/);
 assert.match(claim('A-up-down-up-upward-leg-volume-or-green-red-absolute-height-aids').text,/第二段向上.*绿柱.*红柱绝对值/);assert.match(claim('C-high-column-height-qualitative-not-B-area-method').text,/柱高度.*一高一矮/);
 assert.match(claim('subminute-compare-area-one-minute-also-zero-axis-lines').text,/若为1分级.*黄白线回抽0轴/);
 assert.match(claim('B-inner-small-to-large-C-not-reach-last-inner-rebound-start').text,/B末向下无该内部级背驰.*更小转大/);assert.match(claim('B-consolidation-divergence-return-above-first-green-not-all-inner-start').review_note,/第一箭头不是B内部最后一次反弹起点/);
 assert.match(claim('B-growing-green-areas-wait-break-A-low-before-gap-comparison').text,/最后跌破A低/);
 checks.push('A跨色绝对大小/B含前三绿的面积/C柱高三量不混，不大过保原量词不补严格小于；1分以下与1分零轴辅助范围不同，外B盘背不强制内末段同级背，回第一箭头不等必回最后内反弹起点');

 const trade=claim('rebound-participation-level-stock-cost-futures-hypothetical-T0-literal');assert.match(source('0424-b001').text,/但由于T\+0/);assert.match(trade.text,/股指期货有约100点.*原连接处写T\+0/);assert.notEqual(trade.ambiguity_status,'none');assert.match(trade.review_note,/不私改T\+1/);
 assert.match(claim('ABC-overlap-one-center-4087-4122-current-reference').text,/4087—4122/);assert.match(claim('may31-original-one-center-expands-five-4015-4122-original-kuozhang').text,/扩张.*4015—4122/);
 const newCenter=claim('new-five-center-starts-yesterday-C-other-decomposition-allowed');assert.match(newCenter.text,/昨日C为第一段/);assert.match(newCenter.review_note,/未明确认可读者所报区间.*一定正确/);
 assert.equal(source('0426-b012').role,'reader');assert.match(source('0426-b012').text,/4027-4077/);
 assert.match(claim('may31-three-down-legs-vs-B-inner-divergence-nesting-1002').text,/10:02低点/);
 checks.push('T+0原字不修T+1，期指100点是如果场景非当年产品制度/实赚证明；1分4087-4122与原扩张5分4015-4122各保，C新分解首段不等读者4027-4077获认可，10:02是案例定位非买入成交保证');

 assert.match(claim('late-rotation-dont-sell-weak-chase-risen-strong-reset-rhythm').text,/已涨才杀三线追一线.*节奏不对/);assert.match(claim('master-one-before-precise-sector-jumping-skilled-goal').text,/无此技术先做好一只/);
 assert.match(claim('S-ST-two-limit-down-comparison-rebound-space-author-case').review_note,/非精确复利等式\/当前涨跌停规则/);
 for(const p of ['0426-b003','0426-b007','0426-b008','0426-b012','0427-b000','0427-b004','0427-b007']){assert.equal(source(p).role,'reader');assert.equal(graph.db.prepare("SELECT count(*) n FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed' AND e.passage_id=?").get('volume_1-a53e99c37ca5-p'+p).n,0);}
 assert.match(claim('half-line-middle-of-shock-still-at-least-three-months-influence').review_note,/至少影响期非所有月线三月后确认有效/);
 checks.push('节奏差不追涨换股、轮动准点只是技术目标，读者短差/S-ST账户/另一枢界/最低时间问题没冒作者事实；S-ST比例是历史粗略比较非当前规则，1/2线影响期与月线确认期不同，预测/盈利强语不实证');

 const links={
 'index-second-sell-not-individual-same-kind-weak-stock-third-0948':['0422-b006','0423-fig1'],
 'may29-divergence-leg-unconfirmed-before-gap-first-sell-unavailable':['0422-b007','0423-fig1'],
 'gap-and-subminute-at-same-coarse-view-not-global-identical-level':['0422-b008','0423-fig1'],
 'B-three-apparent-centers-not-complete-sloping-third-within-second':['0422-b008','0423-fig1'],
 'gap-down-first-leg-A-up-second-sell-forming-not-already-complete':['0422-b009','0423-fig1'],
 'A-internal-structure-confirm-no-new-high-or-consolidation-top':['0423-b000','0423-fig1'],
 'A-up-down-up-upward-leg-volume-or-green-red-absolute-height-aids':['0423-b000','0423-fig1'],
 'B-vs-gap-green-area-include-three-small-not-greater-literal':['0423-b001','0423-fig1'],
 'B-consolidation-divergence-return-above-first-green-not-all-inner-start':['0423-b001','0424-fig1'],
 'C-high-column-height-qualitative-not-B-area-method':['0423-b001','0424-fig1'],
 'ABC-overlap-one-center-4087-4122-current-reference':['0423-b001','0424-fig1'],
 'B-inner-small-to-large-C-not-reach-last-inner-rebound-start':['0423-b002','0424-fig1'],
 'may31-early-rise-below-4087-third-sell':['0424-b002','0425-fig1'],
 'may31-three-down-legs-vs-B-inner-divergence-nesting-1002':['0424-b002','0425-fig1'],
 'may31-original-one-center-expands-five-4015-4122-original-kuozhang':['0424-b003','0425-fig1'],
 'half-line-middle-of-shock-still-at-least-three-months-influence':['0424-b004','0425-fig2'],
 };
 for(const [slug,[p,f]] of Object.entries(links)){const es=claim(slug).evidence;const e=es.find(e=>e.passage_id==='volume_1-a53e99c37ca5-p'+p);assert.deepEqual(e.figure_ids,['volume_1-a53e99c37ca5-p'+f]);assert.equal(e.figures.length,1);for(const other of es)if(other!==e)assert.deepEqual(other.figure_ids,[]);}
 const figs=graph.db.prepare("SELECT id,origin_status,note FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 422 AND 427").all();assert.equal(figs.length,4);assert.equal(figs.filter(f=>f.origin_status==='unverified').length,2);assert.equal(figs.filter(f=>f.origin_status==='later_annotation').length,2);
 assert.match(figs.find(f=>f.id.endsWith('0423-fig1')).note,/24,52,9/);assert.match(figs.find(f=>f.id.endsWith('0424-fig1')).note,/12,26,9/);assert.match(figs.find(f=>f.id.endsWith('0425-fig2')).note,/2011\/08\/18/);assert.match(figs.find(f=>f.id.endsWith('0425-fig2')).note,/2007\/9/);
 const plan=JSON.parse(readFileSync(resolve(agent,'curation/source-audit/stage-c-l056-source-plan.json'),'utf8'));assert.equal(plan.operations.length,18);const pops=plan.operations.filter(op=>op.table==='passages');assert.equal(pops.length,14);for(const op of pops){assert.deepEqual(Object.keys(op.after),['published_at']);assert.equal(op.before.published_at,op.after.published_at.replace(' ',''));assert.equal(source(op.id.split('-p')[1]).published_at,op.after.published_at);}
 const ledger=readFileSync(resolve(agent,'curation/upper/c_stage_l056.coverage.jsonl'),'utf8').trim().split('\n').map(JSON.parse);assert.equal(ledger.length,48);assert.equal(new Set(ledger.map(p=>p.passage_id)).size,48);assert.equal(graph.metadata.semantic_completion,false);
 checks.push('16命题16关联4图逐项核，2未核2后加；原样24/52/9与重绘12/26/9、后日线头2011/轴2007/9不混，后K不证前日预测/数值；14时间空格4图元数据授权变化、48段全台账不等全书或Windows验收');

 const anchor=trade.evidence[0].id;
 const requests=[['search',{query:'不大过'},['search','不大过']],['concept',{id:'最低级别',limit:20},['concept','最低级别','--limit','20']],['neighbors',{id:'跌停',depth:1,limit:100},['neighbors','跌停','--depth','1','--limit','100']],['evidence',{id:anchor},['evidence',anchor]],['page',{documentId:'volume_1.pdf',page:423},['page','--document-id','volume_1.pdf','--page','423']],['search',{query:'但由于T+0',scope:'source',limit:8},['search','但由于T+0','--scope','source','--limit','8']],['coverage',{},['coverage']]];
 const parity=[];for(const [command,args,argv] of requests){const a=JSON.parse(JSON.stringify(graph.query(command,args)));assert.deepEqual(JSON.parse(JSON.stringify(desktop.query(command,args))),a);const cli=spawnSync(process.execPath,[resolve(agent,'bin/chan-kg.mjs'),...argv,'--kb',root],{encoding:'utf8',maxBuffer:24*1024*1024});assert.equal(cli.status,0,cli.stderr);assert.deepEqual(JSON.parse(cli.stdout),a);parity.push({command,args,cli_matches_shared:true,desktop_module_matches_shared:true});}
 assert.deepEqual({database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
 const report={graph_version:graph.metadata.graph_version,schema_version:graph.metadata.schema_version,checks,parity,intended_figure_links_checked:{claims:16,associations:16,unique_figures:4},core_sha256:sha(resolve(agent,'src/core.mjs')),desktop_core_sha256:sha(resolve(agent,'../chan-kg-desktop/vendor/core.mjs')),database_and_manifest_unchanged:true,pass:true,limits:['同模型语义边界/来源和模块一致检查，不是独立或人类金标准/真实Windows交付运行。','T+0/不大过/标题昨天/09:47-9点48原字、MACD参数/比较量及小转大/实时完成/执行保证范围仍待核。','后图非当时预测证明；跨页编号context未修，冻结召回回归/完整G及产品交付未完成。']};
 writeFileSync(resolve(agent,'curation/source-audit/stage-c-l056-verification.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({graph_version:report.graph_version,boundary_groups:checks.length,parity:parity.length,figure_links:report.intended_figure_links_checked,pass:true}));
}finally{graph.close();desktop.close();}
