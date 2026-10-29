param([ValidateSet('test','validate','status')][string]$Action='test')
$ErrorActionPreference='Stop'
$repoRoot=Split-Path -Parent $PSScriptRoot
$nodePath=Join-Path $repoRoot 'release/chanlun-rag-0.4.2-windows-x64/runtime/x64/node.exe'
Push-Location (Join-Path $repoRoot 'source')
try {
  if ($Action -eq 'test') { & $nodePath --test --test-reporter=tap test/*.test.mjs }
  elseif ($Action -eq 'validate') { & $nodePath scripts/validate.mjs }
  else { & $nodePath bin/chan-kg.mjs status }
  if ($LASTEXITCODE -ne 0) { throw "Command failed: $LASTEXITCODE" }
} finally { Pop-Location }
