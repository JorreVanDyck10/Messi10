# Sports Vision Raoul versie

Korte voorbereiding voor de verdediging — 13 november 2026

## 1 Het project in één minuut

We maken een programma dat een voetbalvideo verwerkt. Het herkent personen of spelers, tekent kaders en toont hun plaats op een klein veld naast het camerabeeld. Dat veld noemen we de minimap.

We gebruiken een bestaand YOLO-model en hebben modellen bijgetraind op voetbalbeelden. Met een homography zetten we beeldpunten om naar een bovenaanzicht. Streamlit is onze lokale interface.

### De basisroute

1. Een MP4 uploaden en controleren.
2. Vier veldpunten aanduiden en twee extra punten gebruiken als controle.
3. YOLO laat spelers en scheidsrechters herkennen.
4. De onderkant van het spelerskader als voetpunt nemen.
5. Dat punt omzetten naar de minimap en beide beelden samen tonen.

Dit is de eenvoudige P004-route met een vaste camera. De uitgebreide route gebruikt ook extra rolmodellen en kan automatische veldherkenning gebruiken.

### De begrippen die je moet kennen

- **YOLO:** een model dat objecten vindt en kaders en klassen voorspelt.
- **Transfer learning:** beginnen met een model dat al beeldkenmerken heeft geleerd.
- **Fine-tuning:** dat model verder trainen op onze eigen voorbeelden.
- **Label:** het juiste kader en de juiste klasse bij een trainingsvoorbeeld.
- **Epoch:** één doorgang door de trainingsdata. **Batch:** beelden die tegelijk verwerkt worden.
- **Loss:** de trainingsfout. **Learning rate:** de stapgrootte van de gewichtsupdate.
- **Adam:** de optimizer die bepaalt hoe de gewichten worden bijgewerkt.
- **Early stopping:** stoppen als de validatiemaat niet meer verbetert volgens de ingestelde regels.

De trainingsvolgorde is: voorspellen, fout berekenen, gradients berekenen met backpropagation en gewichten aanpassen.

### Train validatie en test

Trainingsbeelden passen gewichten aan. Validatiebeelden helpen modellen en instellingen kiezen. Testbeelden dienen voor de beoordeling nadat de keuzes vastliggen. Bij video houden we tijdgroepen bij elkaar, omdat opeenvolgende beelden sterk op elkaar lijken.

## 2 Resultaten en fouten

### Meten zonder begrippen te verwarren

- **Confidence:** de modelscore van een voorspelling. Geen gegarandeerde kans op een juist antwoord.
- **IoU:** hoeveel een voorspeld kader overlapt met het juiste kader.
- **TP:** juist gevonden object. **FP:** foutieve detectie. **FN:** gemist object.
- **Precision:** hoeveel van onze voorspellingen juist zijn.
- **Recall:** hoeveel van de gelabelde objecten we vinden.
- **AP:** vat precision en recall samen over verschillende confidencegrenzen.
- **AP@50:95:** beoordeelt de kaderoverlap strenger dan AP@50. **mAP** middelt AP over klassen.

NMS verwijdert sterk overlappende dubbele voorspellingen. De NMS-overlapgrens is iets anders dan de IoU-grens voor een juiste evaluatiematch.

### Drie resultaten om te onthouden

**Spelers:** P004 behaalde historisch 74,50% speler-AP@50 en 26,55% AP@50:95 op twaalf validatiebeelden. Het verbeterde tegenover P003 op spelers, maar scheidsrechter-recall werd slechter. Dit zijn geen scores voor elke video of voor de volledige R007-route.

**Bal:** extra training gaf geen betere validatie-AP. Op Football48 haalde het bestaande model 67,82% AP@50. F001 haalde 60,40% en F002 43,07%. Op de andere PANORIS-set bleven de validatiescores nul. Meng die twee datasets niet tot één vergelijking.

**Veld:** in de Broadcast-proef waren 252 van 1239 frames intern bruikbaar, ongeveer 20,3%. Dit is dekking van de automatische kalibratie, geen bewezen nauwkeurigheid van de veldposities.

### Ons duidelijkste probleem

Bij de eerste baltraining op resolutie 640 werden de kleine balkaders na verkleinen door een softwarefilter verwijderd. Daardoor kreeg het model geen bruikbare boxvoorbeelden. Op 1920 bleven ze wel behouden, maar de validatie bleef slecht. Een hogere resolutie lost dus niet alles op.

Andere fouten: gemiste spelers, twee personen in één kader, verkeerde rollen en onbetrouwbare voetpunten. Een dalende trainingsloss bewijst geen goede herkenning op nieuwe beelden.

## 3 Korte antwoorden voor de verdediging

### Wat doet de homography

Ze zet punten uit het camerabeeld om naar een plat bovenaanzicht met behulp van bekende puntparen. We gebruiken het midden van de onderkant van een persoonskader als geschat voetpunt. Dit werkt voor het grondvlak. Een bal in de lucht kan je zo niet betrouwbaar plaatsen.

### Waarom een vaste camera

Dan blijft dezelfde omzetting bruikbaar. Als de camera draait of inzoomt, moet de omzetting opnieuw bepaald of gevolgd worden.

### Wat zijn de extra onderdelen

Tracking probeert een speler over frames dezelfde ID te geven. Teamkleurherkenning verdeelt spelers in Team A/B. Een extra MobileNet-classifier probeert rollen zoals steward of supporter te herkennen. Automatische veldherkenning gebruikt externe PnLCalib-modellen. Optical flow volgt kort de camerabeweging. Deze extra's zijn niet allemaal actief in de eenvoudige basisroute.

### Tellen jullie altijd precies de juiste spelers

Nee. Alleen voorspelde spelers met een geldige veldpositie en passende zichtbaarheid tellen mee. Een steward hoort niet mee te tellen, maar een verkeerde rolvoorspelling kan dat toch veroorzaken. Zonder betrouwbare kalibratie is het veldtotaal onbekend, niet nul.

### Waarom trainden jullie niet vanaf nul

We hebben weinig eigen beelden. Een pretrained model kent al algemene beeldkenmerken. Dat is een praktisch vertrekpunt, maar het maakt goede labels en eerlijke evaluatie niet minder belangrijk.

### Is alles al onafhankelijk getest

Nee. Aanvullende labels zijn voorlopig AI-werk en menselijke review staat nog open. Onze TeamTrack-testgroep is niet meer volledig onaangeroerd. Een nieuwe onafhankelijke eindtest en een gezamenlijke demo blijven nodig.

### Wat deed AI

Codex hielp uitgebreid bij code, labels, proeven en documentatie. Ook deze samenvatting is met Codex gemaakt. Wij moeten de gebruikte werking en resultaten zelf begrijpen en kunnen uitleggen.

### Wat moet ik zelf kunnen tonen

Het gekozen modelprofiel, één trainingsconfiguratie, één echte resultaatmeting en één foutvoorbeeld. Leg daarna het pad uit van kader naar voetpunt naar minimap. Beschrijf alleen taken als je eigen bijdrage als je die werkelijk hebt uitgevoerd.

Bronnen en verdere uitleg: Studiegids.md, vooral hoofdstukken 1–3, 10–18, 22–23 en 33. Deze korte versie vervangt geen voorbereiding op de extra onderdelen die jullie daadwerkelijk demonstreren.
