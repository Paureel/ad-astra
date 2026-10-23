# Included numerical results

Every result in this directory is numerical evidence. None is a certified
energy bound or a promoted record. Provenance hashes identify the exact input
parameters, benchmark, evaluator source and runtime used to generate it.

| File | Purpose |
| --- | --- |
| `paper-reproduction.json` | Original R=5 m, sigma=4/m, beta=1 paper fixture; finite-window comparison and separately included infinite tail |
| `baseline.json` | Fixed R=20 m, sigma=1/m, beta=2 benchmark; whole-space energy and numerical diagnostics |
| `search-example.json` | Re-evaluation of the included eight-trial coordinate-search example |
| `search-example-viewer.json` | The same example with computed density slices and null-ray trajectories for import in `web/index.html` |

The baseline is approximately `4.250080505e45 J`. The small search example is
approximately `4.248944993e45 J`, a numerical reduction of about **0.0267%**.
Both pass the declared finite diagnostics. Global admissibility and rigorous
energy enclosures remain open, so no certified improvement is claimed.

The default viewer artifact is `web/default-result.js`. Regenerate all artifacts
using the commands in CODEX_BOOTSTRAP.md after changing any evaluator input.
The files' timestamps and numerical evidence are retained rather than silently
rewritten as if a future code revision had produced them.

