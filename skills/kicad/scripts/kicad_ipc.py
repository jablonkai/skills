#!/usr/bin/env python3
"""kicad_ipc.py - edit the board open in a running KiCad PCB editor through the IPC API.

Needs kicad-python (kipy) and KiCad's API server switched on (Preferences > Plugins >
Enable KiCad API). Run it with the venv that has kipy:

    ~/.venvs/kicad/bin/python kicad_ipc.py status

Subcommands:
  status        KiCad version, open board, footprint count, copper layers
  list          footprints with reference, value, position (mm), rotation, side
  move          move/rotate one footprint
  place-circle  place footprints evenly on a circle
  set-title     edit the title block (title, revision, date, company, comments)
  save          save the open board

Every footprint edit is one commit, so a single Cmd/Ctrl+Z in KiCad undoes the whole
command. Title-block edits are not on KiCad's undo stack.
Nothing is written to disk unless --save is given (or the save subcommand runs).
Coordinates are board millimetres as shown in the PCB editor: X right, Y DOWN.
Angles are degrees counter-clockwise as seen from the top, like KiCad's rotation field.

Exit status: 0 ok, 1 failed, 3 setup error (no connection, no board, kipy missing).
"""
import argparse
import fnmatch
import json
import math
import os
import re
import sys
import threading
import time

try:
    from kipy import KiCad
    from kipy.errors import ApiError, ConnectionError as KiConnectionError
    from kipy.geometry import Angle, Vector2
    from kipy.proto.board.board_types_pb2 import BoardLayer
    from kipy.proto.common.types.base_types_pb2 import DocumentType
except ImportError as e:  # pragma: no cover - environment problem
    sys.stderr.write(
        f"setup error: kipy not importable ({e}).\n"
        "  python3 -m venv ~/.venvs/kicad && ~/.venvs/kicad/bin/pip install kicad-python\n"
        "  then run: ~/.venvs/kicad/bin/python kicad_ipc.py ...\n")
    sys.exit(3)

NM_PER_MM = 1_000_000


class SetupError(Exception):
    pass


# --------------------------------------------------------------------------- connection

def connect(timeout_ms, wait_s=20):
    """Connect; KiCad answers 'not ready' while it is still loading a board, so retry."""
    deadline = time.monotonic() + wait_s
    while True:
        try:
            kicad = KiCad(timeout_ms=timeout_ms)
            kicad.ping()
            kicad.get_open_documents(DocumentType.DOCTYPE_PCB)
            return kicad
        except ApiError as e:
            if "not ready" in str(e).lower() and time.monotonic() < deadline:
                time.sleep(1)
                continue
            raise SetupError(f"KiCad's API answered: {e}")
        except (KiConnectionError, OSError) as e:
            raise SetupError(
                f"cannot reach KiCad's API ({e}). Start KiCad, switch on Preferences > Plugins > "
                "Enable KiCad API, and open the board in the PCB editor.")


def get_board(kicad):
    try:
        return kicad.get_board()
    except ApiError as e:
        raise SetupError(
            f"no board available ({e}). Open the .kicad_pcb in the PCB editor. If the project "
            "manager owns the API socket, open the board from the project or launch the standalone "
            "PCB Editor first.")


# --------------------------------------------------------------------------- helpers

def ref_of(fp):
    return fp.reference_field.text.value


def natural_key(s):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]


def expand_refs(spec, available):
    """'D1-D8', 'D1,D3,R2', 'D*' (glob) or a mix; keeps the given order."""
    out = []
    for part in [p.strip() for p in spec.split(",") if p.strip()]:
        m = re.fullmatch(r"([A-Za-z_#]+)(\d+)-(?:\1)?(\d+)", part)
        if m:
            pre, a, b = m.group(1), int(m.group(2)), int(m.group(3))
            step = 1 if b >= a else -1
            out += [f"{pre}{i}" for i in range(a, b + step, step)]
        elif any(c in part for c in "*?["):
            out += sorted((r for r in available if fnmatch.fnmatchcase(r, part)), key=natural_key)
        else:
            out.append(part)
    missing = [r for r in out if r not in available]
    if missing:
        raise SetupError(f"footprint(s) not on the board: {', '.join(missing)}")
    if len(set(out)) != len(out):
        raise SetupError("a reference appears twice in the list")
    return out


def fp_row(fp):
    p = fp.position
    return {"ref": ref_of(fp), "value": fp.value_field.text.value,
            "x": round(p.x / NM_PER_MM, 4), "y": round(p.y / NM_PER_MM, 4),
            "rot": round(fp.orientation.degrees, 3),
            "side": "front" if fp.layer == BoardLayer.BL_F_Cu else "back"}


