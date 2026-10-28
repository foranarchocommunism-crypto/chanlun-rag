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
const claim = slug => { const c = graph.getClaim('upper-l051-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try {
 assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l051-c-stage-%' AND review_status='reviewed'").get().n,37);
 const flow=claim('recommendation-self-reinforcing-flow-hypothetical-numbers');assert.match(flow.text,/假设.*5%.*5000人.*2000股.*1000万股/);assert.notEqual(flow.ambiguity_status,'none');assert.equal(flow.conditions.length,2);
 assert.equal(5000*2000,10000000);assert.match(flow.review_note,/非真实调查.*单位为股非1000万元/);
 assert.notEqual(claim('short-switching-exhausts-outsiders-longer-organization-evolves-author').ambiguity_status,'none');
 assert.match(claim('short-switching-exhausts-outsiders-longer-organization-evolves-author').review_note,/不认定任何具体私募/);
 assert.match(claim('warning-against-paid-tips-author-opinion-not-legal-verdict').review_note,/不证明所有收费服务都是诈骗/);
 assert.match(claim('buy-by-level-point-not-author-target-or-chase').text,/级别买卖点.*不让现在追高/);
 for(const p of ['0372-b004','0372-b005','0372-b006','0372-b007','0374-b009','0377-b007'])assert.equal(graph.db.prepare("SELECT count(*) n FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed' AND e.passage_id=?").get('volume_1-a53e99c37ca5-p'+p).n,0);
 checks.push('37新增；5000人×2000股为1000万股是假设流量非荐股准确率或1000万元，会员/私募演化与收费批评非普遍法律分类，16股表/999洗盘/416涨幅不冒实绩，按级别买点不追对象');

 assert.match(claim('B-needs-third-buy-otherwise-oscillation-consolidation-divergence').text,/B须出现三买.*否则仍围绕B震荡/);
 assert.match(claim('B-needs-third-buy-otherwise-oscillation-consolidation-divergence').review_note,/只明确B.*未逐项认可读者/);
 assert.match(claim('C2-incomplete-no-high-no-confirmed-third-buy').text,/C2未完.*所谈走势类型均须完成/);
 assert.match(claim('C2-incomplete-no-high-no-confirmed-third-buy').review_note,/限该问.*不推广所有走势/);
 assert.match(claim('MACD-first-up-zero-then-sideways-second-buy-auxiliary').review_note,/没有明确周期.*单独定义为所有二买/);
 assert.match(claim('ultrashort-afternoon-third-buy-after-morning-extension-example').review_note,/不是已认可读者午前公式/);
 assert.match(claim('4000-valid-break-center-then-third-buy-failure-third-sell-possible').text,/先形成.*中枢.*三买.*三卖/);
 checks.push('B三买后才结束/否则盘背震荡，不认可整套A/B或只MACD；C2所涉完整走势类型与读者两个中枢不混，未推广任何不新高均未完成，4000中枢后三买仍可三卖失败，午前公式/固定14点未背书');

 assert.match(claim('1429-historical-pressure-model-start-and-first-two-tops').text,/1429\+15×9=1564.*1429\+109×7.5=2246.5/);
 assert.equal(1429+15*9,1564);assert.equal(1429+109*7.5,2246.5);assert.equal(1429+178*7.5,2764);assert.equal(1429+180*15,4129);assert.equal(1429+270*15,5479);
 assert.match(claim('1429-historical-pressure-model-start-and-first-two-tops').review_note,/1558不等1564.*2245不等2246.5.*图1249/);
 assert.notEqual(claim('pressure-rates-360-per-year-fractions-author-basis').ambiguity_status,'none');
 assert.match(claim('pressure-rates-360-per-year-fractions-author-basis').review_note,/未给物理\/统计必然证明/);
 assert.match(claim('half-line-three-scenarios-top-balance-or-strong-break').text,/多头陷阱.*强盘整.*强破.*5479/);
 assert.match(claim('pressure-line-three-months-before-july-claim-market-chooses').text,/至少需3个月.*至少7月前/);
 assert.notEqual(claim('pressure-line-three-months-before-july-claim-market-chooses').ambiguity_status,'none');
 assert.match(claim('half-line-eventual-break-support-author-long-bull-premise').review_note,/非项目验证未来必破/);
 checks.push('1429历史线五个原公式算术一致但历史近似不作数值相等或样本外证明，图1249不修1429；360角到年点速率是作者模型非因果必然，至少3月/7月强时间与最终破线只是历史主张、无伪造概率');

 assert.match(claim('may11-weak-day-branch-expansion-4000-still-needs-third-buy').review_note,/三种指5\/10次日强中弱日内情况.*非.*中期模式/);
 assert.match(claim('may11-weak-day-branch-expansion-4000-still-needs-third-buy').review_note,/扩张原字保留/);
 assert.match(claim('may12-three-patterns-not-preselected-first-by-god').text,/不能认为.*一定选第一种/);
 assert.match(claim('may16-1017-weekly-gap-bottom-divergence-case').review_note,/填周线缺口不等周线背驰/);
 assert.match(claim('oscillation-until-third-points-third-sell-wait-adequate-bottom').text,/三卖后观察.*够级别底背驰/);
 assert.match(claim('may17-4040-key-extension-versus-expansion-conditional').review_note,/不将任何价格站稳当一般扩展充分定义/);
 assert.match(claim('half-line-center-ultimate-level-form-still-forming').text,/最终级别和形式仍在形成/);
 assert.match(claim('direction-by-buy-sell-level-long-bull-until-long-sell').text,/季度线有卖点则转空/);
 checks.push('日内强中弱与中期压力线三模式不混，扩张/扩展原词分开；原震荡三卖停止回补等够级底背，周缺口非周背驰，4040站稳只案例不替一般扩展定义，最终大级别形式仍形成、长期多也有季线卖点退出');

 const plan=JSON.parse(readFileSync(resolve(agent,'curation/source-audit/stage-c-l051-source-plan.json'),'utf8'));assert.equal(plan.operations.length,20);const pops=plan.operations.filter(x=>x.table==='passages');assert.equal(pops.length,16);const dates=pops.filter(op=>op.before.published_at.slice(0,10)!==op.after.published_at.slice(0,10));assert.equal(dates.length,4);
 for(const op of pops){assert.equal(source(op.id.split('-p')[1]).published_at,op.after.published_at);if(!dates.includes(op))assert.equal(op.before.published_at,op.after.published_at.replace(' ',''));}
 assert.equal(source('0373-b004').published_at,'2007-05-10 15:36:28');assert.equal(source('0374-b002').published_at,'2007-05-10 15:36:28');assert.equal(source('0373-b003').published_at,'2007-05-09 15:25:06');
 for(const p of ['0381-b003','0381-b004','0381-b005','0381-b006','0381-b007','0381-b008','0381-b009','0381-b010']){assert.equal(source(p).role,'reader');assert.equal(graph.db.prepare("SELECT count(*) n FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed' AND e.passage_id=?").get('volume_1-a53e99c37ca5-p'+p).n,0);}
 assert.equal(source('0381-b006').speaker,'CCTV');
 const ledger=readFileSync(resolve(agent,'curation/upper/c_stage_l051.coverage.jsonl'),'utf8').trim().split('\n').map(JSON.parse);assert.equal(ledger.length,129);
 assert.notEqual(claim('oscillation-profit-vs-unilateral-author-skill-claim').ambiguity_status,'none');
 assert.match(claim('oscillation-profit-vs-unilateral-author-skill-claim').review_note,/不当本项目回测结果/);
 checks.push('四段5/10日期/12空格规范，前5/9不污染；129段全台账，5/17CCTV600832两段比较与其他读者保持身份无作者证据，政治/私德/收益强语未升实证');

 const links={
  'may9-gap-not-completely-filled-five-day-skill-fallback':['0373-b001',['0373-fig1']],
  'may10-oscillation-above-center-not-only-green-fall':['0373-b004',['0373-fig1']],
  '1429-historical-pressure-model-start-and-first-two-tops':['0375-b011',['0376-fig1']],
  'jan-mar2007-quarter-line-pullback-2764-historical-reading':['0376-b002',['0376-fig1']],
  'half-line-three-scenarios-top-balance-or-strong-break':['0377-b000',['0376-fig1']],
  'may14-4040-day-center-reference-retest-4000':['0379-b003',['0380-fig1']],
  'may15-4040-1046-last-rebound-five-day-break-case':['0379-b009',['0380-fig1']],
  'may16-1017-weekly-gap-bottom-divergence-case':['0380-b008',['0380-fig1']],
 };
 for(const [slug,[p,fs]] of Object.entries(links)){const e=claim(slug).evidence.find(e=>e.passage_id==='volume_1-a53e99c37ca5-p'+p);assert.deepEqual(e.figure_ids,fs.map(f=>'volume_1-a53e99c37ca5-p'+f));assert.ok(e.figures.every(f=>f.origin_status==='later_annotation'));}
 const figs=graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 371 AND 382").all();assert.equal(figs.length,4);assert.ok(figs.every(f=>f.origin_status==='later_annotation'));
 assert.equal(graph.db.prepare("SELECT count(*) n FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed' AND EXISTS(SELECT 1 FROM json_each(e.figure_ids) f WHERE f.value='volume_1-a53e99c37ca5-p0381-fig1')").get().n,0);
 assert.equal(graph.db.prepare("SELECT processing_status FROM units WHERE id='lesson-051'").get().processing_status,'semantic_read_with_pending');assert.equal(graph.metadata.semantic_completion,false);
 checks.push('8命题8关联3作者语境图逐项核，四整图含未来K皆后加；第4图是CCTV读者且无reviewed作者图证，1249/后6124与1429模型分开，模块检查不冒实际Windows验收');

 const anchor=claim('B-needs-third-buy-otherwise-oscillation-consolidation-divergence').evidence[0].id;
 const requests=[['search',{query:'短线荐股'},['search','短线荐股']],['concept',{id:'1429点历史压力线',limit:20},['concept','1429点历史压力线','--limit','20']],['neighbors',{id:'短线荐股',depth:1,limit:100},['neighbors','短线荐股','--depth','1','--limit','100']],['evidence',{id:anchor},['evidence',anchor]],['page',{documentId:'volume_1.pdf',page:381},['page','--document-id','volume_1.pdf','--page','381']],['search',{query:'5160955',scope:'source',limit:8},['search','5160955','--scope','source','--limit','8']],['coverage',{},['coverage']]];
 const parity=[];for(const [command,args,argv] of requests){const a=JSON.parse(JSON.stringify(graph.query(command,args)));assert.deepEqual(JSON.parse(JSON.stringify(desktop.query(command,args))),a);const cli=spawnSync(process.execPath,[resolve(agent,'bin/chan-kg.mjs'),...argv,'--kb',root],{encoding:'utf8',maxBuffer:24*1024*1024});assert.equal(cli.status,0,cli.stderr);assert.deepEqual(JSON.parse(cli.stdout),a);parity.push({command,args,cli_matches_shared:true,desktop_module_matches_shared:true});}
 assert.deepEqual({database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
 const report={graph_version:graph.metadata.graph_version,schema_version:graph.metadata.schema_version,checks,parity,intended_figure_links_checked:{claims:8,associations:8,unique_figures:3,reader_context_figures_not_author_evidence:1},core_sha256:sha(resolve(agent,'src/core.mjs')),desktop_core_sha256:sha(resolve(agent,'../chan-kg-desktop/vendor/core.mjs')),database_and_manifest_unchanged:true,pass:true,limits:['同一模型来源/语义边界与模块一致性，非独立语义/回答质量或真实Windows运行。','荐股流量是作者假设，压力线/360/三个月及收益强语未外部实证，原图1249与正文1429不解决，完成与扩展具体案例全几何未证。','冻结重合前20召回回归仍开放，未改核心排序/金标准规避。']};writeFileSync(resolve(agent,'curation/source-audit/stage-c-l051-verification.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({graph_version:report.graph_version,boundary_groups:checks.length,parity:parity.length,figure_links:report.intended_figure_links_checked,pass:true}));
}finally{graph.close();desktop.close();}
