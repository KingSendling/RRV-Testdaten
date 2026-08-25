# Schadenschmiede

Interne Streamlit-App zur Erzeugung synthetischer Testdokumente für den
Camunda-Prozess der Reiserücktrittsversicherung (RRV). Alle erzeugten Daten
sind frei erfunden und ausschließlich für Testzwecke gedacht.

## Design

Helles, ruhiges Erscheinungsbild mit ADAC-Gelb (`#FFCC00`) als einziger
Akzentfarbe für primäre Buttons, Checkbox-Häkchen und Eingabefokus. Schrift
ist die Systemschrift (`-apple-system`/SF Pro auf Mac/iPhone), mit "Inter"
als Web-Font-Fallback auf anderen Geräten, damit es überall nach Apple-Design
aussieht statt nur auf Apple-Geräten. Konfiguriert über
[.streamlit/config.toml](.streamlit/config.toml) (Grundfarben) und
zusätzliches CSS in `app.py` (Schrift, Rundungen, Schatten).

Das Logo (Amboss trägt ein Dokument mit geknickter Ecke) ist als Inline-SVG
in `_logo_svg()`/`_logo_lockup()` in `app.py` umgesetzt und bildet die
Kopfzeile sowie den Login-Bildschirm.

## Setup

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\streamlit run app.py
```

## Verwendung

0. Optional: "Teilprozess (TP)" und "Testfall (TF)" oben ausfüllen, damit alle
   erzeugten Dateinamen mit z. B. `TP10_TF01_` beginnen (nützlich, um
   Testläufe eindeutig zuzuordnen). Leer lassen für die Standard-Dateinamen.
1. Falldaten in der Eingabemaske ausfüllen (Krankheit, Name, Adresse, Daten, IBAN …).
2. Gewünschte Dokumenttypen auswählen (Rechnung, Buchungsbestätigung, Storno,
   Ärztliche Bescheinigung, Schadenmeldung (Formular), Online-Schadenmeldung).
3. Reiseanbieter auswählen (gilt für Rechnung, Buchungsbestätigung & Storno).
4. Optional: "Neuen Zufallsfall generieren" würfelt alle Zusatzfelder
   (Rechnungsnummern, Beträge, Arztname …) neu, ohne die oben gesetzten
   Kernfelder oder den gewählten Anbieter zu verändern.
5. "Dokumente generieren" klicken und die PDFs einzeln, als ZIP oder als ein
   zusammengefügtes Gesamt-PDF herunterladen. Ein Deckblatt mit allen
   Falldaten wird automatisch mitgeneriert.

## Testperson vorausfüllen

Über "👤 Testperson aus Liste vorausfüllen" oben in der App lässt sich Mgl.-Nr.,
Name, Vorname, Geburtsdatum und Adresse mit einer von 116 vordefinierten
Testpersonen aus dem internen Testdatensatz (`data/testpersonen.py`, erzeugt
aus `TEST_DATA_INT3.xlsx`, Reiter "Extra-Daten") vorausfüllen. Krankheit,
Termine und IBAN bleiben dabei unverändert.

## Testfall wiederholen

Beim Generieren wird zusätzlich eine JSON-Datei mit allen Falldaten zum
Download angeboten ("Fall als JSON exportieren"). Über "📂 Bestehenden
Testfall wiederholen" oben in der App lässt sich diese Datei später wieder
hochladen: Alle Zufallsdaten (Name, IBAN, Diagnosetext, Beträge, Anbieter …)
bleiben dabei exakt identisch, nur ein neues Ereignisdatum wird eingegeben –
alle anderen Datumsfelder (Storno, Reisezeitraum, Buchung, AU-Zeitraum …)
verschieben sich automatisch um denselben Abstand mit, damit der Testfall
zeitlich schlüssig bleibt. Das Geburtsdatum ändert sich nicht.

## Prozess-JSON (Omnia)

Nach dem Generieren zeigt Abschnitt "6. Prozess-JSON (Omnia)" ein kopierbares
JSON mit den Dokumenteneingangs-Metadaten für die kombinierte Scan-
Übermittlung aller passenden gewählten Dokumente – erkannt werden
Schadenmeldung (Formular, `SMF`, 4 Seiten), Ärztliche Bescheinigung (`AEB`,
2 Seiten), Buchungsbestätigung (`REISEBU`, 1 Seite) und Storno-Rechnung
(`STORNO-RE`, 1 Seite); `sourcePdfMetadata.pageCount` und die Seitenbereiche
in `documents[]` ergeben sich automatisch aus der Auswahl in Abschnitt 2
(Rechnung und Online-Schadenmeldung haben keinen bekannten Dokumenttyp-Code
und tauchen daher nicht auf). `mglNr` wird auf 9-stellig numerisch normiert.

`externalRefId` wird zufällig vorbelegt, lässt sich aber jederzeit manuell
überschreiben oder per "🎲 Neu" neu auswürfeln (`externalDocumentId`/
`externalPageId` je Dokument werden deterministisch aus Mitgliedsnummer und
Dokumenttyp abgeleitet, Schema `{TYP}-{mglNr}-KOMBI-01[-P0N]`).
`processId`, `inputDate` und `scanDate` sind system-/zeitpunktabhängige
Werte und müssen manuell eingetragen werden. Zusätzlich wählbar: der
**Eingangskanal** (E-Mail oder Post – steuert `scanType`/`medium`/
`recipientAddressType` sowie ob `sender`/`receiver` gesetzt sind), das
**Ereignisland** (`caseEventCountry`/`claimEventCountry`) und das
**Tarifpaket** (`coveragePackage`, mit Freitext-Option).

## Datumslogik

Das Buchungsdatum liegt immer vor oder am selben Tag wie das Stornodatum
UND vor dem Reisebeginn (sonst würde der Camunda-Prozess den Testfall
aussteuern) – das wird sowohl
bei der Zufallsgenerierung sichergestellt als auch unmittelbar vor dem
Erzeugen der Dokumente noch einmal automatisch korrigiert, falls das
Stornodatum manuell davor verschoben wurde.

## Projektstruktur

```
app.py                              Streamlit-Einstiegspunkt
assets/                             Original-ADAC-Formularvorlage
data/providers.py                   Fiktive Reiseanbieter (Namen, Farben, Layout-Varianten)
data/field_mapping.py               AcroForm-Feldnamen der Ärztlichen Bescheinigung & Schadenmeldung
data/testpersonen.py                116 vordefinierte Testpersonen (Mgl.-Nr., Name, Geburtsdatum, Adresse)
generators/rechnung.py              Rechnung
generators/buchungsbestaetigung.py  Buchungsbestätigung
generators/storno.py                Storno-Rechnung
generators/aerztliche_bescheinigung.py  Ärztliche Bescheinigung (AcroForm-Fill, Seiten 5-6)
generators/schadenmeldung.py        Schadenmeldung (AcroForm-Fill, Seiten 1-4 derselben Vorlage)
generators/online_schadenmeldung.py Online-Schadenmeldung (angelehnt an das ADAC-Online-Formular)
generators/deckblatt.py             Deckblatt mit Fallübersicht
utils/fake_data.py                  Falldaten-Modell, IBAN-Generator, Datumslogik
utils/pdf_helpers.py                Gemeinsame PDF-Bausteine (Wasserzeichen, Layouts)
utils/prozess_json.py               Prozess-/Dokumenteneingangs-JSON für das Omnia-Zielsystem
```

## Hinweise

- Kein echter Upload/Integration in Camunda – Dokumente werden lokal heruntergeladen.
- Keine Persistierung – die App ist zustandslos pro Streamlit-Session.
- Alle PDFs tragen ein "TESTDOKUMENT – fiktive Daten"-Wasserzeichen.
