# Overdracht aan persoon 2

`person-ball-val-1920.jsonl` bevat twaalf echte bronmomenten: frames 2100–2225 en 2450–2575, telkens met stappen van 25 frames. Het bronbestand staat via Git LFS in `assets/videos/HBTFZwMdcCw.mp4`.

- Frame-index: nulgebaseerd in de bronvideo. Tijd: oorspronkelijke presentatietijd in seconden.
- Beeld: 3840 × 960. Boxen: `x1,y1,x2,y2` in oorspronkelijke bronpixels.
- Klassebetekenis: `person` is een generieke mens; `ball` is de experimentele baldetector. Een class-ID is lokaal aan het genoemde model. `dataset_class_id` gebruikt hier 0 voor person en 1 voor ball.
- Werkpunt: confidence 0,25. Er zijn 135 persoonsvoorspellingen; dat zijn geen gemeten true positives.
- De baldetector heeft geen validatiewinst en is niet gepromoveerd. `ball-val-empty-output.jsonl` bewaart alle twaalf lege balrecords. De referentielabels bevatten wel een zichtbare bal: leeg betekent hier een detectorfout, geen negatief bronbeeld.
- Voorbeeld normaal bronmoment: frame 2100 op 84 s. Moeilijk bronmoment: frame 2525 op 101 s. Het balrecord van frame 2100 demonstreert lege uitvoer.

Beide stromen zijn gecontroleerd op precies dezelfde video-identiteit, frame-ID, index, tijd en afmetingen. Model- en configuratieherkomst staan in `person-run.json` en `ball-run.json`. Deze gegevens zijn invoer voor veldprojectie en synchronisatie; ze bewijzen nog geen werkende tactical map of tracking.
