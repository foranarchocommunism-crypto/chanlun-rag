// Uncached paired wall-clock benchmark, separate from quality evaluation caching.
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {spawnSync} from 'node:child_process';
import {cpus,hostname} from 'node:os';
import {RetrievalService} from '../src/retrieval.mjs';
import {Reranker} from '../src/reranker.mjs';
import {locations} from '../src/config.mjs';
import {sha256} from '../src/corpus.mjs';
const out=resolve('build/graph-v2/acceptance');mkdirSync(out,{recursive:true});
const queries=readFileSync('build/final-kb-retrieval-307029129712/cases.jsonl','utf8').trim().split('\n').slice(0,30).map(JSON.parse);
const paths=locations(),current=new RetrievalService(),{RetrievalService:Legacy}=await import(pathToFileURL(resolve('build/graph-v2/baseline/app/src/retrieval.mjs')));
const legacy=new Legacy({...paths,profilePath:resolve('build/graph-v2/baseline/app/profiles/default.json')});
await legacy.dense?.close();legacy.dense=current.dense;
current.reranker=new Reranker(paths.modelPath,current.index.models.reranker);legacy.reranker=current.reranker;
const rows=[],cold=[],percentile=(xs,p)=>xs.length?[...xs].sort((a,b)=>a-b)[Math.ceil(xs.length*p)-1]:null;
const run=async(name,q)=>{const start=performance.now();try{const p=await(name==='L'?legacy:current).retrieve({query:q,limit:20,contextBudget:60000,...(name==='G2'?{profile:'hybrid-graph-v2-rerank'}:{})});return {arm:name,success:true,end_to_end_ms:performance.now()-start,queue_wait_ms:p.runtime.queue_wait_ms??0,graph_ms:p.runtime.stages.graph?.elapsed_ms??0,rerank_count:p.runtime.stages.rerank?.reranked??p.runtime.stages.rerank?.input_ids?.length??p.runtime.stages.graph?.admission?.rerank_input_ids?.length??40};}catch(e){return{arm:name,success:false,end_to_end_ms:performance.now()-start,error:{code:e.code,message:e.message}};}};
try{
 await run('L','中枢是什么？');await run('G2','中枢是什么？');
 for(let round=0;round<5;round++){
  for(const [i,q]of queries.entries())for(const arm of ((round+i)%2?['G2','L']:['L','G2']))rows.push({round,id:q.query_id,...await run(arm,q.query_text)});
  writeFileSync(resolve(out,'performance-progress.json'),JSON.stringify({rows}));console.log(JSON.stringify({round:round+1,rows:rows.length,rss:process.memoryUsage().rss}));
 }
 const peakRSS=process.resourceUsage().maxRSS*1024;
 legacy.dense=null;legacy.reranker=null;await legacy.close();await current.close();
 for(let i=0;i<3;i++){
  const t=performance.now(),r=spawnSync(process.execPath,['--import',pathToFileURL(resolve('scripts/deny-network.mjs')).href,'bin/chan-kg.mjs','retrieve','中枢是什么，成立需要什么条件？','--profile','hybrid-graph-v2-rerank','--limit','5'],{encoding:'utf8',windowsHide:true,maxBuffer:4e6,timeout:120000});
  cold.push({elapsed_ms:performance.now()-t,success:r.status===0,error:r.status===0?null:r.stderr});
 }
 const matched=queries.filter(q=>rows.filter(r=>r.id===q.query_id).every(r=>r.success)).map(q=>q.query_id);
 const aggregate=arm=>{const rs=rows.filter(r=>r.arm===arm),ok=rs.filter(r=>r.success),pair=ok.filter(r=>matched.includes(r.id));return{calls:rs.length,failures:rs.filter(r=>!r.success).length,p95_ms:percentile(ok.map(r=>r.end_to_end_ms),.95),matched_p95_ms:percentile(pair.map(r=>r.end_to_end_ms),.95),graph_p95_ms:percentile(ok.map(r=>r.graph_ms),.95),max_queue_wait_ms:Math.max(...ok.map(r=>r.queue_wait_ms)),max_rerank_count:Math.max(...ok.map(r=>r.rerank_count))};};
 const L=aggregate('L'),G2=aggregate('G2'),checks={current_no_failures:G2.failures===0,warm_absolute:G2.p95_ms<=6000,warm_ratio:G2.matched_p95_ms<=1.25*L.matched_p95_ms,graph:G2.graph_p95_ms<=50,rss:peakRSS<=2147483648,cold:cold.every(x=>x.success&&x.elapsed_ms<=12000),reranker:G2.max_rerank_count<=48};
 const result={created_at:new Date().toISOString(),executed:true,passed:Object.values(checks).every(Boolean),uncached:true,prewarmed:true,rounds:5,fixed_queries:queries.map(q=>({id:q.query_id,query:q.query_text})),host:{hostname:hostname(),cpu:cpus()[0].model,node:process.version},method:'First30 frozen legacy development cases, five rounds, alternating arm order, shared model instance, no score cache; paired timing excludes query groups where either arm failed, failures retained separately',matched_query_count:matched.length,L,G2,cold,peak_rss_bytes:peakRSS,checks,rows,
 inputs:{database:sha256(current.graph.path),profile:sha256(paths.profilePath),experimental_profile:sha256(current.graphConfigPath),code:Object.fromEntries(readdirSync('src').filter(x=>x.endsWith('.mjs')).map(x=>[x,sha256(resolve('src',x))]))}};
 writeFileSync(resolve(out,'performance.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({...result,rows:undefined,fixed_queries:undefined}));
}catch(e){console.error(e);legacy.dense=null;legacy.reranker=null;await legacy.close();await current.close();process.exitCode=1;}
