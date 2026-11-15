import csv
from collections import Counter
import matplotlib.pyplot as plt
import textwrap

# Percorsi sul Desktop del Mac
input_csv = "/Users/giulia/Desktop/evening_dresses_pulito.csv"
output_img = "/Users/giulia/Desktop/provenienza geografica.png"

# Strutture dati per il conteggio
conteggio_stati = Counter()
conteggio_sconosciuti = 0

# 1. Lettura del file CSV ed estrazione dei dati dalla colonna "Stato"
with open(input_csv, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    col_stato = next((c for c in reader.fieldnames if c.strip().lower() == "stato"), None)
    
    if not col_stato:
        print("Errore: la colonna 'Stato' non è presente nel file CSV!")
        exit()
        
    for row in reader:
        stato = (row.get(col_stato) or "").strip()
        
        # Le celle vuote o non specificate confluiscono in "Sconosciuti"
        if not stato or stato.lower() in {"non specificato", "sconosciuto", "unknown"}:
            conteggio_sconosciuti += 1
        else:
            conteggio_stati[stato] += 1

totale_complessivo = sum(conteggio_stati.values()) + conteggio_sconosciuti

if totale_complessivo == 0:
    print("Nessun dato trovato per generare il grafico.")
    exit()

# 2. Selezione dei primi 6 stati noti e aggregazione del resto in "Altro"
stati_noti_ordinati = conteggio_stati.most_common()
top_6 = stati_noti_ordinati[:6]
altri_stati = stati_noti_ordinati[6:]

# Liste per il grafico a torta
stati_grafico = [elem[0] for elem in top_6]
conteggi_grafico = [elem[1] for elem in top_6]

# Aggiunta della macro-categoria "Altro" (se ci sono stati oltre i primi 6)
totale_altro = sum(elem[1] for elem in altri_stati)
if totale_altro > 0:
    stati_grafico.append("Altro")
    conteggi_grafico.append(totale_altro)

# Aggiunta della categoria "Sconosciuti"
if conteggio_sconosciuti > 0:
    stati_grafico.append("Sconosciuti")
    conteggi_grafico.append(conteggio_sconosciuti)

# 3. Funzione per etichette nelle fette (percentuale + conteggio assoluto)
def formatta_etichetta(pct):
    valore = int(round(pct * totale_complessivo / 100.0))
    # Mostra il testo dentro la fetta solo se >= 1.5% per evitare sovrapposizioni
    if pct >= 1.5:
        return f"{pct:.1f}%\n({valore})"
    return ""

# 4. Creazione della figura con Matplotlib
fig, ax = plt.subplots(figsize=(12, 8))

# Palette colori: assegniamo tonalità distinte e un grigio per "Sconosciuti"
palette = list(plt.cm.tab20.colors[:len(stati_grafico)])
if "Sconosciuti" in stati_grafico:
    idx_sconosciuti = stati_grafico.index("Sconosciuti")
    palette[idx_sconosciuti] = "#B0BEC5"  # Grigio neutro

fette, testi, testi_auto = ax.pie(
    conteggi_grafico,
    autopct=formatta_etichetta,
    startangle=140,
    pctdistance=0.8,
    colors=palette,
    wedgeprops={"edgecolor": "white", "linewidth": 1.2}
)

for t in testi_auto:
    t.set_fontsize(9)
    t.set_fontweight("bold")

# 5. Costruzione delle voci della legenda con dettaglio per "Altro"
etichette_legenda = []
for stato, qta in zip(stati_grafico, conteggi_grafico):
    pct = qta / totale_complessivo * 100
    if stato == "Altro":
        # Formattazione dell'elenco degli stati minori
        dettaglio_stati = ", ".join([f"{s} ({c})" for s, c in altri_stati])
        dettaglio_wrap = textwrap.fill(dettaglio_stati, width=44)
        dettaglio_indented = "\n   ".join(dettaglio_wrap.split("\n"))
        etichette_legenda.append(f"Altro: {qta} ({pct:.1f}%)\n   [{dettaglio_indented}]")
    else:
        etichette_legenda.append(f"{stato}: {qta} ({pct:.1f}%)")

# Posizionamento della legenda esterna a destra
ax.legend(
    fette,
    etichette_legenda,
    title="Stati (oggetti e %)",
    loc="center left",
    bbox_to_anchor=(1.02, 0.5),
    fontsize=9,
    title_fontsize=11
)

# Titolo e impostazione circolare
ax.set_title("provenienza geografica dell'archivio", fontsize=16, pad=20, fontweight="bold")
ax.axis("equal")

# 6. Salvataggio su file immagine ad alta risoluzione
plt.tight_layout()
plt.savefig(output_img, dpi=300, bbox_inches="tight")
plt.close()

print("Grafico generato con successo e salvato in:")
print(output_img)
