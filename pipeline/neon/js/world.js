// Neon motion runtime (rendering_method: neon): kinetic typography on near-black, lime + magenta accents, UI windows,
// a 3D camera on every scene. A pure function of timeline time t (HyperFrames hf-seek): DOM transforms set per frame.
const D = window.__NEON;
const { W, H } = D;
const VERT = H > W, S = Math.min(W, H) / 1080 * (VERT ? 1.35 : 1);     // vertical: bigger UI (the frame is tall)
const LIME = "#D4FF2A", MAG = "#FF2FD0", INK = "#F4F4F0", BG = "#050505";
const clamp01 = (x) => Math.max(0, Math.min(1, x));
const lerp = (a, b, s) => a + (b - a) * s;
const expoOut = (s) => (s >= 1 ? 1 : 1 - Math.pow(2, -10 * clamp01(s)));
const expoIn = (s) => (s <= 0 ? 0 : Math.pow(2, 10 * clamp01(s) - 10));
function spring(t, z = 0.42, w = 17) {
  if (t <= 0) return 0;
  const wd = w * Math.sqrt(1 - z * z);
  return 1 - Math.exp(-z * w * t) * (Math.cos(wd * t) + (z * w / wd) * Math.sin(wd * t));
}
const esc = (s) => s.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
const hl = (s) => esc(s).replace(/\*([^*]+)\*/g, `<span style="background:${LIME};color:${BG};padding:0 .18em">$1</span>`);
const el = (tag, css, inner = "") => { const e = document.createElement(tag); e.style.cssText = css; e.innerHTML = inner; return e; };
const spark = (c, size) => `<svg width="${size}" height="${size}" viewBox="-50 -50 100 100" style="overflow:visible"><g stroke="${c}" stroke-width="7" stroke-linecap="round">${
  Array.from({ length: 12 }, (_, i) => { const a = i / 12 * Math.PI * 2, r = i % 2 ? 38 : 47;
    return `<line x1="${Math.cos(a) * 8}" y1="${Math.sin(a) * 8}" x2="${Math.cos(a) * r}" y2="${Math.sin(a) * r}"/>`; }).join("")}</g></svg>`;

const stage = document.getElementById("stage");
const fx = document.getElementById("fx").getContext("2d");
const grainC = document.getElementById("grain"), grain = grainC.getContext("2d");
const capEl = document.getElementById("cap");

// the time the k-th spoken word of a scene starts (spread evenly when the scene has fewer words)
function wordT(sh, k) {
  const ws = sh.words;
  if (ws.length) return ws[Math.min(k, ws.length - 1)][1];
  return lerp(sh.start + 0.2, sh.end - 0.3, k / 4);
}
const BIG = VERT ? W * 0.2 : H * 0.22;

