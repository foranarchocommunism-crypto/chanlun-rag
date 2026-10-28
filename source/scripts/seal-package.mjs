// Final pre-ZIP seal after assembling licenses/docs; never modifies canonical inputs.
import assert from 'node:assert/strict';
import { copyFileSync, existsSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs';
import { relative, resolve, sep } from 'node:path';
import { sha256 } from '../src/corpus.mjs';
assert.ok(process.argv[2], 'Provide the explicit pre-ZIP directory');
const output = resolve(process.argv[2]);
assert.ok(output.startsWith(resolve('../deliveries') + sep));
assert.ok(!existsSync(`${output}.zip`), 'Do not reseal a published ZIP; build a new release');
const manifestPath = resolve(output, 'release-manifest.json');
const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
for (const file of ['MSVC-RUNTIME-LICENSE.txt', 'MSVC-license-source.json']) {
  assert.ok(existsSync(resolve('licenses', file))); copyFileSync(resolve('licenses', file), resolve(output, 'licenses', file));
}
const native = JSON.parse(readFileSync('build/native-runtime/native-runtime-manifest.json', 'utf8'));
for (const asset of native.assets) for (const directory of [manifest.runtimes ? 'runtime/x64' : 'runtime', 'app/node_modules/onnxruntime-node/bin/napi-v6/win32/x64', 'app/node_modules/@img/sharp-win32-x64/lib']) {
  if (existsSync(resolve(output, directory))) copyFileSync(resolve('build/native-runtime', asset.file), resolve(output, directory, asset.file));
}
copyFileSync(resolve('scripts/verify-portable.mjs'), resolve(output, 'app/scripts/verify-portable.mjs'));
copyFileSync(resolve('scripts/doctor.ps1'), resolve(output, 'app/scripts/doctor.ps1'));
copyFileSync(resolve('docs/portable-readme.md'), resolve(output, 'README.md'));
copyFileSync(resolve('docs/COMPATIBILITY.md'), resolve(output, 'docs/COMPATIBILITY.md'));
if (manifest.runtime) manifest.runtime.native_license = 'licenses/MSVC-RUNTIME-LICENSE.txt';
manifest.status = 'portable_release_environment_results_in_external_receipt';
writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n');
const files = [];
function visit(directory) { for (const entry of readdirSync(directory, { withFileTypes: true })) { const path = resolve(directory, entry.name); if (entry.isDirectory()) visit(path); else if (path !== resolve(output, 'checksums.sha256')) files.push(path); } }
visit(output); files.sort();
writeFileSync(resolve(output, 'checksums.sha256'), files.map(path => `${sha256(path)}  ${relative(output, path).split(sep).join('/')}`).join('\n') + '\n');
const receipt = { sealed_at: new Date().toISOString(), output, files: files.length + 1, bytes: files.reduce((sum, path) => sum + statSync(path).size, 0),
  manifest_sha256: sha256(manifestPath), checksums_sha256: sha256(resolve(output, 'checksums.sha256')), candidate: false };
writeFileSync(`${output}.build-receipt.json`, JSON.stringify(receipt, null, 2) + '\n'); console.log(JSON.stringify(receipt));
