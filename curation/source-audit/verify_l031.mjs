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
const claim = slug => { const c = graph.getClaim('upper-l031-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try {
  assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l031-c-stage-%' AND review_status='reviewed'").get().n, 47);
  assert.match(claim('two-phases-cost-zero-then-earn-shares').text, /成本为零前先降到零.*为零后再挣股票.*至少月线以上卖点/);
  assert.match(claim('two-phases-cost-zero-then-earn-shares').review_note, /不等剩余股票无经济价值或无风险/);
  assert.match(claim('before-zero-swing-must-not-increase-plan-shares').review_note, /不等盘中卖出回补时股数永不变化/);
  assert.match(claim('after-zero-reinvest-swing-proceeds-for-more-shares').conditions.join(''), /收回最初投入.*较低位置回补/);
  assert.match(claim('double-price-large-sell-recover-initial-capital').review_note, /不是价格一翻倍立即机械卖一半/);
  checks.push('47新增；先降成本后挣股分阶段，零现金成本非经济无风险；计划总量非时刻股数，回补卖出所得非重新投本金，翻倍/大卖点不改机械卖半');

  assert.match(claim('prepared-one-entry-no-upward-add-planned-allocation').text, /事前定好.*一次性.*留机动资金/);
  assert.match(claim('skill-based-entry-size-three-vs-eight-thousand').text, /技术好可先8千.*不好可先3千.*中线形态保持.*次级买点/);
  assert.notEqual(claim('prepared-one-entry-no-upward-add-planned-allocation').ambiguity_status, 'none');
  assert.ok(claim('down-hold-has-thesis-and-severe-shape-exceptions').exceptions.length);
  assert.match(claim('down-hold-has-thesis-and-severe-shape-exceptions').review_note, /不补为两个各自充分的独立信号/);
  assert.match(claim('midterm-entry-at-least-daily-buy-not-falling-blind').text, /中线仓位至少应在日线级别买点/);
  assert.match(claim('two-three-stocks-versus-dozens-large-capital-exception').exceptions.join(''), /特别大/);
  assert.match(claim('long-pressure-free-funds-and-leverage-story').review_note, /原文未具名.*不由深天地A配图认证/);
  checks.push('准备充分一次性与弱技术3千分批另存，机动1/10非全仓；不抛有除非条款且短语关系未形式化，日线中线买点与大资金多股例外保留，透支故事不凭图认证');

  assert.match(claim('capital-zero-point-five-float-does-not-decide-entry').text, /取决于买入位置.*0.5%流通盘/);
  assert.match(claim('capacity-thirty-float-versus-minute-ten-day-volume').text, /流通盘千分之五.*30分以上.*1分.*10天均量的1%/);
  assert.match(claim('capacity-thirty-float-versus-minute-ten-day-volume').review_note, /两个不同分母不可混用/);
  assert.notEqual(claim('capacity-thirty-float-versus-minute-ten-day-volume').ambiguity_status, 'none');
  assert.match(claim('consolidation-type-contains-one-center-not-equal-center').text, /盘整与中枢不是同一概念/);
  assert.match(claim('perfect-means-center-eventually-forms-count-type').text, /趋势两个以上、盘整一个/);
  assert.match(claim('center-framework-earlier-kiss-only-reference').text, /前面的吻等均线说法可只作参考/);
  checks.push('容量0.5%流通盘与1分10天均量1%分母分开，非小量必不套/可成交实测；盘整含一相应中枢非中枢本身，趋势两个以上，吻只是参考');

  assert.match(claim('weekly-three-legs-original-explicitly-qualified').text, /先把0124—0206.*不太严谨.*第一段内部第三小段/);
  assert.equal(claim('weekly-three-legs-original-explicitly-qualified').evidence.length, 2);
  assert.match(claim('weekly-center-first-daily-then-expand-case').text, /先形成一个日线中枢.*扩张.*第一段里面第三小段/);
  assert.match(claim('weekly-center-first-daily-then-expand-case').review_note, /不宣称已形成完整周线中枢/);
  assert.match(claim('feb27-first-minute-center-2869-next-conditional').text, /次日若开盘不马上回2869之上/);
  assert.match(claim('formed-thirty-center-watch-second-then-nest').review_note, /不等第二个必背驰/);
  checks.push('周线前两段粗说与作者同日明确不严谨的收窄联合存证，先日线后扩张/第一段第三小段未改已成周线；2869次日条件与第二中枢关注不改已完成');

  assert.match(claim('standard-trend-nesting-with-sudden-break-exception').conditions.join(''), /标准/);
  assert.match(claim('standard-trend-nesting-with-sudden-break-exception').exceptions.join(''), /突发事件/);
  assert.match(claim('feb15-center-1048-1129-third-buy-1413').text, /1048—1129.*1114—1129.*前三段同级.*1413/);
  assert.match(claim('third-buy-not-necessarily-after-consolidation-divergence').text, /不要求每个三买都先有盘背/);
  assert.match(claim('a-c-consolidation-and-internal-c-divergence-nesting').text, /A与C比较.*C内部次级.*一般/);
  assert.match(claim('connections-below-one-and-c-must-rise-in-up-down-up').text, /1分以下.*微微向上.*不符上下上/);
  assert.match(claim('099-five-main-fall-even-one-divergence-wait-parent').text, /即使有1分背驰.*等5分进入背驰段/);
  checks.push('标准嵌套有突发破裂例外，分钟中枢三段同级/延伸/1413个例分开；三买可无盘背，A-C与C内部两重比较，反弹C真上行与5分主跌父段限制保留');

  for (const short of ['0230-b008', '0231-b002', '0232-b005', '0232-b012']) assert.equal(source(short).role, 'reader');
  assert.equal(source('0231-b003').role, 'author_reply');
  assert.equal(source('0227-b001').published_at, '2007-02-26 15:50:13');
  assert.equal(source('0228-b002').published_at, '2007-02-27 15:31:20');
  const figs = graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 219 AND 232").all();
  assert.equal(figs.filter(f => f.origin_status === 'later_annotation').length, 5); assert.equal(figs.filter(f => f.origin_status === 'unverified').length, 1);
  assert.equal(graph.db.prepare("SELECT processing_status FROM units WHERE id='lesson-031'").get().processing_status, 'semantic_read_with_pending');
  assert.equal(graph.metadata.semantic_completion, false);
  checks.push('嵌引作者原话/周线质疑仍读者，原作者明确限定独立；日期与全文不改，仅6图5后加1未核，31有记录而全书未完成');
  const anchor = claim('weekly-three-legs-original-explicitly-qualified').evidence[0].id;
  const requests = [
    ['search', { query: '成本为零前先降到零' }, ['search', '成本为零前先降到零']],
    ['concept', { id: '零成本持仓', limit: 20 }, ['concept', '零成本持仓', '--limit', '20']],
    ['neighbors', { id: '交易容量', depth: 1, limit: 100 }, ['neighbors', '交易容量', '--depth', '1', '--limit', '100']],
    ['evidence', { id: anchor }, ['evidence', anchor]],
    ['page', { documentId: 'volume_1.pdf', page: 231 }, ['page', '--document-id', 'volume_1.pdf', '--page', '231']],
    ['search', { query: '第三段不下来的话', scope: 'source', limit: 8 }, ['search', '第三段不下来的话', '--scope', 'source', '--limit', '8']],
    ['coverage', {}, ['coverage']],
  ];
  const parity = [];
  for (const [command, args, argv] of requests) {
    const a = JSON.parse(JSON.stringify(graph.query(command, args)));
    assert.deepEqual(JSON.parse(JSON.stringify(desktop.query(command, args))), a);
    const cli = spawnSync(process.execPath, [resolve(agent, 'bin/chan-kg.mjs'), ...argv, '--kb', root], { encoding: 'utf8', maxBuffer: 24 * 1024 * 1024 });
    assert.equal(cli.status, 0, cli.stderr); assert.deepEqual(JSON.parse(cli.stdout), a);
    parity.push({ command, args, cli_matches_shared: true, desktop_module_matches_shared: true });
  }
  assert.deepEqual({ database: sha(resolve(root, 'graph.sqlite')), manifest: sha(resolve(root, 'manifest.json')) }, before);
  const report = { graph_version: graph.metadata.graph_version, schema_version: graph.metadata.schema_version, checks, parity,
    core_sha256: sha(resolve(agent, 'src/core.mjs')), desktop_core_sha256: sha(resolve(agent, '../chan-kg-desktop/vendor/core.mjs')),
    database_and_manifest_unchanged: true, pass: true,
    limits: ['同模型边界检查与模块一致性，不是独立语义审查、历史行情/测度论证明核验或Windows实际离线/PDF交互。',
      '未验证零成本策略利润或风险保证、历史账户和未具名故事身份、容量冲击成本或所有级别的唯一分段算法。'] };
  writeFileSync(resolve(agent, 'curation/source-audit/stage-c-l031-verification.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ graph_version: report.graph_version, boundary_groups: checks.length, parity: parity.length, pass: true }));
} finally { graph.close(); desktop.close(); }
