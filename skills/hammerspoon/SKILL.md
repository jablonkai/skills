---
name: hammerspoon
description: 'Automate macOS with Hammerspoon from the command line: run one-off Lua in the live app through the hs CLI (hs.ipc) to list screens, apps and windows or move and resize windows now, and write modular config files for persistent behaviour — window layouts for one or several monitors, global hotkeys that run shell scripts or launch apps, app, screen, Wi-Fi, USB and sleep watchers — then reload and read the console for errors. Use for "set up a two-monitor window layout with Hammerspoon", "bind ctrl+alt+B to run my backup script", "which windows are open on which screen", "when Zoom launches, mute the mic", "re-tile my windows when I plug in the external display", "write me a Hammerspoon config", "why does my init.lua error". Not for Apple Shortcuts (apple-shortcuts), scripting one app''s documents (keynote, numbers, pages), OBS scenes (obs), Karabiner-Elements key remapping, Raycast, Alfred, Rectangle or BetterTouchTool setups, or plain AppleScript with no Hammerspoon.'
summary: "automate macOS with Hammerspoon via the hs CLI — window layouts for multi-monitor setups, hotkeys that run shell scripts, app and screen watchers, screen/app/window inventory, modular init.lua files with reload and console error checks"
category: mac-automation
risk: medium
tags:
    - hammerspoon
    - lua
    - macos
    - window-management
    - hotkeys
    - automation
metadata:
  version: "1.0.0"
---

# Hammerspoon from the command line

Hammerspoon (free, MIT) is a macOS app that exposes the system to Lua: windows,
screens, hotkeys, app and hardware events, tasks, alerts. Its config is
`~/.hammerspoon/init.lua`. This skill drives the **running** app through its `hs`
command-line tool and manages persistent behaviour as small module files, so the
user's own config is never rewritten. Verified against **Hammerspoon 1.1.1** on
macOS 27 (arm64).

There are two ways to get something done, and choosing right matters:

| Way | Use it for | Survives a reload / restart? |
|-----|-----------|------------------------------|
| **One-off Lua** (`hsctl.py run`, `inventory`) | questions ("what's open where?"), doing something once ("tile these now") | no — nothing is saved |
| **Agent module** (`hsctl.py install NAME file.lua`) | anything that must keep working: hotkeys, watchers, a layout bound to a key | yes — it lives in `~/.hammerspoon/agent/NAME.lua` |

A hotkey or watcher created with one-off Lua dies at the next reload, so when the
user asks for a hotkey, a watcher, or "set up", always write a module.

- [scripts/hsctl.py](scripts/hsctl.py): the helper (stdlib Python 3.9+). Exit codes:
  **0** ok, **1** setup problem (not running, no ipc, no Accessibility), **2**
  Hammerspoon reported a Lua or load error, **3** timeout.
- [references/api-reference.md](references/api-reference.md): the hs.* APIs this
  skill leans on: window, screen, geometry, layout, hotkey, application, task,
  watchers, alert/notify, httpserver, console.
- [references/recipes.md](references/recipes.md): complete modules for a
  multi-monitor layout, hotkey → shell script, app watcher, re-layout on display
  change, plus the inventory report.
- [references/gotchas.md](references/gotchas.md): **read before debugging a hotkey
  that does nothing, a window that won't move, or a watcher that stops firing.** It
  also has the security posture.

## 1. Check first

```bash
S=scripts   # paths are relative to this skill's directory
python3 $S/hsctl.py check
```

It prints JSON and lists any `problems`. Fix them in this order:

- **Not installed:** `brew install --cask hammerspoon`, then `open -a Hammerspoon`.
- **`ipc: false`:** the config doesn't `require("hs.ipc")`, so `hs` can't reach the
  app. Ask the user, then `hsctl.py enable-ipc --restart`. It adds the line to the top
  of `init.lua` (after a backup) and relaunches Hammerspoon.
- **`accessibility: false`:** only the user can grant it (System Settings › Privacy &
  Security › Accessibility › Hammerspoon). Until then, Hammerspoon sees only its own
  windows and cannot move anything. Say so and stop; don't try to work around it.

The `hs` binary ships inside the app bundle. `hsctl.py` finds it there, so it doesn't
matter that `hs` isn't on `PATH`. Don't run `hs.ipc.cliInstall()` for the user.

## 2. Ask the live app (one-off Lua)

```bash
python3 $S/hsctl.py inventory                 # screens, regular apps, standard visible windows
python3 $S/hsctl.py inventory --all           # + minimized, non-standard, background apps
python3 $S/hsctl.py run --json -e 'return hs.window.focusedWindow():frame()'
python3 $S/hsctl.py run -f snippet.lua        # or -e CODE, or - for stdin
```

- `--json` returns the first return value as JSON. Geometry becomes `{x,y,w,h}`, and
  userdata (windows, apps, screens) becomes its `tostring()`, so return tables of
  plain fields rather than objects. Without `--json`, `hs` prints the value as text.
- Answer inventory questions from `inventory`, not from a screenshot or guesswork.
  Report windows grouped by screen (by name, with resolution), and say which app is
  frontmost. Windows with an empty title are usually helper panels; mention them only
  if asked.
- Each `run` gets a fresh chunk, so its `local`s are gone afterwards. Store state you
  need again in a global table, or better, in a module.
