import {test} from 'node:test';
import assert from 'node:assert/strict';
import {numericQualityGates,verifyGates} from '../scripts/verify-graph-v2-gates.mjs';
test('quality gate rejects missing, string, boundary and insufficient effect values',()=>{
 assert.deepEqual(numericQualityGates(null),{two_hop_quality:false,ordinary_quality:false,negative_cases:false});
 const m={independent_semantic_acceptance:true,acceptance_statistics:{two_hop:{G2_T48:{difference:.05,ci95_lower:.001},G2_G1:{difference:.05,ci95_lower:.001}}}};
 assert.equal(numericQualityGates(m).two_hop_quality,true);
 m.acceptance_statistics.two_hop.G2_G1.ci95_lower=0;assert.equal(numericQualityGates(m).two_hop_quality,false);
 m.acceptance_statistics.two_hop.G2_G1={difference:'0.06',ci95_lower:.01};assert.equal(numericQualityGates(m).two_hop_quality,false);
 m.acceptance_statistics.two_hop.G2_G1={difference:.049,ci95_lower:.01};assert.equal(numericQualityGates(m).two_hop_quality,false);
});
test('ordinary and negative gates require all quantitative and human judgments',()=>{
 const m={acceptance_statistics:{ordinary:{G2_L:{difference:-.01,ci95_lower:-.02},G2_T48:{difference:0,ci95_lower:-.01}},critical_regressions:0,independently_reviewed_negatives:true,new_irrelevant_graph_primary:0,unsupported_path_conclusions:0}};
 assert.equal(numericQualityGates(m).ordinary_quality,true);assert.equal(numericQualityGates(m).negative_cases,true);
 m.acceptance_statistics.critical_regressions=1;assert.equal(numericQualityGates(m).ordinary_quality,false);
 m.acceptance_statistics.independently_reviewed_negatives=false;assert.equal(numericQualityGates(m).negative_cases,false);
});
