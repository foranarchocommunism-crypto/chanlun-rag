// Scope, provenance and quote associations for the published pilot64 completion.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {KnowledgeGraph} from '../../src/core.mjs';
const agent=resolve(dirname(fileURLToPath(import.meta.url)),'../..'),root=resolve(agent,'../shared-knowledge/v0.1.0');
const read=p=>JSON.parse(readFileSync(p,'utf8')),sha=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const graph=new KnowledgeGraph(root),before={db:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},checks=[];
const claim=s=>{const c=graph.getClaim('lower-l064-c-stage-'+s);assert.ok(c,s);return c;};
try{
 assert.equal(graph.metadata.graph_version,'0.1.0-review-307029129712');
 const proof=read(resolve(agent,'curation/source-audit/stage-h-l064-amendment-applied.json'));assert.ok(proof.pass);assert.equal(proof.final_graph_version,graph.metadata.graph_version);assert.equal(proof.all_original_reviewed_claim_semantics_unchanged,3327);assert.equal(proof.all_original_reviewed_evidence_unchanged,4522);
 assert.equal(claim('106-107-arrow-stroke-under-preset-rounding').conditions.length,2);
 assert.match(graph.getClaim('lower-l064-precision-consistent').text,/精度一旦预设.*一致/);
 assert.match(graph.getClaim('lower-l064-precision-software-limits').text,/不是理论必然.*自行预设/);
 assert.match(claim('108-109-not-three-segments-same-direction-gap-contained').review_note,/必要条件非充分.*突发逆向缺口早期说法另列待核/);
 assert.match(graph.getClaim('lower-l067-definition-refines-segment-destruction').text,/精确化/);
 checks.push('106至107限预设取整且一路一致，64自选与61截整选择并存；108至109至少三笔和顺向缺口保，突发逆向缺口仍有67精确化待联读记录，不伪造统一例外。');

 assert.match(claim('first-red-arrow-already-near-prior108-109-area-strong').text,/略破109.*面积.*108至109.*力度强/);
 assert.match(claim('110-111-compare104-105-around105-110-center').text,/104至105.*105至110.*不能用108至109/);
 assert.match(claim('110-not-third-sell105-107-near-leave-wait-structure-break').text,/105至107.*不构成三卖.*至少等.*被破坏/);
 const micro=claim('second-red-arrow-down-up-down-break-not-div-without-sudden-destruction');assert.match(micro.text,/价格图第二红箭头.*MACD第一个红箭头/);assert.equal(micro.exceptions.length,1);
 assert.match(claim('green-rebound-analogue-third-sell-micro-center-two-branches').text,/类中枢.*类三卖.*转大级别.*或.*移动/);
 const running=claim('running-up-down-up-second-micro-center-final-green-area-comparison');assert.match(running.text,/第二上与第一上低点稍重合.*第二类中枢前后两段/);assert.ok(!running.concept_ids.includes(graph.db.prepare("SELECT id FROM concepts WHERE label='盘整背驰'").get().id));
 checks.push('110至111对104至105、105至110枢与105至107所指不同；110接近非三卖。价格图/指标两套红箭头、突发破坏例外及类中枢/类三卖边界保，奔走型原高低字不静改。');

 assert.match(claim('idle-money-only-market-not-disrupt-normal-life').text,/只用空闲.*压力.*正常生活/);
 assert.match(claim('retail-follow-result-not-author-intervention-personal-resources').text,/纯技术角度错误.*普通散户.*自己的操作级别/);
 assert.match(claim('july10-instant3919-break-not-effective-stand').text,/瞬间突破3919.*压力未改.*有效突破/);
 assert.match(claim('annual-line-alone-not-good-need-new-capital-volume-signs').text,/不是.*年线.*一定好.*新资金.*成交量/);
 assert.match(claim('july16-weak-shortterm-no-buy-before-fiveweek-restand').text,/中短线且技术不好.*5周.*中长线.*可/);
 checks.push('闲钱/不影响生活、散户不照搬个人干预、瞬间3919非有效、年线须新资金迹象、短线弱技能5周等待与中长线动态建仓各有对象，不能删前提。');

 assert.match(claim('july8-platform-branch3400-strong-above-usual-trap-limit2800').text,/最强.*3400上.*一般.*极限约2800/);
 assert.match(claim('july8-large-platform-after-rebound-renewed-fall-limit2100').text,/平台后.*大反弹.*重新下跌.*2100/);
 assert.match(claim('july8-branch-duration-first-two-fast-july-third-atleast-halfyear').text,/最快7月.*第三种至少半年.*尚无预定/);
 assert.match(claim('july11-50pe-50percent-growth-to33-historical-valuation-example').review_note,/股价不变.*盈利.*预期增长/);
 assert.match(claim('july13-no-skill-fund-index-suggestion-not-tracking-guarantee').review_note,/原强说法.*非本项目.*收益保证/);
 checks.push('三角/平台/大平台三支含必要条件、最强/一般/极限和最快/至少时限，后验实际走势不倒写前瞻；PEG/50倍/指数不跑输及长期赚钱为作者历史论证，未冒当前事实或保证。');

 const fs=graph.db.prepare("SELECT * FROM figures WHERE document_id='volume_2-5332cd1b6038' AND pdf_page BETWEEN 12 AND 32").all();assert.equal(fs.length,5);assert.equal(fs.filter(f=>f.origin_status==='later_annotation').length,4);
 assert.match(fs.find(f=>f.id.endsWith('p0014-fig1')).note,/5分钟.*07\/03/);assert.match(fs.find(f=>f.id.endsWith('p0022-fig1')).note,/8月.*5235.16/);assert.match(fs.find(f=>f.id.endsWith('p0021-fig1')).note,/CCTV.*不能归作者/);
 assert.equal(graph.db.prepare("SELECT role FROM passages WHERE id='volume_2-5332cd1b6038-p0021-b004'").get().role,'reader');
 for(const suffix of ['gap-in-same-stroke','line-below-center-is-analogy'])assert.match(graph.getClaim('lower-l064-'+suffix).review_note,/2026-10-21.*已/);
 checks.push('1原发未核4后加图，原111的3724.19与重绘3724.35不静合；14的7月3日及22的8月行情晚于正文，CCTV回答为读者。两条旧图审未完成描述已更新，原命题/证据保持。');

 const rows=readFileSync(resolve(agent,'curation/lower/c_stage_l064.reviewed.jsonl'),'utf8').trim().split('\n').map(JSON.parse);let links=0;const unique=new Set();
 for(const r of rows){const actual=graph.getClaim(r.id);assert.equal(actual.text,r.text);assert.deepEqual(actual.conditions,r.conditions);assert.deepEqual(actual.exceptions,r.exceptions);
  for(const e of r.evidence){const found=actual.evidence.find(a=>a.passage_id===e.passage_id);assert.ok(found);assert.equal(found.quote,e.quote);assert.deepEqual(found.figure_ids,e.figure_ids);for(const f of e.figure_ids){links++;unique.add(f);}}
 }
 const ledger=readFileSync(resolve(agent,'curation/lower/c_stage_l064.coverage.jsonl'),'utf8').trim().split('\n').map(JSON.parse);assert.equal(ledger.length,223);assert.equal(new Set(ledger.map(r=>r.passage_id)).size,223);
 for(const p of ledger){const s=graph.db.prepare('SELECT text FROM passages WHERE id=?').get(p.passage_id);assert.equal(createHash('sha256').update(s.text).digest('hex'),p.source_text_sha256);}
 const example=claim('110-111-compare104-105-around105-110-center'),anchor=example.evidence.find(e=>e.passage_id.endsWith('p0013-b003')).id;
 const requests=[['search',{query:'104至105'},['search','104至105']],['evidence',{id:anchor},['evidence',anchor]],['page',{documentId:'volume_2.pdf',page:21},['page','--document-id','volume_2.pdf','--page','21']]],parity=[];
 for(const [command,args,argv] of requests){const shared=JSON.parse(JSON.stringify(graph.query(command,args)));const cli=spawnSync(process.execPath,[resolve(agent,'bin/chan-kg.mjs'),...argv,'--kb',root],{encoding:'utf8',maxBuffer:24*1024*1024});assert.equal(cli.status,0,cli.stderr);assert.deepEqual(JSON.parse(cli.stdout),shared);parity.push({command,args,cli_matches_shared:true});}
 assert.deepEqual({db:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
 const report={graph_version:graph.metadata.graph_version,delivery_scope:'shared_knowledge_base_only',checks,parity,pass:true,new_claims:42,new_evidence:62,ledger_passages:223,new_figure_associations:links,new_unique_figures:unique.size,source_hashes_match:true,database_and_manifest_unchanged:true,limits:['同一主代理四轮不是独立/人类复核，未核原博客。','突发逆向缺口早期说法、类中枢/奔走型特殊原字及实际执行/外部绩效继续显式待核。','108课逐段台账齐备不等全部知识解释已确认；全书最终质量审计/归档及哈希尚未完成。']};
 writeFileSync(resolve(agent,'curation/source-audit/stage-h-l064-verification.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({graph_version:report.graph_version,boundary_groups:checks.length,parity:parity.length,new_figure_associations:links,new_unique_figures:unique.size,pass:true}));
}finally{graph.close();}
