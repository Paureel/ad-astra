# Scientific viewer

From the repository root, run `npm run dev` and open http://127.0.0.1:4173.
Node 18+ is sufficient; no npm install or runtime CDN is needed. The viewer
uses vendored Three.js modules, so use HTTP rather than opening a file URL.
`npm run build` creates static `dist/` files without publishing them.

One full-screen scene contains the geometry, selected energy, and historical
evaluations. Select a timeline point or use the history slider to inspect its
saved artifact. The camera and physical color scale stay fixed between entries.
Each history arrow switches the density mesh, stationary limit and optical metric
together. The newest entry is **Paureel · Compact 100 m**, a separate research
scenario. Its concrete displayed energy is the refined **1.5448691 × 10⁴⁵ J**
estimate; the replayed continuum interval remains in provenance and exports.
The timeline starts as a slim bottom strip. Its native disclosure control
expands the chart on demand and collapses it again, by pointer or keyboard.
The scene fits the dynamic viewport rather than a fixed minimum height, so the
timeline remains reachable on short phones. Mobile disclosure and history
controls have 44 px targets; the expanded chart adapts to the viewport height.
On short screens, opening it temporarily hides auxiliary scene overlays.
The icon controls select layers, camera views, the density slice, and PNG export.
Controls expose accessible names, focus states, and tooltips. Arrow keys rotate
the focused canvas, +/− zoom, and 0 restores the perspective camera. Scroll zoom
works while holding the left mouse button to orbit, and can enter the 10 m cabin.
The observer-dependent optical map follows the camera inside and outside.

The density and selected-metric surfaces stay stationary. The main scene has
no ship-emitted ray lines, markers or ray playback controls. The finite ray data
are preserved in JSON exports; plain-language light-path explanations and final
stored values remain inside provenance. The play/pause control affects only
the illustrative mass-comparison rotation, which updates at at most 24 fps,
stops in hidden tabs and starts paused under reduced-motion preferences.

## Annihilation comparison

The selected candidate's unchanged `energy.value_J` is converted to an ideal
rest-energy equivalent using `m_antimatter = E / (2c²)` and
`m_matter = m_antimatter`. Both annihilating rest masses contribute. The display
assumes complete conversion and complete recovery; it does not model production,
containment, losses, a reaction, or an energy source for the geometry. Antimatter
does not supply a negative-energy stress tensor. This is a scale comparison,
not an inferred propulsion fuel requirement.

