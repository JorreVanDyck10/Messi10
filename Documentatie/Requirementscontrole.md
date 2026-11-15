# Requirementscontrole - 15 november 2026

Bronversie: GitHub main `524d081a` en Jorres uploadpakket `8e29c3ff`. Versie 4 verwerkt de persoonlijke verklaring van Milan Wouters. De aangeleverde opdracht-PDF en het aanvullende indieningsbericht zijn gecontroleerd. **Conclusie: veel onderdelen zijn aanwezig; de volledige geaccepteerde oplevering is nog niet voor alle onderdelen aangetoond.** De menselijke review van de 80 beelden is inmiddels geregistreerd en staat niet langer als open taak vermeld.

## Kernvereisten

| ID | Vereiste | Status en bewijs | Nog nodig |
|---|---|---|---|
| C01 | Toegelaten sport | Aanwezig: voetbal | Geen |
| C02 | Statische camerahoek voor MVP | Geschikte handmatige route en historische pilots aanwezig | Actuele eindclip met begin-/midden-/eindcontrole |
| C03 | Pretrained detector als basis | Aanwezig: YOLO11s en Andrews YOLOv8x | Eindprofiel in demonstratie benoemen |
| C04 | Gerichte datakloof | Aanwezig: kleine, bewogen en deels bedekte bal | Zelfstandig uitleggen met voorbeelden |
| C05 | 40-80 moeilijke beelden annoteren | Aanwezig: 80 beelden; goedgekeurd volgens geregistreerde teamverklaring | De eigen bijdrage aan de training verbinden |
| C06 | Ondersteunde annotatie | AI/provider-voorstellen en menselijke teamreview geregistreerd | Herkomst blijven vermelden |
| C07 | Consistente afspraken als team | Regels en gezamenlijke goedkeuring vastgelegd in REVIEW.md | Geen individueel reviewlog verzinnen; mondeling toelichten |
| C08 | Blur, occlusie en twijfel behandelen | Regels vastgelegd; twijfelgevallen volgens verklaring buiten de huidige selectie | Werkelijke voorbeelden kunnen uitleggen |
| C09 | Train/val-strategie | 48/32, gescheiden wedstrijdgroepen; labels/splits ongewijzigd bij review | Datasetidentiteit bij training/evaluatie bewaren |
| C10 | Fine-tuning op geannoteerde set | Echte eerdere trainingen en Andrews trainingsnotebook aanwezig | Precieze koppeling tussen definitieve 80-reviewset en concrete training/evaluatie verduidelijken |
| C11 | mAP@50 en mAP@50:95 | Beide AP-maten aanwezig; oorspronkelijke Andrew-validatie en checkpointmetrics uit Jorres pakket toegevoegd | Geen historische AP als score van Andrew of YOLO26 presenteren; nieuwe ruwe evaluaties delen |
| C12 | Foutanalyse met FP/FN | Concrete historische fouten, hypotheses en negatieve resultaten aanwezig | Eigen voorbeelden zelfstandig verdedigen |
| C13 | Minstens vier bekende veldpunten | In code aanwezig, met onafhankelijke controles | Actuele eigen kalibratie en visuele beoordeling |
| C14 | Homography met OpenCV | Aanwezig in geometry.py | Puntparen en vlakke aanname kunnen verklaren |
| C15 | Ruimtelijk zinvolle minimap | Geïmplementeerd; werkelijke automatische demonstratie van 75 frames meegeleverd, 73 projecties beschikbaar | Actuele geaccepteerde statische einddemonstratie |
| C16 | Perspectief begrijpen | Uitleg aanwezig | Individuele mondelinge beheersing aantonen |
| C17 | Lokale interface voor MP4 | Streamlit, starters, tests en technische controles aanwezig | Verse installatie en einddemonstratie van gekozen versie |
| C18 | Gesynchroniseerd beeld en minimap | Gedeelde framerecords en renderer, plus werkelijk berekende demonstratievideo aanwezig | Naast synchronisatie ook geometrische juistheid controleren |
| C19 | Gestructureerde experimenten | Resolutie-, tegel-, freeze- en YOLO26-protocol beschreven | Ruwe lokale nieuwe experimentbestanden delen |
| C20 | Proces en individueel eigenaarschap | Andrews verklaring, Jorres afronding en gezamenlijke logs aanwezig | Milan, Andrew en Jorre beschreven; individuele verdediging en overige persoonlijke verklaringen blijven nodig |
| C21 | Transparant GenAI-gebruik | Milans persoonlijke verklaring, Andrews hoofdstuk 16 en gezamenlijke disclosures verwerkt | Afzonderlijke cursuspolicy nog controleren |

