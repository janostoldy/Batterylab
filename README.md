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

## ⚙️ Installation

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

## ▶️ Anwendung starten

```bash
streamlit run app.py
```

Anschließend öffnet sich automatisch der Browser unter  
👉 **http://localhost:8501**

---

## 📂 Projektstruktur

```
├── app.py                # Hauptdatei der Streamlit-Anwendung
├── app_pages/            # Unterseiten der Streamlit-Anwendung
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

## 🧾 Lizenz


---

## 👤 Autor

Entwickelt von **<DEIN NAME>**  
Maschinenbau – Technische Universität München  
📍 München, Deutschland
