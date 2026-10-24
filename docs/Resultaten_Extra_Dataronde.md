# Extra dataronde: vier werkelijk uitgevoerde experimenten

De gebruiker vroeg om de extra data daadwerkelijk te benutten. Twee nieuwe YOLO-ballentrainingen en twee rol-/teamtrainingen zijn uitgevoerd. De winst is gemengd: de rolmodellen verbeteren spelers en officials, maar er is geen universeel beter model. De bestaande standaardprofielen en veldgewichten blijven behouden; nieuwe rolprofielen zijn apart beschikbaar.

## Nieuwe labels en kwaliteitscontrole

De 48 bestaande bal-/persoonsbeelden zijn technisch en visueel opnieuw bekeken. De 36 balboxen zijn ongeveer 5–15 pixels breed; native cropresolutie blijft daarom 1280 × 640. De reviewbladen bewaren alle positieve patches en de twaalf negatieve contextbeelden. Er zijn in deze ronde geen balboxen aangepast en geen menselijke reviewers ingevuld.

Uit de twaalf extra trainingsframes zijn 52 bruikbare rolcrops gelabeld: 35 spelers, negen scheidsrechters en acht lijnrechters. De bestaande `football48`-validatiegroepen leveren 59 aanvullende controlecrops: 55 spelers en vier scheidsrechters. Twintig onbeslisbare/fragementarische validatiecrops zijn met identiteit uitgesloten. De nieuwe labels komen uit de extra Tsukuba-opname; claims over algemene wedstrijdoverdracht blijven beperkt.

Het nieuwe rolmanifest gebruikt 92 beeldbestanden en 1.528 ongeaugmenteerde crops. Het is een afzonderlijke uitbreiding naast de kernset van 48 balbeelden. De historische datasets blijven bestaan. Menselijke teamreview en een onafhankelijke eindtest zijn niet vervangen door AI-review.

## Bal: fine-tuning verslaat de baseline niet

Beide runs gebruiken exact 36 train-/12 validatiebeelden, met 26/10 balobjecten, twaalf bewust negatieve frames en dezelfde gescheiden tijdgroepen. Pretrained `sports ball` (werkelijke COCO-ID 32) wordt correct vergeleken met lokale klasse `ball` (ID 0). Alle onderstaande AP-scores gebruiken dezelfde projectimplementatie met 101 recallpunten en dezelfde predict-instellingen: resolutie 1280, confidencevloer 0,001 en NMS-IoU 0,70. TP/FP/FN gelden bij confidence 0,25 en matching-IoU 0,50.

| Model | AP@50 | AP@50:95 | TP | FP | FN |
|---|---:|---:|---:|---:|---:|
| Pretrained YOLO11n | 67,82% | 34,23% | 3 | 0 | 7 |
| F001, eerste 10 modules vast | 60,40% | 28,57% | 3 | 0 | 7 |
| F002, alle modules trainbaar | 43,07% | 24,36% | 4 | 0 | 6 |

Beide runs gebruiken Adam, learning rate 0,001, batch 4, seed 42, AMP, maximaal 100 epochs en patience 20. Geometrische/kleur-/mengaugmentaties staan uit, horizontaal spiegelen op 0,5. Rechthoekige batches bewaren de native cropverhouding; de frameworkdataloader schakelt daardoor shuffle uit. Beide runs stopten na **57 epochs**, met checkpoint van epoch **37**. De effectieve `nbs=64` en volledige werkelijke configuratie zijn bewaard. Werkelijke hardware: RTX 3050 Laptop GPU, 4 GiB; geen nieuwe 4050-benchmark.

De checkpoints zijn door de vastgezette Ultralytics-fitness geselecteerd, die hier AP@50:95 weegt. De frameworkvalidatie en de afzonderlijke predict-/AP101-meting kunnen verschillen door preprocessing en AP-berekening. Vergelijk daarom de baseline en kandidaten uitsluitend binnen de bovenstaande gelijk uitgevoerde projectmeting.

F002 heeft op de gekozen confidence één extra TP, maar een duidelijk slechtere AP-curve. Volgens de vooraf vastgelegde primaire AP@50:95-regel geldt dat niet als verbetering. Geen van beide ballenmodellen wordt als nieuw productiemodel gekozen. Beide echte checkpoints blijven downloadbaar als negatieve experimenten.

**Foutanalyse:** bij confidence 0,25 blijven 6–7 van de tien ballen gemist. De kleine eigen set en de nieuwe detectiekop vormen mogelijke verklaringen; de runs hebben geen afzonderlijk causaal bewijs daarvoor geleverd. Alle drie modellen gebruiken dezelfde gecontroleerde labels en gemaskeerde native crops. Hun prestaties zijn geen meting op een onbewerkte volledige panoramavideo. De vroegere 0%-metingen op een andere dataset en invoerschaal worden niet rechtstreeks met deze scores vergeleken.

## Rollen: duidelijke winst op de toegevoegde bron, met afwegingen

R009 start vanaf R007 en traint drie laatste featureblokken plus de rolkop. R010 houdt de backbone volledig vast. Beide gebruiken dezelfde nieuwe rolgegevens, twintig fine-tuningepochs met tien gebalanceerde updates, dezelfde warm-startnormalisatie en afzonderlijke koprefits. R010's onveranderde backbone is tensor voor tensor gecontroleerd.

