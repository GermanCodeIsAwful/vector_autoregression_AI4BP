# VAR_INFO.md - Vector Autoregression als Wissensbasis

Dieses Dokument sammelt die fachlichen Grundlagen, Interpretationen,
Modellierungsentscheidungen, Parameterhinweise und Grenzen rund um Vector
Autoregression (VAR). Es ist bewusst als lebendes Nachschlagewerk gedacht:
Neue Erkenntnisse, konkrete Projektergebnisse, Modellentscheidungen,
Interpretationen und Limitierungen können direkt in den vorgesehenen Bereichen
ergänzt werden.

Hinweis zur Begrifflichkeit: In der Statistik und Zeitreihenanalyse heißt die
Methode **Vector Autoregression**. Falls im Projekt oder in Notizen
"Vector Autoreflexion" auftaucht, ist damit sehr wahrscheinlich
**Vector Autoregression (VAR)** gemeint.

---

## 1. Kurzdefinition

Ein **Vector Autoregression Model (VAR)** ist ein multivariates
Zeitreihenmodell, in dem mehrere Variablen gemeinsam über ihre eigenen
Vergangenheitswerte und die Vergangenheitswerte der anderen Variablen erklärt
werden.

Statt eine einzelne Zeitreihe isoliert zu modellieren, betrachtet VAR ein
System aus mehreren Zeitreihen. Jede Variable darf von allen Variablen im
System abhängen, jeweils mit Verzögerungen, den sogenannten **Lags**.

Beispielhafte Fragestellung:

- Wie hängen Umsatz, Marketingausgaben und Website-Traffic über die Zeit
  zusammen?
- Reagiert Variable A verzögert auf Veränderungen in Variable B?
- Verbessern vergangene Werte einer Variable die Prognose einer anderen
  Variable?
- Wie breitet sich ein einmaliger Schock in einer Variable über das System aus?

VAR ist besonders nützlich, wenn keine einzelne Variable eindeutig nur
"Ursache" oder nur "Wirkung" ist, sondern mehrere Größen dynamisch miteinander
interagieren.

---

## 2. Intuition

Bei einem einfachen autoregressiven Modell, etwa AR(p), wird eine einzelne
Zeitreihe durch ihre eigenen vergangenen Werte erklärt:

```text
y_t = c + phi_1 * y_(t-1) + ... + phi_p * y_(t-p) + u_t
```

Ein VAR erweitert diese Idee auf mehrere Zeitreihen gleichzeitig. Jede
Variable bekommt ihre eigene Gleichung. In jeder Gleichung stehen als
Erklärungsgrößen die vergangenen Werte aller Variablen.

Für zwei Variablen, zum Beispiel `x` und `y`, kann ein VAR(1) so aussehen:

```text
x_t = c_x + a_11 * x_(t-1) + a_12 * y_(t-1) + u_x,t
y_t = c_y + a_21 * x_(t-1) + a_22 * y_(t-1) + u_y,t
```

Die zentrale Idee:

- `x_t` hängt von der Vergangenheit von `x` und `y` ab.
- `y_t` hängt ebenfalls von der Vergangenheit von `x` und `y` ab.
- Die Variablen werden nicht einzeln, sondern als dynamisches System
  modelliert.

Das Modell ist "autoregressiv", weil Vergangenheitswerte genutzt werden. Es ist
"vector", weil nicht eine einzelne Variable, sondern ein Vektor mehrerer
Variablen modelliert wird.

---

## 3. Mathematische Grundform

Ein VAR-Modell der Ordnung `p`, kurz VAR(p), wird meist so geschrieben:

```text
y_t = c + A_1 y_(t-1) + A_2 y_(t-2) + ... + A_p y_(t-p) + u_t
```

Dabei gilt:

- `y_t` ist ein Vektor mit `K` Variablen zum Zeitpunkt `t`.
- `c` ist ein Vektor von Konstanten oder Intercepts.
- `A_1` bis `A_p` sind Koeffizientenmatrizen.
- `p` ist die Lag-Ordnung, also die Anzahl vergangener Perioden.
- `u_t` ist der Fehler- bzw. Innovationsvektor.
- `K` ist die Anzahl der endogenen Variablen im System.

Wenn `K = 3` und `p = 2`, dann enthält das Modell drei Gleichungen. Jede
Gleichung nutzt zwei Lags aller drei Variablen. Pro Gleichung entstehen also
mindestens `K * p = 6` Lag-Koeffizienten, zusätzlich zu Intercept,
Trend, saisonalen Dummies oder exogenen Variablen, falls diese genutzt werden.

Die Fehlerterme `u_t` können zeitgleich miteinander korreliert sein. Das ist
einer der Gründe, warum Impulsantworten und strukturelle Interpretationen bei
VAR besondere Vorsicht brauchen.

---

## 4. Was wird in einem VAR als endogen betrachtet?

In einem Standard-VAR sind alle Variablen im Vektor `y_t` **endogen**. Das
bedeutet: Sie werden innerhalb des Modells gemeinsam erklärt. Keine dieser
Variablen wird als rein externe Ursache gesetzt.

Beispiel:

```text
y_t = [sales_t, traffic_t, ad_spend_t]'
```

Dann modelliert das VAR-System:

- `sales_t` aus vergangenen Werten von `sales`, `traffic`, `ad_spend`
- `traffic_t` aus vergangenen Werten von `sales`, `traffic`, `ad_spend`
- `ad_spend_t` aus vergangenen Werten von `sales`, `traffic`, `ad_spend`

Das ist stark, aber auch anspruchsvoll: Wenn eine Variable in Wahrheit extern
gesteuert wird, etwa ein fest geplanter Kampagnenbudgetplan, kann ein
Standard-VAR die Datenlogik verzerren. In solchen Fällen kann ein VAR mit
exogenen Variablen, oft VARX genannt, sinnvoller sein.

