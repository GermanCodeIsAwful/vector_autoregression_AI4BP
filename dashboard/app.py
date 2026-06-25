from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

DATASETS = {
    "fred": {
        "label": "FRED Makro (Monatsdaten)",
        "path": ROOT / "data" / "var_fred_macro.csv",
        "question": "Wie hängen Inflation, Arbeitslosigkeit, Leitzins und Industrieproduktion über die Zeit zusammen?",
        "default": [
            "inflation_yoy",
            "unemployment_rate",
            "fed_funds_rate",
            "industrial_production_growth_yoy",
        ],
        "max_lag": 18,
        "default_horizon": 24,
        "max_horizon": 72,
        "period_name": "Monate",
    },
    "beijing": {
        "label": "Beijing Tiantan Air Quality (Tagesdaten)",
        "path": ROOT / "data" / "beijing_air_quality_tiantan_daily_var.csv",
        "question": "Wie hängen PM2.5, NO2, Temperatur, Luftdruck und Wind über die Zeit zusammen?",
        "default": ["pm25", "no2", "temperature", "pressure", "wind_speed"],
        "max_lag": 21,
        "default_horizon": 90,
        "max_horizon": 180,
        "period_name": "Tage",
    },
}

NAMES = {
    "inflation_yoy": "Inflation",
    "unemployment_rate": "Arbeitslosigkeit",
    "fed_funds_rate": "Fed Funds Rate",
    "industrial_production_growth_yoy": "Industrieproduktion",
    "pm25": "PM2.5",
    "no2": "NO2",
    "log_pm25": "log PM2.5",
    "log_no2": "log NO2",
    "log_inflation_yoy": "log Inflation",
    "log_unemployment_rate": "log Arbeitslosigkeit",
    "log_fed_funds_rate": "log Fed Funds Rate",
    "log_industrial_production_growth_yoy": "log Industrieproduktion",
    "temperature": "Temperatur",
    "pressure": "Luftdruck",
    "wind_speed": "Wind",
}


def nice(name: str) -> str:
    if name in NAMES:
        return NAMES[name]
    if name.startswith("log_"):
        return "log " + nice(name[4:])
    if name.startswith("slog_"):
        return "signed log " + nice(name[5:])
    return name.replace("_", " ")


def load_dataset(key: str) -> pd.DataFrame:
    df = pd.read_csv(DATASETS[key]["path"], parse_dates=["date"]).sort_values("date")
    df = df.set_index("date")
    if not df.index.is_unique:
        raise ValueError("Die Datumsachse enthält Duplikate.")
    if df.isna().any().any():
        raise ValueError("Die Demo erwartet vollständige Zeitreihen ohne Missing Values.")
    return df


def signed_log1p(series: pd.Series) -> pd.Series:
    return np.sign(series) * np.log1p(np.abs(series))


def signed_expm1(series: pd.Series) -> pd.Series:
    return np.sign(series) * np.expm1(np.abs(series))


def inverse_if_needed(series: pd.Series, inverse_kind: str | None) -> tuple[pd.Series, str]:
    if inverse_kind == "log1p":
        return np.expm1(series), "rückgerechnete Originaleinheiten"
    if inverse_kind == "signed_log1p":
        return signed_expm1(series), "rückgerechnete Originaleinheiten"
    return series, "Modell-Einheiten"


def transform_frame(
    raw: pd.DataFrame,
    selected: list[str],
    mode: str,
    dataset_key: str,
) -> tuple[pd.DataFrame, list[str], dict[str, str]]:
    out = pd.DataFrame(index=raw.index)
    notes: list[str] = []
    inverse_map: dict[str, str] = {}

    for col in selected:
        series = raw[col].astype(float)

        if mode.startswith("Log1p"):
            if series.min() >= 0:
                name = f"log_{col}" if not col.startswith("log_") else col
                out[name] = np.log1p(series)
                inverse_map[name] = "log1p"
                notes.append(f"{nice(col)} wird mit log1p transformiert.")
            else:
                out[col] = series
                notes.append(f"{nice(col)} bleibt roh, weil log1p bei negativen Werten nicht passt.")

        elif mode.startswith("Signed Log1p"):
            name = f"slog_{col}" if not col.startswith("slog_") else col
            out[name] = signed_log1p(series)
            inverse_map[name] = "signed_log1p"
            notes.append(f"{nice(col)} wird mit signed log1p transformiert.")

        else:
            out[col] = series

    out = out.dropna()

    if mode.startswith("Z-Skalierung"):
        mu = out.mean()
        sigma = out.std(ddof=0).replace(0, 1.0)
        out = (out - mu) / sigma
        inverse_map.clear()
        notes.append("Alle gewählten Reihen werden als z-Werte dargestellt: Mittelwert 0, Standardabweichung 1.")

    if "Differenzen" in mode:
        out = out.diff().dropna()
        inverse_map.clear()
        notes.append("Das Modell arbeitet auf ersten Differenzen, also Veränderungen statt Niveaus.")

    return out.dropna(), notes, inverse_map


