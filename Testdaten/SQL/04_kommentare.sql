-- 04_kommentare.sql  (Block 8)
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
    (N'G010', N'Umsatzerlöse', NULL, 10, N'Blatt', 1),
    (N'G020', N'Herstellungskosten des Umsatzes', NULL, 20, N'Summe', 0),
    (N'G021', N'Materialeinsatz (variable Kosten)', N'G020', 21, N'Blatt', 1),
    (N'G022', N'Produktionsgemeinkosten', N'G020', 22, N'Blatt', 1),
    (N'G025', N'Bruttoergebnis', NULL, 25, N'Berechnet', 0),
    (N'G030', N'Vertriebskosten', NULL, 30, N'Summe', 0),
    (N'G031', N'Personal Vertrieb', N'G030', 31, N'Blatt', 1),
    (N'G032', N'Provisionen', N'G030', 32, N'Blatt', 1),
    (N'G033', N'Distribution', N'G030', 33, N'Blatt', 1),
    (N'G034', N'Werbung', N'G030', 34, N'Blatt', 1),
    (N'G035', N'Sonstige Vertriebskosten', N'G030', 35, N'Blatt', 1),
    (N'G040', N'Verwaltungskosten', NULL, 40, N'Summe', 0),
    (N'G041', N'Personal Verwaltung', N'G040', 41, N'Blatt', 1),
    (N'G042', N'Miete und IT', N'G040', 42, N'Blatt', 1),
    (N'G043', N'Sonstige Verwaltungskosten', N'G040', 43, N'Blatt', 1),
    (N'G050', N'Sonstige betriebliche Erträge', NULL, 50, N'Blatt', 1),
    (N'G060', N'EBIT', NULL, 60, N'Berechnet', 0),
    (N'G070', N'Umsatzrendite', NULL, 70, N'Berechnet', 0);
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
    (N'G034', N'2026-07', N'marketing@demo.local', N'2026-08-05 09:12', N'Sommerkampagne Sandalen vorgezogen, Mehrkosten ca. 6 TEUR; Ausgleich im Q4 geplant.'),
    (N'G032', N'2026-07', N'controlling@demo.local', N'2026-08-05 10:40', N'Provisionen über Plan wegen Sonderaktion KA03.'),
    (N'G021', N'2026-08', N'einkauf@demo.local', N'2026-09-03 14:05', N'Lederpreise +4 % seit Juni, Nachverhandlung läuft.'),
    (N'G031', N'2026-08', N'hr@demo.local', N'2026-09-04 08:30', N'Zwei unbesetzte Stellen Vertrieb Export, Einsparung temporär.'),
    (N'G042', N'2026-09', N'it@demo.local', N'2026-10-02 11:15', N'Lizenzkosten Fabric-Kapazität erstmals enthalten.'),
    (N'G010', N'2026-09', N'vertrieb.west@demo.local', N'2026-10-02 16:48', N'Umsatz Sandalen unter Plan: Preisnachlässe bei KA03 und KA10, Menge im Plan.');
GO
-- Sicht fürs Semantikmodell (= Fact_Kommentare)
CREATE OR ALTER VIEW planung.v_Kommentare AS
SELECT KommentarID, GuVZeileID, Periode, Bearbeiter, Zeitstempel, Kommentar FROM planung.Kommentare;
GO
