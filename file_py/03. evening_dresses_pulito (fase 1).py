import csv
import re

# Percorsi sul tuo Desktop Mac
input_csv = "/Users/giulia/Desktop/evening_dresses_iniziale.csv"
output_csv = "/Users/giulia/Desktop/evening_dresses_pulito.csv"


def inverti_cognome_nome(valore):
  """Se il nome è in formato 'Cognome, Nome', inverte in 'Nome Cognome' rimuovendo la virgola."""
  if not valore:
    return ""
  valore = valore.strip()
  if "," in valore:
    parti = [p.strip() for p in valore.split(",") if p.strip()]
    if len(parti) == 2:
      return f"{parti[1]} {parti[0]}"
    elif len(parti) > 2:
      return f"{' '.join(parti[1:])} {parti[0]}"
  return valore


def uniforma_ruolo(valore):
  """Sostituisce con 'Designer' qualsiasi dicitura che contenga 'design' (es."""
  if not valore:
    return ""
  valore_pulito = valore.strip()
  if re.search(r"design", valore_pulito, flags=re.IGNORECASE):
    return "Designer"
  return valore_pulito


def pulisci_luogo(valore):
  """Rimuove '(city)' o '(City)' dal campo luogo."""
  if not valore:
    return ""
  return re.sub(r"\s*\(\s*city\s*\)", "", valore, flags=re.IGNORECASE).strip()


righe_pulite = []
with open(input_csv, "r", encoding="utf-8-sig") as f:
  reader = csv.DictReader(f)
  fieldnames = reader.fieldnames

  for row in reader:
    # 1. Correzione Designer (Nome Cognome)
    if "Designer" in row:
      row["Designer"] = inverti_cognome_nome(row["Designer"])

    # 2. Correzione Ruolo ('Designer')
    if "Ruolo" in row:
      row["Ruolo"] = uniforma_ruolo(row["Ruolo"])

    # 3. Correzione Luogo (rimozione di '(city)')
    if "Luogo" in row:
      row["Luogo"] = pulisci_luogo(row["Luogo"])

    righe_pulite.append(row)

# Salvataggio del nuovo file CSV pulito
with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
  writer = csv.DictWriter(f, fieldnames=fieldnames)
  writer.writeheader()
  writer.writerows(righe_pulite)

print(
    f"Operazione completata! Elaborate {len(righe_pulite)} righe e salvate in:"
)
print(output_csv)
