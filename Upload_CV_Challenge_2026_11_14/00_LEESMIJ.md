# Sports Vision - uploadpakket

Team: Andrew, Milan Wouters, Raoul en Jorre. Documentatieversie 5: 15 november 2026.
Broncode: main commit 524d081a, inclusief de technische fixes en bevestigde review van 80 balbeelden.

De definitieve PDF en Jorres presentatie staan in 01_Rapport en 02_Presentatie. [05_Documentatie](05_Documentatie/README.md) bevat de AI-beschrijvingen van Milan, Jorre en Raoul en Andrews eigen verklaring, de gezamenlijke disclosures, requirementscontrole en bronbewijzen. De PDF en presentatie zijn gelijk aan de actuele repository-documentatie. De code, modellen, data en demonstratie volgen Jorres uploadpakket; de documentatieronde voegt geen nieuwe training toe.

## Inhoud

- 01_Rapport/Sports_Vision_Rapport.pdf: projectverslag met aanpak, training, fouten, resultaten, extra's en GenAI.
- 02_Presentatie/Sports_Vision_Presentatie.pptx: bewerkbare presentatie met bronverwijzingen in de notities.
- 03_Code/Training_en_Evaluatie.ipynb: gecontroleerd overzicht, checkpointmetadata en optionele herhaling van training.
- 03_Code/Andrew_Prototype/train.ipynb en check_mAP.ipynb: originele notebooks met historische uitvoer.
- 03_Code/: actuele app, bibliotheek, scripts, tests, gekozen gewichten, veldmodellen en trainingsdata.
- 04_Demonstratie/: invoer van 3 seconden en de werkelijk berekende video met minimap en teams.
- 05_Documentatie/: definitieve AI-verantwoording, requirementscontrole en bronbijlagen.
- BESTANDEN_SHA256.json: actuele identiteit van alle bestanden. CONTROLE.json: oorspronkelijke controles van Jorre; CONTROLE_DOCUMENTATIE.json: nieuwe documentatie- en pakketcontrole.

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

De grote bestanden gebruiken Git LFS. Na het ophalen van de repository: `git lfs pull --include="Upload_CV_Challenge_2026_11_14/**"`. Controleer dat modellen en beelden echte bestanden zijn, geen kleine LFS-pointerteksten. De lokale inzendings-ZIP heet `Inzending_Sports_Vision_DEFINITIEF_v5_GITHUB_2026_11_15.zip` en bevat deze volledige map. De ZIP staat buiten deze map zodat zij zichzelf niet insluit. Voor GitHub blijven de map en Git LFS de bron; de ZIP is het uploadbestand.

## Aanvulling versie 5

Het AI-gebruik van alle vier teamleden staat in 05_Documentatie, het rapport en de presentatie. De beschrijvingen van Jorre en Raoul zijn aangeleverd door Milan.

Alle 80 gereviewde beelden zijn op hash, split en cropcoördinaten verbonden met de grotere historische baltraining. De oorspronkelijke 132 bronbeelden, 282 complete COCO-trainingscrops, begin-/eindgewichten en logs zijn toegevoegd. Open 03_Code/Bal_v2_Training_en_Labelkoppeling.ipynb voor de uitgevoerde audit en de standaard uitgeschakelde hertraincel. De historische AP geldt voor de volledige validatie van 73 beelden, niet voor een nieuwe afzonderlijke 32-beeldenmeting of Andrews huidige balmodel.

## Download voor indiening

[Download de definitieve inzendings-ZIP](https://github.com/JorreVanDyck10/Messi10/releases/download/cv-challenge-inzending-v5-20261115/Inzending_Sports_Vision_DEFINITIEF_v5_GITHUB_2026_11_15.zip). Alle persoonlijke bijdragen en AI-verklaringen zijn inbegrepen. De grote historische bronvideo staat afzonderlijk bij dezelfde release; de vereiste demonstratie en alle bijgevoegde annotatiebeelden blijven in de ZIP. Zie [DOWNLOAD_ZIP.md](DOWNLOAD_ZIP.md).
