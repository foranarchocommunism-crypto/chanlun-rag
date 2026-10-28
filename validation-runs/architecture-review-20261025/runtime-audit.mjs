import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
const out = dirname(fileURLToPath(import.meta.url)), root = resolve(out, '../..'), app = resolve(root, 'chan-kg-agent');
const { RetrievalService } = await import(pathToFileURL(resolve(app, 'src/retrieval.mjs')));
const { expandGraph } = await import(pathToFileURL(resolve(app, 'src/graph-expansion.mjs')));
const { fuse } = await import(pathToFileURL(resolve(app, 'src/lexical.mjs')));
const { sha256 } = await import(pathToFileURL(resolve(app, 'src/corpus.mjs')));
const results = { created_at: new Date().toISOString(), runtime: process.version, queries: [], faults: [], cached_graph_diagnostics: {}, source_delivery_comparison: [] };
const save = () => writeFileSync(resolve(out, 'runtime-audit.json'), JSON.stringify(results, null, 2));
for (const name of ['retrieval','graph-expansion','definition-anchors','corpus','dense','embedding','lexical','reranker','core','config']) {
 const a=resolve(app,`src/${name}.mjs`), b=resolve(root,`deliveries/chan-kg-agent-0.3.0-windows-x64-307029129712/app/src/${name}.mjs`);
 results.source_delivery_comparison.push({file:`src/${name}.mjs`,source_sha256:sha256(a),delivery_sha256:existsSync(b)?sha256(b):null,equal:existsSync(b)&&sha256(a)===sha256(b)});
}
const startup=performance.now(), service=new RetrievalService();
results.service_construct_ms=performance.now()-startup;
const compact=p=>({ids:p.data.reviewed.map(c=>c.id),status:p.data.status,paths:p.data.relation_paths.length,
 depth2:p.data.relation_paths.filter(p=>p.depth===2).length,anchors:p.data.reviewed.filter(c=>c.retrieval.definition_anchor_priority).map(c=>({id:c.id,score:c.retrieval.rerank_score})),runtime:p.runtime,budget:p.data.budget});
