# Erzeugt die Demo-Daten für den Workshop "Fabric IQ Plan"
# Ausführen: python generate_testdaten.py  (schreibt CSV-Dateien in denselben Ordner)
import os, numpy as np, pandas as pd
rng = np.random.default_rng(42)
OUT = os.path.dirname(os.path.abspath(__file__))
def save(df, name): df.to_csv(os.path.join(OUT, name + ".csv"), index=False, encoding="utf-8-sig")

# ---------------- Kalender ----------------
monate = pd.period_range("2024-01", "2027-12", freq="M")   # 2027 = Planjahr für Block 4
kal = pd.DataFrame({
    "Periode": [str(p) for p in monate],
    "Datum": [p.to_timestamp().strftime("%Y-%m-%d") for p in monate],
    "Monatsbeginn": [p.to_timestamp().strftime("%Y-%m-%d") for p in monate],
    "Jahr": [p.year for p in monate], "Monat": [p.month for p in monate],
    "MonatName": [p.to_timestamp().strftime("%B") for p in monate],
    "Quartal": [f"Q{(p.month-1)//3+1}" for p in monate],
})
kal["MonatName"] = kal["Monat"].map({1:"Januar",2:"Februar",3:"März",4:"April",5:"Mai",6:"Juni",7:"Juli",8:"August",9:"September",10:"Oktober",11:"November",12:"Dezember"})
kal["Status"] = np.where(kal["Periode"] <= "2026-09", "abgeschlossen", "offen")
save(kal, "Dim_Kalender")

# ---------------- Key Accounts ----------------
ka = pd.DataFrame([
    ("KA01","Nordkauf GmbH","Nord","Deutschland",1.4),
    ("KA02","Hanse Mode AG","Nord","Deutschland",0.9),
    ("KA03","Rhein Retail","West","Deutschland",1.6),
    ("KA04","Ruhr Textil KG","West","Deutschland",0.7),
    ("KA05","Alpenstil GmbH","Süd","Deutschland",1.2),
    ("KA06","Isar Fashion","Süd","Deutschland",1.0),
    ("KA07","Elbe Outlet","Ost","Deutschland",0.6),
    ("KA08","Donau Trend GmbH","Ost","Österreich",0.8),
    ("KA09","Wien Accessoires","Ost","Österreich",0.5),
    ("KA10","Helvetia Mode AG","Zentral","Schweiz",1.1),
    ("KA11","Zürich Style","Zentral","Schweiz",0.7),
    ("KA12","Berner Boutique","West","Schweiz",0.4),
], columns=["KeyAccountID","KeyAccount","Region","Land","Groesse"])
save(ka.drop(columns="Groesse"), "Dim_KeyAccount")

# ---------------- Produkte ----------------
# Saisonprofil je Produktgruppe (Index Monat 1..12), zusätzlich Dezember-Spitze für alle
winter = np.array([1.5,1.2,0.8,0.5,0.3,0.2,0.2,0.3,0.6,1.1,1.6,2.2])
sommer = np.array([0.3,0.3,0.6,1.0,1.5,1.8,1.7,1.4,0.9,0.5,0.4,1.0])
prod = pd.DataFrame([
    ("P01","Lederhandschuhe Classic","Handschuhe","Winter-Accessoires",49.0,21.0,"winter"),
    ("P02","Strickhandschuhe Wool","Handschuhe","Winter-Accessoires",24.0,10.0,"winter"),
    ("P03","Touchscreen-Handschuhe","Handschuhe","Winter-Accessoires",29.0,12.0,"winter"),
    ("P04","Kaschmirschal","Schals","Winter-Accessoires",89.0,42.0,"winter"),
    ("P05","Wollschal Streifen","Schals","Winter-Accessoires",39.0,16.0,"winter"),
    ("P06","Beanie Merino","Mützen","Winter-Accessoires",34.0,13.0,"winter"),
    ("P07","Bommelmütze","Mützen","Winter-Accessoires",27.0,11.0,"winter"),
    ("P08","Ledersandale Riviera","Sandalen","Sommer-Accessoires",79.0,38.0,"sommer"),
    ("P09","Zehentrenner Beach","Sandalen","Sommer-Accessoires",19.0,7.0,"sommer"),
    ("P10","Trekkingsandale","Sandalen","Sommer-Accessoires",69.0,33.0,"sommer"),
    ("P11","Strohhut Panama","Sonnenhüte","Sommer-Accessoires",45.0,18.0,"sommer"),
    ("P12","Bucket Hat","Sonnenhüte","Sommer-Accessoires",25.0,9.0,"sommer"),
    ("P13","Sonnenbrille Aviator","Sonnenbrillen","Sommer-Accessoires",59.0,22.0,"sommer"),
    ("P14","Sonnenbrille Sport","Sonnenbrillen","Sommer-Accessoires",49.0,19.0,"sommer"),
], columns=["ProduktID","Produkt","Produktgruppe","Sparte","Listenpreis","VarStueckkosten","Saison"])
save(prod.drop(columns=["Listenpreis","VarStueckkosten","Saison"]), "Dim_Produkt")

