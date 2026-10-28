"""Resume an official HTTPS test image and verify the vendor-published SHA-256.

The URL file may contain an expiring signed link obtained through the vendor UI.
It stays in the temporary infrastructure directory and is never printed.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
from urllib.parse import urlsplit

parser = argparse.ArgumentParser()
parser.add_argument('--url-file', type=Path, required=True)
parser.add_argument('--target', type=Path, required=True)
parser.add_argument('--expected-sha256', required=True)
parser.add_argument('--source-page', required=True)
parser.add_argument('--workers', type=int, default=8, choices=range(1, 25))
parser.add_argument('--part-mib', type=int, default=16, choices=[1, 2, 4, 8, 16])
args = parser.parse_args()
url = args.url_file.read_text(encoding='utf-8-sig').strip()
assert url.startswith('https://')
target = args.target.resolve()
parts = target.with_name(target.name + '.parts')
parts.mkdir(parents=True, exist_ok=True)
header_file = parts / 'head.txt'
head = subprocess.run(['curl.exe', '-sSfIL', '--connect-timeout', '20', '--max-time', '60', '-o', str(header_file), url], capture_output=True)
assert head.returncode == 0, 'Official download HEAD failed; inspect local header file, regenerate an expired link through the official page if needed'
headers = header_file.read_text(encoding='utf-8')
size = int(re.findall(r'(?im)^Content-Length:\s*(\d+)', headers)[-1])
etag = re.findall(r'(?im)^ETag:\s*(.+)', headers)[-1].strip()
identity = {'bytes': size, 'etag': etag, 'expected_sha256': args.expected_sha256.lower()}
identity_file = parts / 'identity.json'
if identity_file.exists():
    assert json.loads(identity_file.read_text(encoding='utf-8')) == identity, 'Source image changed; do not mix image versions'
else:
    assert shutil.disk_usage(target.parent).free > 2 * size + 5 * 1024**3, 'Insufficient space for verified image assembly'
    identity_file.write_text(json.dumps(identity, indent=2), encoding='utf-8')
width = args.part_mib * 1024 * 1024
partition_file = parts / 'partition.json'
if partition_file.exists():
    assert json.loads(partition_file.read_text()) == {'width': width}, 'Preserve the existing partition width when resuming'
else:
    assert width == 16 * 1024 * 1024 or not list(parts.glob('*.part')), 'Existing parts use the original 16 MiB partition width'
    partition_file.write_text(json.dumps({'width': width}), encoding='utf-8')
tasks = [(n, start, min(size - 1, start + width - 1)) for n, start in enumerate(range(0, size, width))]


def fetch(task):
    n, start, end = task
    path = parts / f'{n:04}.part'
    for attempt in range(12):
        have = path.stat().st_size if path.exists() else 0
        if have == end - start + 1:
            return
        assert 0 <= have < end - start + 1
        begin = start + have
        tail = parts / f'{n:04}.tail'
        header = parts / f'{n:04}.headers'
        result = subprocess.run(['curl.exe', '-sSfL', '--connect-timeout', '20', '--max-time', '240',
                                 '--speed-limit', '1024', '--speed-time', '45', '--range', f'{begin}-{end}',
                                 '-D', str(header), '-o', str(tail), url], capture_output=True)
        text = header.read_text(encoding='utf-8') if header.exists() else ''
        if tail.exists() and tail.stat().st_size:
            assert f'bytes {begin}-{end}/{size}' in text and etag in text, 'Response range or image identity changed'
            assert tail.stat().st_size <= end - begin + 1
            with path.open('ab') as output, tail.open('rb') as source:
                shutil.copyfileobj(source, output)
            tail.unlink()
        if path.exists() and path.stat().st_size == end - start + 1:
            return
        if result.returncode == 22:
            raise RuntimeError('Official download link rejected or expired; regenerate it through the vendor UI without changing image identity')
    raise RuntimeError(f'Image part {n} is still incomplete after resumable retries')


started = time.monotonic()
print(json.dumps({'started': True, 'bytes': size, 'parts': len(tasks), 'parallel': args.workers}), flush=True)
with ThreadPoolExecutor(max_workers=args.workers) as pool:
    for done, future in enumerate(as_completed([pool.submit(fetch, task) for task in tasks]), 1):
        future.result()
        if done % 32 == 0 or done == len(tasks):
            print(json.dumps({'complete_parts': done, 'total_parts': len(tasks), 'elapsed_seconds': time.monotonic() - started}), flush=True)
assert not target.exists(), 'Preserve an existing assembled image'
with target.open('xb') as output:
    for n, _, _ in tasks:
        with (parts / f'{n:04}.part').open('rb') as source:
            shutil.copyfileobj(source, output, 8 * 1024 * 1024)
assert target.stat().st_size == size
with target.open('rb') as stream:
    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
assert digest == args.expected_sha256.lower(), 'Vendor-published image SHA-256 mismatch; do not execute this image'
source = urlsplit(url)
receipt = {**identity, 'sha256': digest, 'vendor_hash_matched': True, 'source_page': args.source_page,
           'source_image': source.scheme + '://' + source.netloc + source.path, 'image': str(target),
           'elapsed_seconds': time.monotonic() - started}
target.with_suffix(target.suffix + '.download-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps(receipt), flush=True)
