// Blocky 3D renderer runtime (rendering_method: blocky3d). Built by pipeline/blocky3d/render.py into
// output/jobs/<id>/blocky3d/. Everything on screen is a pure function of timeline time t (HyperFrames hf-seek):
// no clock, no requestAnimationFrame, every random choice seeded. Units: a person is 5 tall.
import * as THREE from "three";
import { GLTFLoader } from "./loaders/GLTFLoader.js";
import { OBJLoader } from "./loaders/OBJLoader.js";
import { MTLLoader } from "./loaders/MTLLoader.js";

const D = window.__BLOCKY;
const { W, H } = D;
window.__hf = window.__hf || {};
window.__hf.buildReady = window.__hf.buildReady || {};

// ---------------------------------------------------------------- helpers
const rnd = (i, k = 0) => { const x = Math.sin(i * 127.1 + k * 311.7 + 0.5) * 43758.5453; return x - Math.floor(x); };
const clamp01 = (x) => Math.max(0, Math.min(1, x));
const lerp = (a, b, s) => a + (b - a) * s;
const ease = (s) => s * s * (3 - 2 * s);
const easeOut = (s) => 1 - Math.pow(1 - clamp01(s), 3);
function spring(t, z = 0.7, w = 11) {           // closed-form damped spring 0 -> 1 (smooth-motion-studio)
  if (t <= 0) return 0;
  const wd = w * Math.sqrt(1 - z * z);
  return 1 - Math.exp(-z * w * t) * (Math.cos(wd * t) + (z * w / wd) * Math.sin(wd * t));
}
function canvasTex(w, h, draw, repeat) {
  const c = document.createElement("canvas"); c.width = w; c.height = h;
  draw(c.getContext("2d"), w, h);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  if (repeat) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(repeat[0], repeat[1]); }
  return t;
}
const V = (x, y, z) => new THREE.Vector3(x, y, z);

// ---------------------------------------------------------------- renderer + grade
const canvas = document.getElementById("world");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(W, H, false);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(W < H ? 42 : 34, W / H, 0.1, 900);

const GRADES = {
  bright: { sky: ["#3f9df5", "#8fcaff", "#d9efff"], fog: [0xbfe0ff, 90, 320], hemi: [0xeaf4ff, 0x8a9a6a, 1.25], sun: [0xfff0d8, 2.6], exp: 1.05, sunPos: [40, 85, 35] },
  dusk: { sky: ["#3b3f8f", "#d9779a", "#ffc58a"], fog: [0xe8a888, 70, 260], hemi: [0xffd8c0, 0x5a4a6a, 0.9], sun: [0xffa060, 2.3], exp: 1.0, sunPos: [70, 30, 10] },
  night: { sky: ["#05070f", "#121c3d", "#2a3566"], fog: [0x1b2240, 40, 190], hemi: [0x7f96d9, 0x1a1a2a, 0.6], sun: [0x9fb6ff, 1.0], exp: 1.2, sunPos: [-30, 70, 20] },
  fog: { sky: ["#9aa6b2", "#b9c3cc", "#d5dbe0"], fog: [0xc7cfd6, 14, 110], hemi: [0xdfe7ee, 0x7a8288, 1.1], sun: [0xe8eef5, 1.1], exp: 1.0, sunPos: [20, 80, 30] },
};
let G = GRADES[D.grade] || GRADES.bright;
const SKY = {};
const skyOf = (gr0) => SKY[gr0.sky.join()] || (SKY[gr0.sky.join()] = canvasTex(4, 256, (g, w, h) => {
  const gr = g.createLinearGradient(0, 0, 0, h);
  gr.addColorStop(0, gr0.sky[0]); gr.addColorStop(0.62, gr0.sky[1]); gr.addColorStop(1, gr0.sky[2]);
  g.fillStyle = gr; g.fillRect(0, 0, w, h);
}));
let skyTex = skyOf(G);
const spaceTex = canvasTex(4, 256, (g, w, h) => {
  const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, "#02030a"); gr.addColorStop(1, "#141a33");
  g.fillStyle = gr; g.fillRect(0, 0, w, h);
});
const FOG = new THREE.Fog(G.fog[0], G.fog[1], G.fog[2]);
scene.background = skyTex;
scene.fog = FOG;
renderer.toneMappingExposure = G.exp;
const hemi = new THREE.HemisphereLight(G.hemi[0], G.hemi[1], G.hemi[2]);
scene.add(hemi);
const sun = new THREE.DirectionalLight(G.sun[0], G.sun[1]);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048); sun.shadow.radius = 4; sun.shadow.bias = -0.0004;
Object.assign(sun.shadow.camera, { left: -48, right: 48, top: 48, bottom: -48, near: 1, far: 260 });
scene.add(sun, sun.target);
// web series: every scene has its own time of day; Blocky 3D videos keep the one grade they start with
let curGrade = D.grade;
function applyGrade(name) {
  if (name === curGrade) return;
  curGrade = name; G = GRADES[name] || GRADES.bright; skyTex = skyOf(G);
  FOG.color.set(G.fog[0]); FOG.near = G.fog[1]; FOG.far = G.fog[2];
  hemi.color.set(G.hemi[0]); hemi.groundColor.set(G.hemi[1]); hemi.intensity = G.hemi[2];
  sun.color.set(G.sun[0]); sun.intensity = G.sun[1]; renderer.toneMappingExposure = G.exp;
}

