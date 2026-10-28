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
const claim = slug => { const c = graph.getClaim('upper-l050-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try {
 assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l050-c-stage-%' AND review_status='reviewed'").get().n,31);
 assert.match(claim('structure-then-comparable-legs-then-MACD-period').text,/先分析中枢.*选需比较力度.*最后/);
 assert.match(claim('MACD-periods-calculation-sensitivity-not-identical-output').review_note,/不把跨周期采样.*数值完全相同/);
 assert.notEqual(claim('MACD-periods-calculation-sensitivity-not-identical-output').ambiguity_status,'none');
 assert.match(claim('choose-thirty-if-one-complex-two-areas-clearer').text,/1分.*复杂.*30分.*清楚两柱面积/);
 assert.match(claim('choose-thirty-if-one-complex-two-areas-clearer').review_note,/不是将1分信号升级30分/);
 assert.equal(claim('structure-then-comparable-legs-then-MACD-period').conditions.length,2);
 checks.push('31新增；MACD先中枢走势选段再周期辅助，常对应非必同周期，线性为作者说明未冒跨采样无损等值；30图更清楚不把小级信号升级30分');

 assert.match(claim('understand-logic-not-belief-in-author-confidence').text,/反对因相信作者而盲信/);
 assert.match(claim('study-existing-then-record-live-simulations-before-real-trades').text,/已有走势.*模拟.*逐次记录.*复盘.*真买卖/);
 assert.equal(claim('study-existing-then-record-live-simulations-before-real-trades').conditions.length,2);
 assert.match(claim('static-dynamic-actual-learning-sequence-not-days').review_note,/静态看懂不等真实当下无前视偏差/);
 assert.notEqual(claim('method-practice-geometric-profit-guarantee-author-only').ambiguity_status,'none');
 assert.match(claim('method-practice-geometric-profit-guarantee-author-only').review_note,/未给数学证明/);
 assert.match(claim('experience-psychology-and-long-practice-affect-precision').review_note,/不据结果差异反证理论永远正确/);
 checks.push('先静态再动态模拟记录复盘再实操，足够把握未伪造数值门槛；逻辑反盲信与几何保证收益的作者强语分开，未以亏损全归人或已证明理论代替证据');

 assert.match(claim('very-long-pullback-premise-change-may-not-fully-return').text,/特别长.*年线.*交易规则完全改变.*可能不完全回拉/);
 assert.equal(claim('very-long-pullback-premise-change-may-not-fully-return').conditions.length,2);
 assert.match(claim('unchanged-premises-author-certain-pullback-not-proof').text,/前提未变.*一定回拉/);
 assert.notEqual(claim('unchanged-premises-author-certain-pullback-not-proof').ambiguity_status,'none');
 assert.match(claim('unchanged-premises-author-certain-pullback-not-proof').review_note,/未给全前提清单.*回拉时限/);
 assert.match(claim('small-to-large-operate-as-center-oscillation').text,/转大以后.*中枢震荡/);
 assert.equal(source('0368-b010').role,'reader');assert.equal(source('0368-b011').role,'reader');
 checks.push('特别长回拉可因制度/规则改变前提而不完全回拉，前提未变作者仍断言一定，未软成可能也未认证全市场保证；日线读者问题/年线例区分，全前提与时限未补');

 assert.match(claim('five-day-three-days-no-return-usual-imprecise-delayed-confirmation').text,/不精确.*通常三天.*离真正高点远/);
 assert.match(claim('five-day-three-days-no-return-usual-imprecise-delayed-confirmation').review_note,/未答最低触线还是最高低于.*收盘/);
 assert.match(claim('small-funds-under-million-more-than-five-too-many').text,/一般100万以下超过5只/);
 assert.match(claim('small-funds-under-million-more-than-five-too-many').review_note,/不认可读者明日全抛重来/);
 assert.match(claim('997-need-comparable-legs-no-endorsement-form-repeat-rhythm').text,/未说比较哪两段.*不知/);
 assert.match(claim('part-funds-practice-qualified-not-every-reader-detail').review_note,/不逐项认可读者.*天天满仓/);
 assert.match(claim('short-five-day-medium-five-week-higher-skill-divergence-not-gap-guess').review_note,/45单边非盘整/);
 checks.push('5日三天为通常不精确延迟法非最低/最高/收盘完整定义，和47缺口三天不同对象；100万以下超5只仅一般能力建议，997未认可具体卖点，部分练不背书天天满仓等整套读者计划');

 assert.match(claim('five-minute-moving-no-new-five-center-until-it-ends').text,/尚未出现5分中枢.*出现则这次移动结束/);
 assert.match(claim('one-down-next-one-up-divergence-or-no-high-can-exit-before-five-center').text,/1分走势向下.*1分向上.*背驰或不创新高.*将成5分中枢/);
 assert.equal(claim('one-down-next-one-up-divergence-or-no-high-can-exit-before-five-center').conditions.length,3);
 assert.match(claim('one-down-next-one-up-divergence-or-no-high-can-exit-before-five-center').review_note,/将形成不等此刻.*已完/);
 assert.match(claim('framework-before-orderbook-details-promised-not-provided').text,/留以后讲/);
 const plan=JSON.parse(readFileSync(resolve(agent,'curation/source-audit/stage-c-l050-source-plan.json'),'utf8'));assert.equal(plan.operations.length,30);assert.equal(plan.operations.filter(x=>x.table==='passages').length,28);
 for(const op of plan.operations.filter(x=>x.table==='passages')){assert.equal(source(op.id.split('-p')[1]).published_at,op.after.published_at);assert.equal(op.before.published_at,op.after.published_at.replace(' ',''));}
 assert.equal(source('0365-b007').role,'reader');assert.equal(source('0365-b007').speaker,'CCTV');
 const selected=claim('switching-needs-skill-strength-otherwise-focus').evidence[0];assert.ok(!selected.quote.includes('999')&&!selected.quote.includes('基金'));
 for(const p of ['0365-b009','0365-b010','0365-b011','0365-b012','0366-b002','0366-b003','0367-b000','0367-b001','0368-b008','0370-b005'])assert.equal(graph.db.prepare("SELECT count(*) n FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed' AND e.passage_id=?").get('volume_1-a53e99c37ca5-p'+p).n,0);
 const ledger=readFileSync(resolve(agent,'curation/upper/c_stage_l050.coverage.jsonl'),'utf8').trim().split('\n').map(JSON.parse);assert.equal(ledger.length,105);
 checks.push('新5分枢将成与已完成分开，完整1分先下后上/背驰或不新高不可改AND；盘口细节只预告，28时间只空格，105段含两篇非技术附文，CCTV九段不冒作者证明，999盈利/基金指控被引文边界排除');

 const links={
  'apr27-break-3745-no-third-buy-oscillation':['0364-b003',['0364-fig1']],
  'apr27-afternoon-compare-apr26-0930-MACD-no-new-high-sell':['0364-b003',['0364-fig1']],
  'apr27-five-center-expanded-thirty-3720-3761':['0365-b000',['0364-fig1']],
  'may8-gap-volume-strong-balance-not-as-strong-as-appearance':['0367-b003',['0367-fig1']],
  'short-five-day-medium-five-week-higher-skill-divergence-not-gap-guess':['0367-b004',['0367-fig1']],
 };
 for(const [slug,[p,fs]] of Object.entries(links)){const e=claim(slug).evidence.find(e=>e.passage_id==='volume_1-a53e99c37ca5-p'+p);assert.deepEqual(e.figure_ids,fs.map(f=>'volume_1-a53e99c37ca5-p'+f));assert.ok(e.figures.every(f=>f.origin_status==='later_annotation'));}
 assert.equal(graph.db.prepare("SELECT processing_status FROM units WHERE id='lesson-050'").get().processing_status,'semantic_read_with_pending');assert.equal(graph.metadata.semantic_completion,false);
 checks.push('5命题5关联2整图逐项核，4/30与5/9后K不认证早前文字或预测；原3720/3761不按图小数改，模块一致性不冒实际Windows或全书完成');

 const anchor=claim('very-long-pullback-premise-change-may-not-fully-return').evidence[0].id;
 const requests=[['search',{query:'理论成立前提'},['search','理论成立前提']],['concept',{id:'模拟操作',limit:20},['concept','模拟操作','--limit','20']],['neighbors',{id:'理论成立前提',depth:1,limit:100},['neighbors','理论成立前提','--depth','1','--limit','100']],['evidence',{id:anchor},['evidence',anchor]],['page',{documentId:'volume_1.pdf',page:369},['page','--document-id','volume_1.pdf','--page','369']],['search',{query:'3天拉不回来',scope:'source',limit:8},['search','3天拉不回来','--scope','source','--limit','8']],['coverage',{},['coverage']]];
 const parity=[];for(const [command,args,argv] of requests){const a=JSON.parse(JSON.stringify(graph.query(command,args)));assert.deepEqual(JSON.parse(JSON.stringify(desktop.query(command,args))),a);const cli=spawnSync(process.execPath,[resolve(agent,'bin/chan-kg.mjs'),...argv,'--kb',root],{encoding:'utf8',maxBuffer:24*1024*1024});assert.equal(cli.status,0,cli.stderr);assert.deepEqual(JSON.parse(cli.stdout),a);parity.push({command,args,cli_matches_shared:true,desktop_module_matches_shared:true});}
 assert.deepEqual({database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
 const report={graph_version:graph.metadata.graph_version,schema_version:graph.metadata.schema_version,checks,parity,intended_figure_links_checked:{claims:5,associations:5,unique_figures:2},core_sha256:sha(resolve(agent,'src/core.mjs')),desktop_core_sha256:sha(resolve(agent,'../chan-kg-desktop/vendor/core.mjs')),database_and_manifest_unchanged:true,pass:true,limits:['同模型边界/来源与模块一致检查，不代独立语义/回答质量或Windows实际运行。','理论全前提/回拉期限及保证未独立证明，MACD跨采样公式/均线三天完整判定与实时执行细节未补。','冻结重合前20召回回归未通过修改金标准/核心排序规避。']};writeFileSync(resolve(agent,'curation/source-audit/stage-c-l050-verification.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({graph_version:report.graph_version,boundary_groups:checks.length,parity:parity.length,figure_links:report.intended_figure_links_checked,pass:true}));
}finally{graph.close();desktop.close();}
