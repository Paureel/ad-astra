import * as THREE from "three";
import { SATURN, SATURN_GLSL } from "./saturn.js";

const VERTEX = `varying vec2 screenUV;void main(){screenUV=uv;gl_Position=vec4(position.xy,0.,1.);}`;
const TRACE = `
precision highp float;
varying vec2 screenUV;
uniform vec3 observer;uniform mat3 orientation;uniform float aspect;uniform float tangent;
uniform float boundary;uniform int budget;uniform float fixedCt;uniform float fixedStep;uniform float stepScale;
uniform int auditMode;uniform vec3 auditPoint;
uniform vec2 mapOffset;uniform vec2 mapScale;
uniform float stepCenter;uniform float stepWidth;
${window.AdAstraMetric.GLSL}
void main(){
 if(auditMode>0&&auditMode<5){Metric M=metricFields(auditPoint);if(auditMode==1)gl_FragColor=vec4(M.W,1.);else gl_FragColor=vec4(M.K[auditMode-2],1.);return;}
 vec2 xy=(mapOffset+screenUV*mapScale)*2.-1.;
 vec3 view=normalize(orientation*vec3(xy.x*aspect*tangent,xy.y*tangent,-1.));
 vec3 q=observer,n=-view;float ell=0.,ct=0.;
 float initialP0=dot(metricFields(q).W,n)-1.;
 for(int i=0;i<2048;i++){
  if(i>=budget||length(q)>=boundary||(fixedCt>0.&&ct>=fixedCt-0.00001))break;
  float h=fixedStep>0.?fixedStep:stepScale*(modelKind==1?.25:1.)*clamp((abs(length(q)-stepCenter)-stepWidth)*.15,.12,8192.);
  if(fixedCt>0.)h=min(h,fixedCt-ct);
  opticalStep(q,n,ell,h);ct+=h;
 }
 if(auditMode==5){gl_FragColor=vec4(q,ct);return;}
 if(auditMode==6){gl_FragColor=vec4(n,ell);return;}
 float finalP0=exp(clamp(ell,-40.,40.))*(dot(metricFields(q).W,n)-1.);
 float drift=abs(finalP0-initialP0)/max(.001,abs(initialP0));
 float valid=(length(q)>=boundary&&drift<.02&&abs(ell)<40.)?1.:0.;
 gl_FragColor=vec4((-n)*.5+.5,valid);
}`;
const SKY = `
varying vec2 screenUV;
uniform sampler2D directionMap;uniform sampler2D skyMap;uniform mat3 orientation;
uniform float aspect;uniform float tangent;uniform bool lensed;uniform bool skyReady;
uniform float continuityThreshold;
${SATURN_GLSL}
void main(){
 vec2 xy=screenUV*2.-1.;vec3 d=normalize(orientation*vec3(xy.x*aspect*tangent,xy.y*tangent,-1.));
 float valid=1.;if(lensed){vec4 ray=texture2D(directionMap,screenUV);vec3 raw=ray.rgb*2.-1.;valid=step(.999,ray.a)*step(continuityThreshold,length(raw));d=normalize(raw);}
 vec2 uv=vec2(atan(d.y,d.x)/6.28318530718+.5,asin(clamp(d.z,-1.,1.))/3.14159265359+.5);
 vec3 stars=skyReady?texture2D(skyMap,uv).rgb:vec3(0.);
 vec3 base=vec3(.003,.006,.017);
 // A quiet reference sky. Catalogue colors/fluxes retain fixed display exposure;
 // this pass predicts directions, not redshifted stellar spectra or photometry.
 vec3 sky=base+stars*.38;
 gl_FragColor=vec4(valid>0.?saturn(d,sky):base,1.);
 #include <colorspace_fragment>
}`;

function plane(material) {
  const scene = new THREE.Scene();
  scene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), material));
  return scene;
}

export async function loadCompactCache() {
  const entry=(window.WARP_BUNDLED_HISTORY||[]).find(e=>e.artifact.candidate.parameters.family==="compact100");
  if(!entry)return null;
  const meta=entry.artifact.provenance.optical_cache;
  if(meta.path!=="compact100-fields.bin" || meta.radial_nodes!==1025 || meta.angular_nodes!==513)
    throw new Error("Unsupported compact optical cache.");
  const response=await fetch(meta.path);
  if(!response.ok)throw new Error("Compact optical cache could not be loaded.");
  const bytes=await response.arrayBuffer();
  if(bytes.byteLength!==meta.radial_nodes*meta.angular_nodes*32)throw new Error("Incomplete compact optical cache.");
  const hash=Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",bytes)),v=>v.toString(16).padStart(2,"0")).join("");
  if(hash!==meta.sha256)throw new Error("Compact optical cache hash differs from its geometry.");
  const data=new Float32Array(bytes),half=data.length/2;
  return {a:data.subarray(0,half),b:data.subarray(half),nr:meta.radial_nodes,nm:meta.angular_nodes,hash};
}

