#!/usr/bin/env node
// Legt einen neuen Beitrag an: Ordner + index.md + verkleinerte, sauber benannte Bilder.
//
//   npm run neuer-beitrag -- --titel "Naked Naturweinmesse Vol. 3" \
//        --unterzeile "Save the Date" --darstellung einzelbild \
//        --datum 2027-01-15 --text text.md  bild1.jpg bild2.jpg
//
// Pflicht: --titel, --unterzeile, mindestens ein Bild.
// Optional: --datum (Standard: heute), --darstellung (einzelbild|lightbox|slider,
//           Standard: einzelbild bzw. slider bei 2+ Bildern nicht automatisch – bewusst wählen),
//           --text (Datei mit dem Beitragstext in Markdown), --link (Zusatzlink in Markdown)
import fs from "node:fs";
import path from "node:path";
import { verkleinere, sichererName } from "./bilder-verkleinern.mjs";

const args = process.argv.slice(2);
const opt = {};
const dateien = [];
for (let i = 0; i < args.length; i++) {
  if (args[i].startsWith("--")) opt[args[i].slice(2)] = args[++i];
  else dateien.push(args[i]);
}
const fehler = (m) => { console.error("FEHLER: " + m); process.exit(1); };
if (!opt.titel) fehler('--titel fehlt');
if (!opt.unterzeile) fehler('--unterzeile fehlt (kleine orange Zeile über dem Titel)');
if (!dateien.length) fehler("mindestens ein Bild angeben");
const darstellung = opt.darstellung || "einzelbild";
if (!["einzelbild", "lightbox", "slider"].includes(darstellung)) fehler("--darstellung muss einzelbild, lightbox oder slider sein");
const heute = new Date();
const datum = opt.datum || heute.toISOString().slice(0, 10);
if (!/^\d{4}-\d{2}-\d{2}$/.test(datum)) fehler("--datum im Format 2027-01-15");
const uhrzeit = `${String(heute.getHours()).padStart(2, "0")}:${String(heute.getMinutes()).padStart(2, "0")}`;

const slug = sichererName(opt.titel).replace(/\./g, "-").replace(/-+/g, "-").slice(0, 60);
const ordner = path.join("src", "posts", `${datum}-${slug}`);
if (fs.existsSync(ordner)) fehler(`Ordner ${ordner} gibt es schon`);
fs.mkdirSync(ordner, { recursive: true });

const bilder = [];
for (const d of dateien) {
  if (!fs.existsSync(d)) fehler(`Bild ${d} nicht gefunden`);
  const name = await verkleinere(d, ordner);
  bilder.push(name);
}

const yamlStr = (s) => JSON.stringify(String(s));   // sicher für : und Anführungszeichen
let fm = `---\ntitel: ${yamlStr(opt.titel)}\nunterzeile: ${yamlStr(opt.unterzeile)}\ndatum: ${datum} ${uhrzeit}\ndarstellung: ${darstellung}\nbilder:\n${bilder.map((b) => `- ${b}`).join("\n")}\n`;
if (opt.link) fm += `zusatzlink: ${yamlStr(opt.link)}\n`;
fm += "---\n\n";
const text = opt.text ? fs.readFileSync(opt.text, "utf8").trim() : "TEXT HIER EINFÜGEN";
fs.writeFileSync(path.join(ordner, "index.md"), fm + text + "\n");
console.log(`Beitrag angelegt: ${ordner}/index.md\nBilder: ${bilder.join(", ")}`);
