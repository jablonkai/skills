# Vendored: @scenery/cavalry-types 1.0.0

Complete TypeScript definitions for Cavalry's scripting API, vendored from
[`@scenery/cavalry-types`](https://www.npmjs.com/package/@scenery/cavalry-types) 1.0.0
(github.com/scenery-io/cavalry-types, MIT — see [LICENSE](LICENSE); last published 2026-05-06).

This is the authoritative, machine-readable API surface — grep it when a function isn't in
[../api-reference.md](../api-reference.md):

| File | Contents |
|---|---|
| `namespaces/api.d.ts` | the full `api` module (~2900 lines, JSDoc'd with examples) |
| `namespaces/cavalry.d.ts` | `cavalry` utilities: Path, Line, math/noise, color, fonts |
| `namespaces/ui.d.ts` | script windows: layouts, all widgets, callbacks |
| `namespaces/ctx.d.ts` | `ctx` — JavaScript *expression* context (Duplicator/Connect Shape indices: `ctx.index`, `ctx.count`, `ctx.positionX/Y`) |
| `namespaces/render.d.ts` | render-script hooks (`render.composition`, `render.path`, …) |
| `namespaces/def.d.ts` | attribute-definition metadata types |
| `namespaces/console.d.ts` | console logging |
| root `*.d.ts` | aggregators for script/plugin type-checking setups |

Usage pattern: `grep -n "functionName" namespaces/api.d.ts`, then read the surrounding JSDoc
block — most entries include a runnable example.

To refresh: `npm pack @scenery/cavalry-types` and copy `package/types/*` over this directory.