// ---------------------------------------------------------------- build every scene once
const SC = D.shots.map((sh, i) => {
  const root = el("div", "position:absolute;inset:0;display:none"), cam = el("div", "position:absolute;inset:0;transform-style:preserve-3d");
  root.appendChild(cam); stage.appendChild(root);
  const box = el("div", `position:absolute;left:0;right:0;top:0;bottom:0;display:flex;flex-direction:column;align-items:center;justify-content:center;transform-style:preserve-3d`);
  cam.appendChild(box);
  const parts = [];
  const add = (e) => { box.appendChild(e); parts.push(e); return e; };
  if (sh.kind === "headline") {
    let k = 0;
    sh.lines.forEach((ln, j) => {
      const last = j === sh.lines.length - 1;
      const e = add(el("div", `font:${BIG * (sh.lines.length > 2 ? 0.75 : 1)}px/0.92 "Anton";color:${last ? LIME : INK};text-transform:uppercase;letter-spacing:-.01em;white-space:nowrap`, esc(ln)));
      e._t = wordT(sh, k); k += ln.split(/\s+/).length;
    });
  } else if (sh.kind === "logo") {
    if (sh.extra) { const e = add(el("div", `font:700 ${34 * S}px "Mono";color:${INK};letter-spacing:.5em;margin-bottom:${20 * S}px;text-transform:uppercase`, esc(sh.extra))); e._t = wordT(sh, 0); e._fade = 1; }
    const row = add(el("div", `display:flex;align-items:center;gap:${24 * S}px`));
    row._t = wordT(sh, sh.extra ? 1 : 0);
    row.innerHTML = `<span class="spk">${spark(LIME, 90 * S)}</span><span style="font:${BIG * 0.85}px/1 'Archivo';color:${LIME};text-shadow:0 0 ${40 * S}px rgba(212,255,42,.45);white-space:nowrap">${esc(sh.text)}</span><span class="spk">${spark(LIME, 90 * S)}</span>`;
  } else if (sh.kind === "prompt") {
    const w = VERT ? W * 0.86 : W * 0.62;
    const win = add(el("div", `width:${w}px;border:${2 * S}px solid rgba(244,244,240,.7);background:rgba(20,20,20,.85);box-shadow:0 0 ${60 * S}px rgba(212,255,42,.12)`));
    win.innerHTML = `<div style="display:flex;justify-content:space-between;padding:${14 * S}px ${20 * S}px;border-bottom:${2 * S}px solid rgba(244,244,240,.25);font:700 ${22 * S}px 'Mono';color:${INK};letter-spacing:.15em"><span>● ${esc(sh.extra || "PROMPT")}</span><span style="opacity:.5">NEW GENERATION</span></div>
      <div class="ptext" style="padding:${30 * S}px ${26 * S}px ${40 * S}px;font:700 ${40 * S}px/1.45 'Mono';color:${INK};min-height:${180 * S}px"></div>`;
    win._t = sh.start; win._open = 1;
    win._plain = sh.text.replace(/\*/g, "");
  } else if (sh.kind === "nodes") {
    const row = add(el("div", `display:flex;flex-direction:${VERT ? "column" : "row"};align-items:center;gap:${(VERT ? 90 : 110) * S}px`));
    row._nodes = sh.items.map((it, k) => {
      const n = el("div", `font:700 ${32 * S}px 'Mono';color:${INK};border:${3 * S}px solid ${INK};padding:${22 * S}px ${30 * S}px;letter-spacing:.12em;text-transform:uppercase;background:${BG}`, esc(it));
      n._t = lerp(sh.start + 0.25, sh.end - 0.5, k / Math.max(1, sh.items.length - 1) * 0.85); row.appendChild(n); return n;
    });
  } else if (sh.kind === "stack") {
    const st = add(el("div", `position:relative;width:${(VERT ? 0.62 : 0.5) * W}px;height:${sh.items.length * 110 * S}px;transform:rotateX(52deg) rotateZ(${VERT ? -8 : -14}deg);transform-style:preserve-3d`));
    st._cards = sh.items.map((it, k) => {
      const c = el("div", `position:absolute;left:0;right:0;top:${k * 100 * S}px;height:${82 * S}px;border:${3 * S}px solid ${k === sh.items.length - 1 ? LIME : "rgba(244,244,240,.8)"};background:#101010;display:flex;align-items:center;padding-left:${30 * S}px;font:700 ${34 * S}px 'Mono';color:${k === sh.items.length - 1 ? LIME : INK};letter-spacing:.14em;text-transform:uppercase;box-sizing:border-box`, `<span style="color:${MAG};margin-right:${20 * S}px">▸</span>${esc(it)}`);
      c._t = lerp(sh.start + 0.2, sh.end - 0.5, k / Math.max(1, sh.items.length) * 0.9); st.appendChild(c); return c;
    });
  } else if (sh.kind === "number") {
    const n = add(el("div", `font:${BIG * 1.35}px/0.9 'Anton';color:${MAG};text-shadow:0 0 ${50 * S}px rgba(255,47,208,.5)`, esc(sh.text)));
    n._t = wordT(sh, 0); n._num = sh.text;
    if (sh.extra) { const l = add(el("div", `font:700 ${30 * S}px 'Mono';color:${INK};letter-spacing:.3em;margin-top:${24 * S}px;text-transform:uppercase`, esc(sh.extra))); l._t = wordT(sh, 1); l._fade = 1; }
  } else if (sh.kind === "tunnel") {
    const frames = [];
    for (let k = 0; k < 7; k++) { const f = el("div", `position:absolute;left:50%;top:50%;width:${W * 0.5}px;height:${W * 0.5 * (VERT ? 1.4 : 0.56)}px;border:${4 * S}px solid ${LIME};margin:-${W * 0.25 * (VERT ? 1.4 : 0.56)}px 0 0 -${W * 0.25}px;opacity:.8`); cam.appendChild(f); frames.push(f); }
    const word = add(el("div", `font:${BIG * 0.8}px/1 'Archivo';color:${INK};text-transform:uppercase`, esc(sh.text)));
    word._t = wordT(sh, 0); word._stretch = 1; root._frames = frames;
  } else if (sh.kind === "words") {
    const p = add(el("div", `max-width:${W * 0.82}px;text-align:center;font:${BIG * 0.42}px/1.12 'Archivo';color:${INK}`));
    const toks = sh.text.split(/\s+/);
    p._words = toks.map((w, k) => { const s = el("span", "display:inline-block;margin:0 .14em", hl(w)); s._t = wordT(sh, k); p.appendChild(s); return s; });
  } else if (sh.kind === "endcard") {
    if (sh.extra) { const k = add(el("div", `font:${48 * S}px 'SerifI';color:${INK};opacity:.85;margin-bottom:${10 * S}px`, `✳ ${esc(sh.extra)}`)); k._t = sh.start; k._fade = 1; }
    const row = add(el("div", `display:flex;align-items:center;gap:${20 * S}px`));
    row.innerHTML = `${spark(LIME, 80 * S)}<span style="font:${BIG * 0.8}px/1 'Archivo';color:${LIME};text-shadow:0 0 ${40 * S}px rgba(212,255,42,.45)">${esc(sh.text)}</span>${spark(LIME, 80 * S)}`;
    row._t = wordT(sh, 0);
    const pill = add(el("div", `margin-top:${40 * S}px;font:700 ${30 * S}px 'Mono';color:${INK};border:${3 * S}px solid ${INK};padding:${14 * S}px ${26 * S}px;letter-spacing:.2em`, `COMMENT <span style="background:${LIME};color:${BG};padding:0 .3em">${esc(sh.text.split(/\s+/)[0].toUpperCase())}</span>`));
    pill._t = wordT(sh, 2); pill._fade = 1;
  }
  return { sh, root, cam, parts, i };
});

