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
const claim = slug => { const c = graph.getClaim('upper-l032-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try {
  assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l032-c-stage-%' AND review_status='reviewed'").get().n, 41);
  assert.match(claim('a-formed-not-predict-b-required').text, /A已经走出不能.*B必有/);
  assert.match(claim('thirty-a-center-b-at-most-five').text, /b不能再含30分中枢.*最多是5分/);
  assert.match(claim('b-no-divergence-b-center-may-exceed-a').text, /B至少与A同级.*也可更大.*a`\+B/);
  assert.match(claim('daily-b-reclassify-c-use-daily-standard').text, /若B扩为日线.*后若有c段.*日线标准/);
  assert.match(claim('exit-standard-changes-when-b-becomes-daily').text, /不必机械等30分背驰/);
  assert.match(claim('renotation-a-prime-a-prime-author-accepts').text, /a`\+A`最好/);
  checks.push('41新增；A已形成不保证B/c，b最多5分不固定恰5分；B可更大需a`+B重组并按新级别判断，作者明确认可a`+A`记号但不认可读者所有推测');

  assert.match(claim('2915-is-gg-not-center-top-2894-correction').text, /明确更正.*最高点GG.*上沿在2894附近/);
  assert.equal(claim('2915-is-gg-not-center-top-2894-correction').evidence.length, 2);
  assert.match(claim('forecast-all-possibilities-qualified-not-blanket-ban').text, /正文.*预测无意义.*答疑.*允许.*所有可能/);
  assert.match(claim('feb28-2915-five-day-branches-not-confirmed').text, /能则期待.*不能则/);
  assert.match(claim('feb28-2915-five-day-branches-not-confirmed').review_note, /不是已形成第二5分/);
  assert.match(claim('praise-cctv-does-not-change-reader-identity').review_note, /不能.*可能性改成作者保证/);
  checks.push('2915原说与GG更正联合，ZG仅约2894而非2915.70；预测全分支允许与唯一预言分开，未来第二中枢/站稳未确认，CCTV表扬不改读者身份');

  assert.match(claim('nine-sublevel-extension-author-limit-with-wave-premise').text, /不能超过9个次级.*9个30分.*三日线/);
  assert.ok(claim('nine-sublevel-extension-author-limit-with-wave-premise').conditions.length);
  assert.notEqual(claim('nine-sublevel-extension-author-limit-with-wave-premise').ambiguity_status, 'none');
  assert.match(claim('straight-limit-up-no-wave-cannot-add-level').text, /没有波动的直线.*不能.*无扩展、延伸/);
  assert.match(claim('five-center-three-one-types-with-child-center').text, /三个1分走势类型.*至少含一个1分中枢.*若自选1分最低/);
  assert.match(claim('five-center-three-one-types-with-child-center').review_note, /三个1分类型与三根1分K不等价/);
  checks.push('延伸九次级及作者周线判断保留有波动前提和阈值待核，不按9根K/时间升格；严格5分须三1分类型，自选最低三K非等价且直上直下无重合不成中枢');

  assert.match(claim('third-buy-retest-at-least-sublevel-three-down-up-down').text, /至少一个次级回抽.*三段下上下/);
  assert.match(claim('600888-reader-profit-not-daily-third-buy').text, /否定.*仍在.*至少日线/);
  assert.match(claim('600888-reader-profit-not-daily-third-buy').review_note, /13%自述未被认证/);
  assert.match(claim('third-buy-above-center-strong-stock-index-exception').exceptions.join(''), /指数单日大幅下跌/);
  assert.match(claim('order-book-anomaly-only-in-valid-nesting').text, /不是每次盘口异常/);
  assert.match(claim('five-divergence-rebuy-parent-rise-vs-nesting').review_note, /未直接回答.*GG.*数学条件/);
  checks.push('三买回抽至少次级三段非任意三K；600888获利未认证三买，日线以上个例及指数单日大跌例外保留；盘口异动需套内，未答跨多个GG扩展条件不补答案');

  assert.match(claim('subminute-time-chart-or-one-minute-hist-not-lines').text, /1分以下.*1分MACD红绿柱.*不看黄白线/);
  assert.match(claim('600550-no-five-without-macd-lines-return-zero').text, /黄白线未回0轴.*尾盘低点为1分以下.*非5分/);
  assert.match(claim('subminute-time-chart-or-one-minute-hist-not-lines').review_note, /不取消普通本级MACD回轴/);
  assert.match(claim('divergence-level-not-rise-level-without-nesting').text, /无必然对应.*必须满足区间套/);
  assert.match(claim('mar1-subminute-turns-center-third-sell-next-day').text, /次日.*若有三卖.*否则/);
  checks.push('1分柱波辨1分以下与普通本级黄白线回轴分对象，600550低点非5分；背驰/上涨级别对应需区间套，次日三卖分支不等当日已确认');

  for (const short of ['0236-b002', '0236-b003', '0236-b004', '0236-b005', '0237-b000']) {
    assert.equal(source(short).role, 'author_commentary'); assert.equal(source(short).published_at, '2007-02-28');
  }
  assert.equal(source('0236-b001').published_at, '2007-02-28 08:44:37');
  for (const short of ['0237-b002', '0237-b004', '0237-b006', '0242-b011']) assert.equal(source(short).role, 'reader');
  assert.equal(source('0237-b006').speaker, 'CCTV');
  const links = {
    'fall-to-third-buy-and-416-gain-case': ['0233-b002', ['0233-fig1']],
    'unicom-936-945-552-and-resistance-line-case': ['0236-b000', ['0235-fig1', '0236-fig1']],
    'close-supplement-live-regroup-1351-third-buy': ['0236-b003', ['0237-fig1']],
    '2915-is-gg-not-center-top-2894-correction': ['0236-b004', ['0237-fig1']],
    'feb28-2915-five-day-branches-not-confirmed': ['0236-b004', ['0237-fig1']],
    'mar1-2800-thirty-center-five-day-fail-case': ['0241-b003', ['0241-fig1']],
    'mar1-subminute-turns-center-third-sell-next-day': ['0241-b008', ['0241-fig1']],
  };
  for (const [slug, [passage, figures]] of Object.entries(links)) {
    const e = claim(slug).evidence.find(e => e.passage_id === 'volume_1-a53e99c37ca5-p' + passage);
    assert.deepEqual(e.figure_ids, figures.map(f => 'volume_1-a53e99c37ca5-p' + f));
    assert.equal(e.figures.length, figures.length);
  }
  const figs = graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 233 AND 243").all();
  assert.equal(figs.filter(f => f.origin_status === 'later_annotation').length, 2); assert.equal(figs.filter(f => f.origin_status === 'unverified').length, 3);
  assert.equal(graph.db.prepare("SELECT processing_status FROM units WHERE id='lesson-032'").get().processing_status, 'semantic_read_with_pending');
  assert.equal(graph.metadata.semantic_completion, false);
  checks.push('5收盘补充仅日粒度且角色正确，早课8:44不改、CCTV/其他读者不混；7命题8图关联逐项验证，5图2后加3未核，32有记录而全书未完成');
  const anchor = claim('2915-is-gg-not-center-top-2894-correction').evidence.find(e => e.passage_id.endsWith('p0236-b004')).id;
  const requests = [
    ['search', { query: '2915所指是围绕中枢波动的最高点GG' }, ['search', '2915所指是围绕中枢波动的最高点GG']],
    ['concept', { id: 'GG', limit: 20 }, ['concept', 'GG', '--limit', '20']],
    ['neighbors', { id: 'GG', depth: 1, limit: 100 }, ['neighbors', 'GG', '--depth', '1', '--limit', '100']],
    ['evidence', { id: anchor }, ['evidence', anchor]],
    ['page', { documentId: 'volume_1.pdf', page: 237 }, ['page', '--document-id', 'volume_1.pdf', '--page', '237']],
    ['search', { query: '然后突破B直接上去', scope: 'source', limit: 8 }, ['search', '然后突破B直接上去', '--scope', 'source', '--limit', '8']],
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
      '未验证收益/无风险主张、历史实盘、9段完整阈值和所有中枢扩展程序；32收盘补入具体时间未载。'] };
  writeFileSync(resolve(agent, 'curation/source-audit/stage-c-l032-verification.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ graph_version: report.graph_version, boundary_groups: checks.length, parity: parity.length, pass: true }));
} finally { graph.close(); desktop.close(); }
