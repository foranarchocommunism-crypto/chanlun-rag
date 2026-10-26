import assert from 'node:assert/strict';
import { test } from 'node:test';
import { admitGraph } from '../src/graph-admission.mjs';
import { fixture, fakeService, request } from './fixtures/graph-v2-fixture.mjs';
test('A01 Graph-only candidates reach the actual scoring call despite 100 text candidates', async () => {
  const s = fakeService(), p = await s.retrieve(request);
  assert.ok(p.runtime.stages.rerank.input_ids.includes('answer'));
  assert.ok(p.runtime.stages.rerank.input_ids.includes('bridge'));
  assert.equal(p.runtime.stages.graph.admission.graph_only, 2);
  assert.equal(new Set(p.runtime.stages.rerank.input_ids).size, p.runtime.stages.rerank.candidates);
  assert.ok(p.runtime.primary_result_ids.includes('answer'));
});
for (const R of [20,40,44,48]) for (const C of [20,40,100]) test('A04 exact capacity R=' + R + ', C=' + C, async () => {
  const s = fakeService(), p = await s.retrieve({ ...request, rerankBudget: R, candidateBudget: C });
  const a = p.runtime.stages.graph.admission;
  assert.equal(a.text_protected, Math.min(40,R,C)); assert.equal(a.graph_allowance, Math.min(8,Math.max(0,Math.min(R,C)-40)));
  assert.ok(p.runtime.stages.rerank.candidates <= Math.min(R,C));
  assert.deepEqual(p.runtime.stages.rerank.input_ids.slice(0,a.text_protected), s.lexicalSearch(request).slice(0,a.text_protected).map(x=>x.id));
});
test('A03 duplicated paths and an already present anchor do not consume multiple seats', async () => {
  const f = fixture(), s = fakeService(f), stage = s.graphStage.run(f.base, [{results:f.base}], request, s.profile.fusion, c=>c?.review_status==='reviewed');
  const a = admitGraph(f.base,[{results:f.base}],[...stage.paths,...stage.paths],[{id:'seed',reasons:[]}],request);
  assert.equal(a.headCount,42); assert.equal(a.trace.graph_only,2); assert.equal(a.trace.definition_anchors,0);
  assert.equal(new Set(a.trace.rerank_input_ids).size,42);
});
test('A05 empty graph does not pad the scoring input', async () => {
  const f=fixture(); f.corpus.relations=[]; const p=await fakeService(f).retrieve(request);
  assert.equal(p.runtime.stages.rerank.candidates,40); assert.equal(p.runtime.stages.graph.status,'empty'); assert.equal(p.runtime.degraded,false);
});
test('A06 a two-claim bundle cannot enter one remaining slot', async () => {
  const f=fixture(), s=fakeService(f), stage=s.graphStage.run(f.base,[{results:f.base}],request,s.profile.fusion,c=>c?.review_status==='reviewed');
  const onlySecond=stage.paths.filter(p=>p.depth===2);
  const a=admitGraph(f.base,[{results:f.base}],onlySecond,[],request,1);
  assert.equal(a.trace.promoted.length,0); assert.equal(a.paths.length,0); assert.equal(a.trace.deferred.length,1);
});
test('A07 source, zero graph budget, no query root and explicit concept root are observable', async () => {
  for (const patch of [{mode:'source'},{graphBudget:0},{graphDepth:0},{query:'如何烤披萨？'},{query:'换一个完全不含实体的说法'}]) {
    const p=await fakeService().retrieve({...request,...patch});
    assert.equal(p.runtime.stages.graph.status,'skipped'); assert.equal(p.runtime.actual_channels.includes('supported_graph_expansion'),false);
  }
  const f=fixture(); f.corpus.claims.get('answer').concept_ids.push('A');
  const p=await fakeService(f).retrieve({...request,query:'没有原名称',conceptId:'A'});
  assert.ok(p.runtime.stages.graph.seed_nodes>0);
});

test('N02 second hop has no reserved candidate seat and path depth does not change admission priority',()=>{
  const f=fixture(),base=f.base,step=id=>({support_claim_id:id});
  const common={seed_rank:1,concept_path:['A','B'],steps:[step('one')],support_claim_id:'one'};
  const one={...common,path_id:'a-direct',depth:1},two={...common,path_id:'z-chain',depth:2,steps:[step('two')],support_claim_id:'two'};
  const run=paths=>admitGraph(base,[{results:base}],paths,[],request,1);
  const first=run([two,one]);assert.deepEqual(first.trace.promoted.map(x=>x.id),['one']);
  // Changing only depth cannot move a candidate ahead of its otherwise identical competitor.
  const changed=run([{...two,depth:1},{...one,depth:2}]);assert.deepEqual(changed.trace.promoted,first.trace.promoted);
});

test('N03 every candidate is reranked on its own text, conditions and exceptions, without a two-hop prompt',async()=>{
  const f=fixture(),s=fakeService(f),observed=[];
  s.reranker.score=async(query,texts)=>{observed.push(...texts);return{scores:texts.map(()=>0),truncated:texts.map(()=>false),score_meaning:'synthetic_equal_scores'};};
  const p=await s.retrieve(request);
  assert.ok(p.runtime.stages.rerank.input_ids.includes('answer'));
  p.runtime.stages.rerank.input_ids.forEach((id,i)=>{const c=f.corpus.claims.get(id);assert.equal(observed[i],[c.text,...c.conditions,...c.exceptions].join(' '));});
});

