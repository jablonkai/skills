# Gotchas

Each one below was hit on Hammerspoon 1.1.1 / macOS 27, or is a classic from the
Hammerspoon issue tracker.

## Nothing happens

- **Accessibility not granted.** `hs.accessibilityState()` is `false`: window lists
  contain only Hammerspoon's own windows, `setFrame` is a no-op, and keystroke
  synthesis is ignored. No error is raised. Only the user can grant it (System
  Settings › Privacy & Security › Accessibility); after granting, no restart is needed.
- **Localized app names.** `app:name()` and the app-watcher `name` are localized:
  TextEdit is "Szövegszerkesztő" on a Hungarian system, and
  `hs.application.get("TextEdit")` returns nil there. Match by bundle ID
  (`com.apple.TextEdit`); `inventory` shows each app's and window's `bundleID`.
- **Garbage-collected objects.** `local hk = hs.hotkey.bind(...)` at the top of a chunk
  works until Lua's GC runs, then the hotkey (or watcher, timer, task) silently dies.
  Keep every such object on the module table `M` — the loader holds `M` in
  `hsagent.modules`.
- **One-off objects die on reload.** A hotkey bound with `hsctl.py run` lives in the
  current Lua state only; the next reload (install, remove, the user's own reload)
  wipes it. Persistent things go in a module.
- **Screen patterns are lowercased.** `hs.screen.find("LG")` never matches: the name is
  lowercased before `string.match`, so write `hs.screen.find("lg")`. Patterns are Lua
  patterns — escape `-` as `%-` (`"built%-in"`).
- **The hotkey combo is taken by macOS or another app.** Registration succeeds but the
  key never reaches Hammerspoon (e.g. ⌃↑ = Mission Control, ⌘Space = Spotlight). Pick
  combos with ⌃⌥ or ⌃⌥⌘; ask the user to test if in doubt.
- **A second bind of the same combo shadows the first** — no error. `hsctl.py list`
  shows every active hotkey; check before choosing.

## Testing without a keyboard

- `hs.eventtap.keyStroke(mods, key)` posted from Hammerspoon does **not** trigger
  Hammerspoon's own hotkeys, and `hs.hotkey.getHotkeys()` doesn't expose callbacks.
  That is why modules put each action in a named function: `hsctl.py call NAME FUNC`
  runs exactly what the hotkey would.

## Windows land in the wrong place

- **Animation races**: with the default `animationDuration = 0.2`, moving several
  windows in a loop can leave some half-way. Set `hs.window.animationDuration = 0` in
  layout code.
- **Apps round sizes**: Terminal resizes in character cells, some apps enforce a
  minimum size; frames can be off by a few points. Compare with a tolerance (±10 pt).
  `hs.window.setFrameCorrectness = true` helps with stuck edges.
- **Full-screen windows** live in their own Space and refuse `setFrame`; skip them
  (`w:isFullScreen()`) or `w:setFullScreen(false)` first.
- **Other Spaces**: windows on a different desktop Space are often missing from
  `visibleWindows()`/`allWindows()`; Hammerspoon can't move windows between Spaces
  reliably.
- **`moveToUnit` uses the window's current screen** — move it to the target screen first,
  or compute the frame from the target screen (`fromUnitRect(scr:frame())`).
- **Screen ids change** across reboots and re-plugs; names can repeat (two identical
  monitors). Prefer name patterns with a fallback, or `getUUID()` for identical models.
- **`hs.screen.watcher` fires in bursts** while displays settle; debounce with a timer
  (see the layout recipe) or the layout runs against half-configured screens.

## Hammerspoon freezes or the CLI hangs

- **An unresponsive app stalls every window query.** `hs.window.allWindows()`, and
  anything else that walks windows, asks each app over Accessibility and waits up to
  the AX timeout (several seconds) for each one that doesn't answer. One hung app (a
  beach-balling game launcher, say) turns a 50 ms query into minutes and trips the CLI
  timeout. Set `hs.window.timeout(1)` first. `inventory` does this; layout actions
  should too.

- **`hs.execute` blocks** the whole app (all hotkeys, all watchers) until the command
  returns. Use `hs.task` for anything that can take more than a moment.
- **`hs` reads a piped stdin as code** and waits for EOF. From a script or an agent
  shell, call `hs ... </dev/null` (hsctl.py does this). Symptom: `hs -c` never returns.
- **`-q` matters**: without it stdout starts with `-- Loading extension: …` lines, which
  break any parsing.
- **Long work over ipc** hits the 4 s CLI timeout (exit 69, "receive timeout") but keeps
  running inside Hammerspoon. Move it to `hs.timer.doAfter(0, fn)` or `hs.task`.
- **Reload drops the ipc port**: `hs -c 'hs.reload()'` exits 69 with "message port was
  invalidated". hsctl.py schedules the reload on a timer and polls until the new Lua
  state answers.
- **init.lua errors before `require("hs.ipc")`** → after a reload the CLI can't connect
  at all. `hsctl.py restore` (file-level, works without ipc) then `hsctl.py restart`.
  `enable-ipc` puts the require on the first line for this reason.

## Errors you won't see unless you look

- Errors inside callbacks (hotkeys, timers, watchers, task completions) don't propagate
  anywhere — they print `ERROR: LuaSkin: hs.<module> callback error: …` plus a
  traceback in the console. Run `hsctl.py console --errors` after exercising an action.
- `hs.task` with a relative `launchPath` (`"zsh"`) fails to start; `start()` returns
  false and nothing runs. Use absolute paths.
- A script without the executable bit exits 126 through `/bin/zsh -lc '"$0"'`; a typo'd
  path exits 127. Report `exitCode` from the task callback.

## Security posture

- **What the skill opens:** nothing new on the network. `hs` talks to Hammerspoon over
  `hs.ipc`, a CFMessagePort (Mach port) in the user's login session. Only processes
  running as the same user can reach it; there is no TCP/HTTP listener, so cross-origin
  attacks don't apply and there is no token to steal.
- **What enabling ipc means:** every process of that user can then run arbitrary Lua
  inside Hammerspoon — with Hammerspoon's Accessibility rights (control any window,
  synthesize input) and `hs.execute` (any shell command). That is the same power as
  editing `~/.hammerspoon/init.lua`, which any such process can already do, but it is
  immediate. Ask the user before `enable-ipc`; mention it when they have security
  tooling or shared accounts.
- **What the skill writes:** `~/.hammerspoon/agent/*.lua`, one marked loader block and
  a `require("hs.ipc")` line in `init.lua`; backups of every overwritten file in
  `~/.hammerspoon/.agent-backups/` (last 20 per file). Nothing else in the user's
  config is modified.
- **Stop path:** `hsctl.py remove NAME` (one module), `disable-all` (every agent module,
  reversible with `enable-all`), `restore` (previous `init.lua`), `restart`. Each
  module's `stop()` runs before a reload.
- **Network-facing recipes** (`hs.httpserver`) bind to `localhost`, require a password,
  and expose fixed actions only — never an endpoint that evaluates request bodies.
