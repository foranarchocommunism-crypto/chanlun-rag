"""Preserve source/audit materials in the code repository, never in the user ZIP."""
from pathlib import Path
import os, json, hashlib, shutil

repo = Path(__file__).resolve().parents[1]
original_root = Path.home() / 'Desktop/RAG'
original = original_root / 'chan-kg-agent'
records = []
excluded = []
def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()
def retain(source, target):
    if source.is_dir():
        for base, dirs, files in os.walk(source):
            kept = []
            for name in dirs:
                generated = name == '__pycache__' or name == 'node_modules' or (
                    'validation-runs' in source.parts and name.startswith('chan-kg-agent-'))
                if generated:
                    excluded.append({'path': str(Path(base) / name), 'reason': 'generated cache or unpacked runtime; retained reports and fixtures separately'})
                else: kept.append(name)
            dirs[:] = kept
            for name in files:
                if name.endswith('.pyc'): continue
                path = Path(base) / name
                retain(path, target / path.relative_to(source))
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    value = digest(source)
    if target.exists():
        assert digest(target) == value, f'Existing file differs: {target}'
    else:
        try: shutil.copyfile(source, target)
        except Exception:
            print(json.dumps({'copy_failed_source': str(source), 'target': str(target)}, ensure_ascii=True), flush=True)
            raise
    assert digest(target) == value
    records.append({'from': source.relative_to(original_root).as_posix(), 'to': target.relative_to(repo).as_posix(),
                    'sha256': value, 'bytes': source.stat().st_size})

for name in ['curation', 'tools', 'scripts', 'evaluation', 'docs/research']:
    retain(original / name, repo / 'source' / name)
retain(original / 'docs/implementation-status.json', repo / 'source/docs/implementation-status.json')
retain(original_root / 'validation-runs', repo / 'validation-runs')
for name in ['graph-v2', 'final-figure-audit']:
    retain(original / 'build' / name, repo / 'research-artifacts' / name)
for name in ['AGENTS.md', '完整实施计划.md', '交付与验收报告.md', '架构终审报告.md']:
    retain(original_root / name, repo / 'docs/development-history' / name)
receipt = {'client_date': '2026-10-28', 'source_directory': str(original_root), 'repository': str(repo),
           'copied_or_verified_files': len(records), 'bytes': sum(x['bytes'] for x in records),
           'all_sha256_matched': True, 'user_runtime_zip_modified': False, 'excluded': excluded, 'records': records}
(repo / '验收记录/开发资料保留核对-20261028.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'files': len(records), 'mib': round(receipt['bytes']/1048576, 2), 'all_hashes_matched': True}), flush=True)