---

## 5. Typische Varianten

### 5.1 Reduced-Form VAR

Das klassische VAR ist ein **Reduced-Form VAR**. Es beschreibt dynamische
Zusammenhänge, ohne sofort eine kausale Struktur zu behaupten.

Typische Nutzung:

- Prognosen
- dynamische Abhängigkeiten
- Granger-Kausalität
- Impulsantworten mit vorsichtiger Interpretation
- Forecast Error Variance Decomposition

Wichtig: Reduced-form Koeffizienten sind nicht automatisch kausal.

### 5.2 Structural VAR (SVAR)

Ein **Structural VAR** ergänzt das Modell um Identifikationsannahmen. Ziel ist,
aus den beobachteten Innovationskorrelationen strukturelle Schocks abzuleiten.

Typische Identifikationsarten:

- rekursive Identifikation, oft über Cholesky-Zerlegung
- kurzfristige Restriktionen
- langfristige Restriktionen
- Vorzeichenrestriktionen
- externe Instrumente oder Proxy-SVAR

SVAR ist interpretativ stärker, aber nur so glaubwürdig wie die zugrunde
liegenden Identifikationsannahmen.

### 5.3 VECM bei Kointegration

Wenn mehrere Variablen nicht stationär sind, aber eine langfristige
Gleichgewichtsbeziehung besitzen, kann ein **Vector Error Correction Model
(VECM)** angemessener sein.

Typischer Fall:

- Variablen sind integriert der Ordnung 1, also I(1).
- Linearkombinationen dieser Variablen sind stationär.
- Es gibt eine langfristige Beziehung, zu der das System zurückkehrt.

Ein reines VAR in Differenzen verliert diese langfristige Information. Ein VAR
in Levels kann bei nicht stationären Daten problematisch sein. VECM ist dann
der natürliche Kandidat.

### 5.4 Bayesian VAR (BVAR)

Ein **Bayesian VAR** nutzt Priors bzw. Shrinkage, um die vielen Parameter eines
VAR stabiler zu schätzen. Das ist besonders nützlich bei:

- vielen Variablen
- vielen Lags
- relativ kurzen Zeitreihen
- stark korrelierten Prädiktoren
- Prognosefokus

BVAR reduziert Overfitting, verlangt aber Entscheidungen über Priors.

### 5.5 VARX

Ein **VARX** enthält zusätzlich exogene Variablen:

```text
y_t = c + A_1 y_(t-1) + ... + A_p y_(t-p) + B x_t + u_t
```

`x_t` sind externe Variablen, die nicht innerhalb des VAR-Systems modelliert
werden.

Beispiele:

- Feiertagsdummies
- externe Preise
- Wettervariablen
- regulatorische Ereignisse
- geplante Kampagnen
- makroökonomische Szenarioannahmen

VARX ist sinnvoll, wenn bestimmte Größen das System beeinflussen, aber selbst
nicht sinnvoll als endogene Systemvariablen behandelt werden sollen.

---

## 6. Datenstruktur und Voraussetzungen

Ein VAR braucht Zeitreihendaten in regelmäßiger Frequenz.

Typische Anforderungen:

- eine eindeutige Zeitachse
- gleiche Frequenz für alle Variablen
- keine ungeklärten Lücken
- ausreichend viele Beobachtungen
- sinnvolle Transformationen
- stationäre oder passend modellierte Variablen
- keine massiven unbehandelten Ausreißer
- keine extrem starke Multikollinearität ohne fachliche Begründung

Die Datenmatrix sieht typischerweise so aus:

| Zeitpunkt | Variable 1 | Variable 2 | Variable 3 |
|---|---:|---:|---:|
| t1 | ... | ... | ... |
| t2 | ... | ... | ... |
| t3 | ... | ... | ... |

Jede Zeile ist ein Zeitpunkt. Jede Spalte ist eine Variable.

### 6.1 Frequenz

Die Frequenz bestimmt, was ein Lag bedeutet:

- Tagesdaten: Lag 1 = ein Tag
- Wochendaten: Lag 1 = eine Woche
- Monatsdaten: Lag 1 = ein Monat
- Quartalsdaten: Lag 1 = ein Quartal

Die Wahl der Frequenz beeinflusst die Interpretation stark. Ein VAR(4) auf
Wochendaten beschreibt vier Wochen Verzögerung, ein VAR(4) auf Quartalsdaten
ein ganzes Jahr.

### 6.2 Fehlende Werte

Fehlende Werte sind in VAR-Modellen besonders problematisch, weil Lags
gebildet werden. Eine einzelne Lücke kann mehrere Trainingszeilen unbrauchbar
machen.

Mögliche Strategien:

- Zeitreihe kürzen
- fachlich begründete Imputation
- Aggregation auf gröbere Frequenz
- Variablen mit vielen Lücken ausschließen
- separate Missing-Indikatoren nur mit Vorsicht verwenden

Wichtig ist, dass fehlende Werte nicht unbemerkt mit Standardwerten wie `0`
ersetzt werden, wenn `0` fachlich nicht bedeutet, dass nichts passiert ist.

### 6.3 Ausreißer

Ausreißer können Koeffizienten, Residuen, Stabilitätstests und Impulsantworten
stark beeinflussen.

Typische Behandlung:

- prüfen, ob es Messfehler oder echte Ereignisse sind
- Ereignisdummies verwenden
- robuste Transformationen prüfen
- Winsorisierung nur mit Begründung
- Sensitivitätsanalyse mit und ohne Ausreißer durchführen

Bei echten Ereignissen sollte man dokumentieren, ob sie Teil der
Modellrealität sind oder als Sonderfall modelliert werden.

