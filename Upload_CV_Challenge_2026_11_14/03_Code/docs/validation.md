# Werkelijk uitgevoerde technische controles

Datum: 16 oktober 2026. Platform: Windows, Python 3.11, CPU-inference. De gecontroleerde code staat op branch `codex/pipeline-minimap`. Tijdens de hieronder beschreven lokale validatie had de repository nog geen commit; daarom bevatten die runmanifesten `git_commit: null` en daarnaast een SHA-256 van de werkelijke bronbestanden. Dit document rapporteert die lokale controles, geen menselijke review of eindacceptatie.

## Testresultaat

`python -m pytest -q`: **33 passed in 9.68s** tijdens de laatste volledige uitvoering.

Daarnaast geslaagd:

- Ruff-controle en formaatcontrole van alle 22 Python-bestanden;
- Python compileall;
- dependencycontrole: alle geïnstalleerde packages zijn compatibel;
- installatie-dry-run met `requirements.lock`: geen wijzigingen nodig;
- beschikbaarheid en daadwerkelijke werking van FFmpeg/ffprobe en H.264-encoding.

De tests onderzoeken onder andere een bekende perspectieftransformatie, ongeldige puntconfiguraties, onafhankelijke controlepunten, verkeerde kalibratieschaal, ongeldige boxes en homogene delers, semantische modelrollen, gewichtshashes, variabele framerate, encoderfalen, beschadigde cachebestanden, proceslocking, echte ByteTrack-indexkoppeling, lage confidence, lege frames, trajectgaten en projectspecifieke trackingtellingen.

Streamlit AppTest controleert de beginsituatie, de volledige kalibratieberekening en reviewflow, intrekken van goedkeuring na gewijzigde punten, een volledige videoverwerking na expliciete klik, geen herverwerking door een gewone rerun en het verbergen van oude resultaten bij een trackingwijziging. Bestandsuploads en de tabelinvoer zijn in die tests gecontroleerd geïnjecteerd; er is geen browserhandmatige voetbalacceptatie uitgevoerd.

## Werkelijke lokale uitvoeringen

Iedere hieronder vermelde uitvoering verwerkt **20 frames van 640 × 360 op 10 fps** en controleert de uitvoer als **20 H.264-frames van 1920 × 720 op 10 fps**. Het gaat om een gegenereerde scène met rechthoeken, niet om voetbalbeelden.

| Uitvoering | Werkelijk gemeten verwerkingstijd | Betekenis |
|---|---:|---|
| Synthetische detector, volledige pipeline | 2,569 s | Geometrie, lege frame 8, rendering, JSONL, encoding en uitvoercontrole |
| Echte YOLO11n op dezelfde synthetische scène | 3,903 s | Echte gewichtslading en inference door de geïntegreerde videoketen |
| Replay van die echte opgeslagen detecties | 0,498 s | Gevalideerd hergebruik zonder nieuwe modelinference |

Deze runs volgden elkaar in hetzelfde Python-proces op; laden/caches en achtergrondbelasting beïnvloeden de tijden. Dit zijn engineeringmetingen, geen betrouwbare vergelijking van voetbalprestaties of realtimegarantie. De voorafgaande invoercontrole valt buiten de weergegeven verwerkingstijd. De lokale samenvatting staat in `artifacts/current-validation.json`; alle afzonderlijke mappen bevatten hun volledige runmanifest, hashes en metingen.

De synthetische controlebeelden zijn visueel bekeken: links en rechts tonen hetzelfde framenummer en tijdstip, en het geprojecteerde punt komt overeen met het onderste midden van de bekende box. Het lege detectieframe wordt behouden. Geautomatiseerde tests bevestigen ook het ontbreken van een verzonnen waarneming bij een trackinggat.

## Afzonderlijke echte modelproef

YOLO11n-gewichten zijn gedownload via de officiële Ultralytics-assetfunctie. SHA-256:

```text
0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1
```

