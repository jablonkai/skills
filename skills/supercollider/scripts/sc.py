#!/usr/bin/env python3
"""Drive SuperCollider 3 from the command line: offline NRT renders and a live session.

    sc.py check                                   app path, version, ffmpeg, startup file
    sc.py render FILE.scd -o OUT.wav [--duration S] [--tail S] [--seed N]
             [--sample-rate HZ] [--channels N] [--sample-format int24] [--timeout S]
                                                  NRT render, faster than realtime, no
                                                  audio device; prints errors + WAV JSON
    sc.py start [--port P] [--timeout S]          boot a headless sclang + scsynth session
    sc.py status                                  liveness, server, synth count, CPU
    sc.py run (-f FILE | -e CODE | -) [--timeout S]
                                                  evaluate code in the session; prints
                                                  the result and errors, exit 2 on error
    sc.py stop                                    CmdPeriod: free all synths, stop patterns
    sc.py record-start OUT.wav [--seconds S]      start recording the server output
    sc.py record-stop                             stop it (waits until the file is closed)
    sc.py record -o OUT.wav --seconds S [--lead-in S] (-f FILE | -e CODE | -)
                                                  one-shot: record, run, wait, stop, check
    sc.py logs [--errors] [-n N]                  the session's post window
    sc.py shutdown                                quit the server and sclang, reap orphans

Exit codes: 0 ok, 1 usage or setup problem, 2 SuperCollider reported an error,
3 timeout (sclang was killed; nothing is left running).

The live session is a background supervisor that owns sclang's stdin and stdout. Clients
reach it over a Unix socket in a 0700 directory under $TMPDIR/supercollider-skill/, and
every request carries a random token from a 0600 state file. The skill opens no TCP or
UDP listener of its own; scsynth binds 127.0.0.1 only.
"""

import argparse
import json
import os
import re
import secrets
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
APP_CANDIDATES = [
    os.environ.get("SUPERCOLLIDER_APP", ""),
    "/Applications/SuperCollider.app",
    os.path.expanduser("~/Applications/SuperCollider.app"),
]
STATE_DIR = os.path.join(tempfile.gettempdir(), "supercollider-skill")
STATE_FILE = os.path.join(STATE_DIR, "state.json")
SOCKET_PATH = os.path.join(STATE_DIR, "ctl.sock")
SESSION_LOG = os.path.join(STATE_DIR, "session.log")
SERVE_LOG = os.path.join(STATE_DIR, "serve.log")
STARTUP_FILE = os.path.expanduser(
    "~/Library/Application Support/SuperCollider/startup.scd")
DEFAULT_PORT = 57115  # not 57110, so the SC IDE's own server can run alongside
EOC = "\x0c"  # sclang -i evaluates everything up to a form feed as one chunk

# sclang's start-up chatter; dropped from what the helper prints (kept in the log)
NOISE = re.compile(
    r"^\s*$|^compiling |^\s*Found \d+ primitives|^\s*Compiling directory|"
    r"^\s*numentries|^\s*\d+ method selectors|^\s*method table size|^\s*Number of Symbols|"
    r"^\s*Byte Code Size|^compile done|^\s*compiled \d+ files|^\s*Compiled \d+ files|"
    r"^\s*Welcome to SuperCollider|^\s*-> an Interpreter|setting clientID to|"
    r"^Class tree inited|^\s*\*\*\* Welcome|^NumPrimitives|^\s*'/\w+' NRT|"
    r"^nextOSCPacket|^start time|^cleaning up OSC|^SC_SKILL_(INFO|DONE|BEGIN|END)|"
    r"^\s*For help type|^Shared memory server interface|^SuperCollider 3 server ready|"
    r"^Number of Devices|^\s+\d+ : |^\s*\"[^\"]+\" (Input|Output) Device|"
    r"^\s+Streams: |^\s+\d+\s+channels|^SC_AudioDriver|^PublishPortToRendezvous|"
    r"^Requested notification messages|^Receiving notification messages")
PARSE_HINT = re.compile(r"^(opening bracket was|unmatched |\s+in interpreted text line)")
ERROR_LINE = re.compile(
    r"^(ERROR|FAILURE IN SERVER|\*\*\* ERROR|Exception in |SC_SKILL_FAIL|"
    r"exception in real time|alloc failed|WARNING: .*not found)")


