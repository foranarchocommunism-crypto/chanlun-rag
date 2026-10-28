// Prepare source material for independent human annotation; never certifies semantic truth.
import { readFileSync,writeFileSync,mkdirSync,existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { RetrievalService } from '../src/retrieval.mjs';
import { sha256 } from '../src/corpus.mjs';
const out=resolve('evaluation/graph-v2');mkdirSync(out,{recursive:true});
if(existsSync(resolve(out,'annotation-review.json')))throw new Error('Review record already exists; do not overwrite human decisions or cancellation.');
const s=new RetrievalService();
try{
 const exposed=new Set(),oldUnits=new Set();
 for(const p of ['build/final-kb-retrieval-307029129712/cases.jsonl','evaluation/acceptance-v1/cases.jsonl'])if(existsSync(p))for(const c of readFileSync(p,'utf8').trim().split('\n').map(JSON.parse)){
  for(const e of c.expected_source_refs??[])exposed.add(e.passage_id);
  for(const u of c.expected_chapter_refs??[])oldUnits.add(u);
 }
 const corpus=s.corpus,relations=corpus.relations.filter(r=>r.review_status==='reviewed');
 const admissible=id=>{const c=corpus.claims.get(id),es=corpus.evidenceByClaim.get(id)??[];return c?.review_status==='reviewed'&&c.kind==='explicit'&&c.ambiguity_status==='none'&&es.length&&es.every(e=>!exposed.has(e.passage_id));};
 const support=r=>r.claim_ids.filter(admissible).sort();
 const edges=relations.map(r=>({...r,eligible_supports:support(r)})).filter(r=>r.eligible_supports.length),adj=new Map();
 for(const r of edges)for(const n of [r.source,r.target]){if(!adj.has(n))adj.set(n,[]);adj.get(n).push(r);}
 const used=new Set(),chains=[],seen=new Set();
 for(const [middle,rs]of [...adj].sort((a,b)=>a[0].localeCompare(b[0])))for(const a of rs)for(const b of rs){
  if(a.id>=b.id)continue;
  const first=a.source===middle?a.target:a.source,last=b.source===middle?b.target:b.source;if(first===last)continue;
  const key=[a.id,b.id].join('|');if(seen.has(key))continue;seen.add(key);
  let chosen;
  for(const ca of a.eligible_supports)for(const cb of b.eligible_supports){
   if(ca===cb)continue;const passages=[...new Set([ca,cb].flatMap(id=>corpus.evidenceByClaim.get(id).map(e=>e.passage_id)))];
   if(passages.some(id=>used.has(id)))continue;chosen={ca,cb,passages};break;
  }
  if(!chosen)continue;chosen.passages.forEach(id=>used.add(id));
  const group='chain-'+String(chains.length+1).padStart(3,'0');
  chains.push({source_group:group,planned_split:chains.length<20?'development':'acceptance',question:null,question_author:null,human_gold_reviewed:false,
   entity_path:[first,middle,last].map(id=>({id,label:corpus.concepts.get(id).label})),relations:[a,b].map(r=>({id:r.id,type:r.type,source:r.source,target:r.target})),
   evidence_claims:[chosen.ca,chosen.cb].map(id=>corpus.hydrateClaim(id)),
   source_passage_ids:chosen.passages,source_units:[...new Set(chosen.passages.map(id=>corpus.passages.get(id).unit_id))],
   review_tasks:['Read the original quoted passages and surrounding source context','Verify each relation with all conditions and direction','Decide whether the combined question legitimately requires both sources; do not infer transitivity','Author a non-leading question and independently mark all required and acceptable evidence','Record rejected or ambiguous chain explicitly']});
  if(chains.length>=50)break;
 }
 const unique=chains.slice(0,50);
 const report={created_at:new Date().toISOString(),status:'awaiting_independent_human_annotation',semantic_acceptance_complete:false,canonical_database_sha256:sha256(s.graph.path),
  exposed_passages:exposed.size,eligible_relations:edges.length,prepared_distinct_disjoint_chains:unique.length,
  development_chain_sources:unique.filter(x=>x.planned_split==='development').length,acceptance_chain_sources:unique.filter(x=>x.planned_split==='acceptance').length,
  source_split_basis:'No source passage overlaps legacy240, exposed24, or another proposed chain. Chapter overlap is possible and explicitly listed; not a claim of unseen-document generalization.',
  target_counts:{new_development_questions:60,new_holdout_questions:120,holdout_two_hop_questions:60,holdout_distinct_chains:30},
  missing_work:['Independent human source and relation review','Human-authored/approved questions and relevance gold','Ordinary, conditional/negative and out-of-domain strata','Freeze full120 holdout only after source-group isolation verification'],
  chains:unique};
 writeFileSync(resolve(out,'source-review-pack.json'),JSON.stringify(report,null,2));
 writeFileSync(resolve(out,'annotation-review.json'),JSON.stringify({status:'not_reviewed',human_annotation_complete:false,reviewer:null,cases:[],source_pack_sha256:sha256(resolve(out,'source-review-pack.json'))},null,2));
 console.log(JSON.stringify({...report,chains:undefined}));
}finally{await s.close();}

