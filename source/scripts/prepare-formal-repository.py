"""Create a standalone local release repository; do not modify older deliveries."""
from pathlib import Path
import json
import shutil

app = Path(__file__).resolve().parents[1]
target = Path.home() / 'Desktop' / '缠论知识检索正式版'
assert not target.exists(), 'Preserve existing repository; choose an explicit new location'
target.mkdir()
(target / '发布状态.json').write_text(json.dumps({'status': 'preparing', 'version': '0.4.0', 'ready_to_use': False}, ensure_ascii=False, indent=2), encoding='utf-8')
source = target / 'source'
source.mkdir()
for name in ['src', 'bin', 'contracts', 'profiles', 'policies', 'test', 'licenses']:
    shutil.copytree(app / name, source / name)
for name in ['package.json', 'package-lock.json', 'README.md', 'AGENT_GUIDE.md', 'AGENTS.md', 'chan-kg-mcp.cmd']:
    if (app / name).exists(): shutil.copyfile(app / name, source / name)
for name in ['docs', 'scripts', 'evaluation', 'indexes', 'models', 'node_modules', 'build/native-runtime']:
    (source / name).mkdir(parents=True, exist_ok=True)
scripts = ['validate.mjs', 'package-portable.mjs', 'verify-portable.mjs', 'deny-network.mjs', 'doctor.ps1', 'build-index.mjs', 'build-vectors.mjs',
           'audit-fixed-knowledge.mjs', 'build-fixed-release-gates.mjs', 'evaluate-fixed-corpus.mjs', 'prepare-formal-repository.py']
for name in scripts: shutil.copyfile(app / 'scripts' / name, source / 'scripts' / name)
shutil.copytree(app / 'scripts/lib', source / 'scripts/lib', dirs_exist_ok=True)
for name in ['portable-readme.md', 'fixed-release.md', 'MAINTENANCE.md', 'COMPATIBILITY.md', 'graph-v2.md', 'retrieval-contract.md', 'agent-answer-examples.md']:
    shutil.copyfile(app / 'docs' / name, source / 'docs' / name)
shutil.copytree(app / 'evaluation/fixed-corpus', source / 'evaluation/fixed-corpus')
shutil.copytree(app / 'indexes/static-0.4.0', source / 'indexes/static-0.4.0')
shutil.copyfile(app / 'indexes/active.json', source / 'indexes/active.json')
shutil.copytree(app / 'build/native-runtime', source / 'build/native-runtime', dirs_exist_ok=True)
shutil.copytree(app.parent / 'shared-knowledge/v0.1.0', target / 'shared-knowledge/v0.1.0')
for name in ['release', 'archives', '验收记录', 'tools']: (target / name).mkdir()
(target / '.gitignore').write_text('''source/node_modules/
source/models/
source/build/
release/
archives/
*.tmp
__pycache__/
''', encoding='utf-8')
(target / 'README.md').write_text('''# 缠论知识检索正式版 0.4.0

日常使用 release 目录里的运行包，或从本目录执行 chan-kg.cmd。开始前可运行“验证正式版.cmd”。具体命令见“开始使用.md”。

知识库已经固定，后续不再新增。软件保留已复核、待核、拒绝和歧义状态；正式发布不等于所有知识都已经完成语义复核。

## 目录

- release：可直接运行的 Windows x64 版本，自带 Node、模型、知识和索引。
- archives：同版本 ZIP 及 SHA-256，可用于重新解压恢复。
- source：本次发布源码、固定依赖、模型、测试和构建工具。
- shared-knowledge：源码测试使用的冻结知识底本，与运行包数据库内容相同。
- 验收记录：测试、知识校验、Graph 对照、故障恢复和全新解压运行回执。

这是本地 Git 发布仓库。Git 记录源码、固定知识和验收记录；运行包、模型依赖副本和 ZIP 保存在同一目录中，由文件哈希清单及发布回执绑定，不重复写入 Git 历史。

## 修复与使用边界

快照准入拒绝 WAL 和活动写入，构建中断可以通过已确认检查点恢复，发布清单不会留下半截正式 JSON。Graph 失败按请求设置明确报错或受控降级；详细说明见 source/docs/fixed-release.md。

Graph 保留有来源的定义定位和关系追查。二跳自然竞争，没有特殊通道和最低名额。整体收益以验收记录中的实际对照为准。

运行本目录的 tools/dev.ps1 test 可用随包 Node 执行源码测试，无需全局安装。检查发布状态及确切提交、ZIP 哈希，读取“发布状态.json”和“验收记录/正式交付回执.json”。
''', encoding='utf-8')
(target / '开始使用.md').write_text('''# 开始使用

在此目录打开 PowerShell，执行：

```powershell
.\chan-kg.cmd status
.\chan-kg.cmd retrieve "中枢是什么，成立需要什么条件？" --limit 5
.\chan-kg.cmd claim upper-l017-center-definition
.\chan-kg.cmd retrieve "第77课线段称呼与确认时点" --mode research
.\chan-kg.cmd retrieve "基本上可以这样理解" --mode source
.\chan-kg.cmd retrieve "背驰与买卖点有哪些关系？" --profile hybrid-graph-v2-rerank --allow-degraded
.\chan-kg.cmd retrieve "中枢的成立条件" --trace
.\验证正式版.cmd
```

默认返回已复核知识。research 单列待核线索；source 用于核对原话与发言者。结果中的条件、例外和歧义必须保留，相关性分数不表示事实概率。

为 Agent 配置 MCP 时，使用本目录的 chan-kg-mcp.cmd；配置示例见 MCP配置示例.json。目录移动后相应修改客户端中的绝对路径。

发现文件损坏或不匹配时，从 archives 的正式 ZIP 解压一套新目录并运行 verify.cmd，再让 Agent 连接新目录。每次使用整套文件，不逐个混换数据库或模型。
''', encoding='utf-8')
product = 'chan-kg-agent-0.4.0-windows-x64'
for launcher, entry in [('chan-kg.cmd', 'chan-kg.cmd'), ('chan-kg-mcp.cmd', 'chan-kg-mcp.cmd'), ('验证正式版.cmd', 'verify.cmd')]:
    (target / launcher).write_bytes((f'@echo off\r\ncall "%~dp0release\\{product}\\{entry}" %*\r\nexit /b %errorlevel%\r\n').encode('utf-8'))
(target / 'MCP配置示例.json').write_text(json.dumps({'mcpServers': {'chan-kg': {'command': r'C:\Windows\System32\cmd.exe', 'args': ['/d', '/s', '/c', 'call', str(target / 'chan-kg-mcp.cmd')]}}}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
(target / 'tools/dev.ps1').write_text('''param([ValidateSet('test','validate','status')][string]$Action='test')
$ErrorActionPreference='Stop'
$repoRoot=Split-Path -Parent $PSScriptRoot
$nodePath=Join-Path $repoRoot 'release/chan-kg-agent-0.4.0-windows-x64/runtime/x64/node.exe'
Push-Location (Join-Path $repoRoot 'source')
try {
  if ($Action -eq 'test') { & $nodePath --test --test-reporter=tap test/*.test.mjs }
  elseif ($Action -eq 'validate') { & $nodePath scripts/validate.mjs }
  else { & $nodePath bin/chan-kg.mjs status }
  if ($LASTEXITCODE -ne 0) { throw "Command failed: $LASTEXITCODE" }
} finally { Pop-Location }
''', encoding='utf-8-sig')
print(json.dumps({'repository': str(target), 'source_prepared': True, 'artifact_status': 'awaiting_verified_archive'}, ensure_ascii=False))
