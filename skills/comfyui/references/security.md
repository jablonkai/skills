# Security posture

ComfyUI's API has **no authentication**. Whoever reaches the port can queue arbitrary node
graphs, read every output and input image, upload files, and — with ComfyUI-Manager
installed — install custom nodes, which is arbitrary code execution. The skill therefore:

- **Binds loopback only.** `server start` always passes `--listen 127.0.0.1` and refuses
  `--listen`/`--enable-cors-header` in the extra arguments. `comfy.py` refuses a
  non-loopback `--url`/`$COMFYUI_URL` unless `--allow-remote` is given, which is only for a
  host the user named.
- **Leaves cross-origin protection on.** Without `--enable-cors-header`, ComfyUI's
  origin-only middleware rejects browser requests whose `Origin` host differs from `Host`,
  so a web page cannot drive the local server. The client sends no `Origin` header.
- **Never installs custom nodes on its own.** Not through Manager, not by cloning into
  `custom_nodes/`. A downloaded workflow failing with `missing_node_type` is reported with the
  node class and the package that provides it; installing is the user's decision.
- **Treats downloaded workflows as code-adjacent.** A graph can only call installed nodes,
  but some installed nodes run shell commands or Python (e.g. "exec" style utility nodes).
  Read `inspect` output for such nodes before running a workflow from the internet.
- **Scopes its stop path.** `stop` only cancels prompts whose `client_id` starts with
  `comfyui-skill-`; the editor's jobs are left alone unless the user asks for `--all`.
  `server stop` only kills the process `server start` launched (pid file).
- **Keeps inputs local.** Uploaded images go to ComfyUI's `input/` folder, outputs to
  `output/`; neither leaves the machine.
