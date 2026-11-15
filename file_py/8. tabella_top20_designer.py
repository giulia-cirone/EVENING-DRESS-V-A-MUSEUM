import csv
import json
import os
import re
import ssl
import textwrap
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
import matplotlib.pyplot as plt

# Percorsi dei file sul Desktop del Mac
csv_principale = "/Users/giulia/Desktop/evening_dresses_pulito.csv"
csv_alternativo = "/Users/giulia/Desktop/evening_dresses_arricchito.csv"
input_csv = csv_principale if os.path.exists(csv_principale) else csv_alternativo

output_json = "/Users/giulia/Desktop/dati biografici 20 designer più diffusi.json"
output_csv = "/Users/giulia/Desktop/tabella_top20_designer.csv"
output_png = "/Users/giulia/Desktop/tabella_top20_designer.png"

# Endpoint API pubblici (gratuiti e senza registrazione)
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
WIKIPEDIA_API_EN = "https://en.wikipedia.org/w/api.php"
WIKIPEDIA_API_IT = "https://it.wikipedia.org/w/api.php"
LLM_FREE_URL = "https://text.pollinations.ai/openai"

HEADERS = {
    "User-Agent": "ArchivioModaRicerca/1.0 (https://collections.vam.ac.uk; studio@example.org) Python-urllib/3"
}

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

cache_entita = {}

# Varianti per risolvere nomi brevi o d'arte nel catalogo V&A
ALIAS_DESIGNER = {
    "yuki": ["Yuki Torimaru", "Gun'yuki Torimaru"],
    "yuri": ["Yuki Torimaru", "Gun'yuki Torimaru"],
    "madame grès": ["Madame Grès", "Germaine Émilie Krebs"],
    "callot soeurs": ["Callot Soeurs", "Callot sisters"],
}

# Mappa geografica di supporto per l'estrazione diretta dalle biografie Wikipedia
LUOGHI_GEOGRAFICI_TO_NAZIONE = {
    "paris": "Francia", "parigi": "Francia", "france": "Francia", "francia": "Francia",
    "london": "Regno Unito", "londra": "Regno Unito", "britain": "Regno Unito", "great britain": "Regno Unito",
    "england": "Regno Unito", "scotland": "Regno Unito", "uk": "Regno Unito",
    "united kingdom": "Regno Unito", "regno unito": "Regno Unito", "inghilterra": "Regno Unito",
    "greece": "Grecia", "grecia": "Grecia", "athens": "Grecia", "atene": "Grecia",
    "italy": "Italia", "italia": "Italia", "rome": "Italia", "roma": "Italia", "milan": "Italia", "milano": "Italia",
    "spain": "Spagna", "spagna": "Spagna", "madrid": "Spagna", "barcelona": "Spagna",
    "san sebastián": "Spagna", "san sebastian": "Spagna",
    "new york": "Stati Uniti", "united states": "Stati Uniti", "los angeles": "Stati Uniti", "stati uniti": "Stati Uniti",
    "tokyo": "Giappone", "osaka": "Giappone", "japan": "Giappone", "giappone": "Giappone",
}

VERBI_ATTIVITA = (
    "work", "worked", "open", "opened", "found", "founded", "establish", "established",
    "move", "moved", "base", "based", "career", "atelier", "couture", "house", "salon",
    "design", "designed", "studio", "director", "label", "brand", "return", "returned",
    "settled", "boutique", "lavor", "fond", "apr", "trasfer", "carriera", "casa di moda"
)


