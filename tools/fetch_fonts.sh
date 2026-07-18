#!/usr/bin/env bash
# Regenerate Inter TTF fonts into assets/fonts (not tracked in git; too large).
# Needs: pnpm + fonttools (pipx install fonttools && pipx inject fonttools brotli)
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/assets/fonts"
TMP="$(mktemp -d)"
cd "$TMP"
pnpm add inter-ui >/dev/null 2>&1 || true
SRC="$TMP/node_modules/inter-ui/web"
mkdir -p "$OUT"
for w in Regular Medium SemiBold Bold ExtraBold; do
  fonttools ttx -o "$OUT/Inter-$w.ttf" "$SRC/Inter-$w.woff2"
done
rm -rf "$TMP"
echo "Fonts written to $OUT"
