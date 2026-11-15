# Uitvoeringsstatus persoon 1

**Vervolg uitgevoerd:** [baldetail behouden en F005 getraind](Verbetering_Baldetectie_Detailbehoud.md), met een gelijke vergelijking op 51 volledige validatiebeelden, echte gecombineerde video-overdracht en 78 gerichte rolreviewgevallen. De suite slaagt nu met 238 tests en vier subtests. Menselijke review, een onafhankelijke eindtest en een nieuwe 4050-meting blijven open. De onderstaande derde ronde is een eerder meetmoment.

**Actuele uitvoering, 26 oktober 2026:** [werkpakket 1, derde ronde](Uitvoering_Persoon_1_Derde_Ronde.md) bevat de nieuwe technische data-audit, 93 extra rolcrops, vijf echte roltrainingen, twee baltrainingen, kopmenging, evaluatie, acht checkpoints en overdracht. De samengevoegde suite slaagt met 225 tests en 4 subtests. De later ontvangen 56 volledige beelden zijn technisch gecontroleerd; op hun 14 validatiebeelden halen alle drie bevroren balmodellen bij imgsz 1280 nul AP. R007 blijft standaard; R015 en F003 zijn kandidaten met expliciete toepassingsgrenzen. Menselijke review en een onafhankelijke eindtest blijven open. De onderstaande oudere aantallen en scores zijn historische uitvoeringsnotities, geen actuele totaalscore.

## Historische uitvoeringsnotities

De laatste synchronisatie bevat daarnaast 130 volledige beelden uit drie nieuwe leveringen. Hun technische validators en dataloaders slagen eveneens. Er staan nu 146 achtklassenbeelden en daarnaast 40 drieklassenbeelden; de aanvullende 130 zijn niet gebruikt in de al afgeronde trainingen of in de genoemde 14-frame-balmeting. Zie het actuele verslag voor de precieze scopes.

**Actuele rol-/teamuitbreiding:** [R007 is werkelijk getraind en geïntegreerd](Resultaten_Rollen_en_Teams.md), inclusief extra bronbeelden, echte validatie en een aparte overdracht. Spelers krijgen A/B of onbekend. Supporters en kleine centrale officials blijven zwak; er is geen universele betrouwbare rolherkenning of menselijke review geclaimd. Het tweeklassenprofiel blijft als basisprofiel bewaard.

**Nieuwe speleroplevering:** [TeamTrack-spelermodel, dataset, echte metingen en overdracht](Resultaten_Spelermodel.md). Het standaardprofiel gebruikt nu `player`/`referee`; de onderstaande balstatus blijft als afzonderlijk experiment gelden. Er is nog geen volledige verre officialdekking of onafhankelijke projecteindtest.

**Bijgewerkt op 16 oktober 2026. Echte fine-tuning en project-mAP zijn nu uitgevoerd.** De resultaten zijn voorlopig wegens openstaande menselijke labelreview; de validatiescores tonen nog geen verbetering. Zie [het volledige resultatenverslag](Resultaten_Balexperimenten.md).

## Werkelijk afgerond

- Gekozen bronvideo volledig gedownload en gedeeld via Git LFS, met bronmetadata en checksum.
- Vastgezette Python-, PyTorch-, CUDA- en Ultralytics-omgeving ingericht. Doelhardware: RTX 4050. Werkelijke uitvoerhardware: RTX 3050 Laptop GPU, 4 GB.
- Oorspronkelijke tijdgroepen voor inference gereserveerd en zestig kandidaatframes geëxtraheerd.
- Voorlopige baldataset gemaakt: 47 visueel door AI gecontroleerde bronframes, verdeeld in 27 train, 12 validatie en 8 gereserveerde testframes. Pixelboxen, YOLO-labels, uitsluitingen, bewijsbeelden en reproductiecode zijn bewaard.
- Twee echte runs van elk 100 epochs uitgevoerd, met batch 4 en verse pretrained YOLO11n-initialisatie. EXP-001: 640. EXP-002: 1920 met rechthoekige batches. De synthetische softwareproef blijft daarvan gescheiden.
- Voorbewerkingsprobleem vastgesteld: op 640 verwijdert de trainingsfilter alle 27 balboxen; op 1920 blijven ze behouden.
- Baseline en beide checkpoints op dezelfde twaalf validatiebeelden gemeten, bij gelijke inferentieresoluties van 640 en 1920. **Alle validatierijen: mAP@50 = 0% en mAP@50:95 = 0%.**
- Trainingsdiagnose voor EXP-002: **mAP@50 = 14,85%, mAP@50:95 = 13,07%**, met 4 TP, 0 FP en 23 FN bij confidence 0,25. Dit is geen onafhankelijke prestatiemeting.
- Checkpoints, volledige instellingen, logs, curves, meetbestanden, vergelijkingen, beslissingen, fouten en AI-gebruik bewaard. Geen checkpoint is gepromoveerd tot bruikbare baldetector.
- Overdracht voor persoon 2: twaalf bronmomenten met 135 persoonsvoorspellingen en correcte lege balrecords bij confidence 0,25. Identiteiten, tijdstempels en oorspronkelijke pixelcoördinaten gecontroleerd.
- 36 automatische softwaretests geslaagd. De voorlopige AI-route kan geen formele eindtest of menselijke goedkeuring nabootsen.

## Openstaande inhoudelijke stappen

| Onderdeel | Wat nog nodig is |
|---|---|
| Annotatiebetrouwbaarheid | Beide studenten maken en bespreken de zes onafhankelijke proefannotaties en reviewen het volledige pakket |
| Splits | Actie-inhoud, groepsgrenzen en waarschuwingen voor visuele overeenkomst gezamenlijk beoordelen |
| Bron en modelrollen | Geometrie door persoon 2 en gezamenlijke keuzes inhoudelijk bevestigen |
| Bruikbare baldetectie | De validatiefouten ondersteunen een nieuwe ontwikkelhypothese; er is nog geen bewezen verbetering |
| Onafhankelijke eindtest | Na menselijke review en modelselectie eerst een systeemfreeze; nog geen testinference uitgevoerd |
| Geïntegreerde toepassing | Homography, tactical map en synchronisatie door persoon 2 integreren en controleren |
| Verdediging | Beide studenten moeten keuzes, code, fouten, beperkingen en AI-hulp zelf kunnen uitleggen |

De oorspronkelijke kandidaatdataset onder data/panoris blijft een historisch ontwikkelpakket met person/ball. Oudere rapporten met lege mAP-velden gaan over dat pakket vóór referentielabels. Nieuwe echte projectmetingen staan onder reports/ball-experiments en horen bij panoris-ball-ai-v1.

## Meteen gebruiken op de 4050-laptop

Volg de README voor installatie en git lfs pull. Meet de bewaarde gewichten na met:

```powershell
.\scripts\Run-BallExperiment.ps1 -Resolution 1920 -CandidateWeights artifacts/ball-ai-v1/EXP-002-best.pt
```

Voor opnieuw trainen laat je -CandidateWeights weg. De starter schrijft nieuwe uitvoermappen en bewaart de werkelijke hardware. De menselijke review staat beschreven in datasets/panoris-ball-ai-v1/README.md.
