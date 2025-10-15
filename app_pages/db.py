import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from classes.datenbank import Database
from src.filtern import daten_filter, typ_filer
from src.plotting_df import highlight_status, status_func
from classes.datenanalyse import Analyse
import os

def add_data_app():
    st.title("Daten hinzufügen")
    DB = Database("Add_Data")
    DA = Analyse()
    con2 = st.container(border=True)
    con2.header("Analayze EIS Data")
    folder = con2.text_input("Daten-Ordner eingeben",
                             value=st.session_state.get("folder","/Volumes/ftm/EV_Lab_BatLab/02_Messexport/Urban/BA_Toldy/Charakterisierung"),
                             placeholder="/Data")
    st.session_state["folder"] = folder
    alle_zellen = DB.get_all_zells()
    zelle = con2.selectbox("Zellen eingeben", alle_zellen["id"], index=st.session_state.get("zelle_index",None))
    st.session_state["zelle_index"] = alle_zellen["id"].tolist().index(zelle) if zelle in alle_zellen["id"].tolist() else None
    typs = ["Eingangsprüfung", "EIS-Analyse","EIS-Analyse (+5)","Create LUP","Ageing","DVA-Analyse","Kapazitäts-Messung","Impedanz",
            "Thermische Relaxation"]
    typ = con2.selectbox("Analyse Art",typs, index=st.session_state.get("typ_index",None))
    st.session_state["typ_index"] = typs.index(typ) if typ in typs else None
    last_cycle = DB.get_zell_cycle(zelle)
    last_cycle = last_cycle.values[0][0] if not last_cycle.empty else 1
    cycle = con2.number_input("Zyklus eingeben", min_value=0, max_value=1000, value=last_cycle, step=1)

    try:
        datei_liste = DB.get_all_files()
        con2.info(f"Aktualisiert um {datetime.now().strftime('%H:%M:%S')}")
    except Exception as e:
        con2.error(f"Fehler beim Abrufen der Datenbank: {e}")
        datei_liste = None

    dis_button = False
    if datei_liste is not None:
        try:
            with st.spinner("Daten suchen...", show_time=True):
                files = [f for f in os.listdir(folder) if f.endswith('.mpr') or f.endswith('.csv')]
        except Exception as e:
            con2.error(f"Fehler beim Abrufen der Dateien im Ordner: {e}")
            files = None
        if files is not None and len(files) > 0:
            # DF mit allen Dateien und Status und gefilterten Dateien
            gespeicherte_dateien = datei_liste['name'].values
            import_files = pd.DataFrame([{'Datei': f,'Größe (KB)': round(os.path.getsize(os.path.join(folder, f)) / 1024)} for f in files])
            import_files["Status"] = import_files["Datei"].apply(lambda f: status_func(f, gespeicherte_dateien, folder))
            col1, col2 = con2.columns([4,1])
            col1.write("Gefundene .mpr-Dateien")
            filter = col2.selectbox(
                "Status",
                ("Neu","In Datenbank","Fehlende Daten"),
                label_visibility="collapsed",
                index=None,
                placeholder="Filter wählen...",

            )
            # Filter anwenden, wenn ausgewählt
            if filter:
                filter_files = import_files[import_files["Status"] == filter]
            else:
                filter_files = import_files

            if "filter_files" not in st.session_state or st.session_state.filter_files.equals(filter_files) == False:
                 st.session_state.filter_files = filter_files
            event = con2.dataframe(
                st.session_state.filter_files.style.map(highlight_status, subset=["Status"]),
                key="data",
                on_select="rerun",
                selection_mode="multi-row",
            )
            selected_rows = st.session_state.filter_files.iloc[event.selection.rows]
            if con2.button("Analyse", type="primary", use_container_width=True, disabled=dis_button):
                file_dir = [os.path.join(folder, f) for f in selected_rows["Datei"]]
                my_bar = st.progress(0, text="Daten werden analysiert...")
                if typ == "EIS-Analyse":
                    DA.analyze_EIS_data(file_path=file_dir, cycle=cycle, Zelle=zelle, save_data=True)
                elif typ == "EIS-Analyse (+5)":
                    for n, direkt in enumerate(file_dir):
                        my_bar.progress((n+1) / len(file_dir), text=f"Analysiere {os.path.basename(direkt)} ...")
                        DA.analyze_EIS_data(file_path=[direkt], cycle=cycle, Zelle=zelle, save_data=True)
                        cycle = cycle + 5
                elif typ == "Create LUP":
                    DA.analyze_LUP_data(file_path=file_dir, cycle=cycle, Zelle=zelle, save_data=True)
                elif typ == "DVA-Analyse":
                    DA.analys_OCV_data(file_path=file_dir, cycle=cycle, Zelle=zelle, save_data=True)
                elif typ == "Kapazitäts-Messung":
                    DA.analys_kapa_data(file_path=file_dir, cycle=cycle, Zelle=zelle, save_data=True)
                elif typ == "Eingangsprüfung":
                    DA.analyse_eingang(file_path=file_dir, cycle=cycle, Zelle=zelle, save_data=True, bar=my_bar)
                elif typ == "Ageing":
                    DA.analyze_Aeging(file_path=file_dir, cycle=cycle, Zelle=zelle, save_data=True, bar=my_bar)
                elif typ == "Thermische Relaxation":
                    DA.add_relax(file_path=file_dir, cycle=cycle, Zelle=zelle, save_data=True)
                elif typ == "Impedanz":
                    DA.analyse_imp(file_path=file_dir, cycle=cycle, Zelle=zelle, save_data=True, bar=my_bar)
                my_bar.progress(1, text="Datenanalyse erfolgreich!")
                my_bar.empty()
                con2.success("Daten erfolgreich in Datenbank gespeichert.")
                datei_liste = DB.get_all_files()
        else:
            con2.warning("Keine Datein im Ordner gefunden.")
            # Liste der Unterordner im angegebenen Ordner anzeigen
            try:
                con1 = st.container(border=False)
                ordner_liste = [d for d in os.listdir(folder) if os.path.isdir(os.path.join(folder, d))]
                if ordner_liste:
                    con1.subheader("Gefundene Unterordner:")
                    for n, ordner in enumerate(ordner_liste):
                        space, col1, col2 = con1.columns([1, 1, 20])
                        col1.write(n)
                        if col2.button(f"📁 {ordner}", key=f"ordner_{ordner}", type="tertiary",
                                       help=f"Ordner {ordner} öffnen"):
                            st.session_state["folder"] = os.path.join(folder, ordner)

                else:
                    con2.warning("Keine Unterordner im angegebenen Ordner gefunden.")
            except Exception as e:
                st.error(f"Fehler beim Auflisten der Unterordner: {e}")

    if 'datei_liste' in locals():
        #df.columns = ['Datei', 'Zyklus', 'Zelle']
        st.write("Dateien in Datenbank:")
        datei_liste.sort_values(by=["datum"], ascending=False, inplace=True)
        st.dataframe(datei_liste)

