#!/usr/bin/env python3
"""Build or edit a MaterialCraft graph from a JSON spec, cook it and read it back.

The spec names its new nodes, so wires, outputs, exposed inputs and raw steps can refer to
them before their numeric ids exist:

  {
    "in": "base.sbs",                    # or "template": "empty", "size": 1024, "name": "Rock"
    "graph": 0,                             # graph index to edit (default: the package's open graph)
    "nodes": {"noise": {"def": "pixel_processor"},
              "lev":   {"def": "levels"}},
    "wires": [["noise", "lev"], ["noise:output", "blend:mask"], [12, "lev"]],
    "outputs": {"roughness": {"from": "lev", "usage": "Roughness"}},
    "params": [{"node": 13, "param": "out_high", "value": 0.4}],
    "exposed": [{"id": "rough", "label": "Roughness", "default": 0.5, "min": 0, "max": 1,
                 "bind": [{"node": "lev", "param": "out_high"}]}],
    "presets": [{"name": "glossy", "values": {"rough": 0.1}}],
    "steps": [{"id": "graph.node.base", "params": {"id": "@noise", "tiling": true}}],
    "save": "out.sbs"
  }

A node reference is a spec name or an existing node's integer id. A wire end is NODE or
NODE:PORT; the target port defaults to the node's first input, the source port to `output`.
In raw steps, a string "@name" becomes that node's id.

Every node def, parameter key, port, usage and command key is checked against the CLI's own
registries before anything runs (the CLI ignores unknown command keys silently). The build runs
as two batches (add nodes, then wire/configure/cook/save), so a failure saves nothing. The result
is read back: nodes, wires, outputs, exposed inputs, bindings, presets, and a full cook with no
errors. Prints JSON; exits 1 on any failed check.
"""
import argparse
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mclib as m  # noqa: E402


def parse_end(end, is_target):
    if isinstance(end, int):
        return end, None
    s = str(end)
    node, _, port = s.partition(":")
    node = int(node) if node.isdigit() else node
    return node, (port or None)


