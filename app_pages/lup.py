import plotly.express as px
import streamlit as st
import pandas as pd
import numpy as np

from classes.datenbank import Database
import plotly.graph_objects as go
from scipy.optimize import root, curve_fit

from src.auswertung import robust_start_end_median


def lup_app():
    with st.sidebar:
        side = st.radio(
            "Wähle eine Option",
            ("Table", "Formierung", "Fit")
        )
    if side == "Table":
        table_app()
    elif side == "Formierung":
        form_app()
    else:
        fit_app()

def table_app():
    st.title("Creat Look-Up-Table")
    DB = Database("lup")
    df = DB.get_lup()
    df['calc_soc'] = df['soc']/2500 + 0.1
    plots = ['phasezdeg', 'calc_rezohm', 'calc_imzohm']

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

def form_app():
    st.title("Formierungs Data")
    DB = Database("lup")
    df = DB.get_deis()
    df['calc_soc'] = df['soc']/2500
    plots = ['phasezdeg', 'calc_rezohm', 'calc_imzohm','zohm']
    df = df.sort_values(["zelle","soc","calc_ima","cycle"])
    st.write(df)
    data_df = df[df[("zelle")]==('JT_VTC_008')]
    data_df = data_df[data_df["calc_ima"]==1250]
    data_df = data_df.sort_values(["soc","cycle"])
    dia = st.segmented_control('Diagramme', ['SOC', 'Zyklen', 'Zyklen-mittel'])
    if dia == 'SOC':
        for plot in plots:
            st.subheader(plot + ' 200 Hz')
            fig = px.line(data_df,
                            x='calc_soc',
                            y=plot,
                            color='cycle',
                            )
            st.plotly_chart(fig)
    elif dia == 'Zyklen':
        socs = [0.2,0.5,0.8]
        data_df = df[df["calc_ima"]==1250]
        soc = st.segmented_control("SOC wählen", socs, default=socs[0])
        data_df = data_df[data_df["calc_soc"]== soc]
        data_df = data_df.sort_values(["zelle","soc","cycle"])
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
                            x='cycle',
                            y=plot,
                            color='zelle',
                            )
            st.plotly_chart(fig)
            gruppen = [daf for _, daf in data_df.groupby(['soc','zelle'])]
            result1 = pd.DataFrame([{
                "soc": gruppe["soc"].iloc[0],
                "zelle": gruppe["zelle"].iloc[0],
                **(
                    {
                        "robust_start_end_median": robust_start_end_median(gruppe[plot]),
                        "div": gruppe[plot].iloc[:-3].median() - gruppe[plot].iloc[0],
                        "mean": gruppe[plot].mean(),
                    }
                    if (gruppe["cycle"] == 0).any()
                    else {
                        "robust_start_end_median": robust_start_end_median(pd.concat([inital_mean[plot],gruppe[plot]])),
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
                }
                if (gruppe["cycle"] == 0).any()
                else {
                    "abw_phase": robust_start_end_median(pd.concat([inital_mean["phasezdeg"], gruppe["phasezdeg"]])),
                    "abw_re": robust_start_end_median(pd.concat([inital_mean["calc_rezohm"], gruppe["calc_rezohm"]])),
                    "abw_im": robust_start_end_median(pd.concat([inital_mean["calc_imzohm"], gruppe["calc_imzohm"]])),
                    "abw_abs": robust_start_end_median(pd.concat([inital_mean["zohm"], gruppe["zohm"]])),
                }
            )
        } for gruppe in gruppen])

        gruppen = [daf for _, daf in result2.groupby(['soc', 'ima'])]
        result3 = pd.DataFrame([{
            "ima": gruppe["ima"].iloc[0],
            "soc": gruppe["soc"].iloc[0],
            "abw_phase": gruppe["abw_phase"].mean(),
            "abw_re": gruppe["abw_re"].mean(),
            "abw_im": gruppe["abw_im"].mean(),
            "abw_abs": gruppe["abw_abs"].mean(),
        } for gruppe in gruppen])
        st.subheader("Abweichung")
        st.write(result3)
        result3 = result3.sort_values(by=['ima'])
        if st.button("result.latex", use_container_width=True):
            tec = result3.to_latex(index=False)
            st.markdown(tec, unsafe_allow_html=True)
        st.session_state["Abweichung"] = result3
    elif dia == 'Zyklen-mittel':
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
    st.title("Fit Data")
    DB = Database("lup")
    df = DB.get_lup()
    df['calc_soc'] = round(df['soc']/ 2500 + 0.1,2)

    unique_ima = df["calc_ima"].unique()
    data_df = df[df["freqhz"].between(195, 205)]
    socs = [0.2, 0.5, 0.8]
    data_df = data_df[data_df["calc_soc"].isin(socs)]
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
    if "Abweichung" in st.session_state:
        state = st.session_state["Abweichung"]
        state = state[state["ima"]==ima]
        st.write(state)
        abw_2 = state[state['soc'] == 500][pl1].values[0] if not state[state['soc'] == 500].empty else 0
        abw_5 = state[state['soc'] == 1250][pl1].values[0] if not state[state['soc'] == 500].empty else 0
        abw_8 =  state[state['soc'] == 2000][pl1].values[0] if not state[state['soc'] == 500].empty else 0

    col1.write("Delta 0.2 SOC")
    div_2 = coln2.number_input("0.2",label_visibility="collapsed",value=abw_2)
    col1, coln2, soc5 = con1.columns(3)
    col1.write("Delta 0.5 SOC")
    div_5 = coln2.number_input("0.5",label_visibility="collapsed",value=abw_5)
    col1, coln2, soc8 = con1.columns(3)
    col1.write("Delta 0.8 SOC")
    div_8 = coln2.number_input("0.8",label_visibility="collapsed",value=abw_8)
    fig = go.Figure()
    fits = pd.DataFrame()
    for soc in socs:
        dat = data_df[data_df["calc_soc"]== soc]
        dat = dat[dat["calc_ima"] == ima]
        x = dat['temperaturec']
        y = dat[pl]
        def func(x, a, b,c):
            return a * np.exp( b * x) + c

        params, _ = curve_fit(func, x, y,p0=(100, -0.1, 3), maxfev=10000)
        a, b,c = params
        x_fit = np.linspace(min(x), max(x), 100)
        y_fit = func(x_fit, a, b,c)
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
        def inv_x(y, a, b, c):
            return (1 / b) * np.log((y - c) / a)
        inital = inv_x(y_fit[0], a, b,c)
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