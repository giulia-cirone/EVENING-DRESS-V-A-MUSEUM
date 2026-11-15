import csv
import json
import os
import re
import ssl
import time
import urllib.request
from collections import Counter
import matplotlib.pyplot as plt

# Percorsi dei file sul Desktop del Mac
file_json_analisi = "/Users/giulia/Desktop/analisi_indossatrici_francia_1950_1969.json"
file_csv_arricchito = "/Users/giulia/Desktop/evening_dresses_arricchito.csv"
output_img = "/Users/giulia/Desktop/confronto tra anni 50 e anni 60.png"

# Endpoint LLM gratuito (oppure OpenAI se è configurata la variabile OPENAI_API_KEY)
LLM_FREE_URL = "https://text.pollinations.ai/openai"

HEADERS = {
    "User-Agent": "ArchivioModaRicerca/1.0 (https://collections.vam.ac.uk; studio@example.org) Python-urllib/3"
}

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


def classifica_decennio(data_str):
    """
    Suddivide le datazioni tra anni '50 (1950-1959) e anni '60 (1960-1969).
    Regola esplicita: se è presente un anno >= 1960 (es. '1959-1960'),
    l'abito viene contato tra quelli degli anni '60.
    """
    if not data_str:
        return None
    anni = [int(a) for a in re.findall(r"\b(1[789]\d\d|20\d\d)s?\b", str(data_str), flags=re.IGNORECASE)]
    if any(1960 <= a <= 1969 for a in anni):
        return "anni_60"
    if any(1950 <= a <= 1959 for a in anni):
        return "anni_50"
    return None


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
    """Classificatore locale di riserva se non si usa il JSON già elaborato."""
    t = f"{storia_en} {riassunto_en}".lower()

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

    return ruolo, occasione