def anno_in_decennio(anno):
    """Converte un anno intero nel relativo decennio (es. 1937 -> anni '30)."""
    dec = (anno // 10) * 10
    return f"anni {dec}" if dec >= 2000 else f"anni '{str(dec)[2:]}"


def normalizza_periodo_output(periodo_str):
    """
    Garantisce il formato richiesto:
    - Anni precisi (es. '1937 - 1957') SENZA decenni tra parentesi se gli anni sono noti.
    - Decenni (es. \"anni '10 - anni '70\") SOLO se non si conoscono gli anni precisi.
    """
    if not periodo_str:
        return "Non disponibile"
    s = str(periodo_str).strip()
    s = re.sub(
        r"\s*\(anni\s*['’]?\d{2,4}(?:\s*-\s*anni\s*['’]?\d{2,4})?\)",
        "",
        s,
        flags=re.IGNORECASE
    ).strip()

    m_ca = re.match(r"^ca\.\s*(\d{4})\s*-\s*(\d{4}|oggi|in attività)$", s, flags=re.IGNORECASE)
    if m_ca:
        anno_in = int(m_ca.group(1))
        fine_raw = m_ca.group(2)
        dec_in = anno_in_decennio(anno_in)
        if fine_raw.isdigit():
            dec_fine = anno_in_decennio(int(fine_raw))
            return f"{dec_in} - {dec_fine}" if dec_in != dec_fine else dec_in
        return f"dagli {dec_in}"

    return s


def pulisci_luogo_nascita(luogo):
    """Rimuove '[Maison]' e normalizza quartieri/arrondissement nel nome della città."""
    if not luogo:
        return ""
    luogo = str(luogo).replace("[Maison]", "").strip()
    luogo = re.sub(r"^[IVXLCDM]+\s+arrondissement\s+di\s+Parigi", "Parigi", luogo, flags=re.IGNORECASE)
    return luogo.strip()


def richiedi_json_get(base_url, params, tentativi=4):
    """Esegue una richiesta GET HTTP e restituisce il JSON decodificato."""
    params["format"] = "json"
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers=HEADERS)

    for tentativo in range(tentativi):
        try:
            with urllib.request.urlopen(req, context=ssl_context, timeout=20) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                time.sleep(2.0 * (tentativo + 1))
            else:
                return None
        except Exception:
            time.sleep(1.0)
    return None


def scarica_entita_batch(lista_qid):
    """Scarica fino a 45 entità Wikidata in una sola chiamata HTTP."""
    da_scaricare = [q for q in dict.fromkeys(lista_qid) if q and q not in cache_entita]
    if not da_scaricare:
        return

    for i in range(0, len(da_scaricare), 45):
        blocco = da_scaricare[i:i + 45]
        dati = richiedi_json_get(WIKIDATA_API, {
            "action": "wbgetentities",
            "ids": "|".join(blocco),
            "props": "labels|claims|descriptions",
            "languages": "it|en"
        })
        entities = (dati or {}).get("entities", {})
        for qid in blocco:
            cache_entita[qid] = entities.get(qid, {})
        time.sleep(0.3)


def etichetta_italiana(qid):
    """Restituisce il nome in italiano (o inglese) di un Q-ID Wikidata."""
    if not qid:
        return ""
    if qid not in cache_entita:
        scarica_entita_batch([qid])
    ent = cache_entita.get(qid, {})
    labels = ent.get("labels", {})
    nome = labels.get("it", {}).get("value") or labels.get("en", {}).get("value") or ""

    if "regno unito di gran bretagna" in nome.lower():
        return "Regno Unito"
    return nome


def estrai_qid_proprieta(entita, prop, solo_attuali=False):
    """Estrae i Q-ID di una proprietà Wikidata, filtrando opzionalmente gli stati storici (P582)."""
    risultati_attuali = []
    tutti = []
    for claim in entita.get("claims", {}).get(prop, []):
        val = claim.get("mainsnak", {}).get("datavalue", {}).get("value", {})
        if isinstance(val, dict) and "id" in val:
            qid = val["id"]
            tutti.append(qid)
            qualifiers = claim.get("qualifiers", {})
            if "P582" not in qualifiers:
                risultati_attuali.append(qid)

    if solo_attuali and risultati_attuali:
        return risultati_attuali
    return tutti


def estrai_anno_proprieta(entita, prop):
    """Estrae l'anno intero da una proprietà temporale Wikidata."""
    anni = []
    for claim in entita.get("claims", {}).get(prop, []):
        val = claim.get("mainsnak", {}).get("datavalue", {}).get("value", {})
        if isinstance(val, dict) and "time" in val:
            match = re.search(r"([+-]?\d{4})-", val["time"])
            if match:
                anni.append(abs(int(match.group(1))))
    return min(anni) if anni else None


