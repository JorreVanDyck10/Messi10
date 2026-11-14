# YOLO26 gebruiken en terugschakelen

Alleen de spelersdetector verandert. Baldetectie, rollen, teams, ByteTrack, veldprojectie, minimap en afstanden gebruiken dezelfde bestaande pipeline.

**Status:** Raouls getrainde YOLO26-spelerscheckpoint ontbreekt nog in deze checkout. De import en startprocedure zijn voorbereid; de volledige YOLO26-voetbalroute kan pas met zijn `best.pt` gecontroleerd worden. Een algemeen COCO-model vervangt het voetbalcheckpoint niet. Er is hier geen nieuwe voetbaltraining uitgevoerd.

## Installeren en starten

Vanuit de projectmap, met de bestaande werkende Python 3.11/3.12-appomgeving:

```powershell
./scripts/Setup-Yolo26.ps1 -BasePython .venv/Scripts/python.exe
./scripts/Import-Yolo26.ps1 -Weights 'C:/pad/naar/Raouls/best.pt'
./scripts/Start-Yolo26.ps1 -CheckOnly
./scripts/Start-Yolo26.ps1
```

De aparte omgeving gebruikt Ultralytics 8.4.211 en hergebruikt Torch uit de basisomgeving. Bewaar die basisomgeving. Een bestaande YOLO26-omgeving wordt niet overschreven. De import controleert architectuur, klasse `player`, echte gewichtsbytes en SHA-256. Het checkpoint wordt gekopieerd naar `artifacts/yolo26-players-v1/<hash>/`; het profiel komt in `configs/models-broadcast-yolo26.json`. Deel vervolgens dat profiel en die modelmap via Git LFS met de anderen.

De startprocedure kiest CUDA indien beschikbaar, anders CPU. Eventueel kun je `-Device cpu` of `-Device 0` meegeven. Beide analysepagina's krijgen hetzelfde gekozen profiel. Automatische veldherkenning gebruikt de bestaande lokale `.tools/field-runtime.json`; als die installatie ontbreekt, is handmatige veldkalibratie beschikbaar. `-CheckOnly` laadt de echte detectie-, rol- en shirtmodellen zonder de app te openen.

## Terug naar YOLO11

```powershell
./scripts/Start-Yolo11.ps1 -CheckOnly
./scripts/Start-Yolo11.ps1
```

Gebruik eventueel `-Python 'pad/naar/python.exe'` voor een andere bestaande appomgeving. Het bewaarde profiel is `configs/models-broadcast-yolo11.json`. Ook de oorspronkelijke spelersgewichten zijn afzonderlijk gekopieerd naar `artifacts/yolo11-original-v1/players_best.pt`, met dezelfde SHA-256: `fb6deea2d6c51bada9d3f8bfd666882212f45d1a1584547d02dc98aa59aaaa25`. Het oorspronkelijke standaardprofiel en de oorspronkelijke startprocedures blijven beschikbaar.

## Keuzes

Een afzonderlijke omgeving houdt de oorspronkelijke YOLO11-bibliotheken beschikbaar. YOLO26 krijgt expliciet `nms=True`, dezelfde detectiekop als in de bestaande vergelijkingscode; een controle weigert een afwijkende actieve end-to-end-kop. Drempel, beeldresolutie en boxfusie blijven behouden. Deze aansluiting bewijst geen betere nauwkeurigheid: daarvoor moeten de echte gewichten op dezelfde video's gecontroleerd worden. De import schrijft oude YOLO11-scores daarom niet toe aan YOLO26.
