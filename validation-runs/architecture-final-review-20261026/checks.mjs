// Read-only production audit; all mutation/failure probes use isolated copied fixtures.
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync,writeFileSync,mkdirSync,cpSync,readdirSync,statSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {spawnSync} from 'node:child_process';
const out=dirname(fileURLToPath(import.meta.url)),root=resolve(out,'../..'),app=resolve(root,'chan-kg-agent'),run=resolve(out,'run-'+Date.now());mkdirSync(run);
const {RetrievalService}=await import(pathToFileURL(resolve(app,'src/retrieval.mjs'))),{sha256}=await import(pathToFileURL(resolve(app,'src/corpus.mjs')));
const old=resolve(root,'validation-runs/architecture-review-20261025/fixtures'),json=(p,v)=>writeFileSync(p,JSON.stringify(v,null,2)),read=p=>JSON.parse(readFileSync(p,'utf8').replace(/^\uFEFF/,''));
const r={created_at:new Date().toISOString(),client_audit_date:'2026-10-26',run,production_modified:false,observations:[],commands:[]},save=()=>{json(resolve(run,'results.json'),r);json(resolve(out,'latest.json'),{run,results:resolve(run,'results.json')});},record=(name,data)=>{r.observations.push({name,...data});save();console.log(JSON.stringify({name,...data}));};
const code=Object.fromEntries(readdirSync(resolve(app,'src')).filter(n=>n.endsWith('.mjs')).map(n=>[n,sha256(resolve(app,'src',n))]));
const production=[...Object.keys(code).map(n=>resolve(app,'src',n)),...read(resolve(app,'build/graph-v2/protected-inputs-before.json')).map(x=>x.path),resolve(app,'scripts/build-index.mjs'),resolve(app,'scripts/build-vectors.mjs')];
const before=Object.fromEntries(production.map(p=>[p,sha256(p)]));r.protected_before=before;
const receipt=read(resolve(app,'fresh-extraction-delivery-receipt.json'));
record('current_code_matches_verified_rc2',{matches:JSON.stringify(code)===JSON.stringify(receipt.code_sha256),version:read(resolve(app,'package.json')).version,
 package_matches:Object.entries(code).every(([n,h])=>sha256(resolve(receipt.extracted_path,'app/src',n))===h),canonical_matches:before[resolve(root,'shared-knowledge/v0.1.0/graph.sqlite')]===receipt.canonical_database_sha256});
