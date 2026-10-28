import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { KnowledgeGraph } from '../../src/core.mjs';
const agent=resolve(dirname(fileURLToPath(import.meta.url)),'../..'),root=resolve(agent,'../shared-knowledge/v0.1.0'),sha=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const before={database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},graph=new KnowledgeGraph(root),checks=[];
const claim=s=>{const r=graph.getClaim('upper-l061-c-stage-'+s);assert.ok(r,s);return r;},source=s=>graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p'+s);
try{
 assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l061-c-stage-%' AND review_status='reviewed'").get().n,44);
 const provisional=claim('provisional-divergence-from65-invalid-if-stronger-else-recurse');assert.match(provisional.text,/先假设.*大于55—60.*否定.*继续观察/);assert.equal(provisional.conditions.length,1);
 assert.match(claim('at69-no-newhigh-no-divergence70-risk-zone-not-confirmed').text,/未创新高.*70.*危险区.*不是卖出确认/);
 assert.equal(claim('69-70-vs67-68-no-consolidation-div-no-exit-except-subsegment').exceptions.length,1);
 assert.match(claim('71-third-buy66-69-future-expand-or-center-up-requires-no-pan-div').review_note,/必要要求.*非单一充分/);
 assert.match(claim('four-nests65-69-71-inner71-locate72').text,/65起.*69起.*71起.*71内部/);
 checks.push('44新增；65起先假设/强于前段否定/未否定继续递归不是已确认；69未新高、70无盘背而细级例外、71无盘背只是上移必要要求，四重是本例非所有转折固定四层。');

 assert.match(claim('74-second-and-third69-72-not70-73-associativity').text,/69—72.*不能归70—73.*结合律/);
 assert.match(claim('third-point-atleast-five-subsegments-three-center-four-leave-five-point').text,/至少需5段次级别.*前三段.*第四段.*第五段/);
 assert.match(claim('second-third-coincident-often-force-not-guarantee').review_note,/往往非必然/);
 assert.match(claim('five60-69-key69-4244-third-sell-below-expands-atleast30').review_note,/非单价低于4244/);
 assert.match(claim('after72-break73-also4244-stand-max-five-else-five-down-or30').review_note,/同价但不是同时间点/);
 checks.push('74二三卖须69—72枢合法结合而非70—73，至少五次级完整分组不简化五笔；二三重合往往非保证，69/73同4244不同点且需三类结构。');

 const qty=claim('72-sell-quantity-five-or-below-all-larger-capacity-hedge');assert.equal(qty.conditions.length,2);assert.match(qty.text,/5分及以下.*全卖.*更大级别按.*数量/);
 assert.match(claim('one-top-exit-wait-one-bottom-monthly-ignore-smaller-volatility').review_note,/大级破坏\/快速空间例外/);
 assert.match(claim('rhythm-buy-sell-points-capital-efficiency-not-must-sixteen-stocks').text,/不要求.*买这些股票/);
 assert.match(claim('jun28-should-sell-buy-not-must-low-skill-control-position').text,/买不一定.*控制仓位/);
 assert.match(claim('105-div-no-clear-one-center-intraday-cost-noT0-skill-exceptions').text,/前无明确1分枢.*非T\+0.*技术好者除外/);
 checks.push('72卖量按级别/容量分，大级非全清，原级别保60例外；16只示例不必跟买、0成本/100%非实证，震荡买不一定、105无明确一分枢仅盘中且费用/非T+0/技能条件保。');

 const plan=JSON.parse(readFileSync(resolve(agent,'curation/source-audit/stage-c-l061-source-plan.json'),'utf8'));assert.equal(plan.operations.length,19);const pops=plan.operations.filter(o=>o.table==='passages');assert.equal(pops.length,8);assert.equal(pops.filter(o=>o.after.role==='author_commentary').length,6);
 for(const op of pops)for(const [k,v] of Object.entries(op.after))assert.equal(source(op.id.split('-p')[1])[k],v);
 assert.equal(source('0461-b005').role,'author_reply');assert.equal(source('0461-b005').published_at,'2007-05-22 08:49:55');assert.match(source('0461-b005').text,/。”$/);assert.equal(source('0461-b006').role,'author_commentary');assert.equal(source('0462-b004').published_at,'2007-06-22 08:30:44');assert.equal(source('0457-b001').published_at,'2007-06-21');
 const conflict=claim('jun28-100-top102-second103-unfinished-literal102-completion-conflict');assert.notEqual(conflict.ambiguity_status,'none');assert.match(conflict.text,/103.*未走完.*要102走完/);assert.match(source('0468-b001').text,/103在收盘时还没走完，要102走完/);
 assert.match(claim('new-segment-break-old-literal-down-laterhigh-below-priorlow').text,/后高点一定低于前低点/);
 assert.notEqual(claim('jun22-46-87-thirty-center4067-4192-third-leg-unfinished').ambiguity_status,'none');assert.match(claim('jun22-46-87-thirty-center4067-4192-third-leg-unfinished').text,/已构成.*第三段是否完成尚待看/);
 checks.push('嵌套5/22旧答闭引后六段恢复6/22文章，两旧答日期空格修正，6/21只有日不造时分；30分枢已构成/第三段未确认、103未完/要102完和跌段后高低于前低原字保张力，不静改。');

 const precision=claim('4022-precision-two-decimal-no-break-truncate-overlap-round-not');assert.equal(precision.conditions.length,2);assert.match(precision.text,/4022.69.*4022.42.*同为4022.*4023\/4022/);
 assert.match(claim('jun29-henceforth-direct-truncation-choice-not-universal-theorem').review_note,/以后时效.*不是理论必须/);
 assert.match(claim('jun28-requote-jun4-monthly-five-vs4144-compress-july-aug-direction').review_note,/3600为6\/4引用时点不是6\/28/);
 assert.match(claim('jun29-quarter500wick-july-halfline4159-beforestand-big-shake').text,/下月.*4159/);
 assert.match(claim('jun29-atleast-one-div-entry-res3919-fiveweek-unskilled-can-stay-out').text,/至少1分以上.*5周线.*可不参与/);
 checks.push('4022精度三方案：两位无破、截整可重、舍入不同；6/29以后选择不倒写59算法或抹64自选。凌晨发布时间/前交易日、6/4引述3600/原5月/5周及4144/次月4159分时点。');

 const links={
 'around-one-center-strength-compare55-60-vs-from65':['0457-b006',['0458-fig1']],
 'provisional-divergence-from65-invalid-if-stronger-else-recurse':['0457-b006',['0458-fig1']],
 'at69-no-newhigh-no-divergence70-risk-zone-not-confirmed':['0457-b007',['0458-fig1']],
 '69-70-vs67-68-no-consolidation-div-no-exit-except-subsegment':['0458-b000',['0458-fig1']],
 '71-third-buy66-69-future-expand-or-center-up-requires-no-pan-div':['0458-b000',['0458-fig1']],
 '71-weaker69-70-and-from69-weaker65-66-red-area-aid':['0458-b000',['0458-fig1']],
 'four-nests65-69-71-inner71-locate72':['0458-b001',['0458-fig1']],
 '72-sell-quantity-five-or-below-all-larger-capacity-hedge':['0458-b002',['0458-fig1']],
 '74-second-and-third69-72-not70-73-associativity':['0458-b003',['0458-fig1']],
 'third-point-atleast-five-subsegments-three-center-four-leave-five-point':['0459-b000',['0458-fig1']],
 'second-third-coincident-often-force-not-guarantee':['0459-b000',['0458-fig1']],
 'five60-69-key69-4244-third-sell-below-expands-atleast30':['0459-b001',['0458-fig1']],
 'after72-break73-also4244-stand-max-five-else-five-down-or30':['0459-b001',['0458-fig1']],
 'jun21-4244-next-4144-mid-close4147-near-not-same':['0459-b003',['0459-fig1']],
 'jun22-81-82-pan84-second-microdiv87-not-end-unless85-4131':['0462-b005',['0463-fig1']],
 'jun22-five75-84-lower4188-return-fail-warn-third-sell':['0462-b006',['0463-fig2']],
 'jun22-46-87-thirty-center4067-4192-third-leg-unfinished':['0462-b006',['0463-fig2']],
 'jun23-hand-draw-figure-one-equivalent-segment-second-distinctions':['0464-b002',['0464-fig1','0464-fig2']],
 'jun26-published-prior-session-return4131-under4188-third-sell':['0464-b005',['0465-fig1']],
 'jun26-4025-new-one-lower3982-return-new-five-else-line-down':['0464-b005',['0465-fig1']],
 'jun27-break3982-retest4025-watch4131-before-third-buy-oscillation':['0466-b003',['0466-fig1']],
 'jun28-100-top102-second103-unfinished-literal102-completion-conflict':['0468-b001',['0467-fig1']],
 '4022-precision-two-decimal-no-break-truncate-overlap-round-not':['0468-b004',['0468-fig1']],
 'jun29-henceforth-direct-truncation-choice-not-universal-theorem':['0469-b002',['0468-fig1']],
 '105-div-no-clear-one-center-intraday-cost-noT0-skill-exceptions':['0469-b005',['0469-fig1']]};
 let associations=0;const unique=new Set();for(const [slug,[p,fs]] of Object.entries(links)){const es=claim(slug).evidence,target=es.find(e=>e.passage_id==='volume_1-a53e99c37ca5-p'+p);assert.ok(target,slug);const ids=fs.map(f=>'volume_1-a53e99c37ca5-p'+f);assert.deepEqual(target.figure_ids,ids);assert.equal(target.figures.length,ids.length);for(const e of es)if(e!==target)assert.deepEqual(e.figure_ids,[]);associations+=ids.length;ids.forEach(id=>unique.add(id));}
 assert.equal(Object.keys(links).length,25);assert.equal(associations,26);assert.equal(unique.size,11);
 const figs=graph.db.prepare("SELECT id,origin_status,note FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 457 AND 470").all();assert.equal(figs.length,11);assert.equal(figs.filter(f=>f.origin_status==='later_annotation').length,4);assert.match(figs.find(f=>f.id.endsWith('0466-fig1')).note,/6\/29/);
 const ledger=readFileSync(resolve(agent,'curation/upper/c_stage_l061.coverage.jsonl'),'utf8').trim().split('\n').map(JSON.parse);assert.equal(ledger.length,83);assert.equal(new Set(ledger.map(p=>p.passage_id)).size,83);assert.equal(graph.metadata.semantic_completion,false);
 checks.push('83段全台账、25命题26图文关联11整图核；7原发未核4后加，464手绘等/不等/小转大不造参数；原87/后89、3819诸小数/105原3780.84与重绘3779.81分存，未来K不证前瞻。');
 const anchor=precision.evidence[0].id,requests=[['search',{query:'4022.69'},['search','4022.69']],['concept',{id:'区间套',limit:10},['concept','区间套','--limit','10']],['neighbors',{id:'结合律',depth:1,limit:100},['neighbors','结合律','--depth','1','--limit','100']],['evidence',{id:anchor},['evidence',anchor]],['page',{documentId:'volume_1.pdf',page:461},['page','--document-id','volume_1.pdf','--page','461']],['search',{query:'还有一只是600569',scope:'source',limit:3},['search','还有一只是600569','--scope','source','--limit','3']],['coverage',{},['coverage']]];
 const parity=[];for(const [command,args,argv] of requests){const a=JSON.parse(JSON.stringify(graph.query(command,args))),cli=spawnSync(process.execPath,[resolve(agent,'bin/chan-kg.mjs'),...argv,'--kb',root],{encoding:'utf8',maxBuffer:24*1024*1024});assert.equal(cli.status,0,cli.stderr);assert.deepEqual(JSON.parse(cli.stdout),a);parity.push({command,args,cli_matches_shared:true});}
 assert.deepEqual({database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
 const report={graph_version:graph.metadata.graph_version,schema_version:graph.metadata.schema_version,delivery_scope:'shared_knowledge_base_only',checks,parity,intended_figure_links_checked:{claims:25,associations:26,unique_figures:11},database_and_manifest_unchanged:true,pass:true,limits:['同代理四轮不是独立/人类金标准；未核原博客和逐笔真实成交。','108课均有阅读记录不等全部解释统一；43/57混合旁注、54跨页完整问题和全书覆盖来源/交付审计未完成。','软件交付已排除；现有检索回归和生成回答评价边界如实披露。']};writeFileSync(resolve(agent,'curation/source-audit/stage-c-l061-verification.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({graph_version:report.graph_version,boundary_groups:checks.length,parity:parity.length,figure_links:report.intended_figure_links_checked,pass:true}));
}finally{graph.close();}
