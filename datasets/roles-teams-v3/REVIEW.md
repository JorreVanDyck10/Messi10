# Wat een menselijke reviewer controleert

De huidige status is **voorlopige AI-review**. Dit document en het CSV-bestand zijn geen bewijs dat een student de labels al heeft goedgekeurd.

Open `reports/person1-round3/data-audit-final/new-crops/`: de zeven `labels-*.jpg`-bladen tonen alle 93 nieuwe crops. De `*-context.jpg`-beelden tonen de voorgestelde boxen in het oorspronkelijke beeld. De ruwe beelden staan onder `datasets/roles-teams-v3/sources`; de oudere crops verwijzen vanuit het manifest naar hun oorspronkelijke datasetversie.

Gebruik `reports/person1-round3/data-audit-final/human-review.csv` voor alle 1.621 crops. De `image`-paden daarin zijn relatief aan `datasets/roles-teams-v3`, niet aan de CSV-map. De boxkolom gebruikt oorspronkelijke pixels.

Controleer per rij:

1. **Eén bedoelde persoon:** omvat de box daadwerkelijk de bedoelde persoon, met de afgesproken zichtbare begrenzing? Vermijd één box om twee verschillende personen en meerdere labels van dezelfde persoon onder bijna gelijke boxen.
2. **Juiste rol:** speler omvat ook doelman; centrale referee en assistant referee blijven onderscheiden. Kleur, een fluorescerend vest of alleen veldpositie bewijst geen functie. Bij onvoldoende rolbewijs blijft `person` passend of wordt de crop uitgesloten van specifieke rolsupervisie.
3. **Voldoende zichtbaarheid:** controleer blur, occlusion, beeldrand en uitsluitend een hand/hoofd/voeten. Lees eerst de labelregels en beoordeel twijfel in de broncontext.
4. **Team alleen met bewijs:** alleen gecontroleerde spelers hebben een teamlabel. Een andere keeperskleur geeft geen automatisch team. De nieuwe bronnen hebben bewust geen teamlabels.
5. **Herkomst en subset:** noteer een verkeerd bronmoment of verdacht duplicaat; verplaats geen losse bijna gelijke frames tussen train en val om een score te verbeteren.

Vul pas na echte controle `reviewer`, `review_status`, eventuele correctie en `notes` in. Bewaar de oorspronkelijke CSV en de besproken correcties; maak bij labelwijzigingen een nieuwe manifestversie. Laat de andere student verschillen controleren. Nieuwe echte annotatiefouten in validatie vereisen herbeoordeling van **alle** betrokken referentiemodellen.

Voor de onafhankelijke proefannotatie kiezen jullie gezamenlijk zes ontwikkelbeelden met duidelijke objecten, kleine objecten, overlap/occlusion, blur, beeldrand en afwezig doel. Maak de relevante annotaties eerst afzonderlijk, bespreek daarna aanwezigheid, klasse en boxbegrenzing en leg de definitieve regel vast. Rapporteer pas overeenstemming als beide echte annotatiepakketten bestaan.

Gereserveerde testbeelden worden niet via modeluitvoer voor tuning gebruikt. Eventuele testlabelreview gebeurt met de afgesproken afzonderlijke reviewerprocedure. Er is in deze ronde geen testinference uitgevoerd.
