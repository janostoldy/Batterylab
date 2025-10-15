import streamlit as st
from galvani import BioLogic

from classes.datenbank import Database
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy.spatial import cKDTree
from scipy.interpolate import griddata, interp1d
from scipy.signal import savgol_filter
from src.plotting_functions import colors_short

def basytec_app():
    with st.sidebar:
        side = st.radio(
            "Wähle eine Option",
            ("Berechnen", "Anpassen","Vergleichen")
        )
    if side == "Berechnen":
        berechnen_app()
    elif side == "Anpassen":
        anpassen_app()
    else:
        vergleichen_app()

def berechnen_app():
    st.title("Basytec - Calc")
    DB = Database("Impedanz")

    files = DB.get_imp_files()
    data = []
    c_rates = []
    for f in files.itertuples(index=False):
        c_rate = DB.get_imp_rate(f.name)
        for c in c_rate:
            if float(c[0]) not in c_rates:
                c_rates.append(float(c[0]))
            row = f._asdict()
            row["c_rate"] = float(c[0])
            data.append(row)
    df = pd.DataFrame(data)
    st.write(df)
    colums = ["time", "voltage", "current", "temp", "delta_cap", "c_rate", "re", "im", "phase", "freq",
              "datei", "typ"]
    imp_data = pd.DataFrame()
    for plt in df.itertuples(index=False):
        data = DB.get_impedanz(plt.name,plt.c_rate)
        if data[0].typ == "Basytec":
            min_time = min(row.time for row in data)
            filtered_rows = [row for row in data if row.time == min_time]
        else:
            filtered_rows = data
        filtered_df = pd.DataFrame(filtered_rows, columns=colums)
        filtered_df = filtered_df.sort_values('freq')
        imp_data = pd.concat([imp_data, filtered_df], ignore_index=True)
        imp_data["c_rate"] = pd.to_numeric(imp_data["c_rate"], errors="coerce")

    imp_data = imp_data.drop(imp_data[(imp_data["typ"] == "Biologic") & (imp_data["freq"] == 1001.9983)].index)
    con1 = st.container(border=False)

    col1, col2 = con1.columns(2)
    options = ["Niqhist", "Bode-Re", "Bode-Im", "Bode-Phase","Basy"]
    plot = col1.segmented_control("Plots", options, default=options[0])
    col2_1 ,col2_2 = col2.columns(2)
    fmin = col2_1.number_input("F_min",0,2000)
    fmax = col2_2.number_input("F_max",0,2000)
    cut = col2.toggle("Niedrige und Hohe Frequenzen schneiden")
    dis = False if plot != "Basy" else True
    calc = col1.toggle("Calc_Field", disabled=dis)
    lut_impedanz = pd.DataFrame()
    options = ["Setup", "C-Rate"]
    subplot = col1.segmented_control("Subplots", options, default=options[0])

    if calc or dis:
        for c in c_rates:
            data = imp_data[imp_data["c_rate"] == c]
            data = data[data["freq"] <= 1900]
            basy = data[data["typ"] == "Basytec"]
            biol = data[data["typ"] == "Biologic"]

            re_f_basy = interp1d(basy["freq"], basy["re"],kind='quadratic', fill_value='extrapolate')
            re_f_biol = interp1d(biol["freq"], biol["re"],kind='quadratic', fill_value='extrapolate')
            im_f_basy = interp1d(basy["freq"], basy["im"], kind='quadratic', fill_value='extrapolate')
            im_f_biol = interp1d(biol["freq"], biol["im"], kind='quadratic', fill_value='extrapolate')

            x_common = np.linspace(min(basy["freq"].min(), biol["freq"].min()),max(basy["freq"].max(), biol["freq"].max()),200)

            re_inter_basy = re_f_basy(x_common)
            re_inter_biol = re_f_biol(x_common)
            im_inter_basy = im_f_basy(x_common)
            im_inter_biol = im_f_biol(x_common)

            Z_basy = re_inter_basy + 1j * im_inter_basy
            Z_biol = re_inter_biol + 1j * im_inter_biol

            Y_total = 1 / Z_basy - 1 / Z_biol
            Z_total = 1 / Y_total

            re_diff = Z_total.real
            im_diff = Z_total.imag
            ph_diff = np.arctan2(im_diff, re_diff)

            diff_frame = pd.DataFrame({
                "time": 0,
                "voltage": 0,
                "current": 2.9*c,
                "temp": 26,
                "delta_cap": 0,
                "c_rate": c,
                "re": re_diff,
                "im": im_diff,
                "phase": ph_diff,
                "freq": x_common,
                "datei": "Berechnet",
                "typ": "calc"
            })
            lut_data = pd.DataFrame({
                "c_rate": c,
                "re": re_diff,
                "im": im_diff,
                "phase": ph_diff,
                "freq": x_common,
            })
            lut_impedanz = pd.concat([lut_impedanz, lut_data], ignore_index=True)
            imp_data = pd.concat([imp_data, diff_frame], ignore_index=True)

    if cut:
        imp_data = imp_data[imp_data["freq"] <= fmax]
        imp_data = imp_data[imp_data["freq"] >= fmin]
        lut_impedanz = lut_impedanz[lut_impedanz["freq"] <= fmax]
        lut_impedanz = lut_impedanz[lut_impedanz["freq"] >= fmin]

    if plot == "Niqhist":
        x_data = "re"
        y_data = "im"
    elif plot == "Bode-Re":
        x_data = "freq"
        y_data = "re"
    elif plot == "Bode-Im":
        x_data = "freq"
        y_data = "im"
    elif plot == "Bode-Phase":
        x_data = "freq"
        y_data = "phase"
    elif plot == "Basy":
        if con1.button("In DB speichern", type='secondary', use_container_width=True):
            DB.df_in_DB(lut_impedanz,'basytec')
        plot_basy(lut_impedanz)
        con = st.container()
        con.subheader("Ersatzschaltbild")
        con.image("src/pic/basytec.png")
        subplot = "Pass"

    if subplot == "Setup":
        plot_c_rates(imp_data, x_data, y_data, c_rates)
    elif subplot == "C-Rate":
        plot_typ(imp_data, x_data, y_data)

