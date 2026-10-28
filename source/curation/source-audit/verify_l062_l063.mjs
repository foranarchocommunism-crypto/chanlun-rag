// Read-only verification of published knowledge and source associations.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {KnowledgeGraph} from '../../src/core.mjs';
const agent=resolve(dirname(fileURLToPath(import.meta.url)),'../..'),root=resolve(agent,'../shared-knowledge/v0.1.0');
const read=p=>JSON.parse(readFileSync(p,'utf8')),sha=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const before={db:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))};
const graph=new KnowledgeGraph(root),checks=[];
const claim=s=>{const c=graph.getClaim('lower-l063-c-stage-'+s);assert.ok(c,s);return c;};
try{
 assert.equal(graph.metadata.graph_version,'0.1.0-review-2ac69fd77eec');
 const plan=read(resolve(agent,'curation/source-audit/stage-h-l062-l063-amendment-plan.json'));
 const proof=read(resolve(agent,'curation/source-audit/stage-h-l062-l063-amendment-applied.json'));
 assert.ok(proof.pass);assert.equal(proof.final_graph_version,graph.metadata.graph_version);
 assert.equal(proof.all_original_reviewed_claims_unchanged,3312);assert.equal(proof.all_original_reviewed_evidence_only_allowed_figure_changes,4505);
 for(const a of plan.evidence_figure_amendments){const e=graph.db.prepare('SELECT * FROM evidence WHERE id=?').get(a.evidence_id);assert.equal(e.claim_id,a.claim_id);assert.deepEqual(JSON.parse(e.figure_ids),a.after_figure_ids);}
 checks.push('旧3312命题及4505引文/字符偏移/坐标逐行保存，8处图关联显式修订；62正文黑白图与两张后加彩色图分开。');

 const memory=claim('one-decomposition-remember-only-last-unfinished-one-minute-type');
 assert.equal(memory.conditions.length,2);assert.equal(memory.exceptions.length,1);assert.match(memory.text,/一种分解.*最近一个未完成.*分解多样.*更多/);
 assert.match(claim('ideal-operability-not-practical-per-trade-reconstruction').review_note,/质因数分解只是作者类比/);
 assert.match(claim('mark-child-for-intuition-other-level-marks-personal-choice').text,/次级别.*5分钟图.*30分钟乃至年线.*个人/);
 assert.match(graph.getClaim('lower-l063-macd-higher-chart-convenience').evidence.map(e=>e.quote).join(''),/参数.*上限/);
 checks.push('一种分解/已完成走势上移标注前提和多分解例外均保；周期标记自由、理想可操作与实际便利、MACD参数上限没有混成图周期等于中枢级别。');

 const raw=graph.db.prepare("SELECT * FROM figures WHERE id='volume_2-5332cd1b6038-p0011-fig1'").get();
 const redraw=graph.db.prepare("SELECT * FROM figures WHERE id='volume_2-5332cd1b6038-p0011-fig2'").get();
 assert.equal(raw.origin_status,'unverified');assert.match(raw.note,/3724.19/);assert.equal(redraw.origin_status,'later_annotation');assert.match(redraw.note,/3724.35.*3724.19/);
 const caseClaim=claim('july2-110-small-top111-small-bottom-divergence-case');assert.match(caseClaim.text,/110.*线段里.*小顶背驰.*111.*小底背驰/);
 assert.match(claim('111-green-macd-area-comparison-not-previous-arrow-proof').review_note,/未逐K完整解答/);
 for(const e of caseClaim.evidence){assert.equal(e.role,'author_commentary');assert.equal(e.published_at,'2007-07-02 15:32:58');}
 const stand=claim('july2-107-stand-atleast-center-oscillation-conditional');assert.equal(stand.conditions.length,2);assert.match(stand.text,/若能站稳.*107.*至少.*中枢震荡/);assert.match(stand.review_note,/未给完整中枢区间/);
 checks.push('110/111是线段内历史例，111绿柱比较未冒充全部逐K答案；107站稳只保至少震荡，原图3724.19/重绘3724.35各存，日期/原发未知与后加身份独立。');

 assert.match(claim('july2-3919-first-pressure-neckline-then-fiveweek-average').text,/3919.*第一压力.*5周/);
 assert.match(claim('july2-five-month-average-support-triangle-platform-watch-effective-break').text,/5月.*是否有效跌破/);
 assert.match(claim('center-oscillation-profit-not-necessarily-less-same-level-oneway-up').text,/纯理论.*不一定.*相应级别/);
 assert.match(claim('novice-oscillation-watch-half-flat-or-small-practice').text,/没有基础.*半仓或空仓.*少量资金/);
 assert.match(claim('novice-oscillation-rather-sell-early-than-late').text,/初学者.*震荡/);
 assert.match(claim('novice-avoid-authors-volatile-holdings-prefer-milder-stock').review_note,/自述.*未核账户/);
 checks.push('3919/5周压力与原5月支持区分，三角或平台限有效跌破条件；理论相对利润非实证，初学者观望/少量练习/卖早/避剧烈股及零成本自述边界保留。');

 const records=readFileSync(resolve(agent,'curation/lower/c_stage_l062_l063.reviewed.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
 let associations=0;const unique=new Set();
 for(const r of records){const actual=graph.getClaim(r.id);assert.equal(actual.text,r.text);assert.deepEqual(actual.conditions,r.conditions);assert.deepEqual(actual.exceptions,r.exceptions);
  for(const e of r.evidence){const a=actual.evidence.find(x=>x.passage_id===e.passage_id);assert.ok(a);assert.equal(a.quote,e.quote);assert.deepEqual(a.figure_ids,e.figure_ids);for(const id of e.figure_ids){associations++;unique.add(id);}}
 }
 const ledger=readFileSync(resolve(agent,'curation/lower/c_stage_l062_l063.coverage.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
 assert.equal(ledger.length,33);assert.equal(new Set(ledger.map(p=>p.passage_id)).size,33);
 for(const p of ledger){const r=graph.db.prepare('SELECT text FROM passages WHERE id=?').get(p.passage_id);assert.equal(createHash('sha256').update(r.text).digest('hex'),p.source_text_sha256);}
 checks.push('15新增命题逐字段与审核批次一致；17引文及全部指定图关联可返回，33段台账原文哈希完整，未将来源未核图自动认作作者原发。');

 const anchor=caseClaim.evidence[0].id;
 const requests=[['search',{query:'最近一个未完成'},['search','最近一个未完成']],['evidence',{id:anchor},['evidence',anchor]],['page',{documentId:'volume_2.pdf',page:11},['page','--document-id','volume_2.pdf','--page','11']]];
 const parity=[];
 for(const [command,args,argv] of requests){const shared=JSON.parse(JSON.stringify(graph.query(command,args)));const cli=spawnSync(process.execPath,[resolve(agent,'bin/chan-kg.mjs'),...argv,'--kb',root],{encoding:'utf8',maxBuffer:24*1024*1024});assert.equal(cli.status,0,cli.stderr);assert.deepEqual(JSON.parse(cli.stdout),shared);parity.push({command,args,cli_matches_shared:true});}
 assert.deepEqual({db:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
 const report={graph_version:graph.metadata.graph_version,delivery_scope:'shared_knowledge_base_only',checks,parity,new_claims:records.length,new_evidence:17,new_figure_associations:associations,new_unique_figures:unique.size,old_figure_associations_amended:8,ledger_passages:33,source_hashes_match:true,database_and_manifest_unchanged:true,pass:true,limits:['同一主代理语义和原图复核，不称独立或人工金标准。','63留给读者的笔/底分型/中枢练习，需64后文来源继续联读，不能由后加图补作者原答。','64课223段、全书最终覆盖与交付审计尚未完成；历史执行/收益/原博客外部事实未核。']};
 writeFileSync(resolve(agent,'curation/source-audit/stage-h-l062-l063-verification.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({graph_version:report.graph_version,boundary_groups:checks.length,parity:parity.length,new_figure_associations:associations,pass:true}));
}finally{graph.close();}
