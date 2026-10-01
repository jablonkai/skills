# Sonic Pi gotchas

Verified on Sonic Pi 5.0.0 (SuperSonic engine v0.71) on macOS.

## Timing

- **Sound lands 0.5 s after evaluation** (`current_sched_ahead_time` = 0.5).
  `sp.py record` starts the recorder after that lead time. A manual
  `record-start` → `run` take therefore begins with about 0.5 s of silence.
- **`stop` does not cancel notes already scheduled.** Up to 0.5 s of the old music
  (plus release tails) still plays after `stop-all-jobs`. `sp.py record` waits 1 s
  after stopping before it records, so a new take is not polluted.
- **Recording is realtime.** There is no offline render. Budget wall-clock time
  equal to the take, plus about 3 s.
- `use_bpm` affects `sleep`, `release:`/`sustain:` times and `sample_duration`.
  `sp.py record --bpm` must match it, or the take is cut short or runs long.

## Loops

- A `live_loop` without `sleep`/`sync` raises "did not sleep" and stops.
- **An unknown sample name is not an error.** `sample :drum_snare_sof` logs
  "no match found, skipping" and plays nothing. `sp.py run`/`record` print these as
  `WARNING`, and `sp.py logs --errors` includes them. Check the name against
  [dsl-reference.md](dsl-reference.md).
- Re-running a file re-defines its loops in place. Loops from earlier runs that are
  missing from the new code keep playing. Use `stop` (all jobs), or redefine the
  loop with `stop` as its body.
- A runtime error inside a loop kills **that** loop only; the rest keep playing.
  The error can arrive after `run`'s wait window, so check `sp.py logs --errors`.
- `with_fx` wrapped **around** a `live_loop` is evaluated once: a later re-run does
  not change its options, and code placed after the block runs with the FX already
  torn down. Put `with_fx` inside the loop body.
- Without `use_random_seed`, `rrand`/`choose`/`shuffle` still give the same
  sequence on every run, because Sonic Pi seeds each thread deterministically.
  Change the seed to get variation; keep it to reproduce a take.

## Sessions

- **Orphans live about 90 s.** The daemon's kill switch allows a 40 s grace period
  and then 5 × 10 s without keep-alives (the source comment saying "3 s" is wrong).
  `sp.py shutdown` and `sp.py start` reap an orphan at once with `/daemon/exit`.
- **The bundled `headless-record.rb` writes no file on 5.0.0.** It sends its record
  command to the engine over UDP, but the engine only listens on TCP. Use
  `sp.py record` (the spider's recorder) instead. See [osc-protocol.md](osc-protocol.md).
- A headless session and the GUI can run at the same time; each picks free ports.
  Both play on the default output device.
- **Attach mode is blind.** The GUI owns the reply port, so `run` cannot see errors
  and `logs` has nothing. Use a headless session when you need feedback.
- `sp.py attach` reads the token from the spider's command line. After the GUI
  restarts, the port and token change, so attach again.
- `osc-cues` (port 4560) is Sonic Pi's **incoming** OSC port for `sync "/osc*/..."`
  from other apps. It is not the code-evaluation port.

## Security posture

- Every socket is UDP on 127.0.0.1. There is no HTTP endpoint, so browsers cannot
  reach it (no cross-origin exposure).
- Every spider and daemon message must carry Sonic Pi's per-launch 32-bit token;
  messages without it are logged and ignored.
- The helper keeps the token in `$TMPDIR/sonic-pi-skill/state.json` (mode 0600,
  directory 0700) and never prints it.
- **The token is not a strong secret.** Any process running as the same user can
  read it from `ps` or from that file, and evaluated code is full Ruby with the
  user's file and network access. Treat a running session like an open Ruby REPL:
  do not run code from untrusted sources, and `shutdown` when done.
- **Stop path:**
  - `sp.py stop`: stops all jobs.
  - `sp.py shutdown`: stops jobs and ends the engine. In attach mode it only stops
    jobs and detaches.
  - Killing the helper: the daemon reaps itself within about 90 s.
