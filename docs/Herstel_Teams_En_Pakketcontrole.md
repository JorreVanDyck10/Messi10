# Teamherkenning en controle van `final`

Controle op 13 november 2026, tegenover hoofdcode `27097eb8`.
Deze controle gaat over de map **`final`**, niet over het oudere inleverpakket `Final2`.

## Wat ging er mis?

Er waren twee problemen die samen het vreemde beeld verklaren:

1. De teamcode gebruikte alleen spelers met een geldige veldprojectie. Als het veld niet gevonden werd, kregen de spelers geen shirtkenmerken en geen team. Hun vakjes en tracking-ID's konden wel zichtbaar zijn. Daardoor stond er overal **team onbekend**. Deze blokkade zat zowel in de hoofdcode als in `final`.
2. `final` was nog grotendeels de snapshot van 30 oktober. De standaardstart koos schoolmodus en latere verbeteringen voor zichtbare spelers bij ontbrekende veldkalibratie waren niet meegekomen.

Een team afleiden uit een shirt heeft geen veldcoordinaten nodig. Een speler op de minimap zetten of zijn afstand berekenen heeft die coordinaten wel nodig. De herstelcode maakt dat onderscheid nu ook.

De oorspronkelijke video en startopdracht zijn onbekend. De screenshot past bij deze fout, maar bewijst niet dat dit de enige oorzaak van de onbekende teams op dat specifieke fragment is.

## Wat is wel en niet meegekomen?

| Controle | Resultaat |
| --- | --- |
| Python-modules in `final/src/football_pipeline` voor het herstel | 70 modules: 57 met dezelfde uitvoerbare code als de hoofdmap, 13 verschillend |
| Na het gerichte herstel | 60 gelijk, 10 nog verschillend; commentaar, opmaak en docstrings tellen niet als codeverschil |
| Interne relatieve imports naar ontbrekende modules | Geen gevonden in de verpakte pipeline |
| Gewichten uit het school- en broadcastprofiel | Alle 7 verwijzingen aanwezig; SHA-256 komt overeen met het profiel; echte LFS-bestanden gedownload |
| Teaminstellingen en teamkern voor het herstel | Dezelfde code/instellingen als in de hoofdmap; er ontbrak geen apart teammodel |
| Modules alleen in de hoofdmap | 17, vooral latere veld-, trainings- en evaluatieonderdelen; zie het volledige JSON-overzicht |

De overgebleven verschillen zitten in resultatenweergave, automatische kalibratie, evaluatie/training, modelprofiel laden, veldleren, veldbeweging, pipeline, puntkiezer en trainingsbudget. `final` is dus nog steeds een afzonderlijk pakket en geen volledige kopie van de nieuwste hoofdmap. Een geslaagde import- en testcontrole bewijst niet dat alle mogelijkheden van de hoofdmap erin zitten.

De volledige bestandslijsten en modelcontrole staan in `reports/final-team-sync-audit.json` in de hoofdrepository en in het gerepareerde pakket. De hoofdrepository bevat `scripts/audit_final_sync.py` om de vergelijking opnieuw te maken:

```powershell
python scripts/audit_final_sync.py --output reports/final-team-sync-audit.json
```

## Wat is aangepast?

- In beide codeversies: shirtkenmerken, teamvoorbeelden en teamtoewijzing mogen ook bij `calibration_unavailable` werken voor gedetecteerde spelers.
- Personen worden zonder veldbewijs niet zomaar spelers. Bekend buiten het veld, ongeldige boxen en uitgesloten projecties krijgen geen extra toegang tot de teamherkenning.
- In `final`: de bestaande herstelcode uit de hoofdmap voor zichtbare spelers en framediagnostiek is overgenomen in `contracts.py`, `participants.py` en `render.py`.
- `Start-Final.ps1` start standaard broadcast. Schoolmodus blijft beschikbaar via `-Mode school`.
- De README, herkomstinformatie en pakketchecksums zijn bijgewerkt. Modelgewichten, teamdrempels en trainingsresultaten zijn niet veranderd.

Bij ontbrekende kalibratie mogen zichtbare spelers dus een shirtteam krijgen, maar veldtellingen en afstanden blijven onbekend en de minimap wordt niet gevuld met verzonnen posities.

## Hoe is dit gecontroleerd?

De nieuwe regressietests lieten voor het herstel drie fouten zien: geen shirtkenmerken, geen doorgifte naar de shirtmodule en geen beschikbare teamgroepen. Na het herstel slagen die controles.

| Controle | Resultaat |
| --- | --- |
| Gerichte hoofdcode-tests voor teams, rollen, zichtbaarheid, tracking, afstanden en geometrie | 109 geslaagd |
| Volledige verpakte testset van `final` | 202 geslaagd |
| Synthetische video met twee shirtkleuren, zonder veldkalibratie | 30 frames opnieuw ingelezen en geexporteerd; 180 teamtoewijzingen; veldtellingen blijven onbekend |
| Echte meegeleverde shirtgewichten op kunstmatige spelersuitsneden | Twee groepen A/B beschikbaar zonder veldprojectie |
| Echte broadcastdetector op vijf frames uit `examples/teamtrack_20s.mp4` | Shirtkenmerken worden nu berekend, maar te weinig spelersgroepen voor teams: `insufficient_groups` |

De laatste controle is bewust ook opgenomen. Het meegeleverde panoramische voorbeeld gaf maar een voorspelde speler per onderzocht frame. Het is daarmee geen bewijs dat de detector en teamindeling op iedere video goed werken. De kunstmatige test controleert de softwareketen, geen voetbalnauwkeurigheid. Er is geen nieuwe training of onafhankelijke kwaliteitsmeting uitgevoerd.

De controles zijn uitgevoerd met Python 3.12, Torch 2.10.0 CPU, Ultralytics 8.3.221 en FFmpeg, vanuit een afzonderlijke herstelcheckout. De volledige tests gebruiken de code uit `final` met een omgeving uit de bovenliggende map. Een schone installatie van de gedocumenteerde Python 3.11-omgeving en het externe automatische veldmodel is hierbij niet opnieuw uitgevoerd.

## Gebruiken

Gebruik de herstelbranch `codex/fix-teamherkenning`. Installeer bij een nieuwe checkout eerst de afhankelijkheden en het externe veldmodel volgens de README van `final`.

Vanuit `final`, op CPU:

```powershell
.\scripts\Start-Final.ps1 -Mode broadcast
```

Met een geschikte NVIDIA-installatie:

```powershell
.\scripts\Start-Final.ps1 -Mode broadcast -Device 0
```

Start een **nieuwe analyse**. Een al gemaakte resultaatvideo verandert niet vanzelf na een codewijziging. Te weinig duidelijke spelers, sterk gelijkende shirts, keepers of fouten van de detector kunnen nog altijd onbekende teams geven. Het herstel maakt shirtteams onafhankelijk van ontbrekende veldprojectie; het lost de automatische veldherkenning zelf niet op.
