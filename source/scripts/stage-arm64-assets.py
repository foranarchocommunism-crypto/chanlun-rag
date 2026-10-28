"""Stage pinned Windows ARM64 assets and audit their PE dependency closure.

Inputs are the unmodified official Node ZIP, lockfile-pinned sharp tarball,
and files expanded from the signed Microsoft ARM64 redistributable. No installer
is executed and no system DLL or global package is changed.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import shutil
import struct
import tarfile
import zipfile


def pe(path):
    data = path.read_bytes()
    u16 = lambda at: struct.unpack_from('<H', data, at)[0]
    u32 = lambda at: struct.unpack_from('<I', data, at)[0]
    start = u32(0x3c)
    assert data[start:start+4] == b'PE\0\0', path
    machine, count, optional_size = u16(start+4), u16(start+6), u16(start+20)
    optional = start+24
    assert u16(optional) == 0x20b, path
    sections = []
    for i in range(count):
        offset = optional + optional_size + i*40
        virtual_size, address, raw_size, raw_at = struct.unpack_from('<IIII', data, offset+8)
        sections.append((address, max(virtual_size, raw_size), raw_at))
    def file_at(rva):
        for address, size, raw_at in sections:
            if address <= rva < address+size:
                return raw_at+rva-address
        assert rva < u32(optional+60), (path, hex(rva))
        return rva
    def string(rva):
        at = file_at(rva)
        return data[at:data.index(0, at)].decode('ascii').lower()
    imports = []
    table = u32(optional+112+8)
    if table:
        at = file_at(table)
        while any(data[at:at+20]):
            imports.append(string(u32(at+12)))
            at += 20
    table = u32(optional+112+13*8)
    if table:
        at = file_at(table)
        while any(data[at:at+32]):
            assert u32(at) & 1, 'Only RVA-form delay imports are supported'
            imports.append(string(u32(at+4)))
            at += 32
    return {'machine': f'{machine:04x}', 'imports': sorted(set(imports))}


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


parser = argparse.ArgumentParser()
parser.add_argument('--inputs', type=Path, required=True)
args = parser.parse_args()
source = Path(__file__).resolve().parents[1]
inputs = args.inputs
stage = source / 'build/portable-platforms/arm64'
stage.mkdir(parents=True, exist_ok=True)
node_zip = inputs / 'node-v24.15.0-win-arm64.zip'
assert digest(node_zip) == 'c9eb7402eda26e2ba7e44b6727fc85a8de56c5095b1f71ebd3062892211aa116'
with zipfile.ZipFile(node_zip) as archive:
    (stage / 'node.exe').write_bytes(archive.read('node-v24.15.0-win-arm64/node.exe'))
assert digest(stage / 'node.exe') == '49a54c103f4919ce64199a043ef5cd309507de491d718085edee089cd8e87543'
lock = json.loads((source / 'package-lock.json').read_text(encoding='utf-8'))
sharp_entry = lock['packages']['node_modules/@img/sharp-win32-arm64']
sharp_tar = inputs / 'img-sharp-win32-arm64-0.35.5.tgz'
algorithm, expected = sharp_entry['integrity'].split('-', 1)
assert algorithm == 'sha512'
assert base64.b64encode(hashlib.sha512(sharp_tar.read_bytes()).digest()).decode() == expected
sharp = stage / 'sharp-win32-arm64'
sharp.mkdir(exist_ok=True)
with tarfile.open(sharp_tar, 'r:gz') as archive:
    for entry in archive:
        parts = Path(entry.name).parts
        assert parts[0] == 'package' and '..' not in parts and not entry.issym() and not entry.islnk()
        target = sharp.joinpath(*parts[1:])
        if entry.isdir():
            target.mkdir(parents=True, exist_ok=True)
        elif entry.isfile():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.extractfile(entry).read())
        else:
            raise ValueError(f'Unsupported archive entry: {entry.name}')
crt = {p.name.removesuffix('_arm64').lower(): p for p in (inputs / 'arm-current-runtime-files').glob('*.dll_arm64')}
native_paths = [stage / 'node.exe'] + list(sharp.rglob('*.dll')) + list(sharp.rglob('*.node'))
native_paths += list((source / 'node_modules/onnxruntime-node/bin/napi-v6/win32/arm64').glob('*'))
native_paths = [p for p in native_paths if p.suffix.lower() in ('.exe', '.dll', '.node')]
audit, needed = {}, set()
queue = native_paths[:]
while queue:
    path = queue.pop()
    key = str(path.relative_to(source)) if path.is_relative_to(source) else path.name
    if key in audit:
        continue
    entry = pe(path)
    assert entry['machine'] == 'aa64', (path, entry['machine'])
    audit[key] = entry
    for dependency in entry['imports']:
        if dependency in crt and dependency not in needed:
            needed.add(dependency)
            queue.append(crt[dependency])
        elif dependency.startswith(('msvcp140', 'vcruntime140', 'concrt140')) and dependency not in crt:
            raise ValueError(f'Missing CRT import {dependency} from {path}')
runtime = stage / 'native-runtime'
runtime.mkdir(exist_ok=True)
assets = []
for name in sorted(needed):
    assert pe(crt[name])['machine'] == 'aa64'
    target = runtime / name
    shutil.copyfile(crt[name], target)
    assets.append({'file': name, 'sha256': digest(target), 'machine': 'aa64',
                   'version': '14.51.36247.0', 'source_payload': crt[name].name})
license_from = inputs / 'arm-current-0/u4'
shutil.copyfile(license_from, stage / 'MSVC-RUNTIME-LICENSE.rtf')
manifest = {
    'arch': 'arm64', 'node': {'file': 'node.exe', 'version': 'v24.15.0', 'sha256': digest(stage / 'node.exe'),
    'url': 'https://nodejs.org/dist/v24.15.0/node-v24.15.0-win-arm64.zip', 'archive_sha256': digest(node_zip)},
    'sharp': {'version': sharp_entry['version'], 'url': sharp_entry['resolved'], 'integrity': sharp_entry['integrity']},
    'native_dependencies': assets, 'pe_import_audit': audit,
    'crt_source': {'url': 'https://aka.ms/vc14/vc_redist.arm64.exe', 'sha256': digest(inputs / 'vc_redist.arm64.current.exe'),
                   'version': '14.51.36247.0', 'authenticode': 'See arm64-asset-signatures.json for actual verification'},
    'excluded_mixed_arch_payload': {'file': 'vcruntime140_1.dll_arm64', 'actual_machine': pe(crt['vcruntime140_1.dll'])['machine'],
                                    'reason': 'Not imported by the ARM64 dependency closure; x64 compatibility payload'},
}
(stage / 'platform-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'staged': str(stage), 'node_sha256': manifest['node']['sha256'],
                  'native_modules_audited': len(audit), 'crt_files': sorted(needed)}))
