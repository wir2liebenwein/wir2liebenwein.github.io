#!/bin/bash
# ---------------------------------------------------------------------------
# Raw backup of www.wir2liebenwein.de (Webflow) into ./_archive
#
# Run in Terminal:   bash download-site.sh
#
# - crawls every page of the site (incl. paginated /neues pages)
# - downloads all images, CSS, JS, fonts and PDFs from the Webflow CDN
# - writes manifests (URL -> local file) so nothing is lost when Webflow is cancelled
# Needs only curl/grep/sed (preinstalled on macOS). Takes a few minutes.
# ---------------------------------------------------------------------------
set -u
cd "$(dirname "$0")" || exit 1
ROOT="$(pwd)"
OUT="$ROOT/_archive"
BASE="${BASE:-https://www.wir2liebenwein.de}"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
ASSET_HOSTS='(website-files\.com|uploads-ssl\.webflow\.com|assets\.website-files|cloudfront\.net|ajax\.googleapis\.com|fonts\.googleapis\.com|fonts\.gstatic\.com|use\.typekit\.net)'

rm -rf "$OUT/assets" "$OUT/pages"          # start clean on re-runs
mkdir -p "$OUT/pages" "$OUT/assets"
WORK="$OUT/_crawl"; mkdir -p "$WORK"
LOG="$OUT/crawl-log.txt"; : > "$LOG"
echo "__none__" > "$WORK/visited.txt"
echo "__none__" > "$WORK/assets-done.txt"
: > "$WORK/assets.txt"
printf 'url\tlocal_file\n' > "$OUT/pages-manifest.tsv"
printf 'url\tlocal_file\thttp_status\n' > "$OUT/assets-manifest.tsv"
printf '%s\n' / /neues /bottleshop /unser-wein /verkostung /ueber-uns /bestell-kontakt \
  /sortiment /magazin /pannobile /naturweine /datenschutz /impressum > "$WORK/queue.txt"
[ -f "$ROOT/csv-image-urls.txt" ] && cat "$ROOT/csv-image-urls.txt" >> "$WORK/assets.txt"

fetch() { curl -sSL --compressed -A "$UA" --retry 3 --max-time 90 -o "$2" -w '%{http_code}' "$1" 2>>"$LOG"; }

page_file() {            # "/winzer/beck?x=1" -> $OUT/pages/winzer/beck__x=1.html
  local p="$1" q=""
  case "$p" in *\?*) q="${p#*\?}"; p="${p%%\?*}";; esac
  p="${p%/}"; [ -z "$p" ] && p="/index"
  local f="$OUT/pages$p"
  [ -n "$q" ] && f="${f}__$(printf '%s' "$q" | tr -c 'A-Za-z0-9=._-' '_')"
  echo "$f.html"
}

