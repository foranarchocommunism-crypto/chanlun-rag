import assert from 'node:assert/strict';
import { after, test } from 'node:test';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { gunzipSync } from 'node:zlib';
import { resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { KnowledgeGraph } from '../src/core.mjs';

const root = resolve(process.env.CHAN_KG_PATH ?? '../shared-knowledge/v0.1.0');
const graph = new KnowledgeGraph(root);
after(() => graph.close());

test('固定底本覆盖907个实际PDF页面与108课，语义进度独立', () => {
  const c = graph.coverage().data;
  assert.equal(c.counts.pages, 907);
  assert.equal(c.counts.documents, 2);
  assert.equal(new Set(c.units.filter(x => x.kind === 'lesson').map(x => x.lesson_number)).size, 108);
  assert.equal(c.source_extraction_complete, true);
  assert.equal(typeof c.semantic_completion, 'boolean');
  assert.ok(c.units.some(x => x.processing_status !== 'semantic_extraction_complete'));
});
test('两字词可查，并且默认命题均已复核', () => {
  for (const word of ['中枢', '走势', '级别']) {
    const r = graph.search(word).data;
    assert.ok(r.results.length > 0, word);
    assert.ok(r.results.every(x => x.review_status === 'reviewed'));
    assert.ok(graph.search(word, { scope: 'source' }).data.total > 0);
  }
});
test('核心中枢定义保留数量、连续、次级别及完成条件', () => {
  const c = graph.getClaim('upper-l017-center-definition');
  assert.match(c.text, /至少三个连续次级别/);
  assert.ok(c.conditions.some(x => x.includes('完成')));
  assert.ok(c.evidence.some(x => x.pdf_page === 76));
  assert.ok(c.evidence.some(x => x.pdf_page === 82));
  assert.equal(c.importance_level, 1);
});
test('最低不可分解级别的定义入口独立保留', () => {
  const c = graph.getClaim('upper-l017-minimum-level-center');
  assert.match(c.text, /K线/);
  assert.match(c.conditions.join(' '), /(?:最低|不能分解|不可分解)/);
});
test('盘整及趋势保留完成状态与趋势方向条件', () => {
  const consolidation = graph.getClaim('upper-l017-consolidation-definition');
  const trend = graph.getClaim('upper-l017-trend-definition');
  assert.match(consolidation.conditions.join(' '), /完成/);
  assert.match(trend.conditions.join(' ') + trend.text, /同向/);
});
test('实际PDF75页提问、作者答复、下一课正确分开', () => {
  const p = graph.page({ documentId: 'volume_1.pdf', page: 75 }).data;
  assert.equal(p.page.printed_page, '69');
  assert.ok(p.passages.some(x => x.role === 'reader' && x.speaker === '清' && x.text.includes('不能不佩服')));
  assert.ok(p.passages.some(x => x.role === 'author_reply' && x.speaker === '缠中说禅' && x.text.startsWith('级别在某种程度')));
  assert.ok(p.passages.some(x => x.role === 'author_body' && x.text.startsWith('教你炒股票17')));
});
test('无冒号嵌入作者时间头后的答复正确识别', () => {
  const p = graph.page({ documentId: 'volume_2.pdf', page: 56 }).data;
  const reply = p.passages.find(x => x.id.endsWith('-b005'));
  assert.equal(reply.speaker, '缠中说禅');
  assert.equal(reply.role, 'author_reply');
});
test('每个复核引用精确对应归一文本及实际PDF字符', () => {
  const all = graph.db.prepare("SELECT id FROM claims WHERE review_status='reviewed'").all();
  assert.ok(all.length > 50);
  const cache = new Map();
  for (const { id } of all) {
    const c = graph.getClaim(id);
    assert.ok(c.evidence.length > 0, id);
    assert.ok([1, 2, 3, 4].includes(c.importance_level), id);
    assert.ok(c.importance_reason.length > 0, id);
    for (const e of c.evidence) {
      assert.equal(Array.from(e.passage_text).slice(e.quote_start, e.quote_end).join(''), e.quote, e.id);
      assert.equal(e.speaker, '缠中说禅');
      for (const span of e.source_spans) {
        const page = graph.db.prepare('SELECT geometry_path FROM pages WHERE document_id=? AND pdf_page=?').get(span.document_id, span.pdf_page);
        if (!cache.has(page.geometry_path)) cache.set(page.geometry_path, JSON.parse(gunzipSync(readFileSync(resolve(root, page.geometry_path))).toString('utf8')));
        const geometry = cache.get(page.geometry_path);
        const chars = span.char_indices.map(i => geometry.chars[i]?.[0]).join('');
        assert.equal(chars, e.quote, e.id);
        for (const [x0, top, x1, bottom] of span.boxes) {
          assert.ok(x0 >= 0 && x1 <= geometry.width + 1 && x0 <= x1);
          assert.ok(top >= 0 && bottom <= geometry.height + 1 && top <= bottom);
        }
      }
    }
  }
});
test('作者明说与推论有独立身份和可解析前提链', () => {
  const c = graph.getClaim('synthesis-center-prerequisites');
  assert.equal(c.kind, 'inferred');
  assert.ok(c.derivation.supporting_claim_ids.length > 0);
  for (const premise of c.derivation.supporting_claim_ids) assert.equal(graph.getClaim(premise).review_status, 'reviewed');
  assert.equal(graph.getClaim('upper-l017-center-definition').kind, 'explicit');
});
test('重叠例子的算术答案独立标为整理推论，不补出中枢成立条件', () => {
  const c = graph.getClaim('upper-l017-c-stage-example-overlap-arithmetic');
  assert.equal(c.kind, 'inferred');
  assert.match(c.text, /下界为12元、上界为18元/);
  assert.match(c.conditions.join(' '), /不据此确认三段的级别、完成状态/);
  assert.deepEqual(c.derivation.supporting_claim_ids, ['upper-l017-overlap-example', 'upper-l018-center-first-three']);
  assert.match(c.review_note, /未直接写出答案/);
  assert.equal(graph.getClaim('upper-l017-second-point-law').ambiguity_status, 'source_buy_sell_wording_pending');
});
test('前段尾部的新时间头只修订其后内容日期', () => {
  const page = graph.page({ documentId: 'volume_1.pdf', page: 86 }).data;
  const dates = Object.fromEntries(page.passages.map(p => [p.id.split('-p')[1], p.published_at]));
  assert.equal(dates['0086-b002'], '2006-12-27 15:25:27');
  assert.equal(dates['0086-b003'], '2006-12-27 15:29:37');
  for (const suffix of ['0086-b004', '0086-b005', '0086-b006']) assert.equal(dates[suffix], '2006-12-28 15:45:14');
});
test('解盘技术补充保留作者身份、递归入口和成交分笔的区别', () => {
  const c = graph.getClaim('lower-l065-recursion-a0-practical-theoretical');
  assert.equal(c.kind, 'explicit');
  assert.match(c.text, /a0/);
  assert.match(c.conditions.join(' '), /实际分笔成交不是/);
  const e = c.evidence.find(x => x.passage_id.endsWith('p0039-b009'));
  assert.equal(e.role, 'author_commentary');
  assert.equal(e.speaker, '缠中说禅');
  assert.equal(e.published_at, '2007-07-20 08:26:20');
  assert.match(c.review_note, /语境：/);
  assert.match(c.review_note, /适用条件：/);
});
test('简短组合回复保留问题范围，低级别卖点不冒充日线背驰定位', () => {
  const nine = graph.getClaim('lower-l066-nine-types-combine-before-center');
  assert.match(nine.text, /提问中/);
  assert.match(nine.text, /不一定/);
  assert.match(nine.text, /3\+3\+3/);
  assert.ok(nine.evidence.every(e => !/^缠中说禅20/.test(e.quote)));
  const sells = graph.getClaim('lower-l066-intraday-sell-point-not-daily-location-case');
  assert.match(sells.text, /不能称日线背驰段已经被定位/);
  assert.match(sells.conditions.join(' '), /60分钟尚未/);
  assert.ok(sells.evidence.some(e => e.pdf_page === 49));
  assert.ok(sells.evidence.some(e => e.pdf_page === 50));
});
test('中枢的九段延伸不被当成所有中枢必要条件，笔破坏与线段破坏分开', () => {
  const nine = graph.getClaim('lower-l069-c-stage-nine-segments-not-necessary');
  assert.match(nine.text, /不等于所有5分钟中枢必须由九段构成/);
  const destruction = graph.getClaim('lower-l071-c-stage-stroke-vs-segment-no-implication');
  assert.match(destruction.text, /笔破坏不必然线段破坏/);
  assert.match(destruction.text, /第二种未必/);
  assert.ok(destruction.evidence.some(e => e.passage_id.endsWith('p0102-b007')));
});
test('作者错误图警示及后加图来源与文字命题分别保留', () => {
  const notice = graph.getClaim('lower-l071-c-stage-diagram-correction-notice');
  assert.match(notice.text, /第81课更正/);
  const figures = graph.db.prepare("SELECT id,origin_status,note FROM figures WHERE id IN ('volume_2-5332cd1b6038-p0094-fig1','volume_2-5332cd1b6038-p0094-fig2','volume_2-5332cd1b6038-p0095-fig1')").all();
  assert.equal(figures.filter(f => f.origin_status === 'later_annotation').length, 2);
  assert.match(figures.find(f => f.id.endsWith('p0094-fig2')).note, /最后一个图有问题/);
  const macd = graph.getClaim('upper-l019-c-stage-macd-new-low-contrast-case');
  assert.ok(macd.evidence.every(e => !e.quote.includes('最小级别')));
  assert.match(macd.review_note, /引文严格止于括号注之前/);
});
test('71课错误图的更正保留81课限定及作者认可读者答案的证据链', () => {
  const correction = graph.getClaim('lower-l081-c-stage-lesson71-last-diagram-correction');
  assert.match(correction.text, /第71课最后一图/);
  assert.match(correction.text, /低于类似5/);
  assert.ok(correction.evidence.some(e => e.passage_id.endsWith('p0173-b012')));
  const answer = graph.getClaim('lower-l081-c-stage-two-diagrams-conditional-answer');
  for (const suffix of ['p0173-b009', 'p0173-b010', 'p0173-b011']) {
    assert.ok(answer.evidence.some(e => e.passage_id.endsWith(suffix)));
  }
  assert.match(answer.review_note, /引述读者答案/);
  assert.match(answer.conditions.join(' '), /第81课开头图一、图二/);
});

test('新笔两个联合条件及新旧标准选择分别可查', () => {
  const criteria = graph.getClaim('lower-l081-c-stage-new-stroke-two-joint-conditions');
  assert.match(criteria.text, /联合满足/);
  assert.match(criteria.text, /不共用K线/);
  assert.match(criteria.text, /不考虑包含关系，至少有3根K线/);
  const choice = graph.getClaim('lower-l081-c-stage-new-standard-optional-old-kept');
  assert.match(choice.text, /可以用新笔标准/);
  assert.match(choice.text, /仍用老标准/);
  assert.ok(choice.evidence.some(e => e.passage_id.endsWith('p0179-b001')));
});

test('中枢简式的回升或回调是替代条件，来源时间头不污染跨页评论', () => {
  const formula = graph.getClaim('upper-l020-center-formula-reduced');
  assert.equal(formula.conditions.length, 2);
  assert.match(formula.conditions[1], /择一适用/);
  assert.match(formula.conditions[1], /或回调形成时/);
  assert.equal(formula.evidence[0].id, 'evidence-7d2db211b0452a2d');
  for (const [suffix, date] of [['p0107-b006', '2007-01-10 16:22:39'], ['p0115-b001', '2007-01-12 15:26:45'], ['p0121-b000', '2007-01-17 15:18:53'], ['p0137-b002', '2007-01-22 15:27:14']]) {
    const p = graph.db.prepare('SELECT published_at,role,speaker FROM passages WHERE id=?').get(`volume_1-a53e99c37ca5-${suffix}`);
    assert.equal(p.published_at, date);
    assert.equal(p.role, 'author_commentary');
    assert.equal(p.speaker, '缠中说禅');
  }
});

test('候选必须显式开启，重要性与复核状态独立', () => {
  const candidate = graph.db.prepare("SELECT id FROM claims WHERE review_status='pending' LIMIT 1").get();
  assert.equal(graph.getClaim(candidate.id), null);
  assert.equal(graph.getClaim(candidate.id, { includeUnreviewed: true }).review_status, 'pending');
  assert.ok(graph.search('', { maxImportance: 1, limit: 100 }).data.results.every(c => c.importance_level === 1));
  assert.throws(() => graph.search('', { reviewStatus: 'pending' }), /includeUnreviewed/);
});
test('字符串false和隐式数值转换不能开启候选或改变查询规模', () => {
  for (const includeUnreviewed of ['false', 'true', 0, 1, [], null]) {
    assert.throws(() => graph.search('', { includeUnreviewed }), /boolean/);
    assert.throws(() => graph.concepts({ includeUnreviewed }), /boolean/);
  }
  for (const value of [true, false, [1], null, '', '1e1', '0x10', 1.5]) {
    assert.throws(() => graph.search('中枢', { limit: value }), /整数/);
    assert.throws(() => graph.search('中枢', { maxImportance: value }), /整数/);
    assert.throws(() => graph.neighbors('走势中枢', { depth: value }), /整数/);
  }
  assert.equal(graph.search('中枢', { limit: '2' }).data.limit, 2);
});
test('汇编后记和006年读者头不会留作作者候选，后加图有独立来源状态', () => {
  const appendices = graph.db.prepare("SELECT * FROM units WHERE kind='compiler_appendix'").all();
  assert.equal(appendices.length, 2);
  for (const unit of appendices) {
    assert.equal(unit.lesson_number, null);
    assert.equal(unit.processing_status, 'excluded_from_author_knowledge');
    assert.equal(graph.db.prepare("SELECT count(*) AS n FROM passages WHERE unit_id=? AND (role!='unknown' OR speaker IS NOT NULL)").get(unit.id).n, 0);
    assert.equal(graph.db.prepare("SELECT count(*) AS n FROM claims c JOIN evidence e ON e.claim_id=c.id JOIN passages p ON p.id=e.passage_id WHERE p.unit_id=? AND c.review_status!='rejected'").get(unit.id).n, 0);
  }
  const reader = graph.db.prepare('SELECT role,speaker,published_at FROM passages WHERE id=?').get('volume_1-a53e99c37ca5-p0074-b008');
  assert.equal(reader.role, 'reader');
  assert.equal(reader.published_at, null);
  const figure = graph.db.prepare('SELECT origin_status,note FROM figures WHERE id=?').get('volume_2-5332cd1b6038-p0054-fig1');
  assert.equal(figure.origin_status, 'later_annotation');
  assert.match(figure.note, /2008-08-15/);
});
test('关系均由已复核命题支持，等级筛选沿同一依据', () => {
  const r = graph.neighbors('走势中枢', { maxImportance: 1 }).data;
  assert.ok(r.edges.length > 0);
  for (const edge of r.edges) {
    assert.equal(edge.importance_level, 1);
    assert.ok(edge.claim_ids.length > 0);
    for (const id of edge.claim_ids) assert.equal(graph.getClaim(id).review_status, 'reviewed');
  }
});
test('分页与邻域截断明确，不返回无限图', () => {
  const r = graph.search('中枢', { limit: 1 }).data;
  assert.equal(r.results.length, 1);
  assert.equal(r.truncated, true);
  assert.equal(r.next_offset, 1);
  const n = graph.neighbors('走势中枢', { limit: 1 }).data;
  assert.equal(n.nodes.length, 1);
  assert.equal(n.truncated, true);
});
test('Agent CLI独立运行并与公共查询模块结果一致', () => {
  const r = spawnSync(process.execPath, ['bin/chan-kg.mjs', 'search', '中枢', '--limit', '2', '--kb', root], { encoding: 'utf8', cwd: resolve('.') });
  assert.equal(r.status, 0, r.stderr);
  assert.deepEqual(JSON.parse(r.stdout), graph.search('中枢', { limit: 2 }));
});
test('固定底本哈希、数据库约束及只读行为可核验', () => {
  assert.deepEqual(graph.db.prepare('PRAGMA foreign_key_check').all(), []);
  for (const d of graph.sources().data.documents) {
    assert.equal(createHash('sha256').update(readFileSync(graph.resourcePath(d.resource_path))).digest('hex'), d.sha256);
  }
  assert.throws(() => graph.db.exec("INSERT INTO metadata VALUES('test','true')"), /readonly|read-only/i);
  assert.throws(() => graph.resourcePath('../outside.pdf'), /超出/);
  assert.throws(() => graph.page({ documentId: 'volume_1.pdf', page: 0 }), /页码/);
});
