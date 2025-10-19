import streamlit as st
import plotly.express as px
import pandas as pd
from src.auswertung import max_dev_to_median, robust_start_end_median, robust_start_end_abw, normiere_kurve
from classes.datenanalyse import Analyse
from classes.datenbank import Database
from src.filtern import daten_filter, soc_filer
from src.plotting_functions import colors

def eis_app():
    with st.sidebar:
        side = st.radio(
            "Wähle eine Option",
            ("Kurven", "Punkte", "Formierung")
        )
    if side == "Kurven":
        niqhist_app()
    elif side == "Punkte":
        points_app()
    else:
        form_app()

def points_app():
    st.title("Points")
    DB = Database("Points")
    alldata = DB.get_all_eis()
    con1 = st.container(border=True)
    cycle, zelle = daten_filter(con1, alldata)
    all_soc = DB.get_all_eis_soc()
    soc = soc_filer(con1, all_soc)
    filt_data = pd.DataFrame()
    spalten = ["datei", "soc", "zelle", "cycle", "datum"]
    if not cycle or not zelle:
        st.warning("Keine Werte ausgewählt")
    else:
        con1 = st.container(border=False)
        data = pd.DataFrame()
        for z in zelle:
            for c in cycle:
                file = DB.get_file(c, z, "EIS")
                if file.empty:
                    continue
                for s in soc:
                    cycle_data = DB.get_eis_points(file["name"].values[0],s)
                    cycle_data = pd.DataFrame(cycle_data)
                    if cycle_data.empty:
                        continue
                    filt_data = pd.concat([filt_data, cycle_data[spalten]])
                    data = pd.concat([data, cycle_data])

        con1.subheader("Ausgewählte Daten:")
        con1.write(filt_data)
        con1.subheader("Plots:")

        key = 0
        col1, col2 = con1.columns(2)
        options = ["SoC", "Zelle", "Zyklus"]
        selected = col1.segmented_control("Subplots",options,help="Wähle Wert aus der in einem Diagramm angezeigt wird",default=options[1])
        options = ["cycle","cap_cycle","soc"]
        x_values = col1.segmented_control("X-Achse", options,default=options[0])
        options = [col for col in data.columns if col not in ["datei", "cycle", "zelle", "datum", "soc"]]
        y_values = col2.selectbox("Y-Werte", options)
        graphs = col2.toggle("Alle Grafen in einem Plot")
        aus = col2.toggle("Ausreißer entfernen")
        if aus:
            gruppen = []
            for _, gruppe in data.groupby(['soc', 'zelle']):
                werte = gruppe[y_values]
                q1 = werte.quantile(0.25)
                q3 = werte.quantile(0.75)
                iqr = q3 - q1
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                erster = gruppe.iloc[[0]]

                gefiltert = gruppe.iloc[1:]
                gefiltert = gefiltert[(gefiltert[y_values] >= lower) & (gefiltert[y_values] <= upper)]

                gruppe_clean = pd.concat([erster, gefiltert])
                gruppen.append(gruppe_clean)
            data = pd.concat(gruppen, ignore_index=True)
        if not graphs:
            if selected == "SoC":
                plots = soc
                data = data.sort_values(by=["cycle"])
                plot_name = "soc"
                subplots = "zelle"
                einheit = "mAh"
            elif selected == "Zyklus":
                plots = zelle
                plot_name = "zelle"
                subplots = "cycle"
                einheit = "mAh"
            else:
                plots = zelle
                plot_name = "zelle"
                subplots = "soc"
                einheit = ""
        else:
            plots = ["allen ausgewählten Daten"]
            plot_name = ""
            data_mod = data
            subplots = "zelle"
            einheit = ""

        for p in plots:
            con2 = st.container(border=False)
            con2.divider()
            if not graphs:
                data_mod = data[data[plot_name] == p]
            if selected == "Zyklus":
                data_mod.sort_values("soc", inplace=True)
            name = f"{plot_name} {p} {einheit}"
            fig = plot_points(data_mod, name, x_values, y_values,subplots)
            con2.plotly_chart(fig)
            space, col2 = con2.columns([4, 1])
            key += 1

            con2.dataframe(data_mod)

