# Extra data en training voor veldherkenning

De nieuwe route verzamelt SoccerNet Calibration 2023 en circa dertig officiële
wedstrijdsamenvattingen binnen een corpuslimiet van 20 GiB. De eerste training
gebruikt alleen bestaande SoccerNet-labels. Highlightbeelden en modelvoorstellen
zijn expliciet **geen gecontroleerde trainingslabels**.

Het officiële veldmodel is al op SoccerNet getraind. Een betere SoccerNet-score
na fine-tuning is daarom geen onafhankelijke generalisatietest. De bestaande
Broadcast-clip is eveneens een ontwikkelclip. Onafhankelijke menselijke
projectiefouten en foutieve kalibraties daarop blijven onbekend tot review.

## Omgeving

Voer vanuit de projectmap uit:

```powershell
.\.venv\Scripts\python.exe scripts\setup_field_training.py
```

Dit maakt `.tools/field-training-env`, met de vastgezette inferentiebibliotheken
uit `.tools/pnlcalib-env` als alleen-lezen importbasis. De extra bibliotheken
worden uitsluitend in de trainingsomgeving geïnstalleerd. De Windows-DLL-paden
worden lokaal toegevoegd; de globale PATH en bestaande omgevingen worden niet
aangepast. Verwijder de basisomgeving niet zolang de training haar gebruikt.
De volledige packageversies staan in `installed-requirements.txt`.

De upstream checkout blijft vastgezet en ongewijzigd. De eigen aansturing gebruikt
één CUDA-GPU, zonder NCCL, DDP of W&B-login. Beide netwerken gebruiken dezelfde
Windows-veilige selectie van hoofdcamerabeelden. De bestaande semantische kanalen
en 960 × 540-modelinvoer blijven behouden.

De officiële labels bevatten kleine afrondingsoverschrijdingen aan de beeldrand.
Coördinaten maximaal 0.0001 buiten het genormaliseerde interval worden in de
ingelezen trainingskopie tot de rand begrensd; de bronbestanden blijven intact.
De datasetindex telt deze correcties. Grotere overschrijdingen, niet-eindige
waarden en ongeldige structuren worden met reden uitgesloten.

## Verzamelen en frames voorbereiden

```powershell
$fieldPython = '.\.tools\field-training-env\Scripts\python.exe'
& $fieldPython -m football_pipeline.field_data dataset --root data\field-corpus --limit-gib 20
& $fieldPython -m football_pipeline.field_data discover --root data\field-corpus
& $fieldPython -m football_pipeline.field_data highlights --root data\field-corpus --count 30 --ffmpeg .tools\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe
& $fieldPython -m football_pipeline.field_data frames --root data\field-corpus
& $fieldPython -m football_pipeline.field_learning propose --root data\field-corpus
```

De CLI serialiseert corpusmutaties met een writerlock. Voer bovenstaande stappen
achtereenvolgens uit. Stoppen en opnieuw starten behoudt downloads; bestaande
voltooide bestanden worden op hash gecontroleerd. Een server die geen Range
ondersteunt laat het gedeeltelijke bestand opnieuw downloaden. ZIP-extractie
controleert CRC en bestandspaden. Een gewijzigde bestaande dataset wordt niet
stilzwijgend vervangen.

De zoekopdrachten gebruiken de officiële kanalen FIFA, Serie A, Bundesliga, UEFA,
LaLiga en Barclays WSL. De selectie wisselt kanalen af. Niet-beschikbare video's
krijgen een foutstatus, waarna de verzamelaar andere kandidaten probeert.
Nieuwe downloads hebben maximaal 720p, onder de afgesproken 1080p-bovengrens.
Een grens per mediastream en ruimte voor samenvoegen voorkomen dat één lange
video het corpus vult. Onvoltooide bestanden tellen mee voor de opslaglimiet.
Een tijdelijke URL en publiek zichtbare video bewijzen geen trainingsrechten:
licentiemetadata, herkomst en gebruiksstatus staan in de inventaris.

Per video worden maximaal 180 visueel verschillende frames geselecteerd, met
minstens twee seconden afstand. Histogram- en beeldverschillen markeren
camerawissels. Een grasheuristiek scheidt overzichtskandidaten van mogelijke
close-ups; dit is geen menselijke beoordeling van kalibreerbaarheid. De beelden
worden maximaal 1280 pixels breed opgeslagen, met oorspronkelijke frame-index,
tijdstip, afmetingen en een checksum.

Een titel levert slechts een kandidaat-wedstrijd-ID. `match_identity_verified`
en `training_eligible` blijven onwaar. Voordat highlightbeelden later kunnen
meetrainen, moeten wedstrijdidentiteit, gebruik en labels gecontroleerd worden;
alle herhalingen en andere uploads van dezelfde wedstrijd moeten dan dezelfde
split krijgen. Ongedateerde compilaties worden niet in trainingssplits opgenomen.
De huidige trainer accepteert uitsluitend de officiële SoccerNet-datasetstructuur,
zodat een voorstelmap niet per ongeluk als trainingsdataset wordt gebruikt.

