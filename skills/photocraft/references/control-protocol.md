# Control protocol: headless `serve` and the desktop control port

Condensed from the vendor's `docs/control-protocol.md` (storytold/photocraft, v0.9.0),
which is not shipped with the CLI, and checked against the installed 0.16.0, which added
`doc.replaceSmartObject`.

## Contents
- [Envelope](#envelope) · [Headless serve methods](#headless-serve-methods)
- [Filesystem roots](#filesystem-roots) · [Desktop control port](#desktop-control-port)
- [Security posture](#security-posture) · [Limits and timeouts](#limits-and-timeouts)

## Envelope

One JSON object per line in each direction:

```json
{"id": 1, "method": "doc.open", "params": {"path": "/abs/in.psd"}}
{"id": 1, "ok": true, "result": {...}}
{"id": 2, "ok": false, "error": "no document open"}
```

An oversized or non-UTF-8 line gets one error reply with `id: null`. On stdio the session
keeps serving.

## Headless serve methods

| Method | Params → result |
|---|---|
| `engine.execute` | `{command, params?, wait?}`: any engine command. `wait: false` starts a long one as a job, `{job, pending}` |
| `batch` | `{steps: [{command, params?} \| {method, params?}], stopOnError? (true)}` → `{completed, failed, results}`. At most 256 steps |
| `doc.new` | `file.new` params → `{document}` |
| `doc.open` | `{path}` → `{index, name, width, height, layers, warnings}` |
| `doc.place` | `{path, scale? (%), fit? (true), center? ([x, y]), index?}` → `{layer, scale, bounds [x0,y0,x1,y1], smartObject}`. Embeds a Smart Object above the active layer. `fit` defaults to true (shrinks to the canvas when larger); pass `fit:false` with an explicit `scale` |
| `doc.replaceSmartObject` | `{path, layer? (active layer), index?}` → `{layer, instances, warnings}`. Replace Contents from the read root. Keeps the old **scale**, so refit with `edit.transform` + `quad` |
| `doc.save` | `{path?, format?, quality? (1..100), index?, tiffLayers?, tgaBits?}`. `.pcraft`/`.psd`/`.psb` keep layers; any other extension writes a flattened copy and returns a warning. With no `path` only PSD/PSB/.pcraft writes back to its own file |
| `doc.render` | `{index?, maxSide? (1024; 0 = full, max 2048), path?}`: a PNG preview to `path`, else `{mime, base64}` |
| `doc.inspect` | `{index?}`: the same JSON as `photocraft-cli info` |
| `doc.exportLayers` | `{dir, format? (png), prefix?, visibleOnly? (true), quality?, index?}` → `{files, count}`. Refuses to overwrite existing files |
| `doc.exportDataSets` | `{dir, format?, dataSets?, naming? ("{name}\|{index}\|{document}"), index?}` → `{files, count}` |
| `doc.importDataSets` | `{path, delimiter? (,), index?}` → `{imported}` |
| `doc.select` / `doc.close` | `{index}` / `{index?}` |
| `session.list` | open documents (with `dirty`) and the active index |
| `engine.commands` | `{filter?}`: the registry with `params`, `enabled`, `disabledReason` |
| `jobs.list` / `jobs.cancel` | background jobs |
| `methods` | the list above |

There is **no layer-comp export method in `serve`**. Either apply each comp and
`doc.save` it to its own path, or use `photocraft-cli run … --cmd
file.export.layerCompsToFiles` (see [recipes.md](recipes.md#template-edit-and-layer-comps)).

## Filesystem roots

File access in `serve`, MCP and the desktop port **fails closed**: without
`--automation-read-root` / `--automation-write-root` every open, place, save or export is
refused.

- Reads (`doc.open`, `doc.place`, `doc.replaceSmartObject`, `doc.importDataSets`) must lie beneath the read root.
  Writes (`doc.save`, `doc.render` with `path`, `doc.export*`) must lie beneath the write
  root.
- A path is either relative (resolved against the root) or absolute and textually
  beneath the root. **`..` anywhere in the path is rejected**, even inside an absolute
  path, so normalise paths first (`pc_session.py` does it). `~` is not expanded.
- The parent folder of a new output must already exist.
- Engine commands that take raw paths (`file.export.layerCompsToFiles`,
  `file.import.variableDataSets`, `layer.smartObjects.replaceContents`, …) are
  **disabled** under automation: "uses ambient filesystem paths and is disabled". Use the
  `doc.*` method (`doc.replaceSmartObject` for Replace Contents), or run the command with `photocraft-cli run`, which is trusted local.
- The desktop app's `app.open` / `app.save` accept **relative paths only**.

## Desktop control port

Start the app with a control port (what `scripts/pc_live.py start` does):

```sh
open -n -b ai.storyteller.photocraft --args --control 7878 \
  --control-token-file ~/.config/photocraft-skill/control.token \
  --automation-read-root /work --automation-write-root /work
```

- Listens on `127.0.0.1` only. The app creates the token file (256-bit, mode 0600) if it
  is missing.
- **The first frame on every TCP connection must be** `{"id":"auth","method":"auth","params":{"token":"<64 hex>"}}`.
  Nothing else is dispatched before it. The app closes connections that are idle for
  30 s.
- Desktop methods: `engine.execute`, `engine.commands`, `ui.inspect` (tool, panels,
  `document`, `session`, `dialogs`, `windows`), `ui.screenshot {path?}` (a path relative to
  the write root; captures the app window), `ui.menu.invoke {id}` (opens a command's
  dialog when no params are given), `ui.set`, `ui.pointer`, `ui.click`, `ui.key`,
  `ui.type`, `app.open {path}`, `app.save {path?}`, `app.quit`.
- **`app.quit` quits at once and discards unsaved edits** (verified in 0.9.0: no
  prompt). Save first.
- Never launch `PhotoCraft.app/Contents/MacOS/PhotoCraft --help` or similar to probe
  flags: it opens the GUI.

## Security posture

- The bearer token is the whole credential. Whoever has it gets command execution, UI
  input and app control. Keep the token file private: never commit it, log it, or pass it
  as `--control-token` on the command line, where other processes can see it.
- Loopback, unencrypted. Never expose, tunnel or proxy the port.
- File access is limited to the roots given at launch. Grant the narrowest folder the
  task needs, never `~` or `/`.
- The control port is opt-in. Start it only when the user wants to watch edits live, and
  stop it (`pc_live.py stop`) when done. `serve` over stdio needs no token and no
  listener.

## Limits and timeouts

- Desktop replies time out after 60 s. `timeout: not run` is safe to resend; `timeout: no
  reply in 60s` may still apply, so inspect before retrying.
- An idle headless TCP `serve` releases its port (0.16.0+); reconnect rather than keep a
  connection open between unrelated jobs.
- 1 MiB per request line, 8 MiB per reply, 256 steps per `batch`.
- `doc.render` previews: at most 2048 px on the long edge and 5 MiB of PNG.
- Long commands: pass `"wait": false` and poll `jobs.list`. Any later request applies
  finished jobs first.
