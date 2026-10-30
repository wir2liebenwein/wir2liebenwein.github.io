"""One-time migration: Webflow raw backup  ->  Eleventy source tree.

usage: python3 -I import_webflow.py <raw_dir> <repo_dir>

raw_dir  contains pages/ assets/ assets-manifest.tsv   (output of download-site.sh)
repo_dir is the Eleventy repo; posts must already exist (csv_to_posts.py)
"""
import sys, os, re, json, shutil, hashlib
from urllib.parse import unquote, urlsplit
from bs4 import BeautifulSoup
import yaml

RAW, REPO = sys.argv[1], sys.argv[2]
SRC = os.path.join(REPO, "src")
report = {"missing_assets": set(), "pages": []}

# ---------------------------------------------------------------- assets ---
WF_HOSTS = ("cdn.prod.website-files.com", "uploads-ssl.webflow.com")

def key_of(url):
    """normalize an asset URL: both Webflow CDN hosts serve identical files."""
    u = url.replace("&amp;", "&")
    parts = urlsplit(u if "://" in u else "https://" + u)
    path = unquote(parts.path)
    host = parts.netloc
    if host in WF_HOSTS:
        host = "wf"
    if host == "d3e54v103j8qbb.cloudfront.net":
        return "jquery"
    return host + path

def clean(name):
    name = unquote(name)
    name = re.sub(r"^[0-9a-f]{24}_", "", name)
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", name)
    return re.sub(r"-+", "-", name).strip("-").lower()   # lowercase: macOS/Windows are case-insensitive

asset_map = {}      # key -> site path ("/assets/...")
taken = {}          # site path -> key
copies = []         # (src_file, dest_site_path)

WEINLISTE_KEY = None
for line in open(os.path.join(RAW, "assets-manifest.tsv"), encoding="utf-8").read().splitlines()[1:]:
    url, local, status = line.split("\t")
    if status != "200":
        continue
    k = key_of(url)
    if k in asset_map:
        continue
    fname = os.path.basename(unquote(urlsplit(url).path))
    ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
    if k == "jquery":
        dest = "/assets/js/jquery-3.5.1.min.js"
    elif "webfont.js" in url:
        continue                                   # Google font loader: dropped
    elif ext == "css":
        dest = "/assets/css/webflow.css"
    elif ext == "js":
        dest = "/assets/js/" + fname
    elif ext in ("ttf", "woff", "woff2", "otf"):
        dest = "/assets/fonts/" + clean(fname)
    elif ext == "pdf":
        if "Sortiment11" in fname:
            dest = "/downloads/weinliste.pdf"
        else:
            dest = "/downloads/archiv/" + clean(fname).lower()
    else:
        dest = "/assets/images/" + clean(fname)
    if dest.lower() in taken and taken[dest.lower()] != k:
        hexid = re.match(r"^([0-9a-f]{24})_", unquote(fname))
        stem, dot, e = dest.rpartition(".")
        dest = f"{stem}-{(hexid.group(1)[-6:] if hexid else hashlib.md5(k.encode()).hexdigest()[:6])}.{e}"
    taken[dest.lower()] = k
    asset_map[k] = dest
    copies.append((os.path.join(RAW, local), dest))

for src, dest in copies:
    out = os.path.join(SRC, dest.lstrip("/"))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    shutil.copyfile(src, out)

URL_RE = re.compile(r"https?://(?:cdn\.prod\.website-files\.com|uploads-ssl\.webflow\.com|d3e54v103j8qbb\.cloudfront\.net)/[^\"'\s)<>,]+")

def localize(text):
    def rep(m):
        url = m.group(0)
        frag = ""
        if "#" in url:
            url, frag = url.split("#", 1)
            frag = "#" + frag
        k = key_of(url)
        if k in asset_map:
            return asset_map[k] + frag
        report["missing_assets"].add(url)
        return m.group(0)
    return URL_RE.sub(rep, text)

# CSS: localize url(...) and make them relative so the site works under any path
css_path = os.path.join(SRC, "assets/css/webflow.css")
css = open(css_path, encoding="utf-8").read()
css = localize(css)
css = re.sub(r'url\("?/assets/', 'url("../', css)
css = re.sub(r'url\("\.\./([^")]+)\)', r'url("../\1")', css)
open(css_path, "w", encoding="utf-8").write(css)

# ------------------------------------------------------------------ pages ---
WEINLISTE_SEITE = {}

def fix_links(html):
    html = localize(html)
    # internal absolute links -> site relative
    html = re.sub(r'href="https?://(?:www\.)?(?:wir2liebenwein\.de|w2lw\.webflow\.io)(/[^"]*)?"',
                  lambda m: f'href="{m.group(1) or "/"}"', html)
    # strip Webflow subresource-integrity attributes (files are now local)
    html = re.sub(r'\s(integrity|crossorigin)="[^"]*"', "", html)
    return html

def weinliste_links(html, page_key):
    """Tag links to the Weinliste so the page number lives in _data/weinliste.json"""
    def rep(m):
        page = m.group(1)
        WEINLISTE_SEITE.setdefault(page_key, int(page))
        return f'href="/downloads/weinliste.pdf#page={page}" data-weinliste-seite="{page_key}"'
    return re.sub(r'href="/downloads/weinliste\.pdf#page=(\d+)"', rep, html)

