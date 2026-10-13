# Erzeugt die Berichtsseiten (PBIR-Format) für das Power-BI-Projekt. Nach generate_semantikmodell.py ausführen.
import os, json, shutil, uuid
HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "Workshop Fabric IQ Plan"
RP = os.path.join(os.path.dirname(HERE), "Semantikmodell", NAME + ".Report")
DEF = os.path.join(RP, "definition")
if os.path.exists(DEF): shutil.rmtree(DEF)
for f in ["report.json"]:
    p = os.path.join(RP, f)
    if os.path.exists(p): os.remove(p)
os.makedirs(os.path.join(DEF, "pages"))
SCH = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/"
def w(path, obj): open(path, "w", encoding="utf-8", newline="\n").write(json.dumps(obj, indent=2, ensure_ascii=False))
nid = lambda: uuid.uuid4().hex[:20]

def col(entity, prop): return {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}
def mea(prop): return {"Measure": {"Expression": {"SourceRef": {"Entity": "Kennzahlen"}}, "Property": prop}}
def lvl(entity, hier, level, prop): return {"HierarchyLevel": {"Expression": {"Hierarchy": {"Expression": {"SourceRef": {"Entity": entity}}, "Hierarchy": hier}}, "Level": level}}
def proj(field):
    f = field.get("Column") or field.get("Measure")
    if f: ent, prop = f["Expression"]["SourceRef"]["Entity"], f["Property"]
    else:
        h = field["HierarchyLevel"]; ent = h["Expression"]["Hierarchy"]["Expression"]["SourceRef"]["Entity"]; prop = h["Level"]
        return {"field": field, "queryRef": f'{ent}.{h["Expression"]["Hierarchy"]["Hierarchy"]}.{prop}', "nativeQueryRef": prop}
    return {"field": field, "queryRef": f"{ent}.{prop}", "nativeQueryRef": prop}

def visual(vtype, x, y, wdt, hgt, roles, title=None, sort=None, extra=None):
    v = {"$schema": SCH + "visualContainer/1.0.0/schema.json", "name": nid(),
         "position": {"x": x, "y": y, "z": 0, "width": wdt, "height": hgt},
         "visual": {"visualType": vtype, "query": {"queryState": {r: {"projections": [proj(f) for f in fs]} for r, fs in roles.items()}},
                    "drillFilterOtherVisuals": True}}
    if sort: v["visual"]["query"]["sortDefinition"] = {"sort": [{"field": sort[0], "direction": sort[1]}]}
    if title: v["visual"]["visualContainerObjects"] = {"title": [{"properties": {"text": {"expr": {"Literal": {"Value": f"'{title}'"}}}, "show": {"expr": {"Literal": {"Value": "true"}}}}}]}
    if extra: v["visual"]["objects"] = extra
    return v

def page_filter(entity, prop, values, numeric=False):
    lit = [[{"Literal": {"Value": (f"{v}L" if numeric else f"'{v}'")}}] for v in values]
    return {"filters": [{"name": nid(), "field": col(entity, prop), "type": "Categorical",
            "filter": {"Version": 2, "From": [{"Name": "t", "Entity": entity, "Type": 0}],
                       "Where": [{"Condition": {"In": {"Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": prop}}], "Values": lit}}}]}}]}

K, KA, PR, GV, SZ, VE, FS = "Dim_Kalender", "Dim_KeyAccount", "Dim_Produkt", "Dim_GuV", "Dim_Szenario", "Dim_Version", "Dim_ForecastStand"
slicer_obj = {"data": [{"properties": {"mode": {"expr": {"Literal": {"Value": "'Dropdown'"}}}}}]}

