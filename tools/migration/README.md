# Migration from Webflow (one-time, October 2026)

These files document how the site was moved out of Webflow. They are **not needed**
for day-to-day work and are kept only for reference.

| File | Purpose |
|---|---|
| `download-site.sh` | Crawled www.wir2liebenwein.de (all pages + every CDN asset) into a raw backup `_archive/` |
| `webflow-blog-posts.csv` | Webflow CMS export of the "Blog Posts" collection (86 posts, 17 archived) |
| `csv_to_posts.py` | CSV → `src/posts/<datum>-<slug>/index.md` (+ `image-map.json`) |
| `import_webflow.py` | Raw backup → `src/seiten/*.html`, `src/index.njk`, `src/neues.njk`, `src/assets/**`, Weinliste |
| `image-map.json` | Which Webflow CDN image became which file in which post folder |

The raw backup itself (`_archive/`) is not part of this repository.
