"""Generator für die Storno-Rechnung / Stornobestätigung."""

from __future__ import annotations

import io
import random

from reportlab.lib.colors import HexColor
from reportlab.pdfgen.canvas import Canvas

from data.providers import Provider
from utils.fake_data import (
    FallDaten,
    effektive_erstattung,
    effektive_stornokosten,
    effektiver_reisepreis,
    teilnehmer_namen_text,
)
from utils.pdf_helpers import PAGE_H, PAGE_W, draw_footer_note, draw_header, draw_watermark, fmt_betrag, fmt_datum


def erzeuge_storno(fall: FallDaten, provider: Provider, rng: random.Random) -> bytes:
    buf = io.BytesIO()
    c = Canvas(buf, pagesize=(PAGE_W, PAGE_H))

    storno_nr = f"ST-{rng.randint(100000, 999999)}"

    draw_watermark(c)
    y = draw_header(c, provider, "Storno-Rechnung", "Storno-Nr.", storno_nr)

    margin = 50
    c.setFont("Helvetica", 9)
    c.setFillColor(HexColor("#111111"))
    c.drawString(margin, y, f"{fall.vorname} {fall.name}")
    c.drawString(margin, y - 13, fall.strasse)
    c.drawString(margin, y - 26, fall.plz_ort)
    if fall.weitere_teilnehmer:
        c.setFont("Helvetica", 8)
        c.setFillColor(HexColor("#555555"))
        c.drawString(margin, y - 39, f"Mitreisende:{teilnehmer_namen_text(fall)}")
        c.setFont("Helvetica", 9)
        c.setFillColor(HexColor("#111111"))

    c.drawRightString(PAGE_W - margin, y, f"Ursprüngl. Buchungsnr.: {fall.buchungsnummer}")
    c.drawRightString(PAGE_W - margin, y - 13, f"Stornodatum: {fmt_datum(fall.stornodatum)}")

    y -= 55
    c.setFont("Helvetica-Bold", 9.5)
    c.setFillColor(HexColor(provider.farbe_primaer))
    c.drawString(margin, y, "Stornogrund:")
    c.setFont("Helvetica", 9.5)
    c.setFillColor(HexColor("#111111"))
    c.drawString(margin + 100, y, "Rücktritt")
    y -= 22

    reisepreis_anzeige = effektiver_reisepreis(fall)
    stornokosten = effektive_stornokosten(fall)
    erstattung = effektive_erstattung(fall)

    if fall.stornostaffel_override.strip():
        satz_text = fall.stornostaffel_override.strip()
    else:
        tage_vorher = (fall.reise_von - fall.stornodatum).days
        if tage_vorher > 30:
            satz_text = "20% (mehr als 30 Tage vor Reiseantritt)"
        elif tage_vorher > 14:
            satz_text = "40% (15-30 Tage vor Reiseantritt)"
        elif tage_vorher > 7:
            satz_text = "60% (8-14 Tage vor Reiseantritt)"
        elif tage_vorher > 1:
            satz_text = "80% (2-7 Tage vor Reiseantritt)"
        else:
            satz_text = "95% (kurzfristiger Rücktritt)"

    zeilen = [
        ("Ursprünglicher Reisepreis", fmt_betrag(reisepreis_anzeige)),
        ("Stornostaffel", satz_text),
        ("Stornokosten", fmt_betrag(stornokosten)),
    ]
    c.setFont("Helvetica-Bold", 9)
    for label, wert in zeilen:
        c.setFillColor(HexColor("#333333"))
        c.setFont("Helvetica-Bold", 9)
        c.drawString(margin, y, label + ":")
        c.setFillColor(HexColor("#111111"))
        c.setFont("Helvetica", 9)
        c.drawString(margin + 190, y, str(wert))
        y -= 18

    y -= 8
    c.setStrokeColor(HexColor(provider.farbe_primaer))
    c.setLineWidth(1)
    c.line(margin, y, PAGE_W - margin, y)
    y -= 20

    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(HexColor("#111111"))
    c.drawString(margin, y, "Zu erstattender Betrag:")
    c.drawRightString(PAGE_W - margin, y, fmt_betrag(erstattung))

    y -= 40
    c.setFont("Helvetica", 8.5)
    c.setFillColor(HexColor("#333333"))
    c.drawString(
        margin,
        y,
        "Die Erstattung erfolgt auf das bei der Buchung hinterlegte Zahlungsmittel",
    )
    c.drawString(margin, y - 12, "innerhalb von 14 Werktagen nach Bestätigung der Stornierung.")

    draw_footer_note(c, f"{provider.name} · {provider.strasse}, {provider.plz_ort}")

    c.showPage()
    c.save()
    return buf.getvalue()
