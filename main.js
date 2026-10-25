import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

const { gsap, ScrollTrigger, Lenis } = window;
gsap.registerPlugin(ScrollTrigger);

const mqMobile = matchMedia('(max-width: 820px)');
const isMobile = () => mqMobile.matches;
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

const FORMULAS = [
  { name: 'LEAN', color: '#73EDFF' },
  { name: 'BUILD', color: '#FF9B46' },
  { name: 'LIFT', color: '#7DFF9B' },
  { name: 'RECOVER', color: '#FF6FB5' },
  { name: 'VEGAN', color: '#4ADE80' },
];

/* =========================================================
   Shared animated state — GSAP tweens it, the render loop reads it
   ========================================================= */
const S = {
  w0: 1, wM: 0, wO: 0, w6: 0, wG: 0, w100: 0,
  chaos: 3, orbMix: 0, tintMix: 0, opacity: 0,
  cupX: 2.2, cupY: -4, cupScale: 0, cupSpin: 0,
  pX: 2.2, pY: 0, pScale: 1,
  vel: 0,
};

/* =========================================================
   Smooth scroll
   ========================================================= */
const lenis = new Lenis({ lerp: reduced ? 1 : 0.085, smoothWheel: !reduced });
lenis.on('scroll', ScrollTrigger.update);
gsap.ticker.add((t) => lenis.raf(t * 1000));
gsap.ticker.lagSmoothing(0);
lenis.stop();

/* =========================================================
   THREE
   ========================================================= */
const canvas = $('#webgl');
let three = null;
try { three = initThree(); } catch (e) { console.warn('WebGL unavailable', e); canvas.style.display = 'none'; }

