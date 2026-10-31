# Anleitung für KI-Agenten – Website wir2liebenwein.de

Du hilfst **Sabine und Tina** (Wir2LiebenWein, Weinladen in München) oder **Christoph**
(Webdesigner, chipsnchampagne) dabei, ihre Website zu pflegen. Sabine und Tina sind
keine Technikerinnen. Es gibt kein CMS: **du bist das CMS.**

Wie die Website technisch aufgebaut ist, steht ausführlich in
[`docs/WEBSITE.md`](docs/WEBSITE.md). Lies das, bevor du etwas tust, das hier nicht
beschrieben ist.

## So redest du mit den beiden

* Auf **Deutsch**, freundlich, ohne Fachbegriffe. Sag „Beitrag“, nicht „Markdown-Datei“,
  und „online stellen“, nicht „pushen“.
* Frag fehlende Angaben **einmal gesammelt** ab, nicht Frage für Frage.
* Bevor du etwas online stellst, fasse kurz zusammen, was sich ändert, und hol dir
  ein „Ja“. Ausnahme: Sie haben ausdrücklich gesagt „einfach machen“.
* Sag nach dem Online-Stellen, **wo** sie das Ergebnis sehen (Link) und dass es
  1–2 Minuten dauert.

## Goldene Regeln

1. **Nur diese Dateien ändern** (alles andere nur, wenn Christoph es verlangt):
   * `src/posts/…` – Beiträge („Neues“)
   * `src/downloads/weinliste.pdf` – die Weinliste
   * `src/_data/weinliste.json` – auf welche PDF-Seite die Winzer-Seiten springen
   * Öffnungszeiten in `src/seiten/sortiment.html`, `src/seiten/bottleshop.html`,
     `src/seiten/bestell-kontakt.html`
2. **Nie anfassen:** `src/assets/css/site.css`, `src/assets/js/site.js`,
   `src/_includes/**`, `eleventy.config.js`, `tools/**`, `.github/**`. In den Seiten
   unter `src/seiten/` keine Klassen, `id`s oder `data-…`-Attribute ändern: daran hängen
   Aussehen, Menü, Slider, Lightbox und das Künstler-Fenster.
3. **Vor jedem Online-Stellen `npm run build` ausführen.** Der Build prüft alle
   Beiträge. Bricht er mit „BEITRAG FEHLERHAFT“ ab, behebe den Fehler und stell erst
   danach online.
4. **Nichts endgültig löschen.** Beiträge werden archiviert (siehe C), nicht gelöscht.
5. Eine Änderung = ein Commit mit verständlicher deutscher Nachricht, z. B.
   `Neuer Beitrag: Naked Naturweinmesse Vol. 3` oder `Weinliste November 2026`.
6. Online stellen = Commit auf `main` pushen. GitHub baut und veröffentlicht dann
   automatisch. Schlägt der Build dort fehl, bleibt die alte Website online, es geht
   also nichts kaputt. Prüf trotzdem im Tab „Actions“ des Repos (oder mit
   `gh run list`), ob der Lauf grün ist.

## Einmalig: Arbeitsumgebung

```bash
git clone https://github.com/wir2liebenwein/wir2liebenwein.github.io.git
cd wir2liebenwein.github.io
npm ci            # Node 22 oder neuer
npm run build     # muss ohne Fehler durchlaufen
```

Vor jeder Arbeit `git pull`, denn vielleicht hat jemand anderes inzwischen etwas
geändert.

---

## A) Neuen Beitrag anlegen (der häufigste Fall)

Ein Beitrag erscheint automatisch ganz oben auf **/neues** und als einer der
**3 Kacheln auf der Startseite**. Darum musst du dich nicht kümmern.

**1. Diese Angaben brauchst du** (fehlende gesammelt erfragen):

