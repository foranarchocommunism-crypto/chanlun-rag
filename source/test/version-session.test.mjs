import { test } from 'node:test';
import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';
import { mkdtempSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { resolve, sep } from 'node:path';
import { KnowledgeGraph } from '../src/core.mjs';

test('固定快照会话阻止并发提交，关闭后重新打开匹配版本；拒绝半发布清单', () => {
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
    database.exec('BEGIN IMMEDIATE');
    database.prepare("UPDATE metadata SET value=? WHERE key='graph_version'").run(JSON.stringify('after'));
    assert.throws(() => database.exec('COMMIT'), /locked/);
    database.exec('ROLLBACK');
    assert.equal(graph.query('sources').graph_version, 'before');
    graph.close(); graph = null;
    database.prepare("UPDATE metadata SET value=? WHERE key='graph_version'").run(JSON.stringify('after'));
    manifest('after');
    graph = new KnowledgeGraph(temporary);
    assert.equal(graph.query('sources').graph_version, 'after');
    manifest('publishing');
    assert.throws(() => graph.query('sources'), /正在发布/);
    manifest('after');
    assert.equal(graph.query('sources').graph_version, 'after');
  } finally {
    graph?.close();
    database.close();
    const expectedRoot = resolve(tmpdir()) + sep + 'chan-kg-query-';
    assert.ok(resolve(temporary).startsWith(expectedRoot));
    rmSync(temporary, { recursive: true });
  }
});