---

## 7. Stationarität

Viele klassische VAR-Auswertungen setzen stationäre Zeitreihen voraus.
Stationarität bedeutet grob, dass zentrale Eigenschaften der Zeitreihe über die
Zeit stabil bleiben:

- Erwartungswert
- Varianz
- Autokovarianzstruktur

Nicht stationäre Zeitreihen können zu Scheinkorrelationen und instabilen
Interpretationen führen.

### 7.1 Typische Anzeichen für Nichtstationarität

- klarer Trend
- wachsende oder schrumpfende Varianz
- saisonale Muster ohne Modellierung
- strukturelle Brüche
- sehr langsames Zurückkehren nach Schocks
- hohe Persistenz

### 7.2 Typische Tests

Häufig verwendete Tests:

- Augmented Dickey-Fuller Test (ADF)
- KPSS-Test
- Phillips-Perron-Test

Diese Tests liefern Hinweise, aber keine absolute Wahrheit. Sie sollten immer
zusammen mit Plots, Fachwissen und Modellzweck interpretiert werden.

### 7.3 Transformationen

Mögliche Transformationen:

- Logarithmen bei positiven, wachstumsartigen Größen
- erste Differenzen
- log-Differenzen als approximative Wachstumsraten
- saisonale Differenzen
- Standardisierung für Vergleichbarkeit
- Detrending
- Deflation nominaler Größen

Beispiel:

```text
log_diff_y_t = log(y_t) - log(y_(t-1))
```

Diese Transformation entspricht näherungsweise einer prozentualen
Veränderungsrate.

### 7.4 Levels oder Differenzen?

Diese Entscheidung ist zentral.

VAR in Levels:

- erhält langfristige Beziehungen
- ist manchmal für Prognosen brauchbar, auch bei hoher Persistenz
- kann bei Nichtstationarität problematische Inferenz erzeugen

VAR in Differenzen:

- verbessert oft Stationarität
- reduziert Scheinkorrelationen
- verliert langfristige Niveauinformationen
- verändert die Interpretation zu Veränderungen statt Niveaus

VECM:

- sinnvoll bei kointegrierten nicht stationären Variablen
- erhält langfristige Gleichgewichtsbeziehungen
- modelliert kurzfristige Dynamik und langfristige Anpassung gemeinsam

Dokumentiere immer, warum Levels, Differenzen oder VECM gewählt wurden.

---

## 8. Aufbau eines VAR-Modells

Ein VAR besteht aus mehreren Bausteinen.

### 8.1 Endogene Variablen

Das sind die Variablen, die gemeinsam modelliert werden.

Leitfragen:

- Gehört diese Variable wirklich in das dynamische System?
- Gibt es eine plausible Rückkopplung mit anderen Variablen?
- Ist die Variable zeitlich vor oder nach den anderen Größen beobachtbar?
- Ist sie steuerbar, beobachtbar oder nur abgeleitet?
- Ist sie zu stark mit einer anderen Variable redundant?

### 8.2 Lag-Ordnung `p`

Die Lag-Ordnung bestimmt, wie viele vergangene Perioden in das Modell eingehen.

Ein VAR(1) nutzt:

```text
y_(t-1)
```

Ein VAR(3) nutzt:

```text
y_(t-1), y_(t-2), y_(t-3)
```

Je höher `p`, desto flexibler ist das Modell. Gleichzeitig steigen
Parameterzahl und Overfitting-Risiko stark.

### 8.3 Deterministische Terme

Mögliche deterministische Bestandteile:

- Intercept
- linearer Trend
- quadratischer Trend
- saisonale Dummies
- Feiertagsdummies
- Ereignisdummies
- Strukturbruch-Dummies

Nicht jeder deterministische Term ist sinnvoll. Ein Trend sollte fachlich und
visuell begründet sein.

### 8.4 Exogene Variablen

Exogene Variablen können aufgenommen werden, wenn sie das System beeinflussen,
aber nicht selbst durch das System erklärt werden sollen.

Beispiele:

- Kalenderinformationen
- bekannte externe Preise
- politische Ereignisse
- Wetter
- Feiertage
- Sonderaktionen

Achtung: Exogene Variablen müssen für Prognosen in die Zukunft bekannt oder
als Szenario verfügbar sein.

### 8.5 Fehlerstruktur

Der Fehlervektor `u_t` enthält die unerklärten Innovationen aller Gleichungen.
Die Fehler können contemporaneous, also zum selben Zeitpunkt, korreliert sein.

Das ist wichtig für:

- Standardfehler
- Impulsantworten
- strukturelle Interpretation
- Cholesky-Ordnungen
- Forecast-Unsicherheit

---

## 9. Parameterzahl und Datenbedarf

VAR-Modelle können schnell sehr viele Parameter haben.

Pro Gleichung gilt näherungsweise:

```text
Anzahl Parameter pro Gleichung = K * p + d
```

Dabei:

- `K` = Anzahl endogener Variablen
- `p` = Lag-Ordnung
- `d` = Anzahl deterministischer oder exogener Terme pro Gleichung

Für das gesamte System:

```text
Lag-Koeffizienten insgesamt = K * K * p
```

Beispiel:

- `K = 5` Variablen
- `p = 4` Lags
- ohne Zusatzterme

Dann:

```text
Lag-Koeffizienten insgesamt = 5 * 5 * 4 = 100
```

Zusätzlich kommen Intercepts, Trends, exogene Terme und die
Kovarianzmatrix der Residuen hinzu.

Faustregel: Je mehr Variablen und Lags, desto mehr Beobachtungen werden
benötigt. Ein großes VAR mit kurzer Zeitreihe wirkt oft beeindruckend, ist aber
häufig instabil und schlecht generalisierbar.

---

## 10. Schätzung

