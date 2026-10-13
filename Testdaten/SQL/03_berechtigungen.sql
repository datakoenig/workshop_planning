-- 03_berechtigungen.sql  (Block 6, Variante 1)
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
