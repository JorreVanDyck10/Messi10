# Persoonlijke bijdrage en AI-gebruik — Milan Wouters

Bijgewerkt op 15 november 2026. Eigen bijdrage op basis van Milans verklaring; de technische AI-hulp is beschreven in de projectgeschiedenis en `docs/ai_usage.md`.

## Eigen werk

Ik heb zelf voetbalvideo's gezocht en geselecteerd voor het project. Ik heb ook aan het labelen en controleren van de beelden gewerkt, met ondersteuning van annotatievoorstellen. Samen met het team heb ik de definitieve labels beoordeeld. De huidige selectie van 80 beelden is volgens onze teamverklaring gecontroleerd en akkoord; twijfelgevallen vielen buiten die selectie.

De eerste annotatievoorstellen kwamen van providerlabels en Codex. Die herkomst blijft in de dataset staan. Mijn bijdrage aan het labelwerk betekent dus niet dat ik alle oorspronkelijke boxen zonder hulpmiddelen heb getekend. Er is geen individueel correctielog waarmee achteraf een exact aantal door mij aangepaste boxen kan worden vastgesteld.

## Waarvoor ik AI gebruikte

Ik gebruikte Codex als hulp bij het uitwerken en implementeren van de videopipeline, de Streamlit-interface, annotatiegereedschap en datasetcuratie. AI hielp ook met het opzetten en uitvoeren van trainings- en evaluatieopdrachten, het onderzoeken van mislukte proeven, foutmeldingen, installatie, modelintegratie en mergeconflicten. Verder gebruikte ik AI voor uitleg, het controleren en herschrijven van documentatie, de presentatie en het samenstellen van de inzending. De AI-bijdrage omvat daarmee ook gegenereerde code en technische uitvoering.

In de vastgelegde projectgeschiedenis koos ik onder meer de PANORIS-video `https://www.youtube.com/watch?v=HBTFZwMdcCw` en gaf ik aan dat het programma op een laptop met een RTX 4050 moest kunnen draaien. Codex hielp daarna bij het technisch verwerken van de gekozen bron. De lokaal vastgelegde GPU-proeven op een RTX 3050 zijn geen metingen op die beoogde RTX 4050.

Voorbeelden van vastgelegde instructies zijn: “fix de merge conflicts”, “ik moet de hoeken ... gewoon selecteren” en “ik wil spelertracking toevoegen”. Dit zijn korte voorbeelden uit de geschiedenis, geen gereconstrueerd volledig promptlog. Exacte model-ID's en iedere afzonderlijke sessie zijn niet vastgelegd.

## Controle en verantwoordelijkheid

De menselijke controle van de 80 beelden staat in `datasets/school-ball80-review-v1/REVIEW.md`. Technische tests, negatieve trainingsresultaten en modelvergelijkingen blijven afzonderlijk vastgelegd. Een geslaagde softwaretest bewijst geen herkenningsnauwkeurigheid; ontwikkelmetingen bewijzen geen onafhankelijke eindtest. De documentatie houdt die grenzen zichtbaar.

Ik blijf verantwoordelijk voor mijn bijdrage en moet de gebruikte code en keuzes zelf kunnen uitleggen. Het rapport, de presentatie en deze verklaring zijn met AI-hulp opgesteld en op taal en samenhang gecontroleerd. Een geschreven verklaring vervangt mijn eigen mondelinge verdediging niet.

Bronnen: mijn verklaring in deze opdracht; `docs/ai_usage.md`; `docs/GenAI_Disclosure.md`; de geregistreerde teamreview. Deze verklaring verandert de oorspronkelijke datasetmetadata niet.
