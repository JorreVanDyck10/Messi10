# Getrainde rolherkenning en teams — R007

Het rolprofiel `configs/models-players.json` gebruikt nu werkelijk getrainde aanvullende rol- en teamherkenning. Het onderscheidt spelers, scheidsrechters, lijnrechters, stewards, supporters en personen met een onduidelijke rol. Spelers krijgen Team A, Team B of team onbekend. Dit is experimenteel: vooral supporters, kleine centrale officials en afwijkende doelmankleding blijven zwak. Alle aanvullende labels zijn door AI gecontroleerd; menselijke review is niet nagebootst.

## Modellen en echte klassen

De bestaande P004-spelerdetector blijft behouden. Een tweede pretrained YOLO11n levert generieke persoonsvoorstellen, ook buiten het veld. De voorstellen worden samengevoegd. Een kleine MobileNetV3 beoordeelt vervolgens de volledige persoonsuitsnede en shirtkleuren. De laatste drie featureblokken en twee classificatiekoppen zijn daadwerkelijk getraind. Het vertrekpunt is [de officiële Torchvision MobileNetV3 Small](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.mobilenet_v3_small.html).

De classifier gebruikt geen veldpositie als rolkenmerk. Daarna geldt de veldfilter van persoon 2: uitsluitend de uiteindelijke rol `player` met een geldig voetpunt binnen het actuele veld telt mee. Correct herkende stewards tellen ook binnen het veld niet mee. Een verkeerd als speler herkende steward kan nog steeds meetellen.

| Kop | Werkelijke ID | Naam |
|---|---:|---|
| Rol | 0 | `player` |
| Rol | 1 | `referee` |
| Rol | 2 | `assistant_referee` |
| Rol | 3 | `steward` |
| Rol | 4 | `spectator` |
| Rol | 5 | `person` |
| Team | 0 | `team_a` |
| Team | 1 | `team_b` |

De oorspronkelijke YOLO-klasse-ID blijft apart beschikbaar. Een generieke persoonsklasse wordt niet door alleen een manifestwijziging een speler; daarvoor wordt de getrainde classifier uitgevoerd.

Het geselecteerde bestand `artifacts/appearance-v1/roles_teams.pt` is ongeveer 3,9 MB, met SHA-256:

`adad67b0e3b60803d11a179c11c24d5c6cf2a31cbe9804a93c5da43b2bc008f2`

`roles_seed_r004.pt` is uitsluitend een bewaard trainingsvertrekpunt. `person_proposals.pt` bevat de echte pretrained persoonsdetector. De modelprofielen bevatten alle gewichtshashes.

## Bronbeelden, labels en splits

De oorspronkelijke 60 TeamTrack-beelden en YOLO-labels blijven behouden. Alleen hun 36 train- en 12 validatiebeelden worden voor deze classifier gebruikt. De twaalf bestaande testbeelden worden niet geopend.

Elf gelicentieerde Commons-foto’s leveren extra steward- en supporteruitsneden: zeven trainingsfoto’s, vier validatiefoto’s. Zie [de auteurs, licenties en bronlinks](../datasets/roles-teams-v1/ATTRIBUTION.md). Alle uitsneden uit één foto blijven in dezelfde subset. Dit zijn geselecteerde classificatiecrops; overige personen in de foto zijn niet volledig geannoteerd.

Een eerste videoproef toonde ernstige verwarring op de oorspronkelijke YouTube-video. Daarom zijn negen beelden toegevoegd binnen de bestaande ontwikkel-/validatiewindows:

| Subset/groep | Frame-indexen | Tijdstippen |
|---|---|---|
| Train `original-dev-00` | 0, 75, 150 | 0, 3, 6 s |
| Train `original-dev-14` | 350, 425, 500 | 14, 17, 20 s |
| Validatie `original-val-84` | 2100, 2175, 2250 | 84, 87, 90 s |

