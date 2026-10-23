import * as THREE from "three";
import { OrbitControls } from "./vendor/OrbitControls.js";

const $ = (id) => document.getElementById(id);
const host = $("scene-container"),
  canvas = $("geometry-canvas");
const { sampleSlice } = window.WarpProofViewer;
const { createRaySampler, densityRGB } = window.AdAstraPhysics;
const motionPreference = matchMedia("(prefers-reduced-motion: reduce)");
let renderer,
  controls,
  camera,
  scene,
  field,
  rayGroup,
  reference,
  sliceMesh,
  craft;
let pending = false,
  currentArtifact = null,
  framingFactor = 1;
let playing = !motionPreference.matches,
  elapsed_ms = 0,
  lastTick = null,
  lastRender = -Infinity;
const layers = { field: true, rays: true, reference: true };
const rayColors = [
  "#ffdc8a",
  "#ffb87c",
  "#f391cd",
  "#c59bff",
  "#8fb8ff",
  "#7bbfff",
  "#b4a5ff",
  "#c992de",
  "#e9a8ac",
];

function requestRender() {
  if (!pending) {
    pending = true;
    requestAnimationFrame((now) => {
      pending = false;
      if (!renderer || document.hidden) {
        lastTick = null;
        return;
      }
      if (playing && lastTick !== null)
        elapsed_ms += Math.max(0, now - lastTick);
      lastTick = now;
      // Cap playback at 30 fps; paused camera views render on demand.
      if (playing && now - lastRender < 1000 / 30) {
        requestRender();
        return;
      }
      controls.update();
      animateRays();
      renderer.render(scene, camera);
      updateScale();
      lastRender = now;
      window.dispatchEvent(
        new CustomEvent("astra:frame", { detail: { elapsed_ms } }),
      );
      if (playing) requestRender();
    });
  }
}
function setPlaying(value) {
  playing = value;
  lastTick = null;
  const button = $("motion-toggle");
  button.setAttribute("aria-pressed", String(playing));
  const action = playing
    ? "Pause sampled-ray playback"
    : "Play sampled-ray playback";
  button.setAttribute("aria-label", action);
  button.title = action;
  document.documentElement.dataset.motion = playing ? "on" : "off";
  requestRender();
}
function animateRays() {
  const playback = rayGroup?.userData.playback;
  if (!playback?.length) return;
  const first = Math.min(...playback.map((p) => p.sampler.start_s));
  const last = Math.max(...playback.map((p) => p.sampler.end_s));
  const time = first + ((elapsed_ms % 12000) / 12000) * (last - first);
  const extent = currentArtifact.geometry.extent_m;
  const place = (object, point) => {
    object.visible = !!point && Math.max(...point.map(Math.abs)) <= extent;
    if (object.visible) object.position.set(...point);
  };
  for (const { sampler, marker, trail } of playback) {
    place(marker, sampler.sample(time));
    trail.forEach((dot, i) =>
      place(dot, sampler.sample(time - (i + 1) * (last - first) * 0.012)),
    );
  }
  $("ray-clock").textContent = (time * 1e9).toFixed(0) + " ns";
  $("ray-clock").hidden = !layers.rays;
}
function dispose(group) {
  if (!group) return;
  group.traverse((node) => {
    node.geometry?.dispose();
    if (node.material) {
      for (const material of [].concat(node.material)) {
        material.map?.dispose();
        material.dispose();
      }
    }
  });
  scene.remove(group);
}
function line(points, color, opacity = 0.4, dashed = false) {
  const geometry = new THREE.BufferGeometry().setFromPoints(
    points.map((p) => new THREE.Vector3(...p)),
  );
  const material = dashed
    ? new THREE.LineDashedMaterial({
        color,
        transparent: true,
        opacity,
        dashSize: 0.6,
        gapSize: 0.6,
      })
    : new THREE.LineBasicMaterial({
        color,
        transparent: true,
        opacity,
        depthWrite: false,
      });
  const object = new THREE.Line(geometry, material);
  if (dashed) object.computeLineDistances();
  return object;
}
function label(text, position, size = 2, color = "#9baacb") {
  const c = document.createElement("canvas");
  c.width = 256;
  c.height = 64;
  const ctx = c.getContext("2d");
  ctx.font = "24px monospace";
  ctx.fillStyle = color;
  ctx.textAlign = "center";
  ctx.fillText(text, 128, 42);
  const texture = new THREE.CanvasTexture(c);
  texture.colorSpace = THREE.SRGBColorSpace;
  const sprite = new THREE.Sprite(
    new THREE.SpriteMaterial({
      map: texture,
      transparent: true,
      depthWrite: false,
    }),
  );
  sprite.scale.set(size * 4, size, 1);
  sprite.position.set(...position);
  return sprite;
}
function createGrid() {
  const grid = new THREE.Group();
  for (let i = -40; i <= 40; i += 5) {
    grid.add(
      line(
        [
          [-40, i, -24],
          [40, i, -24],
        ],
        "#7182b8",
        i === 0 ? 0.3 : 0.13,
      ),
      line(
        [
          [i, -40, -24],
          [i, 40, -24],
        ],
        "#7182b8",
        i === 0 ? 0.3 : 0.13,
      ),
    );
  }
  grid.add(
    line(
      [
        [-40, -40, -24],
        [40, -40, -24],
        [40, 40, -24],
        [-40, 40, -24],
        [-40, -40, -24],
      ],
      "#8b8dc0",
      0.2,
    ),
  );
  for (let x = -40; x <= 40; x += 20)
    grid.add(label(String(x), [x, -44, -24], 1.2));
  grid.add(
    label("x / m", [0, -49, -24], 1.4),
    label("y / m", [-45, 0, -24], 1.4),
  );
  scene.add(grid);
}
function createReference(data) {
  const group = new THREE.Group();
  const levels = data.geometry.isosurfaces || [];
  const radius = levels.find((s) => s.f === 0.5)?.radius_m || 20;
  for (let theta = 0; theta < Math.PI; theta += Math.PI / 12) {
    const pts = [];
    for (let i = 0; i <= 120; i++) {
      const phi = (i / 120) * Math.PI * 2;
      pts.push([
        radius * Math.cos(phi) * Math.cos(theta),
        radius * Math.cos(phi) * Math.sin(theta),
        radius * Math.sin(phi),
      ]);
    }
    group.add(line(pts, "#92a4df", 0.26));
  }
  for (let latitude = -60; latitude <= 60; latitude += 20) {
    const lat = (latitude * Math.PI) / 180,
      pts = [];
    for (let i = 0; i <= 144; i++) {
      const p = (i / 144) * Math.PI * 2;
      pts.push([
        radius * Math.cos(lat) * Math.cos(p),
        radius * Math.cos(lat) * Math.sin(p),
        radius * Math.sin(lat),
      ]);
    }
    group.add(line(pts, "#a2a3e8", 0.23));
  }
  for (const surface of levels) {
    const pts = [];
    for (let i = 0; i <= 200; i++) {
      const p = (i / 200) * Math.PI * 2;
      pts.push([
        surface.radius_m * Math.cos(p),
        surface.radius_m * Math.sin(p),
        0,
      ]);
    }
    group.add(line(pts, "#aabafa", surface.f === 0.5 ? 0.75 : 0.27));
  }
  const cabin = new THREE.Group();
  for (let plane = 0; plane < 3; plane++) {
    const pts = [];
    for (let i = 0; i <= 128; i++) {
      const p = (i / 128) * Math.PI * 2,
        a = data.geometry.cabin_radius_m * Math.cos(p),
        b = data.geometry.cabin_radius_m * Math.sin(p);
      pts.push(plane === 0 ? [a, b, 0] : plane === 1 ? [a, 0, b] : [0, a, b]);
    }
    cabin.add(line(pts, "#a0d9f5", 0.28, true));
  }
  group.add(cabin);
  return group;
}
function createField(data) {
  const source = data.slices.find((s) => s.plane === "xy" && s.offset_m === 0);
  const group = new THREE.Group();
  if (!source) return group;
  // Axisymmetry is part of this frozen family. Revolve the central x-y samples
  // about x; color uses the same fixed linear density scale as the 2D slice.
  const extent = Math.min(data.geometry.extent_m, 40),
    positions = [],
    colors = [],
    strengths = [];
  const scale = data.display.rho_scale_abs_J_m3;
  for (let i = 0; i <= 100; i++) {
    const x = -extent + (2 * extent * i) / 100;
    for (let j = 1; j <= 50; j++) {
      const r = (extent * j) / 50,
        value = sampleSlice(source, x, r),
        strength = Math.min(1, Math.abs(value) / scale);
      if (strength < 0.00005) continue;
      const rgb = densityRGB(value, scale);
      const color = new THREE.Color().setRGB(
        rgb[0] / 255,
        rgb[1] / 255,
        rgb[2] / 255,
        THREE.SRGBColorSpace,
      );
      const segments = Math.max(8, Math.ceil(r * 3));
      for (let k = 0; k < segments; k++) {
        const angle = (k / segments) * Math.PI * 2;
        positions.push(x, r * Math.cos(angle), r * Math.sin(angle));
        colors.push(color.r, color.g, color.b);
        strengths.push(strength);
      }
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute(
    "position",
    new THREE.Float32BufferAttribute(positions, 3),
  );
  geometry.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
  geometry.setAttribute(
    "strength",
    new THREE.Float32BufferAttribute(strengths, 1),
  );
  const material = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    vertexColors: true,
    uniforms: { pixelRatio: { value: Math.min(devicePixelRatio || 1, 2) } },
    vertexShader: `attribute float strength; varying vec3 vColor; varying float vStrength; uniform float pixelRatio; void main(){vColor=color;vStrength=strength;vec4 view=modelViewMatrix*vec4(position,1.);gl_Position=projectionMatrix*view;gl_PointSize=clamp(200./-view.z,1.1,3.5)*pixelRatio;}`,
    fragmentShader: `varying vec3 vColor;varying float vStrength;void main(){float r=length(gl_PointCoord-vec2(.5));if(r>.5)discard;float a=(1.-smoothstep(.15,.5,r))*(.12+.78*pow(vStrength,.4));gl_FragColor=vec4(vColor,a);\n#include <tonemapping_fragment>\n#include <colorspace_fragment>}`,
  });
  group.add(new THREE.Points(geometry, material));
  return group;
}
function createRays(data) {
  const group = new THREE.Group(),
    extent = data.geometry.extent_m;
  group.userData.playback = [];
  data.rays.forEach((ray, i) => {
    // Only supplied ray samples are drawn; paths outside the visible cube stop
    // at the cube. Playback interpolates supplied samples in their coordinate
    // time, never extrapolating beyond an individual ray's finite integration.
    let segment = [];
    for (const p of ray.points) {
      if (
        Math.max(Math.abs(p.x_m), Math.abs(p.y_m), Math.abs(p.z_m)) <= extent
      ) {
        segment.push([p.x_m, p.y_m, p.z_m]);
      } else if (segment.length) {
        if (segment.length > 1)
          group.add(line(segment, rayColors[i % rayColors.length], 0.68));
        segment = [];
      }
    }
    if (segment.length > 1)
      group.add(line(segment, rayColors[i % rayColors.length], 0.68));
    try {
      const sampler = createRaySampler(ray.points);
      const marker = new THREE.Group();
      const color = rayColors[i % rayColors.length];
      marker.add(
        new THREE.Mesh(
          new THREE.SphereGeometry(0.28, 8, 6),
          new THREE.MeshBasicMaterial({ color: "#fff7ed" }),
        ),
      );
      marker.add(
        new THREE.Mesh(
          new THREE.SphereGeometry(0.85, 12, 8),
          new THREE.MeshBasicMaterial({
            color,
            transparent: true,
            opacity: 0.18,
            depthWrite: false,
            blending: THREE.AdditiveBlending,
          }),
        ),
      );
      const trail = Array.from(
        { length: 5 },
        (_, j) =>
          new THREE.Mesh(
            new THREE.SphereGeometry(0.24, 6, 4),
            new THREE.MeshBasicMaterial({
              color,
              transparent: true,
              opacity: 0.65 - j * 0.1,
              depthWrite: false,
            }),
          ),
      );
      group.add(marker, ...trail);
      group.userData.playback.push({ sampler, marker, trail });
    } catch {
      // Partial/invalid time series keep their supplied static path only.
    }
  });
  return group;
}
function createCraft(length) {
  const group = new THREE.Group();
  const positions = new Float32Array([
    length / 2,
    0,
    0,
    -length / 2,
    1.5,
    0,
    -length / 2,
    -1.5,
    0,
    -length / 4,
    0,
    1.2,
  ]);
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setIndex([0, 1, 3, 0, 3, 2, 0, 2, 1, 1, 2, 3]);
  geometry.computeVertexNormals();
  group.add(
    new THREE.Mesh(
      geometry,
      new THREE.MeshStandardMaterial({
        color: "#c5d5f6",
        metalness: 0.45,
        roughness: 0.5,
        side: THREE.DoubleSide,
      }),
    ),
  );
  const edges = new THREE.EdgesGeometry(geometry);
  group.add(
    new THREE.LineSegments(
      edges,
      new THREE.LineBasicMaterial({
        color: "#fff1cc",
        transparent: true,
        opacity: 0.8,
      }),
    ),
  );
  return group;
}
function createSlice(data, slice) {
  const n = 160,
    buffer = new Uint8Array(n * n * 4),
    scale = data.display.rho_scale_abs_J_m3;
  for (let j = 0; j < n; j++)
    for (let i = 0; i < n; i++) {
      const u =
          slice.u_m[0] + (i / (n - 1)) * (slice.u_m.at(-1) - slice.u_m[0]),
        v = slice.v_m[0] + (j / (n - 1)) * (slice.v_m.at(-1) - slice.v_m[0]),
        value = sampleSlice(slice, u, v),
        strength = Math.min(1, Math.abs(value) / scale);
      const rgb = densityRGB(value, scale);
      const k = (j * n + i) * 4;
      buffer[k] = rgb[0];
      buffer[k + 1] = rgb[1];
      buffer[k + 2] = rgb[2];
      buffer[k + 3] = Math.round((0.02 + 0.55 * strength) * 255);
    }
  const texture = new THREE.DataTexture(buffer, n, n);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.magFilter = texture.minFilter = THREE.LinearFilter;
  texture.needsUpdate = true;
  const width = slice.u_m.at(-1) - slice.u_m[0],
    height = slice.v_m.at(-1) - slice.v_m[0],
    centerU = (slice.u_m.at(-1) + slice.u_m[0]) / 2,
    centerV = (slice.v_m.at(-1) + slice.v_m[0]) / 2;
  const mesh = new THREE.Mesh(
    new THREE.PlaneGeometry(width, height),
    new THREE.MeshBasicMaterial({
      map: texture,
      transparent: true,
      side: THREE.DoubleSide,
      depthWrite: false,
    }),
  );
  if (slice.plane === "xy") mesh.position.set(centerU, centerV, slice.offset_m);
  else {
    mesh.rotation.set(0, Math.PI / 2, Math.PI / 2);
    mesh.position.set(slice.offset_m, centerU, centerV);
  }
  mesh.renderOrder = 1;
  return mesh;
}
function updateData({ artifact, slice }) {
  if (!renderer) return;
  if (currentArtifact !== artifact) {
    currentArtifact = artifact;
    elapsed_ms = 0;
    for (const group of [field, rayGroup, reference, craft]) dispose(group);
    field = createField(artifact);
    rayGroup = createRays(artifact);
    reference = createReference(artifact);
    craft = createCraft(artifact.geometry.ship_length_m);
    scene.add(field, rayGroup, reference, craft);
  }
  dispose(sliceMesh);
  sliceMesh = createSlice(artifact, slice);
  scene.add(sliceMesh);
  applyLayers();
  requestRender();
}
function applyLayers() {
  if (field) field.visible = layers.field;
  if (sliceMesh) sliceMesh.visible = layers.field;
  if (rayGroup) rayGroup.visible = layers.rays;
  if (reference) reference.visible = layers.reference;
  document.querySelector(".field-key").hidden = !layers.field;
  requestRender();
}
function setCamera(view) {
  if (!camera) return;
  controls.dispose();
  camera.up.set(0, 0, 1);
  controls.target.set(0, 0, 0);
  if (view === "xy") {
    camera.position.set(0, 0, 100);
    camera.up.set(0, 1, 0);
  } else if (view === "yz") {
    camera.position.set(100, 0, 0);
    camera.up.set(0, 0, 1);
  } else camera.position.set(46, -65, 43);
  framingFactor = Math.max(1, 0.9 / (host.clientWidth / host.clientHeight));
  camera.position.multiplyScalar(framingFactor);
  camera.lookAt(0, 0, 0);
  controls = createControls();
  controls.update();
  document.querySelectorAll("[data-camera]").forEach((b) => {
    b.classList.toggle("selected", b.dataset.camera === view);
    b.setAttribute("aria-pressed", String(b.dataset.camera === view));
  });
  requestRender();
}
function createControls() {
  const orbit = new OrbitControls(camera, canvas);
  orbit.enableDamping = !matchMedia("(prefers-reduced-motion: reduce)").matches;
  orbit.dampingFactor = 0.12;
  orbit.enablePan = false;
  orbit.minDistance = 45;
  orbit.maxDistance = 320;
  orbit.addEventListener("change", requestRender);
  orbit.addEventListener("start", () => {
    document.querySelectorAll("[data-camera]").forEach((button) => {
      button.classList.remove("selected");
      button.setAttribute("aria-pressed", "false");
    });
  });
  return orbit;
}
function updateScale() {
  if (!camera) return;
  const center = controls.target.clone(),
    end = center.clone().add(new THREE.Vector3(20, 0, 0));
  const a = center.project(camera),
    b = end.project(camera),
    pixels = (Math.abs(b.x - a.x) * host.clientWidth) / 2;
  const bar = document.querySelector(".scale-bar");
  bar.hidden = pixels < 10 || pixels > host.clientWidth / 2;
  bar.querySelector("i").style.width = pixels + "px";
}
function fail(error) {
  $("scene-fallback").hidden = false;
  $("capture-scene").disabled = true;
  $("motion-toggle").disabled = true;
  $("ray-clock").hidden = true;
  console.error("Ad Astra 3D:", error);
}
try {
  renderer = new THREE.WebGLRenderer({
    canvas,
    alpha: true,
    antialias: true,
    preserveDrawingBuffer: true,
  });
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2("#0b1229", 0.002);
  camera = new THREE.PerspectiveCamera(40, 1, 0.1, 600);
  camera.up.set(0, 0, 1);
  controls = createControls();
  scene.add(new THREE.AmbientLight("#a6baff", 1.8));
  const light = new THREE.DirectionalLight("#ffe9d1", 3);
  light.position.set(10, -20, 30);
  scene.add(light);
  createGrid();
  new ResizeObserver(() => {
    const w = host.clientWidth,
      h = host.clientHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    const factor = Math.max(1, 0.9 / camera.aspect);
    camera.position.multiplyScalar(factor / framingFactor);
    framingFactor = factor;
    camera.updateProjectionMatrix();
    requestRender();
  }).observe(host);
  setCamera("perspective");
  setPlaying(playing);
  $("motion-toggle").addEventListener("click", () => setPlaying(!playing));
  $("ray-clock").title =
    "Shared ray coordinate time; the finite integration is replayed over 12 seconds.";
  motionPreference.addEventListener("change", (event) => {
    if (event.matches) setPlaying(false);
  });
  document.addEventListener("visibilitychange", () => {
    lastTick = null;
    if (!document.hidden) requestRender();
  });
  if (window.WarpProofState) updateData(window.WarpProofState);
  window.addEventListener("warp:select", (event) => updateData(event.detail));
  window.addEventListener("warp:slice", (event) => updateData(event.detail));
  for (const name of ["field", "rays", "reference"])
    $("layer-" + name).addEventListener("click", (event) => {
      layers[name] = !layers[name];
      event.currentTarget.setAttribute("aria-pressed", String(layers[name]));
      applyLayers();
    });
  document
    .querySelectorAll("[data-camera]")
    .forEach((button) =>
      button.addEventListener("click", () => setCamera(button.dataset.camera)),
    );
  $("reset-camera").addEventListener("click", () => setCamera("perspective"));
  canvas.addEventListener("keydown", (event) => {
    if (
      ![
        "ArrowLeft",
        "ArrowRight",
        "ArrowUp",
        "ArrowDown",
        "+",
        "-",
        "=",
        "0",
      ].includes(event.key)
    )
      return;
    event.preventDefault();
    if (event.key === "0") {
      setCamera("perspective");
      return;
    }
    const offset = camera.position.clone().sub(controls.target),
      s = new THREE.Spherical().setFromVector3(
        new THREE.Vector3(offset.x, offset.z, offset.y),
      );
    if (event.key === "ArrowLeft") s.theta -= 0.1;
    if (event.key === "ArrowRight") s.theta += 0.1;
    if (event.key === "ArrowUp") s.phi = Math.max(0.05, s.phi - 0.1);
    if (event.key === "ArrowDown")
      s.phi = Math.min(Math.PI - 0.05, s.phi + 0.1);
    if (["+", "="].includes(event.key))
      s.radius = Math.max(45, s.radius * 0.92);
    if (event.key === "-") s.radius = Math.min(230, s.radius * 1.08);
    const next = new THREE.Vector3().setFromSpherical(s);
    camera.position.set(next.x, next.z, next.y).add(controls.target);
    controls.update();
    requestRender();
  });
  $("capture-scene").addEventListener("click", () => {
    renderer.render(scene, camera);
    const output = document.createElement("canvas");
    output.width = canvas.width;
    output.height = canvas.height + 120;
    const ctx = output.getContext("2d");
    ctx.fillStyle = "#0b1229";
    ctx.fillRect(0, 0, output.width, output.height);
    ctx.drawImage(canvas, 0, 0);
    ctx.font = "14px monospace";
    ctx.fillStyle = "#d4dafa";
    ctx.fillText(
      "Ad Astra · " +
        currentArtifact.candidate.id +
        " · " +
        currentArtifact.benchmark.id,
      22,
      canvas.height + 30,
    );
    ctx.fillStyle = "#9daaca";
    ctx.fillText(
      "Comoving metres · numerical only · reference F surfaces · 8 m scale craft",
      22,
      canvas.height + 53,
    );
    ctx.font = "11px monospace";
    ctx.fillText(
      "Parameters: " + currentArtifact.candidate.parameter_hash,
      22,
      canvas.height + 77,
    );
    ctx.fillText(
      "Ray coordinate time: " +
        $("ray-clock").textContent +
        (layers.rays ? " · sampled finite integration" : " · rays hidden"),
      22,
      canvas.height + 99,
    );
    const link = document.createElement("a");
    link.href = output.toDataURL("image/png");
    link.download = currentArtifact.candidate.id + "-geometry.png";
    link.click();
  });
  canvas.addEventListener("webglcontextlost", (event) => {
    event.preventDefault();
    fail("WebGL context lost. Reload to restore 3D.");
  });
} catch (error) {
  fail(error);
}
