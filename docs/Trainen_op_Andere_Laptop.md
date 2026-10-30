# Trainen via de app, op iedere eigen Windows-laptop

Open **Modellen trainen** in de zijbalk. Er zijn knoppen voor spelers, bal,
rollen, shirtkenmerken, spelerscontext, veldpunten en veldlijnen. **Train veldmodel
volledig** zet beide veldnetwerken achter elkaar; **Alles trainen** zet alle zeven
onderdelen in een lokale wachtrij. Een andere laptop start zijn eigen app en
gebruikt zijn eigen GPU. Alleen de website openen die op iemand anders zijn
computer draait, verplaatst de training niet naar jouw GPU.

## Eerste installatie

Gebruik het laptop-startpakket of een eigen kopie van deze broncode. Kopieer
geen `.venv` of `.tools` van een andere computer. Vereist: Windows, Python 3.11,
Git voor Windows en een NVIDIA-driver die de gekozen CUDA-runtime ondersteunt.

Open PowerShell in de nieuwe projectmap:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/Setup-Laptop.ps1
powershell -ExecutionPolicy Bypass -File scripts/Start-Laptop.ps1
```

De installatie maakt de appomgeving, FFmpeg/ffprobe en de afzonderlijke
veld-/trainingsomgeving lokaal aan. Hij gebruikt PyTorch 2.7.1 met CUDA 12.8,
ook voor de veldomgeving. De bestaande 4050-omgeving wordt niet overschreven:
het script weigert een bestaande andere `.venv`. Een door dit script begonnen
installatie kan wel worden hervat. Datasets en startgewichten komen uit GitHub;
een overdrachtspakket blijft beschikbaar als alternatief.

De officiële [PyTorch 2.7-release](https://pytorch.org/blog/pytorch-2-7/)
introduceert Blackwell-ondersteuning en CUDA 12.8-wheels. De huidige oudere
CUDA 12.1/12.4-omgevingen zijn daarom geen passend startpunt voor een RTX 5070.
De app controleert niet alleen `cuda.is_available`, maar voert een echte
voorwaartse en achterwaartse GPU-berekening uit. Een incompatibele installatie
wordt vóór training gemeld. De 5070 zelf is niet op deze 4050-laptop getest.

## Data en gewichten delen

### Rechtstreeks uit GitHub

De trainingsinvoer staat ook in Git: zie de
[catalogus met 15.324 bestanden](../datasets/training-runtime-v1/README.md).
De bestaande bijdragen onder `assets`, `datasets` en `final` zijn behouden.
Afbeeldingen en het grote featurecheckpoint worden via Git LFS opgehaald;
de labels, splits en bronmanifesten zijn eveneens meegedeeld.

Na clonen of bijwerken kun je `git lfs pull` uitvoeren. `Setup-Laptop.ps1`
haalt de benodigde bestanden ook automatisch op, controleert SHA-256 en
registreert de eigen projectmap. De trainingsknoppen werken daarna zonder
een los ZIP-bestand te importeren. Een andere drive of mapnaam is toegestaan.

### Een pakket gebruiken of modelgewichten teruggeven

Bij **Trainen op een andere laptop** maak je een trainingspakket of importeer
je een gekopieerd pakket. Het voorbereide pakket van deze ronde bevat ongeveer
5,1 GB: 15.324 bestanden met de geselecteerde beelden, labels, features en
startgewichten. Je kopieert het ZIP-bestand zelf naar de andere laptop.

De import controleert de inhoud met SHA-256, weigert uitvoerbare bestanden en
paden buiten het project en overschrijft geen afwijkende bestaande bestanden.
De bronmanifesten blijven bytegelijk bewaard. Trainingsjobs verbinden hun
werkruimteverwijzingen expliciet met de nieuwe projectmap en controleren de
beeld- en labelhashes opnieuw. `C:/Messi10` hoeft op de andere laptop niet te
bestaan. Alleen de vereiste referenties binnen het project worden verplaatst;
er wordt niet naar een toevallig gelijknamig bestand gezocht.

Na een afgeronde training gebruik je **Exporteer modelgewichten** bij de ronde.
Dit pakket bevat checkpoints en hun herkomst, niet opnieuw alle trainingsbeelden.
Dezelfde importknop op de andere laptop herkent een modelpakket. Hij maakt
experimentele profielen onder `configs` en combineert uitsluitend de werkelijk
getrainde onderdelen in:

- `configs/models-shared-candidate.json`: spelers, bal, rollen, shirt en context;
- `configs/field-shared-candidate.json`: veldpunten en veldlijnen.

Een nieuwe import vervangt alleen de onderdelen in dat modelpakket. Een
contextmodel blijft alleen in de combinatie wanneer zijn rol- en shirthashes
overeenkomen. Anders wordt context weggelaten: kies het gecombineerde proefprofiel
als **Startprofiel** en train context opnieuw. Contextfeatures worden dan opnieuw
uit echte detecties berekend met de actuele gewichten. De vaste aangeleerde
featureprojectie dient als starttransformatie; de context-uitvoerlaag wordt
opnieuw geleerd. Er worden geen rol- of veldlabels uit voorspellingen verzonnen.

## Training uitvoeren en verdelen

1. Voer de laptopinstallatie uit of importeer een datapakket en controleer de GPU.
2. Controleer onder **Trainingsdata en startprofiel** welke data werkelijk
   gebruikt worden. De veldindex van dit pakket heeft 128 trainingsbeelden en
   48 validatiebeelden uit verschillende wedstrijden. Meer GPU-capaciteit voegt
   niet automatisch nieuwe gelabelde data toe.
3. Kies het maximum aantal epochs en de trainingstijd per model. Start een
   onderdeel of de hele wachtrij. Datacontrole en featureberekening vallen buiten
   dit optimizerbudget. Shirttraining werkt met stappen in plaats van epochs.
4. De pagina toont status en log. Verversen, sluiten en opnieuw openen stopt
   de worker niet. **Stop na dit model** laat de huidige taak afronden en start
   geen volgende. Onderbroken processen worden bij heropenen herkenbaar gemeld;
   opnieuw trainen maakt een nieuwe map en bewaart oude checkpoints.

Er draait één beheerde trainingsronde tegelijk per laptop. Modellen krijgen
eigen subprocessen zodat GPU-geheugen tussen taken wordt vrijgegeven. De
startbatch voor YOLO houdt rekening met vrije VRAM; bekende CUDA-geheugenfouten
kunnen terugvallen naar een kleinere batch. De resolutie blijft vast, zodat
een laptop geen schijnbaar vergelijkbare meting op kleinere beelden uitvoert.

Een bruikbare verdeling is de veldnetwerken op de 5070 en spelers/rollen op de
4050. Deel daarna de modelpakketten. Train context nadat de gekozen rol- en
shirtmodellen samengevoegd zijn. De neutrale Team A/B-groepering per video blijft
een analysebewerking; shirtmetric en rol-/contextnetwerken zijn de aangeleerde
onderdelen die hier apart getraind worden.

## Evaluatie en gebruiken

Alle uitvoer staat onder `artifacts/training-workbench`. Nieuwe gewichten
vervangen het standaardprofiel niet automatisch. YOLO schrijft validatiemetrics;
de andere trainers schrijven hun bestaande taakmetingen. Een afgeronde job is
geen bewijs van betere nauwkeurigheid. Menselijke review en een onafhankelijke
eindtest blijven apart vereist.

Na beoordeling kun je de gecombineerde proefmodellen expliciet starten:

```powershell
scripts/Start-Laptop.ps1 -ModelProfile configs/models-shared-candidate.json -FieldRuntime configs/field-shared-candidate.json
```

Gebruik alleen de parameters voor profielen die daadwerkelijk bestaan.
Een sterkere GPU maakt vooral meer training, grotere batches of modellen
mogelijk; dezelfde gewichten en beeldinstellingen worden niet vanzelf
nauwkeuriger door alleen van GPU te wisselen.

De eerdere veldproef en zijn beperkingen staan in
[Spelers en veld](Spelers_en_Veld_Betrouwbaarheid_20261030.md). De drie getrainde
veldvarianten haalden de projectiecriteria niet en zijn niet als standaard
geactiveerd. De verbeterde weergave bewaart wel spelerboxen en beeld-ID's bij
velduitval, zonder ontbrekende veldposities als echte metingen te tonen.