def niqhist_app():
    st.title("EIS")
    DB = Database("EIS")
    alldata = DB.get_all_eis()
    con1 = st.container(border=True)
    cycle, zelle = daten_filter(con1, alldata)
    all_soc = DB.get_all_eis_soc()
    soc = soc_filer(con1, all_soc)
    filt_data = pd.DataFrame()
    spalten = ["datei", "soc", "zelle", "cycle", "datum"]
    if not cycle or not zelle:
        st.warning("Keine Werte ausgewählt")
    else:
        con1 = st.container(border=False)
        data = pd.DataFrame()
        data_list = []
        for z in zelle:
            for c in cycle:
                file = DB.get_file(c, z, "EIS")
                if file.empty:
                    continue
                for s in soc:
                    cycle_data = DB.get_eis_plots(file["name"].values[0], s)
                    cycle_data = pd.DataFrame(cycle_data)
                    if cycle_data.empty:
                        continue
                    filt_data = pd.concat([filt_data, cycle_data[spalten]])
                    data = pd.concat([data, cycle_data])
                    data_list.append(cycle_data)


        con1.subheader("Ausgewählte Daten:")
        con1.write(filt_data.drop_duplicates())
        if con1.button("Daten Aktualisieren", type="secondary", use_container_width=True,
                       help="Führt die Niqhist-Analyse ein weiteres mal durch um neue Datenpunkte hinzuzufügen"):
            DA = Analyse()
            DA.calc_niquist_data(data_list,True)
        con1.subheader("Plots:")

        key = 0
        col1, col2 = con1.columns(2)

        kHz = col2.toggle("2kHz anzeigen")
        tabels = col2.toggle("Tabellen anzeigen")
        graphs = col2.toggle("Alle Grafen in einem Plot")
        options = ["soc", "cycle","zelle"]
        big_plot = col1.segmented_control("Daten", options,
                                          help="Wähle Wert der einzelnen Diagramme",
                                          default=options[2],
                                          disabled=graphs)
        options = ["Niqhist", "Bode-Re", "Bode-Im", "Bode-Phase","Bode-Z"]
        plot = col1.segmented_control("Plots",options,default=options[0])
        if plot == "Niqhist":
            x_data = "calc_rezohm"
            y_data = "calc_imzohm"
            log_x = False
        elif plot == "Bode-Re":
            x_data = "freqhz"
            y_data = "calc_rezohm"
            log_x = True
        elif plot == "Bode-Im":
            x_data = "freqhz"
            y_data = "calc_imzohm"
            log_x = True
        elif plot == "Bode-Phase":
            x_data = "freqhz"
            y_data = "phasezdeg"
            log_x = True
        elif plot == "Bode-Z":
            x_data = "freqhz"
            y_data = "zohm"
            log_x = True

        if not graphs:
            if big_plot == "soc":
                plots = soc
                plot_name = "soc"
            elif big_plot == "cycle":
                plots = cycle
                plot_name = "cycle"
            elif big_plot == "zelle":
                plots = zelle
                plot_name = "zelle"

        else:
            plots = ["allen ausgewählten Daten"]
            data_mod = data
            plot_name = ""

        subplots = 'color'

        for p in plots:
            con2 = st.container(border=False)
            con2.divider()
            if not graphs:
                data_mod = data[data[plot_name] == p]
                if data_mod.empty:
                    continue
            data_mod['color'] = data_mod['zelle'].astype(str) + "_" + data_mod['cycle'].astype(str) + "_" + data_mod['soc'].astype(str)
            data_mod.sort_values(by=["datei","freqhz"], inplace=True)

            if not kHz:
                data_mod = data_mod[data_mod["freqhz"] != 1999]
            name = f"Niqhist plot von {p}"
            fig = plot_graphs(data_mod, name,subplots,x_data,y_data, log_x)
            con2.plotly_chart(fig)
            space, col2 = con2.columns([4, 1])
            key += 1
            if tabels:
                con2.dataframe(data_mod)

