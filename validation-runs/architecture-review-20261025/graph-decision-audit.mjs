import { readFileSync,writeFileSync } from 'node:fs';
import { dirname,resolve } from 'node:path';
import { fileURLToPath,pathToFileURL } from 'node:url';
const out=dirname(fileURLToPath(import.meta.url)),root=resolve(out,'../..'),app=resolve(root,'chan-kg-agent');
const { KnowledgeGraph }=await import(pathToFileURL(resolve(app,'src/core.mjs')));
const { readCorpus }=await import(pathToFileURL(resolve(app,'src/corpus.mjs')));
const { expandGraph }=await import(pathToFileURL(resolve(app,'src/graph-expansion.mjs')));
const { fuse }=await import(pathToFileURL(resolve(app,'src/lexical.mjs')));
const { uniquePassages,rankedMetrics }=await import(pathToFileURL(resolve(app,'scripts/lib/retrieval-baselines.mjs')));
const graph=new KnowledgeGraph(resolve(root,'shared-knowledge/v0.1.0'));
try{
 const corpus=readCorpus(graph), cached=JSON.parse(readFileSync(resolve(root,'validation-runs/agent-implementation-20261022/m3-hybrid-development.json'),'utf8'));
 const gold=new Map(readFileSync(resolve(app,'build/final-kb-retrieval-307029129712/cases.jsonl'),'utf8').trim().split('\n').map(JSON.parse).map(c=>[c.query_id,[...new Set(c.expected_source_refs.map(e=>e.passage_id))]]));
 const evidence=new Map([...corpus.claims.values()].filter(c=>c.review_status==='reviewed').map(c=>[c.id,[...new Set((corpus.evidenceByClaim.get(c.id)??[]).map(e=>e.passage_id))].sort()]));
 const observations=[];
 for(const item of cached.observations){
  const channels=[{name:'lexical',weight:1,results:item.raw_lexical},{name:'dense',weight:.5,results:item.raw_dense}],base=fuse(channels,100),union=new Set(channels.flatMap(c=>c.results.map(r=>r.id)));
  const expansion=expandGraph(corpus,base,{query:item.query_text,mode:'knowledge',limit:20,graphDepth:1,graphBudget:20},c=>c?.review_status==='reviewed');
  const supported=[...new Set(expansion.paths.map(p=>p.support_claim_id))],onlyGraph=supported.filter(id=>!union.has(id));
  const enhanced=fuse([...channels,{name:'graph',weight:.1,results:supported.map(id=>({id,score:0}))}],100);
  const metric=rank=>rankedMetrics(uniquePassages(rank,evidence,100),gold.get(item.query_id),20);
  const relationCounts=new Map();for(const p of expansion.paths)relationCounts.set(p.relation_id,(relationCounts.get(p.relation_id)??0)+1);
  observations.push({id:item.query_id,query:item.query_text,lexical_candidates:item.raw_lexical.length,only_graph_support_candidates:onlyGraph.length,only_graph_candidates_entering_fused100:enhanced.filter(r=>onlyGraph.includes(r.id)).length,only_graph_examples:onlyGraph.slice(0,2),raw_reported_additions:expansion.additions.length,distinct_relations:relationCounts.size,largest_relation_path_share:Math.max(...relationCounts.values(),0),base:metric(base),graph:metric(enhanced)});
 }
 const sum=key=>observations.reduce((n,r)=>n+r[key],0),avg=(variant,key)=>observations.reduce((n,r)=>n+r[variant][key],0)/observations.length;
 const result={created_at:new Date().toISOString(),scope:'Current graph/fusion implementation replayed over stored raw lexical/vector rankings; definition anchors and reranker excluded to isolate ordinary graph expansion.',
  counts:{cases:observations.length,lexical_always_100:observations.every(r=>r.lexical_candidates===100),queries_with_graph_only_candidate:observations.filter(r=>r.only_graph_support_candidates>0).length,graph_only_candidate_occurrences:sum('only_graph_support_candidates'),graph_only_admitted_to_top100:sum('only_graph_candidates_entering_fused100'),queries_one_relation_uses_at_least_half_budget:observations.filter(r=>r.largest_relation_path_share>=10).length,queries_single_relation_uses_entire_budget:observations.filter(r=>r.largest_relation_path_share===20).length,average_distinct_relations:sum('distinct_relations')/observations.length},
  highest_support_relation:corpus.relations.map(r=>({id:r.id,type:r.type,source:corpus.concepts.get(r.source)?.label,target:corpus.concepts.get(r.target)?.label,supporting_claims:r.claim_ids.length})).sort((a,b)=>b.supporting_claims-a.supporting_claims).slice(0,5),
  scores:{graph_only_best:.1/61,lexical_rank100_min:1/160,dense_rank100_min:.5/160},
  metrics:{hybrid_recall20:avg('base','recall'),graph_recall20:avg('graph','recall'),hybrid_complete_groups20:avg('base','all_annotated_evidence_found'),graph_complete_groups20:avg('graph','all_annotated_evidence_found'),improved:observations.filter(r=>r.graph.recall>r.base.recall).length,regressed:observations.filter(r=>r.graph.recall<r.base.recall).length},observations};
 writeFileSync(resolve(out,'graph-decision-audit.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({...result,observations:undefined}));
}finally{graph.close();}
