import plotly.express as px
import streamlit as st
import pandas as pd
import numpy as np

from classes.datenbank import Database
import plotly.graph_objects as go
from scipy.optimize import curve_fit

from src.auswertung import robust_start_end_median, robust_start_end_theo_median


def lup_app():
    with st.sidebar:
        side = st.radio(
            "Wähle eine Option",
            ("Table", "Formierung", "Fit")
        )
    if side == "Table":
        table_app()
    elif side == "Formierung":
        deis_form_app()
    else:
        fit_app()

def table_app():
    # Zeigt Look-Up-Tabelle an
    st.title("Creat Look-Up-Table")
    # Objekt der Klasse DAtanbank erstellem
    DB = Database("lup")
    # Daten abrufen
    df = DB.get_lup()
    df['calc_soc'] = df['soc']/2500 + 0.1
    plots = ['phasezdeg', 'calc_rezohm', 'calc_imzohm']

    # Daten Filtern
    data_df = df[df["calc_ima"]==1250]
    data_df = data_df[data_df["freqhz"].between(195, 205)]
    data_df["temperaturec_cat"] = data_df["temperaturec"].astype(str)
    data_df = data_df.sort_values("soc")
    for plot in plots:
        st.subheader(plot + ' 200 Hz')
        fig = px.scatter(data_df,
                        x='calc_soc',
                        y=plot,
                        color='temperaturec_cat',
                        hover_data=["datei"],
                        symbol="temperaturec_cat",
                         )
        st.plotly_chart(fig)
    show_data = data_df[[
        "freqhz", "zohm", "temperaturec", "phasezdeg",
        "calc_rezohm", "calc_imzohm", "soc", "temperaturec_cat", "calc_soc"
    ]].copy()
    show_data.sort_values(["temperaturec_cat","calc_soc"])
    st.write(show_data)