def form_app():
    st.title("Formierungs Analyse")
    DB = Database("form")
    eis = DB.get_all_eis_data()

    eis = eis.rename(columns={
        "calc_rezohm": "re",
        "calc_imzohm": "im",
        "phasezdeg": "phase",
        "zohm": "betrag"
    })
    eis["freqhz"] = eis["freqhz"].round(2)
    df_eis = eis.melt(
        id_vars=["freqhz", "soc", "zelle", "cycle"],
        value_vars=["re", "im", "phase", "betrag"],
        var_name="parameter",
        value_name="wert"
    )

    points = DB.get_all_eis_points()
    wert_spalten = ['im_max', 're_min', 're_max', 'im_min', 'phase_max', 'phase_min', 'im_zif', 'phase_zif', 'mpd',
                    'phase_184','phase_400','im_631', 'im_63','im_400','im_184','re_184', 're_400']
    df_points = points.melt(
        id_vars=['soc', 'zelle', 'cycle'],  # diese bleiben unverändert
        #value_vars=wert_spalten,  # diese Spalten werden umgeformt
        var_name='parameter',  # neue Spalte für den Parameternamen
        value_name='wert'  # neue Spalte für den Wert
    )
    df_match_eis = df_eis.drop(columns=["freqhz"])
    df_match_eis['parameter'] = df_eis['parameter'] + '_' + df_eis['freqhz'].astype(str)
    exclude = ['phase_200','phase_400','im_631', 'im_63','im_400','im_200','re_200', 're_400']
    df_match_points = df_points[~df_points['parameter'].isin(exclude)]
    df_all = pd.concat([df_match_points, df_match_eis])

    agg_funcs = {
        'wert': ['mean', 'std', 'median', 'min', 'max', max_dev_to_median]
    }

    ops = ['overall_freq','std_soc_freq','tab_zelle','plot_para_zelle','div_soc_cycle']
    sel1 = st.segmented_control("Plots wählen", options=ops, default=ops[0])
    df_match_points = df_match_points.dropna()
    if sel1 == 'overall_freq':
        plot_freq_overall(df_eis, agg_funcs)
    elif sel1 == 'std_soc_freq':
        plot_soc_freq(df_eis, agg_funcs)
    elif sel1 == 'tab_zelle':
        plot_tab_zelle(df_points)
    elif sel1 == 'plot_para_zelle':
        plot_para_zelle(df_points)
    elif sel1 == 'div_soc_cycle':
        div_soc_cycle(df_points)
    else:
        plot_tab_overall(df_points,df_match_eis,agg_funcs)

        #y: Abweichung, x: soc, plots für bestimte frequenzen z.B. phase 400hz

def plot_points(data, name,x_values, y_values, subplots):
    fig = px.line(data,
                  x=x_values,
                  y=y_values,
                  color=subplots,
                  title=f"{y_values} von {name}",
                  markers=True,
                  color_discrete_sequence=list(colors.values()),
                  )
    fig.update_layout(
        yaxis_title=y_values,
        xaxis_title=x_values,
        template='simple_white',
    )
    return fig

def plot_graphs(data, name, subplots, x, y, log):
    fig = px.line(data,
                  x=x,
                  y=y,
                  color=subplots,
                  log_x = True,
                  title=name,
                  markers=True,
                  color_discrete_sequence=list(colors.values()),
                  hover_data="freqhz"
                  )

    return fig

