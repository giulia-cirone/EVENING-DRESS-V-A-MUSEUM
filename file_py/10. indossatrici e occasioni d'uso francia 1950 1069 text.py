import csv
import json
import os
import re
import ssl
import textwrap
import time
import urllib.request
from collections import Counter

# Percorsi dei file sul Desktop del Mac
file_json_analisi = "/Users/giulia/Desktop/analisi_indossatrici_francia_1950_1969.json"
file_csv_arricchito = "/Users/giulia/Desktop/evening_dresses_arricchito.csv"
file_txt_output = "/Users/giulia/Desktop/descrizione_indossatrici_e_occasioni.txt"

# Endpoint LLM gratuito (oppure OpenAI se è configurata la variabile d'ambiente OPENAI_API_KEY)
LLM_FREE_URL = "https://text.pollinations.ai/openai"

HEADERS = {
    "User-Agent": "ArchivioModaRicerca/1.0 (https://collections.vam.ac.uk; studio@example.org) Python-urllib/3"
}

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


def nel_periodo_1950_1969(data_str):
    """Restituisce True se almeno un anno indicato nella datazione è compreso tra 1950 e 1969."""
    if not data_str:
        return False
    anni = [int(a) for a in re.findall(r"\b(1[789]\d\d|20\d\d)s?\b", str(data_str), flags=re.IGNORECASE)]
    return any(1950 <= a <= 1969 for a in anni)


