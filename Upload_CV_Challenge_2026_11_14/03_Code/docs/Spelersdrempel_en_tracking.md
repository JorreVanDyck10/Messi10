# Spelersdrempel en tracking

De gewone Streamlit-app toont bij **Verwerken** de confidence-drempel voor spelers. De beginwaarde is **0,25**; het oorspronkelijke modelprofiel, de detectiedrempels, de trackingconfiguratie en Andrews balinstellingen worden niet overschreven.

## Aanpassen en terugzetten

- Verschuif **Confidence-drempel spelers** tussen 0,10 en 0,95. De aanduiding verandert naar **Aangepaste instellingen**.
- De gekozen drempel geldt dan strikt voor spelerboxen, minimap, zichtbare trajectpunten, tellingen en teamweergave, ook als een speler al een tracking-ID heeft. Lagere scores blijven in de ruwe framegegevens beschikbaar en kunnen intern gekoppeld blijven.
- Kies daarna **Verwerken**. Verschuiven start geen dure analyse automatisch en bestaande resultaten krijgen geen nieuwe betekenis.
- Klik op **Oorspronkelijke instellingen herstellen** om terug te keren naar 0,25 én het oorspronkelijke beleid: actuele detecties met een tracking-ID mogen onder die drempel zichtbaar blijven. Klik opnieuw op **Verwerken**.
- Met **Oorspronkelijke model- en trackinginstellingen downloaden** bewaar je het geselecteerde modelprofiel, de ongewijzigde trackingdrempels en het oorspronkelijke weergavebeleid als JSON.

De keuzes gelden voor de huidige sessie. Elke nieuwe run bewaart het effectieve `player_policy` in het runmanifest en de framerecords. De cache houdt rekening met die keuze. Oude framerecords zonder dit veld behouden hun oorspronkelijke beleid. De resultaatpagina vermeldt de instellingen waarmee die analyse gemaakt is.

Dezelfde bediening staat ook in **Alles automatisch analyseren na upload**. Een nieuwe upload mag daar zoals voorheen automatisch starten. Na verschuiven of herstellen wacht de app altijd op **Verwerken**; dat geldt ook wanneer je van de handmatige naar de automatische route schakelt.

De momentopname van vóór deze wijziging staat lokaal in `C:/Messi10/artifacts/player-threshold-tracking-20261113/original-settings/`, inclusief hashes en de originele configuratiebestanden. Modelgewichten worden via hun bestaande paden en hashes geïdentificeerd; ze worden niet vervangen of opnieuw getraind. De `final`-map wordt niet aangepast.

## Wat tracking doet

ByteTrack koppelt actuele spelerboxen met bewegingsvoorspelling en boxoverlap. Detecties met lage scores kunnen een bestaand ID helpen behouden. De schuif verandert deze interne invoer niet. Een confidence-score is geen gemeten nauwkeurigheidspercentage.

De huidige tracker gebruikt een hoge drempel van 0,25, een lage drempel van 0,10, nieuwe tracks vanaf 0,25 en een buffer van 30 updates. Bij 25 fps is de buffer circa 1,2 seconden; dit garandeert geen correcte herkoppeling. De buffer houdt intern informatie bij en tekent geen verzonnen waarnemingen.

In de automatische modus wordt camerabeweging met achtergrondkenmerken gecompenseerd. Bij een camerawissel of onbetrouwbare compensatie start de tracker met nieuwe tijdelijke ID's. Het zijn geen namen, rugnummers of gegarandeerd unieke spelers over een hele wedstrijd. Overlap en gemiste detecties kunnen extra ID-wissels veroorzaken.

Een beeld-ID kan tijdens ontbrekende veldherkenning blijven bestaan. Een minimaptraject en afstandsmeting vereisen actuele geldige veldposities; over ontbrekende waarnemingen worden geen lijnen doorgetrokken. Bij een strikte weergavedrempel worden ook afstandsintervallen onderbroken wanneer de speler niet meetelt.

## Controle opnieuw uitvoeren

De ontwikkelmeting van 13 november 2026 leverde onderstaande resultaten op,
met het huidige model en ongewijzigde ByteTrack-instellingen. Iedere clip
bevat 150 opeenvolgende gelabelde validatieframes; de veldselectie gebruikt
providergeometrie.

| Clip | Beeld-/veld-IDF1 | ID-wissels |
|---|---:|---:|
| SNGS-021 | 98,12% | 0 |
| SNGS-039 | 89,73% | 8 |
| SNGS-078 | 95,12% | 1 |
| Samen, 450 frames | **93,95%** | **9** |

Dit is geen onafhankelijke eindtest of meting over een volledige wedstrijd.
Op de laatste upload kregen 97,47% van de spelerwaarnemingen een ID; er waren
37 tijdelijke ID's in 20 seconden. Zonder referentie-ID's bewijst dit geen
trackingnauwkeurigheid of aantal unieke spelers. Op uploadframe 250 toont de
oorspronkelijke stand 21 spelers en de strikte drempel 0,65 toont er 18, met
dezelfde interne ID's en identieke balgegevens. Alle drie weergavevideo's
bevatten dezelfde 500 bronframes. CSV-tellingen en JSON zijn gecontroleerd.

Softwarecontrole: 538 tests en vier subtests geslaagd, inclusief herstelknop,
automatische upload zonder herverwerking bij schuiven, cache, teamcorrecties,
lage trackingconfidence en camerawissels. Lint, formattering, codekaart en
functiedocumentatie zijn gecontroleerd. Begin/midden/einde en gemeten
ID-wisselfragmenten zijn visueel bekeken; geen volledige menselijke labelreview.

```powershell
Set-Location C:/Messi10
& ./.venv/Scripts/python.exe -m pytest tests/test_player_display_settings.py tests/test_team_pipeline.py tests/test_tracking.py tests/test_tracking_motion.py -q
& ./.venv/Scripts/python.exe -m scripts.audit_player_tracking --output artifacts/player-threshold-tracking-rerun --upload-run C:/Messi10/runs/ad76870607ac6b98a5d85819955f62132e265129108714e8ce82469d057bbe7e
```

De audit gebruikt uitsluitend drie bestaande temporele validatieclips en de vaste laatste upload. Detector, teams en trackingparameters blijven gelijk. `tracking-validation.json` bevat IDF1 en ID-wissels met referentielabels; `upload-observations.json` bevat alleen waarneembare continuïteit zonder identiteitswaarheid. De drempelvideo's gebruiken exact dezelfde opgeslagen detecties en ID's. Het meetverslag komt in `C:/Messi10/artifacts/player-threshold-tracking-20261113/REPORT.md`. De resultaten zijn ontwikkelvalidatie, geen onafhankelijke eindtest.
