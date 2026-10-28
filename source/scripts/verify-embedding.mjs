import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { EmbeddingModel, dot } from '../src/embedding.mjs';
const root = resolve('models');
const samples = ['相邻K线有包含关系，向下合并时取较低的高点和较低的低点。', '走势类型完成后才能按两个同向中枢定义趋势。',
  '第三类买点的回抽不能回到原中枢区间。', '为这个句子生成表示以用于检索相关文章：同级别中枢之间的连接一定是次级别吗？',
  'Zn相应配合未提供唯一数值阈值。', '读者提问不能作为作者明确结论。', '中枢是什么？', '股票收益经验不是经过本项目独立验证的成功率。'];
const q8 = new EmbeddingModel(root), fp32 = new EmbeddingModel(root, 'fp32');
try {
  const pool = JSON.parse(readFileSync(resolve(q8.path, 'original-metadata/1_Pooling/config.json'), 'utf8'));
  assert.equal(pool.pooling_mode_cls_token, true); assert.equal(pool.word_embedding_dimension, 512);
  assert.equal(pool.pooling_mode_mean_tokens, false);
  const t = performance.now(); const a = await fp32.encode(samples); const fp32Ms = performance.now() - t;
  const tq = performance.now(); const b = await q8.encode(samples); const q8Ms = performance.now() - tq;
  const cosine = a.vectors.map((v, i) => dot(v, b.vectors[i]));
  const norm = b.vectors.map(v => Math.sqrt(dot(v, v)));
  assert.ok(norm.every(n => Math.abs(n - 1) < 1e-5));
  assert.ok(cosine.every(x => x > .95), 'Quantization drift exceeds initial consistency gate');
  const output = { created_at: new Date().toISOString(), models_offline_only: true, dimensions: 512, pooling: 'cls', normalize: true,
    original_metadata_checked: true, original_pytorch_output_compared: false,
    scope: 'Fixed original pooling/config and converted ONNX fp32 versus q8 outputs; not an independent PyTorch or semantic correctness proof.',
    model_manifest_sha256: q8.manifestSha256, samples: samples.map((text, i) => ({ text, cosine_fp32_q8: cosine[i], q8_norm: norm[i], tokens: b.input_lengths[i] })),
    min_cosine: Math.min(...cosine), mean_cosine: cosine.reduce((s, x) => s + x, 0) / cosine.length, fp32_ms: fp32Ms, q8_ms: q8Ms,
    process_peak_rss_bytes: process.resourceUsage().maxRSS * 1024, memory: process.memoryUsage(), passed: true };
  writeFileSync('../validation-runs/agent-implementation-20261022/m3-embedding-consistency.json', JSON.stringify(output, null, 2) + '\n');
  console.log(JSON.stringify({ ...output, samples: undefined }));
} finally { await q8.close(); await fp32.close(); }
