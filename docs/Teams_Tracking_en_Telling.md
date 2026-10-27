# Onderdeel 3: teams, tracking, telling en toepassing

## Gebruik

De automatische uploadanalyse herkent nu ook twee shirtkleurgroepen. Zij verwerkt
eerst detectie, veldprojectie en tijdelijke speler-ID’s en maakt daarna de
definitieve video met dezelfde Team A/B-kleuren voor de hele clip. Het bestaande
spelermodel en de instellingen van het veldmodel blijven de invoer; het
experimentele veldprofiel wordt hierdoor niet geactiveerd.

Start zoals gebruikelijk met `scripts/Start-Spelermodel.ps1` en upload een MP4.
Bij handmatige analyse kun je **Teams op shirtkleur herkennen** uitschakelen.
Spelertracking houdt de bestaande voorwaarden: automatische cameracompensatie,
of bij handmatige kalibratie de bestaande MVP-acceptatie. Zonder tracking kan
de kleurmodule individuele detecties indelen, maar zijn er geen speler-ID’s om
handmatig te koppelen.

Na verwerking toont **Teams en telling** een exact bronframe met dezelfde
bounding boxes, teamkleuren, trajecten en tactical map als de uitvoer. De vier
getallen zijn totaal, Team A, Team B en onbekend. De framekiezer bestuurt deze
frameweergave; de videospeler heeft zijn eigen afspeeltijd. De grafiek laat het
verloop zien en verbindt geen intervallen over ontbrekende veldtellingen.

Met **Een opgeslagen teamanalyse openen** kun je een eerdere teamrun bekijken
zonder opnieuw te uploaden. De bestanden blijven beschikbaar via **Bestanden
en analysedetails**.

## Teamindeling corrigeren

Open **Teamindeling corrigeren**. Je kunt:

- Team A/B een naam en een goed leesbare weergavekleur geven.
- **Shirtprototype aanpassen** aanvinken en een nieuwe shirtkleur kiezen.
  De shirtkleur stuurt de indeling; de weergavekleur stuurt alleen de overlay.
- Een tijdelijke speler-ID aan Team A/B koppelen, expliciet onbekend maken,
  of met **Automatisch herstellen** de ID-correctie verwijderen.

Klik vervolgens op **Correcties toepassen**. Een ID-correctie geldt voor alle
waarnemingen van die track, ook vóór het gekozen frame. Het resultaat wordt in
een nieuwe runmap bewaard. Detectie, veldposities, bronrollen en track-ID’s
worden exact overgenomen; alleen teamlabels, tellingen en weergave veranderen.
Een volgende correctie gebruikt weer de oorspronkelijke analyse met de totale
opgeslagen correcties. De oorspronkelijke run wordt niet overschreven.

Correcties zijn gebonden aan de oorspronkelijke cache-identiteit en videohash.
Een speler-ID uit een andere video of trackingrun wordt niet geaccepteerd.
Correcties zijn gebruikersinstellingen; ze gelden niet als onafhankelijke
evaluatiereferenties. Een afgeleide teamweergave kan geen nieuwe oorspronkelijke
MVP-run vervangen.

## Werking en grenzen

`configs/teams.json` bevat versie 1 van `torso_lab_dominant_modes_v1`. De module
gebruikt alleen detecties met de echte rol `player`. De centrale uitsnede van
het bovenlichaam vermijdt hoofd, armen, broek en boxrand. Smalle stroken naast
de persoon schatten de lokale achtergrond. Groen wordt niet algemeen
verwijderd: een groen shirt kan dus een teamkleur zijn.

Kleuren worden in CIELAB gemeten. Te kleine boxes, te weinig voorgrond en een
te grote kleurspreiding leveren geen kleurwaarneming op. Een deterministische
steekproef van maximaal 2.048 waarnemingen, ongeveer vijf keer per seconde,
bestrijkt de clip. Getrackte spelers krijgen één robuuste mediaankleur, met
minimaal drie steekproefwaarnemingen. Vervolgens worden de twee dominante
compacte kleurgroepen gezocht. Iedere groep vereist minimaal twee leden en
drie verschillende bronframes. De afstandsgrenzen staan in het profiel; er
wordt geen nauwkeurigheid uit deze technische grenzen afgeleid.

De prototypes blijven voor de hele analyse vast. Afwijkende of onvoldoende
onderscheidbare kleuren blijven onbekend. Bij tracking bevestigen drie
opeenvolgende passende kleurwaarnemingen een team. Een bevestigd label wijzigt
pas na vijf passende waarnemingen voor het andere team. Eén afwijkende of
ontbrekende kleurwaarneming behoudt het tracklabel. De geschiedenis vervalt
na meer dan 1,2 seconde zonder actuele waarneming. Nieuwe track-ID’s bouwen
hun eigen geschiedenis op; de bestaande tracker vernieuwt ID’s bij
camerawissels en onbetrouwbare camerabeweging.

