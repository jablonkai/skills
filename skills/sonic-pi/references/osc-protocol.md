# Sonic Pi 5 OSC protocol

This page is for anything `sp.py` does not wrap. Source:
`Sonic Pi.app/Contents/Resources/app/server/ruby/bin/{daemon.rb,spider-server.rb}`
and the headless harnesses next to them (`headless_boot.rb`, `headless-run.rb`,
`headless-record.rb`, `repl.rb`; `headless-record.rb` is broken on 5.0.0, see
below). All traffic is OSC over UDP on localhost.

## Processes

| Process | Role |
|---------|------|
| `daemon.rb` (bundled Ruby) | picks free ports, makes a token, spawns the others, kill switch |
| `spider-server.rb` | evaluates code, sends logs and errors to the client |
| `Sonic Pi - SuperSonic` | the audio engine (replaces scsynth in v5), TCP on 127.0.0.1 |

## Boot handshake

1. Run `<app>/Contents/Resources/app/server/native/ruby/bin/ruby
   <app>/Contents/Resources/app/server/ruby/bin/daemon.rb`.
2. Read its **first stdout line**, which holds six integers:
   `daemon-port gui-listen gui-send engine-port cues-port token`.
3. Bind UDP `gui-listen` to receive the spider's messages.
4. Every 1–4 s, send `/daemon/keep-alive <token>` to `daemon-port`. Without it, the
   daemon exits after about 90 s (40 s grace plus 5 × 10 s windows).
5. Send `/ping <token> <id>` to `gui-send` until `/ack <id>` arrives. The engine is
   ready when `/log/info` contains "Live Coding begin" or `/supersonic/info`
   arrives.
6. To end: send `/daemon/exit <token>` to `daemon-port`, which kills the spider and
   the engine.

The daemon also accepts `--no-scsynth-inputs`, `--audio-output DEV`,
`--audio-input DEV`, `--audio-sample-rate N` and `--audio-buffer-size N`.

## Attaching to the GUI's session

The GUI spawns the daemon itself. Its values are visible only in the spider's
arguments: `spider-server.rb -u <gui-send> <gui-listen> <engine> <engine-send>
<cues> <token>`. They are also written to `~/.sonic-pi/log/daemon.log`, but only
when the GUI exits. The GUI already binds `gui-listen`, so an attached client can
send messages but receives no replies.

## Client → spider (`gui-send`), first argument always the token

| Path | Args after token | Effect |
|------|------------------|--------|
| `/run-code` | code (string) [, workspace, silent] | evaluate code as a new run |
| `/stop-all-jobs` | — | stop every run and loop |
| `/stop-job` | job id (int) | stop one run |
| `/ping` | id | replies `/ack id` |
| `/start-recording` | — | start the built-in recorder (temp file) |
| `/stop-recording` | — | stop it |
| `/save-recording` | absolute path | move the take there (48 kHz s24 stereo WAV) |
| `/delete-recording` | — | discard the take |
| `/mixer-output-volume` | float, int | output fader (0 mutes, and also mutes takes) |
| `/exit` | — | stop the spider |

There are more endpoints for buffers and the mixer (`/save-and-run-buffer`,
`/mixer-hpf-enable`, …). List them with
`grep -n 'add_method("/' spider-server.rb`.

## Spider → client (`gui-listen`)

| Path | Args |
|------|------|
| `/log/multi_message` | run id, thread name, time, count, then (kind, text) pairs; kind 1 = `puts` |
| `/log/info` | style, text |
| `/error` | run id, message (HTML-ish), backtrace, line (−1 if unknown) |
| `/syntax_error` | run id, message, offending code line, line (int), line (string), column start, column end |
| `/run/started`, `/run/ended` | run id |
| `/ack` | ping id |
| `/spider/ready`, `/link-bpm`, `/supersonic/*` | status (forwarded by the daemon too) |

`sp.py` writes every non-GUI message as one JSON line per message to
`$TMPDIR/sonic-pi-skill/session.jsonl`: `{"t": epoch, "path": ..., "args": [...]}`.

## Engine (`engine-port`) direct

On 5.0.0 the engine listens on **TCP only** (127.0.0.1),
although the daemon passes it `-u <port>`. A UDP send gets "connection refused".
That is why the bundled `headless-record.rb`, which sends
`/supersonic/record/start <path> wav 24` over UDP, writes no file on 5.0.0.

Record through the spider instead (`/start-recording`, `/stop-recording`,
`/save-recording`), as `sp.py` does. The recorder tap sits after the main mixer, so
a muted mixer records silence.

## Incoming OSC from other apps (`cues-port`, default 4560)

Other programs can send OSC to port 4560. Code receives it with
`sync "/osc*/some/path"`, and `get "/osc*/some/path"` reads the last value. This is
how external controllers or data streams drive a running piece. It needs no token.
