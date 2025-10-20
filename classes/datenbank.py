import pandas as pd
import streamlit as st
from sqlalchemy import text, create_engine, MetaData, Table
from sqlalchemy.dialects.postgresql import insert
import time


class Database:
    def __init__(self, db_name="Battery_Lab"):
        self.name = db_name

    def df_in_DB_alt(self, df, table_name):
        """
        Fügt einen DataFrame in die angegebene Tabelle der Datenbank ein (mit UPSERT-Logik für MySQL).

        - Prüft, ob die Spalten des DataFrames mit denen der Tabelle übereinstimmen.
        - Erwartet eine Spalte 'hash' als eindeutigen Schlüssel.
        - Nutzt Batch-Insert für Effizienz.
        - Bei Konflikt (gleicher 'hash') werden die Werte aktualisiert.
        """

        # Hol Spaltennamen aus der Datenbank (als Liste)
        conn = st.connection("sql", type="sql")
        result = conn.query(
            """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = :table
              AND TABLE_SCHEMA = 'Formierung'
            """,
            params={"table": table_name}
        )
        db_columns = [row["COLUMN_NAME"] for row in result]

        # Nur Spalten einfügen, die in der Tabelle existieren
        df = df[[col for col in df.columns if col in db_columns]]

        if df.empty:
            return

        columns = df.columns.tolist()
        placeholders = ", ".join([f":{col}" for col in columns])
        update_clause = ", ".join([f"{col} = VALUES({col})" for col in columns if col != 'hash'])

        sql = f"""
        INSERT INTO {table_name} ({", ".join(columns)})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE {update_clause}
        """

        # Daten als Liste von Dictionaries vorbereiten
        data_dicts = df.to_dict(orient="records")

        with conn.session as s:
            s.execute(sql, data_dicts)
            s.commit()

    def df_in_DB(self, df, table_name):
        url = st.secrets["url"]["url"]
        engine = create_engine(url)

        with engine.connect() as conn:
            metadata = MetaData()
            table = Table(table_name, metadata, autoload_with=engine)

            pk_cols = [col.name for col in table.primary_key.columns]

            valid_columns = set([col.name for col in table.columns])
            df = df[[col for col in df.columns if col in valid_columns]]

            for row in df.to_dict(orient='records'):
                stmt = insert(table).values(**row)
                upsert_stmt = stmt.on_conflict_do_update(
                    index_elements=pk_cols,
                    set_={col: stmt.excluded[col]
                          for col in row.keys()
                          if col not in pk_cols and col in stmt.excluded}
                )
                conn.execute(upsert_stmt)

            conn.commit()

    def insert_file(self, file, cycle, Info="", Zelle="", Typ=""):
        conn = st.connection("sql", type="sql")
        cap_p_cycle = self.get_cap_cycle(Zelle)
        cap_cycle = int(cycle * cap_p_cycle.values[0])
        sql = """
            INSERT INTO files (name, datum, info, cycle, zelle, typ, cap_cycle)
            VALUES (:name, CURRENT_TIMESTAMP, :info, :cycle, :zelle, :typ, :cap_cycle)
            ON CONFLICT (name) DO UPDATE SET
                datum = CURRENT_TIMESTAMP,
                info = EXCLUDED.info,
                cycle = EXCLUDED.cycle,
                zelle = EXCLUDED.zelle,
                typ = EXCLUDED.typ"""
        values = {"name": file, "info": Info, "cycle": cycle, "zelle": Zelle, "typ": Typ, "cap_cycle": cap_cycle}
        with conn.session as s:
            s.execute(text(sql), values)
            s.commit()


    def delete_file(self, file):
        conn = st.connection("sql", type="sql")
        tables = ["eis", "files", "kapa", "eis_points", "dva", "dva_points"]
        with conn.session as s:
            for table in tables:
                if table == "eis":
                    sql = f"DELETE FROM {table} WHERE datei = :file"
                elif table == "files":
                    sql = f"DELETE FROM {table} WHERE name = :file"
                elif table == "kapa":
                    sql = f"DELETE FROM {table} WHERE datei = :file"
                elif table == "eis_points":
                    sql = f"DELETE FROM {table} WHERE datei = :file"
                elif table == "dva":
                    sql = f"DELETE FROM {table} WHERE datei = :file"
                elif table == "dva_points":
                    sql = f"DELETE FROM {table} WHERE datei = :file"
                s.execute(text(sql), {"file": file})
            s.commit()

    @st.cache_data(ttl=0)
    def get_all_files(_self):
        conn = st.connection("sql", type="sql")
        return conn.query("SELECT * FROM files", ttl=0)

    def get_all_eingang(self):
        conn = st.connection("sql", type="sql")
        sql = "SELECT * FROM files WHERE files.typ!='Ageing'"
        return conn.query(sql)

    def get_file(self, cycle, zelle, typ):
        conn = st.connection("sql", type="sql")
        if typ == "*":
            sql = "SELECT * FROM files WHERE files.cycle=:cycle AND files.zelle=:zelle"
            values = {"cycle": cycle, "zelle": zelle}
        else:
            sql = "SELECT * FROM files WHERE files.cycle=:cycle AND files.zelle=:zelle AND files.typ=:typ"
            values = {"cycle": cycle, "zelle": zelle, "typ": typ}
        with conn.session as s:
            file = s.execute(text(sql), params=values).fetchall()
            return pd.DataFrame(file)

    def get_file_typs(self):
        conn = st.connection("sql", type="sql")
        sql = f"""SELECT DISTINCT typ FROM files """
        return conn.query(sql)

    @st.cache_data(ttl=0)
    def get_all_zells(_self):
        conn = st.connection("sql", type="sql")
        return conn.query("SELECT * FROM zellen")

    def update_zelle(self, Zelle, cycle):
        conn = st.connection("sql", type="sql")
        sql = "UPDATE zellen SET cycle = :cycle WHERE id = :zelle"
        params = {"cycle": cycle, "zelle": Zelle}
        with conn.session as s:
            s.execute(text(sql), params)
            s.commit()

    def get_kapa_cycles(self):
        conn = st.connection("sql", type="sql")
        return conn.query("SELECT DISTINCT cycle FROM files WHERE typ='Kapa'")

    def get_zell_cycle(self, zelle, Max=True):
        conn = st.connection("sql", type="sql")
        sql = "SELECT cycle FROM zellen WHERE id = :zelle"
        params = {"zelle": zelle}
        return conn.query(sql, params=params)

    def get_cap_cycle(self, zelle):
        conn = st.connection("sql", type="sql")
        sql = "SELECT cap_p_cyc FROM zellen WHERE id = :zelle"
        params = {"zelle": zelle}
        return conn.query(sql, params=params)

    def delete_zell(self, id):
        """
            Lösche eine Zelle aus der Tabelle zellen.

            :param hash: Hash Wert der Zelle, die geupdated wird.
        """
        conn = st.connection("sql", type="sql")
        sql = "DELETE FROM zellen WHERE id = :id"
        params = {"id": id}
        with conn.session as s:
            s.execute(sql, params)
            s.commit()

    def get_all_kapa(self):
        conn = st.connection("sql", type="sql")
        sql = "SELECT * FROM files WHERE typ = 'Kapa'"
        return conn.query(sql)
    def get_kapa(self, Datei):
        conn = st.connection("sql", type="sql")
        sql = """SELECT kapa.datei, kapa.kapa, kapa.info, files.datum, files.cycle, files.zelle, files.cap_cycle
                     FROM kapa INNER JOIN files ON kapa.datei=files.name
                     WHERE kapa.datei = :datei"""
        params = {"datei": Datei}
        with conn.session as s:
           result = s.execute(text(sql), params).fetchall()
        return result

    def get_initial_kapa(self, zelle):
        conn = st.connection("sql", type="sql")
        sql = """SELECT inital_kapa
            FROM zellen
            WHERE id = :zelle
        """
        params = {"zelle": zelle}
        with conn.session as s:
            result = s.execute(text(sql), params=params).fetchall()
        return result

    def get_all_dva(self):
        conn = st.connection("sql", type="sql")
        sql = "SELECT * FROM files WHERE typ = 'DVA'"
        return conn.query(sql)
    def get_dva(self, Datei):
        conn = st.connection("sql", type="sql")
        sql1 = "SELECT * FROM dva WHERE datei = :datei"
        sql2 = "SELECT * FROM dva_points WHERE datei = :datei"
        params = {"datei": Datei}
        with conn.session as s:
            data = s.execute(text(sql1), params).fetchall()
            points = s.execute(text(sql2), params).fetchall()
        return data, points

    def get_all_eis_data(self):
        conn = st.connection("sql", type="sql")
        sql = """SELECT eis.freqhz, eis.zohm, eis.phasezdeg, eis.calc_rezohm, eis.calc_imzohm, eis.soc, files.zelle, files.cycle
                 FROM eis INNER JOIN files ON eis.datei = files.name
                 WHERE eis.typ='eis' AND (eis.datei NOT LIKE '%Characterization%' OR files.zelle = 'JT_VTC_009' 
                     OR files.zelle = 'JT_VTC_010' OR files.zelle = 'JT_VTC_006'OR files.zelle = 'JT_VTC_003')"""
        return conn.query(sql)

    def get_all_eis_points(self):
        conn = st.connection("sql", type="sql")
        sql = """SELECT eis_points.im_min, eis_points.im_max, eis_points.re_min, eis_points.re_max, eis_points.phase_max, eis_points.phase_min,
                        eis_points.re_zif, eis_points.mpd, eis_points.d_zi_max_re, eis_points.d_zi_min_re,
                        eis_points.phase_16, eis_points.phase_57, eis_points.phase_184, eis_points.phase_376, eis_points.phase_600,
                        eis_points.im_16, eis_points.im_57, eis_points.im_184, eis_points.im_376, eis_points.im_600,
                        eis_points.re_16,eis_points.re_57, eis_points.re_184, eis_points.re_376, eis_points.re_600,
                        
                        eis_points.soc, files.zelle, files.cycle
                 FROM eis_points INNER JOIN files ON eis_points.datei = files.name"""
        return conn.query(sql)

    def get_all_eis(self):
        conn = st.connection("sql", type="sql")
        sql = "SELECT * FROM files WHERE typ = 'EIS'"
        return conn.query(sql)
    def get_all_eis_soc(self):
        conn = st.connection("sql", type="sql")
        sql = ("SELECT DISTINCT soc FROM eis_points ")
        return conn.query(sql)
    def get_eis_points(self, Datei, soc):
        conn = st.connection("sql", type="sql")
        sql = """SELECT eis_points.*, files.datum, files.cycle, files.zelle, files.cap_cycle
                      FROM eis_points INNER JOIN files ON eis_points.datei=files.name 
                      WHERE eis_points.datei = :datei AND eis_points.soc = :soc"""
        params = {"datei": Datei, "soc": soc}
        with conn.session as s:
            result = s.execute(text(sql), params).fetchall()
        return result
    def get_eis_plots(self, Datei, soc):
        conn = st.connection("sql", type="sql")
        sql = """SELECT eis.*, files.datum, files.cycle, files.zelle, files.cap_cycle
                      FROM eis INNER JOIN files ON eis.datei = files.name
                      WHERE eis.datei = :datei AND eis.soc = :soc AND eis.typ = 'eis'"""
        params = {"datei": Datei, "soc": soc}
        with conn.session as s:
            result = s.execute(text(sql), params).fetchall()
        return result
    def get_lup(self):
        conn = st.connection("sql", type="sql")
        sql = """SELECT *
                 FROM eis
                 WHERE typ = 'lup' """
        return conn.query(sql)

    def get_deis(self):
        conn = st.connection("sql", type="sql")
        sql = """SELECT eis.soc, eis.freqhz, eis.calc_ima, eis.calc_rezohm, eis.calc_imzohm, eis.zohm, eis.phasezdeg,
                eis.temperaturec, files.cycle, files.zelle
                FROM eis INNER JOIN files ON eis.datei = files.name
                WHERE eis.typ = 'deis' """
        return conn.query(sql)

    def get_imp_bio(self):
        conn = st.connection("sql", type="sql")
        sql = """SELECT * 
                 FROM imp 
                 WHERE typ = 'Biologic' AND c_rate = 0.25"""
        return conn.query(sql)

    def get_imp_files(self):
        conn = st.connection("sql", type="sql")
        sql = """SELECT * 
                 FROM files 
                 where typ = 'imp'"""
        return conn.query(sql)
    def get_imp_rate(self,Datei):
        conn = st.connection("sql", type="sql")
        sql = """SELECT DISTINCT c_rate FROM imp 
                 WHERE datei = :datei
                 ORDER BY c_rate ASC"""
        params = {"datei": Datei}
        with conn.session as s:
            result = s.execute(text(sql), params).fetchall()
        return result
    def get_impedanz(self, Datei, c_rate):
        conn = st.connection("sql", type="sql")
        sql = """SELECT * FROM imp WHERE datei = :datei AND ROUND(c_rate, 2) = :c_rate"""
        params = {"datei": Datei, "c_rate": c_rate}
        with conn.session as s:
            result = s.execute(text(sql), params).fetchall()
        return result

    def get_impedanz_basy(self):
        conn = st.connection("sql", type="sql")
        sql = """SELECT * FROM imp WHERE typ = 'Basytec'"""
        return conn.query(sql)

    def get_impedanz_bio(self):
        conn = st.connection("sql", type="sql")
        sql = """SELECT * FROM imp WHERE typ = 'Biologic'"""
        return conn.query(sql)

    def get_basytec(self):
        conn = st.connection("sql", type="sql")
        sql = """SELECT * FROM basytec"""
        return conn.query(sql)

    def update_files(self, zelle):
        conn = st.connection("sql", type="sql")
        sql = "SELECT cap_p_cyc FROM zellen WHERE id = :zelle"
        params = {"zelle": zelle}
        cap = conn.query(sql, params=params)

    def get_form(self):
        conn = st.connection("sql", type="sql")
        sql = """SELECT * FROM form"""
        return conn.query(sql)


    def check_con(self):
        conn = st.connection("sql", type="sql")
        start = time.time()
        with conn.session as s:
            s.execute(text("SELECT 1"))
        end = time.time()
        return round(end - start,3)
