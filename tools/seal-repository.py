"""Seal versioned repository files; runtime files have their own verified checksum list."""
from pathlib import Path
import subprocess
import hashlib
from concurrent.futures import ThreadPoolExecutor

repo = Path(__file__).resolve().parents[1]
names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=repo).decode('utf-8').split('\0')
names = sorted(n for n in names if n and n != '仓库文件清单.sha256')

def entry(name):
    with (repo / name).open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return digest + '  ' + name + '\n'

with ThreadPoolExecutor(max_workers=4) as workers:
    lines = list(workers.map(entry, names))
(repo / '仓库文件清单.sha256').write_text(''.join(lines), encoding='utf-8', newline='\n')
print({'sealed_versioned_files': len(lines), 'runtime_scope': 'Each Release ZIP contains its own checksums.sha256; archive digest is recorded in 发布状态.json'}, flush=True)
