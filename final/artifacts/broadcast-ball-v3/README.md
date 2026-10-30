# Broadcastbal v3

Optionele baldetector voor de bestaande 640-pixeltegelroute. Niet gebruiken als
bewezen verbetering op volledige beelden. De eenvoudige schoolbasis blijft F005.

- Gewichten: `broadcast_ball_v3.pt`, via Git LFS.
- SHA-256: `97c314c3ec62c072ff700cb2fe682f13806e3c9b59acd9c0c98077a2c7c22058`.
- Werkelijk getraind: twee kandidaten, elk 16 epochs vanaf dezelfde v2-gewichten;
  uitsluitend het aantal vastgezette lagen verschilt tussen de kandidaten: 10 of 0.
- Gemeenschappelijk: Adam, basisleertempo 0,0001, batch 4, invoer 640, seed 42,
  warmup 1 epoch met `warmup_bias_lr=0`, beperkte kleurvariatie en spiegeling.
- De kandidaat met 0 vastgezette lagen is volgens de vooraf beschreven selectie gekozen.

Op dezelfde 73 ontwikkelbeelden met dezelfde 640-tegels stijgt AP@50:95 van
23,34% (v2) naar 25,74%. Bij confidence 0,25 en matching-IoU 0,5: TP 36 → 36,
ongekoppeld 12 → 5, FN 37 → 37. Precision wordt 87,80%; recall blijft 49,32%.

De andere kandidaat vindt 39 labels met 11 ongekoppelde voorspellingen en haalt
AP@50:95 23,96%. De gekozen kandidaat heeft de hoogste tegel-AP en minder
ongekoppelde voorspellingen, maar niet de hoogste recall van de twee kandidaten.

Zonder tegels verslechtert de gekozen kandidaat: AP@50:95 18,01% → 16,79%,
TP 22 → 19. Op positieve validatiecrops stijgt het aantal ongekoppelde voorspellingen
van 2 naar 4; op de 12 gecontroleerde negatieve crops blijven beide op nul.
Er wordt geen verbetering op alle routes beweerd.

De 197 trainingscrops en 85 validatiecrops komen uit 132 bestaande bronbeelden.
Wedstrijden blijven gescheiden. Kleine, eerder gebruikte ontwikkelvalidatie,
AI-curatie, geen menselijke labelgoedkeuring en geen onafhankelijke eindtest.
Extra fysieke ballen op volledige beelden kunnen ongelabeld zijn.

Protocol, resultaten en bronkopieën: `reports/broadcast-data/v3-experiment.json`
en `reports/broadcast-data/v3-source/`. De volledige lokale trainingslogs staan
onder `artifacts/broadcast-ball-v3/`; die grote werkmappen gaan niet mee in Git.
Herhalen: `scripts/experiment_broadcast_v3.py --output artifacts/broadcast-ball-v3-repeat`.

Start: `scripts/Start-School.ps1 -BroadcastTiles`. Alleen de expliciete COCO-klasse
32 `sports ball` wordt aangeboden; andere uitvoerklassen zijn niet gevalideerd.
