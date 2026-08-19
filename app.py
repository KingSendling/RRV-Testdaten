"""RRV Testdokumente Generator – interne Streamlit-App zur Erzeugung
synthetischer Testdokumente für den Camunda-Prozess "Reiserücktrittsversicherung".

Alle erzeugten Daten sind fiktiv und ausschließlich für Testzwecke gedacht.
"""

from __future__ import annotations

import io
import random
import re
import zipfile
from dataclasses import replace
from datetime import date, timedelta

import streamlit as st

from data.providers import PROVIDERS, zufaelliger_anbieter
from generators.aerztliche_bescheinigung import erzeuge_aerztliche_bescheinigung
from generators.buchungsbestaetigung import erzeuge_buchungsbestaetigung
from generators.deckblatt import erzeuge_deckblatt
from generators.rechnung import erzeuge_rechnung
from generators.storno import erzeuge_storno
from utils.fake_data import (
    FallDaten,
    KRANKHEITEN_VORSCHLAEGE,
    generate_fake_iban,
    get_faker,
    is_valid_iban_checksum,
    pruefe_datumslogik,
    wuerfle_zusatzfelder,
)

st.set_page_config(
    page_title="RRV Testdokumente Generator",
    page_icon="🧾",
    layout="wide",
)

DOC_RECHNUNG = "Rechnung"
DOC_BUCHUNG = "Buchungsbestätigung"
DOC_STORNO = "Storno-Rechnung / Stornobestätigung"
DOC_AERZTLICH = "Ärztliche Bescheinigung"
PROVIDER_DOC_TYPES = [DOC_RECHNUNG, DOC_BUCHUNG, DOC_STORNO]
PROVIDER_NAMEN = [p.name for p in PROVIDERS]

FREITEXT_SENTINEL = "Sonstige / Freitext …"


def _slug(text: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "_", text)
    return text.strip("_")


def _anbieter_by_name(name: str):
    for p in PROVIDERS:
        if p.name == name:
            return p
    return PROVIDERS[0]


def _init_state():
    if st.session_state.get("initialized"):
        return

    rng = random.Random()
    fake = get_faker()
    heute = date.today()

    fall = FallDaten(
        krankheit=rng.choice(KRANKHEITEN_VORSCHLAEGE),
        mgl_nr=f"A{rng.randint(100000000, 999999999)}",
        name=fake.last_name(),
        vorname=fake.first_name(),
        strasse=f"{fake.street_name()} {fake.building_number()}",
        plz_ort=f"{fake.postcode()} {fake.city()}",
        geburtsdatum=fake.date_of_birth(minimum_age=18, maximum_age=75),
        stornodatum=heute - timedelta(days=3),
        ereignisdatum=heute - timedelta(days=4),
        reise_von=heute + timedelta(days=14),
        reise_bis=heute + timedelta(days=24),
        iban=generate_fake_iban(rng),
    )
    fall = wuerfle_zusatzfelder(fall, rng, fake)

    st.session_state.fall = fall
    st.session_state.generated = {}

    st.session_state["in_krankheit_choice"] = fall.krankheit
    st.session_state["in_krankheit_freitext"] = ""
    st.session_state["in_mgl_nr"] = fall.mgl_nr
    st.session_state["in_name"] = fall.name
    st.session_state["in_vorname"] = fall.vorname
    st.session_state["in_strasse"] = fall.strasse
    st.session_state["in_plz_ort"] = fall.plz_ort
    st.session_state["in_geburtsdatum"] = fall.geburtsdatum
    st.session_state["in_stornodatum"] = fall.stornodatum
    st.session_state["in_ereignisdatum"] = fall.ereignisdatum
    st.session_state["in_reise_von"] = fall.reise_von
    st.session_state["in_reise_bis"] = fall.reise_bis
    st.session_state["in_iban"] = fall.iban
    st.session_state["in_anbieter"] = zufaelliger_anbieter(rng).name

    st.session_state["chk_rechnung"] = True
    st.session_state["chk_buchung"] = True
    st.session_state["chk_storno"] = True
    st.session_state["chk_aerztlich"] = True

    st.session_state.initialized = True


def _aktuelle_krankheit() -> str:
    choice = st.session_state.get("in_krankheit_choice", KRANKHEITEN_VORSCHLAEGE[0])
    if choice == FREITEXT_SENTINEL:
        freitext = st.session_state.get("in_krankheit_freitext", "").strip()
        return freitext or "Nicht näher bezeichnete Erkrankung"
    return choice


def _core_falldaten_aus_eingabe() -> FallDaten:
    return FallDaten(
        krankheit=_aktuelle_krankheit(),
        mgl_nr=st.session_state["in_mgl_nr"],
        name=st.session_state["in_name"],
        vorname=st.session_state["in_vorname"],
        strasse=st.session_state["in_strasse"],
        plz_ort=st.session_state["in_plz_ort"],
        geburtsdatum=st.session_state["in_geburtsdatum"],
        stornodatum=st.session_state["in_stornodatum"],
        ereignisdatum=st.session_state["in_ereignisdatum"],
        reise_von=st.session_state["in_reise_von"],
        reise_bis=st.session_state["in_reise_bis"],
        iban=st.session_state["in_iban"],
    )


