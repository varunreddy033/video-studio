// Storyboard page of Video Studio (docs/STORYBOARD_PLAN.md): the Theme tab, the scene grid and the scene editor.
// Loaded after index.html's own script and uses its helpers (h, $, api, toast, data, current, go, progressCard).
// A scene is shown as its real composition in an <iframe> (same HTML / CSS / GSAP timeline as the render); edits are
// a CSS block on top of it, the same block the server writes into the scene (pipeline/motion_gfx/storyboard.py).

let sbOpen = false, sb = null, sbSel = null, sbPath = null, sbEdit = { els: {} }, sbUndo = [], sbRedo = [];
let sbFrameEl = null, sbSaveTimer = null, sbView = "current", sbStamp = Date.now(), sbOrig = new Map(), sbDrag = null;
let sbTab = "element", sbHover = null, sbPosterReq = null, sbApplying = false;
const SB_TEXT_TYPES = ["kinetic", "title", "figure", "chapter", "memo"];
const sbNice = (x) => String(x).replace(/_/g, " ");
const SB_WRAPPERS = ["stage", "far", "cam", "mid", "near", "life", "ent"];

const sbFill = (box, ...kids) => fill(box, ...kids.flat().filter(k => k !== null && k !== undefined && k !== false));

// ------------------------------------------------------------------ Theme tab (Look & sound)
function themePane(r, getText, setText, recheck) {
  const box = h("div", {}, h("p", { class: "hint" }, "Loading themes…"));
  (async () => {
    let list; try { list = await lookList("themes", "/api/themes"); } catch (e) { box.firstChild.textContent = e.message; return; }
    const cur = (r.theme || {}).id || "auto";
    const motion = (r.stats || {}).rendering_method === "motion";
    const pick = (id) => { if (id === cur) return; setText(setHeaderKey(getText(), "theme", id === "auto" ? null : id)); recheck(); };
    const sets = (t) => { const s = Object.assign({}, (t.settings || {}).all, (t.settings || {})[motion ? "motion" : "ai_image"]);
      if (motion && t.show) s.show = t.show; return Object.entries(s).map(([k, v]) => `${k.replace("_", " ")}: ${String(v).replace(/^theme_/, "").replace(/_/g, " ")}`).join(" · "); };
    sbFill(box, 
      h("p", { class: "hint", style: "margin-top:0" }, "One theme per video: colours, type, scene design, camera and transitions together. "
        + "A click writes theme: into the script header. Lines you set yourself in the other tabs still win over the theme."),
      h("div", { class: "styles" }, list.map(t => { const pv = t.base || (t.show && !t.show.startsWith("theme_") ? t.show : null);
        return tile(t.id === cur, () => pick(t.id), "Use this theme",
          h("div", { class: "pv wide" + (pv ? "" : " autopv") }, pv ? h("img", { src: `/api/formats/${pv}/preview.jpg`, alt: t.label + " preview", loading: "lazy" }) : h("b", {}, "AUTO"),
            (t.swatch || []).length ? h("div", { class: "sw" }, t.swatch.map(c => h("i", { style: `background:${c[0]};border-color:${c[2]}` }))) : null),
          h("b", {}, t.label + (t.id === cur ? " ✓" : "")), h("span", {}, t.description), sets(t) ? h("small", { style: "color:var(--muted)" }, sets(t)) : null); })));
  })();
  return box;
}

// ------------------------------------------------------------------ page
function sbBusy() { return data && ["queued", "rendering"].includes(data.status); }
function openStoryboard() { sbOpen = true; sbSel = null; sbView = "current"; showStoryboard(true); }
function closeStoryboard() { sbFlush(); sbOpen = false; sbSel = null; $("#main").classList.remove("wide"); showJob(); }
const sbScene = (sid) => sb.scenes.find(s => s.sid === sid);
const sbUrl = (s, q = "") => `/api/jobs/${current}/storyboard/frame/${s.sid}?t=${sbStamp}${q}`;

async function showStoryboard(reload = true) {
  const m = $("#main"); m.classList.add("wide");
  if (reload || !sb) { try { sb = await api(`/api/jobs/${current}/storyboard`); sbStamp = Date.now(); } catch (e) { toast(e.message); return; } }
  if (!sbOpen) return;
  if (sbSel && !sbScene(sbSel)) sbSel = null;
  // while a build or render runs the scene files are being rewritten: show the progress, not half-written scenes
  fill(m, ...(sbBusy() ? [sbTop(), progressCard(), h("p", { class: "hint" }, "The scenes come back when this has finished. Your edits are saved.")]
    : [sbTop(), !sb.scenes.length ? sbEmpty() : sbSel ? sbEditor() : sbGrid()]));
}

function sbTop() {
  const busy = sbBusy(), n = sb.scenes.length;
  const changed = sb.scenes.filter(s => s.edited || s.regenerated).length;
  const theme = h("select", { class: "inp", style: "width:auto", disabled: busy, title: "Storyboard theme of this video",
    onchange: async (e) => { const id = e.target.value;
      if (!confirm("Change the theme and build the storyboard again? Scenes you edited keep their edits where the layout stays the same.")) { e.target.value = (sb.theme || {}).id || "auto"; return; }
      try { const text = setHeaderKey(data.script, "theme", id === "auto" ? null : id);
        await api(`/api/jobs/${current}/script`, { method: "PUT", body: JSON.stringify({ text }) }); editText = null;
        await api(`/api/jobs/${current}/storyboard`, { method: "POST", body: "{}" }); refresh(true); } catch (err) { toast(err.message); } } });
  lookList("themes", "/api/themes").then(list => { fill(theme, ...list.map(t => h("option", { value: t.id }, t.label))); theme.value = (sb.theme || {}).id || "auto"; }).catch(() => {});
  const build = async () => { try { await api(`/api/jobs/${current}/storyboard`, { method: "POST", body: "{}" }); refresh(true); } catch (e) { toast(e.message); } };
  const render = async (mode) => { await sbFlush(); go(mode); };
  return h("div", { class: "row sbtop" },
    h("button", { class: "btn small", onclick: sbSel ? () => { sbFlush(); sbSel = null; showStoryboard(true); } : closeStoryboard }, sbSel ? "All scenes" : "Back to the video"),
    h("h2", {}, "Storyboard"), h("span", { class: "hint" }, n ? `${n} scenes, ${ts(sb.scenes.reduce((a, x) => a + x.dur, 0))}${changed ? `, ${changed} changed by you` : ""}` : ""),
    h("div", { class: "spacer" }), h("span", { class: "hint" }, "Theme"), theme,
    h("button", { class: "btn small", disabled: busy, onclick: build, title: "Voice + scenes only, no video render" }, n ? "Rebuild storyboard" : "Build storyboard"),
    h("button", { class: "btn small", disabled: busy || !n, onclick: () => render("draft"), title: "Draft render with every accepted change (unchanged scenes are reused from the last draft)" }, "Preview video"),
    h("button", { class: "btn small primary", disabled: busy || !n, onclick: () => render("final") }, "Make final"));
}

function sbEmpty() {
  return h("div", { class: "card" }, h("h3", {}, "No storyboard yet"),
    h("p", { class: "hint" }, sbBusy() ? "Building…" : "Press Build storyboard: it makes the voice and every scene (about as long as a draft's first step), without rendering a video. "
      + "Then you can look at each scene, move and restyle things, and regenerate single scenes before the final."));
}

