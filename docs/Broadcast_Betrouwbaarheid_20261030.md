# Broadcastbetrouwbaarheid — 30 oktober 2026

Het model vindt en deelt veel zichtbare spelers correct in, maar is nog geen onderbouwde bron voor volledige wedstrijdstatistieken of nauwkeurige gelopen afstanden. De uitgebreidere meting geeft voor de automatische keten **93,46% spelerprecision, 82,46% spelerrecall en 78,50% correct gevonden én correct ingedeelde spelerwaarnemingen**. De veldprojectie blijft een belangrijke beperking.

**Het oorspronkelijke standaardveldbeleid is hersteld.** De kleine camerabrug die op 28 oktober voorlopig was gekozen, krijgt met de uitgebreidere veldlijnreferentie geen goedkeuring. De detector-, rol-, team- en trackergewichten zijn behouden. Nieuwe proeven zijn niet stilzwijgend in de app gezet.

## Hoe de keten werkt

De detector stelt personen en spelers voor. Een geleerd uiterlijk- en contextmodel verfijnt de rollen. Team A en B worden per analyse uit shirtkenmerken gegroepeerd; dit zijn neutrale groepen, geen herkende clubnamen. ByteTrack koppelt beeldwaarnemingen aan tijdelijke ID’s, met cameracompensatie.

Een afzonderlijk veldmodel herkent veldpunten en lijnen. Daaruit wordt een projectie op een aangenomen veldtemplate bepaald. Een recent anker mag maximaal twee seconden via gecontroleerde camerabeweging worden overbrugd. Een intern geldige projectie is nog geen bewezen nauwkeurige veldpositie. Afstanden worden uit waargenomen posities per tijdelijk ID geschat, met meetgaten en onderbrekingen.

## Wat werkelijk is gemeten

De vaste selectie bestaat uit 2.700 beelden: drie afzonderlijke vensters van zes seconden uit elk van zes bestaande clips. Het gaat om het begin, midden en einde van clips van dertig seconden. De helft is training en de helft validatie, met drie wedstrijden per split. De nieuwe 1.800 beelden hebben geen frame-ID- of beeldhashoverlap met de oorspronkelijke 900 beelden. ZIP-checksums, beeldhashes en bronlabels zijn gecontroleerd.

De validatie bevat **1.350 beelden en 19.874 spelerwaarnemingen**, geen 19.874 verschillende personen. Deze wedstrijden zijn al voor ontwikkeling gebruikt. Dit is geen onafhankelijke eindtest. De losse vensters bewijzen geen blijvende identiteit over een volledige wedstrijd.

| Meting op dezelfde validatiebeelden | Automatische keten | Met providergeometrie |
|---|---:|---:|
| Spelerprecision | 93,46% | 93,95% |
| Spelerrecall | 82,46% | 93,82% |
| Correct gevonden én correct team / alle spelerwaarnemingen | 78,50% | 89,47% |
| IDF1 van beeldtracks | 90,74% | 92,45% |
| IDF1 van tracks met veldpositie | 85,78% | 92,45% |
| Beelden met beschikbare veldprojectie | 1.185/1.350 (87,78%) | 1.350/1.350 |
| Gemiddelde absolute telfout bij beschikbare projectie | 0,73 spelers | 0,57 spelers |

De app telt ook een gekoppelde detectie onder confidence 0,25 mee. De nieuwe runtime-score volgt die bestaande regel. De oudere vaste 0,25-benchmark blijft daarnaast reproduceerbaar. Ontbrekende kalibratie wordt bij telfouten als onbekend behandeld, niet als nul spelers.

De automatische route heeft 16.388 correcte en 1.146 foutpositieve spelerwaarnemingen en mist er 3.486. Het totale aantal spelers klopt op 536 van de 1.185 beschikbare frames. Zo’n kloppend totaal kan een gemiste speler en een foutpositief tegen elkaar wegstrepen; precision en recall blijven daarom nodig. Er zijn 35 veld-ID-wissels en 44 beeld-ID-wissels, opgeteld over de afzonderlijke vensters.

De providerroute gebruikt referentiecorrespondenties om geometrie als ontwikkelfactor te onderzoeken. De rolbeslissingen en teamgroepering kunnen daardoor eveneens veranderen. Deze route is geen automatische veldnauwkeurigheid en geen gegarandeerde bovengrens voor iedere afzonderlijke score.

De spreiding over tijd is groot. Automatische precision is circa 96,45% aan het begin, 90,20% in het midden en 94,07% aan het einde. Recall is respectievelijk 72,62%, 80,50% en 93,90%. De gewichten zijn gelijk; de andere beelden en velddekking verklaren dat verschillende tijdvakken andere scores geven.

Keeperteams blijven zwak: 381 van 979 keeperwaarnemingen krijgen het juiste team, 179 een verkeerd team. De rest wordt niet correct gevonden en ingedeeld. De hoge teamscore onder gevonden spelers mag daarom niet als betrouwbare keeperkoppeling worden gelezen.

## Veldposities zijn niet hetzelfde als gevonden spelers