def plot_freq_overall(df_long,agg_funcs):
    # Gruppieren nach Frequenz und Parameter (soc und cycle fallen weg)
    df_eis = df_long.groupby(['freqhz', 'parameter']).agg(
        mittelwert=('wert', 'mean'),
        std=('wert', 'std'),
        median=('wert', 'median'),
        min=('wert', 'min'),
        max=('wert', 'max')
    ).reset_index()

    # Variationskoeffizient hinzufügen
    df_eis['cv'] = df_eis['std'] / df_eis['mittelwert']
    opt = ['re', 'im','phase','betrag']
    sel = st.segmented_control("Wert auswählen", options=opt, default=opt[0])
    df_long = df_long[df_long['parameter'] == sel]
    df_sorted = df_long.sort_values("soc")
    #for zelle in df_sorted['zelle'].unique():
    #df_plot = df_sorted[df_sorted['zelle'] == zelle]
    fig = px.box(df_sorted,
                 x="freqhz",
                 y='wert',
                 log_x=True,
                 color="zelle",
                 hover_data=["soc","cycle"],)
    st.plotly_chart(fig)
    st.write(df_eis)

def plot_soc_freq(df_long,agg_funcs):
    freq = df_long['zelle'].unique()
    sel2 = st.segmented_control("Zelle wählen",options=freq)
    opt = ['re', 'im','phase','betrag']
    sel3 = st.segmented_control("Wert auswählen", options=opt, default=opt[0])
    if sel2:
        df_para = df_long[df_long['parameter'] == sel3]
        df_freq= df_para[df_para['zelle'] == sel2]
        cycle = [0, 5,15,30,50]
        #soc = [500,1250,2000]
        df_sorted = df_freq[df_freq['cycle'].isin(cycle)]
        #df_sorted = df_freq[df_freq['soc'].isin(soc)]
        df_sorted = df_sorted.sort_values("soc")
        st.write(df_sorted)
        fig = px.box(df_sorted,
                     x="freqhz",
                     y='wert',
                     log_x=True,
                     color="cycle",
                     #color="soc",
                     hover_data=["soc", "cycle"], )
        st.plotly_chart(fig)
        df_eis = df_sorted.groupby(['freqhz', 'cycle']).agg(
        #df_eis=df_sorted.groupby(['freqhz', 'soc']).agg(
            mittelwert=('wert', 'mean'),
            std=('wert', 'std'),
            median=('wert', 'median'),
            min=('wert', 'min'),
            max=('wert', 'max')
        ).reset_index()
        opt2 = ['mittelwert','std','median','min','max']
        sel4 = st.segmented_control("Wert auswählen", options=opt2, default=opt2[0])
        fig = px.line(df_eis,
                      x="freqhz",
                      y=sel4,
                      log_x=True,
                      color="cycle"
                      #color = "soc",
        )
        st.plotly_chart(fig)
        st.write(df_eis)
        st.subheader("Differenz der Werte")
        if sel3 == 're':
            st.write("bei 5,4Hz")
            data = df_eis[df_eis['freqhz'].between(5, 6)]
            data.sort_values(by='cycle', inplace=True)
            st.write(data)
            res1 = pd.DataFrame([{
                "Zyklen": "0-5",
                "Start": data["std"].iloc[0]*1000,
                "Ende":  data["std"].iloc[1]*1000,
                "Diff": data["std"].iloc[1]*1000 - data["std"].iloc[0]*1000,
                "Diff/Zyklus": (data["std"].iloc[1] * 1000 - data["std"].iloc[0] * 1000)/5,
                "Diff/Zyklus in %": (data["std"].iloc[1] - data["std"].iloc[0]) / data["std"].iloc[0] / 5 * 100,
            }])
            res2 = pd.DataFrame([{
                "Zyklen": "30-50",
                "Start": data["std"].iloc[3] * 1000,
                "Ende": data["std"].iloc[4] * 1000,
                "Diff": data["std"].iloc[4] * 1000 - data["std"].iloc[3] * 1000,
                "Diff/Zyklus": (data["std"].iloc[4] * 1000 - data["std"].iloc[3] * 1000) / 20,
                "Diff/Zyklus in %": (data["std"].iloc[4] - data["std"].iloc[3]) / data["std"].iloc[3] / 20 * 100,
            }])
            st.write(pd.concat([res1,res2]))
        elif sel3 == 'im':
            st.write("bei 56Hz")
            data = df_eis[df_eis['freqhz'].between(56, 57)]
            res1 = pd.DataFrame([{
                "Zyklen": "0-5",
                "Start": data["std"].iloc[0]*1000,
                "Ende":  data["std"].iloc[1]*1000,
                "Diff": data["std"].iloc[1]*1000 - data["std"].iloc[0]*1000,
                "Diff/Zyklus": (data["std"].iloc[1] * 1000 - data["std"].iloc[0] * 1000)/5,
                "Diff/Zyklus in %": (data["std"].iloc[1] - data["std"].iloc[0]) / data["std"].iloc[0] / 5 * 100,
            }])
            res2 = pd.DataFrame([{
                "Zyklen": "30-50",
                "Start": data["std"].iloc[3] * 1000,
                "Ende": data["std"].iloc[4] * 1000,
                "Diff": data["std"].iloc[4] * 1000 - data["std"].iloc[3] * 1000,
                "Diff/Zyklus": (data["std"].iloc[4] * 1000 - data["std"].iloc[3] * 1000) / 20,
                "Diff/Zyklus in %": (data["std"].iloc[4] - data["std"].iloc[3]) / data["std"].iloc[3] / 20 * 100,
            }])
            st.write(pd.concat([res1,res2]))