def cerca_qid_designer(nome_designer):
    """Cerca il Q-ID dello stilista su Wikidata dando precedenza alla persona (Q5)."""
    parole_moda = (
        "fashion", "designer", "couturier", "dressmaker", "clothing",
        "moda", "stilista", "sart", "costume", "textile", "sisters"
    )
    chiave = nome_designer.strip().lower()
    varianti = ALIAS_DESIGNER.get(chiave, [re.sub(r"\([^)]*\)", "", nome_designer).strip()])

    candidati_qid = []
    for var in varianti:
        for query in (var, f"{var} fashion designer"):
            dati = richiedi_json_get(WIKIDATA_API, {
                "action": "wbsearchentities",
                "search": query,
                "language": "en",
                "limit": 8
            })
            time.sleep(0.25)
            for item in (dati or {}).get("search", []):
                desc = (item.get("description") or "").lower()
                if any(k in desc for k in parole_moda):
                    if item["id"] not in candidati_qid:
                        candidati_qid.append(item["id"])

    if not candidati_qid:
        return None

    scarica_entita_batch(candidati_qid)
    for qid in candidati_qid:
        ent = cache_entita.get(qid, {})
        if "Q5" in estrai_qid_proprieta(ent, "P31"):
            return qid

    return candidati_qid[0]


def ottieni_biografia_wikipedia(nome_ricerca):
    """Scarica la biografia completa da Wikipedia EN/IT per analisi LLM e fallback locale."""
    chiave = nome_ricerca.strip().lower()
    query_nome = ALIAS_DESIGNER.get(chiave, [nome_ricerca])[0]

    for api_wiki in (WIKIPEDIA_API_EN, WIKIPEDIA_API_IT):
        dati = richiedi_json_get(api_wiki, {
            "action": "query",
            "generator": "search",
            "gsrsearch": f"{query_nome} fashion designer",
            "gsrlimit": 1,
            "prop": "extracts",
            "exchars": 3200,
            "explaintext": 1
        })
        pages = (dati or {}).get("query", {}).get("pages", {})
        for page in pages.values():
            estratto = (page.get("extract") or "").strip()
            if estratto and len(estratto) > 80:
                return estratto
    return ""


def estrai_nazioni_attivita_da_wiki(testo_wiki):
    """Estrae dal testo biografico le reali nazioni in cui lo stilista ha lavorato."""
    if not testo_wiki:
        return []
    conteggio_nazioni = {}
    frasi = re.split(r"(?<=[.!?])\s+", testo_wiki)

    for frase in frasi:
        f_low = frase.lower()
        if any(k in f_low for k in ("born in", "nato a", "nata a", "died in", "morì a")) and not any(v in f_low for v in VERBI_ATTIVITA):
            continue
        if any(v in f_low for v in VERBI_ATTIVITA):
            for chiave, nazione in LUOGHI_GEOGRAFICI_TO_NAZIONE.items():
                if re.search(rf"\b{re.escape(chiave)}\b", f_low):
                    conteggio_nazioni[nazione] = conteggio_nazioni.get(nazione, 0) + 1

    ordinate = sorted(conteggio_nazioni.items(), key=lambda x: (-x[1], x[0]))
    return [naz for naz, _ in ordinate[:2]]


