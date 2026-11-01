---
name: comfyui
description: 'Drive a local ComfyUI server (source or Desktop) via its HTTP API with a dependency-free Python client — run workflow templates with overrides (prompt, seed, size, steps, model), batch over prompt lists or image folders with fixed seeds, img2img and inpainting with uploaded inputs, list installed nodes and models, convert editor-saved workflows to API format, validate before queuing, cancel runs, and collect outputs with their parameters. Use whenever the user wants images generated or transformed with ComfyUI or local diffusion models on their own machine (Stable Diffusion, SDXL, FLUX, Qwen-Image, GGUF), or mentions a ComfyUI workflow JSON, node_errors or the ComfyUI queue — e.g. "run my ComfyUI workflow with seeds 1–4", "img2img this folder in ComfyUI", "which checkpoints do I have", "generate variations locally with FLUX". Not for cloud generators (picsart-*, generate-media), painting or retouching in Krita/GIMP/Pixelmator, plain resizing or conversion (imagemagick), or 3D renders (blender).
summary: "drive a local ComfyUI server over its HTTP API — parameterised workflow runs, prompt and image-folder batches with seed control, img2img and inpainting uploads, node and model inspection, editor-to-API workflow conversion, pre-queue validation, scoped cancel, outputs with params sidecars and PNG-metadata checks"
category: design-automation
compatibility: "Built for ComfyUI 0.42.0 (source install, Python 3.12 venv) and Comfy Desktop 1.1.8 on macOS 27, Apple silicon (MPS); ComfyUI-GGUF for .gguf models. Client scripts need Python 3.9+."
risk: medium
tags:
    - comfyui
    - stable-diffusion
    - image-generation
    - workflows
    - local-ai
license: GPL-3.0-only
metadata:
  version: "1.0.0"
  author: "Tamás Jablonkai"
---

# ComfyUI Control

ComfyUI is a node-graph runner for diffusion models that is itself a local HTTP server
(source install: `127.0.0.1:8188`; Comfy Desktop: `127.0.0.1:8000`). A run is one
**API-format workflow** — `{node_id: {class_type, inputs}}` — posted to `/prompt`; the
server queues it, executes it, and records outputs under `/history/{prompt_id}`. Everything
here goes through [scripts/comfy.py](scripts/comfy.py), a standard-library client (Python
3.9+, nothing to install) that prints JSON on stdout, progress on stderr, and exits 1 on
failure. Verified against **ComfyUI 0.42.0** (macOS, MPS) and **Comfy Desktop 1.1.8**.

```bash
C=~/.claude/skills/comfyui/scripts/comfy.py     # adjust to where the skill lives
python3 $C status                                # version, device memory, queue
```

## The run loop

1. **Find the server** — `status`. It tries `$COMFYUI_URL`, then `:8188`, then `:8000`. Not
   running → `python3 $C server start` (headless, `~/ComfyUI` or `$COMFYUI_ROOT`, loopback
   only, adds `--cache-none` on ≤ 16 GB machines). With Desktop, ask the user to open it.
   The queue is shared with the editor: if `status` shows prompts you didn't queue, the
   user is working — say so before adding a long batch behind them.
2. **Look before you build** — `models --all` (non-empty model folders) and
   `nodes --search TEXT` / `nodes --class KSampler` (inputs, enum options, ranges). Model
   names in a workflow must match these exactly.
3. **Get a workflow.** Prefer one the user already runs: editor saves live in
   `<root>/user/default/workflows/*.json` (UI format). `comfy.py` accepts UI or API format
   everywhere and converts on the fly; `convert UI.json -o api.json` writes the API file
   when you want to read or edit it. A starter graph is in
   [assets/](assets/) (checkpoint models only — see [workflows.md](references/workflows.md)
   for split-loader and GGUF graphs).
4. **Find the knobs** — `inspect WF` lists every node with id, class, title, literal
   inputs and links, plus a `parameters` summary (seeds, steps, size, models, texts).
5. **Validate** — `validate WF [overrides]` checks classes, required inputs, links and
   enum/range values against `/object_info` and queues nothing. `run` repeats this check
   and refuses to queue on errors; the server then validates again (`node_errors`).
6. **Run** — `run WF [overrides] --out DIR`: queue, wait (polling `/history`), download
   every saved output into DIR, and write `<file>.params.json` (prompt_id, status, seconds,
   overrides, seeds, steps, size, models, prompt texts) plus `runs.jsonl`. A timeout
   (`--timeout`, default 1800 s per prompt) does not cancel the prompt: the server keeps
   going, and `collect PROMPT_ID --out DIR` downloads the result once it is done.
7. **Verify** — `scripts/check_outputs.py DIR --count N --width W --height H --seeds S
   --history` (below). Report the files, the seeds and the time per image.

## Overrides