// ---------------------------------------------------------------- grounds
function groundTex(kind) {
  const T = (draw, rep) => canvasTex(256, 256, draw, rep);
  const noise = (g, base, spots, n, s) => { g.fillStyle = base; g.fillRect(0, 0, 256, 256);
    for (let i = 0; i < n; i++) { g.fillStyle = spots[i % spots.length]; g.fillRect(rnd(i, 1) * 256, rnd(i, 2) * 256, s, s); } };
  switch (kind) {
    case "paving": return T((g) => { g.fillStyle = "#d9d4cb"; g.fillRect(0, 0, 256, 256); g.strokeStyle = "#bdb6aa"; g.lineWidth = 6;
      for (let i = 0; i <= 4; i++) { g.beginPath(); g.moveTo(0, i * 64); g.lineTo(256, i * 64); g.stroke(); }
      for (let r = 0; r < 4; r++) for (let i = 0; i <= 2; i++) { const x = i * 128 + (r % 2) * 64; g.beginPath(); g.moveTo(x, r * 64); g.lineTo(x, r * 64 + 64); g.stroke(); } }, [60, 60]);
    case "grass": case "road": return T((g) => noise(g, "#6fcf5a", ["#63c050", "#7ad966"], 400, 10), [50, 50]);
    case "forest": return T((g) => noise(g, "#4f8f3e", ["#477f37", "#5c9c48", "#6b5a3a"], 500, 9), [50, 50]);
    case "sand": return T((g) => noise(g, "#f1dcaa", ["#e8cf98", "#f7e6bd"], 500, 6), [60, 60]);
    case "arena": return T((g) => { const c = ["#ffcc3d", "#ff6b6b", "#4fc3f7", "#7bd389"];
      for (let y = 0; y < 4; y++) for (let x = 0; x < 4; x++) { g.fillStyle = c[(x + y) % 4]; g.fillRect(x * 64, y * 64, 64, 64); } }, [30, 30]);
    case "space": return T((g) => noise(g, "#8c8f99", ["#7d808a", "#9a9daa", "#6c6f78"], 600, 8), [40, 40]);
    case "wood": return T((g) => { for (let i = 0; i < 8; i++) { g.fillStyle = i % 2 ? "#c9955e" : "#bf8a52"; g.fillRect(0, i * 32, 256, 32);
      g.fillStyle = "#a87545"; g.fillRect(((i * 97) % 256), i * 32, 3, 32); } }, [8, 8]);
    case "tile": return T((g) => { g.fillStyle = "#f4f4f2"; g.fillRect(0, 0, 256, 256); g.fillStyle = "#cfd8e3";
      for (let y = 0; y < 4; y++) for (let x = 0; x < 4; x++) if ((x + y) % 2) g.fillRect(x * 64, y * 64, 64, 64); }, [10, 10]);
  }
  return T((g) => noise(g, "#888", ["#999"], 10, 4), [20, 20]);
}
const MAT = (o) => new THREE.MeshStandardMaterial(Object.assign({ roughness: 0.9 }, o));
function box(w, h, d, mat, x, y, z, parent) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat); m.position.set(x, y, z);
  m.castShadow = m.receiveShadow = true; parent.add(m); return m;
}
let SEA = null;
function buildBase(lay, grp) {
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(700, 700), MAT({ map: groundTex(lay.indoor ? "grass" : lay.ground) }));
  ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; grp.add(ground);
  if (lay.ground === "road") {
    box(14, 0.12, 400, MAT({ color: 0x5b5f66 }), 0, 0.06, 100, grp);
    for (const s of [-1, 1]) box(3.2, 0.3, 400, MAT({ color: 0xcfcac2 }), s * 8.6, 0.15, 100, grp);
    const dash = MAT({ color: 0xf2f2f2 });
    for (let z = -100; z < 300; z += 8) box(0.45, 0.14, 4, dash, 0, 0.07, z, grp);
  }
  if (lay.path) box(7, 0.1, 400, MAT({ color: 0xd9c9a0 }), 0, 0.05, 100, grp);
  if (lay.sea) {
    const seaTex = canvasTex(128, 128, (g) => { g.fillStyle = "#2c8fd6"; g.fillRect(0, 0, 128, 128); g.fillStyle = "#4aa8ea";
      for (let i = 0; i < 40; i++) g.fillRect(rnd(i, 7) * 128, rnd(i, 8) * 128, 18, 3); }, [40, 20]);
    SEA = new THREE.Mesh(new THREE.PlaneGeometry(800, 300), MAT({ map: seaTex, roughness: 0.25, metalness: 0.1 }));
    SEA.rotation.x = -Math.PI / 2; SEA.position.set(0, 0.08, -26 - 150); grp.add(SEA);
    box(800, 0.06, 4, MAT({ color: 0xffffff, transparent: true, opacity: 0.6 }), 0, 0.1, -26, grp);
  }
  if (lay.barn) {                           // a red barn (no barn in the CC0 packs): walls, gable roof, X doors
    const red = MAT({ color: 0xb8342b }), dark = MAT({ color: 0x6b1f1a }), white = MAT({ color: 0xf3efe6 });
    box(18, 11, 14, red, -12, 5.5, -34, grp);
    for (const s of [-1, 1]) { const r = box(11.6, 0.8, 15, dark, -12 + s * 4.6, 13.4, -34, grp); r.rotation.z = -s * 0.62; }
    box(7, 8, 0.4, dark, -12, 4, -26.9, grp);
    for (const s of [-1, 1]) { const x = box(0.5, 10.4, 0.5, white, -12, 4, -26.6, grp); x.rotation.z = s * 0.72; }
    box(7.6, 0.5, 0.5, white, -12, 8.1, -26.6, grp);
  }
  if (lay.river) {                          // a river across the frame and a bridge broken in the middle
    const water = canvasTex(128, 128, (g) => { g.fillStyle = "#2f86c9"; g.fillRect(0, 0, 128, 128); g.fillStyle = "#57a8e3";
      for (let i = 0; i < 50; i++) g.fillRect(rnd(i, 5) * 128, rnd(i, 6) * 128, 22, 3); }, [60, 3]);
    SEA = new THREE.Mesh(new THREE.PlaneGeometry(400, 14), MAT({ map: water, roughness: 0.25, metalness: 0.1 }));
    SEA.rotation.x = -Math.PI / 2; SEA.position.set(0, 0.1, -19); grp.add(SEA);
    for (const z of [-11.6, -26.4]) box(400, 0.5, 1.4, MAT({ color: 0x8a6a45 }), 0, 0.2, z, grp);
    const wood = MAT({ color: 0x9a6b3f }), post = MAT({ color: 0x5e4026 });
    for (const [z0, z1] of [[-11, -16.5], [-21.5, -27]]) {           // the two halves still standing
      const len = Math.abs(z1 - z0), zc = (z0 + z1) / 2;
      box(5, 0.5, len, wood, 4, 1.4, zc, grp);
      for (const s of [-1, 1]) box(0.3, 1.2, len, post, 4 + s * 2.4, 2.1, zc, grp);
      box(0.6, 2.4, 0.6, post, 1.8, 0.6, z1 + (z1 < z0 ? 0.3 : -0.3), grp); box(0.6, 2.4, 0.6, post, 6.2, 0.6, z1 + (z1 < z0 ? 0.3 : -0.3), grp);
    }
    const broken = box(5, 0.5, 4.6, wood, 4.6, 0.5, -19, grp); broken.rotation.set(0.55, 0.3, 0.2);   // the missing middle, in the water
  }
  if (lay.walls === "arena") {              // painted walls in big flat colours (the camouflage-game look)
    const cols = [0xffcc3d, 0xff6b6b, 0x4fc3f7, 0x7bd389, 0xb084f5, 0xffffff, 0x222222];
    for (let i = 0; i < 14; i++) box(8, 16, 2, MAT({ color: cols[i % cols.length] }), -52 + i * 8, 8, -44, grp);
    for (const s of [-1, 1]) for (let i = 0; i < 12; i++) box(2, 14, 9, MAT({ color: cols[(i + 3) % cols.length] }), s * 34, 7, -36 + i * 9, grp);
  }
  if (lay.stars || D.grade === "night" || D.series) {
    const n = 700, pos = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) { const a = rnd(i, 3) * Math.PI * 2, b = rnd(i, 4) * 0.45 + 0.08;
      pos.set([Math.cos(a) * Math.cos(b) * 500, Math.sin(b) * 500, Math.sin(a) * Math.cos(b) * 500], i * 3); }
    const g = new THREE.BufferGeometry(); g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    grp.userData.stars = new THREE.Points(g, new THREE.PointsMaterial({ color: 0xffffff, size: 1.6, sizeAttenuation: false, fog: false }));
    grp.add(grp.userData.stars);
  }
  if (lay.indoor) {
    const R = lay.room, back = -14;
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(R.w, 60), MAT({ map: groundTex(lay.ground) }));
    floor.rotation.x = -Math.PI / 2; floor.position.set(0, 0.03, back + 30); floor.receiveShadow = true; grp.add(floor);
    const wall = MAT({ color: R.wall });
    box(R.w + 1, R.h, 0.6, wall, 0, R.h / 2, back - 0.3, grp);
    for (const s of [-1, 1]) box(0.6, R.h, 60, wall, s * (R.w / 2 + 0.3), R.h / 2, back + 30, grp);
    const trim = MAT({ color: 0xffffff });
    box(R.w, 0.5, 0.7, trim, 0, 0.25, back + 0.05, grp);
    if (R.window) {
      box(7, 4.2, 0.2, MAT({ color: 0xffffff }), -6, 5.2, back + 0.1, grp);
      box(6.2, 3.4, 0.25, MAT({ color: D.grade === "night" ? 0x1a2350 : 0xa9dcff, emissive: D.grade === "night" ? 0x0a1030 : 0x335577, emissiveIntensity: 0.6 }), -6, 5.2, back + 0.15, grp);
    }
    if (R.board) {
      box(12, 4.6, 0.25, MAT({ color: 0xffffff }), 3, 5.4, back + 0.12, grp);
      box(11.2, 3.9, 0.3, MAT({ color: 0x2f5d3a }), 3, 5.4, back + 0.18, grp);
    }
  }
}

