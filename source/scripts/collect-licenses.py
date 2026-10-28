from pathlib import Path
import hashlib
import json
import subprocess
import urllib.request
root = Path(__file__).resolve().parents[1]
version = subprocess.check_output(['node', '--version'], text=True).strip()
sources = {
    'NODE-LICENSE.txt': f'https://raw.githubusercontent.com/nodejs/node/{version}/LICENSE',
    'BGE-MODELS-MIT-LICENSE.txt': 'https://raw.githubusercontent.com/FlagOpen/FlagEmbedding/master/LICENSE',
}
records = []
for filename, url in sources.items():
    with urllib.request.urlopen(url, timeout=30) as response:
        data = response.read()
    (root / 'licenses' / filename).write_bytes(data)
    records.append({'file': filename, 'url': url, 'sha256': hashlib.sha256(data).hexdigest()})
(root / 'licenses/license-provenance.json').write_text(json.dumps({'node_version': version, 'assets': records}, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'licenses': [r['file'] for r in records]}))
