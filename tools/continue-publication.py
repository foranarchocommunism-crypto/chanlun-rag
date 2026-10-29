"""Detached supervisor for the user-authorized publication; no application code changes."""
from pathlib import Path
from datetime import datetime, timezone
import subprocess
import json
import hashlib
import time
import sys
import shutil
import re

root = Path(__file__).resolve().parents[1]
repository = 'foranarchocommunism-crypto/chanlun-rag'
state_file = root / 'source/build/publication-background-state.json'
state_file.parent.mkdir(parents=True, exist_ok=True)
state = {'started_at': datetime.now(timezone.utc).isoformat(), 'status': 'running'}
def save(step, **extra):
    state.update(step=step, updated_at=datetime.now(timezone.utc).isoformat(), **extra)
    state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(step, flush=True)
def run(*args):
    previous_step = state.get('step', 'running')
    dispatch_started = datetime.now(timezone.utc)
    while True:
        try:
            result = subprocess.check_output(list(args), cwd=root, encoding='utf-8', stderr=subprocess.PIPE)
            if state.get('step') == 'waiting_for_network': save(previous_step, status='running')
            return result.strip()
        except subprocess.CalledProcessError as error:
            detail = error.stderr or ''
            transient = any(x in detail.lower() for x in ['timeout', 'error connecting', 'connection', 'eof', 'tls handshake', 'network is unreachable', 'temporarily unavailable', 'rate limit', 'context deadline', 'request canceled', 'stream error']) or bool(re.search(r'http 5\d\d', detail.lower()))
            if not transient: raise
            save('waiting_for_network', status='running', retry_seconds=60, operation=list(args[:3]))
            time.sleep(60)
            if args[:3] == ('gh', 'workflow', 'run'):
                # A timed-out dispatch may already have succeeded; never blindly duplicate it.
                recent = json.loads(gh('run', 'list', '--repo', repository, '--workflow', 'publish.yml', '--branch', 'publication-tools', '--limit', '1', '--json', 'databaseId,createdAt'))
                if recent and datetime.fromisoformat(recent[0]['createdAt'].replace('Z', '+00:00')) >= dispatch_started:
                    return ''
def gh(*args): return run('gh', *args)
def release():
    return next(r for r in json.loads(gh('api', 'repos/' + repository + '/releases')) if r['tag_name'] == 'v0.4.1')

try:
    save('waiting_for_existing_upload')
    if '--wait-pid' in sys.argv:
        pid = int(sys.argv[sys.argv.index('--wait-pid') + 1])
        # Wait only for the known uploader, never for an unrelated reused PID.
        query = f"$p=Get-CimInstance Win32_Process -Filter 'ProcessId={pid}'; if ($p -and $p.CommandLine -like '*resumable-publication.py upload*') {{ Wait-Process -Id {pid} -ErrorAction SilentlyContinue }}"
        subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', query], check=True)
    if release()['draft']:
        runs = json.loads(gh('run', 'list', '--repo', repository, '--workflow', 'publish.yml', '--branch', 'publication-tools', '--limit', '1', '--json', 'databaseId,status,conclusion,url'))
        if not runs or runs[0]['status'] == 'completed':
            save('resuming_and_verifying_uploaded_parts')
            while True:
                uploaded = subprocess.run([sys.executable, '-u', 'tools/resumable-publication.py', 'upload'], cwd=root)
                if uploaded.returncode == 0:
                    break
                assert release()['draft'], 'Release changed externally; refusing further uploads'
                save('retrying_incomplete_upload', status='running', retry_seconds=60, last_upload_exit_code=uploaded.returncode)
                time.sleep(60)
                save('resuming_and_verifying_uploaded_parts', status='running')
            manifest_path = root / 'archives/publication-parts/publication-manifest.json'
            manifest_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            save('dispatching_server_verification')
            gh('workflow', 'run', 'publish.yml', '--repo', repository, '--ref', 'publication-tools', '-f', 'manifest_sha256=' + manifest_sha)
            time.sleep(8)
            runs = json.loads(gh('run', 'list', '--repo', repository, '--workflow', 'publish.yml', '--branch', 'publication-tools', '--limit', '1', '--json', 'databaseId,status,conclusion,url'))
        assert runs, 'No dispatched workflow run found'
        run_id = str(runs[0]['databaseId'])
        save('waiting_for_server_publication', workflow_url=runs[0]['url'])
        while True:
            current = json.loads(gh('run', 'view', run_id, '--repo', repository, '--json', 'status,conclusion,url'))
            if current['status'] == 'completed':
                assert current['conclusion'] == 'success', 'Server publication failed: ' + current['url']
                break
            time.sleep(30)
    save('verifying_public_release')
    published = release()
    assert not published['draft']
    gh('api', '--method', 'PATCH', 'repos/' + repository, '-f', 'default_branch=main')
    subprocess.run([sys.executable, 'tools/verify-github-publication.py'], cwd=root, check=True)
    manifest_path = root / 'archives/publication-parts/publication-manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    expected = manifest['refs']['refs/heads/main']
    assert run('git', 'rev-parse', 'main') == expected and run('git', 'branch', '--show-current') == 'main'
    assert not run('git', 'diff', '--cached', '--name-only'), 'Existing user-staged changes require manual bookkeeping'
    own_files = ['tools/publication-worker.py', 'tools/publication-workflow.yml', 'tools/resumable-publication.py',
                 'tools/verify-github-publication.py', 'tools/continue-publication.py',
                 '验收记录/GitHub发布核对.json', '验收记录/发布传输清单.json', '发布状态.json']
    changed = set(run('git', '-c', 'core.quotepath=false', 'diff', '--name-only').splitlines())
    assert changed <= set(own_files), 'Unrelated user modifications require manual bookkeeping'
    shutil.copy2(manifest_path, root / '验收记录/发布传输清单.json')
    status_path = root / '发布状态.json'
    status = json.loads(status_path.read_text(encoding='utf-8'))
    status.update(status='released', ready_to_use=True, release_url=published['html_url'],
                  published_at=published['published_at'], publication_workflow=state.get('workflow_url'),
                  publication_receipt='验收记录/GitHub发布核对.json')
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    save('recording_verified_publication')
    run('git', 'add', '--', *own_files)
    subprocess.run([sys.executable, 'tools/seal-repository.py'], cwd=root, check=True)
    run('git', 'add', '--', '仓库文件清单.sha256')
    run('git', 'commit', '-m', 'Record verified GitHub release and resumable publication tooling')
    run('git', '-c', 'http.version=HTTP/1.1', '-c', 'http.lowSpeedTime=60', '-c', 'http.lowSpeedLimit=1024', 'push', 'origin', 'main')
    remote_main = run('git', 'ls-remote', 'origin', 'refs/heads/main').split()[0]
    assert remote_main == run('git', 'rev-parse', 'main')
    # Temporary local transport copies are owned by this operation; preserve user ZIPs.
    temporary = (root / 'archives/publication-parts').resolve()
    assert temporary.name == 'publication-parts' and temporary.is_relative_to((root / 'archives').resolve())
    assert (root / '验收记录/发布传输清单.json').read_bytes() == manifest_path.read_bytes()
    shutil.rmtree(temporary)
    bundle = (root / 'archives/chanlun-publication.bundle').resolve()
    assert bundle.name == 'chanlun-publication.bundle' and bundle.parent == (root / 'archives').resolve()
    bundle.unlink()
    save('complete', status='complete', remote_main=remote_main, release_url=published['html_url'])
except Exception as error:
    save('needs_attention', status='failed', error=type(error).__name__ + ': ' + str(error))
    raise