function initThree() {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
  const dpr = () => Math.min(devicePixelRatio, isMobile() ? 1.5 : 1.75);
  renderer.setPixelRatio(dpr());
  renderer.setSize(innerWidth, innerHeight);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.95;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(35, innerWidth / innerHeight, 0.1, 100);
  camera.position.set(0, 0, 10);

  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(renderer), 0.04).texture;

  /* ---------- background gradient quad ---------- */
  const bgMat = new THREE.ShaderMaterial({
    depthWrite: false, depthTest: false,
    uniforms: {
      uTime: { value: 0 }, uAspect: { value: innerWidth / innerHeight },
      uBase: { value: new THREE.Color('#050816') },
      uA: { value: new THREE.Color('#73EDFF') }, uB: { value: new THREE.Color('#1BA2FF') },
      uGlow: { value: new THREE.Vector2(0.4, 0) }, uGlowAmt: { value: 1 },
    },
    vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, .9999, 1.); }`,
    fragmentShader: `
      varying vec2 vUv; uniform float uTime, uAspect, uGlowAmt; uniform vec3 uBase, uA, uB; uniform vec2 uGlow;
      void main(){
        vec2 p = vUv * 2. - 1.; p.x *= uAspect;
        vec2 g = uGlow; g.x *= uAspect;
        float d1 = length(p - g);
        float d2 = length(p - vec2(-1.1 * uAspect + sin(uTime*.1)*.3, -.9 + cos(uTime*.13)*.2));
        vec3 c = uBase;
        c += uA * .10 * exp(-d1 * d1 * 1.6) * uGlowAmt;
        c += uB * .05 * exp(-d2 * d2 * 1.2);
        gl_FragColor = vec4(c, 1.);
      }`,
  });
  const bg = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), bgMat);
  bg.frustumCulled = false; bg.renderOrder = -10;
  scene.add(bg);

  /* ---------- lights ---------- */
  const key = new THREE.DirectionalLight(0xffffff, 1.6); key.position.set(3, 5, 6); scene.add(key);
  const rimA = new THREE.PointLight(0x73edff, 30, 12); rimA.position.set(-3, 1.5, -2); scene.add(rimA);
  const rimB = new THREE.PointLight(0x1ba2ff, 20, 12); rimB.position.set(3, -2, -1.5); scene.add(rimB);
  scene.add(new THREE.AmbientLight(0x223366, 0.6));

  /* ---------- the cup ---------- */
  const cup = new THREE.Group();
  const tilt = new THREE.Group();
  tilt.add(cup);
  scene.add(tilt);

  const rAt = (y) => 0.6 + ((y + 1.2) / 2.4) * 0.26; // cup wall radius at height y
  const cupProfile = [new THREE.Vector2(0.001, -1.2)];
  for (let i = 0; i <= 20; i++) { const y = -1.2 + (i / 20) * 2.4; cupProfile.push(new THREE.Vector2(rAt(y), y)); }
  cupProfile.push(new THREE.Vector2(0.9, 1.22), new THREE.Vector2(0.9, 1.26), new THREE.Vector2(0.85, 1.26));
  const cupMat = new THREE.MeshPhysicalMaterial({
    color: 0xffffff, roughness: 0.06, metalness: 0, transmission: 1, thickness: 0.35, ior: 1.42,
    clearcoat: 1, clearcoatRoughness: 0.04, envMapIntensity: 1.4, side: THREE.DoubleSide,
  });
  cup.add(new THREE.Mesh(new THREE.LatheGeometry(cupProfile, 96), cupMat));

  // liquid + foam
  const fillY = 0.78;
  const liqProfile = [new THREE.Vector2(0.001, -1.14)];
  for (let i = 0; i <= 16; i++) { const y = -1.14 + (i / 16) * (fillY + 1.14); liqProfile.push(new THREE.Vector2(rAt(y) - 0.045, y)); }
  liqProfile.push(new THREE.Vector2(0.001, fillY + 0.02));
  const liqMat = new THREE.MeshPhysicalMaterial({ color: new THREE.Color(FORMULAS[0].color), roughness: 0.35, sheen: 1, sheenColor: new THREE.Color(0xffffff), sheenRoughness: 0.4, emissive: new THREE.Color(FORMULAS[0].color), emissiveIntensity: 0.12 });
  cup.add(new THREE.Mesh(new THREE.LatheGeometry(liqProfile, 64), liqMat));
  const foamProfile = [];
  for (let i = 0; i <= 6; i++) { const y = fillY - 0.16 + (i / 6) * 0.16; foamProfile.push(new THREE.Vector2(rAt(y) - 0.04, y)); }
  foamProfile.push(new THREE.Vector2(0.4, fillY + 0.05), new THREE.Vector2(0.001, fillY + 0.06));
  const foamMat = new THREE.MeshStandardMaterial({ color: 0xf7f2ea, roughness: 0.85 });
  cup.add(new THREE.Mesh(new THREE.LatheGeometry(foamProfile, 64), foamMat));

  // branded sleeve (canvas texture, redrawn per formula)
  const sc = document.createElement('canvas'); sc.width = 2048; sc.height = 440;
  const sctx = sc.getContext('2d');
  const sleeveTex = new THREE.CanvasTexture(sc);
  sleeveTex.colorSpace = THREE.SRGBColorSpace;
  sleeveTex.anisotropy = renderer.capabilities.getMaxAnisotropy();
  function drawSleeve(f) {
    const W = sc.width, H = sc.height;
    sctx.fillStyle = '#0B1230'; sctx.fillRect(0, 0, W, H);
    sctx.fillStyle = f.color; sctx.fillRect(0, 14, W, 8); sctx.fillRect(0, H - 22, W, 8);
    for (let k = 0; k < 2; k++) {
      const ox = k * (W / 2);
      // bolt
      sctx.save(); sctx.translate(ox + 120, 95); sctx.scale(1.25, 1.25);
      sctx.fillStyle = f.color;
      sctx.beginPath(); sctx.moveTo(70, 0); sctx.lineTo(10, 120); sctx.lineTo(55, 120); sctx.lineTo(30, 210); sctx.lineTo(110, 80); sctx.lineTo(62, 80); sctx.lineTo(95, 0); sctx.closePath(); sctx.fill();
      sctx.restore();
      sctx.fillStyle = '#F4F8FF';
      sctx.font = '900 150px "Barlow Condensed"'; sctx.textBaseline = 'alphabetic';
      sctx.fillText('SHAKE-O-MAT', ox + 290, 238);
      sctx.fillStyle = f.color; sctx.font = '900 92px "Barlow Condensed"';
      sctx.fillText(f.name, ox + 292, 340);
      sctx.fillStyle = '#8AA0C8'; sctx.font = '700 34px "Barlow Condensed"';
      sctx.fillText('R E C O V E R .   I N S T A N T L Y .', ox + 292 + sctx.measureText(f.name).width * 0 + 0, 392);
    }
    sleeveTex.needsUpdate = true;
  }
  const sy0 = -0.55, sy1 = 0.5;
  const sleeve = new THREE.Mesh(
    new THREE.CylinderGeometry(rAt(sy1) + 0.018, rAt(sy0) + 0.018, sy1 - sy0, 96, 1, true),
    new THREE.MeshPhysicalMaterial({ map: sleeveTex, roughness: 0.5, clearcoat: 0.4, clearcoatRoughness: 0.4 })
  );
  sleeve.position.y = (sy0 + sy1) / 2;
  cup.add(sleeve);

  // dome lid
  const lidProfile = [new THREE.Vector2(0.93, 1.2), new THREE.Vector2(0.95, 1.27), new THREE.Vector2(0.92, 1.34), new THREE.Vector2(0.86, 1.36)];
  for (let i = 1; i <= 14; i++) { const a = (i / 14) * (Math.PI / 2); lidProfile.push(new THREE.Vector2(0.86 * Math.cos(a), 1.36 + 0.5 * Math.sin(a))); }
  const lidMat = new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.12, transmission: 0.92, thickness: 0.15, clearcoat: 1, side: THREE.DoubleSide });
  cup.add(new THREE.Mesh(new THREE.LatheGeometry(lidProfile, 96), lidMat));

  // straw
  const strawCurve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(0.15, -0.9, 0.05), new THREE.Vector3(0.18, 1.3, 0.05), new THREE.Vector3(0.22, 2.25, 0.05), new THREE.Vector3(0.36, 2.52, 0.05), new THREE.Vector3(0.68, 2.62, 0.05),
  ]);
  const strawMat = new THREE.MeshStandardMaterial({ color: new THREE.Color(FORMULAS[0].color), emissive: new THREE.Color(FORMULAS[0].color), emissiveIntensity: 0.9, roughness: 0.3 });
  cup.add(new THREE.Mesh(new THREE.TubeGeometry(strawCurve, 80, 0.055, 16, false), strawMat));
  cup.position.y = -0.55;

  // floor glow
  const glowMat = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    uniforms: { uColor: { value: new THREE.Color(FORMULAS[0].color) } },
    vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.); }`,
    fragmentShader: `varying vec2 vUv; uniform vec3 uColor; void main(){ float d = length(vUv-.5)*2.; float a = smoothstep(1.,0.,d); gl_FragColor = vec4(uColor * a * a * .45, 1.); }`,
  });
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(3.4, 3.4), glowMat);
  floor.rotation.x = -Math.PI / 2; floor.position.y = -1.85;
  tilt.add(floor);

  /* ---------- particles ---------- */
  const N = isMobile() ? 6000 : 13000;
  const shapes = buildShapes(N);
  const pg = new THREE.BufferGeometry();
  pg.setAttribute('position', new THREE.BufferAttribute(shapes.vortex, 3));
  pg.setAttribute('aMachine', new THREE.BufferAttribute(shapes.machine, 3));
  pg.setAttribute('aOrbs', new THREE.BufferAttribute(shapes.orbs, 3));
  pg.setAttribute('aSixty', new THREE.BufferAttribute(shapes.sixty, 3));
  pg.setAttribute('aGalaxy', new THREE.BufferAttribute(shapes.galaxy, 3));
  pg.setAttribute('aHundred', new THREE.BufferAttribute(shapes.hundred, 3));
  pg.setAttribute('aRand', new THREE.BufferAttribute(shapes.rand, 1));
  pg.setAttribute('aColor', new THREE.BufferAttribute(shapes.color, 3));
  pg.setAttribute('aOrbColor', new THREE.BufferAttribute(shapes.orbColor, 3));

  const pMat = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    uniforms: {
      uTime: { value: 0 }, uW0: { value: 1 }, uW: { value: new THREE.Vector4() }, uW5: { value: 0 },
      uChaos: { value: 0 }, uSize: { value: isMobile() ? 8.5 : 9 }, uPR: { value: renderer.getPixelRatio() },
      uOpacity: { value: 1 }, uTint: { value: new THREE.Color(FORMULAS[0].color) }, uTintMix: { value: 0 }, uOrbMix: { value: 0 },
      uMouse: { value: new THREE.Vector3(99, 99, 0) }, uVel: { value: 0 },
    },
    vertexShader: `
      uniform float uTime, uW0, uW5, uChaos, uSize, uPR, uOpacity, uTintMix, uOrbMix, uVel;
      uniform vec4 uW; uniform vec3 uTint, uMouse;
      attribute vec3 aMachine, aOrbs, aSixty, aGalaxy, aHundred, aColor, aOrbColor;
      attribute float aRand;
      varying vec3 vColor; varying float vAlpha;
      mat2 rot(float a){ float c = cos(a), s = sin(a); return mat2(c, -s, s, c); }
      void main(){
        float ph = aRand * 6.2831;
        vec3 pV = position;
        float r = length(pV.xz);
        pV.xz = rot(uTime * .45 / (.35 + r * .45)) * pV.xz;
        pV.y += sin(uTime * .7 + ph) * .08 + uVel * .002 * (aRand - .5) * 40.;
        vec3 pG = aGalaxy; pG.xz = rot(uTime * .07) * pG.xz; pG.yz = rot(-1.08) * pG.yz;
        vec3 jit = .02 * vec3(sin(uTime * 2. + ph * 7.), cos(uTime * 1.7 + ph * 5.), sin(uTime * 1.3 + ph * 3.));
        vec3 pO = aOrbs; pO.xy = rot(uTime * .12) * pO.xy;
        vec3 p = pV * uW0 + (aMachine + jit) * uW.x + (pO + jit) * uW.y + (aSixty + jit) * uW.z + pG * uW.w + (aHundred + jit) * uW5;
        p += uChaos * vec3(sin(ph * 3.1 + uTime), cos(ph * 2.3 + uTime * 1.3), sin(ph * 1.7 + uTime * .7)) * (1.2 + aRand * 2.4);
        vec3 dm = p - uMouse; float dl = length(dm.xy);
        p.xy += normalize(dm.xy + 1e-4) * smoothstep(1.1, 0., dl) * .45;
        vec4 mv = modelViewMatrix * vec4(p, 1.);
        gl_Position = projectionMatrix * mv;
        gl_PointSize = uSize * (.35 + aRand * 1.1) * uPR * (10. / -mv.z);
        vec3 c = mix(aColor, aOrbColor, uOrbMix);
        c = mix(c, uTint, uTintMix * (.35 + .65 * aRand));
        vColor = c;
        vAlpha = uOpacity * (.6 + .4 * fract(aRand * 13.7));
      }`,
    fragmentShader: `
      varying vec3 vColor; varying float vAlpha;
      void main(){
        float d = length(gl_PointCoord - .5);
        float a = smoothstep(.5, 0., d); a *= a;
        gl_FragColor = vec4(vColor * (.55 + a * .9), a * vAlpha * 1.0);
      }`,
  });
  const points = new THREE.Points(pg, pMat);
  points.frustumCulled = false;
  const pGroup = new THREE.Group();
  pGroup.add(points);
  scene.add(pGroup);

  /* ---------- post ---------- */
  const composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, camera));
  const bloom = new UnrealBloomPass(new THREE.Vector2(innerWidth, innerHeight), 0.9, 0.5, 0.6);
  composer.addPass(bloom);
  composer.addPass(new OutputPass());

  return { renderer, scene, camera, composer, bloom, bgMat, cup, tilt, liqMat, strawMat, glowMat, pMat, pGroup, drawSleeve, dpr };
}

