-- 02_plan_view.sql
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
