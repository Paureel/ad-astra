"use strict";
// Cross-model history, input identity, cache interpolation and cabin ray checks.
const assert=require("node:assert/strict"),fs=require("node:fs"),crypto=require("node:crypto"),vm=require("node:vm");
const {createMetric,trace,step}=require("./metric.js");
const {logTimeline}=require("./timeline.js");
const context={window:{}};
for(const file of ["default-result.js","history.js","solution-data.js"])
  vm.runInNewContext(fs.readFileSync(__dirname+"/"+file,"utf8"),context);
const entries=context.window.WARP_BUNDLED_HISTORY,artifact=entries.at(-1).artifact;
const solution=context.window.AD_ASTRA_SOLUTIONS.solutions.find(s=>s.parameter_hash===artifact.candidate.parameter_hash);
const receipt=JSON.parse(fs.readFileSync(__dirname+"/../research/compact100/result.json"));
const hash=p=>crypto.createHash("sha256").update(fs.readFileSync(__dirname+"/"+p)).digest("hex");
assert.equal(artifact.provenance.research_result_sha256,hash("../research/compact100/result.json"));
assert.equal(artifact.provenance.generator_sha256,hash("../scripts/build_compact_viewer.py"));
assert.equal(artifact.candidate.parameter_hash,receipt.candidate_sha256);
assert.equal(artifact.energy.value_J,receipt.independent_energy_refinement.at(-1).absolute_energy_J);
assert.equal(artifact.energy.value_kind,"estimate");
assert.deepEqual(Array.from(artifact.energy.interval_J),receipt.energy_J_interval.map(Number));
const meta=artifact.provenance.optical_cache;
assert.equal(meta.sha256,hash(meta.path));
const buffer=fs.readFileSync(__dirname+"/"+meta.path);
const data=new Float32Array(buffer.buffer.slice(buffer.byteOffset,buffer.byteOffset+buffer.byteLength));
const cache={nr:meta.radial_nodes,nm:meta.angular_nodes,a:data.subarray(0,data.length/2),b:data.subarray(data.length/2)};
assert.equal(data.length,cache.nr*cache.nm*8);
assert.ok(data.every(Number.isFinite));
const metric=createMetric(artifact.candidate.parameters);
const cached={...metric,fields:q=>metric.cachedFields(q,cache)};
let maxW=0,maxK=0;
for(const fixture of solution.field_audit) {
  const field=cached.fields(fixture.q);
  field.W.forEach((v,i)=>maxW=Math.max(maxW,Math.abs(v-fixture.W[i])));
  field.K.forEach((v,i)=>maxK=Math.max(maxK,Math.abs(v-fixture.K[i])));
}
assert.ok(maxW<.002&&maxK<.003,"The optical cache matches the exact Cartesian fields, including both poles.");
const far=solution.optical_far_reference;
const optical=trace(cached,far.origin,far.view,{steps:1280,stepScale:.25});
assert.ok(optical.resolved);
const cacheDirectionError=Math.hypot(...optical.state.slice(3,6).map((v,i)=>v+far.source_direction[i]));
assert.ok(cacheDirectionError<.001,"Cached optics agree with the independent raw-momentum Hamiltonian reference.");
const inside=solution.optical_inside_reference;
let state=[...inside.origin,...inside.view.map(v=>-v),0];
for(let i=0;i<960;i++)state=step(metric,state,.05);
const cabinPositionError=Math.hypot(...state.slice(0,3).map((v,i)=>v-inside.state[i]));
const cabinDirectionError=Math.hypot(...state.slice(3,6).map((v,i)=>v-inside.state[i+3]));
assert.ok(cabinPositionError<1e-5&&cabinDirectionError<1e-6,"Camera-inside equations agree with independent adaptive integration.");
// Actual old-to-new-to-old metric switching; no shared mutable model parameters.
const point=[-13.65,0,0],referenceEntry=entries[1].artifact;
const first=createMetric(referenceEntry.candidate.parameters).fields(point);
const newer=createMetric(artifact.candidate.parameters).fields(point);
const restored=createMetric(referenceEntry.candidate.parameters).fields(point);
assert.deepEqual(first,restored);
assert.ok(Math.hypot(...first.W.map((v,i)=>v-newer.W[i]))>.1);
const projection=logTimeline([
  {timestamp:context.window.WARP_PUBLICATIONS[0].published_on,energy_J:2.66e44},
  ...entries.map(e=>({timestamp:e.evaluated_utc,energy_J:e.artifact.energy.value_J}))
],{left:0,top:0,width:1000,height:200});
assert.equal(projection.points[1].x,projection.points[2].x,"Same-hour timestamps remain identical.");
assert.ok(projection.points[3].x-projection.points[2].x>200,"Recent submissions remain separated on the reverse logarithmic time axis.");
console.log("PASS: compact100 exact identity, estimate/enclosure distinction, binary cache, inside-camera ray, scenario switch and recent logarithmic spacing.");
console.log(JSON.stringify({maxW,maxK,cacheDirectionError,cabinPositionError,cabinDirectionError}));
