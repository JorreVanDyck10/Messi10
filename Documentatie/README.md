# Gezamenlijke documentatie - Sports Vision

**Versie 5, bijgewerkt op 15 november 2026**, na pull van main en ophalen van Jorres uploadbranch `8e29c3ff`. Andrews vierklassenmodel, oorspronkelijke tracker en AI-verantwoording en Jorres technische afronding en labelreview zijn verwerkt.

De definitieve inzendingsmap is [Upload_CV_Challenge_2026_11_14](../Upload_CV_Challenge_2026_11_14). Versie 5 gebruikt Jorres twaalf-slidepresentatie en bevat Milans persoonlijke bijdrage en AI-gebruik. De PDF en presentatie in beide mappen zijn gelijk.

## Direct openen

- [Projectrapport in PDF](Rapport_Sports_Vision.pdf) · [bewerkbare tekst](Rapport_Sports_Vision.md)
- [PowerPointpresentatie](Presentatie_Sports_Vision.pptx)
- [Uitgevoerd trainings- en resultatennotebook](Training_en_Resultaten.ipynb)
- [Requirementscontrole en resterende opleverpunten](Requirementscontrole.md)
- [AI-gebruik Milan Wouters](AI_Usage_Milan_Wouters.md), [Jorre Van Dyck](AI_Usage_Jorre_Van_Dyck.md) en [Raoul](AI_Usage_Raoul.md)
- [Andrews eigen AI-verantwoording](../docs/VierKlassenModel.md#16-gebruik-van-ai-tijdens-de-ontwikkeling)
- [Bijdragen van alle vier teamleden](Bijdragen_Andrew_en_Jorre.md)
- [GenAI-gebruik en eigenaarschap](GenAI_en_Eigenaarschap.md)
- [Versie en wijzigingen](Versie_en_Wijzigingen.md)

## Aangeleverde brondocumenten

- **Andrew:** [VierKlassenModel.md](../docs/VierKlassenModel.md), inclusief AI-gebruik in hoofdstuk 16; [oorspronkelijke training](../Andrew_Prototype/train.ipynb) en [prototype](../Andrew_Prototype/model_deployment.ipynb).
- **Jorre:** [Afronding van 14 november](../docs/Afronding_20261114.md), [technische controles](../reports/release-20261114/checks.json) en [review van de 80 beelden](../final/datasets/school-ball80-review-v1/REVIEW.md).
- [YOLO26-vergelijking](../docs/Yolo26_Spelersvergelijking.md) en [spelersdrempel/tracking](../docs/Spelersdrempel_en_tracking.md).

## Actuele stand

De menselijke review van alle huidige 80 labels is geregistreerd en goedgekeurd volgens expliciete teambevestiging. De oorspronkelijke AI/provider-herkomst, labels en 48/32-split blijven behouden. Dit is geen nieuwe training of onafhankelijke eindtest.

De hoofdbron gebruikt het bestaande YOLO11s-spelermodel en uitsluitend de baluitvoer uit Andrews YOLOv8x. De hoofdbron en het afzonderlijke GitHub-final-pakket hebben verschillende starters; volg de README van de gekozen versie. Lokale niet-gepubliceerde appaanpassingen worden niet als gedeelde GitHub-functies voorgesteld.

De [audit van de 80 beelden en baltraining](Koppeling_80_Beelden_en_Baltraining.md) toont nu hun opname in de grotere historische trainingsset. Open blijven een heldere vaste-camera-MVP-demonstratie, ruwe nieuwe experimentbewijzen, de aparte GenAI-policy en de individuele verdediging. Zie de requirementscontrole.

## Reproduceren en indienen

Het notebook leest de meegeleverde bewijzen en echte historische logs en start geen training. De oorspronkelijke trainingscode staat al in de repository. De scripts onder Bouwdocumentatie houden de documenten bewerkbaar. Voor model-/data-inspectie moet Git LFS de echte bestanden hebben opgehaald.

De compacte documenten staan rechtstreeks in GitHub. Grote lokale ZIP-bestanden, virtuele omgevingen en caches worden niet meegecommit. De nieuwe inzendings-ZIP wordt gemaakt uit de uploadmap, inclusief Jorres uitvoer-/trainingscode, modellen, data en demonstratie. Volg de uploadstarters in die map. Een oudere lokale ZIP is geen actuele release.

[Downloadbare GitHub-inzendings-ZIP](https://github.com/JorreVanDyck10/Messi10/releases/download/cv-challenge-inzending-v5-20261115/Inzending_Sports_Vision_DEFINITIEF_v5_GITHUB_2026_11_15.zip): de grote historische bronvideo staat apart bij dezelfde release; alle verplichte bestanden en teamverklaringen zitten in de ZIP.