// ---------------------------------------------------------------- models (Kenney CC0 packs, copied into models/)
const gltf = new GLTFLoader(), cache = new Map();
function loadModel(file) {
  if (!cache.has(file)) {
    const url = "models/" + file;
    cache.set(file, file.endsWith(".obj")
      ? new MTLLoader().loadAsync(url.replace(/\.obj$/, ".mtl")).then((mtl) => { mtl.preload(); return new OBJLoader().setMaterials(mtl).loadAsync(url); })
      : gltf.loadAsync(url).then((g) => g.scene));
  }
  return cache.get(file);
}
async function place(p, grp) {
  const src = await loadModel(p.file);
  const obj = src.clone(true);
  const b = new THREE.Box3().setFromObject(obj), sz = b.getSize(V(0, 0, 0)), c = b.getCenter(V(0, 0, 0));
  const s = p.h ? p.h / Math.max(sz.y, 1e-3) : (p.w || 4) / Math.max(sz.x, sz.z, 1e-3);
  obj.scale.setScalar(s);
  obj.position.set(-c.x * s, -b.min.y * s, -c.z * s);
  obj.traverse((m) => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; } });
  const outer = new THREE.Group(); outer.add(obj);
  outer.position.set(p.x, p.y || 0, p.z); outer.rotation.y = (p.r || 0) * Math.PI / 180;
  grp.add(outer);
}
const SETS = {};
const loads = [];
const PROPS = {};                                          // shot props: one copy each, shown by the shots that use them
for (const [id, file] of Object.entries(D.props || {})) loads.push(loadModel(file).then((src) => {
  const g = new THREE.Group(), o = src.clone(true); o.scale.setScalar(3.05);
  o.traverse((m) => { if (m.isMesh) { m.castShadow = m.receiveShadow = true; } });
  g.add(o); g.visible = false; scene.add(g); PROPS[id] = g; }));
for (const [name, lay] of Object.entries(D.sets)) {
  const grp = new THREE.Group(); grp.visible = false; scene.add(grp);
  buildBase(lay, grp);
  for (const p of lay.props) loads.push(place(p, grp));
  SETS[name] = { grp, lay };
}

// ---------------------------------------------------------------- faces (our own design: square eyes + brows)
const FACE_CACHE = new Map();
function face(state, skin, open) {
  const key = state + skin + open;
  if (FACE_CACHE.has(key)) return FACE_CACHE.get(key);
  const tex = canvasTex(256, 256, (g) => {
    g.fillStyle = skin; g.fillRect(0, 0, 256, 256);
    g.fillStyle = "#1c1c22"; g.strokeStyle = "#1c1c22"; g.lineCap = "round"; g.lineJoin = "round";
    const eye = (x, y, ew, eh) => { g.fillStyle = "#1c1c22"; g.fillRect(x - ew / 2, y - eh / 2, ew, eh);
      g.fillStyle = "#fff"; g.fillRect(x - ew / 2 + ew * 0.18, y - eh / 2 + eh * 0.14, ew * 0.3, eh * 0.26); g.fillStyle = "#1c1c22"; };
    const brow = (x1, y1, x2, y2) => { g.lineWidth = 11; g.beginPath(); g.moveTo(x1, y1); g.lineTo(x2, y2); g.stroke(); };
    const closed = (y) => { g.lineWidth = 12; for (const x of [88, 168]) { g.beginPath(); g.moveTo(x - 24, y + 8); g.lineTo(x, y - 4); g.lineTo(x + 24, y + 8); g.stroke(); } };
    const oMouth = (w, h) => { g.beginPath(); g.ellipse(128, 182, w, h, 0, 0, Math.PI * 2); g.fill(); };
    const tear = (x) => { g.fillStyle = "#59b8ff"; g.fillRect(x - 6, 132, 12, 70); g.fillStyle = "#1c1c22"; };
    const big = state === "shocked" || state === "scared";
    if (state === "shut" || state === "crying") closed(108); else eye(88, 112, big ? 30 : 26, big ? 46 : 38), eye(168, 112, big ? 30 : 26, big ? 46 : 38);
    g.lineWidth = 10;
    switch (state) {
      case "happy": brow(66, 70, 108, 66); brow(190, 70, 148, 66);
        if (open) { g.beginPath(); g.arc(128, 160, 34, 0, Math.PI); g.fill(); } else { g.beginPath(); g.arc(128, 160, 34, 0.15 * Math.PI, 0.85 * Math.PI); g.stroke(); } break;
      case "sad": brow(66, 66, 108, 78); brow(190, 66, 148, 78);
        g.beginPath(); g.arc(128, 206, 30, 1.2 * Math.PI, 1.8 * Math.PI); g.stroke(); if (open) oMouth(14, 10); break;
      case "angry": brow(64, 62, 110, 82); brow(192, 62, 146, 82);
        if (open) oMouth(22, 14); else { g.beginPath(); g.moveTo(100, 184); g.lineTo(156, 178); g.stroke(); } break;
      case "scared": brow(64, 74, 108, 62); brow(192, 74, 148, 62);
        if (open) oMouth(18, 22); else { g.lineWidth = 9; g.beginPath(); g.moveTo(92, 186); for (let k = 0; k <= 6; k++) g.lineTo(92 + k * 12, 186 + (k % 2 ? -8 : 8)); g.stroke(); } break;
      case "shocked": brow(64, 58, 108, 56); brow(192, 58, 148, 56); oMouth(16, open ? 28 : 22); break;
      case "smirk": brow(66, 72, 108, 72); brow(190, 64, 148, 70);
        g.beginPath(); g.moveTo(100, 180); g.quadraticCurveTo(140, 186, 160, 168); g.stroke(); break;
      case "crying": brow(66, 64, 108, 76); brow(190, 64, 148, 76); tear(88); tear(168); oMouth(22, open ? 20 : 14); break;
      case "shut": brow(62, 70, 108, 80); brow(194, 70, 148, 80); if (open) oMouth(30, 36); else { g.beginPath(); g.moveTo(108, 180); g.lineTo(148, 180); g.stroke(); } break;
      default: brow(66, 72, 108, 70); brow(190, 72, 148, 70);
        if (open) oMouth(18, 14); else { g.beginPath(); g.moveTo(104, 176); g.lineTo(152, 176); g.stroke(); }
    }
  });
  FACE_CACHE.set(key, tex);
  return tex;
}

// ---------------------------------------------------------------- the rig: boxes, pivots at shoulders and hips
function makeRig() {
  const root = new THREE.Object3D(), body = new THREE.Object3D(); root.add(body);
  const torso = new THREE.Object3D(); torso.position.set(0, 3, 0); body.add(torso);
  const head = new THREE.Object3D(); head.position.set(0, 4.05, 0); body.add(head);
  const headMesh = new THREE.Object3D(); headMesh.position.set(0, 0.55, 0); head.add(headMesh);
  const faceP = new THREE.Object3D(); faceP.position.set(0, 0.5, 0.562); head.add(faceP);
  const hair = new THREE.Object3D(); hair.position.set(0, 1.12, -0.02); head.add(hair);
  const limb = (x, y, dy) => { const p = new THREE.Object3D(); p.position.set(x, y, 0); body.add(p); const m = new THREE.Object3D(); m.position.set(0, dy, 0); p.add(m); return [p, m]; };
  const [armL, armLm] = limb(-1.5, 3.9, -0.9), [armR, armRm] = limb(1.5, 3.9, -0.9), [legL, legLm] = limb(-0.5, 2.0, -1.0), [legR, legRm] = limb(0.5, 2.0, -1.0);
  return { root, body, head, parts: { torso, head: headMesh, face: faceP, hair, armL: armLm, armR: armRm, legL: legLm, legR: legRm },
           pivots: { armL, armR, legL, legR } };
}
const GEOM = { torso: new THREE.BoxGeometry(2, 2, 1), head: new THREE.BoxGeometry(1.12, 1.1, 1.12), face: new THREE.PlaneGeometry(1.0, 1.0),
  hair: new THREE.BoxGeometry(1.26, 0.38, 1.3), armL: new THREE.BoxGeometry(1, 2, 1), armR: new THREE.BoxGeometry(1, 2, 1),
  legL: new THREE.BoxGeometry(1, 2, 1), legR: new THREE.BoxGeometry(1, 2, 1) };
