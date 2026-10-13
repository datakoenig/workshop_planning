# Workshop Fabric IQ Plan – Demo-Daten und Semantikmodell

Dieses Repository enthält die Demo-Daten, das Power-BI-Semantikmodell und die SQL-Skripte für den Workshop zu **Microsoft Fabric IQ Plan** (Planning Sheets, Power Tables, Intelligence Sheets). Alle Daten sind synthetisch und frei verwendbar. Sie sind so aufgebaut, dass sich die typischen Fragen einer Budget- und Forecast-Planung im Controlling damit durchspielen lassen: Gegenstromverfahren, rollierender Forecast, Berechtigungen, Kommentierung einer GuV und Treiberanalyse.

## Inhalt

```
Testdaten/                  CSV-Dateien, Generatoren, Datenmodell-Beschreibung
  SQL/                      T-SQL-Skripte für die Fabric SQL Database (Writeback-Ziel)
Semantikmodell/             Power-BI-Projekt (PBIP, TMDL) mit Bericht
  Workshop Fabric IQ Plan.pbip
  Workshop Fabric IQ Plan.SemanticModel/
  Workshop Fabric IQ Plan.Report/
```

## Der Leitfall

Ein Hersteller von Mode-Accessoires:

- **2 Sparten**, 6 Produktgruppen, 14 Produkte: Winter-Accessoires (Handschuhe, Schals, Mützen) und Sommer-Accessoires (Sandalen, Sonnenhüte, Sonnenbrillen)
- **12 Key Accounts** in 5 Regionen und 3 Ländern (Deutschland, Österreich, Schweiz). Die Regionen „West“ und „Ost“ kommen in mehreren Ländern vor – das ist Absicht, damit sich Leserechte auf Land und Schreibrechte auf Region unterscheiden lassen
- **8 Kostenstellen** in drei Bereichen (Vertrieb, Herstellung, Verwaltung), **9 Kostenarten**
- **Ist-Daten** Januar 2024 bis September 2026, **Budget 2026**, neun monatliche **Forecast-Stände** 2026, Kalender bis Dezember 2027 (Planjahr für die Budgetierung)

### Eingebaute Geschichten

Die Daten sind nicht zufällig, sondern erzählen etwas:

- **Saisonalität:** Winterware mit Spitze November bis Februar, Sommerware Mai bis August, Dezember als Spitze für alle. Verteilungsregeln „wie Vorjahr“ lassen sich daraus ableiten.
- **Gegenstromverfahren:** Das Budget 2026 liegt in drei Szenarien (Pessimistisch, Base, Optimistisch) und drei Versionen vor. Top-Down ist glatt (Vorjahr +5 %), Bottom-Up weicht je Kunde und Produkt ab, Konsolidiert liegt dazwischen. Base und Konsolidiert sind als Default markiert.
- **Forecast-Historie:** Stand `FC 2026MM` wurde am 1. des Monats erstellt und umfasst die Monate MM bis Dezember. Der Fehler sinkt mit kürzerem Horizont, d.h. die Prognosen für Juli 2026 nähern sich von Januar bis Juli dem Ist-Wert an. Sandalen werden bei langem Horizont systematisch zu optimistisch geplant.
- **Treiberanalyse:** Die Umsatzrendite liegt 2025 bei knapp 11 % (Ziel 10 %), 2026 deutlich darunter. Ursachen in den Daten: Preisdruck bei Sandalen (−8 %), Mengenrückgang bei Handschuhen (−10 %), Werbung +25 %.
- **GuV:** Umsatzkostenverfahren mit 18 Zeilen in drei Typen (Blatt, Summe, Berechnet). Nur Blattzeilen sind kommentierbar.

## Testdaten

Alle CSV-Dateien: UTF-8 mit BOM, Komma als Trennzeichen, Dezimalpunkt, Perioden als `JJJJ-MM`. Sie lassen sich direkt in ein Lakehouse, eine Fabric SQL Database oder per Power Query laden.

### Dimensionen

| Datei | Schlüssel | Inhalt |
|---|---|---|
| Dim_Kalender | Periode | Jahr → Quartal → Monat, `Monatsbeginn` als Datum, `Status` abgeschlossen/offen (Grenze 2026-09) |
| Dim_KeyAccount | KeyAccountID | Land → Region → Key Account |
| Dim_Produkt | ProduktID | Sparte → Produktgruppe → Produkt |
| Dim_Kostenstelle | KostenstelleID | Bereich → Kostenstelle |
| Dim_Kostenart | KostenartID | Kostenart mit Zuordnung zur GuV-Zeile |
| Dim_GuV | GuVZeileID | GuV nach Umsatzkostenverfahren, Parent-Child, `Typ`, `Kommentierbar`, flache Darstellung `GuV Zeile` mit Einrückung, Hierarchiespalten Ebene1/Ebene2 |
| Dim_Szenario | Szenario | Pessimistisch, Base (Default), Optimistisch |
| Dim_Version | Version | Top-Down, Bottom-Up, Konsolidiert (Default) |
| Dim_ForecastStand | ForecastStand | FC 202601 … FC 202609 mit Erstellungsdatum |
| Dim_Treiber | Treiber | Treiberbaum: Absatzmenge, Preis, Stückkosten → Umsatz, variable Kosten → Deckungsbeitrag → Fixkosten → EBIT → Umsatzrendite |

