#!/usr/bin/env bash
# Check that Final Cut Pro's Titles and Generators browser lists installed templates.
#
#   bash motn-fcp-browser.sh "Template Name" ["Other Name" ...]
#   bash motn-fcp-browser.sh --all            print every name the browser shows
#
# Reads FCP's window through Accessibility (System Events): it shows the Titles and
# Generators sidebar if it is hidden (one checkbox click; nothing else is clicked or
# typed), then collects the browser item names. FCP must be running with a library
# open. Exit 0 when every name is listed, 1 when one is missing, 2 when FCP or
# Accessibility is unavailable. A template installed while FCP runs may only appear
# after FCP is relaunched — that is FCP's cache, not a failed install.
set -euo pipefail

if ! pgrep -xq "Final Cut Pro"; then
  echo '{"ok": false, "error": "Final Cut Pro is not running (open -b com.apple.FinalCut)"}'
  exit 2
fi

names=$(osascript -l JavaScript - <<'JXA' 2>&1
function run() {
  const se = Application('System Events');
  const p = se.processes.byName('Final Cut Pro');
  const w = p.windows.byName('Final Cut Pro');
  // descend only through layout containers, so the thousands of timeline items stay unvisited
  function find(e, test, d) {
    if (d > 9) return null;
    let kids = []; try { kids = e.uiElements(); } catch (x) {}
    for (const k of kids) { try { if (test(k)) return k; } catch (x) {} }
    for (const k of kids) {
      let r = ''; try { r = k.role(); } catch (x) {}
      if (r === 'AXGroup' || r === 'AXSplitGroup') { const f = find(k, test, d + 1); if (f) return f; }
    }
    return null;
  }
  const cb = find(w, e => e.role() === 'AXCheckBox' && /Titles and Generators/.test(e.description()), 0);
  if (!cb) return 'ERR no Titles and Generators sidebar button (is a library open?)';
  if (String(cb.value()) !== '1') { cb.click(); delay(2); }
  const box = cb.attributes.byName('AXParent').value();
  // breadth-first with bulk queries (one Apple Event per level, not per item):
  // the element whose children are all AXImage is the browser grid
  let q = [box], out = [];
  for (let d = 0; d < 6 && q.length && !out.length; d++) {
    const next = [];
    for (const e of q) {
      let roles = []; try { roles = e.uiElements.role(); } catch (x) {}
      if (roles.length && roles.every(r => r === 'AXImage')) { out = out.concat(e.uiElements.name()); continue; }
      roles.forEach((r, i) => { if (!['AXImage', 'AXOutline', 'AXStaticText', 'AXButton', 'AXCheckBox', 'AXTextField'].includes(r)) next.push(e.uiElements[i]); });
    }
    q = next;
  }
  return out.join('\n');
}
JXA
) || true

if [[ "$names" == ERR* || "$names" == *"execution error"* || "$names" == *"(-1719)"* || "$names" == *"(-25211)"* ]]; then
  printf '{"ok": false, "error": %s}\n' "$(printf '%s' "$names" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read().strip()[:300]))')"
  exit 2
fi

if [[ "${1:-}" == "--all" ]]; then
  printf '%s\n' "$names"
  exit 0
fi

NAMES="$names" python3 - "$@" <<'PY'
import json, os, sys
shown = [n for n in os.environ["NAMES"].splitlines() if n]
# FCP shows a template in a nested category as "Sub - Name"; match either form
found = {w: any(s == w or s.endswith(" - " + w) for s in shown) for w in sys.argv[1:]}
print(json.dumps({"ok": all(found.values()), "browser_items": len(shown), "found": found}, ensure_ascii=False))
sys.exit(0 if all(found.values()) else 1)
PY