Ein Reduced-Form VAR kann meist Gleichung für Gleichung per Ordinary Least
Squares (OLS) geschätzt werden, weil jede Gleichung dieselben Regressoren
enthält.

Praktische Konsequenz:

- Die Schätzung ist konzeptionell relativ einfach.
- Die Herausforderung liegt weniger in der Rechentechnik als in Spezifikation,
  Diagnostik und Interpretation.

Nach der Schätzung erhält man:

- Koeffizientenmatrizen
- Residuen
- Residualkovarianzmatrix
- angepasste Werte
- Prognosen
- diagnostische Teststatistiken
- Grundlage für Impulsantworten und Varianzzerlegung

---

## 11. Stabilität

Ein VAR sollte stabil sein, wenn klassische Impulsantworten,
Varianzzerlegungen und langfristige Interpretationen genutzt werden.

Technisch wird ein VAR häufig über die Eigenwerte der Companion-Matrix geprüft.
Ein stabiles VAR verlangt, dass die relevanten Wurzeln innerhalb des
Einheitskreises liegen.

Praktische Interpretation:

- Schocks klingen mit der Zeit ab.
- Das System explodiert nicht.
- Langfristige Simulationen sind sinnvoller.

Warnzeichen:

- Impulsantworten wachsen unbegrenzt.
- Prognosen laufen unrealistisch weg.
- kleine Spezifikationsänderungen ändern die Ergebnisse drastisch.
- Stabilitätstest wird nicht bestanden.

Bei Instabilität prüfen:

- Transformationen
- Differenzen statt Levels
- Kointegration und VECM
- weniger Lags
- andere Variablenauswahl
- Strukturbrüche
- Ausreißer
- saisonale oder deterministische Terme

---

## 12. Modellierungsworkflow

Ein robuster VAR-Workflow kann so aussehen:

1. Fachliche Fragestellung definieren.
2. Endogene und exogene Variablen festlegen.
3. Zeitfrequenz und Beobachtungszeitraum bestimmen.
4. Datenqualität prüfen.
5. Plots und deskriptive Statistiken erstellen.
6. Transformationen entscheiden.
7. Stationarität und mögliche Kointegration prüfen.
8. Maximale Lag-Zahl fachlich begrenzen.
9. Lag-Ordnung mit Informationskriterien und Diagnostik wählen.
10. Modell schätzen.
11. Residuen prüfen.
12. Stabilität prüfen.
13. Granger-Kausalität, Impulsantworten und Varianzzerlegung auswerten.
14. Prognoseleistung prüfen.
15. Robustheitschecks durchführen.
16. Ergebnisse fachlich interpretieren.
17. Limitationen dokumentieren.

---

## 13. Lag-Auswahl

Die Wahl der Lag-Ordnung ist eine der wichtigsten Entscheidungen.

### 13.1 Informationskriterien

Häufige Kriterien:

- AIC: Akaike Information Criterion
- BIC bzw. Schwarz Criterion
- HQIC: Hannan-Quinn Information Criterion
- FPE: Final Prediction Error

Typische Tendenz:

- AIC wählt oft mehr Lags.
- BIC wählt oft sparsamere Modelle.
- HQIC liegt häufig dazwischen.

Kein Kriterium ist immer "richtig". Die Auswahl muss zum Ziel passen.

### 13.2 Fachliche Plausibilität

Die Lag-Ordnung sollte zur Datenfrequenz und zum Prozess passen.

Beispiele:

- Bei Monatsdaten können 12 Lags saisonale Jahresmuster erfassen.
- Bei Quartalsdaten können 4 Lags ein Jahr abdecken.
- Bei Tagesdaten kann eine hohe Lag-Zahl schnell sehr viele Parameter erzeugen.

Die maximale Lag-Zahl sollte nicht nur algorithmisch, sondern fachlich begrenzt
werden.

### 13.3 Residualdiagnostik

Nach der Lag-Auswahl müssen die Residuen geprüft werden. Wenn Residuen noch
Autokorrelation zeigen, fehlen möglicherweise Lags oder wichtige Variablen.

Ein Modell mit bestem Informationskriterium ist nicht automatisch gut, wenn die
Residuenstruktur schlecht ist.

### 13.4 Prognoseziel vs. Interpretation

Für Prognosen kann ein anderes Modell optimal sein als für Interpretation.

- Prognosefokus: Out-of-sample Performance, Cross-Validation, Rolling Forecasts
- Interpretationsfokus: Stabilität, Sparsamkeit, robuste Dynamik,
  nachvollziehbare Spezifikation

---

## 14. Wie wählt man gute Parameter?

Dieser Abschnitt ist als praktischer Leitfaden für konkrete
Modellentscheidungen gedacht.

### 14.1 Anzahl der Variablen `K`

Gute Wahl:

- Variablen sind fachlich relevant.
- Es gibt plausible dynamische Wechselwirkungen.
- Jede Variable fügt neue Information hinzu.
- Die Datenhistorie reicht für die Parameterzahl.

Vorsicht:

- zu viele stark korrelierte Variablen
- Variablen ohne klare Rolle
- mehrere Varianten derselben Messgröße
- Variablen, die erst nach dem Prognosezeitpunkt bekannt sind

Pragmatische Regel:

> Lieber ein kleines, gut begründetes VAR als ein großes System, das jede
> verfügbare Spalte aufnimmt.

### 14.2 Lag-Ordnung `p`

Gute Wahl:

- Informationskriterien unterstützen sie.
- Residuen zeigen keine starke Autokorrelation.
- Modell bleibt stabil.
- Koeffizienten und Impulsantworten sind nicht extrem fragil.
- Datenmenge reicht aus.

Anpassen, wenn:

