"""Restore an already locally verified ZIP with Git's standard binary patch format."""
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
import zipfile

repo = os.environ['GITHUB_REPOSITORY']
assert repo == 'foranarchocommunism-crypto/chanlun-rag'
tag = os.environ['RELEASE_TAG']
assert re.fullmatch(r'v\d+\.\d+\.\d+', tag)
expected_manifest = os.environ['MANIFEST_SHA256']
assert re.fullmatch('[0-9a-f]{64}', expected_manifest)
root = Path(os.environ['RUNNER_TEMP']) / ('verified-docs-' + tag)
root.mkdir()
def gh(*args): return subprocess.check_output(['gh', *args], encoding='utf-8')
def sha(path):
    with path.open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()
def release():
    return next(x for x in json.loads(gh('api', 'repos/' + repo + '/releases')) if x['tag_name'] == tag)
assert release()['draft'], 'Only an unpublished draft may be changed'
gh('release', 'download', tag, '--repo', repo, '--pattern', 'documentation-publication.json', '--dir', str(root))
manifest_path = root / 'documentation-publication.json'
assert sha(manifest_path) == expected_manifest
m = json.loads(manifest_path.read_text(encoding='utf-8'))
assert m['tag'] == tag and m['repository'] == repo
assert json.loads(gh('api', 'repos/' + repo + '/git/refs/tags/' + tag))['object']['sha'] == m['tag_commit']
for item in [m['base'], m['target']]:
    assert re.fullmatch(r'chanlun-rag-\d+\.\d+\.\d+-windows-x64\.zip', item['name'])
assert m['patch']['name'] == 'documentation-update.patch'
gh('release', 'download', m['base']['tag'], '--repo', repo, '--pattern', m['base']['name'], '--dir', str(root))
gh('release', 'download', tag, '--repo', repo, '--pattern', m['patch']['name'], '--dir', str(root))
base = root / m['base']['name']
patch = root / m['patch']['name']
assert sha(base) == m['base']['sha256'] and sha(patch) == m['patch']['sha256']
assert patch.stat().st_size == m['patch']['bytes']
headers = re.findall(br'^diff --git .*$', patch.read_bytes(), re.M)
assert headers == [b'diff --git a/base/runtime.zip b/target/runtime.zip']
shutil.copy2(base, root / 'runtime.zip')
subprocess.run(['git', 'apply', '--check', '--binary', '-p2', str(patch)], cwd=root, check=True)
subprocess.run(['git', 'apply', '--binary', '-p2', str(patch)], cwd=root, check=True)
restored = root / 'runtime.zip'
assert restored.stat().st_size == m['target']['bytes'] and sha(restored) == m['target']['sha256']
target = root / m['target']['name']
restored.rename(target)
prefix = target.stem + '/'
with zipfile.ZipFile(target) as zipped:
    for name in ['INSTALL_FOR_AGENT.md', 'AI安装提示词.txt', '开始使用.md', 'docs/assets/readme-cover.png']:
        assert prefix + name in zipped.namelist()
    guide = zipped.read(prefix + 'INSTALL_FOR_AGENT.md')
    prompt = zipped.read(prefix + 'AI安装提示词.txt')
    assert b'https://' not in guide + prompt and b'http://' not in guide + prompt
    assert json.loads(zipped.read(prefix + 'release-manifest.json'))['product_version'] == tag[1:]
print('Restored ZIP is byte-identical to the locally tested ZIP; local guide confirmed', flush=True)
checksum = target.with_suffix('.zip.sha256')
checksum.write_text(m['target']['sha256'] + '  ' + target.name + '\n', encoding='ascii', newline='\n')
assert release()['draft']
gh('release', 'upload', tag, str(target), str(checksum), '--repo', repo, '--clobber')
published = release()
asset = next(a for a in published['assets'] if a['name'] == target.name)
assert asset['digest'] == 'sha256:' + m['target']['sha256'] and asset['size'] == m['target']['bytes']
for a in published['assets']:
    if a['name'] in {'documentation-publication.json', 'documentation-update.patch'}:
        gh('api', '--method', 'DELETE', 'repos/' + repo + '/releases/assets/' + str(a['id']))
        time.sleep(1)
gh('release', 'edit', tag, '--repo', repo, '--draft=false', '--latest')
print('Published ' + tag + ' with the complete verified user ZIP', flush=True)
