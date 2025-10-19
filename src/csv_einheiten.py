import pandas as pd

# === Einstellungen ===
datei = "bode_form.csv"                # Pfad zur CSV-Datei
spalten = ["wert","div"]  # Spaltennamen, die *1000 genommen werden sollen
ausgabe_datei = "bode_form_milliohm.csv"        # Name der Ausgabedatei

# === CSV einlesen ===
df = pd.read_csv(datei)

# === Werte in den angegebenen Spalten mit 1000 multiplizieren ===
for spalte in spalten:
    if spalte in df.columns:
        df[spalte] = round(df[spalte] * 1000,6)
    else:
        print(f"Spalte '{spalte}' nicht gefunden!")

# === Neue Datei speichern ===
df.to_csv(ausgabe_datei, index=False)

print(f"Fertig! Datei '{ausgabe_datei}' wurde erstellt.")