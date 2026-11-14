# Extra velddata en lokale training

Momentopname: 2026-10-16T20:07:21.345092+00:00. Live status staat in `artifacts/field-training-full/job.json`.

| Onderdeel | Resultaat |
|---|---:|
| Gedownloade highlights | 30 |
| Geselecteerde highlightframes | 4204 |
| Overzichtskandidaten | 3259 |
| Mogelijke close-ups | 945 |
| Technisch geldige SoccerNet-trainbeelden | 8317 |
| Technisch geldige SoccerNet-validatiebeelden | 1649 |
| Overlappende wedstrijden tussen train en validatie | 0 |
| Corpusopslag | 9.95 / 20 GiB |

Beide veldnetwerken hebben een echte GPU-trainingsstap en validatiestap uitgevoerd. De opgeslagen gewichten laden opnieuw; het piekgebruik bleef onder 2,6 GB. Dit is een technische proef, geen gemeten verbetering.

Alle 4.204 labelvoorstellen zijn aangemaakt en technisch gecontroleerd. De uitgebreide job heeft ook de nieuwe GPU-preflight doorlopen en is gestart met de volledige trainingsselectie. Hij traint beide netwerken met maximaal 30 epochs en vergelijkt daarna de beste checkpoints. De eerste training gebruikt uitsluitend bestaande SoccerNet-labels.

Highlightvoorstellen zijn ongecontroleerd en uitgesloten van training. Menselijke Broadcast-projectiefouten blijven onbekend. Het standaardmodel wordt niet automatisch vervangen.

De volledige inventaris en hashes staan in [het JSON-rapport](field-training-preparation.json). Commando's en hervatten staan in [de werkwijze](../docs/Veldmodel_Training.md).

De korte technische vergelijking gaf nog geen duidelijke kwaliteitswinst: Broadcast-dekking 20,26% voor de baseline en 20,18% na één trainingsstap. Zie [het vergelijkingsrapport](../artifacts/field-training-smoke/comparison/report.md).
