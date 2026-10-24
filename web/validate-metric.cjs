"use strict";
const assert = require("node:assert/strict"),
  fs = require("node:fs"),
  vm = require("node:vm"),
  crypto = require("node:crypto");
const { createMetric, step, trace, rhs } = require("./metric.js");
const context = { window: {} };
for (const file of ["default-result.js", "history.js", "solution-data.js"])
  vm.runInNewContext(fs.readFileSync(__dirname + "/" + file, "utf8"), context);
const solutions = JSON.parse(JSON.stringify(context.window.AD_ASTRA_SOLUTIONS));
assert.equal(
  solutions.generator_sha256,
  crypto
    .createHash("sha256")
    .update(fs.readFileSync(__dirname + "/../scripts/build_optics.py"))
    .digest("hex"),
  "Regenerate after generator edits.",
);
const artifacts = context.window.WARP_BUNDLED_HISTORY.map(
  (row) => row.artifact,
);
let maxW = 0,
  maxK = 0,
  maxRho = 0,
  maxAdaptive = 0,
  maxTail = 0;
for (const solution of solutions.solutions) {
  const artifact = artifacts.find(
    (a) => a.candidate.parameter_hash === solution.parameter_hash,
  );
  assert.ok(artifact, "Every mesh must bind to a bundled candidate.");
  assert.equal(
    solution.evaluator_source_sha256,
    artifact.provenance.evaluator_source_sha256,
  );
  const metric = createMetric(artifact.candidate.parameters);
  for (const fixture of solution.field_audit) {
    const field = metric.fields(fixture.q);
    field.W.forEach(
      (v, i) => (maxW = Math.max(maxW, Math.abs(v - fixture.W[i]))),
    );
    field.K.forEach(
      (v, i) => (maxK = Math.max(maxK, Math.abs(v - fixture.K[i]))),
    );
    for (let i = 0; i < 3; i++)
      for (let j = 0; j < 3; j++)
        assert.ok(
          Math.abs(field.K[i * 3 + j] - field.K[j * 3 + i]) < 1e-13,
          "Gradient shift Hessian is symmetric.",
        );
  }
  for (const [x, r] of solution.surface_meridian)
    assert.ok(
      Math.abs(Math.hypot(...metric.fields([x, r, 0]).W) - 1) < 1e-9,
      "Selected stationary limit satisfies g00=0.",
    );
  for (let i = 0; i < solution.density_meridian.length; i += 53) {
    const [x, r, v] = solution.density_meridian[i],
      { K } = metric.fields([x, r, 0]);
    const traceK = K[0] + K[4] + K[8],
      rho =
        (299792458 ** 4 / (16 * Math.PI * 6.6743e-11)) *
        (traceK ** 2 - K.reduce((s, x) => s + x * x, 0));
    maxRho = Math.max(maxRho, Math.abs(rho / solution.density_scale_J_m3 - v));
  }
  const farRef = solution.optical_far_reference;
  const farTrace = trace(metric, farRef.origin, farRef.view, {
    steps: 640,
    stepScale: 0.5,
  });
  assert.ok(farTrace.resolved);
  const farError = Math.hypot(
    ...farTrace.state.slice(3, 6).map((v, i) => v + farRef.source_direction[i]),
  );
  assert.ok(
    farError < 2e-4,
    "Sensitive off-axis ray agrees with independent raw-momentum Hamiltonian DOP853.",
  );
  assert.ok(farRef.null_residual < 1e-9);
  const ref = solution.optical_reference;
  let state = [...ref.origin, ...ref.view.map((v) => -v), 0];
  for (let i = 0; i < 240; i++) state = step(metric, state, 0.2);
  assert.ok(
    Math.hypot(...state.slice(0, 3).map((x, i) => x - ref.state[i])) < 1e-6,
    "RK4 vs independent Python DOP853 position.",
  );
  assert.ok(
    Math.hypot(...state.slice(3, 6).map((x, i) => x - ref.state[i + 3])) < 1e-8,
    "RK4 vs independent Python DOP853 direction.",
  );
  for (const offset of [-0.35, 0, 0.35]) {
    let view = ref.view.map((x, i) => x + (i === 1 ? offset : 0));
    const norm = Math.hypot(...view);
    view = view.map((x) => x / norm);
    const coarse = trace(metric, ref.origin, view),
      fine = trace(metric, ref.origin, view, { steps: 640, stepScale: 0.5 }),
      far = trace(metric, ref.origin, view, { boundary: 131072 });
    assert.ok(
      coarse.resolved && fine.resolved && far.resolved,
      "Audit rays reach finite boundaries.",
    );
    maxAdaptive = Math.max(
      maxAdaptive,
      Math.hypot(
        ...coarse.state.slice(3, 6).map((x, i) => x - fine.state[i + 3]),
      ),
    );
    maxTail = Math.max(
      maxTail,
      Math.hypot(
        ...coarse.state.slice(3, 6).map((x, i) => x - far.state[i + 3]),
      ),
    );
    const rate = rhs(metric, [...ref.origin, ...view, 0]);
    assert.ok(
      Math.abs(view.reduce((s, v, i) => s + v * rate[i + 3], 0)) < 1e-12,
      "Direction derivative is tangent to unit sphere.",
    );
  }
}
assert.ok(
  maxW < 2e-11 && maxK < 2e-11,
  "Independent analytic derivatives match Python Jet2.",
);
assert.ok(
  maxRho < 2e-7,
  "Direct density samples retain the same signed Hamiltonian-constraint density.",
);
assert.ok(
  maxAdaptive < 1e-4,
  "Sampled angular convergence with half steps and finite stopping surface.",
);
assert.ok(
  maxTail < 5e-4,
  "Sampled finite-boundary convergence (not global bound).",
);
// Flat and constant-shift spacetimes cannot bend normalized null directions.
for (const W of [
  [0, 0, 0],
  [2, 0, 0],
]) {
  const flat = { fields: () => ({ W, K: Array(9).fill(0) }) },
    n = [0.6, 0.8, 0],
    initial = [1, 2, 3, ...n, 0],
    result = step(flat, initial, 7);
  result
    .slice(3)
    .forEach((x, i) => assert.ok(Math.abs(x - initial[i + 3]) < 1e-14));
  result
    .slice(0, 3)
    .forEach((x, i) =>
      assert.ok(Math.abs(x - (initial[i] + 7 * (W[i] - n[i]))) < 1e-14),
    );
}
assert.throws(() =>
  createMetric({
    speed_c: 2,
    R_m: 20,
    sigma_per_m: 1,
    coefficients: [{ x_power: 5, transverse_power: 0, coefficient: "1/10" }],
  }),
);
const sky = JSON.parse(fs.readFileSync(__dirname + "/stars.json", "utf8"));
for (const [field, file] of [
  ["generator_sha256", "../scripts/build_sky.py"],
  ["png_sha256", "stars.png"],
])
  assert.equal(
    sky[field],
    crypto
      .createHash("sha256")
      .update(fs.readFileSync(__dirname + "/" + file))
      .digest("hex"),
  );
assert.equal(sky.stars.length, 8785);
assert.equal(sky.display.magnitude_limit, 5.5);
assert.equal(
  sky.stars.filter((row) => row[3] < sky.display.magnitude_limit).length,
  2816,
);
console.log(
  "PASS: selected-metric surface, independent Hessian/density, backward null-ray RK4, flat-space limits, data identity, and catalogue integrity.",
);
console.log(JSON.stringify({ maxW, maxK, maxRho, maxAdaptive, maxTail }));
const { describeRay } = require("./ray-story.js");
for (const artifact of artifacts) {
  for (const ray of artifact.rays) {
    const text = describeRay(ray),
      forward = ray.launch_direction_eulerian[0],
      ratio = ray.points.at(-1).eulerian_frequency_ratio;
    assert.match(text, /local observer/);
    if (forward > 0.001) assert.match(text, /ahead of the ship/);
    else if (forward < -0.001) assert.match(text, /backward/);
    else assert.match(text, /directly sideways/);
    if (ratio > 1.01) assert.match(text, /blueshift/);
    if (ratio < 0.99) assert.match(text, /redshift/);
  }
}
console.log(
  "PASS: plain-language ray direction and frequency explanations agree with stored paths.",
);
