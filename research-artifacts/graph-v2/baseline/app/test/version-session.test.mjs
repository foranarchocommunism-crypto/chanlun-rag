import { test } from 'node:test';
import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';
import { mkdtempSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { resolve, sep } from 'node:path';
import { KnowledgeGraph } from '../src/core.mjs';

test('长期开启的会话读取当前版本，拒绝半发布数据并释放读事务', () => {
  const temporary = mkdtempSync(resolve(tmpdir(), 'chan-kg-query-'));
  const database = new DatabaseSync(resolve(temporary, 'graph.sqlite'));
  let graph;
  const manifest = version => writeFileSync(resolve(temporary, 'manifest.json'), JSON.stringify({ schema_version: '1.1.0', graph_version: version }));
  try {
    database.exec(readFileSync('contracts/schema.sql', 'utf8'));
    database.prepare('INSERT INTO metadata VALUES(?,?)').run('schema_version', JSON.stringify('1.1.0'));
    database.prepare('INSERT INTO metadata VALUES(?,?)').run('graph_version', JSON.stringify('before'));
    manifest('before');
    graph = new KnowledgeGraph(temporary);
    assert.equal(graph.query('sources').graph_version, 'before');
    database.prepare("UPDATE metadata SET value=? WHERE key='graph_version'").run(JSON.stringify('after'));
    manifest('after');
    assert.equal(graph.query('sources').graph_version, 'after');
    database.prepare("UPDATE metadata SET value=? WHERE key='graph_version'").run(JSON.stringify('publishing'));
    assert.throws(() => graph.query('sources'), /正在发布/);
    manifest('publishing');
    assert.equal(graph.query('sources').graph_version, 'publishing');
  } finally {
    graph?.close();
    database.close();
    const expectedRoot = resolve(tmpdir()) + sep + 'chan-kg-query-';
    assert.ok(resolve(temporary).startsWith(expectedRoot));
    rmSync(temporary, { recursive: true });
  }
});
