#!/usr/bin/env node
// affinity-cli.mjs — zero-dependency CLI for Affinity's local automation endpoint.
//
// Affinity (by Canva) exposes its scripting SDK on http://localhost:6767/sse when
// the AI connector is enabled (Settings → AI connector). The endpoint speaks the
// MCP protocol (JSON-RPC over SSE), but this CLI talks to it directly — no MCP
// client configuration, no npm dependencies. Node >= 18.
//
// Usage:
//   affinity-cli.mjs ping
//   affinity-cli.mjs tools [--json]
//   affinity-cli.mjs call <tool> ['{"json":"args"}']
//   affinity-cli.mjs run <file.js> [--title "<title>"]
//   affinity-cli.mjs add --title "<t>" --description "<d>" --file <file.js>
//   affinity-cli.mjs list
//   affinity-cli.mjs save --title "<t>" [--out <path>]
//   affinity-cli.mjs search <query...>
//   affinity-cli.mjs docs [<topic-filename>]
//   affinity-cli.mjs docs-dump <output-dir>
//   affinity-cli.mjs render [--selection] [--uuid <u>] [--spread <n>] [--out <path>]
//
// Env: AFFINITY_MCP_URL (default http://localhost:6767), AFFINITY_TIMEOUT_MS (default 120000)

import { readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";

const BASE = (process.env.AFFINITY_MCP_URL || "http://localhost:6767").replace(/\/+$/, "");
const TIMEOUT_MS = Number(process.env.AFFINITY_TIMEOUT_MS || 120000);

// Tool names tried, in order, for `run` — the direct-execute tool name is not
// stable across Affinity releases, so we match against the live tools/list.
const EXEC_TOOL_CANDIDATES = [
  "run_script",
  "execute_script",
  "run_javascript",
  "execute_javascript",
  "evaluate_script",
  "run_library_script",
];
const CODE_ARG_CANDIDATES = ["code", "script", "source", "javascript"];

function withTimeout(promise, ms, label) {
  let timer;
  const timeout = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error(`Timed out after ${ms}ms: ${label}`)), ms);
  });
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timer));
}

class McpClient {
  constructor() {
    this.pending = new Map();
    this.nextId = 1;
    this.controller = new AbortController();
    this.postUrl = null;
  }

  async connect() {
    let res;
    try {
      res = await withTimeout(
        fetch(`${BASE}/sse`, {
          headers: { Accept: "text/event-stream" },
          signal: this.controller.signal,
        }),
        5000,
        "connecting to Affinity endpoint"
      );
    } catch (err) {
      throw new Error(
        `Cannot reach ${BASE}/sse — is Affinity running with the AI connector enabled? (${err.message})`
      );
    }
    if (!res.ok || !res.body) {
      throw new Error(`SSE connect failed: HTTP ${res.status}`);
    }

    const endpointReady = new Promise((resolve, reject) => {
      this.resolveEndpoint = resolve;
      this.rejectEndpoint = reject;
    });
    this.readLoop(res.body).catch(() => {});
    this.postUrl = await withTimeout(endpointReady, 10000, "waiting for endpoint event");

    const versions = ["2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05"];
    let lastError;
    for (const protocolVersion of versions) {
      try {
        this.serverInfo = await this.request("initialize", {
          protocolVersion,
          capabilities: {},
          clientInfo: { name: "affinity-cli", version: "1.0.0" },
        });
        lastError = null;
        break;
      } catch (err) {
        lastError = err;
        if (!/protocol version/i.test(err.message)) throw err;
      }
    }
    if (lastError) throw lastError;
    await this.notify("notifications/initialized");
  }