function applyPose(r, p, pos, yaw) {
  r.root.position.copy(pos); r.root.rotation.set(p.rootX || 0, yaw, p.rootZ || 0);
  r.root.position.y += p.rootY || 0;
  r.body.position.y = (r.hipsY || 0) + (p.bob || 0) / (r.S || 1); r.body.rotation.set(p.lean || 0, p.twist || 0, p.tilt || 0);
  r.pivots.armL.rotation.set(p.armL || 0, 0, -(p.armZL ?? p.armZ ?? 0));
  r.pivots.armR.rotation.set(p.armR || 0, 0, p.armZR ?? p.armZ ?? 0);
  r.pivots.legL.rotation.set(p.legL || 0, 0, 0); r.pivots.legR.rotation.set(p.legR || 0, 0, 0);
  r.head.rotation.set(p.headX || 0, p.headY || 0, p.headZ || 0);
}

// actions: pose from global time t, the time in the shot u and a seed k
const LIE = -Math.PI / 2;
const POSE = {
  idle: (t, u, k) => ({ armL: 0.06 * Math.sin(t * 2.1 + k), armR: -0.06 * Math.sin(t * 2.1 + k), armZ: 0.05, bob: 0.03 * Math.sin(t * 2.6 + k), headZ: 0.04 * Math.sin(t * 1.3 + k) }),
  talk: (t, u, k) => Object.assign(POSE.idle(t, u, k), { armR: -0.5 - 0.25 * Math.sin(t * 4.2 + k), armZR: 0.15, headX: 0.05 * Math.sin(t * 5 + k), headY: 0.12 * Math.sin(t * 1.7 + k) }),
  walk: (t, u, k) => { const ph = t * 6 + k; return { armL: 0.5 * Math.sin(ph), armR: -0.5 * Math.sin(ph), legL: -0.55 * Math.sin(ph), legR: 0.55 * Math.sin(ph), armZ: 0.06, bob: 0.12 * Math.abs(Math.cos(ph)) }; },
  run: (t, u, k) => { const ph = t * 12 + k; return { armL: 0.95 * Math.sin(ph), armR: -0.95 * Math.sin(ph), legL: -0.85 * Math.sin(ph), legR: 0.85 * Math.sin(ph), armZ: 0.12, lean: 0.2, bob: 0.3 * Math.abs(Math.cos(ph)), headX: -0.12 }; },
  jump: (t, u, k) => { const c = ((u + k * 0.1) % 1.1) / 1.1, air = Math.max(0, Math.sin(c * Math.PI * 1.25));
    return { rootY: 2.4 * air, armL: -2.6 * air, armR: -2.6 * air, armZ: 0.3, legL: -0.4 * air, legR: -0.4 * air, bob: c > 0.8 ? -0.3 : 0 }; },
  fall: (t, u, k) => { const f = easeOut(u / 0.55); return { rootX: LIE * f, rootY: 0.55 * f, armL: -2.2 * f, armR: -2.0 * f, armZ: 0.6 * f, legL: -0.3 * f, bob: f >= 1 ? 0.02 * Math.sin(t * 2) : 0 }; },
  lie: (t, u, k) => ({ rootX: LIE, rootY: 0.55, armZ: 0.15, bob: 0.03 * Math.sin(t * 1.6 + k) }),
  sleep: (t, u, k) => ({ rootX: LIE, rootY: 0.55, armZ: 0.12, bob: 0.05 * Math.sin(t * 1.2 + k) }),
  sit: (t, u, k) => ({ bob: -1.55 + 0.02 * Math.sin(t * 2 + k), legL: -1.5, legR: -1.5, armL: -0.7, armR: -0.7, armZ: 0.1, headZ: 0.04 * Math.sin(t * 1.1 + k) }),
  wave: (t, u, k) => Object.assign(POSE.idle(t, u, k), { armZR: 2.7 + 0.3 * Math.sin(t * 9 + k), armR: 0, headZ: 0.06 }),
  point: (t, u, k) => Object.assign(POSE.idle(t, u, k), { armR: -1.55, armZR: 0.05, lean: 0.06, headY: 0.05 }),
  dance: (t, u, k) => { const ph = t * 7.2 + k * 1.7; return { armL: -2.5 + 0.45 * Math.sin(ph), armR: -2.5 - 0.45 * Math.sin(ph), armZ: 0.35 + 0.15 * Math.sin(ph * 0.5),
    legL: 0.25 * Math.max(0, Math.sin(ph)), legR: 0.25 * Math.max(0, -Math.sin(ph)), bob: 0.28 * Math.abs(Math.sin(ph)), twist: 0.32 * Math.sin(ph * 0.5), headZ: 0.12 * Math.sin(ph + 0.6) }; },
  cheer: (t, u, k) => { const ph = t * 8 + k; return { armL: -2.9, armR: -2.9, armZ: 0.25 + 0.1 * Math.sin(ph), rootY: 0.5 * Math.max(0, Math.sin(ph)), headX: -0.15 }; },
  scared: (t, u, k) => ({ armL: -2.1, armR: -2.1, armZ: -0.25, lean: -0.1, tilt: 0.03 * Math.sin(t * 40 + k), headX: -0.08, bob: 0.02 * Math.sin(t * 33) }),
  cry: (t, u, k) => ({ armL: -2.4, armR: -2.4, armZ: -0.45, headX: 0.32, lean: 0.12, bob: 0.06 * Math.abs(Math.sin(t * 7 + k)) }),
  freeze: (t, u, k) => ({ armL: -0.25, armR: -0.25, armZ: 0.35, headX: -0.1 }),
};
const ACTION_FACE = { idle: "neutral", talk: "neutral", walk: "neutral", run: "scared", jump: "happy", fall: "shocked", sit: "neutral",
  lie: "neutral", sleep: "shut", wave: "happy", point: "neutral", dance: "happy", cheer: "happy", scared: "scared", cry: "crying", freeze: "shocked" };
const SPEED = { run: 9, walk: 3.2 };