# ---------------- Ist-Absatz ----------------
def basismenge(k, p):
    return 120 * k.Groesse * (1.0 if p.Listenpreis > 40 else 1.8)

rows = []
for _, k in ka.iterrows():
    for _, p in prod.iterrows():
        profil = winter if p.Saison == "winter" else sommer
        for _, m in kal.iterrows():
            if m.Periode > "2026-09": break
            wachstum = 1.0 + 0.04 * (m.Jahr - 2024)           # 4 % p.a.
            preisfaktor = 1.0 + 0.02 * (m.Jahr - 2024)        # Preiserhöhung 2 % p.a.
            # Story für Block 9: 2026 Preisdruck bei Sandalen (-8 %) und Mengenrückgang Handschuhe (-10 %)
            if m.Jahr == 2026 and p.Produktgruppe == "Sandalen": preisfaktor *= 0.92
            if m.Jahr == 2026 and p.Produktgruppe == "Handschuhe": wachstum *= 0.90
            menge = basismenge(k, p) * profil[m.Monat-1] * wachstum * rng.normal(1.0, 0.12)
            menge = max(0, int(round(menge)))
            preis = round(p.Listenpreis * preisfaktor * rng.normal(1.0, 0.02), 2)
            rows.append((m.Periode, k.KeyAccountID, p.ProduktID, menge, preis,
                         round(menge*preis, 2), round(menge*p.VarStueckkosten*(1+0.015*(m.Jahr-2024)), 2)))
ist = pd.DataFrame(rows, columns=["Periode","KeyAccountID","ProduktID","Menge","Preis","Umsatz","VariableKosten"])
save(ist, "Fact_Absatz_Ist")

# ---------------- Kostenstellen / Kostenarten / Gemeinkosten ----------------
kst = pd.DataFrame([
    ("KST100","Vertrieb Inland","Vertrieb"),("KST110","Vertrieb Export","Vertrieb"),
    ("KST200","Marketing","Vertrieb"),("KST300","Logistik","Vertrieb"),
    ("KST400","Produktion","Herstellung"),("KST500","Einkauf","Herstellung"),
    ("KST600","Verwaltung","Verwaltung"),("KST700","IT","Verwaltung"),
], columns=["KostenstelleID","Kostenstelle","Bereich"])
save(kst, "Dim_Kostenstelle")
koa = pd.DataFrame([
    ("KOA4000","Personalkosten","Personal"),("KOA4100","Provisionen","Provision"),
    ("KOA4200","Frachten und Distribution","Distribution"),("KOA4300","Werbung","Werbung"),
    ("KOA4400","Miete","Miete"),("KOA4500","IT-Lizenzen und Hosting","IT"),
    ("KOA4600","Abschreibungen","Abschreibungen"),("KOA4700","Reisekosten","Reisekosten"),
    ("KOA4800","Sonstige Aufwendungen","Sonstige Aufwendungen"),
], columns=["KostenartID","Kostenart","GuVZuordnung"])
save(koa, "Dim_Kostenart")

