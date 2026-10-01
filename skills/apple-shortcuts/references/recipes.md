# Recipes

`S` is this skill's `scripts/` directory.

## A reusable step: bash

```bash
#!/usr/bin/env bash
# word-count.sh FILE  -> prints the count, or exits non-zero with the reason on stderr
set -euo pipefail
S=/path/to/apple-shortcuts/scripts
[[ -f "${1:-}" ]] || { echo "usage: word-count.sh FILE (file must exist)" >&2; exit 2; }
json=$(python3 "$S/sc-run.py" "Word Count" -i "$1" --timeout 30) && rc=0 || rc=$?
if (( rc != 0 )); then
  echo "Word Count failed (exit $rc): $(python3 -c 'import json,sys; print(json.load(sys.stdin).get("error",""))' <<<"$json")" >&2
  exit "$rc"
fi
python3 -c 'import json,sys; print(json.load(sys.stdin)["stdout"])' <<<"$json"
```

## A reusable step: Python

```python
import json, subprocess

def run_shortcut(name, *inputs, output=None, expect=None, timeout=60, script="scripts/sc-run.py"):
    cmd = ["python3", script, name, "--timeout", str(timeout)]
    for p in inputs:
        cmd += ["-i", p]
    if output:
        cmd += ["-o", output]
    if expect:
        cmd += ["--expect", expect]
    r = subprocess.run(cmd, capture_output=True, text=True)
    res = json.loads(r.stdout)
    if r.returncode != 0:
        raise RuntimeError(f"{name}: exit {r.returncode}: {res.get('error')}")
    return res["stdout"] if output is None else output
```

## Chaining

```bash
python3 $S/sc-run.py "Resize" -i photo.heic -o /tmp/step1.png --expect image &&
python3 $S/sc-run.py "Add Watermark" -i /tmp/step1.png -o final.png --expect image
```

- Pass files between steps rather than piping binary data.
- Text results move through the JSON's `stdout`, or `--stdin` into the next step.
- Stop the chain on the first non-zero exit. Each step checks its own output.

## Batches

```bash
python3 $S/sc-run.py "Resize" --batch ~/in --out ~/out --glob '*.jpg' --glob '*.png' --glob '*.heic' --expect image
# interrupted or partly failed? fix the cause and run the same command again: done items are skipped
```

## Scheduling

- `launchd`/`cron` jobs run outside the GUI session's permissions. Shortcuts that touch
  Photos, Contacts or the network may prompt, and a prompt hangs the run.
- Run the shortcut once interactively, so the prompts are answered, before scheduling it.
- Always keep the timeout.

## Building by hand

When an action isn't in `sc-build.py`'s verified list, give the user editor steps.
Menu wording varies between releases and UI languages:

1. Shortcuts › File › New Shortcut (⌘N), then name it in the title bar.
2. Open the ⓘ panel (Shortcut Details) and turn on "Use as Quick Action" or "Receive
   input", choosing the input types. This is what makes `-i` and stdin reach it.
3. Search the action list on the right (for example "Change Case"), drag it in, and
   click its blue parameter tokens to set them. Insert **Shortcut Input** as the variable.
4. End with **Stop and Output**, set to the last result. Without it there may be nothing
   for `-o` or stdout.
5. Test it from the agent with `sc-run.py NAME --stdin test --timeout 20`.

To reuse it elsewhere, export it (Share › Export File) and decode it with `sc-decode.py`.
