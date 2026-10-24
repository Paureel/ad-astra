import * as THREE from "three";
import { OrbitControls } from "./vendor/OrbitControls.js";
import { StellarOptics, loadCompactCache } from "./optics.js";
import { createRayInspector } from "./ray-inspector.js";

const $ = (id) => document.getElementById(id);
const host = $("scene-container"),
  canvas = $("geometry-canvas");
const { sampleSlice } = window.WarpProofViewer;
const { densityRGB } = window.AdAstraPhysics;
const motionPreference = matchMedia("(prefers-reduced-motion: reduce)");
const mobileGraphics = matchMedia("(pointer: coarse)").matches;
let renderer,
  controls,
  camera,
  scene,
  field,
  reference,
  sliceMesh,
  craft,
  optics;
let pending = false,
  frameHandle = null,
  sceneDirty = true,
  sceneReady = false,
  graphicsState = "starting",
  fatalGraphicsError = false,
  contextLosses = 0,
  contextRestorations = 0,
  gpuFrames = 0,
  currentArtifact = null,
  framingFactor = 1;
let playing = !motionPreference.matches,
  elapsed_ms = 0,
  lastTick = null,
  lastRender = -Infinity,
  frameDeltas = [],
  slowFrames = 0,
  lastQualityChange = 0;
const layers = { field: true, reference: true };

