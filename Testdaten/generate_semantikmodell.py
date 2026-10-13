# Erzeugt ein Power-BI-Projekt (PBIP, TMDL) für die Demo-Daten.
# Ausführen: python generate_semantikmodell.py  -> Ordner "..\Semantikmodell"
import os, uuid, json
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(os.path.dirname(HERE), "Semantikmodell")
NAME = "Workshop Fabric IQ Plan"
SM = os.path.join(ROOT, NAME + ".SemanticModel"); DEF = os.path.join(SM, "definition")
RP = os.path.join(ROOT, NAME + ".Report")
for d in [os.path.join(DEF, "tables"), RP]: os.makedirs(d, exist_ok=True)
# >>> ANPASSEN: lokaler Pfad zum Ordner "Testdaten" (wird als Parameter "Ordner" ins Modell geschrieben; in Power BI Desktop jederzeit änderbar)
CSV_DIR = r"C:\Users\artur\OneDrive\Dokumente\Claude\Projects\Workshop Fabric Plan\Testdaten" + "\\"
g = lambda: str(uuid.uuid4())
def w(path, text): open(path, "w", encoding="utf-8", newline="\n").write(text)

# ---- Tabellen: (Name, [(Spalte, Typ)], ist_dimension)
S, I, D, B, DT = "string", "int64", "double", "boolean", "dateTime"
tables = {
 "Dim_Kalender": ([("Periode",S),("Datum",DT),("Monatsbeginn",DT),("Jahr",I),("Monat",I),("MonatName",S),("Quartal",S),("Status",S)], True),
 "Dim_KeyAccount": ([("KeyAccountID",S),("KeyAccount",S),("Region",S),("Land",S)], True),
 "Dim_Produkt": ([("ProduktID",S),("Produkt",S),("Produktgruppe",S),("Sparte",S)], True),
 "Dim_Kostenstelle": ([("KostenstelleID",S),("Kostenstelle",S),("Bereich",S)], True),
 "Dim_Kostenart": ([("KostenartID",S),("Kostenart",S),("GuVZuordnung",S)], True),
 "Dim_GuV": ([("GuVZeileID",S),("Bezeichnung",S),("ParentID",S),("Sortierung",I),("Typ",S),("Quelle",S),("Kommentierbar",B),("Ebene1",S),("Ebene2",S),("Sortierung1",I),("Sortierung2",I),("GuV Zeile",S),("Fett",B)], True),
 "Dim_Szenario": ([("Szenario",S),("Sortierung",I),("IstDefault",B)], True),
 "Dim_Version": ([("Version",S),("Sortierung",I),("IstDefault",B)], True),
 "Dim_ForecastStand": ([("ForecastStand",S),("Erstellt",DT),("Sortierung",I)], True),
 "Dim_Treiber": ([("Treiber",S),("Formel",S),("Typ",S),("Einheit",S)], True),
 "Fact_Absatz_Ist": ([("Periode",S),("KeyAccountID",S),("ProduktID",S),("Menge",I),("Preis",D),("Umsatz",D),("VariableKosten",D)], False),
 "Fact_Gemeinkosten_Ist": ([("Periode",S),("KostenstelleID",S),("KostenartID",S),("Betrag",D)], False),
 "Fact_SonstigeErtraege_Ist": ([("Periode",S),("GuVZeileID",S),("Betrag",D)], False),
 "Fact_Budget_Absatz": ([("Periode",S),("Szenario",S),("Version",S),("KeyAccountID",S),("ProduktID",S),("Menge",I),("Preis",D),("Umsatz",D)], False),
 "Fact_Budget_Gemeinkosten": ([("Periode",S),("Szenario",S),("Version",S),("KostenstelleID",S),("KostenartID",S),("Betrag",D)], False),
 "Fact_Forecast_Absatz": ([("ForecastStand",S),("Periode",S),("KeyAccountID",S),("ProduktID",S),("Menge",I),("Preis",D),("Umsatz",D)], False),
 "Fact_Kommentare": ([("KommentarID",I),("GuVZeileID",S),("Periode",S),("Bearbeiter",S),("Zeitstempel",DT),("Kommentar",S)], False),
 "Config_Berechtigungen": ([("Benutzer",S),("Planungsbereich",S),("Recht",S),("Ebene",S),("Wert",S)], True),
 "Config_Berechtigungsantraege": ([("AntragID",I),("Benutzer",S),("Planungsbereich",S),("Ebene",S),("Wert",S),("Begruendung",S),("Status",S),("Freigabe_durch",S),("Freigabe_am",S)], True),
 "Berechtigung_KeyAccount": ([("Benutzer",S),("Planungsbereich",S),("Recht",S),("KeyAccountID",S)], True),
 "Dim_KeyAccount_Eingabe": ([("KeyAccountID",S),("KeyAccount",S),("Region",S),("Land",S)], True),   # gleiche CSV wie Dim_KeyAccount, eigene RLS-Regel (Schreibrechte)
 "Config_Zielwerte": ([("Produktgruppe",S),("Ziel_Umsatzrendite",D)], True),
}
mtype = {S:"type text", I:"Int64.Type", D:"type number", B:"type logical", DT:"type datetime"}
sortby = {"Dim_Kalender":{"MonatName":"Monat"}, "Dim_GuV":{"Bezeichnung":"Sortierung","Ebene1":"Sortierung1","Ebene2":"Sortierung2","GuV Zeile":"Sortierung"},
          "Dim_Szenario":{"Szenario":"Sortierung"}, "Dim_Version":{"Version":"Sortierung"}, "Dim_ForecastStand":{"ForecastStand":"Sortierung"}}