// clothes and hair from presets/blocky_cast/<id>.json
function shirtTex(c) {
  return canvasTex(64, 64, (g) => {
    g.fillStyle = c.shirt_colour; g.fillRect(0, 0, 64, 64);
    if (c.shirt === "stripes") { g.fillStyle = c.shirt_colour2; for (let y = 8; y < 64; y += 16) g.fillRect(0, y, 64, 8); }
    if (c.shirt === "jacket") { g.fillStyle = c.shirt_colour2; g.fillRect(24, 0, 16, 64); g.fillStyle = "#00000033"; g.fillRect(31, 0, 2, 64); }
    if (c.shirt === "suit") { g.fillStyle = c.shirt_colour2; g.beginPath(); g.moveTo(20, 0); g.lineTo(44, 0); g.lineTo(32, 30); g.fill();
      g.fillStyle = "#b3202a"; g.fillRect(29, 4, 6, 26); }
  });
}
function dressHair(r, c, mat) {
  const add = (w, h, d, x, y, z, m = mat) => { const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m); b.position.set(x, y, z); b.castShadow = true; r.parts.hair.add(b); return b; };
  if (c.hair === "bald") { add(0.12, 0.45, 0.9, -0.6, -0.55, -0.05); add(0.12, 0.45, 0.9, 0.6, -0.55, -0.05); return; }
  add(1.26, 0.38, 1.3, 0, 0, 0);
  if (c.hair === "spiky") for (let s = 0; s < 7; s++) { const b = add(0.34, 0.6 + rnd(s, 9) * 0.3, 0.34, -0.45 + (s % 4) * 0.3, 0.3, -0.35 + Math.floor(s / 4) * 0.45); b.rotation.set(-0.5 + rnd(s, 7) * 0.4, 0, -0.6 + rnd(s, 8) * 1.2); }
  if (c.hair === "short") add(1.26, 0.7, 0.3, 0, -0.45, -0.52);
  if (c.hair === "long") { add(1.3, 1.9, 0.32, 0, -1.0, -0.55); add(0.18, 1.3, 1.0, -0.62, -0.7, -0.08); add(0.18, 1.3, 1.0, 0.62, -0.7, -0.08); }
  if (c.hair === "bun") { add(1.26, 0.6, 0.3, 0, -0.4, -0.52); add(0.6, 0.55, 0.6, 0, 0.42, -0.3); }
  if (c.hair === "cap") add(1.0, 0.12, 0.7, 0, -0.1, 0.85);
}
const ACTORS = {};
// studio characters (assets/blocky3d/studio): poseable GLBs (hips, arm_L/R, leg_L/R, neck -> head -> face) built in
// metres, 1.6 m tall -> scaled x STUDIO_S to our 5-unit person; faces are 512 px textures swapped on the face quad
const STUDIO_S = 3.05, STUDIO = {}, FACE_TEX = {};
const texLoader = new THREE.TextureLoader();
for (const [name, c] of Object.entries(D.cast)) if (c.model && c.count === 1) loads.push(loadModel(c.model).then((s) => { STUDIO[name] = s; }));
for (const f of D.studio_faces || []) loads.push(texLoader.loadAsync("models/studio/textures/faces/face_" + f + ".png").then((t) => {
  t.colorSpace = THREE.SRGBColorSpace; t.flipY = false; FACE_TEX[f] = t; }));
const STUDIO_FACE = { shut: "sleeping" };                  // our face names -> studio face files
const OPEN_MOUTH = { happy: "laugh", smile: "laugh", angry: "yelling", scared: "screaming" };
function studioFace(state, lashes, open) {
  let f = STUDIO_FACE[state] || state;
  if (open) f = OPEN_MOUTH[f] || "shocked";
  return FACE_TEX[f + (lashes ? "_lashes" : "")] || FACE_TEX[f] || FACE_TEX["neutral" + (lashes ? "_lashes" : "")];
}
function studioActor(name, c) {
  const obj = STUDIO[name].clone(true), root = new THREE.Object3D();
  obj.scale.setScalar(STUDIO_S); root.add(obj);
  const node = (n) => obj.getObjectByName(n);
  const hips = node("hips"), arms = [node("arm_L"), node("arm_R")].sort((a, b) => a.position.x - b.position.x);
  const legs = [node("leg_L"), node("leg_R")].sort((a, b) => a.position.x - b.position.x);
  let faceMesh = null;
  node("face").traverse((m) => { if (m.isMesh && !faceMesh) faceMesh = m; });
  faceMesh.material = faceMesh.material.clone();
  obj.traverse((m) => { if (m.isMesh) { m.castShadow = m !== faceMesh; m.receiveShadow = true; } });
  const r = { root, body: hips, head: node("neck") || node("head"), hipsY: hips.position.y, S: STUDIO_S,
              pivots: { armL: arms[0], armR: arms[1], legL: legs[0], legR: legs[1] } };   // -x side = our L
  root.visible = false; scene.add(root);
  return { r, faceMesh, c, lashes: !!c.lashes };
}
function actor(name) {
  if (ACTORS[name]) return ACTORS[name];
  if (D.cast[name].model) return (ACTORS[name] = studioActor(name, D.cast[name]));
  const c = D.cast[name], r = makeRig();
  const shirt = MAT({ map: shirtTex(c), roughness: 0.8 }), plain = MAT({ color: c.shirt_colour, roughness: 0.8 });
  const mats = { torso: shirt, armL: c.shirt === "stripes" ? shirt : plain, armR: c.shirt === "stripes" ? shirt : plain,
    head: MAT({ color: c.skin, roughness: 0.7 }), face: MAT({ map: face("neutral", c.skin, false), roughness: 0.7 }),
    hair: MAT({ color: c.hair_colour, roughness: 0.75 }), legL: MAT({ color: c.pants_colour, roughness: 0.8 }) };
  mats.legR = mats.legL;
  for (const [part, node] of Object.entries(r.parts)) {
    if (part === "hair") continue;
    const m = new THREE.Mesh(GEOM[part], mats[part]); m.castShadow = part !== "face"; node.add(m);
  }
  dressHair(r, c, mats.hair);
  if (c.shirt === "dress") { const sk = new THREE.Mesh(new THREE.BoxGeometry(2.3, 1.1, 1.4), plain); sk.position.set(0, 1.55, 0); sk.castShadow = true; r.body.add(sk); }
  r.root.visible = false; scene.add(r.root);
  ACTORS[name] = { r, mats, c };
  return ACTORS[name];
}

// crowd: one InstancedMesh per body part, seeded colours, poses written per frame through a template rig
const CROWD_N = Math.max(0, ...Object.values(D.cast).map((c) => (c.count > 1 ? c.count : 0)));
const crowdName = Object.keys(D.cast).find((n) => D.cast[n].count > 1);
const inst = {};
const crowdFaces = {};
if (CROWD_N) {
  const cc = D.cast[crowdName];
  const SHIRTS = [0xe85d75, 0x4f8ef7, 0xf7c548, 0x9b6cf0, 0x48c9b0, 0xf28c38, 0xffffff, 0x2f3542, 0x7bd389, 0xff8fc7];
  const PANTS = [0x2b2d42, 0x3d5a80, 0x5c4033, 0x1d1f24, 0x6c757d], SKINS = [0xf2d0a7, 0xe0ac80, 0xb57a4f, 0x8d5a3b, 0xffe0c2];
  const HAIRS = [0x1d1f24, 0x6b3e26, 0xe8c26b, 0xc0392b, 0x8e44ad, 0x2c3e50];
  for (const s of ["neutral", "happy", "shocked", "scared", "sad", "angry", "shut", "crying", "smirk"]) crowdFaces[s] = face(s, "#ffffff", false);
  const col = new THREE.Color();
  for (const part of Object.keys(GEOM)) {
    const mat = part === "face" ? MAT({ map: crowdFaces.neutral, roughness: 0.7 }) : MAT({ roughness: 0.8 });
    const im = new THREE.InstancedMesh(GEOM[part], mat, CROWD_N); im.castShadow = part !== "face"; im.count = 0;
    for (let i = 0; i < CROWD_N; i++) {
      const pick = (arr, k) => arr[Math.floor(rnd(i, k) * arr.length)];
      const shirt = cc.random ? pick(SHIRTS, 10) : new THREE.Color(cc.shirt_colour).offsetHSL(0, 0, (rnd(i, 10) - 0.5) * 0.15).getHex();
      const skin = cc.random ? pick(SKINS, 11) : new THREE.Color(cc.skin).getHex();
      const C2 = { torso: shirt, armL: shirt, armR: shirt, legL: cc.random ? pick(PANTS, 12) : new THREE.Color(cc.pants_colour).getHex(),
        head: skin, face: skin, hair: cc.random ? pick(HAIRS, 13) : new THREE.Color(cc.hair_colour).getHex() };
      C2.legR = C2.legL; im.setColorAt(i, col.set(C2[part]));
    }
    scene.add(im); inst[part] = im;
  }
}
const tmpl = makeRig(); scene.add(tmpl.root); tmpl.root.visible = false;
function drawCrowd(n, posOf, poseOf, faceState) {
  if (!CROWD_N) return;
  inst.face.material.map = crowdFaces[faceState] || crowdFaces.neutral;
  for (let i = 0; i < n; i++) {
    const q = posOf(i);
    applyPose(tmpl, poseOf(i), q.pos, q.yaw);
    tmpl.root.updateMatrixWorld(true);
    for (const [part, node] of Object.entries(tmpl.parts)) inst[part].setMatrixAt(i, node.matrixWorld);
  }
  for (const im of Object.values(inst)) { im.count = n; im.instanceMatrix.needsUpdate = true; }
}