const sbVert = () => sb.size[1] > sb.size[0];
const sbPosterUrl = (s) => sb.posters && sb.posters[s.sid] ? `/api/jobs/${current}/storyboard/poster/${sb.posters[s.sid]}` : null;

// A scene's picture: its poster (a still made once on the server), a shimmer while the poster is being made.
// Live pages are expensive (a 1080p scene paints for ~0.5 s), so at most ONE plays at a time: the card under the mouse.
function sbShot(s, opts = {}) {
  const url = sbPosterUrl(s);
  const box = h("div", { class: "sbshot" + (sbVert() ? " vert" : "") + (url ? "" : " wait"), "data-sid": s.sid },
    url ? h("img", { src: url, alt: `Scene ${s.n}: ${s.text}`, decoding: "async", loading: "lazy" }) : null,
    opts.badges === false ? null : h("span", { class: "num" }, String(s.n)),
    opts.badges === false ? null : h("span", { class: "dur" }, `${s.dur.toFixed(1)} s`));
  if (opts.live) {
    box.addEventListener("mouseenter", () => sbLive(box, s));
    box.addEventListener("mouseleave", () => sbLiveStop(box));
  }
  return box;
}
function sbLive(box, s) {
  sbLiveStop();
  const [W, H] = sb.size, k = box.clientWidth / W;
  const fr = h("iframe", { class: "live", src: sbUrl(s), tabindex: "-1", title: `Scene ${s.n} preview`, style: `width:${W}px;height:${H}px;transform:scale(${k})` });
  sbHover = { box, fr, timer: null };
  fr.addEventListener("load", () => { const wait = () => { if (!sbHover || sbHover.fr !== fr) return; const w = fr.contentWindow;
    if (w && w.SB && w.SB.ready) { fr.classList.add("on"); if (w.SB.tl) { w.SB.tl.repeat(-1).restart(); } } else sbHover.timer = setTimeout(wait, 40); }; wait(); });
  box.append(fr);
}
function sbLiveStop(box) {
  if (!sbHover || (box && sbHover.box !== box)) return;
  clearTimeout(sbHover.timer); sbHover.fr.remove(); sbHover = null;
}
// posters that are missing or out of date (a scene changed): made in one batch, then swapped in place
async function sbPosters() {
  if (sbBusy() || sbPosterReq || !sb || !sb.scenes.length || sb.scenes.every(s => sb.posters && sb.posters[s.sid])) return;
  sbPosterReq = api(`/api/jobs/${current}/storyboard/posters`, { method: "POST", body: "{}" });
  try { sb.posters = await sbPosterReq; } catch (e) { toast("Scene pictures: " + e.message); sbPosterReq = null; return; }
  sbPosterReq = null;
  document.querySelectorAll(".sbshot.wait[data-sid]").forEach(box => { const s = sbScene(box.dataset.sid), url = s && sbPosterUrl(s);
    if (url) { box.classList.remove("wait"); box.prepend(h("img", { src: url, alt: `Scene ${s.n}: ${s.text}`, decoding: "async" })); } });
}
// the whole video as a strip: every scene as wide as it is long (chapters marked, changed scenes underlined)
function sbReel() {
  return h("div", { class: "sbreel", role: "list" }, sb.scenes.map(s => h("button", {
    class: [s.chapter && s.n > 1 && sb.scenes[s.n - 2].chapter !== s.chapter ? "ch" : "", s.sid === sbSel ? "on" : "",
      s.edited || s.regenerated || s.pending != null || (sb.state[s.sid] || {}).opts ? "mod" : ""].join(" "),
    style: `flex-grow:${s.dur}`, title: `Scene ${s.n} · ${s.dur.toFixed(1)} s · ${s.text}`, role: "listitem",
    onclick: () => sbOpenScene(s.sid) }, s.dur > 1.2 ? String(s.n) : "")));
}

function sbFlags(s) {
  return [s.pending != null ? h("span", { class: "chip info" }, "new version waiting") : null,
    s.regenerated ? h("span", { class: "chip warn" }, `version ${s.current}`) : null,
    s.edited ? h("span", { class: "chip ok" }, "edited") : null,
    s.stale ? h("span", { class: "chip bad", title: "The edits were made on another layout of this scene and are not applied" }, "edits not applied") : null];
}

function sbGrid() {
  let chapter = null; const out = [];
  for (const s of sb.scenes) {
    if (s.chapter && s.chapter !== chapter) { chapter = s.chapter; out.push(h("h3", { class: "sbchap" }, chapter)); }
    const o = (sb.state[s.sid] || {}).opts;
    out.push(h("div", { class: "sbcard", role: "button", tabindex: "0", "aria-label": `Edit scene ${s.n}`, onclick: () => sbOpenScene(s.sid),
        onkeydown: (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); sbOpenScene(s.sid); } } },
      sbShot(s, { live: true }),
      h("div", { class: "meta" }, h("span", { class: "chip" }, sbNice(s.template)), h("span", { class: "hint" }, ts(s.start)), ...sbFlags(s),
        o ? h("span", { class: "chip info", title: "Options set by hand: " + Object.keys(o).join(", ") }, "custom") : null),
      h("div", { class: "sbtext" }, s.text),
      h("div", { class: "foot" }, [s.icons.length ? `picture: ${s.icons.map(i => i.split(":")[1]).join(", ")}` : "text scene",
        `layout ${s.variant + 1}${s.frame ? ", " + s.frame + " frame" : ""}`, s.transition ? `${sbNice(s.transition)} in` : ""].filter(Boolean).join(" · "))));
  }
  setTimeout(sbPosters, 0);
  return h("div", {}, sbReel(), h("div", { class: "sbgrid" + (sbVert() ? " vert" : "") }, out));
}

function sbOpenScene(sid) {
  sbLiveStop(); sbFlush(); sbSel = sid; sbPath = null; sbUndo = []; sbRedo = []; sbView = "current"; sbOrig = new Map();
  const st = sb.state[sid] || {}; const e = ((st.edits || {})[String(st.current || 0)]) || {};
  sbEdit = { els: JSON.parse(JSON.stringify(e.els || {})), bg: e.bg };
  showStoryboard(false);
}

