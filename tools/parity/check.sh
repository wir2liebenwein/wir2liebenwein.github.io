#!/usr/bin/env bash
# Builds the current checkout and compares it with the baseline screenshots.
#   tools/parity/check.sh [out_dir]          (baseline: $PARITY_BASELINE, default ../parity/baseline)
# Make the baseline once from the reference commit:
#   git worktree add ../w2lw-base 208910b && (cd ../w2lw-base && npm ci && npm run build)
#   python3 tools/parity/shots.py ../w2lw-base/_site ../parity/baseline
#   python3 tools/parity/states.py ../w2lw-base/_site ../parity/baseline-states
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
repo="$(cd "$here/../.." && pwd)"
base="${PARITY_BASELINE:-$repo/../parity/baseline}"
out="${1:-$repo/../parity/current}"
cd "$repo"
npx eleventy --quiet >/dev/null
rm -rf "$out" "$out-states" "$out-diff" "$out-states-diff"
python3 "$here/shots.py" _site "$out"
python3 "$here/states.py" _site "$out-states"
echo "== pages =="
python3 "$here/diff.py" "$base" "$out" "$out-diff" || true
echo "== interactive states =="
python3 "$here/diff.py" "$base-states" "$out-states" "$out-states-diff" || true
