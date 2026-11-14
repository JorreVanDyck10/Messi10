# Sports Vision - uploadpakket

Team: Andrew, Milan, Raoul en Jorre. Versie: 14 november 2026.
Broncode: main commit 524d081a, inclusief de technische fixes en bevestigde review van 80 balbeelden.

## Inhoud

- 01_Rapport/Sports_Vision_Rapport.pdf: projectverslag met aanpak, training, fouten, resultaten, extra's en GenAI.
- 01_Rapport/Bronmateriaal_Milan/: originele studiegids-PDF gepubliceerd door Milan; historische bron, geen actuele statusverklaring.
- 02_Presentatie/Sports_Vision_Presentatie.pptx: bewerkbare presentatie met bronverwijzingen in de notities.
- 03_Code/Training_en_Evaluatie.ipynb: gecontroleerd overzicht, checkpointmetadata en optionele herhaling van training.
- 03_Code/Andrew_Prototype/train.ipynb en check_mAP.ipynb: originele notebooks met historische uitvoer.
- 03_Code/: actuele app, bibliotheek, scripts, tests, gekozen gewichten, veldmodellen en trainingsdata.
- 04_Demonstratie/: invoer van 3 seconden en de werkelijk berekende video met minimap en teams.
- BESTANDEN_SHA256.json: identiteit van alle bestanden. CONTROLE.json: uitgevoerde verpakkingscontroles.

## Starten op Windows

Haal de volledige uploadmap inclusief Git LFS-bestanden op. Installeer Python 3.11 en Git voor Windows. Open PowerShell in 03_Code:

```powershell
powershell -ExecutionPolicy Bypass -File .\Setup-Upload.ps1
powershell -ExecutionPolicy Bypass -File .\Start-Upload.ps1
```

De installatie downloadt Python-bibliotheken en FFmpeg. De modelgewichten en PnLCalib-broncode zijn al meegeleverd. Virtuele omgevingen en computerafhankelijke runtimepaden worden lokaal aangemaakt. De standaardinstallatie gebruikt CPU en vereist geen NVIDIA-kaart. Een CPU kan voor enkele seconden video meerdere minuten nodig hebben.

Upload ../04_Demonstratie/01_Invoer_3_seconden.mp4. Het opgeslagen resultaat is ook zonder installatie afspeelbaar. Voor een statische camera met zelf aangeklikte veldpunten: Start-Upload.ps1 -Manual. Kies minstens vier bekende veldpunten plus de onafhankelijke controles. De originele gedeelde starters blijven bewaard voor hun eigen workflows.

## Training nakijken

Start na installatie in 03_Code:

```powershell
.\.venv\Scripts\python.exe -m notebook Training_en_Evaluatie.ipynb
```

Het overzichtsnotebook voert standaard geen nieuwe training of video-inference uit. De standaardcellen tonen echte lokale datasetgegevens, opgeslagen resultaten en herkomst. RUN_TRAINING=True start bewust een nieuwe run; oude gewichten worden niet overschreven. Open de originele Andrew-notebooks vanuit Andrew_Prototype zodat archive/data.yaml relatief klopt.

De originele checkpoints bevatten historische absolute trainingspaden. De nieuwe notebookroute maakt een lokale data.yaml. Nieuwe training is niet bit-voor-bit gelijk aan oude GPU-runs. Het oorspronkelijke tussencheckpoint voor de laatste spelersronde is niet beschikbaar; de meegeleverde herhaalroute begint daarom bij pretrained YOLO11s. Dit is expliciet een nieuwe training met dezelfde architectuur en data, geen reconstructie van de oude run.

## Modelkeuze

Het uploadprofiel gebruikt YOLO11s voor veldspelers en Andrews YOLOv8x uitsluitend voor baldetectie. De bestaande appearance-, shirt- en contextmodules ondersteunen rollen en neutrale Team A/B-groepen. Andrews originele model heeft vier klassen; zijn notebookcijfers over vier klassen zijn geen score voor alleen de bal en geen YOLO11-score. Historische alternatieve profielen blijven als documentatie staan; alleen meegeleverde gewichten zijn direct bruikbaar.

## Herkomst en beperkingen

De 80-beeldenreviewset is volgens expliciete gebruikersbevestiging menselijk gecontroleerd en akkoord. Twijfelgevallen vielen buiten de selectie. Andere historische datasets worden daarmee niet automatisch goedgekeurd. De broncode, notebooks en documenten zijn met Codex-ondersteuning gemaakt; de AI-herkomst is vermeld. De presentatie is een voorbereid deck voor het team, geen bewijs van een reeds afgelegde verdediging.

De huidige functionele tests zijn op een bestaande Windows/Python 3.12 CPU-omgeving uitgevoerd. Er is geen nieuwe schone GPU-installatie of onafhankelijke nauwkeurigheidstest uitgevoerd. De installatiebestanden voor dit uploadpakket zijn op syntax en lokale padbinding gecontroleerd. De automatische kalibratiedekking van de demonstratie zegt niet dat de veldposities op 97,3% van de frames nauwkeurig zijn.

PnLCalib staat onder GPL-2.0. De originele LICENSE en broncode zijn meegeleverd. Ultralytics kent eigen licentievoorwaarden. Brondata en hun publicaties blijven beschreven in de oorspronkelijke metadata en bronnenbestanden. Dit pakket is bedoeld als onderwijsinzending, niet als claim op eigendom van externe data.


## Ophalen via GitHub

De grote bestanden gebruiken Git LFS. Na het ophalen van de repository: `git lfs pull --include="Upload_CV_Challenge_2026_11_14/**"`. Controleer dat modellen en beelden echte bestanden zijn, geen kleine LFS-pointerteksten. Er is voor deze stap nog geen ZIP gemaakt.
