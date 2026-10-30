# wir2liebenwein.de — how the website is built

*Written October 2026, during the move from Webflow to this repository.*

This document describes the website completely: what is on it, how every part is
made, where the content lives and what to watch out for. It is meant for developers
and for AI agents. Day-to-day editing instructions (adding a post, swapping the
Weinliste) are in [`../AGENTS.md`](../AGENTS.md).

---

## 1. In one paragraph

Wir2LiebenWein (W2LW) is a small natural-wine shop and bar run by Sabine and Tina in
Munich-Westend (Schwanthalerstraße 142). It sells wines from winemakers in Gols,
Burgenland (Austria). The website is a brochure site with a **blog ("Neues")**, a
**downloadable wine list ("Weinliste" / Sortiment PDF)**, portraits of the
winemakers and some info pages. It was built in **Webflow** in 2019/2020. In
October 2026 it was exported and rebuilt as a static site with
[**Eleventy**](https://www.11ty.dev/). The look is **pixel-identical**: the original
Webflow CSS, JavaScript and HTML markup are reused unchanged, and only the blog is
generated from Markdown files.

## 2. Repository layout

```
├── AGENTS.md                     instructions for agents (German, for client edits)
├── CLAUDE.md                     points to AGENTS.md
├── docs/WEBSITE.md               this file
├── eleventy.config.js            build config + post validation + Weinliste page links
├── package.json                  npm scripts (build, start, neuer-beitrag, bilder)
├── .github/workflows/
│   └── veroeffentlichen.yml      GitHub Actions: build + deploy to GitHub Pages
├── src/
│   ├── index.njk                 homepage (static Webflow HTML + latest 3 posts)
│   ├── neues.njk                 blog list, paginated (5 per page)
│   ├── posts/                    ★ THE BLOG – one folder per post
│   │   ├── 2026-10-11-naked-naturweinmesse-vol-2-2/
│   │   │   ├── index.md          text + front matter
│   │   │   └── naked01.jpg       the post's images
│   │   ├── _archiv/              posts that were "archived" in Webflow (not published)
│   │   └── posts.11tydata.json   posts have no page of their own (permalink: false)
│   ├── seiten/                   all other pages, as frozen Webflow HTML
│   │   ├── sortiment.html, bottleshop.html, unser-wein.html, …
│   │   ├── winzer/*.html         8 winemaker portraits
│   │   └── weinpakete-2/*.html   9 wine-package pages (not in the menu)
│   ├── downloads/
│   │   ├── weinliste.pdf         ★ THE WINE LIST – always this exact file name
│   │   └── archiv/               old lists still linked somewhere
│   ├── _data/weinliste.json      ★ which PDF page each winemaker page jumps to
│   ├── _includes/
│   │   ├── layouts/base.njk      <head>, nav, footer, scripts – shared by all pages
│   │   └── partials/             nav, footer, blog post, homepage teaser, blog list
│   └── assets/
│       ├── css/webflow.css       original Webflow stylesheet (do not edit)
│       ├── css/eigene-anpassungen.css   overrides go here
│       ├── js/                   jQuery 3.5.1 + Webflow runtime (do not edit)
│       ├── fonts/                self-hosted fonts incl. W2LW icon font
│       └── images/               all non-blog images
└── tools/
    ├── neuer-beitrag.mjs         scaffolds a new post (folder, resized images, index.md)
    ├── bilder-verkleinern.mjs    resizes images to ≤1600 px / web-safe names
    └── migration/                one-time Webflow migration scripts + CSV (reference only)
```

★ = the three things clients change.

## 3. Site map

| URL | Source | Kind | Notes |
|---|---|---|---|
| `/` | `src/index.njk` | static + generated | Homepage; "Neuigkeiten" row = newest 3 posts |
| `/neues/`, `/neues/2/` … `/neues/14/` | `src/neues.njk` | generated | Blog, 5 posts per page, newest first |
| `/bottleshop/` | `seiten/bottleshop.html` | static | Shop/bar, opening hours |
| `/unser-wein/` | `seiten/unser-wein.html` | static | "Winzer / Wein": winemaker overview (was a CMS list in Webflow) |
| `/winzer/beck/` … | `seiten/winzer/*.html` | static | beck, gsellmann, heinrich, nittnaus, pittnauer, preisinger, renner-sistas, upa |
| `/verkostung` | — | **missing** | In the main menu, but the page does not exist (404 on the old site too) |
| `/ueber-uns/` | `seiten/ueber-uns.html` | static | About Sabine & Tina |
| `/bestell-kontakt/` | `seiten/bestell-kontakt.html` | static | How to order, contact, opening hours |
| `/sortiment/` | `seiten/sortiment.html` | static | Range description + **Weinliste download** + opening hours |
| `/magazin/` | `seiten/magazin.html` | static | "The Naturals" magazine |
| `/pannobile/` | `seiten/pannobile.html` | static | Pannobile region; embeds a YouTube video |
| `/naturweine/` | `seiten/naturweine.html` | static | What natural wine is |
| `/weinpakete-2/<name>/` | `seiten/weinpakete-2/*.html` | static | 9 wine packages (bambule, bubbles, funky-fuer-fortgeschrittene, glou-glou, klassisch-deluxe, naturwein-einstieg, pannobile, rare-und-sexy, schoen-gereift). Not linked from the menu. |
| `/impressum/`, `/datenschutz/` | `seiten/*.html` | static | Legal pages |
| `/404.html` | `seiten/404.html` | static | Shown for unknown URLs |

Static pages are the original Webflow HTML (body only). Their front matter holds the
`<title>`, meta description and the Webflow page id. They are copied 1:1;
`htmlTemplateEngine: false` makes sure nothing inside them is interpreted as a template.

URLs keep the Webflow paths. The new site serves them with a trailing slash
(`/sortiment/`), and links without the slash (`/sortiment`) redirect automatically.

## 4. Shared layout (every page)

`src/_includes/layouts/base.njk` wraps every page:

1. **`<head>`**: title/description/OpenGraph from front matter, `webflow.css`,
   `eigene-anpassungen.css`, the Webflow `w-mod-js` snippet, favicon/webclip, and a
   1280 px max-width rule for big screens.
2. **Navigation** (`partials/nav.njk`): logo (wordmark + sign) and the links Neues ·
   Bottleshop · Winzer / Wein · Verkostung · Über Uns · Bestellen · Sortiment.
   "Bestellen" and "Sortiment" carry icon-font glyphs. On tablet and phone (below
   992 px) it collapses into a burger menu, which is handled by `webflow.js`. The active
   link gets `w--current`, which is decided at build time from `page.url`.
3. **Page content.**
4. **Footer** (`partials/footer.njk`): "Der Schnell-Bestell-Kontakt" (text, phone
   +49 172 855 80 60, info@wir2liebenwein.de, link to Bestell-Kontakt), "Hier sind wir
   auch unterwegs" (Facebook, Instagram icons), "©Copyright 2020 WIR2LIEBENWEIN",
   Datenschutz & Impressum.
5. **Scripts**: jQuery 3.5.1 and the Webflow runtime. The Neues page loads a
   different runtime bundle (`webflow.19e9a5f9…js`) that additionally contains the
   **slider** and **lightbox** modules (front matter `webflow_bundle: slider`).

Most pages also contain these blocks in their own HTML: the big grey section titles
("Neuigkeiten", "Winzer", …), teaser modules (image + Oswald headline + "Mehr
Erfahren" + arrow), a newsletter block and an Instagram teaser. The newsletter block
is not a form. "Direkt anmelden" is a plain `mailto:info@…`, and the text asks people
to write "Newsletter" as the subject. "Yeah! Neues entdecken" is a `mailto:` with the
subject "Verkostungstermine".

**There are no forms, no cookies, no analytics and no tracking scripts.** External
requests: only the YouTube embed on `/pannobile/`.

### Webflow runtime and interactions

`webflow.js` runs the burger menu, the blog slider and lightbox, and a few
"Interactions" (IX2), for example the hover zoom on the homepage post thumbnails. IX2
finds its animations through the `data-w-id` attributes on elements and the
`data-wf-page` / `data-wf-site` attributes on `<html>`. **Keep those attributes
untouched**, or the animations silently stop.

### Fonts

All self-hosted in `src/assets/fonts/`, declared in `webflow.css`:

| Font | Used for |
|---|---|
| Oswald (variable) | Headlines, nav, post titles, uppercase labels |
| Source Sans Pro Regular/Bold | Body text |
| Libre Baskerville | A few accent texts (serif) |
| **W2LW icon font** (`W2LW-Icon-Font.woff`) | Icons are typed as letters: `a` = mail/contact, `C` = list/Sortiment, `A` = order, `b` = arrow ("Yeah! Neues entdecken"), `g` = arrow in the magazine badge, `D` = download, `J` = Instagram |
| facebook-icon.woff | The Facebook "A" in the footer |

The old site *additionally* loaded Oswald from Google Fonts through `webfont.js`. That
is gone (see §9).

## 5. The blog ("Neues")

### 5.1 One post = one folder

```
src/posts/2026-10-11-naked-naturweinmesse-vol-2-2/
├── index.md
└── naked01.jpg
```

The folder name is `<date>-<slug>`. The slug (folder name without the date) is
also the post's HTML anchor (`/neues/#naked-naturweinmesse-vol-2-2`).

### 5.2 Front matter

```yaml
---
titel: Naked Naturweinmesse Vol. 2        # big Oswald headline (h2)
unterzeile: Vorfreude pur                 # small orange line above the title ("Tag" in Webflow)
datum: 2026-10-11 17:47                   # sort order; time optional; not displayed anywhere
darstellung: einzelbild                   # einzelbild | lightbox | slider  (see 5.3)
bilder:                                   # files in the same folder; first = main/teaser image
- naked01.jpg
zusatzlink: |-                            # optional, Markdown; shown under the text with a pink arrow
  Hier bekommt ihr eure [Tickets](https://…)
veroeffentlicht: false                    # optional; false = hidden (used for archived posts)
webflow_id: 6acbcbcec816eb85bbcf5edf      # only on migrated posts, for reference
---

Post text in Markdown…
```

| Field | Required | Webflow field | Shown as |
|---|---|---|---|
| `titel` | yes | Überschrift | `<h2 class="heading">` |
| `unterzeile` | yes | Tag | `<div class="post-tag">` (orange caps) |
| `datum` | yes | Date (+ Created On time) | not shown, only sorts |
| `darstellung` | yes | Einzelbild / Slider / Lightbox switches | see 5.3 |
| `bilder` | yes, ≥1 | Teaser/Mainimage/Slide 1 … Slide 5 | see 5.3; `bilder[0]` is also the homepage thumbnail |
| `zusatzlink` | no | Zusätzlicher Link | `.text-arrow-combo` |
| body | – | Postinhalte | `.rich-text-block` |

**Text conventions.** Paragraphs are separated by a blank line. A line break inside a
paragraph ends the line with `\`. A **deliberate empty line** (the clients use them
for breathing room) is a paragraph containing only `&nbsp;`. A few migrated posts
contain `<p></p>`: Webflow had paragraphs holding just a space, which browsers
collapse to only their margin, and this keeps that spacing exact. Bold is `**…**`.
External links open in a new tab automatically. Internal links are written as
`/winzer/beck`.

### 5.3 Image display modes

Every Webflow post contained *all three* layouts and hid two of them with CSS. The
real rules, worked out from the live site rather than from the field names, are:

| `darstellung` | Webflow switches | What is shown |
|---|---|---|
| `slider` | Slider = on | Webflow slider with all `bilder` (arrows + dots) |
| `einzelbild` | Slider off, Einzelbild on | `bilder[0]` large, opens in lightbox on click |
| `lightbox` | Slider off, Einzelbild off | `bilder[0]` large **plus** a row of up to 3 thumbnails (`bilder[1..3]`); all open in the lightbox |

Current split: 50 einzelbild, 15 lightbox, 4 slider. The lightbox row is rendered
even when there is only one image, because its 20 px top padding is part of the
original spacing. Post images are always shown at full column width (max 800 px).
`eigene-anpassungen.css` enforces this, matching what Webflow did through
`srcset`/`sizes`.

### 5.4 Under every post

The text is followed by the optional `zusatzlink` with an arrow, then a fixed bar with
two links: "Unsere Kontaktdaten ✉" → `/bestell-kontakt` and "Unser Sortiment" →
`/sortiment`. That bar is hard-coded in `partials/beitrag.njk` and identical for every
post.

### 5.5 Ordering, homepage, pagination

* Collection `beitraege` (in `eleventy.config.js`): all `src/posts/*/index.md`, minus
  `veroeffentlicht: false`, sorted by `datum` descending. Webflow sorted by Date, then
  by creation time, which is why migrated posts carry a time.
* **Homepage** (`partials/home-neuigkeiten.njk`): the first 3 posts, shown as
  thumbnail + unterzeile + titel. Each one links to the post on `/neues/`
  (`/neues/#slug`).
* **Neues** (`neues.njk` + `partials/neues-liste.njk`): 5 posts per page; `/neues/`,
  `/neues/2/` … with "Zurück"/"Weiter". With 69 posts that makes 14 pages; the count
  grows automatically.
* Old Webflow page URLs (`/neues?f5d5cea0_page=3`) are redirected to `/neues/3/` by a
  tiny inline script.

There are **no individual post pages**, just as on the old site. Everything lives on
`/neues/`.

### 5.6 Validation (safety net)

Every build checks each post: required fields present, `darstellung` valid, every
image exists, image names only `a-z 0-9 - _ .`, no image above 3 MB, and a slider with
at least 2 images. Any violation **fails the build** with a German explanation. On
GitHub this means the deploy is skipped and **the live site stays as it was**.

### 5.7 Archived posts

The 17 posts that were archived in Webflow are in `src/posts/_archiv/` with
`veroeffentlicht: false`. They are ignored by the build. To bring one back, move its
folder up one level and delete the `veroeffentlicht` line.

## 6. The Weinliste (wine list PDF)

* Lives at **`src/downloads/weinliste.pdf`**, published as `/downloads/weinliste.pdf`.
  The file name never changes, so updating the list means replacing one file.
* Linked from `/sortiment/` (big download button), `/naturweine/`, `/pannobile/` (3
  links) and each winemaker page ("zu den Weinen").
* The winemaker links **jump to a specific PDF page** (`#page=4`). The page numbers
  live in **`src/_data/weinliste.json`**:

  ```json
  "seiten": { "beck": 4, "gsellmann": 6, "heinrich": 5, "naturweine": 1, "nittnaus": 6,
              "pannobile": 3, "pittnauer": 7, "preisinger": 8, "renner-sistas": 9, "sortiment": 1 }
  ```

  In the HTML these links carry `data-weinliste-seite="beck"`; at build time a
  transform writes the right `#page=` from the JSON. **When a new list arrives, check
  whether the winemakers moved to other pages** and update this file.
* `/winzer/upa/` still links to the **November 2021** list
  (`downloads/archiv/sortimentliste_1121.pdf`, page 9), exactly as on the old site.
  UPA (beer) is probably no longer stocked; this needs a decision.

## 7. Static pages (winemakers, packages, info)

These were partly Webflow CMS collections ("Winzer", "Weinpakete"). No export of those
collections exists, so they were frozen as HTML. They rarely change. To edit them,
change the text directly in `src/seiten/…html`, keep the class names, and leave the
`data-w-id` attributes alone.

**Opening hours are written by hand in three places**, each formatted differently:
`seiten/sortiment.html`, `seiten/bottleshop.html` and `seiten/bestell-kontakt.html`.
Change all three; posts announcing new hours are a separate matter.

## 8. Build and hosting

* `npm run build` → `_site/`. `npm start` serves it locally at http://localhost:8080
  with live reload.
* Every push to `main` triggers `.github/workflows/veroeffentlichen.yml`: `npm ci` →
  `npm run build` → deploy to **GitHub Pages**. That takes about 1–2 minutes.
* The repository is `wir2liebenwein/wir2liebenwein.github.io`, so the test address is
  https://wir2liebenwein.github.io/. The site uses root-relative URLs (`/assets/…`), so
  it must run at a domain root (that address or the real domain), not under a
  sub-path.
* **Going live on www.wir2liebenwein.de.** In the repo, go to Settings → Pages → Custom
  domain = `www.wir2liebenwein.de`. Then, at the DNS provider, change **only**:
  * `www` → CNAME `wir2liebenwein.github.io`
  * the bare domain `@` → A records `185.199.108.153`, `185.199.109.153`,
    `185.199.110.153`, `185.199.111.153`

  Leave the MX/TXT/SPF records alone, because email depends on them. Then tick
  "Enforce HTTPS".
* Size: about 145 MB, mostly images. GitHub Pages allows 1 GB.

## 9. Deliberate differences from the Webflow site

| Change | Why |
|---|---|
| Removed the Google Fonts loader (`webfont.js`) | Oswald was already self-hosted. Loading it from Google sends visitor IPs to Google (LG München, 2022). No visual change. |
| Posts render only the active image layout; hidden duplicates and the hidden "What's a Rich Text element?" placeholder block are gone | Cleaner HTML, same look |
| Sliders show only real images | Webflow always rendered 5 slides, leaving empty slides when there were fewer images |
| Lightbox groups per post | Webflow put every image on the page into one gallery |
| Homepage teasers link to the exact post (`/neues/#slug`) | Previously all went to the top of `/neues` |
| Pagination URLs `/neues/2/` instead of `?f5d5cea0_page=2` | Static hosts ignore query strings; old links are redirected |
| `<title>` of the blog page is "Neues" | It was wrongly "Unser Wein" |
| Post images have alt text (= title) and lazy loading; no `srcset` | Accessibility/speed; CMS images have no resized variants |
| Image file names are web-safe (`ros%C3%A9.jpg` → `rose.jpg`, Webflow ID prefixes removed) | Robust URLs |

Verification: all 15 main page types and all 14 blog pages were screenshotted (desktop
1440 px and mobile 390 px) against the original Webflow HTML and compared
pixel by pixel. They are identical, apart from a sub-pixel rounding difference
in some mobile image heights.

## 10. Known issues inherited from the live site (October 2026)

1. **`/verkostung` does not exist.** It is in the main menu and on the homepage
   ("Wer verkostet das Leben?"), and one post links to it as "Newsletteranmeldung".
   Webflow returned 404 too. Either recreate the page or remove the links.
2. `/weinpakete` (an overview page) does not exist but is linked from all 9 package
   pages. `/winzer/achs` and `/winzer/muff` are linked from `/unser-wein/` but do not
   exist.
3. `/winzer/upa/` links to the 2021 wine list (§6).
4. **Datenschutzerklärung**: it describes Google Analytics and Google Maps (neither is
   used) and does not mention hosting. It must be updated for GitHub Pages, and the
   YouTube embed on `/pannobile/` should be mentioned or switched to
   `youtube-nocookie.com`.
5. Small things: the copyright line says 2020, the homepage `<title>` is just "W2LW",
   and the newest post contains the typo "Ticktes".
