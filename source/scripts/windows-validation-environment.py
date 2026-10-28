"""Temporary, task-owned Windows VM validation. Credentials stay outside the project.

Run install after the official ISO download is complete, then native and container.
The environment is retained until project delivery; cleanup is a separate gated step.
"""
import argparse
import hashlib
import json
from pathlib import Path, PureWindowsPath
import secrets
import subprocess
import time

WORKSPACE = Path(__file__).resolve().parents[2]
INFRA = Path(r'C:\Users\13240\.codex\containers\chan-kg')
RUN = WORKSPACE / 'validation-runs/windows-compatibility-20261023'
VBOX = r'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe'
VM = 'chan-kg-clean-win2022'
GUEST_PS = r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
SOURCE = WORKSPACE / 'chan-kg-agent/scripts'
GUEST_ROOT = PureWindowsPath(r'C:\validation')


def invoke(arguments, timeout=120, check=True):
    result = subprocess.run(arguments, capture_output=True, encoding='utf-8', errors='replace',
                            timeout=timeout, creationflags=subprocess.CREATE_NO_WINDOW)
    if check and result.returncode:
        raise RuntimeError(f'Command failed ({result.returncode}): {result.stdout[-3000:]} {result.stderr[-3000:]}')
    return result


def password_file(name):
    path = INFRA / name
    if not path.exists():
        path.write_text('Aa1' + secrets.token_hex(16), encoding='ascii')
        who = invoke(['whoami']).stdout.strip()
        invoke(['icacls', str(path), '/inheritance:r', '/grant:r', f'{who}:F', 'SYSTEM:F'])
    return path


def guest(command, standard=False, timeout=180, check=True):
    import base64
    encoded = base64.b64encode(command.encode('utf-16-le')).decode('ascii')
    pw = password_file('standard-password.txt' if standard else 'guest-password.txt')
    return invoke([VBOX, 'guestcontrol', VM, 'run', '--username', 'agentuser' if standard else 'validator',
                   '--passwordfile', str(pw), '--exe', GUEST_PS, '--timeout', str(timeout * 1000),
                   '--wait-stdout', '--wait-stderr', '--', '-NoLogo', '-NoProfile',
                   '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-EncodedCommand', encoded],
                  timeout=timeout + 30, check=check)


def wait_guest(limit=1800):
    started = time.monotonic()
    while time.monotonic() - started < limit:
        result = guest("[Console]::Write('GUEST_READY')", timeout=15, check=False)
        if result.returncode == 0 and 'GUEST_READY' in result.stdout:
            print(json.dumps({'stage': 'guest_ready', 'elapsed_seconds': time.monotonic() - started}), flush=True)
            return
        time.sleep(15)
    raise RuntimeError('Guest login did not become ready within the install/reboot limit')


def copy_to(path, target):
    destination = PureWindowsPath(target)
    invoke([VBOX, 'guestcontrol', VM, 'copyto', '--username', 'validator', '--passwordfile',
            str(password_file('guest-password.txt')), '--target-directory', str(destination.parent) + '\\', str(path)], timeout=600)
    if path.name != destination.name:
        original = str(destination.parent / path.name).replace("'", "''")
        target_quoted = str(destination).replace("'", "''")
        guest(f"$ErrorActionPreference='Stop'; Move-Item -LiteralPath '{original}' -Destination '{target_quoted}' -Force")


