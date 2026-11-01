#!/usr/bin/env python3
"""Look up PdfCraft automation tools and registry commands without dumping all of
`pdfcraft-cli tools` (183 tools, one large JSON document).

  pf_tool.py NAME...            description and arguments of each tool
  pf_tool.py --search WORD...   tools whose name or description matches every word
  pf_tool.py --commands FILTER  registry commands (menu items) and the tool behind each
"""

import argparse
import textwrap

import pflib


def load_tools():
    data, _ = pflib.run_json(["tools"])
    return {t["name"]: t for t in data}


def arg_line(name, spec, required):
    kind = spec.get("type", "")
    if "enum" in spec:
        kind = "|".join(str(v) for v in spec["enum"])
    elif kind == "array" and isinstance(spec.get("items"), dict):
        kind = f"array<{spec['items'].get('type', '?')}>"
    bounds = []
    for key in ("minimum", "maximum"):
        if key in spec:
            bounds.append(f"{key[:3]} {spec[key]}")
    line = f"  {name}{'*' if required else ''}: {kind}"
    if bounds:
        line += f" ({', '.join(bounds)})"
    if spec.get("description"):
        line += f" — {spec['description']}"
    return line


def show(tool):
    schema = tool.get("input_schema") or {}
    required = set(schema.get("required", []))
    ro = " [read-only]" if tool.get("read_only") else ""
    print(f"## {tool['name']}{ro}")
    print(textwrap.fill(tool.get("description", ""), 100))
    props = schema.get("properties", {})
    if props:
        print("args (* = required):")
        for name, spec in props.items():
            print(arg_line(name, spec, name in required))
    print()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*")
    ap.add_argument("--search", nargs="+", metavar="WORD")
    ap.add_argument("--commands", metavar="FILTER")
    a = ap.parse_args()

    if a.commands is not None:
        data, _ = pflib.run_json(["run", "command_list", f"filter={a.commands}"])
        for c in data.get("commands", []):
            tool = c.get("tool") or "-"
            menu = c.get("menu") or "-"
            print(f"{c['id']:<36} tool={tool:<24} menu={menu:<10} {c.get('label', '')}")
        return

    tools = load_tools()
    if a.search:
        words = [w.lower() for w in a.search]
        for name, t in sorted(tools.items()):
            hay = (name + " " + t.get("description", "")).lower()
            if all(w in hay for w in words):
                print(f"{name:<32} {t.get('description', '').split('. ')[0][:90]}")
        return

    if not a.names:
        ap.error("give tool names, --search or --commands")
    missing = [n for n in a.names if n not in tools]
    for n in a.names:
        if n in tools:
            show(tools[n])
    if missing:
        pflib.die(f"unknown tool(s): {', '.join(missing)} — try --search", 1)


if __name__ == "__main__":
    main()
