"""Check remote identity and public download, without treating local Git commits as uploaded."""
from pathlib import Path
import subprocess
import json
import hashlib
import urllib.request

root = Path(__file__).resolve().parents[1]
repository = 'foranarchocommunism-crypto/chanlun-rag'
def gh(path): return json.loads(subprocess.check_output(['gh', 'api', 'repos/' + repository + path], encoding='utf-8'))
def ref(name): return subprocess.check_output(['git', 'rev-parse', name], cwd=root, encoding='ascii').strip()
report = {'passed': False, 'checks': [], 'problems': []}
def check(name, condition):
    report['checks'].append({'name': name, 'passed': bool(condition)})
    if not condition: report['problems'].append(name)

metadata = gh('')
check('public_repository_with_main_default', metadata['visibility'] == 'public' and metadata['default_branch'] == 'main')
remote = {r['ref']: r['object']['sha'] for kind in ['heads', 'tags'] for r in gh('/git/matching-refs/' + kind + '/')}
for name in ['refs/heads/main', 'refs/heads/archive/development-main', 'refs/tags/v0.4.0', 'refs/tags/v0.4.1']:
    check('exact_' + name, remote.get(name) == ref(name))
release = next(r for r in gh('/releases') if r['tag_name'] == 'v0.4.1')
check('release_published', not release['draft'])
archive = root / 'archives/chanlun-rag-0.4.1-windows-x64.zip'
expected_sha = '957abe459d0e227ff93cdfe23c3caf8a2e30c39853796520e4dc17ddd7c300f1'
assets = {a['name']: a for a in release['assets']}
runtime = assets.get(archive.name, {})
check('runtime_size_and_server_sha256', runtime.get('size') == archive.stat().st_size and runtime.get('digest') == 'sha256:' + expected_sha)
checksum = archive.with_suffix('.zip.sha256')
check('checksum_asset', assets.get(checksum.name, {}).get('digest') == 'sha256:' + hashlib.sha256(checksum.read_bytes()).hexdigest())
check('only_user_runtime_and_checksum_assets', set(assets) == {archive.name, checksum.name})
if not release['draft'] and runtime:
    try:
        with urllib.request.urlopen(urllib.request.Request(runtime['browser_download_url'], method='HEAD'), timeout=60) as response:
            check('anonymous_download_head', response.status == 200 and int(response.headers['Content-Length']) == archive.stat().st_size)
    except Exception as error:
        check('anonymous_download_head', False)
        report['download_error'] = type(error).__name__ + ': ' + str(error)
report['passed'] = not report['problems']
report['remote_refs'] = remote
report['release_url'] = release['html_url']
report['archive_sha256'] = runtime.get('digest')
(root / '验收记录/GitHub发布核对.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'passed': report['passed'], 'problems': report['problems']}), flush=True)
raise SystemExit(0 if report['passed'] else 1)
