import csv
import html
import json
import os
import re
from collections import Counter

# Cartella di lavoro sul Desktop del Mac
desktop = "/Users/giulia/Desktop"

# Percorsi dei file di input
path_csv = os.path.join(desktop, "evening_dresses_arricchito.csv")
path_json_designer = os.path.join(desktop, "dati biografici 20 designer più diffusi.json")
path_json_indossatrici = os.path.join(desktop, "analisi_indossatrici_francia_1950_1969.json")
path_json_stilistica = os.path.join(desktop, "analisi_stilistica_francia_1950_1969.json")
path_txt_indossatrici = os.path.join(desktop, "descrizione_indossatrici_e_occasioni.txt")
path_txt_stilistica = os.path.join(desktop, "sintesi_stilistica_anni50_vs_anni60.txt")

# Percorso del file HTML di output
path_html_output = os.path.join(desktop, "report_evening_dresses_v&am.html")

# Dizionario tessile di supporto per estrarre i materiali più utilizzati nel CSV
DIZIONARIO_MATERIALI_IT = {
    "silk": "Seta",
    "satin": "Raso",
    "tulle": "Tulle",
    "velvet": "Velluto",
    "lace": "Pizzo",
    "chiffon": "Chiffon",
    "organza": "Organza",
    "taffeta": "Taffetà",
    "faille": "Faille",
    "crepe": "Crêpe",
    "crêpe": "Crêpe",
    "cotton": "Cotone",
    "wool": "Lana",
    "nylon": "Nylon",
    "rayon": "Rayon",
    "polyester": "Poliestere",
    "acetate": "Acetato",
    "brocade": "Brocato",
    "lamé": "Lamé",
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
}


def nel_periodo_1950_1969(data_str):
    """Restituisce True se almeno un anno nella datazione rientra tra il 1950 e il 1969."""
    if not data_str:
        return False
    anni = [int(a) for a in re.findall(r"\b(1[789]\d\d|20\d\d)s?\b", str(data_str), flags=re.IGNORECASE)]
    return any(1950 <= a <= 1969 for a in anni)


def leggi_json_sicuro(percorso, default=None):
    """Carica un file JSON se esiste sul Desktop, altrimenti restituisce il valore predefinito."""
    if os.path.exists(percorso):
        with open(percorso, "r", encoding="utf-8") as f:
            return json.load(f)
    return default if default is not None else []


def leggi_testo_pulito(percorso, fallback_msg):
    """Legge un file TXT rimuovendo eventuali intestazioni iniziali e restituendo i paragrafi."""
    if not os.path.exists(percorso):
        return [fallback_msg]
    with open(percorso, "r", encoding="utf-8") as f:
        righe = [r.strip() for r in f.readlines()]

    paragrafi = []
    for i, r in enumerate(righe):
        if not r or set(r) <= {"=", "-"}:
            continue
        # Salta il titolo maiuscolo della prima riga se seguito da separatore
        if i == 0 and r.isupper():
            continue
        paragrafi.append(r)
    return paragrafi if paragrafi else [fallback_msg]


# --- 1. LETTURA ED ELABORAZIONE DEI DATI ---

totale_catalogo = 0
abiti_francia_totali = 0
abiti_fr_50_69 = []
designer_fr_50_69 = Counter()
designer_tutto_catalogo = Counter()
materiali_fr_50_69 = Counter()
esposti_in_galleria_fr = 0

