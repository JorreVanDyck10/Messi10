# Twaalf extra ontwikkelkandidaten — nog geen trainingslabels

Deze map bevat **12 nieuwe volledige videoframes van 4096 × 1080**, geselecteerd uit 25 onderzochte momenten in de zes bestaande trainingsgroepen van `football48`. Er zijn geen validatie- of testgroepen geanalyseerd. Dit zijn nieuwe momenten uit **dezelfde wedstrijd**, geen twaalf nieuwe situaties uit verschillende wedstrijden.

De selectie geeft voorrang aan onzekere R007-rolvoorstellen en mogelijke spelers buiten de bestaande, door AI geschatte veldregio. Dat zijn onderzoekssignalen, geen bewezen fouten. Het volledige frame blijft ongemaskeerd en bevat ook de zijlijnomgeving. De automatische voorstellen staan in `manifest.json`; er zijn bewust geen YOLO-labelbestanden gemaakt die onterecht als negatieve of gecontroleerde beelden kunnen worden gebruikt.

Ook de voorgestelde teams zijn ongecontroleerd: de neutrale kleurclustering wordt per bronclip opnieuw opgebouwd. A/B kan daardoor tussen fragmenten wisselen. Definitieve labels moeten de teamindeling voor deze wedstrijd gezamenlijk vastleggen.

**Status:** ongelabeld, menselijke review open, niet geschikt voor training zonder verdere annotatie. Er is met dit pakket geen model getraind en geen verbeterde nauwkeurigheid gemeten. De bestaande datasets en geselecteerde gewichten zijn niet aangepast.

## Bekijken en controleren

Open `contactsheet.jpg` voor het overzicht en `images/` voor de volledige resolutie. Controleer de bronbeelden bij het annoteren, niet uitsluitend het verkleinde overzicht. Elk voorstel moet worden nagekeken, inclusief gemiste personen en objecten. Label een speler niet als steward op basis van alleen een voorspelling of veldpositie; officials, doelmannen, reserve-/technische staf en onbeslisbare personen vragen de afgesproken inhoudelijke regels.

Ieder beeld bevat zijn cliphash, exacte clipframe-index, tijdstip, bronafmetingen en beeldhash. De oorspronkelijke lange video is niet opnieuw gebruikt: de geschatte oorspronkelijke index blijft expliciet bij benadering, omdat de referentieclips maximaal één frame kunnen afwijken. Voor exacte reproductie zijn de cliphash en clipindex leidend.

De gekozen momenten liggen minstens één seconde van de bestaande annotatiemomenten en onderling minstens drie seconden binnen hun groep. Dat voorkomt exacte herhaling en beperkt nabije duplicaten, maar maakt beelden uit dezelfde wedstrijd niet statistisch onafhankelijk. Nieuwe labels behouden later de trainingsgroep van hun bron; deze modelgestuurde selectie mag geen onafhankelijke eindtest worden.

## Reproduceren

Na `git lfs pull`, projectinstallatie en installatie van de modellen:

```powershell
.\.venv\Scripts\python.exe -m scripts.collect_development_candidates --output data\eigen-ontwikkelkandidaten
```

Kies een nieuwe uitvoermap; het script overschrijft geen bestaand pakket. Inference gebruikt het bestaande rollenprofiel en de werkelijke software/GPU van de uitvoerder. `selection-pool.json` bewaart alle onderzochte kandidaten en hun selectiesignalen. Beeldbestanden zijn JPEG-exports op kwaliteit 95, met een hash van de oorspronkelijke gedecodeerde pixels naast de bestandshash.

## Wat eerst verbeteren

1. **Baldetectie:** de geleverde 48 persoons-/balbeelden zijn nog niet voor een nieuwe geselecteerde detector gebruikt. Controleer vooral kleine ballen, negatieven, crop-/maskervoorbewerking en labelreview; vergelijk vervolgens een echte nieuwe training met de baseline op dezelfde validatiegroepen.
2. **Rollen:** deze twaalf frames kunnen nieuwe trainingscrops opleveren voor het onderscheid speler/official/persoon. Ze leveren geen gegarandeerde uitbreiding van steward-/supporterlabels: die rollen moeten echt zichtbaar en betrouwbaar identificeerbaar zijn.
3. **Teams:** gebruik A/B per wedstrijd, met gecontroleerde doelmannen en onbekende teams. Gegevens uit één extra tijdstip bewijzen geen transfer naar andere shirtkleuren.
4. **Veld:** rol-/balboxen trainen het punten- en lijnmodel niet. Hiervoor zijn passende gecontroleerde veldpunten/lijnen nodig; sterke panoramavervorming vraagt bovendien een geometrische oplossing.

Voor werkelijke variatie zijn andere wedstrijden en camera's waardevoller dan veel opeenvolgende frames. [SoccerNet Game State Reconstruction](https://www.soccer-net.org/tasks/game-state-reconstruction) bevat speler-/doelman-/scheidsrechterrollen en teams, maar geen gegarandeerd aparte steward-/supporterlabels. [SoccerTrack v2](https://atomscott.github.io/SoccerTrack-v2/) biedt panoramawedstrijden met rollen en teams. Bronnen zijn onderzocht, niet gedownload of automatisch aan de eigen dataset toegevoegd; gebruiksvoorwaarden en eventuele toegang blijven per bron te controleren. Sommige [SoccerNet-datasets vragen accounttoegang en NDA-acceptatie](https://www.soccer-net.org/data).

De opdracht vraagt een gerichte eigen annotatieset van 40–80 uitdagende beelden. Dit kandidaatpakket verandert die afgesproken set niet automatisch. Kies binnen de kernset eerst de nuttigste gevallen; houd externe data of verdere uitbreidingen afzonderlijk en transparant bij.