// ---------------------------------------------------------------- shots
const SPOTS = [[0, 0], [3.4, -0.8], [-3.4, -0.8], [6.6, -1.6], [-6.6, -1.6]];
const look = V(0, 0, 0);
function speaking(t) { for (const w of D.speech) if (t >= w[0] && t < w[1]) return true; return false; }
function shotAt(t) { let i = 0; while (i < D.shots.length - 1 && t >= D.shots[i + 1].start) i++; return i; }
const capEl = document.getElementById("cap"), signEl = document.getElementById("sign"), signText = document.getElementById("signText");
let lastCap = -1, lastSign = -1;

let LOADED = false;                                        // seeks before the models are in draw nothing
function renderAt(t) {
  if (!LOADED) return;
  const si = shotAt(t), sh = D.shots[si], u = t - sh.start, d = Math.max(0.2, sh.end - sh.start);
  const s = clamp01(u / d);
  if (D.series && sh.grade) applyGrade(sh.grade);
  const S = SETS[sh.set] || Object.values(SETS)[0];
  for (const v of Object.values(SETS)) v.grp.visible = v === S;
  if (D.series && S.grp.userData.stars) S.grp.userData.stars.visible = !!S.lay.stars || curGrade === "night";
  const indoor = S.lay.indoor;
  scene.background = S.lay.stars ? spaceTex : skyTex;     // space is always black, whatever the grade
  scene.fog = S.lay.stars ? null : FOG;
  for (const a of Object.values(ACTORS)) a.r.root.visible = false;
  if (SEA) SEA.material.map.offset.set(t * 0.01, t * 0.02);
  if (sh.type === "line" || sh.type === "card") { renderSeries(t, si, sh, u, s, S); return; }

  const who = sh.type === "shot" ? sh.who : [];
  const people = who.filter((n) => D.cast[n].count === 1);
  const crowdHere = who.some((n) => D.cast[n].count > 1);
  const action = sh.action || "idle";
  const poseT = action === "freeze" ? sh.start : t;
  const move = (SPEED[action] || 0) * u * (indoor ? 0.15 : 1);
  const faceState = sh.face || ACTION_FACE[action] || "neutral";
  const over = sh.camera === "over_shoulder" && people.length > 1;

  // individuals
  let lead = null;
  people.forEach((name, i) => {
    const a = actor(name), [x, z] = over && i === 1 ? [2.2, 7] : SPOTS[Math.min(i, SPOTS.length - 1)];
    const pose = POSE[action](poseT, u, i * 1.3 + sh.seed);
    const pos = V(x, 0, z + move);
    applyPose(a.r, pose, pos, over && i === 1 ? Math.PI : -x * 0.04);
    const talking = action === "talk" && i === 0 && speaking(t) && Math.floor(t * 9) % 2 === 0;
    const open = talking || (faceState === "shut" && action !== "sleep" && action !== "lie");
    if (a.faceMesh) { a.faceMesh.material.map = studioFace(faceState, a.lashes, talking); a.faceMesh.material.needsUpdate = true; }
    else a.mats.face.map = face(faceState, a.c.skin, open);
    a.r.root.visible = true;
    if (i === 0) lead = { pos, lying: ["fall", "lie", "sleep"].includes(action) && (action !== "fall" || u > 0.4), sitting: action === "sit" };
  });
  // the shot's prop (prop=<id>), studio assets are in metres like the characters
  for (const p of Object.values(PROPS)) p.visible = false;
  let propF = null;
  if (sh.prop && PROPS[sh.prop]) {
    const p = PROPS[sh.prop], solo = !lead;
    p.position.set(solo ? 0 : 3.2, 0, solo ? -2 : 1.2 + move); p.rotation.y = solo ? 0.35 * Math.sin(t * 0.4) : -0.4;
    p.visible = true;
    if (solo) { const b = new THREE.Box3().setFromObject(p); propF = b.getCenter(V(0, 0, 0)); propF.y = Math.max(1.2, propF.y); }
  }
  // crowd
  let crowdC = null, crowdDepth = 0;
  if (crowdHere && CROWD_N) {
    const n = Math.min(CROWD_N, D.cast[who.find((w) => D.cast[w].count > 1)].count);
    const cols = Math.max(4, Math.min(22, Math.ceil(Math.sqrt(n * 2.2)))), rows = Math.ceil(n / cols);
    const z0 = people.length ? -8 : 2, gap = indoor ? 1.8 : 2.2;
    crowdDepth = rows * 2.6;
    drawCrowd(n, (i) => ({ pos: V(-(cols - 1) * gap / 2 + (i % cols) * gap + (rnd(i, 1) - 0.5) * 0.9, 0,
      z0 - Math.floor(i / cols) * 2.6 + (rnd(i, 2) - 0.5) * 1.0 + move), yaw: (rnd(i, 3) - 0.5) * 0.5 }),
      (i) => POSE[action](poseT, u, rnd(i, 4) * 6.28), faceState);
    crowdC = V(0, 2.5, z0 - crowdDepth / 2 + move);
  } else drawCrowd(0);

  // camera
  let F, R;
  if (lead && action === "cry") lead.crying = true;
  if (lead) { F = lead.lying ? lead.pos.clone().add(V(0, 0.8, -2.4)) : lead.pos.clone().add(V(0, lead.sitting ? 2.9 : lead.crying ? 3.9 : 4.4, 0)); R = people.length > 1 ? 15 : 12; }
  else if (crowdC) { F = crowdC.clone(); R = Math.max(18, crowdDepth * 1.1 + 10); }
  else if (propF) { F = propF; R = 9; }
  else { F = V(2, 3, -16); R = 20; }           // nobody in the shot: frame the set's middle distance (the bridge, the barn)
  const auto = { run: "track", walk: "track", dance: "orbit", cheer: "orbit", freeze: "high_angle", scared: "close_up", cry: "close_up",
    talk: "push_in", fall: "low_angle" }[action] || "push_in";
  let cam = sh.type === "sign" ? "sign" : (sh.camera === "auto" ? auto : sh.camera);
  if (cam === "close_up" && !lead) cam = "push_in";
  // smooth 3D camera (smooth-motion-studio): every shot travels on a spherical path around its subject with a
  // sine-eased move, a sideways arc (parallax = depth), a soft-spring push on the cut and a slow handheld sway.
  // [yaw0, yaw1, pitch0, pitch1, dist0, dist1 (x R; close_up / sign: absolute), lift]
  const RIG = {
    push_in: [0.14, -0.04, 0.07, 0.04, 1.3, 0.85, 0.9], pull_out: [-0.06, 0.16, 0.04, 0.13, 0.8, 1.3, 0.9],
    locked: [0.06, -0.04, 0.03, 0.03, 1.0, 0.93, 0.9], track: [0.18, 0.04, 0.0, 0.03, 0.82, 0.7, 0.4],
    orbit: [-0.55, 0.55, 0.1, 0.06, 1.0, 0.95, 0.9], crane_up: [0.12, -0.04, -0.14, 0.55, 1.0, 1.12, 0.9],
    crane_down: [-0.1, 0.06, 0.75, 0.04, 1.2, 0.9, 0.9], low_angle: [0.3, 0.06, -0.24, -0.17, 0.68, 0.56, 1.4],
    high_angle: [-0.32, 0.3, 0.95, 0.78, 1.45, 1.15, -2.5], close_up: [0.24, -0.06, 0.04, 0.0, 5.9, 4.6, 0.45],
    over_shoulder: [0.35, 0.22, 0.06, 0.04, 0.6, 0.52, 0.3], whip: [1.15, -0.02, 0.06, 0.04, 1.0, 0.88, 0.9],
    sign: [-0.22, 0.22, 0.12, 0.08, 26, 20, 0.5] };
  const rig = RIG[cam] || RIG.push_in;
  if (cam === "sign") F = V(0, 4.5, -10);
  const dir = si % 2 ? -1 : 1;                                           // alternate the arc side shot to shot
  const inOut = 0.5 - 0.5 * Math.cos(Math.PI * s);
  const k = cam === "whip" ? easeOut(u / 0.32) : inOut;
  const yaw = dir * lerp(rig[0], rig[1], k) + 0.012 * Math.sin(t * 1.9 + si * 2.1) + 0.008 * Math.sin(t * 3.1);
  const pitch = lerp(rig[2], rig[3], inOut) + 0.008 * Math.sin(t * 2.3 + si * 1.3);
  const abs = cam === "close_up" || cam === "sign";
  const dist = (abs ? 1 : R) * lerp(rig[4], rig[5], inOut) * (1 + 0.14 * (1 - spring(u, 0.7, 11)));   // soft settle on the cut
  let P = F.clone().add(V(Math.sin(yaw) * Math.cos(pitch) * dist, Math.sin(pitch) * dist, Math.cos(yaw) * Math.cos(pitch) * dist));
  const L = F.clone().add(V(0, rig[6], 0));
  if (cam === "over_shoulder" && over) P = V(3.5 + 0.6 * inOut, 5.6, 10.2 + move - 0.8 * inOut);
  if (indoor) { P.x = Math.max(-11.5, Math.min(11.5, P.x)); }
  P.y = Math.max(0.7, P.y);
  camera.position.copy(P); camera.lookAt(L);
  sun.target.position.set(F.x, 0, F.z); sun.position.set(F.x + G.sunPos[0], G.sunPos[1], F.z + G.sunPos[2]);
  renderer.render(scene, camera);
  overlays(t, si, sh, u);
}

