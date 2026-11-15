import csv

input_csv = "/Users/giulia/Desktop/evening_dresses_pulito.csv"
output_csv = "/Users/giulia/Desktop/evening_dresses_pulito.csv"

righe_uniche = []
url_visti = set()
conteggio_doppioni = 0

with open(input_csv, "r", encoding="utf-8-sig") as f:
  reader = csv.DictReader(f)
  fieldnames = reader.fieldnames

  for row in reader:
    url = (row.get("URL Miniatura") or "").strip()

    # Se l'URL è presente ed è già stato incontrato, scarta la riga
    if url and url in url_visti:
      conteggio_doppioni += 1
      continue

    # Se l'URL è valorizzato, memorizzalo per identificare i successivi doppioni
    if url:
      url_visti.add(url)

    righe_uniche.append(row)

# Salvataggio delle righe prive di duplicati
with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
  writer = csv.DictWriter(f, fieldnames=fieldnames)
  writer.writeheader()
  writer.writerows(righe_uniche)

print(f"Rimozione duplicati completata!")
print(f"- Righe duplicate eliminate: {conteggio_doppioni}")
print(f"- Righe totali rimanenti: {len(righe_uniche)}")
print(f"- File aggiornato: {output_csv}")
