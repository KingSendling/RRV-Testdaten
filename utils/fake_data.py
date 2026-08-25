"""Hilfsfunktionen für Zufalls-/Testdaten: IBAN-Generator, Faker-Wrapper,
Datumslogik und das Falldaten-Datenmodell.

Alle Daten sind ausschließlich fiktiv und für Testzwecke gedacht.
"""

from __future__ import annotations

import random
import string
from dataclasses import dataclass, field, fields, replace
from datetime import date, timedelta

from faker import Faker

# BLZ-Bereich, der von der Bundesbank nicht an echte Institute vergeben wird
# -> klar erkennbar als Testdaten, aber strukturell gültig (8-stellig).
FIKTIVE_BLZ_PRAEFIXE = ["9999", "9998", "9997"]

KRANKHEITEN_VORSCHLAEGE = [
    "Grippaler Infekt",
    "Magen-Darm-Infekt",
    "Bänderriss (Sprunggelenk)",
    "Schwangerschaftskomplikation",
    "Akute Blinddarmentzündung",
    "Bandscheibenvorfall",
    "Knochenbruch (Unterarm)",
    "Herz-Kreislauf-Beschwerden",
    "Migräneattacke",
    "Covid-19-Infektion",
]

REISEZIELE = [
    "Mallorca, Spanien",
    "Kreta, Griechenland",
    "Antalya, Türkei",
    "Toskana, Italien",
    "Algarve, Portugal",
    "Kanarische Inseln, Spanien",
    "Côte d'Azur, Frankreich",
    "Istrien, Kroatien",
    "Sylt, Deutschland",
    "Tirol, Österreich",
]

FACHRICHTUNGEN = [
    "Orthopädie",
    "Innere Medizin",
    "Chirurgie",
    "Gynäkologie",
    "Neurologie",
    "Kardiologie",
]

BANKNAMEN = [
    "Sparkasse Musterstadt",
    "Volksbank Beispiel eG",
    "Deutsche Testbank AG",
    "Raiffeisenbank Fiktiv eG",
    "Testhausen Kreissparkasse",
]

# Ordnet eine Krankheit einem plausiblen ICD-10-GM-Code + Bezeichnung zu.
# Die Ärztliche Bescheinigung hat kein eigenes Formularfeld für den ICD-10-
# Code - er wird stattdessen an den Diagnosetext angehängt (siehe
# generators/aerztliche_bescheinigung.py).
ICD10_VORSCHLAEGE: dict[str, tuple[str, str]] = {
    "Grippaler Infekt": ("J06.9", "Akute Infektion der oberen Atemwege, nicht näher bezeichnet"),
    "Magen-Darm-Infekt": ("A09", "Sonstige und nicht näher bezeichnete Gastroenteritis und Kolitis"),
    "Bänderriss (Sprunggelenk)": ("S93.4", "Distorsion und Zerrung des oberen Sprunggelenkes"),
    "Schwangerschaftskomplikation": ("O47.0", "Vorzeitige Wehen ohne Entbindung"),
    "Akute Blinddarmentzündung": ("K35.80", "Akute Appendizitis, nicht näher bezeichnet"),
    "Bandscheibenvorfall": ("M51.2", "Sonstige näher bezeichnete Bandscheibenverlagerung"),
    "Knochenbruch (Unterarm)": ("S52.5", "Distale Fraktur des Radius"),
    "Herz-Kreislauf-Beschwerden": ("I10", "Essentielle Hypertonie"),
    "Migräneattacke": ("G43.9", "Migräne, nicht näher bezeichnet"),
    "Covid-19-Infektion": ("U07.1", "COVID-19, Virus nachgewiesen"),
}

# Ordnet eine Krankheit einer der 9 Stornierungsgrund-Kategorien des
# Schadenmeldeformulars zu (Exportwerte "1"-"9" von Feld 17).
STORNIERUNGSGRUND_KATEGORIEN: dict[str, str] = {
    "Grippaler Infekt": "Unerwartete, schwere Erkrankung",
    "Magen-Darm-Infekt": "Unerwartete, schwere Erkrankung",
    "Bänderriss (Sprunggelenk)": "Unfall",
    "Schwangerschaftskomplikation": "Schwangerschaft",
    "Akute Blinddarmentzündung": "Unerwartete, schwere Erkrankung",
    "Bandscheibenvorfall": "Unerwartete, schwere Erkrankung",
    "Knochenbruch (Unterarm)": "Unfall",
    "Herz-Kreislauf-Beschwerden": "Unerwartete, schwere Erkrankung",
    "Migräneattacke": "Unerwartete, schwere Erkrankung",
    "Covid-19-Infektion": "Unerwartete, schwere Erkrankung",
}