// ------------------------------------------------------------------ editor: the scene's own DOM
const sbWin = () => sbFrameEl && sbFrameEl.contentWindow, sbDoc = () => sbFrameEl && sbFrameEl.contentDocument;
function sbElFor(path) {
  const w = sbWin(); if (!w || !w.SB) return null;
  const [head, ...idx] = path.split("/"); let e = sbDoc().getElementById(`${w.SB.hid}-${head}`);
  for (const k of idx) { if (!e) return null; e = e.children[+k]; }
  return e || null;
}
function sbPathOf(el) {
  const hid = sbWin().SB.hid, stage = sbDoc().getElementById(hid + "-stage");
  if (!el || !stage || !stage.contains(el) || el === stage) return null;
  const svg = el.closest("svg"); if (svg && svg !== el) el = svg;                 // parts of a drawing: the drawing
  const idx = []; let e = el;
  while (e && !(e.id && e.id.startsWith(hid + "-"))) { const p = e.parentElement; if (!p) return null; idx.unshift([...p.children].indexOf(e)); e = p; }
  if (!e) return null;
  const head = e.id.slice(hid.length + 1);
  if (SB_WRAPPERS.includes(head) && !idx.length) return null;                     // the scene's own layers
  if (idx.length > 10) return sbPathOf(el.parentElement);
  return [head, ...idx].join("/");
}
function sbSelector(hid, path) { const [head, ...idx] = path.split("/"); return `#${hid}-${head}` + idx.map(k => ` > :nth-child(${+k + 1})`).join(""); }
function sbCss() {                                    // the same block storyboard.edit_blocks writes into the render
  const { hid, W, H } = sbWin().SB, out = [];
  if (sbEdit.bg) out.push(`#${hid}-stage { background: ${sbEdit.bg} !important; }`);
  for (const [path, e] of Object.entries(sbEdit.els)) {
    const d = [];
    if ("x" in e) { const dx = e.x * W, dy = e.y * H, b = e.base;
      if (e.mode === "abs") d.push(`margin-left:${b[0] + dx}px`, `margin-top:${b[1] + dy}px`, `margin-right:${b[2] - dx}px`, `margin-bottom:${b[3] - dy}px`);
      else d.push("position:relative", `left:${b[0] + dx}px`, `top:${b[1] + dy}px`); }
    if ("zoom" in e) d.push(`zoom:${e.zoom}`);
    if ("fs" in e) d.push(`font-size:${e.fs * H}px`);
    if (e.color) d.push(`color:${e.color}`, `-webkit-text-fill-color:${e.color}`);
    if (e.font) d.push(`font-family:"${e.font}"`);
    if (e.align) d.push(`text-align:${e.align}`);
    if ("z" in e) d.push(`z-index:${e.z}`);
    if (e.hidden) d.push("display:none");
    if (d.length) out.push(`${sbSelector(hid, path)} { ${d.map(x => x + " !important").join("; ")}; }`);
  }
  return out.join("\n");
}
function sbApply() {
  const doc = sbDoc(); if (!doc || !sbWin().SB) return;
  let st = doc.getElementById("sb-live"); if (!st) { st = doc.createElement("style"); st.id = "sb-live"; doc.head.append(st); }
  st.textContent = sbCss();
  for (const [path, orig] of sbOrig) { const el = sbElFor(path); const e = sbEdit.els[path] || {};        // text back to generated, then the edit
    if (el && orig.text !== undefined) el.textContent = "text" in e ? e.text : orig.text; }
  for (const [path, e] of Object.entries(sbEdit.els)) if ("text" in e) { const el = sbElFor(path);
    if (el) { if (!sbOrig.has(path)) sbOrig.set(path, { text: el.textContent }); el.textContent = e.text; } }
  sbBox();
}
function sbBox() {
  const doc = sbDoc(); if (!doc) return;
  let box = doc.getElementById("sb-box");
  if (!box) { box = doc.createElement("div"); box.id = "sb-box";
    // the scene page has none of our CSS variables: take the app's accent colours from this page's tokens
    const tok = getComputedStyle(document.documentElement), acc = tok.getPropertyValue("--accent").trim(), on = tok.getPropertyValue("--on-media").trim();
    box.style.cssText = `position:fixed;z-index:2147483647;pointer-events:none;outline:4px solid ${acc};outline-offset:2px;display:none`;
    const hd = doc.createElement("div"); hd.id = "sb-handle";
    hd.style.cssText = `position:absolute;right:-22px;bottom:-22px;width:36px;height:36px;background:${acc};border:4px solid ${on};border-radius:50%;pointer-events:auto;cursor:nwse-resize`;
    box.append(hd); doc.body.append(box); }
  const el = sbPath && sbView === "current" ? sbElFor(sbPath) : null;
  if (!el) { box.style.display = "none"; return; }
  const r = el.getBoundingClientRect();
  Object.assign(box.style, { display: "block", left: r.left + "px", top: r.top + "px", width: r.width + "px", height: r.height + "px" });
}
function sbSnap() { sbUndo.push(JSON.stringify(sbEdit)); if (sbUndo.length > 100) sbUndo.shift(); sbRedo = []; }
function sbTouch(redraw = true) {                     // after any change: show it, save it soon
  sbApply(); clearTimeout(sbSaveTimer); sbSaveTimer = setTimeout(sbFlush, 600);
  const s = $("#sbsaved"); if (s) s.textContent = "Saving…";
  if (redraw) sbProps();
}
async function sbFlush() {
  if (!sbSaveTimer) return; clearTimeout(sbSaveTimer); sbSaveTimer = null;
  const sid = sbSel; if (!sid) return;
  try { const r = await api(`/api/jobs/${current}/storyboard/scene/${sid}`, { method: "PUT", body: JSON.stringify(sbEdit) });
    sb.state[sid] = r.scene; const row = sbScene(sid); if (row) { row.edited = Object.keys(sbEdit.els).length > 0 || !!sbEdit.bg; row.stale = false; }
    sbStamp = Date.now(); const s = $("#sbsaved"); if (s) s.textContent = "All changes saved";
  } catch (e) { toast("Not saved: " + e.message); const s = $("#sbsaved"); if (s) s.textContent = "NOT saved: " + e.message; }
}
function sbHistory(from, to) { if (!from.length) return; to.push(JSON.stringify(sbEdit)); sbEdit = JSON.parse(from.pop()); if (sbPath && !sbElFor(sbPath)) sbPath = null; sbTouch(); }
function sbEnsureMove(path) {                         // first move of an element: how it is positioned + its start values
  const e = sbEdit.els[path] || (sbEdit.els[path] = {});
  if ("x" in e) return e;
  const cs = sbWin().getComputedStyle(sbElFor(path)), f = (v) => parseFloat(v) || 0;
  if (cs.position === "absolute" || cs.position === "fixed") { e.mode = "abs"; e.base = [f(cs.marginLeft), f(cs.marginTop), f(cs.marginRight), f(cs.marginBottom)]; }
  else { e.mode = "rel"; e.base = cs.position === "relative" ? [f(cs.left), f(cs.top), 0, 0] : [0, 0, 0, 0]; }
  e.x = 0; e.y = 0; return e;
}
function sbProbe(path) {                              // screen px per px of offset (camera scale, zoom, the element's own scale)
  const e = sbEnsureMove(path), el = sbElFor(path), { W, H } = sbWin().SB, r0 = el.getBoundingClientRect(), x0 = e.x, y0 = e.y;
  e.x = x0 + 20 / W; e.y = y0 + 20 / H; sbApply(); const r1 = el.getBoundingClientRect(); e.x = x0; e.y = y0; sbApply();
  const kx = (r1.left - r0.left) / 20, ky = (r1.top - r0.top) / 20;
  return { kx: Math.abs(kx) > 0.05 ? kx : 1, ky: Math.abs(ky) > 0.05 ? ky : 1 };
}
function sbClean(path) { const e = sbEdit.els[path]; if (e && !Object.keys(e).length) delete sbEdit.els[path]; }