def die(msg, code=1):
    print(msg, file=sys.stderr)
    sys.exit(code)


# --------------------------------------------------------------------- setup

def find_app():
    for path in APP_CANDIDATES:
        if path and os.path.isfile(os.path.join(path, "Contents/MacOS/sclang")):
            return path
    return None


def sclang_path():
    app = find_app()
    if not app:
        die("SuperCollider.app not found in /Applications or ~/Applications "
            "(set SUPERCOLLIDER_APP, or: brew install --cask supercollider)")
    return os.path.join(app, "Contents/MacOS/sclang")


def app_version(app):
    out = subprocess.run(["defaults", "read", os.path.join(app, "Contents/Info.plist"),
                          "CFBundleShortVersionString"], capture_output=True, text=True)
    return out.stdout.strip() or "unknown"


def cmd_check(_args):
    app = find_app()
    report = {
        "app": app,
        "version": app_version(app) if app else None,
        "sclang": os.path.join(app, "Contents/MacOS/sclang") if app else None,
        "ffmpeg": shutil_which("ffmpeg"),
        "ffprobe": shutil_which("ffprobe"),
        "startup_file": STARTUP_FILE if os.path.exists(STARTUP_FILE) else None,
        "session": session_alive(),
    }
    print(json.dumps(report, indent=2))
    problems = []
    if not app:
        problems.append("SuperCollider.app missing: brew install --cask supercollider")
    if not report["ffmpeg"]:
        problems.append("ffmpeg missing (needed to check takes): brew install ffmpeg")
    if report["startup_file"]:
        problems.append("a startup.scd exists and runs before every render and session; "
                        "if it boots a server or plays sound, renders can misbehave")
    for p in problems:
        print("note: " + p, file=sys.stderr)
    sys.exit(0 if app and report["ffmpeg"] else 1)


def shutil_which(name):
    from shutil import which
    return which(name)


def sc_string(text):
    """A Python str as an sclang string literal."""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def filter_post(lines):
    """Post-window lines minus start-up chatter, markers and error dumps."""
    normal, _ = split_errors(lines)
    return [l for l in normal if not NOISE.search(l) and "SC_SKILL_" not in l]


def split_errors(lines):
    """Separate sclang error reports from normal output.

    sclang prints a runtime error as a dump: the ERROR line, the receiver object, ARGS,
    a tab-indented CALL STACK, then a one-line restatement starting with "^^". A parse
    error prints the position and the source with a caret, closed by a dashed rule.
    The condensed form keeps the message, the hint, PATH, the position and source
    excerpt, and the short "RECEIVER: x" — enough to fix the code.
    """
    normal, errors = [], []
    mode = None  # None, "runtime", "parse", "dump", "stack", "caret"
    for line in lines:
        stripped = line.strip()
        if ERROR_LINE.search(line) and mode != "caret":
            errors.append(line)
            mode = "parse" if re.search(r"[Pp]arse error|syntax error", line) else "runtime"
            continue
        if mode == "caret":  # the "^^" restatement: keep only its short RECEIVER
            if line.startswith("RECEIVER:") or line.startswith("Perhaps"):
                if line.startswith("RECEIVER:") and stripped != "RECEIVER:":
                    errors.append(line)
                continue
            mode = None
        if line.startswith("^^"):
            mode = "caret"
            continue
        if mode == "parse":
            if stripped.startswith("-----"):
                mode = None
            elif stripped and stripped != "in interpreted text":
                errors.append(line.rstrip())
            continue
        if mode in ("runtime", "dump", "stack"):
            if stripped == "RECEIVER:" or stripped == "ARGS:" or stripped == "KEYWORD ARGUMENTS:":
                mode = "dump"
                continue
            if stripped == "CALL STACK:":
                mode = "stack"
                continue
            if line.startswith("PATH:"):
                errors.append(line)
                mode = "runtime"
                continue
            if mode in ("dump", "stack") or line.startswith("\t"):
                continue
            if not stripped:
                continue
            if "SC_SKILL_" not in line and not line.startswith("-> "):
                errors.append(line)
            continue
        if PARSE_HINT.search(line):
            errors.append(line)
            continue
        normal.append(line)
    return normal, errors


def errors_in(lines):
    return split_errors(lines)[1]


def kill_group(proc):
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


def wav_report(path):
    sys.path.insert(0, HERE)
    import wav_check
    return wav_check.measure(path)