### Fakten

| Datei | Granularität | Kennzahlen |
|---|---|---|
| Fact_Absatz_Ist | Periode × Key Account × Produkt | Menge, Preis, Umsatz, VariableKosten |
| Fact_Gemeinkosten_Ist | Periode × Kostenstelle × Kostenart | Betrag |
| Fact_SonstigeErtraege_Ist | Periode | Betrag |
| Fact_Budget_Absatz | Periode × Szenario × Version × Key Account × Produkt | Menge, Preis, Umsatz |
| Fact_Budget_Gemeinkosten | Periode × Szenario × Version × Kostenstelle × Kostenart | Betrag |
| Fact_Forecast_Absatz | ForecastStand × Periode × Key Account × Produkt | Menge, Preis, Umsatz |
| Fact_Kommentare | GuV-Zeile × Periode × Bearbeiter | Kommentar, Zeitstempel |

Die Budget- und Forecast-Fakten sind der **Startzustand**. Im Workshop werden sie durch die Writeback-Tabellen aus Fabric IQ Plan ergänzt oder ersetzt; die Tabellennamen im Semantikmodell bleiben dabei gleich, nur die Quelle wechselt von CSV auf die SQL-View.

### Konfiguration und Berechtigungen

| Datei | Zweck |
|---|---|
| Config_Berechtigungen | Eine Zeile je Recht: Benutzer, Planungsbereich, Recht (Lesen/Schreiben), Ebene (Gesamt/Land/Region/KeyAccount), Wert |
| Berechtigung_KeyAccount | Die Berechtigungen aufgelöst je Benutzer × Key Account; Grundlage für RLS und Schreibrechte im Modell |
| Config_Berechtigungsantraege | Beispiele für einen Antragsworkflow (beantragt / freigegeben / abgelehnt) |
| Config_Zielwerte | Ziel-Umsatzrendite je Produktgruppe |

Die Benutzer in den Berechtigungstabellen sind Platzhalter (`@demo.local`). Für eigene Tests die Zeilen auf echte Benutzerprinzipalnamen (UPN) umstellen – genau so, wie `USERPRINCIPALNAME()` sie liefert.

### Generatoren

Alle Dateien werden aus Python-Skripten erzeugt (benötigt `pandas` und `numpy`). Die Erzeugung ist deterministisch (fester Zufalls-Seed), d.h. ein erneuter Lauf ergibt identische Daten.

| Skript | Erzeugt |
|---|---|
| `generate_testdaten.py` | alle CSV-Dateien |
| `generate_semantikmodell.py` | das Power-BI-Projekt (TMDL) – überschreibt den Ordner `Semantikmodell`, inkl. Beziehungen, Measures und RLS-Rolle |
| `generate_bericht.py` | die Berichtsseiten (PBIR) – überschreibt den Bericht |
| `generate_sql.py` | die T-SQL-Skripte im Ordner `SQL` |

Wer das Modell oder den Bericht in Power BI Desktop weiterbearbeitet hat, sollte die beiden mittleren Skripte nicht mehr ausführen, sondern Änderungen direkt im Projekt vornehmen.

## Semantikmodell

Power-BI-Projekt im TMDL-Format. Öffnen über `Semantikmodell\Workshop Fabric IQ Plan.pbip` in Power BI Desktop (die Vorschaufunktion für PBIP-Projekte muss aktiviert sein). Nach dem Öffnen **Aktualisieren**; die CSV-Dateien werden über den Parameter `Ordner` geladen, dessen Pfad einmalig auf den eigenen Testdaten-Ordner anzupassen ist (Transformieren → Parameter bearbeiten). Anschließend in einen Fabric-Workspace veröffentlichen.

### Struktur

- Sternschema: sieben Faktentabellen an den Dimensionen; `Dim_KeyAccount_Eingabe` ist eine zweite Key-Account-Dimension ohne Beziehungen, die nur über eine eigene RLS-Regel die Zeilen eines Eingabe-Sheets auf die beschreibbaren Key Accounts begrenzt
- Hierarchien: Zeit (Jahr → Quartal → Monat), GuV Struktur (Ebene1 → Ebene2)
- Tabelle `Kennzahlen` mit allen Measures (siehe unten)
- RLS-Rolle `Vertrieb`: filtert `Dim_KeyAccount` nach Leserechten und `Dim_KeyAccount_Eingabe` nach Schreibrechten aus `Berechtigung_KeyAccount`, jeweils über `USERPRINCIPALNAME()`. Alle Nutzer müssen Mitglied dieser Rolle sein; was jemand sieht, entscheidet ausschließlich die Berechtigungstabelle

