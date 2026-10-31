// Erzeugt die WebP-Fassungen der Bühnenbilder (CSS-Hintergründe) nach
// src/assets/images/optimiert/. Originale bleiben. Aufruf: node tools/bilder/buehnen-webp.mjs
import sharp from "sharp";
import fs from "node:fs";
const BILDER = ["404_header", "bestell-kontakt-2x", "bottleshop", "home", "neues-780396",
  "sortiment-3", "unser_wein_header-2x", "vielfalt_im_denken"];
const quelle = "src/assets/images/", ziel = "src/assets/images/optimiert/";
fs.mkdirSync(ziel, { recursive: true });
for (const name of BILDER) {
  for (const [suffix, breite] of [["", 2000], ["-1080", 1080]]) {
    const out = `${ziel}${name}${suffix}.webp`;
    await sharp(`${quelle}${name}.jpg`).resize({ width: breite, withoutEnlargement: true })
      .webp({ quality: 80 }).toFile(out);
    console.log(out, fs.statSync(out).size);
  }
}