class Builder:
    def __init__(self, spec, args):
        self.spec = spec
        self.args = args
        self.problems = []
        self.base_graph = None
        self.names = {}

    # ---- validation -----------------------------------------------------------

    def def_of(self, ref):
        if isinstance(ref, int):
            for n in (self.base_graph or {}).get("nodes", []):
                if n["id"] == ref:
                    return n["def"]
            self.problems.append("node %d does not exist in the input graph" % ref)
            return None
        if ref not in self.spec.get("nodes", {}) and ref not in self.out_names():
            self.problems.append("unknown node name `%s`" % ref)
            return None
        if ref in self.out_names():
            return "output"
        return self.spec["nodes"][ref].get("def")

    def out_names(self):
        return {"out:" + k for k in self.spec.get("outputs", {})}

    def check_port(self, ref, port, kind):
        d = self.def_of(ref)
        if d is None:
            return
        nd = m.nodes().get(d)
        if nd is None:
            return
        ports = [p["id"] for p in nd.get(kind, [])]
        if port is not None and port not in ports:
            self.problems.append("node `%s` (%s) has no %s port `%s`; it has %s" % (ref, d, kind[:-1], port, ports))
        if port is None and not ports:
            self.problems.append("node `%s` (%s) has no %s" % (ref, d, kind))

    def check_param(self, d, key, where):
        nd = m.nodes().get(d)
        if nd and key not in [p["id"] for p in nd["params"]]:
            self.problems.append("%s: `%s` has no parameter `%s`; it has %s"
                                 % (where, d, key, [p["id"] for p in nd["params"]]))

    def validate(self):
        lib = m.nodes()
        for name, n in self.spec.get("nodes", {}).items():
            if name.isdigit() or ":" in name or name.startswith("out:"):
                self.problems.append("node name `%s`: use a word, not a number or a colon" % name)
            d = n.get("def")
            if d not in lib:
                close = [k for k in lib if d and (d in k or k in d)][:8]
                self.problems.append("node `%s`: unknown def `%s`%s" % (name, d, " (close: %s)" % close if close else ""))
                continue
            for k in n.get("params", {}):
                self.check_param(d, k, "node `%s`" % name)
            bad = set(n) - {"def", "params", "at", "label"}
            if bad:
                self.problems.append("node `%s`: unknown keys %s" % (name, sorted(bad)))
        for w in self.spec.get("wires", []):
            if not (isinstance(w, list) and len(w) == 2):
                self.problems.append("wire %r: write [FROM, TO]" % (w,))
                continue
            (a, ap), (b, bp) = parse_end(w[0], False), parse_end(w[1], True)
            self.check_port(a, ap or "output", "outputs")
            self.check_port(b, bp, "inputs")
        for ident, o in self.spec.get("outputs", {}).items():
            try:
                m.usage_index(o.get("usage", "Any"))
            except m.McError as e:
                self.problems.append("output `%s`: %s" % (ident, e))
            src, sp = parse_end(o.get("from"), False)
            self.check_port(src, sp or "output", "outputs")
        for p in self.spec.get("params", []):
            d = self.def_of(parse_end(p.get("node"), False)[0])
            if d:
                self.check_param(d, p.get("param"), "params")
        exposed_ids = {e.get("id") for e in self.spec.get("exposed", [])}
        exposed_ids |= {e["id"] for e in (self.base_graph or {}).get("exposed", [])}
        for e in self.spec.get("exposed", []):
            binds = e.get("bind", [])
            for b in binds if isinstance(binds, list) else [binds]:
                d = self.def_of(parse_end(b.get("node"), False)[0])
                if d:
                    self.check_param(d, b.get("param"), "exposed `%s` bind" % e.get("id"))
            if "default" not in e:
                self.problems.append("exposed `%s`: needs a `default`" % e.get("id"))
        for pr in self.spec.get("presets", []):
            for k in pr.get("values", {}):
                if k not in exposed_ids:
                    self.problems.append("preset `%s`: no exposed input `%s`" % (pr.get("name"), k))
        for i, st in enumerate(self.spec.get("steps", [])):
            for pb in m.check_step(st.get("id"), st.get("params")):
                self.problems.append("step %d: %s" % (i, pb))
        bad = set(self.spec) - {"in", "template", "size", "name", "graph", "nodes", "wires", "outputs",
                                "params", "exposed", "presets", "steps", "save"}
        if bad:
            self.problems.append("spec: unknown keys %s" % sorted(bad))

    # ---- batches --------------------------------------------------------------

    def ref(self, r):
        node, _ = parse_end(r, False)
        return node if isinstance(node, int) else self.names[node]

    def resolve(self, v):
        if isinstance(v, str) and v.startswith("@") and v[1:] in self.names:
            return self.names[v[1:]]
        if isinstance(v, list):
            return [self.resolve(x) for x in v]
        if isinstance(v, dict):
            return {k: self.resolve(x) for k, x in v.items()}
        return v

    def add_steps(self):
        steps, order = [], []
        if self.spec.get("graph") is not None:
            steps.append({"id": "graph.open", "params": {"graph": self.spec["graph"]}})
        x0 = 0
        if self.base_graph and self.base_graph.get("nodes"):
            x0 = max(n["pos"][0] for n in self.base_graph["nodes"]) + 300
        for i, (name, n) in enumerate(self.spec.get("nodes", {}).items()):
            p = {"def": n["def"], "at": n.get("at", [x0 + 220 * i, 0])}
            if n.get("params"):
                p["params"] = n["params"]
            p["label"] = n.get("label", name)
            steps.append({"id": "graph.node.add", "params": p})
            order.append(name)
        k = len(order)
        for j, (ident, o) in enumerate(self.spec.get("outputs", {}).items()):
            steps.append({"id": "graph.node.add", "params": {
                "def": "output", "at": [x0 + 220 * (k + 1), 160 * j],
                "params": {"identifier": ident, "usage": m.usage_index(o.get("usage", "Any"))}}})
            order.append("out:" + ident)
        return steps, order

    @staticmethod
    def selected(step):
        """graph.node.* and edit.* commands refuse to run with an empty selection, even when given
        `id`/`ids`; select the target first so the step acts on it."""
        p = step.get("params", {})
        target = p.get("ids") or ([p["id"]] if isinstance(p.get("id"), int) else None)
        cid = step["id"]
        if target and (cid.startswith("graph.node.") or cid.startswith("edit.")) and cid != "graph.node.add":
            return [{"id": "graph.select", "params": {"ids": target}}, step]
        return [step]

    def config_steps(self):
        st = []
        if self.spec.get("graph") is not None:
            st.append({"id": "graph.open", "params": {"graph": self.spec["graph"]}})
        for w in self.spec.get("wires", []):
            (a, ap), (b, bp) = parse_end(w[0], False), parse_end(w[1], True)
            p = {"from": self.ref(a), "to": self.ref(b)}
            if ap:
                p["fromPort"] = ap
            if bp:
                p["toPort"] = bp
            st.append({"id": "graph.connect", "params": p})
        for ident, o in self.spec.get("outputs", {}).items():
            a, ap = parse_end(o["from"], False)
            p = {"from": self.ref(a), "to": self.names["out:" + ident]}
            if ap:
                p["fromPort"] = ap
            st.append({"id": "graph.connect", "params": p})
        for p in self.spec.get("params", []):
            st += self.selected({"id": "graph.node.param", "params": {
                "id": self.ref(p["node"]), "param": p["param"], "value": p["value"]}})
        for e in self.spec.get("exposed", []):
            p = {k: e[k] for k in ("id", "label", "min", "max", "group") if k in e}
            p["default"] = m.typed(e["default"])
            binds = e.get("bind", [])
            binds = binds if isinstance(binds, list) else [binds]
            st.append({"id": "graph.exposed.add", "params": p})
            for b in binds:
                st += self.selected({"id": "graph.node.bind", "params": {
                    "id": self.ref(b["node"]), "param": b["param"], "input": e["id"]}})
        for raw in self.spec.get("steps", []):
            st += self.selected({"id": raw["id"], "params": self.resolve(raw.get("params", {}))})
        if self.spec.get("presets"):
            defaults = {e["id"]: e["default"] for e in (self.base_graph or {}).get("exposed", [])}
            defaults.update({e["id"]: m.typed(e["default"]) for e in self.spec.get("exposed", [])})
            for pr in self.spec["presets"]:
                for k, v in pr.get("values", {}).items():
                    st.append({"id": "graph.exposed.set", "params": {"id": k, "value": v}})
                st.append({"id": "graph.preset.save", "params": {"name": pr["name"]}})
                for k in pr.get("values", {}):  # back to the defaults, so presets don't leak into the save
                    st.append({"id": "graph.exposed.set", "params": {"id": k, "value": defaults[k]}})
        return st

    # ---- run ------------------------------------------------------------------

    def build(self):
        a = self.args
        out = a.save or self.spec.get("save")
        if not out:
            raise m.McError("no output: give `save` in the spec or --save")
        out = m.sbs_path(out)  # the CLI keeps .sbs/.mcraft and appends .sbs to any other extension (out.foo -> out.foo.sbs)
        inp = a.inp or self.spec.get("in")
        if inp and m.same_file(inp, out):
            raise m.McError("refusing to write over the input; save to a new path")
        if not a.dry_run:
            m.refuse_overwrite(out, a.overwrite)
        tmpdir = tempfile.mkdtemp(prefix="mcbuild-")
        if inp:
            if not os.path.exists(inp) and inp != "sample":
                raise m.McError("input %s not found" % inp)
            base = inp
        else:
            tpl = self.spec.get("template", "empty")
            base = os.path.join(tmpdir, "base.sbs")
            args = ["new", tpl, base]
            if self.spec.get("size"):
                args += ["--size", str(self.spec["size"])]
            if self.spec.get("name"):
                args += ["--name", self.spec["name"]]
            m.run(args)  # into the temp dir, so a dry run still sees the template's nodes
        self.base_graph = m.graph_of(base, self.spec.get("graph"))
        self.validate()
        if self.problems:
            return {"ok": False, "problems": self.problems}

        add, order = self.add_steps()
        mid = os.path.join(tmpdir, "nodes.sbs")
        if a.dry_run:
            self.names = {n: "<%s>" % n for n in order}
            return {"ok": True, "dry_run": True, "batch_1": add, "batch_2": self.config_steps()}
        res = self.batch({"open": os.path.abspath(base), "steps": add, "save": mid}, tmpdir, "add")
        ids = [r["id"] for r in res["results"] if isinstance(r, dict) and "id" in r]
        if len(ids) != len(order):
            raise m.McError("expected %d node ids from the add batch, got %r" % (len(order), res["results"]))
        self.names = dict(zip(order, ids))
        conf = self.config_steps()
        self.batch({"open": mid, "steps": conf, "save": os.path.abspath(out)}, tmpdir, "config")
        return self.verify(out)

    def batch(self, script, tmpdir, tag):
        path = os.path.join(tmpdir, "batch-%s.json" % tag)
        with open(path, "w") as f:
            json.dump(script, f)
        return m.run_json(["batch", path])

    def verify(self, out):
        g = m.graph_of(out, self.spec.get("graph"))
        checks, fails = [], []
        by_id = {n["id"]: n for n in g["nodes"]}
        for name, nid in self.names.items():
            want = "output" if name.startswith("out:") else self.spec["nodes"][name]["def"]
            got = by_id.get(nid, {}).get("def")
            (checks if got == want else fails).append("node %s = %s (%s)" % (name, nid, got))
        conns = {(c["from"], c["to"], c["toPort"]) for c in g["connections"]}
        for w in self.spec.get("wires", []):
            (a, _), (b, bp) = parse_end(w[0], False), parse_end(w[1], True)
            fa, tb = self.ref(a), self.ref(b)
            port = bp or m.nodes()[by_id[tb]["def"]]["inputs"][0]["id"]
            ok = (fa, tb, port) in conns
            (checks if ok else fails).append("wire %s -> %s:%s" % (w[0], w[1] if bp else w[1], port))
        outs = {o["identifier"]: o for o in m.outputs(g)}
        for ident, o in self.spec.get("outputs", {}).items():
            got = outs.get(ident)
            want_src = self.ref(parse_end(o["from"], False)[0])
            ok = got and got["source"] == want_src and got["usage"] == m.USAGES[m.usage_index(o.get("usage", "Any"))]
            (checks if ok else fails).append("output %s <- %s (%s)" % (ident, o["from"], got and got["usage"]))
        exposed = {e["id"] for e in g.get("exposed", [])}
        bound = {(n["id"], k): v for n in g["nodes"] for k, v in n.get("bindings", {}).items()}
        for e in self.spec.get("exposed", []):
            (checks if e["id"] in exposed else fails).append("exposed %s" % e["id"])
            binds = e.get("bind", [])
            for b in binds if isinstance(binds, list) else [binds]:
                ok = bound.get((self.ref(b["node"]), b["param"])) == e["id"]
                (checks if ok else fails).append(
                    "bind %s -> %s.%s (0.4.1 does not save bindings in .sbs)" % (e["id"], b["node"], b["param"]))
        presets = {p["name"] for p in g.get("presets", [])}
        for pr in self.spec.get("presets", []):
            (checks if pr["name"] in presets else fails).append(
                "preset %s (0.4.1 does not save presets in .sbs)" % pr["name"])
        cook_args = ["cook", out, "--full"]
        if self.spec.get("graph") is not None:
            cook_args += ["--graph", str(self.spec["graph"])]
        errs = m.cook_errors(m.run_json(cook_args))
        if errs:
            fails.append("cook errors: %s" % errs)
        unwired = [o["identifier"] for o in m.outputs(g) if o["source"] is None]
        if unwired:
            fails.append("outputs with nothing wired in: %s" % unwired)
        return {"ok": not fails, "saved": out, "graph": g["name"], "size": g.get("size"),
                "nodes": len(g["nodes"]), "ids": self.names,
                "outputs": [{k: o[k] for k in ("identifier", "usage", "source")} for o in m.outputs(g)],
                "exposed": sorted(exposed), "presets": sorted(presets),
                "cook_errors": errs, "checked": len(checks), "failed": fails}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", help="JSON spec file")
    ap.add_argument("--in", dest="inp", help="input .sbs (overrides the spec's `in`)")
    ap.add_argument("--save", help="output .sbs (overrides the spec's `save`)")
    ap.add_argument("--overwrite", action="store_true", help="replace an existing output")
    ap.add_argument("--dry-run", action="store_true", help="validate and print the two batches; run nothing")
    a = ap.parse_args()
    try:
        with open(a.spec) as f:
            spec = json.load(f)
    except (OSError, ValueError) as e:
        raise m.McError("cannot read spec %s: %s" % (a.spec, e))
    res = Builder(spec, a).build()
    m.emit(res, ok=res.get("ok", False))


if __name__ == "__main__":
    m.main_guard(main)
