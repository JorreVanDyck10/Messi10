# GenAI-disclosure — werkversie

**Datum:** 16 oktober 2026. **Tool:** Codex. Een precieze model-ID is in dit werklog niet vastgesteld.

## Wat met AI-hulp is gemaakt

De uitgebreide werkinstructie, sjablonen, Python-hulpmiddelen, lokale annotatiepagina, PowerShell-starters, configuraties en softwaretests in deze wijziging zijn met AI-hulp opgesteld. AI hielp ook bij bronnenonderzoek, lokale omgeving, het downloaden van de door de gebruiker gekozen video en het uitvoeren van technische controles en pretrained inference.

De opdrachtgever leverde de oorspronkelijke werkbeschrijving, vroeg uitvoering van persoon 1, noemde de RTX 4050 als doellaptop en koos expliciet de YouTube-bron. Er is geen menselijke annotatiereview, gezamenlijke datasetgoedkeuring of individuele mondelinge verdediging namens de studenten nagebootst.

## Werkelijke representatieve prompts

De volgende korte prompts zijn letterlijk uit de gesprekshistorie overgenomen:

1. `wees uitgebreid en concreet`
2. `voer alles van persoon 1 uit`
3. `ik ga het programma runnen op een laptop met een 4050 videokaart`

De latere gebruikersinstructie bevatte de bronlink `https://www.youtube.com/watch?v=HBTFZwMdcCw` en de tekst `dit is de link van die video download dat en zet dat ook mee in de github`. De langere implementatieprompt met het volledige werkplan blijft als oorspronkelijke prompt in de gesprekshistorie beschikbaar; deze is hier niet achteraf gereconstrueerd.

## Controle en verworpen aannames

- De werkelijke ontwikkel-GPU bleek een RTX 3050. Na de gebruikersverduidelijking is de RTX 4050 als doelhardware behouden en zijn lokale meetresultaten apart benoemd.
- De eerste PyAV-versie had geen passende Windows-wheel in deze omgeving. De afhankelijkheid is aangepast naar de daadwerkelijk geïnstalleerde en geteste versie 16.0.1.
- Alfheim-beelden zijn niet zonder geometriebeoordeling als projectbron geaccepteerd wegens zichtbare vervorming.
- Zowel 640 als 1920 inference is werkelijk op dezelfde ontwikkelframes uitgevoerd. Aantallen voorspellingen zijn niet tot nauwkeurigheidsclaims verheven.
- Softwaretests en een synthetische training zijn daadwerkelijk uitgevoerd. Synthetische scores tellen niet mee als voetbalresultaten.
- Datasetvalidatie weigert de oorspronkelijke ongereviewde kandidaatdataset. De later toegevoegde baldataset gebruikt een afzonderlijke, expliciet voorlopige AI-route. Er zijn geen testmetrics of menselijke goedkeuringen verzonnen.

## Werkelijke vervolgstap: balannotaties en training

De gebruiker vroeg daarna expliciet: `Echte fine-tuning en project-mAP zijn nog niet uitgevoerd` en `hoort dit bij alles van persoon 1 zoja doe dit dan ook`.

Codex heeft daarop 47 beelden uit de gekozen echte voetbalvideo visueel van balboxen voorzien, met oorspronkelijke context en vergrote uitsneden. Helderheidscomponenten en de eerdere YOLO-voorstellen hielpen bij het zoeken; verkeerde of ontbrekende voorstellen zijn visueel gecorrigeerd. Eén voorbeeld is frame 2525: de helderheidscomponent nam een schoen mee, waarna de box is beperkt tot de bal. Onduidelijke bronmomenten zijn uitgesloten en zijn geen negatieve labels geworden.

Deze dataset staat nadrukkelijk als `provisional_ai_visual` geregistreerd. Annotator is `Codex AI`; menselijke reviewernamen blijven leeg en `human_review_completed` is onwaar. Er zijn geen twee onafhankelijk werkende mensen nagebootst. De afzonderlijke voorlopige ontwikkelroute controleert labels, bronbeelden en bewijschecksums. De normale teamreview en formele testbeveiliging blijven bestaan.

De echte trainings- en validatieresultaten worden in `docs/Resultaten_Balexperimenten.md` vastgelegd. De 640-run bracht daadwerkelijk een voorbewerkingsfout voor deze kleine ballen aan het licht: er bleven nul trainingsinstanties over. Het vervolg op 1920 met rechthoekige batches is vooraf als gericht experiment geregistreerd. Het wordt niet als een zuivere wijziging van uitsluitend resolutie voorgesteld.

