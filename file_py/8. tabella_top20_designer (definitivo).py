import csv
import json
import textwrap
import matplotlib.pyplot as plt

# Percorsi dei file sul Desktop del Mac
file_json = "/Users/giulia/Desktop/dati biografici 20 designer più diffusi.json"
file_csv = "/Users/giulia/Desktop/tabella_top20_designer.csv"
file_png = "/Users/giulia/Desktop/tabella_top20_designer.png"

# 1. Lettura del file JSON esistente e correzione del luogo di nascita di Schiaparelli
with open(file_json, "r", encoding="utf-8") as f:
    dati_designer = json.load(f)

for record in dati_designer:
    luogo = record.get("luogo_nascita", "")
    if "palazzo corsini" in luogo.lower() or "schiaparelli" in record.get("designer", "").lower():
        if "palazzo corsini" in luogo.lower():
            record["luogo_nascita"] = "Roma (Italia)"

# 2. Salvataggio del JSON aggiornato
with open(file_json, "w", encoding="utf-8") as f:
    json.dump(dati_designer, f, ensure_ascii=False, indent=2)

# 3. Aggiornamento del file CSV
intestazioni = ["#", "Designer", "Abiti", "Luogo di nascita", "Luogo di attività (Nazione)", "Periodo di attività"]
righe_tabella = []

for rec in dati_designer:
    righe_tabella.append([
        str(rec["posizione"]),
        rec["designer"],
        str(rec["abiti_archivio"]),
        rec["luogo_nascita"],
        rec["luogo_attivita"],
        rec["periodo_attivita"]
    ])

with open(file_csv, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(intestazioni)
    writer.writerows(righe_tabella)

# 4. Rigenerazione della tabella in formato immagine PNG
dati_per_figura = []
for r in righe_tabella:
    dati_per_figura.append([
        r[0],
        textwrap.fill(r[1], width=24),
        r[2],
        textwrap.fill(r[3], width=28),
        textwrap.fill(r[4], width=22),
        textwrap.fill(r[5], width=22)
    ])

fig, ax = plt.subplots(figsize=(16.5, 13.5))
ax.axis("off")

tabella = ax.table(
    cellText=dati_per_figura,
    colLabels=["#", "Designer", "Abiti", "Luogo di nascita", "Luogo di attività\n(Nazione)", "Periodo di attività"],
    loc="center",
    cellLoc="left",
    colWidths=[0.035, 0.20, 0.055, 0.26, 0.22, 0.23]
)

tabella.auto_set_font_size(False)
tabella.set_fontsize(9)
tabella.scale(1, 2.25)

for (row, col), cell in tabella.get_celld().items():
    cell.set_edgecolor("#CCCCCC")
    if row == 0:
        cell.set_facecolor("#1f4e78")
        cell.get_text().set_color("white")
        cell.get_text().set_weight("bold")
    elif row % 2 == 1:
        cell.set_facecolor("#f4f7fa")
    else:
        cell.set_facecolor("#ffffff")

ax.set_title("I 20 Designer più frequenti dell'archivio: biografia e carriera", fontsize=15, fontweight="bold", pad=15)
plt.tight_layout()
plt.savefig(file_png, dpi=300, bbox_inches="tight")
plt.close()

print("Correzione applicata con successo a tutti e 3 i file:")
print(f"  1. JSON: {file_json}")
print(f"  2. CSV:  {file_csv}")
print(f"  3. PNG:  {file_png}")