if os.path.exists(path_csv):
    with open(path_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []

        col_stato = next((c for c in fieldnames if c.strip().lower() == "stato"), None)
        col_data = next((c for c in fieldnames if c.strip().lower() == "datazione"), None)
        col_des = next((c for c in fieldnames if "designer" in c.strip().lower()), None)
        col_mat = next((c for c in fieldnames if c.strip().lower() == "materiali"), None)
        col_pos = next((c for c in fieldnames if c.strip().lower() == "posizione"), None)

        ignoti = {"unknown", "sconosciuto", "non specificato", "anonymous", "anonimo", ""}

        for row in reader:
            totale_catalogo += 1
            stato = (row.get(col_stato) or "").strip() if col_stato else ""
            datazione = (row.get(col_data) or "").strip() if col_data else ""
            designer = (row.get(col_des) or "").strip() if col_des else ""
            materiali = (row.get(col_mat) or "").strip() if col_mat else ""
            posizione = (row.get(col_pos) or "").strip() if col_pos else ""

            if designer.lower() not in ignoti:
                designer_tutto_catalogo[designer] += 1

            if stato.lower() == "francia":
                abiti_francia_totali += 1
                if nel_periodo_1950_1969(datazione):
                    abiti_fr_50_69.append(row)
                    if designer.lower() not in ignoti:
                        designer_fr_50_69[designer] += 1
                    if posizione and "storage" not in posizione.lower() and "deposito" not in posizione.lower():
                        esposti_in_galleria_fr += 1

                    # Conteggio materiali presenti nel testo
                    t_low = materiali.lower()
                    trovati_abito = set()
                    for en_k, it_v in DIZIONARIO_MATERIALI_IT.items():
                        if re.search(rf"\b{re.escape(en_k)}\b", t_low):
                            trovati_abito.add(it_v)
                    for m_it in trovati_abito:
                        materiali_fr_50_69[m_it] += 1

n_fr_50_69 = len(abiti_fr_50_69)
pct_fr_sul_totale = (n_fr_50_69 / totale_catalogo * 100) if totale_catalogo else 0.0

# Lettura dei file JSON generati nelle fasi precedenti
dati_20_designer = leggi_json_sicuro(path_json_designer, [])
dati_indossatrici = leggi_json_sicuro(path_json_indossatrici, [])
dati_stilistica = leggi_json_sicuro(path_json_stilistica, [])

# Stilisti più ricorrenti nel periodo francese 1950-1969 (Top 3)
top_designer_fr_str = ", ".join(
    [f"{nome} ({qta})" for nome, qta in designer_fr_50_69.most_common(3)]
) or "Non disponibile"

# Primo stilista assoluto nell'intero catalogo V&A (dal JSON top 20 o dal CSV)
if dati_20_designer:
    primo_ass = dati_20_designer[0]
    top_designer_catalogo_str = f"{primo_ass['designer']} ({primo_ass['abiti_archivio']} abiti)"
elif designer_tutto_catalogo:
    n_top, q_top = designer_tutto_catalogo.most_common(1)[0]
    top_designer_catalogo_str = f"{n_top} ({q_top} abiti)"
else:
    top_designer_catalogo_str = "Non disponibile"

# Materiali più utilizzati nel periodo 1950-1969 (Top 3)
top_materiali_str = ", ".join(
    [f"{mat} ({qta} abiti)" for mat, qta in materiali_fr_50_69.most_common(3)]
) or "Non disponibile"

# Categoria sociale e occasione d'uso più frequenti (escludendo 'Non specificato')
ruoli_counter = Counter(
    r.get("posizione_sociale_ruolo", "Non specificato")
    for r in dati_indossatrici
    if "non specificat" not in r.get("posizione_sociale_ruolo", "").lower()
)
occasioni_counter = Counter(
    r.get("occasione_uso", "Non specificata")
    for r in dati_indossatrici
    if "non specificat" not in r.get("occasione_uso", "").lower()
)

top_ruolo_str = (
    f"{ruoli_counter.most_common(1)[0][0]} ({ruoli_counter.most_common(1)[0][1]} abiti)"
    if ruoli_counter else "Non disponibile"
)
top_occasione_str = (
    f"{occasioni_counter.most_common(1)[0][0]} ({occasioni_counter.most_common(1)[0][1]} abiti)"
    if occasioni_counter else "Non disponibile"
)

# Silhouette e tecnica sartoriale più frequenti (dal JSON stilistico)
sil_counter = Counter(
    r.get("silhouette", "Non specificata")
    for r in dati_stilistica
    if "non specificat" not in r.get("silhouette", "").lower()
)
tec_counter = Counter()
for r in dati_stilistica:
    for t in r.get("tecniche_e_confezione", []):
        if "non specificat" not in t.lower():
            tec_counter[t] += 1

top_silhouette_str = (
    f"{sil_counter.most_common(1)[0][0]} ({sil_counter.most_common(1)[0][1]} abiti)"
    if sil_counter else "Non disponibile"
)
top_tecnica_str = (
    f"{tec_counter.most_common(1)[0][0]} ({tec_counter.most_common(1)[0][1]} abiti)"
    if tec_counter else "Non disponibile"
)

# --- 2. LETTURA DEI TESTI DI APPROFONDIMENTO STORICO-STILISTICO ---

paragrafi_indossatrici = leggi_testo_pulito(
    path_txt_indossatrici,
    "Descrizione su indossatrici e occasioni d'uso non ancora generata."
)
paragrafi_stilistica = leggi_testo_pulito(
    path_txt_stilistica,
    "Sintesi sul confronto stilistico tra anni '50 e anni '60 non ancora generata."
)

html_paragrafi_indossatrici = "\n".join(
    f"        <p>{html.escape(p)}</p>" for p in paragrafi_indossatrici
)
html_paragrafi_stilistica = "\n".join(
    f"        <p>{html.escape(p)}</p>" for p in paragrafi_stilistica
)

# --- 3. COSTRUZIONE DELLA PAGINA HTML TRAMITE F-STRING ---

html_content = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Abiti da Sera al Victoria and Albert Museum — Report di Sintesi</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.65;
            color: #222222;
            background-color: #fafafa;
            margin: 0;
            padding: 24px 16px;
        }}
        main {{
            max-width: 900px;
            margin: 0 auto;
            background-color: #ffffff;
            padding: 36px 40px;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
        }}
        h1 {{
            font-size: 1.9rem;
            color: #1a2a3a;
            margin-top: 0;
            margin-bottom: 12px;
            border-bottom: 2px solid #1f4e78;
            padding-bottom: 10px;
        }}
        h2 {{
            font-size: 1.35rem;
            color: #1f4e78;
            margin-top: 36px;
            margin-bottom: 14px;
            border-bottom: 1px solid #dcdcdc;
            padding-bottom: 6px;
        }}
        h3 {{
            font-size: 1.1rem;
            color: #333333;
            margin-top: 24px;
            margin-bottom: 8px;
        }}
        p {{
            margin-top: 0;
            margin-bottom: 14px;
            text-align: justify;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 18px 0 24px 0;
            font-size: 0.96rem;
        }}
        th, td {{
            border: 1px solid #cccccc;
            padding: 10px 14px;
            text-align: left;
        }}
        th {{
            background-color: #1f4e78;
            color: #ffffff;
            font-weight: 600;
        }}
        tr:nth-child(even) td {{
            background-color: #f6f8fa;
        }}
        figure {{
            margin: 26px 0;
            padding: 14px;
            border: 1px solid #e2e2e2;
            background-color: #fcfcfc;
            border-radius: 4px;
        }}
        figure img {{
            width: 100%;
            height: auto;
            display: block;
        }}
        figcaption {{
            margin-top: 10px;
            font-size: 0.92rem;
            color: #555555;
            font-style: italic;
        }}
        .box-testo {{
            background-color: #f8fafc;
            border-left: 4px solid #1f4e78;
            padding: 16px 20px;
            margin: 16px 0;
        }}
        footer {{
            margin-top: 40px;
            padding-top: 14px;
            border-top: 1px solid #e0e0e0;
            font-size: 0.85rem;
            color: #666666;
            text-align: center;
        }}
    </style>
