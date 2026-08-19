"""Koordinaten-/Feld-Mapping für das Original-Formular
`Schadenmeldeformular_RRV_Vorlage.pdf`, Abschnitt "Ärztliche Bescheinigung"
(Seiten 5 und 6, 1-indiziert / Seitenindex 4 und 5).

Das Formular enthält echte AcroForm-Felder. Die Namen wurden per pypdf
(`PdfReader.get_fields()` und Analyse der Annotationen je Seite) ermittelt
und über die (x, y)-Koordinaten den sichtbaren Label-Texten zugeordnet.

Seitenindizes (0-basiert, `reader.pages[i]`):
    4 -> Formularseite 5 ("A. Krankheit/Unfall", "1. Krankheit/Unfall",
         "2. Stationäre Behandlung")
    5 -> Formularseite 6 ("3. Vorerkrankungen", "4. Ihre Einschätzung",
         "B. Schwangerschaft", Fußbereich)
"""

SEITE_KRANKHEIT = 4  # Formularseite 5
SEITE_SCHWANGERSCHAFT = 5  # Formularseite 6

# --- Textfelder: logischer Schlüssel -> PDF-Feldname ------------------------
TEXT_FELDER = {
    # Kopfbereich (Seite 5)
    "mgl_nr": "60",
    "name_vorname": "61",
    "geburtsdatum": "62",
    "strasse": "63",
    "plz_ort": "64",
    # A.1 Krankheit/Unfall (Seite 5)
    "diagnose": "65",
    "datum_diagnosestellung": "66",
    "datum_erster_arztbesuch": "67",
    "therapie": "70",
    "ueberweisung_wann": "72",
    "ueberweisung_an_wen": "73",
    "au_von": "74a",
    "au_bis": "74b",
    # A.2 Stationäre Behandlung (Seite 5)
    "klinik_von": "75",
    "klinik_bis": "76",
    "klinikname": "77",
    "einweisender_arzt": "78",
    # 3. Vorerkrankungen (Seite 6)
    "vorerkrankungen_seit_wann": "80",
    "vorerkrankungen_diagnose": "81",
    # 4. Ihre Einschätzung (Seite 6)
    "einschaetzung_datum_zumutbar": "87",
    "einschaetzung_datum_moeglich": "88",
    # B. Schwangerschaft (Seite 6)
    "schwangerschaft_festgestellt_datum": "90",
    "schwangerschaft_ssw_datum": "91",
    "schwangerschaft_ssw": "92",
    "schwangerschaft_nicht_zumutbar_datum": "93",
    "schwangerschaft_grund": "94",
    # Fußbereich (Seite 6)
    "bescheinigung_datum": "97",
    "bescheinigung_ort": "98",
}

# --- Checkbox-/Radiofelder: logischer Schlüssel -> (PDF-Feldname, on-Werte) --
# Jedes Radiofeld hat zwei Kid-Widgets mit Exportwerten "/1" (linke Option)
# und "/2" (rechte Option). Bei Feld 7/8/8b/9/10/11/12/14 ist die Reihenfolge
# Ja="/1", Nein="/2". Feld 13 ist eine Sonderform: "/1" = "nicht zumutbar",
# "/2" = "bzw. nicht möglich".
CHECKBOX_FELDER = {
    "reisefaehigkeit": {"feld": "Feld 7", "ja": "/1", "nein": "/2"},
    "facharzt_ueberweisung": {"feld": "Feld 8", "ja": "/1", "nein": "/2"},
    "arbeitsunfaehigkeit": {"feld": "Feld 8b", "ja": "/1", "nein": "/2"},
    "stationaer": {"feld": "Feld 9", "ja": "/1", "nein": "/2"},
    "vorerkrankungen": {"feld": "Feld 10", "ja": "/1", "nein": "/2"},
    "vor_reisebuchung_gefragt": {"feld": "Feld 11", "ja": "/1", "nein": "/2"},
    "bedenken_reisebuchung": {"feld": "Feld 12", "ja": "/1", "nein": "/2"},
    "einschaetzung_variante": {
        "feld": "Feld 13",
        "zumutbar": "/1",
        "moeglich": "/2",
    },
    "schwangerschaft_komplikationen": {"feld": "Feld 14", "ja": "/1", "nein": "/2"},
}

# Für den "Stempel des Arztes/der Ärztin"-Kasten existiert kein AcroForm-Feld
# (nur eine gedruckte Box für einen echten Praxisstempel). Diese Fläche wird
# per Koordinaten-Overlay befüllt. Rect in PDF-Punkten (Ursprung unten links),
# ermittelt über die Vektor-Rechtecke der Seite 6.
STEMPEL_BOX = {"seite": SEITE_SCHWANGERSCHAFT, "x0": 300.5, "x1": 536.0, "y_top": 104.0}