def deis_form_app():
    # Zeigt Formierung der DEIS-Werte an
    st.title("Formierungs Data")
    #Erstellt Objekt der Klasse ADtenbank
    DB = Database("lup")
    # Daten Abrufen
    df = DB.get_deis()
    df['calc_soc'] = df['soc']/2500
    #theo_cycle erstellen
    df['theo_cycle'] = np.select(
        [
            df['zelle'].isin(['JT_VTC_003', 'JT_VTC_006', 'JT_VTC_010']),
            df['zelle'].isin(['JT_VTC_004', 'JT_VTC_007', 'JT_VTC_009'])
        ],
        [
            df['cycle'] * 0.6,
            df['cycle'] * 0.8
        ],
        default=df['cycle']
    )
    plots = ['phasezdeg', 'calc_rezohm', 'calc_imzohm','zohm']
    df = df.sort_values(["zelle","soc","calc_ima","cycle"])

    st.write(df)
    dia = st.segmented_control('Diagramme', ['SOC', 'Zyklen', 'Zyklen-mittel'])
    if dia == 'SOC':
        # Entwicklung der Parameter über SOC
        # Daten weiter filtern
        data_df = df[df[("zelle")] == ('JT_VTC_008')]
        data_df = data_df[data_df["calc_ima"] == 1250]
        data_df = data_df.sort_values(["soc", "cycle"])
        for plot in plots:
            st.subheader(plot + ' 200 Hz')
            fig = px.line(data_df,
                            x='calc_soc',
                            y=plot,
                            color='cycle',
                            )
            st.plotly_chart(fig)
    elif dia == 'Zyklen':
        #Entwicklung der Parameter einzelner Zellen
        # Diese Seite muss vor der Fit Seite geöffnet werden
        socs = [0.2,0.5,0.8]
        data_df = df[df["calc_ima"]==2500]
        soc = st.segmented_control("SOC wählen", socs, default=socs[0])
        x_tog = st.toggle("Theoretische Zyklenzahl")
        x_val = 'cycle' if not x_tog else 'theo_cycle'
        data_df = data_df[data_df["calc_soc"]== soc]
        data_df = data_df.sort_values(["zelle","soc","cycle"])
        # Initialer Mittelwert der Zellen
        inital = data_df[data_df["cycle"]==0]
        inital_mean = pd.DataFrame([{
            "phasezdeg": inital["phasezdeg"].mean(),
            "calc_rezohm": inital["calc_rezohm"].mean(),
            "calc_imzohm": inital["calc_imzohm"].mean(),
            "zohm": inital["zohm"].mean(),
        }])
        for plot in plots:
            st.subheader(plot + ' 200 Hz')
            fig = px.line(data_df,
                            x=x_val,
                            y=plot,
                            color='zelle',
                           hover_data=['cycle', 'theo_cycle'],
                            )
            st.plotly_chart(fig)
            gruppen = [daf for _, daf in data_df.groupby(['soc','zelle'])]
            # Wenn initialwert Fehlt, Mittelwert der Anderen Zellen verwenden
            result1 = pd.DataFrame([{
                "soc": gruppe["soc"].iloc[0],
                "zelle": gruppe["zelle"].iloc[0],
                **(
                    {
                        "robust_start_end_median": robust_start_end_median(gruppe[plot]),
                        "robust_start_theo_median": robust_start_end_theo_median(gruppe[plot],gruppe["zelle"].iloc[0]),
                        "div": gruppe[plot].iloc[:-3].median() - gruppe[plot].iloc[0],
                        "mean": gruppe[plot].mean(),
                    }
                    if (gruppe["cycle"] == 0).any()
                    else {
                        "robust_start_end_median": robust_start_end_median(pd.concat([inital_mean[plot],gruppe[plot]])),
                        "robust_start_theo_median": robust_start_end_theo_median(pd.concat([inital_mean[plot], gruppe[plot]]),gruppe["zelle"].iloc[0]),
                        "div": gruppe[plot].iloc[:-3].median() - inital_mean[plot].iloc[0],
                        "mean": pd.concat([gruppe[plot],inital_mean[plot]]).mean(),
                    }
                )
            } for gruppe in gruppen])
            st.write(result1)

        #Tabelle aufbauen
        data_df = df[df["calc_soc"].isin(socs)]
        gruppen = [daf for _, daf in data_df.groupby(['soc', 'calc_ima','zelle'])]
        result2 = pd.DataFrame([{
            "soc": gruppe["soc"].iloc[0],
            "ima": gruppe["calc_ima"].iloc[0],
            "zelle": gruppe["zelle"].iloc[0],
            **(
                {
                    "abw_phase": robust_start_end_median(gruppe["phasezdeg"]),
                    "abw_re": robust_start_end_median(gruppe["calc_rezohm"]),
                    "abw_im": robust_start_end_median(gruppe["calc_imzohm"]),
                    "abw_abs": robust_start_end_median(gruppe["zohm"]),
                    "abw_phase_theo": robust_start_end_theo_median(gruppe["phasezdeg"], gruppe["zelle"].iloc[0]),
                    "abw_re_theo": robust_start_end_theo_median(gruppe["calc_rezohm"], gruppe["zelle"].iloc[0]),
                    "abw_im_theo": robust_start_end_theo_median(gruppe["calc_imzohm"], gruppe["zelle"].iloc[0]),
                    "abw_abs_theo": robust_start_end_theo_median(gruppe["zohm"], gruppe["zelle"].iloc[0]),
                }
                if (gruppe["cycle"] == 0).any()
                else {
                    "abw_phase": robust_start_end_median(pd.concat([inital_mean["phasezdeg"], gruppe["phasezdeg"]])),
                    "abw_re": robust_start_end_median(pd.concat([inital_mean["calc_rezohm"], gruppe["calc_rezohm"]])),
                    "abw_im": robust_start_end_median(pd.concat([inital_mean["calc_imzohm"], gruppe["calc_imzohm"]])),
                    "abw_abs": robust_start_end_median(pd.concat([inital_mean["zohm"], gruppe["zohm"]])),
                    "abw_phase_theo": robust_start_end_theo_median(pd.concat([inital_mean["phasezdeg"], gruppe["phasezdeg"]]), gruppe["zelle"].iloc[0]),
                    "abw_re_theo": robust_start_end_theo_median(pd.concat([inital_mean["calc_rezohm"], gruppe["calc_rezohm"]]), gruppe["zelle"].iloc[0]),
                    "abw_im_theo": robust_start_end_theo_median(pd.concat([inital_mean["calc_imzohm"], gruppe["calc_imzohm"]]), gruppe["zelle"].iloc[0]),
                    "abw_abs_theo": robust_start_end_theo_median(pd.concat([inital_mean["zohm"], gruppe["zohm"]]), gruppe["zelle"].iloc[0]),
                }
            )
        } for gruppe in gruppen])

        #Darstellung der Abweichungen pro Zelle
        st.subheader("Abweichung Zellen")
        dat2 = result2[result2["ima"] == 2500]
        dat2 = dat2[dat2["soc"] == 1250]
        dat2.drop(columns=["ima","soc"], inplace=True)
        dat2 = dat2.round(3)
        st.write(dat2)
        latex_table = dat2.to_latex(index=False, escape=False, decimal=",")
        st.download_button(
            label="LaTeX-Tabelle herunterladen",
            data=latex_table,
            file_name=f"Form_DEIS_Zellen.tex",
            mime="text/plain"
        )

        #Darstellung der Gemittelten werte fpr unterschiedliche C-Raten während der Messung
        gruppen = [daf for _, daf in result2.groupby(['soc', 'ima'])]
        result3 = pd.DataFrame([{
            "ima": gruppe["ima"].iloc[0],
            "soc": gruppe["soc"].iloc[0],
            "abw_phase": gruppe["abw_phase"].mean(),
            "abw_re": gruppe["abw_re"].mean(),
            "abw_im": gruppe["abw_im"].mean(),
            "abw_abs": gruppe["abw_abs"].mean(),
        } for gruppe in gruppen])
        st.subheader("Abweichung alle")
        st.write(result3)
        result3 = result3.round(3)
        result3 = result3.sort_values(by=['ima'])
        latex_table = result3.to_latex(index=False, escape=False, decimal=",")
        st.download_button(
            label="LaTeX-Tabelle herunterladen",
            data=latex_table,
            file_name=f"Form_DEIS.tex",
            mime="text/plain"
        )
        #Abweichungen in der Session speichern für Exponentielle Fits
        st.session_state["Abweichung"] = result3
    elif dia == 'Zyklen-mittel':
        #Streung der Zellen bei 3 SOCs über Zyklen
        data_df = df[df["cycle"] <= 50]
        socs = [0.2,0.5,0.8]
        data_df = data_df.sort_values(["zelle", "soc", "cycle"])
        data_df = data_df[data_df["calc_soc"].isin(socs)]
        for plot in plots:
            st.subheader(plot + ' 200 Hz')
            fig = px.box(data_df,
                         x="cycle",
                         y=plot,
                         color="soc",
                         )
            st.plotly_chart(fig)
            gruppen = [df for _, df in data_df.groupby(['cycle','soc','calc_ima'])]
            result1 = pd.DataFrame([{
                "soc": gruppe["soc"].iloc[0],
                "cycle": gruppe["cycle"].iloc[0],
                "ima": gruppe["calc_ima"].iloc[0],
                "median": gruppe[plot].median(),
                "std": gruppe[plot].std() if gruppe[plot].std() is not None else 0,
                "max": gruppe[plot].max(),
                "min": gruppe[plot].min(),
            } for gruppe in gruppen])
            result1 = result1.sort_values("cycle")
            gruppen = [df for _, df in result1.groupby(['soc'])]
            result2 = pd.DataFrame([{
                "soc": gruppe["soc"].iloc[0],
                "Abweichung": robust_start_end_median(gruppe["median"]),
                "div": gruppe["median"].iloc[:-3].median() - gruppe["median"].iloc[0],
            } for gruppe in gruppen])
            st.write(result2)


