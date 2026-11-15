import csv
from collections import Counter

input_csv = "/Users/giulia/Desktop/evening_dresses_pulito.csv"
output_csv = "/Users/giulia/Desktop/evening_dresses_pulito.csv"

# Dizionario geografico completo Luogo -> Stato in italiano
MAPPA_STATI = {
    # REGNO UNITO (Città, contee, quartieri londinesi, nazioni costitutive)
    "london": "Regno Unito",
    "england": "Regno Unito",
    "great britain": "Regno Unito",
    "britain": "Regno Unito",
    "uk": "Regno Unito",
    "united kingdom": "Regno Unito",
    "scotland": "Regno Unito",
    "wales": "Regno Unito",
    "glasgow": "Regno Unito",
    "edinburgh": "Regno Unito",
    "spitalfields": "Regno Unito",
    "birmingham": "Regno Unito",
    "manchester": "Regno Unito",
    "leeds": "Regno Unito",
    "liverpool": "Regno Unito",
    "nottingham": "Regno Unito",
    "nottinghamshire": "Regno Unito",
    "staffordshire": "Regno Unito",
    "surrey": "Regno Unito",
    "kent (england)": "Regno Unito",
    "kent": "Regno Unito",
    "benenden, kent": "Regno Unito",
    "cornwall": "Regno Unito",
    "exeter": "Regno Unito",
    "oxford": "Regno Unito",
    "brighton": "Regno Unito",
    "belfast": "Regno Unito",
    "salford": "Regno Unito",
    "sunderland": "Regno Unito",
    "stoke-on-trent": "Regno Unito",
    "stoke": "Regno Unito",
    "east anglia": "Regno Unito",
    "lancashire": "Regno Unito",
    "bedfordshire": "Regno Unito",
    "leicester": "Regno Unito",
    "loughborough": "Regno Unito",
    "macclesfield": "Regno Unito",
    "maidstone": "Regno Unito",
    "northampton": "Regno Unito",
    "norwich": "Regno Unito",
    "wolverhampton": "Regno Unito",
    "gateshead": "Regno Unito",
    "greenwich": "Regno Unito",
    "honiton": "Regno Unito",
    "isle of wight": "Regno Unito",
    "lacock abbey": "Regno Unito",
    "lewes": "Regno Unito",
    "pontypridd": "Regno Unito",
    "rochester": "Regno Unito",
    "rushden (northamptonshire)": "Regno Unito",
    "saffron walden": "Regno Unito",
    "st. ives": "Regno Unito",
    "windsor castle": "Regno Unito",
    "buckingham palace": "Regno Unito",
    "piccadilly": "Regno Unito",
    "pinner": "Regno Unito",
    "shoreditch": "Regno Unito",
    "camberwell": "Regno Unito",
    "bromley": "Regno Unito",
    "chislehurst": "Regno Unito",
    "chiswick": "Regno Unito",
    "bethnal green": "Regno Unito",
    "bannister hall": "Regno Unito",
    "barlaston": "Regno Unito",
    "bishop's stortford": "Regno Unito",
    "egerton": "Regno Unito",
    "etruria": "Regno Unito",
    "handsworth": "Regno Unito",
    "hanley": "Regno Unito",
    "hawkhurst": "Regno Unito",
    # FRANCIA
    "paris": "Francia",
    "france": "Francia",
    "nice": "Francia",
    "alsace": "Francia",
    "lyon": "Francia",
    "lyons": "Francia",
    "limoges": "Francia",
    "colmar": "Francia",
    "bretagne": "Francia",
    "cherbourg": "Francia",
    "forest of fontainebleau": "Francia",
    # ITALIA
    "italy": "Italia",
    "milan": "Italia",
    "milan (city)": "Italia",
    "milan (province)": "Italia",
    "rome": "Italia",
    "florence": "Italia",
    "florence (city)": "Italia",
    "naples": "Italia",
    "naples (province)": "Italia",
    "venice": "Italia",
    "turin": "Italia",
    "genoa": "Italia",
    "bologna": "Italia",
    "palermo": "Italia",
    "sicily": "Italia",
    "tuscany": "Italia",
    "lombardy": "Italia",
    "piedmont": "Italia",
    "umbria": "Italia",
    "abruzzi": "Italia",
    "abruzzo": "Italia",
    "sardinia": "Italia",
    "verona": "Italia",
    "siena": "Italia",
    "faenza": "Italia",
    "perugia": "Italia",
    "arienzo": "Italia",
    "messina": "Italia",
    "marches": "Italia",
    "romagna": "Italia",
    "latium": "Italia",
    "southern italy": "Italia",
    "syracuse": "Italia",
    "teramo": "Italia",
    "vicenza (town)": "Italia",
    "sant'angelo in vado": "Italia",
    "papal states": "Italia",
    "convent of santa maria degli angeli": "Italia",
    "monastery of santa maria degli angeli, florence": "Italia",
    # STATI UNITI
    "united states": "Stati Uniti",
    "united states of america": "Stati Uniti",
    "usa": "Stati Uniti",
    "america": "Stati Uniti",
    "new york": "Stati Uniti",
    "new york (city)": "Stati Uniti",
    "california": "Stati Uniti",
    "los angeles": "Stati Uniti",
    "san francisco": "Stati Uniti",
    "hollywood": "Stati Uniti",
    "massachusetts": "Stati Uniti",
    "milwaukee": "Stati Uniti",
    "oshkosh (city)": "Stati Uniti",
    # SPAGNA
    "spain": "Spagna",
    "madrid": "Spagna",
    "madrid (region)": "Spagna",
    "barcelona": "Spagna",
    "leon": "Spagna",
    # SVIZZERA
    "switzerland": "Svizzera",
    "zurich": "Svizzera",
    "geneva": "Svizzera",
    # GERMANIA
    "germany": "Germania",
    "berlin": "Germania",
    "leipzig": "Germania",
    "nuremberg": "Germania",
    "augsburg": "Germania",
    "nymphenburg": "Germania",
    "römhild": "Germania",
    "siegburg": "Germania",
    "upper rhine": "Germania",
    "westphalia": "Germania",
    # AUSTRIA
    "austria": "Austria",
    "vienna": "Austria",
    "vienna (city)": "Austria",
    # BELGIO
    "belgium": "Belgio",
    "brussels": "Belgio",
    "antwerp": "Belgio",
    "flanders": "Belgio",
    "hainaut": "Belgio",
    "mechelen": "Belgio",
    "mosan": "Belgio",
    # PAESI BASSI
    "netherlands": "Paesi Bassi",
    "amsterdam": "Paesi Bassi",
    "holland": "Paesi Bassi",
    "haarlem": "Paesi Bassi",
    "utrecht": "Paesi Bassi",
    # IRLANDA
    "ireland": "Irlanda",
    "ireland (country)": "Irlanda",
    "dublin": "Irlanda",
    "carrickmacross": "Irlanda",
    # GRECIA
    "greece": "Grecia",
    "crete": "Grecia",
    "dodecanese": "Grecia",
    "macedonia (greece)": "Grecia",
    "trikeri": "Grecia",
    "yannina": "Grecia",
    # RUSSIA
    "russia": "Russia",
    "moscow": "Russia",
    "saint petersburg": "Russia",
    "st petersburg": "Russia",
    "st. petersburg": "Russia",
    # REPUBBLICA CECA
    "prague": "Repubblica Ceca",
    "cheb": "Repubblica Ceca",
    "eger": "Repubblica Ceca",
    "czech republic": "Repubblica Ceca",
    # POLONIA
    "poland": "Polonia",
    "gdansk": "Polonia",
    # BALCANI E EUROPA ORIENTALE
    "croatia": "Croazia",
    "bosnia": "Bosnia ed Erzegovina",
    "herzegovina": "Bosnia ed Erzegovina",
    "serbia": "Serbia",
    "montenegro": "Montenegro",
    "macedonia": "Macedonia del Nord",
    "skopska crna gora": "Macedonia del Nord",
    "bulgaria": "Bulgaria",
    "romania": "Romania",
    "kalotaszeg": "Romania",
    "hungary": "Ungheria",
    # ALTRI PAESI EUROPEI
    "denmark": "Danimarca",
    "finland": "Finlandia",
    "sweden": "Svezia",
    "stockholm": "Svezia",
    "lund": "Svezia",
    "norway": "Norvegia",
    "telemark": "Norvegia",
    "malta": "Malta",
    "malta (nation)": "Malta",
    "monaco": "Monaco",
    # ASIA ORIENTALE
    "china": "Cina",
    "beijing": "Cina",
    "shanghai": "Cina",
    "hong kong": "Cina",
    "guangdong": "Cina",
    "guangzhou": "Cina",
    "hetian": "Cina",
    "khotan": "Cina",
    "shache": "Cina",
    "yarkand": "Cina",
    "ngari": "Cina",
    "japan": "Giappone",
    "tokyo": "Giappone",
    "tokyo (city)": "Giappone",
    "kyoto": "Giappone",
    "kobe": "Giappone",
    "korea": "Corea del Sud",
    "south korea": "Corea del Sud",
    "seoul": "Corea del Sud",
    # SUD-EST ASIATICO
    "indonesia": "Indonesia",
    "java": "Indonesia",
    "borneo": "Indonesia",
    "surakarta": "Indonesia",
    "philippines": "Filippine",
    "manila": "Filippine",
    # ASIA MERIDIONALE
    "india": "India",
    "delhi": "India",
    "agra": "India",
    "kolkata": "India",
    "madras": "India",
    "amritsar": "India",
    "bengal": "India",
    "west bengal": "India",
    "gujarat": "India",
    "kashmir": "India",
    "punjab (india)": "India",
    "chanderi": "India",
    "kutch": "India",
    "mysore": "India",
    "andhra pradesh": "India",
    "thanjavur": "India",
    "mandi": "India",
    "mughal empire": "India",
    "kathiawar": "India",
    "malappuram": "India",
    "dharwar": "India",
    "rohtak": "India",
    "coromandel coast": "India",
    "konarak": "India",
    "pakistan": "Pakistan",
    "lahore": "Pakistan",
    "sindh": "Pakistan",
    "hazara": "Pakistan",
    "kohat": "Pakistan",
    "shikarpur": "Pakistan",
    "north-west frontier province": "Pakistan",
    "bangladesh": "Bangladesh",
    "dhaka": "Bangladesh",
    "bhutan": "Bhutan",
    "afghanistan": "Afghanistan",
    "ghazni": "Afghanistan",
    # TURCHIA E MEDIO ORIENTE
    "turkey": "Turchia",
    "istanbul": "Turchia",
    "anatolia": "Turchia",
    "iznik": "Turchia",
    "iran": "Iran",
    "tehran": "Iran",
    "saudi arabia": "Arabia Saudita",
    "bahrain": "Bahrein",
    "palestine": "Palestina",
    "phoenicia": "Libano",
    "yemen": "Yemen",
    # AFRICA
    "egypt": "Egitto",
    "cairo": "Egitto",
    "akhmim": "Egitto",
    "faiyum": "Egitto",
    "south africa": "Sudafrica",
    "johannesburg": "Sudafrica",
    "nigeria": "Nigeria",
    "lagos": "Nigeria",
    "ghana": "Ghana",
    "accra": "Ghana",
    "morocco": "Marocco",
    "kenya": "Kenya",
    "tanzania": "Tanzania",
    "zanzibar": "Tanzania",
    "senegal": "Senegal",
    "dakar": "Senegal",
    "mali": "Mali",
    "bamako": "Mali",
    "burkina faso": "Burkina Faso",
    "sierra leone": "Sierra Leone",
    # AMERICHE E OCEANIA
    "canada": "Canada",
    "montreal": "Canada",
    "australia": "Australia",
    "mexico": "Messico",
    "brazil": "Brasile",
    "rio de janeiro": "Brasile",
    "argentina": "Argentina",
    "buenos aires": "Argentina",
    "bolivia": "Bolivia",
    "paraguay": "Paraguay",
    "guyana": "Guyana",
    "jamaica": "Giamaica",
    "barbados": "Barbados",
    "trinidad": "Trinidad e Tobago",
    # REGIONI AMPIE
    "central asia": "Asia Centrale",
    "turkestan": "Asia Centrale",
    "europe": "Europa",
    "western europe": "Europa",
}