def valid_lag_limit(n_obs: int, n_vars: int, wanted: int) -> int:
    return max(1, min(wanted, (n_obs - 2) // (n_vars + 1)))


def make_lag_matrix(frame: pd.DataFrame, p: int) -> tuple[np.ndarray, np.ndarray, list[str]]:
    arr = np.asarray(frame, dtype=float)
    n_obs, n_vars = arr.shape

    if n_obs <= p:
        raise ValueError("Nicht genug Beobachtungen für diese Lag-Ordnung.")

    x_parts = [np.ones((n_obs - p, 1))]
    names = ["const"]

    for lag in range(1, p + 1):
        x_parts.append(arr[p - lag : n_obs - lag])
        names.extend(f"{col}_lag{lag}" for col in frame.columns)

    return np.hstack(x_parts), arr[p:], names


def fit_var(frame: pd.DataFrame, p: int) -> dict[str, object]:
    x, y, names = make_lag_matrix(frame, p)
    coef = np.linalg.lstsq(x, y, rcond=None)[0]
    resid = y - x @ coef
    sigma_u = (resid.T @ resid) / max(len(resid), 1)

    return {
        "p": p,
        "columns": list(frame.columns),
        "coef": coef,
        "resid": resid,
        "sigma_u": sigma_u,
        "x_names": names,
    }


def lag_criteria(frame: pd.DataFrame, max_lag: int) -> pd.DataFrame:
    k = frame.shape[1]
    rows = []

    for p in range(1, max_lag + 1):
        model = fit_var(frame, p)
        resid = np.asarray(model["resid"])
        n_eff = len(resid)

        sign, logdet = np.linalg.slogdet(np.asarray(model["sigma_u"]))
        if sign <= 0 or not np.isfinite(logdet):
            logdet = math.log(max(float(np.linalg.det(np.asarray(model["sigma_u"]))), 1e-12))

        params = k * (k * p + 1)

        rows.append(
            {
                "p": p,
                "effective_n": n_eff,
                "parameters": params,
                "aic": logdet + 2 * params / n_eff,
                "bic": logdet + math.log(n_eff) * params / n_eff,
            }
        )

    return pd.DataFrame(rows)


def validation_lag_scores(
    train_z: pd.DataFrame,
    max_lag: int,
    requested_horizon: int,
    target: str,
) -> pd.DataFrame:
    """
    Interne Validierung nur auf Trainingsdaten:
    - letzter Teil der Trainingsdaten = Validierung
    - davor wird geschätzt
    - Lag mit kleinstem Zielvariablen-RMSE kann gewählt werden
    """
    if len(train_z) < 20:
        return pd.DataFrame(columns=["p", "validierungs_rmse", "validierungs_rmse_gesamt", "validierungs_horizont"])

    val_horizon = min(max(2, requested_horizon), max(2, len(train_z) // 4))
    inner_train = train_z.iloc[:-val_horizon]
    validation = train_z.iloc[-val_horizon:]

    rows = []

    for p in range(1, max_lag + 1):
        if len(inner_train) <= p + 2:
            continue

        try:
            model = fit_var(inner_train, p)
            pred = forecast_var(model, inner_train, len(validation))
        except Exception:
            continue

        pred_df = pd.DataFrame(pred, index=validation.index, columns=train_z.columns)

        target_rmse = float(np.sqrt(((pred_df[target] - validation[target]) ** 2).mean()))
        overall_rmse = float(np.sqrt(((pred_df - validation) ** 2).mean().mean()))

        rows.append(
            {
                "p": p,
                "validierungs_rmse": target_rmse,
                "validierungs_rmse_gesamt": overall_rmse,
                "validierungs_horizont": val_horizon,
            }
        )

    return pd.DataFrame(rows)


def coefficient_block(model: dict[str, object], lag: int = 1) -> pd.DataFrame:
    cols = list(model["columns"])
    k = len(cols)
    start = 1 + (lag - 1) * k
    block = np.asarray(model["coef"])[start : start + k, :].T
    return pd.DataFrame(block, index=cols, columns=cols)


def companion_roots(model: dict[str, object]) -> np.ndarray:
    cols = list(model["columns"])
    k = len(cols)
    p = int(model["p"])
    coef = np.asarray(model["coef"])

    blocks = [coef[1 + lag * k : 1 + (lag + 1) * k, :].T for lag in range(p)]
    top = np.hstack(blocks)

    if p == 1:
        companion = top
    else:
        lower = np.hstack([np.eye(k * (p - 1)), np.zeros((k * (p - 1), k))])
        companion = np.vstack([top, lower])

    return np.linalg.eigvals(companion)


def resid_acf1(model: dict[str, object]) -> pd.Series:
    resid = np.asarray(model["resid"])
    out = {}

    for i, col in enumerate(model["columns"]):
        out[col] = np.corrcoef(resid[:-1, i], resid[1:, i])[0, 1] if len(resid) > 2 else np.nan

    return pd.Series(out)


def granger_sse_improvement(frame: pd.DataFrame, p: int, source: str, target: str) -> float:
    x, y_all, _ = make_lag_matrix(frame, p)
    cols = list(frame.columns)
    k = len(cols)

    source_i = cols.index(source)
    target_i = cols.index(target)
    y = y_all[:, target_i]

    beta_full = np.linalg.lstsq(x, y, rcond=None)[0]
    sse_full = float((y - x @ beta_full) @ (y - x @ beta_full))

    keep = np.ones(x.shape[1], dtype=bool)
    for lag in range(p):
        keep[1 + lag * k + source_i] = False

    beta_restricted = np.linalg.lstsq(x[:, keep], y, rcond=None)[0]
    sse_restricted = float((y - x[:, keep] @ beta_restricted) @ (y - x[:, keep] @ beta_restricted))

    return 100 * (sse_restricted - sse_full) / max(sse_restricted, 1e-12)


def granger_table(frame: pd.DataFrame, p: int) -> pd.DataFrame:
    rows = []

    for target in frame.columns:
        for source in frame.columns:
            if source != target:
                rows.append(
                    {
                        "Quelle": source,
                        "Ziel": target,
                        "SSE-Verbesserung %": granger_sse_improvement(frame, p, source, target),
                    }
                )

    return pd.DataFrame(rows).sort_values("SSE-Verbesserung %", ascending=False)


def impulse_response(model: dict[str, object], shock: str, steps: int, size: float) -> pd.DataFrame:
    cols = list(model["columns"])
    k = len(cols)
    p = int(model["p"])
    coef = np.asarray(model["coef"])

    shock_vec = np.zeros(k)
    shock_vec[cols.index(shock)] = size
    responses = [shock_vec]

    for h in range(1, steps + 1):
        y = np.zeros(k)
        for lag in range(1, p + 1):
            prev = responses[h - lag] if h - lag >= 0 else np.zeros(k)
            block = coef[1 + (lag - 1) * k : 1 + lag * k, :]
            y += prev @ block
        responses.append(y)

    return pd.DataFrame(responses, columns=cols, index=pd.RangeIndex(steps + 1, name="Horizont"))


def forecast_var(model: dict[str, object], history: pd.DataFrame, steps: int) -> np.ndarray:
    hist = [row.copy() for row in np.asarray(history, dtype=float)[-int(model["p"]) :]]
    preds = []

    for _ in range(steps):
        x = [1.0]
        for lag in range(1, int(model["p"]) + 1):
            x.extend(hist[-lag])

        y = np.asarray(x) @ np.asarray(model["coef"])
        preds.append(y)
        hist.append(y)

    return np.asarray(preds)


def rolling_one_step_forecast_var(
    train_z: pd.DataFrame,
    test_model_units: pd.DataFrame,
    mu: pd.Series,
    sigma: pd.Series,
    p: int,
) -> pd.DataFrame:
    """
    Rollierender 1-Step-Testforecast:
    - Für jeden Testzeitpunkt wird mit allen bis dahin bekannten echten Daten neu geschätzt.
    - Das ist oft besser im Backtest, aber nicht dasselbe wie ein echter Mehrschritt-Forecast in die Zukunft.
    """
    history_z = train_z.copy()
    preds_z = []

    for idx, row in test_model_units.iterrows():
        model_i = fit_var(history_z, p)
        pred_z = forecast_var(model_i, history_z, 1)[0]
        preds_z.append(pred_z)

        actual_z_row = ((row - mu) / sigma).to_frame().T
        actual_z_row.index = [idx]
        history_z = pd.concat([history_z, actual_z_row], axis=0)

    pred_z_df = pd.DataFrame(preds_z, index=test_model_units.index, columns=test_model_units.columns)
    return pred_z_df * sigma.to_numpy() + mu.to_numpy()


def split_scale(frame: pd.DataFrame, horizon: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    train = frame.iloc[:-horizon]
    test = frame.iloc[-horizon:]

    mu = train.mean()
    sigma = train.std(ddof=0).replace(0, 1.0)

    return (train - mu) / sigma, test, mu, sigma


def pretty_columns(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.rename(columns={col: nice(str(col)) for col in frame.columns})


def pretty_index(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out.index = [nice(str(i)) for i in out.index]
    return out


def _self_check() -> None:
    for key, cfg in DATASETS.items():
        raw = load_dataset(key)
        frame, _, _ = transform_frame(raw, cfg["default"], "Rohwerte", key)

        horizon = min(cfg["default_horizon"], max(4, len(frame) // 5))
        train_z, test, mu, sigma = split_scale(frame, horizon)

        max_lag = min(3, valid_lag_limit(len(train_z), train_z.shape[1], cfg["max_lag"]))
        criteria = lag_criteria(train_z, max_lag)
        p = int(criteria.loc[criteria["bic"].idxmin(), "p"])

        model = fit_var(train_z, p)
        forecast = forecast_var(model, train_z, min(3, len(test)))
        rolling = rolling_one_step_forecast_var(train_z, test.iloc[: min(3, len(test))], mu, sigma, p)
        roots = companion_roots(model)
        irf = impulse_response(model, list(model["columns"])[0], 3, 1.0)

        assert forecast.shape[1] == frame.shape[1]
        assert rolling.shape[1] == frame.shape[1]
        assert irf.shape == (4, frame.shape[1])
        assert np.isfinite(np.abs(roots)).all()
        assert np.isfinite(mu.to_numpy()).all()
        assert np.isfinite(sigma.to_numpy()).all()

    print("Self-check: ok")


def run_app() -> None:
    import altair as alt
    import streamlit as st

    st.set_page_config(page_title="VAR Live-Demo", layout="wide")

    def line_chart(frame: pd.DataFrame, title: str, markers: bool = False, y_title: str = "Wert"):
        plot = pretty_columns(frame).copy()
        x_label = plot.index.name or "Index"

        long = plot.reset_index().rename(columns={plot.reset_index().columns[0]: "x"})
        long = long.melt("x", var_name="Reihe", value_name="Wert").dropna()

        x_type = "T" if pd.api.types.is_datetime64_any_dtype(plot.index) else "Q"

        base = alt.Chart(long).encode(
            x=alt.X(f"x:{x_type}", title=x_label),
            y=alt.Y("Wert:Q", title=y_title),
            color=alt.Color("Reihe:N", title=""),
            tooltip=[
                alt.Tooltip(f"x:{x_type}", title=x_label),
                "Reihe:N",
                alt.Tooltip("Wert:Q", format=".3f"),
            ],
        )

        chart = base.mark_line()
        if markers:
            chart = chart + base.mark_point(size=20)

        return chart.properties(title=title, height=320).interactive()

    def forecast_chart(
        train_actual: pd.Series,
        test_actual: pd.Series,
        forecast_dynamic: pd.Series,
        forecast_rolling: pd.Series,
        naive: pd.Series,
        title: str,
        split_at,
        visible_series: list[str] | set[str] | None = None,
        markers: bool = False,
        y_title: str = "Wert",
    ):
        def as_rows(series: pd.Series, label: str) -> pd.DataFrame:
            return pd.DataFrame(
                {
                    "x": series.index,
                    "Reihe": label,
                    "Wert": series.to_numpy(dtype=float),
                }
            )

        available_series = {
            "Train Ist": train_actual,
            "Test Ist": test_actual,
            "VAR Forecast dynamisch": forecast_dynamic,
            "VAR Forecast rollierend 1-Step": forecast_rolling,
            "Naiver Forecast": naive,
        }
        visible = set(visible_series or available_series.keys())
        selected_parts = [as_rows(series, label) for label, series in available_series.items() if label in visible]
        plot = pd.concat(selected_parts, ignore_index=True).dropna() if selected_parts else pd.DataFrame(
            columns=["x", "Reihe", "Wert"]
        )

        x_is_date = pd.api.types.is_datetime64_any_dtype(plot["x"])
        x_type = "T" if x_is_date else "Q"
        x_label = train_actual.index.name or "Datum"

        base = alt.Chart(plot).encode(
            x=alt.X(f"x:{x_type}", title=x_label),
            y=alt.Y("Wert:Q", title=y_title),
            color=alt.Color("Reihe:N", title=""),
            tooltip=[
                alt.Tooltip(f"x:{x_type}", title=x_label),
                "Reihe:N",
                alt.Tooltip("Wert:Q", format=".3f"),
            ],
        )

        lines = base.mark_line()
        if markers:
            lines = lines + base.mark_point(size=20)

        split_data = pd.DataFrame({"x": [split_at], "Label": ["Start Test / Forecast"]})
        split_rule = (
            alt.Chart(split_data)
            .mark_rule(color="red", strokeWidth=2)
            .encode(
                x=alt.X(f"x:{x_type}"),
                tooltip=[
                    alt.Tooltip(f"x:{x_type}", title="Split"),
                    alt.Tooltip("Label:N", title=""),
                ],
            )
        )

        return (lines + split_rule).properties(title=title, height=400).interactive()

    def bar_chart(series: pd.Series, title: str, y_title: str = "Wert"):
        data = pd.DataFrame({"Reihe": [nice(str(i)) for i in series.index], "Wert": series.to_numpy()})

        return (
            alt.Chart(data)
            .mark_bar()
            .encode(
                x=alt.X("Reihe:N", sort="-y", title=""),
                y=alt.Y("Wert:Q", title=y_title),
                tooltip=["Reihe:N", alt.Tooltip("Wert:Q", format=".3f")],
            )
            .properties(title=title, height=280)
        )

    def heatmap(frame: pd.DataFrame, title: str):
        plot = frame.copy()
        plot.index = [nice(str(i)) for i in plot.index]
        plot.columns = [nice(str(c)) for c in plot.columns]

        long = plot.reset_index(names="Ziel").melt("Ziel", var_name="Quelle", value_name="Koeffizient")

        return (
            alt.Chart(long)
            .mark_rect()
            .encode(
                x=alt.X("Quelle:N", title="Quelle Lag 1"),
                y=alt.Y("Ziel:N", title="Ziel heute"),
                color=alt.Color("Koeffizient:Q", scale=alt.Scale(scheme="redblue", reverse=True)),
                tooltip=["Quelle:N", "Ziel:N", alt.Tooltip("Koeffizient:Q", format=".3f")],
            )
            .properties(title=title, height=320)
        )

    st.title("VAR Live-Demo")
    st.caption("Interaktive, sachliche Aufbereitung der Hands-on-Notebooks zu FRED und Beijing.")

    dataset_key = st.sidebar.selectbox(
        "Datensatz",
        list(DATASETS),
        format_func=lambda key: DATASETS[key]["label"],
    )
    cfg = DATASETS[dataset_key]
    raw_all = load_dataset(dataset_key)

    date_min = raw_all.index.min().date()
    date_max = raw_all.index.max().date()

    chosen_dates = st.sidebar.date_input(
        "Zeitraum",
        value=(date_min, date_max),
        min_value=date_min,
        max_value=date_max,
    )

    if isinstance(chosen_dates, tuple) and len(chosen_dates) == 2:
        start, end = pd.to_datetime(chosen_dates[0]), pd.to_datetime(chosen_dates[1])
    else:
        start, end = pd.to_datetime(date_min), pd.to_datetime(date_max)

    raw = raw_all.loc[(raw_all.index >= start) & (raw_all.index <= end)]

    selected = st.sidebar.multiselect("Variablen", list(raw.columns), default=cfg["default"])
    if len(selected) < 2:
        st.warning("Bitte mindestens zwei Variablen wählen.")
        st.stop()

    modes = [
        "Rohwerte",
        "Log1p für positive Reihen",
        "Signed Log1p für alle Reihen",
        "Z-Skalierung",
        "Erste Differenzen",
        "Log1p + erste Differenzen",
        "Signed Log1p + erste Differenzen",
    ]

    mode = st.sidebar.selectbox("Transformation", modes)
    show_markers = st.sidebar.checkbox("Datenpunkte markieren", value=False)

    frame, notes, inverse_map = transform_frame(raw, selected, mode, dataset_key)

    if len(frame) < 30:
        st.warning("Der gewählte Zeitraum ist für diese Demo zu kurz.")
        st.stop()

    target = st.sidebar.selectbox(
        "Forecast-Zielvariable",
        list(frame.columns),
        format_func=nice,
    )

    max_h = max(2, len(frame) // 2)
    default_h = min(cfg["default_horizon"], max_h)

    horizon = st.sidebar.slider(
        "Test-/Forecast-Horizont",
        2,
        max_h,
        default_h,
    )

    train_len = len(frame) - horizon
    max_lag = valid_lag_limit(train_len, len(frame.columns), cfg["max_lag"])
    max_lag = st.sidebar.slider("Max. Lag prüfen", 1, max_lag, min(max_lag, cfg["max_lag"]))

    lag_mode = st.sidebar.radio(
        "Lag wählen nach",
        ["BIC", "AIC", "Validierung RMSE", "manuell"],
        horizontal=True,
    )

    manual_lag = st.sidebar.slider("Manueller Lag", 1, max_lag, min(2, max_lag))

    train_z, test_model_units, mu, sigma = split_scale(frame, horizon)

    criteria = lag_criteria(train_z, max_lag)
    validation_scores = validation_lag_scores(train_z, max_lag, horizon, target)

    if not validation_scores.empty:
        criteria = criteria.merge(validation_scores, on="p", how="left")
    else:
        criteria["validierungs_rmse"] = np.nan
        criteria["validierungs_rmse_gesamt"] = np.nan
        criteria["validierungs_horizont"] = np.nan

    if lag_mode == "manuell":
        p = manual_lag
    elif lag_mode == "Validierung RMSE":
        if criteria["validierungs_rmse"].notna().any():
            p = int(criteria.loc[criteria["validierungs_rmse"].idxmin(), "p"])
        else:
            p = int(criteria.loc[criteria["bic"].idxmin(), "p"])
            st.sidebar.warning("Validierung nicht möglich. BIC wird verwendet.")
    else:
        p = int(criteria.loc[criteria[lag_mode.lower()].idxmin(), "p"])

    model = fit_var(train_z, p)

    roots = companion_roots(model)
    max_root = float(np.max(np.abs(roots)))
    acf1 = resid_acf1(model)
    params = len(frame.columns) * (len(frame.columns) * p + 1)

    granger = granger_table(train_z, p)

    forecast_z = forecast_var(model, train_z, horizon)
    forecast_model = pd.DataFrame(
        forecast_z * sigma.to_numpy() + mu.to_numpy(),
        index=test_model_units.index,
        columns=frame.columns,
    )

    rolling_forecast_model = rolling_one_step_forecast_var(
        train_z=train_z,
        test_model_units=test_model_units,
        mu=mu,
        sigma=sigma,
        p=p,
    )

    naive_model = pd.DataFrame(
        np.repeat(frame.iloc[[-horizon - 1]].to_numpy(), horizon, axis=0),
        index=test_model_units.index,
        columns=frame.columns,
    )

    rmse = pd.DataFrame(
        {
            "VAR dynamisch": np.sqrt(((forecast_model - test_model_units) ** 2).mean()),
            "VAR rollierend 1-Step": np.sqrt(((rolling_forecast_model - test_model_units) ** 2).mean()),
            "Naiver letzter Wert": np.sqrt(((naive_model - test_model_units) ** 2).mean()),
        }
    )

    rmse["Gewinner"] = rmse.idxmin(axis=1)

    shock = st.sidebar.selectbox("IRF-Schockvariable", list(frame.columns), format_func=nice)
    shock_size = st.sidebar.slider("Schockgröße in Standardabweichungen", 0.5, 3.0, 1.0, 0.5)
    irf_steps = st.sidebar.slider("IRF-Horizont", 4, min(60, cfg["max_horizon"]), min(24, cfg["default_horizon"]))

    with st.sidebar.expander("Kurz erklärt: Bedienung"):
        st.markdown(
            """
            - **Forecast-Zielvariable**: Reihe, die im Forecast-Tab detailliert angezeigt wird.
            - **Horizont**: letzte Beobachtungen, die als Test/Forecast-Zeitraum genutzt werden.
            - **Max. Lag prüfen**: bis zu welcher Verzögerung AIC/BIC/Validierung suchen.
            - **Validierung RMSE**: wählt den Lag, der auf einem internen Validierungsfenster den kleinsten Fehler hat.
            - **Manueller Lag**: setzt die Lag-Länge direkt.
            """
        )

    st.subheader(cfg["label"])
    st.write(cfg["question"])

    if notes:
        st.info(" ".join(notes))

    metric_cols = st.columns(5)
    metric_cols[0].metric("Beobachtungen", f"{len(frame):,}".replace(",", "."))
    metric_cols[1].metric("Variablen", len(frame.columns))
    metric_cols[2].metric("VAR-Lag", p)
    metric_cols[3].metric("Parameter", params)
    metric_cols[4].metric("Stabilität", "ok" if max_root < 1 else "kritisch", f"Wurzel {max_root:.3f}")

    tab_data, tab_model, tab_forecast, tab_experiments = st.tabs(
        ["Daten", "VAR-Lauf", "Forecast", "Experimente"]
    )

    with tab_data:
        st.markdown("**Datenblick**")
        st.write("Erst die Reihen prüfen: Ausreißer, Trends und Skalen sieht man hier schneller als in Koeffizienten.")

        with st.expander("Kurz erklärt: Transformation"):
            st.markdown(
                """
                - **Rohwerte**: Werte gehen unverändert ins Modell.
                - **Log1p**: dämpft starke Ausschläge, funktioniert aber nur sinnvoll bei nichtnegativen Reihen.
                - **Signed Log1p**: dämpft Ausschläge auch bei negativen Werten, z. B. bei FRED-Wachstumsraten.
                - **Z-Skalierung**: setzt jede Reihe auf Mittelwert 0 und Standardabweichung 1.
                - **Erste Differenzen**: modelliert Veränderungen statt Niveaus.
                - **Log + Differenzen**: oft sinnvoll, wenn Trends oder starke Skalenunterschiede die Prognose stören.
                """
            )

        st.altair_chart(
            line_chart(
                (frame - frame.mean()) / frame.std(ddof=0).replace(0, 1.0),
                "Ausgewählte Modellreihen, z-skaliert",
                show_markers,
            ),
            width="stretch",
        )

        st.dataframe(
            pretty_index(frame.describe().T[["mean", "std", "min", "max"]]).round(3),
            width="stretch",
        )

    with tab_model:
        st.markdown("**Lag-Auswahl und Modellcheck**")
        st.write("AIC wählt oft mehr Dynamik, BIC meist sparsamer. Validierung RMSE optimiert direkt den Prognosefehler.")

        with st.expander("Kurz erklärt: AIC, BIC, Validierung und Lag"):
            st.markdown(
                """
                - **Lag p**: Anzahl vergangener Zeitpunkte, die das VAR-Modell nutzt.
                - **AIC**: bestraft viele Parameter eher mild und wählt deshalb oft mehr Lags.
                - **BIC**: bestraft viele Parameter stärker und wählt deshalb oft einfachere Modelle.
                - **Validierung RMSE**: testet Lags auf einem zurückgehaltenen Teil der Trainingsdaten.
                - **Kleiner ist besser**: bei AIC, BIC und RMSE gewinnt jeweils der niedrigste Wert.
                """
            )

        criteria_display = criteria.set_index("p").copy()

        st.altair_chart(
            line_chart(criteria_display[["aic", "bic"]], "Informationskriterien", True),
            width="stretch",
        )

        if criteria["validierungs_rmse"].notna().any():
            st.altair_chart(
                line_chart(
                    criteria_display[["validierungs_rmse"]],
                    f"Validierungs-RMSE für {nice(target)}",
                    True,
                    "RMSE",
                ),
                width="stretch",
            )

        st.dataframe(criteria.round(4), width="stretch")

        left, right = st.columns(2)

        with left:
            with st.expander("Kurz erklärt: Koeffizienten"):
                st.markdown(
                    """
                    - Zeigt, wie stark eine Variable aus der Vergangenheit mit einer heutigen Variable zusammenhängt.
                    - Positive Werte sprechen für gleichläufige Bewegung, negative für gegenläufige Bewegung.
                    """
                )

            st.altair_chart(
                heatmap(coefficient_block(model, 1), "Koeffizienten Lag 1"),
                width="stretch",
            )

        with right:
            with st.expander("Kurz erklärt: Residual-Autokorrelation"):
                st.markdown(
                    """
                    - Residuen sind die Modellfehler.
                    - Autokorrelation nahe 0 ist gut, weil dann wenig systematische Restdynamik übrig bleibt.
                    """
                )

            st.altair_chart(
                bar_chart(acf1, "Residual-Autokorrelation Lag 1", "Korrelation"),
                width="stretch",
            )

        with st.expander("Kurz erklärt: RMSE"):
            st.markdown(
                """
                - **RMSE** misst den durchschnittlichen Prognosefehler.
                - Niedriger ist besser.
                - **VAR dynamisch** prognostiziert den kompletten Testzeitraum nur aus den Trainingsdaten.
                - **VAR rollierend 1-Step** schätzt im Test Schritt für Schritt neu mit den bereits bekannten Ist-Werten.
                - **Naiver Forecast** nutzt einfach den letzten bekannten Wert als Prognose.
                """
            )

        st.dataframe(
            pretty_index(rmse.rename(index={i: nice(str(i)) for i in rmse.index}).round(3)),
            width="stretch",
        )

    with tab_forecast:
        st.markdown("**Forecast-Test mit Train-Daten, Ist-Daten und Prognose**")
        st.write(
            "Links vom roten Strich liegen die Train-Daten. Rechts davon liegen Test-Ist-Werte, dynamischer VAR-Forecast, "
            "rollierender 1-Step-Forecast und der naive Vergleichsforecast."
        )

        with st.expander("Kurz erklärt: Forecast-Chart"):
            st.markdown(
                """
                - **Train Ist**: Daten, auf denen das Modell geschätzt wurde.
                - **Roter Strich**: Start des Test-/Forecast-Zeitraums.
                - **Test Ist**: echte Werte im zurückgehaltenen Testzeitraum.
                - **VAR Forecast dynamisch**: echter Mehrschritt-Forecast nur aus Trainingsdaten.
                - **VAR Forecast rollierend 1-Step**: sagt immer nur den nächsten Punkt voraus und nutzt danach den echten neuen Ist-Wert.
                - **Naiver Forecast**: Vergleichslinie mit dem letzten bekannten Wert.
                - **Sichtbare Linien**: blendet einzelne Linien im Chart ein oder aus, ohne die Berechnung zu stoppen.
                """
            )

        train_actual = frame.iloc[:-horizon][target]
        actual = test_model_units[target]
        forecast_dynamic = forecast_model[target]
        forecast_rolling = rolling_forecast_model[target]
        naive = naive_model[target]

        inverse_kind = inverse_map.get(target)

        train_actual, y_title = inverse_if_needed(train_actual, inverse_kind)
        actual, _ = inverse_if_needed(actual, inverse_kind)
        forecast_dynamic, _ = inverse_if_needed(forecast_dynamic, inverse_kind)
        forecast_rolling, _ = inverse_if_needed(forecast_rolling, inverse_kind)
        naive, _ = inverse_if_needed(naive, inverse_kind)

        split_at = test_model_units.index[0]

        forecast_table = pd.DataFrame(
            {
                "Test Ist": actual,
                "VAR dynamisch": forecast_dynamic,
                "VAR rollierend 1-Step": forecast_rolling,
                "Naiver Forecast": naive,
                "Fehler VAR dynamisch": forecast_dynamic - actual,
                "Fehler VAR rollierend": forecast_rolling - actual,
                "Fehler naiv": naive - actual,
            }
        )

        forecast_line_options = [
            "Train Ist",
            "Test Ist",
            "VAR Forecast dynamisch",
            "VAR Forecast rollierend 1-Step",
            "Naiver Forecast",
        ]
        visible_forecast_lines = st.multiselect(
            "Sichtbare Linien im Forecast-Graph",
            options=forecast_line_options,
            default=forecast_line_options,
            help="Hier kannst du einzelne Linien schnell ein- oder ausblenden, z. B. nur Test Ist und Naiver Forecast anzeigen.",
            key="visible_forecast_lines",
        )

        if visible_forecast_lines:
            st.altair_chart(
                forecast_chart(
                    train_actual=train_actual,
                    test_actual=actual,
                    forecast_dynamic=forecast_dynamic,
                    forecast_rolling=forecast_rolling,
                    naive=naive,
                    title=f"Forecast-Test: {nice(target)}",
                    split_at=split_at,
                    visible_series=visible_forecast_lines,
                    markers=show_markers,
                    y_title=y_title,
                ),
                width="stretch",
            )
        else:
            st.info(
                "Alle Linien sind ausgeblendet. Wähle oben mindestens eine Linie aus. "
                "Die Berechnung läuft trotzdem weiter und die Werte stehen unten in der Tabelle."
            )

        st.dataframe(forecast_table.round(3), width="stretch")

        st.warning(
            "Interpretation: Der dynamische VAR-Forecast ist näher an echter Zukunftsprognose. "
            "Der rollierende 1-Step-Forecast ist oft besser im Backtest, nutzt aber im Testverlauf bereits neue Ist-Werte."
        )

    with tab_experiments:
        st.markdown("**Live-Experimente**")
        st.write(
            "Ändere links genau eine Sache: Datensatz, Variablen, Zeitraum, Transformation, Lag-Regel, Horizont oder Schockvariable."
        )

        with st.expander("Kurz erklärt: Granger-Hinweis"):
            st.markdown(
                """
                - Prüft, ob Vergangenheitswerte einer Quelle die Prognose eines Ziels verbessern.
                - Hier als einfache SSE-Verbesserung dargestellt.
                - Das ist ein Prognosehinweis, keine echte Kausalitätsaussage.
                """
            )

        top_granger = granger.head(10).copy()
        top_granger["Quelle"] = top_granger["Quelle"].map(nice)
        top_granger["Ziel"] = top_granger["Ziel"].map(nice)

        st.dataframe(top_granger.round(3), width="stretch")

        with st.expander("Kurz erklärt: Impulsantwort / IRF"):
            st.markdown(
                """
                - Simuliert einen einmaligen Schock in einer Variable.
                - Danach sieht man, wie die anderen Variablen im Modell reagieren.
                - Ohne zusätzliche Annahmen ist das nur dynamisch, nicht kausal zu lesen.
                """
            )

        irf_z = impulse_response(model, shock, irf_steps, shock_size)
        irf_units = irf_z * sigma[frame.columns].to_numpy()

        st.altair_chart(
            line_chart(irf_units, f"Impulsantwort auf {nice(shock)}", show_markers, "Modell-Einheiten"),
            width="stretch",
        )

        st.warning(
            "Vorsicht bei der Lesart: VAR zeigt dynamische Prognosebeziehungen. "
            "Granger-Hinweise und IRFs sind ohne zusätzliche Identifikation keine echten Kausalaussagen."
        )


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    else:
        run_app()