`physics.js` uses the exact SI value `c = 299792458 m/s` from
[NIST](https://www.nist.gov/pml/special-publication-330/sp-330-section-2)
and the measured reference Earth mass `5.9722e24 kg` from the
[NASA Earth Fact Sheet](https://nssdc.gsfc.nasa.gov/planetary/factsheet/earthfact.html).
The annihilation interpretation follows
[CERN](https://home.cern/science/physics/antimatter/).
The `anti-Earths` value means Earth masses of antimatter; an equal mass of
ordinary matter is shown beside it. Counts are rounded to four significant
digits and update with the selected timeline evaluation.

The paired spheres share one linear length scale with the small Earth reference:
their radius ratio is the cube root of their mass in Earth masses. This is an
equal-density volume comparison, not a proposed self-gravitating object. It
has a separate scale from the metre-based geometry. Violet identifies antimatter
and amber ordinary matter by convention; these are not predicted appearances.

The timeline includes Rodal's original published **2.66 × 10^44 J** tail-corrected
total (Appendix 9, Eq. 9.14 and following paragraph), published **17 December
2025**, with the paper's original 1c, 5 m, sigma=4/m settings. This is a separate
literature reference, not an eligible 2c benchmark entry. Its hollow orange
marker opens the source and parameters; the selected 2c geometry stays visible.
The paper provides a date without a publication hour, which remains explicit
in the metadata. Its rounded value keeps three significant digits.

The 2c reference is attributed to Rodal's metric; its energy is the repository's
calculation. The supplied search example is labelled **Paureel**, as requested,
with that attribution recorded separately from the unchanged scientific data.
Future entries use contributor names, not candidate IDs.

Both axes are logarithmic. Energy uses log10(joules). Time uses
reverse log10(1 + UTC hours before the latest entry), increasing toward the
newest date on the right. This expands recent submissions while retaining older
publications. The one-hour shift handles zero age; Unix timestamps are not
logged. Events are placed in UTC one-hour bins without changing their
original timestamps. Same-hour events share exactly the same x coordinate;
separate callouts and the history controls keep them inspectable. Date labels
and hours use the browser's local timezone; provenance and CSV retain UTC.
Axis ticks are thinned for legibility, not for data resolution.

All points are connected chronologically. A dashed, muted connector identifies
transitions across the 1c publication, 2c benchmark and compact100 scenario;
its tooltip explains the changed comparison scope.
Solid blue connectors compare evaluations of the same fixed benchmark.
History dates are recorded evaluations, not acceptance or certification dates.
Numerical error estimates are not certified intervals.
Previously saved browser artifacts remain readable from IndexedDB. The interface
has no import control; add new evaluations through `records/history.json`.

Generate a result for the repository history with:

```sh
.venv/bin/python -m warpproof render-data candidates/example-perturbation.json \
  --output results/local/example-viewer.json
```

The browser only displays artifacts; it does not rerun the energy calculation.
Additional artifacts must match the baseline benchmark, version, speed, objective, reference
geometry, fixed parameters, and density scale. Array dimensions, finite values,
monotonic axes, and resource limits are checked. Imported status fields cannot
change the permanent numerical-only display or enable formal promotion.

## Scientific semantics

- Energy is the whole-space absolute Eulerian source-energy integral in joules,
  including the infinite exterior tail. It is not derived from displayed pixels.
- Positions are comoving metres. The frozen slices are Euclidean; this is a
  coordinate view, not a curved-space embedding.
- The 3D point field revolves direct Python evaluations on a refined meridional
  grid around x, using axisymmetry. It covers radius ≤40 m for v1 and ≤100 m
  for the separately labelled compact100 tensor spline.
  Samples below 0.005% of the fixed density scale are omitted for display; no
  energy is removed from the integral. Opacity exposes structure rather than
  encoding a second physical field. Older local artifacts without a generated
  mesh retain their supplied interpolated density samples.
- The signed color mapping is symmetric and fixed to common baseline endpoints.
  Contrast is asinh(|ρ|/(0.0001×scale))/asinh(10000), using the same transform for
  both signs, candidates and slices. This exposes weaker negative peaks without
  changing values; the legend uses that same mapping. Both signs use identical
  glyph size, opacity and depth treatment, with no red outlines or halos.
  Azimuth samples follow circumference (target 6 m spacing, 12–64 off-axis,
  one on-axis), so the wider outer region is not undersampled by a fixed count.
  Rose denotes negative density; cyan denotes positive density, in J/m³.
  Values outside the scale saturate and are counted in provenance and the slice.
- The slice interpolates the supplied density grid. Offset and plane selection
  update the 3D slice and optional 2D view. Their axes and units remain explicit.
- The wireframe is the selected metric's stationary limit |∇Φ| = 1 (g₀₀ = 0).
  Dashed circles mark the 10 m cabin. These are coordinate diagnostics, not an
  event horizon, energy boundary or physical hull. No baseline stationary-limit
  shape is substituted for an unbundled artifact.
- The 8 m scale craft is schematic and contributes no gravitating mass.
- Ship-emitted ray data remain finite supplied integrations, with no
  extrapolation. Their details report coordinate time and local frequency ratios,
  not a local observer’s proper clock or a proof of an event horizon.
- The floor grid has 5 m spacing. The scale bar projects 20 m along x at the
  current view's origin, and hides when that projection is too short or large.
- PNG exports include the candidate, benchmark, parameter hash, units, and
  numerical status and optical scope. JSON preserves the original
  artifact; CSV reports history.

Model source: [Rodal, arXiv:2512.18008v1](https://arxiv.org/abs/2512.18008v1).
The benchmark's 2c energy is the repository calculation, not a figure quoted
from the paper. Formal obligations remain in `docs/FORMALIZATION.md`.

Regenerate history with `npm run data` after updating
the generated reports and their viewer artifacts. The bundler checks candidate,
benchmark, energy, and evaluator identity; it never edits a score. The same
command regenerates `docs/energy-timeline.svg` for the README, using the viewer’s
hourly logarithmic projection. `npm test` checks that this figure is current.

`records/history.json` is the reviewable timeline manifest. Add a generated report
and viewer path, plus `"author": {"git_commit": "FULL_COMMIT_HASH"}` for a new
contribution. The bundler reads that exact local Git commit's author name with
`git show`; it does not infer authors from filenames or candidate IDs. Explicit
attribution is supported when an entry has no commit, including the original
bootstrap results. History updates are reviewed source changes; the viewer does
not automatically synchronize remote contributions.
Imported artifacts can also declare `provenance.git_author`,
`provenance.github_author`, or `provenance.author`; these remain reported metadata.
Missing attribution displays `Unattributed` until supplied. Old browser imports
matching known parameters inherit the current manifest's attribution.

Run `npm test` for schema, interpolation, SI frame conversion, bundled history,
and fixed-benchmark import checks. Browser layout and WebGL checks are separate.

## Calculated reference sky

The quiet background contains measured Hipparcos stars and one extended Saturn
reference source. Saturn uses a measured oblate reference shape and principal
ring radii, at a chosen 1.2 million km distance. Backward null-ray integration
through the selected metric maps every sky pixel, including Saturn's disk and
rings, to its source direction. The lens icon toggles the unlensed reference
for comparison. The camera is an instantaneous Eulerian observer; its position
changes the optical calculation, even inside the bubble.

The sky keeps fixed display colors and exposure. It predicts approximate angular
deflection, not spectra, photon counts or calibrated magnification. Planet
placement, bands and lighting are illustrative; no ephemeris or Saturn gravity
is included. The 65,536 m finite boundary, 640-step interactive limit and interpolated angular
map have unresolved directions and no rigorous global error bound. Stationary views progressively refine with
twice the angular resolution and half the interactive step size. Unresolved
blends of widely separated ray directions are rejected. Geometry and
outgoing ray paths remain coordinate overlays. Full equations, source attribution,
sampling, numerical audits and approximation limits are in
[VISUALIZATION_OPTICS.md](../docs/VISUALIZATION_OPTICS.md).

Rebuild all selected display meshes from the history and the quiet sky offline:

```sh
make display-data
```

This uses the reference Python environment and never modifies scores or history.
The sky can also be refreshed from NASA using `scripts/build_sky.py`; the committed
catalogue records its query, epoch, exclusions, generator and PNG digests. A new
contribution only needs its exact candidate, report and viewer in the existing
history workflow. The optical mesh generator discovers the candidate by file
hash and refuses mismatched evaluator identities.

Local performance/audit hooks are available as `AdAstraDiagnostics.snapshot()`,
`.audit()` and `.benchmark({orbit:true,duration_ms:6000})`. Benchmarks intentionally
move the camera only when invoked. No GPU readback runs during ordinary use.
