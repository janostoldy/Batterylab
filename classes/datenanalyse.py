import os
import hashlib
from galvani import BioLogic
import streamlit as st

from src.auswertung import mean_pairwise_abs_diff
from classes.datenbank import Database
from config import mes_spalten
import pandas as pd
import numpy as np
from scipy.signal import savgol_filter, find_peaks
from scipy.ndimage import gaussian_filter1d

class Analyse:
    def __init__(self):
        # Initialisiere die Datenbankverbindung
        self.DB = Database("Analyse")

    def analyse_eingang(self, file_path, cycle, Zelle, save_data, bar):
        for data_path in file_path:
            data_name = os.path.basename(data_path)
            data_path = [data_path]
            if "01_MB" in data_name:
                bar.progress(1 / 3, text="Kapazität analysieren...")
                self.analys_kapa_data(data_path, cycle, Zelle, save_data)
            elif "02_MB" in data_name:
                bar.progress(2 / 3, text="OCV analysieren...")
                self.analys_OCV_data(data_path, cycle, Zelle, save_data)
            elif "03_MB" in data_name:
                bar.progress(3 / 3, text="EIS analysieren...")
                self.analyze_EIS_data(data_path, cycle, Zelle, save_data)
            else:
                raise Exception("Keine Eingangsprüfung!")


    def add_relax(self, file_path, cycle, Zelle, save_data):
        #try:
            for data_path in file_path:
                data_name = os.path.basename(data_path)
                if save_data:
                    self.DB.insert_file(data_name, cycle, "Thermische-Relaxation", Zelle, "Relaxation")
        #except Exception as e:
         #   raise Exception(f"Fehler bei Relaxation -> {e}")

    def analyze_Aeging(self, file_path, cycle, Zelle, save_data, bar):
        try:
            n_files = len(file_path)
            for i, data_path in enumerate(file_path):
                data_name = os.path.basename(data_path)
                bar.progress((i+1)/n_files, text=f"Analysieren von Datei {i+1} von {n_files}: {data_name}")
                mpr_file = BioLogic.MPRfile(data_path)
                df = pd.DataFrame(mpr_file.data)
                ageing_raw = df.rename(columns=mes_spalten)
                if 'zohm' in ageing_raw:
                    self.analyze_EIS_data([data_path], cycle, Zelle, save_data)
                    continue
                aeging_cycles = ageing_raw['cycle number'].iloc[-1] - ageing_raw['cycle number'].iloc[0]
                cycle = cycle + aeging_cycles
                if save_data:
                    cycle = int(cycle)
                    self.DB.update_zelle(Zelle, cycle)
                    self.DB.insert_file(data_name, cycle, "Aeging-Analyse", Zelle, "Ageing")
        except Exception as e:
            raise Exception(f"Fehler bei Ageing-Analyse -> {e}")

    def calc_niquist_data(self, eis_data,save_data):
        results = []

        def nearest(series, value):
            array = np.array(series)
            idx = (np.abs(array - value)).argmin()            # Index des nächstgelegenen Werts
            return idx

        for eis in eis_data:
            eis = eis[eis["freqhz"] != 1999]
            eis = eis.sort_values(by="freqhz")
            re = eis['calc_rezohm']
            im = eis['calc_imzohm']
            freq = eis['freqhz']
            phase = eis['phasezdeg']
            s_im = savgol_filter(im, window_length=7, polyorder=2)
            minima_indices, _ = find_peaks(-s_im)
            minima_indices = minima_indices[0]
            maxima_indices, _ = find_peaks(s_im)
            maxima_indices = maxima_indices[0]
            zif_indizes = np.where(np.diff(np.sign(im)))[0]
            zif_indizes = zif_indizes[0]

            idx_200 = nearest(freq, 200)
            idx_400 = nearest(freq, 400)
            idx_631 = nearest(freq, 631)
            idx_31 = nearest(freq, 31)
            idx_16 = nearest(freq, 16)

            mpd = mean_pairwise_abs_diff(eis['zohm'])

            temp = {
                'soc': eis['soc'].values[0],
                'calc_ima': eis['calc_ima'].values[0],
                'im_min': im.iloc[minima_indices],
                're_min': re.iloc[minima_indices],
                'phase_min': phase.iloc[minima_indices],
                'freq_min': freq.iloc[minima_indices],
                'im_max': im.iloc[maxima_indices],
                're_max': re.iloc[maxima_indices],
                'phase_max': phase.iloc[maxima_indices],
                'freq_max': freq.iloc[maxima_indices],
                'im_zif': im.iloc[zif_indizes],
                're_zif': re.iloc[zif_indizes],
                'phase_zif': phase.iloc[zif_indizes],
                'freq_zif': freq.iloc[zif_indizes],
                're_184': re.iloc[idx_200],
                'im_184': im.iloc[idx_200],
                'phase_184': phase.iloc[idx_200],
                're_376': re.iloc[idx_400],
                'im_376': im.iloc[idx_400],
                'phase_376': phase.iloc[idx_400],
                'mpd': mpd,
                'im_600': im.iloc[idx_631],
                'im_57': im.iloc[idx_31],
                'im_16': im.iloc[idx_16],
                'd_zi_min_re': re.iloc[minima_indices] - re.iloc[zif_indizes],
                'd_zi_max_re': re.iloc[maxima_indices] - re.iloc[zif_indizes],
                'datei': eis['datei'].values[0]
            }
            results.append(temp)
        
        niquist_df = pd.DataFrame(results)
        if save_data:
            self.DB.df_in_DB(df=niquist_df, table_name='eis_points')

    def analyze_EIS_data(self, file_path, cycle, Zelle, save_data, typ='eis'):
        try:
            for data_path in file_path:
                data_name = os.path.basename(data_path)
                mpr_file = BioLogic.MPRfile(data_path)
                df = pd.DataFrame(mpr_file.data)
                df = df.rename(columns=mes_spalten)

                if 'zohm' not in df.columns:
                    raise Exception("Keine Eis-Daten")

                # Eis Messung
                start_eis_indices = df[((df['flags'] == 37) | (df['flags'] == 165) | (df['flags'] == 53) | (df['flags'] == 181)) & (df['freqhz'] > 0)].index
                end_eis_indices = df[((df['flags'] == 69) | (df['flags'] == 197) | (df['flags'] == 85) | (df['flags'] == 213)) & (df['freqhz'] > 0)].index
                if len(start_eis_indices) == 0 or len(end_eis_indices) == 0:
                    raise Exception('No EIS data found in file or wrong flags.')

                eis_values = [df.loc[start:end].copy() for start, end in zip(start_eis_indices, end_eis_indices)]
                zero_soc = min(df.qqomah)
                eis_soc = round((df.qqomah[start_eis_indices - 1] - zero_soc) / 125) * 125
                eis_ImA = df.ima[start_eis_indices - 1]
                eis_Calc_ImA = round(eis_ImA / 1250) * 1250
                start_time = df.times[start_eis_indices]

                for i, eis in enumerate(eis_values):
                    # Real und Imaginärteil berechnen
                    eis_phi = np.deg2rad(eis['phasezdeg'])
                    eis.loc[:, 'calc_rezohm'] = eis['zohm'] * np.cos(eis_phi.values)
                    eis.loc[:, 'calc_imzohm'] = eis['zohm'] * np.sin(eis_phi.values) * -1

                    eis.loc[:, 'soc'] = eis_soc.iloc[i]
                    eis.loc[:, 'calc_ima'] = eis_Calc_ImA.iloc[i]
                    eis.loc[:, 'calc_times'] = eis['times'] - start_time.iloc[i]
                    eis.loc[:, 'datei'] = data_name
                    eis.loc[:, 'typ'] = typ

                self.analyze_DEIS_data(df, data_name, cycle, Zelle, save_data)

                self.calc_niquist_data(eis_values, save_data)
                if save_data:
                    self.DB.insert_file(data_name, cycle, "Eis Messung", Zelle, "EIS")
                    for eis in eis_values:
                        self.DB.df_in_DB(df=eis, table_name='eis')

        except Exception as e:
            raise Exception(f"Fehler bei EIS-Analyse -> {e}")

    def analyze_DEIS_data(self, df, data_name, cycle, Zelle, save_data):
        try:
            deis_values = df[(df['flags'].isin([117, 101, 229, 245])) & (df['freqhz'] > 0)].copy()
            if len(deis_values) == 0:
                raise Exception('No DEIS data found in file or wrong flags.')
            deis_indices = deis_values.index
            deis_soc = round(df.qqomah[deis_indices - 1] / 125) * 125
            deis_ImA = df.ima[deis_indices - 1]
            deis_Calc_ImA = round(deis_ImA / 1250) * 1250

            #Anpassungen, um Daten zusammenzufügen
            deis_soc.index = deis_soc.index + 1
            deis_Calc_ImA.index = deis_Calc_ImA.index + 1

            # Real und Imaginärteil berechnen
            deis_phi = np.deg2rad(deis_values['phasezdeg'])  # Konvertiere Winkel in Radiant
            deis_values.loc[:, 'calc_rezohm'] = deis_values['zohm'] * np.cos(deis_phi)
            deis_values.loc[:, 'calc_imzohm'] = deis_values['zohm'] * np.sin(deis_phi)

            deis_values.loc[:, 'soc'] = deis_soc
            deis_values.loc[:, 'calc_ima'] = deis_Calc_ImA
            deis_values.loc[:, 'calc_times'] = 0
            deis_values.loc[:, 'datei'] = os.path.basename(data_name)
            deis_values.loc[:, 'typ'] = "deis"

            if save_data:
                self.DB.df_in_DB(df=deis_values, table_name='eis')
        except Exception as e:
            st.warning(f"Fehler bei DEIS-Analyse -> {e}")

    def analyze_LUP_data(self, file_path, cycle, Zelle, save_data):
        data_name = os.path.basename(file_path[0])
        mpr_file = BioLogic.MPRfile(file_path[0])
        df = pd.DataFrame(mpr_file.data)
        df = df.rename(columns=mes_spalten)

        if 'zohm' not in df.columns:
            raise Exception("Keine Eis-Daten")

        deis_values = df[(df['flags'].isin([117, 101, 229, 245])) & (df['freqhz'] > 0)].copy()
        if len(deis_values) == 0:
            raise Exception('No DEIS data found in file or wrong flags.')
        deis_indices = deis_values.index
        deis_soc = round(df.qqomah[deis_indices - 1] / 125) * 125
        deis_ImA = df.ima[deis_indices - 1]
        deis_Calc_ImA = round(deis_ImA / 1250) * 1250
        deis_values['temperaturec'] = round(deis_values['temperaturec'] /5) * 5

        #Anpassungen, um Daten zusammenzufügen
        deis_soc.index = deis_soc.index + 1
        deis_Calc_ImA.index = deis_Calc_ImA.index + 1

        # Real und Imaginärteil berechnen
        deis_phi = np.deg2rad(deis_values['phasezdeg'])  # Konvertiere Winkel in Radiant
        deis_values.loc[:, 'calc_rezohm'] = deis_values['zohm'] * np.cos(deis_phi)
        deis_values.loc[:, 'calc_imzohm'] = deis_values['zohm'] * np.sin(deis_phi)

        deis_values.loc[:, 'soc'] = deis_soc
        deis_values.loc[:, 'calc_ima'] = deis_Calc_ImA
        deis_values.loc[:, 'calc_times'] = 0
        deis_values.loc[:, 'datei'] = os.path.basename(data_name)
        deis_values.loc[:, 'typ'] = "lup"

        if save_data:
            self.DB.insert_file(data_name, cycle, "Look-Up Table", Zelle, "deis")
            self.DB.df_in_DB(df=deis_values, table_name='eis')

    def analys_kapa_data(self,file_path, cycle, Zelle, save_data):
        try:
            try:
                inital = self.DB.get_initial_kapa(Zelle)
            except:
                inital = 0
            for data_path in file_path:
                data_name = os.path.basename(data_path)
                mpr_file = BioLogic.MPRfile(data_path)
                df = pd.DataFrame(mpr_file.data)
                kapa_raw = df.rename(columns=mes_spalten)
                kapa = max(kapa_raw['qqomah']) - min(kapa_raw['qqomah'])

                data = pd.DataFrame({
                    'datei': [data_name],
                    'info': [f"Zelle {Zelle} nach Zyklus {cycle}"],
                    'kapa': [kapa],
                    #'kapa_norm': [kapa] - inital,
                })

                if save_data:
                    self.DB.df_in_DB(df=data, table_name='kapa')
                    self.DB.insert_file(data_name, cycle, "Kapazitäts-Analyse", Zelle, "Kapa")
        except Exception as e:
            raise Exception(f"Fehler bei Kapazitäts-Analyse -> {e}")

    def analys_OCV_data(self, file_path, cycle, Zelle, save_data):
        try:
            for data_path in file_path:
                data_name = os.path.basename(data_path)
                mpr_file = BioLogic.MPRfile(data_path)
                df = pd.DataFrame(mpr_file.data)
                dva_raw = df.rename(columns=mes_spalten)

                QQomAh_smoove = gaussian_filter1d(dva_raw["qqomah"], sigma=5)
                QQomAh_diff = np.gradient(QQomAh_smoove)
                Ecell_smoove = gaussian_filter1d(dva_raw["ecellv"], sigma=5)
                Ecell_diff = np.gradient(Ecell_smoove)
                dva = Ecell_diff[:] / QQomAh_diff[:]
                dva_smoove = gaussian_filter1d(dva, sigma=15)
                dva_ind = np.where(dva_smoove < 0.001)
                first_index = dva_ind[0][0]
                dva_ind = np.where(np.diff(dva_smoove) > 0)[0]
                last_index = dva_ind[-1] + 1 if len(dva_ind) > 0 else len(dva_smoove) - 1

                dva_edit = dva_raw[first_index:last_index]
                dva_edit['qqomah_smoove'] = QQomAh_smoove[first_index:last_index]
                dva_edit['ecellv_smoove'] = Ecell_smoove[first_index:last_index]
                dva_edit['calc_dv_dq'] = dva_smoove[first_index:last_index]
                dva_edit['cycle'] = cycle
                dva_edit['zelle'] = Zelle
                dva_edit['datei'] = data_name

                Q0_val = QQomAh_smoove[0]
                Q0 = dva_edit['qqomah_smoove'].iloc[0]
                Qactual = dva_edit['qqomah_smoove'].iloc[-1]
                peaks = find_peaks(dva_edit['calc_dv_dq'].values, distance=700, height=0.00035)[0]
                Q1 = dva_edit['qqomah_smoove'].iloc[peaks[-2]]
                Q2 = Qactual - Q1
                Q3 = Qactual - dva_edit['qqomah_smoove'].iloc[peaks[-1]]

                calc_Points = pd.DataFrame({
                    'datei': [data_name] * 5,
                    'point': ['Q0', 'Q1', 'Q2', 'Q3', 'Qactual'],
                    'value': [Q0_val, Q1, Q2, Q3, Qactual],
                    'x_start': [Q0, Q0, Qactual - Q2, Qactual - Q3, Q0],
                    'x_end': [Q0, Q1, Qactual, Qactual, Qactual],
                })

                if save_data:
                    self.DB.df_in_DB(df=dva_edit, table_name='dva')
                    self.DB.df_in_DB(df=calc_Points, table_name='dva_points')
                    self.DB.insert_file(data_name, cycle, "DVA Analyse", Zelle, "DVA")
        except Exception as e:
            raise Exception(f"Fehler bei OCV-Analyse -> {e}")

    def analyse_imp(self, file_path, cycle, Zelle, save_data, bar):
        n_files = len(file_path)
        for i, data_path in enumerate(file_path):
            data_name = os.path.basename(data_path)
            bar.progress((i + 1) / n_files, text=f"Analysieren Datei {i + 1} von {n_files}: {data_name}")
            if data_path.endswith(".csv"):
                self.analyse_imp_safion(data_path, cycle, Zelle, save_data)
            elif data_path.endswith(".mpr"):
                self.analyse_imp_biologic(data_path, cycle, Zelle, save_data)

    def analyse_imp_safion(self, data_path, cycle, Zelle, save_data):
        df = pd.read_csv(data_path)
        data_name = os.path.basename(data_path)

        # Metadaten und Daten trennen
        meta_columns = df.columns[:13]  # Die ersten 13 Spalten sind Metadaten
        data_columns = df.columns[13:]  # Die restlichen Spalten sind Daten

        new_columns = ["re", "im", "phase", "freq"]
        meta_data = pd.DataFrame()
        for idx, row in df.iterrows():
            data = pd.DataFrame()

            meta_data_in = pd.DataFrame([row[meta_columns].values], columns=meta_columns)
            meta_data['time'] = meta_data_in['Time [s]']
            meta_data['voltage'] = meta_data_in['Voltage [V]']
            meta_data['current'] = meta_data_in['Current [A]']
            meta_data['temp'] = meta_data_in['Temperature [°C]']
            meta_data['delta_cap'] = 0
            meta_data['c_rate'] = meta_data_in['C-Rate']
            meta_data['datei'] = data_name
            meta_data['typ'] = ("Basytec")

            for i in range(0, len(data_columns), 4):
                data_group = row[data_columns[i:i + 4]].values
                data_df = pd.DataFrame(list(data_group))
                data = pd.concat([data, data_df], axis=1, ignore_index=True)
            # Erstellen eines neuen DataFrames
            data = data.T
            data.columns = new_columns
            data["im"] = -data["im"]
            for col in meta_data.columns:
                data[col] = meta_data[col].values[0]
            if save_data:
                self.DB.df_in_DB(df=data, table_name='imp')
                self.DB.insert_file(data_name, cycle, "Imp Untersuchung", Zelle, "imp")

    def analyse_imp_biologic(self, data_path, cycle,  Zelle, save_data):
        data_name = os.path.basename(data_path)
        mpr_file = BioLogic.MPRfile(data_path)
        df = pd.DataFrame(mpr_file.data)
        df = df.rename(columns=mes_spalten)

        if 'zohm' not in df.columns:
            raise Exception("Keine Eis-Daten")

        # Eis Messung
        start_eis_indices = df[((df['flags'] == 37) | (df['flags'] == 165)) & (df['freqhz'] > 0)].index
        end_eis_indices = df[((df['flags'] == 69) | (df['flags'] == 197)) & (df['freqhz'] > 0)].index
        if len(start_eis_indices) == 0 or len(end_eis_indices) == 0:
            start_eis_indices = df[((df['flags'] == 53) | (df['flags'] == 181)) & (df['freqhz'] > 0)].index
            end_eis_indices = df[((df['flags'] == 85) | (df['flags'] == 213)) & (df['freqhz'] > 0)].index
        if len(start_eis_indices) == 0 or len(end_eis_indices) == 0:
            raise Exception('No EIS data found in file or wrong flags.')

        eis_values = [df.loc[start:end].copy() for start, end in zip(start_eis_indices, end_eis_indices)]
        zero_soc = min(df.qqomah)
        eis_soc = round((df.qqomah[start_eis_indices - 1] - zero_soc) / 125) * 125
        eis_ImA = df.ima[start_eis_indices - 1]
        eis_C_Rate = round(eis_ImA / 2900,2)
        start_time = df.times[start_eis_indices]

        data = pd.DataFrame()
        for i, eis in enumerate(eis_values):
            temp = pd.DataFrame()
            eis_phi = np.deg2rad(eis['phasezdeg'])
            temp['re'] = eis['zohm'] * np.cos(eis_phi.values)
            temp['im'] = eis['zohm'] * np.sin(eis_phi.values) * -1
            temp['freq'] = eis['freqhz']
            temp['phase'] = eis_phi
            temp['temp'] = eis['temperaturec']
            temp['current'] = eis['ima']
            temp['voltage'] = eis['ecellv']
            temp['delta_cap'] = eis_soc.iloc[i]
            temp['c_rate'] = eis_C_Rate.iloc[i]
            temp['time'] = eis['times'] - start_time.iloc[i]
            temp['datei'] = data_name
            temp['typ'] = "Biologic"
            data = pd.concat([data, temp], ignore_index=True)

        if save_data:
            self.DB.insert_file(data_name, cycle, "Imp Untersuchung", Zelle, "imp")
            self.DB.df_in_DB(df=data, table_name='imp')

    def insert_data(self, eis_values, deis_values, data_name):
        for eis in eis_values:
            self.DB.df_in_DB(df=eis, table_name='eis')
        self.DB.df_in_DB(df=deis_values, table_name='eis')