- Residuen autokorreliert sind: mehr Lags prüfen.
- Modell instabil wird: weniger Lags oder Transformationen prüfen.
- Prognose schlecht ist: alternative Lags per Out-of-sample Test vergleichen.
- Parameterzahl zu hoch ist: Lags reduzieren oder BVAR/Shrinkage prüfen.

### 14.3 Deterministische Terme

Intercept:

- meist sinnvoll, wenn Variablen nicht um null zentriert sind.

Trend:

- nur aufnehmen, wenn ein deterministischer Trend fachlich plausibel ist.
- bei stochastischen Trends eher Differenzen oder VECM prüfen.

Saisonale Dummies:

- sinnvoll bei stabiler Saisonalität.
- besonders wichtig, wenn die Frequenz saisonale Muster enthält.

Ereignisdummies:

- sinnvoll bei bekannten Sonderereignissen.
- sollten nicht wahllos Ausreißer "wegmodellieren".

### 14.4 Transformationen

Gute Transformationen machen die Daten modellierbarer, ohne die Fragestellung
zu zerstören.

Typische Entscheidungen:

- Levels für Niveauinterpretation
- Differenzen für Veränderungsinterpretation
- Logarithmen für relative Veränderungen und Varianzstabilisierung
- log-Differenzen für Wachstumsraten
- Standardisierung, wenn Größenordnungen sehr unterschiedlich sind

Immer dokumentieren:

- Was wurde transformiert?
- Warum?
- Wie verändert sich dadurch die Interpretation?
- Können Ergebnisse in Originaleinheiten zurückübersetzt werden?

### 14.5 Trainingsfenster

Mögliche Varianten:

- komplettes historisches Fenster
- Rolling Window
- Expanding Window
- Zeitraum nach Strukturbruch
- nur aktuelle Regimephase

Gute Wahl hängt davon ab, ob alte Daten noch relevant sind.

Anpassen, wenn:

- Strukturbrüche auftreten.
- Markt, Prozess oder Messsystem sich geändert hat.
- Prognosen in jüngeren Perioden schlechter werden.

### 14.6 Prognosehorizont

VAR-Prognosen werden mit zunehmendem Horizont unsicherer.

Wichtige Fragen:

- Für wie viele Perioden wird prognostiziert?
- Gibt es für diesen Horizont genug Validierungsdaten?
- Werden exogene Variablen in der Zukunft benötigt?
- Wie schnell wachsen Prognoseintervalle?

Ein Modell kann für kurze Horizonte gut und für lange Horizonte ungeeignet
sein.

### 14.7 Regularisierung und Shrinkage

Wenn `K` oder `p` groß ist, kann Regularisierung helfen.

Optionen:

- Bayesian VAR
- Ridge-ähnliche Shrinkage
- Lasso/Elastic Net
- Faktor-Modelle
- kleinere Variablenauswahl

Regularisierung reduziert Varianz und Overfitting, kann aber Bias einführen.

---

## 15. Interpretation der Koeffizienten

VAR-Koeffizienten geben an, wie vergangene Werte einer Variable mit aktuellen
Werten einer anderen Variable zusammenhängen, **gegeben die übrigen Lags im
Modell**.

Beispiel:

```text
y_t = ... + a_12,1 * x_(t-1) + ...
```

Eine einfache Lesart:

> Wenn `x` in der Vorperiode um eine Einheit höher war, ist `y_t` im Modell um
> `a_12,1` Einheiten höher oder niedriger, unter Kontrolle der übrigen
> enthaltenen Lags.

Aber Vorsicht:

- Einzelne Koeffizienten sind oft schwer isoliert interpretierbar.
- Dynamische Effekte verteilen sich über mehrere Lags.
- Multikollinearität zwischen Lags kann Vorzeichen und Signifikanz verzerren.
- Kausalität folgt daraus nicht automatisch.
- Bei transformierten Variablen ändert sich die Einheit der Interpretation.

In der Praxis sind Impulsantworten häufig hilfreicher als einzelne
Koeffizienten, weil sie die dynamische Gesamtreaktion über mehrere Perioden
zeigen.

---

## 16. Granger-Kausalität

Granger-Kausalität prüft, ob vergangene Werte einer Variable helfen, eine andere
Variable vorherzusagen, nachdem deren eigene Vergangenheit und andere Variablen
berücksichtigt wurden.

Vereinfacht:

> `x` Granger-verursacht `y`, wenn Lags von `x` die Prognose von `y` verbessern.

Wichtig:

- Granger-Kausalität ist Prognosekausalität, nicht automatisch echte
  Ursache-Wirkung-Kausalität.
- Eine dritte, ausgelassene Variable kann beide Reihen treiben.
- Ergebnisse hängen von Lag-Ordnung, Transformationen und Stichprobe ab.
- Nichtstationarität kann Tests verzerren.

Gute Formulierung:

> Die vergangenen Werte von `x` enthalten zusätzliche Prognoseinformation für
> `y`.

Riskante Formulierung:

> `x` verursacht `y`.

---

## 17. Impulsantwortfunktionen (Impulse Response Functions, IRF)

Impulsantworten zeigen, wie das System auf einen einmaligen Schock in einer
Variable reagiert.

Typische Frage:

> Was passiert mit allen Variablen über die nächsten Perioden, wenn Variable
> `x` heute einen unerwarteten positiven Schock erhält?

IRFs sind eines der wichtigsten Interpretationswerkzeuge in VAR-Modellen.

### 17.1 Was eine IRF zeigt

Eine IRF zeigt:

- Richtung der Reaktion
- Stärke der Reaktion
- zeitliche Verzögerung
- Dauer des Effekts
- mögliches Zurückkehren zum Ausgangsniveau
- mögliche Überschwinger
- Unsicherheit über Konfidenzbänder