def _core_feldnamen() -> list[str]:
    return [
        "krankheit",
        "mgl_nr",
        "name",
        "vorname",
        "strasse",
        "plz_ort",
        "geburtsdatum",
        "stornodatum",
        "ereignisdatum",
        "reise_von",
        "reise_bis",
        "iban",
    ]


def _aktueller_fall_mit_core_ueberschrieben() -> FallDaten:
    core = _core_falldaten_aus_eingabe()
    updates = {k: getattr(core, k) for k in _core_feldnamen()}
    return replace(st.session_state.fall, **updates)


_init_state()

st.title("🧾 RRV Testdokumente Generator")
st.caption(
    "Interne App zur Erzeugung synthetischer Testdokumente für den Camunda-"
    "Prozess der Reiserücktrittsversicherung. Alle Daten sind frei erfunden."
)

st.subheader("1. Falldaten")

col1, col2 = st.columns(2)

with col1:
    krankheit_optionen = KRANKHEITEN_VORSCHLAEGE + [FREITEXT_SENTINEL]
    st.selectbox("Krankheit / Grund", krankheit_optionen, key="in_krankheit_choice")
    if st.session_state["in_krankheit_choice"] == FREITEXT_SENTINEL:
        st.text_input("Krankheit / Grund (Freitext)", key="in_krankheit_freitext")

    st.text_input("Mgl.-Nr. (ADAC Mitglieds-/Kundennummer)", key="in_mgl_nr")
    st.text_input("Name (Nachname)", key="in_name")
    st.text_input("Vorname", key="in_vorname")
    st.text_input("Straße/Hausnummer", key="in_strasse")
    st.text_input("PLZ/Ort", key="in_plz_ort")

    iban_col, iban_btn_col = st.columns([3, 1])
    if iban_btn_col.button("🎲 Neu", help="Neue fiktive IBAN generieren", use_container_width=True):
        st.session_state["in_iban"] = generate_fake_iban(random.Random())
    iban_col.text_input("IBAN", key="in_iban")
    if not is_valid_iban_checksum(st.session_state["in_iban"]):
        st.warning(
            "IBAN-Prüfsumme ist ungültig (MOD-97). Für Testzwecke unkritisch, "
            "aber bitte prüfen, falls das im Zielsystem validiert wird."
        )

with col2:
    st.date_input("Geburtsdatum", key="in_geburtsdatum", format="DD.MM.YYYY")
    st.date_input("Stornodatum", key="in_stornodatum", format="DD.MM.YYYY")
    st.date_input("Ereignisdatum (Diagnose/Versicherungsfall)", key="in_ereignisdatum", format="DD.MM.YYYY")
    reise_col1, reise_col2 = st.columns(2)
    reise_col1.date_input("Reisezeitraum von", key="in_reise_von", format="DD.MM.YYYY")
    reise_col2.date_input("Reisezeitraum bis", key="in_reise_bis", format="DD.MM.YYYY")

vorschau_fall = _aktueller_fall_mit_core_ueberschrieben()
warnungen = pruefe_datumslogik(vorschau_fall)
for w in warnungen:
    st.warning(f"⚠️ {w}")

st.divider()
st.subheader("2. Dokumenttypen")

dt_col1, dt_col2, dt_col3, dt_col4 = st.columns(4)
dt_col1.checkbox(DOC_RECHNUNG, key="chk_rechnung")
dt_col2.checkbox(DOC_BUCHUNG, key="chk_buchung")
dt_col3.checkbox(DOC_STORNO, key="chk_storno")
dt_col4.checkbox(DOC_AERZTLICH, key="chk_aerztlich")

st.divider()
st.subheader("3. Reiseanbieter")
st.caption(
    "Gilt für Rechnung, Buchungsbestätigung & Storno – alle drei stammen "
    "vom selben Anbieter, damit der Testfall in sich schlüssig bleibt. Jeder "
    "Anbieter hat ein eigenes Farbschema, Logo und PDF-Layout."
)

anbieter_sel_col, anbieter_btn_col, anbieter_preview_col = st.columns([3, 1, 2])

if anbieter_btn_col.button(
    "🎲 Zufällig", help="Zufälligen Reiseanbieter wählen", use_container_width=True
):
    st.session_state["in_anbieter"] = random.choice(PROVIDER_NAMEN)

anbieter_sel_col.selectbox("Reiseanbieter", PROVIDER_NAMEN, key="in_anbieter")

