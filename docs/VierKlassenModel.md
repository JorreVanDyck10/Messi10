# Uitleg van de Python-code: Objectdetectie en tracking van een voetbal en scheidsrechters

## 1. Inleiding

Het python script "model_deployment" heeft als doel om met behulp van **YOLO** een voetbal en scheidsrechters te detecteren en te volgen in een voetbalvideo.

Naast het detecteren van objecten probeert het programma ervoor te zorgen dat de voetbal en scheidsrechters gedurende opeenvolgende videoframes correct gevolgd worden. Wanneer een object tijdelijk niet gedetecteerd wordt, probeert het programma de positie ervan te voorspellen op basis van de eerder waargenomen beweging.

De code maakt gebruik van verschillende libraries:

| Libraries | Functie |
|---|---|
| `ultralytics` | Gebruiken van het YOLO-model voor objectdetectie. |
| `tqdm` | Tonen van de voortgang tijdens het verwerken van de video. |
| `collections` | Werken met datastructuren zoals dictionaries. |
| `cv2` (OpenCV) | Inlezen, bewerken en opslaan van videobeelden. |
| `numpy` | Uitvoeren van wiskundige berekeningen en positiebepalingen. |

Het eindresultaat is een nieuwe video waarin de voetbal en scheidsrechters aangeduid worden met bounding boxes.

---

## 2. Libraries importeren

```python
from ultralytics import YOLO
from tqdm import tqdm
from collections import defaultdict
import cv2
import numpy as np
```

Hier worden de nodige libraries geïmporteerd.

- **YOLO:** Hiermee wordt het getrainde objectdetectiemodel geladen.
- **tqdm:** Hiermee wordt een voortgangsbalk weergegeven tijdens het verwerken van de frames.
- **defaultdict:** Een datastructuur uit Python. Overblijfsel uit een vorige versie. Hier wordt deze uiteindelijk niet gebruikt.
- **OpenCV:** Wordt gebruikt om de video frame per frame te verwerken.
- **NumPy:** Wordt gebruikt voor vectorberekeningen, afstanden en bewegingsvoorspellingen.

## 3. Video en model instellen

```python
source = "./videos/video.mp4"
target = "./videos/result_video.mp4"
model_path = "./runs/detect/soccer_training/ball_detector_640/weights/best.pt"

model = YOLO(model_path)
```

In dit gedeelte worden de paden naar de bestanden ingesteld.

- `source`: De oorspronkelijke voetbalvideo.
- `target`: De locatie waar de verwerkte video wordt opgeslagen.
- `model_path`: De locatie van het getrainde YOLO-model.

Met `YOLO(model_path)` wordt het getrainde model ingeladen.

Het model bevat de aangeleerde kennis om objecten in de video te herkennen, waaronder de voetbal en scheidsrechters.

## 4. Video openen en eigenschappen uitlezen

```python
cap = cv2.VideoCapture(source)

if not cap.isOpened():
    raise RuntimeError(f"Could not open video: {source}")
```

Met `cv2.VideoCapture()` wordt de oorspronkelijke video geopend.

Vervolgens wordt gecontroleerd of de video succesvol geladen is. Indien dit niet lukt, wordt een foutmelding weergegeven.

Daarna worden de eigenschappen van de clip opgehaald:

```python
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
```

Deze informatie is nodig om de nieuwe video met dezelfde eigenschappen aan te maken.

```python
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter(target, fourcc, fps, (width, height))
```

Hier wordt de video-uitvoer ingesteld.

`mp4v` is de gebruikte videocodec. De uitvoervideo krijgt dezelfde resolutie en framerate als de oorspronkelijke video.

---

## 5. Parameters en instellingen

In dit gedeelte worden verschillende parameters gedefinieerd die bepalen hoe de objectdetectie en tracking werken.

```python
REFEREE_COLOR = (0, 0, 255)
BALL_COLOR = (0, 165, 255)
```

Deze waarden bepalen de kleuren van de bounding boxes.

