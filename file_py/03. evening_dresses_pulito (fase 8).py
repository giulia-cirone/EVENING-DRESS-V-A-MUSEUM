import csv
from collections import Counter

input_csv = "/Users/giulia/Desktop/evening_dresses_pulito.csv"
output_csv = "/Users/giulia/Desktop/evening_dresses_pulito.csv"

# Mappa delle forme brevi o varianti verso la forma canonica estesa
MAPPA_DESIGNER = {
    # Balmain
    "balmain": "Pierre Balmain",
    "pierre balmain": "Pierre Balmain",
    "house of balmain": "Pierre Balmain",
    
    # Dior
    "dior": "Christian Dior",
    "christian dior": "Christian Dior",
    "house of dior": "Christian Dior",
    "christian dior london": "Christian Dior",
    
    # Schiaparelli
    "schiaparelli": "Elsa Schiaparelli",
    "elsa schiaparelli": "Elsa Schiaparelli",
    
    # Balenciaga
    "balenciaga": "Cristóbal Balenciaga",
    "cristobal balenciaga": "Cristóbal Balenciaga",
    "cristóbal balenciaga": "Cristóbal Balenciaga",
    
    # Givenchy
    "givenchy": "Hubert de Givenchy",
    "hubert de givenchy": "Hubert de Givenchy",
    
    # Chanel
    "chanel": "Coco Chanel",
    "gabrielle chanel": "Coco Chanel",
    "coco chanel": "Coco Chanel",
    "house of chanel": "Coco Chanel",
    
    # Lanvin
    "lanvin": "Jeanne Lanvin",
    "jeanne lanvin": "Jeanne Lanvin",
    
    # Vionnet
    "vionnet": "Madeleine Vionnet",
    "madeleine vionnet": "Madeleine Vionnet",
    
    # Worth
    "worth": "Charles Frederick Worth",
    "charles frederick worth": "Charles Frederick Worth",
    "house of worth": "House of Worth",
    
    # Saint Laurent
    "saint laurent": "Yves Saint Laurent",
    "yves saint laurent": "Yves Saint Laurent",
    "ysl": "Yves Saint Laurent",
    
    # Grès
    "gres": "Madame Grès",
    "grès": "Madame Grès",
    "madame gres": "Madame Grès",
    "madame grès": "Madame Grès",
    "alix": "Madame Grès",
    
    # Poiret
    "poiret": "Paul Poiret",
    "paul poiret": "Paul Poiret",
    
    # Patou
    "patou": "Jean Patou",
    "jean patou": "Jean Patou",
    
    # Fath
    "fath": "Jacques Fath",
    "jacques fath": "Jacques Fath",
    
    # Paquin
    "paquin": "Jeanne Paquin",
    "jeanne paquin": "Jeanne Paquin",
    
    # Fortuny
    "fortuny": "Mariano Fortuny",
    "mariano fortuny": "Mariano Fortuny",
    "mariano fortuny y madrazo": "Mariano Fortuny",
    
    # Designer britannici
    "hartnell": "Norman Hartnell",
    "norman hartnell": "Norman Hartnell",
    "sir norman hartnell": "Norman Hartnell",
    "amies": "Hardy Amies",
    "hardy amies": "Hardy Amies",
    "sir hardy amies": "Hardy Amies",
    "westwood": "Vivienne Westwood",
    "vivienne westwood": "Vivienne Westwood",
    "muir": "Jean Muir",
    "jean muir": "Jean Muir",
    "rhodes": "Zandra Rhodes",
    "zandra rhodes": "Zandra Rhodes",
    "gibb": "Bill Gibb",
    "bill gibb": "Bill Gibb",
    "stiebel": "Victor Stiebel",
    "victor stiebel": "Victor Stiebel",
    "oldfield": "Bruce Oldfield",
    "bruce oldfield": "Bruce Oldfield",
    "mcqueen": "Alexander McQueen",
    "alexander mcqueen": "Alexander McQueen",
    "galliano": "John Galliano",
    "john galliano": "John Galliano",
    "lucile": "Lucile (Lady Duff Gordon)",
    "lady duff gordon": "Lucile (Lady Duff Gordon)",
    
    # Designer americani ed internazionali
    "halston": "Halston",
    "roy halston frowick": "Halston",
    "mainbocher": "Mainbocher",
    "charles james": "Charles James",
    "james": "Charles James",
    "versace": "Gianni Versace",
    "gianni versace": "Gianni Versace",
    "armani": "Giorgio Armani",
    "giorgio armani": "Giorgio Armani",
    "valentino": "Valentino Garavani",
    "valentino garavani": "Valentino Garavani",
    "cardin": "Pierre Cardin",
    "pierre cardin": "Pierre Cardin",
    "courreges": "André Courrèges",
    "courrèges": "André Courrèges",
    "andre courreges": "André Courrèges",
    "andré courrèges": "André Courrèges",
    "rabanne": "Paco Rabanne",
    "paco rabanne": "Paco Rabanne",
    "ungaro": "Emanuel Ungaro",
    "emanuel ungaro": "Emanuel Ungaro",
    "miyake": "Issey Miyake",
    "issey miyake": "Issey Miyake",
    "yamamoto": "Yohji Yamamoto",
    "yohji yamamoto": "Yohji Yamamoto",
    "kawakubo": "Rei Kawakubo",
    "rei kawakubo": "Rei Kawakubo"
}

