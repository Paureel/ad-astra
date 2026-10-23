"use strict";
const assert = require("node:assert/strict");
const {
  C_M_S,
  EARTH_MASS_KG,
  annihilationEquivalent,
  createRaySampler,
  densityRGB,
  DENSITY_COLORS,
} = require("./physics.js");
const pairEnergy = 2 * EARTH_MASS_KG * C_M_S ** 2;
assert.deepEqual(densityRGB(0, 10), DENSITY_COLORS.zero);
assert.deepEqual(densityRGB(-10, 10), DENSITY_COLORS.negative);
assert.deepEqual(densityRGB(10, 10), DENSITY_COLORS.positive);
assert.deepEqual(densityRGB(1e99, 10), DENSITY_COLORS.positive);
assert.deepEqual(densityRGB(5, 10), [47, 124, 140]);
assert.throws(() => densityRGB(NaN, 10));
assert.throws(() => densityRGB(1, 0));
const onePair = annihilationEquivalent(pairEnergy);
assert.ok(
  Math.abs(onePair.earth_masses_each - 1) < 1e-14,
  "One anti-Earth AND one Earth release two Earth rest energies.",
);
assert.equal(onePair.matter_kg, onePair.antimatter_kg);
const eightPairs = annihilationEquivalent(8 * pairEnergy);
assert.ok(
  Math.abs(eightPairs.radius_in_earth_radii - 2) < 1e-14,
  "Equal-density volume, not radius or projected area, encodes mass.",
);
assert.equal(annihilationEquivalent(0).antimatter_kg, 0);
for (const energy of [-1, NaN, Infinity, "1"])
  assert.throws(() => annihilationEquivalent(energy));
// Unequal time spacing catches index-based motion; no extrapolation is allowed.
const ray = createRaySampler([
  { t_s: 0, x_m: 0, y_m: 0, z_m: 0 },
  { t_s: 2, x_m: 4, y_m: 6, z_m: -2 },
  { t_s: 10, x_m: 12, y_m: 10, z_m: 6 },
]);
assert.deepEqual(ray.sample(1), [2, 3, -1]);
assert.deepEqual(ray.sample(0), [0, 0, 0]);
assert.deepEqual(ray.sample(6), [8, 8, 2]);
assert.deepEqual(ray.sample(10), [12, 10, 6]);
assert.equal(ray.sample(-0.01), null);
assert.equal(ray.sample(10.01), null);
assert.equal(ray.sample(NaN), null);
assert.throws(() => createRaySampler([{ t_s: 0 }, { t_s: 0 }]));
for (const endTime of [0, -1])
  assert.throws(
    () =>
      createRaySampler([
        { t_s: 0, x_m: 0, y_m: 0, z_m: 0 },
        { t_s: endTime, x_m: 1, y_m: 0, z_m: 0 },
      ]),
    /strictly increasing/,
  );
console.log(
  "PASS: annihilation pair mass, equal-density volume scaling, finite coordinate-time ray interpolation, and no extrapolation.",
);
