# Broadcastspelers en teams — 2026-10-28

Spelers worden binnen het bestaande veld geselecteerd. De rolclassifier kan betrouwbare spelerlabels beschermen; officials blijven afzonderlijke rollen. Buitenveldse personen zijn uitgesteld.

## Vergelijking

Deze ontwikkelmeting gebruikt vaste validatiewedstrijden en referentiegeometrie uit providerannotaties. Ze meet detectie, rollen en teamgroepering samen, maar geen automatische veldnauwkeurigheid. Per clip is slechts één vaste A/B-omwisseling toegestaan.

| Kandidaat | Spelerprecision | Recall | Team correct/toegewezen | Teamdekking gematcht | Correct team/alle spelers |
|---|---:|---:|---:|---:|---:|
| r007-baseline | 87.31% | 37.40% | 93.31% | 33.07% | 11.54% |
| previous-m | 91.88% | 90.41% | 96.94% | 93.84% | 82.24% |
| multisource-m | 92.07% | 91.04% | 97.05% | 93.79% | 82.87% |
| multisource-s | 92.14% | 91.16% | 97.00% | 93.58% | 82.75% |

Geselecteerd: **multisource-m**. Alle streefgrenzen gehaald: **False**.

## Data en training

Broadcastbeelden: {'train': 1710, 'val': 348}. Wedstrijden: {'train': ['4', '6', '9'], 'val': ['2', '3', '5']}.
Som van geregistreerde faselooptijden: 208.83 minuten. Fasen kunnen overlappen; dit is geen gemeten GPU-rekentijd en geen complete som van alle verkennende proeven.
Oorspronkelijke team-, keeper- en tracklabels blijven bewaard. Geen officiële test- of challengebeelden gebruikt.

De validatieset is herhaald gebruikt om checkpoints, drempels en combinaties te kiezen. Daarom zijn deze ontwikkelcijfers geen onafhankelijke eindtest. De aangeleerde shirtprojectie presteerde slechter dan de verzadigingsgewogen kleurhistogrammen; die eenvoudigere referentie is behouden. De speler- en rolmodellen zijn wel werkelijk bijgetraind.

## Toepassing

Nieuwe uitvoer: `C:\Messi10\runs\d3cff1b2360bb235635d9e2dcd99870a462d153a6b253913c73afb2f07b61664`. De veldkalibraties zijn op alle frames identiek aan de oorspronkelijke analyse.
Open: [broadcastanalyse](http://127.0.0.1:8501/?run=d3cff1b2360bb235635d9e2dcd99870a462d153a6b253913c73afb2f07b61664).

Video, minimap en CSV gebruiken dezelfde teamindeling. Bij ontbrekende veldkalibratie blijven veldposities en telling onbekend.

## Grenzen

Keepers met afwijkende kleding worden niet in een veldspelerskleur gedwongen; zonder betrouwbare koppeling blijft hun team onbekend. Team- en keeperresultaten, gemiste spelers en foutpositieven staan afzonderlijk in het JSON-rapport. De getoonde bronclip is ontwikkeldata; visuele AI-controle is geen menselijke acceptatie of onafhankelijke eindtest. Tracking-ID's blijven tijdelijk.

Voor het geselecteerde profiel zijn 176 van 194 keepers gematcht; 16 krijgen het correcte team. Dit onderdeel blijft dus een beperking.

Reproduceren en verdere trainingsrondes: zie `docs/Broadcast_Hervatten.md` en de brongebonden trainingsrecords in `reports/broadcast-pitch-v1/summary.json`. Starten: `scripts/Start-Gezamenlijk.ps1`.

## Extra voetbaltrainingsdata

De aanvullende detectorronde gebruikt zeven trainingswedstrijden: {'4': 540, '6': 570, '9': 600, 'sportsmot:v_1yHWGw8DH4A': 811, 'sportsmot:v_HdiyOtliFiw': 744, 'sportsmot:v_gQNyhv8y0QY': 580, 'sportsmot:v_iIxMOsCGH58': 91}. De SportsMOT-selectie bevat uitsluitend officiële voetbal-trainclips. De oorspronkelijke SoccerNet-validatiewedstrijden zijn behouden. Beelden en labels zijn op hash gecontroleerd; bronfingerprints staan in het verslag. SportsMOT is gepubliceerd onder CC-BY-NC-4.0.
