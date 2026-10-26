import assert from 'node:assert/strict';
import { test } from 'node:test';
import { fakeService, request } from './fixtures/graph-v2-fixture.mjs';
test('B08 two-hop packet contains every edge source and separately identified bridge evidence',async()=>{
  const p=await fakeService().retrieve({...request,limit:1});
  assert.equal(p.runtime.primary_result_ids[0],'answer');
  const path=p.data.relation_paths.find(p=>p.depth===2);
  assert.ok(path);assert.equal(path.steps.length,2);assert.equal(path.evidence_chain_complete,true);
  assert.deepEqual(path.steps.map(s=>s.support_evidence_ids[0]),['e-bridge','e-answer']);
  assert.equal(path.auxiliary_claims[0].id,'bridge');assert.ok(path.auxiliary_claims[0].conditions.length);
  assert.equal(p.data.budget.returned_primary,1);assert.match(path.semantics,/not_transitive/);
});
test('B09 small context defers whole paths with all relation continuation commands',async()=>{
  const s=fakeService(), ranked=[{id:'answer',score:1}], runtime={};
  const base=s.package(ranked,{...request,limit:1},runtime);
  const budget=Math.max(1000,[...JSON.stringify(base.data)].length+300);
  const stage=s.graphStage.run(s.lexicalSearch(request),[{results:s.lexicalSearch(request)}],request,s.profile.fusion,c=>c?.review_status==='reviewed');
  const p=s.package(ranked,{...request,limit:1,contextBudget:budget},runtime,stage.paths);
  assert.ok([...JSON.stringify(p.data)].length<=budget);
  assert.equal(p.data.budget.returned_primary,1);
  assert.equal(p.data.relation_paths.some(p=>p.depth===2),false);
  assert.equal(p.data.deferred.find(d=>d.path_id?.includes('r001/r002')).follow_ups.length,2);
  assert.equal(p.data.budget.used_codepoints,[...JSON.stringify(p.data)].length);
});