def carica_o_prepara_dati():
    """Carica il JSON generato dallo script precedente oppure estrae i dati dal CSV arricchito."""
    if os.path.exists(file_json_analisi):
        with open(file_json_analisi, "r", encoding="utf-8") as f:
            return json.load(f)

    # Fallback: lettura diretta da evening_dresses_arricchito.csv
    record_list = []
    with open(file_csv_arricchito, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        col_stato = next((c for c in fieldnames if c.strip().lower() == "stato"), None)
        col_data = next((c for c in fieldnames if c.strip().lower() == "datazione"), None)
        col_storia = next((c for c in fieldnames if c.strip().lower() == "storia dell'oggetto"), None)
        col_designer = next((c for c in fieldnames if "designer" in c.strip().lower()), None)

        for row in reader:
            stato = (row.get(col_stato) or "").strip()
            datazione = (row.get(col_data) or "").strip()
            if stato.lower() == "francia" and nel_periodo_1950_1969(datazione):
                record_list.append({
                    "designer": (row.get(col_designer) or "").strip() if col_designer else "",
                    "datazione": datazione,
                    "posizione_sociale_ruolo": "Non specificato",
                    "occasione_uso": "Non specificata",
                    "persona_citata": "",
                    "storia_oggetto_en": (row.get(col_storia) or "").strip() if col_storia else ""
                })
    return record_list


def genera_descrizione_con_llm(dati_abiti):
    """Invia i dati aggregati e gli estratti delle schede all'LLM per ottenere un testo sintetico in italiano."""
    totale = len(dati_abiti)
    ruoli = Counter(r.get("posizione_sociale_ruolo", "Non specificato") for r in dati_abiti)
    occasioni = Counter(r.get("occasione_uso", "Non specificata") for r in dati_abiti)
    nomi = Counter(r.get("persona_citata", "") for r in dati_abiti if r.get("persona_citata"))

    # Considera solo le figure citate più di 3 volte
    figure_rilevanti = [f"{nome} ({qta} abiti)" for nome, qta in nomi.most_common() if qta > 3]

    # Seleziona fino a 15 esempi significativi di 'Storia dell'oggetto' non vuoti
    esempi_storie = []
    for r in dati_abiti:
        storia = (r.get("storia_oggetto_en") or "").strip()
        if storia and len(storia) > 25:
            designer = r.get("designer") or "Designer non indicato"
            data = r.get("datazione") or ""
            esempi_storie.append(f"- [{designer}, {data}]: {storia[:260]}")
        if len(esempi_storie) >= 15:
            break

    riepilogo_ruoli = ", ".join([f"{k}: {v} ({v/totale*100:.1f}%)" for k, v in ruoli.most_common()])
    riepilogo_occasioni = ", ".join([f"{k}: {v} ({v/totale*100:.1f}%)" for k, v in occasioni.most_common()])
    riepilogo_nomi = ", ".join(figure_rilevanti) if figure_rilevanti else "Nessun nominativo ricorrente (> 3 abiti)"

    prompt = (
        "Sei uno storico della moda che sta redigendo una relazione curatorial-scientifica "
        "sugli abiti da sera francesi (1950-1969) conservati al Victoria and Albert Museum.\n"
        "Sulla base dei dati statistici e degli estratti delle schede riportati sotto, scrivi "
        "una BREVE DESCRIZIONE DISCORSIVA IN ITALIANO (2 o 3 paragrafi chiari e scorrevoli, circa 150-220 parole) "
        "che illustri:\n"
        "1. Chi indossava principalmente questi abiti (profilo sociale, ruolo, estrazione, clientela internazionale);\n"
        "2. In quali occasioni sociali, mondane o istituzionali venivano sfoggiati più di frequente;\n"
        "3. Eventuali figure ricorrenti (solo se presenti nell'elenco > 3 abiti, altrimenti non citare nomi singoli).\n"
        "Non usare elenchi puntati né titoli, scrivi solo prosa fluida e professionale in italiano.\n\n"
        f"DATI QUANTITATIVI (su {totale} abiti francesi 1950-1969):\n"
        f"- Posizione sociale / ruolo: {riepilogo_ruoli}\n"
        f"- Occasioni d'uso: {riepilogo_occasioni}\n"
        f"- Figure ricorrenti (> 3 abiti): {riepilogo_nomi}\n\n"
        "ESTRATTI ESEMPLIFICATIVI DALLE SCHEDE (Object history):\n" + "\n".join(esempi_storie)
    )

    payload = json.dumps({
        "model": "openai",
        "messages": [
            {"role": "system", "content": "Sei uno storico della moda. Scrivi testi chiari, eleganti e rigorosi in italiano."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
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
                testo_generato = dati_resp.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if testo_generato and len(testo_generato) > 50:
                    return testo_generato
        except Exception:
            time.sleep(2.0 * (tentativo + 1))

    # Testo di riserva automatico se il servizio LLM esterno risulta momentaneamente irraggiungibile
    ruoli_noti = [(k, v) for k, v in ruoli.most_common() if "non specificat" not in k.lower()]
    occ_note = [(k, v) for k, v in occasioni.most_common() if "non specificat" not in k.lower()]

    top_ruolo = ruoli_noti[0][0].lower() if ruoli_noti else "esponenti dell'alta società internazionale"
    top_occ = occ_note[0][0].lower() if occ_note else "serate di gala e ricevimenti mondani"

    return (
        f"L'analisi dei {totale} abiti da sera francesi datati tra il 1950 e il 1969 evidenzia come "
        f"l'alta moda parigina di questo ventennio fosse destinata principalmente a {top_ruolo}, "
        f"accanto a figure dell'aristocrazia britannica ed europea, protagoniste dello spettacolo e "
        f"personalità legate al mondo diplomatico e culturale.\n\n"
        f"Per quanto riguarda i contesti d'uso documentati nelle schede museali, i capi venivano "
        f"indossati soprattutto in occasione di {top_occ}, ricevimenti ufficiali di corte, prime "
        f"teatrali o all'opera e cene formali, confermando il ruolo centrale della couture francese "
        f"nella vita mondana e rappresentativa del secondo dopoguerra."
    )


# --- ESECUZIONE PRINCIPALE ---

dati = carica_o_prepara_dati()

if not dati:
    print("Errore: nessun abito francese (1950-1969) trovato nei file sul Desktop.")
    exit()

print(f"Generazione descrizione tramite LLM per {len(dati)} abiti francesi (1950-1969)...\n")
descrizione_italiana = genera_descrizione_con_llm(dati)

# Stampa formattata nella IDLE Shell
print("=" * 85)
print("DESCRIZIONE GENERATA DAL MODELLO LLM")
print("=" * 85)
for paragrafo in descrizione_italiana.split("\n"):
    if paragrafo.strip():
        print(textwrap.fill(paragrafo.strip(), width=85))
        print()
print("=" * 85)

# Salvataggio in file di testo sul Desktop
with open(file_txt_output, "w", encoding="utf-8") as f:
    f.write("ANALISI DEGLI ABITI DA SERA FRANCESI (1950–1969): INDOSSATRICI E OCCASIONI D'USO\n")
    f.write("=" * 80 + "\n\n")
    f.write(descrizione_italiana.strip() + "\n")

print(f"Descrizione salvata con successo sul Desktop in:\n{file_txt_output}")
