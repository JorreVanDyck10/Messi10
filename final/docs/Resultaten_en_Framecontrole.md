# Analyses terugvinden en frame voor frame controleren

Deze verbeteringen veranderen de toepassing en de uitleg. Modelgewichten,
modelinstellingen, trainingscode en detectiedrempels zijn niet aangepast.

## Een bestaande analyse openen

Open bovenaan **Opgeslagen analyses** en vink **Een eerdere analyse openen** aan.
Kies een resultaat op datum, kalibratiemethode, duur en analyse-ID. Dit werkt
ook in de schoolmodus, zonder opnieuw een video te uploaden. De datum wordt
uitdrukkelijk in UTC weergegeven.

Alleen voltooide analyses uit de actieve uitvoermap verschijnen in de lijst.
Bij openen controleert de toepassing de bestaande bestanden en checksums.
Beschadigde of ontbrekende uitvoer geeft een foutmelding. Met **Opnieuw laden**
kun je de geselecteerde analyse opnieuw laten controleren. De directe links
werken nu ook voor geldige analysenamen met de achtervoeging die bij een
eerdere onvoltooide uitvoering kan ontstaan.

De algemene historie bewaart haar resultaat apart van je actieve upload en
start geen nieuwe verwerking. Vink de optie uit om terug te gaan naar de uploadstappen.
De bestaande aparte schermen voor teamcorrecties en uitgebreide automatische
veldreview blijven beschikbaar.

Bij het verlaten van een directe analyselink of de aparte teamweergave wordt
de oude schermstatus gewist. Daardoor kan die analyse niet per ongeluk als
resultaat van een andere upload verschijnen. De opgeslagen bestanden blijven
behouden. De lijst wordt op het werkelijke tijdstip gesorteerd, ook als bestanden
verschillende tijdzones vermelden; onbekende datums komen onderaan.

## Eén exact frame bekijken

Onder het resultaat kun je **Een exact frame en de veldposities bekijken**
aanvinken. Kies een frame met de schuifbalk. Je ziet het opgeslagen uitvoerbeeld
met detecties en minimap, plus de gegevens van hetzelfde framenummer en tijdstip.
De toepassing leest de bestaande video; ze voert geen nieuwe detectie uit.
Het oorspronkelijke bronbestand mag daarom verplaatst zijn.

De tabel bevat per opgeslagen detectie de rol, confidence, een eventueel
track-ID, de veldcoördinaten en of die detectie als speler meetelt. `u` en `v`
lopen van 0 tot 1 over lengte en breedte; het zijn geen meters. Een onbekende
of ongeldige veldpositie blijft leeg. Een onbekende telling is niet hetzelfde
als nul spelers. Bij een leeg frame wordt duidelijk vermeld dat er geen
detecties zijn opgeslagen.

Met **Gegevens van dit frame downloaden (CSV)** neem je de tabel mee,
inclusief framenummer en tijd. De tabel kan meer opgeslagen kandidaten bevatten
dan zichtbaar zijn in de video; gefilterde detecties tellen niet noodzakelijk mee.
Deze controle helpt bij foutanalyse, maar beoordeelt de juistheid niet automatisch.

Om door langere analyses te bladeren onthoudt de toepassing waar iedere
frameregel begint. Ze hoeft zo niet alle detectiegegevens tegelijk in het
geheugen te laden. Alleen de gekozen regel en een beperkt aantal videoframes
worden bewaard voor snelle herhaling.

## Duidelijkere puntcontrole

De instructies volgen nu het gekozen velddeel. **Volledig veld** vraagt de
veldhoeken en de twee snijpunten van middenlijn en zijlijnen. Bij een gekozen
**strafschopgebied** volg je het bijbehorende bovenaanzicht en gebruik je de
twee doelgebiedpunten als controle.

De kleuren zijn gelijkgetrokken: blauw voor fitpunten en geel voor
controlepunten, zowel tijdens het klikken als in de controlebeelden.
Vier fitpunten bepalen de transformatie; twee andere punten controleren ze.
De berekening en bestaande controlegrenzen zijn niet gewijzigd.

Na een klik blijven zoom en scrollpositie behouden voor het volgende punt.
De klik wordt nog altijd in de oorspronkelijke beeldpixels opgeslagen; zoom
verandert de geometrie niet. Bij een ander gekozen velddeel wordt het beeld
weer op de volledige weergave gezet.

Framecontrole weigert ongeldige tijdstippen en onbruikbare detectiegegevens
met een leesbare foutmelding. Niet-eindige of te ver buiten het veld liggende
coördinaten blijven leeg in de tabel en CSV, ook als een oud bestand ze als
geldig had aangeduid. De status vermeldt dan **Ongeldige coördinaten**. Dit is
controle van de opgeslagen gegevens, geen nieuwe voorspelling of hertelling.

## Relevante code

- `src/football_pipeline/app_results.py`: opgeslagen analyses en resultaatweergave.
- `src/football_pipeline/result_inspection.py`: opgeslagen frames en CSV-tabel.
- `streamlit_app.py`: toegang tot historie en instructies voor kalibratie.
- `src/football_pipeline/render.py`: kleuren van de klik- en controlepunten.

De nieuwe tests gebruiken expliciet synthetische detecties en echte
video-encoding. Ze controleren onder meer heropenen zonder bronvideo,
lege frames, onbekende posities, CSV-gegevens, bestandscontrole en directe links.
De laatste volledige controle slaagt met **428 tests en 4 subtests**; zie
[het testrapport](../reports/app-reliability-tests.xml). De kliklogica voor
zoom, scroll en oorspronkelijke beeldcoördinaten is ook met JavaScript gecontroleerd.
