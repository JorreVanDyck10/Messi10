# Spelerdetector v3

Geselecteerd experiment: **EXP-P006**, 19 oktober 2026. Startpunt: pretrained YOLO11n. De training gebruikt 60 publieke SN-GSR-2024-beelden uit drie wedstrijden; validatie gebruikt 20 beelden uit drie andere wedstrijden. De bronselectie bevat in totaal 80 frames. Test- en challengebeelden zijn niet geopend.

## Metingen op de nieuwe validatieset

| Model, invoer | Spelers AP@50 | Spelers AP@50:95 | Spelers recall bij 0,25 | Officials AP@50 |
|---|---:|---:|---:|---:|
| Oud TeamTrack-model, 1280 | 1,61% | 0,22% | 1,71% | 0,03% |
| EXP-P005, 1280, zonder augmentatie | 89,07% | 55,26% | 86,30% | 29,29% |
| EXP-P006, 1280, met augmentatie | 93,17% | 58,98% | 91,78% | 31,93% |

De oude productie-instelling 1920 is ook gemeten en presteert op deze nieuwe beelden nog slechter. Deze vergelijking is niet de oorspronkelijke TeamTrack-panorama-evaluatie.

De nieuwe spelerprecision bij confidence 0,25 en IoU 0,5 is 80,48%: 268 TP, 65 FP en 24 FN. AP@50 is dus geen percentage correct geclassificeerde boxen. Officials blijven zwak: 10 TP, 16 FP en 16 FN op 26 referentieboxen.

Voor alle drie positief geannoteerde klassen samen bedraagt mAP@50 41,70% en mAP@50:95 25,14%. De bal behaalde geen validatie-AP. Het applicatieprofiel biedt daarom uitsluitend `player` en `referee` aan. De ongebruikte `person`-uitvoerkop heeft geen positieve voorbeelden in deze selectie en wordt evenmin aangeboden. Er is geen herkenning van namen of teams.

## Identiteit en beperkingen

- Gewichten: `players_best.pt`.
- SHA-256: `beecb2439ca3329816df75e28c247236dfd7b283e66db72168139a1d28891aee`.
- Profiel: `configs/models-players-v3.json`, invoer 1280, confidence 0,10, NMS-IoU 0,70. ByteTrack ontvangt daardoor ook lage kandidaten voor de tweede associatiestap; nieuwe tracks starten pas bij 0,25. De gerapporteerde detectieprecision/recall is op 0,25 gemeten en geldt niet rechtstreeks voor alle getoonde boxen vanaf 0,10.
- Resultaten en selectie: `reports/course-improvement/`.
- Volledige trainingslogs, curves en checkpoints: `artifacts/course-improvement-20261019/players/`.
- Bron: [SN-GSR-2024](https://huggingface.co/datasets/SoccerNet/SN-GSR-2024), revisie `3cc710eb6d53a23350a3d2863311c1c0a2e645d7`, annotatieversie 1.3.

De selectie gebruikt gepubliceerde providerannotaties. De menselijke teamreview en een onafhankelijke eindtest blijven open. De 20 validatiebeelden dienen voor modelselectie en bewijzen geen universele nauwkeurigheid op andere wedstrijden. `vergelijking-ontwikkelbeeld.jpg` is een visuele controle op de bestaande ontwikkelclip; het aantal getekende boxen is geen extra nauwkeurigheidsscore.
