// Eleventy-Konfiguration für wir2liebenwein.de
// Wer hier etwas ändert, sollte docs/WEBSITE.md gelesen haben.
import fs from "node:fs";
import path from "node:path";
import markdownIt from "markdown-it";
import Image from "@11ty/eleventy-img";
import sharp from "sharp";

const DARSTELLUNGEN = ["einzelbild", "lightbox", "slider"];
const BILD_ENDUNGEN = /\.(jpe?g|png|gif|webp)$/i;

// Markdown: externe Links öffnen in neuem Tab (wie bisher in Webflow)
const md = markdownIt({ html: true, breaks: false, linkify: false });
const defaultLink = md.renderer.rules.link_open || ((t, i, o, e, s) => s.renderToken(t, i, o));
md.renderer.rules.link_open = (tokens, idx, options, env, self) => {
  const href = tokens[idx].attrGet("href") || "";
  if (/^https?:\/\//.test(href)) {
    tokens[idx].attrSet("target", "_blank");
    tokens[idx].attrSet("rel", "noopener");
  }
  return defaultLink(tokens, idx, options, env, self);
};

// "2026-10-11" oder "2026-10-11 17:47" -> sortierbarer Text
const sortKey = (datum) => String(datum instanceof Date ? datum.toISOString() : datum).replace(" ", "T");

function pruefeBeitrag(item) {
  const d = item.data;
  const wo = path.relative(".", item.inputPath);
  const fehler = [];
  for (const feld of ["titel", "unterzeile", "datum", "darstellung", "bilder"]) {
    if (d[feld] === undefined || d[feld] === null || d[feld] === "") fehler.push(`Feld "${feld}" fehlt`);
  }
  if (d.datum && !(d.datum instanceof Date) && !/^\d{4}-\d{2}-\d{2}( \d{2}:\d{2})?$/.test(String(d.datum)))
    fehler.push(`"datum" muss so aussehen: 2026-11-14  (optional mit Uhrzeit: 2026-11-14 18:30)`);
  if (d.darstellung && !DARSTELLUNGEN.includes(d.darstellung))
    fehler.push(`"darstellung" muss einzelbild, lightbox oder slider sein (ist: ${d.darstellung})`);
  if (!Array.isArray(d.bilder) || d.bilder.length === 0) fehler.push(`"bilder" braucht mindestens ein Bild`);
  else {
    const ordner = path.dirname(item.inputPath);
    for (const b of d.bilder) {
      if (!BILD_ENDUNGEN.test(b)) fehler.push(`Bild "${b}" ist kein jpg/png/gif/webp`);
      else if (!/^[a-z0-9._-]+$/.test(b))
        fehler.push(`Bildname "${b}" nur mit a-z, 0-9, - _ . (keine Leerzeichen, Umlaute, Großbuchstaben)`);
      else if (!fs.existsSync(path.join(ordner, b))) fehler.push(`Bild "${b}" liegt nicht im Ordner ${ordner}`);
      else if (fs.statSync(path.join(ordner, b)).size > 3 * 1024 * 1024)
        fehler.push(`Bild "${b}" ist größer als 3 MB – bitte mit "npm run bilder" verkleinern`);
    }
  }
  if (d.darstellung === "slider" && Array.isArray(d.bilder) && d.bilder.length < 2)
    fehler.push(`"slider" braucht mindestens 2 Bilder`);
  if (fehler.length) throw new Error(`\n\nBEITRAG FEHLERHAFT: ${wo}\n  - ${fehler.join("\n  - ")}\n`);
}