## Optionele uitbreidingen

| Onderdeel | Status en grens |
|---|---|
| Spelertracking | Gedeelde ByteTrack-route; trackinghandleiding rapporteert IDF1 93,95% en 9 ID-wissels op 450 ontwikkelframes. Ruwe lokale auditmap ontbreekt hier. |
| Andrews prototype-tracking | Eigen snelheidsvoorspelling, smoothing en greedy referee-matching beschreven. Niet gelijkgesteld aan ByteTrack of automatisch als volledig geïntegreerd voorgesteld. |
| Automatische keypoints | Extern veldmodel en geometriecontrole geïntegreerd. Geen automatische claim dat een eigen gereviewde keypoint-fine-tuning is geslaagd. |
| Teamindeling | Conditionele ontwikkelmetingen aanwezig; keeperteams blijven zwak. |
| Verdere extra's | Trajecten, afstandsschattingen, framecontrole en exports. Geen bewezen algemene afstandsnauwkeurigheid in meters. |

De genoemde uitbreidingen zijn opties. De opdracht verplicht niet allemaal tegelijk een specifieke tracker, KDE-heatmap, YOLO-versie, minimum-FPS of een afzonderlijk testbestand. Voor sterke generalisatieclaims blijft een onafhankelijke test wel nodig.

## Indiening en zichtbaarheid

| Onderdeel | Beschikbaar | Grens |
|---|---|---|
| PDF-rapport | Rapport_Sports_Vision.pdf plus Markdown-bron | Open punten zijn expliciet vermeld |
| Trainingscode/notebook | Training_en_Resultaten.ipynb, originele Andrew-notebooks en projectmodules | Inspectienotebook start geen nieuwe training |
| Uitvoercode | Reeds in de repository onder src, scripts, configs, streamlit_app.py en final | GitHub-final en hoofdbron hebben verschillende startprocedures |
| Presentatie | Jorres presentatie, twaalf bewerkbare slides; aangevuld met Milan | Team oefent eigen verdediging |
| Eén ZIP per team | Opnieuw samengesteld uit de definitieve uploadmap; zie CONTROLE_DOCUMENTATIE.json | Oude lokale ZIP's zijn geen actuele GitHub-release en worden niet als broncode gecommit |
| Goed geschreven/AI-gecheckt | Rapport en slides met Codex-hulp opgesteld en nagekeken | AI-bijdrage staat expliciet vermeld |
| GitHub-zichtbaarheid | Documentatie-map en directe verwijzingen naar Andrew en Jorre | Publicatiecontrole verifieert de remote commit |

## Nieuwe controles en geregistreerde bronnen

- Jorres gedeelde controle van 14 november: 537 tests geslaagd, één GPU-proef overgeslagen en vier subtests geslaagd op CPU. Dit is een bronrapportage uit checks.json.
- Huidige lokale samenvoeging: 75 gerichte regressietests geslaagd. Geen nieuwe training of volledige echte video-evaluatie.
- De actuele 80 labels zijn goedgekeurd volgens de expliciete teambevestiging. De oorspronkelijke AI/provider-herkomst en de labels/splits blijven behouden.
- Het documentatienotebook controleert bestanden en hashes en leest de gedeelde reviewregistratie. Jorres uploadnotebook en oorspronkelijke Andrew-notebooks blijven aanwezig. Rapport en presentatie zijn op weergave gecontroleerd.

## Controle van het definitieve inzendingspakket

De uploadmap bevat één definitief rapport, Jorres bijgewerkte presentatie, het uitgevoerde overzichtsnotebook, de oorspronkelijke Andrew-notebooks, uitvoercode, gekozen gewichten, trainingsdata en een demonstratie. De historische CONTROLE.json blijft bronbewijs; CONTROLE_DOCUMENTATIE.json beschrijft uitsluitend de nieuwe pakketcontrole. De inhoudelijke review van de opdracht is geen automatische scoregarantie.

## Resterende prioriteiten

1. Koppel de definitieve eigen labelselectie helder aan de training en beide AP-maten. Menselijke review is al geregistreerd.
2. Lever een actuele geaccepteerde statische MVP-demonstratie met geldige homography en minimap.
3. Deel de ruwe nieuwe YOLO26-/trackingexperimenten, inclusief logs, gewichten, hashes en afzonderlijke evaluaties.
4. Controleer de aparte GenAI-policy en oefen de individuele verdediging.
5. Controleer het uiteindelijke ZIP-bestand op dezelfde gekozen code-, model- en datasetversie.
