import streamlit as st
from dotenv import load_dotenv

from app_pages.home import home_app
from app_pages.niquist import eis_app
from app_pages.db import add_data_app, edit_data_app
from app_pages.kapa import kapazitaet_app
from app_pages.biologic import biologic_app
from app_pages.dva import dva_app
from app_pages.zellen import add_zelle_app, show_zelle_app
#from app_pages.pruefung import pruefung_app
from app_pages.safion import safion_app
from app_pages.impedanz import basytec_app
#from app_pages.ecd import ecd_app
from app_pages.lup import lup_app

# streamlit run c:/projects/ba_pipline/app.py
# streamlit run /Users/janostoldy/Documents/git_projecte/ba_app/app.py
load_dotenv()
st.set_page_config(layout="wide", page_icon="🔋", page_title="Analyse-Tool")

# Seitenleiste generieren
home_page = st.Page(home_app, title="Home", default=True, icon="👋")
biologic_page = st.Page(biologic_app, title="Biologic", icon="📈")
safion_page = st.Page(safion_app, title="Safion", icon="📈")
#eingang_page = st.Page(pruefung_app, title="Prüfungen", icon="📥")
kapa_page = st.Page(kapazitaet_app, title="Kapazität", icon="📈")
dva_page = st.Page(dva_app, title="DVA", icon="📈")
eis_page = st.Page(eis_app, title="EIS", icon="📈")
basytec_page = st.Page(basytec_app, title="Basytec", icon="📈")
#ecd_page = st.Page(ecd_app, title="ECD", icon="🎛️")
lup_page = st.Page(lup_app, title="Look Up Table", icon="🗒️")
add_data_page = st.Page(add_data_app, title="Daten hinzufügen", icon="📰")
delete_data_page = st.Page(edit_data_app, title="Daten bearbeiten", icon="📰")
zelle_page = st.Page(add_zelle_app, title="Zellen hinzufügen", icon="📰")
pg = st.navigation(
    {
        "Start": [home_page],
        "Daten": [
            add_data_page,
            delete_data_page,
            zelle_page,
        ],
        "Analysen": [
            biologic_page,
            safion_page,
            #ecd_page,
        ],
        "Anwendungen": [
            #eingang_page,
            kapa_page,
            eis_page,
            dva_page,
            basytec_page,
            lup_page,
        ],
    }
)
pg.run()