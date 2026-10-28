import { copyFileSync, cpSync, existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const source = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const nodeIndex = args.indexOf('--node');
const node = nodeIndex < 0 ? process.execPath : resolve(args[nodeIndex + 1]);
const outputIndex = args.indexOf('--output');
const output = outputIndex < 0 ? resolve(source, '../delivery/agent') : resolve(args[outputIndex + 1]);
if (!existsSync(node)) throw new Error(`Node运行时不存在：${node}`);
if (!existsSync(resolve(source, 'licenses/NODE-LICENSE.txt'))) throw new Error('缺少随运行时分发的Node许可证');
mkdirSync(output, { recursive: true });
for (const item of ['bin', 'src', 'scripts', 'test', 'contracts', 'licenses', 'package.json', 'chan-kg.cmd', 'README.md', 'AGENT_GUIDE.md']) {
  cpSync(resolve(source, item), resolve(output, item), { recursive: true });
}
mkdirSync(resolve(output, 'runtime'), { recursive: true });
copyFileSync(node, resolve(output, 'runtime/node.exe'));
const runtime = spawnSync(node, ['--version'], { encoding: 'utf8' });
if (runtime.status !== 0 || Number(runtime.stdout.trim().slice(1).split('.')[0]) < 24) throw new Error('Agent需要Node24及以上运行时');
const sha = path => createHash('sha256').update(readFileSync(path)).digest('hex');
const git = spawnSync('git', ['rev-parse', 'HEAD'], { cwd: source, encoding: 'utf8' });
const manifest = {
  product: 'chan-kg-agent', version: JSON.parse(readFileSync(resolve(source, 'package.json'))).version,
  code_commit: git.status === 0 ? git.stdout.trim() : null,
  core_sha256: sha(resolve(output, 'src/core.mjs')),
  runtime: { version: runtime.stdout.trim(), sha256: sha(resolve(output, 'runtime/node.exe')), license: 'licenses/NODE-LICENSE.txt' },
  shared_graph_default: '../shared-knowledge/v0.1.0', independent_of_desktop: true,
};
writeFileSync(resolve(output, 'product-manifest.json'), JSON.stringify(manifest, null, 2));
console.log(JSON.stringify({ output, ...manifest }, null, 2));
