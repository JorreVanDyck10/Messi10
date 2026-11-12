# Cursuscheck: een project dat we kunnen uitleggen

Datum: 12 november 2026. Branch: `codex/cursus-eenvoud`.

## Ons besluit

De kern is passend bij de cursus en de challenge. Het project is vooral te breed geworden door alle uitbreidingen samen. We hoeven YOLO, training of homography niet weg te gooien. We kunnen onze basisdemo veel duidelijker maken met **één getrainde detector, een vaste camera en handmatig gekozen veldpunten**.

Daarom is `scripts/Start-Cursus.ps1` toegevoegd. Dit kiest het bestaande P004-basisprofiel met alleen `player` en `referee`. Er is geen tweede personendetector, MobileNet-rolclassifier of teamclassifier in dat profiel. De handmatige veldmodus staat als eerste keuze ingesteld. We verwijderen de bestaande uitbreidingen niet. In de volledige app kan je nog naar andere profielen of automatische veldherkenning schakelen; het is geen nieuwe aparte interface die alles verbergt.

Dit is een eenvoudiger startpad, geen bewijs van betere herkenning. P004 heeft bekende fouten, vooral op andere camera's en bij kleine officials. De clip moet dus echt worden bekeken. Bestaande metingen van R007/R009 gelden niet voor dit eenvoudige profiel.

## Wat is gecontroleerd?

- `1_DL_Setting_the_Scene.pptx`: alle 90 dia's op doorzoekbare tekst gecontroleerd.
- `2_DL_Adv_Deep_Learning.pptx`: alle 72 dia's op doorzoekbare tekst gecontroleerd. Ook de diagrammen op dia's 28, 30, 48, 58, 62 en 66 visueel bekeken. Aanvullend zijn 29, 40 en 59 gerenderd.
- De challenge-PDF en de echte configuraties, detectiecode, veldprojectie, rolclassifier, tracking en startscript vergeleken met die lesinhoud.

De dianummers hieronder zijn de volgorde in het bestand, inclusief titelbladen. Dit zijn de twee beschikbare lesdecks. Dat iets er niet in staat, bewijst niet dat het nooit in een andere les behandeld is. We maken ook onderscheid tussen een onderwerp kort noemen en een algoritme in detail leren.

## Wat sluit rechtstreeks aan op de slides?

| Onderwerp | Waar in de les? | Wat doen wij ermee? | Advies |
| --- | --- | --- | --- |
| Bestaand model aanpassen met weinig taakdata | Les 1, dia 4 | YOLO11n bijtrainen op voetbalbeelden | Behouden. Dit is juist een logische keuze. |
| Betrouwbare data en menselijk toezicht | Les 1, dia's 14, 49, 52-53 en 68-69 | Labels, fouten, onzekere rollen en beperkte datasets bespreken | Meer aandacht aan geven. Dit is belangrijker dan nog een model toevoegen. |
| CNN's | Les 2, dia 66 | Beeldkenmerken leren voor detectie | Op hoofdlijnen uitleggen. De slide behandelt CNN's, niet de volledige YOLO11-architectuur. |
| Trainingscyclus, batch en epoch | Les 2, dia's 28-29 | Batch 4, herhaald trainen en gewichten bijwerken | Kunnen uitleggen met één eigen trainingsrun. |
| Validatie en overfitting | Les 2, dia 30 | Modellen vergelijken op aparte beelden | Behouden. Er is nog geen onaangeroerde onafhankelijke eindtest. |
| Voorbewerking | Les 2, dia's 33-35 | Beelden verkleinen en kleine boxen behouden | Ons 640-versus-1920-probleem is een sterk concreet voorbeeld. |
| Loss, gradients en learning rate | Les 2, dia's 37-40 | Trainingsfout berekenen en gewichten stap voor stap aanpassen | Niet schrappen omdat de termen moeilijk klinken. Ze zijn lesstof. |
| Adam | Les 2, dia 48 | Optimizer bij onze training | Behouden en eenvoudig uitleggen als een methode die de gewichtsupdates bepaalt. |
| Early stopping en L2/weight decay | Les 2, dia's 58-59 | Patience 20 en weight decay 0,0005 | Behouden. Geen eigen ingewikkelde optimizer nodig. |
| Data augmentation | Les 2, dia's 62-64 | Horizontaal spiegelen | Behouden. Meer vervormingen toevoegen geeft niet automatisch betere voorbeelden. |

Let op bij dia 28: de opsomming kan de indruk geven dat gewichten al vóór backpropagation worden bijgewerkt. Onze uitleg moet de daadwerkelijke volgorde volgen: voorspellen, loss berekenen, gradients via backpropagation bepalen en daarna de optimizer laten bijwerken.

