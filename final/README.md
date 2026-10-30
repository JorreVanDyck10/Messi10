# Sports Vision — final

Deze map is het afzonderlijk startbare eindpakket van **30 oktober 2026**. Het bevat de actuele interface, detectie, homography, minimap, tracking, teams en afstandsschatting, met de geselecteerde modellen en de belangrijkste onderbouwing. De eenvoudige schoolmodus is de standaardstart.

## Downloaden en starten

Vereist: Windows, Python **3.11**, Git met **Git LFS** en PowerShell. Internet is nodig tijdens installatie. Voer vanuit een nieuwe checkout uit:

```powershell
git clone https://github.com/JorreVanDyck10/Messi10.git
cd Messi10
git lfs install
git lfs pull --include="final/**"
cd final
python scripts/verify_final.py
.\scripts\Setup-Final.ps1
.\scripts\Start-Final.ps1
```

`python` moet naar Python 3.11 wijzen. Geef indien nodig het volledige pad mee via `Setup-Final.ps1 -Python 'C:\pad\naar\python.exe'`. De installatie maakt een eigen `.venv` in deze map. De CPU-start werkt zonder NVIDIA-kaart; verwerking duurt dan langer.

Voor de NVIDIA-laptop:

```powershell
.\scripts\Setup-Final.ps1 -Cuda
.\scripts\Start-Final.ps1 -Device 0
```

Open de lokale URL die Streamlit toont. Upload een MP4 met een vaste camera, selecteer het zichtbare velddeel, klik de veldpunten en controlepunten, keur de kalibratie na visuele controle goed en verwerk de clip. Resultaten komen onder `runs/school`.

Alleen de modelbestanden en het gekozen device controleren:

```powershell
.\scripts\Start-Final.ps1 -CheckOnly
```

## Inhoud

| Bestand of map | Doel |
| --- | --- |
| [Korte uitleg](docs/Sports_Vision_Korte_Uitleg_NL.docx) | Beknopte projectuitleg in Word |
| [Verdedigingsverslag](docs/Verdedigingsverslag_Sports_Vision_NL.docx) | Uitgebreide uitleg voor de mondelinge verdediging |
| [Projectuitleg in PDF](docs/Projectuitleg_en_mondelinge_verdediging.pdf) | Bestaande export van de projectuitleg |
| [Schoolhandleiding](docs/Schoolversie_en_Verdediging.md) | Homography, modellen, labelafspraken en verdediging |
| [GenAI-disclosure](docs/GenAI_Disclosure.md) | AI-gebruik en openstaande menselijke review |
| `streamlit_app.py`, `src/football_pipeline/` | Interface en volledige pipelinecode |
| `persoon1/` | Annotatie-editor, training en evaluatiehulpmiddelen |
| `configs/`, `artifacts/` | Gekozen profielen, trackinginstellingen en gewichten |
| `datasets/school-ball80-review-v1/` | 80 beelden met ballabels en herkomst: 48 train, 32 validatie |
| `examples/teamtrack_20s.mp4` | Bestaand TeamTrack-voorbeeldfragment voor invoercontrole |
| `reports/` | Bewaarde modelmetingen, voorbeelden en pakketcontrole |
| `tests/` | Gerichte softwaretests voor app, kalibratie, verwerking, teams en afstanden |
| `SOURCE.json`, `MANIFEST.json` | Herkomst van de snapshot en SHA-256 per pakketbestand |

De Word- en PDF-bestanden zijn bestaande documenten, ongewijzigd overgenomen. De technische handleidingen bevatten ook historische verwijzingen naar de volledige repository. **Voor installatie geldt deze README.** De reviewset staat hier onder `datasets/`, ook waar oudere documentatie `data/school-ball80-review-v1` noemt. Oude experimenten, volledige trainingscorpora, caches en virtuele omgevingen staan buiten het eindpakket.

## Modellen en uitbreidingen

De schoolbasis gebruikt spelers/officials **P006** en balmodel **F005** op volledige beelden. Voor de experimentele broadcastbal v3 met tegelverwerking:

```powershell
.\scripts\Start-Final.ps1 -BroadcastTiles
```

De broadcastuitbreiding gebruikt de geselecteerde broadcastspelers, rolherkenning, teams en automatische veldkalibratie. Het afzonderlijke PnLCalib-veldmodel wordt met vastgelegde upstreamversie en checksums geïnstalleerd; de grote externe veldgewichten en omgeving worden niet gedupliceerd in Git:

```powershell
python scripts/setup_field_model.py --device cpu
.\scripts\Start-Final.ps1 -Mode broadcast
```

Voor CUDA gebruik je `--device cuda:0` bij de veldinstallatie en `-Device 0` bij de broadcaststart. Het veldmodel houdt zijn eigen omgeving onder `.tools`. De broadcastmodus vereist deze aanvullende installatie; de schoolmodus heeft die niet nodig.

Afstanden vereisen bestaande tijdelijke track-ID's. Ze zijn schattingen op basis van veldposities en meetdekking, geen gevalideerde spelersstatistieken. Zie [afstanden](docs/Afgelegde_Afstand.md) en [opgeslagen analyses en framecontrole](docs/Resultaten_en_Framecontrole.md).

## Annotaties en reproduceerbaarheid

Open de meegeleverde reviewset vanuit `final`:

```powershell
$env:PYTHONPATH = 'src;.'
.\.venv\Scripts\python.exe -m persoon1 annotate --manifest datasets/school-ball80-review-v1/manifest.json --split all --port 8765
```

De labels zijn bestaande provider-/AI-voorstellen. Menselijke review staat open. De 80 beelden zijn ontwikkelgegevens; ze vormen geen onafhankelijke eindtest. `verify_final.py` controleert de oorspronkelijke pakketchecksums, dus na bewuste labelwijzigingen meldt het script die wijzigingen.

De oorspronkelijke trainingsmetingen blijven gekoppeld aan hun eigen data en experimenten. De 80-beeldenreviewset heeft geen nieuwe training of nieuwe prestaties opgeleverd. De trainingscode is meegeleverd; voor het herhalen van historische trainingen blijven de volledige brondata uit de hoofdrepository nodig.

## Controles

```powershell
python scripts/verify_final.py
.\.venv\Scripts\python.exe -m football_pipeline doctor
.\.venv\Scripts\python.exe -m pytest -q
```

De pakketcontroles worden beschreven in [reports/final-checks.json](reports/final-checks.json). Softwaretests controleren de werking; de historische modelmetingen zijn ontwikkelmetingen. Een onafhankelijke eindtest, volledige menselijke labelreview en onafhankelijke tracking-/afstandsnauwkeurigheid zijn nog niet uitgevoerd.