function requestRender() {
  sceneDirty = true;
  scheduleFrame();
}
function scheduleFrame() {
  if (!sceneReady || graphicsState !== "ready" || document.hidden) return;
  if (!pending) {
    pending = true;
    frameHandle = requestAnimationFrame((now) => {
      pending = false;
      frameHandle = null;
      if (graphicsState !== "ready" || document.hidden) {
        lastTick = null;
        return;
      }
      if (playing && lastTick !== null)
        elapsed_ms += Math.max(0, now - lastTick);
      lastTick = now;
      controls.update();
      if (sceneDirty) {
        // Clear before rendering: optical refinement can request the next tile.
        sceneDirty = false;
        renderScene();
        if (lastRender > 0 && now - lastRender < 250) {
          const dt = now - lastRender;
          frameDeltas.push(dt);
          if (frameDeltas.length > 240) frameDeltas.shift();
          slowFrames =
            dt > 27 && dt < 250 ? slowFrames + 1 : Math.max(0, slowFrames - 1);
          // Reduce angular resolution, never the geodesic equations.
          if (slowFrames > 16 && now - lastQualityChange > 1500) {
            if (optics.reduceQuality()) {
              lastQualityChange = now;
              requestRender();
            } else if (renderer.getPixelRatio() > 1) {
              setPixelRatio(1);
              lastQualityChange = now;
            }
            slowFrames = 0;
          }
        }
        updateScale();
        lastRender = now;
      }
      window.dispatchEvent(
        new CustomEvent("astra:frame", { detail: { elapsed_ms } }),
      );
      // The illustrative 2D mass rotation does not change the 3D scene.
      if (playing) scheduleFrame();
    });
  }
}
function renderScene() {
  if (graphicsState !== "ready" || renderer.getContext().isContextLost()) return;
  // The schematic scale craft must not enclose and obscure a cabin observer.
  if (craft) craft.visible = camera.position.length() > 6;
  renderer.autoClear = true;
  optics.render(camera);
  renderer.autoClear = false;
  renderer.clearDepth();
  renderer.render(scene, camera);
  gpuFrames++;
}
function setPixelRatio(value) {
  renderer.setPixelRatio(value);
  for (const points of field?.children || [])
    points.material.uniforms.pixelRatio.value = renderer.getPixelRatio();
  requestRender();
}
function solutionFor(data) {
  return window.AD_ASTRA_SOLUTIONS.solutions.find(
    (s) =>
      s.parameter_hash === data.candidate.parameter_hash &&
      s.evaluator_source_sha256 === data.provenance?.evaluator_source_sha256,
  );
}
function setPlaying(value) {
  playing = value;
  lastTick = null;
  const button = $("motion-toggle");
  button.setAttribute("aria-pressed", String(playing));
  const action = playing
    ? "Pause mass-comparison rotation"
    : "Play mass-comparison rotation";
  button.setAttribute("aria-label", action);
  button.title = action;
  document.documentElement.dataset.motion = playing ? "on" : "off";
  requestRender();
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
  const solution = solutionFor(data);
  if (solution) {
    // g_00 = |W|² - 1. This selected-metric stationary limit is neither
    // a hull nor a global causal horizon. Spatial slices remain Euclidean.
    const meridian = solution.surface_meridian;
    for (let k = 0; k < 8; k++) {
      const phi = (k * Math.PI) / 4;
      group.add(
        line(
          meridian.map(([x, r]) => [x, r * Math.cos(phi), r * Math.sin(phi)]),
          "#a5b7f2",
          0.22,
        ),
      );
    }
    for (let j = 16; j < 128; j += 16) {
      const [x, r] = meridian[j],
        pts = [];
      for (let k = 0; k <= 96; k++) {
        const phi = (k * Math.PI) / 48;
        pts.push([x, r * Math.cos(phi), r * Math.sin(phi)]);
      }
      group.add(line(pts, "#a5b7f2", 0.16));
    }
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
  const group = new THREE.Group(),
    solution = solutionFor(data);
  const clouds = [0, 1].map(() => ({
    positions: [],
    colors: [],
  }));
  const scale = data.display.rho_scale_abs_J_m3;
  let samples = solution?.density_meridian;
  if (!samples) {
    // Older local artifacts have no independently generated display mesh.
    // Retain their sampled field, but never substitute the baseline surface.
    const source = data.slices.find(
      (s) => s.plane === "xy" && s.offset_m === 0,
    );
    samples = [];
    if (source)
      for (let i = 0; i <= 100; i++)
        for (let j = 1; j <= 50; j++) {
          const x = -40 + 0.8 * i,
            r = 0.8 * j,
            v = sampleSlice(source, x, r) / scale;
          if (Math.abs(v) >= 0.00005) samples.push([x, r, v]);
        }
  }
  samples.forEach(([x, r, value]) => {
    const rgb = densityRGB(value * scale, scale),
      color = new THREE.Color().setRGB(
        ...rgb.map((v) => v / 255),
        THREE.SRGBColorSpace,
      );
    const { positions, colors } = clouds[value < 0 ? 1 : 0];
    // Stagger azimuthal samples to avoid visually inventing meridional bands.
    const phase = x * 2.399963229728653 + r * 0.7548776662466927;
    // A fixed count undersamples the large outer negative region. Follow
    // circumference for both signs; don't stack duplicate samples on the axis.
    const azimuths = r<1e-6 ? 1 : Math.max(12,Math.min(64,Math.ceil(2*Math.PI*r/6)));
    for (let k = 0; k < azimuths; k++) {
      const phi = (k * Math.PI * 2) / azimuths + phase;
      positions.push(x, r * Math.cos(phi), r * Math.sin(phi));
      colors.push(color.r, color.g, color.b);
    }
  });
  clouds.forEach(({ positions, colors }) => {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute(
      "position",
      new THREE.Float32BufferAttribute(positions, 3),
    );
    geometry.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
    const material = new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      vertexColors: true,
      depthTest: true,
      uniforms: {
        pixelRatio: { value: renderer.getPixelRatio() },
      },
      vertexShader: `varying vec3 vColor;uniform float pixelRatio;
      void main(){vColor=color;vec4 view=modelViewMatrix*vec4(position,1.);gl_Position=projectionMatrix*view;gl_PointSize=clamp(200./-view.z,2.5,3.5)*pixelRatio;}`,
      fragmentShader: `varying vec3 vColor;
      void main(){float r=length(gl_PointCoord-vec2(.5));if(r>.5)discard;float a=(1.-smoothstep(.15,.5,r))*.6;gl_FragColor=vec4(vColor,a);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>}`,
    });
    const points = new THREE.Points(geometry, material);
    // Identical point size, opacity and depth treatment for both signs.
    points.renderOrder = 0;
    group.add(points);
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
    if ($("ray-dialog").open) $("ray-dialog").close();
    currentArtifact = artifact;
    optics.setArtifact(artifact);
    elapsed_ms = 0;
    for (const group of [field, reference, craft]) dispose(group);
    field = createField(artifact);
    reference = createReference(artifact);
    craft = createCraft(artifact.geometry.ship_length_m);
    scene.add(field, reference, craft);
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
    camera.position.set(0, 0, 330);
    camera.up.set(0, 1, 0);
  } else if (view === "yz") {
    camera.position.set(330, 0, 0);
    camera.up.set(0, 0, 1);
  } else camera.position.set(-167.67, -236.925, 156.735);
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
  orbit.minDistance = 0.35;
  orbit.maxDistance = 800;
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
function setupDiagnostics() {
  // Opt-in local QA: no readbacks or benchmark motion during normal use.
  let benchmarking = false;
  window.AdAstraDiagnostics = {
    snapshot() {
      const sorted = frameDeltas.slice().sort((a, b) => a - b);
      return {
        fps: sorted.length
          ? 1000 / (sorted.reduce((a, b) => a + b, 0) / sorted.length)
          : null,
        p95_frame_ms: sorted[Math.floor(sorted.length * 0.95)] ?? null,
        pixel_ratio: renderer.getPixelRatio(),
        renderer: renderer.info.render,
        optics: optics.diagnostics(),
        surface: solutionFor(currentArtifact)?.surface_quantity,
        field_vertices: field?.children.reduce(
          (n, p) => n + p.geometry.attributes.position.count,
          0,
        ),
        playing,
        graphics_state: graphicsState,
        context_losses: contextLosses,
        context_restorations: contextRestorations,
        gpu_frames: gpuFrames,
        gpu_memory: { ...renderer.info.memory },
        mobile_graphics: mobileGraphics,
        shader_errors:window.AdAstraShaderErrors||[],
        candidate_id:currentArtifact?.candidate.id,
        parameter_hash:currentArtifact?.candidate.parameter_hash,
        benchmark_id:currentArtifact?.benchmark.id,
        ray_count: currentArtifact?.rays.length,
        observer_m: camera.position.toArray(),
        view_direction: camera.getWorldDirection(new THREE.Vector3()).toArray(),
      };
    },
    audit(ray = null, {inside=false} = {}) {
      const solution = solutionFor(currentArtifact);
      if (!solution)
        throw new Error("No independent fixtures for this artifact.");
      const result = optics.audit(
        solution.field_audit,
        inside ? solution.optical_inside_reference : solution.optical_reference,
        ray,
      );
      requestRender();
      return result;
    },
    setOpticalRows(rows) {
      if (!Number.isInteger(rows) || rows < 72 || rows > 576)
        throw new Error("Audit resolution must be 72–576 rows.");
      optics.quality = rows / optics.baseRows;
      optics.dirty = true;
      requestRender();
    },
    setObserver(position) {
      if (
        !Array.isArray(position) ||
        position.length !== 3 ||
        !position.every(Number.isFinite) ||
        Math.hypot(...position) < 0.35 ||
        Math.hypot(...position) > 800
      )
        throw new Error("Observer must be within the supported camera range.");
      camera.position.set(...position);
      camera.lookAt(0, 0, 0);
      controls.update();
      requestRender();
    },
    async benchmark({ orbit = true, duration_ms = 6000 } = {}) {
      if (benchmarking) throw new Error("Benchmark already running.");
      benchmarking = true;
      const saved = camera.position.clone(),
        wasPlaying = playing;
      controls.enableDamping = false;
      setPlaying(true);
      frameDeltas = [];
      try {
        await new Promise((resolve) => {
          let start = null;
          const tick = (now) => {
            if (start === null) start = now;
            if (orbit) {
              const a = (now - start) * 0.00013;
              camera.position
                .copy(saved)
                .applyAxisAngle(new THREE.Vector3(0, 0, 1), a);
              camera.lookAt(0, 0, 0);
            }
            requestRender();
            if (now - start >= duration_ms) resolve();
            else requestAnimationFrame(tick);
          };
          requestAnimationFrame(tick);
        });
        return this.snapshot();
      } finally {
        camera.position.copy(saved);
        controls.enableDamping = !motionPreference.matches;
        controls.update();
        setPlaying(wasPlaying);
        benchmarking = false;
        requestRender();
      }
    },
  };
}
function fail(error) {
  fatalGraphicsError = true;
  graphicsState = "failed";
  $("scene-fallback").textContent = "3D unavailable. Open the density slice to inspect the computed field.";
  $("scene-fallback").hidden = false;
  $("capture-scene").disabled = true;
  $("motion-toggle").disabled = true;
  console.error("Ad Astra 3D:", error);
}
try {
  renderer = new THREE.WebGLRenderer({
    canvas,
    alpha: true,
    antialias: !mobileGraphics,
    preserveDrawingBuffer: false,
  });
  setPixelRatio(Math.min(devicePixelRatio || 1, mobileGraphics ? 1.25 : 1.5));
  // Install these before loading the field cache: Safari can reset the GPU
  // during initial loading as well as while switching or restoring tabs.
  canvas.addEventListener("webglcontextlost", (event) => {
    event.preventDefault();
    if (fatalGraphicsError) return;
    graphicsState = "lost";
    contextLosses++;
    if (frameHandle !== null) cancelAnimationFrame(frameHandle);
    pending = false;
    frameHandle = null;
    lastTick = null;
    optics?.suspend();
    $("scene-fallback").textContent = "Restoring 3D…";
    $("scene-fallback").hidden = false;
    $("capture-scene").disabled = true;
    $("motion-toggle").disabled = true;
  });
  canvas.addEventListener("webglcontextrestored", () => {
    if (fatalGraphicsError) return;
    contextRestorations++;
    // Three.js rebuilds its GL resources before this listener runs. Optical
    // render targets contain no valid directions until explicitly recalculated.
    optics?.restoreContext();
    setPixelRatio(1);
    renderer.setSize(host.clientWidth, host.clientHeight, false);
    optics?.reduceQuality();
    graphicsState = sceneReady ? "ready" : "starting";
    $("scene-fallback").hidden = true;
    $("capture-scene").disabled = false;
    $("motion-toggle").disabled = false;
    if (optics) $("stellar-lensing").disabled = !optics.available;
    lastTick = null;
    lastRender = -Infinity;
    requestRender();
  });
  renderer.debug.onShaderError=(gl,program,vertex,fragment)=>{
    if (gl.isContextLost()) return;
    (window.AdAstraShaderErrors ||= []).push(gl.getProgramInfoLog(program)+"\n"+gl.getShaderInfoLog(vertex)+"\n"+gl.getShaderInfoLog(fragment));
    fail("3D graphics could not be compiled. Reload to retry.");
  };
  optics = new StellarOptics(renderer, requestRender, await loadCompactCache(), { mobile: mobileGraphics });
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2("#0b1229", 0.002);
  camera = new THREE.PerspectiveCamera(40, 1, 0.02, 2000);
  camera.up.set(0, 0, 1);
  controls = createControls();
  scene.add(new THREE.AmbientLight("#a6baff", 1.8));
  const light = new THREE.DirectionalLight("#ffe9d1", 3);
  light.position.set(10, -20, 30);
  scene.add(light);
  createGrid();
  createRayInspector({
    getArtifact: () => currentArtifact,
    isPlaying: () => playing,
    setPlaying,
  });
  setupDiagnostics();
  $("stellar-lensing").disabled = !optics.available;
  $("stellar-lensing").setAttribute("aria-pressed", String(optics.available));
  $("stellar-lensing").addEventListener("click", (event) => {
    optics.setEnabled(!optics.enabled);
    event.currentTarget.setAttribute("aria-pressed", String(optics.enabled));
  });
  new ResizeObserver(() => {
    const w = host.clientWidth,
      h = host.clientHeight;
    if (!w || !h) return;
    const previous = renderer.getSize(new THREE.Vector2());
    if (graphicsState !== "lost" && (previous.x !== w || previous.y !== h))
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
  motionPreference.addEventListener("change", (event) => {
    if (event.matches) setPlaying(false);
  });
  document.addEventListener("visibilitychange", () => {
    lastTick = null;
    lastRender = -Infinity;
    if (document.hidden) optics.suspend();
    else requestRender();
  });
  if (window.WarpProofState) updateData(window.WarpProofState);
  window.addEventListener("warp:select", (event) => updateData(event.detail));
  window.addEventListener("warp:slice", (event) => updateData(event.detail));
  for (const name of ["field", "reference"])
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
      s.radius = Math.max(0.35, s.radius * 0.85);
    if (event.key === "-") s.radius = Math.min(800, s.radius * 1.08);
    const next = new THREE.Vector3().setFromSpherical(s);
    camera.position.set(next.x, next.z, next.y).add(controls.target);
    controls.update();
    requestRender();
  });
  $("capture-scene").addEventListener("click", () => {
    renderScene();
    const output = document.createElement("canvas");
    output.width = canvas.width;
    const meta = optics.diagnostics(),
      view = camera.getWorldDirection(new THREE.Vector3());
    const captions = [
      `Ad Astra · ${currentArtifact.candidate.id} · ${currentArtifact.benchmark.id}`,
      "Comoving metres · numerical only · g00 = 0 surface · schematic 8 m craft",
      "Color: symmetric asinh contrast; identical glyph size/opacity for both signs",
      "Parameters: " + currentArtifact.candidate.parameter_hash,
      "Observer / m: " +
        camera.position
          .toArray()
          .map((x) => x.toPrecision(8))
          .join(", "),
      "View direction: " +
        view
          .toArray()
          .map((x) => x.toPrecision(8))
          .join(", "),
      `Sky: ${meta.width} x ${meta.height}; ${meta.refined ? "refined" : "interactive"}; finite-boundary angular approximation`,
    ];
    const ctx = output.getContext("2d");
    ctx.font = "11px monospace";
    const lines = [];
    for (const caption of captions) {
      let line = "";
      for (const char of caption) {
        if (ctx.measureText(line + char).width > output.width - 44) {
          lines.push(line);
          line = "";
        }
        line += char;
      }
      if (line) lines.push(line);
    }
    output.height = canvas.height + lines.length * 16 + 28;
    ctx.fillStyle = "#0b1229";
    ctx.fillRect(0, 0, output.width, output.height);
    ctx.drawImage(canvas, 0, 0);
    ctx.font = "11px monospace";
    lines.forEach((line, i) => {
      ctx.fillStyle = i === 0 ? "#d4dafa" : "#9daaca";
      ctx.fillText(line, 22, canvas.height + 22 + i * 16);
    });
    const link = document.createElement("a");
    link.href = output.toDataURL("image/png");
    link.download = currentArtifact.candidate.id + "-geometry.png";
    link.click();
  });
  sceneReady = true;
  graphicsState = renderer.getContext().isContextLost() ? "lost" : "ready";
  requestRender();
} catch (error) {
  fail(error);
}
