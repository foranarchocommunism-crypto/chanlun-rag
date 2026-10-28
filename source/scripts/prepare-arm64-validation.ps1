param(
    [Parameter(Mandatory=$true)][string]$Iso,
    [Parameter(Mandatory=$true)][string]$Archive,
    [Parameter(Mandatory=$true)][string]$ArchiveSHA256,
    [string]$Infrastructure='C:\Users\13240\.codex\containers\chan-kg'
)
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
$infra=[IO.Path]::GetFullPath($Infrastructure)
$vm=Join-Path $infra 'arm64-vm'
$vhd=Join-Path $vm 'system.vhdx'
if (Test-Path -LiteralPath $vhd) { throw 'An ARM64 validation disk already exists. Inspect it instead of replacing it.' }
if ((Get-FileHash -LiteralPath $Iso -Algorithm SHA256).Hash.ToLowerInvariant() -ne '8992f2d2cfd2fa647e579e9eb31fc21f34da8333c29b6170fde17d2ed6623e9c') { throw 'Official ARM64 ISO SHA256 mismatch.' }
if ((Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ArchiveSHA256) { throw 'Actual product ZIP SHA256 mismatch.' }
New-Item -ItemType Directory -Path $vm -Force | Out-Null
$diskpart=Join-Path $vm 'create-owned-disk.txt'
@("create vdisk file=`"$vhd`" maximum=65536 type=expandable", "select vdisk file=`"$vhd`"", 'attach vdisk') | Set-Content -LiteralPath $diskpart -Encoding ascii
& diskpart.exe /s $diskpart | Out-File -LiteralPath (Join-Path $vm 'diskpart.log') -Encoding utf8
if ($LASTEXITCODE -ne 0) { throw 'Creating the task-owned virtual disk failed.' }
$isoMounted=$false
try {
    $disk=Get-DiskImage -ImagePath $vhd | Get-Disk
    if ($disk.PartitionStyle -ne 'RAW' -or $disk.BusType -notin @('File Backed Virtual','FileBackedVirtual','Virtual') -or $disk.Size -lt 63GB -or $disk.IsBoot -or $disk.IsSystem) { throw 'Disk is not the new empty task-owned virtual disk.' }
    $disk | Select-Object Number,UniqueId,Path,BusType,Size,PartitionStyle,IsBoot,IsSystem | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $vm 'owned-disk-before-partition.json') -Encoding utf8
    $disk=$disk | Initialize-Disk -PartitionStyle GPT -PassThru
    function Format-OwnedPartition($Partition,[string]$Filesystem,[string]$Label) {
        $current=Get-DiskImage -ImagePath $vhd | Get-Disk
        if ($Partition.DiskNumber -ne $current.Number -or $current.UniqueId -ne $disk.UniqueId -or $current.IsBoot -or $current.IsSystem) { throw 'Virtual disk identity changed before format.' }
        return ($Partition | Format-Volume -FileSystem $Filesystem -NewFileSystemLabel $Label -Confirm:$false)
    }
    $efi=New-Partition -DiskNumber $disk.Number -Size 260MB -GptType '{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}' -AssignDriveLetter
    $efiVolume=Format-OwnedPartition $efi 'FAT32' 'CHANKGEFI'
    New-Partition -DiskNumber $disk.Number -Size 16MB -GptType '{e3c9e316-0b5c-4db8-817d-f92df00215ae}' | Out-Null
    $windows=New-Partition -DiskNumber $disk.Number -UseMaximumSize -AssignDriveLetter
    $windowsVolume=Format-OwnedPartition $windows 'NTFS' 'CHANKGARM'
    function Ensure-OwnedDriveLetter($Partition) {
        $volume=$Partition | Get-Volume
        if (-not $volume.DriveLetter) {
            $used=@(Get-Volume | Where-Object DriveLetter | ForEach-Object {[string]$_.DriveLetter})
            $letter=@('U','V','W','X','Y','Z','T','S','R' | Where-Object {$_ -notin $used})[0]
            if (-not $letter) { throw 'No unused temporary drive letter for the owned virtual disk.' }
            $current=Get-DiskImage -ImagePath $vhd | Get-Disk
            if ($Partition.DiskNumber -ne $current.Number -or $current.IsBoot -or $current.IsSystem) { throw 'Unexpected virtual disk while assigning a drive letter.' }
            $Partition | Add-PartitionAccessPath -AccessPath ($letter + ':\')
            $volume=Get-Partition -DiskNumber $current.Number -PartitionNumber $Partition.PartitionNumber | Get-Volume
        }
        if (-not $volume.DriveLetter) { throw 'The owned virtual disk volume has no drive letter.' }
        return $volume
    }
    $efiVolume=Ensure-OwnedDriveLetter $efi
    $windowsVolume=Ensure-OwnedDriveLetter $windows
    $osRoot=$windowsVolume.DriveLetter + ':\'
    $efiRoot=$efiVolume.DriveLetter + ':\'
    if ($osRoot -eq ($env:SystemDrive + '\') -or $efiRoot -eq ($env:SystemDrive + '\')) { throw 'Refusing any host system-volume target.' }
    $mounted=Mount-DiskImage -ImagePath $Iso -PassThru
    $isoMounted=$true
    $dvd=($mounted | Get-Volume).DriveLetter + ':\'
    $wim=Join-Path $dvd 'sources\install.wim'
    if (-not (Test-Path -LiteralPath $wim)) { $wim=Join-Path $dvd 'sources\install.esd' }
    $images=Get-WindowsImage -ImagePath $wim
    $pro=@($images | Where-Object ImageName -eq 'Windows 11 Pro')
    if ($pro.Count -ne 1) { throw 'Windows 11 Pro image selection is ambiguous.' }
    $image=Get-WindowsImage -ImagePath $wim -Index $pro[0].ImageIndex
    if ($image.Architecture -ne 12) { throw 'Selected Windows image is not ARM64.' }
    $image | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $vm 'official-image.json') -Encoding utf8
    & dism.exe /Apply-Image "/ImageFile:$wim" "/Index:$($pro[0].ImageIndex)" "/ApplyDir:$osRoot" /CheckIntegrity /NoRpFix | Out-File -LiteralPath (Join-Path $vm 'dism-apply.log') -Encoding utf8
    if ($LASTEXITCODE -ne 0) { throw 'Applying the official ARM64 image failed; preserve the disk and DISM log.' }
    & "$env:SystemRoot\System32\bcdboot.exe" (Join-Path $osRoot 'Windows') /s ($efiVolume.DriveLetter + ':') /f UEFI /v | Out-File -LiteralPath (Join-Path $vm 'bcdboot.log') -Encoding utf8
    if ($LASTEXITCODE -ne 0) { throw 'Creating boot files on the owned EFI partition failed.' }
    New-Item -ItemType Directory -Path (Join-Path $efiRoot 'EFI\Boot') -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $osRoot 'Windows\Boot\EFI\bootmgfw.efi') -Destination (Join-Path $efiRoot 'EFI\Boot\bootaa64.efi')
    & bcdedit.exe /store (Join-Path $efiRoot 'EFI\Microsoft\Boot\BCD') /enum all | Out-File -LiteralPath (Join-Path $vm 'guest-bcd.txt') -Encoding utf8
    $validation=Join-Path $osRoot 'validation'
    New-Item -ItemType Directory -Path $validation -Force | Out-Null
    Copy-Item -LiteralPath $Archive -Destination (Join-Path $validation 'agent.zip')
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'validation-guest-native.ps1') -Destination $validation
    $setup=@'
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
New-Item -ItemType Directory -Path C:\validation\work -Force | Out-Null
& icacls.exe C:\validation\work /grant '*S-1-5-32-545:(OI)(CI)M' /T | Out-Null
$action=New-ScheduledTaskAction -Execute 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' -Argument '-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File C:\validation\run-arm-validation.ps1'
$principal=New-ScheduledTaskPrincipal -GroupId 'S-1-5-32-545' -RunLevel Limited
$trigger=New-ScheduledTaskTrigger -AtLogOn
$settings=New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 12) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName ChanKGStandardUserValidation -Action $action -Principal $principal -Trigger $trigger -Settings $settings | Out-Null
'@
    $runner=@'
$ProgressPreference='SilentlyContinue'
$env:CHAN_KG_VERIFICATION_TIMEOUT_MS='7200000'
try {
    & C:\validation\validation-guest-native.ps1 -ExpectedSHA256 '__ZIP_SHA256__' -ExpectedArchitecture ARM64 -DoctorTimeoutSeconds 7200 *>&1 | Out-File -LiteralPath C:\validation\work\arm-native-execution.log -Encoding utf8
} finally {
    [IO.File]::WriteAllText('C:\validation\work\guest-run-finished.txt',(Get-Date -Format o))
    & shutdown.exe /s /t 5
}
'@.Replace('__ZIP_SHA256__',$ArchiveSHA256)
    $utf8bom=New-Object Text.UTF8Encoding($true)
    [IO.File]::WriteAllText((Join-Path $validation 'setup-standard-test.ps1'),$setup,$utf8bom)
    [IO.File]::WriteAllText((Join-Path $validation 'run-arm-validation.ps1'),$runner,$utf8bom)
    $passwordPath=Join-Path $infra 'arm64-guest-password.txt'
    if (-not (Test-Path -LiteralPath $passwordPath)) {
        $secret='Aa1' + [Guid]::NewGuid().ToString('N')
        [IO.File]::WriteAllText($passwordPath,$secret,[Text.Encoding]::ASCII)
        & icacls.exe $passwordPath /inheritance:r /grant:r ((& whoami.exe) + ':F') 'SYSTEM:F' | Out-Null
    }
    $secret=[IO.File]::ReadAllText($passwordPath)
    $xml=@'
<?xml version="1.0" encoding="utf-8"?>
<unattend xmlns="urn:schemas-microsoft-com:unattend" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
  <settings pass="specialize">
    <component name="Microsoft-Windows-Shell-Setup" processorArchitecture="arm64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS"><ComputerName>CHANKGARM</ComputerName><TimeZone>UTC</TimeZone></component>
    <component name="Microsoft-Windows-Deployment" processorArchitecture="arm64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS"><RunSynchronous><RunSynchronousCommand wcm:action="add"><Order>1</Order><Path>powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File C:\validation\setup-standard-test.ps1</Path></RunSynchronousCommand></RunSynchronous></component>
  </settings>
  <settings pass="oobeSystem">
    <component name="Microsoft-Windows-International-Core" processorArchitecture="arm64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS"><InputLocale>0409:00000409</InputLocale><SystemLocale>en-US</SystemLocale><UILanguage>en-US</UILanguage><UserLocale>en-US</UserLocale></component>
    <component name="Microsoft-Windows-Shell-Setup" processorArchitecture="arm64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS">
      <OOBE><HideEULAPage>true</HideEULAPage><HideOnlineAccountScreens>true</HideOnlineAccountScreens><HideWirelessSetupInOOBE>true</HideWirelessSetupInOOBE><ProtectYourPC>3</ProtectYourPC></OOBE>
      <UserAccounts><LocalAccounts>
        <LocalAccount wcm:action="add"><Name>validator</Name><Group>Administrators</Group><Password><Value>__PASSWORD__</Value><PlainText>true</PlainText></Password></LocalAccount>
        <LocalAccount wcm:action="add"><Name>agentuser</Name><Group>Users</Group><Password><Value>__PASSWORD__</Value><PlainText>true</PlainText></Password></LocalAccount>
      </LocalAccounts></UserAccounts>
      <AutoLogon><Username>agentuser</Username><Enabled>true</Enabled><LogonCount>1</LogonCount><Password><Value>__PASSWORD__</Value><PlainText>true</PlainText></Password></AutoLogon>
    </component>
  </settings>
</unattend>
'@.Replace('__PASSWORD__',$secret)
    New-Item -ItemType Directory -Path (Join-Path $osRoot 'Windows\Panther') -Force | Out-Null
    [IO.File]::WriteAllText((Join-Path $osRoot 'Windows\Panther\unattend.xml'),$xml,(New-Object Text.UTF8Encoding($false)))
    [ordered]@{prepared_at=(Get-Date -Format o);disk=$vhd;iso_sha256='8992f2d2cfd2fa647e579e9eb31fc21f34da8333c29b6170fde17d2ed6623e9c';zip_sha256=$ArchiveSHA256;image_index=$pro[0].ImageIndex;architecture='ARM64';method='Microsoft DISM offline image deployment into task-owned GPT VHDX; native ARM64 Windows boot under QEMU TCG';host_boot_store_modified=$false;network_device='none';test_user='agentuser standard limited token'} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $vm 'preparation-receipt.json') -Encoding utf8
} finally {
    if ($isoMounted) { Dismount-DiskImage -ImagePath $Iso }
    Dismount-DiskImage -ImagePath $vhd
}