</head>
<body>
    <main>
        <header>
            <h1>Abiti da sera al Victoria and Albert Museum: l'alta moda francese (1950–1969)</h1>
            <p>
                Questo report sintetizza l'analisi computazionale e storico-artistica condotta sulla collezione di
                abiti da sera conservati presso il <strong>Victoria and Albert Museum (V&amp;A)</strong> di Londra.
                A partire dal dataset catalografico arricchito con le schede tecniche ufficiali del museo (materiali,
                descrizioni fisiche e storia dell'oggetto), lo studio approfondisce in particolare la produzione
                francese realizzata tra il <strong>1950 e il 1969</strong>, esaminandone i principali couturier,
                l'impiego tessile, il profilo sociale delle committenti, le occasioni d'uso e l'evoluzione stilistica
                tra anni Cinquanta e anni Sessanta.
            </p>
        </header>

        <section id="dati">
            <h2>Dati</h2>
            <p>
                La tabella seguente raccoglie i principali indicatori quantitativi ricavati dall'incrocio tra il
                catalogo generale e i file strutturati dedicati al nucleo francese del ventennio 1950–1969.
            </p>
            <table>
                <thead>
                    <tr>
                        <th>Indicatore</th>
                        <th>Valore rilevato</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>Numero totale di abiti da sera nel catalogo V&amp;A</strong></td>
                        <td>{totale_catalogo} abiti</td>
                    </tr>
                    <tr>
                        <td><strong>Numero totale di abiti di produzione francese (intero archivio)</strong></td>
                        <td>{abiti_francia_totali} abiti</td>
                    </tr>
                    <tr>
                        <td><strong>Abiti francesi datati tra il 1950 e il 1969</strong></td>
                        <td>{n_fr_50_69} abiti ({pct_fr_sul_totale:.1f}% del catalogo complessivo)</td>
                    </tr>
                    <tr>
                        <td><strong>Stilista più rappresentato nell'intero catalogo</strong></td>
                        <td>{html.escape(top_designer_catalogo_str)}</td>
                    </tr>
                    <tr>
                        <td><strong>Stilisti più ricorrenti in Francia (1950–1969)</strong></td>
                        <td>{html.escape(top_designer_fr_str)}</td>
                    </tr>
                    <tr>
                        <td><strong>Materiali più utilizzati (Francia, 1950–1969)</strong></td>
                        <td>{html.escape(top_materiali_str)}</td>
                    </tr>
                    <tr>
                        <td><strong>Categoria sociale / ruolo più frequente</strong></td>
                        <td>{html.escape(top_ruolo_str)}</td>
                    </tr>
                    <tr>
                        <td><strong>Occasione d'uso più frequente</strong></td>
                        <td>{html.escape(top_occasione_str)}</td>
                    </tr>
                    <tr>
                        <td><strong>Silhouette più ricorrente (1950–1969)</strong></td>
                        <td>{html.escape(top_silhouette_str)}</td>
                    </tr>
                    <tr>
                        <td><strong>Lavorazione / tecnica più frequente (1950–1969)</strong></td>
                        <td>{html.escape(top_tecnica_str)}</td>
                    </tr>
                    <tr>
                        <td><strong>Abiti francesi (1950–1969) esposti in galleria</strong></td>
                        <td>{esposti_in_galleria_fr} su {n_fr_50_69}</td>
                    </tr>
                </tbody>
            </table>
        </section>

        <section id="grafici-e-tabelle">
            <h2>Grafici e Tabelle</h2>
            <p>
                Di seguito sono riportate le visualizzazioni grafiche prodotte durante l'indagine sui materiali,
                sulla committenza e sul confronto diacronico tra gli anni Cinquanta e gli anni Sessanta.
            </p>

            <figure>
                <img src="materiali_francia_1950_1969.png" alt="Grafico a torta dei materiali più utilizzati negli abiti da sera francesi 1950-1969">
                <figcaption>
                    <strong>Figura 1 — Materiali più utilizzati (Francia, 1950–1969):</strong> distribuzione percentuale
                    dei tessuti e delle applicazioni decorative estratti dalle schede tecniche del museo.
                </figcaption>
            </figure>

            <figure>
                <img src="indossatrici_e_occasioni_francia_1950_1969.png" alt="Grafico su chi indossava gli abiti da sera francesi e occasioni d'uso">
                <figcaption>
                    <strong>Figura 2 — Profilo sociale e occasioni d'uso (1950–1969):</strong> classificazione delle
                    indossatrici per ruolo o estrazione sociale e dei contesti mondani o istituzionali documentati.
                </figcaption>
            </figure>

            <figure>
                <img src="confronto tra anni 50 e anni 60.png" alt="Confronto tra anni 50 e anni 60 su profilo sociale e occasioni d'uso">
                <figcaption>
                    <strong>Figura 3 — Confronto tra anni '50 e anni '60 (committenza e occasioni):</strong> analisi
                    comparativa tra il decennio 1950–1959 e il decennio 1960–1969 per verificare continuità e mutamenti
                    nella clientela e negli eventi sociali.
                </figcaption>
            </figure>

            <figure>
                <img src="confronto_stilistico_anni50_vs_anni60.png" alt="Confronto stilistico tra anni 50 e anni 60 su silhouette e tecniche sartoriali">
                <figcaption>
                    <strong>Figura 4 — Confronto stilistico tra anni '50 e anni '60 (silhouette e tecniche):</strong>
                    evoluzione delle linee costruttive (dal post-New Look alle silhouette scivolate) e passaggio dalle
                    strutture interne tradizionali a soluzioni di confezione più moderne.
                </figcaption>
            </figure>
        </section>

        <section id="approfondimento-storico-stilistico">
            <h2>Approfondimento Storico-Stilistico</h2>

            <h3>Committenza, profilo sociale e occasioni d'uso</h3>
            <div class="box-testo">
{html_paragrafi_indossatrici}
            </div>

            <h3>Evoluzione stilistica tra anni '50 e anni '60</h3>
            <div class="box-testo">
{html_paragrafi_stilistica}
            </div>
        </section>

        <footer>
            Report generato automaticamente in Python dai dati del catalogo Victoria and Albert Museum.
        </footer>
    </main>
</body>
</html>
"""

# Salvataggio del file HTML sul Desktop
with open(path_html_output, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Report HTML generato con successo sul Desktop in:\n{path_html_output}")
print("Puoi aprirlo direttamente facendo doppio clic sul file (si aprirà nel tuo browser senza alcun server).")