/* ---------- particle target shapes ---------- */
function sampleText(text, N, height, weight = 900) {
  const c = document.createElement('canvas'); c.width = 900; c.height = 320;
  const x = c.getContext('2d');
  x.fillStyle = '#fff'; x.textAlign = 'center'; x.textBaseline = 'middle';
  x.font = `${weight} 300px "Barlow Condensed"`;
  x.fillText(text, 450, 170);
  const d = x.getImageData(0, 0, 900, 320).data;
  const pts = [];
  for (let py = 0; py < 320; py += 2) for (let px = 0; px < 900; px += 2) if (d[(py * 900 + px) * 4 + 3] > 128) pts.push(px, py);
  const out = new Float32Array(N * 3);
  const s = height / 300;
  const cnt = pts.length / 2;
  for (let i = 0; i < N; i++) {
    const k = cnt ? (Math.random() * cnt) | 0 : 0;
    out[i * 3] = ((pts[k * 2] ?? 450) - 450) * s + (Math.random() - 0.5) * s * 2;
    out[i * 3 + 1] = -((pts[k * 2 + 1] ?? 160) - 160) * s;
    out[i * 3 + 2] = (Math.random() - 0.5) * 0.35;
  }
  return out;
}

function buildShapes(N) {
  const R = Math.random;
  const vortex = new Float32Array(N * 3), machine = new Float32Array(N * 3), orbs = new Float32Array(N * 3), galaxy = new Float32Array(N * 3);
  const rand = new Float32Array(N), color = new Float32Array(N * 3), orbColor = new Float32Array(N * 3);
  const pal = ['#73EDFF', '#1BA2FF', '#F4F8FF', '#1BA2FF', '#73EDFF'].map((h) => new THREE.Color(h));
  const fcol = FORMULAS.map((f) => new THREE.Color(f.color));
  const gauss = () => (R() + R() + R() - 1.5) / 1.5;

  // machine wireframe
  const hx = 0.85, hy = 1.7, hz = 0.45, oy = -0.25;
  const C = [[-hx, -hy, -hz], [hx, -hy, -hz], [hx, hy, -hz], [-hx, hy, -hz], [-hx, -hy, hz], [hx, -hy, hz], [hx, hy, hz], [-hx, hy, hz]];
  const E = [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 4], [0, 4], [1, 5], [2, 6], [3, 7]];
  const rectEdge = (x0, x1, y0, y1) => {
    const per = 2 * (x1 - x0 + y1 - y0); let t = R() * per;
    if (t < x1 - x0) return [x0 + t, y0]; t -= x1 - x0;
    if (t < y1 - y0) return [x1, y0 + t]; t -= y1 - y0;
    if (t < x1 - x0) return [x1 - t, y1]; t -= x1 - x0;
    return [x0, y1 - t];
  };

  for (let i = 0; i < N; i++) {
    const i3 = i * 3;
    rand[i] = R();
    // vortex
    const vr = 1.25 + Math.pow(R(), 1.6) * 3.8, va = R() * Math.PI * 2;
    vortex[i3] = Math.cos(va) * vr; vortex[i3 + 1] = (R() - 0.5) * 7 * (0.5 + vr / 8); vortex[i3 + 2] = Math.sin(va) * vr;
    // machine
    const m = R();
    let p;
    if (m < 0.42) { const e = E[(R() * 12) | 0], a = C[e[0]], b = C[e[1]], t = R(); p = [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]; }
    else if (m < 0.72) { p = [(R() - 0.5) * 1.3, -0.15 + R() * 1.55, hz]; }
    else if (m < 0.86) { const q = R() < 0.6 ? rectEdge(-0.72, 0.72, hy + 0.2, hy + 0.55) : [(R() - 0.5) * 1.3, hy + 0.27 + R() * 0.2]; p = [q[0], q[1], hz * 0.6]; }
    else { const q = rectEdge(-0.65, 0.65, -1.5, -0.45); p = [q[0], q[1], hz]; }
    machine[i3] = p[0]; machine[i3 + 1] = p[1] + oy; machine[i3 + 2] = p[2];
    // orbs in a pentagon
    const k = i % 5, ang = (k / 5) * Math.PI * 2;
    const th = R() * Math.PI * 2, ph = Math.acos(2 * R() - 1), rr = 0.5 * Math.cbrt(0.35 + 0.65 * R());
    orbs[i3] = Math.sin(ang) * 1.45 + rr * Math.sin(ph) * Math.cos(th);
    orbs[i3 + 1] = Math.cos(ang) * 1.45 + rr * Math.cos(ph);
    orbs[i3 + 2] = rr * Math.sin(ph) * Math.sin(th);
    orbColor[i3] = fcol[k].r; orbColor[i3 + 1] = fcol[k].g; orbColor[i3 + 2] = fcol[k].b;
    // galaxy
    const gr = 0.9 + Math.pow(R(), 0.85) * 6, arm = i % 3, ga = (arm / 3) * Math.PI * 2 + gr * 0.75 + gauss() * 0.35;
    galaxy[i3] = Math.cos(ga) * gr + gauss() * 0.15; galaxy[i3 + 1] = gauss() * 0.18 * (1.2 - gr / 7); galaxy[i3 + 2] = Math.sin(ga) * gr + gauss() * 0.15;
    // base color
    const c = pal[(R() * pal.length) | 0];
    color[i3] = c.r; color[i3 + 1] = c.g; color[i3 + 2] = c.b;
  }
  return { vortex, machine, orbs, galaxy, sixty: sampleText('60', N, 3.4), hundred: sampleText('100', N, 2.6), rand, color, orbColor };
}