Geselecteerde personen zijn visueel beoordeeld. Posters, borden en onbeslisbare verre officials zijn uitgesloten. Onzekere personen aan de zijlijn behouden `person`. Enkele overlappende voorstellen betreffen dezelfde persoon; aantallen betekenen uitsneden, geen unieke mensen. Alle uitsneden uit hetzelfde beeld blijven samen.

De actuele speler-/rolselectie bevat **80 unieke bronbeelden**: 60 TeamTrack-beelden, 11 foto’s en 9 YouTube-frames. De nieuwe classifier gebruikt daarvan 68 train-/validatiebeelden. De twaalf testbeelden blijven buiten uitvoering. De classificatiemanifestversie is `roles-teams-v1.1`, in de map `datasets/roles-teams-v1`. De historische balexperimenten staan afzonderlijk: inclusief hun 47 beelden en vijf overlappende oorspronkelijke momenten zijn cumulatief 122 unieke bronbeelden onderzocht. Het totale historische project wordt dus niet als een dataset van slechts 80 beelden voorgesteld.

| Rol | Training | Validatie |
|---|---:|---:|
| Speler | 928 | 314 |
| Scheidsrechter | 43 | 15 |
| Lijnrechter | 42 | 15 |
| Steward | 7 | 8 |
| Supporter | 13 | 11 |
| Persoon, rol onduidelijk | 12 | 9 |

Foto’s en extra bronframes krijgen alleen tijdens training spiegel-/resolutievarianten. Validatie wordt niet geaugmenteerd. Beeldhashes, boxen, groepen en labels staan in het manifest; de automatische voorstellen en visuele controlebladen zijn bewaard.

Team A is wit met rode doelman in TeamTrack, en claret/lichtblauw met oranje doelman in de oorspronkelijke video. Team B is blauw met gele doelman in TeamTrack, en donker/goud met groene doelman in de oorspronkelijke video. Dit zijn visuele AI-toewijzingen, geen geverifieerde clubnamen. Bronresoluties blijven 6500×1000 en 3840×960. De veldalgoritmen en kalibratieafspraken zijn niet veranderd.

## Werkelijke experimenten

Preregistraties, curves, afgewezen resultaten en metingen staan onder `reports/appearance-experiments`.

- R001 miste alle acht validatiestewards. Niet overgenomen.
- R002 voegde kleurbehoud, een extra trainingsfoto en fotoaugmentatie toe.
- R003 gaf shirtkleur meer gewicht en selecteerde op de werkelijke confidencegrens.
- R004 leerde extra CNN-features, maar verwarde veel personen op de oorspronkelijke video. De positieve eerste cropresultaten bewijzen dus geen videotransfer.
- R005 voegde de tweede wedstrijd en de generieke persoonsklasse toe; stewardherkenning verslechterde.
- R006 behield de R004-backbone en had een iets hogere aggregate macro-F1 dan R007, maar veel minder correcte speleruitsneden boven de werkgrens: 257 tegenover 307, en drie tegenover zes stewards.
- **R007 is geselecteerd** als afweging voor spelers, stewards en teams. De normalisatie van de warm-startkop bleef behouden, en het beste fine-tuningcheckpoint is samen met zijn kop bewaard. Supporterherkenning blijft slechter dan bij R006.
- R008 gebruikte dezelfde gewichten met overlappende detectie-uitsneden. Meer spelers gevonden, maar ook veel meer foutpositieven en extra rekentijd. Dit is een afzonderlijk experimenteel profiel, niet de standaard.

R007 gebruikt seed 42, Adam, twintig fine-tuningepochs met tien gebalanceerde updates per epoch, backbone-learning-rate 0,00005 en head-learning-rate 0,0005. Alleen de laatste drie featureblokken worden aangepast; batchnorm-statistieken blijven vast. Koppen krijgen daarnaast maximaal 400 supervised updates met Adam 0,005. Selectie gebruikt ontwikkel-macro-F1 op confidence 0,65. Rol en getraind team hebben diezelfde werkgrens. Onzekere rollen worden `person`; onzekere teams blijven onbekend.