function overlays(t, si, sh, u) {
  if (D.series) seriesCard(si, sh, u);
  let k = -1;
  for (let j = 0; j < D.caps.length; j++) if (t >= D.caps[j].t0 && t < D.caps[j].t1) k = j;
  if (k !== lastCap) { capEl.innerHTML = k < 0 ? "" : D.caps[k].html; lastCap = k; }
  capEl.style.transform = `translate(-50%, 0) scale(${0.82 + 0.18 * (k < 0 ? 0 : spring(t - D.caps[k].t0, 0.42, 17))})`;
  const isSign = sh.type === "sign";
  if ((isSign ? si : -1) !== lastSign) {
    signEl.className = isSign ? `sign ${sh.sign}` : "sign off";
    signText.textContent = isSign ? sh.text : "";
    lastSign = isSign ? si : -1;
  }
  if (isSign) { const p = spring(u, 0.5, 13); signEl.style.opacity = String(clamp01(u / 0.12));
    signEl.style.transform = `translate(-50%, -50%) scale(${0.7 + 0.3 * p}) rotate(${(1 - p) * -4 + (sh.sign === "note" ? -2 : 0)}deg)`; }
}

// ---------------------------------------------------------------- web series (rendering_method: series)
// pipeline/series/render.py sends one shot per spoken line (type "line") or scene card (type "card"):
// people [{name, x, z}] (the scene's blocking), speaker, listener, focus, faces {name: face}, frame
// (close | react | ots | medium | two | wide | low | high), body (talk | sad | scared | cry), grade per scene.
// Each person's mouth moves only on their own words (D.speech_by), everyone faces the others (cheated to camera).
const SPEECH_BY = D.speech_by || {};
function mouthOf(name, t) {                       // 0 closed, 1 half, 2 open (a syllable-ish flap inside each word)
  const ws = SPEECH_BY[name]; if (!ws) return 0;
  for (const w of ws) if (t >= w[0] && t < w[1]) {
    const len = Math.max(0.06, w[1] - w[0]), syl = Math.max(1, Math.round(len / 0.17));
    const v = Math.abs(Math.sin(((t - w[0]) / len) * Math.PI * syl));
    return v > 0.66 ? 2 : v > 0.25 ? 1 : 0;
  }
  return 0;
}
// studio faces: the face's own eyes and brows + a drawn talking mouth (instead of swapping to another expression)
const TALK_TEX = {};
function talkTex(f, lashes, level) {
  const key = f + (lashes ? "_l" : "") + level;
  if (TALK_TEX[key]) return TALK_TEX[key];
  const base = FACE_TEX[f + (lashes ? "_lashes" : "")] || FACE_TEX[f];
  if (!base || !base.image) return null;
  const c = document.createElement("canvas"); c.width = c.height = 512; const g = c.getContext("2d");
  g.drawImage(base.image, 0, 0, 512, 512);
  g.clearRect(150, 296, 212, 140);                // the mouth band (eyes and brows end above row 260)
  const w = level === 2 ? 64 : 48, hh = level === 2 ? 50 : 26, cx = 256, cy = 340;
  g.fillStyle = "#1c1c22"; g.beginPath(); g.ellipse(cx, cy, w, hh, 0, 0, Math.PI * 2); g.fill();
  g.fillStyle = "#e0566b"; g.beginPath(); g.ellipse(cx, cy + hh * 0.45, w * 0.62, hh * 0.42, 0, 0, Math.PI * 2); g.fill();
  if (level === 2) { g.fillStyle = "#ffffff"; g.fillRect(cx - w * 0.6, cy - hh + 2, w * 1.2, hh * 0.28); }
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace; tex.flipY = false;
  return (TALK_TEX[key] = tex);
}
const STUDIO_ONLY = { smile: "happy", laugh: "happy", yelling: "angry", nervous_sweat: "scared", worried: "sad",
  anime_shocked: "shocked", anime_worried: "scared", smug: "smirk", determined: "angry", glare: "angry", unimpressed: "neutral" };
