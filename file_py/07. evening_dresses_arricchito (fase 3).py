import csv
import html
import json
import re
import ssl
import time
import urllib.parse
import urllib.request

# Percorso del file CSV sul Desktop del Mac (viene letto e aggiornato)
file_csv = "/Users/giulia/Desktop/evening_dresses_arricchito.csv"

# Endpoint ufficiali delle API V&A
API_SEARCH_URL = "https://api.vam.ac.uk/v2/objects/search"
API_OBJECT_URL = "https://api.vam.ac.uk/v2/object/"

# Contesto SSL per evitare errori di verifica certificati su macOS
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
    """Decodifica entità HTML, rimuove eventuali tag e normalizza gli spazi."""
    if not testo:
        return ""
    testo_decodificato = html.unescape(str(testo))
    senza_tag = re.sub(r"<[^>]+>", " ", testo_decodificato)
    return re.sub(r"\s+", " ", senza_tag).strip()


def estrai_materiali_e_descrizione(record):
    """Estrae e combina 'Materials and techniques' e 'Physical description' dal record V&A."""
    if not isinstance(record, dict):
        return ""

    # 1. Sezione "Materials and techniques"
    mat_tech = pulisci_testo(record.get("materialsAndTechniques", ""))
    if not mat_tech:
        # Fallback sulle liste strutturate 'materials' e 'techniques' se il campo testuale è vuoto
        voci = []
        for campo in ("materials", "techniques"):
            lista = record.get(campo) or []
            if isinstance(lista, list):
                for elem in lista:
                    if isinstance(elem, dict) and elem.get("text"):
                        voci.append(pulisci_testo(elem["text"]))
                    elif isinstance(elem, str) and elem.strip():
                        voci.append(pulisci_testo(elem))
        mat_tech = ", ".join(dict.fromkeys(voci))

    # 2. Sezione "Physical description"
    phys_desc = pulisci_testo(record.get("physicalDescription", ""))

    # Combina le due sezioni evitando duplicazioni
    if mat_tech and phys_desc:
        if mat_tech.lower() == phys_desc.lower() or phys_desc.lower() in mat_tech.lower():
            return mat_tech
        if mat_tech.lower() in phys_desc.lower():
            return phys_desc
        return f"{mat_tech} | {phys_desc}"
    return mat_tech or phys_desc


def costruisci_indice_accessioni():
    """Indicizza Numero Accessione -> systemNumber dalla ricerca V&A."""
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


def recupera_materiali(system_number):
    """Scarica la scheda tecnica completa ed estrae materiali e descrizione fisica."""
    url = f"{API_OBJECT_URL}{urllib.parse.quote(system_number)}"
    dati = scarica_json(url)
    if not dati or "record" not in dati:
        return ""
    return estrai_materiali_e_descrizione(dati["record"])


# --- ESECUZIONE PRINCIPALE ---

# 1. Lettura del CSV arricchito esistente
with open(file_csv, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    fieldnames_orig = list(reader.fieldnames)
    righe = list(reader)

# Individuazione delle colonne "Posizione" e "Numero accessione"
col_posizione = next((c for c in fieldnames_orig if c.strip().lower() == "posizione"), None)
col_accessione = next((c for c in fieldnames_orig if "accessione" in c.strip().lower()), None)

if not col_posizione or not col_accessione:
    print("Errore: verifica che nel CSV siano presenti le colonne 'Posizione' e 'Numero accessione'.")
    exit()

# Inserimento della colonna "Materiali" subito dopo "Posizione"
# (rimuove un'eventuale colonna "Materiali" preesistente se lo script viene rieseguito)
fieldnames_puliti = [c for c in fieldnames_orig if c.strip().lower() != "materiali"]
nuovi_fieldnames = []
for col in fieldnames_puliti:
    nuovi_fieldnames.append(col)
    if col == col_posizione:
        nuovi_fieldnames.append("Materiali")

# 2. Costruzione della mappa Numero accessione -> systemNumber dal catalogo V&A
mappa_vam = costruisci_indice_accessioni()

# 3. Abbinamento tramite Numero accessione e scaricamento dei dati
cache_materiali = {}
totale_righe = len(righe)
abbinati_con_materiali = 0

print(f"\n2. Recupero 'Materials and techniques' e 'Physical description' per {totale_righe} abiti...")

for idx, row in enumerate(righe, 1):
    acc_orig = (row.get(col_accessione) or "").strip()
    acc_norm = acc_orig.lower()

    if not acc_norm:
        row["Materiali"] = ""
        continue

    if acc_norm in cache_materiali:
        testo_materiali = cache_materiali[acc_norm]
    else:
        sys_num = mappa_vam.get(acc_norm)
        if not sys_num:
            sys_num = cerca_system_number_singolo(acc_orig)

        if sys_num:
            testo_materiali = recupera_materiali(sys_num)
            time.sleep(0.1)  # Pausa breve per non sovraccaricare il server del museo
        else:
            testo_materiali = ""

        cache_materiali[acc_norm] = testo_materiali

    row["Materiali"] = testo_materiali
    if testo_materiali:
        abbinati_con_materiali += 1

    # Aggiornamento stato avanzamento ogni 25 righe nella Shell di IDLE
    if idx % 25 == 0 or idx == totale_righe:
        print(f"   Elaborati {idx}/{totale_righe} abiti (schede con 'Materiali' compilato: {abbinati_con_materiali})")

# 4. Salvataggio sul file CSV arricchito
with open(file_csv, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=nuovi_fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(righe)

print("\nOperazione completata con successo!")
print(f"File aggiornato in: {file_csv}")
print(f"Righe totali: {totale_righe} | Righe con 'Materiali' valorizzata: {abbinati_con_materiali}")
