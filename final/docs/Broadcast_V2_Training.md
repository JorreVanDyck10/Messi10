# Broadcast v2 — trainingsdata en gemeten balverbetering

Update 28 oktober: deze oorspronkelijke vergelijking blijft bewaard. Er is nu
ook een [v3-tegelkandidaat en ruimere handmatige kalibratie](Verbeteringen_20261028.md).
De geselecteerde v2- en v3-gewichten zijn via Git LFS beschikbaar.

Deze ronde verbetert de voorbereiding van de eerder verzamelde beelden en
voert een echte, beperkte baltraining uit. Er zijn geen nieuwe bronbeelden
bijgeteld. De bestaande spelersdetector en de actieve standaardconfiguraties
zijn behouden. De nieuwe balgewichten zijn lokaal beschikbaar als optioneel
experimenteel profiel.

## Verbeteringen aan de data

De aanvullende spelerselectie bewaart één trainingsbeeld per clipseconde.
Binnen die seconde krijgt een beeld met meer geannoteerde officials voorrang,
gevolgd door scherpte. Alle 1.710 bronseconden uit de 57 trainingsclips blijven
vertegenwoordigd met 1.710 beelden, tegenover de eerdere 6.000. De mediane
afstand tussen trainingsframes stijgt van 0,2 naar 1,0 seconde. Het aandeel
afstanden onder 0,5 seconde daalt van 100% naar 13,7%.

Alle 2.000 validatiebeelden en hun speler-/officiallabels zijn ongewijzigd.
Dit is een minder redundante trainingsoptie; de spelerherkenning is in deze
ronde niet opnieuw getraind of als nauwkeuriger gepresenteerd. De oorspronkelijke
6.000 trainingsbeelden blijven beschikbaar.

Voor ballen zijn er 640 × 640-uitsneden die exact de oorspronkelijke pixels
behouden. Er is geen resizing of nieuwe JPEG-compressie: PNG-crops zijn pixel
voor pixel met hun bron vergeleken. De bal staat op verschillende plaatsen in
de trainingscrops. Alle crops van een bronbeeld behouden dezelfde wedstrijdsplit.

Van 36 volledige negatieve kandidaten zijn er 34 visueel door AI gecontroleerd
en behouden. Twee uitsneden met een mogelijk extra balletje worden uitgesloten.
Een ontbrekend label maakt een uitsnede nooit automatisch negatief. Twee
identieke cropvensters zijn eveneens verwijderd.

| Baltaak | Positief | Gecontroleerd negatief | Totaal |
|---|---:|---:|---:|
| Training | 175 | 22 | 197 |
| Validatie | 73 | 12 | 85 |

Deze 282 crops komen uit 132 oorspronkelijke beelden. De validatiecrops
vertegenwoordigen 73 bronbeelden uit drie wedstrijden; sommige negatieve
crops komen uit dezelfde validatiebeelden als de positieve crops.

| Dataset | Trainingsbestand | Klassen |
|---|---|---|
| Minder redundante spelerset | `data/broadcast-training-v2/players/data.yaml` | 0 speler, 1 official |
| Native balcrops | `data/broadcast-training-v2/balls/data.yaml` | 0 bal |
| Dezelfde crops voor de bestaande COCO-kop | `data/broadcast-training-v2/ball-coco/data.yaml` | 32 sports ball; andere COCO-klassen niet gesuperviseerd |

## Werkelijk uitgevoerde training en vergelijking

Het nieuwe balmodel start van F005 en traint twaalf epochs: invoer 640,
batch 4, eerste tien lagen vast, AdamW met basisleertempo 0,0001, mixed precision
en seed 42. Mosaic, mixup en schaalaugmentatie staan uit. De run gebruikte de
RTX 3050 Laptop GPU. De volledige daadwerkelijke instellingen staan in
`artifacts/broadcast-ball-v2/fine-tune/args.yaml`.

Voor en na worden binnen elke rij dezelfde beelden en inferentie-instellingen
gebruikt. AP gebruikt een confidencevloer van 0,001. Aantallen hieronder gebruiken
confidence 0,25 en matching-IoU 0,5. AP@50:95 gebruikt de bestaande
101-puntsimplementatie; dit is niet de volledige COCO-benchmark.