def plot_tab_overall(df_long,df_eis,agg_funcs):
    df_overall = df_eis.groupby(['parameter']).agg(agg_funcs)
    df_overall.columns = ['mittelwert', 'std', 'median', 'min', 'max', 'max_abw_median']
    df_overall = df_overall.reset_index()
    df_overall['cv'] = abs(df_overall['std'] / df_overall['mittelwert'])
    df_min_cv = (
        df_overall.sort_values('cv', ascending=True)
    )
    df_min_med =  (
        df_overall.sort_values('max_abw_median', ascending=True)
    )
    df_combined = pd.concat([df_min_cv, df_min_med])
    df_combined = df_combined.drop_duplicates()

    df_long = df_long[~df_long['zelle'].isin(['U_VTC5A_007', 'JT_VTC_001', 'JT_VTC_002'])]
    df_agg = df_long.groupby(['parameter']).agg(agg_funcs)

    # Spaltennamen bereinigen
    df_agg.columns = ['mittelwert', 'std', 'median', 'min', 'max', 'max_abw_median']

    # Index zurücksetzen
    df_agg = df_agg.reset_index()
    df_agg['cv'] = abs(df_agg['std'] / df_agg['mittelwert'])
    df_combined =pd.concat([df_combined, df_agg])
    df_combined = df_combined.reset_index(drop=True)
    st.write(df_combined)

