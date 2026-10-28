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
  assert.equal(graph.db.prepare("SELECT count(*) AS n FROM claims WHERE id GLOB 'lower-l09[78]-c-stage-*' AND review_status='reviewed'").get().n,56);
  const deviation=claim('097','deviation-from-points-skilled-not-beginner');
  assert.equal(deviation.ambiguity_status,'skilled_deviation_limit_unspecified');assert.ok(deviation.conditions.some(x=>x.includes('熟练')));
  assert.match(claim('097','application-hard-and-person-dependent').review_note,/修辞性比例/);
  assert.match(claim('097','classification-foundation-not-application-skill').text,/不等于应用能力/);
  checks.push('56默认增量；医学比例仅作者修辞，理论不等应用，偏移买卖点有熟练范围');
  assert.equal(claim('097','jan31-daily-center-forming').ambiguity_status,'daily_center_forming_vs_oscillation_formed');
  assert.match(claim('097','jan31-daily-center-forming').text,/正在形成/);
  assert.match(claim('097','jan31-large-oscillation-range-not-axis-3600').review_note,/非明说中轴价格3600/);
  assert.match(claim('097','jan31-grid-450-and-5228').text,/5228/);
  assert.equal(claim('098','feb14-consolidation-daily-first-center-risk').ambiguity_status,'daily_center_cross_date_completion_scope');
  checks.push('日中枢形成层次跨日期待核，3600为幅度尺度非中轴价，5228未合并5224/5209');
  assert.match(claim('097','feb1-petro-explicit-revision-by-force').text,/明确说.*30.*分力改变.*24/);
  assert.match(claim('097','feb1-long-outlook-retained-conditional').review_note,/不能把沉默本身/);
  assert.match(graph.getClaim('lower-l091-c-stage-petro-24-wine-not-price-guarantee').text,/酒话.*愿望/);
  assert.match(claim('098','feb13-petro-24-center-not-forecast-target').text,/24上下中枢/);
  checks.push('有原话才留具体修订，24酒话/愿望与后来中枢区间分开，沉默不是全局有效算法');
  const ret=claim('098','divergence-return-then-classify');assert.match(ret.text,/盘整背驰或真正背驰.*回拉原中枢.*完全分类/);
  assert.match(ret.review_note,/不代表只到必停/);
  assert.match(claim('097','feb4-divergence-return-independent-news').text,/利好只是加强力度/);
  assert.match(graph.getClaim('lower-l071-c-stage-trend-end-divergence-retrace').text,/回拉必形成更大级别中枢/);
  checks.push('回中枢后继续分类非只到即停，利好不替代成立但可加强力度，旧趋势背驰条件未删');
  const seq=claim('098','feb4-364-break-and-361-exception');assert.ok(seq.exceptions[0].includes('363开始线段跌破361'));
  assert.match(seq.review_note,/不是指数价位/);
  assert.match(claim('098','feb4-next-class-divergence-await-slope').review_note,/当时类背驰已成立/);
  assert.match(claim('098','class-divergence-sell-depends-op-level').text,/个人选择和操作级别/);
  checks.push('361至364是编号且条件保留，关注类背驰非已确认，微型卖出依操作级别');
  assert.match(claim('098','slightly-leading-not-fully-inverse').text,/稍先于大盘.*非完全逆势.*可能补跌/);
  assert.equal(claim('098','new-stock-selection-conjunctive').conditions.length,3);
  assert.match(claim('098','position-control-not-necessarily-empty').text,/不一定空仓/);
  assert.match(claim('098','t1-retrace-risk-stronger-stock-proposal').review_note,/非消除T\+1风险/);
  checks.push('稍先非完全逆势，新股三个条件，控仓不等空仓，强股建议不消T+1限制');
  assert.match(claim('098','feb14-next-thirty-up-direction-not-trend').text,/仍在中阴酝酿.*仅盘整.*不一定成为上涨/);
  assert.ok(claim('098','feb14-bench-capability-at-least-thirty').conditions[0].includes('假设'));
  assert.equal(claim('098','feb15-600795-risk-allocation-example').ambiguity_status,'small_third_buy_constructing_not_confirmed');
  assert.match(claim('098','feb15-600795-method-not-buy-instruction').text,/不一定让人买.*再买没意义/);
  assert.match(claim('098','feb18-red-histogram-await-confirmation').text,/并不代表一切无忧.*仍需确认/);
  assert.match(claim('098','feb18-indicators-imprecise-center-primary').text,/不精确.*未构成线段类上涨.*中枢已成/);
  checks.push('向上方向非必上涨，小板凳为人群假设；600795估算/三买构造非买入指令，红柱非反转确认');
  const figures=graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_2-5332cd1b6038' AND pdf_page BETWEEN 323 AND 338").all();
  assert.equal(figures.length,6);assert.equal(figures.filter(x=>x.origin_status==='later_annotation').length,5);assert.equal(figures.filter(x=>x.origin_status==='unverified').length,1);
  assert.equal(graph.metadata.semantic_completion,false);
  checks.push('五后期图一未核图，未来日K不反填中枢/分型/背驰完成，整体语义未完成');
  const requests=[
    ['search',{query:'不一定空仓'},['search','不一定空仓']],
    ['concept',{id:'盘整背驰',limit:100},['concept','盘整背驰','--limit','100']],
    ['concept',{id:'操作熟练程度',limit:100},['concept','操作熟练程度','--limit','100']],
    ['neighbors',{id:'仓位',depth:1,limit:100},['neighbors','仓位','--depth','1','--limit','100']],
    ['evidence',{id:deviation.evidence.find(e=>e.pdf_page===325).id},['evidence',deviation.evidence.find(e=>e.pdf_page===325).id]],
    ['page',{documentId:'volume_2.pdf',page:333},['page','--document-id','volume_2.pdf','--page','333']],
    ['search',{query:'背驰成立只保证',scope:'source'},['search','背驰成立只保证','--scope','source']],
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
    limits:['模块与CLI检查不是Windows成品离线、PDF高亮或实际界面验收。','同模型开发场景，不证明医学类比、预测完备性/收益保证或未参数化的熟练偏移、强股/仓位阈值。']};
  writeFileSync(resolve(agent,'curation/source-audit/stage-c-l097-l098-verification.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report));
} finally {graph.close();desktop.close();}