| Invoerroute | AP@50:95 voor → na | Gevonden labels voor → na | Ongekoppelde detecties voor → na |
|---|---:|---:|---:|
| 85 native crops, 73 ballabels | 10,34% → 25,55% | 21 → 36 | 10 → 2 |
| 73 volledige beelden, invoer 1280 | 10,95% → 18,01% | 28 → 22 | 33 → 10 |
| Dezelfde 73 volledige beelden, 640-tegels | 10,19% → 23,34% | 23 → 36 | 33 → 12 |

De optionele profielen gebruiken de geteste 640-tegelroute: tegels van 640,
invoer 640, overlap 0,2 en globale NMS-IoU 0,5. Op de twaalf gecontroleerde
negatieve validatiecrops hebben beide modellen nul detecties vanaf 0,25.

De route zonder tegels heeft op de vaste confidencegrens minder gevonden
labels na training. Gebruik de kandidaat daarom met zijn tegelconfiguratie.
Er is geen nieuwe confidencegrens op de validatie gekozen.

Deze scores gelden voor een kleine, AI-gecurateerde ontwikkelset. De drie
validatiewedstrijden waren al bij eerdere ontwikkeling betrokken. Er is geen
menselijke labelgoedkeuring of onafhankelijke eindtest ingevuld. Op volledige
beelden kunnen extra fysieke ballen ontbreken in de labels; een ongekoppelde
voorspelling is daar niet automatisch een bewezen fout.

## Gebruiken in de bestaande app

Kies bij **Modelprofiel**:

- **Spelers v3 + broadcastbal v2 — experimentele combinatie** voor de bestaande
  speler-/officialdetector plus het nieuwe balmodel;
- **Broadcastbal v2 — native tegels, experimenteel** voor alleen de baltaak.

De bestanden zijn `configs/models-players-ball-broadcast-v2.json` en
`configs/models-ball-broadcast-v2.json`. De profielscanner ontdekt ze automatisch.
Een echte runtimecontrole van de combinatie laadt beide modellen en produceert
spelers-, official- en baldetecties. Dit is een integratiecontrole, geen
gezamenlijke nauwkeurigheidsmeting.

De lokale gewichten staan in `artifacts/broadcast-ball-v2/broadcast_ball_v2.pt`.
SHA-256: `0bfd52b880a6994b646c78374fb00156ba211b3a464f8c8a273873f9b5d2bb52`.
Deze kandidaat is niet als actieve standaard ingesteld.

## Controle en herhaling

`reports/broadcast-data/v2-summary.json` bevat de datacontroles;
`v2-experiment.json` de daadwerkelijke voorspellingsevaluaties;
`v2-negative-review.json` elke negatieve reviewbeslissing. Onder de artefactmap
staan voorspellingen, foutlijsten en de werkelijke trainingsbroncodekopie.
Alle 48 gerichte data-, crop- en modeloverdrachttests slagen.

Een volgende datasetversie voorbereiden en met dezelfde frozen review controleren:

```powershell
$env:PYTHONPATH = "$PWD\src;$PWD"
.\.venv\Scripts\python.exe -m scripts.prepare_broadcast_v2 --output data/broadcast-training-v2-next
.\.venv\Scripts\python.exe -m scripts.prepare_broadcast_v2 --output data/broadcast-training-v2-next --decisions reports/broadcast-data/v2-negative-review.json
```

De review wordt alleen hergebruikt als de voorbereidingsfingerprint exact
overeenkomt. Gewijzigde beelden of crops vereisen een nieuwe review. Bestaande
afgeronde datasets worden niet overschreven.

Een volgende, afzonderlijke trainingsrun starten:

```powershell
.\.venv\Scripts\python.exe -m scripts.experiment_broadcast_v2 --dataset data/broadcast-training-v2 --output artifacts/broadcast-ball-v2-next --epochs 12
```

De huidige wrapper legt broncode en parameters vast en weigert een onderbroken
training als voltooid voor te stellen. De oorspronkelijke afgeronde run gebruikte
de bewaarde `artifacts/broadcast-ball-v2/experiment-source.py`; de latere wrapper
voegt expliciete hervattingscontroles en versiegebonden rapportnamen toe.
Deze wijzigingen veranderen de gemeten gewichten niet.
