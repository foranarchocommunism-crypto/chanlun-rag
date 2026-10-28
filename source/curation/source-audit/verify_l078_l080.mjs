import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { KnowledgeGraph } from '../../src/core.mjs';
import { KnowledgeGraph as DesktopGraph } from '../../../chan-kg-desktop/vendor/core.mjs';

const agent=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
const root=resolve(agent,'../shared-knowledge/v0.1.0');
const sha=path=>createHash('sha256').update(readFileSync(path)).digest('hex');
const before={database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))};
const graph=new KnowledgeGraph(root),desktop=new DesktopGraph(root);
const id=(lesson,slug)=>`lower-l${lesson}-c-stage-${slug}`;
const claim=(lesson,slug)=>{const r=graph.getClaim(id(lesson,slug));assert.ok(r);return r;};
const page=n=>graph.query('page',{documentId:'volume_2.pdf',page:n}).data;
const checks=[];
try {
  const p162=page(162),p165=page(165);
  for(const n of ['003','004'])assert.equal(p162.passages.find(x=>x.id.endsWith('-b'+n)).role,'reader');
  const resumed=p162.passages.find(x=>x.id.endsWith('-b005'));
  assert.equal(resumed.role,'author_commentary');assert.equal(resumed.speaker,'缠中说禅');
  assert.equal(resumed.published_at,'2007-09-13 16:00:16');
  assert.equal(p165.passages.find(x=>x.id.endsWith('-b002')).role,'reader');
  assert.equal(p165.passages.find(x=>x.id.endsWith('-b003')).role,'author_commentary');
  assert.equal(p165.passages.find(x=>x.id.endsWith('-b003')).published_at,'2007-09-13 20:55:15');
  checks.push('引用网友后作者身份及文章时间恢复；网友原话、署名与后续答疑身份保留');
  const sequence=claim('078','second-sequence-inclusion-required');
  assert.match(sequence.text,/严格按包含关系.*不适用第一种/);
  assert.ok(claim('078','b-extension-after-break-bottom').conditions.includes('B已确认线段破坏其前段'));
  assert.ok(claim('078','destruction-backward-transmission').exceptions.some(x=>x.includes('新股')));
  checks.push('第二序列包含处理、B对前段已确认及新股首段例外保留');
  const standard=claim('078','standardize-only-basic-unit-analysis');
  assert.ok(standard.conditions.includes('以线段为没有内部结构的基本部件'));
  assert.match(standard.review_note,/不能倒改原始分段/);
  const right=claim('079','right-diagram-uncompleted-two-more-strokes');
  assert.match(right.text,/须再看两笔.*尚未完成/);
  assert.match(claim('079','right-diagram-nine-below-seven-alternative').conditions.join(' '),/9跌破7.*10位置不变/);
  checks.push('标准化限于高层部件用途；右图缺后续确认与假设变体条件分开');
  const method=claim('079','third-method-response-level');
  assert.ok(method.conditions.includes('散户有充足时间'));
  assert.ok(method.conditions.includes('交易通道可用'));
  assert.match(claim('079','third-method-first-return-exit').text,/不能新高或出现盘整背驰/);
  assert.ok(claim('079','third-method-all-exit-skilled-exception').conditions.includes('对背驰判断特别有把握'));
  assert.match(claim('079','prefer-first-center-third-buy').text,/尽量/);
  checks.push('第三买点法的时间、通道、反应级别、或触发及能力替代条件保留');
  assert.match(claim('079','fractal-small-points-one-way').text,/不一定.*辅助/);
  assert.equal(claim('080','top-fractal-exit-author-stance').ambiguity_status,'cross_lesson_scope_requires_context');
  const corrected=claim('080','sep13-wrong-level-explicit-correction');
  assert.match(corrected.text,/错把.*不构成笔.*连1分钟中枢尚未构成/);
  assert.ok(corrected.evidence.some(x=>x.pdf_page===164&&x.role==='author_commentary'));
  assert.match(claim('080','sep13-corrected-96-conditional').text,/跌破96.*不破则97/);
  const rumor=claim('080','600078-rumor-not-company-benefit');
  assert.ok(rumor.evidence.every(x=>x.role!=='reader'));
  assert.match(rumor.text,/不能保证.*公司仍可能无收益/);
  checks.push('辅助分型与强语气论述分别保留；原错图/明确更正、未来96分支及传闻不确定性可查');
  const coverage=graph.query('coverage',{}).data;
  const unit80=coverage.units.find(x=>x.id==='lesson-080');
  const note=typeof unit80.note==='string'?JSON.parse(unit80.note):unit80.note;
  assert.equal(note.explicit_later_source_resolutions[0].supporting_claim_ids[0],id('081','two-diagrams-conditional-answer'));
  assert.match(claim('081','two-diagrams-conditional-answer').text,/5＝7.*一段.*5高于7.*三段/);
  assert.match(claim('080','early-pure-center-not-overturned').text,/否认.*推翻/);
  assert.equal(coverage.semantic_completion,false);
  checks.push('80课不完整答复显式关联81课作者补全；原纯理论中枢未被时间排序覆盖');
  const requests=[
    ['search',{query:'中枢'},['search','中枢']],
    ['search',{query:'包含',limit:100},['search','包含','--limit','100']],
    ['concept',{id:'分型',limit:100},['concept','分型','--limit','100']],
    ['neighbors',{id:'特征序列',depth:1,limit:100},['neighbors','特征序列','--depth','1','--limit','100']],
    ['evidence',{id:corrected.evidence[0].id},['evidence',corrected.evidence[0].id]],
    ['page',{documentId:'volume_2.pdf',page:162},['page','--document-id','volume_2.pdf','--page','162']],
    ['search',{query:'这就如同下棋',scope:'source'},['search','这就如同下棋','--scope','source']],
    ['coverage',{},['coverage']],
  ];
  const parity=[];
  for(const [command,args,argv] of requests){
    const a=JSON.parse(JSON.stringify(graph.query(command,args)));
    assert.deepEqual(JSON.parse(JSON.stringify(desktop.query(command,args))),a);
    const cli=spawnSync(process.execPath,[resolve(agent,'bin/chan-kg.mjs'),...argv,'--kb',root],{encoding:'utf8',maxBuffer:24*1024*1024});
    assert.equal(cli.status,0,cli.stderr);assert.deepEqual(JSON.parse(cli.stdout),a);
    parity.push({command,args,cli_matches_shared:true,desktop_module_matches_shared:true});
  }
  const edge=graph.query('neighbors',{id:'特征序列',limit:200}).data.edges.find(x=>x.claim_ids.includes(sequence.id));
  assert.ok(edge);
  const possibility=graph.query('neighbors',{id:'特征序列',limit:200}).data.edges.filter(x=>
    x.claim_ids.includes(id('080','feature-sequence-three-elements-general')));
  assert.equal(possibility.length,1);assert.equal(possibility[0].type,'related');
  assert.match(claim('080','feature-sequence-three-elements-general').text,/才可能/);
  checks.push('三个元素才可能形成分型只建立关联；过强的特征序列必须有分型连接已显式修正');
  assert.deepEqual({database:sha(resolve(root,'graph.sqlite')),manifest:sha(resolve(root,'manifest.json'))},before);
  const report={graph_version:graph.metadata.graph_version,schema_version:graph.metadata.schema_version,checks,parity,
    core_sha256:sha(resolve(agent,'src/core.mjs')),desktop_core_sha256:sha(resolve(agent,'../chan-kg-desktop/vendor/core.mjs')),
    database_and_manifest_unchanged:true,pass:true,
    limits:['共享核心、桌面vendor和CLI的数据检查，不代替Electron界面或Windows打包离线验收。','同模型开发场景，非人工独立语义金标准。']};
  writeFileSync(resolve(agent,'curation/source-audit/stage-c-l078-l080-verification.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report));
} finally {graph.close();desktop.close();}
