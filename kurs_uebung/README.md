# Kurs-Übung: VAR von Grund auf

Zwei Jupyter-Notebooks rund um **Vector Autoregression (VAR)**, aufgebaut auf dem
praktischen Beispiel aus dem `dashboard/` (FRED-Makrodaten). Die Teilnehmenden
bauen ein VAR mit reinem `numpy`/`pandas` Schritt für Schritt selbst nach.

## Schnellstart: Umgebung & Notebook starten

Du brauchst Python 3 mit `numpy`, `pandas`, `matplotlib` und JupyterLab. Wähle
**einen** der beiden Wege (im Ordner `kurs_uebung/`):

### Mit pip + venv

```bash
# Windows (PowerShell)
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
jupyter lab
```

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
jupyter lab
```

### Mit uv (schneller, keine manuelle venv nötig)

```bash
# Variante 1: aus requirements.txt eine Umgebung bauen
uv venv
uv pip install -r requirements.txt
uv run jupyter lab

# Variante 2: ganz ohne Setup-Datei, Pakete ad hoc dazuladen
uv run --with jupyterlab --with numpy --with pandas --with matplotlib jupyter lab
```

> 💡 uv installieren: `irm https://astral.sh/uv/install.ps1 | iex` (Windows) bzw.
> `curl -LsSf https://astral.sh/uv/install.sh | sh` (macOS/Linux).
> Hinter Firmen-Proxy mit eigener CA hilft bei uv das Flag `--native-tls`.

Nach dem Start öffnet JupyterLab im Browser – dort `VAR_Uebung.ipynb` öffnen und
die Zellen von oben nach unten ausführen.

## Dateien

| Datei | Zweck |
|---|---|
| `VAR_Uebung.ipynb` | **Übung** mit Boilerplate-Code und `# TODO`-Stellen (ca. 20 Min). Pro Aufgabe eine Self-Check-Zelle. |
| `VAR_Uebung_Loesung.ipynb` | **Musterlösung** mit vollständigem Code, Erklärungen, Impulsantwort und Einordnung. Im Anschluss austeilen. |
| `requirements.txt` | Pakete für die Notebooks (für pip und uv). |
| `_build_notebooks.py` | Generator-Skript (einzige Quelle der Wahrheit – hält Übung und Lösung synchron). |

## Ablauf im Kurs

1. `VAR_Uebung.ipynb` austeilen, Zellen der Reihe nach ausführen.
2. Die fünf Kern-TODOs lösen: Lag-Matrix, OLS-Schätzung, AIC/BIC, Mehrschritt-Forecast,
   RMSE-Vergleich gegen eine naive Benchmark. Bonus: Stabilität (Companion-Wurzeln).
3. Self-Checks geben sofort Rückmeldung (`OK` = korrekt).
4. Im Anschluss `VAR_Uebung_Loesung.ipynb` bereitstellen.

## Voraussetzungen

- Umgebung gemäß **Schnellstart** oben (pip oder uv) mit `numpy`, `pandas`,
  `matplotlib`, `jupyterlab`.
- Der Ordner `../data/` mit `var_fred_macro.csv` (Datenpfad wird automatisch gefunden).

## Notebooks neu erzeugen

```bash
python kurs_uebung/_build_notebooks.py
```

