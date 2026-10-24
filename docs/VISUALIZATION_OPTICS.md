# Selected-metric display and optical approximation

WP-008 visualization work; compact100 integration starts at revision
`9780771dc2058856b6a5257748e0866dfefd4df0`. Scope: `web/`, derived display
generators, timeline, viewer checks and documentation. The original evaluator,
benchmark, scientific energy receipts, past values and formal refusal gate
are preserved. A separately labelled compact100 history entry is added.

## Geometry and quantities

The implemented metric is `ds² = -du² + |dq + W du|²`, with `u = ct` in metres,
`W = ∇Φ`, and `K = DW = Hess Φ`. The reference implementation remains
`src/warpproof/geometry.py`, based on
[Rodal's pinned paper](https://arxiv.org/html/2512.18008v1).

The wireframe is the selected candidate's **stationary limit**, `|W| = 1`, where
`g00 = 0`. It is not a material boundary, energy isosurface, event horizon, or
causal certification. The baseline's forward radius is 20 m and equatorial
radius is 40 m, so a spherical F-profile was inadequate as its shape. The
perturbed candidate uses its own field, including the compact polynomial.
Dashed circles retain the specified 10 m cabin. The 8 m craft is schematic;
it hides within 6 m of the camera to avoid enclosing a cabin observer.

`scripts/build_optics.py` finds the exact candidate file hashes in the history
manifest, solves 129 meridional stationary-limit roots by 48 bisections, and
checks for one resolved radial crossing on a separate 513-radius scan. A future
candidate with multiple or unresolved sampled branches is refused rather than
assigned a misleading surface. This scan does not prove global topology.
Curves interpolate these sampled roots. Max sampled residual is about 2.3e-13
before decimal serialization; interpolated segments have no rigorous bound.

The 3D density cloud uses direct Python metric evaluations on radial samples
0–40 m at 0.5 m spacing, refined to 0.125 m at 17–23 m, with 49 polar angles.
Each point revolves by axisymmetry with circumference-aware sampling: target
6 m spacing, 12–64 azimuths off-axis and one on-axis. A fixed count undersampled
the wider outer negative region. Coordinates are rounded to 1e-7 m for v1
and 1e-10 m for compact100; normalized densities retain eight
significant digits. Signed colors retain the common baseline endpoints and symmetric asinh contrast;
opacity is a display aid. The color transform is
`asinh(min(1, |ρ|/scale)/0.0001) / asinh(10000)` for both signs. The fixed symmetric
transform exposes weak regions without changing values or using separate sign
normalizations. The legend uses that same transform. Both signs have identical
2.5–3.5 pixel glyphs (before device-pixel scaling), 0.6 peak opacity and depth
testing. There are no red outlines, halos or sign-specific boosts. Magnitude is
encoded by color; opacity is a shared display style. The 2D slice retains grid interpolation.
Unknown older browser artifacts retain their supplied density grid and cabin
reference, with no substituted baseline stationary-limit surface.

## Backward null rays

### Compact100 model

The separate research geometry is evaluated from the submitted degree-six
tensor B-spline and the exact original core/cutoff in
`research/compact100/geometry.py`. Its stationary limit spans approximately
12.36–55.63 m in sampled radial directions; **100 m is its flat-exterior radius**,
not a spherical hull or stationary limit. Direct density samples cover 0–100 m,
with refined inner-wall sampling. The initial view frames this wider region.

`web/compact-metric.js` independently evaluates the numerical spline and its
derivatives. CPU checks agree with Python fields to about 1e-14. For fast GPU
optics, a hash-checked 1025×513 cache stores six regular Cartesian dyad
coefficients of W and Hess Φ in two Float32 RGBA textures. Coordinates are
`t=cbrt((r−11)/89)` and `s=acos(−μ)/π`, resolving the inner wall and both poles.
The core/cutoff and the exactly flat exterior use analytic fields. Cached W
and Hess Φ are interpolated independently; they approximate the underlying
metric's derivatives, not a new energy evaluator. The same Killing-drift mask
rejects unresolved rays. No rigorous global interpolation bound is claimed.

The generator's 8,192 off-grid samples, including the axis and inner wall,
had maximum component errors below 0.000965 in W and 0.001/m in Hess Φ.
Independent CPU cache fixtures give about 0.000246 and 0.000996/m; the refined
cached far-ray source direction differs from raw-momentum DOP853 by about
6.24e-5 rad. A separate camera-inside 48 m integration agrees with exact-spline
RK4 to about 1.52e-7 m and 4.65e-9 rad. These are sampled diagnostics.

Compact100 interactive steps use
`0.5 × 0.25 × clamp(0.15×(abs(r−18)−7), 0.12, 8192)` with a 640-step budget.
Stationary refinement halves those steps with a 1,280-step budget. Historical
v1 metrics retain their analytic evaluator and original step rules. Each
selection synchronously changes the field mesh, stationary limit, metric
uniforms and cache mode; angular refinement is invalidated. Arrows back to v1
turn compact sampling off. There is no asynchronous late-result swap.

The main number and timeline show the refined numerical **1.5448691e45 J**
estimate. The separately replayed continuum interval remains in provenance.
Both axes stay logarithmic; time uses reverse `log10(1 + hours before latest)`
in UTC one-hour bins, with date labels. Recent submissions expand on the right;
identical hourly bins stay identical. Cross-scenario connectors are dashed.

### Integration equations

For a future-directed photon with Eulerian direction `n = p/ω`, unit `|n|`,
`ω = -p0 + W·p`, the Hamilton equations give `dq/du = n-W` and `dp/du = Kᵀp`.
Using past distance `l = -u` gives

```
dq/dl = W - n
dn/dl = -Kᵀn + n(nᵀKᵀn)
d(ln ω)/dl = -nᵀK n
```

Each screen ray starts at the **current camera position**, with `n` opposite the
viewing direction. The camera represents an instantaneous Eulerian observer,
not an observer fixed at that comoving coordinate over time. Orbiting and scroll
zoom recompute the map, including within the cabin. Near-zero coordinate
advance does not mean a photon stops locally; all local observers measure c.

The browser implements analytic potential derivatives separately from Python's
Jet2 calculation. RK4 normalizes `n` after each step and uses metre steps
`0.5 * clamp(0.15*(abs(r-R)-4), 0.12, 8192)`. Integration stops at the finite 65,536 m
sphere or after 640 interactive steps. A direction is accepted only after reaching that
sphere, with relative Killing-energy drift below 2% and `|ln ω| < 40`.
The Killing quantity is `p0 = ω(W·n - 1)`. Normalizing `n` enforces the null
constraint by construction; it is not an independent accuracy check.

Unresolved directions receive no source light. This is a numerical mask, not a
horizon diagnosis. Near critical directions need more careful integration; no
rigorous all-direction error bound or global causal analysis is claimed.
The eternal stationary geometry is assumed; bubble creation is not modeled.

A desktop GPU angular map starts with 144 interactive rows and an aspect-matched
width capped at 512. Touch devices start with 72 rows and a width capped at 256.
Mobile interactive maps use 4×4 scissored draws to bound per-draw work, including
when switching back to an analytic older metric. It updates
when the camera or selected metric changes, then interpolates to screen
resolution. After 120 ms without camera changes, 16 desktop or 64 mobile scissored tiles
progressively compute a map with twice as many rows and columns, quarter-scale
steps and a 1,280-step budget. Only the completed refined map replaces the
interactive map. Paused/reduced-motion views also finish this calculation. Floating-point linear filtering is used where supported, otherwise
half-float. Sustained slow frames reduce angular resolution and then pixel
ratio; they do not alter the geodesic equations. This angular interpolation and
its handling of unresolved boundaries limit resolved image detail and caustics.
Interpolated source vectors whose length falls below 0.9998 are rejected
(0.998 on half-float fallback), rather than normalizing an unresolved blend of
widely separated directions into a false source image.
The view is not a photon-counting or calibrated magnification prediction.

Touch devices cap the main buffer pixel ratio at 1.25 and omit multisample
antialiasing. Drawing-buffer preservation is disabled; PNG export renders and
copies the canvas synchronously. Only camera, data, layer, resize, sky loading
and unfinished optical refinement trigger WebGL draws. The illustrative 2D
mass rotation does not redraw a settled 3D scene.

WebGL context loss pauses rendering and cancels pending refinement. On the
browser's restoration event, Three.js recreates GL resources; the viewer
refreshes extension capabilities and cache textures, discards optical-map
completion state, and recomputes the selected metric's directions. The camera,
history selection, layer choices and motion preference are retained. Recovery
reduces resolution to relieve pressure; it does not alter integration settings.
An actual shader/initialization failure still fails visibly. A browser or OS
that cannot restore its context may still require a reload. See the
[WebGL context restoration contract](https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/webglcontextrestored_event).

`EXT_color_buffer_float` is required for calculated lensing; without it the
viewer shows the unlensed reference sky and disables the comparison control.
See the [Khronos specification](https://registry.khronos.org/webgl/extensions/EXT_color_buffer_float/).

## Reference sky and Saturn

`stars.json` preserves 8,785 coordinate-bearing Hipparcos entries with V < 6.5,
retrieved from [NASA HEASARC's Hipparcos mirror](https://heasarc.gsfc.nasa.gov/W3Browse/catalog/hipparcos.html).
Four entries with missing coordinates are explicitly excluded. Coordinates are
ICRS at J1991.25 on J2000 equatorial axes, with no proper motion correction.
The renderer uses only the 2,816 stars brighter than V = 5.5 to keep the sky quiet.
A fixed orientation relative to the warp axes is a reference choice.
Gaussian PSFs make unresolved sources visible; these are not stellar radii.
B−V encodes approximate warm/cool display colors. Relative V flux sets the
pre-tone-mapping raster strength, with fixed exposure and no absolute calibration.
`scripts/build_sky.py` records the query, raw VOTable digest and display settings.

Saturn is a single placed extended source at 1.2 million km, roughly 20 Saturn
equatorial radii from the scene. Its reference ellipsoid has equatorial radius
60,268 km and polar radius 54,364 km. The thin C/B/A annuli use NASA's edges
74,658–91,975 / 91,975–117,507 / 122,340–136,780 km. See
[NASA's ring table](https://nssdc.gsfc.nasa.gov/planetary/factsheet/satringfact.html)
and [Cassini's shape reference](https://atmos.nmsu.edu/data_and_services/atmospheres_data/Cassini/sci-saturn.html).
The rings' representative optical depths are 0.2 / 1.5 / 0.7, within the table's
ranges. The disk and thin rings have analytic intersections and simple mutual
shadows. Latitude bands and Lambert illumination are illustrative; detailed
clouds, scattering, narrow ringlets and spectral photometry are omitted.
Saturn is an angular reference source, with a chosen pole and sunlight, not an
ephemeris position or a proposed mass within this metric's source stress tensor.

The same source-direction map remaps both the stars and the entire planet. The
planet approximation neglects the finite ray-exit displacement relative to its
1.2e9 m distance, and the metric tail beyond 65,536 m. Saturn's own gravity,
source motion and proper light-travel-time evolution are omitted. These errors
are not included in the sampled ray audit. No exaggerated bending is added.
Colors stay fixed rather than predicting frequency-shifted spectra. The density and
wireframe are **coordinate diagnostic overlays**;
they are not rendered as optically observed material.

## Ship-emitted ray data and motion

The main scene omits all ship-emitted lines, markers, trails, ray toggles and ray
clocks at the user's request. The original Python DOP853 integrations remain
unchanged in the data and exports. Provenance contains an optional light-path
explanation dialog, with a direction selector and final actual stored sample.
Its plain-language interpretation describes the recorded course and frequency
shift, separate from the background optical approximation.

Forward examples make less headway relative to the ship and blueshift in the
recorded interval; the transverse example curves rearward and blueshifts; rearward
examples reach the finite 80 m stopping sphere and redshift. These are descriptions
of stored paths, not a theorem about every metric, angle or ultimate fate.
The test-ray model omits radiation backreaction despite very large forward
blueshifts. A local observer still measures light at c.

The only autonomous scene motion is the illustrative mass-comparison rotation.
It has a pause control, updates at at most 24 fps, stops in hidden tabs, and starts
paused under reduced-motion preferences. OrbitControls permits scroll zoom while
a left mouse orbit gesture remains active, including entry into the cabin.

## Evidence and limits

`npm test` compares JS derivatives to independently implemented Python Jet2
fixtures at inner, support-boundary, wall and far points; it checks the selected
stationary limit, density identity, normalized-ray equations, straight flat and
constant-shift limits, independent DOP853 reference and sampled refinement.
The display generator hash binds its fixtures; candidate/evaluator hashes bind
the mesh to existing artifacts. Passing these tests does not certify the metric
or close any formal research obligation.

Measured CPU maximum errors on all three bundled candidates: W ~1.1e-14, K ~8.0e-15/m,
normalized density ~4.5e-8 after coordinate rounding. Three sampled directions
per candidate changed by at most 5.0e-5 rad under half steps, and 4.1e-5 rad when
the exit radius doubled. Different step crossings contribute to these figures;
they are sampled comparisons, not rigorous bounds.

Earlier v1-only Safari GPU readback: max shift error 4.15e-7, Hessian error 2.15e-7/m;
RK4 at 0.2 m steps differs from Python DOP853 by 0.254 mm and 1.06e-6 rad after
48 m. For the sensitive selected-candidate far ray below, GPU interactive
source direction differs from the independent Hamiltonian reference by 1.18e-4
rad, and the refined calculation by 6.95e-6 rad. These opt-in readbacks do not run
during normal use.

`AdAstraDiagnostics.audit()` and `.benchmark({orbit:true,duration_ms:6000})`
allow local inspection without exposing labels in the experience. Hardware,
viewport, browser, critical directions and background load affect performance;
40 fps is a target, not a guarantee on every device. Before the mobile-context
recovery changes, seven-second local
Safari compact100 orbit benchmarks measured 89.9 fps outside (95th-percentile
frame 12 ms) and 89.9 fps inside the 10 m cabin (95th-percentile frame 13 ms),
with 139,099 density vertices, 144 interactive optical rows, a 1,543×888 CSS
viewport and device pixel ratio 1. The perspective, XY and YZ views were
visually inspected for both density signs. Native history arrows restored each
candidate's matching geometry/optical hash; a 320 px viewport had no horizontal
overflow. These are local observations, not a hardware-independent guarantee.
No website was hosted.

Mobile recovery was subsequently tested locally in desktop Safari with a
390×664 viewport, forced coarse-pointer detection and device pixel ratio 3.
Three real `WEBGL_lose_context` loss/restore cycles rebuilt the view, including
a history selection made while the context was lost. The selected candidate,
camera and controls survived, and resource counts returned to 61 geometries
and 13 textures. A settled three-second interval produced zero WebGL frames
with the illustrative animation enabled. This profile exercises the mobile
code path; it is not physical iPhone 14 testing or a mobile FPS guarantee.
Twenty subsequent history switches completed without loss, fallback or growing
resource counts. A separate compact100 reset retained paused motion and a
hidden density layer; restored-cache GPU fixtures remained within 0.000270
in W and 0.001015/m in Hess Φ. The resolved far-ray error was 7.54e-5 rad
(6.22e-5 rad refined). A tab return resumed refinement, and PNG export produced
a nonblank scene with buffer preservation disabled. These are local sampled
regressions, not a proof that Safari will never reset its GPU.

Compact100 GPU readback gave maximum fixture errors of 0.000270 in W and
0.001015/m in Hess Φ. The exterior-origin 48 m reference differed by 2.67 mm
and 3.29e-5 rad; its resolved interactive far-ray direction differed from
independent Hamiltonian integration by 7.54e-5 rad. The cabin-origin 48 m
reference differed by 1.02 mm and 1.51e-6 rad. That cabin ray did not pass the
interactive far-boundary acceptance mask, so it contributes no background
source light. Diagnostics report unresolved directions explicitly instead of
presenting their unfinished direction as a source. These are sampled checks.

## Saturn distortion audit and correction

A user reported a relatively undistorted Saturn over the coordinate bubble and
a giant off-axis arc. Projected overlap with the g00 wireframe cannot determine
optical distortion: the full null path matters, the field has an infinite tail,
and different parts of an extended image must be deflected differently to
change its shape. Orbiting also changes the observer position, not just screen
orientation. These are consequences of this viewer's stated metric and observer,
not conclusions imported from Alcubierre visualizations.

The audit found that the original 72-row bilinear map could interpolate widely
separated outgoing directions, creating misleading source pixels. A constant
unit-length vector average is generally shorter than one; normalizing it can
invent a source direction unsupported by either ray. The new continuity mask
rejects such unresolved interpolation. Interactive resolution doubles, integration
steps halve, and stationary views refine again without a long GPU submission.
Large arcs in an unresolved view must not be interpreted as a verified caustic.
The mask is conservative and may omit narrow physical images.

The checked sensitive ray starts at (-220,0,0) m with view direction
(0.9022466247,-0.3715129548,0.2189272769). Separate raw covariant-momentum
Hamilton equations, with constant p0, were integrated by Python DOP853 to an
exact 65,536 m boundary event (rtol2e-11, atol1e-12; 0.25 m near-field step cap).
The baseline source direction was approximately
(0.5629877597,0.7120315859,-0.4195900417), with final null residual 1.14e-12.
The old full-step direction differed by about 0.00313 rad (0.18°). Half-scale
steps reduce that to about 1.12e-4 rad; quarter-scale steps reduce it to about
1.1e-5 rad. Source directions remain approximations, particularly near critical
rays. This independent far reference is regenerated for every bundled candidate
and checked by `npm test`; it shares only the metric fields with the display,
not the normalized-direction ODE or RK4 integration.

## Handoff

Prepared with Codex assistance under human direction. The implementation and
numerical checks have not received independent human review. The next useful
scientific audit is an error-controlled image reconstruction near critical ray
bundles, including finite-source/time and spectral transport; the current mask
conservatively omits unresolved images. No scientific record is promoted.

Validation: `make check-formal`, `make display-data`, `npm test`, source-manifest
verification, local Safari desktop/mobile preview, native scroll entry into the
cabin, real OrbitControls held-drag wheel regression, GPU field/ray readback and
six-second orbit benchmarks. Other browsers/devices have not been benchmarked.
