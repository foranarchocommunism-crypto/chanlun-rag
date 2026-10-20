import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { KnowledgeGraph } from '../../src/core.mjs';
const agent=resolve(dirname(fileURLToPath(import.meta.url)),'../..'),root=resolve(agent,'../shared-knowledge/v0.1.0');
const sha=p=>createHash('sha256').update(readFileSync(p)).digest('hex'),before={database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))};
const graph=new KnowledgeGraph(root),checks=[];
const claim=s=>{const r=graph.getClaim('upper-l059-c-stage-'+s);assert.ok(r,s);return r;},source=s=>graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p'+s);
try{
 assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l059-c-stage-%' AND review_status='reviewed'").get().n,28);
 assert.match(claim('segment-shape-not-amplitude-nonoverlap-up-can-extend').text,/长短和幅度无关.*各低点.*前一个高点/);
 assert.match(claim('adjacent-segments-alternate-direction-not-two-same-direction').text,/不能同向/);
 assert.notEqual(claim('atleast-three-fold-no-flat-one-price-limit-below-segment').ambiguity_status,'none');
 assert.match(claim('early-segment-end-trend-divergence-else-consolidation-shock-second').text,/一般.*趋势背驰.*盘整背驰.*突发.*第二类/);
 assert.match(claim('early-segment-end-trend-divergence-else-consolidation-shock-second').review_note,/后64\/67/);
 assert.match(claim('third-red-arrow-higher-green-segment-end-unconfirmed').text,/尚不能确定完成/);
 checks.push('28新增；线段看形态非幅度、相邻必须异向，三折/一字涨停与早期背驰确认不静代后64/67特征序列；图三尾段仍未确认。');

 const precision=claim('3994-precision-one-or-three-segments-preselect-uniform');assert.match(precision.text,/3994.57.*3994.21.*个位.*三线段.*两位小数.*一线段/);assert.equal(precision.conditions.length,2);assert.match(precision.review_note,/未指定四舍五入\/截尾算法/);
 assert.match(claim('near-and-obvious-down-up-down-prefers-three-no-substantial-impact-author').text,/明显下—上—下.*倾向/);
 assert.match(claim('1-19-five-type-only-consolidation-no-two-five-centers').review_note,/58图17.*编号差异未自动归因/);
 assert.match(claim('one-minute-chart-is-precision-premise-not-larger-level-ban').text,/精度.*并不妨碍.*更大级别/);
 checks.push('3994.57/3994.21原数、预设统一精度和明显三折倾向保留，未造舍入算法；7—8—9及58图17/59图19各保局部编号，不自动跨图同号实体合并。');

 assert.match(claim('1-19-five-type-only-consolidation-no-two-five-centers').text,/未形成两个5分钟中枢.*盘整/);
 assert.match(claim('19-45-atleast-five-center41-below32-but-type-unfinished').text,/41低于32.*尚未最终完成/);
 assert.match(claim('alternate22-31-five-center29-below24-unfinished-invariant').text,/29低于24.*22—31.*未完成/);
 const trend=claim('alternate41-third-buy-if-new-five-nonoverlap-then-uptrend');assert.equal(trend.conditions.length,2);assert.match(trend.text,/若41起.*最终形成.*不重叠.*才成为/);
 assert.match(claim('second33-and37-two-recent-one-centers-third-buys').text,/33对应28—31、37对应32—35/);
 checks.push('1—19最终只盘整、新19—45未完和另一22—31枢分开；41三买限该分解，新5分最终非重叠才条件上涨趋势，33/37各有相应最近一分枢。');

 const strong=claim('strong-if-no42-45-third-sell-or-expand-not-touch22-31-oscillation');assert.match(strong.text,/不出三卖，或虽出三卖.*不触及22—31五分中枢震荡区间/);assert.match(strong.review_note,/不同于只取中枢核心/);
 assert.match(claim('otherwise-weaker30-center-expand-from22-31-operation-own-level').text,/自身操作级别/);
 assert.match(claim('jun14-42-45-extended-nine-now-five-center-gap-not-filled').review_note,/总结构.*不是所有中枢定义须九段/);
 const rhythm=claim('oscillation-sell-before-buy-top-reduce-bottom-rebuy-old-low-chips');assert.equal(rhythm.conditions.length,2);assert.match(rhythm.text,/低位已有筹码.*先减仓.*再补/);
 assert.match(claim('possible-third-sell-stronger-shake-stop-rebuy-wait-down-buy').text,/可能形成.*停止回补.*出现买点再进入/);
 checks.push('强支是无三卖或后扩张不触旧枢震荡区间，区间非中枢核心；9段是本例延伸总结构。先卖后买限已有低位筹码，可能三卖阶段即停补、再入仍须买点。');

 const plan=JSON.parse(readFileSync(resolve(agent,'curation/source-audit/stage-c-l059-source-plan.json'),'utf8'));assert.equal(plan.operations.length,12);const pops=plan.operations.filter(o=>o.table==='passages');assert.equal(pops.length,5);for(const op of pops){assert.equal(op.after.published_at,'2007-06-15 15:30:42');assert.equal(source(op.id.split('-p')[1]).published_at,op.after.published_at);}
 assert.equal(source('0447-b004').published_at,'2007-06-14 15:33:09');assert.equal(source('0448-b008').published_at,'2007-06-18 08:18:39');assert.equal(source('0450-b004').published_at,'2007-06-18 15:16:38');
 for(const p of ['0448-b004','0448-b005','0448-b006','0448-b007']){assert.equal(source(p).role,'reader');assert.equal(graph.db.prepare("SELECT count(*) n FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed' AND e.passage_id=?").get('volume_1-a53e99c37ca5-p'+p).n,0);}
 assert.match(claim('jun15-two-stock-groups-conditional-newhigh-or-no-large-divergence-retest').review_note,/是且/);
 assert.match(claim('jun18-gap-nature-watch-one-third-sell-effective-below4224').review_note,/联合.*压力增大/);
 checks.push('5段日期按6/15时间头及跨页纠正；6/18宏观文章/收评分时独立。CCTV9元三买和罗锅身份仅reader；6/15两股票组联合条件、6/18一分三卖有效破4224联合不降成触价。');

 const links={
 'first20-23-one-center-extends-29-third-buy':['0445-b000','0444-fig1'],
 'second33-and37-two-recent-one-centers-third-buys':['0445-b000','0444-fig2'],
 'third-red-arrow-higher-green-segment-end-unconfirmed':['0445-b000','0445-fig1'],
 'early-segment-end-trend-divergence-else-consolidation-shock-second':['0445-b000','0445-fig1'],
 'third-future-42-45-one-center-oscillation-until-third-point':['0445-b000','0445-fig1'],
 '1-19-five-type-only-consolidation-no-two-five-centers':['0446-b001','0445-fig2'],
 '19-45-atleast-five-center41-below32-but-type-unfinished':['0446-b001','0446-fig1'],
 'alternate22-31-five-center29-below24-unfinished-invariant':['0446-b002','0446-fig1'],
 'alternate41-third-buy-if-new-five-nonoverlap-then-uptrend':['0446-b002','0446-fig1'],
 'strong-if-no42-45-third-sell-or-expand-not-touch22-31-oscillation':['0446-b003','0446-fig1'],
 'otherwise-weaker30-center-expand-from22-31-operation-own-level':['0446-b003','0446-fig1'],
 'jun14-42-45-extended-nine-now-five-center-gap-not-filled':['0447-b001','0447-fig1'],
 'jun15-third-goal4144-reached-stand-before-fourth-newhigh':['0447-b006','0447-fig1'],
 'jun18-gap-nature-watch-one-third-sell-effective-below4224':['0450-b004','0450-fig1']};
 for(const [slug,[p,f]] of Object.entries(links)){const es=claim(slug).evidence,target=es.find(e=>e.passage_id==='volume_1-a53e99c37ca5-p'+p);assert.ok(target,slug);assert.deepEqual(target.figure_ids,['volume_1-a53e99c37ca5-p'+f]);assert.equal(target.figures.length,1);for(const e of es)if(e!==target)assert.deepEqual(e.figure_ids,[]);}
 const figs=graph.db.prepare("SELECT id,origin_status,note FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 443 AND 450").all();assert.equal(figs.length,7);assert.equal(figs.filter(f=>f.origin_status==='later_annotation').length,3);assert.match(figs.find(f=>f.id.endsWith('0445-fig2')).note,/26\/12\/9/);assert.match(figs.find(f=>f.id.endsWith('0450-fig1')).note,/6\/19/);
 const ledger=readFileSync(resolve(agent,'curation/upper/c_stage_l059.coverage.jsonl'),'utf8').trim().split('\n').map(JSON.parse);assert.equal(ledger.length,46);assert.equal(new Set(ledger.map(p=>p.passage_id)).size,46);assert.equal(graph.metadata.semantic_completion,false);
 checks.push('46段全台账、14命题14图文关联7整图核；4未核3后加，原26/12/9顺序与后6/15/6/19未来K不静修、不证明当时预测；独立宏观观点非现行经济/监管事实。');
 const anchor=precision.evidence[0].id,requests=[['search',{query:'3994.57'},['search','3994.57']],['concept',{id:'价格精度',limit:10},['concept','价格精度','--limit','10']],['neighbors',{id:'市场分力',depth:1,limit:100},['neighbors','市场分力','--depth','1','--limit','100']],['evidence',{id:anchor},['evidence',anchor]],['page',{documentId:'volume_1.pdf',page:446},['page','--document-id','volume_1.pdf','--page','446']],['search',{query:'CCTV',scope:'source',limit:3},['search','CCTV','--scope','source','--limit','3']],['coverage',{},['coverage']]];
 const parity=[];for(const [command,args,argv] of requests){const a=JSON.parse(JSON.stringify(graph.query(command,args))),cli=spawnSync(process.execPath,[resolve(agent,'bin/chan-kg.mjs'),...argv,'--kb',root],{encoding:'utf8',maxBuffer:24*1024*1024});assert.equal(cli.status,0,cli.stderr);assert.deepEqual(JSON.parse(cli.stdout),a);parity.push({command,args,cli_matches_shared:true});}
 assert.deepEqual({database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
 const report={graph_version:graph.metadata.graph_version,schema_version:graph.metadata.schema_version,delivery_scope:'shared_knowledge_base_only',checks,parity,intended_figure_links_checked:{claims:14,associations:14,unique_figures:7},database_and_manifest_unchanged:true,pass:true,limits:['同一代理四轮，不是独立或人类金标准；原博客未逐字核对。','早期线段/精度/局部编号、强语与区间边界待核；43/57来源夹注、54跨页问题、余60至61及最终知识库交付审计未完成。','软件构建和产品交付已排除，现有检索回归仍需如实披露。']};writeFileSync(resolve(agent,'curation/source-audit/stage-c-l059-verification.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({graph_version:report.graph_version,boundary_groups:checks.length,parity:parity.length,figure_links:report.intended_figure_links_checked,pass:true}));
}finally{graph.close();}
