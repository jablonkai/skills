# The running app and MCP

The headless CLI is the default. Use these only when the user wants to watch the
edits in PdfCraft's window, or wants PdfCraft's tools as an MCP server.

## Driving a running app (`ui --control`)

PdfCraft's own control channel. This skill ships no bridge of its own.

```sh
C=$PWD/pdfcraft-control.json
/Applications/PdfCraft.app/Contents/MacOS/PdfCraft --control "$C" &   # opens the window
until [ -s "$C" ]; do sleep 0.5; done
bash $S/pf.sh ui --control "$C" open path="$PWD/report.pdf"
bash $S/pf.sh ui --control "$C" commands                 # menu commands, enabled state
bash $S/pf.sh ui --control "$C" command id=page.rotate
bash $S/pf.sh ui --control "$C" screenshot --out shot.png
bash $S/pf.sh ui --control "$C" quit                     # stop path
rm -f "$C"
```

- **Save before `quit`.** With unsaved changes it answers
  `{"needs_confirmation": true, "quitting": false}`. In 0.15.0 testing, the app
  still exited about 3 s later and the changes were lost.

- Methods (0.15.0): `state`, `inspect`, `click`, `focus`, `resize`, `move`,
  `drag`, `type`, `key`, `command`, `commands`, `set`, `open`, `screenshot`,
  `quit`. An unknown method lists them.
- `open` returns `pending: true`. Poll `state` until `active` is non-null
  (it carries `doc`, `page`, `zoom_percent`) before sending commands.
- `command id=<registry id>` runs a menu command on the active document
  (`{"ran": "page.rotate"}`). `pf_tool.py --commands WORD` lists the ids.
- **Security posture:** the app writes `{pid, port, token}` to FILE with mode
  600 and listens on `127.0.0.1` only. `ui` sends the token. It is a raw TCP
  protocol, not HTTP, so a browser page can't reach it cross-origin. Anyone who
  can read FILE can drive the app, so keep FILE in a private folder and delete
  it after `quit`.
- Verify the result from the saved file with the usual read-back (`pf_verify.py`).
  A screenshot only shows the window.

## MCP server

```sh
bash $S/pf.sh mcp --compact \
     --automation-read-root "$PWD/in" --automation-write-root "$PWD/out"
```

- stdio MCP server with the same 179 tools. `--compact` lists a core set plus
  `tool_search` and `tool_call`.
- `--automation-read-root` / `--automation-write-root` confine what the tools
  may open and write (links followed). **A root left out grants no access of
  that kind.** That is the sandboxed option when an MCP client, not this skill,
  is in control. Register it in the client's MCP config. Don't start it from a
  task: it waits on stdin.
