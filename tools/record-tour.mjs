// Records the captioned setup walkthrough (the Mac flow of the Setup page) as a 1080p MP4, like the home-page tour of
// the Agentic Coding with Claude workshop.
//
//   node tools/record-tour.mjs [last-scene]
//
// Writes site/video/setup.mp4 and site/video/setup-poster.jpg. Needs Google Chrome and ffmpeg (set CHROME and FFMPEG
// if they aren't at the macOS defaults). [last-scene] stops early, for a quick test.
//
// tools/tour/stage.html is a stage with a terminal, a browser frame, captions and title cards. This script serves
// it over HTTP (so the browser frame can scroll the pages it shows), drives it scene by scene through window.stage,
// and moves a drawn cursor with real mouse events. The terminal is a simplified re-creation of a Mac shell session;
// its words come from running the Setup page's commands (uv 0.13.3 is the version the page was checked with). The
// browser frame shows the real Setup page, rendered with Quarto and copied from site/_site/ at record time, and real JupyterLab 4.6
// screenshots from tools/tour/pages/ (jlab-a.png to jlab-e.png, captured with tools/shoot.mjs; see scenes.mjs).
import { spawn, spawnSync } from 'node:child_process';
import { createServer } from 'node:http';
import { cpSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { extname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ROOT = resolve(fileURLToPath(new URL('..', import.meta.url))); // not .pathname: that keeps %20 for spaces
const LAST = process.argv[2] || '';
const W = 1280;
const H = 720;
const SCALE = 1.5;
const BUILD = join(ROOT, 'build', 'tour');
const FRAMES = join(BUILD, 'frames');
const OUT = join(ROOT, 'site', 'video');
rmSync(BUILD, { recursive: true, force: true });
mkdirSync(FRAMES, { recursive: true });
mkdirSync(OUT, { recursive: true });
cpSync(join(ROOT, 'tools', 'tour'), join(BUILD, 'www'), { recursive: true });
cpSync(join(ROOT, 'site', 'images', 'lib_logo_white.png'), join(BUILD, 'www', 'logo-white.png'));

// The real Setup page, for the browser frame. Always render it fresh (only this one file), so the frame never shows a
// stale page. Quarto isn't on PATH here; RStudio ships one.
const SITE = join(ROOT, 'site', '_site');
const quarto = process.env.QUARTO || ['/Applications/RStudio.app/Contents/Resources/app/quarto/bin/quarto', 'quarto'].find((q) => q === 'quarto' || existsSync(q));
console.log('rendering site/setup.qmd with Quarto');
const render = spawnSync(quarto, ['render', 'site/setup.qmd'], { cwd: ROOT, stdio: 'inherit' });
if (render.status !== 0 || !existsSync(join(SITE, 'setup.html'))) { console.error('Quarto could not render site/setup.qmd'); process.exit(1); }
const PAGE = join(BUILD, 'www', 'pages', 'setup');
mkdirSync(PAGE, { recursive: true });
cpSync(join(SITE, 'setup.html'), join(PAGE, 'index.html'));
cpSync(join(SITE, 'site_libs'), join(PAGE, 'site_libs'), { recursive: true, filter: (src) => !src.includes('revealjs') });
cpSync(join(SITE, 'images'), join(PAGE, 'images'), { recursive: true });

// A tiny static server for the stage and the pages it shows.
const types = {
  '.html': 'text/html; charset=utf-8', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.js': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.woff': 'font/woff', '.woff2': 'font/woff2',
};
const server = createServer((req, res) => {
  const path = join(BUILD, 'www', decodeURIComponent(new URL(req.url, 'http://x').pathname));
  if (!path.startsWith(join(BUILD, 'www')) || !existsSync(path)) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'content-type': types[extname(path)] || 'application/octet-stream' });
  res.end(readFileSync(path));
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const BASE = `http://127.0.0.1:${server.address().port}`;

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const chrome = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const port = 9700 + Math.floor(Math.random() * 200);
const proc = spawn(chrome, ['--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run', '--no-default-browser-check',
  '--force-color-profile=srgb', `--user-data-dir=${mkdtempSync(join(tmpdir(), 'tour-'))}`, `--remote-debugging-port=${port}`, 'about:blank'],
{ stdio: 'ignore' });
process.on('exit', () => proc.kill());

let target;
for (let i = 0; i < 50 && !target; i++) {
  await sleep(200);
  try { target = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find((t) => t.type === 'page'); } catch {}
}
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener('open', r, { once: true }));
let id = 0;
const pending = new Map();
const frames = [];
const errors = [];
ws.addEventListener('message', (event) => {
  const msg = JSON.parse(event.data);
  if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
  if (msg.method === 'Page.screencastFrame') {
    const file = join(FRAMES, String(frames.length).padStart(6, '0') + '.jpg');
    writeFileSync(file, Buffer.from(msg.params.data, 'base64'));
    frames.push({ file, t: msg.params.metadata.timestamp });
    send('Page.screencastFrameAck', { sessionId: msg.params.sessionId });
  }
  if (msg.method === 'Runtime.exceptionThrown') errors.push(msg.params.exceptionDetails.exception?.description);
});
const send = (method, params = {}) => new Promise((res) => { const n = ++id; pending.set(n, res); ws.send(JSON.stringify({ id: n, method, params })); });
async function evaluate(expression) {
  const result = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
  if (result.result?.exceptionDetails) throw new Error(result.result.exceptionDetails.exception?.description || 'evaluate failed: ' + expression.slice(0, 80));
  return result.result?.result?.value;
}
const js = (v) => JSON.stringify(v);
const S = (code) => evaluate(`(async () => { ${code} })()`);

// Cursor: drawn into the stage. Moved with real mouse events (so hover effects fire) and placed by hand, because
// mouse events over the iframe never reach the stage's own listeners.
let mouse = { x: W * 0.62, y: H * 0.72 };
async function moveTo(x, y, ms = 700) {
  const steps = Math.max(10, Math.round(ms / 16));
  const from = { ...mouse };
  for (let i = 1; i <= steps; i++) {
    const p = i / steps;
    const e = p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;
    const px = from.x + (x - from.x) * e, py = from.y + (y - from.y) * e;
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: px, y: py });
    await send('Runtime.evaluate', { expression: `__cur(${px},${py})` });
    await sleep(ms / steps);
  }
  mouse = { x, y };
}
// A real click (or double-click) at the cursor, with a red ring so it shows up on screen.
async function click(count = 1) {
  const { x, y } = mouse;
  await evaluate(`__click(${x},${y})`);
  for (let n = 1; n <= count; n++) {
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', buttons: 1, clickCount: n });
    await sleep(70);
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', buttons: 0, clickCount: n });
    await sleep(count > 1 ? 90 : 0);
  }
}
async function hoverText(text, ms = 800, dy = 0) {
  const p = await evaluate(`stage.browser.find(${js(text)})`);
  if (!p) return false;
  await moveTo(p.x, p.y + dy, ms);
  // The page may have moved while the cursor travelled; look again and correct, so the click lands on the text.
  const q = await evaluate(`stage.browser.find(${js(text)})`);
  if (q && Math.hypot(q.x - p.x, q.y - p.y) > 2) await moveTo(q.x, q.y + dy, 200);
  return true;
}
const CURSOR = `(() => {
  const style = document.createElement('style');
  style.textContent = '#tour-cursor { position: fixed; left: 0; top: 0; z-index: 2147483647; pointer-events: none; transform: translate(-200px, -200px); } #tour-cursor svg { display: block; filter: drop-shadow(0 1px 2px rgba(0,0,0,.4)); } body.carded #tour-cursor { opacity: 0; }';
  document.head.append(style);
  const c = document.createElement('div'); c.id = 'tour-cursor';
  c.innerHTML = '<svg width="28" height="28" viewBox="0 0 24 24"><path d="M5 2.6 19.2 12.6l-6.4 1.2 3.8 7.2-2.7 1.4-3.8-7.3-4.9 4.3Z" fill="#111" stroke="#fff" stroke-width="1.5" stroke-linejoin="round"/></svg>';
  document.body.append(c);
})()`;