/* =========================================================
   Scene states
   ========================================================= */
const STATES = {
  hero: () => { const m = isMobile(); return { w: [1, 0, 0, 0, 0, 0], cupX: m ? 0 : 2.3, cupY: m ? 1.3 : 0, cupScale: m ? 0.55 : 1, pX: m ? 0 : 2.3, pY: m ? 1.2 : 0, pScale: m ? 0.62 : 1, orbMix: 0, tintMix: 0, opacity: 1 }; },
  steps0: () => { const m = isMobile(); return { w: [0, 1, 0, 0, 0, 0], cupScale: 0, cupY: -3.5, pX: m ? 0 : 2.4, pY: m ? 0.5 : -0.1, pScale: m ? 0.42 : 0.95, orbMix: 0, tintMix: 0, opacity: 1 }; },
  steps1: () => { const m = isMobile(); return { w: [0, 0, 1, 0, 0, 0], cupScale: 0, cupY: -3.5, pX: m ? 0 : 2.4, pY: m ? 0.55 : 0, pScale: m ? 0.42 : 1, orbMix: 1, tintMix: 0, opacity: 1 }; },
  steps2: () => { const m = isMobile(); return { w: [0, 0, 0, 1, 0, 0], cupScale: 0, cupY: -3.5, pX: m ? 0 : 2.5, pY: m ? 0.6 : 0, pScale: m ? 0.42 : 0.95, orbMix: 0, tintMix: 0.3, opacity: 1 }; },
  formulas: () => { const m = isMobile(); return { w: [0, 0, 0, 0, 1, 0], cupX: m ? 0 : 2.4, cupY: m ? 1.05 : -0.1, cupScale: m ? 0.5 : 0.95, pX: m ? 0 : 2.4, pY: m ? 0.7 : -0.6, pScale: m ? 0.45 : 0.75, orbMix: 0, tintMix: 0.85, opacity: 0.95 }; },
  why: () => ({ w: [0, 0, 0, 0, 1, 0], cupScale: 0, cupY: 4, pX: 0, pY: -1.2, pScale: 1.4, orbMix: 0, tintMix: 0.3, opacity: 0.45 }),
  machine: () => ({ w: [1, 0, 0, 0, 0, 0], cupScale: 0, cupY: 4, pX: isMobile() ? 0 : -2.8, pY: 0, pScale: 1.1, orbMix: 0, tintMix: 0.2, opacity: 0.55 }),
  honest: () => ({ w: [0, 0, 0, 0, 1, 0], cupScale: 0, cupY: 4, pX: 0, pY: 0.4, pScale: 1.6, orbMix: 0, tintMix: 0, opacity: 0.28 }),
  cups: () => ({ w: [0, 0, 0, 0, 1, 0], cupScale: 0, cupY: 4, pX: 0, pY: -0.6, pScale: 1.9, orbMix: 0, tintMix: 0.6, opacity: 0.3 }),
  waitlist: () => { const m = isMobile(); return { w: [0, 0, 0, 0, 0, 1], cupScale: 0, cupY: 4, pX: m ? 0 : 3.4, pY: m ? 2 : 0.6, pScale: m ? 0.5 : 0.75, orbMix: 0, tintMix: 0.5, opacity: m ? 0.35 : 0.9 }; },
  faq: () => ({ w: [0, 0, 0, 0, 1, 0], cupScale: 0, cupY: 4, pX: 0, pY: 0, pScale: 1.7, orbMix: 0, tintMix: 0.2, opacity: 0.25 }),
  contact: () => ({ w: [1, 0, 0, 0, 0, 0], cupScale: 0, cupY: 4, pX: 0, pY: 0, pScale: 1.5, orbMix: 0, tintMix: 0.2, opacity: 0.25 }),
  pump: () => { const m = isMobile(); return { w: [0, 0, 1, 0, 0, 0], cupScale: 0, cupY: 4, pX: m ? 0 : 3.6, pY: m ? 2.2 : 0.3, pScale: m ? 0.4 : 0.7, orbMix: 1, tintMix: 0, opacity: m ? 0.35 : 0.7 }; },
  footer: () => ({ w: [1, 0, 0, 0, 0, 0], cupScale: 0, cupY: 4, pX: 0, pY: 0.6, pScale: 1.2, orbMix: 0, tintMix: 0.5, opacity: 1 }),
};
let currentState = null;
function setState(key, instant = false) {
  if (key === currentState || !STATES[key]) return;
  currentState = key;
  const t = STATES[key]();
  const [w0, wM, wO, w6, wG, w100] = t.w;
  const vars = { w0, wM, wO, w6, wG, w100, orbMix: t.orbMix, tintMix: t.tintMix, opacity: t.opacity, pX: t.pX, pY: t.pY, pScale: t.pScale, cupScale: t.cupScale, cupY: t.cupY };
  if (t.cupX !== undefined) vars.cupX = t.cupX;
  if (instant) { Object.assign(S, vars); return; }
  gsap.to(S, { ...vars, duration: 1.7, ease: 'power3.inOut', overwrite: 'auto' });
  if (!reduced) {
    gsap.killTweensOf(S, 'chaos');
    gsap.timeline().to(S, { chaos: 0.55, duration: 0.6, ease: 'sine.out' }).to(S, { chaos: 0, duration: 1.1, ease: 'sine.inOut' });
  }
}

