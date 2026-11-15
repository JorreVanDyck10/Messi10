# Verbetering van teamindeling en dubbele persoonsboxen

Op verzoek `maak het beter` zijn twee concrete softwarefouten aangepakt: dubbele observaties van dezelfde persoon en verwarring tussen shirtkleuren op nieuwe video's. De modelgewichten zijn hierbij behouden. Dit is een vervolgstap op de werkelijk uitgevoerde dataronde; er wordt geen extra trainingsrun of onafhankelijke eindtest geclaimd.

## 1. Minder dubbele detecties en betere voetpunten

De gespecialiseerde detector vond soms alleen het bovenlichaam, terwijl de algemene persoonsdetector dezelfde persoon volledig vond. De gebruikelijke overlapmaat IoU bleef daardoor onder 0,5: beide boxen werden doorgegeven. Dat gaf bijvoorbeeld twee lijnrechterboxen rond één official en een verkeerd laagste punt bij de korte box.

De samenvoeging controleert nu aanvullend op bijna volledige insluiting, overeenkomstige horizontale as en bovenkant, verhouding tussen de hoogtes en verschillende modelbronnen. Een voldoende sterk volledig lichaam krijgt de voorkeur. De oorspronkelijke detectie-identiteit, modelklasse en beeldcoördinaten van die box blijven behouden. De rolclassifier beoordeelt vervolgens de gekozen uitsnede. Gewoon overlappende spelers mogen niet samenvallen; daarvoor zijn gerichte regressietests toegevoegd.

Dezelfde twaalf oorspronkelijke TeamTrack-validatiebeelden, klassen, gewichten, resolutie 1920 en evaluatie-instellingen zijn opnieuw gebruikt. Alle cijfers hieronder zijn **spelersdetectie**, inclusief doelmannen volgens de bestaande labels. Het betreft ontwikkelvalidatie met voorlopige AI-labels.

| Profiel | Speler AP@50 vóór → na | Speler AP@50:95 vóór → na | Correcte detecties TP | Foutieve detecties FP vóór → na | Gemist FN |
|---|---:|---:|---:|---:|---:|
| R007, standaard | 75,42% → 75,96% | 26,07% → 26,26% | 197 → 197 | 53 → 48 | 67 → 67 |
| R009, alternatief | 76,52% → 77,07% | 26,65% → 26,85% | 197 → 197 | 51 → 46 | 67 → 67 |

TP/FP/FN gebruiken confidence 0,25 en match-IoU 0,50; de AP-curve gebruikt alle bewaarde voorstellen vanaf 0,10. De AP-implementatie en klassemapping zijn gelijk gehouden. De gezamenlijke officialscore en het aantal correct aan een team gekoppelde gematchte spelers veranderen hier niet: 192 van 197. De vijf verdwenen FP's zijn dus geen vijf teruggevonden spelers.

Op de ruwe panorama-opname blijft in frame 29 één lijnrechterbox over waar er voorheen twee waren. De behouden box bevat ook zijn benen. Dit beeld heeft geen volledige detectiereferentie en levert daarom geen extra mAP-score op.

## 2. Shirtkleur krijgt een betrouwbaardere betekenis

De eerdere losse hue-histogrammen gaven ook veel gewicht aan de hue van weinig verzadigde pixels. Bij witte/grijze shirts is die kleurhoek een onbetrouwbaar onderscheid. Bovendien werden de eerste twee clusters na slechts drie updates definitief vastgezet.

De nieuwe uitvoering:

1. Weegt de huebijdrage met de verzadiging van iedere pixel. Grijs levert geen huebewijs.
2. Behoudt verdelingen van kleur en helderheid, zodat rugnummers niet als enige mediane shirtkleur gaan gelden.
3. Verwijdert gemengde groene achtergrond, maar behoudt een overwegend groene torso. Dat is een beperkte kleurheuristiek, geen getrainde kledingsegmentatie.
4. Verfijnt de eerste maximaal 200 voldoende zekere spelerobservaties. A/B blijven tijdens het verfijnen op de bestaande clusteridentiteiten uitgelijnd.
5. Laat een te onzekere of afwijkende kleur ongekoppeld. Een nieuw videohash begint opnieuw.

