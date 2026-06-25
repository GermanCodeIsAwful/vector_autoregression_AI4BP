from pathlib import Path
from zipfile import ZipFile
import urllib.request

import pandas as pd


# =========================
# Einstellungen
# =========================

START_DATE = "2013-03-01"
END_DATE = "2017-02-28"

STATION = "Tiantan"

# Dieses Script liegt im data-Ordner und schreibt die CSV direkt daneben.
OUT_DIR = Path(__file__).resolve().parent

OUT_FILE = OUT_DIR / f"beijing_air_quality_{STATION.lower()}_daily_var.csv"

# WICHTIG: Das ist die konkrete PRSA-ZIP, nicht der generische UCI-Bundle-Download
DOWNLOAD_URL = (
    "https://archive.ics.uci.edu/ml/machine-learning-databases/00501/"
    "PRSA2017_Data_20130301-20170228.zip"
)

ZIP_FILE = OUT_DIR / "PRSA2017_Data_20130301-20170228.zip"
EXTRACT_DIR = OUT_DIR / "beijing_air_quality_raw"


def download_if_needed():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if ZIP_FILE.exists():
        print(f"ZIP existiert bereits: {ZIP_FILE}")
        return

    print("Lade Beijing-Air-Quality-Datensatz herunter...")
    urllib.request.urlretrieve(DOWNLOAD_URL, ZIP_FILE)
    print(f"Gespeichert: {ZIP_FILE}")


def extract_if_needed():
    if EXTRACT_DIR.exists() and any(EXTRACT_DIR.rglob("PRSA_Data_*.csv")):
        print(f"Daten sind bereits entpackt: {EXTRACT_DIR}")
        return

    print("Entpacke ZIP-Datei...")
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)

    with ZipFile(ZIP_FILE, "r") as z:
        z.extractall(EXTRACT_DIR)

    print(f"Entpackt nach: {EXTRACT_DIR}")


def load_station_data(station: str) -> pd.DataFrame:
    csv_files = list(EXTRACT_DIR.rglob("PRSA_Data_*.csv"))

    if not csv_files:
        all_csvs = list(EXTRACT_DIR.rglob("*.csv"))
        raise FileNotFoundError(
            "Keine PRSA_Data_*.csv-Dateien gefunden.\n"
            f"Gefundene CSV-Dateien: {[f.name for f in all_csvs]}"
        )

    matching_files = [
        f for f in csv_files
        if station.lower() in f.name.lower()
    ]

    if not matching_files:
        available = [f.name for f in csv_files]
        raise ValueError(
            f"Keine Datei für Station '{station}' gefunden.\n"
            f"Verfügbare Dateien:\n{available}"
        )

    file_path = matching_files[0]

    print(f"Lade Station: {station}")
    print(f"Datei: {file_path}")

    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()

    print("Spalten im Datensatz:")
    print(df.columns.tolist())

    required_cols = ["year", "month", "day", "hour"]
    missing = [col for col in required_cols if col not in df.columns]

    if missing:
        raise KeyError(
            f"Diese Datumsspalten fehlen: {missing}\n"
            f"Vorhandene Spalten: {df.columns.tolist()}"
        )

    df["datetime"] = pd.to_datetime(
        df[["year", "month", "day", "hour"]]
    )

    df = df.sort_values("datetime")
    df = df.set_index("datetime")

    return df


def prepare_daily_var_data(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "PM2.5",
        "NO2",
        "TEMP",
        "PRES",
        "WSPM",
    ]

    missing = [col for col in cols if col not in df.columns]

    if missing:
        raise KeyError(
            f"Diese Variablen fehlen: {missing}\n"
            f"Vorhandene Spalten: {df.columns.tolist()}"
        )

    df = df[cols].copy()

    for col in cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Fehlende Werte interpolieren
    df = df.interpolate(method="time")
    df = df.dropna()

    # Stündliche Daten zu Tagesdurchschnitten aggregieren
    daily = df.resample("D").mean()

    # Zeitraum filtern
    daily = daily.loc[START_DATE:END_DATE].copy()

    # Schönere Spaltennamen
    daily = daily.rename(
        columns={
            "PM2.5": "pm25",
            "NO2": "no2",
            "TEMP": "temperature",
            "PRES": "pressure",
            "WSPM": "wind_speed",
        }
    )

    daily = daily.reset_index()
    daily = daily.rename(columns={"datetime": "date"})

    return daily


def main():
    download_if_needed()
    extract_if_needed()

    hourly = load_station_data(STATION)
    daily_var_data = prepare_daily_var_data(hourly)

    daily_var_data.to_csv(OUT_FILE, index=False)

    print()
    print(f"CSV gespeichert unter: {OUT_FILE}")
    print()
    print("Erste Zeilen:")
    print(daily_var_data.head())
    print()
    print("Letzte Zeilen:")
    print(daily_var_data.tail())


if __name__ == "__main__":
    main()