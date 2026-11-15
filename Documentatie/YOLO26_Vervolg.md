# YOLO26 - behouden keuze en resterend bewijs

De [opgehaalde vergelijking](../docs/Yolo26_Spelersvergelijking.md) behoudt het bestaande YOLO11s-spelermodel: gerapporteerde gemiddelde pipeline-F1 91,81%, tegenover 91,62% voor opnieuw getraind YOLO11s en 91,45% voor YOLO26s. De gemeten detectorstacktijden zijn 250,81, 251,18 en 252,67 ms.

Deze cijfers komen uit de gedeelde handleiding; de ruwe lokale experimentmap is niet meegecommit. Het zijn ontwikkelmetingen met één seed, geen onafhankelijke eindtest. Detectorstacktijd omvat niet decoding, rol/team of het veldnetwerk en is geen volledige video-FPS. Nieuwe exacte AP-getallen worden niet ingevuld zonder bron.

Nog te delen: comparison.json, afzonderlijke evaluaties met beide AP-maten, oorspronkelijke args.yaml/results.csv, gewichten/hashes, hardwarebewijs en concrete verbeterde én verslechterde gevallen. De registratie van menselijke review van de 80 beelden verandert deze eerdere validatie niet in nieuwe testdata.
