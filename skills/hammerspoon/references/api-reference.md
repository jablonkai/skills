# API reference (the parts this skill uses)

Hammerspoon 1.1.1, Lua 5.4. Full docs: <https://www.hammerspoon.org/docs/>, or ask
the live app — `hsctl.py run -e 'return tostring(hs.doc.hs.window.moveToUnit)'`
prints the installed version's own docstring (works for any `hs.*` function).

## Contents
- [Coordinates and geometry](#coordinates-and-geometry)
- [hs.screen](#hsscreen)
- [hs.window](#hswindow)
- [hs.window.filter](#hswindowfilter)
- [hs.layout](#hslayout)
- [hs.application](#hsapplication)
- [hs.hotkey](#hshotkey)
- [hs.task and hs.execute](#hstask-and-hsexecute)
- [Watchers and timers](#watchers-and-timers)
- [Feedback: alert, notify, console](#feedback-alert-notify-console)
- [hs.httpserver](#hshttpserver)
- [hs CLI](#hs-cli)

## Coordinates and geometry

- One global space for all screens, origin top-left of the **primary** screen, y down.
  A screen left of the primary has negative x; above it, negative y.
- `screen:frame()` excludes the menu bar and Dock; `screen:fullFrame()` includes them.
- `hs.geometry.rect(x, y, w, h)`; `.table` gives `{x,y,w,h}`; fields `x y w h x2 y2 center`.
- **Unit rect**: fractions of a screen, `{x, y, w, h}` in 0..1.
  `hs.geometry(unit):fromUnitRect(screen:frame())` → absolute frame;
  `hs.layout.left50`, `right50`, `left30`, `right70`, `maximized` are predefined.

## hs.screen

| Call | Returns |
|------|---------|
| `hs.screen.allScreens()` | all screens |
| `hs.screen.primaryScreen()` | the one with the menu bar |
| `hs.screen.mainScreen()` | the one with the focused window |
| `hs.screen.find(hint)` | by id (number), UUID, **lowercased** name pattern, position `{x,y}` or resolution `{w,h}` |
| `s:name()`, `s:id()`, `s:getUUID()` | identity — name is human, UUID is the stable one |
| `s:frame()`, `s:fullFrame()` | geometry rects |
| `s:position()` | grid position relative to primary, e.g. `-1, 0` = left of it |
| `s:toEast()`, `s:toWest()`, `s:next()` | neighbours |

## hs.window

| Call | Notes |
|------|-------|
| `hs.window.focusedWindow()` | may be nil (desktop focused) |
| `hs.window.visibleWindows()` / `allWindows()` | all apps; `allWindows` includes minimized |
| `hs.window.orderedWindows()` | visible standard windows, front to back |
| `app:allWindows()`, `app:mainWindow()`, `app:focusedWindow()` | per app |
| `w:title()`, `w:id()`, `w:application()`, `w:screen()` | `screen()` = screen with most of the window |
| `w:isStandard()`, `isMinimized()`, `isFullScreen()`, `isVisible()` | filter panels and sheets with `isStandard()` |
| `w:frame()`, `w:setFrame(rect[, dur])` | absolute frame |
| `w:moveToUnit(unit[, dur])` | fraction of the window's **current** screen |
| `w:moveToScreen(screen[, noResize, ensureInBounds][, dur])` | keeps relative position/size |
| `w:maximize()`, `w:centerOnScreen()`, `w:focus()`, `w:raise()`, `w:minimize()`, `w:setFullScreen(bool)` | |
| `hs.window.animationDuration` | default 0.2 s; set 0 for scripted layouts |
| `hs.window.setFrameCorrectness` | `true` works around edge stickiness and step-resizing apps (Terminal) at some speed cost |

To put a window at a unit rect on another screen in one step:
`w:setFrame(hs.geometry(unit):fromUnitRect(scr:frame()))`.

## hs.window.filter

Event-driven window tracking. Heavier than an app watcher; use when per-window events
matter.

```lua
M.wf = hs.window.filter.new({ "Safari" })   -- or true = all, or a table of app names
M.wf:subscribe(hs.window.filter.windowCreated, function(win, appName) ... end)
-- events: windowCreated, windowDestroyed, windowFocused, windowMoved, windowsChanged, ...
M.wf:getWindows()                             -- current matches
-- in stop(): M.wf:unsubscribeAll()
```

App names here are the localized names `app:name()` returns — check them in
`inventory` first.

## hs.layout

`hs.layout.apply(rules)` — each rule:
`{ app (name | hs.application | nil), window title (string | hs.window | function | nil), screen (name | hs.screen | function | nil), unitRect, frameRect, fullFrameRect }`,
only one of the last three non-nil. Matches **all** windows of the app (including
non-standard ones), and app names must be the localized ones — the explicit loop in
the layout recipe is easier to get right and to report from.

## hs.application

| Call | Notes |
|------|-------|
| `hs.application.get(hint)` | running app by **bundle ID**, name or pid — first match |
| `hs.application.find(hint)` | pattern match; may return several |
| `hs.application.runningApplications()` | all; `a:kind() == 1` = regular Dock apps |
| `hs.application.frontmostApplication()` | |
| `hs.application.launchOrFocusByBundleID(id)` | launch or focus |
| `hs.application.open(id, wait)` | launch; `wait` seconds for its first window |
| `a:name()` (localized), `a:bundleID()`, `a:pid()`, `a:isHidden()`, `a:hide()`, `a:kill()` | |
| `a:selectMenuItem({"File", "New Window"})` | drive a menu (localized titles) |
| `hs.application.watcher.new(fn(name, event, app))` | `:start()`/`:stop()`; events `launching launched activated deactivated hidden unhidden terminated` |

## hs.hotkey

```lua
M.hk = hs.hotkey.bind(mods, key, [message,] pressedfn[, releasedfn, repeatfn])
-- mods: {"cmd","alt","ctrl","shift"} (also "⌘⌥⌃⇧" or "cmd+alt" strings), or {} for none
-- key: "a".."z", "0".."9", "f1".."f20", "left", "return", "space", "escape", ... (hs.keycodes.map)
M.hk:disable(); M.hk:enable(); M.hk:delete()
hs.hotkey.getHotkeys()   -- active hotkeys: { idx = "⌃⌥L", msg = ..., ... } (no callback)
hs.hotkey.modal.new(mods, key)   -- a mode: :bind() keys inside it, :enter()/:exit()
```

Binding a combination that is already bound in this config does **not** fail: the new
hotkey shadows the old one (console: `Disabled hotkey …`), and deleting it
re-enables the old one. Check `hsctl.py list` before choosing a combo. Shortcuts of
other apps or macOS are not detected — a combo macOS reserves may simply never fire.

## hs.task and hs.execute

```lua
M.task = hs.task.new("/bin/zsh", function(exitCode, stdOut, stdErr) ... end, { "-lc", "cmd here" })
M.task:start()          -- async; returns immediately
M.task:isRunning(); M.task:terminate(); M.task:waitUntilExit() -- (blocks: avoid)
M.task:setWorkingDirectory(dir); M.task:setEnvironment(tbl)
```

- `launchPath` must be absolute. Hammerspoon's own environment has a minimal `PATH`;
  `/bin/zsh -lc` gives the user's login `PATH`.
- `hs.execute(cmd[, withUserEnv])` → `output, status, type, rc` — **synchronous**, the
  whole app (all hotkeys, all watchers) freezes until it returns. Fine for a 50 ms
  `pmset -g`; wrong for anything that can take seconds.
- Keep the task object referenced (`M.task`) or it can be collected mid-run.

## Watchers and timers

All but `hs.audiodevice.watcher` follow `X.new(fn):start()` / `:stop()`; keep them on `M`.

| Watcher | Fires on | Callback |
|---------|----------|----------|
| `hs.application.watcher` | app lifecycle | `(name, event, app)` |
| `hs.screen.watcher` | displays added/removed/rearranged, Dock resize | `()` — bursts, debounce |
| `hs.caffeinate.watcher` | sleep, wake, screen lock, screensaver | `(event)` e.g. `systemDidWake`, `screensDidUnlock` |
| `hs.wifi.watcher` | SSID change by default; more via `:watchingFor` (SSID name needs Location permission) | `(watcher, message[, interface, ...])` |
| `hs.usb.watcher` | USB devices | `({eventType, productName, vendorName, vendorID, productID})` |
| `hs.pathwatcher` | files under a path changed | `(paths, flagTables)` |
| `hs.battery.watcher` | power source / charge | `()` |
| `hs.audiodevice.watcher` | default device changed — module-level: `setCallback(fn)` then `start()` | `(event)` e.g. `"dIn "`, `"dOut"` |

Timers: `hs.timer.doAfter(sec, fn)`, `hs.timer.doEvery(sec, fn)`, `hs.timer.doAt("08:00", "1d", fn)`,
`hs.timer.waitUntil(predicate, fn)`. All return a timer — keep it, `:stop()` it.

## Feedback: alert, notify, console

- `hs.alert.show(text[, style][, screen][, seconds])` — big transient overlay.
- `hs.notify.new({ title = ..., informativeText = ... }):send()` — Notification
  Centre (the user must allow Hammerspoon notifications); `hs.notify.show(t, sub, info)`
  is shorthand.
- `print(...)` → the console. `hs.console.getConsole()` returns the whole console text
  (`hsctl.py console` filters it). Log levels for modules: `hs.logger.new("name", "info")`.
- Callback errors land in the console as `ERROR: LuaSkin: hs.<module> callback error: …`
  with a traceback — they don't stop the rest of the config.

## hs.httpserver

For a local webhook ("trigger my layout from a Stream Deck / another machine"):

```lua
M.server = hs.httpserver.new(false, false)   -- no SSL, no Bonjour
M.server:setInterface("localhost")           -- loopback only; never bind 0.0.0.0 unasked
M.server:setPort(8765)
M.server:setPassword("…")                    -- HTTP basic auth
M.server:setCallback(function(method, path, headers, body)
  if method == "POST" and path == "/layout" then M.apply(); return "ok", 200, {} end
  return "not found", 404, {}
end)
M.server:start()
-- in stop(): M.server:stop()
```

Anything exposed this way runs with Hammerspoon's Accessibility rights; keep it on
loopback, password-protected, and limited to fixed actions (never eval a request body).

## hs CLI

`hs` lives at `Hammerspoon.app/Contents/Frameworks/hs/hs` (`hs.ipc.cliInstall()` would
symlink it into `/usr/local/bin`; `hsctl.py` doesn't need that).

| Flag | Meaning |
|------|---------|
| `-c CODE` | run code (repeatable); a bare expression is auto-`return`ed |
| `-q` | quiet: only errors and the final result (otherwise "-- Loading extension" lines) |
| `-t SEC` | send/receive timeout, default 4 |
| `-n` | no colour |
| `-A` | launch Hammerspoon without asking if it's not running |
| `FILE [args]` | run a file; args in `_cli.args` |

Exit codes seen on 1.1.1: 0 ok, 65 Lua error (message on stderr), 69 transport error
(timeout, or the port went away because of a reload), 1 no message port (not running
or `hs.ipc` not loaded). **If stdin is a pipe, `hs` reads it as code** and waits for
EOF — call it with `</dev/null` from scripts (hsctl.py does).
