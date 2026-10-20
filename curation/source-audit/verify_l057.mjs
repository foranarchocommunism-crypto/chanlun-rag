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
const claim = slug => { const c = graph.getClaim('upper-l057-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try {
 assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l057-c-stage-%' AND review_status='reviewed'").get().n,35);
 const coarse=claim('minimum-analysis-view-three-subsegments-overlap-not-final-segment-definition');assert.notEqual(coarse.ambiguity_status,'none');assert.equal(coarse.conditions.length,2);assert.match(coarse.review_note,/不是|非后来特征序列线段定义/);
 assert.match(claim('gap01-and-complex23-real-levels-differ-coarse-one-view-same-lines').text,/01缺口比复杂23真实级别低/);
 const precise=claim('precise45-leave56-retest-sublevel-not-all-below-one-4077-third-sell');assert.match(precise.text,/不能把所有1分以下笼统作直接次级/);assert.equal(precise.conditions.length,2);assert.match(precise.text,/4077.*三卖/);
 assert.match(claim('ten-segments-weak-third-not-recognized-consistent-alternative-standard').text,/同等弱处须全图统一处理/);
 assert.match(claim('at0930-no-future-segments-same-standard-through-time').text,/9:30尚无后续线段/);
 checks.push('35新增；最小分析粗视角全部以下线段化与精确次级离返不同，缺口真实比23更低不强合原级；45/56完整次级才判4077三卖，弱段另类标准须全图一致，9:30无未来段不回看改规则，线段比喻非后特征序列定义');

 assert.match(claim('fine56-up-up-area-divergence-needs-skill-reaction-channel').text,/熟练、反应和通道都快/);
 assert.match(claim('67-down-up-down-later-weaker-time-for-space-zero-green-retrace').text,/幅度小但时间长.*时间换空间.*绿柱回0/);
 assert.match(claim('67-down-up-down-later-weaker-time-for-space-zero-green-retrace').review_note,/不能用绿柱回0单独等同.*黄白线回0/);
 assert.match(claim('at6-alternate-center345456-23-vs67-oscillation-return-near').text,/34、45、56.*23与67.*附近/);assert.match(claim('at6-alternate-center345456-23-vs67-oscillation-return-near').review_note,/不硬套旧边界/);
 assert.match(claim('if7-first-buy-9-second-no-low-or-consolidation-divergence').text,/若把点7当一买.*不新低或盘背.*更低级/);
 assert.match(claim('ten-lines-group-nine-after-gap-five-center4015-4122').text,/\(12\+23\+34\)\+\(45\+56\+67\)\+\(78\+89\+910\).*4015—4122/);assert.match(claim('ten-lines-group-nine-after-gap-five-center4015-4122').review_note,/01缺口之后九段/);
 checks.push('精细56须技艺反应通道三条件；67幅小但时长/绿柱回0不可忽略亦非黄白0轴；另一34-45-56枢不硬套原边界，回附近/若7一买/不新低或盘背/内部更低级均保，5分三组九段不说十段裸相交');

 assert.match(claim('novice-not-full-position-trade-base-longer-part-practice').text,/不应全仓.*部分仓位练习/);
 assert.notEqual(claim('thirty-third-buy-center-up-no-new-center-hold-huge-price-ideal').ambiguity_status,'none');assert.match(claim('not-short-only-annual-decades-weekly-two-years-author-examples').review_note,/未统计验证/);
 assert.match(claim('sell-on-rise-no-panic-profit-early-new-buy-before-return-author-view').review_note,/局部反抽/);
 const risk=claim('novice-unseen-buy90-position-wait-batch-T1-risk');assert.equal(risk.conditions.length,2);assert.match(risk.text,/不能T\+1跑掉风险大.*应分批/);assert.match(risk.review_note,/90%是读者自述.*不用于私改56原T\+0/);
 const exit=claim('rebound-exit-half-good-skill-small-capital-full-then-select-rebuy');assert.equal(exit.conditions.length,2);assert.match(exit.text,/技术好且资金不大/);assert.match(exit.review_note,/并未给反弹固定百分比或点位/);
 assert.notEqual(claim('down40-rebound20-half-two-thirds-rebuy-lower-author-example').ambiguity_status,'none');assert.match(claim('down40-rebound20-half-two-thirds-rebuy-lower-author-example').review_note,/未给第二轮回落价/);
 checks.push('不熟勿全仓/部分练习，年周持有例非实测期限、预设30持有理想不逃避实际小转大；局部上涨卖点非必高于前收，未见买点90%是读者且T+1风险/分批须保，半仓默认或技好且资小可全出非固定反弹点位，40/20例不证必回本');

 const article=[...Array(4)].map((_,i)=>'0432-b'+String(i+7).padStart(3,'0')).concat([...Array(5)].map((_,i)=>'0433-b'+String(i).padStart(3,'0')),['0434-b000','0434-b001']);assert.equal(article.length,11);
 for(const p of article){assert.equal(source(p).role,'author_commentary');assert.equal(source(p).published_at,'2007-06-04');}
 assert.equal(source('0432-b000').published_at,'2007-06-01 15:47:14');for(const p of ['0432-b001','0432-b002'])assert.equal(source(p).published_at,'2007-06-01 15:47:30');assert.equal(source('0432-b006').role,'author_reply');
 const support=claim('jun1-halfline4144-support3734-3434-before-unverified-note');assert.equal(support.evidence[0].quote.includes('备注'),false);assert.equal(support.evidence[0].quote.includes('月线3k'),false);assert.notEqual(support.ambiguity_status,'none');assert.match(source('0432-b001').text,/备注.*月线3k/);
 assert.equal(source('0432-b001').role,'author_commentary');const pending=readFileSync(resolve(agent,'curation/upper/c_stage_l057.pending.jsonl'),'utf8').trim().split('\n').map(JSON.parse);const mixed=pending.find(p=>p.id.endsWith('mixed-annotation-role-date-and-source-boundaries'));assert.ok(mixed.blocks_full_semantic_extraction_completion);assert.match(mixed.suggested_action,/整段原文搜索\/上下文归属仍可能混淆/);
 assert.equal(claim('jun4-halfline4144-shenzhen13700-stand-before-midterm-strong').evidence[0].role,'author_commentary');
 checks.push('11段6/4独立文章从6/1回复改为author_commentary/仅日期不造时分，2段按尾头15:47:30且前段时间不串；432备注作者引文排除，但原段source仍可含未核备注且角色混合，已列阻断待核，不伪称来源隔离完成');

 assert.match(claim('jun1-halfline4144-support3734-3434-before-unverified-note').text,/4144.*3734.*3434/);
 assert.match(claim('jun4-morning-five-month-wording3600-normal-adjust-if-no-break').review_note,/不静改5日线/);assert.match(claim('jun4-close-average-now3540-rebound-down40-at-halfyear-best-year').text,/3540.*40%以上.*半年最好年线/);
 assert.match(claim('jun4-average-short-beartrap-divergence-location-MACD-zero-pressure').review_note,/零轴是MACD量非价格0/);
 assert.equal(claim('ST-five-percent-historical-rebound-after-larger-fall-not-copper-proof').evidence[0].quote.includes('铜矿'),false);
 assert.match(claim('futures-not-risk-insurance-skill-liquidation-author-view').review_note,/不升级为所有对冲机制无效/);
 for(const p of ['0432-b005','0435-b005','0435-b008','0435-b011','0436-b001']){assert.equal(source(p).role,'reader');assert.equal(graph.db.prepare("SELECT count(*) n FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed' AND e.passage_id=?").get('volume_1-a53e99c37ca5-p'+p).n,0);}
 for(const p of ['0431-b001','0432-b008','0432-b010','0433-b000','0433-b001','0433-b002','0433-b004','0434-b000','0434-b001','0434-b002'])assert.equal(graph.db.prepare("SELECT count(*) n FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed' AND e.passage_id=?").get('volume_1-a53e99c37ca5-p'+p).n,0);
 checks.push('原5月均线参数不借未核备注补5期，3600/3540分时点、3734/3434与图值不改，MACD0轴非价格目标；读者失真/90%/期货保险/反弹幅度不升作者事实，铜矿/政策舆论/国债/自述没作技术实证，期货有风险不等所有对冲无效');

 const links={
 'minimum-analysis-view-three-subsegments-overlap-not-final-segment-definition':['0428-b001','0428-fig1'],
 'gap01-and-complex23-real-levels-differ-coarse-one-view-same-lines':['0428-b002','0428-fig1'],
 'ten-segments-weak-third-not-recognized-consistent-alternative-standard':['0428-b003','0428-fig1'],
 'precise45-leave56-retest-sublevel-not-all-below-one-4077-third-sell':['0429-b001','0429-fig1'],
 'fine56-up-up-area-divergence-needs-skill-reaction-channel':['0429-b002','0429-fig1'],
 '67-down-up-down-later-weaker-time-for-space-zero-green-retrace':['0429-b003','0429-fig1'],
 'at6-alternate-center345456-23-vs67-oscillation-return-near':['0430-b001','0430-fig1'],
 'if7-first-buy-9-second-no-low-or-consolidation-divergence':['0430-b001','0430-fig1'],
 'ten-lines-group-nine-after-gap-five-center4015-4122':['0430-b002','0430-fig1'],
 'jun1-halfline4144-support3734-3434-before-unverified-note':['0432-b001','0431-fig1'],
 'jun4-average-short-beartrap-divergence-location-MACD-zero-pressure':['0435-b001','0434-fig1'],
 };
 for(const [slug,[p,f]] of Object.entries(links)){const es=claim(slug).evidence;const e=es.find(e=>e.passage_id==='volume_1-a53e99c37ca5-p'+p);assert.deepEqual(e.figure_ids,['volume_1-a53e99c37ca5-p'+f]);assert.equal(e.figures.length,1);for(const other of es)if(other!==e)assert.deepEqual(other.figure_ids,[]);}
 const figs=graph.db.prepare("SELECT id,origin_status,note FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 427 AND 436").all();assert.equal(figs.length,5);assert.equal(figs.filter(f=>f.origin_status==='unverified').length,3);assert.equal(figs.filter(f=>f.origin_status==='later_annotation').length,2);assert.match(figs.find(f=>f.id.endsWith('0431-fig1')).note,/3739.273.*3440.034/);assert.match(figs.find(f=>f.id.endsWith('0434-fig1')).note,/6\/13/);
 const plan=JSON.parse(readFileSync(resolve(agent,'curation/source-audit/stage-c-l057-source-plan.json'),'utf8'));assert.equal(plan.operations.length,28);const pops=plan.operations.filter(op=>op.table==='passages');assert.equal(pops.length,23);assert.equal(pops.filter(op=>op.after.role==='author_commentary').length,11);assert.equal(pops.filter(op=>op.after.published_at==='2007-06-01 15:47:30').length,2);for(const op of pops)assert.equal(source(op.id.split('-p')[1]).published_at,op.after.published_at);
 const ledger=readFileSync(resolve(agent,'curation/upper/c_stage_l057.coverage.jsonl'),'utf8').trim().split('\n').map(JSON.parse);assert.equal(ledger.length,66);assert.equal(new Set(ledger.map(p=>p.passage_id)).size,66);assert.equal(graph.metadata.semantic_completion,false);
 checks.push('11命题11关联5图逐项核，3当时可得未核/2后加，431右端7月/434右端6月13不证当时预测；23段身份/时间与5图元数据授权变化、66段全台账不等全书或实际Windows验收');

 const anchor=support.evidence[0].id;
 const requests=[['search',{query:'时间换空间'},['search','时间换空间']],['concept',{id:'次级别',limit:20},['concept','次级别','--limit','20']],['neighbors',{id:'时间换空间',depth:1,limit:100},['neighbors','时间换空间','--depth','1','--limit','100']],['evidence',{id:anchor},['evidence',anchor]],['page',{documentId:'volume_1.pdf',page:432},['page','--document-id','volume_1.pdf','--page','432']],['search',{query:'必须建立与资本市场发展阶段相适应',scope:'source',limit:8},['search','必须建立与资本市场发展阶段相适应','--scope','source','--limit','8']],['coverage',{},['coverage']]];
 const parity=[];for(const [command,args,argv] of requests){const a=JSON.parse(JSON.stringify(graph.query(command,args)));assert.deepEqual(JSON.parse(JSON.stringify(desktop.query(command,args))),a);const cli=spawnSync(process.execPath,[resolve(agent,'bin/chan-kg.mjs'),...argv,'--kb',root],{encoding:'utf8',maxBuffer:24*1024*1024});assert.equal(cli.status,0,cli.stderr);assert.deepEqual(JSON.parse(cli.stdout),a);parity.push({command,args,cli_matches_shared:true,desktop_module_matches_shared:true});}
 assert.deepEqual({database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
 const report={graph_version:graph.metadata.graph_version,schema_version:graph.metadata.schema_version,checks,parity,intended_figure_links_checked:{claims:11,associations:11,unique_figures:5},mixed_annotation_status:{passage:'volume_1-a53e99c37ca5-p0432-b001',reviewed_author_quote_excludes_annotation:true,source_search_context_still_mixed:true,source_span_split_complete:false},core_sha256:sha(resolve(agent,'src/core.mjs')),desktop_core_sha256:sha(resolve(agent,'../chan-kg-desktop/vendor/core.mjs')),database_and_manifest_unchanged:true,pass:true,limits:['同模型语义边界/来源和模块一致检查，不是独立或人类金标准/真实Windows运行。','432备注仍混合来源，作者引用避开不等原文搜索隔离完成；与43夹注及54跨页编号context后续修。','粗视角/精次级和弱段标准、30持有理想/反弹资金强语、原5月均线及图文数差仍待核；冻结召回回归/完整G及产品交付未完成。']};
 writeFileSync(resolve(agent,'curation/source-audit/stage-c-l057-verification.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({graph_version:report.graph_version,boundary_groups:checks.length,parity:parity.length,figure_links:report.intended_figure_links_checked,mixed_annotation_source_split_complete:false,pass:true}));
}finally{graph.close();desktop.close();}
