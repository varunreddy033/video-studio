// Check-page previews: one bundle + one browser, then a still of the Motion composition at each requested frame.
//   node scripts/stills.mjs <timeline.json> <public-dir> <out-dir> <frame,frame,...> [scale]
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {readFileSync} from 'node:fs';
import {bundle} from '@remotion/bundler';
import {openBrowser, renderStill, selectComposition} from '@remotion/renderer';

const [, , timelinePath, publicDir, outDir, framesArg, scaleArg] = process.argv;
const here = path.dirname(fileURLToPath(import.meta.url));
const inputProps = JSON.parse(readFileSync(timelinePath, 'utf8'));
const frames = framesArg.split(',').map(Number);
const scale = Number(scaleArg || 0.5);

const serveUrl = await bundle({entryPoint: path.join(here, '..', 'src', 'index.ts'), publicDir});
const browser = await openBrowser('chrome');
const composition = await selectComposition({serveUrl, id: 'Motion', inputProps, puppeteerInstance: browser});
let i = 0;
for (const frame of frames) {
  const output = path.join(outDir, `scene_${String(i).padStart(2, '0')}.jpg`);
  await renderStill({composition, serveUrl, output, frame, inputProps, imageFormat: 'jpeg', jpegQuality: 85,
    scale, puppeteerInstance: browser, overwrite: true});
  i++;
}
await browser.close({silent: true});
console.log(JSON.stringify({ok: true, count: i}));
