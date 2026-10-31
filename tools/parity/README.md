# Parity check (visual regression)

Screenshots every built page and compares it pixel by pixel with a baseline, so a
refactor can prove that nothing moved. Used for the semantic rebuild of 2026; the
baseline is commit `208910b` (the Webflow migration).

Needs Python 3 with `playwright`, `pillow`, `numpy` and a Chrome at `/usr/bin/google-chrome`.

| Script | Does |
|---|---|
| `shots.py <site> <out> [filter …]` | full-page PNG of every page at 1440 / 768 / 390 px, motion reduced |
| `states.py <site> <out>` | viewport PNGs of the interactive states with motion on: burger menu, nav on scroll, thumbnail hover, parallax, artist modal, slider, lightbox |
| `diff.py <a> <b> <diffs>` | lists every changed shot and writes a diff image (changed pixels in red) |
| `check.sh` | build + `shots.py` + `states.py` + `diff.py` against `../parity/baseline` |

Both shooters serve the site themselves (`serve.py`, which mimics GitHub Pages) and
block every non-local request, so the YouTube embed stays an empty frame.

Make the baseline once, outside the repo:

```bash
git worktree add ../w2lw-base 208910b
(cd ../w2lw-base && npm ci && npx eleventy)
python3 tools/parity/shots.py  ../w2lw-base/_site ../parity/baseline
python3 tools/parity/states.py ../w2lw-base/_site ../parity/baseline-states
tools/parity/check.sh            # after every change
```

Stability: lazy images are switched to eager before each shot, scroll-driven
transforms are waited out, and every full-page capture is repeated until two in a
row agree (Chrome occasionally paints a band twice). Two runs of the baseline give
0 changed pixels across all 129 page shots and 14 state shots.
