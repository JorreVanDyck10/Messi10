# Sports Vision — werkpakket persoon 1

Werkende hulpmiddelen voor video-inspectie, frame-extractie, assisted bounding-boxannotatie, datasetcontrole, YOLO-training en vergelijkbare detectie-evaluatie. De doellaptop heeft een **RTX 4050**. GPU en geheugen worden op die laptop opnieuw gecontroleerd.

De door de gebruiker gekozen [PANORIS-video](https://www.youtube.com/watch?v=HBTFZwMdcCw) staat volledig in `assets/videos/HBTFZwMdcCw.mp4`, op 3840 × 960 pixels, met bronmetadata en checksum. De MP4 wordt met **Git LFS** beheerd. De lokale ontwikkelmachine heeft een RTX 3050; metingen daarop gelden niet als 4050-benchmark.

**Echte uitvoering:** twee runs van elk 100 epochs zijn afgerond. Validatie-mAP@50 en mAP@50:95 blijven 0%; een trainingsdiagnose van de tweede run geeft 14,85% en 13,07%. Dit zijn voorlopige metingen met expliciet gemarkeerde AI-labels. Lees [de resultaten en foutenanalyse](Resultaten_Balexperimenten.md) voor de betekenis en beperkingen.

## Starten op de 4050-laptop

Installeer Python **3.12**, Git met Git LFS en een werkende NVIDIA-driver. Gebruik voor iedere laptop een eigen projectomgeving; kopieer `.venv` niet van een andere machine.

De implementatie wordt geleverd op branch `main`. Clone die branch op de doellaptop en open de projectmap:

```powershell
git clone --branch main https://github.com/JorreVanDyck10/Messi10.git
cd Messi10
```

Voer daar uit:

```powershell
git lfs install --local
git lfs pull
.\scripts\Setup-Persoon1.ps1
.\scripts\Run-BallExperiment.ps1 -Resolution 1920 -CandidateWeights artifacts/ball-ai-v1/EXP-002-best.pt
```

Dit bouwt de voorlopige baldataset opnieuw op en meet de meegeleverde gewichten en de pretrained referentie op jouw laptop. Het checkpoint is experimenteel; de meetresultaten en beperkingen bepalen of het bruikbaar is. Wil je zelf opnieuw trainen, laat dan `-CandidateWeights` weg.

Voor het oorspronkelijke annotatietraject gebruik je `Start-Persoon1.ps1 -Mode prepare`, vervolgens `-Mode baseline -Split train` en `-Mode annotate -Split train`. Open dan [de lokale annotatietool](http://127.0.0.1:8765) in je browser. De tool toont bronbeelden, automatische voorstellen, boxcorrectie en aparte review. Hij blijft alleen op de eigen computer bereikbaar. Stoppen kan met Ctrl+C in het terminalvenster. De voorlopige baldataset heeft zijn eigen reviewcommando in de dataset-README.

Voor kleine objecten kun je in de annotatietool tot 800% inzoomen en door het vergrote beeld scrollen. Voor de bekeken panorama leverde een aanvullende pretrained proef op 1920 pixels meer bruikbare persoonsvoorstellen op. Je kunt die apart maken en laden:

```powershell
.\scripts\Start-Persoon1.ps1 -Mode baseline -Split train -InferenceSize 1920
.\scripts\Start-Persoon1.ps1 -Mode annotate -Split train -InferenceSize 1920
```

`InferenceSize` verandert alleen inference en de gekozen voorstellenmap; de eerste trainingsreferentie blijft 640. Meer voorstellen of hogere confidence bewijzen zonder referentielabels geen betere nauwkeurigheid.

Wanneer `python` naar een andere versie verwijst, gebruik je bijvoorbeeld `Setup-Persoon1.ps1 -Python 'C:\pad\naar\Python312\python.exe'`. Als PowerShell lokale scripts blokkeert, kun je één script starten met `powershell -ExecutionPolicy Bypass -File .\scripts\Setup-Persoon1.ps1`; dit wijzigt geen blijvend beleid.

Een bestaande uitvoermap wordt niet overschreven. Gebruik voor herhaalde baselines een nieuwe naam, bijvoorbeeld `-RunName baseline-train-640-02`. De annotatiestarter gebruikt standaard de voorstellen uit `runs/baseline-train-640/proposals`; voor een andere map gebruik je de CLI hieronder.

## Wat al is uitgevoerd en wat nog nodig is

Zie [de uitvoeringsstatus](Status_Persoon_1.md) voor echte resultaten en resterende stappen. De oorspronkelijke [uitgebreide werkinstructie](01_Persoon_1_Data_Model_Evaluatie.md) en [invulsjablonen](Invulsjablonen_Persoon_1.md) staan naast de software.

Naast de oorspronkelijke zestig kandidaatbeelden is nu een afzonderlijke **voorlopige baldataset met 47 visueel door AI gecontroleerde frames** opgebouwd: 27 train, 12 validatie en 8 gereserveerd voor test. De route gebruikt een baldetector naast de pretrained personendetector. De [selectie, boxregels en beperkingen](../datasets/panoris-ball-ai-v1/README.md) en alle pixelboxen staan in de repository. Onderlinge menselijke review staat nog open; die wordt niet door de AI-controle vervangen.

De selectie is vóór modelinference vastgelegd: 36 trainframes uit zes tijdgroepen, 12 validatieframes uit twee groepen en 12 gereserveerde testframes uit twee groepen. Het zijn nieuwe momenten uit dezelfde opname, geen onafhankelijke wedstrijden. De genoemde tijdafstand is een controlehulpmiddel en bewijst op zichzelf geen onafhankelijkheid.

## Echte balexperimenten herhalen

Na installatie en `git lfs pull` voert dit de echte training en een gelijke vergelijking met de pretrained baseline uit:

```powershell
.\scripts\Run-BallExperiment.ps1 -Resolution 1920
```

De starter bouwt de 47 bronframes en vastgelegde AI-labels opnieuw op. Hij traint maximaal 100 epochs met `configs/train-ball-1920.json` en maakt voorspellingen, beide mAP-varianten en FP/FN-records op dezelfde 12 validatiebeelden. Geheugentekort verlaagt batch 4 naar 2 en 1. Er wordt geen testinference uitgevoerd. Een unieke uitvoermap bewaart iedere herhaling.

De oorspronkelijke 640-configuratie is eveneens werkelijk getest. Bij deze panorama verwijdert de voorbewerking alle trainingsboxen: op 640 zijn hun breedte en hoogte te klein. Op 960 zouden slechts 4 van de 27 boxen de vastgestelde filter passeren; op 1920 alle 27. Daarom gebruikt het vervolgexperiment 1920 en rechthoekige batches. Zie `reports/ball-preprocessing-diagnostic.json`. De 640-run is een vastgelegd negatief resultaat en geen bruikbare baldetector.

Voor deze duidelijk gemarkeerde ontwikkelroute gebruiken training en scoring expliciet `--provisional-ai-labels` met een inhoudsgebonden AI-attestatie. De standaardroute blijft onafhankelijke teamreview vereisen. Voor de formele eindtest moeten de studenten eerst de labels en besluiten controleren. Scores uit deze voorlopige route mogen niet als menselijk geverifieerde eindresultaten worden voorgesteld.

## Annoteren en reviewen

1. Voer de baseline uit op train en desgewenst val; voer geen ontwikkelbaseline uit op test.
2. Laad automatische voorstellen in de annotatietool, controleer gemiste objecten en corrigeer boxen en klassen.
3. Vul de echte annotatornaam in en bewaar. Een leeg frame moet expliciet als werkelijk negatief worden bevestigd.
4. Laat de andere persoon de bewaarde labels controleren en met een andere naam goedkeuren. Iedere wijziging maakt de oude review ongeldig.
5. Bewaar review en exportvoorbeelden voor het verslag. Onbeslisbare frames blijven buiten de definitieve scored dataset of worden door andere geschikte frames vervangen.

Testannotaties kunnen apart worden gemaakt met `-Mode annotate -Split test`. Gebruik de daarbij opgedane modelinzichten niet voor tuning; automatische modelinference op test vereist een latere systeemfreeze. De tool registreert namen en handelingen, maar verifieert geen menselijke identiteit.

Voor een eigen voorstellenmap:

```powershell
.\.venv\Scripts\python.exe -m persoon1 annotate --manifest data/panoris/manifest.json --proposals runs/mijn-run/proposals --split train
```

## Datasetcontrole en training

```powershell
.\scripts\Start-Persoon1.ps1 -Mode validate
```

De controle geeft fouten bij ontbrekende labels, ongeldige boxen, directe overlap, te korte tijdafstand tussen subsets en ontbrekende onafhankelijke reviews. Nabije visuele duplicaten leveren een waarschuwing voor menselijke controle. Dat labels daadwerkelijk correct zijn, moet visueel worden beoordeeld.

Na de controles kopieer je `configs/approvals-example.json` naar `configs/approvals.json`. Vul alleen echte besluiten en de actuele `dataset_fingerprint` uit het validatierapport in. Beide teamleden moeten labels, splits, klassendekking, bron en modelrollen hebben beoordeeld. Deze voorbeeldgoedkeuring staat bewust standaard op onwaar.

```powershell
.\scripts\Start-Persoon1.ps1 -Mode train
```

De eerste trainingsinstellingen staan in `configs/train-reference.json`: pretrained YOLO11n, 640, batch 4, Adam, learning rate 0.001, maximaal 100 epochs en patience 20. Alleen CUDA-geheugentekort activeert de terugval naar batch 2 en vervolgens 1, steeds vanuit verse pretrained gewichten. Gewichten, werkelijke frameworkconfiguratie, logs en provenance blijven per poging bewaard. Testbeelden worden niet in de trainingsdataset opgenomen.

Een aparte technische proef kan met `python -m persoon1 train ... --smoke`; ook die vereist de echte datasetcontrole en is duidelijk als technische proef gemarkeerd. Een CPU-run is mogelijk met `--device cpu`, maar vormt een andere hardwaremeting.

## Evaluatie en foutenanalyse

Maak voor ieder model expliciet de mapping van **modelklassenaam** naar **datasetklassenaam**. Gebruik voor de pretrained referentie het voorbeeld met `person` en `sports ball`; pas de mapping aan de gekozen definitieve dataset aan. Bij een gespecialiseerde detector gebruik je de werkelijke klassen van dat model.

```powershell
.\.venv\Scripts\python.exe -m persoon1 predict --manifest data/panoris/manifest.json --weights models/yolo11n.pt --mapping configs/mapping-pretrained-example.json --output runs/baseline-val-640 --split val --device 0
.\.venv\Scripts\python.exe -m persoon1 evaluate --manifest data/panoris/manifest.json --predictions runs/baseline-val-640 --output runs/baseline-val-metrics
```

Gebruik voor een fine-tuned model een nieuwe uitvoermap en de bijpassende mapping. Vergelijk daarna:

```powershell
.\.venv\Scripts\python.exe -m persoon1 compare --baseline runs/baseline-val-metrics/metrics.json --candidate runs/fine-val-metrics/metrics.json --output reports/comparison.json
```

Beide modellen worden met **dezelfde evaluator** gemeten: 101-punts geïnterpoleerde box-AP bij IoU 0.50 tot 0.95. Dit is een expliciete projectmeting zonder crowd/ignore-regio's; het is geen claim dat de volledige COCO-benchmark is uitgevoerd. Klassen zonder geannoteerde objecten krijgen geen verzonnen nul-AP. De datasetcontrole verlangt voldoende klassendekking vóór training.

Het vaste confidencewerkpunt voor FP/FN staat los van de laag ingestelde confidence-ondergrens voor de AP-curve. Iedere evaluatie maakt `metrics.json`, `per-class.csv`, `errors.json` en `report.md`. De foutrecords bevatten echte mismatches; hun oorzaken moeten nog visueel worden vastgesteld. De vergelijking weigert verschillende labels, subsets, klassen of relevante inference-instellingen.

## Onafhankelijke eindtest

Leg na modelselectie een freeze vast op basis van de voltooide ontwikkelrun:

```powershell
.\.venv\Scripts\python.exe -m persoon1 freeze --manifest data/panoris/manifest.json --approvals configs/approvals.json --weights models/yolo11n.pt --inference runs/baseline-val-640/run.json --output reports/final-freeze.json
.\.venv\Scripts\python.exe -m persoon1 predict --manifest data/panoris/manifest.json --weights models/yolo11n.pt --mapping configs/mapping-pretrained-example.json --output runs/final-test --split test --freeze reports/final-freeze.json --approvals configs/approvals.json
.\.venv\Scripts\python.exe -m persoon1 evaluate --manifest data/panoris/manifest.json --predictions runs/final-test --output runs/final-test-metrics --freeze reports/final-freeze.json --approvals configs/approvals.json
```

Vervang de voorbeeldgewichten en mapping door de werkelijk geselecteerde configuratie. Dataset, model en inference moeten met de freeze overeenkomen. Testtoegang wordt bij de dataset vastgelegd. Gewijzigde configuraties krijgen niet opnieuw dezelfde beelden als onafhankelijke eindtest. Die discipline blijft ook een verantwoordelijkheid van het team; de bestanden zijn geen onveranderlijk extern auditregister.

## Overdracht en controles

Iedere inferentierun levert `detections.jsonl` met bronvideo-ID, oorspronkelijke frame-index, presentatietijd, beeldafmetingen en boxen in bronpixels. Ook een leeg detectieframe wordt geschreven. `run.json` bevat instellingen, gewichtenchecksum, beeldchecksums en de werkelijke omgeving. Voorstellen staan gescheiden van definitieve labels. Op geselecteerde beelden wordt geen volledige videoverwerking of volledige trackingclaim gebaseerd.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m persoon1 --help
```

De tests gebruiken herkenbaar synthetische fixtures en controleren onder meer AP met handmatig verifieerbare gevallen, dubbele matches, leakage, reviews, coördinaten, variabele framerate en semantische klassekoppeling. Testfixtures tellen niet mee als projectannotaties of trainingsresultaten.

Een extra volledige softwarecontrole van de GPU-trainingsroute is beschikbaar als `python -m persoon1.technical_check`. Die genereert uitsluitend synthetische rechthoeken, voert één epoch uit en bewaart een duidelijk als synthetisch gemarkeerd rapport. Die uitkomst bewijst geen prestatie op voetbalbeelden of geschiktheid van de echte annotaties.

De volledige video en de bewaarde experimentele checkpoints worden via Git LFS gedeeld. Kleine meetbestanden, selectie, labelspecificaties en bewijsbeelden staan in Git. Grote gegenereerde datasets, lokale omgevingen en volledige werkmappen blijven lokaal. Reproduceer hun inhoud via de bronvideo, vastgelegde selectie, versies en manifests.
