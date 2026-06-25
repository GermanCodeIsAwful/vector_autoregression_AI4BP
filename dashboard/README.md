# VAR Live-Demo Dashboard

Interaktives Streamlit-Dashboard zur Vector Autoregression (FRED-Makrodaten und
Beijing-Luftqualität). Reproduzierbar über **uv** (lokal) und **Docker**.

## Was ist drin?

| Datei | Zweck |
|---|---|
| `app.py` | Das Streamlit-Dashboard (inkl. `--self-check`). |
| `pyproject.toml` | Abhängigkeiten (streamlit, altair, numpy, pandas). |
| `uv.lock` | Exakt gepinnte Versionen für reproduzierbare Umgebungen. |
| `Dockerfile` | Container-Image auf Basis von uv. |

Die Daten liegen bewusst eine Ebene höher in `../data/`. `app.py` findet sie über
einen relativen Pfad automatisch – sowohl lokal als auch im Container.

---

## Variante A: Lokal mit uv (empfohlen)

[uv](https://docs.astral.sh/uv/) ist ein schneller Python-Paket- und
Umgebungsmanager. Installation (einmalig):

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Dashboard starten (im Ordner `dashboard/`):

```bash
cd dashboard
uv sync --frozen          # installiert exakt die Versionen aus uv.lock
uv run streamlit run app.py
```

Browser öffnet sich auf <http://localhost:8501>.

Schneller Funktionstest ohne UI:

```bash
uv run python app.py --self-check    # erwartet: "Self-check: ok"
```

> **Hinter Firmen-Proxy mit eigener CA?** Falls uv beim Download
> `invalid peer certificate` meldet, den System-Zertifikatspeicher nutzen:
> `uv sync --frozen --native-tls` bzw. die CA über `SSL_CERT_FILE` setzen.

---

## Variante B: Mit Docker (maximale Reproduzierbarkeit)

Der **Build-Kontext ist der Projekt-Root** (das Image braucht `../data`), das
`Dockerfile` liegt aber hier im Dashboard-Bereich.

```bash
# aus dem Projekt-Root ausführen:
docker build -f dashboard/Dockerfile -t var-dashboard .
docker run --rm -p 8501:8501 var-dashboard
```

Dann <http://localhost:8501> öffnen. Beenden mit `Ctrl+C`.

Optional per `docker compose` (Datei `compose.yaml` im Projekt-Root anlegen):

```yaml
services:
  dashboard:
    build:
      context: .
      dockerfile: dashboard/Dockerfile
    ports:
      - "8501:8501"
```

```bash
docker compose up --build
```

> **Proxy/CA im Docker-Build:** Falls der Paket-Download im Container an der
> TLS-Inspektion scheitert, die Firmen-CA ins Image bringen (z. B. CA-Datei
> kopieren und `uv sync` mit `--native-tls` laufen lassen) oder einen internen
> PyPI-Mirror über `UV_INDEX_URL` setzen.

---

## Abhängigkeiten aktualisieren

```bash
cd dashboard
uv lock --upgrade     # neue Versionen auflösen und uv.lock aktualisieren
uv sync --frozen      # Umgebung an das neue Lockfile angleichen
```