De bronbeelden kunnen perspectief, schaduw, gestreepte shirts, overlap en
detectorfouten bevatten. Een doelman heeft geen aparte rol in het huidige
spelermodel: een afwijkende shirtkleur wordt daarom niet op basis van positie
aan een team gekoppeld. Ook de twee dominante kleurgroepen kunnen bij
onrepresentatieve beelden een verkeerde interpretatie hebben. De app biedt
daarvoor prototype- en ID-correcties. Rugnummers, spelersnamen en identiteit
over camerawissels worden niet herkend.

## Telregels en interfaces

De bestaande telregels uit [Spelertelling en rollen](Spelertelling_en_Rollen.md)
blijven gelden. Alleen actuele, zichtbare spelerwaarnemingen met een geldig
voetpunt binnen het geldige veld tellen mee. Een werkelijk gematchte lage
confidencewaarneming blijft toegestaan. Officials en generieke personen worden
niet tot speler of team gepromoveerd. Voorspelde trackerposities tellen niet mee.

`player_summary.by_team` bevat `A`, `B` en `unknown`. Bij een beschikbaar
spelersaantal is hun som gelijk aan `player_summary.on_field`. Bij ontbrekende
veldkalibratie of een model zonder spelerklasse zijn alle drie waarden `null`.
Een geldig leeg frame bevat numeriek `{"A": 0, "B": 0, "unknown": 0}`.

Een detectie bevat aanvullend:

| Veld | Betekenis |
|---|---|
| `shirt_color_lab` | Gemeten CIELAB-kleur, of `null` |
| `team_id` | `A`, `B` of `null` |
| `team_status` | `assigned`, `unknown` of `not_player` |
| `team_match_score` | Maximaal 1; kleurafstand tot het toegewezen team, anders de dichtstbijzijnde groep; of `null` |
| `team_source` | `automatic`, `track_history`, `manual` of `null` |

De kleurmatchscore is `max(0, 1 - afstand / max_match_distance)` en is geen
gekalibreerde waarschijnlijkheid. Een handmatige ID-koppeling krijgt geen
verzonnen kleurmatchscore. `FrameRecord.team_context` bewaart de teamnamen,
weergavekleuren en technische modelstatus voor het betreffende resultaat.
Oudere records zonder deze velden blijven leesbaar. Detectiereplay neemt
afgeleide teamlabels niet als detectorinvoer over.

Extra bestanden per teamrun:

- `teaminstellingen.json`: profiel, prototypes, teamnamen, overlaykleuren en status.
- `teamcorrecties.json`: oorspronkelijke run, videohash, teamwijzigingen en ID-koppelingen.
- `teamtelling.csv`: één regel per bronframe met tijd, status, totaal en teamaantallen.

Ontbrekende tellingen zijn lege CSV-cellen. Bestanden worden gehasht in het
runmanifest. De teaminstellingen en correcties veranderen de cache-identiteit.
Afgebroken correcties krijgen een mislukte runmap; de oorspronkelijke uitvoer
blijft bestaan. De oorspronkelijke ongewijzigde video blijft nodig voor
opnieuw renderen en exacte framecontrole.

De Python-interface voegt het optionele argument
`process_video(..., team_config_path=...)` toe. Bestaande aanroepen zonder dit
argument behouden hun verwerking zonder teamanalyse. De CLI biedt `--teams`:

```powershell
.\.venv\Scripts\python.exe -m football_pipeline process data\clip.mp4 --auto-field --source "Eigen clip" --usage "Lokale analyse" --models configs\models-players.json --tracker configs\bytetrack.yaml --teams configs\teams.json
```

Voor programmatische correcties:

```python
from pathlib import Path
from football_pipeline.contracts import read_json
from football_pipeline.team_results import apply_team_corrections

run = Path("runs/gekozen_run")
correcties = read_json(run / "teamcorrecties.json")
correcties["track_overrides"]["17"] = "A"  # Alleen een werkelijk aanwezige speler-ID.
resultaat = apply_team_corrections(run, correcties, Path("runs"))
```

## Controle en bewijs

De tests gebruiken synthetische kleurbeelden, echte ByteTrack-matching, echte
video-encoding en Streamlit AppTest. Ze controleren indeling, onbekende kleuren,
labelstabiliteit, telregels, correcties, cachegedrag, oudere uitvoer en
ontbrekende intervallen in de grafiek. De synthetische trackingproef stubt
expliciet de menselijke acceptatiegrens en geldt niet als MVP-acceptatie.

Het herhaalbare script `scripts/check_team_integration.py` verwerkt een echte
clip met bestaande automatische veldwaarnemingen, het echte spelermodel en
cameragecompenseerde tracking. Het vergelijkt CSV en JSONL per frame en
controleert uitvoerformaat, teamtotalen en onbekende tellingen. Resultaten,
gemeten runtime en beperkingen staan in
[het technische rapport](../reports/team-analysis/README.md).

Menselijke teamreferenties en trackingreferenties ontbreken. De technische
controle bewijst geen teamnauwkeurigheid, tellingnauwkeurigheid of correcte
persoonlijke identiteit.
