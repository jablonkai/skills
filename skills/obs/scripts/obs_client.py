"""Minimal obs-websocket v5 client on the Python standard library — no pip install.

Speaks RFC 6455 over a plain TCP socket (loopback, no TLS: OBS serves ws:// only),
authenticates with the Hello/Identify SHA-256 challenge, and exposes request, batch and
event calls plus a few helpers that paper over the protocol's sharp edges.

    from obs_client import ObsClient
    with ObsClient() as obs:
        print(obs.call("GetVersion")["obsVersion"])

Connection settings come from OBS_HOST / OBS_PORT / OBS_PASSWORD / OBS_TIMEOUT; when the
port or password is unset they are read from the local obs-websocket config file, so a
default install needs no setup beyond enabling the server. The password is never printed.
"""

import base64
import collections
import hashlib
import json
import os
import socket
import struct
import sys
import time
import uuid

_WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
_OP_HELLO, _OP_IDENTIFY, _OP_IDENTIFIED, _OP_EVENT = 0, 1, 2, 5
_OP_REQUEST, _OP_RESPONSE, _OP_BATCH, _OP_BATCH_RESPONSE = 6, 7, 8, 9
EVENTS_ALL = 0x7FF  # every non-high-volume subscription (General … Ui)

# WebSocket close codes obs-websocket uses to explain a refused session.
_CLOSE_REASONS = {
    4002: "OBS could not decode the message",
    4007: "OBS rejected the session (not identified)",
    4008: "OBS expected authentication but none was sent",
    4009: "authentication failed — wrong password (set OBS_PASSWORD, or copy it from "
          "Tools > WebSocket Server Settings > Show Connect Info)",
    4010: "OBS does not support this RPC version",
}

# Frequent request status codes, so a failure reads as more than a number.
STATUS = {
    203: "RequestFieldMissing (unknown request type or missing field)",
    204: "UnknownRequestType",
    300: "MissingRequestField",
    400: "InvalidRequestField",
    402: "InvalidRequestFieldType",
    500: "OutputRunning",
    501: "OutputNotRunning",
    502: "OutputPaused",
    503: "OutputNotPaused",
    504: "OutputDisabled",
    505: "StudioModeActive",
    506: "StudioModeNotActive",
    600: "ResourceNotFound",
    601: "ResourceAlreadyExists",
    602: "InvalidResourceType",
    604: "InvalidInputKind",
    605: "ResourceNotConfigurable",
    700: "ResourceCreationFailed",
    701: "ResourceActionFailed",
    702: "RequestProcessingFailed",
}


class ObsNotReachable(ConnectionError):
    """OBS is not running, its WebSocket server is off, or the session was refused."""


class ObsRequestError(RuntimeError):
    """A request came back with requestStatus.result == false."""

    def __init__(self, request_type, code, comment):
        self.request_type, self.code, self.comment = request_type, code, comment
        name = STATUS.get(code, "")
        super().__init__(f"{request_type} failed: {code} {name}" + (f" — {comment}" if comment else ""))


def config_dir():
    """The OBS config directory for this platform (it exists once OBS has run)."""
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/obs-studio")
    if sys.platform.startswith("win"):
        return os.path.join(os.environ.get("APPDATA", ""), "obs-studio")
    return os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "obs-studio")


def websocket_config():
    """obs-websocket's saved settings ({} when OBS has never run or the file is unreadable)."""
    path = os.path.join(config_dir(), "plugin_config", "obs-websocket", "config.json")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def obs_color(hex_rgba):
    """'#RRGGBB' or '#RRGGBBAA' → the ABGR integer OBS color settings expect."""
    h = hex_rgba.lstrip("#")
    if len(h) == 6:
        h += "ff"
    r, g, b, a = (int(h[i:i + 2], 16) for i in (0, 2, 4, 6))
    return (a << 24) | (b << 16) | (g << 8) | r