def anpassen_app():
    st.title("Biologic - Anpassen")
    DB = Database("Comp")
    col1, col2 = st.columns(2)

    col1.subheader("Daten-Basytec:")
    xcts = DB.get_impedanz_basy()
    xcts.drop(['voltage', 'current', 'delta_cap', 'phase', 'datei', 'typ'], axis=1, inplace=True)
    basy_dfs = [subdf.reset_index(drop=True) for _, subdf in xcts.groupby("c_rate")]
    for rate in basy_dfs:
        t_start = rate["time"].min()
        rate['qcharge'] = (rate['time']-t_start+1) * rate['c_rate'] * 2900 / 3600
        with col1.expander(f"C-Rate {rate['c_rate'][0]}"):
            st.write(rate)

    col2.subheader("Biologic:")
    bio = DB.get_impedanz_bio()
    bio.drop(['voltage', 'current', 'delta_cap', 'phase', 'datei', 'typ'], axis=1, inplace=True)
    bio = bio[bio['freq'] < 1999]
    bio_dfs = [subdf.reset_index(drop=True) for _, subdf in bio.groupby("c_rate")]
    for rate in bio_dfs:
        t_start = rate["time"].min()
        rate['qcharge'] = (rate['time']-t_start+1) * rate['c_rate'] * 2900 / 3600
        with col2.expander(f"C-Rate {rate['c_rate'][0]}"):
            st.write(rate)

    st.subheader("Look-Up Werte:")
    smoove_bev = st.toggle('Glätten vorher')
    table = pd.DataFrame()
    for rate in basy_dfs:
        freq = [subdf.reset_index(drop=True) for _, subdf in rate.groupby("freq")]
        for f in freq:
            f = f.sort_values(by="time").reset_index(drop=True)
            first_re = f.iloc[0]['re']
            first_im = f.iloc[0]['im']
            if smoove_bev:
                f['re'] =  savgol_filter( f['re'].values, window_length=7, polyorder=2 )
                f['im'] =  savgol_filter( f['im'].values, window_length=7, polyorder=2 )

            f['re'] = f['re'] - first_re
            f['im'] = f['im'] - first_im
            table = pd.concat([table, f], ignore_index=True)
    st.dataframe(table)

    st.subheader("Daten Anpassen:")
    options = ['Nächster', 'Interpoliert']
    opt = st.segmented_control("Art", options, label_visibility='collapsed',default='Nächster')
    smoove_aft = st.toggle('Glätten nacher')
    data = pd.DataFrame()
    fig_after = go.Figure()
    fig_before = go.Figure()
    for i, rate in enumerate(bio_dfs):
        c_rate = rate["c_rate"][0]
        basy = table[table["c_rate"]==c_rate]
        basy_points = basy[["freq", "qcharge"]].values
        values_re = basy["re"].values
        values_im = basy["im"].values

        bio_points = rate[["freq", "qcharge"]].values

        re_interp = griddata(basy_points, values_re, bio_points, method="cubic")
        im_interp = griddata(basy_points, values_im, bio_points, method="cubic")

        tree = cKDTree(basy_points)
        dist, idx = tree.query(bio_points, k=1)


        basy_matched = basy.iloc[idx].reset_index(drop=True)
        rate_reset = rate.reset_index(drop=True)

        if opt == "Interpoliert":
            result = pd.DataFrame({
                "freq": rate["freq"],
                "qcharge": rate["qcharge"],
                "re_diff": rate["re"] - re_interp,
                "im_diff": rate["im"] - im_interp,
                "c_rate": c_rate,
            })
        else:
            result = pd.DataFrame({
                "freq": rate_reset["freq"],
                "qcharge": rate_reset["qcharge"],
                "re_diff": rate_reset["re"] - basy_matched["re"],
                "im_diff": rate_reset["im"] - basy_matched["im"],
                "c_rate": c_rate,
            })
        if smoove_aft:
            result['re_diff'] = savgol_filter(result['re_diff'].values, window_length=5, polyorder=2)
            result['im_diff'] = savgol_filter(result['im_diff'].values, window_length=5, polyorder=2)
        data = pd.concat([data, result], ignore_index=True)
        col = list(colors_short.values())
        fig_after.add_trace(go.Scatter(
            x=result["re_diff"],
            y=result["im_diff"],
            name=c_rate,
            line=dict(color=col[i]),
        ))

        fig_before.add_trace(go.Scatter(
            x= rate_reset["re"],
            y= rate_reset["im"],
            name=c_rate,
            line=dict(color=col[i]),
        ))
    col1, col2 = st.columns(2)
    col1.subheader("Vorher:")
    col1.plotly_chart(fig_before)
    col2.subheader("Nachher:")
    col2.plotly_chart(fig_after)
    st.dataframe(data)
    fig = px.line(data, x="freq", y="re_diff", color="c_rate", color_discrete_sequence=list(colors_short.values()), log_x=True)
    col2.plotly_chart(fig)
    fig = px.line(bio, x="freq", y="re", color="c_rate", color_discrete_sequence=list(colors_short.values()), log_x=True)
    col1.plotly_chart(fig)
    fig = px.line(data, x="freq", y="im_diff", color="c_rate", color_discrete_sequence=list(colors_short.values()),
                  log_x=True)
    col2.plotly_chart(fig)
    fig = px.line(bio, x="freq", y="im", color="c_rate", color_discrete_sequence=list(colors_short.values()),
                  log_x=True)
    col1.plotly_chart(fig)

