"""Fiktive Reiseanbieter für die Testdokument-Generierung.

Alle Namen, Adressen und Kontaktdaten sind frei erfunden und haben keinen
Bezug zu realen Unternehmen. Jeder Anbieter hat ein Farbschema und eine
Layout-Variante (1-3), damit die erzeugten PDFs strukturell unterschiedlich
aussehen.
"""

import hashlib
import io
from dataclasses import dataclass, field

from PIL import Image, ImageDraw, ImageFont


@dataclass
class Provider:
    name: str
    strasse: str
    plz_ort: str
    telefon: str
    email: str
    ust_id: str
    farbe_primaer: str
    farbe_akzent: str
    layout_variante: int  # 1, 2 oder 3

    @property
    def initialen(self) -> str:
        woerter = [w for w in self.name.split(" ") if w and w[0].isupper()]
        if len(woerter) >= 2:
            return (woerter[0][0] + woerter[1][0]).upper()
        return self.name[:2].upper()

    def logo_bytes(self, groesse: int = 160) -> bytes:
        """Erzeugt ein einfaches Platzhalter-Logo (Initialen im farbigen Kreis)."""
        img = Image.new("RGBA", (groesse, groesse), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((0, 0, groesse - 1, groesse - 1), fill=self.farbe_primaer)
        rand = max(2, groesse // 40)
        draw.ellipse(
            (rand, rand, groesse - 1 - rand, groesse - 1 - rand),
            outline=self.farbe_akzent,
            width=max(2, groesse // 30),
        )
        text = self.initialen
        try:
            font = ImageFont.truetype("arialbd.ttf", int(groesse * 0.38))
        except OSError:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(
            ((groesse - tw) / 2 - bbox[0], (groesse - th) / 2 - bbox[1]),
            text,
            fill="white",
            font=font,
        )
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()


PROVIDERS: list[Provider] = [
    Provider(
        name="Blauwal Reisen GmbH",
        strasse="Hafenpromenade 14",
        plz_ort="20457 Hamburg",
        telefon="040 1234567",
        email="service@blauwal-reisen-test.de",
        ust_id="DE111111111",
        farbe_primaer="#0B5394",
        farbe_akzent="#6FA8DC",
        layout_variante=1,
    ),
    Provider(
        name="SonnenZeit Touristik AG",
        strasse="Ringstraße 88",
        plz_ort="80331 München",
        telefon="089 2345678",
        email="kontakt@sonnenzeit-touristik-test.de",
        ust_id="DE222222222",
        farbe_primaer="#E69138",
        farbe_akzent="#F9CB9C",
        layout_variante=2,
    ),
    Provider(
        name="Nordlicht Fernreisen KG",
        strasse="Am Kai 3",
        plz_ort="24103 Kiel",
        telefon="0431 3456789",
        email="info@nordlicht-fernreisen-test.de",
        ust_id="DE333333333",
        farbe_primaer="#134F5C",
        farbe_akzent="#76A5AF",
        layout_variante=3,
    ),
    Provider(
        name="Goldkiesel Urlaubswelt GmbH",
        strasse="Sandweg 21",
        plz_ort="50667 Köln",
        telefon="0221 4567890",
        email="team@goldkiesel-urlaubswelt-test.de",
        ust_id="DE444444444",
        farbe_primaer="#B45F06",
        farbe_akzent="#F6B26B",
        layout_variante=1,
    ),
    Provider(
        name="Wolkenpfad Erlebnisreisen e.K.",
        strasse="Bergblickweg 7",
        plz_ort="70173 Stuttgart",
        telefon="0711 5678901",
        email="hallo@wolkenpfad-erlebnisreisen-test.de",
        ust_id="DE555555555",
        farbe_primaer="#674EA7",
        farbe_akzent="#B4A7D6",
        layout_variante=2,
    ),
    Provider(
        name="Kompassrose Reiseagentur GmbH",
        strasse="Seemannsallee 45",
        plz_ort="28195 Bremen",
        telefon="0421 6789012",
        email="buero@kompassrose-reisen-test.de",
        ust_id="DE666666666",
        farbe_primaer="#38761D",
        farbe_akzent="#93C47D",
        layout_variante=3,
    ),
    Provider(
        name="Fernblick Touristik Nord GmbH",
        strasse="Leuchtturmstraße 9",
        plz_ort="18055 Rostock",
        telefon="0381 7890123",
        email="service@fernblick-touristik-test.de",
        ust_id="DE777777777",
        farbe_primaer="#990000",
        farbe_akzent="#E06666",
        layout_variante=1,
    ),
    Provider(
        name="Silberwelle Reisebüro AG",
        strasse="Uferweg 12",
        plz_ort="60313 Frankfurt am Main",
        telefon="069 8901234",
        email="info@silberwelle-reisebuero-test.de",
        ust_id="DE888888888",
        farbe_primaer="#45818E",
        farbe_akzent="#A2C4C9",
        layout_variante=2,
    ),
    Provider(
        name="Palmengarten Weltreisen GmbH",
        strasse="Oasenweg 5",
        plz_ort="04109 Leipzig",
        telefon="0341 9012345",
        email="kontakt@palmengarten-weltreisen-test.de",
        ust_id="DE999999999",
        farbe_primaer="#BF9000",
        farbe_akzent="#FFD966",
        layout_variante=3,
    ),
]


def zufaelliger_anbieter(rng) -> Provider:
    """Zieht per gegebenem random.Random-Objekt einen zufälligen Anbieter."""
    return rng.choice(PROVIDERS)
