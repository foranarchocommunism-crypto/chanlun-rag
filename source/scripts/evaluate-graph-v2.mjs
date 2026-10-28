// Real retrieval API comparison. Development labels are exposed, model-reviewed evidence only.
import assert from 'node:assert/strict';
import { existsSync,mkdirSync,readFileSync,writeFileSync,appendFileSync,readdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { RetrievalService } from '../src/retrieval.mjs';
import { locations } from '../src/config.mjs';
import { Reranker } from '../src/reranker.mjs';
import { sha256 } from '../src/corpus.mjs';
const argv=process.argv.slice(2),arg=(k,d)=>argv.includes(k)?argv[argv.indexOf(k)+1]:d;
const split=arg('--split','development'),output=resolve(arg('--out','build/graph-v2/development'));
mkdirSync(output,{recursive:true});
let casePath=resolve(arg('--cases','build/final-kb-retrieval-307029129712/cases.jsonl')),freeze=null;
if(split==='acceptance'){
 const frozenPath=arg('--frozen-plan','evaluation/graph-v2/frozen-plan.json');
 assert.ok(existsSync(frozenPath),'Independent reviewed acceptance data not yet frozen; cannot claim acceptance');
 freeze=JSON.parse(readFileSync(frozenPath,'utf8'));assert.equal(freeze.human_annotation_complete,true);
 casePath=resolve(freeze.cases_path);assert.equal(sha256(casePath),freeze.cases_sha256);
}
const allCases=readFileSync(casePath,'utf8').trim().split('\n').map(JSON.parse),cases=allCases.slice(0,Number(arg('--limit',allCases.length)));
if(split==='acceptance')assert.ok(cases.every(c=>c.human_gold_reviewed===true));
const paths=locations(),s=new RetrievalService(), legacyModule=await import(pathToFileURL(resolve('build/graph-v2/baseline/app/src/retrieval.mjs')));
const legacy=new legacyModule.RetrievalService({...paths,profilePath:resolve('build/graph-v2/baseline/app/profiles/default.json')});
await legacy.dense?.close();legacy.dense=s.dense;
s.reranker=new Reranker(paths.modelPath,s.index.models.reranker);legacy.reranker=s.reranker;
// Reuse only byte-identical ordered batches, preserving production padding/batching.
// Performance gates use the separate uncached benchmark, never these timings.
const modelScore=s.reranker.score.bind(s.reranker),batchCache=new Map();let nativeBatches=0,cacheHits=0;
s.reranker.score=async(query,texts)=>{
 const scores=[],truncated=[];let score_meaning;
 for(let i=0;i<texts.length;i+=4){const batch=texts.slice(i,i+4),key=JSON.stringify([query,batch]);let value=batchCache.get(key);
  if(!value){value=await modelScore(query,batch);batchCache.set(key,value);nativeBatches++;}else cacheHits++;
  scores.push(...value.scores);truncated.push(...value.truncated);score_meaning=value.score_meaning;
 }return {scores,truncated,score_meaning};
};
const inputs={database:sha256(s.graph.path),index:sha256(resolve(paths.indexPath,'manifest.json')),profile:sha256(paths.profilePath),experimental_profile:sha256(s.graphConfigPath),cases:sha256(casePath),evaluator:sha256('scripts/evaluate-graph-v2.mjs'),
 code:Object.fromEntries(readdirSync('src').filter(n=>n.endsWith('.mjs')).map(n=>[n,sha256(resolve('src',n))]))};
if(freeze)assert.deepEqual(inputs.code,freeze.code_sha256);
const progressPath=resolve(output,'progress.json'),progress=existsSync(progressPath)?JSON.parse(readFileSync(progressPath,'utf8')):{inputs,observations:[]};
assert.deepEqual(progress.inputs,inputs,'Resume requires identical code, data, profiles and cases');
const rows=progress.observations,save=()=>writeFileSync(progressPath,JSON.stringify({inputs,observations:rows}));
const arms=[['L',{}],['T40',{profile:'hybrid-graph-rerank',graphDepth:0,rerankBudget:40}],['T48',{profile:'hybrid-graph-rerank',graphDepth:0,rerankBudget:48}],
 ['G1',{profile:'hybrid-graph-v2-rerank',graphDepth:1}],['G2',{profile:'hybrid-graph-v2-rerank',graphDepth:2}],['G2-F',{profile:'hybrid-graph-v2-rerank',graphDepth:2,allowDegraded:true}]];
try{
 await s.retrieve({query:'中枢',profile:'hybrid-graph-rerank',graphDepth:0,limit:1});
 for(const c of cases.slice(rows.length)){
  batchCache.clear();
  const gold=[...new Set(c.expected_source_refs.map(x=>x.passage_id))],record={id:c.query_id,query:c.query_text,group:c.source_group??c.expected_chapter_refs?.join('|')??c.query_id,stratum:c.stratum??c.query_type,arms:{}};
  for(const [name,patch]of arms){
   const service=name==='L'?legacy:s,original=service.graphStage?.expand;
   if(name==='G2-F')service.graphStage.expand=()=>{throw new Error('EVALUATION_INJECTED_GRAPH_FAILURE');};
   const callStart=performance.now();
   try{
    const p=await service.retrieve({query:c.query_text,limit:20,contextBudget:60000,...patch});
    const primaryIds=p.runtime.primary_result_ids??[...p.data.reviewed,...p.data.research_leads].filter(x=>!x.retrieval.reasons?.some(r=>r.channel==='known_issue_group')).map(x=>x.id).slice(0,20);
    const claimMap=new Map([...p.data.reviewed,...p.data.research_leads].map(x=>[x.id,x]));
    const evidence=[...new Set(primaryIds.flatMap(id=>claimMap.get(id)?.evidence.map(e=>e.passage_id)??[]))];
    const hits=gold.filter(id=>evidence.includes(id)).length;
    record.arms[name]={primary_ids:primaryIds,evidence,recall:gold.length?hits/gold.length:null,complete:gold.length?Number(hits===gold.length):null,
     paths:p.data.relation_paths.map(p=>({path_id:p.path_id,depth:p.depth,relations:p.relation_path,evidence_chain_complete:p.evidence_chain_complete??false})),
     runtime:p.runtime,context_codepoints:p.data.budget.used_codepoints,
     integrity_errors:[...p.data.reviewed].filter(x=>x.review_status!=='reviewed'||!x.evidence.length||x.evidence.some(e=>e.claim_id!==x.id)).map(c=>c.id)};
   }catch(error){
    record.arms[name]={primary_ids:[],evidence:[],recall:gold.length?0:null,complete:gold.length?0:null,paths:[],integrity_errors:[],failed:true,
      error:{code:error.code??'ERROR',message:error.message},runtime:{elapsed_ms:performance.now()-callStart,stages:{}}};
   }finally{if(name==='G2-F')service.graphStage.expand=original;}
  }
  record.fallback_primary_equal=JSON.stringify(record.arms.T40.primary_ids)===JSON.stringify(record.arms['G2-F'].primary_ids);
  rows.push(record);save();
  if(rows.length%10===0)console.log(JSON.stringify({completed:rows.length,total:cases.length,rss:process.memoryUsage().rss}));
 }
 const mean=values=>{const a=values.filter(x=>x!==null&&Number.isFinite(x));return a.length?a.reduce((x,y)=>x+y,0)/a.length:null;},quantile=(a,p)=>[...a].sort((a,b)=>a-b)[Math.ceil(a.length*p)-1];
 const summary=Object.fromEntries(arms.map(([name])=>[name,{recall:mean(rows.map(r=>r.arms[name].recall)),complete:mean(rows.map(r=>r.arms[name].complete)),
  p95_ms:quantile(rows.map(r=>r.arms[name].runtime.elapsed_ms),.95),graph_p95_ms:quantile(rows.map(r=>r.arms[name].runtime.stages.graph?.elapsed_ms??0),.95),
  graph_only_admitted:rows.reduce((n,r)=>n+(r.arms[name].runtime.stages.graph?.admission?.graph_only??0),0),
  graph_promotions_in_primary:rows.reduce((n,r)=>n+(r.arms[name].runtime.stages.graph?.admission?.final_primary_ids?.length??0),0),
  queries_with_packaged_two_hop:rows.filter(r=>r.arms[name].paths.some(p=>p.depth===2&&p.evidence_chain_complete)).length,
  raw_hop2_queries:rows.filter(r=>(r.arms[name].runtime.stages.graph?.hop2_paths??0)>0).length,
  failures:rows.filter(r=>r.arms[name].failed).length,integrity_errors:rows.reduce((n,r)=>n+r.arms[name].integrity_errors.length,0)}]));
 const differences=Object.fromEntries(['L','T48','G1'].map(name=>{const valid=rows.filter(r=>!r.arms.G2.failed&&!r.arms[name].failed&&r.arms.G2.recall!==null&&r.arms[name].recall!==null);return [name,{
  joint_success_cases:valid.length,improved:valid.filter(r=>r.arms.G2.recall>r.arms[name].recall).length,regressed:valid.filter(r=>r.arms.G2.recall<r.arms[name].recall).length,mean_difference:mean(valid.map(r=>r.arms.G2.recall-r.arms[name].recall)),
  failed_queries_excluded_from_quality_comparison:true}];}));
 for(const [name,digest]of Object.entries(inputs.code))assert.equal(sha256(resolve('src',name)),digest,'Code changed during evaluation');
 const result={created_at:new Date().toISOString(),split,executed:true,real_api:true,all_models_local:true,independent_semantic_acceptance:split==='acceptance',human_reviewed:split==='acceptance',
  model_computation:{reuse:'identical query and ordered batch of4; production padding preserved',native_batches:nativeBatches,cache_hits:cacheHits,timings_valid_for_performance_gates:false},
  cases:rows.length,metrics_definition:'Gold passage recall from first20 primary claims; excludes issue-group extras and graph auxiliary claims; context60000 codepoints',inputs,summary,differences,
  fallback_primary_equal:rows.every(r=>r.fallback_primary_equal),peak_rss_bytes:process.resourceUsage().maxRSS*1024};
 writeFileSync(resolve(output,'per-query.jsonl'),rows.map(r=>JSON.stringify(r)).join('\n')+'\n');
 writeFileSync(resolve(output,'metrics.json'),JSON.stringify(result,null,2));writeFileSync(resolve(output,'versions-and-hashes.json'),JSON.stringify(inputs,null,2));
 console.log(JSON.stringify(result));
}finally{legacy.dense=null;legacy.reranker=null;await legacy.close();await s.close();}