# Monatliche Basisbeträge je (KST, KOA) in EUR; 0 = kommt nicht vor
basis = {
 ("KST100","KOA4000"):42000,("KST100","KOA4100"):0,("KST100","KOA4700"):4000,("KST100","KOA4800"):1500,
 ("KST110","KOA4000"):28000,("KST110","KOA4700"):6000,("KST110","KOA4800"):1200,
 ("KST200","KOA4000"):18000,("KST200","KOA4300"):25000,("KST200","KOA4800"):2000,
 ("KST300","KOA4000"):22000,("KST300","KOA4200"):0,("KST300","KOA4400"):9000,
 ("KST400","KOA4000"):55000,("KST400","KOA4400"):14000,("KST400","KOA4600"):11000,("KST400","KOA4800"):3000,
 ("KST500","KOA4000"):16000,("KST500","KOA4700"):1500,
 ("KST600","KOA4000"):30000,("KST600","KOA4400"):7000,("KST600","KOA4800"):2500,
 ("KST700","KOA4000"):20000,("KST700","KOA4500"):9000,("KST700","KOA4600"):4000,
}
umsatz_monat = ist.groupby("Periode")["Umsatz"].sum()
rows = []
for (k, a), b in basis.items():
    b = b * 1.25   # Kalibrierung Umsatzrendite ~10 %
    for _, m in kal.iterrows():
        if m.Periode > "2026-09": break
        infl = 1 + 0.03*(m.Jahr-2024)
        if a == "KOA4100": betrag = 0.03 * umsatz_monat[m.Periode]           # Provision 3 % vom Umsatz
        elif a == "KOA4200": betrag = 0.02 * umsatz_monat[m.Periode]         # Distribution 2 % vom Umsatz
        elif a in ("KOA4400","KOA4500","KOA4600"): betrag = b * infl         # fix, glatt
        else: betrag = b * infl * rng.normal(1.0, 0.05)
        if m.Jahr == 2026 and a == "KOA4300": betrag *= 1.25                 # Story: Werbung 2026 +25 %
        rows.append((m.Periode, k, a, round(betrag, 2)))
gk = pd.DataFrame(rows, columns=["Periode","KostenstelleID","KostenartID","Betrag"])
gk = gk[gk.Betrag > 0]
save(gk, "Fact_Gemeinkosten_Ist")

# ---------------- Szenarien / Versionen ----------------
save(pd.DataFrame([("Pessimistisch",1,False),("Base",2,True),("Optimistisch",3,False)],
     columns=["Szenario","Sortierung","IstDefault"]), "Dim_Szenario")
save(pd.DataFrame([("Top-Down",1,False),("Bottom-Up",2,False),("Konsolidiert",3,True)],
     columns=["Version","Sortierung","IstDefault"]), "Dim_Version")

# ---------------- Budget 2026 ----------------
ist25 = ist[ist.Periode.str.startswith("2025")].copy()
ist25["Monat"] = ist25.Periode.str[5:].astype(int)
szen_f = {"Pessimistisch":0.92,"Base":1.0,"Optimistisch":1.08}
rows = []
for (kid, pid), g in ist25.groupby(["KeyAccountID","ProduktID"]):
    jahresmenge = g.Menge.sum() * 1.05                       # Planungsannahme +5 %
    saison = g.set_index("Monat").Menge / g.Menge.sum()
    preis = round(g.Preis.mean() * 1.02, 2)
    bu_faktor = rng.normal(1.0, 0.08)                        # Bottom-Up weicht je Kunde/Produkt ab
    for sz, f in szen_f.items():
        for ver in ["Top-Down","Bottom-Up","Konsolidiert"]:
            vf = 1.0 if ver == "Top-Down" else (bu_faktor if ver == "Bottom-Up" else (1+bu_faktor)/2)
            for mo in range(1, 13):
                menge = int(round(jahresmenge * saison.get(mo, 1/12) * f * vf))
                rows.append((f"2026-{mo:02d}", sz, ver, kid, pid, menge, preis, round(menge*preis, 2)))
bud = pd.DataFrame(rows, columns=["Periode","Szenario","Version","KeyAccountID","ProduktID","Menge","Preis","Umsatz"])
save(bud, "Fact_Budget_Absatz")