class ObsClient:
    def __init__(self, host=None, port=None, password=None, timeout=None, events=EVENTS_ALL):
        cfg = websocket_config()
        self.host = host or os.environ.get("OBS_HOST", "127.0.0.1")
        self.port = int(port or os.environ.get("OBS_PORT") or cfg.get("server_port") or 4455)
        if password is None:
            password = os.environ.get("OBS_PASSWORD")
        if password is None and cfg.get("auth_required", True):
            password = cfg.get("server_password")
        self._password = password
        self.timeout = float(timeout or os.environ.get("OBS_TIMEOUT") or 30)
        self._events_mask = events
        self._sock = None
        self._buf = b""
        self.events = collections.deque(maxlen=2000)
        self.hello = {}
        self.server_enabled = cfg.get("server_enabled")  # None when no config file

    # ---- connection -------------------------------------------------------------------

    def __enter__(self):
        return self.connect()

    def __exit__(self, *exc):
        self.close()

    def connect(self):
        try:
            self._sock = socket.create_connection((self.host, self.port), timeout=min(self.timeout, 10))
        except OSError as e:
            hint = ("OBS is not running, or its WebSocket server is off (Tools > WebSocket Server "
                    "Settings > Enable WebSocket server)")
            if self.server_enabled is False:
                hint = "obs-websocket is disabled in OBS (Tools > WebSocket Server Settings > Enable)"
            raise ObsNotReachable(f"cannot reach {self.host}:{self.port} ({e.strerror or e}): {hint}") from None
        self._sock.settimeout(self.timeout)
        self._handshake()
        hello = self._recv_json()
        if hello.get("op") != _OP_HELLO:
            raise ObsNotReachable(f"expected Hello, got {hello!r:.200}")
        self.hello = hello["d"]
        ident = {"rpcVersion": 1, "eventSubscriptions": self._events_mask}
        auth = self.hello.get("authentication")
        if auth:
            if not self._password:
                self.close()
                raise ObsNotReachable("OBS requires a password: set OBS_PASSWORD (Tools > WebSocket "
                                      "Server Settings > Show Connect Info)")
            secret = base64.b64encode(hashlib.sha256((self._password + auth["salt"]).encode()).digest())
            ident["authentication"] = base64.b64encode(
                hashlib.sha256(secret + auth["challenge"].encode()).digest()).decode()
        self._send_json({"op": _OP_IDENTIFY, "d": ident})
        while True:
            msg = self._recv_json()
            if msg.get("op") == _OP_IDENTIFIED:
                return self

    def close(self):
        if self._sock:
            try:
                self._send_frame(0x8, struct.pack("!H", 1000))
            except OSError:
                pass
            self._sock.close()
            self._sock = None

    # ---- requests ---------------------------------------------------------------------

    def call(self, request_type, data=None, **fields):
        """Send one request; return its responseData ({} when none). Raises ObsRequestError."""
        payload = dict(data or {}, **fields)
        rid = uuid.uuid4().hex
        d = {"requestType": request_type, "requestId": rid}
        if payload:
            d["requestData"] = payload
        self._send_json({"op": _OP_REQUEST, "d": d})
        resp = self._await(_OP_RESPONSE, rid)
        st = resp["requestStatus"]
        if not st.get("result"):
            raise ObsRequestError(request_type, st.get("code"), st.get("comment"))
        return resp.get("responseData") or {}

    def try_call(self, request_type, data=None, **fields):
        """Like call(), but return None instead of raising on a request failure."""
        try:
            return self.call(request_type, data, **fields)
        except ObsRequestError:
            return None

    def batch(self, requests, halt_on_failure=False, execution_type=0, raise_on_error=True):
        """Run [("RequestType", {data}) | {"requestType":…, "requestData":…}, …] in one round trip.

        execution_type 0 = serial realtime, 1 = serial frame (one per rendered frame, allows
        {"requestType": "Sleep", "requestData": {"sleepFrames": n}}), 2 = parallel.
        Returns the list of responseData dicts (None for a failed request when raise_on_error
        is False).
        """
        reqs = []
        for r in requests:
            if isinstance(r, dict):
                reqs.append(dict(r))
            else:
                rtype, rdata = (r[0], r[1] if len(r) > 1 else None)
                reqs.append({"requestType": rtype, **({"requestData": rdata} if rdata else {})})
        rid = uuid.uuid4().hex
        self._send_json({"op": _OP_BATCH, "d": {"requestId": rid, "haltOnFailure": halt_on_failure,
                                                "executionType": execution_type, "requests": reqs}})
        results = self._await(_OP_BATCH_RESPONSE, rid)["results"]
        out = []
        for req, res in zip(reqs, results):
            st = res["requestStatus"]
            if not st.get("result"):
                if raise_on_error:
                    raise ObsRequestError(req["requestType"], st.get("code"), st.get("comment"))
                out.append(None)
            else:
                out.append(res.get("responseData") or {})
        return out

    def wait_event(self, event_type, timeout=30, match=None):
        """Block until an event of that type (and matching `match(eventData)`) arrives.

        Events received before the call are checked first, oldest first, and consumed.
        """
        deadline = time.monotonic() + timeout
        while True:
            for ev in list(self.events):
                if ev["eventType"] == event_type and (match is None or match(ev.get("eventData", {}))):
                    self.events.remove(ev)
                    return ev.get("eventData", {})
            left = deadline - time.monotonic()
            if left <= 0:
                raise TimeoutError(f"no {event_type} event within {timeout}s")
            self._sock.settimeout(left)
            try:
                self._dispatch(self._recv_json())
            except socket.timeout:
                pass
            finally:
                if self._sock:
                    self._sock.settimeout(self.timeout)

    # ---- helpers ----------------------------------------------------------------------

    def screenshot(self, source, path, width=None, height=None, fmt=None, quality=-1, settle=0.15):
        """Render `source` (a scene or input) to an image file here; returns the absolute path.

        Uses GetSourceScreenshot, so the file lands on this machine even if OBS were remote.
        Pass only width to keep the aspect ratio. Sources such as text re-render on the next
        video tick, so a screenshot taken right after a settings change can show the old
        frame — `settle` seconds of waiting first covers a few frames.
        """
        if settle:
            time.sleep(settle)
        path = os.path.abspath(path)
        fmt = fmt or (os.path.splitext(path)[1].lstrip(".").lower() or "png")
        fmt = "jpg" if fmt == "jpeg" else fmt
        req = {"sourceName": source, "imageFormat": fmt, "imageCompressionQuality": quality}
        if width:
            req["imageWidth"] = int(width)
        if height:
            req["imageHeight"] = int(height)
        data = self.call("GetSourceScreenshot", req)["imageData"]
        with open(path, "wb") as f:
            f.write(base64.b64decode(data.split(",", 1)[1] if data.startswith("data:") else data))
        return path

    def scene_names(self):
        """Scene names in Scenes-dock order, top first (GetSceneList returns them reversed)."""
        return [s["sceneName"] for s in self.call("GetSceneList")["scenes"]][::-1]

    def input_names(self, kind=None):
        req = {"inputKind": kind} if kind else {}
        return [i["inputName"] for i in self.call("GetInputList", req)["inputs"]]

    def ensure_scene(self, name):
        """Create the scene unless it exists. Returns True when it was created."""
        if name in self.scene_names():
            return False
        self.call("CreateScene", sceneName=name)
        return True

    def item_id(self, scene, source):
        """sceneItemId of `source` in `scene` (ObsRequestError 600 if it is not there)."""
        return self.call("GetSceneItemId", sceneName=scene, sourceName=source)["sceneItemId"]

    def ensure_input(self, scene, name, kind, settings=None, enabled=True):
        """Add input `name` to `scene`, or update its settings if it already exists.

        Input names are global in OBS: an existing input of that name is reused (added to
        `scene` if it isn't there yet) rather than duplicated. Returns the sceneItemId.
        """
        if name in self.input_names():
            if settings:
                self.call("SetInputSettings", inputName=name, inputSettings=settings, overlay=True)
            item = self.try_call("GetSceneItemId", sceneName=scene, sourceName=name)
            if item:
                return item["sceneItemId"]
            return self.call("CreateSceneItem", sceneName=scene, sourceName=name,
                             sceneItemEnabled=enabled)["sceneItemId"]
        return self.call("CreateInput", sceneName=scene, inputName=name, inputKind=kind,
                         inputSettings=settings or {}, sceneItemEnabled=enabled)["sceneItemId"]

    def set_transform(self, scene, source, **transform):
        """Set sceneItemTransform fields (positionX/Y, scaleX/Y, rotation, alignment,
        boundsType/boundsWidth/boundsHeight, crop*) on `source` in `scene`."""
        self.call("SetSceneItemTransform", sceneName=scene, sceneItemId=self.item_id(scene, source),
                  sceneItemTransform=transform)

    def ensure_filter(self, source, name, kind, settings=None):
        """Add filter `name` to `source`, or update its settings (and re-enable it) if it exists."""
        existing = {f["filterName"] for f in self.call("GetSourceFilterList", sourceName=source)["filters"]}
        if name in existing:
            self.call("SetSourceFilterSettings", sourceName=source, filterName=name,
                      filterSettings=settings or {}, overlay=True)
            self.call("SetSourceFilterEnabled", sourceName=source, filterName=name, filterEnabled=True)
        else:
            self.call("CreateSourceFilter", sourceName=source, filterName=name, filterKind=kind,
                      filterSettings=settings or {})

    def input_kind(self, *candidates):
        """First of `candidates` this OBS build supports — e.g. input_kind('text_ft2_source_v2',
        'text_gdiplus_v3') for a text source on any platform."""
        kinds = set(self.call("GetInputKindList", unversioned=False)["inputKinds"])
        for k in candidates:
            if k in kinds:
                return k
        raise ObsRequestError("GetInputKindList", 604, f"none of {candidates} available")

    def text_settings(self, kind, text, size=64, color="#ffffff", face=None):
        """Settings dict for a text input of `kind` (FreeType on macOS/Linux, GDI+ on Windows)."""
        c = obs_color(color)
        if kind.startswith("text_gdiplus"):
            return {"text": text, "color": c & 0xFFFFFF, "opacity": round(((c >> 24) & 0xFF) / 2.55),
                    "font": {"face": face or "Arial", "size": size, "style": "Regular", "flags": 0}}
        return {"text": text, "color1": c, "color2": c,
                "font": {"face": face or "Helvetica", "size": size, "style": "Regular", "flags": 0}}

    # ---- websocket plumbing -------------------------------------------------------------

    def _handshake(self):
        key = base64.b64encode(os.urandom(16)).decode()
        req = (f"GET / HTTP/1.1\r\nHost: {self.host}:{self.port}\r\nUpgrade: websocket\r\n"
               f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n"
               f"Sec-WebSocket-Protocol: obswebsocket.json\r\n\r\n")
        self._sock.sendall(req.encode())
        while b"\r\n\r\n" not in self._buf:
            chunk = self._sock.recv(4096)
            if not chunk:
                raise ObsNotReachable("connection closed during the WebSocket handshake")
            self._buf += chunk
        head, self._buf = self._buf.split(b"\r\n\r\n", 1)
        lines = head.decode("latin-1").split("\r\n")
        if " 101 " not in lines[0] + " ":
            raise ObsNotReachable(f"not an obs-websocket server on port {self.port}: {lines[0]}")
        headers = {k.strip().lower(): v.strip() for k, _, v in (l.partition(":") for l in lines[1:])}
        want = base64.b64encode(hashlib.sha1((key + _WS_GUID).encode()).digest()).decode()
        if headers.get("sec-websocket-accept") != want:
            raise ObsNotReachable("bad Sec-WebSocket-Accept in the handshake")

    def _recv_exact(self, n):
        while len(self._buf) < n:
            chunk = self._sock.recv(max(65536, n - len(self._buf)))
            if not chunk:
                raise ObsNotReachable("OBS closed the connection")
            self._buf += chunk
        out, self._buf = self._buf[:n], self._buf[n:]
        return out

    def _recv_frame(self):
        b0, b1 = self._recv_exact(2)
        fin, opcode, masked, length = b0 & 0x80, b0 & 0x0F, b1 & 0x80, b1 & 0x7F
        if length == 126:
            length = struct.unpack("!H", self._recv_exact(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", self._recv_exact(8))[0]
        mask = self._recv_exact(4) if masked else None
        payload = self._recv_exact(length)
        if mask:
            payload = bytes(c ^ mask[i % 4] for i, c in enumerate(payload))
        return bool(fin), opcode, payload

    def _recv_json(self):
        parts, first_op = [], None
        while True:
            fin, op, payload = self._recv_frame()
            if op == 0x8:  # close
                code = struct.unpack("!H", payload[:2])[0] if len(payload) >= 2 else None
                reason = _CLOSE_REASONS.get(code) or payload[2:].decode("utf-8", "replace") or "no reason"
                self._sock.close()
                self._sock = None
                raise ObsNotReachable(f"OBS closed the session ({code}): {reason}")
            if op == 0x9:  # ping
                self._send_frame(0xA, payload)
                continue
            if op == 0xA:  # pong
                continue
            if op in (0x1, 0x2):
                first_op, parts = op, [payload]
            elif op == 0x0:
                parts.append(payload)
            if fin and first_op is not None:
                return json.loads(b"".join(parts).decode("utf-8"))

    def _send_frame(self, opcode, payload):
        header = bytearray([0x80 | opcode])
        n = len(payload)
        if n < 126:
            header.append(0x80 | n)
        elif n < 1 << 16:
            header.append(0x80 | 126)
            header += struct.pack("!H", n)
        else:
            header.append(0x80 | 127)
            header += struct.pack("!Q", n)
        mask = os.urandom(4)
        header += mask
        self._sock.sendall(bytes(header) + bytes(c ^ mask[i % 4] for i, c in enumerate(payload)))

    def _send_json(self, obj):
        if not self._sock:
            raise ObsNotReachable("not connected")
        self._send_frame(0x1, json.dumps(obj).encode("utf-8"))

    def _dispatch(self, msg):
        if msg.get("op") == _OP_EVENT:
            self.events.append(msg["d"])
        return msg

    def _await(self, op, rid):
        while True:
            msg = self._dispatch(self._recv_json())
            if msg.get("op") == op and msg["d"].get("requestId") == rid:
                return msg["d"]
