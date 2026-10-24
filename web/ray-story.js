/* Plain-language interpretation of the actual finite integration, not a causal
 * classification. Kept separate so direction and frequency claims are testable. */
(() => {
  "use strict";
  function describeRay(ray) {
    const d = ray.launch_direction_eulerian;
    if (!d?.length)
      return "This line follows a test flash of light from the ship’s centre. Its course is calculated from the selected spacetime geometry.";
    const forward = d[0],
      side = Math.hypot(d[1], d[2]),
      end = ray.points.at(-1),
      before = ray.points.at(-2);
    let launch, course;
    if (forward > 0.001) {
      launch =
        side < 0.001
          ? "This flash is aimed straight ahead of the ship."
          : "This flash is aimed ahead of the ship and partly sideways.";
      const advance =
        Math.hypot(
          end.x_m - before.x_m,
          end.y_m - before.y_m,
          end.z_m - before.z_m,
        ) /
        (299792458 * (end.t_s - before.t_s));
      course =
        advance < 0.1
          ? "In this recording it makes progressively less headway near the front of the bubble, relative to the ship. It has not stopped locally: the geometry changes how local light motion translates into these ship-centred coordinates."
          : "Its course changes as it crosses the bubble’s changing geometry. The line shows where the light is relative to the ship, rather than the speed measured by a nearby observer.";
    } else if (forward < -0.001) {
      launch =
        side < 0.001
          ? "This flash is aimed straight backward, behind the ship."
          : "This flash is aimed diagonally backward, behind the ship.";
      course =
        ray.status === "escaped"
          ? "It moves away behind the ship and reaches the calculation’s 80 m stopping sphere. The word “escaped” only means it reached that finite boundary; it does not prove where the light ultimately goes."
          : "It travels through the rear of the changing geometry. This recording ends after a finite interval, so it does not show the light’s ultimate destination.";
    } else {
      launch = "This flash starts directly sideways from the ship.";
      course =
        end.x_m < -0.1
          ? "Its path bends toward the rear in this ship-centred view as it leaves the cabin. The geometry redirects its motion; it is not an engine plume or a force pushing the ship."
          : "The changing geometry redirects its initially sideways course. This line is a light path, not an engine plume or a force pushing the ship.";
    }
    const ratio = end.eulerian_frequency_ratio;
    let frequency = "";
    if (Number.isFinite(ratio) && ratio > 1.01)
      frequency =
        "At the last stored point, the light oscillates faster for local observers than when it was emitted. That shift toward bluer light is called a blueshift.";
    else if (Number.isFinite(ratio) && ratio < 0.99)
      frequency =
        "At the last stored point, the light oscillates more slowly for local observers than when it was emitted. That shift toward redder light is called a redshift.";
    return [
      launch,
      course,
      frequency,
      "Light still travels at c for every local observer. These finite test-ray calculations ignore the light’s own gravitational effect and do not establish an event horizon.",
    ]
      .filter(Boolean)
      .join(" ");
  }
  if (typeof module !== "undefined" && module.exports)
    module.exports = { describeRay };
  if (typeof window !== "undefined") window.AdAstraRayStory = { describeRay };
})();