### Measures (Auswahl)

**Ist:** Umsatz Ist, Menge Ist, Preis Ist, Variable Kosten Ist, Var. Stückkosten Ist, Gemeinkosten Ist, Deckungsbeitrag Ist, EBIT Ist, Umsatzrendite Ist, Ziel Umsatzrendite, Abw. Umsatzrendite zu Ziel (Pp.). Gemeinkosten und sonstige Erträge werden bei Filtern auf Produkt oder Key Account nach Umsatzanteil zugerechnet (`Umsatzanteil`, `… (zugerechnet)`), damit EBIT und Rendite je Produktgruppe sinnvoll sind.

**Vorjahr:** Menge Ist VJ, Umsatz Ist VJ, Preis Ist VJ, Menge Ist Abw. VJ %.

**Budget:** Budget Umsatz, Budget Menge, Budget Preis, Budget Gemeinkosten – fallen ohne Slicer-Auswahl automatisch auf das Default-Szenario Base und die Default-Version Konsolidiert zurück (Spalte `IstDefault`). Die Varianten `… (gewählt)` summieren ohne diese Logik und sind für Matrizen mit Szenario oder Version im Grid gedacht.

**Forecast:** Forecast Umsatz, Forecast Menge, Last Estimate Umsatz/Menge (neuester Stand), Letzter Forecast für Periode (Horizont 0), Menge Ist/LE und Umsatz Ist/LE (abgeschlossene Perioden Ist, offene Last Estimate), die Vorjahresvarianten `… Ist/LE VJ` als Referenz für die Planung des Folgejahres, Abw. zu Budget, Abw. zu Budget %, Prognoseverlauf Umsatz (für die Analyse der Prognosegenauigkeit je Forecast-Stand), Prognosefehler %.

**Berechtigungen:** Schreibrecht (Text „Ja“/„Nein“ je Key Account für den angemeldeten Nutzer), Angemeldeter Benutzer, sowie die Varianten `… (Eingabe)` für Sheets mit `Dim_KeyAccount_Eingabe` in den Zeilen, darunter Budget Menge Land (Eingabe) und Anteil am Land % (Eingabe) für die Landessumme neben der eigenen Eingabe.

**GuV:** GuV Betrag Ist (leitet alle 18 Zeilen inkl. Summen und berechneter Zeilen aus den Fakten her), GuV Betrag VJ, GuV Abw. VJ, GuV Abw. VJ %, Kommentierbar, Anzahl Kommentare, Kommentare (Text), Kommentar vorhanden (Indikator).

**Treiber:** Treiberwert (liefert je Member von `Dim_Treiber` den passenden Wert für ein Row Model).

### Bericht

Fünf Seiten als Einstieg in die Daten: Überblick, Budget 2026, Forecast, GuV, Berechtigungen. Die Seite Forecast braucht einen gewählten Planmonat im Slicer, um den Prognoseverlauf sinnvoll anzuzeigen.

## SQL-Skripte

Für die Fabric SQL Database, die als Writeback-Ziel von Fabric IQ Plan dient. In dieser Reihenfolge ausführen:

| Skript | Inhalt |
|---|---|
| `01_ref_stammdaten.sql` | Schemas `ref` und `planung`, Referenztabellen `ref.Dim_KeyAccount` und `ref.Dim_Produkt` |
| `02_plan_view.sql` | View `planung.v_Absatz_Plan`: übersetzt die Beschriftungen der Writeback-Tabelle in IDs. Die Spaltennamen der Writeback-Tabelle nach dem ersten Writeback prüfen und anpassen |
| `03_berechtigungen.sql` | Lookup-Tabellen für Power-Table-Dropdowns, `planung.Berechtigungen` mit Audit-Trigger, `ref.v_Berechtigungswert` für den abhängigen Dropdown Ebene → Wert, `planung.v_Berechtigung_KeyAccount` (aufgelöste Rechte) |
| `04_kommentare.sql` | `ref.Dim_GuV`, `planung.Kommentare` mit Trigger gegen Kommentare auf Summenzeilen, `planung.v_Kommentare` |

Das Schema heißt `planung`, weil `plan` in T-SQL ein reserviertes Wort ist.

Fabric IQ Plan schreibt die **Beschriftungen** der Dimensionen zurück, keine Schlüssel. Die Übersetzung in IDs passiert bewusst in der Datenbank (Views), nicht über Beziehungen auf Namensspalten im Modell. Die Referenztabellen in `ref` sind damit zugleich der Ort, an dem Umbenennungen von Stammdaten zentral abgefangen werden.

## Hinweise

- Die Daten sind vollständig synthetisch; Firmen-, Produkt- und Personennamen sind erfunden.
- Lizenz: frei verwendbar für Schulung, Demo und eigene Tests.
