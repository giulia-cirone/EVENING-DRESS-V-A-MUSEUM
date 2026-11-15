import base64
import csv
import html
import json
import os
import re
from collections import Counter

# Cartella principale del progetto sul Desktop del Mac
CARTELLA_PROGETTO = "/Users/giulia/Desktop/V&A"

# Percorsi esatti delle sottocartelle presenti in V&A
DIR_CSV = os.path.join(CARTELLA_PROGETTO, "file_csv")
DIR_JSON = os.path.join(CARTELLA_PROGETTO, "file_JSON")
DIR_PNG = os.path.join(CARTELLA_PROGETTO, "file_png")
DIR_TXT = os.path.join(CARTELLA_PROGETTO, "file_txt")

# Percorso del file HTML di output (salvato nella radice di V&A accanto a README.md)
path_html_output = os.path.join(CARTELLA_PROGETTO, "report_evening_dresses_v&am.html")


def trova_in_cartella(cartella, parole_chiave, estensione, escludi=None):
    """
    Cerca un file dentro la cartella specificata ignorando eventuali numeri iniziali
    (es. '01.', '3.', '10.') e differenze tra spazi, trattini e underscore.
    """
    if not os.path.isdir(cartella):
        return "", ""

    escludi = [e.lower() for e in (escludi or [])]
    for nome_file in sorted(os.listdir(cartella)):
        if nome_file.startswith("."):
            continue
        nome_low = nome_file.lower()
        if not nome_low.endswith(estensione.lower()):
            continue
        nome_norm = nome_low.replace("_", " ").replace("-", " ")
        if any(ex in nome_norm for ex in escludi):
            continue
        if all(pk.lower() in nome_norm for pk in parole_chiave):
            percorso_ass = os.path.join(cartella, nome_file)
            percorso_rel = os.path.relpath(percorso_ass, CARTELLA_PROGETTO).replace(os.sep, "/")
            return percorso_ass, percorso_rel
    return "", ""


def immagine_per_html(percorso_ass, percorso_rel):
    """
    Incorpora l'immagine PNG nell'HTML (Base64) così i grafici risultano sempre
    visibili ovunque, sia in locale sul Mac sia su GitHub Pages.
    """
    if percorso_ass and os.path.exists(percorso_ass):
        with open(percorso_ass, "rb") as img_f:
            b64 = base64.b64encode(img_f.read()).decode("ascii")
        return f"data:image/png;base64,{b64}", f"OK ({percorso_rel})"
    return "", "NON TROVATO"


# --- INDIVIDUAZIONE DEI FILE NELLE RISPETTIVE CARTELLE ---

path_csv, rel_csv = trova_in_cartella(DIR_CSV, ["arricchito"], ".csv")

path_json_designer, rel_j_des = trova_in_cartella(DIR_JSON, ["designer"], ".json")
path_json_indossatrici, rel_j_ind = trova_in_cartella(DIR_JSON, ["indossatrici"], ".json")
path_json_stilistica, rel_j_stil = trova_in_cartella(DIR_JSON, ["stilistica"], ".json")

path_txt_indossatrici, rel_t_ind = trova_in_cartella(DIR_TXT, ["indossatrici"], ".txt")
path_txt_stilistica, rel_t_stil = trova_in_cartella(DIR_TXT, ["stilistica"], ".txt")

ass_mat, rel_mat = trova_in_cartella(DIR_PNG, ["materiali", "francia"], ".png")
ass_ind, rel_ind = trova_in_cartella(DIR_PNG, ["indossatrici", "occasioni"], ".png")
ass_soc, rel_soc = trova_in_cartella(DIR_PNG, ["confronto", "50", "60"], ".png", escludi=["stilistic"])
ass_stil, rel_stil = trova_in_cartella(DIR_PNG, ["confronto", "stilistico"], ".png")

src_img_materiali, stato_1 = immagine_per_html(ass_mat, rel_mat)
src_img_indossatrici, stato_2 = immagine_per_html(ass_ind, rel_ind)
src_img_confronto_soc, stato_3 = immagine_per_html(ass_soc, rel_soc)
src_img_confronto_stil, stato_4 = immagine_per_html(ass_stil, rel_stil)

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
    if not data_str:
        return False
    anni = [int(a) for a in re.findall(r"\b(1[789]\d\d|20\d\d)s?\b", str(data_str), flags=re.IGNORECASE)]
    return any(1950 <= a <= 1969 for a in anni)


def leggi_json_sicuro(percorso, default=None):
    if percorso and os.path.exists(percorso):
        with open(percorso, "r", encoding="utf-8") as f:
            return json.load(f)
    return default if default is not None else []


