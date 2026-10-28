# Broadcastcorpus — 27 oktober 2026

Vervolg op 28 oktober: `v2-summary.json` bevat de minder redundante spelerselectie,
native balcrops met gecontroleerde negatieve voorbeelden en de werkelijk
uitgevoerde baltraining. `v2-experiment.json` vergelijkt voor/na op identieke
invoer. Zie [Broadcast v2](../../docs/Broadcast_V2_Training.md) voor resultaten
en de optionele modelprofielen. De eerdere datarondes hieronder blijven als
herkomst bewaard.

De bron is [SoccerNet SN-GSR-2024](https://huggingface.co/datasets/SoccerNet/SN-GSR-2024),
revisie `3cc710eb6d53a23350a3d2863311c1c0a2e645d7`, annotaties v1.3.

Er zijn 8.000 volledige 1080p-beelden uit 115 clips van zes wedstrijden
verzameld: 6.000 train, 2.000 validatie. De volledige audit decodeert alle
beelden, controleert hashes en YOLO-boxen en vindt nul exacte duplicaten en
nul wedstrijden die beide splits delen. Inmiddels slagen 48 gerichte softwaretests.

| Bronklasse | Train | Validatie |
|---|---:|---:|
| Speler, inclusief doelman | 88.336 | 29.676 |
| Official | 8.634 | 2.851 |
| Bal | 5.748 | 1.878 |
| Overige persoon | 202 | 18 |

Voor de actieve speler-/officialtaak gebruik je `data-players.yaml`;
`data-participants.yaml` houdt doelmannen apart. Beide trainen expliciet alleen
deelnemers en gebruiken geen bal als klasse. De oorspronkelijke labels met
ballen blijven voor review bewaard. De visuele AI-steekproef van 24 beelden
vindt onder meer verschoven balboxen bij `SNGS-071_000371` en
`SNGS-097_000376`; de bronlabels zijn dus niet universeel correct verklaard.

Van de veldlabels voldoen er 7.958 aan het bestaande preprocessingbeleid:
5.977 train en 1.981 validatie. Er zijn 42 expliciete uitsluitingen wegens
te grote overschrijdingen van de beeldrand.

De validatiewedstrijden zijn al bij eerdere modelontwikkeling gebruikt.
Test- en challengearchieven blijven ongeopend. Dit vergroot vooral de
temporele dekking van dezelfde zes wedstrijden; het is geen nieuwe
onafhankelijke eindtest. Er is geen model getraind, vervangen of als beter
gepresenteerd. Menselijke labelreview blijft open.

Grote bestanden, alle bronannotaties, volledige manifests, contactbladen,
baluitvergrotingen en de bewerkbare reviewkopie staan lokaal onder
`data/broadcast-sngsr-v1/`. De downloadlogs blijven lokaal onder `reports/`.
`summary.json` bevat de datasetidentiteit en compacte meetresultaten;
`software-tests.xml` bevat de echte testuitvoer.

Zie [gebruik en reproduceerbare opdrachten](../../docs/Broadcast_Trainingsdata.md).

## Vervolg: labelcuratie en aanvullende officialbeelden

`follow-up-summary.json` bewaart de uitgevoerde eindcontroles en hashes.
De balreview selecteert 132 positieve beelden uit 232 gecontroleerde
voorbeelden: 130 behouden bronboxen, twee gecorrigeerde boxen en 100
uitsluitingen. Er zijn 59 train- en 73 validatiebeelden, met dezelfde
gescheiden wedstrijden als het hoofdcorpus. Dit is een kleine AI-selectie,
geen menselijke goedkeuring of volledige balbenchmark.

De aanvullende [Infactory-bron](https://huggingface.co/datasets/infactory-ai/referee-tracking)
levert 1.450 beelden met providerlabels. Credit: Valentino Constantinou,
Mehdi Iranmanesh en John Kanalakis, Infactory; licentie CC BY-NC 4.0.
Na een AI-steekproef van drie beelden per bronclip worden twee clips met
70 twijfelachtige beelden afgezonderd. Er blijven 1.380 beelden over:
1.115 train, 265 validatie; 761 positief met 915 officialboxen en 619
expliciet negatieve beelden. De splits scheiden bronclips, maar de
geanonimiseerde wedstrijdidentiteit is niet bewezen. Gebruik deze export
voor een afzonderlijke officialtaak en meng de onvolledige spelerlabels
niet in het hoofdcorpus.

De bronbeelden zijn samen 9.450 unieke bestanden; de aanbevolen selecties
gebruiken er samen 9.380. De balset is een subset van het hoofdcorpus.
`ball-review-decisions.json`, `ball-corrections.json` en
`referee-review-decisions.json` leggen de AI-beslissingen vast. De oorspronkelijke
labels blijven bewaard en menselijke reviewstatussen blijven open.
