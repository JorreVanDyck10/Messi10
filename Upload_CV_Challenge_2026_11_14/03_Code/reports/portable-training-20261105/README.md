# Frontendtraining en overdracht — 5 november 2026

Acht trainingsknoppen en een gezamenlijke wachtrij zijn beschikbaar: spelers,
bal, rollen, shirt, context, veldpunten, veldlijnen en Andrews vierklassendetector.
Iedere laptop start zijn eigen app en gebruikt zijn lokale GPU. Kandidaten
vervangen de bestaande analysegewichten niet automatisch.

- **Data:** 16.656 catalogusbestanden, 5.377.081.341 bytes, alle SHA-256-controles
  geslaagd. 1.626 bestaande bestanden worden hergebruikt; de overige 15.030
  bestanden zijn toegevoegd. Bestaande bijdragen en `final` zijn behouden.
- **GitHub:** LFS-upload geslaagd. Een volledig aparte HTTP-clone heeft de
  payloads opnieuw gedownload en alle catalogushashes gecontroleerd. De drie
  YOLO-recepten, 176 veldframes en de modelpaden werken vanuit die nieuwe map.
  Zie [bewijs](remote-checkout.json) en [catalogusaudit](github-training-data.json).
- **Frontend:** via de echte hoofdpagina en knoppen zijn een shirttraining en
  een Andrew-training gestart en afgerond op de 4050. Instellingen: maximaal
  één epoch en één minuut optimizerbudget. De Andrew-ronde duurde inclusief
  voorbereiding, validatie en opslag 222,55 seconden en is als `time_limited`
  geregistreerd; de laatste epoch kan gedeeltelijk zijn. De oorspronkelijke
  `best.pt` bleef ongewijzigd. Dit zijn technische proeven, geen betere modellen.
- **Controles:** de lokale volledige suite slaagde met 504 tests en vier
  subtests. Daarna slaagde een extra overdrachtsproef; de vier Andrew-tests
  slagen samen. GitHub Actions is geslaagd voor commit
  `88421dd1cea3f2e1a37342993017f875c19350e8` (inclusief de extra proef).
  Ruff en formatter zijn geslaagd.
- **Andrews data:** 612 train-, 38 validatie- en 13 uitgesloten testbeelden.
  Bronframefamilies zijn gescheiden, volledige wedstrijdscheiding is niet
  aangetoond. De gezamenlijke app gebruikt zijn bestaande tracking; de
  notebookextrapolatie is niet overgenomen.

Een fysieke tweede laptop/RTX 5070 is nog niet getest. De schone projectmap
bewijst de bestandsoverdracht en verwijzingen; de laptopinstallatie bouwt de
omgevingen ter plaatse en voert een echte CUDA-controle uit. Nieuwe veld- en
modelgewichten vereisen beoordeling op onafhankelijke beelden voordat ze als
standaard in aanmerking komen.

[Installatie en bediening](../../docs/Trainen_op_Andere_Laptop.md).
