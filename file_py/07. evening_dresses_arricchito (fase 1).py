import csv
import html
import json
import re
import ssl
import time
import urllib.parse
import urllib.request

# Percorsi dei file sul Desktop del Mac
input_csv = "/Users/giulia/Desktop/evening_dresses_pulito.csv"
output_csv = "/Users/giulia/Desktop/evening_dresses_arricchito.csv"

# Endpoint ufficiali delle collezioni V&A
API_SEARCH_URL = "https://api.vam.ac.uk/v2/objects/search"
API_OBJECT_URL = "https://api.vam.ac.uk/v2/object/"

# Contesto SSL per evitare errori di certificato su macOS con urllib
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


def scarica_json(url, tentativi=3):
    """Esegue una richiesta HTTP GET e restituisce il JSON decodificato."""
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
    req = urllib.request.Request(url, headers=headers)
    for i in range(tentativi):
        try:
            with urllib.request.urlopen(req, context=ssl_context, timeout=20) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            if i == tentativi - 1:
                print(f"  [Avviso] Errore di connessione su {url}: {e}")
                return None
            time.sleep(1)


def pulisci_testo(testo):
    """Rimuove eventuali tag HTML e normalizza gli spazi nel testo di Object history."""
    if not testo:
        return ""
    testo_decodificato = html.unescape(str(testo))
    senza_tag = re.sub(r"<[^>]+>", " ", testo_decodificato)
    return re.sub(r"\s+", " ", senza_tag).strip()


def costruisci_indice_accessioni():
    """Scarica tutte le pagine della ricerca V&A per mappare Numero Accessione -> systemNumber."""
    mappa_accessioni = {}
    pagina = 1
    page_size = 100

    print("1. Scaricamento indice schede dal catalogo V&A...")
    while True:
        params = urllib.parse.urlencode({
            "id_category": "THES48999",
            "kw_object_type": "Evening dress",
            "page": pagina,
            "page_size": page_size,
            "q": ""
        })
        url = f"{API_SEARCH_URL}?{params}"
        dati = scarica_json(url)
        if not dati or "records" not in dati:
            break

        records = dati["records"]
        if not records:
            break

        for rec in records:
            acc = (rec.get("accessionNumber") or "").strip().lower()
            sys_num = (rec.get("systemNumber") or "").strip()
            if acc and sys_num:
                mappa_accessioni[acc] = sys_num

        pagine_totali = dati.get("info", {}).get("pages", 1)
        print(f"   Pagina {pagina}/{pagine_totali} acquisita ({len(mappa_accessioni)} oggetti indicizzati)")

        if pagina >= pagine_totali:
            break
        pagina += 1
        time.sleep(0.15)

    return mappa_accessioni


def cerca_system_number_singolo(numero_accessione):
    """Ricerca di riserva per numero di accessione specifico."""
    params = urllib.parse.urlencode({"q": numero_accessione, "page_size": 10})
    dati = scarica_json(f"{API_SEARCH_URL}?{params}")
    if not dati or "records" not in dati:
        return None

    target = numero_accessione.strip().lower()
    for rec in dati["records"]:
        acc = (rec.get("accessionNumber") or "").strip().lower()
        if acc == target:
            return rec.get("systemNumber")
    return None


def recupera_object_history(system_number):
    """Scarica la scheda tecnica completa dell'oggetto ed estrae 'objectHistory'."""
    url = f"{API_OBJECT_URL}{urllib.parse.quote(system_number)}"
    dati = scarica_json(url)
    if not dati or "record" not in dati:
        return ""
    storia = dati["record"].get("objectHistory", "")
    return pulisci_testo(storia)


# --- ESECUZIONE PRINCIPALE ---

# 1. Lettura del CSV pulito
with open(input_csv, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    fieldnames = list(reader.fieldnames)
    righe = list(reader)

# Individuazione delle colonne "Posizione" e "Numero accessione"
col_posizione = next((c for c in fieldnames if c.strip().lower() == "posizione"), None)
col_accessione = next((c for c in fieldnames if "accessione" in c.strip().lower()), None)

if not col_posizione or not col_accessione:
    print("Errore: verifica che nel CSV siano presenti le colonne 'Posizione' e 'Numero accessione'.")
    exit()

# Inserimento della colonna "Storia dell'oggetto" subito dopo "Posizione"
nuovi_fieldnames = []
for col in fieldnames:
    nuovi_fieldnames.append(col)
    if col == col_posizione:
        nuovi_fieldnames.append("Storia dell'oggetto")

# 2. Costruzione della mappa Numero accessione -> systemNumber dal catalogo V&A
mappa_vam = costruisci_indice_accessioni()

# 3. Abbinamento e scaricamento di "Object history" per ogni riga del CSV
cache_storie = {}
totale_righe = len(righe)
abbinati_con_storia = 0

print(f"\n2. Recupero 'Object history' per {totale_righe} abiti...")

for idx, row in enumerate(righe, 1):
    acc_orig = (row.get(col_accessione) or "").strip()
    acc_norm = acc_orig.lower()

    if not acc_norm:
        row["Storia dell'oggetto"] = ""
        continue

    # Se abbiamo già scaricato questo numero di accessione, riusiamo il risultato
    if acc_norm in cache_storie:
        storia_testo = cache_storie[acc_norm]
    else:
        sys_num = mappa_vam.get(acc_norm)
        if not sys_num:
            sys_num = cerca_system_number_singolo(acc_orig)

        if sys_num:
            storia_testo = recupera_object_history(sys_num)
            time.sleep(0.1)  # Pausa breve per non sovraccaricare il server del museo
        else:
            storia_testo = ""

        cache_storie[acc_norm] = storia_testo

    row["Storia dell'oggetto"] = storia_testo
    if storia_testo:
        abbinati_con_storia += 1

    # Avanzamento ogni 25 righe nella Shell di IDLE
    if idx % 25 == 0 or idx == totale_righe:
        print(f"   Elaborati {idx}/{totale_righe} abiti (schede con 'Object history' compilata: {abbinati_con_storia})")

# 4. Salvataggio del nuovo file CSV arricchito
with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=nuovi_fieldnames)
    writer.writeheader()
    writer.writerows(righe)

print("\nOperazione completata con successo!")
print(f"File salvato in: {output_csv}")
print(f"Righe totali: {totale_righe} | Righe con 'Storia dell'oggetto' valorizzata: {abbinati_con_storia}")