- `REFEREE_COLOR`: Rood voor scheidsrechters.
- `BALL_COLOR`: Oranje voor de voetbal.

OpenCV gebruikt het BGR-kleurformaat in plaats van RGB.

### 5.1 Confidence thresholds

```python
BALL_CONFIDENCE = 0.03
REFEREE_CONFIDENCE = 0.20
```

De confidence geeft aan hoe zeker het YOLO-model is dat een bepaald object aanwezig is.

- De voetbal wordt vanaf een confidence van 0.03 aanvaard.
- Een scheidsrechter wordt pas gedetecteerd vanaf een zekerheid van 0.20.

De lage confidence voor de voetbal is bewust gekozen omdat deze vaak klein is en daardoor moeilijker te detecteren is.

### 5.2 Maximum aantal gemiste frames

```python
BALL_MAX_MISSED_FRAMES = 10
REFEREE_MAX_MISSED_FRAMES = 10
```

Deze parameters bepalen hoeveel frames een object tijdelijk niet gedetecteerd mag worden voordat de tracking ervan wordt stopgezet.

Wanneer de voetbal bijvoorbeeld achter een speler verdwijnt, kan het programma de positie nog maximaal 10 frames voorspellen.

### 5.3 Maximale trackingafstand

```python
BALL_BASE_MAX_DISTANCE = 150
REFEREE_BASE_MAX_DISTANCE = 120
```

Deze waarden bepalen hoe ver een nieuw gedetecteerd object zich maximaal mag bevinden van de voorspelde positie.

De maximale afstand wordt aangepast aan de snelheid van het object.

### 5.4 Smoothing

```python
BALL_SMOOTHING = 0.65
REFEREE_SMOOTHING = 0.65
```

Deze parameters zorgen ervoor dat de beweging van de bounding boxes minder schokkerig wordt.

Een smoothingwaarde van 0.65 betekent dat 65% van de nieuwe detectie en 35% van de vorige positie gebruikt wordt om de nieuwe positie te bepalen.

---

## 6. Trackingvariabelen initialiseren

### 6.1 Voetbal

```python
last_ball_center = None
last_ball_box = None
previous_ball_center = None
missed_ball_frames = 0
last_ball_confidence = 0
```

Deze variabelen bewaren informatie over de laatst gedetecteerde voetbal.

| Variabele | Betekenis |
|---|---|
| `last_ball_center` | Laatst bekende middelpunt van de voetbal. |
| `last_ball_box` | Laatst bekende bounding box van de voetbal. |
| `previous_ball_center` | Middelpunt uit de vorige detectie. |
| `missed_ball_frames` | Aantal opeenvolgende frames waarin de voetbal niet gedetecteerd werd. |
| `last_ball_confidence` | Confidence van de laatste detectie. |

Door deze informatie te bewaren, kan het programma de beweging van de voetbal inschatten.

### 6.2 Scheidsrechters

```python
referee_tracks = {}
next_referee_id = 0
```

Voor scheidsrechters wordt een dictionary gebruikt.

Elke scheidsrechter krijgt een uniek ID. Hierdoor kan het programma verschillende scheidsrechters afzonderlijk blijven volgen.

Per scheidsrechter wordt informatie bewaard over de huidige positie, vorige positie, bounding box, confidence en het aantal gemiste frames.

---

## 7. Positievoorspelling

```python
def predict_position(track):
    velocity = np.array(track["center"]) - np.array(track["previous"])
    return np.array(track["center"]) + velocity * (track["missed"] + 1)
```

Deze functie voorspelt waar een scheidsrechter zich waarschijnlijk bevindt.

Eerst wordt de verplaatsing tussen de huidige en vorige positie berekend.

\[
v = P_t - P_{t-1}
\]

Vervolgens wordt deze verplaatsing gebruikt om de toekomstige positie te voorspellen:

\[
P_{predicted} = P_t + v \cdot (missed + 1)
\]

Hierbij geldt:

