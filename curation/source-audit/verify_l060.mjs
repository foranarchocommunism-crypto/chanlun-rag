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
const claim=s=>{const r=graph.getClaim('upper-l060-c-stage-'+s);assert.ok(r,s);return r;},source=s=>graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p'+s);
try{
 assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l060-c-stage-%' AND review_status='reviewed'").get().n,26);
 const pair=claim('samelevel-B0A1B1A2B2-below-vs-not-below-equality-larger-center');assert.equal(pair.conditions.length,1);assert.match(pair.text,/同级别.*不低于A1/);assert.match(pair.review_note,/含相等/);
 assert.match(claim('expectation-force-only-externalized-actual-trade-not-fear-alone').text,/须外化为买卖行为/);assert.match(claim('no-prediction-not-impossibility-not-driven-by-greed-fear').text,/并非不可预测、不可预期/);
 checks.push('26新增；同级B0/A1/B1/A2/B2不低于含等号，交易化预期模型不冒测量心理，符合理论多解非任意画法，不预测不等不可预测。');

 assert.match(claim('finite-minimum-observed-segment-cost-channel-capacity-flatten-below').text,/成本、交易通道和资金规模.*不能无限细.*每笔成交/);
 assert.match(claim('meaningful-operation-atleast-subminute-segment-literal-not-fixed-minute').text,/至少是1分钟以下线段级别的/);
 assert.match(claim('45-46-vs43-44-consolidation-all-red-areas-sum').text,/所有红柱面积之和/);
 const tiny=claim('45-46-inner-small-to-large-first-no-new-high-exit-smaller-center');assert.equal(tiny.conditions.length,2);assert.match(tiny.text,/小级别转大级别.*不创新高/);
 const big=claim('thirty-operation-ignore46-47-hold-five-up-until-div-or-break');assert.equal(big.conditions.length,2);assert.match(big.text,/30分钟.*忽略46—47.*5分钟上涨背驰或突发破坏/);
 checks.push('理论每笔与有限操作精度分开，成本/通道/容量条件保；原至少1分钟以下线段不改字，45—46所有红面积及最严格小转大，与30分忽略46—47/持到5分背驰或突发破坏分层。');

 assert.match(claim('46-55-five-center55-consolidation-not-true-first-buy57-analogy').text,/仅类比.*严格说盘整背驰无所谓第一类买点/);
 assert.match(claim('55-60-segment-up59-60-div-zero-return-newhigh-weaker-area-height').text,/先回零轴.*60新高.*面积及黄白高度均弱/);
 assert.match(claim('60-pull-under58-61-lower-new58-61-one-center').text,/61实际低于58.*58—61/);
 assert.match(claim('jun19-from60-one-center4224-4254-below-third-sell-not-price-alone').text,/从60起.*4224,4254/);
 assert.match(claim('jun19-above4254-one-third-buy-for-new-up-otherwise-oscillation').text,/4254上出现1分三买.*否则/);
 assert.match(claim('jun20-one-return-fail-touch4224-five-third-sell-or-stand-strong').text,/1分走势不能重新触及.*5分三卖/);
 checks.push('55盘背假一买仅类比，MACD先回零/新高/面积和高度弱联合，58—61新枢与收评从60起[4224,4254]原锚点分存；4224下1分三卖与次日1分回抽不触成5分三卖不同，不简化触价。');

 assert.notEqual(claim('news-during-nested-confirm-worst-after-zero-effect-author-strong').ambiguity_status,'none');assert.match(claim('news-during-nested-confirm-worst-after-zero-effect-author-strong').review_note,/未外证频率/);
 assert.match(claim('not-every-second-sell-act-monthly-or-five-intact-one-center-ignore').text,/1分中枢未破/);
 const exit=claim('large-level-news-break-dont-wait-same-level-intraday-smaller-second');assert.equal(exit.conditions.length,1);assert.match(exit.text,/不必等同级二卖.*1分甚至线段/);
 const space=claim('level-usual-space-fast-five-drop50-may-enter-smaller-than-thirty');assert.equal(space.conditions.length,1);assert.match(space.text,/快速行情.*5分走势跌50%.*原按30分.*5分买入/);
 checks.push('消息精确定位后0影响/小概率为作者强语非实测；并非每二卖要动，大级已破可盘中小级卖，快速小级空间足够可供30操作者5分入，不取消一般原级别或保证成交。');

 const plan=JSON.parse(readFileSync(resolve(agent,'curation/source-audit/stage-c-l060-source-plan.json'),'utf8'));assert.equal(plan.operations.length,7);const pops=plan.operations.filter(o=>o.table==='passages');assert.equal(pops.length,3);for(const op of pops)assert.equal(source(op.id.split('-p')[1]).published_at,'2007-06-20 15:49:31');
 for(const p of ['0456-b005','0456-b006']){assert.equal(source(p).role,'reader');assert.equal(graph.db.prepare("SELECT count(*) n FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed' AND e.passage_id=?").get('volume_1-a53e99c37ca5-p'+p).n,0);}
 assert.match(claim('chart-period-not-move-level-one-minute-can-find-year-center').text,/1分图一样可判断年线中枢/);
 assert.match(claim('four-stock-shapes-individual-not-index-all-same-buy-kind').text,/四形态.*新高回试.*底部双底头肩底/);
 assert.match(claim('jun20-touch46-near4192-center-expand-now-larger-oscillation').review_note,/未明确扩至哪个分钟级别/);
 assert.match(claim('jun20-mid4144-stand-or-adjust-level-five-day-five-week-reference').text,/短线看5日线、中线看5周线/);
 checks.push('3作者跨页答时间只补空格、Abc仍reader，1分图可判年线不混图与走势；四股形态分别看，4192附近触46不添已成30分，短5日/中5周分开，独立PE法规不作现行规则。');

 const links={
 'samelevel-B0A1B1A2B2-below-vs-not-below-equality-larger-center':['0451-b002','0451-fig1'],
 'A1-psych-price-three-expectations-watch-no-actual-trade':['0451-b002','0451-fig1'],
 '45-46-vs43-44-consolidation-all-red-areas-sum':['0452-b002','0452-fig1'],
 '45-46-inner-small-to-large-first-no-new-high-exit-smaller-center':['0452-b002','0452-fig1'],
 'thirty-operation-ignore46-47-hold-five-up-until-div-or-break':['0452-b002','0452-fig1'],
 '46-55-five-center55-consolidation-not-true-first-buy57-analogy':['0453-b001','0452-fig1'],
 '55-60-segment-up59-60-div-zero-return-newhigh-weaker-area-height':['0453-b001','0452-fig1'],
 '60-pull-under58-61-lower-new58-61-one-center':['0453-b001','0452-fig1'],
 'new-one-expand-five-and46-touch-key-no46-superstrong-five-up-continues':['0453-b001','0452-fig1'],
 'jun19-from60-one-center4224-4254-below-third-sell-not-price-alone':['0453-b004','0454-fig1'],
 'jun19-above4254-one-third-buy-for-new-up-otherwise-oscillation':['0453-b004','0454-fig1'],
 'jun20-touch46-near4192-center-expand-now-larger-oscillation':['0456-b002','0456-fig1'],
 'jun20-one-return-fail-touch4224-five-third-sell-or-stand-strong':['0456-b002','0456-fig1']};
 for(const [slug,[p,f]] of Object.entries(links)){const es=claim(slug).evidence,target=es.find(e=>e.passage_id==='volume_1-a53e99c37ca5-p'+p);assert.ok(target,slug);assert.deepEqual(target.figure_ids,['volume_1-a53e99c37ca5-p'+f]);assert.equal(target.figures.length,1);for(const e of es)if(e!==target)assert.deepEqual(e.figure_ids,[]);}
 const figs=graph.db.prepare("SELECT id,origin_status,note FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 451 AND 457").all();assert.equal(figs.length,4);assert.equal(figs.filter(f=>f.origin_status==='later_annotation').length,2);assert.match(figs.find(f=>f.id.endsWith('0454-fig1')).note,/6\/21/);
 const ledger=readFileSync(resolve(agent,'curation/upper/c_stage_l060.coverage.jsonl'),'utf8').trim().split('\n').map(JSON.parse);assert.equal(ledger.length,38);assert.equal(new Set(ledger.map(p=>p.passage_id)).size,38);assert.equal(graph.metadata.semantic_completion,false);
 checks.push('38段全台账、13命题13图文关联4整图；2未核2后加，图右B2只画大于而等号由文字给出，原4067.85/重绘4068.20分存，后6/21不证前判断。');
 const anchor=pair.evidence[0].id,requests=[['search',{query:'B2'},['search','B2']],['concept',{id:'走势破坏',limit:10},['concept','走势破坏','--limit','10']],['neighbors',{id:'最低级别',depth:1,limit:100},['neighbors','最低级别','--depth','1','--limit','100']],['evidence',{id:anchor},['evidence',anchor]],['page',{documentId:'volume_1.pdf',page:453},['page','--document-id','volume_1.pdf','--page','453']],['search',{query:'多少分钟的图和多少分钟的级别',scope:'source',limit:3},['search','多少分钟的图和多少分钟的级别','--scope','source','--limit','3']],['coverage',{},['coverage']]];
 const parity=[];for(const [command,args,argv] of requests){const a=JSON.parse(JSON.stringify(graph.query(command,args))),cli=spawnSync(process.execPath,[resolve(agent,'bin/chan-kg.mjs'),...argv,'--kb',root],{encoding:'utf8',maxBuffer:24*1024*1024});assert.equal(cli.status,0,cli.stderr);assert.deepEqual(JSON.parse(cli.stdout),a);parity.push({command,args,cli_matches_shared:true});}
 assert.deepEqual({database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
 const report={graph_version:graph.metadata.graph_version,schema_version:graph.metadata.schema_version,delivery_scope:'shared_knowledge_base_only',checks,parity,intended_figure_links_checked:{claims:13,associations:13,unique_figures:4},database_and_manifest_unchanged:true,pass:true,limits:['同代理四轮不是独立/人类金标准；两册未与原博客逐字核。','60最低级别/消息强语及中枢锚点待核，43/57夹注、54跨页上下文、61课及最终来源覆盖交付审计未完成。','软件构建和交付已排除，现有检索回归/生成回答评价边界仍如实保留。']};writeFileSync(resolve(agent,'curation/source-audit/stage-c-l060-verification.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({graph_version:report.graph_version,boundary_groups:checks.length,parity:parity.length,figure_links:report.intended_figure_links_checked,pass:true}));
}finally{graph.close();}
