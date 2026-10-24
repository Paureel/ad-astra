// SPDX-License-Identifier: Apache-2.0
// Static README figure, using the viewer's actual hourly logarithmic projection.
import { readFile, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { logTimeline, authorName } = require("../web/timeline.js");
const root = new URL("../", import.meta.url);
const output = new URL("docs/energy-timeline.svg", root);
const manifestBytes = await readFile(new URL("records/history.json", root));
const manifest = JSON.parse(manifestBytes);
const inputs = { "records/history.json": digest(manifestBytes) };
const records = (manifest.publications || []).map((p) => ({
  author: p.author,
  timestamp: p.published_on,
  energy_J: p.energy_J,
  kind: "publication",
  digits: p.significant_digits,
  context: `${p.parameters.speed_c}c publication`,
  benchmark_id:p.id,
}));
for (const row of manifest.evaluations) {
  const bytes = await readFile(new URL(row.report_path, root));
  const report = JSON.parse(bytes);
  inputs[row.report_path] = digest(bytes);
  let name = row.author.name;
  if (row.author.git_commit) {
    if (!/^(?:[a-fA-F0-9]{40}|[a-fA-F0-9]{64})$/.test(row.author.git_commit))
      throw new Error("Attribution requires a full Git commit hash.");
    name = execFileSync("git", ["show", "--no-patch", "--format=%an", row.author.git_commit, "--"], {
      cwd: fileURLToPath(root), encoding: "utf8",
    }).trim();
  }
  if (!authorName(name)) throw new Error("Missing contributor attribution.");
  records.push({
    author: authorName(name),
    timestamp: report.provenance.created_utc,
    energy_J: report.energy.value_J,
    kind: row.kind,
    digits: report.energy.significant_digits||10,
    benchmark_id:report.benchmark.id,
    upper_bound:report.energy.value_kind==="upper_bound",
    context: report.benchmark.scenario_label || `${report.benchmark.speed_c}c${row.kind === "benchmark_reference" ? " reference" : ""}`,
  });
}
records.sort((a, b) => Date.parse(a.timestamp) - Date.parse(b.timestamp));
const width = 1000, height = Math.min(720, Math.max(330, 150 + records.length * 42));
const box = { left: 78, top: 56, width: 884, height: height - 154 };
const projection = logTimeline(records, box);
const bottom = box.top + box.height, end = box.left + box.width;
const parts = [];
const xml = (value) => String(value).replace(/[&<>"']/g, (s) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&apos;",
})[s]);
const text = (x, y, value, extra = "") => parts.push(`<text x="${x}" y="${y}" ${extra}>${xml(value)}</text>`);
function digest(bytes) { return createHash("sha256").update(bytes).digest("hex"); }
function science(value, digits) {
  const [mantissa, exponent] = value.toExponential(digits - 1).split("e");
  return `${mantissa} × 10${exponent.replace(/[+\-\d]/g, (c) => ({
    "+": "", "-": "⁻", "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
    "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
  })[c])}`;
}
function dateLabel(timestamp) {
  const d = new Date(timestamp);
  return `${String(d.getUTCDate()).padStart(2, "0")} ${["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][d.getUTCMonth()]} ${d.getUTCFullYear()}`;
}

text(28, 30, "Energy history", 'class="heading"');
text(972, 30, "Numerical only · UTC · 1 h bins · log/log", 'text-anchor="end" class="meta"');
text(box.left - 12, box.top - 10, "J", 'text-anchor="end" class="tick"');
for (const tick of projection.yTicks) {
  parts.push(`<path d="M${box.left},${tick.y}H${end}" class="grid"/>`);
  text(box.left - 12, tick.y + 4, science(tick.value, 1), 'text-anchor="end" class="tick"');
}
parts.push(`<path d="M${box.left},${box.top}V${bottom}H${end}" class="axis"/>`);
const ticks = [
  { x: box.left, timestamp: projection.origin },
  { x: end, timestamp: projection.latest },
];
for (const tick of projection.xTicks)
  if (!ticks.some((t) => Math.abs(t.x - tick.x) < 118)) ticks.push(tick);
