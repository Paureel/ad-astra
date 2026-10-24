/* Hour-binned, logarithmic scientific history. No fabricated event times. */
(() => {
  "use strict";
  const HOUR_MS = 3600000;
  function hourBucket(timestamp) {
    const ms = Date.parse(timestamp);
    if (!Number.isFinite(ms)) throw new Error("History requires a valid date.");
    return Math.floor(ms / HOUR_MS) * HOUR_MS;
  }
  function authorName(value) {
    const name =
      typeof value === "string" ? value : value?.login || value?.name;
    return typeof name === "string" && name.trim() && name.length <= 128
      ? name.replace(/[\u0000-\u001f\u007f]/g, "").trim()
      : null;
  }
  function artifactAuthor(artifact) {
    const p = artifact.provenance || {};
    return (
      authorName(p.github_author) ||
      authorName(p.git_author) ||
      authorName(p.author) ||
      authorName(artifact.candidate?.author)
    );
  }
  function logTimeline(records, box) {
    if (!records.length) throw new Error("History is empty.");
    const buckets = records.map((r) => hourBucket(r.timestamp));
    const origin = Math.min(...buckets);
    const latest = Math.max(...buckets);
    const hours = buckets.map((t) => 1 + (latest - t) / HOUR_MS);
    const maxHour = Math.max(2, ...hours);
    const logs = records.map((r) => {
      if (!Number.isFinite(r.energy_J) || r.energy_J <= 0)
        throw new Error("Logarithmic history requires positive energies.");
      return Math.log10(r.energy_J);
    });
    const minLogY = Math.floor(Math.min(...logs));
    const maxLogY = Math.max(minLogY + 1, Math.ceil(Math.max(...logs)));
    const x = (hour) =>
      box.left + (1-Math.log10(hour) / Math.log10(maxHour)) * box.width;
    const y = (energy) =>
      box.top +
      ((maxLogY - Math.log10(energy)) / (maxLogY - minLogY)) * box.height;
    const xTicks = [];
    for (let p = 0; p <= Math.ceil(Math.log10(maxHour)); p++) {
      for (const m of [1, 2, 5]) {
        const hour = m * 10 ** p;
        if (hour <= maxHour)
          xTicks.push({
            hour,
            x: x(hour),
            timestamp: latest - (hour - 1) * HOUR_MS,
          });
      }
    }
    const yTicks = [];
    for (let p = minLogY; p <= maxLogY; p++) {
      for (const m of [1, 2, 5]) {
        const value = m * 10 ** p;
        if (Math.log10(value) <= maxLogY)
          yTicks.push({ value, y: y(value), major: m === 1 });
      }
    }
    return {
      origin,
      latest,
      maxHour,
      xTicks,
      yTicks,
      points: records.map((r, i) => ({
        ...r,
        bucket_utc: new Date(buckets[i]).toISOString(),
        hour: hours[i],
        x: x(hours[i]),
        y: y(r.energy_J),
      })),
    };
  }
  const API = { HOUR_MS, hourBucket, logTimeline, authorName, artifactAuthor };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  if (typeof window !== "undefined") window.WarpTimeline = API;
})();
