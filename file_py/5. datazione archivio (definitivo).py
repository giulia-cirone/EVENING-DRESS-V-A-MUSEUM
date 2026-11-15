import csv
import os
import re
from collections import Counter, defaultdict
import matplotlib.pyplot as plt

# Percorsi dei file sul Desktop del Mac
desktop = "/Users/giulia/Desktop"
csv_arricchito = os.path.join(desktop, "evening_dresses_arricchito.csv")
csv_pulito = os.path.join(desktop, "evening_dresses_pulito.csv")
input_csv = csv_arricchito if os.path.exists(csv_arricchito) else csv_pulito

output_jpg = os.path.join(desktop, "datazione archivio.jpg")
output_png = os.path.join(desktop, "datazione archivio.png")

COLORI_STATI = {
    "Regno Unito": "#1f77b4",
    "Francia": "#aec7e8",
    "Stati Uniti": "#ff7f0e",
    "Italia": "#ffbb78",
    "Spagna": "#2ca02c",
    "Svizzera": "#98df8a",
    "Altri stati": "#8c564b",
    "Sconosciuti": "#b0b0b0",
}

STATI_PRINCIPALI = ["Regno Unito", "Francia", "Stati Uniti", "Italia", "Spagna", "Svizzera"]


def estrai_decennio_coerente(data_str):
    """
    Usa la stessa identica regola delle analisi successive:
    - Se almeno un anno è tra 1960 e 1969 (es. '1959-1960', '1965-1970', '1960s') -> 1960
    - Altrimenti, se almeno un anno è tra 1950 e 1959 (es. '1950s', '1948-1950') -> 1950
    - Per tutti gli altri periodi -> decennio dell'anno più recente.
    """
    if not data_str:
        return None
    anni = [int(a) for a in re.findall(r"\b(1[789]\d\d|20\d\d)s?\b", str(data_str), flags=re.IGNORECASE)]
    if not anni:
        return None
    if any(1960 <= a <= 1969 for a in anni):
        return 1960
    if any(1950 <= a <= 1959 for a in anni):
        return 1950
    return (max(anni) // 10) * 10


def normalizza_stato(stato_str):
    """Uniforma il nome dello stato e raggruppa gli sconosciuti."""
    if not stato_str:
        return "Sconosciuti"
    s = stato_str.strip()
    if s.lower() in {"unknown", "sconosciuto", "sconosciuti", "non specificato", "n/a", "none", ""}:
        return "Sconosciuti"
    return s


# --- 1. LETTURA DEL CSV E CONTEGGIO PER DECENNIO E PROVENIENZA ---

conteggio_dec_stato = defaultdict(Counter)
totale_per_stato = Counter()
dettaglio_altri_stati = defaultdict(Counter)
totale_capi_datati = 0

with open(input_csv, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames or []

    col_data = next((c for c in fieldnames if c.strip().lower() == "datazione"), None)
    col_stato = next((c for c in fieldnames if c.strip().lower() == "stato"), None)

    if not col_data or not col_stato:
        print("Errore: colonne 'Datazione' o 'Stato' non trovate nel CSV.")
        exit()

    for row in reader:
        dec = estrai_decennio_coerente(row.get(col_data, ""))
        if dec is None:
            continue

        stato = normalizza_stato(row.get(col_stato, ""))
        totale_capi_datati += 1
        totale_per_stato[stato] += 1

        if stato in STATI_PRINCIPALI or stato == "Sconosciuti":
            conteggio_dec_stato[dec][stato] += 1
        else:
            conteggio_dec_stato[dec]["Altri stati"] += 1
            dettaglio_altri_stati[stato][dec] += 1

decenni_ordinati = sorted(conteggio_dec_stato.keys())

# Verifica numerica nella IDLE Shell
print("Verifica Francia per decennio (allineata alle analisi successive):")
for d in decenni_ordinati:
    if d in (1950, 1960):
        print(f"  Decennio {d}: Francia = {conteggio_dec_stato[d]['Francia']} abiti | Totale decennio = {sum(conteggio_dec_stato[d].values())}")

# --- 2. PREPARAZIONE DELLE SERIE E DELLA LEGENDA ---

ordine_serie = STATI_PRINCIPALI + ["Altri stati", "Sconosciuti"]
x_pos = list(range(len(decenni_ordinati)))
bottom = [0] * len(decenni_ordinati)

fig, ax = plt.subplots(figsize=(16, 9))

for categoria in ordine_serie:
    valori = [conteggio_dec_stato[d][categoria] for d in decenni_ordinati]
    tot_cat = sum(valori)
    if tot_cat == 0:
        continue

    if categoria == "Altri stati":
        righe_altri = [f"Altri stati ({tot_cat}):"]
        for st_alt, cnt_tot in sorted(
            [(s, sum(c.values())) for s, c in dettaglio_altri_stati.items()],
            key=lambda x: (-x[1], x[0])
        ):
            anni_str = ", ".join(
                f"{d} ({q})" if q > 1 else f"{d}"
                for d, q in sorted(dettaglio_altri_stati[st_alt].items())
            )
            righe_altri.append(f"  • {st_alt} ({cnt_tot}): {anni_str}")
        etichetta_legenda = "\n".join(righe_altri)
    else:
        etichetta_legenda = f"{categoria} ({tot_cat})"

    ax.bar(
        x_pos,
        valori,
        bottom=bottom,
        width=0.66,
        color=COLORI_STATI[categoria],
        edgecolor="white",
        linewidth=0.6,
        label=etichetta_legenda
    )

    for idx, val in enumerate(valori):
        if val >= 6:
            ax.text(
                idx,
                bottom[idx] + val / 2,
                str(val),
                ha="center",
                va="center",
                color="white",
                fontsize=8,
                fontweight="bold"
            )

    bottom = [b + v for b, v in zip(bottom, valori)]

max_totale = max(bottom) if bottom else 1
for idx, tot_dec in enumerate(bottom):
    if tot_dec > 0:
        pct = (tot_dec / totale_capi_datati * 100) if totale_capi_datati else 0
        ax.text(
            idx,
            tot_dec + max_totale * 0.015,
            f"{tot_dec}\n({pct:.1f}%)",
            ha="center",
            va="bottom",
            fontsize=8,
            fontweight="bold",
            color="#222222"
        )

ax.set_xticks(x_pos)
ax.set_xticklabels([str(d) for d in decenni_ordinati], rotation=35, ha="right", fontsize=9.5)
ax.set_ylim(0, max_totale * 1.15)
ax.set_xlabel("Decennio", fontsize=11, fontweight="bold", labelpad=8)
ax.set_ylabel(f"Numero di oggetti per decennio (max: {max_totale})", fontsize=11, fontweight="bold", labelpad=8)
ax.set_title("datazione archivio", fontsize=15, fontweight="bold", pad=14)

ax.legend(
    title="Provenienza (totale capi)",
    loc="upper left",
    bbox_to_anchor=(1.01, 1.0),
    fontsize=8.2,
    title_fontsize=9.5,
    framealpha=0.95
)

plt.tight_layout()
plt.savefig(output_jpg, dpi=300, bbox_inches="tight")
plt.savefig(output_png, dpi=300, bbox_inches="tight")
plt.close()

print(f"\nGrafico aggiornato e salvato sul Desktop in:\n  1. {output_jpg}\n  2. {output_png}")
