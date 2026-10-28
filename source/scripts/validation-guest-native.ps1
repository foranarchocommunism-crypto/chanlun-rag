param(
    [string]$Archive = 'C:\validation\agent.zip',
    [string]$Output = 'C:\validation\work',
    [Parameter(Mandatory=$true)][string]$ExpectedSHA256,
    [ValidateSet('AMD64','ARM64')][string]$ExpectedArchitecture='AMD64',
    [ValidateRange(30,7200)][int]$DoctorTimeoutSeconds=180
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
New-Item -ItemType Directory -Path $Output -Force | Out-Null
$env:TEMP = Join-Path $Output 'temp'
$env:TMP = $env:TEMP
New-Item -ItemType Directory -Path $env:TEMP -Force | Out-Null
$receipt = [ordered]@{ passed=$false; started_at=(Get-Date -Format o); archive=$Archive; tests=@() }
try {
    $admin = (New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if ($admin) { throw 'The native portability check must run as a standard user.' }
    $nativeArchitecture=$env:PROCESSOR_ARCHITEW6432
    if (-not $nativeArchitecture) { $nativeArchitecture=$env:PROCESSOR_ARCHITECTURE }
    if ($nativeArchitecture -ne $ExpectedArchitecture) { throw 'Unexpected native Windows architecture.' }
    $os = Get-CimInstance Win32_OperatingSystem
    $receipt.environment = [ordered]@{
        hostname=$env:COMPUTERNAME; os=$os.Caption; version=$os.Version; build=$os.BuildNumber;
        architecture=$env:PROCESSOR_ARCHITECTURE; administrator=$admin;
        node_on_PATH=[bool](Get-Command node.exe -ErrorAction SilentlyContinue);
        python_on_PATH=[bool](Get-Command python.exe -ErrorAction SilentlyContinue);
        active_network_adapters=@(Get-NetAdapter -ErrorAction SilentlyContinue | Where-Object Status -eq 'Up' | Select-Object Name,Status)
    }
    if ($receipt.environment.node_on_PATH -or $receipt.environment.python_on_PATH) { throw 'Unexpected global Node/Python in clean guest.' }
    if (@($receipt.environment.active_network_adapters).Count -ne 0) { throw 'Guest network cable must be disconnected before native verification.' }
    $digest = (Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash.ToLower()
    if ($digest -ne $ExpectedSHA256) { throw 'Actual release ZIP hash mismatch.' }
    $receipt.zip_sha256 = $digest
    $receipt.tests += 'standard_user_no_global_runtimes_and_disconnected_guest_network'
    $target = Join-Path $Output '移位验收 空格路径'
    if (Test-Path -LiteralPath $target) { throw 'Use a fresh extraction path.' }
    Expand-Archive -LiteralPath $Archive -DestinationPath $target
    $products = @(Get-ChildItem -LiteralPath $target -Directory)
    if ($products.Count -ne 1) { throw 'Unexpected release ZIP layout.' }
    $product = $products[0].FullName
    $receipt.extracted_directory = $product
    $receipt.tests += 'actual_zip_extraction_to_unicode_space_path'
    $doctorText = & (Join-Path $product 'doctor.cmd') -Full -TimeoutSeconds $DoctorTimeoutSeconds
    if ($LASTEXITCODE -ne 0) { throw ('doctor failed: ' + ($doctorText -join [Environment]::NewLine)) }
    $doctor = ($doctorText -join [Environment]::NewLine) | ConvertFrom-Json
    if (-not $doctor.passed) { throw 'Full doctor result failed.' }
    $doctor | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $Output 'doctor.json') -Encoding utf8
    $receipt.tests += 'portable_doctor_full_real_model_query'
    $report = Join-Path $Output 'native-portable-verification.json'
    $log = & (Join-Path $product 'verify.cmd') --report $report 2>&1
    $log | Out-String | Set-Content -LiteralPath (Join-Path $Output 'native-verification.log') -Encoding utf8
    if ($LASTEXITCODE -ne 0) { throw 'Bundled verifier failed; inspect native-verification.log and JSON report.' }
    $verification = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
    if (-not $verification.passed) { throw 'Portable verifier reported failure.' }
    $receipt.tests += 'all_checksums_offline_models_CLI_JS_MCP_and_app_local_native_DLLs'
    $receipt.verification_report_sha256 = (Get-FileHash -LiteralPath $report -Algorithm SHA256).Hash.ToLower()
    $receipt.passed = $true
} catch { $receipt.error = $_.Exception.Message; $global:LASTEXITCODE = 1 }
finally {
    $receipt.finished_at = (Get-Date -Format o)
    $receipt | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $Output 'native-guest-receipt.json') -Encoding utf8
    $receipt | ConvertTo-Json -Depth 12
}
if (-not $receipt.passed) { exit 1 }