ausgewaehlter_anbieter = _anbieter_by_name(st.session_state["in_anbieter"])
with anbieter_preview_col:
    logo_col, info_col = st.columns([1, 2])
    logo_col.image(ausgewaehlter_anbieter.logo_bytes(96), width=48)
    info_col.markdown(
        f"Layout-Variante **{ausgewaehlter_anbieter.layout_variante}**<br>"
        f"<span style='display:inline-block;width:12px;height:12px;"
        f"background:{ausgewaehlter_anbieter.farbe_primaer};border-radius:2px;"
        f"margin-right:4px;'></span>"
        f"<span style='display:inline-block;width:12px;height:12px;"
        f"background:{ausgewaehlter_anbieter.farbe_akzent};border-radius:2px;'>"
        f"</span>",
        unsafe_allow_html=True,
    )

st.divider()
st.subheader("4. Generieren")

btn_col1, btn_col2 = st.columns([1, 1])

if btn_col1.button("🎲 Neuen Zufallsfall generieren", use_container_width=True):
    rng = random.Random()
    fake = get_faker()
    aktueller_fall = _aktueller_fall_mit_core_ueberschrieben()
    st.session_state.fall = wuerfle_zusatzfelder(aktueller_fall, rng, fake)
    st.success(
        "Zusatzfelder (Rechnungsnummern, Beträge, Arztname, Diagnosetext …) "
        "wurden neu gewürfelt. Die von dir gesetzten Kernfelder und der "
        "gewählte Reiseanbieter blieben unverändert."
    )

generieren_clicked = btn_col2.button(
    "📄 Dokumente generieren", type="primary", use_container_width=True
)

if generieren_clicked:
    ausgewaehlte_typen = []
    if st.session_state["chk_rechnung"]:
        ausgewaehlte_typen.append(DOC_RECHNUNG)
    if st.session_state["chk_buchung"]:
        ausgewaehlte_typen.append(DOC_BUCHUNG)
    if st.session_state["chk_storno"]:
        ausgewaehlte_typen.append(DOC_STORNO)
    if st.session_state["chk_aerztlich"]:
        ausgewaehlte_typen.append(DOC_AERZTLICH)

    if not ausgewaehlte_typen:
        st.error("Bitte mindestens einen Dokumenttyp auswählen.")
    else:
        fall = _aktueller_fall_mit_core_ueberschrieben()
        st.session_state.fall = fall

        rng = random.Random()
        heute_str = date.today().isoformat()
        mgl_nr_slug = _slug(fall.mgl_nr)
        name_slug = f"{_slug(fall.name)}{_slug(fall.vorname)}"
        ergebnisse: dict[str, bytes] = {}

        if DOC_RECHNUNG in ausgewaehlte_typen:
            pdf = erzeuge_rechnung(fall, ausgewaehlter_anbieter, rng)
            fname = f"{mgl_nr_slug}_Rechnung_{_slug(ausgewaehlter_anbieter.name)}_{name_slug}_{heute_str}.pdf"
            ergebnisse[fname] = pdf

        if DOC_BUCHUNG in ausgewaehlte_typen:
            pdf = erzeuge_buchungsbestaetigung(fall, ausgewaehlter_anbieter, rng)
            fname = f"{mgl_nr_slug}_Buchungsbestaetigung_{_slug(ausgewaehlter_anbieter.name)}_{name_slug}_{heute_str}.pdf"
            ergebnisse[fname] = pdf

        if DOC_STORNO in ausgewaehlte_typen:
            pdf = erzeuge_storno(fall, ausgewaehlter_anbieter, rng)
            fname = f"{mgl_nr_slug}_Storno_{_slug(ausgewaehlter_anbieter.name)}_{name_slug}_{heute_str}.pdf"
            ergebnisse[fname] = pdf

        if DOC_AERZTLICH in ausgewaehlte_typen:
            pdf = erzeuge_aerztliche_bescheinigung(fall)
            fname = f"{mgl_nr_slug}_AerztlicheBescheinigung_{name_slug}_{heute_str}.pdf"
            ergebnisse[fname] = pdf

        deckblatt_pdf = erzeuge_deckblatt(fall, ausgewaehlter_anbieter, list(ergebnisse.keys()))
        deckblatt_fname = f"{mgl_nr_slug}_00_Deckblatt_{name_slug}_{heute_str}.pdf"
        ergebnisse = {deckblatt_fname: deckblatt_pdf, **ergebnisse}

        st.session_state.generated = ergebnisse

        restliche_warnungen = pruefe_datumslogik(fall)
        for w in restliche_warnungen:
            st.warning(f"⚠️ {w}")

        st.success(f"{len(ergebnisse)} Dokument(e) erzeugt.")

if st.session_state.generated:
    st.divider()
    st.subheader("5. Download")

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname, data in st.session_state.generated.items():
            zf.writestr(fname, data)

    st.download_button(
        "⬇️ Alle Dokumente als ZIP herunterladen",
        data=zip_buf.getvalue(),
        file_name=f"RRV_Testfall_{date.today().isoformat()}.zip",
        mime="application/zip",
        type="primary",
    )

    for fname, data in st.session_state.generated.items():
        st.download_button(
            f"⬇️ {fname}",
            data=data,
            file_name=fname,
            mime="application/pdf",
            key=f"dl_{fname}",
        )