def fit_app():
    # App um exponentielle Fits zu erstellen und Abweichungen in Grad zu berechnen
    # Formierung-App muss forher geöffnet werden
    st.title("Fit Data")
    # Daten abrugen
    DB = Database("lup")
    df = DB.get_lup()
    df['calc_soc'] = round(df['soc']/ 2500 + 0.1,2)

    unique_ima = df["calc_ima"].unique()
    data_df = df[df["freqhz"].between(195, 205)]
    gruppen = [df for _, df in data_df.groupby('temperaturec')]
    mean = pd.DataFrame([{
        "temperaturec": gruppe["temperaturec"].iloc[0],
        "phasezdeg": gruppe["phasezdeg"].mean(),
        "calc_rezohm": gruppe["calc_rezohm"].mean(),
        "calc_imzohm":gruppe["calc_imzohm"].mean(),
        "zohm": gruppe["zohm"].mean(),
    } for gruppe in gruppen])
    plots = ['abw_phase', 'abw_re', 'abw_im','abw_abs']
    pl1 = st.segmented_control('Daten wählen', plots, default=plots[0])
    match pl1:
        case "abw_phase":
            pl = 'phasezdeg'
        case "abw_re":
            pl = 'calc_rezohm'
        case "abw_im":
            pl= 'calc_imzohm'
        case "abw_abs":
            pl = 'zohm'
    ima = st.segmented_control('Stom wählen', unique_ima, default=unique_ima[0])
    con1 = st.container()
    col1, coln2, soc2 = con1.columns(3)
    # Abweichungen aus Sessionstate holen
    if "Abweichung" in st.session_state:
        state = st.session_state["Abweichung"]
        state = state[state["ima"]==ima]
        abw_2 = state[state['soc'] == 500][pl1].values[0] if not state[state['soc'] == 500].empty else 0
        abw_5 = state[state['soc'] == 1250][pl1].values[0] if not state[state['soc'] == 500].empty else 0
        abw_8 =  state[state['soc'] == 2000][pl1].values[0] if not state[state['soc'] == 500].empty else 0
    else:
        st.error("Abweichung nicht gefund! --> Erst Seite Formierung öffnen")
        abw_2 = 0
        abw_5 = 0
        abw_8 = 0
    # Zahleninputs  und container für Ergebnisse erstellen
    col1.write("Delta 0.2 SOC")
    div_2 = coln2.number_input("0.2",label_visibility="collapsed",value=abw_2)
    col1, coln2, soc5 = con1.columns(3)
    col1.write("Delta 0.5 SOC")
    div_5 = coln2.number_input("0.5",label_visibility="collapsed",value=abw_5)
    col1, coln2, soc8 = con1.columns(3)
    col1.write("Delta 0.8 SOC")
    div_8 = coln2.number_input("0.8",label_visibility="collapsed",value=abw_8)
    col1, colmean = con1.columns([1,3])
    col1.write("Abweichung ohne SOC-Input")
    # Figure erstellen, damit später plots eingwfügt werden können
    fig = go.Figure()
    fits = pd.DataFrame()
    socs = [0.2, 0.5, 0.8,'mean']

    # Exponentialfunkion definieren
    def func(x, a, b, c):
        return a * np.exp(b * x) + c

    # Inverse Funkton definieren
    def inv_x(y, a, b, c):
        return (1 / b) * np.log((y - c) / a)

    for soc in socs:
        if soc == 'mean':
            x = mean['temperaturec']
            y = mean[pl]
        else:
            dat = data_df[data_df["calc_soc"]== soc]
            dat = dat[dat["calc_ima"] == ima]
            x =  dat['temperaturec']
            y =  dat[pl]

        # Kurve fitten
        params, _ = curve_fit(func, x, y,p0=(100, -0.1, 3), maxfev=10000)
        a, b,c = params
        # x und y-Werte der Fits berechnen
        x_fit = np.linspace(min(x), max(x), 100)
        y_fit = func(x_fit, a, b,c)
        # Plots in Grafik einfügen
        fig.add_trace(go.Scatter(
            x=x,
            y=y,
            mode='markers',
            name=f'SOC: {soc}',
        ))
        fig.add_trace(go.Scatter(
            x=x_fit,
            y=y_fit,
            mode='lines',
            name='Fit',
        ))
        fit = pd.DataFrame({
            'temperatur': x_fit,
            'wert': y_fit,
            'soc': soc,
            'parameter': pl}
        )
        fits = pd.concat([fits, fit])

        inital = inv_x(y_fit[0], a, b,c)
        # Ergebnisse in Richtigen Container eintragen
        match soc:
            case 0.2:
                wert = inital - inv_x((1+div_2) * y_fit[0], a, b,c)
                soc2.write(f'Abweichung {wert} Grad')
            case 0.5:
                wert = inital - inv_x((1+div_5) * y_fit[0], a, b, c)
                soc5.write(f'Abweichung {wert} Grad')
            case 0.8:
                wert = inital - inv_x((1+div_8) * y_fit[0], a, b, c)
                soc8.write(f'Abweichung {wert} Grad')
            case 'mean':
                wert2 = inital - inv_x((1+div_2) * y_fit[0], a, b, c)
                wert5 = inital - inv_x((1 + div_5) * y_fit[0], a, b, c)
                wert8 = inital - inv_x((1 + div_8) * y_fit[0], a, b, c)
                colmean.write(f'Abweichung 20% --> {wert2} Grad \n')
                colmean.write(f'Abweichung 50% -->  {wert5} Grad \n')
                colmean.write(f'Abweichung 80% --> {wert8} Grad \n')

    st.plotly_chart(fig)
    show_data = data_df[[
        "freqhz", "zohm", "temperaturec", "phasezdeg",
        "calc_rezohm", "calc_imzohm", "soc", "calc_soc"
    ]].copy()
    show_data['calc_soc'] = show_data['calc_soc'] *100
    st.write(show_data)
    st.subheader('Fits')
    fits['soc'] = fits['soc']*100
    st.write(fits)