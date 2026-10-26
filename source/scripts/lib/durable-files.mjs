import { createHash, randomUUID } from 'node:crypto';
import { openSync, closeSync, writeFileSync, readFileSync, fsyncSync, renameSync, unlinkSync, existsSync } from 'node:fs';
import { dirname } from 'node:path';

// Same-directory temporary + fsync + rename: reviewed against lowdb and npm/write-file-atomic.
// Guarantees old-or-new visibility on tested Windows; does not claim hardware power-loss durability.
export function atomicWrite(path, value) {
  const temp = `${path}.${process.pid}.${randomUUID()}.tmp`;
  let fd;
  try {
    fd = openSync(temp, 'wx'); writeFileSync(fd, value); fsyncSync(fd); closeSync(fd); fd = undefined;
    for (let attempt = 0;; attempt++) {
      try { renameSync(temp, path); break; }
      catch (error) {
        if (process.platform !== 'win32' || !['EPERM', 'EACCES', 'EBUSY'].includes(error.code) || attempt >= 7) throw error;
        // Windows scanners may briefly hold the destination. Keep the old file intact while retrying.
        Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 5 * 2 ** attempt);
      }
    }
    if (process.platform !== 'win32') { const d = openSync(dirname(path), 'r'); try { fsyncSync(d); } finally { closeSync(d); } }
  } finally { if (fd !== undefined) closeSync(fd); if (existsSync(temp)) unlinkSync(temp); }
}
export const atomicJson = (path, value) => atomicWrite(path, JSON.stringify(value, null, 2) + '\n');
export function acquireBuildLock(path) {
  if (existsSync(path)) {
    let lock;
    try { lock = JSON.parse(readFileSync(path, 'utf8')); } catch { throw new Error(`Unverifiable build lock; inspect before retrying: ${path}`); }
    let live = true;
    try { process.kill(lock.pid, 0); } catch (e) { if (e.code === 'ESRCH') live = false; else throw e; }
    if (live) throw new Error(`Builder still running: ${lock.pid}`);
    unlinkSync(path);
  }
  const token = randomUUID(), fd = openSync(path, 'wx');
  try { writeFileSync(fd, JSON.stringify({ pid: process.pid, token })); fsyncSync(fd); } finally { closeSync(fd); }
  return () => { if (existsSync(path) && JSON.parse(readFileSync(path, 'utf8')).token === token) unlinkSync(path); };
}
export const prefixHash = (path, bytes) => createHash('sha256').update(readFileSync(path).subarray(0, bytes)).digest('hex');