- \(P_t\): Laatst bekende positie.
- \(P_{t-1}\): Vorige positie.
- \(v\): Geschatte verplaatsing per frame.
- \(missed\): Aantal gemiste frames.

---

## 8. De video frame per frame verwerken

```python
for _ in tqdm(range(total_frames)):

    ret, frame = cap.read()

    if not ret:
        break
```

Hier begint de hoofduitwerking van het programma.

De video wordt frame per frame verwerkt.

- `tqdm` toont hoeveel frames al verwerkt zijn.
- `cap.read()` leest het volgende frame uit de video.
- `ret` geeft aan of het frame succesvol gelezen werd.
- `frame` bevat de afbeelding die verwerkt moet worden.

Wanneer er geen frame meer beschikbaar is, wordt de loop beëindigd.

---

## 9. Objectdetectie met YOLO

```python
result = model.predict(
    frame,
    conf=BALL_CONFIDENCE,
    iou=0.5,
    imgsz=1280,
    max_det=300,
    verbose=False
)[0]
```

Hier wordt het YOLO-model toegepast op de huidige frame.

De belangrijkste parameters zijn:

| Parameter | Betekenis |
|---|---|
| `frame` | Het huidige videoframe. |
| `conf` | Minimale confidence voor detecties. |
| `iou=0.5` | IoU-drempel voor Non-Maximum Suppression. |
| `imgsz=1280` | Afbeeldingsgrootte die gebruikt wordt voor de inferentie. |
| `max_det=300` | Maximumaantal detecties per frame. |
| `verbose=False` | Voorkomt uitgebreide uitvoer in de terminal. |

**IoU (Intersection over Union)** bepaalt hoeveel overlap er is tussen twee bounding boxes.

Het wordt gebruikt om overlappende detecties te beoordelen en dubbele detecties te onderdrukken via Non-Maximum Suppression.

---

## 10. Detecties verzamelen en classificeren

```python
ball_candidates = []
referee_candidates = []

for box in result.boxes:

    confidence = float(box.conf[0])
    class_id = int(box.cls[0])
    class_name = model.names[class_id].lower()

    x1, y1, x2, y2 = map(int, box.xyxy[0])

    center = (
        (x1 + x2) // 2,
        (y1 + y2) // 2
    )
```

Alle detecties van YOLO worden overlopen.

Voor elke detectie worden de volgende gegevens opgehaald:

- Confidence.
- Class ID.
- Class name.
- Coördinaten van de bounding box.
- Middelpunt van het gedetecteerde object.

De bounding box bestaat uit vier coördinaten:

\[
(x_1,y_1,x_2,y_2)
\]

Het middelpunt wordt berekend met:

\[
center_x = \frac{x_1+x_2}{2}
\]

\[
center_y = \frac{y_1+y_2}{2}
\]

Daarna worden de objecten opgesplitst:

```python
if "ball" in class_name:

    ball_candidates.append({
        "box": (x1, y1, x2, y2),
        "center": center,
        "confidence": confidence
    })

elif "referee" in class_name and confidence >= REFEREE_CONFIDENCE:

    referee_candidates.append({
        "box": (x1, y1, x2, y2),
        "center": center,
        "confidence": confidence
    })
```

Alle voetbaldetecties worden toegevoegd aan `ball_candidates`.

Alle scheidsrechters met voldoende confidence worden toegevoegd aan `referee_candidates`.

Op deze manier worden beide objectklassen afzonderlijk verwerkt.

---

# 11. Voetbaltracking

Dit is een belangrijk onderdeel van de code.

Het doel is niet alleen om de voetbal te detecteren, maar ook om ervoor te zorgen dat de juiste voetbal doorheen de volledige video gevolgd wordt.

Er kunnen namelijk meerdere detecties in één frame voorkomen. Bovendien kan de voetbal tijdelijk verdwijnen uit het beeld of achter een speler terechtkomen.

### 11.1 De beste voetbaldetectie selecteren

