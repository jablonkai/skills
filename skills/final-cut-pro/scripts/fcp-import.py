#!/usr/bin/env python3
"""Import an FCPXML into Final Cut Pro and confirm it through FCP's AppleScript model.

  fcp-import.py cut.fcpxml [--library ~/Movies/Scratch.fcpbundle] [--timeout 120]

1. DTD-validates the file (refuses an invalid one) and reads the projects it defines.
2. `open -b com.apple.FinalCut FILE` (launches FCP if needed).
3. Polls until every project shows up as a *new* project in FCP's read-only AppleScript
   model, then compares each project's duration with the file's sequence duration.
4. Meanwhile, through System Events (Accessibility):
   - "Import XML" warnings dialog → the warnings are captured and the dialog closed.
     A warning means FCP dropped or changed something: the run fails.
   - "Open Library" chooser (the file has no `library location` import option) → the
     row named like --library is chosen; without --library the run stops and says so.
   Only buttons are pressed — never keystrokes — so nothing can land in another app.
5. Refuses up front when an open library already has the file's event with a project of
   the same name: FCP would merge the events and silently keep only the old project.

Stop path: every wait ends at --timeout; FCP is never quit and nothing is deleted.
"""
import argparse
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fcptime import fmt_time, parse_time  # noqa: E402
from fcpxml_common import (FcpError, app_running, emit, find_app, list_projects, load,  # noqa: E402
                           projects, url_to_path, xmllint)

UI_SCRIPT = r'''
on run argv
  set libName to item 1 of argv
  tell application "System Events"
    if not (exists process "Final Cut Pro") then return "none"
    tell process "Final Cut Pro"
      if exists window "Import XML" then
        set w to window "Import XML"
        set msgs to ""
        try
          repeat with r in rows of outline 1 of scroll area 1 of w
            repeat with st in static texts of r
              set msgs to msgs & (value of st) & linefeed
            end repeat
            try
              repeat with st in static texts of group 1 of r
                set msgs to msgs & (value of st) & linefeed
              end repeat
            end try
          end repeat
        end try
        click button "OK" of w
        return "warnings" & linefeed & msgs
      end if
      if exists window "Open Library" then
        if libName is "" then return "chooser"
        set t to table 1 of scroll area 1 of window "Open Library"
        repeat with i from 1 to count of rows of t
          if value of text field 1 of row i of t is libName then
            set selected of row i of t to true
            delay 0.3
            click button "Choose" of window "Open Library"
            return "chose"
          end if
        end repeat
        return "chooser-no-match"
      end if
    end tell
  end tell
  return "none"
end run
'''