def page_meta(soup):
    m = {}
    m["title"] = soup.title.get_text() if soup.title else ""
    d = soup.head.find("meta", attrs={"name": "description"})
    if d:
        m["description"] = d.get("content", "")
    og = soup.head.find("meta", attrs={"property": "og:title"})
    if og and og.get("content") != m["title"]:
        m["og_title"] = og.get("content")
    m["wf_page"] = soup.html.get("data-wf-page")
    js = [s["src"] for s in soup.find_all("script", src=True) if "/js/webflow." in s["src"] and "schunk" not in s["src"]]
    if js and "19e9a5f9" in js[0]:
        m["webflow_bundle"] = "slider"
    return m

def body_content(soup):
    out = []
    for c in soup.body.children:
        if getattr(c, "name", None) is None:
            if str(c).strip():
                out.append(str(c))
            continue
        cls = c.get("class") or []
        if "navigation-max-width" in cls or "footer" in cls:
            continue
        if c.name == "script" and c.get("src"):
            continue
        out.append(str(c))
    return "\n".join(out)

def write_page(rel_out, front, content, raw=True):
    path = os.path.join(SRC, rel_out)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fm = yaml.safe_dump(front, allow_unicode=True, sort_keys=False, width=1000)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"---\n{fm}---\n{content}\n")
    report["pages"].append(rel_out)

pages_dir = os.path.join(RAW, "pages")
for dirpath, _, files in os.walk(pages_dir):
    for fn in files:
        if not fn.endswith(".html") or "__f5d5cea0" in fn:
            continue
        rel = os.path.relpath(os.path.join(dirpath, fn), pages_dir)[:-5]   # e.g. winzer/beck
        soup = BeautifulSoup(open(os.path.join(dirpath, fn), encoding="utf-8").read(), "lxml")
        meta = page_meta(soup)
        if rel == "index":
            continue     # handled separately below
        if rel == "neues":
            continue
        content = fix_links(body_content(soup))
        key = rel.split("/")[-1]
        content = weinliste_links(content, key)
        front = {"layout": "base.njk", **meta, "permalink": f"/{rel}/"}
        write_page(f"seiten/{rel}.html", front, content)

def split_around(html_str, marker_html):
    i = html_str.index(marker_html)
    return html_str[:i], html_str[i + len(marker_html):]

def raw(s):
    return "{% raw %}" + s + "{% endraw %}"

# homepage: latest 3 posts become a template include
soup = BeautifulSoup(open(os.path.join(pages_dir, "index.html"), encoding="utf-8").read(), "lxml")
meta = page_meta(soup)
dyn = soup.select_one(".blog-post-2-collection")
marker = "@@NEUIGKEITEN@@"
dyn.replace_with(BeautifulSoup(marker, "lxml").p.string if False else marker)
content = fix_links(body_content(soup))
before, after = split_around(content, marker)
write_page("index.njk", {"layout": "base.njk", **meta, "permalink": "/"},
           raw(before) + '\n{% include "partials/home-neuigkeiten.njk" %}\n' + raw(after))

# Neues: the post list + pagination become templates
soup = BeautifulSoup(open(os.path.join(pages_dir, "neues.html"), encoding="utf-8").read(), "lxml")
meta = page_meta(soup)
meta["title"] = "Neues"          # Webflow had the wrong title "Unser Wein" here
wrapper = soup.select_one(".blog-wrapper")
wrapper.replace_with(marker)
content = fix_links(body_content(soup))
before, after = split_around(content, marker)
front = {"layout": "base.njk", **meta,
         "pagination": {"data": "collections.beitraege", "size": 5, "alias": "beitraege"},
         "permalink": "{% if pagination.pageNumber == 0 %}/neues/{% else %}/neues/{{ pagination.pageNumber + 1 }}/{% endif %}"}
write_page("neues.njk", front,
           raw(before) + '\n{% include "partials/neues-liste.njk" %}\n' + raw(after))

# 404 page (Webflow served it for unknown URLs, our crawler saved it as sitemap.xml)
nf = os.path.join(RAW, "sitemap.xml")
if os.path.exists(nf):
    soup = BeautifulSoup(open(nf, encoding="utf-8").read(), "lxml")
    if soup.title and "Not Found" in soup.title.get_text():
        meta = page_meta(soup)
        write_page("seiten/404.html", {"layout": "base.njk", **meta, "title": "Seite nicht gefunden", "permalink": "/404.html"},
                   fix_links(body_content(soup)))

# ------------------------------------------------------------- post images ---
image_map = json.load(open(os.path.join(REPO, "tools/migration/image-map.json"), encoding="utf-8"))
local_by_key = {}
for line in open(os.path.join(RAW, "assets-manifest.tsv"), encoding="utf-8").read().splitlines()[1:]:
    url, local, status = line.split("\t")
    if status == "200":
        local_by_key.setdefault(key_of(url), os.path.join(RAW, local))
missing_post_imgs = []
for dest, url in image_map.items():          # image-map.json: post file -> CDN URL
    src = local_by_key.get(key_of(url))
    if not src:
        missing_post_imgs.append(url)
        continue
    out = os.path.join(REPO, dest)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    shutil.copyfile(src, out)

json.dump({"datei": "/downloads/weinliste.pdf",
           "hinweis": "Seitenzahlen im PDF, auf die die Winzer-Seiten springen. Bei neuer Weinliste prüfen!",
           "seiten": dict(sorted(WEINLISTE_SEITE.items()))},
          open(os.path.join(SRC, "_data/weinliste.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)

print("pages:", len(report["pages"]))
print("assets copied:", len(copies))
print("missing assets referenced in pages/css:", len(report["missing_assets"]))
for u in sorted(report["missing_assets"])[:40]:
    print("   ", u)
print("post images missing:", len(missing_post_imgs))
for u in missing_post_imgs[:20]:
    print("   ", u)