De runs zijn echt uitgevoerd op de aanwezige **RTX 3050 Laptop GPU**. De RTX 4050 blijft de doellaptop; daarop is geen benchmark uitgevoerd.

## Classifier op correcte persoonsuitsneden

Dit meet uitsluitend classificatie wanneer de juiste box al bekend is. Het zijn geen volledige video-detectierecalls of mAP-scores.

| Rol | Correct bij confidence ≥ 0,65 | Recall op deze crops |
|---|---:|---:|
| Speler | 307/314 | 97,77% |
| Scheidsrechter | 12/15 | 80,00% |
| Lijnrechter | 14/15 | 93,33% |
| Steward | 6/8 | 75,00% |
| Supporter | 4/11 | 36,36% |
| Persoon, rol onduidelijk | 5/9 | 55,56% |

De teamkop benoemt **307/314** speleruitsneden correct, maakt vier verkeerde teamkeuzes en laat drie onbekend. Dit geldt voor de bekende wedstrijden en gegeven spelersboxen. De kleine aantallen en herhaald gebruik van ontwikkelvalidatie beperken de conclusies.

## Volledige detector: twaalf TeamTrack-validatiebeelden

Beide varianten gebruiken globale resolutie 1920, proposal-confidencevloer 0,10 en NMS-IoU 0,70. De nieuwe variant gebruikt daarnaast de rolgrens 0,65. TP/FP/FN gelden bij proposal-confidence 0,25 en matching-IoU 0,50. Officialsubtypen zijn voor de vergelijking samengevoegd. Door de confidencevloer verschillen deze AP-scores van de vroegere P004-meting vanaf 0,001.

| Variant | Klasse | AP@50 | AP@50:95 | TP | FP | FN |
|---|---|---:|---:|---:|---:|---:|
| P004 | Speler | 72,94% | 25,85% | 199 | 65 | 65 |
| R007 | Speler | 75,42% | 26,07% | 197 | 53 | 67 |
| P004 | Officials samen | 49,81% | 36,28% | 10 | 0 | 14 |
| R007 | Officials samen | 64,21% | 37,49% | 12 | 3 | 12 |
| R008 extra uitsneden | Speler | 74,29% | 26,79% | 227 | 108 | 37 |
| R008 extra uitsneden | Officials samen | 63,72% | 40,02% | 14 | 5 | 10 |

Van de 197 correct gevonden R007-spelers krijgen **192 het juiste team**, twee een verkeerd team en drie geen team. Ontbrekende spelers tellen niet als correcte teamkeuze.

De aparte volledige detectie-evaluatie blijft zwak voor de centrale scheidsrechter: **3 TP / 12 labels**, tegenover **9 TP / 12 labels** voor de nabije lijnrechter. Crop-classificatie lost gemiste of slechte detectorboxen niet op. Verre officialdekking blijft gedeeltelijk.

Op de geselecteerde externe validatiecrops levert de volledige detector drie van acht stewards en vijf van elf supporters met de juiste rol. Dit is alleen een overlapproef met geselecteerde classificatiecrops, geen mAP-benchmark. Overige personen zijn niet volledig gelabeld; kwalitatieve beelden tonen ook verkeerde stewardlabels. **Volledig betrouwbare supporter- en officialherkenning is niet aangetoond.**

## Videoproef en nieuwe video-identiteit

In het laatste van dertig gecontroleerde ontwikkelframes van de oorspronkelijke video levert R007 twintig spelerkandidaten, één lijnrechter, één scheidsrechter en één generieke persoon. De kandidaat-teamverdeling is 12/8. Dit is detectoruitvoer, geen bewezen correcte wedstrijdselectie. Zonder kalibratie blijft het aantal spelers op het veld onbekend.

Deze beperkte detectorproef verwerkte dertig frames in ongeveer 3,5 seconden op de RTX 3050. Dat omvat niet de volledige veldherkenning en video-encoding en is geen FPS-claim voor de 4050.