def ui_step(lib_name):
    try:
        r = subprocess.run(["osascript", "-e", UI_SCRIPT, lib_name], capture_output=True,
                           text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return "timeout", ""
    if r.returncode != 0:
        if "-1719" in r.stderr or "-25211" in r.stderr or "assistive" in r.stderr.lower():
            return "no-accessibility", r.stderr.strip()
        return "error", r.stderr.strip()
    head, _, rest = r.stdout.partition("\n")
    return head.strip(), rest.strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--library", help=".fcpbundle to pick if FCP asks which library to use")
    ap.add_argument("--timeout", type=float, default=float(os.environ.get("FCP_TIMEOUT", 120)))
    ap.add_argument("--no-validate", action="store_true")
    ap.add_argument("--allow-existing", action="store_true",
                    help="import even if the event already has a project with the same name")
    a = ap.parse_args()
    t0 = time.time()
    try:
        if not find_app():
            raise FcpError("Final Cut Pro not found")
        root = load(a.file)
        version = root.get("version")
        if not a.no_validate:
            ok, msgs = xmllint(a.file, version)
            if not ok:
                emit({"ok": False, "error": "not valid against the FCPXML DTD", "dtd_errors": msgs[:20]})
                return 1
        want = []
        for ev, pr in projects(root):
            seq = pr.find("sequence")
            want.append({"event": ev, "project": pr.get("name"),
                         "duration": parse_time(seq.get("duration", "0s")) if seq is not None else None})
        if not want:
            raise FcpError("the file defines no project (only clips/events are not checked)")
        before = set()
        if app_running():
            live = list_projects()
            before = {p["id"] for p in live}
            # FCP imports into a temporary "<event> 2", merges it into the same-named event
            # in the background, and silently discards any project whose name already exists
            # there (verified on 12.4: the old project stays, nothing is reported).
            target = None
            for o in root.findall("import-options/option"):
                if o.get("key") == "library location":
                    target = (url_to_path(o.get("value", "")) or "").rstrip("/") or None
            clash = [w for w in want if any(
                p["project"] == w["project"] and p["event"] == w["event"]
                and (target is None or p["library_file"] in (None, target)) for p in live)]
            if clash and not a.allow_existing:
                emit({"ok": False, "error": "FCP would silently drop these projects: an event with "
                      "the same name already has a project with the same name — give the project "
                      "(or the event) a new name",
                      "clashes": [f"{w['event']} / {w['project']}" for w in clash]})
                return 1
        lib_name = ""
        if a.library:
            lib_name = os.path.splitext(os.path.basename(os.path.abspath(os.path.expanduser(
                a.library)).rstrip("/")))[0]
        r = subprocess.run(["open", "-b", "com.apple.FinalCut", os.path.abspath(a.file)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise FcpError(f"open failed: {r.stderr.strip()}")

        warnings, notes, found = [], [], {}
        ui_ok = True
        deadline = t0 + a.timeout
        while time.time() < deadline:
            time.sleep(1.5)
            if not app_running():
                continue
            if ui_ok:
                state, text = ui_step(lib_name)
                if state == "warnings":
                    warnings += [ln for ln in text.splitlines() if ln.strip()
                                 and not ln.endswith((".fcpxml", ".fcpxmld"))]
                elif state == "chose":
                    notes.append(f"picked library {lib_name!r} in FCP's chooser")
                elif state in ("chooser", "chooser-no-match"):
                    emit({"ok": False, "error": "FCP is asking which library to import into and "
                          + ("no --library was given" if state == "chooser" else
                             f"no open-recent row is named {lib_name!r}")
                          + "; pick one in FCP (the dialog is left open), or rebuild with "
                            "--library so the file carries a library location",
                          "seconds": round(time.time() - t0, 1)})
                    return 1
                elif state == "no-accessibility":
                    ui_ok = False
                    notes.append("no Accessibility permission for System Events: import dialogs "
                                 "are not watched (System Settings ▸ Privacy & Security ▸ "
                                 "Accessibility ▸ your terminal)")
            try:
                now = list_projects()
            except FcpError as e:
                notes.append(str(e))
                continue
            for w in want:
                key = (w["event"], w["project"])
                if key in found:
                    continue
                for p in now:
                    if p["id"] in before:
                        continue
                    if p["project"] == w["project"] or p["project"].startswith(w["project"] + " "):
                        if w["event"] in (None, p["event"]) or p["event"].startswith(str(w["event"])):
                            found[key] = p
                            break
            if len(found) == len(want):
                time.sleep(1.0)
                if ui_ok:  # a warnings dialog can appear just after the project
                    state, text = ui_step(lib_name)
                    if state == "warnings":
                        warnings += [ln for ln in text.splitlines() if ln.strip()
                                     and not ln.endswith((".fcpxml", ".fcpxmld"))]
                break
        out = []
        ok = True
        for w in want:
            p = found.get((w["event"], w["project"]))
            row = {"event": w["event"], "project": w["project"],
                   "expected_duration": fmt_time(w["duration"]) if w["duration"] is not None else None}
            if p is None:
                row["imported"] = False
                ok = False
            else:
                got = parse_time(p["duration"])
                row.update(imported=True, fcp_name=p["project"], library=p["library"],
                           library_file=p["library_file"], duration=p["duration"],
                           seconds=p["seconds"],
                           duration_match=(w["duration"] is None or got == w["duration"]))
                if p["project"] != w["project"]:
                    row["renamed"] = True
                ok = ok and row["duration_match"]
            out.append(row)
        if warnings:
            ok = False
        res = {"ok": ok, "file": a.file, "version": version, "projects": out,
               "warnings": warnings, "notes": notes, "seconds": round(time.time() - t0, 1)}
        if not found and time.time() >= deadline:
            res["error"] = f"no new project appeared within {a.timeout:.0f}s"
        emit(res)
        return 0 if ok else 1
    except FcpError as e:
        emit({"ok": False, "error": str(e)})
        return 1


if __name__ == "__main__":
    sys.exit(main())