function sbWire() {                                   // the iframe finished loading: select, drag, resize, keys
  const doc = sbDoc(), win = sbWin(); if (!doc || !win.SB) return;
  sbOrig = new Map(); sbApply();
  if (sbView !== "current") return;
  doc.addEventListener("mousedown", (ev) => {
    ev.preventDefault(); win.focus();
    const { W, H } = win.SB;
    if (ev.target.id === "sb-handle" && sbPath) {
      sbSnap(); const k = sbProbe(sbPath), e = sbEdit.els[sbPath], r = sbElFor(sbPath).getBoundingClientRect();
      sbDrag = { kind: "size", sx: ev.clientX, r, k, z0: e.zoom || 1, x0: e.x, y0: e.y }; return; }
    let path = sbPathOf(ev.target);
    const cur = sbPath && sbElFor(sbPath);
    if (cur && cur.contains(ev.target) && !ev.detail || (cur && cur.contains(ev.target) && ev.detail < 2)) path = sbPath;   // drag what is selected; double-click goes deeper
    sbPath = path; sbBox(); sbProps();
    if (!path) return;
    sbSnap(); const k = sbProbe(path), e = sbEdit.els[path];
    sbDrag = { kind: "move", sx: ev.clientX, sy: ev.clientY, k, x0: e.x, y0: e.y, moved: false };
  }, true);
  let last = null, raf = 0;                            // at most one layout + restyle per screen frame while dragging
  doc.addEventListener("mousemove", (ev) => {
    if (!sbDrag) return; last = ev;
    if (!raf) raf = win.requestAnimationFrame(() => { raf = 0; if (last) sbMove(last); });
  }, true);
  const sbMove = (ev) => {
    if (!sbDrag || !sbPath) return; const { W, H } = win.SB, e = sbEdit.els[sbPath]; if (!e) return;
    if (sbDrag.kind === "move") { const dx = ev.clientX - sbDrag.sx, dy = ev.clientY - sbDrag.sy;
      if (!sbDrag.moved && Math.abs(dx) + Math.abs(dy) < 4) return; sbDrag.moved = true;
      e.x = sbDrag.x0 + dx / sbDrag.k.kx / W; e.y = sbDrag.y0 + dy / sbDrag.k.ky / H; sbApply();
    } else { const f = Math.max(0.1, (sbDrag.r.width + (ev.clientX - sbDrag.sx)) / sbDrag.r.width);
      e.zoom = +(sbDrag.z0 * f).toFixed(4); e.x = sbDrag.x0; e.y = sbDrag.y0; sbApply();
      const r = sbElFor(sbPath).getBoundingClientRect(), kz = e.zoom / sbDrag.z0;                 // keep the top-left corner where it was
      e.x += (sbDrag.r.left - r.left) / (sbDrag.k.kx * kz) / W; e.y += (sbDrag.r.top - r.top) / (sbDrag.k.ky * kz) / H; sbApply(); sbDrag.moved = true; }
  };
  const up = () => { if (!sbDrag) return; if (last) { sbMove(last); last = null; } const moved = sbDrag.moved; sbDrag = null;
    if (!moved) { sbUndo.pop(); const e = sbEdit.els[sbPath]; if (e && e.x === 0 && e.y === 0 && Object.keys(e).length === 4) delete sbEdit.els[sbPath]; sbApply(); return; }
    sbTouch(); };
  doc.addEventListener("mouseup", up, true); doc.addEventListener("mouseleave", up, true);
  doc.addEventListener("dragstart", (ev) => ev.preventDefault(), true);       // pictures: our drag, not the browser's
  doc.addEventListener("keydown", sbKey, true);
}
function sbKey(ev) {
  if (!sbOpen || !sbSel || sbView !== "current") return;
  const tag = (ev.target.tagName || "").toLowerCase(); if (["input", "textarea", "select"].includes(tag)) return;
  const mod = ev.metaKey || ev.ctrlKey;
  if (mod && ev.key.toLowerCase() === "z") { ev.preventDefault(); if (ev.shiftKey) sbHistory(sbRedo, sbUndo); else sbHistory(sbUndo, sbRedo); return; }
  if (!sbPath) return;
  const step = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] }[ev.key];
  if (step) { ev.preventDefault(); sbSnap(); const k = sbProbe(sbPath), e = sbEdit.els[sbPath], { W, H } = sbWin().SB, n = ev.shiftKey ? 10 : 1;
    e.x += step[0] * n / Math.abs(k.kx) / W; e.y += step[1] * n / Math.abs(k.ky) / H; sbTouch(false); }
  else if (ev.key === "Escape") { ev.preventDefault(); const el = sbElFor(sbPath); sbPath = el ? sbPathOf(el.parentElement) : null; sbBox(); sbProps(); }
  else if (ev.key === "Delete" || ev.key === "Backspace") { ev.preventDefault(); sbSnap(); (sbEdit.els[sbPath] || (sbEdit.els[sbPath] = {})).hidden = true; sbPath = null; sbTouch(); }
}
document.addEventListener("keydown", sbKey);