def estrai_periodo_da_wiki(testo_wiki, anno_nascita=None, anno_morte=None):
    """Estrae dal testo biografico gli anni precisi di esordio professionale e fine carriera."""
    if not testo_wiki:
        return None, None
    anni_esordio = []
    anni_fine = []

    min_plausibile = (anno_nascita + 15) if anno_nascita else 1850
    max_plausibile = anno_morte if anno_morte else 2026

    frasi = re.split(r"(?<=[.!?])\s+", testo_wiki)
    for frase in frasi:
        f_low = frase.lower()
        if "born " in f_low and not any(k in f_low for k in ("open", "found", "career", "debut", "first", "start", "join")):
            continue

        if any(k in f_low for k in (
            "opened his", "opened her", "opened their", "first boutique", "first salon",
            "first collection", "own house", "own couture", "own label", "began his career",
            "began her career", "fashion career", "established", "founded", "debut", "joined"
        )):
            for m in re.findall(r"\b(1[89]\d\d|20[012]\d)\b", frase):
                y = int(m)
                if min_plausibile <= y <= max_plausibile:
                    anni_esordio.append(y)

        if any(k in f_low for k in (
            "retired", "retirement", "closed his", "closed her", "closed the",
            "stepped down", "left the house", "ceased"
        )):
            for m in re.findall(r"\b(1[89]\d\d|20[012]\d)\b", frase):
                y = int(m)
                if min_plausibile <= y <= max_plausibile:
                    anni_fine.append(y)

    inizio = min(anni_esordio) if anni_esordio else None
    fine = max(anni_fine) if anni_fine else anno_morte
    return inizio, fine


