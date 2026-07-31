# WebSocket Control — protocol details

Rebelle 8 **Pro** ships a WebSocket server for live remote control (interactive
installations, live performance, and — for us — driving the app the user has open).
The [manual page](https://www.escapemotions.com/products/rebelle/motionio_doc/) says
"send any JSON event mentioned in the Rebelle Motion IO reference"; everything below
was additionally established against the installed 8.3.0 build, because a second,
undocumented command family lives on the same socket and it is where canvas export and
preset discovery live.

## Starting the server

```bash
"/Applications/Rebelle 8.app/Contents/MacOS/Rebelle 8" \
  -websocket-server-enable \
  -websocket-port 8265 \
  -websocket-allowed-ip-addresses "::ffff:127.0.0.1,127.0.0.1"
```

Defaults: disabled, port 8265. Without `-websocket-allowed-ip-addresses` any host that
can reach the port may drive the app — keep it local unless the user asks otherwise.
Rebelle logs `WebsocketServer client address '...' accepted|refused` per connection.

The allowlist compares literal peer addresses, and a loopback client shows up as
`::ffff:127.0.0.1`, so an allowlist of just `127.0.0.1` refuses your own connection —
the handshake succeeds and Rebelle then closes the socket. Include both forms.

The server exists only in **Pro**. On connect it sends a greeting line such as
`Rebelle 8 Pro here`, which is a cheap way to confirm both the version and the edition.

## Message shapes

Plain RFC 6455 text frames, one JSON object each. Two families:

| Shape | Purpose |
|---|---|
| `{"event_type": "...", ...}` | the documented Motion IO events (see [json-events.md](json-events.md)) |
| `{"cmd": "...", ...}` | app-level control: discovery, export, zoom (undocumented) |

Most messages get no reply at all. Errors come back as `{error:'...'}` — note that some
are not valid JSON (unquoted key), so parse defensively. An unknown `cmd`, or a `cmd`
with the wrong parameter names, is answered with `{error:'missing parameter: '}` — the
name is left blank, so parameter discovery is trial and error.

Because success is silent, `BOOKMARK` is the workhorse: it is echoed back
(`{"id":"..."}`) when the queue reaches it, which makes it both an acknowledgement and
an ordering guarantee. `scripts/rebelle_ws.py` exposes this as `sync()`.

## Verified `cmd` commands

| Command | Parameters | Result |
|---|---|---|
| `list_tools` | – | JSON array of tool names in UI order; the array index is the `id` used by `select_tool` (empty strings are separators) |
| `list_tool_presets` | – (a `tool` parameter is accepted but ignored) | preset paths of the **currently selected** tool, e.g. `"Watercolor/Round"` — exactly the strings `SET_BRUSH` wants |
| `select_tool` | `id` (integer index into `list_tools`) | switches tool; the list it returns is refreshed lazily, so don't use it to enumerate another tool's presets — read the folders instead ([assets.md](assets.md)) |
| `select_tool_preset` | `name` | replies `{"error":"Preset X was not found for the current tool."}` when it does not match |
| `export_canvas` | `filename` (absolute) | writes the composited canvas (paper + layers + bump shading) as PNG/JPG |
| `set_color` | `hex` (e.g. `"#0AC80A"`) | palette colour |
| `set_brush_paint_param` | `name`, `value` | single brush parameter |
| `set_zoom` | `zoom_percent` | viewport zoom (display only) |
| `clear_canvas` | – | clears the artwork |
| `pointer_event` | wraps a `POINTER_*` event: `{"cmd":"pointer_event","event_type":"POINTER_MOVE","pos":{…}}` | same effect as sending the bare event |

`new_artwork`, `set_paper` and `set_main_window` (`main_menu_visible`) exist but their
parameter names did not fall out of probing — use the `NEW_ARTWORK` / `SET_PAPER`
events instead, which work fine live.

## Behaviour notes

- **`SAVE`/`LOAD` events are rejected** ("aren't supported via Websockets yet") even
  though the docs claim 8.3 support. `export_canvas` is the way to get pixels out.
  16-bit output and `reveal_mask` are likewise Motion-IO-only.
- **`NEW_ARTWORK` works live** — unlike in batch — and replaces whatever the user has
  open, without asking. Confirm before sending it at an artwork you did not create.
- Pointer events work both bare and wrapped in `pointer_event`; bare is simpler.
- Right after the app finishes launching there is a window where events are accepted but
  the artwork is still being initialised, and painting can land on a canvas that is then
  re-created. Export once and look at the result before trusting a long sequence.
- The app keeps painting while you are connected; there is no undo grouping, so a
  mistake is the user's history to clean up.
