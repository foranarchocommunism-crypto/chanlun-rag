$ErrorActionPreference = 'Stop'
$agentRoot = Split-Path -Parent $PSScriptRoot
$target = Join-Path $agentRoot 'build\native-runtime'
New-Item -ItemType Directory -Path $target -Force | Out-Null
$names = @('msvcp140.dll','msvcp140_1.dll','msvcp140_atomic_wait.dll','vcruntime140.dll','vcruntime140_1.dll')
$assets = foreach ($name in $names) {
    $source = Join-Path "$env:SystemRoot\System32" $name
    $signature = Get-AuthenticodeSignature -LiteralPath $source
    if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notlike '*Microsoft*') { throw "Invalid publisher signature: $name" }
    Copy-Item -LiteralPath $source -Destination (Join-Path $target $name) -Force
    [PSCustomObject]@{ file=$name; source=$source; version=(Get-Item -LiteralPath $source).VersionInfo.FileVersion; sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $source).Hash.ToLowerInvariant(); signature='Valid'; publisher=$signature.SignerCertificate.Subject }
}
[PSCustomObject]@{ collected_at=(Get-Date).ToUniversalTime().ToString('o'); purpose='Application-local native dependencies for the local portable package; no system installation or modification'; deployment_reference='https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files'; license_reference='https://visualstudio.microsoft.com/license-terms/vs2022-cruntime/'; assets=@($assets) } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $target 'native-runtime-manifest.json') -Encoding utf8NoBOM
Write-Output ('Collected application-local DLLs: ' + $assets.Count)