def outline_bbox(board):
    """(x0, y0, x1, y1) in mm of the Edge.Cuts shapes, or None. Includes half the line width
    on each side, which doesn't move the centre."""
    shapes = [sh for sh in board.get_shapes() if sh.layer == BoardLayer.BL_Edge_Cuts]
    boxes = board.get_item_bounding_box(shapes) if shapes else []
    if not boxes:
        return None
    x0 = min(b.pos.x for b in boxes)
    y0 = min(b.pos.y for b in boxes)
    x1 = max(b.pos.x + b.size.x for b in boxes)
    y1 = max(b.pos.y + b.size.y for b in boxes)
    return tuple(round(v / NM_PER_MM, 4) for v in (x0, y0, x1, y1))


def resolve_center(spec, board):
    if spec.strip().lower() == "board":
        bb = outline_bbox(board)
        if not bb:
            raise SetupError("--center board: the board has no Edge.Cuts outline")
        return (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
    return parse_xy(spec)


def parse_xy(s):
    try:
        x, y = (float(v) for v in s.split(","))
    except ValueError:
        raise SetupError(f"expected X,Y in mm, got '{s}'")
    return x, y


def commit_edits(board, fps, message, save):
    commit = board.begin_commit()
    try:
        board.update_items(fps)
    except Exception:
        board.drop_commit(commit)
        raise
    board.push_commit(commit, message)
    if save:
        board.save()


# --------------------------------------------------------------------------- commands

def cmd_status(args):
    kicad = connect(args.timeout_ms)
    board = get_board(kicad)
    bb = outline_bbox(board)
    info = {"kicad_version": str(kicad.get_version()), "board": board.name,
            "footprints": len(board.get_footprints()),
            "copper_layers": board.get_copper_layer_count(),
            "outline_mm": list(bb) if bb else None,
            "outline_center_mm": [round((bb[0] + bb[2]) / 2, 4), round((bb[1] + bb[3]) / 2, 4)] if bb else None}
    print(json.dumps(info, indent=2) if args.json else
          "\n".join(f"{k:15} {v}" for k, v in info.items()))
    return 0


def cmd_list(args):
    board = get_board(connect(args.timeout_ms))
    rows = [fp_row(fp) for fp in board.get_footprints()]
    if args.glob:
        rows = [r for r in rows if fnmatch.fnmatchcase(r["ref"], args.glob)]
    rows.sort(key=lambda r: natural_key(r["ref"]))
    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        for r in rows:
            print(f"{r['ref']:8} {r['value']:16} x={r['x']:9.3f} y={r['y']:9.3f} "
                  f"rot={r['rot']:7.2f} {r['side']}")
    return 0


def cmd_move(args):
    board = get_board(connect(args.timeout_ms))
    fps = {ref_of(fp): fp for fp in board.get_footprints()}
    if args.ref not in fps:
        raise SetupError(f"footprint {args.ref} not on the board")
    fp = fps[args.ref]
    x, y = (args.x, args.y)
    if args.relative:
        x += fp.position.x / NM_PER_MM
        y += fp.position.y / NM_PER_MM
    fp.position = Vector2.from_xy_mm(x, y)
    if args.rot is not None:
        fp.orientation = Angle.from_degrees(args.rot)
    if args.dry_run:
        print(json.dumps(fp_row(fp)))
        return 0
    commit_edits(board, [fp], f"Move {args.ref}", args.save)
    print(json.dumps(fp_row(fp)))
    return 0


def cmd_place_circle(args):
    board = get_board(connect(args.timeout_ms))
    fps = {ref_of(fp): fp for fp in board.get_footprints()}
    refs = expand_refs(args.refs, fps)
    cx, cy = resolve_center(args.center, board)
    n = len(refs)
    span = args.span if args.span is not None else 360.0
    step = span / n if abs(span) >= 360 else (span / (n - 1) if n > 1 else 0)
    sign = 1 if args.direction == "ccw" else -1
    rows = []
    for i, ref in enumerate(refs):
        theta = args.start_angle + sign * i * step  # math angle, CCW as seen from the top
        t = math.radians(theta)
        x = cx + args.radius * math.cos(t)
        y = cy - args.radius * math.sin(t)  # board Y grows downward
        fp = fps[ref]
        fp.position = Vector2.from_xy_mm(round(x, 6), round(y, 6))
        if args.facing != "keep":
            rot = theta + (90.0 if args.facing == "tangent" else 0.0) + args.rotation_offset
            fp.orientation = Angle.from_degrees(rot)
        rows.append(fp_row(fp))
    if not args.dry_run:
        commit_edits(board, [fps[r] for r in refs], f"Place {n} footprints on a circle", args.save)
    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        for r in rows:
            print(f"{r['ref']:6} x={r['x']:9.4f} y={r['y']:9.4f} rot={r['rot']:8.3f}")
        print(("dry run - nothing changed" if args.dry_run else
               f"placed {n} footprints (one undo step)") + ("; saved" if args.save and not args.dry_run else ""))
    return 0


def cmd_set_title(args):
    board = get_board(connect(args.timeout_ms))
    tb = board.get_title_block_info()
    for field in ("title", "revision", "date", "company"):
        val = getattr(args, field)
        if val is not None:
            setattr(tb, field, val)
    if args.comment:
        comments = dict(tb.comments)
        for c in args.comment:
            k, _, v = c.partition("=")
            if not k.isdigit() or not 1 <= int(k) <= 9:
                raise SetupError(f"--comment expects N=text with N in 1..9, got '{c}'")
            comments[int(k)] = v
        tb.comments = comments
    board.set_title_block_info(tb)
    if args.save:
        board.save()
    print(json.dumps({"title": tb.title, "revision": tb.revision, "date": tb.date,
                      "company": tb.company, "comments": dict(tb.comments)}, indent=2))
    return 0


def cmd_save(args):
    board = get_board(connect(args.timeout_ms))
    board.save()
    print(f"saved {board.name}")
    return 0


# --------------------------------------------------------------------------- main

def main(argv=None):
    p = argparse.ArgumentParser(prog="kicad_ipc.py", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--timeout-ms", type=int, default=5000, help="per-request API timeout")
    p.add_argument("--timeout", type=int, default=60, help="overall deadline in seconds (default 60)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("status")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("list")
    s.add_argument("--glob", help="filter references, e.g. 'D*'")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_list)

    def edit_flags(sp):
        sp.add_argument("--save", action="store_true", help="save the board after the edit")
        sp.add_argument("--dry-run", action="store_true", help="compute and print, change nothing")

    s = sub.add_parser("move", help="move one footprint to X Y (mm), optionally rotate")
    s.add_argument("ref")
    s.add_argument("x", type=float)
    s.add_argument("y", type=float)
    s.add_argument("--rot", type=float, help="absolute rotation in degrees")
    s.add_argument("--relative", action="store_true", help="X Y are an offset from the current position")
    edit_flags(s)
    s.set_defaults(func=cmd_move)

    s = sub.add_parser("place-circle", help="place footprints evenly on a circle")
    s.add_argument("refs", help="'D1-D8', 'D1,D2,D5' or a glob like 'D*' (natural order)")
    s.add_argument("--center", required=True,
                   help="X,Y in mm, or 'board' for the centre of the Edge.Cuts outline")
    s.add_argument("--radius", type=float, required=True, help="mm")
    s.add_argument("--start-angle", type=float, default=0.0,
                   help="degrees of the first part; 0 = right of centre, 90 = above")
    s.add_argument("--direction", choices=["ccw", "cw"], default="ccw")
    s.add_argument("--span", type=float, help="arc in degrees (default 360 = full circle)")
    s.add_argument("--facing", choices=["radial", "tangent", "keep"], default="radial",
                   help="radial: footprint +X points outward; tangent: +X along the circle")
    s.add_argument("--rotation-offset", type=float, default=0.0,
                   help="degrees added to every computed rotation")
    s.add_argument("--json", action="store_true")
    edit_flags(s)
    s.set_defaults(func=cmd_place_circle)

    s = sub.add_parser("set-title", help="edit the title block")
    for f in ("title", "revision", "date", "company"):
        s.add_argument(f"--{f}")
    s.add_argument("--comment", action="append", help="N=text, N in 1..9 (repeatable)")
    s.add_argument("--save", action="store_true")
    s.set_defaults(func=cmd_set_title)

    s = sub.add_parser("save", help="save the open board")
    s.set_defaults(func=cmd_save)

    args = p.parse_args(argv)

    # kipy can block inside nng's C code, where Python signal handlers never run, so a
    # watchdog thread enforces the overall deadline.
    def _deadline():
        sys.stderr.write(f"setup error: no answer from KiCad within {args.timeout}s. A dialog may be "
                         "open in KiCad (or a macOS 'open for the first time' prompt), or the API "
                         "socket is stale from a crashed KiCad - restart KiCad.\n")
        sys.stderr.flush()
        os._exit(3)

    watchdog = threading.Timer(args.timeout, _deadline)
    watchdog.daemon = True
    watchdog.start()
    try:
        return args.func(args)
    except SetupError as e:
        print(f"setup error: {e}", file=sys.stderr)
        return 3
    except ApiError as e:
        print(f"failed: KiCad API error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