fmt = {D:"#,0.00", I:"#,0", DT:"dd.MM.yyyy"}

for name, (cols, isdim) in tables.items():
    out = [f"table {name}", f"\tlineageTag: {g()}", ""]
    for c, t in cols:
        out += [f"\tcolumn {c}", f"\t\tdataType: {t}", f"\tlineageTag: {g()}".replace("\t","\t\t",1),
                f"\t\tsummarizeBy: {'none' if (isdim or t in (S,B,DT) or c.endswith('ID')) else 'sum'}",
                f"\t\tsourceColumn: {c}"]
        if t in fmt: out.append(f"\t\tformatString: {fmt[t]}")
        if c in sortby.get(name, {}): out.append(f"\t\tsortByColumn: {sortby[name][c]}")
        out.append("")
    if name == "Dim_GuV":
        out += ["\thierarchy 'GuV Struktur'", f"\t\tlineageTag: {g()}", "", "\t\tlevel Ebene1", f"\t\t\tlineageTag: {g()}", "\t\t\tcolumn: Ebene1", "",
                "\t\tlevel Ebene2", f"\t\t\tlineageTag: {g()}", "\t\t\tcolumn: Ebene2", ""]
    if name == "Dim_Kalender":
        out += ["\thierarchy Zeit", f"\t\tlineageTag: {g()}", "", "\t\tlevel Jahr", f"\t\t\tlineageTag: {g()}", "\t\t\tcolumn: Jahr", "",
                "\t\tlevel Quartal", f"\t\t\tlineageTag: {g()}", "\t\t\tcolumn: Quartal", "", "\t\tlevel Monat", f"\t\t\tlineageTag: {g()}", "\t\t\tcolumn: MonatName", ""]
    typen = ", ".join(f'{{"{c}", {mtype[t]}}}' for c, t in cols)
    out += [f"\tpartition {name} = m", "\t\tmode: import", "\t\tsource =", "\t\t\t\tlet",
            f'\t\t\t\t    Quelle = Csv.Document(File.Contents(Ordner & "{"Dim_KeyAccount" if name == "Dim_KeyAccount_Eingabe" else name}.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),',
            "\t\t\t\t    Header = Table.PromoteHeaders(Quelle, [PromoteAllScalars = true]),",
            f'\t\t\t\t    Typen = Table.TransformColumnTypes(Header, {{{typen}}}, "en-US")',
            "\t\t\t\tin", "\t\t\t\t    Typen", ""]
    if name == "Dim_Kalender": out.insert(len(out)-1, "")  # Datentabelle
    w(os.path.join(DEF, "tables", name + ".tmdl"), "\n".join(out))

