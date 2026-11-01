# Gotchas

| Symptom | Cause | Fix |
|---|---|---|
| `models checkpoints` is empty but the user generates fine | split loaders: models are in `diffusion_models`, `unet_gguf`, `text_encoders`, `vae` | `models --all`; report every non-empty folder |
| `.gguf` not in `diffusion_models` | ComfyUI-GGUF registers its own `unet_gguf` / `clip_gguf` folders | use those names with `UnetLoaderGGUF` / `CLIPLoaderGGUF` |
| same image every run | the seed is a literal in the API graph; *randomize* is editor-only | pass `--seed` |
| run finished, no files | cached: identical prompt with caching on executes nothing new; or no Save node (previews are `temp`) | change seed; `--include-temp`; add `SaveImage` |
| prompt "rejected" yet it ran later | `node_errors` with HTTP 200 queues the valid outputs | `comfy.py` dequeues it; by hand, `POST /queue {"delete": [id]}` |
| `bad_linked_input` on a list value | a bare list reads as a link | wrap as `{"__value__": [...]}` |
| `value_not_in_list` on a model name | name differs from disk (subfolder prefix, case, extension) | copy exactly from `models FOLDER` |
| process killed / machine swaps on Apple silicon | models stay cached in unified memory | `--cache-none` (added by `server start` on ≤ 16 GB), 512–768 px, `POST /free` between jobs |
| `Port 8188 is already in use` | a server is already running (editor tab, Desktop, `start.sh`) | use it — `status` finds it |
| your job sits at "pending #N" | the editor's queue is ahead of you | tell the user; never `stop --all` to jump the queue |
| `--width` "replaced link" | the size came from a resolution picker node | intended: the literal now drives the latent |
| output ~8–16 px smaller than the input | latents are 1/8 (SD) or 1/16 (FLUX 2) of the image | feed sizes that are multiples of 16 |
| prompt upsampler / LLM node runs although switched off | a `PreviewAny` on its output forces it to execute | `convert` drops unconsumed previews by default |
| subgraph value ignored | the instance's `widgets_values_named` is stale | `convert` prefers positional values; check `inspect` |
| `missing_node_type` | workflow from the internet uses a custom node | tell the user which; installing it is their decision (see security.md) |
| MPS: `not implemented for 'MPS'` | an op without an MPS kernel | `PYTORCH_ENABLE_MPS_FALLBACK=1` (set by `server start`) |