KLINIKNAMEN = [
    "Klinikum St. Elisabeth",
    "Städtisches Krankenhaus Nordstadt",
    "Marienhospital",
    "Universitätsklinikum Mitte",
    "Kreisklinik Am Waldpark",
]


def get_faker() -> Faker:
    fake = Faker("de_DE")
    return fake


def _mod97_check_digits(bban: str, country_code: str) -> str:
    """Berechnet die IBAN-Prüfziffern nach ISO 7064 (MOD97-10)."""
    rearranged = bban + country_code + "00"
    numeric = ""
    for ch in rearranged:
        if ch.isdigit():
            numeric += ch
        else:
            numeric += str(ord(ch.upper()) - ord("A") + 10)
    remainder = int(numeric) % 97
    check = 98 - remainder
    return f"{check:02d}"


def generate_fake_iban(rng: random.Random) -> str:
    """Erzeugt eine strukturell gültige (MOD-97), aber garantiert fiktive
    deutsche IBAN (BLZ-Bereich existiert bei keinem echten Institut)."""
    blz_praefix = rng.choice(FIKTIVE_BLZ_PRAEFIXE)
    blz = blz_praefix + "".join(rng.choices(string.digits, k=8 - len(blz_praefix)))
    kontonummer = "".join(rng.choices(string.digits, k=10))
    bban = blz + kontonummer
    check_digits = _mod97_check_digits(bban, "DE")
    return f"DE{check_digits}{bban}"


def is_valid_iban_checksum(iban: str) -> bool:
    iban = iban.replace(" ", "").upper()
    if len(iban) < 5:
        return False
    country_code = iban[:2]
    bban = iban[4:]
    expected = _mod97_check_digits(bban, country_code)
    return iban[2:4] == expected


@dataclass
class FallDaten:
    # --- Kernfelder: vom User eingegeben, bleiben bei "Neuer Zufallsfall" erhalten ---
    krankheit: str = "Grippaler Infekt"
    icd10_code: str = ""
    mgl_nr: str = ""
    name: str = ""
    vorname: str = ""
    strasse: str = ""
    plz_ort: str = ""
    geburtsdatum: date = field(default_factory=lambda: date(1985, 5, 15))
    stornodatum: date = field(default_factory=lambda: date.today() - timedelta(days=3))
    ereignisdatum: date = field(default_factory=lambda: date.today() - timedelta(days=4))
    reise_von: date = field(default_factory=lambda: date.today() + timedelta(days=10))
    reise_bis: date = field(default_factory=lambda: date.today() + timedelta(days=20))
    iban: str = ""

    # --- Automatisch generierte Zusatzfelder (werden bei Reroll neu gewürfelt) ---
    reiseziel: str = ""
    rechnungsnummer: str = ""
    rechnungsdatum: date | None = None
    buchungsnummer: str = ""
    buchungsdatum: date | None = None
    reisepreis: float = 0.0
    anzahlung: float = 0.0
    teilnehmer_zusatz: str = ""

    diagnose_text: str = ""
    erster_arztbesuch_datum: date | None = None
    therapie_text: str = ""
    facharzt_ueberweisung: bool = False
    facharzt_fachrichtung: str = ""
    au_von: date | None = None
    au_bis: date | None = None
    stationaer: bool = False
    klinikname: str = ""
    klinik_von: date | None = None
    klinik_bis: date | None = None
    vorerkrankungen: bool = False
    vorerkrankungen_text: str = ""

    arzt_name: str = ""
    praxis_ort: str = ""
    praxisstempel_text: str = ""
    bescheinigung_datum: date | None = None

    telefon: str = ""
    email: str = ""
    reisebuero: str = ""
    bic: str = ""
    bank_name: str = ""
    erstattungsbetrag: float = 0.0
    stornierungsgrund_kategorie: str = ""

    def ist_schwangerschaftsfall(self) -> bool:
        stichworte = ["schwanger", "schwangerschaft"]
        return any(s in self.krankheit.lower() for s in stichworte)


