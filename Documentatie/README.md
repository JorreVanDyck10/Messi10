# Gezamenlijke documentatie - Sports Vision

**Bijgewerkt op 15 november 2026**, na pull van main op `524d081a`. Andrews vierklassenmodel, oorspronkelijke tracker en AI-verantwoording en Jorres technische afronding en labelreview zijn verwerkt.

## Direct openen

- [Projectrapport in PDF](Rapport_Sports_Vision.pdf) · [bewerkbare tekst](Rapport_Sports_Vision.md)
- [PowerPointpresentatie](Presentatie_Sports_Vision.pptx)
- [Uitgevoerd trainings- en resultatennotebook](Training_en_Resultaten.ipynb)
- [Requirementscontrole en resterende opleverpunten](Requirementscontrole.md)
- [Bijdragen van Andrew en Jorre](Bijdragen_Andrew_en_Jorre.md)
- [GenAI-gebruik en eigenaarschap](GenAI_en_Eigenaarschap.md)
- [Versie en wijzigingen](Versie_en_Wijzigingen.md)

## Aangeleverde brondocumenten

- **Andrew:** [VierKlassenModel.md](../docs/VierKlassenModel.md), inclusief AI-gebruik in hoofdstuk 16; [oorspronkelijke training](../Andrew_Prototype/train.ipynb) en [prototype](../Andrew_Prototype/model_deployment.ipynb).
- **Jorre:** [Afronding van 14 november](../docs/Afronding_20261114.md), [technische controles](../reports/release-20261114/checks.json) en [review van de 80 beelden](../final/datasets/school-ball80-review-v1/REVIEW.md).
- [YOLO26-vergelijking](../docs/Yolo26_Spelersvergelijking.md) en [spelersdrempel/tracking](../docs/Spelersdrempel_en_tracking.md).

## Actuele stand

De menselijke review van alle huidige 80 labels is geregistreerd en goedgekeurd volgens expliciete teambevestiging. De oorspronkelijke AI/provider-herkomst, labels en 48/32-split blijven behouden. Dit is geen nieuwe training of onafhankelijke eindtest.

De hoofdbron gebruikt het bestaande YOLO11s-spelermodel en uitsluitend de baluitvoer uit Andrews YOLOv8x. De hoofdbron en het afzonderlijke GitHub-final-pakket hebben verschillende starters; volg de README van de gekozen versie. Lokale niet-gepubliceerde appaanpassingen worden niet als gedeelde GitHub-functies voorgesteld.

Open blijven onder meer de exacte koppeling van de definitieve reviewselectie aan training/evaluatie, een actuele geaccepteerde statische minimapdemonstratie, ruwe nieuwe experimentbewijzen en de individuele verdediging. Zie de requirementscontrole.

## Reproduceren en indienen

Het notebook leest de meegeleverde bewijzen en echte historische logs en start geen training. De oorspronkelijke trainingscode staat al in de repository. De scripts onder Bouwdocumentatie houden de documenten bewerkbaar. Voor model-/data-inspectie moet Git LFS de echte bestanden hebben opgehaald.

De compacte documenten staan rechtstreeks in GitHub. Grote lokale ZIP-bestanden, virtuele omgevingen en caches worden niet meegecommit. Maak voor de uiteindelijke upload één gecontroleerde ZIP per team met de actuele PDF, presentatie en gekozen uitvoer-/trainingscode. Een oudere lokale ZIP is geen actuele release.
