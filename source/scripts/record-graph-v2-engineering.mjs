import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,readdirSync,existsSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {sha256} from '../src/corpus.mjs';
const read=p=>JSON.parse(readFileSync(p,'utf8').replace(/^\uFEFF/,'')),dir='build/graph-v2/acceptance/';mkdirSync(dir,{recursive:true});
const tapPath='build/graph-v2/full-tests.tap',tap=readFileSync(tapPath,'utf8'),match=key=>Number(tap.match(new RegExp('^# '+key+' (\\d+)','m'))?.[1]??NaN);
assert.equal(match('fail'),0);assert.equal(match('pass'),match('tests'));assert.equal(match('cancelled'),0);assert.equal(match('skipped'),0);
const names=[...tap.matchAll(/^# Subtest: (.+)$/gm)].map(x=>x[1]),code=Object.fromEntries(readdirSync('src').filter(n=>n.endsWith('.mjs')).map(n=>[n,sha256(resolve('src',n))]));
const real=read('build/graph-v2/real-model-receipt.json'),interfaces=read('build/graph-v2/interfaces.json'),dev=read('build/graph-v2/development-natural/metrics.json');
assert.equal(real.passed,true);assert.equal(real.uniform_rerank_inputs,true);assert.equal(real.fallback_primary_equal,true);assert.equal(interfaces.passed,true);assert.equal(dev.fallback_primary_equal,true);
const fault={created_at:new Date().toISOString(),mechanism_passed:true,fallback_passed:true,trace_passed:true,code_sha256:code,
 tests:{total:match('tests'),passed:match('pass'),failed:0,tap_path:tapPath,tap_sha256:sha256(tapPath),names},
 real_model:{path:'build/graph-v2/real-model-receipt.json',sha256:sha256('build/graph-v2/real-model-receipt.json'),synthetic:true,semantic_quality_claim:false,graph_only:real.graph_only,primary_rank:real.terminal_primary_rank,complete_two_hop:real.complete_two_hop,uniform_rerank_inputs:real.uniform_rerank_inputs,no_top20_floor:true,fallback_max_score_difference:real.fallback_max_score_difference},
 interfaces:{path:'build/graph-v2/interfaces.json',sha256:sha256('build/graph-v2/interfaces.json'),passed:interfaces.passed},
 real_development_fallback:{queries:dev.cases,primary_equal:dev.fallback_primary_equal},
 tests_sha256:Object.fromEntries(readdirSync('test').filter(n=>n.endsWith('.mjs')).map(n=>[n,sha256(resolve('test',n))]))};
writeFileSync(dir+'fault-results.json',JSON.stringify(fault,null,2));
const plan=read('docs/research/2026-10-25-graph-retrieval-plan/acceptance-plan.json'),performance=read(dir+'performance.json'),delivery=existsSync('fresh-extraction-delivery-receipt.json')?read('fresh-extraction-delivery-receipt.json'):null;
const cases=plan.cases.map(c=>{
 const stageFor={C01:'prepare',C02:'expand',C03:'anchors',C04:'validate',C05:'packagePath'};
 const tests=names.filter(n=>n.startsWith(c.id+' ')||['B01','B02'].includes(c.id)&&n.startsWith('B01/B02 ')||stageFor[c.id]&&n.startsWith('C01-C05 '+stageFor[c.id]+' '));let status=tests.length?'passed':'not_run',evidence=tests;
 if(c.id==='A02'){status=real.passed?'passed':'failed';evidence=['build/graph-v2/real-model-receipt.json','Revised by direct user instruction: actual uniform model scoring, no forced terminal top20 or two-hop lower bound.'];}
 if(c.id==='D01'){status=interfaces.passed?'passed':'failed';evidence=['build/graph-v2/interfaces.json'];}
 if(c.id==='P01'){status=performance.passed?'passed':'failed';evidence=[dir+'performance.json'];}
 if(c.id==='D02'){status=delivery?.passed?'passed':'not_run';evidence=['fresh-extraction-delivery-receipt.json'];}
 if(c.id==='A07'){status='mechanism_passed_semantic_not_accepted';evidence.push('No independent literal-collision/paraphrase relevance labels; no semantic pass inferred from literal routing tests.');}
 if(c.id==='Q01'){status='cancelled_human_annotation_not_accepted';evidence=['evaluation/graph-v2/scope-decision-2026-10-25.json','build/graph-v2/development-natural/metrics.json'];}
 return{id:c.id,status,evidence};
});
cases.push(...names.filter(n=>/^N0[123] /.test(n)).map(name=>({id:name.slice(0,3),status:'passed',evidence:[name]})));
writeFileSync(dir+'case-results.json',JSON.stringify({created_at:new Date().toISOString(),original_plan_retained_as_history:true,revised_cases:['A02','B01','B06'],scope_decision:'evaluation/graph-v2/natural-competition-decision.json',cases},null,2));
const before=read('build/graph-v2/protected-inputs-before.json'),protectedInputs=before.map(x=>({...x,current_sha256:sha256(x.path),unchanged:sha256(x.path).toLowerCase()===x.sha256.toLowerCase()}));
assert.ok(protectedInputs.every(x=>x.unchanged));writeFileSync('build/graph-v2/protected-inputs-after.json',JSON.stringify({passed:true,files:protectedInputs},null,2));
console.log(JSON.stringify({tests:fault.tests.total,mechanism:true,fallback:true,trace:true,case_statuses:cases.map(c=>[c.id,c.status]),protected_inputs_unchanged:true}));