```python
selected_ball = None

if ball_candidates:

    if last_ball_center is None or missed_ball_frames > BALL_MAX_MISSED_FRAMES:

        selected_ball = max(
            ball_candidates,
            key=lambda item: item["confidence"]
        )
```

Wanneer er nog geen vorige voetbalpositie beschikbaar is, of wanneer de voetbal langer dan het toegestane aantal frames gemist werd, wordt de detectie met de hoogste confidence gekozen.

Dit is nodig om de tracking opnieuw op te starten.

### 11.2 Voorspellen van de voetbalpositie

Wanneer de voetbal al eerder gedetecteerd werd, probeert het programma de volgende positie te voorspellen.

```python
velocity = (
    np.array(last_ball_center) -
    np.array(previous_ball_center)
)

predicted_center = (
    np.array(last_ball_center) +
    velocity * (missed_ball_frames + 1)
)
```

De snelheid wordt berekend aan de hand van de vorige twee posities.

Daarna wordt de verwachte positie berekend.

Ook de maximale toegestane afstand wordt aangepast:

```python
max_distance = BALL_BASE_MAX_DISTANCE + (
    np.linalg.norm(velocity) * (missed_ball_frames + 1)
)
```

Dit is belangrijk omdat een voetbal soms zeer snel beweegt.

Wanneer de voetbal sneller beweegt, wordt de toegestane zoekafstand groter.

### 11.3 De juiste detectie selecteren

```python
valid_candidates = []

for candidate in ball_candidates:

    distance = np.linalg.norm(
        np.array(candidate["center"]) - predicted_center
    )

    if distance <= max_distance:
        valid_candidates.append(candidate)
```

Alle kandidaatdetecties worden vergeleken met de voorspelde positie.

De afstand wordt berekend met de Euclidische afstand:

\[
d = \sqrt{(x_2-x_1)^2+(y_2-y_1)^2}
\]

Alle detecties die binnen de maximale afstand vallen, worden als geldig beschouwd.

Vervolgens wordt de dichtstbijzijnde detectie geselecteerd:

```python
selected_ball = min(
    valid_candidates,
    key=lambda item: np.linalg.norm(
        np.array(item["center"]) - predicted_center
    )
)
```

Hierdoor kiest het programma niet zomaar de detectie met de hoogste confidence, maar vooral de detectie die het best aansluit bij de verwachte beweging van de voetbal.

### 11.4 Smoothing toepassen

```python
smoothed_center = (
    BALL_SMOOTHING * detected_center +
    (1 - BALL_SMOOTHING) * np.array(last_ball_center)
)
```

Nadat de juiste voetbal geselecteerd is, wordt de nieuwe positie afgevlakt.

De formule is:

\[
P_{smooth} = \alpha P_{new} + (1-\alpha)P_{old}
\]

Hierbij is \(\alpha = 0.65\).

Het resultaat is een vloeiendere beweging van de bounding box.

Vervolgens worden alle trackingvariabelen bijgewerkt:

```python
previous_ball_center = last_ball_center
last_ball_center = smoothed_center
last_ball_box = selected_ball["box"]
last_ball_confidence = selected_ball["confidence"]
missed_ball_frames = 0
```

### 11.5 Voetbal tijdelijk voorspellen

Wanneer de voetbal niet gedetecteerd wordt:

```python
elif last_ball_center is not None:

    missed_ball_frames += 1
```

Wordt de teller van gemiste frames verhoogd.

Zolang het aantal gemiste frames niet groter is dan 10, blijft het programma de voetbal volgen.

```python
ball_center = tuple(map(int,
    np.array(last_ball_center) + velocity * missed_ball_frames
))
```

De nieuwe positie wordt voorspeld op basis van de laatst bekende snelheid.

De bounding box wordt vervolgens verplaatst naar deze voorspelde positie.

De voetbal krijgt een ander label afhankelijk van de situatie:

- `BALL`: De voetbal werd effectief gedetecteerd.
- `BALL PREDICTED`: De positie van de voetbal werd voorspeld.

