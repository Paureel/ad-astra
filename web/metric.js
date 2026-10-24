/* Numerical display implementation of the frozen scalar potential.
 * Reference: src/warpproof/geometry.py. Never used to score or certify energy. */
(() => {
  "use strict";
  const rational = (value) => {
    if (typeof value === "number") return value;
    const [a, b = 1] = String(value).split("/").map(Number);
    return a / b;
  };
  function createMetric(parameters) {
    const beta = Number(parameters.speed_c),
      R = Number(parameters.R_m),
      sigma = Number(parameters.sigma_per_m);
    const terms = parameters.coefficients.map((row) => [
      row.x_power,
      row.transverse_power,
      rational(row.coefficient),
    ]);
    if (
      ![beta, R, sigma].every(Number.isFinite) ||
      R <= 0 ||
      sigma <= 0 ||
      terms.length > 9 ||
      terms.some(
        ([i, j, a]) =>
          !Number.isInteger(i) ||
          !Number.isInteger(j) ||
          i < 0 ||
          j < 0 ||
          i + 2 * j > 4 ||
          !Number.isFinite(a),
      )
    )
      throw new Error("Invalid frozen-family display parameters.");
    const lp = (x) => Math.log1p(Math.exp(-2 * Math.abs(x)));
    const a = sigma * R,
      t = Math.tanh(a),
      sech2 = (4 * Math.exp(-2 * a)) / (1 + Math.exp(-2 * a)) ** 2;
    function fields(q) {
      const [x, y, z] = q,
        r = Math.hypot(x, y, z),
        safe = r || 1;
      const b = sigma * r,
        n = q.map((v) => v / safe);
      let f, g, df, gp, gpp;
      if (b < 1e-3) {
        const k2 = sigma ** 2 * sech2,
          k4 = sigma ** 4 * sech2 * (1 / 3 - sech2),
          k6 = sigma ** 6 * sech2 * (2 / 45 - (2 * sech2) / 3 + sech2 ** 2);
        f = k2 * r * r + k4 * r ** 4 + k6 * r ** 6;
        g = (k2 * r * r) / 3 + (k4 * r ** 4) / 5 + (k6 * r ** 6) / 7;
        df = 2 * k2 * r + 4 * k4 * r ** 3 + 6 * k6 * r ** 5;
        gp = (2 * k2 * r) / 3 + (4 * k4 * r ** 3) / 5 + (6 * k6 * r ** 5) / 7;
        gpp = (2 * k2) / 3 + (12 * k4 * r * r) / 5 + (30 * k6 * r ** 4) / 7;
      } else {
        const ta = Math.tanh(a + b),
          tb = Math.tanh(a - b);
        f = 1 - (ta + tb) / (2 * t);
        df = (sigma * (ta * ta - tb * tb)) / (2 * t);
        g =
          r <= R
            ? (-2 * Math.exp(-2 * a)) / (1 + Math.exp(-2 * a)) / t +
              (lp(a - b) - lp(a + b)) / (2 * sigma * r * t)
            : 1 - (R / t + (lp(a + b) - lp(b - a)) / (2 * sigma * t)) / r;
        gp = (f - g) / r;
        gpp = df / r - (2 * gp) / r;
      }
      const W = n.map((v, i) => beta * ((i === 0 ? g : 0) + x * gp * v));
      const K = Array.from({ length: 9 }, (_, k) => {
        const i = Math.floor(k / 3),
          j = k % 3;
        return (
          beta *
          (gp * ((i === 0 ? n[j] : 0) + (j === 0 ? n[i] : 0)) +
            x *
              (gpp * n[i] * n[j] +
                (gp / safe) * ((i === j ? 1 : 0) - n[i] * n[j])))
        );
      });
      if (r > 10 && r < 40 && terms.length) {
        const u = x / R,
          w = (y * y + z * z) / (R * R),
          s = (r * r - 100) / 1500,
          h = 4 * s * (1 - s);
        const B = h ** 6,
          Bs = 24 * h ** 5 * (1 - 2 * s),
          Bss = 480 * h ** 4 * (1 - 2 * s) ** 2 - 48 * h ** 5;
        let P = 0,
          Pu = 0,
          Pw = 0,
          Puu = 0,
          Puw = 0,
          Pww = 0;
        for (const [i, j, c] of terms) {
          P += c * u ** i * w ** j;
          if (i) Pu += c * i * u ** (i - 1) * w ** j;
          if (j) Pw += c * j * u ** i * w ** (j - 1);
          if (i > 1) Puu += c * i * (i - 1) * u ** (i - 2) * w ** j;
          if (i && j) Puw += c * i * j * u ** (i - 1) * w ** (j - 1);
          if (j > 1) Pww += c * j * (j - 1) * u ** i * w ** (j - 2);
        }
        const U = [1 / R, 0, 0],
          V = [0, (2 * y) / (R * R), (2 * z) / (R * R)],
          S = q.map((v) => (2 * v) / 1500);
        const dP = U.map((v, i) => Pu * v + Pw * V[i]);
        for (let i = 0; i < 3; i++) {
          W[i] += beta * R * (B * dP[i] + P * Bs * S[i]);
          for (let j = 0; j < 3; j++) {
            const ddP =
              Puu * U[i] * U[j] +
              Puw * (U[i] * V[j] + V[i] * U[j]) +
              Pww * V[i] * V[j] +
              (i === j && i > 0 ? (Pw * 2) / (R * R) : 0);
            K[i * 3 + j] +=
              beta *
              R *
              (B * ddP +
                Bs * (S[i] * dP[j] + dP[i] * S[j]) +
                P * (Bss * S[i] * S[j] + (i === j ? (Bs * 2) / 1500 : 0)));
          }
        }
      }
      return { W, K };
    }
    return { beta, R, sigma, terms, fields };
  }
  function rhs(metric, state) {
    const q = state.slice(0, 3),
      n = state.slice(3, 6),
      { W, K } = metric.fields(q);
    const Kn = [0, 1, 2].map(
      (i) => K[i * 3] * n[0] + K[i * 3 + 1] * n[1] + K[i * 3 + 2] * n[2],
    );
    const rate = n.reduce((s, v, i) => s + v * Kn[i], 0);
    return [
      ...W.map((v, i) => v - n[i]),
      ...Kn.map((v, i) => -v + n[i] * rate),
      -rate,
    ];
  }
  function step(metric, state, h) {
    const add = (v, k, f) => v.map((x, i) => x + f * k[i]);
    const k1 = rhs(metric, state),
      k2 = rhs(metric, add(state, k1, h / 2)),
      k3 = rhs(metric, add(state, k2, h / 2)),
      k4 = rhs(metric, add(state, k3, h));
    const out = state.map(
      (x, i) => x + (h * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i])) / 6,
    );
    const norm = Math.hypot(...out.slice(3, 6));
    for (let i = 3; i < 6; i++) out[i] /= norm;
    return out;
  }
  function trace(
    metric,
    origin,
    view,
    { steps = 320, stepScale = 1, boundary = 65536 } = {},
  ) {
    let state = [...origin, ...view.map((v) => -v), 0];
    let ct = 0;
    for (let i = 0; i < steps; i++) {
      const r = Math.hypot(...state.slice(0, 3));
      if (r >= boundary) return { state, ct, resolved: true, steps: i };
      const h =
        stepScale *
        Math.min(8192, Math.max(0.12, (Math.abs(r - metric.R) - 4) * 0.15));
      state = step(metric, state, h);
      ct += h;
    }
    return { state, ct, resolved: false, steps };
  }
  const GLSL = `
uniform float beta; uniform float profileR; uniform float sigma;
uniform int termCount; uniform vec3 terms[9];
struct Metric { vec3 W; mat3 K; };
mat3 dyad(vec3 a,vec3 b){return mat3(a*b.x,a*b.y,a*b.z);}
float lp(float x){return log(1.0+exp(-2.0*abs(x)));}
float power(float x,int n){if(n<=0)return 1.0;if(n==1)return x;if(n==2)return x*x;if(n==3)return x*x*x;return x*x*x*x;}
Metric metricFields(vec3 q){
 float r=length(q), rr=max(r,1e-10),a=sigma*profileR,b=sigma*r,t=tanh(a);
 vec3 n=q/rr;float f,g,df,gp,gpp;
 if(b<0.001){float sech2=4.0*exp(-2.0*a)/pow(1.0+exp(-2.0*a),2.0);float k2=sigma*sigma*sech2;
  f=k2*r*r;g=f/3.0;gp=2.0*k2*r/3.0;gpp=2.0*k2/3.0;
 }else{
  float ta=tanh(a+b),tb=tanh(a-b);f=1.0-(ta+tb)/(2.0*t);df=sigma*(ta*ta-tb*tb)/(2.0*t);
  if(r<=profileR)g=-2.0*exp(-2.0*a)/(1.0+exp(-2.0*a))/t+(lp(a-b)-lp(a+b))/(2.0*sigma*r*t);
  else g=1.0-(profileR/t+(lp(a+b)-lp(b-a))/(2.0*sigma*t))/r;
  gp=(f-g)/r;gpp=df/r-2.0*gp/r;
 }
 vec3 e=vec3(1,0,0);Metric M;
 M.W=beta*(g*e+q.x*gp*n);
 M.K=beta*(gp*(dyad(e,n)+dyad(n,e))+q.x*(gpp*dyad(n,n)+gp/rr*(mat3(1.0)-dyad(n,n))));
 if(r>10.0&&r<40.0&&termCount>0){
  float u=q.x/profileR,w=dot(q.yz,q.yz)/(profileR*profileR),s=(r*r-100.0)/1500.0,h=4.0*s*(1.0-s);
  float B=pow(h,6.0),Bs=24.0*pow(h,5.0)*(1.0-2.0*s),Bss=480.0*pow(h,4.0)*pow(1.0-2.0*s,2.0)-48.0*pow(h,5.0);
  float P=0.0,Pu=0.0,Pw=0.0,Puu=0.0,Puw=0.0,Pww=0.0;
  for(int k=0;k<9;k++){if(k>=termCount)break;int i=int(terms[k].x),j=int(terms[k].y);float c=terms[k].z;
   P+=c*power(u,i)*power(w,j);
   if(i>0)Pu+=c*float(i)*power(u,i-1)*power(w,j);
   if(j>0)Pw+=c*float(j)*power(u,i)*power(w,j-1);
   if(i>1)Puu+=c*float(i*(i-1))*power(u,i-2)*power(w,j);
   if(i>0&&j>0)Puw+=c*float(i*j)*power(u,i-1)*power(w,j-1);
   if(j>1)Pww+=c*float(j*(j-1))*power(u,i)*power(w,j-2);
  }
  vec3 U=vec3(1.0/profileR,0,0),V=vec3(0,q.y,q.z)*2.0/(profileR*profileR),S=2.0*q/1500.0;
  vec3 dP=Pu*U+Pw*V;
  mat3 ddP=Puu*dyad(U,U)+Puw*(dyad(U,V)+dyad(V,U))+Pww*dyad(V,V)+Pw*mat3(0,0,0,0,2.0/(profileR*profileR),0,0,0,2.0/(profileR*profileR));
  M.W+=beta*profileR*(B*dP+P*Bs*S);
  M.K+=beta*profileR*(B*ddP+Bs*(dyad(S,dP)+dyad(dP,S))+P*(Bss*dyad(S,S)+Bs*2.0/1500.0*mat3(1.0)));
 }
 return M;
}
void opticalRHS(vec3 q,vec3 n,out vec3 dq,out vec3 dn,out float dl){Metric M=metricFields(q);vec3 Kn=M.K*n;float a=dot(n,Kn);dq=M.W-n;dn=-Kn+n*a;dl=-a;}
void opticalStep(inout vec3 q,inout vec3 n,inout float ell,float h){
 vec3 a,b,c,d,e,f,g,k;float l1,l2,l3,l4;
 opticalRHS(q,n,a,b,l1);opticalRHS(q+a*h*.5,n+b*h*.5,c,d,l2);
 opticalRHS(q+c*h*.5,n+d*h*.5,e,f,l3);opticalRHS(q+e*h,n+f*h,g,k,l4);
 q+=h*(a+2.0*c+2.0*e+g)/6.0;n=normalize(n+h*(b+2.0*d+2.0*f+k)/6.0);ell+=h*(l1+2.0*l2+2.0*l3+l4)/6.0;
}
`;
  const API = { createMetric, rhs, step, trace, GLSL };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  if (typeof window !== "undefined") window.AdAstraMetric = API;
})();