export default function (eleventyConfig) {
  eleventyConfig.setLibrary("md", md);
  eleventyConfig.addFilter("markdown", (s) => md.render(String(s || "")));

  // Dateien, die 1:1 kopiert werden
  eleventyConfig.addPassthroughCopy("src/assets");
  eleventyConfig.addPassthroughCopy("src/downloads");
  eleventyConfig.addPassthroughCopy("src/posts/*/*.{jpg,jpeg,JPG,JPEG,png,PNG,gif,webp}");

  // Archivierte Beiträge (in Webflow archiviert) werden nicht veröffentlicht
  eleventyConfig.ignores.add("src/posts/_archiv/**");

  // Alle Beiträge, neueste zuerst
  eleventyConfig.addCollection("beitraege", (api) => {
    const items = api
      .getFilteredByGlob("src/posts/*/index.md")
      .filter((i) => i.data.veroeffentlicht !== false);
    items.forEach(pruefeBeitrag);
    return items.sort((a, b) => sortKey(b.data.datum).localeCompare(sortKey(a.data.datum)));
  });

  // URL eines Bildes aus dem Ordner des Beitrags
  eleventyConfig.addFilter("bildUrl", (item, datei) => {
    const ordner = path.relative("src", path.dirname(item.inputPath)).split(path.sep).join("/");
    return `/${ordner}/${datei}`;
  });

  // Weinliste: Seitenzahlen der Sprung-Links kommen aus src/_data/weinliste.json
  eleventyConfig.addTransform("weinliste-seiten", function (content) {
    if (!(this.page.outputPath || "").endsWith(".html")) return content;
    const wl = JSON.parse(fs.readFileSync("src/_data/weinliste.json", "utf8"));
    return content.replace(
      /href="\/downloads\/weinliste\.pdf(?:#page=\d+)?" data-weinliste-seite="([\w-]+)"/g,
      (m, key) => {
        const s = wl.seiten?.[key];
        return `href="${wl.datei}${s ? "#page=" + s : ""}" data-weinliste-seite="${key}"`;
      }
    );
  });

  // Bilder: jedes <img> bekommt width/height (kein Springen beim Laden); Beitragsbilder
  // zusätzlich verkleinerte WebP-Fassungen per srcset. Die Originale bleiben, wie sie sind.
  const groessen = new Map();
  async function bildMasse(datei) {
    if (!groessen.has(datei)) {
      groessen.set(datei, sharp(datei).metadata().then((m) =>
        (m.orientation || 1) >= 5 ? { w: m.height, h: m.width } : { w: m.width, h: m.height }));
    }
    return groessen.get(datei);
  }
  eleventyConfig.addTransform("bilder", async function (content) {
    if (!(this.page.outputPath || "").endsWith(".html")) return content;
    const teile = [];
    let rest = 0;
    for (const m of content.matchAll(/<img\b[^>]*>/g)) {
      let tag = m[0];
      const src = (tag.match(/\ssrc="([^"]+)"/) || [])[1] || "";
      const datei = path.join("src", decodeURIComponent(src));
      if (src.startsWith("/") && /\.(jpe?g|png|gif|webp)$/i.test(src) && fs.existsSync(datei)) {
        if (!/\swidth=/.test(tag) && !/\sheight=/.test(tag)) {
          const { w, h } = await bildMasse(datei);
          tag = tag.replace(/^<img/, `<img width="${w}" height="${h}"`);
        }
        if (src.startsWith("/posts/") && !/\ssrcset=/.test(tag)) {
          const meta = await Image(datei, {
            widths: [400, 800, 1200, 1600],
            formats: ["webp"],
            outputDir: path.join("_site", "bilder"),
            urlPath: "/bilder/",
            sharpWebpOptions: { quality: 82 },
          });
          const srcset = meta.webp.map((v) => `${v.url} ${v.width}w`).join(", ");
          tag = tag.replace(/^<img/, `<img srcset="${srcset}"`);
        }
      }
      teile.push(content.slice(rest, m.index), tag);
      rest = m.index + m[0].length;
    }
    teile.push(content.slice(rest));
    return teile.join("");
  });

  return {
    dir: { input: "src", output: "_site", includes: "_includes", layouts: "_includes/layouts", data: "_data" },
    htmlTemplateEngine: false,       // übernommene Webflow-Seiten bleiben unverändert
    markdownTemplateEngine: false,   // Beitragstexte werden nicht als Vorlage ausgewertet
  };
}