def leggi_testo_pulito(percorso, fallback_msg):
    if not percorso or not os.path.exists(percorso):
        return [fallback_msg]
    with open(percorso, "r", encoding="utf-8") as f:
        righe = [r.strip() for r in f.readlines()]

    paragrafi = []
    for i, r in enumerate(righe):
        if not r or set(r) <= {"=", "-"}:
            continue
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

if path_csv and os.path.exists(path_csv):
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

                    t_low = materiali.lower()
                    trovati_abito = set()
                    for en_k, it_v in DIZIONARIO_MATERIALI_IT.items():
                        if re.search(rf"\b{re.escape(en_k)}\b", t_low):
                            trovati_abito.add(it_v)
                    for m_it in trovati_abito:
                        materiali_fr_50_69[m_it] += 1

n_fr_50_69 = len(abiti_fr_50_69)
pct_fr_sul_totale = (n_fr_50_69 / totale_catalogo * 100) if totale_catalogo else 0.0

dati_20_designer = leggi_json_sicuro(path_json_designer, [])
dati_indossatrici = leggi_json_sicuro(path_json_indossatrici, [])
dati_stilistica = leggi_json_sicuro(path_json_stilistica, [])

top_designer_fr_str = ", ".join(
    [f"{nome} ({qta})" for nome, qta in designer_fr_50_69.most_common(3)]
) or "Non disponibile"

if dati_20_designer:
    primo_ass = dati_20_designer[0]
    top_designer_catalogo_str = f"{primo_ass['designer']} ({primo_ass['abiti_archivio']} abiti)"
elif designer_tutto_catalogo:
    n_top, q_top = designer_tutto_catalogo.most_common(1)[0]
    top_designer_catalogo_str = f"{n_top} ({q_top} abiti)"
else:
    top_designer_catalogo_str = "Non disponibile"

top_materiali_str = ", ".join(
    [f"{mat} ({qta} abiti)" for mat, qta in materiali_fr_50_69.most_common(3)]
) or "Non disponibile"

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

# --- 3. COSTRUZIONE DELLA PAGINA HTML ---

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
                <img src="{src_img_materiali}" alt="Grafico a torta dei materiali più utilizzati negli abiti da sera francesi 1950-1969">
                <figcaption>
                    <strong>Figura 1 — Materiali più utilizzati (Francia, 1950–1969):</strong> distribuzione percentuale
                    dei tessuti e delle applicazioni decorative estratti dalle schede tecniche del museo.
                </figcaption>
            </figure>

            <figure>
                <img src="{src_img_indossatrici}" alt="Grafico su chi indossava gli abiti da sera francesi e occasioni d'uso">
                <figcaption>
                    <strong>Figura 2 — Profilo sociale e occasioni d'uso (1950–1969):</strong> classificazione delle
                    indossatrici per ruolo o estrazione sociale e dei contesti mondani o istituzionali documentati.
                </figcaption>
            </figure>

            <figure>
                <img src="{src_img_confronto_soc}" alt="Confronto tra anni 50 e anni 60 su profilo sociale e occasioni d'uso">
                <figcaption>
                    <strong>Figura 3 — Confronto tra anni '50 e anni '60 (committenza e occasioni):</strong> analisi
                    comparativa tra il decennio 1950–1959 e il decennio 1960–1969 per verificare continuità e mutamenti
                    nella clientela e negli eventi sociali.
                </figcaption>
            </figure>

            <figure>
                <img src="{src_img_confronto_stil}" alt="Confronto stilistico tra anni 50 e anni 60 su silhouette e tecniche sartoriali">
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

with open(path_html_output, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Report HTML salvato in: {path_html_output}\n")
print("Riepilogo file individuati nelle sottocartelle di V&A:")
print(f"  - CSV arricchito:    {rel_csv or 'NON TROVATO'}")
print(f"  - JSON designer:     {rel_j_des or 'NON TROVATO'}")
print(f"  - JSON indossatrici: {rel_j_ind or 'NON TROVATO'}")
print(f"  - JSON stilistica:   {rel_j_stil or 'NON TROVATO'}")
print(f"  - TXT indossatrici:  {rel_t_ind or 'NON TROVATO'}")
print(f"  - TXT stilistica:    {rel_t_stil or 'NON TROVATO'}")
print(f"  - PNG Figura 1:      {stato_1}")
print(f"  - PNG Figura 2:      {stato_2}")
print(f"  - PNG Figura 3:      {stato_3}")
print(f"  - PNG Figura 4:      {stato_4}")
