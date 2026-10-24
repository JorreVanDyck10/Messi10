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
