"""RRV Testdokumente Generator – interne Streamlit-App zur Erzeugung
synthetischer Testdokumente für den Camunda-Prozess "Reiserücktrittsversicherung".

Alle erzeugten Daten sind fiktiv und ausschließlich für Testzwecke gedacht.
"""

from __future__ import annotations

import hmac
import io
import json
import random
import re
import uuid
import zipfile
from dataclasses import replace
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import streamlit as st

from data.providers import PROVIDERS, zufaelliger_anbieter
from data.testpersonen import TESTPERSONEN
from generators.aerztliche_bescheinigung import erzeuge_aerztliche_bescheinigung
from generators.buchungsbestaetigung import erzeuge_buchungsbestaetigung
from generators.online_schadenmeldung import erzeuge_online_schadenmeldung
from generators.rechnung import erzeuge_rechnung
from generators.schadenmeldung import erzeuge_schadenmeldung
from generators.storno import erzeuge_storno
from utils.pdf_helpers import kombiniere_pdfs
from utils.prozess_json import COVERAGE_PACKAGES, EINGANGSKANAELE, baue_prozess_json
from utils.fake_data import (
    FallDaten,
    ICD10_VORSCHLAEGE,
    KRANKHEITEN_VORSCHLAEGE,
    erzwinge_buchung_vor_storno_und_reise,
    fall_aus_dict,
    fall_zu_dict,
    generate_fake_iban,
    get_faker,
    is_valid_iban_checksum,
    pruefe_datumslogik,
    verschiebe_datumsfelder,
    wuerfle_zusatzfelder,
)

st.set_page_config(
    page_title="Schadenschmiede – RRV Testdokumente",
    page_icon="🔨",
    layout="wide",
)

ADAC_GELB = "#FFCC00"
ADAC_GELB_DUNKEL = "#E6B800"
INK = "#1D1D1F"
INK_MUTED = "#6E6E73"
SURFACE = "#F5F5F7"
LINE = "#E4E4E7"


def _logo_svg(size: int = 52) -> str:
    """Amboss trägt ein Dokument mit geknickter Ecke - das Schadenschmiede-
    Zeichen, als Inline-SVG in den App-Farben."""
    return f"""<svg viewBox="0 0 240 240" width="{size}" height="{size}"
        xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0;">
        <rect x="72" y="176" width="96" height="18" rx="4" fill="{INK}"/>
        <polygon points="92,176 148,176 138,146 102,146" fill="{INK}"/>
        <polygon points="60,146 180,146 160,112 80,112" fill="{INK}"/>
        <rect x="46" y="88" width="148" height="30" rx="6" fill="{INK}"/>
        <polygon points="46,93 46,113 16,103" fill="{INK}"/>
        <g transform="rotate(-6 120 66)">
            <rect x="88" y="20" width="64" height="88" rx="6" fill="#FFFFFF" stroke="{INK}" stroke-width="6"/>
            <polygon points="152,20 152,46 126,20" fill="{ADAC_GELB}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>
            <line x1="100" y1="58" x2="138" y2="58" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>
            <line x1="100" y1="74" x2="138" y2="74" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>
            <line x1="100" y1="90" x2="122" y2="90" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>
        </g>
    </svg>"""


def _logo_lockup(icon_size: int = 52, brand_size: int = 30) -> str:
    """Zeichen + zweizeilige Wortmarke ('Schaden' / 'SCHMIEDE') als HTML-
    Block, für Kopfzeile und Login-Bildschirm."""
    return f"""
    <div style="display:flex; align-items:center; gap:16px; margin-bottom:2px;">
        {_logo_svg(icon_size)}
        <div style="display:flex; flex-direction:column; line-height:1.05;">
            <span style="font-size:12px; font-weight:600; letter-spacing:0.22em;
                text-transform:uppercase; color:{INK_MUTED};">Schaden</span>
            <span style="font-size:{brand_size}px; font-weight:900; letter-spacing:-0.01em;
                color:{INK};">SCHMIEDE</span>
        </div>
    </div>
    """


