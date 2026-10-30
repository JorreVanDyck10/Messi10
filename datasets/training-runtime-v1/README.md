# Gedeelde trainingsinvoer voor de app

`manifest.json` beschrijft de 15.324 bestanden die de zeven trainingsknoppen
nodig hebben: beelden, labels, oorspronkelijke providerannotaties, rol-/shirtfeatures,
de veldindex en startgewichten. Het is een catalogus van bestaande paden;
beelden die al bij andere bijdragen stonden worden hergebruikt.

299 bestanden stonden al in Git. De overige 15.025 bestanden zijn toegevoegd
op hun bestaande projectpaden. Afbeeldingen, gecomprimeerde annotaties en het
featurecheckpoint gebruiken Git LFS. Labels en manifests blijven als gewone
Git-bestanden leesbaar. De oorspronkelijke bytes blijven behouden vanwege
hun SHA-256-controles.

## Na clonen

```powershell
git lfs install
git lfs pull
powershell -ExecutionPolicy Bypass -File scripts/Setup-Laptop.ps1
powershell -ExecutionPolicy Bypass -File scripts/Start-Laptop.ps1
```

De laptopinstallatie haalt de benodigde LFS-objecten ook zelf op en controleert
alle bestanden. Er is geen apart ZIP-bestand van een andere laptop nodig.
Je kunt de controle afzonderlijk herhalen:

```powershell
.venv/Scripts/python.exe -m football_pipeline.repository_training prepare
```

De manifesten kunnen nog de oorspronkelijke bronroot `C:/Messi10` noemen.
De voorbereidingsstap bewaart die herkomst en koppelt trainingsjobs expliciet
aan de eigen checkout. De originele labels worden daarbij niet herschreven.

## Welke data?

- Spelers: de bestaande broadcast-/SportsMOT-combinatie onder
  `data/broadcast-multisource-v1`.
- Bal: de voorbereide beelden en labels onder
  `data/joint-local-20261027-v2/ball`.
- Rollen en shirt: features met hun opgeslagen encoder en alle oorspronkelijke
  beeldreferenties; bestaande bijdragen onder `assets/annotations` en `datasets`
  blijven behouden.
- Context: broadcastbeelden, persoonslabels en providerannotaties onder
  `data/broadcast-pitch-v1`.
- Veld: 128 train- en 48 validatiebeelden uit verschillende wedstrijden,
  met hun oorspronkelijke veldlabels en de vastgezette veldindex.

De volledige corpuscaches, uploads, uitvoervideo's en mislukte experimenten
zijn niet nodig voor deze trainingsconfiguratie en blijven lokaal. Het gehele
project bevat daarnaast meer bestaande datasets van andere bijdragers; deze
catalogus verwijdert of vervangt die niet.

Providerlabels en bestaande AI-curatie zijn geen menselijke eindacceptatie.
Reviewstatus, train-/validatiesplits en beperkingen blijven in de bronmanifesten
en de [trainingshandleiding](../../docs/Trainen_op_Andere_Laptop.md) staan.
