# Recipes

Complete agent modules, each tested on Hammerspoon 1.1.1. Copy one, adapt it, then
`hsctl.py install NAME file.lua` and verify with `hsctl.py call` + `inventory`.

## Contents
- [Multi-monitor window layout on a hotkey](#multi-monitor-window-layout-on-a-hotkey)
- [Hotkey that runs a shell script](#hotkey-that-runs-a-shell-script)
- [React to an app launching or quitting](#react-to-an-app-launching-or-quitting)
- [Inventory report](#inventory-report)
- [Splitting a big config into modules](#splitting-a-big-config-into-modules)
- [Smaller snippets](#smaller-snippets)

## Multi-monitor window layout on a hotkey

Places windows by **bundle ID** on screens found by **name pattern**, re-applies when
displays change, and returns what it placed so `hsctl.py call layout apply` doubles as
the verification. Look up bundle IDs and screen names with `hsctl.py inventory` first.

```lua
-- Two-monitor layout: Chrome left / TextEdit right on the big screen, Finder on the laptop.
local M = {}

-- hs.screen.find matches these as Lua patterns against the lowercased screen name.
M.big = "lg"
M.laptop = "built%-in"

-- Bundle IDs, not app names: names are localized (TextEdit is "Szövegszerkesztő" on a
-- Hungarian system) and hs.application.get(name) then silently finds nothing.
M.rules = {                      -- bundle ID, screen key, unit rect {x, y, w, h}
  { "com.google.Chrome",  "big",    { 0,   0, 0.5, 1 } },
  { "com.apple.TextEdit", "big",    { 0.5, 0, 0.5, 1 } },
  { "com.apple.finder",   "laptop", { 0,   0, 1,   1 } },
}

local function screenFor(key)
  -- Fall back to the primary screen when a display is missing (laptop undocked).
  return hs.screen.find(M[key]) or hs.screen.primaryScreen()
end

function M.apply()
  hs.window.animationDuration = 0
  hs.window.timeout(1)            -- don't let one hung app stall the whole layout
  local placed = {}
  for _, rule in ipairs(M.rules) do
    local bundleID, key, unit = rule[1], rule[2], rule[3]
    local app = hs.application.get(bundleID)
    local scr = screenFor(key)
    for _, win in ipairs(app and app:allWindows() or {}) do
      if win:isStandard() and not win:isMinimized() and not win:isFullScreen() then
        win:setFrame(hs.geometry(unit):fromUnitRect(scr:frame()))
        placed[#placed + 1] = { app = app:name(), title = win:title(), screen = scr:name(), frame = win:frame().table }
      end
    end
  end
  return placed
end

M.hotkey = hs.hotkey.bind({ "ctrl", "alt" }, "L", "Apply window layout", M.apply)
-- Re-apply when displays are plugged in or out (debounced: the event fires in bursts).
M.screenWatcher = hs.screen.watcher.new(function()
  if M.pending then M.pending:stop() end
  M.pending = hs.timer.doAfter(2, M.apply)
end):start()

function M.stop()
  M.hotkey:delete()
  M.screenWatcher:stop()
  if M.pending then M.pending:stop() end
end

return M
```

Verify:

```bash
python3 scripts/hsctl.py install layout layout.lua
python3 scripts/hsctl.py call layout apply      # list of {app, title, screen, frame}
python3 scripts/hsctl.py inventory              # frames match? (allow a few px: apps round sizes)
```

Variations:
- Thirds / quarters: unit rects `{0,0,1/3,1}`, `{0,0,0.5,0.5}`. Centered: `{0.15,0.1,0.7,0.8}`.
- Only the frontmost window: `hs.window.focusedWindow():moveToUnit({0,0,0.5,1})`.
- One window of an app by title: filter on `win:title():find("Inbox", 1, true)`.
- Several layouts: `M.layouts = { work = {...}, focus = {...} }` and
  `function M.apply(name) ... end`, bind each to its own key with
  `function() M.apply("work") end`; `hsctl.py call layout apply work` to test.

## Hotkey that runs a shell script

`hs.task` runs the script asynchronously, so Hammerspoon stays responsive, and the
completion callback reports the exit code. `"$0"` passes the path as one argument
(spaces safe) to a login shell, so the script sees the user's `PATH` (Homebrew tools).

```lua
-- ctrl+alt+B runs a shell script without freezing Hammerspoon and reports the result.
local M = {}

M.script = os.getenv("HOME") .. "/bin/backup.sh"

function M.run()
  if M.task and M.task:isRunning() then
    hs.alert.show("Backup already running")
    return "already running"
  end
  M.task = hs.task.new("/bin/zsh", function(exitCode, stdOut, stdErr)
    M.last = { exitCode = exitCode, stdout = stdOut, stderr = stdErr, at = os.date("%F %T") }
    if exitCode == 0 then
      hs.alert.show("Backup finished")
    else
      hs.alert.show("Backup failed (exit " .. exitCode .. ")")
      print("backup stderr: " .. (stdErr or ""))
    end
  end, { "-lc", '"$0"', M.script })   -- login shell, so the script sees the user's PATH
  M.task:start()
  return "started"
end

M.hotkey = hs.hotkey.bind({ "ctrl", "alt" }, "B", "Run backup", M.run)

function M.stop()
  M.hotkey:delete()
  if M.task and M.task:isRunning() then M.task:terminate() end
end

return M
```

Verify without touching the keyboard — `call` runs the same function the hotkey runs:

```bash
python3 scripts/hsctl.py call backup run                   # "started"
python3 scripts/hsctl.py run --json -e 'return hsagent.modules.backup.last'   # after it ends
```

`last` holds exit code, stdout and stderr; also check the script's own side effect
(the file it writes). Make sure the script is executable (`chmod +x`) — otherwise
the task exits 126 and the alert says so.

## React to an app launching or quitting

```lua
-- When an app launches or quits, react. Matched by bundle ID (names are localized).
local M = {}

M.target = "us.zoom.xos"
M.events = {}

local W = hs.application.watcher
function M.onEvent(name, event, app)
  if not app or app:bundleID() ~= M.target then return end
  if event == W.launched then
    M.events[#M.events + 1] = { event = "launched", at = os.time() }
    hs.alert.show(name .. " launched")
    -- e.g. mute the default microphone while it runs:
    local mic = hs.audiodevice.defaultInputDevice()
    if mic then mic:setInputMuted(true) end
  elseif event == W.terminated then
    M.events[#M.events + 1] = { event = "terminated", at = os.time() }
    local mic = hs.audiodevice.defaultInputDevice()
    if mic then mic:setInputMuted(false) end
  end
end

M.watcher = W.new(M.onEvent):start()

function M.stop() M.watcher:stop() end

return M
```

- Events: `launching`, `launched`, `activated`, `deactivated`, `hidden`, `unhidden`,
  `terminated` (constants on `hs.application.watcher`).
- `name` in the callback is the **localized** name; compare `app:bundleID()`.
- Get the bundle ID of a running app from `hsctl.py inventory` (`apps[].bundleID`)
  or `osascript -e 'id of app "Zoom"'`.
- Test it by launching and quitting the app (`open -b <bundleID>`, then
  `osascript -e 'tell application id "<bundleID>" to quit'`) and reading `M.events`.
- For per-window events (a window of an app opened, focused, moved) use
  `hs.window.filter` instead — see api-reference.md.

## Inventory report

For "what's open where" questions, run `hsctl.py inventory` and summarize — don't
write Lua for it. A good answer:

```
Screens: LG HDR WFHD (2560×976, primary), Built-in Retina Display (1512×949, left of it)

LG HDR WFHD
| App            | Window                   |
|----------------|--------------------------|
| Google Chrome  | Pull requests · GitHub   |  ← frontmost
| Terminal       | ~ — zsh                  |

Built-in Retina Display
| App     | Window      |
|---------|-------------|
| Finder  | Downloads   |

Running apps with no visible window: Mail (hidden), Music
```

- `screen` per window is the screen holding most of the window's area.
- `inventory` lists only standard, visible windows; `--all` adds minimized ones,
  panels and background apps — mention minimized windows separately if they matter.
- Some windows have an empty title (new documents, helper panels); say "(untitled)"
  rather than dropping them.

## Splitting a big config into modules

When the user wants their config organized ("make my init.lua modular"), keep one
concern per module — `layout`, `hotkeys`, `watchers`, `wifi` — each returning its
`M`. Move behaviour out of their `init.lua` only when they ask; otherwise add modules
beside it. Install each module separately so a load error is pinned to one file.
Shared helpers go in a module too; another module reaches it as
`hsagent.modules.helpers` (modules load alphabetically — name helpers so they sort
first, e.g. `a_helpers`, or look them up lazily inside functions).

## Smaller snippets

```lua
-- Launch or focus an app on a hotkey
M.hk = hs.hotkey.bind({ "cmd", "alt" }, "T", function() hs.application.launchOrFocusByBundleID("com.apple.Terminal") end)

-- Reload config on a hotkey (handy while the user edits by hand)
M.hk = hs.hotkey.bind({ "cmd", "alt", "ctrl" }, "R", hs.reload)

-- Wi-Fi watcher: SSID changed (macOS returns nil for the SSID until Hammerspoon has
-- Location Services permission: hs.location.start() once prompts for it)
M.wifi = hs.wifi.watcher.new(function() M.ssid = hs.wifi.currentNetwork() end):start()

-- USB device plugged in
M.usb = hs.usb.watcher.new(function(dev) if dev.eventType == "added" then print(dev.productName) end end):start()

-- Sleep / wake
M.power = hs.caffeinate.watcher.new(function(ev)
  if ev == hs.caffeinate.watcher.systemDidWake then M.apply() end
end):start()

-- Run something every 15 minutes
M.timer = hs.timer.doEvery(15 * 60, function() ... end)

-- A file changed (e.g. reload when a module file is saved)
M.files = hs.pathwatcher.new(hs.configdir .. "/agent", function() hs.reload() end):start()
```
