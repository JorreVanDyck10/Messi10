> **Historisch verslag. De standaardkeuze hieronder is op 30 oktober 2026 teruggedraaid:** beide extra veldframes vallen buiten de uitgebreidere provider-lijntolerantie. Het oorspronkelijke veldbeleid blijft standaard. Zie [de actuele meting en beslissing](Broadcast_Betrouwbaarheid_20261030.md).

# Broadcastbetrouwbaarheid — 28 oktober 2026

## Wat nu beter werkt

Het standaardbroadcastprofiel gebruikt een kleine, gecontroleerde verbetering van de veldprojectie. Als de vaste verdeling van veldpunten geen unieke homografie kan bepalen, wordt geen nieuwe matrix gegokt. Een recente betrouwbare kalibratie mag alleen via de bestaande camerabewegingscontrole worden overbrugd. Punt- en lijncontroles, camerawissels en de maximale leeftijd van twee seconden blijven gelden. Zonder betrouwbare voorgeschiedenis blijft de veldpositie onbekend.

De detector-, rol- en teamgewichten en de trackerinstellingen zijn behouden. De grotere onderzochte modelvarianten voldeden niet aan alle controles. De geleverde winst is bescheiden; dit is geen nieuw bewijs van betrouwbare volledige wedstrijdstatistieken.

## Hoe goed werkt de keten?

Onderstaande vergelijking gebruikt **dezelfde 450 opeenvolgende validatiebeelden** uit drie bestaande ontwikkelwedstrijden. De eerste route gebruikt providergeometrie om herkenning los van automatische kalibratie te meten. De andere routes voeren de automatische veldprojectie en herkenning werkelijk opnieuw uit op dezelfde pixels.

| Meting | Providergeometrie | Automatisch vóór | Automatisch na |
|---|---:|---:|---:|
| Spelerprecision | 96,68% | 96,52% | 96,54% |
| Spelerrecall | 95,02% | 72,45% | 72,79% |
| Correct gevonden én correct team / alle spelers | 91,18% | 69,43% | 69,76% |
| IDF1 voor tracks met veldpositie | 93,95% | 79,71% | 79,87% |
| ID-wissels voor tracks met veldpositie | 9 | 16 | 16 |
| IDF1 voor beeldtracks, ook zonder veldpositie | 93,95% | 90,38% | 90,40% |
| ID-wissels voor beeldtracks | 9 | 22 | 22 |

De wijziging vindt 22 extra referentiespelers bij hetzelfde aantal foutpositieven: **4.771 → 4.793 TP; 172 FP**. Twee extra frames krijgen bruikbare veldprojectie; er gaan geen bestaande geldige frames verloren. De projectiematrices op alle gemeenschappelijke geldige frames blijven gelijk.

De belangrijkste beperking blijft automatische velddekking. Een detector kan iemand correct zien terwijl diens veldpositie onbekend blijft. Dat verklaart waarom de volledige keten duidelijk lager scoort dan herkenning met referentiegeometrie.

Deze korte reeksen zijn relatief gunstig en geven **geen vervanging** voor de bredere ontwikkelmeting op 341 beelden: spelerprecision 92,07%, recall 91,04%, correct gevonden én ingedeeld 82,87%. Die detector- en teamscores veranderen niet door de nieuwe veldregel. De bredere set bevat 194 keeperreferenties; eerder kregen slechts 16 daarvan het juiste team. Keepers en officials blijven aandachtspunten.

## Andere controles en verworpen proeven

- Op 80 bestaande veldbeelden uit meer situaties blijven de aantallen correcte en onjuiste directe kalibraties gelijk, bij beide historische netwerkcaches. Beeld- en labelhashes zijn gecontroleerd.
- Op de langere eigen broadcastclip stijgt bruikbare kalibratie van 251 naar 255 van 1.239 frames, zonder verloren geldige frames. Dat is ongeveer **20,3% → 20,6% dekking**. Er ontbreken menselijke referenties om de nauwkeurigheid op deze clip vast te stellen.
- Een zwaarder gewogen official-contextmodel verbeterde de gezamenlijke teamscore niet. De temporele rolproef gaf geen validatiewinst. Keeperkoppeling leverde geen netto betere validatiescore op.
- Boxfusie met gewicht 0,75 verbeterde de brede momentopnames licht, maar verslechterde tracking en teams op de opeenvolgende reeksen. Niet gekozen.
- Nieuwe directe fits met geometrisch gekozen controlepunten herstelden veel frames, maar maakten ook extra onjuiste projecties geldig op de bredere veldset. Ook de strengere variant met extra controlepunten is afgewezen. De actieve wijziging maakt daarom uitsluitend gebruik van de begrensde camerabrug.
- Trackerdrempel 0,9 werd op training gekozen uit 0,7/0,8/0,85/0,9, maar generaliseerde onvoldoende naar alle validatiereeksen. De oorspronkelijke drempel 0,8 blijft actief.

