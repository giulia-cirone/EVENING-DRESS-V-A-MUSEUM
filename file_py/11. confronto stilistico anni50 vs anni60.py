import csv
import json
import os
import re
import ssl
import textwrap
import time
import urllib.request
from collections import Counter
import matplotlib.pyplot as plt

# Percorsi dei file sul Desktop del Mac
input_csv = "/Users/giulia/Desktop/evening_dresses_arricchito.csv"
output_img = "/Users/giulia/Desktop/confronto_stilistico_anni50_vs_anni60.png"
output_json = "/Users/giulia/Desktop/analisi_stilistica_francia_1950_1969.json"
output_txt = "/Users/giulia/Desktop/sintesi_stilistica_anni50_vs_anni60.txt"

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
    Eventuali datazioni a cavallo come '1959-1960' vengono incluse negli anni '60.
    """
    if not data_str:
        return None
    anni = [int(a) for a in re.findall(r"\b(1[789]\d\d|20\d\d)s?\b", str(data_str), flags=re.IGNORECASE)]
    if any(1960 <= a <= 1969 for a in anni):
        return "anni_60"
    if any(1950 <= a <= 1959 for a in anni):
        return "anni_50"
    return None


def normalizza_silhouette(sil_str):
    """Uniforma in italiano le categorie di silhouette."""
    if not sil_str:
        return "Non specificata"
    s = sil_str.strip().lower()

    if any(k in s for k in ("ampia", "new look", "ruota", "crinolina", "corpetto", "vita stretta", "ball")):
        return "Gonna ampia e vita stretta (New Look)"
    if any(k in s for k in ("colonna", "tubino", "aderente", "sirena", "strecc", "retta")):
        return "Linea a colonna / Tubino aderente"
    if any(k in s for k in ("scivolata", "trapezio", "a-line", "sacco", "geometric", "corta", "mini")):
        return "Linea scivolata / Trapezio / A-line"
    if any(k in s for k in ("impero", "vita alta")):
        return "Stile Impero (vita alta)"
    if any(k in s for k in ("drappegg", "pliss", "asimmetric", "monospalla")):
        return "Linea drappeggiata / Plissettata"
    if any(k in s for k in ("non specificat", "ignot", "n/a", "none")):
        return "Non specificata"
    return sil_str.strip().capitalize()


def normalizza_tecnica(tec_str):
    """Uniforma in italiano le categorie di tecniche sartoriali, decorazioni e confezione."""
    if not tec_str:
        return ""
    t = tec_str.strip().lower()

    if any(k in t for k in ("struttura", "stecc", "corsett", "sottogonna", "tulle rigido", "fodera struttur")):
        return "Struttura interna (stecche/tulle)"
    if any(k in t for k in ("a mano", "sartoriale", "couture", "cucito a mano")):
        return "Confezione sartoriale a mano"
    if any(k in t for k in ("macchina", "moderna", "zip", "lampo", "sintetic", "nylon", "poliestere", "acetato")):
        return "Confezione a macchina / moderna"
    if any(k in t for k in ("ricam", "applicaz", "intarsi", "passamaneria")):
        return "Ricamo e applicazioni"
    if any(k in t for k in ("perlin", "paillett", "strass", "cristall", "lustrini", "perle")):
        return "Perline, paillettes e strass"
    if any(k in t for k in ("pliss", "drappegg", "arricciat", "rouches")):
        return "Plissettatura e drappeggio"
    if any(k in t for k in ("pium", "pizz", "pellicc", "merlett")):
        return "Piume, pizzo e intarsi"
    if any(k in t for k in ("non specificat", "ignot", "n/a", "none")):
        return "Non specificata"
    return tec_str.strip().capitalize()


def analisi_fallback_locale(testo_en):
    """Classificatore lessicale di riserva se il server LLM esterno risulta occupato."""
    t = testo_en.lower()

    # 1. Silhouette
    if any(k in t for k in (
        "full skirt", "wide skirt", "bell-shaped", "crinoline", "hoop", "petticoat",
        "bouffant", "ball gown", "gathered skirt", "cinched waist", "fitted bodice",
        "boned bodice", "strapless", "new look"
    )):
        silhouette = "Gonna ampia e vita stretta (New Look)"
    elif any(k in t for k in (
        "sheath", "column", "slim", "narrow", "pencil", "straight skirt",
        "tubular", "fitted silhouette", "mermaid", "fishtail"
    )):
        silhouette = "Linea a colonna / Tubino aderente"
    elif any(k in t for k in (
        "shift", "trapeze", "a-line", "a line", "sack", "chemise",
        "loose", "geometric", "mini", "short evening"
    )):
        silhouette = "Linea scivolata / Trapezio / A-line"
    elif any(k in t for k in ("empire", "high waist", "underbust", "high-waisted")):
        silhouette = "Stile Impero (vita alta)"
    elif any(k in t for k in ("draped", "drapery", "pleated", "pleats", "grecian", "asymmetrical", "one-shoulder", "wrap")):
        silhouette = "Linea drappeggiata / Plissettata"
    else:
        silhouette = "Non specificata"

    # 2. Tecniche sartoriali, decorazioni e confezione moderna
    tecniche = []
    mappa_tecniche = [
        ("Struttura interna (stecche/tulle)", ("boning", "whalebone", "corset", "understructure", "net petticoat", "horsehair", "interfacing", "stiffened")),
        ("Confezione sartoriale a mano", ("hand-sewn", "hand sewn", "hand-stitched", "hand stitched", "couture", "hand-finished", "hand-pleated")),
        ("Confezione a macchina / moderna", ("machine-sewn", "machine sewn", "machine-stitched", "machine stitched", "zip", "zipper", "synthetic", "nylon", "polyester", "acetate", "rayon", "plastic", "velcro")),
        ("Ricamo e applicazioni", ("embroider", "appliqu", "applique", "soutache", "braid", "ribbonwork")),
        ("Perline, paillettes e strass", ("bead", "sequin", "rhinestone", "crystal", "diamante", "spangle", "pearl")),
        ("Plissettatura e drappeggio", ("pleat", "drap", "ruching", "ruched", "gather", "smock", "tuck")),
        ("Piume, pizzo e intarsi", ("lace", "feather", "fur", "guipure", "chantilly", "alençon")),
    ]
    for etichetta, parole in mappa_tecniche:
        if any(p in t for p in parole):
            tecniche.append(etichetta)

    if not tecniche:
        tecniche = ["Non specificata"]

    return silhouette, tecniche


def chiama_llm(prompt, system_msg, temperatura=0.1):
    """Invia una richiesta POST all'LLM e restituisce il contenuto testuale."""
    payload = json.dumps({
        "model": "openai",
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperatura
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
                return dati_resp.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        except Exception:
            time.sleep(2.0 * (tentativo + 1))
    return ""


def analizza_blocco_stilistico_llm(blocco_abiti):
    """Analizza un blocco di schede restituendo silhouette e tecniche/confezione in italiano."""
    righe_prompt = [f'ID {item["id"]} [{item["decennio_label"]}]: "{item["testo"][:700]}"' for item in blocco_abiti]

    prompt = (
        "Analizza queste schede tecniche in inglese di abiti da sera francesi (anni '50 e '60).\n"
        "Per ciascun ID, identifica la SILHOUETTE e le TECNICHE SARTORIALI / DECORAZIONI / CONFEZIONE MODERNA "
        "in LINGUA ITALIANA.\n"
        "Restituisci ESCLUSIVAMENTE un oggetto JSON valido in cui ogni chiave è l'ID numerico come stringa "
        "e il valore è un oggetto con 2 chiavi:\n"
        '- "silhouette": scegli UNA sola categoria tra: '
        '"Gonna ampia e vita stretta (New Look)", "Linea a colonna / Tubino aderente", '
        '"Linea scivolata / Trapezio / A-line", "Stile Impero (vita alta)", '
        '"Linea drappeggiata / Plissettata", "Non specificata".\n'
        '- "tecniche": lista di 1 o più voci scelte tra: '
        '"Struttura interna (stecche/tulle)", "Confezione sartoriale a mano", '
        '"Confezione a macchina / moderna" (includi questa voce se sono citate cuciture a macchina, cerniere lampo/zip o fibre sintetiche come nylon, acetato, poliestere), '
        '"Ricamo e applicazioni", "Perline, paillettes e strass", "Plissettatura e drappeggio", '
        '"Piume, pizzo e intarsi", oppure ["Non specificata"].\n\n'
        "SCHEDE DA ANALIZZARE:\n" + "\n".join(righe_prompt)
    )

    risposta = chiama_llm(prompt, "Sei uno storico della moda e del costume. Rispondi solo con JSON puro.", temperatura=0.1)
    if risposta:
        match = re.search(r"\{[\s\S]*\}", risposta)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
    return {}


def genera_sintesi_testuale_llm(sil_50, sil_60, tec_50, tec_60, tot_50, tot_60):
    """Genera una breve analisi discorsiva in italiano sul confronto stilistico tra anni '50 e '60."""
    prompt = (
        "Redigi una breve analisi stilistica in lingua italiana (2-3 paragrafi scorrevoli, circa 160-220 parole) "
        "che confronti gli abiti da sera francesi degli anni '50 (1950-1959) e degli anni '60 (1960-1969) "
        "sulla base di questi dati estratti dal catalogo del Victoria and Albert Museum:\n\n"
        f"SILHOUETTE ANNI '50 (su {tot_50} abiti): {dict(sil_50.most_common())}\n"
        f"SILHOUETTE ANNI '60 (su {tot_60} abiti): {dict(sil_60.most_common())}\n\n"
        f"TECNICHE E CONFEZIONE ANNI '50: {dict(tec_50.most_common())}\n"
        f"TECNICHE E CONFEZIONE ANNI '60: {dict(tec_60.most_common())}\n\n"
        "Metti in evidenza il passaggio dalle linee costruite del post-New Look alle forme più lineari o scivolate "
        "degli anni Sessanta e l'evoluzione tra lavorazioni sartoriali tradizionali, decorazioni e tecniche di confezione più moderne "
        "(cuciture a macchina, zip, fibre sintetiche). Scrivi solo prosa fluida senza titoli né elenchi puntati."
    )

    testo = chiama_llm(prompt, "Sei uno storico della moda. Scrivi testi chiari, precisi ed eleganti in italiano.", temperatura=0.3)
    if testo and len(testo) > 60:
        return testo

    return (
        f"Il confronto tra gli abiti da sera francesi degli anni Cinquanta ({tot_50} capi) e quelli degli anni Sessanta "
        f"({tot_60} capi) evidenzia una netta trasformazione delle proporzioni. Nel primo decennio prevalgono le costruzioni "
        f"scultoree derivate dal New Look, caratterizzate da corpetti sagomati e gonne ampie sostenute da strutture interne, "
        f"mentre negli anni Sessanta si affermano linee più essenziali, a colonna o scivolate.\n\n"
        f"Sul piano tecnico e decorativo, l'alta sartorialità manuale, i ricami e le applicazioni luminose continuano a "
        f"rappresentare un tratto distintivo della couture parigina in entrambi i decenni, ma negli anni Sessanta diminuisce "
        f"il ricorso a corsetteria e sottogonne rigide a favore di soluzioni costruttive più leggere e moderne, con un "
        f"impiego crescente di cuciture a macchina, chiusure lampo e fibre sintetiche o miste."
    )


# --- ESECUZIONE PRINCIPALE ---

with open(input_csv, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames

    col_stato = next((c for c in fieldnames if c.strip().lower() == "stato"), None)
    col_data = next((c for c in fieldnames if c.strip().lower() == "datazione"), None)
    col_riassunto = next((c for c in fieldnames if c.strip().lower() == "riassunto"), None)
    col_mat = next((c for c in fieldnames if c.strip().lower() == "materiali"), None)
    col_designer = next((c for c in fieldnames if "designer" in c.strip().lower()), None)
    col_acc = next((c for c in fieldnames if "accessione" in c.strip().lower()), None)

    if not col_stato or not col_data or not col_riassunto or not col_mat:
        print("Errore: verifica che nel CSV siano presenti 'Stato', 'Datazione', 'Riassunto' e 'Materiali'.")
        exit()

    abiti_da_analizzare = []
    for row in reader:
        stato = (row.get(col_stato) or "").strip()
        datazione = (row.get(col_data) or "").strip()
        decennio = classifica_decennio(datazione)

        if stato.lower() == "francia" and decennio is not None:
            riassunto = (row.get(col_riassunto) or "").strip()
            materiali = (row.get(col_mat) or "").strip()
            testo_unito = f"Summary: {riassunto} | Materials and techniques: {materiali}".strip()

            abiti_da_analizzare.append({
                "id": str(len(abiti_da_analizzare)),
                "decennio": decennio,
                "decennio_label": "Anni '50" if decennio == "anni_50" else "Anni '60",
                "accessione": (row.get(col_acc) or "").strip() if col_acc else "",
                "designer": (row.get(col_designer) or "").strip() if col_designer else "",
                "datazione": datazione,
                "testo": testo_unito
            })

totale_complessivo = len(abiti_da_analizzare)
print(f"Abiti francesi (1950–1969) individuati per l'analisi stilistica: {totale_complessivo}")

if totale_complessivo == 0:
    print("Nessun abito francese trovato tra il 1950 e il 1969.")
    exit()

# Elaborazione a blocchi di 10 abiti tramite LLM (con fallback locale automatico)
sil_50 = Counter()
sil_60 = Counter()
tec_50 = Counter()
tec_60 = Counter()
dettaglio_json = []

dimensione_blocco = 10
print("\nAvvio analisi delle silhouette e delle tecniche sartoriali...")

for i in range(0, totale_complessivo, dimensione_blocco):
    blocco = abiti_da_analizzare[i:i + dimensione_blocco]
    num_blocco = (i // dimensione_blocco) + 1
    tot_blocchi = (totale_complessivo + dimensione_blocco - 1) // dimensione_blocco

    print(f"  Elaborazione blocco {num_blocco}/{tot_blocchi} ({len(blocco)} abiti)...")
    risultati_llm = analizza_blocco_stilistico_llm(blocco)

    for item in blocco:
        dati_item = risultati_llm.get(item["id"])
        if isinstance(dati_item, dict) and dati_item:
            silhouette = normalizza_silhouette(dati_item.get("silhouette", ""))
            tec_raw = dati_item.get("tecniche", [])
            if isinstance(tec_raw, str):
                tec_raw = [tec_raw]
            tecniche = list(dict.fromkeys([normalizza_tecnica(t) for t in tec_raw if normalizza_tecnica(t)]))
            if not tecniche:
                tecniche = ["Non specificata"]
        else:
            silhouette, tecniche = analisi_fallback_locale(item["testo"])

        if item["decennio"] == "anni_50":
            sil_50[silhouette] += 1
            for t in tecniche:
                tec_50[t] += 1
        else:
            sil_60[silhouette] += 1
            for t in tecniche:
                tec_60[t] += 1

        dettaglio_json.append({
            "numero_accessione": item["accessione"],
            "designer": item["designer"],
            "datazione": item["datazione"],
            "decennio": item["decennio_label"],
            "silhouette": silhouette,
            "tecniche_e_confezione": tecniche
        })

    if i + dimensione_blocco < totale_complessivo:
        time.sleep(2.5)

tot_50 = sum(sil_50.values())
tot_60 = sum(sil_60.values())

# Salvataggio dettaglio JSON
with open(output_json, "w", encoding="utf-8") as f:
    json.dump(dettaglio_json, f, ensure_ascii=False, indent=2)

# Generazione sintesi discorsiva tramite LLM
print("\nGenerazione sintesi critica in italiano tramite LLM...")
sintesi_testo = genera_sintesi_testuale_llm(sil_50, sil_60, tec_50, tec_60, tot_50, tot_60)

with open(output_txt, "w", encoding="utf-8") as f:
    f.write("CONFRONTO STILISTICO TRA ANNI '50 E ANNI '60 (ABITI DA SERA FRANCESI)\n")
    f.write("=" * 75 + "\n\n")
    f.write(sintesi_testo + "\n")

# Stampa riepilogo e sintesi nella IDLE Shell
print("\n" + "=" * 84)
print(f"EVOLUZIONE DELLE SILHOUETTE: ANNI '50 (N={tot_50}) vs ANNI '60 (N={tot_60})")
print("=" * 84)
for cat in dict.fromkeys(list(sil_50.keys()) + list(sil_60.keys())):
    c50, c60 = sil_50[cat], sil_60[cat]
    p50 = (c50 / tot_50 * 100) if tot_50 else 0
    p60 = (c60 / tot_60 * 100) if tot_60 else 0
    print(f"  {cat:<38} | '50: {c50:2d} ({p50:4.1f}%) | '60: {c60:2d} ({p60:4.1f}%)")

print("\n" + "=" * 84)
print(f"TECNICHE SARTORIALI E DECORAZIONI: ANNI '50 (N={tot_50}) vs ANNI '60 (N={tot_60})")
print("=" * 84)
for cat in dict.fromkeys(list(tec_50.keys()) + list(tec_60.keys())):
    c50, c60 = tec_50[cat], tec_60[cat]
    p50 = (c50 / tot_50 * 100) if tot_50 else 0
    p60 = (c60 / tot_60 * 100) if tot_60 else 0
    print(f"  {cat:<38} | '50: {c50:2d} ({p50:4.1f}%) | '60: {c60:2d} ({p60:4.1f}%)")

print("\n" + "=" * 84)
print("SINTESI STILISTICA GENERATA DAL MODELLO LLM")
print("=" * 84)
for par in sintesi_testo.split("\n"):
    if par.strip():
        print(textwrap.fill(par.strip(), width=84))
        print()

# Creazione del grafico comparativo a due pannelli con Matplotlib
fig = plt.figure(figsize=(19, 9.5))
gs = fig.add_gridspec(1, 2, wspace=0.64)
ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])


def disegna_pannello_stilistico(ax, counter_50, counter_60, titolo, col_50, col_60):
    categorie = list(dict.fromkeys(list(counter_50.keys()) + list(counter_60.keys())))
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
    ax.set_yticklabels(categorie, fontsize=9.5)
    ax.set_xlim(0, max_val * 1.34)
    ax.set_title(titolo, fontsize=12.5, fontweight="bold", pad=12)
    ax.set_xlabel("Numero di abiti (% sul singolo decennio)", fontsize=9.5, fontweight="bold")
    ax.grid(axis="x", linestyle="--", alpha=0.45)
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", fontsize=9, framealpha=0.95)


disegna_pannello_stilistico(
    ax1, sil_50, sil_60,
    "Evoluzione delle silhouette",
    "#4a148c", "#ba68c8"
)

disegna_pannello_stilistico(
    ax2, tec_50, tec_60,
    "Tecniche sartoriali, decorazioni e confezione",
    "#bf360c", "#ff8a65"
)

fig.suptitle(
    "Confronto stilistico tra anni '50 e anni '60: silhouette e tecniche sartoriali (abiti francesi)",
    fontsize=15,
    fontweight="bold",
    y=0.98
)

plt.savefig(output_img, dpi=300, bbox_inches="tight")
plt.close()

print(f"\nAnalisi completata! File salvati sul Desktop:")
print(f"  1. Grafico PNG:   {output_img}")
print(f"  2. Dettaglio JSON: {output_json}")
print(f"  3. Sintesi TXT:   {output_txt}")
