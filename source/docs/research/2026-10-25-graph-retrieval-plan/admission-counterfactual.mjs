// Research-only counterfactual. Imports production readers; changes no production data/code.
// This tests candidate admission, NOT reranker quality, two-hop value, or answer correctness.
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
const out = dirname(fileURLToPath(import.meta.url)), app = resolve(out, '../../..'), root = resolve(app, '..');
const { KnowledgeGraph } = await import(pathToFileURL(resolve(app, 'src/core.mjs')));
const { readCorpus } = await import(pathToFileURL(resolve(app, 'src/corpus.mjs')));
const { expandGraph } = await import(pathToFileURL(resolve(app, 'src/graph-expansion.mjs')));
const { fuse } = await import(pathToFileURL(resolve(app, 'src/lexical.mjs')));
const graph = new KnowledgeGraph(resolve(root, 'shared-knowledge/v0.1.0'));
try {
  const corpus = readCorpus(graph);
  const cached = JSON.parse(readFileSync(resolve(root, 'validation-runs/agent-implementation-20261022/m3-hybrid-development.json'), 'utf8'));
  const gold = new Map(readFileSync(resolve(app, 'build/final-kb-retrieval-307029129712/cases.jsonl'), 'utf8').trim().split('\n').map(JSON.parse).map(c => [c.query_id, new Set(c.expected_source_refs.map(e => e.passage_id))]));
  const evidence = new Map([...corpus.claims.keys()].map(id => [id, (corpus.evidenceByClaim.get(id) ?? []).map(e => e.passage_id)]));
  const coverage = (ids, expected) => {
    const passages = new Set(ids.flatMap(id => evidence.get(id) ?? []));
    const hits = [...expected].filter(id => passages.has(id)).length;
    return { recall: hits / expected.size, complete: Number(hits === expected.size) };
  };
  const observations = cached.observations.map(item => {
    const channels = [{ name: 'lexical', weight: 1, results: item.raw_lexical }, { name: 'dense', weight: .5, results: item.raw_dense }];
    const base = fuse(channels, 100), base40 = base.slice(0, 40).map(r => r.id), baseSet = new Set(base40);
    const union = new Set(channels.flatMap(c => c.results.map(r => r.id)));
    const expansion = expandGraph(corpus, base, { query: item.query_text, mode: 'knowledge', limit: 20, graphDepth: 1, graphBudget: 20 }, c => c?.review_status === 'reviewed');
    const support = [...new Set(expansion.paths.map(p => p.support_claim_id))];
    const pool = support.filter(id => !baseSet.has(id));
    const ordered = [...pool.filter(id => !union.has(id)), ...pool.filter(id => union.has(id))];
    const expected = gold.get(item.query_id), baseline = coverage(base40, expected);
    const variants = [4, 8].map(slots => {
      const added = ordered.slice(0, slots), ids = [...new Set([...base40.slice(0, 40 - added.length), ...added, ...base.map(r => r.id)])].slice(0, 40);
      return { slots, candidates: ids.length, graph_only_admitted: added.filter(id => !union.has(id)).length, rescued_admitted: added.filter(id => union.has(id)).length, ...coverage(ids, expected), admitted_ids: added };
    });
    const additive = [4, 8].map(slots => {
      const added = ordered.slice(0, slots), ids = [...base40, ...added];
      return { slots, candidates: ids.length, ...coverage(ids, expected) };
    });
    return { id: item.query_id, baseline, graph_only_pool: pool.filter(id => !union.has(id)).length, variants, additive };
  });
  const mean = values => values.reduce((a, b) => a + b, 0) / values.length;
  const baseline = { candidate_evidence_recall: mean(observations.map(r => r.baseline.recall)), complete_evidence_fraction: mean(observations.map(r => r.baseline.complete)) };
  const variants = [4, 8].map(slots => {
    const values = observations.map(r => r.variants.find(v => v.slots === slots));
    return { slots, max_candidates: Math.max(...values.map(v => v.candidates)), graph_only_admitted: values.reduce((n, v) => n + v.graph_only_admitted, 0), rescued_admitted: values.reduce((n, v) => n + v.rescued_admitted, 0), queries_with_graph_only_admitted: values.filter(v => v.graph_only_admitted > 0).length, candidate_evidence_recall: mean(values.map(v => v.recall)), complete_evidence_fraction: mean(values.map(v => v.complete)), improved: values.filter((v, i) => v.recall > observations[i].baseline.recall).length, regressed: values.filter((v, i) => v.recall < observations[i].baseline.recall).length };
  });
  const additive = [4, 8].map(slots => {
    const values = observations.map(r => r.additive.find(v => v.slots === slots));
    return { slots, max_candidates: Math.max(...values.map(v => v.candidates)), candidate_evidence_recall: mean(values.map(v => v.recall)), complete_evidence_fraction: mean(values.map(v => v.complete)), improved: values.filter((v, i) => v.recall > observations[i].baseline.recall).length, regressed: values.filter((v, i) => v.recall < observations[i].baseline.recall).length };
  });
  const result = { created_at: new Date().toISOString(), status: 'research_counterfactual_only', cases: observations.length, production_modified: false, graph_depth: 1, graph_path_budget: 20, gold_scope: 'Previously exposed development passage annotations; union of every passage supported by admitted claims, NOT final Recall@20.', exclusions: ['definition anchors', 'reranker', 'new two-hop algorithm', 'new query-root gate', 'new gold annotations', 'answer quality'], admission_rule: 'Fixed-40 variant reserves up to 4 or 8 seats for graph support claims outside baseline top40; additive variant preserves all baseline40. Prioritize outside the full lexical/dense union.', baseline, variants, additive, observations };
  writeFileSync(resolve(out, 'admission-counterfactual.json'), JSON.stringify(result, null, 2));
  console.log(JSON.stringify({ ...result, observations: undefined }, null, 2));
} finally { graph.close(); }