## Wat het team nog zelf moet doen

Beide studenten moeten de code, aannames en nu vastgelegde AI-labels inhoudelijk reviewen, de modelkeuzes verdedigen en de resultaten van de echte trainingsruns begrijpen. De gezamenlijke zes proefannotaties, onafhankelijke review en verdediging blijven hun eigen werk. Werk deze disclosure verder bij met genomen beslissingen, eigen wijzigingen, feedback en werkelijke vervolgprompts.

## Spelerpakket en expliciete AI-review

De gebruiker vroeg om echte player/referee-klassen, een complete modeloverdracht, pushen op main en vervolgens: `kijk da zelf na en ga verder`. Codex heeft daarop alle 60 TeamTrack-beelden en spelerboxen visueel onderzocht, doelmannen als player behouden, de centrale official toegevoegd en verkeerde voorstellen gecorrigeerd. Ambigue verre rolvoorstellen zijn verworpen. De coveragebeperking blijft zichtbaar; menselijke reviewernamen zijn niet verzonnen.

EXP-P001 had onvolledige officiallabels; EXP-P002 is tijdens de laatste labelcontrole gestopt. EXP-P003 en EXP-P004 zijn echte vergelijkbare runs op v2.1. Het geselecteerde P004-checkpoint verbetert de speler-AP, maar vermindert official-recall op het werkpunt. Voorspellingen, configuraties, logs, daadwerkelijke modelnamen en hashes zijn bewaard.

Een latere pull bracht ontwikkelannotaties uit de gereserveerde testclip binnen. Die overlap is gemeld; er zijn geen onafhankelijke projecteindtestresultaten geclaimd. De AI kan de zelfstandige verdediging of daadwerkelijke beoordeling door twee studenten niet als verricht registreren.

## Rollen en spelertelling bij automatische veldherkenning

De gebruiker vroeg vervolgens om GitHub-synchronisatie en verduidelijkte: `alleen spelers op het veld ga tellen en nie stewards bv op het veld`, met afzonderlijke herkenning van stewards, supporters en officials. Codex heeft de telregels en trackerfilter gekoppeld aan zowel de voorspelde rol als de geldige actuele veldpositie, aparte semantische rollen in de pipeline ondersteund en de interface en overdracht aangepast. De veldherkenningsalgoritmen van persoon 2 zijn daarbij behouden.

De bestaande gewichten hebben slechts `player` en `referee`. Het verzoek is daarom niet als bewijs geïnterpreteerd dat steward-, supporter- of volledige officialherkenning al werkt. De toegevoegde extra-roltests gebruiken expliciet synthetische detectoruitvoer. Er is voor deze softwarewijziging geen nieuwe roltraining of mAP-meting uitgevoerd en geen menselijke annotatiereview geregistreerd. [Telregels en open modelwerk](Spelertelling_en_Rollen.md) beschrijven die grens concreet.

## Werkelijke aanvullende rol- en teamtraining

De gebruiker vroeg daarna letterlijk: `zorg dat die extra rolherkenning wel herkent en ook per team`. Codex heeft elf Commons-bronfoto’s met licenties en negen ontwikkel-/validatiebeelden uit de oorspronkelijke video toegevoegd, persoonsuitsneden visueel van rollen en teams voorzien en echte MobileNet-headtraining en gedeeltelijke CNN-fine-tuning uitgevoerd. Een proef met automatische persoonsvoorstellen is bewaard naast de AI-correcties. Bron-ID’s, kleding en context onderbouwen de labels; clubnamen en menselijke review zijn niet verzonnen.

R001..R007 zijn echte trainings-/classificatie-experimenten; R008 is een echte inferentieproef met dezelfde gewichten en extra uitsneden. R004 faalde duidelijk op de oorspronkelijke video, waarna die bron gericht aan training werd toegevoegd. R005/R006 en de extra uitsneden leverden afwegingen of verslechteringen op; die zijn niet weggewerkt. R007 is de gekozen experimentele uitvoering. Ondersteuner- en centrale-officialherkenning blijven aantoonbaar zwak. De aparte cropmetingen worden niet als volledige detectierecalls of projecteindtest voorgesteld.

