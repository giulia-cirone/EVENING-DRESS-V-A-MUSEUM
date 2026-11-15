import csv
import re

input_csv = "/Users/giulia/Desktop/evening_dresses_pulito.csv"
output_csv = "/Users/giulia/Desktop/evening_dresses_pulito.csv"


def uniforma_posizione(valore):
  if not valore:
    return ""
  v = valore.strip()

  # Passaggio 1: sostituisce la parola "store" con "in storage" (case-insensitive)
  v = re.sub(r"\bstore\b", "in storage", v, flags=re.IGNORECASE)

  # Passaggio 2: uniforma a "in storage" qualsiasi voce che contenga "storage"
  # (es. "storage", "in storage", "storage - not bookable", ecc.)
  if re.search(r"storage", v, flags=re.IGNORECASE):
    return "in storage"

  return v


righe_aggiornate = []
with open(input_csv, "r", encoding="utf-8-sig") as f:
  reader = csv.DictReader(f)
  fieldnames = reader.fieldnames

  # Riconosce la colonna indipendentemente da maiuscole/minuscole ('Posizione' o 'POSIZIONE')
  col_pos = next((c for c in fieldnames if c.lower() == "posizione"), None)

  for row in reader:
    if col_pos and row.get(col_pos):
      row[col_pos] = uniforma_posizione(row[col_pos])
    righe_aggiornate.append(row)

# Salvataggio del file CSV aggiornato
with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
  writer = csv.DictWriter(f, fieldnames=fieldnames)
  writer.writeheader()
  writer.writerows(righe_aggiornate)

print("Aggiornamento della colonna POSIZIONE completato con successo!")
print(f"File salvato in: {output_csv}")
