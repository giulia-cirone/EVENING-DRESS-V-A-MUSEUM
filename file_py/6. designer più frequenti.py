import csv
from collections import Counter
import matplotlib.pyplot as plt

# Percorsi sul Desktop del Mac
input_csv = "/Users/giulia/Desktop/evening_dresses_pulito.csv"
output_img = "/Users/giulia/Desktop/designer più frequenti.png"

conteggio_designer = Counter()
conteggio_ignoti = 0

# 1. Lettura del file CSV ed estrazione dei designer
with open(input_csv, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    
    col_designer = next((c for c in fieldnames if "designer" in c.strip().lower() or "maker" in c.strip().lower()), None)
    
    if not col_designer:
        print("Errore: colonna del designer non trovata nel CSV!")
        exit()
        
    for row in reader:
        designer = (row.get(col_designer) or "").strip()
        
        if not designer or designer.lower() in {"unknown", "sconosciuto", "non specificato", "anonymous", "anonimo"}:
            conteggio_ignoti += 1
        else:
            conteggio_designer[designer] += 1

totale_abiti = sum(conteggio_designer.values()) + conteggio_ignoti
totale_designer_distinti = len(conteggio_designer)

if totale_abiti == 0:
    print("Nessun dato trovato per creare il grafico.")
    exit()

# 2. Selezione dei 20 designer più frequenti
top_20 = conteggio_designer.most_common(20)

# 3. Preparazione delle categorie per il grafico
nomi_grafico = [elem[0] for elem in reversed(top_20)]
valori_grafico = [elem[1] for elem in reversed(top_20)]
colori = ["#1f77b4"] * len(nomi_grafico)

nomi_grafico.append("Ignoti / Unknown")
valori_grafico.append(conteggio_ignoti)
colori.append("#e74c3c")

# 4. Creazione del grafico con Matplotlib
fig, ax = plt.subplots(figsize=(13, 9))
barre = ax.barh(nomi_grafico, valori_grafico, color=colori, edgecolor="white", height=0.68)

max_val = max(valori_grafico)
for barra, val in zip(barre, valori_grafico):
    pct = (val / totale_abiti) * 100
    ax.text(
        barra.get_width() + (max_val * 0.01),
        barra.get_y() + barra.get_height() / 2,
        f"{val} ({pct:.1f}%)",
        va="center",
        ha="left",
        fontsize=9,
        fontweight="bold",
        color="#222222"
    )

# 5. Formattazione assi e titolo
ax.set_title("Designer più frequenti", fontsize=16, fontweight="bold", pad=25)
ax.set_xlabel("Numero di abiti", fontsize=12, fontweight="bold", labelpad=10)
ax.set_ylabel("Designer", fontsize=12, fontweight="bold", labelpad=10)

ax.set_xlim(0, max_val * 1.15)
ax.tick_params(axis="y", labelsize=10)
ax.tick_params(axis="x", labelsize=10)

ax.grid(axis="x", linestyle="--", alpha=0.5)
ax.set_axisbelow(True)

testo_box = (
    f"Archivio complessivo: {totale_abiti} abiti\n"
    f"Designer distinti censiti: {totale_designer_distinti}\n"
    f"Abiti di designer ignoti: {conteggio_ignoti} ({conteggio_ignoti/totale_abiti*100:.1f}%)"
)
ax.text(
    0.98, 0.05,
    testo_box,
    transform=ax.transAxes,
    fontsize=10,
    verticalalignment="bottom",
    horizontalalignment="right",
    bbox=dict(boxstyle="round,pad=0.6", facecolor="#f8f9fa", edgecolor="#cccccc", alpha=0.95)
)

# 6. Salvataggio del grafico
plt.tight_layout()
plt.savefig(output_img, dpi=300, bbox_inches="tight")
plt.close()

print(f"Grafico salvato con successo in:\n{output_img}")
