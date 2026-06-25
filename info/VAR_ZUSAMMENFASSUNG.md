# VAR_ZUSAMMENFASSUNG.md

## Kurzfassung

Vector Autoregression (VAR) ist ein multivariates Zeitreihenmodell. Es erklärt
mehrere Variablen gleichzeitig durch ihre eigenen vergangenen Werte und durch
die vergangenen Werte der anderen Variablen im System.

Die Grundidee:

```text
y_t = c + A_1 y_(t-1) + ... + A_p y_(t-p) + u_t
```

Dabei ist `y_t` ein Vektor mehrerer Zeitreihen, `p` die Anzahl der Lags,
`A_1 ... A_p` sind Koeffizientenmatrizen und `u_t` enthält die nicht erklärten
Schocks bzw. Innovationen.

## Wofür VAR nützlich ist

VAR eignet sich, wenn mehrere Zeitreihen dynamisch zusammenhängen und keine
Variable eindeutig nur Ursache oder nur Wirkung ist.

Typische Anwendungen:

- gemeinsame Prognose mehrerer Variablen
- Untersuchung verzögerter Zusammenhänge
- Prüfung von Granger-Kausalität
- Impulsantworten nach Schocks
- Analyse der Prognosefehler-Varianz

## Aufbau eines VAR

Ein VAR besteht aus:

- endogenen Variablen, die gemeinsam modelliert werden
- einer Lag-Ordnung `p`
- optionalen deterministischen Termen wie Intercept, Trend oder saisonalen
  Dummies
- optionalen exogenen Variablen
- einem Fehlervektor mit möglichen zeitgleichen Korrelationen

Je mehr Variablen und je mehr Lags genutzt werden, desto schneller wächst die
Parameterzahl. Das wichtigste Risiko ist deshalb Overfitting.

## Wichtige Varianten

- **Reduced-Form VAR**: Standardmodell für dynamische Zusammenhänge und
  Prognosen, aber ohne automatische Kausalaussage.
- **SVAR**: strukturelles VAR mit zusätzlichen Identifikationsannahmen für
  kausaler interpretierbare Schocks.
- **VECM**: geeignet, wenn nicht stationäre Variablen kointegriert sind.
- **BVAR**: Bayesian VAR mit Shrinkage, hilfreich bei vielen Variablen oder
  wenig Daten.
- **VARX**: VAR mit exogenen Variablen.

## Interpretation

VAR-Koeffizienten zeigen, wie vergangene Werte einer Variable mit aktuellen
Werten anderer Variablen zusammenhängen, unter Kontrolle der übrigen Lags.
Einzelne Koeffizienten sind aber oft schwer zu interpretieren, weil sich
Effekte über mehrere Perioden verteilen.

Hilfreichere Werkzeuge sind meist:

- **Granger-Kausalität**: zeigt zusätzliche Prognoseinformation, keine echte
  Kausalität.
- **Impulsantwortfunktionen (IRF)**: zeigen, wie das System auf einen Schock
  reagiert.
- **Forecast Error Variance Decomposition (FEVD)**: zeigt, welche Schocks zur
  Prognoseunsicherheit beitragen.
- **Prognosen**: müssen gegen einfache Benchmarks geprüft werden.

## Parameterwahl

Gute Parameter hängen von Daten, Frequenz und Fragestellung ab.

Wichtige Entscheidungen:

- Welche Variablen gehören wirklich ins System?
- Wie viele Lags sind fachlich und statistisch sinnvoll?
- Werden Levels, Differenzen oder Log-Differenzen genutzt?
- Braucht das Modell Intercept, Trend, Saison- oder Ereignisdummies?
- Sind exogene Variablen für Prognosen auch in der Zukunft bekannt?
- Reicht die Datenmenge für die gewählte Parameterzahl?

Lag-Auswahl sollte nicht nur automatisch passieren. Informationskriterien wie
AIC, BIC, HQIC oder FPE helfen, aber Residualdiagnostik, Stabilität und
fachliche Plausibilität sind genauso wichtig.

## Worauf man achten muss

Vor der Schätzung:

- Zeitreihe korrekt sortieren
- Missing Values und Ausreißer prüfen
- Stationarität prüfen
- Kointegration prüfen, falls Variablen nicht stationär sind
- maximale Lag-Zahl fachlich begrenzen

Nach der Schätzung:

- Residuen auf Autokorrelation prüfen
- Stabilität prüfen
- Prognoseleistung gegen Benchmarks testen
- IRFs nur mit Unsicherheit interpretieren
- Cholesky-Reihenfolge bei orthogonalisierten IRFs begründen
- Robustheitschecks mit alternativen Spezifikationen durchführen

## Zentrale Limitierungen

VAR zeigt dynamische Zusammenhänge, aber nicht automatisch Kausalität.

Hauptgrenzen:

- lineare Modellstruktur
- hohe Parameterzahl bei vielen Variablen
- empfindlich gegenüber Lag-Wahl und Transformationen
- problematisch bei Nichtstationarität
- anfällig für Strukturbrüche
- IRFs und FEVD können von Identifikationsannahmen abhängen
- Prognosen extrapolieren nur aus historischer Dynamik

## Merksatz

Ein gutes VAR ist klein genug, um stabil zu sein, groß genug, um die relevante
Dynamik abzubilden, und ehrlich genug, um keine Kausalität zu behaupten, die
das Modell nicht identifizieren kann.
