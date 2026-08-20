"""Generator für die Schadenmeldung (Seiten 1-4 des Original-ADAC-Formulars).
Nutzt dieselben echten AcroForm-Felder wie die Ärztliche Bescheinigung
(gleiche Vorlage, unterschiedlicher Seitenbereich)."""

from __future__ import annotations

import io
from datetime import date
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas

from data.field_mapping import (
    CHECKBOX_FELDER_SCHADENMELDUNG,
    SEITE_SCHADENMELDUNG,
    STORNIERUNGSGRUND_EXPORTWERTE,
    STORNIERUNGSGRUND_FELD,
    TEXT_FELDER_SCHADENMELDUNG,
)
from data.providers import Provider
from utils.fake_data import FallDaten
from utils.pdf_helpers import PAGE_H, PAGE_W, draw_diagonal_watermark, fmt_datum

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "assets" / "Schadenmeldeformular_RRV_Vorlage.pdf"


def _euro(betrag: float) -> str:
    text = f"{betrag:,.2f}"
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


def _ort_only(plz_ort: str) -> str:
    teile = plz_ort.split(" ", 1)
    return teile[1] if len(teile) > 1 else plz_ort


def _text_werte(fall: FallDaten, provider: Provider) -> dict[str, str]:
    heute = date.today()
    ort = _ort_only(fall.plz_ort)
    name_vorname = f"{fall.vorname} {fall.name}"

    F = TEXT_FELDER_SCHADENMELDUNG
    werte = {
        F["mgl_nr"]: fall.mgl_nr,
        F["name_vorname_versicherungsnehmer"]: name_vorname,
        F["strasse"]: fall.strasse,
        F["plz_ort"]: fall.plz_ort,
        F["telefon"]: fall.telefon,
        F["reiseveranstalter"]: provider.name,
        F["reisebuero"]: fall.reisebuero,
        F["reiseziel"]: fall.reiseziel,
        F["gebucht_am"]: fmt_datum(fall.buchungsdatum),
        F["storniert_am"]: fmt_datum(fall.stornodatum),
        F["beginn_der_reise"]: fmt_datum(fall.reise_von),
        F["geplante_rueckreise"]: fmt_datum(fall.reise_bis),
        F["versicherungsfall_datum"]: fmt_datum(fall.ereignisdatum),
        F["betroffene_person"]: name_vorname,
        F["teilnehmer1_name"]: name_vorname,
        F["teilnehmer1_geburtsdatum"]: fmt_datum(fall.geburtsdatum),
        F["teilnehmer1_anschrift"]: f"{fall.strasse}, {fall.plz_ort}",
        F["teilnehmer1_mgl_nr"]: fall.mgl_nr,
        F["gesamtreisepreis"]: _euro(fall.reisepreis),
        F["erstattungsbetrag"]: _euro(fall.erstattungsbetrag),
        F["iban"]: fall.iban,
        F["bic"]: fall.bic,
        F["name_kreditinstitut"]: fall.bank_name,
        F["name_kontoinhaber"]: name_vorname,
        F["konto_datum"]: fmt_datum(heute),
        F["konto_ort"]: ort,
        F["erklaerender_name"]: f"{fall.name}, {fall.vorname}",
        F["erklaerender_datum"]: fmt_datum(heute),
        F["erklaerender_ort"]: ort,
        F["schluss_datum"]: fmt_datum(heute),
        F["schluss_ort"]: ort,
    }
    return werte


def _checkbox_werte(fall: FallDaten) -> dict[str, str]:
    C = CHECKBOX_FELDER_SCHADENMELDUNG
    werte = {
        C["verwandt_mit_teilnehmern"]["feld"]: C["verwandt_mit_teilnehmern"]["nein"],
        C["ausgeloest_durch_dritte"]["feld"]: C["ausgeloest_durch_dritte"]["nein"],
        C["andere_versicherung_vorhanden"]["feld"]: C["andere_versicherung_vorhanden"]["nein"],
        C["bereits_gemeldet"]["feld"]: C["bereits_gemeldet"]["nein"],
        C["einwilligung_variante"]["feld"]: C["einwilligung_variante"]["moeglichkeit_1"],
        C["unterlagen_kostenbelege"]["feld"]: C["unterlagen_kostenbelege"]["ja"],
        C["unterlagen_schweigepflichtsentbindung"]["feld"]: C[
            "unterlagen_schweigepflichtsentbindung"
        ]["ja"],
        STORNIERUNGSGRUND_FELD: STORNIERUNGSGRUND_EXPORTWERTE.get(
            fall.stornierungsgrund_kategorie, "/1"
        ),
    }
    return werte


def erzeuge_schadenmeldung(fall: FallDaten, provider: Provider) -> bytes:
    reader = PdfReader(str(TEMPLATE_PATH))
    writer = PdfWriter()
    writer.append(reader)

    text_werte = _text_werte(fall, provider)
    checkbox_werte = _checkbox_werte(fall)
    alle_werte = {**text_werte, **checkbox_werte}

    for seite_idx in SEITE_SCHADENMELDUNG:
        writer.update_page_form_field_values(writer.pages[seite_idx], alle_werte)
    writer.set_need_appearances_writer(True)

    watermark_pdf = io.BytesIO()
    wc = Canvas(watermark_pdf, pagesize=(PAGE_W, PAGE_H))
    for _ in SEITE_SCHADENMELDUNG:
        draw_diagonal_watermark(wc)
        wc.showPage()
    wc.save()
    watermark_reader = PdfReader(io.BytesIO(watermark_pdf.getvalue()))
    for i, seite_idx in enumerate(SEITE_SCHADENMELDUNG):
        writer.pages[seite_idx].merge_page(watermark_reader.pages[i])

    out_writer = PdfWriter()
    out_writer.append(
        writer, pages=(SEITE_SCHADENMELDUNG[0], SEITE_SCHADENMELDUNG[-1] + 1)
    )

    buf = io.BytesIO()
    out_writer.write(buf)
    return buf.getvalue()