  async readLoop(body) {
    const reader = body.getReader();
    const decoder = new TextDecoder();
    let buf = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true }).replace(/\r/g, "");
      let idx;
      while ((idx = buf.indexOf("\n\n")) !== -1) {
        const raw = buf.slice(0, idx);
        buf = buf.slice(idx + 2);
        this.handleEvent(raw);
      }
    }
  }

  handleEvent(raw) {
    let event = "message";
    const data = [];
    for (const line of raw.split("\n")) {
      if (line.startsWith("event:")) event = line.slice(6).trim();
      else if (line.startsWith("data:")) data.push(line.slice(5).trimStart());
    }
    const payload = data.join("\n");
    if (event === "endpoint") {
      let url;
      try {
        url = new URL(payload, BASE);
      } catch {
        this.rejectEndpoint(new Error(`Malformed endpoint event: ${payload}`));
        return;
      }
      // A relative payload resolves against BASE, but an absolute one wins
      // outright — so a hostile or hijacked listener could point every later
      // POST at a host of its choosing, including tools/call bodies carrying
      // the contents of local .js files.
      const expected = new URL(BASE).origin;
      if (url.origin !== expected) {
        this.rejectEndpoint(
          new Error(`Refusing cross-origin endpoint: ${url.origin} (expected ${expected})`)
        );
        return;
      }
      this.resolveEndpoint(url.toString());
      return;
    }
    if (event !== "message" || !payload) return;
    let msg;
    try {
      msg = JSON.parse(payload);
    } catch {
      return;
    }
    if (msg.id != null && this.pending.has(msg.id)) {
      const { resolve, reject } = this.pending.get(msg.id);
      this.pending.delete(msg.id);
      if (msg.error) {
        const data = msg.error.data ? ` ${JSON.stringify(msg.error.data)}` : "";
        reject(new Error(`RPC error ${msg.error.code}: ${msg.error.message}${data}`));
      } else {
        resolve(msg.result);
      }
    }
  }

  async request(method, params) {
    const id = this.nextId++;
    const reply = new Promise((resolve, reject) => this.pending.set(id, { resolve, reject }));
    const res = await fetch(this.postUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jsonrpc: "2.0", id, method, params }),
    });
    if (!res.ok && res.status !== 202) {
      this.pending.delete(id);
      throw new Error(`POST ${method} failed: HTTP ${res.status}`);
    }
    // finally, not just the success path: a timed-out request would otherwise
    // keep its resolver for the life of the process, and docs-dump issues one
    // request per topic in a loop.
    return withTimeout(reply, TIMEOUT_MS, method).finally(() => this.pending.delete(id));
  }

  async notify(method, params = {}) {
    await fetch(this.postUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jsonrpc: "2.0", method, params }),
    });
  }

  callTool(name, args = {}) {
    return this.request("tools/call", { name, arguments: args });
  }

  close() {
    this.controller.abort();
  }
}

function toolText(result) {
  return (result.content || [])
    .filter((item) => item && item.type === "text" && typeof item.text === "string")
    .map((item) => item.text)
    .join("\n");
}

function printToolResult(result) {
  const text = toolText(result);
  if (result.isError) process.exitCode = 1;
  console.log(text || JSON.stringify(result, null, 2));
}

function parseFlags(args) {
  const flags = {};
  const positional = [];
  for (let i = 0; i < args.length; i += 1) {
    if (args[i].startsWith("--")) {
      const key = args[i].slice(2);
      const value = args[i + 1];
      if (value === undefined || value.startsWith("--")) {
        throw new Error(`Missing value for --${key}`);
      }
      flags[key] = value;
      i += 1;
    } else {
      positional.push(args[i]);
    }
  }
  return { flags, positional };
}

async function cmdRun(client, { flags, positional }) {
  const file = positional[0];
  if (!file) throw new Error("Usage: run <file.js> [--title <title>]");
  const code = await readFile(path.resolve(file), "utf8");
  const title = flags.title || path.basename(file, ".js");

  const { tools } = await client.request("tools/list", {});
  const names = tools.map((t) => t.name);
  const execName = EXEC_TOOL_CANDIDATES.find((n) => names.includes(n));

  if (execName) {
    const schema = tools.find((t) => t.name === execName).inputSchema || {};
    const props = Object.keys(schema.properties || {});
    const codeArg = CODE_ARG_CANDIDATES.find((c) => props.includes(c)) || "code";
    // The server refuses execute_script until the preamble doc has been read
    // in the same session, and each CLI invocation is a fresh session.
    await client.callTool("read_sdk_documentation_topic", { filename: "preamble" }).catch(() => {});
    printToolResult(await client.callTool(execName, { [codeArg]: code }));
    return;
  }

  // No direct-execute tool on this Affinity build: install into the script
  // library instead; running it needs a click in Window → General → Scripts.
  const result = await client.callTool("save_script_to_library", {
    title,
    description: flags.description || `Added by affinity-cli on ${new Date().toISOString().slice(0, 10)}`,
    code,
  });
  console.log(toolText(result) || JSON.stringify(result));
  console.log(
    `NOTE: no direct-execute tool on this endpoint. Ask the user to run "${title}" from Window → General → Scripts in Affinity.`
  );
}

