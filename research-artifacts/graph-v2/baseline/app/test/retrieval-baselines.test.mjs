import assert from 'node:assert/strict';
import test from 'node:test';
import { LexicalIndex, tokenize, rankedMetrics, uniquePassages, reciprocalRankFusion } from '../scripts/lib/retrieval-baselines.mjs';

test('Chinese two-character concepts and ASCII parameters survive normalization', () => {
  assert.deepEqual(tokenize('中枢，MACD１２.５'), ['中枢', 'macd', '12.5']);
  assert.deepEqual(tokenize('A A A'), ['a']);
});
test('rare terms can beat generic terms; ties remain deterministic; unknown query is empty', () => {
  const index = new LexicalIndex([{ id: 'c', text: '中枢 背驰' }, { id: 'a', text: '中枢' }, { id: 'b', text: '中枢' }]);
  assert.equal(index.search('背驰 中枢', 3)[0].id, 'c');
  assert.deepEqual(index.search('完全未知', 10), []);
  assert.deepEqual(index.search('中枢', 3).slice(0, 2).map(x => x.id), ['a', 'b']);
});
test('a repeated quote or duplicated evidence row cannot inflate the unique passage budget', () => {
  const result = uniquePassages([{ id: 'c1', score: 3 }, { id: 'c2', score: 2 }], new Map([['c1', ['p1', 'p1']], ['c2', ['p1', 'p2']]]), 2);
  assert.deepEqual(result.map(x => x.id), ['p1', 'p2']);
});
test('fusion rewards independent channel agreement and ignores duplicate items within one channel', () => {
  const result = reciprocalRankFusion([[{ id: 'a' }, { id: 'a' }, { id: 'b' }], [{ id: 'b' }, { id: 'c' }]], 3);
  assert.equal(result[0].id, 'b');
  assert.ok(Math.abs(result[0].score - (1 / 62 + 1 / 61)) < 1e-12);
});
test('ranking metrics agree with hand calculated rank two and three relevance', () => {
  const m = rankedMetrics(['wrong', 'p1', 'p2'], ['p1', 'p2', 'not-retrieved'], 3);
  assert.equal(m.recall, 2 / 3); assert.equal(m.annotated_precision_lower_bound, 2 / 3);
  assert.equal(m.reciprocal_rank, 1 / 2);
  const expected = (1 / Math.log2(3) + 1 / Math.log2(4)) / (1 + 1 / Math.log2(3) + 1 / Math.log2(4));
  assert.ok(Math.abs(m.ndcg_binary - expected) < 1e-12);
  assert.equal(m.all_annotated_evidence_found, 0);
});
test('duplicate ranks do not inflate metrics; no gold has no fabricated perfect score', () => {
  const m = rankedMetrics(['p1', 'p1'], ['p1'], 5);
  assert.equal(m.recall, 1); assert.equal(m.annotated_precision_lower_bound, 1 / 5); assert.equal(m.returned, 1);
  assert.equal(rankedMetrics(['p1'], [], 5), null);
});