/* =========================================================
   Render loop
   ========================================================= */
const pointer = { x: 0, y: 0, sx: 0, sy: 0 };
addEventListener('pointermove', (e) => { pointer.x = (e.clientX / innerWidth) * 2 - 1; pointer.y = -(e.clientY / innerHeight) * 2 + 1; }, { passive: true });

if (three) {
  const { renderer, camera, composer, bgMat, cup, tilt, pMat, pGroup } = three;
  const clock = new THREE.Clock();
  const tmp = new THREE.Vector3(), dir = new THREE.Vector3(), mouseW = new THREE.Vector3();
  let visible = true;
  document.addEventListener('visibilitychange', () => { visible = !document.hidden; });

  gsap.ticker.add(() => {
    if (!visible) return;
    const dt = Math.min(clock.getDelta(), 0.05);
    const t = clock.elapsedTime;
    pointer.sx += (pointer.x - pointer.sx) * 0.06;
    pointer.sy += (pointer.y - pointer.sy) * 0.06;
    S.vel += ((lenis.velocity || 0) - S.vel) * 0.1;

    camera.position.x = pointer.sx * 0.45;
    camera.position.y = pointer.sy * 0.3;
    camera.lookAt(0, 0, 0);

    // cup
    const sc = Math.max(S.cupScale, 0.0001);
    tilt.position.set(S.cupX, S.cupY + Math.sin(t * 1.1) * 0.08, 0);
    tilt.scale.setScalar(sc);
    tilt.visible = S.cupScale > 0.002;
    cup.rotation.y = t * 0.35 + S.cupSpin;
    tilt.rotation.z = THREE.MathUtils.clamp(-S.vel * 0.004, -0.35, 0.35) + Math.sin(t * 0.8) * 0.04 - pointer.sx * 0.08;
    tilt.rotation.x = pointer.sy * -0.12;

    // particles
    pGroup.position.set(S.pX, S.pY, 0);
    pGroup.scale.setScalar(S.pScale);
    const u = pMat.uniforms;
    u.uTime.value = t;
    u.uW0.value = S.w0; u.uW.value.set(S.wM, S.wO, S.w6, S.wG); u.uW5.value = S.w100;
    u.uChaos.value = S.chaos; u.uOrbMix.value = S.orbMix; u.uTintMix.value = S.tintMix; u.uOpacity.value = S.opacity;
    u.uVel.value = S.vel;
    // mouse → particle local space
    tmp.set(pointer.x, pointer.y, 0.5).unproject(camera);
    dir.copy(tmp).sub(camera.position).normalize();
    mouseW.copy(camera.position).addScaledVector(dir, -camera.position.z / dir.z);
    u.uMouse.value.set((mouseW.x - S.pX) / S.pScale, (mouseW.y - S.pY) / S.pScale, 0);

    // background glow follows cup / particle centre
    tmp.set(S.cupScale > 0.1 ? S.cupX : S.pX, S.cupScale > 0.1 ? S.cupY : S.pY, 0).project(camera);
    bgMat.uniforms.uGlow.value.lerp({ x: tmp.x, y: tmp.y }, 0.05);
    bgMat.uniforms.uTime.value = t;

    composer.render(dt);
  });

  addEventListener('resize', () => {
    const w = innerWidth, h = innerHeight;
    camera.aspect = w / h; camera.updateProjectionMatrix();
    renderer.setPixelRatio(three.dpr());
    renderer.setSize(w, h); composer.setSize(w, h);
    bgMat.uniforms.uAspect.value = w / h;
    pMat.uniforms.uPR.value = renderer.getPixelRatio();
    const k = currentState; currentState = null; if (k) setState(k);
  });
}