function setFace(a, state, level) {
  if (a.faceMesh) {
    const f = FACE_TEX[state] || FACE_TEX[state + "_lashes"] ? state : "neutral";
    a.faceMesh.material.map = (level && talkTex(f, a.lashes, level)) || studioFace(f, a.lashes, false);
    a.faceMesh.material.needsUpdate = true;
  } else a.mats.face.map = face(STUDIO_ONLY[state] || state, a.c.skin, level > 0);
}
const HEAD_Y = 4.35;
// a soft key light from the camera's side (no shadows) so faces read at night: series only
const FILL = new THREE.DirectionalLight(0xfff2e6, 0), FILL_BY = { night: 1.15, dusk: 0.65, fog: 0.5, bright: 0.3 };
if (D.series) scene.add(FILL, FILL.target);
function renderSeries(t, si, sh, u, s, S) {
  const indoor = S.lay.indoor;
  scene.background = S.lay.stars ? spaceTex : skyTex;
  scene.fog = S.lay.stars ? null : FOG;
  for (const p of Object.values(PROPS)) p.visible = false;
  drawCrowd(0);
  const ppl = sh.people || [];
  const at = {};
  for (const p of ppl) at[p.name] = V(p.x, 0, p.z);
  // facing: towards the middle of everyone else, cheated 40 % towards the camera (front = +z)
  ppl.forEach((p, i) => {
    const a = actor(p.name), me = at[p.name];
    const others = ppl.filter((q) => q.name !== p.name);
    let yaw = 0;
    if (others.length) {
      const cx = others.reduce((x, q) => x + q.x, 0) / others.length, cz = others.reduce((z, q) => z + q.z, 0) / others.length;
      yaw = Math.atan2(cx - me.x, cz - me.z) * 0.6;
    }
    const talking = sh.type === "line" && p.name === sh.speaker;
    const k = i * 1.3 + 0.7;
    let pose = POSE.idle(t, u, k);
    if (talking) {
      if (sh.body === "scared") pose = POSE.scared(t, u, k);
      else if (sh.body === "cry") pose = POSE.cry(t, u, k);
      else { pose = POSE.talk(t, u, k); if (sh.body === "sad") Object.assign(pose, { headX: 0.2, armR: -0.2 }); }
    } else if (sh.type === "line" && sh.speaker && SPEECH_BY[sh.speaker]) {
      pose.headX = 0.05 * Math.max(0, Math.sin(t * 2.4 + k));           // a listener's slow nod
      pose.headY = (sh.speaker && at[sh.speaker] ? Math.sign(at[sh.speaker].x - me.x) * 0.12 : 0);
    }
    applyPose(a.r, pose, me, yaw);
    a.r.root.visible = true;
    const level = talking ? mouthOf(p.name, t) : 0;
    setFace(a, (sh.faces || {})[p.name] && !talking ? sh.faces[p.name] : talking ? (sh.faces || {})[p.name] || "neutral" : "neutral", level);
  });
  if (sh.speaker && at[sh.speaker] && sh.type === "line") {            // the speaker's own face for this line
    const a = actor(sh.speaker), f = (sh.faces || {})[sh.speaker];
    setFace(a, f || "neutral", mouthOf(sh.speaker, t));
  }

  // camera: a framing per line, a slow dolly inside the shot, a soft settle on the cut, a little handheld sway
  const head = (n) => (at[n] || V(0, 0, 0)).clone().add(V(0, HEAD_Y, 0));
  const facing = (n) => { const a = ACTORS[n]; return a ? a.r.root.rotation.y : 0; };
  const inOut = 0.5 - 0.5 * Math.cos(Math.PI * s);
  const settle = 1 + 0.06 * (1 - spring(u, 0.75, 9));
  const sway = V(0.03 * Math.sin(t * 1.3 + si), 0.02 * Math.sin(t * 1.7 + si * 2), 0);
  const cen = ppl.length ? ppl.reduce((v, p) => v.add(V(p.x, 0, p.z)), V(0, 0, 0)).multiplyScalar(1 / ppl.length) : V(0, 0, -6);
  const span = ppl.length > 1 ? Math.max(...ppl.map((p) => p.x)) - Math.min(...ppl.map((p) => p.x)) : 0;
  let P, L;
  const frame = sh.type === "card" ? "card" : sh.frame || "wide";
  const focus = sh.focus && at[sh.focus] ? sh.focus : (ppl[0] || {}).name;
  if ((frame === "close" || frame === "react") && focus) {
    // a medium close-up: head and shoulders, the eyes on the upper third, look room on the side they face
    const F = head(focus), yw = facing(focus), a = yw * 0.55 + (frame === "react" ? -0.08 : 0.06) * Math.sign(yw || 1);
    const dist = (frame === "react" ? 7.8 : 7.2) * lerp(1.03, 0.96, inOut) * settle;
    P = F.clone().add(V(Math.sin(a) * dist, 0.15, Math.cos(a) * dist));
    L = F.clone().add(V(Math.sin(yw) * 0.8, -0.75, 0));
  } else if (frame === "ots" && focus && sh.listener && at[sh.listener]) {
    // over the listener's shoulder: the camera behind and outside the listener, so their shoulder only edges the
    // frame and the speaker faces us across it
    const F = head(focus), B = head(sh.listener), dir = B.clone().sub(F).setY(0).normalize();
    let side = V(-dir.z, 0, dir.x);
    if (side.z < 0) side.multiplyScalar(-1);                              // the side towards the camera (front)
    P = B.clone().add(dir.clone().multiplyScalar(3.6 * settle)).add(side.multiplyScalar(2.6)).add(V(0, 0.7, 0));
    L = F.clone().add(V(0, -0.55, 0)).lerp(B, 0.12);
  } else if (frame === "medium" && focus) {
    const F = head(focus).add(V(0, -0.9, 0)), yw = facing(focus), a = yw * 0.4;
    const dist = 9.5 * lerp(1.04, 0.95, inOut) * settle;
    P = F.clone().add(V(Math.sin(a) * dist, 0.6, Math.cos(a) * dist)); L = F.clone().add(V(Math.sin(yw) * 0.6, 0, 0));
  } else if (frame === "two" && ppl.length) {
    const F = cen.clone().add(V(0, 3.3, 0)), dist = (8 + span * 1.25) * lerp(1.05, 0.96, inOut) * settle;
    const a = (si % 2 ? -1 : 1) * lerp(0.1, 0.02, inOut);
    P = F.clone().add(V(Math.sin(a) * dist, 0.7, Math.cos(a) * dist)); L = F.clone();
  } else if (frame === "low" && focus) {
    const F = head(focus), yw = facing(focus);
    P = F.clone().add(V(Math.sin(yw * 0.5) * 7, -3.2, Math.cos(yw * 0.5) * 7)); L = F.clone().add(V(0, 0.4, 0));
  } else if (frame === "high" && focus) {
    const F = head(focus);
    P = F.clone().add(V(1.5, 7.5, 7.5 * lerp(1.04, 0.96, inOut))); L = F.clone().add(V(0, -1, 0));
  } else {                                    // wide / card: the whole place, a slow arc
    const F = cen.clone().add(V(0, ppl.length ? 3 : 4, ppl.length ? 0 : -6));
    const dist = (frame === "card" ? 30 : 21 + span) * lerp(1.06, 0.97, inOut);
    const a = (si % 2 ? -1 : 1) * lerp(0.22, 0.08, inOut);
    P = F.clone().add(V(Math.sin(a) * dist, dist * (frame === "card" ? 0.36 : 0.22), Math.cos(a) * dist)); L = F.clone();
  }
  P.add(sway);
  if (indoor) { const w = (S.lay.room.w || 26) / 2 - 1; P.x = Math.max(-w, Math.min(w, P.x)); P.z = Math.min(P.z, 40); P.y = Math.min(P.y, (S.lay.room.h || 12) - 0.8); }
  P.y = Math.max(0.7, P.y);
  camera.position.copy(P); camera.lookAt(L);
  FILL.position.copy(P).add(V(0, 2, 0)); FILL.target.position.copy(L); FILL.intensity = FILL_BY[curGrade] ?? 0.4;
  sun.target.position.set(cen.x, 0, cen.z); sun.position.set(cen.x + G.sunPos[0], G.sunPos[1], cen.z + G.sunPos[2]);
  renderer.render(scene, camera);
  overlays(t, si, sh, u);
}
const cardEl = document.getElementById("card");
let lastCard = -1;
function seriesCard(si, sh, u) {
  if (!cardEl) return;
  const on = sh.type === "card";
  if ((on ? si : -1) !== lastCard) {
    if (on) { document.getElementById("cardN").textContent = "SCENE " + sh.card.number;
      document.getElementById("cardP").textContent = sh.card.place; document.getElementById("cardT").textContent = sh.card.time; }
    lastCard = on ? si : -1;
  }
  if (!on) { cardEl.style.opacity = "0"; return; }
  const d = sh.end - sh.start, fade = Math.min(clamp01(u / 0.35), clamp01((d - u) / 0.35));
  cardEl.style.opacity = String(fade);
  const p = spring(u - 0.1, 0.55, 10);
  document.getElementById("cardP").style.transform = `translateY(${(1 - p) * 18}px) scale(${0.94 + 0.06 * p})`;
  document.getElementById("cardR").style.transform = `scaleX(${easeOut((u - 0.05) / 0.6)})`;
}

const ready = Promise.all(loads).then(() => { LOADED = true; renderAt(0); });
window.__hf.buildReady.blocky = ready;
window.addEventListener("hf-seek", (e) => { renderAt(e.detail.time); });
