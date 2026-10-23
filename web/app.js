/* Ad Astra scientific viewer. No network, remote scripts, or executable imports. */
(() => {
  "use strict";
  const C = 299792458;
  const NS = "http://www.w3.org/2000/svg";
  const MAX_CELLS = 2000000;
  const finite = (value) => typeof value === "number" && Number.isFinite(value);
  const assert = (condition, message) => {
    if (!condition) throw new Error(message);
  };

  function validateArtifact(data) {
    assert(
      data && typeof data === "object" && !Array.isArray(data),
      "Expected one JSON result object.",
    );
    assert(
      data.schema_version === 1 ||
        (typeof data.schema_version === "string" &&
          data.schema_version.length > 0),
      "Missing or unsupported schema_version.",
    );
    assert(
      data.benchmark &&
        typeof data.benchmark.id === "string" &&
        data.benchmark.id.length <= 128,
      "Missing or oversized benchmark.id.",
    );
    assert(
      finite(data.benchmark.speed_c) && data.benchmark.speed_c > 1,
      "This viewer requires a declared superluminal benchmark speed.",
    );
    assert(
      String(data.benchmark.coordinate_frame || "")
        .toLowerCase()
        .startsWith("comoving"),
      "Coordinates must explicitly be comoving; ray times must be t_s in seconds.",
    );
    assert(
      data.candidate &&
        typeof data.candidate.id === "string" &&
        data.candidate.id.length <= 128,
      "Missing or oversized candidate.id.",
    );
    if (data.provenance?.created_utc !== undefined)
      assert(
        typeof data.provenance.created_utc === "string" &&
          data.provenance.created_utc.length <= 80 &&
          Number.isFinite(Date.parse(data.provenance.created_utc)),
        "Invalid provenance timestamp.",
      );
    assert(
      data.energy && finite(data.energy.value_J) && data.energy.value_J >= 0,
      "Missing finite, nonnegative energy.value_J.",
    );
    assert(
      data.geometry &&
        finite(data.geometry.extent_m) &&
        data.geometry.extent_m > 0,
      "Missing positive geometry.extent_m.",
    );
    if (data.geometry.ship_length_m !== undefined)
      assert(
        finite(data.geometry.ship_length_m) && data.geometry.ship_length_m > 0,
        "Ship reference length must be finite and positive.",
      );
    assert(
      data.display &&
        finite(data.display.rho_scale_abs_J_m3) &&
        data.display.rho_scale_abs_J_m3 > 0,
      "Missing fixed benchmark display.rho_scale_abs_J_m3.",
    );
    assert(
      Array.isArray(data.slices) &&
        data.slices.length > 0 &&
        data.slices.length <= 100,
      "Expected 1–100 numerical slices.",
    );
    let cellCount = 0;
    const sliceIDs = new Set();
    for (const slice of data.slices) {
      assert(
        typeof slice.id === "string" && !sliceIDs.has(slice.id),
        "Every slice needs a unique id.",
      );
      sliceIDs.add(slice.id);
      assert(
        ["xy", "yz"].includes(slice.plane),
        "Only xy and yz slice planes are supported.",
      );
      assert(finite(slice.offset_m), "A slice offset is not finite.");
      for (const axis of [slice.u_m, slice.v_m]) {
        assert(
          Array.isArray(axis) && axis.length >= 2 && axis.length <= 2049,
          "A slice axis must have 2–2049 points.",
        );
        assert(
          axis.every(finite) &&
            axis.every(
              (value, index) => index === 0 || value > axis[index - 1],
            ),
          "Slice axes must be finite and strictly increasing.",
        );
      }
      assert(
        Array.isArray(slice.rho_J_m3) &&
          slice.rho_J_m3.length === slice.u_m.length * slice.v_m.length,
        "Density array length does not match the slice grid.",
      );
      assert(
        slice.rho_J_m3.every(finite),
        "Density values include a non-finite number.",
      );
      cellCount += slice.rho_J_m3.length;
    }
    assert(
      cellCount <= MAX_CELLS,
      "Artifact exceeds the viewer limit of two million slice cells.",
    );
    const surfaces = data.geometry.isosurfaces || [];
    assert(
      Array.isArray(surfaces) && surfaces.length <= 20,
      "Too many reference isosurfaces.",
    );
    assert(
      surfaces.every(
        (surface) =>
          finite(surface.f) && finite(surface.radius_m) && surface.radius_m > 0,
      ),
      "Reference isosurfaces require finite f and positive radius_m.",
    );
    assert(
      Array.isArray(data.rays) && data.rays.length <= 200,
      "rays must be an array with at most 200 trajectories.",
    );
    let pointCount = 0;
    const rayIDs = new Set();
    for (const ray of data.rays) {
      const minimumPoints = ray.status === "failed" ? 1 : 2;
      assert(
        typeof ray.id === "string" &&
          !rayIDs.has(ray.id) &&
          Array.isArray(ray.points) &&
          ray.points.length >= minimumPoints,
        "Each ray requires a unique id and enough retained points (one is allowed only for a failed run).",
      );
      rayIDs.add(ray.id);
      assert(
        ray.points.every((point) =>
          ["t_s", "x_m", "y_m", "z_m"].every((key) => finite(point[key])),
        ),
        "Ray samples require finite t_s, x_m, y_m, z_m.",
      );
      pointCount += ray.points.length;
    }
    assert(
      pointCount <= 200000,
      "Artifact exceeds the viewer limit of 200,000 ray samples.",
    );
    return data;
  }

  function bracket(values, q) {
    let low = 0,
      high = values.length - 1;
    while (high - low > 1) {
      const mid = (low + high) >> 1;
      if (values[mid] <= q) low = mid;
      else high = mid;
    }
    return Math.max(0, Math.min(values.length - 2, low));
  }
  function sampleSlice(slice, u, v) {
    const ui = bracket(slice.u_m, u),
      vi = bracket(slice.v_m, v),
      n = slice.u_m.length;
    const a = Math.max(
      0,
      Math.min(1, (u - slice.u_m[ui]) / (slice.u_m[ui + 1] - slice.u_m[ui])),
    );
    const b = Math.max(
      0,
      Math.min(1, (v - slice.v_m[vi]) / (slice.v_m[vi + 1] - slice.v_m[vi])),
    );
    const q = vi * n + ui;
    return (
      (1 - b) * ((1 - a) * slice.rho_J_m3[q] + a * slice.rho_J_m3[q + 1]) +
      b * ((1 - a) * slice.rho_J_m3[q + n] + a * slice.rho_J_m3[q + n + 1])
    );
  }
  function labPosition(point, speedC) {
    return point.x_m + speedC * C * point.t_s;
  }
  function assertCompatible(data, baseline) {
    validateArtifact(data);
    assert(
      data.energy.value_J > 0,
      "Logarithmic history requires a positive energy.",
    );
    assert(
      data.benchmark.id === baseline.benchmark.id &&
        String(data.benchmark.version || "") ===
          String(baseline.benchmark.version || ""),
      "This result belongs to a different benchmark or version.",
    );
    assert(
      data.benchmark.speed_c === baseline.benchmark.speed_c &&
        data.energy.quantity === baseline.energy.quantity,
      "The result changes the benchmark speed or energy quantity.",
    );
    assert(
      JSON.stringify(data.benchmark.units) ===
        JSON.stringify(baseline.benchmark.units),
      "The result changes benchmark units.",
    );
    assert(
      Math.abs(
        data.display.rho_scale_abs_J_m3 / baseline.display.rho_scale_abs_J_m3 -
          1,
      ) < 1e-12,
      "The result changes the fixed benchmark density scale.",
    );
    for (const key of ["extent_m", "cabin_radius_m", "ship_length_m"])
      assert(
        data.geometry[key] === baseline.geometry[key],
        "The result changes fixed reference geometry.",
      );
    assert(
      JSON.stringify(data.geometry.isosurfaces) ===
        JSON.stringify(baseline.geometry.isosurfaces),
      "The result changes reference-profile surfaces.",
    );
    const parameters = data.candidate.parameters || {};
    for (const key of ["R_m", "sigma_per_m", "speed_c"]) {
      if (parameters[key] !== undefined)
        assert(
          parameters[key] === baseline.candidate.parameters[key],
          "The result changes fixed benchmark parameters.",
        );
    }
    return data;
  }
  function entryKey(entry) {
    return [
      entry.artifact.candidate.parameter_hash || entry.artifact.candidate.id,
      entry.artifact.energy.value_J,
      entry.artifact.provenance?.created_utc || "",
    ].join(":");
  }
  const API = {
    validateArtifact,
    sampleSlice,
    labPosition,
    assertCompatible,
    entryKey,
  };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  if (typeof globalThis.document === "undefined") return;
  window.WarpProofViewer = API;
  const $ = (id) => document.getElementById(id);
  const baseline = validateArtifact(window.WARP_DEFAULT_RESULT);
  const densityScale = baseline.display.rho_scale_abs_J_m3;
  const { hourBucket, HOUR_MS, logTimeline, artifactAuthor, authorName } =
    window.WarpTimeline;
  const publications = window.WARP_PUBLICATIONS || [];
  const entries = [];
  function decorateEntry(entry) {
    const known = (window.WARP_BUNDLED_HISTORY || []).find(
      (e) =>
        e.artifact.candidate.parameter_hash ===
        entry.artifact.candidate.parameter_hash,
    );
    const name =
      artifactAuthor(entry.artifact) ||
      authorName(entry.author) ||
      authorName(known?.author) ||
      "Unattributed";
    return {
      ...entry,
      author: {
        ...(known?.author || {}),
        ...(typeof entry.author === "object" ? entry.author : {}),
        name,
      },
      title: name,
    };
  }
  let selectedIndex = 0,
    db = null,
    densityBox = null;
  const superscript = (n) =>
    String(n)
      .split("")
      .map(
        (c) =>
          ({
            "-": "⁻",
            0: "⁰",
            1: "¹",
            2: "²",
            3: "³",
            4: "⁴",
            5: "⁵",
            6: "⁶",
            7: "⁷",
            8: "⁸",
            9: "⁹",
          })[c] || c,
      )
      .join("");
  function sci(n, digits = 5) {
    if (!finite(n)) return "—";
    if (n === 0) return "0";
    const [m, e] = n.toExponential(digits - 1).split("e");
    return m + " × 10" + superscript(Number(e));
  }
  function delta(value) {
    const n = (value / baseline.energy.value_J - 1) * 100;
    return (n < 0 ? "−" : n > 0 ? "+" : "") + Math.abs(n).toFixed(6) + "%";
  }
  function recordTime(entry, short = false) {
    const date = new Date(entry.evaluated_utc || entry.imported_utc);
    if (!Number.isFinite(date.getTime())) return "Unreported";
    return (
      (entry.evaluated_utc ? "" : "Imported ") +
      date.toLocaleString("en-GB", {
        day: short ? undefined : "2-digit",
        month: short ? undefined : "short",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false,
      })
    );
  }
  function current() {
    return entries[selectedIndex];
  }
  function showError(message) {
    $("error-message").textContent = message;
    $("error-message").hidden = false;
  }
  function svg(tag, attrs = {}, content) {
    const node = document.createElementNS(NS, tag);
    for (const [key, value] of Object.entries(attrs))
      node.setAttribute(key, value);
    if (content !== undefined) node.textContent = content;
    return node;
  }
  function download(body, type, filename) {
    const url = URL.createObjectURL(new Blob([body], { type }));
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function selectedSlice() {
    const data = current().artifact;
    return (
      data.slices.find(
        (s) =>
          s.plane === $("slice-plane").value &&
          s.offset_m === Number($("slice-offset").value),
      ) || data.slices[0]
    );
  }
  function fillOffsets() {
    const old = Number($("slice-offset").value),
      plane = $("slice-plane").value;
    const offsets = current()
      .artifact.slices.filter((s) => s.plane === plane)
      .map((s) => s.offset_m)
      .sort((a, b) => a - b);
    $("slice-offset").replaceChildren();
    for (const n of offsets) {
      const option = document.createElement("option");
      option.value = n;
      option.textContent = (plane === "xy" ? "z" : "x") + " = " + n + " m";
      $("slice-offset").append(option);
    }
    $("slice-offset").value = offsets.includes(old)
      ? old
      : offsets.includes(0)
        ? 0
        : offsets[0];
  }
  function updateSlice() {
    drawDensity();
    window.dispatchEvent(
      new CustomEvent("warp:slice", {
        detail: { artifact: current().artifact, slice: selectedSlice() },
      }),
    );
  }
  function fillProvenance() {
    const entry = current(),
      data = entry.artifact,
      p = data.provenance || {};
    $("provenance-heading").textContent = "Provenance";
    $("entry-scope").textContent =
      "Absolute Eulerian source energy for the fixed 2c geometry, including the infinite exterior tail. Values are numerical estimates, not certified bounds or propulsion requirements. Formal promotion remains unavailable.";
    $("source-link").href = "https://arxiv.org/abs/2512.18008v1";
    $("source-link").textContent = "Rodal, 2025 ↗";
    const fields = [
      ["Author", entry.title],
      ["Attribution", entry.author?.source || "Reported artifact metadata"],
      [
        "Git commit",
        entry.author?.git_commit ||
          data.provenance?.git_commit ||
          "Not supplied",
      ],
      ["Candidate", data.candidate.id],
      ["Benchmark", data.benchmark.id],
      ["Recorded evaluation", entry.evaluated_utc],
      [
        "Hourly bin",
        new Date(
          hourBucket(entry.evaluated_utc || entry.imported_utc),
        ).toISOString(),
      ],
      [
        "Timeline axes",
        "log₁₀(elapsed hours + 1), log₁₀(joules); UTC 1-hour bins, local date labels",
      ],
      ["Artifact generated", p.created_utc],
      ["Reported checks", data.status?.numerical || "unreported"],
      ["Evidence", "Numerical only; formal promotion unavailable"],
      ["Speed / cabin radius", "2c / 10 m"],
      ["Positive energy", sci(data.energy.positive_J) + " J"],
      ["Negative magnitude", sci(data.energy.negative_J) + " J"],
      ["Exterior tail", sci(data.energy.tail?.absolute_J) + " J"],
      ["Numerical error estimate", sci(data.energy.error_estimate_J) + " J"],
      ["Error scope", data.energy.error_kind],
      ["Display scale", sci(densityScale) + " J/m³, linear"],
      [
        "Annihilation equivalent",
        sci(
          window.AdAstraPhysics.annihilationEquivalent(data.energy.value_J)
            .antimatter_kg,
        ) + " kg antimatter + equal matter; ideal E = 2mc²",
      ],
      [
        "Comparison constants",
        "c = 299792458 m/s (exact SI); Earth mass = 5.9722 × 10²⁴ kg (NASA)",
      ],
      [
        "Clipped samples",
        data.slices.reduce(
          (n, s) =>
            n +
            s.rho_J_m3.filter((v) => Math.abs(v) > densityScale * (1 + 1e-12))
              .length,
          0,
        ),
      ],
      ["Parameter SHA-256", data.candidate.parameter_hash],
      ["Evaluator SHA-256", p.evaluator_source_sha256],
      ["Benchmark SHA-256", p.benchmark_sha256],
      ["Candidate file SHA-256", p.candidate_file_sha256],
      ["Source", entry.report_path || "Local import"],
    ];
    $("provenance-fields").replaceChildren();
    for (const [label, value] of fields) {
      const dt = document.createElement("dt"),
        dd = document.createElement("dd");
      dt.textContent = label;
      dd.textContent = value ?? "Unreported";
      $("provenance-fields").append(dt, dd);
    }
    $("parameters-json").textContent = JSON.stringify(
      data.candidate.parameters || {},
      null,
      2,
    );
  }
  function openPublication(publication) {
    $("provenance-heading").textContent = publication.full_author;
    const fields = [
      ["Author", publication.full_author],
      ["Published", publication.published_on + " · time not specified"],
      [
        "Published energy",
        sci(publication.energy_J, publication.significant_digits) + " J",
      ],
      ["Quantity", publication.quantity],
      ["Source location", publication.source_location],
      ["Publication DOI", publication.publication_url],
      ["Date source", publication.date_source],
      ["Scope", publication.comparison_scope],
      ["3D scene", "The selected 2c repository evaluation remains displayed."],
    ];
    $("provenance-fields").replaceChildren();
    for (const [label, value] of fields) {
      const dt = document.createElement("dt"),
        dd = document.createElement("dd");
      dt.textContent = label;
      dd.textContent = value;
      $("provenance-fields").append(dt, dd);
    }
    $("parameters-json").textContent = JSON.stringify(
      publication.parameters,
      null,
      2,
    );
    $("entry-scope").textContent = publication.comparison_scope;
    $("source-link").href = publication.source_url;
    $("source-link").textContent =
      publication.author + " · original publication ↗";
    $("provenance-dialog").showModal();
  }
  function select(index) {
    selectedIndex = Math.max(0, Math.min(entries.length - 1, index));
    const entry = current(),
      data = entry.artifact;
    const [m, e] = data.energy.value_J.toExponential(9).split("e");
    $("energy-value").replaceChildren(document.createTextNode(m + " × 10"));
    const exponent = document.createElement("span");
    exponent.className = "exponent";
    exponent.textContent = Number(e);
    const unit = document.createElement("span");
    unit.className = "unit";
    unit.textContent = "J";
    $("energy-value").append(exponent, unit);
    $("candidate-title").textContent = entry.title;
    $("energy-value").title =
      "Absolute Eulerian source energy · " + data.candidate.id;
    $("energy-change").textContent = delta(data.energy.value_J);
    $("history-scrubber").max = entries.length - 1;
    $("history-scrubber").value = selectedIndex;
    $("history-prev").disabled = selectedIndex === 0;
    $("history-next").disabled = selectedIndex === entries.length - 1;
    for (const option of [...$("slice-plane").options])
      option.disabled = !data.slices.some((s) => s.plane === option.value);
    if ($("slice-plane").selectedOptions[0]?.disabled)
      $("slice-plane").value = data.slices[0].plane;
    fillOffsets();
    fillProvenance();
    drawDensity();
    drawHistory();
    $("live-status").textContent =
      entry.title +
      ". " +
      sci(data.energy.value_J, 10) +
      " joules. Numerical only.";
    window.WarpProofState = { artifact: data, slice: selectedSlice() };
    window.dispatchEvent(
      new CustomEvent("warp:select", { detail: window.WarpProofState }),
    );
  }
  function rebuildHistory() {
    entries.sort(
      (a, b) =>
        (Date.parse(a.evaluated_utc) || Date.parse(a.imported_utc) || 0) -
        (Date.parse(b.evaluated_utc) || Date.parse(b.imported_utc) || 0),
    );
    $("history-scrubber").max = entries.length - 1;
  }
  function drawHistory() {
    const chart = $("history-chart"),
      w = chart.clientWidth,
      h = chart.clientHeight;
    if (w < 10) return;
    chart.setAttribute("viewBox", `0 0 ${w} ${h}`);
    chart.setAttribute("data-x-scale", "log10-elapsed-hours-plus-one");
    chart.setAttribute("data-y-scale", "log10-joules");
    chart.setAttribute("data-time-bin-hours", "1");
    chart.replaceChildren();
    const records = [
      ...publications.map((p) => ({
        author: p.author,
        timestamp: p.published_on,
        energy_J: p.energy_J,
        kind: "publication",
        publication: p,
      })),
      ...entries.map((e, index) => ({
        author: e.title,
        timestamp: e.evaluated_utc || e.imported_utc,
        energy_J: e.artifact.energy.value_J,
        kind: e.kind || "repository_evaluation",
        entryIndex: index,
      })),
    ].sort((a, b) => Date.parse(a.timestamp) - Date.parse(b.timestamp));
    const box = {
      left: w < 500 ? 64 : 78,
      top: 24,
      width: w - (w < 500 ? 78 : 94),
      height: h - 67,
    };
    const projection = logTimeline(records, box),
      points = projection.points;
    const bottom = box.top + box.height,
      end = box.left + box.width;
    chart.append(
      svg("path", {
        d: `M${box.left},${box.top}V${bottom}H${end}`,
        fill: "none",
        stroke: "#596e9b",
        "stroke-width": 0.65,
        opacity: 0.7,
      }),
    );
    chart.append(
      svg(
        "text",
        { x: box.left - 9, y: 11, "text-anchor": "end", class: "axis-unit" },
        "J",
      ),
    );
    chart.append(
      svg(
        "text",
        { x: end, y: 11, "text-anchor": "end", class: "axis-unit" },
        "1 h · log/log",
      ),
    );
    for (const tick of projection.yTicks) {
      chart.append(
        svg("line", {
          x1: box.left - 4,
          y1: tick.y,
          x2: end,
          y2: tick.y,
          stroke: "#6f83ae",
          "stroke-width": 0.5,
          opacity: tick.major ? 0.25 : 0.1,
          "stroke-dasharray": tick.major ? "2 5" : "1 7",
        }),
      );
      chart.append(
        svg(
          "text",
          {
            x: box.left - 9,
            y: tick.y + 3,
            "text-anchor": "end",
            class: "axis-tick",
          },
          sci(tick.value, 1),
        ),
      );
    }
    const tickCandidates = [
      { hour: 1, x: box.left, timestamp: projection.origin },
      {
        hour: projection.maxHour,
        x: end,
        timestamp: projection.origin + (projection.maxHour - 1) * HOUR_MS,
      },
      ...projection.xTicks,
    ];
    const labelledTicks = [];
    for (const tick of tickCandidates)
      if (
        !labelledTicks.some(
          (t) => Math.abs(t.x - tick.x) < (w < 500 ? 96 : 115),
        )
      )
        labelledTicks.push(tick);
    for (const tick of projection.xTicks)
      chart.append(
        svg("line", {
          x1: tick.x,
          y1: bottom,
          x2: tick.x,
          y2: bottom + 4,
          stroke: "#6f83ae",
          "stroke-width": 0.5,
          opacity: 0.55,
        }),
      );
    for (const tick of labelledTicks) {
      const date = new Date(tick.timestamp),
        anchor =
          tick.x < box.left + 30
            ? "start"
            : tick.x > end - 30
              ? "end"
              : "middle";
      chart.append(
        svg(
          "text",
          {
            x: tick.x,
            y: bottom + 17,
            "text-anchor": anchor,
            class: "date-tick",
          },
          date.toLocaleDateString("en-GB", {
            day: "2-digit",
            month: "short",
            year: "numeric",
          }),
        ),
        svg(
          "text",
          {
            x: tick.x,
            y: bottom + 29,
            "text-anchor": anchor,
            class: "hour-tick",
          },
          date.toLocaleTimeString("en-GB", {
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
          }),
        ),
      );
    }
    // A literature fixture has different parameters: never draw an improvement
    // connector from its energy to an entry in the fixed 2c benchmark.
    const evaluations = points.filter((p) => p.kind !== "publication");
    if (evaluations.length > 1)
      chart.append(
        svg("path", {
          d: evaluations
            .map((p, i) => (i ? "L" : "M") + p.x + "," + p.y)
            .join(" "),
          fill: "none",
          stroke: "#8caee8",
          "stroke-width": 1,
          opacity: 0.6,
        }),
      );
    const occupied = [],
      labelSlots = new Map();
    const priority = [...points].sort(
      (a, b) =>
        (b.entryIndex === selectedIndex) - (a.entryIndex === selectedIndex),
    );
    for (const point of priority) {
      const anchor =
        point.x < w / 3 ? "start" : point.x > (w * 2) / 3 ? "end" : "middle";
      const labelX =
          point.x + (anchor === "start" ? 10 : anchor === "end" ? -10 : 0),
        width = w < 500 ? 133 : 165;
      const x0 =
        anchor === "start"
          ? labelX
          : anchor === "end"
            ? labelX - width
            : labelX - width / 2;
      for (const offset of [-31, 37, -66, 73, -100, 108]) {
        const y = Math.max(25, Math.min(bottom - 16, point.y + offset));
        const rect = { x: x0, y: y - 12, w: width, h: 29 };
        if (
          !occupied.some(
            (r) =>
              rect.x < r.x + r.w + 7 &&
              rect.x + rect.w + 7 > r.x &&
              rect.y < r.y + r.h + 6 &&
              rect.y + rect.h + 6 > r.y,
          )
        ) {
          occupied.push(rect);
          labelSlots.set(point, { x: labelX, y, anchor });
          break;
        }
      }
    }
    for (const point of points) {
      const publication = point.kind === "publication",
        chosen = !publication && point.entryIndex === selectedIndex;
      const digits = publication ? point.publication.significant_digits : 10;
      const energy = sci(point.energy_J, digits) + " J";
      const context = publication
        ? " · " + point.publication.parameters.speed_c + "c"
        : point.kind === "benchmark_reference"
          ? " · 2c"
          : "";
      const date = publication
        ? point.publication.published_on
        : recordTime(entries[point.entryIndex]);
      const group = svg("g", {
        role: "button",
        tabindex: 0,
        "aria-label": point.author + context + ", " + energy + ", " + date,
        "aria-pressed": String(chosen),
        "data-hour-bucket": point.bucket_utc,
      });
      if (publication) group.setAttribute("aria-haspopup", "dialog");
      group.append(
        svg("circle", { cx: point.x, cy: point.y, r: 13, fill: "transparent" }),
      );
      if (chosen)
        group.append(
          svg("circle", {
            cx: point.x,
            cy: point.y,
            r: 8,
            fill: "#b4d8ff",
            opacity: 0.14,
          }),
        );
      group.append(
        svg("circle", {
          cx: point.x,
          cy: point.y,
          r: publication ? 4.5 : chosen ? 3.5 : 4,
          fill: publication || !chosen ? "#101a32" : "#d2e7ff",
          stroke: publication ? "#d6ae81" : "#92bde9",
          "stroke-width": publication ? 1 : 1.2,
        }),
      );
      const slot = labelSlots.get(point);
      if (slot) {
        group.append(
          svg("path", {
            d: `M${point.x},${point.y}L${slot.x},${slot.y + 5}`,
            fill: "none",
            stroke: publication ? "#ab9272" : "#7d97c8",
            "stroke-width": 0.5,
            opacity: 0.5,
          }),
          svg(
            "text",
            {
              x: slot.x,
              y: slot.y,
              "text-anchor": slot.anchor,
              class: "value-label" + (chosen ? " selected-value" : ""),
            },
            energy,
          ),
          svg(
            "text",
            {
              x: slot.x,
              y: slot.y + 13,
              "text-anchor": slot.anchor,
              class: "title-label",
            },
            point.author + context,
          ),
        );
      }
      group.append(
        svg(
          "title",
          {},
          point.author +
            context +
            " · " +
            energy +
            " · " +
            date +
            (publication
              ? " · publication fixture; different parameters"
              : " · hour bin " + point.bucket_utc),
        ),
      );
      const activate = () =>
        publication
          ? openPublication(point.publication)
          : select(point.entryIndex);
      group.addEventListener("click", activate);
      group.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          activate();
        }
      });
      chart.append(group);
    }
  }
  function densityColor(value) {
    return window.AdAstraPhysics.densityRGB(value, densityScale);
  }
  function drawDensity() {
    if (!entries.length) return;
    const canvas = $("density-canvas"),
      slice = selectedSlice(),
      w = canvas.clientWidth,
      h = canvas.clientHeight,
      dpr = Math.min(devicePixelRatio || 1, 2);
    $("scale-negative").textContent = "−" + sci(densityScale, 2);
    $("scale-positive").textContent = "+" + sci(densityScale, 2);
    if (w < 30 || h < 30) return;
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    const ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);
    const size = Math.min(w - 33, h - 28),
      x = (w - size) / 2 + 7,
      y = 4;
    densityBox = { x, y, size, slice };
    const buffer = document.createElement("canvas");
    buffer.width = buffer.height = 220;
    const bc = buffer.getContext("2d"),
      pixels = bc.createImageData(220, 220);
    for (let row = 0; row < 220; row++)
      for (let col = 0; col < 220; col++) {
        const u =
          slice.u_m[0] + (col / 219) * (slice.u_m.at(-1) - slice.u_m[0]);
        const v =
          slice.v_m.at(-1) - (row / 219) * (slice.v_m.at(-1) - slice.v_m[0]);
        const rgb = densityColor(sampleSlice(slice, u, v)),
          index = (row * 220 + col) * 4;
        pixels.data.set([...rgb, 255], index);
      }
    bc.putImageData(pixels, 0, 0);
    ctx.drawImage(buffer, x, y, size, size);
    ctx.strokeStyle = "#596e9b";
    ctx.lineWidth = 0.6;
    ctx.strokeRect(x, y, size, size);
    ctx.font = "7px SFMono-Regular, monospace";
    ctx.fillStyle = "#99a9cd";
    ctx.textAlign = "center";
    const a = slice.u_m[0],
      b = slice.u_m.at(-1),
      c = slice.v_m[0],
      d = slice.v_m.at(-1);
    for (let i = 0; i < 3; i++) {
      const px = x + (i * size) / 2,
        py = y + (i * size) / 2;
      ctx.fillText((a + ((b - a) * i) / 2).toFixed(0), px, y + size + 12);
      ctx.textAlign = "right";
      ctx.fillText((d - ((d - c) * i) / 2).toFixed(0), x - 6, py + 3);
      ctx.textAlign = "center";
    }
    ctx.setLineDash([2, 3]);
    ctx.strokeStyle = "#86a2cf";
    ctx.lineWidth = 0.55;
    for (const s of current().artifact.geometry.isosurfaces || []) {
      const r2 = s.radius_m * s.radius_m - slice.offset_m * slice.offset_m;
      if (r2 > 0) {
        ctx.beginPath();
        ctx.ellipse(
          x + ((0 - a) / (b - a)) * size,
          y + (d / (d - c)) * size,
          (Math.sqrt(r2) / (b - a)) * size,
          (Math.sqrt(r2) / (d - c)) * size,
          0,
          0,
          Math.PI * 2,
        );
        ctx.stroke();
      }
    }
    $("density-x").textContent = (slice.plane === "xy" ? "x" : "y") + " / m";
    $("density-y").textContent = (slice.plane === "xy" ? "y" : "z") + " / m";
    const clipped = slice.rho_J_m3.filter(
      (n) => Math.abs(n) > densityScale * (1 + 1e-12),
    ).length;
    $("density-readout").textContent = clipped
      ? clipped + " samples exceed scale"
      : "ρE · linear scale";
    $("scale-negative").textContent = "−" + sci(densityScale, 2);
    $("scale-positive").textContent = "+" + sci(densityScale, 2);
  }
  $("density-canvas").addEventListener("pointermove", (event) => {
    if (!densityBox) return;
    const rect = event.currentTarget.getBoundingClientRect(),
      { x, y, size, slice } = densityBox,
      px = event.clientX - rect.left,
      py = event.clientY - rect.top;
    if (px < x || px > x + size || py < y || py > y + size) return;
    const u =
        slice.u_m[0] + ((px - x) / size) * (slice.u_m.at(-1) - slice.u_m[0]),
      v =
        slice.v_m.at(-1) -
        ((py - y) / size) * (slice.v_m.at(-1) - slice.v_m[0]);
    $("density-readout").textContent =
      u.toFixed(1) +
      ", " +
      v.toFixed(1) +
      " m · " +
      sci(sampleSlice(slice, u, v), 3) +
      " J/m³";
  });
  $("density-canvas").addEventListener("pointerleave", drawDensity);
  async function openDB() {
    if (!window.indexedDB) return null;
    return new Promise((resolve, reject) => {
      const request = indexedDB.open("warpproof-local-history", 1);
      request.onupgradeneeded = () =>
        request.result.createObjectStore("evaluations", { keyPath: "key" });
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }
  async function restoreHistory() {
    try {
      db = await openDB();
      if (!db) return;
      const saved = await new Promise((resolve, reject) => {
        const req = db
          .transaction("evaluations")
          .objectStore("evaluations")
          .getAll();
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
      });
      for (const entry of saved) {
        try {
          assertCompatible(entry.artifact, baseline);
          if (!entries.some((e) => entryKey(e) === entryKey(entry)))
            entries.push(decorateEntry(entry));
        } catch {
          /* Incompatible stored artifacts never enter the viewer. */
        }
      }
      if (saved.length) {
        rebuildHistory();
        select(entries.length - 1);
      }
    } catch {
      showError(
        "Saved local history is unavailable. Bundled evaluations remain available.",
      );
    }
  }
  $("history-scrubber").addEventListener("input", (event) =>
    select(Number(event.target.value)),
  );
  $("history-prev").addEventListener("click", () => select(selectedIndex - 1));
  $("history-next").addEventListener("click", () => select(selectedIndex + 1));
  $("slice-plane").addEventListener("change", () => {
    fillOffsets();
    updateSlice();
  });
  $("slice-offset").addEventListener("change", updateSlice);
  const dialog = $("provenance-dialog");
  $("provenance-open").addEventListener("click", () => {
    fillProvenance();
    dialog.showModal();
  });
  $("provenance-close").addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) {
      const r = dialog.getBoundingClientRect();
      if (
        event.clientX < r.left ||
        event.clientX > r.right ||
        event.clientY < r.top ||
        event.clientY > r.bottom
      )
        dialog.close();
    }
  });
  $("export-artifact").addEventListener("click", () =>
    download(
      JSON.stringify(current().artifact, null, 2),
      "application/json",
      current().artifact.candidate.id + "-viewer.json",
    ),
  );
  $("export-history").addEventListener("click", () => {
    const cell = (v) =>
      '"' +
      String(v)
        .replaceAll('"', '""')
        .replace(/^[=+@\-]/, "'$&") +
      '"';
    const rows = [
      [
        "author",
        "kind",
        "recorded_utc",
        "date_precision",
        "hour_bucket_utc",
        "energy_J",
        "change_from_2c_baseline_percent",
        "evidence",
        "candidate",
        "git_commit",
        "source",
      ],
      ...publications.map((p) => [
        p.author,
        "publication",
        p.published_on,
        "day",
        new Date(hourBucket(p.published_on)).toISOString(),
        p.energy_J,
        "",
        "published_numerical",
        p.id,
        "",
        p.source_url,
      ]),
      ...entries.map((e) => [
        e.title,
        e.kind || "repository_evaluation",
        e.evaluated_utc || "",
        "timestamp",
        new Date(hourBucket(e.evaluated_utc || e.imported_utc)).toISOString(),
        e.artifact.energy.value_J,
        (e.artifact.energy.value_J / baseline.energy.value_J - 1) * 100,
        "numerical_only",
        e.artifact.candidate.id,
        e.author?.git_commit || e.artifact.provenance?.git_commit || "",
        e.report_path || "",
      ]),
    ];
    download(
      rows.map((row) => row.map(cell).join(",")).join("\r\n"),
      "text/csv;charset=utf-8",
      "ad-astra-energy-history.csv",
    );
  });
  function toggleSlice(open) {
    $("slice-panel").hidden = !open;
    $("slice-toggle").setAttribute("aria-pressed", String(open));
    if (open) drawDensity();
  }
  $("slice-toggle").addEventListener("click", () =>
    toggleSlice($("slice-panel").hidden),
  );
  $("slice-close").addEventListener("click", () => toggleSlice(false));
  new ResizeObserver(() => {
    drawDensity();
    drawHistory();
  }).observe(document.querySelector("main"));
  for (const entry of window.WARP_BUNDLED_HISTORY || []) {
    assertCompatible(entry.artifact, baseline);
    entries.push(decorateEntry(entry));
  }
  if (!entries.length)
    entries.push({
      title: "Rodal",
      author: { name: "Rodal", source: "Published metric attribution" },
      evaluated_utc: baseline.provenance?.created_utc,
      artifact: baseline,
    });
  rebuildHistory();
  select(entries.length - 1);
  restoreHistory();
})();
