# Vector Autoregression (VAR) – Kursmaterial AI4BP

Ein kompaktes, in sich geschlossenes Lernpaket zu **Vector Autoregression (VAR)**:
eine interaktive Live-Demo, eine Hands-on-Übung zum Selberbauen und die passenden
Datensätze.

## Aufbau

| Ordner | Inhalt | Einstieg |
|---|---|---|
| `dashboard/` | Interaktive **Streamlit-Live-Demo** (FRED-Makro & Beijing-Luftqualität). | [`dashboard/README.md`](dashboard/README.md) |
| `kurs_uebung/` | **Übungs- und Lösungs-Notebook**: ein VAR mit reinem `numpy`/`pandas` Schritt für Schritt nachbauen. | [`kurs_uebung/README.md`](kurs_uebung/README.md) |
| `data/` | Aufbereitete CSV-Daten plus die Skripte, mit denen sie erzeugt wurden. | – |
| `info/` | Fachliche Begleitlektüre: ausführliche Wissensbasis und Kurzfassung. | [`info/VAR_ZUSAMMENFASSUNG.md`](info/VAR_ZUSAMMENFASSUNG.md) |

## Schnellstart

- **Live-Demo ansehen** → in den Ordner `dashboard/` und der dortigen Anleitung
  folgen (`uv run streamlit run app.py`).
- **Selbst üben** → in den Ordner `kurs_uebung/`, Umgebung einrichten und
  `VAR_Uebung.ipynb` öffnen. Die Musterlösung liegt daneben.

## Daten

Beide Datensätze liegen fertig in `data/`. Sie lassen sich mit `data/get_data.py`
(FRED-Makrodaten) und `data/get_data_2.py` (Beijing-Luftqualität) neu erzeugen –
beide Skripte schreiben ihre CSV direkt in den `data/`-Ordner.

> Hinweis zur Lesart: VAR zeigt dynamische Prognosebeziehungen. Granger-Hinweise
> und Impulsantworten sind ohne zusätzliche Identifikation **keine** echten
> Kausalaussagen. Mehr dazu in `info/`.