def analizza_blocco_con_llm(blocco_schede):
    """Classifica un blocco di schede tramite LLM restituendo ruolo sociale e occasione in italiano."""
    righe_prompt = [f'ID {item["id"]}: "{item["testo"][:650]}"' for item in blocco_schede]

    prompt = (
        "Analizza queste schede museali in inglese relative ad abiti da sera francesi (1950-1969).\n"
        "Per ciascun ID, individua CHI indossava l'abito e in QUALE occasione in LINGUA ITALIANA.\n"
        "Restituisci ESCLUSIVAMENTE un oggetto JSON valido con chiave = ID stringa e valore = oggetto con 2 chiavi:\n"
        '- "ruolo_sociale": una tra "Aristocrazia e Nobiltà", "Alta borghesia e Socialite", '
        '"Cinema, Teatro e Spettacolo", "Moda e Giornalismo", "Diplomazia e Politica", "Non specificato".\n'
        '- "occasione": una tra "Ballo e Serata di gala", "Ricevimento ufficiale / Corte", '
        '"Teatro, Opera e Prime", "Cena formale e Cocktail", "Cerimonia e Matrimonio", '
        '"Sfilata / Esposizione", "Non specificata".\n\n'
        "SCHEDE:\n" + "\n".join(righe_prompt)
    )

    payload = json.dumps({
        "model": "openai",
        "messages": [
            {"role": "system", "content": "Sei uno storico della moda. Rispondi solo con JSON puro."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1
    }).encode("utf-8")

    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    url_llm = "https://api.openai.com/v1/chat/completions" if openai_key else LLM_FREE_URL
    headers_llm = {"Content-Type": "application/json", "User-Agent": HEADERS["User-Agent"]}
    if openai_key:
        headers_llm["Authorization"] = f"Bearer {openai_key}"

    req = urllib.request.Request(url_llm, data=payload, headers=headers_llm, method="POST")
    for tentativo in range(3):
        try:
            with urllib.request.urlopen(req, context=ssl_context, timeout=35) as resp:
                dati_resp = json.loads(resp.read().decode("utf-8"))
                testo = dati_resp.get("choices", [{}])[0].get("message", {}).get("content", "")
                match = re.search(r"\{[\s\S]*\}", testo)
                if match:
                    return json.loads(match.group(0))
        except Exception:
            time.sleep(2.0 * (tentativo + 1))
    return {}


def carica_record_classificati():
    """Carica i record già classificati dal JSON oppure li elabora dal CSV arricchito."""
    if os.path.exists(file_json_analisi):
        print(f"Caricamento dati già classificati da:\n  {file_json_analisi}")
        with open(file_json_analisi, "r", encoding="utf-8") as f:
            return json.load(f)

    print("File JSON non trovato: avvio analisi diretta da evening_dresses_arricchito.csv...")
    abiti_filtrati = []
    with open(file_csv_arricchito, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        col_stato = next((c for c in fieldnames if c.strip().lower() == "stato"), None)
        col_data = next((c for c in fieldnames if c.strip().lower() == "datazione"), None)
        col_storia = next((c for c in fieldnames if c.strip().lower() == "storia dell'oggetto"), None)
        col_riassunto = next((c for c in fieldnames if c.strip().lower() == "riassunto"), None)

        for row in reader:
            stato = (row.get(col_stato) or "").strip()
            datazione = (row.get(col_data) or "").strip()
            if stato.lower() == "francia" and classifica_decennio(datazione) is not None:
                storia = (row.get(col_storia) or "").strip()
                riassunto = (row.get(col_riassunto) or "").strip() if col_riassunto else ""
                abiti_filtrati.append({
                    "id": str(len(abiti_filtrati)),
                    "datazione": datazione,
                    "storia_originale": storia,
                    "riassunto_originale": riassunto,
                    "testo": f"Object history: {storia} | Summary: {riassunto}".strip()
                })

    risultati = []
    for i in range(0, len(abiti_filtrati), 10):
        blocco = abiti_filtrati[i:i + 10]
        ris_llm = analizza_blocco_con_llm(blocco)
        for item in blocco:
            dati_item = ris_llm.get(item["id"])
            if isinstance(dati_item, dict) and dati_item:
                ruolo = normalizza_ruolo(dati_item.get("ruolo_sociale", ""))
                occ = normalizza_occasione(dati_item.get("occasione", ""))
            else:
                ruolo, occ = analisi_fallback_locale(item["storia_originale"], item["riassunto_originale"])
            risultati.append({
                "datazione": item["datazione"],
                "posizione_sociale_ruolo": ruolo,
                "occasione_uso": occ
            })
        if i + 10 < len(abiti_filtrati):
            time.sleep(2.5)

    return risultati


# --- ESECUZIONE PRINCIPALE ---

record_totali = carica_record_classificati()

ruoli_50 = Counter()
ruoli_60 = Counter()
occ_50 = Counter()
occ_60 = Counter()

for rec in record_totali:
    decennio = classifica_decennio(rec.get("datazione", ""))
    ruolo = normalizza_ruolo(rec.get("posizione_sociale_ruolo", ""))
    occasione = normalizza_occasione(rec.get("occasione_uso", ""))

    if decennio == "anni_50":
        ruoli_50[ruolo] += 1
        occ_50[occasione] += 1
    elif decennio == "anni_60":
        ruoli_60[ruolo] += 1
        occ_60[occasione] += 1

tot_50 = sum(ruoli_50.values())
tot_60 = sum(ruoli_60.values())

if tot_50 == 0 and tot_60 == 0:
    print("Nessun abito francese trovato nei decenni 1950–1959 e 1960–1969.")
    exit()

# Stampa tabella comparativa nella IDLE Shell
print("\n" + "=" * 78)
print(f"CONFRONTO ANNI '50 (N={tot_50}) vs ANNI '60 (N={tot_60}) - POSIZIONE SOCIALE / RUOLO")
print("=" * 78)
for cat in dict.fromkeys(list(ruoli_50.keys()) + list(ruoli_60.keys())):
    c50, c60 = ruoli_50[cat], ruoli_60[cat]
    p50 = (c50 / tot_50 * 100) if tot_50 else 0
    p60 = (c60 / tot_60 * 100) if tot_60 else 0
    print(f"  {cat:<30} | '50: {c50:2d} ({p50:4.1f}%) | '60: {c60:2d} ({p60:4.1f}%)")

print("\n" + "=" * 78)
print(f"CONFRONTO ANNI '50 (N={tot_50}) vs ANNI '60 (N={tot_60}) - OCCASIONI D'USO")
print("=" * 78)
for cat in dict.fromkeys(list(occ_50.keys()) + list(occ_60.keys())):
    c50, c60 = occ_50[cat], occ_60[cat]
    p50 = (c50 / tot_50 * 100) if tot_50 else 0
    p60 = (c60 / tot_60 * 100) if tot_60 else 0
    print(f"  {cat:<30} | '50: {c50:2d} ({p50:4.1f}%) | '60: {c60:2d} ({p60:4.1f}%)")

# Creazione del grafico a barre orizzontali raggruppate con Matplotlib
fig = plt.figure(figsize=(18.5, 9.2))
gs = fig.add_gridspec(1, 2, wspace=0.58)
ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])


def disegna_pannello_confronto(ax, counter_50, counter_60, titolo_pannello, col_50, col_60):
    categorie = list(dict.fromkeys(list(counter_50.keys()) + list(counter_60.keys())))
    # Ordina dal meno frequente al più frequente (così il più frequente è in cima)
    categorie.sort(key=lambda c: counter_50[c] + counter_60[c])

    y_pos = list(range(len(categorie)))
    altezza = 0.36

    vals_50 = [counter_50[c] for c in categorie]
    vals_60 = [counter_60[c] for c in categorie]

    bars_50 = ax.barh(
        [y + altezza / 2 for y in y_pos],
        vals_50,
        height=altezza,
        color=col_50,
        edgecolor="white",
        label=f"Anni '50 (1950–1959 | N={tot_50})"
    )
    bars_60 = ax.barh(
        [y - altezza / 2 for y in y_pos],
        vals_60,
        height=altezza,
        color=col_60,
        edgecolor="white",
        label=f"Anni '60 (1960–1969 | N={tot_60})"
    )

    max_val = max(vals_50 + vals_60) if (vals_50 or vals_60) else 1

    for bar, v in zip(bars_50, vals_50):
        pct = (v / tot_50 * 100) if tot_50 else 0
        ax.text(
            v + max_val * 0.02,
            bar.get_y() + bar.get_height() / 2,
            f"{v} ({pct:.1f}%)",
            va="center",
            fontsize=8.5,
            fontweight="bold",
            color="#1a1a1a"
        )

    for bar, v in zip(bars_60, vals_60):
        pct = (v / tot_60 * 100) if tot_60 else 0
        ax.text(
            v + max_val * 0.02,
            bar.get_y() + bar.get_height() / 2,
            f"{v} ({pct:.1f}%)",
            va="center",
            fontsize=8.5,
            fontweight="bold",
            color="#333333"
        )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(categorie, fontsize=10)
    ax.set_xlim(0, max_val * 1.32)
    ax.set_title(titolo_pannello, fontsize=12.5, fontweight="bold", pad=12)
    ax.set_xlabel("Numero di abiti (% sul singolo decennio)", fontsize=9.5, fontweight="bold")
    ax.grid(axis="x", linestyle="--", alpha=0.45)
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", fontsize=9, framealpha=0.95)


# Pannello sinistro: Posizione sociale / ruolo / professione
disegna_pannello_confronto(
    ax1, ruoli_50, ruoli_60,
    "Posizione sociale, ruolo o professione",
    "#1f4e78", "#6baed6"
)

# Pannello destro: Occasioni d'uso più frequenti
disegna_pannello_confronto(
    ax2, occ_50, occ_60,
    "Occasioni d'uso più frequenti",
    "#2e7d32", "#81c784"
)

fig.suptitle(
    "Confronto tra anni '50 e anni '60: profilo sociale e occasioni d'uso (abiti francesi)",
    fontsize=15,
    fontweight="bold",
    y=0.98
)

# Salvataggio del grafico sul Desktop
plt.savefig(output_img, dpi=300, bbox_inches="tight")
plt.close()

print(f"\nGrafico salvato con successo sul Desktop in:\n{output_img}")
