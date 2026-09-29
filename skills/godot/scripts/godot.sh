#!/usr/bin/env bash
# Locate the Godot 4.x binary and run it. Every other script in this skill goes
# through here, so the binary lookup and the version gate live in one place.
#
#   bash godot.sh --check           binary, version, .NET or not, export templates
#   bash godot.sh --bin             print the binary path only
#   bash godot.sh [godot args...]   run Godot with the given arguments
#
# Override the lookup with GODOT_BIN=/path/to/Godot. Override the export template
# root with GODOT_TEMPLATES_DIR (default: ~/Library/Application Support/Godot/export_templates).
set -euo pipefail

find_godot() {
  local candidate app
  for candidate in \
    "${GODOT_BIN:-}" \
    "$(command -v godot 2>/dev/null || true)" \
    "$(command -v godot4 2>/dev/null || true)"; do
    if [[ -n "$candidate" && -x "$candidate" ]]; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  # Homebrew casks and manual installs land here; Godot_mono.app is the .NET build.
  for app in /Applications/Godot.app "$HOME/Applications/Godot.app" \
    /Applications/Godot_mono.app "$HOME/Applications/Godot_mono.app"; do
    if [[ -x "$app/Contents/MacOS/Godot" ]]; then
      printf '%s' "$app/Contents/MacOS/Godot"
      return 0
    fi
  done
  return 1
}

if ! BIN=$(find_godot); then
  echo "Godot not found — install it (brew install --cask godot) or set GODOT_BIN" >&2
  exit 2
fi

# "4.7.2.stable.official.ed1daf0bf" (standard) or "4.7.2.stable.mono.official.…" (.NET)
full_version=$("$BIN" --version 2>/dev/null | tail -n1 | tr -d '\r')
if [[ "${full_version%%.*}" != "4" ]]; then
  echo "Godot 4.x required, found '${full_version:-unknown}' at $BIN" >&2
  exit 2
fi

case "${1:-}" in
  --bin)
    echo "$BIN"
    ;;
  --check)
    echo "$BIN"
    echo "Godot $full_version"
    if [[ "$full_version" == *.mono.* ]]; then
      echo "build: .NET — C# projects are out of scope for this skill; GDScript still works"
    else
      echo "build: standard (GDScript only)"
    fi
    # Templates live in a folder named after the version up to the status tag,
    # e.g. 4.7.2.stable (standard) or 4.7.2.stable.mono (.NET).
    tag=$(sed -E 's/^([0-9.]+\.[a-z0-9]+)(\.mono)?\..*$/\1\2/' <<<"$full_version")
    tpl_root=${GODOT_TEMPLATES_DIR:-"$HOME/Library/Application Support/Godot/export_templates"}
    tpl="$tpl_root/$tag"
    if [[ -f "$tpl/version.txt" ]]; then
      platforms=()
      [[ -f "$tpl/macos.zip" ]] && platforms+=(macOS)
      [[ -f "$tpl/web_nothreads_release.zip" ]] && platforms+=(Web)
      ls "$tpl"/windows_release_* >/dev/null 2>&1 && platforms+=(Windows)
      ls "$tpl"/linux_release.* >/dev/null 2>&1 && platforms+=(Linux)
      [[ -f "$tpl/android_release.apk" ]] && platforms+=(Android)
      [[ -f "$tpl/ios.zip" ]] && platforms+=(iOS)
      echo "export templates: $tag installed (${platforms[*]:-none}) at $tpl"
    else
      # 4.7.2.stable -> Godot_v4.7.2-stable_export_templates.tpz (.mono -> _mono_)
      release=$(sed -E 's/\.([a-z][a-z0-9]*)$/-\1/' <<<"${tag%.mono}")
      mono=""
      [[ "$tag" == *.mono ]] && mono="_mono"
      echo "export templates: MISSING for $tag — exports will fail. Install from the editor"
      echo "  (Editor > Manage Export Templates > Download and Install), or download"
      echo "  Godot_v${release}${mono}_export_templates.tpz (about 1 GB) from"
      echo "  https://github.com/godotengine/godot/releases and unzip its templates/"
      echo "  folder contents into: $tpl"
    fi
    ;;
  *)
    exec "$BIN" "$@"
    ;;
esac
