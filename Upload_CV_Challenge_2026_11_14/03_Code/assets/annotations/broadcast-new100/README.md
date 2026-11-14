# 100 nieuwe volledige broadcastframes

100 ongewijzigde beelden van 1920 × 1080 uit vijf andere broadcastbronclips, met **3.338 boxen**, waaronder **94 speelballen**. De selectie komt uit de DFL Bundesliga Data Shootout-voorbeeldclips die Roboflow beschikbaar stelt. De vijf clipnamen zijn bronidentificaties; wedstrijdnamen en datums zijn niet onafhankelijk vastgesteld.

| Klasse | YOLO-ID | Boxen |
| --- | ---: | ---: |
| player, inclusief doelmannen op het veld | 0 | 2.053 |
| in_play_ball, uitsluitend de speelbal | 1 | 94 |
| referee, inclusief assistenten | 2 | 238 |
| other_person, o.a. staf, wisselspelers en fotografen | 3 | 779 |
| crowd, één box per zichtbare publieksgroep | 4 | 109 |
| goal, inclusief zichtbaar doelnet | 5 | 27 |
| corner_flag, vlag en paal | 6 | 38 |
| stored_goals, gereserveerde klasse zonder voorbeelden | 7 | 0 |

Dit zijn aantallen per beeld, geen unieke personen, ballen of acties. Tribunepubliek is als groep gelabeld; groepsleden krijgen geen afzonderlijke box. Coaches en wisselspelers aan de zijlijn zijn `other_person`. **Klasse 1 betekent hier alleen de speelbal**; oudere sets waarin `ball` ook reserveballen omvat, mogen niet zonder harmonisatie worden samengevoegd. Reserveballen zijn voor deze speelbaltaak achtergrond.

## Beelden ophalen

GitHub bevat de labels, COCO-export, bronmetadata, controles en dit reproductiescript. Video's, PNG's en voorbeeldbeelden blijven lokaal: toestemming om de wedstrijdbeelden opnieuw te publiceren is niet vastgesteld. De licentie van voorbeeldcode verleent die toestemming niet. Gebruik de bronbeelden binnen de toepasselijke voorwaarden.

Voer vanuit de repository uit:

```powershell
python -m pip install -r assets/annotations/broadcast-new100/requirements.txt
python assets/annotations/broadcast-new100/fetch_and_build.py --download
```

Het script haalt alleen de vijf benodigde clips op, controleert hun SHA-256 en reconstrueert de exact geselecteerde frames. Het heeft geen detectiemodellen nodig en draait geen nieuwe inferentie. De eerste download is ongeveer 97 MB. Beschikbaarheid van externe downloads kan veranderen.

Met bestaande MP4-bestanden:

```powershell
python assets/annotations/broadcast-new100/fetch_and_build.py --source-dir "C:/pad/naar/de/vijf/clips"
```

De uitvoer staat standaard in deze map. `--output "C:/pad/naar/dataset"` maakt dezelfde export op een andere locatie. Beelden staan onder `images/train` en `images/val`; `previews` bevat volledige frames met getekende boxen. De invoer-PNG's bevatten geen overlays, uitsneden, maskers of schaalwijzigingen. Het script verifieert pixelgelijkheid met de gedecodeerde bronframes en de opgeslagen PNG-hashes. Bij verschillen tussen videodecoders of PNG-encoders meldt het script een fout in plaats van ongemerkt andere beelden te gebruiken.

## Trainingssets

| Configuratie in de uitvoermap | Train | Val | Gebruik |
| --- | ---: | ---: | --- |
| `data.yaml` | 74 | 20 | Acht klassen; alleen beelden met betrouwbaar gelokaliseerde speelbal |
| `in-play-ball/data.yaml` | 74 | 20 | Alleen de speelbal, hernummerd naar klasse 0 |
| `players/data.yaml` | 80 | 20 | Alleen actieve spelers, inclusief doelmannen, hernummerd naar klasse 0 |

Gebruik de bijgeleverde configuraties en tekstlijsten. **Train niet rechtstreeks op de hele hoofdmap `images/train` voor de baltaak**: zes beelden missen een betrouwbare ballokalisatie. Hun scène- en persoonslabels zijn beschikbaar, maar ze zijn geen negatieve balvoorbeelden. `manifest.json`, de COCO-beeldmetadata en `verification.json` vermelden de uitsluitingen expliciet. De complete COCO-export bevat alle 100 beelden; pas dezelfde uitsluitingen toe bij baltraining of -evaluatie.

Voorbeeld, na het ophalen van de beelden:

```powershell
yolo detect train model=yolo11n.pt data=assets/annotations/broadcast-new100/in-play-ball/data.yaml imgsz=1280
```

De beelden binnen een bronclip zijn ongeveer 1,5 seconde van elkaar gescheiden. Alle 20 beelden uit `121364_0.mp4` staan op `val`; de andere vier bronnen staan op `train`. Er is geen overlap van bronclips tussen de subsets. Dit is een ontwikkelsplit: de gebruikte Roboflow-voorstelmodellen kunnen deze voorbeeldclips tijdens hun training hebben gezien. Beschouw deze selectie dus niet als onafhankelijke test voor die modellen, en meng naburige momenten niet willekeurig over subsets.

## Bronnen en controle

De vijf bronnen zijn `08fd33_0.mp4`, `0bfacc_0.mp4`, `121364_0.mp4`, `2e57b9_0.mp4` en `573e61_0.mp4`. Iedere clip heeft 750 frames bij 25 fps. Er zijn 20 frames per bron geselecteerd tussen frame 10 en 739, dus 0,40–29,56 seconden. Deze toevoeging levert losse gelabelde frames; de clips hebben geen doorlopende labels of tracking-ID's en zijn hier niet opnieuw als fragmenten van 20 seconden geëxporteerd.

Bronnen: [Roboflow sports setup](https://github.com/roboflow/sports/blob/42c80c06b6b65a7f89455b89fe31cdf4c38ba227/examples/soccer/setup.sh), [Football AI-notebook met DFL-bronvermelding](https://colab.research.google.com/github/roboflow-ai/notebooks/blob/main/notebooks/football-ai.ipynb). De exacte download-ID's, bronhashes, tijden, boxen en voorstelmodellen staan in `source-annotations.json`.

De labels zijn gemaakt met modelvoorstellen en visuele correctie door Codex. Alle volledige scènes zijn bekeken; speelballen en aanvullende personen zijn ook op detailuitsneden gecontroleerd. Verkeerde labels op reclame, stoelen, camera's, handen en dubbele persoonsboxen zijn verwijderd of aangepast. Niet-zichtbare objecten worden niet verzonnen. Bij zeer kleine, gedeeltelijk verborgen of onscherpe objecten kunnen resterende fouten en ontbrekende labels voorkomen. **Onafhankelijke menselijke review staat open** (`human_review_complete: false`); er is geen gemeten labelnauwkeurigheid of nieuw modeltrainingsresultaat.

`verification.json` registreert bronhashes, pixelgelijkheid van alle 100 beelden, unieke beeldhashes, splits, boxaantallen en uitgesloten frames. YOLO gebruikt genormaliseerde centrumcoördinaten; COCO gebruikt pixelcoördinaten en categorie-ID = YOLO-ID + 1. `crowd` is een gewone detectieklasse (`iscrowd: 0`), geen COCO-ignore-regio.