pages = [
 ("Überblick", None, [
   visual("slicer", 20, 20, 240, 60, {"Values": [col(K, "Jahr")]}, extra=slicer_obj),
   visual("card", 300, 20, 300, 100, {"Values": [mea("Umsatz Ist")]}, "Umsatz Ist"),
   visual("card", 620, 20, 300, 100, {"Values": [mea("EBIT Ist")]}, "EBIT Ist"),
   visual("card", 940, 20, 300, 100, {"Values": [mea("Umsatzrendite Ist")]}, "Umsatzrendite Ist"),
   visual("lineChart", 20, 140, 800, 280, {"Category": [col(K, "Periode")], "Y": [mea("Umsatz Ist")], "Series": [col(PR, "Sparte")]}, "Umsatz je Monat und Sparte", (col(K, "Periode"), "Ascending")),
   visual("clusteredBarChart", 840, 140, 420, 280, {"Category": [col(PR, "Produktgruppe")], "Y": [mea("Umsatz Ist"), mea("Deckungsbeitrag Ist")]}, "Umsatz und DB je Produktgruppe", (mea("Umsatz Ist"), "Descending")),
   visual("tableEx", 20, 440, 800, 260, {"Values": [col(KA, "Land"), col(KA, "Region"), col(KA, "KeyAccount"), mea("Umsatz Ist"), mea("Menge Ist")]}, "Key Accounts", (mea("Umsatz Ist"), "Descending")),
   visual("clusteredColumnChart", 840, 440, 420, 260, {"Category": [col(PR, "Produktgruppe")], "Y": [mea("Umsatzrendite Ist"), mea("Ziel Umsatzrendite")]}, "Umsatzrendite vs. Ziel je Produktgruppe"),
 ]),
 ("Budget 2026", page_filter(K, "Jahr", [2026], numeric=True), [
   visual("slicer", 20, 20, 300, 60, {"Values": [col(SZ, "Szenario")]}, extra=slicer_obj),
   visual("slicer", 340, 20, 300, 60, {"Values": [col(VE, "Version")]}, extra=slicer_obj),
   visual("card", 660, 20, 290, 100, {"Values": [mea("Budget Umsatz")]}, "Budget Umsatz (Default Basis/Konsolidiert)"),
   visual("card", 970, 20, 290, 100, {"Values": [mea("Budget Gemeinkosten")]}, "Budget Gemeinkosten"),
   visual("pivotTable", 20, 140, 620, 260, {"Rows": [col(SZ, "Szenario")], "Columns": [col(VE, "Version")], "Values": [mea("Budget Umsatz (gewählt)")]}, "Szenario × Version – Umsatz"),
   visual("lineChart", 660, 140, 600, 260, {"Category": [col(K, "Periode")], "Y": [mea("Budget Umsatz"), mea("Umsatz Ist")]}, "Budget vs. Ist je Monat", (col(K, "Periode"), "Ascending")),
   visual("pivotTable", 20, 420, 1240, 280, {"Rows": [col(PR, "Sparte"), col(PR, "Produktgruppe")], "Columns": [col(K, "MonatName")], "Values": [mea("Budget Umsatz")]}, "Budget Umsatz nach Produktgruppe und Monat"),
 ]),
 ("Forecast", page_filter(K, "Jahr", [2026], numeric=True), [
   visual("slicer", 20, 20, 300, 60, {"Values": [col(K, "Periode")]}, "Planmonat für Prognoseverlauf wählen", extra=slicer_obj),
   visual("slicer", 340, 20, 300, 60, {"Values": [col(FS, "ForecastStand")]}, extra=slicer_obj),
   visual("lineChart", 20, 100, 620, 300, {"Category": [col(FS, "ForecastStand")], "Y": [mea("Prognoseverlauf Umsatz"), mea("Budget Umsatz")]}, "Prognoseverlauf für gewählten Monat (letzter Punkt = Ist)", (col(FS, "ForecastStand"), "Ascending")),
   visual("tableEx", 660, 100, 600, 300, {"Values": [col(FS, "ForecastStand"), mea("Forecast Umsatz"), mea("Umsatz Ist"), mea("Prognosefehler %")]}, "Prognosefehler je Stand", (col(FS, "ForecastStand"), "Ascending")),
   visual("pivotTable", 20, 420, 1240, 280, {"Rows": [col(K, "Periode")], "Values": [col(K, "Status"), mea("Budget Umsatz"), mea("LE / Ist Umsatz"), mea("Abw. zu Budget"), mea("Abw. zu Budget %"), mea("Letzter Forecast für Periode")]}, "Budget – LE/Ist – Abweichung"),
 ]),
 ("GuV", None, [
   visual("slicer", 20, 20, 240, 60, {"Values": [col(K, "Jahr")]}, extra=slicer_obj),
   visual("pivotTable", 20, 100, 760, 600, {"Rows": [lvl(GV, "GuV Struktur", "Ebene1", "Ebene1"), lvl(GV, "GuV Struktur", "Ebene2", "Ebene2")], "Columns": [col(K, "Jahr")], "Values": [mea("GuV Betrag Ist")]}, "GuV nach Umsatzkostenverfahren"),
   visual("tableEx", 800, 100, 460, 300, {"Values": [col(GV, "Bezeichnung"), col(GV, "Typ"), mea("Kommentierbar")]}, "Kommentierbare Zeilen", (col(GV, "Bezeichnung"), "Ascending")),
   visual("tableEx", 800, 420, 460, 280, {"Values": [col(K, "Periode"), col(GV, "Bezeichnung"), col("Fact_Kommentare", "Bearbeiter"), col("Fact_Kommentare", "Kommentar")]}, "Kommentare"),
 ]),
 ("Berechtigungen", None, [
   visual("tableEx", 20, 20, 1240, 320, {"Values": [col("Config_Berechtigungen", c) for c in ["Benutzer", "Rolle", "Land_Lesen", "Region_Schreiben", "KeyAccount_Schreiben", "Planungsbereich"]]}, "Berechtigungstabelle (Power Table)"),
   visual("tableEx", 20, 360, 1240, 340, {"Values": [col("Config_Berechtigungsantraege", c) for c in ["AntragID", "Benutzer", "Typ", "Wert", "Begruendung", "Status", "Freigabe_durch", "Freigabe_am"]]}, "Berechtigungsanträge"),
 ]),
]

order = []
for i, (title, flt, visuals) in enumerate(pages, 1):
    pname = f"seite{i}"; order.append(pname)
    pd_ = os.path.join(DEF, "pages", pname); os.makedirs(os.path.join(pd_, "visuals"))
    page = {"$schema": SCH + "page/1.0.0/schema.json", "name": pname, "displayName": title, "displayOption": "FitToPage", "height": 720, "width": 1280}
    if flt: page["filterConfig"] = flt
    w(os.path.join(pd_, "page.json"), page)
    for v in visuals:
        vd = os.path.join(pd_, "visuals", v["name"]); os.makedirs(vd); w(os.path.join(vd, "visual.json"), v)
w(os.path.join(DEF, "pages", "pages.json"), {"$schema": SCH + "pagesMetadata/1.0.0/schema.json", "pageOrder": order, "activePageName": order[0]})
w(os.path.join(DEF, "report.json"), {"$schema": SCH + "report/1.0.0/schema.json",
   "themeCollection": {"baseTheme": {"name": "CY24SU10", "reportVersionAtImport": "5.55", "type": "SharedResources"}},
   "settings": {"useStylableVisualContainerHeader": True, "defaultFilterActionIsDataFilter": True}})
w(os.path.join(DEF, "version.json"), {"$schema": SCH + "versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
w(os.path.join(RP, "definition.pbir"), {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/1.0.0/schema.json",
   "version": "4.0", "datasetReference": {"byPath": {"path": "../" + NAME + ".SemanticModel"}}})
print("fertig:", len(pages), "Seiten")