Dit maakt het mogelijk om de voetbal tijdelijk te blijven volgen wanneer deze bijvoorbeeld achter een speler verdwijnt.

---

# 12. Scheidsrechtertracking

Voor het volgen van scheidsrechters wordt een andere aanpak gebruikt.

Omdat er meerdere referees aanwezig kunnen zijn, moet het programma bijhouden welke detectie bij welke scheidsrechter hoort.

Daarom wordt gebruikgemaakt van een eenvoudige vorm van objecttracking op basis van de afstand tussen opeenvolgende posities.

### 12.1 Tracks initialiseren

```python
for track in referee_tracks.values():
    track["matched"] = False
```

Aan het begin van ieder frame worden alle bestaande tracks op `False` gezet.

Dit betekent dat de scheidsrechters nog niet gekoppeld zijn aan een nieuwe detectie in de huidige frame.

### 12.2 Mogelijke overeenkomsten zoeken

```python
possible_matches = []
```

Vervolgens worden alle bestaande scheidsrechtertracks overlopen.

```python
for referee_id, track in referee_tracks.items():

    if track["missed"] >= REFEREE_MAX_MISSED_FRAMES:
        continue

    predicted = predict_position(track)
```

Voor iedere scheidsrechter wordt de verwachte positie berekend.

Daarna wordt de maximale toegestane afstand bepaald:

```python
velocity = np.linalg.norm(
    np.array(track["center"]) - np.array(track["previous"])
)

max_distance = REFEREE_BASE_MAX_DISTANCE + velocity * (
    track["missed"] + 1
)
```

Net zoals bij de voetbal wordt de maximale afstand aangepast aan de snelheid.

Vervolgens worden alle mogelijke combinaties tussen bestaande tracks en nieuwe detecties onderzocht.

```python
for candidate_index, candidate in enumerate(referee_candidates):

    distance = np.linalg.norm(
        np.array(candidate["center"]) - predicted
    )

    if distance <= max_distance:
        possible_matches.append(
            (distance, referee_id, candidate_index)
        )
```

Wanneer een detectie dicht genoeg bij de voorspelde positie ligt, wordt deze combinatie toegevoegd aan `possible_matches`.

### 12.3 Beste overeenkomsten selecteren

```python
possible_matches.sort(key=lambda item: item[0])
```

Alle mogelijke overeenkomsten worden gesorteerd op basis van afstand.

De kleinste afstand komt eerst.

Daarna wordt ervoor gezorgd dat één detectie niet aan meerdere scheidsrechtertracks gekoppeld wordt en dat één track niet meerdere detecties krijgt.

```python
used_tracks = set()
used_candidates = set()
```

Dit gebeurt met:

```python
for distance, referee_id, candidate_index in possible_matches:

    if referee_id in used_tracks or candidate_index in used_candidates:
        continue
```

Hierdoor krijgt iedere scheidsrechter maximaal één detectie per frame.

Dit is belangrijk om de verschillende scheidsrechters afzonderlijk te blijven volgen.

**Opmerking:** Dit is een eenvoudige greedy matching-methode. Ze kiest telkens de beste beschikbare combinatie, maar garandeert niet dat de totale afstand van alle koppelingen minimaal is.

### 12.4 Trackinggegevens bijwerken

Wanneer een bestaande scheidsrechter gekoppeld wordt aan een nieuwe detectie, worden de gegevens bijgewerkt.

```python
track["previous"] = track["center"]
track["center"] = tuple(map(int, smoothed_center))
track["box"] = candidate["box"]
track["confidence"] = candidate["confidence"]
track["missed"] = 0
track["matched"] = True
```

De nieuwe positie wordt eerst gesmoothed.

Daarna worden de vorige positie, huidige positie, bounding box, en confidence opgeslagen.

De teller van gemiste frames wordt opnieuw op nul gezet.

### 12.5 Nieuwe scheidsrechters toevoegen

