# Controle van de uitlegbranch

## Aanvulling: uitleg bij iedere functie

De aanvulling vanaf commit `0773fbc` is eveneens op 29 oktober 2026 gecontroleerd:

- **618 van 618 benoemde Python-functies** hebben een niet-lege docstring, verdeeld
  over 168 actuele bronbestanden. Daarvan zijn 516 ontbrekende functiebeschrijvingen
  toegevoegd; 102 aanwezige beschrijvingen zijn behouden, inclusief de vier functies
  van de nieuwe controletool.
- De scope omvat `src`, `persoon1`, `scripts`, de datasethelpers onder
  `assets/annotations` en `streamlit_app.py`, inclusief methoden en geneste callbacks.
  Tests en historische bronkopieën vallen buiten deze productiedekking.
- De enige benoemde PowerShell-functie heeft ook comment-based help gekregen.
- **158 gewijzigde bestaande Python-bestanden** hebben exact dezelfde AST zodra
  docstrings worden weggelaten. Deze aanvulling wijzigt geen uitvoerbare Python.
- De volledige testreeks slaagt opnieuw: **422 tests en 4 subtests**, 49,78 seconden.
  Dezelfde 48 bestaande Pillow-deprecationwaarschuwingen blijven zichtbaar.
- Ruff-checks slagen; 163 bestanden vallen binnen de bestaande formatteringsscope.
  De codekaart bevat nu 296 codebestanden en is actueel.

Reproduceren: `python scripts/check_function_docs.py`. Optioneel schrijft
`--report pad/naar/rapport.json` dezelfde dekking als JSON weg. De CI controleert
de aanwezigheid voortaan bij iedere run. Aanwezigheidscontrole vervangt geen
inhoudelijke review van de uitleg of beheersing van de code door de studenten.

## Eerste controle van de leesgids

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
