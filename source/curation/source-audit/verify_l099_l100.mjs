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
  assert.equal(graph.db.prepare("SELECT count(*) AS n FROM claims WHERE (id LIKE 'lower-l099-c-stage-%' OR id LIKE 'lower-l100-c-stage-%') AND review_status='reviewed'").get().n,55);
  const general=claim('099','general-not-same-level-partition');
  assert.match(general.text,/一般划分.*不是同级别.*整体却不必就是1分钟/);
  assert.deepEqual(general.evidence.map(e=>e.pdf_page).sort((a,b)=>a-b),[338,339]);
  const absorb=claim('099','associativity-absorb-old-last-center');assert.match(absorb.text,/a\+b\+c\+d\+e\+f=a\+b\+c\+\(d\+e\+f\)/);
  assert.match(claim('099','post-divergence-fgh-preserve-old-type').text,/a\+b\+c\+d\+e\+\(f\+g\+h\)/);
  assert.ok(claim('099','post-divergence-fgh-preserve-old-type').conditions[0].includes('已构成'));
  assert.match(claim('099','center-first-nine-case-repartition').review_note,/不是任意九笔/);
  checks.push('55条新增；一般划分非同级别，两重组依中枢成立，中枢优先而非任意三段九段');
  assert.ok(claim('099','completed-type-next-at-least-larger-center').conditions[0].includes('已经完成'));
  assert.equal(claim('099','deeper-center-danger-reference').ambiguity_status,'second_or_further_center_reference');
  assert.match(claim('099','danger-relative-downtrend-good-for-longs').text,/下跌.*对多头反为好事/);
  const old=graph.getClaim('lower-l098-c-stage-divergence-return-then-classify');
  assert.equal(old.ambiguity_status,'return_guarantee_cross_lesson_scope');
  const amendment=JSON.parse(readFileSync(resolve(agent,'curation/source-audit/stage-d-l024-l098-l099-return-scope.json'),'utf8'));
  assert.equal(amendment.graph_version,graph.metadata.graph_version);assert.equal(amendment.changes.length,1);
  assert.equal(amendment.source_evidence_concepts_relations_unchanged,true);assert.equal(amendment.all_other_claims_unchanged,true);
  assert.match(old.review_note,/第24课.*第98课.*第99课/);
  checks.push('走势完成前提与相对危险保留；98仅加跨课歧义，旧文字/条件/证据及其他命题未改');
  assert.match(claim('100','feb25-three-layer-current-states').text,/30分钟.*未三卖.*5分钟.*不能100%.*1分钟下跌已成/);
  assert.match(claim('100','pullback-five-third-sell-or-oscillation').text,/若成.*确认第二5分钟中枢.*若不成.*继续震荡/);
  const higher=claim('100','five-change-not-thirty-change-immediate');assert.match(higher.text,/本身不改变30分钟.*下跌以后结束并回拉构30分钟三卖/);
  assert.deepEqual(higher.evidence.map(e=>e.pdf_page).sort((a,b)=>a-b),[346,347]);
  checks.push('30/5/1当前状态不互借，5分钟三卖两支与以后结束回拉才触30分钟三卖分层');
  assert.equal(claim('100','ability-only-quantity-author-general-claim').ambiguity_status,'general_executable_vs_specific_capability_gate');
  assert.match(claim('100','capacity-gate-and-tiny-practice').text,/处理不了可能三卖者不参加.*特别小仓位/);
  assert.match(claim('100','small-fund-one-layer-large-multilayer').text,/小资金可只用一个层次.*较大资金不合适/);
  checks.push('一般数量即可执行与具体能力退出门槛并列，极小仓练习非无风险，小/大资金范围保留');
  assert.match(claim('100','feb26-retrace-minimum-fractal-only-prototype').text,/仅雏形.*不破底且高于当日高点.*之后还须/);
  assert.match(claim('100','feb27-fractal-formed-stroke-upper-4391').text,/4331.*成立.*4391.*延伸为笔/);
  assert.match(claim('100','feb29-4331-five-center-4391-boundary').text,/已延伸5分钟.*4391.*才能延伸为笔/);
  assert.match(claim('100','mar3-week-fractal-4391-stroke-4695').text,/4391.*周底分型已现.*4695/);
  assert.match(claim('100','mar3-a-plus-a-nine-segments-no-third-buy').text,/真正三买尚未出现/);
  checks.push('日底雏形/成立/笔、日4391/周4695及中枢三买均不同确认对象，后期图不倒填');
  assert.equal(claim('100','macd-zero-necessary-wording-scope').ambiguity_status,'macd_necessary_wording_vs_auxiliary_scope');
  assert.equal(claim('100','macd-visual-auxiliary-not-special').ambiguity_status,'macd_necessary_wording_vs_auxiliary_scope');
  assert.match(graph.getClaim('upper-l017-c-stage-indicators-auxiliary-not-necessary').text,/没有这两个指标也能判断背驰/);
  assert.match(claim('100','feb29-red-after-entanglement-not-certain').text,/骗线仍可能/);
  assert.match(claim('100','feb29-red-after-entanglement-not-certain').review_note,/未核频率/);
  checks.push('零轴必要用语与同篇非特殊、17非必要并列，作者低骗线频率未当实测胜率');
  assert.match(claim('099','feb22-two-three-still-market-choice').text,/仍保留第二、三/);
  assert.match(claim('099','feb25-policy-force-third-branch-eliminated').text,/已排除前述第三支/);
  assert.match(claim('100','feb27-second-branch-first-not-excluded').text,/第一支仍不能完全排除/);
  assert.match(claim('100','feb27-half-exit-or-hold-or-skilled-swap').text,/出一半.*心态好者可持.*技术更高者可换股/);
  assert.match(claim('100','mar4-return-center-third-buy-absent').text,/真正三买未出.*当日已/);
  checks.push('分支按日筛除而非未来预知；减半/持有/换股依人群，3/4回中枢有当天文字');
  const figures=graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_2-5332cd1b6038' AND pdf_page BETWEEN 339 AND 352").all();
  assert.equal(figures.length,6);assert.ok(figures.every(x=>x.origin_status==='later_annotation'));
  assert.equal(graph.metadata.semantic_completion,false);
  checks.push('六图均后加，CHYS20091010及未来K线不作作者观点唯一证明，整体语义仍未完成');
  const requests=[
    ['search',{query:'中阴危险'},['search','中阴危险']],
    ['concept',{id:'中阴阶段',limit:100},['concept','中阴阶段','--limit','100']],
    ['concept',{id:'结合律',limit:100},['concept','结合律','--limit','100']],
    ['neighbors',{id:'完全分类',depth:1,limit:100},['neighbors','完全分类','--depth','1','--limit','100']],
    ['evidence',{id:general.evidence.find(e=>e.pdf_page===339).id},['evidence',general.evidence.find(e=>e.pdf_page===339).id]],
    ['page',{documentId:'volume_2.pdf',page:346},['page','--document-id','volume_2.pdf','--page','346']],
    ['search',{query:'a+b+c+d+e+f',scope:'source'},['search','a+b+c+d+e+f','--scope','source']],
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
    limits:['模块与CLI检查不是Windows成品离线、PDF高亮或实际界面验收。','同模型开发场景，不证明全部跨课范围已统一、完全分类可执行性、MACD必要性或作者收益/预测自述。']};
  writeFileSync(resolve(agent,'curation/source-audit/stage-c-l099-l100-verification.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report));
} finally {graph.close();desktop.close();}
