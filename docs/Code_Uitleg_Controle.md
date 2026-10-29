# Controle van de uitlegbranch

Uitgevoerd op 29 oktober 2026, vanaf basiscommit
`4a3f9e5` op branch `codex/code-uitleg-verdediging`.

| Controle | Resultaat |
| --- | --- |
| Volledige `pytest -q`-reeks | 422 tests en 4 subtests geslaagd, 67,41 seconden |
| `ruff check src streamlit_app.py scripts tests` | Geslaagd |
| `ruff format --check src streamlit_app.py scripts tests` | Geslaagd, 162 bestanden binnen de bestaande formatteringsscope |
| `python scripts/build_code_guide.py --check` | Geslaagd, 295 codebestanden opgenomen |
| Lokale verwijzingen in de twee nieuwe leesdocumenten | Alle doelen bestaan |
| AST-vergelijking van 88 bestaande Python-modules | Alleen docstrings/commentaar en de hieronder genoemde vereenvoudiging |
| Historische bronkopieën onder `reports` | Ongewijzigd |

De enige wijziging van uitvoerbare bestaande Python is het samenvoegen van twee
identieke opeenvolgende guards rond de appearanceclassificatie in
`UltralyticsDetector.detect`. Eerst worden persoonsvoorstellen samengevoegd,
daarna volgt classificatie, onder dezelfde voorwaarde als voorheen. De bestaande
tests voor detectie, rollen, app, teams en integratie zijn onderdeel van de reeks.

De controleomgeving is apart onder de genegeerde map `output/code-uitleg` gebouwd
met Python 3.11.0, de projectdependencies en developmenttools uit `pyproject.toml`,
plus expliciet `torch 2.6.0+cpu`, `torchvision 0.21.0+cpu` en
`ultralytics 8.3.221`. Belangrijke overige versies: Streamlit 1.64.0,
OpenCV 4.14.0.94, NumPy 2.4.6, pytest 9.2.0 en Ruff 0.17.3.
Dit is geen claim dat exact `requirements.lock` is geïnstalleerd.

De testreeks meldt 48 bestaande deprecationwaarschuwingen voor Pillow `getdata`
in `persoon1/core.py`; geen test faalt hierdoor. Er is geen nieuwe modeltraining,
GPU-prestatiemeting of menselijke beoordeling van labels of herkenningskwaliteit
uitgevoerd voor deze documentatiewijziging.

De codekaart wordt uit brontekst opgebouwd met Python AST, zonder modules te
importeren. Zo start documenteren geen training of datasetbewerking. De CI-workflow
controleert voortaan ook of die kaart actueel is; voer na nieuwe codebestanden of
wijzigingen aan de beschreven functies `python scripts/build_code_guide.py` uit.