## Gebruik en interfaces

Start met `scripts/Start-Gezamenlijk.ps1` of `scripts/Start-Spelermodel.ps1 -Recognition broadcast`.

`configs/models-broadcast.json` bevat nu optionele `field_settings`. Bij een nieuwe automatische analyse geldt: expliciete `field_settings` in de aanroep gaat vóór `calibration_settings` in de veldruntime; daarna volgt het modelprofiel. Een expliciet meegegeven bestaande kalibratie behoudt haar eigen instellingen. Handmatige kalibratie wordt hierdoor niet gewijzigd. Bestaande uitvoermappen worden niet overschreven.

Het afzonderlijke profiel `configs/field-motion-rank.json` kan via de bestaande CLI-optie `--field-settings` worden gebruikt. De algemene legacy-instellingen en andere herkenningsprofielen blijven beschikbaar. Alleen het geselecteerde broadcastprofiel kiest de nieuwe veldregel standaard.

De evaluatie ondersteunt nu een expliciet confidencewerkpunt, cijfers per wedstrijd en afzonderlijke beeld- en veldtracking. Confidence 0,10 meet het ruwe lagere detectiewerkpunt; de app toont/telt standaard vanaf 0,25 of bij een gekoppeld track. Een losse 0,10-score is daarom geen exacte score voor de volledige runtime.

## Bewijs, reproduceerbaarheid en grenzen

- [Vastgelegde baseline en datasplits](../reports/broadcast-reliability-day1-20261028/summary.json): 3.936 trainingsbeelden, 348 validatiebeelden; alle 4.284 beeldhashes gecontroleerd. Geen wedstrijd- of identieke beeldhashoverlap binnen deze manifesten. Dit sluit overlap met alle historische pretraining niet uit.
- `data/broadcast-temporal-v1/manifest.json`: 900 opeenvolgende beelden, zes vaste clips, 150 beelden per clip. Eerste clip per reeds gekozen wedstrijd, eerste volledig gelabelde reeks; selectie vóór inference. Training en validatie blijven apart.
- [Beeld- en veldtracking vóór de wijziging](../reports/broadcast-reliability-day2-20261028/image-and-field-tracking-comparison.json), [controle van gemeenschappelijke projecties](../reports/broadcast-reliability-day2-20261028/final-common-projection-check.json), [bredere veldcontrole](../reports/broadcast-reliability-day2-20261028/field-motion-rank-final-historical80.json).
- [433 tests en vier subtests geslaagd](../reports/broadcast-reliability-day2-20261028/final-tests.xml), inclusief camerawissels, meetgaten, overlappende personen, identiteitsfragmentatie, onbepaalbare geometrie en het verstrijken van de camerabrug. Ruff en formatteringscontrole slagen voor de CI-paden.
- Lokale native integratie, gepaarde looptijdmetingen en de volledige clip staan onder `artifacts/broadcast-reliability-release-20261028`. `integration.json` en `timing.json` bevatten de werkelijke uitvoerpaden en tijden. De looptijdvergelijking gebruikt dezelfde opgeslagen veldnetwerkwaarnemingen; de ongewijzigde veldnetwerkinference is uitgesloten.
- Afstanden blijven waargenomen schattingen per tijdelijk ID, met meetdekking en onderbrekingen. Geen GPS-/afstandreferenties zijn beschikbaar; er is geen afstandsnauwkeurigheid gemeten.

De validatie is herhaald gebruikt voor ontwikkeling. **Menselijke review en een onafhankelijke eindtest ontbreken.** Er is geen menselijke acceptatie ingevuld. Gegevens, verworpen proeven en oorspronkelijke analyses zijn behouden. Het [hervatdocument](Broadcast_Betrouwbaarheid_Hervatten.md) beschrijft de actuele status en mogelijke vervolgstappen.

## Gecontroleerde uitvoering openen

De volledige analyse staat bij de opgeslagen analyses onder run `316e0824bc9fbb019691a294474bbc008c9701072b5309b6ee3939e759e6c386`. Video en alle 1.239 CSV-tellingen zijn gecontroleerd. Afstands-CSV’s staan lokaal onder `artifacts/broadcast-reliability-release-20261028/exports`.

De gepaarde native looptijden zijn mediaan **38,87 s vóór en 38,38 s na** op dezelfde 150 frames; de afgesproken grens van maximaal20%extra tijd is gehaald. Dit is een kleine lokale vergelijking, geen algemene snelheidsclaim.

In scope `on_pitch_players` rendert het beeld alleen getelde veldspelers. Bij ontbrekende kalibratie kan daarom ook de beeldoverlay leeg zijn, hoewel ruwe detecties worden bewaard. Frame619 toont dit; frame18 is gecontroleerd met geldige projectie, spelerboxen en minimap. Deze visuele controle is geen menselijke acceptatie.

[Definitieve ontwikkelacceptatie en bronhashes](../reports/broadcast-reliability-day2-20261028/final-acceptance.json).
