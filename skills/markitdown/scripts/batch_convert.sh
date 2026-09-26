#!/usr/bin/env bash
# Convert every supported document under a directory tree to Markdown.
#
# Usage: batch_convert.sh SRC_DIR [OUT_DIR]
#
# Mirrors SRC_DIR's structure into OUT_DIR (default: next to each source file),
# writing <name>.<ext>.md so report.pdf and report.docx never collide.
# Existing outputs newer than their source are skipped, so reruns are cheap.
#
# markitdown exits 0 with empty output for image-only content (scans, photos),
# so empty results are reported separately instead of counted as successes.
#
# Environment:
#   MARKITDOWN   markitdown command to run (default: markitdown)
#   EXTENSIONS   space-separated extensions to pick up (default below)
#
# Exit status: 0 if every file converted with content, 1 if any failed or came
# back empty, 2 on usage errors. Legacy .doc/.ppt files are listed, not counted.

set -uo pipefail

if [[ $# -lt 1 || $# -gt 2 || ! -d "$1" ]]; then
  echo "usage: $(basename "$0") SRC_DIR [OUT_DIR]" >&2
  exit 2
fi

src="${1%/}"
out="${2:-}"
out="${out%/}"
md_cmd="${MARKITDOWN:-markitdown}"
exts="${EXTENSIONS:-pdf docx pptx xlsx xls html htm csv json xml epub ipynb msg zip}"

if ! command -v "$md_cmd" >/dev/null 2>&1; then
  echo "error: '$md_cmd' not found — install markitdown or set MARKITDOWN" >&2
  exit 2
fi

find_args=()
for e in $exts; do
  [[ ${#find_args[@]} -gt 0 ]] && find_args+=(-o)
  find_args+=(-iname "*.${e}")
done

ok=0 skipped=0
failed=() empty=()

while IFS= read -r -d '' f; do
  rel="${f#"$src"/}"
  if [[ -n "$out" ]]; then
    dest="$out/$rel.md"
  else
    dest="$f.md"
  fi

  if [[ -s "$dest" && "$dest" -nt "$f" ]]; then
    skipped=$((skipped + 1))
    continue
  fi

  mkdir -p "$(dirname "$dest")"
  if ! err=$("$md_cmd" "$f" -o "$dest" 2>&1 >/dev/null); then
    failed+=("$rel: $(printf '%s\n' "$err" | tail -n 1)")
    rm -f "$dest"
    continue
  fi

  if [[ -z "$(tr -d '[:space:]' < "$dest")" ]]; then
    empty+=("$rel")
  else
    ok=$((ok + 1))
  fi
done < <(find "$src" -type f \( "${find_args[@]}" \) -print0 | sort -z)

# Legacy binary Office formats have no markitdown converter; name them so they
# aren't silently missing from the output.
legacy=()
while IFS= read -r -d '' f; do
  legacy+=("${f#"$src"/}")
done < <(find "$src" -type f \( -iname '*.doc' -o -iname '*.ppt' \) -print0 | sort -z)

echo "converted: $ok, skipped (up to date): $skipped, empty: ${#empty[@]}, failed: ${#failed[@]}, legacy (unsupported): ${#legacy[@]}"
for e in ${empty[@]+"${empty[@]}"}; do
  echo "EMPTY   $e  (likely scanned/image-only — needs OCR)"
done
for e in ${failed[@]+"${failed[@]}"}; do
  echo "FAILED  $e"
done

for e in ${legacy[@]+"${legacy[@]}"}; do
  echo "LEGACY  $e  (convert to .docx/.pptx first: textutil or soffice --convert-to)"
done

[[ ${#failed[@]} -eq 0 && ${#empty[@]} -eq 0 ]]
