import csv
import json

# Nome del file effettivamente creato sul tuo Desktop
input_json = "/Users/giulia/Desktop/evening_dresses_iniziale.json"
output_csv = "/Users/giulia/Desktop/evening_dresses_iniziale.csv"

with open(input_json, "r", encoding="utf-8") as f:
  data = json.load(f)

rows = []
for item in data:
  maker = item.get("_primaryMaker") or {}
  images = item.get("_images") or {}
  loc = item.get("_currentLocation") or {}

  rows.append({
      "ID Sistema": item.get("systemNumber", ""),
      "Numero Accessione": item.get("accessionNumber", ""),
      "Tipo Oggetto": item.get("objectType", ""),
      "Titolo": item.get("_primaryTitle", ""),
      "Designer": maker.get("name", ""),
      "Ruolo": maker.get("association", ""),
      "Datazione": item.get("_primaryDate", ""),
      "Luogo": item.get("_primaryPlace", ""),
      "Posizione": loc.get("displayName", ""),
      "URL Miniatura": images.get("_primary_thumbnail", ""),
      "URL IIIF": images.get("_iiif_image_base_url", ""),
  })

with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
  if rows:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

print(
    f"Fatto! Creato con successo '{output_csv}' con {len(rows)} abiti da sera."
)
