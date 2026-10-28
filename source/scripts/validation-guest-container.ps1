param(
    [string]$Root = 'C:\validation',
    [ValidateSet('enable','verify')][string]$Phase = 'verify'
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
if ($Phase -eq 'enable') {
    $result = Install-WindowsFeature Containers
    $result | Select-Object Success,RestartNeeded,ExitCode | ConvertTo-Json
    if (-not $result.Success) { exit 1 }
    exit 0
}
$out = Join-Path $Root 'work'
$receipt = [ordered]@{passed=$false;started_at=(Get-Date -Format o);network='none';isolation='process'}
try {
    $zip = Join-Path $Root 'docker.zip'
    $infra = Join-Path $Root 'infra'
    if (-not (Test-Path -LiteralPath (Join-Path $infra 'docker\docker.exe'))) { Expand-Archive -LiteralPath $zip -DestinationPath $infra }
    $docker = Join-Path $infra 'docker\docker.exe'
    $dockerd = Join-Path $infra 'docker\dockerd.exe'
    $daemon = 'C:\validation\daemon.json'
    if (-not (Test-Path -LiteralPath $daemon)) {
        [ordered]@{'data-root'='C:\validation\docker-data';hosts=@('npipe:////./pipe/docker_engine');bridge='none'} | ConvertTo-Json | Set-Content -LiteralPath $daemon -Encoding ascii
    }
    if (-not (Get-Service docker -ErrorAction SilentlyContinue)) {
        & $dockerd --register-service --config-file $daemon
        if ($LASTEXITCODE -ne 0) { throw 'Could not register isolated guest Docker service.' }
    }
    Start-Service docker
    & $docker version | Out-String | Set-Content -LiteralPath (Join-Path $out 'docker-version.txt') -Encoding utf8
    & $docker info --format '{{json .}}' | Set-Content -LiteralPath (Join-Path $out 'docker-info.json') -Encoding utf8
    if ($LASTEXITCODE -ne 0) { throw 'Docker engine did not become ready.' }
    & $docker pull mcr.microsoft.com/windows/servercore:ltsc2022
    if ($LASTEXITCODE -ne 0) { throw 'Official Windows Server Core image pull failed.' }
    $base = (& $docker image inspect mcr.microsoft.com/windows/servercore:ltsc2022 | Out-String | ConvertFrom-Json)[0]
    $receipt.base_image_id = $base.Id
    $receipt.base_image_digests = $base.RepoDigests
    $native = Get-Content -LiteralPath (Join-Path $out 'native-guest-receipt.json') -Raw | ConvertFrom-Json
    if (-not $native.passed) { throw 'Native guest verification must pass before container test.' }
    $release = Get-Content -LiteralPath (Join-Path $native.extracted_directory 'release-manifest.json') -Raw | ConvertFrom-Json
    $receipt.image = 'chan-kg-verification:' + $release.product_version
    $receipt.container = 'chan-kg-final-verification-' + $release.product_version
    $context = Join-Path $Root 'container-context'
    New-Item -ItemType Directory -Path $context -Force | Out-Null
    $product = Get-Item -LiteralPath $native.extracted_directory
    Copy-Item -LiteralPath $product.FullName -Destination (Join-Path $context $product.Name) -Recurse
    $dockerfile = "FROM mcr.microsoft.com/windows/servercore@" + ($base.RepoDigests[0] -split '@')[1] + "`r`nCOPY " + $product.Name + "/ C:/chan-kg/`r`nWORKDIR C:/chan-kg`r`n"
    [IO.File]::WriteAllText((Join-Path $context 'Dockerfile'),$dockerfile,(New-Object Text.UTF8Encoding($false)))
    & $docker build --isolation process --network none --tag $receipt.image $context
    if ($LASTEXITCODE -ne 0) { throw 'Building the actual ZIP image failed.' }
    & $docker image inspect $receipt.image | Set-Content -LiteralPath (Join-Path $out 'container-image-inspect.json') -Encoding utf8
    & $docker run --name $receipt.container --network none --isolation process $receipt.image C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoLogo -NoProfile -NonInteractive -Command "if ((Get-Command node.exe,python.exe -ErrorAction SilentlyContinue)) { throw 'Unexpected global runtime' }; & C:\chan-kg\verify.cmd --report C:\container-verification.json; exit `$LASTEXITCODE"
    $containerExit = $LASTEXITCODE
    & $docker inspect $receipt.container | Set-Content -LiteralPath (Join-Path $out 'container-inspect.json') -Encoding utf8
    & $docker cp ($receipt.container + ':C:\container-verification.json') (Join-Path $out 'container-portable-verification.json')
    if ($LASTEXITCODE -ne 0 -or $containerExit -ne 0) { throw ('Actual container verifier failed: exit=' + $containerExit) }
    $verification = Get-Content -LiteralPath (Join-Path $out 'container-portable-verification.json') -Raw | ConvertFrom-Json
    if (-not $verification.passed) { throw 'Container report failed.' }
    $receipt.actual_zip_sha256 = $native.zip_sha256
    $receipt.passed = $true
    $receipt.cleanup = 'Keep test environment until complete project delivery, then remove under host cleanup receipt.'
} catch { $receipt.error = $_.Exception.Message }
finally {
    $receipt.finished_at = (Get-Date -Format o)
    $receipt | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $out 'container-guest-receipt.json') -Encoding utf8
    $receipt | ConvertTo-Json -Depth 12
}
if (-not $receipt.passed) { exit 1 }
