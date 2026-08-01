#!/usr/bin/env bash
# Install the Krita Bridge plugin into the user's Krita resource folder and
# enable it in kritarc, so it starts with every Krita launch.
#
# Usage: krita-install-bridge.sh [--force]
#
# Krita rewrites kritarc when it quits, so a running Krita would clobber the
# enable flag written here — the script refuses to touch the config while Krita
# is running and tells you to quit it first.
#
# Paths (override with KRITA_RESOURCES / KRITA_RC):
#   macOS  ~/Library/Application Support/krita/pykrita  +  ~/Library/Preferences/kritarc
#   Linux  ~/.local/share/krita/pykrita                 +  ~/.config/kritarc
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)

case "$(uname -s)" in
    Darwin)
        RESOURCES="${KRITA_RESOURCES:-$HOME/Library/Application Support/krita}"
        RC="${KRITA_RC:-$HOME/Library/Preferences/kritarc}" ;;
    *)
        RESOURCES="${KRITA_RESOURCES:-$HOME/.local/share/krita}"
        RC="${KRITA_RC:-$HOME/.config/kritarc}" ;;
esac
PYKRITA="$RESOURCES/pykrita"

if pgrep -x krita >/dev/null 2>&1 && [ "${1:-}" != "--force" ]; then
    echo "ERROR: Krita is running. Quit it first — it rewrites kritarc on exit and" >&2
    echo "       would discard the enable flag written here. (--force to override.)" >&2
    exit 1
fi

mkdir -p "$PYKRITA"
cp -R "$HERE/krita_bridge" "$PYKRITA/"
cp "$HERE/krita_bridge.desktop" "$PYKRITA/"
echo "installed: $PYKRITA/krita_bridge{,.desktop}"

RC="$RC" python3 - <<'PY'
import os, re
rc = os.environ["RC"]
text = open(rc).read() if os.path.exists(rc) else ""
key, value = "enable_krita_bridge", "true"

if re.search(r"^\[python\]\s*$", text, re.M):
    # Replace the key inside the existing [python] group, or append it there.
    def patch(match):
        body = match.group(2)
        if re.search(r"^%s=" % key, body, re.M):
            return match.group(1) + re.sub(r"^%s=.*$" % key, "%s=%s" % (key, value),
                                           body, flags=re.M)
        return match.group(1) + body.rstrip("\n") + "\n%s=%s\n" % (key, value)
    text = re.sub(r"(^\[python\]\s*\n)((?:(?!^\[).*\n?)*)", patch, text, count=1, flags=re.M)
else:
    text = text.rstrip("\n") + "\n\n[python]\n%s=%s\n" % (key, value)

os.makedirs(os.path.dirname(rc), exist_ok=True)
with open(rc, "w") as f:
    f.write(text)
print("enabled in %s: [python] %s=%s" % (rc, key, value))
PY

echo
echo "Start Krita; the bridge comes up automatically. Verify with:"
echo "  bash $HERE/krita-send.sh --ping"
