import csv
import json
import os
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
import matplotlib.pyplot as plt

# Percorsi dei file sul Desktop del Mac
input_csv = "/Users/giulia/Desktop/evening_dresses_arricchito.csv"
output_img = "/Users/giulia/Desktop/indossatrici_e_occasioni_francia_1950_1969.png"
output_json = "/Users/giulia/Desktop/analisi_indossatrici_francia_1950_1969.json"

# Endpoint LLM gratuito (oppure OpenAI se è configurata la variabile OPENAI_API_KEY)
LLM_FREE_URL = "https://text.pollinations.ai/openai"

HEADERS = {
    "User-Agent": "ArchivioModaRicerca/1.0 (https://collections.vam.ac.uk; studio@example.org) Python-urllib/3"
}

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


def nel_periodo_1950_1969(data_str):
    """Restituisce True se almeno un anno nella datazione rientra tra il 1950 e il 1969."""
    if not data_str:
        return False
    anni = [int(a) for a in re.findall(r"\b(1[789]\d\d|20\d\d)s?\b", str(data_str), flags=re.IGNORECASE)]
    return any(1950 <= a <= 1969 for a in anni)


def normalizza_ruolo(ruolo_str):
    """Uniforma in italiano le categorie di posizione sociale, ruolo o professione."""
    if not ruolo_str:
        return "Non specificato"
    r = ruolo_str.strip().lower()

    if any(k in r for k in ("aristocra", "nobilt", "principess", "duchess", "contess", "lady", "reale", "royal")):
        return "Aristocrazia e Nobiltà"
    if any(k in r for k in ("spettacolo", "cinema", "teatro", "attric", "cantant", "ballerin", "music", "artista")):
        return "Cinema, Teatro e Spettacolo"
    if any(k in r for k in ("moda", "giornalis", "modell", "editor", "fotograf", "stilist")):
        return "Moda e Giornalismo"
    if any(k in r for k in ("diplomaz", "politic", "ambasciat", "minist")):
        return "Diplomazia e Politica"
    if any(k in r for k in ("borghes", "socialite", "collezionist", "client", "privata", "ereditier")):
        return "Alta borghesia e Socialite"
    if any(k in r for k in ("non specificat", "ignot", "sconosciut", "n/a", "none", "nessun")):
        return "Non specificato"
    return ruolo_str.strip().capitalize()


def normalizza_occasione(occ_str):
    """Uniforma in italiano le categorie delle occasioni d'uso."""
    if not occ_str:
        return "Non specificata"
    o = occ_str.strip().lower()

    if any(k in o for k in ("ballo", "gala", "debutt")):
        return "Ballo e Serata di gala"
    if any(k in o for k in ("corte", "ufficiale", "ricevimento", "stato", "ambasciata", "incoronaz")):
        return "Ricevimento ufficiale / Corte"
    if any(k in o for k in ("opera", "teatro", "prima", "concerto", "spettacolo")):
        return "Teatro, Opera e Prime"
    if any(k in o for k in ("cena", "cocktail", "party", "festa", "banchetto", "ricevimento privato")):
        return "Cena formale e Cocktail"
    if any(k in o for k in ("matrimonio", "cerimonia", "nozze", "sposa")):
        return "Cerimonia e Matrimonio"
    if any(k in o for k in ("sfilata", "esposizione", "mostra", "collezione")):
        return "Sfilata / Esposizione"
    if any(k in o for k in ("non specificat", "ignot", "sconosciut", "n/a", "none", "nessun")):
        return "Non specificata"
    return occ_str.strip().capitalize()


