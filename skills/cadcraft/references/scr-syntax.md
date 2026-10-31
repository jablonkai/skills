# .scr scripts in CADCraft 0.15.1

`--script TEXT`, `--script-file F.scr`, the `script` session step and `cc_build.py`'s
`{"script": …}` item all feed text to the command line as typed input. Prefer JSON
commands: they take complete params, fail loudly, and return handles. Use a script when
the user hands you one or for quick geometry.

## Rules (verified)

- A **space or a newline** ends an input, as in AutoCAD (except inside TEXT content);
  a blank line is Enter.
- Coordinates: `x,y` absolute, `@dx,dy` relative, `@dist<angle` polar.
- Command names and aliases work (`LINE`/`L`, `CIRCLE`/`C`, `RECTANG`/`REC`, `PLINE`/`PL`).
- An unknown command stops the run with exit 1 (`unknown command \`FOO\``), nothing saved.

## Work on one line

```
LINE 0,0 50,0 50,30 C
CIRCLE 25,15 5
CIRCLE 0,0 D 6
PLINE 60,0 100,0 A 100,30 L 60,30 C
RECTANG 0,-40 @40,20
DIMLINEAR 0,0 50,0 25,-10
ZOOM E
```

## Break silently

- **`TEXT`/`DTEXT`** keeps reading: after the text it starts a new text line and takes
  every following script line as more text until a **blank line**. `TEXT 0,40 5 0 Hello
  script` followed directly by `CIRCLE 0,0 3` produced Text "Hello script", Text "CIRCLE
  0,0 3" and no circle. Spaces inside the text are literal. Fix: a blank line right
  after every TEXT line — or use the `text`/`mtext` JSON commands.
- **`-LAYER` chains** broke the rest of the script in 0.8.0; in 0.15.1 `-LAYER M GEOM C 3
  GEOM` + a blank line makes GEOM green and current, and later lines run. Still check
  the layer table with `info` after a script that sets layers — and prefer
  `layer.new {"name": "GEOM", "color": "Green", "current": true}`.
- Any command whose prompt sequence you don't know exactly. Check with a dry run on a
  scratch drawing and `cadcraft-cli info` before trusting it.

## Check a script

Run it with `--save` to a scratch file, then `cadcraft-cli info` the counts: the stderr
echo shows only `Command: X` lines, not whether the inputs landed where you meant.
