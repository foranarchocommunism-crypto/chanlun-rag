"""Build and verify a docs-only portable patch without changing the retrieval core."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil
import subprocess
import zipfile
import sys

repo = Path(__file__).resolve().parents[1]
version = json.loads((repo / 'source/package.json').read_text(encoding='utf-8'))['version']
assert version == '0.4.2'
name = f'chanlun-rag-{version}-windows-x64'
base = repo / 'release/chanlun-rag-0.4.1-windows-x64'
stage = repo / 'source/build/documentation-release' / name
archive = repo / 'archives' / (name + '.zip')
records = repo / '验收记录'
sha = lambda p: hashlib.file_digest(p.open('rb'), 'sha256').hexdigest()
mode = sys.argv[1] if len(sys.argv) > 1 else 'build'

if mode == 'build':
    assert not stage.exists(), 'Preserve existing build evidence'
    for line in (base / 'checksums.sha256').read_text(encoding='utf-8').splitlines():
        digest, rel = line.split('  ', 1)
        p = (base / rel).resolve()
        assert p.is_relative_to(base.resolve()) and sha(p) == digest, rel
    shutil.copytree(base, stage, ignore=shutil.ignore_patterns('连接资料'))
    for folder in ['src', 'bin']:
        for p in (repo / 'source' / folder).glob('*.mjs'):
            assert sha(p) == sha(stage / 'app' / folder / p.name), str(p)
    for file in ['package.json', 'package-lock.json']:
        shutil.copy2(repo / 'source' / file, stage / 'app' / file)
    for file in ['README.md', '开始使用.md', 'INSTALL_FOR_AGENT.md', 'AI安装提示词.txt']:
        text = (repo / file).read_text(encoding='utf-8')
        if file == 'README.md':
            for rel in ['验收记录/入门发布验证.md', 'docs/资料保留说明.md', 'source/docs/fixed-release.md']:
                text = text.replace('](' + rel + ')', '](https://github.com/foranarchocommunism-crypto/chanlun-rag/blob/main/' + rel + ')')
        (stage / file).write_text(text, encoding='utf-8', newline='\n')
    (stage / 'docs/assets').mkdir(parents=True, exist_ok=True)
    shutil.copy2(repo / 'docs/assets/readme-cover.png', stage / 'docs/assets/readme-cover.png')
    manifest = json.loads((stage / 'release-manifest.json').read_text(encoding='utf-8'))
    manifest.update(product_version=version, built_at=datetime.now(timezone.utc).isoformat(),
                    code_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, encoding='ascii').strip())
    manifest['documentation_patch'] = {'base_version': '0.4.1',
        'base_archive_sha256': '957abe459d0e227ff93cdfe23c3caf8a2e30c39853796520e4dc17ddd7c300f1',
        'local_agent_guide': 'INSTALL_FOR_AGENT.md', 'guide_network_required': False,
        'retrieval_core_changed': False, 'knowledge_changed': False}
    (stage / 'release-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
    files = sorted(p for p in stage.rglob('*') if p.is_file() and p.name != 'checksums.sha256')
    (stage / 'checksums.sha256').write_text(''.join(sha(p)+'  '+p.relative_to(stage).as_posix()+'\n' for p in files), encoding='utf-8', newline='\n')
    print(json.dumps({'stage': str(stage), 'files': len(files)+1}), flush=True)
elif mode == 'zip':
    verified = json.loads((records / '0.4.2-打包目录运行验证.json').read_text(encoding='utf-8'))
    assert verified['passed'] and Path(verified['product_root']).resolve() == stage.resolve()
    assert not archive.exists()
    files = sorted(p for p in stage.rglob('*') if p.is_file() and '连接资料' not in p.relative_to(stage).parts)
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as output:
        for p in files: output.write(p, (Path(name) / p.relative_to(stage)).as_posix())
    archive.with_suffix('.zip.sha256').write_text(sha(archive)+'  '+archive.name+'\n', encoding='ascii', newline='\n')
    destination = repo / 'release' / name
    assert not destination.exists()
    with zipfile.ZipFile(archive) as zipped:
        for item in zipped.infolist():
            assert (repo / 'release' / item.filename).resolve().is_relative_to((repo / 'release').resolve())
        zipped.extractall(repo / 'release')
    receipt = {'version': version, 'archive': archive.name, 'sha256': sha(archive), 'bytes': archive.stat().st_size,
               'files': len(files), 'fresh_extraction': str(destination), 'execution_verified': False,
               'local_agent_guide_included': True, 'guide_network_required': False}
    (records / '0.4.2-ZIP与全新解压.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps(receipt, ensure_ascii=False), flush=True)
else:
    raise SystemExit('Use build or zip')