def _diagnose_text_fuer(krankheit: str, rng: random.Random) -> str:
    vorlagen = {
        "Grippaler Infekt": [
            "Ausgeprägter grippaler Infekt mit Fieber, Husten und starkem "
            "Krankheitsgefühl.",
            "Fieberhafter Atemwegsinfekt mit deutlicher Reiseunfähigkeit.",
        ],
        "Magen-Darm-Infekt": [
            "Akute Gastroenteritis mit Erbrechen und Durchfall, "
            "Kreislaufbelastung.",
        ],
        "Bänderriss (Sprunggelenk)": [
            "Ruptur des Außenbandapparates am linken Sprunggelenk nach "
            "Distorsionstrauma.",
        ],
        "Schwangerschaftskomplikation": [
            "Vorzeitige Wehentätigkeit mit ärztlich angeordneter Schonung "
            "und Reiseverbot.",
        ],
        "Akute Blinddarmentzündung": [
            "Akute Appendizitis, operative Versorgung erforderlich.",
        ],
        "Bandscheibenvorfall": [
            "Lumbaler Bandscheibenvorfall mit ausstrahlenden Schmerzen und "
            "Bewegungseinschränkung.",
        ],
        "Knochenbruch (Unterarm)": [
            "Distale Radiusfraktur rechts nach Sturzereignis, "
            "Ruhigstellung erforderlich.",
        ],
        "Herz-Kreislauf-Beschwerden": [
            "Hypertensive Entgleisung mit Schwindel und "
            "Belastungsintoleranz.",
        ],
        "Migräneattacke": [
            "Schwere Migräneattacke mit Aura und ausgeprägter "
            "Reiseunfähigkeit.",
        ],
        "Covid-19-Infektion": [
            "Laborbestätigte Covid-19-Infektion mit Fieber und "
            "Erschöpfungssymptomatik.",
        ],
    }
    optionen = vorlagen.get(
        krankheit, [f"Diagnose im Zusammenhang mit: {krankheit}."]
    )
    return rng.choice(optionen)


def _therapie_text_fuer(krankheit: str, rng: random.Random) -> str:
    optionen = [
        "Medikamentöse Therapie, körperliche Schonung, engmaschige Kontrolle.",
        "Symptomatische Behandlung, Bettruhe, ausreichende Flüssigkeitszufuhr.",
        "Ruhigstellung, Physiotherapie, schmerzadaptierte Medikation.",
        "Stationäre Überwachung, medikamentöse Einstellung, Verlaufskontrolle.",
    ]
    return rng.choice(optionen)


