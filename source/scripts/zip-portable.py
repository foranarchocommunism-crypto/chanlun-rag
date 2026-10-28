"""Package a verified release directory without replacing an existing archive."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import zipfile

parser = argparse.ArgumentParser()
parser.add_argument('--product', type=Path, required=True)
parser.add_argument('--run', type=Path, required=True)
args = parser.parse_args()
product, run = args.product.resolve(), args.run.resolve()
assert json.loads((run / 'local-portable-verification.json').read_text(encoding='utf-8-sig'))['passed']
archive = product.parent / (product.name + '.zip')
assert not archive.exists(), 'Use a new release directory instead of replacing a published ZIP'
files = sorted(p for p in product.rglob('*') if p.is_file())
with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as output:
    for i, path in enumerate(files):
        output.write(path, (Path(product.name) / path.relative_to(product)).as_posix())
        if (i + 1) % 2000 == 0:
            print(json.dumps({'packed': i + 1, 'total': len(files)}), flush=True)
with archive.open('rb') as stream:
    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
with zipfile.ZipFile(archive) as check:
    assert check.testzip() is None, 'ZIP CRC validation failed'
    assert len(check.namelist()) == len(files)
receipt = {
    'archive': str(archive), 'sha256': digest, 'bytes': archive.stat().st_size,
    'files': len(files), 'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'crc_checked': True, 'independent_vm_and_container_verification': 'pending_actual_zip_execution',
}
(run / 'zip-build.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
Path(str(archive) + '.sha256').write_text(digest + '  ' + archive.name + '\n', encoding='ascii')
print(json.dumps(receipt, ensure_ascii=False), flush=True)