## Wat is ingewikkelder dan nodig?

| Huidig onderdeel | Waarom lastiger uit te leggen? | Eenvoudiger keuze voor de basisdemo | Gevolg |
| --- | --- | --- | --- |
| PnLCalib met punt- én lijnnetwerk | Twee externe netwerken, aparte runtime en veel geometriecontroles | Zelf vier veldpunten aanduiden plus twee controlepunten | Vaste camera nodig. Automatische pan/zoom-verwerking valt weg. |
| Optical flow, Lucas-Kanade en RANSAC | Extra bewegingsschatting met drift, resetregels en tijdslimieten | Eén vaste homography voor dezelfde vaste camerastand | Clip kiezen zonder camerabeweging of wissels. |
| Twee detectoren combineren en boxen samenvoegen | Verschillende voorstellen, NMS, insluiting en foutieve dubbele personen | Alleen de getrainde P004-detector gebruiken | Minder onderdelen. Mogelijk ook meer gemiste personen. |
| Extra MobileNet voor zes rollen | Een tweede trainingsprobleem met eigen labels, crops, normalisatie en drempels | Alleen de twee echt getrainde detectorrollen tonen | Geen steward-/supporter-/aparte lijnrechterclaim. |
| Getrainde teamkop plus kleurclusters | Twee teammethodes, opwarmfase, kleurfeatures en afwijkende keepersshirts | Teams buiten de basisdemo houden | Teamkleuren worden een afzonderlijke extra. |
| ByteTrack, Kalmanfilter en trajecten | Matching over tijd en ID-wissels vragen extra referentiedata | Eerst detecties en minimap zonder tracking | Geen claim over blijvende speler-ID's. |
| Tiling en veel profielvarianten | Meer modelaanroepen, overlap en meer keuzes | Geen tiling in de P004-basisroute | Kleine objecten kunnen nog steeds worden gemist. |

MobileNet is ook een CNN en is dus niet automatisch te moeilijk of verkeerd. Het probleem is de extra dataset, training en foutanalyse die erbij komen. Ensemble methods staan op les 2 dia 61, maar dat betekent niet dat onze gespecialiseerde boxsamenvoeging daarmee volledig uitgelegd is. De twee lesdecks leggen PnLCalib, ByteTrack of onze complete teammethode niet uit.

**Als we één extra willen verdedigen:** teamkleurherkenning is conceptueel vaak overzichtelijker dan automatisch bewegende camera's. We moeten dan wel de daadwerkelijk gebruikte code uitleggen. De huidige methode gebruikt meer dan een simpel K-means-voorbeeld: onder meer kleur-/helderheidsverdelingen en een opwarmfase. Een nieuw simpeler kleurmodel zou een nieuw experiment met eigen evaluatie zijn. Dat is in deze branch niet verzonnen of alvast als even goed aangemerkt.

## Wat mogen we volgens de opdracht niet weglaten?

De challenge-PDF vraagt in het basisproject gerichte annotaties van 40-80 uitdagende frames, echte fine-tuning, mAP@50 en mAP@50:95, concrete foutanalyse, minstens vier bekende vlakke veldpunten, homography en een lokale interface met een gesynchroniseerde minimap.

YOLO, mAP en homography staan niet als uitgewerkte algoritmen in deze twee lesdecks, maar zijn wel nodig voor deze opdracht. Alleen een pretrained model uitvoeren en de training schrappen zou dus een verkeerde vereenvoudiging zijn. Hetzelfde geldt voor de minimap verwijderen omdat perspectief moeilijk klinkt.

Tracking, teamkleurclustering en automatische keypoints zijn uitbreidingen. De rubric noemt voor toegang tot de hoogste categorie boven 85% een succesvol verdedigde extra. Dat is geen garantie op een cijfer. De basis moet eerst goed zijn. Pretrained PnLCalib uitvoeren mogen we niet voorstellen als zelf een keypointmodel trainen.

## Zo kunnen we het eenvoudig uitleggen

