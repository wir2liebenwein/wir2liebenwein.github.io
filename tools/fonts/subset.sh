#!/usr/bin/env bash
# Rebuilds the WOFF2 web fonts from the original TTFs in tools/fonts/ttf/.
# Latin subset (Google Fonts "latin" range), hinting and all OpenType features kept,
# so the glyphs render exactly like the TTFs did. Needs: pip install fonttools brotli
set -euo pipefail
cd "$(dirname "$0")"
LATIN="U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"
for f in oswald-variablefont_wght sourcesanspro-regular sourcesanspro-bold librebaskerville-regular; do
  pyftsubset "ttf/$f.ttf" --unicodes="$LATIN" --layout-features='*' --flavor=woff2 \
    --notdef-outline --name-IDs='*' --name-languages='*' --output-file="../../src/assets/fonts/$f.woff2"
done
ls -l ../../src/assets/fonts/*.woff2
