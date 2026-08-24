"""Erzeugt das Prozess-/Dokumenteneingangs-JSON für das Omnia-Zielsystem,
passend zur "Schadenmeldung (Formular)" (4 Seiten, Dokumenttyp "SMF").

ProcessID, inputDate und scanDate sind system-/zeitpunktabhängige Werte, die
nicht automatisch bekannt sein können und daher vom Nutzer manuell
eingetragen werden (leerer String, falls noch nicht gesetzt).
"""

from __future__ import annotations

import re

from utils.fake_data import FallDaten

SMF_SEITENANZAHL = 4


def normiere_mgl_nr(mgl_nr: str) -> str:
    """Extrahiert die reine 9-stellige numerische Mitgliedsnummer (Omnia
    erwartet rein numerisch ohne führenden Buchstaben, z.B. '010861268'),
    unabhängig vom Anzeigeformat in der App (z.B. 'A123456789')."""
    ziffern = re.sub(r"\D", "", mgl_nr)
    return ziffern[-9:].zfill(9) if ziffern else ""


def baue_prozess_json(
    fall: FallDaten,
    external_ref_id: str,
    external_document_id: str,
    process_id: str,
    input_date: str,
    scan_date: str,
) -> dict:
    event_datum_raw = fall.ereignisdatum.strftime("%Y.%m.%d")

    seiten = [
        {
            "externalPageId": f"{external_document_id}-P{seite:02d}",
            "pageNumber": seite,
            "rotation": 0,
            "comment": "",
        }
        for seite in range(1, SMF_SEITENANZAHL + 1)
    ]

    return {
        "processId": process_id,
        "process": {
            "sourceSystem": "Omnia",
            "externalRefId": external_ref_id,
            "inputDate": input_date,
            "scanType": "F",
            "scanDate": scan_date,
            "medium": "M",
            "sender": fall.email,
            "receiver": "schadenservice@versicherer.de",
            "mglNr": normiere_mgl_nr(fall.mgl_nr),
            "refNr": None,
            "priority": "0",
            "eventDateRaw": event_datum_raw,
            "recipientAddressType": "EMAIL",
            "inboundOutboundIndicator": "E",
            "caseNumber": None,
            "caseEventDateRaw": event_datum_raw,
            "caseEventType": "402",
            "caseEventCountry": "DE",
            "claimNumber": None,
            "claimEventDateRaw": event_datum_raw,
            "claimEventType": "702",
            "claimEventCountry": "DE",
            "productGom1": "Reiserücktritts-Versicherung",
            "claimPolicyGom2": "Reiserücktritts-Versicherung",
            "policyNumberGom2": None,
            "coveragePackage": "RK-KOMFORT-EUROPA",
            "elvGom3": "Rücktritt",
        },
        "sourcePdfMetadata": {"pageCount": SMF_SEITENANZAHL},
        "documents": [
            {
                "sourcePdfPageFrom": 1,
                "sourcePdfPageTo": SMF_SEITENANZAHL,
                "documentType": "SMF",
                "externalDocumentId": external_document_id,
                "pages": seiten,
            }
        ],
    }
