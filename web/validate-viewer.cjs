"use strict";
const assert = require("node:assert/strict");
const {
  validateArtifact,
  sampleSlice,
  labPosition,
  assertCompatible,
  entryKey,
} = require("./app.js");
const fs = require("node:fs");
const vm = require("node:vm");
const {
  HOUR_MS,
  hourBucket,
  logTimeline,
  artifactAuthor,
} = require("./timeline.js");

// Deliberately synthetic interface fixture, never a scientific result.
const fixture = {
  schema_version: "interface-test-only",
  benchmark: {
    id: "synthetic-interface-fixture",
    version: "1",
    speed_c: 2,
    coordinate_frame: "comoving",
  },
  candidate: { id: "synthetic-interface-fixture" },
  energy: { quantity: "test-only", value_J: 1 },
  geometry: {
    extent_m: 2,
    ship_length_m: 1,
    isosurfaces: [{ f: 0.5, radius_m: 1 }],
  },
  display: { rho_scale_abs_J_m3: 10 },
  slices: [
    {
      id: "xy-0",
      plane: "xy",
      offset_m: 0,
      u_m: [-2, 0, 2],
      v_m: [-2, 0, 2],
      rho_J_m3: [-8, -4, 0, -2, 2, 6, 4, 8, 12],
    },
  ],
  rays: [
    {
      id: "test-ray",
      points: [
        { t_s: 0, x_m: 0, y_m: 0, z_m: 0 },
        { t_s: 1e-8, x_m: 0, y_m: 0, z_m: 0 },
      ],
    },
  ],
};
assert.equal(validateArtifact(fixture), fixture);
const copy = () => structuredClone(fixture);
const failed = copy();
failed.rays[0].status = "failed";
failed.rays[0].points = [failed.rays[0].points[0]];
assert.equal(validateArtifact(failed), failed);
let bad = copy();
bad.slices[0].rho_J_m3.pop();
assert.throws(() => validateArtifact(bad), /array length/);
bad = copy();
bad.slices[0].rho_J_m3[2] = NaN;
assert.throws(() => validateArtifact(bad), /non-finite/);
bad = copy();
bad.slices[0].u_m[1] = -2;
assert.throws(() => validateArtifact(bad), /strictly increasing/);
bad = copy();
bad.benchmark.coordinate_frame = "laboratory";
assert.throws(() => validateArtifact(bad), /comoving/);
bad = copy();
bad.rays.push(structuredClone(bad.rays[0]));
assert.throws(() => validateArtifact(bad), /unique id/);
bad = copy();
bad.geometry.ship_length_m = -1;
assert.throws(() => validateArtifact(bad), /positive/);
bad = copy();
bad.energy.value_J = Infinity;
assert.throws(() => validateArtifact(bad), /finite/);

// An affine physical field must survive bilinear display interpolation exactly.
// The fixture grid samples rho(u,v) = 2*u + 3*v + 2.
for (const u of [-1.6, -0.25, 0.7, 1.8])
  for (const v of [-1.7, -0.1, 0.9, 1.6]) {
    assert.ok(
      Math.abs(sampleSlice(fixture.slices[0], u, v) - (2 * u + 3 * v + 2)) <
        1e-12,
    );
  }
// A comoving point at x=0 follows the stipulated bubble centre in laboratory units.
assert.equal(labPosition({ x_m: 0, t_s: 1 }, 2), 599584916);
assert.equal(labPosition({ x_m: 12, t_s: 0 }, 2), 12);
const bundle = { window: {} };
vm.createContext(bundle);
for (const name of ["default-result.js", "history.js"])
  vm.runInContext(
    fs.readFileSync(require("node:path").join(__dirname, name), "utf8"),
    bundle,
  );