// ---------------------------------------------------------------- per-frame animation
function landSlam(e, t) {               // a big word slams in: 2.4x -> 1x with blur, lands on its spoken word
  const u = t - e._t;
  if (u < 0) { e.style.opacity = 0; return false; }
  if (e._fade) { e.style.opacity = clamp01(u / 0.25); e.style.transform = `translateY(${(1 - expoOut(u / 0.4)) * 30 * S}px)`; return false; }
  const s = expoOut(u / 0.22);
  e.style.opacity = clamp01(u / 0.06);
  e.style.transform = `scale(${lerp(2.4, 1, s)}) rotateX(${(1 - s) * -30}deg)`;
  e.style.filter = s < 1 ? `blur(${(1 - s) * 14 * S}px)` : "none";
  return u < 0.25;
}
function typeCount(sh, plain, t) {      // characters typed so far, paced by the scene's spoken words
  const ws = sh.words;
  if (!ws.length) return Math.floor(plain.length * clamp01((t - sh.start) / Math.max(0.5, sh.end - sh.start - 0.4)));
  const n = ws.length, k = ws.findIndex((w) => w[1] > t);
  const done = k < 0 ? n : k, frac = done / n;
  return Math.min(plain.length, Math.floor(plain.length * frac + (k < 0 ? plain.length : 0)));
}
function sceneAt(t) { let i = 0; while (i < SC.length - 1 && t >= SC[i + 1].sh.start) i++; return i; }

