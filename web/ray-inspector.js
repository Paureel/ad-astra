// Details remain off-canvas until a ray is selected. All values are supplied
// numerical integration samples; frequency is relative to emission, not hertz.
export function createRayInspector({ getArtifact, isPlaying, setPlaying }) {
  const $ = (id) => document.getElementById(id);
  const dialog = $("ray-dialog"),
    select = $("ray-select");
  let resume = false;
  const format = (value) =>
    Number.isFinite(value) ? Number(value).toPrecision(6) : "Not supplied";
  function fill(index) {
    const ray = getArtifact().rays[index];
    if (!ray) return;
    select.value = String(index);
    const point = ray.points.at(-1);
    $("ray-heading").textContent = "Light · " + ray.label;
    $("ray-explanation").textContent = window.AdAstraRayStory.describeRay(ray);
    const fields = [
      [
        "Emission direction",
        (ray.launch_direction_eulerian || []).map(format).join(", "),
      ],
      ["Final stored time", format(point.t_s * 1e9) + " ns"],
      [
        "Final position (x, y, z)",
        [point.x_m, point.y_m, point.z_m].map(format).join(", ") + " m",
      ],
      ["Frequency ÷ emitted frequency", format(point.eulerian_frequency_ratio)],
      ["Highest frequency ratio", format(ray.max_eulerian_frequency_ratio)],
      ["Integration status", ray.status],
      ["Stopping sphere", format(ray.event_radius_m) + " m; finite boundary"],
      ["Sampled null residual", format(ray.max_null_residual)],
      ["Residual definition", ray.null_residual_definition],
      [
        "Integrator",
        ray.integrator
          ? `${ray.integrator.method}; rtol ${ray.integrator.rtol}, atol ${ray.integrator.atol}, max Δ(ct) ${ray.integrator.max_step_ct_m} m`
          : "Not supplied",
      ],
    ];
    $("ray-fields").replaceChildren(
      ...fields.flatMap(([name, value]) => {
        const dt = document.createElement("dt"),
          dd = document.createElement("dd");
        dt.textContent = name;
        dd.textContent = value ?? "Not supplied";
        return [dt, dd];
      }),
    );
  }
  function open(index = 0) {
    const artifact = getArtifact();
    if (!artifact?.rays?.length) return;
    select.replaceChildren(
      ...artifact.rays.map((ray, i) => {
        const option = document.createElement("option");
        option.value = i;
        option.textContent = ray.label;
        return option;
      }),
    );
    resume = isPlaying();
    setPlaying(false);
    fill(index);
    dialog.showModal();
  }
  select.addEventListener("change", () => fill(Number(select.value)));
  $("ray-inspect").addEventListener("click", () => open());
  $("ray-close").addEventListener("click", () => dialog.close());
  dialog.addEventListener("close", () => {
    if (resume) setPlaying(true);
    resume = false;
  });
  dialog.addEventListener("click", (event) => {
    if (event.target !== dialog) return;
    const r = dialog.getBoundingClientRect();
    if (
      event.clientX < r.left ||
      event.clientX > r.right ||
      event.clientY < r.top ||
      event.clientY > r.bottom
    )
      dialog.close();
  });
  return { open };
}