### 17.2 Reduced-Form IRF

Reduced-form Schocks können gleichzeitig korreliert sein. Deshalb ist ein
"Schock in Variable x" nicht automatisch isoliert von allen anderen Schocks.

### 17.3 Orthogonalisierte IRF

Orthogonalisierte IRFs nutzen häufig eine Cholesky-Zerlegung. Dabei spielt die
Reihenfolge der Variablen eine große Rolle.

Interpretation:

- Variablen weiter vorne in der Ordnung können contemporaneous auf spätere
  Variablen wirken.
- Variablen weiter hinten reagieren contemporaneous auf frühere Variablen,
  aber nicht umgekehrt.

Die Reihenfolge muss fachlich begründet werden.

### 17.4 Generalisierte IRF

Generalisierte IRFs sind weniger abhängig von der Variablenordnung, beruhen
aber ebenfalls auf Annahmen über die Fehlerstruktur.

### 17.5 Kumulative IRF

Kumulative IRFs summieren die Reaktion über mehrere Perioden. Sie sind vor
allem bei differenzierten Variablen nützlich, wenn man den Gesamteffekt auf ein
Niveau rekonstruieren möchte.

Vorsicht:

- Kumulative Effekte können Unsicherheit stark akkumulieren.
- Bei instabilen Modellen können sie irreführend sein.

---

## 18. Forecast Error Variance Decomposition (FEVD)

Die Forecast Error Variance Decomposition zeigt, welcher Anteil der
Prognosefehler-Varianz einer Variable durch Schocks in den einzelnen Variablen
des Systems erklärt wird.

Typische Frage:

> Wie viel der Unsicherheit in der Prognose von `y` entsteht durch Schocks in
> `y` selbst, und wie viel durch Schocks in `x`, `z`, usw.?

Interpretation:

- hoher Anteil eigener Schocks: Variable wird vor allem durch eigene
  Innovationen getrieben.
- hoher Anteil anderer Schocks: andere Variablen tragen stark zur
  Prognoseunsicherheit bei.
- Anteile können sich mit dem Prognosehorizont verändern.

Vorsicht:

- FEVD hängt bei orthogonalisierter Zerlegung von der Variablenordnung ab.
- Sie erklärt Unsicherheit, nicht notwendigerweise kausale Bedeutung.
- Sie ist nur sinnvoll, wenn Modell und Identifikation plausibel sind.

---

## 19. Prognosen mit VAR

VAR kann für multivariate Prognosen genutzt werden. Es prognostiziert alle
endogenen Variablen gemeinsam.

Vorteile:

- nutzt gegenseitige Dynamik
- erzeugt konsistente Systemprognosen
- kann mehrere Zielgrößen gleichzeitig prognostizieren
- erlaubt Szenarien mit exogenen Variablen, falls VARX genutzt wird

Grenzen:

- Prognosegüte sinkt oft mit längerem Horizont.
- Strukturbrüche verschlechtern Prognosen.
- Zu viele Parameter führen zu Overfitting.
- Exogene Zukunftswerte müssen bekannt oder geschätzt sein.

Wichtige Validierungsarten:

- Train/Test Split nach Zeit
- Rolling Forecast Evaluation
- Expanding Window Evaluation
- Vergleich gegen naive Benchmarks
- Vergleich gegen univariate Modelle
- Vergleich gegen einfache Durchschnitts- oder Random-Walk-Prognosen

Ein VAR ist nur dann prognostisch überzeugend, wenn es einfache Benchmarks
schlägt oder fachlich klaren Mehrwert liefert.

---

## 20. Residualdiagnostik

Nach der Schätzung sollten Residuen systematisch geprüft werden.

### 20.1 Autokorrelation

Residuen sollten möglichst keine systematische Autokorrelation mehr enthalten.

Wenn doch:

- Lag-Ordnung erhöhen
- fehlende Variablen prüfen
- Saisonkomponenten ergänzen
- Transformationen überdenken

### 20.2 Heteroskedastizität

Wenn die Varianz der Residuen über die Zeit stark schwankt:

- log-Transformation prüfen
- robuste Standardfehler prüfen
- Volatilitätsmodellierung erwägen
- Strukturbrüche prüfen

### 20.3 Normalität

Normalverteilung der Residuen ist für manche Inferenzverfahren hilfreich, aber
in der Praxis nicht immer realistisch.

Bei deutlicher Nichtnormalität:

- Ausreißer prüfen
- Bootstrap-Konfidenzbänder nutzen
- Transformationen prüfen

### 20.4 Strukturbrüche

Wenn sich Beziehungen über die Zeit ändern:

- Modell auf Teilperioden schätzen
- Rolling Window verwenden
- Dummies ergänzen
- Regimewechselmodelle prüfen

---

## 21. Annahmen und Voraussetzungen

Ein klassisches VAR beruht auf mehreren Annahmen:

- lineare Zusammenhänge
- ausreichende Datenmenge
- korrekt gewählte Lag-Struktur
- keine relevanten ausgelassenen Variablen für die betrachtete Fragestellung
- stationäre oder angemessen transformierte Zeitreihen
- stabile Parameter über den betrachteten Zeitraum
- Fehler ohne verbleibende Autokorrelation
- sinnvolle Modellidentifikation bei struktureller Interpretation

Diese Annahmen sind nie automatisch erfüllt. Sie müssen geprüft, begründet und
dokumentiert werden.

---

## 22. Häufige Fehler

### 22.1 Zu viele Variablen

Mehr Variablen bedeuten nicht automatisch ein besseres Modell. Sie erhöhen die
Parameterzahl quadratisch und können das Modell instabil machen.

### 22.2 Zu viele Lags

Viele Lags können vergangene Dynamik besser abbilden, aber auch Overfitting
verursachen. Besonders bei kurzen Zeitreihen ist das kritisch.

