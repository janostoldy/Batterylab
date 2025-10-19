import numpy as np
import streamlit as st

def mean_pairwise_abs_diff(x):
    x = np.asarray(x)
    x = x[~np.isnan(x)]         # NaNs entfernen falls nötig
    n = x.size
    if n < 2:
        return 0.0
    x_sorted = np.sort(x)       # O(n log n)
    k = np.arange(1, n+1)       # 1..n
    S = (x_sorted * (2*k - n - 1)).sum()
    mean = 2.0 * S / (n * (n - 1))
    return mean

# Funktion zur Berechnung der relativen Abweichung zum Median
def max_dev_to_median(x):
    med = np.median(x)
    return max(np.abs(x - med) / med)

def robust_start_end_median(df):
    med_start = df.iloc[0]
    med_end = df.iloc[-3:].median()
    delta_abs = med_end - med_start
    delta_rel = delta_abs / abs(med_start)
    return delta_rel

def robust_start_end_theo_median(df,zelle):
    med_start = df.iloc[0]
    if zelle in ['JT_VTC_003', 'JT_VTC_006', 'JT_VTC_010']:
        med_end = df.iloc[7:9].median()
    elif zelle in ['JT_VTC_004', 'JT_VTC_007', 'JT_VTC_009']:
        med_end = df.iloc[6:8].median()
    else:
        med_end = df.iloc[5:7].median()
    delta_abs = med_end - med_start
    delta_rel = delta_abs / abs(med_start)
    return delta_rel

def robust_start_end_abw(df, tol=0.05):
    if "wert" in df.columns:
        werte = df["wert"]
    elif "median" in df.columns:
        werte = df["median"]
    else:
        return -1
    med_end = werte.iloc[-3:].median()
    for z, wert in enumerate(werte.values):
        delta_abs = abs((wert - med_end)/ med_end)
        if delta_abs < tol:
            return df['cycle'].iloc[z]
    return -1

def normiere_kurve(gruppe):
    startwert = gruppe['wert'].iloc[0]
    gruppe['wert'] = gruppe['wert'] / startwert
    return gruppe