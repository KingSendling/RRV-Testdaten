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
2. Gewünschte Dokumenttypen auswählen (Rechnung, Buchungsbestätigung, Storno, Ärztliche Bescheinigung).
3. Optional: "Neuen Zufallsfall generieren" würfelt alle Zusatzfelder (Anbieter,
   Rechnungsnummern, Beträge, Arztname …) neu, ohne die oben gesetzten
   Kernfelder zu verändern.
4. "Dokumente generieren" klicken und die PDFs einzeln oder als ZIP herunterladen.

## Projektstruktur

```
app.py                              Streamlit-Einstiegspunkt
assets/                             Original-ADAC-Formularvorlage
data/providers.py                   Fiktive Reiseanbieter (Namen, Farben, Layout-Varianten)
data/field_mapping.py               AcroForm-Feldnamen der Ärztlichen Bescheinigung
generators/rechnung.py              Rechnung
generators/buchungsbestaetigung.py  Buchungsbestätigung
generators/storno.py                Storno-Rechnung
generators/aerztliche_bescheinigung.py  Ärztliche Bescheinigung (AcroForm-Fill)
utils/fake_data.py                  Falldaten-Modell, IBAN-Generator, Datumslogik
utils/pdf_helpers.py                Gemeinsame PDF-Bausteine (Wasserzeichen, Layouts)
```

## Hinweise

- Kein echter Upload/Integration in Camunda – Dokumente werden lokal heruntergeladen.
- Keine Persistierung – die App ist zustandslos pro Streamlit-Session.
- Alle PDFs tragen ein "TESTDOKUMENT – fiktive Daten"-Wasserzeichen.
