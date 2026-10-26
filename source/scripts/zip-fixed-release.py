"""Archive a verified staging artifact and freshly extract into the formal repository."""
from pathlib import Path
import json
import hashlib
import zipfile

repo = Path.home() / 'Desktop' / '缠论知识检索正式版'
stage = repo / 'source/build/formal-release/product'
verification = json.loads((repo / '验收记录/打包目录运行验证.json').read_text(encoding='utf-8'))
assert verification['passed'] and Path(verification['product_root']).resolve() == stage.resolve()
name = 'chan-kg-agent-0.4.0-windows-x64'
archive = repo / 'archives' / (name + '.zip')
target = repo / 'release' / name
assert not archive.exists() and not target.exists(), 'Preserve previous artifacts; archive/extraction must be new'
files = sorted(p for p in stage.rglob('*') if p.is_file())
with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as output:
    for i, path in enumerate(files):
        output.write(path, (Path(name) / path.relative_to(stage)).as_posix())
        if (i + 1) % 2000 == 0: print(json.dumps({'packed': i + 1, 'total': len(files)}), flush=True)
with archive.open('rb') as stream: digest = hashlib.file_digest(stream, 'sha256').hexdigest()
with zipfile.ZipFile(archive) as source:
    assert len(source.namelist()) == len(files)
    for item in source.infolist(): assert (repo / 'release' / item.filename).resolve().is_relative_to((repo / 'release').resolve())
    source.extractall(repo / 'release')
receipt = {'archive': str(archive), 'archive_sha256': digest, 'archive_bytes': archive.stat().st_size,
           'files': len(files), 'fresh_extraction': True, 'crc_checked_while_extracting': True,
           'extracted_path': str(target), 'verification_still_required': True}
(repo / '验收记录/ZIP与全新解压.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
archive.with_suffix('.zip.sha256').write_text(digest + '  ' + archive.name + '\n', encoding='ascii')
print(json.dumps({'archive_sha256': digest, 'files': len(files), 'fresh_extraction': True}), flush=True)