const scenes = (await import(pathToFileURL(join(ROOT, 'tools', 'tour', 'scenes.mjs')).href)).default({ S, js, sleep, moveTo, hoverText, evaluate, click, getMouse: () => mouse });

await send('Runtime.enable');
await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: SCALE, mobile: false });
await send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: 'light' }] });
await send('Page.navigate', { url: BASE + '/stage.html' });
for (let i = 0; i < 100; i++) { await sleep(100); if ((await evaluate('document.readyState')) === 'complete') break; }
await evaluate(CURSOR);
await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: mouse.x, y: mouse.y });
await sleep(400);
await send('Page.startScreencast', { format: 'jpeg', quality: 90, maxWidth: W * SCALE, maxHeight: H * SCALE, everyNthFrame: 1 });

let failed = null;
for (const [name, run] of scenes) {
  const started = Date.now();
  try { await run(); } catch (error) { failed = name + ': ' + error.message; break; }
  console.log('scene', name.padEnd(12), ((Date.now() - started) / 1000).toFixed(1) + 's');
  if (name === LAST) break;
}
await sleep(300);
await send('Page.stopScreencast');
await sleep(500);
ws.close();
proc.kill();
server.close();

if (failed) console.log('FAILED in scene', failed);
if (errors.length) console.log('page errors:', errors.join(' | '));
console.log('frames', frames.length);

