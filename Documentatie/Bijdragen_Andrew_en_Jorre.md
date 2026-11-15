# Bijdragen van Andrew en Jorre

Bijgewerkt op 15 november 2026, op basis van main `524d081a`.

## Andrew

De oorspronkelijke uitleg staat in [VierKlassenModel.md](../docs/VierKlassenModel.md). Hoofdstuk 16 bevat zijn eigen AI-verantwoording. De oorspronkelijke training staat in [train.ipynb](../Andrew_Prototype/train.ipynb); het prototype in [model_deployment.ipynb](../Andrew_Prototype/model_deployment.ipynb).

- Het trainingsnotebook begint bij YOLOv8x met vier klassen: ball, goalkeeper, player en referee. De ingestelde invoer is 1280, batch 6, maximaal 50 epochs en patience 20. De runnaam met '640' verandert die instelling niet.
- Het oorspronkelijke deploymentprototype toont bal en scheidsrechters. Het gebruikt bewegingsvoorspelling, snelheidsafhankelijke afstandskoppeling, smoothing 0,65 en maximaal tien voorspelde frames bij uitval. Greedy matching is geen gegarandeerd optimale associatie.
- De geïntegreerde broadcastpipeline gebruikt uitsluitend Andrews baluitvoer. De spelersdetector en gedeelde ByteTrack-route blijven afzonderlijke onderdelen.
- Andrew vermeldt AI-hulp voor documentstructuur, eerste codeonderdelen en debugging. Volgens zijn verklaring heeft hij voorstellen beoordeeld, aangepast en getest en blijft de verantwoordelijkheid bij hem. Toolnamen en model-ID's zijn niet gespecificeerd en zijn hier niet aangevuld.
- Hij noemt de publieke football-players-detection-1-verzameling als bron. De modelherkomst en technische inferentiecontrole staan in [de modelkaart](../artifacts/andrew-four-class-v1/README.md) en [provenance.json](../artifacts/andrew-four-class-v1/provenance.json).

Dit is een samenvatting van zijn aangeleverde verklaring, geen nieuwe onafhankelijke mAP-test of mondelinge beoordeling.

## Jorre

De technische afronding staat in [Afronding_20261114.md](../docs/Afronding_20261114.md), met [checks.json](../reports/release-20261114/checks.json).

- De gedeelde module-imports en Streamlit-tests zijn hersteld. Laptop instellen blijft het beginscherm; analysetests kiezen hun werkruimte expliciet.
- De gedeelde CPU-controle meldt 537 geslaagde tests, één overgeslagen GPU-proef en vier geslaagde subtests. Ruff, codekaart en functie-uitleg zijn gecontroleerd. Dit is geen nieuwe GPU-installatie- of nauwkeurigheidsproef.
- De menselijke review van alle huidige 80 labels is geregistreerd op basis van expliciete gebruikersbevestiging. Twijfelgevallen lagen buiten de selectie; beelden, labels en 48/32-splits zijn niet veranderd. De oorspronkelijke AI/provider-herkomst blijft vermeld.
- Het volledige [reviewverslag](../final/datasets/school-ball80-review-v1/REVIEW.md) benoemt de afspraken en grenzen. Er zijn geen individuele reviewernamen, aantallen meningsverschillen of specifieke correcties achteraf ingevuld.

## Gezamenlijke documentatie

Deze bijdragen zijn verwerkt in het [rapport](Rapport_Sports_Vision.pdf), de [presentatie](Presentatie_Sports_Vision.pptx), het [uitgevoerde notebook](Training_en_Resultaten.ipynb), de [GenAI-verantwoording](GenAI_en_Eigenaarschap.md) en de [requirementscontrole](Requirementscontrole.md). Overige persoonlijke bijdragen worden alleen op naam gezet wanneer daarvoor een werkelijke verklaring of bron bestaat.