Op de officiële [Ultralytics-testafbeelding bus.jpg](https://github.com/ultralytics/assets/blob/main/im/bus.jpg), 810 × 1080 pixels, produceerde de adapter vier `person`-detecties. Alle boxes lagen in de oorspronkelijke beeldcoördinaten; geen detectie werd tot `player` hernoemd. Het lokale rapport staat in `artifacts/model-smoke.json`. Dit is geen mAP-meting en zegt niets over voetbalgeneralisatie.

## Omgeving

| Onderdeel | Geteste versie |
|---|---|
| Streamlit | 1.64.0 |
| Ultralytics | 8.4.178 |
| PyTorch | 2.14.1+cpu |
| Torchvision | 0.29.1+cpu |
| OpenCV Python | 4.14.0.94 |
| NumPy | 2.4.6 |
| LAP | 0.5.13 |
| FFmpeg/ffprobe | N-127564-g3c92f003c7-20261015, BtbN Windows-build |

Alle Python-versies, inclusief indirecte dependencies en testtools, staan vast in `requirements.lock`. De effectieve ByteTrack-buffer in deze versie is rechtstreeks 30 frame-updates; de compatibiliteitstest controleert ook 1,2 seconde bij 25 fps.

## Nog niet aangetoond

- Geschiktheid en toegestaan gebruik van een echte voetbalclip.
- Geprojecteerde spelersposities en camerastabiliteit op die clip.
- De definitieve, afzonderlijke speler- en scheidsrechterklassen.
- Handmatige trackingreferenties en kwalitatieve meerwaarde op voetbalbeelden.
- Echte mAP, ID-prestaties of metrische positienauwkeurigheid.
- Menselijke MVP-acceptatie, tweede-laptopacceptatie en mondelinge verdediging.
- Een geslaagde GitHub Actions-run; de status daarvan moet afzonderlijk op GitHub worden gecontroleerd.

Volg voor die onderdelen de nog openstaande checklist in `acceptance.md`. De productiepoort voor tracking is niet automatisch geaccepteerd; alleen de technische test stubt die grens expliciet.

## Integratie met het werkpakket van persoon 1

Op 16 oktober 2026 is de bijgewerkte `main` met het werkpakket van persoon 1 in `codex/pipeline-minimap` geïntegreerd. De conflicten in README, ignore-regels en requirements zijn gecombineerd met behoud van beide werkpakketten. `requirements.txt` en `requirements-lock.txt` blijven de trainingsomgeving van persoon 1 beschrijven; `requirements.lock` blijft de afzonderlijke CPU-pipelineomgeving. De gezamenlijke README legt uit dat deze verschillende omgevingen in eigen checkouts worden gebruikt.

De volledige gecombineerde testsuite slaagde: **65 passed, 4 subtests passed**. Er waren 33 bestaande Pillow-deprecatiewaarschuwingen in de tests van persoon 1; geen testfouten. De pipelineomgeving kreeg PyAV 16.0.1 als testdependency voor de overgenomen videotests. De productie-instellingen van persoon 1 zijn niet veranderd. Ruff en de formaatcontrole slagen binnen het bestaande pipelinebereik; de formattering van de overgenomen persoon-1-code blijft behouden.

## Eerste echte PANORIS-pilot

Daarna is het fragment met bronframes 0–149 technisch gekalibreerd en met echte YOLO-inference verwerkt. De vijf onafhankelijke controlepunten geven op frame 0 een mediaan van 4,84 pixels en een maximum van 12,97 pixels. De volledige video bevat 150 gesynchroniseerde frames. De CPU-run duurde 26,13 seconden. Menselijke review blijft open en de uitvoer is uitdrukkelijk geen MVP-acceptatie. Zie `PANORIS_Pilot.md` voor de scope, voorbeelden en beperkingen.

Na toevoeging van de pilotroute slagen **70 tests en 4 subtests**, met dezelfde 33 bestaande Pillow-deprecatiewaarschuwingen; lint en formaatcontrole slagen voor 24 Python-bestanden. Grote video-uitvoer blijft lokaal; de gemeten samenvattingen en observaties staan onder `reports/panoris-pilot-*`.

## Klikbare kalibratiepunten

Na de gemelde lege-coördinatenfout is de handmatige invoer uitgebreid met aanklikbare punten op het referentiebeeld. De labels zijn linksboven, rechtsboven, rechtsonder, linksonder, middenlijn boven en middenlijn onder. Een schema onderscheidt de twee middenlijn-/zijlijnsnijpunten van de middenstip. De tabel blijft beschikbaar voor correcties; ontbrekende punten houden de berekenknop uitgeschakeld.

De aanvullende controles onderzoeken originele pixelcoördinaten, afwijzen van niet-eindige/buitenbeeldcoördinaten en vertraagde browserklikken, automatisch volgend punt, behoud na rerun en intrekken van een eerder berekende kalibratie na een correctie. AppTest doorloopt alle zes punten. De lokale browser toont het echte 3840 × 960-fragment, markeringen en duidelijke labels; de zoomregeling is bediend. Het browservoorbeeld staat in `reports/calibration-picker-preview.png`. Dit controleert de interface en vervangt geen menselijke review van de gekozen geometrie.

De volledige suite slaagt nu: **87 tests en 4 subtests**, met dezelfde 33 bestaande Pillow-deprecatiewaarschuwingen. Lint en formaatcontrole slagen voor de pipelinecode.

Bij het testen meldde de gebruiker vervolgens onafhankelijke fouten van 13,54 en circa 60 pixels. De actuele browserpuntentabel op referentieframe 9 leverde bij afzonderlijke herberekening 13,54 en 60,93 pixels op. Deze geselecteerde punten en de diagnose zijn bewaard in `reports/calibration-click-diagnosis.json`; de grenzen van 19,79 pixels mediaan en 39,58 pixels maximum blijven gelijk. De foutweergave benoemt nu ieder controlepunt, toont grenswaarden en tekent de berekende positie met een kruis en verbindingslijn. Die berekende plek is geen onafhankelijke waarheid en wordt niet automatisch overgenomen.

Daarna zijn via **Pilotpunten invullen** de bestaande suggesties geladen en op referentieframe 0 berekend. De browser bevestigde **Puntcontrole geslaagd**, met fouten 6,81 / 12,97 / 3,75 / 3,44 / 4,84 pixels. Het bewijsbeeld staat in `reports/calibration-control-success.png`. Het menselijke reviewformulier blijft leeg en ongeaccordeerd. Twee extra tests controleren de diagnostiek, behoud van de fout bij een rerun en herstel na puntcorrectie. De volledige suite slaagt nu met **89 tests en 4 subtests**; de 33 bestaande Pillow-waarschuwingen zijn onveranderd.

## Modeloverdracht voor spelertracking

Het nieuwe commando `register-player-model` controleert de gewichtenmetadata, expliciete klassemapping, confidence, hashes en het reguliere modelcontract. Tests gebruiken herkenbaar gesimuleerde spelersmetadata; een echte registratiepoging met `weights/yolo11n.pt` is afgewezen met de bestaande person→player-controle en heeft geen spelersprofiel achtergelaten. Er is geen getraind voetbalmodel bijgemaakt of als beschikbaar voorgesteld.

AppTest controleert dat wisselen van modelprofiel tracking uitzet en een oud resultaat niet opnieuw toont of verwerking start. De bestaande tracking- en MVP-poorten blijven gelden. Na deze toevoeging slagen **96 tests en 4 subtests**, met dezelfde 33 bestaande Pillow-waarschuwingen; lint, formattering en diffcontrole slagen. De echte spelertrackingrun wacht op getrainde spelersgewichten en menselijke MVP-review volgens `Spelermodel_Overdracht.md`.

## Gecontroleerde veldherkenning en camerabeweging

De uiteindelijke softwareversie slaagt met **141 tests en 4 subtests**, 33 bestaande
Pillow-waarschuwingen en geen fouten. Ruff, formaatcontrole (43 Python-bestanden)
en diffcontrole slagen. De tests omvatten aparte punt-/lijncontroles, uitsluiten
van fitpunten als kwaliteitsbewijs, volledige ruwe scorebundels, confidencekeuze,
Lucas–Kanade-pan/zoom, bidirectionele fout, RANSAC-inliereisen, verlopen
overbrugging, drift, camerawissels, onscherpte, herstel, oude en nieuwe replay,
de handmatige workflow en expliciete menselijke invoer via AppTest.

De echte Broadcast-video is volledig opnieuw door dezelfde veldgewichten
verwerkt. Met hetzelfde opgeslagen netwerkresultaat geven de vier stappen
0, 228, 277 en 252 intern geldige frames. De strengere confidence blijft wegens
gelijke ontwikkeluitkomst behouden. De uiteindelijke 252 frames omvatten
228 directe en 24 gevolgde schattingen; dit is 20,3% van alle 1.239 frames.
Nauwkeurigheid op menselijke referenties en dekking op kalibreerbare frames
zijn niet ingevuld. De kandidaat is experimenteel.

De demo en baselinevergelijking bevatten elk exact 1.239 H.264-frames op 25 fps
en 1920 × 720. Alle oorspronkelijke detecties zijn zonder nieuwe detectorinference
overgenomen; alleen de veldposities zijn opnieuw berekend. Ongeldige kalibraties
hebben geen veldposities. Gevolgde frames voldoen aan de inlier- en leeftijdsgrenzen.
Zoeken naar bronframes 0, 114, 723 en 1238 levert pixelidentiek beeld aan
opeenvolgend decoderen. Er zijn geen echte menselijke referentiebestanden of
inhoudelijke goedkeuringen door de agent aangemaakt.

Zie `reports/broadcast-field-software-check.json`,
`reports/broadcast-field-experiment.json` en [het cursusgerichte verslag](Broadcast_Veldexperiment.md).