De huidige speler-/rolselectie heeft 80 bronbeelden, maar samen met de historische balexperimenten zijn cumulatief 122 verschillende bronbeelden onderzocht. Alle nieuwe labels blijven voorlopig AI-labelwerk. De oorspronkelijke testbeelden, menselijke MVP-acceptatie en zelfstandige verdediging worden niet als verricht geregistreerd. [De volledige afwegingen en echte cijfers](Resultaten_Rollen_en_Teams.md) blijven beschikbaar.

## Gezamenlijke integratiecontrole

De gebruiker vroeg: `zorg dat alles samen nu tegoei werkt ook van de andere persoon die heeft gepushed` en bevestigde `Team A en Team B gebruiken`. Codex heeft de nieuwste dataoverdracht `857adf5` opgehaald, de bestanden en dataloader gecontroleerd, een gecombineerde startopdracht toegevoegd en de uitvoeraudit uitgebreid met echte rol- en teammetadata. De afzonderlijke veldomgeving is lokaal geïnstalleerd. Beide echte videoproeven, 150 vaste-camera-frames en 120 automatische-veldframes, zijn uitgevoerd met R007 op de hier beschikbare RTX 3050. De automatische Commons-proef leverde 0 betrouwbare veldframes op; veldposities en tellingen bleven onbekend. Die negatieve uitkomst wordt niet als geslaagde veldherkenning gepresenteerd.

De softwaretests gebruiken daarnaast expliciet synthetische fixtures voor extra rollen, lege frames en exportfouten. Een opgeslagen echte modelrun is met de Streamlit-testomgeving op begin, midden en einde geopend. Dat is geen menselijke nauwkeurigheidsreview. De nieuw opgehaalde 48 persoons-/balbeelden zijn niet automatisch aan de roltraining toegevoegd; datasets, bronidentiteiten en bestaande kalibratiegrenzen blijven gescheiden. [Uitvoering en beperkingen](Gezamenlijke_Integratie.md) staan bij de nieuwe rapporten.

## Gerichte extra datakandidaten

De gebruiker vroeg: `kun je nog meer data verzamelen zodat onze oplossing beter word? of is dat niet slim`. Codex heeft de oorspronkelijke opdracht gelezen en de voorwaarden van mogelijke externe bronnen onderzocht. Vervolgens zijn 25 momenten uit uitsluitend de zes bestaande `football48`-trainingsgroepen met echte R007-inference bekeken en twaalf extra volledige frames geselecteerd. Rolonzekerheid en mogelijke afwijking van een bestaande, door AI geschatte veldregio bepalen de selectie; voorspellingen worden niet als referentielabel gebruikt.

De beelden, bron-/beeldhashes, exacte clipindices, alle selectiesignalen en voorstellen zijn bewaard onder `datasets/development-candidates-v1`. Onafhankelijke sequentiële decodering controleert de twaalf clipframe-identiteiten en reproduceert de JPEG-bestanden. De beelden zijn ongelabeld en niet automatisch geschikt gemaakt voor training. Validatie- en testgroepen zijn niet gebruikt, er is geen nieuwe wedstrijd toegevoegd, geen model opnieuw getraind en geen kwaliteitswinst geclaimd. SoccerNet GSR en SoccerTrack v2 zijn kandidaatbronnen voor bredere variatie; externe gated data of licentievoorwaarden zijn niet namens de gebruiker geaccepteerd.

## Uitgevoerde vervolgronde met echte training

Op `ok doe maar` heeft Codex de 48 beelden en balpatches opnieuw bekeken en twee echte YOLO-trainingsruns uitgevoerd: F001 met tien vaste modules en F002 zonder vaste backbone. Beide eindigden na 57 epochs, met echte checkpoints, logs, curves en baselinevergelijking. De fijngetrainde modellen blijven op de afgesproken AP@50:95-maat onder de pretrained baseline. De negatieve resultaten worden behouden en de modellen worden niet als verbetering geïntegreerd.

Daarnaast zijn 52 roltrainingscrops uit de twaalf kandidaten en 59 rolvalidatiecrops uit bestaande validatiebeelden door AI gelabeld. Onbeslisbare fragmenten zijn expliciet uitgesloten. De nieuwe rolversie bewaart de oude labels, de tijdgroepen en alle bronhashes. De toegevoegde opname heeft geen team-supervisie; een codecontrole voorkomt dat alleen rolgegevens haar toch een bekende teamwedstrijd maken. Er zijn geen extra steward-/supporterlabels of menselijke reviews verzonnen.