Team A en Team B zijn neutrale namen. De kleurmarge is geen gekalibreerde waarschijnlijkheid. Bestaande wedstrijdspecifieke teamgewichten en hun bekende bronidentiteiten blijven werken; de nieuwe kleurprocedure wordt gebruikt voor video's die niet onder die supervisie vallen. De features van de getrainde rolclassifier zijn niet gewijzigd.

## 3. Vergelijking op vaste referenties, inclusief tegenvallers

Er zijn 54 extra teamreferenties op bestaande rolvalidatiecrops vastgelegd: 48 duidelijke witte/blauwe veldspeleruitsneden en zes rode keepers met **onbekende** teamrelatie. Eén crop met twee overlappende teams is uitgesloten. Alle 55 oorspronkelijke uitsneden en de uitsluitreden blijven zichtbaar op het controleblad. Deze labels zijn door AI visueel gecontroleerd, niet door de twee studenten gereviewd. Ze worden niet stilzwijgend trainingslabels en blijven buiten de bestaande trainingsmanifesten.

De kleurproef krijgt de juiste persoonsboxen en rollen als invoer. Dat is bewust een **voorwaardelijke teammeting**, geen detectie-mAP. Het systeem krijgt de teamlabels niet te zien. Elke bron begint zonder clusters; de opwarmbeelden tellen wel mee als onbekend. Voor de score is hoogstens één A/B-omwisseling per hele video toegestaan, omdat A/B op een nieuwe video geen vaste clubidentiteit hebben.

| Referentiebron | Beoordeelde crops | Correct vóór → na | Verkeerd vóór → na | Onbekend, inclusief opwarming, vóór → na |
|---|---:|---:|---:|---:|
| Oorspronkelijke gebruikersvideo | 50 | 13 → 15 | 0 → 0 | 37 → 35 |
| TeamTrack, zonder bekende-wedstrijdsupervisie in deze kleurproef | 240 | 190 → 185 | 1 → 1 | 49 → 54 |
| Toegevoegde panorama-opname | 48 | 27 → 30 | 5 → 2 | 16 → 16 |
| Totaal | 338 | 230 → 230 | 6 → 3 | 102 → 105 |

De verbetering is gemengd: evenveel correcte koppelingen in totaal, maar half zoveel verkeerde en drie extra onbekende. Op TeamTrack worden vijf extra gevallen afgewezen. De standaardpipeline gebruikt voor de bekende TeamTrack-bron de bestaande supervised teamhead; de volledige detectieproef behoudt daar zijn 192 correcte teamkoppelingen. Deze validatie is gebruikt voor softwarekeuze en is geen onaangeroerde eindtest.

De 24 expliciet geregistreerde TeamTrack-doelmannen zijn uit deze kleurtabel gehouden. Bij de oorspronkelijke video betekent de telling de bestaande teamgelabelde spelerselectie; daar is keepermetadata niet volledig geregistreerd. De zes rode keepers uit de nieuwe opname zijn niet gescoord op correct team: hun team is niet vastgesteld. Twee krijgen toch een kleurcluster. **Een derde keeperskleur blijft dus een open probleem**; hun team mag hieruit niet als bewezen correct worden gerapporteerd.

Een afzonderlijke controle op frame 29 van de ruwe nieuwe video geeft:

| Vijftien duidelijk beoordeelbare enkelvoudige spelersvoorstellen | Voorheen | Nieuw |
|---|---:|---:|
| Juist team | 9 | 15 |
| Verkeerd team | 4 | 0 |
| Onbekend | 2 | 0 |

Dit is een achteraf beoordeeld ontwikkelvoorbeeld. Vijf andere voorstellen zijn expliciet niet als betrouwbare enkelvoudige teamreferentie gebruikt: een smalle lichaamsstrook, een onscherp bovenlichaam, een box om twee blauwe spelers, een rode keeper zonder teamreferentie en een box met twee verschillende teams. Alle twintig crops en hun uitsluitredenen zijn bewaard. Die foute/gecombineerde persoonsboxen blijven een detectiebeperking; alleen een beter shirtlabel lost die niet op.

Ook de verworpen kleurvarianten zijn bewaard: mediane Lab-kleur, circulaire HSV-gemiddelden en verschillende histogramgewichten. Alleen helderheid verlagen of groene pixels onbeperkt behouden gaf elders meer fouten. Zie het experimentregister voor de echte uitkomsten. Deze kleine ontwikkelset bewijst geen algemene prestatie op andere wedstrijden.