/* =========================================================
   Formula selection — recolours cup, particles and the whole UI
   ========================================================= */
let formulaIdx = -1;
function setFormula(i, animate = true) {
  if (i === formulaIdx) return;
  const prev = formulaIdx;
  formulaIdx = i;
  const f = FORMULAS[i];
  document.documentElement.style.setProperty('--accent', f.color);
  if (three) {
    const c = new THREE.Color(f.color);
    const d = animate ? 1.2 : 0;
    for (const target of [three.liqMat.color, three.liqMat.emissive, three.strawMat.color, three.strawMat.emissive, three.glowMat.uniforms.uColor.value, three.pMat.uniforms.uTint.value, three.bgMat.uniforms.uA.value]) {
      gsap.to(target, { r: c.r, g: c.g, b: c.b, duration: d, ease: 'power2.inOut' });
    }
    three.drawSleeve(f);
    if (animate && prev !== -1) gsap.to(S, { cupSpin: `+=${Math.PI * 2}`, duration: 1.4, ease: 'expo.inOut' });
  }
  // DOM
  $$('#formulaNav button').forEach((b, k) => b.classList.toggle('is-active', k === i));
  const cards = $$('.fcard');
  if (prev !== -1) {
    const out = cards[prev];
    out.classList.remove('is-active');
    gsap.to(out.children, { y: -40, autoAlpha: 0, duration: 0.45, stagger: 0.03, ease: 'power2.in', overwrite: true });
  }
  const inn = cards[i];
  inn.classList.add('is-active');
  gsap.fromTo(inn.children, { y: 60, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: animate ? 0.9 : 0, delay: animate && prev !== -1 ? 0.25 : 0, stagger: 0.06, ease: 'expo.out', overwrite: true });
  const bw = $('#bgWord');
  if (animate) {
    gsap.timeline()
      .to(bw, { yPercent: -60, autoAlpha: 0, duration: 0.4, ease: 'power2.in' })
      .add(() => { bw.textContent = f.name; })
      .fromTo(bw, { yPercent: 60, autoAlpha: 0 }, { yPercent: 0, autoAlpha: 1, duration: 0.9, ease: 'expo.out' });
  } else bw.textContent = f.name;
}

/* =========================================================
   Steps
   ========================================================= */
let stepIdx = -1;
function setStep(i) {
  if (i === stepIdx) return;
  const prev = stepIdx;
  stepIdx = i;
  const steps = $$('.step');
  if (prev !== -1) {
    steps[prev].classList.remove('is-active');
    gsap.to(steps[prev].children, { y: -40, autoAlpha: 0, duration: 0.45, stagger: 0.03, ease: 'power2.in', overwrite: true });
  }
  steps[i].classList.add('is-active');
  gsap.fromTo(steps[i].children, { y: 60, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.9, delay: prev !== -1 ? 0.25 : 0, stagger: 0.07, ease: 'expo.out', overwrite: true });
  $$('.steps__rail i').forEach((el, k) => gsap.to(el, { backgroundColor: k <= i ? getComputedStyle(document.documentElement).getPropertyValue('--accent').trim() : 'rgba(244,248,255,0.12)', duration: 0.6 }));
}

/* =========================================================
   Text splitting
   ========================================================= */
function splitChars(el) {
  const text = el.textContent; el.textContent = '';
  el.setAttribute('aria-label', text);
  for (const ch of text) {
    const s = document.createElement('span'); s.className = 'ch'; s.setAttribute('aria-hidden', 'true');
    s.textContent = ch === ' ' ? ' ' : ch; el.appendChild(s);
  }
  return $$('.ch', el);
}
function splitWords(el) {
  const html = el.innerHTML;
  const tmp = document.createElement('div'); tmp.innerHTML = html;
  el.innerHTML = '';
  const walk = (node, parent) => {
    node.childNodes.forEach((n) => {
      if (n.nodeType === 3) {
        n.textContent.split(/(\s+)/).forEach((part) => {
          if (!part) return;
          if (/^\s+$/.test(part)) { parent.appendChild(document.createTextNode(' ')); return; }
          const m = document.createElement('span'); m.className = 'wm';
          const w = document.createElement('span'); w.className = 'w'; w.textContent = part;
          m.appendChild(w); parent.appendChild(m);
        });
      } else if (n.nodeType === 1) {
        const clone = n.cloneNode(false); parent.appendChild(clone); walk(n, clone);
      }
    });
  };
  walk(tmp, el);
  return $$('.w', el);
}

/* =========================================================
   UI: nav, cursor, magnetic, marquee, reveals
   ========================================================= */