async function main() {
  const [command, ...rest] = process.argv.slice(2);
  if (!command) {
    console.error("Commands: ping | tools | call | run | add | list | save | search | docs | docs-dump | render");
    process.exit(1);
  }

  const client = new McpClient();
  try {
    await client.connect();

    switch (command) {
      case "ping": {
        const info = client.serverInfo?.serverInfo || {};
        console.log(`OK ${BASE} — ${info.name || "unknown server"} ${info.version || ""}`.trim());
        break;
      }
      case "tools": {
        const { tools } = await client.request("tools/list", {});
        if (rest.includes("--json")) {
          console.log(JSON.stringify(tools, null, 2));
        } else {
          for (const t of tools) {
            const desc = (t.description || "").split("\n")[0];
            console.log(`${t.name} — ${desc}`);
          }
        }
        break;
      }
      case "call": {
        const [name, argsJson] = rest;
        if (!name) throw new Error('Usage: call <tool> [\'{"json":"args"}\']');
        printToolResult(await client.callTool(name, argsJson ? JSON.parse(argsJson) : {}));
        break;
      }
      case "run":
        await cmdRun(client, parseFlags(rest));
        break;
      case "add": {
        const { flags } = parseFlags(rest);
        if (!flags.title || !flags.description || !flags.file) {
          throw new Error("Usage: add --title <t> --description <d> --file <file.js>");
        }
        const code = await readFile(path.resolve(flags.file), "utf8");
        printToolResult(
          await client.callTool("save_script_to_library", {
            title: flags.title,
            description: flags.description,
            code,
          })
        );
        break;
      }
      case "list":
        printToolResult(await client.callTool("list_library_scripts", {}));
        break;
      case "save": {
        const { flags } = parseFlags(rest);
        if (!flags.title) throw new Error("Usage: save --title <t> [--out <path>]");
        const result = await client.callTool("read_library_script", { title: flags.title });
        const code = toolText(result);
        if (!code) throw new Error(`No script content returned for "${flags.title}"`);
        const out = path.resolve(
          flags.out || flags.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") + ".js"
        );
        await mkdir(path.dirname(out), { recursive: true });
        await writeFile(out, code, "utf8");
        console.log(`Saved "${flags.title}" to ${out}`);
        break;
      }
      case "render": {
        const selection = rest.includes("--selection");
        const { flags } = parseFlags(rest.filter((a) => a !== "--selection"));
        const out = flags.out || "affinity-render.jpg";
        let uuid = flags.uuid;
        await client.callTool("read_sdk_documentation_topic", { filename: "preamble" }).catch(() => {});
        if (!uuid) {
          const probe = await client.callTool("execute_script", {
            script:
              "const { app } = require('/application'); const d = app.documents.current; console.log(d ? d.sessionUuid : 'NONE');",
          });
          uuid = toolText(probe).trim();
          if (!uuid || uuid === "NONE") throw new Error("No document open in Affinity");
        }
        const result = selection
          ? await client.callTool("render_selection", { document_session_uuid: uuid })
          : await client.callTool("render_spread", {
              document_session_uuid: uuid,
              spread_index: Number(flags.spread || 0),
            });
        const image = (result.content || []).find((c) => c && c.type === "image" && c.data);
        const b64 = image ? image.data : toolText(result).replace(/^data:image\/\w+;base64,/, "").trim();
        if (!b64 || /\s/.test(b64.slice(0, 100)) || result.isError) {
          throw new Error(`Render failed: ${toolText(result) || JSON.stringify(result).slice(0, 300)}`);
        }
        await mkdir(path.dirname(path.resolve(out)), { recursive: true });
        await writeFile(path.resolve(out), Buffer.from(b64, "base64"));
        console.log(`Rendered to ${path.resolve(out)} (doc ${uuid})`);
        break;
      }
      case "search": {
        const query = rest.join(" ").trim();
        if (!query) throw new Error('Usage: search <query...>');
        printToolResult(await client.callTool("search_sdk_hints", { prompt: query }));
        break;
      }
      case "docs": {
        const topic = rest[0];
        if (topic) {
          if (topic !== "preamble") {
            await client.callTool("read_sdk_documentation_topic", { filename: "preamble" }).catch(() => {});
          }
          printToolResult(await client.callTool("read_sdk_documentation_topic", { filename: topic }));
        } else {
          printToolResult(await client.callTool("list_sdk_documentation", {}));
        }
        break;
      }
      case "docs-dump": {
        const outDir = rest[0];
        if (!outDir) throw new Error("Usage: docs-dump <output-dir>");
        // Several topics refuse to load until the preamble has been read in-session.
        await client.callTool("read_sdk_documentation_topic", { filename: "preamble" }).catch(() => {});
        const listResult = await client.callTool("list_sdk_documentation", {});
        const topics = [
          ...new Set(
            toolText(listResult)
              .split(",")
              .map((s) => s.trim())
              .filter(Boolean)
          ),
        ];
        const root = path.resolve(outDir);
        let saved = 0;
        for (const topic of topics) {
          const dest = path.resolve(root, topic);
          if (!dest.startsWith(root + path.sep)) {
            console.error(`Skipped unsafe path: ${topic}`);
            continue;
          }
          try {
            // Long dumps can outlive the SSE session; rerunning resumes where it left off.
            if (!rest.includes("--force") && (await readFile(dest, "utf8").catch(() => null)) !== null) {
              saved += 1;
              continue;
            }
            const doc = await client.callTool("read_sdk_documentation_topic", { filename: topic });
            await mkdir(path.dirname(dest), { recursive: true });
            await writeFile(dest, toolText(doc), "utf8");
            saved += 1;
          } catch (err) {
            console.error(`Failed: ${topic} — ${err.message}`);
            process.exitCode = 1;
          }
        }
        console.log(`Saved ${saved}/${topics.length} SDK doc topics to ${root}`);
        break;
      }
      default:
        throw new Error(`Unknown command "${command}"`);
    }
  } finally {
    client.close();
  }
}

main().catch((err) => {
  console.error(err.message);
  process.exit(1);
});
