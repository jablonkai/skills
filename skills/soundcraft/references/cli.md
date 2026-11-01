# soundcraft-cli reference (0.16.0)

Every subcommand takes `--help`; the table below summarises them. Every subcommand exits non-zero with `soundcraft-cli: <message>` on stderr
on failure.

| Subcommand | Does |
|---|---|
| `info FILE [--compact]` | Audio file → JSON `{channels, format, frames, sample_format, sample_rate, seconds, bwf}`. `.scraft` → Pro Tools-style text: name, rate, depth, files, tracks with clip start/end/duration, markers. No plugins, pan, gain or automation. |
| `convert IN OUT [--bit-depth 16\|24\|32f] [--rate HZ] [--normalize] [--dither \| --no-dither]` | One file. Output format from OUT's extension (wav, aiff, flac). Dithers only when the output loses resolution unless told. `--normalize` → peak −0.1 dBFS. Prints `wrote OUT (N ch, RATE Hz, S s)`. **Overwrites OUT, even when OUT is IN.** |
| `run [--in S.scraft \| --demo] [--cmd ID[=JSON]]… [--bounce OUT] [--start T --end T] [--save S.scraft [--in-place]] [--inspect [--compact]]` | Opens a session (or a new empty one, or the demo), runs each `--cmd` in order, then bounces, saves, inspects. |
| `script FILE [--in S \| --demo] [--save S [--in-place]] [--keep-going] [--bounce OUT [--start T --end T]]` | Same (`--keep-going` reports a failing line and continues instead of stopping), with commands from FILE: one `ID JSON` per line (JSON optional), `#` comments and blank lines allowed. Without `--start/--end`, `--bounce` covers the whole session. |
| `commands [FILTER]` | Registry table: id, label, menu path. FILTER matches the row text. |
| `describe ID [--compact]` | JSON `{id, label, menu, shortcut, params, enabled, disabled_reason}`. `params` is a one-line signature; `enabled` reflects an empty session, so "nothing is selected" here is normal. |
| `plugins` | Built-in plugin ids, names, categories. Parameters: `sc_inspect.py plugin ID`. |
| `app [--port P] [--compact] METHOD [JSON]` | Calls a command on a running app's control port (default 7979, or `$SOUNDCRAFT_CONTROL_PORT`). See [live-app.md](live-app.md). |
| `mcp [--connect PORT] [--demo] [--automation-read-root DIR]… [--automation-write-root DIR]…` | MCP server on stdio. Roots confine every path commands read/write; a kind left out grants none. Roots conflict with `--connect`. |
| `parity [--write PATH]` | Markdown report of feature parity (informational). |

## Output of `run` / `script`

stdout, in order:

1. one line per command: `ID: <compact JSON result>`, e.g.
   `file.import_audio: {"imported":[{"channels":1,"clip":3,"frames":384000,"source":1,"track":2}]}`
2. `--bounce`: `{"bytes","lufs","path","peak_db","seconds","true_peak_db"}`
3. `--save`: `{"audio_files_written": N, "path": …}`
4. `--inspect`: pretty-printed `session.inspect` JSON

The first failing command aborts the run: `FILE:LINE: ID: bad parameters for …` (script)
or `soundcraft-cli: ID: …` (run). Nothing after it runs and nothing is saved.

## Time

- Command params: samples (int), or a `"m:ss.fff"` string where the signature says
  "position" (`at`, `start`, `end`). Fade `length` and `by` are samples only.
- `--start/--end` flags: seconds (`1.5`) or `m:ss.fff`. Not samples, and `1s` is rejected.
- Session rate comes from `session.new {"sample_rate"}` (default 48000); imports at
  another rate are converted on import and keep their duration.

## Formats

- Read: wav/bwf/rf64, aif(f/c), flac, mp1/mp2/mp3, ogg/oga, m4a/m4b/aac/mp4, caf, mkv/webm (`info` and `convert` list the same set).
- Bounce/convert write: wav, aiff, flac; bit depth 16, 24 or 32f.
- `file.bounce_mix` writes at the session rate; to deliver another rate, bounce then
  `convert --rate`.
