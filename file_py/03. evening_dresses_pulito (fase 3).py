import csv
import re

input_csv = "/Users/giulia/Desktop/evening_dresses_pulito.csv"
output_csv = "/Users/giulia/Desktop/evening_dresses_pulito.csv"


def uniforma_datazione(valore):
  if not valore:
    return ""
  v = valore.strip()

  # 1. Intervalli di decenni con 's' (es. "1900s-1920s" -> "1900 - 1929")
  m_dec_range = re.search(
      r"(\b\d{4})s\s*(?:-|to|/)\s*(\b\d{4})s", v, flags=re.IGNORECASE
  )
  if m_dec_range:
    y1 = int(m_dec_range.group(1))
    y2 = int(m_dec_range.group(2)) + 9
    return f"{y1} - {y2}"

  # 2. Due date a 4 cifre (es. "1970-1974", "1950 - 1956", "1995/1996", "1935 to 1936")
  m_full = re.search(
      r"(\b\d{4}\b)\s*(?:-|to|/)\s*(\b\d{4}\b)", v, flags=re.IGNORECASE
  )
  if m_full:
    return f"{m_full.group(1)} - {m_full.group(2)}"

  # 3. Anno a 4 cifre con abbreviazione a 2 cifre (es. "1968-70" -> "1968 - 1970", "1955-57" -> "1955 - 1957")
  m_short = re.search(
      r"(\b\d{2})(\d{2})\s*(?:-|to|/)\s*(\b\d{2}\b)", v, flags=re.IGNORECASE
  )
  if m_short:
    century = m_short.group(1)
    y1 = century + m_short.group(2)
    y2 = century + m_short.group(3)
    return f"{y1} - {y2}"

  # 4. Decennio singolo (es. "1920s" -> "1920 - 1929", "1840s" -> "1840 - 1849")
  m_decade = re.search(r"(\b\d{4})s\b", v, flags=re.IGNORECASE)
  if m_decade:
    y = int(m_decade.group(1))
    return f"{y} - {y+9}"

  # 5. Secoli scritti in lettere (es. "early 19th century" -> "1800 - 1899")
  m_century = re.search(
      r"(\d{1,2})(?:st|nd|rd|th)\s+century", v, flags=re.IGNORECASE
  )
  if m_century:
    sec = int(m_century.group(1))
    start_year = (sec - 1) * 100
    return f"{start_year} - {start_year + 99}"

  # 6. Singolo anno a 4 cifre (es. "ca. 1957", "March 1959", "late 1996", "14 February 1979")
  anni_trovati = re.findall(r"\b\d{4}\b", v)
  if len(anni_trovati) == 1:
    return anni_trovati[0]
  elif len(anni_trovati) >= 2:
    return f"{anni_trovati[0]} - {anni_trovati[1]}"

  return v


righe_aggiornate = []
with open(input_csv, "r", encoding="utf-8-sig") as f:
  reader = csv.DictReader(f)
  fieldnames = reader.fieldnames

  # Riconosce sia 'Datazione' che 'DATAZIONE'
  col_data = next((c for c in fieldnames if c.lower() == "datazione"), None)

  for row in reader:
    if col_data and row.get(col_data):
      row[col_data] = uniforma_datazione(row[col_data])
    righe_aggiornate.append(row)

with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
  writer = csv.DictWriter(f, fieldnames=fieldnames)
  writer.writeheader()
  writer.writerows(righe_aggiornate)

print("Uniformazione date completata!")
print(f"File salvato: {output_csv}")
