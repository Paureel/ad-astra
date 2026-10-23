/* Equal-density mass spheres. Their rotation is illustrative, not physical time. */
(() => {
  "use strict";
  const { annihilationEquivalent } = window.AdAstraPhysics;
  const canvas = document.getElementById("equivalence-canvas");
  const ctx = canvas.getContext("2d");
  const count = document.getElementById("antimatter-count");
  const matching = document.getElementById("matter-count");
  let equivalent,
    width = 300,
    height = 140,
    angle = 0;
  const dots = [];
  // A deterministic spherical graticule, not geography or simulated material.
  for (let lat = -75; lat <= 75; lat += 5)
    for (let lon = 0; lon < 360; lon += 6) {
      const a = (lat * Math.PI) / 180,
        b = (lon * Math.PI) / 180;
      dots.push([
        Math.cos(a) * Math.cos(b),
        Math.sin(a),
        Math.cos(a) * Math.sin(b),
      ]);
    }
  function globe(x, y, radius, rgb, rotation) {
    if (radius <= 0) return;
    const glow = ctx.createRadialGradient(
      x,
      y,
      radius * 0.4,
      x,
      y,
      radius * 1.35,
    );
    glow.addColorStop(0, `rgba(${rgb},0.11)`);
    glow.addColorStop(0.7, `rgba(${rgb},0.07)`);
    glow.addColorStop(1, `rgba(${rgb},0)`);
    ctx.fillStyle = glow;
    ctx.fillRect(
      x - radius * 1.4,
      y - radius * 1.4,
      radius * 2.8,
      radius * 2.8,
    );
    const surface = ctx.createRadialGradient(
      x - radius * 0.34,
      y - radius * 0.4,
      0,
      x,
      y,
      radius,
    );
    surface.addColorStop(0, `rgba(${rgb},0.46)`);
    surface.addColorStop(0.58, `rgba(${rgb},0.15)`);
    surface.addColorStop(1, "rgba(8,14,32,0.92)");
    ctx.fillStyle = surface;
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fill();
    for (const [dx, dy, dz] of dots) {
      const px = dx * Math.cos(rotation) - dz * Math.sin(rotation);
      const depth = dx * Math.sin(rotation) + dz * Math.cos(rotation);
      if (depth < -0.08) continue;
      const py = dy * 0.94 - depth * 0.34;
      ctx.fillStyle = `rgba(${rgb},${0.15 + 0.65 * Math.max(0, depth)})`;
      ctx.beginPath();
      ctx.arc(
        x + px * radius,
        y + py * radius,
        Math.max(0.35, radius * 0.009),
        0,
        Math.PI * 2,
      );
      ctx.fill();
    }
    ctx.strokeStyle = `rgba(${rgb},0.58)`;
    ctx.lineWidth = 0.65;
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.stroke();
  }
  function draw() {
    ctx.clearRect(0, 0, width, height);
    if (!equivalent) return;
    // The largest of the mass spheres and the Earth reference fits the frame.
    // Every radius shares the SAME linear length scale, with volume ∝ mass.
    const ratio = equivalent.radius_in_earth_radii;
    const unitRadius = Math.min(
      Math.min(width * 0.17, height * 0.32) / Math.max(1, ratio),
      height * 0.085,
    );
    const r = ratio * unitRadius,
      y = height * 0.43;
    globe(width * 0.28, y, r, "183,151,255", angle);
    globe(width * 0.72, y, r, "255,189,112", angle);
    ctx.font = "16px -apple-system, sans-serif";
    ctx.fillStyle = "#8999be";
    ctx.textAlign = "center";
    ctx.fillText("+", width * 0.5, y + 5);
    const earthY = height * 0.87,
      earthX = width * 0.36;
    globe(earthX, earthY, unitRadius, "162,226,201", angle);
    ctx.font = `${width < 200 ? 8 : 9}px monospace`;
    ctx.fillStyle = "#93a6bc";
    ctx.textAlign = "left";
    ctx.fillText("1 Earth", earthX + unitRadius + 7, earthY + 3);
  }
  function update({ artifact }) {
    equivalent = annihilationEquivalent(artifact.energy.value_J);
    const n = new Intl.NumberFormat("en", {
      maximumSignificantDigits: 4,
      notation:
        equivalent.earth_masses_each >= 1e6 ||
        (equivalent.earth_masses_each > 0 &&
          equivalent.earth_masses_each < 0.01)
          ? "scientific"
          : "standard",
    }).format(equivalent.earth_masses_each);
    count.textContent = "≈ " + n;
    matching.textContent = "+ " + n + " Earths";
    canvas.setAttribute(
      "aria-label",
      `Equal-density mass comparison: approximately ${n} anti-Earth masses plus ${n} Earth masses. Each large sphere has ${equivalent.radius_in_earth_radii.toPrecision(4)} times the radius of the Earth reference. Separate from the geometry's metre scale.`,
    );
    document.getElementById("equivalence").title =
      "Ideal annihilation equivalent: equal matter and antimatter masses, E = 2mc², complete energy recovery. Sphere volume represents mass at Earth's mean density. An energy comparison, not a propulsion fuel requirement.";
    draw();
  }
  new ResizeObserver(() => {
    width = canvas.clientWidth;
    height = canvas.clientHeight;
    const ratio = Math.min(devicePixelRatio || 1, 2);
    canvas.width = width * ratio;
    canvas.height = height * ratio;
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    draw();
  }).observe(canvas);
  window.addEventListener("warp:select", (event) => update(event.detail));
  window.addEventListener("astra:frame", (event) => {
    angle = event.detail.elapsed_ms * 0.000055;
    draw();
  });
  if (window.WarpProofState) update(window.WarpProofState);
})();
