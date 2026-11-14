# Controle modelomschakeling — 14 november 2026

- Volledige bestaande testreeks, oorspronkelijke appomgeving: **546 geslaagd, 1 overgeslagen, 4 subtests geslaagd**. Bestaande Pillow-deprecatiewaarschuwingen blijven aanwezig.
- Afzonderlijke YOLO26-omgeving (Ultralytics 8.4.211, Torch 2.6.0 CPU): **24 geslaagde tests** voor modelimport, profielen, teams en tracking.
- Ruff-controle en opmaakcontrole slagen; codekaart actueel; alle 784 gecontroleerde functies hebben documentatie.
- `Start-Yolo11.ps1 -Device cpu -CheckOnly` laadt de echte detectie-, rol- en shirtmodellen succesvol. De originele spelerskopie heeft SHA-256 `fb6deea2d6c51bada9d3f8bfd666882212f45d1a1584547d02dc98aa59aaaa25`.
- De nieuwe YOLO26-runtime verwerkt een synthetisch beeld met het algemene YOLO26s-model en expliciet `nms=True`; de actieve backend heeft `end2end=False`. Dit is uitsluitend een technische controle van de bibliotheek en detectiekop, geen voetbalmeting.
- Starten zonder voetbalcheckpoint geeft import- en terugschakelinstructies. De import weigert het algemene COCO-model als vervanging voor het gespecialiseerde spelercheckpoint.

**Nog niet gecontroleerd:** volledige voetbalanalyse met Raouls getrainde YOLO26-gewichten, omdat zijn checkpoint ontbreekt. Ook de automatische veldruntime is niet op deze checkout geïnstalleerd; handmatige kalibratie blijft beschikbaar. Geen nieuwe training of nieuwe nauwkeurigheidsclaim.
