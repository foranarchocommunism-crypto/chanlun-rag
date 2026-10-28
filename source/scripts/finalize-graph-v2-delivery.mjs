import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,readdirSync,copyFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {spawnSync} from 'node:child_process';
import {sha256} from '../src/corpus.mjs';
const read=p=>JSON.parse(readFileSync(p,'utf8').replace(/^\uFEFF/,'')),dir='build/graph-v2/acceptance/',z=read(dir+'zip-extraction.json'),fresh=read(dir+'fresh-portable-verification.json'),local=read(dir+'local-portable-verification.json');
assert.equal(fresh.passed,true);assert.equal(local.passed,true);assert.equal(resolve(fresh.product_root),resolve(z.extracted_path));
assert.equal(sha256(z.archive),z.archive_sha256);assert.equal(z.fresh_extraction,true);
const code=Object.fromEntries(readdirSync('src').filter(n=>n.endsWith('.mjs')).map(n=>[n,sha256(resolve('src',n))]));
for(const [name,digest]of Object.entries(code))assert.equal(sha256(resolve(z.extracted_path,'app/src',name)),digest);
for(const folder of ['bin','contracts'])for(const name of readdirSync(folder))if(/\.(mjs|json|sql)$/.test(name))assert.equal(sha256(resolve(z.extracted_path,'app',folder,name)),sha256(resolve(folder,name)));
const manifest=read(resolve(z.extracted_path,'release-manifest.json'));
assert.equal(manifest.product_version,read('package.json').version);assert.equal(manifest.graph_v2.default_enabled,false);
assert.equal(manifest.graph_v2.hop_selection_policy,'shared_pool_no_reservations_no_floors');
const receipt={created_at:new Date().toISOString(),passed:true,scope:'Windows x64 candidate engineering delivery; not independent semantic acceptance',...z,
 product_version:manifest.product_version,default_strategy_changed:false,experimental_strategy_enabled_by_default:false,
 fresh_verification_path:resolve(dir+'fresh-portable-verification.json'),fresh_verification_sha256:sha256(dir+'fresh-portable-verification.json'),
 local_verification_path:resolve(dir+'local-portable-verification.json'),local_verification_sha256:sha256(dir+'local-portable-verification.json'),
 actual_executable:fresh.environment.executable,network_policy:fresh.network_policy,
 checks:fresh.checks,code_sha256:code,release_manifest_sha256:sha256(resolve(z.extracted_path,'release-manifest.json')),
 checksums_sha256:sha256(resolve(z.extracted_path,'checksums.sha256')),canonical_database_sha256:manifest.canonical_database_sha256,
 limits:['Semantic gain not certified; student assignment cancelled','Deep Windows paths may exceed the platform path limit; use a short extraction directory','Current host tested; no independent clean-host or ARM64 claim'],
 superseded_candidate:'0.4.0-rc.1; retained as an experiment record, not the current candidate'};
writeFileSync('fresh-extraction-delivery-receipt.json',JSON.stringify(receipt,null,2));
writeFileSync(z.archive+'.delivery-receipt.json',JSON.stringify(receipt,null,2));
const r=spawnSync(process.execPath,['scripts/record-graph-v2-engineering.mjs'],{encoding:'utf8',windowsHide:true});assert.equal(r.status,0,r.stderr);console.log(r.stdout.trim());
const g=spawnSync(process.execPath,['scripts/verify-graph-v2-gates.mjs'],{encoding:'utf8',windowsHide:true});
assert.equal(g.status,1,'Independent semantic activation is intentionally not accepted');
const gates=read(dir+'gate-results.json');assert.equal(gates.gates.find(g=>g.id==='delivery').passed,true);assert.equal(gates.gates.find(g=>g.id==='resources').passed,true);
copyFileSync(dir+'gate-results.json',z.archive+'.gate-results.json');
console.log(JSON.stringify({passed:true,archive:z.archive,sha256:z.archive_sha256,default_activation_accepted:gates.new_default_accepted,engineering_gates:gates.gates.filter(g=>g.passed).map(g=>g.id)}));