function initUI() {
  // anchor scrolling
  $$('a[data-scroll]').forEach((a) => a.addEventListener('click', (e) => {
    const id = a.getAttribute('href');
    const el = id === '#top' ? 0 : $(id);
    if (el === null) return;
    e.preventDefault();
    lenis.scrollTo(el, { duration: 1.8, easing: (x) => 1 - Math.pow(1 - x, 4) });
  }));

  // nav hide / progress
  const nav = $('#nav'), prog = $('#navProgress');
  let lastY = 0;
  lenis.on('scroll', ({ scroll, limit }) => {
    nav.classList.toggle('is-scrolled', scroll > 40);
    nav.classList.toggle('is-hidden', scroll > lastY && scroll > 400);
    lastY = scroll;
    prog.style.transform = `scaleX(${limit ? scroll / limit : 0})`;
  });

  // cursor
  const cur = $('#cursor');
  if (matchMedia('(hover:hover) and (pointer:fine)').matches) {
    const qx = gsap.quickTo(cur, 'x', { duration: 0.35, ease: 'power3' });
    const qy = gsap.quickTo(cur, 'y', { duration: 0.35, ease: 'power3' });
    addEventListener('pointermove', (e) => { qx(e.clientX); qy(e.clientY); cur.style.opacity = 1; });
    document.addEventListener('pointerover', (e) => cur.classList.toggle('is-hover', !!e.target.closest('a,button,summary,label,input,textarea')));
    // magnetic
    $$('.magnetic').forEach((el) => {
      el.addEventListener('pointermove', (e) => {
        const r = el.getBoundingClientRect();
        gsap.to(el, { x: (e.clientX - r.left - r.width / 2) * 0.25, y: (e.clientY - r.top - r.height / 2) * 0.35, duration: 0.5, ease: 'power3' });
      });
      el.addEventListener('pointerleave', () => gsap.to(el, { x: 0, y: 0, duration: 0.9, ease: 'elastic.out(1,0.4)' }));
    });
    // card tilt
    $$('.tilt').forEach((el) => {
      el.addEventListener('pointermove', (e) => {
        const r = el.getBoundingClientRect();
        const px = (e.clientX - r.left) / r.width - 0.5, py = (e.clientY - r.top) / r.height - 0.5;
        gsap.to(el, { rotateY: px * 12, rotateX: -py * 12, duration: 0.6, ease: 'power3' });
      });
      el.addEventListener('pointerleave', () => gsap.to(el, { rotateY: 0, rotateX: 0, duration: 1, ease: 'elastic.out(1,0.5)' }));
    });
  }

  // marquee (velocity reactive)
  const track = $('#marquee');
  const set = $('.marquee__set', track);
  track.appendChild(set.cloneNode(true)).setAttribute('aria-hidden', 'true');
  const mq = gsap.to(track, { xPercent: -50, duration: 28, ease: 'none', repeat: -1 });
  gsap.ticker.add(() => {
    const v = lenis.velocity || 0;
    mq.timeScale(gsap.utils.clamp(-6, 6, 1 + Math.abs(v) * 0.08) * (v < -0.5 ? -1 : 1));
  });

  // word reveals
  $$('.split-words').forEach((el) => {
    const words = splitWords(el);
    gsap.from(words, { yPercent: 115, rotate: 5, duration: 1.2, stagger: 0.05, ease: 'expo.out', scrollTrigger: { trigger: el, start: 'top 86%' } });
  });
  // generic reveals (hero ones are handled by the intro)
  const reveals = $$('.reveal-up').filter((el) => !el.closest('.hero'));
  gsap.set(reveals, { y: 50, autoAlpha: 0 });
  ScrollTrigger.batch(reveals, { start: 'top 90%', once: true, onEnter: (b) => gsap.to(b, { y: 0, autoAlpha: 1, duration: 1.1, stagger: 0.08, ease: 'expo.out' }) });

  // counters
  $$('.count').forEach((el) => {
    const to = +el.dataset.to;
    const o = { v: to === 0 ? 9 : 0 };
    ScrollTrigger.create({ trigger: el, start: 'top 88%', once: true, onEnter: () => gsap.to(o, { v: to, duration: 2, ease: 'power3.out', onUpdate: () => { el.textContent = Math.round(o.v); } }) });
  });
  gsap.to('#halfRing', { strokeDashoffset: 540.4 * 0.5, duration: 2.2, ease: 'power3.out', scrollTrigger: { trigger: '.why__fact', start: 'top 85%' } });

  // machine reveal
  gsap.to('#machineFrame', { clipPath: 'inset(0% 0% 0% 0% round 22px)', ease: 'none', scrollTrigger: { trigger: '.machine', start: 'top 85%', end: 'center 60%', scrub: 1 } });
  gsap.fromTo('#machineImg', { scale: 1.3, yPercent: -8 }, { scale: 1, yPercent: 0, ease: 'none', scrollTrigger: { trigger: '.machine', start: 'top bottom', end: 'bottom top', scrub: true } });
  gsap.from('.machine__badge', { scale: 0, rotate: -30, duration: 1, ease: 'back.out(2)', scrollTrigger: { trigger: '.machine__media', start: 'center 70%' } });

  // honest strike-through
  gsap.fromTo('.honest__col--no li span', { '--strike': 0 }, { '--strike': 1, stagger: 0.2, ease: 'none', scrollTrigger: { trigger: '.honest__col--no', start: 'top 70%', end: 'bottom 55%', scrub: 1 } });
  gsap.from('.honest__col li', { x: -30, autoAlpha: 0, stagger: 0.06, duration: 0.8, ease: 'expo.out', scrollTrigger: { trigger: '.honest__cols', start: 'top 80%' } });

  // cups parallax
  $$('.cup-card__img img').forEach((img) => gsap.fromTo(img, { yPercent: -8 }, { yPercent: 8, ease: 'none', scrollTrigger: { trigger: img, start: 'top bottom', end: 'bottom top', scrub: true } }));
  gsap.from('.cup-card', { y: 120, rotateX: 25, autoAlpha: 0, stagger: 0.15, duration: 1.4, ease: 'expo.out', scrollTrigger: { trigger: '.cups__grid', start: 'top 85%' } });

  // footer word
  gsap.from('.footer__big', { yPercent: 60, autoAlpha: 0, ease: 'none', scrollTrigger: { trigger: '.footer', start: 'top bottom', end: 'top 40%', scrub: 1 } });

  // FAQ accordion with height animation
  $$('.qa').forEach((d) => {
    const s = $('summary', d), a = $('.qa__a', d);
    s.addEventListener('click', (e) => {
      e.preventDefault();
      if (d.open) gsap.to(a, { height: 0, duration: 0.5, ease: 'power3.inOut', onComplete: () => { d.open = false; a.style.height = ''; ScrollTrigger.refresh(); } });
      else { d.open = true; gsap.fromTo(a, { height: 0 }, { height: 'auto', duration: 0.6, ease: 'expo.out', onComplete: () => ScrollTrigger.refresh() }); }
    });
  });

  // forms
  initForm($('#waitlistForm'), $('#waitlistFoot'));
  initForm($('#contactForm'), $('#contactForm .form__foot'));
}

