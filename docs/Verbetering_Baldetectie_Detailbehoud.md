# Persoon 1 verder uitgevoerd: baldetail behouden en rolproblemen gericht onderzoeken

**26 oktober 2026.** De eerdere nulscore op volledige panoramabeelden is onderzocht met echte, bevroren modelvergelijkingen. Een nieuwe optionele tegelroute behoudt beeldinformatie en werkt in dezelfde lokale detectie-interface. De bestaande R007-rollen, teamindeling en veldtelling blijven behouden. Menselijke annotatiereview en de onafhankelijke eindtest zijn niet als uitgevoerd geregistreerd.

## 1. Onderzoeksvraag en vaste vergelijking

Bij het invoeren van een volledig 4096×1080-panorama op breedte 1280 wordt een bal van zes bronpixels nog geen twee pixels breed. De hypothese was dat dit detailverlies de eerdere nul-AP helpt verklaren. De baseline, F003 en F004 zijn daarom op **dezelfde 14 volledige validatiebeelden met 67 gelabelde ballen** verwerkt onder vier vooraf opgeslagen instellingen:

| Verwerking | Invoer | Aantal detectorpasses per panorama |
|---|---|---:|
| Volledig verkleind | Hele beeld, imgsz 1280 | 1 |
| Volledig op bronbreedte | Hele beeld, imgsz 4096 | 1 |
| Native tegels | Tegels 1280, imgsz 1280 | 4 |
| Kleine tegels vergroot | Tegels 640, imgsz 1280 | 16 |

Overlap is 20%. De tegelgrenzen worden tot de echte beeldranden doorgetrokken. Alle voorspellingen komen terug in oorspronkelijke pixels, gevolgd door globale NMS met IoU 0,50. Lokale NMS is 0,70; AP-confidencevloer is 0,001, werkpunt is 0,25 en match-IoU is 0,50. Per detectorpass geldt maxdet 300; na het samenvoegen is er geen extra globale aantallimiet. Er wordt geen veldmasker of kennis van de gelabelde balpositie gebruikt om voorspellingen te filteren. Alle positieve én negatieve uitkomsten blijven bewaard.

De twee tegelschalen zijn daarna op basis van de ontwikkelresultaten samengevoegd. **Deze multiscale-keuze is een vervolgkeuze na inzage in de afzonderlijke resultaten**, geen vooraf geregistreerde onafhankelijke eindtest. De bronbeelden, gewichten, klassenmapping en labels veranderden hierbij niet.

## 2. Echte resultaten op volledige beelden

De onderstaande AP wordt berekend door de referenties en voorspellingen van beide beeldleveringen samen te nemen. Het is geen ongewogen gemiddelde van twee subsetpercentages.

| Model en verwerking | Bal AP@50 | Bal AP@50:95 | TP / FP / FN bij 0,25 | Zichtbare speelbal gevonden |
|---|---:|---:|---|---:|
| Pretrained, hele beeld 1280 | 0,00% | 0,00% | 0 / 4 / 67 | 0/14 |
| Pretrained, hele beeld 4096 | 51,64% | 19,09% | 28 / 10 / 39 | 4/14 |
| Pretrained, native tegels | 62,98% | 23,04% | 31 / 0 / 36 | 4/14 |
| Pretrained, kleine vergrote tegels | 48,04% | 21,14% | 16 / 0 / 51 | 8/14 |
| Pretrained, beide tegelschalen | 70,19% | 26,47% | 36 / 0 / 31 | 8/14 |
| F003, beide tegelschalen | 74,01% | 26,57% | 34 / 0 / 33 | 4/14 |
| F004, beide tegelschalen | 70,14% | 25,91% | 28 / 0 / 39 | 6/14 |

De labeltaak `ball` omvat ook reserveballen. Daarom staat de zichtbare speelbal **apart als recall**: hoeveel van de veertien zichtbare, geannoteerde speelballen worden met IoU ≥0,50 en confidence ≥0,25 geraakt? Dit is geen speelbal-AP; reservebalvoorspellingen worden voor deze aparte recall niet als foutpositief geteld. Het systeem herkent daarmee nog niet automatisch welke gedetecteerde bal de speelbal is.

