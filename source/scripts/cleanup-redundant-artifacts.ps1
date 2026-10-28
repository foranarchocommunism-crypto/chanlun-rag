$ErrorActionPreference='Stop'
$workspace=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$run=Join-Path $workspace 'validation-runs\x64-delivery-20261023'
$native=Get-Content -LiteralPath (Join-Path $run 'native-guest-receipt.json') -Raw | ConvertFrom-Json
$release=Get-Content -LiteralPath (Join-Path $run 'zip-build.json') -Raw | ConvertFrom-Json
if (-not $native.passed -or $native.zip_sha256 -ne $release.sha256) { throw 'Final actual x64 ZIP must pass before pruning previous artifacts.' }
$proof=Get-Content -LiteralPath (Join-Path $run 'verified-duplicate-artifacts.json') -Raw | ConvertFrom-Json
$actions=@()
$metadata=Join-Path $run 'superseded-delivery-metadata'
New-Item -ItemType Directory -Path $metadata -Force | Out-Null
function Remove-ExactOwnedTree([string]$Target,[string]$Expected) {
  $targetPath=[IO.Path]::GetFullPath($Target).TrimEnd('\')
  if ($targetPath -cne [IO.Path]::GetFullPath($Expected).TrimEnd('\') -or -not $targetPath.StartsWith($workspace+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe generated-directory deletion target.' }
  if (-not (Test-Path -LiteralPath $targetPath)) { return }
  if ((Get-Item -LiteralPath $targetPath).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Refuse redirected artifact directory.' }
  if (@(Get-ChildItem -LiteralPath $targetPath -Recurse -Force -Attributes ReparsePoint).Count) { throw 'Refuse redirected artifact contents.' }
  $files=@(Get-ChildItem -LiteralPath $targetPath -Recurse -File -Force)
  $bytes=($files | Measure-Object Length -Sum).Sum
  Remove-Item -LiteralPath $targetPath -Recurse -Force
  $script:actions += [pscustomobject]@{action='removed_redundant_or_cancelled_generated_tree';path=$targetPath;files=$files.Count;bytes=$bytes}
}
$names=@('chan-kg-agent-0.2.0-307029129712','chan-kg-agent-0.2.1-307029129712','chan-kg-agent-0.3.0-307029129712','chan-knowledge-20261022-307029129712')
$allowed=@($names | ForEach-Object { Join-Path $workspace ('deliveries\'+$_) })
$allowed += Join-Path $workspace 'validation-runs\移位验收 空格路径\chan-kg-agent-0.2.0-307029129712'
foreach ($entry in $proof.verified) {
  $absolute=[IO.Path]::GetFullPath($entry.directory)
  if ($absolute -notin $allowed -or -not $entry.all_file_sha256_match_archive_manifest) { throw 'Unapproved duplicate audit entry.' }
  Remove-ExactOwnedTree $absolute $absolute
}
foreach ($name in @('chan-kg-agent-0.2.0-307029129712','chan-kg-agent-0.3.0-307029129712')) {
  $archive=Join-Path $workspace ('deliveries\'+$name+'.zip')
  $entry=@($proof.verified | Where-Object archive -eq $archive)[0]
  if (-not $entry -or (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.archive_sha256) { throw 'Superseded archive identity changed.' }
  $bytes=(Get-Item -LiteralPath $archive).Length
  Remove-Item -LiteralPath $archive -Force
  $actions += [pscustomobject]@{action='removed_superseded_archive';path=$archive;bytes=$bytes;sha256=$entry.archive_sha256}
}
foreach ($name in $names) {
  foreach ($file in @(Get-ChildItem -LiteralPath (Join-Path $workspace 'deliveries') -File | Where-Object { $_.Name -like ($name+'*') -and $_.Extension -in @('.json','.sha256') })) {
    if ($name -eq 'chan-knowledge-20261022-307029129712' -or $file.Name -eq 'chan-kg-agent-0.2.1-307029129712.zip.sha256') { continue }
    $destination=[IO.Path]::GetFullPath((Join-Path $metadata $file.Name))
    if (-not $destination.StartsWith($metadata+'\') -or (Test-Path -LiteralPath $destination)) { throw 'Metadata destination is not a fresh owned path.' }
    Move-Item -LiteralPath $file.FullName -Destination $destination
  }
}
$superseded=Join-Path $workspace 'validation-runs\windows-compatibility-20261023\superseded-candidate'
if (Test-Path -LiteralPath $superseded) {
  $oldZip=Join-Path $superseded 'chan-kg-agent-0.2.1-307029129712.zip'
  if ((Get-FileHash -LiteralPath $oldZip -Algorithm SHA256).Hash.ToLowerInvariant() -ne '8df2bf9b2d38fbe42b6c03bc844eeb5aa450ab1d86193a8da7ae7cd7bbefe894') { throw 'Cancelled candidate changed.' }
  foreach ($file in @(Get-ChildItem -LiteralPath $superseded -File | Where-Object Extension -ne '.zip')) { Copy-Item -LiteralPath $file.FullName -Destination (Join-Path $metadata ('cancelled-'+$file.Name)) }
  Remove-ExactOwnedTree $superseded (Join-Path $workspace 'validation-runs\windows-compatibility-20261023\superseded-candidate')
}
$baseline=Join-Path $workspace 'validation-runs\agent-implementation-20261022\baseline-knowledge'
if (Test-Path -LiteralPath $baseline) {
  $files=@(Get-ChildItem -LiteralPath $baseline -File)
  if ($files.Count -ne 2) { throw 'Baseline knowledge contains unique files.' }
  foreach ($file in $files) {
    $canonical=Join-Path $workspace ('shared-knowledge\v0.1.0\'+$file.Name)
    if ((Get-FileHash -LiteralPath $file.FullName).Hash -ne (Get-FileHash -LiteralPath $canonical).Hash) { throw 'Baseline knowledge differs from canonical.' }
  }
  Remove-ExactOwnedTree $baseline (Join-Path $workspace 'validation-runs\agent-implementation-20261022\baseline-knowledge')
}
$arm=Join-Path $workspace 'chan-kg-agent\build\portable-platforms\arm64'
if (Test-Path -LiteralPath $arm) {
  $preserved=Join-Path $metadata 'cancelled-ARM64-static-receipts'
  New-Item -ItemType Directory -Path $preserved -Force | Out-Null
  Get-ChildItem -LiteralPath $arm -File -Filter '*.json' | Copy-Item -Destination $preserved
  Remove-ExactOwnedTree $arm (Join-Path $workspace 'chan-kg-agent\build\portable-platforms\arm64')
}
Remove-ExactOwnedTree (Join-Path $workspace 'validation-runs\windows-compatibility-20261023\launcher probe 中文 空格') (Join-Path $workspace 'validation-runs\windows-compatibility-20261023\launcher probe 中文 空格')
Remove-ExactOwnedTree (Join-Path $workspace 'chan-kg-agent\scripts\__pycache__') (Join-Path $workspace 'chan-kg-agent\scripts\__pycache__')
$receipt=[ordered]@{passed=$true;finished_at=(Get-Date -Format o);actions=$actions;removed_file_bytes=($actions | Measure-Object bytes -Sum).Sum;retained=@('Current final x64 directory and ZIP','One previous usable x64 0.2.1 ZIP for rollback','Knowledge-only ZIP with unique historical audit files','Pre-implementation source backup and curation records','Canonical graph and fixed PDFs','Frozen evaluation, active models and source maintenance dependencies');recycle_bin='Not accessed or emptied'}
$receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $run 'backup-cleanup.json') -Encoding utf8
$receipt | ConvertTo-Json -Depth 8