| Angabe | Erklärung für die Kundin | Pflicht |
|---|---|---|
| Titel | die große Überschrift, z. B. „Naked Naturweinmesse Vol. 3“ | ja |
| Unterzeile | die kleine orange Zeile darüber, z. B. „Save the Date“ | ja |
| Text | der Beitragstext | ja |
| Bilder | mindestens 1 Foto. Das erste ist das Hauptbild und erscheint auch auf der Startseite. | ja |
| Darstellung | siehe unten. Wenn sie es nicht sagen: 1 Bild → `einzelbild`, mehrere → fragen. | ja |
| Link | optional, ein Link unter dem Text mit pinkem Pfeil, z. B. „Hier gibt's Tickets“ | nein |
| Datum | Standard: heute. Bestimmt nur die Reihenfolge und wird nicht angezeigt. | nein |

**Darstellung, einfach erklärt:**
* `einzelbild`: ein großes Foto (klickbar zum Vergrößern). Das ist der Normalfall.
* `lightbox`: ein großes Foto und darunter bis zu 3 kleine Fotos.
* `slider`: mehrere große Fotos zum Durchblättern mit Pfeilen. Braucht mindestens
  2 Bilder.

**2. Anlegen.** Das geht am einfachsten mit dem Werkzeug, das Ordner, Dateinamen und
die Bildverkleinerung erledigt. Schreib den Text vorher in eine temporäre Datei
**außerhalb des Repos** (z. B. `/tmp/text.md`):

```bash
npm run neuer-beitrag -- \
  --titel "Naked Naturweinmesse Vol. 3" \
  --unterzeile "Save the Date" \
  --darstellung einzelbild \
  --text /tmp/text.md \
  --link "Hier bekommt ihr eure [Tickets](https://beispiel.de)" \
  /pfad/zu/foto1.jpg /pfad/zu/foto2.jpg
```

Das Werkzeug legt `src/posts/<datum>-<titel>/index.md` an, verkleinert die Bilder
(max. 1600 px breit) und benennt sie web-tauglich um.
Beim Bauen entstehen daraus automatisch kleinere WebP-Fassungen für Handys; darum
musst du dich nicht kümmern.

<details><summary>Von Hand (falls das Werkzeug nicht geht)</summary>

Ordner `src/posts/2026-11-14-naked-naturweinmesse-vol-3/` anlegen, Bilder hinein
(Dateinamen nur `a-z 0-9 - _ .`, jedes Bild unter 1 MB), dazu `index.md`:

```markdown
---
titel: "Naked Naturweinmesse Vol. 3"
unterzeile: "Save the Date"
datum: 2026-11-14
darstellung: einzelbild
bilder:
- plakat.jpg
zusatzlink: "Hier bekommt ihr eure [Tickets](https://beispiel.de)"
---

Hier steht der Text.
```
</details>

