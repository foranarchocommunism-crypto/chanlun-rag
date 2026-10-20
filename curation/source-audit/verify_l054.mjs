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
const claim = slug => { const c = graph.getClaim('upper-l054-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try {
 assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l054-c-stage-%' AND review_status='reviewed'").get().n,41);
 assert.match(claim('case-equalities-d1-g2-d2-g4-and-g0-set-18-5').text,/d1=g2、d2=g4.*18.5/);assert.match(claim('case-equalities-d1-g2-d2-g4-and-g0-set-18-5').review_note,/18.59.*18.5/);
 assert.match(source('0401-b001').text,/^g0g3=.*g2d3$/);
 const eq=claim('associativity-g0g3-original-formula-ends-at-d3-unresolved');assert.notEqual(eq.ambiguity_status,'none');assert.match(eq.review_note,/不能暗改g0d3或补d3g3/);
 assert.match(claim('subminute-legs-as-lines-except-last-at-chosen-level').text,/除最后一个.*1分以下/);
 assert.match(claim('g1-two-legs-no-one-center-tick-second-sell-d2-first-center').text,/尚无1分中枢.*分笔操作者.*二卖.*d2才形成/);
 assert.match(claim('single-price-overlap-counts-not-ignored-under-equality').text,/一个价位.*仍不影响g3三卖.*只要有重叠就算/);
 assert.equal(claim('single-price-overlap-counts-not-ignored-under-equality').evidence[1].quote.includes('主力'),false);
 checks.push('41新增；d1=g2/d2=g4本图条件、g0正文18.5/图18.59与g0g3原式右端d3张力不修；除最后一段保留，分笔二卖非1分二卖，单价位重叠不能任意忽略/亦非孤立价重复就有枢');

 const first=claim('first-decomposition-g5-five-center-d2-g5-whole-submoves');assert.match(first.text,/到d5g5.*\[d2,g5\].*1分走势当线段/);assert.notEqual(first.ambiguity_status,'none');assert.match(first.review_note,/不把\[d2,g5\]静改成三个子中枢边缘交集/);
 const second=claim('second-decomposition-g6-five-center-d3-g5-g7-not-third-sell');assert.match(second.text,/到g6.*\[d3,g5\].*g7不构成/);
 assert.match(claim('d7g7-one-minute-type-specific-retest-doji-lower-chart-confirmation').review_note,/不建任意两十字或六根K必成/);
 assert.match(claim('g7-two-decompositions-same-direction-warning-not-identical-labels').review_note,/第一式g7三卖、第二式g7非三卖/);
 assert.match(claim('choose-current-meaningful-decomposition-all-must-obey-rules').text,/所有分解仍须合规范/);
 assert.match(claim('same-level-centers-must-have-sublevel-connection-in-this-decomposition').review_note,/18课.*次级或更低/);assert.notEqual(claim('same-level-centers-must-have-sublevel-connection-in-this-decomposition').ambiguity_status,'none');
 assert.match(claim('trend-center-connector-same-direction-no-overlap-wrong-d2g2').text,/与趋势同向.*中枢有重叠且连接方向不对/);
 checks.push('首式g5/[d2,g5]与二式g6/[d3,g5]区间、完成点、g7标签各保，整体次级走势端点非子枢交集；本例K形不作递归充分公式；两枢无连接禁式与三次级成高枢不同，连接同向/无重叠并列，18次级或更低范围不覆盖');

 const fast=claim('fast-forceful-weekly-break-smaller-third-needs-volume-strength');assert.equal(fast.conditions.length,2);assert.equal(fast.exceptions.length,1);assert.match(fast.text,/成交量和力度配合/);
 assert.match(claim('novice-buy-wait-own-level-third-sell-prefer-early-use-first-second').text,/不熟者买入仍等.*卖点则宁早勿晚.*一、二卖/);
 assert.match(claim('extreme-amplitude-does-not-alone-upgrade-center-theoretical-example').text,/10000.*0.01.*100000000.*仍称5分/);assert.notEqual(claim('extreme-amplitude-does-not-alone-upgrade-center-theoretical-example').ambiguity_status,'none');
 assert.match(claim('third-point-followthrough-absolute-author-claim-premises-unverified').text,/一定继续向下.*一定继续向上/);assert.match(claim('third-point-followthrough-absolute-author-claim-premises-unverified').review_note,/不替换成必成趋势\/永久不回\/实盘保证/);
 assert.match(claim('divergence-return-causes-oscillation-third-only-trend-possibility').text,/趋势的可能/);
 checks.push('快速大幅周破用30/5三类须迅猛量力配合且分普通震荡，新手买等本级/卖宁早与一二卖提示不对称；极端价差为理论例不验真实制度，三类后方向强语不等必成完整趋势/永不回/实盘保证');

 const one=claim('rare-second-buy-below-first-or-second-sell-above-first-approved');assert.match(one.text,/二买能否低于一买、二卖能否高于一卖.*很少见/);assert.equal(one.evidence[0].quote,'1.当然有可能，虽然很少见。');assert.equal(one.conditions.length,2);assert.match(one.review_note,/近邻API上下文未覆盖跨页整组问题/);
 assert.equal(source('0408-b008').role,'reader');assert.match(source('0408-b008').text,/第二类买点比第一买点低.*第二类卖点比第一卖点高/);
 const two=claim('second-center-guarantee-no-larger-level-wording-reader-item-two');assert.equal(two.evidence[0].quote,'2.这绝对保证。没有什么更大级别，就是按这定义来。');assert.notEqual(two.ambiguity_status,'none');assert.equal(two.conditions.length,2);
 for(const p of ['0408-b009','0408-b010','0409-b000'])assert.equal(source(p).role,'reader');
 assert.match(source('0408-b009').text,/更大级别/);assert.match(source('0409-b000').text,/时间的无限性/);
 assert.match(claim('third-point-sublevel-leave-return-no-center-reentry-item-three').text,/次级别离开、次级别返回不重回中枢/);
 assert.match(claim('third-point-sublevel-leave-return-no-center-reentry-item-three').review_note,/不把读者完整因果判断冒作者明说/);
 for(const c of [one,two,claim('third-point-sublevel-leave-return-no-center-reentry-item-three')])for(const e of c.evidence)assert.equal(e.role,'author_reply');
 checks.push('编号1少见倒置二类许可、2绝对保证/没有什么更大级别与3重申次级离返分别对号；作者原引仅短答，408/409跨页问保持reader并在条件/备注指定稳定段ID，默认邻段不涵盖全问的限制明确，不冒读者因果或宣称53已全解决');

 assert.match(claim('may24-ten-first-1115-second-third-to1412-five-center').text,/10:00.*11:15.*1分级.*14:12.*1分以下背驰/);
 assert.match(claim('1116-not-necessarily-consolidation-divergence-small-to-large-larger-context').review_note,/11:15.*11:16/);
 assert.match(claim('1116-not-necessarily-consolidation-divergence-small-to-large-larger-context').text,/5月22日11:00/);
 assert.match(claim('unicom-channel-rise-skill-trade-rails-divergence-or-hold-unbroken').text,/有技术.*没技术.*下轨不破/);assert.match(claim('unicom-channel-rise-skill-trade-rails-divergence-or-hold-unbroken').review_note,/不等当前联通趋势.*等同布林通道/);
 assert.equal(claim('skill-criterion-fast-current-ruleful-decomposition-not-real-diploma').evidence[0].quote.includes('北大'),false);
 for(const p of ['0407-b002','0407-b003','0407-b005','0407-b007','0407-b009','0408-b008','0409-b002','0409-b010','0409-b011']){assert.equal(source(p).role,'reader');assert.equal(graph.db.prepare("SELECT count(*) n FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed' AND e.passage_id=?").get('volume_1-a53e99c37ca5-p'+p).n,0);}
 for(const p of ['0410-b001','0410-b002','0410-b003','0410-b004','0410-b005','0410-b006','0411-b001','0411-b002','0411-b003'])assert.equal(graph.db.prepare("SELECT count(*) n FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed' AND e.passage_id=?").get('volume_1-a53e99c37ca5-p'+p).n,0);
 checks.push('5/24日内两卖1分级与1分以下背驰、读者11:16/作者11:15分别保；联通通道按技能/下轨条件非当前或布林定义，MACD仅辅；CCTV/Joyce及读者操作/解答没升作者，收费/财富/宏观30-50%/文化学历语境没作技术实证');

 const links={
 'case-equalities-d1-g2-d2-g4-and-g0-set-18-5':['0400-b010','0401-fig1'],
 'subminute-legs-as-lines-except-last-at-chosen-level':['0400-b011','0401-fig1'],
 'g1-two-legs-no-one-center-tick-second-sell-d2-first-center':['0400-b012','0401-fig1'],
 'equality-touch-oscillation-g3-third-sell-if-strict-g2-earlier':['0400-b012','0401-fig1'],
 'associativity-g0g3-original-formula-ends-at-d3-unresolved':['0401-b000','0402-fig1'],
 'single-price-overlap-counts-not-ignored-under-equality':['0401-b002','0402-fig1'],
 'successive-leg-strength-MACD-consolidation-divergence-scale-operability':['0401-b003','0402-fig1'],
 'same-level-centers-must-have-sublevel-connection-in-this-decomposition':['0401-b004','0403-fig1'],
 'at-d4-two-permitted-decompositions-preserve-original-formulas':['0401-b005','0403-fig1'],
 'rebound-first-intermediate-second-center-oscillation-g4-equals-d2':['0402-b000','0403-fig1'],
 'first-decomposition-g5-five-center-d2-g5-whole-submoves':['0402-b002','0404-fig1'],
 'd7g7-one-minute-type-specific-retest-doji-lower-chart-confirmation':['0402-b004','0404-fig1'],
 'second-decomposition-g6-five-center-d3-g5-g7-not-third-sell':['0403-b001','0405-fig1'],
 'g7-two-decompositions-same-direction-warning-not-identical-labels':['0405-b002','0405-fig1'],
 'may24-ten-first-1115-second-third-to1412-five-center':['0406-b001','0406-fig1'],
 '1116-not-necessarily-consolidation-divergence-small-to-large-larger-context':['0407-b016','0408-fig1'],
 'trend-center-connector-same-direction-no-overlap-wrong-d2g2':['0410-b007','0403-fig1'],
 };
 for(const [slug,[p,f]] of Object.entries(links)){const es=claim(slug).evidence;const e=es.find(e=>e.passage_id==='volume_1-a53e99c37ca5-p'+p);assert.deepEqual(e.figure_ids,['volume_1-a53e99c37ca5-p'+f]);assert.equal(e.figures.length,1);for(const other of es)if(other!==e)assert.deepEqual(other.figure_ids,[]);}
 const figs=graph.db.prepare("SELECT id,origin_status,note FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 400 AND 411").all();assert.equal(figs.length,7);assert.equal(figs.filter(f=>f.origin_status==='unverified').length,6);assert.equal(figs.filter(f=>f.origin_status==='later_annotation').length,1);assert.equal(figs.find(f=>f.id.endsWith('0408-fig1')).origin_status,'later_annotation');assert.match(figs.find(f=>f.id.endsWith('0408-fig1')).note,/5\/25/);
 const plan=JSON.parse(readFileSync(resolve(agent,'curation/source-audit/stage-c-l054-source-plan.json'),'utf8'));assert.equal(plan.operations.length,26);const pops=plan.operations.filter(op=>op.table==='passages');assert.equal(pops.length,19);for(const op of pops){assert.deepEqual(Object.keys(op.after),['published_at']);assert.equal(op.before.published_at,op.after.published_at.replace(' ',''));assert.equal(source(op.id.split('-p')[1]).published_at,op.after.published_at);}
 const ledger=readFileSync(resolve(agent,'curation/upper/c_stage_l054.coverage.jsonl'),'utf8').trim().split('\n').map(JSON.parse);assert.equal(ledger.length,101);assert.equal(new Set(ledger.map(p=>p.passage_id)).size,101);assert.equal(graph.metadata.semantic_completion,false);
 checks.push('17命题17关联7图逐项核，6原发未核/408图含5/25为后加且不证5/24预测；19时间空格/7图备注授权变化、101段全台账，条件/身份/坐标完整不等全书或实际Windows验收');

 const anchor=two.evidence[0].id;
 const requests=[['search',{query:'通道式上涨'},['search','通道式上涨']],['concept',{id:'分解多样性',limit:20},['concept','分解多样性','--limit','20']],['neighbors',{id:'通道式上涨',depth:1,limit:100},['neighbors','通道式上涨','--depth','1','--limit','100']],['evidence',{id:anchor},['evidence',anchor]],['page',{documentId:'volume_1.pdf',page:408},['page','--document-id','volume_1.pdf','--page','408']],['search',{query:'第二类买点比第一买点低',scope:'source',limit:8},['search','第二类买点比第一买点低','--scope','source','--limit','8']],['coverage',{},['coverage']]];
 const parity=[];for(const [command,args,argv] of requests){const a=JSON.parse(JSON.stringify(graph.query(command,args)));assert.deepEqual(JSON.parse(JSON.stringify(desktop.query(command,args))),a);const cli=spawnSync(process.execPath,[resolve(agent,'bin/chan-kg.mjs'),...argv,'--kb',root],{encoding:'utf8',maxBuffer:24*1024*1024});assert.equal(cli.status,0,cli.stderr);assert.deepEqual(JSON.parse(cli.stdout),a);parity.push({command,args,cli_matches_shared:true,desktop_module_matches_shared:true});}
 assert.deepEqual({database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
 const report={graph_version:graph.metadata.graph_version,schema_version:graph.metadata.schema_version,checks,parity,intended_figure_links_checked:{claims:17,associations:17,unique_figures:7},numbered_reply_context_scope:'原短答作者身份/编号与原跨页reader问题分别核，条件与备注给稳定ID；默认邻段context不涵盖全组，需page408/409联读，此限制未宣称修复。',core_sha256:sha(resolve(agent,'src/core.mjs')),desktop_core_sha256:sha(resolve(agent,'../chan-kg-desktop/vendor/core.mjs')),database_and_manifest_unchanged:true,pass:true,limits:['同模型语义边界/指代/来源和模块一致检查，不是独立或人类金标准/真实Windows运行。','原公式端点/设价、子枢用语/走势高低点、18与54连接级别、三类方向强语/快速突破、编号2更大级别等范围仍待核。','跨页编号问题未自动全部纳入近邻context，已在条件/备注标明联读源ID；完整G/召回回归及产品交付未完成。']};
 writeFileSync(resolve(agent,'curation/source-audit/stage-c-l054-verification.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({graph_version:report.graph_version,boundary_groups:checks.length,parity:parity.length,figure_links:report.intended_figure_links_checked,pass:true}));
}finally{graph.close();desktop.close();}
