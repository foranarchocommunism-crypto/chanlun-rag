"""Fetch fixed-revision public model assets; no runtime network fallback."""
from pathlib import Path
import hashlib
import json
import sys
import time
import urllib.request

root = Path(__file__).resolve().parents[1]
specs = {
    'embedding': {
        'repo': 'Xenova/bge-small-zh-v1.5', 'revision': '75c43b069aac4d136ba6bc1122f995fedcfd2781',
        'original_repo': 'BAAI/bge-small-zh-v1.5', 'original_revision': '7999e1d3359715c523056ef9478215996d62a620',
        'license': 'MIT', 'pooling': 'cls', 'normalize': True, 'dimensions': 512,
        'query_instruction': '为这个句子生成表示以用于检索相关文章：',
        'files': ['config.json', 'tokenizer.json', 'tokenizer_config.json', 'special_tokens_map.json', 'vocab.txt', 'README.md', 'quantize_config.json', 'onnx/model_quantized.onnx', 'onnx/model.onnx'],
    },
    'reranker': {
        'repo': 'Xenova/bge-reranker-base', 'revision': '280bcc27a84e0b898c251e06fddb25171bd9b101',
        'original_repo': 'BAAI/bge-reranker-base', 'original_revision': '2cfc18c9415c912f9d8155881c133215df768a70',
        'license': 'MIT', 'score': 'raw_cross_encoder_logit_relevance_not_truth_probability',
        'files': ['config.json', 'tokenizer.json', 'tokenizer_config.json', 'special_tokens_map.json', 'sentencepiece.bpe.model', 'README.md', 'onnx/model_quantized.onnx'],
    }
}

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def download(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + '.part')
    request = urllib.request.Request(url, headers={'User-Agent': 'chan-kg-agent-model-build/0.2'})
    with urllib.request.urlopen(request, timeout=45) as response, part.open('wb') as output:
        count = 0
        for chunk in iter(lambda: response.read(1024 * 1024), b''):
            output.write(chunk)
            count += len(chunk)
    part.replace(path)
    print(json.dumps({'downloaded': str(path.relative_to(root)), 'bytes': count}), flush=True)

for name in sys.argv[1:] or ['embedding']:
    spec = specs[name]
    target = root / 'models' / spec['repo']
    receipt_path = target / 'model-manifest.json'
    if receipt_path.exists():
        old = json.loads(receipt_path.read_text(encoding='utf-8'))
        if all((target / f['path']).exists() and sha(target / f['path']) == f['sha256'] for f in old['assets']):
            print(json.dumps({'already_verified': name}), flush=True)
            continue
        raise SystemExit('Existing model receipt mismatch; inspect rather than overwriting a model version.')
    for filename in spec['files']:
        path = target / filename
        if not path.exists():
            download(f"https://huggingface.co/{spec['repo']}/resolve/{spec['revision']}/{filename}?download=true", path)
    original_files = ['README.md', 'config.json'] + (['1_Pooling/config.json'] if name == 'embedding' else [])
    for filename in original_files:
        path = target / 'original-metadata' / filename
        if not path.exists():
            download(f"https://huggingface.co/{spec['original_repo']}/resolve/{spec['original_revision']}/{filename}", path)
    paths = sorted(p for p in target.rglob('*') if p.is_file() and not p.name.endswith('.part'))
    result = {**spec, 'downloaded_at_unix': time.time(), 'remote_runtime_loading': False,
              'source_urls': [f"https://huggingface.co/{spec['repo']}/tree/{spec['revision']}", f"https://huggingface.co/{spec['original_repo']}/tree/{spec['original_revision']}"],
              'assets': [{'path': p.relative_to(target).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in paths]}
    receipt_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'model': name, 'manifest': str(receipt_path)}), flush=True)
