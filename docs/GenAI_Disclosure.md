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
