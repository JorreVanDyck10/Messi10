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