## Trainen en hervatten

Eerst één echte training- en validatiestap per netwerk:

```powershell
& $fieldPython scripts\run_field_training.py --smoke --comparison-frames 20 --output artifacts\field-training-smoke --video data\uploads\6cdaf4089cb578636bc4773bde0ebdc1e68b8554e169d413e855bdf144780f4a.mp4
```

Daarna de volledige run, gevolgd door vergelijking op 200 vooraf vastgelegde
validatiebeelden en alle frames van de Broadcast-clip:

```powershell
& $fieldPython scripts\run_field_training.py --output artifacts\field-training-full --video data\uploads\6cdaf4089cb578636bc4773bde0ebdc1e68b8554e169d413e855bdf144780f4a.mp4
```

De trainer gebruikt batch 1, mixed precision, Adam met learning rate 0.0001,
maximaal 30 epochs per netwerk en early stopping na acht epochs zonder lager
validatieverlies. Het puntennetwerk wordt eerst getraind, daarna het lijnnetwerk.
Zichtbaarheidsmaskers worden vóór het middelen toegepast op de kwadratische
heatmapfouten. De normalisatie telt uitsluitend pixels in geldige kanalen.
Een lege maskerset draagt nul verlies bij.

Een volledige job voert zelf eerst opnieuw een korte GPU-proef uit in de submap
`preflight`. Met `--wait-for-pid PID` kan de job vooraf wachten op een bestaande
GPU-taak. Het statusbestand toont die wachttijd expliciet.

`training-report.json` bewaart de datasetfingerprint, uitgesloten annotaties,
basisgewichten, software-identiteit, verliezen, epochduur en piek-GPU-geheugen.
Iedere voltooide epoch bewaart een resumecheckpoint met optimizer, AMP-scaler
en randomtoestanden. Start dezelfde opdracht opnieuw om te hervatten. Gewijzigde
invoer of trainingscode vereist een nieuwe uitvoermap. Een onderbroken epoch
wordt opnieuw uitgevoerd vanaf de vorige voltooide epoch.
Nieuwe checkpoints krijgen eerst een eigen bestand en pas daarna een atomair
gepubliceerde verwijzing. Een onderbreking tussen die twee stappen laat de
vorige voltooide epoch beschikbaar. Gelijktijdige trainers voor dezelfde
uitvoermap worden geweigerd.

De beste gewichten en `field-runtime.json` verschijnen na voltooiing van beide
netwerken. Smokegewichten zijn herkenbaar gemarkeerd. `job.json`, `train.log` en
`compare.log` tonen de fase, voortgang en eventuele fout. Een volledige run kan
lang duren op een laptop; er wordt geen vaste eindtijd beloofd.

## Vergelijking en modelgebruik

```powershell
& $fieldPython -m football_pipeline.field_learning compare --candidate artifacts\field-training-full\field-runtime.json --output artifacts\field-comparison --limit-valid 200 --video data\uploads\6cdaf4089cb578636bc4773bde0ebdc1e68b8554e169d413e855bdf144780f4a.mp4
```

De vergelijking gebruikt dezelfde geometrie- en camerabewegingsinstellingen voor
beide modellen. De validatiemeting rapporteert punt-tot-geannoteerde-lijnfouten
op vlakke rechte lijnen, dekking en kalibraties met een fout boven 1% van de
beelddiagonaal. Cirkels en boven het grondvlak gelegen doelonderdelen tellen niet
mee in deze projectmeting; dit is niet de volledige officiële SoccerNet-metric.
Geldige schattingen zonder scorebare referentielijnen worden apart geteld.

De Broadcast-meting rapporteert alle-frame-dekking en de langste uitval.
Menselijke projectiefouten en foutieve kalibraties krijgen daar `null` zolang
referenties ontbreken. Er worden geen beoordelaars of verbeteringen verzonnen.

Eigen gewichten worden door de bestaande worker ondersteund via hun gegenereerde
runtimebestand. De worker controleert de gewichtenhash, basisgewichten,
datasetfingerprint en het bijbehorende voltooide trainingsrapport. De bestaande
releasecontrole blijft gelden voor officiële modellen. Gewijzigde gewichten
leveren een andere cache-identiteit. De standaardruntime wordt niet automatisch
vervangen; een kandidaat kan eerst met de CLI worden onderzocht:

```powershell
.\.venv\Scripts\python.exe -m football_pipeline calibrate-auto data\wedstrijd.mp4 --runtime artifacts\field-training-full\field-runtime.json --source 'Eigen ontwikkelvideo' --usage 'Lokale beoordeling'
```

De corpuslimiet geldt voor downloads, uitgepakte datasets, geselecteerde frames en
voorstellen onder `data/field-corpus`. Trainingscheckpoints en vergelijkingsruns
staan apart onder `artifacts`; omgevingen en deze uitvoer vallen buiten de 20 GiB.
