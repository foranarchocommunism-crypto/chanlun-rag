"""Read-only duplicate audit. Deletion uses the separately checked PowerShell plan."""
import hashlib
import json
from pathlib import Path
import re
import zipfile

workspace = Path(__file__).resolve().parents[2]
run = workspace / 'validation-runs/x64-delivery-20261023'
expected = {
    'chan-kg-agent-0.2.0-307029129712': '39e0fc6038f88fd6ebeb4145f80465ef0ddb394f4901c6a14ad6a62b90d9542b',
    'chan-kg-agent-0.2.1-307029129712': '18677eed84f8d4cfd2690a28ce2e2eb1acd4857e0a9ba51a9d2e04c9850502a7',
    'chan-kg-agent-0.3.0-307029129712': '1d827fbfc168b16ef8de99ac689df2f8b737f3b7e9237eed4737a7e897ece4af',
    'chan-knowledge-20261022-307029129712': '80d13cfacca2c09cebf318579c27168771575c3a5213a50b319da033ae68d6dc',
}

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

verified = []
for name, archive_hash in expected.items():
    archive = workspace / 'deliveries' / (name + '.zip')
    assert digest(archive) == archive_hash, archive
    with zipfile.ZipFile(archive) as bundle:
        checksum_name = 'SHA256SUMS.txt' if name.startswith('chan-knowledge-') else 'checksums.sha256'
        checksum = bundle.read(name + '/' + checksum_name)
        hashes = {}
        for line in checksum.decode('utf-8-sig').splitlines():
            match = re.fullmatch(r'([0-9a-fA-F]{64})\s+\*?(.+)', line)
            assert match, line
            hashes[match[2].replace('\\', '/')] = match[1].lower()
        hashes[checksum_name] = hashlib.sha256(checksum).hexdigest()
        targets = [workspace/'deliveries'/name]
        if name == 'chan-kg-agent-0.2.0-307029129712':
            targets.append(workspace/'validation-runs/移位验收 空格路径'/name)
        for directory in targets:
            if not directory.exists():
                continue
            assert directory.resolve().is_relative_to(workspace.resolve()) and not directory.is_symlink()
            files = {p.relative_to(directory).as_posix(): p for p in directory.rglob('*') if p.is_file()}
            assert files.keys() == hashes.keys(), 'An old extraction has unique or missing files: ' + str(directory)
            for relative, path in files.items():
                assert not path.is_symlink() and digest(path) == hashes[relative], path
            verified.append({'directory': str(directory), 'archive': str(archive), 'archive_sha256': archive_hash,
                             'files': len(files), 'bytes': sum(p.stat().st_size for p in files.values()),
                             'all_file_sha256_match_archive_manifest': True})
            print(json.dumps({'duplicate_verified': str(directory), 'files': len(files)}, ensure_ascii=False), flush=True)
(run/'verified-duplicate-artifacts.json').write_text(json.dumps({'verified': verified}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
