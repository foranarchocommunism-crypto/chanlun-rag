"""Freeze and back up the pre-migration runtime, source, evaluation and data inputs."""
from pathlib import Path
import datetime
import hashlib
import json
import shutil
import subprocess
import zipfile

agent = Path(__file__).resolve().parents[1]
root = agent.parent
run = root / 'validation-runs' / 'agent-implementation-20261022'
run.mkdir(parents=True, exist_ok=True)
receipt = run / 'baseline.json'
if receipt.exists():
    raise SystemExit('Baseline already frozen; preserve it and use its existing receipt.')

def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()

expected = {
    'shared-knowledge/v0.1.0/graph.sqlite': '3463d772e607c6e89104c17c02c6b3656cca766f444d226c011fb9d8a9017271',
    'shared-knowledge/v0.1.0/manifest.json': '4eafc2500d74089d2b8a113598afb83470c4553d53748a5ca6207f614c238aac',
    'volume_1.pdf': 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b',
    'volume_2.pdf': '5332cd1b60381c47ceb81358db6bbb47882efd074fc5c869dcc3002aaed1b5c0',
}
for relative, digest in expected.items():
    assert sha(root / relative) == digest, f'Baseline changed: {relative}'

protected = []
for directory in ['bin', 'src', 'scripts', 'test', 'contracts', 'docs', 'evaluation', 'licenses']:
    protected.extend(p for p in (agent / directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
protected.extend(p for p in agent.iterdir() if p.is_file())
protected.extend([agent / 'curation/delivery-scope.json', root / '完整实施计划.md', root / 'AGENTS.md'])
protected = sorted(set(protected))
records = [{'path': p.relative_to(root).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in protected]
archive = run / 'pre-implementation-source.zip'
with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as output:
    for path in protected:
        output.write(path, path.relative_to(root).as_posix())

backup = run / 'baseline-knowledge'
backup.mkdir()
for filename in ['graph.sqlite', 'manifest.json']:
    source = root / 'shared-knowledge/v0.1.0' / filename
    shutil.copy2(source, backup / filename)
    assert sha(source) == sha(backup / filename)
for relative, digest in expected.items():
    assert sha(root / relative) == digest, f'Concurrent data change: {relative}'
result = {
    'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'objective': 'Implement 完整实施计划.md, M0-M7; do not narrow delivery scope',
    'baseline_graph_version': json.loads((backup / 'manifest.json').read_text(encoding='utf-8'))['graph_version'],
    'canonical_inputs': expected,
    'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=agent, text=True).strip(),
    'git_status': subprocess.check_output(['git', 'status', '--short'], cwd=agent, text=True).splitlines(),
    'protected_files': records,
    'source_backup': {'path': archive.name, 'sha256': sha(archive)},
    'knowledge_backup': {'path': backup.name, 'database_sha256': sha(backup / 'graph.sqlite')},
    'old_desktop_archive': 'User moved to Recycle Bin; not required or restored',
    'restore': 'Extract source archive to a separate directory; compare paths/hashes before restoring only intended files. Canonical baseline is in baseline-knowledge.',
}
receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'receipt': str(receipt), 'protected_files': len(records), 'source_archive_bytes': archive.stat().st_size}, ensure_ascii=False))
