"""Generator für die Ärztliche Bescheinigung (Seiten 5-6 des Original-
ADAC-Formulars). Nutzt echte AcroForm-Felder der Vorlage; nur der
"Stempel des Arztes/der Ärztin"-Kasten hat kein Formularfeld und wird per
Koordinaten-Overlay befüllt.
"""

from __future__ import annotations

import io
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import HexColor
from reportlab.pdfgen.canvas import Canvas

from data.field_mapping import (
    CHECKBOX_FELDER,
    SEITE_KRANKHEIT,
    SEITE_SCHWANGERSCHAFT,
    STEMPEL_BOX,
    TEXT_FELDER,
)
from utils.fake_data import FallDaten
from utils.pdf_helpers import PAGE_H, PAGE_W, draw_diagonal_watermark, fmt_datum

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "assets" / "Schadenmeldeformular_RRV_Vorlage.pdf"


def _wrap_text(text: str, max_chars: int) -> list[str]:
    woerter = text.split()
    zeilen: list[str] = []
    aktuell = ""
    for wort in woerter:
        kandidat = (aktuell + " " + wort).strip()
        if len(kandidat) > max_chars and aktuell:
            zeilen.append(aktuell)
            aktuell = wort
        else:
            aktuell = kandidat
    if aktuell:
        zeilen.append(aktuell)
    return zeilen


def _stempel_overlay_pdf(fall: FallDaten) -> bytes:
    buf = io.BytesIO()
    c = Canvas(buf, pagesize=(PAGE_W, PAGE_H))
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(HexColor("#111111"))

    x = STEMPEL_BOX["x0"] + 6
    y = STEMPEL_BOX["y_top"] - 16
    zeilenhoehe = 10.5

    c.drawString(x, y, fall.arzt_name)
    y -= zeilenhoehe
    c.setFont("Helvetica", 7.5)

    adresstext = fall.praxisstempel_text
    for zeile in _wrap_text(adresstext, 44):
        c.drawString(x, y, zeile)
        y -= zeilenhoehe

    c.showPage()
    c.save()
    return buf.getvalue()


def _diagnose_mit_icd10(fall: FallDaten) -> str:
    """Das Formular hat kein eigenes Feld für den ICD-10-Code - er wird
    daher an den Diagnosetext angehängt."""
    if fall.icd10_code:
        return f"{fall.diagnose_text} (ICD-10: {fall.icd10_code})"
    return fall.diagnose_text


def _text_werte(fall: FallDaten) -> dict[str, dict[str, str]]:
    seite5: dict[str, str] = {
        TEXT_FELDER["mgl_nr"]: fall.mgl_nr,
        TEXT_FELDER["name_vorname"]: f"{fall.name}, {fall.vorname}",
        TEXT_FELDER["geburtsdatum"]: fmt_datum(fall.geburtsdatum),
        TEXT_FELDER["strasse"]: fall.strasse,
        TEXT_FELDER["plz_ort"]: fall.plz_ort,
        TEXT_FELDER["diagnose"]: _diagnose_mit_icd10(fall),
        TEXT_FELDER["datum_diagnosestellung"]: fmt_datum(fall.ereignisdatum),
        TEXT_FELDER["datum_erster_arztbesuch"]: fmt_datum(fall.erster_arztbesuch_datum),
        TEXT_FELDER["therapie"]: fall.therapie_text,
        TEXT_FELDER["au_von"]: fmt_datum(fall.au_von),
        TEXT_FELDER["au_bis"]: fmt_datum(fall.au_bis),
    }
    if fall.facharzt_ueberweisung:
        seite5[TEXT_FELDER["ueberweisung_wann"]] = fmt_datum(fall.ereignisdatum)
        seite5[TEXT_FELDER["ueberweisung_an_wen"]] = f"Facharztpraxis für {fall.facharzt_fachrichtung}"
    if fall.stationaer:
        seite5[TEXT_FELDER["klinik_von"]] = fmt_datum(fall.klinik_von)
        seite5[TEXT_FELDER["klinik_bis"]] = fmt_datum(fall.klinik_bis)
        seite5[TEXT_FELDER["klinikname"]] = fall.klinikname
        seite5[TEXT_FELDER["einweisender_arzt"]] = fall.arzt_name

    seite6: dict[str, str] = {
        TEXT_FELDER["einschaetzung_datum_zumutbar"]: fmt_datum(fall.ereignisdatum),
        TEXT_FELDER["bescheinigung_datum"]: fmt_datum(fall.bescheinigung_datum),
        TEXT_FELDER["bescheinigung_ort"]: fall.praxis_ort,
    }
    if fall.vorerkrankungen:
        seite6[TEXT_FELDER["vorerkrankungen_diagnose"]] = fall.vorerkrankungen_text

    if fall.ist_schwangerschaftsfall():
        seite6[TEXT_FELDER["schwangerschaft_festgestellt_datum"]] = fmt_datum(
            fall.ereignisdatum
        )
        seite6[TEXT_FELDER["schwangerschaft_nicht_zumutbar_datum"]] = fmt_datum(
            fall.ereignisdatum
        )
        seite6[TEXT_FELDER["schwangerschaft_grund"]] = (
            "Ärztlich festgestellte Risikoschwangerschaft mit angeordneter "
            "Schonung; Reiseantritt aus medizinischer Sicht nicht vertretbar."
        )

    return {"seite5": seite5, "seite6": seite6}