def wuerfle_zusatzfelder(fall: FallDaten, rng: random.Random, fake: Faker) -> FallDaten:
    """Erzeugt eine Kopie von `fall`, bei der alle Zusatzfelder (nicht die
    Kernfelder) neu, aber in sich konsistent gewürfelt werden."""
    neu = replace(fall)

    neu.reiseziel = rng.choice(REISEZIELE)
    neu.rechnungsnummer = f"RG-{rng.randint(100000, 999999)}"
    neu.rechnungsdatum = neu.stornodatum + timedelta(days=rng.randint(0, 2))
    neu.buchungsnummer = f"BK-{rng.randint(100000, 999999)}"
    # Gebucht wird immer VOR dem Reisebeginn und VOR (oder am selben Tag wie)
    # dem Stornodatum - sonst würde der Camunda-Prozess den Testfall wegen
    # unplausibler Reihenfolge (Storno vor Buchung) aussteuern.
    fruehestes_bezugsdatum = min(neu.stornodatum, neu.reise_von)
    neu.buchungsdatum = fruehestes_bezugsdatum - timedelta(days=rng.randint(14, 150))

    grundpreis = rng.randint(2, 6) * 100 + rng.choice([0, 49, 90, 99])
    personen = rng.choice([1, 1, 2, 2, 3])
    neu.reisepreis = round(grundpreis * personen, 2)
    neu.anzahlung = round(neu.reisepreis * rng.choice([0.1, 0.15, 0.2]), 2)
    if personen > 1:
        neu.teilnehmer_zusatz = f" + {personen - 1} weitere Person(en)"
    else:
        neu.teilnehmer_zusatz = ""

    neu.diagnose_text = _diagnose_text_fuer(fall.krankheit, rng)
    neu.erster_arztbesuch_datum = fall.ereignisdatum - timedelta(
        days=rng.randint(0, 2)
    )
    neu.therapie_text = _therapie_text_fuer(fall.krankheit, rng)

    neu.facharzt_ueberweisung = rng.random() < 0.4
    neu.facharzt_fachrichtung = (
        rng.choice(FACHRICHTUNGEN) if neu.facharzt_ueberweisung else ""
    )

    au_dauer = rng.randint(3, 14)
    neu.au_von = fall.ereignisdatum
    neu.au_bis = fall.ereignisdatum + timedelta(days=au_dauer)

    neu.stationaer = rng.random() < 0.25
    if neu.stationaer:
        neu.klinikname = rng.choice(KLINIKNAMEN)
        klinik_dauer = rng.randint(1, 5)
        neu.klinik_von = fall.ereignisdatum
        neu.klinik_bis = fall.ereignisdatum + timedelta(days=klinik_dauer)
    else:
        neu.klinikname = ""
        neu.klinik_von = None
        neu.klinik_bis = None

    neu.vorerkrankungen = rng.random() < 0.1
    neu.vorerkrankungen_text = (
        "Bekannte Vorerkrankung ohne Zusammenhang zum aktuellen Ereignis."
        if neu.vorerkrankungen
        else ""
    )

    nachname_arzt = fake.last_name()
    neu.arzt_name = f"Dr. med. {fake.first_name()} {nachname_arzt}"
    neu.praxis_ort = fake.city()
    neu.praxisstempel_text = (
        f"Dr. med. {nachname_arzt} · Praxis für Allgemeinmedizin · "
        f"{fake.street_name()} {fake.building_number()}, "
        f"{fake.postcode()} {neu.praxis_ort}"
    )
    neu.bescheinigung_datum = fall.ereignisdatum + timedelta(days=rng.randint(0, 3))

    neu.telefon = fake.phone_number()
    neu.email = fake.email()
    neu.reisebuero = f"{fake.company()} Reisebüro"
    neu.bic = fake.swift(length=8)
    neu.bank_name = rng.choice(BANKNAMEN)
    _, erstattung = berechne_stornokosten(neu.reisepreis, fall.reise_von, fall.stornodatum)
    neu.erstattungsbetrag = erstattung
    neu.stornierungsgrund_kategorie = STORNIERUNGSGRUND_KATEGORIEN.get(
        fall.krankheit, "Unerwartete, schwere Erkrankung"
    )

    return neu


def erzwinge_buchung_vor_storno_und_reise(fall: FallDaten, rng: random.Random) -> FallDaten:
    """Stellt sicher, dass Buchungsdatum <= Stornodatum UND Buchungsdatum <=
    Reisebeginn gilt - beide Regeln sind hart, da der Camunda-Prozess
    Testfälle mit Storno oder Reisebeginn vor der Buchung immer aussteuert.
    Wird als Sicherheitsnetz aufgerufen, falls Stornodatum oder
    Reisezeitraum nachträglich (ohne Reroll) manuell vor das gewürfelte
    Buchungsdatum verschoben wurden."""
    fruehestes_bezugsdatum = min(fall.stornodatum, fall.reise_von)
    if fall.buchungsdatum is not None and fall.buchungsdatum <= fruehestes_bezugsdatum:
        return fall
    neu = replace(fall)
    neu.buchungsdatum = fruehestes_bezugsdatum - timedelta(days=rng.randint(14, 150))
    return neu


def pruefe_datumslogik(fall: FallDaten) -> list[str]:
    """Gibt eine Liste von Warnhinweisen (nicht blockierend) zurück."""
    warnungen: list[str] = []

    if fall.buchungsdatum is not None and fall.buchungsdatum > fall.stornodatum:
        warnungen.append(
            "Buchungsdatum liegt nach dem Stornodatum – der Prozess würde "
            "diesen Testfall aussteuern. Wird beim Generieren automatisch "
            "korrigiert."
        )
    if fall.buchungsdatum is not None and fall.buchungsdatum > fall.reise_von:
        warnungen.append(
            "Buchungsdatum liegt nach dem Reisebeginn – der Prozess würde "
            "diesen Testfall aussteuern. Wird beim Generieren automatisch "
            "korrigiert."
        )
    if fall.reise_bis <= fall.reise_von:
        warnungen.append(
            "Reiseende liegt nicht nach dem Reisebeginn – bitte prüfen."
        )
    if fall.stornodatum >= fall.reise_von:
        warnungen.append(
            "Stornodatum liegt nicht vor dem Reisebeginn – unüblich für "
            "einen Rücktritt."
        )
    if fall.ereignisdatum > fall.stornodatum + timedelta(days=3):
        warnungen.append(
            "Ereignisdatum liegt deutlich nach dem Stornodatum – "
            "inhaltlich prüfen."
        )
    if fall.ereignisdatum < fall.stornodatum - timedelta(days=30):
        warnungen.append(
            "Ereignisdatum liegt sehr lange vor dem Stornodatum – "
            "inhaltlich prüfen."
        )
    heute = date.today()
    if fall.geburtsdatum >= heute:
        warnungen.append("Geburtsdatum liegt in der Zukunft.")
    alter = (heute - fall.geburtsdatum).days / 365.25
    if alter < 0 or alter > 110:
        warnungen.append("Geburtsdatum ergibt ein unplausibles Alter.")

    return warnungen