def plot_tab_zelle(df_all):
    zellen_dict = {zelle: df for zelle, df in df_all.groupby('zelle')}
    all_df = pd.DataFrame()
    con1 = st.container()
    for zelle in zellen_dict:
        con1.subheader(zelle)
        zelle_df = zellen_dict[zelle]
        zelle_df = zelle_df.drop(columns=['zelle'])
        gruppen = []
        #Filtern
        zelle_df = zelle_df.sort_values(by=['cycle'])
        for _, gruppe in zelle_df.groupby(['soc', 'parameter']):
            werte = gruppe["wert"]
            q1 = werte.quantile(0.25)
            q3 = werte.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            erster = gruppe.iloc[[0]]
            gefiltert = gruppe.iloc[1:]
            gefiltert = gefiltert[(gefiltert["wert"] >= lower) & (gefiltert["wert"] <= upper)]
            gruppe_clean = pd.concat([erster, gefiltert])

            anzahl_entfernt = len(werte) - len(gruppe_clean)
            gruppe_clean = gruppe_clean.assign(korrekturen=anzahl_entfernt)
            gruppen.append(gruppe_clean)
        zelle_df = pd.concat(gruppen, ignore_index=True)
        gruppen = [df for _, df in zelle_df.groupby(['soc', 'parameter'])]
        result1 = pd.DataFrame([{
            "soc": gruppe["soc"].iloc[0],
            "parameter": gruppe["parameter"].iloc[0],
            #"corections": gruppe["korrekturen"].iloc[0],
            "robust_median": robust_start_end_median(gruppe["wert"]),
            "mean": gruppe["wert"].mean(),
            "div": gruppe["wert"].iloc[-3:].median() - gruppe["wert"].iloc[0],
            "bis_median_0.05": robust_start_end_abw(gruppe,0.05),
            "bis_median_0.01": robust_start_end_abw(gruppe,0.01)
        } for gruppe in gruppen])
        gruppen = [df for _, df in result1.groupby('parameter')]
        result2 = pd.DataFrame([{
            "zelle": zelle,
            "parameter": gruppe["parameter"].iloc[0],
            #"corections": gruppe["corections"].sum(),
            "gesamt_delta_mean": gruppe[gruppe["soc"] == 1250]["robust_median"].iloc[0],
            "delta_soc": gruppe["mean"].max() - gruppe["mean"].min(),
            "div_20": gruppe[gruppe["soc"] == 500]["div"].values[0] if not gruppe[gruppe["soc"] == 500].empty else None,
            "div_50": gruppe[gruppe["soc"] == 1250]["div"].values[0] if not gruppe[gruppe["soc"] == 1250].empty else None,
            "div_80": gruppe[gruppe["soc"] == 2000]["div"].values[0] if not gruppe[gruppe["soc"] == 2000].empty else None,
            "gesamt_bis_median_0.05_20SOC": gruppe[gruppe["soc"] == 500]["bis_median_0.05"].values[0] if not gruppe[gruppe["soc"] == 500].empty else None,
            "gesamt_bis_median_0.01_20SOC": gruppe[gruppe["soc"] == 500]["bis_median_0.01"].values[0] if not gruppe[gruppe["soc"] == 500].empty else None,
            "gesamt_bis_median_0.05_50SOC": gruppe[gruppe["soc"] == 1250]["bis_median_0.05"].values[0] if not gruppe[gruppe["soc"] == 1250].empty else None,
            "gesamt_bis_median_0.01_50SOC": gruppe[gruppe["soc"] == 1250]["bis_median_0.01"].values[0] if not gruppe[gruppe["soc"] == 1250].empty else None,
            "gesamt_bis_median_0.05_80SOC": gruppe[gruppe["soc"] == 2000]["bis_median_0.05"].values[0] if not gruppe[gruppe["soc"] == 2000].empty else None,
            "gesamt_bis_median_0.01_80SOC": gruppe[gruppe["soc"] == 2000]["bis_median_0.01"].values[0] if not gruppe[gruppe["soc"] == 2000].empty else None,
        } for gruppe in gruppen])
        #mask = ~result2["parameter"].str.contains("phase", case=False, na=False)
        #result2.loc[mask, soc] = result2.loc[mask, soc].apply(lambda x: x * 1000)
        #result2[soc] = result2[soc].apply(lambda x: float(f"{x:.3g}"))
        con1.write(result2)
        latex_table = result2.to_latex(index=False, escape=False, decimal=",")
        con1.download_button(
            label="LaTeX-Tabelle herunterladen",
            data=latex_table,
            file_name=f"Form_{zelle}.tex",
            mime="text/plain"
        )
        all_df = pd.concat([all_df, result2])

    st.subheader("Zusammenfassung")
    soc = st.segmented_control("SOC_wählen",["div_20","div_50","div_80"],default="div_50")
    wide = all_df.pivot_table(
        index='parameter',
        columns='zelle',
        values=soc,
        aggfunc='first'
    ).sort_index()
    if 'JT_VTC_001' in wide.columns:
        wide = wide.drop(columns=['JT_VTC_001', 'JT_VTC_002'])
    wide = wide.reset_index()
    mask = ~wide["parameter"].str.contains("phase", case=False, na=False)
    wide.loc[mask, wide.columns != "parameter"] = wide.loc[mask, wide.columns != "parameter"] * 1000
    wide = wide.round(3)
    st.write(wide)

    latex_table = wide.to_latex(index=False, escape=False, decimal=",")
    st.download_button(
        label="LaTeX-Tabelle herunterladen",
        data=latex_table,
        file_name=f"Form_Zellen.tex",
        mime="text/plain"
    )

