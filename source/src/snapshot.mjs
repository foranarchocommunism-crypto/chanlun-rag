import { DatabaseSync } from 'node:sqlite';
import { createHash } from 'node:crypto';
import { existsSync, readFileSync, statSync } from 'node:fs';

const fail = message => { throw Object.assign(new Error(message), { code: 'INDEX_STALE' }); };
export function assertStaticDatabase(path) {
  for (const suffix of ['-wal', '-shm', '-journal']) {
    if (existsSync(path + suffix)) fail(`Unsealed SQLite sidecar: ${path + suffix}; publish a closed DELETE-mode snapshot`);
  }
  // Header bytes 18/19 describe the on-disk read/write format, including dormant WAL mode.
  const bytes = readFileSync(path);
  if (bytes.length < 100 || bytes.toString('ascii', 0, 16) !== 'SQLite format 3\0' || bytes[18] !== 1 || bytes[19] !== 1) {
    fail(`Only sealed rollback-journal SQLite snapshots are accepted: ${path}`);
  }
  return createHash('sha256').update(bytes).digest('hex');
}
function stamp(path) { const s = statSync(path); return `${s.size}:${s.mtimeMs}:${s.ctimeMs}:${s.ino}`; }
export function openStaticDatabase(path, expectedHash) {
  const digest = assertStaticDatabase(path), initial = stamp(path);
  if (expectedHash && digest !== expectedHash) fail(`Snapshot checksum mismatch: ${path}`);
  const db = new DatabaseSync(path, { readOnly: true });
  try {
    // Hold a read transaction: in DELETE mode an external writer cannot commit during this session.
    db.exec('BEGIN'); db.prepare('SELECT count(*) AS n FROM sqlite_master').get();
    const version = db.prepare('PRAGMA data_version').get().data_version;
    const assertCurrent = () => {
      for (const suffix of ['-wal', '-shm', '-journal']) if (existsSync(path + suffix)) fail(`Snapshot is being written: ${path}`);
      if (stamp(path) !== initial || db.prepare('PRAGMA data_version').get().data_version !== version) fail(`Snapshot changed: ${path}`);
    };
    assertCurrent();
    return { db, sha256: digest, assertCurrent };
  } catch (error) { db.close(); throw error; }
}
