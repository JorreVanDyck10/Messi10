# Van gelabelde data naar spelertracking

**Telregels voor de veldherkenning:** zie [Spelertelling en rollen](Spelertelling_en_Rollen.md). Alleen de rol `player` met een geldig voetpunt binnen het actuele veld telt mee en gaat naar spelertracking. Andere rollen blijven afzonderlijk beschikbaar. De huidige gewichten hebben uitsluitend `player` en de gezamenlijke officialklasse `referee`; extra rolondersteuning in de code betekent nog geen getrainde steward- of supporterherkenning.

**Nieuwe feitelijke overdracht:** zie [het resultatenverslag](Resultaten_Spelermodel.md), `reports/players-experiments/handoff.json`, `configs/models-players.json` en `artifacts/players-v2/players_best.pt`. De gewichten zijn daadwerkelijk getraind met 0=player en 1=referee. AI-review, gedeeltelijke officialdekking en eindtestbeperkingen zijn expliciet vastgelegd. De historische checklist hieronder is geen bewijs van menselijke acceptatie.

## Oorspronkelijke acceptatieafspraken

De ByteTrack-adapter en vijf seconden waargenomen trajecten zijn al geïmplementeerd. De huidige PANORIS-baseline levert `person` en `ball`. De gebruiker koos expliciet om pas echte spelertracking te gebruiken na levering van echte spelerklassen; tijdelijke person-tracking is niet toegevoegd.

## Eerst afspraken bij de labels

- `player`: veldspelers én doelmannen. Een afzonderlijke doelmanklasse mag in de overdracht ook expliciet naar `player` worden gemapt.
- `referee`: scheidsrechters, afzonderlijk van spelers.
- `person`: iemand van wie niet betrouwbaar is vastgesteld dat die een speler of scheidsrechter is. Dit wordt niet automatisch `player`.
- `ball`: optioneel en afzonderlijk; gaat niet naar de spelertracker of de grondprojectie.

Leg de werkelijke klasse-ID's vast in de datasetconfiguratie. Het voorbeeld `configs/player-class-mapping.example.json` veronderstelt 0=player, 1=referee, 2=ball; pas dat aan als de werkelijke dataset anders is ingedeeld. Alleen de naam in een configuratie veranderen maakt bestaande person-annotaties niet betrouwbaar tot spelersannotaties: die betekenis moet uit de labels en review blijken.

Bewaar train-/val-/testgroepen en frameherkomst. Houd de gereserveerde testgroepen buiten ontwikkeling. Meer labels veranderen het bestaande `yolo11n.pt` niet: persoon 1 moet eerst trainen en evalueren. ByteTrack zelf hoeft geen nieuw model op deze labels te trainen; handmatige identiteitreferenties voor tracking-evaluatie zijn een afzonderlijke stap.

## Wat persoon 1 aanlevert

1. Commit met de labels, datasetconfiguratie en review-/splitmanifesten.
2. Getrainde gewichten, bijvoorbeeld `players_best.pt`, met SHA-256. Deel grote gewichten via LFS of afgesproken opslag; niet als gewone Git-binary.
3. Werkelijke klasse-ID's en klassennamen en de expliciete semantische mapping.
4. Evaluatierecord en geselecteerde modelversie. Geen kwaliteitsclaim op basis van alleen het aantal labels.
5. Inference-instellingen, softwareversies en eventuele wijzigingen aan bronvideo of detectieformaat.

De training blijft in de eigen omgeving van persoon 1. Het registreren hieronder installeert geen trainingsdependencies en start geen training.

## Eerstvolgende checklist voor persoon 1

- [ ] Leg `player` (inclusief doelmannen), `referee` en eventuele extra klassen vast vóór verdere annotatie.
- [ ] Lever beelden én bijbehorende labels aan met datasetconfiguratie, video-/frameherkomst en reproduceerbare paden. Voorkom verwijzingen die alleen op de eigen laptop werken.
- [ ] Laat labels reviewen, leg train-/val-/testgroepen vast en controleer dubbele of bijna identieke frames. Houd gereserveerde testbeelden buiten ontwikkeling.
- [ ] Train een echte detector op de goedgekeurde labels en selecteer de gewichten op ontwikkel-/validatiegegevens.
- [ ] Bewaar de evaluatierun en lever `players_best.pt`, SHA-256, werkelijke klasse-ID's/namen, mapping, inference-instellingen en softwareversies aan.
- [ ] Push code, kleine configuraties, manifests en rapporten. Maak grote beelden/gewichten bereikbaar via de afgesproken opslag of Git LFS; alleen een pointer zonder toegankelijk bestand is geen volledige overdracht.
- [ ] Meld bij de overdracht de commit en wijzigingen in videobron, splits, coördinaten of detectieformaat.

