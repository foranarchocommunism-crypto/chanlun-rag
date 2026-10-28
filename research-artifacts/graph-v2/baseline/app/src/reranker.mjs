import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { sha256 } from './corpus.mjs';
export class Reranker {
  constructor(modelRoot, settings = {}) {
    this.path = resolve(modelRoot, 'Xenova/bge-reranker-base');
    const manifest = resolve(this.path, 'model-manifest.json');
    if (!existsSync(manifest)) throw Object.assign(new Error('Offline reranker model missing'), { code: 'MODEL_MISSING' });
    this.manifest = JSON.parse(readFileSync(manifest, 'utf8')); this.manifestSha256 = sha256(manifest);
    if (settings.model_manifest_sha256 && settings.model_manifest_sha256 !== this.manifestSha256) throw Object.assign(new Error('Reranker revision mismatch'), { code: 'INDEX_STALE' });
    for (const name of ['config.json', 'tokenizer.json', 'tokenizer_config.json', 'onnx/model_quantized.onnx']) {
      const asset = this.manifest.assets.find(f => f.path === name);
      if (!asset || !existsSync(resolve(this.path, name))) throw Object.assign(new Error(`Missing reranker asset: ${name}`), { code: 'MODEL_MISSING' });
      if (sha256(resolve(this.path, name)) !== asset.sha256) throw Object.assign(new Error(`Reranker checksum mismatch: ${name}`), { code: 'MODEL_INVALID' });
    }
  }
  async open() {
    if (this.model) return;
    const { env, AutoTokenizer, AutoModelForSequenceClassification } = await import('@huggingface/transformers');
    env.allowRemoteModels = false; env.allowLocalModels = true; env.useFSCache = false; env.useBrowserCache = false;
    this.tokenizer = await AutoTokenizer.from_pretrained(this.path, { local_files_only: true });
    this.model = await AutoModelForSequenceClassification.from_pretrained(this.path, { local_files_only: true, dtype: 'q8', device: 'cpu',
      session_options: { intraOpNumThreads: 4, interOpNumThreads: 1, graphOptimizationLevel: 'all' } });
  }
  async score(query, texts) {
    await this.open(); const scores = [], truncated = [];
    for (let i = 0; i < texts.length; i += 4) {
      const batch = texts.slice(i, i + 4), queries = batch.map(() => query.normalize('NFKC'));
      const raw = this.tokenizer(queries, { text_pair: batch, padding: true, truncation: false });
      truncated.push(...raw.attention_mask.tolist().map(row => row.reduce((a, b) => a + Number(b), 0) > 512));
      const inputs = this.tokenizer(queries, { text_pair: batch, padding: true, truncation: true, max_length: 512 });
      const { logits } = await this.model(inputs);
      for (const row of logits.tolist()) { if (row.length !== 1 || !Number.isFinite(row[0])) throw Object.assign(new Error('Unexpected cross-encoder logits'), { code: 'MODEL_INVALID' }); scores.push(row[0]); }
    }
    return { scores, truncated, score_meaning: 'raw_cross_encoder_logit_relevance_not_truth_probability' };
  }
  async close() { if (this.model) { await this.model.dispose(); this.model = null; this.tokenizer = null; } }
}
