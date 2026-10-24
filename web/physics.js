/* Display conversions and finite sampled-ray playback; never a scoring engine. */
(() => {
  "use strict";
  const C_M_S = 299792458; // Exact SI definition, NIST SP 330.
  const EARTH_MASS_KG = 5.9722e24; // NASA Earth Fact Sheet, 15 November 2024.
  const DENSITY_COLORS = {
    zero: [15, 23, 43],
    negative: [255, 110, 144],
    positive: [79, 225, 237],
  };
  // One symmetric contrast transform for both signs, candidates and slices.
  const DENSITY_CONTRAST = 0.0001;

  function densityRGB(value, scale) {
    if (!Number.isFinite(value) || !Number.isFinite(scale) || scale <= 0)
      throw new Error(
        "Density color requires a finite value and positive finite scale.",
      );
    const fraction =
      Math.asinh(Math.min(1, Math.abs(value) / scale) / DENSITY_CONTRAST) /
      Math.asinh(1 / DENSITY_CONTRAST);
    const end = value < 0 ? DENSITY_COLORS.negative : DENSITY_COLORS.positive;
    return DENSITY_COLORS.zero.map((v, i) =>
      Math.round(v + (end[i] - v) * fraction),
    );
  }

  function annihilationEquivalent(energy_J) {
    if (!Number.isFinite(energy_J) || energy_J < 0)
      throw new Error(
        "Annihilation equivalence requires finite, nonnegative joules.",
      );
    // Both equal rest masses contribute: E = (m_matter + m_antimatter)c².
    // This ideal rest-energy comparison assumes complete conversion and recovery.
    const antimatter_kg = energy_J / C_M_S / C_M_S / 2;
    const earth_masses_each = antimatter_kg / EARTH_MASS_KG;
    return {
      antimatter_kg,
      matter_kg: antimatter_kg,
      earth_masses_each,
      radius_in_earth_radii: Math.cbrt(earth_masses_each),
    };
  }

  function createRaySampler(points) {
    if (!Array.isArray(points) || points.length < 2)
      throw new Error("Ray playback needs at least two supplied samples.");
    points.forEach((p, i) => {
      if (
        ![p.t_s, p.x_m, p.y_m, p.z_m].every(Number.isFinite) ||
        (i > 0 && p.t_s <= points[i - 1].t_s)
      )
        throw new Error(
          "Ray samples need finite coordinates and strictly increasing times.",
        );
    });
    return {
      start_s: points[0].t_s,
      end_s: points.at(-1).t_s,
      sample(time_s) {
        if (
          !Number.isFinite(time_s) ||
          time_s < points[0].t_s ||
          time_s > points.at(-1).t_s
        )
          return null;
        let lo = 0,
          hi = points.length - 1;
        while (hi - lo > 1) {
          const mid = (lo + hi) >> 1;
          if (points[mid].t_s <= time_s) lo = mid;
          else hi = mid;
        }
        const a = points[lo],
          b = points[hi];
        const fraction = (time_s - a.t_s) / (b.t_s - a.t_s);
        return ["x_m", "y_m", "z_m"].map(
          (key) => a[key] + fraction * (b[key] - a[key]),
        );
      },
    };
  }

  const API = {
    DENSITY_COLORS,
    DENSITY_CONTRAST,
    densityRGB,
    C_M_S,
    EARTH_MASS_KG,
    annihilationEquivalent,
    createRaySampler,
  };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  if (typeof window !== "undefined") window.AdAstraPhysics = API;
})();
