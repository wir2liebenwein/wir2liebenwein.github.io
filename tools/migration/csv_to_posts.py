"""Convert the Webflow 'Blog Posts' CSV export into one Markdown file per post.

Output: <repo>/src/posts/<YYYY-MM-DD>-<slug>/index.md   (live posts)
        <repo>/src/posts/_archiv/<YYYY-MM-DD>-<slug>/index.md (archived in Webflow)
Also writes <repo>/tools/image-map.json : original CDN URL -> repo path,
used later to copy images from the raw backup.
"""
import csv, json, re, sys, os
from urllib.parse import unquote
from datetime import datetime
from markdownify import markdownify as md
import yaml

csv_path, repo = sys.argv[1], sys.argv[2]

# multi-line values as readable YAML blocks ( key: |  ...)
def _str(dumper, s):
    return dumper.represent_scalar("tag:yaml.org,2002:str", s, style="|" if "\n" in s else None)
yaml.SafeDumper.add_representer(str, _str)
rows = list(csv.DictReader(open(csv_path, encoding="utf-8")))

def parse_date(s):
    return datetime.strptime(s[4:24], "%b %d %Y %H:%M:%S") if s else None

def clean_html(h):
    h = re.sub(r'\s(id|class)=""', "", h)
    # 1) paragraph with only a normal space: browsers collapse it (margin only) -> empty <p></p>
    h = re.sub(r"<p>[ \t\n]*</p>", "<p>LEERPXYZ</p>", h)
    # 2) Webflow spacer paragraphs (zero-width joiner / nbsp / br = intentional blank line)
    #    -> "&nbsp;" line in Markdown
    h = h.replace("\u200d", "")
    h = re.sub(r"<p[^>]*>\s*(&nbsp;|\s|<br>)*\s*</p>", "<p>LEERZEILEXYZ</p>", h)
    h = h.replace("&nbsp;", " ")
    h = re.sub(r"<(strong|em|b|i)>(\s*)</\1>", r"\2", h)   # empty bold/italic around a space
    # internal absolute links -> site-relative
    h = re.sub(r'https?://(www\.)?(wir2liebenwein\.de|w2lw\.webflow\.io)', "", h)
    return h

def to_md(h):
    if not h.strip():
        return ""
    m = md(clean_html(h), heading_style="ATX", bullets="-", strong_em_symbol="*", newline_style="backslash")
    m = re.sub(r"[ \t]+\n", "\n", m)
    m = re.sub(r"\n{3,}", "\n\n", m).strip()
    m = m.replace("** **", " ")
    m = m.replace("LEERZEILEXYZ", "&nbsp;")
    m = m.replace("LEERPXYZ", "<p></p>")
    return m

def local_name(url):
    base = url.split("/")[-1].split("?")[0]
    base = unquote(base)
    base = re.sub(r"^[0-9a-f]{24}_", "", base)            # strip Webflow id prefix
    base = base.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss"), ("é", "e"), ("è", "e"), ("@", "-at-"), ("&", "-und-"), ("+", "-")):
        base = base.replace(a, b)
    base = re.sub(r"[^a-z0-9._-]+", "-", base)            # web-safe file names
    return re.sub(r"-+", "-", base).strip("-")

img_cols = ["Teaser / Mainimage / Slide 1", "Slide 2 / Lightbox Thumb 1",
            "Slide 3 / Lightbox Thumb 2", "Slide 4 / Lightbox Thumb 3", "Slide 5"]
image_map, used_dirs = {}, set()

def sort_key(x):
    return (parse_date(x["Date"]), parse_date(x["Created On"]))

for x in sorted(rows, key=sort_key):
    d = parse_date(x["Date"]).strftime("%Y-%m-%d")
    folder = f"{d}-{x['Blog']}"
    archived = x["Archived"] == "true"
    sub = os.path.join("src", "posts", "_archiv" if archived else "", folder)
    sub = os.path.normpath(sub)
    assert sub not in used_dirs, sub
    used_dirs.add(sub)
    os.makedirs(os.path.join(repo, sub), exist_ok=True)

    # Rules derived from the live Webflow output (not from the flag names):
    # Slider on -> slider only; else Einzelbild on -> main image only;
    # else -> main image + up to 3 lightbox thumbnails (images 2-4).
    if x["Slider"] == "true":
        mode = "slider"
    elif x["Einzelbild"] == "true":
        mode = "einzelbild"
    else:
        mode = "lightbox"

    bilder, names = [], {}
    for c in img_cols:
        u = x[c].strip()
        if not u:
            continue
        n = local_name(u)
        # avoid two different source files mapping to one name
        if n in names and names[n] != u:
            stem, ext = os.path.splitext(n)
            n = f"{stem}-{len(names)}{ext}"
        names[n] = u
        image_map[os.path.join(sub, n)] = u
        bilder.append(n)

    # images embedded in the rich text
    body_html = x["Postinhalte"]
    for u in set(re.findall(r'https?://[^"\s]+(?:website-files\.com|webflow\.com)[^"\s]*', body_html)):
        n = local_name(u)
        image_map[os.path.join(sub, n)] = u
        body_html = body_html.replace(u, n)

    fm = {
        "titel": x["Überschrift"].strip(),
        "unterzeile": x["Tag"].strip(),
        # Webflow sorts by Date, then by creation time -> keep the time for same-day order
        "datum": d + " " + parse_date(x["Created On"]).strftime("%H:%M"),
        "darstellung": mode,
        "bilder": bilder,
    }
    link_md = to_md(x["Zusätzlicher Link"])
    if link_md:
        fm["zusatzlink"] = link_md
    if archived:
        fm["veroeffentlicht"] = False
    fm["webflow_id"] = x["Item ID"]

    front = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False, width=1000)
    body = to_md(body_html)
    with open(os.path.join(repo, sub, "index.md"), "w", encoding="utf-8") as f:
        f.write(f"---\n{front}---\n\n{body}\n")

os.makedirs(os.path.join(repo, "tools"), exist_ok=True)
json.dump(image_map, open(os.path.join(repo, "tools", "image-map.json"), "w"), indent=1, ensure_ascii=False)
print(len(used_dirs), "posts,", len(image_map), "images")
