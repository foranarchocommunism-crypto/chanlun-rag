import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';
import { readFileSync,writeFileSync,mkdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { fixture, request as template } from '../test/fixtures/graph-v2-fixture.mjs';
import { RetrievalService } from '../src/retrieval.mjs';
import { sha256 } from '../src/corpus.mjs';
import { pathToFileURL } from 'node:url';
const output=resolve('build/graph-v2/real-model-'+Date.now()), kb=resolve(output,'knowledge'), index=resolve(output,'index'), policy=resolve(output,'policy.json');
const request={...template,query:'起点甲的最终校验口令是什么？'};
mkdirSync(kb,{recursive:true});
const f=fixture(150);
f.corpus.claims.get('bridge').text='起点甲的最终校验口令采用桥接乙的登记值。';
f.corpus.claims.get('answer').text='桥接乙的通行暗号登记为「紫色天鹅」。';
for(const c of f.corpus.claims.values())if(c.id.startsWith('n')){
 c.text='索引词汇记录'+c.id+'：关键词为起点甲、最终、校验、口令。记录用途为词汇统计，不定义设备参数。';
 const e=f.corpus.evidenceByClaim.get(c.id)[0],p=f.corpus.passages.get(e.passage_id);
 p.text=c.text;e.quote=c.text;e.quote_end=[...c.text].length;
}
const db=new DatabaseSync(resolve(kb,'graph.sqlite'));db.exec(readFileSync('contracts/schema.sql','utf8'));
const ins=(table,columns,values)=>db.prepare('INSERT INTO '+table+'('+columns.join(',')+') VALUES('+values.map(()=>'?').join(',')+')').run(...values);
ins('metadata',['key','value'],['schema_version',JSON.stringify('1.1.0')]);ins('metadata',['key','value'],['graph_version',JSON.stringify('graph-v2-isolated-model-fixture')]);
ins('documents',['id','filename','sha256','page_count','resource_path'],['fixture-doc','SYNTHETIC-GRAPH-TEST.pdf','0'.repeat(64),1,'SYNTHETIC-GRAPH-TEST.pdf']);
ins('units',['id','title','kind','document_id','start_page','end_page'],['fixture-unit','隔离测试，不是作者知识','fixture','fixture-doc',1,1]);
ins('pages',['id','document_id','pdf_page','width','height','raw_text','geometry_path'],['fixture-page','fixture-doc',1,600,800,'synthetic','synthetic.json']);
for(const c of f.corpus.concepts.values())ins('concepts',['id','label','aliases'],[c.id,c.label,JSON.stringify(c.aliases)]);
let i=0;
for(const c of f.corpus.claims.values()){
 const e=f.corpus.evidenceByClaim.get(c.id)[0];
 ins('passages',['id','unit_id','document_id','pdf_page','block_index','role','speaker','text','raw_text','boxes','normalized_map','source_char_indices'],[e.passage_id,'fixture-unit','fixture-doc',1,i++,'author_body','synthetic fixture',c.text,c.text,'[]','[]','[]']);
 ins('claims',['id','text','kind','conditions','concept_ids','review_status','importance_level','importance_reason'],[c.id,c.text,c.kind,JSON.stringify(c.conditions),JSON.stringify(c.concept_ids),c.review_status,2,'synthetic fixture']);
 ins('evidence',['id','claim_id','passage_id','quote','quote_start','quote_end','source_spans'],[e.id,c.id,e.passage_id,c.text,0,[...c.text].length,'[]']);
}
for(const r of f.corpus.relations)ins('relations',['id','source','target','type','claim_ids','review_status'],[r.id,r.source,r.target,r.type,JSON.stringify(r.claim_ids),r.review_status]);
db.close();
const json=(p,v)=>writeFileSync(p,JSON.stringify(v,null,2));
json(resolve(kb,'manifest.json'),{schema_version:'1.1.0',graph_version:'graph-v2-isolated-model-fixture'});
json(policy,{policy_version:'synthetic-v2',graph_version:'graph-v2-isolated-model-fixture',issues:[]});
const deny=pathToFileURL(resolve('scripts/deny-network.mjs')).href;
for(const [name,args]of [['index',['scripts/build-index.mjs','--kb',kb,'--policy',policy,'--output',index]],['vectors',['scripts/build-vectors.mjs','--index',index]]]){
 const r=spawnSync(process.execPath,['--import',deny,...args],{encoding:'utf8',windowsHide:true,maxBuffer:4e6});
 writeFileSync(resolve(output,name+'.log'),r.stdout+'\n'+r.stderr);assert.equal(r.status,0,r.stderr);
}
const s=new RetrievalService({kbPath:kb,indexPath:index,policyPath:policy});
try{
 const lexical=s.lexicalSearch(request), dense=await s.dense.search(request.query,{mode:'knowledge',limit:100,accept:r=>s.eligible(s.corpus.claims.get(r.claim_id),request)});
 const baseline=await s.retrieve({...request,graphDepth:0});
 const score=s.reranker.score.bind(s.reranker),observed=[];
 s.reranker.score=async(q,texts)=>{observed.push(...texts);return score(q,texts);};
 const graph=await s.retrieve(request);s.reranker.score=score;
 const before=s.reranker; const inputRows=graph.runtime.stages.rerank.input_ids;
 const original=s.graphStage.packagePath;s.graphStage.packagePath=()=>{throw new Error('REAL_MODEL_PACKAGE_FAILURE');};
 const failed=await s.retrieve({...request,allowDegraded:true});s.graphStage.packagePath=original;
 const primary=p=>p.runtime.primary_result_ids;
 const result={created_at:new Date().toISOString(),fixture:output,synthetic:true,semantic_quality_claim:false,real_index_build:true,real_embedding_model:true,real_reranker:true,
 network_policy:'child index builders deny Node network APIs; current model classes enforce local_files_only',
 graph_only:!lexical.some(r=>r.id==='answer')&&!dense.results.some(r=>r.id==='answer'),
 lexical_answer_rank:lexical.findIndex(r=>r.id==='answer')+1,dense_answer_rank:dense.results.findIndex(r=>r.id==='answer')+1,
 actual_reranker_input:inputRows,baseline_primary:primary(baseline),graph_primary:primary(graph),
 uniform_rerank_inputs:inputRows.every((id,i)=>{const c=s.corpus.claims.get(id);return observed[i]===[c.text,...c.conditions,...c.exceptions].join(' ');}),
 terminal_primary_rank:primary(graph).includes('answer')?primary(graph).indexOf('answer')+1:null,
 no_terminal_top20_floor:true,
 complete_two_hop:graph.data.relation_paths.some(p=>p.depth===2&&p.evidence_chain_complete),
 fallback_primary_equal:JSON.stringify(primary(failed))===JSON.stringify(primary(baseline)),
 fallback_reranker_calls:failed.runtime.stages.rerank.calls,
 fallback_max_score_difference:Math.max(0,...baseline.data.reviewed.map(c=>Math.abs((failed.data.reviewed.find(x=>x.id===c.id)?.retrieval.rerank_score??NaN)-c.retrieval.rerank_score))),
 graph,baseline,fallback:failed,fixture_db_sha256:sha256(resolve(kb,'graph.sqlite'))};
 result.passed=result.graph_only&&inputRows.includes('answer')&&result.uniform_rerank_inputs&&result.fallback_primary_equal&&result.fallback_reranker_calls===1;
 json(resolve(output,'receipt.json'),result);json(resolve('build/graph-v2/real-model-receipt.json'),result);
 console.log(JSON.stringify({...result,graph:undefined,baseline:undefined,fallback:undefined,actual_reranker_input:undefined}));
 if(!result.passed)process.exitCode=1;
}finally{await s.close();}