// ------------------------------------------------------------------ editor: panels
function sbSet(key, value) {                          // one property of the selected element (undefined = back to generated)
  if (!sbPath) return; sbSnap(); const e = sbEdit.els[sbPath] || (sbEdit.els[sbPath] = {});
  if (value === undefined || value === "" || value === null) delete e[key]; else e[key] = value;
  if (key === "text" && value === undefined) { const o = sbOrig.get(sbPath), el = sbElFor(sbPath); if (o && el) el.textContent = o.text; }
  sbClean(sbPath); sbTouch(key !== "text" && key !== "fs" && key !== "zoom" && key !== "color");
}
function sbProps() {
  if (sbPath && sbTab !== "element" && $("#sbside")) { sbTab = "element"; sbDrawSide(); return; }
  const box = $("#sbprops"); if (!box) return;
  const s = sbScene(sbSel), win = sbWin();
  if (sbView !== "current") { sbFill(box, h("p", { class: "hint" }, "This is the new version. Accept it to edit it.")); return; }
  const scene = [h("h4", {}, "Scene"),
    h("label", { class: "sbrow" }, "Background", h("input", { type: "color", value: sbEdit.bg || "#000000", oninput: (e) => { sbSnap(); sbEdit.bg = e.target.value; sbTouch(false); } }),
      sbEdit.bg ? h("button", { class: "btn small", onclick: () => { sbSnap(); delete sbEdit.bg; sbTouch(); } }, "Generated") : null),
    h("div", { class: "row" }, h("button", { class: "btn small", disabled: !Object.keys(sbEdit.els).length && !sbEdit.bg,
      onclick: () => { if (!confirm("Remove every manual edit of this scene?")) return; sbSnap(); sbEdit = { els: {} }; sbPath = null; sbTouch(); } }, "Reset the whole scene"))];
  const el = sbPath && win && win.SB ? sbElFor(sbPath) : null;
  if (!el) { sbFill(box, h("p", { class: "hint", style: "margin-top:0" }, "Click something in the scene to select it. Drag to move, drag the round handle to resize, arrow keys nudge (Shift = 10), "
      + "double-click goes inside a group, Esc selects the group around it, ⌘Z / ⇧⌘Z undo and redo."), ...scene); return; }
  const e = sbEdit.els[sbPath] || {}, cs = win.getComputedStyle(el), H = win.SB.H;
  const isText = !el.children.length && el.textContent.trim().length > 0 && !["IMG", "svg"].includes(el.tagName);
  const hasText = el.textContent.trim().length > 0;
  const hex = (c) => { const m = (c || "").match(/\d+/g); return m ? "#" + m.slice(0, 3).map(v => (+v).toString(16).padStart(2, "0")).join("") : "#000000"; };
  const zNow = "z" in e ? e.z : (parseInt(cs.zIndex) || 0);
  const kids = [h("h4", {}, isText ? "Text" : el.tagName === "IMG" ? "Picture" : "Element", h("span", { class: "hint", style: "font-weight:400" }, " " + sbPath)),
    isText ? h("textarea", { class: "inp", rows: "2", oninput: (ev) => sbSet("text", ev.target.value) }, "text" in e ? e.text : el.textContent) : null,
    isText && "text" in e ? h("button", { class: "btn small", onclick: () => sbSet("text", undefined) }, "Generated text") : null,
    h("label", { class: "sbrow" }, "Size %", h("input", { class: "inp", type: "number", min: "10", max: "800", step: "5", value: Math.round((e.zoom || 1) * 100),
      onchange: (ev) => sbSet("zoom", Math.max(0.1, Math.min(8, (+ev.target.value || 100) / 100)) === 1 ? undefined : (+ev.target.value) / 100) })),
    hasText ? h("label", { class: "sbrow" }, "Font size", h("input", { class: "inp", type: "number", min: "8", max: "900", value: Math.round(parseFloat(cs.fontSize) / (parseFloat(cs.zoom) || 1)),
      onchange: (ev) => sbSet("fs", +ev.target.value > 0 ? +ev.target.value / H : undefined) }), h("span", { class: "hint" }, "px")) : null,
    hasText ? h("label", { class: "sbrow" }, "Font", (() => { const sel = h("select", { class: "inp", onchange: (ev) => sbSet("font", ev.target.value || undefined) },
      h("option", { value: "" }, "Generated"), sb.fonts.map(f => h("option", { value: f }, f))); sel.value = e.font || ""; return sel; })()) : null,
    hasText ? h("label", { class: "sbrow" }, "Colour", h("input", { type: "color", value: e.color || hex(cs.color), oninput: (ev) => sbSet("color", ev.target.value) }),
      e.color ? h("button", { class: "btn small", onclick: () => sbSet("color", undefined) }, "Generated") : null) : null,
    hasText ? h("div", { class: "sbrow" }, "Align", ["left", "center", "right"].map(a => h("button", { class: "btn small" + (e.align === a ? " primary" : ""),
      onclick: () => sbSet("align", e.align === a ? undefined : a) }, a))) : null,
    h("div", { class: "sbrow" }, "Layer", h("button", { class: "btn small", onclick: () => sbSet("z", zNow + 1) }, "Forward"), h("button", { class: "btn small", onclick: () => sbSet("z", zNow - 1) }, "Back"),
      h("button", { class: "btn small", onclick: () => sbSet("z", 9999) }, "Front"), "z" in e ? h("span", { class: "hint" }, String(e.z)) : null),
    h("div", { class: "row" }, h("button", { class: "btn small", onclick: () => { const el2 = sbElFor(sbPath); sbPath = sbPathOf(el2.parentElement); sbBox(); sbProps(); } }, "Select group"),
      h("button", { class: "btn small", onclick: () => { sbSet("hidden", true); sbPath = null; sbBox(); sbProps(); } }, "Hide"),
      h("button", { class: "btn small", disabled: !sbEdit.els[sbPath], title: "Back to how this element was generated",
        onclick: () => { sbSnap(); const o = sbOrig.get(sbPath), el2 = sbElFor(sbPath); if (o && el2) el2.textContent = o.text; delete sbEdit.els[sbPath]; sbTouch(); } }, "Reset element"))];
  const hidden = Object.entries(sbEdit.els).filter(([, v]) => v.hidden).map(([p]) => h("button", { class: "btn small", onclick: () => { sbSnap(); delete sbEdit.els[p].hidden; sbClean(p); sbTouch(); } }, "Show " + p));
  sbFill(box, ...kids, hidden.length ? h("div", { class: "row", style: "margin-top:8px" }, hidden) : null, ...scene);
}

function sbRegenPanel(s) {
  const st = sb.state[s.sid] || {}, busy = sbBusy();
  const what = h("select", { class: "inp" }, h("option", { value: "scene" }, "The whole scene (another scene type)"), h("option", { value: "layout" }, "Same type, another layout"),
    h("option", { value: "icon" }, "Only the picture / illustration"));
  const type = h("select", { class: "inp" }, h("option", { value: "" }, "Any type that fits the line"), sb.types.map(t => h("option", { value: t }, t.replace(/_/g, " "))));
  const query = h("input", { class: "inp", placeholder: "Picture you want, e.g. realistic microchip (optional)" });
  what.onchange = () => { type.style.display = what.value === "scene" ? "" : "none"; query.style.display = what.value === "layout" ? "none" : ""; };
  const run = async (ev) => { await sbFlush(); ev.target.disabled = true; ev.target.textContent = "Regenerating scene " + s.n + "…";
    try { sb = await api(`/api/jobs/${current}/storyboard/scene/${s.sid}/regenerate`, { method: "POST", body: JSON.stringify({ what: what.value, type: type.value, query: query.value }) });
      sbStamp = Date.now(); sbView = "pending"; sbPath = null; showStoryboard(false); } catch (e) { toast(e.message); ev.target.disabled = false; ev.target.textContent = "Regenerate this scene"; } };
  const decide = async (action, n) => { await sbFlush();
    try { sb = await api(`/api/jobs/${current}/storyboard/scene/${s.sid}/version`, { method: "POST", body: JSON.stringify({ action, n }) });
      sbStamp = Date.now(); toast(action === "accept" ? "New version accepted" : action === "reject" ? "New version discarded" : `Version ${n} restored`); sbOpenScene(s.sid); } catch (e) { toast(e.message); } };
  const pending = s.pending != null ? h("div", { class: "banner warn", style: "margin:0 0 10px" }, h("b", {}, `Version ${s.pending} is waiting.`), " Only this scene was regenerated. ",
    h("div", { class: "row", style: "margin-top:8px" },
      h("button", { class: "btn small" + (sbView === "pending" ? " primary" : ""), onclick: () => { sbView = "pending"; sbPath = null; showStoryboard(false); } }, "Show new"),
      h("button", { class: "btn small" + (sbView === "current" ? " primary" : ""), onclick: () => { sbView = "current"; showStoryboard(false); } }, "Show current"),
      h("button", { class: "btn small", onclick: () => decide("accept") }, "Accept"), h("button", { class: "btn small", onclick: () => decide("reject") }, "Reject"))) : null;
  const versions = (st.versions || []).filter(v => v.n !== s.pending);
  return h("div", {}, h("h4", {}, "Regenerate"), pending,
    s.pending == null ? h("div", { class: "sbcol" }, what, type, query,
      h("button", { class: "btn small primary", disabled: busy, onclick: run }, "Regenerate this scene"),
      h("p", { class: "hint", style: "margin:0" }, "Uses this scene's line, the video's theme and the same length. The other scenes are not touched; the current version is kept until you accept the new one.")) : null,
    versions.length ? h("div", { style: "margin-top:12px" }, h("h4", {}, "Versions"), versions.map(v => h("div", { class: "sbrow" },
      h("span", {}, `v${v.n} · ${v.source} · ${v.template.replace(/_/g, " ")}` + (v.note ? ` (${v.note})` : "")), h("div", { class: "spacer" }),
      v.n === (st.current || 0) ? h("span", { class: "chip ok" }, "in use") : h("button", { class: "btn small", onclick: () => decide("restore", v.n) }, "Restore")))) : null);
}

