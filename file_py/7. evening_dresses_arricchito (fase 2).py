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
API_OBJECT_URL = "https://api.vam.ac.uk/v2/museumobject/"

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


def combina_riassunto(summary, brief):
    """Unisce in modo pulito 'Summary' e 'Brief description' evitando ripetizioni."""
    s = pulisci_testo(summary)
    b = pulisci_testo(brief)
    if s and b:
        if s.lower() == b.lower() or b.lower() in s.lower():
            return s
        if s.lower() in b.lower():
            return b
        return f"{s} | {b}"
    return s or b


def costruisci_indice_accessioni():
    """Indicizza Numero Accessione -> (systemNumber, briefDescription) dalla ricerca V&A."""
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
            brief_search = rec.get("briefDescription") or ""
            if acc and sys_num:
                mappa_accessioni[acc] = (sys_num, brief_search)

        pagine_totali = dati.get("info", {}).get("pages", 1)
        print(f"   Pagina {pagina}/{pagine_totali} acquisita ({len(mappa_accessioni)} oggetti indicizzati)")

        if pagina >= pagine_totali:
            break
        pagina += 1
        time.sleep(0.15)

    return mappa_accessioni


def cerca_oggetto_singolo(numero_accessione):
    """Ricerca di riserva per numero di accessione specifico."""
    params = urllib.parse.urlencode({"q": numero_accessione, "page_size": 10})
    dati = scarica_json(f"{API_SEARCH_URL}?{params}")
    if not dati or "records" not in dati:
        return None, ""

    target = numero_accessione.strip().lower()
    for rec in dati["records"]:
        acc = (rec.get("accessionNumber") or "").strip().lower()
        if acc == target:
            return rec.get("systemNumber"), (rec.get("briefDescription") or "")
    return None, ""


def recupera_summary_e_brief(system_number, brief_fallback=""):
    """Scarica la scheda tecnica completa ed estrae 'summaryDescription' e 'briefDescription'."""
    url = f"{API_OBJECT_URL}{urllib.parse.quote(system_number)}"
    dati = scarica_json(url)
    if not dati or "record" not in dati:
        return pulisci_testo(brief_fallback)

    record = dati["record"]
    summary_text = record.get("summaryDescription", "")
    brief_text = record.get("briefDescription") or brief_fallback
    return combina_riassunto(summary_text, brief_text)


# --- ESECUZIONE PRINCIPALE ---

# 1. Lettura del CSV arricchito esistente
with open(file_csv, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    fieldnames_orig = list(reader.fieldnames)
    righe = list(reader)

# Individuazione delle colonne "Storia dell'oggetto" e "Numero accessione"
col_storia = next((c for c in fieldnames_orig if c.strip().lower() == "storia dell'oggetto"), None)
col_accessione = next((c for c in fieldnames_orig if "accessione" in c.strip().lower()), None)

if not col_storia or not col_accessione:
    print("Errore: verifica che nel CSV siano presenti le colonne 'Storia dell'oggetto' e 'Numero accessione'.")
    exit()

# Inserimento della colonna "Riassunto" subito dopo "Storia dell'oggetto"
# (rimuove un'eventuale colonna "Riassunto" preesistente per evitare duplicati se rieseguito)
fieldnames_puliti = [c for c in fieldnames_orig if c.strip().lower() != "riassunto"]
nuovi_fieldnames = []
for col in fieldnames_puliti:
    nuovi_fieldnames.append(col)
    if col == col_storia:
        nuovi_fieldnames.append("Riassunto")

# 2. Costruzione della mappa dal catalogo V&A
mappa_vam = costruisci_indice_accessioni()

# 3. Abbinamento tramite Numero accessione e recupero di Summary / Brief description
cache_riassunti = {}
totale_righe = len(righe)
abbinati_con_riassunto = 0

print(f"\n2. Recupero 'Summary' e 'Brief description' per {totale_righe} abiti...")

for idx, row in enumerate(righe, 1):
    acc_orig = (row.get(col_accessione) or "").strip()
    acc_norm = acc_orig.lower()

    if not acc_norm:
        row["Riassunto"] = ""
        continue

    if acc_norm in cache_riassunti:
        testo_riassunto = cache_riassunti[acc_norm]
    else:
        if acc_norm in mappa_vam:
            sys_num, brief_search = mappa_vam[acc_norm]
        else:
            sys_num, brief_search = cerca_oggetto_singolo(acc_orig)

        if sys_num:
            testo_riassunto = recupera_summary_e_brief(sys_num, brief_search)
            time.sleep(0.1)  # Pausa breve per rispettare i limiti del server V&A
        else:
            testo_riassunto = ""

        cache_riassunti[acc_norm] = testo_riassunto

    row["Riassunto"] = testo_riassunto
    if testo_riassunto:
        abbinati_con_riassunto += 1

    # Aggiornamento stato avanzamento ogni 25 righe nella Shell
    if idx % 25 == 0 or idx == totale_righe:
        print(f"   Elaborati {idx}/{totale_righe} abiti (schede con 'Riassunto' compilato: {abbinati_con_riassunto})")

# 4. Salvataggio sul file CSV arricchito
with open(file_csv, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=nuovi_fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(righe)

print("\nOperazione completata con successo!")
print(f"File aggiornato in: {file_csv}")
print(f"Righe totali: {totale_righe} | Righe con 'Riassunto' valorizzato: {abbinati_con_riassunto}")
