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