Meer invoerresolutie is hier dus aantoonbaar nuttig, maar slechts een deel van het probleem. F003 heeft een iets hogere gezamenlijke AP dan pretrained bij beide tegelschalen, terwijl pretrained twee keer zoveel van de speelbalreferenties vindt. Een model alleen op de hoogste totale bal-AP kiezen zou die relevante afweging verbergen. Nul FP op deze veertien ontwikkelbeelden is geen garantie voor foutloze andere video's.

Alle afzonderlijke scores, voorspellingen, IoU-fouten en configuraties staan in `reports/person1-round4/resolution-transfer`. De gepoolde AP en aparte speelbalreferenties staan in `resolution-summary`. De eerdere nulmetingen blijven ongewijzigd als referentie voor de oude verwerkingsinstelling.

## 3. Werkende interface voor persoon 2 en 3

`football_pipeline.ball_tiles` voert de tegelverwerking uit. Het modelmanifest kan voor een afzonderlijke ballenleverancier `ball_tiles` vastleggen: tegelgroottes, invoerresolutie, overlap en globale NMS. De loader accepteert alleen een echte balbronklasse en begrensde, unieke tegelgroottes. Een generieke persoonsklasse kan daardoor niet via deze optie als bal worden voorgesteld. Bestaande profielen volgen hun oorspronkelijke detectiepad.

De nieuwe optionele profielen zijn:

- `configs/models-ball-tiles.json`: pretrained baldetector met beide tegelschalen.
- `configs/models-players-ball-tiles.json`: dezelfde balroute naast de bestaande R007-rollen en Team A/B.

Start zoals gebruikelijk en kies het gewenste profiel in **Modelprofiel**. Het standaardprofiel wordt niet vervangen. De balleverancier gebruikt de echte COCO-klasse **32, sports ball**; de persoonsleverancier houdt **0, person**. De aanvullende rolclassifier blijft verantwoordelijk voor gespecialiseerde rollen. Een bal is geen grondpersoon en telt niet mee als speler.

Deze verwerking gebruikt twintig detectorpasses per panorama en kost meer tijd dan één verkleinde invoer. De opgeslagen ontwikkeltijden zijn geen 4050-benchmark of garantie op realtimeverwerking. Nieuwe videobronnen blijven de veldkalibratie van persoon 2 nodig hebben.

## 4. Rolherkenning: fouten concreet gemaakt

De al beschikbare voorspellingen van R007, R009 en R015 op dezelfde 468 validatiecrops zijn naast elkaar gelegd. Dat levert **78 reviewgevallen** op:

- 13 gevallen waarin minstens één model een niet-spelerreferentie als speler behandelt: vier generieke personen, drie scheidsrechters en zes supporters.
- 30 overige fouten bij zeldzame rollen of officials.
- 34 overige meningsverschillen tussen modellen.
- Eén overig geval waarin alle drie modellen afwijken van het bestaande AI-label.

Dit zijn aantallen **unieke referentiecrops**, geen aantallen foutieve detecties in volledige video's en geen bewezen aantallen unieke mensen. De categorieën in de prioriteitenlijst zijn exclusief; één geval wordt niet dubbel geteld.

De eerste controlebladen tonen onder meer supporters in clubshirts die door meerdere modellen met zeer hoge confidence als speler worden geclassificeerd. Een hogere algemene confidencedrempel lost zo'n contextfout niet op. Het oorspronkelijke beeld, locatie en rolcontext moeten worden onderzocht; een clubshirt is geen bewijs dat iemand op dat moment veldspeler is. De bestaande veldpoort beschermt de telling wanneer de locatie buiten het geldige veld ligt, maar maakt de rolvoorspelling zelf niet correct.

`reports/person1-round4/role-review/priorities.json` bevat bronverwijzingen, boxen, de drie voorspellingen, redenen en lege reviewerstatus. Zes controlebladen tonen de eerste 72 gevallen. **De oorspronkelijke AI-labels zijn daarbij niet automatisch juist verklaard of gewijzigd.** Een echte correctie vereist broncontext en een nieuwe datasetversie, waarna alle betrokken modellen opnieuw op dezelfde versie worden gemeten.

## 5. Reproduceren

Voer na de gebruikelijke installatie vanuit de repository uit; gebruik bij herhaling nieuwe uitvoermappen:

