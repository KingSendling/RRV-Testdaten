"""Koordinaten-/Feld-Mapping für das Original-Formular
`Schadenmeldeformular_RRV_Vorlage.pdf`.

Das Formular enthält echte AcroForm-Felder. Die Namen wurden per pypdf
(`PdfReader.get_fields()` und Analyse der Annotationen je Seite) ermittelt
und über die (x, y)-Koordinaten den sichtbaren Label-Texten zugeordnet.

Seitenindizes (0-basiert, `reader.pages[i]`):
    0 -> Formularseite 1 ("1. Persönliche Angaben", "2. Angaben zur Reise",
         "3. Stornierungs-, Abbruchs- oder Unterbrechungsgrund")
    1 -> Formularseite 2 ("4. Reiseteilnehmer", "5. Versicherungsinformation",
         "6. Angaben zur Kontoverbindung", Beginn "7. Schlusserklärung")
    2 -> Formularseite 3 (Einwilligungs-/Schweigepflichtentbindungstext,
         Möglichkeit I/II)
    3 -> Formularseite 4 (Fortsetzung Einwilligungstext, Unterschriften,
         beigefügte Unterlagen)
    4 -> Formularseite 5 ("A. Krankheit/Unfall", "1. Krankheit/Unfall",
         "2. Stationäre Behandlung")
    5 -> Formularseite 6 ("3. Vorerkrankungen", "4. Ihre Einschätzung",
         "B. Schwangerschaft", Fußbereich)
"""

SEITE_SCHADENMELDUNG = (0, 1, 2, 3)  # Formularseiten 1-4
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


# =============================================================================
# Schadenmeldung (Seiten 1-4)
# =============================================================================

# Feld "60" (ADAC Mitglieds-/Kundennummer) ist dasselbe Feld wie in
# TEXT_FELDER oben (Seite 1 und Seite 5 zeigen denselben Formularwert an).
TEXT_FELDER_SCHADENMELDUNG = {
    # Kopfbereich (Seite 1)
    "mgl_nr": "60",
    # 1. Persönliche Angaben (Seite 1)
    "name_vorname_versicherungsnehmer": "2",
    "strasse": "3",
    "plz_ort": "4",
    "telefon": "5",
    # 2. Angaben zur Reise (Seite 1)
    "reiseveranstalter": "7",
    "reisebuero": "8",
    "reiseziel": "9",
    "gebucht_am": "10",
    "storniert_am": "11",
    "beginn_der_reise": "12",
    "geplante_rueckreise": "13",
    "reiseabbruch_am": "14",
    # 3. Stornierungsgrund (Seite 1)
    "versicherungsfall_datum": "16",
    "stornierungsgrund_freitext": "21",
    "betroffene_person": "22",
    # 4. Reiseteilnehmer (Seite 2) - Teilnehmer 1
    "teilnehmer1_name": "29",
    "teilnehmer1_geburtsdatum": "30",
    "teilnehmer1_anschrift": "31",
    "teilnehmer1_mgl_nr": "32",
    # 5. Versicherungsinformation (Seite 2)
    "gesamtreisepreis": "41",
    "erstattungsbetrag": "42",
    "versicherungsgesellschaft": "46",
    "versicherungsschein_nr": "47",
    "art_der_versicherung": "48",
    # 6. Kontoverbindung (Seite 2)
    "iban": "49",
    "bic": "50",
    "name_kreditinstitut": "51",
    "name_kontoinhaber": "52",
    "konto_datum": "53",
    "konto_ort": "54",
    # 7. Schlusserklärung (Seite 4)
    "erklaerender_name": "116A",
    "erklaerender_datum": "117A",
    "erklaerender_ort": "117B",
    "schluss_datum": "56",
    "schluss_ort": "57",
}

# logischer Schlüssel -> (PDF-Feldname, on-Werte). Feld 15/25/27/43/44 folgen
# dem Muster "/1" = erste Option, "/2" = zweite Option.
CHECKBOX_FELDER_SCHADENMELDUNG = {
    "reise_dienstlich_beruflich": {"feld": "15", "dienstlich": "/1", "beruflich": "/2"},
    "verwandt_mit_teilnehmern": {"feld": "25", "ja": "/1", "nein": "/2"},
    "ausgeloest_durch_dritte": {"feld": "27", "ja": "/1", "nein": "/2"},
    "andere_versicherung_vorhanden": {"feld": "43", "ja": "/1", "nein": "/2"},
    "bereits_gemeldet": {"feld": "44", "ja": "/1", "nein": "/2"},
    # Einwilligungserklärung Seite 3: "Ja" = Möglichkeit I (pauschal),
    # "Nein" = Möglichkeit II (Einzelfall).
    "einwilligung_variante": {"feld": "M1", "moeglichkeit_1": "/Ja", "moeglichkeit_2": "/Nein"},
    # Beigefügte Unterlagen Seite 4, jeweils eigenständige Checkboxen (nur "/Ja").
    "unterlagen_kostenbelege": {"feld": "118", "ja": "/Ja"},
    "unterlagen_sonstiges": {"feld": "119", "ja": "/Ja"},
    "unterlagen_schweigepflichtsentbindung": {"feld": "120", "ja": "/Ja"},
}

# Stornierungsgrund-Kategorien (Feld 17, Seite 1) -> Exportwert "/1".."/9".
STORNIERUNGSGRUND_FELD = "17"
STORNIERUNGSGRUND_EXPORTWERTE = {
    "Unerwartete, schwere Erkrankung": "/1",
    "Unfall": "/2",
    "Schwangerschaft": "/3",
    "Tod": "/4",
    "Impfunverträglichkeit": "/5",
    "Änderung Arbeitssituation": "/6",
    "Elementarereignisse": "/7",
    "Strafbare Handlung Dritter": "/8",
    "Sonstiges": "/9",
}
