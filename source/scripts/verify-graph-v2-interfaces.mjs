import assert from 'node:assert/strict';
import { readFileSync,writeFileSync,mkdirSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { AjvJsonSchemaValidator } from '@modelcontextprotocol/sdk/validation/ajv-provider.js';
import { RetrievalService } from '../src/retrieval.mjs';
const output=resolve('build/graph-v2'),deny=pathToFileURL(resolve('scripts/deny-network.mjs')).href;
mkdirSync(output,{recursive:true});const service=new RetrievalService();
const client=new Client({name:'graph-v2-interface-verifier',version:'1.0.0'},{capabilities:{}});
const transport=new StdioClientTransport({command:process.execPath,args:['--import',deny,resolve('bin/chan-kg-mcp.mjs')],stderr:'pipe'});
let diagnostics='';transport.stderr?.on('data',d=>diagnostics+=d);
const report={started_at:new Date().toISOString(),passed:false,checks:[]};
try{
 await client.connect(transport);const tools=await client.listTools();
 assert.ok(tools.tools.find(t=>t.name==='retrieve').inputSchema.properties.profile.enum.includes('hybrid-graph-v2-rerank'));
 const schema=JSON.parse(readFileSync('contracts/evidence-packet.schema.json','utf8'));delete schema.$schema;
 const validate=new AjvJsonSchemaValidator().getValidator(schema);
 for(const request of [
  {query:'中枢是什么，成立需要什么条件？',profile:'hybrid-graph-v2-rerank',limit:5,contextBudget:60000},
  {query:'如何烤披萨？',profile:'hybrid-graph-v2-rerank',limit:2,rerankBudget:40},
  {query:'背驰与买卖点有哪些关系？',profile:'hybrid-graph-v2-rerank',limit:3,rerankBudget:20}
 ]){
  const js=await service.retrieve(request),mcp=await client.callTool({name:'retrieve',arguments:request});
  assert.ok(!mcp.isError,JSON.stringify(mcp));assert.equal(validate(js).valid,true);
  const args=['--import',deny,'bin/chan-kg.mjs','retrieve',request.query,'--profile',request.profile,'--limit',String(request.limit),...(request.rerankBudget?['--rerank-budget',String(request.rerankBudget)]:[])];
  const cli=spawnSync(process.execPath,args,{encoding:'utf8',windowsHide:true,maxBuffer:4e6});assert.equal(cli.status,0,cli.stderr);
  assert.deepEqual(js.data,mcp.structuredContent.data);assert.deepEqual(js.data,JSON.parse(cli.stdout).data);
  const claim=js.data.reviewed[0];if(claim){const follow=await client.callTool({name:'claim',arguments:{id:claim.id}});assert.equal(follow.structuredContent.data.claim.id,claim.id);
    const evidence=await client.callTool({name:'evidence',arguments:{id:claim.evidence[0].id}});assert.ok(evidence.structuredContent.data.evidence.pdf_page>0);}
  report.checks.push({query:request.query,budget:request.rerankBudget??48,passed:true,graph_status:js.runtime.stages.graph.status,primary:js.runtime.primary_result_ids});
 }
 const invalid=await client.callTool({name:'retrieve',arguments:{query:'中枢',profile:'hybrid-graph-v2-rerank',allowDegraded:'false'}});assert.equal(invalid.isError,true);
 report.passed=true;report.invalid_boolean_rejected=true;report.node_network_apis_denied=true;
}finally{await client.close();await service.close();report.completed_at=new Date().toISOString();report.diagnostics=diagnostics;writeFileSync(resolve(output,'interfaces.json'),JSON.stringify(report,null,2));}
console.log(JSON.stringify(report));