### 22.3 Nichtstationarität ignorieren

Nichtstationäre Daten können scheinbar starke Beziehungen erzeugen, die nur auf
gemeinsamen Trends beruhen.

### 22.4 Granger-Kausalität als echte Kausalität lesen

Granger-Kausalität bedeutet Prognoseinformation, nicht zwingend kausale Wirkung.

### 22.5 Cholesky-Reihenfolge nicht begründen

Orthogonalisierte Impulsantworten können stark von der Variablenordnung
abhängen. Ohne fachliche Begründung sind kausale Aussagen schwach.

### 22.6 Exogene Variablen für Prognosen vergessen

Wenn exogene Variablen im Modell enthalten sind, braucht man ihre Zukunftswerte
für Prognosen. Sonst ist das Modell praktisch schwer nutzbar.

### 22.7 Daten-Leakage

Transformationen, Skalierungen oder Feature-Auswahl dürfen nicht auf Basis des
gesamten Datensatzes erfolgen, wenn eine echte Prognoseevaluation geplant ist.

### 22.8 Benchmarks vergessen

Ein komplexes VAR sollte gegen einfache Alternativen geprüft werden. Wenn ein
naiver Forecast gleich gut ist, muss der Mehrwert des VAR begründet werden.

---

## 23. Grenzen und Limitierungen

VAR ist mächtig, aber nicht für jede Fragestellung geeignet.

### 23.1 Korrelation statt Kausalität

Ohne zusätzliche Identifikationsannahmen liefert VAR vor allem dynamische
Korrelationen und Prognosebeziehungen.

### 23.2 Lineare Struktur

Klassisches VAR modelliert lineare Abhängigkeiten. Nichtlineare Effekte,
Schwellen, Sättigung und asymmetrische Reaktionen werden nicht automatisch
abgebildet.

### 23.3 Parameterexplosion

Die Anzahl der Parameter steigt mit `K^2 * p`. Große Systeme brauchen sehr viel
Daten oder Shrinkage.

### 23.4 Empfindlichkeit gegenüber Spezifikation

Ergebnisse können sich ändern durch:

- andere Lag-Zahl
- andere Variablenreihenfolge
- andere Transformationen
- andere Stichprobe
- Aufnahme oder Ausschluss einzelner Variablen
- Behandlung von Ausreißern

### 23.5 Strukturbrüche

Wenn sich die Welt im Beobachtungszeitraum verändert, schätzt VAR einen
Durchschnitt über unterschiedliche Regime.

### 23.6 Schwache Extrapolation

VAR extrapoliert aus historischer Dynamik. Neue Situationen, neue Regeln oder
noch nie beobachtete Schocks können schlecht abgebildet werden.

### 23.7 Interpretationslast

VAR liefert viele Zahlen. Ohne klare Fragestellung kann die Interpretation
beliebig werden.

---

## 24. Worauf man bei der Nutzung achten sollte

Vor dem Modell:

- Sind die Variablen fachlich sinnvoll?
- Ist die Frequenz passend?
- Gibt es genug Beobachtungen?
- Sind die Daten sauber und zeitlich korrekt sortiert?
- Gibt es Lücken, Ausreißer oder Strukturbrüche?
- Sind Transformationen dokumentiert?

Während der Modellierung:

- Lag-Ordnung nicht blind wählen.
- Stationarität und Kointegration prüfen.
- Residuen kontrollieren.
- Stabilität prüfen.
- Modell nicht nur nach einem einzigen Kriterium auswählen.
- Parameterzahl im Blick behalten.

Bei der Interpretation:

- Koeffizienten nicht isoliert überinterpretieren.
- Granger-Kausalität vorsichtig formulieren.
- IRFs mit Konfidenzbändern betrachten.
- Cholesky-Reihenfolge begründen.
- Robustheitschecks berichten.
- Unsicherheit klar benennen.

Bei Prognosen:

- keine zufälligen Train/Test Splits bei Zeitreihen.
- nur vergangene Information im Training verwenden.
- Benchmarks einbeziehen.
- Prognosehorizont separat bewerten.
- Exogene Zukunftswerte sicherstellen.

---

## 25. Gute Berichtsformulierungen

### 25.1 Koeffizienten

Gut:

> Der Lag von `x` ist im Modell mit `y` verbunden, nachdem die übrigen Lags
> kontrolliert wurden.

Vorsichtig:

> Das Ergebnis deutet auf eine verzögerte Beziehung zwischen `x` und `y` hin.

Zu stark:

> `x` verursacht `y`.

### 25.2 Granger-Kausalität

Gut:

> Vergangene Werte von `x` verbessern die Prognose von `y` innerhalb der
> gewählten VAR-Spezifikation.

Zu stark:

> `x` ist die Ursache von `y`.

### 25.3 Impulsantworten

Gut:

> Nach einem positiven Schock in `x` zeigt `y` im Modell eine positive Reaktion
> über etwa drei Perioden. Die Unsicherheitsbänder sollten bei der Bewertung
> berücksichtigt werden.

Zu stark:

> Eine Erhöhung von `x` führt sicher zu einer Erhöhung von `y`.

### 25.4 Prognosen

Gut:

> Das VAR verbessert die kurzfristige Prognose gegenüber dem Benchmark im
> getesteten Zeitraum.

Zu stark:

> Das VAR sagt die Zukunft zuverlässig voraus.

---

## 26. Checkliste: Vor der Schätzung