function drawGrain(t) {
  // new grain on every frame (grain at 24/s against 30 fps left every 5th frame frozen)
  const f = Math.round(t * 600), w = grainC.width, h = grainC.height, img = grain.createImageData(w, h);
  let seed = f * 9301 + 49297;
  for (let i = 0; i < img.data.length; i += 4) { seed = (seed * 9301 + 49297) % 233280; const v = (seed / 233280) * 255;
    img.data[i] = img.data[i + 1] = img.data[i + 2] = v; img.data[i + 3] = 255; }
  grain.putImageData(img, 0, 0);
}

function renderAt(t) {
  const si = sceneAt(t), C = SC[si], sh = C.sh, u = t - sh.start, d = Math.max(0.3, sh.end - sh.start);
  SC.forEach((x) => { x.root.style.display = x === C ? "block" : "none"; });
  fx.clearRect(0, 0, W, H);
  let shake = 0;
  // kinds
  for (const e of C.parts) {
    if (e._open) {                                           // prompt window: shutter open, then typed text
      const o = expoOut((t - e._t) / 0.45);
      e.style.clipPath = `inset(${(1 - o) * 49}% 0% ${(1 - o) * 49}% 0%)`;
      e.style.transform = `rotateX(${8 - 6 * clamp01(u / d)}deg) rotateY(${-10 + 16 * clamp01(u / d)}deg)`;
      const n = typeCount(sh, e._plain, t), shown = [];
      let c = 0;
      for (const part of sh.text.split(/(\*[^*]+\*)/)) {     // keep highlights while typing
        const raw = part.replace(/\*/g, ""), take = raw.slice(0, Math.max(0, n - c)); c += raw.length;
        if (take) shown.push(part.startsWith("*") ? `<span style="background:${LIME};color:${BG};padding:0 .15em">${esc(take)}</span>` : esc(take));
      }
      e.querySelector(".ptext").innerHTML = shown.join("") + `<span style="opacity:${Math.floor(t * 2.2) % 2 ? 1 : 0};color:${LIME}">▌</span>`;
    } else if (e._nodes) {
      const pts = e._nodes.map((n) => { const a = clamp01((t - n._t) / 0.35); n.style.opacity = a > 0 ? 1 : 0;
        n.style.transform = `scale(${a > 0 ? spring(t - n._t, 0.4, 16) : 0})`; const r = n.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2, n._t, r.width / 2, r.height / 2]; });
      for (let k = 0; k + 1 < pts.length; k++) {               // glowing wire grows to the next box, a comet runs along it
        const g = clamp01((t - pts[k][2] - 0.2) / Math.max(0.2, pts[k + 1][2] - pts[k][2] - 0.2));
        if (g <= 0) continue;
        // from box edge to box edge, so the wire never crosses a label
        const [cx1, cy1, , hw1, hh1] = pts[k], [cx2, cy2, , hw2, hh2] = pts[k + 1];
        const x1 = VERT ? cx1 : cx1 + hw1, y1 = VERT ? cy1 + hh1 : cy1, x2 = VERT ? cx2 : cx2 - hw2, y2 = VERT ? cy2 - hh2 : cy2;
        const xe = lerp(x1, x2, g), ye = lerp(y1, y2, g);
        fx.save(); fx.strokeStyle = LIME; fx.shadowColor = LIME; fx.shadowBlur = 24 * S; fx.lineWidth = 5 * S; fx.lineCap = "round";
        fx.beginPath(); fx.moveTo(x1, y1); fx.lineTo(xe, ye); fx.stroke();
        const c = (t * 0.9 + k * 0.3) % 1; fx.fillStyle = "#fff"; fx.beginPath(); fx.arc(lerp(x1, xe, c), lerp(y1, ye, c), 7 * S, 0, 7); fx.fill(); fx.restore();
      }
    } else if (e._cards) {
      e._cards.forEach((c, k) => { const a = t - c._t; c.style.opacity = a > 0 ? 1 : 0;
        c.style.transform = `translateZ(${(a > 0 ? spring(a, 0.5, 14) : 0) * (k * 26 * S)}px) translateX(${a > 0 ? (1 - spring(a, 0.5, 14)) * -W * 0.4 : 0}px)`; });
    } else if (e._words) {
      e._words.forEach((w) => { const a = t - w._t; w.style.opacity = a > 0 ? 1 : 0.12;
        w.style.transform = `translateY(${a > 0 ? (1 - spring(a, 0.45, 16)) * 40 * S : 0}px)`; });
    } else {
      if (landSlam(e, t)) shake = Math.max(shake, 1 - (t - e._t) / 0.25);
      if (e._stretch && t >= e._t) e.style.letterSpacing = `${lerp(0.6, 0.02, expoOut((t - e._t) / 0.6))}em`;
      if (e._num && t >= e._t) {                             // count up numbers like 5H, 40%, 1,000
        const m = e._num.match(/^([^\d]*)([\d,.]+)(.*)$/);
        if (m) { const v = parseFloat(m[2].replace(/,/g, "")), k = expoOut((t - e._t) / 0.7);
          e.textContent = m[1] + (Number.isInteger(v) ? Math.round(v * k).toLocaleString("en-US") : (v * k).toFixed(1)) + m[3]; }
      }
    }
  }
  C.root.querySelectorAll(".spk svg").forEach((s, k) => { s.style.transform = `rotate(${t * 90 * (k ? -1 : 1)}deg) scale(${0.9 + 0.1 * Math.sin(t * 4)})`; });
  if (C.root._frames) C.root._frames.forEach((f, k) => {     // tunnel: frames fly at the camera, forever
    const z = ((t * 0.55 + k / 7) % 1), sc = 0.15 * Math.pow(18, z);
    f.style.transform = `scale(${sc}) rotate(${(k % 2 ? 1 : -1) * 6 * z}deg)`; f.style.opacity = String(clamp01(z * 3) * clamp01((1 - z) * 4));
  });
  // 3D camera: a slow push, a drift that alternates side, a spring kick on the cut, a shake when something slams,
  // and the exit: the last 0.28 s zooms through with blur
  const dir = si % 2 ? -1 : 1, s = clamp01(u / d), kick = 1 - spring(u, 0.55, 14);
  const ex = clamp01((u - (d - 0.28)) / 0.28), exE = expoIn(ex);
  const jx = shake * 14 * S * Math.sin(t * 90), jy = shake * 10 * S * Math.cos(t * 77);
  C.cam.style.transform = `translate(${jx}px, ${jy}px) scale(${(1 + 0.06 * s + 0.08 * kick) * (1 + 1.6 * exE)}) rotateY(${dir * lerp(6, -4, s)}deg) rotateX(${lerp(4, -2, s)}deg)`;
  C.cam.style.filter = exE > 0.02 ? `blur(${exE * 18 * S}px)` : "none";
  C.cam.style.opacity = String(1 - exE * 0.9);
  if (shake > 0.6) { fx.fillStyle = `rgba(212,255,42,${(shake - 0.6) * 0.35})`; fx.fillRect(0, 0, W, H); }   // lime flash on a slam
  // HUD, captions, grain
  const tc = new Date(t * 1000).toISOString().substr(14, 8).replace(".", ":");
  document.getElementById("hudTR").textContent = `00:${tc}`;
  document.getElementById("hudBR").textContent = `SCENE ${String(si + 1).padStart(2, "0")}/${String(SC.length).padStart(2, "0")}`;
  let k = -1;
  for (let j = 0; j < D.caps.length; j++) if (t >= D.caps[j].t0 && t < D.caps[j].t1) k = j;
  capEl.innerHTML = k < 0 ? "" : D.caps[k].html;
  drawGrain(t);
}

window.__hf = window.__hf || {};
window.__hf.buildReady = window.__hf.buildReady || {};
window.__hf.buildReady.neon = document.fonts.ready.then(() => renderAt(0));
window.addEventListener("hf-seek", (e) => renderAt(e.detail.time));