```powershell
python -m scripts.ball_resolution_experiment --output runs/eigen-resolutieproef
python -m scripts.summarize_ball_resolution --source runs/eigen-resolutieproef --output runs/eigen-resolutiesamenvatting
python -m scripts.prioritize_role_review --output runs/eigen-rolreview
python -m scripts.train_fullscene_ball --run runs/eigen-F005 --config configs/train-fullscene60-ball-native.json
python -m scripts.export_tiled_ball_handoff --video assets/clips20/panorama128057-training48/128057_phase-0540_20s.mp4 --output runs/eigen-tegeloverdracht
```

De gerichte softwaretests controleren randdekking, beide coördinaatassen, dubbele detecties, nabije afzonderlijke ballen, afgesneden trainingsballen, testsetblokkering, ongeldige tegelconfiguratie en semantische klassemapping. De volledige suite slaagt met **238 tests en vier subtests**; het daadwerkelijke JUnit-bestand staat in de rapportmap.

Menselijke review, een onafhankelijke eindtest en een echte nieuwe 4050-meting blijven open. De gegevens komen uit dezelfde ontwikkelopname en dezelfde tijdgroepen. Er wordt geen algemene nauwkeurigheidsclaim over andere wedstrijden gedaan.

## 6. F005 werkelijk getraind en op alle volledige validatiebeelden gemeten

De nieuwe training start opnieuw vanaf pretrained YOLO11n. De COCO-kop met tachtig echte namen blijft behouden, maar alleen klasse **32, sports ball** krijgt positieve supervisie. Deze specialist vervangt geen speler- of persoonsdetector. Hij leert ook reserveballen; er wordt geen apart onderscheid tussen speelbal en reservebal getraind.

De bron is `football-fullscene60-001`: **40 oorspronkelijke trainingsframes en 20 oorspronkelijke validatieframes**. De afgeleide set bevat 159/80 overlappende tegels van 1280×1080, met 236/131 balboxen en 36 gecontroleerde trainingstegels zonder gelabelde bal. Eén trainingstegel is uitgesloten omdat de rand door een balbox liep. Die uitsluiting laat twee originele trainingsbalreferenties zonder tegelvoorbeeld; de gebruikte tegels dekken **208 van de 210** trainingsreferenties en alle **110** validatiereferenties. Overlap veroorzaakt herhaling van objecten, geen nieuwe onafhankelijke objecten of frames.

De aparte audit controleerde voor **alle 239 PNG-tegels** pixelgelijkheid met de oorspronkelijke uitsnede, checksums, oorspronkelijke boxcoördinaten, klasse en behouden tijdgroepen. Er staan geen ingetekende boxen of maskers in de trainingspixels. Bewijs: `EXP-F005/dataset-audit.json`.

| Instelling | Uitgevoerd |
|---|---|
| Start | Pretrained YOLO11n, bestaande 80-klassenkop |
| Input / batch | 1280, rechthoekig / 2 |
| Optimizer / learning-rate | Adam / 0,0001 |
| Vastgezette modules | Eerste 10 |
| Maximum / patience | 50 epochs / 10 |
| Werkelijk / beste checkpoint | 37 epochs / epoch 27 |
| Augmentatie | Horizontaal spiegelen 0,5; overige vastgelegde augmentaties uit |
| Seed / AMP | 42 / aan |
| Hardware | RTX 3050 Laptop, 4 GiB |

`rect=True` schakelt shuffle in de gebruikte Ultralytics-versie uit; dit staat in de werkelijke log. De effectieve batchinstellingen met nbs 64, softwareversies, volledige configuratie, curves en checkpoint zijn opgeslagen. Er was geen OOM-herstart nodig. De frameworkfitness selecteert op tegelvalidatie met alleen de gelabelde balcategorie. Dat is een andere populatie dan de volledige beelden hieronder.

De grotere vergelijking omvat **51 volledige validatieframes uit vijf leveringen**, met **265 balreferenties: 218 reserveballen en 47 zichtbare speelballen**. De oorspronkelijke veertien frames blijven daarin herkenbaar. De beelden komen uit dezelfde twee validatie-tijdgroepen van één opname; dit is geen onafhankelijke eindtest. Vóór het samenvoegen zijn identieke labels en beeldidentiteiten van alle modellen gecontroleerd.