Voor 1.319 validatieframes vallen de bronveldlijnen binnen het ondersteunde labelbereik. Op 596 daarvan blijft de projectie binnen de vaste referentietolerantie; op 561 wordt die overschreden en op 162 ontbreekt de projectie. Nog 31 veldreferenties worden apart gehouden wegens coördinaten buiten het ondersteunde voorbewerkingsbereik. Alle personenbeelden blijven in de herkennings- en trackingmeting.

De tolerantie is een mediane lijnprojectieafwijking van maximaal 0,5% en een maximale afwijking van 1% van de beelddiagonaal. Buiten tolerantie betekent dat minstens één criterium wordt overschreden; dit is geen menselijke classificatie van een volledig verkeerde kaart. De toets gebruikt het aangenomen template van 105 × 68 meter. Dit meet geen GPS- of afstandsnauwkeurigheid.

Op de eigen clip van 49,56 seconden heeft het oorspronkelijke beleid slechts **251 van 1.239 frames (20,26%)** een intern geldige veldprojectie. Er zijn geen onafhankelijke positie- of afstandsreferenties voor deze clip. Goede ontwikkelscores op andere camera’s onderbouwen dus geen volledige statistieken voor deze eigen opname.

## Waarom de eerdere keuze is teruggedraaid

De rank-bridgeproef herstelde in de eerste validatiereeks twee frames en 22 spelerwaarnemingen. De nieuwe veldlijntoets laat zien dat beide extra frames, index 90 en 92 van SNGS-078, buiten de referentietolerantie vallen. Op de andere 1.800 beelden verandert deze proef geen projectie. Daarmee faalt de afgesproken grens voor extra projecties buiten tolerantie.

`configs/models-broadcast.json` is gecontroleerd gelijk aan het oorspronkelijk geladen profiel. Het oorspronkelijke veldbeleid blijft standaard. De optionele profielondersteuning en `configs/field-motion-rank.json` zijn behouden om de afgewezen proef expliciet te kunnen reproduceren. Het [verslag van 28 oktober](Broadcast_Betrouwbaarheid_Resultaten.md) is als historisch gemarkeerd; de acceptatie daar is door deze controle achterhaald. Bestaande analyses en modellen zijn bewaard.

## Andere onderzochte routes

- Terugwerken vanaf een toekomstig veldanker verhoogde recall en veld-IDF1, maar verlaagde precision, teamscore en beeld-IDF1. Niet gekozen.
- Trackgewogen shirtgroepering, identiteitsuitsluiting, trackmedianen en wortelhistogrammen voldeden niet aan de trainingscontroles. Een geleerde kleurtransformatie verbeterde training sterk en faalde op validatie.
- Automatisch bijsnijden verbeterde enkele eigen beelden, maar verhoogde projecties buiten tolerantie op de bredere validatie. Pixelcontroles waren onvoldoende robuust of te traag.
- Een kleine veldnetwerk-uitvoerlaag is getraind met 1.024 bestaande beelden uit 289 trainingswedstrijden. Alleen 231 wedstrijden trainden de laag; 58 interne holdoutwedstrijden kozen het checkpoint. De oorspronkelijke validatie koos geen gewichten. De netwerkvervanging faalde een andere veldvalidatie; aanvullende toepassing voegde twee projecties buiten tolerantie toe. Beide routes blijven uitgeschakeld.
- Een motion-only proef voor een onbepaalbare zichtbare puntverdeling herstelt zeven frames ten opzichte van de tijdelijke rank-bridgebaseline op de eigen clip. Op 2.700 gelabelde beelden is er geen extra projectie. Zonder nauwkeurigheidsbewijs voor die zeven frames blijft ook deze proef uit de standaard.
- Een vaste contextdrempelproef op training verwijderde negen foutpositieven, maar verloor een correct gevonden en ingedeelde speler. De drempel blijft 0,99. Geen validatiezoektocht volgde.

## Bewijs en hervatten

Na herstel van het standaardprofiel slagen **455 tests en 4 subtests**. Ook Ruff check, Ruff format en de lokale afhankelijkhedencontrole slagen. De [definitieve selectiebeslissing](../reports/broadcast-reliability-20261030/final-decision.json) legt expliciet vast dat de eerdere acceptatie is achterhaald en dat de modeldoelen nog niet zijn gehaald.

De [samenvatting met bronhashes](../reports/broadcast-reliability-20261030/summary.json), [datasetcontrole](../reports/broadcast-reliability-20261030/temporal-extension-audit.json), [uitgebreide veldaudit](../reports/broadcast-reliability-20261030/motion-rank-release-audit.json) en [profielherstelcontrole](../reports/broadcast-reliability-20261030/profile-restoration.json) bevatten de onderbouwing. De getoonde latere automatische waarnemingen zijn hergebruikt nadat alle projectie-inputs exact gelijk bleken aan het herstelde standaardbeleid; voor gewijzigde projecties wordt geen oude detectorrun als nieuwe inference gepresenteerd.

Nieuwe en historische proeven hebben aparte uitvoermappen. Zware beeld-, netwerk- en featurecaches blijven lokaal bewaard; selectie- en evaluatiescripts zijn versieerbaar. [Het hervatdocument](Broadcast_Betrouwbaarheid_Hervatten.md) beschrijft controles, opdrachten, Git-status en resterende beperkingen. Menselijke review, onafhankelijke eindtest en afstandsvalidatie blijven expliciet onvoltooid.
