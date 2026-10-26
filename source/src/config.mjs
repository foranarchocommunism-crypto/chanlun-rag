import { existsSync, readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
export const appRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
export function locations(options = {}) {
  const portable = existsSync(resolve(appRoot, '../knowledge/manifest.json'));
  const root = portable ? resolve(appRoot, '..') : appRoot;
  const activeFile = resolve(root, 'indexes/active.json');
  const active = existsSync(activeFile) ? JSON.parse(readFileSync(activeFile, 'utf8')).directory : 'lexical-1-307029129712';
  return {
    root,
    kbPath: resolve(options.kbPath ?? process.env.CHAN_KG_PATH ?? (portable ? resolve(root, 'knowledge') : resolve(appRoot, '../shared-knowledge/v0.1.0'))),
    indexPath: resolve(options.indexPath ?? process.env.CHAN_KG_INDEX ?? resolve(root, 'indexes', active)),
    modelPath: resolve(options.modelPath ?? resolve(root, 'models')),
    policyPath: resolve(options.policyPath ?? resolve(root, 'policies/ambiguity-issues.json')),
    profilePath: resolve(options.profilePath ?? resolve(root, 'profiles/default.json')),
  };
}
