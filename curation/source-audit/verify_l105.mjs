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
  assert.equal(graph.db.prepare("SELECT count(*) AS n FROM claims WHERE id LIKE 'lower-l105-c-stage-%' AND review_status='reviewed'").get().n,66);
  const canonical=graph.query('concept',{id:'机械化操作',limit:100});
  const alias=graph.query('concept',{id:'机械操作',limit:100});
  assert.equal(canonical.data.concept.id,alias.data.concept.id);
  assert.ok(alias.data.claims.some(x=>x.id===id('105','mechanical-follow-structural-joints')));
  assert.ok(graph.query('search',{query:'机械操作',limit:20}).data.results.some(x=>x.id===id('105','mechanical-follow-structural-joints')));
  assert.ok(claim('105','classification-choice-must-be-complete').conditions[0].includes('完全分类'));
  assert.match(claim('105','mechanical-follow-structural-joints').review_note,/不直接等同电脑自动交易/);
  const aliasAudit=JSON.parse(readFileSync(resolve(agent,'curation/source-audit/stage-d-l105-mechanical-alias.json'),'utf8'));
  assert.equal(aliasAudit.graph_version,graph.metadata.graph_version);assert.equal(aliasAudit.aliases.length,1);
  assert.ok(aliasAudit.aliases[0].source_evidence.some(e=>e.source_type==='course_title_context'&&e.quote.includes('远离聪明、机械操作')));
  checks.push('66新增；机械操作标题别名与正文机械化操作同概念可查，完全分类前提保留，未宣称自动交易已实现');
  const plan=JSON.parse(readFileSync(resolve(agent,'curation/source-audit/stage-c-l105-source-plan.json'),'utf8'));
  const sourceOps=plan.operations.filter(x=>x.table==='passages');assert.equal(sourceOps.length,48);
  for(const op of sourceOps){const p=graph.db.prepare('SELECT * FROM passages WHERE id=?').get(op.id);
    for(const [key,value] of Object.entries(op.after))assert.equal(p[key],value,op.id+':'+key);
    assert.equal(createHash('sha256').update(p.text).digest('hex'),op.text_sha256);
  }
  const pdate=(suffix)=>graph.db.prepare('SELECT role,speaker,published_at FROM passages WHERE id=?').get('volume_2-5332cd1b6038-p'+suffix);
  assert.equal(pdate('0391-b007').published_at,'2008-04-29 15:02:13');assert.equal(pdate('0391-b008').published_at,'2008-04-30 15:17:52');
  assert.equal(pdate('0392-b000').published_at,'2008-04-30 15:17:52');assert.equal(pdate('0392-b001').published_at,'2008-05-05 16:54:42');
  assert.equal(pdate('0392-b003').published_at,'2008-05-06 13:25:02');assert.equal(pdate('0392-b004').published_at,'2008-05-07 15:06:22');
  assert.equal(pdate('0393-b006').role,'author_commentary');assert.equal(pdate('0393-b006').speaker,'缠中说禅');
  assert.equal(pdate('0396-b004').published_at,'2008-06-12 15:23:31');assert.equal(pdate('0397-b008').published_at,'2008-06-19 08:11:01');
  assert.equal(pdate('0401-b000').published_at,'2008-07-03 15:42:51');assert.equal(pdate('0401-b002').published_at,'2008-07-04 16:04:21');
  assert.equal(pdate('0401-b003').published_at,'2008-07-09 16:06:27');
  assert.equal(graph.db.prepare("SELECT count(*) AS n FROM passages WHERE unit_id='lesson-105' AND role='reader'").get().n,0);
  checks.push('48段身份/日期逐项匹配源页校核，段末下一时间头不污染前段；连续作者解盘不再误标读者，文字哈希保留');
  assert.match(claim('105','apr16-half-position-range-break-rule').text,/必然半仓.*真破位则不回补.*余下半仓/);
  assert.match(claim('105','jul2-active-accumulation-partial-chips-not-always-half').text,/卖部分.*筹码够多时可只补固定数量/);
  assert.match(claim('105','jul2-active-accumulation-partial-chips-not-always-half').review_note,/不等4\/16半仓/);
  assert.equal(claim('105','jul1-two-third-centers-no-risk-author-assertion').ambiguity_status,'active_accumulation_risk_free_claim_vs_execution_constraints');
  assert.match(claim('105','apr14-bench-or-sprint-by-capability').text,/具有相应水平为假设.*短跑不应变成长跑/);
  checks.push('4/16半仓只限当例，7/2部分筹码和固定数量两支不套统一半仓；主动买套无风险只归作者断言，能力门槛保留');
  assert.match(claim('105','apr18-three-rebound-strengths-not-chart-periods').text,/4778至5524.*4196至4695/);
  assert.equal(claim('105','apr18-three-rebound-strengths-not-chart-periods').ambiguity_status,'rebound_strength_grade_vs_structural_level_and_price_rounding');
  assert.match(claim('105','apr22-3085-fractal-confirmed-stroke-pending').text,/分型成立.*回试能否站住最终成向上笔/);
  assert.match(claim('105','jul3-containment-delays-bottom-step-boundaries').text,/底分型须再等次日.*2753、2945、缺口、3483/);
  assert.match(claim('105','jul4-weak-bottom-2753-still-pending').text,/终于勉强形成.*最弱.*2753未攻克/);
  assert.equal(claim('105','apr28-daily-up-stroke-and-five-day-line').ambiguity_status,'completed_daily_stroke_vs_further_extension_wording');
  checks.push('历史力度级别不换成固定结构级别，分型/成笔与跨日包含/最低分型分别确认；完成又延伸措辞未擅改');
  const entry=claim('105','jun19-nesting-entry-boundaries-for-exit');
  assert.match(entry.text,/区间套成立即进场.*并非等.*2917.*站稳才进.*2917站住且继续满足笔延伸/);
  assert.match(claim('105','jun12-third-sell-divergence-or-more-centers').text,/第二中枢三卖之后是否真正背驰/);
  assert.match(claim('105','jun12-no-new-low-second-center-third-buy').text,/第二中枢出现三买/);
  checks.push('区间套入场与2917持有/退出边界不倒置，站住及笔延伸联合，第二中枢后三卖/三买分支齐全');
  assert.match(claim('105','forecast-not-market-no-hundred-percent').text,/没有100%准确可能.*不能把分析预测当市场走势本身/);
  assert.equal(claim('105','jun10-prediction-game-operation-absolute-wording').ambiguity_status,'absolute_rule_design_vs_actual_executability');
  assert.match(claim('105','jun10-prediction-game-operation-absolute-wording').text,/3300缺口不回补才可回补筹码/);
  assert.match(claim('105','jun10-down-divergence-rebound-gap-two-paths').text,/不能回补6月10日缺口就退出.*能回补则/);
  checks.push('预测非100%与绝对操作规则设计不混，3300支撑缺口不补/新6月10日缺口反弹补回的对象和筹码回补分开');
  const minimum=claim('105','jul1-theoretical-minimum-above-2990');
  assert.ok(minimum.conditions.includes('这次下跌最终完成'));assert.ok(minimum.conditions.some(x=>x.includes('相应级别')));
  assert.match(minimum.text,/2990之上.*继续下跌仍/);
  assert.match(claim('105','jul1-empirical-third-3700-not-guaranteed').text,/经验参考.*非100%保证.*90%以上/);
  assert.match(claim('105','jul1-final-decline-ninety-nine-not-hundred').text,/非理论100%.*大的第三中枢.*99%/);
  assert.match(claim('105','jul2-inverted-t-seventy-percent-empirical').text,/70%.*经验性.*与其理论无关.*辅助/);
  assert.match(claim('105','jul1-active-accumulation-stage-eighty-percent-filter').review_note,/并不逐例严格吻合/);
  const cross=claim('105','jul1-final-decline-ninety-nine-not-hundred');assert.deepEqual(cross.evidence.map(x=>x.pdf_page).sort((a,b)=>a-b),[399,400]);
  checks.push('2990完成/相应级别条件与3700经验1/3分开，90/99/70皆作者自述非项目统计；两种第三中枢和80%例范围保留');
  const figures=graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_2-5332cd1b6038' AND pdf_page BETWEEN 383 AND 401").all();
  assert.equal(figures.length,11);assert.equal(figures.filter(x=>x.origin_status==='later_annotation').length,9);
  assert.equal(figures.filter(x=>x.origin_status==='unverified').length,2);
  assert.equal(graph.metadata.semantic_completion,false);
  assert.equal(claim('105','jul9-moving-average-classification-homework').ambiguity_status,'moving_average_homework_answer_deferred');
  checks.push('11本课图9后加2未知流程，不将图表自动认可为作者算法，7/9均线分类仍只是作业，整体语义未完成');
  const requests=[
    ['search',{query:'机械操作'},['search','机械操作']],
    ['concept',{id:'主动买套',limit:100},['concept','主动买套','--limit','100']],
    ['concept',{id:'倒T型K线',limit:100},['concept','倒T型K线','--limit','100']],
    ['neighbors',{id:'机械化操作',depth:1,limit:100},['neighbors','机械化操作','--depth','1','--limit','100']],
    ['evidence',{id:cross.evidence.find(e=>e.pdf_page===400).id},['evidence',cross.evidence.find(e=>e.pdf_page===400).id]],
    ['page',{documentId:'volume_2.pdf',page:392},['page','--document-id','volume_2.pdf','--page','392']],
    ['search',{query:'2917',scope:'source'},['search','2917','--scope','source']],
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
    limits:['模块与CLI检查不是Windows成品离线、PDF高亮或实际界面验收。','同模型开发场景，不证明全书歧义已解决、作者2990理论已独立重建、3700经验/70/90/99比例已实测、主动买套无风险或未知图是作者程序。']};
  writeFileSync(resolve(agent,'curation/source-audit/stage-c-l105-verification.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report));
} finally {graph.close();desktop.close();}
