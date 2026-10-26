// Fail-closed default-activation gate. Missing/cancelled evidence is never a pass.
import {readFileSync,writeFileSync,existsSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {pathToFileURL} from 'node:url';
import {sha256} from '../src/corpus.mjs';
const number=x=>typeof x==='number'&&Number.isFinite(x);
export function numericQualityGates(metrics){
 const q=metrics?.acceptance_statistics;
 const superiority=x=>number(x?.difference)&&x.difference>=.05&&number(x.ci95_lower)&&x.ci95_lower>0;
 const noninferiority=x=>number(x?.difference)&&x.difference>=-.01&&number(x.ci95_lower)&&x.ci95_lower>=-.02;
 return {two_hop_quality:metrics?.independent_semantic_acceptance===true&&superiority(q?.two_hop?.G2_T48)&&superiority(q?.two_hop?.G2_G1),
 ordinary_quality:noninferiority(q?.ordinary?.G2_L)&&noninferiority(q?.ordinary?.G2_T48)&&q?.critical_regressions===0,
 negative_cases:q?.independently_reviewed_negatives===true&&q?.new_irrelevant_graph_primary===0&&q?.unsupported_path_conclusions===0};
}
export function verifyGates(root=process.cwd()){
 const read=p=>existsSync(resolve(root,p))?JSON.parse(readFileSync(resolve(root,p),'utf8').replace(/^\uFEFF/,'')):null;
 const plan=read('docs/research/2026-10-25-graph-retrieval-plan/acceptance-plan.json'),dir='build/graph-v2/acceptance/';
 const tests=read(dir+'fault-results.json'),perf=read(dir+'performance.json'),delivery=read('fresh-extraction-delivery-receipt.json'),metrics=read(dir+'metrics.json');
 const frozen=read('evaluation/graph-v2/frozen-plan.json'),review=read('evaluation/graph-v2/annotation-review.json'),versions=read(dir+'versions-and-hashes.json');
 const code=Object.fromEntries(readdirSync(resolve(root,'src')).filter(n=>n.endsWith('.mjs')).map(n=>[n,sha256(resolve(root,'src',n))]));
 const current=x=>x&&JSON.stringify(x)===JSON.stringify(code);
 const quality=numericQualityGates(metrics),required=(plan?.required_future_artifacts??[]).filter(p=>!p.endsWith('gate-results.json'));
 const natural=read('evaluation/graph-v2/natural-competition-decision.json');
 const missing=required.filter(p=>!existsSync(resolve(root,p))),validHuman=review?.human_annotation_complete===true&&frozen?.human_annotation_complete===true&&frozen?.cases_sha256&&existsSync(resolve(root,frozen.cases_path??'_missing'))&&sha256(resolve(root,frozen.cases_path))===frozen.cases_sha256;
 const engineeringCurrent=current(tests?.code_sha256),semanticCurrent=current(versions?.code)&&current(frozen?.code_sha256);
 const performanceValid=perf?.uncached===true&&perf?.rows?.length===300&&perf?.rounds===5&&perf?.G2?.failures===0&&
  number(perf.G2.p95_ms)&&perf.G2.p95_ms<=6000&&number(perf.L?.p95_ms)&&perf.G2.p95_ms<=1.25*perf.L.p95_ms&&
  number(perf.G2.graph_p95_ms)&&perf.G2.graph_p95_ms<=50&&number(perf.peak_rss_bytes)&&perf.peak_rss_bytes<=2147483648&&
  number(perf.G2.max_rerank_count)&&perf.G2.max_rerank_count<=48&&perf.cold?.length>=3&&perf.cold.every(r=>r.success===true&&number(r.elapsed_ms)&&r.elapsed_ms<=12000);
 const records=[
  ['mechanism',engineeringCurrent&&tests?.mechanism_passed===true,'deterministic mechanism tests and real-model positive control'],
  ['fallback',engineeringCurrent&&tests?.fallback_passed===true,'strict, permissive, fatal and recovery fault evidence'],
  ['two_hop_quality',!!validHuman&&semanticCurrent&&quality.two_hop_quality,'requires independent necessary-chain questions, +5pp versus T48 and G1, CI lower >0'],
  ['ordinary_quality',!!validHuman&&semanticCurrent&&quality.ordinary_quality,'requires independent ordinary and critical-condition judgments'],
  ['trace',engineeringCurrent&&tests?.trace_passed===true,'complete supported steps and bounded whole-path deferral'],
  ['negative_cases',!!validHuman&&semanticCurrent&&quality.negative_cases,'literal routing tests alone do not establish negative semantic relevance'],
  ['resources',current(perf?.inputs?.code)&&performanceValid,'uncached 30 queries x5 paired rounds, cold/RSS/graph/input limits'],
  ['delivery',current(delivery?.code_sha256)&&delivery?.passed===true&&delivery?.fresh_extraction===true,'fresh artifact hashes plus bundled JS/CLI/MCP and source follow-up']
 ].map(([id,passed,evidence])=>natural&&id==='two_hop_quality'?{id,passed:false,required:false,status:'retired_by_user',evidence:'No two-hop-specific superiority requirement; natural competition per direct user instruction.'}:{id,passed:passed===true,required:true,status:passed===true?'passed':'not_accepted',evidence});
 const statuses=read(dir+'case-results.json');
 const unresolved_cases=(plan?.cases??[]).filter(c=>statuses?.cases?.find(x=>x.id===c.id)?.status!=='passed').map(c=>c.id);
 const result={created_at:new Date().toISOString(),purpose:'graph_v2_default_activation_only',passed:!!plan&&!missing.length&&!unresolved_cases.length&&records.filter(g=>g.required).every(g=>g.passed),
  new_default_accepted:false,student_annotation_status:review?.status??'missing',missing_artifacts:missing,unresolved_cases,gates:records,
  decision:'Keep experimental profile default disabled. Two-hop has no reserved path/candidate slots, no result floor and no special reranking input; two-hop-specific superiority gate retired by user. Independent general semantic activation evidence remains absent.',code_sha256:code};
 result.new_default_accepted=result.passed;return result;
}
if(process.argv[1]&&import.meta.url===pathToFileURL(resolve(process.argv[1])).href){
 const r=verifyGates(),p=resolve('build/graph-v2/acceptance/gate-results.json');mkdirSync(dirname(p),{recursive:true});writeFileSync(p,JSON.stringify(r,null,2));console.log(JSON.stringify(r));if(!r.passed)process.exitCode=1;
}
