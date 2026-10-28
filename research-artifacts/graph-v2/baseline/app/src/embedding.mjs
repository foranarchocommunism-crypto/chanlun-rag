import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { sha256, codepoints } from './corpus.mjs';

export class EmbeddingModel {
  constructor(modelRoot, dtype = 'q8') {
    this.path = resolve(modelRoot, 'Xenova/bge-small-zh-v1.5'); this.dtype = dtype;
    const path = resolve(this.path, 'model-manifest.json');
    if (!existsSync(path)) throw Object.assign(new Error('Offline embedding model manifest missing'), { code: 'MODEL_MISSING' });
    this.manifest = JSON.parse(readFileSync(path, 'utf8')); this.manifestSha256 = sha256(path);
    const required = ['config.json', 'tokenizer.json', 'tokenizer_config.json', `onnx/${dtype === 'fp32' ? 'model.onnx' : 'model_quantized.onnx'}`];
    for (const name of required) {
      const asset = this.manifest.assets.find(a => a.path === name), filename = resolve(this.path, name);
      if (!asset || !existsSync(filename)) throw Object.assign(new Error(`Missing model asset: ${name}`), { code: 'MODEL_MISSING' });
      if (sha256(filename) !== asset.sha256) throw Object.assign(new Error(`Model checksum mismatch: ${name}`), { code: 'MODEL_INVALID' });
    }
  }
  async open() {
    if (this.extractor) return;
    const { env, pipeline } = await import('@huggingface/transformers');
    env.allowRemoteModels = false; env.allowLocalModels = true; env.useFSCache = false; env.useBrowserCache = false;
    this.extractor = await pipeline('feature-extraction', this.path, { local_files_only: true, dtype: this.dtype, device: 'cpu',
      session_options: { intraOpNumThreads: 4, interOpNumThreads: 1, graphOptimizationLevel: 'all' } });
  }
  async encode(texts, { query = false, instruction = true } = {}) {
    await this.open();
    const inputs = texts.map(text => (query && instruction ? this.manifest.query_instruction : '') + String(text).normalize('NFKC'));
    // Truncation is measured and exposed, never silently treated as full-query encoding.
    const tokenized = this.extractor.tokenizer(inputs, { padding: true, truncation: false });
    const lengths = tokenized.attention_mask.tolist().map(row => row.reduce((a, b) => a + Number(b), 0));
    const output = await this.extractor(inputs, { pooling: 'cls', normalize: true });
    if (output.dims[1] !== 512 || output.dims[0] !== inputs.length) throw Object.assign(new Error('Unexpected embedding dimensions'), { code: 'MODEL_INVALID' });
    for (const value of output.data) if (!Number.isFinite(value)) throw Object.assign(new Error('Nonfinite embedding'), { code: 'MODEL_INVALID' });
    return { vectors: output.tolist().map(row => Float32Array.from(row)), input_lengths: lengths,
      truncated: lengths.map(length => length > 512), dtype: this.dtype };
  }
  async close() { if (this.extractor) { await this.extractor.dispose(); this.extractor = null; } }
}
export function dot(a, b) { let result = 0; for (let i = 0; i < a.length; i++) result += a[i] * b[i]; return result; }
