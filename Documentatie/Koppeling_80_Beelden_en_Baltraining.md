# De 80 reviewbeelden en de historische baltraining

Gecontroleerd op 15 november 2026. Dit is een nieuwe controle van bestaand bewijs, zonder nieuwe training of nauwkeurigheidsmeting.

## Aangetoonde verbinding

Alle 80 beelden van `datasets/school-ball80-review-v1` zijn ongewijzigde selecties uit het oorspronkelijke balcorpus van 132 bronbeelden. Voor ieder geselecteerd beeld komen de beeldhash, labelhash en train/val-split exact overeen. De reviewset telt 48 trainbeelden en 32 validatiebeelden.

Deze 80 bronbeelden zijn teruggevonden in 174 positieve uitsneden van de historische cropdataset. Het volledige experiment gebruikt 282 crops uit 132 bronbeelden, inclusief aanvullende beelden en negatieve uitsneden. De boxcoördinaten van iedere betrokken positieve crop zijn gecontroleerd tegen de oorspronkelijke balbox en de crop-offset. Kindbeelden behouden de split van hun bronbeeld.

De datasetfingerprint in het oorspronkelijke v2-experiment komt overeen met het originele cropmanifest en de bronfingerprint van de COCO-klasse-32-trainingsdataset. De opgeslagen begin- en eindgewichten komen overeen met de hashes van het experiment. Het trainingslog bevat twaalf voltooide epochs. Dit maakt de verbinding van reviewselectie naar bronlabels, crops, training en historische evaluatie controleerbaar.

## Betekenis en grenzen

De 80 beelden vormen een achteraf gereviewde subset van een grotere, eerder gebruikte dataset. Er is geen afzonderlijke nieuwe training op exact 48/32 beelden uitgevoerd. De latere menselijke goedkeuring van deze 80 beelden keurt de overige bronbeelden en historische experimenten niet automatisch goed. De oorspronkelijke reviewvelden blijven ongewijzigd bewaard.

De bestaande v2-evaluatie gebruikt 73 volledige validatiebeelden. Op volledige beelden rapporteert zij AP@50 41,64% en AP@50:95 18,01%; met tegelinvoer 57,49% en 23,34%. Dit zijn ontwikkelmetingen op de volledige historische validatie. Het zijn geen nieuwe scores op alleen de 32 review-validatiebeelden en geen scores voor Andrews huidige balmodel. De huidige app blijft Andrews model gebruiken; bal v2 blijft een gedocumenteerd trainings- en evaluatie-experiment.

De opdracht vraagt 40–80 gerichte annotaties en fine-tuning op de geannoteerde data. De opname van alle 80 in de historische train/val-keten is nu aangetoond. Het team moet de chronologie en het gebruik van aanvullende data duidelijk toelichten; het pakket claimt geen exact-80-run.

## Meegeleverd in de uploadmap

- `03_Code/datasets/school-ball80-review-v1`: definitieve reviewset en geregistreerde menselijke goedkeuring.
- `03_Code/data/broadcast-ball-review-v1/curated`: oorspronkelijke 132 beelden, labels en manifest.
- `03_Code/data/broadcast-training-v2/ball-coco`: complete trainingscrops en klasse-32-labels.
- `03_Code/data/broadcast-training-v2/balls/manifest.json`: oorspronkelijke provenance van de crops; beeldbestanden voor training staan onder ball-coco.
- `03_Code/artifacts/broadcast-ball-v2`: historische eindgewichten, args.yaml, results.csv en bewaarde experimentbron.
- `03_Code/artifacts/fullscene-ball-v1/fullscene_ball_f005.pt`: historische beginweging.
- `03_Code/Bal_v2_Training_en_Labelkoppeling.ipynb`: uitgevoerd inspectienotebook en bewust uitgeschakelde hertraincel.
- `Trainingsbewijs/labelset_training_koppeling.json`: controle per reviewbeeld en bijbehorende crops.

Voer de bestandscontrole uit vanuit de uploadmap:

```powershell
python .\03_Code\scripts\controle_labelset_training.py --code-root .\03_Code
```

Het notebook bindt voor een eventuele nieuwe training de oude YAML-paden aan de uitgepakte map en schrijft naar een nieuwe runmap. De oorspronkelijke bewijsbestanden worden niet overschreven. De oude uitgebreide experimentscripts blijven historische routes met hun eigen overige padvereisten; de meegeleverde notebook biedt de gerichte hertrainroute.