- If a window query in `run` times out, an app is probably hung: put
  `hs.window.timeout(1)` first, as `inventory` does.
- `run` has a 10 s timeout (`--timeout`). Hammerspoon is single-threaded, so slow
  work (`hs.execute`, big loops) freezes it. Run shell commands with `hs.task`.

## 3. Persistent behaviour: agent modules

A module is a Lua file that **returns a table**. The loader in `init.lua` keeps every
module in `hsagent.modules.NAME`. That global reference stops Lua's garbage
collector from silently killing hotkeys and watchers (the classic "works for a minute,
then stops"). It also lets anyone call the module's actions by name.

```lua
-- layout.lua
local M = {}

function M.apply()                -- the action: callable by hotkey, watcher or hsctl call
  -- ... do the work, return something useful to report
end

M.hotkey = hs.hotkey.bind({ "ctrl", "alt" }, "L", M.apply)    -- keep a reference in M
M.watcher = hs.screen.watcher.new(M.apply):start()             -- ditto

function M.stop()                  -- called before every reload
  M.hotkey:delete()
  M.watcher:stop()
end

return M
```

Rules that keep modules working and testable:

- **Put each action in a named function on `M`** and bind the hotkey to it. A hotkey's
  callback can't be read back from `hs.hotkey`, and Hammerspoon's own synthetic
  keystrokes don't fire its hotkeys. `hsctl.py call NAME FUNC` is therefore the only
  way to exercise the action without a human at the keyboard.
- **Keep every hotkey, watcher, timer and task on `M`.** Don't use bare locals, which
  get garbage-collected, and don't use new globals, which collide between modules.
- **Use `hs.task` for shell commands.** Give it an absolute path to the executable
  (`/bin/zsh`, not `zsh`) and report the outcome with `hs.alert` or `hs.notify` from
  its completion callback. `hs.execute` blocks the whole app until the command ends.
- **Match apps by bundle ID** (`hs.application.get("com.apple.TextEdit")`), not by
  name. Names are localized: on a Hungarian system TextEdit is "Szövegszerkesztő", and
  a name lookup silently finds nothing. `inventory` shows every app's `bundleID`.
- Find screens by name pattern with a fallback (`hs.screen.find("LG") or
  hs.screen.primaryScreen()`). Displays get unplugged, and ids change between boots.
  `find` matches a Lua pattern against the **lowercased** name, so use `"lg"` and
  `"built%-in"`.
- Set `hs.window.animationDuration = 0` and `hs.window.timeout(1)` inside layout
  actions. Animated moves race with the next move and land in the wrong place, and one
  hung app otherwise stalls every window query for seconds.

Install, verify, iterate:

```bash
python3 $S/hsctl.py install layout layout.lua   # syntax check, copy, reload, load report (JSON)
python3 $S/hsctl.py call layout apply           # run the action now, print its return value
python3 $S/hsctl.py inventory                   # verify the effect, e.g. window frames
python3 $S/hsctl.py list                        # modules, their exports, active hotkeys
```

- `install` writes `~/.hammerspoon/agent/NAME.lua`. On first use it adds one marked
  block (`-- BEGIN agent modules` … `-- END agent modules`) to the end of `init.lua`,
  plus `require("hs.ipc")` if it's missing. It never touches the user's other lines,
  and it backs up `init.lua` and the module first (`~/.hammerspoon/.agent-backups/`).
- If the module fails to load, `install` exits 2 with the Lua error and **rolls it
  back** (to the previous version, or removes it). Read the error, fix the file,
  install again.
- Always confirm the effect after installing: check that `list` shows the hotkey
  (e.g. `⌃⌥L`), `call` the action, and look at `inventory` or the action's side effect
  (a file the script wrote, a window frame). A clean load alone proves little.
- When the user already has hand-written config in `init.lua`, leave it alone. Add a
  module beside it, and mention any of their hotkeys yours would collide with
  (`list` shows every active hotkey).

## 4. Reload, errors, undo

```bash
python3 $S/hsctl.py reload                 # reload, wait for ipc, JSON with load errors
python3 $S/hsctl.py console --errors       # error lines + tracebacks since the last reload
python3 $S/hsctl.py console -n 40          # the last 40 console lines
python3 $S/hsctl.py remove NAME            # delete a module (backed up) and reload
python3 $S/hsctl.py disable-all            # stop loading every agent module (enable-all undoes)
python3 $S/hsctl.py restore [--list]       # put back the latest (or a chosen) init.lua backup
python3 $S/hsctl.py restart                # quit + relaunch when ipc is gone
```

- Callback errors (in a hotkey, timer or watcher) don't fail `install`; they appear
  later in the console as `ERROR: LuaSkin: hs.<module> callback error`. After calling
  an action, run `console --errors`.
- If `reload` times out, `init.lua` errors before `require("hs.ipc")` runs, so the CLI
  can't connect. Run `restore`, then `restart`.

## 5. Report back

Say what was installed (the module path and the hotkey in symbols, e.g. `⌃⌥L`),
what you verified and how (the frames from `inventory`, the file the script wrote),
and how to undo it (`hsctl.py remove NAME`). If the user needs to do something
(grant Accessibility, press a key to try it), say exactly what.
