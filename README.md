# Analisi della collezione di Abiti da Sera del Victoria and Albert Museum (V&A)

Progetto di analisi dati e storia del costume dedicato agli abiti da sera conservati presso il **Victoria and Albert Museum** di Londra (783 abiti da sera), con un approfondimento specifico sulla produzione di alta moda **francese** realizzata tra il **1950 e il 1969**.

---

## Obiettivi e percorso metodologico

1. **Analisi esplorativa dell'archivio complessivo**: mappatura della distribuzione geografica, dell'andamento cronologico per decenni e dei designer più ricorrenti (con individuazione degli abiti privi di attribuzione). Dai risultati preliminari è emerso che, oltre al Regno Unito (46,7%), la **Francia** rappresenta il secondo nucleo più rilevante della collezione (41,4%, pari a 324 capi), raggiungendo il massimo picco quantitativo proprio nei decenni **1950** e **1960** (rispettivamente **61** abiti francesi su 104 totali negli anni '50 e **71** abiti francesi su 134 totali negli anni '60, per un complesso di 132 capi). Questa evidenza strutturale ha motivato la scelta di concentrare l'analisi successiva sull'alta moda francese del ventennio **1950–1969**.
2. **Arricchimento del catalogo**: integrazione dei dati di base con le schede tecniche ufficiali del museo (*Object history*, *Summary*, *Materials and techniques* e *Physical description*) tramite abbinamento sul numero di accessione.
3. **Mappatura biografica dei designer principali**: individuazione dei 20 couturier più ricorrenti nell'archivio e ricostruzione del loro profilo biografico (luogo di nascita, nazione principale di attività e periodo di carriera).
4. **Analisi dell'alta moda francese (1950–1969)**:
   * studio dei materiali tessili e decorativi più utilizzati;
   * profilazione sociale delle indossatrici e analisi delle occasioni d'uso più frequenti;
   * confronto diacronico tra gli **anni Cinquanta (1950–1959)** e gli **anni Sessanta (1960–1969)** per committenza, occasioni d'uso, evoluzione delle silhouette e tecniche sartoriali.
5. **Sintesi divulgativa**: generazione automatica di relazioni critiche in lingua italiana e di un report HTML navigabile offline.

---

## Fonti dei dati

* **Victoria and Albert Museum (V&A) Collections API (`api.vam.ac.uk/v2`)**: dati catalografici, descrizioni fisiche, materiali, tecniche e storia degli oggetti.
* **Wikidata API & Wikipedia API**: dati biografici, luoghi di nascita, sedi di attività e cronologia delle carriere dei designer.
* **Elaborazione semantica via LLM**: estrazione, classificazione e traduzione in italiano di materiali, ruoli sociali, occasioni d'uso, silhouette e tecniche di confezione.

---

## Struttura dei file del progetto

### 1. Dataset principali (CSV)
* `evening_dresses_iniziale.csv`: dataset iniziale ottenuto dall'API del V&A Museum.
* `evening_dresses_pulito.csv`: dataset ripulito con le informazioni essenziali dei capi.
* `evening_dresses_arricchito.csv`: dataset completo arricchito con le colonne `Materiali`, `Storia dell'oggetto` e `Riassunto`.

### 2. Dati strutturati e sintesi testuali (JSON e TXT)
* `dati biografici 20 designer più diffusi.json`: dati biografici (luogo di nascita, nazione di attività, periodo di carriera) dei 20 stilisti più frequenti nell'archivio.
* `analisi_indossatrici_francia_1950_1969.json`: classificazione per singolo abito francese (1950–1969) di posizione sociale/ruolo, occasione d'uso ed eventuale persona citata.
* `analisi_stilistica_francia_1950_1969.json`: classificazione stilistica per singolo abito francese (1950–1969) relativa a silhouette e tecniche sartoriali/costruttive.
* `descrizione_indossatrici_e_occasioni.txt`: sintesi discorsiva in italiano su committenza, profilo sociale e occasioni d'uso.
* `sintesi_stilistica_anni50_vs_anni60.txt`: sintesi critica in italiano sull'evoluzione delle silhouette e delle tecniche di confezione tra anni '50 e anni '60.

### 3. Visualizzazioni e Tabelle (PNG)

#### Fase 1 — Composizione generale dell'archivio (analisi esplorativa iniziale)
* `provenienza geografica.png`: grafico a torta sulla distribuzione geografica complessiva dell'archivio (Regno Unito 46,7%, Francia 41,4%, Stati Uniti 4,7%, Italia 3,2%, ecc.).
* `datazione archivio.png` / `datazione archivio.png`: istogramma impilato per decenni (dal 1760 al 2010) con suddivisione per provenienza geografica, allineato ai criteri cronologici delle analisi successive (**61** abiti francesi nel 1950 e **71** nel 1960, con picco complessivo di 134 capi nel decennio 1960).
* `designer più frequenti.png`: grafico a barre orizzontali sui 20 designer più ricorrenti e sul peso degli abiti senza designer assegnato (*Ignoti / Unknown*: 130 capi su 783, pari al 16,6%, su un totale di 225 designer distinti censiti).

#### Fase 2 — Approfondimento biografico, materiali e analisi Francia 1950–1969
* `tabella_top20_designer.png`: tabella riepilogativa dei 20 designer più frequenti dell'archivio con luogo di nascita, nazione di attività e periodo di carriera.
* `materiali_francia_1950_1969.png`: grafico a torta dei materiali più impiegati negli abiti francesi (1950–1969).
* `indossatrici_e_occasioni_francia_1950_1969.png`: grafici a barre orizzontali su posizione sociale/professione e occasioni d'uso (1950–1969).
* `confronto tra anni 50 e anni 60.png`: confronto comparativo tra 1950–1959 (61 abiti francesi) e 1960–1969 (71 abiti francesi) su profilo sociale e occasioni d'uso.
* `confronto_stilistico_anni50_vs_anni60.png`: confronto comparativo tra 1950–1959 (61 abiti francesi) e 1960–1969 (71 abiti francesi) su silhouette e tecniche sartoriali/moderne.

### 4. Report finale
* `report_evening_dresses_v&am.html`: pagina HTML autonoma (con CSS interno, senza dipendenze esterne né JavaScript) che raccoglie indicatori quantitativi, grafici e approfondimenti testuali. Apribile direttamente con doppio clic in qualsiasi browser.

---

## Requisiti e utilizzo

* **Linguaggio**: Python 3.x (eseguibile tramite IDLE su macOS o da terminale).
* **Librerie richieste**: moduli standard di Python (`csv`, `json`, `urllib`, `re`, `html`, `collections`, `textwrap`, `ssl`, `time`) e `matplotlib` per la generazione dei grafici e delle tabelle.
* **Ordine consigliato di esecuzione**:
  1. Analisi esplorativa iniziale dell'archivio (`provenienza geografica.png`, `datazione archivio.png`, `designer più frequenti.png`).
  2. Estrazione biografica dei 20 designer più frequenti (`dati biografici 20 designer più diffusi.json` e relativa tabella).
  3. Arricchimento del CSV con i dati V&A (`Materiali`, `Storia dell'oggetto`, `Riassunto`).
  4. Analisi dei materiali, delle indossatrici/occasioni e del confronto stilistico anni '50 vs anni '60 (generazione dei file `.json`, `.txt` e `.png`).
  5. Generazione della pagina finale `report_evening_dresses_v&am.html`.
