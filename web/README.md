# Scientific viewer

From the repository root, run `npm run dev` and open http://127.0.0.1:4173.
Node 18+ is sufficient; no npm install or runtime CDN is needed. The viewer
uses vendored Three.js modules, so use HTTP rather than opening a file URL.
`npm run build` creates static `dist/` files without publishing them.

One full-screen scene contains the geometry, selected energy, and historical
evaluations. Select a timeline point or use the history slider to inspect its
saved artifact. The camera and physical color scale stay fixed between entries.
The icon controls select layers, camera views, the density slice, and PNG export.
Controls expose accessible names, focus states, and tooltips. Arrow keys rotate
the focused canvas, +/− zoom, and 0 restores the perspective camera.

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
log10(1 + elapsed UTC hours since the first publication's day boundary).
The one-hour shift makes the first coordinate positive; Unix timestamps are
not logged. Events are placed in UTC one-hour bins without changing their
original timestamps. Same-hour events share exactly the same x coordinate;
separate callouts and the history controls keep them inspectable. Date labels
and hours use the browser's local timezone; provenance and CSV retain UTC.
Axis ticks are thinned for legibility, not for data resolution.

Only fixed-benchmark evaluations are connected. Literature points never create
an apparent improvement line across different speeds, sizes, or definitions.
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
- The 3D point field revolves bilinearly interpolated central XY samples around
  x, using the frozen family's axisymmetry. It covers x ∈ [−40,40] m and radial
  distance up to 40 m. Samples below 0.005% of the fixed density scale are omitted
  for display; no energy is removed from the reported integral. Opacity helps
  expose structure and is not a second physical field.
- The signed color mapping is linear, symmetric, and fixed to the baseline.
  Orange denotes negative density; mint denotes positive density, in J/m³.
  Values outside the scale saturate and are counted in provenance and the slice.
- The slice interpolates the supplied density grid. Offset and plane selection
  update the 3D slice and optional 2D view. Their axes and units remain explicit.
- The spherical wireframe is the published baseline F = 0.5 reference profile.
  Additional rings mark F = 0.1 and 0.9. Dashed circles mark the 10 m cabin.
  These are reference markers, not candidate energy isosurfaces or a physical hull.
- The 8 m scale craft is schematic and contributes no gravitating mass.
- Ray lines connect only the supplied finite numerical integration samples.
  Segments outside the display cube are omitted; no spline or extrapolation is
  used. A finite integration interval does not establish an event horizon.
- The floor grid has 5 m spacing. The scale bar projects 20 m along x at the
  current view's origin, and hides when that projection is too short or large.
- PNG exports include the candidate, benchmark, parameter hash, units, and
  numerical status. JSON preserves the original artifact; CSV reports history.

Model source: [Rodal, arXiv:2512.18008v1](https://arxiv.org/abs/2512.18008v1).
The benchmark's 2c energy is the repository calculation, not a figure quoted
from the paper. Formal obligations remain in `docs/FORMALIZATION.md`.

Regenerate history with `python3 scripts/build_viewer_history.py` after updating
the generated reports and their viewer artifacts. The bundler checks candidate,
benchmark, energy, and evaluator identity; it never edits a score.

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
