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
input_csv = "/Users/giulia/Desktop/evening_dresses_arricchito.csv"
output_img = "/Users/giulia/Desktop/materiali_francia_1950_1969.png"

# Endpoint LLM gratuito (oppure OpenAI se è impostata la variabile d'ambiente OPENAI_API_KEY)
LLM_FREE_URL = "https://text.pollinations.ai/openai"

HEADERS = {
    "User-Agent": "ArchivioModaRicerca/1.0 (https://collections.vam.ac.uk; studio@example.org) Python-urllib/3"
}

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Dizionario di traduzione tessile EN -> IT (usato per uniformare i termini e come riserva offline)
DIZIONARIO_MATERIALI_IT = {
    "silk": "Seta",
    "satin": "Raso",
    "tulle": "Tulle",
    "net": "Tulle / Rete",
    "velvet": "Velluto",
    "lace": "Pizzo",
    "chiffon": "Chiffon",
    "organza": "Organza",
    "taffeta": "Taffetà",
    "faille": "Faille",
    "crepe": "Crêpe",
    "crêpe": "Crêpe",
    "georgette": "Georgette",
    "muslin": "Mussola",
    "cotton": "Cotone",
    "wool": "Lana",
    "linen": "Lino",
    "nylon": "Nylon",
    "rayon": "Rayon",
    "polyester": "Poliestere",
    "acetate": "Acetato",
    "viscose": "Viscosa",
    "brocade": "Brocato",
    "jacquard": "Jacquard",
    "damask": "Damasco",
    "lamé": "Lamé",
    "lame": "Lamé",
    "sequin": "Paillettes / Lustrini",
    "sequins": "Paillettes / Lustrini",
    "bead": "Perline",
    "beads": "Perline",
    "rhinestone": "Strass",
    "rhinestones": "Strass",
    "crystal": "Cristalli",
    "crystals": "Cristalli",
    "pearl": "Perle",
    "pearls": "Perle",
    "feather": "Piume",
    "feathers": "Piume",
    "fur": "Pelliccia",
    "leather": "Pelle",
    "metallic thread": "Filo metallico",
    "metal thread": "Filo metallico",
    "plastic": "Plastica",
    "boning": "Stecche",
}


def nel_periodo_1950_1969(data_str):
    """Verifica se la datazione dell'abito rientra tra il 1950 e il 1969 (inclusi)."""
    if not data_str:
        return False
    anni = [int(a) for a in re.findall(r"\b(1[789]\d\d|20\d\d)s?\b", str(data_str), flags=re.IGNORECASE)]
    if not anni:
        return False
    if len(anni) == 1:
        return 1950 <= anni[0] <= 1969
    anno_min, anno_max = min(anni), max(anni)
    anno_medio = (anno_min + anno_max) / 2
    return (1950 <= anno_medio <= 1969) or (anno_min >= 1950 and anno_max <= 1969)


def normalizza_etichetta_italiana(termine):
    """Uniforma la traduzione italiana dei materiali per evitare sinonimi frammentati."""
    if not termine:
        return ""
    t = termine.strip().capitalize()
    t_low = t.lower()

    mappa_sinonimi = {
        "sequins": "Paillettes / Lustrini",
        "paillettes": "Paillettes / Lustrini",
        "lustrini": "Paillettes / Lustrini",
        "taffeta": "Taffetà",
        "taffeta'": "Taffetà",
        "crepe": "Crêpe",
        "lame": "Lamé",
        "rete": "Tulle / Rete",
        "merletto": "Pizzo",
        "pizzo / merletto": "Pizzo",
        "raso di seta": "Raso",
        "satin": "Raso",
    }
    return mappa_sinonimi.get(t_low, t)


def estrai_materiali_fallback(testo_en):
    """Estrae e traduce in italiano i materiali dal testo inglese (riserva se l'LLM è occupato)."""
    trovati = []
    t_low = testo_en.lower()
    for en_term, it_label in DIZIONARIO_MATERIALI_IT.items():
        if re.search(rf"\b{re.escape(en_term)}\b", t_low):
            if it_label not in trovati:
                trovati.append(it_label)
    return trovati


