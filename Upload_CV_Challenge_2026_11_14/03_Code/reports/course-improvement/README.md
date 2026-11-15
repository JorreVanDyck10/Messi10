# Ontwikkelronde volgens de cursus — 19 oktober 2026

De spelerverbetering is geactiveerd in `configs/models.json` en `configs/models-players.json`. Het profiel gebruikt EXP-P006, gewichthash `beecb2439ca3329816df75e28c247236dfd7b283e66db72168139a1d28891aee`.

| Spelermeting op 20 validatiebeelden uit drie andere wedstrijden | Resultaat |
|---|---:|
| Spelers AP@50 | 93,17% |
| Spelers AP@50:95 | 58,98% |
| Spelers precision / recall bij 0,25 | 80,48% / 91,78% |
| Spelers TP / FP / FN | 268 / 65 / 24 |
| Officials TP / FP / FN | 10 / 16 / 16 |
| Bal-AP | 0; niet aangeboden |

De detector geeft vanaf 0,10 door voor de tweede associatiestap van ByteTrack; nieuwe tracks beginnen vanaf 0,25. De precision/recall hierboven geldt voor de meetdrempel 0,25. AP voor spelers is geen algemene accuracy of mAP over alle klassen.

## Veld: kandidaat afgewezen

De actieve veldgewichten blijven de oorspronkelijke PnLCalib-release. Op de twintig validatiebeelden leveren ze twaalf correcte, twee foutieve en zes ontbrekende projecties op. De kandidaat uit de secundaire selectie houdt twaalf correcte projecties over met één foutieve en zeven ontbrekende projecties. Op de bestaande echte ontwikkelclip valt hij echter terug van zes naar nul intern bruikbare frames op veertig. Daarom is hij niet als standaard ingesteld. Deze interne bruikbaarheid is geen menselijke nauwkeurigheidsmeting.

De volledige fine-tuning, uitvoerlaagtraining, voorzichtige uitvoerlaagtraining en duale lijnproef staan in de afzonderlijke JSON-rapporten. `field-secondary-selection.json` beschrijft een **kandidaatselectie**, geen activering. De bijbehorende kopieën van trainingsrapporten zijn eveneens kandidaatprovenance. De definitieve beslissing staat in `field-selection.json`.

De oorspronkelijke veldtussenrapporten in `artifacts/course-improvement-20261019/field-policy*` gebruikten een later herstelde referentiemeting die sommige zichtbare lijnen oversloeg. De hier gekopieerde vergelijkingen gebruiken de gecorrigeerde homogene lijnmeting.

## Herkomst en open cursuswerk

`dataset-manifest.json` legt 60 trainingsbeelden uit wedstrijden 4, 6 en 9 en 20 validatiebeelden uit wedstrijden 2, 3 en 5 vast, inclusief de checksums en providerboxen. Bron: SN-GSR-2024 v1.3, vaste revisie. Test-/challengearchieven zijn niet geopend. Overlap met de oorspronkelijke voortraining van het veldmodel is niet uitgesloten.

Dit zijn kleine ontwikkelmetingen met gepubliceerde annotaties. De eigen assisted-labelingbijdrage, menselijke teamreview en onafhankelijke eindtest blijven open. De dataset heeft een afzonderlijke bewerkbare reviewkopie. [Methode, cursusverwijzingen, GenAI-vermelding en herhaalcommando's](../../docs/Modelverbetering_Volgens_Cursus.md).
