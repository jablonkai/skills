# Security posture

- **Headless only.** The skill runs `anicraft-cli` as a child process (`serve`, `exec`,
  `info`, `render`). No network port is opened and no running app is controlled, so
  the live-bridge requirements (token auth, cross-origin rejection, a stop path) do not
  apply. `mcp` is not used either; if a user wires it into an MCP client, that client's
  permissions decide what it may touch.
- **File access** is whatever paths the spec or command names: imports read them,
  `save_as` and exports write them. `ac_build.py` refuses to save over its source,
  resolves relative paths against the spec's folder, and only replaces an existing
  output with `--overwrite`.
- **Scripts in documents.** Frame actions and the ActionScript 3 subset run only in
  AniCraft's own interpreter (`control.test_movie`, the HTML export's player). Unsupported
  ActionScript is kept as text and not run (`script.check` → `runs`, `problems`). There is
  no file or network access from that subset. An exported HTML page runs the movie's
  scripts in the viewer's browser — treat HTML from untrusted `.anicraft` files like any
  other untrusted page.
- **Plug-ins** (WebAssembly) load only with `--plugins DIR` / `ANICRAFT_PLUGINS`. The
  skill never sets them unless the user asks, which also keeps runs repeatable.
- `ffmpeg` is run by the engine for video export; `ANICRAFT_FFMPEG` / the `ffmpeg` param
  choose which binary — don't point them at anything but a real ffmpeg.
