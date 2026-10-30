#!/usr/bin/env node
// Bilder webtauglich machen: max. 1600 px breit, JPEG-Qualität 82, sauberer Dateiname.
//
//   npm run bilder -- src/posts/2027-01-15-mein-beitrag
//     -> verkleinert alle zu großen Bilder in diesem Ordner (Name bleibt gleich)
//
// Wird auch von tools/neuer-beitrag.mjs benutzt.
import fs from "node:fs";
import path from "node:path";
import sharp from "sharp";

const MAX_BREITE = 1600;
const MAX_BYTES = 900 * 1024;

export function sichererName(name) {
  return name
    .toLowerCase()
    .replace(/ä/g, "ae").replace(/ö/g, "oe").replace(/ü/g, "ue").replace(/ß/g, "ss")
    .normalize("NFKD").replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9._-]+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
}

/** kopiert/verkleinert `quelle` nach `zielOrdner`, gibt den neuen Dateinamen zurück */
export async function verkleinere(quelle, zielOrdner) {
  const ext = path.extname(quelle).toLowerCase();
  const basis = sichererName(path.basename(quelle, path.extname(quelle)));
  const istPng = ext === ".png";
  let name = basis + (istPng ? ".png" : ".jpg");
  let i = 2;
  while (fs.existsSync(path.join(zielOrdner, name)) && path.resolve(path.join(zielOrdner, name)) !== path.resolve(quelle))
    name = `${basis}-${i++}${istPng ? ".png" : ".jpg"}`;
  const ziel = path.join(zielOrdner, name);
  let bild = sharp(quelle, { failOn: "none" }).rotate();          // Handy-Fotos richtig drehen
  const meta = await bild.metadata();
  if ((meta.width || 0) > MAX_BREITE) bild = bild.resize({ width: MAX_BREITE });
  const puffer = istPng ? await bild.png({ compressionLevel: 9 }).toBuffer() : await bild.jpeg({ quality: 82, mozjpeg: true }).toBuffer();
  fs.writeFileSync(ziel, puffer);
  return name;
}

// Aufruf von der Kommandozeile: alle Bilder in den angegebenen Ordnern prüfen
if (import.meta.url === `file://${process.argv[1]}`) {
  const ordner = process.argv.slice(2);
  if (!ordner.length) { console.error("Ordner angeben, z.B. npm run bilder -- src/posts/2027-01-15-xyz"); process.exit(1); }
  for (const o of ordner) {
    for (const f of fs.readdirSync(o)) {
      if (!/\.(jpe?g|png)$/i.test(f)) continue;
      const p = path.join(o, f);
      const meta = await sharp(p).metadata();
      if ((meta.width || 0) <= MAX_BREITE && fs.statSync(p).size <= MAX_BYTES) continue;
      const vorher = fs.statSync(p).size;
      let bild = sharp(p, { failOn: "none" }).rotate();
      if ((meta.width || 0) > MAX_BREITE) bild = bild.resize({ width: MAX_BREITE });
      const buf = /\.png$/i.test(f) ? await bild.png({ compressionLevel: 9 }).toBuffer() : await bild.jpeg({ quality: 82, mozjpeg: true }).toBuffer();
      fs.writeFileSync(p, buf);
      console.log(`${p}: ${Math.round(vorher / 1024)} KB -> ${Math.round(buf.length / 1024)} KB`);
    }
  }
}
