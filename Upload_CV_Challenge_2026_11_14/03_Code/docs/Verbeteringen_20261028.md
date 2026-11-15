# Verbeteringen van 28 oktober 2026

## Handmatige kalibratie op een gedeeltelijk veld

De app vereiste oorspronkelijk vier volledige veldhoeken. Nu kun je ook kiezen
voor het linker of rechter strafschopgebied. Je klikt de vier hoeken van het grote
gebied en controleert met twee andere hoeken van het kleine doelgebied. Een
bovenaanzicht toont steeds welk punt bedoeld wordt. De werking blijft hetzelfde
cursusprincipe: vier bekende puntparen, OpenCV-homography en aparte controles.

De presets gebruiken 16,5 m en 5,5 m diepte en de bijbehorende gebiedsbreedtes.
De veldafmetingen zijn instelbaar; 105 × 68 m is een zichtbare aanname die je moet
controleren. Punten buiten het fitgebied worden met de homography geprojecteerd,
in plaats van alle spelers buiten het aangeklikte rechthoekje te weigeren.
Punten achter de perspectiefhorizon en buiten de veldcoördinaten worden geweigerd.

De controle op begin, midden en einde tekent nu ook de geschatte veldgrenzen en
middenlijn. Zo kun je fouten buiten de vier fitpunten zien. Het wisselen van
gebied of afmetingen maakt eerdere kalibraties en resultaten ongeldig. De
bestaande review op een vaste camera blijft vereist; er is geen menselijke
goedkeuring door AI ingevuld.

## Controle met echte broadcastbeelden

Het script `scripts/check_partial_calibration.py` gebruikt bestaande providerlijnen
uit de 8.000-frameverzameling. Per clip en per kant wordt het eerste beeld met
alle benodigde lijnen en zes zichtbare snijpunten genomen, zonder selectie op
de uiteindelijke controlefout. De twee doelgebiedpunten blijven buiten de fit.

Van 230 clip/kant-combinaties hebben er 195 geen volledig zichtbaar zestal.
Van de 35 geschikte combinaties slagen 33; twee worden door de ongewijzigde
controlegrenzen geweigerd. De 33 geslaagde gevallen liggen in 17 trainings- en
16 validatiegevallen. Bij alle 33 vallen volledige veldhoeken buiten beeld:
de oorspronkelijke invoerroute kon daar dus geen vier zichtbare veldhoeken bieden.

De projecties van 448 provider-spelervoetpunten verschillen mediaan 0,42 m en
op het 90e percentiel 1,29 m van de providergrondposities, bij aangenomen
105 × 68 m. Dit is overeenkomst tussen providergegevens, geen onafhankelijk
gemeten menselijke positienauwkeurigheid. Het is ook geen detector-AP.
Menselijke visuele beoordeling en een vaste-camera-MVP-demonstratie blijven open.

Bewijs: `reports/partial-calibration-v3/summary.json`. Lokale controlebeelden staan
ernaast en worden niet als extra bronbeelden naar Git gekopieerd. Herhalen:

```powershell
$env:PYTHONPATH='src;.'
.\.venv\Scripts\python.exe scripts/check_partial_calibration.py --output reports/partial-calibration-repeat
```

De eerste twee controles zijn bewaard. De eerste selecteerde nog geen zichtbaar
zestal. De tweede weigerde ten onrechte wanneer ongeziene delen van het veld
achter de camera lagen. Die te strenge aanname is vervangen door controle van
de zichtbare zijde van de perspectiefhorizon. Dit is een gedocumenteerde
ontwikkeliteratie, geen vooraf blinde eindtest. Bronkopieën en hashes blijven
bij de bijbehorende rapporten bewaard.

## Baltraining met één gecontroleerd verschil

Twee nieuwe kandidaten starten allebei van v2 en gebruiken dezelfde beelden,
seed, optimizer, leertempo en augmentaties. Alleen `freeze` verschilt: tien
lagen vast of alle lagen bijleren. Beide hebben werkelijk 16 epochs uitgevoerd.
De vooraf opgeslagen selectie vereist hogere tegel-AP, minstens evenveel TP,
hoogstens evenveel ongekoppelde detecties en geen extra detecties op negatieve crops.

| Route op dezelfde ontwikkeldata | V2 | Freeze 10 | Freeze 0, gekozen |
|---|---:|---:|---:|
| 640-tegels: AP@50:95 | 23,34% | 23,96% | 25,74% |
| Gevonden labels vanaf 0,25 | 36 | 39 | 36 |
| Ongekoppelde detecties vanaf 0,25 | 12 | 11 | 5 |
| Volledig beeld 1280: AP@50:95 | 18,01% | 16,45% | 16,79% |

De kandidaat met alle lagen vrij heeft de hoogste tegel-AP en minder ongekoppelde
detecties, maar mist nog 37 van 73 labels. De crop- en volledige-beeldroutes
verbeteren niet op elk werkpunt. Daarom wordt v3 alleen met de gemeten tegelroute
aangeboden. De eenvoudige schoolbasis blijft P006 + F005 zonder tegels.

De data blijven AI-gecurateerd en de validatie is al eerder gebruikt. Er is geen
menselijke review of onafhankelijke eindtest ingevuld. Zie de volledige cijfers
in `reports/broadcast-data/v3-experiment.json` en de modelkaart in
`artifacts/broadcast-ball-v3/README.md`.

Start de eenvoudigere app met `scripts/Start-School.ps1`. Voeg `-BroadcastTiles`
toe voor de gekozen v3-baldetector. V2 blijft apart beschikbaar voor vergelijking.
De geselecteerde v2- en v3-gewichten worden via Git LFS bewaard; datasets,
volledige trainingsmappen en lokale uitvoervideo's blijven buiten Git.
