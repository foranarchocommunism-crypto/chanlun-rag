$ErrorActionPreference = 'Stop'
$agentRoot = Split-Path -Parent $PSScriptRoot
$workspace = Split-Path -Parent $agentRoot
$deliveryReceipt=Join-Path $workspace 'deliveries\delivery-receipt.json'
if (-not (Test-Path -LiteralPath $deliveryReceipt)) { throw 'Keep temporary environments and backups until complete project delivery.' }
$delivery=Get-Content -LiteralPath $deliveryReceipt -Raw | ConvertFrom-Json
if (-not $delivery.project_delivered -or -not $delivery.required_architectures_verified) { throw 'The current user-authorized delivery gate has not passed.' }
$run = Join-Path $workspace 'validation-runs\agent-implementation-20261022'
$verification = Get-Content -LiteralPath (Join-Path $run 'm7-directory-verification.json') -Raw | ConvertFrom-Json
if (-not $verification.passed) { throw 'Keep recovery artifacts until the final package directory passes verification' }
$oldPackage = [IO.Path]::GetFullPath((Join-Path $agentRoot 'build\pre-native-runtime-package'))
$expected = Join-Path $agentRoot 'build\pre-native-runtime-package'
$actions = @()
if (Test-Path -LiteralPath $oldPackage) {
    $resolved = (Resolve-Path -LiteralPath $oldPackage).Path
    if ($resolved -ne $expected -or -not $resolved.StartsWith((Join-Path $agentRoot 'build') + [IO.Path]::DirectorySeparatorChar)) { throw 'Unexpected generated artifact deletion target' }
    if ((Get-Item -LiteralPath $resolved).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Refuse a redirected generated directory' }
    $manifest = Get-Content -LiteralPath (Join-Path $resolved 'release-manifest.json') -Raw | ConvertFrom-Json
    if ($manifest.product -ne 'chan-kg-agent' -or $manifest.product_version -ne '0.2.0') { throw 'Not the known generated pre-native package' }
    $size = (Get-ChildItem -LiteralPath $resolved -Recurse -File | Measure-Object -Property Length -Sum).Sum
    Remove-Item -LiteralPath $resolved -Recurse -Force
    $actions += [PSCustomObject]@{ action='removed_regenerable_incomplete_package'; path=$resolved; bytes=$size; basis='Created during this implementation; final package directory now passes all checks. Source and baseline backups retained.' }
}
$residue = Join-Path $run 'retained-build-residue'
New-Item -ItemType Directory -Path $residue -Force | Out-Null
$failed = Join-Path $workspace 'shared-knowledge\v0.1.0\building.failed-01.sqlite'
if (Test-Path -LiteralPath $failed) {
    $destination = [IO.Path]::GetFullPath((Join-Path $residue 'building.failed-01.sqlite'))
    if (-not $destination.StartsWith($run + [IO.Path]::DirectorySeparatorChar) -or (Test-Path -LiteralPath $destination)) { throw 'Unexpected retained residue path' }
    $hash = (Get-FileHash -LiteralPath $failed -Algorithm SHA256).Hash.ToLowerInvariant()
    Move-Item -LiteralPath $failed -Destination $destination
    $actions += [PSCustomObject]@{ action='retained_failed_build_outside_canonical_package'; source=$failed; destination=$destination; sha256=$hash; basis='Known failed-build residue; no active code references found; not graph.sqlite' }
}
$failedIndex = Join-Path $agentRoot 'build\failed-index-20261022-column-count'
if (Test-Path -LiteralPath $failedIndex) {
    $resolved = (Resolve-Path -LiteralPath $failedIndex).Path
    $destination = Join-Path $residue 'failed-index-20261022-column-count'
    if (-not $resolved.StartsWith((Join-Path $agentRoot 'build') + [IO.Path]::DirectorySeparatorChar) -or (Test-Path -LiteralPath $destination)) { throw 'Unexpected failed-index path' }
    Move-Item -LiteralPath $resolved -Destination $destination
    $actions += [PSCustomObject]@{ action='retained_failed_derived_index'; source=$resolved; destination=$destination }
}
[PSCustomObject]@{ completed_at=(Get-Date).ToUniversalTime().ToString('o'); actions=@($actions); old_desktop_archive='User moved to Recycle Bin; not restored'; preserved=@('Canonical graph.sqlite and fixed PDFs','Pre-implementation source/knowledge backups','Original knowledge-only delivery','Version-bound development snapshots still used by evaluation','Curation/source-research records','Fixed local models and runtime production dependencies'); runtime_exclusions=@('Desktop app','Full curation/source project','Original test/build directories','Development software installers') } | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath (Join-Path $run 'm7-directory-cleanup.json') -Encoding utf8NoBOM
Write-Output ('Cleanup actions: ' + $actions.Count)
