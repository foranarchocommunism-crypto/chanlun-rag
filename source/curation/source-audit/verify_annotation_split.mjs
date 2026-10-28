import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync,writeFileSync } from 'node:fs';
import { resolve,dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { KnowledgeGraph } from '../../src/core.mjs';
const agent=resolve(dirname(fileURLToPath(import.meta.url)),'../..'),root=resolve(agent,'../shared-knowledge/v0.1.0'),sha=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const before={database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},g=new KnowledgeGraph(root);
try{
 const plan=JSON.parse(readFileSync(resolve(agent,'curation/source-audit/stage-h-annotation-split-plan.json'),'utf8')),applied=JSON.parse(readFileSync(resolve(agent,'curation/source-audit/stage-h-annotation-split-applied.json'),'utf8'));
 assert.equal(g.metadata.graph_version,applied.graph_version);assert.equal(g.metadata.schema_version,'1.1.0');const rows=[];
 for(const item of plan.items){
  const parts=item.parts.map(s=>g.db.prepare('select * from passages where id=?').get(s.after.id));assert.equal(parts.map(s=>s.text).join(''),item.before.text);assert.deepEqual(parts.flatMap(s=>JSON.parse(s.normalized_map)),JSON.parse(item.before.normalized_map));
  for(const [i,p] of parts.entries())if(item.parts[i].kind==='unknown_annotation'){
   assert.equal(p.role,'unknown');assert.equal(p.speaker,null);assert.equal(p.published_at,null);assert.equal(g.db.prepare("select count(*) n from evidence e join claims c on c.id=e.claim_id where e.passage_id=? and c.review_status='reviewed'").get(p.id).n,0);
   const r=g.search(p.text,{scope:'source',limit:10});assert.equal(r.data.total,1);assert.equal(r.data.results[0].id,p.id);assert.equal(r.data.results[0].role,'unknown');rows.push({query:p.text,results:r.data.results.map(r=>({id:r.id,role:r.role,speaker:r.speaker,published_at:r.published_at}))});
   const cli=spawnSync(process.execPath,[resolve(agent,'bin/chan-kg.mjs'),'search',p.text,'--scope','source','--limit','10','--kb',root],{encoding:'utf8'});assert.equal(cli.status,0,cli.stderr);assert.deepEqual(JSON.parse(cli.stdout),r);
  }
 }
 const moved=g.getEvidence('evidence-66e71b5de52ad2a9');assert.equal(moved.passage_id,'volume_1-a53e99c37ca5-p0316-b004-s02');assert.equal(moved.quote_start,0);assert.equal(moved.quote_end,16);assert.equal(moved.role,'author_reply');assert.equal(moved.published_at,'2007-04-09 21:51:46');assert.equal(moved.passage_text,'有了结合律，方向都不是最重要的。');
 const old=plan.items[0].evidence_migrations.find(m=>m.before.id===moved.id).before;assert.equal(moved.quote,old.quote);assert.deepEqual(moved.source_spans,JSON.parse(old.source_spans));
 assert.equal(g.getClaim('candidate-ce7b8fbb2d590dfe'),null);assert.equal(g.getClaim('candidate-ce7b8fbb2d590dfe',{includeUnreviewed:true}),null);const rejected=g.getClaim('candidate-ce7b8fbb2d590dfe',{includeUnreviewed:true,reviewStatus:'rejected'});assert.equal(rejected.evidence.length,3);assert.ok(rejected.evidence.some(e=>e.role==='unknown'));
 const first=g.getEvidence('evidence-05b5c4e5f83d831b'),second=g.getEvidence('evidence-83686649456c158a');assert.equal(first.passage_text.includes('（注：'),false);assert.equal(second.passage_text.includes('（备注：'),false);assert.equal(second.role,'author_commentary');
 const required=['0408-b008','0408-b009','0408-b010','0409-b000','0409-b002'],shortAnswers=['evidence-9be60cb14e850afb','evidence-a4a4e9f37c497344','evidence-6f9ef383f21d0504'];
 const context=[];for(const id of shortAnswers){const e=g.getEvidence(id),ids=new Set(e.context.map(p=>p.id));const missing=required.filter(s=>!ids.has('volume_1-a53e99c37ca5-p'+s));context.push({evidence_id:id,returned_context_pages:[...new Set(e.context.map(p=>p.pdf_page))],required_question_passages:required,missing});}
 assert.deepEqual({database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
 const report={graph_version:g.metadata.graph_version,schema_version:g.metadata.schema_version,delivery_scope:'shared_knowledge_base_only',unknown_source_queries:rows,all_split_characters_and_mapping_preserved:true,reviewed_tail_quote_and_pdf_coordinates_preserved:true,rejected_candidate_default_and_unreviewed_hidden:true,existing_cli_source_role_parity:true,short_answer_context_live_audit:context,database_and_manifest_unchanged:true,pass:true,limits:['只验证两处已知夹注及三个短答上下文，不冒全书语义审计。','未知夹注仍保全文和页内定位，未知不等已证汇编者姓名；历史批次原始段落身份以provenance迁移映射解释。']};
 writeFileSync(resolve(agent,'curation/source-audit/stage-h-annotation-split-verification.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({graph_version:report.graph_version,source_annotations:2,reviewed_evidence_relocated:1,short_answer_context_missing:context.map(c=>({id:c.evidence_id,missing:c.missing})),pass:true}));
}finally{g.close();}