// ------------------------------------------------------------------ editor: the scene's and the cut's own options
// Every choice the planner made for this scene, changeable by hand (storyboard.save_opts on the server). A change
// rebuilds the scenes right away (voice + plan cached, ~2 s); scenes nobody touched stay exactly as they were.
async function sbSetOpt(s, patch) {
  if (sbApplying) return;
  await sbFlush();
  const cur = Object.assign({}, (sb.state[s.sid] || {}).opts || {});
  for (const [k, v] of Object.entries(patch)) { if (v === undefined || v === null) delete cur[k]; else cur[k] = v; }
  if (!("layout" in cur)) delete cur.template;
  sbApplying = true; const note = $("#sbapplying"); if (note) note.hidden = false;
  try { sb = await api(`/api/jobs/${current}/storyboard/scene/${s.sid}/options`, { method: "PUT", body: JSON.stringify(cur) });
    sbStamp = Date.now(); toast(`Scene ${s.n} updated`); }
  catch (e) { toast(e.message); }
  finally { sbApplying = false; }
  sbOpenScene(s.sid);
}
function sbChoice(s, key, values, opts = {}) {
  const o = (sb.state[s.sid] || {}).opts || {}, set = o[key], planned = s[key];
  const label = opts.label || sbNice;
  return h("div", { class: "sbopts", role: "group", "aria-label": opts.name || key },
    opts.noAuto ? null : h("button", { class: "sbopt" + (set === undefined ? " on" : ""), disabled: opts.disabled || sbApplying,
      title: planned ? `Automatic: ${sbNice(planned)}` : "Automatic", onclick: () => set !== undefined && sbSetOpt(s, { [key]: undefined }) },
      planned && set === undefined && opts.showPlanned !== false ? `Auto (${label(planned)})` : "Auto"),
    values.map(v => h("button", { class: "sbopt" + (set === v ? " on" : "") + (planned === v && set === undefined ? " plan" : ""), disabled: opts.disabled || sbApplying,
      title: opts.title ? opts.title(v) : sbNice(v), onclick: () => set !== v && sbSetOpt(s, { [key]: v }) }, opts.render ? opts.render(v) : label(v))));
}
function sbScenePane(s) {
  const O = sb.options || {}, o = (sb.state[s.sid] || {}).opts || {}, pinned = (s.current || 0) > 0;
  const lays = (O.layouts || {})[s.template] || [];
  const layVal = o.template === s.template && "layout" in o ? o.layout : undefined;
  const colours = O.palette_colours || {}, vid = O.video_palettes || [];
  const pals = [...vid, ...(O.palette || []).filter(p => !vid.includes(p))];
  const swatch = (p) => [h("i", { style: `background:${(colours[p] || [])[0]};border-color:${(colours[p] || [])[2]}` }), sbNice(p)];
  const lockNote = pinned ? h("p", { class: "sbnote" }, `This scene uses regenerated version ${s.current}, which keeps its own layout, colours and text entrance. Restore version 0 under Versions to change them here, or regenerate it.`) : null;
  return h("div", { class: "sbpane" },
    h("h4", {}, `Layout of this ${sbNice(s.template)} scene`),
    lays.length ? h("div", { class: "sbopts" },
      h("button", { class: "sbopt" + (layVal === undefined ? " on" : ""), disabled: pinned || sbApplying, onclick: () => layVal !== undefined && sbSetOpt(s, { layout: undefined }) }, "Auto"),
      lays.map(l => h("button", { class: "sbopt" + (layVal === l.n ? " on" : "") + (s.variant === l.n && layVal === undefined ? " plan" : ""), disabled: pinned || sbApplying,
        title: `Arrangement ${l.arrangement}${l.frame ? ", " + l.frame + " frame" : ", no frame"}`,
        onclick: () => layVal !== l.n && sbSetOpt(s, { layout: l.n, template: s.template }) }, `${l.arrangement}${l.frame ? " · " + l.frame : ""}`)))
      : h("p", { class: "sbnote" }, "This scene type has one layout."),
    s.edited && lays.length ? h("p", { class: "sbnote" }, "Your manual edits belong to the current layout; on another layout they are kept but not applied.") : null,
    h("h4", {}, "Colours"), sbChoice(s, "palette", vid.length ? vid : pals, { disabled: pinned, render: swatch, name: "palette" }),
    vid.length ? h("details", { style: "margin-top:8px" }, h("summary", { class: "hint", style: "font-weight:500" }, "Colours of other formats"),
      sbChoice(s, "palette", pals.filter(p => !vid.includes(p)), { disabled: pinned, render: swatch, name: "other palettes", noAuto: true })) : null,
    SB_TEXT_TYPES.includes(s.template) ? [h("h4", {}, "How the words come in"), sbChoice(s, "text_entrance", O.text_entrance || [], { disabled: pinned, showPlanned: false })] : null,
    lockNote, h("hr", {}), sbRegenPanel(s));
}
function sbCutPane(s) {
  const O = sb.options || {}, o = (sb.state[s.sid] || {}).opts || {};
  const first = s.n === 1;
  const sw = (key, text) => h("label", { class: "sbswitch" }, h("input", { type: "checkbox", checked: o[key] !== false, disabled: sbApplying,
    onchange: (e) => sbSetOpt(s, { [key]: e.target.checked ? undefined : false }) }), text);
  return h("div", { class: "sbpane" },
    h("h4", {}, first ? "Cut into this scene" : `Cut from scene ${s.n - 1} into this one`),
    first ? h("p", { class: "sbnote" }, "The first scene opens the video, so it has no cut in.") : sbChoice(s, "transition", O.transition || [], { name: "transition" }),
    h("h4", {}, "Camera move"), sbChoice(s, "camera", O.camera || [], { name: "camera", label: (v) => v === "flat" ? "still" : sbNice(v) }),
    h("h4", {}, "Scene entrance"), sbChoice(s, "entrance", O.entrance || [], { name: "entrance" }),
    h("h4", {}, "Sound"),
    first ? null : sw("cut_sfx", "Whoosh on the cut"),
    sw("scene_sfx", `Sound effects inside the scene${s.sfx ? ` (${s.sfx})` : ""}`),
    h("p", { class: "sbnote" }, "Changes rebuild the scenes in a couple of seconds. The next draft or final re-renders only the scenes that changed."));
}
function sbDrawSide() {
  const side = $("#sbside"); if (!side) return;
  const s = sbScene(sbSel); if (!s) return;
  const tabs = [["element", "Element"], ["scene", "Scene"], ["cut", "Cut + camera"]];
  sbFill(side, h("div", { class: "sbtabs", role: "tablist" }, tabs.map(([k, t]) => h("button", { class: sbTab === k ? "on" : "", role: "tab", "aria-selected": String(sbTab === k),
      onclick: () => { sbTab = k; sbDrawSide(); } }, t))),
    h("div", { class: "sbpane", id: "sbapplying", hidden: !sbApplying, style: "padding-bottom:0" }, h("span", { class: "chip info" }, "Rebuilding the scene…")),
    sbTab === "element" ? h("div", { class: "sbpane", id: "sbprops" }) : sbTab === "scene" ? sbScenePane(s) : sbCutPane(s));
  if (sbTab === "element") sbProps();
}

