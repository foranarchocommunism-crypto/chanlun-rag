import assert from 'node:assert/strict';
import { test } from 'node:test';
import { expandGraphV2, GRAPH_LIMITS } from '../src/graph-expansion.mjs';
import { fixture, request } from './fixtures/graph-v2-fixture.mjs';
const expand=(f,patch={})=>expandGraphV2(f.corpus,f.base,{...request,...patch},c=>c?.review_status==='reviewed');
test('B01/B02 duplicate supports count once; a competitive two-hop path can enter the shared pool',()=>{
  const f=fixture();
  for(let i=0;i<20;i++){f.claim('dup'+i,'重复的桥接支持',['A','B']);f.corpus.relations[0].claim_ids.push('dup'+i);}
  for(let i=0;i<30;i++){f.concept('D'+i);f.claim('d'+i,'干扰分支'+i,['A','D'+i]);f.relation('r1'+String(i).padStart(2,'0'),'A','D'+i,['d'+i]);}
  const p=expand(f);
  assert.ok(p.paths.some(p=>p.depth===2&&p.support_claim_id==='answer'));
  assert.equal(p.paths.filter(p=>p.depth===1&&p.relation_id==='r001').length,1);
  assert.ok(p.paths.length<=20); assert.ok(p.trace.max_fanout<=4);
});

test('N01 second hop has no minimum when stronger first-hop supports fill the common path budget',()=>{
  const f=fixture();
  f.concept('D');f.claim('direct','起点甲的直接证据',['A','D']);f.relation('r000','A','D',['direct']);
  const seeds=[{id:'direct'},{id:'bridge'},...f.base];
  const p=expandGraphV2(f.corpus,seeds,{...request,graphBudget:2},c=>c?.review_status==='reviewed');
  assert.ok(p.trace.hop2_discovered>0);assert.equal(p.trace.hop2_paths,0);assert.equal(p.paths.length,2);
  assert.equal(p.trace.selection_policy,'shared_pool_no_hop_reservations');
});
test('B03 an absent or unreviewed bridge cannot propagate',()=>{
  for(const state of ['missing','pending','rejected']){
    const f=fixture(); if(state==='missing')f.corpus.evidenceByClaim.delete('bridge'); else f.corpus.claims.get('bridge').review_status=state;
    assert.equal(expand(f).paths.some(p=>p.support_claim_id==='answer'),false);
  }
});
test('B03 all edge supports honor request eligibility, including document filtering',()=>{
  const f=fixture(), p=expandGraphV2(f.corpus,f.base,request,c=>c?.review_status==='reviewed'&&c.id!=='bridge');
  assert.equal(p.paths.length,0);
});
test('B03 research can traverse a pending bridge only with an explicit research pool',()=>{
  const f=fixture();f.corpus.claims.get('bridge').review_status='pending';f.corpus.relations[0].review_status='pending';
  const p=expandGraphV2(f.corpus,f.base,{...request,mode:'research'},c=>c&&c.review_status!=='rejected');
  const chain=p.paths.find(p=>p.depth===2);assert.ok(chain);assert.equal(chain.steps[0].support_review_status,'pending');
  assert.equal(expand(f).paths.some(p=>p.depth===2),false);
});
test('B04 high fanout, rejected entries and large support lists respect counted hard limits',()=>{
  const f=fixture();
  for(let i=0;i<600;i++){f.concept('N'+i);f.claim('c'+i,'edge',['A','N'+i],i%2?'rejected':'reviewed');f.relation('z'+String(i).padStart(3,'0'),'A','N'+i,['c'+i]);}
  const p=expand(f,{graphBudget:100});
  assert.ok(p.trace.edge_reads<=GRAPH_LIMITS.edges);assert.ok(p.trace.support_checks<=GRAPH_LIMITS.supports);
  assert.ok(p.trace.nodes<=64);assert.ok(p.trace.max_adjacency_reads<=32);assert.ok(p.trace.max_fanout<=4);assert.ok(p.truncated);
});
test('B05 cycles do not become paths, reverse direction and shared bridge are preserved',()=>{
  const f=fixture();f.concept('D','入口丁');f.claim('db','入口丁连桥接乙',['D','B']);f.relation('r003','D','B',['db']);
  const p=expand(f,{query:'起点甲与入口丁'});
  for(const path of p.paths) assert.equal(new Set(path.concept_path).size,path.concept_path.length);
  assert.ok(p.paths.some(p=>p.depth===2&&p.concept_path[0]==='A'&&p.support_claim_id==='answer'));
  assert.ok(p.paths.some(p=>p.depth===2&&p.concept_path[0]==='D'&&p.support_claim_id==='answer'));
  const rev=expand(f,{query:'终点丙'});assert.ok(rev.paths.some(p=>p.traversal_direction==='target_to_source_association_only'));
});
for(const depth of [0,1,2])for(const budget of [0,1,2,20,100])test('B06 bounded depth='+depth+' budget='+budget,()=>{
  const p=expand(fixture(),{graphDepth:depth,graphBudget:budget});
  assert.ok(p.paths.length<=budget);assert.ok(p.paths.every(p=>p.depth<=depth));if(budget===1)assert.ok(p.paths.every(p=>p.depth===1));
});
test('B07 row ordering does not alter path identity and canonical supports',()=>{
  const f=fixture();const a=expand(f).paths;
  f.corpus.relations.reverse();for(const r of f.corpus.relations)r.claim_ids.reverse();
  f.corpus.concepts=new Map([...f.corpus.concepts].reverse());
  assert.deepEqual(expand(f).paths,a);
});

