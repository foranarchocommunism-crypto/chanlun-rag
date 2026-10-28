"""Preserve old releases; zip the verified candidate and extract to a new path."""
import hashlib
import json
import zipfile
import datetime
import sys
from pathlib import Path

app = Path(__file__).resolve().parents[1]
version = json.loads((app / 'package.json').read_text(encoding='utf-8'))['version']
product = app.parent / 'deliveries' / f'chan-kg-agent-{version}-windows-x64-307029129712'
run = app / 'build/graph-v2/acceptance'
local = json.loads((run / 'local-portable-verification.json').read_text(encoding='utf-8'))
assert local['passed'] and Path(local['product_root']).resolve() == product.resolve()
archive = product.parent / (product.name + '.zip')
target = app.parent / ('验收 自然竞争' if version.endswith('rc.2') else '验收 二跳')
extract_only = '--extract-only' in sys.argv
assert archive.exists() if extract_only else not archive.exists(), 'Preserve an existing archive; --extract-only explicitly reuses it'
assert not target.exists(), 'Fresh extraction requires a new directory'
files = sorted(p for p in product.rglob('*') if p.is_file())
if not extract_only:
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as output:
        for i, path in enumerate(files):
            output.write(path, (Path(product.name) / path.relative_to(product)).as_posix())
            if (i + 1) % 2000 == 0:
                print(json.dumps({'packed': i + 1, 'total': len(files)}), flush=True)
with archive.open('rb') as stream:
    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
with zipfile.ZipFile(archive) as source:
    assert len(source.namelist()) == len(files)
    for item in source.infolist():
        assert (target / item.filename).resolve().is_relative_to(target.resolve())
    source.extractall(target)  # validates each member's CRC while extracting
receipt = {'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'archive': str(archive),
           'archive_sha256': digest, 'archive_bytes': archive.stat().st_size, 'files': len(files),
           'fresh_extraction': True, 'extracted_path': str(target / product.name), 'crc_checked': True,
           'native_environment': 'current Windows x64 host; no independent clean host claim',
           'additional_platform_validation': 'outside current scope'}
(run / 'zip-extraction.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
Path(str(archive) + '.sha256').write_text(digest + '  ' + archive.name + '\n', encoding='ascii')
print(json.dumps(receipt, ensure_ascii=False), flush=True)
