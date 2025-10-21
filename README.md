# 🔋 Analyse- und Visualisierungsanwendung für Zellmessdaten

Diese Anwendung wurde mit [Streamlit](https://streamlit.io) entwickelt und dient zur **Analyse, Verarbeitung und Visualisierung von Messdaten** aus Zellversuchen.  
Sie ermöglicht die interaktive Auswertung von Parametern, Zellen und Messwerten sowie die übersichtliche Darstellung von Kennwerten in Tabellen und Diagrammen.

---

## 🚀 Funktionen

- **Datenimport:** CSV- oder mpr-Dateien können direkt in der Anwendung geladen werden.  
- **Filterung:** Parameter (z. B. Zyklus, Zelle, Ladezustand) können gezielt ein- oder ausgeschlossen werden.  
- **Berechnung:** Kennwerte wie Mittelwerte, Differenzen oder normierte Kurven werden automatisch berechnet.  
- **Visualisierung:** Interaktive Diagramme für Zellverläufe, Trends und Vergleichsdaten.  
- **Export:** Ergebnisse lassen sich als CSV-Datei speichern.  

---

## 🧩 Voraussetzungen

- Python 3.10 oder neuer  
- Internetbrowser (z. B. Chrome, Firefox, Edge)  
- Empfohlene Bildschirmauflösung: 1920×1080  

---

## ⚙️ Installation (Nur WebApp)

1. Repository klonen:
   ```bash
   git clone https://github.com/janostoldy/Batterylab
   cd Batterylab
   ```

2. Virtuelle Umgebung erstellen und aktivieren:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # macOS/Linux
   .venv\Scripts\activate      # Windows
   ```

3. Abhängigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   ```
---
## ▶️ Anwendung starten (Nur WebApp)

```bash
streamlit run app.py
```

Anschließend öffnet sich automatisch der Browser unter  
👉 **http://localhost:8501**

---

## ⚙️ Installation (WebApp und Datenbank)
1. [Dockerdateien](docker) in Project-Ordner speichern ([Dockerfile](docker/Dockerfile) und [docker-compose.yml](docker/docker-compose.yml))
2. Credentials in [docker-compose.yml](docker/docker-compose.yml) anpassen
3. Container starten --> Erstellt Datebank und läde WebApp herunter:
    ```bash
       docker compose up -d
    ```
4. ```.dump```-Datei in Datenbank einfügen:
5. App mit Datenbank verbinden:
```.streamlit/secrets.toml``` im Verzeichnis erstellen und Verbindungsdetails 
mit Credentials einfügen:
   ```toml
   [connections.sql]
       host="localhost"
       port=5431
       url = "postgresql://postgres:<passwort>@localhost:5431/battery_db"
       username="postgres"
       passwort= "<passwort>"
   ```
6. Container neustarten
    ```bash
      docker compose restart
    ```
   
### Infos

- Die Konfiguration kann verwendet werden, um nur die Datenbank in Docker auszuführen.
- Die WebApp kann anschließend separat gestartet werden (siehe [Anleitung](#-installation-nur-webapp)).
- Entferne dazu den Abschnitt ```battery_app``` aus der Datei [docker-compose.yml](docker/docker-compose.yml).
- In diesem Fall läuft die WebApp über die Projektdateien, in denen direkt Änderungen vorgenommen werden können.

---

## 📂 Projektstruktur

```
├── app.py                # Hauptdatei der Streamlit-Anwendung
├── app_pages/            # Unterseiten der Streamlit-Anwendung
    ├── biologic.py       # Ermöglicht schnelles darstellen von .mpr-Datein
    ├── db.py             # Daten zur Datenbank hinzugügen und bearbeiten
    ├── dva.py            # Zeigt DVA-Kurven
    ├── ecd.py            # Bearbeiten von Ersatzschaltbildern (nicht verwendet) 
    ├── home.py           # Homescreen
    ├── impedanz.py       # Vergleich von Basytech/Safion und Biologic-Daten
    ├── kapa.py           # Kapazitätsanalyse
    ├── lup.py            # Zeigt Look-Up-Tables zur Temperaturschätzung, 
    │                     # Entwicklung der DEIS-Parameter und den Fehler dieser
    │                     # Parameter durch Formierung
    ├── niqhist.py        # Darstellung von Niquist und Bode-Diagrammen und Entwicklung von
    │                     # EIS-Parametern durch Formierung
    ├── pruefung.py       # Darstellung von Eingangsprüfung (nicht verwendet) 
    ├── safion.py         # Ermöglicht schnelles darstellen von .csv-Datein des Safions
    └── zellen.py         # Hinzufügen von Zellen zur Datenbank
├── classes/              
    ├── datenanalyse.py   # Auswertung der Ergebnisse
    └── datenbank.py      # Komunikation mit Datenbank
├── src/                  # Hilfsfunktionen zur Filterung oder Auswertung
├── requirements.txt      # Liste der Python-Abhängigkeiten
└── README.md             # Projektdokumentation
```

---

## 🧠 Beispielnutzung

1. Datei im Bereich **„Daten hinzufügen“** auswählen
2. Im Bereich **„EIS“** wechseln 
3. Parameter auswählen oder filtern 
4. Ergebnisse werden automatisch berechnet und angezeigt
5. Interaktive Diagramme ermöglichen Detailanalysen
6. Export der ergebnisse als ```.csv```-Datei

---

## 🧪 Verwendete Bibliotheken

- [Streamlit](https://streamlit.io/) – Weboberfläche  
- [pandas](https://pandas.pydata.org/) – Datenverarbeitung  
- [numpy](https://numpy.org/) – numerische Berechnungen  
- [plotly](https://plotly.com/python/) – Diagramme  
- [scipy](https://scipy.org) - Datenauswertung
- [galvani](https://github.com/echemdata/galvani) - Import von ```.mpr```-Datein

---

## 🧾 Darstellungen in der Arbeit

#### Preprocessing
- Verarbeitung der Daten --> [datenanalyse.py](classes/datenanalyse.py)
- Schreiben und Lesen aus Datenbank --> [datenbank.py](classes/datenbank.py)
#### Postprocessing und Darstellung
- Abbildung 2.9: [niqhist_app()](app_pages/niquist.py)
- Abbildung 2.10: [niqhist_app()](app_pages/niquist.py)
- Abbildung 4.1: [niqhist_app()](app_pages/niquist.py)
- Abbildung 4.2: [niqhist_app()](app_pages/niquist.py)
- Abbildung 4.3: [niqhist_app()](app_pages/niquist.py)
- Abbildung 4.4: [form_app() --> div_soc_cycle(...)](app_pages/niquist.py)
- Abbildung 4.5: [form_app() --> plot_soc_freq(...)](app_pages/niquist.py)
- Abbildung 4.6: Daten aus [form_app() --> plot_tab_zelle(...)](app_pages/niquist.py)
- Tabelle 4.2:  [form_app() --> plot_tab_zelle(...)](app_pages/niquist.py)
- Tabelle 4.3:  [form_app() --> plot_tab_zelle(...)](app_pages/niquist.py)
- Abbildung 4.7: [lup_app() --> deis_form_app()](app_pages/lup.py) --> Diagramme: SOC
- Tabelle 4.4: [lup_app() --> deis_form_app()](app_pages/lup.py) --> Diagramme: Zyklen
- Tabelle 4.5: [lup_app() --> deis_form_app()](app_pages/lup.py) --> Diagramme: Zyklen
- Abbildung 4.8: [kapazitaet_app](app_pages/kapa.py)
- Abbildung 4.9: [kapazitaet_app](app_pages/kapa.py)
- Abbildung 4.10: [lup_app() --> fit_app](app_pages/lup.py)
- Tabelle 4.5: [lup_app() --> fit_app](app_pages/lup.py)
- Tabelle 4.5: [lup_app() --> fit_app](app_pages/lup.py)
- Abbildung 4.11: [lup_app() --> fit_app](app_pages/lup.py)
- Abbildung 4.12: [basytec_app --> berechnen_app](app_pages/impedanz.py)
- Abbildung 4.13: [basytec_app --> berechnen_app](app_pages/impedanz.py)
- Abbildung 4.14: Manuell über [safion_app()](app_pages/safion.py) und [biologic_app() --> allgemein_app()](app_pages/biologic.py)


---

## 👤 Autor

Entwickelt von **janostoldy**  
Maschinenbau – Technische Universität München  
📍 München, Deutschland
