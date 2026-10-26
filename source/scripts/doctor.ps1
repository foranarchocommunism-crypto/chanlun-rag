param([switch]$Full, [ValidateRange(30,7200)][int]$TimeoutSeconds=180)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$product = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$result = [ordered]@{
    passed = $false
    checked_at = (Get-Date -Format o)
    product_root = $product
    checks = @()
    full_model_query = [bool]$Full
}
$exitCode = 1
function Get-LocalSHA256([string]$Path) {
    $stream = [IO.File]::OpenRead($Path)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try { return [BitConverter]::ToString($algorithm.ComputeHash($stream)).Replace('-','').ToLowerInvariant() }
    finally { $stream.Dispose(); $algorithm.Dispose() }
}
try {
    $os = Get-CimInstance Win32_OperatingSystem
    $nativeArch = $env:PROCESSOR_ARCHITEW6432
    if (-not $nativeArch) { $nativeArch = $env:PROCESSOR_ARCHITECTURE }
    $result.environment = [ordered]@{
        windows = $os.Caption
        build = [int]$os.BuildNumber
        architecture = $nativeArch
        physical_memory_bytes = [long](Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory
        powershell = $PSVersionTable.PSVersion.ToString()
        administrator_required = $false
    }
    $nodeArch = switch ($nativeArch) { 'AMD64' { 'x64' }; 'ARM64' { 'arm64' }; default { throw 'This release requires native x64 or ARM64 Windows.' } }
    if ([int]$os.BuildNumber -lt 17763) {
        throw 'This release requires Windows 10 1809 or newer, x64 or ARM64.'
    }
    $result.checks += 'windows_native_architecture_and_minimum_build'
    $result.environment.selected_node_arch = $nodeArch
    $runtime = Join-Path $product ('runtime\' + $nodeArch + '\node.exe')
    if (-not (Test-Path -LiteralPath $runtime -PathType Leaf)) { throw 'Bundled runtime is missing. Extract the complete release ZIP first.' }
    $manifest = Get-Content -LiteralPath (Join-Path $product 'release-manifest.json') -Raw | ConvertFrom-Json
    if ((Get-LocalSHA256 $runtime) -ne $manifest.runtimes.$nodeArch.sha256) { throw 'Bundled runtime checksum mismatch.' }
    $result.checks += 'bundled_runtime_sha256'
    $cli = Join-Path $product 'app\bin\chan-kg.mjs'
    $start = New-Object System.Diagnostics.ProcessStartInfo
    $start.FileName = $runtime
    $start.Arguments = '"' + $cli + '" status'
    if ($Full) { $start.Arguments = '"' + $cli + '" retrieve "中枢成立需要什么条件？" --limit 3' }
    $start.UseShellExecute = $false
    $start.CreateNoWindow = $true
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    $start.StandardOutputEncoding = New-Object System.Text.UTF8Encoding($false)
    $start.StandardErrorEncoding = New-Object System.Text.UTF8Encoding($false)
    $start.WorkingDirectory = [IO.Path]::GetTempPath()
    $start.EnvironmentVariables['PATH'] = [IO.Path]::GetDirectoryName($runtime) + ';' + (Join-Path $env:SystemRoot 'System32')
    $start.EnvironmentVariables['NODE_PATH'] = ''
    $start.EnvironmentVariables['NODE_OPTIONS'] = ''
    $start.EnvironmentVariables['CHAN_KG_PATH'] = Join-Path $product 'knowledge'
    $start.EnvironmentVariables['CHAN_KG_INDEX'] = Join-Path $product 'indexes\active'
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $start
    try {
        [void]$process.Start()
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit($TimeoutSeconds * 1000)) { $process.Kill(); throw ('Local runtime check timed out after ' + $TimeoutSeconds + ' seconds.') }
        $output = $stdout.GetAwaiter().GetResult()
        $diagnostics = $stderr.GetAwaiter().GetResult()
        if ($process.ExitCode -ne 0) { throw ('Local runtime failed: ' + $diagnostics) }
        $packet = $output | ConvertFrom-Json
        if ($packet.graph_version -ne $manifest.graph_version) { throw 'Knowledge version mismatch.' }
        if ($Full) {
            if ($packet.runtime.degraded) { throw 'The full model query degraded.' }
            if ($packet.runtime.actual_channels -notcontains 'semantic_vector' -or $packet.runtime.actual_channels -notcontains 'cross_encoder_rerank') { throw 'Expected model channels did not run.' }
            if (@($packet.data.reviewed).Count -lt 1) { throw 'The full query returned no reviewed evidence.' }
        } elseif ($packet.data.index_problem -or $packet.data.dense_problem) { throw 'Knowledge/index/model configuration is inconsistent.' }
        $result.checks += $(if ($Full) { 'real_embedding_and_reranker_query' } else { 'real_status_with_isolated_PATH' })
        $result.graph_version = $packet.graph_version
        $result.diagnostics = $diagnostics.Trim()
    } finally { $process.Dispose() }
    $result.passed = $true
    $exitCode = 0
} catch {
    $result.error = $_.Exception.Message
} finally {
    $result | ConvertTo-Json -Depth 8
}
exit $exitCode