for (const tick of ticks.sort((a, b) => a.x - b.x)) {
  parts.push(`<path d="M${tick.x},${bottom}v5" class="axis"/>`);
  const anchor = tick.x === box.left ? "start" : tick.x === end ? "end" : "middle";
  text(tick.x, bottom + 23, dateLabel(tick.timestamp), `text-anchor="${anchor}" class="tick"`);
  const d = new Date(tick.timestamp);
  text(tick.x, bottom + 39, `${String(d.getUTCHours()).padStart(2, "0")}:00`, `text-anchor="${anchor}" class="hour"`);
}
for (let i = 1; i < projection.points.length; i++) {
  const a = projection.points[i - 1], b = projection.points[i];
  const different = a.benchmark_id !== b.benchmark_id;
  parts.push(`<path d="M${a.x},${a.y}L${b.x},${b.y}" class="${different ? "literature-link" : "evaluation-link"}"><title>${different ? "Chronology across different parameters, not an improvement comparison" : "Same fixed benchmark"}</title></path>`);
}
const occupied = [];
// Label the newest entries first when a large history has crowded callouts.
for (const point of [...projection.points].reverse()) {
  const publication = point.kind === "publication";
  const anchor = point.x > width / 2 ? "end" : "start";
  const x = point.x + (anchor === "end" ? -12 : 12);
  const x0 = anchor === "end" ? x - 275 : x;
  let labelY;
  for (const offset of [-28, 48, -76, 96, -124, 144, -172, 192]) {
    const y = Math.max(box.top + 4, Math.min(bottom - 26, point.y + offset));
    const rect = { x: x0, y: y - 14, width: 275, height: 37 };
    if (!occupied.some((r) => rect.x < r.x + r.width + 8 && rect.x + rect.width + 8 > r.x && rect.y < r.y + r.height + 6 && rect.y + rect.height + 6 > r.y)) {
      occupied.push(rect); labelY = y; break;
    }
  }
  const color = publication ? "#e0b780" : "#a8d1ff";
  parts.push(`<g><title>${xml(`${point.author} · ${point.context} · ${science(point.energy_J, point.digits)} J · ${point.timestamp}`)}</title>`);
  if (labelY !== undefined) {
    parts.push(`<path d="M${point.x},${point.y}L${x},${labelY + 4}" class="leader"/>`);
    text(x, labelY, `${point.upper_bound?"≤ ":""}${science(point.energy_J, point.digits)} J`, `text-anchor="${anchor}" class="energy"`);
    text(x, labelY + 18, `${point.author} · ${point.context}`, `text-anchor="${anchor}" class="author"`);
  }
  parts.push(`<circle cx="${point.x}" cy="${point.y}" r="5" fill="${publication ? "#0b1426" : color}" stroke="${color}" stroke-width="1.5"/></g>`);
}
text(box.left, height - 19, "Dates use UTC; the original publication reports a day, not an hour.", 'class="meta"');
const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="title description">
<title id="title">Ad Astra energy timeline</title>
<desc id="description">Publication and contributor energy values on logarithmic axes. Time uses reverse log10(1 + UTC hours before the latest entry), in one-hour bins, expanding recent submissions. Dashed lines distinguish different parameters and the separate compact100 scenario. All results are numerical, not formally certified.</desc>
<metadata>${xml(JSON.stringify({ license: "Apache-2.0", generator: "scripts/build-timeline.mjs", inputs, records }))}</metadata>
<style>text{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;fill:#b6c6e1}.heading{font-family:system-ui,sans-serif;font-size:15px;fill:#e3edff}.meta{font-size:10px;fill:#94a9cd}.tick{font-size:10px}.hour{font-size:9px;fill:#91a6cb}.energy{font-size:13px;fill:#e4eeff}.author{font-size:11px;fill:#aabddc}.grid{stroke:#708bb0;stroke-opacity:.16;stroke-dasharray:2 6;fill:none}.axis{stroke:#657fa5;stroke-opacity:.65;fill:none}.literature-link{stroke:#c3ac90;stroke-width:1.5;stroke-dasharray:5 6;fill:none}.evaluation-link{stroke:#9cbeef;stroke-width:1.5;fill:none}.leader{stroke:#829dc3;stroke-opacity:.5;fill:none}</style>
<rect width="${width}" height="${height}" rx="12" fill="#0b1426"/>
${parts.join("\n")}
</svg>
`;
if (process.argv.includes("--check")) {
  if (await readFile(output, "utf8") !== svg) throw new Error("README timeline is stale. Run npm run data, then make manifest.");
  console.log("PASS: README timeline matches the saved records and shared hourly log/log projection.");
} else {
  await writeFile(output, svg);
  console.log(`Generated docs/energy-timeline.svg from ${records.length} saved records.`);
}
