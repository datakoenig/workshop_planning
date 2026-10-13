# Erzeugt T-SQL-Skripte für die Fabric SQL Database (Writeback-Ziel): Referenztabellen + View Name -> ID
import os, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "SQL")
def lit(v): return "N'" + str(v).replace("'", "''") + "'"
def inserts(table, df):
    cols = ", ".join(f"[{c}]" for c in df.columns)
    rows = ",\n".join("    (" + ", ".join(lit(v) if isinstance(v, str) else str(v) for v in r) + ")" for r in df.itertuples(index=False))
    return f"INSERT INTO {table} ({cols}) VALUES\n{rows};\n"

ka = pd.read_csv(os.path.join(HERE, "Dim_KeyAccount.csv")); pr = pd.read_csv(os.path.join(HERE, "Dim_Produkt.csv"))
s1 = f"""-- 01_ref_stammdaten.sql
-- Referenztabellen für die Übersetzung der Writeback-Beschriftungen in IDs.
-- Inhalt identisch mit Dim_KeyAccount.csv / Dim_Produkt.csv des Semantikmodells.
IF SCHEMA_ID('ref') IS NULL EXEC('CREATE SCHEMA ref');
IF SCHEMA_ID('planung') IS NULL EXEC('CREATE SCHEMA planung');
GO
DROP TABLE IF EXISTS ref.Dim_KeyAccount;
CREATE TABLE ref.Dim_KeyAccount (
    KeyAccountID NVARCHAR(10)  NOT NULL PRIMARY KEY,
    KeyAccount   NVARCHAR(100) NOT NULL UNIQUE,
    Region       NVARCHAR(50)  NOT NULL,
    Land         NVARCHAR(50)  NOT NULL
);
DROP TABLE IF EXISTS ref.Dim_Produkt;
CREATE TABLE ref.Dim_Produkt (
    ProduktID     NVARCHAR(10)  NOT NULL PRIMARY KEY,
    Produkt       NVARCHAR(100) NOT NULL UNIQUE,
    Produktgruppe NVARCHAR(50)  NOT NULL,
    Sparte        NVARCHAR(50)  NOT NULL
);
GO
{inserts("ref.Dim_KeyAccount", ka)}
{inserts("ref.Dim_Produkt", pr)}
GO
"""
s2 = """-- 02_plan_view.sql
-- View über die Writeback-Tabelle des Planning Sheets (Typ Wide): Beschriftungen -> IDs.
-- Spaltennamen der Writeback-Tabelle nach dem ersten Writeback prüfen und hier anpassen
-- (Fabric Plan benennt die Spalten nach den Feldern im Sheet; Szenario-/Versionsspalte ggf. ergänzen).
CREATE OR ALTER VIEW planung.v_Absatz_Plan AS
SELECT
    wb.[Periode]                AS Periode,
    ka.KeyAccountID,
    pr.ProduktID,
    wb.[Scenario]               AS Szenario,          -- Spaltenname prüfen
    CAST(wb.[Menge Plan]  AS INT)           AS Menge,
    CAST(wb.[Preis Plan]  AS DECIMAL(18,2)) AS Preis,
    CAST(wb.[Umsatz Plan] AS DECIMAL(18,2)) AS Umsatz
FROM planung.Absatz_Plan AS wb
JOIN ref.Dim_KeyAccount AS ka ON ka.KeyAccount = wb.[KeyAccount]
JOIN ref.Dim_Produkt    AS pr ON pr.Produkt    = wb.[Produkt];
GO

-- Kontrolle: Beschriftungen, die keiner ID zugeordnet werden konnten (müssen 0 Zeilen sein)
-- SELECT DISTINCT wb.[KeyAccount], wb.[Produkt]
-- FROM planung.Absatz_Plan wb
-- LEFT JOIN ref.Dim_KeyAccount ka ON ka.KeyAccount = wb.[KeyAccount]
-- LEFT JOIN ref.Dim_Produkt    pr ON pr.Produkt    = wb.[Produkt]
-- WHERE ka.KeyAccountID IS NULL OR pr.ProduktID IS NULL;
"""
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, "01_ref_stammdaten.sql"), "w", encoding="utf-8-sig", newline="\r\n").write(s1)
open(os.path.join(OUT, "02_plan_view.sql"), "w", encoding="utf-8-sig", newline="\r\n").write(s2)
s3 = """-- 03_berechtigungen.sql  (Block 6, Variante 1)
-- Voraussetzung: 01_ref_stammdaten.sql (ref.Dim_KeyAccount, Schemas ref/planung)
-- Lookup-Tabellen für die Dropdowns der Power Table, Berechtigungstabelle, Werte-View für den abhängigen Dropdown.

-- Lookups -------------------------------------------------------------------
DROP TABLE IF EXISTS planung.Berechtigungen;
DROP TABLE IF EXISTS ref.Benutzer;
DROP TABLE IF EXISTS ref.Planungsbereich;
DROP TABLE IF EXISTS ref.Recht;
DROP TABLE IF EXISTS ref.Ebene;
GO
CREATE TABLE ref.Benutzer (
    Benutzer NVARCHAR(100) NOT NULL PRIMARY KEY,   -- UPN / E-Mail, wie USERPRINCIPALNAME() im Modell
    Anzeigename NVARCHAR(100) NOT NULL,
    Rolle NVARCHAR(30) NOT NULL CHECK (Rolle IN (N'Administrator', N'Manager', N'Planer Vertrieb', N'Planer Einkauf', N'Planer Personal')),
    Land NVARCHAR(50) NULL                         -- Heimatland des Managers (Zeilensicherheit der Power Table)
);
CREATE TABLE ref.Planungsbereich (Planungsbereich NVARCHAR(30) NOT NULL PRIMARY KEY, Sortierung INT NOT NULL);
CREATE TABLE ref.Recht           (Recht           NVARCHAR(30) NOT NULL PRIMARY KEY, Sortierung INT NOT NULL);
CREATE TABLE ref.Ebene           (Ebene           NVARCHAR(30) NOT NULL PRIMARY KEY, Sortierung INT NOT NULL);
GO
INSERT INTO ref.Planungsbereich VALUES (N'Vertrieb', 1), (N'Material', 2), (N'Personal', 3);
INSERT INTO ref.Recht           VALUES (N'Lesen', 1), (N'Schreiben', 2);
INSERT INTO ref.Ebene           VALUES (N'Gesamt', 1), (N'Land', 2), (N'Region', 3), (N'KeyAccount', 4);
INSERT INTO ref.Benutzer VALUES
    (N'admin@demo.local',          N'Admin Demo',        N'Administrator',   NULL),
    (N'manager.de@demo.local',     N'Manager DE',        N'Manager',         N'Deutschland'),
    (N'manager.ch@demo.local',     N'Manager CH',        N'Manager',         N'Schweiz'),
    (N'vertrieb.nord@demo.local',  N'Vertrieb Nord',     N'Planer Vertrieb', N'Deutschland'),
    (N'vertrieb.west@demo.local',  N'Vertrieb West',     N'Planer Vertrieb', N'Deutschland'),
    (N'vertrieb.ka03@demo.local',  N'Betreuer KA03',     N'Planer Vertrieb', N'Deutschland'),
    (N'vertrieb.at@demo.local',    N'Vertrieb AT',       N'Planer Vertrieb', N'Österreich'),
    (N'einkauf@demo.local',        N'Einkaufsplanung',   N'Planer Einkauf',  NULL),
    (N'hr@demo.local',             N'Personalplanung',   N'Planer Personal', NULL),
    (N'Artur@biordie.com',         N'Artur König',       N'Administrator',   NULL);
GO

-- Werte-View für den abhängigen Dropdown (Ebene -> Wert) ----------------------
CREATE OR ALTER VIEW ref.v_Berechtigungswert AS
SELECT N'Gesamt' AS Ebene, N'*' AS Wert, N'Alle' AS Bezeichnung, NULL AS Land
UNION ALL SELECT DISTINCT N'Land',       Land,         Land,       Land FROM ref.Dim_KeyAccount
UNION ALL SELECT DISTINCT N'Region',     Land + N' / ' + Region, Region, Land FROM ref.Dim_KeyAccount   -- Region ist nur mit Land eindeutig (West, Ost)
UNION ALL SELECT          N'KeyAccount', KeyAccountID, KeyAccount, Land FROM ref.Dim_KeyAccount;
GO

-- Berechtigungstabelle: eine Zeile je Recht ------------------------------------
CREATE TABLE planung.Berechtigungen (
    BerechtigungID   INT IDENTITY(1,1) PRIMARY KEY,
    Benutzer         NVARCHAR(100) NOT NULL REFERENCES ref.Benutzer (Benutzer),
    Planungsbereich  NVARCHAR(30)  NOT NULL REFERENCES ref.Planungsbereich (Planungsbereich),
    Recht            NVARCHAR(30)  NOT NULL REFERENCES ref.Recht (Recht),
    Ebene            NVARCHAR(30)  NOT NULL REFERENCES ref.Ebene (Ebene),
    Wert             NVARCHAR(100) NOT NULL,          -- Wert aus ref.v_Berechtigungswert (Land, 'Land / Region' oder KeyAccountID, '*' bei Gesamt)
    GueltigVon       DATE          NOT NULL DEFAULT CAST(SYSUTCDATETIME() AS DATE),
    GueltigBis       DATE          NULL,
    Aktiv            BIT           NOT NULL DEFAULT 1,
    GeaendertVon     NVARCHAR(100) NOT NULL DEFAULT SUSER_SNAME(),
    GeaendertAm      DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT UQ_Berechtigung UNIQUE (Benutzer, Planungsbereich, Recht, Ebene, Wert)
);
GO
-- Audit-Spalten bei Änderung nachziehen (Power Table schreibt per UPDATE)
CREATE OR ALTER TRIGGER planung.trg_Berechtigungen_Audit ON planung.Berechtigungen AFTER UPDATE AS
BEGIN
    SET NOCOUNT ON;
    UPDATE b SET GeaendertVon = SUSER_SNAME(), GeaendertAm = SYSUTCDATETIME()
    FROM planung.Berechtigungen b JOIN inserted i ON i.BerechtigungID = b.BerechtigungID;
END;
GO

-- Beispielzeilen: die beiden Use Cases der Agenda ------------------------------
INSERT INTO planung.Berechtigungen (Benutzer, Planungsbereich, Recht, Ebene, Wert) VALUES
    -- Einkaufsplaner: Vertriebsplanung sehen, nur Material/Personal eingeben
    (N'einkauf@demo.local',       N'Vertrieb', N'Lesen',     N'Gesamt',     N'*'),
    (N'einkauf@demo.local',       N'Material', N'Schreiben', N'Gesamt',     N'*'),
    (N'hr@demo.local',            N'Vertrieb', N'Lesen',     N'Gesamt',     N'*'),
    (N'hr@demo.local',            N'Personal', N'Schreiben', N'Gesamt',     N'*'),
    -- Vertrieb: Land lesen (RLS), eigene Region / eigenen Key Account schreiben
    (N'vertrieb.nord@demo.local', N'Vertrieb', N'Lesen',     N'Land',       N'Deutschland'),
    (N'vertrieb.nord@demo.local', N'Vertrieb', N'Schreiben', N'Region',     N'Deutschland / Nord'),
    (N'vertrieb.west@demo.local', N'Vertrieb', N'Lesen',     N'Land',       N'Deutschland'),
    (N'vertrieb.west@demo.local', N'Vertrieb', N'Schreiben', N'Region',     N'Deutschland / West'),
    (N'vertrieb.ka03@demo.local', N'Vertrieb', N'Lesen',     N'Land',       N'Deutschland'),
    (N'vertrieb.ka03@demo.local', N'Vertrieb', N'Schreiben', N'KeyAccount', N'KA03'),
    (N'vertrieb.at@demo.local',   N'Vertrieb', N'Lesen',     N'Land',       N'Österreich'),
    (N'vertrieb.at@demo.local',   N'Vertrieb', N'Schreiben', N'Region',     N'Österreich / Ost'),
    -- Manager: alles im eigenen Land lesen und schreiben
    (N'manager.de@demo.local',    N'Vertrieb', N'Lesen',     N'Land',       N'Deutschland'),
    (N'manager.de@demo.local',    N'Vertrieb', N'Schreiben', N'Land',       N'Deutschland'),
    (N'manager.ch@demo.local',    N'Vertrieb', N'Lesen',     N'Land',       N'Schweiz'),
    (N'manager.ch@demo.local',    N'Vertrieb', N'Schreiben', N'Land',       N'Schweiz'),
    -- Referent / Testkonto
    (N'Artur@biordie.com',        N'Vertrieb', N'Lesen',     N'Gesamt',     N'*'),
    (N'Artur@biordie.com',        N'Vertrieb', N'Schreiben', N'Region',     N'Deutschland / Nord');
GO

-- Aufgelöste Sicht: je Benutzer und Key Account das effektive Recht -------------
-- (Quelle für RLS im Semantikmodell und für die Zellsperre im Planning Sheet)
CREATE OR ALTER VIEW planung.v_Berechtigung_KeyAccount AS
SELECT DISTINCT b.Benutzer, b.Planungsbereich, b.Recht, ka.KeyAccountID, ka.KeyAccount, ka.Region, ka.Land
FROM planung.Berechtigungen b
JOIN ref.Dim_KeyAccount ka
  ON (b.Ebene = N'Gesamt')
  OR (b.Ebene = N'Land'       AND ka.Land = b.Wert)
  OR (b.Ebene = N'Region'     AND ka.Land + N' / ' + ka.Region = b.Wert)
  OR (b.Ebene = N'KeyAccount' AND ka.KeyAccountID = b.Wert)
WHERE b.Aktiv = 1
  AND b.GueltigVon <= CAST(SYSUTCDATETIME() AS DATE)
  AND (b.GueltigBis IS NULL OR b.GueltigBis >= CAST(SYSUTCDATETIME() AS DATE));
GO
"""
open(os.path.join(OUT, "03_berechtigungen.sql"), "w", encoding="utf-8-sig", newline="\r\n").write(s3)