# ---- Kennzahlen
measures = [
 ("Umsatz Ist", "SUM ( Fact_Absatz_Ist[Umsatz] )", "#,0"),
 ("Menge Ist", "SUM ( Fact_Absatz_Ist[Menge] )", "#,0"),
 ("Variable Kosten Ist", "SUM ( Fact_Absatz_Ist[VariableKosten] )", "#,0"),
 ("Gemeinkosten Ist", "SUM ( Fact_Gemeinkosten_Ist[Betrag] )", "#,0"),
 ("Sonstige Erträge Ist", "SUM ( Fact_SonstigeErtraege_Ist[Betrag] )", "#,0"),
 ('Menge Ist VJ', '-- Vorjahreswert im gleichen Monat (bzw. Quartal/Jahr), unabhängig von Periode-Filtern\nVAR _vj = MAX ( Dim_Kalender[Jahr] ) - 1\nVAR _monate = VALUES ( Dim_Kalender[Monat] )\nRETURN CALCULATE ( [Menge Ist], REMOVEFILTERS ( Dim_Kalender ), Dim_Kalender[Jahr] = _vj, _monate )', '#,0'),
 ('Umsatz Ist VJ', 'VAR _vj = MAX ( Dim_Kalender[Jahr] ) - 1\nVAR _monate = VALUES ( Dim_Kalender[Monat] )\nRETURN CALCULATE ( [Umsatz Ist], REMOVEFILTERS ( Dim_Kalender ), Dim_Kalender[Jahr] = _vj, _monate )', '#,0'),
 ('Preis Ist', '-- mengengewichteter Durchschnittspreis\nDIVIDE ( [Umsatz Ist], [Menge Ist] )', '#,0.00'),
 ('Preis Ist VJ', 'DIVIDE ( [Umsatz Ist VJ], [Menge Ist VJ] )', '#,0.00'),
 ('Menge Ist Abw. VJ %', 'DIVIDE ( [Menge Ist] - [Menge Ist VJ], [Menge Ist VJ] )', '0.0 %;-0.0 %;0.0 %'),
 ("Deckungsbeitrag Ist", "[Umsatz Ist] - [Variable Kosten Ist]", "#,0"),
 ('Umsatzanteil', '-- Anteil des gefilterten Umsatzes (Produkt / Key Account) am Gesamtumsatz, für die Schlüsselung der Gemeinkosten\nDIVIDE ( [Umsatz Ist], CALCULATE ( [Umsatz Ist], REMOVEFILTERS ( Dim_Produkt ), REMOVEFILTERS ( Dim_KeyAccount ) ) )', '0.0 %'),
 ('Gemeinkosten Ist (zugerechnet)', '[Gemeinkosten Ist] * [Umsatzanteil]', '#,0'),
 ('Sonstige Erträge Ist (zugerechnet)', '[Sonstige Erträge Ist] * [Umsatzanteil]', '#,0'),
 ("EBIT Ist", "-- Gemeinkosten und sonstige Erträge nach Umsatzanteil geschlüsselt, damit EBIT je Produktgruppe / Key Account sinnvoll ist\n[Deckungsbeitrag Ist] - [Gemeinkosten Ist (zugerechnet)] + [Sonstige Erträge Ist (zugerechnet)]", "#,0"),
 ("Umsatzrendite Ist", "DIVIDE ( [EBIT Ist], [Umsatz Ist] )", "0.0 %"),
 ('Var. Stückkosten Ist', 'DIVIDE ( [Variable Kosten Ist], [Menge Ist] )', '#,0.00'),
 ('Treiberwert', '-- Wert je Member von Dim_Treiber für das Row Model (Treiberbaum) im Planning Sheet; Fixkosten nach Umsatzanteil zugerechnet\nSWITCH (\n    SELECTEDVALUE ( Dim_Treiber[Treiber] ),\n    "Absatzmenge", [Menge Ist],\n    "Preis", [Preis Ist],\n    "VarStueckkosten", [Var. Stückkosten Ist],\n    "Umsatz", [Umsatz Ist],\n    "VariableKosten", [Variable Kosten Ist],\n    "Deckungsbeitrag", [Deckungsbeitrag Ist],\n    "Fixkosten", [Gemeinkosten Ist (zugerechnet)] - [Sonstige Erträge Ist (zugerechnet)],\n    "EBIT", [EBIT Ist],\n    "Umsatzrendite", [Umsatzrendite Ist]\n)', '#,0.00'),
 ("Ziel Umsatzrendite", """VAR _pg = SELECTEDVALUE ( Dim_Produkt[Produktgruppe], "Gesamt" )
RETURN LOOKUPVALUE ( Config_Zielwerte[Ziel_Umsatzrendite], Config_Zielwerte[Produktgruppe], _pg )""", "0.0 %"),
 ("Abw. Umsatzrendite zu Ziel (Pp.)", "( [Umsatzrendite Ist] - [Ziel Umsatzrendite] ) * 100", "0.0"),
 # Budget
 ("Budget Umsatz (gewählt)", "SUM ( Fact_Budget_Absatz[Umsatz] )", "#,0"),
 ("Budget Menge (gewählt)", "SUM ( Fact_Budget_Absatz[Menge] )", "#,0"),
 ("Budget Gemeinkosten (gewählt)", "SUM ( Fact_Budget_Gemeinkosten[Betrag] )", "#,0"),
 ("Budget Umsatz", """-- Ohne Auswahl: Base-Szenario und Version Konsolidiert (IstDefault)
VAR _szGewaehlt = ISFILTERED ( Dim_Szenario[Szenario] )
VAR _veGewaehlt = ISFILTERED ( Dim_Version[Version] )
RETURN
    CALCULATE (
        SUM ( Fact_Budget_Absatz[Umsatz] ),
        FILTER ( VALUES ( Dim_Szenario ), _szGewaehlt || Dim_Szenario[IstDefault] = TRUE () ),
        FILTER ( VALUES ( Dim_Version ), _veGewaehlt || Dim_Version[IstDefault] = TRUE () )
    )""", "#,0"),
 ('Budget Menge', '-- Ohne Auswahl: Base-Szenario und Version Konsolidiert (IstDefault)\nVAR _szGewaehlt = ISFILTERED ( Dim_Szenario[Szenario] )\nVAR _veGewaehlt = ISFILTERED ( Dim_Version[Version] )\nRETURN\n    CALCULATE (\n        SUM ( Fact_Budget_Absatz[Menge] ),\n        FILTER ( VALUES ( Dim_Szenario ), _szGewaehlt || Dim_Szenario[IstDefault] = TRUE () ),\n        FILTER ( VALUES ( Dim_Version ), _veGewaehlt || Dim_Version[IstDefault] = TRUE () )\n    )', '#,0'),
 ('Budget Preis', 'DIVIDE ( [Budget Umsatz], [Budget Menge] )', '#,0.00'),
 ('Budget Menge Land', '-- Landessumme unabhängig vom Key-Account-Filter (z.B. Schreibrecht = 1); innerhalb der RLS\nVAR _land = VALUES ( Dim_KeyAccount[Land] )\nRETURN CALCULATE ( [Budget Menge], REMOVEFILTERS ( Dim_KeyAccount ), TREATAS ( _land, Dim_KeyAccount[Land] ) )', '#,0'),
 ('Budget Umsatz Land', 'VAR _land = VALUES ( Dim_KeyAccount[Land] )\nRETURN CALCULATE ( [Budget Umsatz], REMOVEFILTERS ( Dim_KeyAccount ), TREATAS ( _land, Dim_KeyAccount[Land] ) )', '#,0'),
 ('Anteil am Land %', 'DIVIDE ( [Budget Umsatz], [Budget Umsatz Land] )', '0.0 %'),
 ("Budget Gemeinkosten", """VAR _szGewaehlt = ISFILTERED ( Dim_Szenario[Szenario] )
VAR _veGewaehlt = ISFILTERED ( Dim_Version[Version] )
RETURN
    CALCULATE (
        SUM ( Fact_Budget_Gemeinkosten[Betrag] ),
        FILTER ( VALUES ( Dim_Szenario ), _szGewaehlt || Dim_Szenario[IstDefault] = TRUE () ),
        FILTER ( VALUES ( Dim_Version ), _veGewaehlt || Dim_Version[IstDefault] = TRUE () )
    )""", "#,0"),
 # Forecast
 ("Forecast Umsatz", "SUM ( Fact_Forecast_Absatz[Umsatz] )", "#,0"),
 ("Forecast Menge", "SUM ( Fact_Forecast_Absatz[Menge] )", "#,0"),
 ("Last Estimate Umsatz", """-- Neuester Forecast-Stand, unabhängig von einer Stand-Auswahl
VAR _neu = CALCULATE ( MAX ( Dim_ForecastStand[Sortierung] ), REMOVEFILTERS ( Dim_ForecastStand ) )
RETURN CALCULATE ( [Forecast Umsatz], REMOVEFILTERS ( Dim_ForecastStand ), Dim_ForecastStand[Sortierung] = _neu )""", "#,0"),
 ("Letzter Forecast für Periode", """-- Für abgeschlossene Perioden: der Stand, der im Monat der Periode erstellt wurde (Horizont 0)
VAR _mo = MAX ( Dim_Kalender[Monat] )
RETURN CALCULATE ( [Forecast Umsatz], REMOVEFILTERS ( Dim_ForecastStand ), Dim_ForecastStand[Sortierung] = _mo )""", "#,0"),
 ('Last Estimate Menge', 'VAR _neu = CALCULATE ( MAX ( Dim_ForecastStand[Sortierung] ), REMOVEFILTERS ( Dim_ForecastStand ) )\nRETURN CALCULATE ( [Forecast Menge], REMOVEFILTERS ( Dim_ForecastStand ), Dim_ForecastStand[Sortierung] = _neu )', '#,0'),
 ('Menge Ist/LE', '-- je Periode: abgeschlossen -> Ist, offen -> neuester Forecast-Stand; auch auf Quartals-/Jahresebene korrekt\nSUMX ( VALUES ( Dim_Kalender[Periode] ), IF ( CALCULATE ( MAX ( Dim_Kalender[Status] ) ) = "abgeschlossen", [Menge Ist], [Last Estimate Menge] ) )', '#,0'),
 ('Umsatz Ist/LE', 'SUMX ( VALUES ( Dim_Kalender[Periode] ), IF ( CALCULATE ( MAX ( Dim_Kalender[Status] ) ) = "abgeschlossen", [Umsatz Ist], [Last Estimate Umsatz] ) )', '#,0'),
 ('Menge Ist/LE VJ', '-- Referenz für die Budgetplanung des Folgejahres (z.B. 2027 -> Ist/LE 2026)\nVAR _vj = MAX ( Dim_Kalender[Jahr] ) - 1\nVAR _monate = VALUES ( Dim_Kalender[Monat] )\nRETURN CALCULATE ( [Menge Ist/LE], REMOVEFILTERS ( Dim_Kalender ), Dim_Kalender[Jahr] = _vj, _monate )', '#,0'),
 ('Umsatz Ist/LE VJ', 'VAR _vj = MAX ( Dim_Kalender[Jahr] ) - 1\nVAR _monate = VALUES ( Dim_Kalender[Monat] )\nRETURN CALCULATE ( [Umsatz Ist/LE], REMOVEFILTERS ( Dim_Kalender ), Dim_Kalender[Jahr] = _vj, _monate )', '#,0'),
 ('Preis Ist/LE VJ', 'DIVIDE ( [Umsatz Ist/LE VJ], [Menge Ist/LE VJ] )', '#,0.00'),
 ("LE / Ist Umsatz", "[Umsatz Ist/LE]", "#,0"),
 ("Abw. zu Budget", "[LE / Ist Umsatz] - [Budget Umsatz]", "#,0;-#,0;0"),
 ("Abw. zu Budget %", "DIVIDE ( [Abw. zu Budget], [Budget Umsatz] )", "0.0 %;-0.0 %;0.0 %"),
 ("Prognoseverlauf Umsatz", """-- Für einen gewählten Planmonat: je Forecast-Stand der Wert für diesen Monat, im Monat selbst der Ist-Wert
VAR _mo = MAX ( Dim_Kalender[Monat] )
VAR _st = MAX ( Dim_ForecastStand[Sortierung] )
RETURN SWITCH ( TRUE (), _st < _mo, [Forecast Umsatz], _st = _mo, [Umsatz Ist], BLANK () )""", "#,0"),
 ("Prognosefehler %", "DIVIDE ( [Forecast Umsatz] - [Umsatz Ist], [Umsatz Ist] )", "0.0 %;-0.0 %;0.0 %"),
 # GuV
 ("GuV Betrag Ist", """-- GuV-Zeile im Kontext: bei einer Zeile diese, bei mehreren (Ebene1-Knoten) die Zeile ohne Parent; auf Gesamtebene leer
VAR _z =
    IF (
        HASONEVALUE ( Dim_GuV[GuVZeileID] ),
        SELECTEDVALUE ( Dim_GuV[GuVZeileID] ),
        IF (
            ISINSCOPE ( Dim_GuV[Ebene1] ) || ISINSCOPE ( Dim_GuV[Bezeichnung] ),
            CALCULATE ( MIN ( Dim_GuV[GuVZeileID] ), ISBLANK ( Dim_GuV[ParentID] ) ),
            BLANK ()
        )
    )
VAR _g021 = [Variable Kosten Ist]
VAR _g022 = CALCULATE ( [Gemeinkosten Ist], Dim_Kostenstelle[Bereich] = "Herstellung" )
VAR _g031 = CALCULATE ( [Gemeinkosten Ist], Dim_Kostenstelle[Bereich] = "Vertrieb", Dim_Kostenart[GuVZuordnung] = "Personal" )
VAR _g032 = CALCULATE ( [Gemeinkosten Ist], Dim_Kostenart[GuVZuordnung] = "Provision" )
VAR _g033 = CALCULATE ( [Gemeinkosten Ist], Dim_Kostenart[GuVZuordnung] = "Distribution" )
VAR _g034 = CALCULATE ( [Gemeinkosten Ist], Dim_Kostenart[GuVZuordnung] = "Werbung" )
VAR _g035 = CALCULATE ( [Gemeinkosten Ist], Dim_Kostenstelle[Bereich] = "Vertrieb", NOT Dim_Kostenart[GuVZuordnung] IN { "Personal", "Provision", "Distribution", "Werbung" } )
VAR _g041 = CALCULATE ( [Gemeinkosten Ist], Dim_Kostenstelle[Bereich] = "Verwaltung", Dim_Kostenart[GuVZuordnung] = "Personal" )
VAR _g042 = CALCULATE ( [Gemeinkosten Ist], Dim_Kostenart[GuVZuordnung] IN { "Miete", "IT" } )
VAR _g043 = CALCULATE ( [Gemeinkosten Ist], Dim_Kostenstelle[Bereich] = "Verwaltung", NOT Dim_Kostenart[GuVZuordnung] IN { "Personal", "Miete", "IT" } )
VAR _g010 = [Umsatz Ist]
VAR _g020 = _g021 + _g022
VAR _g025 = _g010 - _g020
VAR _g030 = _g031 + _g032 + _g033 + _g034 + _g035
VAR _g040 = _g041 + _g042 + _g043
VAR _g050 = CALCULATE ( [Sonstige Erträge Ist], REMOVEFILTERS ( Dim_GuV ) )
VAR _g060 = _g025 - _g030 - _g040 + _g050
RETURN SWITCH ( _z,
    "G010", _g010, "G020", _g020, "G021", _g021, "G022", _g022, "G025", _g025,
    "G030", _g030, "G031", _g031, "G032", _g032, "G033", _g033, "G034", _g034, "G035", _g035,
    "G040", _g040, "G041", _g041, "G042", _g042, "G043", _g043,
    "G050", _g050, "G060", _g060, "G070", DIVIDE ( _g060, _g010 ) )""", "#,0.00"),
 ('Schreibrecht', '-- 1, wenn im aktuellen Kontext mindestens ein Key Account liegt, für den der angemeldete Nutzer schreiben darf\n-- (robust für Zeilen, Summen und Spaltenkontexte); Text "Ja"/"Nein", weil Fabric Plan Measure-Filterwerte als Text übergibt; Filter im Eingabe-Sheet: Schreibrecht = Ja\nVAR _erlaubt =\n    SELECTCOLUMNS (\n        FILTER (\n            ALL ( Berechtigung_KeyAccount ),\n            Berechtigung_KeyAccount[Benutzer] = USERPRINCIPALNAME ()\n                && Berechtigung_KeyAccount[Planungsbereich] = "Vertrieb"\n                && Berechtigung_KeyAccount[Recht] = "Schreiben"\n        ),\n        "k", Berechtigung_KeyAccount[KeyAccountID]\n    )\nRETURN\n    IF ( COUNTROWS ( INTERSECT ( VALUES ( Dim_KeyAccount[KeyAccountID] ), _erlaubt ) ) > 0, "Ja", "Nein" )', None),
 ('Angemeldeter Benutzer', 'USERPRINCIPALNAME ()', None),
 ('Menge Ist (Eingabe)', '-- für Sheets mit Dim_KeyAccount_Eingabe in den Zeilen (keine Beziehung, RLS nach Schreibrecht)\nCALCULATE ( [Menge Ist], TREATAS ( VALUES ( Dim_KeyAccount_Eingabe[KeyAccountID] ), Dim_KeyAccount[KeyAccountID] ) )', '#,0'),
 ('Umsatz Ist (Eingabe)', '-- für Sheets mit Dim_KeyAccount_Eingabe in den Zeilen (keine Beziehung, RLS nach Schreibrecht)\nCALCULATE ( [Umsatz Ist], TREATAS ( VALUES ( Dim_KeyAccount_Eingabe[KeyAccountID] ), Dim_KeyAccount[KeyAccountID] ) )', '#,0'),
 ('Menge Ist VJ (Eingabe)', '-- für Sheets mit Dim_KeyAccount_Eingabe in den Zeilen (keine Beziehung, RLS nach Schreibrecht)\nCALCULATE ( [Menge Ist VJ], TREATAS ( VALUES ( Dim_KeyAccount_Eingabe[KeyAccountID] ), Dim_KeyAccount[KeyAccountID] ) )', '#,0'),
 ('Umsatz Ist VJ (Eingabe)', '-- für Sheets mit Dim_KeyAccount_Eingabe in den Zeilen (keine Beziehung, RLS nach Schreibrecht)\nCALCULATE ( [Umsatz Ist VJ], TREATAS ( VALUES ( Dim_KeyAccount_Eingabe[KeyAccountID] ), Dim_KeyAccount[KeyAccountID] ) )', '#,0'),
 ('Menge Ist/LE VJ (Eingabe)', '-- für Sheets mit Dim_KeyAccount_Eingabe in den Zeilen (keine Beziehung, RLS nach Schreibrecht)\nCALCULATE ( [Menge Ist/LE VJ], TREATAS ( VALUES ( Dim_KeyAccount_Eingabe[KeyAccountID] ), Dim_KeyAccount[KeyAccountID] ) )', '#,0'),
 ('Umsatz Ist/LE VJ (Eingabe)', '-- für Sheets mit Dim_KeyAccount_Eingabe in den Zeilen (keine Beziehung, RLS nach Schreibrecht)\nCALCULATE ( [Umsatz Ist/LE VJ], TREATAS ( VALUES ( Dim_KeyAccount_Eingabe[KeyAccountID] ), Dim_KeyAccount[KeyAccountID] ) )', '#,0'),
 ('Budget Menge (Eingabe)', '-- für Sheets mit Dim_KeyAccount_Eingabe in den Zeilen (keine Beziehung, RLS nach Schreibrecht)\nCALCULATE ( [Budget Menge], TREATAS ( VALUES ( Dim_KeyAccount_Eingabe[KeyAccountID] ), Dim_KeyAccount[KeyAccountID] ) )', '#,0'),
 ('Budget Umsatz (Eingabe)', '-- für Sheets mit Dim_KeyAccount_Eingabe in den Zeilen (keine Beziehung, RLS nach Schreibrecht)\nCALCULATE ( [Budget Umsatz], TREATAS ( VALUES ( Dim_KeyAccount_Eingabe[KeyAccountID] ), Dim_KeyAccount[KeyAccountID] ) )', '#,0'),
 ('Preis Ist/LE VJ (Eingabe)', 'DIVIDE ( [Umsatz Ist/LE VJ (Eingabe)], [Menge Ist/LE VJ (Eingabe)] )', '#,0.00'),
 ('Budget Menge Land (Eingabe)', '-- Landessumme aller Key Accounts (innerhalb der Lese-RLS), unabhängig von den Zeilen des Eingabe-Sheets\nCALCULATE ( [Budget Menge], REMOVEFILTERS ( Dim_KeyAccount ), TREATAS ( VALUES ( Dim_KeyAccount_Eingabe[Land] ), Dim_KeyAccount[Land] ) )', '#,0'),
 ('Budget Umsatz Land (Eingabe)', 'CALCULATE ( [Budget Umsatz], REMOVEFILTERS ( Dim_KeyAccount ), TREATAS ( VALUES ( Dim_KeyAccount_Eingabe[Land] ), Dim_KeyAccount[Land] ) )', '#,0'),
 ('Anteil am Land % (Eingabe)', 'DIVIDE ( [Budget Umsatz (Eingabe)], [Budget Umsatz Land (Eingabe)] )', '0.0 %'),
 ('GuV Betrag VJ', 'VAR _vj = MAX ( Dim_Kalender[Jahr] ) - 1\nVAR _monate = VALUES ( Dim_Kalender[Monat] )\nRETURN CALCULATE ( [GuV Betrag Ist], REMOVEFILTERS ( Dim_Kalender ), Dim_Kalender[Jahr] = _vj, _monate )', '#,0.00'),
 ('GuV Abw. VJ', '[GuV Betrag Ist] - [GuV Betrag VJ]', '#,0.00;-#,0.00;0'),
 ('GuV Abw. VJ %', 'DIVIDE ( [GuV Betrag Ist] - [GuV Betrag VJ], ABS ( [GuV Betrag VJ] ) )', '0.0 %;-0.0 %;0.0 %'),
 ("Anzahl Kommentare", "COUNTROWS ( Fact_Kommentare )", "#,0"),
 ('Kommentare', '-- alle Kommentare im aktuellen Kontext (GuV-Zeile × Periode), chronologisch, für die Anzeige neben den Zahlen\nCONCATENATEX (\n    Fact_Kommentare,\n    Fact_Kommentare[Bearbeiter] & ": " & Fact_Kommentare[Kommentar],\n    UNICHAR ( 10 ),\n    Fact_Kommentare[Zeitstempel], ASC\n)', None),
 ('Kommentar vorhanden', 'IF ( [Anzahl Kommentare] > 0, "●", "" )', None),
 ("Kommentierbar", "IF ( SELECTEDVALUE ( Dim_GuV[Kommentierbar] ) = TRUE (), \"ja\", \"gesperrt\" )", None),
]
out = ["table Kennzahlen", f"\tlineageTag: {g()}", ""]
for n, expr, f in measures:
    lines = expr.split("\n")
    if len(lines) == 1: out.append(f"\tmeasure '{n}' = {expr}")
    else: out += [f"\tmeasure '{n}' =", *("\t\t\t" + l for l in lines)]
    if f: out.append(f"\t\tformatString: {f}")
    out += [f"\t\tlineageTag: {g()}", ""]