def interroga_llm_blocco_5(blocco_info):
    """
    Invia un blocco di 5 designer all'LLM insieme agli estratti Wikipedia
    e restituisce un dizionario {nome_designer: {luogo_nascita, luogo_attivita, periodo_attivita}}.
    """
    blocchi_testuali = []
    for item in blocco_info:
        nome_query = ALIAS_DESIGNER.get(item["designer"].strip().lower(), [item["designer"]])[0]
        estratto_breve = (item["wiki"] or "")[:1200]
        blocchi_testuali.append(
            f"- DESIGNER CSV: \"{item['designer']}\" (Nome completo: \"{nome_query}\")\n"
            f"  Indizi Wikidata: nascita='{item['nascita_base']}', sede='{item['attivita_base']}', periodo='{item['periodo_base']}'\n"
            f"  Biografia web: {estratto_breve}"
        )

    prompt = (
        "Analizza questi 5 stilisti di moda e restituisci ESCLUSIVAMENTE un array JSON valido "
        "con 5 oggetti aventi ciascuno queste 4 chiavi esatte:\n"
        '- "designer": il valore esatto di DESIGNER CSV indicato sotto.\n'
        '- "luogo_nascita": "Città (Nazione attuale)" di nascita dello stilista (es. "Parigi (Francia)", "Roma (Italia)"). '
        "Non scrivere mai 'Maison' né nomi di edifici/quartieri.\n"
        '- "luogo_attivita": SOLO la nazione o le nazioni in italiano (separate da virgola) in cui lo stilista '
        "ha lavorato principalmente (NON il paese di nascita o di cittadinanza; es. Jean Dessès -> 'Francia, Grecia'; "
        "Yuki -> 'Francia, Regno Unito'; Edward Molyneux -> 'Francia').\n"
        '- "periodo_attivita": periodo lavorativo della carriera dello stilista dall\'esordio come designer '
        "(NON dalla nascita) alla fine della sua carriera o ritiro (NON gli anni successivi della maison). "
        "FORMATO OBBLIGATORIO: scrivi gli anni precisi (es. '1937 - 1957' o '1962 - oggi') se noti; "
        "scrivi i decenni (es. \"anni '70 - anni 2000\") SOLO SE gli anni precisi non sono disponibili (mai entrambi).\n\n"
        "DATI DEI 5 DESIGNER:\n" + "\n\n".join(blocchi_testuali)
    )

    payload = json.dumps({
        "model": "openai",
        "messages": [
            {"role": "system", "content": "Sei uno storico della moda. Rispondi esclusivamente con un array JSON puro."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1
    }).encode("utf-8")

    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    url_llm = "https://api.openai.com/v1/chat/completions" if openai_key else LLM_FREE_URL

    headers_llm = {
        "Content-Type": "application/json",
        "User-Agent": HEADERS["User-Agent"]
    }
    if openai_key:
        headers_llm["Authorization"] = f"Bearer {openai_key}"

    req = urllib.request.Request(url_llm, data=payload, headers=headers_llm, method="POST")
    for tentativo in range(3):
        try:
            with urllib.request.urlopen(req, context=ssl_context, timeout=35) as resp:
                risposta_raw = resp.read().decode("utf-8")
                dati_resp = json.loads(risposta_raw)
                testo = dati_resp.get("choices", [{}])[0].get("message", {}).get("content", "")
                match = re.search(r"\[[\s\S]*\]", testo)
                if match:
                    lista_ris = json.loads(match.group(0))
                    mappa = {}
                    for obj in lista_ris:
                        if isinstance(obj, dict) and obj.get("designer"):
                            mappa[obj["designer"].strip().lower()] = obj
                    return mappa
        except Exception:
            time.sleep(2.0 * (tentativo + 1))

    return {}


def prepara_dati_base_designer(pos, designer, num_abiti, qid):
    """Prepara i dati base da Wikidata + Wikipedia per un singolo designer."""
    biografia_wiki = ottieni_biografia_wikipedia(designer)

    luogo_nascita = ""
    nazioni_attivita = []
    anno_inizio_esatto = None
    anno_fine_esatto = None
    anno_nascita = None
    anno_morte = None

    if qid and qid in cache_entita:
        ent = cache_entita[qid]

        # Luogo di nascita
        p19 = estrai_qid_proprieta(ent, "P19") or estrai_qid_proprieta(ent, "P740") or estrai_qid_proprieta(ent, "P159")
        if p19:
            qid_citta = p19[0]
            citta = etichetta_italiana(qid_citta)
            ent_citta = cache_entita.get(qid_citta, {})
            paesi_citta = estrai_qid_proprieta(ent_citta, "P17", solo_attuali=True)
            nazione = etichetta_italiana(paesi_citta[-1]) if paesi_citta else ""
            if citta and nazione and citta.lower() != nazione.lower():
                luogo_nascita = f"{citta} ({nazione})"
            else:
                luogo_nascita = citta or nazione
            luogo_nascita = pulisci_luogo_nascita(luogo_nascita)

        # Sedi effettive di lavoro su Wikidata (P937, P159, P108)
        for prop in ("P937", "P159", "P108"):
            for loc_qid in estrai_qid_proprieta(ent, prop):
                ent_loc = cache_entita.get(loc_qid, {})
                paesi_loc = estrai_qid_proprieta(ent_loc, "P17", solo_attuali=True)
                naz = etichetta_italiana(paesi_loc[-1]) if paesi_loc else ""
                if naz and naz not in nazioni_attivita:
                    nazioni_attivita.append(naz)

        anno_inizio_esatto = estrai_anno_proprieta(ent, "P2031") or estrai_anno_proprieta(ent, "P571")
        anno_fine_esatto = estrai_anno_proprieta(ent, "P2032") or estrai_anno_proprieta(ent, "P576")
        anno_nascita = estrai_anno_proprieta(ent, "P569")
        anno_morte = estrai_anno_proprieta(ent, "P570")

    # Integrazione da Wikipedia (luoghi di lavoro reali e date carriera)
    for naz in estrai_nazioni_attivita_da_wiki(biografia_wiki):
        if naz not in nazioni_attivita:
            nazioni_attivita.append(naz)

    if not nazioni_attivita and qid and qid in cache_entita:
        for naz_qid in estrai_qid_proprieta(cache_entita[qid], "P27", solo_attuali=True):
            naz = etichetta_italiana(naz_qid)
            if naz and naz not in nazioni_attivita:
                nazioni_attivita.append(naz)

    inizio_wiki, fine_wiki = estrai_periodo_da_wiki(biografia_wiki, anno_nascita, anno_morte)
    if not anno_inizio_esatto and inizio_wiki:
        anno_inizio_esatto = inizio_wiki
    if not anno_fine_esatto:
        anno_fine_esatto = fine_wiki or anno_morte

    if anno_inizio_esatto:
        fine_str = str(anno_fine_esatto) if anno_fine_esatto else "oggi"
        periodo_base = f"{anno_inizio_esatto} - {fine_str}"
    elif anno_nascita:
        dec_in = anno_in_decennio(anno_nascita + 22)
        if anno_morte:
            dec_fine = anno_in_decennio(anno_morte)
            periodo_base = f"{dec_in} - {dec_fine}" if dec_in != dec_fine else dec_in
        else:
            periodo_base = f"dagli {dec_in}"
    else:
        periodo_base = ""

    return {
        "posizione": pos,
        "designer": designer,
        "abiti": num_abiti,
        "wiki": biografia_wiki,
        "nascita_base": pulisci_luogo_nascita(luogo_nascita),
        "attivita_base": ", ".join(nazioni_attivita[:3]),
        "periodo_base": periodo_base,
    }


def salva_json_progressivo(lista_record, percorso_json):
    """Salva e aggiorna su disco il file JSON con i designer elaborati finora."""
    with open(percorso_json, "w", encoding="utf-8") as f:
        json.dump(lista_record, f, ensure_ascii=False, indent=2)


# --- ESECUZIONE PRINCIPALE ---

# 1. Estrazione dei 20 designer più frequenti dal CSV
conteggio_designer = Counter()

with open(input_csv, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    col_designer = next(
        (c for c in reader.fieldnames if "designer" in c.strip().lower() or "maker" in c.strip().lower()),
        None
    )
    if not col_designer:
        print("Errore: colonna 'Designer' non trovata nel CSV!")
        exit()

    for row in reader:
        nome = (row.get(col_designer) or "").strip()
        if nome and nome.lower() not in {"unknown", "sconosciuto", "non specificato", "anonymous", "anonimo"}:
            conteggio_designer[nome] += 1

top_20 = conteggio_designer.most_common(20)

# 2. Recupero identificativi Wikidata in blocco
print("1. Ricerca identificativi Wikidata per i 20 designer...")
mappa_designer_qid = {}
for pos, (designer, _) in enumerate(top_20, 1):
    qid = cerca_qid_designer(designer)
    mappa_designer_qid[designer] = qid

qid_validi = [q for q in mappa_designer_qid.values() if q]
scarica_entita_batch(qid_validi)

qid_collegati = []
for qid in qid_validi:
    ent = cache_entita.get(qid, {})
    for prop in ("P19", "P740", "P159", "P937", "P108", "P27"):
        qid_collegati.extend(estrai_qid_proprieta(ent, prop, solo_attuali=(prop == "P27")))
scarica_entita_batch(qid_collegati)

qid_paesi = []
for qid_luogo in qid_collegati:
    ent_luogo = cache_entita.get(qid_luogo, {})
    qid_paesi.extend(estrai_qid_proprieta(ent_luogo, "P17", solo_attuali=True))
scarica_entita_batch(qid_paesi)

# 3. Elaborazione a blocchi di 5 designer alla volta con aggiornamento progressivo del JSON
print("\n2. Elaborazione a blocchi di 5 designer e aggiornamento progressivo del file JSON...")
archivio_json_progressivo = []
salva_json_progressivo(archivio_json_progressivo, output_json)

dimensione_blocco = 5
for indice_inizio in range(0, len(top_20), dimensione_blocco):
    sotto_lista = top_20[indice_inizio:indice_inizio + dimensione_blocco]
    num_blocco = (indice_inizio // dimensione_blocco) + 1
    tot_blocchi = (len(top_20) + dimensione_blocco - 1) // dimensione_blocco

    print(f"\n   --- Blocco {num_blocco}/{tot_blocchi} (designer {indice_inizio + 1}-{indice_inizio + len(sotto_lista)}) ---")

    blocco_preparato = []
    for offset, (designer, num_abiti) in enumerate(sotto_lista):
        pos = indice_inizio + offset + 1
        print(f"   [{pos:2d}/20] Acquisizione biografia web: {designer}...")
        info_base = prepara_dati_base_designer(pos, designer, num_abiti, mappa_designer_qid.get(designer))
        blocco_preparato.append(info_base)

    # Analisi collettiva dei 5 designer tramite LLM
    print(f"   -> Invio blocco {num_blocco} di 5 designer all'LLM per verifica e sintesi...")
    risultati_llm = interroga_llm_blocco_5(blocco_preparato)

    # Unione dei risultati e aggiornamento immediato del file JSON
    for info in blocco_preparato:
        chiave_d = info["designer"].strip().lower()
        dati_llm = risultati_llm.get(chiave_d, {})

        luogo_nascita = pulisci_luogo_nascita(dati_llm.get("luogo_nascita") or info["nascita_base"]) or "Non disponibile"
        luogo_attivita = (dati_llm.get("luogo_attivita") or info["attivita_base"] or "Non disponibile").strip()
        periodo_grezzo = (dati_llm.get("periodo_attivita") or info["periodo_base"] or "Non disponibile").strip()
        periodo_finale = normalizza_periodo_output(periodo_grezzo)

        record_designer = {
            "posizione": info["posizione"],
            "designer": info["designer"],
            "abiti_archivio": info["abiti"],
            "luogo_nascita": luogo_nascita,
            "luogo_attivita": luogo_attivita,
            "periodo_attivita": periodo_finale
        }
        archivio_json_progressivo.append(record_designer)

    # Aggiornamento su disco del file JSON dopo ogni gruppo di 5 designer
    salva_json_progressivo(archivio_json_progressivo, output_json)
    print(f"   [OK] File JSON aggiornato su Desktop ({len(archivio_json_progressivo)}/20 designer salvati).")

    # Pausa di sicurezza tra un blocco da 5 e il successivo
    if indice_inizio + dimensione_blocco < len(top_20):
        time.sleep(3.0)

# 4. Stampa riepilogo finale nella IDLE Shell
intestazioni = ["#", "Designer", "Abiti", "Luogo di nascita", "Luogo di attività (Nazione)", "Periodo di attività"]
print("\n" + "=" * 124)
print(f"{intestazioni[0]:<3} | {intestazioni[1]:<24} | {intestazioni[2]:<5} | {intestazioni[3]:<30} | {intestazioni[4]:<24} | {intestazioni[5]}")
print("-" * 124)

righe_tabella = []
for rec in archivio_json_progressivo:
    r = [
        str(rec["posizione"]),
        rec["designer"],
        str(rec["abiti_archivio"]),
        rec["luogo_nascita"],
        rec["luogo_attivita"],
        rec["periodo_attivita"]
    ]
    righe_tabella.append(r)
    print(f"{r[0]:<3} | {r[1]:<24} | {r[2]:<5} | {r[3]:<30} | {r[4]:<24} | {r[5]}")
print("=" * 124)

# 5. Salvataggio anche in CSV e immagine PNG sincronizzati con il JSON
with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(intestazioni)
    writer.writerows(righe_tabella)

dati_per_figura = []
for r in righe_tabella:
    dati_per_figura.append([
        r[0],
        textwrap.fill(r[1], width=24),
        r[2],
        textwrap.fill(r[3], width=28),
        textwrap.fill(r[4], width=22),
        textwrap.fill(r[5], width=22)
    ])

fig, ax = plt.subplots(figsize=(16.5, 13.5))
ax.axis("off")

tabella = ax.table(
    cellText=dati_per_figura,
    colLabels=["#", "Designer", "Abiti", "Luogo di nascita", "Luogo di attività\n(Nazione)", "Periodo di attività"],
    loc="center",
    cellLoc="left",
    colWidths=[0.035, 0.20, 0.055, 0.26, 0.22, 0.23]
)

tabella.auto_set_font_size(False)
tabella.set_fontsize(9)
tabella.scale(1, 2.25)

for (row, col), cell in tabella.get_celld().items():
    cell.set_edgecolor("#CCCCCC")
    if row == 0:
        cell.set_facecolor("#1f4e78")
        cell.get_text().set_color("white")
        cell.get_text().set_weight("bold")
    elif row % 2 == 1:
        cell.set_facecolor("#f4f7fa")
    else:
        cell.set_facecolor("#ffffff")

ax.set_title("I 20 Designer più frequenti dell'archivio: biografia e carriera", fontsize=15, fontweight="bold", pad=15)
plt.tight_layout()
plt.savefig(output_png, dpi=300, bbox_inches="tight")
plt.close()

print(f"\nTutti e 20 i designer sono stati salvati con successo:")
print(f"  1. JSON progressivo:        {output_json}")
print(f"  2. CSV (per Excel/Numbers): {output_csv}")
print(f"  3. Immagine PNG:            {output_png}")