def deduci_stato_preciso(luogo):
  """Deduce in modo preciso lo Stato in italiano a partire dal campo Luogo."""
  if not luogo:
    return ""
  l_orig = luogo.strip()
  l_pulito = l_orig.lower()

  # 1. Ricerca esatta
  if l_pulito in MAPPA_STATI:
    return MAPPA_STATI[l_pulito]

  # 2. Ricerca per parole chiave (da parole più lunghe a più corte per massima precisione)
  for k in sorted(MAPPA_STATI.keys(), key=lambda x: -len(x)):
    if k in l_pulito:
      return MAPPA_STATI[k]

  # Se il luogo coincide già con il nome di uno stato non in elenco, lo restituisce
  return l_orig


righe_aggiornate = []
anteprima_associazioni = Counter()
non_mappati = Counter()

with open(input_csv, "r", encoding="utf-8-sig") as f:
  reader = csv.DictReader(f)
  fieldnames = list(reader.fieldnames)

  col_data = next(
      (c for c in fieldnames if c.strip().lower() == "datazione"), None
  )
  col_luogo = next(
      (c for c in fieldnames if c.strip().lower() == "luogo"), None
  )

  # Costruisce l'ordine delle colonne con 'Stato' inserito tra 'Datazione' e 'Luogo'
  nuovi_fieldnames = []
  colonne_senza_stato = [c for c in fieldnames if c.strip().lower() != "stato"]

  for f_name in colonne_senza_stato:
    nuovi_fieldnames.append(f_name)
    if col_data and f_name == col_data:
      nuovi_fieldnames.append("Stato")

  # Se per caso non c'era 'Datazione', inserisce 'Stato' prima di 'Luogo'
  if "Stato" not in nuovi_fieldnames:
    idx = (
        nuovi_fieldnames.index(col_luogo)
        if col_luogo in nuovi_fieldnames
        else len(nuovi_fieldnames)
    )
    nuovi_fieldnames.insert(idx, "Stato")

  for row in reader:
    luogo_val = (row.get(col_luogo) or "").strip()
    stato_val = deduci_stato_preciso(luogo_val)

    if luogo_val:
      anteprima_associazioni[(luogo_val, stato_val)] += 1
      if luogo_val.lower() not in MAPPA_STATI and not any(
          k in luogo_val.lower() for k in MAPPA_STATI
      ):
        non_mappati[luogo_val] += 1

    row["Stato"] = stato_val
    righe_aggiornate.append(row)