def analisi_fallback_locale(storia_en, riassunto_en=""):
    """Classificatore locale di riserva in italiano se il servizio LLM esterno non risponde."""
    t = f"{storia_en} {riassunto_en}".lower()

    # 1. Posizione sociale / ruolo / professione
    if any(k in t for k in (
        "princess", "queen", "duchess", "countess", "lady ", "baroness",
        "viscountess", "marchioness", "hon.", "honourable", "aristocrat", "lord "
    )):
        ruolo = "Aristocrazia e Nobiltà"
    elif any(k in t for k in (
        "actress", "actor", "singer", "dancer", "ballerina", "theatre",
        "theater", "film", "cinema", "stage", "performer", "musician"
    )):
        ruolo = "Cinema, Teatro e Spettacolo"
    elif any(k in t for k in (
        "model", "fashion editor", "vogue", "harper's bazaar", "journalist",
        "designer", "couturier", "stylist", "photographer"
    )):
        ruolo = "Moda e Giornalismo"
    elif any(k in t for k in ("ambassador", "diplomat", "embassy", "minister", "politician", "wife of the", "consort")):
        ruolo = "Diplomazia e Politica"
    elif any(k in t for k in (
        "mrs ", "miss ", "worn by", "donated by", "given by", "bequeathed by",
        "client", "private collector", "socialite", "debutante"
    )):
        ruolo = "Alta borghesia e Socialite"
    else:
        ruolo = "Non specificato"

    # 2. Occasione d'uso
    if any(k in t for k in ("ball", "gala", "charity ball", "debutante", "coming out", "queen charlotte")):
        occasione = "Ballo e Serata di gala"
    elif any(k in t for k in (
        "royal", "palace", "buckingham", "state visit", "embassy",
        "reception", "presentation at court", "coronation", "investiture"
    )):
        occasione = "Ricevimento ufficiale / Corte"
    elif any(k in t for k in ("opera", "theatre", "theater", "premiere", "first night", "concert", "covent garden", "glyndebourne")):
        occasione = "Teatro, Opera e Prime"
    elif any(k in t for k in ("dinner", "cocktail", "party", "supper", "banquet", "soirée", "soiree")):
        occasione = "Cena formale e Cocktail"
    elif any(k in t for k in ("wedding", "marriage", "bride", "bridesmaid", "ceremony")):
        occasione = "Cerimonia e Matrimonio"
    elif any(k in t for k in ("catwalk", "runway", "fashion show", "collection", "exhibition", "cecil beaton")):
        occasione = "Sfilata / Esposizione"
    else:
        occasione = "Non specificata"

    # 3. Estrazione eventuale nome proprio associato a "Worn by" / "Made for"
    nome_trovato = ""
    pattern_nome = re.compile(
        r"(?i:worn by|made for|commissioned by)\s+(?i:the\s+(?:actress|singer|dancer|socialite|model)\s+)?"
        r"([A-Z][a-zA-Z'.-]+(?:\s+(?:of|de|du|von|van)\s+[A-Z][a-zA-Z'.-]+|\s+[A-Z][a-zA-Z'.-]+){1,3})"
    )
    match_nome = pattern_nome.search(storia_en)
    if match_nome:
        nome_trovato = match_nome.group(1).strip()

    return ruolo, occasione, nome_trovato