Bij de synchronisatie op 16 oktober 2026 bevatte `main` tot commit `9d38af9` drie extra clips onder `assets/videos/teamtrack/`, maar geen bijbehorende volledige label-/spelermodeloverdracht. Hun beschikbaarheid is nog geen bewijs van gereviewde labels of een getraind spelersmodel. Bij keuze van een andere clip moet persoon 2 de video-identiteit, constante framerate en camerageometrie opnieuw controleren en een passende kalibratie maken. PANORIS-punten worden niet op deze andere video's hergebruikt.

Na de eerste geslaagde speler-MVP maakt persoon 1 voor de tracking-evaluatie handmatige referentie-ID's op de korte ontwikkelfragmenten; persoon 2 reviewt die. Dit staat los van de bounding-boxlabels voor detectortraining.

## Registreren in de pipelineomgeving

Zet de gewichten lokaal in `weights/players_best.pt`. Maak `configs/player-class-mapping.json` met de werkelijke mapping. Registreer daarna vanuit de projectmap:

```powershell
.\.venv\Scripts\python.exe -m football_pipeline register-player-model weights\players_best.pt --mapping configs\player-class-mapping.json --output configs\models-players.json --model-id players_v1 --imgsz 1920 --confidence 0.10 --iou 0.70 --device cpu --evaluation-record reports\players-evaluation.json
```

Vervang het evaluatiepad door het werkelijke bestand. De optie `--evaluation-record` is technisch optioneel, zodat een integratieproef mogelijk blijft; voor de definitieve overdracht is het evaluatierecord wel nodig. De inference-resolutie moet bij de gekozen modelproef horen. 1920 is hier een vertrekpunt, geen bewijs van betere nauwkeurigheid.

Het commando leest de werkelijke klassennamen uit de gewichten, controleert de mapping, berekent gewichtshashes en gebruikt de reguliere manifestvalidatie. Een COCO-klasse `person` kan hiermee niet als `player` worden geregistreerd. Bestaande profielen worden niet overschreven; gebruik bij een nieuwe versie bijvoorbeeld `models-players-v2.json` met een nieuwe model-ID. Registratie bevestigt geen menselijke MVP-acceptatie of modelnauwkeurigheid.

## Via de frontend testen

1. Ververs de lokale Streamlit-pagina, laad de clip en controleer de kalibratie.
2. Kies onder **Modelprofiel** het nieuwe spelersprofiel. Bestanden `configs/models*.json` verschijnen bij een rerun; een herstart of wijziging van een omgevingsvariabele is niet nodig.
3. Verwerk eerst zonder tracking. Controleer geometrie, synchronisatie, afspeelbaarheid, actuele detecties en runtime. De eerdere technische person-pilot vervangt deze controle niet.
4. Leg de werkelijke MVP-review vast:

```powershell
.\.venv\Scripts\python.exe -m football_pipeline accept-mvp runs\RUNMAP --reviewer "Echte naam reviewer" --confirm-review
```

5. Vink **Spelertracking en trajecten toevoegen** aan en laad het gemaakte `runs/RUNMAP/mvp_acceptance.json`.
6. Verwerk opnieuw: actuele spelers krijgen dezelfde tijdelijke ID op video en minimap, met maximaal vijf seconden traject. Na ontbrekende of ongeldige waarnemingen blijft een zichtbare onderbreking.

Bij een andere modelkeuze schakelt de interface tracking uit en verwijdert ze het oude resultaat uit de weergave. De pipeline controleert dat de MVP-review bij precies dezelfde video, kalibratie, gewichten, instellingen en omgeving hoort. Een profiel zonder `player` blijft geblokkeerd.

Een track-ID is geen spelersnaam en kan bij overlap of verdwijnen wisselen. Onderzoek dat op de afgesproken ontwikkelfragmenten met onafhankelijke handmatige referentie-ID's.