gk25 = gk[gk.Periode.str.startswith("2025")]
rows = []
for (k, a), g in gk25.groupby(["KostenstelleID","KostenartID"]):
    jahr = g.Betrag.sum() * 1.03
    for sz, f in {"Pessimistisch":1.03,"Base":1.0,"Optimistisch":0.98}.items():
        for ver in ["Top-Down","Bottom-Up","Konsolidiert"]:
            vf = 1.0 if ver == "Top-Down" else (1.04 if ver == "Bottom-Up" else 1.02)
            for mo in range(1, 13):
                rows.append((f"2026-{mo:02d}", sz, ver, k, a, round(jahr/12*f*vf, 2)))
save(pd.DataFrame(rows, columns=["Periode","Szenario","Version","KostenstelleID","KostenartID","Betrag"]), "Fact_Budget_Gemeinkosten")

# ---------------- Forecast-Stände 2026 ----------------
# Stand FC 2026MM wird zu Beginn des Monats MM erstellt und umfasst MM..12.
# Der Fehler sinkt mit kürzerem Horizont (Prognosegenauigkeit steigt) – Basis ist der spätere Ist-Wert (bis 09)
# bzw. das Budget Basis/Konsolidiert für Okt–Dez.
ist26 = ist[ist.Periode.str.startswith("2026")].set_index(["Periode","KeyAccountID","ProduktID"])
bud26 = bud[(bud.Szenario=="Base")&(bud.Version=="Konsolidiert")].set_index(["Periode","KeyAccountID","ProduktID"])
rows, staende = [], []
for stand in range(1, 10):
    staende.append((f"FC 2026{stand:02d}", f"2026-{stand:02d}-01", stand))
    for mo in range(stand, 13):
        per = f"2026-{mo:02d}"
        horizont = mo - stand
        quelle = ist26 if per <= "2026-09" else bud26
        for (kid, pid), r in quelle.xs(per, level="Periode").iterrows():
            sigma = 0.04 + 0.03 * horizont                     # 4 % bei Horizont 0, +3 % je Monat
            bias = 1.0 + 0.02 * horizont * (1 if pid in ("P08","P09","P10") else 0)  # Sandalen anfangs zu optimistisch
            menge = max(0, int(round(r.Menge * bias * rng.normal(1.0, sigma))))
            preis = round(r.Preis * rng.normal(1.0, sigma/3), 2)
            rows.append((f"FC 2026{stand:02d}", per, kid, pid, menge, preis, round(menge*preis, 2)))
fc = pd.DataFrame(rows, columns=["ForecastStand","Periode","KeyAccountID","ProduktID","Menge","Preis","Umsatz"])
save(fc, "Fact_Forecast_Absatz")
save(pd.DataFrame(staende, columns=["ForecastStand","Erstellt","Sortierung"]), "Dim_ForecastStand")

# ---------------- GuV-Struktur (Umsatzkostenverfahren) ----------------
guv = pd.DataFrame([
    ("G010","Umsatzerlöse",None,10,"Blatt","Umsatz",True),
    ("G020","Herstellungskosten des Umsatzes",None,20,"Summe",None,False),
    ("G021","Materialeinsatz (variable Kosten)","G020",21,"Blatt","VariableKosten",True),
    ("G022","Produktionsgemeinkosten","G020",22,"Blatt","KST:Herstellung",True),
    ("G025","Bruttoergebnis",None,25,"Berechnet","G010 - G020",False),
    ("G030","Vertriebskosten",None,30,"Summe",None,False),
    ("G031","Personal Vertrieb","G030",31,"Blatt","KST:Vertrieb;KOA:Personal",True),
    ("G032","Provisionen","G030",32,"Blatt","KOA:Provision",True),
    ("G033","Distribution","G030",33,"Blatt","KOA:Distribution",True),
    ("G034","Werbung","G030",34,"Blatt","KOA:Werbung",True),
    ("G035","Sonstige Vertriebskosten","G030",35,"Blatt","KST:Vertrieb;KOA:Rest",True),
    ("G040","Verwaltungskosten",None,40,"Summe",None,False),
    ("G041","Personal Verwaltung","G040",41,"Blatt","KST:Verwaltung;KOA:Personal",True),
    ("G042","Miete und IT","G040",42,"Blatt","KOA:Miete;KOA:IT",True),
    ("G043","Sonstige Verwaltungskosten","G040",43,"Blatt","KST:Verwaltung;KOA:Rest",True),
    ("G050","Sonstige betriebliche Erträge",None,50,"Blatt","manuell",True),
    ("G060","EBIT",None,60,"Berechnet","G025 - G030 - G040 + G050",False),
    ("G070","Umsatzrendite",None,70,"Berechnet","G060 / G010",False),
], columns=["GuVZeileID","Bezeichnung","ParentID","Sortierung","Typ","Quelle","Kommentierbar"])
name = guv.set_index("GuVZeileID").Bezeichnung
guv["Ebene1"] = [name[r.ParentID] if r.ParentID else r.Bezeichnung for _, r in guv.iterrows()]
guv["Ebene2"] = guv.Bezeichnung
# Flache Darstellung für Intelligence Sheets: Blätter unter einem Knoten eingerückt, Summen/Ergebnisse auf Ebene 0
guv["GuV Zeile"] = ["\u2003\u2003" + r.Bezeichnung if r.ParentID else r.Bezeichnung for _, r in guv.iterrows()]
guv["Fett"] = guv.Typ.isin(["Summe", "Berechnet"])
sort = guv.set_index("GuVZeileID").Sortierung
guv["Sortierung1"] = [sort[r.ParentID] if r.ParentID else r.Sortierung for _, r in guv.iterrows()]   # Sortierung der Ebene1
guv["Sortierung2"] = guv.Sortierung
save(guv, "Dim_GuV")

