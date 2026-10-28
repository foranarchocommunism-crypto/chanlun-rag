"""Run a task-owned native ARM64 Windows guest through whole-system emulation.

No host NIC, boot configuration or input devices are controlled. QMP is bound
to loopback for process status and framebuffer evidence; the guest has no NIC.
The VHDX must be prepared by prepare-arm64-validation.ps1 first.
"""
import argparse
import json
from pathlib import Path
import shutil
import socket
import subprocess
import time

WORKSPACE = Path(__file__).resolve().parents[2]
INFRA = Path(r'C:\Users\13240\.codex\containers\chan-kg')
VM = INFRA / 'arm64-vm'
RUN = WORKSPACE / 'validation-runs/windows-compatibility-20261023/arm64'
QEMU = INFRA / 'qemu/qemu-system-aarch64.exe'
PORT = 26148


def qmp(command, arguments=None):
    with socket.create_connection(('127.0.0.1', PORT), timeout=15) as connection:
        stream = connection.makefile('rwb', buffering=0)
        json.loads(stream.readline())
        stream.write(b'{"execute":"qmp_capabilities"}\r\n')
        while 'return' not in json.loads(stream.readline()):
            pass
        stream.write((json.dumps({'execute': command, **({'arguments': arguments} if arguments else {})})+'\r\n').encode())
        while True:
            response = json.loads(stream.readline())
            if 'error' in response:
                raise RuntimeError(response['error'])
            if 'return' in response:
                return response['return']


parser = argparse.ArgumentParser()
parser.add_argument('phase', choices=['start', 'status', 'collect'])
args = parser.parse_args()
RUN.mkdir(parents=True, exist_ok=True)
if args.phase == 'start':
    assert (VM / 'preparation-receipt.json').exists(), 'Prepare and detach the Windows ARM64 disk first'
    try:
        existing = qmp('query-status')
    except (OSError, ValueError):
        existing = None
    assert existing is None, f'Existing QEMU guest must be inspected, not restarted: {existing}'
    attached = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
        f"(Get-DiskImage -ImagePath '{VM / 'system.vhdx'}').Attached"], capture_output=True, text=True, check=True,
        creationflags=subprocess.CREATE_NO_WINDOW).stdout.strip()
    assert attached == 'False', 'Detach the owned VHDX from the host before guest boot'
    variables = VM / 'efi-vars.fd'
    if not variables.exists():
        shutil.copyfile(INFRA / 'qemu/share/edk2-arm-vars.fd', variables)
    arguments = [str(QEMU), '-name', 'chan-kg-native-arm64-validation',
        '-machine', 'virt,acpi=on,gic-version=3', '-cpu', 'max', '-accel', 'tcg,thread=multi',
        '-smp', '4', '-m', '6144', '-display', 'none', '-device', 'ramfb',
        '-drive', f'if=pflash,format=raw,unit=0,readonly=on,file={INFRA / "qemu/share/edk2-aarch64-code.fd"}',
        '-drive', f'if=pflash,format=raw,unit=1,file={variables}',
        '-drive', f'if=none,id=os,format=vhdx,file={VM / "system.vhdx"}',
        '-device', 'nvme,drive=os,serial=CHANKGARM64,bootindex=0',
        '-device', 'qemu-xhci', '-device', 'usb-kbd', '-device', 'usb-tablet',
        '-nic', 'none', '-qmp', f'tcp:127.0.0.1:{PORT},server=on,wait=off',
        '-serial', f'file:{VM / "serial.log"}']
    with (VM / 'qemu-stdout.log').open('ab') as output, (VM / 'qemu-stderr.log').open('ab') as errors:
        process = subprocess.Popen(arguments, stdout=output, stderr=errors, creationflags=subprocess.CREATE_NO_WINDOW)
    receipt = {'pid': process.pid, 'started_unix': time.time(), 'command': arguments,
               'architecture': 'ARM64 guest under x64-host TCG whole-system emulation',
               'network': 'no NIC', 'performance_claim': False, 'shutdown': 'guest shuts down after standard-user test'}
    (RUN / 'boot-process.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'started': True, 'pid': process.pid, 'qmp_loopback_port': PORT}))
elif args.phase == 'status':
    try:
        status = qmp('query-status')
        screenshot = str(RUN / 'guest-framebuffer.ppm')
        qmp('screendump', {'filename': screenshot})
        print(json.dumps({'qmp': status, 'screenshot': screenshot}))
    except (OSError, ValueError) as error:
        print(json.dumps({'qmp_unreachable': True, 'error': str(error),
                          'next': 'Inspect the recorded process and stderr; collect only after verified guest shutdown'}))
else:
    try:
        running = qmp('query-status')
    except (OSError, ValueError):
        running = None
    assert running is None, f'Guest still has a live QMP handle: {running}'
    # The recorded PID can be stale. Check all current processes by exact binary
    # and owned disk path before mounting; never infer shutdown from QMP failure.
    ps = rf"""
$ErrorActionPreference='Stop'
$vmDisk='{VM / 'system.vhdx'}'
$running=@(Get-CimInstance Win32_Process | Where-Object {{ $_.ExecutablePath -eq '{QEMU}' -and $_.CommandLine -like '*chan-kg-native-arm64-validation*' }})
if ($running.Count) {{ throw 'ARM64 QEMU process still exists; do not mount its live disk.' }}
$image=Mount-DiskImage -ImagePath $vmDisk -Access ReadOnly -PassThru
try {{
  $disk=$image | Get-Disk
  $volume=@($disk | Get-Partition | Get-Volume -ErrorAction SilentlyContinue | Where-Object FileSystemLabel -eq 'CHANKGARM')
  if ($volume.Count -ne 1) {{ throw 'Could not identify the owned Windows ARM64 volume.' }}
  if (-not $volume[0].DriveLetter) {{ throw 'Read-only guest volume has no drive letter; inspect disk mapping.' }}
  $root=$volume[0].DriveLetter + ':\'
  if ($root -eq ($env:SystemDrive + '\')) {{ throw 'Refusing host Windows volume.' }}
  if (Test-Path -LiteralPath ($root+'validation\work')) {{ Copy-Item -LiteralPath ($root+'validation\work') -Destination '{RUN / 'guest-work'}' -Recurse }}
  foreach ($log in @('Windows\Panther\setuperr.log','Windows\Panther\UnattendGC\setuperr.log','Windows\Panther\UnattendGC\setupact.log')) {{
    if (Test-Path -LiteralPath ($root+$log)) {{ Copy-Item -LiteralPath ($root+$log) -Destination (Join-Path '{RUN}' ($log.Replace('\','-'))) }}
  }}
}} finally {{ Dismount-DiskImage -ImagePath $vmDisk }}
"""
    script = VM / 'collect-results.ps1'
    script.write_text(ps, encoding='utf-8-sig')
    subprocess.run(['powershell.exe', '-NoLogo', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', str(script)],
                   check=True, creationflags=subprocess.CREATE_NO_WINDOW)
    native = RUN / 'guest-work/native-guest-receipt.json'
    assert native.exists(), 'Guest shut down without a native verification receipt; inspect collected setup logs'
    receipt = json.loads(native.read_text(encoding='utf-8-sig'))
    assert receipt['passed'] and receipt['environment']['architecture'] == 'ARM64', receipt
    print(json.dumps({'passed': True, 'receipt': str(native), 'zip_sha256': receipt['zip_sha256'],
                      'physical_ARM_performance_verified': False}))
