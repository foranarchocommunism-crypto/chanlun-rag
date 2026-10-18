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
const claim = slug => { const c = graph.getClaim('upper-l026-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try {
  assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l026-c-stage-%' AND review_status='reviewed'").get().n, 47);
  assert.match(claim('foreseeable-trading-continuation-level-horizon').text, /可预见.*继续交易.*日线.*一周.*1分钟/);
  assert.match(claim('sudden-stop-or-cancellation-invalidates-premise').text, /突然停止交易.*事后不算.*前提失效/);
  assert.match(claim('ordinary-suspension-vs-permanent-stop-author-claim').text, /停牌.*不会被突然停止而永远没有/);
  assert.notEqual(claim('ordinary-suspension-vs-permanent-stop-author-claim').ambiguity_status, 'none');
  assert.match(claim('319-last-exit-not-from-chart-self-report').text, /并非看图/);
  assert.match(claim('capital-deadline-self-imposed-trading-stop').text, /资金有限期.*停止时限/);
  assert.match(claim('deadline-lower-frame-last-resort').text, /尽量.*没有办法的办法/);
  checks.push('47新增；可交易期限/交易有效前提与突然终止/取消例外、普通停牌不同，319自述明确非看图，降级只尽量控制期限风险');

  assert.match(claim('positive-cost-risk-and-negative-cost-ambition').text, /负价格.*作者|作者.*负价格/);
  assert.match(claim('positive-cost-risk-and-negative-cost-ambition').review_note, /不把负价格改成证券市场报价为负/);
  assert.notEqual(claim('positive-cost-risk-and-negative-cost-ambition').ambiguity_status, 'none');
  assert.match(claim('warrant-keep-original-size-no-added-position-self-report').text, /认购权证.*负2.8.*恢复原数量.*绝不额外加仓/);
  assert.match(claim('warrant-keep-original-size-no-added-position-self-report').review_note, /不猜为前课038004认沽/);
  assert.match(claim('minute-fifty-thousand-shares-self-example').text, /5万股.*1毛.*可能约4000/);
  assert.notEqual(claim('long-capital-plus-skill-unbeatable-author-formula').ambiguity_status, 'none');
  checks.push('负成本/负报价、目标原数量/逐刻数量不混；未具名认购不猜认沽；手续费示例和战无不胜为作者自述而非收益实证');

  assert.match(claim('thirty-minute-strength-changes-rebuy-level').text, /30分钟很强.*1分钟.*30分钟很弱.*至少.*30分钟/);
  assert.match(claim('large-frame-before-short-trade-up-down-sides').text, /震荡.*上涨.*夹空.*下跌.*被套.*末段急拉.*1分钟/);
  assert.match(claim('index-signal-only-if-stock-aligned').text, /个股与大盘一致为条件/);
  assert.match(claim('novice-near-bottom-at-least-daily-entry').text, /特别新手.*至少日线买点.*1\/3.*单边上扬除外/);
  assert.match(claim('unskilled-small-position-quarter-or-third').text, /不熟练且仓位不太大.*1\/3或1\/4.*不能追高/);
  assert.match(claim('fast-drop-macd-rebuy-size-and-prolonged-fall-exception').text, /小资金5分.*特别连绵跌势除外/);
  checks.push('级别/数量视角仍受强弱、日线方向、指数个股一致、小资金与连绵跌势限制；1/3或1/4及新手日线买点条件保留');

  assert.match(claim('long-entry-fundamentals-short-tech').text, /中长线.*基本面.*短线.*技术.*挑好一点/);
  assert.match(claim('long-selection-not-casual-cut-conditional').text, /中长线谨慎选择.*仍看好.*随意斩仓/);
  assert.match(claim('bull-no-light-cut-delisting-exception').text, /牛市.*相应技术.*面临退市.*除外/);
  assert.match(claim('600677-earnings-trap-exit-half-or-small-position').text, /仓位不多.*重仓.*减半/);
  assert.match(graph.getClaim('upper-l013-c-stage-average-second-entry-break-old-bear-low-exit').text, /程序有问题.*反弹中出清/);
  assert.match(claim('600677-week250-59-conditional').text, /5.9.*不有效跌破/);
  assert.notEqual(claim('tcl-recovery-conditional-author-recap').ambiguity_status, 'none');
  checks.push('纯技术与中长线基本面分工、不轻斩仓与重仓减半/退市/旧买点失效防护并存；5.9和TCL后评是条件化历史判断');

  assert.match(claim('chihong-center-jul27-aug26-no-average').text, /中枢与均线无关.*727到826/);
  assert.match(claim('600316-third-buy-needs-preceding-first-second').review_note, /不推出二三必紧接或价序永无例外/);
  assert.match(claim('600836-intraday-second-buy-not-chase').text, /14:30.*1分钟第一中枢.*回抽二买.*拉起后再买/);
  assert.match(claim('600836-thirty-minute-first-second-dates').text, /1月4日10点左右.*1月18日11点/);
  assert.notEqual(claim('600343-earnings-one-yuan-author-forecast').ambiguity_status, 'none');
  assert.notEqual(claim('larger-short-difference-ten-percent-author-claim').ambiguity_status, 'none');
  assert.match(claim('mindset-requires-technical-insight').review_note, /不是对读者.*预言认可/);
  checks.push('中枢无关均线、三买反问和600836时间按原文保存，不造邻接价序定律；业绩1元/降成本10%未实证，读者预言不当作者认可');

  assert.equal(source('0173-b010').published_at, '2007-01-31 15:24:33');
  for (const short of ['0173-b011', '0173-b012', '0173-b013', '0173-b014', '0174-b000', '0174-b001']) assert.equal(source(short).published_at, '2007-02-01 15:32:19');
  assert.match(source('0173-b013').text, /周线中线/);
  assert.match(source('0176-b005').text, /顺便斩仓/);
  assert.equal(source('0170-b008').role, 'reader');
  const figs = graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 166 AND 178").all();
  assert.equal(figs.filter(f => f.origin_status === 'later_annotation').length, 4); assert.equal(figs.filter(f => f.origin_status === 'unverified').length, 2);
  assert.equal(graph.db.prepare("SELECT processing_status FROM units WHERE id='lesson-026'").get().processing_status, 'semantic_read_with_pending');
  assert.equal(graph.metadata.semantic_completion, false);
  checks.push('6段日期修正只管嵌头后文，记者转载仍读者，原词周线中线/顺便不改；6图4后加2未核，26有阅读记录而全书未完成');

  const anchor = claim('foreseeable-trading-continuation-level-horizon').evidence[0].id;
  const requests = [
    ['search', { query: '资金有限期等于自行设置交易停止时限' }, ['search', '资金有限期等于自行设置交易停止时限']],
    ['concept', { id: '交易有效性', limit: 20 }, ['concept', '交易有效性', '--limit', '20']],
    ['neighbors', { id: '资金期限', depth: 1, limit: 100 }, ['neighbors', '资金期限', '--depth', '1', '--limit', '100']],
    ['evidence', { id: anchor }, ['evidence', anchor]],
    ['page', { documentId: 'volume_1.pdf', page: 173 }, ['page', '--document-id', 'volume_1.pdf', '--page', '173']],
    ['search', { query: '如无意外', scope: 'source', limit: 8 }, ['search', '如无意外', '--scope', 'source', '--limit', '8']],
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
    limits: ['同模型来源边界检查与模块一致性，不是独立语义审查、财务回测或Windows实际离线/PDF交互。',
      '作者无风险/战无不胜强主张、负成本交易自述和业绩预测均未由本检查证实。'] };
  writeFileSync(resolve(agent, 'curation/source-audit/stage-c-l026-verification.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ graph_version: report.graph_version, boundary_groups: checks.length, parity: parity.length, pass: true }));
} finally { graph.close(); desktop.close(); }
