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
const claim = slug => { const c = graph.getClaim('upper-l040-c-stage-' + slug); assert.ok(c, slug); return c; };
const source = short => graph.db.prepare('SELECT * FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p' + short);
const checks = [];
try {
  assert.equal(graph.db.prepare("SELECT count(*) n FROM claims WHERE id LIKE 'upper-l040-c-stage-%' AND review_status='reviewed'").get().n, 34);
  assert.match(claim('small-entry-large-rise-keep-small-or-upgrade-partial-small').review_note, /不是小级买错被套就随意改长线/);
  assert.match(claim('Ai-divergence-next-protection-break-forms-higher-center').text, /i偶时Ai\+3跌破Ai高点.*i奇时Ai\+3升破Ai低点.*Ai\+1、Ai\+2、Ai\+3/);
  assert.match(claim('A0-through-At-equals-B1-B2-thirty-decomposition-switch').text, /A0\+A1\+…\+At=B1\+B2/);
  assert.match(claim('A0-through-At-equals-B1-B2-thirty-decomposition-switch').review_note, /换档依原式30分分解已成立/);
  assert.match(claim('N-layer-fugue-each-capital-shares-rhythm').text, /每层对应一定资金筹码/);
  assert.match(claim('each-layer-independent-and-integrated-own-level-rhythm').review_note, /并非风险完全无相关/);
  checks.push('34新增；盘背后奇偶保护位演化次高中心，A0至At可重分B1+B2才换档；非套牢改中线，N层各自筹码节奏非风险互不相关，收益预期不作保证');

  assert.match(claim('non-MACD-moving-average-area-alternative').text, /短期与长期均线之间的面积/);
  assert.match(claim('non-MACD-moving-average-area-alternative').review_note, /未给长短周期、面积积分区间/);
  assert.match(claim('subminute-case-one-minute-green-area-two-sum-versus-one').text, /1分钟以下.*1分MACD.*两个绿柱面积之和/);
  assert.match(claim('subminute-case-one-minute-green-area-two-sum-versus-one').review_note, /不能抽成任意两根单柱高度/);
  assert.match(claim('morning-five-top-sell-rhythm-before-bottom-precision').text, /若上午5分明显顶背驰先卖/);
  assert.deepEqual(claim('000802-one-minute-above-fifteen-bottom-case').evidence[0].figure_ids, []);
  assert.match(claim('time-window-auxiliary-first-basic-framework').text, /辅助.*基本理论框架/);
  checks.push('均线面积另一路未给完整周期积分算法，1分以下借1分MACD为具体双面积和/单面积例非柱高计数；先卖节奏有已识别顶背前提，指数图不挂000802股例，时间窗仅辅助');

  for (const p of ['0296-b002', '0296-b003', '0296-b004', '0296-b006', '0296-b007']) assert.equal(source(p).role, 'reader');
  assert.match(claim('standard-divergence-two-small-trends-inside-trend').text, /最标准背驰.*趋势中比较两段小级别趋势/);
  assert.match(claim('standard-divergence-two-small-trends-inside-trend').review_note, /未逐项证明A>B也属标准/);
  assert.match(claim('divergence-method-extension-even-same-direction-center-waves').review_note, /类似方法可用不等都改名标准趋势背驰/);
  assert.match(graph.getClaim('upper-l037-c-stage-trend-divergence-requires-trend-and-same-level-a-b').text, /A、B为同级别/);
  checks.push('17/24/37引文是读者，作者标准两小趋势与震荡类似比较推广分开；未以无矛盾三字证明读者A>B标准或撤37同级A/B和相对层级待核');

  assert.notEqual(claim('any-underwater-not-buy-point-author-claim-tension').ambiguity_status, 'none');
  assert.match(claim('any-underwater-not-buy-point-author-claim-tension').review_note, /39称非最低那笔总有被套/);
  assert.match(graph.getClaim('upper-l039-c-stage-not-lowest-print-may-be-underwater-direction-author-view').text, /总有被套/);
  assert.notEqual(claim('mar29-zero-cost-safe-negative-only-profit-author-strong-wording').ambiguity_status, 'none');
  assert.match(claim('mar29-zero-cost-safe-negative-only-profit-author-strong-wording').review_note, /非全部经济风险/);
  assert.notEqual(claim('rhythm-makes-unbeatable-and-lower-cost-self-report').ambiguity_status, 'none');
  assert.match(claim('good-stock-buy-point-large-level-performance-metaphor').review_note, /不替代企业财务业绩/);
  checks.push('39总有被套与40被套非买点的未明范围张力并存，不以事后浮亏定义正确；零成本安全/负成本利润/无人能胜为未核强词，好垃圾绩优只是时点修辞');

  assert.match(claim('small-capital-two-three-sectors-one-stock-each').review_note, /未认可读者10至20万及20%/);
  assert.notEqual(claim('fund-weakness-vs-stable-long-no-cashout-author-view').ambiguity_status, 'none');
  assert.match(claim('five-day-trim-versus-long-term-fundamental-valuation').text, /跌破5日线减仓.*真中长线.*基本面/);
  assert.match(claim('next-day-drop-possible-not-certain-many-participants-current').review_note, /可能非必然/);
  for (const p of ['0297-b009', '0297-b010', '0297-b011', '0298-b000', '0298-b001', '0298-b002', '0298-b003', '0299-b008']) {
    assert.equal(graph.db.prepare("SELECT count(*) n FROM evidence e JOIN claims c ON c.id=e.claim_id WHERE c.review_status='reviewed' AND e.passage_id=?").get('volume_1-a53e99c37ca5-p' + p).n, 0);
  }
  const ledger = readFileSync(resolve(agent, 'curation/upper/c_stage_l040.coverage.jsonl'), 'utf8').trim().split('\n').map(line => JSON.parse(line));
  assert.equal(ledger.length, 125);
  assert.equal(ledger.filter(r => r.result === 'nontechnical-political-economy-essay-context').length, 7);
  assert.equal(source('0301-b002').role, 'reader');
  checks.push('配置问中20%/金额不认证，基金安全概括未分类；技术5日减仓与真长线基本面分境，次日跌只是可能；7段货币评论和未名基金指控只作原文上下文，读者动员不进作者知识');

  const dateGroups = [
    [['0292-b002', '0293-b000', '0293-b001', '0293-b002'], '2007-03-27 21:29:47'],
    [['0293-b003', '0293-b004', '0293-b005'], '2007-03-28 15:24:11'],
    [['0298-b007', '0298-b008', '0299-b000', '0299-b001'], '2007-03-29 21:44:58'],
  ];
  for (const [passages, stamp] of dateGroups) for (const p of passages) assert.equal(source(p).published_at, stamp);
  assert.equal(source('0292-b001').published_at, '2007-03-27 12:57:02');
  assert.match(source('0292-b001').text, /2007-03-2721:29:47$/);
  assert.equal(source('0298-b006').published_at, '2007-03-29 12:41:24');
  assert.match(source('0298-b006').text, /2007-03-2921:44:58$/);
  const links = {
    'Ai-divergence-next-protection-break-forms-higher-center': ['0291-b002', ['0291-fig1', '0291-fig2']],
    'mar27-night-time-window-three-day-month-close-case': ['0292-b002', ['0292-fig1', '0292-fig2']],
    'mar27-second-line-earnings-relative-stability-author-view': ['0293-b001', ['0292-fig1', '0292-fig2']],
    'novice-five-day-hold-fallback': ['0293-b002', ['0292-fig2']],
    'mar27-balanced-center-no-new-low-less-down-force': ['0293-b012', ['0294-fig1']],
    'subminute-case-one-minute-green-area-two-sum-versus-one': ['0295-b009', ['0295-fig1', '0296-fig1']],
    'morning-five-top-sell-rhythm-before-bottom-precision': ['0295-b010', ['0295-fig1', '0296-fig1']],
  };
  for (const [slug, [passage, figures]] of Object.entries(links)) {
    const e = claim(slug).evidence.find(e => e.passage_id === 'volume_1-a53e99c37ca5-p' + passage);
    assert.deepEqual(e.figure_ids, figures.map(f => 'volume_1-a53e99c37ca5-p' + f)); assert.equal(e.figures.length, figures.length);
  }
  const figs = graph.db.prepare("SELECT origin_status FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page BETWEEN 291 AND 296").all();
  assert.equal(figs.length, 7); assert.equal(figs.filter(f => f.origin_status === 'later_annotation').length, 3);
  assert.equal(figs.filter(f => f.origin_status === 'unverified').length, 4);
  assert.equal(graph.db.prepare("SELECT processing_status FROM units WHERE id='lesson-040'").get().processing_status, 'semantic_read_with_pending');
  assert.equal(graph.metadata.semantic_completion, false);
  checks.push('11段日期分三夜/收盘组、午间和尾头字符保留；7命题12配图逐项确认，7图3后加4原发未核；全书未完成');

  const anchor = claim('any-underwater-not-buy-point-author-claim-tension').evidence[0].id;
  const requests = [
    ['search', { query: '多重赋格操作' }, ['search', '多重赋格操作']],
    ['concept', { id: '多重赋格操作', limit: 20 }, ['concept', '多重赋格操作', '--limit', '20']],
    ['neighbors', { id: '时间之窗', depth: 1, limit: 100 }, ['neighbors', '时间之窗', '--depth', '1', '--limit', '100']],
    ['evidence', { id: anchor }, ['evidence', anchor]],
    ['page', { documentId: 'volume_1.pdf', page: 296 }, ['page', '--document-id', 'volume_1.pdf', '--page', '296']],
    ['search', { query: '17课', scope: 'source', limit: 8 }, ['search', '17课', '--scope', 'source', '--limit', '8']],
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
    intended_figure_links_checked: { claims: 7, associations: 12, unique_figures: 7 },
    core_sha256: sha(resolve(agent, 'src/core.mjs')), desktop_core_sha256: sha(resolve(agent, '../chan-kg-desktop/vendor/core.mjs')),
    database_and_manifest_unchanged: true, pass: true,
    limits: ['同模型边界检查与模块一致性，不是独立语义审查或Windows实际离线/PDF交互。', '未补全换档/均线面积算法，未消除被套/安全强词张力或认证政治经济观点、基金指控、历史收益和时间窗概率。'] };
  writeFileSync(resolve(agent, 'curation/source-audit/stage-c-l040-verification.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ graph_version: report.graph_version, boundary_groups: checks.length, parity: parity.length, figure_links: report.intended_figure_links_checked, pass: true }));
} finally { graph.close(); desktop.close(); }
