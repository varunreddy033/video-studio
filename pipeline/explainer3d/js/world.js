// 3D explainer renderer runtime (rendering_method: explainer3d). Clean CG subjects on a white disc in a coloured
// gradient world, gentle camera moves, infographic overlays (title, meter, chart, count) and 1-3 word captions.
// Everything on screen is a pure function of timeline time t (HyperFrames hf-seek); every random choice is seeded.
import * as THREE from "three";
import { GLTFLoader } from "./loaders/GLTFLoader.js";

const D = window.__EXPLAINER;
const { W, H } = D;
window.__hf = window.__hf || {};
window.__hf.buildReady = window.__hf.buildReady || {};

const clamp01 = (x) => Math.max(0, Math.min(1, x));
const lerp = (a, b, s) => a + (b - a) * s;
const inOut = (s) => 0.5 - 0.5 * Math.cos(Math.PI * clamp01(s));
const easeOut = (s) => 1 - Math.pow(1 - clamp01(s), 3);
const rnd = (i, k = 0) => { const x = Math.sin(i * 127.1 + k * 311.7 + 0.5) * 43758.5453; return x - Math.floor(x); };
function spring(t, z = 0.5, w = 13) {
  if (t <= 0) return 0;
  const wd = w * Math.sqrt(1 - z * z);
  return 1 - Math.exp(-z * w * t) * (Math.cos(wd * t) + (z * w / wd) * Math.sin(wd * t));
}
const V = (x, y, z) => new THREE.Vector3(x, y, z);

// ---------------------------------------------------------------- renderer, lights, backgrounds
const renderer = new THREE.WebGLRenderer({ canvas: document.getElementById("world"), antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H, false);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.1;
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(W < H ? 34 : 28, W / H, 0.05, 2000);
const hemi = new THREE.HemisphereLight(0xffffff, 0x8aa0b8, 1.3); scene.add(hemi);
const key = new THREE.DirectionalLight(0xffffff, 2.4); key.position.set(4, 9, 6); key.castShadow = true;
key.shadow.mapSize.set(2048, 2048); key.shadow.radius = 6; key.shadow.bias = -0.0005;
Object.assign(key.shadow.camera, { left: -12, right: 12, top: 12, bottom: -12, near: 0.5, far: 60 });
scene.add(key, key.target);
const rim = new THREE.DirectionalLight(0xbfe4ff, 1.4); rim.position.set(-6, 5, -8); scene.add(rim);

function radial(inner, outer) {
  const c = document.createElement("canvas"); c.width = 540; c.height = 960;
  const g = c.getContext("2d"), gr = g.createRadialGradient(270, 400, 40, 270, 480, 760);
  gr.addColorStop(0, inner); gr.addColorStop(1, outer); g.fillStyle = gr; g.fillRect(0, 0, 540, 960);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
function linear(stops) {
  const c = document.createElement("canvas"); c.width = 8; c.height = 960;
  const g = c.getContext("2d"), gr = g.createLinearGradient(0, 0, 0, 960);
  stops.forEach(([o, col]) => gr.addColorStop(o, col)); g.fillStyle = gr; g.fillRect(0, 0, 8, 960);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
const BG = { blue: radial("#5cc8ec", "#1c86c0"), deep: radial("#27407a", "#0b1430"), red: radial("#d8443c", "#6e1010"),
  space: radial("#141a3a", "#020308"), dusk: linear([[0, "#2b2a63"], [0.55, "#b2557a"], [1, "#f4a66a"]]),
  white: radial("#ffffff", "#d9e2ea") };
const stars = (() => {
  const n = 1400, p = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { const u = rnd(i, 1) * 2 - 1, th = rnd(i, 2) * 6.283, s = Math.sqrt(1 - u * u);
    p.set([200 * s * Math.cos(th), 200 * u, 200 * s * Math.sin(th)], i * 3); }
  const g = new THREE.BufferGeometry(); g.setAttribute("position", new THREE.BufferAttribute(p, 3));
  const pts = new THREE.Points(g, new THREE.PointsMaterial({ color: 0xffffff, size: 1.5, sizeAttenuation: false }));
  pts.visible = false; scene.add(pts); return pts;
})();
const discMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.55 });

// ---------------------------------------------------------------- models
const gltf = new GLTFLoader(), cache = new Map();
const loadModel = (url) => { if (!cache.has(url)) cache.set(url, gltf.loadAsync(url).then((g) => g.scene)); return cache.get(url); };
function fit(obj, size) {        // scale so the biggest side is `size`, centred on x/z, standing on y = 0
  const b = new THREE.Box3().setFromObject(obj), sz = b.getSize(V(0, 0, 0)), c = b.getCenter(V(0, 0, 0));
  const s = size / Math.max(sz.x, sz.y, sz.z, 1e-3);
  obj.scale.setScalar(s); obj.position.set(-c.x * s, -b.min.y * s, -c.z * s);
  obj.traverse((m) => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; } });
  const g = new THREE.Group(); g.add(obj); return g;
}
const FLOATING = new Set(["earth", "planet_titan"]);