const baseline = JSON.parse(JSON.stringify(bundle.window.WARP_DEFAULT_RESULT));
const history = JSON.parse(JSON.stringify(bundle.window.WARP_BUNDLED_HISTORY));
assert.equal(history.length, 2);
assert.deepEqual(
  history.map((e) => e.title),
  ["Rodal", "Paureel"],
);
const publication = bundle.window.WARP_PUBLICATIONS[0];
assert.equal(publication.author, "Rodal");
assert.equal(publication.energy_J, 2.66e44);
assert.equal(publication.significant_digits, 3);
assert.equal(publication.date_precision, "day");
assert.equal(publication.parameters.speed_c, 1);
for (const entry of history) assertCompatible(entry.artifact, baseline);
assert.ok(
  history[0].artifact.energy.value_J > history[1].artifact.energy.value_J,
);
assert.notEqual(entryKey(history[0]), entryKey(history[1]));
// Equal decades must occupy equal distances on BOTH axes, after hour binning.
const start = Date.parse("2025-12-17T00:00:00Z");
const plot = logTimeline(
  [
    { timestamp: new Date(start).toISOString(), energy_J: 1e44 },
    { timestamp: new Date(start + 9 * HOUR_MS).toISOString(), energy_J: 1e45 },
    { timestamp: new Date(start + 99 * HOUR_MS).toISOString(), energy_J: 1e46 },
  ],
  { left: 0, top: 0, width: 400, height: 200 },
);
assert.equal(
  plot.points[1].x - plot.points[0].x,
  plot.points[2].x - plot.points[1].x,
);
assert.equal(
  plot.points[0].y - plot.points[1].y,
  plot.points[1].y - plot.points[2].y,
);
assert.equal(
  hourBucket("2026-10-23T22:06:31Z"),
  hourBucket("2026-10-23T22:59:59Z"),
);
assert.equal(
  hourBucket("2026-10-23T23:00:00Z") - hourBucket("2026-10-23T22:59:59Z"),
  HOUR_MS,
);
assert.throws(
  () =>
    logTimeline([{ timestamp: "2025-12-17", energy_J: 0 }], {
      left: 0,
      top: 0,
      width: 1,
      height: 1,
    }),
  /positive energies/,
);
assert.throws(() => hourBucket("invalid"), /valid date/);
assert.equal(
  artifactAuthor({
    provenance: { git_author: { name: "Future Contributor" } },
  }),
  "Future Contributor",
);
assert.equal(
  artifactAuthor({
    provenance: { github_author: { login: "new-researcher" } },
  }),
  "new-researcher",
);
const actualPlot = logTimeline(
  history.map((e) => ({
    timestamp: e.evaluated_utc,
    energy_J: e.artifact.energy.value_J,
  })),
  { left: 0, top: 0, width: 400, height: 200 },
);
assert.equal(actualPlot.points[0].x, actualPlot.points[1].x); // same hour; never fake time jitter
const change = (fn) => {
  const candidate = structuredClone(history[1].artifact);
  fn(candidate);
  return candidate;
};
assert.throws(
  () =>
    assertCompatible(
      change((d) => (d.display.rho_scale_abs_J_m3 *= 2)),
      baseline,
    ),
  /fixed benchmark density scale/,
);
assert.throws(
  () =>
    assertCompatible(
      change((d) => (d.benchmark.speed_c = 3)),
      baseline,
    ),
  /benchmark speed/,
);
assert.throws(
  () =>
    assertCompatible(
      change((d) => (d.benchmark.version = "other")),
      baseline,
    ),
  /benchmark or version/,
);
assert.throws(
  () =>
    assertCompatible(
      change((d) => (d.geometry.cabin_radius_m = 1)),
      baseline,
    ),
  /reference geometry/,
);
assert.throws(
  () =>
    assertCompatible(
      change((d) => (d.candidate.parameters.R_m = 2)),
      baseline,
    ),
  /benchmark parameters/,
);
assert.throws(
  () =>
    assertCompatible(
      change((d) => (d.geometry.isosurfaces[0].radius_m = 1)),
      baseline,
    ),
  /reference-profile/,
);
assert.throws(
  () =>
    assertCompatible(
      change((d) => (d.benchmark.units.energy = "kWh")),
      baseline,
    ),
  /benchmark units/,
);
assert.throws(
  () =>
    assertCompatible(
      change((d) => (d.provenance.created_utc = {})),
      baseline,
    ),
  /provenance timestamp/,
);
// A claimed status is inert input; no successful parser check promotes it.
const spoof = change((d) => {
  d.status.formal_certification = true;
  d.status.evidence_level = "formally_certified";
});
assertCompatible(spoof, baseline);
const html = fs.readFileSync(
  require("node:path").join(__dirname, "index.html"),
  "utf8",
);
assert.match(html, /Numerical only/);
assert.match(html, /Formal promotion\s+remains unavailable/);
assert.equal((html.match(/<main\b/g) || []).length, 1);
assert.equal((html.match(/<(?:section|aside)\b/g) || []).length, 0);
console.log(
  "PASS: schema rejection, interpolation, SI conversion, actual history identity, fixed benchmark imports, immutable evidence, author attribution, and hourly log/log axes.",
);