R009 past de bestaande rolbackbone gedeeltelijk aan; R010 houdt die backbone exact vast. Beide zijn werkelijk getraind en op dezelfde behouden/toegevoegde validatiecrops én de oorspronkelijke volledige detectievalidatie vergeleken. R009 verbetert spelers/officials, maar andere rollen blijven zwak of verslechteren in de gedeeltelijke externe proef. Daarom zijn de nieuwe profielen expliciete alternatieven en blijft R007 standaard. Nieuwe ruwe videoproeven en een volledige R009-pipelinerun zijn als technische controles bewaard, met onbekende veldtellingen wanneer kalibratie faalt. [Alle uitkomsten en grenzen](Resultaten_Extra_Dataronde.md) blijven beschikbaar.

## Gerichte softwareverbetering van teams en persoonsvoorstellen

Op `maak het beter` heeft Codex de bestaande foutbeelden onderzocht, aanvullende voorlopige teamreferenties visueel vastgelegd en verschillende kleurkenmerken op dezelfde ontwikkelbeelden vergeleken. Er zijn geen menselijke reviews, nieuwe training, extra eindtest of clubidentiteiten verzonnen. De gekozen kleurprocedure weegt hue met verzadiging en verfijnt de eerste clusters. Zij vermindert verkeerde teamkoppelingen op de ontwikkelreferenties, met ook extra onbekende gevallen en een terugval in TeamTrack-dekking. Alle negatieve varianten blijven zichtbaar.

Een aanvullende insluitingscontrole voegt dubbele bovenlichaam-/volledige-lichaamvoorstellen van verschillende detectoren samen. Beide echte rolprofielen zijn volledig opnieuw geëvalueerd: vijf minder speler-FP, gelijkblijvende TP en FN op dezelfde twaalf validatiebeelden. Een afzonderlijk gelabeld snapshot blijft een gedeeltelijk ontwikkelvoorbeeld en wordt niet als onafhankelijke video-accuracy gepresenteerd. De automatische en statische gezamenlijke pilots zijn opnieuw technisch uitgevoerd. De beperkingen van andere rollen, keepers en veldherkenning blijven benoemd in [het voor/na-rapport](Verbetering_Teams_en_Boxen.md).

## Werkverdeling voor drie menselijke teamleden

Op 26 oktober 2026 vroeg de gebruiker om al het verbeterwerk over drie personen te verdelen. Codex heeft de actuele GitHub-versie en bestaande resultaten gebruikt om [een gezamenlijk werkplan](Werkverdeling_3_Personen.md) te schrijven met data/modellen bij persoon 1, veld/projectie bij persoon 2 en teams/tracking/integratie bij persoon 3. Taken, primaire bestanden, overdrachten, review en gezamenlijke acceptatie zijn beschreven. Deze wijziging voert die taken niet uit, maakt geen nieuwe nauwkeurigheidsmetingen en registreert geen menselijke review of MVP-acceptatie. Er zijn hiervoor geen nieuwe chats of agents gestart.

## Uitvoering werkpakket 1, derde ronde

De gebruiker vroeg vervolgens `1 Data, detectie, rolherkenning en modeltraining ... doe dit`. Codex heeft nieuwe vrije Commons-bronnen met attributie geregistreerd, persoonsvoorstellen en 93 voorlopige AI-rolcrops beoordeeld, een ambigue rol met behoud van V3.0 naar V3.1 gecorrigeerd en de data-audit en kopieerlekguard uitgevoerd. De correcte-crop- en volledige detectiemetingen blijven gescheiden. Vijf echte roltrainingen, twee echte baltrainingen, een compatibele lineaire kopmengproef en één afgewezen persoonsvoorstelablation zijn bewaard. R015 is een alternatief met regressies; R007 blijft standaard. F003 wint op native-crop-AP@50:95, maar een echt raw-frame-logo-FP verhindert een algemene videokwaliteitsclaim.