// pictogram people: one InstancedMesh for bodies and one for heads
function crowd(n, colour) {
  const col = { red: 0xe0453a, green: 0x2ecc71, blue: 0x3d8bfd }[colour] || 0xe0453a;
  const mat = new THREE.MeshStandardMaterial({ color: col, roughness: 0.45 });
  const body = new THREE.InstancedMesh(new THREE.CapsuleGeometry(0.16, 0.34, 6, 12), mat, n);
  const head = new THREE.InstancedMesh(new THREE.SphereGeometry(0.15, 16, 12), mat, n);
  body.castShadow = head.castShadow = true;
  const g = new THREE.Group(); g.add(body, head);
  const pos = [];
  const cols = Math.ceil(Math.sqrt(n * 1.4));
  for (let i = 0; i < n; i++) pos.push([((i % cols) - (cols - 1) / 2) * 0.62 + (rnd(i, 3) - 0.5) * 0.18,
    -Math.floor(i / cols) * 0.62 + (Math.ceil(n / cols) - 1) * 0.31 + (rnd(i, 4) - 0.5) * 0.18, rnd(i, 5)]);
  pos.sort((a, b) => (a[0] ** 2 + a[1] ** 2) - (b[0] ** 2 + b[1] ** 2));       // they appear from the middle out
  g.userData = { body, head, pos, n, radius: cols * 0.36 };
  return g;
}
const dummy = new THREE.Object3D();
function drawCrowd(g, u, d) {
  const { body, head, pos, n } = g.userData;
  for (let i = 0; i < n; i++) {
    const appear = clamp01((u - 0.15 - (i / n) * Math.min(1.6, d * 0.55)) / 0.25), s = appear < 1 ? spring(appear * 0.6, 0.45, 14) : 1;
    const [x, z, k] = pos[i], bob = 0.04 * Math.sin(u * 6 + k * 6);
    dummy.position.set(x, 0.33 + bob, z); dummy.scale.setScalar(Math.max(1e-3, s)); dummy.rotation.set(0, 0, 0); dummy.updateMatrix();
    body.setMatrixAt(i, dummy.matrix);
    dummy.position.set(x, 0.72 + bob, z); dummy.updateMatrix(); head.setMatrixAt(i, dummy.matrix);
  }
  body.instanceMatrix.needsUpdate = head.instanceMatrix.needsUpdate = true;
}

// one group per scene, built at load
const SCENES = [];
const loads = [];
D.shots.forEach((sh, i) => {
  const g = new THREE.Group(); g.visible = false; scene.add(g);
  const s = sh.subject, entry = { g, sh, radius: 2, items: [], floating: false };
  SCENES.push(entry);
  if (s.kind !== "none" && !(s.kind === "model" && FLOATING.has(s.model))) {
    const disc = new THREE.Mesh(new THREE.CylinderGeometry(6, 6.2, 0.3, 96), discMat);
    disc.position.y = -0.15; disc.receiveShadow = true; g.add(disc);
  }
  if (s.kind === "model") {
    entry.floating = FLOATING.has(s.model);
    loads.push(loadModel(D.models[s.model]).then((src) => {
      const m = fit(src.clone(true), entry.floating ? 4.2 : 3.0);
      if (entry.floating) m.position.y = -2.1;
      const sz = new THREE.Box3().setFromObject(m).getSize(V(0, 0, 0));   // frame the real shape (tall phone vs flat pool)
      g.add(m); entry.items = [m]; entry.radius = entry.floating ? 2.6 : 0.5 * Math.max(sz.x, sz.y, sz.z) + 0.5;
      entry.height = entry.floating ? 0 : sz.y; }));
  } else if (s.kind === "pile" || s.kind === "food") {
    const ids = s.kind === "food" ? ["apple", "bread_loaf", "fish", "rice_bowl"] : [s.model];
    const n = s.kind === "food" ? 12 : Math.min(s.n, 64);
    loads.push(Promise.all(ids.map((id) => loadModel(D.models[id]))).then((srcs) => {
      const cols = Math.ceil(Math.sqrt(n)), gap = 1.15;
      for (let k = 0; k < n; k++) {
        const m = fit(srcs[k % srcs.length].clone(true), 0.9);
        m.position.set(((k % cols) - (cols - 1) / 2) * gap, 0, (Math.floor(k / cols) - (Math.ceil(n / cols) - 1) / 2) * gap);
        m.rotation.y = rnd(k, i) * 6.28; g.add(m); entry.items.push(m);
      }
      entry.radius = Math.max(1.6, cols * gap * 0.62); }));
  } else if (s.kind === "crowd") {
    const c = crowd(s.n, s.colour); g.add(c); entry.items = [c]; entry.radius = Math.max(1.8, c.userData.radius);
  }
});

