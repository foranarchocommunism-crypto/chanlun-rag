"""Write the concrete release receipt only after both artifact executions pass."""
from pathlib import Path
import json
import hashlib
import subprocess
from datetime import datetime, timezone

repo = Path.home() / 'Desktop' / '缠论知识检索正式版'
records = repo / '验收记录'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
def digest(path):
    with path.open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()
stage = read(records / '打包目录运行验证.json')
fresh = read(records / '全新解压运行验证.json')
archive = read(records / 'ZIP与全新解压.json')
knowledge = read(records / 'knowledge-integrity.json')
metrics = read(records / 'graph-value-final/metrics.json')
behavior = read(records / 'definition-and-fallback.json')
gates = read(records / 'gates.json')
assert stage['passed'] and fresh['passed'] and knowledge['pass'] and gates['passed']
product = Path(archive['extracted_path'])
assert Path(fresh['product_root']).resolve() == product.resolve()
assert digest(Path(archive['archive'])) == archive['archive_sha256']
source_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip()
manifest = read(product / 'release-manifest.json')
assert manifest['code_commit'] == source_commit
code = {p.name: digest(p) for p in (repo / 'source/src').glob('*.mjs')}
assert code == metrics['inputs']['code']
assert all(digest(product / 'app/src' / n) == h for n, h in code.items())
canonical = digest(product / 'knowledge/graph.sqlite')
assert canonical == knowledge['canonical_sha256'] == digest(repo / 'shared-knowledge/v0.1.0/graph.sqlite')
tap = (records / '正式仓库源码测试.tap').read_text(encoding='utf-8-sig')
assert '# tests 117' in tap and '# pass 117' in tap and '# fail 0' in tap and '# skipped 0' in tap
receipt = {
    'client_release_date': '2026-10-26', 'generated_at_host_utc': datetime.now(timezone.utc).isoformat(),
    'passed': True, 'product_version': '0.4.0', 'repository': str(repo), 'source_commit': source_commit,
    'release': str(product), 'archive': archive, 'canonical_sha256': canonical, 'source_code_sha256': code,
    'tests': {'passed': 117, 'failed': 0, 'skipped': 0, 'rerun_from_standalone_repository': True},
    'engineering': {'static_snapshot_admission': True, 'WAL_rejected': True, 'read_session_blocks_commit': True,
                    'checkpoint_recovery': True, 'partial_manifest_recovery': True, 'projection_recovery': True,
                    'transient_windows_rename_retry': True, 'graph_fallback': True, 'queue_capacity_and_deadline': True,
                    'effective_request_fingerprints_and_trace': True},
    'artifact': {'staging_execution_passed': True, 'fresh_extraction_execution_passed': True,
                 'interface_equality': ['CLI', 'JavaScript', 'MCP stdio'], 'uses_bundled_runtime': True,
                 'network_scope': fresh['network_policy'], 'independent_clean_host': False},
    'knowledge': {'fixed_corpus': True, 'updates_planned': False, 'content_unchanged': True,
                  'review_states': knowledge['statuses'], 'independent_full_semantic_review_claimed': False},
    'graph': {'value_metrics': metrics['summary'], 'comparisons': metrics['comparisons'],
              'functional_definition_probe': [{k: x[k] for k in ['name', 'expected_definition_rank']} for x in behavior['definition_comparison']],
              'independent_semantic_acceptance': False, 'overall_quality_gain_claimed': False,
              'two_hop_special_channels_or_floors': False},
    'evidence': {str(p.relative_to(repo)): digest(p) for p in [records / 'gates.json', records / 'knowledge-integrity.json', records / 'tests-final.tap', records / '正式仓库源码测试.tap', records / '打包目录运行验证.json', records / '全新解压运行验证.json', records / 'graph-value-final/metrics.json', records / 'definition-and-fallback.json']},
}
(records / '正式交付回执.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
summary = metrics['summary']
rows = '\n'.join(f'| {name} | {value["recall"]*100:.3f}% | {value["complete_fraction"]*100:.3f}% |' for name, value in summary.items())
(records / 'Graph价值验证.md').write_text(f'''# Graph 价值验证

本次使用当前正式代码、本地模型和固定 240 道已使用过的开发题，比较默认策略 D、文本 T40/T48，以及新准入方案 G1/G2。成绩只统计主结果中的原文证据，不把辅助路径重复计分。

| 方案 | Recall@20 | 原文齐全比例 |
|---|---:|---:|
{rows}

逐题差异见 graph-value-final/metrics.json 和 progress.json。它们是开发对照，不是独立人工语义验收。相同顺序的 4 条重排批次复用结果，不用这些计时报告性能。

“中枢是什么，成立需要什么条件”的既有功能回归中：默认策略和新图准入都把 upper-l017-center-definition 放在第 1；文本 40、文本 48 的前 5 条都没有它。这证明定义定位在这一具体查询上的作用，没有被扩大成所有问题都有提升。

保留有来源的定义定位和关系导航；通用图扩展的整体独特收益仍未确立。二跳自然竞争，不增加专项通道、名额或下限。遍历发生、候选进入主结果、完整证据链返回和答案正确是不同事实。
''', encoding='utf-8')
(records / '工程修复与正式发布.md').write_text(f'''# 0.4.0 正式发布记录

正式仓库位于 {repo}。源码提交 {source_commit}，正式标签为 v0.4.0。软件、固定知识、向量、模型和运行时已经成套发布。

## 已完成

- 固定快照拒绝 WAL、共享内存和写入日志，会话持有只读事务并校验文件身份。
- 投影在独立目录完成后发布；向量用前缀哈希恢复已确认检查点；清单完整写入后替换；Windows 短暂占用时有限重试。
- 新旧 Graph 配置均有实体触发和资源限制、严格报错或受控降级；队列容量和等待时间有上限。
- 生效请求、内容指纹、排队时间、最终结果来源始终记录；trace 可追加各阶段排名和原始理由。
- 知识内容未改，已复核、待核和歧义继续保留。不存在新增知识维护任务。

## 验收

117 项自动测试全部通过，并在正式仓库源码中重新运行。知识库完整性、两册 PDF 哈希及引用位置检查通过。真实构建脚本在三个中断位置终止后重试成功；已确认向量损坏时明确拒绝恢复。

打包目录与全新 ZIP 解压件均用包内 Node 完成 CLI、JavaScript 和真实 MCP stdio 校验，使用隔离 PATH 并关闭 Node 网络调用。实际环境是当前 Windows x64 主机，没有把本次验证写成独立干净机器或真实断电验收。

ZIP SHA-256：{archive['archive_sha256']}。

Graph 效果另见 Graph价值验证.md；本次工程发布不宣称全库关系已经重新人工复核，也不宣称二跳带来总体收益。
''', encoding='utf-8')
(repo / '发布状态.json').write_text(json.dumps({'status': 'released', 'version': '0.4.0', 'ready_to_use': True,
    'source_commit': source_commit, 'release_tag': 'v0.4.0', 'archive_sha256': archive['archive_sha256'],
    'receipt': '验收记录/正式交付回执.json'}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
# Exclude only generated staging/cache and Git internals. All delivered files, including ZIP and dependencies, are bound.
files = []
for path in repo.rglob('*'):
    if not path.is_file(): continue
    rel = path.relative_to(repo)
    if rel.parts[0] == '.git' or rel.parts[:2] == ('source', 'build') or path.name == '仓库文件清单.sha256': continue
    files.append(path)
(repo / '仓库文件清单.sha256').write_text(''.join(f'{digest(p)}  {p.relative_to(repo).as_posix()}\n' for p in sorted(files)), encoding='utf-8')
print(json.dumps({'passed': True, 'source_commit': source_commit, 'archive_sha256': archive['archive_sha256'], 'bound_files': len(files)}), flush=True)
