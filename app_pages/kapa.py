import plotly.express as px
import streamlit as st
import pandas as pd
import io
from src.filtern import daten_filter
from src.plotting_functions import colors
from classes.datenbank import Database

def kapazitaet_app():
    st.title("Kapazität")
    DB = Database("Kapazitaet")
    alldata = DB.get_all_kapa()
    con0 = st.container(border=True)
    cycle, zelle = daten_filter(con0, alldata)
    filt_data = pd.DataFrame()
    if not cycle or not zelle:
        st.warning("Keine Werte ausgewählt")
    else:
        con1 = st.container(border=False)
        data = pd.DataFrame()
        for d in alldata.itertuples(index=False):
            if d.cycle in cycle and d.zelle in zelle:
                kap = DB.get_kapa(d.name)
                kap = pd.DataFrame(kap)
                filt_data = pd.concat([filt_data, kap])
                data = pd.concat([data, kap])

        con1.subheader("Ausgewählte Daten:")
        con1.write(filt_data)
        con1.subheader("Plots:")

        norm = con1.toggle("Startpunkt normieren")
        if norm:
            temp = data[data["zelle"]=='JT_VTC_002']
            data = data[~data["datei"].str.contains("Characterization", na=False)]
            data = pd.concat([data, temp])
            data["kapa_norm"] = data.groupby("zelle")["kapa"].transform(lambda x: x - x.iloc[0])
            plot_y = "kapa_norm"
        else:
            plot_y = "kapa"
        selected = con1.toggle("Alle Grafen in einem Plot")
        if selected :
            plots = ["Allen Zellen"]
            plot_name = ""
            data_mod = data
            subplots = "zelle"
            einheit = "mAh"
        else:
            plots = zelle
            plot_name = "zelle"
            subplots = "zelle"
            einheit = "mAh"
        plot_x = con1.segmented_control("X-Achse",["cycle", "cap_cycle"],default="cycle")


        key = 0
        for p in plots:
            con2 = st.container(border=False)
            con2.divider()
            if not selected:
                data_mod = data[data[plot_name] == p]
            name = f"Kapazität von {plot_name} {p} in {einheit}"
            fig = plot_kapa(data_mod, name,subplots,plot_x,plot_y)
            con2.plotly_chart(fig)
            fig.update_layout(
                template="plotly",  # <- wichtig!
                paper_bgcolor='white',
                plot_bgcolor='white',
                font_color='black',
                legend_title_font_color='black',
                xaxis=dict(
                    showgrid=True,
                    gridcolor='#e0e0e0',  # Farbe des Grids
                    gridwidth=1  # Dicke der Linien
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='#e0e0e0',
                    gridwidth=1
                )
            )
            key += 1

            con2.dataframe(data_mod)


def plot_kapa(data,name,subplots,x,y):
    data = data.sort_values(by=x)
    fig = px.line(data,
                  x=x,
                  y=y,
                  color=subplots,
                  title=name,
                  markers=True,  # Marker aktivieren
                  color_discrete_sequence=list(colors.values())
                  )
    fig.update_layout(
        yaxis_title='Kapazirät (mAh)',
        xaxis_title='Zyklken',
        template='simple_white'
    )
    return fig