guv = pd.read_csv(os.path.join(HERE, "Dim_GuV.csv")).fillna("")
kom = pd.read_csv(os.path.join(HERE, "Fact_Kommentare.csv"))
guv_rows = ",\n".join(f"    ({lit(r.GuVZeileID)}, {lit(r.Bezeichnung)}, {lit(r.ParentID) if r.ParentID else 'NULL'}, {r.Sortierung}, {lit(r.Typ)}, {1 if r.Kommentierbar else 0})" for r in guv.itertuples())
kom_rows = ",\n".join(f"    ({lit(r.GuVZeileID)}, {lit(r.Periode)}, {lit(r.Bearbeiter)}, {lit(r.Zeitstempel)}, {lit(r.Kommentar)})" for r in kom.itertuples())
s4 = f"""-- 04_kommentare.sql  (Block 8)
-- Kommentare als Datensätze: Erfassung per Power Table (Formular), Anzeige im Modell über Fact_Kommentare.
-- Voraussetzung: 01_ref_stammdaten.sql (Schemas ref/planung)

DROP TABLE IF EXISTS planung.Kommentare;
DROP TABLE IF EXISTS ref.Dim_GuV;
GO
CREATE TABLE ref.Dim_GuV (
    GuVZeileID    NVARCHAR(10)  NOT NULL PRIMARY KEY,
    Bezeichnung   NVARCHAR(100) NOT NULL UNIQUE,
    ParentID      NVARCHAR(10)  NULL,
    Sortierung    INT           NOT NULL,
    Typ           NVARCHAR(20)  NOT NULL,          -- Blatt / Summe / Berechnet
    Kommentierbar BIT           NOT NULL           -- nur Blattzeilen
);
GO
INSERT INTO ref.Dim_GuV (GuVZeileID, Bezeichnung, ParentID, Sortierung, Typ, Kommentierbar) VALUES
{guv_rows};
GO
-- Lookup für das Formular: nur kommentierbare Zeilen, in GuV-Reihenfolge
CREATE OR ALTER VIEW ref.v_GuVZeile_Kommentierbar AS
SELECT GuVZeileID, Bezeichnung, Sortierung FROM ref.Dim_GuV WHERE Kommentierbar = 1;
GO
CREATE TABLE planung.Kommentare (
    KommentarID  INT IDENTITY(1,1) PRIMARY KEY,
    GuVZeileID   NVARCHAR(10)   NOT NULL REFERENCES ref.Dim_GuV (GuVZeileID),
    Periode      NVARCHAR(7)    NOT NULL,          -- JJJJ-MM, Schlüssel von Dim_Kalender
    Bearbeiter   NVARCHAR(100)  NOT NULL DEFAULT SUSER_SNAME(),
    Zeitstempel  DATETIME2(0)   NOT NULL DEFAULT SYSUTCDATETIME(),
    Kommentar    NVARCHAR(1000) NOT NULL,
    CONSTRAINT CK_Kommentar_Periode CHECK (Periode LIKE '[12][0-9][0-9][0-9]-[01][0-9]')
);
GO
-- Summenzeilen auch auf Datenbankebene sperren (falls das Formular den Lookup nicht filtert)
CREATE OR ALTER TRIGGER planung.trg_Kommentare_NurBlatt ON planung.Kommentare AFTER INSERT, UPDATE AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (SELECT 1 FROM inserted i JOIN ref.Dim_GuV g ON g.GuVZeileID = i.GuVZeileID WHERE g.Kommentierbar = 0)
    BEGIN
        RAISERROR (N'Kommentare sind nur auf Blattzeilen der GuV zulässig.', 16, 1);
        ROLLBACK TRANSACTION;
    END
END;
GO
INSERT INTO planung.Kommentare (GuVZeileID, Periode, Bearbeiter, Zeitstempel, Kommentar) VALUES
{kom_rows};
GO
-- Sicht fürs Semantikmodell (= Fact_Kommentare)
CREATE OR ALTER VIEW planung.v_Kommentare AS
SELECT KommentarID, GuVZeileID, Periode, Bearbeiter, Zeitstempel, Kommentar FROM planung.Kommentare;
GO
"""
open(os.path.join(OUT, "04_kommentare.sql"), "w", encoding="utf-8-sig", newline="\r\n").write(s4)
print("fertig")
