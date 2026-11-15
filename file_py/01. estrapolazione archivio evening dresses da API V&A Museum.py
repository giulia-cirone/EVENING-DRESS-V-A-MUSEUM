import json
import time
import requests

base_url = "https://api.vam.ac.uk/v2/objects/search"

# Parametri corretti per l'endpoint V&A
params = {
    "q": "evening wear",
    "q_object_type": "evening dress",
    "page_size": 100,
    "page": 1,
}

all_records = []

while True:
  res = requests.get(base_url, params=params)
  if res.status_code != 200:
    print(f"Errore {res.status_code}")
    break

  data = res.json()
  records = data.get("records", [])
  if not records:
    break

  # Filtro per escludere stampe/vignette e tenere solo gli abiti effettivi
  for r in records:
    obj_type = (r.get("objectType") or "").lower()
    if "dress" in obj_type or "gown" in obj_type:
      all_records.append(r)

  total_api = data.get("info", {}).get("record_count", 0)
  print(f"Pagina {params['page']}: raccolti finora {len(all_records)} abiti...")

  # Si ferma quando le pagine finiscono o abbiamo superato il totale
  if params["page"] * params["page_size"] >= total_api or len(records) < params[
      "page_size"
  ]:
    break

  params["page"] += 1
  time.sleep(0.2)

output_file = "/Users/giulia/Desktop/evening_dresses_iniziale.json"
with open(output_file, "w", encoding="utf-8") as f:
  json.dump(all_records, f, ensure_ascii=False, indent=2)

print(
    f"\nDownload completato! Salvati {len(all_records)} abiti in '{output_file}'"
)