def fall_zu_dict(fall: FallDaten, anbieter_name: str = "") -> dict:
    """Serialisiert einen Testfall vollständig nach JSON-kompatiblem dict,
    damit er als Datei gespeichert und später (z.B. zur Wiederholung eines
    Tests mit neuem Ereignisdatum) wieder geladen werden kann."""
    daten = {}
    for k, v in vars(fall).items():
        if isinstance(v, date):
            daten[k] = v.isoformat()
        else:
            daten[k] = v
    daten["_anbieter_name"] = anbieter_name
    daten["_format_version"] = 1
    return daten


_DATUM_FELDER = [
    "geburtsdatum",
    "stornodatum",
    "ereignisdatum",
    "reise_von",
    "reise_bis",
    "rechnungsdatum",
    "buchungsdatum",
    "erster_arztbesuch_datum",
    "au_von",
    "au_bis",
    "klinik_von",
    "klinik_bis",
    "bescheinigung_datum",
]

# Wird beim Verschieben NICHT mitverschoben - das Geburtsdatum einer Person
# ändert sich nicht dadurch, dass ein Testfall an einem anderen Tag
# wiederholt wird.
_NICHT_VERSCHIEBBAR = {"geburtsdatum"}


def fall_aus_dict(daten: dict) -> tuple[FallDaten, str]:
    """Rekonstruiert einen Testfall aus fall_zu_dict(). Gibt (FallDaten,
    anbieter_name) zurück."""
    anbieter_name = daten.get("_anbieter_name", "")
    feldnamen = {f.name for f in fields(FallDaten)}
    kwargs = {}
    for k, v in daten.items():
        if k not in feldnamen:
            continue
        if k in _DATUM_FELDER and v is not None:
            kwargs[k] = date.fromisoformat(v)
        else:
            kwargs[k] = v
    return FallDaten(**kwargs), anbieter_name


def verschiebe_datumsfelder(fall: FallDaten, neues_ereignisdatum: date) -> FallDaten:
    """Verschiebt alle Datumsfelder eines Testfalls (außer Geburtsdatum) um
    dieselbe Anzahl Tage, sodass `ereignisdatum` zu `neues_ereignisdatum`
    wird. So lässt sich ein bereits erzeugter Testfall 1:1 wiederholen -
    alle Zufallsdaten (Name, IBAN, Diagnosetext, Beträge, Anbieter ...)
    bleiben identisch, nur die zeitliche Lage des gesamten Falls verschiebt
    sich einheitlich."""
    delta = neues_ereignisdatum - fall.ereignisdatum
    if delta == timedelta(0):
        return fall
    neu = replace(fall)
    for feldname in _DATUM_FELDER:
        if feldname in _NICHT_VERSCHIEBBAR:
            continue
        wert = getattr(fall, feldname)
        if wert is not None:
            setattr(neu, feldname, wert + delta)
    return neu


def berechne_stornokosten(reisepreis: float, reise_von: date, stornodatum: date) -> tuple[float, float]:
    """Berechnet gestaffelte Stornokosten nach Tagen vor Reiseantritt.
    Gibt (stornokosten, erstattungsbetrag) zurück."""
    tage_vorher = (reise_von - stornodatum).days
    if tage_vorher > 30:
        satz = 0.20
    elif tage_vorher > 14:
        satz = 0.40
    elif tage_vorher > 7:
        satz = 0.60
    elif tage_vorher > 1:
        satz = 0.80
    else:
        satz = 0.95
    stornokosten = round(reisepreis * satz, 2)
    erstattung = round(reisepreis - stornokosten, 2)
    return stornokosten, erstattung
