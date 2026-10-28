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
const claim = slug => { const c = graph.getClaim('upper-l055-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try {
 assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l055-c-stage-%' AND review_status='reviewed'").get().n,39);
 assert.match(claim('cash-chip-exchange-asymmetric-time-irreversible-nominal-money').text,/名义钱额.*时间不可逆/);assert.notEqual(claim('cash-chip-exchange-asymmetric-time-irreversible-nominal-money').ambiguity_status,'none');assert.match(claim('cash-chip-exchange-asymmetric-time-irreversible-nominal-money').review_note,/不推广为购买力/);
 assert.match(claim('buy-before-mature-sell-climax-timing-metaphor-not-physiology').review_note,/不作生理学或性别能力事实/);
 const retail=claim('retail-daily-or-above-can-wait-second-or-third-buy'),scale=claim('scale-or-training-start-at-least-second-use-oscillation-learn-stock');assert.equal(retail.conditions.length,2);assert.equal(scale.conditions.length,2);assert.match(retail.text,/不必都在一买.*二买.*三买/);assert.match(scale.text,/资金规模.*至少从二买/);
 assert.match(claim('stock-character-frequency-amplitude-complexity-with-common-center-patterns').text,/频率、幅度、形态复杂度/);assert.notEqual(claim('good-base-entry-cost-below-area-rise-cost-only-decreases-author-ideal').ambiguity_status,'none');
 checks.push('39新增；买卖非同构为名义现金/时间模型而非购买力或金融定理证明，成人同构修辞不作生理性别事实；散户日线以上可二三买与规模/训练至少二买各保前提，股性频幅复杂度非恒定参数，理想建仓降本非市场自动保证');

 const assoc=claim('association-A-still-center-B-complete-subtype-retest-complete-third');assert.match(assoc.text,/A仍须.*B是完成次级走势.*回试段是否次级完成/);assert.equal(assoc.conditions.length,2);assert.match(assoc.review_note,/不静补统一\+1索引/);
 const compare=claim('two-decomposition-MACD-comparisons-author-approval-d4-both-divergence');assert.match(compare.text,/g3d4与g2d3.*g3d4与g1d2.*d4为背驰点/);assert.equal(compare.conditions.length,2);assert.match(compare.evidence[0].quote,/^对的，这里/);
 const ref=compare.evidence[0].context.find(p=>p.id==='volume_1-a53e99c37ca5-p0414-b009');assert.ok(ref);assert.equal(ref.role,'reader');assert.match(ref.text,/g3d4和g2d3.*g3d4和g1d2/);assert.equal(compare.evidence[0].role,'author_reply');
 const disagree=claim('decomposition-strength-disagreement-only-valid-minimum-return-not-both');assert.match(disagree.text,/可能不一致.*后段力度居前两段之间.*不必达到另一不成立分解/);assert.match(disagree.review_note,/不一定.*不能.*全部回抽目标同时保证/);
 checks.push('A保原级中枢、B和回试均完整次级，结合律不自动给+1统一起点；两解比较细式留reader且作者对的明确认可，原引只作者答；后段力度居前两段之间时可不一致，不同时保证所有分解回抽最低幅度');

 assert.match(claim('rebuy-only-when-technically-allowed-do-not-chase-after-missed').text,/在技术允许时买回.*不要等再冲高才追高/);
 assert.match(claim('capital-channel-time-decide-own-style-level-not-small-fund-total-ban').text,/资金量、通道、操作时间/);assert.match(claim('capital-channel-time-decide-own-style-level-not-small-fund-total-ban').review_note,/不立一切小资金任何中枢震荡都禁做/);
 assert.match(claim('profits-for-family-gradual-principal-consumption-withdrawal').text,/逐步提取本金及该消费的钱/);assert.notEqual(claim('profits-for-family-gradual-principal-consumption-withdrawal').ambiguity_status,'none');
 assert.match(claim('withdraw-principal-not-clear-all-cash-safety-first').text,/并非要求清仓/);assert.match(claim('withdraw-principal-not-clear-all-cash-safety-first').review_note,/不将非清仓误改永不空仓/);
 assert.match(source('0418-b009').text,/日线出现背弛.*最多就是一些30分钟的背弛/);assert.match(claim('daily-divergence-clear-vs-thirty-divergence-center-oscillation').review_note,/读者再不空仓并未获无条件认可/);
 checks.push('技术允许才回补非卖后无条件追高；资金通道时间定个体级别，作者对的非小资一律禁震荡；逐步本金/消费款提取与清仓、永不空仓不同，日线背弛与30分处理保持级别及原字，不等盈利筹码免风险');

 assert.match(claim('increased-costs-minimum-five-even-thirty-plus-level').text,/最低至少5分甚至30分以上/);assert.match(claim('increased-costs-minimum-five-even-thirty-plus-level').review_note,/不是理论最小级别/);
 assert.match(claim('unexpected-event-may-confirm-existing-thirty-top-leg-then-current-points').text,/极可能.*逐步确认买卖点/);assert.match(claim('unexpected-event-may-confirm-existing-thirty-top-leg-then-current-points').review_note,/不是5\/29尾盘当时已完成确认/);
 assert.match(source('0420-b002').text,/05300947/);assert.match(source('0422-b006').text,/9点48/);assert.notEqual(claim('may30-miss-first-second-sell-0947-author-not-guaranteed-fill').ambiguity_status,'none');
 assert.match(claim('may30-miss-first-second-sell-0947-author-not-guaranteed-fill').review_note,/不会错过.*不等所有资产T\+1\/跌停\/容量下保证成交/);
 assert.match(claim('thirty-top-pressure-at-least-one-bottom-for-strong-rebound-higher-buy-points').text,/至少需1分底背驰.*5分、30分.*重新走出买点/);
 assert.match(claim('five-third-buy-cannot-offset-thirty-top-daily-author-conditional-answer').text,/5分三买斗不过30分顶背驰、日线的则没问题/);assert.equal(claim('five-third-buy-cannot-offset-thirty-top-daily-author-conditional-answer').conditions.length,2);assert.notEqual(claim('five-third-buy-cannot-offset-thirty-top-daily-author-conditional-answer').ambiguity_status,'none');
 assert.notEqual(claim('unexpected-events-position-cost-control-zero-cost-tool-author').ambiguity_status,'none');assert.notEqual(claim('low-held-profit-zero-cost-can-use-second-third-exit-author-claim').ambiguity_status,'none');
 checks.push('成本上升提高5/30操作门槛不改理论最小级，原已背驰段/极可能突发确认不等前日已可一卖；09:47与下课9点48分别保，二卖不会错过/0成本安全/日线没问题留作者强语，T+1跌停成交与实盘免回撤未证，至少1分反弹非大底已完成');

 assert.match(claim('half-line-june-4144-daily-not-week-month-at-least-three-months').text,/4129.*4144.*不保证周\/月.*至少3个月.*但市场未必走出/);
 assert.match(claim('may30-month-shape-half-line-at-least-three-months-three-scenarios-open').text,/长上阴.*至少影响3个月.*尚未最后确认/);assert.match(source('0419-b003').text,/月线留下长上阴/);
 assert.match(claim('may28-gap-balance-next-three-day-pressure-not-universal-gap-law').review_note,/不是50\/53破5日线三天规则/);
 assert.match(claim('thirty-top-return-may8-21-thirty-center-for-future-oscillation').text,/5月8日至21日/);
 for(const p of ['0414-b009','0414-b012','0415-b000','0418-b001','0418-b004','0418-b008','0422-b002']){assert.equal(source(p).role,'reader');assert.equal(graph.db.prepare("SELECT count(*) n FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed' AND e.passage_id=?").get('volume_1-a53e99c37ca5-p'+p).n,0);}
 for(const p of ['0412-b001','0412-b002','0413-b005','0414-b001','0415-b006','0415-b009','0416-b001','0416-b002','0418-b011','0418-b012','0419-b000','0419-b006'])assert.equal(graph.db.prepare("SELECT count(*) n FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed' AND e.passage_id=?").get('volume_1-a53e99c37ca5-p'+p).n,0);
 assert.equal(claim('reduce-on-sell-rebuy-at-appropriate-buy-not-fixed-portfolio-proof').evidence[0].quote.includes('指引'),false);
 assert.notEqual(claim('macro-bull-change-only-economic-retreat-author-historical-view').ambiguity_status,'none');
 checks.push('历史1/2线六月4144、日周月确认不同，至少3月确认与至少3月影响非一回事；理想路径未必/三模式未定，缺口三天非均线三天，长上阴原字保；读者公式/操作亏损/不空仓没升作者，法律草案/内幕时点/70-5-25自述及生理比喻未作事实证明');

 const links={
 'may28-gap-balance-next-three-day-pressure-not-universal-gap-law':['0413-b003','0417-fig1'],
 'half-line-june-4144-daily-not-week-month-at-least-three-months':['0413-b004','0420-fig1'],
 'may29-balance-first-three-thirty-bars-4323-support-4300-center':['0416-b006','0417-fig1'],
 'may30-adjustment-from-feb6-2541-half-line-shenzhen-13700':['0421-b001','0420-fig1'],
 'thirty-top-return-may8-21-thirty-center-for-future-oscillation':['0421-b002','0421-fig1'],
 };
 for(const [slug,[p,f]] of Object.entries(links)){const es=claim(slug).evidence;const e=es.find(e=>e.passage_id==='volume_1-a53e99c37ca5-p'+p);assert.deepEqual(e.figure_ids,['volume_1-a53e99c37ca5-p'+f]);assert.equal(e.figures.length,1);for(const other of es)if(other!==e)assert.deepEqual(other.figure_ids,[]);}
 const figs=graph.db.prepare("SELECT id,origin_status,note FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 412 AND 422").all();assert.equal(figs.length,3);assert.ok(figs.every(f=>f.origin_status==='later_annotation'));assert.match(figs.find(f=>f.id.endsWith('0420-fig1')).note,/右端已到7月/);assert.match(figs.find(f=>f.id.endsWith('0421-fig1')).note,/5\/9.*5\/8/);
 assert.ok(claim('may30-miss-first-second-sell-0947-author-not-guaranteed-fill').evidence.every(e=>e.figure_ids.length===0));
 const plan=JSON.parse(readFileSync(resolve(agent,'curation/source-audit/stage-c-l055-source-plan.json'),'utf8'));assert.equal(plan.operations.length,24);const pops=plan.operations.filter(op=>op.table==='passages');assert.equal(pops.length,21);for(const op of pops){assert.deepEqual(Object.keys(op.after),['published_at']);assert.equal(op.before.published_at,op.after.published_at.replace(' ',''));assert.equal(source(op.id.split('-p')[1]).published_at,op.after.published_at);}
 const ledger=readFileSync(resolve(agent,'curation/upper/c_stage_l055.coverage.jsonl'),'utf8').trim().split('\n').map(JSON.parse);assert.equal(ledger.length,107);assert.equal(new Set(ledger.map(p=>p.passage_id)).size,107);assert.equal(graph.metadata.semantic_completion,false);
 checks.push('5命题5关联3图逐项核且全后加：两30分含6/4、日线选5/30但含7月，1249/1429与框5/9/正文5/8各保；日线图未附09:47定位命题，21时间空格/3图备注授权变化，107段全台账不称全书或真实产品验收');

 const anchor=compare.evidence[0].id;
 const requests=[['search',{query:'本金提取'},['search','本金提取']],['concept',{id:'股性',limit:20},['concept','股性','--limit','20']],['neighbors',{id:'本金提取',depth:1,limit:100},['neighbors','本金提取','--depth','1','--limit','100']],['evidence',{id:anchor},['evidence',anchor]],['page',{documentId:'volume_1.pdf',page:414},['page','--document-id','volume_1.pdf','--page','414']],['search',{query:'05300947',scope:'source',limit:8},['search','05300947','--scope','source','--limit','8']],['coverage',{},['coverage']]];
 const parity=[];for(const [command,args,argv] of requests){const a=JSON.parse(JSON.stringify(graph.query(command,args)));assert.deepEqual(JSON.parse(JSON.stringify(desktop.query(command,args))),a);const cli=spawnSync(process.execPath,[resolve(agent,'bin/chan-kg.mjs'),...argv,'--kb',root],{encoding:'utf8',maxBuffer:24*1024*1024});assert.equal(cli.status,0,cli.stderr);assert.deepEqual(JSON.parse(cli.stdout),a);parity.push({command,args,cli_matches_shared:true,desktop_module_matches_shared:true});}
 assert.deepEqual({database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
 const report={graph_version:graph.metadata.graph_version,schema_version:graph.metadata.schema_version,checks,parity,intended_figure_links_checked:{claims:5,associations:5,unique_figures:3},core_sha256:sha(resolve(agent,'src/core.mjs')),desktop_core_sha256:sha(resolve(agent,'../chan-kg-desktop/vendor/core.mjs')),database_and_manifest_unchanged:true,pass:true,limits:['同模型语义边界/来源/指代和模块一致检查，非独立或人类金标准/真实Windows交付运行。','作者0成本安全/二卖/日线没问题强语、三类完成/双分解等值、宏观法律自述和09:47/9点48范围仍待核。','3幅后加图不是当时预测证明；跨页编号context未修，冻结召回回归/完整G及产品交付未完成。']};
 writeFileSync(resolve(agent,'curation/source-audit/stage-c-l055-verification.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({graph_version:report.graph_version,boundary_groups:checks.length,parity:parity.length,figure_links:report.intended_figure_links_checked,pass:true}));
}finally{graph.close();desktop.close();}
