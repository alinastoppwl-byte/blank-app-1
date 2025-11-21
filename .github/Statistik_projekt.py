import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------
# CSV EINLESEN
# -----------------------------
df = pd.read_csv("tommy_hilfiger_flights.csv")

# Datum konvertieren
df["date"] = pd.to_datetime(df["date"])

# -----------------------------
# MILES -> KM
# -----------------------------
df["distance_km"] = df["distance_miles"] * 1.60934

# -----------------------------
# ORTS-KOORDINATEN
# -----------------------------
coords = {
    "Michigen (BTL)": (42.3077, -85.2511),
    "Florida (PBI)": (26.6832, -80.0956),
    "Connecticut (HVN)": (41.2637, -72.8868),
    "California (VNY)": (34.2100, -118.4890),
    "Texas (AUS)": (30.1975, -97.6663)
}

df["lat_from"] = df["from"].map(lambda x: coords[x][0])
df["lon_from"] = df["from"].map(lambda x: coords[x][1])
df["lat_to"]   = df["to"].map(lambda x: coords[x][0])
df["lon_to"]   = df["to"].map(lambda x: coords[x][1])

# -----------------------------
# DUPLIKATE LINIEN FETTER ZEICHNEN
# -----------------------------
# Duplikate = Flüge gleicher Route (from->to)
route_counts = df.groupby(["from", "to"]).size().reset_index(name="count")

# count in Haupt-DF mergen
df = df.merge(route_counts, on=["from", "to"], how="left")

# Linienbreite bestimmen
# 1 Flug = 2px, 2 Flüge = 4px, 3 Flüge = 6px ...
df["line_width"] = df["count"].apply(lambda x: 2 + (x - 1) * 2)

# -----------------------------
# STATISTIK
# -----------------------------
total_distance = df["distance_km"].sum()
total_emission = total_distance * 2.5 / 1000  # Tonnen CO₂
avg_distance   = df["distance_km"].mean()

# Vergleich mit Pfaffenhofen CO₂
pfaffenhofen_emission = 5000  # Tonnen CO₂ pro Jahr (realistisch)
pfaffenhofen_percent = (total_emission / pfaffenhofen_emission) * 100

# -----------------------------
# UI
# -----------------------------
st.set_page_config(page_title="Tommy Hilfiger Flights", layout="wide")
st.title("🛩️ Privatjet-Tracker – Tommy Hilfiger")

st.write("""
Diese App zeigt echte Flugdaten von **Tommy Hilfiger** aus einer CSV-Datei,
zeichnet alle Flugrouten auf einer Weltkarte und hebt doppelte Routen hervor,
indem mehrfach geflogene Strecken **dicker** dargestellt werden.
""")

# KPIs
col1, col2, col3 = st.columns(3)
col1.metric("Anzahl Flüge", len(df))
col2.metric("Gesamtdistanz (km)", f"{total_distance:,.0f}")
col3.metric("CO₂-Ausstoß (t)", f"{total_emission:.2f}")

st.caption(
    f"Das entspricht **{pfaffenhofen_percent:.2f}%** der jährlichen "
    f"CO₂-Emissionen der Stadt *Pfaffenhofen a.d.Ilm* (≈5000 t/Jahr)."
)

# -----------------------------
# Datum-Slider
# -----------------------------
min_date, max_date = df["date"].min(), df["date"].max()

selected_date = st.slider(
    "Flüge bis folgendem Datum anzeigen:",
    min_value=min_date.date(),
    max_value=max_date.date(),
    value=max_date.date()
)

filtered = df[df["date"].dt.date <= selected_date]

# -----------------------------
# WELTKARTE
# -----------------------------
st.subheader("🌍 Flugroutenkarte")

fig = px.scatter_geo()

# Linien einzeln hinzufügen (mit variabler Dicke)
for _, row in filtered.iterrows():
    fig.add_trace(px.line_geo(
        lat=[row["lat_from"], row["lat_to"]],
        lon=[row["lon_from"], row["lon_to"]],
    ).data[0].update(line=dict(width=row["line_width"], color="red")))

fig.update_layout(
    height=650,
    showlegend=False,
    margin=dict(l=0, r=0, t=30, b=0),
    title="Flugrouten von Tommy Hilfiger (doppelte Strecken dicker)"
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Tabelle
# -----------------------------
st.subheader("📋 Flugdaten (gefiltert)")
st.dataframe(filtered[[
    "date","from","to","distance_miles","distance_km","count"
]])

st.info("Dicke Linien = Strecken, die mehrfach geflogen wurden.")
