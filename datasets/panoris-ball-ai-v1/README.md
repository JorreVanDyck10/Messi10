# Voorlopige balannotaties op echte voetbalbeelden

De 47 boxen in `selection.json` zijn door Codex visueel aangewezen en gecontroleerd op bronresolutie en in vergrote uitsneden. Dit zijn **AI-annotaties met openstaande menselijke review**. Ze zijn geen automatisch goedgekeurde teamlabels. Beide studenten moeten ze inhoudelijk beoordelen voordat ze voor de formele eindtest tellen.

De gekozen route gebruikt een afzonderlijke baldetector naast de oorspronkelijke pretrained personendetector. Alleen de klasse `ball` wordt op deze dataset getraind en gemeten. Een `person`-voorspelling bewijst geen speler- of scheidsrechterrol.

## Selectie en beperkingen

Er zijn 27 trainframes uit vijf tijdgroepen, 12 validatieframes uit twee andere groepen en 8 testframes uit twee gereserveerde groepen. De tijdgroepen komen uit de eerder vastgelegde selectie. Dertien extra trainingsbeelden liggen 0,2 seconde na een helder oorspronkelijk trainingsbeeld en blijven in dezelfde groep. Deze beelden vergroten de annotatieomvang, maar vormen geen dertien onafhankelijke spelsituaties.

Onduidelijke oorspronkelijke kandidaten zijn expliciet uitgesloten, niet als negatieve beelden gelabeld. De opgenomen beelden hebben elk één zichtbare, lokaliseerbare bal. Daardoor gelden de resultaten uitsluitend voor deze geselecteerde zichtbare balsituaties. Ze meten niet hoe het systeem werkt als de bal onzichtbaar is, en onderbouwen geen algemene foutpositieve frequentie op een volledige video. Testselectie gebruikte bronzichtbaarheid, geen modeluitvoer. Er is nog geen testinference uitgevoerd.

Het vaste veld geeft sterke globale beeldgelijkenis tussen subsets. Tijdafstand alleen bewijst geen statistische onafhankelijkheid. De claim blijft beperkt tot andere momenten uit dezelfde opname. De verdeling en actie-inhoud moeten nog door het team worden gereviewd.

## Toegepaste boxregels

- Gebruik de zichtbare balgrens in het oorspronkelijke beeld. Neem de zichtbare bewegingswaas mee; schat geen verborgen volledige balvorm.
- Controleer kleine objecten vergroot én in hun spelcontext; schoenen, shirts en veldlijnen zijn geen ballen.
- Corrigeer voorstellen die alleen de helderste kern omvatten of een schoen meenemen. Alle opgenomen ballen blijven zichtbaar lokaliseerbaar.
- Teken geen locatie voor een volledig verborgen of onbeslisbaar object. Zulke kandidaten zijn uitgesloten.
- Er zijn geen gecontroleerde negatieve voorbeelden in deze versie. Een lege automatische voorspelling wordt nooit een negatief referentielabel.

De eerste componentvoorstellen op kleur en helderheid en de bestaande YOLO-voorstellen hielpen bij het zoeken. De boxen zijn daarna visueel gecontroleerd. Dit vervangt de onafhankelijke proefannotatie door beide studenten niet.

## Opnieuw opbouwen

Vanuit de repository, na installatie en `git lfs pull`:

```powershell
.\.venv\Scripts\python.exe -m persoon1.project_dataset --video assets/videos/HBTFZwMdcCw.mp4
```

Dit controleert de volledige videohash, decodeert de oorspronkelijke frames, schrijft YOLO-labels, vergrote bewijsuitsneden, een manifest, een validatierapport en een afzonderlijke AI-attestatie. Bronbeelden blijven lokaal onder `data/panoris-ball-ai-v1`; de volledige selectie en pixelboxen zijn hier versieerbaar.

Voor menselijke review:

```powershell
.\.venv\Scripts\python.exe -m persoon1 annotate --manifest data/panoris-ball-ai-v1/manifest.json --split train
```

Controleer eveneens `val` en `test`. Laat eerst een student de labels onder de eigen naam bewaren en daarna de andere student onafhankelijk reviewen. Leg daarna werkelijke gezamenlijke besluiten vast. Een labelcorrectie vereist een nieuwe datasetversie en hernieuwde meting van alle referentiemodellen. De AI-attestatie vervangt de formele teamgoedkeuring niet.