def _checkbox_werte(fall: FallDaten) -> dict[str, dict[str, str]]:
    def cb(key: str, ja: bool) -> tuple[str, str]:
        cfg = CHECKBOX_FELDER[key]
        return cfg["feld"], (cfg["ja"] if ja else cfg["nein"])

    seite5: dict[str, str] = {}
    for key, ja in [
        ("reisefaehigkeit", False),
        ("facharzt_ueberweisung", fall.facharzt_ueberweisung),
        ("arbeitsunfaehigkeit", True),
        ("stationaer", fall.stationaer),
    ]:
        feldname, wert = cb(key, ja)
        seite5[feldname] = wert

    seite6: dict[str, str] = {}
    for key, ja in [
        ("vorerkrankungen", fall.vorerkrankungen),
        ("vor_reisebuchung_gefragt", False),
        ("bedenken_reisebuchung", False),
    ]:
        feldname, wert = cb(key, ja)
        seite6[feldname] = wert
    seite6[CHECKBOX_FELDER["einschaetzung_variante"]["feld"]] = CHECKBOX_FELDER[
        "einschaetzung_variante"
    ]["zumutbar"]
    if fall.ist_schwangerschaftsfall():
        feldname, wert = cb("schwangerschaft_komplikationen", False)
        seite6[feldname] = wert

    return {"seite5": seite5, "seite6": seite6}


def erzeuge_aerztliche_bescheinigung(fall: FallDaten) -> bytes:
    reader = PdfReader(str(TEMPLATE_PATH))
    writer = PdfWriter()
    writer.append(reader)

    werte = _text_werte(fall)
    checkboxen = _checkbox_werte(fall)

    writer.update_page_form_field_values(
        writer.pages[SEITE_KRANKHEIT],
        {**werte["seite5"], **checkboxen["seite5"]},
    )
    writer.update_page_form_field_values(
        writer.pages[SEITE_SCHWANGERSCHAFT],
        {**werte["seite6"], **checkboxen["seite6"]},
    )
    writer.set_need_appearances_writer(True)

    stempel_overlay = PdfReader(io.BytesIO(_stempel_overlay_pdf(fall)))
    writer.pages[SEITE_SCHWANGERSCHAFT].merge_page(stempel_overlay.pages[0])

    watermark_pdf = io.BytesIO()
    wc = Canvas(watermark_pdf, pagesize=(PAGE_W, PAGE_H))
    draw_diagonal_watermark(wc)
    wc.showPage()
    draw_diagonal_watermark(wc)
    wc.showPage()
    wc.save()
    watermark_reader = PdfReader(io.BytesIO(watermark_pdf.getvalue()))
    writer.pages[SEITE_KRANKHEIT].merge_page(watermark_reader.pages[0])
    writer.pages[SEITE_SCHWANGERSCHAFT].merge_page(watermark_reader.pages[1])

    out_writer = PdfWriter()
    out_writer.append(writer, pages=(SEITE_KRANKHEIT, SEITE_SCHWANGERSCHAFT + 1))

    buf = io.BytesIO()
    out_writer.write(buf)
    return buf.getvalue()
