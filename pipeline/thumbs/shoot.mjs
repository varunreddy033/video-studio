// Screenshots designed thumbnails (pipeline/thumbs/render.py) with the headless Chromium HyperFrames already
// installed, through puppeteer-core (a dependency of hyperframes: nothing new, no network).
//
//   node shoot.mjs <jobs.json>      jobs.json = {"chrome": "<path>", "pages": [{"html", "png", "w", "h"}]}
//
// For every page: load the local HTML, wait for the bundled fonts, run the page's own fit() (shrinks text that is
// too wide or too tall), measure every element with a data-role (box, font size, cap height of its font, overflow),
// then save a PNG. Prints one JSON line: [{"png", "ms", "boxes": [...], "error"}].
import fs from "node:fs";
import puppeteer from "puppeteer-core";

const job = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const browser = await puppeteer.launch({
  executablePath: job.chrome,
  headless: true,
  args: ["--no-sandbox", "--disable-gpu", "--font-render-hinting=none", "--hide-scrollbars", "--disable-lcd-text",
         "--force-color-profile=srgb", "--disable-features=Translate", "--no-first-run", "--disable-extensions"],
});
const out = [];
try {
  const page = await browser.newPage();
  for (const p of job.pages) {
    const t0 = Date.now();
    try {
      await page.setViewport({ width: p.w, height: p.h, deviceScaleFactor: 1 });
      await page.goto("file://" + p.html, { waitUntil: "load" });
      await page.evaluate(async () => { await document.fonts.ready; });
      const boxes = await page.evaluate(async () => {
        if (window.fitAll) window.fitAll();
        await document.fonts.ready;
        const cv = document.createElement("canvas").getContext("2d");
        return [...document.querySelectorAll("[data-role]")].map((el) => {
          const r = el.getBoundingClientRect();
          const cs = getComputedStyle(el);
          const fs = parseFloat(cs.fontSize) || 0;
          cv.font = `${cs.fontWeight} ${fs}px ${cs.fontFamily}`;
          const cap = fs ? cv.measureText("H").actualBoundingBoxAscent : 0;
          return { role: el.dataset.role, x: r.left, y: r.top, w: r.width, h: r.height, font: fs, cap,
                   family: cs.fontFamily, words: (el.dataset.words || "").length ? +el.dataset.words : null,
                   overflow: el.dataset.text ? (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1) : false,
                   text: el.dataset.text ? el.innerText.replace(/\s+/g, " ").trim() : "" };
        });
      });
      await page.screenshot({ path: p.png, type: "png", clip: { x: 0, y: 0, width: p.w, height: p.h } });
      out.push({ png: p.png, ms: Date.now() - t0, boxes });
    } catch (e) {
      out.push({ png: p.png, ms: Date.now() - t0, boxes: [], error: String(e && e.message || e) });
    }
  }
} finally {
  await browser.close();
}
process.stdout.write(JSON.stringify(out) + "\n");
