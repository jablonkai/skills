#!/usr/bin/env python3
"""Drive a running Hammerspoon from the command line through its hs CLI (hs.ipc).

    hsctl.py check                          app, version, hs binary, ipc, Accessibility,
                                            screens, config dir, agent modules (JSON)
    hsctl.py run (-e CODE | -f FILE | -) [--json] [--timeout S]
                                            run Lua in the live Hammerspoon; --json wraps
                                            the return values as JSON (userdata -> text)
    hsctl.py inventory [--all] [--ax-timeout S]
                                            screens, running apps and windows as JSON
    hsctl.py install NAME FILE [--keep-on-error]
                                            copy FILE to <config>/agent/NAME.lua, make sure
                                            init.lua loads agent modules, reload, report
                                            load errors (rolls back a failing module)
    hsctl.py remove NAME                    delete an agent module and reload
    hsctl.py list                           agent modules, their load state and exports,
                                            and every active hotkey
    hsctl.py call NAME FUNC [ARG ...]       call hsagent.modules.NAME.FUNC(ARG ...) -- run
                                            a hotkey's action without pressing the keys
    hsctl.py reload [--timeout S]           reload the config, wait for ipc, print errors
    hsctl.py console [--errors] [--all] [-n N]
                                            the Hammerspoon console since the last reload
    hsctl.py disable-all | enable-all       stop / start loading every agent module
    hsctl.py restore [--list] [--file F]    put back an init.lua backup
    hsctl.py enable-ipc [--restart]         add require("hs.ipc") to init.lua
    hsctl.py restart [--timeout S]          quit and relaunch Hammerspoon, wait for ipc

Exit codes: 0 ok, 1 usage or setup problem (Hammerspoon not running, no ipc, no
Accessibility), 2 Hammerspoon reported a Lua or load error, 3 timeout.

The skill adds no listener of its own: hs talks to Hammerspoon over a local Mach
message port that only processes of the same user can reach. Edits to init.lua are
confined to one marked block plus a require("hs.ipc") line, and every edit is
preceded by a backup in <config>/.agent-backups/.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

APP_CANDIDATES = [
    os.environ.get("HAMMERSPOON_APP", ""),
    "/Applications/Hammerspoon.app",
    os.path.expanduser("~/Applications/Hammerspoon.app"),
]
HS_IN_BUNDLE = "Contents/Frameworks/hs/hs"
BEGIN = "-- BEGIN agent modules"
END = "-- END agent modules"
IPC_RE = re.compile(r"""require\s*\(?\s*["']hs\.ipc["']""")
NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
NO_PORT = "can't access Hammerspoon message port"
KEEP_BACKUPS = 20

LOADER = BEGIN + """ (managed by the hammerspoon skill; modules live in agent/)
hsagent = { modules = {}, errors = {}, loadedAt = hs.timer.secondsSinceEpoch() }
do
  local dir = hs.configdir .. "/agent"
  if hs.fs.attributes(dir, "mode") == "directory" and not hs.fs.attributes(dir .. "/.disabled") then
    local names = {}
    for file in hs.fs.dir(dir) do
      local name = file:match("^([%l][%l%d_]*)%.lua$")
      if name then names[#names + 1] = name end
    end
    table.sort(names)
    for _, name in ipairs(names) do
      local chunk, err = loadfile(dir .. "/" .. name .. ".lua")
      local ok, mod = false, err
      if chunk then ok, mod = pcall(chunk) end
      if ok then
        hsagent.modules[name] = mod == nil and true or mod
      else
        hsagent.errors[name] = tostring(mod)
        print("*** ERROR: agent module '" .. name .. "' failed to load: " .. tostring(mod))
      end
    end
  end
  local previous = hs.shutdownCallback
  hs.shutdownCallback = function()
    for _, mod in pairs(hsagent.modules) do
      if type(mod) == "table" and type(mod.stop) == "function" then pcall(mod.stop) end
    end
    if previous then previous() end
  end
end
""" + END

# Turns any Lua value into something hs.json.encode accepts: geometry -> {x,y,w,h},
# userdata/functions -> their tostring(), sparse arrays -> string keys, depth-capped.
LUA_CLEAN = r"""
local function __clean(v, d)
  local t = type(v)
  if t == "nil" or t == "boolean" or t == "string" then return v end
  if t == "number" then if v ~= v or v == math.huge or v == -math.huge then return tostring(v) end return v end
  if t ~= "table" then return tostring(v) end
  if d > 8 then return "<table depth limit>" end
  if rawget(v, "_x") ~= nil and rawget(v, "_w") ~= nil then return v.table end
  if rawget(v, "_x") ~= nil and rawget(v, "_y") ~= nil then return { x = v.x, y = v.y } end
  local n, maxi, out = 0, 0, {}
  for k in pairs(v) do
    n = n + 1
    if math.type(k) == "integer" and k > 0 and k > maxi then maxi = k end
  end
  local isArray = n > 0 and maxi == n
  for k, val in pairs(v) do
    local key = isArray and k or tostring(k)
    local c = __clean(val, d + 1)
    if c ~= nil then out[key] = c end
  end
  return out
end
"""


def die(msg, code=1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def find_app():
    for path in APP_CANDIDATES:
        if path and os.path.isdir(path):
            return path
    return None


def find_hs():
    env = os.environ.get("HS_BIN")
    if env and os.access(env, os.X_OK):
        return env
    app = find_app()
    if app and os.access(os.path.join(app, HS_IN_BUNDLE), os.X_OK):
        return os.path.join(app, HS_IN_BUNDLE)
    return shutil.which("hs")


def app_version(app):
    try:
        out = subprocess.run(
            ["defaults", "read", os.path.join(app, "Contents/Info.plist"), "CFBundleShortVersionString"],
            capture_output=True, text=True, timeout=5)
        return out.stdout.strip() or None
    except (OSError, subprocess.TimeoutExpired):
        return None


def is_running():
    return subprocess.run(["pgrep", "-xq", "Hammerspoon"]).returncode == 0


def lua_long_string(text):
    level = 0
    while f"]{'=' * level}]" in text:
        level += 1
    eq = "=" * level
    return f"[{eq}[\n{text}]{eq}]"


def hs_raw(code, timeout=4.0):
    """Run code through hs -q. Returns (rc, stdout, stderr); rc 3 on our own timeout."""
    hs = find_hs()
    if not hs:
        die("hs CLI not found: install Hammerspoon (brew install --cask hammerspoon)")
    cmd = [hs, "-q", "-n", "-t", str(timeout), "-c", code]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5,
                           stdin=subprocess.DEVNULL)  # hs reads a piped stdin as code
    except subprocess.TimeoutExpired:
        return 3, "", "timeout: hs did not return"
    return p.returncode, p.stdout, p.stderr


def classify(rc, err):
    """Map an hs return code to (our exit code, message)."""
    if rc == 0:
        return 0, ""
    if NO_PORT in err:
        return 1, ("Hammerspoon is not running or hs.ipc is not loaded. "
                   "Run `hsctl.py check`; fix with `hsctl.py enable-ipc --restart`.")
    if rc == 65:
        return 2, err.strip()
    if rc == 3 or "receive timeout" in err or "send timeout" in err:
        return 3, ("timeout: Hammerspoon did not answer in time (the code may still be "
                   "running inside Hammerspoon; long jobs belong in hs.task or hs.timer)")
    return 2, err.strip() or f"hs exited {rc}"


def hs_eval(code, timeout=4.0):
    """Evaluate code, return the decoded JSON value of its first result; exits on error."""
    wrapped = (LUA_CLEAN + "local __f, __e = load(" + lua_long_string(code) + ", '=hsctl', 't')\n"
               "if not __f then error(__e, 0) end\n"
               "local __r = table.pack(__f())\n"
               "return hs.json.encode({ ok = true, v = __clean(__r[1], 0) })")
    rc, out, err = hs_raw(wrapped, timeout)
    code_, msg = classify(rc, err)
    if code_:
        die(msg, code_)
    try:
        return json.loads(out.strip() or "{}").get("v")
    except json.JSONDecodeError:
        die(f"unexpected hs output: {out[:300]!r}", 2)


def ping(timeout=2.0, tries=3):
    for attempt in range(tries):
        rc, out, _ = hs_raw('return "pong"', timeout)
        if rc == 0 and out.strip() == "pong":
            return True
        if attempt + 1 < tries:
            time.sleep(0.3)
    return False


def config_dir():
    if os.environ.get("HS_CONFIG_DIR"):
        return os.path.expanduser(os.environ["HS_CONFIG_DIR"])
    if ping():
        rc, out, _ = hs_raw("return hs.configdir")
        if rc == 0 and out.strip():
            return out.strip()
    return os.path.expanduser("~/.hammerspoon")


def init_path(cfg):
    return os.path.join(cfg, "init.lua")


def backup(path, cfg):
    if not os.path.exists(path):
        return None
    bdir = os.path.join(cfg, ".agent-backups")
    os.makedirs(bdir, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    dest = os.path.join(bdir, f"{os.path.basename(path)}.{stamp}")
    n = 1
    while os.path.exists(dest):
        dest = os.path.join(bdir, f"{os.path.basename(path)}.{stamp}-{n}")
        n += 1
    shutil.copy2(path, dest)
    same = sorted(f for f in os.listdir(bdir) if f.startswith(os.path.basename(path) + "."))
    for old in same[:-KEEP_BACKUPS]:
        os.remove(os.path.join(bdir, old))
    return dest


def read(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return ""


def write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def with_ipc(text):
    if IPC_RE.search(text):
        return text
    return 'require("hs.ipc")  -- hs CLI access (added by the hammerspoon skill)\n' + text


def with_loader(text):
    start, end = text.find(BEGIN), text.find(END)
    if start != -1 and end != -1 and end > start:
        return text[:start] + LOADER + text[end + len(END):]
    sep = "" if not text or text.endswith("\n\n") else ("\n" if text.endswith("\n") else "\n\n")
    return text + sep + LOADER + "\n"


def edit_init(cfg, ipc=True, loader=True):
    """Ensure the ipc line and the loader block; back up first. Returns True if changed."""
    path = init_path(cfg)
    old = read(path)
    new = old
    if ipc:
        new = with_ipc(new)
    if loader:
        new = with_loader(new)
    if new == old:
        return False
    os.makedirs(cfg, exist_ok=True)
    saved = backup(path, cfg)
    write(path, new)
    print(f"init.lua updated{f' (backup: {saved})' if saved else ''}", file=sys.stderr)
    return True


def console_since_reload(n=None, errors=False, everything=False):
    text = hs_eval("return hs.console.getConsole()") or ""
    if not everything:
        marks = [m.start() for m in re.finditer(r"-- Loading .*init\.lua", text)]
        if marks:
            line_start = text.rfind("\n", 0, marks[-1]) + 1
            text = text[line_start:]
    lines = text.splitlines()
    if errors:
        lines = error_lines(lines)
    if n:
        lines = lines[-n:]
    return lines


ERROR_RE = re.compile(r"\*\*\* ERROR|stack traceback|LuaSkin|attempt to |error:|\.lua:\d+:", re.I)


TIMESTAMP_RE = re.compile(r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d")


def error_lines(lines):
    out, keep = [], 0
    for line in lines:
        if ERROR_RE.search(line):
            out.append(line)
            keep = 6  # the traceback lines that follow
        elif keep and line.strip() and not TIMESTAMP_RE.match(line):
            out.append(line)
            keep -= 1
        else:
            keep = 0
    return out


def reload(timeout=10.0):
    """Reload via a timer (so the ipc reply is not cut off) and wait for the new state."""
    if not ping():
        die("Hammerspoon is not reachable over ipc; see `hsctl.py check`")
    rc, _, err = hs_raw('__hsctl_reload_pending = true; hs.timer.doAfter(0.2, hs.reload); return "ok"')
    code, msg = classify(rc, err)
    if code:
        die(msg, code)
    deadline = time.time() + timeout
    time.sleep(0.4)
    while time.time() < deadline:
        rc, out, _ = hs_raw("return tostring(__hsctl_reload_pending == nil)", 1.5)
        if rc == 0 and out.strip() == "true":
            return
        time.sleep(0.25)
    die("Hammerspoon did not come back after the reload. init.lua probably errors before "
        'require("hs.ipc") runs: look at the console window, then `hsctl.py restore` and '
        "`hsctl.py restart`.", 3)


STATE_LUA = r"""
local mods, errs = {}, {}
if hsagent then
  for name, mod in pairs(hsagent.modules) do
    local keys = {}
    if type(mod) == "table" then
      for k, v in pairs(mod) do keys[#keys + 1] = tostring(k) .. (type(v) == "function" and "()" or "") end
      table.sort(keys)
    end
    mods[name] = keys
  end
  for name, e in pairs(hsagent.errors) do errs[name] = e end
end
local hk = {}
for _, h in ipairs(hs.hotkey.getHotkeys()) do hk[#hk + 1] = h.idx end
return { loader = hsagent ~= nil, modules = mods, errors = errs, hotkeys = hk }
"""


def agent_state():
    return hs_eval(STATE_LUA)


def report_after_reload(name=None):
    state = agent_state() or {}
    errs = console_since_reload(errors=True)
    out = {"modules": state.get("modules") or {}, "errors": state.get("errors") or {},
           "hotkeys": state.get("hotkeys") or [], "console_errors": errs}
    print(json.dumps(out, indent=2, ensure_ascii=False))
    failed = bool(out["errors"]) if name is None else name in out["errors"]
    return failed or (name is None and bool(errs)), out


# ---------------------------------------------------------------- subcommands

def cmd_check(args):
    app = find_app()
    hs = find_hs()
    info = {
        "app": app, "version": app_version(app) if app else None, "running": is_running(),
        "hs_cli": hs, "ipc": False, "accessibility": None, "screens": None,
        "config_dir": None, "init_has_ipc": None, "loader_installed": None, "agent_modules": None,
    }
    problems = []
    if not app:
        problems.append("Hammerspoon is not installed: brew install --cask hammerspoon")
    elif not info["running"]:
        problems.append("Hammerspoon is not running: open -a Hammerspoon")
    if info["running"] and hs:
        info["ipc"] = ping()
    cfg = config_dir()
    init = read(init_path(cfg))
    info.update(config_dir=cfg, init_has_ipc=bool(IPC_RE.search(init)), loader_installed=BEGIN in init)
    agent_dir = os.path.join(cfg, "agent")
    if os.path.isdir(agent_dir):
        info["agent_modules"] = sorted(f[:-4] for f in os.listdir(agent_dir) if f.endswith(".lua"))
        info["agent_disabled"] = os.path.exists(os.path.join(agent_dir, ".disabled"))
    if info["running"] and not info["ipc"]:
        problems.append("hs.ipc is not loaded: `hsctl.py enable-ipc --restart` (ask the user first)")
    if info["ipc"]:
        v = hs_eval("return { ax = hs.accessibilityState(), screens = #hs.screen.allScreens(),"
                    " version = hs.processInfo.version }")
        info.update(accessibility=v["ax"], screens=v["screens"], version=v["version"])
        if not v["ax"]:
            problems.append("Accessibility is not granted: the user must enable Hammerspoon in System "
                            "Settings > Privacy & Security > Accessibility (windows and keystrokes "
                            "do not work until then)")
    info["problems"] = problems
    print(json.dumps(info, indent=2))
    return 1 if problems else 0


def read_code(args):
    if args.e is not None:
        return args.e
    if args.f == "-" or (args.f is None):
        return sys.stdin.read()
    return read(args.f) or die(f"cannot read {args.f}")


def cmd_run(args):
    code = read_code(args)
    if args.json:
        print(json.dumps(hs_eval(code, args.timeout), indent=2, ensure_ascii=False))
        return 0
    rc, out, err = hs_raw(code, args.timeout)
    sys.stdout.write(out)
    code_, msg = classify(rc, err)
    if code_:
        print(msg, file=sys.stderr)
    return code_


INVENTORY_LUA = r"""
local all = ...
-- An unresponsive app makes every Accessibility query wait for it (default ~6 s per
-- call, so a full window list can stall for minutes); cap it.
hs.window.timeout(AX_TIMEOUT)
local screens, apps, wins = {}, {}, {}
local primary = hs.screen.primaryScreen()
for _, s in ipairs(hs.screen.allScreens()) do
  screens[#screens + 1] = { id = s:id(), name = s:name(), uuid = s:getUUID(),
    frame = s:frame().table, fullFrame = s:fullFrame().table, primary = s == primary }
end
local focused = hs.window.focusedWindow()
local list = all and hs.window.allWindows() or hs.window.visibleWindows()
for _, w in ipairs(list) do
  if all or w:isStandard() then
    local app, scr = w:application(), w:screen()
    wins[#wins + 1] = { id = w:id(), app = app and app:name() or "?",
      bundleID = app and app:bundleID() or nil, title = w:title(),
      screen = scr and scr:name() or nil, screenId = scr and scr:id() or nil,
      frame = w:frame().table, standard = w:isStandard(), minimized = w:isMinimized(),
      fullscreen = w:isFullScreen(), focused = focused ~= nil and w:id() == focused:id() }
  end
end
for _, a in ipairs(hs.application.runningApplications()) do
  if all or a:kind() == 1 then
    apps[#apps + 1] = { name = a:name(), bundleID = a:bundleID(), pid = a:pid(),
      hidden = a:isHidden(), frontmost = a:isFrontmost(), windows = #a:allWindows() }
  end
end
table.sort(apps, function(x, y) return (x.name or "") < (y.name or "") end)
return { screens = screens, apps = apps, windows = wins, accessibility = hs.accessibilityState() }
"""


def cmd_inventory(args):
    code = INVENTORY_LUA.replace("local all = ...", f"local all = {'true' if args.all else 'false'}")
    code = code.replace("AX_TIMEOUT", repr(float(args.ax_timeout)))
    print(json.dumps(hs_eval(code, 30), indent=2, ensure_ascii=False))
    return 0


def cmd_install(args):
    if not NAME_RE.match(args.name):
        die("module NAME must be lowercase letters, digits and _ and start with a letter")
    src = os.path.abspath(args.file)
    if not os.path.isfile(src):
        die(f"no such file: {args.file}")
    if not ping():
        die("Hammerspoon is not reachable over ipc; see `hsctl.py check`")
    syntax = hs_eval(f"local f, e = loadfile({lua_long_string(src)}); return e")
    if syntax:
        die(f"syntax error: {syntax}", 2)
    body = read(src)
    if re.search(r"\bhs\.execute\s*\(", body):
        print("warning: hs.execute blocks Hammerspoon until the command exits; "
              "use hs.task for anything slow", file=sys.stderr)
    if not re.search(r"^\s*return\b", body, re.M):
        print("warning: the module returns nothing; return a table (with stop() and its "
              "actions) so its objects stay referenced and it can be called by name",
              file=sys.stderr)
    cfg = config_dir()
    agent_dir = os.path.join(cfg, "agent")
    os.makedirs(agent_dir, exist_ok=True)
    dest = os.path.join(agent_dir, args.name + ".lua")
    previous = backup(dest, cfg)
    edit_init(cfg)
    shutil.copyfile(src, dest)
    reload(args.timeout)
    failed, _ = report_after_reload(args.name)
    if failed and not args.keep_on_error:
        if previous:
            shutil.copyfile(previous, dest)
            note = "previous version restored"
        else:
            os.remove(dest)
            note = "module removed"
        reload(args.timeout)
        die(f"module '{args.name}' failed to load; {note} (use --keep-on-error to keep it)", 2)
    if failed:
        return 2
    print(f"installed {dest}", file=sys.stderr)
    return 0


def cmd_remove(args):
    cfg = config_dir()
    dest = os.path.join(cfg, "agent", args.name + ".lua")
    if not os.path.exists(dest):
        die(f"no agent module named {args.name}")
    saved = backup(dest, cfg)
    os.remove(dest)
    print(f"removed {dest} (backup: {saved})", file=sys.stderr)
    reload(args.timeout)
    report_after_reload()
    return 0


def cmd_list(args):
    cfg = config_dir()
    agent_dir = os.path.join(cfg, "agent")
    files = sorted(f[:-4] for f in os.listdir(agent_dir) if f.endswith(".lua")) if os.path.isdir(agent_dir) else []
    state = agent_state() if ping() else None
    print(json.dumps({"config_dir": cfg, "files": files,
                      "disabled": os.path.exists(os.path.join(agent_dir, ".disabled")),
                      "live": state}, indent=2, ensure_ascii=False))
    return 0


def cmd_call(args):
    argv = ", ".join(lua_long_string(a) if not re.fullmatch(r"-?\d+(\.\d+)?|true|false|nil", a) else a
                     for a in args.args)
    code = (f"local m = hsagent and hsagent.modules[{json.dumps(args.name)}]\n"
            f"if type(m) ~= 'table' then error('agent module {args.name} is not loaded', 0) end\n"
            f"local fn = m[{json.dumps(args.func)}]\n"
            f"if type(fn) ~= 'function' then error('{args.name}.{args.func} is not a function', 0) end\n"
            f"return fn({argv})")
    print(json.dumps(hs_eval(code, args.timeout), indent=2, ensure_ascii=False))
    return 0


def cmd_reload(args):
    reload(args.timeout)
    failed, _ = report_after_reload()
    return 2 if failed else 0


def cmd_console(args):
    lines = console_since_reload(args.n, args.errors, args.all)
    print("\n".join(lines))
    return 2 if args.errors and lines else 0


def cmd_disable(args, on):
    cfg = config_dir()
    agent_dir = os.path.join(cfg, "agent")
    os.makedirs(agent_dir, exist_ok=True)
    flag = os.path.join(agent_dir, ".disabled")
    if on:
        open(flag, "w").close()
    elif os.path.exists(flag):
        os.remove(flag)
    if ping():
        reload(args.timeout)
        report_after_reload()
    return 0


def cmd_restore(args):
    cfg = config_dir()
    bdir = os.path.join(cfg, ".agent-backups")
    backups = sorted(f for f in os.listdir(bdir) if f.startswith("init.lua.")) if os.path.isdir(bdir) else []
    if args.list:
        print("\n".join(os.path.join(bdir, b) for b in backups))
        return 0
    src = args.file or (os.path.join(bdir, backups[-1]) if backups else None)
    if not src or not os.path.isfile(src):
        die("no init.lua backup to restore")
    saved = backup(init_path(cfg), cfg)
    shutil.copyfile(src, init_path(cfg))
    print(f"restored {src} -> init.lua (the replaced file is saved as {saved})", file=sys.stderr)
    if ping():
        reload(args.timeout)
        report_after_reload()
    else:
        print("ipc is down: run `hsctl.py restart` to load the restored config", file=sys.stderr)
    return 0


def restart(timeout):
    subprocess.run(["osascript", "-e", 'tell application "Hammerspoon" to quit'],
                   capture_output=True, timeout=15)
    for _ in range(40):
        if not is_running():
            break
        time.sleep(0.25)
    else:
        subprocess.run(["pkill", "-x", "Hammerspoon"])
        time.sleep(1)
    subprocess.run(["open", "-g", "-a", find_app() or "Hammerspoon"], check=False)
    deadline = time.time() + timeout
    while time.time() < deadline:
        if ping(1.5):
            return True
        time.sleep(0.4)
    return False


def cmd_restart(args):
    if not restart(args.timeout):
        die("Hammerspoon started but ipc did not answer: init.lua lacks require(\"hs.ipc\") "
            "or fails before it (see the console window)", 3)
    report_after_reload()
    return 0


def cmd_enable_ipc(args):
    cfg = config_dir()
    changed = edit_init(cfg, ipc=True, loader=False)
    if ping():
        print("ipc already answering", file=sys.stderr)
        return 0
    if not changed:
        print("init.lua already loads hs.ipc", file=sys.stderr)
    if args.restart:
        return cmd_restart(args)
    print("restart Hammerspoon to load it: `hsctl.py restart`", file=sys.stderr)
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    r = sub.add_parser("run")
    g = r.add_mutually_exclusive_group()
    g.add_argument("-e", metavar="CODE")
    g.add_argument("-f", metavar="FILE", help="Lua file, or - for stdin")
    r.add_argument("--json", action="store_true")
    r.add_argument("--timeout", type=float, default=10)
    i = sub.add_parser("inventory")
    i.add_argument("--all", action="store_true", help="include non-standard, minimized and background")
    i.add_argument("--ax-timeout", type=float, default=1.0,
                   help="seconds to wait for an unresponsive app (hs.window.timeout), default 1")
    ins = sub.add_parser("install")
    ins.add_argument("name")
    ins.add_argument("file")
    ins.add_argument("--keep-on-error", action="store_true")
    ins.add_argument("--timeout", type=float, default=10)
    rm = sub.add_parser("remove")
    rm.add_argument("name")
    rm.add_argument("--timeout", type=float, default=10)
    sub.add_parser("list")
    c = sub.add_parser("call")
    c.add_argument("name")
    c.add_argument("func")
    c.add_argument("args", nargs="*")
    c.add_argument("--timeout", type=float, default=10)
    rl = sub.add_parser("reload")
    rl.add_argument("--timeout", type=float, default=10)
    co = sub.add_parser("console")
    co.add_argument("--errors", action="store_true")
    co.add_argument("--all", action="store_true", help="whole console, not just since the last reload")
    co.add_argument("-n", type=int)
    for name in ("disable-all", "enable-all"):
        d = sub.add_parser(name)
        d.add_argument("--timeout", type=float, default=10)
    rs = sub.add_parser("restore")
    rs.add_argument("--list", action="store_true")
    rs.add_argument("--file")
    rs.add_argument("--timeout", type=float, default=10)
    ei = sub.add_parser("enable-ipc")
    ei.add_argument("--restart", action="store_true")
    ei.add_argument("--timeout", type=float, default=15)
    rst = sub.add_parser("restart")
    rst.add_argument("--timeout", type=float, default=15)
    args = p.parse_args()
    handlers = {
        "check": cmd_check, "run": cmd_run, "inventory": cmd_inventory, "install": cmd_install,
        "remove": cmd_remove, "list": cmd_list, "call": cmd_call, "reload": cmd_reload,
        "console": cmd_console, "disable-all": lambda a: cmd_disable(a, True),
        "enable-all": lambda a: cmd_disable(a, False), "restore": cmd_restore,
        "enable-ipc": cmd_enable_ipc, "restart": cmd_restart,
    }
    sys.exit(handlers[args.cmd](args))


if __name__ == "__main__":
    main()