function initForm(form, foot) {
  if (!form) return;
  const original = foot.textContent;
  form.addEventListener('submit', (e) => {
    let bad = null;
    $$('[required]', form).forEach((inp) => {
      const wrap = inp.closest('.field, .check');
      const ok = inp.type === 'checkbox' ? inp.checked : inp.value.trim() && inp.validity.valid;
      wrap?.classList.toggle('is-invalid', !ok);
      if (!ok && !bad) bad = inp;
    });
    if (bad) {
      e.preventDefault();
      foot.textContent = bad.type === 'checkbox' ? '⚠ Potvrdi privolu da te možemo obavijestiti.' : bad.type === 'email' ? '⚠ Upiši ispravnu email adresu.' : '⚠ Ispuni sva obavezna polja.';
      foot.classList.add('is-error');
      gsap.fromTo(form, { x: -10 }, { x: 0, duration: 0.6, ease: 'elastic.out(1,0.3)' });
      bad.focus();
      return;
    }
    foot.textContent = original; foot.classList.remove('is-error');
    try { window.gtag?.('event', 'generate_lead', { event_category: form.id }); } catch (_) {}
  });
}

/* =========================================================
   Scroll → scene choreography
   ========================================================= */
function initScenes() {
  const steps = $('#kako'), formulas = $('#formule');
  let active = null;
  const resolve = (k) => (k === 'steps' ? `steps${Math.max(stepIdx, 0)}` : k);

  // pinned sub-progress
  ScrollTrigger.create({
    trigger: steps, start: 'top top', end: 'bottom bottom',
    onUpdate: (self) => { setStep(Math.min(2, Math.floor(self.progress * 3))); if (active === 'steps') setState(resolve('steps')); },
  });
  ScrollTrigger.create({
    trigger: formulas, start: 'top top', end: 'bottom bottom',
    onUpdate: (self) => setFormula(Math.min(4, Math.floor(self.progress * 5))),
  });
  $$('#formulaNav button').forEach((b) => b.addEventListener('click', () => {
    const i = +b.dataset.i;
    const top = formulas.offsetTop, span = formulas.offsetHeight - innerHeight;
    lenis.scrollTo(top + span * ((i + 0.5) / 5), { duration: 1.4 });
  }));

  // one active section at a time
  $$('[data-state]').forEach((el) => {
    ScrollTrigger.create({
      trigger: el, start: 'top 50%', end: 'bottom 50%',
      onToggle: (self) => {
        if (!self.isActive) return;
        active = el.dataset.state;
        setState(resolve(active));
        const id = el.id;
        $$('.nav__links a').forEach((a) => a.classList.toggle('is-current', id && a.getAttribute('href') === `#${id}`));
      },
    });
  });

  // hero exit: subtle parallax of copy
  gsap.to('.hero__inner', { yPercent: -18, autoAlpha: 0.2, ease: 'none', scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: true } });
}

/* =========================================================
   Boot: loader → intro
   ========================================================= */
async function boot() {
  const countEl = $('#loaderCount'), fill = $('#loaderFill');
  const prog = { v: 0 };
  const counter = gsap.to(prog, { v: 60, duration: 2.2, ease: 'power2.inOut', onUpdate: () => { countEl.textContent = Math.round(prog.v); fill.style.height = `${(prog.v / 60) * 100}%`; } });

  try { await Promise.race([Promise.all([document.fonts.load('900 100px "Barlow Condensed"'), document.fonts.load('700 100px "Barlow Condensed"')]), new Promise((r) => setTimeout(r, 1200))]); } catch (_) {}

  // fonts are ready → rebuild text-based particle targets & sleeve
  if (three) {
    const g = three.pGroup.children[0].geometry;
    const n = g.attributes.position.count;
    g.setAttribute('aSixty', new THREE.BufferAttribute(sampleText('60', n, 3.4), 3));
    g.setAttribute('aHundred', new THREE.BufferAttribute(sampleText('100', n, 2.6), 3));
  }
  setFormula(0, false);
  setStep(0);
  $$('.step').slice(1).forEach((s) => gsap.set(s.children, { autoAlpha: 0 }));
  $$('.fcard').slice(1).forEach((s) => gsap.set(s.children, { autoAlpha: 0 }));

  const titleChars = $$('.hero__title .split').flatMap(splitChars);
  initUI();
  initScenes();

  await counter.then();
  document.body.classList.remove('is-loading');
  lenis.start();
  window.scrollTo(0, 0);

  const tl = gsap.timeline();
  tl.to('#loader', { clipPath: 'inset(0 0 100% 0)', duration: 1.1, ease: 'expo.inOut' })
    .add(() => { $('#loader').remove(); }, '>')
    .from('#nav', { yPercent: -120, duration: 1, ease: 'expo.out' }, 0.6)
    .from(titleChars, { yPercent: 120, rotate: 8, duration: 1.2, stagger: 0.025, ease: 'expo.out' }, 0.55)
    .from('.hero .reveal-up', { y: 40, autoAlpha: 0, duration: 1, stagger: 0.08, ease: 'expo.out' }, 0.9)
    .to('#heroRing', { strokeDashoffset: 0, duration: 2.4, ease: 'power2.inOut' }, 0.8)
    .from('.hero__scroll, .hero__timer', { autoAlpha: 0, duration: 1 }, 1.4);

  // the scene assembles: cup rises, vortex implodes into place
  gsap.killTweensOf(S);
  currentState = null;
  setState('hero', true);
  S.cupScale = 0; S.cupY = -4; S.chaos = 3; S.opacity = 0;
  const h = STATES.hero();
  gsap.to(S, { cupScale: h.cupScale, cupY: h.cupY, duration: 2.2, ease: 'expo.out', delay: 0.5 });
  gsap.to(S, { cupSpin: Math.PI * 2, duration: 2.6, ease: 'expo.out', delay: 0.5 });
  gsap.to(S, { chaos: 0, opacity: 1, duration: 2.6, ease: 'power3.out', delay: 0.3 });
  ScrollTrigger.refresh();
}
boot();
