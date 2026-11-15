# Gezamenlijke toepassing: rollen, teams en veld

De dataoverdracht `857adf5` is opgenomen, naast het werk van beide personen. De modellen werken achter elkaar in dezelfde videopipeline: veldpunten en lijnen, persoonsvoorstellen, getrainde rollen, Team A/B, voetpuntprojectie, telling en gesynchroniseerde H.264-uitvoer. De technische koppeling is gecontroleerd. Herkenningskwaliteit blijft beperkt; deze controle bewijst geen juiste herkenning op iedere video.

## Eén startopdracht

Vanuit de projectmap:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\Start-Wedstrijd.ps1
```

Dit selecteert het R007-rollenprofiel en opent de automatische veldmodus. Upload een MP4, vul bron en toegestaan gebruik in, en klik **Verwerken**. De ploegen heten **Team A** en **Team B**, zoals gevraagd. Onzekere teams blijven onbekend. Scheidsrechters, lijnrechters, stewards, supporters en personen blijven afzonderlijke voorspelde rollen. Alleen voorspelde spelers met een geldige actuele veldpositie tellen mee.

Voor handmatige kalibratie blijft `scripts\Start-Spelermodel.ps1 -Recognition players` beschikbaar. De algemene persoonsroute van persoon 2 blijft beschikbaar via `scripts\Start-Spelermodel.ps1`.

De detectieomgeving en de veldomgeving blijven afzonderlijk. Beide zijn hier lokaal voorbereid. Op een tweede laptop:

```powershell
git pull --ff-only origin main
git lfs pull
# Met een bestaande Python 3.11 of 3.12:
powershell -ExecutionPolicy Bypass -File scripts\Setup-Persoon1.ps1 -Python C:\pad\python.exe
# Met Python 3.11, afzonderlijk voor PnLCalib:
C:\pad\naar\python311.exe scripts\setup_field_model.py
```

De `C:\pad`-waarden zijn voorbeelden die je vervangt. De veldsetup downloadt officiële gewichten en CUDA-dependencies onder `.tools` en `weights`; de lokale omgevingen staan niet in Git. De detectieomgeving wordt niet aangepast. Een eigen veldruntime kan met `Start-Wedstrijd.ps1 -FieldRuntime C:\pad\field-runtime.json` worden aangewezen. Voor CPU moeten zowel detectie (`-Device cpu`) als de afzonderlijke veldsetup (`--device cpu`) expliciet op CPU staan. Het startscript neemt de bestaande veldruntime over en overschrijft geen eigen veldmodelkeuze.

## Werkelijke controles

| Controle | Uitkomst en beperking |
|---|---|
| Nieuwste dataset en clips | 48 unieke beelden, 36 train/12 val, 512 `person`-boxen, 36 balboxen; bestanden, coördinaten, dataloader en acht clips gecontroleerd |
| Vaste camera, echte R007-inference | Alle 150 ontwikkelframes van de oorspronkelijke video verwerkt; rollen, teams, projecties en H.264 op dezelfde tijdlijn |
| Automatische veldroute, echte netwerken | Alle 120 frames van de bestaande Commons-ontwikkelpilot door de aparte PnLCalib-worker én R007 verwerkt; uitvoeraudit geslaagd |
| Geen betrouwbare veldherkenning | Op deze Commons-clip 0/120 geldige kalibraties; veldposities en veldtellingen blijven onbekend |
| Team- en rolcontract | Classifier-ID's, drempels, abstentie, teammethode en totalen gecontroleerd; niet-spelers tellen niet mee |
| Interface | Gezamenlijke workflow, leeg frame, bronframe kiezen en opgeslagen uitvoer openen getest |

De definitieve softwarecontrole slaagt met **206 tests en 4 subtests**. Ruff, formattercontrole, pakketcontrole en PowerShell-parsercontrole slagen eveneens. Daarnaast is de echte automatische uitvoer in Streamlit geopend op frames 0, 60 en 119; er is daarbij geen menselijke referentie of goedkeuring geregistreerd.

De vaste pilot heeft 14–32 voorspelde spelers op het veld, mediaan 22. Dat zijn detecties, geen gecontroleerd wedstrijdaantal: gemiste, dubbele of verkeerd geclassificeerde personen blijven mogelijk. De afgeleide clip heeft een eigen hash en gebruikt daarom videolokale kleurclusters. Team A/B is daarbij niet bewezen voor iedere speler. De automatische Commons-proef toont eveneens duidelijke rolfouten bij een andere camera en kleding.

Deze gezamenlijke proeven draaiden op de werkelijk beschikbare **RTX 3050 Laptop GPU**. De oudere 4050-metingen van persoon 2 blijven afzonderlijke metingen van zijn toenmalige profielen; die snelheden en kwaliteit worden niet aan R007 toegeschreven.

De acht nieuwe panoramaclips en hun 48 crops hebben eigen bronidentiteiten en afmetingen. Ze krijgen geen kalibratie van een andere video. De labels hebben klassen `person` en `ball`; ze worden niet als speler-, official- of teamlabels ingevoerd. De modellen zijn door deze datasetcontrole niet opnieuw getraind. Historische datasets blijven bestaan; het totale project bevat meer dan deze nieuwe 48 beelden.

## Bewijs en herhaling

Rapporten: `reports/joint-integration/static-roles-pipeline.json`, `automatic-roles-pipeline.json`, `incoming-football48-validation.json` en `software-tests.xml`. Video's en controlebeelden staan op de werkelijke lokale uitvoerpaden in die rapporten.

Na projectinstallatie kan de gezamenlijke proef op een eigen ontwikkelclip worden herhaald:

```powershell
.\.venv\Scripts\python.exe -m scripts.verify_player_pipeline C:\pad\clip.mp4 --auto-field --models configs\models-players.json --source "Videobron" --usage "Toegestaan gebruik" --runs runs\joint-local --report reports\joint-local.json
```

Met `--automatic-calibration C:\pad\bundel\automatic_calibration.json` kan een bestaande bundel voor exact dezelfde video worden gebruikt, in plaats van `--auto-field`.

De Commons-pilot blijft **2018 FIFA U-17 Women's World Cup — New Zealand vs Canada — 24**, NaBUru38, [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), [bronpagina](https://commons.wikimedia.org/wiki/File:2018_FIFA_U-17_Women%27s_World_Cup_-_New_Zealand_vs_Canada_-_24.webm). Wijzigingen: eerste twaalf seconden, 10 fps, audio verwijderd en rollen-/veldoverlay met minimap. Afgeleide uitvoer valt onder dezelfde licentie; geen endorsement.

Speler-ID's en trajecten blijven in de automatische cameramodus uit zolang cameracompensatie niet gevalideerd is. Voor een vaste camera blijft ByteTrack beschikbaar na de bestaande MVP-acceptatie. Er zijn geen menselijke reviews, prestaties of acceptaties ingevuld die niet werkelijk zijn uitgevoerd.