const s=new RetrievalService();
try{
 for(const profile of ['hybrid-graph-rerank','hybrid-graph-v2-rerank']){
  const p=await s.retrieve({query:'如何烤披萨？',profile,limit:2});
  record('out_of_domain_routing',{profile,status:p.data.status,graph:p.runtime.stages.graph,channels:p.runtime.actual_channels,primary:p.runtime.primary_result_ids});
 }
 const source=await s.retrieve({query:'走势中枢',mode:'source',profile:'hybrid-graph-rerank',limit:1});
 record('source_channel_reporting',{graph:source.runtime.stages.graph,channels:source.runtime.actual_channels});
 for(const profile of ['hybrid-graph-rerank','hybrid-graph-v2-rerank']){
  const q={query:'中枢是什么，成立需要什么条件？',profile,limit:3},base=await s.retrieve({...q,graphDepth:0}),expand=s.graphStage.expand;
  s.graphStage.expand=()=>{throw new Error('FINAL_AUDIT_GRAPH_LOCAL_FAILURE');};
  let strict;try{await s.retrieve(q);strict={returned:true};}catch(e){strict={code:e.code};}
  const p=await s.retrieve({...q,allowDegraded:true});s.graphStage.expand=expand;
  record('graph_fallback',{profile,strict,degraded:p.runtime.degraded,primary_equal:JSON.stringify(p.runtime.primary_result_ids)===JSON.stringify(base.runtime.primary_result_ids),data_equal:JSON.stringify(p.data)===JSON.stringify(base.data),channels:p.runtime.actual_channels});
 }
 const started=performance.now(),queued=await Promise.all(Array.from({length:4},(_,i)=>s.retrieve({query:'中枢是什么？',profile:'hybrid-graph-v2-rerank',limit:1}).then(p=>({i,queue_wait_ms:p.runtime.queue_wait_ms,elapsed_ms:p.runtime.elapsed_ms,end_to_end_ms:p.runtime.end_to_end_ms,caller_ms:performance.now()-started}))));
 record('queue_time_now_observed',{requests:queued});
 const p=await s.retrieve({query:'中枢是什么？',profile:'hybrid-graph-v2-rerank',limit:3});json(resolve(run,'current-packet.json'),p);
 record('packet_replay_fields',{runtime_keys:Object.keys(p.runtime),top_level_keys:Object.keys(p),data_budget:p.data.budget,packet_path:resolve(run,'current-packet.json')});
}finally{await s.close();}
const kb=resolve(run,'kb'),index=resolve(run,'index-baseline'),policy=resolve(run,'policy.json');
cpSync(resolve(old,'kb-v0'),kb,{recursive:true});cpSync(resolve(old,'index-v0'),index,{recursive:true});cpSync(resolve(old,'v0.policy.json'),policy);
const options={kbPath:kb,indexPath:index,policyPath:policy},query={query:'audit-claim-00',profile:'hybrid',limit:1};
const writer=new DatabaseSync(resolve(kb,'graph.sqlite'));writer.exec('PRAGMA journal_mode=WAL;PRAGMA wal_autocheckpoint=0;');
const hash=sha256(resolve(kb,'graph.sqlite')),m=read(resolve(index,'manifest.json'));m.canonical_source_sha256=hash;m.indexed_snapshot_sha256=hash;json(resolve(index,'manifest.json'),m);
const vectorsBefore=sha256(resolve(index,'vectors.f32')),live=new RetrievalService(options);let fresh;
try{
 const original=await live.retrieve(query),changed='WAL_FINAL_REVIEW_20261026：这是隔离夹具的新原文，与原索引的文本不同。';
 writer.exec('BEGIN');writer.prepare('UPDATE claims SET text=? WHERE id=?').run(changed,'audit-claim-00');writer.prepare('UPDATE passages SET text=?,raw_text=? WHERE id=?').run(changed,changed,'audit-passage-00');writer.prepare('UPDATE evidence SET quote=?,quote_end=? WHERE claim_id=?').run(changed,[...changed].length,'audit-claim-00');writer.exec('COMMIT');
 const existing=await live.retrieve(query);fresh=new RetrievalService(options);const renewed=await fresh.retrieve(query);
 record('wal_consistency_gap',{main_hash_unchanged:sha256(resolve(kb,'graph.sqlite'))===hash,wal_bytes:statSync(resolve(kb,'graph.sqlite-wal')).size,
  old_vectors_unchanged:sha256(resolve(index,'vectors.f32'))===vectorsBefore,original_text:original.data.reviewed[0]?.text,existing_text:existing.data.reviewed[0]?.text,new_text:renewed.data.reviewed[0]?.text,
  existing_degraded:existing.runtime.degraded,new_degraded:renewed.runtime.degraded,new_channels:renewed.runtime.actual_channels,new_index_problem:fresh.indexProblem});
}finally{await live.close();await fresh?.close();writer.close();}
// Use a separate unchanged fixture for interrupted builds; no WAL-corrupted input is reused.
const buildKb=resolve(run,'build-kb');cpSync(resolve(old,'kb-v0'),buildKb,{recursive:true});
const command=(name,args)=>{const t=performance.now(),v=spawnSync(process.execPath,['--import',pathToFileURL(resolve(app,'scripts/deny-network.mjs')).href,...args],{cwd:app,encoding:'utf8',windowsHide:true,maxBuffer:4e6,timeout:120000});writeFileSync(resolve(run,name+'.log'),v.stdout+'\n'+v.stderr);const value={name,status:v.status,elapsed_ms:performance.now()-t,tail:v.stderr.slice(-1500)};r.commands.push(value);save();return value;};
const build=(name,target,preload)=>command(name,[...(preload?['--import',pathToFileURL(preload).href]:[]),'scripts/build-index.mjs','--kb',buildKb,'--policy',policy,'--output',target]);
const vectors=(name,target,preload)=>command(name,[...(preload?['--import',pathToFileURL(preload).href]:[]),'scripts/build-vectors.mjs','--index',target]);
const preloads={
 checkpoint:`import fs from 'node:fs';import {syncBuiltinESMExports} from 'node:module';const w=fs.writeFileSync;let n=0;fs.writeFileSync=function(p,...a){if(String(p).endsWith('vector-progress.json')&&++n===2)throw Error('AUDIT_FSYNC_BEFORE_CHECKPOINT');return w.call(this,p,...a);};syncBuiltinESMExports();`,
 projection:`import fs from 'node:fs';import {syncBuiltinESMExports} from 'node:module';const w=fs.writeFileSync;fs.writeFileSync=function(p,...a){if(String(p).endsWith('manifest.json'))throw Error('AUDIT_INDEX_MANIFEST');return w.call(this,p,...a);};syncBuiltinESMExports();`,
 manifest:`import fs from 'node:fs';import {syncBuiltinESMExports} from 'node:module';const w=fs.writeFileSync;fs.writeFileSync=function(p,...a){if(String(p).endsWith('manifest.json')){w.call(this,p,'{"interrupted":');throw Error('AUDIT_PARTIAL_MANIFEST');}return w.call(this,p,...a);};syncBuiltinESMExports();`
};
for(const [name,source]of Object.entries(preloads))writeFileSync(resolve(run,name+'.mjs'),source);
const torn=resolve(run,'torn-checkpoint');assert.equal(build('checkpoint-index',torn).status,0);
const a=vectors('checkpoint-fail',torn,resolve(run,'checkpoint.mjs')),b=vectors('checkpoint-retry',torn);
record('checkpoint_retry_gap',{first_exit:a.status,retry_exit:b.status,file_vectors:statSync(resolve(torn,'vectors.f32')).size/2048,checkpoint_vectors:read(resolve(torn,'vector-progress.json')).next,error:b.tail});
const proj=resolve(run,'incomplete-projection'),c=build('projection-fail',proj,resolve(run,'projection.mjs')),d=build('projection-retry',proj);
record('projection_retry_gap',{first_exit:c.status,retry_exit:d.status,error:d.tail});
const manifest=resolve(run,'torn-manifest');assert.equal(build('manifest-index',manifest).status,0);
const e=vectors('manifest-fail',manifest,resolve(run,'manifest.mjs')),f=vectors('manifest-retry',manifest);
record('manifest_retry_gap',{first_exit:e.status,retry_exit:f.status,manifest_contents:readFileSync(resolve(manifest,'manifest.json'),'utf8'),error:f.tail});
const after=Object.fromEntries(production.map(p=>[p,sha256(p)]));r.protected_after=after;r.production_unchanged=Object.entries(before).every(([p,h])=>after[p]===h);r.completed_at=new Date().toISOString();r.completed=true;save();
assert.equal(r.production_unchanged,true);console.log(JSON.stringify({completed:true,run,production_unchanged:true}));
