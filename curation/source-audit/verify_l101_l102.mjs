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
  assert.equal(graph.db.prepare("SELECT count(*) AS n FROM claims WHERE (id LIKE 'lower-l101-c-stage-%' OR id LIKE 'lower-l102-c-stage-%') AND review_status='reviewed'").get().n,59);
  const general=claim('101','second-buy-retest-end-definition');
  assert.ok(general.conditions.every(x=>/第一类买点|一买/.test(x)));
  assert.match(claim('101','second-buy-below-first-permitted').text,/比一买低完全可以/);
  assert.match(claim('101','first-second-third-higher-only-general').text,/一般情况下/);
  assert.match(claim('101','second-third-coincide-strongest').text,/二三买合一.*一般/);
  assert.match(graph.getClaim('upper-l021-c-stage-second-third-coincidence-no-guaranteed-trend').text,/不.*排除.*扩张/);
  checks.push('59条新增；二买三式保留，低于一买可行，合一不保证大级别上涨');
  assert.match(claim('101','second-third-not-necessarily-adjacent').text,/二三之间可以/);
  assert.equal(claim('101','intervening-oscillation-buys-loose-naming').ambiguity_status,'strict_second_buy_vs_loose_oscillation_name');
  assert.ok(claim('101','first-second-only-current-rise-intermediate').conditions[0].includes('这回升'));
  assert.match(claim('101','above-twenty-not-no-opportunity').text,/并非没有机会/);
  checks.push('中间震荡点宽称与严格二买分开；回升中阴对象保留，20以上口号有明确机会限制');
  assert.equal(claim('101','recursive-unique-decomposition-author-claim').ambiguity_status,'formal_proof_not_reproduced');
  assert.equal(claim('101','a0-arbitrary-design-author-wording').ambiguity_status,'a0_arbitrary_design_vs_uniqueness_prerequisite');
  assert.ok(graph.getClaim('lower-l084-c-stage-fractal-only-recursion-start-optional').conditions[0].includes('保证分解唯一性'));
  assert.match(claim('101','chosen-fractal-design-best-author-opinion').text,/笔出现的可能性最大/);
  assert.equal(claim('102','perfection-overall-structure-author-claim').ambiguity_status,'formal_proof_not_reproduced');
  checks.push('唯一性/最优性归作者；随意a0并列84唯一性前提，未报形式证明或最优实验通过');
  assert.match(claim('102','classification-control-means-current-display').review_note,/可控不解释为可操纵价格/);
  assert.match(claim('102','three-layer-expression-and-change-order').text,/a1A1\+a5A5\+a30A30/);
  assert.equal(claim('102','three-layer-expression-and-change-order').ambiguity_status,'coefficients_not_formally_defined');
  assert.match(claim('102','eight-level-names-convenience').text,/名称可以任意取/);
  checks.push('可控为当下显示，名称可换而非结构任意；三层表达未补系数或加权算法');
  assert.match(claim('102','mar10-third-sell-formed-minute-down-likely').text,/三卖.*极可能/);
  assert.match(claim('102','mar11-gap-not-filled-minute-down-formed').text,/差1点.*尚未.*已经形成/);
  assert.match(claim('102','mar11-minute-not-thirty-divergence').text,/真正背驰还没有出现/);
  assert.match(claim('102','mar13-thirty-end-likely-five-not-formed').text,/结束后的强力反弹.*最后5分钟下跌尚未形成/);
  assert.ok(claim('102','mar11-worst-five-center-break-then-thirty').exceptions[0].includes('可能没有背驰'));
  checks.push('跨日极可能/已成分别记录；缺口尚差1点，30分钟未背驰/5分钟未成，极端例外保留');
  const chart=claim('102','mar17-sixty-chart-minute-center-reference');
  assert.equal(chart.ambiguity_status,'chart_reference_frame_vs_strict_structural_level');
  assert.match(chart.evidence[0].quote,/60分钟图上的1分钟中枢/);
  const oldState=claim('102','mar17-retest-stroke-not-yet-author-state'),correction=claim('102','mar19-explicit-correction-enough-stroke');
  assert.match(oldState.evidence[0].quote,/反抽笔还没有出现/);
  assert.match(correction.evidence[0].quote,/必须有一个纠正.*已经足够构成一笔/);
  assert.equal(oldState.evidence[0].published_at,'2008-03-17 15:17:29');
  assert.equal(correction.evidence[0].published_at,'2008-03-19 15:21:35');
  checks.push('60分钟图上1分钟参考框架保留；3/17旧判断与3/19明确纠正各有独立日期原句');
  assert.match(claim('102','mar19-divergence-leg-not-confirmed-bottom').text,/仍无明确区间套.*不能完全确认/);
  const cross=claim('102','mar19-3775-fractal-to-stroke-still-conditional');
  assert.deepEqual(cross.evidence.map(x=>x.pdf_page).sort((a,b)=>a-b),[365,366]);
  assert.match(cross.text,/若连笔都不能延伸.*还须探底/);
  assert.match(claim('102','mar18-large-fund-batches-base-position').text,/底仓.*其他资金/);
  assert.match(claim('102','mar18-low-price-drop-preference-not-rule').review_note,/不是第一类买点定义/);
  checks.push('背驰段未确/底分型/笔分层，跨页续句齐全；底仓及其他资金、40%偏好非充分买点');
  const figures=graph.db.prepare("SELECT id,origin_status FROM figures WHERE document_id='volume_2-5332cd1b6038' AND pdf_page BETWEEN 353 AND 365").all();
  assert.equal(figures.length,6);assert.equal(figures.filter(x=>x.origin_status==='later_annotation').length,3);
  assert.equal(figures.filter(x=>x.origin_status==='unverified').length,3);
  assert.equal(graph.db.prepare("SELECT origin_status FROM figures WHERE id='volume_2-5332cd1b6038-p0366-fig1'").get().origin_status,'unverified');
  assert.equal(graph.metadata.semantic_completion,false);
  checks.push('六本课图三后加三未核，366下一课图未修改，整体语义仍未完成');
  const requests=[
    ['search',{query:'二买最弱情况'},['search','二买最弱情况']],
    ['concept',{id:'第二类买点',limit:100},['concept','第二类买点','--limit','100']],
    ['concept',{id:'走势终完美',limit:100},['concept','走势终完美','--limit','100']],
    ['neighbors',{id:'完全分类',depth:1,limit:100},['neighbors','完全分类','--depth','1','--limit','100']],
    ['evidence',{id:cross.evidence.find(e=>e.pdf_page===366).id},['evidence',cross.evidence.find(e=>e.pdf_page===366).id]],
    ['page',{documentId:'volume_2.pdf',page:353},['page','--document-id','volume_2.pdf','--page','353']],
    ['search',{query:'必须有一个纠正',scope:'source'},['search','必须有一个纠正','--scope','source']],
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
    limits:['模块与CLI检查不是Windows成品离线、PDF高亮或实际界面验收。','同模型开发场景，不证明全书歧义已解决、唯一分解/最优性已形式证明、精确定位/收益已实测。']};
  writeFileSync(resolve(agent,'curation/source-audit/stage-c-l101-l102-verification.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report));
} finally {graph.close();desktop.close();}