out += ["\tcolumn Platzhalter", "\t\tdataType: string", "\t\tisHidden", f"\t\tlineageTag: {g()}", "\t\tsummarizeBy: none", "\t\tsourceColumn: [Platzhalter]", "",
        "\tpartition Kennzahlen = calculated", "\t\tmode: import", '\t\tsource = ROW ( "Platzhalter", BLANK () )', ""]
w(os.path.join(DEF, "tables", "Kennzahlen.tmdl"), "\n".join(out))

# ---- Beziehungen
rels = [
 ("Fact_Absatz_Ist","Periode","Dim_Kalender","Periode"),("Fact_Absatz_Ist","KeyAccountID","Dim_KeyAccount","KeyAccountID"),("Fact_Absatz_Ist","ProduktID","Dim_Produkt","ProduktID"),
 ("Fact_Gemeinkosten_Ist","Periode","Dim_Kalender","Periode"),("Fact_Gemeinkosten_Ist","KostenstelleID","Dim_Kostenstelle","KostenstelleID"),("Fact_Gemeinkosten_Ist","KostenartID","Dim_Kostenart","KostenartID"),
 ("Fact_SonstigeErtraege_Ist","Periode","Dim_Kalender","Periode"),("Fact_SonstigeErtraege_Ist","GuVZeileID","Dim_GuV","GuVZeileID"),
 ("Fact_Budget_Absatz","Periode","Dim_Kalender","Periode"),("Fact_Budget_Absatz","Szenario","Dim_Szenario","Szenario"),("Fact_Budget_Absatz","Version","Dim_Version","Version"),
 ("Fact_Budget_Absatz","KeyAccountID","Dim_KeyAccount","KeyAccountID"),("Fact_Budget_Absatz","ProduktID","Dim_Produkt","ProduktID"),
 ("Fact_Budget_Gemeinkosten","Periode","Dim_Kalender","Periode"),("Fact_Budget_Gemeinkosten","Szenario","Dim_Szenario","Szenario"),("Fact_Budget_Gemeinkosten","Version","Dim_Version","Version"),
 ("Fact_Budget_Gemeinkosten","KostenstelleID","Dim_Kostenstelle","KostenstelleID"),("Fact_Budget_Gemeinkosten","KostenartID","Dim_Kostenart","KostenartID"),
 ("Fact_Forecast_Absatz","Periode","Dim_Kalender","Periode"),("Fact_Forecast_Absatz","ForecastStand","Dim_ForecastStand","ForecastStand"),
 ("Fact_Forecast_Absatz","KeyAccountID","Dim_KeyAccount","KeyAccountID"),("Fact_Forecast_Absatz","ProduktID","Dim_Produkt","ProduktID"),
 ("Fact_Kommentare","Periode","Dim_Kalender","Periode"),("Fact_Kommentare","GuVZeileID","Dim_GuV","GuVZeileID"),
]
out = []
for ft, fc, tt, tc in rels: out += [f"relationship {g()}", f"\tfromColumn: {ft}.{fc}", f"\ttoColumn: {tt}.{tc}", ""]
w(os.path.join(DEF, "relationships.tmdl"), "\n".join(out))