// ---------------------------------------------------------------- overlays (2D canvas) + captions
const ov = document.getElementById("ov").getContext("2d");
const S = W / 1080;                                         // overlay sizes are designed at 1080 px wide
function rr(x, y, w, h, r) { ov.beginPath(); ov.moveTo(x + r, y); ov.arcTo(x + w, y, x + w, y + h, r); ov.arcTo(x + w, y + h, x, y + h, r);
  ov.arcTo(x, y + h, x, y, r); ov.arcTo(x, y, x + w, y, r); ov.closePath(); }
function title(text, u) {
  const p = spring(u - 0.05, 0.42, 15); if (p <= 0) return;
  ov.save(); ov.translate(W / 2, H * 0.13); ov.scale(0.6 + 0.4 * p, 0.6 + 0.4 * p); ov.rotate(-0.04 * (1 - p));
  ov.font = `${Math.round(150 * S)}px "Title"`; ov.textAlign = "center"; ov.textBaseline = "middle"; ov.lineJoin = "round";
  ov.lineWidth = 26 * S; ov.strokeStyle = "#ffffff"; ov.strokeText(text, 0, 0);
  ov.fillStyle = "#e8222b"; ov.fillText(text, 0, 0); ov.restore();
}
function meter(m, u) {
  const a = clamp01(u / 0.25), v = m.value / 100 * easeOut((u - 0.2) / 1.2), y = H * 0.82;
  ov.save(); ov.globalAlpha = a; rr(140 * S, y, 800 * S, 130 * S, 30 * S); ov.fillStyle = "rgba(10,20,40,0.55)"; ov.fill();
  ov.font = `${Math.round(40 * S)}px "Body"`; ov.fillStyle = "#fff"; ov.textBaseline = "middle";
  ov.fillText(m.label, 180 * S, y + 40 * S); ov.textAlign = "right"; ov.fillText(Math.round(v * 100) + "%", 900 * S, y + 40 * S);
  rr(180 * S, y + 78 * S, 720 * S, 24 * S, 12 * S); ov.fillStyle = "rgba(255,255,255,0.25)"; ov.fill();
  rr(180 * S, y + 78 * S, Math.max(24, 720 * v) * S, 24 * S, 12 * S); ov.fillStyle = v > 0.6 ? "#ff5a4a" : "#3ee07a"; ov.fill();
  ov.restore();
}
function chart(series, u) {
  const a = clamp01(u / 0.25), x0 = 110 * S, y0 = H * 0.1 + 10 * S * Math.sin(u * 1.6), w = 860 * S, h = 640 * S, cols = ["#2fbf5b", "#e0453a", "#3d8bfd"];
  ov.save(); ov.globalAlpha = a;
  ov.translate(W / 2, y0 + h / 2); ov.rotate(0.012 * Math.sin(u * 1.1)); ov.translate(-W / 2, -(y0 + h / 2));  /* a card that floats, never frozen */ rr(x0, y0, w, h, 40 * S); ov.fillStyle = "rgba(255,255,255,0.94)"; ov.fill();
  const max = Math.max(...series.flatMap((s) => s.values)), min = Math.min(0, ...series.flatMap((s) => s.values));
  const px = (i, n) => x0 + 80 * S + (w - 140 * S) * i / (n - 1), py = (v) => y0 + h - 70 * S - (h - 170 * S) * (v - min) / (max - min || 1);
  ov.font = `${Math.round(34 * S)}px "Body"`; ov.textBaseline = "middle";
  series.forEach((s, k) => {
    ov.fillStyle = cols[k]; ov.fillText("● " + s.name, x0 + 60 * S + k * 260 * S, y0 + 55 * S);
    const prog = easeOut((u - 0.25 - k * 0.15) / 1.4) * (s.values.length - 1);
    ov.strokeStyle = cols[k]; ov.lineWidth = 9 * S; ov.lineJoin = ov.lineCap = "round"; ov.beginPath();
    for (let i = 0; i <= Math.floor(prog); i++) (i ? ov.lineTo : ov.moveTo).call(ov, px(i, s.values.length), py(s.values[i]));
    const f = prog - Math.floor(prog), i0 = Math.floor(prog);
    if (f > 0 && i0 + 1 < s.values.length) ov.lineTo(lerp(px(i0, s.values.length), px(i0 + 1, s.values.length), f), lerp(py(s.values[i0]), py(s.values[i0 + 1]), f));
    ov.stroke();
  });
  ov.restore();
}
function count(text, u) {
  const p = spring(u - 0.1, 0.38, 16); if (p <= 0) return;
  ov.save(); ov.translate(W / 2, H * 0.12); ov.scale(p, p); ov.font = `${Math.round(110 * S)}px "Title"`; ov.textAlign = "center";
  ov.textBaseline = "middle"; ov.lineWidth = 16 * S; ov.strokeStyle = "#0b3d1c"; ov.strokeText(text, 0, 0);
  ov.fillStyle = "#3ee07a"; ov.fillText(text, 0, 0); ov.restore();
}
const capEl = document.getElementById("cap");
let lastCap = -1;
function captionsAt(t) {
  let k = -1;
  for (let j = 0; j < D.caps.length; j++) if (t >= D.caps[j].t0 && t < D.caps[j].t1) k = j;
  if (k !== lastCap) { capEl.textContent = k < 0 ? "" : D.caps[k].text; lastCap = k; }
  capEl.style.transform = `translate(-50%, -50%) scale(${k < 0 ? 0 : 0.85 + 0.15 * spring(t - D.caps[k].t0, 0.45, 18)})`;
}

