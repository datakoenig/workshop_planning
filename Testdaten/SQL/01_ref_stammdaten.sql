-- 01_ref_stammdaten.sql
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
INSERT INTO ref.Dim_KeyAccount ([KeyAccountID], [KeyAccount], [Region], [Land]) VALUES
    (N'KA01', N'Nordkauf GmbH', N'Nord', N'Deutschland'),
    (N'KA02', N'Hanse Mode AG', N'Nord', N'Deutschland'),
    (N'KA03', N'Rhein Retail', N'West', N'Deutschland'),
    (N'KA04', N'Ruhr Textil KG', N'West', N'Deutschland'),
    (N'KA05', N'Alpenstil GmbH', N'Süd', N'Deutschland'),
    (N'KA06', N'Isar Fashion', N'Süd', N'Deutschland'),
    (N'KA07', N'Elbe Outlet', N'Ost', N'Deutschland'),
    (N'KA08', N'Donau Trend GmbH', N'Ost', N'Österreich'),
    (N'KA09', N'Wien Accessoires', N'Ost', N'Österreich'),
    (N'KA10', N'Helvetia Mode AG', N'Zentral', N'Schweiz'),
    (N'KA11', N'Zürich Style', N'Zentral', N'Schweiz'),
    (N'KA12', N'Berner Boutique', N'West', N'Schweiz');

INSERT INTO ref.Dim_Produkt ([ProduktID], [Produkt], [Produktgruppe], [Sparte]) VALUES
    (N'P01', N'Lederhandschuhe Classic', N'Handschuhe', N'Winter-Accessoires'),
    (N'P02', N'Strickhandschuhe Wool', N'Handschuhe', N'Winter-Accessoires'),
    (N'P03', N'Touchscreen-Handschuhe', N'Handschuhe', N'Winter-Accessoires'),
    (N'P04', N'Kaschmirschal', N'Schals', N'Winter-Accessoires'),
    (N'P05', N'Wollschal Streifen', N'Schals', N'Winter-Accessoires'),
    (N'P06', N'Beanie Merino', N'Mützen', N'Winter-Accessoires'),
    (N'P07', N'Bommelmütze', N'Mützen', N'Winter-Accessoires'),
    (N'P08', N'Ledersandale Riviera', N'Sandalen', N'Sommer-Accessoires'),
    (N'P09', N'Zehentrenner Beach', N'Sandalen', N'Sommer-Accessoires'),
    (N'P10', N'Trekkingsandale', N'Sandalen', N'Sommer-Accessoires'),
    (N'P11', N'Strohhut Panama', N'Sonnenhüte', N'Sommer-Accessoires'),
    (N'P12', N'Bucket Hat', N'Sonnenhüte', N'Sommer-Accessoires'),
    (N'P13', N'Sonnenbrille Aviator', N'Sonnenbrillen', N'Sommer-Accessoires'),
    (N'P14', N'Sonnenbrille Sport', N'Sonnenbrillen', N'Sommer-Accessoires');

GO