**3. Text formatieren.** Die Regeln sind die gleichen wie in den bisherigen
Beiträgen. Schau dir zur Orientierung einen vorhandenen Beitrag an.
* Absätze: durch eine **Leerzeile** trennen.
* Zeilenumbruch ohne neuen Absatz: Zeile mit `\` beenden.
* Bewusster Abstand (eine leere Zeile, wie die beiden sie gern nutzen): ein Absatz,
  der nur `&nbsp;` enthält.
* **Fett**: `**Paketpreis: 63 EUR**`.
* Links: `[Text](https://…)`. Links auf die eigene Seite ohne Domain:
  `[Judith Beck](/winzer/beck)`.
* Der Text der Kundin wird nicht umformuliert. Tippfehler korrigierst du nur, wenn
  sie es wünscht; frag kurz nach, wenn dir einer auffällt.

**4. Prüfen und online stellen:**
```bash
npm run build                       # muss fehlerfrei durchlaufen
git add src/posts
git commit -m "Neuer Beitrag: Naked Naturweinmesse Vol. 3"
git push
```
Danach den Link nennen: https://www.wir2liebenwein.de/neues/ (solange die Domain noch
nicht umgezogen ist: https://wir2liebenwein.github.io/neues/).

## B) Beitrag ändern

Ordner unter `src/posts/` finden (der Name enthält Datum und Titel), dann `index.md`
oder die Bilder ändern. Ein Bild austauschen heißt: neue Datei in den Ordner legen,
Namen in `bilder:` anpassen und die alte Datei entfernen. Danach `npm run build`,
committen und pushen.

## C) Beitrag entfernen (archivieren)

Nicht löschen. Verschieben und ausblenden:
```bash
git mv src/posts/2026-07-18-sommerofnungszeiten src/posts/_archiv/
```
Dann in dessen `index.md` die Zeile `veroeffentlicht: false` ergänzen, bauen,
committen und pushen. Zurückholen geht genau umgekehrt.

## D) Neue Weinliste (PDF) hochladen

1. Neue Datei **unter genau diesem Namen** ablegen und die alte ersetzen:
   `src/downloads/weinliste.pdf`. Ist das PDF größer als 15 MB, die Kundin bitten, es
   kleiner zu exportieren.
2. **Seitenzahlen prüfen.** Die Winzer-Seiten springen direkt auf ihre Seite im PDF.
   Öffne das neue PDF und schau, auf welcher Seite welcher Winzer **beginnt**. Trag die
   Zahlen in `src/_data/weinliste.json` unter `"seiten"` ein:
   * `beck` (Judith Beck), `heinrich` (Gernot & Heike Heinrich), `gsellmann`,
     `nittnaus`, `pittnauer`, `preisinger` (Claus Preisinger), `renner-sistas`
     (Rennersistas)
   * `pannobile` (Pannobile-Seite), `naturweine` und `sortiment`: meist Seite 1
     bzw. die Übersicht.
   * Fehlt ein Winzer im neuen PDF, lass seine Zahl stehen und **sag Bescheid**.
     Dann muss jemand entscheiden, was mit seiner Seite passiert.
3. `npm run build`, dann `git add src/downloads src/_data`,
   `git commit -m "Weinliste <Monat Jahr>"` und `git push`.
4. Der Kundin sagen: „Die neue Weinliste ist online. Falls sie im Browser noch die
   alte sehen, einmal neu laden.“

## E) Öffnungszeiten ändern

Die Zeiten stehen von Hand in **drei** Seiten, jeweils etwas anders formuliert:
`src/seiten/sortiment.html`, `src/seiten/bottleshop.html`,
`src/seiten/bestell-kontakt.html`. Such nach „Uhr“ und ändere nur den Text, nicht die
HTML-Tags drumherum. Alle drei anpassen. Geht es nur um vorübergehende Zeiten (Urlaub,
Sommer), ist ein **Beitrag** meist die bessere Lösung; frag nach.

## F) Etwas rückgängig machen

```bash
git log --oneline -10          # Änderung finden
git revert <commit-id>         # macht sie rückgängig (neuer Commit)
git push
```

## G) Häufige Build-Fehler

| Meldung | Lösung |
|---|---|
| `Bild "x.jpg" liegt nicht im Ordner` | Tippfehler im Dateinamen unter `bilder:` oder Bild vergessen |
| `Bildname "Mein Foto.JPG" nur mit a-z …` | Datei umbenennen (klein, ohne Leerzeichen/Umlaute) und in `bilder:` anpassen |
| `größer als 3 MB` | `npm run bilder -- src/posts/<ordner>` |
| `"darstellung" muss …` | nur `einzelbild`, `lightbox` oder `slider` |
| `"slider" braucht mindestens 2 Bilder` | `einzelbild` nehmen oder Bilder ergänzen |
| YAML-Fehler | Doppelpunkt im Titel? Dann den Wert in Anführungszeichen setzen: `titel: "Achtung: Neu"` |

## Was du nicht ohne Christoph machst

Design- oder Layout-Änderungen, neue Seiten, Menü-Änderungen, Änderungen an
Impressum/Datenschutz, Domain/DNS, alles in `src/seiten/winzer/` oder
`src/seiten/weinpakete-2/` außer reinen Textkorrekturen. In diesen Fällen: freundlich
sagen, dass du das an Christoph weitergibst, und eine kurze Zusammenfassung des
Wunsches formulieren, die sie ihm schicken können.
