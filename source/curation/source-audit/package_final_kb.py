"""Create and hash-check the knowledge-only directory/archive, never a software build."""
import hashlib,json,shutil,sqlite3,subprocess,sys,zipfile
from datetime import datetime,timezone
from pathlib import Path
AGENT=Path(__file__).resolve().parents[2];WORK=AGENT.parent;KB=WORK/'shared-knowledge/v0.1.0';AUDIT=Path(__file__).resolve().parent
VERSION='0.1.0-review-307029129712';NAME='chan-knowledge-20261022-307029129712'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def copy(source,target):target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
def main():
 quality=read(AUDIT/'stage-h-final-kb-quality.json');assert quality['graph_version']==VERSION and quality['quality_ready_for_knowledge_delivery']
 before=dict(database=sha(KB/'graph.sqlite'),manifest=sha(KB/'manifest.json'));assert before==quality['final_sha256']
 destination=WORK/'deliveries';destination.mkdir(exist_ok=True);out=destination/NAME;archive=destination/(NAME+'.zip');receipt=destination/(NAME+'.delivery-receipt.json')
 assert not out.exists() and not archive.exists() and not receipt.exists();out.mkdir()
 for name in ['graph.sqlite','manifest.json']:copy(KB/name,out/name)
 for name in ['sources','geometry','provenance','exports']:shutil.copytree(KB/name,out/name)
 assert sha(out/'graph.sqlite')==before['database'] and sha(out/'manifest.json')==before['manifest']
 # Preserve the existing construction record tree, excluding ignored build files,
 # runtimes, failed DBs and software launch/package outputs.
 tracked=subprocess.run(['git','-c','core.quotepath=false','ls-files','-z','--','curation','contracts','tools','evaluation'],cwd=AGENT,text=True,encoding='utf-8',check=True,capture_output=True).stdout.split('\0')
 tracked=[p for p in tracked if (AGENT/p).is_file()]
 assert len(tracked)>200 and 'curation/source-audit/stage-h-final-kb-quality.json' in tracked
 for name in tracked:copy(AGENT/name,out/'build-records'/name)
 revision=subprocess.run(['git','rev-parse','HEAD'],cwd=AGENT,text=True,encoding='utf-8',check=True,capture_output=True).stdout.strip()
 for source,target in [
  ('stage-h-final-kb-quality.json','final-quality.json'),('stage-h-l064-checkpoint.json','all108-lesson-coverage.json'),
  ('stage-h-final-figure-log-completion.json','all528-figure-records.json'),('stage-h-final-reviewed-ambiguities.jsonl','reviewed-ambiguities.jsonl'),
  ('stage-h-final-retrieval-snapshot.json','retrieval-snapshot.json')]:copy(AUDIT/source,out/'audit'/target)
 copy(AGENT/'evaluation/stage-h-final-baselines-307029129712.results.json',out/'audit/natural-question-retrieval.results.json')
 copy(AGENT/'evaluation/stage-g-development-current.results.json',out/'audit/frozen-plan-regression.results.json')
 copy(AGENT/'curation/delivery-scope.json',out/'audit/delivery-scope.json')
 (out/'build-records/README.md').write_text('''# 构建记录

这里保存逐课命题批次、逐段台账、图审记录、待核及局部补证、来源修订、Schema和构建工具。文件中的旧版本、原工作区绝对路径和当时未完成项属于历史记录；当前交付状态以根目录README、delivery-manifest.json、audit/final-quality.json及压缩包旁的delivery-receipt.json为准。

上下册pending.jsonl是追加式历史日志，须与partial-resolutions及source-resolutions一同读，不能把每条旧待核都算作当前来源错误。SQLite中的2611个pending是未进入默认集合的原始候选，可能与后来细分命题重叠，不是2611个独立知识缺口。

final-retrieval-tool-snapshot保存本次实际使用的离线评测工具、查询模块和240题原始开发题；仅供复算和审计，无捆绑运行时，无新增应用产品。复算时从交付知识库重新创建快照，原实验快照的物理SQLite哈希可能不同，但图谱内容版本相同。
''',encoding='utf-8')
 (out/'README.md').write_text('''# 缠中说禅知识库交付说明

交付范围是共享知识库。固定版本：`0.1.0-review-307029129712`，Schema：`1.1.0`。两册907页、108课正文和可明确识别的作者技术答疑已逐来源单元处理；108课逐段台账已核对闭合。两处汇编后记/学习大纲单独保留为整理者身份未核的附录。

| 内容 | 数量 |
|---|---:|
| 已复核、默认知识命题 | 3369 |
| 已复核证据引文 | 4584 |
| 概念 / 有命题支撑的关系 | 318 / 692 |
| 原文段落（含附录） | 9650 |
| 配图及查看记录 | 528 |
| 原文明说 / 整理推论 | 3366 / 3 |

`graph.sqlite`是唯一知识事实源。`exports/claims.jsonl`、`concepts.jsonl`、`relations.jsonl`、`reviewed-knowledge.md`和`coverage.json`均来自同一版本。命题包含条件、例外、级别与完成限制、原文明说/推论、复核和歧义状态；引文可追溯到来源身份、实际/印刷页、字符与坐标。原PDF在sources，页面/字符几何在geometry，43/57课夹注拆分的原始行和映射沿革在provenance。

默认使用已复核知识。473条已复核命题仍保留显式歧义；2611个候选未进入默认知识，另有28个已拒绝候选。已复核表示出处、身份、转述和条件经过核对，不表示作者全部理论、历史收益和解释分歧已经证实或统一。265张图的原始作者/原发仍未核，263张明确为后加图；这与528张图均有查看记录是不同的判断。

## 先看哪些文件

- 阅读：`exports/reviewed-knowledge.md`。
- 结构化使用：`exports/claims.jsonl`，需要完整原文、候选或关系时读`graph.sqlite`。
- 覆盖：`audit/all108-lesson-coverage.json`。
- 质量与已知边界：`audit/final-quality.json`。
- 仍有歧义的已复核命题：`audit/reviewed-ambiguities.jsonl`。
- 完整逐课台账、图审、来源修复、待核与补证历史：`build-records/curation`。

## 检索评测与限制

240道冻结开发题的既定取证计划通过239道，来源身份核对240道通过。原“重合”查询前20条未召回指定第21课命题的问题仍保留，未改题或改金标准。

另用这240题的原始完整问题文字、同一冻结知识库、每通道100个候选段落，实际比较了下列方案。这里的Recall只针对已经标注的证据段落；未标注结果不自动算无关。

| 方案 | Recall@10 | Recall@20 |
|---|---:|---:|
| 原文关键词（离线BM25） | 43.35% | 51.23% |
| 已复核结构化知识关键词 | 72.00% | 81.89% |
| 原文+结构化离线融合 | 67.38% | 79.60% |
| 现有搜索命令直接输入整句问题 | 6.96% | 12.53% |

现有搜索工具直接接收整句自然问题时召回较弱，适合拆成概念、关键词并核对原文证据。离线融合只是评测方法，没有添加到软件中。纯向量方案未实现。开发题由模型复核，无人工金标准或独立留出集；未给生成回答打分，未声称反幻觉、冲突处理、消融或完整G类评测全部通过。原始结果与方法、预算、延迟及局限在audit的两份results.json中。

知识来源限定这两册汇编，未宣称与原博客逐字校对；位图作者、历史账户收益、实际成交和当时外部金融/法律事实未获额外认证。原文编号、符号、价格和术语有疑点时保留原字并列明边界。

## 校验与恢复

`SHA256SUMS.txt`覆盖目录内除其自身以外的全部文件。压缩包旁的`delivery-receipt.json`记载压缩包SHA-256、清单哈希、文件数，以及对实际复制件/压缩包逐文件校验结果。原始数据和构建记录保留，可按provenance及批次记录追溯；历史构建脚本可能含一次性版本保护，不要对已发布库直接重复运行。

本次没有交付新的Agent软件访问产品或Windows应用；构建记录中的现有校验/评测代码只用于知识库审计。`semantic_completion=false`等历史元数据表示未将全部候选和解释分歧宣布为确认知识，交付的全书处理完成状态由delivery-manifest与实际交付回执记录。
''',encoding='utf-8')
 delivery=dict(delivery_scope='shared_knowledge_base_only',graph_version=VERSION,schema_version='1.1.0',construction_scope_processed=True,all_explanations_confirmed=False,reviewed_claims=3369,reviewed_evidence=4584,concepts=318,relations=692,lesson_reading_and_disposition_complete=108,pdf_pages=907,figures_with_viewing_records=528,known_limits='README.md and audit/final-quality.json',canonical_kb_sha256=before,construction_records_git_revision=revision,construction_record_files=len(tracked),software_deliverables_excluded=True,external_delivery_receipt=receipt.name,checksum_manifest='SHA256SUMS.txt')
 write(out/'delivery-manifest.json',delivery)
 # Validate the actual delivered copy (including its own PDFs and geometry).
 checked=subprocess.run(['node',str(AGENT/'scripts/validate.mjs'),str(out)],cwd=AGENT,text=True,encoding='utf-8',capture_output=True)
 assert checked.returncode==0,checked.stderr or checked.stdout
 validation=json.loads(checked.stdout);assert validation['pass'] and validation['graph_version']==VERSION and validation['reviewed_claims']==3369 and not validation['errors']
 write(out/'audit/delivery-copy-validation.json',validation)
 assert before==dict(database=sha(KB/'graph.sqlite'),manifest=sha(KB/'manifest.json'))
 files=sorted(p for p in out.rglob('*') if p.is_file());hashes={p.relative_to(out).as_posix():sha(p) for p in files}
 checksum=out/'SHA256SUMS.txt';checksum.write_text(''.join(h+'  '+p+'\n' for p,h in hashes.items()),encoding='utf-8');hashes[checksum.name]=sha(checksum)
 assert all(sha(out/name)==h for name,h in hashes.items())
 with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
  for name in sorted(hashes):z.write(out/name,NAME+'/'+name)
 with zipfile.ZipFile(archive) as z:
  assert set(z.namelist())=={NAME+'/'+name for name in hashes}
  for name,expected in hashes.items():
   h=hashlib.sha256()
   with z.open(NAME+'/'+name) as f:
    for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
   assert h.hexdigest()==expected,name
 assert before==dict(database=sha(KB/'graph.sqlite'),manifest=sha(KB/'manifest.json'))
 result=dict(delivery_verified_at=datetime.now(timezone.utc).isoformat(),graph_version=VERSION,delivery_scope='shared_knowledge_base_only',directory=str(out),archive=str(archive),archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,checksum_manifest_sha256=sha(checksum),files_including_checksum=len(hashes),uncompressed_file_bytes=sum((out/name).stat().st_size for name in hashes),all_directory_file_hashes_checked=True,all_archive_file_hashes_and_crc_checked=True,actual_delivery_copy_validation=validation,canonical_kb_unchanged=True,canonical_kb_sha256=before,construction_records_git_revision=revision,knowledge_delivery_complete=True,all_explanations_confirmed=False)
 write(receipt,result);write(AUDIT/'stage-h-final-kb-delivery-receipt.json',result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');sys.stderr.reconfigure(encoding='utf-8');main()