// ---------------------------------------------------------------- camera: eased path + spring settle on the cut
const RIG = { push_in: [0.18, -0.05, 0.22, 0.16, 1.5, 1.05], pull_out: [-0.05, 0.2, 0.15, 0.28, 1.0, 1.55],
  orbit: [-0.6, 0.6, 0.2, 0.2, 1.3, 1.25], dolly: [0.55, 0.15, 0.12, 0.14, 1.35, 1.2], top: [0.1, -0.15, 1.05, 0.8, 1.6, 1.3],
  close: [0.25, 0.05, 0.12, 0.08, 0.95, 0.72] };
const sceneAt = (t) => { let i = 0; while (i < D.shots.length - 1 && t >= D.shots[i + 1].start) i++; return i; };
let LOADED = false;
function renderAt(t) {
  if (!LOADED) return;
  const si = sceneAt(t), E = SCENES[si], sh = E.sh, u = t - sh.start, d = Math.max(0.3, sh.end - sh.start), s = clamp01(u / d);
  SCENES.forEach((x) => { x.g.visible = x === E; });
  scene.background = BG[sh.bg] || BG.blue; stars.visible = sh.bg === "space";
  // subject life: turntable, float, pops
  if (sh.subject.kind === "model" && E.items[0]) {
    const m = E.items[0], p = spring(u, 0.5, 12);
    m.rotation.y = (E.floating ? 0.25 : 0.35) * t + si; m.scale.setScalar(0.85 + 0.15 * p);
    if (E.floating) m.position.y = -2.1 + 0.08 * Math.sin(t * 1.4);
  } else if (sh.subject.kind === "pile" || sh.subject.kind === "food") {
    E.items.forEach((m, k) => { const a = (u - 0.1 - k * Math.min(0.12, d * 0.6 / E.items.length)) ;
      m.scale.setScalar(Math.max(1e-3, a > 0 ? spring(a, 0.4, 15) : 0)); m.rotation.y += 0; });
  } else if (sh.subject.kind === "crowd" && E.items[0]) drawCrowd(E.items[0], u, d);
  // camera
  const rig = RIG[sh.camera] || RIG.push_in, dir = si % 2 ? -1 : 1, k = inOut(s);
  const R = E.radius * (W < H ? 3.6 : 2.8), yaw = dir * lerp(rig[0], rig[1], k), pitch = lerp(rig[2], rig[3], k);
  const dist = R * lerp(rig[4], rig[5], k) * (1 + 0.12 * (1 - spring(u, 0.7, 11)));
  const F = V(0, E.floating ? 0 : (E.height ? E.height * 0.5 : E.radius * 0.45), 0);
  camera.position.set(F.x + Math.sin(yaw) * Math.cos(pitch) * dist, F.y + Math.sin(pitch) * dist, F.z + Math.cos(yaw) * Math.cos(pitch) * dist);
  camera.lookAt(F.x, F.y + (sh.chart ? -E.radius * 0.6 : 0), F.z);
  renderer.render(scene, camera);
  // overlays
  ov.clearRect(0, 0, W, H);
  if (sh.chart) chart(sh.chart, u);
  if (sh.meter) meter(sh.meter, u);
  if (sh.title) title(sh.title, u);
  if (sh.count) count(sh.count, u);
  captionsAt(t);
}

const ready = Promise.all(loads).then(() => { LOADED = true; renderAt(0); });
window.__hf.buildReady.explainer = ready;
window.addEventListener("hf-seek", (e) => renderAt(e.detail.time));