export class StellarOptics {
  constructor(renderer, invalidate, compactCache = null) {
    this.renderer = renderer;
    this.invalidate = invalidate;
    this.camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    this.enabled = true;
    this.dirty = true;
    this.quality = 1;
    this.signature = "";
    this.changedAt = 0;
    this.refineIndex = 0;
    this.refined = false;
    this.refineTimer = null;
    this.available = !!renderer
      .getContext()
      .getExtension("EXT_color_buffer_float");
    this.floatLinear = !!renderer
      .getContext()
      .getExtension("OES_texture_float_linear");
    this.compactCache=compactCache;
    this.compactTextures=[compactCache?.a,compactCache?.b].map(data=>{
      const texture=new THREE.DataTexture(data||new Float32Array(4),compactCache?.nr||1,compactCache?.nm||1,THREE.RGBAFormat,THREE.FloatType);
      texture.minFilter=texture.magFilter=this.floatLinear?THREE.LinearFilter:THREE.NearestFilter;
      texture.needsUpdate=true;return texture;
    });
    this.traceMaterial = new THREE.ShaderMaterial({
      vertexShader: VERTEX,
      fragmentShader: TRACE,
      depthWrite: false,
      depthTest: false,
      toneMapped: false,
      uniforms: {
        observer: { value: new THREE.Vector3() },
        orientation: { value: new THREE.Matrix3() },
        aspect: { value: 1 },
        tangent: { value: 1 },
        beta: { value: 2 },
        profileR: { value: 20 },
        stepCenter:{value:20}, stepWidth:{value:4},
        modelKind:{value:0},compactA:{value:this.compactTextures[0]},compactB:{value:this.compactTextures[1]},
        compactSize:{value:new THREE.Vector2(compactCache?.nr||1,compactCache?.nm||1)},compactLinear:{value:this.floatLinear},
        sigma: { value: 1 },
        termCount: { value: 0 },
        terms: { value: Array.from({ length: 9 }, () => new THREE.Vector3()) },
        boundary: { value: 65536 },
        budget: { value: 640 },
        stepScale: { value: 0.5 },
        fixedCt: { value: 0 },
        fixedStep: { value: 0 },
        auditMode: { value: 0 },
        auditPoint: { value: new THREE.Vector3() },
        mapOffset: { value: new THREE.Vector2(0, 0) },
        mapScale: { value: new THREE.Vector2(1, 1) },
      },
    });
    this.traceScene = plane(this.traceMaterial);
    this.target = new THREE.WebGLRenderTarget(128, 72, {
      type: this.floatLinear ? THREE.FloatType : THREE.HalfFloatType,
      minFilter: THREE.LinearFilter,
      magFilter: THREE.LinearFilter,
      depthBuffer: false,
    });
    this.fineTarget = this.target.clone();
    const skyTexture = new THREE.TextureLoader().load("stars.png", () => {
      this.skyMaterial.uniforms.skyReady.value = true;
      invalidate();
    });
    skyTexture.colorSpace = THREE.SRGBColorSpace;
    skyTexture.wrapS = THREE.RepeatWrapping;
    skyTexture.wrapT = THREE.ClampToEdgeWrapping;
    this.skyMaterial = new THREE.ShaderMaterial({
      vertexShader: VERTEX,
      fragmentShader: SKY,
      depthWrite: false,
      depthTest: false,
      toneMapped: false,
      uniforms: {
        directionMap: { value: this.target.texture },
        skyMap: { value: skyTexture },
        orientation: { value: new THREE.Matrix3() },
        aspect: { value: 1 },
        tangent: { value: 1 },
        lensed: { value: this.available },
        skyReady: { value: false },
        continuityThreshold: { value: this.floatLinear ? 0.9998 : 0.998 },
      },
    });
    this.skyScene = plane(this.skyMaterial);
  }
  setArtifact(artifact) {
    this.metric = window.AdAstraMetric.createMetric(
      artifact.candidate.parameters,
    );
    const u = this.traceMaterial.uniforms,
      m = this.metric;
    if(m.family==="compact100" && this.compactCache?.hash!==artifact.provenance.optical_cache.sha256)
      throw new Error("The selected compact geometry and optical cache differ.");
    this.parameterHash=artifact.candidate.parameter_hash;
    u.modelKind.value=m.family==="compact100"?1:0;
    u.stepCenter.value=m.stepCenter;
    u.stepWidth.value=m.stepWidth;
    u.beta.value = m.beta;
    u.profileR.value = m.R;
    u.sigma.value = m.sigma;
    u.termCount.value = m.terms.length;
    m.terms.forEach((term, i) => u.terms.value[i].set(...term));
    this.dirty = true;
    this.refined = false;
    this.refineIndex = 0;
    clearTimeout(this.refineTimer);
  }
  setEnabled(value) {
    this.enabled = value;
    this.invalidate();
  }
  reduceQuality() {
    if (this.quality > 0.58) {
      this.quality *= 0.8;
      this.dirty = true;
      return true;
    }
    return false;
  }
  render(camera) {
    camera.updateMatrixWorld();
    const orientation = new THREE.Matrix3().setFromMatrix4(camera.matrixWorld);
    const tangent = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
    const signature = [...camera.matrixWorld.elements, camera.aspect].join(",");
    const sy = this.skyMaterial.uniforms,
      tr = this.traceMaterial.uniforms;
    sy.orientation.value.copy(orientation);
    sy.aspect.value = camera.aspect;
    sy.tangent.value = tangent;
    sy.lensed.value = this.available && this.enabled && !!this.metric;
    if (sy.lensed.value && (this.dirty || signature !== this.signature)) {
      const h = Math.round(144 * this.quality),
        w = Math.max(32, Math.round(h * camera.aspect));
      if (this.target.width !== w || this.target.height !== h)
        this.target.setSize(w, h);
      tr.observer.value.copy(camera.position);
      tr.orientation.value.copy(orientation);
      tr.aspect.value = camera.aspect;
      tr.tangent.value = tangent;
      this.renderer.setRenderTarget(this.target);
      this.renderer.render(this.traceScene, this.camera);
      this.renderer.setRenderTarget(null);
      this.signature = signature;
      this.dirty = false;
      sy.directionMap.value = this.target.texture;
      this.changedAt = performance.now();
      this.refineIndex = 0;
      this.refined = false;
      clearTimeout(this.refineTimer);
      this.refineTimer = setTimeout(this.invalidate, 140);
    } else if (
      sy.lensed.value &&
      !this.refined &&
      performance.now() - this.changedAt >= 120
    ) {
      // Refine a stationary view in small tiles. Each tile has less work than
      // a full interactive map, avoiding a long single-frame GPU submission.
      const w = this.target.width * 2,
        h = this.target.height * 2;
      if (this.fineTarget.width !== w || this.fineTarget.height !== h)
        this.fineTarget.setSize(w, h);
      const ix = this.refineIndex % 4,
        iy = Math.floor(this.refineIndex / 4);
      const x = Math.floor((ix * w) / 4),
        y = Math.floor((iy * h) / 4),
        tw = Math.floor(((ix + 1) * w) / 4) - x,
        th = Math.floor(((iy + 1) * h) / 4) - y;
      this.fineTarget.viewport.set(x, y, tw, th);
      this.fineTarget.scissor.set(x, y, tw, th);
      this.fineTarget.scissorTest = true;
      tr.mapOffset.value.set(x / w, y / h);
      tr.mapScale.value.set(tw / w, th / h);
      tr.stepScale.value = 0.25;
      tr.budget.value = 1280;
      this.renderer.setRenderTarget(this.fineTarget);
      this.renderer.render(this.traceScene, this.camera);
      this.renderer.setRenderTarget(null);
      tr.mapOffset.value.set(0, 0);
      tr.mapScale.value.set(1, 1);
      tr.stepScale.value = 0.5;
      tr.budget.value = 640;
      if (++this.refineIndex === 16) {
        this.refined = true;
        sy.directionMap.value = this.fineTarget.texture;
      } else this.invalidate();
    }
    this.renderer.render(this.skyScene, this.camera);
  }
  diagnostics() {
    return {
      available: this.available,
      family:this.metric?.family,
      parameter_hash:this.parameterHash,
      cache_sha256:this.metric?.family==="compact100"?this.compactCache?.hash:null,
      lensed: this.enabled,
      width: this.refined ? this.fineTarget.width : this.target.width,
      height: this.refined ? this.fineTarget.height : this.target.height,
      refined: this.refined,
      boundary_m: 65536,
      step_budget: 640,
      step_scale: 0.5,
      refined_step_budget: 1280,
      refined_step_scale: 0.25,
      method:
        "RK4, normalized Eulerian direction, adaptive distance steps; finite-boundary angular mapping",
      spectra: "catalogue reference colors, redshift photometry omitted",
      saturn: SATURN,
    };
  }
  audit(fixtures, reference, selectedRay = null) {
    if (!this.available)
      throw new Error("Floating-point optical audit unavailable.");
    const target = new THREE.WebGLRenderTarget(1, 1, {
      type: THREE.FloatType,
      depthBuffer: false,
    });
    const u = this.traceMaterial.uniforms,
      pixels = new Float32Array(4);
    let maxW = 0,
      maxK = 0;
    const read = () => {
      this.renderer.setRenderTarget(target);
      this.renderer.render(this.traceScene, this.camera);
      this.renderer.readRenderTargetPixels(target, 0, 0, 1, 1, pixels);
      return [...pixels];
    };
    for (const f of fixtures) {
      u.auditPoint.value.set(...f.q);
      for (let mode = 1; mode <= 4; mode++) {
        u.auditMode.value = mode;
        const x = read();
        for (let i = 0; i < 3; i++)
          if (mode === 1) maxW = Math.max(maxW, Math.abs(x[i] - f.W[i]));
          else maxK = Math.max(maxK, Math.abs(x[i] - f.K[(mode - 2) * 3 + i]));
      }
    }
    // One pixel along the known reference direction, using the same GPU RK4.
    const forward = new THREE.Vector3(...reference.view),
      right = new THREE.Vector3()
        .crossVectors(forward, new THREE.Vector3(0, 0, 1))
        .normalize(),
      up = new THREE.Vector3().crossVectors(right, forward).normalize();
    const basis = new THREE.Matrix4().makeBasis(
      right,
      up,
      forward.clone().negate(),
    );
    u.observer.value.set(...reference.origin);
    u.orientation.value.setFromMatrix4(basis);
    u.fixedCt.value = reference.past_ct_m;
    u.fixedStep.value = this.metric.family==="compact100"?.05:.2;
    u.budget.value = Math.ceil(reference.past_ct_m/u.fixedStep.value)+1;
    u.auditMode.value = 5;
    const q = read();
    u.auditMode.value = 6;
    const n = read();
    const position_error_m = Math.hypot(
      ...q.slice(0, 3).map((v, i) => v - reference.state[i]),
    );
    const direction_error_rad = Math.hypot(
      ...n.slice(0, 3).map((v, i) => v - reference.state[3 + i]),
    );
    u.auditMode.value = 0;
    u.fixedCt.value = 0;
    u.fixedStep.value = 0;
    u.budget.value = 640;
    if (selectedRay) {
      const forward = new THREE.Vector3(...selectedRay.view).normalize(),
        right = new THREE.Vector3()
          .crossVectors(forward, new THREE.Vector3(0, 0, 1))
          .normalize(),
        up = new THREE.Vector3().crossVectors(right, forward).normalize();
      u.observer.value.set(...selectedRay.origin);
      u.orientation.value.setFromMatrix4(
        new THREE.Matrix4().makeBasis(right, up, forward.clone().negate()),
      );
    }
    // Use the production acceptance mask before comparing a source direction.
    // A budget-limited or unstable ray has no displayed background direction.
    u.auditMode.value = 0;
    const adaptive_resolved = read()[3] > 0.5;
    u.auditMode.value = 6;
    const adaptive = read();
    const ray = selectedRay || reference;
    const cpu = window.AdAstraMetric.trace(this.metric, ray.origin, ray.view, {
      steps: 2560,
      stepScale: 0.25,
    });
    const adaptive_direction_error_rad = adaptive_resolved && cpu.resolved ? Math.hypot(
      ...adaptive.slice(0, 3).map((v, i) => v - cpu.state[i + 3]),
    ) : null;
    let refined_hamilton_source_error_rad = null;
    if (selectedRay?.source_direction) {
      u.stepScale.value = 0.25;
      u.budget.value = 1280;
      const refined = read();
      refined_hamilton_source_error_rad = Math.hypot(
        ...refined
          .slice(0, 3)
          .map((v, i) => v + selectedRay.source_direction[i]),
      );
      u.stepScale.value = 0.5;
      u.budget.value = 640;
    }
    u.auditMode.value = 0;
    this.renderer.setRenderTarget(null);
    target.dispose();
    this.dirty = true;
    return {
      gpu_source_direction:adaptive_resolved ? adaptive.slice(0,3).map(v=>-v) : null,
      adaptive_resolved,
      cpu_resolved:cpu.resolved,
      family:this.metric.family,
      parameter_hash:this.parameterHash,
      max_shift_abs_error: maxW,
      max_hessian_abs_error_per_m: maxK,
      position_error_m,
      direction_error_rad,
      adaptive_direction_error_rad,
      hamilton_source_error_rad: adaptive_resolved && selectedRay?.source_direction
        ? Math.hypot(
            ...adaptive
              .slice(0, 3)
              .map((v, i) => v + selectedRay.source_direction[i]),
          )
        : null,
      refined_hamilton_source_error_rad,
      reference:
        "Python DOP853 rtol=2e-11: 48 m fixed-step reference; optional 65,536 m raw-momentum Hamiltonian reference. Sampled audits, not global bounds.",
    };
  }
}
