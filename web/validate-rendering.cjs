"use strict";
// Exercise actual optical scheduling with Three.js objects and a recording renderer.
const assert=require('node:assert/strict'),fs=require('node:fs/promises'),path=require('node:path'),os=require('node:os'),vm=require('node:vm'),{pathToFileURL}=require('node:url');
(async()=>{
 const dir=await fs.mkdtemp(path.join(os.tmpdir(),'ad-astra-rendering-'));
 let optics;
 try {
  for(const [src,dest] of [['vendor/three.module.min.js','three.mjs'],['vendor/three.core.min.js','three.core.mjs'],['saturn.js','saturn.mjs'],['optics.js','optics.mjs']]) {
   let s=await fs.readFile(path.join(__dirname,src),'utf8');
   s=s.replaceAll('./three.core.min.js','./three.core.mjs').replace('from "three"','from "./three.mjs"').replace('./saturn.js','./saturn.mjs');
   await fs.writeFile(path.join(dir,dest),s);
  }
  const THREE=await import(pathToFileURL(path.join(dir,'three.mjs')).href);
  const originalLoad=THREE.TextureLoader.prototype.load;
  THREE.TextureLoader.prototype.load=function(){return new THREE.Texture()};
  global.window={AdAstraMetric:require('./metric.js')};
  const {StellarOptics}=await import(pathToFileURL(path.join(dir,'optics.mjs')).href);
  const context={window:{}};
  for(const file of ['default-result.js','history.js'])vm.runInNewContext(await fs.readFile(path.join(__dirname,file),'utf8'),context);
  const entries=context.window.WARP_BUNDLED_HISTORY;
  let floatLinear=true,target=null;
  const draws=[],renderer={getContext:()=>({getExtension:name=>name==='EXT_color_buffer_float'||floatLinear}),setRenderTarget:t=>{target=t},render:scene=>{
   if(scene===optics.traceScene)draws.push({target,rect:target.viewport.clone(),offset:optics.traceMaterial.uniforms.mapOffset.value.toArray(),scale:optics.traceMaterial.uniforms.mapScale.value.toArray(),budget:optics.traceMaterial.uniforms.budget.value,hash:optics.parameterHash});
  }};
  optics=new StellarOptics(renderer,()=>{},null,{mobile:true});
  const camera=new THREE.PerspectiveCamera(40,2.2,.02,2000);camera.position.set(-168,-237,157);camera.lookAt(0,0,0);
  const coverage=(records,w,h)=>{
   const pixels=new Uint8Array(w*h);
   for(const {rect:r,offset,scale} of records){assert.ok(Math.abs(offset[0]+scale[0]/(2*r.z)-(r.x+.5)/w)<1e-12);assert.ok(Math.abs(offset[1]+scale[1]/(2*r.w)-(r.y+.5)/h)<1e-12);assert.ok(r.x>=0&&r.y>=0&&r.x+r.z<=w&&r.y+r.w<=h);for(let y=r.y;y<r.y+r.w;y++)for(let x=r.x;x<r.x+r.z;x++)pixels[y*w+x]++}
   assert.ok(pixels.every(n=>n===1),'Tiles cover each pixel exactly once, including odd dimensions.');
  };
  optics.setArtifact(entries[1].artifact);optics.render(camera);
  assert.equal(optics.target.height,72);
  assert.equal(draws.length,16);
  assert.ok(draws.every(d=>d.rect.z*d.rect.w<=1152&&d.budget===640));
  coverage(draws,optics.target.width,optics.target.height);
  assert.equal(optics.skyMaterial.uniforms.directionMap.value,optics.target.texture);
  draws.length=0;optics.changedAt=performance.now()-200;
  for(let i=0;i<64;i++)optics.render(camera);
  assert.equal(draws.length,64);assert.ok(optics.refined);
  assert.ok(draws.every(d=>d.budget===1280));coverage(draws,optics.fineTarget.width,optics.fineTarget.height);
  const completed=optics.fineTarget.texture;
  optics.setArtifact(entries[0].artifact);draws.length=0;optics.render(camera);
  assert.equal(optics.parameterHash,entries[0].artifact.candidate.parameter_hash);
  assert.ok(draws.every(d=>d.hash===optics.parameterHash));
  assert.notEqual(optics.skyMaterial.uniforms.directionMap.value,completed,'A history change cannot display the previous refined map.');
  optics.changedAt=performance.now()-200;optics.render(camera);assert.equal(optics.refineIndex,1);
  const hash=optics.parameterHash;
  optics.setEnabled(false);floatLinear=false;optics.restoreContext();
  assert.equal(optics.parameterHash,hash);assert.equal(optics.enabled,false);
  assert.equal(optics.refineIndex,0);assert.equal(optics.refined,false);assert.equal(optics.dirty,true);
  assert.equal(optics.traceMaterial.uniforms.compactLinear.value,false);
  assert.equal(optics.refineTimer,null);
  optics.setEnabled(true);draws.length=0;optics.render(camera);
  coverage(draws,optics.target.width,optics.target.height);
  assert.ok(draws.every(d=>d.budget===640));
  assert.deepEqual(optics.traceMaterial.uniforms.mapOffset.value.toArray(),[0,0]);
  assert.deepEqual(optics.traceMaterial.uniforms.mapScale.value.toArray(),[1,1]);
  camera.aspect=20;camera.updateProjectionMatrix();draws.length=0;optics.render(camera);
  assert.equal(optics.target.width,256);assert.ok(draws.every(d=>d.rect.z*d.rect.w<=1152));
  THREE.TextureLoader.prototype.load=originalLoad;
  console.log('PASS: mobile optical draw bounds, complete tile coverage, history-map invalidation, context-restoration capability refresh and unchanged ray integration budgets.');
 } finally {optics?.suspend();delete global.window;await fs.rm(dir,{recursive:true,force:true})}
})().catch(e=>{console.error(e);process.exitCode=1});
