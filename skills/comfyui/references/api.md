# ComfyUI HTTP / WebSocket API

Checked against ComfyUI 0.42.0 (`server.py`, `openapi.yaml` in the checkout). Every route
is also served under `/api/…` (the editor uses that prefix). No authentication: anything
that can reach the port can queue work, read outputs and upload files.

## Endpoints

| Method + path | Use | Notes |
|---|---|---|
| `GET /system_stats` | version, OS, RAM, devices (VRAM), launch `argv` | cheapest liveness probe |
| `GET /object_info` | the whole node catalog (several MB) | `/object_info/{class}` for one node |
| `GET /models` | model folder names | `/models/{folder}` lists files in one |
| `POST /prompt` | queue a workflow | body below; `GET /prompt` = queue size |
| `GET /queue` | `{queue_running, queue_pending}` | items: `[number, prompt_id, prompt, extra_data, outputs]` |
| `POST /queue` | `{"delete": [prompt_id…]}` or `{"clear": true}` | `clear` wipes **everyone's** pending prompts |
| `POST /interrupt` | stop the running prompt | `{"prompt_id": id}` interrupts only if that one runs; `{}` = global |
| `GET /history[/{prompt_id}]` | finished prompts with outputs and status | `?max_items=N`; `POST /history {"delete": […]}` / `{"clear": true}` |
| `GET /view?filename=&subfolder=&type=` | download an output/input/temp file | `type` = `output` / `input` / `temp` |
| `POST /upload/image` | multipart: `image` (file), `type`=`input`, `subfolder`, `overwrite` | returns `{name, subfolder, type}`; the LoadImage value is `subfolder/name` |
| `POST /upload/mask` | as above plus `original_ref` JSON | merges the mask into the alpha of an uploaded image |
| `POST /free` | `{"unload_models": true, "free_memory": true}` | releases models between big jobs |
| `GET /api/jobs`, `/api/jobs/{id}` | newer job list/status | `POST /api/jobs/{id}/cancel` |
| `GET /api/workflow_templates` | bundled template index | per custom-node package |
| `GET /userdata?dir=workflows` | the editor's saved workflows | `GET /userdata/workflows%2F<file>` downloads one |

## `POST /prompt`

```json
{"prompt": {"3": {"class_type": "KSampler", "inputs": {"seed": 5, "model": ["4", 0], "...": "..."}}},
 "client_id": "comfyui-skill-<hex>",
 "prompt_id": "<optional uuid>",
 "extra_data": {"extra_pnginfo": {"workflow": {"...": "UI-format graph, embedded in PNGs"}}},
 "front": false}
```

- An input value is a literal or a link `[source_node_id, output_index]`. A literal **list**
  must be wrapped as `{"__value__": [...]}`, or it is read as a broken link.
- `_meta.title` is ignored by the server; the editor shows it.
- Success: `200 {"prompt_id", "number", "node_errors": {}}`.
- Partial: `200` with non-empty `node_errors` — the outputs that validated **are queued**.
- Failure: `400 {"error": {"type", "message", "details"}, "node_errors": {node_id:
  {"errors": [{"type", "message", "details", "extra_info": {"input_name", …}}],
  "dependent_outputs": […], "class_type"}}}`.

Error `type`s: `prompt_no_outputs`, `prompt_outputs_failed_validation`, `missing_node_type`,
`required_input_missing`, `bad_linked_input`, `return_type_mismatch`, `invalid_input_type`,
`value_not_in_list`, `value_smaller_than_min`, `value_bigger_than_max`,
`custom_validation_failed`, `invalid_dynamic_input`, `dependency_cycle`,
`exception_during_validation`.

## `/history/{prompt_id}`

```json
{"<prompt_id>": {
  "prompt": [number, prompt_id, {graph}, {extra_data}, [output_node_ids]],
  "outputs": {"9": {"images": [{"filename": "x_00001_.png", "subfolder": "", "type": "output"}]},
              "24": {"text": ["..."]}},
  "status": {"status_str": "success" | "error", "completed": true,
             "messages": [["execution_start", {…}], ["execution_cached", {"nodes": […]}],
                          ["execution_error", {"node_id", "node_type", "exception_message", "traceback"}]]},
  "meta": {"9": {"node_id", "display_node", "parent_node", "real_node_id"}}}}
```

The entry appears only once the prompt has finished (or failed). Output lists are keyed by
kind (`images`, `gifs`, `videos`, `audio`, `text`, …); `type: temp` entries are previews.

## WebSocket `/ws?clientId=<client_id>`

Text frames are JSON `{"type", "data"}`; binary frames are live preview images (skip them).
Types: `status` (queue_remaining), `execution_start`, `execution_cached` (nodes skipped
from cache), `executing` (`node`; `node: null` = prompt finished), `progress`
(`value`/`max` for the current sampler), `progress_state`, `executed` (one node's UI output),
`execution_success`, `execution_error`, `execution_interrupted`. Messages for a prompt go to
the `client_id` that queued it. `comfy.py` polls `/history` instead (no WebSocket in the
standard library); open the socket only when per-step progress matters.
