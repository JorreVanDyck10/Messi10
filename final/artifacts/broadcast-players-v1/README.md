# Broadcastspelers v1

Geselecteerd: `multisource-m`. Spelerprecision 92.07%, recall 91.04%; teamaccuracy onder toegewezen gematchte spelers 97.05%, teamdekking onder gematchte spelers 93.79%.

Dit zijn ontwikkelmetingen op aparte SoccerNet-GSR-wedstrijden met referentiegeometrie; geen onafhankelijke eindtest en geen score voor automatische veldherkenning. Keepers blijven speler, maar een onzekere teamkoppeling blijft onbekend. Personen buiten het geldige veld worden niet als speler geanalyseerd of getoond.

Start met `scripts/Start-Gezamenlijk.ps1` of `scripts/Start-Spelermodel.ps1 -Recognition broadcast`. Modelgewichten worden via Git LFS geleverd. Zie `reports/broadcast-pitch-v1/summary.json` voor splits, hashes, kandidaatsvergelijking en werkelijk trainingsbudget.

Alle streefgrenzen gehaald: **False**. De validatieset is gebruikt voor checkpoint- en drempelselectie; deze cijfers zijn geen onafhankelijke generalisatietest.

Bronnen: [SoccerNet-GSR](https://www.soccer-net.org/tasks/game-state-reconstruction), [SN-GSR-2024](https://huggingface.co/datasets/SoccerNet/SN-GSR-2024), [SportsMOT](https://huggingface.co/datasets/MCG-NJU/SportsMOT) (officiële voetbal-trainselectie, CC-BY-NC-4.0; zie trainingsrecords voor het gekozen model), [Ultralytics YOLO11](https://docs.ultralytics.com/models/yolo11/). De oorspronkelijke gebruiksvoorwaarden blijven van toepassing.
