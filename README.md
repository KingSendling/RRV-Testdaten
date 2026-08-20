# RRV Testdokumente Generator

Interne Streamlit-App zur Erzeugung synthetischer Testdokumente für den
Camunda-Prozess der Reiserücktrittsversicherung (RRV). Alle erzeugten Daten
sind frei erfunden und ausschließlich für Testzwecke gedacht.

## Setup

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\streamlit run app.py
```

## Verwendung

1. Falldaten in der Eingabemaske ausfüllen (Krankheit, Name, Adresse, Daten, IBAN …).
2. Gewünschte Dokumenttypen auswählen (Rechnung, Buchungsbestätigung, Storno,
   Ärztliche Bescheinigung, Schadenmeldung (Formular), Online-Schadenmeldung).
3. Reiseanbieter auswählen (gilt für Rechnung, Buchungsbestätigung & Storno).
4. Optional: "Neuen Zufallsfall generieren" würfelt alle Zusatzfelder
   (Rechnungsnummern, Beträge, Arztname …) neu, ohne die oben gesetzten
   Kernfelder oder den gewählten Anbieter zu verändern.
5. "Dokumente generieren" klicken und die PDFs einzeln oder als ZIP
   herunterladen. Ein Deckblatt mit allen Falldaten wird automatisch
   mitgeneriert.

## Projektstruktur

```
app.py                              Streamlit-Einstiegspunkt
assets/                             Original-ADAC-Formularvorlage
data/providers.py                   Fiktive Reiseanbieter (Namen, Farben, Layout-Varianten)
data/field_mapping.py               AcroForm-Feldnamen der Ärztlichen Bescheinigung & Schadenmeldung
generators/rechnung.py              Rechnung
generators/buchungsbestaetigung.py  Buchungsbestätigung
generators/storno.py                Storno-Rechnung
generators/aerztliche_bescheinigung.py  Ärztliche Bescheinigung (AcroForm-Fill, Seiten 5-6)
generators/schadenmeldung.py        Schadenmeldung (AcroForm-Fill, Seiten 1-4 derselben Vorlage)
generators/online_schadenmeldung.py Online-Schadenmeldung (angelehnt an das ADAC-Online-Formular)
generators/deckblatt.py             Deckblatt mit Fallübersicht
utils/fake_data.py                  Falldaten-Modell, IBAN-Generator, Datumslogik
utils/pdf_helpers.py                Gemeinsame PDF-Bausteine (Wasserzeichen, Layouts)
```

## Hinweise

- Kein echter Upload/Integration in Camunda – Dokumente werden lokal heruntergeladen.
- Keine Persistierung – die App ist zustandslos pro Streamlit-Session.
- Alle PDFs tragen ein "TESTDOKUMENT – fiktive Daten"-Wasserzeichen.
