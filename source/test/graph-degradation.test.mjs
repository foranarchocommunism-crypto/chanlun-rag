import assert from 'node:assert/strict';
import { test } from 'node:test';
import { fakeService, request } from './fixtures/graph-v2-fixture.mjs';
for (const method of ['prepare','expand','anchors','validate','packagePath']) test('C01-C05 '+method+' failure has atomic fallback, strict mode and next-request recovery',async()=>{
  const s=fakeService(), baseline=await s.retrieve({...request,graphDepth:0});
  const original=s.graphStage[method], before={...s.calls};
  s.graphStage[method]=function(...args){ original.apply(this,args); throw new Error('INJECTED_'+method); };
  const p=await s.retrieve({...request,allowDegraded:true});
  assert.deepEqual(p.data,baseline.data); assert.equal(p.runtime.degraded,true);
  assert.equal(p.runtime.stages.graph.status,'failed');assert.equal(p.runtime.stages.graph.committed_paths,0);
  assert.equal(p.runtime.actual_channels.some(c=>c.includes('graph')),false);
  assert.equal(s.calls.dense-before.dense,1);assert.equal(s.calls.rerank-before.rerank,1);
  await assert.rejects(s.retrieve(request),e=>e.code==='GRAPH_EXECUTION_ERROR');
  assert.equal(s.graphStage.view,null);
  s.graphStage[method]=original;
  const next=await s.retrieve(request);assert.ok(next.runtime.stages.graph.committed_paths>0);
});
test('C04 invalid computed graph evidence fails validation but canonical corrupt errors propagate',async()=>{
  const s=fakeService(), original=s.graphStage.expand;
  s.graphStage.expand=function(...args){const e=original.apply(this,args);e.paths[0].steps[0].support_evidence_ids=['unknown'];return e;};
  const p=await s.retrieve({...request,allowDegraded:true});assert.equal(p.runtime.degradation_reasons[0].code,'GRAPH_OUTPUT_INVALID');
  s.graphStage.expand=()=>{throw Object.assign(new Error('canonical evidence missing'),{code:'CANONICAL_CORRUPT'});};
  await assert.rejects(s.retrieve({...request,allowDegraded:true}),e=>e.code==='CANONICAL_CORRUPT');
});
test('C06 deterministic monotonic deadline produces GRAPH_TIMEOUT',async()=>{
  const s=fakeService();let ticks=0;s.graphStage.clock=()=>ticks++>5?200:0;
  const p=await s.retrieve({...request,allowDegraded:true});assert.equal(p.runtime.degradation_reasons[0].code,'GRAPH_TIMEOUT');
});
for(const id of ['bridge','answer'])test('C02 failure during actual traversal support lookup: '+id,async()=>{
  const s=fakeService(),baseline=await s.retrieve({...request,graphDepth:0});
  const get=s.corpus.evidenceByClaim.get.bind(s.corpus.evidenceByClaim);
  s.corpus.evidenceByClaim.get=key=>{if(key===id)throw new Error('during traversal '+id);return get(key);};
  const p=await s.retrieve({...request,allowDegraded:true});assert.deepEqual(p.data,baseline.data);
  assert.equal(p.runtime.stages.graph.status,'failed');assert.equal(s.graphStage.view,null);
});
test('C07 invalid request, version errors and cancellation cannot be swallowed',async()=>{
  const s=fakeService();
  await assert.rejects(s.retrieve({...request,query:'',allowDegraded:true}),e=>e.code==='INVALID_REQUEST');
  s.ensureCurrent=()=>{throw Object.assign(new Error('stale'),{code:'INDEX_STALE'});};
  await assert.rejects(s.retrieve({...request,allowDegraded:true}),e=>e.code==='INDEX_STALE');
  const c=new AbortController();c.abort();
  await assert.rejects(fakeService().retrieve({...request,allowDegraded:true},{signal:c.signal}),e=>e.name==='AbortError');
});
test('C08 failed queued request does not poison the next request',async()=>{
  const s=fakeService();let n=0;const expand=s.graphStage.expand;
  s.graphStage.expand=function(...args){if(!n++)throw new Error('first request');return expand.apply(this,args);};
  const results=await Promise.allSettled([s.retrieve(request),s.retrieve(request)]);
  assert.equal(results[0].status,'rejected');assert.equal(results[1].status,'fulfilled');
  assert.ok(results[1].value.runtime.queue_wait_ms>=0);
});
test('C09 independent dense and graph failures preserve lexical fallback and all reasons',async()=>{
  const s=fakeService();s.dense.search=async()=>{throw new Error('dense failed');};s.graphStage.expand=()=>{throw new Error('graph failed');};
  const p=await s.retrieve({...request,allowDegraded:true});
  assert.equal(p.runtime.degradation_reasons.length,2);
  assert.deepEqual(p.runtime.actual_channels,['structured_lexical','cross_encoder_rerank']);
});
test('C09 reranker failure cannot turn graph seats into forced final positions',async()=>{
  const s=fakeService();s.reranker.score=async()=>{throw new Error('ranker failed');};
  const p=await s.retrieve({...request,allowDegraded:true});
  assert.equal(p.runtime.stages.graph.status,'discarded');assert.equal(p.data.relation_paths.length,0);
  assert.equal(p.runtime.primary_result_ids.includes('answer'),false);
});
test('C10 normal budget exhaustion is visible without degradation',async()=>{
  const p=await fakeService().retrieve({...request,graphDepth:1,graphBudget:1});
  assert.equal(p.runtime.degraded,false);assert.notEqual(p.runtime.stages.graph.status,'failed');
});
test('legacy graph profile also gains the controlled failure boundary',async()=>{
  const s=fakeService(), input={...request,profile:'hybrid-graph-rerank',rerankBudget:40};
  const baseline=await s.retrieve({...input,graphDepth:0});
  s.graphStage.expand=()=>{throw new Error('legacy graph failure');};
  assert.deepEqual((await s.retrieve({...input,allowDegraded:true})).data,baseline.data);
});

