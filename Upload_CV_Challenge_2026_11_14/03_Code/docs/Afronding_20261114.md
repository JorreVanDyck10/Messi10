# Technische afronding en labelreview - 14 november 2026

Deze wijziging vertrekt van main na de merge van AN-Laptop-ver (a2c89e37).

## Herstel van de toepassing en controles

De Streamlit-app importeert de gedeelde modules consequent via `football_pipeline`, hetzelfde pakket als CLI en tests. Daardoor worden geen tweede modulekopieÃ«n geladen via `src.football_pipeline`; verwerking, callbacks en testmocks gebruiken dezelfde functies en classes.

Laptop instellen blijft het beginscherm. De navigatietest controleert dit scherm en schakelt vervolgens naar Nieuwe analyse. De overige analysetests kiezen vooraf expliciet hun werkruimte. Bestaande asserts voor verwerking, klikcoÃ¶rdinaten, automatische kalibratie, fouten/retries en schoolmodus blijven actief.

De imports en opmaak zijn hersteld, vijf ontbrekende functie-uitlegteksten zijn aangevuld en de codekaart is opnieuw gegenereerd.

## Uitgevoerde verificatie

- Volledige hoofdsuite: **537 passed, 1 skipped, 4 subtests passed**. De skip betreft uitsluitend de echte CUDA/GPU-proef op deze CPU-laptop.
- Ruff check en Ruff format: geslaagd; 230 bestanden voldoen aan de opmaakcontrole.
- Functie-uitleg: 784 functies gecontroleerd; geen ontbrekende docstrings.
- Codekaart: actueel en gecontroleerd met --check.
- Trainingscatalogus: 16.656 bestanden en 5.377.081.920 bytes gecontroleerd met check-git; LFS-pointerhashes toegestaan.
- Doctor: FFmpeg, ffprobe en Python-dependencies beschikbaar.
- Eindpakket: 360 bestanden en alle 80 beeld-/labelparen geverifieerd; geen overlap van trainings- en validatiegroepen.

De machineleesbare registratie staat in [checks.json](../reports/release-20261114/checks.json). De tests zijn uitgevoerd op de bestaande Windows/Python 3.12 CPU-omgeving; dit is geen nieuwe CUDA-installatieproef of nieuwe nauwkeurigheidsbenchmark.

## Labelreview

Volgens de expliciete bevestiging van de gebruiker heeft het team alle huidige 80 labels gecontroleerd en goedgekeurd. Twijfelgevallen vielen buiten deze selectie. AI/provider-herkomst blijft behouden, net als 48 trainingsbeelden en 32 validatiebeelden. De labelbestanden zelf zijn niet gewijzigd. Zie [reviewverslag](../final/datasets/school-ball80-review-v1/REVIEW.md).

Deze review geldt niet automatisch voor andere historische datasets. Ze verandert geen historische trainingsresultaten en maakt de selectie niet tot onafhankelijke eindtest.

## Modellen en grenzen

De modelgewichten en herkenningsdrempels zijn met deze technische afronding niet gewijzigd. De beschikbare profielen behouden hun eigen modelkeuze. Het broadcastprofiel gebruikt alleen de baluitvoer uit Andrews vierklassige YOLOv8x; het YOLO11-spelermodel is een afzonderlijke detector. Trainingsscores horen bij de betreffende gewichten en dataset, niet bij alle profielen gezamenlijk.

De zelfstandige mondelinge verdediging blijft de verantwoordelijkheid van het team. Deze technische controle registreert geen presentatie, onafhankelijke modelvalidatie of nieuwe review van andere datasets.