1. **Data:** "We kozen moeilijke voetbalbeelden en tekenden kaders rond onze doelobjecten. Bij de bal zijn er ook kleine en wazige voorbeelden. De aanvullende AI-labels moeten we nog onafhankelijk nakijken."
2. **Trainingscyclus:** "Het netwerk voorspelt. We berekenen de fout. Backpropagation bepaalt welke gewichten bijdragen aan die fout. Adam gebruikt die informatie om de gewichten aan te passen."
3. **Transfer learning:** "Het model kende al algemene beeldkenmerken. We trainden het verder op onze voetbalbeelden, in plaats van helemaal opnieuw te beginnen."
4. **Eerlijke vergelijking:** "P003 hield de eerste tien modules vast. P004 mocht alles aanpassen. De overige gekozen instellingen bleven gelijk. P004 scoorde beter op spelers, maar minder goed op scheidsrechter-recall."
5. **Gevonden probleem:** "Bij 640 werden de balkaders na verkleinen zo klein dat de software ze verwijderde. Op 1920 bleven ze behouden. Dat verbeterde de invoer, maar gaf nog geen goede PANORIS-validatiescore."
6. **Geometrie:** "We koppelen bekende punten in het camerabeeld aan punten op een plat veld. De homography zet zo een voetpunt om naar een minimappunt. Bij een vaste camera kan dezelfde omzetting blijven gelden."
7. **Beperking:** "Een bal in de lucht ligt niet op het grondvlak. Een verkeerd kader geeft een verkeerd voetpunt. En een validatiescore uit dezelfde wedstrijd bewijst niet dat elke wedstrijd goed werkt."

We hoeven de interne tensorberekeningen van een volledige YOLO11-backbone niet uit het hoofd te herleiden. We moeten wel convoluties, gewichten leren, loss, train/val/test, confidence en IoU kunnen onderscheiden. Confidence is de modelscore. IoU meet overlap tussen kaders. Geen van beide is hetzelfde als AP of recall.

## Starten en controleren

Vanuit de projectmap, na de bestaande installatie met `scripts/Setup-Persoon1.ps1` en FFmpeg via `scripts/setup_tools.ps1`:

```powershell
# Alleen bestanden en hashes controleren, zonder training, app of GPU-inference:
powershell -ExecutionPolicy Bypass -File scripts/Start-Cursus.ps1 -CheckOnly

# Eenvoudige basisroute op GPU 0:
powershell -ExecutionPolicy Bypass -File scripts/Start-Cursus.ps1

# CPU-alternatief:
powershell -ExecutionPolicy Bypass -File scripts/Start-Cursus.ps1 -Device cpu
```

Kies een vaste overzichtscamera. Klik de vier veldpunten en twee controlepunten aan, controleer begin/midden/einde en laat tracking uit. Alleen werkelijke bronrechten en menselijke kalibratiebeoordeling invullen. Geen automatisch veldmodel installeren voor deze route. Het script kiest alleen bestaande gewichten; er is geen nieuwe training nodig.

P004 is niet automatisch een betere demo dan R007. De oorspronkelijke P004-spelerscore is 74,50% AP@50 en 26,55% AP@50:95 op twaalf ontwikkelvalidatiebeelden. De rol-/teampipeline heeft andere cijfers en deels andere meetinstellingen. De vereenvoudiging verandert dat bewijs niet. Gebruik geen score uit de uitgebreide route bij een video uit de eenvoudige route.

## Wat blijft nog echt werk?

De belangrijkste resterende punten zijn menselijke labelreview, een onafhankelijke eindtest en een gezamenlijk beoordeelde demo op de doellaptop. Die zijn inhoudelijk waardevoller dan nog extra netwerken toevoegen. Een ingewikkelde methode weglaten lost ontbrekende evaluatie niet op.

Deze branch voegt de vergelijking en het eenvoudige startscript toe. Er is geen nieuwe trainingsrun, GPU-benchmark of volledige videoproef uitgevoerd. Model-/evaluatiehashes en PowerShell-syntax zijn gecontroleerd. Final2 en de bestaande presentatie zijn niet herschreven: die beschrijven ook de daadwerkelijk uitgevoerde uitbreidingen. Dit document maakt de aanbevolen afbakening voor de verdediging concreet. De inhoudelijke beoordeling en de tekst zijn met Codex gemaakt.

## Bronnen in deze repository

- `1_DL_Setting_the_Scene.pptx` en `2_DL_Adv_Deep_Learning.pptx`, met de bovengenoemde dianummers.
- `CV_Challenge_2026_2027.pdf`, pagina's 2-4: basisopdracht, extra's en rubric.
- `configs/models-players-base.json`, `configs/train-players-reference.json` en `configs/train-players-unfrozen.json`.
- `src/football_pipeline/detection.py`, `geometry.py`, `appearance.py`, `teams.py`, `tracking.py`, `automatic_calibration.py` en `field_motion.py`.
- `docs/Resultaten_Spelermodel.md`, `docs/Resultaten_Extra_Dataronde.md` en `docs/Broadcast_Veldexperiment.md` voor echte uitkomsten en beperkingen.