# Stampa a video dell'anteprima
print("=" * 70)
print("             ANTEPRIMA MAPPATURA PRECISA LUOGO -> STATO")
print("=" * 70)
print(f"Righe totali analizzate: {len(righe_aggiornate)}")
print(f"Colonna inserita: 'Stato' posizionata tra '{col_data}' e '{col_luogo}'")
print("-" * 70)
print("Mappature applicate (campione delle più frequenti):")
for (luogo, stato), count in sorted(
    anteprima_associazioni.items(), key=lambda x: -x[1]
)[:20]:
  print(f"  • '{luogo}'  -->  '{stato}' ({count} occorrenze)")

print("-" * 70)
if non_mappati:
  print(f"Luoghi non riconosciuti: {len(non_mappati)}")
  for l, c in non_mappati.most_common(5):
    print(f"  • '{l}' ({c} volte)")
else:
  print("Copertura completa: TUTTI i luoghi del file sono stati associati!")
print("=" * 70)

# Conferma prima del salvataggio
conferma = (
    input(
        "\nVuoi procedere e salvare le modifiche su 'evening_dresses_pulito.csv'? (s/n): "
    )
    .strip()
    .lower()
)

if conferma == "s":
  with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(
        f, fieldnames=nuovi_fieldnames, extrasaction="ignore"
    )
    writer.writeheader()
    writer.writerows(righe_aggiornate)
  print(
      f"\nModifiche salvate con successo! File aggiornato con mappatura precisa in:\n{output_csv}"
  )
else:
  print("\nOperazione annullata: il file NON è stato modificato.")
