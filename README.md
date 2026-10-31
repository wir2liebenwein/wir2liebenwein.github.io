# wir2liebenwein.de

Website of **Wir2LiebenWein**, natural wine shop & bar in Munich-Westend.
Static site built with [Eleventy](https://www.11ty.dev/), migrated from Webflow in October 2026
and rebuilt as semantic, accessible HTML/CSS/JS in autumn 2026 (same look, no Webflow code).

* **Editing content (posts, Weinliste)** → [`AGENTS.md`](AGENTS.md) (German, written for AI agents
  that act as the "CMS" for the shop owners)
* **How the site is built** → [`docs/WEBSITE.md`](docs/WEBSITE.md)

```bash
npm ci
npm start        # local preview with live reload: http://localhost:8080
npm run build    # -> _site/  (also validates every blog post)
```

Every push to `main` is built and deployed to GitHub Pages by
`.github/workflows/veroeffentlichen.yml`. If the build fails, the live site stays unchanged.

## Preview a pull request

GitHub Pages only publishes `main`, so a pull request has no preview link. Run its branch
locally instead. The branch name is at the top of the pull request ("… wants to merge
into `main` from `<branch>`"). You need Node 22.

**Use a fresh folder outside Dropbox.** Running `npm ci` or switching branches inside a
synced folder makes Dropbox upload thousands of files and can leave the repo in a broken
state.

```bash
cd ~/Desktop
git clone -b <branch> https://github.com/wir2liebenwein/wir2liebenwein.github.io w2lw-test
cd w2lw-test
npm ci
npm start        # http://localhost:8080 – Ctrl+C stops it
```

New commits on the pull request: `git pull`, then `npm start` again. When you are done,
delete the `w2lw-test` folder.

Compare it side by side with the current version at https://wir2liebenwein.github.io/,
and check in **Safari** too (Mac, and Develop → Enter Responsive Design Mode for phone
widths), not only in Chrome. The interactive parts:

| What | Where | Check |
|---|---|---|
| Burger menu | any page, window narrower than 992 px | opens, closes with Esc and on link click |
| Nav on scroll | any page | bar slides away scrolling down, returns scrolling up |
| Parallax | home, bar photo, window wider than 992 px | photo moves slower than the page |
| Artist window | `/winzer/beck/` → "Nikolaus Eberstaller" | opens; "schliessen", the X and Esc close it |
| Slider | `/neues/` → "Alkoholfrei neu gedacht" | arrows and dots; after the last image comes the first |
| Lightbox | `/neues/2/` → Saluki pizza post | thumbnails, arrow keys, Esc |
| Keyboard | any page, press Tab | first stop "Zum Inhalt springen", then a magenta focus ring |

The same checks run automatically in `tools/parity/behaviour.py` (Chrome only); see
[`tools/parity/README.md`](tools/parity/README.md).