def _inject_custom_css() -> None:
    """Apple-artiges Erscheinungsbild: Systemschrift (SF Pro auf Apple-
    Geräten, sonst Inter als naher Ersatz), ruhige Grautöne, dezente
    Schatten statt harter Rahmen, ADAC-Gelb als einzige Akzentfarbe."""
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [data-testid="stAppViewContainer"] {{
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text",
                "Inter", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: {INK};
        }}

        [data-testid="stAppViewContainer"] {{
            background: #FFFFFF;
        }}
        [data-testid="stHeader"] {{
            background: transparent;
        }}

        h1, h2, h3, h4 {{
            font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", sans-serif;
            font-weight: 700;
            letter-spacing: -0.015em;
            color: {INK};
        }}
        [data-testid="stMarkdownContainer"] p {{
            color: {INK};
        }}
        [data-testid="stCaptionContainer"], .stCaption {{
            color: {INK_MUTED};
        }}

        /* Buttons -------------------------------------------------- */
        .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {{
            border-radius: 10px;
            font-weight: 600;
            border: 1px solid {LINE};
            background: #FFFFFF;
            color: {INK};
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
            transition: transform 0.06s ease, box-shadow 0.15s ease;
        }}
        .stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {{
            border-color: {ADAC_GELB_DUNKEL};
            box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        }}
        .stButton > button:active, .stDownloadButton > button:active {{
            transform: scale(0.98);
        }}
        .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"],
        .stFormSubmitButton > button[kind="primary"] {{
            background: {ADAC_GELB};
            border: 1px solid {ADAC_GELB_DUNKEL};
            color: {INK} !important;
            box-shadow: 0 2px 8px rgba(230,184,0,0.35);
        }}
        /* Streamlit setzt die Textfarbe primärer Buttons teils auf einem
           inneren Element (nicht dem <button> selbst) - dort ebenfalls
           überschreiben, sonst bleibt der Text bei manchen Buttons weiß. */
        .stButton > button[kind="primary"] *, .stDownloadButton > button[kind="primary"] *,
        .stFormSubmitButton > button[kind="primary"] * {{
            color: {INK} !important;
            fill: {INK} !important;
        }}
        .stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover {{
            background: {ADAC_GELB_DUNKEL};
            box-shadow: 0 3px 10px rgba(230,184,0,0.45);
        }}

        /* Inputs ----------------------------------------------------- */
        .stTextInput input, .stNumberInput input, .stDateInput input,
        [data-baseweb="select"] > div, .stTextArea textarea {{
            border-radius: 10px !important;
            border: 1px solid {LINE} !important;
            background: {SURFACE} !important;
            box-shadow: none !important;
        }}
        .stTextInput input:focus, .stNumberInput input:focus, .stDateInput input:focus,
        [data-baseweb="select"]:focus-within > div {{
            border-color: {ADAC_GELB_DUNKEL} !important;
            box-shadow: 0 0 0 3px rgba(255,204,0,0.35) !important;
        }}

        /* Checkboxen: gelber Haken statt Standard-Rot ---------------- */
        .stCheckbox [data-baseweb="checkbox"] div[aria-checked="true"] {{
            background-color: {ADAC_GELB} !important;
            border-color: {ADAC_GELB_DUNKEL} !important;
        }}
        .stCheckbox [data-baseweb="checkbox"] svg {{
            fill: {INK} !important;
        }}

        /* Karten-Optik für Expander & Code-Block --------------------- */
        [data-testid="stExpander"] {{
            border: 1px solid {LINE};
            border-radius: 14px;
            background: {SURFACE};
            box-shadow: 0 1px 2px rgba(0,0,0,0.03);
        }}
        [data-testid="stExpander"] summary {{
            font-weight: 600;
        }}
        [data-testid="stCodeBlock"] {{
            border-radius: 12px;
            border: 1px solid {LINE};
        }}

        /* Divider dezenter ------------------------------------------- */
        hr {{
            border-color: {LINE};
        }}

        /* Downloadbutton-Liste: etwas Luft --------------------------- */
        .stDownloadButton {{
            margin-bottom: 4px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


_inject_custom_css()


def _check_password() -> bool:
    """Zeigt ein einfaches Passwort-Gate, bevor die App gerendert wird.

    Das Passwort wird über Streamlit-Secrets konfiguriert (lokal in
    .streamlit/secrets.toml, in der Cloud über die App-Settings) und NIE
    im Code oder Git-Repo hinterlegt.
    """
    if st.session_state.get("authenticated"):
        return True

    if "app_password" not in st.secrets:
        st.warning(
            "⚠️ Kein Passwortschutz konfiguriert (Secret 'app_password' "
            "fehlt) – die App ist aktuell ungeschützt erreichbar. Für den "
            "produktiven Einsatz in den App-Settings auf share.streamlit.io "
            "unter 'Secrets' ein `app_password` hinterlegen."
        )
        return True

    st.markdown(_logo_lockup(), unsafe_allow_html=True)
    st.caption("🔒 Bitte Passwort eingeben, um fortzufahren.")

    with st.form("login_form"):
        pw = st.text_input("Passwort", type="password")
        submitted = st.form_submit_button("Anmelden")

    if submitted:
        if hmac.compare_digest(pw, st.secrets["app_password"]):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Falsches Passwort.")

    return False


if not _check_password():
    st.stop()

DOC_RECHNUNG = "Rechnung"
DOC_BUCHUNG = "Buchungsbestätigung"
DOC_STORNO = "Storno-Rechnung / Stornobestätigung"
DOC_AERZTLICH = "Ärztliche Bescheinigung"
DOC_SCHADENMELDUNG_FORMULAR = "Schadenmeldung (Formular)"
DOC_SCHADENMELDUNG_ONLINE = "Online-Schadenmeldung"
PROVIDER_DOC_TYPES = [DOC_RECHNUNG, DOC_BUCHUNG, DOC_STORNO]
PROVIDER_NAMEN = [p.name for p in PROVIDERS]

FREITEXT_SENTINEL = "Sonstige / Freitext …"


def _jetzt_iso_mit_millis() -> str:
    """Aktuelles Datum/Uhrzeit in der deutschen Zeitzone (München,
    Europe/Berlin - inkl. Sommer-/Winterzeit) im von Omnia erwarteten Format
    ('2026-08-24T12:50:41.506Z'), als Default für inputDate/scanDate."""
    jetzt = datetime.now(ZoneInfo("Europe/Berlin"))
    return jetzt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{jetzt.microsecond // 1000:03d}Z"


def _slug(text: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "_", text)
    return text.strip("_")


def _dateiname_praefix() -> str:
    """Baut den optionalen Dateinamen-Präfix aus Teilprozess- und
    Testfall-Kennung, z. B. 'TP10_TF01_'. Leer, falls beide Felder leer
    sind; einzeln nutzbar, falls nur eines gesetzt ist."""
    tp = _slug(st.session_state.get("in_teilprozess", ""))
    tf = _slug(st.session_state.get("in_testfall", ""))
    teile = []
    if tp:
        teile.append(f"TP{tp}")
    if tf:
        teile.append(f"TF{tf}")
    return "_".join(teile) + "_" if teile else ""


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
    st.session_state.generated_fall_json = None
    st.session_state.generated_fall_json_fname = None
    st.session_state.generated_dateiname_praefix = ""
    st.session_state.generated_kombiniert_pdf = None
    st.session_state.generated_kombiniert_pdf_fname = None
    st.session_state.prozess_dokument_typen = []

    st.session_state["in_external_ref_id"] = ""
    st.session_state["in_process_id"] = ""
    st.session_state["in_input_date"] = _jetzt_iso_mit_millis()
    st.session_state["in_scan_date"] = _jetzt_iso_mit_millis()
    st.session_state["in_eingangskanal"] = "E-Mail"
    st.session_state["in_ereignisland"] = "DE"
    st.session_state["in_coverage_package_choice"] = COVERAGE_PACKAGES[0]
    st.session_state["in_coverage_package_freitext"] = ""

    st.session_state["in_teilprozess"] = ""
    st.session_state["in_testfall"] = ""

    st.session_state["in_krankheit_choice"] = fall.krankheit
    st.session_state["in_krankheit_freitext"] = ""
    st.session_state["in_icd10_choice"] = _icd10_option_text(fall.krankheit)
    st.session_state["in_icd10_freitext"] = ""
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
    st.session_state["chk_schadenmeldung_formular"] = True
    st.session_state["chk_schadenmeldung_online"] = True

    st.session_state.initialized = True


def _aktuelle_krankheit() -> str:
    choice = st.session_state.get("in_krankheit_choice", KRANKHEITEN_VORSCHLAEGE[0])
    if choice == FREITEXT_SENTINEL:
        freitext = st.session_state.get("in_krankheit_freitext", "").strip()
        return freitext or "Nicht näher bezeichnete Erkrankung"
    return choice


def _icd10_option_text(krankheit: str) -> str:
    code, bezeichnung = ICD10_VORSCHLAEGE.get(krankheit, ICD10_VORSCHLAEGE["Grippaler Infekt"])
    return f"{code} – {bezeichnung}"


def _aktueller_icd10_code() -> str:
    choice = st.session_state.get("in_icd10_choice", _icd10_option_text(KRANKHEITEN_VORSCHLAEGE[0]))
    if choice == FREITEXT_SENTINEL:
        return st.session_state.get("in_icd10_freitext", "").strip()
    return choice.split(" – ")[0]


def _core_falldaten_aus_eingabe() -> FallDaten:
    return FallDaten(
        krankheit=_aktuelle_krankheit(),
        icd10_code=_aktueller_icd10_code(),
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
        "icd10_code",
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

st.markdown(_logo_lockup(icon_size=56, brand_size=32), unsafe_allow_html=True)
st.caption(
    "RRV Testdokumente Generator – interne App zur Erzeugung synthetischer "
    "Testdokumente für den Camunda-Prozess der Reiserücktrittsversicherung. "
    "Alle Daten sind frei erfunden."
)

tp_col, tf_col = st.columns(2)
tp_col.text_input(
    "Teilprozess (TP)",
    key="in_teilprozess",
    placeholder="z. B. 10",
    help="Optional. Wird als 'TP<Wert>_' vor den Dateinamen gestellt.",
)
tf_col.text_input(
    "Testfall (TF)",
    key="in_testfall",
    placeholder="z. B. 01",
    help="Optional. Wird als 'TF<Wert>_' vor den Dateinamen gestellt.",
)
dateiname_vorschau = _dateiname_praefix()
if dateiname_vorschau:
    st.caption(f"Dateinamen beginnen mit: `{dateiname_vorschau}`")

with st.expander("📂 Bestehenden Testfall wiederholen (optional)"):
    st.caption(
        "Lädt eine zuvor unter '5. Download' exportierte Testfall-JSON-Datei "
        "erneut. Alle Zufallsdaten (Name, IBAN, Diagnosetext, Beträge, "
        "Anbieter …) bleiben dabei exakt identisch – nur das Ereignisdatum "
        "wird auf den neuen Wert gesetzt, und alle anderen Datumsfelder "
        "(Storno, Reisezeitraum, Buchung, AU-Zeitraum …) verschieben sich "
        "um denselben Abstand mit, damit der Testfall zeitlich schlüssig "
        "bleibt. Das Geburtsdatum ändert sich nicht."
    )
    hochgeladene_datei = st.file_uploader(
        "Testfall-JSON hochladen", type="json", key="upload_testfall"
    )
    if hochgeladene_datei is not None:
        try:
            geladene_daten = json.loads(hochgeladene_datei.getvalue().decode("utf-8"))
            geladener_fall, geladener_anbieter = fall_aus_dict(geladene_daten)
        except Exception as exc:
            st.error(f"Konnte Datei nicht lesen: {exc}")
            geladener_fall = None
            geladener_anbieter = ""

        if geladener_fall is not None:
            st.write(
                f"Geladen: **{geladener_fall.vorname} {geladener_fall.name}** "
                f"({geladener_fall.mgl_nr}) · bisheriges Ereignisdatum: "
                f"{geladener_fall.ereignisdatum.strftime('%d.%m.%Y')}"
            )
            neues_ereignisdatum = st.date_input(
                "Neues Ereignisdatum",
                value=date.today(),
                format="DD.MM.YYYY",
                key="upload_neues_ereignisdatum",
            )
            if st.button("Testfall laden & Datum verschieben"):
                verschoben = verschiebe_datumsfelder(geladener_fall, neues_ereignisdatum)
                st.session_state.fall = verschoben
                gewaehlte_krankheit = verschoben.krankheit
                if gewaehlte_krankheit in KRANKHEITEN_VORSCHLAEGE:
                    st.session_state["in_krankheit_choice"] = gewaehlte_krankheit
                    st.session_state["in_krankheit_freitext"] = ""
                else:
                    st.session_state["in_krankheit_choice"] = FREITEXT_SENTINEL
                    st.session_state["in_krankheit_freitext"] = gewaehlte_krankheit
                if verschoben.icd10_code and verschoben.icd10_code == ICD10_VORSCHLAEGE.get(
                    gewaehlte_krankheit, (None, None)
                )[0]:
                    st.session_state["in_icd10_choice"] = _icd10_option_text(gewaehlte_krankheit)
                    st.session_state["in_icd10_freitext"] = ""
                else:
                    st.session_state["in_icd10_choice"] = FREITEXT_SENTINEL
                    st.session_state["in_icd10_freitext"] = verschoben.icd10_code
                st.session_state["in_mgl_nr"] = verschoben.mgl_nr
                st.session_state["in_name"] = verschoben.name
                st.session_state["in_vorname"] = verschoben.vorname
                st.session_state["in_strasse"] = verschoben.strasse
                st.session_state["in_plz_ort"] = verschoben.plz_ort
                st.session_state["in_geburtsdatum"] = verschoben.geburtsdatum
                st.session_state["in_stornodatum"] = verschoben.stornodatum
                st.session_state["in_ereignisdatum"] = verschoben.ereignisdatum
                st.session_state["in_reise_von"] = verschoben.reise_von
                st.session_state["in_reise_bis"] = verschoben.reise_bis
                st.session_state["in_iban"] = verschoben.iban
                if geladener_anbieter in PROVIDER_NAMEN:
                    st.session_state["in_anbieter"] = geladener_anbieter
                st.session_state.generated = {}
                st.success(
                    "Testfall geladen, Datum verschoben. Werte unten prüfen "
                    "und ggf. anpassen, dann Dokumente generieren."
                )
                st.rerun()

with st.expander("👤 Testperson aus Liste vorausfüllen (optional)"):
    st.caption(
        "Füllt Mgl.-Nr., Name, Vorname, Geburtsdatum und Adresse mit einer "
        "vordefinierten Testperson aus dem internen Testdatensatz vor. "
        "Krankheit, Termine und IBAN bleiben unverändert."
    )
    testperson_col, testperson_btn_col = st.columns([3, 1])
    testperson_anzeige = testperson_col.selectbox(
        "Testperson",
        [p.anzeige for p in TESTPERSONEN],
        key="in_testperson_auswahl",
        label_visibility="collapsed",
    )
    if testperson_btn_col.button("Übernehmen", use_container_width=True):
        gewaehlte_person = next(
            p for p in TESTPERSONEN if p.anzeige == testperson_anzeige
        )
        st.session_state["in_mgl_nr"] = gewaehlte_person.mgl_nr
        st.session_state["in_name"] = gewaehlte_person.nachname
        st.session_state["in_vorname"] = gewaehlte_person.vorname
        st.session_state["in_geburtsdatum"] = gewaehlte_person.geburtsdatum
        st.session_state["in_strasse"] = gewaehlte_person.strasse
        st.session_state["in_plz_ort"] = gewaehlte_person.plz_ort
        st.success(f"Daten von {gewaehlte_person.anzeige} übernommen.")
        st.rerun()

st.subheader("1. Falldaten")

col1, col2 = st.columns(2)

with col1:
    krankheit_optionen = KRANKHEITEN_VORSCHLAEGE + [FREITEXT_SENTINEL]
    st.selectbox("Krankheit / Grund", krankheit_optionen, key="in_krankheit_choice")
    if st.session_state["in_krankheit_choice"] == FREITEXT_SENTINEL:
        st.text_input("Krankheit / Grund (Freitext)", key="in_krankheit_freitext")

    icd10_col, icd10_btn_col = st.columns([3, 1])
    if icd10_btn_col.button(
        "🎲 Passend zur Krankheit",
        help="ICD-10-Code passend zur gewählten Krankheit übernehmen",
        use_container_width=True,
    ):
        st.session_state["in_icd10_choice"] = _icd10_option_text(_aktuelle_krankheit())
    icd10_optionen = [_icd10_option_text(k) for k in KRANKHEITEN_VORSCHLAEGE] + [FREITEXT_SENTINEL]
    icd10_col.selectbox("ICD-10-Code (Ärztliche Bescheinigung)", icd10_optionen, key="in_icd10_choice")
    if st.session_state["in_icd10_choice"] == FREITEXT_SENTINEL:
        st.text_input("ICD-10-Code (Freitext)", key="in_icd10_freitext")

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
    st.date_input(
        "Geburtsdatum",
        key="in_geburtsdatum",
        format="DD.MM.YYYY",
        min_value=date(1943, 1, 1),
        max_value=date.today(),
    )
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

dt_col1, dt_col2, dt_col3, dt_col4, dt_col5, dt_col6 = st.columns(6)
dt_col1.checkbox(DOC_RECHNUNG, key="chk_rechnung")
dt_col2.checkbox(DOC_BUCHUNG, key="chk_buchung")
dt_col3.checkbox(DOC_STORNO, key="chk_storno")
dt_col4.checkbox(DOC_AERZTLICH, key="chk_aerztlich")
dt_col5.checkbox(DOC_SCHADENMELDUNG_FORMULAR, key="chk_schadenmeldung_formular")
dt_col6.checkbox(DOC_SCHADENMELDUNG_ONLINE, key="chk_schadenmeldung_online")
st.caption(
    f"'{DOC_SCHADENMELDUNG_FORMULAR}' befüllt die Seiten 1-4 der Original-"
    "ADAC-Formularvorlage (dasselbe PDF wie die Ärztliche Bescheinigung). "
    f"'{DOC_SCHADENMELDUNG_ONLINE}' orientiert sich am 4-stufigen ADAC-Online-"
    "Formular (Schaden → Dokumente & Rechnungen → Persönliche Daten → "
    "Prüfen & Senden)."
)

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
    if st.session_state["chk_schadenmeldung_formular"]:
        ausgewaehlte_typen.append(DOC_SCHADENMELDUNG_FORMULAR)
    if st.session_state["chk_schadenmeldung_online"]:
        ausgewaehlte_typen.append(DOC_SCHADENMELDUNG_ONLINE)

    if not ausgewaehlte_typen:
        st.error("Bitte mindestens einen Dokumenttyp auswählen.")
    else:
        fall = _aktueller_fall_mit_core_ueberschrieben()
        fall = erzwinge_buchung_vor_storno_und_reise(fall, random.Random())
        st.session_state.fall = fall

        rng = random.Random()
        ereignisdatum_str = fall.ereignisdatum.isoformat()
        mgl_nr_slug = _slug(fall.mgl_nr)
        name_slug = f"{_slug(fall.name)}{_slug(fall.vorname)}"
        dateiname_praefix = _dateiname_praefix()
        ergebnisse: dict[str, bytes] = {}

        if DOC_RECHNUNG in ausgewaehlte_typen:
            pdf = erzeuge_rechnung(fall, ausgewaehlter_anbieter, rng)
            fname = f"{dateiname_praefix}{mgl_nr_slug}_Rechnung_{_slug(ausgewaehlter_anbieter.name)}_{name_slug}_{ereignisdatum_str}.pdf"
            ergebnisse[fname] = pdf

        if DOC_BUCHUNG in ausgewaehlte_typen:
            pdf = erzeuge_buchungsbestaetigung(fall, ausgewaehlter_anbieter, rng)
            fname = f"{dateiname_praefix}{mgl_nr_slug}_Buchungsbestaetigung_{_slug(ausgewaehlter_anbieter.name)}_{name_slug}_{ereignisdatum_str}.pdf"
            ergebnisse[fname] = pdf

        if DOC_STORNO in ausgewaehlte_typen:
            pdf = erzeuge_storno(fall, ausgewaehlter_anbieter, rng)
            fname = f"{dateiname_praefix}{mgl_nr_slug}_Storno_{_slug(ausgewaehlter_anbieter.name)}_{name_slug}_{ereignisdatum_str}.pdf"
            ergebnisse[fname] = pdf

        if DOC_AERZTLICH in ausgewaehlte_typen:
            pdf = erzeuge_aerztliche_bescheinigung(fall)
            fname = f"{dateiname_praefix}{mgl_nr_slug}_AerztlicheBescheinigung_{name_slug}_{ereignisdatum_str}.pdf"
            ergebnisse[fname] = pdf

        if DOC_SCHADENMELDUNG_FORMULAR in ausgewaehlte_typen:
            pdf = erzeuge_schadenmeldung(fall, ausgewaehlter_anbieter)
            fname = f"{dateiname_praefix}{mgl_nr_slug}_Schadenmeldung_{name_slug}_{ereignisdatum_str}.pdf"
            ergebnisse[fname] = pdf

        if DOC_SCHADENMELDUNG_ONLINE in ausgewaehlte_typen:
            pdf = erzeuge_online_schadenmeldung(fall, list(ergebnisse.keys()), rng)
            fname = f"{dateiname_praefix}{mgl_nr_slug}_OnlineSchadenmeldung_{name_slug}_{ereignisdatum_str}.pdf"
            ergebnisse[fname] = pdf

        st.session_state.generated = ergebnisse
        st.session_state.generated_kombiniert_pdf = kombiniere_pdfs(list(ergebnisse.values()))
        st.session_state.generated_kombiniert_pdf_fname = (
            f"{dateiname_praefix}{mgl_nr_slug}_Gesamtdokument_{name_slug}_{ereignisdatum_str}.pdf"
        )
        st.session_state.generated_fall_json = json.dumps(
            fall_zu_dict(fall, ausgewaehlter_anbieter.name), ensure_ascii=False, indent=2
        )
        st.session_state.generated_fall_json_fname = (
            f"{dateiname_praefix}{mgl_nr_slug}_Testfall_{name_slug}_{ereignisdatum_str}.json"
        )
        st.session_state.generated_dateiname_praefix = dateiname_praefix
        st.session_state["in_external_ref_id"] = str(uuid.uuid4())
        st.session_state["in_input_date"] = _jetzt_iso_mit_millis()
        st.session_state["in_scan_date"] = _jetzt_iso_mit_millis()

        # Reihenfolge der Dokumente in der kombinierten Scan-Übermittlung
        # (SMF, AEB, REISEBU, STORNO-RE) - nur tatsächlich erzeugte Typen.
        prozess_dokument_typen = []
        if DOC_SCHADENMELDUNG_FORMULAR in ausgewaehlte_typen:
            prozess_dokument_typen.append("SMF")
        if DOC_AERZTLICH in ausgewaehlte_typen:
            prozess_dokument_typen.append("AEB")
        if DOC_BUCHUNG in ausgewaehlte_typen:
            prozess_dokument_typen.append("REISEBU")
        if DOC_STORNO in ausgewaehlte_typen:
            prozess_dokument_typen.append("STORNO-RE")
        st.session_state.prozess_dokument_typen = prozess_dokument_typen

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
        if st.session_state.generated_fall_json:
            zf.writestr(
                st.session_state.generated_fall_json_fname,
                st.session_state.generated_fall_json,
            )

    bundle_col1, bundle_col2, bundle_col3 = st.columns(3)
    bundle_col1.download_button(
        "⬇️ Alle Dokumente als ZIP herunterladen",
        data=zip_buf.getvalue(),
        file_name=f"{st.session_state.get('generated_dateiname_praefix', '')}RRV_Testfall_{date.today().isoformat()}.zip",
        mime="application/zip",
        type="primary",
        use_container_width=True,
    )

    if st.session_state.generated_kombiniert_pdf:
        bundle_col2.download_button(
            "⬇️ Alle Dokumente als ein PDF herunterladen",
            data=st.session_state.generated_kombiniert_pdf,
            file_name=st.session_state.generated_kombiniert_pdf_fname,
            mime="application/pdf",
            type="primary",
            use_container_width=True,
            help="Alle erzeugten PDFs in dieser Reihenfolge zu einer Datei zusammengefügt.",
        )

    if st.session_state.generated_fall_json:
        bundle_col3.download_button(
            "⬇️ Fall als JSON exportieren (für spätere Wiederholung)",
            data=st.session_state.generated_fall_json,
            file_name=st.session_state.generated_fall_json_fname,
            mime="application/json",
            type="primary",
            use_container_width=True,
            help=(
                "Damit lässt sich dieser Testfall über 'Bestehenden Testfall "
                "wiederholen' oben mit neuem Ereignisdatum erneut erzeugen."
            ),
        )

    for fname, data in st.session_state.generated.items():
        st.download_button(
            f"⬇️ {fname}",
            data=data,
            file_name=fname,
            mime="application/pdf",
            key=f"dl_{fname}",
        )

    st.divider()
    st.subheader("6. Prozess-JSON (Omnia)")
    doc_typen_liste = ", ".join(st.session_state.prozess_dokument_typen) or "–"
    st.caption(
        "Dokumenteneingangs-Metadaten für die kombinierte Scan-Übermittlung "
        f"der gewählten Dokumente ({doc_typen_liste}), passend zum aktuellen "
        "Testfall. Eingangs- und Scan-Datum sind mit dem aktuellen Zeitpunkt "
        "vorbelegt, ProcessID ist dir nicht bekannt – bitte manuell eintragen."
    )

    refid_col, refid_btn_col = st.columns([3, 1])
    if refid_btn_col.button(
        "🎲 Neu",
        help="Neue zufällige externalRefId generieren",
        use_container_width=True,
        key="btn_neue_external_ref_id",
    ):
        st.session_state["in_external_ref_id"] = str(uuid.uuid4())
    refid_col.text_input(
        "externalRefId",
        key="in_external_ref_id",
        help="Zufällig vorbelegt, kann bei Bedarf manuell überschrieben werden.",
    )

    pj_col1, pj_col2, pj_col3 = st.columns(3)
    pj_col1.text_input(
        "ProcessID",
        key="in_process_id",
        placeholder="z. B. 35427ae3-30cf-4f7b-d6dc-08df01ac6554",
    )
    pj_col2.text_input(
        "inputDate",
        key="in_input_date",
        help="Vorbelegt mit dem aktuellen UTC-Zeitpunkt, kann bei Bedarf manuell überschrieben werden.",
    )
    pj_col3.text_input(
        "scanDate",
        key="in_scan_date",
        help="Vorbelegt mit dem aktuellen UTC-Zeitpunkt, kann bei Bedarf manuell überschrieben werden.",
    )

    pj_col4, pj_col5, pj_col6 = st.columns(3)
    pj_col4.selectbox(
        "Eingangskanal",
        list(EINGANGSKANAELE.keys()),
        key="in_eingangskanal",
        help=(
            "Bestimmt scanType/medium/recipientAddressType sowie ob "
            "sender/receiver gesetzt sind (bei Post gibt es keine "
            "E-Mail-Adressen)."
        ),
    )
    pj_col5.text_input(
        "Ereignisland (caseEventCountry/claimEventCountry)",
        key="in_ereignisland",
        max_chars=2,
        help="Zweistelliger Ländercode, z. B. DE oder PT.",
    )
    coverage_optionen = COVERAGE_PACKAGES + [FREITEXT_SENTINEL]
    pj_col6.selectbox("Tarifpaket (coveragePackage)", coverage_optionen, key="in_coverage_package_choice")
    if st.session_state["in_coverage_package_choice"] == FREITEXT_SENTINEL:
        pj_col6.text_input(
            "Tarifpaket (Freitext)",
            key="in_coverage_package_freitext",
        )

    coverage_package_wert = (
        st.session_state["in_coverage_package_freitext"]
        if st.session_state["in_coverage_package_choice"] == FREITEXT_SENTINEL
        else st.session_state["in_coverage_package_choice"]
    )

    prozess_json_dict = baue_prozess_json(
        st.session_state.fall,
        dokument_typen=st.session_state.prozess_dokument_typen,
        external_ref_id=st.session_state["in_external_ref_id"],
        process_id=st.session_state["in_process_id"],
        input_date=st.session_state["in_input_date"],
        scan_date=st.session_state["in_scan_date"],
        eingangskanal=st.session_state["in_eingangskanal"],
        ereignisland=st.session_state["in_ereignisland"],
        coverage_package=coverage_package_wert,
    )
    if not st.session_state.prozess_dokument_typen:
        st.warning(
            "⚠️ Keiner der für das Prozess-JSON bekannten Dokumenttypen "
            "(Schadenmeldung Formular, Ärztliche Bescheinigung, "
            "Buchungsbestätigung, Storno-Rechnung) wurde generiert – die "
            "Dokumentenliste im JSON ist daher leer."
        )
    prozess_json_text = json.dumps(prozess_json_dict, ensure_ascii=False, indent=2)
    st.code(prozess_json_text, language="json")

    _fall = st.session_state.fall
    prozess_json_fname = (
        f"{st.session_state.get('generated_dateiname_praefix', '')}"
        f"{_slug(_fall.mgl_nr)}_ProzessJSON_{_slug(_fall.name)}{_slug(_fall.vorname)}_"
        f"{_fall.ereignisdatum.isoformat()}.json"
    )
    st.download_button(
        "⬇️ Prozess-JSON herunterladen",
        data=prozess_json_text,
        file_name=prozess_json_fname,
        mime="application/json",
        type="primary",
        use_container_width=True,
    )