```python
for candidate_index, candidate in enumerate(referee_candidates):

    if candidate_index in used_candidates:
        continue
```

Wanneer een detectie niet gekoppeld kon worden aan een bestaande referee, wordt ervan uitgegaan dat het om een nieuwe scheidsrechtertrack gaat.

```python
referee_tracks[next_referee_id] = {
    "center": candidate["center"],
    "previous": candidate["center"],
    "box": candidate["box"],
    "confidence": candidate["confidence"],
    "missed": 0,
    "matched": True
}

next_referee_id += 1
```

De nieuwe scheidsrechter krijgt een uniek ID.

Op deze manier kunnen meerdere scheidsrechters tegelijkertijd gevolgd worden.

### 12.6 Gemiste scheidsrechters verwerken

Na het koppelen worden alle bestaande tracks opnieuw overlopen.

```python
if not track["matched"]:
    track["missed"] += 1
```

Wanneer een scheidsrechter niet gedetecteerd werd, wordt het aantal gemiste frames verhoogd.

```python
if track["missed"] > REFEREE_MAX_MISSED_FRAMES:
    del referee_tracks[referee_id]
    continue
```

Wanneer een scheidsrechter langer dan 10 frames niet gedetecteerd wordt, wordt zijn track verwijderd.

Wanneer de scheidsrechter slechts tijdelijk gemist wordt, wordt zijn positie voorspeld:

```python
if track["missed"] > 0:

    predicted = predict_position(track)
    referee_center = tuple(map(int, predicted))
```

Hierdoor blijft de scheidsrechter tijdelijk zichtbaar in de video, zelfs wanneer YOLO hem niet detecteert.

Net zoals bij de voetbal krijgt de scheidsrechter een ander label:

- `REFEREE`: De scheidsrechter werd effectief gedetecteerd.
- `REFEREE PREDICTED`: De positie werd voorspeld.

---

## 13. Bounding boxes tekenen

Zowel voor de voetbal als voor de scheidsrechters worden bounding boxes getekend.

Bijvoorbeeld:

```python
cv2.rectangle(
    frame,
    (x1, y1),
    (x2, y2),
    BALL_COLOR,
    2
)
```

De functie `cv2.rectangle()` tekent een rechthoek rond het object.

De parameters zijn:

- `frame`: Het huidige videoframe.
- `(x1, y1)`: Linkerbovenhoek.
- `(x2, y2)`: Rechteronderhoek.
- `BALL_COLOR`: De kleur van de rechthoek.
- `2`: De dikte van de lijn.

Vervolgens wordt het label boven de bounding box geplaatst:

```python
cv2.putText(
    frame,
    label,
    (x1, max(y1 - 10, 20)),
    cv2.FONT_HERSHEY_SIMPLEX,
    0.6,
    BALL_COLOR,
    2
)
```

Hiermee wordt bijvoorbeeld `BALL 0.85` of `BALL PREDICTED` weergegeven.

Dezelfde techniek wordt toegepast voor de scheidsrechters, maar met een rode bounding box.

---

## 14. Video opslaan en bestanden afsluiten

```python
out.write(frame)
```

Nadat alle objecten gedetecteerd en getekend zijn, wordt de aangepaste frame toegevoegd aan de uitvoervideo.

Wanneer alle frames verwerkt zijn, worden de gebruikte bestanden afgesloten:

```python
cap.release()
out.release()
cv2.destroyAllWindows()
```

- `cap.release()`: Sluit de oorspronkelijke video.
- `out.release()`: Slaat de uitvoervideo correct op en sluit deze af.
- `cv2.destroyAllWindows()`: Sluit eventuele OpenCV-vensters.

Tot slot wordt de locatie van de nieuwe video weergegeven:

```python
print(f"Video saved to: {target}")
```

De verwerkte video wordt opgeslagen als:

`./videos/result_video.mp4`

---

## 15. Conclusie

Deze code combineert objectdetectie met YOLO en een zelf geïmplementeerd trackingsysteem om een voetbal en meerdere scheidsrechters doorheen een voetbalvideo te volgen.