def plot_para_zelle(df_all):
    gruppen = []
    # Filtert Extremwerte raus
    df_all = df_all.sort_values(by=['cycle'])
    for _, gruppe in df_all.groupby(['zelle', 'soc', 'parameter']):
        werte = gruppe["wert"]
        q1 = werte.quantile(0.25)
        q3 = werte.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        erster = gruppe.iloc[[0]]
        gefiltert = gruppe.iloc[1:]
        gefiltert = gefiltert[(gefiltert["wert"] >= lower) & (gefiltert["wert"] <= upper)]
        gruppe_clean = pd.concat([erster, gefiltert])

        anzahl_entfernt = len(werte) - len(gruppe_clean)
        gruppe_clean = gruppe_clean.assign(korrekturen=anzahl_entfernt)
        gruppen.append(gruppe_clean)
    zelle_df = pd.concat(gruppen, ignore_index=True)

    opt1 = [500, 1250, 2000]
    soc = st.segmented_control("SOC auswählen", options=opt1, default=opt1[0])
    data_df = zelle_df[zelle_df["soc"] == soc]

    opt2 = ["wert", "wert_norm", 'div']
    wert = st.segmented_control("SOC auswählen", options=opt2, default=opt2[0])

    for para in data_df['parameter'].unique():
        st.write(para)
        plot_df = data_df[data_df['parameter'] == para]
        gruppen = [df for _, df in plot_df.groupby('zelle')]
        norm_df = pd.DataFrame()
        for gruppe in gruppen:
            first = gruppe.iloc[0]['wert']
            gruppe['wert_norm'] = gruppe['wert'] / first
            gruppe['div'] = gruppe['wert'] - first
            norm_df = pd.concat([norm_df, gruppe])
        norm_df = norm_df.sort_values('cycle')
        fig = px.line(norm_df,
                      x="cycle",
                      y=wert,
                      color="zelle")
        if wert == "wert_norm":
            fig.update_yaxes(range=[0.5, 1.5])
        st.plotly_chart(fig)

def div_soc_cycle(df_all):
    gruppen = []
    # Filtert Extremwerte raus
    df_all = df_all.sort_values(by=['cycle'])

    soc = [500, 1250, 2000]
    data_df = df_all[df_all["soc"].isin(soc)]
    opt1 = data_df['zelle'].unique()
    zelle = st.segmented_control("Zelle wählen", options=opt1, default=opt1[0])
    data_df = data_df[data_df["zelle"] == zelle]
    opt2 = ["wert", "wert_norm", 'div']
    wert = st.segmented_control("SOC auswählen", options=opt2, default=opt2[0])

    for para in data_df['parameter'].unique():
        st.write(para)
        plot_df = data_df[data_df['parameter'] == para]
        gruppen = [df for _, df in plot_df.groupby('soc')]
        norm_df = pd.DataFrame()
        for gruppe in gruppen:
            first = gruppe.iloc[0]['wert']
            gruppe['wert_norm'] = gruppe['wert'] / first
            gruppe['div'] = gruppe['wert'] - first
            norm_df = pd.concat([norm_df, gruppe])
        norm_df = norm_df.sort_values('cycle')
        fig = px.line(norm_df,
                      x="cycle",
                      y=wert,
                      color="soc")
        if wert == "wert_norm":
            fig.update_yaxes(range=[0.5, 1.5])
        st.plotly_chart(fig)
        st.write(norm_df)
    gruppen = []