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
const claim = slug => { const c = graph.getClaim('upper-l030-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try {
  assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l030-c-stage-%' AND review_status='reviewed'").get().n, 27);
  assert.match(claim('pure-trading-price-not-information-completeness').text, /不论价格是否充分反映信息/);
  assert.match(claim('ordered-price-path-and-irreversible-trading-time').text, /不可逆.*今天交易可改成昨天或直接不算/);
  assert.match(claim('price-sufficient-market-author-defined').text, /时间不可逆.*完全等价反映在价格轨迹/);
  assert.match(claim('price-sufficient-market-author-defined').review_note, /不等市场价格已反映全部信息/);
  assert.match(claim('retroactive-cancellation-non-price-sufficient-example').review_note, /不作为.*现行交易撤销法律规则/);
  checks.push('27条新增；作者价格充分有效为交易时间/轨迹定义，不等全部信息反映，交易随意抹除是定义外情形而非普通停牌');

  assert.equal(claim('two-premises-and-absolute-validity-author-claim').conditions.length, 2);
  assert.match(claim('two-premises-and-absolute-validity-author-claim').text, /只要两者存在.*绝对有效/);
  assert.notEqual(claim('two-premises-and-absolute-validity-author-claim').ambiguity_status, 'none');
  assert.match(claim('two-premises-and-absolute-validity-author-claim').review_note, /72课.*主要针对动力学/);
  assert.match(graph.getClaim('lower-l072-dynamics-premises').conditions.join(''), /动力学/);
  assert.match(claim('absolute-convergence-only-one-participant-boundary').text, /每笔交易都仅他参与.*仍持有1股/);
  assert.match(claim('zero-vector-follow-market-metaphor').review_note, /不构造.*向量数值模型/);
  checks.push('两前提/绝对性保留作者归属与未证状态，72动力学范围另存；极端1股非安全阈值，不动点及零向量比喻不补公理/数值模型');

  assert.match(claim('entered-divergence-leg-can-break-and-reassess').text, /进入背驰段.*小级别结构可能突然破裂.*新走势重新判断/);
  assert.match(claim('entered-divergence-leg-can-break-and-reassess').review_note, /不等已经成功背驰.*不.*必可提前退出/);
  assert.notEqual(claim('greater-level-control-energy-and-capital-skill-view').ambiguity_status, 'none');
  assert.match(claim('same-theory-different-capital-and-trader-outcomes').text, /资金规模.*基本面把握.*不同结果/);
  assert.match(claim('understanding-versus-practice-seen-heard-learned-done').text, /不保证操作能力/);
  checks.push('进入背驰段仍可破裂需重估，不等成功背驰或无损成交；周线控制/资金功力只作者经验，同法不同结果及理解/实践分开');

  assert.match(claim('first-center-next-center-lower-level-strength').text, /若不出现背驰段.*第二个中枢.*比第一个低/);
  assert.match(claim('first-center-next-center-lower-level-strength').review_note, /不能冒充同级趋势中枢计数/);
  assert.match(claim('one-extending-center-not-numbered-many').text, /延伸时就只有一个中枢/);
  assert.match(claim('600607-after-buy-not-on-thirty-buy').text, /出现后的走势发展.*没有买在/);
  assert.match(claim('third-buy-localize-like-first-below-sublevel').review_note, /不等三买在本级定义上就是一买/);
  assert.match(claim('000581-third-buy-wait-completed-sublevel-retest').text, /次级回抽不能再进中枢.*不能未走出来就冲入/);
  checks.push('较低第二中枢不计成同级趋势第二，延伸仍一中枢；600607非买在30分买点，三买定位类一买不改本级定义，000581需次级走出且回抽不入');

  assert.match(claim('lowest-three-consecutive-k-have-direction').text, /连续三根且有方向.*从高位下来.*下上下/);
  assert.ok(claim('lowest-three-consecutive-k-have-direction').conditions.length);
  assert.match(claim('lowest-three-consecutive-k-have-direction').review_note, /非后期严格1分必由三根K/);
  assert.match(claim('novice-fundamental-near-bottom-large-buy-selection').text, /新手.*基本面有支持.*离底部不远.*大级别出现买点.*熟练后另论/);
  assert.ok(source('0218-b009').text.includes('离底部不元'));
  assert.match(claim('feb13-2850-one-minute-divergence-not-five').text, /定为1分钟.*读者10:45称5分/);
  checks.push('早期自选最低三K须连续且有方向，从高位下来才是下上下例；新手三条件/熟练例外与原不元字形保留，10:45更正为1分');

  assert.equal(source('0216-b005').published_at, '2007-02-13 15:09:43');
  assert.equal(source('0217-b000').published_at, '2007-02-14 15:13:25');
  assert.equal(source('0218-b017').role, 'reader'); assert.equal(source('0218-b017').speaker, 'CCTV');
  assert.equal(source('0218-b014').role, 'reader');
  assert.equal(graph.db.prepare("SELECT count(*) n FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 213 AND 218").get().n, 0);
  assert.equal(graph.db.prepare("SELECT processing_status FROM units WHERE id='lesson-030'").get().processing_status, 'semantic_read_with_pending');
  assert.equal(graph.metadata.semantic_completion, false);
  checks.push('1跨页解盘改2/14，前段2/13不改；CCTV及大盘仍读者，实际六页无配图；30有记录而全书未完成');
  const anchor = claim('ordered-price-path-and-irreversible-trading-time').evidence[0].id;
  const requests = [
    ['search', { query: '进入背驰段后遇绝对突发事件' }, ['search', '进入背驰段后遇绝对突发事件']],
    ['concept', { id: '交易时间不可逆', limit: 20 }, ['concept', '交易时间不可逆', '--limit', '20']],
    ['neighbors', { id: '交易延异性', depth: 1, limit: 100 }, ['neighbors', '交易延异性', '--depth', '1', '--limit', '100']],
    ['evidence', { id: anchor }, ['evidence', anchor]],
    ['page', { documentId: 'volume_1.pdf', page: 218 }, ['page', '--document-id', 'volume_1.pdf', '--page', '218']],
    ['search', { query: '第三类买点好象一定是次级别的', scope: 'source', limit: 8 }, ['search', '第三类买点好象一定是次级别的', '--scope', 'source', '--limit', '8']],
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
      '未验证作者绝对有效主张、公理化/不动点形式证明、周线控制界限或实测操作效率。'] };
  writeFileSync(resolve(agent, 'curation/source-audit/stage-c-l030-verification.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ graph_version: report.graph_version, boundary_groups: checks.length, parity: parity.length, pass: true }));
} finally { graph.close(); desktop.close(); }
