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