def analizza_blocco_con_llm(blocco_abiti):
    """
    Invia un blocco di descrizioni inglesi all'LLM chiedendo di estrarre
    i materiali principali di ciascun abito tradotti in italiano.
    """
    righe_prompt = []
    for item in blocco_abiti:
        testo_pulito = item["testo"][:450]
        righe_prompt.append(f'ID {item["id"]}: "{testo_pulito}"')

    prompt = (
        "Analizza queste descrizioni tecniche in inglese di abiti da sera francesi (1950-1969). "
        "Per ciascun ID, estrai l'elenco dei principali materiali tessili e decorativi utilizzati "
        "(es. Seta, Tulle, Raso, Velluto, Pizzo, Organza, Taffetà, Chiffon, Crêpe, Cotone, Nylon, "
        "Paillettes / Lustrini, Perline, Strass, Brocato, Lamé, Piume, Lana), TRADOTTI IN ITALIANO.\n"
        "Restituisci ESCLUSIVAMENTE un oggetto JSON valido in cui le chiavi sono gli ID numerici "
        'come stringhe e i valori sono liste di materiali in italiano (es. {"0": ["Seta", "Tulle"], "1": ["Raso", "Perline"]}).\n\n'
        "TESTI DA ANALIZZARE:\n" + "\n".join(righe_prompt)
    )

    payload = json.dumps({
        "model": "openai",
        "messages": [
            {"role": "system", "content": "Sei un esperto di tessuti e storia della moda. Rispondi solo con JSON puro."},
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
                match = re.search(r"\{[\s\S]*\}", testo)
                if match:
                    return json.loads(match.group(0))
        except Exception:
            time.sleep(2.0 * (tentativo + 1))

    return {}


# --- ESECUZIONE PRINCIPALE ---

# 1. Lettura del CSV arricchito e filtraggio per Stato = Francia e Datazione 1950-1969
with open(input_csv, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames

    col_stato = next((c for c in fieldnames if c.strip().lower() == "stato"), None)
    col_data = next((c for c in fieldnames if c.strip().lower() == "datazione"), None)
    col_mat = next((c for c in fieldnames if c.strip().lower() == "materiali"), None)

    if not col_stato or not col_data or not col_mat:
        print("Errore: verifica che nel CSV esistano le colonne 'Stato', 'Datazione' e 'Materiali'.")
        exit()

    abiti_filtrati = []
    for idx, row in enumerate(reader):
        stato = (row.get(col_stato) or "").strip()
        datazione = (row.get(col_data) or "").strip()
        materiali_testo = (row.get(col_mat) or "").strip()

        if stato.lower() == "francia" and nel_periodo_1950_1969(datazione):
            if materiali_testo:
                abiti_filtrati.append({
                    "id": str(len(abiti_filtrati)),
                    "testo": materiali_testo
                })

totale_abiti_francia = len(abiti_filtrati)
print(f"Abiti trovati per Stato='Francia' e Datazione 1950-1969 con materiali valorizzati: {totale_abiti_francia}")

if totale_abiti_francia == 0:
    print("Nessun abito trovato con i criteri richiesti.")
    exit()

# 2. Analisi tramite LLM a blocchi di 12 abiti per estrarre e tradurre i materiali in italiano
conteggio_materiali = Counter()
dimensione_blocco = 12

print("\nAvvio analisi dei materiali tramite LLM e traduzione in italiano...")

for i in range(0, totale_abiti_francia, dimensione_blocco):
    blocco = abiti_filtrati[i:i + dimensione_blocco]
    num_blocco = (i // dimensione_blocco) + 1
    tot_blocchi = (totale_abiti_francia + dimensione_blocco - 1) // dimensione_blocco

    print(f"  Elaborazione blocco {num_blocco}/{tot_blocchi} ({len(blocco)} abiti)...")
    risultati_llm = analizza_blocco_con_llm(blocco)

    for item in blocco:
        lista_mat = risultati_llm.get(item["id"])
        # Se l'LLM non ha risposto su questo elemento, attiva l'estrazione/traduzione di riserva
        if not isinstance(lista_mat, list) or not lista_mat:
            lista_mat = estrai_materiali_fallback(item["testo"])

        # Evita duplicati sullo stesso abito e normalizza il nome italiano
        materiali_unici_abito = set()
        for m in lista_mat:
            if isinstance(m, str) and m.strip():
                nome_it = normalizza_etichetta_italiana(m)
                if nome_it:
                    materiali_unici_abito.add(nome_it)

        for mat in materiali_unici_abito:
            conteggio_materiali[mat] += 1

    if i + dimensione_blocco < totale_abiti_francia:
        time.sleep(2.5)

if not conteggio_materiali:
    print("Impossibile estrarre materiali dai testi analizzati.")
    exit()

# Stampa riepilogo dei risultati nella IDLE Shell
print("\n" + "=" * 60)
print("MATERIALI PIÙ UTILIZZATI (FRANCIA, 1950-1969)")
print("=" * 60)
for mat, qta in conteggio_materiali.most_common():
    print(f"  - {mat:<26}: {qta:3d} abiti")
print("=" * 60)

# 3. Preparazione dei dati per il grafico a torta (Top 8 materiali + "Altro")
top_n = 8
piu_frequenti = conteggio_materiali.most_common(top_n)
altri = conteggio_materiali.most_common()[top_n:]

etichette = [m for m, _ in piu_frequenti]
valori = [c for _, c in piu_frequenti]

if altri:
    somma_altri = sum(c for _, c in altri)
    etichette.append("Altro")
    valori.append(somma_altri)

totale_occorrenze = sum(valori)
palette = list(plt.cm.tab20.colors)
colori = [palette[i % len(palette)] for i in range(len(etichette))]
if altri:
    colori[-1] = "#B0BEC5"  # Grigio neutro per "Altro"

# 4. Creazione del grafico a torta con Matplotlib
fig, ax = plt.subplots(figsize=(14, 8.5))

wedges, texts, autotexts = ax.pie(
    valori,
    labels=None,
    autopct=lambda pct: f"{pct:.1f}%" if pct >= 3.0 else "",
    pctdistance=0.75,
    startangle=140,
    colors=colori,
    wedgeprops={"edgecolor": "white", "linewidth": 1.2},
    textprops={"fontsize": 9.5, "fontweight": "bold", "color": "#111111"}
)

# Legenda dettagliata in italiano
etichette_legenda = []
for nome, qta in piu_frequenti:
    pct = (qta / totale_occorrenze) * 100
    etichette_legenda.append(f"{nome} ({qta} | {pct:.1f}%)")

if altri:
    somma_altri = sum(c for _, c in altri)
    pct_altri = (somma_altri / totale_occorrenze) * 100
    dettagli_altri = ", ".join([f"{m} ({c})" for m, c in altri])
    dettagli_wrappati = textwrap.fill(dettagli_altri, width=48)
    etichette_legenda.append(f"Altro ({somma_altri} | {pct_altri:.1f}%):\n  • {dettagli_wrappati}")

ax.legend(
    wedges,
    etichette_legenda,
    title=f"Materiali individuati (su {totale_abiti_francia} abiti)",
    loc="center left",
    bbox_to_anchor=(1.02, 0.5),
    fontsize=9.5,
    title_fontsize=11
)

ax.set_title(
    "Materiali più utilizzati negli abiti da sera francesi (1950–1969)",
    fontsize=15,
    fontweight="bold",
    pad=20
)

# 5. Salvataggio del grafico sul Desktop
plt.tight_layout()
plt.savefig(output_img, dpi=300, bbox_inches="tight")
plt.close()

print(f"\nGrafico a torta generato e salvato con successo in:\n{output_img}")
