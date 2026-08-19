"""Gemeinsame PDF-Bausteine für die Generatoren: Wasserzeichen, Formatierung
und die drei strukturell unterschiedlichen Anbieter-Briefkopf-Layouts."""

from __future__ import annotations

import io
from datetime import date

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

from data.providers import Provider

PAGE_W, PAGE_H = A4


def fmt_datum(d: date | None) -> str:
    if d is None:
        return ""
    return d.strftime("%d.%m.%Y")


def fmt_betrag(betrag: float) -> str:
    text = f"{betrag:,.2f}"
    text = text.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{text} EUR"


def draw_diagonal_watermark(c: Canvas):
    c.saveState()
    c.setFont("Helvetica-Bold", 46)
    c.setFillColor(HexColor("#C0C0C0"))
    try:
        c.setFillAlpha(0.28)
    except Exception:
        pass
    c.translate(PAGE_W / 2, PAGE_H / 2)
    c.rotate(38)
    c.drawCentredString(0, 0, "TESTDOKUMENT – FIKTIVE DATEN")
    c.restoreState()


def draw_watermark(c: Canvas):
    """Diagonales Wasserzeichen + kleine Fußzeilen-Notiz. Für frei
    gestaltete Dokumente (Rechnung, Buchungsbestätigung, Storno)."""
    draw_diagonal_watermark(c)

    c.saveState()
    c.setFont("Helvetica", 7)
    c.setFillColor(HexColor("#888888"))
    c.drawString(
        50,
        44,
        "TESTDOKUMENT – fiktive Daten, kein echter Geschäftsvorfall",
    )
    c.restoreState()


def draw_header(c: Canvas, provider: Provider, titel: str, referenz_label: str, referenz_wert: str) -> float:
    """Zeichnet den Anbieter-Briefkopf abhängig von der Layout-Variante des
    Anbieters. Gibt die y-Koordinate zurück, ab der Inhalt folgen kann."""
    variante = provider.layout_variante
    if variante == 1:
        return _header_variante_1(c, provider, titel, referenz_label, referenz_wert)
    elif variante == 2:
        return _header_variante_2(c, provider, titel, referenz_label, referenz_wert)
    else:
        return _header_variante_3(c, provider, titel, referenz_label, referenz_wert)


def _logo_image(provider: Provider) -> ImageReader:
    return ImageReader(io.BytesIO(provider.logo_bytes()))


def _header_variante_1(c: Canvas, p: Provider, titel: str, ref_label: str, ref_wert: str) -> float:
    margin = 50
    logo = _logo_image(p)
    c.drawImage(logo, margin, PAGE_H - 100, width=50, height=50, mask="auto")

    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(HexColor(p.farbe_primaer))
    c.drawString(margin + 60, PAGE_H - 65, p.name)

    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor("#333333"))
    c.drawString(margin + 60, PAGE_H - 78, p.strasse + " | " + p.plz_ort)
    c.drawString(margin + 60, PAGE_H - 89, f"Tel. {p.telefon} | {p.email}")

    c.setFont("Helvetica", 8)
    c.drawRightString(PAGE_W - margin, PAGE_H - 65, f"USt-IdNr.: {p.ust_id}")
    c.drawRightString(PAGE_W - margin, PAGE_H - 78, f"{ref_label}: {ref_wert}")

    y = PAGE_H - 120
    c.setStrokeColor(HexColor(p.farbe_primaer))
    c.setLineWidth(1.5)
    c.line(margin, y, PAGE_W - margin, y)

    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(HexColor("#111111"))
    c.drawString(margin, y - 30, titel)

    return y - 55


def _header_variante_2(c: Canvas, p: Provider, titel: str, ref_label: str, ref_wert: str) -> float:
    margin = 50
    bar_h = 90
    c.setFillColor(HexColor(p.farbe_primaer))
    c.rect(0, PAGE_H - bar_h, PAGE_W, bar_h, fill=1, stroke=0)

    logo = _logo_image(p)
    c.drawImage(logo, margin, PAGE_H - bar_h + 15, width=45, height=45, mask="auto")

    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(HexColor("#FFFFFF"))
    c.drawString(margin + 58, PAGE_H - 42, p.name)
    c.setFont("Helvetica", 8)
    c.drawString(margin + 58, PAGE_H - 55, p.strasse + ", " + p.plz_ort)
    c.drawString(margin + 58, PAGE_H - 66, f"Tel. {p.telefon} | {p.email} | USt-IdNr. {p.ust_id}")

    c.setFillColor(HexColor(p.farbe_akzent))
    c.rect(0, PAGE_H - bar_h - 6, PAGE_W, 6, fill=1, stroke=0)

    y = PAGE_H - bar_h - 40
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(HexColor("#111111"))
    c.drawString(margin, y, titel)
    c.setFont("Helvetica", 9)
    c.drawRightString(PAGE_W - margin, y, f"{ref_label}: {ref_wert}")

    return y - 30


def _header_variante_3(c: Canvas, p: Provider, titel: str, ref_label: str, ref_wert: str) -> float:
    margin = 50
    logo = _logo_image(p)
    logo_size = 44
    c.drawImage(
        logo,
        PAGE_W / 2 - logo_size / 2,
        PAGE_H - 80,
        width=logo_size,
        height=logo_size,
        mask="auto",
    )

    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(HexColor(p.farbe_primaer))
    c.drawCentredString(PAGE_W / 2, PAGE_H - 95, p.name)

    c.setFont("Helvetica", 7.5)
    c.setFillColor(HexColor("#555555"))
    c.drawCentredString(
        PAGE_W / 2,
        PAGE_H - 106,
        f"{p.strasse} · {p.plz_ort} · Tel. {p.telefon} · {p.email} · USt-IdNr. {p.ust_id}",
    )

    y = PAGE_H - 122
    c.setStrokeColor(HexColor(p.farbe_akzent))
    c.setLineWidth(2)
    c.line(margin, y, PAGE_W - margin, y)

    c.setFont("Helvetica-Bold", 15)
    c.setFillColor(HexColor("#111111"))
    c.drawString(margin, y - 28, titel)
    c.setFont("Helvetica", 9)
    c.drawRightString(PAGE_W - margin, y - 28, f"{ref_label}: {ref_wert}")

    return y - 52


def draw_footer_note(c: Canvas, text: str):
    c.saveState()
    c.setFont("Helvetica-Oblique", 7.5)
    c.setFillColor(HexColor("#666666"))
    c.drawString(50, 30, text)
    c.restoreState()