| Flag | Sets |
|---|---|
| `--prompt T` / `--negative T` | the text feeding the sampler's positive / negative input (exposed subgraph `prompt` param first, else traced from `positive`) |
| `--seed N` | every `seed`/`noise_seed` input |
| `--steps N` | every `steps` input |
| `--width W --height H` | width/height on latent/image nodes — replaces a link from a resolution picker |
| `--image PATH` / `--mask PATH` | uploads, then sets the single `LoadImage` / `LoadImageMask` |
| `--set TARGET.input=VALUE` | anything: TARGET = node id (`18:7` inside a subgraph), `_meta.title`, or a unique class_type |
| `--set param=VALUE` | a parameter the editor exposed on a subgraph (shown as `params` in `inspect`) |

VALUE is parsed as JSON when it can be (`5`, `0.6`, `true`, `"text"`), else used as a
string; `@/path/file.png` uploads the file and uses its input name. `--set ID.class_type=X`
swaps a node's class (e.g. `UNETLoader` → `UnetLoaderGGUF`, same `unet_name` input). Every
override is echoed in the result — check that it hit the node you meant.

## Batches

```bash
python3 $C batch WF --prompts prompts.txt --seeds 101-104 --out DIR   # each prompt × each seed
python3 $C batch WF --images in/ --set KSampler.denoise=0.55 --seed 7 --out DIR   # img2img per file
```

`--prompts` takes one prompt per line (`#` comments), or `.jsonl` lines like
`{"prompt": "...", "set": {"KSampler.cfg": 4}}`. `--images` uploads each file into the
`LoadImage` node. Items run one after another; each is recorded in `DIR/batch.jsonl`, a
failed item does not stop the rest, and `--resume` skips items already done and *collects*
timed-out ones from `/history` instead of rendering them again. Local names
default to `{stem}` (input image name) or `{stem}_s{seed}`; change with `--name`
(`{stem} {index} {seed} {orig} {n} {prompt_id}`).

## Img2img and inpainting

- **Img2img**: `LoadImage` → `VAEEncode` (with the model's VAE) → sampler `latent_image`,
  `denoise` 0.3–0.7 (lower keeps more of the input). Output size follows the input, rounded
  down to the latent multiple (8 or 16) — feed sizes that are already multiples.
- **Inpainting**: the mask is white = repaint. Either upload an RGBA image whose
  transparent pixels are the hole (`LoadImage` outputs that as MASK), or a separate mask via
  `LoadImageMask`. Wire `VAEEncodeForInpaint` (denoise 1.0, inpaint models) or
  `SetLatentNoiseMask` (any model, denoise < 1). Recipes: [workflows.md](references/workflows.md).

## Verifying

`check_outputs.py` reads files only — dimensions for PNG/JPEG/WebP, and in PNGs the
`prompt` chunk (the exact API graph that ran, seeds included) and `workflow` chunk (editor
graph; present when the run came from a UI-format file). `--history` re-reads
`/history/{prompt_id}` from the sidecars and requires `success`. A run counts as done only
when the count, sizes and seeds check out — not when `run` returned.

## Stopping

`python3 $C stop` interrupts and dequeues **only prompts this client queued** (their
`client_id` starts with `comfyui-skill-`), leaving the user's editor jobs alone. `--all`
cancels everyone's — only when the user asks. `server stop` stops a server that
`server start` launched (pid file in `~/.cache/comfyui-skill/`), never one the user started.

## Reference routing

| Need | Read |
|---|---|
| Endpoint shapes, `/history` layout, error types, WebSocket messages | [api.md](references/api.md) |
| UI vs API format, subgraphs, graphs for checkpoint / split / GGUF / img2img / inpaint | [workflows.md](references/workflows.md) |
| Something behaves oddly (no output, OOM, wrong seed, cached run, 0 checkpoints) | [gotchas.md](references/gotchas.md) |
| Exposing the server, custom nodes, downloaded workflows | [security.md](references/security.md) |

## Key gotchas

- **Models can live outside `checkpoints/`.** Modern models are split (diffusion model +
  text encoder + VAE) and `.gguf` files appear in the `unet_gguf` folder, not
  `diffusion_models`. "No checkpoints" is not "no models" — report what `models --all` shows.
- **A seed in the file is fixed.** The editor's *randomize* only applies in the editor; via
  the API the stored seed runs again. Pass `--seed` for every run you want reproducible or
  different.
- **`node_errors` with HTTP 200 still queues** the outputs that did validate. `comfy.py`
  removes such a partial prompt; when posting by hand, check `node_errors` first.
- **Memory**: on 16 GB Apple silicon a 1024² run of an 8–12 GB model swaps; use 512–768 px
  and `--cache-none`, and don't queue next to a running editor batch.

## Safety

- Generation is GPU-heavy and runs on the user's machine: say how many images a batch will
  make before starting one larger than ~10.
- Outputs land in ComfyUI's `output/` folder as well as `--out`. Delete only files you made.
- Installing custom nodes (Manager, `git clone` into `custom_nodes/`) runs third-party code
  — only on the user's explicit request, and never to make a downloaded workflow "work".