Een opnieuw gecodeerd ontwikkelfragment heeft een nieuwe video-identiteit en activeert videolokale kleurclustering. De proef toont het resetten en opbouwen van kleuren, maar veel indelingen blijven onbekend. Het betreft dezelfde wedstrijd en bewijst geen generalisatie. Nieuwe A/B-labels zijn geen clubnamen en hoeven tussen video’s niet dezelfde club te betekenen. De kleurafstandsmarge is geen gekalibreerde waarschijnlijkheid. Afwijkende doelmankleding kan bij deze automatische route onbekend of fout blijven.

## Starten en overdracht

Na `git pull` en `git lfs pull`:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/Start-Spelermodel.ps1 -Recognition players
```

Het R007-rolprofiel is `configs/models-players.json`. Het algemene standaardprofiel `configs/models.json` en `configs/models-persons.json` blijven de door persoon 2 op de 4050 gecontroleerde persoonsroute gebruiken. Het oude tweeklassenprofiel blijft `configs/models-players-base.json`; de uitsnedenproef is `configs/models-roles-tiles.json`. CPU-fallback voor rollen: `Start-Spelermodel.ps1 -Recognition players -Device cpu`.

Tijdens afronding zijn de nieuwe velddata-/trainingscode en RTX 4050-controles van persoon 2 samengevoegd. Zijn Broadcast-records betreffen de algemene persoonsdetector en oorspronkelijke P004-detector. De aanvullende R007-classifier is nog niet op die Broadcast-clip of de 4050 gemeten; de eerdere tekortkomingen zijn behouden als waarschuwing en niet als nieuwe R007-evaluatie voorgesteld.

De geselecteerde trainingsroute herhalen met een nieuwe runmap:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/Train-RollenTeams.ps1 -RunName eigen-rollen-run
```

De training gebruikt de geleverde R004-seed en bronbeelden uit Git LFS en overschrijft het geselecteerde model niet. Voor identieke bronbytes gebruik je Git LFS. Het Commons-downloadhulpmiddel controleert hashes en keurt gewijzigde bronbytes niet als dezelfde dataset goed.

`reports/appearance-experiments/handoff.json` bevat hashes, echte uitvoerklassen, instellingen, softwareversies en bewijsverwijzingen. Detecties behouden boxen in bronpixels en krijgen oorspronkelijke detectorrol, classifier-ID/-klasse/-confidence, team-ID/-klasse/-confidence en de teammethode. Bij lage rolconfidence kan de hoogste `role_class_id` afwijken van de uiteindelijke terugvalrol `person`. Kleurclustering heeft geen getrainde teamklasse-ID.

`player_summary.teams` verdeelt uitsluitend de werkelijk meegetelde veldspelers over A, B en onbekend; samen vormen zij het veldtotaal. Bij ongeldige veldherkenning blijft ook die verdeling onbekend. Replay bewaart de modeluitvoer voor rol/team en herberekent geometrie, telling en tracking. De bestaande MVP-acceptatie en blokkade op automatische cameratracking blijven gelden.

De softwaretests en echte modelmetingen zijn afzonderlijk bewaard. Menselijke labelreview, onafhankelijke projecteindtest en beoordeling op de 4050 blijven open.

De samengevoegde versie slaagt met **199 tests en 4 subtests**, inclusief de nieuwste veldtraining en GPU-/persoonscontroles van persoon 2. Ruff, formatting en dependencycontrole slagen. Zie `reports/appearance-experiments/software-validation.json`.

De nieuwe model- en bronbestanden zijn na publicatie werkelijk opnieuw uit GitHub gedownload in een lege LFS-cache: 23 bestanden, 43.021.348 bytes. Iedere hash en bestandsgrootte is tegen de gepubliceerde pointer gecontroleerd; de verse classifier is geladen met de zes juiste rolnamen. Het bewijs staat in `reports/appearance-experiments/remote-download-verification.json`. Dit is geen controle tegen alleen de bestaande lokale cache.
