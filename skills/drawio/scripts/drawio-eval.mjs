#!/usr/bin/env node
// Run JavaScript inside a live draw.io desktop window over the Chrome DevTools
// Protocol. draw.io must have been started with --remote-debugging-port (see
// drawio-start.sh). Needs Node 22+ for the built-in WebSocket.
//
//   node drawio-eval.mjs --ping                 connection + open windows
//   node drawio-eval.mjs -c 'return D.info()'   inline code
//   node drawio-eval.mjs build.js               code from a file
//   node drawio-eval.mjs --screenshot out.png   capture the window as PNG
//
// Code runs as the body of an async function with `ui` (the EditorUi/App),
// `graph`, `model`, `D` (helpers from drawio-helpers.js) and `ARGS` (extra
// command-line arguments after the file) in scope. `return` a JSON-able value
// to print it. A file may instead be an ES module whose
// `export default async function ({ ui, graph, model, D, ARGS })` is called
// with that scope — see example-architecture.mjs.
//
// Options: --port N (default $DRAWIO_PORT or 9338), --window <substring of the
// window title> to pick one of several open windows, --timeout seconds.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2);
const opts = { port: process.env.DRAWIO_PORT || '9338', window: null, timeout: 60 };
let mode = null, code = null, outFile = null;
const extra = [];

for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === '--port') opts.port = argv[++i];
  else if (a === '--window') opts.window = argv[++i];
  else if (a === '--timeout') opts.timeout = Number(argv[++i]);
  else if (a === '--ping') mode = 'ping';
  else if (a === '--screenshot') { mode = 'shot'; outFile = argv[++i]; }
  else if (a === '-c') { mode = 'eval'; code = argv[++i]; }
  else if (mode === null) { mode = 'eval'; code = fs.readFileSync(a, 'utf8'); }
  else extra.push(a);
}

function fail(msg, exitCode = 1) {
  console.log(JSON.stringify({ ok: false, error: msg }));
  process.exit(exitCode);
}

if (mode === null) fail('usage: drawio-eval.mjs [--port N] [--window T] (--ping | -c CODE | FILE [ARGS...] | --screenshot OUT.png)', 2);
if (typeof WebSocket === 'undefined') fail(`Node ${process.version} has no global WebSocket — use Node 22+`);

let pages;
try {
  const res = await fetch(`http://127.0.0.1:${opts.port}/json/list`);
  pages = (await res.json()).filter(p => p.type === 'page' && p.url.includes('index.html'));
} catch {
  fail(`nothing answers on 127.0.0.1:${opts.port} — start draw.io with scripts/drawio-start.sh`, 3);
}

const windows = pages.map(p => p.title.replace(/ - draw\.io$/, ''));
let page = pages[0];
if (opts.window) {
  page = pages.find(p => p.title.includes(opts.window));
  if (!page) fail(`no window titled like "${opts.window}"; open: ${JSON.stringify(windows)}`);
}
if (!page) fail('draw.io is running but has no editor window open');

const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = () => reject(); })
  .catch(() => fail('could not open the DevTools WebSocket'));

let nextId = 1;
const pending = new Map();
ws.onmessage = e => {
  const m = JSON.parse(e.data);
  if (pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
};
function send(method, params = {}) {
  const id = nextId++;
  ws.send(JSON.stringify({ id, method, params }));
  return new Promise(resolve => pending.set(id, resolve));
}

const timer = setTimeout(() => fail(`timed out after ${opts.timeout}s`), opts.timeout * 1000);

async function evaluate(expression) {
  const m = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  if (m.error) throw new Error(m.error.message);
  if (m.result.exceptionDetails) {
    const ex = m.result.exceptionDetails;
    throw new Error(ex.exception?.description || ex.exception?.value || ex.text);
  }
  return m.result.result.value;
}

try {
  // Install the helper library once per window (idempotent).
  const helpers = fs.readFileSync(path.join(here, 'drawio-helpers.js'), 'utf8');
  await evaluate(helpers);

  let result;
  if (mode === 'ping') {
    result = { ok: true, port: Number(opts.port), windows, active: page.title.replace(/ - draw\.io$/, ''),
      info: await evaluate('window.__drawioReady().then(() => D.info())') };
  } else if (mode === 'shot') {
    const m = await send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync(outFile, Buffer.from(m.result.data, 'base64'));
    result = { ok: true, screenshot: path.resolve(outFile) };
  } else {
    // A module-style file (`export default async function ({ D, ... }) {}`) is
    // called with the scope object; anything else is used as a function body.
    const moduleForm = /^\s*export\s+default\s+/m.test(code);
    const body = moduleForm
      ? code.replace(/^\s*export\s+default\s+/m, 'const __main = ') +
        '\nreturn await __main({ ui, graph, model, D, ARGS });'
      : code;
    const wrapped = `window.__drawioReady().then(async () => {
      const ui = D.ui, graph = D.graph, model = D.model, ARGS = ${JSON.stringify(extra)};
      ${body}
    })`;
    result = { ok: true, result: await evaluate(wrapped) ?? null };
  }
  console.log(JSON.stringify(result, null, 1));
  clearTimeout(timer);
  ws.close();
} catch (e) {
  fail(String(e.message || e).split('\n').slice(0, 6).join('\n'));
}