## 4. Gezamenlijke toepassing en gebruik

De volledige standaardpipeline is opnieuw uitgevoerd met de bestaande automatische veldwaarnemingen op alle 120 frames van de Commons-ontwikkelclip: detectie, rol/teams, projectiebeleid, export, synchronisatie en H.264-uitvoer zijn gecontroleerd. De veldwaarnemingen zijn hergebruikt voor exact dezelfde videohash; het veldmodel is voor deze vergelijking niet opnieuw getraind. De clip levert nog steeds 0 betrouwbare veldframes: veldposities en aantallen blijven terecht onbekend. Dit is geen verbetering van de automatische veldherkenning.

Daarnaast is de bestaande statische ontwikkelpilot van 150 frames opnieuw uitgevoerd met zijn oorspronkelijke technische kalibratie. Menselijke kalibratiegoedkeuring en MVP-acceptatie blijven uitgeschakeld. De geautomatiseerde audit controleert de telregels: alleen voorspelde spelers met bruikbaar voetpunt binnen het veld tellen mee. Officials, stewards en supporters blijven andere rollen. Een verkeerde rolvoorspelling blijft wel een mogelijke oorzaak van een verkeerde telling.

Start de verbeterde standaarduitvoering vanuit de repository:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\Start-Wedstrijd.ps1
```

Het bestaande R009-alternatief, met betere nieuwe-spelerherkenning maar zwakkere zeldzame rollen, blijft expliciet beschikbaar:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\Start-Wedstrijd.ps1 -Recognition roles-r009
```

Deze codewijzigingen vereisen geen nieuwe modeldownload. De echte videoproeven zijn hier op een RTX 3050 Laptop GPU uitgevoerd; ze worden niet als een nieuwe RTX 4050-meting voorgesteld. Voor de gebruiker blijft GPU-device 0 het startpunt.

## 5. Bewijs en reproductie

- `reports/team-colour-v2/detection-r007/` en `detection-r009/`: nieuwe volledige detectiemetingen, boxen, foutgevallen en teamkoppelingen. De oude vergelijkingsruns blijven in `reports/appearance-experiments/EXP-R007` en `EXP-R009` staan.
- `reports/team-colour-v2/baseline/implementation.py`: exacte oude kleurimplementatie, afkomstig van commit `1d7c299`.
- `baseline/metrics.json` en `final/metrics.json`: alle bron-/label-/implementatiehashes en iedere cropscore.
- `new-match-team-reference.json`, `new-match-team-review.jpg` en `review-index.json`: aanvullende referenties met de voorlopige reviewstatus.
- `raw-r009-final/`: echte inference op frames 0–29, bronidentiteit, instellingen, JSONL en gerenderd beeld.
- `raw-snapshot-comparison.json` en `raw-frame29-team-review.jpg`: de vijftien referenties, vijf uitsluitingen en beide voorspellingen op dezelfde boxen.
- `joint-pipeline.json` en `static-pipeline.json`: technische integratiecontroles, uitvoerpaden, GPU en beperkingen.
- `software-tests.xml`: volledige softwaresuite. Fixtures zijn geen echte modelnauwkeurigheidsreferentie.

Voer de kleurvergelijking uit in een omgeving met de projectdependencies en het project op het Pythonpad, bijvoorbeeld na installatie volgens de README. Gebruik nieuwe uitvoermappen:

```powershell
python -m scripts.evaluate_video_teams --implementation reports/team-colour-v2/baseline/implementation.py --output runs/team-benchmark-before
python -m scripts.evaluate_video_teams --output runs/team-benchmark-after
python -m persoon1.appearance_evaluation --models configs/models-players.json --output runs/detection-merge-check
python -m pytest -q
```

Bronvideo's, beeldafmetingen, train-/val-/testgroepen, modelklassen en gewichten zijn niet veranderd. De huidige code-identiteit zorgt ervoor dat eerdere gecachte video's niet onterecht als uitvoering van de nieuwe code worden hergebruikt. Steward-/supporterherkenning, kleine officials, gecombineerde personenboxen, keeperskleuren en ontbrekende veldkalibratie blijven aantoonbare open punten.