| Conditionele classificatie bij rolconfidence ≥0,65 | R007 | R009 | R010 |
|---|---:|---:|---:|
| Correcte rollen op 59 nieuwe validatiecrops | 28/59 | **58/59** | 57/59 |
| Spelers op die 59 crops | 28/55 | 54/55 | 54/55 |
| Scheidsrechters op die 59 crops | 0/4 | 4/4 | 3/4 |
| Macro-F1 op 372 behouden validatiecrops | 0,7935 | **0,8151** | 0,8109 |
| Spelers op behouden validatiecrops | 307/314 | 313/314 | 311/314 |
| Scheidsrechters op behouden validatiecrops | 12/15 | 13/15 | 12/15 |
| Lijnrechters op behouden validatiecrops | 14/15 | 14/15 | 13/15 |
| Stewards op behouden validatiecrops | 6/8 | 5/8 | 6/8 |
| Supporters op behouden validatiecrops | 4/11 | 4/11 | 4/11 |

Dit is classificatie **gegeven een correcte persoonsbox**, geen videodetectierecall of mAP. De nieuwe validatiecrops bevatten alleen spelers en scheidsrechters; daaruit volgt geen bewijs van verbeterde stewardherkenning. Ook zijn dit ontwikkelgegevens met AI-labels en herhaald gebruikte validatie.

## De volledige detector opnieuw gemeten

Dezelfde twaalf TeamTrack-validatiebeelden, 264 spelerlabels, 24 officiallabels en inferentie-instellingen zijn voor de rolpipeline gebruikt. De proposal-confidencevloer is 0,10; dit verschilt van de balmeting hierboven. Lokalisatie en de aanvullende rolstap worden hier samen gemeten.

| Pipeline | Speler AP@50 | Speler AP@50:95 | Officials AP@50 | Officials AP@50:95 |
|---|---:|---:|---:|---:|
| R007 | 75,42% | 26,07% | 64,21% | 37,49% |
| R009 | **76,52%** | **26,65%** | **68,68%** | **38,27%** |
| R010 | 75,69% | 26,18% | 66,04% | 38,22% |

R009 houdt op de werkgrens 197 TP en 67 FN voor spelers, met 51 FP tegenover 53 bij R007. De aanvullende classifier herstelt geen ontbrekende detectorvoorstellen: centrale scheidsrechters blijven op slechts 3 TP van 12 labels. Van de 197 correct gevonden spelers krijgen er bij R009 192 het juiste bekende team; dat aantal was bij R007 hetzelfde.

De gedeeltelijke externe rollenproef verslechtert: correct gevonden/geclassificeerde geselecteerde stewards gaan van 3/8 naar 2/8 en supporters van 5/11 naar 2/11 voor beide nieuwe profielen. Dit is een overlapproef op geselecteerde crops, geen volledige detectiemAP. De uitkomst is wel reden om niet overal stilzwijgend R007 te vervangen.

**Beslissing:** R009 is het voorkeursalternatief van deze dataronde voor spelers/officials. R007 blijft standaard wegens de afweging bij andere rollen. R010 en de twee afgewezen balmodellen blijven als echte experimenten beschikbaar. Er is geen universele verbetering of productiegoedkeuring geclaimd.

## Teams, geometrie en echte videoproeven

Teams blijven **Team A/Team B/onbekend**. De toegevoegde bron heeft geen gecontroleerde teamlabels en wordt niet als bekende wedstrijd van de getrainde teamkop geregistreerd. De bestaande kleurclustering blijft daar experimenteel. In de 30-frameproef op het ruwe validatiefragment geeft R009 in het laatste frame twintig spelerkandidaten, maar ook dubbele/verkeerde officials en een onbetrouwbare A/B-verdeling. Dat is diagnostiek, geen nauwkeurigheidsscore.

R009 is daarnaast door de complete automatische pipeline met de bestaande Commons-ontwikkelclip gevoerd. Detectie, classifier, projectiecontract, tellingen en gesynchroniseerde H.264 worden gecontroleerd. De veldmodellen blijven dezelfde; de oorspronkelijke uitval op die clip wordt niet door roltraining opgelost. Bij onvoldoende veldpunten blijven posities en tellingen onbekend. Veldherkenning en cameracompensatie van persoon 2 zijn niet aangepast, en tracking behoudt zijn bestaande acceptatiegrenzen.

## Gebruiken en reproduceren

Na `git pull --ff-only origin main` en `git lfs pull`:

```powershell
# Bestaande standaard behouden; kies expliciet het nieuwe alternatief:
powershell -ExecutionPolicy Bypass -File scripts\Start-Wedstrijd.ps1 -Recognition roles-r009

# Zonder automatische veldmodus:
powershell -ExecutionPolicy Bypass -File scripts\Start-Spelermodel.ps1 -Recognition roles-r009

# Ballentraining herhalen; kies een nieuwe runmap:
.\.venv\Scripts\python.exe -m scripts.football48_ball_experiment --run runs\eigen-F001 --config configs\train-football48-ball-reference.json --provisional-ai-labels
```

De roltraining en vergelijking staan in `datasets/roles-teams-v2/README.md`. Configuraties, bron-/labelhashes, preprocessing, curves, voorspellingen en fouten zijn bewaard onder `reports/football48-ball-experiments` en `reports/appearance-experiments/EXP-R009`/`EXP-R010`. De gewichten staan via Git LFS onder `artifacts/football48-ball-v1` en `artifacts/appearance-v2`.

Alle nieuwe annotaties zijn voorlopig AI-werk. Definitieve menselijke review, nieuwe onafhankelijke wedstrijden en een onaangeroerde eindtest blijven nodig voor sterkere conclusies.