# -------------------------------------------------------------------- render

def cmd_render(args):
    user_file = os.path.abspath(args.file)
    out_file = os.path.abspath(args.output)
    if not os.path.isfile(user_file):
        die(f"no such file: {args.file}")
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    if os.path.exists(out_file):
        os.remove(out_file)
    work = tempfile.mkdtemp(prefix="sc-render-")
    template = open(os.path.join(HERE, "nrt_wrap.scd")).read()
    values = {
        "USER_FILE": sc_string(user_file),
        "OUT_FILE": sc_string(out_file),
        "DURATION": "nil" if args.duration is None else repr(float(args.duration)),
        "TAIL": repr(float(args.tail)),
        "SEED": str(int(args.seed)),
        "SAMPLE_RATE": str(int(args.sample_rate)),
        "CHANNELS": str(int(args.channels)),
        "SAMPLE_FORMAT": sc_string(args.sample_format),
        "OSC_FILE": sc_string(os.path.join(work, "score.osc")),
    }
    for key, value in values.items():
        template = template.replace("@@" + key + "@@", value)
    wrapper = os.path.join(work, "render.scd")
    with open(wrapper, "w") as fh:
        fh.write(template)

    started = time.time()
    proc = subprocess.Popen([sclang_path(), wrapper], stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, errors="replace",
                            start_new_session=True, cwd=os.path.dirname(user_file))
    timed_out = False
    try:
        output, _ = proc.communicate(timeout=args.timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        kill_group(proc)
        output, _ = proc.communicate()
    elapsed = time.time() - started
    lines = output.splitlines()
    with open(os.path.join(work, "post.log"), "w") as fh:
        fh.write(output)

    shown = [l for l in filter_post(lines) if not l.startswith("SC_SKILL_FAIL")]
    errors = errors_in(lines)
    info = next((l for l in lines if l.startswith("SC_SKILL_INFO")), "")
    done = next((l for l in lines if l.startswith("SC_SKILL_DONE")), "")
    if shown:
        print("--- post window ---")
        print("\n".join(shown[-60:]))
    if info:
        print(info.replace("SC_SKILL_INFO ", "render: "))
    print(f"wall time: {elapsed:.1f} s   full log: {os.path.join(work, 'post.log')}")

    if timed_out:
        die(f"TIMEOUT after {args.timeout} s — sclang (and any scsynth it started) was "
            "killed. Usual causes: an error inside a Routine/fork (sclang does not exit "
            "on those), an infinite loop, or a wait for a server that never boots.", 3)
    nrt_exit = re.search(r"exit=(\d+)", done)
    if errors or not done or (nrt_exit and nrt_exit.group(1) != "0"):
        sys.stdout.flush()
        print("--- errors ---", file=sys.stderr)
        print("\n".join(errors) if errors else
              "sclang exited without finishing the render (see the post window above)",
              file=sys.stderr)
        sys.exit(2)
    if not os.path.isfile(out_file):
        die("render finished but no WAV was written", 2)
    report = wav_report(out_file)
    print(json.dumps(report, indent=2))
    if report.get("silent"):
        die("the WAV is silent (below -60 LUFS): check amplitudes, Out.ar bus and "
            "that the synths are actually started in the score", 2)


# -------------------------------------------------------------- live session

def read_state():
    try:
        with open(STATE_FILE) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def pid_alive(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def session_alive():
    state = read_state()
    return bool(state and pid_alive(state.get("supervisor_pid")))


def request(payload, timeout=60):
    state = read_state()
    if not state or not pid_alive(state.get("supervisor_pid")):
        die("no session running — start one with: sc.py start")
    payload["token"] = state["token"]
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(timeout + 10)
    try:
        sock.connect(SOCKET_PATH)
        sock.sendall(json.dumps(payload).encode() + b"\n")
        data = b""
        while not data.endswith(b"\n"):
            chunk = sock.recv(65536)
            if not chunk:
                break
            data += chunk
    except (OSError, socket.timeout) as exc:
        die(f"session not responding ({exc}); try: sc.py shutdown && sc.py start")
    finally:
        sock.close()
    try:
        return json.loads(data.decode())
    except ValueError:
        die("garbled reply from the session supervisor; see " + SERVE_LOG)


def reap_orphans(state):
    """Kill whatever a dead session left behind (sclang, scsynth)."""
    if not state:
        return []
    killed = []
    for key in ("scsynth_pid", "sclang_pid"):
        pid = state.get(key)
        if pid and pid_alive(pid):
            try:
                os.kill(pid, signal.SIGKILL)
                killed.append(f"{key.split('_')[0]} {pid}")
            except OSError:
                pass
    return killed


def cmd_start(args):
    state = read_state()
    if state and pid_alive(state.get("supervisor_pid")):
        print(json.dumps({"session": "already running", "port": state.get("port")}))
        return
    killed = reap_orphans(state)
    if killed:
        print("reaped leftovers of a dead session: " + ", ".join(killed), file=sys.stderr)
    os.makedirs(STATE_DIR, mode=0o700, exist_ok=True)
    os.chmod(STATE_DIR, 0o700)
    for path in (STATE_FILE, SOCKET_PATH, SESSION_LOG):  # a new session starts a new log
        if os.path.exists(path):
            os.remove(path)
    token = secrets.token_hex(16)
    fd = os.open(STATE_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as fh:
        json.dump({"token": token, "port": args.port, "status": "booting"}, fh)
    with open(SERVE_LOG, "w") as log:
        subprocess.Popen([sys.executable, os.path.abspath(__file__), "_serve",
                          "--port", str(args.port)],
                         stdout=log, stderr=log, stdin=subprocess.DEVNULL,
                         start_new_session=True)
    deadline = time.time() + args.timeout
    while time.time() < deadline:
        state = read_state() or {}
        if state.get("status") == "ready":
            print(json.dumps({"session": "ready", "port": state["port"],
                              "sample_rate": state.get("sample_rate"),
                              "log": SESSION_LOG}))
            return
        if state.get("status") == "failed":
            die("server failed to boot:\n" + state.get("error", "") +
                f"\nsee {SESSION_LOG}", 2)
        time.sleep(0.2)
    die(f"session did not become ready in {args.timeout} s; see {SESSION_LOG}", 3)


def code_from(args):
    if getattr(args, "file", None):
        path = os.path.abspath(args.file)
        if not os.path.isfile(path):
            die(f"no such file: {args.file}")
        # executeFile reports errors with the file name and line, and sets
        # thisProcess.nowExecutingPath so relative paths in the file work
        return f"thisProcess.interpreter.executeFile({sc_string(path)})"
    if getattr(args, "code", None) == "-" or (
            not getattr(args, "code", None) and not getattr(args, "file", None)):
        return sys.stdin.read()
    return args.code


def print_run_reply(reply):
    for line in reply.get("output", []):
        print(line)
    if reply.get("errors"):
        sys.stdout.flush()
        print("--- errors ---", file=sys.stderr)
        print("\n".join(reply["errors"]), file=sys.stderr)
    if reply.get("timeout"):
        die("TIMEOUT: the interpreter is still busy (an endless loop or a long "
            "blocking call); run: sc.py shutdown", 3)
    if reply.get("errors"):
        sys.exit(2)


def cmd_run(args):
    reply = request({"cmd": "run", "code": code_from(args), "timeout": args.timeout,
                     "settle": args.settle}, args.timeout)
    print_run_reply(reply)


def cmd_simple(name, code, timeout=10, wait_for=None):
    def handler(args):
        reply = request({"cmd": "run", "code": code(args) if callable(code) else code,
                         "timeout": timeout, "settle": 0.2, "wait_for": wait_for,
                         "quiet": True}, timeout)
        print_run_reply(reply)
        print(json.dumps({"ok": True, "cmd": name}))
    return handler


def record_start_code(path, seconds):
    duration = "nil" if seconds is None else repr(float(seconds))
    return (f"s.recHeaderFormat = \"wav\"; s.recSampleFormat = \"int24\"; "
            f"s.record({sc_string(path)}, numChannels: s.options.numOutputBusChannels, "
            f"duration: {duration});")


def cmd_record_start(args):
    path = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    reply = request({"cmd": "run", "code": record_start_code(path, args.seconds),
                     "timeout": 10, "settle": 0.0, "wait_for": "Recording channels",
                     "quiet": True}, 10)
    print_run_reply(reply)
    print(json.dumps({"recording": path, "seconds": args.seconds}))


def cmd_record_stop(_args):
    reply = request({"cmd": "run", "code": "s.stopRecording;", "timeout": 10,
                     "settle": 0.0, "wait_for": "Recording Stopped", "quiet": True}, 10)
    print_run_reply(reply)
    print(json.dumps({"recording": "stopped"}))


def cmd_record(args):
    path = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        os.remove(path)
    errors = []

    def run_code():
        reply = request({"cmd": "run", "code": code_from(args), "timeout": 30,
                         "settle": 0.3}, 30)
        for line in reply.get("output", []):
            print(line)
        errors.extend(reply.get("errors", []))

    if args.lead_in:
        # play first, record later: for loops that wait for a bar line (quant)
        run_code()
        time.sleep(args.lead_in)
    reply = request({"cmd": "run", "code": record_start_code(path, args.seconds),
                     "timeout": 10, "settle": 0.0, "wait_for": "Recording channels",
                     "quiet": True}, 10)
    print_run_reply(reply)
    since = reply.get("start_index", 0)
    started = time.time()
    if not args.lead_in:
        run_code()
    # s.record(duration:) stops the take itself; wait for its "Recording Stopped"
    remaining = args.seconds - (time.time() - started) + 5
    reply = request({"cmd": "wait", "wait_for": "Recording Stopped", "since": since,
                     "timeout": max(remaining, 5)}, max(remaining, 5))
    request({"cmd": "run", "code": "CmdPeriod.run;", "timeout": 10, "settle": 0.2,
             "quiet": True}, 10)
    errors += reply.get("errors", [])
    if errors:
        print("--- errors ---", file=sys.stderr)
        print("\n".join(errors), file=sys.stderr)
    if not os.path.isfile(path):
        die("no take was written (see errors above and: sc.py logs --errors)", 2)
    report = wav_report(path)
    print(json.dumps(report, indent=2))
    if report.get("longest_silence_s", 0) > 1.0 and not args.lead_in:
        print("note: the take has a silent stretch over 1 s; if the code plays with "
              "quant, record again with --lead-in <one bar in seconds>", file=sys.stderr)
    if errors or report.get("silent"):
        if report.get("silent"):
            print("the take is silent (below -60 LUFS)", file=sys.stderr)
        sys.exit(2)


def cmd_status(_args):
    state = read_state()
    if not state or not pid_alive(state.get("supervisor_pid")):
        print(json.dumps({"session": "not running"}))
        sys.exit(1)
    reply = request({"cmd": "run", "timeout": 5, "settle": 0.0, "quiet": True, "code":
                     '"SC_SKILL_STATUS running=% synths=% peakCPU=% sampleRate=%"'
                     '.format(s.serverRunning, s.numSynths, s.peakCPU.round(0.1), '
                     's.actualSampleRate.round).postln;'}, 5)
    line = next((l for l in reply.get("raw", []) if "SC_SKILL_STATUS" in l), "")
    fields = dict(re.findall(r"(\w+)=(\S+)", line))
    print(json.dumps({"session": "running", "port": state.get("port"),
                      "server_running": fields.get("running") == "true",
                      "synths": fields.get("synths"), "peak_cpu": fields.get("peakCPU"),
                      "sample_rate": fields.get("sampleRate"), "log": SESSION_LOG}))


def cmd_logs(args):
    try:
        lines = open(SESSION_LOG, errors="replace").read().splitlines()
    except OSError:
        die("no session log yet")
    lines = errors_in(lines) if args.errors else filter_post(lines)
    print("\n".join(lines[-args.n:]))


def cmd_shutdown(_args):
    state = read_state()
    if state and pid_alive(state.get("supervisor_pid")):
        try:
            request({"cmd": "shutdown"}, 15)
        except SystemExit:
            pass
        deadline = time.time() + 10
        while time.time() < deadline and pid_alive(state.get("supervisor_pid")):
            time.sleep(0.2)
    killed = reap_orphans(read_state() or state)
    if state and pid_alive(state.get("supervisor_pid")):
        os.kill(state["supervisor_pid"], signal.SIGKILL)
        killed.append(f"supervisor {state['supervisor_pid']}")
    for path in (STATE_FILE, SOCKET_PATH):
        if os.path.exists(path):
            os.remove(path)
    print(json.dumps({"session": "stopped", "force_killed": killed}))


# ---------------------------------------------------------------- supervisor

class Supervisor:
    """Owns sclang; serves run/wait/shutdown requests over the Unix socket."""

    def __init__(self, port):
        self.port = port
        self.lines = []  # every line sclang printed, in order
        self.cond = threading.Condition()
        self.lock = threading.Lock()  # one evaluation at a time
        self.log = open(SESSION_LOG, "a", buffering=1)
        self.state = read_state()
        self.proc = subprocess.Popen([sclang_path(), "-i", "skill"],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True,
                                     errors="replace", bufsize=1)
        self.save(sclang_pid=self.proc.pid, supervisor_pid=os.getpid())
        threading.Thread(target=self.reader, daemon=True).start()

    def save(self, **fields):
        self.state.update(fields)
        tmp = STATE_FILE + ".tmp"
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as fh:
            json.dump(self.state, fh)
        os.replace(tmp, STATE_FILE)

    def reader(self):
        for line in self.proc.stdout:
            line = line.rstrip("\n")
            self.log.write(line + "\n")
            with self.cond:
                self.lines.append(line)
                self.cond.notify_all()
        with self.cond:
            self.lines.append("SC_SKILL_EOF")
            self.cond.notify_all()

    def send(self, code):
        self.proc.stdin.write(code + EOC)
        self.proc.stdin.flush()

    def wait_for(self, pattern, since, timeout):
        deadline = time.time() + timeout
        with self.cond:
            while True:
                for i in range(since, len(self.lines)):
                    if pattern in self.lines[i] or self.lines[i] == "SC_SKILL_EOF":
                        return i
                left = deadline - time.time()
                if left <= 0:
                    return None
                self.cond.wait(left)

    def boot(self):
        start = len(self.lines)
        self.send(
            f"s = Server(\\skill, NetAddr(\"127.0.0.1\", {self.port})); Server.default = s;"
            "s.options.bindAddress = \"127.0.0.1\"; s.options.numOutputBusChannels = 2;"
            "s.options.numInputBusChannels = 0; s.options.memSize = 2 ** 18;"
            "s.options.maxNodes = 8192; s.options.numWireBufs = 512;"
            "s.waitForBoot({ \"SC_SKILL_READY pid=% sr=%\".format(s.pid, "
            "s.actualSampleRate.round).postln }, 60,"
            "{ \"SC_SKILL_BOOT_FAILED\".postln });")
        idx = self.wait_for("SC_SKILL_", start, 90)
        line = self.lines[idx] if idx is not None else ""
        if "SC_SKILL_READY" not in line:
            error = "\n".join(errors_in(self.lines[start:])) or line or "boot timed out"
            self.save(status="failed", error=error)
            return False
        fields = dict(re.findall(r"(\w+)=(\S+)", line))
        self.save(status="ready", scsynth_pid=int(fields["pid"]) if fields.get(
            "pid", "nil").isdigit() else None, sample_rate=fields.get("sr"))
        return True

    def run(self, req):
        with self.lock:
            tag = secrets.token_hex(4)
            start = len(self.lines)
            self.send(f"\"SC_SKILL_BEGIN {tag}\".postln;")
            self.send(req["code"])
            self.send(f"\"SC_SKILL_END {tag}\".postln;")
            end = self.wait_for(f"SC_SKILL_END {tag}", start, req.get("timeout", 30))
            if end is None:
                return {"timeout": True, "errors": errors_in(self.lines[start:])}
            if req.get("wait_for"):
                self.wait_for(req["wait_for"], start, req.get("timeout", 30))
            settle = req.get("settle", 0.3)
            if settle:
                time.sleep(settle)  # async errors from routines started by the code
            with self.cond:
                raw = self.lines[start:]
            body = [l for l in raw if "SC_SKILL_BEGIN" not in l]
            output = [] if req.get("quiet") else filter_post(body)
            return {"output": output, "errors": errors_in(body), "raw": raw,
                    "start_index": start}

    def wait(self, req):
        start = int(req.get("since", len(self.lines)))
        idx = self.wait_for(req["wait_for"], start, req.get("timeout", 30))
        return {"found": idx is not None, "errors": [], "timeout": False}

    def shutdown(self):
        with self.lock:
            self.send("s.quit;")
            time.sleep(1.0)
            self.send("0.exit;")
        try:
            self.proc.wait(5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        pid = self.state.get("scsynth_pid")
        if pid and pid_alive(pid):
            os.kill(pid, signal.SIGKILL)

    def serve(self):
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(SOCKET_PATH)
        os.chmod(SOCKET_PATH, 0o600)
        server.listen(4)
        while True:
            conn, _ = server.accept()
            threading.Thread(target=self.handle, args=(conn, server), daemon=True).start()

    def handle(self, conn, server):
        try:
            data = b""
            while not data.endswith(b"\n"):
                chunk = conn.recv(65536)
                if not chunk:
                    return
                data += chunk
            req = json.loads(data.decode())
            if not secrets.compare_digest(str(req.get("token", "")), self.state["token"]):
                reply = {"errors": ["bad token"]}
            elif req.get("cmd") == "run":
                reply = self.run(req)
            elif req.get("cmd") == "wait":
                reply = self.wait(req)
            elif req.get("cmd") == "shutdown":
                self.shutdown()
                conn.sendall(json.dumps({"ok": True}).encode() + b"\n")
                conn.close()
                server.close()
                os._exit(0)
            else:
                reply = {"errors": [f"unknown command {req.get('cmd')}"]}
            conn.sendall(json.dumps(reply).encode() + b"\n")
        except Exception as exc:  # keep serving; report to the client
            try:
                conn.sendall(json.dumps({"errors": [f"supervisor: {exc}"]}).encode() + b"\n")
            except OSError:
                pass
        finally:
            conn.close()


def cmd_serve(args):
    sup = Supervisor(args.port)

    def bail(*_):
        sup.proc.kill()
        pid = sup.state.get("scsynth_pid")
        if pid and pid_alive(pid):
            os.kill(pid, signal.SIGKILL)
        os._exit(1)
    signal.signal(signal.SIGTERM, bail)
    signal.signal(signal.SIGHUP, bail)
    # wait for the class library to compile before sending the boot chunk
    if sup.wait_for("Welcome to SuperCollider", 0, 60) is None:
        sup.save(status="failed", error="sclang did not start")
        bail()
    if not sup.boot():
        sup.proc.kill()
        os._exit(1)
    try:
        sup.serve()
    finally:
        bail()


# ---------------------------------------------------------------------- main

def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check").set_defaults(func=cmd_check)

    p = sub.add_parser("render")
    p.add_argument("file")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--duration", type=float,
                   help="seconds of music; required for a Pattern, default for a Score "
                        "is its last event time")
    p.add_argument("--tail", type=float, default=2.0,
                   help="extra seconds after --duration for releases and reverb (2)")
    p.add_argument("--seed", type=int, default=1234)
    p.add_argument("--sample-rate", type=int, default=48000)
    p.add_argument("--channels", type=int, default=2)
    p.add_argument("--sample-format", default="int24",
                   choices=["int16", "int24", "int32", "float"])
    p.add_argument("--timeout", type=float, default=300)
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("start")
    p.add_argument("--port", type=int, default=DEFAULT_PORT)
    p.add_argument("--timeout", type=float, default=90)
    p.set_defaults(func=cmd_start)

    sub.add_parser("status").set_defaults(func=cmd_status)

    p = sub.add_parser("run")
    p.add_argument("-f", "--file")
    p.add_argument("-e", "--code")
    p.add_argument("--timeout", type=float, default=30)
    p.add_argument("--settle", type=float, default=0.5,
                   help="seconds to keep collecting errors from routines it started")
    p.set_defaults(func=cmd_run)

    sub.add_parser("stop").set_defaults(func=cmd_simple("stop", "CmdPeriod.run;"))

    p = sub.add_parser("record-start")
    p.add_argument("output")
    p.add_argument("--seconds", type=float, help="stop by itself after this long")
    p.set_defaults(func=cmd_record_start)

    sub.add_parser("record-stop").set_defaults(func=cmd_record_stop)

    p = sub.add_parser("record")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--seconds", type=float, required=True)
    p.add_argument("--lead-in", type=float, default=0.0,
                   help="run the code, wait this long, then record (for quantised loops)")
    p.add_argument("-f", "--file")
    p.add_argument("-e", "--code")
    p.set_defaults(func=cmd_record)

    p = sub.add_parser("logs")
    p.add_argument("--errors", action="store_true")
    p.add_argument("-n", type=int, default=80)
    p.set_defaults(func=cmd_logs)

    sub.add_parser("shutdown").set_defaults(func=cmd_shutdown)

    p = sub.add_parser("_serve")
    p.add_argument("--port", type=int, default=DEFAULT_PORT)
    p.set_defaults(func=cmd_serve)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
