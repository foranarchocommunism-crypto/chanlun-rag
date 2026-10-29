"""Use existing Git/gh protocols, checkpointing individual Release assets."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess
import hashlib
import json
import sys
import time
import re

root = Path(__file__).resolve().parents[1]
repository = 'foranarchocommunism-crypto/chanlun-rag'
tag = 'v0.4.1'
parts_root = root / 'archives/publication-parts'
parts_root.mkdir(exist_ok=True)
sha = lambda p: hashlib.file_digest(p.open('rb'), 'sha256').hexdigest()
def run(args, **kwargs):
    # Binary stdin prevents Windows from appending CR to Git tree entry names.
    if isinstance(kwargs.get('input'), str): kwargs['input'] = kwargs['input'].encode('utf-8')
    while True:
        try:
            return subprocess.check_output(args, cwd=root, stderr=subprocess.PIPE, **kwargs).decode('utf-8').strip()
        except subprocess.CalledProcessError as error:
            detail = (error.stderr or b'').decode('utf-8', errors='replace')
            if not transient(detail): raise
            print(json.dumps({'step': 'waiting_for_network', 'retry_seconds': 60}), flush=True)
            time.sleep(60)
def gh(*args): return run(['gh', *args])
def transient(detail):
    text = detail.lower()
    return any(x in text for x in ['timeout', 'error connecting', 'connection', 'eof', 'tls handshake', 'network is unreachable', 'temporarily unavailable', 'rate limit', 'context deadline', 'request canceled', 'stream error']) or bool(re.search(r'http 5\d\d', text))

if sys.argv[1] == 'prepare':
    files = []
    for kind, path in [('bundle', root / 'archives/chanlun-publication.bundle'), ('runtime', root / 'archives/chanlun-rag-0.4.1-windows-x64.zip')]:
        records = []
        with path.open('rb') as source:
            i = 0
            while data := source.read(16 * 1024 * 1024):
                name = f'transfer-{kind}-{i:04d}.part'
                target = parts_root / name
                digest = hashlib.sha256(data).hexdigest()
                if not target.exists(): target.write_bytes(data)
                assert target.stat().st_size == len(data) and sha(target) == digest
                records.append({'name': name, 'bytes': len(data), 'sha256': digest})
                i += 1
        files.append({'name': path.name, 'bytes': path.stat().st_size, 'sha256': sha(path), 'parts': records})
    assert files[1]['sha256'] == '957abe459d0e227ff93cdfe23c3caf8a2e30c39853796520e4dc17ddd7c300f1'
    refs = {r: run(['git', 'rev-parse', r]) for r in ['refs/heads/main', 'refs/heads/archive/development-main', 'refs/tags/v0.4.0', 'refs/tags/v0.4.1']}
    manifest = {'repository': repository, 'tag': tag, 'refs': refs, 'files': files}
    path = parts_root / 'publication-manifest.json'
    path.write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps({'parts': sum(len(f['parts']) for f in files), 'manifest_sha256': sha(path), 'refs': refs}), flush=True)
elif sys.argv[1] == 'upload':
    manifest = json.loads((parts_root / 'publication-manifest.json').read_text(encoding='utf-8'))
    releases = json.loads(gh('api', 'repos/' + repository + '/releases'))
    release = next(r for r in releases if r['tag_name'] == tag)
    assert release['draft'], 'Do not mutate a published release'
    existing = {a['name']: a for a in release['assets']}
    parts = [p for f in manifest['files'] for p in f['parts']]
    pending = [p for p in parts if existing.get(p['name'], {}).get('digest') != 'sha256:' + p['sha256']]
    progress_path = root / 'source/build/publication-upload-progress.json'
    def progress(completed):
        progress_path.write_text(json.dumps({'total': len(parts), 'existing_server_sha256_verified': len(parts)-len(pending),
            'new_uploads_acknowledged': completed, 'updated_at_unix': time.time()}, indent=2)+'\n', encoding='utf-8')
    progress(0)
    print(json.dumps({'already_uploaded_verified': len(parts)-len(pending), 'remaining': len(pending)}), flush=True)
    def upload(part):
        attempt = 0
        while True:
            attempt += 1
            try:
                subprocess.run(['gh', 'release', 'upload', tag, str(parts_root / part['name']), '--repo', repository, '--clobber'], cwd=root, check=True, timeout=240, capture_output=True)
                return part['name']
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
                detail = (error.stderr or b'').decode('utf-8', errors='replace') if isinstance(error, subprocess.CalledProcessError) else 'timeout'
                if not transient(detail):
                    (root / 'source/build/publication-last-upload-error.json').write_text(json.dumps({
                        'part': part['name'], 'attempt': attempt, 'error': detail[:1600], 'updated_at_unix': time.time()
                    }, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
                    raise
                print(json.dumps({'step': 'part_network_retry', 'part': part['name'], 'attempt': attempt, 'retry_seconds': 60}), flush=True)
                time.sleep(60)
    with ThreadPoolExecutor(max_workers=6) as workers:
        for i, result in enumerate(as_completed([workers.submit(upload, p) for p in pending]), 1):
            print(json.dumps({'completed_now': i, 'remaining_at_start': len(pending), 'part': result.result()}), flush=True)
            progress(i)
    assets = json.loads(gh('api', 'repos/' + repository + '/releases/' + str(release['id']) + '/assets?per_page=100'))
    assets = {a['name']: a for a in assets}
    assert all(assets.get(p['name'], {}).get('digest') == 'sha256:' + p['sha256'] for p in parts)
    gh('release', 'upload', tag, str(parts_root / 'publication-manifest.json'), '--repo', repository, '--clobber')
    print('All transfer parts and manifest uploaded and verified', flush=True)
elif sys.argv[1] == 'bootstrap':
    def blob(data): return run(['git', 'hash-object', '-w', '--stdin'], input=data)
    def tree(items): return run(['git', 'mktree'], input=''.join(f'{mode} {kind} {value}\t{name}\n' for mode, kind, value, name in items))
    workflow = blob((root / 'tools/publication-workflow.yml').read_text(encoding='utf-8'))
    worker = blob((root / 'tools/publication-worker.py').read_text(encoding='utf-8'))
    readme = blob('# Publication transfer\n\nThe product repository is being transferred from a verified local Git bundle. The final default branch will be main.\n')
    workflows = tree([('100644', 'blob', workflow, 'publish.yml')])
    github = tree([('040000', 'tree', workflows, 'workflows')])
    tools = tree([('100644', 'blob', worker, 'publication-worker.py')])
    top = tree([('040000', 'tree', github, '.github'), ('100644', 'blob', readme, 'README.md'), ('040000', 'tree', tools, 'tools')])
    previous = subprocess.run(['git', 'rev-parse', '--verify', 'refs/heads/publication-tools'], cwd=root, capture_output=True)
    parents = ['-p', previous.stdout.decode('ascii').strip()] if previous.returncode == 0 else []
    commit = run(['git', 'commit-tree', top, *parents, '-m', 'Bootstrap checksum-verified publication transfer'])
    run(['git', 'update-ref', 'refs/heads/publication-tools', commit])
    print(run(['git', '-c', 'http.version=HTTP/1.1', 'push', 'origin', 'publication-tools']), flush=True)
    gh('api', '--method', 'PATCH', 'repos/' + repository, '-f', 'default_branch=publication-tools')
    print('Publication-only branch initialized; application branches unchanged locally', flush=True)
else:
    raise SystemExit('Use prepare, upload, or bootstrap')