def collect():
    for name in ['native-guest-receipt.json', 'native-portable-verification.json', 'native-verification.log',
                 'doctor.json', 'docker-version.txt', 'docker-info.json', 'container-image-inspect.json',
                 'container-inspect.json', 'container-portable-verification.json', 'container-guest-receipt.json']:
        result = invoke([VBOX, 'guestcontrol', VM, 'copyfrom', '--username', 'validator', '--passwordfile',
                         str(password_file('guest-password.txt')), '--target-directory', str(RUN) + '\\', str(GUEST_ROOT / 'work' / name)],
                        timeout=60, check=False)
        if result.returncode == 0:
            print(json.dumps({'collected': name}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['install', 'native', 'container', 'container-start', 'container-status', 'collect'])
    parser.add_argument('--run', type=Path)
    parser.add_argument('--guest-root', default=r'C:\validation')
    args = parser.parse_args()
    if args.run:
        RUN = args.run.resolve()
    GUEST_ROOT = PureWindowsPath(args.guest_root)
    assert GUEST_ROOT.drive.upper() == 'C:' and str(GUEST_ROOT).lower().startswith('c:\\validation')
    RUN.mkdir(parents=True, exist_ok=True)
    if args.phase == 'install':
        receipt = json.loads((INFRA / 'iso-download-receipt.json').read_text(encoding='utf-8'))
        iso = INFRA / 'SERVER_EVAL_x64FRE_en-us.iso'
        assert iso.stat().st_size == receipt['bytes']
        with iso.open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == receipt['sha256']
        credential = password_file('guest-password.txt')
        # The vendor template emits <ProductKey><Key/></ProductKey> for an evaluation
        # install without a key. Server 2022 then fails before disk installation with
        # "Windows cannot find the Microsoft Software License Terms". Omit only this
        # empty element; the official evaluation image and license acceptance remain.
        template_source = Path(VBOX).parent / 'UnattendedTemplates/win_nt6_unattended.xml'
        import re
        template = template_source.read_text(encoding='utf-8-sig')
        template, removed = re.subn(r'\s*<ProductKey>\s*<Key>@@VBOX_INSERT_PRODUCT_KEY_ELEMENT@@</Key>\s*<WillShowUI>OnError</WillShowUI>\s*</ProductKey>', '', template)
        assert removed == 1, 'Unexpected vendor unattended template; review before installing'
        template_path = INFRA / 'server-evaluation-unattended-template.xml'
        template_path.write_text(template, encoding='utf-8')
        result = invoke([VBOX, 'unattended', 'install', VM, '--iso', str(iso), '--user', 'validator',
                         '--user-password-file', str(credential), '--admin-password-file', str(credential),
                         '--full-user-name', 'Chan KG Validation', '--hostname', 'chan-kg-clean-win2022.test.local',
                         '--image-index', '1', '--locale', 'en_US', '--country', 'US', '--time-zone', 'UTC',
                         '--install-additions', '--script-template', str(template_path), '--start-vm', 'headless'], timeout=180)
        # VirtualBox may include generated credentials in setup diagnostics: redact before retention.
        secret = credential.read_text(encoding='ascii')
        (RUN / 'vm-unattended-install.log').write_text((result.stdout + result.stderr).replace(secret, '[REDACTED]'), encoding='utf-8')
        print(json.dumps({'stage': 'unattended_install_started', 'vm': VM, 'iso_sha256': receipt['sha256']}), flush=True)
        wait_guest()
    elif args.phase == 'native':
        wait_guest(limit=300)
        standard = password_file('standard-password.txt').read_text(encoding='ascii')
        setup = rf"""
    $ErrorActionPreference='Stop'
    New-Item -ItemType Directory -Path '{GUEST_ROOT / 'work'}' -Force | Out-Null
    if (-not (Get-LocalUser -Name agentuser -ErrorAction SilentlyContinue)) {{
      $pw=ConvertTo-SecureString '{standard}' -AsPlainText -Force
      New-LocalUser -Name agentuser -Password $pw -PasswordNeverExpires | Out-Null
      Add-LocalGroupMember -Group Users -Member agentuser
    }}
    & icacls.exe '{GUEST_ROOT / 'work'}' /grant '*S-1-5-32-545:(OI)(CI)M' /T | Out-Null
    """
        guest(setup)
        built = json.loads((RUN / 'zip-build.json').read_text(encoding='utf-8'))
        copy_to(Path(built['archive']), str(GUEST_ROOT / 'agent.zip'))
        copy_to(SOURCE / 'validation-guest-native.ps1', str(GUEST_ROOT / 'validation-guest-native.ps1'))
        copy_to(SOURCE / 'validation-guest-container.ps1', str(GUEST_ROOT / 'validation-guest-container.ps1'))
        copy_to(INFRA / 'docker-29.6.2.zip', str(GUEST_ROOT / 'docker.zip'))
        invoke([VBOX, 'controlvm', VM, 'setlinkstate1', 'off'])
        machine = invoke([VBOX, 'showvminfo', VM, '--machinereadable']).stdout
        assert 'cableconnected1="off"' in machine, 'Guest NIC was not disconnected'
        (RUN / 'vm-native-isolation.txt').write_text(machine, encoding='utf-8')
        result = guest(f"$ProgressPreference='SilentlyContinue'; [Console]::OutputEncoding=[Text.UTF8Encoding]::new($false); & '{GUEST_ROOT / 'validation-guest-native.ps1'}' -Archive '{GUEST_ROOT / 'agent.zip'}' -Output '{GUEST_ROOT / 'work'}' -ExpectedSHA256 '{built['sha256']}'", standard=True, timeout=1200, check=False)
        (RUN / 'native-guest-execution.log').write_text(result.stdout + result.stderr, encoding='utf-8')
        collect()
        assert result.returncode == 0, 'Native guest execution failed; inspect collected receipts and log'
        receipt = json.loads((RUN / 'native-guest-receipt.json').read_text(encoding='utf-8-sig'))
        assert receipt['passed'] and receipt['zip_sha256'] == built['sha256']
        print(json.dumps({'stage': 'native_guest_verified', 'archive_sha256': built['sha256']}), flush=True)
    elif args.phase in ('container', 'container-start'):
        native = json.loads((RUN / 'native-guest-receipt.json').read_text(encoding='utf-8-sig'))
        assert native['passed'], 'Native guest verification must pass first'
        installed = guest("$ProgressPreference='SilentlyContinue'; [Console]::Write((Get-WindowsFeature Containers).Installed)")
        if installed.stdout.strip() != 'True':
            print(json.dumps({'stage': 'enabling_guest_containers'}), flush=True)
            result = guest(f"$ProgressPreference='SilentlyContinue'; & '{GUEST_ROOT / 'validation-guest-container.ps1'}' -Root '{GUEST_ROOT}' -Phase enable", timeout=300)
            (RUN / 'guest-container-feature.log').write_text(result.stdout + result.stderr, encoding='utf-8')
            guest('shutdown.exe /r /t 3', timeout=30)
            time.sleep(20)
            wait_guest()
        invoke([VBOX, 'controlvm', VM, 'setlinkstate1', 'on'])
        copy_to(SOURCE / 'validation-guest-container.ps1', str(GUEST_ROOT / 'validation-guest-container.ps1'))
        if args.phase == 'container-start':
            task = 'ChanKGContainer-' + GUEST_ROOT.name
            command = f"& '{GUEST_ROOT / 'validation-guest-container.ps1'}' -Root '{GUEST_ROOT}' -Phase verify *> '{GUEST_ROOT / 'work/container-task.log'}'"
            import base64
            encoded = base64.b64encode(command.encode('utf-16-le')).decode('ascii')
            task_code = rf"""
$ErrorActionPreference='Stop'
$name='{task}'
if (Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue) {{ throw 'Existing validation task must be inspected, not replaced.' }}
$action=New-ScheduledTaskAction -Execute '{GUEST_PS}' -Argument '-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -EncodedCommand {encoded}'
$settings=New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 12) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName $name -Action $action -User SYSTEM -RunLevel Highest -Settings $settings | Out-Null
Start-ScheduledTask -TaskName $name
[ordered]@{{task=$name;state=(Get-ScheduledTask -TaskName $name).State.ToString()}} | ConvertTo-Json
"""
            result = guest(task_code, timeout=90)
            (RUN / 'container-task-start.json').write_text(result.stdout, encoding='utf-8')
            print(result.stdout.strip(), flush=True)
            raise SystemExit(0)
        print(json.dumps({'stage': 'pulling_official_image_and_verifying_actual_zip_container'}), flush=True)
        result = guest(f"$ProgressPreference='SilentlyContinue'; & '{GUEST_ROOT / 'validation-guest-container.ps1'}' -Root '{GUEST_ROOT}' -Phase verify", timeout=7200, check=False)
        (RUN / 'container-guest-execution.log').write_text(result.stdout + result.stderr, encoding='utf-8')
        collect()
        assert result.returncode == 0, 'Container execution failed; inspect collected receipts and log'
        receipt = json.loads((RUN / 'container-guest-receipt.json').read_text(encoding='utf-8-sig'))
        assert receipt['passed'], receipt
        print(json.dumps({'stage': 'actual_windows_container_verified', 'base_image': receipt['base_image_digests']}), flush=True)
    elif args.phase == 'container-status':
        task = 'ChanKGContainer-' + GUEST_ROOT.name
        result = guest(rf"$ProgressPreference='SilentlyContinue'; $task=Get-ScheduledTask -TaskName '{task}'; $info=Get-ScheduledTaskInfo -TaskName '{task}'; [ordered]@{{task='{task}';state=$task.State.ToString();last_result=$info.LastTaskResult;last_run=$info.LastRunTime.ToString('o')}} | ConvertTo-Json; Get-Content -LiteralPath '{GUEST_ROOT / 'work/container-task.log'}' -Tail 12 -ErrorAction SilentlyContinue; Get-Content -LiteralPath '{GUEST_ROOT / 'work/container-guest-receipt.json'}' -Raw -ErrorAction SilentlyContinue", timeout=90, check=False)
        print(result.stdout[-7000:], flush=True)
    else:
        collect()
