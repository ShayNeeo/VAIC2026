#!/usr/bin/env bash
# Regenerate TTF fonts into assets/fonts (not tracked in git; too large).
# Heading: Sora | Body/data: IBM Plex Sans
# Needs: pnpm + fonttools (pipx install fonttools && pipx inject fonttools brotli)
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/assets/fonts"
TMP="$(mktemp -d)"
cd "$TMP"
pnpm add @fontsource/sora @fontsource/ibm-plex-sans >/dev/null 2>&1 || true
SORA="$TMP/node_modules/@fontsource/sora/files"
PLEX="$TMP/node_modules/@fontsource/ibm-plex-sans/files"
mkdir -p "$OUT"
for pair in 400:Regular 500:Medium 600:SemiBold 700:Bold 800:ExtraBold; do
  num=${pair%:*}; name=${pair#*:}
  fonttools ttx -o "$OUT/Sora-$name.ttf" "$SORA/sora-latin-$num-normal.woff2"
done
for pair in 400:Regular 500:Medium 600:SemiBold 700:Bold; do
  num=${pair%:*}; name=${pair#*:}
  fonttools ttx -o "$OUT/IBMPlexSans-$name.ttf" "$PLEX/ibm-plex-sans-latin-$num-normal.woff2"
done
rm -rf "$TMP"
echo "Fonts written to $OUT"
