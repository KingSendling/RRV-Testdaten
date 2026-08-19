"""Generator für die Online-Schadenmeldung: bildet als Bestätigungs-PDF die
Struktur des ADAC-Online-Formulars für die Reiserücktritt-Schadenmeldung
(https://www.adac.de/produkte/versicherungen/schaden-melden/reiseruecktritt/)
nach – Schritte "Schaden", "Dokumente & Rechnungen", "Persönliche Daten" und
"Prüfen & Senden" – und füllt sie mit den Falldaten.
"""

from __future__ import annotations

import random
from datetime import date

from reportlab.lib.colors import HexColor
from reportlab.pdfgen.canvas import Canvas
import io

from utils.fake_data import FallDaten
from utils.pdf_helpers import PAGE_H, PAGE_W, draw_watermark, fmt_datum

MARGIN = 50
LABEL_BREITE = 230
ADAC_BLAU = "#003781"
ADAC_GELB = "#FFCC00"


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


def _step_heading(c: Canvas, y: float, nr: int, titel: str) -> float:
    c.setFillColor(HexColor(ADAC_BLAU))
    c.circle(MARGIN + 8, y - 4, 9, fill=1, stroke=0)
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(MARGIN + 8, y - 7, str(nr))

    c.setFillColor(HexColor("#111111"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(MARGIN + 24, y - 7, titel)

    c.setStrokeColor(HexColor("#CCCCCC"))
    c.setLineWidth(0.75)
    c.line(MARGIN, y - 16, PAGE_W - MARGIN, y - 16)
    return y - 34


def _frage(c: Canvas, y: float, frage: str, antwort: object) -> float:
    antwort_text = str(antwort) if antwort not in (None, "") else "–"
    zeilen = _wrap(frage, 68)

    c.setFont("Helvetica", 8.5)
    c.setFillColor(HexColor("#555555"))
    for i, zeile in enumerate(zeilen):
        c.drawString(MARGIN, y - i * 11, zeile)
    y -= len(zeilen) * 11 + 2

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(HexColor("#111111"))
    c.drawString(MARGIN, y, antwort_text)
    return y - 20


def erzeuge_online_schadenmeldung(
    fall: FallDaten,
    enthaltene_dokumente: list[str],
    rng: random.Random,
) -> bytes:
    buf = io.BytesIO()
    c = Canvas(buf, pagesize=(PAGE_W, PAGE_H))
    draw_watermark(c)

    vorgangsnummer = f"SM-{rng.randint(1000000, 9999999)}"
    eingangsdatum = date.today()

    y = PAGE_H - 55
    c.setFillColor(HexColor(ADAC_GELB))
    c.rect(0, PAGE_H - 6, PAGE_W, 6, fill=1, stroke=0)

    c.setFont("Helvetica-Bold", 17)
    c.setFillColor(HexColor(ADAC_BLAU))
    c.drawString(MARGIN, y, "ADAC Versicherung AG")
    c.setFont("Helvetica", 10)
    c.setFillColor(HexColor("#333333"))
    c.drawString(MARGIN, y - 16, "Online-Schadenmeldung – Reiserücktrittsversicherung")

    c.setFont("Helvetica", 8.5)
    c.setFillColor(HexColor("#666666"))
    c.drawRightString(PAGE_W - MARGIN, y, f"Vorgangsnr.: {vorgangsnummer}")
    c.drawRightString(PAGE_W - MARGIN, y - 12, f"Eingegangen am: {fmt_datum(eingangsdatum)}")
    c.drawRightString(PAGE_W - MARGIN, y - 24, f"Mgl.-Nr.: {fall.mgl_nr}")

    y -= 55

    y = _step_heading(c, y, 1, "Schaden")
    y = _frage(
        c,
        y,
        "Mussten Sie Ihre Reise aufgrund einer gesundheitlichen Einschränkung ändern?",
        "Ja",
    )
    y = _frage(c, y, "Wann haben Sie Ihre Reise gebucht?", fmt_datum(fall.buchungsdatum))
    y = _frage(
        c,
        y,
        "Für welchen Reisezeitraum ist Ihre Reise geplant? "
        "(Datum der geplanten Anreise / Abreise)",
        f"{fmt_datum(fall.reise_von)} – {fmt_datum(fall.reise_bis)}",
    )
    y = _frage(c, y, "Haben Sie die Reise storniert oder abgebrochen?", "Storniert")
    y = _frage(c, y, "Stornodatum", fmt_datum(fall.stornodatum))
    y = _frage(
        c,
        y,
        "Bitte beschreiben Sie kurz den Grund der gesundheitlichen Einschränkung",
        fall.krankheit,
    )
    y -= 8

    y = _step_heading(c, y, 2, "Dokumente & Rechnungen")
    c.setFont("Helvetica", 8.5)
    c.setFillColor(HexColor("#555555"))
    c.drawString(
        MARGIN,
        y,
        "Hochgeladene Nachweise zu Schaden, Buchung und Kosten:",
    )
    y -= 16
    c.setFont("Helvetica", 9.5)
    c.setFillColor(HexColor("#111111"))
    if enthaltene_dokumente:
        for name in enthaltene_dokumente:
            c.drawString(MARGIN, y, f"📎  {name}")
            y -= 14
    else:
        c.drawString(MARGIN, y, "–")
        y -= 14
    y -= 6

    y = _step_heading(c, y, 3, "Persönliche Daten")
    spalte_x = PAGE_W / 2
    y_start = y
    y = _frage(c, y, "Name, Vorname", f"{fall.name}, {fall.vorname}")
    y = _frage(c, y, "Geburtsdatum", fmt_datum(fall.geburtsdatum))
    y = _frage(c, y, "Adresse", f"{fall.strasse}, {fall.plz_ort}")

    y2 = y_start
    c.setFont("Helvetica", 8.5)
    c.setFillColor(HexColor("#555555"))
    c.drawString(spalte_x, y2, "ADAC Mitglieds-/Kundennummer")
    y2 -= 13
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(HexColor("#111111"))
    c.drawString(spalte_x, y2, fall.mgl_nr)
    y2 -= 22

    c.setFont("Helvetica", 8.5)
    c.setFillColor(HexColor("#555555"))
    c.drawString(spalte_x, y2, "IBAN für die Erstattung")
    y2 -= 13
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(HexColor("#111111"))
    c.drawString(spalte_x, y2, fall.iban)

    y -= 6

    y = _step_heading(c, y, 4, "Prüfen & Senden")
    c.setFont("Helvetica", 8.5)
    c.setFillColor(HexColor("#333333"))
    bestaetigungstext = _wrap(
        "Ich bestätige, dass die vorstehenden Angaben der Wahrheit entsprechen. "
        "Mir ist bekannt, dass unrichtige oder unvollständige Angaben zum "
        "Verlust des Versicherungsschutzes führen können.",
        95,
    )
    for zeile in bestaetigungstext:
        c.drawString(MARGIN, y, zeile)
        y -= 12
    y -= 8

    c.setFont("Helvetica-Bold", 9.5)
    c.setFillColor(HexColor("#111111"))
    c.drawString(
        MARGIN,
        y,
        f"Elektronisch bestätigt und übermittelt am {fmt_datum(eingangsdatum)}",
    )

    c.showPage()
    c.save()
    return buf.getvalue()
