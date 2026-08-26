"""Erzeugt das Prozess-/Dokumenteneingangs-JSON für das Omnia-Zielsystem.

Deckt die kombinierte Scan-Übermittlung mehrerer Dokumente ab (Schadenmeldung,
Ärztliche Bescheinigung, Buchungsbestätigung, Storno-Rechnung), abgeleitet aus
zwei Beispiel-Payloads: einer E-Mail-Einreichung mit nur der Schadenmeldung
und einer Post-Einreichung mit allen vier Dokumenten kombiniert.

ProcessID, inputDate und scanDate sind system-/zeitpunktabhängige Werte, die
nicht automatisch bekannt sein können und daher vom Nutzer manuell
eingetragen werden (leerer String, falls noch nicht gesetzt).
"""

from __future__ import annotations

import re

from utils.fake_data import FallDaten

# Dokumenttyp-Code -> (Label für den Seiten-Kommentar, feste Seitenzahl).
# Alle vier Generatoren erzeugen strukturell immer dieselbe Seitenzahl.
DOKUMENT_TYPEN_INFO: dict[str, tuple[str, int]] = {
    "SMF": ("Schadenmeldeformular", 4),
    "AEB": ("Ärztliche Bescheinigung", 2),
    "REISEBU": ("Buchungsbestätigung", 1),
    "STORNO-RE": ("Stornorechnung", 1),
}

# Eingangskanal bestimmt scanType/medium/recipientAddressType sowie ob
# sender/receiver gesetzt sind (bei Post-Einreichung gibt es keine E-Mail-
# Absender-/Empfängeradresse) - abgeleitet aus dem Vergleich der beiden
# Beispiel-Payloads (E-Mail vs. Post).
EINGANGSKANAELE: dict[str, dict[str, str]] = {
    "E-Mail": {"scanType": "F", "medium": "M", "recipientAddressType": "EMAIL"},
    "Post": {"scanType": "N", "medium": "P", "recipientAddressType": "POSTANSCHRIFT"},
}

COVERAGE_PACKAGES = ["RK-KOMFORT-EUROPA", "RK-PLUS-EUROPA"]


def normiere_mgl_nr(mgl_nr: str) -> str:
    """Extrahiert die reine 9-stellige numerische Mitgliedsnummer (Omnia
    erwartet rein numerisch ohne führenden Buchstaben, z.B. '010861268'),
    unabhängig vom Anzeigeformat in der App (z.B. 'A123456789')."""
    ziffern = re.sub(r"\D", "", mgl_nr)
    return ziffern[-9:].zfill(9) if ziffern else ""


def _baue_dokumente(mgl_nr_norm: str, dokument_typen: list[str]) -> tuple[list[dict], int]:
    """Baut die 'documents'-Liste mit fortlaufenden Seitenbereichen über
    alle gewählten Dokumenttypen hinweg (Reihenfolge = Reihenfolge der
    übergebenen Liste). Gibt (documents, Gesamtseitenzahl) zurück."""
    dokumente = []
    seite_offset = 0
    for typ in dokument_typen:
        info = DOKUMENT_TYPEN_INFO.get(typ)
        if info is None:
            continue
        label, seitenzahl = info
        external_document_id = f"{typ}-{mgl_nr_norm}-KOMBI-01"
        seiten = [
            {
                "externalPageId": f"{external_document_id}-P{seite:02d}",
                "pageNumber": seite,
                "rotation": 0,
                "comment": f"{label} Seite {seite}",
            }
            for seite in range(1, seitenzahl + 1)
        ]
        dokumente.append(
            {
                "sourcePdfPageFrom": seite_offset + 1,
                "sourcePdfPageTo": seite_offset + seitenzahl,
                "documentType": typ,
                "externalDocumentId": external_document_id,
                "pages": seiten,
            }
        )
        seite_offset += seitenzahl
    return dokumente, seite_offset


def baue_prozess_json(
    fall: FallDaten,
    dokument_typen: list[str],
    external_ref_id: str,
    process_id: str,
    input_date: str,
    scan_date: str,
    eingangskanal: str,
    ereignisland: str,
    coverage_package: str,
) -> dict:
    event_datum_raw = fall.ereignisdatum.strftime("%Y.%m.%d")
    mgl_nr_norm = normiere_mgl_nr(fall.mgl_nr)
    kanal = EINGANGSKANAELE.get(eingangskanal, EINGANGSKANAELE["E-Mail"])
    ist_email = eingangskanal == "E-Mail"
    ereignisland_code = (ereignisland or "DE").strip().upper()[:2]

    dokumente, gesamt_seiten = _baue_dokumente(mgl_nr_norm, dokument_typen)

    return {
        "processId": process_id,
        "process": {
            "sourceSystem": "Omnia",
            "externalRefId": external_ref_id,
            "inputDate": input_date,
            "scanType": kanal["scanType"],
            "scanDate": scan_date,
            "medium": kanal["medium"],
            "sender": fall.email if ist_email else None,
            "receiver": "schadenservice@versicherer.de" if ist_email else None,
            "mglNr": mgl_nr_norm,
            "refNr": None,
            "priority": "0",
            "eventDateRaw": event_datum_raw,
            "recipientAddressType": kanal["recipientAddressType"],
            "inboundOutboundIndicator": "E",
            "caseNumber": None,
            "caseEventDateRaw": event_datum_raw,
            "caseEventType": "402",
            "caseEventCountry": ereignisland_code,
            "claimNumber": None,
            "claimEventDateRaw": event_datum_raw,
            "claimEventType": "702",
            "claimEventCountry": ereignisland_code,
            "productGom1": "Reiserücktritts-Versicherung",
            "claimPolicyGom2": "Reiserücktritts-Versicherung",
            "policyNumberGom2": None,
            "coveragePackage": coverage_package,
            "elvGom3": "Rücktritt",
        },
        "sourcePdfMetadata": {"pageCount": gesamt_seiten},
        "documents": dokumente,
    }