def vergleichen_app():
    st.title("Basytec - Compare")
    DB = Database("Comp")
    xcts = DB.get_basytec()
    con1 = st.container(border=True)
    con1.subheader("Messung")
    basy_file = con1.file_uploader("Datei Auswählen", type=["csv"], accept_multiple_files=False)
    con1.subheader("Vergleichswerte")
    bio_file = con1.file_uploader("Datei Auswählen", type=["mpr"], accept_multiple_files=False)

    if basy_file is not None:
        basy_data = pd.read_csv(basy_file)
        st.write(basy_data)

    if bio_file is not None:
        bio_data = pd.DataFrame()
        mpr_file = BioLogic.MPRfile(bio_file)
        bio_data_imp = pd.DataFrame(mpr_file.data)
        bio_data['freq'] = bio_data_imp['freq/Hz']
        z = bio_data_imp['|Z|/Ohm']
        bio_data['phase'] = bio_data_imp['Phase(Z)/deg']
        bio_data['re'] = z * np.cos(bio_data['phase'])
        bio_data['im'] = z * np.sin(bio_data['phase'])
        bio_data['c_rate'] = round(bio_data_imp['I/mA']/2500 / 1250) * 1250

    if bio_file is not None and basy_file is not None:
        c_rate = basy_data['c_rate'].unique()
        for c in c_rate:
            bio_c = bio_data[bio_data['c_rate'] == c]
            basy_c = basy_data[basy_data['c_rate'] == c]
            xcts_c = xcts[xcts['c_rate'] == 0.25]

            re_f_basy = interp1d(basy_c["freq"], basy_c["re"], kind='quadratic', fill_value='extrapolate')
            re_f_xcts = interp1d(xcts_c["freq"], xcts_c["re"], kind='quadratic', fill_value='extrapolate')
            im_f_basy = interp1d(basy_c["freq"], basy_c["im"], kind='quadratic', fill_value='extrapolate')
            im_f_xcts = interp1d(xcts_c["freq"], xcts_c["im"], kind='quadratic', fill_value='extrapolate')

            x_common = np.linspace(min(basy_c["freq"].min(), bio_c["freq"].min()),
                                   max(basy_c["freq"].max(), bio_c["freq"].max()), 200)

            re_inter_basy = re_f_basy(x_common)
            re_inter_xcts = re_f_xcts(x_common)
            im_inter_basy = im_f_basy(x_common)
            im_inter_xcts = im_f_xcts(x_common)

            Z_basy = re_inter_basy + 1j * im_inter_basy
            Z_xcts = re_inter_xcts + 1j * im_inter_xcts

            Y_total = 1 / Z_basy - 1 / Z_xcts
            Z_total = 1 / Y_total

            re_diff = Z_total.real
            im_diff = Z_total.imag
            ph_diff = np.arctan2(im_diff, re_diff)
            calc_c = pd.DataFrame({
                're': re_diff,
                'im': im_diff,
                'phase': ph_diff,
                'c_rate': c,
                'freq': x_common,
            })

            st.write("Realteil")
            plot_comp(basy_c, bio_c, calc_c, 're')
            st.write("Imaginärteil")
            plot_comp(basy_c, bio_c, calc_c, 'im')
            st.write("Phase")
            plot_comp(basy_c, bio_c, calc_c, 'phase')