try {
 const queries=['中枢是什么，成立需要什么条件？','中枢与次级别有哪些关系？','线段与笔、走势类型之间有什么联系？','价格来回重叠的部分应该怎样确认？','最低级别的中枢和普通中枢定义哪里不同？','如何烤披萨？','upper-l017-center-definition'];
 for(const query of queries){
  const item={query};
  for(const [key,extra] of [['hybrid',{profile:'hybrid'}],['graph',{profile:'hybrid-graph'}],['default',{}],['rerank_graph_disabled',{graphDepth:0,graphBudget:0}]]){
   const p=await service.retrieve({query,limit:10,contextBudget:120000,...extra}); item[key]=compact(p);
   if(key==='default'&&query===queries[0])writeFileSync(resolve(out,'example-evidence-packet.json'),JSON.stringify(p,null,2));
  }
  results.queries.push(item); save(); console.log(JSON.stringify({query,completed:results.queries.length}));
 }
 const source=await service.retrieve({query:'基本上可以这样理解',mode:'source',profile:'hybrid-graph',limit:3}); results.source_mode=compact(source);
 const before=service.corpus.relations;
 service.corpus.relations=new Proxy(before,{get(target,property,receiver){if(property===Symbol.iterator)throw Object.assign(new Error('audit injected graph iterator failure'),{code:'AUDIT_GRAPH_FAILURE'});return Reflect.get(target,property,receiver);}});
 try{
  for(const profile of ['hybrid-graph','hybrid'])try{
   const p=await service.retrieve({query:'中枢成立条件',profile,allowDegraded:true,limit:3}); results.faults.push({profile,status:'returned',runtime:p.runtime});
  }catch(e){results.faults.push({profile,status:'threw',code:e.code,message:e.message});}
 }finally{service.corpus.relations=before;}
 const previous=JSON.parse(readFileSync(resolve(root,'validation-runs/agent-implementation-20261022/m3-hybrid-development.json'),'utf8'));
 const counters={cases:0,first_hop_budget_full:0,depth2_with_budget20:0,depth2_with_budget100:0,cyclic_paths_budget100:0,graph_changes_top20:0,graph_only_candidates_enter_top20:0,zero_added_candidates:0};
 const diagnostics=[];
 for(const item of previous.observations){
  const channels=[{name:'lexical',weight:1,results:item.raw_lexical},{name:'dense',weight:.5,results:item.raw_dense}], base=fuse(channels,100);
  const request={query:item.query_text,mode:'knowledge',limit:20,graphDepth:1,graphBudget:20};
  const eligible=c=>c?.review_status==='reviewed';
  const one=expandGraph(service.corpus,base,request,eligible),two=expandGraph(service.corpus,base,{...request,graphDepth:2},eligible),wide=expandGraph(service.corpus,base,{...request,graphDepth:2,graphBudget:100},eligible);
  const seen=new Set(),graphRank=one.paths.filter(p=>{if(seen.has(p.support_claim_id))return false;seen.add(p.support_claim_id);return true;}).map(p=>({id:p.support_claim_id,score:0}));
  const fused=fuse([...channels,{name:'graph',weight:.1,results:graphRank}],100),baseIds=new Set(base.map(r=>r.id));
  counters.cases++; if(one.paths.length===20)counters.first_hop_budget_full++;
  if(two.paths.some(p=>p.depth===2))counters.depth2_with_budget20++;
  if(wide.paths.some(p=>p.depth===2))counters.depth2_with_budget100++;
  counters.cyclic_paths_budget100+=wide.paths.filter(p=>new Set(p.concept_path).size<p.concept_path.length).length;
  if(JSON.stringify(base.slice(0,20).map(r=>r.id))!==JSON.stringify(fused.slice(0,20).map(r=>r.id)))counters.graph_changes_top20++;
  if(fused.slice(0,20).some(r=>!baseIds.has(r.id)))counters.graph_only_candidates_enter_top20++;
  if(!one.additions.length)counters.zero_added_candidates++;
  diagnostics.push({id:item.query_id,query:item.query_text,seed_concepts:new Set(base.slice(0,5).flatMap(r=>service.corpus.claims.get(r.id).concept_ids)).size,one_paths:one.paths.length,two_paths:two.paths.filter(p=>p.depth===2).length,wide_two_paths:wide.paths.filter(p=>p.depth===2).length});
 }
 results.cached_graph_diagnostics={scope:'Fresh execution of current graph code on previously recorded lexical/vector rankings; not a fresh embedding benchmark.',counters,observations:diagnostics};
 const warm=[];
 for(let i=0;i<6;i++){const p=await service.retrieve({query:queries[i%5],limit:10});warm.push(p.runtime);}
 results.warm_measurements={n:warm.length,observations:warm,p50_ms:[...warm].map(r=>r.elapsed_ms).sort((a,b)=>a-b)[3],max_ms:Math.max(...warm.map(r=>r.elapsed_ms))};
 const concurrentStart=performance.now();
 results.concurrent_measurements=await Promise.all(queries.slice(0,4).map(async query=>{const start=performance.now(),p=await service.retrieve({query,limit:5});return {query,wall_ms:performance.now()-start,reported_elapsed_ms:p.runtime.elapsed_ms,queue_wait_estimate_ms:performance.now()-start-p.runtime.elapsed_ms};}));
 results.concurrent_wall_ms=performance.now()-concurrentStart;results.peak_rss_bytes=process.resourceUsage().maxRSS*1024;save();
} finally { await service.close();save(); }
console.log(JSON.stringify({completed:true,counters:results.cached_graph_diagnostics.counters,faults:results.faults,warm:results.warm_measurements,concurrent:results.concurrent_measurements}));
