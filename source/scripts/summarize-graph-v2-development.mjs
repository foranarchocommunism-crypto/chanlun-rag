import {readFileSync,writeFileSync} from 'node:fs';
const p=JSON.parse(readFileSync('build/graph-v2/development-natural/progress.json','utf8'));
const rows=p.observations,counts={};
for(const arm of ['G1','G2']){
 const stats={queries_with_graph_only_primary:0,graph_only_primary_occurrences:0,rescued_primary_occurrences:0,anchor_primary_occurrences:0,query_no_anchor:0,queries_with_any_graph_promotion_in_primary:0,queries_with_two_hop_traversal:0,queries_with_complete_two_hop_packet:0};
 for(const r of rows){const a=r.arms[arm],g=a.runtime.stages.graph,ad=g?.admission;let novel=0;
  for(const id of ad?.final_primary_ids??[]){const origin=ad.promoted.find(p=>p.id===id).origin;
   if(origin==='graph_only'){stats.graph_only_primary_occurrences++;novel++;}else if(origin==='graph_rescued')stats.rescued_primary_occurrences++;else if(origin==='definition_anchor')stats.anchor_primary_occurrences++;
  }
  if(novel)stats.queries_with_graph_only_primary++;
  if(ad?.final_primary_ids?.length)stats.queries_with_any_graph_promotion_in_primary++;
  if(g?.reason==='no_query_anchor')stats.query_no_anchor++;
  if(g?.hop2_paths>0)stats.queries_with_two_hop_traversal++;
  if(a.paths.some(p=>p.depth===2&&p.evidence_chain_complete))stats.queries_with_complete_two_hop_packet++;
 }
 counts[arm]=stats;
}
const result={source:'development-natural/progress.json',independent_semantic_acceptance:false,counts,
 regressions_vs_T48:rows.filter(r=>r.arms.G2.recall<r.arms.T48.recall).map(r=>({id:r.id,query:r.query,T48:r.arms.T48.recall,G2:r.arms.G2.recall,
  T48_evidence_absent_from_G2_not_necessarily_gold:r.arms.T48.evidence.filter(id=>!r.arms.G2.evidence.includes(id))})),
 legacy_failures:rows.filter(r=>r.arms.L.failed).map(r=>({id:r.id,query:r.query,error:r.arms.L.error})),
 interpretation:'Candidate admission and two-hop traversal are active; this exposed set does not demonstrate quality gain. Full path packaging remains budget-limited under60000 codepoints; no complete path count is inferred from traversal counts.'};
writeFileSync('build/graph-v2/development-findings.json',JSON.stringify(result,null,2));console.log(JSON.stringify({counts,regressions:result.regressions_vs_T48.map(r=>({id:r.id,T48:r.T48,G2:r.G2}))}));
