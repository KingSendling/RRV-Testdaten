"""Generator für die Buchungsbestätigung."""

from __future__ import annotations

import io
import random

from reportlab.lib.colors import HexColor
from reportlab.pdfgen.canvas import Canvas

from data.providers import Provider
from utils.fake_data import FallDaten
from utils.pdf_helpers import PAGE_H, PAGE_W, draw_footer_note, draw_header, draw_watermark, fmt_betrag, fmt_datum


def erzeuge_buchungsbestaetigung(fall: FallDaten, provider: Provider, rng: random.Random) -> bytes:
    buf = io.BytesIO()
    c = Canvas(buf, pagesize=(PAGE_W, PAGE_H))

    draw_watermark(c)
    y = draw_header(c, provider, "Buchungsbestätigung", "Buchungsnr.", fall.buchungsnummer)

    margin = 50
    c.setFont("Helvetica", 9)
    c.setFillColor(HexColor("#111111"))
    c.drawString(margin, y, f"{fall.vorname} {fall.name}")
    c.drawString(margin, y - 13, fall.strasse)
    c.drawString(margin, y - 26, fall.plz_ort)

    c.drawRightString(PAGE_W - margin, y, f"Buchungsdatum: {fmt_datum(fall.buchungsdatum)}")
    c.drawRightString(PAGE_W - margin, y - 13, f"Kundennummer: {fall.mgl_nr}")

    y -= 55
    zeilen = [
        ("Reiseziel", fall.reiseziel),
        ("Reisezeitraum", f"{fmt_datum(fall.reise_von)} – {fmt_datum(fall.reise_bis)}"),
        ("Hauptreisender", f"{fall.vorname} {fall.name}{fall.teilnehmer_zusatz}"),
        ("Reisepreis", fmt_betrag(fall.reisepreis)),
        ("Anzahlung (bereits geleistet)", fmt_betrag(fall.anzahlung)),
        ("Restzahlung fällig am", fmt_datum(fall.reise_von)),
    ]

    c.setFont("Helvetica-Bold", 9)
    label_w = 190
    for label, wert in zeilen:
        c.setFillColor(HexColor(provider.farbe_primaer))
        c.setFont("Helvetica-Bold", 9)
        c.drawString(margin, y, label + ":")
        c.setFillColor(HexColor("#111111"))
        c.setFont("Helvetica", 9)
        c.drawString(margin + label_w, y, str(wert))
        y -= 18

    y -= 15
    c.setStrokeColor(HexColor(provider.farbe_akzent))
    c.setLineWidth(1)
    c.line(margin, y, PAGE_W - margin, y)
    y -= 20

    c.setFont("Helvetica-Bold", 9.5)
    c.setFillColor(HexColor("#111111"))
    c.drawString(margin, y, "Zahlungsbedingungen")
    y -= 14
    c.setFont("Helvetica", 8.5)
    c.setFillColor(HexColor("#333333"))
    hinweistext = [
        "Die Anzahlung in Höhe von 10-20% des Reisepreises ist mit Erhalt dieser",
        "Buchungsbestätigung fällig, die Restzahlung spätestens 30 Tage vor Reiseantritt.",
        "Es gelten die allgemeinen Reisebedingungen des Veranstalters. Der Abschluss",
        "einer Reiserücktrittsversicherung wird ausdrücklich empfohlen.",
    ]
    for zeile in hinweistext:
        c.drawString(margin, y, zeile)
        y -= 12

    draw_footer_note(c, f"{provider.name} · {provider.strasse}, {provider.plz_ort}")

    c.showPage()
    c.save()
    return buf.getvalue()
