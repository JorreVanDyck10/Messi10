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
- Datasetvalidatie weigert de huidige ongereviewde kandidaatlabels; er zijn geen testmetrics of menselijke goedkeuringen verzonnen.

## Wat het team nog zelf moet doen

Beide studenten moeten de code en aannames inhoudelijk reviewen, echte labels maken en controleren, de modelkeuzes verdedigen en de resultaten van echte trainingsruns begrijpen. Werk deze disclosure verder bij met genomen beslissingen, eigen wijzigingen, feedback en werkelijke vervolgprompts.