| Zelfde 51 beelden en werkpunt | AP@50 | AP@50:95 | TP / FP / FN | Speelbal gevonden |
|---|---:|---:|---|---:|
| Pretrained, hele beeld 1280 | 0,00% | 0,00% | 0 / 12 / 265 | 0/47 |
| Pretrained, beide tegelschalen | 65,04% | 23,35% | 110 / 5 / 155 | 18/47 |
| F003, beide tegelschalen | 65,52% | 23,41% | 112 / 9 / 153 | 12/47 |
| F005, native tegels | 72,20% | 35,95% | 184 / 25 / 81 | 11/47 |
| F005, beide tegelschalen | 75,70% | 37,88% | 193 / 36 / 72 | 20/47 |
| F005, hele beeld 4096 | 70,12% | 38,01% | 189 / 75 / 76 | 12/47 |

Onder **gelijke multiscale-inferentie** verbetert F005 AP@50 met 10,66 procentpunt en AP@50:95 met 14,53 procentpunt tegenover pretrained. Recall stijgt van 41,51% naar 72,83%, maar precision daalt van 95,65% naar 84,28%. Veel winst betreft reserveballen; de speelbalwinst is slechts twee extra geraakte referenties. Dit is het effect van de gezamenlijke trainingsroute, geen geïsoleerd causaal bewijs voor alleen extra datavolume.

Het hele beeld op 4096 geeft F005 de hoogste AP@50:95, maar slechts 0,13 procentpunt meer dan multiscale en met 75 in plaats van 36 FP. De multiscale-route is daarom een expliciete afweging met minder foutmeldingen; hij wordt niet als winnaar op iedere metriek voorgesteld. Ook F005 op een volledig verkleind 1280-beeld houdt nul AP: training herstelt ontbrekende invoerinformatie niet.

**Keuze:** R007 blijft standaard. Het optionele pretrained tegelprofiel geeft op deze ontwikkelset weinig foutmeldingen. F005 geeft meer gevonden ballen én meer foutmeldingen. Er is geen universele promotie of naderhand aangepaste confidencedrempel. De nieuwe F005-profielen zijn `configs/models-ball-f005.json` en `configs/models-players-ball-f005.json`; de laatste behoudt R007-rollen en Team A/B.

Het geselecteerde gewicht staat in `artifacts/fullscene-ball-v1/fullscene_ball_f005.pt`, SHA-256 **de7d869c01cb8539664c1a3917f6eee90de9d7e655cd484be99999847b0ebf11**. Het bijbehorende `handoff.json` bevat echte klassen, inference, bronversie, resultaten en beperkingen. Andere COCO-klassen uit dit checkpoint zijn niet als verbeterde persoons- of objectdetector geëvalueerd.

## 7. App-uitvoer en overdracht werkelijk gecontroleerd

De applicatiedetector is voor zowel pretrained als F005 op drie oorspronkelijke validatiebeelden aan de meetuitvoer getoetst. Aantallen, bronklasse 32, confidence en oorspronkelijke pixelboxen komen overeen binnen **0,001 pixel en 0,000001 confidence**. De definitieve profielhashes staan in `runtime-equality-final.json` en `runtime-f005-equality.json`; eerdere technische proeven blijven apart bewaard.

Beide gecombineerde profielen zijn echt uitgevoerd op dertig opeenvolgende frames van de bekende 4096×1080-ontwikkelclip. JSONL bevat rollen, Team A/B of onbekend, balboxen, videohash, frame-index en tijdstempel; renderbeelden tonen begin en einde. Alle boxen passen op de oorspronkelijke frames. Zonder veldkalibratie blijft de spelertelling op ieder frame terecht onbekend. Ballen tellen niet als spelers. Dit vervangt geen veldmodel-, tactical-map- of trackingacceptatie van persoon 2 en 3.

De definitieve uitvoer staat in `combined-handoff-final` en `combined-f005-handoff`. Deze video-uitvoering is een technische integratiecontrole, geen geannoteerde video-accuracymeting of 4050-snelheidsbenchmark. De gelijke volledige vergelijking en speelbalreferenties staan in `all-validation-summary`; de complete meetbestanden staan in `full-data-measurements`. Gelijke bestanden in samengestelde en oorspronkelijke experimentmappen zijn hetzelfde bewijs en worden niet als extra uitgevoerde runs geteld.