@st.dialog("Löschen bestätigen",width="small")
def file_loeschen(files,DB):
    st.write("Wollen sie die Zelle wirklich löschen?")
    st.write(files)
    if st.button("Endgültig Löschen", type="primary", use_container_width=True):
        for f in files:
            DB.delete_file(f)
        st.rerun()

@st.dialog("Daten bearbeiten",width="large")
def file_bearbeiten(files, DB):
    alle_zellen = DB.get_all_zells()
    alle_typen = DB.get_file_typs()
    for index, row in files.iterrows():
        st.divider()
        con = st.container()
        con.write(f"Datei {row['name']} bearbeiten:")
        info = con.text_input("Datei Infos", value=row["info"], key=index*5)
        col2, col3, col4, col5 = con.columns([3,3,2,2])
        cycle = col2.number_input("Zyklus", value=row["cycle"], min_value=0, step=1, key=index*5+1)
        ind1 = np.where(alle_zellen == row["zelle"])[0][0]
        zelle = col3.selectbox("Zellen eingeben", alle_zellen, index=int(ind1), key=index*5+2)
        ind2 = np.where(alle_typen == row["typ"])[0][0]
        typ = col4.selectbox("Typ", alle_typen, index=int(ind2), key=index*5+3)
        col5.subheader("")
        if col5.button("Bestätigen", type="primary", use_container_width=True, key=index*5+4):
            try:
                DB.insert_file(row["name"], cycle, info, zelle)
                st.rerun()
            except Exception as e:
                con.error(f"Fehler beim ändern der Daten: {e}")

def edit_data_app():
    st.title("Daten bearbeiten")
    DB = Database("Edit_Data")
    if DB is None:
        st.error("Keine Verbindung zur Datenbank")
        st.stop()
    con1 = st.container(border=True)
    data = DB.get_all_files()
    cycle, zelle = daten_filter(con1, data)
    typ = typ_filer(con1,data)
    data = pd.DataFrame()
    for zel in zelle:
        for cyc in cycle:
            for tp in typ:
                dat = DB.get_file(cyc, zel, tp)
                dat = pd.DataFrame(dat)
                if dat.empty:
                    continue
                data = pd.concat([data, dat], ignore_index=True)

    st.session_state.filter_files = data

    event = con1.dataframe(
        st.session_state.filter_files,
        key="data",
        on_select="rerun",
        selection_mode="multi-row",
    )
    selected_rows = st.session_state.filter_files.iloc[event.selection.rows]

    col1, col2 = con1.columns([1,4])
    if col1.button("Löschen", type="secondary", use_container_width=True):
        if selected_rows.empty:
            con1.warning("Keine Daten ausgewählt!")
        else:
            file_loeschen(selected_rows["name"],DB)
    if col2.button("Bearbeiten", type="primary", use_container_width=True):
        if selected_rows.empty:
            con1.warning("Keine Daten ausgewählt!")
        else:
            file_bearbeiten(selected_rows, DB)