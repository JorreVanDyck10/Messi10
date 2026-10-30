# Afgelegde afstand per speler

De toepassing berekent nu de waargenomen afstand per bestaand speler-ID.
Ze leest de opgeslagen veldposities en trackinggegevens. Er wordt geen
model getraind, geen nieuwe detectie uitgevoerd en geen tracking gestart.

## Gebruiken

1. Open een voltooid resultaat, bijvoorbeeld via **Opgeslagen analyses**.
2. Vink **Afgelegde afstand per speler berekenen** aan.
3. Vul de lengte en breedte van het **hele veld** in meters in. De standaard
   105 × 68 m is een aanname. Gebruik niet de afmetingen van alleen het zichtbare
   strafschopgebied.
4. Bekijk de tabel per trackingfragment en speler-ID.
5. Download de berekening met **Afgelegde afstanden downloaden (CSV)**.

Een analyse moet al track-ID's en geldige spelerposities bevatten. Zonder
tracking kan de toepassing niet bepalen welke waarneming in het volgende
frame dezelfde speler is. Ze toont dan een uitleg in plaats van verzonnen
afstanden. De eenvoudige schoolmodus schakelt tracking niet automatisch in;
gebruik voor deze uitbreiding een bestaande analyse met tracking.

Nieuwe handmatige kalibraties met een strafschopgebied bewaren de gekozen
veldafmetingen. De afstandsweergave neemt die over. Bij oudere of automatische
analyses zonder deze gegevens blijven de defaults uitdrukkelijk aannames.
Gebruik dezelfde afmetingen als voor de kalibratie: hier een getal veranderen
schaalt de afstanden, maar herberekent de homography niet.

## Berekening zoals in de les

De minimap bewaart genormaliseerde coördinaten: `u` over de lengte, `v` over de
breedte. Voor twee opeenvolgende waarnemingen van dezelfde track:

```python
dx = (u2 - u1) * veldlengte
dy = (v2 - v1) * veldbreedte
stapafstand = (dx**2 + dy**2)**0.5
```

Dit is Pythagoras. De waargenomen afgelegde afstand is de som van de geldige
stapafstanden. Er is geen nieuwe leertechniek of ingewikkeld model nodig.

Bij een veld van 100 × 50 m geeft een verschil van 0,03 in `u` en 0,08 in `v`
een stap van 3 m in de lengte en 4 m in de breedte: samen 5 m. Gaat de speler
daarna terug, dan wordt de afgelegde afstand 10 m, hoewel begin- en eindpositie
gelijk zijn. Afgelegde afstand is dus iets anders dan nettoverplaatsing.

## Wat wordt wel en niet opgeteld

Alleen actuele, als speler meegetelde waarnemingen met geldige veldcoördinaten
worden gebruikt. Een algemene persoon of scheidsrechter wordt geen speler.
Een track-ID moet in dat frame uniek zijn. Twee waarnemingen met dezelfde ID
zijn ambigu en worden niet onderling verbonden.

Ontbreekt een speler, ontbreekt de veldprojectie of ontbreekt een frameovergang,
dan wordt dat stuk niet ingevuld. De volgende geldige waarneming begint een
nieuw trajectdeel. Een geregistreerde camerawissel of trackingreset begint
een apart trackingfragment; gelijknamige ID's uit verschillende fragmenten
worden niet als één persoon opgeteld.

De stapafstand gedeeld door de verstreken tijd dient als controle op sprongen.
Standaard worden stappen boven 12 m/s overgeslagen. Dit is een instelbare
projectgrens, geen bewering over de werkelijke topsnelheid van een speler.
Afgewezen sprongen zijn zichtbaar in de tabel en CSV.

## De tabel juist lezen

- **Waargenomen afstand**: som van de geaccepteerde stapafstanden in dit fragment.
- **Gemeten tijd**: alleen de tijd tussen die geaccepteerde waarnemingen.
- **Meetintervallen**: aantal geaccepteerde verbindingen tussen twee frames.
- **Trajectdelen**: afzonderlijke stukjes zonder ingevulde gaten.
- **Overgeslagen sprongen**: stappen die boven de ingestelde controlegrens lagen.

Een lege afstand betekent dat er te weinig opeenvolgende waarnemingen zijn.
Een werkelijk stilstaande track met minstens één geldig interval kan wel
0 meter hebben. Tijdelijke ID's zijn geen namen of rugnummers.

De CSV bevat ook de gebruikte veldafmetingen, framerate, spronggrens en eerste
en laatste waarneming. De oorspronkelijke analysebestanden worden niet gewijzigd.

## Beperkingen en vragen tijdens de verdediging

De uitkomst is een schatting van zichtbare deeltrajecten in deze clip. Een fout
speler-ID, verkeerde homography, verkeerde veldafmetingen of positieruis kan
de afstand vertekenen. Kleine heen-en-weerschommelingen kunnen de som te groot
maken. Daarom is dit geen onafhankelijk gevalideerde volledige wedstrijdafstand.

Oefen deze vragen:

- Waarom vermenigvuldig je `u` met de lengte en `v` met de breedte?
- Waarom gebruik je Pythagoras en niet alleen het verschil tussen begin en einde?
- Waarom tel je geen afstand op over een ontbrekend stuk?
- Waarom staat de gemeten tijd naast de afstand?
- Wat gebeurt er bij een camerawissel, dubbele ID of verkeerde koppeling?
- Waarom zijn de veldafmetingen en projectiekwaliteit belangrijk?

Code: `src/football_pipeline/distances.py` voor de berekening en
`src/football_pipeline/distance_ui.py` voor de weergave en CSV-download.

De volledige softwarecontrole slaagt met **446 tests en 4 subtests**.
[Testrapport](../reports/distance-feature-tests.xml). De afstandstests gebruiken
bekende meetkundige paden, ontbrekende waarnemingen en synthetische tracking;
ze bewijzen de rekenlogica en integratie, geen nauwkeurigheid op echte wedstrijden.
