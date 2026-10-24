"use strict";
const assert = require("node:assert/strict"),
  fs = require("node:fs/promises"),
  path = require("node:path"),
  os = require("node:os"),
  { pathToFileURL } = require("node:url");
(async () => {
  // Run the actual vendored controls with a minimal event target, no browser or
  // rendering engine. .mjs copies also work on the repository's Node 18 target.
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), "ad-astra-controls-"));
  try {
    const three = path.join(dir, "three.mjs"),
      orbit = path.join(dir, "OrbitControls.mjs");
    await fs.copyFile(
      path.join(__dirname, "vendor/three.module.min.js"),
      three,
    );
    await fs.copyFile(
      path.join(__dirname, "vendor/three.core.min.js"),
      path.join(dir, "three.core.mjs"),
    );
    await fs.writeFile(
      three,
      (await fs.readFile(three, "utf8")).replaceAll(
        "./three.core.min.js",
        "./three.core.mjs",
      ),
    );
    await fs.writeFile(
      orbit,
      (
        await fs.readFile(
          path.join(__dirname, "vendor/OrbitControls.js"),
          "utf8",
        )
      ).replace("from 'three'", "from '" + pathToFileURL(three).href + "'"),
    );
    const THREE = await import(pathToFileURL(three).href),
      { OrbitControls } = await import(pathToFileURL(orbit).href);
    const handlers = new Map(),
      root = { addEventListener() {}, removeEventListener() {} };
    const element = {
      style: {},
      clientHeight: 800,
      clientWidth: 1200,
      getRootNode: () => root,
      setPointerCapture() {},
      releasePointerCapture() {},
      addEventListener(name, fn) {
        handlers.set(name, fn);
      },
      removeEventListener(name) {
        handlers.delete(name);
      },
      getBoundingClientRect: () => ({
        left: 0,
        top: 0,
        width: 1200,
        height: 800,
      }),
    };
    const camera = new THREE.PerspectiveCamera(40, 1.5, 0.02, 600);
    camera.position.set(-62, -88, 58);
    const controls = new OrbitControls(camera, element);
    controls.enablePan = false;
    controls.minDistance = 0.35;
    controls.maxDistance = 320;
    let starts = 0,
      ends = 0;
    controls.addEventListener("start", () => starts++);
    controls.addEventListener("end", () => ends++);
    const pointer = {
      pointerId: 1,
      pointerType: "mouse",
      button: 0,
      clientX: 600,
      clientY: 400,
      pageX: 600,
      pageY: 400,
    };
    handlers.get("pointerdown")(pointer);
    handlers.get("pointermove")({ ...pointer, clientX: 650, clientY: 430 });
    const before = camera.position.length(),
      state = controls.state;
    const wheel = {
      deltaY: -800,
      deltaMode: 0,
      clientX: 650,
      clientY: 430,
      preventDefault() {},
    };
    handlers.get("wheel")(wheel);
    assert.ok(
      camera.position.length() < before,
      "Wheel zoom works while the left pointer is held.",
    );
    assert.equal(
      controls.state,
      state,
      "Zoom preserves the active orbit state.",
    );
    assert.equal(starts, 1);
    assert.equal(ends, 0, "Wheel does not prematurely end the orbit.");
    const direction = camera.position.clone().normalize();
    handlers.get("pointermove")({ ...pointer, clientX: 680, clientY: 460 });
    assert.ok(
      direction.distanceTo(camera.position.clone().normalize()) > 0.01,
      "Dragging continues after wheel zoom.",
    );
    for (let i = 0; i < 20; i++) handlers.get("wheel")(wheel);
    assert.ok(
      camera.position.length() < 10,
      "The observer can enter the 10 m cabin.",
    );
    assert.ok(
      camera.position.length() >= 0.35 - 1e-10,
      "The camera stays outside the zero-radius singularity.",
    );
    handlers.get("pointerup")(pointer);
    assert.equal(ends, 1);
    controls.dispose();
    console.log(
      "PASS: real OrbitControls held-drag wheel zoom, continued rotation, cabin access, and gesture lifecycle.",
    );
  } finally {
    await fs.rm(dir, { recursive: true, force: true });
  }
})().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
