"""Report common credential formats without printing candidate secret values."""
from pathlib import Path
import subprocess
import re
import json

r = Path(__file__).resolve().parents[1]
git = lambda args, **kw: subprocess.check_output(['git', *args], cwd=r, encoding='utf-8', **kw)
objects = git(['cat-file', '--batch-check=%(objectname) %(objecttype) %(objectsize) %(rest)'], input=git(['rev-list', '--objects', '--all']))
patterns = {
    'github_token': r'(?<![A-Za-z0-9])(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,})',
    'private_key': r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
    'openai_key': r'(?<![A-Za-z0-9])sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{40,}',
    'workbuddy_token': r'wbSeedToken[=:][^\s]{20,}',
    'aws_key': r'\bAKIA[0-9A-Z]{16}\b',
}
ignore = {'.git', 'node_modules', 'models', 'build', 'release', 'archives', '__pycache__'}
extensions = {'.json', '.jsonl', '.md', '.txt', '.py', '.mjs', '.js', '.ps1', '.toml', '.yaml', '.yml', '.cmd', '.log', '.tap'}
hits = []
count = 0
for p in r.rglob('*'):
    if not p.is_file() or set(p.relative_to(r).parts) & ignore or p.suffix.lower() not in extensions:
        continue
    try: content = p.read_text(encoding='utf-8')
    except (UnicodeError, OSError): continue
    count += 1
    for label, pattern in patterns.items():
        if re.search(pattern, content): hits.append({'path': p.relative_to(r).as_posix(), 'type': label})
seen = set()
large = []
history_count = 0
for line in objects.splitlines():
    parts = line.split(' ', 3)
    if len(parts) < 4 or parts[1] != 'blob': continue
    if int(parts[2]) > 50000000: large.append({'bytes': int(parts[2]), 'path': parts[3]})
    if parts[0] in seen or int(parts[2]) > 12000000 or Path(parts[3]).suffix.lower() not in extensions: continue
    seen.add(parts[0])
    try: content = subprocess.check_output(['git', 'cat-file', 'blob', parts[0]], cwd=r).decode('utf-8')
    except UnicodeError: continue
    history_count += 1
    for label, pattern in patterns.items():
        if re.search(pattern, content): hits.append({'path': parts[3], 'blob': parts[0], 'type': label})
report = {'files_scanned': count, 'unique_history_text_blobs_scanned': history_count, 'credential_pattern_hits': hits,
          'historical_blobs_above_50MB': large, 'scope': 'Common credential formats; not a guarantee of detecting arbitrary secrets'}
(r / '验收记录/公开发布扫描.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False), flush=True)
raise SystemExit(1 if hits or any(x['bytes'] >= 100000000 for x in large) else 0)
