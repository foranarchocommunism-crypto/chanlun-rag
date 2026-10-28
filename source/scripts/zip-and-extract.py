"""Seal the actual product into a ZIP and extract that ZIP to a moved Unicode/space path."""
from pathlib import Path
import datetime
import hashlib
import json
import time
import zipfile

root = Path(__file__).resolve().parents[2]
package = root / 'deliveries/chan-kg-agent-0.2.0-307029129712'
run = root / 'validation-runs/agent-implementation-20261022'
verification = json.loads((run / 'm7-directory-verification.json').read_text(encoding='utf-8'))
assert verification['passed'], 'Verify the actual directory before creating the final ZIP'
archive = package.with_suffix('.zip')
# with_suffix would truncate the dotted product version: use the full directory name.
archive = package.parent / (package.name + '.zip')
target = root / 'validation-runs/移位验收 空格路径'
assert not archive.exists(), 'Preserve an already published archive'
assert not target.exists(), 'Use a new extraction directory instead of overwriting'
assert target.resolve().is_relative_to((root / 'validation-runs').resolve())
files = sorted(p for p in package.rglob('*') if p.is_file())
start = time.monotonic()
with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as output:
    for i, path in enumerate(files):
        output.write(path, (Path(package.name) / path.relative_to(package)).as_posix())
        if (i + 1) % 1000 == 0:
            print(json.dumps({'zipped_files': i + 1, 'total': len(files), 'elapsed_seconds': time.monotonic() - start}), flush=True)
digest = hashlib.sha256()
with archive.open('rb') as stream:
    for block in iter(lambda: stream.read(1024 * 1024), b''):
        digest.update(block)
with zipfile.ZipFile(archive) as source:
    assert len(source.namelist()) == len(files)
    for item in source.infolist():
        assert (target / item.filename).resolve().is_relative_to(target.resolve())
    source.extractall(target)
result = {'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'archive': str(archive), 'archive_bytes': archive.stat().st_size,
          'sha256': digest.hexdigest(), 'files': len(files), 'extracted_directory': str(target / package.name),
          'extracted_from_actual_zip': True, 'unicode_and_space_path': True, 'archive_crc_checked_during_extraction': True,
          'independent_windows_environment': 'deferred_by_user', 'elapsed_seconds': time.monotonic() - start}
(run / 'm7-zip-extraction.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
Path(str(archive) + '.sha256').write_text(digest.hexdigest() + '  ' + archive.name + '\n', encoding='ascii')
print(json.dumps(result, ensure_ascii=False), flush=True)