normalize_link() {       # prints a site path, "ASSET <url>", or nothing
  local h="$1" cur="$2"
  h="${h//&amp;/&}"
  case "$h" in
    mailto:*|tel:*|javascript:*|\#*|"") return;;
    \?*) h="$cur$h";;
    http://www.wir2liebenwein.de*|https://www.wir2liebenwein.de*|http://wir2liebenwein.de*|https://wir2liebenwein.de*|https://w2lw.webflow.io*|http://w2lw.webflow.io*)
      h="$(printf '%s' "$h" | sed -E 's#^https?://[^/]+##')"; [ -z "$h" ] && h="/";;
    /*) ;;
    *) return;;
  esac
  h="${h%%#*}"; [ -z "$h" ] && h="/"
  [ "$h" != "/" ] && h="${h%/}"
  case "${h%%\?*}" in
    *.pdf|*.PDF|*.jpg|*.jpeg|*.png|*.gif|*.svg|*.webp|*.zip|*.mp4) echo "ASSET $BASE$h"; return;;
  esac
  echo "$h"
}

echo "== 1/3 Seiten werden geladen =="
fetch "$BASE/robots.txt" "$OUT/robots.txt" >/dev/null
code=$(fetch "$BASE/sitemap.xml" "$OUT/sitemap.xml")
if [ "$code" = "200" ]; then
  grep -oE '<loc>[^<]+</loc>' "$OUT/sitemap.xml" | sed -E 's#</?loc>##g' | while read -r u; do
    normalize_link "$u" "/"; done | grep -v '^ASSET' >> "$WORK/queue.txt"
fi

n=0
while :; do
  next=$(grep -vxF -f "$WORK/visited.txt" "$WORK/queue.txt" | head -1)
  [ -z "$next" ] && break
  echo "$next" >> "$WORK/visited.txt"
  n=$((n+1)); [ $n -gt 800 ] && { echo "Stop: >800 pages" | tee -a "$LOG"; break; }
  f="$(page_file "$next")"; mkdir -p "$(dirname "$f")"
  code=$(fetch "$BASE$next" "$f")
  echo "[$n] $code $next"
  echo "PAGE $code $next" >> "$LOG"
  if [ "$code" != "200" ]; then rm -f "$f"; continue; fi
  printf '%s\t%s\n' "$BASE$next" "${f#$OUT/}" >> "$OUT/pages-manifest.tsv"
  cur="${next%%\?*}"
  grep -oE 'href="[^"]*"' "$f" | sed -E 's/^href="//; s/"$//' | while read -r h; do
    r="$(normalize_link "$h" "$cur")"
    case "$r" in "") ;; ASSET\ *) echo "${r#ASSET }" >> "$WORK/assets.txt";; *) echo "$r" >> "$WORK/queue.txt";; esac
  done
  grep -oE "https?://[^\"' )<>,]+" "$f" | grep -E "$ASSET_HOSTS" \
    | sed -E 's/&quot;.*$//; s/&amp;/\&/g; s/&#x27;.*$//' >> "$WORK/assets.txt"
  sleep 0.3
done

asset_pass() {
  sort -u "$WORK/assets.txt" > "$WORK/assets.sorted"
  local total; total=$(wc -l < "$WORK/assets.sorted" | tr -d ' ')
  local i=0
  while read -r u; do
    [ -z "$u" ] && continue
    i=$((i+1))
    grep -qxF "$u" "$WORK/assets-done.txt" && continue
    echo "$u" >> "$WORK/assets-done.txt"
    rel="$(printf '%s' "$u" | sed -E 's#^https?://##; s/#.*$//')"
    case "$rel" in */?*) ;; *) continue;; esac      # skip bare hosts like https://fonts.gstatic.com
    case "$rel" in
      *\?*) q="${rel#*\?}"; rel="${rel%%\?*}__$(printf '%s' "$q" | tr -c 'A-Za-z0-9._-' '_' | cut -c1-80)";;
    esac
    case "$rel" in */) rel="${rel}index";; esac
    f="$OUT/assets/$rel"; mkdir -p "$(dirname "$f")"
    code=$(fetch "$u" "$f"); rc=$?
    [ $rc -ne 0 ] && [ "$code" = "200" ] && code="WRITE_ERROR_$rc"
    [ -s "$f" ] || { [ "$code" = "200" ] && code="EMPTY"; }
    echo "  [$i/$total] $code ${rel##*/}"
    printf '%s\t%s\t%s\n' "$u" "assets/$rel" "$code" >> "$OUT/assets-manifest.tsv"
    case "$f" in
      *.css|*css__*|*/css)
        grep -oE 'url\([^)]+\)' "$f" | sed -E "s/^url\(['\"]?//; s/['\"]?\)$//" | grep -E '^https?://' >> "$WORK/assets.txt";;
    esac
  done < "$WORK/assets.sorted"
}

echo "== 2/3 Bilder, CSS, JS, Fonts, PDFs werden geladen =="
asset_pass
echo "== 3/3 In CSS verlinkte Dateien (Fonts etc.) =="
asset_pass

pages=$(($(wc -l < "$OUT/pages-manifest.tsv") - 1))
assets=$(grep -c $'\t200$' "$OUT/assets-manifest.tsv")
failed=$(grep -vc $'\t200$' "$OUT/assets-manifest.tsv")
size=$(du -sh "$OUT" | cut -f1)
{
  echo "Downloaded: $(date)"
  echo "Pages: $pages"
  echo "Assets OK: $assets"
  echo "Assets failed: $((failed-1))"
  echo "Size: $size"
} | tee "$OUT/SUMMARY.txt"
echo
echo "Fertig! Sag Claude Bescheid."