# ---- Parameter, Modell, Datenbank
w(os.path.join(DEF, "expressions.tmdl"), "\n".join([
 f'expression Ordner = "{CSV_DIR}" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]',
 f"\tlineageTag: {g()}", "", "\tannotation PBI_ResultType = Text", ""]))
order = json.dumps(["Ordner"] + list(tables))
w(os.path.join(DEF, "model.tmdl"), "\n".join([
 "model Model", "\tculture: de-DE", "\tdefaultPowerBIDataSourceVersion: powerBI_V3", "\tsourceQueryCulture: de-DE", "\tdataAccessOptions",
 "\t\tlegacyRedirects", "\t\treturnErrorValuesAsNull", "", "annotation __PBI_TimeIntelligenceEnabled = 0", "",
 f"annotation PBI_QueryOrder = {order}", ""] + [f"ref table {t}" for t in list(tables) + ["Kennzahlen"]] + ["", "ref role Vertrieb", "", "ref cultureInfo de-DE", ""]))
os.makedirs(os.path.join(DEF, "cultures"), exist_ok=True)
w(os.path.join(DEF, "cultures", "de-DE.tmdl"), "cultureInfo de-DE\n\n\tlinguisticMetadata =\n\t\t\t{\"Version\":\"1.0.0\",\"Language\":\"de-DE\"}\n\t\tcontentType: json\n")
os.makedirs(os.path.join(DEF, "roles"), exist_ok=True)
w(os.path.join(DEF, "roles", "Vertrieb.tmdl"), """role Vertrieb
	modelPermission: read

	tablePermission Dim_KeyAccount =
			-- Lesen: Key Accounts, für die der angemeldete Nutzer ein Leserecht im Planungsbereich Vertrieb hat
			Dim_KeyAccount[KeyAccountID]
			    IN SELECTCOLUMNS (
			        FILTER (
			            ALL ( Berechtigung_KeyAccount ),
			            Berechtigung_KeyAccount[Benutzer] = USERPRINCIPALNAME ()
			                && Berechtigung_KeyAccount[Planungsbereich] = "Vertrieb"
			                && Berechtigung_KeyAccount[Recht] = "Lesen"
			        ),
			        "k", Berechtigung_KeyAccount[KeyAccountID]
			    )

	tablePermission Dim_KeyAccount_Eingabe =
			-- Schreiben: Key Accounts, für die der angemeldete Nutzer ein Schreibrecht im Planungsbereich Vertrieb hat (Zeilen des Eingabe-Sheets)
			Dim_KeyAccount_Eingabe[KeyAccountID]
			    IN SELECTCOLUMNS (
			        FILTER (
			            ALL ( Berechtigung_KeyAccount ),
			            Berechtigung_KeyAccount[Benutzer] = USERPRINCIPALNAME ()
			                && Berechtigung_KeyAccount[Planungsbereich] = "Vertrieb"
			                && Berechtigung_KeyAccount[Recht] = "Schreiben"
			        ),
			        "k", Berechtigung_KeyAccount[KeyAccountID]
			    )

	annotation PBI_Id = 0d48b20b52d64c70a9a294064c4b0ea3
""")
w(os.path.join(DEF, "database.tmdl"), "database\n\tcompatibilityLevel: 1601\n")
w(os.path.join(SM, "definition.pbism"), json.dumps({"version":"4.0","settings":{}}, indent=2))
w(os.path.join(SM, ".platform"), json.dumps({"$schema":"https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
   "metadata":{"type":"SemanticModel","displayName":NAME},"config":{"version":"2.0","logicalId":g()}}, indent=2))

# ---- Leerer Bericht + Projektdatei
w(os.path.join(RP, "definition.pbir"), json.dumps({"version":"1.0","datasetReference":{"byPath":{"path":"../" + NAME + ".SemanticModel"}}}, indent=2))
w(os.path.join(RP, "report.json"), json.dumps({"config":json.dumps({"version":"5.43","themeCollection":{"baseTheme":{"name":"CY24SU10","version":"5.59","type":2}}}),
   "layoutOptimization":0,"sections":[{"name":"Seite1","displayName":"Seite 1","displayOption":1,"filters":"[]","height":720,"width":1280,"config":"{}","visualContainers":[]}]}, indent=2))
w(os.path.join(RP, ".platform"), json.dumps({"$schema":"https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
   "metadata":{"type":"Report","displayName":NAME},"config":{"version":"2.0","logicalId":g()}}, indent=2))
w(os.path.join(ROOT, NAME + ".pbip"), json.dumps({"version":"1.0","artifacts":[{"report":{"path":NAME + ".Report"}}],"settings":{"enableAutoRecovery":True}}, indent=2))
w(os.path.join(ROOT, ".gitignore"), "**/.pbi/localSettings.json\n**/.pbi/cache.abf\n")
print("fertig:", ROOT)