def analizza_blocco_con_llm(blocco_schede):
    """
    Invia un blocco di schede all'LLM per estrarre e tradurre in italiano:
    - posizione sociale / ruolo / professione di chi indossava l'abito
    - occasione d'uso più frequente
    - eventuale nome proprio se esplicitamente indicato nella scheda
    """
    righe_prompt = []
    for item in blocco_schede:
        testo = item["testo"][:650]
        righe_prompt.append(f'ID {item["id"]}: "{testo}"')

    prompt = (
        "Analizza queste schede museali in inglese relative ad abiti da sera francesi (1950-1969).\n"
        "Per ciascun ID, individua CHI indossava l'abito (ruolo/posizione sociale/professione) e in QUALE occasione, "
        "riportando tutto in LINGUA ITALIANA.\n"
        "Restituisci ESCLUSIVAMENTE un oggetto JSON valido in cui ogni chiave è l'ID numerico come stringa "
        "e il valore è un oggetto con 3 chiavi:\n"
        '- "ruolo_sociale": scegli una categoria tra: '
        '"Aristocrazia e Nobiltà", "Alta borghesia e Socialite", "Cinema, Teatro e Spettacolo", '
        '"Moda e Giornalismo", "Diplomazia e Politica", oppure "Non specificato" se il testo non indica chi lo indossava.\n'
        '- "occasione": scegli una categoria tra: '
        '"Ballo e Serata di gala", "Ricevimento ufficiale / Corte", "Teatro, Opera e Prime", '
        '"Cena formale e Cocktail", "Cerimonia e Matrimonio", "Sfilata / Esposizione", oppure "Non specificata".\n'
        '- "nome_persona": il nome proprio della donna che ha indossato l\'abito (es. "Lady Caroline Paget", "Vivien Leigh") '
        'SOLO SE esplicitamente indicato come indossatrice o committente, altrimenti stringa vuota "".\n\n'
        "SCHEDE DA ANALIZZARE:\n" + "\n".join(righe_prompt)
    )

    payload = json.dumps({
        "model": "openai",
        "messages": [
            {"role": "system", "content": "Sei uno storico della moda e del costume. Rispondi solo con JSON puro."},
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
    col_storia = next((c for c in fieldnames if c.strip().lower() == "storia dell'oggetto"), None)
    col_riassunto = next((c for c in fieldnames if c.strip().lower() == "riassunto"), None)
    col_designer = next((c for c in fieldnames if "designer" in c.strip().lower()), None)
    col_acc = next((c for c in fieldnames if "accessione" in c.strip().lower()), None)

    if not col_stato or not col_data or not col_storia:
        print("Errore: verifica che nel CSV esistano le colonne 'Stato', 'Datazione' e 'Storia dell'oggetto'.")
        exit()

    abiti_filtrati = []
    for row in reader:
        stato = (row.get(col_stato) or "").strip()
        datazione = (row.get(col_data) or "").strip()

        if stato.lower() == "francia" and nel_periodo_1950_1969(datazione):
            storia = (row.get(col_storia) or "").strip()
            riassunto = (row.get(col_riassunto) or "").strip() if col_riassunto else ""
            testo_combinato = f"Object history: {storia} | Summary: {riassunto}".strip()

            abiti_filtrati.append({
                "id": str(len(abiti_filtrati)),
                "accessione": (row.get(col_acc) or "").strip() if col_acc else "",
                "designer": (row.get(col_designer) or "").strip() if col_designer else "",
                "datazione": datazione,
                "storia_originale": storia,
                "riassunto_originale": riassunto,
                "testo": testo_combinato
            })

totale_abiti = len(abiti_filtrati)
print(f"Abiti francesi (1950-1969) individuati nel catalogo: {totale_abiti}")

if totale_abiti == 0:
    print("Nessun abito trovato con i criteri richiesti.")
    exit()

# 2. Analisi a blocchi di 10 abiti tramite LLM (con fallback locale automatico)
conteggio_ruoli = Counter()
conteggio_occasioni = Counter()
conteggio_nomi = Counter()
risultati_dettagliati = []

dimensione_blocco = 10
print("\nAvvio analisi delle schede per posizione sociale, occasioni d'uso e figure citate...")

for i in range(0, totale_abiti, dimensione_blocco):
    blocco = abiti_filtrati[i:i + dimensione_blocco]
    num_blocco = (i // dimensione_blocco) + 1
    tot_blocchi = (totale_abiti + dimensione_blocco - 1) // dimensione_blocco

    print(f"  Elaborazione blocco {num_blocco}/{tot_blocchi} ({len(blocco)} abiti)...")
    risultati_llm = analizza_blocco_con_llm(blocco)

    for item in blocco:
        dati_item = risultati_llm.get(item["id"])

        if isinstance(dati_item, dict) and dati_item:
            ruolo = normalizza_ruolo(dati_item.get("ruolo_sociale", ""))
            occasione = normalizza_occasione(dati_item.get("occasione", ""))
            nome_p = (dati_item.get("nome_persona") or "").strip()
        else:
            ruolo, occasione, nome_p = analisi_fallback_locale(item["storia_originale"], item["riassunto_originale"])

        conteggio_ruoli[ruolo] += 1
        conteggio_occasioni[occasione] += 1

        if nome_p and nome_p.lower() not in {"unknown", "none", "n/a", "non specificato"}:
            conteggio_nomi[nome_p] += 1

        risultati_dettagliati.append({
            "numero_accessione": item["accessione"],
            "designer": item["designer"],
            "datazione": item["datazione"],
            "posizione_sociale_ruolo": ruolo,
            "occasione_uso": occasione,
            "persona_citata": nome_p,
            "storia_oggetto_en": item["storia_originale"]
        })

    if i + dimensione_blocco < totale_abiti:
        time.sleep(2.5)

# Salvataggio del dettaglio strutturato in JSON
with open(output_json, "w", encoding="utf-8") as f:
    json.dump(risultati_dettagliati, f, ensure_ascii=False, indent=2)

# Selezione delle SOLE figure che compaiono PIÙ DI 3 VOLTE (qta > 3)
figure_ricorrenti = [(nome, qta) for nome, qta in conteggio_nomi.most_common() if qta > 3]

# Stampa riepilogo nella IDLE Shell
print("\n" + "=" * 68)
print("POSIZIONE SOCIALE, RUOLO O PROFESSIONE (FRANCIA, 1950-1969)")
print("=" * 68)
for ruolo, qta in conteggio_ruoli.most_common():
    print(f"  - {ruolo:<32}: {qta:3d} abiti ({qta/totale_abiti*100:.1f}%)")

print("\n" + "=" * 68)
print("OCCASIONI D'USO PIÙ FREQUENTI")
print("=" * 68)
for occ, qta in conteggio_occasioni.most_common():
    print(f"  - {occ:<32}: {qta:3d} abiti ({qta/totale_abiti*100:.1f}%)")

if figure_ricorrenti:
    print("\n" + "=" * 68)
    print("FIGURE PIÙ RICORRENTI CITATE NELLE SCHEDE (> 3 ABITI)")
    print("=" * 68)
    for nome, qta in figure_ricorrenti:
        print(f"  - {nome:<32}: {qta:3d} abiti")

# 3. Creazione del grafico con Matplotlib
# Il riquadro inferiore viene inserito SOLO se esistono figure con più di 3 ricorrenze
if figure_ricorrenti:
    fig = plt.figure(figsize=(17.5, 10.5))
    gs = fig.add_gridspec(2, 2, height_ratios=[3.3, 1.15], hspace=0.35, wspace=0.62)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, :])
else:
    fig = plt.figure(figsize=(17.5, 7.5))
    gs = fig.add_gridspec(1, 2, wspace=0.62)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = None

# Pannello sinistro: Posizione sociale / ruolo / professione
items_r = list(reversed(conteggio_ruoli.most_common()))
labels_r = [k for k, _ in items_r]
vals_r = [v for _, v in items_r]
colors_r = ["#B0BEC5" if "non specificat" in k.lower() else "#1f4e78" for k in labels_r]

bars1 = ax1.barh(labels_r, vals_r, color=colors_r, edgecolor="white", height=0.62)
max_r = max(vals_r) if vals_r else 1
for b, v in zip(bars1, vals_r):
    ax1.text(
        v + max_r * 0.02,
        b.get_y() + b.get_height() / 2,
        f"{v} ({v/totale_abiti*100:.1f}%)",
        va="center",
        fontsize=9,
        fontweight="bold"
    )
ax1.set_xlim(0, max_r * 1.26)
ax1.set_title("Posizione sociale, ruolo o professione", fontsize=12.5, fontweight="bold", pad=12)
ax1.set_xlabel("Numero di abiti", fontsize=10, fontweight="bold")
ax1.grid(axis="x", linestyle="--", alpha=0.45)
ax1.set_axisbelow(True)

# Pannello destro: Occasioni più frequenti
items_o = list(reversed(conteggio_occasioni.most_common()))
labels_o = [k for k, _ in items_o]
vals_o = [v for _, v in items_o]
colors_o = ["#B0BEC5" if "non specificat" in k.lower() else "#2e7d32" for k in labels_o]

bars2 = ax2.barh(labels_o, vals_o, color=colors_o, edgecolor="white", height=0.62)
max_o = max(vals_o) if vals_o else 1
for b, v in zip(bars2, vals_o):
    ax2.text(
        v + max_o * 0.02,
        b.get_y() + b.get_height() / 2,
        f"{v} ({v/totale_abiti*100:.1f}%)",
        va="center",
        fontsize=9,
        fontweight="bold"
    )
ax2.set_xlim(0, max_o * 1.26)
ax2.set_title("Occasioni d'uso più frequenti", fontsize=12.5, fontweight="bold", pad=12)
ax2.set_xlabel("Numero di abiti", fontsize=10, fontweight="bold")
ax2.grid(axis="x", linestyle="--", alpha=0.45)
ax2.set_axisbelow(True)

# Riquadro inferiore: mostrato SOLO se ci sono figure con più di 3 abiti
if ax3 is not None:
    ax3.axis("off")
    nomi_str = "   |   ".join([
        f"• {nome} ({qta} abiti)"
        for nome, qta in figure_ricorrenti[:6]
    ])
    testo_riquadro = (
        f"FIGURE PIÙ RICORRENTI CITATE NELLE SCHEDE (> 3 abiti, su {totale_abiti} abiti francesi 1950–1969):\n\n"
        f"{nomi_str}"
    )
    ax3.text(
        0.5, 0.5,
        testo_riquadro,
        ha="center",
        va="center",
        fontsize=10.5,
        bbox=dict(boxstyle="round,pad=0.8", facecolor="#f4f7fa", edgecolor="#1f4e78", linewidth=1.2)
    )

fig.suptitle(
    "Chi indossava gli abiti da sera francesi (1950–1969): profilo sociale e occasioni d'uso",
    fontsize=15,
    fontweight="bold",
    y=0.98 if ax3 is not None else 1.02
)

# 4. Salvataggio immagine sul Desktop
plt.savefig(output_img, dpi=300, bbox_inches="tight")
plt.close()

print(f"\nAnalisi completata con successo! File salvati sul Desktop:")
print(f"  1. Grafico PNG:    {output_img}")
print(f"  2. Dettaglio JSON: {output_json}")