def plot_typ(imp_data, x, y):
    for z, t in enumerate(["Basytec","Biologic"]):
        con = st.container(border=False)
        con.subheader(t)
        data = imp_data[imp_data["typ"] == t]
        data = data[data["freq"] <= 1900]
        log = True if y == "freq" else False

        fig = px.line(data,
                      x=x,
                      log_x=log,
                      y=y,
                      color="c_rate",
                      color_discrete_sequence=list(colors_short.values()),
                      hover_data=['freq']
                      )
        con.plotly_chart(fig)
        con.write(data)

def plot_c_rates(imp_data, x, y, c_rates, ):
    for z, c in enumerate(c_rates):
        con = st.container(border=False)
        con.subheader(f"{c}-C")
        data = imp_data[imp_data["c_rate"] == c]
        data = data[data["freq"] <= 1900]
        log = True if y == "freq" else False

        fig = px.line(data,
                      x=x,
                      log_x=log,
                      y=y,
                      color="typ",
                      color_discrete_sequence=list(colors_short.values()),
                      hover_data=['freq']
                      )
        con.plotly_chart(fig)
        con.write(data)

def plot_basy(data):
    con = st.container(border=False)
    fig1 = px.line(data,
                   x="freq",
                   log_x=True,
                   y="re",
                   color="c_rate",
                   hover_data=['freq'],
                   )
    fig2 = px.line(data,
                   x="freq",
                   log_x=True,
                   y="im",
                   color="c_rate",
                   hover_data=['freq']
                   )
    fig3 = px.line(data,
                   x="freq",
                   log_x=True,
                   y="phase",
                   color="c_rate",
                   hover_data=['freq']
                   )

    con.subheader(f"Realteil")
    con.plotly_chart(fig1)
    con.subheader(f"Imaginärteil")
    con.plotly_chart(fig2)
    con.subheader(f"Phase")
    con.plotly_chart(fig3)

    con.subheader(f"Data")
    con.dataframe(data)

def plot_comp(basy, bio, calc_c, plt):
    con = st.container(border=False)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=calc_c['freq'],y=calc_c[plt], mode="lines",name="Berechnet"))
    fig.add_trace(go.Scatter(x=bio['freq'],y=bio[plt], mode="lines",name="Referenz"))
    fig.add_trace(go.Scatter(x=basy['freq'],y=basy[plt], mode="lines",name="Gemessen"))
    fig.update_xaxes(type="log")
    con.plotly_chart(fig)
