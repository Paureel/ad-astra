/* SPDX-License-Identifier: Apache-2.0
 * Exact numerical tensor-spline evaluator for compact100; optical cache only
 * approximates its Cartesian fields. No score is computed in the browser. */
(() => {
  "use strict";
  const number = x => typeof x === "number" ? x : String(x).split("/").map(Number).reduce((a,b)=>a/b);
  function basis(knots, degree, x) {
    const n = knots.length-degree-2;
    let low=degree, high=n+1;
    if (x >= knots[n+1]) low=n;
    else while(high-low>1) { const m=(low+high)>>1; if(x<knots[m])high=m;else low=m; }
    const values=[1],left=[],right=[];
    for(let j=1;j<=degree;j++) {
      left[j]=x-knots[low+1-j];right[j]=knots[low+j]-x;
      let saved=0;
      for(let k=0;k<j;k++) {const v=values[k]/(right[k+1]+left[j-k]); values[k]=saved+right[k+1]*v;saved=left[j-k]*v;}
      values[j]=saved;
    }
    return {start:low-degree,values};
  }
  function createMetric(p, reference) {
    if(p.outer_radius_m!==100 || p.speed_c!==2 || p.R_m!==20 || p.sigma_per_m!==1)
      throw new Error("Unsupported compact100 display contract.");
    const rk=p.radial_knots_m.map(number), ak=p.angular_knots.map(number), c=p.tensor_coefficients.map(row=>row.map(number));
    if(rk.length!==53 || ak.length!==39 || c.length!==32 || c.some(row=>row.length!==46 || row.some(v=>!Number.isFinite(v))))
      throw new Error("Malformed compact100 spline controls.");
    const nets=[];
    for(let i=0;i<=2;i++) for(let j=0;j<=2-i;j++) {
      let a=c.map(row=>row.slice()),r=rk.slice(),u=ak.slice(),pr=6,pu=6;
      for(let d=0;d<i;d++) {a=a.map(row=>row.slice(1).map((v,k)=>pr*(v-row[k])/(r[k+pr+1]-r[k+1])));r=r.slice(1,-1);pr--;}
      for(let d=0;d<j;d++) {a=a.slice(1).map((row,k)=>row.map((v,l)=>pu*(v-a[k][l])/(u[k+pu+1]-u[k+1])));u=u.slice(1,-1);pu--;}
      nets.push({i,j,a,r,u,pr,pu});
    }
    function jets(r,mu) {
      const out={};
      for(const net of nets) {
        const rb=basis(net.r,net.pr,r),ab=basis(net.u,net.pu,mu);
        let value=0;
        for(let j=0;j<ab.values.length;j++) for(let i=0;i<rb.values.length;i++)
          value+=ab.values[j]*rb.values[i]*net.a[ab.start+j][rb.start+i];
        out[net.i+","+net.j]=value;
      }
      return out;
    }
    function assemble(q,c) {
      const r=Math.hypot(...q), n=q.map(v=>v/r), e=[1,0,0];
      return {W:n.map((v,i)=>c[0]*e[i]+c[1]*v), K:Array.from({length:9},(_,k)=>{
        const i=Math.floor(k/3),j=k%3;
        return c[2]*n[i]*n[j]+c[3]*(n[i]*e[j]+e[i]*n[j])+c[4]*e[i]*e[j]+c[5]*(i===j?1:0);
      })};
    }
    function core(q) {
      const r=Math.hypot(...q), f=reference.fields(q);
      if(r<=10) return f;
      const t=r-10,u=1-t,n=q.map(v=>v/r), eta=u**6*(u**5+11*t*u**4+55*t*t*u**3+165*t**3*u*u+330*t**4*u+462*t**5);
      const ep=-2772*t**5*u**5,epp=-13860*t**4*u**4*(1-2*t),phi=f.Phi;
      return {Phi:eta*phi,W:f.W.map((v,i)=>eta*v+phi*ep*n[i]),K:f.K.map((v,k)=>{
        const i=Math.floor(k/3),j=k%3;
        return eta*v+ep*(n[i]*f.W[j]+f.W[i]*n[j])+phi*(epp*n[i]*n[j]+ep/r*((i===j?1:0)-n[i]*n[j]));
      })};
    }
    function fields(q) {
      const r=Math.hypot(...q);
      if(r>=100)return {Phi:2*q[0],W:[2,0,0],K:Array(9).fill(0)};
      if(r<=11)return core(q);
      const mu=Math.max(-1,Math.min(1,q[0]/r)),v=jets(r,mu),h=v["0,0"],hr=v["1,0"],hu=v["0,1"];
      const fr=2*(h+r*hr),frr=2*(2*hr+r*v["2,0"]),a=2*v["1,1"],b=2*v["0,2"]/r,c=(fr-2*mu*hu)/r;
      return {Phi:2*r*h,...assemble(q,[2*hu,fr-2*mu*hu,frr-2*mu*a+mu*mu*b-c,a-mu*b,b,c])};
    }
    function cachedFields(q, cache) {
      const r=Math.hypot(...q);
      if(r<=11 || r>=100)return fields(q);
      const x=Math.cbrt((r-11)/89)*(cache.nr-1),y=Math.acos(Math.max(-1,Math.min(1,-q[0]/r)))/Math.PI*(cache.nm-1);
      const ix=Math.min(cache.nr-2,Math.floor(x)),iy=Math.min(cache.nm-2,Math.floor(y)),a=x-ix,b=y-iy;
      const out=Array(6).fill(0),stride=cache.nr*4;
      for(let k=0;k<6;k++) {
        const data=k<4?cache.a:cache.b,kk=k<4?k:k-4,offset=iy*stride+ix*4+kk;
        out[k]=(1-b)*((1-a)*data[offset]+a*data[offset+4])+b*((1-a)*data[offset+stride]+a*data[offset+stride+4]);
      }
      return assemble(q,out);
    }
    return {family:"compact100",beta:2,R:20,sigma:1,terms:[],stepCenter:18,stepWidth:7,stepFactor:.25,fields,cachedFields};
  }
  const API={createMetric};
  if(typeof module!=="undefined"&&module.exports)module.exports=API;
  if(typeof window!=="undefined")window.AdAstraCompact=API;
})();
