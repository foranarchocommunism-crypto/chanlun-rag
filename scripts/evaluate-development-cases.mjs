// Re-run saved development retrieval plans without rewriting their source gold.
// Passing retrieval is not an evaluation of a generated answer.
import assert from 'node:assert/strict';
import { readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { KnowledgeGraph } from '../src/core.mjs';

const agent=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const out=resolve(agent,'evaluation');
const files=readdirSync(out).filter(x=>/^stage-g-batch-\d+\.cases\.jsonl$/.test(x)).sort();
const graph=new KnowledgeGraph(resolve(agent,'../shared-knowledge/v0.1.0'));
try {
  const observations=[],ids=new Set();
  for(const file of files){
    const cases=readFileSync(resolve(out,file),'utf8').trim().split('\n').map(JSON.parse);
    for(const item of cases){
      assert.ok(!ids.has(item.query_id),'duplicate question ID');ids.add(item.query_id);
      assert.equal(item.gold_review_status,'model_reviewed_development');
      const claims=item.required_claims.map(id=>graph.getClaim(id));
      assert.ok(claims.every(Boolean),item.query_id+': reviewed support missing');
      const anchors=claims.flatMap(c=>c.evidence);
      assert.ok(item.expected_evidence_ids.every(id=>anchors.some(x=>x.id===id)),item.query_id+': original evidence IDs changed');
      const observedClaims=new Set(),observedPassages=new Set(),observedSources=new Map(),queries=[];
      for(const request of item.retrieval_plan){
        const start=performance.now(),result=graph.query(request.command,request.args);
        for(const c of [...(result.data.results??[]),...(result.data.claims??[])]){
          observedClaims.add(c.id);
          for(const e of c.evidence??[]){observedPassages.add(e.passage_id);observedSources.set(e.passage_id,e);}
          if(c.role&&c.pdf_page){observedPassages.add(c.id);observedSources.set(c.id,c);}
        }
        for(const p of result.data.passages??[]){
          observedPassages.add(p.id);
          observedSources.set(p.id,{...p,document_id:result.data.document.id,printed_page:result.data.page.printed_page});
        }
        queries.push({request,total:result.data.total??result.data.passages?.length??null,
          truncated:result.data.truncated??false,elapsed_ms:performance.now()-start});
      }
      const usesPage=item.retrieval_plan.every(x=>x.command==='page');
      const missing=usesPage?item.expected_source_refs.filter(x=>!observedPassages.has(x.passage_id)).map(x=>x.passage_id):
        item.required_claims.filter(id=>!observedClaims.has(id));
      const sourceMismatches=[];
      for(const expected of item.expected_source_refs){
        const actual=observedSources.get(expected.passage_id);
        for(const field of ['document_id','pdf_page','printed_page','role','speaker','published_at']){
          if(expected[field]!==undefined&&actual?.[field]!==expected[field])
            sourceMismatches.push({passage_id:expected.passage_id,field,expected:expected[field],actual:actual?.[field]??null});
        }
      }
      observations.push({query_id:item.query_id,source_case_file:file,gold_created_graph_version:item.graph_version,
        original_expected_evidence_ids_preserved:true,automatic_retrieval_contract_pass:missing.length===0&&sourceMismatches.length===0,
        source_identity_matches_expected:sourceMismatches.length===0,source_mismatches:sourceMismatches,
        missing,queries,generated_answer_scored:false,semantic_answer_faithfulness_automatically_proven:false});
    }
  }
  const report={graph_version:graph.metadata.graph_version,executable_development_cases:ids.size,final_target_cases:240,
    source_case_files:files,gold_review_status:'model_reviewed_development',human_gold_reviewed:false,
    independent_test_set:false,generated_answers_evaluated:false,
    retrieval_plan_contract_passed:observations.filter(x=>x.automatic_retrieval_contract_pass).length,
    observations,limits:['逐批固定来源开发题，非独立或人工金标准。','只执行取证计划，未评分生成回答，也未完成240题及各检索基线对比。']};
  writeFileSync(resolve(out,'stage-g-development-current.results.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({graph_version:report.graph_version,cases:ids.size,passed:report.retrieval_plan_contract_passed,
    failures:observations.filter(x=>!x.automatic_retrieval_contract_pass)}));
  if(report.retrieval_plan_contract_passed!==ids.size)process.exitCode=1;
} finally {graph.close();}
