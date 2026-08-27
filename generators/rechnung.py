"""Generator für die Reiseveranstalter-Rechnung."""

from __future__ import annotations

import io
import random

from reportlab.lib.colors import HexColor
from reportlab.pdfgen.canvas import Canvas

from data.providers import Provider
from utils.fake_data import FallDaten, teilnehmer_namen_text
from utils.pdf_helpers import PAGE_H, PAGE_W, draw_footer_note, draw_header, draw_watermark, fmt_betrag, fmt_datum

LEISTUNGSPOSITIONEN_VORLAGEN = [
    ("Pauschalreise inkl. Flug & Hotel", 0.70),
    ("Flug (Hin- und Rückflug)", 0.30),
    ("Hotel inkl. Halbpension", 0.55),
    ("Transfer & Reiseversicherung", 0.10),
    ("Mietwagen", 0.20),
]


def erzeuge_rechnung(fall: FallDaten, provider: Provider, rng: random.Random) -> bytes:
    buf = io.BytesIO()
    c = Canvas(buf, pagesize=(PAGE_W, PAGE_H))

    draw_watermark(c)
    y = draw_header(c, provider, "Rechnung", "Rechnungsnr.", fall.rechnungsnummer)

    margin = 50
    c.setFont("Helvetica", 9)
    c.setFillColor(HexColor("#111111"))

    c.drawString(margin, y, f"{fall.vorname} {fall.name}")
    c.drawString(margin, y - 13, fall.strasse)
    c.drawString(margin, y - 26, fall.plz_ort)

    infos_y = y
    c.drawRightString(PAGE_W - margin, infos_y, f"Rechnungsdatum: {fmt_datum(fall.rechnungsdatum)}")
    c.drawRightString(PAGE_W - margin, infos_y - 13, f"Buchungsnummer: {fall.buchungsnummer}")
    c.drawRightString(PAGE_W - margin, infos_y - 26, f"Kundennummer: {fall.mgl_nr}")

    y -= 55
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, y, f"Reiseziel: {fall.reiseziel}")
    y -= 14
    c.setFont("Helvetica", 10)
    c.drawString(
        margin,
        y,
        f"Reisezeitraum: {fmt_datum(fall.reise_von)} – {fmt_datum(fall.reise_bis)}"
        f"{teilnehmer_namen_text(fall)}",
    )
    y -= 30

    anzahl_positionen = rng.randint(1, 3)
    positionen = rng.sample(LEISTUNGSPOSITIONEN_VORLAGEN, anzahl_positionen)
    anteile_summe = sum(a for _, a in positionen) or 1.0

    c.setFillColor(HexColor(provider.farbe_primaer))
    c.rect(margin, y, PAGE_W - 2 * margin, 20, fill=1, stroke=0)
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin + 6, y + 6, "Leistung")
    c.drawRightString(PAGE_W - margin - 6, y + 6, "Betrag")
    y -= 20

    gesamt = 0.0
    c.setFont("Helvetica", 9.5)
    for i, (bezeichnung, anteil) in enumerate(positionen):
        betrag = round(fall.reisepreis * anteil / anteile_summe, 2)
        gesamt += betrag
        c.setFillColor(HexColor("#FAFAFA") if i % 2 == 0 else HexColor("#FFFFFF"))
        c.rect(margin, y - 18, PAGE_W - 2 * margin, 18, fill=1, stroke=0)
        c.setFillColor(HexColor("#111111"))
        c.drawString(margin + 6, y - 13, bezeichnung)
        c.drawRightString(PAGE_W - margin - 6, y - 13, fmt_betrag(betrag))
        y -= 18

    y -= 8
    c.setStrokeColor(HexColor(provider.farbe_primaer))
    c.setLineWidth(1)
    c.line(margin, y, PAGE_W - margin, y)
    y -= 20
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(PAGE_W - margin - 6, y, f"Gesamtbetrag: {fmt_betrag(round(gesamt, 2))}")

    y -= 35
    c.setFont("Helvetica", 8.5)
    c.setFillColor(HexColor("#333333"))
    c.drawString(
        margin,
        y,
        "Zahlungshinweis: Der Rechnungsbetrag wurde bereits vollständig beglichen "
        "bzw. abgebucht.",
    )
    c.drawString(margin, y - 12, f"Zahlung erfolgte auf IBAN {fall.iban}.")

    draw_footer_note(c, f"{provider.name} · {provider.strasse}, {provider.plz_ort}")

    c.showPage()
    c.save()
    return buf.getvalue()
