$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$run = Join-Path $workspace 'validation-runs\x64-delivery-20261023'
$infra = 'C:\Users\13240\.codex\containers\chan-kg'
$vbox = 'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe'
$vmId = 'bd74f9ee-3207-49aa-8993-1acc26001d37'
$actions = @()
$scope = Get-Content -LiteralPath (Join-Path $run 'scope-change.json') -Raw | ConvertFrom-Json
if ($scope.ARM64_validation -ne 'cancelled_by_user' -or $scope.windows_container_validation -ne 'cancelled_by_user') { throw 'Current explicit cleanup authorization is missing.' }
$zip = Get-Content -LiteralPath (Join-Path $run 'zip-build.json') -Raw | ConvertFrom-Json
$native = Get-Content -LiteralPath (Join-Path $run 'native-guest-receipt.json') -Raw | ConvertFrom-Json
if (-not $native.passed -or $native.zip_sha256 -ne $zip.sha256) { throw 'Export the final x64 ZIP verification receipt before removing its VM.' }
if ((Get-FileHash -LiteralPath $zip.archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $zip.sha256) { throw 'Final ZIP changed.' }

function Remove-OwnedTree([string]$Path, [string]$Expected) {
    $absolute = [IO.Path]::GetFullPath($Path).TrimEnd('\')
    if ($absolute -cne [IO.Path]::GetFullPath($Expected).TrimEnd('\')) { throw 'Cleanup target differs from the explicitly owned directory.' }
    if (-not (Test-Path -LiteralPath $absolute)) { return }
    $item = Get-Item -LiteralPath $absolute -Force
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw ('Refuse redirected cleanup root: ' + $absolute) }
    if (@(Get-ChildItem -LiteralPath $absolute -Recurse -Force -Attributes ReparsePoint).Count) { throw ('Refuse nested redirected cleanup paths: ' + $absolute) }
    $files = @(Get-ChildItem -LiteralPath $absolute -Recurse -File -Force)
    $bytes = ($files | Measure-Object Length -Sum).Sum
    Remove-Item -LiteralPath $absolute -Recurse -Force
    $script:actions += [pscustomobject]@{action='removed_owned_tree';path=$absolute;files=$files.Count;bytes=$bytes}
}

if (Test-Path -LiteralPath $vbox) {
    $registered = @(& $vbox list vms)
    if (@($registered | Where-Object { $_ -notmatch $vmId }).Count) { throw 'Unexpected other VirtualBox VM; inspect before uninstalling.' }
    if ($registered.Count) {
        $info = & $vbox showvminfo $vmId --machinereadable | Out-String
        if ($LASTEXITCODE -ne 0 -or $info -notmatch 'name="chan-kg-clean-win2022"' -or $info -notmatch 'chan-kg\\\\vms\\\\chan-kg-clean-win2022') { throw 'VM identity or owned disk path did not match.' }
        [IO.File]::WriteAllText((Join-Path $run 'vm-before-removal.txt'),$info)
        if ($info -match 'VMState="running"') {
            & $vbox controlvm $vmId poweroff
            if ($LASTEXITCODE -ne 0) { throw 'Could not power off the owned validation VM.' }
        }
        & $vbox unregistervm $vmId --delete
        if ($LASTEXITCODE -ne 0) { throw 'Could not delete the owned validation VM.' }
        $actions += [pscustomobject]@{action='unregistered_and_deleted_validation_VM';uuid=$vmId}
    }
    if (@(& $vbox list vms).Count) { throw 'A registered VM remains after task VM removal.' }
    Get-Service -Name VBoxSDS -ErrorAction SilentlyContinue | Stop-Service -Force
    Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^VBox(SVC|SDS|Headless)\.exe$' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    $uninstall = Start-Process -FilePath "$env:SystemRoot\System32\msiexec.exe" -ArgumentList @('/x','{4852102F-57E8-46C0-9424-3F0DBC5467E2}','/qn','/norestart','/L*v',('"'+(Join-Path $run 'virtualbox-uninstall.log')+'"')) -WindowStyle Hidden -Wait -PassThru
    $actions += [pscustomobject]@{action='uninstalled_VirtualBox';exit=$uninstall.ExitCode}
    if ($uninstall.ExitCode -notin @(0,3010)) { throw ('VirtualBox uninstall failed: ' + $uninstall.ExitCode) }
}

$ownedProcesses = @(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -and ($_.ExecutablePath.StartsWith($infra+'\',[StringComparison]::OrdinalIgnoreCase) -or $_.ExecutablePath.StartsWith('C:\Program Files\Oracle\VirtualBox\',[StringComparison]::OrdinalIgnoreCase)) })
if ($ownedProcesses.Count) { throw 'A temporary-environment process still runs; inspect before removing its files.' }
foreach ($level in @('User','Machine')) {
    $current = [Environment]::GetEnvironmentVariable('Path',$level)
    $parts = @($current -split ';' | Where-Object { $_ })
    $kept = @($parts | Where-Object { -not $_.TrimEnd('\').StartsWith($infra,[StringComparison]::OrdinalIgnoreCase) -and $_.TrimEnd('\') -ne 'C:\Program Files\Oracle\VirtualBox' })
    if ($kept.Count -ne $parts.Count) {
        [Environment]::SetEnvironmentVariable('Path',($kept -join ';'),$level)
        $actions += [pscustomobject]@{action='removed_only_owned_PATH_entries';level=$level;removed=$parts.Count-$kept.Count}
    }
    $value = [Environment]::GetEnvironmentVariable('VBOX_MSI_INSTALL_PATH',$level)
    if ($value -and $value.TrimEnd('\') -eq 'C:\Program Files\Oracle\VirtualBox') { [Environment]::SetEnvironmentVariable('VBOX_MSI_INSTALL_PATH',$null,$level) }
}
$profile = 'C:\Users\13240\.VirtualBox'
if (Test-Path -LiteralPath $profile) {
    if ((Get-Item -LiteralPath $profile).CreationTime -lt [datetime]'2026-10-23T11:17:00') { throw 'VirtualBox profile predates this task.' }
    if (@(Get-ChildItem -LiteralPath $profile -Force | Where-Object { $_.Name -notmatch '^(VBoxSVC\.log(?:\.\d+)?|VirtualBox\.xml(?:-prev|-tmp)?)$' }).Count) { throw 'Unexpected VirtualBox profile file.' }
    if ((Get-Content -LiteralPath (Join-Path $profile 'VirtualBox.xml') -Raw) -match '<MachineEntry') { throw 'VirtualBox still records a VM.' }
    Remove-OwnedTree $profile 'C:\Users\13240\.VirtualBox'
}
Remove-OwnedTree 'C:\Program Files\Oracle\VirtualBox' 'C:\Program Files\Oracle\VirtualBox'
Remove-OwnedTree $infra 'C:\Users\13240\.codex\containers\chan-kg'

$features = @(Get-WindowsOptionalFeature -Online | Where-Object { $_.FeatureName -match '^Microsoft-Hyper-V|^Containers$' } | Select-Object FeatureName,State)
$installed = @(Get-ItemProperty -Path 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*','HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -match '^(QEMU|Oracle VirtualBox)' } | Select-Object DisplayName,DisplayVersion)
$services = @(Get-CimInstance Win32_SystemDriver | Where-Object { $_.Name -match '^VBox' } | Select-Object Name,State,PathName)
$listeners = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -in @(25985,26148,26149) } | Select-Object LocalAddress,LocalPort)
$pending = Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending'
$passed = -not (Test-Path -LiteralPath $infra) -and -not (Test-Path -LiteralPath 'C:\Program Files\Oracle\VirtualBox') -and $installed.Count -eq 0 -and $services.Count -eq 0 -and $listeners.Count -eq 0 -and @($features | Where-Object { [string]$_.State -ne 'Disabled' -and [int]$_.State -ne 0 }).Count -eq 0
$receipt = [ordered]@{passed=$passed;finished_at=(Get-Date -Format o);actions=$actions;installed_temporary_software=$installed;remaining_VirtualBox_drivers=$services;temporary_listeners=$listeners;optional_features=$features;Windows_servicing_restart_pending=$pending;host_restarted=$false;restart_note='Windows reports a servicing restart after optional-feature rollback; no host restart or manual deletion of servicing state was performed.';preserved=@('Final x64 product and its runtime/models','Canonical graph and two source PDFs','Maintenance source and audit receipts')}
$receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $run 'environment-cleanup.json') -Encoding utf8
$receipt | ConvertTo-Json -Depth 8
if (-not $passed) { throw 'Some temporary environment components remain; inspect the cleanup receipt.' }
