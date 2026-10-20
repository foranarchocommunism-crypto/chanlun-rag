import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { KnowledgeGraph } from '../../src/core.mjs';
const agent=resolve(dirname(fileURLToPath(import.meta.url)),'../..'),root=resolve(agent,'../shared-knowledge/v0.1.0');
const sha=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const before={database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))};
const graph=new KnowledgeGraph(root),checks=[];
const claim=slug=>{const r=graph.getClaim('upper-l058-c-stage-'+slug);assert.ok(r,slug);return r;};
const source=short=>graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p'+short);
try{
 assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l058-c-stage-%' AND review_status='reviewed'").get().n,35);
 assert.match(claim('inner-five-fold-no-overlap-whole14-15-one-segment').text,/整个14—15仍看作一个向下线段/);
 const early=claim('preprecise-three-fold-gap-exception-nonoverlap-can-extend');assert.notEqual(early.ambiguity_status,'none');assert.match(early.text,/除缺口外至少/);assert.match(early.review_note,/后62至少三笔及67特征序列/);
 assert.match(claim('14-15-force-largest-no-one-minute-plus-divergence').text,/不构成合适买点.*1分钟以上背驰.*最多为1分钟以下/);
 assert.match(claim('15-minimal-green-area-divergence-rebound-last-inner-up').text,/绿柱面积.*最后一个上附近/);
 checks.push('14—15内部箭头五折非独立段而全段仍一段，原三折/缺口例外与后62/67精确说法分层；大力度无1分以上背驰与内最小面积/附近反抽分开。');

 const recent=claim('15-16-third-sell-recent10-13-not-point7');assert.match(recent.text,/最近10—13.*否定.*点7/);assert.equal(recent.conditions.length,1);
 assert.match(claim('third-point-direct-sublevel-leave-return-nearest-center-far').text,/次级别离开、次级别反抽.*最近.*快速/);
 const potential=claim('from16-only-potential-accelerated-fall-can-break-nested-confirm');assert.match(potential.text,/仅可能.*加速下跌.*破坏.*区间套/);
 assert.match(claim('if-divergence-return-at-least15-form-one-center-from15').conditions[0],/背驰成立/);
 checks.push('15—16的1分三卖依据最近10—13和次级离返，点7另一范围不偷换；从16只是可能且加速可破坏，内部区间套确认后才条件回15。');

 assert.match(claim('old1-10-five-center-rebound-not-back-above4015-third-sell').text,/1—10.*4015之上/);
 const broad=claim('below4000-rebound-sell-larger-center-or-fall-author-outlook');assert.match(broad.text,/4000/);assert.equal(broad.exceptions.length,1);assert.match(broad.review_note,/概略历史判断/);
 assert.match(claim('from10-new-five-not-formed-nonoverlap-future-downtrend').text,/尚未形成.*最终.*不重合/);
 assert.match(claim('point7-larger-five-divergence-return-improvement-only-possible').text,/5分钟背驰.*好转可能/);
 assert.match(claim('jun7-break3858-large-center-forming-next4015-conditional').review_note,/正在形成非已经完成/);
 checks.push('旧5分4015与4000概略强语分开；新5分未成且最终不重合才条件下跌，7点好转仍需5分背驰反弹，6/7大枢形成中不冒完成。');

 const plan=JSON.parse(readFileSync(resolve(agent,'curation/source-audit/stage-c-l058-source-plan.json'),'utf8'));assert.equal(plan.operations.length,29);const pops=plan.operations.filter(o=>o.table==='passages');assert.equal(pops.length,25);assert.equal(pops.filter(o=>o.before.role==='reader').length,5);
 for(const op of pops)for(const [k,v] of Object.entries(op.after))assert.equal(source(op.id.split('-p')[1])[k],v);
 assert.equal(source('0438-b003').published_at,'2007-06-05 15:23:01');assert.equal(source('0438-b005').published_at,'2007-06-06 16:52:09');assert.equal(source('0439-b001').published_at,'2007-06-07 15:04:21');assert.equal(source('0439-b002').published_at,'2007-06-08 15:13:42');assert.equal(source('0442-b000').published_at,'2007-06-13 15:49:07');
 for(const p of ['0442-b005','0442-b006','0442-b010','0443-b000','0443-b003','0443-b008']){
  assert.equal(source(p).role,'reader');assert.equal(graph.db.prepare("SELECT count(*) n FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed' AND e.passage_id=?").get('volume_1-a53e99c37ca5-p'+p).n,0);
 }
 checks.push('25段身份/日期逐列核，误reader的5段作者解盘修复；6/6、6/7、6/8、6/13头尾时序/跨页承接正确，真实读者房价/5000传言/10:20操作不入作者证据。');

 assert.match(claim('chart-period-not-move-level-one-chart-can-find-daily-center').text,/1分钟图中也可找日线中枢.*不是一回事/);
 assert.match(claim('objective-move-level-subjective-chart-magnification').text,/走势级别视为客观.*周期图级别是主观选择/);
 assert.match(claim('small-consolidation-divergence-can-resolve-fees-skill-larger-space').text,/小级别盘整背驰.*费用变贵、技术不好.*足够空间/);
 assert.match(claim('jun11-cost-higher-less-frequent-larger-level-five-day-reference').review_note,/当时费用背景/);
 assert.match(claim('missed-buy-three-alternatives-realestate-analogy-personal-choice').review_note,/未在本答确认房价不会跌/);
 assert.match(claim('policy-part-of-force-chart-force-itself-not-news-price-cap').review_note,/5000上限.*未获确认/);
 assert.match(claim('may30-second-sell-jun5-buy-retrospective-not-fill-proof').review_note,/非指数二卖等于所有个股同类/);
 checks.push('图周期/精度与客观走势级别不同，费用/技能限制微小盘背操作；中线/PE策略不泛化定义，星号5%与房价/政策/可成交强语只保历史观点和读者身份。');

 const links={
  'inner-five-fold-no-overlap-whole14-15-one-segment':['0436-b008','0437-fig1'],
  'preprecise-three-fold-gap-exception-nonoverlap-can-extend':['0436-b008','0437-fig1'],
  '14-15-force-largest-no-one-minute-plus-divergence':['0436-b009','0437-fig1'],
  '15-minimal-green-area-divergence-rebound-last-inner-up':['0436-b009','0437-fig1'],
  '15-16-third-sell-recent10-13-not-point7':['0436-b010','0437-fig1'],
  'third-point-direct-sublevel-leave-return-nearest-center-far':['0437-b000','0437-fig1'],
  'from16-only-potential-accelerated-fall-can-break-nested-confirm':['0437-b001','0437-fig1'],
  'if-divergence-return-at-least15-form-one-center-from15':['0437-b001','0437-fig1'],
  'old1-10-five-center-rebound-not-back-above4015-third-sell':['0437-b002','0437-fig1'],
  'from10-new-five-not-formed-nonoverlap-future-downtrend':['0437-b003','0437-fig1'],
  'point7-larger-five-divergence-return-improvement-only-possible':['0437-b003','0437-fig1'],
  'jun5-17-end3404-18-still-watch-ending-center-oscillation':['0438-b001','0438-fig1'],
  'jun6-3858-point7-center-formed-view-oscillation':['0438-b004','0439-fig1'],
  'jun7-break3858-large-center-forming-next4015-conditional':['0438-b006','0439-fig1'],
  'jun12-4015-five-day-retest-next4144-newhigh-conditional-script':['0441-b001','0441-fig1'],
  'jun13-gap-remaining-week-important-shake-required-author-view':['0441-b004','0441-fig1']};
 for(const [slug,[p,f]] of Object.entries(links)){const es=claim(slug).evidence,target=es.find(e=>e.passage_id==='volume_1-a53e99c37ca5-p'+p);assert.ok(target,slug);assert.deepEqual(target.figure_ids,['volume_1-a53e99c37ca5-p'+f]);assert.equal(target.figures.length,1);for(const e of es)if(e!==target)assert.deepEqual(e.figure_ids,[]);}
 const figs=graph.db.prepare("SELECT id,origin_status,note FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 436 AND 443").all();assert.equal(figs.length,4);assert.equal(figs.filter(f=>f.origin_status==='later_annotation').length,2);assert.match(figs.find(f=>f.id.endsWith('0437-fig1')).note,/24\/52\/9/);assert.match(figs.find(f=>f.id.endsWith('0438-fig1')).note,/5分钟.*3404.25/);
 const ledger=readFileSync(resolve(agent,'curation/upper/c_stage_l058.coverage.jsonl'),'utf8').trim().split('\n').map(JSON.parse);assert.equal(ledger.length,72);assert.equal(new Set(ledger.map(p=>p.passage_id)).size,72);assert.equal(graph.metadata.semantic_completion,false);
 checks.push('72段台账与16命题16图文关联4图核对，2未核2后加；原24/52/9与12/26/9、图5分钟与正文走势、3404.25/3404及4016.30/4015分别保，后K不证前日预测。');

 const anchor=recent.evidence[0].id;
 const requests=[['search',{query:'图的级别'},['search','图的级别']],['concept',{id:'私人股权投资',limit:10},['concept','私人股权投资','--limit','10']],['neighbors',{id:'周期K线图',depth:1,limit:100},['neighbors','周期K线图','--depth','1','--limit','100']],['evidence',{id:anchor},['evidence',anchor]],['page',{documentId:'volume_1.pdf',page:438},['page','--document-id','volume_1.pdf','--page','438']],['search',{query:'3858的技术意义在今天',scope:'source',limit:5},['search','3858的技术意义在今天','--scope','source','--limit','5']],['coverage',{},['coverage']]];
 const parity=[];for(const [command,args,argv] of requests){const a=JSON.parse(JSON.stringify(graph.query(command,args))),cli=spawnSync(process.execPath,[resolve(agent,'bin/chan-kg.mjs'),...argv,'--kb',root],{encoding:'utf8',maxBuffer:24*1024*1024});assert.equal(cli.status,0,cli.stderr);assert.deepEqual(JSON.parse(cli.stdout),a);parity.push({command,args,cli_matches_shared:true});}
 assert.deepEqual({database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
 const report={graph_version:graph.metadata.graph_version,schema_version:graph.metadata.schema_version,delivery_scope:'shared_knowledge_base_only',checks,parity,intended_figure_links_checked:{claims:16,associations:16,unique_figures:4},database_and_manifest_unchanged:true,pass:true,limits:['同一代理的来源/条件/图文复核及现有CLI读取一致检查，不是独立或人类金标准。','58早期线段与后精确定义、4000预测强语和实际成交仍待核；43/57混合备注来源拆分、54长编号上下文及全书最终交付审计未完成。','不构建或验收软件产品；冻结检索回归与生成回答评价边界如实保留。']};
 writeFileSync(resolve(agent,'curation/source-audit/stage-c-l058-verification.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({graph_version:report.graph_version,boundary_groups:checks.length,parity:parity.length,figure_links:report.intended_figure_links_checked,pass:true}));
}finally{graph.close();}
