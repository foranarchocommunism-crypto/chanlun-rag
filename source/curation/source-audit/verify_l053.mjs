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
const claim = slug => { const c = graph.getClaim('upper-l053-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try {
 assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l053-c-stage-%' AND review_status='reviewed'").get().n,30);
 assert.match(source('0397-b005').text,/并触及该级别的第一类买卖点/);
 assert.match(source('0397-b005').text,/没有该级别的第一类买卖点/);
 const literal=claim('literal-bing-chuji-versus-no-same-level-first-point-unresolved');assert.notEqual(literal.ambiguity_status,'none');assert.match(literal.review_note,/不改并未触及或并不触及/);
 assert.match(source('0398-b001').text,/并一定要参与/);
 assert.notEqual(claim('literal-bing-yiding-participation-and-skilled-capacity-context').ambiguity_status,'none');
 assert.equal(claim('literal-bing-yiding-participation-and-skilled-capacity-context').evidence[0].quote.includes('并不一定要'),false);
 checks.push('30新增；PDF397并触及与同段没有该级别一类、398并一定要原字均保留，歧义标识和原引可见，不暗补未/不或造无条件操作规则');

 const lines=claim('thirty-view-completed-five-moves-as-unstructured-lines');assert.match(lines.text,/已完成的5分走势/);assert.equal(lines.evidence.length,2);assert.match(lines.review_note,/不直接等于后来特征序列/);
 assert.match(claim('one-level-regroup-extremes-not-all-finer-level-endpoints').review_note,/不证明任意原始接点天然极值/);
 assert.match(claim('switch-magnification-for-divergence-leg-and-third-point').text,/进入背驰段.*区间套.*第三类点.*5分/);
 assert.match(claim('a-B-c-both-legs-viewed-as-B-oscillation-retrospective').text,/a发生时B尚未出现/);
 assert.match(claim('three-one-minute-bars-overlap-not-center-unless-lowest-assumption').text,/若不把1分视为最低级别.*三根单位K线重叠也不等有中枢/);
 assert.match(claim('three-one-minute-bars-overlap-not-center-unless-lowest-assumption').review_note,/不将读者无重叠即永无1分趋势/);
 checks.push('完成次级线段化是所选视角而非新结构线段定义，1分重组不使所有分笔原端点相同，固定操作不禁止背驰/三类点下钻；a发生时B未出现不能倒作当时已知，三根K重叠不能替非最低级递归中枢');

 assert.match(claim('all-three-root-first-at-different-levels-not-same-label').text,/不同级别.*同一级别上保留三类区别/);
 assert.match(claim('reaction-time-costs-require-coarser-level-three-equally-important').text,/反应时间.*交易成本.*同一级别的三类点都重要/);
 const second=claim('second-sell-sublevel-down-up-no-new-high-or-consolidation-divergence');assert.match(second.text,/向下.*向上.*不创新高或盘整背驰/);assert.equal(second.conditions.length,2);assert.equal(second.exceptions.length,1);
 assert.match(claim('first-best-when-present-second-best-small-to-large-no-first').text,/没有该级别一类点.*二类成为最佳/);
 const larger=claim('second-point-larger-center-claim-next-sublevel-overlap');assert.notEqual(larger.ambiguity_status,'none');assert.match(larger.review_note,/不擅定为超过买卖点所属级别一整级/);
 assert.match(claim('third-point-center-end-larger-or-move-to-new-same-level-center').text,/转更大中枢.*新的该级别中枢/);
 assert.match(claim('between-second-third-is-oscillation-trades-use-lower-level-points').text,/期间没有该级别买卖点.*低级别点/);
 checks.push('同级三类均重要与跨级根一类区别；二卖次级下后上，不创新高或盘背保持OR，二类非只补小转大；更大中枢相对基准仍歧义/必将形成非已完成，三类后转大或新同级分支与震荡低级点保留');

 const tiny=claim('tiny-level-conditional-skilled-smooth-channel-thirty-usual-five-floor');assert.match(tiny.text,/技术特别好且通道特别顺.*普通技术按30分.*最低不小于5分/);assert.equal(tiny.conditions.length,2);assert.match(tiny.review_note,/不定义宇宙最低走势级别/);
 assert.match(claim('small-level-utilization-zero-cost-chips-capacity-position-detail-deferred').text,/资金量约束.*细节留待后文/);
 const profit=claim('chase-price-replaced-by-points-daily-third-author-100-profit');assert.notEqual(profit.ambiguity_status,'none');assert.match(profit.text,/100%获利/);assert.match(profit.review_note,/未证实际收益/);assert.equal(profit.evidence.length,2);
 assert.match(claim('miss-daily-third-lower-entry-operability-worsens').text,/30分、5分甚至1分.*可操作性越差/);
 assert.notEqual(claim('unfamiliar-sell-first-rebuy-author-no-loss-context-not-global-guarantee').ambiguity_status,'none');
 checks.push('小级操作须技术且通道，普通30/最低5为人群执行建议非理论最低定义；资金容量/反应/成本与作者100%及不用亏钱强语分层，跨页原引完整，仓位明言以后说不补公式');

 const rotation=claim('two-stock-time-offset-rotation-permitted-with-skill');const ref=rotation.evidence[0].context.find(p=>p.id==='volume_1-a53e99c37ca5-p0399-b005');assert.ok(ref);assert.equal(ref.role,'reader');assert.match(ref.text,/两股之间的时间差/);assert.equal(rotation.evidence[0].quote,'当然可以，关键你的技术过关。');
 assert.match(claim('five-day-usual-three-day-slow-reference-for-beginners').text,/一般看3天确认.*反应慢.*只是参考/);
 assert.match(claim('exrights-short-adjust-long-large-may-ignore').review_note,/不以日期覆盖15/);assert.notEqual(claim('exrights-short-adjust-long-large-may-ignore').ambiguity_status,'none');
 assert.match(claim('may23-4129-at-0945-1045-break-still-needs-confirmation').text,/09:45.*10:45.*7、8分钟.*仍需确认/);
 for(const p of ['0398-b006','0398-b008','0399-b002','0399-b005','0399-b014','0399-b017','0400-b005']){assert.equal(source(p).role,'reader');assert.equal(graph.db.prepare("SELECT count(*) n FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed' AND e.passage_id=?").get('volume_1-a53e99c37ca5-p'+p).n,0);}
 assert.equal(graph.db.prepare("SELECT count(*) n FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed' AND e.passage_id=?").get('volume_1-a53e99c37ca5-p0399-b009').n,0);
 checks.push('两股互动短答保reader相邻上下文，不扩为同板块套利；复权53/28与15均线范围不强合/后日不覆盖，3天慢参考和4129仍需确认/两倍个案保历史，读者收益矿权/趋势问句与文化观点未升技术事实');

 const plan=JSON.parse(readFileSync(resolve(agent,'curation/source-audit/stage-c-l053-source-plan.json'),'utf8'));assert.equal(plan.operations.length,22);
 for(const op of plan.operations){assert.equal(op.table,'passages');assert.deepEqual(Object.keys(op.after),['published_at']);assert.equal(op.before.published_at,op.after.published_at.replace(' ',''));assert.equal(source(op.id.split('-p')[1]).published_at,op.after.published_at);}
 const ledger=readFileSync(resolve(agent,'curation/upper/c_stage_l053.coverage.jsonl'),'utf8').trim().split('\n').map(JSON.parse);assert.equal(ledger.length,57);assert.equal(new Set(ledger.map(p=>p.passage_id)).size,57);
 assert.equal(graph.db.prepare("SELECT count(*) n FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 396 AND 400").get().n,0);
 for(const c of graph.db.prepare("SELECT id FROM claims WHERE id LIKE 'upper-l053-c-stage-%'").all())for(const e of graph.getClaim(c.id).evidence)assert.deepEqual(e.figure_ids,[]);
 assert.equal(graph.db.prepare("SELECT processing_status FROM units WHERE id='lesson-053'").get().processing_status,'semantic_read_with_pending');assert.equal(graph.metadata.semantic_completion,false);
 checks.push('22字段仅日期空格，原字/映射/坐标不改，57段全台账；本课五页无图，无凭空图关联，语义未完成和六待核不伪装全书/Windows验收');

 const anchor=rotation.evidence[0].id;
 const requests=[['search',{query:'第二类买卖点'},['search','第二类买卖点']],['concept',{id:'第二类买卖点',limit:20},['concept','第二类买卖点','--limit','20']],['neighbors',{id:'区间套',depth:1,limit:100},['neighbors','区间套','--depth','1','--limit','100']],['evidence',{id:anchor},['evidence',anchor]],['page',{documentId:'volume_1.pdf',page:397},['page','--document-id','volume_1.pdf','--page','397']],['search',{query:'并触及该级别',scope:'source',limit:8},['search','并触及该级别','--scope','source','--limit','8']],['coverage',{},['coverage']]];
 const parity=[];for(const [command,args,argv] of requests){const a=JSON.parse(JSON.stringify(graph.query(command,args)));assert.deepEqual(JSON.parse(JSON.stringify(desktop.query(command,args))),a);const cli=spawnSync(process.execPath,[resolve(agent,'bin/chan-kg.mjs'),...argv,'--kb',root],{encoding:'utf8',maxBuffer:24*1024*1024});assert.equal(cli.status,0,cli.stderr);assert.deepEqual(JSON.parse(cli.stdout),a);parity.push({command,args,cli_matches_shared:true,desktop_module_matches_shared:true});}
 assert.deepEqual({database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
 const report={graph_version:graph.metadata.graph_version,schema_version:graph.metadata.schema_version,checks,parity,intended_figure_links_checked:{claims:0,associations:0,unique_figures:0},core_sha256:sha(resolve(agent,'src/core.mjs')),desktop_core_sha256:sha(resolve(agent,'../chan-kg-desktop/vendor/core.mjs')),database_and_manifest_unchanged:true,pass:true,limits:['同模型语义边界/指代/来源和模块一致检查，非独立或人类金标准/真实Windows运行。','并触及/并一定要原字、二类更大中枢比较基准/完成、复权跨课范围及绝对收益强语仍待核。','冻结重合前20召回回归未修，完整G/产品交付未验收。']};
 writeFileSync(resolve(agent,'curation/source-audit/stage-c-l053-verification.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({graph_version:report.graph_version,boundary_groups:checks.length,parity:parity.length,figure_links:report.intended_figure_links_checked,pass:true}));
}finally{graph.close();desktop.close();}