De belangrijkste onderdelen zijn:

1. **Objectdetectie:** YOLO herkent de voetbal en scheidsrechters in elk videoframe.
2. **Objectselectie:** Het programma selecteert de meest waarschijnlijke voetbaldetectie op basis van de voorspelde positie en afstand.
3. **Objecttracking:** Scheidsrechters krijgen een uniek ID zodat ze afzonderlijk gevolgd kunnen worden.
4. **Positievoorspelling:** Wanneer een object tijdelijk niet gedetecteerd wordt, wordt de verwachte positie berekend op basis van de vorige beweging.
5. **Smoothing:** De positie van objecten wordt afgevlakt om schokkerige bewegingen van bounding boxes te verminderen.
6. **Visualisatie:** De gedetecteerde en voorspelde objecten worden aangeduid met bounding boxes en labels.

Een belangrijk onderscheid is dat YOLO verantwoordelijk is voor het herkennen van objecten, terwijl het zelfgeschreven trackingsysteem verantwoordelijk is voor het behouden van de objectidentiteit en het voorspellen van posities tussen opeenvolgende frames.

Het programma gebruikt dus niet alleen objectdetectie, maar combineert deze met bewegingsvoorspelling en objecttracking om een stabieler resultaat te verkrijgen.

---

# 16. Gebruik van AI tijdens de ontwikkeling

Tijdens de ontwikkeling en documentatie van dit document en deze documentatie werd generatieve AI gebruikt als ondersteunend hulpmiddel. AI werd op verschillende momenten ingezet om het ontwikkelingsproces efficiënter te maken en de kwaliteit van de code en het tekstdocument te verbeteren.

## 16.1 Opmaak en structuur van de documentatie

AI werd gebruikt om de documentatie overzichtelijker en duidelijker te structureren. Hierbij werd ondersteuning geboden bij:

- Het opdelen van de code in logische hoofdstukken en subhoofdstukken.
- Het opstellen van Markdown-tabellen om parameters en variabelen toe te lichten.
- Het verbeteren van de leesbaarheid en formulering van de technische uitleg.

## 16.2 Eerste versie van de code

AI werd gebruikt als ondersteuning bij het uitwerken van de eerste versie van bepaalde onderdelen van de code.

Hierbij hielp AI onder andere met:

- Het structureren van de verschillende stappen van het detectieproces.
- Het uitwerken van de logica voor het volgen van de voetbal.
- Het opzetten van een trackingsysteem voor meerdere scheidsrechters.
- Het toepassen van positiebepaling en bewegingsvoorspelling.

De voorgestelde code en oplossingen werden vervolgens handmatig geëvalueerd en aangepast aan de specifieke vereisten van het project.

## 16.3 Debugging en foutopsporing

Tijdens het ontwikkelen werd AI ook gebruikt om te helpen bij het opsporen en oplossen van fouten.

Wanneer bepaalde onderdelen niet het gewenste resultaat opleverden, kon AI helpen bij:

- Het analyseren van foutmeldingen.
- Het opsporen van mogelijke fouten in de trackinglogica.
- Het controleren van berekeningen voor afstanden en voorspelde posities.

De voorgestelde aanpassingen werden getest en waar nodig verder aangepast.

## 16.4 Ownership

De uiteindelijke implementatie, keuzes van parameters, evaluatie van de resultaten en aanpassingen aan de code werden afgestemd op de werking en doelstellingen van het project.

Het gebruik van AI maakte het mogelijk om sneller verschillende oplossingen te onderzoeken, technische problemen beter te begrijpen en de documentatie duidelijker op te stellen.

Hoewel AI tijdens de ontwikkeling werd gebruikt als ondersteunend hulpmiddel, blijft de volledige verantwoordelijkheid voor de uiteindelijke code, de gemaakte keuzes, de uitgevoerde aanpassingen en de inhoud van de documentatie bij de auteur.
