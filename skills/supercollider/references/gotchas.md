# Gotchas

Each of these was hit while building or testing this skill on SuperCollider 3.14.1 /
macOS.

## Headless and processes

- **Don't set `QT_QPA_PLATFORM=offscreen`.** The macOS bundle ships only the `cocoa`
  Qt plugin, so sclang aborts at start with *Could not find the Qt platform plugin
  "offscreen"*. Plain `sclang` already runs without a window.
- **sclang does not exit on an error inside a Routine or `fork`.** The error is
  printed, then the process waits forever. A script that ends with `0.exit` inside a
  routine therefore hangs when anything before it fails. `render` has a watchdog
  (`--timeout`, default 300 s) and kills the whole process group, exit 3.
- **The exit code is 0 even after `ERROR:` lines** unless the script calls `1.exit`.
  `sc.py` decides success by parsing the post window, so trust its exit code, not
  sclang's.
- **`exit` does not stop evaluation.** Code after `1.exit` in the same block still
  runs. To bail out, throw (`Error("why").throw`) and catch it once.
- **Orphaned scsynth:** killing an sclang that booted a server leaves `scsynth`
  running. It holds the port and the audio device. `sc.py shutdown` and `sc.py start`
  kill the scsynth the session recorded. To find others:
  `pgrep -fl 'scsynth -u'` — but never kill the SC IDE's (`sclang -i scqt` and its
  server on 57110) without asking.
- **startup.scd runs first.** Every sclang run executes
  `~/Library/Application Support/SuperCollider/startup.scd`. If it boots a server or
  plays something, renders and sessions misbehave. `sc.py check` warns when the file
  exists.
- **Class library compile** takes ~0.5 s per sclang start. Extensions in
  `~/Library/Application Support/SuperCollider/Extensions` are compiled too, and a
  broken one fails every run.

## Silence

- No `Out.ar` in the SynthDef, or the wrong bus (anything above 1 is not the stereo
  output).
- `amp` around 0.01 per voice → about −50 LUFS. Start at 0.1–0.3 per voice and use
  `Limiter.ar(sig, 0.9)` on busy mixes.
- An effect synth placed at the **head** reads its bus before the voices write it.
  Use `\addAction, \addToTail` (pattern) or add action 1 (score).
- `ReplaceOut` in an effect writes over the dry sound. `Out` adds to it.
- In NRT, a Pattern with only `\rest`s, or a pattern that ends before it starts (for
  example `Pseq([...], 0)`), renders a silent file. `render` exits 2 on a silent WAV.
- Live: an `Env.adsr` SynthDef without a `gate` argument never releases, so voices
  pile up. One that has `gate` but `doneAction: 0` never frees: `status` shows the
  synth count climbing.

## Timing and length

- `\dur` in patterns counts beats. NRT and the default live clock run at 1 beat per
  second. Set the BPM live with `TempoClock.default.tempo = bpm / 60`, and in NRT with
  `Pbindf(p, \stretch, 60 / bpm)`.
- `render` writes `duration + tail` seconds. Pass `--tail 0` when the length must be
  exact.
- **`s.record` needs an absolute path.** With a relative one (for example
  `thisProcess.nowExecutingPath.dirname` after `sclang file.scd` run from the file's
  folder gives `.`), 3.14.1 fails with *Recording was prepared already with a
  different path* and records nothing. `sc.py record` always passes absolute paths.
  In your own code, use `path.absolutePath` (`standardizePath` and `PathName` leave
  `./` relative).
- `record --seconds S` uses the server recorder's own duration, so the take is S s
  long (±1 block). The first ~50 ms can be silent while the code reaches the server.
- Live pattern events are sent `s.latency` (0.2 s) ahead. Errors and the first note
  come slightly after `run` returns.

## Live session code

- `s.sync` / `.wait` outside `fork { }` → *yield was called outside of a Routine*.
- `run -f` evaluates the whole file as one block. Two `( … )` blocks one after the
  other without `;` are a parse error.
- After `stop` (CmdPeriod), `Pdef`s are stopped but still defined. `Pdef(\x).play`
  resumes one.
- An endless loop (`inf.do { }` without `wait`) blocks the interpreter. `run` times
  out with exit 3; `shutdown` kills it.

## Security posture

- The skill opens no network listener of its own. The helper and the session talk
  over a Unix socket in `$TMPDIR/supercollider-skill/`. The directory is 0700, and
  the socket and state file are 0600.
- Every request carries a random 128-bit token from the state file. A local process
  of another user can't connect; a process of the same user can read the token. That
  is the same trust boundary as the user's shell.
- `run` evaluates arbitrary sclang code, which can do anything the user can
  (`"rm -rf …".unixCmd`). Run only code you wrote or reviewed.
- The session's scsynth binds **127.0.0.1** only (`ServerOptions.bindAddress`).
- **sclang's own language port is not loopback-only.** sclang always opens a UDP port
  (57120, or 57121 when the IDE already holds 57120) on all interfaces. It evaluates
  nothing by itself, but any `OSCdef`/`OSCFunc` in the user's code becomes reachable
  from the network. Restrict such responders to localhost with their `srcID`
  argument: `OSCdef(\x, func, '/path', NetAddr("127.0.0.1", nil))`. The macOS
  firewall may ask once to allow incoming connections for sclang. Denying it is fine.
- Stop path: `sc.py stop` silences everything (CmdPeriod). `sc.py shutdown` quits the
  server and sclang, and kills them if they don't respond. If the supervisor is
  killed with SIGTERM/SIGHUP, it kills sclang and scsynth too. After a SIGKILL, the
  next `start` or `shutdown` reaps them from the state file.
