"""Generator für das Deckblatt: fasst alle Falldaten und Zusatzangaben eines
Testfalls auf einer Seite zusammen, damit Tester die Eckdaten nicht erst aus
den Einzeldokumenten zusammensuchen müssen."""

from __future__ import annotations

import io
from datetime import date

from reportlab.lib.colors import HexColor
from reportlab.pdfgen.canvas import Canvas

from data.providers import Provider
from utils.fake_data import FallDaten
from utils.pdf_helpers import PAGE_H, PAGE_W, draw_watermark, fmt_betrag, fmt_datum

MARGIN = 50
LABEL_BREITE = 165


def _abschnitt(c: Canvas, y: float, titel: str) -> float:
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(HexColor("#111111"))
    c.drawString(MARGIN, y, titel)
    c.setStrokeColor(HexColor("#CCCCCC"))
    c.setLineWidth(0.75)
    c.line(MARGIN, y - 5, PAGE_W - MARGIN, y - 5)
    return y - 22


def _wrap(text: str, max_chars: int) -> list[str]:
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
    return zeilen or [""]


def _zeile(c: Canvas, y: float, label: str, wert: object) -> float:
    text = str(wert) if wert not in (None, "") else "–"
    zeilen = _wrap(text, 68)

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(HexColor("#444444"))
    c.drawString(MARGIN, y, label + ":")

    c.setFont("Helvetica", 9)
    c.setFillColor(HexColor("#111111"))
    for i, zeile in enumerate(zeilen):
        c.drawString(MARGIN + LABEL_BREITE, y - i * 12, zeile)

    return y - max(15, len(zeilen) * 12 + 3)


def erzeuge_deckblatt(
    fall: FallDaten,
    provider: Provider | None,
    enthaltene_dokumente: list[str],
) -> bytes:
    buf = io.BytesIO()
    c = Canvas(buf, pagesize=(PAGE_W, PAGE_H))
    draw_watermark(c)

    y = PAGE_H - 60
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(HexColor("#111111"))
    c.drawString(MARGIN, y, "Testfall-Deckblatt")
    c.setFont("Helvetica", 9)
    c.setFillColor(HexColor("#666666"))
    c.drawRightString(PAGE_W - MARGIN, y, f"Erzeugt am {fmt_datum(date.today())}")
    y -= 15
    c.setFont("Helvetica", 9)
    c.setFillColor(HexColor("#666666"))
    c.drawRightString(PAGE_W - MARGIN, y, f"Mgl.-Nr.: {fall.mgl_nr}")
    y -= 30

    y = _abschnitt(c, y, "Versicherungsnehmer")
    y = _zeile(c, y, "Mgl.-Nr.", fall.mgl_nr)
    y = _zeile(c, y, "Name", f"{fall.vorname} {fall.name}")
    y = _zeile(c, y, "Adresse", f"{fall.strasse}, {fall.plz_ort}")
    y = _zeile(c, y, "Geburtsdatum", fmt_datum(fall.geburtsdatum))
    y = _zeile(c, y, "IBAN", fall.iban)
    y -= 8

    y = _abschnitt(c, y, "Versicherungsfall")
    y = _zeile(c, y, "Krankheit / Grund", fall.krankheit)
    y = _zeile(c, y, "Ereignisdatum", fmt_datum(fall.ereignisdatum))
    y = _zeile(c, y, "Stornodatum", fmt_datum(fall.stornodatum))
    y = _zeile(
        c, y, "Reisezeitraum", f"{fmt_datum(fall.reise_von)} – {fmt_datum(fall.reise_bis)}"
    )
    y = _zeile(c, y, "Reiseziel", fall.reiseziel)
    y -= 8

    if provider is not None:
        y = _abschnitt(c, y, "Reiseanbieter (Rechnung / Buchungsbestätigung / Storno)")
        y = _zeile(c, y, "Anbieter", provider.name)
        y = _zeile(c, y, "Adresse", f"{provider.strasse}, {provider.plz_ort}")
        y = _zeile(c, y, "Rechnungsnr.", fall.rechnungsnummer)
        y = _zeile(c, y, "Buchungsnr.", fall.buchungsnummer)
        y = _zeile(c, y, "Reisepreis", fmt_betrag(fall.reisepreis))
        y -= 8

    y = _abschnitt(c, y, "Ärztliche Bescheinigung")
    y = _zeile(c, y, "Diagnose", fall.diagnose_text)
    y = _zeile(c, y, "Behandelnder Arzt", fall.arzt_name)
    y = _zeile(
        c, y, "Arbeitsunfähigkeit", f"{fmt_datum(fall.au_von)} – {fmt_datum(fall.au_bis)}"
    )
    if fall.stationaer:
        y = _zeile(
            c,
            y,
            "Stationäre Behandlung",
            f"{fall.klinikname} ({fmt_datum(fall.klinik_von)} – {fmt_datum(fall.klinik_bis)})",
        )
    y -= 8

    y = _abschnitt(c, y, "Enthaltene Dokumente in diesem Testfall")
    c.setFont("Helvetica", 9)
    c.setFillColor(HexColor("#111111"))
    if enthaltene_dokumente:
        for name in enthaltene_dokumente:
            c.drawString(MARGIN, y, f"•  {name}")
            y -= 14
    else:
        c.drawString(MARGIN, y, "–")
        y -= 14

    c.showPage()
    c.save()
    return buf.getvalue()