// Constant 30 fps from timestamped frames: each frame lasts until the next one arrives.
// The first card fades in a few frames after the screencast starts; skip those frames so the video opens on the card.
const hold = frames.findIndex((frame, i) => frames[i + 1] && frames[i + 1].t - frame.t >= 1.0);
if (hold > 0 && frames[hold].t - frames[0].t < 0.5) frames.splice(0, hold);
const lines = ['ffconcat version 1.0'];
frames.forEach((frame, i) => {
  const next = frames[i + 1];
  lines.push(`file '${frame.file}'`, `duration ${(next ? next.t - frame.t : 2.5).toFixed(4)}`);
});
lines.push(`file '${frames[frames.length - 1].file}'`);
writeFileSync(join(BUILD, 'frames.ffconcat'), lines.join('\n') + '\n');
const ffmpeg = process.env.FFMPEG || '/opt/homebrew/bin/ffmpeg';
const video = join(OUT, 'setup.mp4');
// Limited (TV) range, BT.709, which is what players expect from h264 video; full-range output shows crushed blacks.
// The screencast JPEGs are full-range BT.601, so convert the matrix and range explicitly, then tag the stream.
const filter = 'fps=30,scale=1920:1080:flags=lanczos+accurate_rnd+full_chroma_int:in_range=pc:out_range=tv:in_color_matrix=bt601:out_color_matrix=bt709,format=yuv420p';
const enc = spawnSync(ffmpeg, ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', join(BUILD, 'frames.ffconcat'),
  '-vf', filter, '-c:v', 'libx264', '-preset', 'slow', '-crf', '24', '-pix_fmt', 'yuv420p',
  '-color_range', 'tv', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
  '-movflags', '+faststart', video], { stdio: 'inherit' });
console.log(enc.status === 0 ? 'video ' + video : 'ffmpeg failed');
// Poster: the title card, a moment after it fades in. Go through PNG (RGB) so the JPEG gets the right colors.
const posterPng = join(BUILD, 'poster.png');
spawnSync(ffmpeg, ['-y', '-loglevel', 'error', '-ss', '1.2', '-i', video, '-frames:v', '1', posterPng], { stdio: 'inherit' });
spawnSync(ffmpeg, ['-y', '-loglevel', 'error', '-i', posterPng, '-q:v', '3', join(OUT, 'setup-poster.jpg')], { stdio: 'inherit' });
process.exit(failed ? 1 : 0);