- [ ] Fragestellung klar formuliert
- [ ] Ziel ist Prognose, Interpretation oder beides
- [ ] Variablen fachlich begründet
- [ ] Zeitfrequenz festgelegt
- [ ] Zeitraum dokumentiert
- [ ] Daten sortiert und duplikatfrei
- [ ] Missing Values geprüft
- [ ] Ausreißer geprüft
- [ ] Plots erstellt
- [ ] Transformationen entschieden
- [ ] Stationarität geprüft
- [ ] Kointegration geprüft, falls relevant
- [ ] maximale Lag-Zahl fachlich begründet
- [ ] Train/Test-Aufteilung zeitlich korrekt

---

## 27. Checkliste: Nach der Schätzung

- [ ] Informationskriterien dokumentiert
- [ ] gewählte Lag-Ordnung begründet
- [ ] Koeffizienten geprüft
- [ ] Residualautokorrelation geprüft
- [ ] Residualverteilung geprüft
- [ ] Heteroskedastizität geprüft
- [ ] Stabilität geprüft
- [ ] Modell gegen Benchmarks getestet
- [ ] IRFs mit Unsicherheit ausgewertet
- [ ] FEVD ausgewertet, falls relevant
- [ ] Granger-Kausalität nur vorsichtig interpretiert
- [ ] Robustheitschecks durchgeführt
- [ ] Limitierungen dokumentiert

---

## 28. Checkliste: Vor der Kommunikation der Ergebnisse

- [ ] Kausalität nicht überbehauptet
- [ ] Transformationen klar erklärt
- [ ] Einheiten der Variablen klar
- [ ] Prognosehorizont genannt
- [ ] Unsicherheit sichtbar
- [ ] Cholesky-Reihenfolge begründet, falls genutzt
- [ ] alternative Spezifikationen geprüft
- [ ] Modellgrenzen explizit genannt
- [ ] fachliche Plausibilität diskutiert

---

## 29. Mini-Beispiel zur Interpretation

Angenommen, ein VAR enthält:

- `sales`
- `traffic`
- `ad_spend`

Ein Granger-Test zeigt, dass `ad_spend` zusätzliche Prognoseinformation für
`sales` enthält.

Vorsichtige Interpretation:

> Innerhalb der gewählten Spezifikation verbessern vergangene Werte von
> `ad_spend` die Prognose von `sales`. Das spricht für eine verzögerte
> dynamische Beziehung. Es beweist aber nicht allein, dass höhere
> Werbeausgaben kausal höhere Umsätze verursachen.

Eine IRF zeigt, dass ein positiver Schock in `ad_spend` nach zwei Perioden mit
einem Anstieg von `sales` verbunden ist.

Vorsichtige Interpretation:

> Das Modell deutet auf eine verzögerte positive Reaktion von `sales` auf einen
> unerwarteten Anstieg in `ad_spend` hin. Die Aussage hängt von
> Spezifikation, Transformation, Schockdefinition und Identifikation ab.

---

## 30. Entscheidungshilfe: Wann ist VAR geeignet?

VAR ist gut geeignet, wenn:

- mehrere Zeitreihen sich gegenseitig beeinflussen könnten.
- dynamische Wechselwirkungen relevant sind.
- Prognosen mehrerer Variablen gemeinsam benötigt werden.
- man verzögerte Zusammenhänge untersuchen möchte.
- genug Daten vorhanden sind.
- lineare Approximation angemessen ist.

VAR ist weniger geeignet, wenn:

- nur eine Zielvariable interessiert und andere Variablen rein externe Treiber
  sind.
- sehr wenige Beobachtungen verfügbar sind.
- die Beziehungen stark nichtlinear sind.
- starke Regimewechsel dominieren.
- kausale Identifikation ohne zusätzliche Annahmen verlangt wird.
- Variablen unterschiedliche Frequenzen haben und nicht sauber harmonisiert
  werden können.

---

## 31. Alternativen zu VAR

Je nach Ziel können andere Methoden sinnvoller sein.

| Ziel oder Problem | Mögliche Alternative |
|---|---|
| eine einzelne Zeitreihe prognostizieren | ARIMA, ETS, Prophet, State Space Models |
| externe Treiber für eine Zielvariable | ARIMAX, Dynamic Regression, Distributed Lag Models |
| langfristige Beziehung nicht stationärer Variablen | VECM |
| viele Variablen, wenig Daten | BVAR, Factor Models, Regularisierung |
| nichtlineare Dynamik | Random Forests, Gradient Boosting, Neural Nets, nonlinear VAR |
| kausale Effekte | Experimente, Difference-in-Differences, IV, Causal Impact, SVAR mit starker Identifikation |
| wechselnde Regime | Markov Switching Models, Time-Varying Parameter VAR |

---

## 32. Kurzfazit

Vector Autoregression ist ein flexibles Werkzeug zur Analyse und Prognose
mehrerer miteinander verbundener Zeitreihen. Die Stärke liegt darin, dynamische
Wechselwirkungen ohne harte Vorabtrennung in Ursache und Wirkung abzubilden.

Die wichtigsten Punkte:

- VAR modelliert mehrere Variablen gemeinsam.
- Jede Variable wird durch eigene und fremde Lags erklärt.
- Lag-Ordnung, Variablenauswahl und Transformationen sind entscheidend.
- Stationarität, Stabilität und Residualdiagnostik müssen geprüft werden.
- Koeffizienten sind oft weniger anschaulich als Impulsantworten.
- Granger-Kausalität bedeutet Prognoseinformation, nicht automatisch echte
  Kausalität.
- Impulsantworten und FEVD hängen von Identifikationsannahmen ab.
- Große VARs brauchen viele Daten oder Regularisierung.
- Ergebnisse sollten immer mit Robustheitschecks und Benchmarks abgesichert
  werden.

Ein gutes VAR ist nicht das Modell mit den meisten Variablen, sondern das
Modell, dessen Spezifikation fachlich begründet, diagnostisch tragfähig und
interpretativ ehrlich ist.