# --- OSM-JSON (Online-Schadenmeldung, strukturierte Fallangaben) -------------

# fall.stornierungsgrund_kategorie ist einer der 9 Werte aus
# STORNIERUNGSGRUND_KATEGORIEN in utils/fake_data.py - für die aktuellen
# KRANKHEITEN_VORSCHLAEGE kommen davon aber nur diese drei tatsächlich vor.
OSM_STORNIERUNGSGRUND_MAPPING: dict[str, str] = {
    "Unerwartete, schwere Erkrankung": "Krankheit",
    "Unfall": "Unfall",
    "Schwangerschaft": "Schwangerschaft",
}

OSM_VERWANDTSCHAFTSGRADE = ["Partner", "Kinder", "Eltern", "Sonstige Verwandte"]


def _splitte_strasse(strasse: str) -> tuple[str, str]:
    """Trennt 'Musterstr. 12' in ('Musterstr.', '12')."""
    teile = strasse.rsplit(" ", 1)
    if len(teile) == 2:
        return teile[0], teile[1]
    return strasse, ""


def _splitte_plz_ort(plz_ort: str) -> tuple[str, str]:
    """Trennt '12345 Musterstadt' in ('12345', 'Musterstadt')."""
    teile = plz_ort.split(" ", 1)
    if len(teile) == 2:
        return teile[0], teile[1]
    return "", plz_ort


def baue_osm_json(fall: FallDaten, external_document_id: str, process_id: str, rng, fake) -> dict:
    """Baut das OSM-JSON (strukturierte Online-Schadenmeldung-Daten) für das
    Omnia-Zielsystem. Die Ärztliche-Bescheinigung-/Schadenmeldung-Generatoren
    dieser App modellieren die erkrankte Person immer als die Versicherungs-
    nehmerin/den Versicherungsnehmer selbst (kein separates Datenmodell für
    "erkrankter Angehöriger") - 'damageCausingPerson' entspricht daher hier
    bewusst der Person aus 'policyHolder'. Mitreisende (Feld 'participants')
    sind in `fall.teilnehmer_zusatz` nur als Anzahl/Text hinterlegt, nicht als
    einzelne Personen - für sie werden daher zur Anzeige passende fiktive
    Namen/Geburtsdaten erzeugt."""
    strasse, hausnummer = _splitte_strasse(fall.strasse)
    plz, ort = _splitte_plz_ort(fall.plz_ort)

    anzahl_mitreisende_match = re.search(r"\+\s*(\d+)\s*weitere", fall.teilnehmer_zusatz)
    anzahl_mitreisende = int(anzahl_mitreisende_match.group(1)) if anzahl_mitreisende_match else 0
    participants = [
        {
            "givenName": fake.first_name(),
            "surName": fall.name,
            "kinship": [rng.choice(OSM_VERWANDTSCHAFTSGRADE)],
            "dateOfBirth": fake.date_of_birth(minimum_age=1, maximum_age=80).isoformat(),
        }
        for _ in range(anzahl_mitreisende)
    ]

    return {
        "processId": process_id,
        "externalDocumentId": external_document_id,
        "policyHolder": {
            "givenName": fall.vorname,
            "surName": fall.name,
            "email": fall.email,
            "address": {
                "street": strasse,
                "houseNumber": hausnummer,
                "zipCode": plz,
                "city": ort,
            },
        },
        "damageCausingPerson": {
            "givenName": fall.vorname,
            "surName": fall.name,
            "kinship": ["Ich selbst"],
        },
        "reasonForCancellation": [
            OSM_STORNIERUNGSGRUND_MAPPING.get(fall.stornierungsgrund_kategorie, "Sonstiges")
        ],
        "cancellationDate": fall.stornodatum.isoformat(),
        "interruptionDate": fall.stornodatum.isoformat(),
        "isBusinessTrip": False,
        "participants": participants,
        "hasAdditionalInsurance": False,
        "bankAccount": {
            "iban": fall.iban,
            "accountHolder": [{"givenName": fall.vorname, "surName": fall.name}],
        },
        "isResubmission": False,
    }
