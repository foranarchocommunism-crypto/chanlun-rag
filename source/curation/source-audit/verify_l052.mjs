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
const claim = slug => { const c = graph.getClaim('upper-l052-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try {
 assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l052-c-stage-%' AND review_status='reviewed'").get().n,39);
 const literal=claim('literal-divergence-level-not-smaller-than-turn-level-unresolved');assert.match(literal.text,/一定不小于/);assert.match(source('0383-b002').text,/背驰的级别一定不小于转折的级别/);assert.notEqual(literal.ambiguity_status,'none');assert.match(literal.review_note,/不静修为不大于/);
 assert.match(claim('thirty-top-divergence-exit-own-down-or-above-consolidation-author').text,/30分钟级别以上的盘整/);
 assert.match(claim('thirty-top-divergence-exit-own-down-or-above-consolidation-author').review_note,/不静改为严格大于.*与49/);
 assert.match(claim('basic-patterns-predictable-price-formed-in-present-author-view').review_note,/非点位\/时间预报已验证/);
 assert.match(claim('prediction-includes-observers-not-independent-clockwork').review_note,/量子力学只作类比/);
 assert.notEqual(claim('multi-level-isomorphic-patterns-mental-structure-religious-analogy').ambiguity_status,'none');
 checks.push('39新增；原不小于/30级别以上盘整字面与跨课作用域张力不修，不冒无争议总规则；观察参与/固定级别和模式预测与精确未来点价分开，量子/宗教类比不作物理心理证明');

 assert.match(claim('near-opposite-points-use-large-unless-skilled-exit-room').text,/很接近.*看大级.*除非.*退出空间/);
 assert.equal(claim('near-opposite-points-use-large-unless-skilled-exit-room').conditions.length,2);
 assert.match(claim('match-intended-level-to-volatility-tolerance').text,/只能忍受小级波动则按小级/);
 assert.match(claim('precise-five-completion-needs-one-chart-only-five-enlarge-base').text,/精确判断5分走势完成需1分图.*只有5分图.*最小级/);
 assert.match(claim('precise-five-completion-needs-one-chart-only-five-enlarge-base').review_note,/与49\/50.*辅助场景分开/);
 assert.match(claim('may21-fast-market-channel-no-exact-low-guarantee').text,/准备不足或通道慢.*买不到精确位置/);
 assert.match(claim('may21-1040-second-buy-first-retest-zero-on-one-MACD').review_note,/须结构与级别联查/);
 checks.push('相反大小点接近非同一点，大级优先而小级须有退出空间；精确5分完成须1分形态和较大MACD辅助小信号不同范围，通道慢/快市可买不到精确点，10:40二买不单靠柱线定义');

 assert.match(claim('third-points-both-leave-retest-sublevel-one-child-center-not-safe').text,/离开和回试都必须次级别.*一个次级中枢.*岛型反转/);
 assert.match(claim('third-points-both-leave-retest-sublevel-one-child-center-not-safe').review_note,/走势类型不等只数次级中枢/);
 assert.match(claim('leaving-child-center-can-be-within-parent-context-affirmation').text,/离开段的次级中枢可在原中枢内/);
 assert.match(claim('leaving-child-center-can-be-within-parent-context-affirmation').review_note,/仅明确离开段子枢可在内/);
 assert.match(claim('price-outside-center-leaves-usual-return-third-point-not-pulled-back').review_note,/不等之后永远绝不回/);
 assert.notEqual(claim('third-buy-larger-oscillation-close-to-first-sell-size-and-exit-room').ambiguity_status,'none');
 assert.match(claim('same-level-decomposition-associativity-standard-high-low-joints').review_note,/不等任何未调整原分解/);
 assert.match(claim('extension-first-three-range-later-oscillation-five-thirty-decomposition').text,/前三段区间.*5分和30分.*不同/);
 checks.push('离开/回试须次级走势类型，子中枢不等走势全波动，单个上方子枢不保安全；可在内仅离开段，抽不回限该次级回试非永不回，三买后可转大；结合律可归标准非任意原接点自动高低，延伸前三段与全波动分开');

 assert.match(claim('600216-not-may18-1000-thirty-third-buy-use-five-subtypes').text,/否认.*5月18日10:00.*至少由三段1分走势类型/);
 const yes=claim('600216-may17-1455-author-yes-to-reader-two-legs');assert.equal(yes.evidence[0].quote,'对');assert.notEqual(yes.ambiguity_status,'none');
 const ref=yes.evidence[0].context.find(p=>p.id==='volume_1-a53e99c37ca5-p0395-b000');assert.ok(ref);assert.equal(ref.role,'reader');assert.match(ref.text,/05161020~05171010.*05171010~05171455/);assert.equal(yes.evidence[0].role,'author_reply');
 assert.match(yes.review_note,/时刻来自紧前读者.*不是|时刻来自紧前读者.*非把读者/);
 assert.match(claim('second-buy-thirty-first-five-up-five-retest-no-low-second-leg').text,/30分一买后.*5分.*回试不破低点.*第二段/);
 assert.match(claim('second-buy-thirty-first-five-up-five-retest-no-low-second-leg').review_note,/不凭读者.*A1或A3/);
 assert.match(claim('all-points-root-first-first-root-divergence-not-same-level-collapse').review_note,/不将所有同级二三买静改成同级一买/);
 checks.push('600216先否5/18 10:00，5/17 14:55只由作者对明确认可紧前读者两段，API原引只对/上下文保reader；二买30一买后5上5回不破在次级第二段，不硬填A1/A3，根于一类不合并同级标签');

 const plan=JSON.parse(readFileSync(resolve(agent,'curation/source-audit/stage-c-l052-source-plan.json'),'utf8'));assert.equal(plan.operations.length,63);const pops=plan.operations.filter(x=>x.table==='passages');assert.equal(pops.length,53);const dates=pops.filter(op=>op.before.published_at.slice(0,10)!==op.after.published_at.slice(0,10));assert.equal(dates.length,3);
 for(const op of pops){assert.equal(source(op.id.split('-p')[1]).published_at,op.after.published_at);if(!dates.includes(op))assert.equal(op.before.published_at,op.after.published_at.replace(' ',''));}
 assert.equal(source('0390-b001').published_at,'2007-05-21 15:42:35');assert.equal(source('0390-b002').published_at,'2007-05-22 15:28:48');assert.equal(source('0390-b004').published_at,'2007-05-22 15:28:48');
 for(const p of ['0386-b005','0386-b009','0387-b000','0392-b005','0392-b007']){assert.equal(source(p).role,'reader');assert.equal(graph.db.prepare("SELECT count(*) n FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed' AND e.passage_id=?").get('volume_1-a53e99c37ca5-p'+p).n,0);}
 for(const p of ['0387-b002','0387-b003','0387-b004','0388-b000','0388-b001','0388-b002','0388-b003','0390-b004','0394-b005','0395-b006'])assert.equal(graph.db.prepare("SELECT count(*) n FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed' AND e.passage_id=?").get('volume_1-a53e99c37ca5-p'+p).n,0);
 assert.ok(!claim('skill-fallback-five-ten-week-and-five-day-kiss').evidence.find(e=>e.passage_id.endsWith('0390-b000')).quote.includes('铜矿'));
 assert.ok(!claim('novice-coarser-view-strong-large-up-sell-to-rebuy').evidence[0].quote.includes('500%'));
 const ledger=readFileSync(resolve(agent,'curation/upper/c_stage_l052.coverage.jsonl'),'utf8').trim().split('\n').map(JSON.parse);assert.equal(ledger.length,150);
 checks.push('三段5/22日期与50空格规范，前5/21不污染，150段全台账；CCTV600279/802/569保持reader，政策/医学比喻/铜矿内幕/绩效与监管自述不作新事实，技术引文切掉无关股票涨幅/铜矿话');

 const links={
  'may18-1326-compare-two-down-legs-one-MACD-nesting':['0384-b001',['0384-fig1']],
  'may21-fourth-thirty-bar-4050-unilateral-interval-branches':['0388-b004',['0389-fig1','0389-fig2']],
  'may22-4129-first-cross-does-not-exclude-first-top-scenario':['0390-b002',['0389-fig1','0389-fig2']],
  'may21-fast-market-channel-no-exact-low-guarantee':['0390-b008',['0391-fig1','0391-fig2']],
  'may21-1040-second-buy-first-retest-zero-on-one-MACD':['0390-b008',['0391-fig1','0391-fig2']],
  '600216-not-may18-1000-thirty-third-buy-use-five-subtypes':['0394-b009',['0394-fig1']],
  '600216-may17-1455-author-yes-to-reader-two-legs':['0395-b001',['0395-fig1']],
 };
 for(const [slug,[p,fs]] of Object.entries(links)){const e=claim(slug).evidence.find(e=>e.passage_id==='volume_1-a53e99c37ca5-p'+p);assert.deepEqual(e.figure_ids,fs.map(f=>'volume_1-a53e99c37ca5-p'+f));assert.equal(e.figures.length,fs.length);}
 const figs=graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 382 AND 396").all();assert.equal(figs.length,10);assert.equal(figs.filter(f=>f.origin_status==='later_annotation').length,5);
 for(const f of ['0386-fig1','0387-fig1','0392-fig1'])assert.equal(graph.db.prepare("SELECT count(*) n FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed' AND EXISTS(SELECT 1 FROM json_each(e.figure_ids) f WHERE f.value=?)").get('volume_1-a53e99c37ca5-p'+f).n,0);
 assert.equal(graph.db.prepare("SELECT processing_status FROM units WHERE id='lesson-052'").get().processing_status,'semantic_read_with_pending');assert.equal(graph.metadata.semantic_completion,false);
 checks.push('7命题11关联7图逐项核，10整图5后加5当时可得但原发未核；另3幅CCTV图无作者证据，未来K不证预测，模块一致非真实Windows/全书验收');

 const anchor=yes.evidence[0].id;
 const requests=[['search',{query:'岛型反转'},['search','岛型反转']],['concept',{id:'第三类买卖点',limit:20},['concept','第三类买卖点','--limit','20']],['neighbors',{id:'岛型反转',depth:1,limit:100},['neighbors','岛型反转','--depth','1','--limit','100']],['evidence',{id:anchor},['evidence',anchor]],['page',{documentId:'volume_1.pdf',page:395},['page','--document-id','volume_1.pdf','--page','395']],['search',{query:'05171010~05171455',scope:'source',limit:8},['search','05171010~05171455','--scope','source','--limit','8']],['coverage',{},['coverage']]];
 const parity=[];for(const [command,args,argv] of requests){const a=JSON.parse(JSON.stringify(graph.query(command,args)));assert.deepEqual(JSON.parse(JSON.stringify(desktop.query(command,args))),a);const cli=spawnSync(process.execPath,[resolve(agent,'bin/chan-kg.mjs'),...argv,'--kb',root],{encoding:'utf8',maxBuffer:24*1024*1024});assert.equal(cli.status,0,cli.stderr);assert.deepEqual(JSON.parse(cli.stdout),a);parity.push({command,args,cli_matches_shared:true,desktop_module_matches_shared:true});}
 assert.deepEqual({database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
 const report={graph_version:graph.metadata.graph_version,schema_version:graph.metadata.schema_version,checks,parity,intended_figure_links_checked:{claims:7,associations:11,unique_figures:7,reader_context_figures_not_author_evidence:3},core_sha256:sha(resolve(agent,'src/core.mjs')),desktop_core_sha256:sha(resolve(agent,'../chan-kg-desktop/vendor/core.mjs')),database_and_manifest_unchanged:true,pass:true,limits:['同模型范围/指代/来源与模块一致检查，非独立语义或实际Windows运行。','不小于及30以上盘整原字跨课张力未统一；哲学/预测绝对性与全金融/执行未实证，三买类型完成/次级分解等值仍待核。','冻结重合前20召回回归保持开放，未改核心排序或金标准规避。']};writeFileSync(resolve(agent,'curation/source-audit/stage-c-l052-verification.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({graph_version:report.graph_version,boundary_groups:checks.length,parity:parity.length,figure_links:report.intended_figure_links_checked,pass:true}));
}finally{graph.close();desktop.close();}
