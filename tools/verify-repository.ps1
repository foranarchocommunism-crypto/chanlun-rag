param()
$ErrorActionPreference = 'Stop'
$repoRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$listPath = Join-Path $repoRoot '仓库文件清单.sha256'
if (-not (Test-Path -LiteralPath $listPath)) { throw 'Repository checksum list is not ready.' }
$count = 0
foreach ($line in [IO.File]::ReadLines($listPath, [Text.Encoding]::UTF8)) {
    if ($line -notmatch '^[0-9a-f]{64}  .+$') { throw 'Invalid checksum entry.' }
    $expected = $line.Substring(0, 64)
    $filePath = [IO.Path]::GetFullPath((Join-Path $repoRoot $line.Substring(66)))
    if (-not $filePath.StartsWith($repoRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Checksum path escaped repository.' }
    $stream = [IO.File]::OpenRead($filePath)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try { $actual = [BitConverter]::ToString($algorithm.ComputeHash($stream)).Replace('-', '').ToLowerInvariant() }
    finally { $algorithm.Dispose(); $stream.Dispose() }
    if ($actual -ne $expected) { throw "Checksum mismatch: $filePath" }
    $count++
}
Write-Output "Verified $count repository files."
