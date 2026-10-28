"""Compare fixed author safetensors to FP32 ONNX initializers without a Torch runtime."""
from pathlib import Path
import hashlib
import json
import sys
import urllib.request

root = Path(__file__).resolve().parents[1]
validation = root / 'build/model-validation'
sys.path.insert(0, str(validation / 'python-libs'))
import numpy as np
import onnx
from onnx import numpy_helper
from safetensors.numpy import load_file

validation.mkdir(parents=True, exist_ok=True)
original = validation / 'bge-small-zh-v1.5-original.safetensors'
revision = '7999e1d3359715c523056ef9478215996d62a620'
url = f'https://huggingface.co/BAAI/bge-small-zh-v1.5/resolve/{revision}/model.safetensors?download=true'
if not original.exists():
    part = original.with_suffix('.part')
    with urllib.request.urlopen(url, timeout=45) as response, part.open('wb') as output:
        for block in iter(lambda: response.read(1024 * 1024), b''):
            output.write(block)
    part.replace(original)

def file_sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def tensor_key(a):
    return (tuple(a.shape), a.dtype.str, hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest())

model_path = root / 'models/Xenova/bge-small-zh-v1.5/onnx/model.onnx'
model = onnx.load(str(model_path))
initializers = {t.name: numpy_helper.to_array(t) for t in model.graph.initializer}
lookup = {}
for name, array in initializers.items():
    lookup.setdefault(tensor_key(array), []).append(name)
weights = load_file(str(original))
matches = []
missing = []
for name, array in weights.items():
    options = [('direct', array)] + ([('transpose', array.T)] if array.ndim == 2 else [])
    found = None
    for orientation, value in options:
        names = lookup.get(tensor_key(value))
        if names:
            found = {'author_tensor': name, 'shape': list(array.shape), 'onnx_initializers': names, 'orientation': orientation, 'elements': int(array.size)}
            matches.append(found)
            break
    if found is None:
        missing.append({'author_tensor': name, 'shape': list(array.shape), 'elements': int(array.size)})
total = sum(int(a.size) for a in weights.values())
matched = sum(x['elements'] for x in matches)
omitted_feature_irrelevant = {'embeddings.position_ids', 'pooler.dense.bias', 'pooler.dense.weight'}
unexpected_missing = [x for x in missing if x['author_tensor'] not in omitted_feature_irrelevant]
used_elements = total - sum(x['elements'] for x in missing if x['author_tensor'] in omitted_feature_irrelevant)
outputs = [x.name for x in model.graph.output]
pooler_nodes = [n.name for n in model.graph.node if 'pooler' in n.name.lower()]
result = {
    'author_revision': revision, 'author_url': url, 'author_weights_sha256': file_sha(original),
    'onnx_fp32_sha256': file_sha(model_path), 'comparison': 'Exact tensor bytes with explicit transpose allowance; duplicate initializer values recorded, not an independent execution proof.',
    'author_tensors': len(weights), 'exact_matching_tensors': len(matches), 'matched_elements': matched, 'total_elements': total,
    'element_coverage': matched / total, 'matches': matches, 'unmatched': missing,
    'feature_output_names': outputs, 'pooler_nodes': pooler_nodes,
    'used_encoder_parameter_element_coverage': matched / used_elements,
    'omission_explanation': 'Feature graph returns last_hidden_state only, with no pooler nodes; CLS pooling ignores the original pooler. position_ids is a non-trainable indexing buffer, not an encoder weight.',
    'unexpected_unmatched': unexpected_missing,
    'onnx_runtime_fp32_vs_quantized_report': 'm3-embedding-consistency.json',
    'pytorch_output_equivalence_proven': False,
}
report = root.parent / 'validation-runs/agent-implementation-20261022/m3-author-weights.json'
report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: v for k, v in result.items() if k not in ('matches',)}, ensure_ascii=False), flush=True)
assert outputs == ['last_hidden_state'] and not pooler_nodes
assert not unexpected_missing and matched == used_elements, 'Every used encoder parameter must match exactly'
