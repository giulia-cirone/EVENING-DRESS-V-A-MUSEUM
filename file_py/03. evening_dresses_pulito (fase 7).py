import csv
from collections import Counter

input_csv = "/Users/giulia/Desktop/evening_dresses_pulito.csv"
output_csv = "/Users/giulia/Desktop/evening_dresses_pulito.csv"

righe_da_mantenere = []
conteggio_eliminate = Counter()
totale_righe_iniziali = 0

# 1. Lettura ed elaborazione in memoria (nessuna modifica su disco)
with open(input_csv, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    
    col_tipo = next((c for c in fieldnames if c.strip().lower() == "tipo oggetto"), None)
    
    if not col_tipo:
        print("Errore: colonna 'Tipo Oggetto' non trovata nel file CSV!")
        exit()
        
    for row in reader:
        totale_righe_iniziali += 1
        valore = (row.get(col_tipo) or "").strip()
        
        # Mantiene esclusivamente le righe il cui tipo oggetto è "evening dress" (case-insensitive)
        if valore.lower() == "evening dress":
            righe_da_mantenere.append(row)
        else:
            conteggio_eliminate[valore] += 1

totale_eliminate = sum(conteggio_eliminate.values())

# 2. Anteprima a video
print("=" * 65)
print("              ANTEPRIMA DELLE MODIFICHE")
print("=" * 65)
print(f"Righe totali nel file attuale:          {totale_righe_iniziali}")
print(f"Righe con solo 'evening dress':        {len(righe_da_mantenere)}")
print(f"Righe diverse che verranno rimosse:     {totale_eliminate}")
print("-" * 65)

if totale_eliminate > 0:
    print("Campione delle tipologie che verranno eliminate:")
    for voce, count in conteggio_eliminate.most_common(10):
        nome_mostrato = voce if voce else "(valore vuoto)"
        print(f"  • {nome_mostrato}: {count} riga/he")
else:
    print("Il file contiene già esclusivamente la voce 'Evening dress'.")

print("=" * 65)

# 3. Richiesta di conferma
conferma = input("\nVuoi procedere e salvare le modifiche su 'evening_dresses_pulito.csv'? (s/n): ").strip().lower()

if conferma == "s":
    with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(righe_da_mantenere)
    print(f"\nModifiche salvate con successo! File aggiornato con {len(righe_da_mantenere)} righe.")
else:
    print("\nOperazione annullata: il file NON è stato modificato.")
