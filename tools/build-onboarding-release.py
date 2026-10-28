"""Build a tutorial-only patch from a checksum-verified immutable 0.4.0 runtime."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import zipfile
import sys

repo = Path(__file__).resolve().parents[1]
base = repo / 'release/chan-kg-agent-0.4.0-windows-x64'
name = 'chanlun-rag-0.4.1-windows-x64'
stage = repo / 'source/build/onboarding' / name
archive = repo / 'archives' / (name + '.zip')
sha = lambda path: hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()

if sys.argv[1:] == ['--zip']:
    report = json.loads((repo / '验收记录/0.4.1-打包目录运行验证.json').read_text(encoding='utf-8'))
    assert report['passed'] and Path(report['product_root']).resolve() == stage.resolve()
    assert not archive.exists(), 'Never overwrite a published ZIP'
    files = sorted(p for p in stage.rglob('*') if p.is_file() and '连接资料' not in p.relative_to(stage).parts)
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as output:
        for p in files: output.write(p, (Path(name) / p.relative_to(stage)).as_posix())
    archive.with_suffix('.zip.sha256').write_text(sha(archive) + '  ' + archive.name + '\n', encoding='ascii')
    destination = repo / 'release' / name
    assert not destination.exists()
    with zipfile.ZipFile(archive) as zipped:
        for item in zipped.infolist():
            assert (repo / 'release' / item.filename).resolve().is_relative_to((repo / 'release').resolve())
        zipped.extractall(repo / 'release')
    receipt = {'archive': archive.name, 'sha256': sha(archive), 'bytes': archive.stat().st_size,
               'files': len(files), 'fresh_extraction': str(destination), 'execution_verified': False}
    (repo / '验收记录/0.4.1-ZIP与全新解压.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(receipt, ensure_ascii=False), flush=True)
    raise SystemExit()

assert not stage.exists(), 'Preserve previous staging evidence'
for line in (base / 'checksums.sha256').read_text(encoding='utf-8').splitlines():
    digest, rel = line.split('  ', 1)
    path = (base / rel).resolve()
    assert path.is_relative_to(base.resolve()) and sha(path) == digest, rel
shutil.copytree(base, stage)
for file in ['package.json', 'package-lock.json']:
    shutil.copy2(repo / 'source' / file, stage / 'app' / file)
shutil.copytree(repo / 'source/onboarding', stage / 'onboarding')
guide = (repo / '开始使用.md').read_text(encoding='utf-8')
(stage / '开始使用.md').write_text(guide, encoding='utf-8')
readme = (repo / 'README.md').read_text(encoding='utf-8')
for rel in ['验收记录/入门发布验证.md', 'docs/资料保留说明.md', 'source/docs/fixed-release.md']:
    readme = readme.replace('](' + rel + ')', '](https://github.com/foranarchocommunism-crypto/chanlun-rag/blob/main/' + rel + ')')
(stage / 'README.md').write_text(readme, encoding='utf-8')
for label, mode in [('开始连接', 'generate'), ('检查是否正常', 'check'), ('合并已有配置', 'merge')]:
    cmd = '@echo off\r\nsetlocal\r\nchcp 65001 >nul\r\n"%~dp0runtime\\x64\\node.exe" "%~dp0onboarding\\connect.mjs" ' + mode + '\r\nset "CHANLUN_RESULT=%errorlevel%"\r\npause\r\nexit /b %CHANLUN_RESULT%\r\n'
    (stage / (label + '.cmd')).write_bytes(cmd.encode('utf-8'))
manifest = json.loads((stage / 'release-manifest.json').read_text(encoding='utf-8'))
manifest.update(product_version='0.4.1', display_name='缠论RAG',
    code_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip())
manifest['onboarding_patch'] = {'base_version': '0.4.0', 'base_archive_sha256': '7780ab2e580ad5782e71a231e4e676b35c622ed86934045201cad2e61af793cf',
    'retrieval_core_changed': False, 'knowledge_changed': False, 'gui_clients': ['Codex', 'Claude Desktop', 'WorkBuddy'],
    'source': 'source/onboarding/connect.mjs', 'clean_windows_verified': False}
manifest['entrypoints'] += ['开始连接.cmd', '检查是否正常.cmd', '合并已有配置.cmd']
(stage / 'release-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
for p in (repo / 'source/src').glob('*.mjs'):
    assert sha(p) == sha(stage / 'app/src' / p.name), p.name
files = sorted(p for p in stage.rglob('*') if p.is_file() and p.name != 'checksums.sha256')
(stage / 'checksums.sha256').write_text(''.join(sha(p)+'  '+p.relative_to(stage).as_posix()+'\n' for p in files), encoding='utf-8')
print(json.dumps({'stage': str(stage), 'files': len(files), 'version': '0.4.1'}, ensure_ascii=False), flush=True)
