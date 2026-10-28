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
const claim = slug => { const c = graph.getClaim('upper-l041-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try {
  assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l041-c-stage-%' AND review_status='reviewed'").get().n, 30);
  assert.match(claim('no-chase-third-points-form-in-pullback-and-rebound').text, /第三类买卖点.*分别在回调与反弹/);
  assert.match(claim('no-chase-third-points-form-in-pullback-and-rebound').review_note, /不等任意回调/);
  const cross = claim('rhythm-before-precision-learning-and-practice');
  assert.deepEqual(cross.evidence.map(e=>e.pdf_page).sort((a,b)=>a-b), [301,302]);
  assert.match(cross.review_note, /不取消识别有效点和级别/);
  assert.notEqual(claim('capital-size-not-protection-same-zero-speed-rhetoric').ambiguity_status, 'none');
  assert.match(claim('three-opportunities-rhetoric-and-rest-after-repeated-errors').review_note, /三类点必全出现/);
  checks.push('30新增；买点/卖点及三类点回调反弹不等任意波动；跨页节奏精度联合保留，资金归零同速/三次机会/死亡强词不成为结果定律');

  assert.match(claim('beginner-prefer-thirty-minutes-never-below-five').text, /初学者.*30分钟.*不能小于5分钟/);
  assert.ok(claim('beginner-prefer-thirty-minutes-never-below-five').conditions.some(x=>x.includes('初学者')));
  assert.match(claim('beginner-five-minute-divergence-stage-is-necessary-not-buy-signal').review_note, /必要限制.*不是进入背驰段便已背驰/);
  assert.match(claim('smaller-level-higher-precision-frequent-errors-harm-learning').review_note, /不是任何交易频率必然失误|而非任何交易频率必然失误/);
  assert.match(claim('accuracy-before-frequency-and-transaction-beneficiaries').review_note, /没有提供准确率阈值/);
  checks.push('初学者30分较好且不得低于5分有精度前提，未入背驰段不得操作为必要限制非买入充分信号；频率/受益人说法无样本或统一阈值');

  const risk=claim('small-point-against-nonexhausted-large-trend-risk');
  assert.equal(risk.conditions.length,2); assert.match(risk.conditions.join(' '), /相反.*尚无衰竭/);
  assert.match(risk.review_note, /不扩成所有小级别操作都禁做/);
  assert.match(graph.getClaim('upper-l040-c-stage-each-layer-independent-and-integrated-own-level-rhythm').review_note, /并非风险完全无相关/);
  assert.match(claim('divergence-consolidation-only-turn-force-is-current').text, /只意味着转向.*中枢星球系统分布.*当下买卖力度/);
  assert.match(claim('divergence-consolidation-only-turn-force-is-current').review_note, /转向不等一定发展为反趋势/);
  assert.match(claim('force-estimation-auxiliary-tools-promised-not-specified').text, /留待专门课程.*未展开/);
  checks.push('小级逆大级且大级尚无衰竭两个条件联合，40多层机会不抹风险；背驰盘背只转向，幅度依中枢系统和当下力量，未来辅助课程不虚构成本课公式');

  assert.equal(source('0306-b000').role,'reader');
  assert.equal(source('0306-b001').role,'author_reply');
  assert.notEqual(claim('completion-question-basically-yes-qualified-not-equivalence').ambiguity_status,'none');
  assert.match(claim('completion-question-basically-yes-qualified-not-equivalence').review_note, /不转写成趋势完成当且仅当/);
  assert.match(claim('own-level-consolidation-center-end-consolidation-end').text,/该级别盘整中枢结束.*该级别盘整就结束/);
  assert.match(claim('own-consolidation-end-may-enter-larger-consolidation').text,/不意味着一定脱离盘整.*还可以进入更大/);
  assert.match(claim('yearly-perspective-consolidation-almost-absolute-scope').review_note,/不作所有市场无限历史/);
  checks.push('完成原问保留读者，基本上认可不改成充要定理；本级中枢/盘整结束仍可更大盘整，年线基本绝对为有范围的强表述');

  assert.equal(source('0305-b001').role,'reader');
  assert.match(source('0305-b001').text,/3272.41/);
  assert.match(claim('sector-rotation-reply-does-not-confirm-reader-fifteen-minute-top').review_note,/作者未明确确认该数值/);
  assert.match(claim('monthly-quarterly-large-sell-point-and-long-operation-exit').review_note,/通常而非任意小卖点即永远放弃/);
  assert.notEqual(claim('career-analogy-switch-not-from-buy-to-sell-single-stock-max-profit-view').ambiguity_status,'none');
  const ledger=readFileSync(resolve(agent,'curation/upper/c_stage_l041.coverage.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
  assert.equal(ledger.length,67); assert.equal(ledger.filter(x=>x.result==='nontechnical-political-economy-essay-context').length,8);
  for (const p of ['0302-b009','0303-b000','0303-b001','0303-b002','0303-b003','0303-b004','0303-b005','0304-b000','0304-b008','0304-b009','0304-b012','0305-b010','0305-b012']) {
    assert.equal(graph.db.prepare("SELECT count(*) n FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed' AND e.passage_id=?").get('volume_1-a53e99c37ca5-p'+p).n,0);
  }
  checks.push('历史二线/300/5日线保留时点与未核机构，作者轮动答不确认读者15分3272.41预测；月季大卖点非永死，职业单股最大利润强词未实证；八段经济附文和非技术人生货币答保留上下文');

  const plan=JSON.parse(readFileSync(resolve(agent,'curation/source-audit/stage-c-l041-source-plan.json'),'utf8'));
  assert.equal(plan.operations.length,17);
  for(const op of plan.operations){assert.equal(op.table,'passages'); assert.equal(source(op.id.split('-p')[1]).published_at,op.after.published_at); assert.equal(op.after.published_at.replace(' ',''),op.before.published_at);}
  assert.equal(graph.db.prepare("SELECT count(*) n FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 301 AND 306").get().n,0);
  for(const c of graph.db.prepare("SELECT id FROM claims WHERE id LIKE 'upper-l041-c-stage-%'").all()) for(const e of graph.getClaim(c.id).evidence) assert.deepEqual(e.figure_ids,[]);
  assert.equal(graph.db.prepare("SELECT processing_status FROM units WHERE id='lesson-041'").get().processing_status,'semantic_read_with_pending');
  assert.equal(graph.metadata.semantic_completion,false);
  checks.push('17来源日期仅规范空格、不改数字/原字/身份；本课六页无图且30命题无虚挂图，来源台账全67段；全书尚未完成');

  const anchor=cross.evidence[0].id;
  const requests=[
    ['search',{query:'初学者'},['search','初学者']],
    ['concept',{id:'背驰段',limit:20},['concept','背驰段','--limit','20']],
    ['neighbors',{id:'完成',depth:1,limit:100},['neighbors','完成','--depth','1','--limit','100']],
    ['evidence',{id:anchor},['evidence',anchor]],
    ['page',{documentId:'volume_1.pdf',page:306},['page','--document-id','volume_1.pdf','--page','306']],
    ['search',{query:'3272.41',scope:'source',limit:8},['search','3272.41','--scope','source','--limit','8']],
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
    intended_figure_links_checked:{claims:0,associations:0,unique_figures:0},
    core_sha256:sha(resolve(agent,'src/core.mjs')),desktop_core_sha256:sha(resolve(agent,'../chan-kg-desktop/vendor/core.mjs')),
    database_and_manifest_unchanged:true,pass:true,
    limits:['同模型边界检查与模块一致性，不是独立语义复核或Windows实际离线/PDF交互。','未补全完成充要算法、力度预测公式或认证历史预测/机构与宏观观点。']};
  writeFileSync(resolve(agent,'curation/source-audit/stage-c-l041-verification.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({graph_version:report.graph_version,boundary_groups:checks.length,parity:parity.length,figure_links:report.intended_figure_links_checked,pass:true}));
}finally{graph.close();desktop.close();}
