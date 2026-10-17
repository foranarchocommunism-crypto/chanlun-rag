import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { KnowledgeGraph } from '../../src/core.mjs';
import { KnowledgeGraph as DesktopGraph } from '../../../chan-kg-desktop/vendor/core.mjs';

const agent=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
const root=resolve(agent,'../shared-knowledge/v0.1.0');
const sha=path=>createHash('sha256').update(readFileSync(path)).digest('hex');
const before={database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))};
const graph=new KnowledgeGraph(root),desktop=new DesktopGraph(root);
const id=(lesson,slug)=>`lower-l${lesson}-c-stage-${slug}`;
const claim=(lesson,slug)=>{const c=graph.getClaim(id(lesson,slug));assert.ok(c);return c;};
const checks=[];
try {
  assert.equal(graph.db.prepare("SELECT count(*) AS n FROM claims WHERE (id LIKE 'lower-l103-c-stage-%' OR id LIKE 'lower-l104-c-stage-%') AND review_status='reviewed'").get().n,53);
  const defense=claim('103','macd-zero-defense-corresponding-chart');
  assert.ok(defense.exceptions[0].includes('背驰'));assert.ok(defense.evidence.some(x=>x.quote.includes('技术高点')));
  const cross=claim('103','macd-defense-lowest-period-by-capability');
  assert.deepEqual(cross.evidence.map(x=>x.pdf_page).sort((a,b)=>a-b),[366,367]);
  assert.match(cross.text,/按能力选最低时间周期.*60或30/);
  assert.match(claim('103','macd-defense-skilled-divergence-exception').text,/允许技术较高者在背驰情况下介入/);
  checks.push('53新增；零轴防守有最低周期/能力条件及高手背驰例外，跨366/367续句齐全');
  assert.equal(claim('104','geometry-energy-dynamics-author-program').ambiguity_status,'physics_analogy_no_formal_market_mapping');
  assert.ok(claim('104','geometry-energy-dynamics-author-program').evidence.some(e=>e.quote.includes('具体怎么样，以后慢慢说来')));
  assert.ok(graph.query('concept',{id:'几何结构',limit:10}).data.claims.some(x=>x.id===id('104','geometry-energy-dynamics-author-program')));
  checks.push('几何/物理纲领归作者，未声称物理方程、量纲、市场映射或实证已提供');
  const scale=claim('103','3600-scale-targets-4922-3424-author');
  assert.equal(scale.ambiguity_status,'author_reported_rounding_and_unverified_price_rhythm');
  assert.match(scale.text,/600点.*1345点.*4922.*3424/);assert.match(scale.review_note,/并非精确600\/1345/);
  assert.equal(claim('104','price-target-three-percent-author-convention').ambiguity_status,'price_target_tolerance_not_structural_epsilon');
  assert.match(claim('104','mar28-no-daily-fractal-no-final-bottom').text,/日底分型都尚不足.*没有最终结论/);
  checks.push('原600/1345价差近似未私改，3600为幅度；3%价格目标惯例不替结构容差，3424未最终确认');
  assert.match(claim('103','mar25-five-to-thirty-macd-exit-condition').text,/5分钟.*30分钟/);
  assert.match(claim('103','mar26-five-consolidation-only-fifteen-zero').text,/5分钟.*只带15分钟/);
  assert.equal(claim('103','mar25-five-to-thirty-macd-exit-condition').evidence[0].published_at,'2008-03-25 15:09:37');
  assert.equal(claim('103','mar26-five-consolidation-only-fifteen-zero').evidence[0].published_at,'2008-03-26 15:15:26');
  assert.match(claim('103','warrant-no-chase-expiry-warning').text,/0.8.*0.6.*未介入者不得再介入.*高度投机/);
  assert.match(claim('104','mar27-warrant-one-center-consolidation').text,/一般人远离/);
  checks.push('3/25预期5带30与3/26实际只带15按日留存；权证0.6/0.7/0.8对象和一般人远离限制保留');
  assert.match(claim('104','small-fund-short-bite-large-chips-now').text,/以前离底部远未要求沉淀.*最近/);
  const t1=claim('104','apr2-3462-fail-retest-and-t1-tail');assert.match(t1.text,/前一天尾盘打提前量/);
  assert.match(t1.review_note,/不改变T\+1制度/);
  assert.ok(graph.query('concept',{id:'T+1',limit:10}).data.claims.some(x=>x.id===t1.id));
  checks.push('大小资金及最近才沉淀范围保留，前日尾盘提前量不取消T+1或保证隔夜退出');
  const answer=claim('104','apr3-homework-apr7-author-answer-3396');
  assert.deepEqual(answer.evidence.map(x=>x.pdf_page).sort((a,b)=>a-b),[379,380]);
  assert.ok(answer.evidence.some(x=>x.published_at==='2008-04-03 15:24:59'));assert.ok(answer.evidence.some(x=>x.published_at==='2008-04-07 15:21:25'));
  assert.match(answer.text,/只和60分钟底分型有关，3396/);assert.match(answer.review_note,/突破下降趋势线是未核制作者加字/);
  checks.push('4/3作业与4/7作者3396答案跨页/日期齐全，图上下降趋势线括注不冒充作者解释');
  assert.match(claim('104','apr7-sixty-up-stroke-formed').text,/60分钟图.*第一次延伸出向上笔/);
  const week=claim('104','apr7-day-3613-week-fractal-likely-exception');assert.ok(week.exceptions[0].includes('本周内再破底'));
  assert.match(week.text,/可能性极大/);
  assert.match(claim('104','apr11-week-bottom-3840-stroke-or-relay').text,/周底分型已形成.*3840.*或失败/);
  assert.match(claim('104','apr11-three-chart-boundaries-not-one-level').text,/3533.*60分钟.*3613.*日线.*3840.*周图/);
  checks.push('4/7六十分钟笔已成、周底极可能及再破底例外，与4/11周底已成/周笔两支分开；三价三图不互借');
  const figures=graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_2-5332cd1b6038' AND pdf_page BETWEEN 366 AND 382").all();
  assert.equal(figures.length,13);assert.equal(figures.filter(x=>x.origin_status==='later_annotation').length,12);
  assert.equal(figures.filter(x=>x.origin_status==='unverified').length,1);assert.equal(graph.metadata.semantic_completion,false);
  checks.push('13图12后加1未核，主图及插图右端均检查；全书语义仍未完成');
  const requests=[
    ['search',{query:'最低时间周期'},['search','最低时间周期']],
    ['concept',{id:'MACD',limit:100},['concept','MACD','--limit','100']],
    ['concept',{id:'几何结构',limit:100},['concept','几何结构','--limit','100']],
    ['neighbors',{id:'底分型',depth:1,limit:100},['neighbors','底分型','--depth','1','--limit','100']],
    ['evidence',{id:cross.evidence.find(e=>e.pdf_page===367).id},['evidence',cross.evidence.find(e=>e.pdf_page===367).id]],
    ['page',{documentId:'volume_2.pdf',page:381},['page','--document-id','volume_2.pdf','--page','381']],
    ['search',{query:'3396',scope:'source'},['search','3396','--scope','source']],
    ['coverage',{},['coverage']],
  ];
  const parity=[];
  for(const [command,args,argv] of requests){
    const a=JSON.parse(JSON.stringify(graph.query(command,args)));
    assert.deepEqual(JSON.parse(JSON.stringify(desktop.query(command,args))),a);
    const cli=spawnSync(process.execPath,[resolve(agent,'bin/chan-kg.mjs'),...argv,'--kb',root],{encoding:'utf8',maxBuffer:24*1024*1024});
    assert.equal(cli.status,0,cli.stderr);assert.deepEqual(JSON.parse(cli.stdout),a);
    parity.push({command,args,cli_matches_shared:true,desktop_module_matches_shared:true});
  }
  assert.deepEqual({database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
  const report={graph_version:graph.metadata.graph_version,schema_version:graph.metadata.schema_version,checks,parity,
    core_sha256:sha(resolve(agent,'src/core.mjs')),desktop_core_sha256:sha(resolve(agent,'../chan-kg-desktop/vendor/core.mjs')),
    database_and_manifest_unchanged:true,pass:true,
    limits:['模块与CLI检查不是Windows成品离线、PDF高亮或实际界面验收。','同模型开发场景，不证明全书歧义已解决、物理几何映射已证明、价格目标预测/交易收益已实测或3%可作结构容差。']};
  writeFileSync(resolve(agent,'curation/source-audit/stage-c-l103-l104-verification.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report));
} finally {graph.close();desktop.close();}
