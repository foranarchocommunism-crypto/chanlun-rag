import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';
import { readFileSync, writeFileSync, mkdirSync, cpSync, existsSync, statSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { spawn } from 'node:child_process';
const out=dirname(fileURLToPath(import.meta.url)),root=resolve(out,'../..'),app=resolve(root,'chan-kg-agent'),fixtures=resolve(out,'fixtures');
mkdirSync(fixtures,{recursive:true});
const { RetrievalService }=await import(pathToFileURL(resolve(app,'src/retrieval.mjs')));
const { sha256 }=await import(pathToFileURL(resolve(app,'src/corpus.mjs')));
const result={created_at:new Date().toISOString(),scope:'Synthetic isolated SQLite fixtures, actual unmodified build-index/build-vectors and local ONNX embeddings. Canonical and released files remain unchanged.',scenarios:[],commands:[]};
const json=(p,v)=>writeFileSync(p,JSON.stringify(v,null,2)+'\n');
const save=()=>json(resolve(out,'lifecycle-audit.json'),result);
const record=(name,data)=>{result.scenarios.push({name,...data});save();console.log(JSON.stringify({name,...data}));};
async function run(name,args){
 const started=performance.now();let stdout='',stderr='';
 const child=spawn(process.execPath,args,{cwd:app,windowsHide:true,stdio:['ignore','pipe','pipe']});
 child.stdout.on('data',d=>stdout+=d);child.stderr.on('data',d=>stderr+=d);
 const outcome=await new Promise((res,rej)=>{child.on('error',rej);child.on('close',(code,signal)=>res({code,signal}));});
 writeFileSync(resolve(out,`${name}.stdout.log`),stdout);writeFileSync(resolve(out,`${name}.stderr.log`),stderr);
 const entry={name,...outcome,elapsed_ms:performance.now()-started,args,stderr_tail:stderr.slice(-2200)};result.commands.push(entry);save();return entry;
}
const buildIndex=(name,kb,policy,index,preload)=>run(name,[...(preload?['--import',pathToFileURL(preload).href]:[]),'scripts/build-index.mjs','--kb',kb,'--policy',policy,'--output',index]);
const buildVectors=(name,index,preload)=>run(name,[...(preload?['--import',pathToFileURL(preload).href]:[]),'scripts/build-vectors.mjs','--index',index]);
const config=(kb,index,policy)=>({kbPath:kb,indexPath:index,policyPath:policy});
const policy=(name,version)=>{const p=resolve(fixtures,`${name}.policy.json`);json(p,{policy_version:'audit-1',graph_version:version,issues:[]});return p;};
function createKb(path,version){
 mkdirSync(path);const db=new DatabaseSync(resolve(path,'graph.sqlite'));db.exec(readFileSync(resolve(app,'contracts/schema.sql'),'utf8'));
 const ins=(table,columns,values)=>db.prepare(`INSERT INTO ${table}(${columns.join(',')}) VALUES(${values.map(()=>'?').join(',')})`).run(...values);
 ins('metadata',['key','value'],['schema_version',JSON.stringify('1.1.0')]);ins('metadata',['key','value'],['graph_version',JSON.stringify(version)]);
 ins('documents',['id','filename','sha256','page_count','resource_path'],['audit-doc','SYNTHETIC-AUDIT-NOT-SOURCE.pdf','0'.repeat(64),1,'SYNTHETIC-AUDIT-NOT-SOURCE.pdf']);
 ins('units',['id','title','kind','document_id','start_page','end_page'],['audit-unit','Synthetic audit fixture','audit','audit-doc',1,1]);
 ins('pages',['id','document_id','pdf_page','width','height','raw_text','geometry_path'],['audit-page','audit-doc',1,600,800,'synthetic','synthetic.json']);
 for(let i=0;i<3;i++)ins('concepts',['id','label'],[`audit-concept-${i}`,['夹具旧词','夹具类别','夹具路径'][i]]);
 for(let i=0;i<36;i++){
  const suffix=String(i).padStart(2,'0'),cid=`audit-claim-${suffix}`,pid=`audit-passage-${suffix}`;
  const text=`夹具旧词的独立检索样例编号${suffix}，用于测试本地索引更新删除和构建恢复，条件是测试序号等于${i}。`;
  ins('passages',['id','unit_id','document_id','pdf_page','block_index','role','speaker','text','raw_text','boxes','normalized_map','source_char_indices'],[pid,'audit-unit','audit-doc',1,i,'author_body','synthetic audit author',text,text,'[[0,0,100,20]]','[]','[]']);
  ins('claims',['id','text','kind','conditions','concept_ids','review_status','importance_level','importance_reason'],[cid,text,'explicit',JSON.stringify([`测试序号为${i}`]),JSON.stringify(['audit-concept-0','audit-concept-1']),'reviewed',2,'synthetic fixture']);
  ins('evidence',['id','claim_id','passage_id','quote','quote_start','quote_end','source_spans'],[`audit-evidence-${suffix}`,cid,pid,text,0,[...text].length,'[]']);
  ins('reviews',['id','claim_id','reviewer','checked_at','checks','result','note'],[`audit-review-${suffix}`,cid,'synthetic-fixture','2026-10-25','{}','reviewed','Not domain knowledge']);
 }
 ins('relations',['id','source','target','type','claim_ids','review_status'],['audit-relation-0','audit-concept-0','audit-concept-1','related',JSON.stringify(['audit-claim-00']),'reviewed']);
 ins('relations',['id','source','target','type','claim_ids','review_status'],['audit-relation-1','audit-concept-1','audit-concept-2','related',JSON.stringify(['audit-claim-01']),'reviewed']);
 db.close();json(resolve(path,'manifest.json'),{schema_version:'1.1.0',graph_version:version});
}
function changeVersion(kb,version,mutator){const db=new DatabaseSync(resolve(kb,'graph.sqlite'));db.exec('PRAGMA foreign_keys=ON;BEGIN');mutator(db);db.prepare("UPDATE metadata SET value=? WHERE key='graph_version'").run(JSON.stringify(version));db.exec('COMMIT');db.close();json(resolve(kb,'manifest.json'),{schema_version:'1.1.0',graph_version:version});}
async function queryOnce(options,request){let s;try{s=new RetrievalService(options);const p=await s.retrieve(request);return{status:'returned',index_problem:s.indexProblem,channels:p.runtime.actual_channels,degraded:p.runtime.degraded,text:p.data.reviewed[0]?.text,ids:p.data.reviewed.map(c=>c.id)};}catch(e){return{status:'threw',code:e.code,message:e.message};}finally{await s?.close();}}
function claimVector(index,id){const manifest=JSON.parse(readFileSync(resolve(index,'manifest.json'),'utf8')),rows=JSON.parse(readFileSync(resolve(index,'vector-rows.json'),'utf8'));const r=rows.find(r=>r.kind==='claim'&&r.claim_id===id);if(!r)return null;const b=readFileSync(resolve(index,'vectors.f32'));return{row:r,bytes:b.subarray(r.vector_row*512*4,(r.vector_row+1)*512*4).toString('base64'),matrix_sha256:manifest.models.embedding.vectors_sha256};}
const query={query:'audit-claim-00',profile:'hybrid',limit:1};
const kb0=resolve(fixtures,'kb-v0'),idx0=resolve(fixtures,'index-v0'),p0=policy('v0','audit-v0');createKb(kb0,'audit-v0');
assert.equal((await buildIndex('base-index',kb0,p0,idx0)).code,0);assert.equal((await buildVectors('base-vectors',idx0)).code,0);
const baseline=await queryOnce(config(kb0,idx0,p0),query);record('baseline_real_vector_retrieval',baseline);assert.equal(baseline.degraded,false);
const originalVector=claimVector(idx0,'audit-claim-00');

const kb1=resolve(fixtures,'kb-v1'),idx1=resolve(fixtures,'index-v1'),p1=policy('v1','audit-v1');cpSync(kb0,kb1,{recursive:true});
const newText='夹具新词表示被正式更新后的独立检索文本，原先的旧词内容已撤回；本句仅为故障注入夹具。';
changeVersion(kb1,'audit-v1',db=>{db.prepare('UPDATE claims SET text=? WHERE id=?').run(newText,'audit-claim-00');db.prepare('UPDATE passages SET text=?,raw_text=? WHERE id=?').run(newText,newText,'audit-passage-00');db.prepare('UPDATE evidence SET quote=?,quote_end=? WHERE claim_id=?').run(newText,[...newText].length,'audit-claim-00');});
record('update_old_index_rejected',{normal:await queryOnce(config(kb1,idx0,p1),query),opt_in_fallback:await queryOnce(config(kb1,idx0,p1),{...query,allowDegraded:true})});
assert.equal((await buildIndex('update-index',kb1,p1,idx1)).code,0);assert.equal((await buildVectors('update-vectors',idx1)).code,0);
const newVector=claimVector(idx1,'audit-claim-00');record('update_rebuild_and_old_snapshot',{updated:await queryOnce(config(kb1,idx1,p1),query),claim_vector_changed:originalVector.bytes!==newVector.bytes,old_snapshot_still_usable:await queryOnce(config(kb0,idx0,p0),query)});

const kb2=resolve(fixtures,'kb-v2'),idx2=resolve(fixtures,'index-v2'),p2=policy('v2','audit-v2');cpSync(kb1,kb2,{recursive:true});
changeVersion(kb2,'audit-v2',db=>{db.prepare('DELETE FROM evidence WHERE claim_id=?').run('audit-claim-01');db.prepare('DELETE FROM reviews WHERE claim_id=?').run('audit-claim-01');db.prepare('DELETE FROM relations WHERE id=?').run('audit-relation-1');db.prepare('DELETE FROM claims WHERE id=?').run('audit-claim-01');});
record('delete_old_index_rejected',await queryOnce(config(kb2,idx1,p2),query));
assert.equal((await buildIndex('delete-index',kb2,p2,idx2)).code,0);assert.equal((await buildVectors('delete-vectors',idx2)).code,0);
let deleteService=new RetrievalService(config(kb2,idx2,p2));let deletedLookup;
try{await deleteService.query('claim',{id:'audit-claim-01'});deletedLookup='unexpected return';}catch(e){deletedLookup=e.code;}finally{await deleteService.close();}
record('delete_rebuild',{deleted_claim_lookup:deletedLookup,deleted_claim_vector:claimVector(idx2,'audit-claim-01'),unaffected_claim:await queryOnce(config(kb2,idx2,p2),query)});

const liveKb=resolve(fixtures,'kb-live-delete-mode');cpSync(kb0,liveKb,{recursive:true});let live=new RetrievalService(config(liveKb,idx0,p0));
const writer=new DatabaseSync(resolve(liveKb,'graph.sqlite'));writer.prepare('UPDATE claims SET text=text||? WHERE id=?').run(' live mutation','audit-claim-00');writer.close();
let liveResult;try{await live.retrieve(query);liveResult='unexpected return';}catch(e){liveResult={code:e.code,message:e.message};}finally{await live.close();}
record('live_rollback_journal_update_rejected',{existing_session:liveResult,new_session:await queryOnce(config(liveKb,idx0,p0),query)});

function checkpointPreload(mode){const file=resolve(fixtures,`${mode}.mjs`);writeFileSync(file,`import fs from 'node:fs';import {syncBuiltinESMExports} from 'node:module';const write=fs.writeFileSync;let count=0;fs.writeFileSync=function(path,...args){if(String(path).endsWith('vector-progress.json')&&++count===2){${mode==='kill-after-checkpoint'?"write.call(this,path,...args);process.kill(process.pid,'SIGKILL');":"throw new Error('AUDIT_INJECTED_FAILURE_AFTER_VECTOR_FSYNC_BEFORE_CHECKPOINT');"}}return write.call(this,path,...args);};syncBuiltinESMExports();\n`);return file;}
const killIndex=resolve(fixtures,'index-kill');assert.equal((await buildIndex('kill-index',kb0,p0,killIndex)).code,0);
const killed=await buildVectors('kill-vectors',killIndex,checkpointPreload('kill-after-checkpoint'));
const killedProgress=JSON.parse(readFileSync(resolve(killIndex,'vector-progress.json'),'utf8'));
const resumed=await buildVectors('kill-resume-vectors',killIndex);
record('process_kill_after_committed_checkpoint',{first_exit:killed.code,signal:killed.signal,checkpoint_next:killedProgress.next,retry_exit:resumed.code,final:await queryOnce(config(kb0,killIndex,p0),query),old_snapshot:await queryOnce(config(kb0,idx0,p0),query)});

const tornIndex=resolve(fixtures,'index-torn-checkpoint');assert.equal((await buildIndex('torn-index',kb0,p0,tornIndex)).code,0);
const torn=await buildVectors('torn-vectors',tornIndex,checkpointPreload('throw-before-checkpoint'));
const tornProgress=JSON.parse(readFileSync(resolve(tornIndex,'vector-progress.json'),'utf8'));
const tornRetry=await buildVectors('torn-retry-vectors',tornIndex);
record('vector_fsync_checkpoint_gap',{first_exit:torn.code,checkpoint_vectors:tornProgress.next,file_vectors:statSync(resolve(tornIndex,'vectors.f32')).size/(512*4),retry_exit:tornRetry.code,retry_error:tornRetry.stderr_tail,default_open:await queryOnce(config(kb0,tornIndex,p0),query),explicit_fallback:await queryOnce(config(kb0,tornIndex,p0),{...query,allowDegraded:true})});

const failManifest=resolve(fixtures,'fail-index-manifest.mjs');writeFileSync(failManifest,"import fs from 'node:fs';import {syncBuiltinESMExports} from 'node:module';const write=fs.writeFileSync;fs.writeFileSync=function(path,...args){if(String(path).endsWith('manifest.json'))throw new Error('AUDIT_INDEX_MANIFEST_WRITE_FAILURE');return write.call(this,path,...args);};syncBuiltinESMExports();\n");
const incompleteIndex=resolve(fixtures,'index-incomplete');
const incomplete=await buildIndex('incomplete-index',kb0,p0,incompleteIndex,failManifest),incompleteRetry=await buildIndex('incomplete-index-retry',kb0,p0,incompleteIndex);
record('projection_build_failure_retry',{first_exit:incomplete.code,same_directory_retry_exit:incompleteRetry.code,retry_error:incompleteRetry.stderr_tail,old_snapshot:await queryOnce(config(kb0,idx0,p0),query)});

const corruptManifest=resolve(fixtures,'corrupt-vector-manifest.mjs');writeFileSync(corruptManifest,"import fs from 'node:fs';import {syncBuiltinESMExports} from 'node:module';const write=fs.writeFileSync;fs.writeFileSync=function(path,...args){if(String(path).endsWith('manifest.json')){write.call(this,path,'{\"interrupted\":');throw new Error('AUDIT_INTERRUPTED_MANIFEST_OVERWRITE');}return write.call(this,path,...args);};syncBuiltinESMExports();\n");
const tornManifestIndex=resolve(fixtures,'index-torn-manifest');assert.equal((await buildIndex('manifest-index',kb0,p0,tornManifestIndex)).code,0);
const manifestFail=await buildVectors('manifest-vectors',tornManifestIndex,corruptManifest),manifestRetry=await buildVectors('manifest-retry-vectors',tornManifestIndex);
record('manifest_overwrite_interruption',{first_exit:manifestFail.code,retry_exit:manifestRetry.code,retry_error:manifestRetry.stderr_tail,even_opt_in_fallback:await queryOnce(config(kb0,tornManifestIndex,p0),{...query,allowDegraded:true}),old_snapshot:await queryOnce(config(kb0,idx0,p0),query)});

// WAL boundary: journal-mode setup changes only storage bytes; bind an otherwise identical copied index to that baseline before any mutation.
const walKb=resolve(fixtures,'kb-wal'),walIndex=resolve(fixtures,'index-wal');cpSync(kb0,walKb,{recursive:true});cpSync(idx0,walIndex,{recursive:true});
const walWriter=new DatabaseSync(resolve(walKb,'graph.sqlite'));walWriter.exec('PRAGMA journal_mode=WAL;PRAGMA wal_autocheckpoint=0;');
const walInitialHash=sha256(resolve(walKb,'graph.sqlite')),wm=JSON.parse(readFileSync(resolve(walIndex,'manifest.json'),'utf8'));wm.canonical_source_sha256=walInitialHash;wm.indexed_snapshot_sha256=walInitialHash;json(resolve(walIndex,'manifest.json'),wm);
let walSession=new RetrievalService(config(walKb,walIndex,p0)),freshWal;
const walInitial=await walSession.retrieve(query);assert.equal(walInitial.runtime.degraded,false);
const walText='WAL_COMMITTED_NEW_TEXT_20261025: only in isolated audit fixture';
walWriter.prepare('UPDATE claims SET text=? WHERE id=?').run(walText,'audit-claim-00');
let oldWalResult,newWalResult;
try{const p=await walSession.retrieve(query);oldWalResult={status:'returned',text:p.data.reviewed[0]?.text,degraded:p.runtime.degraded};}catch(e){oldWalResult={status:'threw',code:e.code,message:e.message};}
try{freshWal=new RetrievalService(config(walKb,walIndex,p0));const p=await freshWal.retrieve(query);newWalResult={status:'returned',text:p.data.reviewed[0]?.text,degraded:p.runtime.degraded,channels:p.runtime.actual_channels,index_problem:freshWal.indexProblem};}catch(e){newWalResult={status:'threw',code:e.code,message:e.message};}
record('wal_committed_update_same_graph_version',{condition:'Writable WAL database with no graph version change; not the shipped immutable DELETE-journal deployment. Tests whether content hash/session fingerprint catches such a writer.',main_file_hash_unchanged:sha256(resolve(walKb,'graph.sqlite'))===walInitialHash,wal_bytes:statSync(resolve(walKb,'graph.sqlite-wal')).size,actual_sqlite_text:walWriter.prepare('SELECT text FROM claims WHERE id=?').get('audit-claim-00').text,existing_session:oldWalResult,new_session:newWalResult,old_vectors_unchanged:claimVector(walIndex,'audit-claim-00').bytes===originalVector.bytes});
await walSession.close();await freshWal?.close();walWriter.close();
record('wal_after_checkpoint',await queryOnce(config(walKb,walIndex,p0),query));
result.completed=true;save();console.log(JSON.stringify({completed:true,scenarios:result.scenarios.length,commands:result.commands.length}));
