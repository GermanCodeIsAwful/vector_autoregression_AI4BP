from pathlib import Path
import pandas as pd
import numpy as np

START_DATE = "1990-01-01"
END_DATE = "2024-12-31"

# Dieses Script liegt im data-Ordner und schreibt die CSV direkt daneben.
OUT_DIR = Path(__file__).resolve().parent
OUT_FILE = OUT_DIR / "var_fred_macro.csv"

SERIES = {
    "UNRATE": "unemployment_rate",
    "CPIAUCSL": "cpi",
    "FEDFUNDS": "fed_funds_rate",
    "INDPRO": "industrial_production",
}

def load_fred_series(series_id: str, name: str) -> pd.DataFrame:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    df = pd.read_csv(url)
    df.columns = ["date", name]
    df["date"] = pd.to_datetime(df["date"])
    return df

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    data = None

    for series_id, name in SERIES.items():
        df = load_fred_series(series_id, name)
        data = df if data is None else data.merge(df, on="date", how="outer")

    data = data.sort_values("date")

    data = data[
        (data["date"] >= START_DATE) &
        (data["date"] <= END_DATE)
    ].copy()

    data["inflation_yoy"] = 100 * (
        np.log(data["cpi"]) - np.log(data["cpi"].shift(12))
    )

    data["industrial_production_growth_yoy"] = 100 * (
        np.log(data["industrial_production"])
        - np.log(data["industrial_production"].shift(12))
    )

    var_data = data[
        [
            "date",
            "inflation_yoy",
            "unemployment_rate",
            "fed_funds_rate",
            "industrial_production_growth_yoy",
        ]
    ].dropna()

    var_data.to_csv(OUT_FILE, index=False)

    print(f"Gespeichert: {OUT_FILE}")
    print(var_data.head())
    print(var_data.tail())

if __name__ == "__main__":
    main()