Alle modelgewichten, echte klassebetekenissen, hashes, configuraties, curves, bron-/labelversies, foutregisters en echte JSONL-overdracht worden gedeeld. De volledige R015-videoproef en softwaresuite zijn uitgevoerd op de aanwezige RTX 3050. De bestaande Commons-ontwikkelclip bevat nu één roltrainingsframe en mag niet als ongeziene projecteindtest worden gepresenteerd. Er zijn geen nieuwe menselijke reviewers, onafhankelijke eindtest of 4050-resultaten verzonnen. De algemene R011-vergelijkingsnotitie is na zijn start geschreven en wordt niet als voorafgaande trainingpreregistratie voorgesteld. [Alle resultaten en grenzen](Uitvoering_Persoon_1_Derde_Ronde.md) blijven controleerbaar.

Bij de afsluitende synchronisatie kwamen twee upstream-dataleveringen met 40 en 16 volledige panoramabeelden binnen. Codex heeft de technische validators en dataloaders opnieuw uitgevoerd, met aparte rapporten zodat de eerdere broncontrole niet wordt overschreven. De datasets zijn niet stilzwijgend toegevoegd aan afgeronde trainingen. Een vooraf genoteerde overdrachtsmeting met drie bevroren balmodellen op de veertien volledige validatiebeelden levert overal nul AP bij imgsz 1280 en voor F003 zestien FP bij confidence 0,25. Ook dit negatieve resultaat, de geschilderde-letter-FP, hashes en voorspellingen worden gepubliceerd. Groepslabels `crowd` worden niet als afzonderlijke supporterlabels gebruikt. Na samenvoeging slagen 225 tests en vier subtests; de menselijke review en onafhankelijke eindtest blijven open.

De volgende pull bevatte nog drie leveringen met samen 130 volledige beelden. Codex heeft deze behouden en hun technische validators en individuele/gecombineerde dataloaders uitgevoerd, zonder de eerdere trainingen of scorepopulaties te veranderen. De 60-beeldenlevering heeft een afzonderlijke speelbalexport; dit verschilt van de gemeten taak waarin reserveballen ook positief zijn. Ook hiervoor is geen menselijke review, nieuwe training of nieuwe prestatiemeting verzonnen.

Na de echte GitHub-push zijn acht checkpoints en veertien nieuwe bronbeelden uit een nieuwe LFS-cache opnieuw gedownload. Alle 22 hashes en groottes kloppen; de zes rolclassifiers en twee YOLO-modellen zijn uit de opgehaalde bestanden geladen en de veertien beelden gedecodeerd. Het bewijsrapport bewaart de gepubliceerde assetcommit en daadwerkelijke uitvoerbetekenissen. Dit is geen menselijke kwaliteitsgoedkeuring of nieuwe accuracyclaim.

## Vervolg persoon 1: baldetail, native training en rolreviewprioriteiten

Op `doe maar verder met wat je kunt` heeft Codex de nul-AP op globale 1280-panorama-invoer onderzocht. Drie bevroren modellen zijn onder vier vooraf opgeslagen resolutie-/tegelinstellingen op dezelfde veertien beelden gemeten. De daarop gekozen combinatie van twee tegelschalen is expliciet een ontwikkelkeuze na inzage. Een balleninterface met originele pixelcoördinaten en globale NMS, gerichte regressietests en optionele profielen zijn toegevoegd. De bestaande R007-rollen, teams, veldpoort en trackingacceptatie blijven behouden.

F005 is werkelijk gedurende 37 epochs getraind op 159/80 pixel-identieke tegels uit de fullscene60-tijdsplit, met het beste checkpoint uit epoch 27. De aparte audit controleert alle 239 tegels en oorspronkelijke boxcoördinaten. Alle kandidaat- en baselinemetingen zijn op dezelfde 51 volledige validatiebeelden samengevoegd. De nieuwe training verbetert all-ball-AP, met meer FP en slechts beperkte speelbalwinst. Beide kanten van de afweging worden gepubliceerd. De bronnen delen twee validatie-tijdgroepen binnen één opname; dit wordt niet als onafhankelijke eindtest gepresenteerd.

De app-route reproduceert op echte beelden de gemeten boxen en beide gecombineerde profielen zijn op dertig opeenvolgende videoframes uitgevoerd. 238 tests en vier subtests slagen. Voor rollen zijn bestaande R007/R009/R015-voorspellingen gebruikt om 78 reviewgevallen te prioriteren; dat is geen nieuwe roltraining of menselijke labelreview. Er zijn geen reviewers, nieuwe clubnamen, 4050-metingen of gegarandeerde algemene nauwkeurigheid verzonnen. [Alle resultaten](Verbetering_Baldetectie_Detailbehoud.md) zijn herleidbaar.