# Sonstige betriebliche Erträge (kleine, unregelmäßige Beträge)
sbe = pd.DataFrame({"Periode": kal[kal.Periode<="2026-09"].Periode,
                    "GuVZeileID":"G050", "Betrag": np.round(rng.gamma(2, 1500, size=(kal.Periode<="2026-09").sum()), 2)})
save(sbe, "Fact_SonstigeErtraege_Ist")

# ---------------- Berechtigungen ----------------
# Eine Zeile je Recht (gleicher Inhalt wie SQL/03_berechtigungen.sql). Ebene/Wert: Gesamt=*, Land, "Land / Region", KeyAccountID
ber = pd.DataFrame([
    ("einkauf@demo.local",       "Vertrieb", "Lesen",     "Gesamt",     "*"),
    ("einkauf@demo.local",       "Material", "Schreiben", "Gesamt",     "*"),
    ("hr@demo.local",            "Vertrieb", "Lesen",     "Gesamt",     "*"),
    ("hr@demo.local",            "Personal", "Schreiben", "Gesamt",     "*"),
    ("vertrieb.nord@demo.local", "Vertrieb", "Lesen",     "Land",       "Deutschland"),
    ("vertrieb.nord@demo.local", "Vertrieb", "Schreiben", "Region",     "Deutschland / Nord"),
    ("vertrieb.west@demo.local", "Vertrieb", "Lesen",     "Land",       "Deutschland"),
    ("vertrieb.west@demo.local", "Vertrieb", "Schreiben", "Region",     "Deutschland / West"),
    ("vertrieb.ka03@demo.local", "Vertrieb", "Lesen",     "Land",       "Deutschland"),
    ("vertrieb.ka03@demo.local", "Vertrieb", "Schreiben", "KeyAccount", "KA03"),
    ("vertrieb.at@demo.local",   "Vertrieb", "Lesen",     "Land",       "Österreich"),
    ("vertrieb.at@demo.local",   "Vertrieb", "Schreiben", "Region",     "Österreich / Ost"),
    ("manager.de@demo.local",    "Vertrieb", "Lesen",     "Land",       "Deutschland"),
    ("manager.de@demo.local",    "Vertrieb", "Schreiben", "Land",       "Deutschland"),
    ("manager.ch@demo.local",    "Vertrieb", "Lesen",     "Land",       "Schweiz"),
    ("manager.ch@demo.local",    "Vertrieb", "Schreiben", "Land",       "Schweiz"),
    # Referent / Testkonto
    ("Artur@biordie.com",        "Vertrieb", "Lesen",     "Gesamt",     "*"),
    ("Artur@biordie.com",        "Vertrieb", "Schreiben", "Region",     "Deutschland / Nord"),
], columns=["Benutzer","Planungsbereich","Recht","Ebene","Wert"])
save(ber, "Config_Berechtigungen")
# Aufgelöst je Key Account (entspricht planung.v_Berechtigung_KeyAccount) – Quelle für RLS und Measure Schreibrecht
rows = []
for _, b in ber.iterrows():
    for _, k in ka.iterrows():
        ok = (b.Ebene == "Gesamt" or (b.Ebene == "Land" and k.Land == b.Wert)
              or (b.Ebene == "Region" and f"{k.Land} / {k.Region}" == b.Wert) or (b.Ebene == "KeyAccount" and k.KeyAccountID == b.Wert))
        if ok: rows.append((b.Benutzer, b.Planungsbereich, b.Recht, k.KeyAccountID))
