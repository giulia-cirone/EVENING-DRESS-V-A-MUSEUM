import csv
import re
from collections import Counter, defaultdict
import matplotlib.pyplot as plt

def estrai_decennio(data_str):
    if not data_str:
        return None
    match = re.search(r'\b(1[789]\d\d|20\d\d)\b', data_str)
    if match:
        anno = int(match.group(1))
        return str((anno // 10) * 10)
    return None

input_csv = "/Users/giulia/Desktop/evening_dresses_pulito.csv"
output_img1 = "/Users/giulia/Desktop/datazione archivio.png"
output_img2 = "/Users/giulia/Desktop/decenni.png"

conteggio_per_decennio_stato = defaultdict(Counter)
totale_per_stato = Counter()
# Mappa per memorizzare i decenni di ogni stato minore: {stato: Counter({decennio: n_oggetti})}
decenni_per_stato = defaultdict(Counter)
tutti_decenni = set()

# 1. Lettura dei dati dal file CSV
with open(input_csv, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    col_data = next((c for c in reader.fieldnames if c.strip().lower() == "datazione"), None)
    col_stato = next((c for c in reader.fieldnames if c.strip().lower() == "stato"), None)
    
    for row in reader:
        stato = (row.get(col_stato) or "").strip()
        datazione = (row.get(col_data) or "").strip()
        
        if not stato or stato.lower() in {"non specificato", "sconosciuto", "unknown"}:
            stato = "Sconosciuti"
            
        decennio = estrai_decennio(datazione)
        if decennio:
            totale_per_stato[stato] += 1
            conteggio_per_decennio_stato[decennio][stato] += 1
            decenni_per_stato[stato][decennio] += 1
            tutti_decenni.add(decennio)

totale_complessivo = sum(totale_per_stato.values())

# 2. Selezione dei PRIMI 6 STATI noti (escluso "Sconosciuti")
top_6_stati = [s for s, _ in totale_per_stato.most_common() if s != "Sconosciuti"][:6]

# Identificazione degli stati minori che confluiranno in "Altri stati"
stati_in_altri = [s for s, _ in totale_per_stato.most_common() if s not in top_6_stati and s != "Sconosciuti"]

# Categorie finali del grafico
categorie_stati = list(top_6_stati)
if stati_in_altri:
    categorie_stati.append("Altri stati")
if totale_per_stato["Sconosciuti"] > 0:
    categorie_stati.append("Sconosciuti")

decenni_ordinati = sorted(list(tutti_decenni), key=lambda d: int(d))

# Riorganizzazione dei conteggi per decennio
dati_grafico = {cat: [] for cat in categorie_stati}
totali_per_colonna = []

for dec in decenni_ordinati:
    sub_counts = conteggio_per_decennio_stato[dec]
    somma_decennio = 0
    
    # Primi 6 stati
    for cat in top_6_stati:
        qta = sub_counts[cat]
        dati_grafico[cat].append(qta)
        somma_decennio += qta
        
    # Somma stati minori
    if "Altri stati" in categorie_stati:
        altri_qta = sum(q for s, q in sub_counts.items() if s in stati_in_altri)
        dati_grafico["Altri stati"].append(altri_qta)
        somma_decennio += altri_qta
        
    # Sconosciuti
    if "Sconosciuti" in categorie_stati:
        sconc_qta = sub_counts["Sconosciuti"]
        dati_grafico["Sconosciuti"].append(sconc_qta)
        somma_decennio += sconc_qta
        
    totali_per_colonna.append(somma_decennio)

# 3. Assegnazione colori coerente con la torta (palette tab20)
palette_tab20 = list(plt.cm.tab20.colors)
colori_mappa = {}

for idx, stato in enumerate(top_6_stati):
    colori_mappa[stato] = palette_tab20[idx]

colori_mappa["Altri stati"] = palette_tab20[10]  # Marrone
colori_mappa["Sconosciuti"] = "#B0BEC5"          # Grigio neutro

# 4. Creazione del grafico con Matplotlib
fig, ax = plt.subplots(figsize=(15.5, 8.5))

bottom = [0] * len(decenni_ordinati)
barre_create = []

for cat in categorie_stati:
    valori = dati_grafico[cat]
    b = ax.bar(
        decenni_ordinati,
        valori,
        bottom=bottom,
        color=colori_mappa.get(cat, "#7f7f7f"),
        edgecolor="white",
        linewidth=0.8,
        width=0.75
    )
    barre_create.append(b)
    
    # Scrittura del valore interno solo se lo spessore è >= 6
    for i, (bot, v) in enumerate(zip(bottom, valori)):
        if v >= 6:
            ax.text(
                i,
                bot + v / 2,
                f"{v}",
                ha="center",
                va="center",
                fontsize=8,
                color="white",
                fontweight="bold"
            )
            
    bottom = [bot + v for bot, v in zip(bottom, valori)]

# 5. Etichette numeriche sopra ogni colonna (Totale e %)
for i, tot in enumerate(totali_per_colonna):
    if tot > 0:
        pct = (tot / totale_complessivo) * 100
        ax.text(
            i,
            tot + 2,
            f"{tot}\n({pct:.1f}%)",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold"
        )

# 6. Costruzione delle etichette della legenda con specifica dei decenni per "Altri stati"
etichette_legenda = []
for cat in categorie_stati:
    if cat == "Altri stati":
        tot_altri = sum(totale_per_stato[s] for s in stati_in_altri)
        righe_dettaglio = []
        for s in stati_in_altri:
            cnt_dec = decenni_per_stato[s]
            # Elenco decenni ordinati con conteggio tra parentesi se > 1 (es. 1960 (2) oppure 1900)
            dec_list = [f"{d} ({c})" if c > 1 else f"{d}" for d, c in sorted(cnt_dec.items(), key=lambda x: int(x[0]))]
            dec_testo = ", ".join(dec_list)
            righe_dettaglio.append(f"  • {s} ({totale_per_stato[s]}): {dec_testo}")
        
        testo_altri = f"Altri stati ({tot_altri}):\n" + "\n".join(righe_dettaglio)
        etichette_legenda.append(testo_altri)
    elif cat == "Sconosciuti":
        etichette_legenda.append(f"Sconosciuti ({totale_per_stato['Sconosciuti']})")
    else:
        etichette_legenda.append(f"{cat} ({totale_per_stato[cat]})")

# 7. Scala asse Y tarata a 130
ax.set_ylim(0, 145)
ax.set_yticks(range(0, 131, 20))
ax.set_yticklabels([str(y) for y in range(0, 131, 20)], fontsize=10)

# Formattazione assi e titolo
ax.set_title("datazione archivio", fontsize=16, fontweight="bold", pad=20)
ax.set_xlabel("Decennio", fontsize=12, fontweight="bold", labelpad=10)
ax.set_ylabel("Numero di oggetti per decennio (max: 130)", fontsize=11, fontweight="bold", labelpad=10)

ax.tick_params(axis="x", rotation=45, labelsize=10)
ax.grid(axis="y", linestyle="--", alpha=0.5)
ax.set_axisbelow(True)

# Posizionamento legenda
ax.legend(
    barre_create,
    etichette_legenda,
    title="Provenienza (totale capi)",
    loc="upper left",
    bbox_to_anchor=(1.01, 1),
    fontsize=8.5,
    title_fontsize=10.5
)

# 8. Salvataggio delle immagini
plt.tight_layout()
plt.savefig(output_img1, dpi=300, bbox_inches="tight")
plt.savefig(output_img2, dpi=300, bbox_inches="tight")
plt.close()

print("Grafico generato con successo!")
print(f"File salvati:\n- {output_img1}\n- {output_img2}")
