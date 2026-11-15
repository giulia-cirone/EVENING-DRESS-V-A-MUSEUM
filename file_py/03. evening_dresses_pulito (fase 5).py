import csv
import re

input_csv = "/Users/giulia/Desktop/evening_dresses_pulito.csv"
output_csv = "/Users/giulia/Desktop/evening_dresses_pulito.csv"

voci_da_eliminare = {
    "evening headdress",
    "dress shirt",
    "pyjama dress",
    "dress fabric",
    "day dress",
    "dress panel",
    "dress trimming",
    "dress front",
    "dress bodice",
    "dress robings",
    "dress fastener",
    "dress ornament",
    "head dress",
}

righe_filtrate = []
righe_eliminate = []
modifiche_esempi = []

# 1. Lettura ed elaborazione solo in memoria (il file su disco non viene toccato)
with open(input_csv, "r", encoding="utf-8-sig") as f:
  reader = csv.DictReader(f)
  fieldnames = reader.fieldnames

  col_tipo = next(
      (c for c in fieldnames if c.strip().lower() == "tipo oggetto"), None
  )

  for row in reader:
    valore_orig = (row.get(col_tipo) or "").strip()

    # Controllo eliminazione
    if valore_orig.lower() in voci_da_eliminare:
      righe_eliminate.append(valore_orig)
      continue

    # Controllo sostituzione Gown -> dress
    valore_nuovo = re.sub(
        r"\bgown\b", "dress", valore_orig, flags=re.IGNORECASE
    ).strip()
    if valore_orig != valore_nuovo and len(modifiche_esempi) < 10:
      modifiche_esempi.append((valore_orig, valore_nuovo))

    row[col_tipo] = valore_nuovo
    righe_filtrate.append(row)

# 2. Mostra a schermo l'anteprima
print("=" * 60)
print("ANTEPRIMA DELLE MODIFICHE (NESSUN FILE È STATO ANCORA TOCCATO)")
print("=" * 60)
print(f"Righe scartate/eliminate: {len(righe_eliminate)}")
if righe_eliminate:
  print(
      "Esempi di voci eliminate:",
      list(set(righe_eliminate))[:5],
  )

print(f"\nEsempi di testi modificati ({len(modifiche_esempi)} mostrati):")
for orig, nuovo in modifiche_esempi:
  print(f"  [PRIMA] '{orig}'  -->  [DOPO] '{nuovo}'")

print(f"\nRighe totali che rimarranno nel foglio: {len(righe_filtrate)}")
print("=" * 60)

# 3. Richiesta di conferma prima di salvare
conferma = input("\nVuoi applicare e salvare queste modifiche? (s/n): ").strip().lower()

if conferma == "s":
  with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(righe_filtrate)
  print("\nOperazione confermata: il file è stato aggiornato con successo!")
else:
  print("\nOperazione annullata: il file NON è stato modificato.")