def normalizza_designer(nome):
    if not nome:
        return ""
    n_pulito = nome.strip()
    n_lower = n_pulito.lower()
    
    # 1. Ricerca diretta nel vocabolario canonico
    if n_lower in MAPPA_DESIGNER:
        return MAPPA_DESIGNER[n_lower]
    
    # 2. Gestione del formato "Cognome, Nome" (es. "Balmain, Pierre" -> "Pierre Balmain")
    if "," in n_pulito:
        parti = [p.strip() for p in n_pulito.split(",", 1)]
        inverso = f"{parti[1]} {parti[0]}"
        if inverso.lower() in MAPPA_DESIGNER:
            return MAPPA_DESIGNER[inverso.lower()]
        return inverso.title()
        
    return n_pulito

righe_aggiornate = []
modifiche_effettuate = Counter()
totale_righe = 0

# 1. Elaborazione in memoria
with open(input_csv, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    
    col_designer = next((c for c in fieldnames if "designer" in c.strip().lower() or "maker" in c.strip().lower()), None)
    
    if not col_designer:
        print("Errore: nessuna colonna 'Designer' trovata nel file CSV!")
        exit()
        
    for row in reader:
        totale_righe += 1
        valore_orig = (row.get(col_designer) or "").strip()
        valore_norm = normalizza_designer(valore_orig)
        
        if valore_orig and valore_orig != valore_norm:
            modifiche_effettuate[(valore_orig, valore_norm)] += 1
            
        row[col_designer] = valore_norm
        righe_aggiornate.append(row)

# 2. Stampa a video dell'anteprima
print("=" * 70)
print("             ANTEPRIMA UNIFORMAZIONE NOMI DESIGNER")
print("=" * 70)
print(f"Righe totali analizzate:               {totale_righe}")
print(f"Colonna interessata:                   '{col_designer}'")
print(f"Nomi unici che verranno uniformati:    {len(modifiche_effettuate)}")
print(f"Totale righe corrette:                 {sum(modifiche_effettuate.values())}")
print("-" * 70)

if modifiche_effettuate:
    print("Dettaglio delle sostituzioni (PRIMA  -->  DOPO):")
    for (orig, nuovo), count in sorted(modifiche_effettuate.items(), key=lambda x: -x[1]):
        print(f"  • '{orig}'  -->  '{nuovo}' ({count} occorrenze)")
else:
    print("Nessuna modifica necessaria: i nomi sono già tutti uniformati.")

print("=" * 70)

# 3. Richiesta di conferma interattiva
conferma = input("\nVuoi procedere e salvare le modifiche su 'evening_dresses_pulito.csv'? (s/n): ").strip().lower()

if conferma == "s":
    with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(righe_aggiornate)
    print(f"\nModifiche salvate con successo in:\n{output_csv}")
else:
    print("\nOperazione annullata: il file NON è stato modificato.")
