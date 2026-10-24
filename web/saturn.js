// Extended reference source. Length unit here is Saturn's equatorial radius,
// not the metre scale of the diagnostic geometry. No ephemeris is implied.
export const SATURN = Object.freeze({
  equatorial_radius_km: 60268,
  polar_radius_km: 54364,
  distance_km: 1200000,
  direction: [0.588, 0.696, -0.41],
  rings_km: { C: [74658, 91975], B: [91975, 117507], A: [122340, 136780] },
  source: "https://nssdc.gsfc.nasa.gov/planetary/factsheet/satringfact.html",
});

// Analytic intersections with an oblate reference ellipsoid and thin annuli.
// Lambert shading/bands are illustrative; sizes and principal ring edges are
// measured. The same backward null-ray direction map remaps every planet pixel.
export const SATURN_GLSL = `
float bodyHit(vec3 o,vec3 d){
 vec3 scale=vec3(1.,1.,60268./54364.);vec3 a=d*scale,b=o*scale;
 float A=dot(a,a),B=dot(a,b),C=dot(b,b)-1.,disc=B*B-A*C;
 if(disc<0.)return 1e6;float t=(-B-sqrt(disc))/A;return t>0.?t:1e6;
}
float ringTau(float r){
 if(r>=74658./60268.&&r<91975./60268.)return .2;
 if(r>=91975./60268.&&r<117507./60268.)return 1.5;
 if(r>=122340./60268.&&r<136780./60268.)return .7;
 return 0.;
}
vec3 saturn(vec3 d,vec3 sky){
 vec3 centre=normalize(vec3(.588,.696,-.41));
 if(dot(d,centre)<.99)return sky;
 vec3 o=-centre*(1200000./60268.);
 vec3 sun=normalize(vec3(-.9,-.1,.4));
 float tb=bodyHit(o,d),tr=abs(d.z)>.00001?-o.z/d.z:1e6;
 vec3 color=sky;
 if(tb<1e5){
  vec3 p=o+tb*d,N=normalize(p*vec3(1.,1.,pow(60268./54364.,2.)));
  float latitude=asin(clamp(p.z/(54364./60268.),-1.,1.));
  float bands=1.+.045*sin(latitude*32.)+.018*sin(latitude*83.);
  float light=max(0.,dot(N,sun));
  // Ring shadow on the atmosphere, using the same thin-annulus geometry.
  float ts=-p.z/sun.z;
  if(ts>0.)light*=exp(-ringTau(length((p+sun*ts).xy))/abs(sun.z));
  color=vec3(.16,.133,.095)*bands*(.025+.975*light);
 }
 if(tr>0.&&tr<tb){
  vec3 p=o+tr*d;float tau=ringTau(length(p.xy));
  if(tau>0.){
   float opacity=1.-exp(-tau/max(.025,abs(d.z)));
   float light=bodyHit(p+sun*.0001,sun)<1e5?.04:.65;
   color=mix(color,vec3(.17,.155,.125)*light,opacity);
  }
 }
 return color;
}`;
