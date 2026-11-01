# Workflows: formats and graph recipes

## Two formats

| | UI format (editor File ▸ Save, `user/default/workflows/`) | API format (File ▸ Export (API), `/prompt`) |
|---|---|---|
| Shape | `{nodes: [...], links: [...], definitions: {subgraphs}}` | `{node_id: {class_type, inputs, _meta}}` |
| Widget values | positional `widgets_values` (+ `widgets_values_named` in new editors) | named `inputs` |
| Subgraphs, notes, reroutes, bypass | kept | flattened / dropped |

`comfy.py convert` does the editor's flattening:

- subgraph instances expand into inner nodes with ids `outer:inner` (`18:7`); values typed on
  the instance flow to the inner inputs, and those inputs are tagged
  `_meta.params = {input: exposed_label}` so `--set prompt=…` and `--prompt` find them;
- `Note`/`MarkdownNote` are dropped, `Reroute` is passed through, legacy `PrimitiveNode`
  values are inlined, bypassed (mode 4) nodes pass their same-type input through, muted
  (mode 2) nodes are removed;
- preview nodes nothing consumes (`Preview*`, `ImageCompare`) are dropped (keep with
  `--keep-previews`), then every node that feeds no output node is pruned;
- `widgets_values` (what the editor executes) wins over `widgets_values_named`, which can be
  stale after edits — names come from the named map only when the lengths match.

Positional mapping without names follows `/object_info` input order, skipping the hidden
`control_after_generate` value after a seed and the upload widget after an image combo.
Exotic custom widgets can still misalign; if `validate` shows a value in the wrong input,
ask the user for File ▸ Export (API) of that workflow.

## Starter graphs

[assets/t2i-checkpoint.api.json](../assets/t2i-checkpoint.api.json) is ComfyUI's default
graph (SD 1.5/SDXL checkpoint). Swap `ckpt_name` for a file from `models checkpoints`.
For other model families build from the user's own saved workflow — sampler settings,
latent node and text encoder type are family-specific and guessing them gives noise.

### Split loaders (FLUX, Qwen-Image, SD3, Wan…)

Replace `CheckpointLoaderSimple` with three loaders and rewire:

```
UNETLoader{unet_name} ─MODEL→ KSampler.model
CLIPLoader{clip_name, type: flux2|qwen_image|sd3|…} ─CLIP→ CLIPTextEncode.clip
VAELoader{vae_name} ─VAE→ VAEDecode.vae
```

- `.gguf` diffusion models need the ComfyUI-GGUF custom node: `UnetLoaderGGUF` (same
  `unet_name` input; files listed under the `unet_gguf` folder), `CLIPLoaderGGUF` for gguf
  encoders.
- The latent node is family-specific (`EmptyLatentImage` 4-ch SD, `EmptySD3LatentImage`,
  `EmptyFlux2LatentImage`, …). `nodes --search latent` lists them.
- Distilled/turbo models want low steps and `cfg` 1 — copy these from the user's workflow.

### Img2img

```
LoadImage{image} ─IMAGE→ VAEEncode{pixels, vae} ─LATENT→ KSampler.latent_image
KSampler{denoise: 0.3–0.7}
```

Replace the empty-latent node with the `VAEEncode`; nothing else changes. With
`SamplerCustomAdvanced` graphs, denoise comes from the sigmas: `BasicScheduler.denoise`,
or drop the first entries of a `ManualSigmas` list.

### Inpainting

```
LoadImage (RGBA: transparent = repaint) ─IMAGE→ VAEEncodeForInpaint{pixels, vae, mask, grow_mask_by: 6}
                                         └MASK─┘                        ─LATENT→ KSampler{denoise: 1.0}
```

- `VAEEncodeForInpaint` blanks the masked area — use with inpaint models at denoise 1.0.
- For ordinary models: `VAEEncode` → `SetLatentNoiseMask{samples, mask}` → sampler with
  denoise 0.5–0.9.
- A separate black/white mask file: `LoadImageMask{image, channel: red}` (white = repaint).
- `InpaintModelConditioning` is the variant for models with inpaint conditioning (FLUX Fill).

### Batches inside one prompt

`batch_size` on the latent node makes N images from one seed in one prompt (faster, but the
images are not reproducible one by one). For per-image seeds use `comfy.py batch --seeds`.