save(pd.DataFrame(rows, columns=["Benutzer","Planungsbereich","Recht","KeyAccountID"]).drop_duplicates(), "Berechtigung_KeyAccount")
save(pd.DataFrame([
    (1,"vertrieb.nord@demo.local","Vertrieb","Region","Deutschland / Süd","Vertretung Kollege","beantragt","",""),
    (2,"vertrieb.west@demo.local","Vertrieb","KeyAccount","KA12","Neuer Kunde in Betreuung","freigegeben","manager.ch@demo.local","2026-09-15"),
    (3,"vertrieb.at@demo.local","Vertrieb","Region","Deutschland / Nord","","abgelehnt","manager.de@demo.local","2026-09-20"),
], columns=["AntragID","Benutzer","Planungsbereich","Ebene","Wert","Begruendung","Status","Freigabe_durch","Freigabe_am"]), "Config_Berechtigungsantraege")

# ---------------- Kommentare ----------------
save(pd.DataFrame([
    (1,"G034","2026-07","marketing@demo.local","2026-08-05 09:12","Sommerkampagne Sandalen vorgezogen, Mehrkosten ca. 6 TEUR; Ausgleich im Q4 geplant."),
    (2,"G032","2026-07","controlling@demo.local","2026-08-05 10:40","Provisionen über Plan wegen Sonderaktion KA03."),
    (3,"G021","2026-08","einkauf@demo.local","2026-09-03 14:05","Lederpreise +4 % seit Juni, Nachverhandlung läuft."),
    (4,"G031","2026-08","hr@demo.local","2026-09-04 08:30","Zwei unbesetzte Stellen Vertrieb Export, Einsparung temporär."),
    (5,"G042","2026-09","it@demo.local","2026-10-02 11:15","Lizenzkosten Fabric-Kapazität erstmals enthalten."),
    (6,"G010","2026-09","vertrieb.west@demo.local","2026-10-02 16:48","Umsatz Sandalen unter Plan: Preisnachlässe bei KA03 und KA10, Menge im Plan."),
], columns=["KommentarID","GuVZeileID","Periode","Bearbeiter","Zeitstempel","Kommentar"]), "Fact_Kommentare")

# ---------------- Treiber ----------------
save(pd.DataFrame([
    ("Absatzmenge",None,"Eingabe","Stück"),("Preis",None,"Eingabe","EUR/Stück"),("VarStueckkosten",None,"Eingabe","EUR/Stück"),
    ("Umsatz","Absatzmenge * Preis","Berechnet","EUR"),("VariableKosten","Absatzmenge * VarStueckkosten","Berechnet","EUR"),
    ("Deckungsbeitrag","Umsatz - VariableKosten","Berechnet","EUR"),("Fixkosten",None,"Eingabe","EUR"),
    ("EBIT","Deckungsbeitrag - Fixkosten","Berechnet","EUR"),("Umsatzrendite","EBIT / Umsatz","Berechnet","%"),
], columns=["Treiber","Formel","Typ","Einheit"]), "Dim_Treiber")
save(pd.DataFrame([
    ("Handschuhe",0.12),("Schals",0.14),("Mützen",0.11),("Sandalen",0.12),("Sonnenhüte",0.10),("Sonnenbrillen",0.13),("Gesamt",0.10),
], columns=["Produktgruppe","Ziel_Umsatzrendite"]), "Config_Zielwerte")

print("fertig:", {f: len(pd.read_csv(os.path.join(OUT, f+".csv"))) for f in
      ["Fact_Absatz_Ist","Fact_Gemeinkosten_Ist","Fact_Budget_Absatz","Fact_Budget_Gemeinkosten","Fact_Forecast_Absatz"]})