function sbEditor() {
  const s = sbScene(sbSel), [W, H] = sb.size, busy = sbBusy();
  const avail = ($("#main").clientWidth || 1100) - (window.innerWidth > 1180 ? 210 + 340 + 70 : 64);
  const width = Math.max(200, Math.min(sbVert() ? 420 : 980, Math.round(avail))), k = width / W;
  const pendingView = sbView === "pending" && s.pending != null;
  sbFrameEl = h("iframe", { src: sbUrl(s, pendingView ? `&v=${s.pending}` : "&raw=1"), title: `Scene ${s.n}`, style: `width:${W}px;height:${H}px;transform:scale(${k});` });
  const tc = h("span", { class: "tc" }, "0.00 s");
  const showT = (t) => { tc.textContent = `${(+t).toFixed(2)} / ${(s.dur + s.ov).toFixed(1)} s`; };
  sbFrameEl.addEventListener("load", () => { const wait = () => { const w = sbWin(); if (w && w.SB && w.SB.ready) { sbWire(); sbProps(); scrub.max = w.SB.length; scrub.value = w.SB.still; showT(w.SB.still); } else setTimeout(wait, 50); }; wait(); });
  const scrub = h("input", { type: "range", min: "0", max: String(s.dur + s.ov), step: "0.01", "aria-label": "Scene time",
    oninput: (e) => { const w = sbWin(); if (w && w.SB) { w.SB.seek(+e.target.value); showT(e.target.value); sbBox(); } } });
  const playBtn = h("button", { class: "btn small primary", "aria-label": "Play the scene" }, "Play");
  playBtn.onclick = () => { const w = sbWin(); if (!w || !w.SB || !w.SB.tl) return;
    if (!w.SB.tl.paused() && w.SB.tl.progress() < 1) { w.SB.tl.pause(); playBtn.textContent = "Play"; return; }
    w.SB.tl.restart(); playBtn.textContent = "Pause";
    const tick = () => { if (!sbFrameEl.isConnected) return; const t = w.SB.tl.time(); scrub.value = t; showT(t); sbBox();
      if (!w.SB.tl.paused() && w.SB.tl.progress() < 1) requestAnimationFrame(tick); else playBtn.textContent = "Play"; }; tick(); };
  const list = h("div", { class: "sblist" }, sb.scenes.map(x => h("div", { class: "sbitem" + (x.sid === s.sid ? " on" : ""), role: "button", tabindex: "0",
    "aria-label": `Scene ${x.n}`, onclick: () => sbOpenScene(x.sid), onkeydown: (e) => { if (e.key === "Enter") sbOpenScene(x.sid); } },
    sbShot(x, { badges: true }),
    h("div", {}, h("span", { class: "chip", style: "font-size:11px" }, sbNice(x.template)),
      x.edited || x.regenerated || x.pending != null || (sb.state[x.sid] || {}).opts ? h("span", { class: "chip ok", style: "font-size:11px;margin-left:4px" }, x.pending != null ? "new" : "changed") : null,
      h("div", { class: "sbtext" }, x.text)))));
  setTimeout(() => { const on = list.querySelector(".on"); if (on) on.scrollIntoView({ block: "nearest", inline: "nearest" }); sbPosters(); }, 0);
  const prev = sb.scenes[s.n - 2], next = sb.scenes[s.n];
  const side = h("div", { class: "sbside", id: "sbside" });
  setTimeout(sbDrawSide, 0);
  return h("div", {}, sbReel(), h("div", { class: "sbedit" },
    list,
    h("div", { class: "sbcentre" },
      h("div", { class: "sbstage" },
        h("div", { class: "row", style: "margin-bottom:10px" }, h("b", { class: "sbtitle" }, `Scene ${s.n}`), h("span", { class: "chip" }, sbNice(s.template)),
          h("span", { class: "hint" }, `${ts(s.start)} · ${s.dur.toFixed(1)} s`), ...sbFlags(s), h("div", { class: "spacer" }),
          h("button", { class: "btn small", disabled: !prev, title: "Previous scene", "aria-label": "Previous scene", onclick: () => prev && sbOpenScene(prev.sid) }, "‹"),
          h("button", { class: "btn small", disabled: !next, title: "Next scene", "aria-label": "Next scene", onclick: () => next && sbOpenScene(next.sid) }, "›"),
          h("button", { class: "btn small", title: "Undo (⌘Z)", onclick: () => sbHistory(sbUndo, sbRedo) }, "Undo"), h("button", { class: "btn small", title: "Redo (⇧⌘Z)", onclick: () => sbHistory(sbRedo, sbUndo) }, "Redo"),
          h("span", { class: "hint", id: "sbsaved" }, busy ? "Rendering: edits are locked" : "All changes saved")),
        s.stale ? h("div", { class: "banner warn", style: "margin:0 0 10px" }, "This scene's edits were made on another layout and are NOT in the video. They are shown here; change anything (or press Undo then Redo) to apply them to this layout, or reset the scene.") : null,
        h("div", { class: "sbframe big" + (pendingView ? " pending" : ""), style: `width:${width}px;height:${Math.round(H * k)}px;margin:0 auto` }, sbFrameEl),
        h("div", { class: "sbtransport" }, playBtn,
          h("button", { class: "btn small", onclick: () => { const w = sbWin(); if (w && w.SB) { w.SB.tl && w.SB.tl.pause(); playBtn.textContent = "Play"; w.SB.seek(w.SB.still); scrub.value = w.SB.still; showT(w.SB.still); sbBox(); } } }, "Still"),
          scrub, tc),
        h("p", { class: "sbtext", style: "margin:12px 0 0" }, h("b", { style: "color:var(--ink)" }, "Narration: "), s.text))),
    side));
}

// ------------------------------------------------------------------ shot storyboard (every other rendering method)
// AI images, Blocky 3D, 3D explainer, Neon motion: one card per shot tag of script.md (pipeline/shot_storyboard.py).
// An edit rewrites that shot's lines of the script (kept only when Check still passes); AI-image shots can also make
// another version of their picture (| seed=N), which waits for Accept / Reject.
let shOpen = false, sh = null, shSel = null, shPic = Date.now();
function openShots() { shOpen = true; shSel = null; showShots(true); }
function closeShots() { shOpen = false; shSel = null; $("#main").classList.remove("wide"); showJob(); }
const shUrl = (s, seed) => `/api/jobs/${current}/shots/${s.i}/picture?t=${shPic}` + (seed !== undefined ? `&seed=${seed}` : "");
const shVert = () => sh.size[1] > sh.size[0];

async function showShots(reload = true) {
  const m = $("#main"); m.classList.add("wide");
  if (reload || !sh) { try { sh = await api(`/api/jobs/${current}/shots`); } catch (e) { toast(e.message); return; } }
  if (!shOpen) return;
  if (shSel !== null && !sh.shots[shSel]) shSel = null;
  fill(m, shTop(), ...(sh.busy ? [progressCard(), h("p", { class: "hint" }, "The shots come back when the render has finished.")]
    : !sh.ok ? [h("div", { class: "banner warn" }, "The script has errors; fix them in the Script tab first: " + sh.errors.map(e => `line ${e.line}: ${e.msg}`).join("; "))]
    : [shSel !== null ? shEditor(sh.shots[shSel]) : shGrid()]));
}

function shTop() {
  const n = sh.shots.length, busy = sh.busy;
  return h("div", { class: "row sbtop" },
    h("button", { class: "btn small", onclick: shSel !== null ? () => { shSel = null; showShots(false); } : closeShots }, shSel !== null ? "All shots" : "Back to the video"),
    h("h2", {}, "Storyboard"), h("span", { class: "hint" }, `${sh.label} · ${n} shots, ${ts(sh.shots.reduce((a, x) => a + x.dur, 0))}`),
    h("div", { class: "spacer" }),
    h("button", { class: "btn small", disabled: busy || !sh.ok, onclick: () => go("draft"), title: "Draft render with your changes" }, "Preview video"),
    h("button", { class: "btn small primary", disabled: busy || !sh.ok, onclick: () => go("final"),
      title: sh.method === "ai_image" ? "Unchanged AI images are reused; only new or changed pictures are made" : "" }, "Make final"));
}

function shPicture(s, seed) {
  const box = h("div", { class: "sbshot" + (shVert() ? " vert" : "") },
    h("span", { class: "num" }, String(s.i + 1)), h("span", { class: "dur" }, `${s.dur.toFixed(1)} s`));
  const img = h("img", { src: shUrl(s, seed), alt: `Shot ${s.i + 1}: ${s.narration}`, decoding: "async", loading: "lazy" });
  img.onerror = () => { img.remove(); box.classList.add("wait"); box.append(h("b", { class: "shtag" }, `[${s.type}]`)); };
  box.prepend(img);
  return box;
}

const shSummary = (s) => { const f = s.fields;
  return f.prompt || f.query || f.text || f.title || f.label || f.who || f.subject || f.kind && [f.kind, f.text || f.words].filter(Boolean).join(": ") || ""; };

function shGrid() {
  const cards = sh.shots.map(s => h("div", { class: "sbcard", role: "button", tabindex: "0", "aria-label": `Edit shot ${s.i + 1}`,
      onclick: () => { shSel = s.i; showShots(false); },
      onkeydown: (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); shSel = s.i; showShots(false); } } },
    shPicture(s),
    h("div", { class: "meta" }, h("span", { class: "chip" }, s.type), h("span", { class: "hint" }, ts(s.start) + (s.timed ? "" : " (estimate)")),
      s.pending ? h("span", { class: "chip info" }, "new picture waiting") : null, s.seed ? h("span", { class: "chip" }, `version ${s.seed}`) : null),
    h("div", { class: "sbtext" }, s.narration),
    h("div", { class: "foot" }, String(shSummary(s)).slice(0, 120))));
  return h("div", {}, h("p", { class: "hint" }, "Click a shot to change its picture, words and options. Pictures come from the last render "
      + (sh.method === "ai_image" ? "or the AI-image cache." : "(make a draft to see them).")),
    h("div", { class: "sbgrid" + (shVert() ? " vert" : "") }, cards));
}

function shEditor(s) {
  const ta = h("textarea", { class: "inp", rows: Math.min(14, s.text.split("\n").length + 2), spellcheck: "false",
    style: "width:100%;font-family:var(--mono,monospace)", "aria-label": "This shot's lines of the script" }, s.text);
  const err = h("div", { class: "banner warn", hidden: true });
  const save = async () => {
    err.hidden = true;
    try { sh = await api(`/api/jobs/${current}/shots/${s.i}`, { method: "PUT", body: JSON.stringify({ text: ta.value, old: s.text }) });
      editText = null; shPic = Date.now(); toast("Shot saved"); api("/api/jobs/" + current).then(d => { data = d; }).catch(() => {}); showShots(false); }
    catch (e) { err.textContent = e.message; err.hidden = false; }
  };
  const ver = async (body) => { try { sh = await api(`/api/jobs/${current}/shots/${s.i}/version`, { method: "POST", body: JSON.stringify(body) });
    editText = null; shPic = Date.now(); api("/api/jobs/" + current).then(d => { data = d; }).catch(() => {}); showShots(false); } catch (e) { toast(e.message); } };
  const ai = s.type === "ai" || s.type === "stock";
  const newImg = h("button", { class: "btn", disabled: sh.busy, onclick: async (e) => { e.target.disabled = true; e.target.textContent = "Making a new picture… (~25 s)";
    try { sh = await api(`/api/jobs/${current}/shots/${s.i}/new_image`, { method: "POST", body: "{}" }); shPic = Date.now(); showShots(false); }
    catch (er) { toast(er.message); e.target.disabled = false; e.target.textContent = "New picture"; } } }, "New picture");
  const fields = Object.entries(s.fields).filter(([k]) => k !== "type").map(([k, v]) =>
    h("div", { class: "row", style: "gap:8px" }, h("span", { class: "hint", style: "min-width:90px" }, sbNice(k)),
      h("span", {}, Array.isArray(v) ? v.map(x => Array.isArray(x) ? x.join(": ") : (typeof x === "object" ? JSON.stringify(x) : x)).join(", ") : String(v))));
  return h("div", { class: "row", style: "align-items:flex-start;gap:20px;flex-wrap:wrap" },
    h("div", { style: "flex:1 1 420px;min-width:0" },
      shPicture(s, s.pending || undefined),
      s.pending ? h("div", { class: "row", style: "margin-top:10px" }, h("b", {}, `New picture (version ${s.pending})`),
        h("button", { class: "btn small primary", onclick: () => ver({ action: "accept" }) }, "Accept"),
        h("button", { class: "btn small", onclick: () => ver({ action: "reject" }) }, "Reject")) : null,
      ai && (s.versions || []).length > 1 ? h("div", { style: "margin-top:12px" }, h("h3", {}, "Versions"),
        h("div", { class: "row", style: "flex-wrap:wrap;gap:8px" }, s.versions.filter(v => v.ready).map(v =>
          h("button", { class: "btn small" + (v.seed === s.seed ? " primary" : ""), title: v.seed ? `seed=${v.seed}` : "the first picture",
            onclick: () => v.seed !== s.seed && ver({ action: "use", seed: v.seed }) },
            h("img", { src: shUrl(s, v.seed), alt: `version ${v.seed}`, style: "width:96px;display:block;border-radius:6px" }),
            v.seed === s.seed ? "in use" : `use ${v.seed || "first"}`)))) : null,
      h("div", { class: "card", style: "margin-top:12px" }, h("h3", {}, "What this shot is now"), fields)),
    h("div", { style: "flex:1 1 420px;min-width:0" },
      h("h3", { style: "margin-top:0" }, `Shot ${s.i + 1} · ${ts(s.start)} · ${s.dur.toFixed(1)} s`),
      h("p", { class: "hint" }, "Change the tag (picture and its options) and the words spoken under it, then Save. "
        + "The script is checked first; nothing is saved if it gets errors. Video-wide settings (art style, camera, transitions, voice, music, captions) are in Look & sound."),
      ta, err,
      h("div", { class: "row", style: "margin-top:10px" }, h("button", { class: "btn primary", disabled: sh.busy, onclick: save }, "Save shot"),
        h("button", { class: "btn", onclick: () => { ta.value = s.text; err.hidden = true; } }, "Undo changes"), ai ? newImg : null),
      h("details", { style: "margin-top:16px" }, h("summary", {}, `Every option of ${sh.label} tags`),
        h("pre", { style: "white-space:pre-wrap;font-size:12px" }, sh.help))));
}
